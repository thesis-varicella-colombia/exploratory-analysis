"""Estimate daily national Rt from individual symptom-onset dates in Sivigila."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from rt_daily_sivigila import ALIASES, DIVIPOLA, RAW, ROOT, estimate_daily, week_one_start

SYMPTOM_PARQUET = ROOT / "data/sivigila_integrado_symptom_semanal_municipal.parquet"
OUTPUT = ROOT / "docs/data_processed/numero_reproductivo/rt_national_symptom_daily.csv"
WEEKLY_OUTPUT = ROOT / "docs/data_processed/numero_reproductivo/weekly_series_symptom_2008_2025.csv"
SOURCE_COLUMNS = ["ANO", "COD_EVE", "COD_DPTO_R", "COD_MUN_R", "AJUSTE", "INI_SIN"]


def parse_onset_date(values: pd.Series, source_year: int) -> pd.Series:
    """Parse the 2013 month/day/year exception and day/month/year otherwise."""
    first = values.str.extract(r"^(\d{1,2}/\d{1,2}/\d{4})", expand=False)
    date_format = "%m/%d/%Y" if source_year == 2013 else "%d/%m/%Y"
    return pd.to_datetime(first, format=date_format, errors="coerce")


def onset_counts(raw_dir: Path = RAW, divipola: Path = DIVIPOLA) -> tuple[pd.Series, pd.DataFrame]:
    """Count eligible individual records by INI_SIN, auditing each source year."""
    codes = pd.read_csv(divipola, dtype=str, encoding="utf-8-sig")["Código Municipio"]
    valid = set(codes.str.strip().str.zfill(5))
    if not set(ALIASES.values()) <= valid:
        raise ValueError("DIVIPOLA lacks a target municipality for a required alias")
    counts: Counter = Counter()
    audits = []
    for source_year in range(2007, 2026):
        source = raw_dir / f"Datos_{source_year}_831.csv"
        audit: Counter = Counter()
        for chunk in pd.read_csv(source, usecols=SOURCE_COLUMNS, dtype=str,
                                 keep_default_na=False, encoding="utf-8-sig", chunksize=50_000):
            audit["source_rows"] += len(chunk)
            if not pd.to_numeric(chunk.ANO, errors="coerce").eq(source_year).all():
                raise ValueError(f"{source.name}: source year does not match ANO")
            if not pd.to_numeric(chunk.COD_EVE, errors="coerce").eq(831).all():
                raise ValueError(f"{source.name}: contains an event other than 831")
            code = (chunk.COD_DPTO_R.str.strip().str.zfill(2)
                    + chunk.COD_MUN_R.str.strip().str.zfill(3)).replace(ALIASES)
            included = code.isin(valid) & ~chunk.AJUSTE.str.strip().str.upper().isin(["6", "D"])
            audit["included_rows"] += int(included.sum())
            dates = parse_onset_date(chunk.loc[included, "INI_SIN"], source_year)
            audit["missing_or_invalid_onset"] += int(dates.isna().sum())
            audit["valid_onset"] += int(dates.notna().sum())
            counts.update(dates.dropna().dt.normalize().value_counts().to_dict())
        audits.append({"source_year": source_year, **audit})
    observed = pd.Series(counts, name="cases", dtype="int64")
    observed.index = pd.DatetimeIndex(observed.index, name="date")
    quality = pd.DataFrame(audits).fillna(0).astype("int64")
    quality["valid_onset_percent"] = 100 * quality.valid_onset / quality.included_rows
    if int(observed.sum()) != int(quality.valid_onset.sum()):
        raise AssertionError("Daily onset counts do not conserve valid records")
    return observed.sort_index(), quality


def symptom_weekly_reference(path: Path = SYMPTOM_PARQUET) -> pd.DataFrame:
    """Read weekly national onset totals from the locally integrated Parquet."""
    dataset = ds.dataset(path, format="parquet")
    frame = dataset.to_table(columns=["ano_epidemiologico", "semana_epidemiologica",
                                      "casos_total"]).to_pandas()
    all_year_cases = int(frame.casos_total.sum())
    weekly = (frame.groupby(["ano_epidemiologico", "semana_epidemiologica"], as_index=False)
              .casos_total.sum().rename(columns={"ano_epidemiologico": "year",
                                         "semana_epidemiologica": "week",
                                         "casos_total": "cases"}))
    if weekly.duplicated(["year", "week"]).any() or (weekly.cases < 0).any():
        raise ValueError("Invalid weekly onset reference")
    selected = weekly.loc[weekly.year.between(2008, 2025)].sort_values(
        ["year", "week"]).reset_index(drop=True)
    selected.attrs["all_year_cases"] = all_year_cases
    return selected


def build_onset_daily_series(observed: pd.Series, reference: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reconcile daily counts against observed weeks, retaining absent weeks as NA."""
    lookup = reference.set_index(["year", "week"])["cases"]
    days_parts = []
    week_rows = []
    for year in range(2008, 2026):
        first = week_one_start(year)
        weeks_in_year = (week_one_start(year + 1) - first).days // 7
        for week in range(1, weeks_in_year + 1):
            start = first + timedelta(weeks=week - 1)
            dates = pd.date_range(start, periods=7)
            key = (year, week)
            available = key in lookup.index and pd.notna(lookup.loc[key])
            counts = observed.reindex(dates, fill_value=0).to_numpy(dtype=float)
            if available:
                if int(counts.sum()) != int(lookup.loc[key]):
                    raise ValueError(f"{key}: daily sum {counts.sum():.0f} differs from Parquet {lookup.loc[key]}")
                weekly_count = int(lookup.loc[key])
            else:
                if counts.sum() != 0:
                    raise ValueError(f"{key}: onset cases exist in an absent reference week")
                counts[:] = np.nan
                weekly_count = np.nan
            days_parts.append(pd.DataFrame({"date": dates, "year": year, "week": week,
                                            "cases": counts, "missing_week": not available}))
            week_rows.append({"year": year, "week": week, "week_start": start,
                              "cases": weekly_count, "missing_week": not available})
    daily = pd.concat(days_parts, ignore_index=True)
    weekly = pd.DataFrame(week_rows)
    if daily.date.duplicated().any() or not daily.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Daily onset calendar is duplicated or discontinuous")
    if len(daily) != 6580 or len(weekly) != 940:
        raise AssertionError("Unexpected 2008–2025 epidemiological calendar length")
    return daily, weekly


