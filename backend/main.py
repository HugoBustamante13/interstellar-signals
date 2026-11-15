from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from models import HealthRecord, init_db, get_session, utcnow
from thresholds import THRESHOLDS, evaluate, get_recommendation
import live

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Astronaut Health Monitoring API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo en vivo: el celular envía lecturas simuladas y la web las recoge.
# /demo/ sirve el prototipo y /demo/control.html la página de control del celular.
app.include_router(live.router)
if live.PROTOTIPO_DIR.is_dir():
    app.mount("/demo", StaticFiles(directory=live.PROTOTIPO_DIR, html=True), name="demo")


@app.get("/indicators")
def list_indicators():
    """Devuelve la configuración de indicadores (rangos) para que el frontend
    pueda renderizar formularios y leyendas de color."""
    return THRESHOLDS


class HealthRecordCreate(BaseModel):
    """Entrada de POST /records: sin id ni timestamp (los fija el servidor)."""

    astronaut_id: str = "default"
    heart_rate: Optional[float] = Field(default=None, ge=0)
    systolic_bp: Optional[float] = Field(default=None, ge=0)
    spo2: Optional[float] = Field(default=None, ge=0)
    body_temp: Optional[float] = None
    glucose: Optional[float] = Field(default=None, ge=0)
    sleep_hours: Optional[float] = Field(default=None, ge=0)
    mood: Optional[float] = None


@app.post("/records")
def create_record(
    payload: HealthRecordCreate, session: Session = Depends(get_session)
):
    if all(getattr(payload, f) is None for f in THRESHOLDS):
        raise HTTPException(
            status_code=422, detail="Se requiere al menos un indicador."
        )
    record = HealthRecord(**payload.model_dump(), timestamp=utcnow())
    session.add(record)
    session.commit()
    session.refresh(record)
    return assess_record(record)


@app.get("/records")
def list_records(
    astronaut_id: str = "default", session: Session = Depends(get_session)
):
    statement = (
        select(HealthRecord)
        .where(HealthRecord.astronaut_id == astronaut_id)
        .order_by(HealthRecord.timestamp)
    )
    return [serialize(r) for r in session.exec(statement).all()]


@app.get("/records/latest")
def latest_record(astronaut_id: str = "default", session: Session = Depends(get_session)):
    statement = (
        select(HealthRecord)
        .where(HealthRecord.astronaut_id == astronaut_id)
        .order_by(HealthRecord.timestamp.desc())
    )
    record = session.exec(statement).first()
    if not record:
        return None
    return assess_record(record)


def serialize(record: HealthRecord) -> dict:
    """model_dump con timestamp en UTC con offset (SQLite lo devuelve sin zona)."""
    data = record.model_dump()
    ts = data["timestamp"]
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    data["timestamp"] = ts.astimezone(timezone.utc)
    return data


def assess_record(record: HealthRecord):
    """Agrega status + recomendación por cada indicador presente en el registro."""
    result = serialize(record)
    assessment = {}
    for field in THRESHOLDS:
        value = getattr(record, field, None)
        if value is None:
            continue
        status = evaluate(field, value)
        assessment[field] = {
            "value": value,
            "status": status,
            "recommendation": get_recommendation(field, status),
        }
    result["assessment"] = assessment
    return result
