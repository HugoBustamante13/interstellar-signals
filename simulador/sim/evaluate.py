#!/usr/bin/env python3
"""
Evaluacion sobre datos SINTETICOS:
  (1) verificacion de implementacion contra cifras publicadas: TODA CIRCULAR (derivas calibradas con esas cifras;
      DE de la linea base derivadas de los mismos percentiles). Prueba el codigo, no el realismo.
  (1b) validacion independiente, hold-out: valores absolutos en vuelo (holdout_targets.json) no usados para calibrar.
  (2) desempeno del semaforo contra las anomalias etiquetadas, (3) tabla de compromisos, (4) grilla, (5) ejercicio.
  (6) validacion independiente, robustez: el semaforo con deriva, ruido y magnitud de anomalias x0,5 y x1,5.

El simulador sirve para probar la LOGICA del semaforo con verdad conocida; NO es un modelo fisiologico validado.
La parte (2) mide el semaforo contra anomalias que inventamos nosotros: sirve para comparar
configuraciones y encontrar fallos de diseno, no para afirmar una sensibilidad clinica.
"""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import simulator as sim
import semaforo as sf

HERE = Path(__file__).resolve().parent
MERGE_GAP = 2  # dias: alertas separadas por <=2 dias se cuentan como un solo episodio


def episodes(mask, days):
    """Lista de (inicio, fin) de rachas True, uniendo huecos <= MERGE_GAP."""
    idx = np.where(mask)[0]
    if idx.size == 0:
        return []
    out, s, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if days[i] - days[prev] > MERGE_GAP + 1:
            out.append((days[s], days[prev]))
            s = i
        prev = i
    out.append((days[s], days[prev]))
    return out


def evaluate_semaforo(daily, anomalies, st, grace, level=1):
    """Metricas por astronauta-mision. level 1 = amarillo o peor, 2 = solo rojo.

    v0.2: un evento real cuenta como detectado solo si dentro de su ventana [inicio, fin + grace] aparece
    una alerta NUEVA: el estado pasa a >= level desde un nivel menor, o sube de nivel (amarillo -> rojo).
    Una alerta que ya estaba encendida antes del evento no cuenta como acierto.
    """
    df = daily.merge(st[["astronaut_id", "mission_day", "status"]], on=["astronaut_id", "mission_day"])
    health = anomalies[anomalies["is_health_event"]]
    art = anomalies[~anomalies["is_health_event"]]
    n_miss = df["astronaut_id"].nunique()
    fa, tot_ep = 0, 0
    fa_art = 0
    det_rows = []
    for aid, g in df[df["phase"] == "inflight"].groupby("astronaut_id"):
        days = g["mission_day"].values
        s = g["status"].values
        mask = s >= level
        prev = np.concatenate([[0], s[:-1]])
        onset = mask & (s > prev)
        eps = episodes(mask, days)
        hw = health[health["astronaut_id"] == aid]
        aw = art[art["astronaut_id"] == aid]
        truth_days = set(days[g["truth_fitness_lt80"].values])
        for (a, b) in eps:
            tot_ep += 1
            overlap = any((a <= r.end_day + grace) and (b >= r.start_day) for r in hw.itertuples()) \
                or any(a <= d <= b for d in truth_days)
            if not overlap:
                fa += 1
                if any(a <= r.start_day <= b for r in aw.itertuples()):
                    fa_art += 1
        for r in hw.itertuples():
            win = (days >= r.start_day) & (days <= r.end_day + grace)
            hit = np.where(win & onset)[0]
            det_rows.append({"type": r.type, "detected": hit.size > 0,
                             "already_on_at_start": bool(mask[win][0]) if win.any() else False,
                             "latency": (days[hit[0]] - r.start_day) if hit.size else np.nan})
    det = pd.DataFrame(det_rows)
    return {"missions": n_miss, "episodes": tot_ep, "false_episodes": fa, "false_per_mission": fa / n_miss,
            "false_from_artifact_per_mission": fa_art / n_miss, "detections": det}


