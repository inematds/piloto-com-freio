import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import freio  # noqa: E402


def roda(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        cod = freio.main(list(args))
    return cod, buf.getvalue()


class Casa(unittest.TestCase):
    def test_bash_prefixo(self):
        self.assertTrue(freio.casa("Bash(git reset --hard *)", "Bash(git reset --hard HEAD~3)"))
        self.assertTrue(freio.casa("Bash(git reset --hard *)", "Bash(git reset --hard)"))
        self.assertFalse(freio.casa("Bash(git reset --hard *)", "Bash(git reset --soft HEAD)"))

    def test_read_env(self):
        self.assertTrue(freio.casa("Read(./.env)", "Read(./.env)"))
        self.assertTrue(freio.casa("Read(./.env.*)", "Read(.env.local)"))
        self.assertFalse(freio.casa("Read(./.env)", "Read(./README.md)"))

    def test_ferramenta_inteira(self):
        self.assertTrue(freio.casa("mcp__gmail__send_email", "mcp__gmail__send_email(para=todos)"))
        self.assertFalse(freio.casa("Bash(rm -rf *)", "Edit(app.py)"))


class Fluxo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_entrevista_aplicar_testar(self):
        regras = self.tmp / "regras.json"
        cod, out = roda("entrevista", "--respostas", str(RAIZ / "exemplos/respostas.json"), "--saida", str(regras))
        self.assertEqual(cod, 0)
        deny = json.loads(regras.read_text())["permissions"]["deny"]
        self.assertIn("Read(./.env)", deny)
        self.assertIn("mcp__gmail__send_email", deny)
        self.assertNotIn("Bash(vercel --prod*)", deny)  # deploy com volta fica no automático

        # prévia não grava
        cod, out = roda("aplicar", "--projeto", str(self.tmp), "--de", str(regras))
        self.assertFalse((self.tmp / ".claude/settings.json").exists())
        self.assertIn("prévia", out)

        # grava preservando o que já existe
        (self.tmp / ".claude").mkdir()
        (self.tmp / ".claude/settings.json").write_text(json.dumps({"model": "x", "permissions": {"deny": ["Bash(sudo *)"]}}))
        cod, out = roda("aplicar", "--projeto", str(self.tmp), "--de", str(regras), "--sim")
        d = json.loads((self.tmp / ".claude/settings.json").read_text())
        self.assertEqual(d["model"], "x")
        self.assertEqual(d["permissions"]["deny"][0], "Bash(sudo *)")
        self.assertIn("Bash(git push --force*)", d["permissions"]["deny"])
        self.assertTrue(list((self.tmp / ".claude").glob("settings.json.antes-freio-*")))

        # idempotente
        cod, out = roda("aplicar", "--projeto", str(self.tmp), "--de", str(regras), "--sim")
        self.assertIn("nada a mudar", out)

        cod, out = roda("testar", "Bash(git reset --hard HEAD)", "--projeto", str(self.tmp))
        self.assertEqual(cod, 0)
        self.assertIn("BARRADA", out)
        cod, out = roda("testar", "Bash(git status)", "--projeto", str(self.tmp))
        self.assertEqual(cod, 1)

    def test_auditar_aponta_gritos(self):
        (self.tmp / "CLAUDE.md").write_text("IMPORTANT!!! ALWAYS use the brand colours\nuse tom leve\n")
        cod, out = roda("auditar", "--projeto", str(self.tmp))
        self.assertIn("Linhas que gritam", out)
        self.assertIn("/doctor prompt-audit", out)
        self.assertIn("FALTA", out)

    def test_projeto_inexistente(self):
        with self.assertRaises(SystemExit) as c:
            roda("aplicar", "--projeto", str(self.tmp / "nao-existe"), "--sim")
        self.assertIn("não existe", str(c.exception))
        self.assertFalse((self.tmp / "nao-existe").exists())

    def test_prompts(self):
        for nome in ("pronto", "revisor", "orquestrador", "entrevista", "advisor"):
            cod, out = roda("prompt", nome)
            self.assertTrue(out.strip())

    def test_hook_stop(self):
        hook = RAIZ / "hooks/conferir-antes-de-parar.sh"
        ok = subprocess.run(["bash", str(hook)], input="{}", text=True, capture_output=True, env={"CHECAGEM": "true", "PATH": "/usr/bin:/bin"})
        self.assertEqual(ok.returncode, 0)
        falha = subprocess.run(["bash", str(hook)], input="{}", text=True, capture_output=True, env={"CHECAGEM": "echo quebrou; false", "PATH": "/usr/bin:/bin"})
        self.assertEqual(falha.returncode, 2)
        self.assertIn("quebrou", falha.stderr)
        laco = subprocess.run(["bash", str(hook)], input='{"stop_hook_active": true}', text=True, capture_output=True, env={"CHECAGEM": "false", "PATH": "/usr/bin:/bin"})
        self.assertEqual(laco.returncode, 0)


if __name__ == "__main__":
    unittest.main()
