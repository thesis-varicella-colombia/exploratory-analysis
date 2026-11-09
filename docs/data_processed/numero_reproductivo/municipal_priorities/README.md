# Municipios prioritarios para analizar Rₜ

Se revisaron las **1.122 entidades municipales**, para fecha de notificación e
inicio de síntomas, durante 2008–2025. La selección siguiente prioriza investigación
retrospectiva de valores extremos; **no es una clasificación de riesgo sanitario
actual ni confirma brotes**. No se modificaron las estimaciones ni las gráficas.

## Criterios

Se usaron los [resultados diarios originales](../rt_stratified/README.md), sin
los promedios de visualización. Para considerar interpretable un día se exigió
el mismo criterio intermedio del [diagnóstico de precisión](../rt_information/README.md):
anchura relativa del intervalo del 95 % ≤1 y aporte formal de la previa ≤10 %
a cada parámetro de la posterior Gamma. Se conservaron también los resultados
con anchuras máximas de 0,5 y 2 para explorar la sensibilidad a ese filtro.

Como umbrales descriptivos se eligieron Rₜ ≥2 para valores altos y Rₜ ≤0,5 para
bajos, con el intervalo completo por encima o por debajo de 1, respectivamente.
Un episodio es una secuencia de días consecutivos que cumplen todas esas
condiciones; no representa una sucesión de observaciones independientes.

Para las señales altas se buscaron episodios de al menos siete días en **ambas
fechas**, separados como máximo por 14 días, y picos recientes ≥5 en ambas fechas
con diferencia máxima de 14 días. Para los descensos de la sección 3 se mantiene
el requisito de 14 días consecutivos en cada fecha. Esa tolerancia solo empareja episodios para revisarlos: no estima ni
corrige la demora de notificación. Ambas series comparten casos y no constituyen
confirmaciones independientes. Los umbrales de magnitud y duración son decisiones
exploratorias, no puntos de corte epidemiológicos validados.

Las dos listas altas comparten **15 municipios**: reúnen **73 municipios distintos**.
Ambas listas se ordenan de mayor a menor por el pico de Rₜ por síntomas.
La página muestra únicamente estas dos listas. Sus [especificaciones de datos](README_data.md)
describen los campos y la selección.

## 1. Señales altas sostenidas en 2022–2025

En la tabla, N significa fecha de notificación y S, inicio de síntomas.
Los picos corresponden al episodio emparejado elegido, no necesariamente al
máximo de todo el período. Todos los días de cada tramo pasan el filtro intermedio.
Son **44 municipios**, con al menos siete días consecutivos en cada fecha.

