"""Python implementation of EpiEstim's parametric SI path for weekly incidence.

Methods follow EpiEstim R/discr_si.R and R/estimate_R_agg.R (dt=7,
recon_opt='naive') and the Wallinga--Lipsitch inversion in epitrix. This is
an independent implementation, not a call to the R package. Inputs remain
assumptions; this module does not estimate a varicella serial interval.
"""

from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp
from scipy.stats import gamma


@dataclass
class WeeklyResult:
    daily_incidence: np.ndarray
    daily_infectiousness: np.ndarray
    weekly_infectiousness: np.ndarray
    estimates: np.ndarray
    first_reconstructed_week: int
    max_reconstruction_change: float


def discr_si(days, mean_days, sd_days):
    """EpiEstim's shifted-Gamma discretization, including the zero-day mass."""
    if not np.isfinite(mean_days) or not np.isfinite(sd_days) or mean_days <= 1 or sd_days <= 0:
        raise ValueError("mean_days must exceed one and sd_days must be positive")
    k = np.asarray(days, dtype=float)
    if np.any(k < 0) or np.any(k != np.floor(k)):
        raise ValueError("days must be nonnegative integers")
    shape = ((mean_days - 1) / sd_days) ** 2
    scale = sd_days**2 / (mean_days - 1)
    f = lambda x, a: gamma.cdf(x, a=a, scale=scale)
    weights = (k * f(k, shape) + (k - 2) * f(k - 2, shape)
               - 2 * (k - 1) * f(k - 1, shape)
               + shape * scale * (2 * f(k - 1, shape + 1)
                                - f(k - 2, shape + 1) - f(k, shape + 1)))
    return np.maximum(weights, 0)


def _infectiousness(daily, weights):
    # w[0]=0. The first day's cases may infect later days but have no
    # observed infectors; this matches EpiEstim's incidence convention.
    result = np.convolve(daily, weights, mode="full")[:len(daily)]
    result[0] = np.nan
    return result


def _posterior(daily, weights, starts, ends, prior_mean=5.0, prior_sd=5.0):
    """Daily Poisson--Gamma posterior for zero-based inclusive windows."""
    infectiousness = _infectiousness(daily, weights)
    cumulative_cases = np.r_[0, np.cumsum(daily)]
    cumulative_lambda = np.r_[0, np.cumsum(np.nan_to_num(infectiousness, nan=0))]
    shape = (prior_mean / prior_sd) ** 2 + cumulative_cases[ends + 1] - cumulative_cases[starts]
    rate = prior_mean / prior_sd**2 + cumulative_lambda[ends + 1] - cumulative_lambda[starts]
    means = shape / rate
    # EpiEstim returns NA while the window end is before the mean of its
    # discrete SI distribution (R time indices start at one).
    mean_si = np.dot(np.arange(len(weights)), weights)
    means[ends + 1 <= mean_si] = np.nan
    return means, shape, rate, infectiousness


def _growth_rates(rt, weights, precision=0.001):
    """Invert epitrix::r2R0 on EpiEstim's 0.001/day growth-rate grid."""
    # Keep the leading near-zero lags in place: removing them shifts all later
    # lags toward day zero and changes the growth-rate conversion.
    last_lag = np.flatnonzero(weights >= 1e-6)[-1] + 1
    w = weights[:last_lag].copy()
    w /= w.sum()
    t = np.r_[0.0, np.arange(0.5, len(w) + 0.5, 1.0)]
    # epitrix::r2R0 averages exp(-r*t) over each interval
    # [t[i], t[i+1]], then weights those interval averages by w[i].
    def grid_values(bound):
        grid = np.arange(-bound, bound + precision / 2, precision)
        left = np.exp(-grid[:, None] * t[None, :-1])
        right = np.exp(-grid[:, None] * t[None, 1:])
        denom = -((right - left) / np.diff(t)[None, :]) @ w
        values = np.divide(grid, denom, out=np.ones_like(grid), where=np.abs(grid) > 1e-12)
        values[np.abs(grid) <= 1e-12] = 1
        return grid, values

    bound = 1.0
    for _ in range(5):
        grid, values = grid_values(bound)
        where = np.searchsorted(values, rt)
        if np.all((where > 0) & (where < len(grid))):
            left = where - 1
            right = where
            nearest = np.where(abs(rt - values[left]) <= abs(values[right] - rt), left, right)
            return grid[nearest]
        bound *= 5
    raise ValueError("R values fall outside the growth-rate grid")


