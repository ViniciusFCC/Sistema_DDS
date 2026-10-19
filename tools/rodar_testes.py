"""CA-05, CA-06, CA-07, CA-08, CA-09 e CA-10: roda os testes e o build e grava o log.

Uso:
    uv run python -X utf8 tools/rodar_testes.py [--saida LOG.md] [--titulo TEXTO]

Cada script roda com `sys.executable -X utf8` e cwd na raiz (os scripts acham
dados pelo próprio caminho; layout do EDR-043). PYTHONUTF8=1 vai
no ambiente para que os subprocessos da mutação também usem UTF-8 (R4, sem
editar o código). "Passou" = a última linha "N PASS, M FAIL, de T testes" com
M = 0, N = T = esperado e código de saída 0. A planilha é gerada numa pasta
temporária, nunca por cima da entregue. Não modifica os scripts que verifica (R7).
"""
import argparse
import datetime as dt
import os
import platform
import re
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import comparar_planilhas  # noqa: E402

# Contagens esperadas e fonte (SPEC §6)
TESTES = [
    ("pneu", "tests/test_tire_model.py", 43, "registro-de-versoes-V2_4.md:16"),
    ("oráculos", "tests/test_tire_oracles.py", 5, "registro-de-versoes-V2_4.md:16"),
    ("suspensão", "tests/test_suspension_model.py", 42, "HANDOFF §6.2"),
    ("cinemática", "tests/test_kinematics_model.py", 53, "HANDOFF §6.2"),
    ("hardpoints", "tests/test_hardpoints.py", 35, "HANDOFF §6.2"),
]
MUTACAO = ("tests/mutation_tire.py", 23)
RE_RESUMO = re.compile(r"^(\d+) PASS, (\d+) FAIL, de (\d+) testes\s*$")
RE_MUTACAO = re.compile(r"^(\d+) / (\d+)\s*$")
NAO_EXECUTAVEL = (
    "tests/test_workbook.py",
    "depende de LibreOffice e de `/mnt/skills/public/xlsx/scripts/recalc.py` "
    "(linhas 10 e 28, chamado com `python3`), que não existem nesta máquina (SPEC D2). "
    "Na fase A ele nunca conta como aprovado (R6). Resultado registrado no sandbox: 19/19 "
    "(registro-de-versoes-V2_4.md:17), não reproduzido aqui.",
)


def rodar(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, "-X", "utf8", *args], cwd=RAIZ, env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def cauda(texto: str, n: int = 15) -> str:
    linhas = texto.strip().splitlines()
    return "\n".join(linhas[-n:])


