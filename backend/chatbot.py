"""
On-board health assistant (chatbot) for the Astronaut Health Monitor.

HYBRID design:
- OFFLINE rule-based core: always answers, no internet or API key, using the
  knowledge base in this file + the astronaut's real context (latest record,
  traffic light, trend). This is the challenge's argument: the crew decides
  without waiting for Earth (up to ~20 min one-way delay to Mars).
- OPTIONAL LLM layer: if ANTHROPIC_API_KEY + internet are available, Claude
  rephrases the same answer, GROUNDED in the KB facts and the context. On any
  failure it falls back to the rule-based answer. It never breaks.

The assistant speaks ENGLISH (submission pages must be in English).

Honesty (mandatory, see CLAUDE.md and the behavioral research ficha):
- Demo data is synthetic; this is not a validated physiological model nor medical advice.
- Thresholds are general clinical/lab references (mostly non-astronaut populations),
  not NASA alarm criteria. No NASA branding. The use of AI is disclosed in the UI.

Behavioral knowledge (sleep / mood / team) is sourced from the team research ficha:
AASM/SRS 2015, Jones 2022, Flynn-Evans 2016, Akerstedt 2014 (KSS), Topp 2015 (WHO-5),
Kroenke 2003 (PHQ-2), Kanas (Shuttle/Mir), NASA BHP (Passmore 2026).
"""
from __future__ import annotations

import os
import unicodedata
from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from models import HealthRecord, get_session, utcnow
from thresholds import THRESHOLDS, Status, evaluate

router = APIRouter(prefix="/chat", tags=["chatbot"])

# Modelo del LLM. Por defecto Opus 5; el equipo puede bajarlo a un modelo más
# barato con CHATBOT_MODEL=claude-haiku-4-5 para la demo.
LLM_MODEL = os.getenv("CHATBOT_MODEL", "claude-opus-5")

DISCLAIMER = (
    "I'm not medical advice and the demo data is synthetic. Thresholds are general "
    "clinical references (mostly from Earth populations), not NASA alarm criteria."
)

# --------------------------------------------------------------------------- #
# Knowledge base (single source for the assistant's text)
# --------------------------------------------------------------------------- #

# Etiquetas legibles (el backend/thresholds.py no las trae). Mantener sincronizado
# con frontend/src/data/thresholds.ts (labels en español en la app; el bot va en inglés).
LABELS = {
    "heart_rate": "Heart rate",
    "systolic_bp": "Systolic blood pressure",
    "spo2": "SpO2 (oxygen saturation)",
    "body_temp": "Body temperature",
    "glucose": "Glucose",
    "sleep_hours": "Sleep hours",
    "mood": "Mood",
}

