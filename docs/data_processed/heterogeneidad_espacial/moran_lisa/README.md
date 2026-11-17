# Cómo se calculan la I de Moran global y los clústeres LISA en este análisis

La **I de Moran global** resume, en un solo número por período, si los municipios
con tasas de notificación parecidas tienden a estar cerca unos de otros en el
conjunto del país.

- **I > 0:** municipios vecinos tienen tasas parecidas más de lo esperado bajo una
  reasignación aleatoria; hay asociación espacial positiva.
- **I ≈ 0:** las tasas se distribuyen como si fueran espacialmente independientes.
- **I < 0:** vecinos con tasas contrastantes más de lo esperado al azar.

Los **indicadores locales de asociación espacial (LISA)** de
[Anselin (1995)](https://onlinelibrary.wiley.com/doi/10.1111/j.1538-4632.1995.tb00338.x)
descomponen esa medida global municipio por municipio y comparan la tasa de cada
uno con el promedio de sus vecinos. Clasifican cada municipio en cuatro contrastes
locales: **High–High (HH)** es una tasa alta rodeada de tasas altas; **Low–Low (LL)**,
una tasa baja rodeada de tasas bajas; **High–Low (HL)** y **Low–High (LH)** son
discordancias locales. «Alta» y «baja» se definen respecto de la **media municipal
de cada período**, no por un umbral absoluto de incidencia. El análisis es
descriptivo: no prueba transmisión entre municipios ni atribuye causas.

Este proyecto utiliza una implementación propia en Python, en
[`scripts/generate_moran_lisa.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_moran_lisa.py),
que construye la vecindad, calcula las estadísticas y evalúa su significación por
permutaciones. El [notebook introductorio](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/notebooks/01_moran_global_knn.ipynb)
muestra paso a paso una primera versión de la I de Moran global para un solo año;
no es el cálculo final descrito aquí.

## Definiciones y fundamento matemático

### Tasas, desviaciones y media del período

Sea $n$ el número de municipios incluidos y $x_i$ la tasa de notificación por
100.000 habitantes del municipio $i$ en un período. Las tasas se tratan como
valores observados, no como variables aleatorias del modelo. La media del período es

$$
\bar x=\frac{1}{n}\sum_{i=1}^{n}x_i.
$$

El análisis trabaja con las **desviaciones respecto de esa media**:

$$
d_i=x_i-\bar x.
$$

Un $d_i>0$ indica una tasa por encima del promedio municipal del período; un
$d_i<0$, por debajo. «Alto» y «bajo» se definen siempre respecto de $\bar x$ del
mismo período, de modo que las etiquetas no son comparables entre períodos como
niveles absolutos de incidencia.

### Matriz de pesos espaciales por k vecinos más cercanos

Para cada municipio se toma un **punto interior** de su polígono (el punto
representativo de la geometría). La distancia entre dos municipios es la distancia
de **gran círculo** entre sus puntos, calculada con la fórmula de haversine y un
radio terrestre de 6.371 km (el radio medio estándar de la Tierra). Como el método
solo ordena los municipios por cercanía para quedarse con los ocho más próximos,
el valor del radio fija únicamente las unidades en kilómetros: multiplicar todas
las distancias por una constante no altera ese orden ni, por tanto, la selección
de vecinos.

La **distancia de haversine** es la longitud del arco sobre la superficie de una
esfera entre dos puntos dados por su latitud $\varphi$ y longitud $\lambda$; sigue
la curvatura de la Tierra en lugar de atravesar su interior. Se usa porque los
puntos vienen en coordenadas geográficas: restar grados como si fueran un plano
distorsiona las distancias, ya que un grado de longitud abarca menos kilómetros a
mayor latitud. Con $\Delta\varphi=\varphi_2-\varphi_1$ y $\Delta\lambda=\lambda_2-\lambda_1$:

$$
d=2R\,\arcsin\!\sqrt{\,\sin^2\!\Big(\tfrac{\Delta\varphi}{2}\Big)
+\cos\varphi_1\cos\varphi_2\,\sin^2\!\Big(\tfrac{\Delta\lambda}{2}\Big)} .
$$

El término $\sin^2(\theta/2)$ es la función «haversine» que da nombre a la fórmula,
y $R=6.371$ km es el radio terrestre anterior.

Por ejemplo, el punto interior de Bogotá está en $\varphi_1=4{,}2832^\circ$,
$\lambda_1=-74{,}1754^\circ$ y el de Soacha en $\varphi_2=4{,}5055^\circ$,
$\lambda_2=-74{,}1999^\circ$. Las diferencias son $\Delta\varphi=0{,}2223^\circ$ y
$\Delta\lambda=-0{,}0245^\circ$, que en radianes valen $0{,}003880$ y $-0{,}000428$.
Sustituyendo, $\sin^2(\Delta\varphi/2)\approx3{,}76\times10^{-6}$ domina frente al
término de longitud, y la fórmula da $d\approx 2\times 6.371\times\arcsin\sqrt{3{,}80\times10^{-6}}\approx 24{,}9$ km.
Así, Soacha entra entre los vecinos más cercanos de Bogotá y un municipio a cientos
de kilómetros no.

Cada municipio se conecta con sus $k=8$ **vecinos más cercanos**. Los pesos están
**estandarizados por filas** (row-standardized): cada vecino recibe el mismo peso
$1/k=1/8$ y los demás municipios, peso cero. Un municipio nunca es vecino de sí
mismo ($w_{ii}=0$):

$$
w_{ij}=
\begin{cases}
\dfrac{1}{k}, & \text{si } j \text{ es uno de los } k \text{ vecinos más cercanos de } i,\\[4pt]
0, & \text{en otro caso.}
\end{cases}
\qquad
\sum_{j=1}^{n} w_{ij}=1 .
$$

Esta vecindad depende solo de la geometría, no de las tasas. Por eso la **matriz de
pesos es la misma en los cuatro períodos**: entre períodos solo cambian las tasas
$x_i$. Como la relación «ser uno de los 8 más cercanos» no es simétrica, la matriz
es dirigida: que $j$ sea vecino de $i$ no implica que $i$ lo sea de $j$.

Se usa $k=8$ por cuatro razones:

- **Analogía con la contigüidad «reina».** En una retícula regular cada celda tiene
  ocho vecinos inmediatos (cuatro lados y cuatro esquinas). Con unidades
  irregulares como los municipios, $k=8$ imita ese «vecindario inmediato» sin
  depender de las fronteras compartidas.
- **Equilibrio entre ruido y suavizado.** Un $k$ pequeño hace el rezago espacial
  muy sensible a uno o dos vecinos atípicos; uno grande promedia sobre un área
  amplia y diluye los patrones locales. Ocho es un punto intermedio habitual.
- **Nadie queda aislado.** A diferencia de la contigüidad por frontera, los vecinos
  más cercanos garantizan que todo municipio reciba exactamente ocho vecinos,
  incluidos los insulares o remotos que no comparten límite con otros.
- **Coherencia con el resto del análisis.** Los cálculos espaciales dependientes
  del proyecto reutilizan esta misma geometría de ocho vecinos, de modo que sus
  resultados son comparables entre sí.

Los clústeres **locales** dependen de esta elección y no deben leerse como una
selección territorial invariable: con otra vecindad cambian. La [sensibilidad a la
vecindad del sitio](../../../index.html#spatial-sensitivity-title) repite el cálculo
con tres valores de $k$ (4, 8 y 12 vecinos). En 2022–2025, por ejemplo, hay cero
clústeres HH ajustados con 4 u 8 vecinos y 15 con 12. La I de Moran **global**, en
cambio, permanece positiva con los tres valores de $k$.

El **rezago espacial** de $i$ es el promedio de las desviaciones de sus vecinos:

$$
\text{lag}_i=\sum_{j=1}^{n} w_{ij}\,d_j=\frac{1}{k}\sum_{j\in N(i)} d_j,
$$

donde $N(i)$ es el conjunto de los 8 vecinos de $i$. En el CSV municipal este valor
se publica como `lag_deviation`.

El rezago resume **cómo es el entorno** del municipio frente a la media del período:
$\text{lag}_i>0$ significa vecinos con tasas por encima del promedio (zona de
incidencia alta) y $\text{lag}_i<0$, vecinos por debajo (zona baja). Es el «valor
del vecindario», sin contar al municipio mismo; el nombre «rezago» (del inglés
*spatial lag*) es una analogía con el rezago temporal, pero aquí la referencia es
el espacio, no el tiempo.

### I de Moran global

Con pesos estandarizados por filas, la I de Moran global del período es

$$
I=\frac{\sum_{i=1}^{n}\sum_{j=1}^{n} w_{ij}\,d_i d_j}{\sum_{i=1}^{n} d_i^{2}} .
$$

El denominador $\sum_i d_i^2$ es la suma de cuadrados de las desviaciones; como los
pesos de cada fila suman uno, el factor de normalización habitual $n/\!\sum_i\sum_j w_{ij}$
vale uno y no aparece. Usando el rezago espacial, la expresión implementada es

$$
I=\frac{\sum_{i=1}^{n} d_i\,\text{lag}_i}{\sum_{i=1}^{n} d_i^{2}}
=\frac{\mathbf d^{\top}\mathbf{lag}}{\mathbf d^{\top}\mathbf d},
$$

con $\mathbf d=(d_1,\ldots,d_n)^{\top}$ y $\mathbf{lag}=(\text{lag}_1,\ldots,\text{lag}_n)^{\top}$.
La I queda indefinida si todas las tasas son iguales, porque $\mathbf d^{\top}\mathbf d=0$;
el script interrumpe el cálculo en ese caso. La I global se publica como `global_i`.

Se lee como una correlación, aproximadamente entre $-1$ y $1$, entre la desviación
de cada municipio y la de su entorno. $I>0$ indica **autocorrelación espacial
positiva**: lo alto tiende a estar rodeado de alto y lo bajo de bajo, es decir, la
incidencia se agrupa geográficamente. $I\approx 0$ indica ausencia de patrón
espacial, y $I<0$, el caso infrecuente de vecinos sistemáticamente contrastantes.
Es una medida **de resumen del país entero**: dice *si* hay estructura espacial,
pero no *qué* municipios la forman; eso lo señalan los indicadores locales.

### Indicadores locales LISA

El LISA de cada municipio descompone la I global en una contribución por unidad:

$$
I_i=\frac{d_i\,\text{lag}_i}{\left(\sum_{m=1}^{n} d_m^{2}\right)\big/ n}
=\frac{n\,d_i\,\text{lag}_i}{\mathbf d^{\top}\mathbf d}.
$$

El promedio de los $I_i$ es igual a la I global. Un $I_i$ positivo señala
**concordancia local** (el municipio y sus vecinos se parecen: forma parte de un
clúster); uno negativo, **discordancia** (contrasta con su entorno: es un valor
atípico espacial). El valor se publica como `local_i`.

El **cuadrante** combina el signo de la desviación propia con el del rezago para
decir *de qué tipo* es la señal local:

| Cuadrante | Condición | Lectura |
| --- | --- | --- |
| **HH** | $d_i>0$ y $\text{lag}_i>0$ | foco: tasa alta rodeada de tasas altas |
| **LL** | $d_i<0$ y $\text{lag}_i<0$ | zona fría: tasa baja rodeada de tasas bajas |
| **HL** | $d_i>0$ y $\text{lag}_i<0$ | atípico alto: pico aislado entre vecinos bajos |
| **LH** | $d_i<0$ y $\text{lag}_i>0$ | atípico bajo: hueco entre vecinos altos |

HH y LL corresponden a $I_i>0$ (concordancia, clústeres); HL y LH a $I_i<0$
(discordancia, atípicos). Un municipio con desviación exactamente cero no entra en
ningún cuadrante y se marca como `NS` (sin clúster). En los mapas, cada municipio se
pinta con su cuadrante: así los LISA localizan dónde está el agrupamiento que la I
global solo resume.

### Resumen: cómo encajan rezago, I global e indicadores locales

Las tres medidas parten de la misma desviación $d_i=x_i-\bar x$ (tasa propia frente
a la media del período) y responden preguntas distintas:

| Medida | Columna | Pregunta que responde |
| --- | --- | --- |
| **Rezago espacial** | `lag_deviation` | ¿Cómo es el entorno del municipio? (promedio de sus vecinos) |
| **I de Moran global** | `global_i` | ¿Hay agrupamiento espacial en todo el país? (un número por período) |
| **LISA local** | `local_i` + cuadrante | ¿Dónde está ese agrupamiento, municipio por municipio? |

```
d_i   (¿cómo estoy yo?)   ─┐
                           ├─► I_i local ─► cuadrante ─► mapa (dónde está el clúster)
lag_i (¿cómo es mi        ─┘       │
       entorno?)                   └─ promedio de los I_i ─► I global (¿hay patrón en el país?)
```

Estas etiquetas son **relativas a la media de cada período**, no a un umbral
absoluto de incidencia; por eso no se comparan como niveles entre períodos y un `LL`
puede reflejar subregistro en lugar de menor enfermedad real.

### Significación por permutaciones

No se asume una distribución teórica para $I$. La significación se evalúa
reasignando las tasas al azar y comparando con el valor observado. Todas las
permutaciones usan la semilla fija $2026$, de modo que el resultado es reproducible.

**Global (incondicional, unilateral).** Se baraja el vector completo de
desviaciones y se recalcula la estadística, $B=9.999$ veces. El valor $p$ es la
proporción de barajados cuya estadística iguala o supera la observada, con la
corrección de muestreo de Monte Carlo:

$$
p=\frac{1+\#\{\,I^{*}\ge I\,\}}{B+1}.
$$

Es una **prueba unilateral para asociación positiva**; con $B=9.999$ el valor $p$
mínimo posible es $1/(9.999+1)=0{,}0001$. Se publica como `p_positive`.

**Local (condicional, bilateral).** Para cada municipio focal $i$ se mantiene fija
su propia tasa y se reasignan **sin reemplazo** las de los demás para formar nuevos
conjuntos de 8 vecinos, $B=9.999$ veces. El valor $p$ local es **bilateral**,
porque un clúster puede ser de concordancia ($I_i$ grande positivo) o de
discordancia ($I_i$ grande negativo):

$$
p_i=\frac{1+\#\{\,|I_i^{*}|\ge |I_i|\,\}}{B+1}.
$$

Un municipio con $d_i=0$ no se contrasta y recibe $p_i=1$. Se publica como
`p_two_sided`.

### Ajuste por comparaciones múltiples

**El problema.** Un valor $p\le 0{,}05$ significa que un resultado así de extremo
ocurriría por puro azar solo un 5 % de las veces. Pero aquí no se hace una prueba,
sino **una por cada municipio**: 1.102 pruebas en cada período. Aunque no existiera
ningún clúster real, ese 5 % aplicado a 1.102 municipios produciría del orden de
55 «clústeres» **falsos** solo por azar. Es como lanzar muchas monedas: si pruebas
suficientes, algunas saldrán cara varias veces seguidas sin que estén trucadas.

**La solución.** Se aplica el procedimiento de
[Benjamini–Hochberg (1995)](https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x),
que endurece la exigencia según cuántas pruebas se hagan. En lugar del valor $p$
original, calcula para cada municipio un valor **$q$**, que se interpreta igual
(cuanto menor, más fiable) pero ya tiene en cuenta que se hicieron muchas pruebas a
la vez. Controla la **tasa de falsos descubrimientos**: la proporción esperada de
clústeres señalados que en realidad serían falsas alarmas. El ajuste se hace por
separado dentro de cada período, sobre sus 1.102 valores $p$ locales. El valor $q$
se publica como `q_bh`.

En fórmula: ordenados los valores $p$ de menor a mayor, $p_{(1)}\le\cdots\le p_{(n)}$,
el valor $q$ del municipio en la posición $r$ es

$$
q_{(r)}=\min_{s\ge r}\ \min\!\left(\frac{n}{s}\,p_{(s)},\,1\right).
$$

**El resultado.** Cada municipio se clasifica de dos formas, con el mismo umbral de
$0{,}05$:

- `cluster_nominal`: su cuadrante si $p_i\le 0{,}05$ **sin ajustar**. Son señales
  **exploratorias**: abundantes, pero algunas serán falsas alarmas.
- `cluster_fdr`: su cuadrante si $q_i\le 0{,}05$, es decir, los clústeres que
  **sobreviven al ajuste**. Son más **conservadores y fiables**.

En otro caso el municipio queda como `NS` (sin clúster). Por eso los mapas suelen
mostrar muchos clústeres nominales y pocos (o ninguno) tras el ajuste.

Nota: las pruebas global y locales responden preguntas distintas. La global resume
la estructura del país y las locales señalan municipios concretos. Que no quede
ningún clúster local tras el ajuste en un período **no contradice** una I global
positiva: significa que el país tiene estructura espacial, pero ningún municipio
aislado destaca con suficiente fuerza para resistir la corrección.

## 1. Preparar las tasas municipales por período

Los insumos son dos archivos ya publicados con el sitio:

- [`spatial_series_2008_2025.csv`](../spatial_series_2008_2025.csv): tasas
  municipales por año y por período, con columnas `period`, `code`,
  `notifications`, `population_years`, `years` y `rate_per_100k`. Su construcción
  (notificaciones de varicela por residencia y año epidemiológico, denominadores
  poblacionales y exclusión de 2007) se documenta en el
  [README de la serie municipal](../README_spatial_series.md).
- [`municipal_boundaries_dane.geojson`](../../cartografia/municipal_boundaries_dane.geojson):
  cartografía MGN 2025 del DANE. Solo se usan las entidades con
  `properties.kind == "MUNICIPIO"`, ordenadas por su `code` de cinco dígitos.

Para cada período se recalcula la tasa exacta a partir de los conteos y la
población, en lugar de releer el valor redondeado:

$$
x_i=\frac{\text{notifications}_i}{\text{population\_years}_i}\times 100.000 .
$$

Una fila se incluye solo si `rate_per_100k` no está vacío y `population_years > 0`;
en otro caso se trata como tasa faltante y el municipio no participa en ese período.

Se analizan los cuatro períodos **2008–2014**, **2015–2019**, **2020–2021** y
**2022–2025**.

## 2. Construir la vecindad común

El universo de análisis son los municipios con **tasa válida en los cuatro
períodos y geometría disponible**: la intersección de los conjuntos por período.
Esto deja **1.102 municipios**. El municipio **Nuevo Belén de Bajirá (27493)** se
excluye por no tener tasa válida en todos los períodos.

Con ese universo fijo se calcula una sola matriz de 8 vecinos más cercanos por
gran círculo, que se reutiliza en los cuatro períodos. El script verifica que
ningún municipio aparezca como vecino de sí mismo. Mantener la vecindad constante
permite que las diferencias de la I entre períodos provengan de las tasas y no de
un cambio en la definición de proximidad.

## 3. Calcular Moran global y LISA por período

Para cada período se arma el vector de tasas en el orden común de municipios y se
calculan, con las fórmulas anteriores: la I global y su valor $p$ por permutación
incondicional; los $I_i$ locales, sus valores $p$ bilaterales por permutación
condicional y sus valores $q$ de Benjamini–Hochberg; los cuadrantes y las dos
clasificaciones de clúster. El generador de números aleatorios parte de la semilla
$2026$ una sola vez y avanza a lo largo de todos los períodos.

Los resultados se escriben en dos CSV: un resumen por período
([`moran_global_periods.csv`](../moran_global_periods.csv)) y el detalle municipal
([`moran_lisa_periods.csv`](../moran_lisa_periods.csv)).

## Resultados publicados

El resumen global es:

| Período | Municipios | I de Moran | p global | HH / LL sin ajuste | HH / LL con ajuste |
| --- | --- | --- | --- | --- | --- |
| 2008–2014 | 1.102 | 0,3473 | 0,0001 | 96 / 98 | 51 / 0 |
| 2015–2019 | 1.102 | 0,2580 | 0,0001 | 112 / 101 | 34 / 1 |
| 2020–2021 | 1.102 | 0,1269 | 0,0001 | 53 / 32 | 0 / 0 |
| 2022–2025 | 1.102 | 0,1782 | 0,0001 | 93 / 60 | 0 / 0 |

La I global es positiva y significativa en los cuatro períodos con $p=0{,}0001$
(el mínimo alcanzable con 9.999 permutaciones). Su magnitud observada baja del
período prevacunal (0,3473) a 2015–2019 (0,2580), cae en 2020–2021 (0,1269) y sube
parcialmente en 2022–2025 (0,1782). No se ha probado formalmente si esas diferencias
entre períodos son significativas. Tras el ajuste de Benjamini–Hochberg quedan 51
clústeres HH en 2008–2014, 34 HH y 1 LL en 2015–2019 y ninguno en los dos últimos
períodos con ocho vecinos.

## Interpretación y límites

- **Análisis descriptivo.** La estructura espacial de las tasas notificadas no
  demuestra transmisión entre municipios vecinos ni atribuye los cambios a la
  vacunación. Motiva estudiar cobertura vacunal, clima y características
  territoriales junto con la vigilancia.
- **Global frente a local.** Una I global positiva y la ausencia de clústeres
  locales tras el ajuste no se contradicen: resumen y detalle responden preguntas
  distintas.
- **Tasas bajas.** Un municipio clasificado como LL puede reflejar subregistro o un
  denominador inestable, no necesariamente menor incidencia real.
- **Período 2020–2021.** Tiene la menor I global y menos clústeres nominales que los
  períodos adyacentes; su lectura requiere considerar cambios de movilidad,
  contactos, acceso a servicios y notificación durante la pandemia, no un efecto
  aislado de la vacuna.
- **Clústeres nominales.** Los mapas muestran por defecto `cluster_nominal`
  ($p\le 0{,}05$ sin ajuste), que son exploratorios y abundantes; el selector de la
  página permite ver los que sobreviven al ajuste. Las etiquetas comparan cada
  municipio con la media de su propio período.
- **Sensibilidad a la vecindad.** La [sección de heterogeneidad espacial del sitio](../../../index.html#spatial-sensitivity-title)
  incluye una comprobación breve que repite el cálculo con 4, 8 y 12 vecinos sobre
  el mismo universo. Muestra que la I global permanece positiva pero que los
  clústeres HH locales dependen de la especificación. Esa sensibilidad no cubre
  todavía contigüidad ni suavizado de tasas de municipios pequeños.

## Archivos y scripts del cálculo

Las columnas de los dos CSV de salida se documentan en las
[especificaciones de los datos](README_data.md).

- [`moran_global_periods.csv`](../moran_global_periods.csv): resumen por período (I global, valor $p$ y conteos de clústeres HH/LL con y sin ajuste).
- [`moran_lisa_periods.csv`](../moran_lisa_periods.csv): detalle por municipio y período (tasa, rezago, $I_i$, valores $p$ y $q$, y cuadrante con y sin ajuste).
- [`spatial_series_2008_2025.csv`](../spatial_series_2008_2025.csv): tasas municipales de entrada.
- [`municipal_boundaries_dane.geojson`](../../cartografia/municipal_boundaries_dane.geojson): geometría municipal MGN 2025.
- [`scripts/generate_moran_lisa.py`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/scripts/generate_moran_lisa.py): cálculo completo descrito aquí. Se reproduce con `.venv/bin/python scripts/generate_moran_lisa.py`.
- [`notebooks/01_moran_global_knn.ipynb`](https://github.com/thesis-varicella-colombia/exploratory-analysis/blob/main/notebooks/01_moran_global_knn.ipynb): cuaderno introductorio de la I de Moran global para un solo año.
