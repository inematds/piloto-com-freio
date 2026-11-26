#!/usr/bin/env bash
# Hook "Stop" do Claude Code: o que TEM de rodar sempre não fica só no prompt.
# Roda a checagem do projeto antes de deixar o Claude encerrar. Falhou → devolve o erro e ele continua.
# Ligue em .claude/settings.json:
#   "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "bash hooks/conferir-antes-de-parar.sh"}]}]}
# Troque CHECAGEM pelo comando do seu projeto (testes, build, lint).
CHECAGEM=${CHECAGEM:-"python3 -m unittest discover -s tests -q"}
entrada=$(cat)
# Evita laço: se o Claude já está continuando por causa deste hook, deixa parar.
if echo "$entrada" | grep -q '"stop_hook_active": *true'; then exit 0; fi
if saida=$(bash -c "$CHECAGEM" 2>&1); then exit 0; fi
echo "A checagem falhou. Corrija antes de terminar:" >&2
echo "$saida" | tail -20 >&2
exit 2