# Per tracked indicator: what it is, why it matters in space (HRP hazard), how to
# measure it, and extra sourced facts the assistant can teach.
INDICATORS = {
    "heart_rate": {
        "que_es": "The number of heartbeats per minute at rest.",
        "espacio": (
            "In microgravity the cardiovascular system readapts (fluids shift toward "
            "the chest and head), so your resting HR can differ from Earth. "
            "HRP hazard: altered gravity."
        ),
        "como_medir": "At rest, seated and calm for 5 min. The wrist/finger sensor reads it; you can also count your pulse for 30 s and multiply by 2.",
        "facts": None,
    },
    "systolic_bp": {
        "que_es": "The peak pressure in your arteries when the heart beats (the top number).",
        "espacio": (
            "In flight blood pressure tends to drop a bit versus Earth due to "
            "cardiovascular readaptation, so a fixed Earth threshold can cause false "
            "alarms. HRP hazard: altered gravity."
        ),
        "como_medir": "With the cuff at heart level, at rest and without talking. Avoid measuring right after exercise or coffee.",
        "facts": None,
    },
    "spo2": {
        "que_es": "The percentage of oxygen carried by your red blood cells (saturation).",
        "espacio": (
            "Tracks oxygenation and, indirectly, cabin air quality (a hostile closed "
            "environment controls O2, CO2 and pressure). HRP hazard: hostile closed environment."
        ),
        "como_medir": "With the pulse oximeter on your finger, still for a few seconds until the reading stabilizes. Warm hands give a better signal.",
        "facts": None,
    },
    "body_temp": {
        "que_es": "Your body temperature.",
        "espacio": (
            "An early signal of infection or immune response, which spaceflight can "
            "alter. Note: the limit depends on where the sensor measures (core temp "
            "~= oral + 0.47 C). HRP hazard: hostile closed environment."
        ),
        "como_medir": "With the thermometer at the usual site (oral/armpit/forehead). Always use the same site so readings are comparable.",
        "facts": None,
    },
    "glucose": {
        "que_es": "Your blood sugar level.",
        "espacio": (
            "Reflects your nutrition and metabolism, which matter on long missions "
            "with controlled diet and activity. HRP hazard: hostile closed environment / nutrition."
        ),
        "como_medir": "With the glucometer, ideally fasting or at the same time relative to meals so readings are comparable.",
        "facts": None,
    },
    "sleep_hours": {
        "que_es": "How many hours you slept.",
        "espacio": (
            "Confinement and irregular schedules hurt sleep, and short sleep degrades "
            "mood and cognition. HRP hazards: isolation and confinement (sleep loss)."
        ),
        "como_medir": "Log the real hours of sleep from last night (the sensor's estimate or your own).",
        "facts": (
            "On the ISS 8.5 h are scheduled, but astronauts sleep about 6.5 +/- 1.4 h "
            "(Jones 2022); the scheduled 8.5 h happened only ~5.9% of nights. Seven "
            "nights of 6 h is roughly like 24-36 h awake. Healthy reference: >= 7 h "
            "(AASM/SRS 2015). A sleep alert should follow a pattern, not one reading: "
            "<= 6 h for three nights in a row, or a single night under 5 h."
        ),
    },
    "mood": {
        "que_es": "How you feel emotionally, on a 1 (very bad) to 5 (very good) scale.",
        "espacio": (
            "Prolonged isolation can bring behavioral changes; logging it helps catch "
            "them early. HRP hazard: isolation and confinement (behavioral health)."
        ),
        "como_medir": "Rate yourself 1-5 for your overall mood today. Be honest: it's for you.",
        "facts": (
            "The daily 1-5 emoji is a quick check. Well-being is screened with the WHO-5 "
            "every 14 days (0-100: <= 50 = low well-being, <= 28 = possible depression; "
            "Topp 2015). Ask me about the WHO-5 if you want details."
        ),
    },
}

# Behavioral indicators the assistant can EXPLAIN and guide on, but that the app
# does not track in the database yet (team decision; see docs/decision_integracion_semaforo.md,
# open point 7.3). Sourced from the research ficha.
BEHAVIORAL = {
    "kss": (
        "**Karolinska Sleepiness Scale (KSS)** — a 1-9 self-rating of how sleepy you "
        "feel right now (Akerstedt 2014). Rough reading: green 1-5, yellow 6-7, red 8-9. "
        "If it's >= 7 before a critical task, consider a vigilance check (PVT-B) or a short rest."
    ),
    "who5": (
        "**WHO-5 Well-Being Index** — 5 questions about the last 2 weeks, scored 0-100 "
        "(Topp 2015). Guide: > 50 fine, 29-50 low well-being (worth watching), <= 28 "
        "possible depression (escalate). A 10-point drop from your own baseline is "
        "meaningful. Taken every 14 days, matching NASA's private psychological "
        "conferences (PPC). It's a screen, not a diagnosis."
    ),
    "team": (
        "**Team climate** — a quick daily read of the mood with the crew and with ground "
        "control. It matters because on long missions tension can shift toward mission "
        "control (Kanas); a relationship with ground that turns negative is itself a "
        "warning sign. (The exact threshold here is a design choice, not a sourced cutoff.)"
    ),
}

# The 5 hazards of spaceflight (NASA's Human Research Program; NASA summarizes them
# with the RIDGE acronym).
HAZARDS = {
    "radiation": (
        "Space radiation: one of the most serious risks; it can damage cells and DNA. "
        "It isn't captured by a simple cabin indicator, so in this app it's an "
        "acknowledged limitation (it would need a dosimeter)."
    ),
    "isolation": (
        "Isolation and confinement: small groups in tight quarters for months can show "
        "mood and sleep changes. We reflect it with mood and sleep hours."
    ),
    "distance": (
        "Distance from Earth: medical help can take up to ~20 min one-way, so you must "
        "be able to self-assess and act without waiting for the ground. That's why this "
        "app works offline."
    ),
    "gravity": (
        "Altered gravity: the body readapts (heart, muscles, bones, inner ear). We "
        "reflect it with heart rate and blood pressure."
    ),
    "environment": (
        "Hostile closed environment: the vehicle controls air, pressure, temperature "
        "and microbes. We reflect it with SpO2 and body temperature."
    ),
}

