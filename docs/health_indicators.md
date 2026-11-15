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
| Aislamiento y confinamiento | Grupos pequeños en espacio reducido por meses/años pueden mostrar cambios de comportamiento. | `mood`, `sleep_hours` |
| Distancia de la Tierra | Dificulta recibir ayuda médica desde la Tierra → la tripulación debe ser más autosuficiente. | Justifica que el software dé recomendaciones accionables sin depender de conexión a Tierra. |
| Campos de gravedad alterados | El cuerpo debe adaptarse (músculos, huesos, oído interno, órganos) a distintos niveles de gravedad. | `heart_rate`, `systolic_bp` (adaptación cardiovascular); pérdida de densidad ósea no cubierta aún (ver "Riesgos pendientes"). |
| Ambientes cerrados hostiles | La nave debe controlar temperatura, presión, luz, ruido y microbios; se monitorea la respuesta inmune. | `body_temp`, `spo2` |

## Riesgos específicos de NASA HRP mapeados a indicadores

| Riesgo (NASA HRP) | Sistema afectado | Indicador en nuestro MVP |
|---|---|---|
| Adaptaciones cardiovasculares | Cardiovascular | `heart_rate`, `systolic_bp` |
| Hipoxia | Oxigenación tisular | `spo2` |
| Nutrición inadecuada | Metabólico | `glucose` |
| Sueño inadecuado / horarios irregulares | Sistema nervioso / ritmo circadiano | `sleep_hours` |
| Cambios de comportamiento y trastornos psiquiátricos | Salud mental | `mood` |
| Interacciones huésped-microorganismo | Inmune | `body_temp` (proxy indirecto de infección/respuesta inmune) |

## Riesgos de NASA HRP identificados pero NO cubiertos en el MVP
(oportunidades para siguientes iteraciones)

- **SANS** (Spaceflight-Associated Neuro-ocular Syndrome): cambios estructurales en ojos/cerebro — requeriría input de imagen (ej. fondo de ojo) o cuestionario visual.
- **Pérdida de densidad ósea y fitness musculoesquelético**: requeriría registrar minutos de ejercicio/countermeasures y, idealmente, densitometría periódica.
- **Mal de descompresión**: relevante sobre todo en EVA/spacewalks; no aplica a monitoreo diario rutinario.
- **Radiación acumulada**: necesitaría un valor de dosis (mSv) si se simula un dosímetro — se puede agregar como indicador futuro con rango basado en límites de carrera de NASA.
- **Función vestibular/sensorimotora**: mareo, coordinación — se podría agregar como cuestionario rápido (escala 1-5 como `mood`).

## Rangos de referencia usados en el MVP (clínicos generales, no específicos de NASA)

> Ninguna de las dos fuentes de NASA/CSA consultadas publica rangos numéricos exactos
> de uso abierto para bpm, mmHg, SpO2, glucosa, etc. en astronautas. Los rangos abajo
> son clínicos generales (población terrestre sana) y deben tratarse como una
> aproximación razonable para el demo, no como protocolo médico real.

| Indicador | Normal | Atención | Crítico |
|---|---|---|---|
| Frecuencia cardíaca (bpm) | 60–100 | 100–120 o 50–60 | >120 o <50 |
| Presión sistólica (mmHg) | 90–120 | 120–140 | >140 o <90 |
| SpO2 (%) | 95–100 | 90–94 | <90 |
| Temperatura corporal (°C) | 36.1–37.2 | 37.3–38.0 o 35.5–36.0 | >38.0 o <35.5 |
| Glucosa (mg/dL) | 70–140 | 140–180 o 60–70 | >180 o <60 |
| Horas de sueño (h) | 7–9 | 5–7 | <5 |
| Estado de ánimo (1-5) | 4–5 | 2–3 | 1 |

## Nota para la presentación del proyecto
Dado que las fuentes oficiales no publican umbrales numéricos exactos para uso en
cabina, es honesto (y buena práctica para el jurado) aclarar en el pitch que los
rangos son una aproximación clínica general, y que el valor del proyecto está en
el **sistema** (recolección, visualización, alerta, recomendación) más que en los
números exactos — los cuales en un producto real vendrían de flight surgeons.