| Municipio y código | Departamento | Tramo por notificación | Tramo por síntomas | Pico Rₜ N / S | Días consecutivos N / S |
| --- | --- | --- | --- | ---: | ---: |
| CALARCÁ · `63130` | QUINDÍO | 10/03/2022–19/03/2022 | 08/03/2022–16/03/2022 | 14,99 / 15,43 | 10 / 9 |
| VALLE DEL GUAMUEZ · `86865` | PUTUMAYO | 29/04/2023–08/05/2023 | 23/04/2023–30/04/2023 | 13,70 / 12,02 | 10 / 8 |
| EL CARMEN DE BOLÍVAR · `13244` | BOLÍVAR | 29/05/2025–04/06/2025 | 19/05/2025–27/05/2025 | 11,88 / 9,87 | 7 / 9 |
| DUITAMA · `15238` | BOYACÁ | 19/10/2023–01/11/2023 | 18/10/2023–31/10/2023 | 7,60 / 8,65 | 14 / 14 |
| MELGAR · `73449` | TOLIMA | 28/02/2022–07/03/2022 | 24/02/2022–04/03/2022 | 6,09 / 7,38 | 8 / 9 |
| PUERTO GAITÁN · `50568` | META | 12/05/2024–23/05/2024 | 08/05/2024–21/05/2024 | 8,61 / 7,35 | 12 / 14 |
| GIRARDOT · `25307` | CUNDINAMARCA | 10/05/2025–18/05/2025 | 08/05/2025–16/05/2025 | 7,25 / 6,79 | 9 / 9 |
| ALBANIA · `44035` | LA GUAJIRA | 05/04/2024–11/04/2024 | 05/04/2024–12/04/2024 | 7,19 / 6,43 | 7 / 8 |
| RIOHACHA · `44001` | LA GUAJIRA | 15/04/2023–27/04/2023 | 22/03/2023–01/04/2023 | 3,60 / 6,28 | 13 / 11 |
| CICUCO · `13188` | BOLÍVAR | 29/08/2023–06/09/2023 | 26/08/2023–03/09/2023 | 8,85 / 6,07 | 9 / 9 |
| MADRID · `25430` | CUNDINAMARCA | 20/07/2025–01/08/2025 | 21/07/2025–01/08/2025 | 5,32 / 5,80 | 13 / 12 |
| FLORENCIA · `18001` | CAQUETÁ | 11/06/2022–18/06/2022 | 01/06/2022–08/06/2022 | 3,25 / 5,42 | 8 / 8 |
| BARRANCAS · `44078` | LA GUAJIRA | 24/03/2022–05/04/2022 | 22/03/2022–03/04/2022 | 4,96 / 5,38 | 13 / 13 |
| MAGANGUÉ · `13430` | BOLÍVAR | 21/03/2025–01/04/2025 | 19/03/2025–31/03/2025 | 5,13 / 5,30 | 12 / 13 |
| TULUÁ · `76834` | VALLE DEL CAUCA | 29/10/2024–10/11/2024 | 27/10/2024–08/11/2024 | 8,66 / 5,30 | 13 / 13 |
| MANIZALES · `17001` | CALDAS | 13/07/2024–26/07/2024 | 10/07/2024–21/07/2024 | 6,91 / 5,29 | 14 / 12 |
| SABANAGRANDE · `08634` | ATLÁNTICO | 08/04/2024–19/04/2024 | 06/04/2024–18/04/2024 | 8,53 / 5,22 | 12 / 13 |
| IBAGUÉ · `73001` | TOLIMA | 18/08/2025–25/08/2025 | 16/08/2025–27/08/2025 | 2,96 / 5,11 | 8 / 12 |
| POPAYÁN · `19001` | CAUCA | 13/05/2023–26/05/2023 | 09/05/2023–22/05/2023 | 7,05 / 4,60 | 14 / 14 |
| CARTAGO · `76147` | VALLE DEL CAUCA | 22/04/2022–28/04/2022 | 14/04/2022–23/04/2022 | 3,20 / 4,40 | 7 / 10 |
| YOPAL · `85001` | CASANARE | 09/08/2023–28/08/2023 | 06/08/2023–24/08/2023 | 4,19 / 4,32 | 20 / 19 |
| SINCELEJO · `70001` | SUCRE | 20/02/2024–29/02/2024 | 16/02/2024–27/02/2024 | 4,31 / 4,20 | 10 / 12 |
| PALMIRA · `76520` | VALLE DEL CAUCA | 08/01/2024–15/01/2024 | 04/01/2024–11/01/2024 | 4,16 / 4,00 | 8 / 8 |
| GALAPA · `08296` | ATLÁNTICO | 16/09/2023–27/09/2023 | 14/09/2023–21/09/2023 | 4,49 / 3,94 | 12 / 8 |
| AGUACHICA · `20011` | CESAR | 10/09/2025–23/09/2025 | 07/09/2025–18/09/2025 | 4,05 / 3,86 | 14 / 12 |
| SOACHA · `25754` | CUNDINAMARCA | 16/07/2023–25/07/2023 | 10/07/2023–17/07/2023 | 3,55 / 3,65 | 10 / 8 |
| APARTADÓ · `05045` | ANTIOQUIA | 17/08/2022–24/08/2022 | 14/08/2022–23/08/2022 | 6,08 / 3,52 | 8 / 10 |
| TIERRALTA · `23807` | CÓRDOBA | 29/09/2023–08/10/2023 | 26/09/2023–05/10/2023 | 3,33 / 3,38 | 10 / 10 |
| BARANOA · `08078` | ATLÁNTICO | 10/09/2025–18/09/2025 | 06/09/2025–15/09/2025 | 3,49 / 3,37 | 9 / 10 |
| NEIVA · `41001` | HUILA | 17/03/2025–30/03/2025 | 11/03/2025–26/03/2025 | 3,15 / 3,27 | 14 / 16 |
| CARTAGENA DE INDIAS · `13001` | BOLÍVAR | 27/08/2022–03/09/2022 | 24/08/2022–02/09/2022 | 3,31 / 3,21 | 8 / 10 |
| PEREIRA · `66001` | RISARALDA | 09/11/2024–21/11/2024 | 07/11/2024–18/11/2024 | 3,25 / 3,19 | 13 / 12 |
| SAN ANDRÉS · `88001` | ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA | 05/10/2023–19/10/2023 | 25/09/2023–14/10/2023 | 2,77 / 3,16 | 15 / 20 |
| VILLAVICENCIO · `50001` | META | 18/02/2023–26/02/2023 | 16/02/2023–24/02/2023 | 3,04 / 3,07 | 9 / 9 |
| PASTO · `52001` | NARIÑO | 22/02/2022–03/03/2022 | 20/02/2022–05/03/2022 | 3,65 / 2,96 | 10 / 14 |
| MEDELLÍN · `05001` | ANTIOQUIA | 23/04/2024–30/04/2024 | 25/04/2024–06/05/2024 | 2,37 / 2,95 | 8 / 12 |
| MONTERÍA · `23001` | CÓRDOBA | 29/07/2023–11/08/2023 | 17/07/2023–07/08/2023 | 3,25 / 2,89 | 14 / 22 |
| BELLO · `05088` | ANTIOQUIA | 11/04/2024–18/04/2024 | 08/04/2024–14/04/2024 | 3,96 / 2,76 | 8 / 7 |
| SOGAMOSO · `15759` | BOYACÁ | 14/07/2025–24/07/2025 | 14/07/2025–23/07/2025 | 3,09 / 2,67 | 11 / 10 |
| URIBIA · `44847` | LA GUAJIRA | 09/05/2025–21/05/2025 | 28/04/2025–04/05/2025 | 6,45 / 2,50 | 13 / 7 |
| VALLEDUPAR · `20001` | CESAR | 02/10/2025–13/10/2025 | 29/09/2025–07/10/2025 | 3,10 / 2,48 | 12 / 9 |
| BARRANQUILLA · `08001` | ATLÁNTICO | 07/07/2022–14/07/2022 | 03/07/2022–11/07/2022 | 2,92 / 2,44 | 8 / 9 |
| ARMENIA · `63001` | QUINDÍO | 10/08/2023–20/08/2023 | 06/08/2023–12/08/2023 | 2,89 / 2,21 | 11 / 7 |
| BUCARAMANGA · `68001` | SANTANDER | 02/08/2023–11/08/2023 | 01/08/2023–07/08/2023 | 2,54 / 2,09 | 10 / 7 |

