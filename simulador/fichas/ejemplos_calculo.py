"""Ejemplos numericos de las fichas (DATOS SINTETICOS). Recalcula a mano la banda personal y la compara con semaforo.py.
Uso: python3 fichas/ejemplos_calculo.py   (desde la raiz del paquete)"""
import sys, json, math
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))
import semaforo as sf

cfg = sf.Config(ROOT / "sim" / "semaforo_config.json")
d = pd.read_csv(ROOT / "out" / "mission_synthetic_daily.csv")
res = sf.run_semaforo(d, cfg, return_bands=True, return_reasons=True)
W, band = int(cfg("general.baseline_window_days")), float(cfg("general.band_sd"))
out = {}
COL = {"hr_rest": "hr_rest_bpm", "bp_sys": "bp_sys_mmhg", "bp_dia": "bp_dia_mmhg", "spo2": "spo2_pct", "temp": "temp_c",
       "sleep": "sleep_h", "mood": "mood_1_5", "glucose": "glucose_mgdl"}
def ejemplo(k, aid, day):
    s = d[d.astronaut_id == aid].set_index("mission_day")[COL[k]]
    win = s.loc[day - W:day - 1].dropna()
    n, m, sd = len(win), win.mean(), win.std(ddof=1)
    sd_eff = max(sd * math.sqrt(1 + 1 / n), cfg(f"sd_floor.{k}"))
    lo, hi = m - band * sd_eff, m + band * sd_eff
    r = res[(res.astronaut_id == aid) & (res.mission_day == day)].iloc[0]
    ok = (abs(r[f"base_{k}"] - m) < 1e-9) if n >= int(cfg("general.min_window_points")) else None
    return dict(astronauta=aid, dia=day, lectura=float(s.loc[day]) if not np.isnan(s.loc[day]) else None, n_ventana=n,
                media=round(m, 2), de=round(sd, 2), de_prediccion=round(sd * math.sqrt(1 + 1 / n), 2),
                banda_baja=round(lo, 2), banda_alta=round(hi, 2),
                coincide_con_semaforo_py=bool(ok) if ok is not None else "ventana insuficiente",
                banda_semaforo_py=[None if np.isnan(r[f"lo_{k}"]) else round(float(r[f"lo_{k}"]), 2), None if np.isnan(r[f"hi_{k}"]) else round(float(r[f"hi_{k}"]), 2)])
for k in ["hr_rest", "bp_sys", "bp_dia", "spo2", "temp", "sleep", "mood"]:
    out[k] = ejemplo(k, "SIM-001", 60)
# ejercicio: ventana de 7 dias con amarillo (primer cambio de verde a amarillo en SIM-002)
ex = res[res.astronaut_id == "SIM-002"].set_index("mission_day")["status_exercise"]
first = int(ex[(ex == 1) & (ex.shift(1, fill_value=0) == 0)].index[0])
mins = d[d.astronaut_id == "SIM-002"].set_index("mission_day")["exercise_min"].loc[first - 6:first]
out["exercise"] = dict(astronauta="SIM-002", dia=first, minutos_7_dias=[float(x) for x in mins.fillna(0).values],
                       sesiones_hechas=int((mins.fillna(0) >= cfg("yellow_extra.exercise_session_min_done")).sum()),
                       minimo_sesiones=int(cfg("yellow_extra.exercise_min_sessions_week")), estado=int(ex.loc[first]))
# aptitud: dia de prueba mas bajo
ft = d.dropna(subset=["fitness_pct_preflight"])
low = ft.sort_values("fitness_pct_preflight").iloc[0]
out["fitness"] = dict(astronauta=low.astronaut_id, dia=int(low.mission_day), aptitud_pct=float(low.fitness_pct_preflight), limite_rojo=cfg("absolute_red.fitness_lt_pct"))
# glucosa: lecturas en la ventana de 28 dias
g = d[d.astronaut_id == "SIM-001"].set_index("mission_day")["glucose_mgdl"].loc[32:59].dropna()
out["glucose_ventana"] = dict(n_lecturas_en_28_dias=len(g), minimo_requerido=int(cfg("general.min_window_points")))
# temperatura: reglas absolutas
t = d[(d.mission_day > 14)].groupby("astronaut_id").temp_c.agg(["mean", "max"]).round(2)
out["temp_vuelo_por_astronauta"] = t.to_dict("index")
print(json.dumps(out, indent=1, ensure_ascii=False, default=float))
