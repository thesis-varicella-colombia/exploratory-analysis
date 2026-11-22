"""Annual coverage and age-specific notified incidence on the map geography.

Keep the PAI analysis year already shifted by one; never apply a second lag.
Missing population stays missing; absent notification rows use the panel's zero
convention and remain explicitly flagged. Coverage does not vary by incidence age.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from generate_age_standardized_sir import (
    CASES, POPULATION, GEOMETRY, AGE_GROUPS, CASE_COLUMNS, POPULATION_COLUMNS,
    harmonize_age_population,
)
from municipal_coverage import normalize_codes

ROOT = Path(__file__).resolve().parents[1]
METRICS = ["reference", "administrative", "survivors"]
DETAIL_FIELDS = ["doses", "reference_population", "pai_target_population", "survivor_population"]
EB_GROUPS = ["all", "under_1", "1_4", "5_14", "15_49", "50_plus"]

OUTPUT = ROOT / "docs/data_processed/cobertura_vacunacion/coverage_incidence"
EB_SOURCE = ROOT / "docs/data_processed/cobertura_vacunacion/empirical_bayes/municipal_incidence_eb.csv"


def load_eb():
    """Map (code, age_group) -> {year: (eb_global, eb_local)} from the annual EB rows."""
    eb = pd.read_csv(EB_SOURCE, dtype={"code": str})
    eb = eb[eb.scope.eq("annual")].copy()
    eb["year"] = eb.year.astype(int)
    lookup = {}
    for (code, age), block in eb.groupby(["code", "age_group"]):
        lookup[(code, age)] = {row.year: (row.rate_eb, row.rate_eb_local) for row in block.itertuples()}
    return lookup


def _clean(value):
    return round(float(value), 8) if pd.notna(value) and np.isfinite(value) else None


def eb_series(lookup, code, age, years, local=False):
    """EB rate per year for one municipality and age group; None where absent."""
    per_year = lookup.get((code, age), {})
    return [_clean(per_year[y][1 if local else 0]) if y in per_year else None for y in years]


def annual_incidence(population, notifications, codes, years):
    pop = harmonize_age_population(population)
    notifications = notifications.copy()
    notifications["codigo_municipio"] = normalize_codes(notifications.codigo_municipio)
    fields = ["casos_total", "casos_edad_desconocida", *CASE_COLUMNS.values()]
    cases = notifications.groupby(["codigo_municipio", "ano_epidemiologico"], as_index=False)[fields].sum()
    keys = pd.MultiIndex.from_product([sorted(codes), years], names=["codigo_municipio", "ano_epidemiologico"]).to_frame(index=False)
    panel = keys.merge(pop, how="left", validate="one_to_one").merge(
        cases, how="left", validate="one_to_one", indicator=True)
    panel["notification_record_present"] = panel.pop("_merge").eq("both")
    panel[fields] = panel[fields].fillna(0)
    if not np.array_equal(panel[list(CASE_COLUMNS.values())].sum(axis=1) + panel.casos_edad_desconocida, panel.casos_total):
        raise ValueError("Age counts do not reconcile with total notifications")
    return panel


def values(series):
    return [round(float(x), 8) if pd.notna(x) and np.isfinite(x) else None for x in series]


def aggregate_series(panel, coverage, years):
    """Pool matched numerators/denominators; never average municipal incidence."""
    ages = ["all", *AGE_GROUPS]
    result = dict(code="all", years=years, aggregate=True,
                  incidence={age: [] for age in ages}, incidence_eb={age: [] for age in ages},
                  incidence_eb_local={age: [] for age in ages},
                  cases={age: [] for age in ages},
                  population={age: [] for age in ages}, coverage={},
                  incidence_entities={age: [] for age in ages},
                  missing_notification_entities={age: [] for age in ages},
                  notification_record_present=[], coverage_entities={}, coverage_details={})
    for year in years:
        selected = panel[panel.ano_epidemiologico.eq(year)]
        result["notification_record_present"].append(bool(selected.notification_record_present.any()))
        for age in ages:
            population = selected[list(POPULATION_COLUMNS.values())].sum(axis=1, min_count=5) if age == "all" else selected[POPULATION_COLUMNS[age]]
            cases = selected.casos_total if age == "all" else selected[CASE_COLUMNS[age]]
            valid = population.gt(0) & np.isfinite(population) & np.isfinite(cases)
            n = int(valid.sum())
            total_population, total_cases = population[valid].sum(), cases[valid].sum()
            result["incidence_entities"][age].append(n)
            result["missing_notification_entities"][age].append(int((valid & ~selected.notification_record_present).sum()))
            result["population"][age].append(float(total_population) if n else None)
            result["cases"][age].append(float(total_cases) if n else None)
            pooled = round(100000 * total_cases / total_population, 8) if n else None
            result["incidence"][age].append(pooled)
            # The national aggregate pools numerators and denominators, so it does not
            # suffer the small-number instability EB corrects: its smoothed value equals
            # the pooled rate. EB (global or local) only changes individual municipalities.
            result["incidence_eb"][age].append(pooled)
            result["incidence_eb_local"][age].append(pooled)
    for dose in ["first_dose", "booster"]:
        result["coverage"][dose] = {metric: [] for metric in METRICS}
        result["coverage_entities"][dose] = {metric: [] for metric in METRICS}
        result["coverage_details"][dose] = {metric: {field: [] for field in DETAIL_FIELDS} for metric in METRICS}
        for year in years:
            selected = coverage[coverage.year.eq(year) & coverage.dose.eq(dose)]
            for metric in METRICS:
                if metric in ["reference", "survivors"]:
                    field = "reference_population" if metric == "reference" else "survivor_population"
                    value_field = "reference_coverage_pct" if metric == "reference" else "survivor_coverage_pct"
                    population = selected.get(field, pd.Series(np.nan, index=selected.index))
                    pct = selected.get(value_field, pd.Series(np.nan, index=selected.index))
                    valid = population.gt(0) & np.isfinite(population) & np.isfinite(selected.doses) & selected.doses.ge(0) & pct.notna()
                    numerator = selected.loc[valid, "doses"].sum() * 100
                    denominator = population[valid].sum()
                else:
                    valid = selected.pai_target_population.gt(0) & np.isfinite(selected.pai_target_population) & np.isfinite(selected.administrative_coverage_pct) & selected.administrative_coverage_pct.ge(0)
                    weights = selected.loc[valid, "pai_target_population"]
                    numerator = (selected.loc[valid, "administrative_coverage_pct"] * weights).sum()
                    denominator = weights.sum()
                result["coverage_entities"][dose][metric].append(int(valid.sum()))
                result["coverage"][dose][metric].append(round(numerator / denominator, 8) if denominator > 0 else None)
                for field in DETAIL_FIELDS:
                    matched = selected.get(field, pd.Series(np.nan, index=selected.index)).loc[valid]
                    complete = len(matched) > 0 and np.isfinite(matched).all() and matched.ge(0).all()
                    result["coverage_details"][dose][metric][field].append(float(matched.sum()) if complete else None)
    return result


def main():
    geography = {f["properties"]["code"]: f["properties"] for f in json.loads(GEOMETRY.read_text())["features"]}
    coverage = pd.read_csv(ROOT / "docs/data_processed/cobertura_vacunacion/vaccine_coverage_comparison.csv", dtype={"code": str})
    years = list(range(2008, 2026))
    population = pd.read_csv(POPULATION, dtype={"codigo_municipio": str})
    fields = ["codigo_municipio", "ano_epidemiologico", "casos_total", "casos_edad_desconocida", *CASE_COLUMNS.values()]
    notifications = ds.dataset(CASES, format="parquet").to_table(columns=fields).to_pandas()
    panel = annual_incidence(population, notifications, geography, years)
    eb_lookup = load_eb()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for code, group in panel.groupby("codigo_municipio"):
        group = group.sort_values("ano_epidemiologico")
        counts = {age: group[column] for age, column in CASE_COLUMNS.items()}
        pops = {age: group["poblacion_" + {"under_1": "menor_1", "1_4": "1_4", "5_14": "5_14", "15_49": "15_49", "50_plus": "50_mas"}[age]] for age in AGE_GROUPS}
        counts["all"] = group.casos_total
        pops["all"] = sum(pops.values())
        incidence = {age: values(100000 * counts[age] / pops[age].where(pops[age] > 0)) for age in counts}
        incidence_eb = {age: eb_series(eb_lookup, code, age, years) for age in EB_GROUPS}
        incidence_eb_local = {age: eb_series(eb_lookup, code, age, years, local=True) for age in EB_GROUPS}
        payload = dict(code=code, years=years, incidence=incidence, incidence_eb=incidence_eb, incidence_eb_local=incidence_eb_local,
                       cases={age: values(x) for age, x in counts.items()},
                       population={age: values(x) for age, x in pops.items()},
                       unknown_age_cases=values(group.casos_edad_desconocida),
                       notification_record_present=group.notification_record_present.tolist(), coverage={}, coverage_details={})
        for dose in ["first_dose", "booster"]:
            selected = coverage[coverage.code.eq(code) & coverage.dose.eq(dose)].set_index("year").reindex(years)
            payload["coverage"][dose] = {metric: values(selected[column]) for metric, column in [
                ("administrative", "administrative_coverage_pct"), ("reference", "reference_coverage_pct"), ("survivors", "survivor_coverage_pct")]}
            payload["coverage_details"][dose] = {metric: {field: values(selected[field]) for field in DETAIL_FIELDS} for metric in METRICS}
        (OUTPUT / (code + ".json")).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    (OUTPUT / "all.json").write_text(json.dumps(aggregate_series(panel, coverage, years), ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    manifest = dict(years=years, excluded_year="2007 is diagnostic only due to the documented notification discrepancy", entities=list(geography.values()),
                    aggregate={"code": "all", "name": "Todos los municipios", "department": "Agregado de las 1.122 entidades de la cartografía"},
                    aggregation="incidence: sum cases / sum matching valid age populations * 100000; reference/survivors coverage: sum doses / sum matching valid denominators * 100; administrative: published percentages weighted by positive PAI targets; each series reports its own included entity count; not an arithmetic municipal mean or proof of complete national reporting",
                    age_groups={"all": "Todas las edades", "under_1": "Menores de 1 año", "1_4": "1–4 años", "5_14": "5–14 años", "15_49": "15–49 años", "50_plus": "50 años o más"},
                    incidence="100000 * annual notifications / same-year age-specific population; all ages include unknown-age notifications",
                    incidence_eb="Empirical-Bayes smoothed incidence per age group and year (global Poisson-Gamma, Marshall 1991), shrinking towards the national group mean, for the 1,102 comparable municipalities; null for entities outside that panel; the national aggregate equals its pooled crude rate. See empirical_bayes/README.md",
                    incidence_eb_local="Local (neighbourhood) Empirical-Bayes smoothed incidence, shrinking towards the mean of each municipality and its 8 nearest neighbours; same universe and null rules as incidence_eb. See empirical_bayes/README.md",
                    population_rule="DANE grouped ages, both sexes; historical Mapiripana summed into Barrancominas before joining",
                    coverage="vaccine_coverage_comparison.csv; keep shifted analysis year, first dose age 1, booster age 5; survivors: first dose only / sobrevivientes_edad_1 of same analysis year, already calculated from previous-year births minus infant deaths",
                    tooltip_details="doses, DANE reference population (age 1 or age 5) survivor population (births minus infant deaths of previous year), and original PAI target; aggregate details sum the same entities included by the selected measure, and remain null if any matched component is missing",
                    missingness="absent notification rows assigned zero and flagged; missing/nonpositive population yields null incidence; coverage missingness retained",
                    scope="descriptive annual series; separate units and axes; no causal interpretation or measured population immunity")
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Generated {len(geography)} entity series, {len(years)} years and six incidence age groups")


if __name__ == "__main__":
    main()
