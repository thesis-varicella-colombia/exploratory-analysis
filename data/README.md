# Datos de entrada

Esta carpeta guarda **copias locales** de los insumos necesarios para regenerar los datos publicados por este repositorio. Los scripts de `scripts/` no leen rutas de otros repositorios. Los CSV que consume la página se generan en `docs/data_processed/` y se publican con GitHub Pages; los insumos de esta carpeta no forman parte de esa carpeta publicada.

## Procedencia

Ambos insumos proceden de [`thesis-varicella-colombia/data-processing`](https://github.com/thesis-varicella-colombia/data-processing). El Parquet local coincide archivo por archivo con el del repositorio de origen; el CSV de población se copió de allí el 16 de octubre de 2026. En esa fecha, la copia local de origen tenía `HEAD` en `cca6bec23ad449563d569e28ac064fdba6b25a39`. Los archivos de datos no estaban registrados en Git en ese repositorio; por ello el commit **no identifica por sí solo** su contenido. Los SHA-256 de abajo identifican las copias exactas utilizadas aquí.

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

`scripts/generate_annual_series.py` suma `casos_total` por año epidemiológico. Estas son **notificaciones**, no personas enfermas deduplicadas. El script divide ese total entre la suma de `poblacion_total` de **todos** los municipios del CSV anual y multiplica por 100.000. No suma la población integrada del Parquet: esta se repite en cada semana y solo está presente donde hubo notificaciones. La salida se llama *tasa anual de notificación por 100.000 habitantes*; no estima la incidencia clínica real. El CSV de población contiene algunas filas con valor cero: se conservan en la suma y su cantidad se informa por año en `zero_population_entities`.

Para 2007, el [protocolo de vigilancia de varicela, sección 5.1.2, página 4](https://www.minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf) informa **69.695 casos**. Ese valor se conserva como referencia en el script y en el CSV derivado. La base local suma **26.441 notificaciones** y solo registra **106 entidades de residencia** ese año. La diferencia señala una discrepancia de cobertura o definición aún no resuelta; por eso 2007 se muestra como diagnóstico y se excluye de la serie analítica de tasas 2008–2023. Véase también el [README principal](../README.md).

Para regenerar el CSV desde la raíz de este repositorio, con Python 3 y DuckDB CLI instalado:

```bash
python3 scripts/generate_annual_series.py
```

El script produce `docs/data_processed/annual_series_2007_2023.csv` sin leer archivos externos al repositorio.