def alert_fractions(daily, st):
    """Fraccion de dias de vuelo en alerta, en total y en dias limpios (sin ninguna anomalia ni artefacto)."""
    df = daily.merge(st, on=["astronaut_id", "mission_day"])
    f = df[df["phase"] == "inflight"]
    clean = f[(f["truth_anomaly_ids"] == "") & (~f["truth_fitness_lt80"])]
    out = {"frac_days_yellow_plus_total": f["status"].ge(1).mean(), "frac_days_red_total": f["status"].ge(2).mean(),
           "frac_days_yellow_plus_clean": clean["status"].ge(1).mean(), "frac_days_red_clean": clean["status"].ge(2).mean()}
    per = {}
    for c in [c for c in st.columns if c.startswith("status_")]:
        k = c[len("status_"):]
        per[k] = {"amarillo_o_peor_dias_limpios": round(float(clean[c].ge(1).mean()), 4),
                  "rojo_dias_limpios": round(float(clean[c].ge(2).mean()), 4)}
    return {k: round(float(v), 4) for k, v in out.items()}, per


def summarize_detection(det):
    g = det.groupby("type").agg(n=("detected", "size"), recall=("detected", "mean"),
                                latency_median_days=("latency", "median"))
    g["recall"] = g["recall"].round(3)
    return g


def false_episode_causes(daily, anomalies, st, grace):
    """Que indicadores aparecen en los episodios falsos (amarillo o peor)."""
    df = daily.merge(st[["astronaut_id", "mission_day", "status", "reasons"]], on=["astronaut_id", "mission_day"])
    health = anomalies[anomalies["is_health_event"]]
    cnt = {}
    n_fa = 0
    for aid, g in df[df["phase"] == "inflight"].groupby("astronaut_id"):
        days, s, rs = g["mission_day"].values, g["status"].values, g["reasons"].values
        hw = health[health["astronaut_id"] == aid]
        truth_days = set(days[g["truth_fitness_lt80"].values])
        for (a, b) in episodes(s >= 1, days):
            ov = any((a <= r.end_day + grace) and (b >= r.start_day) for r in hw.itertuples()) \
                or any(a <= d <= b for d in truth_days)
            if ov:
                continue
            n_fa += 1
            seen = set()
            for d, r in zip(days, rs):
                if a <= d <= b and r:
                    for tok in r.split(";"):
                        seen.add(tok)
            for tok in seen:
                cnt[tok] = cnt.get(tok, 0) + 1
    return n_fa, pd.Series(cnt, name="episodios_falsos").sort_values(ascending=False)


# ----------------------------------------------------------------------------------------------
def cosinor_amp(hours, y):
    X = np.column_stack([np.ones_like(hours), np.cos(2 * np.pi * hours / 24), np.sin(2 * np.pi * hours / 24)])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(np.hypot(b[1], b[2]))


