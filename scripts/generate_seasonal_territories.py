"""Publish weekly age-specific rates by territory and case date for section 5A.

Run with .venv/bin/python scripts/generate_seasonal_territories.py.
"""

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import pyarrow.dataset as ds


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/data_processed/estacionalidad/seasonal_territories"
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
CATALOG = ROOT / "docs/data_processed/numero_reproductivo/rt_stratified/manifest.json"
GROUPS = {
    "all": ("casos_total", "poblacion_total"),
    "5_14": ("casos_5_14", "poblacion_5_14"),
    "15_49": ("casos_15_49", "poblacion_15_49"),
}


def calendar():
    notification = ROOT / "docs/data_processed/evolucion_semanal/weekly_series_2007_2025.csv"
    symptom = ROOT / "docs/data_processed/numero_reproductivo/weekly_series_symptom_2008_2025.csv"
    observed = {}
    with notification.open(newline="", encoding="utf-8") as source:
        observed["notification"] = {(int(row["year"]), int(row["week"]))
                                    for row in csv.DictReader(source)
                                    if row["age_group"] == "all" and 2008 <= int(row["year"]) <= 2025
                                    and row["notifications"] != ""}
    with symptom.open(newline="", encoding="utf-8") as source:
        observed["symptom"] = {(int(row["year"]), int(row["week"]))
                               for row in csv.DictReader(source) if row["missing_week"] == "False"}
    weeks = sorted(observed["notification"] | observed["symptom"])
    return weeks, observed


def populations():
    values = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    seen = set()
    with POPULATION.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            year = int(row["ano_epidemiologico"])
            if not 2008 <= year <= 2025:
                continue
            code = row["codigo_municipio"].zfill(5)
            if (code, year) in seen:
                raise ValueError(f"Duplicate population: {code}, {year}")
            seen.add((code, year))
            counts = [int(row[column]) for _, column in GROUPS.values()]
            if any(value < 0 for value in counts):
                raise ValueError(f"Negative population: {code}, {year}")
            for entity in ("national", f"department_{code[:2]}", f"municipality_{code}"):
                totals = values[entity][year]
                for i, count in enumerate(counts):
                    totals[i] += count
    return values


def cases(method):
    folder = ROOT / f"data/sivigila_integrado_{method}_semanal_municipal.parquet"
    columns = ["codigo_municipio", "ano_epidemiologico", "semana_epidemiologica",
               *(column for column, _ in GROUPS.values())]
    table = ds.dataset(folder, format="parquet").to_table(columns=columns)
    values = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    for row in table.to_pylist():
        year, week = row["ano_epidemiologico"], row["semana_epidemiologica"]
        if not 2008 <= year <= 2025 or not 1 <= week <= 53:
            continue
        code = str(row["codigo_municipio"]).zfill(5)
        counts = [int(row[column] or 0) for column, _ in GROUPS.values()]
        if any(count < 0 for count in counts):
            raise ValueError(f"Negative cases: {method}, {code}, {year}, {week}")
        for entity in ("national", f"department_{code[:2]}", f"municipality_{code}"):
            totals = values[entity][(year, week)]
            for i, count in enumerate(counts):
                totals[i] += count
    return values


def generate():
    weeks, observed = calendar()
    population = populations()
    counts = {method: cases(method) for method in ("notification", "symptom")}
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entities = [{key: row[key] for key in ("id", "name", "dimension", "code", "department") if key in row}
                for row in catalog["series"] if row["dimension"] in ("national", "department", "municipality")]
    if len(entities) != 1156 or len(weeks) < 900:
        raise ValueError("Incomplete entity catalog or weekly calendar")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {"version": 1, "weeks": weeks, "groups": list(GROUPS), "entities": entities,
                "source": "integrated weekly municipality counts; municipal annual population"}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for entity in entities:
        entity_id = entity["id"]
        payload = {"id": entity_id, "series": {}}
        for method in ("notification", "symptom"):
            series = {group: [] for group in GROUPS}
            for year, week in weeks:
                known = (year, week) in observed[method]
                numerator = counts[method][entity_id].get((year, week), (0, 0, 0))
                denominator = population[entity_id].get(year, (0, 0, 0))
                for index, group in enumerate(GROUPS):
                    series[group].append(round(numerator[index] / denominator[index] * 100_000, 4)
                                         if known and denominator[index] > 0 else None)
            payload["series"][method] = series
        with gzip.GzipFile(filename=str(OUTPUT / f"{entity_id}.json.gz"), mode="wb", mtime=0) as target:
            target.write(json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8"))
    print(f"Published {len(entities)} territories and {len(weeks)} weeks in {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    generate()