Son buenos puntos de partida para contrastar la subida de los conteos, su
distribución por edad, la concentración en pocos días y la demora de notificación.
Las fechas de cada serie y los intervalos en los extremos se conservan en los CSV.
Duitama, además, pasa a valores bajos en noviembre de 2023: aproximadamente 0,35
por notificación y 0,30 por síntomas, lo que permite estudiar la subida y el descenso.

**La selección depende del filtro de precisión.** Con anchura relativa ≤0,5,
solo cuatro de los 44 municipios tienen algún día que cumple en 2022–2025 en
ambas fechas. Esto no implica que todo el episodio seleccionado cumpla ese
límite más exigente; los resultados con límites 0,5, 1 y 2 están en el CSV de resúmenes.

## 2. Picos muy altos recientes: auditar antes de interpretar su magnitud

Estos **44 municipios** tienen picos que pasan el filtro intermedio y son ≥5 en
ambas fechas, con máximos próximos en el tiempo. Pueden corresponder a incrementos
desde un nivel previo muy bajo; un Rₜ grande no implica un gran número absoluto
de casos ni demuestra transmisión local de esa magnitud.

| Municipio y código | Departamento | Fecha del pico N / S | Pico Rₜ N / S |
| --- | --- | --- | ---: |
| PATÍA · `19532` | CAUCA | 05/08/2023 / 04/08/2023 | 28,96 / 40,39 |
| CALARCÁ · `63130` | QUINDÍO | 10/03/2022 / 08/03/2022 | 14,99 / 15,43 |
| PUERTO ESCONDIDO · `23574` | CÓRDOBA | 29/07/2024 / 27/07/2024 | 7,90 / 14,54 |
| ATACO · `73067` | TOLIMA | 31/05/2023 / 25/05/2023 | 13,88 / 12,99 |
| ALCALÁ · `76020` | VALLE DEL CAUCA | 05/08/2022 / 02/08/2022 | 9,59 / 12,94 |
| VALLE DEL GUAMUEZ · `86865` | PUTUMAYO | 29/04/2023 / 23/04/2023 | 13,70 / 12,02 |
| VALLEDUPAR · `20001` | CESAR | 19/07/2022 / 14/07/2022 | 13,96 / 11,31 |
| SANTIAGO DE TOLÚ · `70820` | SUCRE | 23/11/2024 / 22/11/2024 | 11,41 / 10,99 |
| APARTADÓ · `05045` | ANTIOQUIA | 28/05/2022 / 21/05/2022 | 10,46 / 10,27 |
| EL CARMEN DE BOLÍVAR · `13244` | BOLÍVAR | 29/05/2025 / 19/05/2025 | 11,88 / 9,87 |
| CHÁMEZA · `85015` | CASANARE | 03/04/2022 / 29/03/2022 | 12,13 / 9,62 |
| PUERTO CARREÑO · `99001` | VICHADA | 18/09/2024 / 18/09/2024 | 14,87 / 9,47 |
| PALMITO · `70523` | SUCRE | 08/09/2025 / 03/09/2025 | 8,99 / 9,38 |
| SAN SEBASTIÁN DE MARIQUITA · `73443` | TOLIMA | 21/03/2022 / 17/03/2022 | 5,83 / 9,07 |
| GIRARDOT · `25307` | CUNDINAMARCA | 26/02/2022 / 19/02/2022 | 12,50 / 8,85 |
| DUITAMA · `15238` | BOYACÁ | 20/10/2023 / 24/10/2023 | 7,60 / 8,65 |
| CUBARRAL · `50223` | META | 05/06/2023 / 02/06/2023 | 11,20 / 8,62 |
| CHINCHINÁ · `17174` | CALDAS | 08/11/2022 / 01/11/2022 | 6,09 / 8,39 |
| GARZÓN · `41298` | HUILA | 29/04/2023 / 23/04/2023 | 7,35 / 8,12 |
| SAN MARTÍN DE LOBA · `13667` | BOLÍVAR | 05/10/2023 / 03/10/2023 | 6,90 / 8,00 |
| USIACURÍ · `08849` | ATLÁNTICO | 15/08/2023 / 11/08/2023 | 10,35 / 7,95 |
| LA VIRGINIA · `66400` | RISARALDA | 04/04/2022 / 01/04/2022 | 8,72 / 7,86 |
| BUESACO · `52110` | NARIÑO | 29/11/2023 / 27/11/2023 | 6,49 / 7,80 |
| PUERTO GAITÁN · `50568` | META | 12/05/2024 / 17/05/2024 | 8,61 / 7,35 |
| ASTREA · `20032` | CESAR | 21/09/2025 / 15/09/2025 | 8,08 / 7,29 |
| SOCHA · `15757` | BOYACÁ | 30/04/2022 / 25/04/2022 | 6,65 / 7,17 |
| CHÍA · `25175` | CUNDINAMARCA | 15/07/2024 / 12/07/2024 | 5,85 / 7,16 |
| CALAMAR · `95015` | GUAVIARE | 12/07/2023 / 08/07/2023 | 7,89 / 7,16 |
| MADRID · `25430` | CUNDINAMARCA | 17/09/2025 / 16/09/2025 | 7,65 / 7,16 |
| SALDAÑA · `73671` | TOLIMA | 10/03/2025 / 07/03/2025 | 8,33 / 7,13 |
| MORICHAL · `94888` | GUAINÍA | 19/04/2025 / 17/04/2025 | 5,36 / 6,72 |
| LA PRIMAVERA · `99524` | VICHADA | 15/07/2023 / 09/07/2023 | 6,45 / 6,72 |
| COVEÑAS · `70221` | SUCRE | 15/08/2023 / 13/08/2023 | 5,13 / 6,52 |
| RISARALDA · `17616` | CALDAS | 25/03/2022 / 21/03/2022 | 7,32 / 6,50 |
| EL PIÑÓN · `47258` | MAGDALENA | 20/03/2024 / 09/03/2024 | 11,13 / 6,47 |
| ALBANIA · `44035` | LA GUAJIRA | 11/04/2024 / 10/04/2024 | 7,19 / 6,43 |
| PUEBLORRICO · `05576` | ANTIOQUIA | 29/01/2024 / 25/01/2024 | 8,00 / 6,14 |
| CICUCO · `13188` | BOLÍVAR | 29/08/2023 / 26/08/2023 | 8,85 / 6,07 |
| VILLA DE SAN DIEGO DE UBATÉ · `25843` | CUNDINAMARCA | 09/03/2022 / 08/03/2022 | 7,36 / 6,03 |
| SINCELEJO · `70001` | SUCRE | 23/02/2022 / 23/02/2022 | 7,90 / 5,42 |
| TULUÁ · `76834` | VALLE DEL CAUCA | 31/10/2024 / 29/10/2024 | 8,66 / 5,30 |
| MANIZALES · `17001` | CALDAS | 19/07/2024 / 17/07/2024 | 6,91 / 5,29 |
| SABANAGRANDE · `08634` | ATLÁNTICO | 08/04/2024 / 11/04/2024 | 8,53 / 5,22 |
| AGUAZUL · `85010` | CASANARE | 11/08/2023 / 08/08/2023 | 5,74 / 5,16 |