def validate_simulator(P, seed):
    rows = []

    def add(item, target, source, simulated, tol, circular, unit="", kind=None):
        # Correccion 14 nov: NINGUN chequeo de esta funcion es independiente. Las derivas se calibraron con estas
        # cifras y las DE de la linea base se derivaron de los mismos percentiles P5/P95 que se comparan aqui.
        # Solo prueban que el codigo implementa el modelo. La validacion independiente esta en holdout_checks().
        ok = abs(simulated - target) <= tol
        rows.append({"item": item, "target": target, "source": source, "simulated": round(float(simulated), 2),
                     "tolerance": tol, "unit": unit, "within_tolerance": bool(ok),
                     "kind": kind or "verificacion de implementacion (circular)"})

    res = sim.simulate_cohort(P, 100, 100, seed, with_intraday=False)
    d = res["daily"]
    clean = d[d["truth_anomaly_ids"] == ""]
    fl = clean[clean["phase"] == "inflight"]
    pre = clean[clean["phase"] == "preflight"]
    men = lambda x: x[x["sex"] == "M"]

    # temperatura
    base = pre.groupby("astronaut_id")["temp_c"].mean()
    late = fl[(fl.mission_day >= 76) & (fl.mission_day <= 150)].groupby("astronaut_id")["temp_c"].mean()
    add("Temperatura en reposo, cambio dias 76-150 vs previo", 1.01, "Stahn et al., Sci Rep 2017 (+1,01 C)",
        (late - base).mean(), 0.15, True, "C")
    mid = fl[(fl.mission_day >= 70) & (fl.mission_day <= 80)].groupby("astronaut_id")["temp_c"].mean()
    add("Temperatura: fraccion del cambio final ya alcanzada hacia el dia 75", 0.95, "Stahn 2017 (meseta tras ~75 dias)",
        ((mid - base).mean()) / ((late - base).mean()), 0.08, True, "fraccion")
    # presion (hombres)
    for col, tgt in (("bp_sys_mmhg", -8.0), ("bp_dia_mmhg", -9.0)):
        b = men(pre).groupby("astronaut_id")[col].mean()
        l = men(fl)[men(fl).mission_day >= 40].groupby("astronaut_id")[col].mean()
        add(f"{col}, hombres, cambio dias 40-180 vs previo", tgt, "Norsk et al., J Physiol 2015",
            (l - b).mean(), 2.0, True, "mmHg")
    # presion (mujeres, cambio relativo igual al de los hombres: SUPUESTO, no medido)
    b = pre[pre.sex == "F"].groupby("astronaut_id")["bp_sys_mmhg"].mean()
    l = fl[(fl.sex == "F") & (fl.mission_day >= 40)].groupby("astronaut_id")["bp_sys_mmhg"].mean()
    add("bp_sys, mujeres, cambio (supuesto: mismo cambio relativo que hombres; sin datos publicados)",
        -8.0 * P("bp.sys_mean_F") / P("bp.sys_mean_M"), "supuesto del equipo (sin dato de mujeres)",
        (l - b).mean(), 2.0, True, "mmHg")
    # FC en reposo sin cambio
    for sx in ("F", "M"):
        b = pre[pre.sex == sx].groupby("astronaut_id")["hr_rest_bpm"].mean()
        l = fl[(fl.sex == sx) & (fl.mission_day >= 40)].groupby("astronaut_id")["hr_rest_bpm"].mean()
        add(f"FC en reposo, cambio dias 40-180 vs previo ({sx})", 0.0, "Norsk 2015 (FC sin cambio, 8 hombres)",
            (l - b).mean(), 1.5, True, "lpm")
    # sueno
    dec = {a["astronaut_id"] for a in res["astronauts"] if a["sleep_direction"] == "decrease"}
    add("Fraccion de astronautas que duermen menos en vuelo", 0.70, "Otsuka et al., Sci Rep 2021 (7 de 10)",
        len(dec) / len(res["astronauts"]), 0.10, True, "fraccion")
    sl = clean.copy()
    sl["dec"] = sl["astronaut_id"].isin(dec)
    b = sl[(sl.phase == "preflight") & sl.dec].groupby("astronaut_id")["sleep_h"].mean()
    e = sl[(sl.mission_day >= 19) & (sl.mission_day <= 23) & sl.dec].groupby("astronaut_id")["sleep_h"].mean()
    l = sl[(sl.mission_day >= 140) & (sl.mission_day <= 150) & sl.dec].groupby("astronaut_id")["sleep_h"].mean()
    add("Sueno, quienes duermen menos: cambio ~dia 21", -45.1, "Otsuka 2021 (454,0 a 408,9 min)",
        (e - b).mean() * 60, 12.0, True, "min")
    add("Sueno, quienes duermen menos: cambio ~dia 143", -72.4, "Otsuka 2021 (454,0 a 381,6 min)",
        (l - b).mean() * 60, 12.0, True, "min")
    # aptitud fisica
    last = d[(d.mission_day == 180)]
    truth_loss = []
    for a in res["astronauts"]:
        truth_loss.append(a["fitness_loss"] * (1 - np.exp(-180 / P("exercise.fitness_tau_days"))))
    truth_loss = np.array(truth_loss)
    add("Perdida media de aptitud fisica al dia 180 (valor real simulado)", 0.11 * (1 - np.exp(-180 / 60)),
        "NASA HRP R09 (10-12 %) escalada por el avance al dia 180", truth_loss.mean(), 0.02, True, "fraccion")
    add("Fraccion con perdida real > 20 % (de la perdida final)", 0.12, "NASA HRP R09 (12-38 % segun metodo, extremo inferior)",
        float(np.mean([a["fitness_loss"] > 0.20 for a in res["astronauts"]])), 0.06, True, "fraccion")
    # distribuciones de la linea base: CIRCULAR (las DE se derivaron de estos mismos percentiles)
    for sx in ("F", "M"):
        x = pre[pre.sex == sx]["hr_rest_bpm"].dropna()
        add(f"FC en reposo previo, P5 ({sx})", P(f"hr.p5_{sx}"), "NHSR 41 (terrestre)", np.percentile(x, 5), 5.0, False, "lpm")
        add(f"FC en reposo previo, P95 ({sx})", P(f"hr.p95_{sx}"), "NHSR 41 (terrestre)", np.percentile(x, 95), 5.0, False, "lpm")
        x = pre[pre.sex == sx]["bp_sys_mmhg"].dropna()
        add(f"PA sistolica previa, P5 ({sx})", P(f"bp.sys_p5_{sx}"), "NHSR 35 (terrestre)", np.percentile(x, 5), 5.0, False, "mmHg")
        add(f"PA sistolica previa, P95 ({sx})", P(f"bp.sys_p95_{sx}"), "NHSR 35 (terrestre)", np.percentile(x, 95), 5.0, False, "mmHg")
    x = pre["temp_c"].dropna()
    add("Temperatura previa, P2,5", 35.7, "Obermeyer, BMJ 2017 (95 % entre 35,7 y 37,3)", np.percentile(x, 2.5), 0.2, False, "C")
    add("Temperatura previa, P97,5", 37.3, "Obermeyer, BMJ 2017", np.percentile(x, 97.5), 0.2, False, "C")
    t75 = fl[(fl.mission_day >= 70) & (fl.mission_day <= 80)]["temp_c"].mean() - pre["temp_c"].mean()
    add("Temperatura: cambio dias 70-80 vs previo (Stahn Fig. 1a: ~36,3 -> ~37,7, leido de figura)", 1.4,
        "Stahn et al., Sci Rep 2017, Fig. 1a (sensor de frente; lectura de figura +/-0,1 C)", t75, 0.4, False, "C",
        kind="contraste con la misma fuente de la calibracion (no independiente)")
    late_all = fl[fl.mission_day >= 76].groupby("astronaut_id")["temp_c"].mean()
    add("Fraccion de astronautas SANOS con temperatura media > 38,0 C en dias 76-180 (dias sin anomalia)", 0.0,
        "diagnostico: 38,0 C = fiebre oral en Tierra (MSD); debe ser ~0 si el limite rojo fijo fuera valido en vuelo",
        float((late_all > 38.0).mean()), 0.05, False, "fraccion", kind="diagnostico del semaforo (no es validacion)")
    add("SpO2: fraccion de lecturas perdidas", P("spo2.missing_prob"), "supuesto (Hearn 2023 midio 12-82 % con movimiento)",
        d["spo2_pct"].isna().mean() - d["bp_sys_mmhg"].isna().mean(), 0.03, True, "fraccion")

    # amplitud circadiana (necesita la serie intradiaria)
    res2 = sim.simulate_cohort(P, 20, 20, seed + 7, with_intraday=True)
    amps = {"pre": [], "d21": [], "late": []}
    for it in res2["intraday"]:
        n = it["n_days"]
        step = it["step_minutes"]
        spd = 24 * 60 // step
        hr = it["hr_bpm"].reshape(n, spd)
        ctx = it["context"].reshape(n, spd)
        pre_n = -it["first_mission_day"]
        for key, (lo, hi) in {"pre": (0, pre_n), "d21": (pre_n + 15, pre_n + 25), "late": (pre_n + 140, pre_n + 150)}.items():
            hh = np.tile(np.arange(spd) * step / 60.0, hi - lo)
            y = hr[lo:hi].reshape(-1)
            m = ctx[lo:hi].reshape(-1) != 2
            amps[key].append(cosinor_amp(hh[m], y[m]))
    add("Amplitud circadiana de la FC, previo al vuelo", 10.90, "Otsuka 2021", np.mean(amps["pre"]), 1.0, True, "lpm")
    add("Amplitud circadiana de la FC, ~dia 21", 12.54, "Otsuka 2021", np.mean(amps["d21"]), 1.2, True, "lpm")
    add("Amplitud circadiana de la FC, ~dia 143", 12.77, "Otsuka 2021", np.mean(amps["late"]), 1.2, True, "lpm")
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
# VALIDACION INDEPENDIENTE
# ----------------------------------------------------------------------------------------------
def holdout_checks(P, seed, path=HERE / "holdout_targets.json"):
    """(1) Hold-out: valores ABSOLUTOS en vuelo de la investigacion (vacio 1) que NO se usan para calibrar.

    Los objetivos viven en holdout_targets.json, separados de sim_params.json, para que nadie los use al calibrar.
    Lo que es fuera de muestra es el NIVEL absoluto (la linea base sale de NHSR, no de estos estudios). El CAMBIO
    -8/-9 mmHg si se calibro con Norsk 2015, asi que esa parte no es independiente. Se reporta la diferencia, no
    un aprobado: la medicion de la fuente (24 h ambulatoria, otra edad) no es la del simulador (reposo 08:30).
    """
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    targets = spec["targets"]
    res = sim.simulate_cohort(P, 100, 100, seed + 31, with_intraday=True)
    d = res["daily"]
    fl = d[(d["phase"] == "inflight") & (d["truth_anomaly_ids"] == "")]
    sleep_hr = {}
    for it in res["intraday"]:
        spd = 1440 // it["step_minutes"]
        hr = it["hr_bpm"].reshape(it["n_days"], spd)
        ctx = it["context"].reshape(it["n_days"], spd)
        pre_n = -it["first_mission_day"]
        sleep_hr[it["astronaut_id"]] = float(hr[pre_n + 84:][ctx[pre_n + 84:] == 1].mean())
    rows = []
    for t in targets:
        sel = fl[(fl["mission_day"] >= t["days"][0]) & (fl["mission_day"] <= t["days"][1])]
        if t["sex"] != "all":
            sel = sel[sel["sex"] == t["sex"]]
        if t["column"] == "sleep_hr":
            ids = set(sel["astronaut_id"])
            per = pd.Series({k: v for k, v in sleep_hr.items() if k in ids})
        else:
            per = sel.groupby("astronaut_id")[t["column"]].mean()
        sim_mean, sim_sd = float(per.mean()), float(per.std(ddof=1))
        tv = t["value"]
        row = {"item": t["item"], "target": tv, "target_between_sd": t.get("between_sd"), "unit": t["unit"],
               "simulated_mean": round(sim_mean, 2), "simulated_between_sd": round(sim_sd, 2),
               "diff": None if tv is None else round(sim_mean - tv, 2),
               "diff_in_target_sd": None if (tv is None or not t.get("between_sd")) else round((sim_mean - tv) / t["between_sd"], 2),
               "used_for_calibration": False, "estado": t["estado"], "etiqueta": t["etiqueta"],
               "source": t["source"], "measurement_note": t["note"]}
        rows.append(row)
    return pd.DataFrame(rows)


