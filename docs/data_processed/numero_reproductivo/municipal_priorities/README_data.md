# Municipios prioritarios por Rₜ: especificaciones de los datos

## Descripción y archivos

Este conjunto identifica municipios con señales altas de Rₜ durante 2022–2025,
comparando fecha de notificación e inicio de síntomas. Alimenta dos tablas de
la sección «Número reproductivo instantáneo»:

- **Señales sostenidas:** 44 municipios con episodios de al menos siete días en
  ambas fechas.
- **Picos muy altos:** 44 municipios con máximos de Rₜ de al menos cinco en ambas fechas.

Hay 15 municipios compartidos: **73 municipios distintos y 88 filas de tablas**.
Cada fila representa un municipio dentro de una lista; la clave es `category`
y `code`. Las dos tablas son listas fijas para el período y no cambian con los
filtros de territorio o precisión de las gráficas.

| Archivo | Contenido |
| --- | --- |
| [web_tables.json](web_tables.json) | Archivo que carga la página: parámetros, recuentos y listas `sustained` y `peaks`. |
| [priority_candidates.csv](priority_candidates.csv) | 90 filas y 75 municipios: las 88 filas de señales altas, más dos casos de descensos sostenidos que no se muestran en estas tablas. |
| [paired_sustained_episodes.csv](paired_sustained_episodes.csv) | Todos los emparejamientos de episodios entre ambas fechas, incluidos otros períodos y descensos. |
| [qualified_episodes.csv](qualified_episodes.csv) | Todos los tramos extremos identificados desde 2008, incluidos los de un solo día. |
| [municipal_summary.csv](municipal_summary.csv) | Resúmenes para las 1.122 entidades, ambas fechas y cinco horizontes temporales; incluye sensibilidad al filtro de precisión. |
| [metadata.json](metadata.json) | Fuentes, criterios, recuentos y huellas de los archivos de referencia y del script. |

El [informe de resultados](README.md) desarrolla los hallazgos. Las auditorías
adicionales de ese informe no forman parte de las tablas de señales altas.

## Origen y generación

La fuente directa son los [datasets diarios originales de Rₜ](../rt_stratified/README.md),
con 1.122 series municipales por cada fecha. Se leen sus conteos, casos en ventana,
media posterior, límites creíbles y calendario. No se utilizan los promedios
preparados para visualización ni se vuelve a estimar Rₜ.

Esas series proceden de las fechas `FEC_NOT` e `INI_SIN` de los CSV individuales
de varicela, documentados en el
[README de Sivigila de data-processing](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos).
Los archivos originales no se publican allí por su tamaño. Los nombres y
departamentos se contrastan con el [panel municipal](../../varicela_totales_por_anio/README.md).

