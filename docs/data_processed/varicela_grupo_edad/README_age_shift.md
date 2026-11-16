# Composición etaria y razón de incidencias: especificaciones de los datos

## Archivo y origen

Las tres gráficas de la sección «Impacto vacunación y cambios en la distribución
etaria» usan [age_group_series_2007_2025.csv](age_group_series_2007_2025.csv).
El [README del archivo](README.md) documenta su origen en las notificaciones
de varicela por fecha de notificación y en la población anual municipal. Las
notificaciones y poblaciones se agregan nacionalmente por año epidemiológico y
grupo de edad. El archivo contiene 114 filas: 19 años (2007–2025) × seis
categorías, cinco de edad conocida y `unknown`.

La página calcula las tres visualizaciones con
[`docs/charts.js`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/docs/charts.js).
No se publican archivos derivados adicionales. Los conteos representan
notificaciones de vigilancia, no todas las infecciones.

## Composición etaria

Para cada año, la página suma `notifications` de `under_1`, `1_4`, `5_14`,
`15_49`, `50_plus` y `unknown`. La participación de un grupo es su conteo
dividido por ese total. Cada barra apilada suma 100 %; los registros sin edad
también se incluyen. El denominador es el número de notificaciones del año,
no la población del grupo. La composición no es una comparación de incidencias.

La comparación narrativa de periodos usa promedios anuales de conteos y la
participación acumulada dentro de cada periodo. La reducción del total de
notificaciones en 2022–2025 no implica que el conteo de 15–49 años aumente:
su participación puede subir porque los conteos infantiles bajan más.

## Razón de incidencias por edad (ASR)

Se usan las filas `1_4` y `15_49` del mismo año. A partir de los conteos y
poblaciones originales se calculan, sin usar la tasa ya redondeada del CSV:

```text
incidencia_grupo = notifications_grupo / population_grupo × 100.000
ASR = incidencia_15_49 / incidencia_1_4
razón inversa = incidencia_1_4 / incidencia_15_49
```

La gráfica traza el ASR de 2008 a 2025. El punto de 2007 se muestra solo como
referencia diagnóstica porque la base integrada tiene un total nacional
atípicamente bajo ese año. El tooltip conserva la razón inversa y las dos
incidencias. No hay una tabla anual separada: las cifras se derivan del CSV de
origen. Si alguna incidencia utilizada como divisor fuese cero, la razón no
sería calculable; esto no ocurre en las filas nacionales publicadas.

Para resumir los periodos se obtiene la mediana de los ASR anuales de
2008–2014 y, por separado, de 2015–2025. La mediana es de aproximadamente
0,17 y 0,22, respectivamente. Un ASR mayor indica mayor incidencia relativa
en 15–49 años frente a 1–4 años; un valor menor que 1 significa que la
incidencia de 1–4 años todavía es mayor. El ASR de 2024 es cercano a 0,50,
pero baja a cerca de 0,26 en 2025: el cambio no es uniforme entre años.

## Protección indirecta: menores de 1 año

La gráfica compara las filas `under_1` y `1_4` desde 2008 hasta 2025. Cada
incidencia se calcula a partir de `notifications / population × 100.000` del
mismo grupo y año. El año 2007 se excluye por la discrepancia del total
nacional. Los menores de 1 año todavía no son el grupo objetivo de la
primera dosis, administrada a los 12 meses.

La mediana de las incidencias anuales de menores de 1 año es aproximadamente
570 por 100.000 en 2008–2014, 571 en 2015–2019 y 163 en 2022–2025. La
primera comparación no muestra una disminución temprana clara. En 2018 y
2019, la tasa notificada de menores de 1 año supera la de 1–4 años. La
reducción posterior es compatible con una menor exposición, pero las tasas
por sí solas no permiten distinguir protección indirecta de otros cambios
en transmisión, atención o notificación.

## Interpretación y límites

El grupo 15–49 incluye adolescentes de 15–17 años y adultos; no permite
distinguir una edad precisa de infección. Las tasas usan denominadores
poblacionales anuales y pueden verse afectadas por diferencias de consulta,
diagnóstico y notificación entre edades y años. El cambio de series de
población DANE entre 2017 y 2018 también puede influir en las tasas. La
comparación anterior y posterior a 2015 es descriptiva: el ASR no mide la
fuerza de infección ni el estado vacunal individual y no atribuye causalidad
a la vacunación.
