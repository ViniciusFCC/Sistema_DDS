"""
Testes da fundação da V4.0 (incremento 3): nomes definidos e dados por chave.
TC-WB40-001 (ID autorizado pelo usuário): tabela de nomes gerada da V3.0 da tag v3.0 é válida e completa
(nomes únicos e aceitos pelo Excel, células existentes, entradas e resultados cobertos, CSV commitado em dia) e
`verificar_cobertura` recusa entrada sem nome, listando as células.
TC-WB40-002: a V4.0 gerada da tag tem exatamente os nomes da tabela (nome -> destino, escopo do workbook), as mesmas
abas e as 387 fórmulas da V3.0 com texto idêntico, valores iguais fora das células de `alteracoes_v4_0()`, e o gerador
recusa saída em excel/ ou igual à origem antes de abrir qualquer arquivo.
TC-WB40-003: CA-07 da V4.0: a regeneração a partir da tag é igual à excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx
(células, fórmulas, nomes definidos, validações e formatação condicional).
Roda como script: uv run python -X utf8 tests/test_v4_0.py
A V3.0 de partida é o arquivo da tag v3.0, extraído para uma pasta temporária (nunca a planilha viva).
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string
from openpyxl.worksheet.formula import ArrayFormula

import atualizar_planilha as ap
import gerar_v4_0 as gv
import nomes_v4_0 as nv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import comparar_planilhas as cp  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = Path(HERE).parent
CSV_NOMES = RAIZ / "data" / "nomes_V4_0.csv"
TAG_V30 = "v3.0"
CAMINHO_V30 = "excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx"
results = []


def raises(fn, exc=ValueError, needle=None):
    try:
        fn()
        return False
    except exc as e:
        return needle is None or needle in str(e)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def extrair_v30(pasta: Path) -> Path:
    """Arquivo da tag v3.0 numa pasta temporária (binário, sem passar por texto)."""
    destino = pasta / "V3_0_tag.xlsx"
    with open(destino, "wb") as f:
        subprocess.run(["git", "show", f"{TAG_V30}:{CAMINHO_V30}"], cwd=RAIZ, stdout=f, check=True)
    return destino


def eh_formula(v) -> bool:
    return isinstance(v, ArrayFormula) or (isinstance(v, str) and v.startswith("="))


with tempfile.TemporaryDirectory() as tmp:
    v30 = extrair_v30(Path(tmp))
    tabela = nv.tabela_nomes(v30)
    wb = openpyxl.load_workbook(v30)
    try:
        formulas = {(ws.title, c.coordinate) for ws in wb.worksheets if ws.title[:2] in nv.ABAS_RES
                    for lin in ws.iter_rows() for c in lin if eh_formula(c.value)}
        abas = set(wb.sheetnames)
        dims = {ws.title: (ws.max_row, ws.max_column) for ws in wb.worksheets}
    finally:
        wb.close()

    # ---------------- TC-WB40-001 ----------------
    nomes = [n.nome for n in tabela]
    unicos = len(set(nomes)) == len(nomes)
    invalidos = [n for n in nomes if not nv.NOME_VALIDO.fullmatch(n)]
    referencias = [n for n in nomes if nv.parece_referencia(n)]

    def existe(aba, cel):
        if aba not in abas:
            return False
        m = re.fullmatch(r"([A-Z]+)(\d+)", cel)
        return bool(m) and int(m.group(2)) <= dims[aba][0] and column_index_from_string(m.group(1)) <= dims[aba][1]

    inexistentes = [(n.aba, n.celula) for n in tabela if not existe(n.aba, n.celula)]
    por_celula: dict = {}
    for n in tabela:
        por_celula.setdefault((n.aba, n.celula), []).append(n)
    duplicadas = [k for k, v in por_celula.items() if len(v) > 1]
    entradas = ap.celulas_de_entrada()
    ent_mal = sorted(k for k in entradas
                     if len(por_celula.get(k, [])) != 1 or por_celula[k][0].papel not in ("ent", "org", "fte"))
    ent_sobra = sorted(k for k, v in por_celula.items() if v[0].papel in ("ent", "org", "fte") and k not in entradas)
    res_mal = sorted(k for k in formulas if len(por_celula.get(k, [])) != 1 or por_celula[k][0].papel != "res")
    res_sobra = sorted(k for k, v in por_celula.items() if v[0].papel == "res" and k not in formulas)
    papeis_ok = all(n.papel in ("ent", "org", "fte", "res") for n in tabela)
    convencao = [n.nome for n in tabela if not n.nome.startswith(f"{n.papel}_{n.aba[:2]}_")]
    sus_mal = [n.nome for n in tabela if n.sus_id and not all(re.fullmatch(r"SUS-\d{3}(-[FR])?", s)
                                                               for s in n.sus_id.split(";"))]
    ordem_ok = tabela == sorted(tabela, key=lambda n: (n.aba, int(re.sub(r"[A-Z]", "", n.celula)),
                                                         column_index_from_string(re.sub(r"\d", "", n.celula))))
    deterministica = nv.tabela_nomes(v30) == tabela
    csv_igual = CSV_NOMES.exists() and nv.ler_tabela(CSV_NOMES) == tabela
    csv_lf = CSV_NOMES.exists() and b"\r" not in CSV_NOMES.read_bytes()
    csv_cab = CSV_NOMES.exists() and CSV_NOMES.read_bytes().split(b"\n", 1)[0] == b"nome,aba,celula,papel,sus_id,rotulo"
    # Ida e volta do CSV numa pasta temporária (UTF-8, LF, rótulos com vírgula, aspas e acento).
    with tempfile.TemporaryDirectory() as tmp2:
        p = Path(tmp2) / "nomes.csv"
        nv.escrever_tabela(tabela, p)
        ida_volta = nv.ler_tabela(p) == tabela
    # verificar_cobertura (antigo 009): passa com tudo coberto; sem um nome, ValueError que lista as células.
    cob_ok = not raises(lambda: nv.verificar_cobertura(tabela, entradas), Exception)
    faltam = [("05_VEHICLE", "B5"), ("10_TIRE", "B86")]
    parcial = [n for n in tabela if (n.aba, n.celula) not in faltam]
    cob_erro = raises(lambda: nv.verificar_cobertura(parcial, entradas), ValueError, "05_VEHICLE!B5") and \
        raises(lambda: nv.verificar_cobertura(parcial, entradas), ValueError, "10_TIRE!B86")
    ref_ok = all(nv.parece_referencia(x) for x in ("A1", "xfd1048576", "R1C1", "r", "C", "RC", "R12", "abc7")) and \
        not any(nv.parece_referencia(x) for x in ("XFE1", "A1048577", "A0", "res_05_x1", "ent_10_b", "R1C1_x"))
    regex_ok = all(nv.NOME_VALIDO.fullmatch(x) for x in ("a", "ent_05_x", "A" * 255)) and \
        not any(nv.NOME_VALIDO.fullmatch(x) for x in ("1a", "_a", "a-b", "a b", "ação", "A" * 256, ""))
    cont = {p: sum(1 for n in tabela if n.papel == p) for p in ("ent", "org", "fte", "res")}
    # Correção 1 (controlador): letras gregas transliteradas; sus_id só do rótulo e da coluna de ID, nunca da Fonte.
    grego_ok = nv.slug("α [rad]") == "alfa_rad" and nv.slug("Δ Fz (μ, γ)") == "delta_fz_mu_gama" and         nv.slug("Kyγ0 ε") == "kygama0_epsilon" and nv.slug("ÿ Ж z") == "y_z"
    sus_de = {(n.aba, n.celula): n.sus_id for n in tabela}
    sus_rotulo_ok = sus_de.get(("05_VEHICLE", "B5")) == "SUS-002" and sus_de.get(("05_VEHICLE", "F5")) == "SUS-002"
    ok_001 = all((grego_ok, sus_rotulo_ok, unicos, not invalidos, not referencias, not inexistentes, not duplicadas, not ent_mal, not ent_sobra,
                  not res_mal, not res_sobra, papeis_ok, not convencao, not sus_mal, ordem_ok, deterministica, csv_igual,
                  csv_lf, csv_cab, ida_volta, cob_ok, cob_erro, ref_ok, regex_ok))
    check("TC-WB40-001: tabela de nomes da V3.0 (tag) com nomes únicos, válidos e sem cara de referência; células "
          "existentes; cada entrada uma vez como ent/org/fte e cada fórmula das abas 05..14 como res; CSV em dia (UTF-8, "
          "LF); verificar_cobertura lista as células sem nome",
          ok_001,
          f"{len(tabela)} nomes {cont}; únicos={unicos} inválidos={invalidos[:3]} ref={referencias[:3]} "
          f"inexistentes={inexistentes[:3]} dup={duplicadas[:3]} ent={ent_mal[:3]}/{ent_sobra[:3]} "
          f"res={res_mal[:3]}/{res_sobra[:3]} papéis={papeis_ok} conv={convencao[:3]} sus={sus_mal[:3]} "
          f"ordem={ordem_ok} det={deterministica} csv={csv_igual}/{csv_lf}/{csv_cab} ida_volta={ida_volta} "
          f"cobertura={cob_ok}/{cob_erro} ref={ref_ok} regex={regex_ok} grego={grego_ok} sus_rótulo={sus_rotulo_ok} | fórmulas={len(formulas)} entradas={len(entradas)}")

    # ---------------- TC-WB40-002 ----------------
    # Gerador: nomes exatos da tabela (escopo do workbook), mesmas fórmulas e valores da V3.0 fora de alteracoes_v4_0(),
    # registro com o "antes" lido da origem; recusa de saída em excel/ ou igual à origem, sem abrir nem criar arquivo.
    v40 = Path(tmp) / "V4_0.xlsx"
    registro = gv.gerar(v30, v40, tabela)
    alts = gv.alteracoes_v4_0()
    alteradas = {(a["aba"], a["cel"]) for a in alts}
    esperados = {n.nome: f"'{n.aba}'!${re.sub(r'[0-9]', '', n.celula)}${re.sub(r'[A-Z]', '', n.celula)}" for n in tabela}
    wb4 = openpyxl.load_workbook(v40)
    try:
        nomes4 = {k: d.attr_text for k, d in wb4.defined_names.items()}
        locais = [(ws.title, k) for ws in wb4.worksheets for k in ws.defined_names]
        a3 = wb4["00_README"]["A3"].value
        calc = wb4.calculation.fullCalcOnLoad
        novos = {(a["aba"], a["cel"]): wb4[a["aba"]][a["cel"]].value for a in alts}
    finally:
        wb4.close()
    wb3 = openpyxl.load_workbook(v30)
    try:
        nomes3 = {k: d.attr_text for k, d in wb3.defined_names.items()}
        antes3 = {(a["aba"], a["cel"]): wb3[a["aba"]][a["cel"]].value for a in alts}
    finally:
        wb3.close()
    nomes_ok = nomes4 == {**nomes3, **esperados} and "Origens" in nomes3 and not locais
    ok_cmp, rel_cmp = cp.comparar_v40(v40, v30, alteradas, nomes=esperados)
    ok_neg, _ = cp.comparar_v40(v40, v30, set(), nomes=esperados)   # sem as alteradas, a A3 tem de aparecer como diferença
    a3_ok = a3 == gv.TEXTO_A3 and ("00_README", "A3") in alteradas
    novos_ok = all(novos[k] == a["novo"] for a in alts for k in [(a["aba"], a["cel"])]) and \
        {k[0] for k in alteradas} == {"00_README", "15_CHANGELOG"} and len(alteradas) == 4
    reg_cel = [r for r in registro if r["aba"] != "(workbook)"]
    reg_ok = [(r["aba"], r["cel"], r["antes"], r["novo"]) for r in reg_cel] == \
        [(a["aba"], a["cel"], antes3[(a["aba"], a["cel"])], a["novo"]) for a in alts] and \
        all(antes3[k] is None for k in alteradas if k[0] == "15_CHANGELOG") and all(r["ref"] for r in registro)
    # Recusas antes de abrir: origem inexistente com saída em excel/ dá SystemExit (não FileNotFoundError).
    fantasma = Path(tmp) / "nao_existe.xlsx"
    saida_excel = RAIZ / "excel" / "_teste_recusa_V4_0.xlsx"
    rec_excel = raises(lambda: gv.gerar(fantasma, saida_excel, tabela), SystemExit) and not saida_excel.exists()
    rec_viva = raises(lambda: gv.gerar(fantasma, RAIZ / CAMINHO_V30, tabela), SystemExit)
    bytes_v30 = v30.read_bytes()
    rec_origem = raises(lambda: gv.gerar(v30, v30, tabela), SystemExit) and v30.read_bytes() == bytes_v30
    ok_002 = all((nomes_ok, ok_cmp, not ok_neg, a3_ok, novos_ok, reg_ok, calc, rec_excel, rec_viva, rec_origem))
    check("TC-WB40-002: V4.0 gerada da tag com exatamente os nomes da tabela (escopo do workbook, Origens mantido); "
          "mesmas abas e 387 fórmulas idênticas; valores iguais fora de alteracoes_v4_0(); registro com o antes da "
          "origem; recusa saída em excel/ e saída = origem sem abrir nem criar arquivo",
          ok_002,
          f"nomes={nomes_ok} ({len(nomes4)} = {len(nomes3)} + {len(esperados)}; locais={locais[:3]}) comparar_v40={ok_cmp} "
          f"negativo={not ok_neg} A3={a3_ok} novos={novos_ok} registro={reg_ok} fullCalcOnLoad={calc} "
          f"recusas={rec_excel}/{rec_viva}/{rec_origem}" + ("" if ok_cmp else " | " + " ; ".join(rel_cmp[-6:])))

    # ---------------- TC-WB40-003 ----------------
    # CA-07 da V4.0: a regeneração (da tag, com o CSV commitado) é igual à excel/…V4_0.xlsx, inclusive os nomes definidos.
    entregue = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_0.xlsx"
    regen = Path(tmp) / "V4_0_regen.xlsx"
    gv.gerar(v30, regen, nv.ler_tabela(CSV_NOMES))
    if entregue.exists():
        ok_ca07, rel_ca07 = cp.comparar_xlsx(regen, entregue, cp.FORMULAS_ESPERADAS_V40, estrutura=True)
    else:
        ok_ca07, rel_ca07 = False, [f"não existe: {entregue}"]
    check("TC-WB40-003: CA-07 da V4.0: regeneração a partir da tag v3.0 igual à excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx "
          "(células, 387 fórmulas, nomes definidos, validações, formatação condicional, colunas ocultas)",
          ok_ca07, " ; ".join(r for r in rel_ca07 if not r.startswith("  DIF"))[:400] +
          ("" if ok_ca07 else " | " + " ; ".join(rel_ca07[:8])))


# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
