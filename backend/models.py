"""Modelo de datos: astronautas, registros y esquemas de entrada/salida de la API.

Día de misión (convención del simulador): día 1 = día del lanzamiento, días previos −N…−1, no existe el día 0.
Fecha en UTC (la ISS usa GMT). Ver docs/decision_integracion_semaforo.md, sección 1.4.
"""
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as PField
from sqlalchemy import inspect
from sqlmodel import Field, Session, SQLModel, create_engine

from thresholds import INDICATORS

# la base vive junto al backend, sin importar desde qué carpeta se arranque uvicorn
DB_PATH = Path(__file__).resolve().parent / "health_records.db"
engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", echo=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(ts: datetime) -> datetime:
    """SQLite devuelve las fechas sin zona: se interpretan como UTC."""
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def mission_day_for(ts: datetime, launch_date: date) -> int:
    delta = (as_utc(ts).date() - launch_date).days
    return delta + 1 if delta >= 0 else delta


class Astronaut(SQLModel, table=True):
    astronaut_id: str = Field(primary_key=True)
    launch_date: date
    source: str = "manual"  # "manual" | "synthetic"


class HealthRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    astronaut_id: str = Field(default="default", index=True)
    timestamp: datetime = Field(default_factory=utcnow)
    mission_day: int
    source: str = "manual"  # "manual" | "sensor" | "synthetic"
    hr_rest: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    spo2: Optional[float] = None
    temp: Optional[float] = None
    glucose: Optional[float] = None
    sleep: Optional[float] = None
    mood: Optional[float] = None
    exercise: Optional[float] = None
    fitness: Optional[float] = None


def _range(k: str):
    lo, hi = INDICATORS[k]["input_range"]
    return PField(default=None, ge=lo, le=hi)


class HealthRecordCreate(BaseModel):
    """Entrada de POST /records. Todos los indicadores son opcionales, pero al menos uno es obligatorio.
    Los rangos son de plausibilidad (422 si se salen), no umbrales de alerta."""

    model_config = ConfigDict(extra="forbid")

    astronaut_id: str = PField(default="default", min_length=1, max_length=40)
    timestamp: Optional[datetime] = None  # por defecto, ahora en UTC
    source: Literal["manual", "sensor"] = "manual"  # "synthetic" solo lo usa seed_demo.py
    hr_rest: Optional[float] = _range("hr_rest")
    bp_sys: Optional[float] = _range("bp_sys")
    bp_dia: Optional[float] = _range("bp_dia")
    spo2: Optional[float] = _range("spo2")
    temp: Optional[float] = _range("temp")
    glucose: Optional[float] = _range("glucose")
    sleep: Optional[float] = _range("sleep")
    mood: Optional[float] = _range("mood")
    exercise: Optional[float] = _range("exercise")
    fitness: Optional[float] = _range("fitness")

    @model_validator(mode="after")
    def al_menos_un_indicador(self):
        if all(getattr(self, k) is None for k in INDICATORS):
            raise ValueError("Se requiere al menos un indicador.")
        return self


class HealthRecordRead(BaseModel):
    id: int
    astronaut_id: str
    timestamp: str  # ISO 8601 en UTC con «Z»
    mission_day: int
    source: str
    hr_rest: Optional[float] = None
    bp_sys: Optional[float] = None
    bp_dia: Optional[float] = None
    spo2: Optional[float] = None
    temp: Optional[float] = None
    glucose: Optional[float] = None
    sleep: Optional[float] = None
    mood: Optional[float] = None
    exercise: Optional[float] = None
    fitness: Optional[float] = None

    @classmethod
    def of(cls, r: HealthRecord) -> "HealthRecordRead":
        data = r.model_dump()
        data["timestamp"] = as_utc(r.timestamp).isoformat().replace("+00:00", "Z")
        return cls(**data)


def init_db(eng=None) -> None:
    eng = eng or engine
    insp = inspect(eng)
    if insp.has_table("healthrecord") and "mission_day" not in {c["name"] for c in insp.get_columns("healthrecord")}:
        raise RuntimeError(
            f"La base {DB_PATH} tiene el esquema viejo (sin día de misión). Solo tenía datos de prueba: "
            "bórrala y vuelve a arrancar el backend (en Windows: del backend\\health_records.db)."
        )
    SQLModel.metadata.create_all(eng)


def get_session():
    with Session(engine) as session:
        yield session
