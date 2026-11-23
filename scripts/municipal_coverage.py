"""Shared municipal codes, PAI geographic aggregation and coverage precision.

Coverage comparisons use integer units of 10^-8 percentage points, matching
published CSV precision and Math.round(value * 1e8) in the browser. The source
analysis year is retained: harmonization never shifts anio.
"""
import numpy as np
import pandas as pd

ALIASES = {"00011": "11001", "27086": "27493", "94663": "94343", "88000": "88001"}


def normalize_codes(values):
    return values.astype("string").str.strip().str.replace(r"\.0+$", "", regex=True).str.zfill(5).replace(ALIASES)


def complete_sum(values):
    values = pd.to_numeric(values, errors="coerce")
    return values.sum(min_count=len(values)) if values.ge(0).all() and np.isfinite(values).all() else np.nan


def published_percentage(group, column, target):
    percentages = pd.to_numeric(group[column], errors="coerce")
    if not percentages.notna().all():
        return np.nan, "missing_admin_percentage"
    if not (np.isfinite(percentages) & percentages.ge(0)).all():
        return np.nan, "invalid_admin_percentage"
    if len(group) == 1:
        return percentages.iloc[0], "available"
    weights = pd.to_numeric(group[target], errors="coerce")
    if not (np.isfinite(weights) & weights.ge(0)).all() or weights.sum() <= 0:
        return np.nan, "missing_admin_target_for_merge"
    # Only harmonized territories require aggregation: published percentages
    # weighted by their original PAI targets, never an unweighted mean.
    return np.average(percentages, weights=weights), "available"


COVERAGE_SCALE = 100_000_000
PAI_DOSES = (
    ("varicela_un_anio_dosis_unica", "%_varicela_un_anio_dosis_unica", "meta_pob_1_anio"),
    ("varicela_cinco_anios_refuerzo", "%_varicela_cinco_anios_refuerzo", "meta_pob_5_anios"),
)


def coverage_units(values):
    """Nearest integer at published precision; half values round upwards."""
    return np.floor(values * COVERAGE_SCALE + 0.5)


def canonical_coverage(values):
    return coverage_units(values) / COVERAGE_SCALE


def coverage_at_least(values, threshold):
    return coverage_units(values) >= coverage_units(threshold)


def coverage_below(values, threshold):
    return coverage_units(values) < coverage_units(threshold)


def harmonize_coverage(coverage):
    """One PAI row per current code/year, with target-weighted percentages.

    Single records preserve published values. Historical codes that merge into
    one entity sum doses and targets and weight published percentages by targets,
    exactly as the comparative coverage map does. Missing inputs remain missing.
    """
    if coverage.duplicated(["DIVIPOLA", "anio"]).any():
        raise ValueError("Duplicate raw PAI municipality-year")
    coverage = coverage.copy()
    coverage["DIVIPOLA"] = normalize_codes(coverage.DIVIPOLA)
    coverage = coverage.loc[coverage.DIVIPOLA.notna() & coverage.DIVIPOLA.str.fullmatch(r"\d{5}")].copy()
    rows = []
    for (code, year), group in coverage.groupby(["DIVIPOLA", "anio"], sort=False):
        row = group.iloc[0].to_dict()
        row["DIVIPOLA"], row["anio"] = code, year
        if len(group) > 1:
            for doses, percentage, target in PAI_DOSES:
                for column in (doses, target):
                    if column in group:
                        row[column] = complete_sum(group[column])
                if percentage in group:
                    if target not in group:
                        raise ValueError("PAI targets are required to merge historical coverage")
                    row[percentage], _ = published_percentage(group, percentage, target)
        rows.append(row)
    return pd.DataFrame(rows, columns=coverage.columns)


def capped_coverage(values):
    """Finite nonnegative annual percentages, capped at 100; invalid stays missing."""
    values = pd.to_numeric(values, errors="coerce")
    return canonical_coverage(values.where(np.isfinite(values) & values.ge(0)).clip(upper=100))
