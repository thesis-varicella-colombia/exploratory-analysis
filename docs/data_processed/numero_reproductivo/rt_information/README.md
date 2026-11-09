# Diagnóstico de precisión de Rₜ: especificaciones de los datos

## Descripción y archivos

Este conjunto resume la precisión de las estimaciones diarias de Rₜ y su dependencia
de la previa. Alimenta la tabla «Criterios de precisión y resultados Rₜ» para
la selección nacional, departamental o municipal de la página.

- [Resultados de todos los territorios (CSV)](all_periods.csv).
- [Parámetros, criterios y límites (JSON)](metadata.json).
- [Ejemplo nacional (JSON)](national.json). Cada territorio tiene un archivo
  `<id>.json` con `id`, `name` y una lista `rows`; sus identificadores se encuentran
  en el catálogo de las [series diarias de origen](../rt_stratified/README.md).

El CSV tiene **27.744 filas**: 1.156 selecciones × dos fechas de referencia ×
cuatro períodos × tres límites de precisión. Incluye Colombia, 33 departamentos
(Bogotá D.C. incluida) y 1.122 entidades municipales, siempre para todas las edades.
Cada fila representa una combinación única de `id`, `method`, `period` y `width_limit`.
Cada JSON territorial contiene 24 filas. La tabla muestra ocho al elegir un límite.

El CSV utiliza coma como separador, punto decimal y campos vacíos para valores
ausentes. Los JSON utilizan `null`. Los diagnósticos numéricos se publican con
hasta ocho decimales, pero heredan el redondeo de las estimaciones originales.

## Origen y script generador

El insumo directo son los archivos diarios completos
`rt_stratified/{notification,symptom}/{id}.json.gz` y sus calendarios, documentados
en el [README del dataset de Rₜ diario por edad y territorio](../rt_stratified/README.md).
Se utilizan `count`, `window_cases`, `rt`, `rt_lower_95`, `rt_upper_95` y los campos
de calendario `date`, `year` y `missing_week`. Se excluyen las series por edad.
**No se usan los promedios de los archivos reducidos para visualización.**

Los registros originales proceden de las fechas `FEC_NOT` e `INI_SIN` de los CSV
individuales de varicela, descritos en el
[README de Sivigila de data-processing](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos).
Los datos originales no se publican en ese repositorio debido a su tamaño.

[`scripts/analyze_rt_information.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/analyze_rt_information.py)
genera este diagnóstico sin modificar ni volver a estimar Rₜ. La
[metodología de estimación](../README.md) describe el modelo y sus parámetros.

## Criterios aplicados

Se considera estimable un día observado con media posterior positiva y finita,
conteo de ventana válido y límites finitos que contienen la media. Después se
comprueban simultáneamente la anchura relativa y los aportes formales de la previa:

$$
\frac{R_t^{\mathrm{sup}}-R_t^{\mathrm{inf}}}{\widehat R_t}\leq\ell,
\qquad \ell\in\{0{,}5;\ 1;\ 2\}.
$$

Un límite menor es más exigente. Con $\ell=1$, la anchura del intervalo no puede
superar la media posterior. Para la previa de forma $\alpha=1$ y tasa $\beta=0{,}2$:

$$
\frac{\alpha}{\alpha+C_t}\leq 0{,}10,
\qquad
\frac{\beta}{\beta+L_t}\leq 0{,}10.
$$

$C_t$ es el conteo total y $L_t$ la infectividad acumulada de la ventana de 14 días.
Como el archivo de origen no publica $L_t$, el script obtiene el segundo aporte
mediante la identidad $\beta\widehat R_t/(\alpha+C_t)$. Esta operación utiliza
la media posterior redondeada a seis decimales. Estos porcentajes se refieren
a los parámetros de la Gamma, no a una fracción de incertidumbre explicada.

## Diccionario del CSV

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `id` | Texto | Identificador de la selección nacional o territorial. |
| `dimension` | Categoría | `national`, `department` o `municipality`. |
| `name` | Texto | Nombre de la selección. |
| `method` | Categoría | `notification` para fecha de notificación o `symptom` para inicio de síntomas. |
| `period` | Categoría | Años epidemiológicos: `2008-2014`, `2015-2019`, `2020-2021` o `2022-2025`. |
| `width_limit` | Número | Límite ℓ de anchura relativa: 0,5, 1 o 2. |
| `observed_days` | Entero | Días del período fuera de semanas nacionales sin información; no exige que exista Rₜ. |
| `estimated_days` | Entero | Días observados con estimación válida según las comprobaciones anteriores. |
| `estimated_pct` | Número o ausente | Porcentaje de días observados que tienen estimación válida. |
| `information_days` | Entero | Días estimables que cumplen tanto el límite de anchura como ambos límites de aporte de la previa. |
| `information_pct_observed` | Número o ausente | Porcentaje de días observados que cumplen los criterios. |
| `information_pct_estimated` | Número o ausente | Porcentaje de días estimables que cumplen los criterios. |
| `median_relative_width` | Número o ausente | Mediana de la anchura relativa entre todos los días estimables, no solo los que cumplen. |
| `median_window_cases` | Número o ausente | Mediana de casos en la ventana de 14 días entre todos los días estimables. |
| `interval_above_one` | Entero | Días que cumplen los criterios y cuyo límite inferior es mayor que 1. |
| `interval_below_one` | Entero | Días que cumplen los criterios y cuyo límite superior es menor que 1. |
| `interval_includes_one` | Entero | Días que cumplen los criterios y cuyo intervalo incluye 1, también en sus extremos. |
| `longest_start` | Fecha o ausente | Primer día del tramo consecutivo más largo que cumple dentro del período. |
| `longest_end` | Fecha o ausente | Último día de ese tramo. |
| `longest_days` | Entero | Longitud del tramo en días calendario; cero si ningún día cumple. |

`metadata.json` registra las fuentes, número de selecciones, períodos, límites,
fórmulas, parámetros de la previa y convenciones de ausencia, redondeo y tramos.

## Interpretación y límites

Las semanas sin datos se excluyen de los días observados. Los días de inicio
o reinicio sin Rₜ pueden estar observados, pero no son estimables. Las tres
categorías de posición del intervalo respecto a 1 suman `information_days`.

Cumplir los criterios indica menor incertidumbre condicional y menor aporte
formal de la previa; **no valida la vigilancia ni demuestra crecimiento o descenso**.
El intervalo puede incluir 1. Las ventanas solapadas de 14 días no son observaciones
independientes y los tramos consecutivos no son episodios validados. No se incorpora
subregistro ni fechas faltantes, ni se evalúa aquí la sensibilidad a otras previas,
ventanas o distribuciones del intervalo serial.
