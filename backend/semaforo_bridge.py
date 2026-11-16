"""Puente entre la app y el semáforo del simulador.

El backend IMPORTA simulador/sim/semaforo.py tal cual (no lo copia ni lo mueve): lo que se evaluó en las
misiones simuladas es exactamente lo que corre en la app. Ver docs/decision_integracion_semaforo.md, 1.1–1.6.
Solo usa los valores registrados: nunca las columnas de evaluación del simulador ni quality_flags.

Vocabulario de estado en la API: "normal" | "attention" | "critical" (0/1/2 del simulador); la interfaz
muestra «Verde / Amarillo / Rojo». None = sin datos.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlmodel import Session, select

SIM_DIR = Path(__file__).resolve().parents[1] / "simulador" / "sim"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
import semaforo as sf  # noqa: E402  (vive en simulador/sim; lo usan también simulator.py y evaluate.py)

from models import Astronaut, HealthRecord  # noqa: E402
from thresholds import INDICATORS, STATUS_BY_CODE, get_recommendation  # noqa: E402

CFG = sf.Config()  # lee simulador/sim/semaforo_config.json
COLS = {**sf.IND, "exercise": "exercise_min", "fitness": "fitness_pct_preflight"}  # clave canónica → columna del simulador
KEYS = list(INDICATORS)
BANDED = [k for k in sf.IND if k != "glucose" or CFG("mvp.include_glucose")]  # los que tienen línea base personal
EARLY = int(CFG("general.absolute_only_first_days"))


def cfg(key, default=None):
    try:
        return CFG(key)
    except KeyError:
        return default


# ---------- límites absolutos (desde la config, sin copiarlos) ----------
def absolute_limits(k: str) -> dict:
    if k == "glucose":
        return {"red_gt": cfg("absolute_red.glucose_gt"), "red_lt": cfg("absolute_red.glucose_lt"),
                "yellow_gt": cfg("yellow_extra.glucose_yellow_high"), "yellow_lt": cfg("yellow_extra.glucose_yellow_low")}
    lim = {"red_gt": cfg(f"absolute_red.{k}_gt"), "red_lt": cfg(f"absolute_red.{k}_lt"),
           "yellow_lt": cfg(f"absolute_yellow.{k}_lt"), "red_gt_inflight": None}
    if k == "fitness":
        lim["red_lt"] = cfg("absolute_red.fitness_lt_pct")
    if k == "temp":
        lim["red_gt_inflight"] = cfg("absolute_red.temp_gt_inflight")
        lim["inflight_consecutive_days"] = cfg("absolute_red.temp_inflight_consecutive_days", 1)
    return lim


def indicators_meta() -> dict:
    """Respuesta de GET /indicators: metadatos de thresholds.py + límites absolutos de la config."""
    out = {k: {**{f: (list(v) if f == "input_range" else v) for f, v in meta.items()}, "absolute": absolute_limits(k)}
           for k, meta in INDICATORS.items()}
    out["_meta"] = {"absolute_only_first_days": EARLY, "min_window_points": int(CFG("general.min_window_points")),
                    "baseline_window_days": int(CFG("general.baseline_window_days"))}
    return out


def glucose_code(x: float) -> int:
    """Glucosa en ayunas (ADA 2026, valores de la config): no entra al semáforo con línea base."""
    L = absolute_limits("glucose")
    if x < L["red_lt"] or x >= L["red_gt"]:
        return 2
    if x < L["yellow_lt"] or x >= L["yellow_gt"]:
        return 1
    return 0


def absolute_code(k: str, x: float, day: int) -> int:
    """Solo límites absolutos, sin línea base (prevuelo). Temperatura: 38,0 °C en prevuelo y días 1–14, el límite
    de vuelo después; amarillos inferiores (FC < 50) solo en vuelo, como en el simulador."""
    if k == "glucose":
        return glucose_code(x)
    L = absolute_limits(k)
    gt = L["red_gt_inflight"] if k == "temp" and day > EARLY else L["red_gt"]
    if gt is not None and x > gt:
        return 2
    if L["red_lt"] is not None and x < L["red_lt"]:
        return 2
    if L["yellow_lt"] is not None and day > 0 and x < L["yellow_lt"]:
        return 1
    return 0


# ---------- de los registros al día a día del simulador ----------
def build_daily(records: list[HealthRecord], astronaut_id: str) -> pd.DataFrame:
    """Pasos 2–4 de 1.5: última lectura no nula del día por indicador; días continuos sin el 0; columnas del simulador."""
    df = pd.DataFrame([{"timestamp": r.timestamp, "mission_day": r.mission_day, **{k: getattr(r, k) for k in KEYS}}
                       for r in records])
    df[KEYS] = df[KEYS].astype(float)
    daily = df.sort_values("timestamp", kind="stable").groupby("mission_day")[KEYS].last()
    lo, hi = int(daily.index.min()), int(daily.index.max())
    days = pd.Index([d for d in range(lo, hi + 1) if d != 0], name="mission_day")  # run_semaforo cuenta por posición
    daily = daily.reindex(days).rename(columns=COLS).reset_index()
    daily.insert(0, "astronaut_id", astronaut_id)
    return daily


def _carry(values, fn) -> list[int]:
    """Estado por día con arrastre: un día sin lectura conserva el estado anterior (regla del simulador)."""
    prev, out = 0, []
    for day, x in values.items():
        prev = fn(x, day) if not math.isnan(x) else prev
        out.append(prev)
    return out


def _status_frame(daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(valores, estados) por día. Estados: status_<k>, status (global del semáforo), n_yellow, overall y bandas."""
    d = daily.set_index("mission_day")
    if (d.index > 0).any():
        res = sf.run_semaforo(daily, CFG, return_bands=True, return_reasons=False).set_index("mission_day")
    else:
        res = pd.DataFrame(index=d.index)
        res["status"], res["n_yellow"] = 0, 0
        for k in KEYS:
            if k != "glucose":
                res[f"status_{k}"] = 0
        for k in BANDED:
            for p in ("base", "lo", "hi"):
                res[f"{p}_{k}"] = np.nan
    res = res.copy()
    pre = res.index < 0
    if pre.any():  # el simulador no evalúa días previos: aquí solo límites absolutos
        for k in KEYS:
            if k != "glucose":
                res.loc[pre, f"status_{k}"] = _carry(d.loc[pre, COLS[k]], lambda x, day, k=k: absolute_code(k, x, day))
        res.loc[pre, "status"] = res.loc[pre, [f"status_{k}" for k in KEYS if k != "glucose"]].max(axis=1)
        res.loc[pre, "n_yellow"] = 0
    # glucosa aparte: cuenta para el global con max(), pero no para «dos amarillos = rojo»
    res["status_glucose"] = _carry(d[COLS["glucose"]], lambda x, day: glucose_code(x))
    res["overall"] = np.maximum(res["status"].to_numpy(), res["status_glucose"].to_numpy())
    return d, res


