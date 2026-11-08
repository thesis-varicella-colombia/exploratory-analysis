# Serie anual de notificaciones de varicela, 2007–2025

## Descripción y archivos

Este conjunto resume las notificaciones de varicela y la población de Colombia
por año epidemiológico. El CSV nacional contiene **19 filas, una por año**,
y alimenta las gráficas «Notificaciones por año» y «Tasa anual de notificación».
El selector territorial dispone además de series para 33 departamentos y
1.122 entidades municipales de la geografía MGN 2025.

- [Serie anual nacional (CSV)](annual_series_2007_2025.csv).
- [Catálogo territorial y reglas (manifest.json)](manifest.json).
- Series JSON: [conjunto nacional](all.json), [ejemplo de departamento: Antioquia](dep_05.json)
  y [ejemplo municipal: Medellín](05001.json). El catálogo identifica las demás
  selecciones; cada archivo se denomina `<id>.json` y contiene `id` y `rows`.
- [Panel municipal de densidad y denominadores](README.md), usado como insumo
  de las agregaciones territoriales.

El CSV usa UTF-8, coma como separador, punto decimal y campos vacíos para datos
ausentes. `year` es su clave única; los códigos del catálogo son texto y conservan
sus ceros iniciales.

## Origen de los datos

Los enlaces siguientes llevan a la documentación específica de cada fuente en
data-processing. Los archivos originales no se publican allí por su tamaño.

| Fuente | Información utilizada |
| --- | --- |
| [Sivigila integrado por fecha de notificación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | Dataset `sivigila_integrado_notification_semanal_municipal.parquet`: `casos_total`, `ano_epidemiologico` y `codigo_municipio`. Notificaciones de varicela (evento 831), por entidad de residencia y semana de `FEC_NOT`. |
| [Población municipal 2007–2025](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | Dataset `population_municipal_2007_2025.csv`: población total DANE estimada o proyectada del año correspondiente. |
| [GeoJSON DANE del MGN 2025](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/municipios#geometr%C3%ADas-geojson-del-mgn-2025) | Códigos, nombres y agrupación geográfica del panel municipal utilizado por el selector; el área no interviene en la tasa anual. |
| [Documento oficial de vigilancia del INS](https://www.minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf) | Referencia nacional de 69.695 casos en 2007, separada del conteo de la base. |

El año epidemiológico de las notificaciones se deriva de `FEC_NOT`, con semanas
domingo–sábado y semana 1 que contiene el 4 de enero; puede diferir del año calendario.

## Diccionario del CSV nacional

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `year` | Entero | Año epidemiológico, entre 2007 y 2025. |
| `notifications` | Entero | Suma anual de notificaciones de la base integrada. |
| `reporting_entities` | Entero | Entidades distintas con algún registro de notificación en el año; no acredita notificación continua. |
| `population_entities` | Entero | Entidades presentes en la fuente de población del año, incluidas las de población cero. |
| `zero_population_entities` | Entero | Entidades cuya población total es cero. |
| `population` | Entero | Suma de la población anual disponible, en personas. |
| `notification_rate_per_100k` | Número | Notificaciones por 100.000 habitantes, publicadas con dos decimales. |
| `official_2007_cases` | Entero o ausente | Referencia oficial de 69.695 casos, únicamente en 2007. |

## Catálogo y series territoriales

`manifest.json` contiene los años, la opción nacional, las listas `departments`
y `municipalities` (con identificador, código y nombre), el orden territorial y
las reglas de fuente, geografía, agregación, ceros y referencia oficial.

Cada fila de `rows` en los JSON territoriales incluye `year`, `notifications`,
`population`, `notification_rate_per_100k`, `reporting_entities`,
`population_entities`, `zero_population_entities` y `official_2007_cases`, con el
sentido descrito arriba. Agrega dos campos:

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `selected_entities` | Entero | Cantidad de entidades que forman la selección. |
| `missing_population_entities` | Entero | Entidades sin población disponible para ese año. |

La serie nacional conserva los valores del CSV. Las demás selecciones suman casos
y población del panel municipal homologado antes de calcular la tasa; no promedian
tasas municipales. Una población total ausente o no positiva produce una tasa nula.
La referencia oficial de 2007 solo se incluye en el conjunto nacional.

## Scripts generadores y alcance

- [`generate_annual_series.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_annual_series.py)
  genera el CSV nacional a partir del integrado de notificaciones y la población.
- [`generate_annual_territorial.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_annual_territorial.py)
  genera el catálogo y los JSON territoriales usando ese CSV y el panel municipal.

Un cero asignado por ausencia de registro no demuestra ausencia de enfermedad.
Las cifras describen notificaciones, no todas las infecciones. El conteo de 2007
es atípicamente bajo (26.294), con una discrepancia no resuelta frente a los 69.695
casos del INS; se conserva como diagnóstico y el análisis principal comienza en 2008.
