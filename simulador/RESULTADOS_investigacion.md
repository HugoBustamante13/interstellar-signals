# Resultados de investigación (sesión INVESTIGACIÓN)

> Lo escribe solo la sesión de investigación. La sesión de construcción lo lee y aplica valores a los JSON.
> Etiquetas: **[verificado]** = abrí la fuente completa y comprobé la cifra · **[sin verificar]** = solo vi el resumen o un fragmento · **[sin fuente]** = no encontré dato.
> Estados para los JSON: `medido / referencia / derivado / supuesto / sin fuente`. Un dato de análogo va como `referencia` y su fuente dice "análogo: ...".

---

## TANDA 1 (14 nov 2026): vacíos 5, 1 y 4

### Resumen en 5 líneas

1. **Temperatura (vacío 5):** Stahn 2017 midió con un sensor de **frente** (Double Sensor, flujo de calor), no rectal. Su valor previo al vuelo se lee en la figura en **~36,3 °C**, más cerca de la temperatura oral (36,6) que de la rectal (37,0). En vuelo, la media sube a **~37,0–37,7 °C** (pico en el día 75).
2. **El rojo falso de temperatura no se explica solo por mezclar sitios.** Con 36,6 + 1,01 y una dispersión entre personas de ~0,5 °C, más o menos 1 de cada 4 astronautas sanos queda por encima de 38,0 °C en vuelo. Los datos reales de Stahn también tienen gente cerca de 38 °C en reposo. **Un límite rojo absoluto de 38,0 °C choca con la deriva normal en vuelo.** Esto lo tiene que decidir el equipo (ver la opinión al final).
3. **FC y presión absolutas (vacío 1):** hay valores absolutos medidos en la ISS con monitoreo ambulatorio de 24 h (Norsk 2015, 8 hombres, [verificado]): sistólica 129 → 121, diastólica 85 → 76 y FC 64 → 63 lpm. Fu 2019 (12 astronautas, **4 mujeres**) da sistólica de 24 h 120 → 106, pero **sin separar por sexo** y solo leí el resumen.
4. **No encontré valores en vuelo separados por sexo.** Lo único por sexo es posterior al vuelo: tras misiones cortas, el presíncope de pie afectó al **100 % de las mujeres frente al 20 % de los hombres** (Waters 2002, solo el resumen).
5. **Umbrales (vacío 4):** bradicardia sinusal = **menos de 50 lpm** (ACC/AHA/HRS 2018 [verificado]). La misma guía dice que no se pone marcapasos por bradicardia durante el sueño ni en personas sin síntomas. Hipotensión ortostática = caída de **20 mmHg o más en la sistólica, o 10 mmHg o más en la diastólica, en los primeros 3 min de pie** (consenso de 2011 [verificado vía texto de los autores del consenso]). ESC 2018 añade un absoluto de sistólica **menor de 90 mmHg** [sin verificar]. **NASA-STD-3001 no fija ningún número**: solo exige contramedidas [verificado].

---

### Vacío 5. Temperatura central frente a oral

| Indicador | Valor y unidad | Población y condición | Tipo de dato | Fuente | Etiqueta | Limitaciones |
|---|---|---|---|---|---|---|
| Cambio de la temperatura central en reposo en vuelo | **+1,01 °C** frente a la línea base; meseta después de ~75 días; vuelve lento a la línea base (R+10 a R+30) | n = 11 (**7 hombres, 4 mujeres**), 50 ± 4 años, ISS de ~6 meses; mediciones en L-90, días de vuelo 15, 45, 75, 105, 135 y 165, y R+1, R+10 y R+30 | medido | Stahn AC et al., "Increased core body temperature in astronauts during long-duration space missions", *Sci Rep* 7:16180, 2017. https://doi.org/10.1038/s41598-017-15560-w (texto completo: PMC5701078) | [verificado] | El "reposo" es el **mínimo de la fase previa al ejercicio** dentro de una prueba en cicloergómetro, no una medición de 24 h ni de cama. No hay análisis por sexo (pocas mujeres). La hora del día no se reporta |
| Temperatura central absoluta antes del vuelo (Pre) | **~36,3 °C** (IC 95 % aprox. 36,0–36,6) | igual, L-90, en reposo antes del ejercicio | medido (leído de la figura) | Stahn 2017, Fig. 1a | [verificado] (lectura de figura, ±0,1 °C) | El texto no da el número absoluto; lo leí del eje de la Fig. 1a |
| Temperatura central absoluta en vuelo | Día 15 **~37,0**; día 45 ~37,3; **día 75 ~37,7 (pico)**; día 105 ~37,25; día 135 ~37,3; día 165 ~37,4 °C | igual | medido (leído de la figura) | Stahn 2017, Fig. 1a | [verificado] (lectura de figura) | Son medias de grupo. Los IC 95 % miden ±0,3–0,4 °C, así que algunas personas quedan cerca de 38 °C en reposo |
| Temperatura central absoluta después del vuelo | R+1 ~36,9; R+10 ~36,6; R+30 ~36,65 °C | igual | medido (leído de la figura) | Stahn 2017, Fig. 1a | [verificado] (lectura de figura) | — |
| Temperatura máxima durante el ejercicio | Pre ~38,0 → en vuelo ~39,0–39,7 °C (+1,39 °C de media); **más de 40 °C en algunas personas** | igual | medido | Stahn 2017, texto y Fig. 1b | [verificado] | Ejercicio submáximo con escalones hasta el máximo; no aplica al reposo |
| Sitio y método de medición | Sensor de flujo de calor de doble termistor (Double Sensor) **en la frente**, 0,5 Hz, media móvil de 1 min | — | método | Stahn 2017, Métodos | [verificado] | Stahn cita la validación frente a nasofaringe, esófago y arteria, pero **no da el sesgo** en este artículo (está en Gunga 2009, que no abrí) |
| Temperatura central en vuelos cortos (contexto) | +0,06 a 0,16 °C (registros de 24 h, 8–16 días de vuelo) | vuelos cortos | medido (citado por Stahn) | Gundel et al. 1993 y 1997, citados en la discusión de Stahn 2017 | [sin verificar] (no abrí el original) | Solo como contexto |
| Media rectal (Tierra) | **37,04 ± 0,36 °C** (todas las edades); **37,10 ± 0,26** en menores de 60 | 13 estudios, 618 adultos sanos | referencia terrestre | Geneva II et al., "Normal Body Temperature: A Systematic Review", *Open Forum Infect Dis* 6(4):ofz032, 2019. https://doi.org/10.1093/ofid/ofz032 (PMC6456186), Tabla 3 | [verificado] | Metaanálisis de estudios heterogéneos de 1935 a 2017 |
| Media oral (Tierra) | **36,57 ± 0,42 °C** (todas las edades); **36,74 ± 0,30** en menores de 60; mujeres 36,70 ± 0,34; hombres 36,71 ± 0,39 | 33 estudios, 5257 adultos | referencia terrestre | Geneva 2019, Tabla 3 | [verificado] | Casi no hay diferencia por sexo |
| **Diferencia central (rectal) menos oral** | **≈ +0,47 °C** (todas las edades); **≈ +0,36 °C** en menores de 60 | — | **derivado** (resta de medias de grupos distintos) | Geneva 2019, Tabla 3 | [verificado] (las cifras de origen) | No es una diferencia pareada: sale de comparar estudios distintos. En los estudios pareados de la Tabla 2 va de ~0,3 a 0,8 °C (p. ej., Horvath 1950: 37,06 frente a 36,53) |
| Techo ocupacional de temperatura central | No pasar de **38,0 °C** de temperatura central en trabajo pesado prolongado (NIOSH 2016) | trabajadores en la Tierra | referencia terrestre | Citado en la introducción de Stahn 2017 (ref. 5: NIOSH 2016-106) | [sin verificar] (no abrí NIOSH) | Es un límite **central**, no oral, y no es un criterio de fiebre |

