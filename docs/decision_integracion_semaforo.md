# Decisión: integración del semáforo de línea base personal en la app

Fecha: 14-nov-2026 · Autor: agente arquitecto · Estado: **decidido** (los puntos abiertos están en la sección 7)

Resumen: el backend **importa** `simulador/sim/semaforo.py` tal como está y lo usa como **única lógica de color**.
Los rangos fijos normal/atención/crítico de `thresholds.py` **dejan de decidir colores**; solo los límites
absolutos de `semaforo_config.json` actúan sin línea base. Los nombres canónicos son las claves cortas del
simulador (`hr_rest`, `bp_sys`, …). El simulador no se renombra.

---

## 1. Integración del semáforo

### 1.1 Importar, no mover ni reescribir
- `backend/semaforo_bridge.py` agrega `<repo>/simulador/sim` a `sys.path` e importa `semaforo as sf`.
  `sf.Config()` lee por defecto `simulador/sim/semaforo_config.json`.
- **Por qué:** `simulator.py` y `evaluate.py` hacen `import semaforo`; moverlo los rompe y copiarlo crea dos
  versiones de la lógica evaluada (1,82 falsos episodios por misión). Una sola fuente: lo que se evaluó es lo que corre en la app.
  Costo: el backend depende de la ruta relativa `../simulador/sim` y de numpy/pandas (ya están en el venv).
- No se modifica `semaforo.py` para la integración. (La única modificación propuesta está en el punto 4 y queda detrás de una opción de config.)

### 1.2 Convivencia con los umbrales clínicos fijos
- **Una sola lógica de color: la del semáforo.** Las bandas fijas `normal`/`attention` de `thresholds.py` y
  `thresholds.ts` se **eliminan** de la decisión de color. Motivo: es justo lo que el equipo argumenta que da falsas
  alarmas en vuelo (sueño de 6 h, presión −8 mmHg), y tener dos lógicas mostraría colores contradictorios.
- Lo que sí actúa siempre, con o sin línea base, son los **límites absolutos de `semaforo_config.json`**:
  `absolute_red.*` → rojo; `absolute_yellow.*` → amarillo. La línea base personal produce amarillo (3 lecturas seguidas
  fuera de banda) o rojo (salto ≥ 4 DE confirmado).
- `thresholds.py` queda como **metadatos**: etiqueta, unidad, rango de entrada plausible (validación), parte del
  cuerpo y recomendaciones. Los límites absolutos **no se copian** ahí: `/indicators` los lee de la config.
- **Glucosa:** `mvp.include_glucose = 0`, así que `run_semaforo` no la evalúa. El backend la evalúa aparte, solo con
  reglas fijas (ayunas, ADA 2026, valores de la config): rojo `< glucose_lt` (54) o `>= glucose_gt` (126); amarillo
  `< glucose_yellow_low` (70) o `>= glucose_yellow_high` (100). Cuenta para el estado global con `max()`, pero
  **no** cuenta para la regla «dos amarillos = rojo» (igual que en la configuración evaluada).

### 1.3 Pocas lecturas, primeros días de vuelo, prevuelo
| Situación | Comportamiento | Quién lo hace |
|---|---|---|
| Menos de 14 lecturas válidas en la ventana de 28 días | Solo límites absolutos; `baseline.ready=false`; motivo informativo `sin_linea_base` | `run_semaforo` (ya lo hace) |
| Días de vuelo 1–14 | Solo límites absolutos (temperatura con 38,0 °C); motivo informativo `adaptacion_inicial` | `run_semaforo` (ya lo hace) |
| Prevuelo (día < 0) | `run_semaforo` no evalúa días previos. El backend aplica **solo límites absolutos** (temperatura con 38,0 °C, sin FC<50, que en el simulador aplica solo en vuelo; se respeta) | `semaforo_bridge.absolute_status()` |
| Día sin lectura de un indicador | Se arrastra el estado del día anterior (regla del simulador); `carried=true` | `run_semaforo` |

