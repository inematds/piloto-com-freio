# Piloto com Freio

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

Você ainda aprova cada comando do Claude Code, ou liberou tudo e torce para não dar errado? O jeito novo é o meio:
**modo automático** para o que tem volta e **freio** (regra de negação) para o que não tem. Este kit monta isso no
seu projeto em minutos, com o teste da reversibilidade, e traz os prompts de conferência e de revisor separado.

📖 Guia: **https://inematds.github.io/piloto-com-freio/guia/**

## Por que agora

Na palestra "Rethinking Claude Code Best Practices" (Anthropic, nov/2026):
- o modo automático virou o permissão padrão do Claude Code em agosto;
- no teste da Anthropic, pessoas no circuito pegaram ~14% dos comandos claramente perigosos; o modo automático bloqueou 89%;
- ainda assim, ~1 em cada 10 passou. Por isso, o que não tem volta vai numa **regra de negação**: se a chamada casa
  com ela, o classificador nem chega a ver.

## As 5 trocas

| antes | agora | no kit |
|---|---|---|
| corrigir o Claude o tempo todo | modelo atual entende a intenção; instruções sem grito | `freio.py auditar` acha IMPORTANTE/NUNCA/!!! e indica `/doctor prompt-audit` |
| aprovar cada comando | modo automático | `auditar` mostra o seu modo |
| torcer para não dar errado | regra de negação no que não tem volta | `entrevista` → `aplicar` → `testar` |
| "terminei" sem prova | pronto definido, checagem por tarefa, saída real | `prompt pronto`, `prompt revisor`, `hooks/conferir-antes-de-parar.sh` |
| abrir 8 sessões à mão | uma sessão principal que distribui e confere | `prompt orquestrador`, `prompt advisor` |

## Uso (Python 3.9+, sem instalar nada)

```bash
git clone https://github.com/inematds/piloto-com-freio && cd piloto-com-freio
python3 freio.py auditar --projeto ~/meu-projeto          # como está hoje
python3 freio.py entrevista --saida regras.json            # "se errar uma vez, dá para desfazer?"
python3 freio.py aplicar --projeto ~/meu-projeto --de regras.json        # prévia
python3 freio.py aplicar --projeto ~/meu-projeto --de regras.json --sim  # grava (com cópia do anterior)
python3 freio.py testar 'Bash(git reset --hard HEAD)' --projeto ~/meu-projeto
python3 freio.py prompt pronto                              # cole no começo de uma tarefa grande
```

O `testar` é uma aproximação das regras do Claude Code (nome da ferramenta + padrão com `*`). A prova de verdade é
pedir ao próprio Claude: veja `exemplos/prova-real.md` (ele não conseguiu ler o `.env`).

## Conteúdo

| arquivo | o quê |
|---|---|
| `freio.py` | auditar, entrevista, aplicar, testar, prompt |
| `prompts/` | entrevista de confiança, pronto em 3 itens, revisor separado, orquestrador, advisor |
| `hooks/conferir-antes-de-parar.sh` | hook Stop: o que tem de rodar sempre não fica só no prompt |
| `exemplos/` | respostas de exemplo e a prova real |
| `tests/` | `python3 -m unittest discover -s tests` |

Projetos e cursos gratuitos: https://inema.club · Licença MIT.
