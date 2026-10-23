"""
Testes sem motor de recálculo da V4.2 (incremento 5, metas e coerência; projeto T11): estrutura do arquivo gerado e CA-07.
Uso: uv run python -X utf8 tests/test_v4_2.py
Namespace TC-WB42-xxx (IDs autorizados: 001 a 006; este script tem o 001 e o 002 nesta etapa, o 003 e o 004 entram nas
Tasks seguintes; o 005 e o 006 estão em tests/test_workbook_v4_2.py). A V4.1 de partida é o arquivo da tag v4.1,
extraído para uma pasta temporária; nada é gravado em excel/.

TC-WB42-001 (estrutura da V4.2 gerada da tag v4.1 por gerar_v4_2.gerar; parte da Task 2, sem as metas):
- abas e ordem iguais às da V4.1 (a 23_LISTAS entra com as metas, Task 3);
- as 117569 fórmulas da V4.1 com texto idêntico fora da 16_EQUILIBRIO B188 e B189, e nelas só o literal
  "● Dado do TX" -> "● Dado do T11" (mesma contagem de fórmulas);
- o conjunto de células alteradas é exatamente o aprovado (autorização 5 (a), (b), (d) e (e)), montado aqui de forma
  independente: 32 células de Origem (colunas E e H de 05_VEHICLE e 06_SUSPENSION) com `◐ Dado de outro carro (TX, T09)`,
  a lista Origens (00_README A43:B44 e E43:E44), os textos de regra (00_README A49, 14_DASHBOARD A40, 16_EQUILIBRIO A2,
  20_EQ_TROCA A2, 22_CADEIA A2), as duas fórmulas do D16, a h7, a versão e a linha 22 do changelog; todas as outras
  células (valor e tipo) iguais;
- nenhuma ocorrência de "Dado do TX" nem "Dado do T09" em valor, fórmula, validação ou formatação condicional fora do
  04_DECISION_REGISTER e do 15_CHANGELOG (o `OUTRO_CARRO` só tem "TX, T09", sem "Dado do");
- 00_README A43:A48 == ORIGENS_V42 (seis posições, só as duas primeiras mudam), significado e categoria de
  SIGNIFICADO_V42; a lista `Origens` continua em '00_README'!$A$43:$A$48; os nomes definidos, as validações, a
  formatação condicional e as colunas ocultas ficam iguais aos da V4.1;
- 21_COBERTURA: a emenda da h7 (spec §7.4 linha 7) na coluna "Planilha" (D12); a F12 ("Chave agora") continua a fórmula;
- 00_README A3 com "V4.2" e linha 22 do 15_CHANGELOG no formato da 21.
TC-WB42-002: CA-07 da V4.2: duas regenerações (uma da tag, outra do arquivo extraído) iguais, com estrutura; igual a
excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx se ele existir (ele só vai a excel/ na Task 7); o gerador recusa saída em excel/
(e a viva) e saída = origem antes de abrir qualquer arquivo, sem criar nem mudar arquivo; data/nomes_V4_2.csv só com o cabeçalho.
"Passou" = estrutura e regeneração conferidas; não é validação física.
"""
import re
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.worksheet.formula import ArrayFormula

import gerar_v4_2 as g42
import origens

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import comparar_planilhas as cp  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CSV42 = RAIZ / "data" / "nomes_V4_2.csv"
VIVA = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V3_0.xlsx"
results = []

# Células de Origem com rótulo antigo na V4.1 (varredura de 2026-10-23): 05_VEHICLE e 06_SUSPENSION, colunas E e H.
LINHAS_05 = (5, 6, 7, 8, 30, 32, 33, 34)
LINHAS_06 = (4, 5, 6, 7, 10, 11, 14, 15)
DADO = {("05_VEHICLE", f"{c}{r}") for c in "EH" for r in LINHAS_05} | \
       {("06_SUSPENSION", f"{c}{r}") for c in "EH" for r in LINHAS_06}
LISTA = {("00_README", c) for c in ("A43", "B43", "E43", "A44", "B44", "E44")}
REGRA = {("00_README", "A49"), ("14_DASHBOARD", "A40"), ("16_EQUILIBRIO", "A2"), ("20_EQ_TROCA", "A2"),
         ("22_CADEIA", "A2")}
