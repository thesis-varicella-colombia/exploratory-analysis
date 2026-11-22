# Incidencia municipal suavizada por Empirical Bayes

Estos archivos los genera
[`scripts/smooth_rates_empirical_bayes.py`](../../../../scripts/smooth_rates_empirical_bayes.py):
[`municipal_incidence_eb.csv`](municipal_incidence_eb.csv), el panel municipal con
la tasa cruda y las dos tasas suavizadas —global (nacional) y local (vecinos)—
con sus pesos de encogimiento, y
[`municipal_incidence_eb.metadata.json`](municipal_incidence_eb.metadata.json),
el modelo, la escala y los resúmenes por grupo de edad. Esta ficha describe las
fuentes, el universo y las columnas. Las fórmulas del estimador están en el
[README de metodología](README.md); aquí no se repite la matemática.

## Fuentes

- **Panel municipal completo:** construido por `read_panel()` de
  [`generate_age_standardized_sir.py`](../../../../scripts/generate_age_standardized_sir.py):
  conteos observados (`observed_<grupo>`) y población (`population_<grupo>`) por
  grupo de edad, municipio y año, para 2008–2025. Es el único insumo del cálculo;
  la basal 2008–2014 se obtiene sumando los siete años de referencia.

## Universo

- **Municipios:** 1.102 municipios comparables (una geografía estable entre
  periodos), identificados por el campo `code`.
- **Años anuales:** 2008–2025, con denominador de población del mismo año. La
  gráfica de evolución usa la serie suavizada completa; la lista de municipios lee
  los valores de 2024 y 2025.
- **Basal:** periodo agrupado **2008–2014**, con denominador en personas-año
  acumuladas. Aparece en la columna `year` con la etiqueta `baseline_2008_2014`.
- **Grupos de edad:** `all`, `under_1`, `1_4`, `5_14`, `15_49`, `50_plus`.

Cada combinación de municipio × (año anual o basal) × grupo de edad es una fila.
Con 1.102 municipios, 19 periodos (los 18 años 2008–2025 más la basal) y 6 grupos
de edad, el panel tiene 125.628 filas.

## Columnas de `municipal_incidence_eb.csv`

| Columna | Descripción |
| --- | --- |
| `code` | Código territorial de cinco dígitos del municipio. |
| `year` | Año `2008`–`2025`, o `baseline_2008_2014`. |
| `age_group` | Grupo de edad: `all`, `under_1`, `1_4`, `5_14`, `15_49` o `50_plus`. |
| `scope` | `annual` para los años 2008–2025; `baseline` para la basal agrupada. |
| `observed` | Casos observados del municipio en ese periodo y grupo. En la basal, casos sumados 2008–2014. |
| `population` | Población expuesta (personas-año en la basal). |
| `rate_crude` | Tasa cruda por 100.000: `observed / population × 100.000`. |
| `rate_eb` | Tasa suavizada por EB **global** (encogida hacia la media nacional del grupo), por 100.000. |
| `shrinkage` | Peso de encogimiento global $C\in[0,1]$ aplicado a `rate_eb`. |
| `rate_eb_local` | Tasa suavizada por EB **local** (encogida hacia la media del vecindario: el municipio y sus 8 vecinos más cercanos), por 100.000. Nula si el municipio no tiene punto representativo o su vecindario tiene menos de dos áreas válidas. |
| `shrinkage_local` | Peso de encogimiento local $C^{\mathrm{loc}}\in[0,1]$ aplicado a `rate_eb_local`. Nulo en los mismos casos que `rate_eb_local`. |

### Cómo leer `shrinkage`

El peso `shrinkage` indica cuánto pesa la tasa del propio municipio frente a la
media de su grupo de edad en `rate_eb`:

- **Cerca de 1:** `rate_eb` se queda cerca de `rate_crude`; el municipio aporta
  información suficiente (población grande o grupo heterogéneo).
- **Cerca de 0:** `rate_eb` se acerca a la media del grupo; el municipio aporta
  poca información (población pequeña) o el grupo no muestra señal más allá del
  ruido Poisson.

Un `shrinkage` bajo advierte que `rate_eb` refleja sobre todo la media del grupo,
no los datos del municipio. Conviene leerlo junto a `observed` y `population`.

### Variante local (vecinos)

