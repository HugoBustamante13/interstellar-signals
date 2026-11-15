# Prototipo web — Interstellar Signals

Página única (HTML + Three.js) para que cada astronauta **se autoevalúe**: chequeo diario, figura 3D con su semáforo por zona, tendencias frente a su línea base, historial de la tripulación y documentación.

**Todos los datos son sintéticos** (generados por `simulador/`). No es un dispositivo médico ni está validado clínicamente.

## Abrirlo
Abre `prototipo/index.html` en el navegador (doble clic). Necesita internet solo para cargar Three.js desde jsDelivr.

## Modificarlo
1. Edita `prototipo/template.html` (no `index.html`, que se genera).
2. Regenera: `python prototipo/build.py` (requiere pandas).
3. Recarga `index.html`.

- `build_data.py` une `mission_synthetic_daily.csv` + `mission_synthetic_semaforo.csv` del simulador y **descarta las columnas `truth_*`**.
- Nombres de demostración: SIM-001 = Zamar, SIM-002 = Carlos (datos de `simulador/out_2astronautas`).
