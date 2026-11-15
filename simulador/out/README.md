# Dataset de misión SINTÉTICO (v0.3)

> **DATOS SINTÉTICOS.** Todo lo que hay en esta carpeta sale de un simulador. **No son mediciones de astronautas reales.** Cada fila lleva `data_origin = synthetic` y cada perfil se llama `SIM-###`.

NASA Space Apps Challenge 2026, reto "Create Health Monitoring Software for Astronauts on Space Missions".

> **Para qué sirve y para qué no.** El simulador sirve para **probar la lógica del semáforo con verdad conocida** (sabemos qué días hay un evento y cuáles son errores del sensor). **No es un modelo fisiológico validado.** Sus resultados no describen a astronautas reales.

**Mensaje para la presentación (texto listo):** "Los datos de la demo son sintéticos. El simulador no es un modelo fisiológico validado: lo usamos para probar la lógica del semáforo con verdad conocida. Las métricas del semáforo son contra anomalías que inventamos nosotros. Comparamos el simulador con valores publicados en astronautas (Norsk 2015) y **no coincide** en hombres: la presión sale 11–16 mmHg más baja y la FC unos 8 lpm más alta, porque partimos de adultos jóvenes de la población general medidos sentados y no de astronautas medidos durante 24 horas. Por eso los umbrales son decisiones del equipo, declaradas como supuesto, y hay que validarlos con datos reales cuando existan."

**Si te preguntan por el semáforo (cifras de la v0.3, 200 misiones simuladas, contra anomalías inventadas):** 1,8 episodios de falsa alerta por misión de 180 días (0,8 en rojo). El 5,8 % de los días sin evento queda en amarillo o rojo (1,5 % en rojo). Una alerta nueva aparece dentro del evento o en los 3 días siguientes en el 62 % de los eventos (38 % en rojo), con mediana de 2 días. Por tipo: caída de SpO2 94 %, abandono del ejercicio 90 %, infección 73 %, pico de PA 47 %, falta de sueño 43 %, ánimo bajo 37 % y glucosa alta 12 % (la glucosa está fuera del semáforo mínimo). **Es un rango, no un número fijo:** con el ruido ×1,5 la detección baja a 54 %, y con eventos a la mitad de tamaño baja a 44 %; ni el ruido ni el tamaño de los eventos tienen fuente.

## Qué se simuló

- 4 astronautas simulados (2 F, 2 M), 30 días previos al vuelo (ancla personal) y 180 días de vuelo. No existe el día 0.
- 8 indicadores diarios: FC en reposo, presión arterial (sistólica y diastólica), SpO2, temperatura (escala oral), glucosa en ayunas (manual semanal), horas de sueño, estado de ánimo (1–5) y ejercicio/aptitud física.
- Serie intradiaria de FC cada 30 min con ritmo circadiano y contexto (vigilia, sueño, ejercicio).
- Anomalías con etiqueta de verdad (infección, falta de sueño, pico de PA, caída de SpO2, ánimo bajo, abandono del ejercicio, glucosa alta) y **artefactos de sensor** de un día (errores de medición, no eventos de salud).
- Estado del semáforo v0.3 por día e indicador (umbrales **provisionales**).

Modelo por indicador: línea base personal + deriva en vuelo + ritmo circadiano (solo FC) + ruido AR(1) + anomalías.

## Qué cambió en la v0.3 (temperatura)

En la v0.2 no había límite absoluto de temperatura después del día 14 de vuelo. El muestreo normal dejaba a 2 de los 4 astronautas simulados con la temperatura en ≥38,0 °C el 87 % y el 94 % de los días de vuelo, y el semáforo seguía en verde (la línea base móvil de 28 días absorbe una subida lenta). En la v0.3:

1. **Tope de la meseta simulada en 38,0 °C** (`temp.plateau_max_c`, supuesto). Stahn 2017 deja a algunas personas cerca de 38 °C en reposo y no hay dato medido por encima. El tope recorta la deriva, no la línea base.
2. **Rojo fijo de 38,5 °C desde el día 15, con 2 lecturas seguidas** (`absolute_red.temp_gt_inflight` y `temp_inflight_consecutive_days`, supuesto del equipo, sin fuente publicada). Los primeros 14 días siguen con 38,0 °C (referencia terrestre, MSD Manual).

Efecto medido con 200 misiones (`evaluation/tradeoff_table.csv`):

| Variante | Falsos amarillo+ por misión | Falsos rojos por misión | Recall amarillo+ | Recall rojo |
|---|---|---|---|---|
| F. v0.2, sin rojo de temperatura en vuelo | 1,80 | 0,78 | 0,608 | 0,348 |
| G. rojo de 38,5 °C con 1 lectura | 2,24 | 1,25 | 0,643 | 0,413 |
| **H. v0.3: 38,5 °C con 2 lecturas seguidas** | **1,82** | **0,80** | **0,623** | **0,379** |
| 39,0 °C con 2 lecturas | 1,80 | 0,78 | 0,609 | 0,354 |
| 38,0 °C con 2 lecturas | 3,52 | 2,76 | 0,669 | 0,476 |

