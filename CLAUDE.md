# Proyecto: NASA Space Apps Challenge 2026 — Astronaut Health Monitor

## Reto
«Create Health Monitoring Software for Astronauts on Space Missions» — NASA Space
Apps Challenge 2026, sede Barranquilla.

## Objetivo
**Principio rector: el software es una ayuda para que cada astronauta se autoevalúe.**
Toda pantalla, texto o función debe servir a que el propio astronauta registre sus
datos, entienda su estado frente a su línea base y decida los primeros pasos. No es una
consola para que otros lo vigilen; escalar al oficial médico es parte de la guía.

Herramienta visual para que astronautas en misiones largas registren indicadores de
salud, vean su estado con un semáforo (verde/amarillo/rojo) sobre una figura humana,
revisen tendencias y reciban una guía de acción cuando algo se sale de rango.
Justificación: los 5 peligros de NASA HRP (radiación, aislamiento/confinamiento,
distancia de la Tierra, gravedad alterada, ambiente cerrado hostil). La distancia
(hasta 20 min de retraso) obliga a que la tripulación decida sin esperar a tierra.

## Equipo y roles
| Persona | Rol |
|---|---|
| Hugo | Líder y sensores ESP32 (FC, SpO2, temperatura vienen del sensor) |
| Andres | Backend, motor de reglas y alertas |
| James | Base de datos SQL y recepción del sensor |
| Jarib | Entrada manual de datos y gamificación |
| Jose | Figura humana y visualización del semáforo |
| Isa | Apuntes de investigación iniciales (base de la guía de peligros) |

## Estructura del repo
```
backend/      FastAPI + SQLite (sqlmodel). /indicators, /astronauts, /records, /status, /series y /live (demo)
              semaforo_bridge.py importa simulador/sim/semaforo.py; seed_demo.py carga la misión sintética
frontend/     React + TS + Vite + Tailwind + Recharts. Mapa corporal, tarjetas, gráfica con banda personal
simulador/    Parte de datos (v0.3): simulador sintético + semáforo con línea base personal
  sim/          simulator.py, semaforo.py, evaluate.py y sus JSON de parámetros/umbrales
  out/          datos sintéticos generados (4 astronautas, 30 días pre + 180 en vuelo)
  out/evaluation/  métricas del semáforo sobre 200 misiones simuladas
  schema/       contrato de datos (JSON Schema) + validate.py
  fichas/       FICHAS_indicadores.md: una ficha por indicador con fuentes
  charts/       9 gráficas PNG de tendencia (DATOS SINTÉTICOS)
  RESULTADOS_investigacion.md   hallazgos con fuente y etiqueta
docs/
  health_indicators.md   mapeo peligros HRP → indicadores, rangos del MVP
  equipo/                documentos Word del equipo (ver abajo)
data/         vacío (reservado)
.claude/agents/   subagentes con modelo asignado
```

Documentos en `docs/equipo/`:
- `Guia_reto_y_5_peligros_HRP.docx`: el reto, los 5 peligros y qué indicador justifica cada uno.
- `Respaldo_indicadores_software.docx`: evidencia y fuentes detrás de cada rango y umbral.
- `Entrega_parte_de_datos.docx` (v0.3): qué contiene `simulador/`, cómo usarlo, qué sirve a cada integrante, pendientes.
- `contexto_carpetas.docx`: versión anterior casi idéntica de la entrega.

Los scripts de `simulador/` resuelven rutas relativas a `simulador/`: correrlos desde
ahí (`cd simulador && python sim/simulator.py --out out`). Dependencias:
`pip install numpy pandas scipy matplotlib jsonschema`.

## Indicadores
Simulador / semáforo (8): FC en reposo (`hr_rest`), presión sistólica y diastólica
(`bp_sys`, `bp_dia`), SpO2, temperatura, glucosa (semanal), horas de sueño, ánimo
(1–5), ejercicio/aptitud física.

App (backend/frontend, 10, desde el 15-nov-2026): los mismos nombres del simulador —
`hr_rest`, `bp_sys`, `bp_dia`, `spo2`, `temp`, `glucose`, `sleep`, `mood`, `exercise`, `fitness`.

## Una sola lógica de semáforo (resuelto el 15-nov-2026)
Antes había dos: umbrales fijos en la app (`thresholds.py`/`thresholds.ts`) y la línea base del simulador.
Ahora el backend usa solo la del simulador (`backend/semaforo_bridge.py` importa `semaforo.py` tal cual);
`thresholds.py` quedó como metadatos y recomendaciones, y el frontend tiene en `frontend/src/data/indicators.ts`
un espejo de los límites absolutos (lo sobrescribe con `GET /indicators`). `backend/test_semaforo_bridge.py`
comprueba que los colores de la app coinciden día a día con `simulador/out/mission_synthetic_semaforo.csv`.
La lógica del simulador, para el pitch:
2. **Simulador** (`simulador/sim/semaforo.py` + `semaforo_config.json`): línea base
   personal (media ± 2,5 DE de los 28 días previos, mín. 14 lecturas); amarillo = 3
   lecturas seguidas fuera de banda; rojo = límite absoluto clínico, salto de 4 DE
   confirmado, o dos indicadores en amarillo. Primeros 14 días de vuelo: solo límites
   absolutos. Evaluado: 1,82 falsos episodios/misión, 62 % de eventos detectados
   (contra anomalías inventadas).