STATUS_EN = {
    Status.NORMAL: "green (normal)",
    Status.ATTENTION: "yellow (attention)",
    Status.CRITICAL: "red (critical)",
}

# English recommendations for the bot (thresholds.py keeps the Spanish ones the
# Spanish app shows; we don't touch those). Sleep/mood improved per the research ficha.
RECOMMENDATIONS_EN = {
    "heart_rate": {
        Status.ATTENTION: "Rest and measure again in 30 min. Avoid intense exercise.",
        Status.CRITICAL: "Report to the flight surgeon. Stay at rest and watch your symptoms.",
    },
    "systolic_bp": {
        Status.ATTENTION: "Hydrate and avoid sudden posture changes.",
        Status.CRITICAL: "Report to the flight surgeon right away.",
    },
    "spo2": {
        Status.ATTENTION: "Check the cabin air quality. Repeat the measurement.",
        Status.CRITICAL: "Immediate alert — possible oxygenation or environment problem.",
    },
    "body_temp": {
        Status.ATTENTION: "Monitor every few hours. Hydrate.",
        Status.CRITICAL: "Possible infection or immune response — contact the flight surgeon.",
    },
    "glucose": {
        Status.ATTENTION: "Adjust your next meal/snack. Measure again in 1-2 h.",
        Status.CRITICAL: "Address it now per your personal medical protocol.",
    },
    "sleep_hours": {
        Status.ATTENTION: "Prioritize sleep hygiene tonight: earlier bedtime, dim light, less caffeine.",
        Status.CRITICAL: "Short sleep risks cognition/mood. If it's <5 h or 3 nights in a row, flag it; avoid critical tasks or EVA if you can.",
    },
    "mood": {
        Status.ATTENTION: "Use behavioral support: exercise, family contact, downtime. Worth a note for the next PPC.",
        Status.CRITICAL: "Reach out to mission behavioral health (BHP). If you have any thought of self-harm, escalate immediately.",
    },
}


def _recommendation(field: str, status: Status) -> Optional[str]:
    if status == Status.NORMAL:
        return None
    return RECOMMENDATIONS_EN.get(field, {}).get(status)

# Escalation guidance (research ficha, section 6). Non-diagnostic.
ESCALATION = (
    "**What you can handle yourself:** sleep hygiene, earlier bedtime, light exposure, "
    "exercise, family contact, short naps.\n"
    "**Note for the next PPC (persistent yellow):** any indicator yellow 3+ days; WHO-5 "
    "between 29 and 50 or a >= 10-point drop; conflict high for 3+ days.\n"
    "**Tell the flight surgeon / BHP now (red):** WHO-5 <= 28; sleep <= 6 h for 3 nights "
    "or under 5 h before an EVA or critical task; KSS 8-9 before a critical task.\n"
    "**Any thought of self-harm: escalate immediately.**"
)

# Gamification (research ficha, section E). Core principle first.
GAMIFICATION = (
    "The golden rule: points are earned for **logging consistently and honestly, never "
    "for \"good\" values** (rewarding good numbers pushes people to fake answers or "
    "under-report). Mechanics that fit:\n"
    "- **Logbook streak** that *pauses* (doesn't reset) when you miss a day.\n"
    "- **\"Honest Report\" badge**: earned when you log a yellow/red and complete the "
    "suggested action.\n"
    "- **Cooperative crew challenge**: the crew logs and adds exercise minutes together, "
    "no individual rankings.\n"
    "- **\"Circadian window\"**: go to bed within +/- 30 min of your target time."
)

# Honesty note for the pitch (research ficha corrections).
HONESTY_NOTE = (
    "A couple of honesty notes for the pitch: \"CONNECT\" is a popular acronym, not an "
    "official HRP strategy (the real countermeasures are NASA's Behavioral Health & "
    "Performance ones). And the numeric cutoffs come from general or lab populations, "
    "not from astronauts, so they're approximations, not validated space criteria."
)

# Quick questions the widget offers as chips (English).
QUICK_QUESTIONS = [
    "How am I doing?",
    "What should I do if something is red?",
    "What is SpO2?",
    "How do I measure blood pressure?",
    "What are the 5 hazards?",
    "How do I log a measurement?",
]


