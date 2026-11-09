"""Describe daily Rt precision and prior contribution from original full series.

Criteria are exploratory screening rules, not a guarantee of surveillance quality
or a validation of assumptions. No estimates or visualization files are changed.
"""
from pathlib import Path
import csv
import gzip
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/data_processed/numero_reproductivo/rt_stratified'
OUTPUT=ROOT/'docs/data_processed/numero_reproductivo/rt_information'
PERIODS={'2008-2014':range(2008,2015),'2015-2019':range(2015,2020),'2020-2021':range(2020,2022),'2022-2025':range(2022,2026)}
WIDTH_LIMITS=(0.5,1.0,2.0)


def number(value):
    return round(float(value),8) if np.isfinite(value) else None


def longest_run(mask,dates):
    index=np.flatnonzero(mask)
    if len(index)==0:return {'start':None,'end':None,'days':0}
    runs=np.split(index,np.flatnonzero(np.diff(index)>1)+1)
    longest=max(runs,key=len)
    return {'start':dates[int(longest[0])],'end':dates[int(longest[-1])],'days':len(longest)}


def assess(data,calendar,prior_shape=1.0,prior_rate=.2):
    rt=np.array(data['rt'],float);low=np.array(data['rt_lower_95'],float);high=np.array(data['rt_upper_95'],float)
    cases=np.array(data['window_cases'],float);years=np.array(calendar['year'],int);missing=np.array(calendar['missing_week'],bool)
    if any(len(x)!=len(rt) for x in [low,high,cases,years,missing]):raise ValueError('Rt payload/calendar length mismatch')
    observed=~missing
    estimated=observed&np.isfinite(rt)&(rt>0)&np.isfinite(low)&np.isfinite(high)&np.isfinite(cases)&(cases>=0)&(high>=low)&(low<=rt)&(rt<=high)
    relative=np.divide(high-low,rt,out=np.full(len(rt),np.nan),where=estimated)
    # Posterior Gamma(a+C,b+Lambda): formal contributions of the prior to its two parameters.
    shape_fraction=prior_shape/(prior_shape+cases)
    rate_fraction=prior_rate*rt/(prior_shape+cases)
    low_prior=(shape_fraction<=.1)&(rate_fraction<=.1)
    rows=[]
    for period,period_years in PERIODS.items():
        selected=np.isin(years,list(period_years));den=int((selected&observed).sum());est=selected&estimated
        for limit in WIDTH_LIMITS:
            info=est&low_prior&(relative<=limit)
            run=longest_run(info,calendar['date'])
            rows.append(dict(method='',period=period,width_limit=limit,observed_days=den,estimated_days=int(est.sum()),
                estimated_pct=number(100*est.sum()/den) if den else None,information_days=int(info.sum()),
                information_pct_observed=number(100*info.sum()/den) if den else None,
                information_pct_estimated=number(100*info.sum()/est.sum()) if est.any() else None,
                median_relative_width=number(np.median(relative[est])) if est.any() else None,
                median_window_cases=number(np.median(cases[est])) if est.any() else None,
                interval_above_one=int((info&(low>1)).sum()),interval_below_one=int((info&(high<1)).sum()),
                interval_includes_one=int((info&(low<=1)&(high>=1)).sum()),
                longest_start=run['start'],longest_end=run['end'],longest_days=run['days']))
    return rows


def main():
    manifest=json.loads((SOURCE/'manifest.json').read_text());method=manifest['method']
    a=(method['prior_mean']/method['prior_sd'])**2;b=method['prior_mean']/method['prior_sd']**2
    OUTPUT.mkdir(parents=True,exist_ok=True)
    selected=[s for s in manifest['series'] if s['dimension']!='age'];all_rows=[]
    for i,series in enumerate(selected):
        rows=[]
        for date_method in ['notification','symptom']:
            data=json.loads(gzip.decompress((SOURCE/date_method/(series['id']+'.json.gz')).read_bytes()))
            part=assess(data,manifest['calendars'][date_method],a,b)
            for row in part:row['method']=date_method
            rows.extend(part)
        (OUTPUT/(series['id']+'.json')).write_text(json.dumps({'id':series['id'],'name':series['name'],'rows':rows},ensure_ascii=False,separators=(',',':'),allow_nan=False))
        for row in rows:all_rows.append({'id':series['id'],'dimension':series['dimension'],'name':series['name'],**row})
        if i%100==0:print(f'Rt diagnostics: {i+1}/{len(selected)}',flush=True)
    with (OUTPUT/'all_periods.csv').open('w',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=list(all_rows[0]));writer.writeheader();writer.writerows(all_rows)
    metadata={'source':'rt_stratified daily original JSON, not rt_visualization averages','series':len(selected),'periods':{p:list(y) for p,y in PERIODS.items()},
       'width_limits':list(WIDTH_LIMITS),'relative_width':'(upper95-lower95)/posterior_mean',
       'prior_rule':'both a/(a+C) and b/(b+Lambda) <= 0.1; second fraction inferred as b*Rt/(a+C) from rounded original mean',
       'prior_shape':a,'prior_rate':b,'criteria':'finite published daily posterior, relative width below selected limit, low formal prior contribution',
       'precision':'source posterior parameters/quantiles are rounded to 6 decimals; derived diagnostics inherit that precision',
       'longest_run':'consecutive calendar days meeting criteria within period, not independently validated episodes',
       'missingness':'observed days exclude national missing weeks; estimation excludes warmup and unestimable windows',
       'limits':'overlapping 14-day windows are dependent; these are descriptive thresholds, not sufficient-data guarantees; no sensitivity to alternative priors/windows/serial intervals is claimed',
       'reference':'https://pmc.ncbi.nlm.nih.gov/articles/PMC3816335/'}
    (OUTPUT/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print(f'Generated {len(selected)} territorial diagnostic files and {len(all_rows)} period rows',flush=True)


if __name__=='__main__':main()