Consecuencia honesta: un astronauta nuevo sin historia solo ve rojo o amarillo por límites clínicos. Sueño y ánimo
no tienen límite absoluto, así que hasta tener línea base nunca alertan (punto abierto 7.3).

### 1.4 Modelo de datos
- **Sí hace falta día de misión y fase.** Nueva tabla `Astronaut(astronaut_id PK, launch_date: date, source: str)`.
  `source ∈ {"manual","synthetic"}`.
- `HealthRecord` agrega `mission_day: int` (desnormalizado, se calcula al insertar) y `source: str`
  (`"manual" | "sensor" | "synthetic"`).
- Convención (la del simulador): día 1 = día del lanzamiento, días previos −N…−1, **no existe el día 0**.
  Fecha en UTC (la ISS usa GMT):
  `delta = (timestamp_utc.date() - launch_date).days; mission_day = delta + 1 if delta >= 0 else delta`.
- Si llega un registro para un `astronaut_id` que no existe, se crea con `launch_date = hoy (UTC)` y `source="manual"`.
- Fase: `"preflight"` si `mission_day < 0`, si no `"inflight"`. Se calcula, no se guarda.

### 1.5 Cálculo de la línea base desde la BD (por petición, sin caché)
`compute_status(session, astronaut_id)` en `semaforo_bridge.py`:
1. Leer todos los registros del astronauta (son ≤ ~250 filas).
2. Agregar por `mission_day`: **última lectura no nula del día por campo** (`groupby("mission_day").last()` sobre
   registros ordenados por timestamp; `last()` de pandas ignora NaN por columna). Así, «vuelve a medir en 30 min» reemplaza la lectura anterior.
3. **Reindexar** a un rango continuo `min_day…max_day` **sin el 0**, con NaN en los días sin datos.
   Es obligatorio: `run_semaforo` cuenta la ventana por posición, no por fecha.
4. Renombrar a las columnas del simulador con `sf.IND` + `{"exercise": "exercise_min", "fitness": "fitness_pct_preflight"}`;
   agregar `astronaut_id` y `mission_day`; crear como NaN cualquier columna que falte.
5. Si `max_day < 0`: solo `absolute_status()`. Si no: `sf.run_semaforo(df, CFG, return_bands=True, return_reasons=True)`
   y tomar la última fila.
6. Glucosa aparte (1.2). Estado global = `max(overall_semaforo, glucosa)`.
7. Derivar el motivo de cada indicador (1.6).

No se usan `truth_*`, `latent_truth`, `quality_flags` ni `data_origin` del CSV en ningún cálculo.

### 1.6 Motivos (`reason.code`) para el frontend
`run_semaforo` solo dice `hr_rest:Y`. El backend deriva el motivo de la última fila, en este orden (gana el primero que se cumpla):

| code | Estado | Condición | Texto (plantilla) |
|---|---|---|---|
| `limite_clinico` | rojo | `status_k == 2` y el valor supera el límite absoluto aplicable (temperatura: 38,0 °C si día ≤ 14 o prevuelo; 38,5 °C en vuelo) | «Límite clínico: {label} {valor} {unidad} (límite {op} {lim})» |
| `salto_confirmado` | rojo | `status_k == 2` y no aplica lo anterior | «Cambio brusco respecto a tu línea base, confirmado al día siguiente» |
| `aptitud_baja` | rojo | `k == "fitness"` y `status == 2` | «Aptitud física {v} % de la previa (mínimo 80 %)» |
| `limite_clinico_bajo` | amarillo | `k == "hr_rest"`, valor < 50, día > 0 | «FC en reposo bajo 50 lpm (bradicardia)» |
| `caida_spo2` | amarillo | `k == "spo2"` y `base - valor >= 3` | «SpO2 cayó {n} puntos bajo tu línea base» |
| `pocas_sesiones` | amarillo | `k == "exercise"` | «{n} sesiones de ≥ 90 min en 7 días (mínimo 3)» |
| `glucosa_ayunas` | amarillo/rojo | `k == "glucose"` | «Glucosa en ayunas {v} mg/dL (rango de referencia 70–99)» |
| `banda_personal` | amarillo | el resto de amarillos | «Fuera de tu banda personal {d} días seguidos (banda {lo}–{hi} {unidad})» |
| `sin_linea_base` | verde (info) | `base_k` es NaN | «Sin línea base todavía: solo límites clínicos» |
| `adaptacion_inicial` | verde (info) | 1 ≤ día ≤ 14 | «Días 1–14 de vuelo: solo límites clínicos» |
| `prevuelo` | verde (info) | día < 0 | «Prevuelo: se está construyendo tu línea base» |
| `null` | verde | resto | — |

