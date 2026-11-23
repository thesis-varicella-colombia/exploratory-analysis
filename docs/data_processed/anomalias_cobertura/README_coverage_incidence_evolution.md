# Evolución de la incidencia ajustada según cobertura municipal

## Descripción y archivos

Este conjunto respalda las conclusiones de la sección «Anomalías (O/E) y cobertura»
sobre si los municipios con menor cobertura presentan una evolución distinta de
la incidencia ajustada. Se comparan tasas del mismo municipio entre períodos y
se resumen sus cambios por grupos fijos de cobertura reciente.

- [`coverage_incidence_evolution_municipal_changes.csv`](coverage_incidence_evolution_municipal_changes.csv):
  6.612 filas, una por municipio, dosis y período inicial.
- [`coverage_incidence_evolution_summary.csv`](coverage_incidence_evolution_summary.csv):
  96 filas, una por dosis, período inicial, referencia de edad, corte y grupo.
- [`coverage_incidence_evolution_correlations.csv`](coverage_incidence_evolution_correlations.csv):
  12 filas, una por dosis, período inicial y referencia de edad.
- [`coverage_incidence_evolution.metadata.json`](coverage_incidence_evolution.metadata.json):
  reglas, fuentes, referencias y límites.

Los CSV usan UTF-8, coma como separador, punto decimal y campos vacíos para
ausencias. Los números de punto flotante se exportan con ocho decimales.
`code` se lee como texto para conservar los ceros iniciales.

## Origen de los datos

