#!/usr/bin/env python3
"""Estimate exploratory weekly national R_t from the published notification series.

Run from any directory: python scripts/generate_rt_national.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gamma

from epiestim_parametric_weekly import estimate_with_gaps


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs/data_processed/evolucion_semanal/weekly_series_2007_2025.csv"
OUTPUT = ROOT / "docs/data_processed/numero_reproductivo/rt_national_weekly.csv"
MEAN_DAYS = 14.1  # Varicella estimate from Simpson 1952, Table 3 in Vink et al. (2014).
SD_DAYS = 2.4     # Study-specific SD reported with that estimate; not a Colombian estimate.
LAGS = 4
WINDOW = 4
PRIOR_SHAPE = 1.0
PRIOR_RATE = 0.2  # Gamma rate: prior mean = 5, variance = 25 (weakly informative).


def serial_weights(mean_days=MEAN_DAYS, sd_days=SD_DAYS, lags=LAGS):
    mean, sd = mean_days / 7, sd_days / 7
    shape = (mean / sd) ** 2
    scale = sd**2 / mean
    edges = np.arange(1, lags + 1, dtype=float)
    raw = gamma.cdf(edges + 0.5, a=shape, scale=scale) - gamma.cdf(
        edges - 0.5, a=shape, scale=scale
    )
    if not np.all(raw > 0):
        raise ValueError("The serial interval weights must be positive")
    # This conditions on intervals 0.5–4.5 weeks and omits both tails.
    return raw / raw.sum()


def estimate_rt(series, weights, window=WINDOW, prior_shape=PRIOR_SHAPE,
                prior_rate=PRIOR_RATE):
    """Return infectiousness and Gamma posterior summaries, leaving gaps as NaN."""
    series = np.asarray(series, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if np.any(np.isinf(series)) or np.any(series[np.isfinite(series)] < 0):
        raise ValueError("Observed incidence must be finite and nonnegative")
    if window < 1 or prior_shape <= 0 or prior_rate <= 0:
        raise ValueError("Invalid window or Gamma prior")
    n, lags = len(series), len(weights)
    infectiousness = np.full(n, np.nan)
    rt = np.full((n, 3), np.nan)
    for t in range(lags, n):
        history = series[t-lags:t]
        if np.all(np.isfinite(history)):
            infectiousness[t] = np.dot(weights, history[::-1])
    for t in range(lags + window - 1, n):
        start = t - window + 1
        incidence_window = series[start:t+1]
        infectiousness_window = infectiousness[start:t+1]
        if not (np.all(np.isfinite(incidence_window)) and
                np.all(np.isfinite(infectiousness_window))):
            continue
        exposure = infectiousness_window.sum()
        if exposure <= 0:
            continue
        post_shape = prior_shape + incidence_window.sum()
        post_rate = prior_rate + exposure
        rt[t] = (
            post_shape / post_rate,
            gamma.ppf(0.025, a=post_shape, scale=1 / post_rate),
            gamma.ppf(0.975, a=post_shape, scale=1 / post_rate),
        )
    return infectiousness, rt


def build_series(path=INPUT):
    raw = pd.read_csv(path)
    rows = raw.loc[(raw.year.between(2008, 2025)) & (raw.age_group == "all")].copy()
    rows = rows.sort_values(["year", "week"]).reset_index(drop=True)
    if rows.empty or rows.duplicated(["year", "week"]).any():
        raise ValueError("Missing or duplicate national weeks")
    if not np.array_equal(np.diff(rows.week_position), np.ones(len(rows) - 1)):
        raise ValueError("week_position must be consecutive")
    missing = rows.loc[rows.notifications.isna(), ["year", "week"]]
    if missing.to_records(index=False).tolist() != [(2008, 52)]:
        raise ValueError(f"Unexpected missing national weeks: {missing.to_dict('records')}")
    rows["missing_week"] = rows.notifications.isna()
    return rows


def main():
    rows = build_series()
    # Main published route: two-week window, matching the literature mean SI
    # (14.1 days) and using full weekly observations.
    infectiousness, estimates, blocks = estimate_with_gaps(
        rows.notifications, MEAN_DAYS, SD_DAYS, window_weeks=2
    )
    rows["lambda_t"] = infectiousness
    rows[["rt", "rt_lower_95", "rt_upper_95"]] = estimates
    # No incidence is invented for the missing week, and no infection history
    # is carried across it. EpiEstim's first valid posterior is in week three
    # of each uninterrupted block under this assumed serial interval.
    affected = np.zeros(len(rows), dtype=bool)
    missing_indices = np.flatnonzero(rows.missing_week.to_numpy())
    for missing_index in missing_indices:
        affected[missing_index] = True
        if missing_index + 1 < len(rows):
            next_block = next((result for indices, result in blocks
                               if indices[0] == missing_index + 1), None)
            if next_block is not None:
                affected[missing_index + 1:
                         missing_index + 1 + next_block.first_reconstructed_week] = True
    rows["missing_affected"] = affected
    if np.any(np.isfinite(estimates[affected])):
        raise ValueError("R_t must be blank wherever the missing week is needed")
    rows = rows.rename(columns={
        "notifications": "cases", "notification_rate_per_100k": "rate_per_100k"
    })
    rows["method"] = "epiestim_parametric_si_python_weekly_aggregated"
    rows["window_days"] = 14
    rows["serial_interval_mean_days"] = MEAN_DAYS
    rows["serial_interval_sd_days"] = SD_DAYS
    columns = ["year", "week", "week_position", "cases", "rate_per_100k",
               "missing_week", "missing_affected", "lambda_t",
               "rt", "rt_lower_95", "rt_upper_95", "method", "window_days",
               "serial_interval_mean_days", "serial_interval_sd_days"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows[columns].to_csv(OUTPUT, index=False, float_format="%.6f")
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({len(rows)} weeks); "
          f"EpiEstim-style parametric SI, 14-day window")


if __name__ == "__main__":
    main()
