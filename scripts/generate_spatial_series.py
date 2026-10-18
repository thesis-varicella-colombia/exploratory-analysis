"""Generate municipal annual and period rates for the Leaflet map.

Requires Python 3 and the DuckDB CLI.
Usage: python3 scripts/generate_spatial_series.py
"""

import csv
import io
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data/sivigila_integrado_semanal_municipal.parquet"
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/spatial_series_2008_2025.csv"
YEARS = range(2008, 2026)
PERIODS = {
    "2008-2014": range(2008, 2015),
    "2015-2019": range(2015, 2020),
    "2020-2021": range(2020, 2022),
    "2022-2025": range(2022, 2026),
}


def read_notifications():
    query = f"""
        SELECT ano_epidemiologico AS year, codigo_municipio AS code,
               SUM(casos_total) AS notifications
        FROM read_parquet('{PARQUET}/*.parquet')
        WHERE ano_epidemiologico BETWEEN 2008 AND 2025
        GROUP BY 1, 2 ORDER BY 1, 2
    """
    result = subprocess.run(
        ["duckdb", "-csv", "-c", query], check=True, capture_output=True, text=True
    )
    return {
        (int(row["year"]), row["code"]): int(row["notifications"])
        for row in csv.DictReader(io.StringIO(result.stdout))
    }


def read_population():
    population = {}
    with POPULATION.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            year = int(row["ano_epidemiologico"])
            if year not in YEARS:
                continue
            key = (year, row["codigo_municipio"])
            if key in population:
                raise ValueError(f"Duplicate population key: {key}")
            value = int(row["poblacion_total"])
            if value < 0:
                raise ValueError(f"Negative population: {key}")
            population[key] = value
    return population


def rate(notifications, population):
    return f"{notifications / population * 100_000:.4f}" if population > 0 else ""


def main():
    notifications = read_notifications()
    population = read_population()
    unmatched = set(notifications) - set(population)
    if {year for year, _ in population} != set(YEARS):
        raise ValueError("Missing years in population")

    annual = defaultdict(dict)
    for (year, code), people in sorted(population.items()):
        cases = notifications.get((year, code), 0)
        annual[code][year] = (cases, people)
    for year, code in sorted(unmatched):
        annual[code][year] = (notifications[(year, code)], 0)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(["period", "code", "notifications", "population_years", "years", "rate_per_100k"])
        for year in YEARS:
            for code in sorted(annual):
                if year not in annual[code]:
                    continue
                cases, people = annual[code][year]
                writer.writerow([str(year), code, cases, people, 1, rate(cases, people)])
        for period, years in PERIODS.items():
            for code in sorted(annual):
                available = [annual[code][year] for year in years if year in annual[code]]
                if not available:
                    continue
                cases = sum(row[0] for row in available)
                people_years = sum(row[1] for row in available)
                period_rate = "" if any(row[0] > 0 and row[1] == 0 for row in available) else rate(cases, people_years)
                writer.writerow([period, code, cases, people_years, len(available), period_rate])
    if unmatched:
        print(f"Notifications without population for {len(unmatched)} municipality-years; rates left blank")
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
