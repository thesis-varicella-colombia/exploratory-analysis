"""Annual municipal cases and incidence versus population / existing DANE area.

Read mpio_narea (km²) from the original compressed GeoJSON; no geometric area
calculation. Use fixed MGN 2025 geography for 2007–2025 and same-year population.
"""
from __future__ import annotations
import argparse
import io
import json
import lzma
import subprocess
from pathlib import Path

import ijson
import numpy as np
import pandas as pd

from municipal_coverage import ALIASES, normalize_codes as normalize, complete_sum

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2007, 2026)


def read_areas(path):
    rows = []
    with lzma.open(path, "rb") as source:
        for feature in ijson.items(source, "features.item"):
            p = feature["properties"]
            value = p.get("mpio_narea")
            area = float(value) if value is not None else np.nan
            rows.append({"code":str(p["mpio_cdpmp"]).zfill(5), "name":p["mpio_cnmbr"],
                         "department":p["dpto_cnmbr"], "kind":p["mpio_tipo"],
                         "area_km2":area if np.isfinite(area) and area > 0 else np.nan})
    frame = pd.DataFrame(rows)
    if frame.code.duplicated().any():
        raise ValueError("Duplicate geographic code")
    return frame




def build_panel(cases, population, areas):
    cases, population = cases.copy(), population.copy()
    if cases.duplicated(["year", "code"]).any():
        raise ValueError("Duplicate notification municipality-year")
    if population.duplicated(["ano_epidemiologico", "codigo_municipio"]).any():
        raise ValueError("Duplicate population municipality-year")
    cases["code"] = normalize(cases.code)
    population["code"] = normalize(population.codigo_municipio)
    population = population.rename(columns={"ano_epidemiologico":"year", "poblacion_total":"population"})
    population["population"] = pd.to_numeric(population.population, errors="coerce")
    population = population.groupby(["year","code"], as_index=False).agg(population=("population",complete_sum))
    cases = cases.groupby(["year","code"], as_index=False).agg(cases=("cases",complete_sum))
    if not set(YEARS).issubset(set(cases.year)):
        raise ValueError("A national notification year is missing; cannot infer municipal zeros")
    grid = pd.MultiIndex.from_product([YEARS,areas.code],names=["year","code"]).to_frame(index=False)
    panel = grid.merge(areas,on="code",validate="many_to_one").merge(population,on=["year","code"],how="left",validate="one_to_one")
    panel = panel.merge(cases,on=["year","code"],how="left",indicator=True,validate="one_to_one")
    panel["notification_record_present"] = panel._merge.eq("both")
    panel.loc[panel._merge.eq("left_only"), "cases"] = 0
    panel = panel.drop(columns="_merge")
    valid_population = np.isfinite(panel.population) & panel.population.gt(0)
    valid_area = np.isfinite(panel.area_km2) & panel.area_km2.gt(0)
    panel["density_per_km2"] = (panel.population / panel.area_km2).where(valid_population & valid_area)
    panel["incidence_per_100k"] = (100000 * panel.cases / panel.population).where(valid_population)
    panel["status"] = np.select([~valid_area, ~valid_population, panel.cases.isna()],
                                ["missing_or_invalid_area", "missing_or_nonpositive_population", "missing_cases"], default="available")
    unmapped = cases.loc[~cases.code.isin(areas.code)]
    metadata = {"area_source":"data/MGN_ADM_MPIO_GRAFICO.geojson.xz", "area_field":"mpio_narea", "area_unit":"km²",
                "area_rule":"use supplied attribute unchanged; fixed MGN 2025 geography across all years",
                "population_source":"data/population_municipal_2007_2025.csv", "density_formula":"population(year) / area_km2",
                "incidence_formula":"100000 * cases(year) / population(year)", "years":list(YEARS),
                "entities":len(areas), "entity_kinds":areas.kind.value_counts().to_dict(), "aliases":ALIASES,
                "zero_rule":"municipal row absent means zero only in a year with national notifications; raw record presence retained",
                "unmapped_notification_rows":len(unmapped), "unmapped_notifications":float(unmapped.cases.sum()),
                "annual":panel.groupby("year").agg(cases=("cases","sum"),plotted=("status",lambda s:int(s.eq("available").sum()))).reset_index().to_dict("records")}
    return panel.sort_values(["year","code"]), metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundaries",type=Path,default=ROOT/"data/MGN_ADM_MPIO_GRAFICO.geojson.xz")
    parser.add_argument("--population",type=Path,default=ROOT/"data/population_municipal_2007_2025.csv")
    parser.add_argument("--parquet",type=Path,default=ROOT/"data/sivigila_integrado_notification_semanal_municipal.parquet")
    parser.add_argument("--output",type=Path,default=ROOT/"docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv")
    args = parser.parse_args()
    parquet = str(args.parquet/"*.parquet").replace("'","''")
    sql = f"SELECT ano_epidemiologico AS year, codigo_municipio AS code, SUM(casos_total) AS cases FROM read_parquet('{parquet}') WHERE ano_epidemiologico BETWEEN 2007 AND 2025 GROUP BY 1,2"
    result = subprocess.run(["duckdb","-csv","-c",sql],check=True,capture_output=True,text=True)
    cases = pd.read_csv(io.StringIO(result.stdout),dtype={"code":str})
    population = pd.read_csv(args.population,dtype={"codigo_municipio":str})
    panel,metadata = build_panel(cases,population,read_areas(args.boundaries))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    panel.to_csv(args.output,index=False,float_format="%.12f")
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Generated {len(panel)} municipality-years; unmatched notification rows: {metadata['unmapped_notification_rows']}")
    print(panel.groupby("year").agg(cases=("cases","sum"),valid=("status",lambda s:s.eq("available").sum())).to_string())


if __name__ == "__main__":
    main()
