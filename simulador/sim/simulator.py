#!/usr/bin/env python3
"""
Simulador de datos de mision, SINTETICOS (NASA Space Apps 2026, monitoreo de salud de astronautas).

TODO lo que produce este script es sintetico: no son mediciones de astronautas reales.

Modelo por astronauta e indicador:
    valor(dia) = linea base personal + deriva en vuelo (por astronauta) + ritmo circadiano (solo FC)
                 + ruido autocorrelacionado + eventos/anomalias etiquetadas
Cada parametro vive en sim_params.json con su estado (medido, referencia, derivado, supuesto, sin fuente)
y su fuente. Con la misma semilla y los mismos parametros se obtiene el mismo dataset.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.signal import lfilter
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
SCHEMA_VERSION = "0.2.0"
GENERATOR = "simulator.py v0.2"
STRATIFY = True  # muestreo estratificado de la linea base de FC y presion sistolica (ver simulate_cohort)
INDICATORS = ["hr_rest", "bp_sys", "bp_dia", "spo2", "temp", "glucose", "sleep", "mood"]
DAILY_VALUE_COLS = ["hr_rest_bpm", "bp_sys_mmhg", "bp_dia_mmhg", "spo2_pct", "temp_c", "glucose_mgdl",
                    "sleep_h", "mood_1_5", "exercise_min", "fitness_pct_preflight"]
DISCLAIMER = ("DATOS SINTETICOS generados por simulacion. No son mediciones de astronautas reales. "
              "Los parametros y sus fuentes estan en params_used.json; los marcados como 'supuesto' o "
              "'sin fuente' son decisiones de diseno, no datos publicados.")


class Params:
    """Lee sim_params.json: cada parametro es [valor, estado, fuente]."""

    def __init__(self, path=HERE / "sim_params.json"):
        self.path = Path(path)
        text = self.path.read_text(encoding="utf-8")
        self.sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        raw = json.loads(text)
        self.raw = {k: v for k, v in raw.items() if not k.startswith("_")}

    def __call__(self, key):
        sec, name = key.split(".", 1)
        return self.raw[sec][name][0]

    def set(self, key, value):
        sec, name = key.split(".", 1)
        self.raw[sec][name][0] = value

    def table(self):
        rows = []
        for sec, d in self.raw.items():
            for name, (value, status, source) in d.items():
                rows.append({"param": f"{sec}.{name}", "value": value, "status": status, "source": source})
        return rows


# ----------------------------------------------------------------------------------------------
# utilidades
# ----------------------------------------------------------------------------------------------
def ar1(rng, n, rho):
    """Ruido AR(1) estacionario de varianza 1 (con calentamiento de 60 pasos)."""
    z = rng.standard_normal(n + 60)
    y = lfilter([math.sqrt(1 - rho ** 2)], [1, -rho], z)
    return y[60:]


def prog(t, tau):
    """Avance de la adaptacion: 0 antes del vuelo, 1 - exp(-t/tau) en vuelo."""
    t = np.asarray(t, dtype=float)
    return np.where(t > 0, 1 - np.exp(-np.clip(t, 0, None) / tau), 0.0)


def between_sd(total_sd, within_sd):
    return math.sqrt(max(total_sd ** 2 - within_sd ** 2, 1e-12))


def tnorm(rng, mean, sd, k=2.5):
    """Normal recortada a +/- k DE (los astronautas pasan filtros medicos)."""
    return float(np.clip(rng.normal(mean, sd), mean - k * sd, mean + k * sd))


def lognormal_params(mean, p_gt, thr):
    """Lognormal con media `mean` y P(X > thr) = p_gt."""
    def f(s):
        mu = math.log(mean) - s ** 2 / 2
        return 1 - norm.cdf((math.log(thr) - mu) / s) - p_gt
    grid = np.linspace(0.05, 3.0, 300)
    vals = np.array([f(x) for x in grid])
    k = int(np.argmax(vals))
    if vals[k] < 0:
        raise ValueError("Con esa media la lognormal no alcanza la proporcion pedida de perdidas > umbral")
    s = brentq(f, 0.05, float(grid[k]))
    return math.log(mean) - s ** 2 / 2, s


def bump(d):
    """Perfil suave de un evento de d dias (maximo 1)."""
    return np.sin(np.pi * (np.arange(d) + 0.5) / d)


# ----------------------------------------------------------------------------------------------
# astronauta y anomalias
# ----------------------------------------------------------------------------------------------
def sample_astronaut(rng, P, sex, aid, z_strat=None):
    S = sex
    a = {"astronaut_id": aid, "sex": sex}
    a["age_years"] = round(float(rng.normal(P(f"cohort.age_mean_{S}"), P(f"cohort.age_sd_{S}"))), 1)

    hr_total = (P(f"hr.p95_{S}") - P(f"hr.p5_{S}")) / 3.29
    hr_b = between_sd(hr_total, P("hr.day_noise_sd"))
    drawn = tnorm(rng, P(f"hr.mean_{S}"), hr_b)
    a["hr_base"] = drawn if z_strat is None else float(P(f"hr.mean_{S}") + np.clip(z_strat["hr"], -2.5, 2.5) * hr_b)

    sys_total = (P(f"bp.sys_p95_{S}") - P(f"bp.sys_p5_{S}")) / 3.29
    dia_total = (P(f"bp.dia_p95_{S}") - P(f"bp.dia_p5_{S}")) / 3.29
    sys_b = between_sd(sys_total, P("bp.day_noise_sd_sys"))
    dia_b = between_sd(dia_total, P("bp.day_noise_sd_dia"))
    c = P("bp.sys_dia_corr")
    z1, z2 = rng.standard_normal(2)
    if z_strat is not None:
        z1 = z_strat["sys"]
    zd = c * z1 + math.sqrt(1 - c ** 2) * z2
    a["sys_base"] = float(P(f"bp.sys_mean_{S}") + np.clip(z1, -2.5, 2.5) * sys_b)
    a["dia_base"] = float(P(f"bp.dia_mean_{S}") + np.clip(zd, -2.5, 2.5) * dia_b)
    zbp = float(rng.standard_normal())
    sd_sys_rel = P("bp.drift_between_sd_mmhg") / abs(P("bp.sys_mean_M"))
    sd_dia_rel = P("bp.drift_between_sd_mmhg") / abs(P("bp.dia_mean_M"))
    a["bp_sys_rel_drift"] = P("bp.drift_sys_mmhg_M") / P("bp.sys_mean_M") + zbp * sd_sys_rel
    a["bp_dia_rel_drift"] = P("bp.drift_dia_mmhg_M") / P("bp.dia_mean_M") + zbp * sd_dia_rel

    a["spo2_base"] = tnorm(rng, P("spo2.mean"), between_sd(P("spo2.total_sd"), P("spo2.within_sd")))
    a["temp_base"] = tnorm(rng, P("temp.mean"), between_sd(P("temp.total_sd"), P("temp.within_sd")))
    a["temp_drift"] = float(np.clip(rng.normal(P("temp.drift_mean"), P("temp.drift_sd")), 0.2, 2.2))
    # v0.3: tope de la meseta individual de reposo (linea base + deriva), supuesto declarado en sim_params.json
    a["temp_drift"] = float(max(min(a["temp_drift"], P("temp.plateau_max_c") - a["temp_base"]), 0.2))
    a["glucose_base"] = tnorm(rng, P("glucose.mean"), between_sd(P("glucose.total_sd"), P("glucose.within_sd")))
    a["glucose_day_offset"] = int(rng.integers(0, int(P("glucose.sample_interval_days"))))

    a["sleep_base_h"] = tnorm(rng, P("sleep.mean_h"), P("sleep.between_sd_h"))
    if rng.random() < P("sleep.p_decrease"):
        a["sleep_direction"] = "decrease"
        a["sleep_drift_h"] = float(min(rng.normal(P("sleep.decrease_total_h"), P("sleep.decrease_sd_h")), -0.2))
    else:
        a["sleep_direction"] = "increase"
        a["sleep_drift_h"] = float(max(rng.normal(P("sleep.increase_total_h"), P("sleep.increase_sd_h")), 0.1))

    a["mood_base"] = tnorm(rng, P("mood.mean"), P("mood.between_sd"))

    a["amp_pre"] = float(max(rng.normal(P("hr_circ.amp_pre"), P("hr_circ.amp_between_sd")), 4.0))
    a["amp_final"] = a["amp_pre"] * P("hr_circ.amp_final") / P("hr_circ.amp_pre")
    a["acrophase_h"] = float(rng.normal(P("hr_circ.acrophase_hour"), P("hr_circ.acrophase_between_sd_h")))

    a["adherence"] = float(np.clip(rng.normal(P("exercise.adherence_mean"), P("exercise.adherence_between_sd")), 0.6, 1.0))
    mu, s = lognormal_params(P("exercise.fitness_loss_mean"), P("exercise.fitness_p_loss_gt20"), 0.20)
    a["fitness_loss"] = float(np.clip(rng.lognormal(mu, s), 0.0, 0.6))
    return a


ANOM_TYPES = [
    # (tipo, clave de parametros, es evento de salud)
    ("infection", "infection", True),
    ("sleep_loss", "sleeploss", True),
    ("bp_spike", "bpspike", True),
    ("spo2_dip", "spo2dip", True),
    ("mood_low", "moodlow", True),
    ("exercise_dropout", "exdrop", True),
    ("glucose_high", "glucosehigh", True),
    ("sensor_artifact", "artifact", False),
]


def schedule_anomalies(rng, P, aid, duration):
    """Lista de anomalias con etiqueta de verdad conocida."""
    out = []
    n = 0
    for atype, key, is_health in ANOM_TYPES:
        for _ in range(int(rng.poisson(P(f"anomaly.{key}_rate")))):
            if atype == "sensor_artifact":
                days = 1
            elif atype == "glucose_high":
                days = int(P("anomaly.glucosehigh_days"))
            else:
                days = int(rng.integers(P(f"anomaly.{key}_days_min"), P(f"anomaly.{key}_days_max") + 1))
            first = int(P("anomaly.first_day"))
            start = int(rng.integers(first, duration - days + 2))
            scale = float(np.clip(rng.normal(1.0, 0.2), 0.6, 1.5))
            n += 1
            out.append({"anomaly_id": f"{aid}-ANOM-{n:03d}", "astronaut_id": aid, "type": atype,
                        "is_health_event": is_health, "start_day": start, "end_day": start + days - 1,
                        "magnitude_scale": round(scale, 3)})
    return out


def anomaly_effects(P, anomalies, pre, duration):
    """Efectos aditivos por indicador, dias bloqueados de ejercicio y artefactos de un dia."""
    n = pre + duration
    eff = {k: np.zeros(n) for k in INDICATORS}
    block_ex = np.zeros(n, dtype=bool)
    labels = [[] for _ in range(n)]
    artifacts = []  # (indice, indicador, desviacion)

    def idx(day):
        return pre + day - 1

    for an in anomalies:
        d0, d1, sc = an["start_day"], an["end_day"], an["magnitude_scale"]
        D = d1 - d0 + 1
        prof = bump(D) if D > 1 else np.array([1.0])
        sl = slice(idx(d0), idx(d1) + 1)
        for i in range(idx(d0), idx(d1) + 1):
            labels[i].append(an["anomaly_id"])
        t = an["type"]
        if t == "infection":
            eff["temp"][sl] += P("anomaly.infection_temp") * sc * prof
            eff["hr_rest"][sl] += P("anomaly.infection_hr") * sc * prof
            eff["sleep"][sl] += P("anomaly.infection_sleep") * sc * prof
            eff["mood"][sl] += P("anomaly.infection_mood") * sc * prof
            block_ex[sl] |= prof > 0.6
        elif t == "sleep_loss":
            eff["sleep"][sl] += P("anomaly.sleeploss_sleep") * sc * prof
            eff["mood"][sl] += P("anomaly.sleeploss_mood") * sc * prof
            eff["hr_rest"][sl] += P("anomaly.sleeploss_hr") * sc * prof
        elif t == "bp_spike":
            eff["bp_sys"][sl] += P("anomaly.bpspike_sys") * sc * prof
            eff["bp_dia"][sl] += P("anomaly.bpspike_dia") * sc * prof
            eff["hr_rest"][sl] += P("anomaly.bpspike_hr") * sc * prof
        elif t == "spo2_dip":
            eff["spo2"][sl] += P("anomaly.spo2dip_spo2") * sc * prof
            eff["hr_rest"][sl] += P("anomaly.spo2dip_hr") * sc * prof
        elif t == "mood_low":
            eff["mood"][sl] += P("anomaly.moodlow_mood") * sc * prof
            eff["sleep"][sl] += P("anomaly.moodlow_sleep") * sc * prof
        elif t == "exercise_dropout":
            block_ex[sl] = True
        elif t == "glucose_high":
            eff["glucose"][sl] += P("anomaly.glucosehigh_glucose") * sc * prof
        elif t == "sensor_artifact":
            choice = ["temp", "hr_rest", "bp_sys", "spo2"][int(an["anomaly_id"][-3:]) % 4]
            dev = {"temp": P("anomaly.artifact_temp"), "hr_rest": P("anomaly.artifact_hr"),
                   "bp_sys": P("anomaly.artifact_bp_sys"), "spo2": P("anomaly.artifact_spo2")}[choice] * sc
            artifacts.append((idx(d0), choice, dev))
            an["indicator"] = choice
    return eff, block_ex, labels, artifacts


# ----------------------------------------------------------------------------------------------
# simulacion de un astronauta
# ----------------------------------------------------------------------------------------------
def simulate_astronaut(rng, P, a, with_intraday=True):
    pre, dur = int(P("mission.preflight_days")), int(P("mission.duration_days"))
    n = pre + dur
    days = np.concatenate([np.arange(-pre, 0), np.arange(1, dur + 1)])
    t = np.where(days > 0, days, 0).astype(float)
    flight = days > 0

    anomalies = schedule_anomalies(rng, P, a["astronaut_id"], dur)
    eff, block_ex, labels, artifacts = anomaly_effects(P, anomalies, pre, dur)

    # ruido diario: sueno, animo y FC correlacionados (hipotesis del equipo)
    C = np.array([[1, P("corr.sleep_mood"), P("corr.sleep_hr")],
                  [P("corr.sleep_mood"), 1, P("corr.mood_hr")],
                  [P("corr.sleep_hr"), P("corr.mood_hr"), 1]])
    L = np.linalg.cholesky(C)
    Zc = rng.standard_normal((n + 60, 3)) @ L.T
    def filt(z, rho):
        y = lfilter([math.sqrt(1 - rho ** 2)], [1, -rho], z)
        return y[60:]
    x_sleep = filt(Zc[:, 0], P("sleep.ar1"))
    x_mood = filt(Zc[:, 1], P("mood.ar1"))
    x_hr = filt(Zc[:, 2], P("hr.ar1"))
    cb = P("bp.sys_dia_corr")
    zs, zd0 = rng.standard_normal(n + 60), rng.standard_normal(n + 60)
    x_sys = filt(zs, P("bp.ar1"))
    x_dia = filt(cb * zs + math.sqrt(1 - cb ** 2) * zd0, P("bp.ar1"))
    x_spo2 = ar1(rng, n, P("spo2.ar1"))
    x_temp = ar1(rng, n, P("temp.ar1"))
    x_gluc = ar1(rng, n, P("glucose.ar1"))

    # --- FC con ritmo circadiano ---
    A = a["amp_pre"] + (a["amp_final"] - a["amp_pre"]) * prog(t, P("hr_circ.amp_tau_days"))
    hm = P("mission.measure_hour")
    cos_m = np.cos(2 * np.pi * (hm - a["acrophase_h"]) / 24)
    mesor = a["hr_base"] - A * cos_m + eff["hr_rest"] + P("hr.day_noise_sd") * x_hr \
        + a.get("hr_drift", 0.0) * prog(t, 21.0)
    step = int(P("mission.intraday_step_min"))
    spd = 24 * 60 // step
    hours = np.arange(spd) * step / 60.0
    circ = A[:, None] * np.cos(2 * np.pi * (hours[None, :] - a["acrophase_h"]) / 24)
    e = ar1(rng, n * spd, P("hr_circ.intraday_ar1")).reshape(n, spd) * P("hr_circ.intraday_sd")
    hr_slots = mesor[:, None] + circ + e

    # --- ejercicio ---
    ex_min = np.full(n, np.nan)
    done = np.zeros(n, dtype=bool)
    for i in range(n):
        if not flight[i]:
            continue
        sched = (days[i] % 7) != int(P("exercise.rest_weekday"))
        ok = sched and (not block_ex[i]) and (rng.random() < a["adherence"])
        done[i] = ok
        ex_min[i] = max(0.0, P("exercise.session_min") + rng.normal(0, P("exercise.minutes_noise_sd"))) if ok else 0.0
    ex_slots = np.zeros((n, spd), dtype=bool)
    s0 = int(round(P("hr_circ.exercise_start_hour") * 60 / step))
    s1 = s0 + int(round(P("exercise.aerobic_min") / step))
    for i in np.where(done)[0]:
        hr_slots[i, s0:s1] += P("hr_circ.exercise_hr_delta")
        hr_slots[i, s1:s1 + 1] += 0.4 * P("hr_circ.exercise_hr_delta")
        ex_slots[i, s0:s1] = True

    sel = np.abs(hours - hm) <= 0.5
    hr_daily = hr_slots[:, sel].mean(axis=1)

    # --- presion arterial ---
    pb = prog(t, P("bp.tau_days"))
    sys_d = a["sys_base"] * (1 + a["bp_sys_rel_drift"] * pb) + P("bp.day_noise_sd_sys") * x_sys + eff["bp_sys"]
    dia_d = a["dia_base"] * (1 + a["bp_dia_rel_drift"] * pb) + P("bp.day_noise_sd_dia") * x_dia + eff["bp_dia"]

    spo2_d = a["spo2_base"] + P("spo2.drift_mean") * prog(t, 14.0) + P("spo2.within_sd") * x_spo2 + eff["spo2"]
    temp_d = a["temp_base"] + a["temp_drift"] * prog(t, P("temp.tau_days")) + P("temp.within_sd") * x_temp \
        + eff["temp"] + P("temp.site_offset_c")
    gluc_d = a["glucose_base"] + P("glucose.within_sd") * x_gluc + eff["glucose"]
    sleep_d = a["sleep_base_h"] + a["sleep_drift_h"] * prog(t, P("sleep.tau_days")) \
        + P("sleep.within_sd_h") * x_sleep + eff["sleep"]
    mood_d = a["mood_base"] + P("mood.within_sd") * x_mood + eff["mood"]

    # artefactos de un dia (error del sensor: NO son eventos de salud)
    for i, ind, dev in artifacts:
        if ind == "temp":
            temp_d[i] += dev
        elif ind == "hr_rest":
            hr_daily[i] += dev
        elif ind == "bp_sys":
            sys_d[i] += dev
        elif ind == "spo2":
            spo2_d[i] += dev

    # --- aptitud fisica (prueba periodica) ---
    fit_true = 100 * (1 - a["fitness_loss"] * prog(t, P("exercise.fitness_tau_days")))
    fit = np.full(n, np.nan)
    fit[pre - 1] = 100.0  # referencia previa al vuelo, por definicion 100 %
    tint = int(P("exercise.fitness_test_interval_days"))
    for i in range(n):
        if flight[i] and days[i] % tint == 0:
            fit[i] = 100 * (1 - a["fitness_loss"] * prog(days[i], P("exercise.fitness_tau_days"))
                            + rng.normal(0, P("exercise.fitness_meas_noise_sd")))

    # --- redondeo, limites y faltantes ---
    hr_v = np.clip(hr_daily, P("hr.min"), P("hr.max"))
    sys_v = np.clip(np.round(sys_d), P("bp.sys_min"), P("bp.sys_max"))
    dia_v = np.clip(np.round(dia_d), P("bp.dia_min"), P("bp.dia_max"))
    spo2_v = np.clip(np.round(spo2_d), P("spo2.min"), P("spo2.max"))
    temp_v = np.clip(np.round(temp_d, 1), P("temp.min"), P("temp.max"))
    gluc_v = np.clip(np.round(gluc_d), P("glucose.min"), P("glucose.max"))
    sleep_v = np.clip(np.round(sleep_d, 2), P("sleep.min_h") if False else P("sleep.min"), P("sleep.max"))
    mood_v = np.clip(np.round(mood_d, 1), P("mood.scale_min"), P("mood.scale_max"))

    flags = [[] for _ in range(n)]
    miss_day = rng.random(n) < P("mission.missing_day_prob")
    miss_spo2 = rng.random(n) < P("spo2.missing_prob")
    gluc_sched = ((days + a["glucose_day_offset"]) % int(P("glucose.sample_interval_days"))) == 0

    df = pd.DataFrame({
        "astronaut_id": a["astronaut_id"], "sex": a["sex"], "mission_day": days,
        "phase": np.where(flight, "inflight", "preflight"),
        "hr_rest_bpm": np.round(hr_v, 1), "bp_sys_mmhg": sys_v, "bp_dia_mmhg": dia_v,
        "spo2_pct": spo2_v, "temp_c": temp_v, "glucose_mgdl": gluc_v, "sleep_h": sleep_v, "mood_1_5": mood_v,
        "exercise_min": np.round(ex_min, 0), "fitness_pct_preflight": np.round(fit, 1),
    })
    df.loc[~gluc_sched, "glucose_mgdl"] = np.nan
    df.loc[miss_spo2, "spo2_pct"] = np.nan
    for i in np.where(miss_spo2)[0]:
        flags[i].append("spo2_missing_motion")
    value_cols = ["hr_rest_bpm", "bp_sys_mmhg", "bp_dia_mmhg", "spo2_pct", "temp_c", "glucose_mgdl",
                  "sleep_h", "mood_1_5", "exercise_min"]
    df.loc[miss_day, value_cols] = np.nan
    for i in np.where(miss_day)[0]:
        flags[i].append("missing_day")
    df["quality_flags"] = [";".join(f) for f in flags]
    df["truth_anomaly_ids"] = [";".join(l) for l in labels]
    df["truth_fitness_lt80"] = flight & (fit_true < 80.0)
    df["data_origin"] = "synthetic"

    intraday = None
    if with_intraday:
        ctx = np.zeros((n, spd), dtype=np.int8)
        ctx[ex_slots] = 2
        flat = ctx.reshape(-1)
        onset = int(round(22.5 * 60 / step))
        for i in range(n):
            if np.isnan(sleep_v[i]):
                continue
            start = (i - 1) * spd + onset
            end = start + int(round(sleep_v[i] * 60 / step))
            lo, hi = max(start, 0), min(end, n * spd)
            if hi > lo:
                seg = flat[lo:hi]
                seg[seg == 0] = 1
        intraday = {"astronaut_id": a["astronaut_id"], "step_minutes": step, "first_mission_day": int(days[0]),
                    "n_days": n, "hr_bpm": np.round(np.clip(hr_slots, 30, 200), 1).reshape(-1),
                    "context": flat}
    return df, anomalies, intraday


# ----------------------------------------------------------------------------------------------
# cohorte
# ----------------------------------------------------------------------------------------------
def simulate_cohort(P, n_female=None, n_male=None, seed=None, with_intraday=True):
    n_f = P("cohort.n_female") if n_female is None else n_female
    n_m = P("cohort.n_male") if n_male is None else n_male
    seed = int(P("mission.seed") if seed is None else seed)
    sexes = ["F"] * n_f + ["M"] * n_m
    children = np.random.SeedSequence(seed).spawn(len(sexes))
    # Muestreo estratificado por sexo: con n tan pequeno, el azar puede dar una cohorte sesgada.
    # Los z de FC y presion sistolica se reparten en cuantiles (i+0.5)/n y se barajan.
    zrng = np.random.default_rng(seed + 1)
    z_by_idx = {}
    for sx in ("F", "M"):
        idx = [i for i, s in enumerate(sexes) if s == sx]
        k = len(idx)
        if k:
            zs_hr = norm.ppf((np.arange(k) + 0.5) / k)
            zs_sys = norm.ppf((np.arange(k) + 0.5) / k)
            zrng.shuffle(zs_hr)
            zrng.shuffle(zs_sys)
            for j, i in enumerate(idx):
                z_by_idx[i] = {"hr": float(zs_hr[j]), "sys": float(zs_sys[j])}
    astronauts, frames, anomalies, intradays = [], [], [], []
    for i, (sex, ss) in enumerate(zip(sexes, children), start=1):
        rng = np.random.default_rng(ss)
        aid = f"SIM-{i:03d}"
        a = sample_astronaut(rng, P, sex, aid, z_by_idx[i - 1] if STRATIFY else None)
        df, an, intra = simulate_astronaut(rng, P, a, with_intraday)
        astronauts.append(a)
        frames.append(df)
        anomalies += an
        if intra is not None:
            intradays.append(intra)
    daily = pd.concat(frames, ignore_index=True)
    return {"astronauts": astronauts, "daily": daily, "anomalies": pd.DataFrame(anomalies),
            "intraday": intradays, "seed": seed}


def observed_preflight(daily):
    """Linea base observada (ancla previa al vuelo): media y DE de los dias previos."""
    pre = daily[daily["phase"] == "preflight"]
    out = {}
    for aid, g in pre.groupby("astronaut_id"):
        out[aid] = {c: {"mean": None if g[c].dropna().empty else round(float(g[c].mean()), 3),
                        "sd": None if g[c].dropna().size < 2 else round(float(g[c].std(ddof=1)), 3),
                        "n": int(g[c].notna().sum())}
                    for c in DAILY_VALUE_COLS if c not in ("exercise_min",)}
    return out


def to_json(P, res, status=None):
    daily = res["daily"]
    obs = observed_preflight(daily)
    latent_keys = {"astronaut_id", "sex", "age_years"}
    astronauts = []
    for a in res["astronauts"]:
        astronauts.append({
            "astronaut_id": a["astronaut_id"], "sex": a["sex"], "age_years": a["age_years"],
            "baseline_preflight_observed": obs[a["astronaut_id"]],
            "latent_truth": {k: (round(v, 4) if isinstance(v, float) else v)
                             for k, v in a.items() if k not in latent_keys},
        })

    def rec(r):
        d = {"astronaut_id": r.astronaut_id, "mission_day": int(r.mission_day), "phase": r.phase}
        for c in DAILY_VALUE_COLS:
            v = getattr(r, c)
            d[c] = None if pd.isna(v) else float(v)
        d["quality_flags"] = [f for f in r.quality_flags.split(";") if f]
        d["truth_anomaly_ids"] = [f for f in r.truth_anomaly_ids.split(";") if f]
        d["truth_fitness_lt80"] = bool(r.truth_fitness_lt80)
        return d

    records = [rec(r) for r in daily.itertuples(index=False)]
    anomalies = []
    for r in res["anomalies"].itertuples(index=False):
        anomalies.append({"anomaly_id": r.anomaly_id, "astronaut_id": r.astronaut_id, "type": r.type,
                          "is_health_event": bool(r.is_health_event), "start_day": int(r.start_day),
                          "end_day": int(r.end_day), "magnitude_scale": float(r.magnitude_scale),
                          **({"indicator": r.indicator} if isinstance(getattr(r, "indicator", None), str) else {})})
    doc = {
        "schema_version": SCHEMA_VERSION,
        "data_origin": "synthetic",
        "disclaimer": DISCLAIMER,
        "generator": {"name": GENERATOR, "seed": res["seed"], "params_sha256": P.sha256},
        "mission": {"duration_days": int(P("mission.duration_days")), "preflight_days": int(P("mission.preflight_days")),
                    "day_convention": "dias previos al vuelo -N..-1; dias de vuelo 1..duration (no existe el dia 0)"},
        "indicators": INDICATOR_META,
        "astronauts": astronauts,
        "daily": records,
        "anomalies": anomalies,
        "intraday_hr": [{"astronaut_id": i["astronaut_id"], "step_minutes": i["step_minutes"],
                         "first_mission_day": i["first_mission_day"], "n_days": i["n_days"],
                         "context_codes": {"0": "vigilia", "1": "sueno", "2": "ejercicio"},
                         "hr_bpm": [float(x) for x in i["hr_bpm"]], "context": [int(x) for x in i["context"]]}
                        for i in res["intraday"]],
    }
    if status is not None:
        doc["semaforo"] = status
    return doc


INDICATOR_META = {
    "hr_rest_bpm": {"label": "FC en reposo", "unit": "lpm", "frequency": "diaria, 08:30 sentado",
                    "reference": "NHSR 41: 52-95 lpm (P5-P95, adultos de EE. UU.)"},
    "bp_sys_mmhg": {"label": "Presion sistolica", "unit": "mmHg", "frequency": "diaria, 08:30 sentado",
                    "reference": "NHSR 35: 94-132 mmHg (P5-P95, adultos sin hipertension)"},
    "bp_dia_mmhg": {"label": "Presion diastolica", "unit": "mmHg", "frequency": "diaria, 08:30 sentado",
                    "reference": "NHSR 35: 51-84 mmHg (P5-P95, adultos sin hipertension)"},
    "spo2_pct": {"label": "SpO2", "unit": "%", "frequency": "diaria",
                 "reference": "sin rango normal con fuente; hipoxemia <90 % (Open Critical Care)"},
    "temp_c": {"label": "Temperatura", "unit": "C", "frequency": "diaria",
               "reference": "Obermeyer 2017: media 36,6; 95 % entre 35,7 y 37,3"},
    "glucose_mgdl": {"label": "Glucosa en ayunas (manual)", "unit": "mg/dl", "frequency": "semanal, entrada manual",
                     "reference": "ADA 2026: hipoglucemia <70; diabetes >=126 en ayunas"},
    "sleep_h": {"label": "Horas de sueno", "unit": "h", "frequency": "diaria (noche previa)",
                "reference": "AASM/SRS: 7 h o mas; NASA: promedio en vuelo 6-6,5 h"},
    "mood_1_5": {"label": "Estado de animo", "unit": "puntaje 1-5", "frequency": "diaria, autorreporte",
                 "reference": "sin fuente (escala decidida por el equipo)"},
    "exercise_min": {"label": "Ejercicio completado", "unit": "min", "frequency": "diaria (solo en vuelo)",
                     "reference": "NASA/Guilliams: bloques de 150 min, 6 dias por semana"},
    "fitness_pct_preflight": {"label": "Aptitud fisica vs previa al vuelo", "unit": "% de la previa",
                              "frequency": "prueba cada 30 dias",
                              "reference": "NASA-STD-3001: mantener >=80 %; R09: perdida media 10-12 %"},
}


def data_dictionary():
    rows = [
        ("astronaut_id", "Identificador del astronauta simulado", "texto", "SIM-001..."),
        ("sex", "Sexo del perfil simulado (F o M)", "texto", "F, M"),
        ("mission_day", "Dia de mision; dias previos -N..-1, vuelo 1..duracion", "dias", "-30..180"),
        ("phase", "preflight o inflight", "texto", "preflight, inflight"),
        ("hr_rest_bpm", "FC en reposo, sentado, 08:30", "lpm", "52-95 (P5-P95, referencia terrestre)"),
        ("bp_sys_mmhg", "Presion sistolica en reposo", "mmHg", "94-132 (referencia terrestre)"),
        ("bp_dia_mmhg", "Presion diastolica en reposo", "mmHg", "51-84 (referencia terrestre)"),
        ("spo2_pct", "Saturacion de oxigeno; vacio si el sensor no leyo", "%", "mayor o igual a 90 es lo esperado; sin rango normal con fuente"),
        ("temp_c", "Temperatura (equivalente oral)", "C", "35,7-37,3 (95 % de Obermeyer 2017)"),
        ("glucose_mgdl", "Glucosa en ayunas, entrada manual semanal; vacio otros dias", "mg/dl", "sin rango normal con fuente"),
        ("sleep_h", "Horas dormidas la noche previa", "h", "6-8 tipico; promedio en vuelo 6-6,5 (NASA)"),
        ("mood_1_5", "Estado de animo autorreportado", "puntaje 1-5", "sin fuente"),
        ("exercise_min", "Minutos de ejercicio completados ese dia (solo vuelo)", "min", "0 o ~150"),
        ("fitness_pct_preflight", "Aptitud fisica respecto a la previa; solo dias de prueba", "%", ">=80 (requisito NASA-STD-3001)"),
        ("quality_flags", "Problemas de calidad conocidos (spo2_missing_motion, missing_day)", "texto", ""),
        ("truth_anomaly_ids", "Etiqueta de verdad: anomalias activas ese dia (ver anomalies)", "texto", ""),
        ("truth_fitness_lt80", "Etiqueta de verdad: la aptitud fisica REAL (no la medida) esta bajo 80 % de la previa", "bool", "False/True"),
        ("data_origin", "Siempre 'synthetic'", "texto", "synthetic"),
    ]
    return pd.DataFrame(rows, columns=["column", "description", "unit", "expected_range"])


def write_outputs(P, res, out_dir, status=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    res["daily"].rename(columns={"data_origin": "data_origin"}).to_csv(out / "mission_synthetic_daily.csv", index=False)
    res["anomalies"].to_csv(out / "mission_synthetic_anomalies.csv", index=False)
    rows = []
    for i in res["intraday"]:
        n_slots = len(i["hr_bpm"])
        slots_per_day = 24 * 60 // i["step_minutes"]
        k = np.arange(n_slots)
        day_idx = k // slots_per_day
        pre_n = -i["first_mission_day"]
        mday = np.where(day_idx < pre_n, i["first_mission_day"] + day_idx, day_idx - pre_n + 1)
        rows.append(pd.DataFrame({
            "astronaut_id": i["astronaut_id"],
            "mission_day": mday,
            "minute_of_day": (k % slots_per_day) * i["step_minutes"],
            "hr_bpm": i["hr_bpm"], "context": i["context"], "data_origin": "synthetic"}))
    if rows:
        pd.concat(rows, ignore_index=True).to_csv(out / "mission_synthetic_intraday_hr.csv", index=False)
    data_dictionary().to_csv(out / "data_dictionary.csv", index=False)
    (out / "params_used.json").write_text(json.dumps(P.table(), ensure_ascii=False, indent=1), encoding="utf-8")
    doc = to_json(P, res, status)
    (out / "mission_synthetic.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return doc


def semaforo_block(daily, config_path=None):
    """Estado del semaforo por dia (referencia para el equipo de software). Calculado sobre datos SINTETICOS."""
    import semaforo as sf
    cfg = sf.Config(config_path) if config_path else sf.Config()
    cfg_text = Path(config_path or (HERE / "semaforo_config.json")).read_text(encoding="utf-8")
    st = sf.run_semaforo(daily, cfg, return_bands=True, return_reasons=True)
    ind_cols = [c for c in st.columns if c.startswith("status_")]
    records = []
    for r in st.itertuples(index=False):
        d = r._asdict()
        records.append({"astronaut_id": d["astronaut_id"], "mission_day": int(d["mission_day"]),
                        "status": int(d["status"]), "n_yellow": int(d["n_yellow"]),
                        "reasons": [x for x in d["reasons"].split(";") if x],
                        "by_indicator": {c[len("status_"):]: int(d[c]) for c in ind_cols}})
    block = {"version": "semaforo.py v0.2", "config_sha256": hashlib.sha256(cfg_text.encode("utf-8")).hexdigest(),
             "status_codes": {"0": "verde", "1": "amarillo", "2": "rojo"},
             "note": ("Estado calculado por el semaforo v0.2 con umbrales PROVISIONALES (supuestos del equipo, "
                      "ver semaforo_config.json). Los dias previos al vuelo y los primeros dias de vuelo solo "
                      "alimentan la linea base o usan limites absolutos."),
             "daily_status": records}
    return block, st


def main():
    ap = argparse.ArgumentParser(description="Simulador de datos de mision SINTETICOS")
    ap.add_argument("--out", default=str(HERE.parent / "out"))
    ap.add_argument("--params", default=str(HERE / "sim_params.json"))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--n-female", type=int, default=None)
    ap.add_argument("--n-male", type=int, default=None)
    ap.add_argument("--no-semaforo", action="store_true", help="no incluir el estado del semaforo en la salida")
    args = ap.parse_args()
    P = Params(args.params)
    res = simulate_cohort(P, args.n_female, args.n_male, args.seed, with_intraday=True)
    status = None
    if not args.no_semaforo:
        status, st = semaforo_block(res["daily"])
        Path(args.out).mkdir(parents=True, exist_ok=True)
        st.assign(data_origin="synthetic").to_csv(Path(args.out) / "mission_synthetic_semaforo.csv", index=False)
    write_outputs(P, res, args.out, status)
    print(f"Listo: {len(res['astronauts'])} astronautas SINTETICOS, {len(res['daily'])} filas diarias, "
          f"{len(res['anomalies'])} anomalias etiquetadas -> {args.out}")


if __name__ == "__main__":
    main()