`rate_eb_local` y `shrinkage_local` provienen de la misma mecánica, pero encogen
cada municipio hacia la media de su **vecindario** (el municipio y sus 8 vecinos
más cercanos, con la matriz de vecindad de la sección 8 Moran/LISA) en vez de
hacia la media nacional. Al apoyarse en 9 municipios y no en todo el país, el EB
local estabiliza **menos** los municipios muy pequeños y recorta menos los
*outliers*; no es «más correcto» que el global, sino una elección distinta del
objetivo de encogimiento. Quedan **nulas** cuando el municipio no tiene punto
representativo o su vecindario tiene menos de dos áreas válidas. Las fórmulas de
la media y la varianza por vecindario están en el
[README de metodología](README.md#6-variante-local-vecinos-encogimiento-hacia-el-vecindario).

## Contenido de `municipal_incidence_eb.metadata.json`

| Clave | Contenido |
| --- | --- |
| `model_global` | Descripción del estimador global: EB Poisson–Gamma por grupo de edad y año (Marshall 1991), que encoge cada municipio hacia la media nacional del grupo. |
| `model_local` | Descripción del estimador local: EB Poisson–Gamma por vecindario (Marshall 1991), que encoge hacia la media del municipio y sus 8 vecinos más cercanos, con la misma matriz de vecindad que la sección 8 (Moran/LISA). |
| `rate_scale_per` | Escala de las tasas: `100000`. |
| `years` | Años anuales suavizados: `[2008, …, 2025]`. |
| `baseline_years` | Años que componen la basal agrupada: `[2008, …, 2014]`. |
| `neighbor_count` | Número de vecinos más cercanos del vecindario local: `8`. |
| `age_groups` | Mapa de código a etiqueta en español de cada grupo de edad. |
| `municipalities` | Número de municipios del panel: `1102`. |
| `municipalities_without_point` | Lista de municipios sin punto geográfico representativo, cuyo `rate_eb_local` y `shrinkage_local` quedan nulos. Puede estar vacía. |
| `shrinkage_rule` | Regla del encogimiento: `C = phi / (phi + m / n)`; `smoothed = C*crude + (1-C)*m`; `phi=0` lleva todo a la media objetivo (nacional en el global, del vecindario en el local). |
| `local_note` | Nota sobre la variante local: cuándo quedan nulos `rate_eb_local`/`shrinkage_local` y por qué estabiliza menos los municipios pequeños que el global. |
| `scope_note` | Nota sobre el alcance de las filas: las anuales cubren 2008–2025 para la gráfica de evolución, la lista de municipios lee 2024 y 2025, y las de basal agrupan 2008–2014. |
| `limitations` | Recordatorio de que EB solo estabiliza varianza y depende del objetivo de encogimiento (nacional o del vecindario). |
| `group_summaries` | Resumen por cada conjunto suavizado (ver abajo). |

### `group_summaries`

Una entrada por cada conjunto sobre el que se estimó el encogimiento, con clave
`annual_<grupo>_<año>` (p. ej. `annual_under_1_2024`) o `baseline_<grupo>`
(p. ej. `baseline_1_4`). Cada entrada contiene:

| Campo | Contenido |
| --- | --- |
| `mean_per_100k` | Media global del grupo $m$, por 100.000 (tasa agrupada: total de casos sobre total de población). |
| `between_var` | Varianza entre áreas $\phi$, en unidades de (tasa por 100.000)². `0` indica que no hay señal detectable más allá del ruido Poisson y que todo el grupo colapsa a la media. |
| `n` | Número de municipios con datos válidos usados en la estimación de ese grupo. |

Estos resúmenes permiten reconstruir hacia dónde se encogió cada municipio
(`mean_per_100k`) y cuánta señal real había en el grupo (`between_var`).

## Valores ausentes

Si la población es ausente, no finita o no positiva, o el conteo no es finito,
la fila no entra en la estimación y `rate_crude`, `rate_eb` y `shrinkage` quedan
nulos. Un conteo de cero casos sobre población positiva sí produce
`rate_crude = 0` y una `rate_eb` válida (encogida hacia la media del grupo).

Además, `rate_eb_local` y `shrinkage_local` quedan nulos —aun con `rate_eb`
válida— cuando el municipio no tiene punto geográfico representativo (está en
`municipalities_without_point`) o cuando su vecindario reúne menos de dos áreas
válidas, de modo que no hay varianza entre áreas que estimar.

## Límites

El encogimiento EB **estabiliza la varianza; no corrige subregistro, cambios de
vigilancia ni errores de denominador**, y depende del supuesto Gamma y del
objetivo de encogimiento (la media nacional en el global, la del vecindario en el
local). Las tasas suavizadas de los municipios pequeños están desplazadas hacia
la media objetivo por diseño: son más estables, no más «verdaderas» caso por
caso. El detalle está en el [README de metodología](README.md).

## Regeneración

Desde la raíz del repositorio:

```bash
.venv/bin/python scripts/smooth_rates_empirical_bayes.py
```

## Descargas

- [`municipal_incidence_eb.csv`](municipal_incidence_eb.csv): panel municipal con
  la tasa cruda, las tasas suavizadas global y local y sus pesos de encogimiento
  por periodo y grupo de edad.
- [`municipal_incidence_eb.metadata.json`](municipal_incidence_eb.metadata.json):
  modelo, escala, años, municipios, regla de encogimiento, límites y resúmenes
  por grupo.
