# Análisis espacio-temporal de la varicela en Colombia

> **Trabajo en desarrollo.** Esta página y sus análisis se están construyendo. Aún faltan contenidos por incorporar, y los resultados, gráficos y textos pueden cambiar a medida que avance el proyecto.

## Ver la página publicada

**Abrir los gráficos en línea:** [https://thesis-varicella-colombia.github.io/exploratory-analysis/](https://thesis-varicella-colombia.github.io/exploratory-analysis/)

La página se puede consultar directamente en el navegador. No hace falta descargar el repositorio ni instalar Python o DuckDB para verla.

Este repositorio contiene datos consolidados de notificaciones de varicela (evento 831 de Sivigila) en [`data/sivigila_integrado_semanal_municipal.parquet/`](data/sivigila_integrado_semanal_municipal.parquet/) y una página para explorarlos.

## Procedencia de los datos

Los tres insumos locales se copiaron de [`data-processing`](https://github.com/thesis-varicella-colombia/data-processing). Sus archivos de datos no están publicados allí en Git; estos enlaces llevan a las fichas técnicas que documentan cómo se obtuvieron y procesaron:

| Copia en este repositorio | Documentación en `data-processing` |
| --- | --- |
| [Notificaciones y variables integradas de varicela](data/sivigila_integrado_semanal_municipal.parquet/) | [Integración semanal municipal](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) |
| [Población municipal anual](data/population_municipal_2007_2025.csv) | [Proyecciones municipales procesadas](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) |
| [GeoJSON municipal MGN 2025, comprimido](data/MGN_ADM_MPIO_GRAFICO.geojson.xz) | [Fuente geográfica y descarga](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/raw/municipios/README.md) |

El [README de datos](data/README.md) registra las rutas de origen, las sumas SHA-256 y el uso de cada insumo. El conjunto integrado también incorpora [cobertura de vacunación](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/vaccine_coverage/README.md) y [variables climáticas](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/climate/README.md).

## Alcance de los datos

Cada fila corresponde a una entidad DIVIPOLA de **residencia** y una combinación de año y semana epidemiológicos **reportados** en Sivigila. La entidad puede ser un municipio, un área no municipalizada o San Andrés (`Isla`). Solo aparecen combinaciones con al menos una notificación: una semana ausente no equivale automáticamente a cero casos.

`casos_total` cuenta registros notificados del evento 831, no personas enfermas deduplicadas ni tasas de incidencia. Los registros con `AJUSTE=6` o `AJUSTE=D` se excluyen en el procesamiento; no se aplica otra deduplicación. Para calcular tasas deben usarse denominadores de población adecuados y documentar la definición de caso.

`inicio_semana` y `fin_semana` interpretan `ANO` y `SEMANA` con la convención de calendario del proyecto (domingo a sábado). El agrupamiento no recalcula la semana a partir de la fecha de notificación ni de inicio de síntomas. Esto importa al cruzar las notificaciones con el clima: la ficha técnica del procesamiento registra discrepancias entre esas fechas y la semana reportada, concentradas en 2007 y 2008. Antes de atribuir una exposición climática semanal a los casos de 2008, se debe revisar esa coherencia temporal.

## Exclusión de 2007

El periodo de análisis es **2008–2025**. El año 2007 aparece en los gráficos para diagnosticar una discrepancia importante entre la base consolidada y la cifra oficial disponible, pero se excluye de las conclusiones de tendencia y los modelos estadísticos:

| Fuente | Notificaciones o casos de varicela en 2007 |
| --- | ---: |
| Base consolidada (`SUM(casos_total)` para `ano_epidemiologico = 2007`) | 26.441 notificaciones |
| [Protocolo de vigilancia de varicela, sección 5.1.2, p. 4](https://minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf) | 69.695 |

La cifra de la base es **43.254 registros menor**, aproximadamente un **62 %** por debajo de la publicada en el protocolo. En 2007 solo aparecen **106 entidades DIVIPOLA de residencia** con notificaciones. La comparación señala una discrepancia importante, pero no establece su causa: podrían influir las fuentes, los cortes, las definiciones o la cobertura de los registros. Las exclusiones documentadas por códigos de residencia no válidos suman 5.780 registros **en todos los años**, por lo que no explican por sí solas la diferencia de 2007.

Se excluye 2007 del periodo analítico principal para evitar que esa discrepancia distorsione las conclusiones sobre incidencia y tendencia anterior a la vacunación. Sus registros permanecen en el parquet y se muestran en los gráficos para auditar la fuente y el procesamiento. Si se aclara la diferencia, se reevaluará esta decisión.

## Cuadernos de Rₜ nacional

La página muestra dos series de **Rₜ estimado cada día** a partir de los registros individuales:
primero por fecha de notificación `FEC_NOT` y después por inicio de síntomas `INI_SIN`.
El método de la primera, sus supuestos y sus análisis de sensibilidad se explican en
[`notebooks/05_rt_nacional_diario.ipynb`](notebooks/05_rt_nacional_diario.ipynb). Los 19 CSV de entrada están
copiados localmente en `data/sivigila/csv/`; por su tamaño, esa carpeta se excluye de Git. El cálculo se
regenera con `python scripts/rt_daily_sivigila.py` y publica
[`docs/data_processed/numero_reproductivo/rt_national_daily.csv`](docs/data_processed/numero_reproductivo/rt_national_daily.csv). La semana
2008-S52 queda sin dato y se exige historia suficiente para cubrir al menos el 99 % del peso serial en
cada día de una ventana publicada.

El [cuaderno paralelo por inicio de síntomas](notebooks/06_rt_nacional_inicio_sintomas.ipynb)
usa `INI_SIN` de los mismos registros individuales y publica
[`rt_national_symptom_daily.csv`](docs/data_processed/numero_reproductivo/rt_national_symptom_daily.csv).
Reproduce los filtros y la posterior del análisis diario, interpreta el formato excepcional
de 2013 y reconcilia los conteos con el Parquet agregado por síntomas. Su auditoría encuentra
20 semanas sin dato, 18 de ellas en 2013; solo el 40,5 % de los registros elegibles del archivo
de 2013 tienen fecha de inicio interpretable. Por ello, las estimaciones de ese tramo se presentan
con un diagnóstico específico de calidad y no como evidencia aislada de transmisión extrema.

Los filtros compartidos de ambas gráficas ofrecen Rₜ nacional y por departamento o municipio
de residencia, siempre para todas las edades. El filtro por edad se retiró: el estimador univariado
no representa la transmisión entre grupos etarios. Las comparaciones por edad permanecen en
las series de casos e incidencia. Los artefactos anteriores por edad se conservan para trazabilidad. [`scripts/generate_rt_stratified.py`](scripts/generate_rt_stratified.py)
recalcula ambas fechas para seis categorías de edad (incluida edad desconocida), 32 departamentos y
Bogotá D.C., y 1.122 entidades municipales DIVIPOLA. Se ejecuta después de los dos scripts diarios
nacionales con `python scripts/generate_rt_stratified.py`. Los archivos comprimidos se cargan por selección
para evitar descargar todas las series; su formato y reglas están en
[`docs/data_processed/numero_reproductivo/rt_stratified/README.md`](docs/data_processed/numero_reproductivo/rt_stratified/README.md).
La página utiliza la versión de visualización generada por
[`scripts/reduce_rt_visualization.py`](scripts/reduce_rt_visualization.py), un paso separado que
resume bloques de hasta siete días con medias adaptativas y un límite de error visual de 0,75 píxeles
en la vista general. Conserva extremos, cruces de Rₜ = 1, huecos y el detalle diario de 2013–2014.
No cambia los originales ni estima nuevas posteriores; la banda resumida aproxima los límites diarios.
El formato, los parámetros y la trazabilidad están en
[`rt_visualization/README.md`](docs/data_processed/numero_reproductivo/rt_visualization/README.md).

La generación reconcilia las dos particiones con los conteos nacionales diarios y las edades por
notificación con la serie semanal publicada. Las ventanas sin exposición calculable no publican Rₜ;
los ceros locales se asignan solo dentro de semanas nacionales observadas.

[`notebooks/02_rt_nacional.ipynb`](notebooks/02_rt_nacional.ipynb) explica paso a paso la estimación exploratoria
semanal de Rₜ a partir de las notificaciones nacionales de 2008–2025: intervalo serial Gamma desplazado
discretizado por día, reconstrucción diaria desde conteos semanales, posterior Poisson–Gamma, intervalos
creíbles y sensibilidad a los parámetros supuestos.
En concordancia con el protocolo de auditoría de datos del proyecto, la semana 52 de 2008 se conserva
sin dato: no se imputan notificaciones. La serie publicada se regenera con
`python scripts/generate_rt_national.py` en `docs/data_processed/numero_reproductivo/rt_national_weekly.csv` y sirve como
comparación metodológica con la serie diaria mostrada en la página. Requiere `scipy` además de las dependencias del notebook anterior.

El [cuaderno comparativo de las tres rutas](notebooks/07_comparacion_rt_tres_series.ipynb)
alinea las estimaciones en cierres semanales comunes, compara las dos series diarias por fecha y
recalcula superposición de posteriores, pérdida predictiva y acuerdo de regímenes para los
escenarios de sensibilidad. Distingue el efecto de los faltantes de `INI_SIN` en 2013 de las
diferencias observadas entre métodos.

El [cuaderno de áreas de Rₜ por períodos](notebooks/08_areas_rt_inicio_sintomas.ipynb)
descompone la ruta diaria de `INI_SIN` en impulso por encima de 1, área por debajo de 1,
balances lineal y logarítmico y diagnóstico anual. Propaga incertidumbre con 4.000
extracciones de las posteriores Gamma diarias y excluye el tramo de calidad deficiente
de 2013–primer trimestre de 2014 de la comparación principal.

Este Rₜ describe un modelo de las **notificaciones por semana de la fecha de notificación**; no es una estimación causal de la
vacunación ni una medida directa del número de infecciones secundarias. La previa Gamma de forma 1 y tasa 0,2
tiene media 5 y varianza 25: es relativamente difusa, pero no no informativa. El intervalo creíble publicado
es condicional a los pesos y al modelo. El CSV identifica el vacío con `missing_week = True` y las tres
semanas sin estimación alrededor de él (2008-S52–S53 y 2009-S01) con `missing_affected = True`.
`lambda_t` suma la infecciosidad diaria reconstruida dentro de la semana; no se lleva historia a través
del vacío. Las primeras estimaciones después del vacío dependen de la historia omitida y requieren cautela.

El intervalo serial se parametriza con la estimación de Simpson para varicela resumida en Vink et al. (2014):
media 14,1 días y desviación estándar 2,4 días (184 intervalos índice–caso en Inglaterra, 1947–1951).
El artículo estima una media agrupada de 14,0 días y reporta diferencias entre estudios. Por ello, estos
parámetros bibliográficos sirven como escenario de referencia, no como estimaciones para Colombia.

### Cálculo en Python según la lógica paramétrica de EpiEstim

[`scripts/epiestim_parametric_weekly.py`](scripts/epiestim_parametric_weekly.py) implementa en Python la
discretización Gamma desplazada de `discr_si()` y la reconstrucción iterativa diaria de la [ruta de incidencia
agregada de EpiEstim](https://mrc-ide.github.io/EpiEstim/articles/EpiEstim_aggregated_data.html), con `dt=7`
y reconstrucción inicial uniforme. La estimación publicada usa **ventanas de 14 días** (`dt_out=14`),
aproximadamente la media serial bibliográfica de varicela y dos períodos de agregación semanales. EpiEstim
sugiere comenzar con una ventana al menos tan larga como la media del intervalo serial y recomienda para
datos agregados no usar una ventana menor que la agregación. Vink et al. (2014) no proponen una ventana
para estimar Rₜ; la elección se compara con ventanas alternativas en el notebook.
Se trata de una implementación propia, no de una llamada al paquete R. La
[comparación reproducible con EpiEstim 2.4 en R](notebooks/04_comparacion_epiestim_r_python.ipynb)
coteja pesos, reconstrucción y posterior en tres tramos nacionales; esta comprobación
numérica no valida los supuestos epidemiológicos. La semana faltante de 2008
divide la serie y nunca se reemplaza por cero.

La pareja media 14,1 y desviación 2,4 corresponde a un estudio histórico de Inglaterra; otras dos muestras
de varicela de Australia y Taiwán reportan 13,1 ± 2,2 y 14,2 ± 1,3 días, respectivamente. Se incluyen en
el análisis de sensibilidad. Ninguna representa una estimación de varicela colombiana, y esta implementación
no infiere los parámetros seriales a partir de los conteos semanales.

## Notebook introductorio: I de Moran

El notebook [`notebooks/01_moran_global_knn.ipynb`](notebooks/01_moran_global_knn.ipynb) muestra, paso a paso, el cálculo de la I de Moran global para la tasa municipal de notificaciones de 2025. Construye una matriz de pesos con los ocho municipios más cercanos a un punto interior de cada geometría, explica cada término de la fórmula y compara el resultado con permutaciones aleatorias. Es una primera iteración para entender el procedimiento, no el análisis espacial final.

Desde la raíz del repositorio, con Python 3.12:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

Abrir `notebooks/01_moran_global_knn.ipynb` y ejecutar las celdas en orden. El notebook usa `docs/data_processed/spatial_series_2008_2025.csv` y `docs/data_processed/municipal_boundaries_dane.geojson`, incluidos en el repositorio; se puede abrir Jupyter desde la raíz o desde `notebooks/`.

## Gráficos y vista local

La [página estática](docs/index.html) muestra las notificaciones y tasas anuales, semanales y por edad, curvas estacionales, un mapa de calor de anomalías semanales ordenadas por latitud y un mapa municipal con años y periodos. El [README de `data/`](data/README.md) documenta las fuentes y los cálculos. Cada CSV publicado tiene su propio script generador.

Desde la raíz del repositorio, con Python 3 y [DuckDB CLI](https://duckdb.org/docs/stable/clients/cli/overview.html) instalados:

```bash
python3 scripts/generate_annual_series.py
python3 scripts/generate_weekly_series.py
python3 scripts/generate_age_group_series.py
python3 scripts/generate_spatial_series.py
python3 scripts/prepare_spatial_boundaries.py
python3 scripts/generate_latitude_week_heatmap.py
python3 -m http.server 8000 --directory docs
```

Abrir `http://localhost:8000/` en el navegador. El servidor local es necesario para cargar los CSV y el GeoJSON mediante JavaScript; abrir `docs/index.html` directamente como archivo puede bloquear esa carga. Los gráficos usan Vega-Lite y el mapa usa Leaflet y teselas de OpenStreetMap, por lo que la vista local necesita conexión a Internet. Los cambios locales aparecerán en la [página publicada](https://thesis-varicella-colombia.github.io/exploratory-analysis/) después de incorporarlos y publicarlos mediante GitHub Pages.
