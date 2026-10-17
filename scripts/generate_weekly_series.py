"""Generate the national weekly series published in docs/.

Requires Python 3 and the `duckdb` command-line application.
Usage: python3 scripts/generate_weekly_series.py
"""

import csv
import io
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data/sivigila_integrado_semanal_municipal.parquet"
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/weekly_series_2007_2025.csv"
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
               semana_epidemiologica AS week,
               SUM(casos_total) AS total,
               {case_columns},
               SUM(casos_edad_desconocida) AS unknown
        FROM read_parquet('{PARQUET}/*.parquet')
        WHERE ano_epidemiologico BETWEEN 2007 AND 2025
        GROUP BY 1, 2 ORDER BY 1, 2
    """
    result = subprocess.run(
        ["duckdb", "-csv", "-c", query],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        (int(row["year"]), int(row["week"])): row
        for row in csv.DictReader(io.StringIO(result.stdout))
    }


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
            total = int(row["poblacion_total"])
            if total < 0:
                raise ValueError(f"Negative population: {key}, total")
            totals[year]["all"] += total
    return totals


def main():
    notifications = read_notifications()
    population = read_population()
    if {year for year, _ in notifications} != set(YEARS) or set(population) != set(YEARS):
        raise ValueError("Missing years in notifications or population")
    if any(week < 1 or week > 53 for _, week in notifications):
        raise ValueError("Week outside the expected epidemiological range")
    groups = ("all", *(age_group for age_group, _, _ in AGE_GROUPS))
    if any(population[year][group] <= 0 for year in YEARS for group in groups):
        raise ValueError("Missing national population for a year or age group")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    position = 0
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow([
            "year", "week", "week_position", "age_group", "notifications", "population",
            "notification_rate_per_100k",
        ])
        for year in YEARS:
            last_week = max(week for observed_year, week in notifications if observed_year == year)
            for week in range(1, last_week + 1):
                position += 1
                source = notifications.get((year, week))
                if source is not None:
                    age_total = sum(int(source[group]) for group in groups if group != "all")
                    if age_total + int(source["unknown"]) != int(source["total"]):
                        raise ValueError(f"Age groups do not sum to weekly notifications: {year}, {week}")
                for group in groups:
                    count = None if source is None else int(source["total" if group == "all" else group])
                    denominator = population[year][group]
                    writer.writerow([
                        year, week, position, group,
                        "" if count is None else count,
                        denominator,
                        "" if count is None else f"{count / denominator * 100_000:.4f}",
                    ])
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
