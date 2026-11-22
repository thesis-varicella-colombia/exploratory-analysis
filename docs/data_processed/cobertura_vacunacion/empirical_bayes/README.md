# Cómo se suavizan las tasas municipales por Empirical Bayes

Los municipios pequeños producen tasas de incidencia inestables: unos pocos
casos sobre una población reducida bastan para que la tasa cruda —y su cociente
respecto a la basal— alcance valores extremos. En el diagnóstico de municipios
prioritarios, de 49 municipios marcados para revisión, 14 tenían 10 o menos
casos sumando los dos años; la basal mediana de ese grupo era de 18 por 100.000,
y el caso extremo (Alejandría, Antioquia, unos 4.700 habitantes) llegaba a un
5.130 % sobre su basal con 30 casos. Esas cifras no reflejan un riesgo real tan
distinto del resto, sino la varianza propia de los números pequeños.

Este análisis estabiliza esa varianza con un estimador **Poisson–Gamma Empirical
Bayes (EB) por grupo de edad**, en **dos variantes** que comparten la misma
mecánica y se diferencian solo en el objetivo hacia el que encogen:

- **Global (nacional):** cada tasa municipal se desplaza hacia la media del país
  en su grupo de edad y año. Es la variante que describen las secciones 2 a 5.
- **Local (vecinos):** cada tasa se desplaza hacia la media de su vecindario —el
  municipio más sus 8 vecinos más cercanos—, de modo que el objetivo de
  encogimiento es regional en lugar de nacional. Es el EB local de Marshall, que
  describe la sección 6.

