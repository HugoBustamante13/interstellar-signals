"""Carga la misión sintética del simulador como datos de demostración (días −30…180).

Uso: cd backend && python seed_demo.py [carpeta del simulador; por defecto ../simulador/out, 4 astronautas]

- launch_date = hoy (UTC) − 179 días: el día 180 es hoy, así una entrada manual cae sobre una historia completa
  (la mejor forma de ver la banda personal). Cada día queda a las 08:30 UTC; el de hoy, antes de la hora actual,
  para que una lectura manual posterior sea siempre la última del día.
- Solo lee los indicadores, astronaut_id y mission_day. Las demás columnas del CSV (las de evaluación del
  simulador, quality_flags, sex, phase, data_origin) no se cargan: son para evaluar, nunca para el producto.
- Es idempotente: borra los registros sintéticos y los astronautas SIM-* antes de insertar.
TODOS LOS DATOS SON SINTÉTICOS.
"""
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import delete
from sqlmodel import Session

from models import Astronaut, HealthRecord, engine, init_db, mission_day_for, utcnow
from semaforo_bridge import COLS

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "simulador" / "out"


def seed(session: Session, sim_dir: Path = DEFAULT_DIR, now: datetime | None = None) -> int:
    now = now or utcnow()
    launch = now.date() - timedelta(days=179)
    df = pd.read_csv(Path(sim_dir) / "mission_synthetic_daily.csv", usecols=["astronaut_id", "mission_day", *COLS.values()])
    session.execute(delete(HealthRecord).where(HealthRecord.source == "synthetic"))
    session.execute(delete(Astronaut).where(Astronaut.astronaut_id.like("SIM-%")))
    for aid in df["astronaut_id"].unique():
        session.add(Astronaut(astronaut_id=str(aid), launch_date=launch, source="synthetic"))
    rows = []
    for r in df.itertuples(index=False):
        d = int(r.mission_day)
        day = launch + timedelta(days=d - 1 if d > 0 else d)
        ts = datetime.combine(day, time(8, 30), tzinfo=timezone.utc)
        ts = max(datetime.combine(day, time(0, 0, 1), tzinfo=timezone.utc), min(ts, now - timedelta(minutes=1)))
        assert mission_day_for(ts, launch) == d, (d, ts)
        values = {k: None if pd.isna(getattr(r, col)) else float(getattr(r, col)) for k, col in COLS.items()}
        rows.append(HealthRecord(astronaut_id=str(r.astronaut_id), timestamp=ts, mission_day=d, source="synthetic", **values))
    session.add_all(rows)
    session.commit()
    return len(rows)


def main() -> None:
    init_db()
    sim_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    with Session(engine) as s:
        n = seed(s, sim_dir)
    print(f"Listo: {n} registros sintéticos cargados desde {sim_dir} (día 180 = hoy).")


if __name__ == "__main__":
    main()
