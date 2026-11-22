"""Read exact ages from both source layouts, excluding other ages and areas."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from extract_vaccine_age_population import extract_source
import extract_vaccine_age_population as population_module


class VaccineAgePopulationTests(unittest.TestCase):
    def fixture(self, directory, recent, missing=False):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Population"
        header_row = 9 if recent else 12
        identifiers = ["DP", "DPNOM", "MPIO", "DPMP", "AÑO", "ÁREA GEOGRÁFICA"] if recent else ["DP", "DPNOM", "DPMP", "MPIO", "AÑO", "ÁREA GEOGRÁFICA"]
        age_names = [f"Total {age} {'año' if age == 1 else 'años'}" if recent else f"Total_{age}" for age in range(7)]
        for _ in range(header_row - (2 if recent else 1)):
            sheet.append([])
        if recent:
            sheet.append(identifiers)
            sheet.append([None] * 6 + age_names)
        else:
            sheet.append(identifiers + age_names)
        for year, area in [(2015,"Total"), (2016,"Cabecera Municipal"), (2016,"Centros Poblados y Rural Disperso"), (2016,"Total"), (2026,"Total")]:
            place = ["05", "Antioquia", "05001", "Medellín"] if recent else ["05", "Antioquia", "Medellín", "05001"]
            sheet.append(place + [year, area] + [9999, 100, 8888, 7777, 40, None if missing else 50, 60])
        path = Path(directory) / "source.xlsx"
        workbook.save(path)
        return path, header_row

    def test_both_layouts_use_total_area_total_sex_exact_ages(self):
        for recent in (False, True):
            with self.subTest(recent=recent), tempfile.TemporaryDirectory() as directory:
                path, header = self.fixture(directory, recent)
                rows = extract_source(path, "Population", header)
                self.assertEqual(rows, [{"codigo_municipio":"05001", "ano_epidemiologico":2016,
                    "poblacion_1_anio":100, "poblacion_4_anios":40, "poblacion_5_anios":50,
                    "poblacion_6_anios":60}])

    def test_missing_age_is_preserved_instead_of_imputed(self):
        with tempfile.TemporaryDirectory() as directory:
            path, header = self.fixture(directory, True, missing=True)
            self.assertIsNone(extract_source(path, "Population", header)[0]["poblacion_5_anios"])

    def test_saved_second_dose_denominator_is_sum_of_three_complete_ages(self):
        for missing in (False, True):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                source, header = self.fixture(directory, True, missing=missing)
                output = Path(directory) / "population.csv"
                with patch.object(population_module, "SOURCES", [(source.name, "Population", header)]):
                    population_module.extract(Path(directory), output)
                row = pd.read_csv(output).iloc[0]
                self.assertEqual(row.poblacion_1_anio, 100)
                if missing:
                    self.assertTrue(pd.isna(row.poblacion_4_6))
                else:
                    self.assertEqual(row.poblacion_4_6, 150)


if __name__ == "__main__":
    unittest.main()
