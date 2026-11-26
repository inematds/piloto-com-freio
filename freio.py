#!/usr/bin/env python3
"""Piloto com Freio: deixe o Claude Code trabalhar no modo automático com freio no que não tem volta.

Comandos:
  auditar     [--projeto DIR]                 mostra modo de permissão, regras de negação e instruções que gritam
  entrevista  [--respostas F] [--saida F]     teste da reversibilidade: "se errar uma vez, dá para desfazer?"
  aplicar     --projeto DIR [--de F] [--sim]  junta as regras de negação no .claude/settings.json (com cópia)
  testar      CHAMADA [--projeto DIR]         diz se uma chamada (ex.: 'Bash(git reset --hard HEAD)') é barrada
  prompt      NOME                            imprime um prompt pronto (pronto, revisor, orquestrador, entrevista, advisor)

Python 3.9+ puro, sem dependências. Licença MIT.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
VERSAO = (AQUI / "VERSION").read_text().strip() if (AQUI / "VERSION").exists() else "0"

# Catálogo de ações comuns. "volta" = dá para desfazer se o Claude errar uma vez?
CATALOGO = [
    {"id": "env", "acao": "ler arquivos de senha (.env)", "volta": False,
     "regras": ["Read(./.env)", "Read(./.env.*)"],
     "porque": "depois que a senha entrou na conversa, não dá para tirar de lá"},
    {"id": "chaves", "acao": "ler chaves e certificados (*.pem, *.key, id_rsa)", "volta": False,
     "regras": ["Read(./**/*.pem)", "Read(./**/*.key)", "Read(~/.ssh/**)"],
     "porque": "chave vazada tem de ser trocada em todo lugar"},
    {"id": "reset", "acao": "descartar trabalho não salvo (git reset --hard, git clean)", "volta": False,
     "regras": ["Bash(git reset --hard *)", "Bash(git clean -f*)", "Bash(git checkout -- *)"],
     "porque": "o que não foi salvo some de vez"},
    {"id": "force", "acao": "reescrever o histórico do servidor (git push --force)", "volta": False,
     "regras": ["Bash(git push --force*)", "Bash(git push -f*)", "Bash(git push * --force*)"],
     "porque": "apaga o trabalho dos outros no remoto"},
    {"id": "apagar", "acao": "apagar pastas inteiras (rm -rf)", "volta": False,
     "regras": ["Bash(rm -rf *)", "Bash(rm -fr *)"],
     "porque": "não tem lixeira no terminal"},
    {"id": "publicar", "acao": "publicar pacote (npm publish, twine upload)", "volta": False,
     "regras": ["Bash(npm publish*)", "Bash(twine upload*)", "Bash(cargo publish*)"],
     "porque": "versão publicada não volta"},
    {"id": "repo", "acao": "apagar repositório no GitHub", "volta": False,
     "regras": ["Bash(gh repo delete*)"],
     "porque": "repositório apagado leva issues e histórico"},
    {"id": "deploy", "acao": "mandar para produção direto (vercel --prod, wrangler deploy)", "volta": None,
     "regras": ["Bash(vercel --prod*)", "Bash(wrangler deploy*)"],
     "porque": "depende: tem rollback? Então pode ficar no automático"},
    {"id": "editar", "acao": "editar arquivos do projeto (com git)", "volta": True, "regras": [],
     "porque": "o git desfaz"},
    {"id": "testes", "acao": "rodar testes e build", "volta": True, "regras": [],
     "porque": "não muda nada fora da máquina"},
]

# Palavras que "gritam" nas instruções feitas para modelos antigos.
GRITOS = re.compile(r"\b(IMPORTANT|NEVER|ALWAYS|MUST|MANDATORY|CRITICAL|IMPORTANTE|NUNCA|SEMPRE|OBRIGAT[ÓO]RIO|JAMAIS)\b|!!!")


def ler_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise SystemExit(f"erro: {p} não é JSON válido ({e})")


def arquivos_settings(projeto: Path | None) -> list[tuple[str, Path]]:
    lista = [("usuário", Path.home() / ".claude" / "settings.json")]
    if projeto:
        lista += [("projeto", projeto / ".claude" / "settings.json"),
                  ("projeto local", projeto / ".claude" / "settings.local.json")]
    return lista


def regras_deny(projeto: Path | None) -> list[str]:
    out: list[str] = []
    for _, p in arquivos_settings(projeto):
        out += ler_json(p).get("permissions", {}).get("deny", []) or []
    return out


# ---------- testar ----------
def _partes(chamada: str) -> tuple[str, str | None]:
    m = re.fullmatch(r"\s*([\w.*-]+)\s*(?:\((.*)\))?\s*", chamada, re.S)
    if not m:
        raise SystemExit(f"erro: chamada mal escrita: {chamada!r} (use Ferramenta(argumento))")
    return m.group(1), m.group(2)


def casa(regra: str, chamada: str) -> bool:
    """Aproximação das regras do Claude Code: nome da ferramenta + padrão com * no argumento.
    'Bash(git reset --hard *)' casa 'Bash(git reset --hard HEAD)'. Regra sem argumento casa a ferramenta toda."""
    rt, ra = _partes(regra)
    ct, ca = _partes(chamada)
    if not fnmatch.fnmatchcase(ct, rt):
        return False
    if ra is None:
        return True
    if ca is None:
        return False
    if rt == "Read" or rt == "Edit" or rt == "Write":
        ra_n, ca_n = ra.removeprefix("./"), ca.removeprefix("./")
        return fnmatch.fnmatchcase(ca_n, ra_n) or fnmatch.fnmatchcase(ca_n, ra_n.replace("**/", ""))
    if ra.endswith(" *") and ca == ra[:-2]:
        return True  # "git reset --hard" sem argumento também é barrado
    return fnmatch.fnmatchcase(ca, ra)


def cmd_testar(a) -> int:
    regras = regras_deny(a.projeto)
    if a.regras:
        regras = list(a.regras)
    hits = [r for r in regras if casa(r, a.chamada)]
    if hits:
        print(f"BARRADA  {a.chamada}\n  pela regra: {hits[0]}")
        return 0
    print(f"PASSA    {a.chamada}\n  nenhuma regra de negação casa; o modo automático é quem decide")
    return 1


# ---------- auditar ----------
def cmd_auditar(a) -> int:
    print(f"Piloto com Freio {VERSAO} — auditoria\n")
    modo, pula = None, False
    for nome, p in arquivos_settings(a.projeto):
        d = ler_json(p)
        perm = d.get("permissions", {})
        if perm.get("defaultMode"):
            modo = perm["defaultMode"]
        if d.get("skipDangerousModePermissionPrompt"):
            pula = True
        estado = "existe" if p.exists() else "não existe"
        print(f"- settings ({nome}): {p}  [{estado}]  deny={len(perm.get('deny', []) or [])}")
    print()
    print(f"Modo de permissão padrão: {modo or 'não definido (o Claude Code usa o padrão da versão)'}")
    if modo == "bypassPermissions":
        print("  ALERTA: tudo liberado. Troque por 'auto' e ponha freio no que não tem volta.")
    elif modo == "auto":
        print("  ok: modo automático. Ele bloqueia a maioria, não tudo: o irreversível vai na lista de negação.")
    if pula:
        print("  aviso: skipDangerousModePermissionPrompt ligado (o aviso do modo perigoso não aparece).")

    deny = regras_deny(a.projeto)
    print(f"\nRegras de negação ativas: {len(deny)}")
    faltam = 0
    for item in CATALOGO:
        if item["volta"] is not False:
            continue
        cobertas = [r for r in item["regras"] if any(casa(d, r.replace("*", "x")) or d == r for d in deny)]
        marca = "ok " if len(cobertas) == len(item["regras"]) else "FALTA"
        if marca != "ok ":
            faltam += 1
        print(f"  [{marca}] {item['acao']}")
    if faltam:
        print(f"\n{faltam} ação(ões) sem volta ainda sem freio. Rode: python3 freio.py entrevista")

    # instruções que gritam
    alvos = [Path.home() / ".claude" / "CLAUDE.md"]
    if a.projeto:
        alvos += [a.projeto / "CLAUDE.md"] + sorted((a.projeto / ".claude" / "skills").glob("*/SKILL.md"))
    total = 0
    linhas_ex = []
    for p in alvos:
        if not p.exists():
            continue
        for n, linha in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if GRITOS.search(linha):
                total += 1
                if len(linhas_ex) < 5:
                    linhas_ex.append(f"  {p}:{n}: {linha.strip()[:90]}")
    print(f"\nLinhas que gritam (IMPORTANTE, NUNCA, !!!): {total}")
    for l in linhas_ex:
        print(l)
    if total:
        print("  Modelo novo não precisa de grito. No Claude Code: /doctor prompt-audit (revisa com a sua aprovação).")
    return 0


# ---------- entrevista ----------
def perguntar(item) -> bool | None:
    while True:
        r = input(f"\nSe o Claude errar UMA vez em \"{item['acao']}\", dá para desfazer? [s/n/pular] ").strip().lower()
        if r in ("s", "sim", "y"):
            return True
        if r in ("n", "nao", "não", "no"):
            return False
        if r in ("p", "pular", ""):
            return None


def cmd_entrevista(a) -> int:
    respostas = ler_json(Path(a.respostas)) if a.respostas else None
    deny: list[str] = []
    relatorio = []
    print("Teste da reversibilidade: se o Claude errar uma vez, dá para desfazer?")
    print("Sim → fica no modo automático.  Não → vai para a lista de negação.\n")
    for item in CATALOGO:
        if respostas is not None:
            volta = respostas.get(item["id"], item["volta"])
        else:
            print(f"- {item['acao']}  (dica: {item['porque']})")
            volta = perguntar(item)
        if volta is False:
            deny += item["regras"]
        relatorio.append((item["acao"], volta))
    for extra in (respostas or {}).get("extras", []):
        if extra.get("volta") is False:
            deny += extra["regras"]
        relatorio.append((extra["acao"], extra.get("volta")))
    print("\nResultado:")
    for acao, volta in relatorio:
        rot = {True: "automático", False: "NEGAR", None: "decidir depois"}[volta]
        print(f"  {rot:>14}  {acao}")
    saida = {"permissions": {"deny": sorted(set(deny))}}
    texto = json.dumps(saida, indent=2, ensure_ascii=False)
    if a.saida:
        Path(a.saida).write_text(texto + "\n")
        print(f"\nRegras gravadas em {a.saida}. Próximo: python3 freio.py aplicar --projeto <pasta> --de {a.saida}")
    else:
        print("\n" + texto)
    return 0


# ---------- aplicar ----------
def cmd_aplicar(a) -> int:
    if a.de:
        novas = ler_json(Path(a.de)).get("permissions", {}).get("deny", [])
    else:
        novas = [r for i in CATALOGO if i["volta"] is False for r in i["regras"]]
    alvo = a.projeto / ".claude" / "settings.json"
    atual = ler_json(alvo)
    deny_atual = atual.get("permissions", {}).get("deny", []) or []
    entram = [r for r in novas if r not in deny_atual]
    print(f"{alvo}\n  já tem {len(deny_atual)} regra(s); entram {len(entram)}:")
    for r in entram:
        print(f"    + {r}")
    if not entram:
        print("  nada a mudar.")
        return 0
    if not a.sim:
        print("\n(prévia) Nada foi gravado. Repita com --sim para gravar (uma cópia do arquivo fica ao lado).")
        return 0
    alvo.parent.mkdir(parents=True, exist_ok=True)
    if alvo.exists():
        copia = alvo.with_name(f"settings.json.antes-freio-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(alvo, copia)
        print(f"  cópia: {copia}")
    atual.setdefault("permissions", {})["deny"] = deny_atual + entram
    alvo.write_text(json.dumps(atual, indent=2, ensure_ascii=False) + "\n")
    print("  gravado. Confira com: python3 freio.py testar 'Bash(git reset --hard HEAD)' --projeto", a.projeto)
    return 0


# ---------- prompt ----------
def cmd_prompt(a) -> int:
    p = AQUI / "prompts" / f"{a.nome}.md"
    if not p.exists():
        nomes = ", ".join(sorted(x.stem for x in (AQUI / "prompts").glob("*.md")))
        raise SystemExit(f"erro: prompt '{a.nome}' não existe. Opções: {nomes}")
    sys.stdout.write(p.read_text())
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="freio.py", description=__doc__.split("\n")[0])
    ap.add_argument("--versao", action="version", version=VERSAO)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("auditar"); s.add_argument("--projeto", type=Path); s.set_defaults(f=cmd_auditar)
    s = sub.add_parser("entrevista"); s.add_argument("--respostas"); s.add_argument("--saida"); s.set_defaults(f=cmd_entrevista)
    s = sub.add_parser("aplicar"); s.add_argument("--projeto", type=Path, required=True); s.add_argument("--de"); s.add_argument("--sim", action="store_true"); s.set_defaults(f=cmd_aplicar)
    s = sub.add_parser("testar"); s.add_argument("chamada"); s.add_argument("--projeto", type=Path); s.add_argument("--regras", nargs="*"); s.set_defaults(f=cmd_testar)
    s = sub.add_parser("prompt"); s.add_argument("nome"); s.set_defaults(f=cmd_prompt)
    a = ap.parse_args(argv)
    proj = getattr(a, "projeto", None)
    if proj is not None and not proj.is_dir():
        raise SystemExit(f"erro: a pasta do projeto não existe: {proj} (confira o caminho em --projeto)")
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
