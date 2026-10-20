"""CA-05, CA-06, CA-07, CA-08, CA-09 e CA-10: roda os testes e o build e grava o log.

Uso:
    uv run python -X utf8 tools/rodar_testes.py [--saida LOG.md] [--titulo TEXTO]

Sem --saida, o log vai para build/verificacao-ultima.md (fora do Git). Os logs de
evidência em docs/migracao/ só são gravados quando pedidos com --saida.

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
import openpyxl  # noqa: E402

# Contagens esperadas e fonte (SPEC §6)
TESTES = [
    ("pneu", "tests/test_tire_model.py", 43, "registro-de-versoes-V2_4.md:16"),
    ("oráculos", "tests/test_tire_oracles.py", 5, "registro-de-versoes-V2_4.md:16"),
    ("suspensão", "tests/test_suspension_model.py", 54, "registro-de-versoes-V3_0.md"),
    ("cinemática", "tests/test_kinematics_model.py", 74, "registro-de-versoes-V3_0.md"),
    ("hardpoints", "tests/test_hardpoints.py", 35, "HANDOFF §6.2"),
    ("equilíbrio", "tests/test_equilibrio.py", 20, "plano do incremento 1 da V4.0"),
]
MODULOS = ["tire_model", "suspension_model", "kinematics_model", "hardpoints", "atualizar_planilha"]
MUTACAO = ("tests/mutation_tire.py", 25)
AUTOTESTE = ("tools/test_comparar_planilhas.py", 15)
RE_RESUMO = re.compile(r"^(\d+) PASS, (\d+) FAIL, de (\d+) testes\s*$")
RE_MUTACAO = re.compile(r"^(\d+) / (\d+)\s*$")
# Teste da planilha (CA-09, EDR-044): Excel via COM ou LibreOffice. Sem motor, sai com
# código 3 e conta como NÃO EXECUTÁVEL, nunca como aprovado (R6).
PLANILHAS = [("tests/test_workbook.py", 19, "pneu (10_TIRE) da V3.0; registro-de-versoes-V3_0.md"),
             ("tests/test_workbook_suspensao.py", 15, "suspensão da V3.0 (15 com a 2ª rodada da revisão metodológica); registro-de-versoes-V3_0.md")]


def rodar(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONUTF8="1")
    cmd = [sys.executable, "-X", "utf8", *args]
    try:
        return subprocess.run(
            cmd, cwd=RAIZ, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        saida = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return subprocess.CompletedProcess(cmd, 124, saida, f"TIMEOUT depois de {timeout} s")


def origens_modulos() -> tuple[bool, list[str]]:
    """De onde os testes importam os módulos (CA-10). Os testes os acham pelo projeto
    instalado pelo uv (EDR-043); se o .pth apontar para outra cópia do repositório,
    eles rodariam outro código. Exige que todos venham de RAIZ/python."""
    codigo = f"import {', '.join(MODULOS)}\n" + "".join(f"print({m}.__file__)\n" for m in MODULOS)
    r = rodar(["-c", codigo])
    origens = r.stdout.splitlines()
    dentro = [Path(o).resolve().is_relative_to(RAIZ / "python") for o in origens]
    ok = r.returncode == 0 and len(origens) == len(MODULOS) and all(dentro)
    return ok, origens or [f"falhou: {cauda(r.stderr, 3)}"]


def cauda(texto: str, n: int = 15) -> str:
    linhas = texto.strip().splitlines()
    return "\n".join(linhas[-n:])


def bloco(titulo: str, texto: str) -> list[str]:
    if not texto.strip():
        return []
    return [f"<details><summary>{titulo}</summary>", "", "```text", texto, "```", "", "</details>", ""]


def versao_planilhas() -> tuple[bool, list[str]]:
    """Fase B, passo 3: a versão da planilha fica no nome do arquivo (EDR-043) e no
    texto de 00_README!A3 ("Versão do workbook: V2.4 ..."). Confere que os dois batem
    em cada planilha de excel/, sem mudar a estrutura da planilha."""
    linhas, ok = [], True
    arquivos = sorted((RAIZ / "excel").glob("FSAE_EV_Suspension_Fase1_V*.xlsx"))
    for f in arquivos:
        m_nome = re.search(r"_V(\d+)[._](\d+)\.xlsx$", f.name)
        wb = openpyxl.load_workbook(f, read_only=True)
        try:  # no modo read_only o arquivo fica aberto (e travado no Windows) até o close()
            a3 = wb["00_README"]["A3"].value
        finally:
            wb.close()
        m_a3 = re.match(r"Versão do workbook: V(\d+)\.(\d+)\b", a3 or "")
        bate = bool(m_nome and m_a3 and m_nome.groups() == m_a3.groups())
        ok &= bate
        lido = f"V{'.'.join(m_a3.groups())}" if m_a3 else f"ilegível: {str(a3)[:60]!r}"
        linhas.append(f"- `excel/{f.name}`: A3 diz {lido}: **{'PASS' if bate else 'FAIL'}**")
    if not arquivos:
        ok, linhas = False, ["- nenhuma planilha encontrada em `excel/`: **FAIL**"]
    return ok, linhas


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else f"indisponível ({r.stderr.strip()})"


TAG_V30 = "v3.0"
CAMINHO_V30 = "excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx"


def referencia_v30(pasta: Path) -> tuple[Path, str]:
    """EDR-051 (fechamento da V3.0): a referência da V3.0 é o arquivo gravado na tag v3.0, que não muda; a planilha da
    árvore passa a ser o arquivo vivo da equipe. Antes de a tag existir, a referência é o próprio arquivo da árvore."""
    if subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{TAG_V30}"], cwd=RAIZ, capture_output=True).returncode == 0:
        blob = subprocess.run(["git", "show", f"{TAG_V30}:{CAMINHO_V30}"], cwd=RAIZ, capture_output=True, check=True).stdout
        destino = pasta / "V3_0_referencia_tag.xlsx"
        destino.write_bytes(blob)
        return destino, f"tag `{TAG_V30}`"
    return RAIZ / CAMINHO_V30, f"arquivo da árvore (a tag `{TAG_V30}` ainda não existe)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, default=RAIZ / "build" / "verificacao-ultima.md")
    ap.add_argument("--titulo", default="Verificação da V3.0 nesta máquina")
    a = ap.parse_args()

    md: list[str] = []
    resumo: list[tuple[str, str, str]] = []  # (CA, item, status)
    pasta_ref = tempfile.TemporaryDirectory(prefix="dds_ref_", ignore_cleanup_errors=True)
    REF30, ORIGEM_REF30 = referencia_v30(Path(pasta_ref.name))

    commit = git("rev-parse", "--short", "HEAD")
    sujo = git("status", "--porcelain", "--untracked-files=no")
    ok_mod, origens = origens_modulos()
    resumo.append(("CA-10", "módulos importados de python/", "PASS" if ok_mod else "FAIL"))
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
        f"- Módulos importados de ({'PASS' if ok_mod else 'FAIL'}): " + ", ".join(f"`{o}`" for o in origens),
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
        pulados = "\n".join(l for l in r.stdout.splitlines() if l.startswith("[SKIP]"))
        detalhes += bloco(f"{script}: testes FAIL", falhas)
        detalhes += bloco(f"{script}: testes SKIP (não contados)", pulados)
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
    # Antes de confiar no comparador, ele precisa acusar alterações conhecidas.
    r = rodar([AUTOTESTE[0]])
    resumos = [m for m in map(RE_RESUMO.match, r.stdout.splitlines()) if m]
    n_pass, n_fail, total = map(int, resumos[-1].groups()) if resumos else (0, -1, -1)
    ok_cmp = n_fail == 0 and n_pass == total == AUTOTESTE[1] and r.returncode == 0
    resumo.append(("CA-07", "autoteste do comparador", "PASS" if ok_cmp else "FAIL"))
    md.append(f"- Autoteste do comparador (`{AUTOTESTE[0]}`): {n_pass} PASS, {n_fail} FAIL, de {total}"
              f" (esperado {AUTOTESTE[1]}): **{'PASS' if ok_cmp else 'FAIL'}**")
    md += bloco("autoteste do comparador: FAIL", "\n".join(l for l in r.stdout.splitlines() if l.startswith("[FAIL]")))
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
        # V3.0 = V2.4 regenerada + python/atualizar_planilha.py (EDR-045 a EDR-049)
        out25 = Path(tmp) / "FSAE_EV_Suspension_Fase1_V3_0.xlsx"
        r25 = rodar(["python/atualizar_planilha.py", str(out), str(out25), "--layout", str(lay)]) if out.exists() else None
        md.append(f"- V3.0: `python/atualizar_planilha.py <tmp>/V2_4.xlsx <tmp>/V3_0.xlsx`, código {r25.returncode if r25 else 'não rodou'}")
        if r25 is not None and r25.returncode == 0 and out25.exists():
            ok7b, r7b = comparar_planilhas.comparar_xlsx(out25, REF30, comparar_planilhas.FORMULAS_ESPERADAS_V30)
        else:
            ok7b, r7b = False, ["CA-07 FAIL: atualizar_planilha não gerou a V3.0"] + ([cauda(r25.stderr)] if r25 else [])
    resumo.append(("CA-07", "planilha vs V2.4 entregue", "PASS" if ok7 else "FAIL"))
    resumo.append(("CA-08", "layout vs entregue", "PASS" if ok8 else "FAIL"))
    resumo.append(("CA-07", "planilha vs V3.0 de referência", "PASS" if ok7b else "FAIL"))
    # CA-07 da planilha viva (EDR-051): tudo igual à referência menos as células de entrada (atualizar_planilha.celulas_de_entrada)
    sys.path.insert(0, str(RAIZ / "python"))
    import atualizar_planilha  # noqa: E402
    ok7v, r7v = comparar_planilhas.comparar_viva(RAIZ / CAMINHO_V30, REF30, atualizar_planilha.celulas_de_entrada())
    resumo.append(("CA-07", "planilha viva vs referência (só entradas mudam)", "PASS" if ok7v else "FAIL"))
    md += [f"- Referência da V3.0: {ORIGEM_REF30}. A regeneração e os testes CA-09 usam a referência; a planilha da árvore "
           "é o arquivo vivo e só passa pela verificação de estrutura.", "",
           "```text", *r7, *r8, "--- V3.0 (regeneração vs referência) ---", *r7b, "--- V3.0 viva ---", *r7v, "```", ""]

    # --- Versão gravada na planilha (fase B, passo 3) ---
    ok_ver, linhas_ver = versao_planilhas()
    resumo.append(("versão", "00_README!A3 = versão no nome do arquivo", "PASS" if ok_ver else "FAIL"))
    md += ["## Versão gravada na planilha (fase B, passo 3)", "",
           "A versão escrita em `00_README!A3` precisa ser a mesma do nome do arquivo.", "",
           *linhas_ver, ""]

    # --- Teste da planilha, Excel x Python (CA-09, EDR-044) ---
    md += ["## Teste da planilha (CA-09)", ""]
    for script, esperado, fonte in PLANILHAS:
        args = [str(REF30)] if script.endswith("suspensao.py") else [
            str(REF30), str(RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V2.1.xlsx"), str(RAIZ / "data" / "layout_V2_4.json"),
            str(RAIZ / "data" / "Hoosier_R25B_13x7_TTC_provisional.tir")]
        r = rodar([script, *args])
        linhas = r.stdout.splitlines()
        motor = next((l for l in linhas if l.startswith(("MOTOR:", "NÃO EXECUTÁVEL:"))), "MOTOR: (não informado)")
        resumos = [m for m in map(RE_RESUMO.match, linhas) if m]
        if r.returncode == 3 and motor.startswith("NÃO EXECUTÁVEL"):
            st, obtido = "NÃO EXECUTÁVEL", "não rodou"
        elif resumos:
            n_pass, n_fail, total = map(int, resumos[-1].groups())
            obtido = f"{n_pass} PASS, {n_fail} FAIL, de {total}"
            st = "PASS" if n_fail == 0 and n_pass == total == esperado and r.returncode == 0 else "FAIL"
        else:
            st, obtido = "FAIL", "sem linha de resumo"
        resumo.append(("CA-09", f"planilha Excel x Python ({Path(script).stem})", st))
        md += [f"- `{script}`: esperado {esperado} ({fonte}); obtido {obtido}; código {r.returncode}: **{st}**",
               f"- {motor}", ""]
        md += bloco(f"{script}: testes FAIL", "\n".join(l for l in linhas if l.startswith("[FAIL]")))
        md += bloco(f"{script}: stderr (final)", cauda(r.stderr))

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
