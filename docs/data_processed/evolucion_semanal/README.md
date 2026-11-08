# Evolución semanal de las notificaciones de varicela

## Descripción del dataset

[`weekly_series_2007_2025.csv`](weekly_series_2007_2025.csv) reúne las notificaciones
de varicela y sus tasas semanales en Colombia entre 2007 y 2025, para todas las
edades y cinco grupos de edad. Alimenta las gráficas «Notificaciones por semana»
e «Incidencia notificada por semana», que comparten el mismo archivo.

Contiene **5.952 filas: 992 semanas × seis grupos**. Cada fila representa un grupo
y una semana epidemiológica; la combinación `year`, `week` y `age_group` es única.
El CSV usa UTF-8, coma como separador, punto decimal y campos vacíos para valores
ausentes.

## Origen de los datos

Los enlaces siguientes llevan a los README específicos de data-processing.
Los archivos originales no se publican en ese repositorio debido a su tamaño.

| Dataset utilizado | Información incorporada |
| --- | --- |
| [Sivigila integrado por fecha de notificación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | `sivigila_integrado_notification_semanal_municipal.parquet`: `casos_total`, los cinco conteos por edad y `casos_edad_desconocida`, agrupados nacionalmente por año y semana epidemiológicos. |
| [Población municipal 2007–2025](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | `population_municipal_2007_2025.csv`: población DANE estimada o proyectada de ambos sexos, agregada nacionalmente para cada grupo y año. |

La semana corresponde a la [fecha de notificación (`FEC_NOT`)](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos)
de los registros de varicela, evento 831. El calendario es domingo–sábado y la
semana 1 contiene el 4 de enero. El año epidemiológico puede diferir del año
calendario; no se utiliza aquí la semana reportada originalmente ni la de inicio
de síntomas.

## Diccionario de datos

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `year` | Entero | Año epidemiológico, entre 2007 y 2025; identifica también el año de población utilizado. |
| `week` | Entero | Semana epidemiológica dentro del año, entre 1 y 53. |
| `week_position` | Entero | Posición consecutiva de la semana en la serie, desde 1 hasta 992; se repite para los seis grupos y permite ordenar el eje temporal. |
| `age_group` | Categoría | Código del grupo de edad, según el diccionario siguiente. |
| `notifications` | Entero o ausente | Notificaciones de varicela del grupo y semana. Queda vacío cuando no hay registro nacional para una semana intermedia. |
| `population` | Entero | Población nacional del mismo grupo y año, en personas. El denominador anual se repite en las semanas de ese año. |
| `notification_rate_per_100k` | Número o ausente | Notificaciones de la semana por 100.000 habitantes del grupo, con cuatro decimales. Queda vacío si falta el conteo semanal. |

Los tipos son lógicos: el CSV no almacena tipos físicos.

| `age_group` | Grupo | Conteo de origen | Población de origen |
| --- | --- | --- | --- |
| `all` | Todas las edades | `casos_total`, incluidos los registros sin edad | `poblacion_total` |
| `under_1` | Menores de 1 año | `casos_menor_1` | `poblacion_menor_1` |
| `1_4` | De 1 a 4 años | `casos_1_4` | `poblacion_1_4` |
| `5_14` | De 5 a 14 años | `casos_5_14` | `poblacion_5_14` |
| `15_49` | De 15 a 49 años | `casos_15_49` | `poblacion_15_49` |
| `50_plus` | 50 años o más | `casos_50_mas` | `poblacion_50_mas` |

Los registros sin edad se incluyen en `all`, pero no tienen fila ni línea propia
porque carecen de un denominador poblacional específico. Por ello, la suma de los
cinco grupos puede ser menor que el total de todas las edades.

## Notificaciones por semana

La gráfica utiliza `notifications` y permite comparar uno o varios grupos.
Un cero significa cero notificaciones del grupo en una semana con registros;
un campo vacío indica ausencia de información nacional para esa semana y produce
una interrupción de la línea. En la publicación actual falta la semana 52 de 2008
para los seis grupos; no se imputa cero.

## Incidencia notificada por semana

La gráfica utiliza `notification_rate_per_100k`, con la población anual del grupo
como denominador. Describe las notificaciones de una semana por 100.000 habitantes;
no es una tasa anual ni anualizada. Las tasas semanales redondeadas no se suman
para obtener la tasa anual. Una semana sin conteo tampoco tiene tasa.

## Script generador y alcance

[`scripts/generate_weekly_series.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_weekly_series.py)
genera el CSV desde las dos fuentes. Valida los años, las semanas, las claves
municipales de población y los denominadores positivos; también comprueba que
los cinco conteos por edad más los registros sin edad sumen el total semanal.
Completa los vacíos entre la semana 1 y la última semana registrada de cada año,
conservando los conteos y tasas ausentes. No genera metadatos separados: sus
especificaciones se documentan en este README.

Las cifras describen notificaciones de vigilancia, no todas las infecciones.
2007 se conserva como referencia diagnóstica por su conteo atípicamente bajo
y la discrepancia con la cifra nacional del INS; el análisis principal comienza
en 2008. Las comparaciones temporales no distinguen por sí solas cambios de
transmisión, consulta, acceso a la atención o registro.
