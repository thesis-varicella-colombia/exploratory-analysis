"""Compact annual series for national, department and municipality selectors.

Reuse the harmonized density panel's notifications/populations, without using
area or density. Preserve the national CSV exactly, the diagnostic 2007 point,
missing denominators and the panel's explicit assigned-zero convention.
"""
import json
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/data_processed'
OUTPUT=DATA/'varicela_totales_por_anio'
YEARS=list(range(2007,2026))
DEPARTMENTS_NORTH_TO_SOUTH=['88','44','08','47','20','70','13','23','54','05','68','81','27','15','85','17','66','25','99','63','11','73','76','50','94','41','19','95','52','18','97','86','91']


def series_rows(panel):
    rows=[]
    for year in YEARS:
        group=panel[panel.year.eq(year)]
        if group.empty: raise ValueError('Missing territorial year')
        population=group.population.sum(min_count=1)
        cases=group.cases.sum(min_count=1)
        rate=100000*cases/population if pd.notna(population) and population>0 else None
        rows.append(dict(year=year,notifications=int(cases),population=float(population) if pd.notna(population) else None,
            notification_rate_per_100k=round(rate,8) if rate is not None else None,
            reporting_entities=int(group.notification_record_present.sum()),population_entities=int(group.population.notna().sum()),
            zero_population_entities=int(group.population.eq(0).sum()),missing_population_entities=int(group.population.isna().sum()),
            selected_entities=len(group),official_2007_cases=None))
    return rows


def main():
    panel=pd.read_csv(DATA/'varicela_totales_por_anio/population_density_2007_2025.csv',dtype={'code':str})
    national=pd.read_csv(DATA/'varicela_totales_por_anio/annual_series_2007_2025.csv')
    if panel.duplicated(['code','year']).any() or len(panel)!=1122*19: raise ValueError('Incomplete geographic panel')
    if set(panel.year)!=set(YEARS) or set(national.year)!=set(YEARS): raise ValueError('Unexpected years')
    if panel.notification_record_present.isna().any(): raise ValueError('Missing record flags')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    aggregate=series_rows(panel)
    for row in aggregate:
        original=national[national.year.eq(row['year'])].iloc[0]
        if row['notifications']!=original.notifications or row['population']!=original.population or row['reporting_entities']!=original.reporting_entities:
            raise ValueError('Mapped totals differ from published national totals')
        for field in national.columns:
            value=original[field]
            row[field]=None if pd.isna(value) else float(value) if field=='notification_rate_per_100k' else int(value)
    (OUTPUT/'all.json').write_text(json.dumps(dict(id='all',rows=aggregate),ensure_ascii=False,separators=(',',':'),allow_nan=False))
    entities=[]
    for code,group in panel.groupby('code',sort=False):
        place=group.iloc[0]
        entities.append(dict(id=code,code=code,dimension='municipality',name=place['name'],department=place.department))
        (OUTPUT/f'{code}.json').write_text(json.dumps(dict(id=code,rows=series_rows(group)),ensure_ascii=False,separators=(',',':'),allow_nan=False))
    departments=[]
    panel['department_code']=panel.code.str[:2]
    for code in DEPARTMENTS_NORTH_TO_SOUTH:
        group=panel[panel.department_code.eq(code)]
        if group.empty: raise ValueError('Missing department')
        name=group.department.iloc[0]
        departments.append(dict(id='dep_'+code,code=code,name=name,dimension='department'))
        (OUTPUT/f'dep_{code}.json').write_text(json.dumps(dict(id='dep_'+code,rows=series_rows(group)),ensure_ascii=False,separators=(',',':'),allow_nan=False))
    order={code:i for i,code in enumerate(DEPARTMENTS_NORTH_TO_SOUTH)}
    entities.sort(key=lambda row:(order[row['code'][:2]],row['name']))
    manifest=dict(years=YEARS,all_label='Todos los municipios y departamentos',departments=departments,municipalities=entities,
        national_source='annual_series_2007_2025.csv retained exactly',territorial_source='population_density_2007_2025.csv: cases, population and record presence only; no area/density computation',
        geography='fixed mapped MGN2025 entities; historical aliases already harmonized including Mapiripana in Barrancominas',
        aggregation='sum notifications / sum available annual population *100000; never average municipal rates; missing or nonpositive total population yields null rate; count missing and zero-population entities explicitly',
        zero_rule='municipal absence of notification row retains the panel assigned zero convention; does not establish absence of disease or complete reporting',
        official_2007='69695 is a national reference and appears only in the all selection',
        department_order='north to south, same published centroid-latitude order as other department filters')
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(f'Generated national, {len(departments)} department and {len(entities)} municipal series for 2007–2025')


if __name__=='__main__':main()
