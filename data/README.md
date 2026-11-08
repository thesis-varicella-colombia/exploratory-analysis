# Datos de entrada

Esta carpeta guarda **copias locales** de los insumos necesarios para regenerar los datos publicados por este repositorio. Los scripts de `scripts/` no leen rutas de otros repositorios. Los CSV que consume la página se generan en `docs/data_processed/` y se publican con GitHub Pages; los insumos de esta carpeta no forman parte de esa carpeta publicada.

## Procedencia

Los insumos proceden de [`thesis-varicella-colombia/data-processing`](https://github.com/thesis-varicella-colombia/data-processing). El Parquet local coincide archivo por archivo con el del repositorio de origen; el CSV de población se copió de allí el 16 de octubre de 2026. En esa fecha, la copia local de origen tenía `HEAD` en `cca6bec23ad449563d569e28ac064fdba6b25a39`. Los archivos de datos no estaban registrados en Git en ese repositorio; por ello el commit **no identifica por sí solo** su contenido. Los SHA-256 de abajo identifican las copias exactas utilizadas aquí. El GeoJSON MGN 2025 se copió del mismo repositorio a `data/` comprimido con XZ, sin modificar el contenido descomprimido.

Las notificaciones originales proceden de los [microdatos de Sivigila publicados por el Instituto Nacional de Salud (INS)](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx); `data-processing` los convirtió, procesó e integró antes de producir el Parquet usado aquí.

| Insumo local | Ruta y ficha en `data-processing` | Contenido |
| --- | --- | --- |
| [`sivigila_integrado_semanal_municipal.parquet/`](sivigila_integrado_semanal_municipal.parquet/) | `data/processed/integration_data/sivigila_integrado_semanal_municipal.parquet/` · [ficha de integración](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | Notificaciones de varicela (evento 831) por entidad DIVIPOLA de residencia y semana epidemiológica reportada, con variables de población y otras fuentes integradas. |
| [`population_municipal_2007_2025.csv`](population_municipal_2007_2025.csv) | `data/processed/population/population_municipal_2007_2025.csv` · [ficha de población](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | Población municipal anual. Cada clave `codigo_municipio`–`ano_epidemiologico` aparece una vez. |
| [`MGN_ADM_MPIO_GRAFICO.geojson.xz`](MGN_ADM_MPIO_GRAFICO.geojson.xz) | `data/raw/municipios/MGN_ADM_MPIO_GRAFICO.geojson` · [ficha geográfica](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/raw/municipios/README.md) | Geometría DANE MGN 2025 de municipios, áreas no municipalizadas e Isla; copia íntegra comprimida. |

El Parquet integrado contiene además columnas de [cobertura municipal de vacunación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/vaccine_coverage/README.md), [precipitación CHIRPS](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/chirps_precipitation/README.md) y [temperatura, humedad y precipitación ERA5](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/climate/README.md). Estas fichas describen las fuentes originales, la preparación y las limitaciones de las variables integradas.

### Integridad de las copias

| Archivo | SHA-256 |
| --- | --- |
| `sivigila_integrado_semanal_municipal.parquet/part-00000-28a93b17-ad5a-4e7c-aa6c-0f91af7c65d8-c000.snappy.parquet` | `683648606247556885945becbf8b5981f37ab14b6a8bae1f9fb653b5624039ae` |
| `sivigila_integrado_semanal_municipal.parquet/part-00001-28a93b17-ad5a-4e7c-aa6c-0f91af7c65d8-c000.snappy.parquet` | `2e84e5eb0b6c6e84ee43a34de522dec742a9c627ea531d0cd44407dd9cd94fe7` |
| `sivigila_integrado_semanal_municipal.parquet/part-00002-28a93b17-ad5a-4e7c-aa6c-0f91af7c65d8-c000.snappy.parquet` | `84c46566ae14be86c251d4bc2e72c056888a6751e88e8b1e38ff2bdd35d6611d` |
| `population_municipal_2007_2025.csv` | `8b8392c3c9d03f130018ad895fab252ca5fd3bb1c37494c8367e515f3b8343f8` |
| `MGN_ADM_MPIO_GRAFICO.geojson.xz` | `86d527cd493b2a8bc1513dc84dc775a7c52973f75528873dfa64f2b9d3f7b4e6` |

SHA-256 del GeoJSON descomprimido: `e5bce5de037c0b5de0d20ccef291ddc274cfc09f29c509500bb8359bd551d7f7`.

La [documentación de población del repositorio de origen](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) explica cómo se construyó el CSV a partir de las proyecciones municipales. La [documentación del dataset integrado](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) describe las uniones y su unidad de observación.

## Uso en los gráficos anuales

`scripts/generate_annual_series.py` suma `casos_total` por año epidemiológico. Estas son **notificaciones**, no personas enfermas deduplicadas. El script divide ese total entre la suma de `poblacion_total` de **todos** los municipios del CSV anual y multiplica por 100.000. No suma la población integrada del Parquet: esta se repite en cada semana y solo está presente donde hubo notificaciones. La salida se llama *tasa anual de notificación por 100.000 habitantes* y describe lo registrado en la fuente procesada. El CSV de población contiene algunas filas con valor cero: se conservan en la suma y su cantidad se informa por año en `zero_population_entities`.

Para 2007, el [protocolo de vigilancia de varicela, sección 5.1.2, página 4](https://www.minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf) informa **69.695 casos**. Ese valor se conserva como referencia en el script y en el CSV derivado. La variante `notification` suma **26.294 notificaciones** y registra **92 entidades de residencia** ese año. La diferencia señala una discrepancia de cobertura o definición aún no resuelta; por eso 2007 se muestra como diagnóstico y se excluye de la línea de tasas 2008–2025. El periodo actualizado de trabajo es 2008–2025, aunque la propuesta original terminaba en 2023. Véase también el [README principal](../README.md).

Para regenerar el CSV desde la raíz de este repositorio, con Python 3 y DuckDB CLI instalado:

```bash
python3 scripts/generate_annual_series.py
```

El script produce `docs/data_processed/varicela_totales_por_anio/annual_series_2007_2025.csv` sin leer archivos externos al repositorio.

### Filtros nacionales, departamentales y municipales

Las gráficas «Notificaciones por año» y «Tasa anual de notificación» comparten
un buscador con la opción predeterminada «Todos los municipios y departamentos»,
los 32 departamentos y Bogotá D.C., y las 1.122 entidades de la cartografía.
Los departamentos se ordenan de norte a sur y los municipios se agrupan en ese
mismo orden. La búsqueda acepta nombre, código o la opción completa de la lista.

[`generate_annual_territorial.py`](../scripts/generate_annual_territorial.py)
publica un JSON por selección y un [catálogo](../docs/data_processed/varicela_totales_por_anio/manifest.json)
en `varicela_totales_por_anio/`. Reutiliza las notificaciones, poblaciones y banderas de
registro de `population_density_2007_2025.csv`; no usa el área ni la densidad para
estas gráficas. La homologación histórica ya incluye Mapiripana en Barrancominas.
La opción nacional conserva exactamente los valores del CSV anual original,
que permanece sin modificar.

Por departamento se suman notificaciones y población anual disponible y luego
se calcula `100000 × suma de notificaciones / suma de población`. No se promedian
tasas municipales. El detalle conserva cuántas entidades tienen población ausente
o cero; una población total ausente o no positiva deja la tasa sin dato. Se conserva la convención
de asignar cero cuando no hay fila municipal de notificaciones, con su límite:
no demuestra ausencia de enfermedad o vigilancia completa.

El filtro modifica los datos de las mismas dos gráficas, sin recrearlas; descarga
solo la selección solicitada y conserva una caché de hasta 16 series. La vista
ampliada utiliza la selección actual. El marcador oficial de 69.695 casos de 2007
se muestra únicamente para el conjunto nacional, y 2007 continúa como diagnóstico
para todos los territorios. Las conclusiones de las series anuales siguen
identificadas como nacionales. El [README de la serie anual](../docs/data_processed/varicela_totales_por_anio/README_annual_series.md),
enlazado antes de las gráficas de densidad, reúne las fuentes, el diccionario y las
descargas del CSV nacional y del catálogo territorial.

```bash
.venv/bin/python scripts/generate_annual_territorial.py
```

## Serie semanal nacional

`scripts/generate_weekly_series.py` produce `docs/data_processed/weekly_series_2007_2025.csv`. Suma `casos_total` y los cinco conteos por grupo de edad del Parquet para cada año y semana epidemiológicos reportados, entre 2007 y 2025. Cada fila identifica el grupo mediante `age_group`; `all` representa todas las edades e incluye las notificaciones sin edad registrada. No se ofrece `unknown` como grupo seleccionable porque carece de denominador de población.

Cada tasa semanal divide las notificaciones de la semana entre la población anual nacional del grupo correspondiente, tomada del mismo CSV de población utilizado en los gráficos anuales, y multiplica por 100.000. Por tanto, representa notificaciones **de esa semana** por 100.000 habitantes, no una tasa anual ni una tasa anualizada. Las tasas semanales redondeadas no se suman para obtener la tasa anual. El script comprueba que, en cada semana registrada, los cinco grupos y la categoría sin edad sumen el total nacional.

`week_position` ordena las semanas consecutivamente y permite mostrar los años epidemiológicos en el eje horizontal, incluso cuando la fecha de inicio de una semana cae en el año calendario anterior. Si no existe registro nacional para una semana intermedia, el CSV deja vacíos el conteo y la tasa de todos los grupos, y la línea se interrumpe: no se imputa cero. Esto ocurre en la semana 51 de 2008. Si hay registros en una semana pero un grupo de edad no registra casos, su conteo es cero. El tramo de 2007 se presenta como referencia diagnóstica por la discrepancia descrita arriba.

```bash
python3 scripts/generate_weekly_series.py
```

## Serie por grupo de edad

`scripts/generate_age_group_series.py` produce `docs/data_processed/age_group_series_2007_2025.csv`. Para cada año suma las notificaciones de los cinco grupos de edad disponibles en el Parquet: menor de 1, 1–4, 5–14, 15–49 y 50 años o más. Las notificaciones con edad desconocida se incluyen en el CSV y la tabla como `unknown`, pero no forman una línea; no se les calcula una tasa porque no existe un denominador de población para esa categoría. En 2008 hay 1.183 notificaciones sin edad registrada; el script comprueba que los cinco grupos y esa categoría sumen el total anual.

La tasa de cada grupo divide sus notificaciones anuales entre la suma de la población municipal anual de ese mismo grupo y multiplica por 100.000. La fuente y la convención son las mismas que para la serie nacional. Los gráficos por edad incluyen 2007 como referencia diagnóstica, aunque el total de ese año en la base integrada está cuestionado; el periodo analítico principal sigue siendo 2008–2025.

```bash
python3 scripts/generate_age_group_series.py
```

## Mapa municipal

`scripts/generate_spatial_series.py` produce `docs/data_processed/spatial_series_2008_2025.csv` para los años 2008–2025 y cuatro periodos: 2008–2014, 2015–2019, 2020–2021 y 2022–2025. Suma `casos_total` del Parquet por municipio y año y usa la población municipal del CSV local una sola vez por año. Cuando no hay filas de notificaciones para un municipio-año con población, registra cero notificaciones; esto describe la base y no prueba ausencia de enfermedad. Si falta población, la tasa queda vacía.

La tasa anual es `notificaciones / población anual × 100.000`. La tasa de cada periodo es `suma de notificaciones / suma de poblaciones anuales × 100.000`: una tasa promedio anual ponderada por población, comparable entre periodos de distinta duración. Si un municipio no tiene población en todos los años de un periodo, el denominador incluye solo los años disponibles; la columna `years` indica cuántos son.

El mapa usa `docs/data_processed/municipal_boundaries_dane.geojson`, generado desde la copia comprimida en `data/`. El [GeoJSON MGN 2025 del DANE](https://geoportal.dane.gov.co/mparcgis/rest/services/MGN2025/Serv_CapasMGN_2025/FeatureServer/317) se simplifica para la web conservando código DIVIPOLA, nombre, departamento y tipo de unidad. Contiene 1.122 polígonos: 1.103 municipios, 18 áreas no municipalizadas y una Isla. Todos sus códigos están en el CSV de población de 2025. El código histórico `94663` (Mapiripana) no tiene polígono separado en esta geometría de 2025; el mapa usa los límites de 2025 para todos los años, por lo que los cambios territoriales históricos no se representan.

```bash
python3 scripts/generate_spatial_series.py
python3 scripts/prepare_spatial_boundaries.py
```

## Mapa de calor de latitud y semana

`scripts/generate_latitude_week_heatmap.py` produce `docs/data_processed/latitude_week_heatmap.csv` para 2008–2014, 2016–2019 y 2022–2025. Agrupa las notificaciones semanales del Parquet por prefijo DIVIPOLA departamental y las divide entre la población anual departamental del CSV local. Si una semana tiene registros nacionales pero no filas de un departamento, asigna cero notificaciones a ese departamento; si no hay registros nacionales, omite ese año en la media de esa semana. Excluye las semanas 53.

Para cada periodo, departamento y semana calcula la media de las tasas de los años disponibles. La anomalía Z resta a esa tasa la media de las 52 tasas semanales del departamento y la divide entre su desviación estándar poblacional entre semanas. El CSV incluye ambas magnitudes y el número de años utilizados. La latitud procede del centroide de las geometrías MGN 2025 simplificadas, ponderado por área tras proyectarlas a EPSG:6933. El mapa muestra 31 departamentos continentales y Bogotá D.C.; excluye el archipiélago de San Andrés y Providencia para mantener el gradiente continental de Amazonas a La Guajira.

Desde la raíz, con `shapely`, `pyproj` y DuckDB CLI instalados:

```bash
python3 scripts/generate_latitude_week_heatmap.py
```

## Casos e incidencia frente a densidad poblacional

[`generate_population_density.py`](../scripts/generate_population_density.py)
produce el panel y sus metadatos en `docs/data_processed/varicela_totales_por_anio/`.
El [README del conjunto](../docs/data_processed/varicela_totales_por_anio/README.md)
reúne las descargas, fuentes, esquema, diccionario y reglas de cálculo.
Extrae directamente `mpio_narea`, en km², del GeoJSON original comprimido en
`data/MGN_ADM_MPIO_GRAFICO.geojson.xz`; no calcula áreas desde las coordenadas
ni usa `shape_Area`. La estructura del atributo está descrita en el
[manual del MGN del DANE](https://geoportal.dane.gov.co/descargas/mgn_2023/MGN2023_ManualDeUso.pdf).
Para cada entidad y año calcula:

- Densidad: población total de ese año / área en km².
- Incidencia notificada: 100.000 × casos de ese año / población total de ese año.

La población procede de `population_municipal_2007_2025.csv` y los casos del
Parquet por fecha de notificación. Se usan los 1.122 códigos de la geografía MGN
2025, incluyendo áreas no municipalizadas y San Andrés. Los códigos históricos
se homologan y sus poblaciones se suman antes de calcular las razones. El área
es fija en todos los años; no se reconstruyen límites históricos. Una entidad
sin fila de notificaciones se considera cero solo si existe información nacional
en ese año; el CSV retiene si había registro. Una población o área ausente o no
positiva impide representar la entidad. Los casos anuales agregados coinciden
con los totales publicados en la sección anual.

Las dos dispersiones aparecen antes de las conclusiones anuales. Comparten
selector, barra de año y animación 0,5×, 1× y 2×, actualizando solo los datos de
las vistas existentes. La animación recorre 2008–2025; 2007 se puede seleccionar
manualmente como diagnóstico. Se pausa al cambiar manualmente el año y al
ocultar la pestaña. El eje horizontal es logarítmico y el vertical usa raíz
cuadrada para conservar ceros y distinguir magnitudes. Los dominios de ambos
ejes permanecen fijos entre años, calculados sobre el panel completo; los valores mostrados
siguen siendo densidades, casos e incidencias originales. No hay agregación o
muestreo de puntos: cada entidad válida aparece una vez por año. La relación
es descriptiva, con población compartida entre los cálculos de densidad e
incidencia, y no estima un efecto causal ni hacinamiento.

```bash
.venv/bin/python scripts/generate_population_density.py
```


### Resúmenes auxiliares de densidad conservados fuera del tablero

[`analyze_population_density.py`](../scripts/analyze_population_density.py)
produce [`population_density_summary_2008_2025.csv`](../docs/data_processed/varicela_totales_por_anio/population_density_summary_2008_2025.csv)
y sus [metadatos](../docs/data_processed/varicela_totales_por_anio/population_density_summary_2008_2025.metadata.json).
Se conservan como análisis auxiliar reproducible; el 2 de noviembre de 2026 se
retiró el bloque «Respaldo numérico y comparación entre grupos» del tablero para
limitar la profundización de una variable con aporte descriptivo adicional limitado.
La página mantiene las dos gráficas animadas y sus conclusiones para 2008–2025,
con la advertencia sobre falacia ecológica. Ya no carga el CSV de resúmenes ni
presenta sus tablas. Los resúmenes auxiliares contienen 810 filas con los mismos
puntos válidos y ceros de las dispersiones y distinguen la mediana municipal de
la incidencia agrupada.

Los grupos predefinidos son departamento (norte a sur), población total
(<10.000, 10.000–<50.000, 50.000–<100.000, ≥100.000), proporción de menores de 15
(<20 %, 20–<30 %, ≥30 %) y densidad (<10, 10–<100, 100–<1.000, ≥1.000 hab/km²).
La proporción de menores de 15 suma los grupos <1, 1–4 y 5–14 de la población
anual, tras la misma homologación de códigos. Si falta alguna edad, la entidad
queda fuera del estrato etario, pero permanece en las otras comparaciones;
la tabla documenta cuántas tienen composición etaria disponible.

La mediana da el mismo peso a cada entidad y la tasa agrupada se calcula como
`100000 × suma(casos) / suma(población)` del grupo. Q1–Q3 es dispersión municipal,
no un intervalo de confianza. Spearman no se calcula con menos de cinco entidades
ni si falta variación; el mínimo de cinco es operativo y no garantiza precisión.
La estratificación no estandariza por edad ni estima efectos ajustados. No se
publican valores p ni se tratan años o territorios como réplicas independientes.
El año 2007 sigue disponible en las gráficas como diagnóstico, pero no entra
en estos resúmenes. Los CSV incluyen conteos, denominadores, disponibilidad del
registro de notificación y motivos de correlación no estimable.

```bash
.venv/bin/python scripts/analyze_population_density.py
```
