"""Puente de la demo en vivo: el celular (simulador de camisa, reloj y entradas
manuales) envía una lectura y la web la recoge por sondeo.

Todo vive en memoria: es para la demostración, no se guarda en la base de datos.
Los datos que pasan por aquí son SIMULADOS; no vienen de sensores reales.
"""
import math
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models import utcnow

router = APIRouter(prefix="/live", tags=["demo en vivo"])

# nombres canónicos (los del simulador) y rango aceptado para cada uno
RANGES = {
    "hr_rest": (20, 250),
    "spo2": (50, 100),
    "temp": (30, 45),
    "sleep": (0, 24),
    "bp_sys": (40, 300),
    "bp_dia": (20, 200),
    "glucose": (10, 600),
    "mood": (1, 5),
    "exercise": (0, 600),
    # informativos: llegan a la web pero el semáforo todavía no los evalúa
    "resp": (4, 60),
    "light": (0, 100000),
}
SYMPTOMS = {"piel", "boca", "resp", "herida"}

_state = {"seq": 0, "reading": None, "context": None}


class Ultrasound(BaseModel):
    """Resultado de una ecografía. La app no interpreta imágenes: solo registra lo que anota quien la hace."""

    exam: Literal["corazon", "vasos", "abdomen", "ojo"]
    result: Literal["sin_hallazgos", "hallazgo", "repetir"]


class LiveReading(BaseModel):
    astronaut: str = Field(min_length=1, max_length=40)
    values: dict[str, float] = {}
    symptoms: list[str] = []
    scenario: Optional[str] = Field(default=None, max_length=60)
    ultrasound: Optional[Ultrasound] = None


class LiveContext(BaseModel):
    """Lo que la web le cuenta al control: quiénes hay y cuál es su línea base hoy."""

    day: Optional[str] = Field(default=None, max_length=20)
    selected: Optional[str] = Field(default=None, max_length=40)
    astronauts: dict[str, dict[str, Optional[float]]] = {}


@router.post("")
def send_reading(payload: LiveReading):
    if not payload.values and not payload.symptoms and not payload.ultrasound:
        raise HTTPException(422, "Envía al menos un valor, una señal o una ecografía.")
    for key, value in payload.values.items():
        if key not in RANGES:
            raise HTTPException(422, f"Indicador desconocido: {key}")
        lo, hi = RANGES[key]
        if not math.isfinite(value) or not lo <= value <= hi:
            raise HTTPException(422, f"{key} fuera de rango ({lo}–{hi}).")
    unknown = set(payload.symptoms) - SYMPTOMS
    if unknown:
        raise HTTPException(422, f"Señal desconocida: {', '.join(sorted(unknown))}")
    _state["seq"] += 1
    _state["reading"] = {**payload.model_dump(), "seq": _state["seq"], "received_at": utcnow()}
    return {"seq": _state["seq"]}


@router.get("")
def latest_reading(since: int = 0):
    """Devuelve la última lectura si es más nueva que `since`; si no, solo el número de secuencia."""
    if _state["reading"] and _state["seq"] > since:
        return {"seq": _state["seq"], "reading": _state["reading"]}
    return {"seq": _state["seq"], "reading": None}


@router.delete("")
def clear_reading():
    """El control pide volver a los datos simulados de la misión."""
    _state["seq"] += 1
    _state["reading"] = {"cleared": True, "seq": _state["seq"]}
    return {"seq": _state["seq"]}


@router.post("/context")
def set_context(payload: LiveContext):
    _state["context"] = payload.model_dump()
    return {"ok": True}


@router.get("/context")
def get_context():
    return _state["context"]


PROTOTIPO_DIR = Path(__file__).resolve().parent.parent / "prototipo"
