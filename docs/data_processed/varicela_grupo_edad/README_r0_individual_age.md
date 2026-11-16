# Escenario R₀ con edades individuales: especificaciones de los datos

## Archivos y origen

La sección «Número reproductivo básico (R₀): escenario prevacunal» usa
[`r0_individual_age_2008_2025.csv`](r0_individual_age_2008_2025.csv), generado
por [`scripts/generate_r0_individual_age_series.py`](../../../scripts/generate_r0_individual_age_series.py).
El script lee los CSV locales de microdatos de varicela individual del evento
831 de Sivigila, documentados en [`data/sivigila/README.md`](../../../data/sivigila/README.md).
Los microdatos individuales no se publican en este directorio; el archivo
derivado contiene solo agregados nacionales por año epidemiológico.
Si los CSV locales están fuera de este checkout, la ruta se indica con la
variable `SIVIGILA_CSV_DIR` al ejecutar el script.

## Selección y conversión de edad

Se usan las notificaciones entre 2008 y 2025 con municipio de residencia
reconocido y se excluyen los ajustes 6 y D. El año epidemiológico se asigna
desde `FEC_NOT` con la misma regla de semanas que el panel integrado. La edad
de `EDAD` se interpreta según `UNI_MED`: 1 = años, 2 = meses, 3 = días,
4 = horas y 5 = minutos. Se divide por 12, 365,25, 365,25 × 24 o
365,25 × 24 × 60, respectivamente, cuando corresponde. No se usa la edad
agrupada ni una marca de clase. Una edad o unidad ausente o no interpretable
queda fuera del promedio y se cuenta en `unknown_age_cases`.

El script comprueba para cada año que los conteos por los cinco grupos de edad
y los casos sin edad coincidan exactamente con
[`age_group_series_2007_2025.csv`](age_group_series_2007_2025.csv), la serie
ya publicada. Por ello, el nuevo cálculo cambia la precisión de la edad media
sin cambiar la selección de notificaciones.

## Columnas y fórmula

Cada fila representa un año epidemiológico. `known_age_cases` es el número de
notificaciones con edad válida, `unknown_age_cases` el de las demás,
`age_sum_years` la suma de las edades convertidas a años y `mean_age_years`
su cociente. El CSV conserva ocho decimales para la suma y la media; la tabla
visible muestra dos decimales.

Para el año *t*, la edad media es la suma de edades individuales válidas
dividida por el número de notificaciones con edad válida. La referencia
prevacunal es la **media simple de las siete medias anuales de 2008–2014**:
cada año pesa igual. Se excluye 2007 por la discrepancia de registros
documentada para la serie de edad. Esta referencia es 12,7907 años.

Con *L* = 75 años, el proxy ilustrativo es `R₀ = 1 + L / edad_media_prevacunal`:
aproximadamente 6,86. La fracción inmune crítica teórica `1 − 1/R₀` es
85,4 %. Si `N` es la población total, `N_v` el número de vacunados y
`N_prot` el número hipotético de vacunados protegidos contra la infección,
entonces `p = N_v / N` es la cobertura y `ε = N_prot / N_v` es la eficacia
vacunal supuesta bajo un modelo de protección completa en esa fracción.
El modelo supone una fracción protegida `f_protegida = p × ε = N_prot / N`
y un número reproductivo tras vacunar `R_v = R₀ × (1 − p × ε)`.
El valor 1 es la frontera del modelo: por encima, la transmisión puede
sostenerse; por debajo, las cadenas tienden a extinguirse. Se usa `R_v ≤ 1`
para definir el umbral teórico de control, sin que ello garantice ausencia
inmediata de casos ni considere importaciones. La condición equivale a
`p × ε ≥ 1 − 1/R₀`; por tanto, la cobertura crítica es
`p_c = (1 − 1/R₀) / ε`.

Se usan 0,82 y 0,92 como escenarios, aunque las cifras publicadas por los
[CDC](https://www.cdc.gov/vaccines/hcp/by-disease/varicella.html) describen
efectividad frente a varicela clínica, no protección medida contra la
infección en Colombia. Con esos supuestos, las coberturas teóricas
`(1 − 1/R₀) / ε` son 104,2 % y 92,9 %. El corte fijo de 92,7 % empleado en
los resultados municipales de otras secciones se conserva para describir
esos resultados ya calculados; no representa la cobertura teórica de 92,9 %
del escenario R₀ con edades individuales.

## Sensibilidad descriptiva

Las siete medias anuales de edad de 2008–2014 van de 12,45 a 13,08 años.
Al repetir la media de referencia siete veces, omitiendo cada año por turno,
el R₀ proxy con `L = 75` queda entre 6,84 y 6,89.
Estos resultados muestran sensibilidad a la selección de años, no intervalos
de incertidumbre estadística.

Si `L` toma los dos valores quinquenales del DANE que abarcan 2008–2014,
74,00 y 75,22 años, el R₀ proxy varía de 6,79 a 6,88. La cobertura
teórica para ε = 0,82 permanece entre 104,0 % y 104,2 %, mientras que
para ε = 0,92 va de 92,7 % a 92,9 %. Estas comparaciones solo varían
`L`; no cubren los demás supuestos del modelo.

## Interpretación y límites

La fórmula `R₀ = 1 + L/A` y el criterio de control para el número reproductivo
tras vacunar se presentan en Anderson, R. M. y May, R. M. (1983),
«[Vaccination against rubella and measles: quantitative investigations of
different policies](https://doi.org/10.1017/S002217240002893X)»,
*Journal of Hygiene*, 90(2), 259–325, ecuaciones 20 y 13, respectivamente.
Los autores atribuyen la
derivación a [Dietz (1975, ecuación 18)](https://www.stat.cmu.edu/~kass/covid/Dietz1975.pdf).
Esa forma de la relación supone, entre otras cosas, equilibrio endémico,
fuerza de infección constante y mortalidad constante e independiente de la
edad. El mismo artículo muestra otras expresiones para otros modelos de
supervivencia (ecuaciones 21–23).

La edad individual reportada puede estar redondeada, especialmente cuando
`UNI_MED` indica años. Además, la edad de notificación no demuestra que sea
la edad de primera infección, y los casos no notificados no aparecen en la
base. Por eso el resultado sigue siendo un proxy de escenario sujeto a los
supuestos de equilibrio endémico y mezcla homogénea, no una estimación
identificada del R₀ de Colombia ni una meta de cobertura vacunal.