**Cómo resolver la mezcla de sitios (lo que pide 4.3.1):**
- Stahn reporta un **cambio** (+1,01 °C) en un sensor de frente. El cambio se puede sumar a cualquier línea base mientras **el sensor y el umbral estén en el mismo sitio**.
- La línea base de Stahn con sensor de frente (~36,3 °C) queda **más cerca de la oral (36,6–36,7) que de la rectal (37,0–37,1)**. Por eso la nota de la frente (~0,6 °C menos) del MSD Manual es coherente en dirección.
- Aunque todo se haga en escala oral, la media en vuelo queda en ~37,6 °C. Con una DE entre personas de ~0,4–0,5 °C, **un rojo fijo en 38,0 °C se dispara en una fracción grande de astronautas sanos**. Esa cifra es la fiebre oral de la Tierra (MSD), pero en vuelo la temperatura normal se corre hacia arriba. Es un problema de **umbral**, no solo de sitio.

---

### Vacío 1. FC y presión arterial absolutas en vuelo

| Indicador | Valor y unidad | Población y condición | Tipo de dato | Fuente | Etiqueta | Limitaciones |
|---|---|---|---|---|---|---|
| Sistólica, media de 24 h | Pre **129 ± 2** → vuelo **121 ± 2** → post 132 ± 2 mmHg (media ± EE) | **8 hombres**, 45–53 años, ISS; pre entre L-322 y L-71; vuelo entre los días 85 y 192; post entre R+58 y R+209. Ambulatoria, braquial, oscilométrica, cada hora de día y cada 2 h de noche | medido | Norsk P, Asmar A, Damgaard M, Christensen NJ, "Fluid shifts, vasodilatation and ambulatory blood pressure reduction during long duration spaceflight", *J Physiol* 593(3):573–584, 2015. https://doi.org/10.1113/jphysiol.2014.284869 (PMC4324706) | [verificado] | Solo hombres. **Dos tomaban IECA** (antihipertensivos) y al menos dos tomaban estatinas. EE → DE: multiplicar por √8 ≈ 2,83 (2 mmHg de EE ≈ 5,7 mmHg de DE) |
| Diastólica, media de 24 h | Pre **85 ± 2** → vuelo **76 ± 2** → post 86 ± 2 mmHg | igual | medido | Norsk 2015 | [verificado] | igual |
| Presión arterial media, 24 h | 102 ± 3 → 92 ± 1 → 103 ± 2 mmHg | igual | medido | Norsk 2015 | [verificado] | igual |
| PA de día (8–23 h) | Sistólica 130 ± 2 → 123 ± 1; diastólica 87 ± 1 → 77 ± 1 mmHg | igual | medido | Norsk 2015 | [verificado] | — |
| PA de noche (23–8 h) | Sistólica 121 ± 4 → 111 ± 4; diastólica 77 ± 3 → 71 ± 3 mmHg; el descenso nocturno de ~8 mmHg se mantiene | igual | medido | Norsk 2015 | [verificado] | Diastólica nocturna no significativa (p = 0,054) |
| PA sentado en reposo (en la Tierra) frente a vuelo | Sistólica 130 ± 2 → 118 ± 2; diastólica 89 ± 3 → 77 ± 2 mmHg | igual, sentado 5–7 min, durante la medición del gasto cardíaco | medido | Norsk 2015 | [verificado] | Es la comparación con mayor caída |
| **FC media de 24 h** | **64 ± 2 → 63 ± 2 lpm** (sin cambio) | igual | medido | Norsk 2015 | [verificado] | EE de 2 → DE ≈ 5,7 lpm |
| FC durante el sueño en vuelo | **58 ± 1 lpm** (la más baja del estudio); de día en vuelo 64 ± 3 | igual | medido | Norsk 2015 | [verificado] | Útil para el umbral de bradicardia nocturna |
| Sistólica de 24 h (latido a latido) | **120 ± 10 → 106 ± 9 → 122 ± 13 mmHg** (media ± DE); diastólica sin cambio | **12 astronautas (4 mujeres)**, 48 ± 5 años, ISS de 6 meses | medido | Fu Q et al., "Impact of Prolonged Spaceflight on Orthostatic Tolerance During Ambulation and Blood Pressure Profiles in Astronauts", *Circulation* 140:729–738, 2019. https://doi.org/10.1161/CIRCULATIONAHA.119.041050 | [sin verificar] (solo el resumen; la web de AHA bloquea el acceso automático) | **No separa por sexo** en el resumen. Usa un método de dedo (latido a latido), por eso la sistólica es más baja que la braquial de Norsk |
| FC en reposo sentado | Pre **54,9 ± 9,6** → post 60,0 ± 9,4 lpm; en vuelo "sin cambio" frente a pre | **6 hombres**, ISS de 2–6 meses, presión de dedo | medido | Hughson RL et al., "Cardiovascular regulation during long-duration spaceflights to the International Space Station", *J Appl Physiol* 112:719–727, 2012. **DOI correcto: 10.1152/japplphysiol.01196.2011** | [sin verificar] (solo el resumen; la web bloquea el acceso automático) | El resumen no da los valores absolutos en vuelo |
| FC y PA frente a la postura previa | FC en vuelo = FC acostado antes del vuelo; PA media entre la de pie y la acostada | **11 hombres**, 9 misiones a la ISS, hasta 6 meses | medido | Verheyden B, Liu J, Beckers F, Aubert AE, "Adaptation of heart rate and blood pressure to short and long duration space missions", *Respir Physiol Neurobiol* 169 Suppl 1:S13–S16, 2009. doi 10.1016/j.resp.2009.03.008 | [sin verificar] (solo el resumen, sin cifras) | **La pista de Isa se confirma:** autores Verheyden, Liu, Beckers y Aubert, 11 astronautas. El resumen no trae números |
| FC y PA en el transbordador | FC y diastólica bajan en vuelo (24 h); la sistólica tiende a bajar | astronautas del transbordador, vuelos cortos | medido | Fritsch-Yelle JM et al., "Microgravity decreases heart rate and arterial pressure in humans", *J Appl Physiol* 80:910, 1996. doi 10.1152/jappl.1996.80.3.910 | [sin verificar] (solo el resumen, sin cifras) | Norsk cita que en vuelos de menos de 2 semanas la diastólica bajó 5 mmHg (n = 12) |
| PA y FC de cosmonautas | PA baja en vuelo, FC sin cambio | 8 cosmonautas hombres, 162–196 días, ISS | medido | Baevsky RM et al., *J Appl Physiol* 103:156–161, 2007. doi 10.1152/japplphysiol.00137.2007 | [sin verificar] (solo el resumen) | Norsk resume una diastólica ~10 mmHg menor que en semisupino en la Tierra |
| Diferencia por sexo (solo después del vuelo) | Presíncope de pie al aterrizar: **mujeres 100 % frente a hombres 20 %**; las mujeres perdieron más volumen plasmático (20 % frente a 7 %) | 35 astronautas, misiones de 5 a 16 días, prueba de pie de 10 min | medido | Waters WW, Ziegler MG, Meck JV, "Postspaceflight orthostatic hypotension occurs mostly in women and is predicted by low vascular resistance", *J Appl Physiol* 92:586–594, 2002. doi 10.1152/japplphysiol.00544.2001 | [sin verificar] (solo el resumen) | **La pista de Isa se confirma.** Es **después** del vuelo y en misiones cortas, no aplica al reposo en vuelo. El resumen no dice cuántas mujeres hubo |
| **FC y PA absolutas en vuelo separadas por sexo** | — | — | — | — | **[sin fuente]** | No encontré ningún estudio público con valores en vuelo separados por sexo. Fu 2019 y Stahn 2017 incluyen mujeres pero no separan |

