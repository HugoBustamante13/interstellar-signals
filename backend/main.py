"""API del monitor de salud. Contrato: docs/decision_integracion_semaforo.md, sección 5.

El color (verde / amarillo / rojo) lo calcula el semáforo del simulador vía semaforo_bridge.py.
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

import live
from models import (Astronaut, HealthRecord, HealthRecordCreate, HealthRecordRead, as_utc, get_session, init_db,
                    mission_day_for, utcnow)
from semaforo_bridge import compute_series, compute_status, indicators_meta
from thresholds import INDICATORS


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
    """Metadatos de cada indicador y sus límites absolutos (leídos de semaforo_config.json)."""
    return indicators_meta()


@app.get("/astronauts")
def list_astronauts(session: Session = Depends(get_session)):
    now = utcnow()
    rows = session.exec(select(Astronaut).order_by(Astronaut.astronaut_id)).all()
    return [{"astronaut_id": a.astronaut_id, "launch_date": a.launch_date.isoformat(), "source": a.source,
             "current_mission_day": mission_day_for(now, a.launch_date)} for a in rows]


@app.post("/records", status_code=201)
def create_record(payload: HealthRecordCreate, session: Session = Depends(get_session)):
    astro = session.get(Astronaut, payload.astronaut_id)
    if astro is None:  # astronauta nuevo: su día 1 es hoy (UTC)
        astro = Astronaut(astronaut_id=payload.astronaut_id, launch_date=utcnow().date(), source="manual")
        session.add(astro)
    ts = as_utc(payload.timestamp) if payload.timestamp else utcnow()
    record = HealthRecord(**payload.model_dump(exclude={"timestamp"}), timestamp=ts,
                          mission_day=mission_day_for(ts, astro.launch_date))
    session.add(record)
    session.commit()
    session.refresh(record)
    return {"record": HealthRecordRead.of(record), "status": compute_status(session, payload.astronaut_id)}


@app.get("/records")
def list_records(astronaut_id: str = "default", session: Session = Depends(get_session)):
    q = select(HealthRecord).where(HealthRecord.astronaut_id == astronaut_id).order_by(HealthRecord.timestamp)
    return [HealthRecordRead.of(r) for r in session.exec(q).all()]


@app.get("/status")
def get_status(astronaut_id: str = "default", session: Session = Depends(get_session)):
    status = compute_status(session, astronaut_id)
    if status is None:
        raise HTTPException(404, f"No hay registros de {astronaut_id}.")
    return status


@app.get("/series")
def get_series(astronaut_id: str = "default", indicator: str = Query(...), session: Session = Depends(get_session)):
    if indicator not in INDICATORS:
        raise HTTPException(422, f"Indicador desconocido: {indicator}")
    series = compute_series(session, astronaut_id, indicator)
    if series is None:
        raise HTTPException(404, f"No hay registros de {astronaut_id}.")
    return series
