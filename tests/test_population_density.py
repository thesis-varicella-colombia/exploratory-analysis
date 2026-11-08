"""Validate supplied areas, same-year denominators, aliases and annual totals."""
import json
import lzma
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import generate_population_density as density


class PopulationDensityTests(unittest.TestCase):
    def areas(self):
        return pd.DataFrame([dict(code='05001',name='Example',department='Example',kind='MUNICIPIO',area_km2=10.)])

    def test_uses_attribute_instead_of_geometry_area(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'area.geojson.xz'
            content={'features':[{'properties':{'mpio_cdpmp':'05001','mpio_cnmbr':'Example','dpto_cnmbr':'Example','mpio_tipo':'MUNICIPIO','mpio_narea':123.45},'geometry':None}]}
            with lzma.open(path,'wt') as target:json.dump(content,target)
            self.assertEqual(density.read_areas(path).iloc[0].area_km2,123.45)

    def test_each_year_uses_its_own_population_and_preserves_zero_cases(self):
        cases=pd.DataFrame([(2020,'05001',20),(2021,'05001',0)],columns=['year','code','cases'])
        pop=pd.DataFrame([('05001',2020,1000),('05001',2021,2000)],columns=['codigo_municipio','ano_epidemiologico','poblacion_total'])
        with patch.object(density,'YEARS',range(2020,2022)):
            result,_=density.build_panel(cases,pop,self.areas())
        self.assertEqual(result.density_per_km2.tolist(),[100,200])
        self.assertEqual(result.incidence_per_100k.tolist(),[2000,0])
        self.assertEqual(result.cases.tolist(),[20,0])

    def test_historical_geography_sums_population_before_computing_density(self):
        cases=pd.DataFrame([(2020,'94343',20)],columns=['year','code','cases'])
        pop=pd.DataFrame([('94343',2020,300),('94663',2020,200)],columns=['codigo_municipio','ano_epidemiologico','poblacion_total'])
        areas=self.areas().assign(code='94343')
        with patch.object(density,'YEARS',[2020]):
            result,_=density.build_panel(cases,pop,areas)
        self.assertEqual(result.iloc[0].population,500)
        self.assertEqual(result.iloc[0].density_per_km2,50)
        self.assertEqual(result.iloc[0].incidence_per_100k,4000)

    def test_published_total_matches_existing_annual_series(self):
        panel=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv',dtype={'code':str})
        annual=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/annual_series_2007_2025.csv')
        self.assertFalse(panel.duplicated(['year','code']).any())
        self.assertEqual(len(panel),19*1122)
        self.assertEqual(panel.groupby('year').cases.sum().tolist(),annual.sort_values('year').notifications.tolist())
        self.assertTrue(panel.groupby('code').area_km2.nunique().eq(1).all())
        visible=panel.loc[panel.status.eq('available')]
        self.assertLess((visible.density_per_km2-visible.population/visible.area_km2).abs().max(),1e-6)
        self.assertTrue(panel.loc[panel.population.le(0),'density_per_km2'].isna().all())


if __name__=='__main__':unittest.main()
