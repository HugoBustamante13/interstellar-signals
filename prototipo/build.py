"""Genera prototipo/index.html: datos sintéticos del simulador + template.html.

Uso (desde la raíz del repo):
    python prototipo/build.py
Opcional: python prototipo/build.py simulador/out_2astronautas "SIM-001=Zamar,SIM-002=Carlos"
"""
import json, subprocess, sys
from pathlib import Path

import build_chat

HERE = Path(__file__).parent
ROOT = HERE.parent
sim = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "simulador" / "out_2astronautas")
names = sys.argv[2] if len(sys.argv) > 2 else "SIM-001=Zamar,SIM-002=Carlos"
data = HERE / "data.json"

subprocess.run([sys.executable, str(HERE / "build_data.py"), sim, str(data), names], check=True)
body = HERE / "body_mesh.json"  # malla del cuerpo 3D (MakeHuman, CC0)
if not body.exists():
    subprocess.run([sys.executable, str(HERE / "build_body.py")], check=True)
html = (HERE / "template.html").read_text(encoding="utf-8")
assert "__DATA__" in html and "__BODY__" in html and "__CHATKB__" in html, "template.html debe contener los marcadores __DATA__, __BODY__ y __CHATKB__"
out = HERE / "index.html"
html = html.replace("__DATA__", data.read_text(encoding="utf-8"), 1).replace("__BODY__", body.read_text(encoding="utf-8"), 1)
# base de conocimiento del asistente, copiada de backend/chatbot.py para que responda sin servidor
html = html.replace("__CHATKB__", json.dumps(build_chat.knowledge_base(), ensure_ascii=False).replace("</", "<\\/"), 1)
out.write_text(html, encoding="utf-8")
data.unlink()
print("Listo:", out)
