"""Extrae la base de conocimiento del asistente (backend/chatbot.py) a JSON.

El prototipo la lleva dentro de la página para que el asistente responda sin servidor
(GitHub Pages, o index.html abierto con doble clic). Así los textos viven en un solo sitio:
se editan en backend/chatbot.py y build.py los copia a la página.

No importa chatbot.py (eso exigiría tener fastapi y sqlmodel instalados): lee el archivo y
evalúa solo las constantes de la lista NAMES.

Uso: python prototipo/build_chat.py  (imprime el JSON; build.py lo usa como módulo)
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parent.parent
NAMES = [
    "DISCLAIMER", "LABELS", "INDICATORS", "BEHAVIORAL", "HAZARDS", "STATUS_EN", "RECOMMENDATIONS_EN",
    "ESCALATION", "GAMIFICATION", "HONESTY_NOTE", "QUICK_QUESTIONS",
    "INDICATOR_SYNONYMS", "HAZARD_SYNONYMS", "BEHAVIORAL_SYNONYMS",
]
# Las claves Status.X de chatbot.py pasan a ser los textos "normal" / "attention" / "critical".
STATUS = SimpleNamespace(NORMAL="normal", ATTENTION="attention", CRITICAL="critical")


def constants(path: Path, names: list[str]) -> dict:
    """Valor de las asignaciones de primer nivel `NOMBRE = ...` pedidas en `names`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in names:
            code = compile(ast.Expression(node.value), str(path), "eval")
            out[target.id] = eval(code, {"__builtins__": {}, "Status": STATUS})  # solo literales y Status.X
    missing = [n for n in names if n not in out]
    assert not missing, f"{path.name}: faltan las constantes {missing}"
    return out


def knowledge_base() -> dict:
    kb = constants(ROOT / "backend" / "chatbot.py", NAMES)
    thresholds = constants(ROOT / "backend" / "thresholds.py", ["THRESHOLDS"])["THRESHOLDS"]
    # del semáforo fijo solo se usa la unidad y el rango de referencia que el asistente cita
    kb["RANGES"] = {k: {"unit": v["unit"], "normal": list(v["normal"])} for k, v in thresholds.items()}
    return kb


if __name__ == "__main__":
    print(json.dumps(knowledge_base(), ensure_ascii=False, indent=1))