`days_out` para `banda_personal`: cuenta hacia atrás los días con lectura cuyo valor está fuera de `[lo_k, hi_k]`
(ignorar el lado que sea NaN). Global: si hay 2 o más amarillos (sin glucosa) → `overall.reasons` incluye
`{"code": "dos_amarillos"}` con la lista de indicadores. Si no hay lectura del indicador ese día → `carried=true`
y el motivo se calcula sobre su último día con lectura.

Vocabulario de estado en la API: se mantiene `"normal" | "attention" | "critical"` (0/1/2 del simulador) para no
romper el frontend. La interfaz muestra «Verde / Amarillo / Rojo».

### 1.7 Datos sintéticos como demo: sí
- `backend/seed_demo.py` carga `simulador/out/mission_synthetic_daily.csv` (4 astronautas, días −30…180).
  `launch_date = hoy_UTC − 179 días`, así el día 180 es hoy y una entrada manual cae sobre una historia completa
  (es la mejor demostración de la banda personal). `timestamp = fecha del día a las 08:30 UTC`, `source="synthetic"`.
- Solo lee las columnas de indicadores, `astronaut_id` y `mission_day`. **Descarta** `truth_*`, `quality_flags`, `sex`,
  `phase` y `data_origin`. Es idempotente: borra los registros `synthetic` y los astronautas `SIM-*` antes de insertar.
- La interfaz muestra una etiqueta fija «DATOS SINTÉTICOS» cuando `astronaut.source == "synthetic"`.

### 1.8 Frontend y `thresholds.ts` (modo local)
- El color del mapa corporal y de las tarjetas registradas viene de `GET /status` (servidor). El frontend **no**
  calcula la línea base.
- `thresholds.ts` se reescribe como `indicators.ts`: metadatos (etiqueta, unidad, rango de entrada, parte del cuerpo)
  y **límites absolutos** copiados de la config, más `evaluateAbsolute(key, value, missionDay)`. Se usa para
  (a) la vista previa mientras se escribe en la tarjeta, marcada «vista previa: solo límite clínico», y
  (b) el modo sin backend, con el aviso «Modo local: solo límites clínicos, sin línea base personal».
- Al arrancar, el frontend pide `GET /indicators` y, si responde, **sobrescribe** la copia local; la copia solo
  manda sin conexión. Comentario de sincronización: «espejo de simulador/sim/semaforo_config.json».

---

## 2. Nombres canónicos

Clave canónica = clave corta del simulador (la misma de `semaforo_config.json`, `sf.IND` y `status_*`). Se usa en la
BD, la API y el frontend. Los CSV del simulador **conservan** sus columnas con unidad (`hr_rest_bpm`…): son el
formato de archivo, y `sf.IND` es la traducción.

