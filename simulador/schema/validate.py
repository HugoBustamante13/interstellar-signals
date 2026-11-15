#!/usr/bin/env python3
"""Valida out/mission_synthetic.json contra schema/mission_synthetic.schema.json (+ chequeos que JSON Schema no expresa).

Uso:  python3 schema/validate.py [ruta_json]
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "out" / "mission_synthetic.json"
schema = json.loads((HERE / "mission_synthetic.schema.json").read_text(encoding="utf-8"))
doc = json.loads(path.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
errors = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
for e in errors[:20]:
    print("ERROR esquema:", "/".join(map(str, e.path)), "->", e.message[:200])
extra = []
ids = {a["astronaut_id"] for a in doc["astronauts"]}
for it in doc["intraday_hr"]:
    n = it["n_days"] * (1440 // it["step_minutes"])
    if len(it["hr_bpm"]) != n or len(it["context"]) != n:
        extra.append(f"intraday {it['astronaut_id']}: longitud {len(it['hr_bpm'])} != {n}")
for an in doc["anomalies"]:
    if an["end_day"] < an["start_day"]:
        extra.append(f"{an['anomaly_id']}: end_day < start_day")
    if an["astronaut_id"] not in ids:
        extra.append(f"{an['anomaly_id']}: astronauta desconocido")
if any(r["astronaut_id"] not in ids for r in doc["daily"]):
    extra.append("daily con astronauta desconocido")
for m in extra[:20]:
    print("ERROR consistencia:", m)
ok = not errors and not extra
print(f"{'OK' if ok else 'FALLA'}: {path.name} | {len(doc['astronauts'])} astronautas, {len(doc['daily'])} filas, "
      f"{len(doc['anomalies'])} anomalias | data_origin={doc.get('data_origin')}")
sys.exit(0 if ok else 1)
