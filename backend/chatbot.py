"""
Asistente de salud (chatbot) para el Astronaut Health Monitor.

Diseño HÍBRIDO:
- Núcleo OFFLINE por reglas: siempre responde, sin internet ni API key, usando la
  base de conocimiento de este archivo + el contexto real del astronauta (último
  registro, semáforo, tendencia). Es el argumento del reto: la tripulación decide
  sin esperar a la Tierra (hasta 20 min de retraso).
- Capa LLM OPCIONAL: si hay ANTHROPIC_API_KEY + internet, Claude redacta la misma
  respuesta de forma más natural, ANCLADA a los hechos de la KB y al contexto. Si
  falla por cualquier razón, se cae a la respuesta por reglas. Nunca se rompe.

Honestidad (obligatoria, ver CLAUDE.md):
- Datos de demo sintéticos; no es un modelo fisiológico validado ni consejo médico.
- Los rangos son referencias clínicas terrestres, no criterios de alarma de NASA.
- No se usa branding de NASA. El uso de IA se declara en la UI (regla de SI del reto).
"""
from __future__ import annotations

import os
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from models import HealthRecord, get_session, utcnow
from thresholds import THRESHOLDS, Status, evaluate, get_recommendation

router = APIRouter(prefix="/chat", tags=["chatbot"])

# Modelo del LLM. Por defecto Opus 5; el equipo puede bajarlo a un modelo más
# barato con CHATBOT_MODEL=claude-haiku-4-5 para la demo.
LLM_MODEL = os.getenv("CHATBOT_MODEL", "claude-opus-5")

DISCLAIMER = (
    "No soy consejo médico y los datos de la demo son sintéticos. Los rangos son "
    "referencias clínicas generales (de la Tierra), no criterios de alarma de NASA."
)

# --------------------------------------------------------------------------- #
# Base de conocimiento (fuente única de los textos del asistente)
# --------------------------------------------------------------------------- #

# Etiquetas legibles (el backend/thresholds.py no las trae; se replican de
# frontend/src/data/thresholds.ts). Mantener sincronizado.
LABELS = {
    "heart_rate": "Frecuencia cardíaca",
    "systolic_bp": "Presión sistólica",
    "spo2": "SpO2 (oxigenación)",
    "body_temp": "Temperatura corporal",
    "glucose": "Glucosa",
    "sleep_hours": "Horas de sueño",
    "mood": "Estado de ánimo",
}

