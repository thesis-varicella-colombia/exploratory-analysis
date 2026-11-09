"""Rt nacional diario desde los registros individuales de Sivigila.

Reproduce los filtros de residencia y ajuste de data-processing; usa FEC_NOT,
no la semana ANO/SEMANA ni una reconstrucción de incidencia diaria.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gamma

from epiestim_parametric_weekly import discr_si

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/sivigila/csv"
DIVIPOLA = ROOT / "data/sivigila/DIVIPOLA-_Códigos_municipios_20261007.csv"
WEEKLY = ROOT / "docs/data_processed/evolucion_semanal/weekly_series_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/numero_reproductivo/rt_national_daily.csv"
ALIASES = {"27086": "27493", "94663": "94343", "88000": "88001"}
COLS = ["ANO", "COD_EVE", "COD_DPTO_R", "COD_MUN_R", "AJUSTE", "FEC_NOT"]


def week_one_start(year: int) -> date:
    """Domingo de la semana epidemiológica 1, que contiene el 4 de enero."""
    jan4 = date(year, 1, 4)
    return jan4 - timedelta(days=(jan4.weekday() + 1) % 7)


def daily_counts(raw_dir: Path = RAW, divipola: Path = DIVIPOLA) -> tuple[pd.Series, Counter]:
    """Cuenta por FEC_NOT los registros incluidos en 2007–2025."""
    codes = pd.read_csv(divipola, dtype=str, encoding="utf-8-sig")["Código Municipio"]
    valid = set(codes.str.strip().str.zfill(5))
    if not set(ALIASES.values()) <= valid:
        raise ValueError("DIVIPOLA no contiene todos los códigos homologados")
    counts: Counter = Counter()
    quality: Counter = Counter()
    for year in range(2007, 2026):
        source = raw_dir / f"Datos_{year}_831.csv"
        for part in pd.read_csv(source, usecols=COLS, dtype=str, keep_default_na=False,
                                encoding="utf-8-sig", chunksize=50_000):
            quality["source_rows"] += len(part)
            if not pd.to_numeric(part.ANO, errors="coerce").eq(year).all():
                raise ValueError(f"{source.name}: ANO no coincide con {year}")
            if not pd.to_numeric(part.COD_EVE, errors="coerce").eq(831).all():
                raise ValueError(f"{source.name}: contiene otro evento")
            code = (part.COD_DPTO_R.str.strip().str.zfill(2)
                    + part.COD_MUN_R.str.strip().str.zfill(3)).replace(ALIASES)
            included = code.isin(valid) & ~part.AJUSTE.str.strip().str.upper().isin(["6", "D"])
            quality["included_rows"] += int(included.sum())
            date_text = part.loc[included, "FEC_NOT"].str.extract(
                r"^(\d{1,2}/\d{1,2}/\d{4})", expand=False)
            dates = pd.to_datetime(date_text, format="%d/%m/%Y", errors="coerce")
            quality["missing_notification_date"] += int(dates.isna().sum())
            counts.update(dates.dropna().dt.normalize().value_counts().to_dict())
    observed = pd.Series(counts, name="notifications", dtype="int64")
    observed.index = pd.DatetimeIndex(observed.index, name="date")
    return observed.sort_index(), quality


def build_daily_series(observed: pd.Series, weekly_path: Path = WEEKLY) -> pd.DataFrame:
    """Crea todos los días de 2008–2025 y conserva semanas faltantes como NA."""
    reference = pd.read_csv(weekly_path)
    reference = reference.loc[reference.age_group.eq("all") & reference.year.between(2008, 2025),
                              ["year", "week", "notifications"]]
    if reference.duplicated(["year", "week"]).any():
        raise ValueError("Serie semanal con claves repetidas")
    lookup = reference.set_index(["year", "week"])["notifications"]
    parts = []
    for year in range(2008, 2026):
        first = week_one_start(year)
        n_weeks = (week_one_start(year + 1) - first).days // 7
        for week in range(1, n_weeks + 1):
            days = pd.date_range(first + timedelta(weeks=week - 1), periods=7)
            key = (year, week)
            known = key in lookup.index and pd.notna(lookup.loc[key])
            values = observed.reindex(days, fill_value=0).to_numpy(dtype=float)
            if not known:
                if values.sum() != 0:
                    raise ValueError(f"{key}: hay casos en una semana ausente de la referencia")
                values[:] = np.nan
            elif int(values.sum()) != int(lookup.loc[key]):
                raise ValueError(f"{key}: total diario {values.sum():.0f} != semanal {lookup.loc[key]}")
            parts.append(pd.DataFrame({"date": days, "year": year, "week": week,
                                       "notifications": values, "missing_week": not known}))
    result = pd.concat(parts, ignore_index=True)
    if result.date.duplicated().any() or not result.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Calendario diario discontinuo o duplicado")
    return result


def estimate_daily(frame: pd.DataFrame, mean_si: float = 14.1, sd_si: float = 2.4,
                   window_days: int = 14, prior_mean: float = 5,
                   prior_sd: float = 5) -> pd.DataFrame:
    """Posterior Poisson–Gamma por ventana diaria; reinicia tras días faltantes."""
    if window_days < 1 or prior_mean <= 0 or prior_sd <= 0:
        raise ValueError("Ventana y parámetros previos deben ser positivos")
    result = frame.copy()
    for column in ["infectiousness", "rt", "rt_lower_95", "rt_upper_95"]:
        result[column] = np.nan
    incidence = result.notifications.to_numpy(dtype=float)
    valid = np.isfinite(incidence)
    boundaries = np.flatnonzero(np.diff(np.r_[False, valid, False]))
    for begin, stop in boundaries.reshape(-1, 2):
        daily = incidence[begin:stop]
        n = len(daily)
        weights = discr_si(np.arange(n), mean_si, sd_si)
        infectiousness = np.convolve(daily, weights, mode="full")[:n]
        infectiousness[0] = np.nan
        result.loc[begin:stop-1, "infectiousness"] = infectiousness
        ends = np.arange(window_days - 1, n)
        starts = ends - window_days + 1
        mean_discrete_si = float(np.dot(np.arange(n), weights))
        # Un día cercano al borde de un bloque ignora transmisores anteriores
        # al inicio observado. Exigimos al menos el 99 % de la masa serial
        # disponible incluso en el primer día de cada ventana publicada.
        min_history_lag = int(np.searchsorted(np.cumsum(weights), .99))
        eligible = (ends + 1 > mean_discrete_si) & (starts >= min_history_lag)
        ends, starts = ends[eligible], starts[eligible]
        if not len(ends):
            continue
        cases_cum = np.r_[0, np.cumsum(daily)]
        lambda_cum = np.r_[0, np.cumsum(np.nan_to_num(infectiousness, nan=0))]
        shape = (prior_mean / prior_sd) ** 2 + cases_cum[ends + 1] - cases_cum[starts]
        rate = prior_mean / prior_sd**2 + lambda_cum[ends + 1] - lambda_cum[starts]
        indices = begin + ends
        result.loc[indices, "rt"] = shape / rate
        result.loc[indices, "rt_lower_95"] = gamma.ppf(.025, a=shape, scale=1 / rate)
        result.loc[indices, "rt_upper_95"] = gamma.ppf(.975, a=shape, scale=1 / rate)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--divipola", type=Path, default=DIVIPOLA)
    parser.add_argument("--weekly", type=Path, default=WEEKLY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    observed, quality = daily_counts(args.raw_dir, args.divipola)
    frame = estimate_daily(build_daily_series(observed, args.weekly))
    frame["method"] = "epiestim_parametric_si_python_daily_notifications"
    frame["window_days"] = 14
    frame["serial_interval_mean_days"] = 14.1
    frame["serial_interval_sd_days"] = 2.4
    frame["prior_mean"] = 5.0
    frame["prior_sd"] = 5.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False, float_format="%.8f")
    print(dict(quality))
    print(f"Días: {len(frame)}; faltantes: {frame.notifications.isna().sum()}; "
          f"posteriores: {frame.rt.notna().sum()}; archivo: {args.output}")


if __name__ == "__main__":
    main()
