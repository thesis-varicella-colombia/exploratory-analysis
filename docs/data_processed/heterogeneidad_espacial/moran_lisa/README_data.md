# Moran global y clústeres LISA municipales por período

Los mapas y la tabla de esta subsección usan dos CSV generados por
[`scripts/generate_moran_lisa.py`](../../../../scripts/generate_moran_lisa.py):
[`moran_global_periods.csv`](../moran_global_periods.csv), un resumen por período,
y [`moran_lisa_periods.csv`](../moran_lisa_periods.csv), el detalle por municipio.
La [metodología del cálculo](README.md) documenta las fórmulas, la vecindad y el
esquema de permutaciones; esta ficha describe las fuentes, la medida y las columnas.

## Fuentes y medida

Las tasas de entrada son las mismas de la
[incidencia notificada municipal](../README_spatial_series.md): notificaciones de
varicela (evento 831) de [Sivigila, INS](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx)
por municipio de residencia y año epidemiológico de la **fecha de notificación**,
sobre denominadores poblacionales anuales. La tasa de cada período es
`suma de notificaciones / suma de poblaciones anuales × 100.000`, un promedio anual
ponderado por población. El año 2007 se excluye por la discrepancia documentada en
la serie de notificaciones.

Sobre esas tasas se calculan, por período, la **I de Moran global** (asociación
espacial del conjunto del país) y los **indicadores locales LISA** de cada
municipio, con su clasificación en cuadrantes HH, LL, HL y LH. «Alto» y «bajo» se
definen respecto de la media municipal de cada período, no por un umbral absoluto.

## Cobertura y universo

Se usa la [cartografía MGN 2025 del DANE](https://geoportal.dane.gov.co/mparcgis/rest/services/MGN2025/Serv_CapasMGN_2025/FeatureServer/317)
para tomar un punto interior de cada municipio y construir la vecindad por los ocho
vecinos más cercanos. El universo son los **1.102 municipios con tasa válida en los
cuatro períodos** (2008–2014, 2015–2019, 2020–2021 y 2022–2025); la vecindad es la
misma en todos ellos. Se excluye **Nuevo Belén de Bajirá (27493)** por falta de
tasa. Los mapas muestran por defecto los clústeres sin ajuste (`cluster_nominal`),
que son exploratorios; el selector permite ver los que resisten el ajuste de
Benjamini–Hochberg (`cluster_fdr`).

## Columnas de `moran_global_periods.csv`

Una fila por período.

| Columna | Descripción |
| --- | --- |
| `period` | Período analizado. |
| `municipalities` | Municipios incluidos (1.102 en todos los períodos). |
| `neighbors` | Número de vecinos más cercanos (8). |
| `permutations` | Permutaciones usadas (9.999). |
| `global_i` | I de Moran global del período. |
| `p_positive` | Valor p unilateral por permutación para asociación positiva (mínimo 0,0001). |
| `hh_nominal` | Municipios High–High con p ≤ 0,05 sin ajuste. |
| `ll_nominal` | Municipios Low–Low con p ≤ 0,05 sin ajuste. |
| `hh_fdr` | Municipios High–High con q ≤ 0,05 tras Benjamini–Hochberg. |
| `ll_fdr` | Municipios Low–Low con q ≤ 0,05 tras Benjamini–Hochberg. |

## Columnas de `moran_lisa_periods.csv`

Una fila por municipio y período.

| Columna | Descripción |
| --- | --- |
| `period` | Período analizado. |
| `code` | Código territorial de cinco dígitos. |
| `rate_per_100k` | Tasa municipal del período por 100.000 habitantes. |
| `lag_deviation` | Rezago espacial: promedio de las desviaciones de los ocho vecinos. |
| `local_i` | Indicador local LISA del municipio. |
| `p_two_sided` | Valor p local bilateral por permutación condicional. |
| `q_bh` | Valor q tras el ajuste de Benjamini–Hochberg del período. |
| `cluster_nominal` | Cuadrante (HH, LL, HL, LH) si p ≤ 0,05 sin ajuste; `NS` en otro caso. |
| `cluster_fdr` | Cuadrante si q ≤ 0,05 tras el ajuste; `NS` en otro caso. |

## Persistencia de los clústeres

A lo largo de los tres períodos no pandémicos (2008–2014, 2015–2019 y 2022–2025),
**23 municipios repiten la etiqueta High–High y 31 la Low–Low** con `cluster_nominal`
(p local ≤ 0,05 sin ajuste): unos pocos territorios cargan de forma sostenida con
incidencia alta o baja frente a su entorno. Esa persistencia es frágil: tras el
ajuste por comparaciones múltiples (`cluster_fdr`) quedan **0 High–High y 0 Low–Low**
repetidos en los tres períodos. Repetir la etiqueta período tras período no basta
para distinguir una señal estable del ruido de evaluar 1.102 municipios a la vez.

## Límites

El análisis es descriptivo: no prueba transmisión entre municipios vecinos ni
atribuye los cambios a la vacunación. Una tasa baja puede reflejar subregistro o un
denominador inestable. La [metodología](README.md) detalla el esquema de
permutaciones, el ajuste por comparaciones múltiples y la sensibilidad a la
vecindad.

## Descargas

- [`moran_global_periods.csv`](../moran_global_periods.csv): resumen de Moran global por período.
- [`moran_lisa_periods.csv`](../moran_lisa_periods.csv): resultados LISA municipales por período.
