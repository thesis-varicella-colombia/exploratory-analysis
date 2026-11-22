# Comparación municipal de cobertura de varicela por año

El mapa de la sección «Cobertura administrativa y dosis sobre población de
referencia» usa dos archivos generados por
[`scripts/generate_vaccine_coverage_comparison.py`](../../../scripts/generate_vaccine_coverage_comparison.py):
[`vaccine_coverage_comparison.csv`](vaccine_coverage_comparison.csv), el panel
municipal por año y dosis, y
[`vaccine_coverage_comparison.metadata.json`](vaccine_coverage_comparison.metadata.json),
el calendario, los denominadores y las reglas de preparación. Esta ficha describe
las fuentes, las cinco medidas y las columnas.

## Fuentes

- **Dosis aplicadas (PAI):** `data/vaccine_coverage_municipal_lagged_2016_2025.csv`,
  registro municipal del Programa Ampliado de Inmunizaciones reportado por el
  Instituto Nacional de Salud, con el desplazamiento de la fuente ya aplicado.
- **Población de referencia:** `data/population_vaccine_ages_municipal_2016_2025.csv`,
  edades simples de las estimaciones y proyecciones del DANE, área Total y ambos
  sexos.
- **Sobrevivientes de 1 año:**
  `data/births_mortality_dane/integration/surviving_infants.parquet`, nacimientos
  menos defunciones de menores de 1 año del DANE.
- **Geografía:** `docs/data_processed/cartografia/municipal_boundaries_dane.geojson`
  (MGN del DANE), sobre la que se homologan los códigos históricos.

## Año de análisis y desplazamiento

El período es **2016–2025**. Se conserva el año de análisis de la fuente (`anio`) y
la población se toma de ese mismo año de análisis; la hoja de dosis original
corresponde al año anterior (`anio − 1`). Por ejemplo, las dosis de la hoja 2015
están etiquetadas 2016 y se dividen entre la población de 2016.

## Las cinco medidas

Para cada municipio, año y dosis el panel calcula cinco cifras. Dos provienen del
PAI (Instituto Nacional de Salud) y tres son estimaciones propias.

- **PAI – primera dosis** y **PAI – segunda dosis** (`administrative_coverage_pct`):
  porcentaje administrativo publicado. En territorios fusionados se ponderan los
  porcentajes por las metas PAI originales.
- **Población proyectada – primera dosis** (`reference_coverage_pct`, `first_dose`):
  `100 × dosis / población exactamente de 1 año` del año de análisis.
- **Población proyectada – segunda dosis** (`reference_coverage_pct`, `booster`):
  `100 × dosis de refuerzo / población exactamente de 5 años` del año de análisis.
- **Sobrevivientes – primera dosis** (`survivor_coverage_pct`, solo `first_dose`):
  `100 × dosis / sobrevivientes de 1 año` del año de análisis. El denominador ya
  equivale a nacimientos(t−1) menos defunciones de menores de 1 año(t−1); no lleva
  desplazamiento adicional.

El refuerzo (segunda dosis) solo aplica a partir de 2019; antes aparece con estado
`not_applicable_before_2019`. La medida de sobrevivientes no aplica al refuerzo.

## Denominadores ausentes y valores altos

Un denominador ausente, no positivo o inválido, o una cantidad de dosis no
registrada, deja la medida sin dato (estados detallados abajo) y el municipio se
dibuja en gris. Una cantidad registrada de cero dosis sí produce 0 %. Los
porcentajes superiores a 100 % se conservan; la escala de color llega hasta 200 %
y recorta visualmente por encima. La razón anual de dosis sobre población no mide
la fracción inmune: `measures_immunity` es `false`.

## Columnas de `vaccine_coverage_comparison.csv`

Una fila por municipio, año y dosis.

| Columna | Descripción |
| --- | --- |
| `code` | Código territorial de cinco dígitos (geografía del mapa). |
| `year` | Año de análisis (2016–2025). |
| `dose` | `first_dose` o `booster`. |
| `source_analysis_year` | Año de análisis de la fuente (igual a `year`). |
| `dose_source_year` | Año de la hoja de dosis original (`year − 1`). |
| `source_rows` | Registros PAI sumados en el municipio-año (0 si falta). |
| `merged_geography` | `True` si se unió más de un registro histórico. |
| `reference_age_group` | Edad del denominador: `age_1` o `age_5`. |
| `doses` | Dosis aplicadas sumadas. |
| `pai_target_population` | Meta de población PAI original. |
| `reference_population` | Población DANE del año de análisis (1 o 5 años). |
| `administrative_coverage_pct` | Cobertura administrativa publicada (PAI). |
| `reference_coverage_pct` | Dosis sobre población proyectada. |
| `administrative_status` | Estado de la cifra PAI. |
| `reference_status` | Estado de la cobertura sobre población proyectada. |
| `survivor_population` | Sobrevivientes de 1 año (solo primera dosis). |
| `survivor_coverage_pct` | Dosis sobre sobrevivientes (solo primera dosis). |
| `survivor_status` | Estado de la cobertura de sobrevivientes. |

### Valores de estado

- `available`: cifra calculada.
- `missing_source_record`: sin registro PAI para ese municipio-año.
- `missing_or_invalid_doses`: dosis ausentes o no numéricas.
- `missing_population` / `missing_survivors`: denominador ausente.
- `nonpositive_population` / `nonpositive_survivors`: denominador cero o negativo.
- `not_applicable_before_2019`: refuerzo antes de 2019.
- `not_applicable_to_booster`: medida de sobrevivientes en filas de refuerzo.

## Límites

La cobertura administrativa y las estimaciones propias responden preguntas
distintas y no son intercambiables. Un porcentaje por encima de 100 % señala
desajustes entre dosis y denominador, no inmunidad. La cartografía incluye
municipios, áreas no municipalizadas e islas; los códigos históricos se homologan
a la geografía del mapa sumando dosis y poblaciones.

## Regeneración

Desde la raíz del repositorio:

```bash
.venv/bin/python scripts/generate_vaccine_coverage_comparison.py
```

## Descargas

- [`vaccine_coverage_comparison.csv`](vaccine_coverage_comparison.csv): panel municipal por año y dosis.
- [`vaccine_coverage_comparison.metadata.json`](vaccine_coverage_comparison.metadata.json): calendario, denominadores y reglas.
