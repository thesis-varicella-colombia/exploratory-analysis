"""Screen all original municipal Rt series for extremes and sustained episodes.

Descriptive research priorities, not a public-health risk ranking. Uses the
existing daily estimates; it neither refits Rt nor changes published charts.
Run from the repository root with .venv/bin/python scripts/analyze_rt_municipal_priorities.py.
"""
import gzip,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd

MIN_HIGH_RUN_DAYS = 7
MIN_LOW_RUN_DAYS = 14
VERY_HIGH_RT = 5
MATCH_TOLERANCE_DAYS = 14

def audit_notification_clusters(root, output):
    """Aggregate a focused audit; never export individual surveillance records."""
    contexts=[('76364',2017,'2017-09-01','2017-10-31'),
              ('76250',2017,'2017-04-01','2017-05-31'),
              ('19532',2023,'2023-07-01','2023-08-31')]
    records=[]
    columns=['COD_DPTO_R','COD_MUN_R','AJUSTE','FEC_NOT','INI_SIN']
    for year in sorted({item[1] for item in contexts}):
        path=root/'data/sivigila/csv'/f'Datos_{year}_831.csv'
        if not path.exists():
            continue
        codes=[code for code,source_year,_,_ in contexts if source_year==year]
        selected=[]
        for chunk in pd.read_csv(path,usecols=columns,dtype=str,keep_default_na=False,
                                 encoding='utf-8-sig',chunksize=50000):
            chunk['code']=chunk.COD_DPTO_R.str.strip().str.zfill(2)+chunk.COD_MUN_R.str.strip().str.zfill(3)
            chunk=chunk[chunk.code.isin(codes)&~chunk.AJUSTE.str.strip().str.upper().isin(['6','D'])].copy()
            if len(chunk):selected.append(chunk)
        if not selected:continue
        frame=pd.concat(selected)
        for column in ['FEC_NOT','INI_SIN']:
            frame[column]=pd.to_datetime(frame[column].str.extract(r'^(\d{1,2}/\d{1,2}/\d{4})',expand=False),
                                          format='%d/%m/%Y',errors='coerce')
        for code,source_year,start,end in contexts:
            if source_year!=year:continue
            rows=frame[frame.code.eq(code)&frame.FEC_NOT.between(start,end)]
            delay=(rows.FEC_NOT-rows.INI_SIN).dt.days
            records.append(dict(code=code,source_year=year,notification_start=start,notification_end=end,
                records=len(rows),valid_pairs=int(delay.notna().sum()),missing_pairs=int(delay.isna().sum()),
                negative_delays=int(delay.lt(0).sum()),delay_median=delay.median(),
                delay_q1=delay.quantile(.25),delay_q3=delay.quantile(.75),
                delay_max=delay.max(),delay_over_30_days=int(delay.gt(30).sum())))
    pd.DataFrame(records).to_csv(output/'notification_delay_audit.csv',index=False,float_format='%.8f')
    return len(records)

