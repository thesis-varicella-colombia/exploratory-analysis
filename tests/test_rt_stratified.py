"""Reconciliation and boundary checks for Rt age and geographic marginals."""
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_rt_stratified import (COLUMNS, NATIONAL, OUTPUT, daily_frame,
                                    estimate_stratum, read_counts)
from rt_daily_sivigila import estimate_daily


class StratifiedRtTests(unittest.TestCase):
    def test_missing_national_days_are_not_local_zeros(self):
        reference = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=3),
                                  "year": 2020, "week": 1, "missing_week": [False, True, False]})
        result = daily_frame({pd.Timestamp("2020-01-01"): 2}, reference)
        np.testing.assert_allclose(result.notifications, [2, np.nan, 0], equal_nan=True)
        with self.assertRaisesRegex(ValueError, "missing national week"):
            daily_frame({pd.Timestamp("2020-01-02"): 1}, reference)

    def test_unexposed_windows_withhold_prior_and_gaps_restart(self):
        zeros = estimate_stratum(pd.DataFrame({"notifications": np.zeros(100)}))
        self.assertTrue(zeros.rt.isna().all())
        counts = np.r_[np.full(50, 10.), np.full(7, np.nan), np.full(50, 10.)]
        frame = pd.DataFrame({"notifications": counts})
        result = estimate_stratum(frame)
        np.testing.assert_allclose(result.rt, estimate_daily(frame).rt, equal_nan=True)
        self.assertTrue(result.loc[50:89, "rt"].isna().all())
        self.assertEqual(result.loc[49, "window_cases"], 140)
        self.assertTrue(np.isnan(result.loc[60, "window_cases"]))

    def test_raw_marginals_share_exclusions_aliases_and_date_parsers(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            places = pd.DataFrame({"Código Municipio": ["05001", "27493", "94343", "88001"]})
            divipola = raw / "places.csv"
            places.to_csv(divipola, index=False)
            base = dict(zip(COLUMNS, ["2013", "831", "05", "001", "", "12/05/2013", "12/05/2013", "6", "2"]))
            for year in range(2007, 2026):
                rows = []
                if year == 2013:
                    rows = [base, {**base, "COD_DPTO_R": "27", "COD_MUN_R": "086", "EDAD": "8", "UNI_MED": "1"},
                            {**base, "AJUSTE": "D"}, {**base, "COD_MUN_R": "999"},
                            {**base, "EDAD": "", "INI_SIN": ""}]
                pd.DataFrame(rows, columns=COLUMNS).to_csv(raw / f"Datos_{year}_831.csv", index=False)
            with patch("builtins.print"):
                counts, _, quality = read_counts(raw, divipola)
            notified = counts["notification"]
            symptom = counts["symptom"]
            self.assertEqual(notified["municipality_05001"][pd.Timestamp("2013-05-12")], 2)
            self.assertEqual(notified["municipality_27493"][pd.Timestamp("2013-05-12")], 1)
            self.assertEqual(symptom["age_under_1"][pd.Timestamp("2013-12-05")], 1)
            self.assertEqual(notified["age_unknown"][pd.Timestamp("2013-05-12")], 1)
            self.assertEqual(sum(sum(row.values()) for key, row in symptom.items() if key.startswith("age_")), 2)
            self.assertEqual(quality[6]["symptom_missing_date"], 1)


@unittest.skipUnless((OUTPUT / "manifest.json").exists(), "Generate the published series first")
class PublishedStrataTests(unittest.TestCase):
    def test_published_counts_intervals_missingness_and_national_regression(self):
        manifest = json.loads((OUTPUT / "manifest.json").read_text())
        for method, (path, field) in NATIONAL.items():
            reference = pd.read_csv(path)
            missing = np.array(manifest["calendars"][method]["missing_week"])
            n = len(reference)
            sums = {dimension: np.zeros(n) for dimension in ["age", "department", "municipality"]}
            by_department = {}
            municipal_sums = {}
            for group in manifest["series"]:
                with gzip.open(OUTPUT / method / f"{group['id']}.json.gz", "rt") as source:
                    data = json.load(source)
                arrays = {key: np.array(values, dtype=float) for key, values in data.items()}
                self.assertTrue(all(len(values) == n for values in arrays.values()))
                self.assertTrue(np.isnan(arrays["count"][missing]).all())
                self.assertTrue(np.isnan(arrays["rt"][missing]).all())
                valid = np.isfinite(arrays["rt"])
                self.assertTrue((arrays["rt_lower_95"][valid] <= arrays["rt"][valid]).all())
                self.assertTrue((arrays["rt_upper_95"][valid] >= arrays["rt"][valid]).all())
                self.assertEqual(int(np.nansum(arrays["count"])), group[method]["cases"])
                self.assertEqual(int(valid.sum()), group[method]["estimated_days"])
                dimension = group["dimension"]
                if dimension == "national":
                    for key in ["rt", "rt_lower_95", "rt_upper_95"]:
                        np.testing.assert_allclose(arrays[key], reference[key], atol=5.1e-7, rtol=0, equal_nan=True)
                else:
                    sums[dimension] += np.nan_to_num(arrays["count"])
                    if dimension == "department":
                        by_department[group["code"]] = arrays["count"]
                    if dimension == "municipality":
                        municipal_sums.setdefault(group["department"], np.zeros(n))
                        municipal_sums[group["department"]] += np.nan_to_num(arrays["count"])
            for values in sums.values():
                np.testing.assert_array_equal(values[~missing], reference[field].to_numpy()[~missing])
            for code, values in by_department.items():
                np.testing.assert_array_equal(values[~missing], municipal_sums[code][~missing])


if __name__ == "__main__":
    unittest.main()