**Patía es el caso más llamativo.** El máximo sin filtrar llega a casi 340, pero
en ese punto la contribución de la previa a la tasa es casi del 100 %, por lo
que se descarta para interpretar su magnitud. Días después aparecen máximos de
28,96 y 40,39 que sí pasan el filtro. Luego, el 15 de agosto, los valores bajan
a 0,25 y 0,22. Es un episodio breve: solo hay 14 y 12 días que pasan el criterio
en todo 2022–2025, por notificación y síntomas, respectivamente.

La auditoría focalizada de sus 85 registros notificados en julio–agosto de 2023
encontró una demora mediana de 0 días y un máximo de 2. Esto hace menos plausible
explicar ese episodio únicamente por una acumulación de notificaciones muy
tardías, aunque no identifica su causa ni descarta otros problemas de registro.

## 3. Valores bajos sostenidos: Bogotá y Cali en 2020

| Municipio y código | Episodio por notificación | Mínimo Rₜ N / S dentro del episodio | Días con Rₜ ≤0,5, N / S |
| --- | --- | ---: | ---: |
| Bogotá, D.C. · `11001` | 28 mar.–14 abr. 2020 | 0,26 / 0,26 | 18 / 20 |
| Santiago de Cali · `76001` | 29 mar.–12 abr. 2020 | 0,22 / 0,19 | 15 / 17 |

