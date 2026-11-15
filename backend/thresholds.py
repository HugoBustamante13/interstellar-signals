"""
Fuente de verdad de los rangos de los indicadores de salud.
Ver docs/health_indicators.md para la justificación clínica/espacial.

Mantener sincronizado con frontend/src/data/thresholds.ts
"""
from enum import Enum


class Status(str, Enum):
    NORMAL = "normal"
    ATTENTION = "attention"
    CRITICAL = "critical"


# Cada regla: (min_normal, max_normal, min_attention, max_attention)
# Fuera de attention => critical
THRESHOLDS = {
    "heart_rate": {"unit": "bpm", "normal": (60, 100), "attention": (50, 120)},
    "systolic_bp": {"unit": "mmHg", "normal": (90, 120), "attention": (85, 140)},
    "spo2": {"unit": "%", "normal": (95, 100), "attention": (90, 100)},
    "body_temp": {"unit": "°C", "normal": (36.1, 37.2), "attention": (35.5, 38.0)},
    "glucose": {"unit": "mg/dL", "normal": (70, 140), "attention": (60, 180)},
    "sleep_hours": {"unit": "h", "normal": (7, 9), "attention": (5, 12)},
    "mood": {"unit": "1-5", "normal": (4, 5), "attention": (2, 5)},
}

RECOMMENDATIONS = {
    "heart_rate": {
        Status.ATTENTION: "Descansa y vuelve a medir en 30 min. Evita ejercicio intenso.",
        Status.CRITICAL: "Reporta a flight surgeon. Mantente en reposo y monitorea síntomas.",
    },
    "systolic_bp": {
        Status.ATTENTION: "Hidrátate y evita cambios posturales bruscos.",
        Status.CRITICAL: "Reporta a flight surgeon de inmediato.",
    },
    "spo2": {
        Status.ATTENTION: "Verifica calidad de aire de la cabina. Repite la medición.",
        Status.CRITICAL: "Alerta inmediata — posible problema de oxigenación o del ambiente.",
    },
    "body_temp": {
        Status.ATTENTION: "Monitorea cada pocas horas. Hidrátate.",
        Status.CRITICAL: "Posible infección o respuesta inmune — contacta a flight surgeon.",
    },
    "glucose": {
        Status.ATTENTION: "Ajusta próxima comida/snack. Vuelve a medir en 1-2 h.",
        Status.CRITICAL: "Atiende de inmediato según protocolo médico personal.",
    },
    "sleep_hours": {
        Status.ATTENTION: "Prioriza higiene de sueño esta noche. Reduce cafeína.",
        Status.CRITICAL: "Riesgo de deterioro cognitivo/ánimo — ajusta rutina y reporta si persiste.",
    },
    "mood": {
        Status.ATTENTION: "Usa recursos de apoyo conductual. Habla con la tripulación.",
        Status.CRITICAL: "Contacta soporte de salud conductual de la misión.",
    },
}


def evaluate(indicator: str, value: float) -> Status:
    rule = THRESHOLDS[indicator]
    n_lo, n_hi = rule["normal"]
    a_lo, a_hi = rule["attention"]
    if n_lo <= value <= n_hi:
        return Status.NORMAL
    if a_lo <= value <= a_hi:
        return Status.ATTENTION
    return Status.CRITICAL


def get_recommendation(indicator: str, status: Status) -> str | None:
    if status == Status.NORMAL:
        return None
    return RECOMMENDATIONS.get(indicator, {}).get(status)
