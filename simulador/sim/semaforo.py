#!/usr/bin/env python3
"""
Semaforo (verde / amarillo / rojo) sobre la linea base personal. v0.2

Cambios v0.2 (14 nov 2026, ver semaforo_config.json):
  - Temperatura: el rojo absoluto de 38,0 C (fiebre ORAL en Tierra) solo aplica en los primeros
    `absolute_only_first_days` dias de vuelo; despues se usa `absolute_red.temp_gt_inflight`
    (None = solo linea base personal). Motivo: la deriva normal en vuelo (+1,01 C, Stahn 2017) cruza 38,0.
  - Salto con confirmacion (`jump_confirm`): rojo solo si la lectura siguiente sigue fuera de la banda.
  - Lecturas con salto nunca entran a la linea base.
  - `exclude_flagged_from_baseline`: 0 = nada, 1 = amarillo y rojo, 2 = solo rojo.
  - Limites inferiores absolutos que dan amarillo: FC < 50 (bradicardia, ACC/AHA/HRS 2018) y,
    opcional, PA sistolica < 90 (ESC 2018, sin verificar).

Reglas (todas parametrizadas en semaforo_config.json; NASA no publica criterios numericos de alarma,
asi que casi todo son supuestos del equipo):
  - Linea base personal: media y DE de las lecturas validas de los ultimos `baseline_window_days`
    dias (incluye los dias previos al vuelo, que sirven de ancla). Los dias que ya estaban en
    amarillo o rojo no entran a la ventana (`exclude_flagged_from_baseline`).
  - Amarillo: `consecutive_days_yellow` lecturas seguidas fuera de la banda (+/- band_sd DE, en la
    direccion que importa). SpO2: ademas, una caida de >= 3 puntos. Ejercicio: menos de N sesiones
    en 7 dias. Glucosa (si se incluye): >=126 o <70.
  - Rojo: limite absoluto (referencias clinicas de la Tierra), o salto de >= jump_sd DE en un dia,
    o aptitud fisica < 80 % de la previa, o dos indicadores en amarillo a la vez.
  - Primeros `absolute_only_first_days` dias de vuelo: no se alerta por banda (solo limites absolutos),
    por la adaptacion aguda conocida.
Dias sin lectura: el estado del indicador se arrastra desde el dia anterior.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)
HERE = Path(__file__).resolve().parent

IND = {
    "hr_rest": "hr_rest_bpm", "bp_sys": "bp_sys_mmhg", "bp_dia": "bp_dia_mmhg", "spo2": "spo2_pct",
    "temp": "temp_c", "glucose": "glucose_mgdl", "sleep": "sleep_h", "mood": "mood_1_5",
}
LABEL = {"hr_rest": "FC en reposo", "bp_sys": "PA sistolica", "bp_dia": "PA diastolica", "spo2": "SpO2",
         "temp": "Temperatura", "glucose": "Glucosa", "sleep": "Sueno", "mood": "Animo",
         "exercise": "Ejercicio", "fitness": "Aptitud fisica"}
ABS_RED = {  # indicador: (clave de config, "gt" o "lt")
    "hr_rest": ("absolute_red.hr_rest_gt", "gt"), "bp_sys": ("absolute_red.bp_sys_gt", "gt"),
    "bp_dia": ("absolute_red.bp_dia_gt", "gt"), "temp": ("absolute_red.temp_gt", "gt"),
    "spo2": ("absolute_red.spo2_lt", "lt"), "glucose": ("absolute_red.glucose_lt", "lt"),
}
ABS_YELLOW_LOW = {  # v0.2: limites inferiores absolutos que dan amarillo (vacio 4 de la investigacion)
    "hr_rest": "absolute_yellow.hr_rest_lt", "bp_sys": "absolute_yellow.bp_sys_lt",
}


def _opt(cfg, key, default):
    """Parametro opcional: devuelve `default` si no existe en el config (compatibilidad con v0.1)."""
    try:
        return cfg(key)
    except KeyError:
        return default


class Config:
    def __init__(self, path=HERE / "semaforo_config.json"):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.raw = {k: v for k, v in raw.items() if not k.startswith("_")}

    def __call__(self, key):
        sec, name = key.split(".", 1)
        return self.raw[sec][name][0]

    def set(self, key, value):
        sec, name = key.split(".", 1)
        sec_d = self.raw.setdefault(sec, {})
        if name in sec_d:
            sec_d[name][0] = value
        else:
            sec_d[name] = [value, "supuesto", "variante de evaluacion"]

    def copy_with(self, **kw):
        import copy
        c = Config.__new__(Config)
        c.raw = copy.deepcopy(self.raw)
        for k, v in kw.items():
            c.set(k.replace("__", "."), v)
        return c


def _stack(daily, col):
    """(M, T) por astronauta; asume el mismo calendario para todos."""
    ids = list(dict.fromkeys(daily["astronaut_id"]))
    piv = daily.pivot(index="astronaut_id", columns="mission_day", values=col).loc[ids]
    return ids, piv.columns.values, piv.values.astype(float)


def run_semaforo(daily, cfg, return_bands=True, return_reasons=True):
    ids, days, _ = _stack(daily, "hr_rest_bpm")
    M, T = len(ids), len(days)
    pre = int((days < 0).sum())
    W = int(cfg("general.baseline_window_days"))
    minpts = int(cfg("general.min_window_points"))
    band = float(cfg("general.band_sd"))
    consec = int(cfg("general.consecutive_days_yellow"))
    jump = float(cfg("general.jump_sd"))
    early_n = int(cfg("general.absolute_only_first_days"))

    excl_mode = int(cfg("general.exclude_flagged_from_baseline"))  # 0 nada, 1 amarillo+rojo, 2 solo rojo
    confirm = int(_opt(cfg, "general.jump_confirm", 0))
    unconf_yellow = int(_opt(cfg, "general.jump_unconfirmed_yellow", 0))
    temp_inflight = _opt(cfg, "absolute_red.temp_gt_inflight", cfg("absolute_red.temp_gt"))
    temp_consec = int(_opt(cfg, "absolute_red.temp_inflight_consecutive_days", 1))  # v0.3: dias seguidos sobre el limite en vuelo
    robust = _opt(cfg, "general.baseline_stat", "mean_sd") == "median_mad"
    pred_inflate = int(_opt(cfg, "general.prediction_interval", 0))

    active = [k for k in IND if k != "glucose" or cfg("mvp.include_glucose")]
    status = {}
    bands = {}
    for k in active:
        X = _stack(daily, IND[k])[2]
        floor = cfg(f"sd_floor.{k}")
        direction = cfg(f"direction.{k}")
        S = np.zeros((M, T), dtype=np.int8)
        Bm = np.full((M, T), np.nan)
        Blo = np.full((M, T), np.nan)
        Bhi = np.full((M, T), np.nan)
        flagged = np.zeros((M, T), dtype=bool)
        streak = np.zeros(M, dtype=int)
        prev = np.zeros(M, dtype=np.int8)
        abs_streak = np.zeros(M, dtype=int)  # dias seguidos sobre el limite absoluto (v0.3)
        jprev = np.zeros(M, dtype=np.int8)  # signo del salto de la ultima lectura valida (0 = no hubo)
        for t in range(T):
            lo_i = max(0, t - W)
            win = X[:, lo_i:t].copy()
            if excl_mode and t > 0:
                win[flagged[:, lo_i:t]] = np.nan
            cnt = np.sum(~np.isnan(win), axis=1)
            usable = cnt >= minpts
            with np.errstate(all="ignore"):
                if robust:
                    # mediana y MAD escalada (1,4826 * MAD ~ DE si la distribucion es normal): un dia raro
                    # no ensancha ni corre la banda, asi que no hace falta sacar los dias marcados.
                    mean = np.nanmedian(win, axis=1)
                    sd = 1.4826 * np.nanmedian(np.abs(win - mean[:, None]), axis=1)
                else:
                    mean = np.nanmean(win, axis=1)
                    sd = np.nanstd(win, axis=1, ddof=1)
                if pred_inflate:
                    sd = sd * np.sqrt(1 + 1 / np.maximum(cnt, 1))  # intervalo de prediccion, no de la media
            sd = np.where(np.isfinite(sd), np.maximum(sd, floor), floor)
            Bm[:, t] = np.where(usable, mean, np.nan)
            if direction in ("both", "low"):
                Blo[:, t] = np.where(usable, mean - band * sd, np.nan)
            if direction in ("both", "high"):
                Bhi[:, t] = np.where(usable, mean + band * sd, np.nan)
            if days[t] < 0:
                continue  # dias previos: solo alimentan la linea base
            x = X[:, t]
            have = ~np.isnan(x)
            with np.errstate(all="ignore"):
                z = (x - mean) / sd
            if direction == "both":
                out, jmp = np.abs(z) > band, np.abs(z) >= jump
            elif direction == "low":
                out, jmp = z < -band, z <= -jump
            else:
                out, jmp = z > band, z >= jump
            sgn = np.sign(np.nan_to_num(z)).astype(np.int8)
            early = days[t] <= early_n
            eval_ok = have & usable & (not early)
            streak = np.where(eval_ok, np.where(out, streak + 1, 0), np.where(early, 0, streak))
            yellow = streak >= consec
            jump_now = eval_ok & jmp
            if confirm:
                # v0.2: el salto solo pasa a rojo si la lectura siguiente sigue fuera de la banda en la misma
                # direccion (un artefacto de sensor de un dia no confirma).
                red = eval_ok & out & (jprev != 0) & (jprev == sgn)
                if unconf_yellow:
                    yellow |= jump_now
            else:
                red = jump_now.copy()
            jprev = np.where(have, np.where(jump_now, sgn, 0), jprev).astype(np.int8)
            if k == "spo2":
                yellow |= have & usable & ((mean - x) >= cfg("yellow_extra.spo2_drop_points"))
            if k == "glucose":
                yellow |= have & ((x >= cfg("yellow_extra.glucose_yellow_high")) | (x < cfg("yellow_extra.glucose_yellow_low")))
            if k == "glucose":
                lim_hi = _opt(cfg, "absolute_red.glucose_gt", None)
                if lim_hi is not None:
                    red |= have & (x >= lim_hi)
            if k in ABS_YELLOW_LOW:
                lim = _opt(cfg, ABS_YELLOW_LOW[k], None)
                if lim is not None and days[t] > 0:
                    yellow |= have & (x < lim)
            if k in ABS_RED:
                key, kind = ABS_RED[k]
                lim = cfg(key)
                if k == "temp" and days[t] > early_n:
                    lim = temp_inflight  # None = en vuelo la temperatura solo se juzga contra la linea base
                if lim is not None:
                    over = have & ((x > lim) if kind == "gt" else (x < lim))
                    # v0.3: el limite de temperatura en vuelo exige `temp_consec` lecturas seguidas (una lectura suelta no basta)
                    need = temp_consec if (k == "temp" and days[t] > early_n) else 1
                    abs_streak = np.where(have, np.where(over, abs_streak + 1, 0), abs_streak)
                    red |= over & (abs_streak >= need)
            s = np.where(red, 2, np.where(yellow, 1, 0)).astype(np.int8)
            s = np.where(have, s, prev)
            S[:, t] = s
            # dias que no entran a la linea base: segun excl_mode, mas cualquier lectura con salto
            flagged[:, t] = ((s >= 1) if excl_mode == 1 else (s >= 2) if excl_mode == 2 else False) | jump_now
            prev = s
        status[k] = S
        bands[k] = (Bm, Blo, Bhi)

    # ejercicio: sesiones hechas en los ultimos 7 dias
    ex = _stack(daily, "exercise_min")[2]
    done = (np.nan_to_num(ex, nan=0.0) >= cfg("yellow_extra.exercise_session_min_done")).astype(int)
    flight = days > 0
    S_ex = np.zeros((M, T), dtype=np.int8)
    if cfg("mvp.include_exercise"):
        csum = np.cumsum(done * flight[None, :], axis=1)
        for t in range(T):
            if days[t] >= 7:
                n7 = csum[:, t] - (csum[:, t - 7] if t >= 7 else 0)
                S_ex[:, t] = np.where(n7 < cfg("yellow_extra.exercise_min_sessions_week"), 1, 0)
    status["exercise"] = S_ex

    # aptitud fisica: ultima prueba conocida (se arrastra hasta la siguiente)
    fit = _stack(daily, "fitness_pct_preflight")[2]
    S_fit = np.zeros((M, T), dtype=np.int8)
    last = np.full(M, np.nan)
    for t in range(T):
        if days[t] > 0:
            v = fit[:, t]
            last = np.where(np.isnan(v), last, v)
            S_fit[:, t] = np.where(last < cfg("absolute_red.fitness_lt_pct"), 2, 0)
    status["fitness"] = S_fit

    names = list(status)
    stack = np.stack([status[k] for k in names], axis=0)  # (K, M, T)
    n_yellow = np.sum(stack == 1, axis=0)
    overall = stack.max(axis=0)
    if cfg("general.two_yellow_to_red"):
        overall = np.where(n_yellow >= 2, 2, overall)

    rows = {"astronaut_id": np.repeat(ids, T), "mission_day": np.tile(days, M),
            "status": overall.reshape(-1).astype(int), "n_yellow": n_yellow.reshape(-1).astype(int)}
    if return_reasons:
        reasons = np.empty((M, T), dtype=object)
        for m in range(M):
            for t in range(T):
                r = [f"{k}:{'R' if stack[i, m, t] == 2 else 'Y'}" for i, k in enumerate(names) if stack[i, m, t] > 0]
                reasons[m, t] = ";".join(r)
        rows["reasons"] = reasons.reshape(-1)
    for k in names:
        rows[f"status_{k}"] = status[k].reshape(-1).astype(int)
    if return_bands:
        for k in active:
            Bm, Blo, Bhi = bands[k]
            rows[f"base_{k}"] = Bm.reshape(-1)
            rows[f"lo_{k}"] = Blo.reshape(-1)
            rows[f"hi_{k}"] = Bhi.reshape(-1)
    return pd.DataFrame(rows)
