"""Une mission_synthetic_daily.csv + mission_synthetic_semaforo.csv en un JSON compacto
para el prototipo. Descarta truth_* (solo para evaluar, nunca en el producto)."""
import json, math, sys
from pathlib import Path
import pandas as pd

SIM = Path(sys.argv[1])          # carpeta de salida del simulador (p. ej. simulador/out_2astronautas)
OUT = Path(sys.argv[2])
# nombres de demostración para los ids sintéticos: "SIM-001=Zamar,SIM-002=Carlos"
NAMES = dict(p.split("=") for p in sys.argv[3].split(",")) if len(sys.argv) > 3 else {}
d = pd.read_csv(SIM / "mission_synthetic_daily.csv")
s = pd.read_csv(SIM / "mission_synthetic_semaforo.csv")
d = d[[c for c in d.columns if not c.startswith("truth_")]]
m = d.merge(s, on=["astronaut_id", "mission_day"], suffixes=("", "_s"))

VAL = {"hr_rest": ("hr_rest_bpm", 1), "bp_sys": ("bp_sys_mmhg", 0), "bp_dia": ("bp_dia_mmhg", 0),
       "spo2": ("spo2_pct", 1), "temp": ("temp_c", 2), "glucose": ("glucose_mgdl", 0),
       "sleep": ("sleep_h", 2), "mood": ("mood_1_5", 1), "exercise": ("exercise_min", 0),
       "fitness": ("fitness_pct_preflight", 1)}
BANDED = ["hr_rest", "bp_sys", "bp_dia", "spo2", "temp", "sleep", "mood"]


def clean(v, nd):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return round(float(v), nd)


out = {}
for aid, g in m.sort_values("mission_day").groupby("astronaut_id"):
    a = {"sex": g.sex.iloc[0], "day": g.mission_day.astype(int).tolist(),
         "status": g.status.astype(int).tolist(),
         "flags": [None if pd.isna(x) else x for x in g.quality_flags]}
    for k, (col, nd) in VAL.items():
        a[k] = [clean(v, nd) for v in g[col]]
        sc = f"status_{k}"
        if sc in g:
            a["s_" + k] = g[sc].astype(int).tolist()
    for k in BANDED:
        nd = VAL[k][1] + 1
        for p in ("base", "lo", "hi"):
            a[f"{p}_{k}"] = [clean(v, nd) for v in g[f"{p}_{k}"]]
    a["sim_id"] = aid
    out[NAMES.get(aid, aid)] = a

OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(OUT, OUT.stat().st_size, "bytes")
# días interesantes para abrir el prototipo
for aid, a in out.items():
    reds = [a["day"][i] for i, st in enumerate(a["status"]) if st == 2]
    print(aid, "rojos en día:", reds)
