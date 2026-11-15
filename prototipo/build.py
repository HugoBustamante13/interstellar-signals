"""Genera prototipo/index.html: datos sintéticos del simulador + template.html.

Uso (desde la raíz del repo):
    python prototipo/build.py
Opcional: python prototipo/build.py simulador/out_2astronautas "SIM-001=Zamar,SIM-002=Carlos"
"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sim = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "simulador" / "out_2astronautas")
names = sys.argv[2] if len(sys.argv) > 2 else "SIM-001=Zamar,SIM-002=Carlos"
data = HERE / "data.json"

subprocess.run([sys.executable, str(HERE / "build_data.py"), sim, str(data), names], check=True)
html = (HERE / "template.html").read_text(encoding="utf-8")
assert "__DATA__" in html, "template.html debe contener el marcador __DATA__"
out = HERE / "index.html"
out.write_text(html.replace("__DATA__", data.read_text(encoding="utf-8"), 1), encoding="utf-8")
data.unlink()
print("Listo:", out)
