# Municipios para revisión: incidencia municipal o infantil y cobertura baja

Actualización: 3 de noviembre de 2026.

La lista incluye a todos los municipios que cumplen cualquiera de los dos criterios completos en 2024 y 2025, sin duplicados. El primer criterio evalúa la tasa municipal total ajustada; ya no exige superar límites en los cinco grupos por separado.

## Criterios

1. **Municipal:** incidencia total ajustada por edad >0,95 × su propia basal de 2008–2014, tanto en 2024 como en 2025. Se usan los mismos pesos nacionales del panel de 2008–2014 en las tasas anuales y basales, publicados en comparable_incidence_annual.csv.
2. **Infantil:** incidencia específica >0,8 × su propia basal en cada uno de los grupos <1, 1–4 y 5–14 años, tanto en 2024 como en 2025. La basal por municipio y edad es 100.000 × suma de casos / suma de poblaciones anuales de ese grupo durante 2008–2014.
3. **Cobertura común:** debe existir alguna medida administrativa o calculada <80 % en cada año. Puede ser una medida o dosis distinta entre 2024 y 2025. La calculada usa población de 1 año para primera dosis y de 5 años para segunda, conservando el desplazamiento de año de la fuente.

Los límites son estrictos. Se aplica AND entre 2024 y 2025 dentro de cada criterio, y luego OR entre criterios completos. No basta cumplir solo el municipal en 2024 y solo el infantil en 2025. El conjunto municipal ya no es necesariamente subconjunto del infantil.

## Resultado

De 1102 municipios comparables, 48 cumplen el criterio municipal y 7 el infantil. Hay 6 en ambos y **49 municipios únicos** en la unión.

Orden: primero quienes cumplen el criterio infantil (incluidos los que cumplen ambos), después quienes cumplen solo el municipal. Dentro de cada grupo se ordena por el menor porcentaje calculable respecto a la basal: mínimo de las seis comparaciones infantiles o de las dos municipales, respectivamente. Basales cero no generan porcentajes; se omiten del mínimo y, si ninguno es calculable, la fila va al final de su grupo. Este orden descriptivo no es una clasificación inferencial de riesgo.