ROBUST_GROUPS = {
    "deriva": ["temp.drift_mean", "bp.drift_sys_mmhg_M", "bp.drift_dia_mmhg_M", "sleep.decrease_total_h",
               "sleep.increase_total_h"],
    "ruido": ["hr.day_noise_sd", "bp.day_noise_sd_sys", "bp.day_noise_sd_dia", "spo2.within_sd", "temp.within_sd",
              "glucose.within_sd", "sleep.within_sd_h", "mood.within_sd", "hr_circ.intraday_sd"],
    # magnitud de los eventos de SALUD (no tasas ni duraciones; los artefactos de sensor no se tocan)
    "magnitud_anomalias": None,
}


def robustness(params_path, cfg, seed, n_per_sex, grace, factors=(0.5, 1.5)):
    """(2) Robustez del semaforo: se escala cada grupo de parametros del SIMULADOR x0,5 y x1,5 (uno a la vez),
    se regenera la cohorte con la misma semilla y se mide el semaforo v0.2 sin cambiar sus umbrales."""
    base_P = sim.Params(params_path)
    anom_keys = [f"anomaly.{k}" for k in base_P.raw["anomaly"]
                 if not k.startswith("artifact") and not any(x in k for x in ("_rate", "_days"))]
    groups = {**ROBUST_GROUPS, "magnitud_anomalias": anom_keys}
    rows = []
    for gname, keys in [("base", [])] + list(groups.items()):
        for f in ([1.0] if gname == "base" else factors):
            P = sim.Params(params_path)
            for k in keys:
                P.set(k, P(k) * f)
            res = sim.simulate_cohort(P, n_per_sex, n_per_sex, seed, with_intraday=False)
            r = score(res["daily"], res["anomalies"], cfg, grace)
            rows.append({"grupo": gname, "factor": f, "n_parametros": len(keys), **r})
            print(gname, f, {k: r[k] for k in list(r)[:4]})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------
