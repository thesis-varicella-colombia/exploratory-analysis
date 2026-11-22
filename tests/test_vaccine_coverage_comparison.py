"""Verify denominators, the retained analysis year, and geographic harmonization."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_vaccine_coverage_comparison import build_comparison


def source(code="05001", year=2016, doses=60, booster=np.nan, admin=91.7, target=50):
    return dict(DIVIPOLA=code, anio=year, varicela_un_anio_dosis_unica=doses,
                varicela_cinco_anios_refuerzo=booster,
                **{"%_varicela_un_anio_dosis_unica": admin,
                   "%_varicela_cinco_anios_refuerzo": 80 if np.isfinite(booster) else np.nan,
                   "meta_pob_1_anio": target, "meta_pob_5_anios": 100})


def population(code="05001", year=2016, age1=40, age5=50):
    return dict(codigo_municipio=code, ano_epidemiologico=year,
                poblacion_1_anio=age1, poblacion_5_anios=age5, poblacion_4_6=200)


def build(sources, populations, codes=("05001",)):
    return build_comparison(pd.DataFrame(sources), pd.DataFrame(populations),
                            {code: {} for code in codes})[0].set_index(["code", "year", "dose"])


class VaccineCoverageComparisonTests(unittest.TestCase):
    def test_survivors_use_already_shifted_year_and_only_first_dose(self):
        survivors = pd.DataFrame([
            dict(codigo_municipio="05001", ano=2015, sobrevivientes_edad_1=999),
            dict(codigo_municipio="05001", ano=2016, sobrevivientes_edad_1=30)])
        data, _ = build_comparison(pd.DataFrame([source()]), pd.DataFrame([population()]),
                                   {"05001": {}}, survivors)
        first, booster = data.iloc[0], data.iloc[1]
        self.assertEqual(first.survivor_population, 30)
        self.assertEqual(first.survivor_coverage_pct, 200)
        self.assertEqual(booster.survivor_status, "not_applicable_to_booster")
        self.assertTrue(pd.isna(booster.survivor_coverage_pct))

    def test_survivors_missing_invalid_and_zero(self):
        for denominator, doses, status, value in [
            (30, 0, "available", 0), (0, 60, "nonpositive_survivors", None),
            (-1, 60, "missing_survivors", None), (np.nan, 60, "missing_survivors", None),
            (30, np.nan, "missing_or_invalid_doses", None)]:
            survivors = pd.DataFrame([dict(codigo_municipio="05001", ano=2016,
                                           sobrevivientes_edad_1=denominator)])
            data, _ = build_comparison(pd.DataFrame([source(doses=doses)]),
                                       pd.DataFrame([population()]), {"05001": {}}, survivors)
            self.assertEqual(data.iloc[0].survivor_status, status)
            if value is None:
                self.assertTrue(pd.isna(data.iloc[0].survivor_coverage_pct))
            else:
                self.assertEqual(data.iloc[0].survivor_coverage_pct, value)

    def test_survivors_harmonize_and_reject_duplicates(self):
        survivors = pd.DataFrame([
            dict(codigo_municipio=code, ano=2016, sobrevivientes_edad_1=value)
            for code, value in [("94343", 20), ("94663", 10), ("-2", 999)]])
        inputs = (pd.DataFrame([source("94343"), source("94663")]),
                  pd.DataFrame([population("94343")]), {"94343": {}})
        data, _ = build_comparison(*inputs, survivors)
        self.assertEqual(data.iloc[0].survivor_population, 30)
        self.assertEqual(data.iloc[0].survivor_coverage_pct, 400)
        survivors.loc[1, "sobrevivientes_edad_1"] = np.nan
        data, _ = build_comparison(*inputs, survivors)
        self.assertTrue(pd.isna(data.iloc[0].survivor_population))
        with self.assertRaisesRegex(ValueError, "Duplicate survivors"):
            build_comparison(*inputs, pd.concat([survivors, survivors.iloc[:1]]))

    def test_preserves_shift_and_uses_analysis_year_population(self):
        data = build([source()], [population(), population(year=2015, age1=999)])
        row = data.loc[("05001", 2016, "first_dose")]
        self.assertEqual(row.dose_source_year, 2015)
        self.assertEqual(row.source_analysis_year, 2016)
        self.assertEqual(row.reference_population, 40)
        self.assertEqual(row.reference_coverage_pct, 150)  # Never cap at 100.
        self.assertEqual(row.administrative_coverage_pct, 91.7)  # Preserve published value.

    def test_booster_uses_exact_age_5_population_and_keeps_2019_missing(self):
        data = build([source(year=2018), source(year=2019), source(year=2020, booster=80)],
                     [population(year=year) for year in (2018, 2019, 2020)])
        self.assertEqual(data.loc[("05001", 2018, "booster"), "reference_status"], "not_applicable_before_2019")
        self.assertTrue(pd.isna(data.loc[("05001", 2019, "booster"), "reference_coverage_pct"]))
        self.assertEqual(data.loc[("05001", 2020, "booster"), "reference_coverage_pct"], 160)
        self.assertEqual(data.loc[("05001", 2020, "booster"), "reference_population"], 50)
        self.assertEqual(data.loc[("05001", 2020, "booster"), "reference_age_group"], "age_5")

    def test_booster_missing_age_5_does_not_fall_back_to_other_ages(self):
        data = build([source(year=2020, booster=80)], [population(year=2020, age5=np.nan)])
        row = data.loc[("05001", 2020, "booster")]
        self.assertEqual(row.reference_status, "missing_population")
        self.assertTrue(pd.isna(row.reference_coverage_pct))

    def test_zero_doses_differ_from_missing_or_zero_population(self):
        sources = [source(year=year, doses=0) for year in (2016, 2017, 2018)]
        data = build(sources, [population(), population(year=2017, age1=0)])
        self.assertEqual(data.loc[("05001", 2016, "first_dose"), "reference_coverage_pct"], 0)
        self.assertEqual(data.loc[("05001", 2017, "first_dose"), "reference_status"], "nonpositive_population")
        self.assertEqual(data.loc[("05001", 2018, "first_dose"), "reference_status"], "missing_population")
        self.assertTrue(pd.isna(data.loc[("05001", 2017, "first_dose"), "reference_coverage_pct"]))

    def test_aliases_sum_doses_population_and_weight_published_percentages(self):
        data = build([source("94343", doses=20, admin=50, target=40),
                      source("94663", doses=30, admin=120, target=10), source("11")],
                     [population("94343", age1=30), population("94663", age1=20), population("11001")],
                     ("94343", "11001"))
        row = data.loc[("94343", 2016, "first_dose")]
        self.assertEqual(row.doses, 50)
        self.assertEqual(row.reference_population, 50)
        self.assertEqual(row.reference_coverage_pct, 100)
        self.assertEqual(row.administrative_coverage_pct, 64)
        self.assertTrue(row.merged_geography)
        self.assertEqual(data.loc[("11001", 2016, "first_dose"), "source_rows"], 1)

    def test_incomplete_merged_doses_cannot_turn_into_partial_total(self):
        data = build([source("94343"), source("94663", doses=np.nan)],
                     [population("94343"), population("94663")], ("94343",))
        row = data.loc[("94343", 2016, "first_dose")]
        self.assertTrue(pd.isna(row.reference_coverage_pct))
        self.assertEqual(row.reference_status, "missing_or_invalid_doses")

    def test_duplicate_source_or_population_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate raw PAI"):
            build([source(), source()], [population()])
        with self.assertRaisesRegex(ValueError, "Duplicate population"):
            build([source()], [population(), population()])


if __name__ == "__main__":
    unittest.main()