# --------------------------------------------------------------------------- #
# Text + intent utilities (offline core)
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    """minúsculas y sin acentos, para hacer match robusto de palabras clave."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# Synonyms per indicator (English + Spanish, so it matches either language).
INDICATOR_SYNONYMS = {
    "heart_rate": ["heart rate", "heart", "pulse", "bpm", "frecuencia cardiaca", "ritmo cardiaco", "pulso", "latidos", "corazon", "fc"],
    "systolic_bp": ["blood pressure", "systolic", "pressure", "mmhg", "presion", "sistolica", "tension"],
    "spo2": ["spo2", "oxygen", "oxygenation", "saturation", "o2", "oxigeno", "oxigenacion", "saturacion"],
    "body_temp": ["temperature", "fever", "thermometer", "temp", "temperatura", "fiebre", "termometro"],
    "glucose": ["glucose", "sugar", "blood sugar", "glucosa", "azucar", "glucemia", "mg/dl"],
    "sleep_hours": ["sleep", "sleeping", "slept", "rest", "sueno", "dormir", "dormi", "descanso"],
    "mood": ["mood", "feeling", "emotional", "animo", "estado de animo", "humor", "me siento"],
}

HAZARD_SYNONYMS = {
    "radiation": ["radiation", "radiacion"],
    "isolation": ["isolation", "confinement", "loneliness", "aislamiento", "confinamiento", "soledad"],
    "distance": ["distance", "delay", "earth", "20 min", "distancia", "retraso", "tierra"],
    "gravity": ["gravity", "microgravity", "weightless", "gravedad", "microgravedad", "ingravidez"],
    "environment": ["environment", "cabin", "air", "closed", "ambiente", "cabina", "aire", "cerrado"],
}

BEHAVIORAL_SYNONYMS = {
    "kss": ["kss", "karolinska", "sleepiness", "somnolencia", "drowsy"],
    "who5": ["who-5", "who5", "well-being", "wellbeing", "bienestar", "depression", "depresion"],
    "team": ["team", "crew", "conflict", "ground control", "mission control", "equipo", "tripulacion", "conflicto"],
}


def _detect_indicator(text: str) -> Optional[str]:
    for key, syns in INDICATOR_SYNONYMS.items():
        if any(s in text for s in syns):
            return key
    return None


def _detect_behavioral(text: str) -> Optional[str]:
    for key, syns in BEHAVIORAL_SYNONYMS.items():
        if any(s in text for s in syns):
            return key
    return None


def _has(text: str, *words: str) -> bool:
    return any(w in text for w in words)


# --------------------------------------------------------------------------- #
# Astronaut's real context (from the database)
# --------------------------------------------------------------------------- #

def _recent_records(session: Session, astronaut_id: str, limit: int = 8):
    stmt = (
        select(HealthRecord)
        .where(HealthRecord.astronaut_id == astronaut_id)
        .order_by(HealthRecord.timestamp.desc())
        .limit(limit)
    )
    return list(session.exec(stmt).all())


def _assess(record: HealthRecord) -> dict:
    """Status + recommendation for each indicator present in the record."""
    out = {}
    for field in THRESHOLDS:
        value = getattr(record, field, None)
        if value is None:
            continue
        status = evaluate(field, value)
        out[field] = {
            "value": value,
            "status": status,
            "recommendation": _recommendation(field, status),
        }
    return out


def _trend(records, field: str) -> Optional[str]:
    """Simple direction of the indicator over recent readings (up/down/stable)."""
    values = [getattr(r, field) for r in reversed(records) if getattr(r, field) is not None]
    if len(values) < 2:
        return None
    delta = values[-1] - values[0]
    span = max(abs(v) for v in values) or 1
    if abs(delta) < 0.03 * span:
        return "stable"
    return "rising" if delta > 0 else "falling"


def _age_text(record: Optional[HealthRecord]) -> Optional[str]:
    if record is None:
        return None
    ts = record.timestamp
    if ts.tzinfo is None:
        from datetime import timezone as _tz
        ts = ts.replace(tzinfo=_tz.utc)
    minutes = (utcnow() - ts).total_seconds() / 60
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{int(minutes)} min ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} h ago"
    return f"{int(hours / 24)} day(s) ago"


def build_context(session: Session, astronaut_id: str) -> dict:
    """Build the current state: latest record, traffic light, trends and alerts.

    NOTE: this is the single place that computes status. When the baseline traffic
    light (semaforo_bridge.compute_status) is implemented, switch _assess here.
    """
    records = _recent_records(session, astronaut_id)
    if not records:
        return {"has_data": False, "alerts": [], "records": []}

    latest = records[0]
    assessment = _assess(latest)
    alerts = []
    for field, a in assessment.items():
        if a["status"] != Status.NORMAL:
            alerts.append({
                "indicator": field,
                "label": LABELS.get(field, field),
                "value": a["value"],
                "unit": THRESHOLDS[field]["unit"],
                "status": a["status"].value,
                "status_en": STATUS_EN[a["status"]],
                "recommendation": a["recommendation"],
            })
    # red first, then yellow
    alerts.sort(key=lambda x: 0 if x["status"] == "critical" else 1)

    trends = {f: _trend(records, f) for f in THRESHOLDS}
    return {
        "has_data": True,
        "age_text": _age_text(latest),
        "assessment": assessment,
        "alerts": alerts,
        "trends": trends,
        "records": records,
    }


def _context_summary_text(ctx: dict) -> str:
    """Readable summary of the state, used in rule answers and as LLM input."""
    if not ctx["has_data"]:
        return "No health records yet for this astronaut."
    lines = [f"Last measurement: {ctx['age_text']}."]
    if ctx.get("external"):
        lines.append("Colors come from your personal-baseline traffic light, not from fixed thresholds.")
    for field, a in ctx["assessment"].items():
        label = a.get("label") or LABELS.get(field, field)
        unit = a.get("unit") or THRESHOLDS.get(field, {}).get("unit", "")
        trend = ctx["trends"].get(field)
        trend_txt = f", trend {trend}" if trend and trend != "stable" else ""
        lines.append(f"- {label}: {a['value']} {unit} -> {STATUS_EN[a['status']]}{trend_txt}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Rule engine (guaranteed offline answer)
# --------------------------------------------------------------------------- #

def _indicator_answer(field: str, ctx: dict) -> str:
    info = INDICATORS[field]
    label = LABELS[field]
    rule = THRESHOLDS[field]
    unit = rule["unit"]
    n_lo, n_hi = rule["normal"]
    parts = [
        f"**{label}** — {info['que_es']}",
        f"Why it matters in space: {info['espacio']}",
        f"How to measure it: {info['como_medir']}",
        f"Reference normal range: {n_lo}-{n_hi} {unit}.",
    ]
    if info.get("facts"):
        parts.append(info["facts"])
    # Include the latest reading if available.
    if ctx["has_data"] and field in ctx["assessment"]:
        a = ctx["assessment"][field]
        parts.append(f"Your latest reading: {a['value']} {unit} -> {STATUS_EN[a['status']]}.")
        if a["recommendation"]:
            parts.append(f"Suggestion: {a['recommendation']}")
    return "\n".join(parts)


def _action_answer(ctx: dict, field: Optional[str]) -> str:
    if not ctx["has_data"]:
        return (
            "Log a measurement first and I'll tell you what to do based on your traffic "
            "light.\nIn general: if something is yellow, repeat the measurement and keep "
            "watching; if it's red or it persists, report it to the mission's medical "
            "officer.\n\n" + ESCALATION
        )
    targets = [field] if field else [a["indicator"] for a in ctx["alerts"]]
    if not targets:
        return "Right now every indicator with data is green. Keep up your routine 👍"
    lines = []
    for f in targets:
        a = ctx["assessment"].get(f)
        if not a:
            continue
        label = a.get("label") or LABELS.get(f, f)
        if a["status"] == Status.NORMAL:
            lines.append(f"**{label}** is green, no action needed.")
        else:
            rec = a["recommendation"] or "Repeat the measurement and watch how it evolves."
            lines.append(f"**{label}** is {STATUS_EN[a['status']]}: {rec}")
    lines.append("")
    lines.append(ESCALATION)
    return "\n".join(lines)


def _status_answer(ctx: dict) -> str:
    if not ctx["has_data"]:
        return "You have no records yet. Enter at least one indicator and I'll assess your state."
    summary = _context_summary_text(ctx)
    if ctx["alerts"]:
        n = len(ctx["alerts"])
        head = f"You have {n} indicator(s) outside green. Check:"
    else:
        head = "Everything you logged is green ✅. Nice work."
    return f"{head}\n{summary}"


def _hazards_answer(text: str) -> str:
    for key, syns in HAZARD_SYNONYMS.items():
        if any(s in text for s in syns):
            return HAZARDS[key]
    intro = "The 5 hazards of spaceflight per NASA's Human Research Program (NASA calls them RIDGE):"
    bullets = "\n".join(f"• {HAZARDS[k]}" for k in ["radiation", "isolation", "distance", "gravity", "environment"])
    return f"{intro}\n{bullets}"


def _app_help_answer(text: str) -> str:
    if _has(text, "traffic light", "color", "green", "yellow", "red", "semaforo", "verde", "amarillo", "rojo"):
        return (
            "The traffic light sums up your state at a glance: **green** = normal, "
            "**yellow** = attention (repeat and watch), **red** = critical (act and "
            "report). Each body part is colored by its indicators."
        )
    return (
        "To log: type your values into each indicator card and press **Register "
        "measurement**. You don't need to fill them all; one is enough. Then you'll see "
        "the color on the figure, the recommendations and the trend charts. Leave blank "
        "anything you didn't measure."
    )


def _gamification_answer(session: Session, astronaut_id: str, ctx: dict) -> str:
    records = ctx.get("records") or []
    total = len(records)
    if not ctx["has_data"]:
        return (
            "Start your streak! Logging your indicators every day is the best health "
            "routine on a mission. Make your first measurement 🚀\n\n" + GAMIFICATION
        )
    if ctx["alerts"]:
        return (
            "Today is a self-care day: you have indicators outside green. Follow the "
            "suggestion and measure again — getting back to green counts as a win 💪 "
            "(that's exactly the \"Honest Report\" idea).\n\n" + GAMIFICATION
        )
    if ctx.get("external"):
        return (
            "Going well! Everything you have on screen is green ✅. Keep the routine: "
            "measuring at the same time each day makes your trends more useful.\n\n" + GAMIFICATION
        )
    return (
        f"Going well! You've logged {total} recent measurement(s) and today everything "
        f"is green ✅. Keep the routine: measuring at the same time each day makes your "
        f"trends more useful.\n\n" + GAMIFICATION
    )


def rule_based_reply(message: str, session: Session, astronaut_id: str, ctx: dict) -> str:
    """Decide the intent and answer using only the knowledge base + context."""
    text = _norm(message)

    # Self-harm safety: always escalate, regardless of other intent.
    if _has(text, "hurt myself", "kill myself", "self-harm", "self harm", "suicid", "end my life", "hacerme dano", "lastimarme", "quitarme la vida"):
        return (
            "I'm really glad you told me. This is above what this app handles: please "
            "contact the flight surgeon or Behavioral Health & Performance (BHP) right "
            "now — any thought of self-harm is an immediate escalation. You don't have "
            "to deal with this alone."
        )

    # Pure greeting
    if _has(text, "hello", "hi", "hey", "hola", "buenas") and len(text) <= 15:
        head = "Hi! I'm your on-board health assistant."
        if ctx["has_data"] and ctx["alerts"]:
            head += f" Heads up: you have {len(ctx['alerts'])} indicator(s) outside green."
        return (
            f"{head} I can explain indicators and risks, tell you how you're doing, "
            "guide you if something is out of range, and help you use the app. What do you need?"
        )

    # Honesty note for the pitch
    if _has(text, "connect", "honest", "pitch", "validated", "source", "fuente", "validado"):
        return HONESTY_NOTE

    # Behavioral extras (KSS / WHO-5 / team climate)
    behavioral = _detect_behavioral(text)
    if behavioral and _detect_indicator(text) is None:
        return BEHAVIORAL[behavioral]

    # Hazards
    if _has(text, "hazard", "hazards", "risk", "peligro", "peligros", "riesgo") or any(
        s in text for syns in HAZARD_SYNONYMS.values() for s in syns
    ):
        if _detect_indicator(text) is None:
            return _hazards_answer(text)

    indicator = _detect_indicator(text)

    # What should I do / action guidance
    if _has(text, "what should i do", "what do i do", "action", "recommend", "out of range", "is red", "is yellow", "feel bad", "que hago", "que debo", "accion", "recomendacion"):
        return _action_answer(ctx, indicator)

    # Escalation specifically
    if _has(text, "escalate", "report", "flight surgeon", "when do i", "escalar", "reportar"):
        return ESCALATION

    # How am I / summary
    if _has(text, "how am i", "my state", "my status", "summary", "how am i doing", "como estoy", "mi estado", "resumen"):
        return _status_answer(ctx)

    # How to measure
    if indicator and _has(text, "how do i measure", "how to measure", "measure", "take a reading", "como mido", "como medir", "medir"):
        return INDICATORS[indicator]["como_medir"] + f"\n\n({DISCLAIMER})"

    # Question about a specific indicator
    if indicator:
        return _indicator_answer(indicator, ctx)

    # App help
    if _has(text, "register", "log", "how do i use", "how does it work", "traffic light", "chart", "app", "help", "registrar", "registro", "semaforo", "ayuda"):
        return _app_help_answer(text)

    # Gamification
    if _has(text, "streak", "points", "badge", "challenge", "reminder", "motivate", "game", "racha", "puntos", "logro", "reto", "recordatorio"):
        return _gamification_answer(session, astronaut_id, ctx)

    # Fallback
    return (
        "I can help you with:\n"
        "• Explaining an indicator (e.g. \"What is SpO2?\") and how to measure it.\n"
        "• Telling you how you're doing and what to do if something is out of range.\n"
        "• The 5 hazards of spaceflight, and behavioral checks (sleep, KSS, WHO-5, team).\n"
        "• How to use the app and read the traffic light.\n"
        "Which one would you like to start with?"
    )


# --------------------------------------------------------------------------- #
# Optional LLM layer (rephrases, grounded in the KB + context)
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = (
    "You are the on-board health assistant of an app that helps astronauts on long "
    "missions SELF-ASSESS. You speak English, in a warm, clear and brief tone (2-5 "
    "sentences). Strict rules:\n"
    "1) Use ONLY the FACTS and CONTEXT I give you; do not invent numbers, ranges or "
    "diagnoses. If it's not in the facts, say so and suggest logging data.\n"
    "2) You are not medical advice and the data is synthetic: do not diagnose. For red "
    "states or anything that persists, recommend reporting to the flight surgeon / BHP. "
    "Any mention of self-harm: escalate immediately.\n"
    "3) Do not mention NASA brands, logos or identifiers.\n"
    "4) The goal is for the astronaut to understand and decide their own first steps."
)


def llm_reply(message: str, facts: str, context_summary: str, history: Optional[list]) -> Optional[str]:
    """Try to rephrase with Claude. Returns None on any failure (no API key, no
    internet, API error) so the caller uses the rule-based answer."""
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    user_block = (
        f"ASTRONAUT CONTEXT (real app data):\n{context_summary}\n\n"
        f"FACTS YOU MAY USE (from our knowledge base):\n{facts}\n\n"
        f"ASTRONAUT'S QUESTION:\n{message}\n\n"
        "Answer in English, briefly, using only those facts and context."
    )
    messages = []
    for turn in (history or [])[-6:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_block})

    try:
        client = anthropic.Anthropic(timeout=20.0, max_retries=1)
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=600,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        if resp.stop_reason == "refusal":
            return None
        text = next((b.text for b in resp.content if b.type == "text"), "").strip()
        return text or None
    except Exception:
        # Offline-first: any error -> use the rule-based core.
        return None


def _facts_for(message: str, ctx: dict) -> str:
    """Select the relevant KB facts to ground the LLM."""
    text = _norm(message)
    chunks = []
    indicator = _detect_indicator(text)
    if indicator:
        info = INDICATORS[indicator]
        rule = THRESHOLDS[indicator]
        chunk = (
            f"{LABELS[indicator]}: {info['que_es']} {info['espacio']} "
            f"How to measure: {info['como_medir']} "
            f"Normal range: {rule['normal'][0]}-{rule['normal'][1]} {rule['unit']}."
        )
        if info.get("facts"):
            chunk += " " + info["facts"]
        chunks.append(chunk)
    behavioral = _detect_behavioral(text)
    if behavioral:
        chunks.append(BEHAVIORAL[behavioral])
    if any(s in text for syns in HAZARD_SYNONYMS.values() for s in syns) or _has(text, "hazard", "risk", "peligro", "riesgo"):
        chunks.append("Hazards (RIDGE): " + " | ".join(HAZARDS.values()))
    if _has(text, "what should i do", "action", "escalate", "report", "que hago", "escalar"):
        chunks.append(ESCALATION)
    if _has(text, "streak", "points", "badge", "challenge", "game", "racha", "puntos", "reto"):
        chunks.append(GAMIFICATION)
    if _has(text, "traffic light", "register", "app", "chart", "color", "semaforo", "registrar"):
        chunks.append(_app_help_answer(text))
    # Always include the base action guide in case they ask what to do.
    chunks.append(
        "Traffic light: green=normal, yellow=attention (repeat and watch), "
        "red=critical (act and report to the flight surgeon)."
    )
    return "\n".join(chunks)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

class ClientIndicator(BaseModel):
    indicator: str = Field(max_length=40)
    label: Optional[str] = Field(default=None, max_length=60)
    value: float
    unit: Optional[str] = Field(default=None, max_length=20)
    status: Literal["normal", "attention", "critical"]


class ClientContext(BaseModel):
    """State the page already shows (prototipo/): the page computed the colors with the
    personal-baseline traffic light, so the assistant uses them as given instead of
    re-evaluating the database with fixed thresholds."""
    astronaut: Optional[str] = Field(default=None, max_length=40)
    when: Optional[str] = Field(default=None, max_length=40)
    indicators: list[ClientIndicator] = Field(default_factory=list, max_length=20)


def context_from_client(c: ClientContext) -> dict:
    if not c.indicators:
        return {"has_data": False, "alerts": [], "records": [], "external": True}
    assessment, alerts = {}, []
    for ind in c.indicators:
        status = Status(ind.status)
        label = ind.label or LABELS.get(ind.indicator, ind.indicator)
        unit = ind.unit or THRESHOLDS.get(ind.indicator, {}).get("unit", "")
        rec = _recommendation(ind.indicator, status)
        value = int(ind.value) if float(ind.value).is_integer() else ind.value
        assessment[ind.indicator] = {"value": value, "status": status, "recommendation": rec, "label": label, "unit": unit}
        if status != Status.NORMAL:
            alerts.append({
                "indicator": ind.indicator, "label": label, "value": value, "unit": unit,
                "status": status.value, "status_en": STATUS_EN[status], "recommendation": rec,
            })
    alerts.sort(key=lambda x: 0 if x["status"] == "critical" else 1)
    return {
        "has_data": True,
        "age_text": c.when or "current reading",
        "assessment": assessment,
        "alerts": alerts,
        "trends": {},
        "records": [],
        "external": True,
    }


class ChatRequest(BaseModel):
    message: str
    astronaut_id: str = "default"
    history: Optional[list] = None  # [{role: 'user'|'assistant', content: str}]
    context: Optional[ClientContext] = None  # sent by prototipo/; the React app omits it


class StatusRequest(BaseModel):
    astronaut_id: str = "default"
    context: Optional[ClientContext] = None


@router.post("")
def chat(payload: ChatRequest, session: Session = Depends(get_session)):
    ctx = context_from_client(payload.context) if payload.context else build_context(session, payload.astronaut_id)

    # 1) Rule-based core (always available, it's the fallback).
    rule_reply = rule_based_reply(payload.message, session, payload.astronaut_id, ctx)

    # 2) Optional LLM layer, grounded in the same facts + context.
    facts = _facts_for(payload.message, ctx)
    context_summary = _context_summary_text(ctx)
    llm = llm_reply(payload.message, facts, context_summary, payload.history)

    reply = llm or rule_reply
    return {
        "reply": reply,
        "source": "llm" if llm else "rules",
        "alerts": ctx["alerts"],
        "disclaimer": DISCLAIMER,
    }


@router.get("/status")
def status(astronaut_id: str = "default", session: Session = Depends(get_session)):
    """Greeting + proactive alerts so the widget can warn when it opens."""
    return _status_payload(build_context(session, astronaut_id))


@router.post("/status")
def status_with_context(payload: StatusRequest, session: Session = Depends(get_session)):
    """Same as GET /chat/status, for pages that send their own on-screen state."""
    ctx = context_from_client(payload.context) if payload.context else build_context(session, payload.astronaut_id)
    return _status_payload(ctx)


def _status_payload(ctx: dict) -> dict:
    if not ctx["has_data"]:
        greeting = (
            "Hi! I'm your health assistant. You haven't logged any measurements yet — "
            "enter your indicators and I'll help you read them."
        )
    elif ctx["alerts"]:
        n = len(ctx["alerts"])
        greeting = f"Heads up: {n} indicator(s) outside green ({ctx['age_text']}). Ask me \"what should I do?\"."
    else:
        greeting = f"All green ✅ ({ctx['age_text']}). How can I help?"
    return {
        "greeting": greeting,
        "alerts": ctx["alerts"],
        "quick_questions": QUICK_QUESTIONS,
        "disclaimer": DISCLAIMER,
        "llm_available": bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")),
    }
