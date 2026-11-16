"""
Metadatos de los indicadores: etiqueta, unidad, rango de entrada, parte del cuerpo y recomendaciones.

Desde la decisión del 14-nov-2026 (docs/decision_integracion_semaforo.md) este archivo NO decide colores.
El color lo da el semáforo del simulador (semaforo_bridge.py), con la línea base personal y los límites
absolutos de simulador/sim/semaforo_config.json. Aquí no se copian límites: /indicators los lee de la config.

Nombres canónicos = claves del simulador (hr_rest, bp_sys, ...). El frontend tiene el espejo en
frontend/src/data/indicators.ts y lo sobrescribe al arrancar con GET /indicators.
"""
from enum import Enum


class Status(str, Enum):
    NORMAL = "normal"  # verde
    ATTENTION = "attention"  # amarillo
    CRITICAL = "critical"  # rojo


STATUS_BY_CODE = {0: Status.NORMAL, 1: Status.ATTENTION, 2: Status.CRITICAL}

# input_range: valores plausibles para validar la entrada (422 si se sale). NO son umbrales de alerta.
INDICATORS = {
    "hr_rest": {"label": "FC en reposo", "unit": "lpm", "input_range": (20, 250), "body_part": "chest", "in_semaforo": True},
    "bp_sys": {"label": "Presión sistólica", "unit": "mmHg", "input_range": (50, 260), "body_part": "chest", "in_semaforo": True},
    "bp_dia": {"label": "Presión diastólica", "unit": "mmHg", "input_range": (30, 160), "body_part": "chest", "in_semaforo": True},
    "spo2": {"label": "SpO2", "unit": "%", "input_range": (50, 100), "body_part": "chest", "in_semaforo": True},
    "temp": {"label": "Temperatura", "unit": "°C", "input_range": (30, 45), "body_part": "core", "in_semaforo": True},
    "glucose": {"label": "Glucosa en ayunas", "unit": "mg/dL", "input_range": (20, 600), "body_part": "abdomen", "in_semaforo": False},
    "sleep": {"label": "Horas de sueño", "unit": "h", "input_range": (0, 24), "body_part": "head", "in_semaforo": True},
    "mood": {"label": "Estado de ánimo", "unit": "1-5", "input_range": (1, 5), "body_part": "head", "in_semaforo": True},
    "exercise": {"label": "Ejercicio", "unit": "min", "input_range": (0, 600), "body_part": "legs", "in_semaforo": True},
    "fitness": {"label": "Aptitud física", "unit": "% previa", "input_range": (0, 150), "body_part": "legs", "in_semaforo": True},
}

# attention = amarillo, critical = rojo
RECOMMENDATIONS = {
    "hr_rest": {
        Status.ATTENTION: "Descansa y vuelve a medir en 30 min. Evita ejercicio intenso.",
        Status.CRITICAL: "Reporta a flight surgeon. Mantente en reposo y monitorea síntomas.",
    },
    "bp_sys": {
        Status.ATTENTION: "Hidrátate y evita cambios posturales bruscos.",
        Status.CRITICAL: "Reporta a flight surgeon de inmediato.",
    },
    "bp_dia": {
        Status.ATTENTION: "Hidrátate y repite la medición en reposo.",
        Status.CRITICAL: "Reporta a flight surgeon de inmediato.",
    },
    "spo2": {
        Status.ATTENTION: "Verifica calidad de aire de la cabina. Repite la medición.",
        Status.CRITICAL: "Alerta inmediata — posible problema de oxigenación o del ambiente.",
    },
    "temp": {
        Status.ATTENTION: "Monitorea cada pocas horas. Hidrátate.",
        Status.CRITICAL: "Posible infección o respuesta inmune — contacta a flight surgeon.",
    },
    "glucose": {
        Status.ATTENTION: "Ajusta próxima comida/snack. Vuelve a medir en 1-2 h.",
        Status.CRITICAL: "Atiende de inmediato según protocolo médico personal.",
    },
    "sleep": {
        Status.ATTENTION: "Prioriza higiene de sueño esta noche. Reduce cafeína.",
        Status.CRITICAL: "Riesgo de deterioro cognitivo/ánimo — ajusta rutina y reporta si persiste.",
    },
    "mood": {
        Status.ATTENTION: "Usa recursos de apoyo conductual. Habla con la tripulación.",
        Status.CRITICAL: "Contacta soporte de salud conductual de la misión.",
    },
    "exercise": {
        Status.ATTENTION: "Retoma tu plan de ejercicio: es la contramedida contra la pérdida muscular y ósea.",
    },
    "fitness": {
        Status.CRITICAL: "Aptitud bajo 80 % de la previa: revisa el plan de ejercicio con el equipo médico.",
    },
}


def get_recommendation(indicator: str, status: Status | None) -> str | None:
    if status is None or status == Status.NORMAL:
        return None
    return RECOMMENDATIONS.get(indicator, {}).get(status)