**Por qué difieren las fuentes:** con brazalete braquial ambulatorio (Norsk) la PA baja 8–10 mmHg. Con presión de dedo (Hughson) no cambia frente a sentado ni acostado. Verheyden 2009 documentó diferencias de hasta 30 mmHg entre dedo y brazo en vuelo (según la discusión de Norsk). La postura de referencia (sentado, acostado o de pie) cambia la conclusión.

---

### Vacío 4. Umbrales de hipotensión y bradicardia

| Indicador | Valor y unidad | Población y condición | Tipo de dato | Fuente | Etiqueta | Limitaciones |
|---|---|---|---|---|---|---|
| Bradicardia sinusal | **Frecuencia sinusal menor de 50 lpm** | adultos (guía clínica) | referencia terrestre (guía) | ACC/AHA/HRS 2018, Kusumoto FM et al., *J Am Coll Cardiol* 2019;74:e51 (doi 10.1016/j.jacc.2018.10.044). Leído en el resumen oficial del ACC "Guidelines Made Simple 2018 Bradycardia", tabla de definiciones: https://www.acc.org/-/media/Non-Clinical/Files-PDFs-Excel-MS-Word-etc/Guidelines/2018/Guidelines_Made_Simple_2018_Bradycardia.pdf | [verificado] (en el documento oficial del ACC; no abrí el texto completo de JACC porque bloquea el acceso automático) | Es una definición diagnóstica, **no un umbral de alarma**. La guía dice que no hay una FC mínima que por sí sola indique marcapasos |
| Bradicardia benigna (sueño y entrenamiento) | La guía lista el sueño y el entrenamiento físico intenso como causas vagales de bradicardia; en el sueño o sin síntomas, **no** se pone marcapasos (recomendación III: Harm) | adultos | referencia terrestre (guía) | ACC GMS 2018, recomendaciones de manejo crónico y tabla de causas | [verificado] | Importante: la FC de sueño en vuelo fue 58 ± 1 lpm (Norsk) y los astronautas entrenan a diario |
| Hipotensión ortostática clásica | Caída sostenida de la sistólica de **20 mmHg o más** (30 mmHg o más si hay hipertensión acostado) o de la diastólica de **10 mmHg o más**, **en los primeros 3 min** de pie o en mesa basculante de 60° o más | adultos | referencia terrestre (consenso) | Freeman R et al., "Consensus statement on the definition of orthostatic hypotension…", *Clin Auton Res* 21:69–72, 2011 (doi 10.1007/s10286-011-0119-5). Leí la definición tal como la reformulan los autores del consenso AAS/EFAS en Fanciulli A et al., *Clin Auton Res* 28:355–362, 2018 (PMC6097730) | [verificado] (vía Fanciulli 2018, texto completo; Freeman 2011 tiene muro de pago) | **Requiere un cambio de postura.** En vuelo no hay "de pie", así que aplica a la vuelta a gravedad (aterrizaje, Marte o la Luna), no al reposo en la ISS |
| Absoluto de sistólica en ortostatismo | Sistólica **menor de 90 mmHg** de pie, añadido por ESC 2018 (útil sobre todo si la sistólica acostado es menor de 110) | adultos | referencia terrestre (guía) | Brignole M et al., "2018 ESC Guidelines for the diagnosis and management of syncope", *Eur Heart J* 39:1883–1948, 2018. doi 10.1093/eurheartj/ehy037 | **[sin verificar]** (solo fragmentos de búsqueda; OUP y el repositorio de la Universidad de Berna bloquean el acceso automático) | Si Isa abre https://academic.oup.com/eurheartj/article/39/21/1883/4939241 y pega la sección de hipotensión ortostática, lo paso a [verificado] |
| Hipertensión acostado (contexto) | Sistólica de 140 o más y/o diastólica de 90 o más tras 5 min acostado | pacientes con falla autonómica | referencia terrestre (consenso) | Fanciulli 2018 (PMC6097730) | [verificado] | Población clínica, no sana |
| Hipotensión absoluta en reposo (sin cambio de postura) | — | — | — | — | **[sin fuente]** | No encontré en guías abiertas una cifra de "hipotensión" en reposo para adultos sanos. El único absoluto es el de 90 mmHg de ESC, y es para la prueba de pie |
| Criterio numérico de NASA | **No existe.** NASA-STD-3001 Vol. 1 Rev. A (2014, Chg 1 de 2015), §4.2.11 "Fitness-for-Duty Orthostatic Hypotension Standard", solo exige usar las contramedidas aprobadas (carga de líquidos y prendas de compresión). En el apéndice F.10 da la incidencia: 20–30 % en misiones cortas y 83 % en largas | astronautas | norma de agencia | NASA-STD-3001 Vol 1 Rev A Chg 1: https://standards.nasa.gov/sites/default/files/standards/NASA/B/Historical/NASA-STD-3001-VOL-1A-Chg1-1.pdf ; Rev C (2023): https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf | [verificado] (Rev A: sección leída; Rev C: busqué en todo el PDF "orthostatic", "hypotension", "bradycardia" y "fever", y no hay umbrales numéricos) | No revisé ESA, JAXA ni CSA a fondo: no encontré criterios públicos |
| Criterios de presíncope en investigación de NASA | Caída de sistólica mayor de 25 mmHg, de FC mayor de 15 lpm o sistólica menor de 70 mmHg | pruebas de tolerancia en investigación | criterio de protocolo | NTRS 20010096254 (aparece en un resultado de búsqueda) | **[sin verificar]** (no lo abrí) | Es un criterio para **detener una prueba**, no una norma clínica. No usar sin abrirlo |