V01 = dict(general__baseline_window_days=14, general__min_window_points=7, general__exclude_flagged_from_baseline=1,
           general__prediction_interval=0, general__band_sd=2.0, general__jump_sd=3.0, general__jump_confirm=0,
           absolute_red__temp_gt_inflight=38.0, absolute_red__temp_inflight_consecutive_days=1, absolute_yellow__hr_rest_lt=None,
           yellow_extra__exercise_min_sessions_week=5)
TRADEOFF_VARIANTS = [
    # (nombre, cambios sobre la configuracion v0.2 de semaforo_config.json)
    ("A. v0.1 original", V01),
    ("B. A + temperatura solo contra linea base en vuelo", {**V01, "absolute_red__temp_gt_inflight": None}),
    ("C. B + salto confirmado al dia siguiente", {**V01, "absolute_red__temp_gt_inflight": None, "general__jump_confirm": 1}),
    ("D. C + linea base 28 d sin sacar dias marcados + banda de prediccion",
     {**V01, "absolute_red__temp_gt_inflight": None, "general__jump_confirm": 1, "general__baseline_window_days": 28,
      "general__min_window_points": 14, "general__exclude_flagged_from_baseline": 0, "general__prediction_interval": 1}),
    ("E. D + banda 2,5 + salto 4 + ejercicio <3", dict(absolute_yellow__hr_rest_lt=None, absolute_red__temp_gt_inflight=None)),
    ("F. v0.2 = E + FC < 50 amarillo (sin rojo de temperatura en vuelo)", dict(absolute_red__temp_gt_inflight=None)),
    ("G. F + rojo fijo 38,5 C en vuelo con 1 lectura (supuesto) + meseta recortada en 38,0 C", dict(absolute_red__temp_inflight_consecutive_days=1)),
    ("H. v0.3 PROPUESTA = G con 2 lecturas seguidas sobre 38,5 C", dict()),
    ("v0.3 + PA sistolica < 90 amarillo (ESC, sin verificar)", dict(absolute_yellow__bp_sys_lt=90)),
    ("v0.3 con rojo fijo 38,0 C en vuelo (2 lecturas)", dict(absolute_red__temp_gt_inflight=38.0)),
    ("v0.3 con rojo fijo 38,5 C en vuelo (3 lecturas)", dict(absolute_red__temp_inflight_consecutive_days=3)),
    ("v0.3 con rojo fijo 39,0 C en vuelo (2 lecturas)", dict(absolute_red__temp_gt_inflight=39.0)),
    ("v0.3 con ejercicio <4", dict(yellow_extra__exercise_min_sessions_week=4)),
    ("v0.3 mas sensible: banda 2,0 + salto 3", dict(general__band_sd=2.0, general__jump_sd=3.0)),
    ("v0.3 menos sensible: banda 3,0", dict(general__band_sd=3.0)),
    ("v0.3 sin 'dos amarillos = rojo'", dict(general__two_yellow_to_red=0)),
    ("DIAGNOSTICO v0.3 sin rojo FC > 100", dict(absolute_red__hr_rest_gt=999)),
    ("DIAGNOSTICO v0.3 sin amarillo por caida de SpO2 >= 3", dict(yellow_extra__spo2_drop_points=99)),
    ("DIAGNOSTICO v0.3 solo linea base personal (sin reglas absolutas ni ejercicio)",
     dict(absolute_yellow__hr_rest_lt=None, absolute_red__hr_rest_gt=999, yellow_extra__spo2_drop_points=99,
          mvp__include_exercise=0, absolute_red__fitness_lt_pct=0, absolute_red__temp_gt_inflight=None)),
]


