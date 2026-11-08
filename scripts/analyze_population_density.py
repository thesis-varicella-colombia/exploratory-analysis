"""Publish annual and stratified descriptive support for density scatter plots.

Use the same valid entities and zeros as the plots. Stratification is descriptive,
not age standardization, adjustment, independent replication or causal inference.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from municipal_coverage import normalize_codes, complete_sum

ROOT=Path(__file__).resolve().parents[1]
MIN_ENTITIES=5
DEPARTMENTS_NORTH_TO_SOUTH=('88','44','08','47','20','70','13','23','54','05','68','81','27','15','85','17','66','25','99','63','11','73','76','50','94','41','19','95','52','18','97','86','91')
POPULATION_LABELS=['Menos de 10.000','10.000 a <50.000','50.000 a <100.000','100.000 o más']
AGE_LABELS=['Menos de 20 %','20 a <30 %','30 % o más']
DENSITY_LABELS=['Menos de 10','10 a <100','100 a <1.000','1.000 o más']


def prepare_panel(panel,population):
    panel=panel.loc[panel.year.between(2008,2025)&panel.status.eq('available')&panel.density_per_km2.gt(0)].copy()
    if panel.duplicated(['code','year']).any():raise ValueError('Duplicate density municipality-year')
    population=population.copy()
    if population.duplicated(['codigo_municipio','ano_epidemiologico']).any():raise ValueError('Duplicate population municipality-year')
    population['code']=normalize_codes(population.codigo_municipio)
    columns=['poblacion_total','poblacion_menor_1','poblacion_1_4','poblacion_5_14']
    for column in columns:population[column]=pd.to_numeric(population[column],errors='coerce')
    population=population.groupby(['code','ano_epidemiologico'])[columns].agg(complete_sum).reset_index().rename(columns={'ano_epidemiologico':'year'})
    panel=panel.merge(population,on=['code','year'],how='left',validate='one_to_one')
    if not np.allclose(panel.population,panel.poblacion_total,rtol=0,atol=1e-6,equal_nan=False):raise ValueError('Density and age population totals do not match')
    young=panel[columns[1:]].sum(axis=1,min_count=3)
    panel['under_15_share']=young.div(panel.population).where(young.between(0,panel.population))
    panel['population_size']=pd.cut(panel.population,[0,10000,50000,100000,np.inf],right=False,labels=POPULATION_LABELS)
    panel['age_composition']=pd.cut(100*panel.under_15_share,[0,20,30,np.inf],right=False,labels=AGE_LABELS)
    panel['density_band']=pd.cut(panel.density_per_km2,[0,10,100,1000,np.inf],right=False,labels=DENSITY_LABELS)
    panel['department_code']=panel.code.str[:2]
    return panel


def correlation(group,field):
    if len(group)<MIN_ENTITIES:return np.nan,'fewer_than_5_entities'
    if group.density_per_km2.nunique()<2:return np.nan,'constant_density'
    if group[field].nunique()<2:return np.nan,'constant_outcome'
    return float(spearmanr(group.density_per_km2,group[field]).statistic),'available'


def summarize(group,year,dimension,key,label,order):
    rho_cases,status_cases=correlation(group,'cases')
    rho_rate,status_rate=correlation(group,'incidence_per_100k')
    return dict(year=int(year),dimension=dimension,group=str(key),group_label=label,group_order=order,
                municipalities=len(group),population=group.population.sum(),cases=group.cases.sum(),
                notification_records=int(group.notification_record_present.sum()),age_population_available=int(group.under_15_share.notna().sum()),
                incidence_median=group.incidence_per_100k.median(),incidence_q1=group.incidence_per_100k.quantile(.25),
                incidence_q3=group.incidence_per_100k.quantile(.75),incidence_pooled=100000*group.cases.sum()/group.population.sum(),
                rho_density_cases=rho_cases,rho_density_incidence=rho_rate,rho_cases_status=status_cases,rho_incidence_status=status_rate)


def build_summary(panel,population):
    panel=prepare_panel(panel,population)
    order={code:index for index,code in enumerate(DEPARTMENTS_NORTH_TO_SOUTH)}
    rows=[]
    for year,selected in panel.groupby('year',sort=True):
        rows.append(summarize(selected,year,'national','all','Todas las entidades válidas',0))
        for code,group in selected.groupby('department_code',sort=True):
            rows.append(summarize(group,year,'department',code,group.department.iloc[0],order[code]))
        for dimension,labels in [('population_size',POPULATION_LABELS),('age_composition',AGE_LABELS),('density_band',DENSITY_LABELS)]:
            for index,label in enumerate(labels):
                group=selected.loc[selected[dimension].eq(label)]
                if len(group):rows.append(summarize(group,year,dimension,str(index),label,index))
    result=pd.DataFrame(rows).sort_values(['year','dimension','group_order'])
    if result.duplicated(['year','dimension','group']).any():raise ValueError('Duplicate density summary key')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel',type=Path,default=ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv')
    parser.add_argument('--population',type=Path,default=ROOT/'data/population_municipal_2007_2025.csv')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/data_processed/varicela_totales_por_anio/population_density_summary_2008_2025.csv')
    args=parser.parse_args()
    panel=pd.read_csv(args.panel,dtype={'code':str})
    population=pd.read_csv(args.population,dtype={'codigo_municipio':str})
    summary=build_summary(panel,population)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    summary.to_csv(args.output,index=False,float_format='%.8f')
    metadata={'panel_source':str(args.panel.relative_to(ROOT)) if args.panel.is_relative_to(ROOT) else str(args.panel),
              'population_source':str(args.population.relative_to(ROOT)) if args.population.is_relative_to(ROOT) else str(args.population),
              'years':sorted(summary.year.unique().tolist()),'minimum_entities_for_rho':MIN_ENTITIES,
              'correlation':'Spearman ranks, unweighted entities, ties use average ranks; no p-values or independence assumption for inference',
              'rho_rule':'blank if fewer than five entities or no variation; five is a computational minimum, not a quality or precision guarantee',
              'incidence_median':'median of municipal rates; each entity counts once',
              'incidence_pooled':'100000 * sum(cases) / sum(population) of the same valid group',
              'age_composition':'share of total population under 15: (<1 + 1-4 + 5-14) / total; both sexes, same year, same code aliases',
              'population_size_labels':POPULATION_LABELS,'age_composition_labels':AGE_LABELS,'density_band_labels':DENSITY_LABELS,
              'department_order':'north to south, same order as Rt department filters','missing_age_rule':'excluded from age strata only; retained in other summaries',
              'scope':'same valid entities as scatter plots; includes zero notifications, non-municipalized areas and San Andres; fixed MGN 2025 area',
              'interpretation':'descriptive stratification, not age standardization, adjusted effects, or causal estimates'}
    args.output.with_suffix('.metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Generated {len(summary)} summary rows')
    print(summary[summary.dimension.eq('national')][['year','municipalities','rho_density_cases','rho_density_incidence','incidence_median','incidence_pooled']].round(3).to_string(index=False))


if __name__=='__main__':main()