---

### Fuentes (lo que realmente abrí completo en la tanda 1)
- Stahn 2017, *Sci Rep*: texto completo (Europe PMC, PMC5701078) y Figura 1 — https://doi.org/10.1038/s41598-017-15560-w
- Geneva 2019, *Open Forum Infect Dis*: texto completo y tablas — https://pmc.ncbi.nlm.nih.gov/articles/PMC6456186/
- Norsk 2015, *J Physiol*: texto completo — https://pmc.ncbi.nlm.nih.gov/articles/PMC4324706/
- ACC, "Guidelines Made Simple 2018 Bradycardia" (PDF oficial del ACC) — enlace en la tabla del vacío 4
- Fanciulli 2018, *Clin Auton Res*: texto completo — https://pmc.ncbi.nlm.nih.gov/articles/PMC6097730/
- NASA-STD-3001 Vol. 1, Rev. A Chg 1 y Rev. C (PDF completos) — enlaces en la tabla del vacío 4
- Solo resúmenes (Europe PMC): Verheyden 2009, Hughson 2012, Fu 2019, Waters 2002, Fritsch-Yelle 1996, Baevsky 2007, Freeman 2011 (metadatos)

### Qué falta o no se pudo verificar
- FC y PA en vuelo **por sexo**: [sin fuente]. Fu 2019 (4 mujeres) quizá separa por sexo en el texto completo, pero AHA bloquea el acceso: **Isa, si puedes, abre https://www.ahajournals.org/doi/10.1161/CIRCULATIONAHA.119.041050 y pega la tabla de resultados.**
- ESC 2018 (absoluto de 90 mmHg): [sin verificar]. Hughson 2012 y Fritsch-Yelle 1996 (valores absolutos): solo resúmenes (journals.physiology.org bloquea el acceso).
- Sesgo del Double Sensor frente a la temperatura rectal o esofágica (Gunga 2009): no lo abrí.
- Valores absolutos de temperatura en Stahn: leídos de la figura (±0,1 °C), no tabulados. Las tablas S1–S2 del suplemento solo dicen qué datos faltan; no las pude descargar.
- Criterios numéricos de ESA, JAXA o CSA: no encontré nada público.

