"""Summarize individual notification ages for the illustrative R0 scenario.

Run with python scripts/generate_r0_individual_age_series.py.
Set SIVIGILA_CSV_DIR when the local source files are stored outside this checkout.
The source CSVs are local microdata and are never copied to the website.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from generate_hospital_age_series import age_group


ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("SIVIGILA_CSV_DIR", ROOT / "data/sivigila/csv"))
DIVIPOLA = ROOT / "data/sivigila/DIVIPOLA-_Códigos_municipios_20261007.csv"
GROUPED = ROOT / "docs/data_processed/varicela_grupo_edad/age_group_series_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/varicela_grupo_edad/r0_individual_age_2008_2025.csv"
YEARS = range(2008, 2026)
GROUPS = ("under_1", "1_4", "5_14", "15_49", "50_plus", "unknown")
COLUMNS = ["ANO", "COD_EVE", "COD_DPTO_R", "COD_MUN_R", "AJUSTE",
           "FEC_NOT", "EDAD", "UNI_MED"]
AGE_DIVISORS = {1: 1, 2: 12, 3: 365.25, 4: 365.25 * 24,
                5: 365.25 * 24 * 60}
ALIASES = {"27086": "27493", "94663": "94343", "88000": "88001"}


def epidemiological_year(dates):
    """Week one starts on the Sunday of the week containing January 4."""
    calendar_year = dates.dt.year
    first = pd.to_datetime(calendar_year.astype(str) + "-01-04")
    first -= pd.to_timedelta((first.dt.weekday + 1) % 7, unit="D")
    following = pd.to_datetime((calendar_year + 1).astype(str) + "-01-04")
    following -= pd.to_timedelta((following.dt.weekday + 1) % 7, unit="D")
    return calendar_year.where(dates.ge(first), calendar_year - 1).where(
        dates.lt(following), calendar_year + 1
    ).astype("int64")


def read_grouped_counts():
    with GROUPED.open(newline="", encoding="utf-8") as source:
        return {(int(row["year"]), row["age_group"]): int(row["notifications"])
                for row in csv.DictReader(source)}


def age_in_years(age, unit):
    """Use the same unit conversion as the published age-group series."""
    values = pd.to_numeric(age.str.strip(), errors="coerce")
    units = pd.to_numeric(unit.str.strip(), errors="coerce")
    years = pd.Series(np.nan, index=age.index)
    for code, divisor in AGE_DIVISORS.items():
        mask = units.eq(code)
        years.loc[mask] = values.loc[mask] / divisor
    return years


def summarize():
    codes = set(pd.read_csv(DIVIPOLA, dtype=str, encoding="utf-8-sig")["Código Municipio"])
    if not set(ALIASES.values()).issubset(codes):
        raise ValueError("Geographic alias targets missing from DIVIPOLA")
    totals = defaultdict(lambda: {"age_sum": 0.0, **{group: 0 for group in GROUPS}})
    for source_year in range(2007, 2026):
        path = RAW / f"Datos_{source_year}_831.csv"
        for chunk in pd.read_csv(path, dtype=str, keep_default_na=False,
                                 encoding="utf-8-sig", usecols=COLUMNS,
                                 chunksize=50_000):
            if not chunk.ANO.eq(str(source_year)).all() or not chunk.COD_EVE.eq("831").all():
                raise ValueError(f"Unexpected year or event in {path}")
            code = (chunk.COD_DPTO_R.str.strip().str.zfill(2)
                    + chunk.COD_MUN_R.str.strip().str.zfill(3)).replace(ALIASES)
            included = code.isin(codes) & ~chunk.AJUSTE.str.strip().str.upper().isin(["6", "D"])
            chunk = chunk.loc[included]
            if chunk.empty:
                continue
            date_text = chunk.FEC_NOT.str.extract(r"^(\d{1,2}/\d{1,2}/\d{4})", expand=False)
            notified = pd.to_datetime(date_text, format="%d/%m/%Y", errors="coerce")
            if notified.isna().any():
                raise ValueError(f"Missing notification date in {path}")
            years = epidemiological_year(notified)
            ages = age_in_years(chunk.EDAD, chunk.UNI_MED)
            groups = age_group(chunk.EDAD, chunk.UNI_MED)
            frame = pd.DataFrame({"year": years, "age": ages, "group": groups})
            for year, subset in frame.groupby("year"):
                if year not in YEARS:
                    continue
                total = totals[year]
                total["age_sum"] += subset.age.sum()
                for group, count in subset.group.value_counts().items():
                    total[group] += int(count)
    return totals


def main():
    totals = summarize()
    published = read_grouped_counts()
    if set(totals) != set(YEARS):
        raise ValueError("Missing years in individual records")
    for year in YEARS:
        for group in GROUPS:
            if totals[year][group] != published[year, group]:
                raise ValueError(f"Individual/grouped count mismatch: {year}/{group}")
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(["year", "known_age_cases", "unknown_age_cases",
                         "age_sum_years", "mean_age_years"])
        for year in YEARS:
            counts = totals[year]
            known = sum(counts[group] for group in GROUPS if group != "unknown")
            writer.writerow([year, known, counts["unknown"],
                             f"{counts['age_sum']:.8f}",
                             f"{counts['age_sum'] / known:.8f}"])
    print(f"Generated {OUTPUT.relative_to(ROOT)}; counts match the published age groups")


if __name__ == "__main__":
    main()
