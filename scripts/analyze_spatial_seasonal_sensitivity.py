"""Sensitivity of existing spatial and seasonal descriptions; originals unchanged."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from generate_moran_lisa import read_points,read_rates,nearest_neighbors,moran_statistics,PERIODS,PERMUTATIONS,SEED
from generate_phase_analysis import read_rates as read_seasonal_rates, PERIODS as SEASONAL_PERIODS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data_processed'


def circular_distance(a,b):
    delta=np.abs(np.asarray(a)-np.asarray(b))%52
    return np.minimum(delta,52-delta)


def smooth_phase(values,width):
    values=np.asarray(values,float)
    if width%2!=1 or width<1:raise ValueError('Smoothing width must be positive and odd')
    smooth=[]
    for i in range(52):
        v=values[(np.arange(i-width//2,i+width//2+1)%52)]
        valid=[float(value) for value in v if np.isfinite(value)]
        smooth.append(sum(valid)/len(valid) if valid else np.nan)
    smooth=np.asarray(smooth)
    if not np.isfinite(smooth).any():return np.nan,np.nan,np.nan
    mean=float(np.nanmean(smooth));amplitude=float(np.nanmax(smooth)-np.nanmin(smooth))
    phase=float(np.nanargmax(smooth)+1) if amplitude>0 and mean>0 else np.nan
    return phase,amplitude,mean


def circular_linear(latitude,weeks):
    x=np.asarray(latitude,float);theta=2*np.pi*(np.asarray(weeks,float)-1)/52
    keep=np.isfinite(x)&np.isfinite(theta);x=x[keep];theta=theta[keep]
    if len(x)<3 or np.std(x)==0 or np.std(np.sin(theta))<1e-12 or np.std(np.cos(theta))<1e-12:return np.nan
    rxc=np.corrcoef(x,np.cos(theta))[0,1];rxs=np.corrcoef(x,np.sin(theta))[0,1];rcs=np.corrcoef(np.cos(theta),np.sin(theta))[0,1]
    if 1-rcs**2<1e-12:return np.nan
    return float(np.sqrt(np.clip((rxc**2+rxs**2-2*rxc*rxs*rcs)/(1-rcs**2),0,1)))


def spatial():
    points=read_points();rates=read_rates();codes=sorted(set(points).intersection(*[set(x) for x in rates.values()]))
    base_global=pd.read_csv(OUT/'heterogeneidad_espacial/moran_global_periods.csv');base_local=pd.read_csv(OUT/'heterogeneidad_espacial/moran_lisa_periods.csv',dtype={'code':str})
    summary=[];local=[]
    for k in [4,8,12]:
        neighbors=nearest_neighbors(points,codes,k=k);rng=np.random.default_rng(SEED)
        for period in PERIODS:
            base=base_local.loc[base_local.period.eq(period)].set_index('code').loc[codes]
            if k==8:
                g=base_global.loc[base_global.period.eq(period)].iloc[0]
                gi,gp=float(g.global_i),float(g.p_positive)
                p,q=base.p_two_sided.to_numpy(),base.q_bh.to_numpy()
                nominal,fdr=base.cluster_nominal.to_numpy(),base.cluster_fdr.to_numpy()
            else:
                values=np.array([rates[period][code] for code in codes])
                gi,gp,_,p,q,_,nominal,fdr=moran_statistics(values,neighbors,rng)
            for code,pv,qv,nom,adj in zip(codes,p,q,nominal,fdr):
                local.append(dict(period=period,neighbors=k,code=code,p_two_sided=pv,q_bh=qv,cluster_nominal=nom,cluster_fdr=adj))
            row=dict(period=period,neighbors=k,municipalities=len(codes),permutations=PERMUTATIONS,global_i=gi,p_positive=gp,
                     hh_nominal=int((nominal=='HH').sum()),hh_fdr=int((fdr=='HH').sum()),ll_fdr=int((fdr=='LL').sum()))
            for method,observed in [('nominal',nominal),('fdr',fdr)]:
                baseline=set(base.index[base['cluster_'+method].eq('HH')]);current=set(np.array(codes)[observed=='HH'])
                union=baseline|current
                row['hh_jaccard_'+method]=len(baseline&current)/len(union) if union else np.nan
                row['hh_added_'+method]=len(current-baseline);row['hh_removed_'+method]=len(baseline-current)
            summary.append(row)
            print(f'Spatial {period}, k={k}: I={gi:.4f}, HH-FDR={row["hh_fdr"]}',flush=True)
    pd.DataFrame(summary).to_csv(OUT/'heterogeneidad_espacial/spatial_sensitivity.csv',index=False,float_format='%.8f')
    pd.DataFrame(local).to_csv(OUT/'heterogeneidad_espacial/spatial_sensitivity_local.csv',index=False,float_format='%.8f')


def seasonal():
    departments,rates=read_seasonal_rates();details=[];summaries=[]
    horizons=[(str(y),[y]) for y in range(2008,2026)]+list(SEASONAL_PERIODS.items())
    for horizon,years in horizons:
        base={};curves={}
        for code in departments:
            curve=[]
            for week in range(1,53):
                values=[rates[y,code][week] for y in years if rates[y,code][week] is not None]
                curve.append(sum(values)/len(values) if values else np.nan)
            curves[code]=curve;base[code]=smooth_phase(curve,5)[0]
        for width in [3,5,9]:
            rows=[]
            for code,(name,latitude) in departments.items():
                peak,amplitude,mean=smooth_phase(curves[code],width)
                distance=float(circular_distance(peak,base[code])) if np.isfinite(peak) and np.isfinite(base[code]) else np.nan
                row=dict(horizon=horizon,department_code=code,department=name,width=width,latitude=latitude,
                         peak_week=peak,amplitude=amplitude,mean_rate=mean,circular_distance_from_5=distance)
                details.append(row);rows.append(row)
            valid=pd.DataFrame(rows).dropna(subset=['peak_week']);distances=valid.circular_distance_from_5.dropna()
            rho=float(spearmanr(valid.latitude,valid.peak_week).statistic) if len(valid)>2 and valid.peak_week.nunique()>1 else np.nan
            summaries.append(dict(horizon=horizon,width=width,departments=len(valid),median_peak_shift=distances.median(),
                p90_peak_shift=distances.quantile(.9),departments_shift_over_4=int(distances.gt(4).sum()),
                spearman_linear=rho,circular_linear_magnitude=circular_linear(valid.latitude,valid.peak_week)))
    pd.DataFrame(details).to_csv(OUT/'estacionalidad/seasonal_sensitivity_departments.csv',index=False,float_format='%.8f')
    pd.DataFrame(summaries).to_csv(OUT/'estacionalidad/seasonal_sensitivity.csv',index=False,float_format='%.8f')
    print('Seasonal sensitivity: 3/5/9 weeks, circular distances and circular-linear association',flush=True)


def main():
    (OUT/'estacionalidad').mkdir(parents=True,exist_ok=True)
    (OUT/'heterogeneidad_espacial').mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True);seasonal();spatial()
    metadata={'spatial':{'neighbors':[4,8,12],'baseline':8,'permutations':PERMUTATIONS,'seed':SEED,
         'weights':'row-standardized directed great-circle k nearest neighbors, same full 1102-entity universe as original',
         'baseline_output':'existing k=8 results reused unchanged','local_test':'same conditional two-sided permutation and period-wise BH as original',
         'jaccard':'HH overlap / union relative to k=8; missing if both sets empty',
         'limits':'k sensitivity only; not contiguity or small-area smoothing; finite Monte Carlo p-values; no test of differences in I'},
         'seasonal':{'widths':[3,5,9],'baseline':5,'window':'circular average of available weeks; national missing week never filled as zero',
         'distance':'min(abs(peak_a-peak_b),52-abs(peak_a-peak_b))','flat_curves':'phase missing if no positive amplitude',
         'circular_reference':'https://raw.githubusercontent.com/circstat/circstat-matlab/master/circ_corrcl.m',
         'circular_linear':'multiple-correlation magnitude of latitude with sin/cos(2*pi*(week-1)/52); no north/south sign',
         'limits':'sensitivity of observed maxima, not sampling confidence intervals, no complete bimodality analysis or causal mechanism'}}
    (OUT/'heterogeneidad_espacial/spatial_seasonal_sensitivity.metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