### Opinión (tanda 1)
- **Temperatura:** simular **en escala oral** (36,6 °C, Obermeyer, ya está así) y mantener la deriva de +1,01 °C (Stahn), con el `site_offset_c` documentado. Mi recomendación honesta es **sacar el rojo absoluto de 38,0 °C de los días de vuelo, o subirlo**, porque la propia fisiología normal en vuelo lo cruza. Como **no tengo fuente** para otro número absoluto, la alternativa defendible es que en vuelo la temperatura se evalúe **solo contra la línea base personal** (banda y salto), y que el 38,0 se mantenga para la fase en Tierra y los primeros 14 días. Si el equipo quiere un absoluto en vuelo, es `supuesto` y hay que decirlo. Esto lo decide Isa (sección 6 del HANDOFF).
- **FC y PA:** para el hombre, usar como **validación en vuelo** los absolutos de Norsk (sistólica 24 h ~121, diastólica ~76, FC ~63, FC de sueño ~58). La deriva de -8/-9 ya está bien calibrada. Para la mujer no hay dato en vuelo: mantener `female_change_rule` = mismo cambio relativo, como `supuesto`, y decirlo.
- **Bradicardia:** agregar un límite inferior de FC con la definición de menos de 50 lpm, pero **como amarillo, no como rojo**, y no de noche: la guía considera benignas la bradicardia del sueño y la del atleta, y la FC de sueño en vuelo ronda 58 lpm. El paso a rojo, si se quiere, es `supuesto`.
- **Hipotensión:** el criterio ortostático (caída de 20/10 mmHg) no aplica en microgravedad. Para el reposo en vuelo no hay umbral con fuente: o se usa la sistólica menor de 90 de ESC como amarillo, etiquetada [sin verificar] hasta que alguien abra la guía, o se deja solo la banda personal.

---

## Tabla para la sesión de construcción (tanda 1)

| Parámetro del simulador | Valor | Estado | Fuente | Etiqueta |
|---|---|---|---|---|
| `temp.mean` (escala oral) | 36,6 °C (sin cambio) | referencia | Obermeyer 2017 (ya está). Lo apoya Geneva 2019: oral 36,57 ± 0,42 (36,74 en menores de 60) | [verificado] (Geneva) |
| `temp.drift_mean` | +1,01 °C | medido | Stahn 2017 (sensor de frente, n = 11, 4 mujeres) | [verificado] |
| `temp.tau_days` | 25 (meseta en ~75 días) | derivado | Stahn 2017, Fig. 1a/c | [verificado] |
| `temp.drift_sd` | 0,35 (sin cambio) | supuesto | Stahn no publica la DE individual; el IC 95 % de la Fig. 1a (±0,3–0,4 con n = 11) sugiere una DE entre personas de ~0,5–0,6 °C (estimación gruesa) | [sin fuente] para la DE exacta |
| `temp.site_offset_c` | 0 si el sensor es oral. Si el sensor mide temperatura central (rectal o esofágica): **+0,4 a +0,5 °C** sobre la oral | derivado | Geneva 2019, Tabla 3: rectal 37,04 menos oral 36,57 = 0,47 (0,36 en menores de 60) | [verificado] (cifras de origen) |
| Línea base con sensor de frente (si Hugo confirma ese sensor) | ~36,3 °C antes del vuelo | medido (leído de la figura) | Stahn 2017, Fig. 1a | [verificado] (±0,1) |
| Validación: temperatura central absoluta en vuelo | ~37,0 (día 15) → ~37,7 (día 75) → ~37,4 (día 165) °C | medido (figura) | Stahn 2017, Fig. 1a | [verificado] (±0,1) |
| `absolute_red.temp_gt` en vuelo | **Decisión del equipo.** 38,0 °C es fiebre **oral en la Tierra** (MSD) y la deriva normal en vuelo lo cruza | — | — | [sin fuente] para un valor en vuelo |
| Validación: sistólica de 24 h en vuelo (hombre) | 121 ± 2 EE (pre 129) mmHg | medido | Norsk 2015 | [verificado] |
| Validación: diastólica de 24 h en vuelo (hombre) | 76 ± 2 EE (pre 85) mmHg | medido | Norsk 2015 | [verificado] |
| Validación: FC de 24 h en vuelo (hombre) | 63 ± 2 EE (pre 64) lpm | medido | Norsk 2015 | [verificado] |
| FC de sueño en vuelo (hombre) | 58 ± 1 EE lpm | medido | Norsk 2015 | [verificado] |
| `bp.drift_between_sd_mmhg` | 5,7 (sin cambio; EE 2 × √8) | derivado | Norsk 2015. Comparar: Fu 2019 reporta una DE de 9–10 mmHg en sistólica (n = 12) | [verificado] (Norsk) / [sin verificar] (Fu) |
| Mujeres: valores en vuelo | — (mantener `female_change_rule` = 1) | supuesto | Ninguna fuente pública separa por sexo | [sin fuente] |
| Nuevo: límite inferior de FC (bradicardia) | menos de 50 lpm → **amarillo** (de día y despierto) | referencia | ACC/AHA/HRS 2018 (definición de bradicardia sinusal) | [verificado] |
| Nuevo: FC menor de 50 → rojo | — | supuesto | La guía no da un umbral de gravedad; usar solo si el equipo lo decide | [sin fuente] |
| Nuevo: límite inferior de sistólica | menos de 90 mmHg → amarillo | referencia | ESC 2018 (absoluto de la prueba de pie) | [sin verificar] |
| Hipotensión ortostática (solo al volver a gravedad) | caída de 20 mmHg o más en sistólica o de 10 mmHg o más en diastólica en 3 min | referencia | Freeman 2011 vía Fanciulli 2018 | [verificado] |
| Criterio numérico de NASA para FC o PA | no existe | sin fuente | NASA-STD-3001 Vol. 1 Rev. A §4.2.11 y Rev. C | [verificado] (ausencia) |