| Municipio | Departamento | Grupo de orden | Menor % de basal | Referencia del porcentaje | Casos 2024–2025 | Municipal >95 % | Infantil >80 % |
|---|---|---|---:|---|---:|---|---|
| FONSECA (44279) | LA GUAJIRA | Infantil | 96,18 | 1–4 años · 2025 | 42 | Sí | Sí |
| QUIBDÓ (27001) | CHOCÓ | Infantil | 100,51 | 5–14 años · 2025 | 54 | No | Sí |
| PLANETA RICA (23555) | CÓRDOBA | Infantil | 101,28 | Menores de 1 año · 2025 | 113 | Sí | Sí |
| PALMITO (70523) | SUCRE | Infantil | 109,33 | 5–14 años · 2024 | 81 | Sí | Sí |
| SAN MARTÍN (20770) | CESAR | Infantil | 109,75 | 1–4 años · 2024 | 51 | Sí | Sí |
| PATÍA (19532) | CAUCA | Infantil | 113,37 | 5–14 años · 2025 | 77 | Sí | Sí |
| ARJONA (13052) | BOLÍVAR | Infantil | 162,92 | 5–14 años · 2025 | 89 | Sí | Sí |
| SANTA MARÍA (15690) | BOYACÁ | Municipal | 95,23 | Municipal ajustada · 2024 | 3 | Sí | No |
| JAMUNDÍ (76364) | VALLE DEL CAUCA | Municipal | 96,90 | Municipal ajustada · 2024 | 257 | Sí | No |
| PRADO (73563) | TOLIMA | Municipal | 97,80 | Municipal ajustada · 2025 | 15 | Sí | No |
| LA PRIMAVERA (99524) | VICHADA | Municipal | 98,22 | Municipal ajustada · 2025 | 36 | Sí | No |
| PUERTO TRIUNFO (05591) | ANTIOQUIA | Municipal | 100,56 | Municipal ajustada · 2025 | 33 | Sí | No |
| SANTA ANA (47707) | MAGDALENA | Municipal | 100,67 | Municipal ajustada · 2025 | 52 | Sí | No |
| PONEDERA (08560) | ATLÁNTICO | Municipal | 102,46 | Municipal ajustada · 2024 | 21 | Sí | No |
| CHINÚ (23182) | CÓRDOBA | Municipal | 107,97 | Municipal ajustada · 2024 | 71 | Sí | No |
| LA JAGUA DE IBIRICO (20400) | CESAR | Municipal | 111,89 | Municipal ajustada · 2024 | 25 | Sí | No |
| ALTO BAUDÓ (27025) | CHOCÓ | Municipal | 112,67 | Municipal ajustada · 2025 | 4 | Sí | No |
| SAN JOSÉ DE URÉ (23682) | CÓRDOBA | Municipal | 114,30 | Municipal ajustada · 2024 | 12 | Sí | No |
| LORICA (23417) | CÓRDOBA | Municipal | 114,87 | Municipal ajustada · 2025 | 156 | Sí | No |
| CLEMENCIA (13222) | BOLÍVAR | Municipal | 119,07 | Municipal ajustada · 2025 | 22 | Sí | No |
| TIMBÍO (19807) | CAUCA | Municipal | 126,74 | Municipal ajustada · 2025 | 22 | Sí | No |
| BAJO BAUDÓ (27077) | CHOCÓ | Municipal | 137,50 | Municipal ajustada · 2025 | 17 | Sí | No |
| SAN VICENTE FERRER (05674) | ANTIOQUIA | Municipal | 145,81 | Municipal ajustada · 2025 | 5 | Sí | No |
| MOÑITOS (23500) | CÓRDOBA | Municipal | 151,06 | Municipal ajustada · 2025 | 48 | Sí | No |
| SAN JACINTO (13654) | BOLÍVAR | Municipal | 152,60 | Municipal ajustada · 2024 | 38 | Sí | No |
| SITIONUEVO (47745) | MAGDALENA | Municipal | 156,26 | Municipal ajustada · 2025 | 22 | Sí | No |
| TIBANÁ (15804) | BOYACÁ | Municipal | 159,14 | Municipal ajustada · 2025 | 16 | Sí | No |
| LA GLORIA (20383) | CESAR | Municipal | 163,94 | Municipal ajustada · 2025 | 25 | Sí | No |
| AGUACHICA (20011) | CESAR | Municipal | 164,83 | Municipal ajustada · 2024 | 186 | Sí | No |
| SANTA CATALINA (13673) | BOLÍVAR | Municipal | 175,59 | Municipal ajustada · 2025 | 13 | Sí | No |
| CHIMÁ (23168) | CÓRDOBA | Municipal | 178,22 | Municipal ajustada · 2025 | 11 | Sí | No |
| TADÓ (27787) | CHOCÓ | Municipal | 190,93 | Municipal ajustada · 2025 | 20 | Sí | No |
| MUTATÁ (05480) | ANTIOQUIA | Municipal | 211,87 | Municipal ajustada · 2025 | 8 | Sí | No |
| PAJARITO (15518) | BOYACÁ | Municipal | 220,57 | Municipal ajustada · 2025 | 3 | Sí | No |
| ARACATACA (47053) | MAGDALENA | Municipal | 223,58 | Municipal ajustada · 2024 | 9 | Sí | No |
| MIRAFLORES (15455) | BOYACÁ | Municipal | 246,46 | Municipal ajustada · 2025 | 9 | Sí | No |
| BELÉN DE UMBRÍA (66088) | RISARALDA | Municipal | 279,39 | Municipal ajustada · 2024 | 76 | Sí | No |
| GAMARRA (20295) | CESAR | Municipal | 286,59 | Municipal ajustada · 2025 | 7 | Sí | No |
| CONFINES (68209) | SANTANDER | Municipal | 293,57 | Municipal ajustada · 2024 | 13 | Sí | No |
| LA VICTORIA (76403) | VALLE DEL CAUCA | Municipal | 398,77 | Municipal ajustada · 2024 | 5 | Sí | No |
| JUAN DE ACOSTA (08372) | ATLÁNTICO | Municipal | 427,08 | Municipal ajustada · 2024 | 44 | Sí | No |
| SAN SEBASTIÁN DE BUENAVISTA (47692) | MAGDALENA | Municipal | 438,70 | Municipal ajustada · 2024 | 25 | Sí | No |
| RIOFRÍO (76616) | VALLE DEL CAUCA | Municipal | 447,19 | Municipal ajustada · 2025 | 7 | Sí | No |
| BUSBANZÁ (15114) | BOYACÁ | Municipal | 556,84 | Municipal ajustada · 2024 | 3 | Sí | No |
| TALAIGUA NUEVO (13780) | BOLÍVAR | Municipal | 666,31 | Municipal ajustada · 2024 | 5 | Sí | No |
| MARGARITA (13440) | BOLÍVAR | Municipal | 680,86 | Municipal ajustada · 2025 | 3 | Sí | No |
| EL ÁGUILA (76243) | VALLE DEL CAUCA | Municipal | 1103,74 | Municipal ajustada · 2025 | 27 | Sí | No |
| REMOLINO (47605) | MAGDALENA | Municipal | 1527,13 | Municipal ajustada · 2025 | 10 | Sí | No |
| ALEJANDRÍA (05021) | ANTIOQUIA | Municipal | 5130,44 | Municipal ajustada · 2025 | 30 | Sí | No |

