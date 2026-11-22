import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_municipal_priority_candidates import candidate_frame,flags,municipality_summary,order_candidates,AGE_GROUPS,CHILD_GROUPS


class MunicipalPriorityTests(unittest.TestCase):
    def test_order_children_first_minimum_percentage_and_undefined_last(self):
        records=[]
        for code,child,score in [('m110',False,110),('child100',True,100),('m96',False,96),('child85',True,85),('zerochild',True,None),('zerom',False,None)]:
            row=dict(code=code,name=code,department='Example',candidate_children=child,candidate_municipal=True,
                     baseline_municipal=100 if score is not None else 0,
                     incidence_municipal_2024=score if score is not None else 1,incidence_municipal_2025=200)
            for age in CHILD_GROUPS:
                row[f'baseline_{age}']=100 if score is not None else 0
                row[f'incidence_{age}_2024']=score if score is not None else 1
                row[f'incidence_{age}_2025']=200
            records.append(row)
        ordered=order_candidates(pd.DataFrame(records))
        self.assertEqual(ordered.code.tolist(),['child85','child100','zerochild','m96','m110','zerom'])
        self.assertEqual(ordered.sort_baseline_pct.iloc[:2].tolist(),[85,100])
        self.assertTrue(pd.isna(ordered.set_index('code').loc['zerochild','sort_baseline_pct']))
        self.assertEqual(ordered.set_index('code').loc['zerochild','sort_undefined_comparisons'],6)
        self.assertEqual(ordered.set_index('code').loc['zerom','sort_undefined_comparisons'],2)

    def test_independent_municipal_and_child_criteria_with_strict_boundaries(self):
        frame=pd.DataFrame({**{f'baseline_{age}':[100.]*9 for age in AGE_GROUPS},
                            **{f'incidence_{age}':[101.]*9 for age in AGE_GROUPS},
                            'baseline_municipal':[100.]*9,'incidence_municipal':[96.]*9,
                            **{field:[79.]*9 for field in ['first_dose_valid_admin','booster_valid_admin','first_dose_calculated','booster_calculated']}})
        for age in CHILD_GROUPS:frame.loc[1,f'incidence_{age}']=81
        frame.loc[1,'incidence_15_49']=10  # Adult age-specific condition is not required.
        frame.loc[2,'incidence_under_1']=80
        frame.loc[3,['baseline_under_1','incidence_under_1']]=0
        frame.loc[4,['baseline_under_1','incidence_under_1']]=[0,1]
        frame.loc[5,'incidence_under_1']=np.nan
        frame.loc[6,['first_dose_valid_admin','booster_valid_admin','first_dose_calculated','booster_calculated']]=80
        frame.loc[7,'incidence_municipal']=95
        frame.loc[8,'incidence_municipal']=95.00000001
        result=flags(frame)
        self.assertEqual(result.candidate_municipal.tolist(),[True,True,True,True,True,True,False,False,True])
        self.assertEqual(result.candidate_children.tolist(),[True,True,False,False,True,False,False,True,True])
        self.assertTrue((result.candidate_municipal&~result.candidate_children).any())
        self.assertTrue((result.candidate_children&~result.candidate_municipal).any())

    def fixtures(self):
        panel=pd.DataFrame([dict(codigo_municipio='05001',ano_epidemiologico=year,casos_total=5*n,
                                **{f'observed_{age}':n for age in AGE_GROUPS},
                                **{f'population_{age}':1000 for age in AGE_GROUPS})
                            for year,n in [(year,10) for year in range(2008,2015)]+[(2023,20),(2024,11),(2025,11)]])
        coverage=pd.DataFrame([dict(code='05001',year=year,dose=dose,administrative_coverage_pct=110 if year==2024 else 79,
                                   reference_coverage_pct=79)
                              for year in [2023,2024,2025] for dose in ['first_dose','booster']])
        municipal=pd.DataFrame([dict(code='05001',horizon=year,baseline_adjusted=100,adjusted_pre_weights=96) for year in [2023,2024,2025]])
        return panel,coverage,{'05001':{'name':'Example','department':'Example'}},municipal

    def test_own_pooled_age_baseline_and_both_years_with_same_year_coverage(self):
        frame=flags(candidate_frame(*self.fixtures())).sort_values('year')
        self.assertEqual(frame.year.tolist(),[2024,2025])
        self.assertTrue(frame.baseline_under_1.eq(1000).all())
        self.assertTrue(frame.incidence_under_1.eq(1100).all())
        self.assertTrue(pd.isna(frame.iloc[0].first_dose_valid_admin))
        summary=municipality_summary(frame).iloc[0]
        self.assertTrue(summary.candidate_municipal)
        self.assertTrue(summary.candidate_children)
        self.assertEqual(summary.qualifying_years_children,'2024;2025')
        self.assertFalse(municipality_summary(frame[frame.year.eq(2024)]).iloc[0].candidate_children)
        inputs=list(self.fixtures())
        inputs[1].loc[inputs[1].year.eq(2025),['administrative_coverage_pct','reference_coverage_pct']]=80
        single=flags(candidate_frame(*inputs))
        self.assertFalse(municipality_summary(single).iloc[0].candidate_children)
        inputs=list(self.fixtures())
        inputs[0].loc[inputs[0].ano_epidemiologico.eq(2025),'observed_under_1']=8
        self.assertFalse(municipality_summary(flags(candidate_frame(*inputs))).iloc[0].candidate_children)

    def test_cannot_mix_different_criteria_across_years(self):
        inputs=list(self.fixtures())
        # 2024: only municipal passes; 2025: only child passes.
        inputs[0].loc[inputs[0].ano_epidemiologico.eq(2024),'observed_under_1']=1
        inputs[3].loc[inputs[3].horizon.eq(2025),'adjusted_pre_weights']=95
        frame=flags(candidate_frame(*inputs))
        self.assertEqual(frame.candidate_municipal.tolist(),[True,False])
        self.assertEqual(frame.candidate_children.tolist(),[False,True])
        self.assertFalse(municipality_summary(frame).iloc[0].candidate_union)

    def test_zero_age_population_is_missing_not_zero_incidence(self):
        inputs=list(self.fixtures())
        inputs[0].loc[inputs[0].ano_epidemiologico.eq(2024),'population_under_1']=0
        frame=flags(candidate_frame(*inputs))
        self.assertTrue(pd.isna(frame.loc[frame.year.eq(2024),'incidence_under_1']).all())
        self.assertFalse(municipality_summary(frame).iloc[0].candidate_children)

    def test_real_results_match_each_age_and_both_years(self):
        annual=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/municipal_priority_age_annual_2024_2025.csv',dtype={'code':str})
        summary=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/municipal_priority_age_all_2024_2025.csv',dtype={'code':str})
        self.assertEqual(len(annual),1102*2)
        self.assertEqual(set(annual.year),{2024,2025})
        municipal_source=pd.read_csv(ROOT/'docs/data_processed/anomalias_cobertura/comparable_incidence_annual.csv',dtype={'code':str}).set_index(['code','horizon'])
        matched=municipal_source.reindex(pd.MultiIndex.from_frame(annual[['code','year']]))
        np.testing.assert_array_equal(annual.baseline_municipal,matched.baseline_adjusted)
        np.testing.assert_array_equal(annual.incidence_municipal,matched.adjusted_pre_weights)
        coverage=annual[['first_dose_valid_admin','booster_valid_admin','first_dose_calculated','booster_calculated']].lt(80).any(axis=1)
        for key,ages,multiplier in [('municipal',['municipal'],.95),('children',CHILD_GROUPS,.8)]:
            comparisons=[annual[f'incidence_{age}'].round(8).gt((multiplier*annual[f'baseline_{age}']).round(8)) for age in ages]
            expected=np.logical_and.reduce(comparisons)&coverage
            np.testing.assert_array_equal(annual[f'candidate_{key}'],expected)
            actual=annual.groupby('code')[f'candidate_{key}'].all().sort_index()
            np.testing.assert_array_equal(actual,summary.set_index('code')[f'candidate_{key}'].sort_index())
        strict=set(summary.loc[summary.candidate_municipal,'code'])
        children=set(summary.loc[summary.candidate_children,'code'])
        self.assertEqual(len(strict),48)
        self.assertIn('76364',strict)
        self.assertEqual(children,{'13052','19532','20770','23555','27001','44279','70523'})
        self.assertEqual(len(strict&children),6)
        self.assertEqual(children-strict,{'27001'})
        union=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/municipal_priority_union_2024_2025.csv',dtype={'code':str})
        self.assertEqual(set(union.code),strict|children)
        self.assertEqual(len(union),49)
        self.assertEqual(len(union),union.code.nunique())
        self.assertTrue(union.candidate_union.all())
        self.assertTrue(union.iloc[:7].candidate_children.all())
        self.assertFalse(union.iloc[7:].candidate_children.any())
        for _,group in union.groupby('sort_group'):
            self.assertTrue(group.sort_baseline_pct.dropna().is_monotonic_increasing)
        for row in union.to_dict('records'):
            comparisons=[]
            for age in CHILD_GROUPS if row['candidate_children'] else ['municipal']:
                baseline=row[f'baseline_{age}']
                for year in [2024,2025]:
                    current=row[f'incidence_{age}_{year}']
                    if baseline>0 and pd.notna(current):comparisons.append(100*current/baseline)
            if comparisons:self.assertAlmostEqual(row['sort_baseline_pct'],min(comparisons),places=7)
            else:self.assertTrue(pd.isna(row['sort_baseline_pct']))

    def test_empirical_bayes_columns_match_smoothed_rates_without_changing_selection(self):
        union=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/municipal_priority_union_2024_2025.csv',dtype={'code':str})
        eb=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/empirical_bayes/municipal_incidence_eb.csv',dtype={'code':str})
        # Selection is unchanged: still 49 union municipalities.
        self.assertEqual(len(union),49)
        # EB columns exist for the municipal line (via "all") and the child groups.
        for col in ['sort_baseline_pct_eb','sort_group_eb','sort_reference_eb','baseline_eb_municipal','incidence_eb_municipal_2024','baseline_eb_1_4']:
            self.assertIn(col,union.columns)
        annual_eb={(r.code,r.age_group,int(r.year)):r.rate_eb for r in eb[eb.scope.eq('annual')].itertuples()}
        baseline_eb={(r.code,r.age_group):r.rate_eb for r in eb[eb.scope.eq('baseline')].itertuples()}
        # Municipal EB uses the "all" fit, not the age-adjusted rate.
        row=union[union.code.eq('05021')].iloc[0]
        self.assertAlmostEqual(row['baseline_eb_municipal'],baseline_eb[('05021','all')],places=6)
        self.assertAlmostEqual(row['incidence_eb_municipal_2024'],annual_eb[('05021','all',2024)],places=6)
        # sort_baseline_pct_eb equals the minimum calculable EB percentage per row.
        for row in union.to_dict('records'):
            groups=CHILD_GROUPS if row['candidate_children'] else ['municipal']
            comparisons=[]
            for age in groups:
                baseline=row[f'baseline_eb_{age}']
                for year in [2024,2025]:
                    current=row[f'incidence_eb_{age}_{year}']
                    if pd.notna(baseline) and baseline>0 and pd.notna(current):comparisons.append(100*current/baseline)
            if comparisons:self.assertAlmostEqual(row['sort_baseline_pct_eb'],min(comparisons),places=6)
            else:self.assertTrue(pd.isna(row['sort_baseline_pct_eb']))
        # EB ordering is monotone within each EB group.
        ordered=union.sort_values(['sort_group_eb','sort_baseline_pct_eb'],na_position='last')
        for _,group in ordered.groupby('sort_group_eb'):
            self.assertTrue(group.sort_baseline_pct_eb.dropna().is_monotonic_increasing)

    def test_local_empirical_bayes_variant_present_and_distinct(self):
        union=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/municipal_priority_union_2024_2025.csv',dtype={'code':str})
        eb=pd.read_csv(ROOT/'docs/data_processed/cobertura_vacunacion/empirical_bayes/municipal_incidence_eb.csv',dtype={'code':str})
        for col in ['sort_baseline_pct_eb_local','sort_group_eb_local','sort_reference_eb_local','baseline_eb_local_municipal','incidence_eb_local_1_4_2024']:
            self.assertIn(col,union.columns)
        annual=({(r.code,r.age_group,int(r.year)):r.rate_eb_local for r in eb[eb.scope.eq('annual')].itertuples()})
        baseline=({(r.code,r.age_group):r.rate_eb_local for r in eb[eb.scope.eq('baseline')].itertuples()})
        row=union[union.code.eq('05021')].iloc[0]
        # Municipal local line uses the "all" local fit.
        self.assertAlmostEqual(row['baseline_eb_local_municipal'],baseline[('05021','all')],places=6)
        self.assertAlmostEqual(row['incidence_eb_local_municipal_2024'],annual[('05021','all',2024)],places=6)
        # sort_baseline_pct_eb_local is the minimum calculable local EB percentage.
        for rec in union.to_dict('records'):
            groups=CHILD_GROUPS if rec['candidate_children'] else ['municipal']
            comparisons=[]
            for age in groups:
                b=rec[f'baseline_eb_local_{age}']
                for year in [2024,2025]:
                    cur=rec[f'incidence_eb_local_{age}_{year}']
                    if pd.notna(b) and b>0 and pd.notna(cur):comparisons.append(100*cur/b)
            if comparisons:self.assertAlmostEqual(rec['sort_baseline_pct_eb_local'],min(comparisons),places=6)
        # National and local EB differ for at least some municipalities.
        self.assertTrue((union.sort_baseline_pct_eb.round(4)!=union.sort_baseline_pct_eb_local.round(4)).any())


if __name__=='__main__':unittest.main()
