import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from smooth_rates_empirical_bayes import eb_global, eb_local, RATE_SCALE


class EmpiricalBayesTests(unittest.TestCase):
    def test_shrinkage_bounds_and_mean_consistency(self):
        rng = np.random.default_rng(0)
        pop = rng.integers(500, 200_000, size=400).astype(float)
        true = rng.gamma(2.0, 0.00005, size=400)        # rate per person
        obs = rng.poisson(pop * true).astype(float)
        smoothed, C, summ = eb_global(obs, pop)
        self.assertTrue(np.all((C >= 0) & (C <= 1)))
        self.assertTrue(np.all(np.isfinite(smoothed)))
        # Pooled mean equals total cases over total population.
        self.assertAlmostEqual(summ["mean_per_100k"], obs.sum() / pop.sum() * RATE_SCALE, places=6)

    def test_large_population_keeps_crude_small_shrinks_to_mean(self):
        # One huge municipality (crude dominates) and one tiny one (shrinks).
        pop = np.array([1_000_000.0, 800.0])
        obs = np.array([3_000.0, 8.0])                  # crude 300 vs 1000 per 100k
        smoothed, C, summ = eb_global(obs, pop)
        crude = obs / pop * RATE_SCALE
        m = summ["mean_per_100k"]
        # Large area: smoothed within 1% of its crude rate.
        self.assertAlmostEqual(smoothed[0], crude[0], delta=0.01 * crude[0])
        # Small area: smoothed strictly between crude and mean, closer to mean.
        self.assertLess(smoothed[1], crude[1])
        self.assertGreater(smoothed[1], m)
        self.assertLess(C[1], C[0])

    def test_no_signal_shrinks_fully_to_mean(self):
        # All areas share the same true rate: between-area variance -> 0.
        pop = np.full(300, 5_000.0)
        obs = np.full(300, 50.0)                        # identical crude rates
        smoothed, C, summ = eb_global(obs, pop)
        self.assertTrue(np.allclose(smoothed, summ["mean_per_100k"]))
        self.assertTrue(np.allclose(C, 0.0))

    def test_missing_and_nonpositive_population_stay_nan(self):
        pop = np.array([1000.0, 0.0, np.nan])
        obs = np.array([10.0, 5.0, 3.0])
        smoothed, C, _ = eb_global(obs, pop)
        self.assertTrue(np.isfinite(smoothed[0]))
        self.assertTrue(np.isnan(smoothed[1]) and np.isnan(smoothed[2]))
        self.assertTrue(np.isnan(C[1]) and np.isnan(C[2]))

    def test_local_shrinks_towards_neighbourhood_not_national_mean(self):
        # Focal small municipality has a high rate; most of the country is low,
        # but its two neighbours are also high. Global pulls the focal down
        # towards the low national mean; local keeps it higher (its region is high).
        pop = np.concatenate(([400.0], np.full(2, 20000.0), np.full(20, 20000.0)))
        obs = np.concatenate(([8.0], [600.0, 600.0], np.full(20, 20.0)))  # focal high, 2 high neighbours, 20 low
        neighbors = np.zeros((23, 2), dtype=int)
        neighbors[0] = [1, 2]
        g_rate, _, _ = eb_global(obs, pop)
        l_rate, l_w = eb_local(obs, pop, neighbors)
        self.assertGreater(l_rate[0], g_rate[0])                      # local stays higher (neighbours are high)
        self.assertTrue(0 <= l_w[0] <= 1)
        self.assertTrue(np.isfinite(l_rate[0]))

    def test_local_focal_invalid_or_isolated_stays_nan(self):
        pop = np.array([0.0, 1000.0, 1000.0])
        obs = np.array([5.0, 10.0, 8.0])
        neighbors = np.array([[1, 2], [0, 2], [0, 1]])
        l_rate, l_w = eb_local(obs, pop, neighbors)
        self.assertTrue(np.isnan(l_rate[0]) and np.isnan(l_w[0]))     # focal has zero population
        self.assertTrue(np.isfinite(l_rate[1]))


if __name__ == "__main__":
    unittest.main()
