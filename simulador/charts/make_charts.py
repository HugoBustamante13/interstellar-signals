#!/usr/bin/env python3
"""Graficas de tendencia por indicador (DATOS SINTETICOS). Una figura por indicador, un panel por astronauta.

Cada panel: serie diaria, linea base personal movil, banda personal, ancla previa al vuelo (zona gris),
eventos de salud etiquetados (franjas naranjas, verdad del simulador), artefactos de sensor (x gris,
NO son eventos de salud) y una franja con el estado del semaforo de ese indicador.

Uso:  python3 charts/make_charts.py            (lee out/, escribe charts/*.png)
Paleta validada con el skill dataviz (validate_palette.js): serie #2a78d6, eventos #eb6834.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT, CH = ROOT / "out", ROOT / "charts"
CFG = json.loads((ROOT / "sim" / "semaforo_config.json").read_text(encoding="utf-8"))
BAND = CFG["general"]["band_sd"][0]

SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
SERIES, EVENT = "#2a78d6", "#eb6834"
BAND_FILL = "#cde2fb"
STATUS = {0: "#0ca30c", 1: "#fab219", 2: "#d03b3b"}
STATUS_LBL = {0: "verde", 1: "amarillo", 2: "rojo"}
EVENT_ES = {"infection": "infección", "sleep_loss": "falta de sueño", "bp_spike": "pico de PA",
            "spo2_dip": "caída de SpO2", "mood_low": "ánimo bajo", "exercise_dropout": "sin ejercicio",
            "glucose_high": "glucosa alta"}

SPECS = [
    # key, columna, titulo, unidad, eventos que afectan, indicador de artefacto, nota
    ("hr_rest", "hr_rest_bpm", "FC en reposo", "lpm", ["infection", "sleep_loss", "bp_spike", "spo2_dip"], "hr_rest",
     "Rojo absoluto > 100 lpm (AHA); amarillo < 50 lpm (ACC/AHA/HRS 2018)."),
    ("bp_sys", "bp_sys_mmhg", "Presión arterial sistólica", "mmHg", ["bp_spike"], "bp_sys",
     "Rojo absoluto > 180 mmHg (AHA 2025). Cambio en vuelo: Norsk 2015 (hombres); mujeres = supuesto."),
    ("bp_dia", "bp_dia_mmhg", "Presión arterial diastólica", "mmHg", ["bp_spike"], None,
     "Rojo absoluto > 120 mmHg (AHA 2025). Cambio en vuelo: Norsk 2015 (hombres); mujeres = supuesto."),
    ("spo2", "spo2_pct", "SpO2", "%", ["spo2_dip"], "spo2",
     "Rojo < 90 % (Open Critical Care); amarillo si cae >= 3 puntos (BTS 2017)."),
    ("temp", "temp_c", "Temperatura (escala oral)", "C", ["infection"], "temp",
     "Deriva normal en vuelo +1,01 °C (Stahn 2017). Rojo fijo 38,0 °C los primeros 14 días; después 38,5 °C en 2 lecturas seguidas (supuesto del equipo)."),
    ("glucose", "glucose_mgdl", "Glucosa en ayunas (manual semanal)", "mg/dl", ["glucose_high"], None,
     "SUPUESTO DEL EQUIPO: parámetros sin respaldo publicado. Fuera del semáforo mínimo."),
    ("sleep", "sleep_h", "Horas de sueño", "h", ["infection", "sleep_loss", "mood_low"], None,
     "Caída en vuelo: Otsuka 2021 (7 de 10 durmieron menos). Alarma solo si baja."),
    ("mood", "mood_1_5", "Estado de ánimo (1-5)", "puntaje", ["infection", "sleep_loss", "mood_low"], None,
     "SUPUESTO DEL EQUIPO: escala y parámetros sin respaldo publicado. Se juzga contra la línea base personal."),
    ("exercise", "exercise_min", "Ejercicio completado", "min/dia", ["exercise_dropout", "infection"], None,
     "Prescrito: 150 min, 6 días/semana (Guilliams, NTRS). Amarillo: < 3 sesiones en 7 días (supuesto)."),
]


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8, length=0)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def synthetic_tag(fig):
    fig.text(0.995, 0.995, "DATOS SINTÉTICOS", ha="right", va="top", fontsize=10, fontweight="bold",
             color="#ffffff", bbox=dict(boxstyle="round,pad=0.35", fc=INK, ec="none"))


def plot_indicator(spec, daily, sem, anom):
    key, col, title, unit, ev_types, art_ind, note = spec
    ids = list(dict.fromkeys(daily["astronaut_id"]))
    n = len(ids)
    H = 2.35 * n + 1.8
    fig = plt.figure(figsize=(11, H), facecolor=SURF)
    gs = fig.add_gridspec(n * 2, 1, height_ratios=[1, 0.09] * n, hspace=0.0,
                          left=0.07, right=0.985, top=1 - 0.95 / H, bottom=1.05 / H)
    status_col = f"status_{key}"
    first_ax = None
    for i, aid in enumerate(ids):
        ax = fig.add_subplot(gs[2 * i], sharex=first_ax)
        sx = fig.add_subplot(gs[2 * i + 1], sharex=ax)
        first_ax = first_ax or ax
        style(ax)
        d = daily[daily.astronaut_id == aid].sort_values("mission_day")
        s = sem[sem.astronaut_id == aid].sort_values("mission_day")
        x = d["mission_day"].values
        y = d[col].values
        ax.axvspan(x.min() - 0.5, 0, color="#f0efec", lw=0)
        ax.axvline(0, color=MUTED, lw=0.8)
        a = anom[(anom.astronaut_id == aid) & (anom.type.isin(ev_types))]
        last_lbl = {}
        for r in a.sort_values("start_day").itertuples():
            ax.axvspan(r.start_day - 0.5, r.end_day + 0.5, color=EVENT, alpha=0.22, lw=0)
            # etiquetas que se pisarian: se apilan en otra altura
            lvl = 0
            while any(abs(r.end_day - d0) < 14 for d0 in last_lbl.get(lvl, [])):
                lvl += 1
            last_lbl.setdefault(lvl, []).append(r.end_day)
            near_end = r.end_day > daily.mission_day.max() - 16
            ax.text(r.start_day - 1 if near_end else r.end_day + 1, 0.04 + 0.11 * lvl, EVENT_ES[r.type],
                    transform=ax.get_xaxis_transform(), ha="right" if near_end else "left", va="bottom", fontsize=6.5, color=INK2,
                    bbox=dict(fc=SURF, ec="none", alpha=0.8, pad=0.8))
        if f"base_{key}" in s:
            b, lo, hi = s[f"base_{key}"].values, s[f"lo_{key}"].values, s[f"hi_{key}"].values
            lo = np.where(np.isnan(lo), 2 * b - hi, lo)
            hi = np.where(np.isnan(hi), 2 * b - lo, hi)
            xs = s["mission_day"].values
            ax.fill_between(xs, lo, hi, color=BAND_FILL, lw=0, step="mid")
            ax.plot(xs, b, color=INK2, lw=1.0, ls=(0, (4, 2)))
        if key == "exercise":
            ax.bar(x, np.nan_to_num(y), width=0.8, color=SERIES, lw=0)
            fit = d[["mission_day", "fitness_pct_preflight"]].dropna()
            fit = fit[fit.mission_day > 0]
            for r in fit.itertuples():
                ax.text(r.mission_day, 0.97, f"aptitud {r.fitness_pct_preflight:.0f} %",
                        transform=ax.get_xaxis_transform(), ha="right" if r.mission_day > x.max() - 10 else "center", va="top", fontsize=6.5, color=INK,
                        bbox=dict(fc=SURF, ec="none", alpha=0.85, pad=0.8))
        elif key == "glucose":
            m = ~np.isnan(y)
            ax.plot(x[m], y[m], color=SERIES, lw=2, marker="o", ms=4, mfc=SERIES, mec=SURF, mew=1)
            for lim, lbl in ((126, "126 (ADA, en ayunas)"), (70, "70 (ADA nivel 1)")):
                ax.axhline(lim, color=MUTED, lw=0.8, ls=":")
                ax.text(x.max(), lim, lbl + " ", fontsize=6.5, color=INK2, va="bottom", ha="right")
        else:
            ax.plot(x, y, color=SERIES, lw=1.6)
        if art_ind:
            aa = anom[(anom.astronaut_id == aid) & (anom.type == "sensor_artifact") & (anom.get("indicator") == art_ind)]
            for r in aa.itertuples():
                v = d.loc[d.mission_day == r.start_day, col]
                if len(v) and not np.isnan(v.values[0]):
                    ax.plot(r.start_day, v.values[0], marker="x", ms=8, mew=2, color=INK2, zorder=5)
        sex = d["sex"].iloc[0]
        ax.text(0.003, 0.96, f"{aid} ({sex})", transform=ax.transAxes, fontsize=8.5, fontweight="bold",
                color=INK, va="top", bbox=dict(fc=SURF, ec="none", alpha=0.85, pad=1.5))
        ax.set_ylabel(unit, fontsize=8, color=INK2)
        plt.setp(ax.get_xticklabels(), visible=False)
        # franja del semaforo
        sx.set_yticks([])
        for sp in sx.spines.values():
            sp.set_visible(False)
        sx.tick_params(colors=INK2, labelsize=8, length=0)
        if status_col in s:
            st = s[s.mission_day > 0]
            for r in st.itertuples():
                sx.axvspan(r.mission_day - 0.5, r.mission_day + 0.5, color=STATUS[getattr(r, status_col)], lw=0)
        else:
            sx.text(0.5, 0.5, "fuera del semáforo mínimo", transform=sx.transAxes, ha="center", va="center",
                    fontsize=6.5, color=MUTED)
        if i < n - 1:
            plt.setp(sx.get_xticklabels(), visible=False)
    first_ax.set_xlim(daily.mission_day.min() - 0.5, daily.mission_day.max() + 0.5)
    sx.set_xlabel("día de misión (negativo = previo al vuelo; no existe el día 0)", fontsize=8, color=INK2)
    fig.text(0.07, 1 - 0.22 / H, f"{title} - tendencia por astronauta", fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.07, 1 - 0.52 / H, note, fontsize=8, color=INK2, va="top")
    if key == "exercise":
        handles = [Patch(fc=SERIES, label="minutos completados"), Patch(fc="#f0efec", label="previo al vuelo")]
    else:
        handles = [Line2D([], [], color=SERIES, lw=2, label="lectura diaria")]
        if key != "glucose":
            handles += [Line2D([], [], color=INK2, lw=1, ls=(0, (4, 2)), label="línea base personal (28 d)"),
                        Patch(fc=BAND_FILL, label=f"banda personal (±{BAND:g} DE)")]
        handles.append(Patch(fc="#f0efec", label="ancla previa al vuelo"))
    handles += [
               Patch(fc=EVENT, alpha=0.4, label="evento de salud (etiqueta)")]
    if art_ind:
        handles.append(Line2D([], [], color=INK2, marker="x", lw=0, ms=7, mew=2, label="artefacto de sensor"))
    if key != "glucose":
        handles += [Patch(fc=STATUS[k], label=f"semáforo: {STATUS_LBL[k]}") for k in (0, 1, 2)]
    fig.legend(handles=handles, loc="lower center", ncol=5 if len(handles) <= 8 else 5, fontsize=7.5,
               frameon=False, bbox_to_anchor=(0.53, 0.004), labelcolor=INK2)
    synthetic_tag(fig)
    path = CH / f"tendencia_{key}_synthetic.png"
    fig.savefig(path, dpi=130, facecolor=SURF)
    plt.close(fig)
    return path


def main():
    daily = pd.read_csv(OUT / "mission_synthetic_daily.csv")
    sem = pd.read_csv(OUT / "mission_synthetic_semaforo.csv")
    anom = pd.read_csv(OUT / "mission_synthetic_anomalies.csv")
    assert (daily["data_origin"] == "synthetic").all()
    for spec in SPECS:
        print(plot_indicator(spec, daily, sem, anom))


if __name__ == "__main__":
    main()
