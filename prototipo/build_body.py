"""Convierte la malla base de MakeHuman (CC0) en un JSON compacto para el prototipo.

Uso (desde la raíz del repo):
    python prototipo/build_body.py

Lee prototipo/assets/makehuman_base_hm08.obj, se queda solo con el grupo «body»
(descarta ayudas y articulaciones), lo escala a 1,78 m con los pies en y = 0 y escribe
prototipo/body_mesh.json: posiciones en int16 y caras de cuatro lados en uint16, en base64.
Conserva los cuadros originales para que el alambre no muestre diagonales.
"""
import base64, json, struct, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "assets" / "makehuman_base_hm08.obj"
OUT = HERE / "body_mesh.json"
HEIGHT = 1.78

V, quads, group = [], [], ""
for line in SRC.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("v "):
        V.append(tuple(float(x) for x in line.split()[1:4]))
    elif line.startswith("g "):
        group = line.split()[1]
    elif line.startswith("f ") and group == "body":
        f = [int(t.split("/")[0]) - 1 for t in line.split()[1:]]
        assert len(f) == 4, "se esperaban solo caras de cuatro lados"
        quads.append(f)

used = sorted({i for f in quads for i in f})
remap = {old: new for new, old in enumerate(used)}
assert len(used) < 65536
ys = [V[i][1] for i in used]
zs = [V[i][2] for i in used]
s = HEIGHT / (max(ys) - min(ys))
# centro en z: el del tronco (los brazos van algo adelantados)
torso = [V[i][2] for i in used if abs(V[i][0]) < 1.0 and 0 < V[i][1] < 5]
zc = (min(torso) + max(torso)) / 2
P = [((V[i][0]) * s, (V[i][1] - min(ys)) * s, (V[i][2] - zc) * s) for i in used]

lo = [min(p[a] for p in P) for a in range(3)]
hi = [max(p[a] for p in P) for a in range(3)]
q = [int(round((p[a] - lo[a]) / (hi[a] - lo[a]) * 65535)) - 32768 for p in P for a in range(3)]
pos = struct.pack(f"<{len(q)}h", *q)
idx = struct.pack(f"<{len(quads) * 4}H", *[remap[i] for f in quads for i in f])


def front(x, y, r=0.03):
    """Punto de la superficie más adelantado cerca de (x, y): ahí se apoya un marcador."""
    near = [p for p in P if (p[0] - x) ** 2 + (p[1] - y) ** 2 < r * r]
    return max(near, key=lambda p: p[2]) if near else None


if "--medidas" in sys.argv:  # ayuda para elegir dónde van los marcadores
    print("caja:", [round(v, 3) for v in lo], [round(v, 3) for v in hi])
    for y in (1.72, 1.66, 1.6, 1.55, 1.45, 1.35, 1.25, 1.1, 0.95, 0.85, 0.7, 0.5):
        row = [p for p in P if abs(p[1] - y) < 0.01]
        print(f"y={y}: x {min(p[0] for p in row):.3f}..{max(p[0] for p in row):.3f}  z máx centro {max((p[2] for p in row if abs(p[0]) < 0.03), default=float('nan')):.3f}")
    for x in (0.22, 0.28, 0.34, 0.40, 0.46, 0.52):
        col = [p for p in P if abs(p[0] - x) < 0.01]
        print(f"x={x}: y {min(p[1] for p in col):.3f}..{max(p[1] for p in col):.3f}  z {min(p[2] for p in col):.3f}..{max(p[2] for p in col):.3f}")
    sys.exit()

# puntos de apoyo de los marcadores del semáforo, sobre la superficie y un poco hacia fuera
TARGETS = {"head": (0, 1.70), "temp": (0, 1.565), "heart": (0.05, 1.33), "arm": (0.34, 1.245),
           "abdomen": (0, 1.08), "hand": (-0.50, 1.04), "leg": (-0.11, 0.72)}
anchors = {}
for name, (x, y) in TARGETS.items():
    pt = front(x, y)
    assert pt, f"sin superficie cerca de {name}"
    anchors[name] = [round(pt[0], 4), round(pt[1], 4), round(pt[2] + 0.012, 4)]

OUT.write_text(json.dumps({
    "source": "MakeHuman base mesh hm08 (CC0 1.0)",
    "nv": len(P), "nq": len(quads), "anchors": anchors, "lo": [round(v, 5) for v in lo], "hi": [round(v, 5) for v in hi],
    "pos": base64.b64encode(pos).decode(), "quad": base64.b64encode(idx).decode(),
}, separators=(",", ":")), encoding="utf-8")
print(OUT, OUT.stat().st_size, "bytes ·", len(P), "vértices ·", len(quads), "cuadros")