def bloco(titulo: str, texto: str) -> list[str]:
    if not texto.strip():
        return []
    return [f"<details><summary>{titulo}</summary>", "", "```text", texto, "```", "", "</details>", ""]


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout.strip() or r.stderr.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, default=RAIZ / "docs" / "migracao" / "verificacao-V2.4-local.md")
    ap.add_argument("--titulo", default="Verificação da V2.4 nesta máquina")
    a = ap.parse_args()

    md: list[str] = []
    resumo: list[tuple[str, str, str]] = []  # (CA, item, status)

    commit = git("rev-parse", "--short", "HEAD")
    sujo = git("status", "--porcelain", "--untracked-files=no")
    md += [
        f"# {a.titulo}", "",
        "Gerado por `tools/rodar_testes.py`. Não edite à mão: rode de novo.", "",
        "## Ambiente (CA-10)", "",
        f"- Data: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Commit: `{commit}`" + (" (com mudanças não commitadas em arquivos versionados)" if sujo else ""),
        f"- Sistema: {platform.platform()}",
        f"- Python: {platform.python_version()} ({sys.executable})",
        f"- numpy {version('numpy')}, scipy {version('scipy')}, openpyxl {version('openpyxl')} (fixados no `uv.lock`)",
        "- Execução: `sys.executable -X utf8 <script>`, cwd=raiz do repositório, `PYTHONUTF8=1`",
        "",
        "## Testes (CA-05)", "",
        "| Conjunto | Script | Esperado | Obtido | Código | Status | Fonte do esperado |",
        "|---|---|---|---|---|---|---|",
    ]
    detalhes: list[str] = []
    for nome, script, esperado, fonte in TESTES:
        r = rodar([script])
        resumos = [m for m in map(RE_RESUMO.match, r.stdout.splitlines()) if m]
        if resumos:
            n_pass, n_fail, total = map(int, resumos[-1].groups())
            obtido = f"{n_pass} PASS, {n_fail} FAIL, de {total}"
            ok = n_fail == 0 and n_pass == total == esperado and r.returncode == 0
        else:
            obtido, ok = "sem linha de resumo", False
        status = "PASS" if ok else "FAIL"
        resumo.append(("CA-05", nome, status))
        md.append(f"| {nome} | `{script}` | {esperado} | {obtido} | {r.returncode} | **{status}** | {fonte} |")
        falhas = "\n".join(l for l in r.stdout.splitlines() if l.startswith("[FAIL]"))
        detalhes += bloco(f"{script}: testes FAIL", falhas)
        detalhes += bloco(f"{script}: stderr (final)", cauda(r.stderr))
    md += [""] + detalhes

    # --- Mutação (CA-06) ---
    script, esperado = MUTACAO
    r = rodar([script])
    linhas = r.stdout.splitlines()
    pre = [l for l in linhas if l.startswith("PRE-CHECAGEM")]
    pre_ok = any(l.startswith("PRE-CHECAGEM OK") for l in pre)
    m = [x for x in map(RE_MUTACAO.match, linhas) if x]
    det, tot = map(int, m[-1].groups()) if m else (None, None)
    ok = pre_ok and det == tot == esperado and r.returncode == 0
    resumo.append(("CA-06", "mutação", "PASS" if ok else "FAIL"))
    md += [
        "## Mutação (CA-06)", "",
        f"- Esperado: {esperado}/{esperado} detectados, com a pré-checagem do original passando.",
        f"- Pré-checagem: {pre[0] if pre else 'AUSENTE (o script não verifica o original)'}",
        f"- Obtido: {det}/{tot} detectados; código de saída {r.returncode}",
        f"- Status: **{'PASS' if ok else 'FAIL'}**",
        "",
    ]
    md += bloco(f"{script}: saída", r.stdout.strip())
    md += bloco(f"{script}: stderr (final)", cauda(r.stderr))

    # --- Build e comparação (CA-07, CA-08) ---
    md += ["## Planilha regenerada (CA-07, CA-08)", ""]
    with tempfile.TemporaryDirectory(prefix="dds_build_") as tmp:
        out = Path(tmp) / "FSAE_EV_Suspension_Fase1_V2_4.xlsx"
        lay = Path(tmp) / "layout_V2_4.json"
        r = rodar(["python/build_workbook.py", str(out), "--layout", str(lay)])
        md.append(f"- Build: `python/build_workbook.py <tmp>/FSAE_EV_Suspension_Fase1_V2_4.xlsx --layout <tmp>/layout_V2_4.json`, código {r.returncode}")
        md += [""] + bloco("build: stdout", cauda(r.stdout)) + bloco("build: stderr (final)", cauda(r.stderr))
        if r.returncode == 0 and out.exists() and lay.exists():
            ok7, r7 = comparar_planilhas.comparar_xlsx(out)
            ok8, r8 = comparar_planilhas.comparar_json(lay)
        else:
            ok7, r7 = False, ["CA-07 FAIL: build não gerou a planilha"]
            ok8, r8 = False, ["CA-08 FAIL: build não gerou o layout"]
    resumo.append(("CA-07", "planilha vs V2.4 entregue", "PASS" if ok7 else "FAIL"))
    resumo.append(("CA-08", "layout vs entregue", "PASS" if ok8 else "FAIL"))
    md += ["```text", *r7, *r8, "```", ""]

    # --- NÃO EXECUTÁVEL (CA-09) ---
    resumo.append(("CA-09", NAO_EXECUTAVEL[0], "NÃO EXECUTÁVEL"))
    md += ["## Teste da planilha (CA-09)", "", f"- `{NAO_EXECUTAVEL[0]}`: **NÃO EXECUTÁVEL**. {NAO_EXECUTAVEL[1]}", ""]

    md[md.index("## Testes (CA-05)"):md.index("## Testes (CA-05)")] = [
        "## Resumo", "", "| CA | Item | Status |", "|---|---|---|",
        *[f"| {ca} | {item} | **{st}** |" for ca, item, st in resumo], "",
    ]
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    for ca, item, st in resumo:
        print(f"{ca}  {st:15s} {item}")
    print(f"log: {a.saida}")
    falhou = any(st == "FAIL" for _, _, st in resumo)
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()