## Tasas usadas en la selección

| Municipio | Medida | Basal 2008–2014 | 2024 | 2025 |
|---|---|---:|---:|---:|
| FONSECA | Municipal total ajustada | 27,80 | 33,46 | 40,39 |
| FONSECA | Menores de 1 año | 47,30 | 197,24 | 98,33 |
| FONSECA | 1–4 años | 76,53 | 98,64 | 73,60 |
| FONSECA | 5–14 años | 28,50 | 86,75 | 57,41 |
| QUIBDÓ | Municipal total ajustada | 17,92 | 25,40 | 12,21 |
| QUIBDÓ | Menores de 1 año | 19,39 | 37,09 | 74,77 |
| QUIBDÓ | 1–4 años | 24,73 | 29,11 | 38,99 |
| QUIBDÓ | 5–14 años | 19,34 | 61,66 | 19,44 |
| PLANETA RICA | Municipal total ajustada | 48,12 | 121,06 | 55,83 |
| PLANETA RICA | Menores de 1 año | 88,32 | 437,45 | 89,45 |
| PLANETA RICA | 1–4 años | 83,49 | 193,17 | 152,94 |
| PLANETA RICA | 5–14 años | 68,02 | 142,92 | 76,58 |
| PALMITO | Municipal total ajustada | 46,68 | 100,86 | 371,42 |
| PALMITO | Menores de 1 año | 49,68 | 334,45 | 2675,59 |
| PALMITO | 1–4 años | 75,49 | 648,30 | 2522,38 |
| PALMITO | 5–14 años | 84,10 | 91,94 | 243,75 |
| SAN MARTÍN | Municipal total ajustada | 28,75 | 73,53 | 74,59 |
| SAN MARTÍN | Menores de 1 año | 56,80 | 180,51 | 179,21 |
| SAN MARTÍN | 1–4 años | 79,41 | 87,15 | 216,83 |
| SAN MARTÍN | 5–14 años | 35,12 | 243,11 | 80,31 |
| PATÍA | Municipal total ajustada | 24,54 | 98,19 | 109,74 |
| PATÍA | Menores de 1 año | 50,97 | 394,48 | 796,81 |
| PATÍA | 1–4 años | 110,49 | 186,83 | 141,91 |
| PATÍA | 5–14 años | 41,92 | 62,43 | 47,53 |
| ARJONA | Municipal total ajustada | 15,83 | 84,51 | 40,99 |
| ARJONA | Menores de 1 año | 0,00 | 83,40 | 255,97 |
| ARJONA | 1–4 años | 31,70 | 59,00 | 60,47 |
| ARJONA | 5–14 años | 13,68 | 51,78 | 22,29 |
| SANTA MARÍA | Municipal total ajustada | 37,55 | 35,76 | 64,40 |
| SANTA MARÍA | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| SANTA MARÍA | 1–4 años | 208,77 | 0,00 | 0,00 |
| SANTA MARÍA | 5–14 años | 19,77 | 194,55 | 0,00 |
| JAMUNDÍ | Municipal total ajustada | 58,97 | 57,15 | 88,91 |
| JAMUNDÍ | Menores de 1 año | 98,97 | 74,18 | 148,48 |
| JAMUNDÍ | 1–4 años | 174,74 | 134,52 | 377,36 |
| JAMUNDÍ | 5–14 años | 136,04 | 80,64 | 117,09 |
| PRADO | Municipal total ajustada | 28,89 | 180,27 | 28,25 |
| PRADO | Menores de 1 año | 0,00 | 819,67 | 833,33 |
| PRADO | 1–4 años | 98,06 | 1183,43 | 0,00 |
| PRADO | 5–14 años | 60,09 | 75,30 | 76,39 |
| LA PRIMAVERA | Municipal total ajustada | 146,25 | 172,48 | 143,64 |
| LA PRIMAVERA | Menores de 1 año | 561,80 | 529,10 | 0,00 |
| LA PRIMAVERA | 1–4 años | 416,61 | 251,57 | 890,59 |
| LA PRIMAVERA | 5–14 años | 152,58 | 433,09 | 87,72 |
| PUERTO TRIUNFO | Municipal total ajustada | 71,89 | 84,72 | 72,29 |
| PUERTO TRIUNFO | Menores de 1 año | 219,30 | 283,29 | 0,00 |
| PUERTO TRIUNFO | 1–4 años | 123,50 | 0,00 | 73,15 |
| PUERTO TRIUNFO | 5–14 años | 156,56 | 30,46 | 61,50 |
| SANTA ANA | Municipal total ajustada | 67,06 | 114,19 | 67,51 |
| SANTA ANA | Menores de 1 año | 140,70 | 178,89 | 0,00 |
| SANTA ANA | 1–4 años | 105,56 | 0,00 | 88,07 |
| SANTA ANA | 5–14 años | 153,33 | 254,15 | 51,07 |
| PONEDERA | Municipal total ajustada | 28,72 | 29,43 | 45,84 |
| PONEDERA | Menores de 1 año | 58,09 | 198,02 | 198,41 |
| PONEDERA | 1–4 años | 51,61 | 0,00 | 296,44 |
| PONEDERA | 5–14 años | 53,80 | 19,37 | 19,40 |
| CHINÚ | Municipal total ajustada | 56,57 | 61,08 | 83,98 |
| CHINÚ | Menores de 1 año | 39,53 | 126,58 | 385,11 |
| CHINÚ | 1–4 años | 105,93 | 125,08 | 380,59 |
| CHINÚ | 5–14 años | 103,36 | 49,39 | 12,43 |
| LA JAGUA DE IBIRICO | Municipal total ajustada | 10,54 | 11,79 | 27,15 |
| LA JAGUA DE IBIRICO | Menores de 1 año | 15,02 | 80,52 | 161,03 |
| LA JAGUA DE IBIRICO | 1–4 años | 15,27 | 0,00 | 80,53 |
| LA JAGUA DE IBIRICO | 5–14 años | 14,73 | 15,84 | 7,90 |
| ALTO BAUDÓ | Municipal total ajustada | 4,49 | 5,92 | 5,06 |
| ALTO BAUDÓ | Menores de 1 año | 20,72 | 0,00 | 0,00 |
| ALTO BAUDÓ | 1–4 años | 5,40 | 32,89 | 0,00 |
| ALTO BAUDÓ | 5–14 años | 9,58 | 0,00 | 27,53 |
| SAN JOSÉ DE URÉ | Municipal total ajustada | 11,83 | 13,52 | 64,69 |
| SAN JOSÉ DE URÉ | Menores de 1 año | 85,25 | 0,00 | 0,00 |
| SAN JOSÉ DE URÉ | 1–4 años | 34,34 | 79,18 | 79,30 |
| SAN JOSÉ DE URÉ | 5–14 años | 11,00 | 0,00 | 53,33 |
| LORICA | Municipal total ajustada | 50,02 | 78,29 | 57,45 |
| LORICA | Menores de 1 año | 132,51 | 150,08 | 50,99 |
| LORICA | 1–4 años | 102,04 | 86,71 | 63,01 |
| LORICA | 5–14 años | 95,28 | 93,47 | 69,63 |
| CLEMENCIA | Municipal total ajustada | 49,15 | 74,73 | 58,52 |
| CLEMENCIA | Menores de 1 año | 144,37 | 325,73 | 662,25 |
| CLEMENCIA | 1–4 años | 96,18 | 234,93 | 238,85 |
| CLEMENCIA | 5–14 años | 86,75 | 31,28 | 62,40 |
| TIMBÍO | Municipal total ajustada | 23,83 | 33,70 | 30,20 |
| TIMBÍO | Menores de 1 año | 152,77 | 197,24 | 0,00 |
| TIMBÍO | 1–4 años | 72,22 | 0,00 | 97,99 |
| TIMBÍO | 5–14 años | 53,12 | 34,93 | 70,70 |
| BAJO BAUDÓ | Municipal total ajustada | 2,99 | 48,23 | 4,11 |
| BAJO BAUDÓ | Menores de 1 año | 39,82 | 116,55 | 0,00 |
| BAJO BAUDÓ | 1–4 años | 5,12 | 28,45 | 0,00 |
| BAJO BAUDÓ | 5–14 años | 0,00 | 22,59 | 0,00 |
| SAN VICENTE FERRER | Municipal total ajustada | 4,11 | 17,66 | 5,99 |
| SAN VICENTE FERRER | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| SAN VICENTE FERRER | 1–4 años | 9,66 | 0,00 | 86,58 |
| SAN VICENTE FERRER | 5–14 años | 3,57 | 28,07 | 0,00 |
| MOÑITOS | Municipal total ajustada | 15,52 | 119,65 | 23,45 |
| MOÑITOS | Menores de 1 año | 48,39 | 168,35 | 0,00 |
| MOÑITOS | 1–4 años | 12,27 | 81,07 | 204,75 |
| MOÑITOS | 5–14 años | 19,63 | 255,72 | 0,00 |
| SAN JACINTO | Municipal total ajustada | 44,11 | 67,31 | 82,11 |
| SAN JACINTO | Menores de 1 año | 165,56 | 0,00 | 0,00 |
| SAN JACINTO | 1–4 años | 97,67 | 56,82 | 398,18 |
| SAN JACINTO | 5–14 años | 69,26 | 63,63 | 85,00 |
| SITIONUEVO | Municipal total ajustada | 21,73 | 41,99 | 33,96 |
| SITIONUEVO | Menores de 1 año | 26,39 | 0,00 | 187,27 |
| SITIONUEVO | 1–4 años | 20,09 | 0,00 | 90,91 |
| SITIONUEVO | 5–14 años | 46,43 | 50,94 | 17,18 |
| TIBANÁ | Municipal total ajustada | 44,82 | 154,56 | 71,33 |
| TIBANÁ | Menores de 1 año | 281,69 | 0,00 | 0,00 |
| TIBANÁ | 1–4 años | 70,37 | 604,84 | 205,34 |
| TIBANÁ | 5–14 años | 128,11 | 227,62 | 233,46 |
| LA GLORIA | Municipal total ajustada | 15,81 | 100,85 | 25,92 |
| LA GLORIA | Menores de 1 año | 45,13 | 0,00 | 0,00 |
| LA GLORIA | 1–4 años | 34,11 | 137,08 | 0,00 |
| LA GLORIA | 5–14 años | 23,53 | 182,72 | 0,00 |
| AGUACHICA | Municipal total ajustada | 21,77 | 35,88 | 102,55 |
| AGUACHICA | Menores de 1 año | 80,06 | 44,11 | 530,74 |
| AGUACHICA | 1–4 años | 59,70 | 32,78 | 601,95 |
| AGUACHICA | 5–14 años | 20,24 | 16,39 | 65,45 |
| SANTA CATALINA | Municipal total ajustada | 15,90 | 59,29 | 27,91 |
| SANTA CATALINA | Menores de 1 año | 52,97 | 0,00 | 0,00 |
| SANTA CATALINA | 1–4 años | 0,00 | 93,37 | 95,33 |
| SANTA CATALINA | 5–14 años | 20,68 | 0,00 | 0,00 |
| CHIMÁ | Municipal total ajustada | 12,81 | 39,92 | 22,82 |
| CHIMÁ | Menores de 1 año | 103,41 | 0,00 | 0,00 |
| CHIMÁ | 1–4 años | 0,00 | 87,80 | 88,42 |
| CHIMÁ | 5–14 años | 20,62 | 0,00 | 0,00 |
| TADÓ | Municipal total ajustada | 2,13 | 100,95 | 4,07 |
| TADÓ | Menores de 1 año | 33,27 | 237,53 | 238,66 |
| TADÓ | 1–4 años | 8,54 | 0,00 | 0,00 |
| TADÓ | 5–14 años | 0,00 | 98,11 | 0,00 |
| MUTATÁ | Municipal total ajustada | 10,22 | 34,62 | 21,66 |
| MUTATÁ | Menores de 1 año | 0,00 | 0,00 | 401,61 |
| MUTATÁ | 1–4 años | 31,21 | 92,00 | 0,00 |
| MUTATÁ | 5–14 años | 17,73 | 32,57 | 0,00 |
| PAJARITO | Municipal total ajustada | 22,89 | 102,43 | 50,49 |
| PAJARITO | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| PAJARITO | 1–4 años | 77,04 | 1481,48 | 0,00 |
| PAJARITO | 5–14 años | 62,54 | 0,00 | 0,00 |
| ARACATACA | Municipal total ajustada | 2,08 | 4,65 | 14,41 |
| ARACATACA | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| ARACATACA | 1–4 años | 3,96 | 0,00 | 60,02 |
| ARACATACA | 5–14 años | 5,02 | 0,00 | 30,82 |
| MIRAFLORES | Municipal total ajustada | 11,40 | 101,68 | 28,09 |
| MIRAFLORES | Menores de 1 año | 115,74 | 0,00 | 0,00 |
| MIRAFLORES | 1–4 años | 84,48 | 0,00 | 0,00 |
| MIRAFLORES | 5–14 años | 19,49 | 415,63 | 84,18 |
| BELÉN DE UMBRÍA | Municipal total ajustada | 50,72 | 141,69 | 236,18 |
| BELÉN DE UMBRÍA | Menores de 1 año | 232,83 | 1875,00 | 1273,89 |
| BELÉN DE UMBRÍA | 1–4 años | 150,97 | 1194,92 | 1679,39 |
| BELÉN DE UMBRÍA | 5–14 años | 117,37 | 52,49 | 293,41 |
| GAMARRA | Municipal total ajustada | 7,14 | 24,93 | 20,47 |
| GAMARRA | Menores de 1 año | 116,41 | 0,00 | 803,21 |
| GAMARRA | 1–4 años | 28,47 | 0,00 | 98,04 |
| GAMARRA | 5–14 años | 5,46 | 0,00 | 0,00 |
| CONFINES | Municipal total ajustada | 64,99 | 190,79 | 213,18 |
| CONFINES | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| CONFINES | 1–4 años | 131,32 | 0,00 | 0,00 |
| CONFINES | 5–14 años | 54,60 | 875,66 | 524,48 |
| LA VICTORIA | Municipal total ajustada | 4,84 | 19,28 | 32,53 |
| LA VICTORIA | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| LA VICTORIA | 1–4 años | 18,55 | 0,00 | 192,31 |
| LA VICTORIA | 5–14 años | 6,32 | 0,00 | 0,00 |
| JUAN DE ACOSTA | Municipal total ajustada | 19,26 | 82,24 | 106,04 |
| JUAN DE ACOSTA | Menores de 1 año | 0,00 | 0,00 | 265,96 |
| JUAN DE ACOSTA | 1–4 años | 40,86 | 196,98 | 328,95 |
| JUAN DE ACOSTA | 5–14 años | 20,26 | 151,21 | 50,47 |
| SAN SEBASTIÁN DE BUENAVISTA | Municipal total ajustada | 10,19 | 44,71 | 67,17 |
| SAN SEBASTIÁN DE BUENAVISTA | Menores de 1 año | 0,00 | 0,00 | 717,70 |
| SAN SEBASTIÁN DE BUENAVISTA | 1–4 años | 36,08 | 226,24 | 114,55 |
| SAN SEBASTIÁN DE BUENAVISTA | 5–14 años | 21,73 | 21,35 | 86,45 |
| RIOFRÍO | Municipal total ajustada | 4,58 | 28,52 | 20,50 |
| RIOFRÍO | Menores de 1 año | 106,44 | 0,00 | 406,50 |
| RIOFRÍO | 1–4 años | 0,00 | 0,00 | 196,27 |
| RIOFRÍO | 5–14 años | 4,65 | 37,85 | 0,00 |
| BUSBANZÁ | Municipal total ajustada | 13,07 | 72,78 | 145,56 |
| BUSBANZÁ | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| BUSBANZÁ | 1–4 años | 189,04 | 1052,63 | 2105,26 |
| BUSBANZÁ | 5–14 años | 0,00 | 0,00 | 0,00 |
| TALAIGUA NUEVO | Municipal total ajustada | 1,07 | 7,16 | 26,90 |
| TALAIGUA NUEVO | Menores de 1 año | 0,00 | 0,00 | 0,00 |
| TALAIGUA NUEVO | 1–4 años | 0,00 | 0,00 | 0,00 |
| TALAIGUA NUEVO | 5–14 años | 0,00 | 0,00 | 32,12 |
| MARGARITA | Municipal total ajustada | 1,26 | 16,97 | 8,58 |
| MARGARITA | Menores de 1 año | 73,91 | 0,00 | 0,00 |
| MARGARITA | 1–4 años | 0,00 | 245,40 | 124,07 |
| MARGARITA | 5–14 años | 0,00 | 0,00 | 0,00 |
| EL ÁGUILA | Municipal total ajustada | 8,80 | 223,23 | 97,18 |
| EL ÁGUILA | Menores de 1 año | 0,00 | 719,42 | 0,00 |
| EL ÁGUILA | 1–4 años | 18,59 | 1369,86 | 696,86 |
| EL ÁGUILA | 5–14 años | 0,00 | 357,78 | 60,61 |
| REMOLINO | Municipal total ajustada | 1,40 | 51,27 | 21,44 |
| REMOLINO | Menores de 1 año | 0,00 | 414,94 | 413,22 |
| REMOLINO | 1–4 años | 0,00 | 102,77 | 102,46 |
| REMOLINO | 5–14 años | 0,00 | 0,00 | 0,00 |
| ALEJANDRÍA | Municipal total ajustada | 3,32 | 488,42 | 170,40 |
| ALEJANDRÍA | Menores de 1 año | 0,00 | 1063,83 | 0,00 |
| ALEJANDRÍA | 1–4 años | 0,00 | 547,95 | 549,45 |
| ALEJANDRÍA | 5–14 años | 0,00 | 1868,00 | 126,26 |

