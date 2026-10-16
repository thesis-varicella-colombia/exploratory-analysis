"""Generate the annual CSV for the national charts published in docs/.

Requires Python 3 and the `duckdb` command-line application.
Usage: python3 scripts/generate_annual_series.py
"""

import csv
import io
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data/sivigila_integrado_semanal_municipal.parquet"
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/annual_series_2007_2023.csv"
YEARS = range(2007, 2024)
OFFICIAL_2007 = 69695  # Varicella protocol, section 5.1.2, p. 4; source in data/README.md.


def read_notifications():
    query = f"""
        SELECT ano_epidemiologico AS year,
               SUM(casos_total) AS notifications,
               COUNT(DISTINCT codigo_municipio) AS reporting_entities
        FROM read_parquet('{PARQUET}/*.parquet')
        WHERE ano_epidemiologico BETWEEN 2007 AND 2023
        GROUP BY 1 ORDER BY 1
    """
    result = subprocess.run(
        ["duckdb", "-csv", "-c", query],
        check=True,
        capture_output=True,
        text=True,
    )
    return {int(row["year"]): row for row in csv.DictReader(io.StringIO(result.stdout))}


def read_population():
    totals = defaultdict(int)
    entities = defaultdict(int)
    zero_population_entities = defaultdict(int)
    seen = set()
    with POPULATION.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            year = int(row["ano_epidemiologico"])
            if year not in YEARS:
                continue
            key = (year, row["codigo_municipio"])
            if key in seen:
                raise ValueError(f"Duplicate population key: {key}")
            seen.add(key)
            value = int(row["poblacion_total"])
            if value < 0:
                raise ValueError(f"Negative population: {key}")
            totals[year] += value
            entities[year] += 1
            if value == 0:
                zero_population_entities[year] += 1
    return totals, entities, zero_population_entities


def main():
    notifications = read_notifications()
    population, population_entities, zero_population_entities = read_population()
    expected = set(YEARS)
    if set(notifications) != expected or set(population) != expected:
        raise ValueError("Missing years in notifications or population")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow([
            "year", "notifications", "reporting_entities", "population_entities",
            "zero_population_entities", "population", "notification_rate_per_100k",
            "official_2007_cases",
        ])
        for year in YEARS:
            count = int(notifications[year]["notifications"])
            writer.writerow([
                year,
                count,
                notifications[year]["reporting_entities"],
                population_entities[year],
                zero_population_entities[year],
                population[year],
                f"{count / population[year] * 100_000:.2f}",
                OFFICIAL_2007 if year == 2007 else "",
            ])
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