| App (viejo) | Simulador: clave / columna CSV | **Canónico** | Unidad | Etiqueta UI |
|---|---|---|---|---|
| `heart_rate` | `hr_rest` / `hr_rest_bpm` | `hr_rest` | lpm (reposo, sentado, mañana) | FC en reposo |
| `systolic_bp` | `bp_sys` / `bp_sys_mmhg` | `bp_sys` | mmHg | Presión sistólica |
| — | `bp_dia` / `bp_dia_mmhg` | `bp_dia` | mmHg | Presión diastólica |
| `spo2` | `spo2` / `spo2_pct` | `spo2` | % | SpO2 |
| `body_temp` | `temp` / `temp_c` | `temp` | °C (equivalente oral) | Temperatura |
| `glucose` | `glucose` / `glucose_mgdl` | `glucose` | mg/dL (ayunas) | Glucosa en ayunas |
| `sleep_hours` | `sleep` / `sleep_h` | `sleep` | h (noche previa) | Horas de sueño |
| `mood` | `mood` / `mood_1_5` | `mood` | 1–5 | Estado de ánimo |
| — | `exercise` / `exercise_min` | `exercise` | min/día | Ejercicio |
| — | `fitness` / `fitness_pct_preflight` | `fitness` | % de la aptitud previa | Aptitud física (prueba periódica) |

Rangos de entrada plausibles (validación 422, no son umbrales): hr_rest 20–250, bp_sys 50–260, bp_dia 30–160,
spo2 50–100, temp 30–45, glucose 20–600, sleep 0–24, mood 1–5, exercise 0–600, fitness 0–150.

Archivos a renombrar: `backend/models.py`, `backend/thresholds.py`, `backend/main.py`,
`frontend/src/data/thresholds.ts` (→ `indicators.ts`), `frontend/src/App.tsx`, `frontend/src/components/BodyMap.tsx`,
`HistoryChart.tsx`, `IndicatorCard.tsx`, `docs/health_indicators.md`, `CLAUDE.md` (sección Indicadores).
**Nada en `simulador/`.**

---

## 3. Sistólica 85–90 mmHg
**Decisión: no es «crítico» ni «atención» por regla fija.** Se juzga contra la banda personal.
- `semaforo_config.json` no tiene límite rojo inferior para la sistólica, y `absolute_yellow.bp_sys_lt = null`
  (ESC 2018 «< 90» está sin verificar y es de la prueba de pie, no de reposo en microgravedad). En vuelo la presión
  baja de forma normal (Norsk 2015), así que un 88 puede ser normal para esa persona.
- `docs/health_indicators.md` estaba mal («crítico <90»): esa tabla se reemplaza por los límites absolutos de la
  config más la explicación de la línea base. El código («atención») también desaparece con 1.2.
- Si el equipo activa `bp_sys_lt = 90`, la app lo aplica sin tocar código (amarillo, solo en vuelo). Ver 7.1.

## 4. ¿Presión como un solo indicador?
**Opinión: sí, para la regla «dos amarillos = rojo».** Hay que mostrar y evaluar las dos lecturas por separado
(cada una con su banda y su límite absoluto), pero un amarillo de sistólica y uno de diastólica casi siempre son el
mismo evento fisiológico. Contarlos como dos convierte un solo hallazgo en rojo, que es justo la falsa escalada que
el semáforo quiere evitar. Implementación: opción `general.bp_counts_once` en la config. Con 1, `n_yellow` usa
`max(status_bp_sys, status_bp_dia)` como un solo indicador `bp`. Se agrega con **valor 0** (sin cambio de
comportamiento). Pasarla a 1 requiere volver a correr `evaluate.py` y actualizar las cifras del pitch. Lo decide el equipo con los números (7.2).

---

## 5. Contrato de API

`GET /indicators`
```json
{
  "hr_rest": {"label": "FC en reposo", "unit": "lpm", "input_range": [20, 250], "body_part": "chest",
              "in_semaforo": true,
              "absolute": {"red_gt": 100, "red_lt": null, "yellow_lt": 50, "red_gt_inflight": null}},
  "temp":    {"label": "Temperatura", "unit": "°C", "input_range": [30, 45], "body_part": "core", "in_semaforo": true,
              "absolute": {"red_gt": 38.0, "red_lt": null, "yellow_lt": null, "red_gt_inflight": 38.5,
                           "inflight_consecutive_days": 2}},
  "glucose": {"label": "Glucosa en ayunas", "unit": "mg/dL", "input_range": [20, 600], "body_part": "abdomen",
              "in_semaforo": false,
              "absolute": {"red_gt": 126, "red_lt": 54, "yellow_gt": 100, "yellow_lt": 70}},
  "...": {},
  "_meta": {"absolute_only_first_days": 14, "min_window_points": 14, "baseline_window_days": 28}
}
```
Los límites se leen de `CFG` (`semaforo_config.json`). Mapeo: `red_gt` ← `absolute_red.<k>_gt`, `red_lt` ←
`absolute_red.<k>_lt`, `yellow_lt` ← `absolute_yellow.<k>_lt`, `fitness`: `red_lt` ← `absolute_red.fitness_lt_pct`.

