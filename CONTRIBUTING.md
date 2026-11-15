# Cómo trabajamos en este repo

Somos varios tocando lo mismo. Estas reglas evitan que nos pisemos.

## El flujo

1. **`main` siempre funciona.** Es lo que se muestra en la demo. Nadie sube directo ahí.
2. **Cada tarea va en su rama**, con tu nombre y la tarea: `jose/figura-3d`, `andres/motor-reglas`.
3. **Se integra con un Pull Request.** Otra persona lo mira y lo aprueba antes de fusionar.
4. **Ramas cortas.** Fusiona en horas o en un día. Entre más vive una rama, más conflictos trae.

```bash
git checkout main
git pull                           # trae lo último antes de empezar
git checkout -b tu-nombre/tarea    # crea tu rama
# ... trabaja y haz commits ...
git push -u origin tu-nombre/tarea
```

Después abre el Pull Request en GitHub (te aparece un botón amarillo «Compare & pull request»).

Si `main` avanzó mientras trabajabas, actualiza tu rama antes de pedir la revisión:

```bash
git checkout main && git pull
git checkout tu-nombre/tarea
git merge main
```

## Regla 1: no edites los archivos generados

Estos archivos los produce un script. No se editan a mano:

| Archivo generado | Se edita | Se regenera con |
|---|---|---|
| `prototipo/index.html` | `prototipo/template.html` | `python prototipo/build.py` |
| `prototipo/body_mesh.json` | `prototipo/build_body.py` | `python prototipo/build_body.py` |

Si `index.html` o `body_mesh.json` entran en conflicto al fusionar, **no lo resuelvas a mano**.
Resuelve primero `template.html`, vuelve a ejecutar el script y sube ese resultado:

```bash
python prototipo/build.py
git add prototipo/index.html
```

## Regla 2: avisa antes de un cambio grande en `template.html`

Casi todo el prototipo vive en ese archivo. Git resuelve solo los cambios en zonas distintas,
así que repartimos por zonas:

| Zona | Quién |
|---|---|
| Figura 3D y mapa corporal | Jose |
| Chequeo y entrada manual, gamificación | Jarib |
| Reglas del semáforo y alertas | Andres |
| Base de datos y recepción del sensor (`backend/`) | James |
| Sensores y página de control (`control.html`, `backend/live.py`) | Hugo |

Si vas a mover o reordenar bloques grandes, avisa en el chat del equipo antes.

## Commits

- En español.
- Un commit por cambio que tenga sentido solo: «Agrega lista de señales al chequeo», no «cambios».

## Antes de pedir revisión

- Abre `prototipo/index.html` y comprueba que carga sin errores en la consola del navegador.
- Si tocaste el backend, arráncalo y prueba el endpoint que cambiaste.
- No subas nada con datos reales de personas: todo lo de la demo es sintético.
