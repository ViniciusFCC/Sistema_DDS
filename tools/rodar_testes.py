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
import conferir_viva  # noqa: E402  (acrescenta python/ ao caminho)
import openpyxl  # noqa: E402
import viva  # noqa: E402

# Contagens esperadas e fonte (SPEC §6)
TESTES = [
    ("pneu", "tests/test_tire_model.py", 43, "registro-de-versoes-V2_4.md:16"),
    ("oráculos", "tests/test_tire_oracles.py", 5, "registro-de-versoes-V2_4.md:16"),
    ("suspensão", "tests/test_suspension_model.py", 54, "registro-de-versoes-V3_0.md"),
    ("cinemática", "tests/test_kinematics_model.py", 76, "registro-de-versoes-V3_0.md; plano do incremento 2 da V4.0"),
    ("hardpoints", "tests/test_hardpoints.py", 35, "HANDOFF §6.2"),
    ("equilíbrio", "tests/test_equilibrio.py", 28, "planos dos incrementos 1 e 2 da V4.0"),
    ("equilíbrio linear", "tests/test_equilibrio_linear.py", 18, "plano do incremento 2 da V4.0"),
    ("V4.0 (nomes e dados)", "tests/test_v4_0.py", 4, "plano do incremento 3 da V4.0"),
    ("V4.1 (estrutura e CA-07)", "tests/test_v4_1.py", 2, "plano do incremento 4 da V4.1 (TC-WB41-001 e 002)"),
    ("V4.2 (estrutura, CA-07, oráculo das metas e fluxo da viva)", "tests/test_v4_2.py", 4,
     "plano do incremento 5 da V4.2 (TC-WB42-001 a 004)"),
    ("MMM em raio fixo", "tests/test_mmm.py", 11, "plano do incremento 6 (TC-MMM-001 a 011)"),
    ("escada de hipóteses", "tests/test_escada.py", 3, "plano do incremento 6 (TC-ESC-001 a 003)"),
]
MODULOS = ["tire_model", "suspension_model", "kinematics_model", "hardpoints", "atualizar_planilha", "equilibrio",
           "equilibrio_linear", "caso_planilha", "nomes_v4_0", "gerar_v4_0", "dados_planilha", "aba_equilibrio", "gerar_v4_1",
           "origens", "gerar_v4_2", "metas", "aba_metas", "viva", "mmm", "escada"]
MUTACAO = [("tests/mutation_tire.py", 25), ("tests/mutation_equilibrio.py", 6),
           ("tests/mutation_planilha_equilibrio.py", 5), ("tests/mutation_mmm.py", 5)]
