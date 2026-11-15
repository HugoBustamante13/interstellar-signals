# Fichas de indicadores de salud (v0.3, 14 nov 2026)

> **DATOS SINTÉTICOS.** Todos los ejemplos numéricos salen de la misión simulada (semilla 42), no de astronautas reales. Los ejemplos se calculan con `fichas/ejemplos_calculo.py` y coinciden con las bandas que entrega `sim/semaforo.py` (comprobado por código).

**Estados de cada dato:** `medido` (cifra publicada, en vuelo o análogo) · `referencia` (valor de adultos en la Tierra o guía clínica) · `derivado` (cálculo sobre una cifra publicada) · `supuesto` (decisión del equipo, sin fuente) · `sin fuente`.
**Etiquetas de verificación:** [verificado] = se abrió la fuente; [sin verificar] = solo resumen o fragmento.

## Cómo juzga el semáforo (igual para los 8 indicadores)
1. **Línea base personal móvil:** media y DE de las lecturas válidas de los 28 días anteriores (mínimo 14 lecturas). Los días previos al vuelo alimentan la línea base. `supuesto`.
2. **Banda:** media ± 2,5 · DE · √(1 + 1/n), con una DE mínima por indicador (FC 2 lpm, presión 3 mmHg, SpO2 0,5 puntos, temperatura 0,15 °C, sueño 0,3 h, ánimo 0,2 puntos). Solo hacia abajo en SpO2, sueño y ánimo. `supuesto`.
3. **Amarillo:** 3 lecturas seguidas fuera de la banda. **Rojo:** límite absoluto, salto de 4 DE confirmado por la lectura siguiente, o dos indicadores en amarillo a la vez. `supuesto`.
4. **Primeros 14 días de vuelo:** solo cuentan los límites absolutos (la línea base todavía no refleja el vuelo). `supuesto`.
5. **NASA no publica criterios numéricos de alarma:** NASA-STD-3001 Vol. 1 Rev. A (§4.2.11) y Rev. C no fijan umbrales de FC, presión, temperatura ni hipotensión [verificado, búsqueda en el PDF completo de Rev. C]. Por eso toda banda, días seguidos y salto son criterio de diseño del equipo.

## Resumen: qué entra al producto
| Indicador | Umbral con fuente | Parte que es supuesto | Entrada al producto |
|---|---|---|---|
| FC en reposo | >100 lpm rojo (AHA); <50 lpm amarillo (ACC/AHA/HRS 2018) | banda, días, salto | Sí (núcleo) |
| Presión arterial | >180 / >120 mmHg rojo (AHA 2025) | banda, días, salto; cambio en mujeres | Sí (núcleo) |
| SpO2 | <90 % rojo (Open Critical Care); caída ≥3 puntos amarillo (BTS 2017) | media, DE y ruido simulados | Sí (secundario) |
| Temperatura | >38,0 °C rojo en los primeros 14 días (MSD) | **rojo de 38,5 °C en vuelo con 2 lecturas seguidas**; tope de 38,0 °C en la meseta simulada | Sí (núcleo), con el rojo en vuelo declarado como supuesto |
| Glucosa | ≥100 / ≥126 mg/dl (ADA 2026); <70 / <54 mg/dl (ADA 2026) | media, DE y deriva | **Fuera del semáforo mínimo**; entra como supuesto del equipo (decisión de Isa) |
| Horas de sueño | ninguno (solo banda personal); 7 h o más es referencia, no alarma | todo el umbral | Sí (núcleo) |
| Estado de ánimo | ninguno | escala 1–5, media, DE y umbral | Entra como supuesto del equipo (decisión de Isa); excepción a la regla de la ficha |
| Ejercicio y aptitud | aptitud <80 % (NASA-STD-3001); prescripción de 6 días/semana (Guilliams) | mínimo de 3 sesiones en 7 días; 90 min por sesión | Sí (secundario) |

