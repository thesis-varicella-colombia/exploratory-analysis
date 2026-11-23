# Casos observados, esperados y SIR municipal: especificación de los datos

La subsección «Comparación entre municipios: casos observados, esperados y SIR»
utiliza dos archivos generados por
[`scripts/generate_age_standardized_sir.py`](../../../scripts/generate_age_standardized_sir.py):

- [`age_standardized_sir_municipal_periods.csv`](age_standardized_sir_municipal_periods.csv):
  4.408 filas, una por municipio y período.
- [`age_standardized_reference_rates.csv`](age_standardized_reference_rates.csv):
  20 filas, una por grupo de edad y período, con las tasas usadas como referencia.
- [`age_standardized_sir_municipal_periods.metadata.json`](age_standardized_sir_municipal_periods.metadata.json):
  reglas de geografía, homologación y referencias.

Esta ficha describe el cálculo del SIR. El cruce posterior con cobertura utiliza
estos resultados, pero añade sus propios requisitos de disponibilidad y validez
de los porcentajes administrativos.

## Fuentes y universo

- **Notificaciones:** registros de varicela de Sivigila (INS), agregados por
  municipio de residencia y semana de la fecha de notificación en
  `data/sivigila_integrado_notification_semanal_municipal.parquet/`.
- **Población:** estimaciones y proyecciones municipales del DANE por grupo de
  edad y año, en `data/population_municipal_2007_2025.csv`.
- **Geografía:** límites municipales DANE MGN 2025 de
  [`municipal_boundaries_dane.geojson`](../cartografia/municipal_boundaries_dane.geojson).

Se incluyen los mismos **1.102 municipios con población disponible en los 18 años
2008–2025**. El generador valida que las poblaciones por edad no sean faltantes
ni negativas. Este conjunto constituye el «panel municipal» del análisis.
Las tasas de referencia se calculan reuniendo las notificaciones y las poblaciones
de esos municipios; no son el promedio simple de sus tasas municipales.

Los códigos históricos se homologan antes de agrupar. En particular, la población
histórica de Mapiripana (`94663`) se suma a Barrancominas (`94343`). Desde 2020,
Mapiripana tiene población cero en los cinco grupos de edad en la fuente; el
generador comprueba que no aparezcan valores positivos que requieran revisar una
posible superposición. Los demás códigos equivalentes figuran en los metadatos.

## Períodos y edades

Los archivos incluyen **2008–2014, 2015–2019, 2020–2021 y 2022–2025**.
El primer período es la referencia prevacunal fija; los otros tres se muestran
en el cruce con cobertura.

Los cinco grupos de edad son `under_1` (menores de 1 año), `1_4`, `5_14`,
`15_49` y `50_plus` (50 años o más). Las notificaciones sin edad conocida se
conservan en una columna aparte y no intervienen en el numerador del SIR ni en
las tasas de referencia por edad.

## Cálculo e interpretación

Para cada grupo de edad, la tasa de referencia es la suma de notificaciones de
los 1.102 municipios dividida entre la suma de sus poblaciones anuales durante
el período. Esta última suma se expresa en **personas-año**; no cuenta personas
únicas seguidas individualmente.

Para cada municipio, se multiplica su población acumulada de cada grupo de edad
por la tasa de referencia correspondiente y se suman los cinco resultados.
El resultado es el número de notificaciones esperadas: una referencia comparativa,
no una predicción de infecciones futuras. El cociente entre las notificaciones
observadas con edad conocida y las esperadas es el **SIR**, o razón estandarizada
de incidencia, calculado mediante estandarización indirecta por edad.

Se conservan dos referencias:

- **`expected_period` y `sir_period`:** usan las tasas del mismo período que los
  datos municipales. Por ejemplo, 2022–2025 usa las tasas de 2022–2025.
  La referencia cambia entre períodos y compara cada municipio con el conjunto
  de municipios durante la misma etapa. Es el SIR usado en la matriz de cobertura.
- **`expected_pre` y `sir_pre`:** usan siempre las tasas de 2008–2014, aplicadas
  a la población por edad del municipio en el período analizado. Permiten
  contrastar lo registrado con lo que correspondería si se mantuvieran las tasas
  prevacunales. En 2008–2014 ambas referencias coinciden.

Un SIR de 1 indica tantas notificaciones como las esperadas; por encima de 1,
más; por debajo de 1, menos. Por ejemplo, 1,5 indica un 50 % más que la referencia.
El SIR es adimensional; los casos esperados pueden ser fraccionarios.

## Columnas del archivo municipal

La clave única es `period` + `code`. Los códigos DIVIPOLA deben leerse como texto
para conservar sus ceros iniciales.

