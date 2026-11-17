"""Build compact municipal climate map frames from weekly Parquet sources.

Run: .venv/bin/python scripts/generate_climate_map.py --source-root ../data-processing/data/processed
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/data_processed/heterogeneidad_espacial/climate_map"
YEARS = range(2007, 2026)
PERIODS = {
    "2007-2014": range(2007, 2015),
    "2015-2019": range(2015, 2020),
    "2020-2021": range(2020, 2022),
    "2022-2025": range(2022, 2026),
}
BASELINE_YEARS = range(2007, 2020)
MIN_SOURCE_COVERAGE = 0.95
MIN_FRAME_COVERAGE = 0.80
SOURCES = {
    "precip_chirps": (
        "chirps_precipitation/chirps_precipitation_weekly_municipal_sat_{year}.parquet",
        "precipitacion_total_mm", "fraccion_area_con_datos", "mm/semana",
    ),
    "precip_era5": (
        "climate/precipitation/precipitation_weekly_municipal_{year}.parquet",
        "precipitacion_total_mm", "fraccion_area_con_datos", "mm/semana",
    ),
    "spec_humidity_era5": (
        "climate/humidity/humidity_weekly_municipal_{year}.parquet",
        "humedad_especifica_media_g_kg",
        "fraccion_area_con_datos_humedad_especifica_media_g_kg", "g/kg",
    ),
    "rel_humidity_era5": (
        "climate/humidity/humidity_weekly_municipal_{year}.parquet",
        "humedad_relativa_media_pct",
        "fraccion_area_con_datos_humedad_relativa_media_pct", "%",
    ),
    "temp_era5": (
        "climate/temperature/temperature_weekly_municipal_{year}.parquet",
        "temperatura_media_c", "fraccion_area_con_datos", "°C",
    ),
}


def read_year(source_root, variable, year):
    pattern, value_column, coverage_column, _ = SOURCES[variable]
    path = source_root / pattern.format(year=year)
    columns = ["codigo_municipio", "ano_epidemiologico", "semana_epidemiologica",
               value_column, coverage_column]
    data = pd.read_parquet(path, columns=columns)
    data["codigo_municipio"] = data.codigo_municipio.astype(str).str.zfill(5)
    if not data.ano_epidemiologico.eq(year).all():
        raise ValueError(f"Unexpected year in {path}")
    if data.duplicated(["codigo_municipio", "semana_epidemiologica"]).any():
        raise ValueError(f"Duplicate municipality-week in {path}")
    if not data[coverage_column].dropna().between(0, 1).all():
        raise ValueError(f"Invalid source coverage in {path}")
    total_weeks = int(data.semana_epidemiologica.nunique())
    if total_weeks not in (52, 53):
        raise ValueError(f"Unexpected weekly calendar in {path}: {total_weeks}")
    values = pd.to_numeric(data[value_column], errors="coerce")
    valid = data[coverage_column].ge(MIN_SOURCE_COVERAGE) & np.isfinite(values)
    if variable.startswith("precip_"):
        valid &= values.ge(0)
    data["valid_value"] = values.where(valid)
    grouped = data.groupby("codigo_municipio").valid_value.agg(["sum", "count"])
    return grouped, total_weeks, set(data.codigo_municipio)


def rounded(value):
    return round(float(value), 4) if value is not None and np.isfinite(value) else None


def build_variable(source_root, variable):
    yearly = {}
    codes = set()
    calendars = {}
    for year in YEARS:
        grouped, total_weeks, year_codes = read_year(source_root, variable, year)
        yearly[year] = grouped
        calendars[year] = total_weeks
        codes.update(year_codes)
    codes = sorted(codes)
    rows = []
    raw_by_horizon = {}
    def aggregate_years(years):
        total_weeks = sum(calendars[year] for year in years)
        sums = np.zeros(len(codes))
        counts = np.zeros(len(codes), dtype=int)
        for year in years:
            frame = yearly[year].reindex(codes).fillna(0)
            sums += frame["sum"].to_numpy(dtype=float)
            counts += frame["count"].to_numpy(dtype=int)
        means = np.divide(sums, counts, out=np.full(len(codes), np.nan), where=counts > 0)
        return means, counts, total_weeks

    horizons = list(PERIODS.items()) + [(str(year), (year,)) for year in YEARS]
    for horizon, years in horizons:
        raw_by_horizon[horizon] = aggregate_years(years)
    baseline_means, baseline_counts, baseline_total = aggregate_years(BASELINE_YEARS)
    baseline_valid = baseline_counts / baseline_total >= MIN_FRAME_COVERAGE
    for horizon, (means, counts, total_weeks) in raw_by_horizon.items():
        current_valid = counts / total_weeks >= MIN_FRAME_COVERAGE
        for index, code in enumerate(codes):
            baseline = baseline_means[index] if baseline_valid[index] else np.nan
            anomaly = means[index] - baseline if current_valid[index] and baseline_valid[index] else np.nan
            rows.append([code, horizon, int(counts[index]), int(total_weeks),
                         rounded(means[index]), rounded(baseline), rounded(anomaly)])
    absolute = [row[4] for row in rows if row[4] is not None and
                row[2] / row[3] >= MIN_FRAME_COVERAGE]
    anomalies = [row[6] for row in rows if row[6] is not None]
    if not absolute or not anomalies:
        raise ValueError(f"No valid map values for {variable}")
    absolute_bounds = np.percentile(absolute, [2, 98])
    anomaly_bounds = np.percentile(anomalies, [2, 98])
    anomaly_limit = max(abs(anomaly_bounds[0]), abs(anomaly_bounds[1]))
    return {
        "schema_version": 1,
        "variable": variable,
        "unit": SOURCES[variable][3],
        "minimum_coverage": MIN_FRAME_COVERAGE,
        "source_week_coverage": MIN_SOURCE_COVERAGE,
        "baseline_horizon": "2007-2019",
        "scale_bounds": {
            "absolute": [rounded(absolute_bounds[0]), rounded(absolute_bounds[1])],
            "anomaly": [rounded(-anomaly_limit), rounded(anomaly_limit)],
        },
        "columns": ["code", "horizon", "valid_weeks", "total_weeks", "mean_value",
                    "baseline_2007_2019", "anomaly"],
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for variable in SOURCES:
        payload = build_variable(args.source_root, variable)
        path = OUTPUT_DIR / f"{variable}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False,
                                   separators=(",", ":")), encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {len(payload['rows'])} rows")


if __name__ == "__main__":
    main()
