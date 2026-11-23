"""Checks for zero diagnostics and indirect age standardization."""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_municipal_zero_inflation import calculate_diagnostics
from generate_age_standardized_sir import PERIODS, calculate_sir, read_panel
from generate_sir_coverage_panel import build_panel, classify_quadrants


class Section10SirCoverageTests(unittest.TestCase):
    def test_zero_diagnostic_reproduces_summary(self):
        result = calculate_diagnostics()
        self.assertEqual(len(result), 1122)
        self.assertTrue((result.national_weeks == 363).all())
        self.assertEqual(result.collapsed_weeks.median(), 35)
        self.assertEqual(int((result.collapsed_weeks >= 26).sum()), 719)
        self.assertEqual(int((result.collapsed_weeks == 52).sum()), 111)

    def test_age_standardized_counts_and_references(self):
        panel = read_panel()
        results, reference_rates = calculate_sir(panel)
        self.assertEqual(len(results), 1102 * len(PERIODS))
        self.assertEqual(len(reference_rates), 5 * len(PERIODS))
        for period in PERIODS:
            subset = results.loc[results.period == period]
            self.assertEqual(len(subset), 1102)
            self.assertTrue((subset.expected_period > 0).all())
            np.testing.assert_allclose(
                subset.observed_known_age / subset.expected_period,
                subset.sir_period,
            )
            np.testing.assert_allclose(
                subset.observed_known_age.sum(),
                subset.expected_period.sum(),
                rtol=1e-12,
            )
            np.testing.assert_array_equal(
                subset.observed_known_age + subset.observed_unknown_age,
                subset.observed_all_ages,
            )
        baseline = results.loc[results.period == "2008-2014"]
        np.testing.assert_allclose(baseline.expected_period, baseline.expected_pre)

    def test_lagged_coverage_and_quadrants(self):
        sir = pd.DataFrame({
            "period": ["2020-2021"] * 4,
            "code": ["00001", "00002", "00003", "00004"],
            "sir_period": [0.8, 1.2, 0.7, 1.3],
            "sir_pre": [0.4, 0.6, 0.5, 0.7],
        })
        coverage = pd.DataFrame({
            "DIVIPOLA": ["00001", "00001", "00002", "00002",
                         "00003", "00003", "00004", "00004"],
            "anio": [2020, 2021] * 4,
            "%_varicela_un_anio_dosis_unica":
                [90, 90, 90, 90, 70, 70, 120, 90],
            "%_varicela_cinco_anios_refuerzo": [90] * 8,
        })
        panel = build_panel(sir, coverage)
        eligible, counts = classify_quadrants(panel, 80)
        self.assertEqual(len(eligible), 4)
        self.assertEqual(int(counts.municipalities.sum()), 4)
        self.assertEqual(int(panel.loc[
            panel.code == "00004", "coverage_first_dose_above_100_years"
        ].iloc[0]), 1)
        cells = set(zip(
            eligible.coverage_above_threshold, eligible.sir_above_one
        ))
        self.assertEqual(cells, {(True, False), (True, True), (False, False)})

    def test_cap_is_annual_and_preserves_invalid_values_and_original_mean(self):
        from municipal_coverage import capped_coverage
        values = pd.Series([120., 80., 0., -1., np.inf, np.nan])
        usable = capped_coverage(values)
        np.testing.assert_allclose(usable.iloc[:3], [100., 80., 0.])
        self.assertTrue(usable.iloc[3:].isna().all())
        sir = pd.DataFrame(dict(period=['2020-2021'], code=['05001'], sir_period=[1.2], sir_pre=[1.]))
        coverage = pd.DataFrame({'DIVIPOLA':['05001']*2, 'anio':[2020,2021],
            '%_varicela_un_anio_dosis_unica':[120,80], '%_varicela_cinco_anios_refuerzo':[120,np.nan]})
        panel = build_panel(sir, coverage)
        self.assertEqual(panel.iloc[0].coverage_first_dose_mean, 100.)
        self.assertEqual(panel.iloc[0].coverage_first_dose_valid_mean, 90.)
        eligible, _ = classify_quadrants(panel, 92.9)
        self.assertEqual(len(eligible), 1)
        self.assertFalse(eligible.iloc[0].coverage_above_threshold)
        self.assertEqual(len(classify_quadrants(panel, 92.9, dose='booster')[0]), 0)

    def test_published_booster_matrix_at_reference_threshold(self):
        source = Path(__file__).resolve().parents[1] / "docs/data_processed"
        panel = pd.read_csv(
            source / "anomalias_cobertura/age_standardized_sir_coverage_periods.csv",
            dtype={"code": str},
        )
        eligible, counts = classify_quadrants(panel, 92.9, dose="booster")
        selected = eligible.loc[eligible.period == "2022-2025"]
        self.assertEqual(len(selected), 1102)
        actual = {
            (bool(row.coverage_above_threshold), bool(row.sir_above_one)):
                int(row.municipalities)
            for row in counts.itertuples(index=False)
            if row.period == "2022-2025"
        }
        self.assertEqual(actual, {
            (False, False): 587,
            (False, True): 267,
            (True, False): 158,
            (True, True): 90,
        })



if __name__ == "__main__":
    unittest.main()
