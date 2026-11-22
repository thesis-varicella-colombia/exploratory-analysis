# Municipios para revisión de incidencia y cobertura (2024–2025)

La tabla de la subsección «Municipios que requieren revisión de incidencia y
cobertura» usa los archivos generados por
[`scripts/analyze_municipal_priority_candidates.py`](../../../scripts/analyze_municipal_priority_candidates.py):
[`municipal_priority_union_2024_2025.csv`](municipal_priority_union_2024_2025.csv),
la lista mostrada;
[`municipal_priority_age_annual_2024_2025.csv`](municipal_priority_age_annual_2024_2025.csv),
el detalle por municipio y año; y
[`municipal_priority_age_2024_2025.metadata.json`](municipal_priority_age_2024_2025.metadata.json),
las reglas y los recuentos. Esta ficha describe las fuentes, los criterios, el
orden y las columnas.

## Fuentes

- **Incidencia municipal ajustada:**
  [`anomalias_cobertura/comparable_incidence_annual.csv`](../anomalias_cobertura/comparable_incidence_annual.csv),
  con pesos de edad fijos del panel nacional 2008–2014 en la tasa y su basal;
  excluye casos sin edad conocida.
- **Incidencia por grupo de edad:** notificaciones de Sivigila (INS) por grupo
  sobre población DANE del mismo grupo y año.
- **Cobertura:** [`vaccine_coverage_comparison.csv`](vaccine_coverage_comparison.csv)
  (ver [su ficha](README_coverage_comparison.md)).
- **Geografía:** `cartografia/municipal_boundaries_dane.geojson`.

## Criterios

Un municipio entra en la lista si cumple **cualquiera** de los dos criterios, con
cumplimiento completo en **2024 y en 2025**:

- **Municipal (>95 %):** incidencia total ajustada por edad estrictamente mayor
  que 0,95 × su basal 2008–2014, en los dos años.
- **Infantil (>80 %):** incidencia estrictamente mayor que 0,80 × su basal, en
  cada grupo de menores de 1 año, 1–4 y 5–14, en los dos años.

Además, debe existir **alguna cobertura administrativa o calculada < 80 % en cada
uno de los dos años**, de primera o segunda dosis. La basal de cada grupo reúne los
casos y las personas-año de 2008–2014. La cobertura calculada es
`100 × dosis / población de referencia` (edad 1 para primera dosis, edad 5 para
refuerzo), con el año de análisis desplazado conservado.

La lista es la **unión** de ambos criterios, sin duplicados: cumplir los dos no
añade una segunda fila. Con los datos actuales son **49 municipios** de 1.102
comparables (48 por el criterio municipal, 7 por el infantil, 6 por ambos).

## Orden de la tabla

Primero las filas del criterio infantil (incluidas las que cumplen ambos) y después
las que cumplen solo el municipal. Dentro de cada grupo, de menor a mayor por el
**mínimo porcentaje calculable** de `100 × incidencia / basal` entre 2024 y 2025 y
los grupos aplicables (seis comparaciones infantiles o dos municipales). Las basales
cero no producen porcentaje y se excluyen del mínimo; una fila sin ningún porcentaje
calculable va al final de su grupo. Los empates se resuelven por departamento y
nombre.

## Archivos y columnas

- `municipal_priority_union_2024_2025.csv`: una fila por municipio seleccionado.
  Incluye identificación (`code`, `name`, `department`), las basales por grupo y
  municipal, las incidencias y coberturas de 2024 y 2025, los indicadores de
  candidatura (`candidate_municipal`, `candidate_children`, `candidate_union`), el
  grupo y la clave de orden (`sort_group`, `sort_baseline_pct`, `sort_reference`).
  Trae además dos variantes suavizadas por Empirical Bayes, cada una con sus
  basales, incidencias y clave de orden: la nacional (`baseline_eb_<grupo>`,
  `incidence_eb_<grupo>_<año>`, `sort_group_eb`, `sort_baseline_pct_eb`,
  `sort_reference_eb`) y la de vecinos (las mismas con el sufijo `_eb_local`). La
  nacional encoge hacia la media del país; la de vecinos, hacia la media del
  municipio y sus 8 vecinos más cercanos (la misma vecindad de la sección 8). La
  fila municipal suavizada usa la tasa de «todas las edades» (`all`) en vez de la
  ajustada por edad. Estas columnas no cambian qué municipios se seleccionan, solo
  sus valores y su orden; el archivo se publica ordenado por la tasa cruda y la
  página reordena a cualquiera de las dos variantes a pedido. El suavizado se
  documenta en la [ficha de metodología de Empirical Bayes](empirical_bayes/README.md).
- `municipal_priority_age_annual_2024_2025.csv`: una fila por municipio y año
  (2024, 2025) con población y casos por grupo, incidencias, basales, coberturas,
  las razones de selección y si el municipio cumple cada criterio ese año.
- `municipal_priority_age_2024_2025.metadata.json`: años, años de basal, etiquetas
  de edad, reglas de tasa y cobertura, definición de cada criterio con sus
  recuentos (totales y por año), orden y límites.

El generador también escribe `municipal_priority_children_2024_2025.csv`,
`municipal_priority_municipal_2024_2025.csv` (cada criterio por separado) y
`municipal_priority_age_all_2024_2025.csv` (los 1.102 municipios comparables).

## Límites

Es una lista para revisión exploratoria, sin incertidumbre ni inferencia causal, no
un orden concluyente de riesgo. Una población de edad ausente o no positiva no puede
cumplir un criterio; una basal cero exige incidencia anual positiva. Los casos sin
edad conocida no se asignan a grupos. Pocos casos y cambios de notificación pueden
afectar las comparaciones. Los valores se redondean para mostrar; la selección usa
ocho decimales.

## Regeneración

Desde la raíz del repositorio, después de generar
`vaccine_coverage_comparison.csv` y `comparable_incidence_annual.csv`:

```bash
.venv/bin/python scripts/analyze_municipal_priority_candidates.py
```

## Descargas

- [`municipal_priority_union_2024_2025.csv`](municipal_priority_union_2024_2025.csv): municipios para revisión.
- [`municipal_priority_age_annual_2024_2025.csv`](municipal_priority_age_annual_2024_2025.csv): detalle anual y criterios.
- [`municipal_priority_age_2024_2025.metadata.json`](municipal_priority_age_2024_2025.metadata.json): reglas y recuentos.
