# Densidad y notificaciones municipales

## Archivos

- [Datos del panel (CSV)](population_density_2007_2025.csv).
- [Metadatos del cálculo (JSON)](population_density_2007_2025.metadata.json).

## Descripción del dataset

`population_density_2007_2025.csv` es un panel anual que reúne las notificaciones
de varicela, la población y el área de cada entidad municipal de Colombia, junto
con su densidad poblacional y tasa de notificación. Permite comparar los conteos
y tasas según la densidad, y distinguir la presencia de registros de los ceros
asignados al completar el panel.

Contiene **21.318 filas: 1.122 entidades × 19 años (2007–2025)**. Cada fila representa
una entidad y un año epidemiológico; la combinación `year` y `code` es única.
Incluye 1.103 municipios, 18 áreas no municipalizadas y la Isla de San Andrés,
según la geografía MGN 2025. El CSV usa UTF-8, coma como separador, punto decimal
y campos vacíos para datos ausentes. Los códigos municipales deben leerse como texto.

## Origen de los datos

Los enlaces llevan a los README de las fuentes. Los archivos de datos originales
no se incluyen en el repositorio data-processing debido a su tamaño.

| Dataset utilizado | Información incorporada |
| --- | --- |
| [Sivigila integrado por fecha de notificación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | `casos_total`, agrupado por entidad de residencia y año epidemiológico. Corresponde a notificaciones de varicela, evento 831, cuya semana se define a partir de `FEC_NOT`. |
| [Población municipal 2007–2025](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | `poblacion_total`: población DANE estimada o proyectada de ambos sexos y todas las edades, para la entidad y el año correspondientes. |
| [GeoJSON DANE del MGN 2025](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/municipios#geometr%C3%ADas-geojson-del-mgn-2025) | Área municipal en km² (`mpio_narea`), código, nombre, departamento y tipo de entidad. Se conserva esa misma área en todos los años. |

## Diccionario de datos

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `year` | Entero | Año epidemiológico de la notificación, entre 2007 y 2025; puede diferir del año calendario. |
| `code` | Texto | Código de cinco dígitos de la entidad, homologado a la geografía MGN 2025. Conserva ceros iniciales. |
| `name` | Texto | Nombre de la entidad según el GeoJSON DANE. |
| `department` | Texto | Nombre del departamento al que pertenece la entidad. |
| `kind` | Categoría | Tipo de entidad: `MUNICIPIO`, `ÁREA NO MUNICIPALIZADA` o `ISLA`. |
| `area_km2` | Número | Área de la entidad en km², tomada de `mpio_narea`; no se recalcula desde las coordenadas. |
| `population` | Número | Población total del año, en personas, después de homologar los códigos históricos. |
| `cases` | Conteo numérico | Total anual de notificaciones de varicela. Puede ser cero por ausencia de registro; consultar `notification_record_present`. |
| `notification_record_present` | Booleano | `True` si existe un agregado de notificaciones para la entidad y el año; `False` si la fila se completó sin registro y se asignaron cero casos. |
| `density_per_km2` | Número | Densidad poblacional en habitantes/km²: población dividida entre área. |
| `incidence_per_100k` | Número | Tasa de notificación por 100.000 habitantes: 100.000 × casos / población. |
| `status` | Categoría | Disponibilidad de los datos para representar la entidad; valores descritos a continuación. |

Los tipos son lógicos: el CSV no almacena tipos físicos. `status` puede tomar
los siguientes valores, en orden de prioridad cuando coincide más de una causa:

- `missing_or_invalid_area`: área ausente, no finita o no positiva.
- `missing_or_nonpositive_population`: población ausente, no finita o no positiva.
- `missing_cases`: conteo ausente, con área y población válidas.
- `available`: área y población válidas y conteo disponible; no acredita vigilancia completa.

## Script generador

El CSV y su JSON de metadatos se generan con
[`scripts/generate_population_density.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_population_density.py).
Este script reúne las tres fuentes, homologa códigos históricos, completa el
panel entidad-año y calcula los indicadores. Las reglas compartidas de homologación
están en [`scripts/municipal_coverage.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/municipal_coverage.py).

El [JSON de metadatos](population_density_2007_2025.metadata.json) registra las
fuentes de área y población, fórmulas, códigos homologados y resumen anual.

## Cómo interpretarlo

Sin registro se asigna cero, lo que **no demuestra ausencia de enfermedad**.
Sin población positiva no se calculan las razones; sin área válida no se calcula
densidad. Los valores ausentes quedan vacíos en el CSV.

La densidad no mide hacinamiento ni demuestra causalidad. Se conserva la geografía
de 2025 para toda la serie. **2007 es solo diagnóstico:** registra 26.294 notificaciones
frente a los 69.695 casos informados por el INS; el análisis principal comienza en 2008.

Las [notas técnicas](TECHNICAL.md) conservan las validaciones e instrucciones de reproducción.
