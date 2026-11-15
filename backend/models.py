from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session

DATABASE_URL = "sqlite:///health_records.db"
engine = create_engine(DATABASE_URL, echo=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HealthRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    astronaut_id: str = "default"
    timestamp: datetime = Field(default_factory=utcnow)
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    spo2: Optional[float] = None
    body_temp: Optional[float] = None
    glucose: Optional[float] = None
    sleep_hours: Optional[float] = None
    mood: Optional[float] = None


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