| Dataset utilizado | Información incorporada |
| --- | --- |
| [`comparable_incidence_periods.csv`](comparable_incidence_periods.csv) | Tasas municipales directamente ajustadas por edad, con proporciones de referencia de 2008–2014 y, como sensibilidad, de 2025. Las calcula `analyze_comparable_incidence.py` desde las notificaciones de Sivigila y la población DANE. |
| [Cruce municipal de SIR y cobertura](README_sir_coverage.md) | `age_standardized_sir_coverage_periods.csv`: cobertura media de 2022–2025 por dosis, con tope anual de 100 % y número de años utilizables. |
| [Notificaciones integradas de Sivigila](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | Registros por municipio de residencia, año epidemiológico de la fecha de notificación y edad; fuente de las tasas ajustadas. |
| [Población municipal](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | Población anual por grupo de edad del DANE, con la homologación territorial del panel de SIR. |

Se conservan los mismos 1.102 municipios. No se usa la fila agregada `all` de
las tasas ni se promedian SIR para medir evolución. Las tasas ajustadas combinan
las tasas de cinco edades con las mismas proporciones de población en todos los
períodos; excluyen notificaciones sin edad conocida.

## Diccionario de datos

### Cambios municipales

Clave única: `code` + `dose` + `baseline`.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `code` | Texto | DIVIPOLA homologado de cinco caracteres. |
| `dose` | Categoría | `first_dose` o `booster`. |
| `baseline` | Categoría | Período inicial: `2008-2014`, `2015-2019` o `2020-2021`. |
| `coverage_pct` | Número | Media de cobertura 2022–2025 tras aplicar el tope anual, en puntos porcentuales. |
| `baseline_rate_pre` | Número o ausente | Tasa inicial ajustada con proporciones por edad de 2008–2014, por 100.000 personas-año. |
| `recent_rate_pre` | Número o ausente | Tasa de 2022–2025 con esa misma referencia de edad. |
| `difference_pre` | Número o ausente | Tasa reciente menos inicial, con referencia de edad 2008–2014. |
| `ratio_pre` | Número o ausente | Tasa reciente dividida por la inicial; ausente si la inicial es cero. |
| `baseline_rate_2025` | Número o ausente | Tasa inicial ajustada con proporciones por edad de 2025. |
| `recent_rate_2025` | Número o ausente | Tasa de 2022–2025 con referencia de edad de 2025. |
| `difference_2025` | Número o ausente | Diferencia con referencia de edad de 2025. |
| `ratio_2025` | Número o ausente | Razón con referencia de edad de 2025; ausente si la tasa inicial es cero. |

El sufijo `pre` identifica la composición por edad de referencia, no el período
inicial del contraste; este último se especifica en `baseline`.

### Resúmenes por grupo

Clave única: `dose` + `baseline` + `age_standard` + `cutoff` + `group`.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `dose` | Categoría | Primera dosis o refuerzo, con los códigos anteriores. |
| `baseline` | Categoría | Período inicial de la comparación. |
| `recent` | Categoría | Período final, siempre `2022-2025`. |
| `age_standard` | Categoría | Referencia de edad: `2008-2014` o `2025`. |
| `cutoff` | Número | Corte de cobertura: 80, 90, 92,9 o 95 %. |
| `group` | Categoría | `below`, inferior al corte; `at_or_above`, igual o superior. |
| `municipalities` | Entero | Municipios con cobertura completa y ambas tasas finitas. |
| `ratio_municipalities` | Entero | Municipios con razón calculable. |
| `zero_baseline` | Entero | Municipios con tasa inicial cero, excluidos de las razones. |
| `median_baseline_rate` | Número o ausente | Mediana de las tasas municipales iniciales. |
| `median_recent_rate` | Número o ausente | Mediana de las tasas municipales recientes. |
| `median_difference` | Número o ausente | Mediana de las diferencias calculadas dentro de cada municipio. |
| `median_ratio` | Número o ausente | Mediana de las razones calculadas dentro de cada municipio. |
| `ratio_q1` | Número o ausente | Percentil 25 de las razones municipales. |
| `ratio_q3` | Número o ausente | Percentil 75 de las razones municipales. |

Cada municipio tiene el mismo peso en estas medianas; no son tasas agregadas del
grupo. La mediana de razones no equivale al cociente de las medianas de tasas.
`100 × (1 − median_ratio)` expresa la reducción relativa mediana cuando las
razones son calculables. Q1–Q3 describe dispersión entre municipios, no un
intervalo de confianza.

### Correlaciones

Clave única: `dose` + `baseline` + `age_standard`.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `dose`, `baseline`, `recent`, `age_standard` | Categoría | Mismo significado que en los resúmenes. |
| `municipalities` | Entero | Municipios con cobertura y tasas utilizables. |
| `ratio_municipalities` | Entero | Municipios con razón calculable. |
| `spearman_ratio` | Número o ausente | Correlación de rangos entre cobertura reciente y razón municipal de cambio. |
| `spearman_difference` | Número o ausente | Correlación de rangos entre cobertura reciente y diferencia absoluta municipal. |

Las correlaciones utilizan la cobertura continua; no dependen del corte. Se
dejan ausentes si no hay suficiente variación o hay menos de tres pares válidos.

## Generación y relación con las conclusiones

[`scripts/analyze_coverage_incidence_evolution.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/analyze_coverage_incidence_evolution.py)
genera los tres CSV y los metadatos desde los dos archivos de entrada. La
cobertura debe ser completa en los cuatro años recientes, finita y no negativa
antes del tope anual. Se conserva el desplazamiento de año de la fuente PAI.

Se forman grupos **retrospectivos y fijos** según cobertura de 2022–2025. Para
cada dosis y corte, los mismos municipios se comparan antes y después; no se
cambia su grupo con la cobertura de otros períodos. El contraste principal usa
refuerzo, corte 92,9 %, período inicial 2015–2019 (etapa anterior a la pandemia)
y composición por edad de 2008–2014. Se revisan también primera dosis, los otros
cortes, las proporciones por edad de 2025 y las referencias iniciales de
2008–2014 y 2020–2021. Estas últimas no responden exactamente a la misma pregunta:
una compara con la era prevacunal y otra con la etapa pandémica.

La página resume los resultados en las conclusiones de anomalías y cobertura;
no conserva la antigua tabla independiente de comparación temporal. Las cifras
son fijas y no cambian al mover los controles de la matriz.

Desde la raíz del repositorio, con las tasas y el cruce de cobertura generados:

```bash
.venv/bin/python scripts/analyze_coverage_incidence_evolution.py
```

## Valores ausentes y alcance

Una tasa inicial cero impide calcular la razón, pero se conserva la diferencia
absoluta. Se publican los denominadores efectivos: para refuerzo con corte 92,9 %
los grupos contienen 854 y 248 municipios; en la comparación con 2015–2019,
las razones utilizan 851 y 248. Para primera dosis, los grupos contienen 785 y
317 municipios, con 784 y 315 razones calculables.

La clasificación usa cobertura del mismo período final que el desenlace y no
reconstruye una exposición previa, esquemas individuales ni cohortes vacunadas.
Una correlación cercana a cero no demuestra equivalencia entre grupos ni ausencia
de efecto de la vacunación. Las diferencias absolutas, las razones y las
comparaciones con otras etapas pueden ofrecer lecturas distintas.

No se calculan intervalos de incertidumbre, pruebas de hipótesis ni efectos
causales. Los grupos de dosis y cortes se solapan. Pocos casos, cambios de
vigilancia, denominadores y diferencias territoriales pueden influir. Las
conclusiones describen notificaciones, no todas las infecciones.