def score(daily, anomalies, cfg, grace):
    s = sf.run_semaforo(daily, cfg, return_bands=False, return_reasons=False)
    a = evaluate_semaforo(daily, anomalies, s, grace, level=1)
    b = evaluate_semaforo(daily, anomalies, s, grace, level=2)
    fr, _ = alert_fractions(daily, s)
    det = a["detections"]
    det = det[det["type"] != "glucose_high"]
    detr = b["detections"]
    detr = detr[detr["type"] != "glucose_high"]
    return {"falsos_amarillo_o_peor_por_mision": round(a["false_per_mission"], 2),
            "falsos_rojo_por_mision": round(b["false_per_mission"], 2),
            "recall_alerta_nueva_amarillo_o_peor": round(float(det["detected"].mean()), 3),
            "recall_alerta_nueva_rojo": round(float(detr["detected"].mean()), 3),
            "latencia_mediana_d": float(det["latency"].median()),
            "frac_eventos_con_alerta_ya_encendida": round(float(det["already_on_at_start"].mean()), 3),
            "frac_dias_alerta_total": fr["frac_days_yellow_plus_total"],
            "frac_dias_alerta_limpios": fr["frac_days_yellow_plus_clean"],
            "frac_dias_rojo_limpios": fr["frac_days_red_clean"]}