**Redundancia a tener en cuenta:** sistólica y diastólica miden casi lo mismo y el semáforo las cuenta como dos indicadores, así que «dos amarillos = rojo» puede dispararse solo por presión. Si el equipo quiere un solo indicador de presión, quédense con la sistólica.

---

## 1. FC en reposo
**Categoría:** cardiovascular.
**Qué mide y por qué importa:** latidos por minuto en reposo, sentado, a las 08:30. Sube con infección, falta de sueño o dolor; en vuelo la FC media no cambia (Norsk 2015), así que una desviación respecto a la propia línea base es una señal útil.
**Variables de entrada:** `hr_rest_bpm` (lpm), 1 lectura al día; el dispositivo real (HRM2 o ECG de la ISS) está pendiente de confirmar con Hugo.
**Fórmula y ejemplo (calculado con código):** SIM-001, día 60 de misión: ventana de 28 días con n = 28, media 69,12 lpm, DE 3,85, DE de predicción 3,85 · √(1 + 1/28) = 3,92. Banda = 69,12 ± 2,5 · 3,92 = **59,32 a 78,92 lpm**. Lectura 63,5 → dentro → verde.
**Valores de referencia y umbrales:**
- Rojo: >100 lpm. `referencia`: AHA, *All About Heart Rate*, 60–100 lpm como normal en reposo. https://www.heart.org/en/health-topics/high-blood-pressure/the-facts-about-high-blood-pressure/all-about-heart-rate-pulse [verificado]
- Amarillo: <50 lpm. `referencia`: Kusumoto et al., ACC/AHA/HRS 2018, *J Am Coll Cardiol* 2019;74:e51, doi 10.1016/j.jacc.2018.10.044 (definición de bradicardia sinusal, [verificado] en el resumen oficial del ACC). Es una definición diagnóstica, no una alarma; la guía considera benigna la bradicardia del sueño y del entrenamiento. Se usa como amarillo, no rojo.
- Banda ±2,5 DE, 3 días seguidos, salto 4 DE: `supuesto`.
**Fuente de los datos:** sintética. Media y P5–P95 de adultos de EE. UU. de 20–39 años (hombres 71, 52–89; mujeres 76, 57–95): Ostchega et al., NHSR n.º 41, NCHS/CDC, 2011. https://www.cdc.gov/nchs/data/nhsr/nhsr041.pdf `referencia` [verificado]. Cambio en vuelo = 0: Norsk et al., *J Physiol* 593(3):573–584, 2015, https://doi.org/10.1113/jphysiol.2014.284869 `medido` (8 hombres; 64 → 63 lpm). Variación diaria de 3 lpm: `supuesto`.
**Limitaciones y sesgos:**
- La referencia es población general joven, no astronautas.
- Norsk son 8 hombres de 45–53 años medidos 24 h; el hold-out del simulador **no coincide**: FC simulada 71 lpm contra 63 lpm medida en hombres en vuelo.
- Mujeres en vuelo: sin fuente.
- El rojo de >100 lpm es la causa más frecuente de falsas alertas (114 episodios en 200 misiones, `out/evaluation/semaforo_false_episode_causes.csv`), en parte por artefactos de sensor.
**Cómo se visualiza:** línea diaria, línea base de 28 días, banda ±2,5 DE y franja de semáforo; zona gris previa al vuelo; x gris para artefactos. `charts/tendencia_hr_rest_synthetic.png`.