`GET /astronauts` → `[{"astronaut_id": "SIM-001", "launch_date": "2026-05-19", "source": "synthetic", "current_mission_day": 180}]`

`POST /records` (modelo `HealthRecordCreate`; todos los indicadores son opcionales, al menos uno es obligatorio, `extra="forbid"`)
```json
{"astronaut_id": "SIM-001", "timestamp": "2026-11-14T13:30:00Z", "source": "manual",
 "hr_rest": 62, "bp_sys": 112, "bp_dia": 70, "spo2": 97, "temp": 36.8,
 "glucose": null, "sleep": 6.5, "mood": 4, "exercise": 95, "fitness": null}
```
`timestamp` es opcional (por defecto, ahora en UTC). `source ∈ {"manual","sensor"}`; `"synthetic"` solo lo usa el seed.
Respuesta `201`: `{"record": <HealthRecordRead>, "status": <StatusResponse>}`.

`GET /records?astronaut_id=SIM-001` → `[HealthRecordRead]`, donde `HealthRecordRead` son los campos de entrada más `id`,
`mission_day` y `timestamp` ISO con `Z`.

`GET /status?astronaut_id=SIM-001` → `StatusResponse` (reemplaza a `GET /records/latest`, que se elimina)
```json
{
  "astronaut_id": "SIM-001", "mission_day": 180, "phase": "inflight",
  "evaluation_mode": "linea_base",
  "data_origin": "synthetic",
  "overall": {"status": "critical",
              "reasons": [{"code": "dos_amarillos", "text": "Dos indicadores en amarillo a la vez: bp_sys, sleep",
                           "indicators": ["bp_sys", "sleep"]}]},
  "indicators": {
    "bp_sys": {"value": 95, "value_day": 180, "carried": false, "status": "attention",
               "reason": {"code": "banda_personal", "text": "Fuera de tu banda personal 3 días seguidos (banda 101–124 mmHg)", "days_out": 3},
               "baseline": {"ready": true, "mean": 112.4, "lo": 101.0, "hi": 124.0},
               "recommendation": "Hidrátate y evita cambios posturales bruscos."},
    "glucose": {"value": null, "value_day": null, "carried": false, "status": null, "reason": null,
                "baseline": null, "recommendation": null}
  }
}
```
`evaluation_mode ∈ {"prevuelo", "adaptacion_inicial", "linea_base"}`. `status: null` = sin datos.

`GET /series?astronaut_id=SIM-001&indicator=bp_sys` (para las gráficas con banda)
→ `[{"mission_day": 1, "value": 110, "status": "normal", "base": 112.1, "lo": 100.9, "hi": 123.3}, ...]`

---

## 6. Plan de implementación (para el agente programador)

**Paso 0.** Esperar a que estén integrados los arreglos en curso (`HealthRecordCreate`, UTC con zona, NaN en
`IndicatorCard` y `lifespan`) y trabajar encima de ellos. Borrar `backend/health_records.db` si existe: el esquema
cambia y solo había datos de prueba.

