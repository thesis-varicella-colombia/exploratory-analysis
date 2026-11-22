# Sobrevivientes de un año: nacimientos y mortalidad infantil DANE

Copia del dataset integrado de `../data-processing/data/processed/births_mortality_dane/integration`, realizada el 2026-11-05. Se conserva el Parquet original sin modificar y sus reportes `quality_report.json` y `unmatched_rows.csv`. El repositorio de origen contiene el procesamiento en `scripts/processing/integrate_surviving_infants.py`.

El archivo `surviving_infants.parquet` contiene 21.868 filas y ocho columnas, para 2008–2025. Claves: `ano`, `codigo_departamento`, `codigo_municipio`; códigos como texto. Los nombres territoriales son descriptivos. Las medidas son `total_nacimientos`, `total_defunciones_menor_1` y `sobrevivientes_edad_1`.

```
sobrevivientes_edad_1(t) = total_nacimientos(t−1) − total_defunciones_menor_1(t−1)
Cobertura Sobrevivientes(t) = 100 × primeras dosis etiquetadas t / sobrevivientes_edad_1(t)
```

El denominador ya está adelantado un año: se une `ano` al año de análisis de vacunación sin aplicar otro desplazamiento. Por ejemplo, el denominador de 2008 sería el saldo de 2007; en este archivo 2008 está ausente porque no hay datos de 2007. Las coberturas disponibles aquí corresponden a 2016–2025 y conservan el año de análisis ya desplazado de la fuente PAI.

En origen se excluyen los totales municipales y se unen nacimientos y mortalidad por claves completas, conservando ambos orígenes. Si hay nacimientos con clave completa pero falta la fila de mortalidad, se asumen cero defunciones (454 filas). Si existe la fila pero algún componente es nulo, el total de defunciones sigue nulo. Se exige el año anterior exacto para el saldo, sin saltar huecos. Los nacimientos ausentes no se imputan como cero. El saldo anual no sigue individualmente una cohorte ni incorpora migración.

El archivo original conserva países y categorías especiales (`-1`, `-2`), claves incompletas, 2.248 saldos nulos y 16 negativos. El reporte de calidad describe esos casos y `unmatched_rows.csv` contiene 1.092 filas con claves incompletas. Los reportes conservan las rutas de las entradas del repositorio de origen. Bogotá está armonizada a `11001`.

Para la cobertura solo se usan códigos municipales de cinco dígitos presentes en la cartografía. Se homologan códigos históricos con las mismas reglas del resto del mapa y se suman los denominadores únicamente cuando todos los componentes son válidos. Los denominadores ausentes, negativos o incompletos dejan la estimación sin dato; un denominador cero tampoco genera porcentaje. Cero dosis registradas con denominador positivo sí produce 0 %. Se conservan los porcentajes superiores a 100 % y no se calcula esta medida para refuerzos.

Regeneración desde la raíz de este repositorio, usando la copia local:

```bash
.venv/bin/python scripts/generate_vaccine_coverage_comparison.py
.venv/bin/python scripts/generate_coverage_incidence_series.py
```

El CSV resultante incorpora `survivor_population`, `survivor_coverage_pct` y `survivor_status`. En «Todos los municipios», Cobertura Sobrevivientes se calcula como 100 × suma de primeras dosis / suma de sobrevivientes sobre las mismas entidades con medida válida; no es la media de porcentajes municipales.
