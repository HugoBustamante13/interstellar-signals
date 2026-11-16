"""Pruebas del puente con el semáforo del simulador y de la API (plan de docs/decision_integracion_semaforo.md, paso 6).

Uso: cd backend && venv\\Scripts\\python -m pip install -r requirements-dev.txt && venv\\Scripts\\python -m pytest -q
Cada prueba usa una base SQLite en memoria con la misión sintética cargada (seed_demo.seed).
"""
import re
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

import semaforo_bridge as sb
from main import app
from models import Astronaut, get_session, init_db, utcnow
from seed_demo import seed

ROOT = Path(__file__).resolve().parents[1]
CODE = {"normal": 0, "attention": 1, "critical": 2}
SIMS = ["SIM-001", "SIM-002", "SIM-003", "SIM-004"]


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    init_db(eng)
    with Session(eng) as s:
        seed(s)
    return eng


@pytest.fixture()
def client(engine):
    def override():
        with Session(engine) as s:
            yield s
    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def sim_csv():
    return pd.read_csv(ROOT / "simulador" / "out" / "mission_synthetic_semaforo.csv")


# (a) lo que corre en la app es lo que se evaluó en el simulador
def test_a_coincide_con_el_simulador_el_dia_180(engine, sim_csv):
    row = sim_csv[(sim_csv.astronaut_id == "SIM-001") & (sim_csv.mission_day == 180)].iloc[0]
    with Session(engine) as s:
        st = sb.compute_status(s, "SIM-001")
    assert st["mission_day"] == 180 and st["data_origin"] == "synthetic" and st["evaluation_mode"] == "linea_base"
    for k in sb.KEYS:
        if k != "glucose":
            assert CODE.get(st["indicators"][k]["status"], 0) == int(row[f"status_{k}"]), k


def test_a_coincide_con_el_simulador_en_toda_la_mision(engine, sim_csv):
    with Session(engine) as s:
        for aid in SIMS:
            d, res = sb._status_frame(sb.build_daily(sb._records(s, aid), aid))
            ref = sim_csv[sim_csv.astronaut_id == aid].set_index("mission_day")
            for k in sb.KEYS:
                if k == "glucose":
                    continue
                got, want = res.loc[res.index > 0, f"status_{k}"], ref.loc[ref.index > 0, f"status_{k}"]
                assert (got.to_numpy() == want.to_numpy()).all(), (aid, k)
            assert (res.loc[res.index > 0, "status"].to_numpy() == ref.loc[ref.index > 0, "status"].to_numpy()).all(), aid


# (b) astronauta nuevo: solo límites clínicos
def test_b_astronauta_nuevo_solo_limites_clinicos(client):
    r = client.post("/records", json={"astronaut_id": "nuevo", "spo2": 88, "sleep": 4})
    assert r.status_code == 201
    st = r.json()["status"]
    assert st["mission_day"] == 1 and st["evaluation_mode"] == "adaptacion_inicial" and st["data_origin"] == "manual"
    assert st["indicators"]["spo2"]["status"] == "critical"
    assert st["indicators"]["spo2"]["reason"]["code"] == "limite_clinico"
    assert st["indicators"]["sleep"]["status"] == "normal"
    assert st["indicators"]["sleep"]["reason"]["code"] == "sin_linea_base"
    assert st["indicators"]["glucose"]["status"] is None


# (c) prevuelo: límites absolutos, temperatura con 38,0 °C
def test_c_prevuelo_temperatura(client, engine):
    with Session(engine) as s:
        s.add(Astronaut(astronaut_id="pre", launch_date=utcnow().date() + timedelta(days=10), source="manual"))
        s.commit()
    st = client.post("/records", json={"astronaut_id": "pre", "temp": 38.3}).json()["status"]
    assert st["mission_day"] == -10 and st["phase"] == "preflight" and st["evaluation_mode"] == "prevuelo"
    assert st["indicators"]["temp"]["status"] == "critical" and st["overall"]["status"] == "critical"


# (d) el backend nunca lee las columnas de evaluación del simulador
def test_d_el_backend_no_usa_columnas_de_evaluacion():
    pattern = re.compile("tru" + "th_|latent_" + "truth")
    for f in Path(__file__).parent.glob("*.py"):
        assert not pattern.search(f.read_text(encoding="utf-8")), f.name


def test_indicadores_leen_la_config(client):
    j = client.get("/indicators").json()
    assert j["hr_rest"]["absolute"]["red_gt"] == 100 and j["hr_rest"]["absolute"]["yellow_lt"] == 50
    assert j["temp"]["absolute"]["red_gt"] == 38.0 and j["temp"]["absolute"]["red_gt_inflight"] == 38.5
    assert j["glucose"]["in_semaforo"] is False and j["glucose"]["absolute"]["red_lt"] == 54
    assert j["fitness"]["absolute"]["red_lt"] == 80
    assert j["_meta"]["absolute_only_first_days"] == 14


def test_validacion_de_entrada(client):
    assert client.post("/records", json={"spo2": 120}).status_code == 422
    assert client.post("/records", json={"heart_rate": 70}).status_code == 422  # nombre viejo: ya no existe
    assert client.post("/records", json={"astronaut_id": "x"}).status_code == 422  # sin indicadores
    assert client.post("/records", json={"hr_rest": 70, "source": "synthetic"}).status_code == 422


def test_astronautas_series_y_404(client):
    sims = [a for a in client.get("/astronauts").json() if a["astronaut_id"].startswith("SIM-")]
    assert len(sims) == 4 and all(a["current_mission_day"] == 180 and a["source"] == "synthetic" for a in sims)
    s = client.get("/series", params={"astronaut_id": "SIM-001", "indicator": "bp_sys"}).json()
    assert len(s) == 210 and s[0]["mission_day"] == -30 and s[-1]["mission_day"] == 180
    assert all(p["mission_day"] != 0 for p in s)
    assert any(p["lo"] is not None and p["hi"] is not None for p in s)
    assert client.get("/series", params={"astronaut_id": "SIM-001", "indicator": "xyz"}).status_code == 422
    assert client.get("/status", params={"astronaut_id": "nadie"}).status_code == 404


def test_entrada_manual_cae_sobre_la_historia(client):
    j = client.post("/records", json={"astronaut_id": "SIM-001", "bp_sys": 190}).json()
    assert j["record"]["mission_day"] == 180 and j["record"]["timestamp"].endswith("Z")
    bp = j["status"]["indicators"]["bp_sys"]
    assert bp["value"] == 190 and bp["status"] == "critical" and bp["reason"]["code"] == "limite_clinico"
    assert bp["baseline"]["ready"] is True and bp["recommendation"]
    assert j["status"]["overall"]["status"] == "critical"
