"""Calculate municipal observed/expected ratios standardized by five age groups.

Both references are retained: age-specific national rates from the same period
identify relative territorial anomalies, while 2008–2014 rates describe how
later notifications compare with a fixed prevaccination reference. The two
ratios answer different questions and must not be interchanged.
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from municipal_coverage import ALIASES, normalize_codes, complete_sum


ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "data/population_municipal_2007_2025.csv"
CASES = ROOT / "data/sivigila_integrado_notification_semanal_municipal.parquet"
GEOMETRY = ROOT / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson"
OUTPUT = ROOT / "docs/data_processed/anomalias_cobertura/age_standardized_sir_municipal_periods.csv"
RATES_OUTPUT = ROOT / "docs/data_processed/anomalias_cobertura/age_standardized_reference_rates.csv"
PERIODS = {
    "2008-2014": range(2008, 2015),
    "2015-2019": range(2015, 2020),
    "2020-2021": range(2020, 2022),
    "2022-2025": range(2022, 2026),
}
AGE_GROUPS = ("under_1", "1_4", "5_14", "15_49", "50_plus")
CASE_COLUMNS = {
    "under_1": "casos_menor_1",
    "1_4": "casos_1_4",
    "5_14": "casos_5_14",
    "15_49": "casos_15_49",
    "50_plus": "casos_50_mas",
}
POPULATION_COLUMNS = {
    "under_1": "poblacion_menor_1",
    "1_4": "poblacion_1_4",
    "5_14": "poblacion_5_14",
    "15_49": "poblacion_15_49",
    "50_plus": "poblacion_50_mas",
}


def harmonize_age_population(population):
    """Sum disjoint historical territorial age populations before geographic filtering.

    Mapiripana (94663) is a former non-municipalized area, now part of
    Barrancominas (94343), not an additional municipality in the modern panel.
    Its separate historical populations are added once; post-merger zero rows
    add nothing to the population already included in Barrancominas.
    """
    keys = ["codigo_municipio", "ano_epidemiologico"]
    if population.duplicated(keys).any():
        raise ValueError("Duplicate raw territory-year population")
    population = population[[*keys, *POPULATION_COLUMNS.values()]].copy()
    raw_codes = population.codigo_municipio.astype("string").str.strip().str.replace(r"\.0+$", "", regex=True).str.zfill(5)
    post_integration = raw_codes.eq("94663") & population.ano_epidemiologico.ge(2020)
    historical_ages = population.loc[post_integration, list(POPULATION_COLUMNS.values())].apply(pd.to_numeric, errors="coerce")
    if historical_ages.gt(0).any().any():
        raise ValueError("Mapiripana has positive population after 2020: verify overlap with Barrancominas before aggregation")
    population["codigo_municipio"] = normalize_codes(population.codigo_municipio)
    return population.groupby(keys, as_index=False)[list(POPULATION_COLUMNS.values())].agg(complete_sum)


def read_panel():
    """Build the full municipality-year panel, including zero-notification rows."""
    features = json.loads(GEOMETRY.read_text(encoding="utf-8"))["features"]
    codes = {
        feature["properties"]["code"]
        for feature in features if feature["properties"]["kind"] == "MUNICIPIO"
    }
    population = harmonize_age_population(pd.read_csv(POPULATION, dtype={"codigo_municipio": str}))
    population = population.loc[
        population.codigo_municipio.isin(codes)
        & population.ano_epidemiologico.between(2008, 2025),
        ["codigo_municipio", "ano_epidemiologico",
         *POPULATION_COLUMNS.values()],
    ].copy()
    population = population.rename(columns={
        value: "population_" + key for key, value in POPULATION_COLUMNS.items()
    })
    if population.duplicated(["codigo_municipio", "ano_epidemiologico"]).any():
        raise ValueError("Duplicate municipality-year population")
    complete_codes = (
        population.groupby("codigo_municipio").ano_epidemiologico.nunique()
    )
    complete_codes = set(complete_codes[complete_codes == 18].index)
    population = population.loc[
        population.codigo_municipio.isin(complete_codes)
    ].copy()
    if len(complete_codes) != 1102 or len(population) != 1102 * 18:
        raise ValueError("Expected 1,102 municipalities with 18 years of population")
    population_fields = ["population_" + group for group in AGE_GROUPS]
    if population[population_fields].isna().any().any() or (
        population[population_fields] < 0
    ).any().any():
        raise ValueError("Missing or negative age-group population")

    fields = [
        "codigo_municipio", "ano_epidemiologico", "casos_total",
        "casos_edad_desconocida", *CASE_COLUMNS.values(),
    ]
    cases = ds.dataset(CASES, format="parquet").to_table(columns=fields).to_pandas()
    cases["codigo_municipio"] = normalize_codes(cases.codigo_municipio)
    cases = cases.loc[
        cases.codigo_municipio.isin(complete_codes)
        & cases.ano_epidemiologico.between(2008, 2025)
    ]
    cases = cases.groupby(
        ["codigo_municipio", "ano_epidemiologico"], as_index=False
    )[["casos_total", "casos_edad_desconocida", *CASE_COLUMNS.values()]].sum()
    cases = cases.rename(columns={
        value: "observed_" + key for key, value in CASE_COLUMNS.items()
    })
    panel = population.merge(
        cases, on=["codigo_municipio", "ano_epidemiologico"], how="left",
        validate="one_to_one", indicator=True,
    )
    panel["without_notification_row"] = panel["_merge"] == "left_only"
    panel = panel.drop(columns="_merge")
    case_fields = ["observed_" + group for group in AGE_GROUPS]
    panel[[*case_fields, "casos_total", "casos_edad_desconocida"]] = panel[
        [*case_fields, "casos_total", "casos_edad_desconocida"]
    ].fillna(0)
    if not np.array_equal(
        panel[case_fields].sum(axis=1).to_numpy()
        + panel.casos_edad_desconocida.to_numpy(),
        panel.casos_total.to_numpy(),
    ):
        raise ValueError("Age-group counts do not reconcile to total cases")
    return panel


def calculate_sir(panel):
    """Return period-level expected counts under period and fixed-baseline rates."""
    output = []
    reference_rows = []
    period_rates = {}
    for period, years in PERIODS.items():
        selected = panel.loc[panel.ano_epidemiologico.isin(years)]
        population_totals = np.array([
            selected["population_" + group].sum() for group in AGE_GROUPS
        ], dtype=float)
        case_totals = np.array([
            selected["observed_" + group].sum() for group in AGE_GROUPS
        ], dtype=float)
        rates = case_totals / population_totals
        period_rates[period] = rates
        for group, observed, population_years, rate in zip(
            AGE_GROUPS, case_totals, population_totals, rates
        ):
            reference_rows.append({
                "period": period,
                "age_group": group,
                "observed": int(observed),
                "population_years": int(population_years),
                "rate_per_100k": rate * 100_000,
            })
        columns = [
            *["population_" + group for group in AGE_GROUPS],
            *["observed_" + group for group in AGE_GROUPS],
            "casos_total", "casos_edad_desconocida", "without_notification_row",
        ]
        summary = selected.groupby("codigo_municipio", as_index=False)[columns].sum()
        summary.insert(0, "period", period)
        summary["years"] = len(years)
        summary["observed_known_age"] = summary[
            ["observed_" + group for group in AGE_GROUPS]
        ].sum(axis=1)
        summary["population_years_total"] = summary[
            ["population_" + group for group in AGE_GROUPS]
        ].sum(axis=1)
        summary["expected_period"] = summary[
            ["population_" + group for group in AGE_GROUPS]
        ].to_numpy() @ rates
        output.append(summary)

    result = pd.concat(output, ignore_index=True)
    baseline_rates = period_rates["2008-2014"]
    result["expected_pre"] = result[
        ["population_" + group for group in AGE_GROUPS]
    ].to_numpy() @ baseline_rates
    for reference in ("period", "pre"):
        expected = result["expected_" + reference]
        result["sir_" + reference] = np.where(
            expected > 0, result.observed_known_age / expected, np.nan
        )
    result = result.rename(columns={
        "codigo_municipio": "code",
        "casos_total": "observed_all_ages",
        "casos_edad_desconocida": "observed_unknown_age",
        "without_notification_row": "years_without_notification_row",
    })
    columns = [
        "period", "code", "years", "observed_known_age",
        "observed_unknown_age", "observed_all_ages",
        "population_years_total", "expected_period", "sir_period",
        "expected_pre", "sir_pre", "years_without_notification_row",
    ]
    return result[columns], pd.DataFrame(reference_rows)


def main():
    result, rates = calculate_sir(read_panel())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False, float_format="%.8f")
    rates.to_csv(RATES_OUTPUT, index=False, float_format="%.8f")
    metadata = {
        "geography": "fixed DANE MGN 2025 municipality boundaries; same 1102 municipalities with 18 years of population",
        "population_rule": "normalize territory codes and sum age populations before filtering to current municipalities",
        "aliases": ALIASES,
        "mapiripana": "94663 is a former non-municipalized area now included in Barrancominas 94343, not a separate municipality in the output",
        "historical_population": "sum the separately recorded populations of 94343 and 94663; 94663 has zero population in all five age groups from 2020 onward in the source, so no post-merger duplication",
        "case_rule": "normalize residence codes before grouping; raw notifications are not modified",
        "references": "age-specific rates by period and fixed 2008-2014 reference, regenerated after population harmonization",
    }
    OUTPUT.with_suffix(".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Municipality-period rows: {len(result)}")
    for period in PERIODS:
        subset = result.loc[result.period == period]
        print(
            f"{period}: median SIR(period)={subset.sir_period.median():.3f}, "
            f"median SIR(pre)={subset.sir_pre.median():.3f}, "
            f"O/E(period)={subset.observed_known_age.sum()/subset.expected_period.sum():.6f}"
        )
    print(f"Generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
