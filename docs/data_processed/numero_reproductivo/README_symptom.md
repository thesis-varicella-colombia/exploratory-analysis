# Rₜ nacional por inicio de síntomas: especificaciones de los datos

## Descripción y archivo

[`rt_national_symptom_daily.csv`](rt_national_symptom_daily.csv) contiene los
conteos diarios por inicio de síntomas y las estimaciones de Rₜ para Colombia,
todas las edades. Cada fila representa una fecha; `date` es la clave única.

Hay **6.580 filas**, del 30 de diciembre de 2007 al 3 de enero de 2026, que cubren
los años epidemiológicos **2008–2025**. Hay 140 días sin conteo por ausencia de
referencia semanal y 6.180 días con estimación de Rₜ. Un conteo disponible no
implica que ya exista suficiente historia para estimar Rₜ.

El CSV usa UTF-8, coma como separador, punto decimal, fechas `AAAA-MM-DD` y campos
vacíos para ausencias. Los números se exportan con ocho decimales;
los conteos siguen siendo cantidades enteras.

## Origen

Los casos se cuentan directamente por `INI_SIN` en los CSV individuales
`Datos_AAAA_831.csv` de varicela, descritos en el
[README de Sivigila](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos).
Se conservan residencias válidas en DIVIPOLA, se homologan códigos y se excluyen
los ajustes `6` y `D`. Las fechas ausentes o no interpretables quedan fuera del
conteo. El archivo fuente de 2013 usa mes/día/año para `INI_SIN`; los demás,
día/mes/año.

Los totales diarios se contrastan con
`sivigila_integrado_symptom_semanal_municipal.parquet`, documentado en el
[README de integración de data-processing](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md).
La [referencia semanal publicada](weekly_series_symptom_2008_2025.csv) identifica
las semanas sin información. Los archivos originales no se publican en GitHub
debido a su tamaño.

## Diccionario del CSV

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `date` | Fecha | Fecha de inicio de síntomas `INI_SIN`. No es la fecha de infección. |
| `year` | Entero | Año epidemiológico; puede diferir del año calendario de `date`. |
| `week` | Entero | Semana epidemiológica, con calendario domingo–sábado y semana 1 que contiene el 4 de enero. |
| `cases` | Conteo o ausente | Registros incluidos cuyo inicio de síntomas interpretable corresponde al día. |
| `missing_week` | Booleano | `True` si falta información semanal nacional; `False` si la semana está observada. |
| `infectiousness` | Número o ausente | Suma ponderada de los conteos anteriores, Λₜ, calculada con los pesos del intervalo serial. |
| `rt` | Número o ausente | Media posterior de Rₜ para la ventana de 14 días que termina en esa fecha. |
| `rt_lower_95` | Número o ausente | Percentil 2,5 de la posterior, límite inferior del intervalo creíble del 95 %. |
| `rt_upper_95` | Número o ausente | Percentil 97,5 de la posterior, límite superior del intervalo creíble del 95 %. |
| `method` | Texto | Identificador `epiestim_parametric_si_python_daily_symptom_onset`. |
| `window_days` | Entero | Ventana de estimación: 14 días. |
| `serial_interval_mean_days` | Número | Media del intervalo serial: 14,1 días. |
| `serial_interval_sd_days` | Número | Desviación estándar del intervalo serial: 2,4 días. |
| `prior_mean` | Número | Media de la previa de Rₜ: 5. |
| `prior_sd` | Número | Desviación estándar de la previa de Rₜ: 5. |

## Generación y relación con la gráfica

[`scripts/rt_symptom_sivigila.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/rt_symptom_sivigila.py)
genera el CSV con el estimador compartido de `rt_daily_sivigila.py`. La
[metodología de Rₜ](README.md) explica el modelo y sus parámetros.

La gráfica carga una [versión reducida](rt_visualization/README.md) de las
[series nacionales y territoriales](rt_stratified/README.md). Comienza con eje
vertical 0–2 para distinguir las variaciones habituales; la opción de escala
completa permite ver los valores mayores sin modificar las estimaciones.
Los filtros territoriales cargan otra serie, no un subconjunto de este CSV nacional.

## Valores ausentes y alcance

Hay 20 semanas nacionales sin datos por síntomas, 18 de ellas en 2013; sus días
quedan ausentes, no en cero. Dentro de una semana observada, un día sin registros
tiene conteo cero. El estimador reinicia después de los vacíos y espera suficiente
historia antes de volver a publicar Rₜ.

En el archivo de 2013, solo 37.920 de 93.606 registros elegibles (40,5 %) tienen
`INI_SIN` interpretable. Esa incompletitud puede afectar las estimaciones aunque
su intervalo creíble sea estrecho. El intervalo no incorpora la incertidumbre
de las fechas faltantes, el subregistro ni los cambios de vigilancia.
