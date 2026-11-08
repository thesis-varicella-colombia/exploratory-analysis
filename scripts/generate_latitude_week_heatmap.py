"""Generate department-week rates and z scores for the latitude heatmap.

Requires Python 3, shapely, pyproj, and the DuckDB CLI.
Usage: python3 scripts/generate_latitude_week_heatmap.py
"""

import csv
import io
import json
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely import transform
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data/sivigila_integrado_semanal_municipal.parquet"
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
BOUNDARIES = ROOT / "docs/data_processed/municipal_boundaries_dane.geojson"
OUTPUT = ROOT / "docs/data_processed/latitude_week_heatmap.csv"
PERIODS = {
    "2008–2014": range(2008, 2015),
    "2016–2019": range(2016, 2020),
    "2022–2025": range(2022, 2026),
    **{str(year): (year,) for year in range(2007, 2026)},
}
YEARS = {year for years in PERIODS.values() for year in years}
EXCLUDED_CODES = {"88"}  # The oceanic archipelago lies north of the mainland gradient.
DISPLAY_NAMES = {
    "11": "Bogotá D.C.",
    "88": "San Andrés y Providencia",
    "76": "Valle del Cauca",
    "54": "Norte de Santander",
}


def read_departments():
    with BOUNDARIES.open(encoding="utf-8") as source:
        features = json.load(source)["features"]
    project = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True).transform
    unproject = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True).transform
    area_by_code = defaultdict(float)
    x_by_code = defaultdict(float)
    y_by_code = defaultdict(float)
    names = {}
    for feature in features:
        props = feature["properties"]
        code = props["code"][:2]
        if code in EXCLUDED_CODES:
            continue
        name = props["department"]
        if code in names and names[code] != name:
            raise ValueError(f"Different department names for {code}")
        names[code] = name
        geometry = transform(shape(feature["geometry"]), project, interleaved=False)
        area = geometry.area
        if area <= 0:
            raise ValueError(f"Empty geometry for {props['code']}")
        area_by_code[code] += area
        x_by_code[code] += area * geometry.centroid.x
        y_by_code[code] += area * geometry.centroid.y
    result = {}
    for code, name in names.items():
        _, latitude = unproject(
            x_by_code[code] / area_by_code[code], y_by_code[code] / area_by_code[code]
        )
        label = DISPLAY_NAMES.get(code, name.title())
        if "," in label:
            raise ValueError(f"Comma in display label: {label}")
        result[code] = (label, latitude)
    if len(result) != 32:
        raise ValueError(f"Expected 32 mainland departments/districts, found {len(result)}")
    return result


def read_population():
    totals = defaultdict(int)
    seen = set()
    with POPULATION.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            year = int(row["ano_epidemiologico"])
            if year not in YEARS:
                continue
            code = row["codigo_municipio"]
            if code[:2] in EXCLUDED_CODES:
                continue
            key = (year, code)
            if key in seen:
                raise ValueError(f"Duplicate population key: {key}")
            seen.add(key)
            population = int(row["poblacion_total"])
            if population < 0:
                raise ValueError(f"Negative population: {key}")
            totals[year, code[:2]] += population
    return totals


def read_notifications():
    query = f"""
        SELECT ano_epidemiologico AS year,
               semana_epidemiologica AS week,
               LEFT(codigo_municipio, 2) AS department_code,
               SUM(casos_total) AS notifications
        FROM read_parquet('{PARQUET}/*.parquet')
        WHERE ano_epidemiologico BETWEEN 2007 AND 2025
          AND semana_epidemiologica BETWEEN 1 AND 52
        GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
    """
    result = subprocess.run(
        ["duckdb", "-csv", "-c", query], check=True, capture_output=True, text=True
    )
    notifications = {}
    observed_weeks = set()
    for row in csv.DictReader(io.StringIO(result.stdout)):
        year = int(row["year"])
        if year not in YEARS:
            continue
        week = int(row["week"])
        code = row["department_code"]
        if code in EXCLUDED_CODES:
            continue
        key = (year, week, code)
        if key in notifications:
            raise ValueError(f"Duplicate notification key: {key}")
        notifications[key] = int(row["notifications"])
        observed_weeks.add((year, week))
    return notifications, observed_weeks


def main():
    departments = read_departments()
    population = read_population()
    notifications, observed_weeks = read_notifications()
    if {code for _, code in population} != set(departments):
        raise ValueError("Population and geometry department codes differ")
    if {code for _, _, code in notifications} - set(departments):
        raise ValueError("Notifications contain unknown department codes")
    if any(population.get((year, code), 0) <= 0 for year in YEARS for code in departments):
        raise ValueError("Missing positive department population")
    if any(not any((year, week) in observed_weeks for week in range(1, 53)) for year in YEARS):
        raise ValueError("Year without observed weeks")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow([
            "period", "department_code", "department", "latitude", "week", "mean_rate_per_100k",
            "department_mean", "sd_rate", "z_score", "years_with_data",
        ])
        for period, years in PERIODS.items():
            for code, (name, latitude) in sorted(departments.items()):
                weekly_rates = []
                for week in range(1, 53):
                    rates = [
                        notifications.get((year, week, code), 0)
                        / population[year, code] * 100_000
                        for year in years if (year, week) in observed_weeks
                    ]
                    weekly_rates.append((week, statistics.fmean(rates) if rates else None, len(rates)))
                observed_rates = [rate for _, rate, _ in weekly_rates if rate is not None]
                department_mean = statistics.fmean(observed_rates)
                sd_rate = statistics.pstdev(observed_rates)
                for week, mean_rate, count in weekly_rates:
                    writer.writerow([
                        period, code, name, f"{latitude:.5f}", week,
                        f"{mean_rate:.6f}" if mean_rate is not None else "",
                        f"{department_mean:.6f}", f"{sd_rate:.6f}",
                        f"{(mean_rate - department_mean) / sd_rate:.6f}"
                        if mean_rate is not None and sd_rate > 0 else "",
                        count,
                    ])
    print(f"Generated: {OUTPUT.relative_to(ROOT)} ({len(PERIODS) * len(departments) * 52} rows)")


if __name__ == "__main__":
    main()
