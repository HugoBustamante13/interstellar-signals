# Indicadores de salud — fundamento y rangos de referencia

## Fuentes consultadas
- NASA Human Research Program — Hazards: https://www.nasa.gov/hrp/hazards/
- NASA Human Research Program — Risks: https://www.nasa.gov/hrp/risks/
- CSA — Monitoring radiation and astronaut health: https://www.asc-csa.gc.ca/eng/news/articles/2026/2026-02-26-monitoring-radiation-astronaut-health.asp
- CSA — Why we conduct science experiments in space: https://www.asc-csa.gc.ca/eng/iss/science/why-do-we-conduct-science-experiments-in-space.asp

## Los 5 hazards (NASA HRP) y su relación con nuestros indicadores

| Hazard | Qué dice NASA | Indicador(es) que lo reflejan en nuestro MVP |
|---|---|---|
| Radiación espacial | Es uno de los riesgos más peligrosos; puede causar daño biológico severo (neutrones ~30% de la radiación en la ISS, según CSA). No hay biomarcador simple medible en cabina. | No cubierto en MVP — requeriría sensores dedicados (ej. CANS/detectores de burbujas). Mencionar como limitación. |
| Aislamiento y confinamiento | Grupos pequeños en espacio reducido por meses/años pueden mostrar cambios de comportamiento. | `mood`, `sleep` |
| Distancia de la Tierra | Dificulta recibir ayuda médica desde la Tierra → la tripulación debe ser más autosuficiente. | Justifica que el software dé recomendaciones accionables sin depender de conexión a Tierra. |
| Campos de gravedad alterados | El cuerpo debe adaptarse (músculos, huesos, oído interno, órganos) a distintos niveles de gravedad. | `hr_rest`, `bp_sys`, `bp_dia` (adaptación cardiovascular); `exercise` y `fitness` vigilan lo que protege hueso y músculo, no la densidad ósea (ver "Riesgos pendientes"). |
| Ambientes cerrados hostiles | La nave debe controlar temperatura, presión, luz, ruido y microbios; se monitorea la respuesta inmune. | `temp`, `spo2` |

## Riesgos específicos de NASA HRP mapeados a indicadores

| Riesgo (NASA HRP) | Sistema afectado | Indicador en nuestro MVP |
|---|---|---|
| Adaptaciones cardiovasculares | Cardiovascular | `hr_rest`, `bp_sys`, `bp_dia` |
| Hipoxia | Oxigenación tisular | `spo2` |
| Nutrición inadecuada | Metabólico | `glucose` |
| Sueño inadecuado / horarios irregulares | Sistema nervioso / ritmo circadiano | `sleep` |
| Cambios de comportamiento y trastornos psiquiátricos | Salud mental | `mood` |
| Interacciones huésped-microorganismo | Inmune | `temp` (proxy indirecto de infección/respuesta inmune) |

## Riesgos de NASA HRP identificados pero NO cubiertos en el MVP
(oportunidades para siguientes iteraciones)

- **SANS** (Spaceflight-Associated Neuro-ocular Syndrome): cambios estructurales en ojos/cerebro — requeriría input de imagen (ej. fondo de ojo) o cuestionario visual.
- **Pérdida de densidad ósea y fitness musculoesquelético**: requeriría registrar minutos de ejercicio/countermeasures y, idealmente, densitometría periódica.
- **Mal de descompresión**: relevante sobre todo en EVA/spacewalks; no aplica a monitoreo diario rutinario.
- **Radiación acumulada**: necesitaría un valor de dosis (mSv) si se simula un dosímetro — se puede agregar como indicador futuro con rango basado en límites de carrera de NASA.
- **Función vestibular/sensorimotora**: mareo, coordinación — se podría agregar como cuestionario rápido (escala 1-5 como `mood`).

## Cómo se decide el color (desde el 14-nov-2026)

Ver `docs/decision_integracion_semaforo.md`. Ya no hay rangos fijos normal / atención / crítico: el backend importa
el semáforo del simulador (`simulador/sim/semaforo.py`) y cada astronauta se compara con **su propia línea base**.

- **Banda personal:** media ± 2,5 DE de las lecturas de los últimos 28 días (mínimo 14 lecturas).
- **Amarillo:** 3 lecturas seguidas fuera de la banda; FC en reposo < 50 lpm (en vuelo); SpO2 3 puntos o más bajo la
  línea base; menos de 3 sesiones de ejercicio de 90 min o más en 7 días; glucosa en ayunas 100–125 o 54–69 mg/dL.
- **Rojo:** un límite clínico absoluto (tabla de abajo), un salto de 4 DE confirmado al día siguiente, aptitud física
  bajo el 80 % de la previa, o dos indicadores en amarillo a la vez.
- **Sin línea base** (astronauta nuevo, prevuelo o días 1–14 de vuelo): solo cuentan los límites absolutos.

### Límites clínicos absolutos (fuente de verdad: `simulador/sim/semaforo_config.json`)

> NASA no publica criterios numéricos de alarma para uso en cabina. Son referencias clínicas terrestres; las bandas,
> los días seguidos y los saltos son supuestos del equipo. La API los sirve en `GET /indicators`.

| Indicador | Clave | Rojo | Amarillo | Fuente |
|---|---|---|---|---|
| FC en reposo (lpm) | `hr_rest` | > 100 | < 50 (solo en vuelo) | AHA; ACC/AHA/HRS 2018 |
| Presión sistólica (mmHg) | `bp_sys` | > 180 | — (sin límite inferior: en vuelo la presión baja de forma normal) | AHA 2025 |
| Presión diastólica (mmHg) | `bp_dia` | > 120 | — | AHA 2025 |
| SpO2 (%) | `spo2` | < 90 | 3 puntos bajo tu línea base | Open Critical Care; BTS 2017 |
| Temperatura (°C) | `temp` | > 38,0 en prevuelo y días 1–14; > 38,5 en dos lecturas seguidas después | — | MSD Manual; 38,5 °C es supuesto del equipo |
| Glucosa en ayunas (mg/dL) | `glucose` | < 54 o ≥ 126 | 54–69 o 100–125 | ADA 2026 (fuera de la regla «dos amarillos») |
| Horas de sueño (h) | `sleep` | — | solo banda personal | — |
| Estado de ánimo (1–5) | `mood` | — | solo banda personal | — |
| Ejercicio (min/día) | `exercise` | — | < 3 sesiones de ≥ 90 min en 7 días | supuesto del equipo |
| Aptitud física (% previa) | `fitness` | < 80 | — | NASA-STD-3001 Vol. 1 Rev. C |

Una sistólica de 85–90 mmHg **no** es «crítico» por regla fija: se juzga contra la banda personal (decisión, sección 3).

## Nota para la presentación del proyecto
Dado que las fuentes oficiales no publican umbrales numéricos exactos para uso en
cabina, es honesto (y buena práctica para el jurado) aclarar en el pitch que los
rangos son una aproximación clínica general, y que el valor del proyecto está en
el **sistema** (recolección, visualización, alerta, recomendación) más que en los
números exactos — los cuales en un producto real vendrían de flight surgeons.
