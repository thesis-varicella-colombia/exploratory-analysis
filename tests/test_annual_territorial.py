import json
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate_annual_territorial import series_rows,YEARS


class AnnualTerritorialTests(unittest.TestCase):
    def test_rate_is_ratio_of_sums_and_missing_population_stays_missing(self):
        source=pd.DataFrame([dict(year=year,population=pop,cases=count,notification_record_present=present)
            for year in YEARS for pop,count,present in [(100,10,True),(900,0,False)]])
        rows=series_rows(source)
        self.assertEqual(rows[0]['notification_rate_per_100k'],1000)
        self.assertEqual(rows[0]['reporting_entities'],1)
        self.assertEqual(rows[0]['selected_entities'],2)
        missing=source.iloc[::2].copy();missing['population']=float('nan')
        rows=series_rows(missing)
        self.assertEqual(rows[0]['notifications'],10)
        self.assertIsNone(rows[0]['population'])
        self.assertIsNone(rows[0]['notification_rate_per_100k'])
        self.assertEqual(rows[0]['missing_population_entities'],1)

    def test_published_national_rows_are_unchanged_and_territorial_totals_match(self):
        directory=ROOT/'docs/data_processed/varicela_totales_por_anio'
        national=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/annual_series_2007_2025.csv')
        aggregate=json.loads((directory/'all.json').read_text())
        for original,row in zip(national.to_dict('records'),aggregate['rows']):
            for field,value in original.items():
                if pd.isna(value):self.assertIsNone(row[field])
                else:self.assertEqual(row[field],value)
        manifest=json.loads((directory/'manifest.json').read_text())
        self.assertEqual(len(manifest['departments']),33)
        self.assertEqual(len(manifest['municipalities']),1122)
        self.assertEqual(manifest['departments'][0]['code'],'88')
        self.assertEqual(manifest['departments'][-1]['code'],'91')
        density=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv',dtype={'code':str})
        for department in manifest['departments']:
            rows=json.loads((directory/(department['id']+'.json')).read_text())['rows']
            selected=density[density.code.str.startswith(department['code'])]
            for year,row in zip(YEARS,rows):
                raw=selected[selected.year.eq(year)]
                self.assertEqual(row['notifications'],raw.cases.sum())
                self.assertEqual(row['population'],raw.population.sum())
                self.assertEqual(row['reporting_entities'],raw.notification_record_present.sum())
                self.assertIsNone(row['official_2007_cases'])
                self.assertAlmostEqual(row['notification_rate_per_100k'],100000*raw.cases.sum()/raw.population.sum(),places=7)
        codes={row['code'] for row in manifest['municipalities']}
        self.assertNotIn('94663',codes)
        barrancominas=json.loads((directory/'94343.json').read_text())['rows']
        self.assertEqual(next(row for row in barrancominas if row['year']==2008)['population'],6214)
        bajira=json.loads((directory/'27493.json').read_text())['rows']
        row=next(row for row in bajira if row['year']==2009)
        self.assertEqual(row['notifications'],1)
        self.assertIsNone(row['notification_rate_per_100k'])


if __name__=='__main__':unittest.main()