def estimate_onset_rt(daily: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Run the shared renewal estimator on symptom-onset cases."""
    input_frame = daily.rename(columns={"cases": "notifications"})
    estimated = estimate_daily(input_frame, **kwargs)
    return estimated.rename(columns={"notifications": "cases"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--divipola", type=Path, default=DIVIPOLA)
    parser.add_argument("--symptom-parquet", type=Path, default=SYMPTOM_PARQUET)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--weekly-output", type=Path, default=WEEKLY_OUTPUT)
    args = parser.parse_args()
    observed, quality = onset_counts(args.raw_dir, args.divipola)
    reference = symptom_weekly_reference(args.symptom_parquet)
    if int(observed.sum()) != reference.attrs["all_year_cases"]:
        raise ValueError("Individual onset cases differ from the full symptom Parquet total")
    daily, weekly = build_onset_daily_series(observed, reference)
    result = estimate_onset_rt(daily)
    result["method"] = "epiestim_parametric_si_python_daily_symptom_onset"
    result["window_days"] = 14
    result["serial_interval_mean_days"] = 14.1
    result["serial_interval_sd_days"] = 2.4
    result["prior_mean"] = 5.0
    result["prior_sd"] = 5.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False, float_format="%.8f")
    weekly.to_csv(args.weekly_output, index=False, float_format="%.8f")
    print(quality.to_string(index=False))
    print(f"Daily rows: {len(result)}; missing weeks: {weekly.missing_week.sum()}; "
          f"posterior days: {result.rt.notna().sum()}; output: {args.output}")


if __name__ == "__main__":
    main()