# ---------- motivos (1.6) ----------
def _num(v, nd: int = 2):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), nd)


def _fmt(v, nd: int | None = None) -> str:
    v = float(v)
    s = f"{v:.{nd}f}" if nd is not None else (f"{v:.0f}" if abs(v - round(v)) < 1e-9 else f"{v:.1f}")
    return s.replace(".", ",")


def _violated(k: str, x: float, day: int):
    """(operador, límite) del límite absoluto rojo que el valor supera, o None."""
    L = absolute_limits(k)
    if k == "glucose":
        return ("<", L["red_lt"]) if x < L["red_lt"] else ("≥", L["red_gt"]) if x >= L["red_gt"] else None
    gt = L["red_gt_inflight"] if k == "temp" and day > EARLY else L["red_gt"]
    if gt is not None and x > gt:
        return (">", gt)
    if L["red_lt"] is not None and x < L["red_lt"]:
        return ("<", L["red_lt"])
    return None


def _days_out(d: pd.DataFrame, res: pd.DataFrame, k: str, until: int) -> int:
    """Lecturas seguidas (hacia atrás desde `until`) fuera de [lo, hi]; ignora el lado de la banda que sea NaN."""
    n = 0
    for day in reversed([x for x in d.index if x <= until]):
        v = d.at[day, COLS[k]]
        if math.isnan(v):
            continue
        lo, hi = res.at[day, f"lo_{k}"], res.at[day, f"hi_{k}"]
        if (not math.isnan(lo) and v < lo) or (not math.isnan(hi) and v > hi):
            n += 1
        else:
            break
    return n


def _sessions_7d(d: pd.DataFrame, day: int) -> int:
    pos = d.index.get_loc(day)
    w = d.iloc[max(0, pos - 6): pos + 1]
    w = w[w.index > 0]
    return int((w["exercise_min"].fillna(0) >= CFG("yellow_extra.exercise_session_min_done")).sum())