## 2. Presión arterial (sistólica y diastólica)
**Categoría:** cardiovascular.
**Qué mide y por qué importa:** presión en reposo (mmHg), 1 lectura al día. En vuelo baja ~8–9 mmHg por vasodilatación, así que una línea base fija de Tierra daría falsas alarmas.
**Variables de entrada:** `bp_sys_mmhg`, `bp_dia_mmhg` (mmHg), 1 al día; manguito automático (la AHA desaconseja depender de relojes). Dispositivo real pendiente con Hugo.
**Fórmula y ejemplo (calculado con código):** SIM-001, día 60. Sistólica: n = 28, media 114,14, DE 4,93, DE de predicción 5,01 → banda **101,61 a 126,68 mmHg**; lectura 120 → verde. Diastólica: media 60,39, DE 4,01, DE de predicción 4,08 → banda **50,18 a 70,60 mmHg**; lectura 71 queda 0,4 mmHg fuera, pero un solo día fuera no da amarillo (se necesitan 3 seguidos).
**Valores de referencia y umbrales:**
- Rojo: sistólica >180 o diastólica >120 mmHg. `referencia`: AHA 2025, hipertensión severa. https://professional.heart.org/en/science-news/2025-high-blood-pressure-guideline/top-things-to-know [verificado]
- Hipotensión: **sin umbral de reposo con fuente.** El absoluto <90 mmHg de la ESC 2018 (Brignole et al., *Eur Heart J* 39:1883, doi 10.1093/eurheartj/ehy037) es de la prueba de pie, [sin verificar]; está desactivado. La caída ortostática de ≥20 / ≥10 mmHg en 3 min de pie (Freeman 2011 vía Fanciulli 2018, PMC6097730 [verificado]) solo aplica al volver a gravedad y no está implementada.
- NASA: sin criterio numérico (NASA-STD-3001, [verificado] la ausencia).
- Banda, días y salto: `supuesto`.
**Fuente de los datos:** sintética. Línea base de adultos sin hipertensión, columna «Normal» (hombres 18–39: 117 [101–132] / 68 [51–84]; mujeres: 109 [94–126] / 67 [52–81]): Wright et al., NHSR n.º 35, NCHS/CDC, 2011. https://www.cdc.gov/nchs/data/nhsr/nhsr035.pdf `referencia` [verificado]. Cambio en vuelo −8 / −9 mmHg: Norsk 2015 (enlace arriba) `medido`, 8 hombres, braquial 24 h. Mujeres: mismo cambio relativo, `supuesto`. Ruido diario (5 y 4 mmHg) y correlación 0,5: `supuesto`.
**Limitaciones y sesgos:**
- Solo hombres en la cifra de vuelo.
- Hold-out del simulador contra Norsk: sistólica simulada 110 contra 121 mmHg medida, diastólica 60 contra 76. La explicación probable (población simulada de 18–39 años sentada, contra astronautas de 45–53 años medidos 24 h) es una hipótesis.
- Fu 2019 (12 astronautas, 4 mujeres, sistólica 120 → 106 con método de dedo, *Circulation* 140:729) está [sin verificar] (solo resumen).
- El método cambia la conclusión: el dedo difiere hasta 30 mmHg del brazo en vuelo (según la discusión de Norsk).
**Cómo se visualiza:** igual que la FC, un panel por astronauta. `charts/tendencia_bp_sys_synthetic.png` y `tendencia_bp_dia_synthetic.png`.