def main():
    root=Path(__file__).resolve().parents[1]
    output=root/'docs/data_processed/numero_reproductivo/municipal_priorities'
    output.mkdir(parents=True,exist_ok=True)
    source=root/'docs/data_processed/numero_reproductivo/rt_stratified'
    m=json.loads((source/'manifest.json').read_text()); summaries=[];episodes=[]
    places={r.code:r for r in pd.read_csv(root/'docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv',dtype={'code':str}).query('year==2025').itertuples()}
    periods={'2008-2025':(2008,2025),'2008-2014':(2008,2014),'2015-2019':(2015,2019),'2020-2021':(2020,2021),'2022-2025':(2022,2025)}
    for method in ['notification','symptom']:
     cal=m['calendars'][method];dates=np.array(cal['date']);years=np.array(cal['year']);observed=~np.array(cal['missing_week'])
     for series in m['series']:
      if series['dimension']!='municipality':continue
      d=json.loads(gzip.decompress((source/method/(series['id']+'.json.gz')).read_bytes()))
      rt,lo,hi,c,count=[np.array(d[k],float) for k in ['rt','rt_lower_95','rt_upper_95','window_cases','count']]
      valid=observed&np.isfinite(rt)&(rt>0)&np.isfinite(lo)&np.isfinite(hi)&np.isfinite(c)&(c>=0)&(lo<=rt)&(hi>=rt)
      width=np.divide(hi-lo,rt,out=np.full(len(rt),np.nan),where=valid)
      prior_a=1/(1+c);prior_b=.2*rt/(1+c)
      qualified=valid&(width<=1)&(prior_a<=.1)&(prior_b<=.1)
      common={'code':series['code'],'name':series['name'],'department':places[series['code']].department,'method':method}
      for period,(start,end) in periods.items():
       selected=(years>=start)&(years<=end);good=selected&qualified;finite=selected&valid
       row={**common,'period':period,'cases':int(np.nansum(count[selected])),'observed_days':int((selected&observed).sum()),'estimated_days':int(finite.sum()),'qualified_days':int(good.sum()),'strict_days':int((finite&(width<=.5)&(prior_a<=.1)&(prior_b<=.1)).sum()),'lenient_days':int((finite&(width<=2)&(prior_a<=.1)&(prior_b<=.1)).sum()),'high_days':int((good&(rt>=2)&(lo>1)).sum()),'low_days':int((good&(rt<=.5)&(hi<1)).sum())}
       for prefix,mask in [('raw',finite),('qualified',good)]:
        ix=np.flatnonzero(mask)
        for label,fun in [('max',np.argmax),('min',np.argmin)]:
         if len(ix):
          i=ix[fun(rt[ix])]
          row.update({f'{prefix}_{label}':rt[i],f'{prefix}_{label}_date':dates[i],f'{prefix}_{label}_lo':lo[i],f'{prefix}_{label}_hi':hi[i],f'{prefix}_{label}_cases':c[i],f'{prefix}_{label}_relative_width':width[i],f'{prefix}_{label}_prior_shape_fraction':prior_a[i],f'{prefix}_{label}_prior_rate_fraction':prior_b[i]})
       summaries.append(row)
      for direction,mask in [('high',qualified&(rt>=2)&(lo>1)),('low',qualified&(rt<=.5)&(hi<1))]:
       ix=np.flatnonzero(mask)
       for run in np.split(ix,np.flatnonzero(np.diff(ix)>1)+1):
        if not len(run):continue
        peak=run[np.argmax(rt[run]) if direction=='high' else np.argmin(rt[run])]
        episodes.append({**common,'direction':direction,'start':dates[run[0]],'end':dates[run[-1]],'days':len(run),'peak_date':dates[peak],'peak_rt':rt[peak],'peak_lo':lo[peak],'peak_hi':hi[peak],'peak_window_cases':c[peak],'episode_count':int(np.nansum(count[run])),'near_2008_gap':bool(((dates[run]>='2008-12-01')&(dates[run]<='2009-02-28')).any()),'sensitive_2013':bool(((dates[run]>='2013-01-01')&(dates[run]<='2014-03-31')).any())})
    s=pd.DataFrame(summaries);e=pd.DataFrame(episodes)
    s.to_csv(output/'municipal_summary.csv',index=False,float_format='%.8f');e.to_csv(output/'qualified_episodes.csv',index=False,float_format='%.8f')

    # Reconcile the precision screen with every published municipality/period/method.
    reference=pd.read_csv(root/'docs/data_processed/numero_reproductivo/rt_information/all_periods.csv',dtype={'id':str})
    reference=reference[reference.dimension.eq('municipality')&reference.width_limit.eq(1)].copy()
    reference['code']=reference.id.str.replace('municipality_','',regex=False)
    check=s[s.period.ne('2008-2025')].merge(reference,on=['code','method','period'],validate='one_to_one')
    assert len(check)==1122*2*4
    assert check.qualified_days.eq(check.information_days).all()
    assert check.estimated_days_x.eq(check.estimated_days_y).all()
    assert s.qualified_days.le(s.estimated_days).all()
    assert s.strict_days.le(s.qualified_days).all() and s.qualified_days.le(s.lenient_days).all()

    # Compare extreme runs across the two date series. A tolerance is for matching
    # surveillance episodes; it does not estimate or correct reporting delays.
    pairs=[]
    eligible_runs=e[(e.direction.eq('high')&e.days.ge(MIN_HIGH_RUN_DAYS))|
                    (e.direction.eq('low')&e.days.ge(MIN_LOW_RUN_DAYS))]
    for (code,direction),group in eligible_runs.groupby(['code','direction']):
        for a in group[group.method.eq('notification')].itertuples():
            for b in group[group.method.eq('symptom')].itertuples():
                gap=(max(pd.Timestamp(a.start),pd.Timestamp(b.start))-min(pd.Timestamp(a.end),pd.Timestamp(b.end))).days
                if gap>MATCH_TOLERANCE_DAYS:continue
                pairs.append(dict(code=code,name=a.name,department=a.department,direction=direction,
                    notification_start=a.start,notification_end=a.end,notification_days=a.days,
                    notification_peak=a.peak_rt,notification_peak_date=a.peak_date,
                notification_peak_lo=a.peak_lo,notification_peak_hi=a.peak_hi,
                    symptom_start=b.start,symptom_end=b.end,symptom_days=b.days,
                    symptom_peak=b.peak_rt,symptom_peak_date=b.peak_date,
                symptom_peak_lo=b.peak_lo,symptom_peak_hi=b.peak_hi,
                    min_days=min(a.days,b.days),gap_days=max(0,gap),
                    sensitive_2013=a.sensitive_2013 or b.sensitive_2013,
                    near_2008_gap=a.near_2008_gap or b.near_2008_gap))
    paired=pd.DataFrame(pairs)
    paired.to_csv(output/'paired_sustained_episodes.csv',index=False,float_format='%.8f')

    recent=s[s.period.eq('2022-2025')]
    n=recent[recent.method.eq('notification')].set_index('code')
    y=recent[recent.method.eq('symptom')].set_index('code')
    priority=[]
    recent_pairs=paired[paired.notification_start.ge('2022-01-01')&paired.symptom_start.ge('2022-01-01')&paired.direction.eq('high')]
    for code in recent_pairs.code.unique():
        best=recent_pairs[recent_pairs.code.eq(code)].sort_values(['min_days','notification_peak'],ascending=False).iloc[0]
        priority.append(dict(code=code,name=best['name'],department=best.department,category='recent_sustained_high_both_dates',
            notification_start=best.notification_start,notification_end=best.notification_end,
            symptom_start=best.symptom_start,symptom_end=best.symptom_end,
            notification_peak=best.notification_peak,notification_peak_date=best.notification_peak_date,
            notification_peak_lo=best.notification_peak_lo,notification_peak_hi=best.notification_peak_hi,
            symptom_peak=best.symptom_peak,symptom_peak_date=best.symptom_peak_date,
            symptom_peak_lo=best.symptom_peak_lo,symptom_peak_hi=best.symptom_peak_hi,
            notification_days=best.notification_days,symptom_days=best.symptom_days))
    for code,a in n.iterrows():
        b=y.loc[code]
        if not (a.get('qualified_max',np.nan)>=VERY_HIGH_RT and b.get('qualified_max',np.nan)>=VERY_HIGH_RT):continue
        gap=abs((pd.Timestamp(a.qualified_max_date)-pd.Timestamp(b.qualified_max_date)).days)
        if gap>MATCH_TOLERANCE_DAYS:continue
        priority.append(dict(code=code,name=a['name'],department=a.department,category='recent_very_high_both_dates',
            notification_peak=a.qualified_max,notification_peak_date=a.qualified_max_date,
            notification_peak_lo=a.qualified_max_lo,notification_peak_hi=a.qualified_max_hi,
            symptom_peak=b.qualified_max,symptom_peak_date=b.qualified_max_date,
            symptom_peak_lo=b.qualified_max_lo,symptom_peak_hi=b.qualified_max_hi))
    lowpairs=paired[paired.direction.eq('low')&~paired.sensitive_2013&~paired.near_2008_gap]
    for code in lowpairs.code.unique():
        best=lowpairs[lowpairs.code.eq(code)].sort_values('min_days',ascending=False).iloc[0]
        priority.append(dict(code=code,name=best['name'],department=best.department,category='sustained_low_both_dates',
            notification_peak=best.notification_peak,notification_peak_date=best.notification_peak_date,
            symptom_peak=best.symptom_peak,symptom_peak_date=best.symptom_peak_date,
            notification_days=best.notification_days,symptom_days=best.symptom_days))
    pd.DataFrame(priority).sort_values(['category','code']).to_csv(output/'priority_candidates.csv',index=False,float_format='%.8f')
    sustained=pd.DataFrame([row for row in priority if row['category']=='recent_sustained_high_both_dates'])
    sustained['min_days']=sustained[['notification_days','symptom_days']].min(axis=1)
    sustained=sustained.sort_values(['symptom_peak','code'],ascending=[False,True])
    peaks=pd.DataFrame([row for row in priority if row['category']=='recent_very_high_both_dates'])
    peaks=peaks.sort_values(['symptom_peak','code'],ascending=[False,True])
    table_metadata=dict(version=1,period='2022-2025',width_limit=1,prior_fraction_max=.1,
        sustained_min_rt=2,sustained_min_days=MIN_HIGH_RUN_DAYS,
        peak_min_rt=VERY_HIGH_RT,matching_tolerance_days=MATCH_TOLERANCE_DAYS,
        sustained_count=len(sustained),peak_count=len(peaks),
        overlap_count=len(set(sustained.code)&set(peaks.code)),
        unique_municipalities=len(set(sustained.code)|set(peaks.code)),
        sort_field='symptom_peak',sort_direction='descending',sort_tie_breaker='code')
    tables={**table_metadata,'sustained':json.loads(sustained.to_json(orient='records',force_ascii=False)),
            'peaks':json.loads(peaks.to_json(orient='records',force_ascii=False))}
    (output/'web_tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    review_specs=[('76364','2008-2025','late_notification_cluster_2017'),
                  ('76250','2008-2025','historical_high_low_reversal_2017'),
                  ('70508','2008-2025','high_notification_signal_during_2013_symptom_gaps'),
                  ('05001','2008-2025','very_low_values_near_2008_gap'),
                  ('08001','2022-2025','recent_short_low_episode_2024')]
    reviews=[]
    for code,period,reason in review_specs:
        for row in s[s.code.eq(code)&s.period.eq(period)].to_dict('records'):
            reviews.append({**row,'review_reason':reason})
    pd.DataFrame(reviews).to_csv(output/'quality_review_candidates.csv',index=False,float_format='%.8f')

    audited_clusters=audit_notification_clusters(root,output)
    metadata=dict(source='docs/data_processed/numero_reproductivo/rt_stratified',
        manifest_sha256=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        municipalities=1122,date_methods=['notification','symptom'],periods=periods,
        precise_screen=dict(relative_width_max=1,prior_shape_fraction_max=.1,prior_rate_fraction_max=.1),
        width_sensitivity=[.5,1,2],extremes=dict(high_min=2,low_max=.5,credible_interval_excludes_one=True),
        paired_runs=dict(min_days_each_high=MIN_HIGH_RUN_DAYS,min_days_each_low=MIN_LOW_RUN_DAYS,
                        max_calendar_gap_days=MATCH_TOLERANCE_DAYS,independent_confirmation=False),
        very_high=dict(minimum_peak_each_method=VERY_HIGH_RT,max_peak_date_difference_days=MATCH_TOLERANCE_DAYS),
        web_tables=table_metadata,
        quality_flags=dict(symptom_data_gap_window=['2013-01-01','2014-03-31'],notification_gap_context=['2008-12-01','2009-02-28']),
        reconciliation_rows=len(check),summary_rows=len(s),episode_rows=len(e),paired_episode_rows=len(paired),
        candidate_rows=len(priority),candidate_municipalities=len({row['code'] for row in priority}),
        additional_review_municipalities=len(review_specs),
        raw_clusters_audited=audited_clusters,
        interpretation='descriptive, retrospective screening; thresholds are exploratory; overlapping windows and both date series are dependent; no Rt re-estimation; raw-date audit restricted to the listed three clusters')
    (output/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(f'Analyzed {len(s)} summaries and {len(e)} extreme runs; reconciled {len(check)} published precision counts.')
    print(f'Candidate municipalities: {metadata["candidate_municipalities"]}; recent sustained high in both dates: {recent_pairs.code.nunique()}')


if __name__ == "__main__":
    main()
