# Piloto com Freio

[![Piloto com Freio](guia/assets/banner.jpg)](https://inematds.github.io/piloto-com-freio/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

Você aprova cada comando do Claude ou liberou tudo e torce? O jeito novo é o meio:
**modo automático** para o que tem volta e **freio** (regra de negação) para o que não tem. Este kit monta isso no
seu projeto em minutos, com o teste da reversibilidade, e traz os prompts de conferência e de revisor separado.

📖 Guia (landing + passo a passo): **https://inematds.github.io/piloto-com-freio/guia/**

## O que é

Liberar tudo é rápido até o dia em que a IA apaga o que não devia. Aprovar tudo é seguro, mas cansa, e quem cansa
aprova sem ler. O Piloto com Freio é um kit gratuito para quem usa o Claude Code, a IA da Anthropic que trabalha
dentro do seu computador. Ele deixa o Claude no modo automático (um verificador aprova o que é seguro e para o que é
arriscado) e põe uma regra de negação, um bloqueio fixo, em tudo que não tem volta. Traz também 5 prompts prontos
para o Claude provar que terminou e um hook que confere o trabalho antes de ele parar. Precisa do Claude Code e do
Python 3.9 ou mais novo; não instala nada.

## Comece colando isto no Claude Code (aberto no seu projeto)

```text
Leia o repositório https://github.com/inematds/piloto-com-freio (README, freio.py e a pasta prompts/).
1. Baixe o kit e rode: python3 freio.py auditar --projeto <a pasta deste projeto>
   Me explique em linguagem simples o que está liberado hoje e o que ainda não tem freio.
2. Faça comigo o teste da reversibilidade (prompts/entrevista.md): para cada tipo de ação,
   me pergunte se dá para desfazer caso você erre uma vez. Poucas perguntas por vez.
3. Grave as minhas respostas num regras.json e me mostre a prévia com freio.py aplicar (sem --sim).
4. Não grave nada no .claude/settings.json antes do meu sim. Depois do sim, rode aplicar --sim
   e confira com freio.py testar, me mostrando a saída real de cada comando.
```

## Baseado na palestra oficial da Anthropic

"Rethinking Claude Code Best Practices", Lydia Hallie (Anthropic), AI Engineer, 12/11/2026 —
https://www.youtube.com/watch?v=vlfCjWuv4es
- o modo automático (`--permission-mode auto`) virou o modo de permissão padrão do Claude Code;
- no teste da Anthropic (agosto), pessoas no circuito pegaram ~14% dos comandos claramente perigosos; o modo automático bloqueou 89%;
- ainda assim, ~1 em cada 10 passou. Por isso, o que não tem volta vai numa **regra de negação**: se a chamada casa
  com ela, o classificador nem chega a ver.

O prompt `advisor` é dica do kit, não da palestra.

## As 5 trocas

| antes | agora | no kit |
|---|---|---|
| corrigir o Claude o tempo todo | modelo atual entende a intenção; instruções sem grito | `freio.py auditar` acha IMPORTANTE/NUNCA/!!! e indica `/doctor prompt-audit` |
| aprovar cada comando | modo automático | `auditar` mostra o seu modo |
| torcer para não dar errado | regra de negação no que não tem volta | `entrevista` → `aplicar` → `testar` |
| "terminei" sem prova | pronto definido, checagem por tarefa, saída real | `prompt pronto`, `prompt revisor`, `hooks/conferir-antes-de-parar.sh` |
| abrir 8 sessões à mão | uma sessão principal que distribui e confere | `prompt orquestrador`, `prompt advisor` |

---

## Instalação técnica

Pré-requisitos: Python 3.9+ (sem dependências) e o Claude Code. Testado em 26/11/2026 no Linux, Python 3.12.3,
Claude Code 2.1.332.

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

**Hook Stop** (`hooks/conferir-antes-de-parar.sh`): roda a checagem do projeto antes de deixar o Claude encerrar;
se falhar, sai com código 2 e devolve o erro. Copie a pasta para o seu projeto (`cp -r hooks ~/meu-projeto/`) e
ligue no `.claude/settings.json` do projeto, com a checagem do seu projeto em `CHECAGEM`:

```json
"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "CHECAGEM='npm test' bash hooks/conferir-antes-de-parar.sh"}]}]}
```

Sem `CHECAGEM`, a checagem padrão é `python3 -m unittest discover -s tests -q`.

| arquivo | o quê |
|---|---|
| `freio.py` | auditar, entrevista, aplicar, testar, prompt |
| `prompts/` | entrevista de confiança, pronto em 3 itens, revisor separado, orquestrador, advisor |
| `hooks/conferir-antes-de-parar.sh` | hook Stop: o que tem de rodar sempre não fica só no prompt |
| `exemplos/` | respostas de exemplo e a prova real |
| `tests/` | `python3 -m unittest discover -s tests` (8 testes) |
| `guia/` | o guia em PT, EN e ES (GitHub Pages) |

## O processo, do início ao fim

1. 🧠 Você abre o Claude Code no seu projeto e cola o pedido acima (ou roda os comandos).
2. ⚙️ `python3 freio.py auditar --projeto <pasta>` — mostra o modo, as regras de negação e as linhas que gritam.
3. 🧠 `python3 freio.py entrevista --saida regras.json` — você responde "dá para desfazer?" para cada ação.
4. ⚙️ `python3 freio.py aplicar --projeto <pasta> --de regras.json` — prévia, nada gravado.
5. 🧠 Você confere a lista e diz sim.
6. ⚙️ `python3 freio.py aplicar --projeto <pasta> --de regras.json --sim` — grava, com cópia do arquivo anterior.
7. ⚙️ `python3 freio.py testar '<chamada>' --projeto <pasta>` — confere se o freio pega.
8. 🤖 Opcional: peça ao Claude para ler o `.env` e veja que ele não consegue (como em `exemplos/prova-real.md`).
9. 🧠 Nas tarefas grandes, cole os prompts `pronto` e `revisor` (`python3 freio.py prompt <nome>`).
10. ⚙️ Copie `hooks/` para o projeto e ligue o hook Stop para a checagem rodar sempre antes do Claude encerrar.

Projetos e cursos gratuitos: https://inema.club · Licença MIT.
