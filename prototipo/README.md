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

## Demo en vivo desde el celular
El celular hace de camisa, reloj y entradas manuales: envía lecturas **simuladas** y la web reacciona al instante.

1. PC y celular en la misma red Wi-Fi.
2. En el PC: `cd backend` y `venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000`
   (si Windows pregunta por el firewall, permite el acceso en redes privadas).
3. En el PC abre `http://localhost:8000/demo/#astronautas`.
4. En el celular abre `http://IP-DEL-PC:8000/demo/control.html` (la IP sale con `ipconfig`).
5. Toca un escenario o mueve los controles y pulsa «Enviar lectura».

- `control.html` es la página del celular; `backend/live.py` es el puente (en memoria, no guarda nada).
- Abierto con doble clic (`file://`), `index.html` no escucha al celular: tiene que servirse desde el backend.

## Alertas de voz
Cuando un indicador pasa a amarillo o rojo, la app muestra un aviso abajo y, si está activo el botón
**Alertas de voz** de la barra superior, pita y lo dice en voz alta: quién, qué indicador, su valor y qué hacer.

- **Cuándo suena:** con una lectura del celular en amarillo o rojo, al evaluar el chequeo y, en «Reproducir en vivo»,
  solo cuando el estado sube (verde → amarillo → rojo). Moverse a mano por la línea de tiempo no suena.
- **Rojo:** tres pitidos agudos, pausa la reproducción y se repite cada 30 s hasta pulsar «Entendido».
  Volver a pulsar «Reproducir en vivo» también cuenta como «Entendido».
- **Amarillo:** dos tonos suaves, una sola vez.
- **No crea umbrales:** dice lo mismo que marca el semáforo en pantalla (`absViolation`, `evalReading`, `indState`).
- **Antes de la demo:** pulsa el botón una vez (el navegador no deja sonar una página que nadie ha tocado) y
  comprueba que diga «Alertas de voz activadas». Usa las voces en español instaladas en el equipo; si no hay
  ninguna, el botón dice «Solo pitido». En Windows se agregan en Configuración → Hora e idioma → Voz.
- El aviso en pantalla sale aunque la voz esté apagada.

## Modelo 3D del cuerpo
La figura 3D usa la malla base de **MakeHuman** (`hm08`), publicada como **CC0 1.0** en septiembre de 2020
([repositorio](https://github.com/makehumancommunity/makehuman), archivo `makehuman/data/3dobjs/base.obj`).
CC0 permite usarla y redistribuirla sin atribución; la citamos igual por cortesía.

- `assets/makehuman_base_hm08.obj`: el archivo original, sin cambios.
- `build_body.py`: se queda con el cuerpo (13 378 caras de cuatro lados), lo escala a 1,78 m y calcula dónde van los marcadores.
- `body_mesh.json`: el resultado, que `build.py` incrusta en `index.html`.

Para mover un marcador, cambia `TARGETS` en `build_body.py` y ejecuta `python prototipo/build_body.py` y luego `python prototipo/build.py`.