def reconstruct_weekly(weekly, mean_days, sd_days, iterations=10):
    """EpiEstim's naive EM reconstruction for an uninterrupted weekly block."""
    weekly = np.asarray(weekly, dtype=float)
    if (weekly.ndim != 1 or len(weekly) < 5 or not np.all(np.isfinite(weekly))
            or np.any(weekly < 0)):
        raise ValueError("Need at least five consecutive, nonnegative weekly counts")
    n = 7 * len(weekly)
    weights = discr_si(np.arange(n), mean_days, sd_days)
    naive = np.repeat(weekly / 7, 7)
    daily = naive.copy()
    change = np.nan
    for _ in range(iterations):
        starts = np.arange(1, len(weekly)) * 7
        ends = starts + 6
        means, _, _, _ = _posterior(daily, weights, starts, ends)
        finite = np.flatnonzero(np.isfinite(means))
        if len(finite) == 0:
            raise ValueError("No weekly posterior means can be estimated")
        first = finite[0] + 1  # first week is excluded from EpiEstim's R estimation
        if not np.array_equal(finite, np.arange(finite[0], len(means))):
            raise ValueError("Nonconsecutive finite reconstruction windows")
        growth = _growth_rates(means[finite], weights)
        offsets = np.arange(1, 8, dtype=float)
        logits = growth[:, None] * offsets[None, :]
        proportions = np.exp(logits - logsumexp(logits, axis=1, keepdims=True))
        updated = naive.copy()
        updated[first * 7:] = (weekly[first:, None] * proportions).ravel()
        change = float(np.max(np.abs(updated - daily)))
        daily = updated
    if not np.allclose(daily.reshape(-1, 7).sum(axis=1), weekly, atol=1e-8):
        raise AssertionError("Reconstructed days must sum to each observed week")
    return daily, weights, first, change


def estimate_weekly(weekly, mean_days, sd_days, window_weeks=4,
                    prior_mean=5.0, prior_sd=5.0, iterations=10):
    """Weekly-end estimates after daily reconstruction, following EpiEstim."""
    if window_weeks < 1 or not isinstance(window_weeks, int):
        raise ValueError("window_weeks must be a positive integer")
    daily, weights, first, change = reconstruct_weekly(weekly, mean_days, sd_days, iterations)
    n_weeks = len(weekly)
    estimates = np.full((n_weeks, 3), np.nan)
    ends = np.arange(n_weeks) * 7 + 6
    starts = ends - 7 * window_weeks + 1
    eligible = starts >= first * 7
    if np.any(eligible):
        means, shape, rate, infectiousness = _posterior(
            daily, weights, starts[eligible], ends[eligible], prior_mean, prior_sd)
        estimates[eligible, 0] = means
        estimates[eligible, 1] = gamma.ppf(.025, a=shape, scale=1 / rate)
        estimates[eligible, 2] = gamma.ppf(.975, a=shape, scale=1 / rate)
        estimates[eligible & ~np.isfinite(estimates[:, 0])] = np.nan
    infectiousness = _infectiousness(daily, weights)
    weekly_infectiousness = np.nansum(infectiousness.reshape(-1, 7), axis=1)
    return WeeklyResult(daily, infectiousness, weekly_infectiousness,
                        estimates, first, change)


def estimate_with_gaps(weekly, mean_days, sd_days, window_weeks=4,
                       prior_mean=5.0, prior_sd=5.0, iterations=10):
    """Estimate each observed block separately; missing weeks never become zero."""
    weekly = np.asarray(weekly, dtype=float)
    estimates = np.full((len(weekly), 3), np.nan)
    weekly_lambda = np.full(len(weekly), np.nan)
    blocks = np.split(np.arange(len(weekly)), np.flatnonzero(~np.isfinite(weekly)) + 1)
    results = []
    for block in blocks:
        block = block[np.isfinite(weekly[block])]
        if len(block) < 5:
            continue
        result = estimate_weekly(weekly[block], mean_days, sd_days, window_weeks,
                                 prior_mean, prior_sd, iterations)
        estimates[block] = result.estimates
        weekly_lambda[block] = result.weekly_infectiousness
        results.append((block, result))
    return weekly_lambda, estimates, results
