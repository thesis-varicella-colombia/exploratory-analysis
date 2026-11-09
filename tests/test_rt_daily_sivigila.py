"""Checks for the daily renewal calculation at missing-data boundaries."""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gamma

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rt_daily_sivigila import estimate_daily


class DailyRtTests(unittest.TestCase):
    def test_gap_never_becomes_zero_or_carries_infectiousness(self):
        incidence = np.r_[np.full(50, 10.0), np.full(7, np.nan), np.full(50, 10.0)]
        frame = pd.DataFrame({"notifications": incidence})
        result = estimate_daily(frame)
        self.assertTrue(result.loc[50:56, "rt"].isna().all())
        self.assertTrue(result.loc[50:56, "infectiousness"].isna().all())
        self.assertTrue(result.loc[57:89, "rt"].isna().all())
        self.assertEqual(result.index[result.rt.notna()].tolist()[0], 33)
        self.assertEqual(result.index[(result.index >= 57) & result.rt.notna()].tolist()[0], 90)

        # Recalculate a posterior directly from the 14 daily counts and
        # weighted infectiousness values of one fully observed window.
        window = result.loc[36:49]
        shape = 1 + window.notifications.sum()
        rate = .2 + window.infectiousness.sum()
        self.assertAlmostEqual(result.loc[49, "rt"], shape / rate, places=10)
        self.assertAlmostEqual(result.loc[49, "rt_lower_95"],
                               gamma.ppf(.025, a=shape, scale=1/rate), places=10)


if __name__ == "__main__":
    unittest.main()
