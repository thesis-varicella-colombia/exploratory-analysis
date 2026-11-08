# Panel municipal de población, área, densidad y notificaciones, 2007–2025

Este conjunto respalda las gráficas «Casos e incidencia según la densidad poblacional»
y el diagnóstico de registros y denominadores. También aporta casos, población y
presencia de registros a las series del selector territorial anual.

## Archivos y cobertura

- [Datos del panel (CSV)](population_density_2007_2025.csv).
- [Metadatos del cálculo (JSON)](population_density_2007_2025.metadata.json).

La unidad de observación es **entidad municipal × año epidemiológico**. La clave
primaria es `(year, code)`. Hay 21.318 filas: 19 años (2007–2025, inclusive)
por 1.122 entidades de la geografía MGN 2025: 1.103 municipios, 18 áreas no
municipalizadas y una entidad de tipo `ISLA` (San Andrés). Providencia pertenece
al grupo `MUNICIPIO`. Las filas están ordenadas por año y código.

El CSV usa UTF-8, coma como separador, punto decimal, encabezado y campos vacíos
para valores ausentes. Los números se publican con hasta 12 posiciones decimales;
esa precisión de almacenamiento no expresa precisión de medición. Los códigos
deben leerse como texto de cinco dígitos, conservando los ceros iniciales.

## Origen y trazabilidad

Las entradas procesadas provienen del repositorio
[data-processing, carpeta data/processed](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/processed).
En una instalación con ambos repositorios hermanos, esa carpeta es
`../data-processing/data/processed`, relativa a la raíz de exploratory-analysis.
El generador utiliza las copias de trabajo de `data/` de este repositorio.
Los archivos de datos originales no se publican en data-processing debido a su
tamaño; los enlaces de las fuentes remiten a sus README de documentación.

