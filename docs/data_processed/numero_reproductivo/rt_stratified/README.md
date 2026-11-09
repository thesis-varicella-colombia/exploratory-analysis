# Rₜ diario por edad y territorio

Generador: `python scripts/generate_rt_stratified.py` desde la raíz del repositorio.
Requiere los 19 CSV individuales locales, DIVIPOLA, las dos series nacionales
`rt_national_daily.csv` y `rt_national_symptom_daily.csv`, y la serie semanal
`weekly_series_2007_2025.csv` para la reconciliación por edad.

Se conservan 1.162 series generadas por fecha: Colombia (total nacional original), seis
categorías nacionales de edad, 32 departamentos y Bogotá D.C., y 1.122 entidades
municipales. Edad y territorio son análisis marginales independientes, sin cruce
entre ambas dimensiones. Los territorios usan residencia homologada a DIVIPOLA.
Incluyen municipios, áreas no municipalizadas y entidades insulares.

La página ofrece únicamente Rₜ nacional y territorial, para todas las edades.
Las series anteriores por edad se conservan como artefactos de trazabilidad y
no se exponen en los filtros: aplicar el estimador univariado a una edad no
representa explícitamente la transmisión entre grupos etarios.

Cada subserie aplica la posterior Poisson–Gamma del estimador nacional a sus
propios conteos diarios: intervalo serial Gamma desplazado con media 14,1 y DE
2,4 días, ventana de 14 días, previa de media 5 y DE 5. No se promedian Rₜ de
municipios para obtener el departamento. Se exige la misma historia del 99 %
del peso serial al inicio y después de cada bloque sin datos.

Las ventanas cuya suma de infecciosidad es ≤ 1e-12 no publican Rₜ: de otro modo,
una serie sin exposición solo reproduciría la previa. Este umbral trata residuos
numéricos como cero, no es un mínimo de casos. Las series nacionales se copian
sin cambiar los valores ya publicados. En series escasas, la previa puede influir
mucho aun cuando se publique una estimación.

Se conservan los calendarios de ausencia nacional: siete días en notificación y
140 días en síntomas. Un día sin registros locales en una semana nacional
observada aporta cero, sin afirmar que se haya descartado subregistro local.
Las fechas de inicio de síntomas del archivo fuente de 2013 se interpretan con
mes/día/año; los demás años y las fechas de notificación con día/mes/año.
Las unidades de edad se convierten con la función compartida del análisis de
hospitalizaciones. Se incluyen las edades no convertibles como categoría propia,
de modo que las edades suman el total.

`manifest.json` contiene los parámetros, los catálogos, la auditoría por archivo
fuente y los calendarios compartidos. En `calendars.notification` y
`calendars.symptom`, los arreglos `date`, `year`, `week` y `missing_week` tienen
6.580 posiciones y cubren los años epidemiológicos 2008–2025.

Cada archivo `{notification,symptom}/{id}.json.gz` contiene cinco arreglos
alineados a su calendario:

| Campo | Significado |
|---|---|
| `count` | Notificaciones o inicios de síntomas del día; null si no hay semana observada |
| `window_cases` | Suma de casos de los últimos 14 días, incluido el actual; null si la ventana es incompleta |
| `rt` | Media posterior de Rₜ; null si no es publicable |
| `rt_lower_95`, `rt_upper_95` | Intervalo creíble condicional del 95 % |

Las estimaciones se redondean a seis decimales. El navegador descarga y
descomprime únicamente la selección actual. Las gráficas se crean una vez y los
filtros actualizan sus datos y señales de título y escala, conservando las vistas
y los controles. La ampliación utiliza los datos de la selección vigente.
Los archivos también pueden leerse
directamente en Python:

```python
import gzip
import json
import pandas as pd
from pathlib import Path

root = Path("docs/data_processed/numero_reproductivo/rt_stratified")
manifest = json.loads((root / "manifest.json").read_text())
with gzip.open(root / "notification/municipality_05001.json.gz", "rt") as source:
    values = json.load(source)
series = pd.DataFrame({**manifest["calendars"]["notification"], **values})
```

La generación verifica, día por día, que edades y municipios sumen el total
nacional para ambas fechas. Las pruebas de publicación comprueban además que
los municipios sumen cada departamento, que se conserven huecos e intervalos,
y que las dos series nacionales reproduzcan las posteriores originales.
