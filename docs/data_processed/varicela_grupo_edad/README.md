# Series anuales de varicela por grupo de edad

## Descripción del dataset

[`age_group_series_2007_2025.csv`](age_group_series_2007_2025.csv) reúne la población,
las notificaciones de varicela y la tasa de notificación por grupo de edad en
Colombia entre 2007 y 2025. Alimenta las tres gráficas de la sección «Varicela por
grupo de edad»; cada una consulta variables del mismo archivo.

Contiene **114 filas: 19 años × seis categorías** (cinco grupos de edad y una
categoría sin edad registrada). Cada fila representa un grupo y un año
epidemiológico; la combinación `year` y `age_group` es única. La población y las
tasas están vacías en la categoría `unknown` porque no tiene un denominador propio.
El CSV usa UTF-8, coma como separador y punto decimal.

## Origen de los datos

Estos enlaces llevan a los README específicos de data-processing. Los archivos
originales no se publican en ese repositorio debido a su tamaño.

| Dataset utilizado | Información incorporada |
| --- | --- |
| [Sivigila integrado por fecha de notificación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | `sivigila_integrado_notification_semanal_municipal.parquet`: notificaciones de varicela (evento 831) por entidad de residencia y semana de `FEC_NOT`. Se suman las columnas de casos por edad y `casos_edad_desconocida` para cada año epidemiológico. |
| [Población municipal 2007–2025](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | `population_municipal_2007_2025.csv`: población DANE estimada o proyectada, de ambos sexos, agregada nacionalmente por grupo de edad y año. |

El año epidemiológico de las notificaciones se deriva de `FEC_NOT`, con semanas
domingo–sábado y semana 1 que contiene el 4 de enero. Puede diferir del año calendario.

## Diccionario de datos

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `year` | Entero | Año epidemiológico de las notificaciones, entre 2007 y 2025; identifica también el año de población utilizado. |
| `age_group` | Categoría | Código del grupo de edad, según el diccionario siguiente. |
| `notifications` | Entero | Total nacional de notificaciones de varicela del grupo y año. Un cero representa cero notificaciones en esta fuente, no necesariamente ausencia de enfermedad. |
| `population` | Entero o ausente | Población nacional del mismo grupo y año, en personas; ausente para `unknown`. |
| `notification_rate_per_100k` | Número o ausente | Notificaciones por 100.000 habitantes del mismo grupo y año, con dos decimales; ausente para `unknown`. |

Los tipos son lógicos: el CSV no almacena tipos físicos. Los valores ausentes
se representan mediante campos vacíos.

| `age_group` | Grupo | Columna de casos en el integrado | Columna de población de origen |
| --- | --- | --- | --- |
| `under_1` | Menores de 1 año | `casos_menor_1` | `poblacion_menor_1` |
| `1_4` | De 1 a 4 años | `casos_1_4` | `poblacion_1_4` |
| `5_14` | De 5 a 14 años | `casos_5_14` | `poblacion_5_14` |
| `15_49` | De 15 a 49 años | `casos_15_49` | `poblacion_15_49` |
| `50_plus` | 50 años o más | `casos_50_mas` | `poblacion_50_mas` |
| `unknown` | Sin edad registrada | `casos_edad_desconocida` | No corresponde |

## Población anual por grupo de edad y total

La gráfica usa `year`, `age_group` y `population`. Las cinco líneas por edad
muestran habitantes, no casos. La línea «Todas las edades» suma las poblaciones
de los cinco grupos en el navegador; no es una fila adicional del CSV y excluye
`unknown`, que no tiene población propia.

La población procede de dos series DANE: 2005–2017 y 2018–2042. El cambio de
serie puede producir discontinuidades; por ejemplo, la población de 5–14 años
pasa de 7,78 millones en 2017 a 8,35 millones en 2018.

## Casos notificados por grupo de edad

La gráfica usa `year`, `age_group` y `notifications` para los cinco grupos con
edad conocida. `unknown` se conserva en el CSV y se informa en la nota de la
sección, pero no forma una línea. Los seis conteos juntos coinciden con el total
anual de notificaciones; omitir `unknown` de las líneas no elimina esos registros
del archivo.

## Incidencia notificada por grupo de edad

La gráfica usa `year`, `age_group` y `notification_rate_per_100k`. Cada tasa
relaciona las notificaciones con la población del mismo grupo y año; no compara
solo conteos absolutos. `unknown` no tiene tasa. Los cambios poblacionales, incluida
la discontinuidad entre series DANE, pueden influir en la evolución de las tasas.

## Script generador y alcance

[`scripts/generate_age_group_series.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_age_group_series.py)
genera el CSV a partir de las dos fuentes. Valida los años, las claves municipales
de población, los denominadores positivos y que los cinco grupos más `unknown`
sumen las notificaciones totales. No genera un archivo de metadatos separado;
las especificaciones se documentan en este README.

Las cifras describen notificaciones de vigilancia, no todas las infecciones.
**2007 se conserva como referencia diagnóstica** por el conteo atípicamente bajo
de la base y su discrepancia con la cifra nacional del INS; el análisis principal
comienza en 2008. La comparación descriptiva entre años no identifica por sí sola
efectos causales de vacunación u otros factores.
