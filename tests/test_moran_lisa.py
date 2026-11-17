"""Checks for the period Moran and local permutation calculations."""

import csv
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_moran_lisa import benjamini_hochberg, moran_statistics, sample_other_indices


class MoranLisaTests(unittest.TestCase):
    def test_benjamini_hochberg_adjustment(self):
        p_values = np.array([0.2, 0.001, 0.04, 0.01])
        adjusted = benjamini_hochberg(p_values)
        np.testing.assert_allclose(adjusted, [0.2, 0.004, 0.053333333333, 0.02])

    def test_conditional_samples_exclude_focal_and_repeats(self):
        draws = sample_other_indices(np.random.default_rng(2026), 12, 8, 4)
        self.assertEqual(draws.shape, (9999, 8))
        self.assertFalse(np.any(draws == 4))
        self.assertTrue(np.all(np.diff(np.sort(draws, axis=1), axis=1) > 0))

    def test_mean_local_moran_equals_global_moran(self):
        rates = np.array([1.0, 2.0, 3.0, 4.0])
        neighbors = np.array([[1, 3], [0, 2], [1, 3], [0, 2]])
        global_i, global_p, local_i, local_p, local_q, lag, nominal, adjusted = (
            moran_statistics(rates, neighbors, np.random.default_rng(2026))
        )
        deviations = rates - rates.mean()
        manual = np.dot(deviations, deviations[neighbors].mean(axis=1)) / np.dot(
            deviations, deviations
        )
        self.assertAlmostEqual(global_i, manual)
        self.assertAlmostEqual(local_i.mean(), global_i)
        self.assertTrue(0 < global_p <= 1)
        self.assertTrue(np.all(local_p <= local_q))
        self.assertEqual(len(lag), len(nominal))
        self.assertEqual(len(nominal), len(adjusted))

    def test_published_counts_and_persistence(self):
        root = Path(__file__).resolve().parents[1]
        with (root / "docs/data_processed/heterogeneidad_espacial/moran_global_periods.csv").open() as source:
            global_rows = {row["period"]: row for row in csv.DictReader(source)}
        with (root / "docs/data_processed/heterogeneidad_espacial/moran_lisa_periods.csv").open() as source:
            local_rows = list(csv.DictReader(source))
        periods = ("2008-2014", "2015-2019", "2020-2021", "2022-2025")
        by_period = {
            period: {row["code"]: row for row in local_rows if row["period"] == period}
            for period in periods
        }
        codes = set(by_period[periods[0]])
        self.assertEqual(len(codes), 1102)
        for period in periods:
            self.assertEqual(set(by_period[period]), codes)
            for kind in ("hh", "ll"):
                self.assertEqual(
                    sum(row["cluster_nominal"] == kind.upper()
                        for row in by_period[period].values()),
                    int(global_rows[period][kind + "_nominal"]),
                )
                self.assertEqual(
                    sum(row["cluster_fdr"] == kind.upper()
                        for row in by_period[period].values()),
                    int(global_rows[period][kind + "_fdr"]),
                )
        non_pandemic = ("2008-2014", "2015-2019", "2022-2025")
        persistent = {
            kind: {
                code for code in codes
                if all(by_period[period][code]["cluster_nominal"] == kind
                       for period in non_pandemic)
            }
            for kind in ("HH", "LL")
        }
        self.assertEqual((len(persistent["HH"]), len(persistent["LL"])), (23, 31))
        collection = json.loads(
            (root / "docs/data_processed/cartografia/municipal_boundaries_dane.geojson").read_text()
        )
        departments = {
            item["properties"]["code"]: item["properties"]["department"]
            for item in collection["features"]
        }
        self.assertEqual(
            sum(departments[code] == "CUNDINAMARCA" for code in persistent["HH"]), 19
        )
        self.assertEqual(
            sum(departments[code] == "CHOCÓ" for code in persistent["LL"]), 16
        )
        self.assertEqual(
            sum(departments[code] == "NARIÑO" for code in persistent["LL"]), 9
        )


if __name__ == "__main__":
    unittest.main()