# Por indicador: qué es, por qué importa en el espacio (peligro HRP asociado),
# cómo medirlo y qué hacer según el estado del semáforo.
INDICATORS = {
    "heart_rate": {
        "que_es": "El número de latidos del corazón por minuto en reposo.",
        "espacio": (
            "En microgravedad el sistema cardiovascular se readapta (los líquidos "
            "se desplazan hacia el torso y la cabeza), así que tu FC en reposo puede "
            "cambiar respecto a la Tierra. Peligro HRP: gravedad alterada."
        ),
        "como_medir": "En reposo, sentado y tranquilo 5 min. El sensor de muñeca/dedo la toma; también puedes contar el pulso 30 s y multiplicar por 2.",
    },
    "systolic_bp": {
        "que_es": "La presión máxima en las arterias cuando el corazón late (el número de arriba).",
        "espacio": (
            "En vuelo la presión tiende a bajar un poco respecto a la Tierra por la "
            "readaptación cardiovascular; por eso un umbral fijo terrestre puede dar "
            "falsas alarmas. Peligro HRP: gravedad alterada."
        ),
        "como_medir": "Con el brazalete a la altura del corazón, en reposo y sin hablar. Evita medir justo después de ejercicio o café.",
    },
    "spo2": {
        "que_es": "El porcentaje de oxígeno que llevan tus glóbulos rojos (saturación).",
        "espacio": (
            "Vigila la oxigenación y, de forma indirecta, la calidad del aire de la "
            "cabina (un ambiente cerrado hostil controla O2, CO2 y presión). "
            "Peligros HRP: ambiente cerrado hostil."
        ),
        "como_medir": "Con el oxímetro en el dedo, quieto unos segundos hasta que la lectura se estabilice. Manos tibias dan mejor señal.",
    },
    "body_temp": {
        "que_es": "La temperatura de tu cuerpo.",
        "espacio": (
            "Sirve como señal temprana de infección o de respuesta inmune, que el "
            "espacio puede alterar. Ojo: el límite depende de dónde mida el sensor "
            "(central ≈ oral + 0,47 °C). Peligro HRP: ambiente cerrado hostil."
        ),
        "como_medir": "Con el termómetro en el sitio habitual (oral/axilar/frente). Usa siempre el mismo sitio para poder comparar.",
    },
    "glucose": {
        "que_es": "El nivel de azúcar en la sangre.",
        "espacio": (
            "Refleja tu nutrición y metabolismo, que importan en misiones largas con "
            "dieta y actividad controladas. Peligro HRP: ambiente cerrado / nutrición."
        ),
        "como_medir": "Con el glucómetro, idealmente en ayunas o a la misma hora respecto a las comidas para comparar.",
    },
    "sleep_hours": {
        "que_es": "Las horas que dormiste.",
        "espacio": (
            "El confinamiento y los horarios irregulares afectan el sueño, y dormir "
            "poco deteriora el ánimo y la cognición. Peligros HRP: aislamiento y "
            "confinamiento."
        ),
        "como_medir": "Registra las horas reales de sueño de la última noche (el sensor o tu propia estimación).",
    },
    "mood": {
        "que_es": "Cómo te sientes anímicamente, en una escala de 1 (muy mal) a 5 (muy bien).",
        "espacio": (
            "El aislamiento prolongado puede traer cambios de comportamiento; "
            "registrarlo ayuda a detectarlos a tiempo. Peligro HRP: aislamiento y "
            "confinamiento."
        ),
        "como_medir": "Autoevalúate del 1 al 5 pensando en tu ánimo general de hoy. Sé honesto: es para ti.",
    },
}

# Los 5 peligros del Human Research Program de NASA.
HAZARDS = {
    "radiacion": (
        "Radiación espacial: uno de los riesgos más serios; puede dañar células y "
        "ADN. No se mide con un indicador simple en cabina, así que en esta app es "
        "una limitación reconocida (haría falta un dosímetro)."
    ),
    "aislamiento": (
        "Aislamiento y confinamiento: grupos pequeños en espacio reducido por meses "
        "pueden tener cambios de ánimo y sueño. Lo reflejamos con ánimo y horas de sueño."
    ),
    "distancia": (
        "Distancia de la Tierra: la ayuda médica puede tardar hasta ~20 min en "
        "responder, así que debes poder autoevaluarte y actuar sin esperar a tierra. "
        "Por eso esta app funciona sin conexión."
    ),
    "gravedad": (
        "Gravedad alterada: el cuerpo se readapta (corazón, músculos, huesos, oído "
        "interno). Lo reflejamos con frecuencia cardíaca y presión."
    ),
    "ambiente": (
        "Ambiente cerrado hostil: la nave controla aire, presión, temperatura y "
        "microbios. Lo reflejamos con SpO2 y temperatura corporal."
    ),
}

STATUS_ES = {
    Status.NORMAL: "verde (normal)",
    Status.ATTENTION: "amarillo (atención)",
    Status.CRITICAL: "rojo (crítico)",
}

# Preguntas rápidas que el widget ofrece como chips.
QUICK_QUESTIONS = [
    "¿Cómo estoy?",
    "¿Qué hago si algo está en rojo?",
    "¿Qué es la SpO2?",
    "¿Cómo mido la presión?",
    "¿Cuáles son los 5 peligros?",
    "¿Cómo registro una medición?",
]


