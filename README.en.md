# Piloto com Freio

[![Piloto com Freio](guia/assets/banner-en.jpg)](https://inematds.github.io/piloto-com-freio/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

Do you approve every single Claude command, or did you allow everything and hope for the best? The new way is in between:
**auto mode** for what can be undone and a **brake** (deny rule) for what can't. This kit sets that up in your
project in minutes, using the reversibility test, and includes the prompts for verification and for a separate reviewer.

📖 Guide (landing page + step by step): **https://inematds.github.io/piloto-com-freio/guia/en/**

## What it is

Allowing everything is fast until the day the AI deletes something it shouldn't have. Approving everything is safe, but tiring, and tired people
approve without reading. Piloto com Freio is a free kit for people who use Claude Code, Anthropic's AI that works
inside your computer. It puts Claude in auto mode (a checker approves what is safe and stops what is
risky) and places a deny rule, a fixed block, on everything that can't be undone. It also includes 5 ready-made prompts
for Claude to prove it has finished, and a hook that checks the work before it stops. It requires Claude Code and
Python 3.9 or newer; it installs nothing.

## Start by pasting this into Claude Code (opened in your project)

```text
Read the repository https://github.com/inematds/piloto-com-freio (README, freio.py and the prompts/ folder).
1. Download the kit and run: python3 freio.py auditar --projeto <this project's folder>
   Explain to me in plain language what is allowed today and what still has no brake.
2. Go through the reversibility test with me (prompts/entrevista.md): for each type of action,
   ask me whether it can be undone if you get it wrong once. A few questions at a time.
3. Save my answers to a regras.json and show me the preview with freio.py aplicar (without --sim).
4. Do not write anything to .claude/settings.json before I say yes. After my yes, run aplicar --sim
   and verify with freio.py testar, showing me the actual output of each command.
```

## Based on Anthropic's official talk

"Rethinking Claude Code Best Practices", Lydia Hallie (Anthropic), AI Engineer, November 12, 2026 —
https://www.youtube.com/watch?v=vlfCjWuv4es
- auto mode (`--permission-mode auto`) became Claude Code's default permission mode;
- in Anthropic's test (August), humans in the loop caught ~14% of clearly dangerous commands; auto mode blocked 89%;
- even so, ~1 in 10 got through. That's why whatever can't be undone goes into a **deny rule**: if the call matches
  it, the classifier never even sees it.

The `advisor` prompt is a tip from the kit, not from the talk.

## The 5 swaps

| before | now | in the kit |
|---|---|---|
| correcting Claude all the time | the current model understands intent; instructions without shouting | `freio.py auditar` finds IMPORTANTE/NUNCA/!!! and points to `/doctor prompt-audit` |
| approving every command | auto mode | `auditar` shows your mode |
| hoping nothing goes wrong | deny rule on what can't be undone | `entrevista` → `aplicar` → `testar` |
| "I'm done" with no proof | defined done, a check per task, real output | `prompt pronto`, `prompt revisor`, `hooks/conferir-antes-de-parar.sh` |
| opening 8 sessions by hand | one main session that distributes and checks | `prompt orquestrador`, `prompt advisor` |

---

## Technical installation

Prerequisites: Python 3.9+ (no dependencies) and Claude Code. Tested on November 26, 2026 on Linux, Python 3.12.3,
Claude Code 2.1.332.

```bash
git clone https://github.com/inematds/piloto-com-freio && cd piloto-com-freio
python3 freio.py auditar --projeto ~/meu-projeto          # how things are today
python3 freio.py entrevista --saida regras.json            # "if it goes wrong once, can it be undone?"
python3 freio.py aplicar --projeto ~/meu-projeto --de regras.json        # preview
python3 freio.py aplicar --projeto ~/meu-projeto --de regras.json --sim  # writes (keeping a copy of the previous one)
python3 freio.py testar 'Bash(git reset --hard HEAD)' --projeto ~/meu-projeto
python3 freio.py prompt pronto                              # paste at the start of a big task
```

The kit prints its messages and prompts in Portuguese.

`testar` is an approximation of Claude Code's rules (tool name + pattern with `*`). The real proof is
asking Claude itself: see `exemplos/prova-real.md` (in Portuguese) (it could not read the `.env`).

**Stop hook** (`hooks/conferir-antes-de-parar.sh`): runs the project's check before letting Claude finish;
if it fails, it exits with code 2 and returns the error. Copy the folder into your project (`cp -r hooks ~/meu-projeto/`) and
enable it in the project's `.claude/settings.json`, with your project's check in `CHECAGEM`:

```json
"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "CHECAGEM='npm test' bash hooks/conferir-antes-de-parar.sh"}]}]}
```

Without `CHECAGEM`, the default check is `python3 -m unittest discover -s tests -q`.

| file | what |
|---|---|
| `freio.py` | auditar, entrevista, aplicar, testar, prompt |
| `prompts/` | trust interview, done in 3 items, separate reviewer, orchestrator, advisor |
| `hooks/conferir-antes-de-parar.sh` | Stop hook: what must always run doesn't live only in the prompt |
| `exemplos/` | sample answers and the real proof |
| `tests/` | `python3 -m unittest discover -s tests` (7 tests) |
| `guia/` | the guide in PT, EN and ES (GitHub Pages) |

## The process, from start to finish

1. 🧠 You open Claude Code in your project and paste the request above (or run the commands).
2. ⚙️ `python3 freio.py auditar --projeto <pasta>` — shows the mode, the deny rules and the lines that shout.
3. 🧠 `python3 freio.py entrevista --saida regras.json` — you answer "can it be undone?" for each action.
4. ⚙️ `python3 freio.py aplicar --projeto <pasta> --de regras.json` — preview, nothing written.
5. 🧠 You check the list and say yes.
6. ⚙️ `python3 freio.py aplicar --projeto <pasta> --de regras.json --sim` — writes, keeping a copy of the previous file.
7. ⚙️ `python3 freio.py testar '<chamada>' --projeto <pasta>` — checks whether the brake catches it.
8. 🤖 Optional: ask Claude to read the `.env` and see that it can't (as in `exemplos/prova-real.md` (in Portuguese)).
9. 🧠 For big tasks, paste the `pronto` and `revisor` prompts (`python3 freio.py prompt <nome>`).
10. ⚙️ Copy `hooks/` into the project and enable the Stop hook so the check always runs before Claude finishes.

Free projects and courses: https://inema.club · MIT License.
