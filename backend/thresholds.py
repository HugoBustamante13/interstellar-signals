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
        Status.ATTENTION: "Rest and measure again in 30 min. Avoid intense exercise.",
        Status.CRITICAL: "Report to the crew medical officer. Stay at rest and monitor your symptoms.",
    },
    "systolic_bp": {
        Status.ATTENTION: "Stay hydrated and avoid sudden changes of posture.",
        Status.CRITICAL: "Report to the crew medical officer right away.",
    },
    "spo2": {
        Status.ATTENTION: "Check the cabin air quality. Repeat the measurement.",
        Status.CRITICAL: "Immediate alert: possible oxygenation or environment problem.",
    },
    "body_temp": {
        Status.ATTENTION: "Monitor every few hours. Stay hydrated.",
        Status.CRITICAL: "Possible infection or immune response: contact the crew medical officer.",
    },
    "glucose": {
        Status.ATTENTION: "Adjust your next meal or snack. Measure again in 1-2 h.",
        Status.CRITICAL: "Act immediately following your personal medical protocol.",
    },
    "sleep_hours": {
        Status.ATTENTION: "Prioritize sleep hygiene tonight. Cut back on caffeine.",
        Status.CRITICAL: "Risk of cognitive and mood decline: adjust your routine and report if it persists.",
    },
    "mood": {
        Status.ATTENTION: "Use behavioral support resources. Talk with your crew.",
        Status.CRITICAL: "Contact the mission's behavioral health support.",
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
