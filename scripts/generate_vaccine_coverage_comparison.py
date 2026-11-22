"""Compare published PAI percentages with user-defined dose/population ratios.

Preserve the analysis year (anio) and use same-analysis-year population exactly age one for
first dose and exactly age five for boosters from 2019. Population estimates are
independent of the published PAI target values. Preserve >100% and missingness; never infer immune fractions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from municipal_coverage import ALIASES, normalize_codes, complete_sum, published_percentage

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data/vaccine_coverage_municipal_lagged_2016_2025.csv"
POPULATION = ROOT / "data/population_vaccine_ages_municipal_2016_2025.csv"
SURVIVORS = ROOT / "data/births_mortality_dane/integration/surviving_infants.parquet"
BOUNDARIES = ROOT / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson"
OUTPUT = ROOT / "docs/data_processed/cobertura_vacunacion/vaccine_coverage_comparison.csv"
DOSES = {
    "first_dose": ("varicela_un_anio_dosis_unica", "%_varicela_un_anio_dosis_unica", "meta_pob_1_anio", "poblacion_1_anio", "age_1"),
    "booster": ("varicela_cinco_anios_refuerzo", "%_varicela_cinco_anios_refuerzo", "meta_pob_5_anios", "poblacion_5_anios", "age_5"),
}


def build_comparison(coverage, population, geography, survivors=None):
    coverage = coverage.copy()
    population = population.copy()
    if coverage.duplicated(["DIVIPOLA", "anio"]).any():
        raise ValueError("Duplicate raw PAI municipality-year")
    if population.duplicated(["codigo_municipio", "ano_epidemiologico"]).any():
        raise ValueError("Duplicate population municipality-year")
    valid_codes = set(geography)
    survivor_pop = pd.Series(dtype=float)
    excluded_survivor_rows = 0
    if survivors is not None:
        survivors = survivors.copy()
        # Special categories (-1/-2, foreign countries) are not municipal codes.
        municipal = survivors.codigo_municipio.str.fullmatch(r"\d{5}", na=False)
        excluded_survivor_rows = int((~municipal).sum())
        survivors = survivors.loc[municipal].copy()
        if survivors.duplicated(["codigo_municipio", "ano"]).any():
            raise ValueError("Duplicate survivors municipality-year")
        survivors["code"] = normalize_codes(survivors.codigo_municipio)
        survivors = survivors.loc[survivors.code.isin(valid_codes)]
        survivor_pop = survivors.groupby(["code", "ano"])["sobrevivientes_edad_1"].agg(complete_sum)
    coverage["code"] = normalize_codes(coverage.DIVIPOLA)
    coverage["year"] = pd.to_numeric(coverage.anio, errors="raise").astype(int)
    coverage["original_code"] = coverage.DIVIPOLA.astype("string").str.strip().str.zfill(5)
    unmapped = coverage.loc[~coverage.code.isin(valid_codes), ["DIVIPOLA", "anio"]]
    coverage = coverage.loc[coverage.code.isin(valid_codes)].copy()
    if coverage.empty:
        raise ValueError("No PAI records match the mapped geography")
    population["code"] = normalize_codes(population.codigo_municipio)
    pop_columns = ["poblacion_1_anio", "poblacion_5_anios"]
    population = population.loc[population.code.isin(valid_codes)]
    pop = population.groupby(["code", "ano_epidemiologico"])[pop_columns].agg(complete_sum)
    groups = {(code, int(year)): group for (code, year), group in coverage.groupby(["code", "year"])}
    years = sorted(coverage.year.unique().tolist())
    rows = []
    for year in years:
        for code, place in sorted(geography.items()):
            group = groups.get((code, year))
            for dose, (doses_column, admin_column, target_column, pop_column, age_group) in DOSES.items():
                row = {"code": code, "year": year, "dose": dose, "source_analysis_year": year, "dose_source_year": year - 1,
                       "source_rows": 0 if group is None else len(group),
                       "merged_geography": group is not None and len(group) > 1,
                       "reference_age_group": age_group, "doses": np.nan, "pai_target_population": np.nan,
                       "reference_population": np.nan, "administrative_coverage_pct": np.nan,
                       "reference_coverage_pct": np.nan}
                if (code, year) in pop.index:
                    row["reference_population"] = pop.loc[(code, year), pop_column]
                if dose == "booster" and year < 2019:
                    row.update(administrative_status="not_applicable_before_2019", reference_status="not_applicable_before_2019")
                elif group is None:
                    row.update(administrative_status="missing_source_record", reference_status="missing_source_record")
                else:
                    row["doses"] = complete_sum(group[doses_column])
                    row["pai_target_population"] = complete_sum(group[target_column])
                    row["administrative_coverage_pct"], row["administrative_status"] = published_percentage(group, admin_column, target_column)
                    denominator = row["reference_population"]
                    if not np.isfinite(row["doses"]):
                        row["reference_status"] = "missing_or_invalid_doses"
                    elif not np.isfinite(denominator):
                        row["reference_status"] = "missing_population"
                    elif denominator <= 0:
                        row["reference_status"] = "nonpositive_population"
                    else:
                        row["reference_coverage_pct"] = 100 * row["doses"] / denominator
                        row["reference_status"] = "available"
                row.update(survivor_population=np.nan, survivor_coverage_pct=np.nan,
                           survivor_status="not_applicable_to_booster")
                if dose == "first_dose":
                    denominator = survivor_pop.get((code, year), np.nan)
                    row["survivor_population"] = denominator
                    if group is None:
                        row["survivor_status"] = "missing_source_record"
                    elif not np.isfinite(row["doses"]):
                        row["survivor_status"] = "missing_or_invalid_doses"
                    elif not np.isfinite(denominator):
                        row["survivor_status"] = "missing_survivors"
                    elif denominator <= 0:
                        row["survivor_status"] = "nonpositive_survivors"
                    else:
                        row["survivor_coverage_pct"] = 100 * row["doses"] / denominator
                        row["survivor_status"] = "available"
                rows.append(row)
    result = pd.DataFrame(rows)
    if result.duplicated(["code", "year", "dose"]).any():
        raise AssertionError("Duplicate comparison key")
    metadata = {"dose_year_rule": "preserve source anio as analysis year; population from that same analysis year; original dose sheet is anio minus one",
                "years": years, "booster_first_year": 2019, "mapped_entities": len(geography),
                "reference_denominators": {"first_dose": "poblacion_1_anio", "booster": "poblacion_5_anios"},
                "population_source": "population_vaccine_ages_municipal_2016_2025.csv; exact ages extracted from DANE workbooks, Total area and both sexes",
                "reference_ages": {"first_dose": [1], "booster": [5]},
                "survivor_source": "data/births_mortality_dane/integration/surviving_infants.parquet",
                "survivor_rule": "first dose only: 100 * doses / sobrevivientes_edad_1(analysis year); denominator already equals births(t-1) minus deaths under age one(t-1); no extra shift",
                "survivor_excluded_special_rows": excluded_survivor_rows,
                "survivor_missingness": "missing, negative or incomplete merged denominators remain missing; zero denominator is nonpositive; no fallback to reference population",
                "booster_population_rule": "population exactly age 5; no other ages",
                "administrative_rule": "published percentage; merged territories use original PAI-target-weighted percentages",
                "aliases": ALIASES, "unmapped_source_rows": len(unmapped),
                "unmapped_source_records": unmapped.fillna("").to_dict("records"),
                "color_scale_upper_pct": 200, "values_above_100_retained": True,
                "measures_immunity": False,
                "counts": result.groupby(["year", "dose"])[["administrative_coverage_pct", "reference_coverage_pct", "survivor_coverage_pct"]].count().reset_index().to_dict("records")}
    return result, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, default=COVERAGE)
    parser.add_argument("--population", type=Path, default=POPULATION)
    parser.add_argument("--survivors", type=Path, default=SURVIVORS)
    parser.add_argument("--boundaries", type=Path, default=BOUNDARIES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    coverage = pd.read_csv(args.coverage, dtype={"DIVIPOLA": str, "CODEP": str}, encoding="utf-8-sig")
    population = pd.read_csv(args.population, dtype={"codigo_municipio": str})
    boundaries = json.loads(args.boundaries.read_text())
    geography = {feature["properties"]["code"]: feature["properties"] for feature in boundaries["features"]}
    data, metadata = build_comparison(coverage, population, geography, pd.read_parquet(args.survivors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False, float_format="%.8f")
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(data)} rows, {len(geography)} mapped entities; analysis years {min(metadata['years'])}–{max(metadata['years'])}")
    print(data.groupby("dose")[["administrative_coverage_pct", "reference_coverage_pct"]].count().to_string())
    print(f"Unmapped source rows: {metadata['unmapped_source_rows']}")


if __name__ == "__main__":
    main()
