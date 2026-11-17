# Sensibilidad a la vecindad espacial

Esta comprobación repite el cálculo de Moran global y LISA con **tres valores de
vecinos más cercanos (4, 8 y 12)** para mostrar cuánto dependen los resultados de
esa elección. La definió [`scripts/analyze_spatial_seasonal_sensitivity.py`](../../../../scripts/analyze_spatial_seasonal_sensitivity.py).
El cálculo principal, las fórmulas y el esquema de permutaciones se documentan en la
[metodología](README.md) y en las [especificaciones de los datos](README_data.md).

## Qué se mantiene y qué cambia

Se conservan los mismos **1.102 municipios**, las mismas tasas por período, la misma
geometría, 9.999 permutaciones y la semilla 2026. Solo cambia el número de vecinos
más cercanos: 4, 8 o 12. Los pesos de cada fila siguen sumando uno ($1/k$ por
vecino). El caso de 8 vecinos es el del análisis principal y se reutiliza sin
cambios como referencia.

Para cada vecindad se vuelve a aplicar el mismo ajuste de Benjamini–Hochberg dentro
de cada período. La coincidencia de los clústeres **High–High (HH)** con los de 8
vecinos se mide con el **índice de Jaccard**: el número de municipios HH comunes a
las dos vecindades dividido por el número de municipios que son HH en al menos una.
Vale 1 si los conjuntos coinciden por completo y queda indefinido (vacío) si ambos
conjuntos están vacíos, caso que no se interpreta como coincidencia.

## Archivos

- [`spatial_sensitivity.csv`](../spatial_sensitivity.csv): resumen por período y vecindad.
- [`spatial_sensitivity_local.csv`](../spatial_sensitivity_local.csv): resultado local por municipio, período y vecindad.
- [`spatial_seasonal_sensitivity.metadata.json`](../spatial_seasonal_sensitivity.metadata.json): método y límites (bloque `spatial`).

## Columnas de `spatial_sensitivity.csv`

Una fila por período y número de vecinos.

| Columna | Descripción |
| --- | --- |
| `period` | Período analizado. |
| `neighbors` | Número de vecinos más cercanos (4, 8 o 12). |
| `municipalities` | Municipios incluidos (1.102). |
| `permutations` | Permutaciones usadas (9.999). |
| `global_i` | I de Moran global con esa vecindad. |
| `p_positive` | Valor p unilateral por permutación para asociación positiva. |
| `hh_nominal` | Municipios High–High con p ≤ 0,05 sin ajuste. |
| `hh_fdr` | Municipios High–High con q ≤ 0,05 tras Benjamini–Hochberg. |
| `ll_fdr` | Municipios Low–Low con q ≤ 0,05 tras Benjamini–Hochberg. |
| `hh_jaccard_nominal` | Índice de Jaccard de los HH nominales frente a los de 8 vecinos; vacío si ambos conjuntos están vacíos. |
| `hh_added_nominal` | HH nominales presentes con esta vecindad y ausentes con 8 vecinos. |
| `hh_removed_nominal` | HH nominales presentes con 8 vecinos y ausentes con esta vecindad. |
| `hh_jaccard_fdr` | Índice de Jaccard de los HH ajustados frente a los de 8 vecinos; vacío si ambos conjuntos están vacíos. |
| `hh_added_fdr` | HH ajustados presentes con esta vecindad y ausentes con 8 vecinos. |
| `hh_removed_fdr` | HH ajustados presentes con 8 vecinos y ausentes con esta vecindad. |

## Columnas de `spatial_sensitivity_local.csv`

Una fila por municipio, período y número de vecinos.

| Columna | Descripción |
| --- | --- |
| `period` | Período analizado. |
| `neighbors` | Número de vecinos más cercanos (4, 8 o 12). |
| `code` | Código territorial de cinco dígitos. |
| `p_two_sided` | Valor p local bilateral por permutación condicional. |
| `q_bh` | Valor q tras el ajuste de Benjamini–Hochberg del período y vecindad. |
| `cluster_nominal` | Cuadrante (HH, LL, HL, LH) si p ≤ 0,05 sin ajuste; `NS` en otro caso. |
| `cluster_fdr` | Cuadrante si q ≤ 0,05 tras el ajuste; `NS` en otro caso. |

## Campos de `spatial_seasonal_sensitivity.metadata.json` (bloque `spatial`)

| Campo | Descripción |
| --- | --- |
| `neighbors` | Valores de vecinos comparados (4, 8, 12). |
| `baseline` | Vecindad de referencia (8). |
| `permutations` | Permutaciones por prueba (9.999). |
| `seed` | Semilla aleatoria (2026). |
| `weights` | Definición de los pesos: vecinos más cercanos por gran círculo, estandarizados por filas, mismo universo de 1.102 entidades. |
| `baseline_output` | Indica que los resultados de 8 vecinos se reutilizan sin cambios. |
| `local_test` | Prueba local usada: permutación condicional bilateral y Benjamini–Hochberg por período. |
| `jaccard` | Definición del índice de coincidencia HH (intersección/unión frente a 8 vecinos; vacío si ambos conjuntos están vacíos). |
| `limits` | Límites: solo sensibilidad a k, no contigüidad ni suavizado de áreas pequeñas; valores p de Monte Carlo finitos; sin prueba de diferencias en I. |

## Lectura

La I de Moran global permanece positiva con los tres valores de vecinos, pero los
clústeres HH locales dependen de la especificación: en 2022–2025 hay 0 HH ajustados
con 4 u 8 vecinos y 15 con 12. Por eso no deben presentarse como una selección
territorial invariable. La comprobación no cubre todavía contigüidad ni suavizado de
tasas de municipios pequeños, y no prueba transmisión entre vecinos ni diferencias
significativas de la I entre etapas.
