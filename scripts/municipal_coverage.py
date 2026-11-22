"""Shared municipal code normalization and complete nonnegative sums."""
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
