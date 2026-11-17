# Incidencia notificada de varicela por municipio

El mapa usa [`spatial_series_2008_2025.csv`](spatial_series_2008_2025.csv), generado por [`scripts/generate_spatial_series.py`](../../../scripts/generate_spatial_series.py). Cada fila corresponde a una entidad municipal y un año epidemiológico de 2008–2025 o uno de los cuatro períodos: 2008–2014, 2015–2019, 2020–2021 y 2022–2025.

## Fuentes y medida

Las notificaciones proceden de los microdatos de varicela (evento 831) de [Sivigila, INS](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx), procesados en la [base integrada semanal municipal](../../../data/README.md). Se agrupan por municipio de residencia y año epidemiológico de la **fecha de notificación**. Los denominadores son las poblaciones municipales anuales de la [fuente procesada de población](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md). El mapa describe notificaciones registradas, no todos los casos ocurridos.

La tasa anual es `notificaciones / población anual × 100.000`. Para cada período se suman las notificaciones y las poblaciones anuales y se calcula `suma de notificaciones / suma de poblaciones anuales × 100.000`. Por tanto, la tasa del período es un promedio anual ponderado por población y puede compararse entre períodos de distinta duración. El año 2007 se excluye por la discrepancia documentada en la serie de notificaciones.

## Cobertura y visualización

Se usa la [cartografía MGN 2025 del DANE](https://geoportal.dane.gov.co/mparcgis/rest/services/MGN2025/Serv_CapasMGN_2025/FeatureServer/317) para todos los años. Incluye 1.103 municipios, 18 áreas no municipalizadas y la Isla de San Andrés. Una entidad sin denominador válido se muestra en gris. El valor cero indica que la base no contiene notificaciones para esa entidad y año; no demuestra ausencia de enfermedad.

La geografía se mantiene fija para comparar años. La población histórica de Mapiripana (94663) se incorpora al denominador de Barrancominas (94343), pues Mapiripana fue un área no municipalizada y no un municipio independiente. La escala de colores también permanece fija durante la exploración.

## Columnas del CSV

| Columna | Descripción |
| --- | --- |
| `period` | Año o período mostrado. |
| `code` | Código territorial de cinco dígitos. |
| `notifications` | Notificaciones acumuladas en el año o período. |
| `population_years` | Población anual o suma de poblaciones anuales del período. |
| `years` | Número de años incluidos en la fila. |
| `rate_per_100k` | Tasa anual o promedio anual del período por 100.000 habitantes; vacía si no hay denominador válido. |