---

## TANDA 2 (14 nov 2026): vacíos 2 (glucosa) y 3 (ánimo)

### Resumen en 4 líneas

1. **Glucosa en vuelo, valores absolutos: [sin fuente] público.** Hughson 2016 (4 hombres y 4 mujeres en la ISS) solo dice en el resumen que sube un índice de resistencia a la insulina, más en los hombres. La tabla con valores absolutos, si existe, está tras un muro y no la pude abrir.
2. **Lo más cercano es un análogo:** inmersión seca de 5 días de ESA (VIVALDI, unas 20 mujeres y 20 hombres). La glucosa en ayunas quedó **por debajo de 6,1 mmol/l (110 mg/dl) en todos y no cambió**. Lo que sí empeoró fue la tolerancia a la glucosa y la sensibilidad a la insulina, algo más en las mujeres.
3. **Ánimo:** no encontré normas numéricas del PANAS en texto abierto: Crawford y Henry 2004 tiene muro y su resumen no trae cifras. Para el **GHQ-12** sí hay umbrales con fuente abierta: en la puntuación clásica 0-0-1-1, el corte más común es **2/3**. En la puntuación Likert 0–36, un estudio de 2026 **en entornos aislados y confinados** da vigilar a partir de 8 y **atención urgente a partir de 12**.
4. **Análogos:** en SIRIUS-19 (NEK, 120 días, 6 personas, 3 mujeres) el PANAS **no cambió**, y el afecto negativo quedó casi siempre en el piso. En Mars-500 (520 días, 6 hombres) el POMS fluctuó sin diferencias significativas. **Conclusión: en estos análogos el ánimo es estable a nivel de grupo.** Por eso evaluarlo contra la línea base personal (como ya hace el semáforo) es lo correcto.

---

### Vacío 2. Glucosa en ayunas

| Indicador | Valor y unidad | Población y condición | Tipo de dato | Fuente | Etiqueta | Limitaciones |
|---|---|---|---|---|---|---|
| Glucosa en ayunas antes, durante y después del vuelo | — | — | — | — | **[sin fuente]** | No encontré valores absolutos publicados en acceso abierto. Busqué en PubMed y PMC con astronautas + glucosa/HOMA/insulina + vuelo, y revisé dos estudios ómicos de NASA (PMC9444344, PMC10376710): no reportan glucosa absoluta |
| Resistencia a la insulina en vuelo | Sube en vuelo frente a antes (p < 0,001); el cambio es mayor en hombres (interacción vuelo × sexo, p = 0,034) | **4 hombres y 4 mujeres**, ISS, 6 meses | medido | Hughson RL et al., "Increased postflight carotid artery stiffness and inflight insulin resistance resulting from 6-mo spaceflight in male and female astronauts", *Am J Physiol Heart Circ Physiol* 310(5):H628–638, 2016. https://doi.org/10.1152/ajpheart.00802.2015 (PubMed 26747504) | [sin verificar] (solo el resumen; no está en PMC y la web de la revista bloquea el acceso automático) | Es lo que ya tenían. Los valores absolutos de glucosa, si están, estarían en las tablas del texto completo |
| Glucosa en ayunas, análogo | **Por debajo de 6,1 mmol/l (110 mg/dl) en todos al inicio, y sin cambio** durante la inmersión | **VIVALDI-1: 20 mujeres; VIVALDI-2: 20 hombres**, jóvenes sanos, inmersión seca de 5 días, MEDES (Toulouse), 2021–2022 | **análogo** | Análogo: Sex-specific cardiometabolic responses during microgravity simulation in ESA VIVALDI dry immersion, *Commun Med* 2026. https://doi.org/10.1038/s43856-026-01540-7 (PMC13194667) | [verificado] (texto completo) | La media absoluta en ayunas solo aparece en una figura que no leí. Son 5 días, no meses. Las dos cohortes son de un solo sexo, en campañas separadas |
| Glucosa 2 h después de la sobrecarga oral (OGTT), análogo | Mujeres 5,6 ± 0,19 → **6,3 ± 0,35** mmol/l (día 3); hombres 6,0 ± 0,26 → **6,7 ± 0,24** mmol/l (día 5). Pasaron de 7,8 mmol/l (rango prediabético) 3 de 18 mujeres y 1 de 19 hombres | igual | análogo | VIVALDI 2026 | [verificado] | Probablemente media ± EE (no lo confirmé). La prueba se hizo en días distintos para cada sexo |
| Resistencia a la insulina (HOMA-IR), análogo | Día 3: +48 % en mujeres y +53 % en hombres. Día 5: +15 % en mujeres y −1 % en hombres | igual | análogo | VIVALDI 2026 | [verificado] | Dirección opuesta a la de Hughson 2016 en vuelo (allí el cambio fue mayor en hombres). Distinto modelo y duración |
| Glucosa en ayunas, análogo de confinamiento | "Aumentó" al final de 520 días | Mars-500, 6 hombres | análogo | Citado en el resumen de Brereton et al., *Comput Struct Biotechnol J* 19:2223, 2021. https://doi.org/10.1016/j.csbj.2021.03.040 | [sin verificar] (fuente secundaria, sin cifra) | Sin valor numérico |
| Glucosa en ayunas normal y alterada (Tierra) | Normal: **menos de 100 mg/dl (5,6 mmol/l)**. Glucosa en ayunas alterada: **100–125 mg/dl (5,6–6,9 mmol/l)**. Diabetes: **126 mg/dl (7,0 mmol/l) o más**. "Ayunas" = 8 h o más sin calorías | adultos no embarazados | referencia terrestre (guía) | American Diabetes Association, "2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2026", *Diabetes Care* 49(Suppl 1), 2026. https://doi.org/10.2337/dc26-S002 (PMC12690183), Tabla 2.1 y criterios de alteración en ayunas | [verificado] (texto de la página en PMC) | Son criterios diagnósticos, no rangos poblacionales (no dan media ni DE). El umbral de hipoglucemia está en la sección 6 de ADA, que no abrí |