En ambas, la tasa municipal se mueve en proporción a la poca información que
aporta el municipio: los municipios grandes conservan casi su tasa cruda y los
pequeños se acercan a la media objetivo. El estimador y su encogimiento por el
método de los momentos siguen a [Marshall (1991), *Mapping disease and mortality
rates using Empirical Bayes estimators*, Applied Statistics 40(2):283–294](https://doi.org/10.2307/2347592),
que trata tanto el caso de **encogimiento global** —usado por [GeoDa](https://geodacenter.github.io/workbook/3b_rates/lab3b.html#empirical-bayes-smoothing)
y por [Clayton & Kaldor (1987), Biometrics 43(3):671–681](https://doi.org/10.2307/2532003)—
como el caso de **encogimiento local** por vecindario.

El cálculo lo realiza
[`scripts/smooth_rates_empirical_bayes.py`](../../../../scripts/smooth_rates_empirical_bayes.py)
sobre el panel comparable de 1.102 municipios, con las funciones `eb_global` y
`eb_local`. El archivo de salida trae las dos tasas suavizadas (`rate_eb` y
`rate_eb_local`) con sus respectivos pesos de encogimiento (`shrinkage` y
`shrinkage_local`). Esta ficha explica el modelo y la estimación; las
especificaciones de los archivos están en [`README_data.md`](README_data.md).

## Definiciones y fundamento matemático

### Conteo municipal y distribución Poisson

Dentro de un grupo de edad $g$, sea $O_{gi}$ el número de casos observados en el
municipio $i$ y $n_{gi}$ su población expuesta (personas-año para la basal). La
tasa cruda es

$$
r_{gi}=\frac{O_{gi}}{n_{gi}}.
$$

El modelo trata el conteo como una Poisson con media igual a la población por la
tasa subyacente $\theta_{gi}$, el verdadero riesgo del municipio que no se
observa directamente:

$$
O_{gi}\mid\theta_{gi}\sim\mathrm{Poisson}\!\left(n_{gi}\,\theta_{gi}\right).
$$

Bajo la Poisson, la varianza del conteo es igual a su media. Por eso, cuando
$n_{gi}$ es pequeña, la tasa cruda $r_{gi}=O_{gi}/n_{gi}$ tiene una varianza
grande y ese es el ruido que el estimador busca atenuar.

### Distribución previa Gamma para la tasa subyacente

Las tasas verdaderas $\theta_{gi}$ de los municipios del grupo no son todas
iguales; el modelo las describe como una muestra de una distribución común. Se
elige una **Gamma**, que solo toma valores positivos y es conjugada de la Poisson:

$$
\theta_{gi}\sim\mathrm{Gamma}(\nu,\alpha),
\qquad \nu>0,\quad\alpha>0,
$$

con media y varianza previas

$$
m_g=\mathbb E[\theta_{gi}]=\frac{\nu}{\alpha},
\qquad
\phi_g=\mathrm{Var}(\theta_{gi}).
$$

La interpretación es directa: $m_g$ es la tasa típica del grupo de edad y
$\phi_g$ mide cuánto varía el riesgo real entre municipios (la **varianza entre
áreas**). A diferencia del cálculo de Rₜ, aquí los hiperparámetros no se fijan de
antemano: se estiman a partir de los propios datos del grupo. Por eso el método
es *empírico*.

### Estimador posterior como media ponderada

Con la Poisson y la Gamma, la media posterior de $\theta_{gi}$ es una media
ponderada entre la tasa cruda del municipio y la media del grupo:

$$
\hat\theta_{gi}=C_{gi}\,r_{gi}+(1-C_{gi})\,m_g,
$$

donde el peso $C_{gi}\in[0,1]$ es el **encogimiento**. El estimador no inventa
información: reparte peso entre lo que dice el municipio y lo que dice el grupo,
según cuánta información aporta cada municipio.

## 1. Insumos y conteos

El insumo es el panel municipal completo de 1.102 municipios comparables y los
18 años 2008–2025, construido por `read_panel()` de
[`generate_age_standardized_sir.py`](../../../../scripts/generate_age_standardized_sir.py).
Para cada grupo de edad $g$ (`under_1`, `1_4`, `5_14`, `15_49`, `50_plus`) trae
los conteos observados `observed_<g>` y la población `population_<g>` de cada
municipio y año. La basal 2008–2014 se obtiene sumando esos conteos y la
población de los siete años de referencia por municipio.

El estimador recibe **conteos y poblaciones**, no tasas ya calculadas. La tasa
cruda se deriva como $O_{gi}/n_{gi}$ y se expresa por 100.000.

## 2. Media global y varianza entre áreas por grupo

Dentro de cada grupo de edad —y por separado para cada año anual y para la
basal— se estiman los dos hiperparámetros por el **método de los momentos** de
Marshall sobre las tasas crudas, ponderando por población:

**Media global (tasa agrupada).** Es el total de casos sobre el total de
población del grupo, no el promedio simple de las tasas municipales:

$$
m_g=\frac{\sum_i O_{gi}}{\sum_i n_{gi}}.
$$

**Varianza ponderada de las tasas crudas.** Mide la dispersión observada de las
tasas alrededor de $m_g$, ponderada por población:

$$
s^2_g=\frac{\sum_i n_{gi}\,(r_{gi}-m_g)^2}{\sum_i n_{gi}}.
$$

**Varianza entre áreas.** La varianza observada $s^2_g$ mezcla la variación real
del riesgo con el ruido Poisson. Se descuenta el componente de ruido, que es del
orden de $m_g/\bar n_g$, con $\bar n_g$ la población media del grupo:

$$
\phi_g=\max\!\left(s^2_g-\frac{m_g}{\bar n_g},\ 0\right),
\qquad \bar n_g=\frac{1}{N}\sum_i n_{gi}.
$$

El recorte en cero evita una varianza negativa: si el ruido Poisson explica toda
la dispersión observada, el modelo concluye que no hay señal real entre
municipios y fija $\phi_g=0$.

## 3. Encogimiento y tasa suavizada

Para cada municipio, el peso de encogimiento combina la varianza entre áreas con
la precisión que aporta su población:

$$
C_{gi}=\frac{\phi_g}{\phi_g+\dfrac{m_g}{n_{gi}}}\in[0,1].
$$

La tasa suavizada es la media ponderada del paso anterior, expresada por 100.000:

$$
\hat\theta_{gi}=C_{gi}\,r_{gi}+(1-C_{gi})\,m_g.
$$

Lectura del peso $C_{gi}$:

- **$C_{gi}\approx 1$ (municipio grande o grupo muy heterogéneo):** $m_g/n_{gi}$
  es pequeño frente a $\phi_g$, se confía en el municipio y la tasa suavizada se
  queda cerca de la cruda.
- **$C_{gi}\approx 0$ (municipio pequeño):** $m_g/n_{gi}$ domina, el municipio
  aporta poca información y la tasa se lleva hacia la media del grupo $m_g$.
- **$\phi_g=0$:** el grupo no muestra señal más allá del ruido Poisson; entonces
  $C_{gi}=0$ para todos y cada tasa colapsa a $m_g$.

En el archivo de salida, `shrinkage` es exactamente este $C_{gi}$.

## 4. Por qué se estima por grupo de edad

El estimador empuja cada tasa hacia **una** media global, bajo el supuesto de que
los municipios del conjunto comparten una distribución Gamma común. Mezclar
edades rompería ese supuesto, porque la incidencia de varicela difiere mucho por
edad: en la basal, la media del grupo de 1–4 años es de unos 742 por 100.000 y la
de 50 años o más, de unos 13 por 100.000. Encoger todas las edades hacia una sola
media arrastraría cada grupo hacia un valor que no le corresponde. Por eso $m_g$,
$\phi_g$ y $C_{gi}$ se calculan **por separado dentro de cada grupo de edad**, y
también por separado para cada año anual y para la basal.

## 5. Suavizar la basal y las tasas anuales por separado

La basal 2008–2014 y cada uno de los años 2008–2025 se suavizan como conjuntos
independientes: cada grupo de edad y año tiene su propia media global y su propia
varianza entre áreas. Así la serie anual suavizada cubre todo el período
2008–2025 para la gráfica de evolución, mientras que la lista de municipios lee
los valores de 2024 y 2025. Mantener separados los años y la basal conserva la
comparación coherente —una basal suavizada frente a tasas anuales suavizadas con
el mismo criterio— sin que un periodo imponga su nivel sobre otro. La basal usa
personas-año como denominador, de modo que $m_g$ y $C_{gi}$ incorporan su mayor
exposición acumulada.

## 6. Variante local (vecinos): encogimiento hacia el vecindario

Las secciones 2 a 5 encogen cada municipio hacia **una** media nacional por
grupo de edad. La variante local de Marshall conserva toda esa mecánica, pero
cambia el objetivo: en lugar de un $m_g$ único para el país, cada municipio $i$
tiene su **propia media y su propia varianza entre áreas**, estimadas **dentro de
su vecindario**. Así la tasa suavizada refleja el nivel regional del municipio y
no el del país entero.

### Vecindario: los 8 vecinos más cercanos de la sección 8

El vecindario de un municipio $i$ es el propio $i$ más sus **8 vecinos más
cercanos**. Se reutiliza **la misma matriz de vecindad que la sección 8
(Moran/LISA)**: la que construyen `read_points` y `nearest_neighbors` de
[`generate_moran_lisa.py`](../../../../scripts/generate_moran_lisa.py), con la
distancia *great-circle* entre los puntos representativos de cada municipio.
Usar la misma definición de vecindad mantiene coherentes el suavizado local y el
diagnóstico de autocorrelación espacial. El número de vecinos, 8, queda
registrado en el metadata como `neighbor_count`.

### Media y varianza por vecindario

Sea $J(i)=\{i\}\cup\{\text{8 vecinos de }i\}$ el conjunto del vecindario. El
estimador de momentos de Marshall se aplica **restringido a $J(i)$**, con los
mismos pasos de la sección 2 pero sumando y promediando solo dentro del
vecindario. La **media objetivo local** es la tasa agrupada del vecindario:

$$
m_i=\frac{\sum_{j\in J(i)} O_{gj}}{\sum_{j\in J(i)} n_{gj}}.
$$

La **varianza ponderada** de las tasas crudas del vecindario alrededor de $m_i$,
y la **varianza entre áreas local** descontando el ruido Poisson, son

$$
s^2_i=\frac{\sum_{j\in J(i)} n_{gj}\,(r_{gj}-m_i)^2}{\sum_{j\in J(i)} n_{gj}},
\qquad
\phi_i=\max\!\left(s^2_i-\frac{m_i}{\bar n_i},\ 0\right),
\qquad
\bar n_i=\frac{1}{|J(i)|}\sum_{j\in J(i)} n_{gj}.
$$

### Encogimiento y tasa suavizada local

El peso de encogimiento y la tasa suavizada se calculan como en la sección 3,
pero usando la media y la varianza del vecindario y la población del **municipio
foco** $n_{gi}$:

$$
C^{\mathrm{loc}}_{i}=\frac{\phi_i}{\phi_i+\dfrac{m_i}{n_{gi}}}\in[0,1],
\qquad
\hat\theta^{\mathrm{loc}}_{gi}=C^{\mathrm{loc}}_{i}\,r_{gi}+\bigl(1-C^{\mathrm{loc}}_{i}\bigr)\,m_i.
$$

En el archivo de salida, `rate_eb_local` es $\hat\theta^{\mathrm{loc}}_{gi}$ por
100.000 y `shrinkage_local` es exactamente $C^{\mathrm{loc}}_{i}$.

### Cuándo queda nula

`rate_eb_local` y `shrinkage_local` son **nulas** en dos casos, porque el foco
debe ser válido:

- El municipio **no tiene punto representativo**, de modo que no entra en la
  matriz de vecindad. El metadata lista estos municipios en
  `municipalities_without_point`.
- El **vecindario tiene menos de dos áreas válidas** (el foco con población y
  conteo finitos y positivos, más al menos otro vecino válido). Sin un segundo
  dato no hay varianza entre áreas que estimar.

### Global frente a local: qué cambia y qué no

- **El local estabiliza menos los municipios muy pequeños.** Cada vecindario
  reúne 9 municipios, mucho menos que los más de mil del país, así que $m_i$ y
  $\phi_i$ se estiman con menos datos y el encogimiento hacia el objetivo es
  menos fuerte que en el global. El suavizado local recorta menos los *outliers*.
- **El local no es «más correcto» que el global.** Es una **elección distinta
  del objetivo de encogimiento** —el nivel regional en lugar del nacional— y
  depende de cómo se defina la vecindad (aquí, los 8 vecinos por distancia de la
  sección 8). Cambiar la vecindad cambiaría el resultado.
- **En el agregado nacional ambas variantes coinciden con la tasa cruda
  agregada.** Un agregado no tiene vecindario ni sufre el problema de los números
  pequeños, de modo que no hay nada que encoger.
- **Reordenan los municipios de forma apreciable.** En los 49 municipios de la
  lista de revisión, el EB local reordena unos 37 respecto al global. Por
  ejemplo, Alejandría pasa de un 5.130 % sobre su basal con la tasa cruda a
  1.083 % con el EB nacional y a 1.492 % con el EB de vecinos: el local la deja
  más alta porque la compara con su entorno, no con todo el país.

## Límites e interpretación honesta

El encogimiento EB **estabiliza la varianza; no corrige sesgos**. En concreto:

- **No corrige el subregistro** ni los cambios de vigilancia: si un municipio
  notifica de menos, su tasa cruda y su tasa suavizada estarán ambas sesgadas
  hacia abajo. El estimador solo reparte peso entre municipio y grupo.
- **No corrige errores de denominador.** Una población mal estimada distorsiona
  la tasa cruda y, a través de ella, el encogimiento.
- **Depende del supuesto Gamma** para la distribución de las tasas verdaderas y
  del objetivo de encogimiento (la media nacional en el global, la del vecindario
  en el local). Si ese supuesto no se sostiene, el grado de encogimiento puede no
  ser el adecuado; por eso se estima por grupo de edad. El local añade una
  dependencia extra: la definición de vecindad.
- **Introduce sesgo a cambio de varianza.** Las tasas suavizadas de los
  municipios pequeños están, por diseño, desplazadas hacia la media del grupo.
  Son más estables, no más «verdaderas» caso por caso.

La tasa suavizada sirve para comparar municipios y mapear patrones sin que los
números pequeños dominen la escala. No debe leerse como un recuento corregido ni
como una estimación del riesgo individual de cada municipio pequeño. Para juzgar
cuánto se movió una tasa, conviene mirar `shrinkage` junto a `observed` y
`population`: un encogimiento bajo señala que la tasa suavizada refleja sobre
todo la media del grupo, no los datos del municipio.

## Regeneración

Desde la raíz del repositorio:

```bash
.venv/bin/python scripts/smooth_rates_empirical_bayes.py
```

## Archivos del cálculo

- [`scripts/smooth_rates_empirical_bayes.py`](../../../../scripts/smooth_rates_empirical_bayes.py):
  implementa las dos variantes del estimador Poisson–Gamma por grupo de edad
  —`eb_global` (nacional) y `eb_local` (vecindario)— y genera los dos archivos de
  salida. La variante local reutiliza la matriz de 8 vecinos de
  [`generate_moran_lisa.py`](../../../../scripts/generate_moran_lisa.py). Su
  docstring recoge el modelo y las fórmulas.
- [`municipal_incidence_eb.csv`](municipal_incidence_eb.csv): tasas crudas y
  suavizadas con el peso de encogimiento por municipio, año/basal y grupo de edad.
- [`municipal_incidence_eb.metadata.json`](municipal_incidence_eb.metadata.json):
  modelo, escala, años, municipios, regla de encogimiento, límites y resúmenes
  por grupo.
- [`README_data.md`](README_data.md): especificaciones de las columnas y el
  metadata de los archivos de salida.
