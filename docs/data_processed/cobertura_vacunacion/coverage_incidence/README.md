# Evolución municipal de cobertura e incidencia por año

La gráfica de la subsección «Evolución de cobertura e incidencia por municipio»
usa los archivos de esta carpeta, generados por
[`scripts/generate_coverage_incidence_series.py`](../../../../scripts/generate_coverage_incidence_series.py):
un archivo `<código>.json` por entidad, `all.json` para el agregado «Todos los
municipios» y [`manifest.json`](manifest.json) con el catálogo de entidades, los
grupos de edad y el método. Esta ficha describe las fuentes, las series y los
archivos.

## Fuentes

- **Incidencia notificada:** notificaciones anuales de varicela (evento 831) de
  Sivigila (INS) por municipio de residencia, sobre denominadores poblacionales
  anuales del DANE por grupo de edad, ambos sexos.
- **Cobertura:** [`vaccine_coverage_comparison.csv`](../vaccine_coverage_comparison.csv),
  el panel municipal de cobertura descrito en
  [su propia ficha](../README_coverage_comparison.md). Se conserva el año de
  análisis ya desplazado; primera dosis usa edad 1 y refuerzo edad 5; la cobertura
  de sobrevivientes solo aplica a primera dosis.

## Período y grupos de edad

El eje temporal cubre **2008–2025**. El año 2007 se excluye por la discrepancia
documentada en la serie de notificaciones. La incidencia se ofrece por grupo:
todas las edades (incluye notificaciones sin edad conocida), menores de 1 año,
1–4, 5–14, 15–49 y 50 años o más.

## Series y cálculo

- **Incidencia:** `100.000 × notificaciones del grupo / población del mismo grupo y
  año`. Es una serie por cada edad marcada; «Todas las edades» es una serie
  adicional, no la suma de las otras.
- **Cobertura:** una serie por cada combinación de dosis y medida (PAI, población
  proyectada, sobrevivientes), sin duplicarse por edad. El filtro de edad cambia
  solo la incidencia; la cobertura conserva su población objetivo (1 año para
  primera dosis, 5 años para refuerzo).

Con «Todos los municipios» cada serie agrega las entidades con el dato válido para
esa medida: la incidencia suma casos y población del grupo; la cobertura sobre
población proyectada y la de sobrevivientes dividen las sumas de dosis y
denominador de las entidades con ambos disponibles; el porcentaje administrativo se
pondera por las metas PAI positivas. Cada serie reporta su propio recuento de
entidades incluidas. No es un promedio aritmético municipal ni acredita vigilancia
nacional completa.

## Valores ausentes

Las filas de notificación ausentes se asignan como cero y se marcan. Una población
ausente o no positiva deja la incidencia nula. La cobertura ausente se conserva
como tal. Los valores ausentes interrumpen las líneas y no se interpolan.

## Archivos

- `manifest.json`: años, año excluido, catálogo de entidades (código, nombre,
  departamento, tipo), definición del agregado, grupos de edad y reglas de método.
- `<código>.json` (una por entidad): claves `years`, `incidence` (por grupo),
  `cases`, `population`, `unknown_age_cases`, `notification_record_present`,
  `coverage` (por dosis y medida) y `coverage_details` (dosis, población de
  referencia, sobrevivientes y meta PAI original).
- `all.json`: la misma estructura para el agregado «Todos los municipios».

## Límites

Son series anuales descriptivas con unidades y ejes separados: la altura o el cruce
de las líneas no demuestra asociación. No hay interpretación causal ni medición de
inmunidad poblacional.

## Regeneración

Desde la raíz del repositorio, después de generar
`vaccine_coverage_comparison.csv`:

```bash
.venv/bin/python scripts/generate_coverage_incidence_series.py
```