1. **`backend/requirements.txt`**: agregar `numpy` y `pandas` con las versiones que ya tiene el venv (`numpy==2.5.4`, `pandas==3.1.1`).
2. **`backend/thresholds.py`**: borrar `Status.NORMAL/ATTENTION` como rangos, `THRESHOLDS[*]["normal"/"attention"]` y
   `evaluate()`. Dejar el enum `Status` y crear `INDICATORS` con los 10 nombres canónicos (`label`, `unit`,
   `input_range`, `body_part`, `in_semaforo`) según la tabla 2. `body_part`: chest = hr_rest, bp_sys, bp_dia, spo2;
   head = mood, sleep; abdomen = glucose; core = temp; legs = exercise, fitness. `RECOMMENDATIONS` se renombra a
   las claves canónicas (attention = amarillo, critical = rojo) y se agrega:
   - `bp_dia`: amarillo «Hidrátate y repite la medición en reposo.» / rojo «Reporta a flight surgeon de inmediato.»
   - `exercise`: amarillo «Retoma tu plan de ejercicio: es la contramedida contra la pérdida muscular y ósea.»
   - `fitness`: rojo «Aptitud bajo 80 % de la previa: revisa el plan de ejercicio con el equipo médico.»
   `get_recommendation(k, status)` se mantiene.
3. **`backend/models.py`**: tabla `Astronaut` (1.4). `HealthRecord`: renombrar campos a los canónicos, agregar `bp_dia`,
   `exercise`, `fitness`, `mission_day: int` y `source: str = "manual"`. `HealthRecordCreate`: mismos campos
   opcionales con `Field(ge=, le=)` según los rangos de 2, `timestamp: datetime | None`,
   `source: Literal["manual","sensor"] = "manual"` y un validador «al menos un indicador». `HealthRecordRead`.
   Función `mission_day_for(ts, launch_date)` (fórmula de 1.4).
4. **`backend/semaforo_bridge.py`** (nuevo): `sys.path` → `Path(__file__).resolve().parents[1] / "simulador" / "sim"`;
   `import semaforo as sf`; `CFG = sf.Config()`; `COLS = {**sf.IND, "exercise": "exercise_min", "fitness": "fitness_pct_preflight"}`.
   Funciones `indicators_meta()` (para `/indicators`, mapeo de 5), `absolute_status(k, x, mission_day)`
   (usa `sf.ABS_RED`, `sf.ABS_YELLOW_LOW` y `CFG`; temperatura con `temp_gt` si día ≤ 14 o < 0 y `temp_gt_inflight`
   en otro caso; FC<50 solo si día > 0; glucosa con las reglas de 1.2), `glucose_status(x)`, `build_daily(records)`
   (pasos 2–4 de 1.5), `compute_status(session, astronaut_id)` (1.5 completo y motivos de 1.6) y
   `compute_series(session, astronaut_id, k)`. Mapeo de estado: `{0: "normal", 1: "attention", 2: "critical"}`.
   No leer ninguna columna `truth_*`.
5. **`backend/main.py`**: `/indicators` → `indicators_meta()`. `POST /records`: crear `Astronaut` si falta, calcular
   `mission_day`, guardar y responder `{"record", "status"}`. `GET /records` con `mission_day`. Nuevos
   `GET /astronauts`, `GET /status` y `GET /series`. Eliminar `GET /records/latest` y `assess_record`.
6. **`backend/test_semaforo_bridge.py`** (nuevo, pytest; agregar `pytest` a requirements):
   (a) con el seed cargado, `compute_status` de SIM-001 en el día 180 coincide en `status_*` con
   `simulador/out/mission_synthetic_semaforo.csv` (día 180, todos los indicadores menos glucosa). Si no coincide,
   comprobar primero si ese CSV se generó con la config actual (`params_used.json`) antes de tocar el código;
   (b) astronauta nuevo con SpO2 88 → `critical`, `limite_clinico`; con sueño 4 h → `normal`, `sin_linea_base`;
   (c) prevuelo con temperatura 38,3 → `critical`;
   (d) `grep` sobre `backend/`: ningún `truth_` ni `latent_truth`.
7. **`backend/seed_demo.py`** (nuevo): según 1.7. Uso: `cd backend && python seed_demo.py`.
8. **`frontend/src/data/thresholds.ts` → `indicators.ts`**: `Status`, `STATUS_COLOR`, `INDICATORS` (espejo de
   `/indicators`, con los valores actuales de la config) y `evaluateAbsolute(key, value, missionDay)`. Borrar `evaluate()`.