## 3. SpO2 (saturación de oxígeno)
**Categoría:** respiratorio y oxigenación.
**Qué mide y por qué importa:** porcentaje de hemoglobina saturada de oxígeno, 1 lectura al día. Detecta hipoxia por CO2 o ambiente de cabina; el riesgo de hipoxia en la ISS es bajo según NASA (R06).
**Variables de entrada:** `spo2_pct` (%), 1 al día; el 10 % de las lecturas se pierde por movimiento (`supuesto`; Hearn et al. 2023 midieron 12–82 % de pérdida en relojes con movimiento muy leve, *Aerosp Med Hum Perform* 94(1):42–47, [verificado]).
**Fórmula y ejemplo (calculado con código):** SIM-001, día 60: n = 26 lecturas válidas, media 97,54 %, DE 0,81, DE de predicción 0,83. Solo hay banda inferior: 97,54 − 2,5 · 0,83 = **95,47 %**. Lectura 98 → verde.
**Valores de referencia y umbrales:**
- Rojo: <90 %. `referencia`: Open Critical Care, hipoxemia. https://opencriticalcare.org/encyclopedia/physiologic-oxygen-terminology/
- Amarillo: caída de ≥3 puntos frente a la línea base. `referencia`: O'Driscoll et al., guía BTS 2017, *BMJ Open Respir Res* 4:e000170. https://pmc.ncbi.nlm.nih.gov/articles/PMC5531304 [verificado]
- Banda personal solo hacia abajo: `supuesto`.
**Fuente de los datos:** sintética. Media 97,5 %, DE y ruido: `supuesto` (sin rango normal con fuente). Cambio en vuelo = 0: Conkin et al., *Aerosp Med Hum Perform* 88(6):527–534, 2017, `medido` (cerca de 97 % con hipoxia leve, 8 hombres, [verificado] en el resumen). https://www.ingentaconnect.com/contentone/asma/amhp/2017/00000088/00000006/art00004
**Limitaciones y sesgos:** lectura entera (resolución de 1 punto), así que la DE es pequeña y la banda angosta; un artefacto de sensor infla la banda durante unos 28 días y en ese tramo el indicador queda casi ciego (visto en las gráficas); la caída de ≥3 puntos es la fuente principal de amarillos falsos de SpO2 (84 episodios en 200 misiones); sin datos de oxímetro en vuelo del equipo real.
**Cómo se visualiza:** igual que la FC, con banda solo inferior. `charts/tendencia_spo2_synthetic.png`.

## 4. Temperatura corporal
**Categoría:** termorregulación.
**Qué mide y por qué importa:** temperatura en escala oral equivalente, 1 lectura al día. En vuelo la temperatura central sube ~1 °C sin que sea fiebre (Stahn 2017), así que un límite fijo de Tierra no sirve tal cual; pero un aumento sostenido sí puede ser una infección.
**Variables de entrada:** `temp_c` (°C), 1 al día. **El sitio de medición del sensor real está pendiente (Hugo).** Stahn midió con un sensor en la frente.
**Fórmula y ejemplo (calculado con código):** SIM-001, día 60: n = 28, media 37,04 °C, DE 0,18, DE de predicción 0,19. Banda = 37,04 ± 2,5 · 0,19 = **36,57 a 37,51 °C**. Lectura 36,8 → verde.
**Valores de referencia y umbrales:**
- Rojo en los primeros 14 días de vuelo: >38,0 °C. `referencia`: MSD Manual, *Fever in Adults* (fiebre oral >38,0 °C). https://msdmanuals.com/home/infections/biology-of-infectious-disease/fever-in-adults [verificado]
- **Rojo desde el día 15: >38,5 °C en 2 lecturas seguidas. `supuesto` del equipo, sin fuente publicada.** Razón: 38,0 °C es fiebre en la Tierra, pero en vuelo algunas personas sanas rozan 38,0 °C en reposo (la media de grupo llega a ~37,7 °C con IC 95 % de ±0,3–0,4 °C en Stahn 2017, Fig. 1a, leída de la figura); 38,5 °C queda 0,5 °C por encima de ese techo. En v0.2 no había límite absoluto en vuelo y un astronauta simulado podía pasar meses en ≥38,0 °C con el semáforo en verde, porque la línea base móvil absorbe la subida lenta.
- Banda ±2,5 DE, 3 días, salto 4 DE confirmado: `supuesto`.
**Fuente de los datos:** sintética. Media oral 36,6 °C: Obermeyer, Samra y Mullainathan, *BMJ* 2017 (35 488 pacientes) `referencia`, apoyada por Geneva et al., *Open Forum Infect Dis* 2019, oral 36,57 ± 0,42, https://doi.org/10.1093/ofid/ofz032 [verificado]. Deriva +1,01 °C con meseta tras ~75 días: Stahn et al., *Sci Rep* 7:16180, 2017, https://doi.org/10.1038/s41598-017-15560-w `medido` [verificado] (11 astronautas, 7 hombres y 4 mujeres, sensor de frente). DE de la deriva (0,35 °C): `supuesto`. **Tope de la meseta individual simulada = 38,0 °C: `supuesto` (v0.3).**
**Limitaciones y sesgos:**
- Sitio de medición: si el sensor real mide temperatura central (rectal o esofágica), hay que sumar ~0,47 °C (Geneva 2019, resta de medias de estudios distintos, `derivado`) y revisar los límites.
- Stahn no publica la DE individual; la lectura de la figura tiene ±0,1 °C.
- El tope de la meseta es una decisión de modelado: sin él, el muestreo normal producía mesetas de 38,4–38,7 °C que nadie ha medido en reposo. Con el tope, SIM-002 y SIM-004 quedan con la meseta cerca de 38,0 °C (media en vuelo 37,9–38,0 °C, cerca del 50 % de los días en ≥38,0 °C y ~4 % en ≥38,5 °C); por eso el rojo de 38,5 °C exige 2 lecturas seguidas (con una sola, el ruido diario daba un rojo falso en la mitad de las misiones simuladas).
- Con la regla v0.3 (38,5 °C con 2 lecturas seguidas) el semáforo detecta el 73 % de las infecciones simuladas (64 % sin esa regla) y el costo en falsas alarmas es de 0,02 episodios por misión (1,82 contra 1,80). Con una sola lectura el costo era de 0,44 (2,24 contra 1,80). Un límite de 39,0 °C casi no mejora la detección. Los chequeos de validación de temperatura del simulador: 2 de 28 quedan fuera de tolerancia (README, límite 4).
**Cómo se visualiza:** igual que la FC; el subtítulo de la gráfica declara el límite supuesto. `charts/tendencia_temp_synthetic.png`.

