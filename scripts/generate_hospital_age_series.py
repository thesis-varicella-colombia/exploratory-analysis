"""Shared age grouping for individual Sivigila records."""
import numpy as np
import pandas as pd

AGE_GROUPS = {
    "under_1": ("casos_menor_1", "poblacion_menor_1"),
    "1_4": ("casos_1_4", "poblacion_1_4"),
    "5_14": ("casos_5_14", "poblacion_5_14"),
    "15_49": ("casos_15_49", "poblacion_15_49"),
    "50_plus": ("casos_50_mas", "poblacion_50_mas"),
    "unknown": ("casos_edad_desconocida", None),
}

def age_group(age, unit):
    """Match the age-unit conversion of calculate_weekly_sivigila.py."""
    age = pd.to_numeric(age.str.strip(), errors="coerce")
    unit = pd.to_numeric(unit.str.strip(), errors="coerce")
    years = pd.Series(np.nan, index=age.index)
    for code, divisor in [(1, 1), (2, 12), (3, 365.25),
                          (4, 365.25 * 24), (5, 365.25 * 24 * 60)]:
        mask = unit.eq(code)
        years.loc[mask] = age.loc[mask] / divisor
    categories = pd.cut(years, [0, 1, 5, 15, 50, np.inf], right=False,
                        labels=list(AGE_GROUPS)[:-1])
    if (years.notna() & categories.isna()).any():
        raise ValueError("Age outside the nonnegative age groups")
    return categories.astype("object").fillna("unknown")