| Columna | Significado |
| --- | --- |
| `period` | Período de agregación. |
| `code` | Código DIVIPOLA homologado de cinco caracteres. |
| `years` | Número de años del período: 7, 5, 2 o 4. |
| `observed_known_age` | Notificaciones con edad conocida; numerador de ambos SIR. |
| `observed_unknown_age` | Notificaciones sin edad conocida, excluidas de los SIR. |
| `observed_all_ages` | Total de notificaciones: suma de las dos columnas anteriores. |
| `population_years_total` | Suma de las poblaciones anuales de los cinco grupos de edad, en personas-año. |
| `expected_period` | Notificaciones esperadas con las tasas por edad del mismo período. |
| `sir_period` | `observed_known_age / expected_period`. |
| `expected_pre` | Notificaciones esperadas con tasas por edad fijas de 2008–2014. |
| `sir_pre` | `observed_known_age / expected_pre`. |
| `years_without_notification_row` | Número de años del período sin fila de notificaciones para el municipio en la fuente agregada. |

## Columnas de las tasas de referencia

La clave única es `period` + `age_group`.

| Columna | Significado |
| --- | --- |
| `period` | Período de referencia. |
| `age_group` | Uno de los cinco grupos de edad. |
| `observed` | Notificaciones con edad conocida del grupo, sumadas en los 1.102 municipios. |
| `population_years` | Población acumulada del grupo en esos municipios, en personas-año. |
| `rate_per_100k` | `100000 × observed / population_years`. |

Para calcular los casos esperados se usa la tasa por persona-año, equivalente a
`rate_per_100k / 100000`. Los CSV se escriben con ocho decimales para los campos
flotantes; los cálculos del generador se realizan antes de ese redondeo.

## Disponibilidad de datos y resumen por períodos

Se reúnen los conteos en períodos de varios años para describir patrones
territoriales en series municipales con pocas notificaciones. Esto no garantiza
por sí solo la precisión de sus cocientes.

El [diagnóstico de ceros de 2008–2014](municipal_zero_diagnostics_2008_2014.csv)
examina las 1.122 entidades de la cartografía, un universo distinto de los 1.102
municipios del SIR. La mediana municipal de semanas sin notificaciones es 83,8 %.
En la entidad mediana, 35 de las 52 posiciones del calendario semanal tienen
los tres cuartiles históricos iguales a cero; 719 entidades presentan ese
resultado en al menos 26 posiciones y 111, en las 52. En esas posiciones no se
pueden distinguir las zonas de un canal cuartílico.

En el cálculo del SIR, un municipio-año sin fila de notificaciones se completa
con cero y queda señalado por `years_without_notification_row`. Ese valor indica
la ausencia de una fila en la fuente; no demuestra ausencia de transmisión.
Una notificación individual sin edad se conserva como edad desconocida, sin
redistribuirla entre los cinco grupos.

## Límites

Los datos representan notificaciones, no todas las infecciones ocurridas.
Cambios de vigilancia, subregistro y errores de población pueden afectar el SIR.
El ajuste tiene en cuenta la composición por edad, pero no controla otros factores
que difieren entre municipios.

Un `sir_period` mayor no implica un aumento absoluto entre períodos, porque su
referencia también cambia. Un cociente no se calcula cuando sus casos esperados
son cero: se deja vacío en el CSV. No se publican intervalos de incertidumbre;
pocos casos pueden producir cocientes inestables. El corte de 1 es descriptivo
y no establece por sí solo un exceso concluyente ni un efecto de la vacunación.

## Regeneración

Desde la raíz del repositorio, con los insumos locales disponibles:

```bash
.venv/bin/python scripts/generate_age_standardized_sir.py
```

El comando genera los dos CSV y el JSON de metadatos descritos en esta ficha.

## Referencia de cobertura en los análisis asociados

La matriz de SIR y cobertura utiliza inicialmente **92,9 %**, obtenido al redondear
`100 × (1 − 1/6,8636) / 0,92 ≈ 92,86 %` del
[escenario R₀ con edades individuales](../varicela_grupo_edad/README_r0_individual_age.md).
La clasificación, el cruce espacial y el seguimiento utilizan el corte redondeado
de 92,9 %, no el valor sin redondear. No interviene en el cálculo del SIR.
Es una referencia descriptiva bajo los supuestos de ese escenario y no una meta
de vacunación calibrada para Colombia.

## Datos del cruce con cobertura

La matriz, el diagrama y el mapa usan el archivo derivado
`age_standardized_sir_coverage_periods.csv`. Sus fuentes, diccionario, preparación
y alcance se documentan en las
[especificaciones del cruce municipal de SIR y cobertura](README_sir_coverage.md).
