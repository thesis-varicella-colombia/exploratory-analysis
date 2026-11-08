"""Shared municipal code normalization and complete nonnegative sums."""
import numpy as np
import pandas as pd

ALIASES = {"00011": "11001", "27086": "27493", "94663": "94343", "88000": "88001"}


def normalize_codes(values):
    return values.astype("string").str.strip().str.replace(r"\.0+$", "", regex=True).str.zfill(5).replace(ALIASES)


def complete_sum(values):
    values = pd.to_numeric(values, errors="coerce")
    return values.sum(min_count=len(values)) if values.ge(0).all() and np.isfinite(values).all() else np.nan