def _reason(k, code, value, vday, day, baseline, d, res):
    label, unit = INDICATORS[k]["label"], INDICATORS[k]["unit"]
    if code == 2:
        if k == "fitness":
            return {"code": "aptitud_baja", "text": f"Aptitud física {_fmt(value)} % de la previa (mínimo {_fmt(CFG('absolute_red.fitness_lt_pct'))} %)"}
        hit = _violated(k, value, vday)
        if hit:
            op, lim = hit
            return {"code": "limite_clinico", "text": f"Límite clínico: {label} {_fmt(value)} {unit} (límite {op} {_fmt(lim, 1 if k == 'temp' else None)})"}
        return {"code": "salto_confirmado", "text": "Cambio brusco respecto a tu línea base, confirmado al día siguiente"}
    if code == 1:
        yl = absolute_limits(k).get("yellow_lt")
        if k != "glucose" and yl is not None and vday > 0 and value < yl:
            text = f"FC en reposo bajo {_fmt(yl)} lpm (bradicardia)" if k == "hr_rest" else f"{label} bajo {_fmt(yl)} {unit}"
            return {"code": "limite_clinico_bajo", "text": text}
        if k == "spo2" and baseline and baseline["mean"] is not None and baseline["mean"] - value >= CFG("yellow_extra.spo2_drop_points"):
            return {"code": "caida_spo2", "text": f"SpO2 cayó {_fmt(baseline['mean'] - value)} puntos bajo tu línea base"}
        if k == "exercise":
            n = _sessions_7d(d, day)
            return {"code": "pocas_sesiones", "sessions": n,
                    "text": f"{n} sesiones de ≥ {_fmt(CFG('yellow_extra.exercise_session_min_done'))} min en 7 días (mínimo {_fmt(CFG('yellow_extra.exercise_min_sessions_week'))})"}
        if k == "glucose":
            return {"code": "glucosa_ayunas", "text": f"Glucosa en ayunas {_fmt(value)} mg/dL (rango de referencia 70–99)"}
        n = _days_out(d, res, k, vday) if k in BANDED else 0
        lo, hi = (baseline or {}).get("lo"), (baseline or {}).get("hi")
        band = f"banda {_fmt(lo, 1)}–{_fmt(hi, 1)} {unit}" if lo is not None and hi is not None else \
            f"mínimo {_fmt(lo, 1)} {unit}" if lo is not None else f"máximo {_fmt(hi, 1)} {unit}" if hi is not None else "sin banda"
        return {"code": "banda_personal", "days_out": n, "text": f"Fuera de tu banda personal {n} días seguidos ({band})"}
    if code == 0:  # informativos en verde
        if day < 0:
            return {"code": "prevuelo", "text": "Prevuelo: se está construyendo tu línea base"}
        if k in BANDED and not (baseline and baseline["ready"]):
            return {"code": "sin_linea_base", "text": "Sin línea base todavía: solo límites clínicos"}
        if 1 <= day <= EARLY:
            return {"code": "adaptacion_inicial", "text": f"Días 1–{EARLY} de vuelo: solo límites clínicos"}
    return None


# ---------- API ----------
def _records(session: Session, astronaut_id: str) -> list[HealthRecord]:
    q = select(HealthRecord).where(HealthRecord.astronaut_id == astronaut_id).order_by(HealthRecord.timestamp)
    return list(session.exec(q).all())


def compute_status(session: Session, astronaut_id: str) -> dict | None:
    """StatusResponse del último día con registros (1.5 completo y motivos de 1.6). None si no hay registros."""
    records = _records(session, astronaut_id)
    if not records:
        return None
    d, res = _status_frame(build_daily(records, astronaut_id))
    day = int(d.index[-1])
    row = res.loc[day]
    indicators = {}
    for k in KEYS:
        have = d[COLS[k]].dropna()
        value = float(have.iloc[-1]) if len(have) else None
        vday = int(have.index[-1]) if len(have) else None
        code = int(row[f"status_{k}"])
        if value is None and (k != "exercise" or code == 0):
            code = None  # sin datos (el ejercicio sí alerta aunque no haya sesiones registradas)
        baseline = None
        if k in BANDED:
            mean, lo, hi = (_num(row[f"{p}_{k}"]) for p in ("base", "lo", "hi"))
            baseline = {"ready": mean is not None, "mean": mean, "lo": lo, "hi": hi}
        status = STATUS_BY_CODE[code] if code is not None else None
        indicators[k] = {
            "value": value, "value_day": vday, "carried": vday is not None and vday != day,
            "status": status.value if status else None,
            "reason": _reason(k, code, value, vday if vday is not None else day, day, baseline, d, res) if code is not None else None,
            "baseline": baseline, "recommendation": get_recommendation(k, status),
        }
    reasons = []
    yellows = [k for k in KEYS if k != "glucose" and indicators[k]["status"] == "attention"]
    if day > 0 and cfg("general.two_yellow_to_red") and int(row["n_yellow"]) >= 2:
        reasons.append({"code": "dos_amarillos", "indicators": yellows,
                        "text": "Dos indicadores en amarillo a la vez: " + ", ".join(INDICATORS[k]["label"] for k in yellows)})
    astro = session.get(Astronaut, astronaut_id)
    return {
        "astronaut_id": astronaut_id, "mission_day": day, "phase": "preflight" if day < 0 else "inflight",
        "evaluation_mode": "prevuelo" if day < 0 else "adaptacion_inicial" if day <= EARLY else "linea_base",
        "data_origin": astro.source if astro else "manual",
        "overall": {"status": STATUS_BY_CODE[int(row["overall"])].value, "reasons": reasons},
        "indicators": indicators,
    }


def compute_series(session: Session, astronaut_id: str, k: str) -> list[dict] | None:
    """Serie diaria de un indicador con su estado y su banda (para las gráficas). None si no hay registros."""
    records = _records(session, astronaut_id)
    if not records:
        return None
    d, res = _status_frame(build_daily(records, astronaut_id))
    out = []
    for day in d.index:
        v = _num(d.at[day, COLS[k]])
        item = {"mission_day": int(day), "value": v,
                "status": STATUS_BY_CODE[int(res.at[day, f"status_{k}"])].value if v is not None else None,
                "base": None, "lo": None, "hi": None}
        if k in BANDED:
            item.update({p: _num(res.at[day, f"{p}_{k}"]) for p in ("base", "lo", "hi")})
        out.append(item)
    return out
