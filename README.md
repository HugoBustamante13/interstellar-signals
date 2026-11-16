# Astronaut Health Monitor — NASA Space Apps Challenge

Herramienta visual para que astronautas registren indicadores de salud, vean su
estado por código de colores sobre un mapa corporal, revisen tendencias en el
tiempo y reciban recomendaciones cuando algo se sale de rango.

## Estructura

```
nasa-space-apps/
├── .claude/agents/        # Subagentes con modelo asignado (ver CLAUDE.md)
├── CLAUDE.md              # Contexto completo del proyecto (equipo, decisiones, pendientes)
├── backend/               # FastAPI + SQLite
├── frontend/              # React + TS + Vite + Tailwind + Recharts
├── simulador/             # Datos sintéticos + semáforo con línea base personal (v0.3)
│   ├── sim/  out/  schema/  fichas/  charts/
│   └── RESULTADOS_investigacion.md
└── docs/
    ├── health_indicators.md
    └── equipo/            # Guía del reto, respaldo de indicadores, entrega de datos (.docx)
```

## Cómo correrlo

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_demo.py          # carga la misión sintética (4 astronautas; el día 180 es hoy)
uvicorn main:app --reload
```
Queda en `http://localhost:8000`. El color lo calcula el semáforo del simulador (`semaforo_bridge.py` importa
`simulador/sim/semaforo.py`): cada astronauta se compara con su propia línea base. Endpoints: `/indicators`,
`/astronauts`, `/records`, `/status`, `/series`. Contrato en `docs/decision_integracion_semaforo.md`, sección 5.

Pruebas: `pip install -r requirements-dev.txt && python -m pytest -q`. Si al arrancar dice «esquema viejo»,
borra `backend/health_records.db` (solo tenía datos de prueba) y vuelve a correr `seed_demo.py`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Queda en `http://localhost:5173` y proxyea `/api` hacia el backend.

### Simulador
```bash
cd simulador
pip install numpy pandas scipy matplotlib jsonschema
python sim/simulator.py --out out_prueba     # genera datos + semáforo (~1 s)
python schema/validate.py out/mission_synthetic.json
```
Ver `docs/equipo/Entrega_parte_de_datos.docx` para el detalle. Todos los datos son sintéticos.

### Prototipo web (demo)
Abre `prototipo/index.html` en el navegador. Para modificarlo edita
`prototipo/template.html` y ejecuta `python prototipo/build.py`
(ver `prototipo/README.md`).

Si el backend no está corriendo, el frontend en React funciona en modo local: solo límites
clínicos, sin línea base personal ni histórico.

## Próximos pasos sugeridos
1. Refinar los umbrales de `docs/health_indicators.md` con fuentes reales de
   NASA HRP (delegar al agente `investigador`).
2. Agregar autenticación simple / selección de astronauta si hay más de un usuario.
3. Agregar gamificación (rachas de mediciones, logros) — mencionado como
   feature opcional del challenge.
4. Mejorar el mapa corporal con una silueta real en vez de círculos (SVG).
5. Agregar explicaciones educativas por indicador ("por qué se mide esto en el espacio").