D16 = {("16_EQUILIBRIO", "B188"), ("16_EQUILIBRIO", "B189")}
OUTRAS = {("21_COBERTURA", "D12"), ("00_README", "A3"), ("15_CHANGELOG", "A22"), ("15_CHANGELOG", "B22"),
          ("15_CHANGELOG", "C22")}
ESPERADO_ALT = DADO | LISTA | REGRA | D16 | OUTRAS


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def raises(fn, exc=Exception):
    try:
        fn()
        return False
    except exc:
        return True


def formula(v):
    if isinstance(v, ArrayFormula):
        return f"{{{v.ref}}}{v.text}"
    return v if isinstance(v, str) and v.startswith("=") else None


def celulas(wb):
    return {(ws.title, c.coordinate): c.value for ws in wb.worksheets
            for lin in ws.iter_rows() for c in lin if c.value is not None}


def varrer_antigos(wb):
    """Onde sobra "Dado do TX" ou "Dado do T09" (valor, fórmula, validação, formatação condicional), fora do 04 e do 15."""
    achados = []
    for ws in wb.worksheets:
        if ws.title in ("04_DECISION_REGISTER", "15_CHANGELOG"):
            continue
        for lin in ws.iter_rows():
            for c in lin:
                t = c.value.text if isinstance(c.value, ArrayFormula) else c.value
                if isinstance(t, str) and ("Dado do TX" in t or "Dado do T09" in t):
                    achados.append(f"{ws.title}!{c.coordinate}")
        for dv in ws.data_validations.dataValidation:
            if any(x in (s or "") for s in (dv.formula1, dv.formula2) for x in ("Dado do TX", "Dado do T09")):
                achados.append(f"{ws.title}:DV")
        for _, regras in ws.conditional_formatting._cf_rules.items():
            if any(x in f for r in regras for f in (r.formula or []) for x in ("Dado do TX", "Dado do T09")):
                achados.append(f"{ws.title}:CF")
    return achados