# --------------------------------------------------------------------------- #
# Utilidades de texto e intención (núcleo offline)
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    """minúsculas y sin acentos, para hacer match robusto de palabras clave."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# Sinónimos por indicador para detectar de cuál habla el usuario.
INDICATOR_SYNONYMS = {
    "heart_rate": ["frecuencia cardiaca", "ritmo cardiaco", "pulso", "latidos", "corazon", "fc", "bpm"],
    "systolic_bp": ["presion", "sistolica", "tension", "mmhg", "blood pressure"],
    "spo2": ["spo2", "oxigeno", "oxigenacion", "saturacion", "o2"],
    "body_temp": ["temperatura", "fiebre", "termometro", "temp"],
    "glucose": ["glucosa", "azucar", "glucemia", "mg/dl"],
    "sleep_hours": ["sueno", "dormir", "dormi", "horas de sueno", "descanso"],
    "mood": ["animo", "estado de animo", "humor", "mood", "me siento"],
}

HAZARD_SYNONYMS = {
    "radiacion": ["radiacion", "radiation"],
    "aislamiento": ["aislamiento", "confinamiento", "soledad"],
    "distancia": ["distancia", "retraso", "tierra", "20 min"],
    "gravedad": ["gravedad", "microgravedad", "ingravidez"],
    "ambiente": ["ambiente", "cabina", "aire", "cerrado"],
}


def _detect_indicator(text: str) -> Optional[str]:
    for key, syns in INDICATOR_SYNONYMS.items():
        if any(s in text for s in syns):
            return key
    return None


def _has(text: str, *words: str) -> bool:
    return any(w in text for w in words)


# --------------------------------------------------------------------------- #
# Contexto real del astronauta (desde la base de datos)
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
    """Estado + recomendación por cada indicador presente en el registro."""
    out = {}
    for field in THRESHOLDS:
        value = getattr(record, field, None)
        if value is None:
            continue
        status = evaluate(field, value)
        out[field] = {
            "value": value,
            "status": status,
            "recommendation": get_recommendation(field, status),
        }
    return out


def _trend(records, field: str) -> Optional[str]:
    """Dirección simple del indicador en las últimas lecturas (sube/baja/estable)."""
    values = [getattr(r, field) for r in reversed(records) if getattr(r, field) is not None]
    if len(values) < 2:
        return None
    delta = values[-1] - values[0]
    span = max(abs(v) for v in values) or 1
    if abs(delta) < 0.03 * span:
        return "estable"
    return "subiendo" if delta > 0 else "bajando"


def _age_text(record: Optional[HealthRecord]) -> Optional[str]:
    if record is None:
        return None
    ts = record.timestamp
    if ts.tzinfo is None:
        from datetime import timezone as _tz
        ts = ts.replace(tzinfo=_tz.utc)
    minutes = (utcnow() - ts).total_seconds() / 60
    if minutes < 1:
        return "hace un momento"
    if minutes < 60:
        return f"hace {int(minutes)} min"
    hours = minutes / 60
    if hours < 24:
        return f"hace {int(hours)} h"
    return f"hace {int(hours / 24)} día(s)"


def build_context(session: Session, astronaut_id: str) -> dict:
    """Arma el estado actual: último registro, semáforo, tendencias y alertas."""
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
                "status_es": STATUS_ES[a["status"]],
                "recommendation": a["recommendation"],
            })
    # rojo primero, luego amarillo
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
    """Resumen legible del estado, usado en respuestas por reglas y como insumo del LLM."""
    if not ctx["has_data"]:
        return "Aún no hay registros de salud para este astronauta."
    lines = [f"Última medición: {ctx['age_text']}."]
    for field, a in ctx["assessment"].items():
        label = LABELS.get(field, field)
        unit = THRESHOLDS[field]["unit"]
        trend = ctx["trends"].get(field)
        trend_txt = f", tendencia {trend}" if trend and trend != "estable" else ""
        lines.append(f"- {label}: {a['value']} {unit} → {STATUS_ES[a['status']]}{trend_txt}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Motor por reglas (respuesta offline garantizada)
# --------------------------------------------------------------------------- #

def _indicator_answer(field: str, ctx: dict) -> str:
    info = INDICATORS[field]
    label = LABELS[field]
    rule = THRESHOLDS[field]
    unit = rule["unit"]
    n_lo, n_hi = rule["normal"]
    parts = [
        f"**{label}** — {info['que_es']}",
        f"Por qué importa en el espacio: {info['espacio']}",
        f"Cómo medirlo: {info['como_medir']}",
        f"Rango normal de referencia: {n_lo}–{n_hi} {unit}.",
    ]
    # Si hay dato reciente, lo incluimos.
    if ctx["has_data"] and field in ctx["assessment"]:
        a = ctx["assessment"][field]
        parts.append(f"Tu última lectura: {a['value']} {unit} → {STATUS_ES[a['status']]}.")
        if a["recommendation"]:
            parts.append(f"Sugerencia: {a['recommendation']}")
    return "\n".join(parts)


def _action_answer(ctx: dict, field: Optional[str]) -> str:
    if not ctx["has_data"]:
        return (
            "Primero registra una medición y te diré qué hacer según tu semáforo.\n"
            "En general: si algo sale en amarillo, repite la medición y vigila; si "
            "sale en rojo o persiste, repórtalo al oficial médico de la misión."
        )
    targets = [field] if field else [a["indicator"] for a in ctx["alerts"]]
    if not targets:
        return "Ahora mismo todos tus indicadores con dato están en verde. Mantén tu rutina 👍"
    lines = []
    for f in targets:
        a = ctx["assessment"].get(f)
        if not a:
            continue
        label = LABELS.get(f, f)
        if a["status"] == Status.NORMAL:
            lines.append(f"**{label}** está en verde, sin acción necesaria.")
        else:
            rec = a["recommendation"] or "Repite la medición y vigila la evolución."
            lines.append(f"**{label}** en {STATUS_ES[a['status']]}: {rec}")
    lines.append(
        "Si un indicador queda en rojo, no mejora al repetir, o aparecen síntomas, "
        "repórtalo al oficial médico (flight surgeon)."
    )
    return "\n".join(lines)


def _status_answer(ctx: dict) -> str:
    if not ctx["has_data"]:
        return "Aún no tienes registros. Ingresa al menos un indicador y evalúo tu estado."
    summary = _context_summary_text(ctx)
    if ctx["alerts"]:
        n = len(ctx["alerts"])
        head = f"Tienes {n} indicador(es) fuera de verde. Revisa:"
    else:
        head = "Todo lo que registraste está en verde ✅. Buen trabajo."
    return f"{head}\n{summary}"


def _hazards_answer(text: str) -> str:
    for key, syns in HAZARD_SYNONYMS.items():
        if any(s in text for s in syns):
            return HAZARDS[key]
    intro = "Los 5 peligros del vuelo espacial según el Human Research Program de NASA:"
    bullets = "\n".join(f"• {HAZARDS[k]}" for k in ["radiacion", "aislamiento", "distancia", "gravedad", "ambiente"])
    return f"{intro}\n{bullets}"


def _app_help_answer(text: str) -> str:
    if _has(text, "semaforo", "color", "verde", "amarillo", "rojo"):
        return (
            "El semáforo resume tu estado de un vistazo: **verde** = normal, "
            "**amarillo** = atención (repite y vigila), **rojo** = crítico (actúa y "
            "reporta). Cada parte del cuerpo se pinta con el color de sus indicadores."
        )
    return (
        "Para registrar: escribe tus valores en las tarjetas de cada indicador y pulsa "
        "**Registrar medición**. No hace falta llenar todos; con uno basta. Luego verás "
        "el color en la figura, las recomendaciones y las gráficas de tendencia. "
        "Puedes dejar vacío lo que no mediste."
    )


def _gamification_answer(session: Session, astronaut_id: str, ctx: dict) -> str:
    records = ctx.get("records") or []
    total = len(records)
    if not ctx["has_data"]:
        return (
            "¡Empieza tu racha! Registrar tus indicadores cada día es la mejor rutina "
            "de salud en una misión. Haz tu primera medición y te felicito 🚀"
        )
    if ctx["alerts"]:
        return (
            "Hoy toca cuidarte: tienes indicadores fuera de verde. Atiende la "
            "recomendación y vuelve a medir — recuperar el verde cuenta como logro 💪"
        )
    return (
        f"¡Vas bien! Llevas {total} medición(es) recientes y hoy todo está en verde ✅. "
        "Mantén la rutina: medir a la misma hora cada día hace tus tendencias más útiles."
    )


def rule_based_reply(message: str, session: Session, astronaut_id: str, ctx: dict) -> str:
    """Decide la intención y responde solo con la base de conocimiento + contexto."""
    text = _norm(message)

    # Saludo puro
    if _has(text, "hola", "buenas", "hey", "saludos") and len(text) <= 15:
        head = "¡Hola! Soy tu asistente de salud a bordo."
        if ctx["has_data"] and ctx["alerts"]:
            head += f" Ojo: tienes {len(ctx['alerts'])} indicador(es) fuera de verde."
        return (
            f"{head} Puedo explicarte indicadores y riesgos, decirte cómo estás, "
            "guiarte si algo sale de rango y ayudarte a usar la app. ¿Qué necesitas?"
        )

    # Peligros HRP
    if _has(text, "peligro", "peligros", "riesgo", "hazard") or any(
        s in text for syns in HAZARD_SYNONYMS.values() for s in syns
    ):
        # Si además pregunta por un indicador, prioriza el indicador abajo.
        if _detect_indicator(text) is None:
            return f"{_hazards_answer(text)}"

    indicator = _detect_indicator(text)

    # ¿Qué hago / guía de acción?
    if _has(text, "que hago", "que debo", "accion", "recomendacion", "deberia", "fuera de rango", "en rojo", "en amarillo", "mal"):
        return _action_answer(ctx, indicator)

    # ¿Cómo estoy / resumen?
    if _has(text, "como estoy", "mi estado", "resumen", "como voy", "estoy bien"):
        return _status_answer(ctx)

    # Cómo medir
    if indicator and _has(text, "como mido", "como medir", "medir", "medicion", "tomar"):
        return INDICATORS[indicator]["como_medir"] + f"\n\n({DISCLAIMER})"

    # Pregunta sobre un indicador concreto
    if indicator:
        return _indicator_answer(indicator, ctx)

    # Ayuda de la app
    if _has(text, "registrar", "registro", "como uso", "como funciona", "semaforo", "grafica", "app", "ayuda"):
        return _app_help_answer(text)

    # Gamificación
    if _has(text, "racha", "puntos", "logro", "reto", "recordatorio", "tarea", "motiva"):
        return _gamification_answer(session, astronaut_id, ctx)

    # Fallback
    return (
        "Puedo ayudarte con:\n"
        "• Explicar un indicador (p. ej. «¿qué es la SpO2?») y cómo medirlo.\n"
        "• Decirte cómo estás y qué hacer si algo sale de rango.\n"
        "• Los 5 peligros del vuelo espacial.\n"
        "• Cómo usar la app y leer el semáforo.\n"
        "¿Sobre cuál quieres empezar?"
    )


# --------------------------------------------------------------------------- #
# Capa LLM opcional (redacta mejor, anclada a la KB y al contexto)
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = (
    "Eres el asistente de salud a bordo de una app que ayuda a astronautas en "
    "misiones largas a AUTOEVALUARSE. Hablas español, en tono cercano, claro y breve "
    "(2-5 frases). Reglas estrictas:\n"
    "1) Usa SOLO los HECHOS y el CONTEXTO que te doy; no inventes cifras, rangos ni "
    "diagnósticos. Si no está en los hechos, dilo y sugiere registrar datos.\n"
    "2) No eres consejo médico y los datos son sintéticos: no diagnostiques. Para "
    "estados en rojo o que persisten, recomienda reportar al oficial médico.\n"
    "3) No menciones marcas, logos ni identificadores de NASA.\n"
    "4) El objetivo es que el propio astronauta entienda y decida sus primeros pasos."
)


def llm_reply(message: str, facts: str, context_summary: str, history: Optional[list]) -> Optional[str]:
    """Intenta redactar con Claude. Devuelve None ante cualquier fallo (sin API key,
    sin internet, error de la API) para que el caller use la respuesta por reglas."""
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    user_block = (
        f"CONTEXTO DEL ASTRONAUTA (datos reales de la app):\n{context_summary}\n\n"
        f"HECHOS QUE PUEDES USAR (de nuestra base de conocimiento):\n{facts}\n\n"
        f"PREGUNTA DEL ASTRONAUTA:\n{message}\n\n"
        "Responde en español, breve, usando solo esos hechos y contexto."
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
        # Offline-first: cualquier error → se usa el núcleo por reglas.
        return None


def _facts_for(message: str, ctx: dict) -> str:
    """Selecciona los hechos de la KB relevantes para anclar al LLM."""
    text = _norm(message)
    chunks = []
    indicator = _detect_indicator(text)
    if indicator:
        info = INDICATORS[indicator]
        rule = THRESHOLDS[indicator]
        chunks.append(
            f"{LABELS[indicator]}: {info['que_es']} {info['espacio']} "
            f"Cómo medir: {info['como_medir']} "
            f"Rango normal: {rule['normal'][0]}-{rule['normal'][1]} {rule['unit']}."
        )
    if any(s in text for syns in HAZARD_SYNONYMS.values() for s in syns) or _has(text, "peligro", "riesgo"):
        chunks.append("Peligros HRP: " + " | ".join(HAZARDS.values()))
    if _has(text, "semaforo", "registrar", "app", "grafica", "color"):
        chunks.append(_app_help_answer(text))
    # Siempre incluimos la guía de acción base por si pregunta qué hacer.
    chunks.append(
        "Semáforo: verde=normal, amarillo=atención (repetir y vigilar), "
        "rojo=crítico (actuar y reportar al oficial médico)."
    )
    return "\n".join(chunks)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

class ChatRequest(BaseModel):
    message: str
    astronaut_id: str = "default"
    history: Optional[list] = None  # [{role: 'user'|'assistant', content: str}]


@router.post("")
def chat(payload: ChatRequest, session: Session = Depends(get_session)):
    ctx = build_context(session, payload.astronaut_id)

    # 1) Núcleo por reglas (siempre disponible, es el fallback).
    rule_reply = rule_based_reply(payload.message, session, payload.astronaut_id, ctx)

    # 2) Capa LLM opcional, anclada a los mismos hechos + contexto.
    facts = _facts_for(payload.message, ctx)
    context_summary = _context_summary_text(ctx)
    llm = llm_reply(payload.message, facts, context_summary, payload.history)

    reply = llm or rule_reply
    return {
        "reply": reply,
        "source": "llm" if llm else "reglas",
        "alerts": ctx["alerts"],
        "disclaimer": DISCLAIMER,
    }


@router.get("/status")
def status(astronaut_id: str = "default", session: Session = Depends(get_session)):
    """Saludo + alertas proactivas para que el widget avise al abrirse."""
    ctx = build_context(session, astronaut_id)
    if not ctx["has_data"]:
        greeting = (
            "¡Hola! Soy tu asistente de salud. Aún no registras mediciones hoy — "
            "ingresa tus indicadores y te ayudo a interpretarlos."
        )
    elif ctx["alerts"]:
        n = len(ctx["alerts"])
        greeting = f"Atención: {n} indicador(es) fuera de verde ({ctx['age_text']}). Pregúntame «¿qué hago?»."
    else:
        greeting = f"Todo en verde ✅ ({ctx['age_text']}). ¿En qué te ayudo?"
    return {
        "greeting": greeting,
        "alerts": ctx["alerts"],
        "quick_questions": QUICK_QUESTIONS,
        "disclaimer": DISCLAIMER,
        "llm_available": bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")),
    }
