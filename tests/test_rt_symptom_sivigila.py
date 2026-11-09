"""Regression checks for the symptom-onset analysis."""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rt_symptom_sivigila import estimate_onset_rt, parse_onset_date


class SymptomOnsetTests(unittest.TestCase):
    def test_source_year_2013_has_a_different_date_order(self):
        values = pd.Series(["12/05/2013 12:00:00 a. m.", ""])
        self.assertEqual(parse_onset_date(values, 2013).iloc[0], pd.Timestamp("2013-12-05"))
        self.assertEqual(parse_onset_date(values, 2012).iloc[0], pd.Timestamp("2013-05-12"))
        self.assertTrue(pd.isna(parse_onset_date(values, 2013).iloc[1]))

    def test_onset_estimator_preserves_cases_and_missing_days(self):
        counts = np.r_[np.full(50, 10.0), np.full(7, np.nan), np.full(50, 10.0)]
        result = estimate_onset_rt(pd.DataFrame({"cases": counts}))
        np.testing.assert_allclose(result.cases.to_numpy(), counts, equal_nan=True)
        self.assertNotIn("notifications", result.columns)
        self.assertTrue(result.loc[50:56, "rt"].isna().all())
        self.assertEqual(result.index[result.rt.notna()].tolist()[0], 33)
        self.assertEqual(result.index[(result.index >= 57) & result.rt.notna()].tolist()[0], 90)


if __name__ == "__main__":
    unittest.main()
