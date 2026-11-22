"""Municipal and age-specific exploratory candidates, requiring BOTH 2024 AND 2025.

A: total municipal age-adjusted incidence strictly above 95% of its own baseline.
B: each of the three child age groups strictly above 80% of its own baseline.
Both require some usable annual vaccination measure <80% in each year.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from generate_age_standardized_sir import read_panel, AGE_GROUPS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data_processed'
YEARS = (2024, 2025)
CHILD_GROUPS = ('under_1', '1_4', '5_14')
LABELS = {'under_1':'Menores de 1 año', '1_4':'1–4 años', '5_14':'5–14 años', '15_49':'15–49 años', '50_plus':'50 años o más'}
CRITERIA = {
    'municipal': {'label':'Municipal: incidencia total ajustada >95 % de la basal', 'groups':['municipal'], 'baseline_fraction':.95},
    'children': {'label':'Grupos infantiles: incidencia >80 % de la basal', 'groups':list(CHILD_GROUPS), 'baseline_fraction':.8},
}
COVERAGE_FIELDS = ('first_dose_valid_admin', 'first_dose_calculated', 'booster_valid_admin', 'booster_calculated')
EB_SOURCE = DATA / 'cobertura_vacunacion/empirical_bayes/municipal_incidence_eb.csv'
# EB equivalents of the rates used by the list. The municipal comparison, which
# normally uses the age-adjusted total rate, uses the EB of "all" (total cases
# over total population, smoothed) when the smoothed view is selected.
EB_LIST_GROUPS = {'municipal': 'all', 'under_1': 'under_1', '1_4': '1_4', '5_14': '5_14'}


def load_eb_rates():
    """Return nested dicts for both EB variants: (code, eb_group[, year]) -> rate."""
    eb = pd.read_csv(EB_SOURCE, dtype={'code': str})
    ann = eb[eb.scope.eq('annual')]
    base = eb[eb.scope.eq('baseline')]
    annual = {'eb': {(r.code, r.age_group, int(r.year)): r.rate_eb for r in ann.itertuples()},
              'eb_local': {(r.code, r.age_group, int(r.year)): r.rate_eb_local for r in ann.itertuples()}}
    baseline = {'eb': {(r.code, r.age_group): r.rate_eb for r in base.itertuples()},
                'eb_local': {(r.code, r.age_group): r.rate_eb_local for r in base.itertuples()}}
    return annual, baseline


def add_eb_columns(summary):
    """Add smoothed columns and ordering keys for both EB variants.

    For each variant (suffix '_eb' national, '_eb_local' neighbours) and each list
    group, adds baseline_<suffix>_<group> and incidence_<suffix>_<group>_<year>.
    The municipal line uses the EB of 'all' (total cases over total population).
    Does not change which municipalities are selected; only values and ordering.
    """
    annual_eb, baseline_eb = load_eb_rates()
    result = summary.copy()
    for suffix in ('eb', 'eb_local'):
        for list_group, eb_group in EB_LIST_GROUPS.items():
            result[f'baseline_{suffix}_{list_group}'] = [
                round(baseline_eb[suffix].get((code, eb_group), np.nan), 8) for code in result.code]
            for year in YEARS:
                result[f'incidence_{suffix}_{list_group}_{year}'] = [
                    round(annual_eb[suffix].get((code, eb_group, year), np.nan), 8) for code in result.code]
        result = order_candidates(result, baseline_field=f'baseline_{suffix}_{{age}}',
                                  incidence_field=f'incidence_{suffix}_{{age}}_{{year}}', suffix=f'_{suffix}')
    # Restore the crude order so the published CSV defaults to the crude view;
    # the page re-sorts to either EB variant on demand.
    return result.sort_values(['sort_group','sort_baseline_pct','department','name'],
                              na_position='last', kind='stable').reset_index(drop=True)


def candidate_frame(panel, coverage, geography, municipal_incidence):
    keys = ['codigo_municipio','ano_epidemiologico']
    if panel.duplicated(keys).any():
        raise ValueError('Duplicate annual panel')
    pre = panel[panel.ano_epidemiologico.between(2008,2014)]
    recent = panel[panel.ano_epidemiologico.isin(YEARS)].copy().rename(columns={'codigo_municipio':'code','ano_epidemiologico':'year'})
    recent['name'] = recent.code.map(lambda code: geography[code]['name'])
    recent['department'] = recent.code.map(lambda code: geography[code]['department'])
    for age in AGE_GROUPS:
        baseline = pre.groupby('codigo_municipio')[[f'observed_{age}',f'population_{age}']].sum(min_count=1)
        complete = pre.groupby('codigo_municipio').ano_epidemiologico.nunique().eq(7)
        baseline_rate = (100000*baseline[f'observed_{age}']/baseline[f'population_{age}'].where(baseline[f'population_{age}'].gt(0))).where(complete)
        recent[f'baseline_{age}'] = recent.code.map(baseline_rate).round(8)
        recent[f'baseline_cases_{age}'] = recent.code.map(baseline[f'observed_{age}'])
        recent[f'baseline_population_years_{age}'] = recent.code.map(baseline[f'population_{age}'])
        pop = recent[f'population_{age}']
        recent[f'incidence_{age}'] = (100000*recent[f'observed_{age}']/pop.where(pop.gt(0))).round(8)
    municipal = municipal_incidence[municipal_incidence.horizon.isin(YEARS) & municipal_incidence.code.ne('all')].copy()
    municipal = municipal.rename(columns={'horizon':'year','baseline_adjusted':'baseline_municipal','adjusted_pre_weights':'incidence_municipal'})
    if municipal.duplicated(['code','year']).any():
        raise ValueError('Duplicate total municipal incidence')
    recent = recent.merge(municipal[['code','year','baseline_municipal','incidence_municipal']],on=['code','year'],how='left',validate='one_to_one')
    for dose in ['first_dose','booster']:
        selected = coverage[coverage.dose.eq(dose)&coverage.year.isin(YEARS)].copy()
        if selected.duplicated(['code','year']).any():
            raise ValueError('Duplicate annual coverage')
        admin = selected.administrative_coverage_pct
        selected[dose+'_admin_recorded'] = admin
        selected[dose+'_valid_admin'] = admin.round(8).where(np.isfinite(admin)&admin.between(0,100))
        selected[dose+'_calculated'] = selected.reference_coverage_pct.where(np.isfinite(selected.reference_coverage_pct)&selected.reference_coverage_pct.ge(0))
        fields = ['code','year',dose+'_admin_recorded',dose+'_valid_admin',dose+'_calculated']
        recent = recent.merge(selected[fields],on=['code','year'],how='left',validate='one_to_one')
    return recent


def flags(frame):
    result = frame.copy()
    result['low_any_coverage'] = result[list(COVERAGE_FIELDS)].lt(80).any(axis=1)
    result['selection_reasons'] = result.apply(lambda row: '; '.join(field for field in COVERAGE_FIELDS if pd.notna(row[field]) and row[field]<80),axis=1)
    for key, criterion in CRITERIA.items():
        comparisons = []
        for age in criterion['groups']:
            current = result[f'incidence_{age}']
            baseline = result[f'baseline_{age}']
            comparison = np.isfinite(current)&np.isfinite(baseline)&current.round(8).gt((criterion['baseline_fraction']*baseline).round(8))
            result[f'{key}_passes_{age}'] = comparison
            comparisons.append(comparison)
        result[f'{key}_incidence'] = np.logical_and.reduce(comparisons)
        result[f'candidate_{key}'] = result[f'{key}_incidence']&result.low_any_coverage
    return result


def order_candidates(summary, baseline_field='baseline_{age}', incidence_field='incidence_{age}_{year}', suffix=''):
    """Children first; within each group, lowest calculable baseline percentage.

    Child rows use the minimum of their six age/year comparisons; municipal-only
    rows use their two total-rate comparisons. Zero baselines have no percentage.
    With suffix='_eb', writes the ordering keys as sort_*_eb using the smoothed
    rate fields, and sorts the rows by the EB percentage.
    """
    result=summary.copy()
    details=[]
    for row in result.to_dict('records'):
        children=bool(row['candidate_children'])
        rank=0 if children else 1 if row['candidate_municipal'] else 2
        comparisons=[]
        undefined=0
        for age in CHILD_GROUPS if children else ['municipal']:
            baseline=row[baseline_field.format(age=age)]
            for year in YEARS:
                current=row.get(incidence_field.format(age=age,year=year),np.nan)
                if pd.notna(baseline) and np.isfinite(baseline) and baseline>0 and pd.notna(current) and np.isfinite(current):
                    comparisons.append((round(100*current/baseline,8),age,year))
                else:
                    undefined+=1
        best=min(comparisons,key=lambda value:value[0]) if comparisons else (np.nan,'',None)
        label='Municipal ajustada' if best[1]=='municipal' else LABELS.get(best[1],'Sin porcentaje calculable')
        details.append({f'sort_group{suffix}':rank,
            f'selection_group{suffix}':'Infantil' if rank==0 else 'Municipal' if rank==1 else 'Sin selección',
            f'sort_baseline_pct{suffix}':best[0],
            f'sort_reference{suffix}':f'{label} · {best[2]}' if best[2] else label,
            f'sort_undefined_comparisons{suffix}':undefined})
    for field in [f'sort_group{suffix}',f'selection_group{suffix}',f'sort_baseline_pct{suffix}',f'sort_reference{suffix}',f'sort_undefined_comparisons{suffix}']:
        result[field]=[record[field] for record in details]
    return result.sort_values([f'sort_group{suffix}',f'sort_baseline_pct{suffix}','department','name'],na_position='last',kind='stable').reset_index(drop=True)


def municipality_summary(annual):
    rows = []
    for code, group in annual.groupby('code'):
        group = group.sort_values('year')
        first = group.iloc[0]
        row = dict(code=code,name=first['name'],department=first.department,cases_2024_2025=group.casos_total.sum())
        row['baseline_municipal'] = first.baseline_municipal
        for age in AGE_GROUPS:
            for field in [f'baseline_{age}',f'baseline_cases_{age}',f'baseline_population_years_{age}']:
                row[field] = first[field]
        for record in group.itertuples():
            for field in [*COVERAGE_FIELDS, 'casos_total', 'incidence_municipal',*[f'incidence_{age}' for age in AGE_GROUPS]]:
                row[field+'_'+str(record.year)] = getattr(record,field)
        for key in CRITERIA:
            qualifying = group[group[f'candidate_{key}']]
            row[f'candidate_{key}'] = set(qualifying.year)==set(YEARS)
            row[f'qualifying_years_{key}'] = ';'.join(qualifying.year.astype(str))
        row['candidate_union'] = row['candidate_municipal'] or row['candidate_children']
        rows.append(row)
    return order_candidates(pd.DataFrame(rows))


def write_report(annual,summary,metadata):
    selected=summary[summary.candidate_union]
    f=lambda value:f'{value:.2f}'.replace('.',',') if pd.notna(value) else 'Sin dato'
    lines=['# Municipios para revisión: incidencia municipal o infantil y cobertura baja','',
        'Actualización: 3 de noviembre de 2026.','',
        'La lista incluye a todos los municipios que cumplen cualquiera de los dos criterios completos en 2024 y 2025, sin duplicados. El primer criterio evalúa la tasa municipal total ajustada; ya no exige superar límites en los cinco grupos por separado.','',
        '## Criterios','',
        '1. **Municipal:** incidencia total ajustada por edad >0,95 × su propia basal de 2008–2014, tanto en 2024 como en 2025. Se usan los mismos pesos nacionales del panel de 2008–2014 en las tasas anuales y basales, publicados en comparable_incidence_annual.csv.','2. **Infantil:** incidencia específica >0,8 × su propia basal en cada uno de los grupos <1, 1–4 y 5–14 años, tanto en 2024 como en 2025. La basal por municipio y edad es 100.000 × suma de casos / suma de poblaciones anuales de ese grupo durante 2008–2014.','3. **Cobertura común:** debe existir alguna medida administrativa o calculada <80 % en cada año. Puede ser una medida o dosis distinta entre 2024 y 2025. La calculada usa población de 1 año para primera dosis y de 5 años para segunda, conservando el desplazamiento de año de la fuente.','',
        'Los límites son estrictos. Se aplica AND entre 2024 y 2025 dentro de cada criterio, y luego OR entre criterios completos. No basta cumplir solo el municipal en 2024 y solo el infantil en 2025. El conjunto municipal ya no es necesariamente subconjunto del infantil.','',
        '## Resultado','',
        f"De {len(summary)} municipios comparables, {metadata['criteria']['municipal']['candidates']} cumplen el criterio municipal y {metadata['criteria']['children']['candidates']} el infantil. Hay {metadata['intersection_candidates']} en ambos y **{len(selected)} municipios únicos** en la unión.",'',
        'Orden: primero quienes cumplen el criterio infantil (incluidos los que cumplen ambos), después quienes cumplen solo el municipal. Dentro de cada grupo se ordena por el menor porcentaje calculable respecto a la basal: mínimo de las seis comparaciones infantiles o de las dos municipales, respectivamente. Basales cero no generan porcentajes; se omiten del mínimo y, si ninguno es calculable, la fila va al final de su grupo. Este orden descriptivo no es una clasificación inferencial de riesgo.','',
        '| Municipio | Departamento | Grupo de orden | Menor % de basal | Referencia del porcentaje | Casos 2024–2025 | Municipal >95 % | Infantil >80 % |','|---|---|---|---:|---|---:|---|---|']
    for r in selected.itertuples():
        lines.append(f'| {r.name} ({r.code}) | {r.department} | {r.selection_group} | {f(r.sort_baseline_pct)} | {r.sort_reference} | {int(r.cases_2024_2025)} | {"Sí" if r.candidate_municipal else "No"} | {"Sí" if r.candidate_children else "No"} |')
    lines+=['','## Tasas usadas en la selección','',
        '| Municipio | Medida | Basal 2008–2014 | 2024 | 2025 |','|---|---|---:|---:|---:|']
    for r in selected.to_dict('records'):
        for age,label in [('municipal','Municipal total ajustada'),*[(a,LABELS[a]) for a in CHILD_GROUPS]]:
            lines.append(f"| {r['name']} | {label} | {f(r[f'baseline_{age}'])} | {f(r[f'incidence_{age}_2024'])} | {f(r[f'incidence_{age}_2025'])} |")
    lines+=['','## Alcance','',
        '- Preselección exploratoria sin intervalos municipales; no es una clasificación concluyente de riesgo ni demuestra efecto de la vacuna. No restringe automáticamente el universo del modelo.','- La tasa municipal ajustada excluye notificaciones sin edad conocida. Los grupos infantiles usan sus propios casos y poblaciones; no se reparte artificialmente la edad desconocida.','- Basal cero exige incidencia positiva mediante comparación directa. Población ausente o no positiva deja la tasa sin dato y no cumple ese criterio; otro criterio completo puede permitir entrar.','- Cobertura administrativa fuera de 0–100 % y faltantes no se consideran bajos ni se convierten en cero. Las otras medidas y los desenlaces se conservan.','- Pocos casos basales pueden producir aumentos grandes. Se conservan conteos y poblaciones por edad para revisar precisión y cambios de notificación.','',
        '## Archivos','',
        '- [Lista completa y criterios que cumple cada municipio](docs/data_processed/cobertura_vacunacion/municipal_priority_union_2024_2025.csv).','- [Criterio municipal](docs/data_processed/cobertura_vacunacion/municipal_priority_municipal_2024_2025.csv).','- [Criterio infantil](docs/data_processed/cobertura_vacunacion/municipal_priority_children_2024_2025.csv).','- [Todos los municipios](docs/data_processed/cobertura_vacunacion/municipal_priority_age_all_2024_2025.csv).','- [Detalle anual](docs/data_processed/cobertura_vacunacion/municipal_priority_age_annual_2024_2025.csv).','- [Metadatos](docs/data_processed/cobertura_vacunacion/municipal_priority_age_2024_2025.metadata.json).','',
        '```bash','.venv/bin/python scripts/analyze_municipal_priority_candidates.py','```','']
    (ROOT/'REVISION_MUNICIPIOS_PRIORITARIOS_2026_11_02.md').write_text('\n'.join(lines))


def main():
    (DATA/'cobertura_vacunacion').mkdir(parents=True,exist_ok=True)
    geography = {f['properties']['code']:f['properties'] for f in json.loads((DATA/'cartografia/municipal_boundaries_dane.geojson').read_text())['features']}
    coverage = pd.read_csv(DATA/'cobertura_vacunacion/vaccine_coverage_comparison.csv',dtype={'code':str})
    municipal_incidence = pd.read_csv(DATA/'anomalias_cobertura/comparable_incidence_annual.csv',dtype={'code':str})
    annual = flags(candidate_frame(read_panel(),coverage,geography,municipal_incidence))
    summary = add_eb_columns(municipality_summary(annual))
    annual.to_csv(DATA/'cobertura_vacunacion/municipal_priority_age_annual_2024_2025.csv',index=False,float_format='%.8f')
    summary.to_csv(DATA/'cobertura_vacunacion/municipal_priority_age_all_2024_2025.csv',index=False,float_format='%.8f')
    summary[summary.candidate_union].to_csv(DATA/'cobertura_vacunacion/municipal_priority_union_2024_2025.csv',index=False,float_format='%.8f')
    metadata = dict(presentation="union_of_age_criteria_without_duplicates",years=list(YEARS),baseline_years=list(range(2008,2015)),age_labels=LABELS,
        rate_rule='children: 100000 * age-group cases / same-age population; baseline pools 2008-2014 cases and population-years',
        municipal_rate_rule='comparable_incidence_annual.csv adjusted_pre_weights and baseline_adjusted, fixed national-panel 2008-2014 age weights in both rates; excludes unknown-age cases',
        coverage_strict_upper_bound=80,coverage_rule='some usable annual administrative or calculated measure <80 in BOTH years; first dose population exactly age 1, booster exactly age 5; preserve shifted analysis year',
        municipalities=len(summary),annual_rows=len(annual),union_candidates=int(summary.candidate_union.sum()),intersection_candidates=int((summary.candidate_municipal&summary.candidate_children).sum()),criteria={},
        ordering='children first, including both-criterion rows; municipal-only second; ascending minimum calculable 100*incidence/baseline across 2024 and 2025 and the applicable groups; exclude zero baselines from percentages, never impute infinity or zero; no calculable percentage sorts last within its group; ties by department/name',
        empirical_bayes='two smoothed variants: national (_eb) and neighbours (_eb_local). Columns baseline_<suffix>_<group>, incidence_<suffix>_<group>_<year> and sort_*_<suffix> use the per-age-group EB rate; the municipal line uses the EB of "all" (total cases over total population) instead of the age-adjusted rate; selection of municipalities is unchanged, only values and ordering; see empirical_bayes/README.md',
        limitations='descriptive screening without uncertainty or causal inference; missing/nonpositive age population cannot meet a criterion; baseline zero requires positive annual incidence; unknown-age cases not assigned to groups; municipal and child criteria are independent and combined by union')
    for key,criterion in CRITERIA.items():
        selected = summary[summary[f'candidate_{key}']]
        selected.to_csv(DATA/f'cobertura_vacunacion/municipal_priority_{key}_2024_2025.csv',index=False,float_format='%.8f')
        metadata['criteria'][key] = {**criterion,'strict':True,'candidates':len(selected),
            'candidates_by_year':{str(y):int(annual.loc[annual.year.eq(y),f'candidate_{key}'].sum()) for y in YEARS}}
    (DATA/'cobertura_vacunacion/municipal_priority_age_2024_2025.metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    write_report(annual,summary,metadata)
    print(json.dumps(metadata['criteria'],ensure_ascii=False))


if __name__=='__main__':
    main()
