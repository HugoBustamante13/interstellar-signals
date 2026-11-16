# Astronaut Health Monitor — NASA Space Apps Challenge

A visual tool for astronauts to log health indicators, see their status as a
traffic light (green/yellow/red) on a body map, review trends over time and get
guidance on next steps when something goes out of range.

## Structure

```
nasa-space-apps/
├── .claude/agents/        # Subagents with an assigned model (see CLAUDE.md)
├── CLAUDE.md              # Full project context (team, decisions, open items)
├── backend/               # FastAPI + SQLite
├── frontend/              # React + TS + Vite + Tailwind + Recharts
├── simulador/             # Synthetic data + traffic light with personal baseline (v0.3)
│   ├── sim/  out/  schema/  fichas/  charts/
│   └── RESULTADOS_investigacion.md
└── docs/
    ├── health_indicators.md
    └── equipo/            # Challenge guide, indicator sources, data delivery (.docx, in Spanish)
```

## How to run it

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
It runs at `http://localhost:8000`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
It runs at `http://localhost:5173` and proxies `/api` to the backend.

### Simulator
```bash
cd simulador
pip install numpy pandas scipy matplotlib jsonschema
python sim/simulator.py --out out_prueba     # generates data + traffic light (~1 s)
python schema/validate.py out/mission_synthetic.json
```
See `docs/equipo/Entrega_parte_de_datos.docx` for details. All data is synthetic.

### Web prototype (demo)
Open `prototipo/index.html` in your browser. To change it, edit
`prototipo/template.html` and run `python prototipo/build.py`
(see `prototipo/README.md`).

If the backend is not running, the frontend still works in local mode
(it evaluates the indicators in the browser, without saving history).

## Suggested next steps
1. Refine the thresholds in `docs/health_indicators.md` with real NASA HRP
   sources (delegate to the `investigador` agent).
2. Add simple authentication / astronaut selection if there is more than one user.
3. Add gamification (measurement streaks, achievements) — mentioned as an
   optional feature of the challenge.
4. Improve the body map with a real silhouette (SVG) instead of circles.
5. Add educational explanations per indicator ("why this is measured in space").
