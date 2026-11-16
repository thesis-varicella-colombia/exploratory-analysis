# Series para los filtros de la curva estacional

Generar desde la raíz del repositorio con
`.venv/bin/python scripts/generate_seasonal_territories.py`.

El generador lee los integrados semanales municipales por fecha de notificación
y de inicio de síntomas, la población municipal anual y el catálogo territorial
de Rₜ. Publica 1.156 series: Colombia, 33 departamentos y 1.122 entidades
municipales. La edad y el territorio se cruzan aquí porque los integrados
semanales contienen conteos por grupo de edad para cada municipio.

`manifest.json` contiene el calendario común de pares `[año, semana]`, los grupos
`all`, `5_14` y `15_49`, y el catálogo territorial. Cada `{id}.json.gz` contiene
las tasas semanales por 100.000 habitantes para las fechas `notification` y
`symptom`, separadas por grupo de edad y alineadas con ese calendario.

La tasa de un departamento se calcula sumando sus casos y poblaciones
municipales por año; no se promedian tasas. Una semana sin datos nacionales se
guarda como `null`. Un municipio sin registros en una semana nacional observada
tiene tasa cero si su población es positiva. Una población ausente o no positiva
también produce `null`. Los valores se redondean a cuatro decimales. El análisis
de la sección 5A omite las semanas 53 y calcula las medianas y los percentiles
entre años a partir de estas tasas.