La detección de infecciones simuladas sube de 0,64 a 0,73. El costo en falsas alarmas es de 0,02 episodios por misión. Las cifras dependen de la magnitud de la infección simulada (+1,3 °C, supuesto).

## De dónde sale cada parámetro

Cada parámetro es `[valor, estado, fuente]` en [`params_used.json`](params_used.json) (copia de `sim/sim_params.json`). Estados: `medido` (publicado en astronautas), `referencia` (adultos en Tierra o guía clínica), `derivado`, `supuesto` (decisión del equipo) y `sin fuente`. Resumen:

| Indicador | Línea base | Cambio en vuelo | Estado |
|---|---|---|---|
| FC en reposo | NHSR 41 (CDC 2011), adultos 20–39 de EE. UU. | sin cambio (Norsk et al., J Physiol 2015, 8 hombres) | referencia / medido |
| Presión arterial | NHSR 35 (CDC 2011) | −8/−9 mmHg (Norsk 2015, hombres); mujeres: mismo cambio relativo | medido / **supuesto** para mujeres |
| SpO2 | 97,5 % | sin cambio (Conkin 2017) | supuesto / medido |
| Temperatura | 36,6 °C oral (Obermeyer, BMJ 2017; Geneva 2019) | +1,01 °C, meseta ~75 d (Stahn et al., Sci Rep 2017, sensor de frente); **meseta individual recortada en 38,0 °C (supuesto, v0.3)** | referencia / medido / **supuesto** (tope) |
| Glucosa | 88 mg/dl | sin dato en vuelo | **supuesto del equipo, sin respaldo publicado** |
| Sueño | 7,4 h | 7 de 10 duermen menos, −72 min (Otsuka et al., Sci Rep 2021) | supuesto / medido |
| Ánimo (1–5) | 3,9 | sin dato | **supuesto del equipo, sin respaldo publicado** |
| Ejercicio / aptitud | 150 min, 6 d/semana (Guilliams, NTRS 20110016265) | pérdida media 10–12 % (NASA HRP R09) | medido |
| Anomalías y artefactos | tasas, duraciones y magnitudes | — | **supuesto** (todas) |

## Reproducir

Semilla: **42**. Python 3.13+ con `numpy pandas scipy matplotlib jsonschema`.

```bash
python3 sim/simulator.py --out out
```

```bash
python3 schema/validate.py out/mission_synthetic.json
```

```bash
python3 sim/evaluate.py
```

```bash
python3 charts/make_charts.py
```

```bash
python3 fichas/ejemplos_calculo.py
```

(Desde la carpeta `hackaton_nasa_sim/`. `evaluate.py` tarda unos 7 minutos: 200 misiones simuladas. El último comando recalcula los ejemplos numéricos de las fichas y los compara con `semaforo.py`.)

## Archivos

| Archivo | Qué es |
|---|---|
| `mission_synthetic.json` | Todo en un archivo. Contrato: `schema/mission_synthetic.schema.json` (v0.2.0) |
| `mission_synthetic_daily.csv` | Una fila por astronauta y día; diccionario en `data_dictionary.csv` |
| `mission_synthetic_intraday_hr.csv` | FC cada 30 min con contexto (0 vigilia, 1 sueño, 2 ejercicio) |
| `mission_synthetic_anomalies.csv` | Anomalías con etiqueta de verdad; `is_health_event = False` = artefacto de sensor |
| `mission_synthetic_semaforo.csv` | Estado del semáforo por día e indicador, con línea base y banda |
| `params_used.json` | Parámetros con estado y fuente |
| `evaluation/` | Verificación de implementación (circular), hold-out, robustez, evaluación del semáforo y tabla de compromisos |
| `../fichas/FICHAS_indicadores.md` | Las 8 fichas de indicador (fórmula con ejemplo, umbrales con su fuente, supuestos y limitaciones) |

## Validación independiente

**(1) Hold-out con valores absolutos en vuelo** (`evaluation/holdout_checks.csv`). Los objetivos viven en `sim/holdout_targets.json`, aparte de `sim_params.json`, y **no se usan para calibrar**. Lo fuera de muestra es el nivel absoluto: el cambio de −8/−9 mmHg sí se calibró con Norsk 2015. Fuente: vacío 1 de `RESULTADOS_investigacion.md`.

| Objetivo (fuente) | Valor | Simulado | Diferencia |
|---|---|---|---|
| PA sistólica en vuelo, hombres (Norsk 2015, 24 h) [verificado] | 121 mmHg | 109,6 | −11,4 (−2,0 DE) |
| PA diastólica en vuelo, hombres (Norsk 2015) [verificado] | 76 mmHg | 59,7 | −16,3 (−2,9 DE) |
| FC en vuelo, hombres (Norsk 2015, 24 h) [verificado] | 63 lpm | 71,0 | +8,0 (+1,4 DE) |
| FC de sueño en vuelo, hombres (Norsk 2015) [verificado] | 58 lpm | 65,6 | +7,6 (+2,7 DE) |
| PA sistólica de 24 h, ambos sexos (Fu 2019, dedo) [sin verificar] | 106 mmHg | 105,6 | −0,4 |
| Mujeres | sin fuente | — | — |