---

### Vacío 3. Estado de ánimo

| Indicador | Valor y unidad | Población y condición | Tipo de dato | Fuente | Etiqueta | Limitaciones |
|---|---|---|---|---|---|---|
| Escala PANAS | 10 ítems positivos y 10 negativos, de 1 a 5 → cada suma va de **10 a 50** | — | método | Descrita en Abeln et al. (SIRIUS-19, abajo); el original es Watson, Clark y Tellegen 1988 (*J Pers Soc Psychol* 54:1063), que no abrí | [verificado] (la escala) | — |
| Normas poblacionales del PANAS | — | 1003 adultos del Reino Unido (muestra no clínica) | referencia terrestre | Crawford JR, Henry JD, *Br J Clin Psychol* 43:245–265, 2004. https://doi.org/10.1348/0144665031752934 | **[sin fuente]** para las cifras (el resumen no las trae y el texto completo tiene muro) | Si Isa tiene acceso, la tabla de normas está en ese artículo. No las relleno de memoria |
| PANAS en un análogo | **Sin cambio** en afecto positivo ni negativo a lo largo de 120 días; el afecto negativo quedó casi siempre en "nada", con muy poca variación (todos menos una persona) | **SIRIUS-19, NEK (IBMP, Moscú)**, marzo–julio 2019, **6 personas (3 mujeres)**, 120 días; PANAS en BDC-2 y en los días 12, 53, 82 y 110, y R+11 | análogo | Abeln V et al., "Chronic, acute and protocol-dependent effects of exercise on psycho-physiological health during long-term isolation and confinement", *BMC Neurosci* 23:41, 2022. https://doi.org/10.1186/s12868-022-00723-x (PMC9244384) | [verificado] (texto completo y tabla de estadística) | Los valores absolutos solo están en figuras. n = 6. Hacían ejercicio programado. Lo aplicaron como parte de las NASA HRP Standard Measures |
| POMS en un análogo | Fluctuó sin diferencias significativas en la alteración total del ánimo; el vigor cambió con el tiempo (p = 0,041, sin diferencias post hoc); el ánimo más bajo y el vigor más bajo coincidieron en el día 366 | **Mars-500, 6 hombres**, 32 ± 5 años, 520 días | análogo | Wang Y et al., "During the long way to Mars: effects of 520 days of confinement (Mars500)…", *PLoS One* 9(4):e87087, 2014. https://doi.org/10.1371/journal.pone.0087087 (PMC3973648) | [verificado] (texto completo) | Valores solo en figura. Solo hombres |
| Corte del GHQ-12, puntuación clásica (0-0-1-1, rango 0–12) | El corte óptimo más común es **2/3** (en estudios internacionales va de 1/2 a 6/7). En atención primaria en Indonesia el óptimo fue **1/2** (sensibilidad 82 %, especificidad 64 %, AUC 0,79) | 676 pacientes de atención primaria (452 mujeres) | referencia terrestre | Anjara SG et al., "Using the GHQ-12 to screen for mental health problems among primary care patients", *Int J Ment Health Syst* 14:62, 2020. https://doi.org/10.1186/s13033-020-00397-0 (PMC7418321) | [verificado] (texto completo; el "2/3 más común" lo cita de una revisión anterior) | El corte depende de la población y de la prevalencia |
| Corte del GHQ-12, puntuación Likert (0-1-2-3, rango 0–36), **entorno aislado y confinado** | Media **5,62 ± 4,25** (n = 730). Corte óptimo **más de 9** (depresión) y **más de 10** (ansiedad). Zona gris: **más de 7–8 = vigilar más de cerca; más de 11–12 = atención clínica urgente** | 730 sudafricanos en entornos aislados y confinados (marina, pesca de altura, petróleo en alta mar); repetición en 128 marinos tras patrullas de 3 semanas | referencia (entorno análogo ocupacional) | "Psychometric validity and clinical utility of the GHQ-12 for screening psychological health in isolated, confined and unusual or extreme environments", *Afr J Psychol Assess* 8:195, 2026. https://doi.org/10.4102/ajopa.v8i0.195 (PMC13444004) | [verificado] (texto completo) | Mayoría de hombres. No son astronautas. En la repetición, un cambio de 8 puntos o más identificó a quienes empeoraron |
| Corte del GHQ-12 de Goldberg 1997 (estudio OMS) | AUC media de 0,88 en 15 centros; la validez no depende del sexo, la edad ni la escolaridad | 5438 pacientes de atención primaria | referencia terrestre | Goldberg DP et al., *Psychol Med* 27:191–197, 1997. https://doi.org/10.1017/s0033291796004242 | [sin verificar] (solo el resumen, que no da el punto de corte) | — |
| Ánimo de astronautas en vuelo (PANAS o GHQ) | — | — | — | — | **[sin fuente]** | No busqué a fondo datos de vuelo; no hallé ninguno abierto en esta tanda |

