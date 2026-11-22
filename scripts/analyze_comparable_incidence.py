"""Direct age standardization with common weights for temporal municipal contrasts.

Keep the existing SIR panel and its universe unchanged. Direct standardized rates
use known-age notifications; crude all-age rates and unknown-age shares remain
explicit. Fixed national age weights from 2008–2014 are compared with 2025 weights.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from generate_age_standardized_sir import read_panel, AGE_GROUPS, PERIODS

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/data_processed'


def reference_weights(panel,years):
    sums=panel.loc[panel.ano_epidemiologico.isin(years),['population_'+g for g in AGE_GROUPS]].sum().to_numpy(float)
    if not np.isfinite(sums).all() or (sums<=0).any():raise ValueError('Invalid reference age populations')
    return sums/sums.sum()


def direct_rates(group,weights):
    population=group[['population_'+g for g in AGE_GROUPS]].sum().to_numpy(float)
    cases=group[['observed_'+g for g in AGE_GROUPS]].sum().to_numpy(float)
    return 100000*np.dot(weights,cases/population) if (population>0).all() else np.nan


def calculate(panel):
    w=reference_weights(panel,range(2008,2015));alt=reference_weights(panel,[2025])
    columns=['population_'+g for g in AGE_GROUPS]+['observed_'+g for g in AGE_GROUPS]+['casos_total','casos_edad_desconocida']
    output=[]
    for horizon,years in [(str(y),[y]) for y in range(2008,2026)]+list(PERIODS.items()):
        selected=panel.loc[panel.ano_epidemiologico.isin(years)]
        for code,group in selected.groupby('codigo_municipio',sort=True):
            n=group[['population_'+g for g in AGE_GROUPS]].to_numpy(float).sum()
            all_cases=float(group.casos_total.sum());unknown=float(group.casos_edad_desconocida.sum())
            output.append(dict(code=code,horizon=horizon,years=len(years),population_years=n,cases=all_cases,
                unknown_age_cases=unknown,unknown_age_pct=100*unknown/all_cases if all_cases>0 else np.nan,
                crude_all_age=100000*all_cases/n if n>0 else np.nan,
                crude_known_age=100000*(all_cases-unknown)/n if n>0 else np.nan,
                adjusted_pre_weights=direct_rates(group,w),adjusted_2025_weights=direct_rates(group,alt)))
        # Aggregate counts and age populations before standardizing the national panel.
        summed=selected[columns].sum().to_frame().T
        n=sum(float(summed['population_'+g].iloc[0]) for g in AGE_GROUPS)
        total=float(summed.casos_total.iloc[0]);unknown=float(summed.casos_edad_desconocida.iloc[0])
        output.append(dict(code='all',horizon=horizon,years=len(years),population_years=n,cases=total,
            unknown_age_cases=unknown,unknown_age_pct=100*unknown/total if total>0 else np.nan,
            crude_all_age=100000*total/n,crude_known_age=100000*(total-unknown)/n,
            adjusted_pre_weights=direct_rates(summed,w),adjusted_2025_weights=direct_rates(summed,alt)))
    result=pd.DataFrame(output)
    baseline=result.loc[result.horizon.eq('2008-2014'),['code','adjusted_pre_weights']].rename(columns={'adjusted_pre_weights':'baseline_adjusted'})
    result=result.merge(baseline,on='code',validate='many_to_one')
    result['difference_from_pre']=result.adjusted_pre_weights-result.baseline_adjusted
    result['ratio_to_pre']=result.adjusted_pre_weights.div(result.baseline_adjusted.where(result.baseline_adjusted>0))
    return result,w,alt


def main():
    (OUTPUT/'anomalias_cobertura').mkdir(parents=True,exist_ok=True)
    panel=read_panel();result,w,alt=calculate(panel)
    geography=json.loads((OUTPUT/'cartografia/municipal_boundaries_dane.geojson').read_text())
    names={f['properties']['code']:f['properties']['name'] for f in geography['features']}
    result['name']=result.code.map(names).fillna('Panel nacional de 1.102 municipios')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    result[result.horizon.isin(PERIODS)].to_csv(OUTPUT/'anomalias_cobertura/comparable_incidence_periods.csv',index=False,float_format='%.8f')
    result[~result.horizon.isin(PERIODS)].to_csv(OUTPUT/'anomalias_cobertura/comparable_incidence_annual.csv',index=False,float_format='%.8f')
    metadata={'universe':'same 1102 municipalities and age counts/populations as existing SIR read_panel; national row is this panel, not all national entities',
        'age_groups':list(AGE_GROUPS),'reference_years':list(range(2008,2015)),'weights':w.tolist(),'sensitivity_year':2025,'sensitivity_weights':alt.tolist(),
        'formula':'100000 * sum(age_weight * sum(known_age_cases) / sum(age_population_years))',
        'baseline':'municipality-specific directly standardized rate in 2008-2014 with the same fixed weights',
        'zero_baseline':'ratio missing if baseline rate is zero; absolute difference retained',
        'unknown_age':'excluded from standardized and crude-known-age rates; reported separately; crude-all-age includes them',
        'interpretation':'descriptive standardized indexes, not actual individual risks or vaccine effects; no sampling confidence intervals are supplied',
        'population_geography':'same corrected SIR read_panel: normalize codes and sum age populations before geographic filtering; historical Mapiripana 94663 included in Barrancominas 94343, not a separate municipality',
        'reference':'https://www.cdc.gov/nchs/hus/sources-definitions/age-adjustment.htm'}
    (OUTPUT/'anomalias_cobertura/comparable_incidence.metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print(result[result.code.eq('all')&result.horizon.isin(PERIODS)][['horizon','crude_all_age','adjusted_pre_weights','adjusted_2025_weights','ratio_to_pre']].round(3).to_string(index=False))


if __name__=='__main__':main()
