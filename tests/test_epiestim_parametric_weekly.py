"""Independent mathematical checks for the Python EpiEstim-style route."""

import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.stats import gamma

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from epiestim_parametric_weekly import (
    _growth_rates, discr_si, estimate_weekly, estimate_with_gaps,
)


class ParametricWeeklyTests(unittest.TestCase):
    def test_growth_rate_inversion_preserves_early_lags(self):
        weights = discr_si(np.arange(141), 14.1, 2.4)
        edges = np.r_[0.0, np.arange(0.5, len(weights) + 0.5)]
        growth = 0.02
        denominator = -np.sum(weights * np.diff(np.exp(-growth * edges))
                              / np.diff(edges))
        reproduction_number = growth / denominator
        inferred = _growth_rates(np.array([reproduction_number]), weights)[0]
        self.assertAlmostEqual(inferred, growth, places=3)

    def test_discr_si_matches_triangular_integral(self):
        mean, sd = 16.0, 5.0
        shape = ((mean - 1) / sd) ** 2
        scale = sd**2 / (mean - 1)
        weights = discr_si(np.arange(100), mean, sd)
        self.assertAlmostEqual(weights[0], 0)
        self.assertAlmostEqual(weights.sum(), 1, places=12)
        for k in (1, 3, 8, 16, 24):
            left = quad(lambda x: (x - k + 2) * gamma.pdf(x, shape, scale=scale),
                        max(0, k - 2), k - 1)[0] if k > 1 else 0
            right = quad(lambda x: (k - x) * gamma.pdf(x, shape, scale=scale),
                         k - 1, k)[0]
            self.assertAlmostEqual(weights[k], left + right, places=11)

    def test_reconstruction_conserves_weekly_totals_and_gaps(self):
        counts = np.array([10, 20, 40, 80, 50, 30, 20, 10, 10, 10], dtype=float)
        result = estimate_weekly(counts, 16, 5)
        np.testing.assert_allclose(result.daily_incidence.reshape(-1, 7).sum(axis=1),
                                   counts, atol=1e-10)
        self.assertTrue(np.isfinite(result.estimates[-1, 0]))
        self.assertTrue(np.isnan(result.estimates[0, 0]))
        with_gap = np.r_[counts, np.nan, counts]
        _, estimates, blocks = estimate_with_gaps(with_gap, 16, 5)
        self.assertEqual(len(blocks), 2)
        self.assertTrue(np.isnan(estimates[len(counts), 0]))
        self.assertTrue(np.isnan(estimates[len(counts) + 1, 0]))


if __name__ == "__main__":
    unittest.main()
