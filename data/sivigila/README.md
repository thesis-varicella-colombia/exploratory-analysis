# Ficha técnica: microdatos de varicela individual — Sivigila

Esta carpeta contiene microdatos del evento **Varicela Individual** (código **831**) del Sistema Nacional de Vigilancia en Salud Pública de Colombia (Sivigila), administrado por el Instituto Nacional de Salud (INS). Sivigila reúne las notificaciones de eventos de interés en salud pública; estos archivos corresponden a registros individuales de varicela publicados por el INS para consulta y análisis. El código 831 identifica la notificación individual, distinta de la notificación colectiva de varicela (código 830).

## Fuente y descarga

Fuente: [Buscador de microdatos de Sivigila del INS](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx).

Para obtener los archivos desde la fuente original:

1. Abrir el buscador de microdatos.
2. Seleccionar **Varicela Individual** como evento y elegir el año deseado.
3. Pulsar **Buscar** y solicitar la descarga del resultado. El portal pide correo electrónico, entidad, nombre y propósito de uso; envía el enlace de descarga al correo indicado.
4. Repetir la consulta para cada año requerido.

El INS describe estas bases como **depuradas, nominales y sin datos de identificación personal**. La disponibilidad y el contenido del portal pueden cambiar con el tiempo; para una versión actualizada, consultar siempre la fuente original.

## Archivos y cobertura

Hay **19 archivos**, uno por año de **2007 a 2025**, sin años faltantes en ese intervalo. El patrón de nombre es `Datos_<año>_831.xlsx`; por ejemplo, `Datos_2007_831.xlsx` y `Datos_2025_831.xlsx`.

Los originales están en `excel/`, en formato **Excel (`.xlsx`)**. Cada uno tiene una hoja llamada `Datos`, con encabezados de variables y filas de registros individuales. Los nombres de las columnas son códigos o abreviaturas del sistema, como `FEC_NOT` (fecha de notificación), `SEMANA` (semana epidemiológica), `ANO` (año epidemiológico), `EDAD`, `SEXO` y `COD_DPTO_O` (departamento de ocurrencia). También hay variables sobre residencia, atención, clasificación y desenlace del caso. Los códigos geográficos y otras categorías deben interpretarse con sus definiciones, no como valores numéricos continuos.

Para generar una copia CSV por año en `csv/`, desde la raíz del repositorio:

```bash
.venv/bin/python scripts/processing/convert_sivigila_excel_to_csv.py
```

El script usa `openpyxl` (incluido en `scripts/requirements.txt`), conserva el orden y los valores de las columnas sin depuración y escribe en UTF-8. Si un CSV ya existe, lo omite; `--overwrite` permite regenerarlo. Los CSV derivados no se incluyen en Git.

El significado de las columnas y de varios valores codificados se documenta en el [diccionario de datos](dic_datos.md). El notebook [`sivigila_raw_explore.ipynb`](../../../notebooks/sivigila_raw_explore.ipynb) permite explorar los archivos. Consulte el diccionario antes de combinar años o construir indicadores; algunas variables pueden estar vacías, depender de otras respuestas o requerir criterios específicos de depuración.

## Consideraciones de uso

- Los registros son **notificaciones de vigilancia**, no una medición de todos los casos de varicela ocurridos en la población. Los conteos directos tampoco son tasas de incidencia: para calcular tasas se necesitan denominadores poblacionales y una definición explícita de caso.
- Para agrupar por año o semana epidemiológica, revise `ANO` y `SEMANA`. `FEC_NOT` es la fecha de notificación y puede responder a una pregunta distinta de la fecha de inicio de síntomas (`INI_SIN`).
- Antes de contar casos, revise las variables de clasificación y ajuste (`TIP_CAS`, `AJUSTE` y las variables de estado final) y documente los filtros aplicados. Para comparar resultados con publicaciones oficiales, consulte el protocolo y la metodología del INS vigentes para el periodo analizado.
- Conserve los archivos originales como fuente y realice cualquier limpieza o transformación en una copia derivada.

Referencias: [portal Sivigila del INS](https://portalsivigila.ins.gov.co/) · [protocolo de vigilancia de varicela del INS](https://www.ins.gov.co/Direcciones/Vigilancia/sivigila/Protocolos/PRO%20Varicela.pdf).
