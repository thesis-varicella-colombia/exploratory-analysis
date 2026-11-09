# Rₜ nacional por fecha de notificación: especificaciones de los datos

## Descripción y archivo

[`rt_national_daily.csv`](rt_national_daily.csv) contiene los conteos diarios de
notificaciones de varicela y las estimaciones de Rₜ para Colombia, todas las edades.
Cada fila representa una fecha; `date` es la clave única.

Hay **6.580 filas**, del 30 de diciembre de 2007 al 3 de enero de 2026, que
corresponden a los años epidemiológicos **2008–2025**. Siete días tienen conteos
ausentes y 6.507 tienen estimación de Rₜ. Los días iniciales y los posteriores
a un vacío pueden tener conteos disponibles sin una estimación publicable.

El CSV usa UTF-8, coma como separador, punto decimal, fechas `AAAA-MM-DD` y campos
vacíos para valores ausentes. Los números se exportan con ocho decimales;
los conteos siguen siendo cantidades enteras.

## Origen

Los conteos se obtienen directamente de `FEC_NOT` en los CSV individuales
`Datos_AAAA_831.csv` de varicela (evento 831), descritos en el
[README de Sivigila](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos).
Se conservan las residencias válidas según DIVIPOLA, se homologan códigos históricos
y se excluyen los ajustes `6` y `D`. La fecha de notificación es interpretable en
todos los registros incluidos en la auditoría de los archivos 2007–2025.

La [serie semanal por notificación](../evolucion_semanal/README.md) permite
contrastar los totales diarios y distinguir semanas observadas de semanas sin
información. Los archivos originales de data-processing se documentan en sus
README; no están publicados en GitHub debido a su tamaño.

## Diccionario del CSV

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `date` | Fecha | Fecha individual de notificación `FEC_NOT`. |
| `year` | Entero | Año epidemiológico; puede diferir del año calendario de `date`. |
| `week` | Entero | Semana epidemiológica, con calendario domingo–sábado y semana 1 que contiene el 4 de enero. |
| `notifications` | Conteo o ausente | Registros incluidos cuya fecha de notificación corresponde al día. |
| `missing_week` | Booleano | `True` si la semana no tiene información en la referencia nacional; `False` si está observada. |
| `infectiousness` | Número o ausente | Suma de los conteos anteriores ponderados por el intervalo serial, Λₜ; no es un conteo observado de personas infecciosas. |
| `rt` | Número o ausente | Media posterior de Rₜ para la ventana de 14 días que termina en esa fecha. |
| `rt_lower_95` | Número o ausente | Percentil 2,5 de la posterior, límite inferior del intervalo creíble del 95 %. |
| `rt_upper_95` | Número o ausente | Percentil 97,5 de la posterior, límite superior del intervalo creíble del 95 %. |
| `method` | Texto | Identificador `epiestim_parametric_si_python_daily_notifications`. |
| `window_days` | Entero | Ventana de estimación: 14 días. |
| `serial_interval_mean_days` | Número | Media del intervalo serial: 14,1 días. |
| `serial_interval_sd_days` | Número | Desviación estándar del intervalo serial: 2,4 días. |
| `prior_mean` | Número | Media de la previa de Rₜ: 5. |
| `prior_sd` | Número | Desviación estándar de la previa de Rₜ: 5. |

## Generación y relación con la gráfica

[`scripts/rt_daily_sivigila.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/rt_daily_sivigila.py)
genera el CSV y aplica el estimador descrito en la [metodología de Rₜ](README.md).
El archivo conserva los resultados diarios originales.

La página carga una [versión reducida para visualización](rt_visualization/README.md)
de las [series nacionales y territoriales](rt_stratified/README.md), derivadas
del mismo cálculo. Los filtros territoriales seleccionan otra serie; no filtran
filas de este CSV nacional ni promedian Rₜ municipales.

## Valores ausentes y alcance

La semana 52 de 2008 conserva sus siete días sin datos; no se imputan ceros.
Dentro de una semana observada, un día sin registros tiene conteo cero. Tras un
vacío, el estimador exige suficiente historia antes de publicar nuevamente Rₜ.
La completitud de `FEC_NOT` no garantiza que todos los casos hayan sido notificados.
Las demoras pueden desplazar y deformar la señal; el intervalo creíble no incorpora
subregistro, cambios de vigilancia ni incertidumbre del intervalo serial.
