# Estacionalidad y gradiente latitudinal: especificaciones de los datos

## Descripción y archivos

Las curvas del componente A y el mapa de calor del componente B describen tasas
semanales de notificación de varicela por 100.000 habitantes. Las curvas también
permiten seleccionar la fecha de inicio de síntomas. Los tres gráficos pedidos
en la página se alimentan de dos conjuntos distintos:

| Archivo | Contenido |
| --- | --- |
| [seasonal_territories/manifest.json](seasonal_territories/manifest.json) | Calendario semanal, grupos de edad y catálogo de 1.156 territorios: Colombia, 33 departamentos o distritos y 1.122 entidades municipales. |
| `seasonal_territories/{id}.json.gz` | Un archivo comprimido por territorio, con tasas para ambas fechas y los grupos `all`, `5_14` y `15_49`. El identificador `{id}` figura en el catálogo. |
| [latitude_week_heatmap.csv](latitude_week_heatmap.csv) | Tasas y anomalías estandarizadas de 32 departamentos o distritos continentales por semana y selección de año o periodo. |
| [municipal_phase_2008_2025.csv](municipal_phase_2008_2025.csv) | Semana pico y amplitud de cada municipio con notificaciones en cada periodo disponible del Componente C. |

Las tasas territoriales se generan con
[`scripts/generate_seasonal_territories.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_seasonal_territories.py).
El mapa se genera con
[`scripts/generate_latitude_week_heatmap.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_latitude_week_heatmap.py).
Las fases municipales se generan con
[`scripts/generate_municipal_phase_analysis.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_municipal_phase_analysis.py).
La página calcula las medianas y percentiles de las curvas al seleccionar fecha y
territorio; estos resúmenes no se guardan como archivos separados.
El catálogo contiene 939 pares `[año, semana]` entre 2008 y 2025. Cada archivo
territorial tiene `id` y `series`, con arreglos `notification` y `symptom` para
los tres grupos; cada arreglo conserva el orden del calendario. Las tasas están
redondeadas a cuatro decimales y `null` representa una tasa ausente.

## Origen y generación

Los conteos semanales proceden del
[Sivigila integrado](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md)
por municipio, año y semana epidemiológicos. Para las curvas se usan los conjuntos
integrados por fecha de notificación y por inicio de síntomas; el mapa usa solo
notificación. Los denominadores son las poblaciones anuales municipales del
[conjunto de población](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md),
sumadas antes de calcular tasas departamentales o nacionales. La tasa de cada
grupo y semana es `casos / población anual del mismo grupo y año × 100.000`;
no es una tasa anualizada. La cartografía del
[GeoJSON municipal](../cartografia/municipal_boundaries_dane.geojson)
aporta los centroides usados para ordenar el mapa de sur a norte.

El calendario distingue ausencia nacional de registros de cero casos en un
territorio. Cuando hay datos nacionales en una semana, un territorio sin filas
de notificación aporta cero. Si la semana falta a escala nacional, la tasa queda
ausente. Las semanas 53 están en el calendario territorial cuando existen, pero
los tres gráficos aquí documentados solo usan las semanas 1 a 52.

## Tasa total entre periodos

El gráfico usa `series[fecha].all` del archivo del territorio seleccionado.
Cada posición corresponde al par `[año, semana]` de `manifest.json`. `all` incluye
los casos sin edad conocida. Se comparan 2008–2014, 2016–2019 y 2022–2025;
2015 y 2020–2021 no participan en estas curvas. Para cada periodo y semana se
ordenan las tasas anuales disponibles y se calculan la mediana y los percentiles
25 y 75 mediante interpolación lineal. La línea representa la mediana y la banda,
la dispersión entre años. Las semanas sin tasa se excluyen del cálculo de esa
semana, sin imputarlas como cero. Los percentiles no son intervalos de confianza.

## Escolares y adultos dentro de cada periodo

Los tres gráficos usan las mismas semanas, fechas, territorios y periodos del
apartado anterior, pero leen `series[fecha]["5_14"]` para edades de 5 a 14 años
y `series[fecha]["15_49"]` para edades de 15 a 49 años. El segundo grupo incluye
personas de 15 a 17 años. Los casos y la población de cada grupo se emparejan
por año y territorio antes de calcular la tasa. Para cada semana y grupo se
representan la mediana y los percentiles 25 y 75 de las tasas anuales disponibles.
Los registros sin edad no se asignan a ninguno de estos dos grupos.

## Componente B: Anomalía estacional por departamento y semana

El CSV tiene **36.608 filas**: 22 selecciones (19 años, de 2007 a 2025, y los
tres periodos anteriores) × 32 departamentos o distritos × 52 semanas. Cada fila
se identifica por `period`, `department_code` y `week`. Se excluye San Andrés y
Providencia del gradiente continental. Para un año, la tasa es la de esa semana;
para un periodo, `mean_rate_per_100k` es la media aritmética de las tasas de esa
semana en los años con datos. Los años sin esa semana no entran en la media.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `period` | Texto | Año individual o uno de los tres periodos. |
| `department_code` | Texto | Código departamental de dos dígitos. |
| `department` | Texto | Nombre mostrado en el eje del mapa. |
| `latitude` | Número | Latitud del centroide de las geometrías municipales agregadas, en grados; ordena las filas. |
| `week` | Entero | Semana epidemiológica de 1 a 52. |
| `mean_rate_per_100k` | Número o vacío | Tasa semanal del año o media de tasas semanales del periodo, por 100.000 habitantes. |
| `department_mean` | Número | Media de las tasas de las semanas disponibles de esa selección y departamento. |
| `sd_rate` | Número | Desviación estándar poblacional de esas tasas entre semanas. |
| `z_score` | Número o vacío | `(mean_rate_per_100k − department_mean) / sd_rate`; vacío si falta la tasa semanal o `sd_rate` es cero. |
| `years_with_data` | Entero | Número de años con tasa disponible para esa semana; en una selección anual vale cero o uno. |

El CSV usa UTF-8, comas y punto decimal. Las tasas y `z_score` se publican con
seis decimales, y la latitud con cinco. Una celda gris representa `z_score` vacío:
por ejemplo, la semana 52 de 2008 no tiene datos nacionales o algunos
departamentos en 2007 no tienen variación semanal. El mapa fija la escala de
colores entre −2 y 2 y satura los extremos; `z_score` en el CSV y el tooltip
conserva valores fuera de ese intervalo. Cero indica la media propia del
departamento, y ±1 o ±2 indican una o dos desviaciones estándar respecto de ella.
El año 2007 se presenta solo como referencia diagnóstica por la discrepancia
documentada entre la base integrada y la cifra oficial.

## Componente C: latitud y semana del pico

El nivel departamental usa [department_phase_2008_2025.csv](department_phase_2008_2025.csv)
con 704 filas: 32 departamentos o distritos continentales × 18 años (2008–2025)
y cuatro periodos. El gráfico de dispersión presenta tres de esos periodos:
2008–2014, 2015–2019 y 2022–2025. El nivel municipal usa
[municipal_phase_2008_2025.csv](municipal_phase_2008_2025.csv), generado desde
la tasa de notificación total del catálogo territorial. Tiene 3.316 filas,
una por municipio y periodo con al menos una tasa semanal positiva. Los
municipios sin notificaciones en un periodo no tienen pico definido y se omiten.

Para cada territorio y periodo se promedian primero las tasas anuales de cada
semana 1–52 con datos. Después se suaviza la curva con una ventana circular de
cinco semanas. `peak_week` es la semana con la tasa suavizada máxima; ante un
empate se elige la primera semana. `amplitude_per_100k` es la diferencia entre
máximo y mínimo de la curva suavizada; `relative_amplitude` divide esa amplitud
por la media suavizada. La latitud municipal proviene del centroide de su
geometría en una proyección de área equivalente. El filtro de búsqueda resalta
el territorio elegido en los tres gráficos y conserva los demás puntos como
referencia.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `period` | Texto | Año o periodo en el archivo departamental; uno de los tres periodos del gráfico en el municipal. |
| `department_code`, `department` | Texto | Código de dos dígitos y nombre del departamento; `department` solo aparece en el archivo departamental. |
| `municipality_code`, `municipality` | Texto | Código de cinco dígitos y nombre; solo en el archivo municipal. |
| `latitude` | Número | Latitud del centroide del territorio, eje horizontal. |
| `peak_week` | Entero | Semana 1–52 de la tasa suavizada máxima, eje vertical. |
| `amplitude_per_100k` | Número | Máximo menos mínimo de la tasa suavizada, por 100.000 habitantes. |
| `mean_rate_per_100k` | Número | Media de las 52 tasas suavizadas disponibles, por 100.000. |
| `relative_amplitude` | Número o vacío | Amplitud absoluta dividida por la media; vacío cuando la media es cero. |
| `observed_weeks` | Entero | Semanas con tasa disponible antes del suavizado. |

Los códigos son texto para conservar los ceros iniciales. Los CSV usan UTF-8,
coma y punto decimal. Los nombres con comas, como `BOGOTÁ, D.C.`, van entre
comillas según el formato CSV.

## Componente D: correlación anual entre latitud y semana del pico

El gráfico lee [phase_spearman_2008_2025.csv](phase_spearman_2008_2025.csv),
generado junto con el archivo departamental anterior por
[`scripts/generate_phase_analysis.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_phase_analysis.py).
Contiene **18 filas**, una por año epidemiológico de 2008 a 2025. El componente
usa los 32 departamentos o distritos continentales de cada año; no incluye
municipios ni San Andrés y Providencia. La fuente inmediata de las tasas es
`latitude_week_heatmap.csv`, calculado por fecha de notificación.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `year` | Entero | Año epidemiológico, 2008–2025. |
| `spearman_r` | Número o vacío | Correlación de Spearman entre latitud del centroide departamental y semana del pico anual; vacío si alguno de los rangos no varía. |
| `departments` | Entero | Número de territorios incluidos; 32 en todos los años publicados. |

Para cada departamento y año se suavizan las tasas de las semanas 1–52 con la
misma ventana circular de cinco semanas del componente C. Se calcula la semana
de máximo y se correlacionan sus rangos con los rangos de latitud, promediando
los rangos empatados. Un coeficiente negativo indica que los departamentos más
septentrionales tienden a tener picos en semanas numéricamente anteriores. El
CSV no incluye intervalos de confianza ni pruebas de significación. Aunque el
suavizado une las semanas 52 y 1, Spearman ordena sus números linealmente: el
resultado puede variar si se cambia el inicio del ciclo anual. La coincidencia
temporal con eventos de lluvia, incluida La Niña de 2010–2011, no establece una
relación causal con la fase de la incidencia.

## Interpretación y límites

Las series describen notificaciones de vigilancia y dependen de la fecha usada;
la fecha de inicio de síntomas puede faltar en algunos registros, especialmente
en 2013. Un pico relativo del mapa no implica una tasa absoluta alta. La
coincidencia o el desfase de picos entre departamentos no demuestra propagación,
asociación con la lluvia ni efecto causal de la vacunación.
