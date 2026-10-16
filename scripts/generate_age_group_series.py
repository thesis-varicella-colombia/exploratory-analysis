"""Generate annual notification counts and rates by age group for the website.

Requires Python 3 and the `duckdb` command-line application.
Usage: python3 scripts/generate_age_group_series.py
"""

import csv
import io
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data/sivigila_integrado_semanal_municipal.parquet"
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/age_group_series_2007_2025.csv"
YEARS = range(2007, 2026)
AGE_GROUPS = (
    ("under_1", "casos_menor_1", "poblacion_menor_1"),
    ("1_4", "casos_1_4", "poblacion_1_4"),
    ("5_14", "casos_5_14", "poblacion_5_14"),
    ("15_49", "casos_15_49", "poblacion_15_49"),
    ("50_plus", "casos_50_mas", "poblacion_50_mas"),
)


def read_notifications():
    case_columns = ",\n               ".join(
        f'SUM({case_column}) AS "{age_group}"'
        for age_group, case_column, _ in AGE_GROUPS
    )
    query = f"""
        SELECT ano_epidemiologico AS year,
               SUM(casos_total) AS total_notifications,
               {case_columns},
               SUM(casos_edad_desconocida) AS unknown
        FROM read_parquet('{PARQUET}/*.parquet')
        WHERE ano_epidemiologico BETWEEN 2007 AND 2025
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
    totals = defaultdict(lambda: defaultdict(int))
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
            for age_group, _, population_column in AGE_GROUPS:
                value = int(row[population_column])
                if value < 0:
                    raise ValueError(f"Negative population: {key}, {age_group}")
                totals[year][age_group] += value
    return totals


def main():
    notifications = read_notifications()
    population = read_population()
    expected = set(YEARS)
    if set(notifications) != expected or set(population) != expected:
        raise ValueError("Missing years in notifications or population")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(["year", "age_group", "notifications", "population", "notification_rate_per_100k"])
        for year in YEARS:
            source = notifications[year]
            age_total = sum(int(source[age_group]) for age_group, _, _ in AGE_GROUPS)
            unknown = int(source["unknown"])
            if age_total + unknown != int(source["total_notifications"]):
                raise ValueError(f"Age groups do not sum to annual notifications: {year}")
            for age_group, _, _ in AGE_GROUPS:
                count = int(source[age_group])
                denominator = population[year][age_group]
                if denominator <= 0:
                    raise ValueError(f"Missing age-group population: {year}, {age_group}")
                writer.writerow([
                    year, age_group, count, denominator,
                    f"{count / denominator * 100_000:.2f}",
                ])
            writer.writerow([year, "unknown", unknown, "", ""])
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