[`scripts/analyze_rt_municipal_priorities.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/analyze_rt_municipal_priorities.py)
genera los CSV y `web_tables.json`. La página los representa mediante
[`docs/rt_municipal_priorities.js`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/docs/rt_municipal_priorities.js).

## Reglas de selección

En cada día se exige una posterior válida, anchura relativa del intervalo del
95 % no mayor que 1 y aporte formal de la previa no mayor que 10 % tanto a la forma
como a la tasa de la posterior. Son los criterios del
[diagnóstico de precisión](../rt_information/README.md).

Para **señales sostenidas**, cada fecha debe tener un tramo de al menos siete
días consecutivos con Rₜ ≥2 y límite inferior del intervalo mayor que 1. Se
emparejan tramos que se solapan o cuya separación no supera 14 días. Si hay
varios pares en el municipio, se elige el de mayor duración mínima entre las
dos fechas; los empates se ordenan por el pico de notificación. Se publica un
par por municipio. El pico es el máximo dentro de ese tramo, no el máximo global.

Para **picos muy altos**, se toma el máximo que pasa el filtro de precisión en
2022–2025 para cada fecha. Ambos deben ser ≥5 y sus fechas diferir como máximo
14 días. No se exige un tramo de siete días para entrar en esta segunda lista.

Ambas tablas comienzan ordenadas de mayor a menor por el pico de Rₜ por inicio de
síntomas. Las flechas de cada encabezado permiten ordenar por esa columna y
alternar entre orden ascendente y descendente. Los números se comparan por su
valor, las fechas cronológicamente y los textos alfabéticamente; los tramos se
ordenan por su fecha de inicio y luego por su final. En caso de empate se usa el
código municipal. La elección del episodio sostenido sigue
la regla de duración anterior. La tolerancia entre fechas no corrige las demoras de notificación.

## Diccionario de las filas de las tablas

Los códigos se conservan como texto de cinco dígitos y las fechas como
`AAAA-MM-DD`. Los números son valores originales redondeados de los resultados
diarios; la página muestra los picos con dos decimales. Los CSV usan coma como
separador y punto decimal; los campos no aplicables están vacíos.

| Campo | Tipo lógico | Descripción |
| --- | --- | --- |
| `code` | Texto | Código de cinco dígitos de la entidad municipal. |
| `name` | Texto | Nombre del municipio o entidad. |
| `department` | Texto | Nombre del departamento. |
| `category` | Categoría | `recent_sustained_high_both_dates` o `recent_very_high_both_dates` en las tablas. El CSV contiene además `sustained_low_both_dates`, que no se muestra. |
| `notification_peak` | Número | Máximo por notificación del tramo elegido o del período, según la lista. |
| `notification_peak_date` | Fecha | Día de ese máximo. |
| `notification_peak_lo` | Número | Límite inferior del intervalo creíble del 95 % en ese día. |
| `notification_peak_hi` | Número | Límite superior de ese intervalo. |
| `symptom_peak` | Número | Máximo por inicio de síntomas del tramo elegido o del período. |
| `symptom_peak_date` | Fecha | Día de ese máximo. |
| `symptom_peak_lo` | Número | Límite inferior del intervalo creíble del 95 % en ese día. |
| `symptom_peak_hi` | Número | Límite superior de ese intervalo. |
| `notification_start` | Fecha | Inicio del tramo por notificación; solo en la lista sostenida. |
| `notification_end` | Fecha | Final inclusivo del tramo por notificación. |
| `notification_days` | Entero | Días consecutivos del tramo por notificación. |
| `symptom_start` | Fecha | Inicio del tramo por síntomas; solo en la lista sostenida. |
| `symptom_end` | Fecha | Final inclusivo del tramo por síntomas. |
| `symptom_days` | Entero | Días consecutivos del tramo por síntomas. |
| `min_days` | Entero | Menor duración entre los dos tramos; criterio utilizado para elegir el episodio de cada municipio. |

En `web_tables.json`, `sustained_count`, `peak_count`, `overlap_count` y
`unique_municipalities` registran 44, 44, 15 y 73. `period`, `width_limit`,
`prior_fraction_max`, `sustained_min_rt`, `sustained_min_days`, `peak_min_rt` y
`matching_tolerance_days` identifican el período y los umbrales. `version`
identifica el formato del archivo. `sort_field`, `sort_direction` y
`sort_tie_breaker` documentan el orden por pico de síntomas descendente y código.

## Interpretación y límites

Son prioridades de investigación retrospectiva, no confirmaciones de brotes ni
una clasificación sanitaria actual. Un Rₜ alto puede resultar de un aumento
desde muy pocos casos anteriores. Ambas fechas comparten registros y las ventanas
móviles de 14 días se solapan: sus coincidencias no son evidencia independiente.
La selección depende de los umbrales y de la calidad de las fechas; el filtro de
precisión no incorpora subregistro ni todos los cambios de vigilancia.

Para reproducir los archivos desde la raíz del repositorio:

```bash
.venv/bin/python scripts/analyze_rt_municipal_priorities.py
```

El script también conserva los análisis históricos y de descensos del informe
completo; en estos últimos se mantiene el requisito de 14 días. La página
solo carga los dos grupos altos de `web_tables.json`.
