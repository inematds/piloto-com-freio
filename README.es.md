# Piloto com Freio

[![Piloto com Freio](guia/assets/banner-es.jpg)](https://inematds.github.io/piloto-com-freio/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

¿Apruebas cada comando de Claude o liberaste todo y cruzas los dedos? La forma nueva es el punto medio:
**modo automático** para lo que tiene vuelta atrás y **freno** (regla de denegación) para lo que no. Este kit monta eso en
tu proyecto en minutos, con la prueba de reversibilidad, y trae los prompts de comprobación y de revisor separado.

📖 Guía (landing + paso a paso): **https://inematds.github.io/piloto-com-freio/guia/es/**

## Qué es

Liberar todo es rápido hasta el día en que la IA borra lo que no debía. Aprobar todo es seguro, pero cansa, y quien se cansa
aprueba sin leer. Piloto com Freio es un kit gratuito para quien usa Claude Code, la IA de Anthropic que trabaja
dentro de tu computadora. Deja a Claude en modo automático (un verificador aprueba lo que es seguro y frena lo que es
riesgoso) y pone una regla de denegación, un bloqueo fijo, en todo lo que no tiene vuelta atrás. Trae además 5 prompts listos
para que Claude demuestre que terminó y un hook que revisa el trabajo antes de que se detenga. Necesita Claude Code y
Python 3.9 o más reciente; no instala nada.

## Empieza pegando esto en Claude Code (abierto en tu proyecto)

```text
Lee el repositorio https://github.com/inematds/piloto-com-freio (README, freio.py y la carpeta prompts/).
1. Descarga el kit y ejecuta: python3 freio.py auditar --projeto <la carpeta de este proyecto>
   Explícame en lenguaje sencillo qué está liberado hoy y qué todavía no tiene freno.
2. Haz conmigo la prueba de reversibilidad (prompts/entrevista.md): para cada tipo de acción,
   pregúntame si se puede deshacer en caso de que te equivoques una vez. Pocas preguntas por vez.
3. Guarda mis respuestas en un regras.json y muéstrame la vista previa con freio.py aplicar (sin --sim).
4. No escribas nada en .claude/settings.json antes de mi sí. Después del sí, ejecuta aplicar --sim
   y comprueba con freio.py testar, mostrándome la salida real de cada comando.
```

## Basado en la charla oficial de Anthropic

"Rethinking Claude Code Best Practices", Lydia Hallie (Anthropic), AI Engineer, 12/11/2026 —
https://www.youtube.com/watch?v=vlfCjWuv4es
- el modo automático (`--permission-mode auto`) pasó a ser el modo de permisos predeterminado de Claude Code;
- en la prueba de Anthropic (agosto), las personas en el circuito detectaron ~14% de los comandos claramente peligrosos; el modo automático bloqueó el 89%;
- aun así, ~1 de cada 10 pasó. Por eso, lo que no tiene vuelta atrás va en una **regla de denegación**: si la llamada coincide
  con ella, el clasificador ni siquiera llega a verla.

El prompt `advisor` es un consejo del kit, no de la charla.

## Los 5 cambios

| antes | ahora | en el kit |
|---|---|---|
| corregir a Claude todo el tiempo | el modelo actual entiende la intención; instrucciones sin gritos | `freio.py auditar` encuentra IMPORTANTE/NUNCA/!!! e indica `/doctor prompt-audit` |
| aprobar cada comando | modo automático | `auditar` muestra tu modo |
| cruzar los dedos para que nada salga mal | regla de denegación en lo que no tiene vuelta atrás | `entrevista` → `aplicar` → `testar` |
| "terminé" sin pruebas | definición de terminado, comprobación por tarea, salida real | `prompt pronto`, `prompt revisor`, `hooks/conferir-antes-de-parar.sh` |
| abrir 8 sesiones a mano | una sesión principal que reparte y comprueba | `prompt orquestrador`, `prompt advisor` |

---

## Instalación técnica

Requisitos previos: Python 3.9+ (sin dependencias) y Claude Code. Probado el 26/11/2026 en Linux, Python 3.12.3,
Claude Code 2.1.332.

```bash
git clone https://github.com/inematds/piloto-com-freio && cd piloto-com-freio
python3 freio.py auditar --projeto ~/meu-projeto          # cómo está hoy
python3 freio.py entrevista --saida regras.json            # "si te equivocas una vez, ¿se puede deshacer?"
python3 freio.py aplicar --projeto ~/meu-projeto --de regras.json        # vista previa
python3 freio.py aplicar --projeto ~/meu-projeto --de regras.json --sim  # guarda (con copia del anterior)
python3 freio.py testar 'Bash(git reset --hard HEAD)' --projeto ~/meu-projeto
python3 freio.py prompt pronto                              # pégalo al comienzo de una tarea grande
```

El kit imprime los mensajes y los prompts en portugués.

`testar` es una aproximación de las reglas de Claude Code (nombre de la herramienta + patrón con `*`). La prueba de verdad es
pedírselo al propio Claude: mira `exemplos/prova-real.md` (en portugués) (no logró leer el `.env`).

**Hook Stop** (`hooks/conferir-antes-de-parar.sh`): ejecuta la comprobación del proyecto antes de dejar que Claude termine;
si falla, sale con código 2 y devuelve el error. Copia la carpeta a tu proyecto (`cp -r hooks ~/meu-projeto/`) y
actívalo en el `.claude/settings.json` del proyecto, con la comprobación de tu proyecto en `CHECAGEM`:

```json
"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "CHECAGEM='npm test' bash hooks/conferir-antes-de-parar.sh"}]}]}
```

Sin `CHECAGEM`, la comprobación predeterminada es `python3 -m unittest discover -s tests -q`.

| archivo | qué es |
|---|---|
| `freio.py` | auditar, entrevista, aplicar, testar, prompt |
| `prompts/` | entrevista de confianza, definición de terminado en 3 puntos, revisor separado, orquestador, advisor |
| `hooks/conferir-antes-de-parar.sh` | hook Stop: lo que tiene que ejecutarse siempre no queda solo en el prompt |
| `exemplos/` | respuestas de ejemplo y la prueba real |
| `tests/` | `python3 -m unittest discover -s tests` (7 pruebas) |
| `guia/` | la guía en PT, EN y ES (GitHub Pages) |

## El proceso, de principio a fin

1. 🧠 Abres Claude Code en tu proyecto y pegas el pedido de arriba (o ejecutas los comandos).
2. ⚙️ `python3 freio.py auditar --projeto <pasta>` — muestra el modo, las reglas de denegación y las líneas que gritan.
3. 🧠 `python3 freio.py entrevista --saida regras.json` — respondes "¿se puede deshacer?" para cada acción.
4. ⚙️ `python3 freio.py aplicar --projeto <pasta> --de regras.json` — vista previa, no se guarda nada.
5. 🧠 Revisas la lista y dices que sí.
6. ⚙️ `python3 freio.py aplicar --projeto <pasta> --de regras.json --sim` — guarda, con copia del archivo anterior.
7. ⚙️ `python3 freio.py testar '<chamada>' --projeto <pasta>` — comprueba que el freno actúe.
8. 🤖 Opcional: pídele a Claude que lea el `.env` y verás que no puede (como en `exemplos/prova-real.md` (en portugués)).
9. 🧠 En las tareas grandes, pega los prompts `pronto` y `revisor` (`python3 freio.py prompt <nome>`).
10. ⚙️ Copia `hooks/` al proyecto y activa el hook Stop para que la comprobación se ejecute siempre antes de que Claude termine.

Proyectos y cursos gratuitos: https://inema.club · Licencia MIT.
