# 2013–marzo de 2014: especificaciones de los datos del detalle de Rₜ

## Descripción y archivo de origen

Esta gráfica muestra **Rₜ por fecha de inicio de síntomas** del 1 de enero de 2013
al 31 de marzo de 2014, con escala vertical completa. Su propósito es diagnóstico:
examinar estimaciones que pueden estar afectadas por vacíos y cambios en el registro.

Es una vista de la serie
[`rt_national_symptom_daily.csv`](rt_national_symptom_daily.csv), no un dataset
ni una estimación adicionales. Para obtenerla se seleccionan las filas con
`2013-01-01 ≤ date ≤ 2014-03-31`, sin recalcular Rₜ al inicio del recorte.
Así se conserva la historia utilizada por el estimador original.

Para Colombia, todas las edades, el recorte contiene **455 fechas**, 126 con
conteo ausente y 135 con Rₜ disponible. El máximo de la media posterior en ese
intervalo es aproximadamente **17,01**, el 12 de diciembre de 2013.

## Origen y diccionario de los datos

La [especificación de la serie por síntomas](README_symptom.md) contiene el
diccionario completo del CSV, sus fuentes y el tratamiento de ausencias.
Los campos usados por este detalle son:

| Campo | Tipo lógico | Uso |
| --- | --- | --- |
| `date` | Fecha | Día de inicio de síntomas; eje horizontal y clave única. |
| `cases` | Conteo o ausente | Registros con inicio de síntomas en el día. |
| `missing_week` | Booleano | Identifica semanas sin información nacional. |
| `rt` | Número o ausente | Media posterior representada por la línea. |
| `rt_lower_95` | Número o ausente | Límite inferior de la banda creíble condicional del 95 %. |
| `rt_upper_95` | Número o ausente | Límite superior de esa banda. |

Los registros proceden de `INI_SIN` en los CSV individuales de varicela,
documentados en el [README de Sivigila](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos).
La referencia para contrastar los conteos es
`sivigila_integrado_symptom_semanal_municipal.parquet`, descrito en el
[README de integración](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md).
Los archivos originales no se publican en GitHub debido a su tamaño.

## Scripts y representación

[`scripts/rt_symptom_sivigila.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/rt_symptom_sivigila.py)
genera la serie diaria con la [metodología compartida](README.md).
[`scripts/reduce_rt_visualization.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/reduce_rt_visualization.py)
conserva los puntos diarios de este intervalo en el bloque de detalle de los
archivos para visualización. La función `rtSpec` de
[`docs/charts.js`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/docs/charts.js)
selecciona el período y utiliza la escala vertical completa.

Los filtros cargan el mismo detalle para el territorio seleccionado. Las cifras
anteriores describen la selección nacional; cambian al elegir otro territorio.

## Interpretación

En el archivo fuente de 2013, solo el **40,5 %** de los registros elegibles tiene
inicio de síntomas interpretable. La gráfica permite ver los picos que la vista
general 0–2 no muestra completos. Un valor alto no prueba por sí solo una
transmisión de esa magnitud: el intervalo creíble es condicional al modelo y no
cubre la incertidumbre de las fechas ausentes ni los cambios de vigilancia.
Las interrupciones se conservan; no representan cero casos ni Rₜ igual a cero.
