# Datos del mapa climático municipal

Los cinco archivos JSON se generan con [`scripts/generate_climate_map.py`](../../../../scripts/generate_climate_map.py) a partir de los Parquet semanales municipales de CHIRPS y ERA5-Land. El contrato exacto está en [`schema.json`](schema.json). El navegador carga un archivo por variable y reutiliza la geometría MGN 2025.

Cada archivo incluye una fila por municipio y horizonte: cuatro períodos (`2007-2014`, `2015-2019`, `2020-2021`, `2022-2025`) y los 19 años de 2007 a 2025. Las columnas de `rows` son, en este orden, `code`, `horizon`, `valid_weeks`, `total_weeks`, `mean_value`, `baseline_2007_2019` y `anomaly`. `mean_value` es la media de los valores semanales válidos, incluso para precipitación en mm/semana. `baseline_2007_2019` es la media semanal municipal de los 13 años de referencia, ponderada por semanas válidas; `anomaly = mean_value - baseline_2007_2019`.

Una semana es válida cuando la cobertura de la fuente alcanza el 95 % y el valor es finito. Un municipio se dibuja en gris si `valid_weeks / total_weeks < 0.80`. La anomalía también requiere una línea base con cobertura suficiente. Los límites de `scale_bounds.absolute` son los percentiles 2 y 98 de los promedios válidos de los 23 horizontes; `scale_bounds.anomaly` usa el máximo valor absoluto de los percentiles 2 y 98 de las anomalías válidas, con límites simétricos. El mapa recorta visualmente los extremos a estos límites y conserva la escala entre horizontes.

Regeneración desde la raíz del repositorio:

```bash
.venv/bin/python scripts/generate_climate_map.py --source-root ../data-processing/data/processed
```