Ambas series muestran descensos marcados que pasan el filtro intermedio y duran
al menos 14 días en cada fecha. Son útiles como casos de comparación para el
cambio general de marzo–abril de 2020. La coincidencia con la pandemia no separa
menor transmisión, cambios de consulta, acceso a atención y cambios de vigilancia.
Un valor bajo tampoco demuestra eliminación de la transmisión.

## 4. Cinco revisiones adicionales de anomalías y calidad

- **Jamundí (`76364`, Valle del Cauca), septiembre–octubre de 2017.** El máximo
  por notificación que pasa el filtro es 62,15, seguido por un mínimo de 0,14.
  No hay un episodio alto equivalente por síntomas en esas fechas. De 150
  registros notificados en esos dos meses, 122 tienen una demora superior a 30
  días; la mediana es **149,5 días**. Es prioritario auditar la notificación
  tardía antes de interpretar ese pico como un aumento contemporáneo de transmisión.
- **El Dovio (`76250`, Valle del Cauca), abril–mayo de 2017.** Máximos de 31,08
  por notificación y 19,30 por síntomas, seguidos por valores de 0,43 y 0,32.
  La auditoría de 93 registros notificados en esos meses encuentra demora mediana
  de 6 días; solo uno supera 30 días. Es un extremo histórico presente en ambas
  fechas, con una subida y un descenso rápidos que merecen revisión.
