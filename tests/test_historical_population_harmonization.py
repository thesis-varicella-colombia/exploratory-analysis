"""Use current Barrancominas geography without treating Mapiripana as a municipality."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from generate_age_standardized_sir import harmonize_age_population,read_panel,AGE_GROUPS,POPULATION_COLUMNS


class HistoricalPopulationHarmonizationTests(unittest.TestCase):
    def test_separate_historical_areas_sum_once_and_post_integration_zeros_add_nothing(self):
        rows=[]
        for code,year,value in [('94343',2019,10),('94663',2019,2),('94343',2020,15),('94663',2020,0)]:
            rows.append({'codigo_municipio':code,'ano_epidemiologico':year,**{column:value for column in POPULATION_COLUMNS.values()}})
        result=harmonize_age_population(pd.DataFrame(rows))
        self.assertEqual(result.codigo_municipio.tolist(),['94343','94343'])
        self.assertEqual(result.poblacion_menor_1.tolist(),[12,15])
        self.assertEqual(result[list(POPULATION_COLUMNS.values())].sum(axis=1).tolist(),[60,75])
        pd.testing.assert_frame_equal(result,harmonize_age_population(result))

    def test_positive_post_integration_child_population_requires_overlap_review(self):
        rows=[{'codigo_municipio':code,'ano_epidemiologico':2020,**{column:1 for column in POPULATION_COLUMNS.values()}} for code in ['94343','94663']]
        with self.assertRaisesRegex(ValueError,'verify overlap'):
            harmonize_age_population(pd.DataFrame(rows))

    def test_missing_historical_age_cannot_become_partial_population(self):
        rows=[{'codigo_municipio':code,'ano_epidemiologico':2019,**{column:1 for column in POPULATION_COLUMNS.values()}} for code in ['94343','94663']]
        rows[1]['poblacion_menor_1']=np.nan
        self.assertTrue(pd.isna(harmonize_age_population(pd.DataFrame(rows)).iloc[0].poblacion_menor_1))

    def test_all_age_denominators_and_cases_match_density_panel(self):
        panel=read_panel().rename(columns={'codigo_municipio':'code','ano_epidemiologico':'year'})
        density=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv',dtype={'code':str})
        joined=panel.merge(density,on=['code','year'],validate='one_to_one')
        self.assertEqual(len(joined),1102*18)
        self.assertNotIn('94663',set(joined.code))
        np.testing.assert_array_equal(joined[['population_'+g for g in AGE_GROUPS]].sum(axis=1),joined.population)
        np.testing.assert_array_equal(joined.casos_total,joined.cases)
        pop=joined[joined.code.eq('94343')].set_index('year')
        self.assertEqual(pop.loc[2008,'population'],6214)
        self.assertEqual(pop.loc[2008,'population_under_1'],238)
        self.assertEqual(pop.loc[2020,'population'],9960)
        self.assertEqual(pop.loc[2025,'population'],11709)
        raw=pd.read_csv(ROOT/'data/population_municipal_2007_2025.csv',dtype={'codigo_municipio':str})
        post=raw[raw.codigo_municipio.eq('94663')&raw.ano_epidemiologico.ge(2020)]
        self.assertTrue(post[list(POPULATION_COLUMNS.values())].eq(0).all().all())

    def test_map_rates_have_same_current_geography_and_population(self):
        spatial=pd.read_csv(ROOT/'docs/data_processed/heterogeneidad_espacial/spatial_series_2008_2025.csv',dtype={'code':str})
        self.assertNotIn('94663',set(spatial.code))
        density=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv',dtype={'code':str})
        density['period']=density.year.astype(str)
        annual=spatial[spatial.period.str.fullmatch(r'\d{4}')].merge(density,on=['period','code'],validate='one_to_one')
        valid=annual.population.notna()
        np.testing.assert_array_equal(annual.loc[valid,'population_years'],annual.loc[valid,'population'])
        np.testing.assert_array_equal(annual.notifications,annual.cases)


if __name__=='__main__':unittest.main()
