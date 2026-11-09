# Versión reducida para visualizar Rₜ

Generar desde la raíz del repositorio:

```bash
python scripts/reduce_rt_visualization.py
```

El script lee `docs/data_processed/numero_reproductivo/rt_stratified/` y escribe exclusivamente en
`docs/data_processed/numero_reproductivo/rt_visualization/`. No modifica el generador original, sus
estimaciones diarias, los CSV nacionales ni los archivos por edad y territorio.
Se ejecuta después de `generate_rt_stratified.py`; no vuelve a estimar Rₜ.
Puede cambiarse `--source`, `--output`, `--max-days` y `--pixel-error`. Se rechaza
una salida igual al directorio original o situada dentro de él.

La vista general resume bloques de hasta siete días con medias aritméticas de
Rₜ, sus dos límites diarios, los conteos diarios y los casos en ventana de 14
días. No se mezclan tramos separados por ausencia de Rₜ. Se retienen exactamente
los extremos de cada tramo, sus extremos mínimo y máximo en las tres curvas,
y ambos días adyacentes a un cruce del umbral Rₜ = 1.

Los bloques se subdividen cuando la distancia de los puntos originales a la
polilínea resumida supera el límite de error visual. La referencia conservadora
es una vista de 650 × 300 píxeles y el límite por defecto es 0,75 píxeles, con
margen para redondeo. La distancia se comprueba por separado para la media y los
dos límites; no se evalúa solo la línea central. Para inicio de síntomas se usa
el dominio más exigente entre la escala completa y la vista 0–2. El control es
para la vista general: al aumentar mucho el zoom o exportar a mayor resolución,
la aproximación puede hacerse más visible. El detalle de enero de 2013 a marzo
de 2014 mantiene todos sus puntos diarios, sin promediar.

Estos promedios son una aproximación gráfica. Los límites promediados no son un
nuevo intervalo creíble del promedio y no deben usarse como una nueva posterior
para inferencia. Las estimaciones, conteos totales y días con Rₜ publicados en el
catálogo siguen siendo los del análisis diario original.

Cada `{notification,symptom}/{id}.json.gz` contiene:

| Campo | Contenido |
|---|---|
| `offset`, `length` | Posición y longitud de los bloques, codificadas por diferencias |
| `count`, `window_cases` | Promedios diarios dentro del bloque |
| `rt`, `rt_lower_95`, `rt_upper_95` | Promedios de las tres curvas diarias |
| `detail` | Los mismos campos para el detalle diario original de 2013–2014 |
| `reduction` | Número de puntos, tolerancia y error visual máximo observado |

Para reconstruir las fechas, se parte de `cursor = 0`; cada bloque comienza en
`first = cursor + offset`, termina en `last = first + length - 1` y deja
`cursor = last + 1`. El punto se sitúa en el centro temporal `(first + last) / 2`,
que puede caer a mediodía. Los índices remiten al calendario diario compartido
en `manifest.json`. El tooltip muestra las fechas inicial y final del bloque.
Los tramos sin Rₜ se representan con extremos nulos para mantener las
interrupciones; sus días interiores no generan puntos de dibujo.

`manifest.json` conserva los catálogos y los calendarios originales y añade
`visualization` con parámetros, recuentos, tamaños y hashes del catálogo y
generador originales. `source_hashes.json` registra el SHA-256 de cada archivo
diario de entrada. Las pruebas verifican esos hashes, los extremos, los huecos,
los cruces del umbral, la banda y la conservación exacta del detalle diario.
