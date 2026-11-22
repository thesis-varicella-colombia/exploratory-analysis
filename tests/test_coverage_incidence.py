"""Verify age-specific incidence, missingness and the historical territory join."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_coverage_incidence_series import annual_incidence, aggregate_series
from generate_age_standardized_sir import CASE_COLUMNS, POPULATION_COLUMNS


class CoverageIncidenceTests(unittest.TestCase):
    def test_aggregate_uses_matched_denominators_and_weighted_admin(self):
        population = pd.DataFrame([
            dict(codigo_municipio=code, ano_epidemiologico=2016,
                 **{field: size for field in POPULATION_COLUMNS.values()})
            for code, size in [("05001", 20), ("05002", 180)]])
        cases = pd.DataFrame([
            dict(codigo_municipio=code, ano_epidemiologico=2016, casos_total=5*n,
                 casos_edad_desconocida=0, **{field: n for field in CASE_COLUMNS.values()})
            for code, n in [("05001", 1), ("05002", 2), ("05003", 100)]])
        panel = annual_incidence(population, cases, ["05001", "05002", "05003"], [2016, 2017])
        coverage = pd.DataFrame([
            dict(code=code, year=2016, dose="first_dose", doses=doses,
                 reference_population=pop, reference_coverage_pct=50 if pd.notna(pop) else np.nan,
                 administrative_coverage_pct=admin, pai_target_population=target)
            for code, doses, pop, admin, target in [("05001",10,20,100,10),("05002",90,180,50,90),("05003",999,np.nan,80,np.nan)]])
        result = aggregate_series(panel, coverage, [2016, 2017])
        self.assertEqual(result["incidence"]["all"], [1500, None])
        self.assertEqual(result["incidence_entities"]["all"], [2, 0])
        self.assertEqual(result["cases"]["all"][0], 15)
        self.assertEqual(result["population"]["all"][0], 1000)
        self.assertEqual(result["coverage"]["first_dose"]["reference"], [50, None])
        self.assertEqual(result["coverage"]["first_dose"]["administrative"], [55, None])
        self.assertEqual(result["coverage_entities"]["first_dose"]["reference"], [2, 0])
        self.assertEqual(result["coverage_entities"]["first_dose"]["administrative"], [2, 0])
        self.assertEqual(result["coverage"]["booster"]["reference"], [None, None])
        self.assertEqual(result["coverage_details"]["first_dose"]["reference"]["doses"], [100, None])
        self.assertEqual(result["coverage_details"]["first_dose"]["reference"]["reference_population"], [200, None])
        self.assertEqual(result["coverage_details"]["first_dose"]["administrative"]["pai_target_population"], [100, None])
        # The published administrative percentage may exist without a dose count.
        # Its tooltip must not display a misleading partial sum of doses.
        coverage.loc[coverage.code.eq("05002"), "doses"] = np.nan
        incomplete = aggregate_series(panel, coverage, [2016, 2017])
        self.assertEqual(incomplete["coverage"]["first_dose"]["administrative"][0], 55)
        self.assertIsNone(incomplete["coverage_details"]["first_dose"]["administrative"]["doses"][0])

    def test_historical_population_and_missingness_are_preserved(self):
        population = pd.DataFrame([
            dict(codigo_municipio=code, ano_epidemiologico=2016,
                 **{field: 20 if code == "94343" else 10 for field in POPULATION_COLUMNS.values()})
            for code in ["94343", "94663"]])
        cases = pd.DataFrame([dict(codigo_municipio="94343", ano_epidemiologico=2016,
                                  casos_total=7, casos_edad_desconocida=2,
                                  **{field: 1 for field in CASE_COLUMNS.values()})])
        panel = annual_incidence(population, cases, ["94343", "05001"], [2016, 2017]).set_index(["codigo_municipio", "ano_epidemiologico"])
        self.assertEqual(panel.loc[("94343", 2016), "poblacion_1_4"], 30)
        self.assertTrue(panel.loc[("94343", 2016), "notification_record_present"])
        self.assertFalse(panel.loc[("94343", 2017), "notification_record_present"])
        self.assertEqual(panel.loc[("94343", 2017), "casos_total"], 0)
        self.assertTrue(pd.isna(panel.loc[("94343", 2017), "poblacion_1_4"]))
        self.assertNotIn("94663", panel.index.get_level_values(0))

    def test_published_series_reconcile_with_existing_products(self):
        directory = ROOT / "docs/data_processed/cobertura_vacunacion/coverage_incidence"
        manifest = json.loads((directory / "manifest.json").read_text())
        self.assertEqual(len(manifest["entities"]), 1122)
        coverage = pd.read_csv(ROOT / "docs/data_processed/cobertura_vacunacion/vaccine_coverage_comparison.csv", dtype={"code": str}).set_index(["code", "year", "dose"])
        baseline = pd.read_csv(ROOT / "docs/data_processed/anomalias_cobertura/comparable_incidence_annual.csv", dtype={"code": str}).set_index(["code", "horizon"])
        for entity in manifest["entities"]:
            code = entity["code"]
            data = json.loads((directory / (code + ".json")).read_text())
            self.assertEqual(data["years"], list(range(2008, 2026)))
            for i, year in enumerate(data["years"]):
                known = sum(data["cases"][age][i] for age in manifest["age_groups"] if age != "all")
                self.assertEqual(known + data["unknown_age_cases"][i], data["cases"]["all"][i])
                for age in manifest["age_groups"]:
                    count, pop, rate = (data[field][age][i] for field in ["cases", "population", "incidence"])
                    if pop is None or pop <= 0:
                        self.assertIsNone(rate)
                    else:
                        self.assertAlmostEqual(rate, 100000 * count / pop, places=7)
                if (code, year) in baseline.index:
                    self.assertAlmostEqual(data["incidence"]["all"][i], baseline.loc[(code, year), "crude_all_age"], places=7)
                for dose in ["first_dose", "booster"]:
                    for metric, column in [("reference", "reference_coverage_pct"), ("administrative", "administrative_coverage_pct"), ("survivors", "survivor_coverage_pct")]:
                        expected = coverage.loc[(code, year, dose), column] if (code, year, dose) in coverage.index else np.nan
                        actual = data["coverage"][dose][metric][i]
                        if np.isnan(expected): self.assertIsNone(actual)
                        else: self.assertEqual(actual, expected)
                        if code in ["05001", "11001", "94343"]:
                            for field in ["doses", "reference_population", "pai_target_population", "survivor_population"]:
                                expected = coverage.loc[(code, year, dose), field] if (code, year, dose) in coverage.index else np.nan
                                actual = data["coverage_details"][dose][metric][field][i]
                                if np.isnan(expected): self.assertIsNone(actual)
                                else: self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