9. **`frontend/src/components/BodyMap.tsx`**: claves canónicas y nueva parte `{id: "legs", label: "Músculo / Ejercicio",
   indicators: ["exercise", "fitness"], cx: 100, cy: 240, r: 14}`. Parte «Pecho» con `bp_dia`.
10. **`frontend/src/components/IndicatorCard.tsx`**: claves canónicas; vista previa con `evaluateAbsolute` y el texto
    «vista previa: solo límite clínico»; nueva prop opcional `serverStatus` (objeto de `indicators[k]` de `/status`)
    que, si existe, define el color y muestra `reason.text` y la banda `lo–hi`.
11. **`frontend/src/App.tsx`**: al montar, pedir `/indicators` (sobrescribe `INDICATORS`) y `/astronauts`; selector de
    astronauta (por defecto, el primero `SIM-*` si existe; si no, `"default"`); `GET /status` al cambiar de astronauta
    y después de cada POST; el mapa corporal usa `status.indicators[k].status`; banner con `evaluation_mode` y
    `overall.reasons`; etiqueta «DATOS SINTÉTICOS» si `data_origin == "synthetic"`; recomendaciones desde
    `status.indicators[*].recommendation`; leyenda «Verde / Amarillo / Rojo». Modo sin backend: `evaluateAbsolute` y aviso de 1.8.
12. **`frontend/src/components/HistoryChart.tsx`**: usar `GET /series`; eje X = `mission_day`; dibujar `lo`/`hi` como
    líneas punteadas (o `Area`) para la banda personal.
13. **`docs/health_indicators.md`**: nombres canónicos y reemplazo de la tabla «Rangos» por los límites absolutos de la
    config, con la explicación de la línea base (sin «crítico <90» en la sistólica). **`CLAUDE.md`**: actualizar
    «Indicadores» y «DOS lógicas» (resuelto, enlazar este documento) y quitar de pendientes la sistólica 85–90.
14. **(Punto 4, aparte)** `simulador/sim/semaforo.py` y `semaforo_config.json`: agregar
    `general.bp_counts_once = [0, "supuesto", "..."]`. En `run_semaforo`, si vale 1, calcular `n_yellow` con
    `bp_sys` y `bp_dia` fusionados con `max`. Correr `cd simulador && python sim/evaluate.py` con 0 y con 1 y dejar las
    dos cifras al equipo. **No** cambiar el valor por defecto.

---

## 7. Abierto para el equipo
1. `absolute_yellow.bp_sys_lt`: ¿activar 90 mmHg (amarillo en vuelo)? Antes hay que verificar ESC 2018. (Andres)
2. `bp_counts_once` en 1: recomendado; depende de la comparación del paso 14 y obliga a actualizar cifras del pitch.
3. Sueño, ánimo y temperatura baja no tienen límite absoluto: sin línea base nunca alertan. ¿Agregar amarillo fijo
   (por ejemplo, sueño < 5 h, ánimo = 1)? Necesita fuente o etiqueta «supuesto». (Andres, Jarib)
4. FC > 100 en reposo ahora es **rojo** (antes, en la app, 100–120 era atención). Es lo que dice la config (AHA);
   confirmar que el equipo lo acepta.
5. Glucosa como ayunas semanal (ADA) en lugar de 70–140: confirmar con quien la ingresa (Jarib).
6. Escala de ánimo 1–5 frente a GHQ-12 (Jarib). Lugar del sensor de temperatura (Hugo): cambia 38,0 / 38,5 °C.
7. Agregación diaria con «última lectura del día»: el simulador modela la lectura de las 08:30. Si el sensor envía
   muchas lecturas, quizá convenga «primera lectura en reposo de la mañana». Decidir cuando se conecte el ESP32 (Hugo, James).
8. `launch_date` del astronauta manual: hoy se fija con el primer registro. ¿Formulario para fijarla?
