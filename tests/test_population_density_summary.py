"""Check descriptive strata, same-year age joins, denominators and estimability."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_population_density import build_summary, prepare_panel, correlation


class DensitySummaryTests(unittest.TestCase):
    def fixtures(self):
        population=pd.DataFrame({'codigo_municipio':['05001','05002','05003','05004','05005'],
            'ano_epidemiologico':[2025]*5,'poblacion_total':[100,100,100,100,1000],
            'poblacion_menor_1':[1]*5,'poblacion_1_4':[4]*5,'poblacion_5_14':[15,15,15,15,295]})
        panel=pd.DataFrame({'code':population.codigo_municipio,'year':2025,'department':'ANTIOQUIA',
            'status':'available','density_per_km2':[1,2,3,4,5],'population':population.poblacion_total,
            'cases':[0,1,2,3,40],'notification_record_present':[False,True,True,True,True]})
        panel['incidence_per_100k']=100000*panel.cases/panel.population
        return panel,population

    def test_median_and_pooled_incidence_have_different_denominators(self):
        panel,pop=self.fixtures();summary=build_summary(panel,pop)
        row=summary[summary.dimension.eq('national')].iloc[0]
        self.assertEqual(row.municipalities,5)
        self.assertEqual(row.notification_records,4)
        self.assertEqual(row.incidence_median,2000)
        self.assertAlmostEqual(row.incidence_pooled,100000*46/1400)
        self.assertAlmostEqual(row.rho_density_cases,1)
        self.assertAlmostEqual(row.rho_density_incidence,1)
        strata=summary[summary.dimension.eq('age_composition')].set_index('group_label')
        self.assertEqual(strata.loc['20 a <30 %','municipalities'],4)
        self.assertEqual(strata.loc['30 % o más','municipalities'],1)
        self.assertTrue(pd.isna(strata.loc['30 % o más','rho_density_cases']))

    def test_missing_age_excludes_only_age_stratum_not_national(self):
        panel,pop=self.fixtures();pop.loc[0,'poblacion_1_4']=np.nan
        summary=build_summary(panel,pop)
        self.assertEqual(summary[summary.dimension.eq('national')].iloc[0].municipalities,5)
        self.assertEqual(summary[summary.dimension.eq('national')].iloc[0].age_population_available,4)
        self.assertEqual(summary.loc[summary.dimension.eq('age_composition'),'municipalities'].sum(),4)

    def test_age_population_uses_same_historical_code_harmonization(self):
        panel,pop=self.fixtures()
        panel.loc[0,'code']='94343'
        pop.loc[0,'codigo_municipio']='94343'
        extra=pop.iloc[[0]].copy();extra['codigo_municipio']='94663'
        extra['poblacion_total']=50;extra['poblacion_5_14']=10
        pop=pd.concat([pop,extra],ignore_index=True)
        panel.loc[0,'population']=150
        prepared=prepare_panel(panel,pop)
        row=prepared[prepared.code.eq('94343')].iloc[0]
        self.assertAlmostEqual(row.under_15_share,(1+4+15+1+4+10)/150)

    def test_correlations_require_size_and_variation(self):
        panel,_=self.fixtures()
        self.assertEqual(correlation(panel.iloc[:4],'cases')[1],'fewer_than_5_entities')
        self.assertEqual(correlation(panel.assign(density_per_km2=1),'cases')[1],'constant_density')
        self.assertEqual(correlation(panel.assign(cases=0),'cases')[1],'constant_outcome')

    def test_published_partitions_reconcile_to_same_annual_entities(self):
        table=pd.read_csv(ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_summary_2008_2025.csv')
        self.assertEqual(len(table),810)
        self.assertFalse(table.duplicated(['year','dimension','group']).any())
        for year,rows in table.groupby('year'):
            national=rows[rows.dimension.eq('national')].iloc[0]
            for dimension in ['department','population_size','density_band']:
                group=rows[rows.dimension.eq(dimension)]
                self.assertEqual(group.municipalities.sum(),national.municipalities,(year,dimension))
                self.assertAlmostEqual(group.population.sum(),national.population)
                self.assertAlmostEqual(group.cases.sum(),national.cases)
            self.assertEqual(rows.loc[rows.dimension.eq('age_composition'),'municipalities'].sum(),national.age_population_available)
        recent=table[table.year.eq(2025)&table.dimension.eq('national')].iloc[0]
        self.assertEqual(recent.municipalities,1122)
        self.assertEqual(round(recent.rho_density_cases,3),.496)
        self.assertEqual(round(recent.rho_density_incidence,3),.304)


if __name__=='__main__':unittest.main()
