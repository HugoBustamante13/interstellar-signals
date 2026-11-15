# Investigación: fuentes de datos y los cuatro problemas del reto

Fecha: 15-nov-2026. Búsqueda web rápida para sustentar el concepto «la camisa vigila a diario; la ecografía solo entra cuando hay rojo». Antes de citar una cifra en el pitch, abrir la fuente y confirmar el número.

## Concepto

| Fuente | Qué aporta | Uso en la app |
|---|---|---|
| Camisa inteligente | FC, respiración, SpO₂, temperatura de piel, actividad | Base diaria |
| Reloj de muñeca | Sueño (actigrafía) y exposición a la luz | Lo que la camisa no cubre durante semanas |
| Manual | Presión con manguito, glucosa, ánimo, ejercicio, señales de defensas | Entrada en el chequeo |
| Ecografía | Diagnóstico | Solo cuando hay rojo |

En el prototipo todos estos datos son simulados o manuales.

## Lo que se confirmó

**Camisa (Bio-Monitor / Astroskin, CSA)**
- Mide pulso y actividad eléctrica del corazón, presión arterial, frecuencia y volumen respiratorio, temperatura de piel, saturación de oxígeno y actividad física. La presión es una estimación continua, no una medida con manguito.
- En el estudio de la Universidad de Waterloo los astronautas la usaron unas 72 horas antes del vuelo y otras 72 horas a bordo. No encontramos sesiones de semanas.
- Fuentes: [CSA, Bio-Monitor](https://www.csa-asc.gc.ca/eng/sciences/astroskin.asp) · [Freethink](https://www.freethink.com/space/smart-shirt) · [NASA NTRS, HERA](https://ntrs.nasa.gov/api/citations/20190000238/downloads/20190000238.pdf)

**Reloj (actigrafía y luz)**
- En la ISS se usó el Actiwatch, que registra actividad y luz ambiente, junto con diarios de sueño.
- En 21 astronautas y 3.248 días en la ISS, el sueño medio fue de 6,4 ± 1,2 h con el reloj interno alineado y de 5,4 ± 1,4 h desalineado.
- NASA ha buscado relojes más nuevos; no confirmamos cuál se usa hoy.
- Fuentes: [PMC5515517](https://rcastoragev2.blob.core.windows.net/04172f60da9099f5a13d74eec33e02ad/PMC5515517.pdf) · [PMC4188436](https://pmc.ncbi.nlm.nih.gov/articles/PMC4188436) · [Sleep-Long](https://phys.org/news/2011-06-slumber-space-station-sleep-long.html)

**Ecografía con guía remota**
- En la ISS un tripulante con poco entrenamiento hace la ecografía guiado por un experto en Tierra. Un estudio de 2006 reportó buena precisión con 2 segundos de latencia.
- El oficial médico de a bordo (CMO) recibe de 40 a 80 horas de entrenamiento práctico y suele tener poca formación médica previa.
- NASA probó en la ISS un software (AMOS) para guiar al tripulante sin apoyo en tiempo real desde Tierra. Es el antecedente más cercano a nuestra idea de autonomía.
- Fuentes: [NASA NTRS, AMOS](https://ntrs.nasa.gov/api/citations/20240012964/downloads/Amos%20Paper%20with%20Figures%20and%20Legends.pdf) · [ESA](https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/International_Space_Station_Benefits_for_Humanity/Advanced_Ultrasound_for_the_Space_Program_and_on_Earth) · [NTRS 2006](https://ntrs.nasa.gov/citations/20060047716)

**Conferencia médica privada (PMC)**
- Cada tripulante habla en privado con su médico de vuelo una vez por semana, y también cuando lo pide.
- Fuentes: [NASA, podcast](https://www.nasa.gov/podcasts/houston-we-have-a-podcast/mission-control-crew-health-consoles) · [NASA, Medical Operations](https://www.nasa.gov/reference/6-0-medical-operations/)

**Sistema inmunitario**
- 14 de 23 astronautas de la ISS (61 %) y 47 de 89 del transbordador (53 %) eliminaron uno o más virus herpes en saliva u orina.
- Casi siempre es asintomático. En algunos casos se asoció con dermatitis atópica o lesiones en la piel.
- Se relaciona con hormonas de estrés y menor inmunidad celular.
- Fuentes: [Rooney et al. 2019, Frontiers in Microbiology](https://pmc.ncbi.nlm.nih.gov/articles/PMC6374706) · [Mehta et al. 2017, npj Microgravity](https://doaj.org/article/f32947e92776479e9e3b840364e87d36)

**Pérdida ósea**
- Con el equipo de fuerza ARED, energía suficiente y vitamina D, la densidad ósea se mantuvo en la mayoría de regiones en misiones de 4 a 6 meses. La resorción no bajó; aumentó la formación.
- La ingesta recomendada de vitamina D se subió a 800 UI en 2006.
- Un seguimiento con 42 astronautas confirmó el resultado.
- Fuentes: [Smith et al. 2012, JBMR](https://pubmed.ncbi.nlm.nih.gov/22549960/) · [NASA NTRS 2014](https://ntrs.nasa.gov/citations/20140013483) · [NASA, blog ISS](https://blogs.nasa.gov/ISS_Science_Blog/2013/10/21/top-ten-space-station-research-results-countdown-ten-preventing-loss-of-bone-mass-in-space-through-diet-and-exercise/)

## Lo que NO se confirmó

- Que el ecógrafo actual de la ISS se llame «Ultrasound 2». En la app decimos «ecografía».
- La cifra de pérdida ósea de 1 a 1,5 % por mes: no apareció en una fuente primaria.
- Pruebas KSS y PVT (Reaction Self Test) en la ISS: la búsqueda no devolvió resultados. No se añadieron a la app.
- Con qué frecuencia aparecen erupciones en la piel en vuelo.

## Decisiones que salieron de aquí

1. Cada indicador declara su fuente: CAMISA, RELOJ o MANUAL. La presión es MANUAL porque la camisa solo la estima.
2. La vista «¿Qué estoy vigilando?» agrupa los indicadores en los cuatro problemas del reto y dice si la medida es directa o indirecta.
3. Defensas y hueso no tienen medida diaria directa. Defensas: temperatura y una lista semanal de señales. Hueso: ejercicio y aptitud, es decir, lo que lo protege.
4. La regla de las señales de defensas (dos señales, o una con 38 °C o más, pasa a amarillo) es un **supuesto del equipo**, no un criterio clínico publicado.
5. El rojo tiene dos tiempos: primeros pasos a bordo con el oficial médico; el médico de vuelo confirma cuando hay enlace.
6. La camisa mide temperatura de piel, no central. Los límites de fiebre necesitan confirmación con termómetro.
