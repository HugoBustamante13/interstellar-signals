"""Pruebas del puente de la demo en vivo (/live). Uso: cd backend && venv/Scripts/python -m pytest -q"""
from fastapi.testclient import TestClient

import live
from main import app

client = TestClient(app)
LECTURA = {"astronaut": "Zamar", "values": {"spo2": 88}}


def test_sin_clave_las_escrituras_quedan_abiertas(monkeypatch):
    monkeypatch.setattr(live, "DEMO_KEY", "")
    assert client.post("/live", json=LECTURA).status_code == 200
    assert client.delete("/live").status_code == 200


def test_con_clave_se_exige_en_encabezado_o_en_la_url(monkeypatch):
    monkeypatch.setattr(live, "DEMO_KEY", "luna")
    assert client.post("/live", json=LECTURA).status_code == 401
    assert client.post("/live", json=LECTURA, headers={"X-Demo-Key": "sol"}).status_code == 401
    assert client.post("/live", json=LECTURA, headers={"X-Demo-Key": "luna"}).status_code == 200
    assert client.post("/live?k=luna", json=LECTURA).status_code == 200
    assert client.delete("/live").status_code == 401
    assert client.post("/live/context", json={}).status_code == 401
    # leer sigue abierto: la página del PC sondea sin clave
    assert client.get("/live").status_code == 200
    assert client.get("/live/context").status_code == 200


def test_valida_indicadores_rangos_y_senales(monkeypatch):
    monkeypatch.setattr(live, "DEMO_KEY", "")
    assert client.post("/live", json={"astronaut": "Zamar", "values": {"spo2": 120}}).status_code == 422
    assert client.post("/live", json={"astronaut": "Zamar", "values": {"xyz": 1}}).status_code == 422
    assert client.post("/live", json={"astronaut": "Zamar", "symptoms": ["fiebre"]}).status_code == 422
    assert client.post("/live", json={"astronaut": "Zamar"}).status_code == 422


def test_la_ultima_lectura_llega_una_sola_vez_por_secuencia(monkeypatch):
    monkeypatch.setattr(live, "DEMO_KEY", "")
    seq = client.post("/live", json=LECTURA).json()["seq"]
    assert client.get(f"/live?since={seq - 1}").json()["reading"]["values"] == {"spo2": 88.0}
    assert client.get(f"/live?since={seq}").json()["reading"] is None
