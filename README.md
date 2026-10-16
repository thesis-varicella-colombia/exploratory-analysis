# Análisis espacio-temporal de la varicela en Colombia

Este repositorio contiene la [propuesta de trabajo de grado](diego_rojas_propuesta_trabajo_de_grado.pdf) y los datos consolidados de notificaciones de varicela (evento 831 de Sivigila) en [`data/sivigila_integrado_semanal_municipal.parquet/`](data/sivigila_integrado_semanal_municipal.parquet/).

## Alcance de los datos

Cada fila corresponde a una entidad DIVIPOLA de **residencia** y una combinación de año y semana epidemiológicos **reportados** en Sivigila. La entidad puede ser un municipio, un área no municipalizada o San Andrés (`Isla`). Solo aparecen combinaciones con al menos una notificación: una semana ausente no equivale automáticamente a cero casos.

`casos_total` cuenta registros notificados del evento 831, no personas enfermas deduplicadas ni tasas de incidencia. Los registros con `AJUSTE=6` o `AJUSTE=D` se excluyen en el procesamiento; no se aplica otra deduplicación. Para calcular tasas deben usarse denominadores de población adecuados y documentar la definición de caso.

`inicio_semana` y `fin_semana` interpretan `ANO` y `SEMANA` con la convención de calendario del proyecto (domingo a sábado). El agrupamiento no recalcula la semana a partir de la fecha de notificación ni de inicio de síntomas. Esto importa al cruzar las notificaciones con el clima: la ficha técnica del procesamiento registra discrepancias entre esas fechas y la semana reportada, concentradas en 2007 y 2008. Antes de atribuir una exposición climática semanal a los casos de 2008, se debe revisar esa coherencia temporal.

## Exclusión de 2007

El periodo de análisis actualizado es **2008–2025**. La propuesta original contemplaba 2007–2023; este trabajo incorpora 2024 y 2025. El año 2007 se excluye de los análisis de tasas, comparaciones temporales y modelos estadísticos por una discrepancia importante entre la base consolidada y la cifra oficial disponible:

| Fuente | Notificaciones o casos de varicela en 2007 |
| --- | ---: |
| Base consolidada (`SUM(casos_total)` para `ano_epidemiologico = 2007`) | 26.441 notificaciones |
| [Protocolo de vigilancia de varicela, sección 5.1.2, p. 4](https://minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf) | 69.695 |

La cifra de la base es **43.254 registros menor**, aproximadamente un **62 %** por debajo de la publicada en el protocolo. En 2007 solo aparecen **106 entidades DIVIPOLA de residencia** con notificaciones. La comparación señala una discrepancia importante, pero no establece su causa: podrían influir las fuentes, los cortes, las definiciones o la cobertura de los registros. Las exclusiones documentadas por códigos de residencia no válidos suman 5.780 registros **en todos los años**, por lo que no explican por sí solas la diferencia de 2007.

Se excluye 2007 del periodo analítico para evitar que esa discrepancia distorsione la incidencia y la tendencia anterior a la vacunación. Sus registros permanecen en el parquet para auditar la fuente y el procesamiento. Si se aclara la diferencia, se reevaluará esta decisión.

## Gráficos anuales y vista local

La [página estática](docs/index.html) muestra las notificaciones y tasas anuales nacionales, además de dos gráficos por grupo de edad. El [README de `data/`](data/README.md) documenta las fuentes y los cálculos. Cada CSV publicado tiene su propio script generador.

Desde la raíz del repositorio, con Python 3 y [DuckDB CLI](https://duckdb.org/docs/stable/clients/cli/overview.html) instalados:

```bash
python3 scripts/generate_annual_series.py
python3 scripts/generate_age_group_series.py
python3 -m http.server 8000 --directory docs
```

Abrir `http://localhost:8000/` en el navegador. El servidor local es necesario para cargar el CSV mediante JavaScript; abrir `docs/index.html` directamente como archivo puede bloquear esa carga. Los gráficos usan Vega-Lite desde un CDN, por lo que la vista local necesita conexión a Internet. Para publicar en GitHub Pages, configurar la fuente como rama `main` y carpeta `/docs` después de incorporar los cambios a esa rama.
