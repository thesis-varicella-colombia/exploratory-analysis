# Mapas departamentales de fase y amplitud

Los cinco mapas (cuatro períodos y un año seleccionable con animación) usan
[`department_phase_2008_2025.csv`](department_phase_2008_2025.csv) y la cartografía
[`department_boundaries_dane.geojson`](department_boundaries_dane.geojson), ambos
generados por [`scripts/generate_phase_analysis.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_phase_analysis.py).
Cada mapa colorea una de tres medidas por departamento: la **fase** (semana del
pico), la **amplitud absoluta** o la **amplitud relativa**.

## Fuentes y medida

La fuente inmediata es [`latitude_week_heatmap.csv`](latitude_week_heatmap.csv),
que contiene las tasas semanales de notificación por 100.000 habitantes de los 32
departamentos o distritos continentales, por fecha de notificación. Se excluye San
Andrés y Providencia del gradiente continental y se usan las semanas 1 a 52 de
2008–2025; 2007 queda fuera por la discrepancia documentada en la serie.

Para cada departamento, período y semana se promedian primero las tasas anuales
disponibles de esa semana. La curva se suaviza con una **ventana circular de cinco
semanas** (de $s-2$ a $s+2$, tomando la semana 52 como vecina de la 1); una semana
sin dato se excluye del promedio para no abrir una caída artificial. Sobre las 52
posiciones de la curva suavizada $\tilde T_{d,s}$ se derivan las tres medidas:

- **Fase** (`peak_week`): la semana con la tasa suavizada máxima. Ante un empate se
  elige la primera semana.
- **Amplitud absoluta** (`amplitude_per_100k`): máximo menos mínimo de la curva, en
  notificaciones por 100.000 habitantes.
- **Amplitud relativa** (`relative_amplitude`): amplitud absoluta dividida por la
  media de la curva suavizada; adimensional y vacía cuando la media es cero.

Los mapas por período agregan todos los años del período antes de suavizar; el mapa
de año individual usa solo las tasas de ese año. Los cinco mapas comparten la escala
de color de cada medida. Las semanas 52 y 1 son contiguas en el calendario aunque
reciban colores distintos.

## Cobertura y geometría

Los períodos son **2008–2014** (prevacunal), **2015–2019** (transición),
**2020–2021** (pandemia) y **2022–2025** (refuerzo). El selector de año recorre
2008–2025. La cartografía agrega las geometrías municipales de la MGN 2025 del DANE
en 32 departamentos o distritos continentales; su latitud es la del centroide
agregado.

## Columnas de `department_phase_2008_2025.csv`

**704 filas**: 32 departamentos × (18 años + 4 períodos). Una fila por territorio y
selección.

| Columna | Descripción |
| --- | --- |
| `period` | Año individual (2008–2025) o uno de los cuatro períodos. |
| `department_code` | Código departamental de dos dígitos. |
| `department` | Nombre del departamento o distrito. |
| `latitude` | Latitud del centroide del departamento, en grados. |
| `peak_week` | Semana 1–52 de la tasa suavizada máxima (la fase). |
| `amplitude_per_100k` | Amplitud absoluta: máximo menos mínimo de la curva suavizada, por 100.000. |
| `mean_rate_per_100k` | Media de las tasas suavizadas disponibles, por 100.000. |
| `relative_amplitude` | Amplitud absoluta dividida por la media; vacía si la media es cero. |
| `observed_weeks` | Semanas con tasa disponible antes del suavizado. |

Los códigos son texto para conservar los ceros iniciales. El CSV usa UTF-8, coma y
punto decimal; las amplitudes y la media llevan nueve decimales, la amplitud
relativa seis y la latitud cinco.

## Estabilidad de los picos estacionales

La comprobación de sensibilidad recalcula la semana del pico con **tres ventanas de
suavizado (3, 5 y 9 semanas)** y mide cuánto se desplaza respecto de la ventana
original de 5. El desplazamiento usa la distancia más corta en el calendario
circular: entre las semanas 52 y 1 hay una semana, no 51. Una curva plana no tiene
fase estimable. La definió [`scripts/analyze_spatial_seasonal_sensitivity.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/analyze_spatial_seasonal_sensitivity.py).

- [`seasonal_sensitivity.csv`](seasonal_sensitivity.csv): resumen por selección y ventana.

  | Columna | Descripción |
  | --- | --- |
  | `horizon` | Año o período evaluado. |
  | `width` | Ancho de la ventana de suavizado (3, 5 o 9 semanas). |
  | `departments` | Departamentos con fase estimable. |
  | `median_peak_shift` | Mediana del desplazamiento del pico respecto de la ventana de 5, en semanas. |
  | `p90_peak_shift` | Percentil 90 de ese desplazamiento. |
  | `departments_shift_over_4` | Departamentos cuyo pico se desplaza más de cuatro semanas. |
  | `spearman_linear` | Correlación de Spearman entre latitud y semana del pico con esa ventana. |
  | `circular_linear_magnitude` | Magnitud de la asociación circular entre latitud y semana del pico (0–1). |

- [`seasonal_sensitivity_departments.csv`](seasonal_sensitivity_departments.csv): detalle por departamento, selección y ventana.

  | Columna | Descripción |
  | --- | --- |
  | `horizon` | Año o período evaluado. |
  | `department_code`, `department` | Código de dos dígitos y nombre. |
  | `width` | Ancho de la ventana de suavizado. |
  | `latitude` | Latitud del centroide. |
  | `peak_week` | Semana del pico con esa ventana. |
  | `amplitude` | Amplitud absoluta con esa ventana. |
  | `mean_rate` | Media de las tasas suavizadas con esa ventana. |
  | `circular_distance_from_5` | Desplazamiento del pico frente a la ventana de 5, en semanas (distancia circular). |

Esta comprobación mide sensibilidad al suavizado, no intervalos de confianza. Un
único máximo puede ocultar un segundo pico; la evaluación completa de bimodalidad
sigue pendiente.

## Interpretación y límites

La fase describe *cuándo* repunta la varicela notificada y las amplitudes, *cuánto*
oscila la tasa en el año. Cuando las tasas y su amplitud son bajas, la semana del
máximo es inestable. La amplitud absoluta no es un recuento de casos; la relativa no
indica si el pico es agudo o prolongado, solo su altura frente a la media, y se
dispara en departamentos con media baja. Ninguna medida demuestra transmisión entre
departamentos, asociación con la lluvia ni efecto causal de la vacunación. Las cifras
resumidas por período son medianas de los 32 departamentos, no tasas nacionales.