La lógica 2 es el argumento central del equipo (en vuelo el cuerpo cambia, p. ej.
presión −8/−9 mmHg según Norsk 2015, así que un umbral fijo de la Tierra da falsas
alarmas). **Decidido (14-nov-2026)** en `docs/decision_integracion_semaforo.md`: el
backend importa `semaforo.py` tal cual (vía `backend/semaforo_bridge.py`) y su lógica
reemplaza a los colores fijos; nombres canónicos = claves del simulador (`hr_rest`,
`bp_sys`, `bp_dia`, `spo2`, `temp`, `glucose`, `sleep`, `mood`, `exercise`). El plan de
implementación (sección 6) quedó ejecutado el 15-nov-2026 en los pasos 1–13; el 14 (`bp_counts_once`) sigue
pendiente. La sección 7 lista lo abierto para el equipo.

## Honestidad en el pitch (obligatorio)
- Todos los datos de demo son sintéticos; el simulador no es un modelo fisiológico validado.
- NASA no publica criterios numéricos de alarma (se revisó NASA-STD-3001 Vol. 1 Rev. C).
  Los límites absolutos son referencias clínicas terrestres; bandas, días seguidos y saltos son supuestos del equipo.
- No decir «validado», «realista» ni «detecta el 62 % de los problemas».
- Las columnas `truth_*` / `latent_truth` son solo para evaluar: nunca usarlas en la lógica del producto ni mostrarlas.

## Pendientes conocidos
- Hugo: dónde mide el sensor de temperatura (cambia límites de 38,0/38,5 °C; central ≈ oral + 0,47 °C).
- Hugo u organización: confirmar si se permite llevar código avanzado al evento.
- Andres: criterios de escalamiento con fuente para reemplazar umbrales supuestos.
- Jarib: confirmar escala de ánimo (1–5 vs GHQ-12).
- Equipo: ¿presión como un solo indicador? Hoy sistólica y diastólica cuentan como dos y «dos amarillos = rojo» puede dispararse solo por presión. El arquitecto recomienda que sí (opción `bp_counts_once`); activarla exige re-correr `evaluate.py` y actualizar cifras del pitch.
- Equipo: aceptar que FC en reposo > 100 pasa a rojo (antes 100–120 era atención) y que sueño, ánimo y temperatura baja no alertan sin línea base (no tienen límite absoluto).
- Verificar fuentes: texto completo de Norsk 2015; Fu 2019, ESC 2018, Hughson 2016, Crawford y Henry 2004.
- Riesgos no cubiertos: radiación acumulada, SANS, densidad ósea, función vestibular.
- Bugs de la revisión del 14-nov-2026 — corregidos ese mismo día:
  - `IndicatorCard`: campo vacío → «sin dato» (antes `NaN` crítico); `App.tsx` no envía indicadores vacíos.
  - Timestamps con zona (`datetime.now(timezone.utc)`); la API serializa con `+00:00`.
  - `POST /records` valida con `HealthRecordCreate` (422 ante valores inválidos o registro vacío); `model_dump()` y `lifespan` en vez de APIs deprecadas.
- `HealthRecordCreate` valida rangos de plausibilidad por indicador (p. ej. spo2 50–100, temp 30–45, mood 1–5) y
  rechaza nombres viejos (`extra="forbid"`): 422.
- La base SQLite cambió de esquema el 15-nov-2026: si el backend dice «esquema viejo», borrar `backend/health_records.db`
  (solo tenía datos de prueba) y correr `python seed_demo.py`.
- Entorno: venv en `backend/venv` (`requirements.txt` ya incluye numpy y pandas; pruebas con `requirements-dev.txt`). Si los subagentes de `.claude/agents/` no aparecen, reiniciar la sesión de Claude Code (el 14-nov no estaban cargados).

## Gestión de modelos (IMPORTANTE)
Subagentes en `.claude/agents/`, cada uno con modelo asignado:
- `investigador` (Haiku) → búsquedas web, NASA HRP/CSA, rangos clínicos, justificación médica.
- `programador` (Sonnet) → endpoints, componentes React, scripts, con especificación clara.
- `arquitecto` (Opus) → decisiones de arquitectura (p. ej. integrar el semáforo del simulador
  al backend), bugs difíciles, revisión final antes de demo.

Regla: investigación → `investigador`. Código con spec clara → `programador`.
Diseño/arquitectura, bugs difíciles o revisión final → `arquitecto`. Trivial → hazlo tú.
No uses `arquitecto` para tareas rutinarias; es el más costoso.

## Convenciones
- Los límites de color viven solo en `simulador/sim/semaforo_config.json`: el backend los lee de ahí
  (`semaforo_bridge.absolute_limits`) y el frontend los recibe con `GET /indicators`. `backend/thresholds.py`
  guarda etiqueta, unidad, rango de entrada y recomendaciones. El espejo local de `frontend/src/data/indicators.ts`
  solo manda sin backend: si cambia la config, actualízalo con la salida de `GET /indicators`.
- Umbrales del semáforo del simulador en `simulador/sim/semaforo_config.json`; cada valor
  lleva su estado (medido/referencia/derivado/supuesto/sin fuente) y su fuente.
- Generar datos nuevos en otra carpeta (`--out otra_carpeta`): `make_charts.py` siempre lee `out/`.
- Commits en español.

## Origen de este repo
Unificado el 14-nov-2026 a partir de `Downloads/organizando/nasa-space-apps` (app y
agentes) y `Downloads/hackaton_sim` (simulador y documentos). Los originales siguen en
Descargas.
