# Cruce municipal de SIR y cobertura de vacunación

## Descripción y archivo

[`age_standardized_sir_coverage_periods.csv`](age_standardized_sir_coverage_periods.csv)
reúne las notificaciones observadas, las esperadas según la estructura por edad,
el SIR y la cobertura administrativa de vacunación de cada municipio. Alimenta
la matriz, el diagrama «Asociación entre cobertura y SIR» y el «Mapa de los cuatro
cuadrantes», que comparten los mismos datos y controles.

Contiene **3.306 filas: 1.102 municipios × tres períodos** (2015–2019, 2020–2021
y 2022–2025). Cada fila representa un municipio y un período; la combinación
`period` + `code` es única. Primera dosis y refuerzo tienen columnas separadas.

El CSV usa UTF-8, coma como separador, punto decimal y campos vacíos para valores
ausentes. Los campos numéricos de punto flotante se exportan con ocho decimales;
los conteos siguen representando cantidades enteras. Los códigos territoriales
se leen como texto para conservar sus ceros iniciales.

## Origen de los datos

Los enlaces siguientes llevan a las especificaciones de los insumos y a los
README específicos de data-processing. Los archivos originales de gran tamaño
no se publican en ese repositorio.

| Dataset utilizado | Información incorporada |
| --- | --- |
| [Casos observados, esperados y SIR municipal](README_sir.md) | `age_standardized_sir_municipal_periods.csv`: notificaciones, poblaciones acumuladas, casos esperados y cocientes SIR para los mismos 1.102 municipios. |
| [Sivigila integrado por fecha de notificación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | `sivigila_integrado_notification_semanal_municipal.parquet`: notificaciones de varicela (evento 831) por municipio de residencia, año epidemiológico y grupo de edad; fuente de los conteos del SIR. |
| [Población municipal 2007–2025](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | `population_municipal_2007_2025.csv`: población anual DANE por edad; denominadores para los casos esperados. |
| [Cobertura municipal de vacunación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/vaccine_coverage/README.md) | Copia local `data/vaccine_coverage_municipal_lagged_2016_2025.csv`: porcentajes administrativos PAI de primera dosis y refuerzo, metas y códigos territoriales. |
| [Geometrías del MGN 2025](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/municipios#geometr%C3%ADas-geojson-del-mgn-2025) | Códigos y límites territoriales del mapa; permiten distinguir municipios de áreas no municipalizadas. |

El año epidemiológico de las notificaciones se deriva de la **fecha de
notificación**. La cobertura conserva el año de análisis de su fuente, que ya
corresponde al año de la hoja PAI original más uno: no se aplica otro rezago.
Para 2015–2019 se dispone de cobertura etiquetada 2016–2019; los otros dos
períodos usan todos sus años. El refuerzo no se clasifica en 2015–2019 porque
no tiene cobertura completa para esa etapa.

## Diccionario del CSV

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `period` | Categoría | Período de agregación: `2015-2019`, `2020-2021` o `2022-2025`. |
| `code` | Texto | Código DIVIPOLA homologado de cinco caracteres. |
| `years` | Entero | Número de años del período del SIR: 5, 2 o 4. |
| `observed_known_age` | Conteo | Notificaciones con edad conocida; numerador de ambos SIR. |
| `observed_unknown_age` | Conteo | Notificaciones sin edad conocida, excluidas de los cocientes SIR. |
| `observed_all_ages` | Conteo | Total de notificaciones, suma de las dos columnas anteriores. |
| `population_years_total` | Entero | Suma de poblaciones anuales de los cinco grupos de edad, en personas-año. |
| `expected_period` | Número | Notificaciones esperadas con las tasas por edad de los 1.102 municipios durante el mismo período. |
| `sir_period` | Número o ausente | `observed_known_age / expected_period`; SIR usado en la matriz, el diagrama y el mapa. |
| `expected_pre` | Número | Notificaciones esperadas con las tasas por edad de 2008–2014, aplicadas a la población del período analizado. |
| `sir_pre` | Número o ausente | `observed_known_age / expected_pre`; comparación con la referencia prevacunal fija. |
| `years_without_notification_row` | Entero | Años del período sin fila de notificaciones para el municipio en la fuente agregada. |
| `coverage_years_available` | Entero o ausente | Años de cobertura con fila disponible, antes de comprobar el porcentaje de cada dosis. |
| `coverage_years_expected` | Entero o ausente | Años requeridos de cobertura: 4 para 2015–2019, 2 para 2020–2021 y 4 para 2022–2025. |
| `coverage_first_dose_mean` | Número o ausente | Media de los porcentajes originales de primera dosis disponibles, sin tope. |
| `coverage_first_dose_years` | Entero o ausente | Años con porcentaje original de primera dosis no faltante. |
| `coverage_first_dose_above_100_years` | Entero o ausente | Años cuyo porcentaje original de primera dosis supera 100 %. |
| `coverage_first_dose_valid_years` | Entero o ausente | Años con primera dosis finita y no negativa, incluidos los ajustados a 100 %. |
| `coverage_first_dose_valid_mean` | Número o ausente | Media de primera dosis tras aplicar el tope anual de 100 % a los valores utilizables. |
| `coverage_booster_mean` | Número o ausente | Media de los porcentajes originales de refuerzo disponibles, sin tope. |
| `coverage_booster_years` | Entero o ausente | Años con porcentaje original de refuerzo no faltante. |
| `coverage_booster_above_100_years` | Entero o ausente | Años cuyo porcentaje original de refuerzo supera 100 %. |
| `coverage_booster_valid_years` | Entero o ausente | Años con refuerzo finito y no negativo, incluidos los ajustados a 100 %. |
| `coverage_booster_valid_mean` | Número o ausente | Media de refuerzo tras aplicar el tope anual de 100 % a los valores utilizables. |

Los tipos son lógicos: el CSV no almacena tipos físicos. Los casos esperados
pueden ser fraccionarios y los SIR son adimensionales. Las columnas de cobertura
se expresan en puntos porcentuales (92,9 representa 92,9 %, no 0,929).

## Generación y relación con las visualizaciones

[`scripts/generate_sir_coverage_panel.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_sir_coverage_panel.py)
genera el CSV uniendo el SIR y la cobertura por código y período. Homologa los
códigos históricos antes de agrupar; si se fusionan territorios, pondera sus
porcentajes administrativos por las metas PAI originales.

Se aplica el tope de **100 % a cada porcentaje anual finito y no negativo antes
de calcular la media del período**. Por ejemplo, 120 % y 80 % dan una media
utilizable de 90 %, mientras que la media original es 100 %. El dato de entrada
no se modifica. El número de años ajustados queda disponible en las columnas
`above_100_years`.

Los controles seleccionan el período, la dosis y el corte de cobertura. Se usan
`coverage_first_dose_valid_mean` o `coverage_booster_valid_mean`, siempre que sus
años utilizables coincidan con `coverage_years_expected`. La matriz separa
SIR < 1 y SIR ≥ 1, y cobertura inferior al corte e igual o superior a él.
El mapa usa esas cuatro categorías. El diagrama y LOESS incluyen los mismos
municipios; el detalle permite consultar la media original y los años ajustados.
Las comparaciones de cobertura usan ocho decimales, la precisión del CSV.

El corte inicial es **92,9 %**, redondeado de
`100 × (1 − 1/6,8636) / 0,92 ≈ 92,86 %`, del
[escenario R₀ con edades individuales](../varicela_grupo_edad/README_r0_individual_age.md).
El corte es una referencia descriptiva; no se estima con este CSV ni es una meta
calibrada para Colombia. No interviene en el cálculo del SIR.

## Valores ausentes y alcance

Un municipio con años faltantes, porcentajes negativos o no finitos no se
clasifica para esa combinación de período y dosis. Una media calculable con
parte de los años no basta: se exige cobertura utilizable en todos los años
requeridos. Un cero registrado y válido se conserva; un faltante no se convierte
en cero ni en 100 %. El SIR queda ausente si sus casos esperados son cero.

El mapa usa los **1.102 municipios del conjunto de SIR**, con población disponible
en los 18 años de 2008–2025. En Amazonas incluye Leticia y Puerto Nariño; las otras
nueve entidades —El Encanto, La Chorrera, La Pedrera, La Victoria, Mirití-Paraná,
Puerto Alegría, Puerto Arica, Puerto Santander y Tarapacá— están clasificadas como
áreas no municipalizadas y quedan fuera del cálculo y de la capa coloreada.
El espacio sin color significa que el territorio está fuera del universo, no
cero casos ni baja cobertura; tampoco se debe al tope de 100 %. Dentro del
universo, el gris claro identifica cobertura incompleta o inválida.

Con los datos actuales, primera dosis 2015–2019 incluye los 1.102 municipios,
654 con algún año ajustado; refuerzo 2022–2025 incluye también los 1.102,
474 con algún año ajustado. Los valores originales de la sección de comparación
de coberturas se conservan sin este tope.

Las cifras representan notificaciones de vigilancia, no todas las infecciones.
El tope no corrige el origen de porcentajes superiores a 100 %. La cobertura de
una cohorte infantil no mide la inmunidad de toda la población. El SIR usa tasas
de referencia propias de cada período; sus cambios no equivalen a cambios
absolutos de incidencia. No se publican intervalos de incertidumbre municipales
y las asociaciones con cobertura son descriptivas, sin interpretación causal.