**Lectura:** el simulador **no pasa** el hold-out en hombres. La PA sale baja y la FC alta. Es coherente con su línea base (adultos de 18–39 años de EE. UU., medición en reposo a las 08:30) frente a astronautas de 45–53 años medidos durante 24 h. El acierto con Fu 2019 es casual: allí la presión se midió en el dedo, que da valores más bajos que el brazalete.

**(2) Robustez del semáforo** (`evaluation/robustness.csv`). Escalé el simulador ×0,5 y ×1,5, un grupo a la vez y con la misma semilla, sin tocar los umbrales del semáforo v0.3. 200 misiones por fila.

| Simulador | Falsos amarillo+ por misión | Falsos rojos por misión | Recall amarillo+ | Recall rojo |
|---|---|---|---|---|
| base | 1,84 | 0,74 | 0,61 | 0,37 |
| deriva ×0,5 / ×1,5 | 1,81 / 1,88 | 0,71 / 0,77 | 0,60 / 0,63 | 0,35 / 0,39 |
| ruido ×0,5 / ×1,5 | 1,28 / **2,98** | 0,52 / **1,32** | 0,77 / **0,54** | 0,60 / **0,29** |
| magnitud de eventos ×0,5 / ×1,5 | 1,85 / 1,82 | 0,81 / 0,79 | **0,44** / 0,73 | **0,14** / 0,56 |

**Lectura:** el semáforo casi no depende de la deriva (la línea base personal la absorbe). Sí depende mucho del ruido día a día y del tamaño de los eventos, y **ninguno de los dos tiene fuente** (son supuestos). Por eso las cifras de desempeño del semáforo no se pueden presentar como un número fijo: son un rango que depende de supuestos.

## Limitaciones (léelas antes de presentar)

1. **Los 28 chequeos de `validation_checks.csv` son circulares** ("verificación de implementación"; 26 dentro de tolerancia y 2 fuera, los dos de temperatura, ver el punto 4). Las derivas se calibraron con las mismas cifras publicadas, y las DE de la línea base se derivaron de los mismos percentiles P5/P95 (NHSR, Obermeyer) contra los que se comparan. Comprueban el código, no el realismo. Lo independiente está en la sección "Validación independiente".
2. **La población base no es de astronautas.** La FC y la PA salen de adultos de EE. UU. de 18–39 años. Frente a Norsk 2015 (astronautas de 45–53 años, PA de 24 h), los hombres simulados quedan ~11 mmHg más bajos en sistólica y ~16 en diastólica en vuelo (medición distinta: reposo sentado frente a 24 h ambulatoria). Algunos perfiles tienen FC de reposo cercana a 100 lpm, poco realista en astronautas.
3. **Mujeres:** no hay datos de FC ni PA en vuelo separados por sexo. Se aplica el mismo cambio relativo que a los hombres (supuesto).
4. **Temperatura:** en escala oral. Stahn 2017 midió en la frente; el cambio se suma como delta. **El sitio del sensor real está pendiente (Hugo).** Con el tope de 38,0 °C (supuesto, v0.3), el 6 % de los astronautas simulados sanos promedia más de 38,0 °C en los días 76–180 (eran 19 % sin tope); el chequeo pide 5 % o menos, así que **sigue fuera por un punto**. El cambio simulado hacia el día 75 (+0,93 °C) es menor que el que se lee en la figura de Stahn (+1,4 °C, lectura ±0,1) y ese chequeo también falla, como en la v0.2: el modelo sube de forma exponencial y no reproduce el pico del día 75. El tope de 38,0 °C es una lectura gruesa de la figura, no una cifra publicada.
5. **Glucosa y ánimo son supuestos del equipo** sin respaldo publicado. Con muestreo semanal, la glucosa no ve eventos de 2 días.
6. **Las anomalías las inventamos nosotros.** El desempeño del semáforo sirve para comparar configuraciones, no para afirmar sensibilidad clínica.
7. NASA no publica criterios numéricos de alarma. Todo umbral marcado `supuesto` es decisión del equipo y está **pendiente**.
8. **Temperatura en vuelo (revisado en la v0.3):** rojo fijo de 38,0 °C los primeros 14 días y de **38,5 °C con 2 lecturas seguidas desde el día 15**, supuesto del equipo sin fuente publicada (ver "Qué cambió en la v0.3"). Costo: una fiebre moderada durante la subida de la deriva puede tardar en alertar; la regla detecta el 73 % de las infecciones simuladas, y esa magnitud (+1,3 °C) también es un supuesto. Si el sensor real mide temperatura central (rectal o esofágica), hay que sumar ~0,47 °C a la escala oral (Geneva 2019, `derivado`) y revisar los dos límites.
9. **Los umbrales de la v0.3 siguen pendientes de decisión del equipo.** Un solo indicador de presión (la sistólica) evitaría que «dos amarillos = rojo» se dispare por la diastólica y la sistólica a la vez.