- **Ovejas (`70508`, Sucre), junio de 2013.** Pico por notificación de 31,53 que
  pasa el filtro. La comparación con síntomas está condicionada por la grave
  incompletitud de esa fecha en el archivo de 2013; no se debe interpretar su
  discordancia como ausencia de un episodio.
- **Medellín (`05001`, Antioquia), diciembre de 2008.** Mínimos de 0,052 por
  notificación y 0,063 por síntomas. Bogotá también alcanza 0,047 y 0,022 en ese
  mes. La proximidad a la semana nacional ausente 52 de 2008 hace prioritaria
  la revisión de la caída de registros y del borde del vacío.
- **Barranquilla (`08001`, Atlántico), diciembre de 2024.** Mínimos de 0,31 y 0,40
  por ambas fechas el 23 de diciembre. Los tramos bajos duran 5 y 9 días:
  ameritan revisión, pero no son descensos de al menos 14 días como los anteriores.

Las auditorías de demoras son agregaciones de los CSV individuales locales de
2017 y 2023, con los filtros de residencia y ajuste de las series originales.
Se limitan a los tres conjuntos de registros indicados (Jamundí, El Dovio y Patía);
no constituyen una validación de todos los registros municipales. No se exportan
datos individuales.

## Archivos, reproducción y comprobaciones

- [75 candidatos seleccionados por reglas explícitas, incluidos los dos descensos (CSV)](priority_candidates.csv).
- [Cinco municipios adicionales para revisión (CSV)](quality_review_candidates.csv).
- [Resumen de las 1.122 entidades por fecha y período (CSV)](municipal_summary.csv).
- [Todos los episodios extremos que pasan el filtro (CSV)](qualified_episodes.csv).
- [Episodios sostenidos emparejados entre fechas (CSV)](paired_sustained_episodes.csv).
- [Auditoría focalizada de demoras, sin registros individuales (CSV)](notification_delay_audit.csv).
- [Tablas que carga la página, solo señales altas y picos (JSON)](web_tables.json).
- [Fuentes, parámetros, huellas y criterios (JSON)](metadata.json).

Los códigos deben leerse como texto de cinco dígitos. En los CSV de episodios,
`peak_rt` es un máximo para episodios altos y un mínimo para bajos.
`episode_count` suma los casos fechados durante el tramo: no suma los conteos
de las ventanas móviles ni representa infecciones atribuibles a ese Rₜ.
El resumen incluye los cuatro períodos de la página y el total 2008–2025;
estos resúmenes se solapan y no deben sumarse entre sí.

Generador:
[`scripts/analyze_rt_municipal_priorities.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/analyze_rt_municipal_priorities.py).
Desde la raíz del repositorio:

```bash
.venv/bin/python scripts/analyze_rt_municipal_priorities.py
```

Se revisaron 2.244 series completas, se generaron 11.220 resúmenes y se identificaron
5.676 tramos extremos, incluidos los de un solo día. Los recuentos de días
interpretables coinciden exactamente con las 8.976 combinaciones municipales,
de fecha y período del diagnóstico publicado con límite 1. Para 2022–2025,
121 municipios tienen algún día interpretable por notificación; 1.001 no tienen
ninguno bajo ese criterio. No tener días que pasen el filtro no demuestra ausencia
de enfermedad y no justifica eliminar el municipio del análisis de conteos o tasas.

Las fuentes de las series y los filtros originales se describen en el
[README de Rₜ por territorio](../rt_stratified/README.md) y en el
[README de Sivigila de data-processing](https://github.com/thesis-varicella-colombia/data-processing/tree/main/data/raw/sivigila#esquema-y-diccionario-de-datos).
Los datos originales no se publican allí por su tamaño. La precaución frente a
demoras y cambios de observación sigue a
[Gostic et al. (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7728287/).
