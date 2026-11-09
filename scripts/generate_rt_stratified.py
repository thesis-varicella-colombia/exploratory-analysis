"""Generate daily Rt by national age group and residence territory for both dates.

Age and geography are separate marginal analyses, not an age-by-territory cross.
The published national calendars define missing weeks; an absent local record in
an otherwise observed national week contributes zero. Individual dates and age
units use the same parsers and exclusions as the existing national analyses.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from generate_hospital_age_series import AGE_GROUPS, age_group
from rt_daily_sivigila import ALIASES, DIVIPOLA, RAW, ROOT, estimate_daily
from rt_symptom_sivigila import parse_onset_date

OUTPUT = ROOT / "docs/data_processed/numero_reproductivo/rt_stratified"
NATIONAL = {
    "notification": (ROOT / "docs/data_processed/numero_reproductivo/rt_national_daily.csv", "notifications"),
    "symptom": (ROOT / "docs/data_processed/numero_reproductivo/rt_national_symptom_daily.csv", "cases"),
}
AGE_LABELS = dict(zip(AGE_GROUPS, ["Menor de 1 año", "1–4 años", "5–14 años",
                                  "15–49 años", "50 años o más", "Sin edad registrada"]))
COLUMNS = ["ANO", "COD_EVE", "COD_DPTO_R", "COD_MUN_R", "AJUSTE", "FEC_NOT",
           "INI_SIN", "EDAD", "UNI_MED"]


def read_counts(raw_dir=RAW, divipola=DIVIPOLA):
    """One raw pass, retaining independent daily age and municipal marginals."""
    places = pd.read_csv(divipola, dtype=str, encoding="utf-8-sig")
    places["Código Municipio"] = places["Código Municipio"].str.strip().str.zfill(5)
    valid = set(places["Código Municipio"])
    if not set(ALIASES.values()) <= valid:
        raise ValueError("DIVIPOLA lacks geographic alias targets")
    counters = {method: defaultdict(Counter) for method in NATIONAL}
    quality = []
    for year in range(2007, 2026):
        audit = Counter()
        for chunk in pd.read_csv(raw_dir / f"Datos_{year}_831.csv", usecols=COLUMNS,
                                 dtype=str, keep_default_na=False, encoding="utf-8-sig",
                                 chunksize=50_000):
            if not pd.to_numeric(chunk.ANO, errors="coerce").eq(year).all() or not pd.to_numeric(
                    chunk.COD_EVE, errors="coerce").eq(831).all():
                raise ValueError(f"Unexpected source year or event in {year}")
            code = (chunk.COD_DPTO_R.str.strip().str.zfill(2)
                    + chunk.COD_MUN_R.str.strip().str.zfill(3)).replace(ALIASES)
            included = code.isin(valid) & ~chunk.AJUSTE.str.strip().str.upper().isin(["6", "D"])
            chunk = chunk.loc[included]
            audit["included"] += len(chunk)
            groups = age_group(chunk.EDAD, chunk.UNI_MED)
            notification = pd.to_datetime(chunk.FEC_NOT.str.extract(
                r"^(\d{1,2}/\d{1,2}/\d{4})", expand=False), format="%d/%m/%Y", errors="coerce")
            symptom = parse_onset_date(chunk.INI_SIN, year)
            for method, dates in [("notification", notification), ("symptom", symptom)]:
                audit[f"{method}_missing_date"] += int(dates.isna().sum())
                frame = pd.DataFrame({"date": dates, "age": groups, "municipality": code.loc[included]}).dropna(subset=["date"])
                for dimension in ["age", "municipality"]:
                    counts = frame.groupby([dimension, "date"]).size()
                    for (key, day), count in counts.items():
                        counters[method][f"{dimension}_{key}"][day] += int(count)
        quality.append({"source_year": year, **audit})
        print(f"Read {year}", flush=True)
    return counters, places, quality


def daily_frame(counts, reference):
    """Apply the national missingness mask without imputing missing weeks."""
    days = pd.DatetimeIndex(reference.date)
    observed = pd.Series(counts, dtype=float).reindex(days, fill_value=0).to_numpy(copy=True)
    missing = reference.missing_week.to_numpy(dtype=bool)
    if observed[missing].sum() != 0:
        raise ValueError("Local cases found in a missing national week")
    observed[missing] = np.nan
    return pd.DataFrame({"date": days, "year": reference.year, "week": reference.week,
                         "notifications": observed, "missing_week": missing})


def estimate_stratum(frame):
    """Use the national estimator, withholding windows with no exposure history."""
    result = estimate_daily(frame)
    result["window_cases"] = result.notifications.rolling(14, min_periods=14).sum()
    exposure = result.infectiousness.rolling(14, min_periods=14).sum()
    # A completely unexposed window only reproduces the Gamma prior, not a
    # data-supported estimate. Tiny numerical residuals count as zero.
    result.loc[exposure.le(1e-12), ["rt", "rt_lower_95", "rt_upper_95"]] = np.nan
    return result


def nullable(values, digits=6):
    return [None if not np.isfinite(value) else round(float(value), digits) for value in values]


def write_series(path, result, count_field="notifications"):
    """Column arrays share the manifest calendar; gzip is decoded on demand."""
    window = result[count_field].rolling(14, min_periods=14).sum()
    payload = {"count": nullable(result[count_field], 0), "window_cases": nullable(window, 0),
               **{field: nullable(result[field]) for field in ["rt", "rt_lower_95", "rt_upper_95"]}}
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(filename=str(path), mode="wb", mtime=0) as target:
        target.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode())
    return {"cases": int(result[count_field].sum()), "estimated_days": int(result.rt.notna().sum())}


def validate_marginals(counts, reference, count_field):
    for dimension in ["age", "municipality"]:
        total = Counter()
        for key, observed in counts.items():
            if key.startswith(dimension + "_"):
                total.update(observed)
        actual = daily_frame(total, reference).notifications.to_numpy()
        np.testing.assert_allclose(actual, reference[count_field], equal_nan=True,
                                   err_msg=f"{dimension}: daily counts differ from national reference")


def validate_notification_ages(counts, reference):
    expected = pd.read_csv(ROOT / "docs/data_processed/evolucion_semanal/weekly_series_2007_2025.csv")
    for key in AGE_LABELS:
        if key == "unknown":
            continue
        frame = daily_frame(counts.get(f"age_{key}", {}), reference)
        observed = frame.groupby(["year", "week"]).notifications.sum(min_count=1)
        target = expected.loc[expected.age_group.eq(key) & expected.year.between(2008, 2025)].set_index(["year", "week"]).notifications
        np.testing.assert_allclose(observed, target.reindex(observed.index), equal_nan=True,
                                   err_msg=f"Weekly age counts differ for {key}")


def generate(output=OUTPUT, raw_dir=RAW, divipola=DIVIPOLA):
    counts_by_method, places, quality = read_counts(raw_dir, divipola)
    municipalities = [{"id": f"municipality_{row['Código Municipio']}",
                       "code": row["Código Municipio"], "name": row["Nombre Municipio"],
                       "department": row["Código Departamento"].zfill(2)}
                      for row in places.to_dict("records")]
    departments = [{"id": f"department_{code.zfill(2)}", "code": code.zfill(2), "name": name}
                   for code, name in places[["Código Departamento", "Nombre Departamento"]].drop_duplicates().itertuples(index=False, name=None)]
    series = [{"id": "national", "name": "Colombia · todas las edades", "dimension": "national"},
              *[{"id": f"age_{key}", "name": label, "dimension": "age"} for key, label in AGE_LABELS.items()],
              *[{**row, "dimension": "department"} for row in departments],
              *[{**row, "dimension": "municipality"} for row in municipalities]]
    manifest = {"version": 1, "method": {"window_days": 14, "serial_interval_mean_days": 14.1,
                  "serial_interval_sd_days": 2.4, "prior_mean": 5, "prior_sd": 5,
                  "zero_exposure_windows": "withheld", "missingness": "national calendar"},
                "series": series, "calendars": {}, "quality": quality}
    for method, (national_path, count_field) in NATIONAL.items():
        reference = pd.read_csv(national_path, parse_dates=["date"])
        counts = counts_by_method[method]
        validate_marginals(counts, reference, count_field)
        if method == "notification":
            validate_notification_ages(counts, reference)
        # Departments are sums of their municipalities; rates or Rt are never averaged.
        for municipality in municipalities:
            counts[f"department_{municipality['department']}"].update(counts.get(municipality["id"], {}))
        manifest["calendars"][method] = reference.assign(date=reference.date.dt.strftime("%Y-%m-%d"))[
            ["date", "year", "week", "missing_week"]].to_dict("list")
        for index, stratum in enumerate(series):
            key = stratum["id"]
            if key == "national":
                result = reference
                field = count_field
            else:
                result = estimate_stratum(daily_frame(counts.get(key, {}), reference))
                field = "notifications"
            summary = write_series(output / method / f"{key}.json.gz", result, field)
            stratum[method] = summary
            if index % 100 == 0:
                print(f"{method}: {index + 1}/{len(series)} series", flush=True)
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Generated {len(series)} series per date source in {output}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--raw-dir", type=Path, default=RAW)
    parser.add_argument("--divipola", type=Path, default=DIVIPOLA)
    args = parser.parse_args()
    generate(args.output, args.raw_dir, args.divipola)