---

### Fuentes (lo que abrí completo en la tanda 2)
- VIVALDI 2026, *Commun Med* — https://pmc.ncbi.nlm.nih.gov/articles/PMC13194667/
- ADA Standards of Care 2026, sección 2 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12690183/
- Abeln 2022, SIRIUS-19, *BMC Neurosci* — https://pmc.ncbi.nlm.nih.gov/articles/PMC9244384/
- Wang 2014, Mars-500, *PLoS One* — https://pmc.ncbi.nlm.nih.gov/articles/PMC3973648/
- Anjara 2020, GHQ-12 — https://pmc.ncbi.nlm.nih.gov/articles/PMC7418321/
- GHQ-12 en entornos aislados y confinados, 2026 — https://pmc.ncbi.nlm.nih.gov/articles/PMC13444004/
- Solo resúmenes: Hughson 2016, Crawford y Henry 2004, Goldberg 1997, Brereton 2021

### Qué falta o no se pudo verificar (tanda 2)
- Glucosa absoluta en vuelo: [sin fuente]. Si Isa puede abrir Hughson 2016 (https://journals.physiology.org/doi/full/10.1152/ajpheart.00802.2015) y pegar la tabla de biomarcadores, la reviso.
- Normas numéricas del PANAS (Crawford y Henry 2004): con muro.
- HERA: no encontré PANAS ni GHQ con cifras en acceso abierto en el tiempo disponible.
- La media absoluta de glucosa en ayunas de VIVALDI está solo en una figura.

### Opinión (tanda 2)
- **Glucosa:** dejarla como **"supuesto del equipo"**, tal como decidió Isa:
  - Media de partida en el rango normal de ADA (menos de 100 mg/dl). El número exacto es `supuesto`; el límite es [verificado].
  - Deriva en vuelo: solo la **dirección** (resistencia a la insulina hacia arriba, Hughson 2016), sin magnitud: `supuesto`.
  - Para el amarillo: alterada en ayunas = 100 mg/dl o más (ADA). Para el rojo: 126 mg/dl o más (ADA). Las dos son `referencia` [verificado]. Al menos los umbrales tienen fuente.
- **Ánimo:** recomiendo **cambiar la escala 1–5 por el GHQ-12 Likert (0–36)**, porque es el único con umbrales abiertos y validados en entornos aislados y confinados:
  - Base: media de 5,6 ± 4,3, `referencia` (análogo: entornos aislados y confinados, PMC13444004).
  - Amarillo: más de 8. Rojo: más de 12. Las dos son `referencia` [verificado].
  - Además: aviso si sube 8 puntos o más frente a la línea base personal.

  El PANAS sirve para describir, pero sin normas abiertas no da umbrales. Si se mantiene la escala 1–5, queda como `supuesto` sin respaldo, y así hay que decirlo.

---

## Tabla para la sesión de construcción (tanda 2)

| Parámetro del simulador | Valor | Estado | Fuente | Etiqueta |
|---|---|---|---|---|
| `glucose.mean` (antes del vuelo) | elegir dentro del rango normal, menos de 100 mg/dl (el número exacto es decisión del equipo) | supuesto (límite: referencia) | ADA 2026, Tabla 2.1 | [verificado] (límite) / [sin fuente] (media) |
| `glucose.drift` en vuelo | dirección hacia arriba; magnitud sin fuente | supuesto | Hughson 2016 (dirección) | [sin verificar] |
| Diferencia por sexo en la deriva de glucosa | mayor en hombres en vuelo (Hughson); mayor en mujeres en el análogo (VIVALDI): **contradictorio** | supuesto (no modelar diferencia) | Hughson 2016; análogo: VIVALDI 2026 | [sin verificar] / [verificado] |
| Validación con análogo: glucosa en ayunas | por debajo de 6,1 mmol/l (110 mg/dl) y estable en 5 días | referencia (análogo: inmersión seca VIVALDI) | PMC13194667 | [verificado] |
| Amarillo de glucosa en ayunas | 100 mg/dl o más (5,6 mmol/l) | referencia | ADA 2026 | [verificado] |
| Rojo de glucosa en ayunas | 126 mg/dl o más (7,0 mmol/l) | referencia | ADA 2026 | [verificado] |
| `mood.scale` | propuesta: GHQ-12 Likert 0–36 (más alto = peor) | referencia | PMC13444004 | [verificado] |
| `mood.mean` / `mood.sd` (GHQ-12 Likert) | 5,6 / 4,3 | referencia (análogo: entornos aislados y confinados, ocupacional) | PMC13444004, Tabla 1 | [verificado] |
| Amarillo de ánimo (GHQ-12 Likert) | más de 8 (zona gris baja: más de 7–8) | referencia | PMC13444004 | [verificado] |
| Rojo de ánimo (GHQ-12 Likert) | más de 12 (zona gris alta: más de 11–12) | referencia | PMC13444004 | [verificado] |
| Cambio personal en GHQ-12 | 8 puntos o más frente a la línea base → amarillo | referencia | PMC13444004 (cambios de 8 o más identificaron deterioro) | [verificado] |
| `mood.drift` en confinamiento | 0 (estable a nivel de grupo) | referencia (análogo: SIRIUS-19 con PANAS; Mars-500 con POMS) | PMC9244384; PMC3973648 | [verificado] |
| Si se mantiene la escala 1–5 | media, DE y umbrales | supuesto | sin respaldo publicado | [sin fuente] |