## 5. Glucosa en ayunas
**Categoría:** metabólico.
**Qué mide y por qué importa:** glucosa capilar en ayunas, entrada **manual semanal**. La resistencia a la insulina sube en vuelo (Hughson 2016, 4 hombres y 4 mujeres, solo resumen, [sin verificar]) y la inmersión seca la empeora (análogo).
**Variables de entrada:** `glucose_mgdl` (mg/dl), 1 lectura cada 7 días; analizador portátil PCBA con cartuchos EC8+ (rango del aparato 20–450 mg/dl, que no es un rango normal), según el catálogo CHeCS de 2011.
**Fórmula y ejemplo (calculado con código):** **no hay banda personal.** En 28 días entran 4 lecturas y el mínimo exigido es 14, así que la banda nunca se calcula. Solo valen los límites absolutos. El indicador está fuera del semáforo mínimo (`mvp.include_glucose = 0`).
**Valores de referencia y umbrales (solo se aplican si se activa el indicador):**
- Amarillo: ≥100 mg/dl (glucosa alterada en ayunas, 100–125) o <70 mg/dl (hipoglucemia nivel 1). Rojo: ≥126 mg/dl (criterio de diabetes) o <54 mg/dl (nivel 2). `referencia`: ADA, *Standards of Care in Diabetes 2026*, sección 2 https://doi.org/10.2337/dc26-S002 y sección 6, tabla 6.4 https://pmc.ncbi.nlm.nih.gov/articles/PMC12690178 [verificado]. Son criterios diagnósticos de la Tierra, no rangos poblacionales.
**Fuente de los datos:** sintética. **Media 88 mg/dl, DE 8 mg/dl y deriva 0: `supuesto` del equipo (decisión de Isa, 14 nov), sin fuente.** Solo el límite superior normal (<100 mg/dl) tiene fuente. Análogo: VIVALDI, inmersión seca de 5 días (ESA), glucosa en ayunas <6,1 mmol/l y sin cambio, *Commun Med* 2026, https://doi.org/10.1038/s43856-026-01540-7 [verificado].
**Limitaciones y sesgos:**
- **Excepción declarada a la regla «sin fuente, no entra»:** entra como supuesto del equipo.
- No hay valores absolutos de glucosa en vuelo en acceso abierto.
- El efecto por sexo es contradictorio (Hughson: mayor en hombres; VIVALDI: mayor en mujeres), así que no se modela.
- Con lecturas semanales el semáforo reacciona tarde: en v0.2 la sensibilidad para «glucosa alta» fue de 0,125.
**Cómo se visualiza:** puntos semanales con líneas de referencia en 70 y 126 mg/dl, marcados «fuera del semáforo mínimo». `charts/tendencia_glucose_synthetic.png`.