def run(args):
    P = sim.Params(args.params)
    cfg = sf.Config(args.config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    grace = int(cfg("evaluation.grace_days"))

    if not args.skip_validation:
        print("1) Verificacion de implementacion (CIRCULAR, no es validacion) ...")
        val = validate_simulator(P, args.eval_seed)
        val.to_csv(out / "validation_checks.csv", index=False)
        print(val[["item", "target", "simulated", "unit", "within_tolerance", "kind"]].to_string())
        print("\n1b) Validacion independiente: hold-out con valores absolutos en vuelo (no usados para calibrar) ...")
        ho = holdout_checks(P, args.eval_seed)
        ho.to_csv(out / "holdout_checks.csv", index=False)
        print(ho[["item", "target", "simulated_mean", "diff", "diff_in_target_sd", "etiqueta"]].to_string())

    print("\n2) Evaluacion del semaforo (configuracion de semaforo_config.json) ...")
    res = sim.simulate_cohort(P, args.n_per_sex, args.n_per_sex, args.eval_seed + 100, with_intraday=False)
    daily, anomalies = res["daily"], res["anomalies"]
    st = sf.run_semaforo(daily, cfg, return_bands=False, return_reasons=True)
    m1 = evaluate_semaforo(daily, anomalies, st, grace, level=1)
    m2 = evaluate_semaforo(daily, anomalies, st, grace, level=2)
    rec1 = summarize_detection(m1["detections"]).rename(columns={"recall": "recall_alerta_nueva_amarillo_o_peor", "latency_median_days": "latencia_mediana_d"})
    rec2 = summarize_detection(m2["detections"])[["recall"]].rename(columns={"recall": "recall_alerta_nueva_rojo"})
    rec = rec1.join(rec2)
    rec.to_csv(out / "semaforo_recall_by_type.csv")
    n_fa, causes = false_episode_causes(daily, anomalies, st, grace)
    causes.to_csv(out / "semaforo_false_episode_causes.csv")
    fr, per = alert_fractions(daily, st)
    summary = {"data_origin": "synthetic",
               "nota": "Evaluado contra anomalias SINTETICAS inventadas por el equipo: sirve para comparar configuraciones, no para afirmar sensibilidad clinica.",
               "misiones_evaluadas": m1["missions"],
               "episodios_falsos_por_mision_amarillo_o_peor": round(m1["false_per_mission"], 2),
               "episodios_falsos_por_mision_solo_rojo": round(m2["false_per_mission"], 2),
               "falsos_por_mision_que_incluyen_un_artefacto_amarillo_o_peor": round(m1["false_from_artifact_per_mission"], 2),
               **fr, "por_indicador_dias_limpios": per,
               "dias_de_vuelo": int(P("mission.duration_days")), "grace_days": grace,
               "metrica_recall": "alerta nueva (cambio a >= nivel o subida de nivel) dentro de [inicio, fin + grace]"}
    (out / "semaforo_eval_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(rec.to_string())
    print("Causas (indicador:nivel) de los episodios falsos amarillo+:\n", causes.to_string())

    print("\n3) Tabla de compromisos (variantes nombradas) ...")
    rows = []
    for name, kw in TRADEOFF_VARIANTS:
        r = score(daily, anomalies, cfg.copy_with(**kw), grace)
        rows.append({"variante": name, **r})
        print(name, r)
    tt = pd.DataFrame(rows)
    tt.to_csv(out / "tradeoff_table.csv", index=False)

    print("\n4) Grilla de sensibilidad sobre v0.2 (banda, dias seguidos, salto, confirmacion) ...")
    grid = []
    for band_sd, consec, jump, conf in itertools.product([2.0, 2.5, 3.0], [2, 3, 4], [3.0, 4.0, 99.0], [0, 1]):
        c = cfg.copy_with(general__band_sd=band_sd, general__consecutive_days_yellow=consec,
                          general__jump_sd=jump, general__jump_confirm=conf)
        grid.append({"band_sd": band_sd, "consecutive_days_yellow": consec, "jump_sd": jump, "jump_confirm": conf,
                     **score(daily, anomalies, c, grace)})
    g = pd.DataFrame(grid)
    g.to_csv(out / "sensitivity_grid.csv", index=False)
    print(g.to_string())

    print("\n5) Variante de ejercicio (sesiones minimas por semana) ...")
    ex_rows = []
    for k in (3, 4, 5):
        c = cfg.copy_with(yellow_extra__exercise_min_sessions_week=k)
        s = sf.run_semaforo(daily, c, return_bands=False, return_reasons=False)
        a = evaluate_semaforo(daily, anomalies, s, grace, level=1)
        dd = a["detections"]
        r = float(dd[dd["type"] == "exercise_dropout"]["detected"].mean())
        fr_k, per_k = alert_fractions(daily, s)
        ex_rows.append({"exercise_min_sessions_week": k, "false_episodes_per_mission": round(a["false_per_mission"], 2),
                        "ejercicio_amarillo_dias_limpios": per_k["exercise"]["amarillo_o_peor_dias_limpios"],
                        "recall_exercise_dropout": round(r, 3)})
    exg = pd.DataFrame(ex_rows)
    exg.to_csv(out / "sensitivity_exercise.csv", index=False)
    print(exg.to_string())

    if not args.skip_robustness:
        print("\n6) Validacion independiente: robustez del semaforo (simulador x0,5 / x1,5) ...")
        rb = robustness(args.params, cfg, args.eval_seed + 200, args.n_per_sex, grace)
        rb.to_csv(out / "robustness.csv", index=False)
        print(rb.to_string())
    return summary, rec, causes, tt, g, exg


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default=str(HERE / "sim_params.json"))
    ap.add_argument("--config", default=str(HERE / "semaforo_config.json"))
    ap.add_argument("--out", default=str(HERE.parent / "out" / "evaluation"))
    ap.add_argument("--eval-seed", type=int, default=1000)
    ap.add_argument("--n-per-sex", type=int, default=100)
    ap.add_argument("--skip-validation", action="store_true")
    ap.add_argument("--skip-robustness", action="store_true")
    run(ap.parse_args())