with tempfile.TemporaryDirectory(prefix="dds_v42_") as tmp:
    tmp = Path(tmp)
    v41 = g42.extrair_v41(tmp)
    v42 = tmp / "V4_2.xlsx"
    g42.gerar(None, v42)                         # da tag v4.1, como o CLI sem --v41
    wb41, wb42 = openpyxl.load_workbook(v41), openpyxl.load_workbook(v42)

    # ---------------- TC-WB42-001 ----------------
    abas_ok = wb42.sheetnames == wb41.sheetnames and wb41.sheetnames[0] == "00_README" and wb41.sheetnames[-1] == "22_CADEIA"
    c41, c42 = celulas(wb41), celulas(wb42)
    f41 = {k: formula(v) for k, v in c41.items() if formula(v)}
    f42 = {k: formula(v) for k, v in c42.items() if formula(v)}
    n_form = len(f41) == 117569 == len(f42) and set(f41) == set(f42)
    form_difs = sorted(k for k in f41 if f42.get(k) != f41[k])
    lit_ok = form_difs == sorted(D16) and all(
        f42[k] == f41[k].replace('"● Dado do TX"', '"● Dado do T11"') and f41[k].count('"● Dado do TX"') == 1
        and '"● Dado do TX"' not in f42[k] for k in D16)
    mudou = {k for k in set(c41) | set(c42) if c41.get(k) != c42.get(k) or type(c41.get(k)) is not type(c42.get(k))}
    conj_ok = mudou == ESPERADO_ALT and len(ESPERADO_ALT) == 50
    # dado: o antigo era TX ou T09, o novo é "outro carro" (E e H iguais entre si)
    dado_ok = len(DADO) == 32 and all(c41[k] in (origens.TX_V41, origens.T09_V41) and c42[k] == origens.OUTRO_CARRO
                                      for k in DADO) and all(c42[(a, f"E{r}")] == c42[(a, f"H{r}")]
                                                              for a, r in [(a, int(re.sub(r"[A-Z]", "", c))) for a, c in DADO])
    # varredura independente: toda célula não-fórmula fora do 00_README com o rótulo exato antigo está em DADO
    com_rotulo = {k for k, v in c41.items() if v in (origens.TX_V41, origens.T09_V41) and k[0] != "00_README"}
    varredura_ok = com_rotulo == DADO
    sobra = varrer_antigos(wb42)
    sobra41 = varrer_antigos(wb41)          # a varredura enxerga o que existe na V4.1 (senão "limpo" não prova nada)
    sem_antigo = not sobra and len(sobra41) == 41
    # lista Origens
    r43 = [c42[("00_README", f"A{r}")] for r in range(43, 49)]
    lista_ok = tuple(r43) == origens.ORIGENS_V42 and len(set(r43)) == 6 and r43[2:] == list(origens.ORIGENS_V42[2:]) and all(
        c42[("00_README", f"B{43 + i}")] == origens.SIGNIFICADO_V42[rot][0]
        and c42[("00_README", f"E{43 + i}")] == origens.SIGNIFICADO_V42[rot][1] for i, rot in enumerate(origens.ORIGENS_V42[:2])) \
        and all(c42[("00_README", f"{c}{r}")] == c41[("00_README", f"{c}{r}")] for r in range(45, 49) for c in "ABE")
    n41 = {k: d.attr_text for k, d in wb41.defined_names.items()}
    n42 = {k: d.attr_text for k, d in wb42.defined_names.items()}
    nomes_ok = n41 == n42 and n42.get("Origens") == "'00_README'!$A$43:$A$48" and len(n42) == 1146
    est = cp._estrutura(v41) == cp._estrutura(v42)
    # h7
    h7 = c42[("21_COBERTURA", "D12")]
    h7_ok = h7.startswith("Sim (entrada, 0 até medir; um sentido por vez, pela entrada \"Sentido da curva\": o outro se vê trocando o sentido;") \
        and h7.endswith("EDR-060, 2026-10-22)") and c41[("21_COBERTURA", "D12")] == "Sim (entrada, 0 até medir)" \
        and c42[("21_COBERTURA", "F12")] == "=ent_16_chave_h7_cg_lateral"
    a3 = c42[("00_README", "A3")]
    a3_ok = a3.startswith("Versão do workbook: V4.2 (incremento 5: metas e coerência; projeto T11 (Origens e D16))") \
        and "V4.1" not in a3 and a3.endswith("| Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated") \
        and c41[("00_README", "A3")].replace("V4.1", "V4.2").endswith(a3[a3.index("| Status"):])
    ch = wb42["15_CHANGELOG"]
    ch_ok = ch["A22"].value == "2026-10" and ch["B22"].value.startswith("V4.2, ") and "EDR-062" in ch["C22"].value \
        and "docs/registro-de-versoes-V4_2-celulas.md" in ch["C22"].value and all(ch[f"{c}23"].value is None for c in "ABC") \
        and all(list(ch[f"{c}22"]._style) == list(ch[f"{c}21"]._style) for c in "ABC")
    # registro do gerador: antes = V4.1, novo = V4.2, mesmo conjunto
    reg = g42.alteracoes_v4_2(wb41)
    reg_set = {(a["aba"], a["cel"]) for a in reg}
    reg_ok = reg_set == ESPERADO_ALT and len(reg) == 50 and all(a["ref"] for a in reg) \
        and all(c41.get((a["aba"], a["cel"])) == a["antes"] and c42.get((a["aba"], a["cel"])) == a["novo"] for a in reg)
    ok_001 = abas_ok and n_form and lit_ok and conj_ok and dado_ok and varredura_ok and sem_antigo and lista_ok \
        and nomes_ok and est and h7_ok and a3_ok and ch_ok and reg_ok
    check("TC-WB42-001: estrutura da V4.2 (sem metas) gerada da tag v4.1: abas e ordem; 117569 fórmulas iguais fora da "
          "16_EQUILIBRIO B188/B189 (só o literal \"● Dado do T11\"); 50 células alteradas = o conjunto aprovado; 32 células de dado "
          "com \"outro carro\"; nenhum \"Dado do TX\"/\"Dado do T09\" fora do 04 e do 15; lista Origens A43:A48 = ORIGENS_V42 e nome "
          "inalterado; nomes, validações e formatação iguais; emenda da h7; A3 com V4.2; changelog linha 22",
          ok_001,
          f"abas={abas_ok} fórmulas={n_form} ({len(f41)}/{len(f42)}) literal={lit_ok} difs_fórmula={form_difs} "
          f"conjunto={conj_ok} (mudou {len(mudou)}; fora do esperado {sorted(mudou - ESPERADO_ALT)[:3]}, "
          f"faltou {sorted(ESPERADO_ALT - mudou)[:3]}) dado={dado_ok} varredura={varredura_ok} sobra={sobra[:3]} "
          f"(V4.1 tinha {len(sobra41)}) lista={lista_ok} nomes={nomes_ok} ({len(n42)}) estrutura={est} h7={h7_ok} A3={a3_ok} "
          f"changelog={ch_ok} registro={reg_ok}")
    wb41.close()
    wb42.close()

    # ---------------- TC-WB42-002 ----------------
    regen1, regen2 = tmp / "V4_2_regen1.xlsx", tmp / "V4_2_regen2.xlsx"
    g42.gerar(None, regen1)
    g42.gerar(v41, regen2, tmp / "registro.md")
    ok_dup, rel_dup = cp.comparar_xlsx(regen1, regen2, cp.FORMULAS_ESPERADAS_V42, estrutura=True)
    ok_dup2, _ = cp.comparar_xlsx(v42, regen1, cp.FORMULAS_ESPERADAS_V42, estrutura=True)
    entregue = cp.ENTREGUE_XLSX_V42
    if entregue.exists():
        ok_ent, rel_ent = cp.comparar_xlsx(regen1, entregue, cp.FORMULAS_ESPERADAS_V42, estrutura=True)
    else:
        ok_ent, rel_ent = True, [f"excel/…V4_2.xlsx ainda não existe (vai a excel/ na Task 7): comparação adiada"]
    reg_md = (tmp / "registro.md").read_text(encoding="utf-8")
    reg_md_ok = reg_md.startswith("# Registro de células da V4.2") and reg_md.count("\n| ") >= 50 and "\r" not in reg_md
    fantasma = tmp / "nao_existe.xlsx"
    saida_excel = RAIZ / "excel" / "_teste_recusa_V4_2.xlsx"
    rec_excel = raises(lambda: g42.gerar(fantasma, saida_excel), SystemExit) and not saida_excel.exists()
    viva_antes = VIVA.stat().st_mtime_ns if VIVA.exists() else None
    rec_viva = raises(lambda: g42.gerar(fantasma, VIVA), SystemExit) and \
        (VIVA.stat().st_mtime_ns if VIVA.exists() else None) == viva_antes
    b41 = v41.read_bytes()
    rec_origem = raises(lambda: g42.gerar(v41, v41), SystemExit) and v41.read_bytes() == b41
    cab = CSV42.read_bytes()
    csv_ok = cab == b"nome,aba,celula,papel,sus_id,rotulo\n"
    check("TC-WB42-002: CA-07 da V4.2: duas regenerações (da tag e do arquivo extraído) iguais, com estrutura "
          f"({cp.FORMULAS_ESPERADAS_V42} fórmulas); igual a excel/…V4_2.xlsx se existir; registro .md gravado; recusa saída em "
          "excel/ (e a viva) e saída = origem sem abrir nem criar arquivo; data/nomes_V4_2.csv só com o cabeçalho",
          ok_dup and ok_dup2 and ok_ent and reg_md_ok and rec_excel and rec_viva and rec_origem and csv_ok,
          f"regen={ok_dup}/{ok_dup2} entregue={ok_ent} registro={reg_md_ok} recusas={rec_excel}/{rec_viva}/{rec_origem} csv={csv_ok} | "
          + " ; ".join(r for r in rel_ent if not r.startswith("  DIF"))[:300]
          + ("" if ok_dup else " | " + " ; ".join(rel_dup[:6])))

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