# A mutação da planilha recalcula cópias pelo Excel (6 execuções do teste, de minutos cada): o limite de 1800 s dos outros não basta.
TIMEOUT_MUTACAO = {"tests/mutation_planilha_equilibrio.py": 7200, "tests/mutation_mmm.py": 3600}
AUTOTESTE = ("tools/test_comparar_planilhas.py", 15)
RE_RESUMO = re.compile(r"^(\d+) PASS, (\d+) FAIL, de (\d+) testes\s*$")
RE_MUTACAO = re.compile(r"^(\d+) / (\d+)\s*$")
# Teste da planilha (CA-09, EDR-044): Excel via COM ou LibreOffice. Sem motor, sai com
# código 3 e conta como NÃO EXECUTÁVEL, nunca como aprovado (R6).
PLANILHAS = [("tests/test_workbook.py", 19, "pneu (10_TIRE) da V3.0; registro-de-versoes-V3_0.md"),
             ("tests/test_workbook_suspensao.py", 15, "suspensão da V3.0 (15 com a 2ª rodada da revisão metodológica); registro-de-versoes-V3_0.md"),
             ("tests/test_workbook_v4_0.py", 2, "V4.0; plano do incremento 3"),
             ("tests/test_workbook_v4_1.py", 5, "V4.1 (TC-WB41-003 a 006, parte 1 e 2 do 006); plano do incremento 4"),
             ("tests/test_workbook_v4_2.py", 2, "V4.2 (TC-WB42-005 e 006); plano do incremento 5")]


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
    em cada planilha de excel/, sem mudar a estrutura da planilha. A V3.0, a V4.0 (EDR-058) e a V4.1 (EDR-060) têm de estar entre elas."""
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
    for obrigatoria in (CAMINHO_V30, CAMINHO_V40, CAMINHO_V41):
        if RAIZ / obrigatoria not in arquivos:
            ok = False
            linhas.append(f"- `{obrigatoria}` não encontrada: **FAIL**")
    return ok, linhas


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else f"indisponível ({r.stderr.strip()})"


TAG_V30 = "v3.0"
CAMINHO_V30 = "excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx"
CAMINHO_V40 = "excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx"
CAMINHO_V41 = "excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx"
CAMINHO_V42 = "excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx"


def referencia_v30(pasta: Path) -> tuple[Path, str]:
    """EDR-051 (fechamento da V3.0): a referência da V3.0 é o arquivo gravado na tag v3.0, que não muda; a planilha da
    árvore passa a ser o arquivo vivo da equipe. Antes de a tag existir, a referência é o próprio arquivo da árvore."""
    if subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{TAG_V30}"], cwd=RAIZ, capture_output=True).returncode == 0:
        blob = subprocess.run(["git", "show", f"{TAG_V30}:{CAMINHO_V30}"], cwd=RAIZ, capture_output=True, check=True).stdout
        destino = pasta / "V3_0_referencia_tag.xlsx"
        destino.write_bytes(blob)
        return destino, f"tag `{TAG_V30}`"
    return RAIZ / CAMINHO_V30, f"arquivo da árvore (a tag `{TAG_V30}` ainda não existe)"


def v30_igual_a_tag(ref30: Path) -> tuple[bool, str]:
    """CA-07 da V3.0 de excel/ (EDR-063, revê o EDR-051 item 2): o arquivo da árvore é igual ao da tag v3.0 (SHA-256). Ele deixou
    de ser a planilha viva (a viva da equipe é a cópia no Drive); antes de a tag existir, a referência é o próprio arquivo e a
    igualdade é trivial."""
    arvore = RAIZ / CAMINHO_V30
    a, b = viva.sha256(arvore), viva.sha256(ref30)
    return a == b, f"SHA-256 de `{CAMINHO_V30}`: {a}; da referência: {b}"


def secao_viva() -> list[str]:
    """Seção informativa do log (fora do resumo; EDR-063): a viva do Drive contra a referência da versão dela. A suíte verifica o
    repositório, e a viva muda sem commit (o mesmo commit daria resultados diferentes); por isso nunca entra no resumo nem
    reprova. Sem Drive montado (ou viva ilegível), NÃO EXECUTÁVEL. Lê só uma cópia."""
    linhas = ["## Viva da equipe (informativo, EDR-063)", "",
              "Fora do resumo e sem efeito no código de saída: a viva é o arquivo que a equipe preenche no Google Drive e muda sem "
              "commit. Conferida (em cópia local) contra a referência da versão dela, lida na 00_README A3; `tools/conferir_viva.py` "
              "dá o mesmo veredito com código de saída.", ""]
    try:
        arq = viva.localizar_viva()
    except ValueError as e:
        return linhas + [f"- Status: **NÃO EXECUTÁVEL** ({e})", ""]
    if arq is None:
        return linhas + ["- Status: **NÃO EXECUTÁVEL** (nenhuma viva localizada: Drive desmontado e `DDS_VIVA` sem valor)", ""]
    with tempfile.TemporaryDirectory(prefix="dds_viva_", ignore_cleanup_errors=True) as tmp:
        try:
            codigo, rel, ver = conferir_viva.conferir(arq, Path(tmp))
        except Exception as e:   # a seção é informativa: nada aqui derruba a suíte
            return linhas + [f"- Status: **NÃO EXECUTÁVEL** (erro ao conferir: {type(e).__name__}: {e})", ""]
    status = {0: "VIVA FIEL (código 0)", 1: "VIVA DIVERGE (código 1)", 3: "NÃO EXECUTÁVEL (viva não lida, código 3)"}[codigo]
    return linhas + [f"- Status: **{status}**", "", "```text", *rel, "```", ""]


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
    md += ["## Mutação (CA-06)", ""]
    for script, esperado in MUTACAO:
        r = rodar([script], timeout=TIMEOUT_MUTACAO.get(script, 1800))
        linhas = r.stdout.splitlines()
        pre = [l for l in linhas if l.startswith("PRE-CHECAGEM")]
        pre_ok = any(l.startswith("PRE-CHECAGEM OK") for l in pre)
        m = [x for x in map(RE_MUTACAO.match, linhas) if x]
        det, tot = map(int, m[-1].groups()) if m else (None, None)
        ok = pre_ok and det == tot == esperado and r.returncode == 0
        resumo.append(("CA-06", f"mutação ({Path(script).name})", "PASS" if ok else "FAIL"))
        md += [
            f"### `{script}`", "",
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
        # V4.0 = V3.0 da tag + python/gerar_v4_0.py (nomes definidos; EDR-058), comparada com a de excel/ inclusive a estrutura
        out40 = Path(tmp) / "FSAE_EV_Suspension_Fase1_V4_0.xlsx"
        r40 = rodar(["python/gerar_v4_0.py", "--v30", str(REF30), "--saida", str(out40)])
        md.append(f"- V4.0: `python/gerar_v4_0.py --v30 <referência da V3.0> --saida <tmp>/V4_0.xlsx`, código {r40.returncode}")
        if r40.returncode == 0 and out40.exists() and (RAIZ / CAMINHO_V40).exists():
            ok7c, r7c = comparar_planilhas.comparar_xlsx(out40, RAIZ / CAMINHO_V40, comparar_planilhas.FORMULAS_ESPERADAS_V40,
                                                         estrutura=True)
        else:
            ok7c, r7c = False, [f"CA-07 FAIL: gerar_v4_0 não gerou a V4.0 ou falta {CAMINHO_V40}", cauda(r40.stderr)]
        # V4.1 = V4.0 da tag v4.0 + python/gerar_v4_1.py (equilíbrio em fórmulas; EDR-060), comparada com a de excel/ inclusive a estrutura
        out41 = Path(tmp) / "FSAE_EV_Suspension_Fase1_V4_1.xlsx"
        r41 = rodar(["python/gerar_v4_1.py", "--saida", str(out41)])
        md.append(f"- V4.1: `python/gerar_v4_1.py --saida <tmp>/V4_1.xlsx` (a V4.0 sai da tag `v4.0`), código {r41.returncode}")
        if r41.returncode == 0 and out41.exists() and (RAIZ / CAMINHO_V41).exists():
            ok7d, r7d = comparar_planilhas.comparar_xlsx(out41, RAIZ / CAMINHO_V41, comparar_planilhas.FORMULAS_ESPERADAS_V41,
                                                         estrutura=True)
        else:
            ok7d, r7d = False, [f"CA-07 FAIL: gerar_v4_1 não gerou a V4.1 ou falta {CAMINHO_V41}", cauda(r41.stderr)]
    resumo.append(("CA-07", "planilha vs V2.4 entregue", "PASS" if ok7 else "FAIL"))
    resumo.append(("CA-08", "layout vs entregue", "PASS" if ok8 else "FAIL"))
    resumo.append(("CA-07", "planilha vs V3.0 de referência", "PASS" if ok7b else "FAIL"))
    resumo.append(("CA-07", "planilha vs V4.0 de referência (com nomes definidos)", "PASS" if ok7c else "FAIL"))
    resumo.append(("CA-07", "planilha vs V4.1 de referência (equilíbrio em fórmulas)", "PASS" if ok7d else "FAIL"))
    # CA-07 da V3.0 de excel/ (EDR-063, revê o EDR-051 item 2): igual ao arquivo da tag v3.0. A viva da equipe é a cópia da V4.1
    # no Drive; ela aparece só na seção informativa mais abaixo.
    ok7v, r7v = v30_igual_a_tag(REF30)
    resumo.append(("CA-07", "V3.0 de excel/ = arquivo da tag v3.0 (SHA-256)", "PASS" if ok7v else "FAIL"))
    # V4.2 = V4.1 da tag v4.1 + python/gerar_v4_2.py (metas e coerência; projeto T11), comparada com a de excel/ quando existir
    ok7e, r7e = None, []
    with tempfile.TemporaryDirectory(prefix="dds_build42_") as tmp42:
        out42 = Path(tmp42) / "FSAE_EV_Suspension_Fase1_V4_2.xlsx"
        r42 = rodar(["python/gerar_v4_2.py", "--saida", str(out42)])
        md.append(f"- V4.2: `python/gerar_v4_2.py --saida <tmp>/V4_2.xlsx` (a V4.1 sai da tag `v4.1`), código {r42.returncode}")
        if r42.returncode != 0 or not out42.exists():
            ok7e, r7e = False, ["CA-07 FAIL: gerar_v4_2 não gerou a V4.2", cauda(r42.stderr)]
        elif (RAIZ / CAMINHO_V42).exists():
            ok7e, r7e = comparar_planilhas.comparar_xlsx(out42, RAIZ / CAMINHO_V42, comparar_planilhas.FORMULAS_ESPERADAS_V42,
                                                         estrutura=True)
        else:
            r7e = [f"{CAMINHO_V42} ainda não existe (a cópia para excel/ é um commit próprio): a V4.2 foi gerada, "
                   "mas a comparação com a de excel/ não pôde ser feita"]
    resumo.append(("CA-07", "planilha vs V4.2 de referência (metas e coerência)",
                   "NÃO EXECUTÁVEL" if ok7e is None else "PASS" if ok7e else "FAIL"))
    md += [f"- Referência da V3.0: {ORIGEM_REF30}. A regeneração e os testes CA-09 usam a referência; a V3.0 de excel/ tem de ser "
           "igual ao arquivo da tag (a viva da equipe é outro arquivo, no Drive).", "",
           "```text", *r7, *r8, "--- V3.0 (regeneração vs referência) ---", *r7b, f"--- V3.0 de excel/ = tag v3.0 --- {r7v}",
           "--- V4.0 (regeneração vs excel/) ---", *r7c, "--- V4.1 (regeneração vs excel/) ---", *r7d,
           "--- V4.2 (regeneração vs excel/) ---", *r7e, "```", ""]

    # --- Viva da equipe (informativo; fora do resumo) ---
    md += secao_viva()

    # --- Versão gravada na planilha (fase B, passo 3) ---
    ok_ver, linhas_ver = versao_planilhas()
    resumo.append(("versão", "00_README!A3 = versão no nome do arquivo", "PASS" if ok_ver else "FAIL"))
    md += ["## Versão gravada na planilha (fase B, passo 3)", "",
           "A versão escrita em `00_README!A3` precisa ser a mesma do nome do arquivo.", "",
           *linhas_ver, ""]

    # --- Teste da planilha, Excel x Python (CA-09, EDR-044) ---
    md += ["## Teste da planilha (CA-09)", ""]
    for script, esperado, fonte in PLANILHAS:
        args = [str(REF30)] if script.endswith("suspensao.py") else [str(RAIZ / CAMINHO_V40)] if script.endswith("_v4_0.py") else [] if script.endswith(("_v4_1.py", "_v4_2.py")) else [
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
