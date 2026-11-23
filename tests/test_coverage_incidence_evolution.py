"""Check paired changes, coverage eligibility and noninterchangeable summaries."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from analyze_coverage_incidence_evolution import municipal_changes, summarize


class CoverageEvolutionTests(unittest.TestCase):
    def fixture(self):
        rates, cov = [], []
        for code, before, after, pct in [('05001', 10, 10, 80), ('05002', 100, 10, 80), ('05003', 0, 3, 100)]:
            for period, rate in [('2008-2014', before), ('2015-2019', before), ('2020-2021', before), ('2022-2025', after)]:
                rates.append(dict(code=code, horizon=period, adjusted_pre_weights=rate, adjusted_2025_weights=rate*2))
            row=dict(code=code, period='2022-2025', coverage_years_expected=4)
            for dose in ['first_dose', 'booster']:
                row[f'coverage_{dose}_valid_years']=4
                row[f'coverage_{dose}_valid_mean']=pct
            cov.append(row)
        return pd.DataFrame(rates), pd.DataFrame(cov)

    def test_paired_ratios_are_not_ratios_of_group_medians(self):
        changes=municipal_changes(*self.fixture())
        summary, _=summarize(changes)
        group=summary[summary.dose.eq('booster')&summary.baseline.eq('2015-2019')&summary.age_standard.eq('2008-2014')&summary.cutoff.eq(92.9)&summary.group.eq('below')].iloc[0]
        self.assertAlmostEqual(group.median_ratio,.55)
        self.assertNotAlmostEqual(group.median_ratio,group.median_recent_rate/group.median_baseline_rate)
        self.assertEqual(group.median_difference,-45)
        high=changes[changes.code.eq('05003')]
        self.assertTrue(high.ratio_pre.isna().all())
        self.assertTrue(high.difference_pre.eq(3).all())

    def test_incomplete_recent_coverage_excluded_and_duplicate_keys_rejected(self):
        rates,cov=self.fixture()
        cov.loc[0,'coverage_booster_valid_years']=3
        changes=municipal_changes(rates,cov)
        self.assertFalse((changes.code.eq('05001')&changes.dose.eq('booster')).any())
        self.assertTrue((changes.code.eq('05001')&changes.dose.eq('first_dose')).any())
        with self.assertRaises(ValueError):municipal_changes(pd.concat([rates,rates.iloc[:1]]),cov)

    def test_exported_main_denominators_and_sensitivity(self):
        out=ROOT/'docs/data_processed/anomalias_cobertura'
        summary=pd.read_csv(out/'coverage_incidence_evolution_summary.csv')
        main=summary[summary.dose.eq('booster')&summary.baseline.eq('2015-2019')&summary.age_standard.eq('2008-2014')&summary.cutoff.eq(92.9)].set_index('group')
        self.assertEqual(main.loc['below','municipalities'],854)
        self.assertEqual(main.loc['below','ratio_municipalities'],851)
        self.assertEqual(main.loc['at_or_above','municipalities'],248)
        np.testing.assert_allclose(main.loc[['below','at_or_above'],'median_ratio'],[.32211919,.32056291],atol=1e-8)
        for _,group in summary.groupby(['dose','baseline','age_standard','cutoff']):
            self.assertEqual(group.municipalities.sum(),1102)
            self.assertTrue((group.ratio_municipalities+group.zero_baseline).eq(group.municipalities).all())


if __name__=='__main__':unittest.main()