| Insumo | Dataset de origen en data-processing | Copia utilizada por el generador |
| --- | --- | --- |
| Notificaciones de varicela, evento 831 | [`data/processed/integration_data/sivigila_integrado_notification_semanal_municipal.parquet/`](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/integration_data/README.md) | `data/sivigila_integrado_notification_semanal_municipal.parquet/` |
| Población municipal anual | [`data/processed/population/population_municipal_2007_2025.csv`](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md) | `data/population_municipal_2007_2025.csv` |
| Área y catálogo de entidades | [GeoJSON DANE, geometrías del MGN 2025](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/municipios#geometr%C3%ADas-geojson-del-mgn-2025) | `data/MGN_ADM_MPIO_GRAFICO.geojson.xz` |

Las notificaciones se agregaron originalmente por municipio de residencia y semana
de `FEC_NOT`, según la [documentación del agregado semanal](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/sivigila/notification_weekly_municipal/README.md).
El año epidemiológico procede de esa fecha, con calendario domingo–sábado y semana 1
que contiene el 4 de enero. No es necesariamente el año `ANO` reportado en el CSV
original ni el año calendario. Se elige la variante `notification`, distinta de
las variantes por semana reportada (`source`) e inicio de síntomas (`symptom`).
El integrado conserva estos conteos al unir otras fuentes; este panel solo usa
`ano_epidemiologico`, `codigo_municipio` y `casos_total` de ese integrado.
Los años de borde 2006 y 2026 se excluyen al seleccionar 2007–2025.

La población es estimada o proyectada, de ambos sexos y todas las edades, y procede
de la fila de área `Total` de los libros poblacionales DANE procesados para
2005–2017 y 2018–2042. Se usa únicamente `poblacion_total` del año correspondiente,
no una población constante ni un promedio entre años. Las fuentes y transformaciones
están documentadas en el [dataset de población](https://github.com/thesis-varicella-colombia/data-processing/blob/main/data/processed/population/README.md).

El área se extrae del atributo `mpio_narea`, en km², del GeoJSON DANE; es el área
de la entidad municipal. **No se calcula desde las coordenadas ni se utiliza
`shape_Area`**. Los nombres, departamentos y tipos se toman de `mpio_cnmbr`,
`dpto_cnmbr` y `mpio_tipo`; el código procede de `mpio_cdpmp`.

## Esquema y diccionario de datos

Los tipos indicados son lógicos; CSV no almacena tipos físicos.

| Campo | Tipo lógico | Unidad y significado | Ausencia permitida |
| --- | --- | --- | --- |
| `year` | Entero | Año epidemiológico, 2007–2025 | No |
| `code` | Texto, cinco dígitos | Código de la entidad en la geografía MGN 2025, tras homologación | No |
| `name` | Texto | Nombre de la entidad según el GeoJSON DANE | No |
| `department` | Texto | Nombre del departamento según el GeoJSON DANE | No |
| `kind` | Categoría | `MUNICIPIO`, `ÁREA NO MUNICIPALIZADA` o `ISLA` | No |
| `area_km2` | Número real | Área municipal en km²; fija para todos los años | Sí, si falta o no es finita y positiva |
| `population` | Número real | Personas estimadas/proyectadas del año, después de homologar y sumar | Sí |
| `cases` | Conteo numérico | Suma anual de `casos_total`; almacenada como número decimal | Sí, si el agregado no puede calcularse |
| `notification_record_present` | Booleano (`True`/`False`) | Existe un agregado de notificaciones para esa entidad y año después de homologar | No |
| `density_per_km2` | Número real | Habitantes por km² | Sí |
| `incidence_per_100k` | Número real | Notificaciones por 100.000 habitantes | Sí |
| `status` | Categoría | Disponibilidad y motivo de exclusión; diccionario siguiente | No |

`status` se asigna en este orden de prioridad: si coinciden varias causas, se
publica la primera.

| Valor | Regla |
| --- | --- |
| `missing_or_invalid_area` | Área ausente, no finita o no positiva |
| `missing_or_nonpositive_population` | Población ausente, no finita o no positiva |
| `missing_cases` | Conteo de casos ausente, con área y población válidas |
| `available` | Área y población válidas y casos disponibles |

`available` expresa disponibilidad de estas variables, no completitud de vigilancia.
El estado no reemplaza la revisión de cada campo: por ejemplo, una tasa puede ser
calculable con población válida aunque falte área, mientras la densidad no lo sea.

## Cómo se calculó

El procedimiento implementado en
[`generate_population_density.py`](../../../scripts/generate_population_density.py)
y [`municipal_coverage.py`](../../../scripts/municipal_coverage.py) es:

1. Leer las entidades y sus áreas del GeoJSON comprimido. Rechazar códigos
   geográficos duplicados y convertir áreas inválidas en ausentes.
2. Sumar `casos_total` por `ano_epidemiologico` y `codigo_municipio` en el Parquet
   de notificaciones, para 2007–2025, mediante DuckDB.
3. Rechazar duplicados de entidad-año en las entradas anuales de casos y población.
   Normalizar los códigos como texto de cinco dígitos y homologarlos según la tabla
   siguiente. Sumar casos y población por código de destino y año.
4. Aplicar una suma completa (`complete_sum`): si algún componente de un grupo
   es ausente, no finito o negativo, el agregado queda ausente. No sustituir una
   población faltante por cero ni sumar únicamente los componentes disponibles.
5. Construir el producto de los 19 años por todas las entidades del GeoJSON y
   unir población y casos mediante uniones izquierdas validadas.
6. Marcar `notification_record_present`. Asignar `cases = 0` únicamente a las
   combinaciones sin fila de casos, después de comprobar que todos los años
   tienen información nacional de notificaciones. Una fila presente con conteo
   ausente no se convierte en cero.
7. Calcular las razones con población finita y estrictamente positiva; para la
   densidad se exige además área finita y estrictamente positiva:

   ```text
   density_per_km2 = population / area_km2
   incidence_per_100k = 100000 × cases / population
   ```

8. Asignar `status`, ordenar por año y código y exportar CSV y metadatos JSON.

### Homologación de códigos

| Código de entrada | Código de destino |
| --- | --- |
| `00011` | `11001` |
| `27086` | `27493` |
| `94663` | `94343` |
| `88000` | `88001` |

Si varios códigos confluyen, se suman sus poblaciones y casos **antes** de calcular
las razones. No se promedian densidades ni tasas. Se mantiene la geografía de 2025
en toda la serie; no se reconstruyen áreas ni límites históricos.

## Diccionario de metadatos JSON

| Clave | Contenido |
| --- | --- |
| `area_source`, `population_source` | Rutas de las copias de entrada relativas a la raíz del repositorio |
| `area_field`, `area_unit`, `area_rule` | Atributo de área, unidad y regla de geografía fija |
| `density_formula`, `incidence_formula` | Fórmulas de las dos razones |
| `years` | Lista de los 19 años incluidos |
| `entities` | Cantidad de entidades por año: 1.122 |
| `entity_kinds` | Cantidades por tipo geográfico |
| `aliases` | Correspondencias de códigos de entrada a destino |
| `zero_rule` | Regla de asignación de ceros y preservación de presencia de registros |
| `unmapped_notification_rows` | Filas entidad-año de notificaciones cuyo código no está en el catálogo, tras homologación |
| `unmapped_notifications` | Suma de casos de esas filas sin correspondencia |
| `annual` | Lista de objetos con `year`, `cases` (suma anual del panel) y `plotted` (filas con `status = available`) |

La procedencia de las notificaciones se describe arriba porque el JSON actual
no incluye una clave específica para ese insumo. El JSON tampoco registra fecha
de ejecución, revisión del código ni hashes de las entradas; no permite por sí
solo identificar una versión inmutable de los archivos de origen.

## Perfil de la publicación actual

El CSV contiene 21.298 filas `available` y 20 con
`missing_or_nonpositive_population`. Hay 11 poblaciones ausentes y nueve iguales
a cero; ambas razones están ausentes en esas 20 filas. No hay áreas ni conteos
de casos ausentes. Los metadatos registran cero filas y cero notificaciones sin
correspondencia geográfica. Hay 17.105 filas con registro presente y 4.213 con
cero asignado por ausencia de registro.

| Año | Notificaciones | Entidades con registro | Entidades disponibles |
| --- | ---: | ---: | ---: |
| 2007 | 26.294 | 92 | 1.118 |
| 2008 | 63.592 | 756 | 1.121 |
| 2009 | 72.603 | 882 | 1.121 |
| 2010 | 73.979 | 909 | 1.121 |
| 2011 | 120.495 | 1.015 | 1.121 |
| 2012 | 99.548 | 1.027 | 1.121 |
| 2013 | 94.017 | 1.025 | 1.121 |
| 2014 | 107.763 | 1.038 | 1.121 |
| 2015 | 110.565 | 1.020 | 1.121 |
| 2016 | 111.930 | 1.029 | 1.121 |
| 2017 | 86.752 | 1.019 | 1.121 |
| 2018 | 74.860 | 1.012 | 1.121 |
| 2019 | 67.239 | 1.008 | 1.121 |
| 2020 | 18.645 | 861 | 1.121 |
| 2021 | 14.079 | 779 | 1.121 |
| 2022 | 22.685 | 876 | 1.121 |
| 2023 | 31.699 | 920 | 1.121 |
| 2024 | 24.894 | 907 | 1.122 |
| 2025 | 29.431 | 930 | 1.122 |

## Reproducción, lectura y validación

Desde la raíz de exploratory-analysis, con las entradas en `data/`, el entorno
Python del proyecto (pandas, numpy e ijson) y el ejecutable `duckdb` en `PATH`:

```bash
.venv/bin/python scripts/generate_population_density.py
.venv/bin/python -m unittest discover -s tests -p 'test_population_density.py'
node tests/test_population_density_visual.js
```

El generador acepta `--boundaries`, `--population`, `--parquet` y `--output`.
La salida predeterminada es esta carpeta; el JSON se escribe junto al CSV con
el sufijo `.metadata.json`. Regenerar sobrescribe ambos archivos.

Ejemplo de lectura desde la raíz del repositorio:

```python
import pandas as pd

panel = pd.read_csv(
    "docs/data_processed/varicela_totales_por_anio/population_density_2007_2025.csv",
    dtype={"code": "string"},
)
assert not panel.duplicated(["year", "code"]).any()
assert len(panel) == 19 * 1122
validos = panel.loc[panel.status.eq("available")]
```

Las pruebas verifican el uso del atributo de área, los denominadores del mismo
año, la homologación antes de calcular razones, los ceros y la coincidencia de
los totales con la serie anual publicada. Los consumidores principales son
[`population_density.js`](../../population_density.js),
[`analyze_population_density.py`](../../../scripts/analyze_population_density.py)
y [`generate_annual_territorial.py`](../../../scripts/generate_annual_territorial.py).

## Interpretación y limitaciones

- Un cero asignado por falta de registro no demuestra ausencia de enfermedad.
  Tener algún registro tampoco acredita notificación continua ni vigilancia completa.
- La incidencia describe notificaciones de esta fuente; no estima automáticamente
  todos los casos ocurridos ni el riesgo individual.
- La densidad es un promedio territorial, no una medida de hacinamiento. Casos,
  densidad y tasa comparten población en sus cálculos o escala; una asociación
  descriptiva no demuestra causalidad.
- Los cambios de límites, la homologación y el uso de área fija pueden afectar
  comparaciones históricas. Las series poblacionales de distintos periodos también
  requieren cautela al interpretar discontinuidades.
- 2007 se conserva para diagnóstico: sus 26.294 notificaciones constituyen un conteo
  atípicamente bajo, agravado por la discrepancia con los 69.695 casos nacionales
  informados en el [documento oficial de vigilancia del INS](https://www.minsalud.gov.co/Documentos%20y%20Publicaciones/PROTOCOLO%20VARICELA.pdf).
  El análisis descriptivo principal comienza en 2008; la causa de la discrepancia
  no está establecida.
