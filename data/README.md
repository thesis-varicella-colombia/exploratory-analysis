# Datos de entrada

Esta carpeta guarda **copias locales** de los insumos necesarios para regenerar los datos publicados por este repositorio. Los scripts de `scripts/` no leen rutas de otros repositorios. Los CSV que consume la página se generan en `docs/data_processed/` y se publican con GitHub Pages; los insumos de esta carpeta no forman parte de esa carpeta publicada.

## Procedencia

Ambos insumos proceden de [`thesis-varicella-colombia/data-processing`](https://github.com/thesis-varicella-colombia/data-processing). El Parquet local coincide archivo por archivo con el del repositorio de origen; el CSV de población se copió de allí el 16 de octubre de 2026. En esa fecha, la copia local de origen tenía `HEAD` en `cca6bec23ad449563d569e28ac064fdba6b25a39`. Los archivos de datos no estaban registrados en Git en ese repositorio; por ello el commit **no identifica por sí solo** su contenido. Los SHA-256 de abajo identifican las copias exactas utilizadas aquí.

Las notificaciones originales proceden de los [microdatos de Sivigila publicados por el Instituto Nacional de Salud (INS)](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx); `data-processing` los convirtió, procesó e integró antes de producir el Parquet usado aquí.

| Insumo local | Ruta en `data-processing` | Contenido |
| --- | --- | --- |
| `sivigila_integrado_semanal_municipal.parquet/` | `data/processed/integration_data/sivigila_integrado_semanal_municipal.parquet/` | Notificaciones de varicela (evento 831) por entidad DIVIPOLA de residencia y semana epidemiológica reportada, con variables de población y otras fuentes integradas. |
| `population_municipal_2007_2025.csv` | `data/processed/population/population_municipal_2007_2025.csv` | Población municipal anual. Cada clave `codigo_municipio`–`ano_epidemiologico` aparece una vez. |

### Integridad de las copias

| Archivo | SHA-256 |
| --- | --- |
| `sivigila_integrado_semanal_municipal.parquet/part-00000-28a93b17-ad5a-4e7c-aa6c-0f91af7c65d8-c000.snappy.parquet` | `683648606247556885945becbf8b5981f37ab14b6a8bae1f9fb653b5624039ae` |
| `sivigila_integrado_semanal_municipal.parquet/part-00001-28a93b17-ad5a-4e7c-aa6c-0f91af7c65d8-c000.snappy.parquet` | `2e84e5eb0b6c6e84ee43a34de522dec742a9c627ea531d0cd44407dd9cd94fe7` |
| `sivigila_integrado_semanal_municipal.parquet/part-00002-28a93b17-ad5a-4e7c-aa6c-0f91af7c65d8-c000.snappy.parquet` | `84c46566ae14be86c251d4bc2e72c056888a6751e88e8b1e38ff2bdd35d6611d` |
| `population_municipal_2007_2025.csv` | `8b8392c3c9d03f130018ad895fab252ca5fd3bb1c37494c8367e515f3b8343f8` |

La [documentación de población del repositorio de origen](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) explica cómo se construyó el CSV a partir de las proyecciones municipales. La [documentación del dataset integrado](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) describe las uniones y su unidad de observación.

## Uso en los gráficos anuales

`scripts/generate_annual_series.py` suma `casos_total` por año epidemiológico. Estas son **notificaciones**, no personas enfermas deduplicadas. El script divide ese total entre la suma de `poblacion_total` de **todos** los municipios del CSV anual y multiplica por 100.000. No suma la población integrada del Parquet: esta se repite en cada semana y solo está presente donde hubo notificaciones. La salida se llama *tasa anual de notificación por 100.000 habitantes* y describe lo registrado en la fuente procesada. El CSV de población contiene algunas filas con valor cero: se conservan en la suma y su cantidad se informa por año en `zero_population_entities`.

Para 2007, el [protocolo de vigilancia de varicela, sección 5.1.2, página 4](https://www.minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf) informa **69.695 casos**. Ese valor se conserva como referencia en el script y en el CSV derivado. La base local suma **26.441 notificaciones** y solo registra **106 entidades de residencia** ese año. La diferencia señala una discrepancia de cobertura o definición aún no resuelta; por eso 2007 se muestra como diagnóstico y se excluye de la línea de tasas 2008–2025. El periodo actualizado de trabajo es 2008–2025, aunque la propuesta original terminaba en 2023. Véase también el [README principal](../README.md).

Para regenerar el CSV desde la raíz de este repositorio, con Python 3 y DuckDB CLI instalado:

```bash
python3 scripts/generate_annual_series.py
```

El script produce `docs/data_processed/annual_series_2007_2025.csv` sin leer archivos externos al repositorio.

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