## 6. Horas de sueño
**Categoría:** sueño.
**Qué mide y por qué importa:** horas dormidas la noche previa. En vuelo los astronautas duermen menos (7 de 10 en Otsuka 2021) y el déficit afecta el estado de ánimo, el rendimiento y la FC.
**Variables de entrada:** `sleep_h` (h), 1 al día; el equipo de la ISS es el Actiwatch Spectrum (muñeca, movimiento y luz).
**Fórmula y ejemplo (calculado con código):** SIM-001, día 60: n = 28, media 5,83 h, DE 0,53, DE de predicción 0,54. Solo banda inferior: 5,83 − 2,5 · 0,54 = **4,47 h**. Lectura 6,44 h → verde.
**Valores de referencia y umbrales:**
- **No hay límite absoluto.** Solo banda personal hacia abajo: `supuesto`.
- Contexto, no alarma: 7 h o más por noche (Watson et al., AASM y SRS, 2015, https://www.aasm.org/resources/pdf/adultsleepdurationconsensus.pdf `referencia`); NASA reporta 6–6,5 h de promedio en vuelo (NASA OCHMO, *Sleep Accommodations*, Rev A, 2021, [verificado]). Un umbral fijo de 7 h estaría en amarillo casi todo el vuelo.
**Fuente de los datos:** sintética. 70 % reduce el sueño y la caída total es −72,4 min (454,0 → 381,6 min) con constante de tiempo ~22 días: Otsuka et al., *Sci Rep* 2021, https://link.springer.com/10.1038/s41598-021-94478-w `medido` [verificado] (10 astronautas, 9 hombres y 1 mujer, ~156 días). Media previa de 7,4 h, DE entre personas y ruido nocturno: `supuesto`. Aumento en los 3 que durmieron más (+0,5 h): `sin fuente`.
**Limitaciones y sesgos:** muestra de 10 y casi todos hombres; la dispersión individual no se publica; la sensibilidad del semáforo a la «falta de sueño» fue moderada (v0.2: 0,43); el actígrafo estima el sueño por movimiento, con error.
**Cómo se visualiza:** igual que la FC, banda solo inferior. `charts/tendencia_sleep_synthetic.png`.

## 7. Estado de ánimo
**Categoría:** psicológico.
**Qué mide y por qué importa:** autorreporte diario del ánimo en una escala de 1 a 5 (más alto = mejor). El aislamiento y el confinamiento afectan el ánimo; en los análogos el nivel de grupo es estable, así que lo útil es la desviación personal.
**Variables de entrada:** `mood_1_5` (puntaje), 1 al día, autorreporte.
**Fórmula y ejemplo (calculado con código):** SIM-001, día 60: n = 28, media 3,83, DE 0,36, DE de predicción 0,37. Solo banda inferior: 3,83 − 2,5 · 0,37 = **2,91**. Lectura 4,3 → verde.
**Valores de referencia y umbrales:**
- **No hay umbral con fuente.** Solo banda personal hacia abajo: `supuesto` del equipo.
- Alternativa documentada, **no implementada** (Isa decidió dejarlo como supuesto del equipo): GHQ-12 en puntuación Likert 0–36 (más alto = peor): media 5,62 ± 4,25 (n = 730), vigilar con >7–8 puntos y atención urgente con >11–12; un cambio de ≥8 puntos entre aplicaciones apareció en una minoría con deterioro. *Afr J Psychol Assess* 8:195, 2026, https://doi.org/10.4102/ajopa.v8i0.195 `referencia` (análogo) [verificado].
**Fuente de los datos:** sintética. Media 3,9, DE entre personas 0,3 y dentro 0,4: `sin fuente`. Cambio en confinamiento = 0: SIRIUS-19, PANAS sin cambio en 120 días (6 personas), Abeln et al., *BMC Neurosci* 23:41, 2022, https://doi.org/10.1186/s12868-022-00723-x [verificado]; Mars-500, POMS sin diferencias significativas (6 hombres, 520 días), Wang et al., *PLoS One* 9(4):e87087, 2014, https://doi.org/10.1371/journal.pone.0087087 [verificado]. `referencia` (análogo).
**Limitaciones y sesgos:**
- **Excepción declarada a la regla «sin fuente, no entra»:** la escala 1–5 no es un instrumento validado.
- El GHQ-12 de arriba es de trabajadores sudafricanos en entornos aislados (no astronautas), tiene sesgo a la derecha (+1,3) y se validó como medición puntual, no diaria.
- En los análogos n = 6.
- Sensibilidad a «ánimo bajo» en v0.2: 0,37.
**Cómo se visualiza:** igual que la FC, banda solo inferior; el subtítulo declara «supuesto del equipo». `charts/tendencia_mood_synthetic.png`.

## 8. Ejercicio y aptitud física
**Categoría:** musculoesquelético y cardiorrespiratorio (contramedida).
**Qué mide y por qué importa:** minutos de ejercicio completados cada día (adherencia a la contramedida) y la aptitud física respecto a la previa al vuelo, medida en una prueba cada 30 días. La microgravedad quita 10–12 % de la fuerza y la aptitud aeróbica en promedio.
**Variables de entrada:** `exercise_min` (min/día, solo vuelo) y `fitness_pct_preflight` (% de la capacidad previa, solo días de prueba).
**Fórmula y ejemplo (calculado con código):** una sesión cuenta como hecha si tiene ≥90 min. **Amarillo** si hay <3 sesiones hechas en los últimos 7 días de vuelo. Ejemplo: SIM-002, día 38, minutos de los 7 días previos [125, 158, 0, 0, 0, 0, 0] → 2 sesiones <3 → amarillo. **Rojo** si la última aptitud medida es <80 % de la previa; en la misión simulada el valor más bajo es 85,8 % (SIM-003, día 180), así que ninguno baja de 80 %.
**Valores de referencia y umbrales:**
- Rojo: aptitud <80 %. `referencia`: NASA-STD-3001 Vol. 1 Rev. C, 4.1.3 y 4.6.2 (mantener al menos 80 % de la capacidad previa). https://standards.nasa.gov/sites/default/files/standards/NASA/C//nasa-std-3001-vol-1-rev-c-signature.pdf [verificado, lectura parcial]
- Amarillo: <3 sesiones en 7 días y 90 min por sesión: `supuesto`. Con 4 sesiones los falsos suben; con 5, ~15 % de los días limpios en amarillo (`out/evaluation/sensitivity_exercise.csv`).
**Fuente de los datos:** sintética. Prescripción de 6 días por semana y bloques de 2,5 h (1,5 h de fuerza y 1 h aeróbica): Guilliams, Nieschwitz, Hoellen y Loehr, Wyle, NTRS 20110016265, https://ntrs.nasa.gov/api/citations/20110016265/downloads/20110016265.pdf `medido` [verificado]. Pérdida media de 11 %: NASA HRP, R09, https://www.nasa.gov/reference/risk-of-reduced-cardiorespiratory-and-musculoskeletal-fitness/ `medido` [verificado]. Adherencia de 92 %, ruido y curva temporal de la pérdida: `supuesto`.
**Limitaciones y sesgos:**
- La fracción de pérdida >20 % usa el extremo inferior del rango publicado (12 %; la fuente da 12–38 % según el método) porque con una media de 11 % la lognormal no alcanza proporciones mayores.
- La página de R09 no indica la muestra.
- La prueba de aptitud cada 30 días es un `supuesto`.
**Cómo se visualiza:** barras de minutos por día, con la aptitud en % sobre las barras y franja de semáforo. `charts/tendencia_exercise_synthetic.png`.
