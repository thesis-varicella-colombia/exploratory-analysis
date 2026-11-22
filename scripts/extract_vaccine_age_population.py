"""Extract exact vaccine denominator ages from municipal DANE population workbooks.

Only the geographical area Total and the both-sex Total age columns are used.
No age group is split or interpolated. Source workbooks remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT.parent / "data-processing/data/raw/population"
OUTPUT = ROOT / "data/population_vaccine_ages_municipal_2016_2025.csv"
SOURCES = (
    ("DCD-area-sexo-edad-proypoblacion-Mun-2005-2017_VP.xlsx", "NuevaMpal", 12),
    ("PPED-AreaSexoEdadMun-2018-2042_VP.xlsx", "PobMunicipalxÁreaSexoEdad", 9),
)
AGES = (1, 4, 5, 6)


def extract_source(path, sheet, header_row):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        rows = workbook[sheet].iter_rows(values_only=True)
        headers = [next(rows) for _ in range(header_row)]
        header = list(headers[-1])
        if header_row == 9:
            header[:6] = headers[-2][:6]
        positions = {value: i for i, value in enumerate(header) if value is not None}
        names = {age: f"Total_{age}" if header_row == 12 else f"Total {age} {'año' if age == 1 else 'años'}" for age in AGES}
        for name in ("MPIO", "AÑO", "ÁREA GEOGRÁFICA", *names.values()):
            if name not in positions:
                raise ValueError(f"{path.name}: missing column {name}")
        result = []
        for values in rows:
            year = values[positions["AÑO"]]
            if not isinstance(year, (int, float)) or not 2016 <= year <= 2025:
                continue
            if values[positions["ÁREA GEOGRÁFICA"]] != "Total":
                continue
            raw_code = values[positions["MPIO"]]
            code = str(int(raw_code) if isinstance(raw_code, (int, float)) else raw_code).strip().zfill(5)
            if len(code) != 5 or not code.isdigit():
                raise ValueError(f"{path.name}: invalid municipal code {raw_code!r}")
            row = {"codigo_municipio": code, "ano_epidemiologico": int(year)}
            for age, name in names.items():
                value = values[positions[name]]
                if value is not None and (not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0 or int(value) != value):
                    raise ValueError(f"Invalid population: {code}, {year}, age {age}")
                row[f"poblacion_{age}_anio" if age == 1 else f"poblacion_{age}_anios"] = value
            result.append(row)
        return result
    finally:
        workbook.close()


def extract(source_root, output):
    rows, provenance = [], []
    for filename, sheet, header_row in SOURCES:
        path = source_root / filename
        print(f"Reading {filename}", flush=True)
        selected = extract_source(path, sheet, header_row)
        rows.extend(selected)
        provenance.append({"file": filename, "sheet": sheet, "header_row": header_row,
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "selected_rows": len(selected)})
        print(f"Selected {len(selected)} municipality-years", flush=True)
    frame = pd.DataFrame(rows)
    if frame.empty or frame.duplicated(["codigo_municipio", "ano_epidemiologico"]).any():
        raise ValueError("Empty or duplicate municipality-year population")
    columns = ["poblacion_1_anio", "poblacion_4_anios", "poblacion_5_anios", "poblacion_6_anios"]
    frame[columns] = frame[columns].astype("Int64")
    frame["poblacion_4_6"] = frame[columns[1:]].sum(axis=1, min_count=3).astype("Int64")
    frame = frame.sort_values(["codigo_municipio", "ano_epidemiologico"])
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    metadata = {"sources": provenance, "area": "Total", "sex": "Total (both sexes)",
                "years": sorted(frame.ano_epidemiologico.unique().tolist()), "rows": len(frame),
                "first_dose": "population exactly age 1", "booster": "population exactly age 5",
                "missing_age_rule": "each exact age remains missing if unavailable; no interpolation",
                "auxiliary_4_6": "legacy sum retained for reproducibility; not used as booster denominator; missing if any component is missing"}
    output.with_suffix(".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(frame)} rows to {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    extract(args.source_root, args.output)


if __name__ == "__main__":
    main()