## Alcance

- Preselección exploratoria sin intervalos municipales; no es una clasificación concluyente de riesgo ni demuestra efecto de la vacuna. No restringe automáticamente el universo del modelo.
- La tasa municipal ajustada excluye notificaciones sin edad conocida. Los grupos infantiles usan sus propios casos y poblaciones; no se reparte artificialmente la edad desconocida.
- Basal cero exige incidencia positiva mediante comparación directa. Población ausente o no positiva deja la tasa sin dato y no cumple ese criterio; otro criterio completo puede permitir entrar.
- Cobertura administrativa fuera de 0–100 % y faltantes no se consideran bajos ni se convierten en cero. Las otras medidas y los desenlaces se conservan.
- Pocos casos basales pueden producir aumentos grandes. Se conservan conteos y poblaciones por edad para revisar precisión y cambios de notificación.

## Archivos

- [Lista completa y criterios que cumple cada municipio](docs/data_processed/cobertura_vacunacion/municipal_priority_union_2024_2025.csv).
- [Criterio municipal](docs/data_processed/cobertura_vacunacion/municipal_priority_municipal_2024_2025.csv).
- [Criterio infantil](docs/data_processed/cobertura_vacunacion/municipal_priority_children_2024_2025.csv).
- [Todos los municipios](docs/data_processed/cobertura_vacunacion/municipal_priority_age_all_2024_2025.csv).
- [Detalle anual](docs/data_processed/cobertura_vacunacion/municipal_priority_age_annual_2024_2025.csv).
- [Metadatos](docs/data_processed/cobertura_vacunacion/municipal_priority_age_2024_2025.metadata.json).

```bash
.venv/bin/python scripts/analyze_municipal_priority_candidates.py
```
