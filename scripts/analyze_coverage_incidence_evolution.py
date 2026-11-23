"""Describe adjusted-incidence changes in fixed retrospective coverage groups.

Municipalities are grouped by 2022-2025 administrative coverage, annually capped
at 100. Compare each municipality to its own earlier rate; summarize municipal
ratios and differences with equal municipality weights. No causal interpretation
or significance claim: coverage and outcomes overlap in time.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from municipal_coverage import coverage_below

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data_processed/anomalias_cobertura'
RECENT = '2022-2025'
BASELINES = ('2008-2014', '2015-2019', '2020-2021')
CUTS = (80., 90., 92.9, 95.)
STANDARDS = {'2008-2014': 'adjusted_pre_weights', '2025': 'adjusted_2025_weights'}


def municipal_changes(rates, coverage):
    """One row per dose, municipality and baseline; complete coverage only."""
    if rates.duplicated(['code', 'horizon']).any():
        raise ValueError('Duplicate rate municipality-period')
    if coverage.duplicated(['code', 'period']).any():
        raise ValueError('Duplicate coverage municipality-period')
    cov = coverage[coverage.period.eq(RECENT)].copy()
    rates = rates[rates.code.ne('all')].copy()
    recent = rates[rates.horizon.eq(RECENT)].set_index('code')
    output = []
    for dose in ('first_dose', 'booster'):
        complete = cov[f'coverage_{dose}_valid_years'].eq(cov.coverage_years_expected)
        selected = cov.loc[complete, ['code', f'coverage_{dose}_valid_mean']].rename(
            columns={f'coverage_{dose}_valid_mean': 'coverage_pct'})
        selected = selected[np.isfinite(selected.coverage_pct) & selected.coverage_pct.between(0, 100)]
        for baseline in BASELINES:
            before = rates[rates.horizon.eq(baseline)].set_index('code')
            frame = selected.set_index('code').copy()
            frame['dose'] = dose
            frame['baseline'] = baseline
            for standard, column in STANDARDS.items():
                suffix = 'pre' if standard == '2008-2014' else '2025'
                frame['baseline_rate_' + suffix] = before[column]
                frame['recent_rate_' + suffix] = recent[column]
                frame['difference_' + suffix] = frame['recent_rate_' + suffix] - frame['baseline_rate_' + suffix]
                frame['ratio_' + suffix] = frame['recent_rate_' + suffix].div(
                    frame['baseline_rate_' + suffix].where(frame['baseline_rate_' + suffix] > 0))
            output.append(frame.reset_index())
    return pd.concat(output, ignore_index=True)


def summarize(changes):
    summaries, correlations = [], []
    for (dose, baseline), frame in changes.groupby(['dose', 'baseline'], sort=True):
        for standard in STANDARDS:
            suffix = 'pre' if standard == '2008-2014' else '2025'
            finite = np.isfinite(frame['baseline_rate_' + suffix]) & np.isfinite(frame['recent_rate_' + suffix])
            matched = frame.loc[finite]
            ratio = matched['ratio_' + suffix]
            ratio_valid = np.isfinite(ratio)
            def rho(values):
                valid = np.isfinite(values)
                return float(spearmanr(matched.loc[valid, 'coverage_pct'], values[valid]).statistic) if valid.sum() > 2 and values[valid].nunique() > 1 and matched.loc[valid, 'coverage_pct'].nunique() > 1 else np.nan
            correlations.append(dict(dose=dose, baseline=baseline, recent=RECENT, age_standard=standard,
                municipalities=len(matched), ratio_municipalities=int(ratio_valid.sum()),
                spearman_ratio=rho(ratio), spearman_difference=rho(matched['difference_' + suffix])))
            for cutoff in CUTS:
                low = coverage_below(matched.coverage_pct, cutoff)
                for label, mask in [('below', low), ('at_or_above', ~low)]:
                    group = matched.loc[mask]
                    ratios = group['ratio_' + suffix]
                    summaries.append(dict(dose=dose, baseline=baseline, recent=RECENT, age_standard=standard,
                        cutoff=cutoff, group=label, municipalities=len(group), ratio_municipalities=int(ratios.notna().sum()),
                        zero_baseline=int(group['baseline_rate_' + suffix].eq(0).sum()),
                        median_baseline_rate=group['baseline_rate_' + suffix].median(),
                        median_recent_rate=group['recent_rate_' + suffix].median(),
                        median_difference=group['difference_' + suffix].median(),
                        median_ratio=ratios.median(), ratio_q1=ratios.quantile(.25), ratio_q3=ratios.quantile(.75)))
    return pd.DataFrame(summaries), pd.DataFrame(correlations)


def main():
    rates = pd.read_csv(OUT/'comparable_incidence_periods.csv', dtype={'code': str, 'horizon': str})
    coverage = pd.read_csv(OUT/'age_standardized_sir_coverage_periods.csv', dtype={'code': str})
    changes = municipal_changes(rates, coverage)
    summary, correlations = summarize(changes)
    for name, frame in [('municipal_changes', changes), ('summary', summary), ('correlations', correlations)]:
        frame.to_csv(OUT/f'coverage_incidence_evolution_{name}.csv', index=False, float_format='%.8f')
    metadata = dict(recent=RECENT, baselines=list(BASELINES), cutoffs=list(CUTS), main_cutoff=92.9,
        age_standards=STANDARDS, universe='same 1102 municipalities as SIR; require complete usable 2022-2025 coverage per dose',
        groups='fixed retrospective groups defined by recent coverage; never reclassify earlier years',
        coverage='arithmetic mean after annual cap at 100, no additional lag, original percentages retained in source',
        outcomes='municipality-specific direct age-adjusted notification rates; standard proportions fixed across periods',
        summaries='equal municipality weight; median of individual recent/baseline ratios, not ratio of group medians or pooled incidence',
        zero_baseline='exclude zero baseline from ratios and Spearman of ratios, retain absolute differences; report denominators',
        uncertainty='descriptive full-panel summaries, no confidence intervals, hypothesis tests or equivalence claim',
        limits='concurrent retrospective grouping, overlapping groups across dose/cutoffs, ecological confounding, notification changes, small counts, no causal vaccine effect',
        sources=['comparable_incidence_periods.csv', 'age_standardized_sir_coverage_periods.csv'])
    (OUT/'coverage_incidence_evolution.metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    print(summary[summary.baseline.eq('2015-2019') & summary.age_standard.eq('2008-2014')].to_string(index=False))
    print(correlations.to_string(index=False))


if __name__ == '__main__':
    main()
