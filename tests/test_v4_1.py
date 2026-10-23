"""
Testes sem motor de recálculo da V4.1 (incremento 4, equilíbrio na planilha): estrutura do arquivo gerado e CA-07.
Uso: uv run python -X utf8 tests/test_v4_1.py
Namespace TC-WB41-xxx (IDs autorizados pelo usuário: 001 a 006; este script tem o 001 e o 002; os outros estão em
tests/test_workbook_v4_1.py). A V4.0 de partida é o arquivo da tag v4.0, extraído para uma pasta temporária; nada é
gravado em excel/.

TC-WB41-001 (estrutura da V4.1 gerada da tag v4.0 por gerar_v4_1.gerar):
- abas: as da V4.0, na mesma ordem, e depois 16, 17, 18, 19, 20, 20a…20d, 21 e 22;
- células da V4.0: as 387 fórmulas e todos os valores iguais, fora das células de alteracoes_v4_1(); o conjunto dessas
  células é exatamente o aprovado (item 6 do plano), montado aqui de forma independente: 6a = status B26:F26, toda
  fórmula da 10_TIRE com a guarda X$26<>"OK" (215 fórmulas ao todo), a nota I26 e os textos que a 6a deixaria falsos
  (00_README A37 e A53, rótulo 10_TIRE A31; ruling do controlador); 6b = 13_VALIDATION A25, 00_README A8,
  14_DASHBOARD A19; 6c = 00_README A3 e 15_CHANGELOG A21:C21. Cada alteração tem antes = V4.0 e novo = V4.1; desfazer a
  regra do EDR-056 (guarda LEFT e entradas limitadas MIN(MAX(…))) devolve o texto da V4.0, e os textos da 6a e da 6b
  mudam só o trecho aprovado. Célula nova numa aba antiga só no bloco do 14_DASHBOARD (linha 40 em diante) e no 15_CHANGELOG;
- células novas: toda fórmula das abas novas e do bloco do 14 está no registro de aba_equilibrio.montar com o mesmo
  texto e uma família do catálogo (F1-F19, REF), na aba que o catálogo e os rulings do controlador aceitam;
- nomes: os 698 da V4.0 (e Origens) iguais; os novos = data/nomes_V4_1.csv = aba_equilibrio.NOMES_V41 (CSV UTF-8, LF),
  válidos no Excel, únicos e sem cara de referência; destino '<aba>'!$C$L;
- todo resultado novo com nome (escopo do ruling da Task 2: toda linha com fórmula da 16, resumos de 17/18, tabelas da
  19 e da 20, custo da 20 e dashboard) e com a pior origem viva ao lado (fórmula sobre Origens): na 16, toda linha de
  resultado a partir da primeira saturação (as verificações e o caso efetivo são passos intermediários; o sentido da
  curva é eco da entrada); resumos de 17/18 e custo da 20 (coluna E); tabela da 19 (M) e da 20 (W); dashboard (E);
- entradas novas: Origem (lista Origens, validação de dados) e Fonte preenchidas, validação na célula do valor, nomes
  ent/org/fte e as três células em celulas_de_entrada_v41().
TC-WB41-002: CA-07 da V4.1: a regeneração a partir da tag é igual à excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx (células,
fórmulas, nomes definidos, validações, formatação condicional, colunas ocultas); o gerador recusa saída em excel/ (e a
viva) e saída = origem antes de abrir qualquer arquivo, sem criar nem mudar arquivo.
"Passou" = estrutura e regeneração conferidas; não é validação física.
"""
import re
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.worksheet.formula import ArrayFormula

import aba_equilibrio as ae
import gerar_v4_1 as g41
import nomes_v4_0 as nv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import comparar_planilhas as cp  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CSV41 = RAIZ / "data" / "nomes_V4_1.csv"
VIVA = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V3_0.xlsx"
results = []

# Famílias aceitas por aba: a coluna "Aba, faixa" do catálogo do plano e os rulings do controlador (Tasks 3, 5 e 6).
# 16: F1-F3, F12, F16, F17 do catálogo, mais as constantes de linha das grades calculadas uma vez na 16 (F4: braço de
# rolagem, denominador e ΔFz do CG lateral; F7: Cy e F'z0; F8: amplitude da grade de α; F9: tan δ_ref) e o K da 1ª linha
# da 19 trazido para a 16 (F14, F15), como diz o docstring de aba_equilibrio (achado desta tarefa, relatado).
GRADE = {"F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11"}
PERMITIDAS = {
    ae.ABA16: {"F1", "F2", "F3", "F12", "F16", "F17", "F4", "F7", "F8", "F9", "F14", "F15"},
    ae.ABA17: GRADE | {"F17"}, ae.ABA18: GRADE | {"F17"},
    ae.ABA19: GRADE | {"F13", "F14", "F15", "F17"},
    ae.ABA20: {"F1", "F4", "F12", "F16", "F17", "F18"} | {f"F{i}" for i in range(4, 17)},
    **{a: {"F1"} | {f"F{i}" for i in range(4, 17)} for a in ae.AUX20.values()},
    ae.ABA21: {"REF"}, ae.ABA22: {"REF"}, "14_DASHBOARD": {"F19"},
}


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


def celulas(wb, abas):
    return {(ws.title, c.coordinate): c.value for ws in wb.worksheets if ws.title in abas
            for lin in ws.iter_rows() for c in lin if c.value is not None}


def linha(cel: str) -> int:
    return int(re.sub(r"[A-Z]", "", cel))


def desfazer_6a(novo: str, col: str) -> str:
    """Inverso de gerar_v4_1.formula_tire_limitada, escrito à parte: guarda LEFT → guarda exata; MIN(MAX(…)) → ref."""
    s = novo.replace(f'LEFT({col}$26,2)<>"OK"', f'{col}$26<>"OK"')
    for lin, lo, hi in ((22, 87, 88), (38, 89, 90), (39, 91, 92), (25, 93, 94)):
        s = s.replace(f"MIN(MAX({col}${lin},$B${lo}),$B${hi})", f"{col}${lin}")
    return s


with tempfile.TemporaryDirectory(prefix="dds_v41_") as tmp:
    tmp = Path(tmp)
    v40 = ae.extrair_v40(tmp)
    v41 = tmp / "V4_1.xlsx"
    registro = g41.gerar(v40, v41)
    alts = g41.alteracoes_v4_1(v40)
    wbm = openpyxl.load_workbook(v40)          # montagem independente, só para ter o registro das fórmulas novas
    _, novas = g41.montar_v41(wbm, alts)
    wbm.close()
    wb40, wb41 = openpyxl.load_workbook(v40), openpyxl.load_workbook(v41)

    # ---------------- TC-WB41-001 ----------------
    abas40 = list(wb40.sheetnames)
    abas_ok = wb41.sheetnames == abas40 + list(g41.ABAS_NOVAS) and list(g41.ABAS_NOVAS) == \
        ["16_EQUILIBRIO", "17_EQ_PAR", "18_EQ_PAR_FINA", "19_EQ_LINEAR", "20_EQ_TROCA", "20a_TROCA", "20b_TROCA",
         "20c_TROCA", "20d_TROCA", "21_COBERTURA", "22_CADEIA"]
    c40, c41 = celulas(wb40, abas40), celulas(wb41, abas40)
    f40 = {k for k, v in c40.items() if formula(v)}
    t10 = wb40["10_TIRE"]
    esperado_alt = {("10_TIRE", f"{c}26") for c in "BCDEF"}
    esperado_alt |= {("10_TIRE", f"{c}{r}") for c in "BCDEF" for r in range(27, t10.max_row + 1)
                     if formula(t10[f"{c}{r}"].value) and f'{c}$26<>"OK"' in t10[f"{c}{r}"].value}
    n_tire = len(esperado_alt)
    esperado_alt |= {("10_TIRE", "I26"), ("00_README", "A37"), ("00_README", "A53"), ("10_TIRE", "A31"),
                     ("13_VALIDATION", "A25"), ("00_README", "A8"), ("14_DASHBOARD", "A19"),
                     *(("13_VALIDATION", c) for c in ("B40", "B41", "B42", "B43", "C43")),
                     ("00_README", "A3"), ("15_CHANGELOG", "A21"), ("15_CHANGELOG", "B21"), ("15_CHANGELOG", "C21")}
    alt_set = {(a["aba"], a["cel"]) for a in alts}
    conj_ok = alt_set == esperado_alt and len(alts) == len(alt_set) and n_tire == 215 and len(f40) == 387
    antes_novo = [f"{a['aba']}!{a['cel']}" for a in alts
                  if c40.get((a["aba"], a["cel"])) != a["antes"] or c41.get((a["aba"], a["cel"])) != a["novo"]]
    reg_ok = [(r["aba"], r["cel"], r["antes"], r["novo"]) for r in registro if r["ref"] != g41.REF_NOVAS] == \
        [(a["aba"], a["cel"], a["antes"], a["novo"]) for a in alts] and all(a["ref"] for a in alts)
    iguais_fora = [k for k in c40 if k not in alt_set and (c41.get(k) != c40[k] or type(c41.get(k)) is not type(c40[k]))]
    sobra = [k for k in c41 if k not in c40 and k not in alt_set
             and not (k[0] == "14_DASHBOARD" and linha(k[1]) >= ae.LINHA14_SECAO)]
    f_iguais = sum(1 for k in f40 if k not in alt_set and c41.get(k) == c40[k])
    inverso = []
    for a in alts:
        col = a["cel"][0]
        if a["aba"] == "10_TIRE" and a["cel"] not in ("I26", "A31") and linha(a["cel"]) > 26:
            if desfazer_6a(a["novo"], col) != a["antes"] or a["novo"] == a["antes"]:
                inverso.append(a["cel"])
        elif a["aba"] == "10_TIRE" and linha(a["cel"]) == 26 and a["cel"] != "I26":
            if not all(t in a["novo"] for t in ('"N/A - entrada ausente"', '"N/A - dataset inválido"',
                                                '"N/A - Fz<=0 (liftoff)"', '"OK"',
                                                "OK - limitado à faixa do .tir (EDR-056): ")):
                inverso.append(a["cel"])
    textos_ok = all(a["novo"].replace(novo, trecho) == a["antes"] and novo in a["novo"]
                    for aba, cel, trecho, novo in g41.TEXTOS_6A + g41.TEXTOS_6B for a in alts if (a["aba"], a["cel"]) == (aba, cel))
    antigas_ok = conj_ok and not antes_novo and reg_ok and not iguais_fora and not sobra and f_iguais == 387 - n_tire - 4 \
        and not inverso and textos_ok
    # Células novas: fórmula ⇔ registro de montar, mesmo texto, família do catálogo e da aba.
    reg_novas = {(r["aba"], r["cel"]): r for r in novas}
    novas41 = {(ws.title, c.coordinate): formula(c.value) for ws in wb41.worksheets
               if ws.title in g41.ABAS_NOVAS or ws.title == "14_DASHBOARD"
               for lin in ws.iter_rows() for c in lin if formula(c.value)
               and not (ws.title == "14_DASHBOARD" and linha(c.coordinate) < ae.LINHA14_SECAO)}
    fora_reg = [k for k in novas41 if k not in reg_novas]
    sem_celula = [k for k in reg_novas if k not in novas41]
    texto_dif = [k for k in novas41 if k in reg_novas and reg_novas[k]["formula"] != novas41[k]]
    fam_mal = sorted({(r["aba"], r["familia"]) for r in novas
                      if r["familia"] not in g41.FAMILIAS or r["familia"] not in PERMITIDAS.get(r["aba"], set())})
    novas_ok = len(novas41) == 117181 and not fora_reg and not sem_celula and not texto_dif and not fam_mal
    # Nomes.
    n40 = {k: d.attr_text for k, d in wb40.defined_names.items()}
    n41 = {k: d.attr_text for k, d in wb41.defined_names.items()}
    tab = nv.ler_tabela(CSV41)
    esperados = {n.nome: f"'{n.aba}'!${re.sub(r'[0-9]', '', n.celula)}${re.sub(r'[A-Z]', '', n.celula)}" for n in tab}
    nomes_novos = [n.nome for n in tab]
    bytes_csv = CSV41.read_bytes()
    nomes_ok = tab == list(ae.NOMES_V41) and len(n40) == 699 and "Origens" in n40 and n41 == {**n40, **esperados} \
        and len(set(nomes_novos)) == len(nomes_novos) and not set(nomes_novos) & set(n40) \
        and all(nv.NOME_VALIDO.fullmatch(x) and not nv.parece_referencia(x) for x in nomes_novos) \
        and b"\r" not in bytes_csv and bytes_csv.split(b"\n", 1)[0] == b"nome,aba,celula,papel,sus_id,rotulo" \
        and not [(ws.title, k) for ws in wb41.worksheets for k in ws.defined_names]
    # Resultados com nome e pior origem.
    por_cel = {(n.aba, n.celula): n for n in tab}
    ws16 = wb41[ae.ABA16]
    sem_nome, sem_pior = [], []
    for r in range(1, ws16.max_row + 1):
        if formula(ws16[f"B{r}"].value) and r not in ae.LINHA_ENTRADA.values():
            if por_cel.get((ae.ABA16, f"B{r}"), nv.Nome("", "", "", "", "", "")).papel != "res":
                sem_nome.append(f"16!B{r}")
    res16 = [ln for ln in ae._LAYOUT16 if ln.tipo == "res"]
    i0 = next(i for i, ln in enumerate(res16) if ln.chave == "S_F")
    for ln in res16[i0:]:
        e = formula(ws16[f"E{ae.LINHAS16[ln.chave]}"].value)
        if ln.chave != "txt_sent" and not (ln.pior and e and "Origens" in e):
            sem_pior.append(f"16!{ln.chave}")
    for aba in (ae.ABA17, ae.ABA18):
        for k, (nome, cel) in ae._nomes_resumo(aba).items():
            e = formula(wb41[aba][f"E{linha(cel)}"].value)
            if por_cel.get((aba, cel)) is None:
                sem_nome.append(f"{aba}!{cel}")
            if not (e and "Origens" in e):
                sem_pior.append(f"{aba}!E{linha(cel)}")
    for (q, k), nome in ae.NOME19.items():
        r = ae.LINHA_TAB19 + k
        if por_cel.get((ae.ABA19, f"{ae.COL19[q]}{r}")) is None:
            sem_nome.append(f"19!{q}{k}")
        if "Origens" not in (formula(wb41[ae.ABA19][f"M{r}"].value) or ""):
            sem_pior.append(f"19!M{r}")
    for (q, j), nome in ae.NOME20.items():
        cel = ae.celula20(q, j)
        if por_cel.get((ae.ABA20, cel)) is None:
            sem_nome.append(f"20!{cel}")
        if "Origens" not in (formula(wb41[ae.ABA20][f"W{linha(cel)}"].value) or ""):
            sem_pior.append(f"20!W{linha(cel)}")
    for q, nome in ae.NOME20_CUSTO.items():
        if "Origens" not in (formula(wb41[ae.ABA20][f"E{ae.LINHA20[q]}"].value) or ""):
            sem_pior.append(f"20!E{ae.LINHA20[q]}")
    for k in ("txt_k", "txt_ver", "apoio"):
        if k not in ae.NOME14 or k + "_pior" not in ae.NOME14:
            sem_nome.append(f"14!{k}")
    res_ok = not sem_nome and not sem_pior
    # Entradas novas.
    dvs = ws16.data_validations.dataValidation
    entra = ae.celulas_de_entrada_v41()
    ent_mal = []
    for e in ae.ENTRADAS16:
        r = ae.LINHA_ENTRADA[e.chave]
        dv_org = any(f"E{r}" in str(v.sqref).split() and "Origens" in (v.formula1 or "") for v in dvs)
        dv_val = any(f"B{r}" in str(v.sqref).split() for v in dvs)
        nomes_e = [por_cel.get((ae.ABA16, f"{c}{r}")) for c in "BEF"]
        if not (ws16[f"E{r}"].value in ae.ORIGENS_LISTA and ws16[f"F{r}"].value and dv_org and dv_val
                and [n.papel if n else None for n in nomes_e] == ["ent", "org", "fte"]
                and all((ae.ABA16, f"{c}{r}") in entra for c in "BEF")):
            ent_mal.append(e.chave)
    ok_001 = abas_ok and antigas_ok and novas_ok and nomes_ok and res_ok and not ent_mal
    check("TC-WB41-001: estrutura da V4.1 gerada da tag v4.0: abas e ordem; 387 fórmulas e valores da V4.0 iguais fora "
          "do item 6 (conjunto aprovado, antes/novo, 215 da 10_TIRE pela regra do EDR-056); toda fórmula nova numa família "
          "do catálogo e da aba; 698 nomes antigos iguais e os novos = data/nomes_V4_1.csv, válidos e únicos; resultados "
          "novos com nome e pior origem; entradas novas com Origem, Fonte, validação e em celulas_de_entrada_v41()",
          ok_001,
          f"abas={abas_ok} alteradas={len(alt_set)} (10_TIRE fórmulas {n_tire}) conjunto={conj_ok} "
          f"antes/novo={antes_novo[:3]} registro={reg_ok} fora_iguais={iguais_fora[:3]} sobra={sobra[:3]} "
          f"fórmulas_iguais={f_iguais} inverso={inverso[:3]} textos={textos_ok} | novas={len(novas41)} "
          f"fora_do_registro={fora_reg[:3]} sem_célula={sem_celula[:3]} texto={texto_dif[:3]} famílias={fam_mal[:5]} "
          f"| nomes={nomes_ok} ({len(n40)} + {len(nomes_novos)} = {len(n41)}) | sem_nome={sem_nome[:5]} "
          f"sem_pior={sem_pior[:5]} | entradas={ent_mal}")
    wb40.close()
    wb41.close()

    # ---------------- TC-WB41-002 ----------------
    entregue = cp.ENTREGUE_XLSX_V41
    regen = tmp / "V4_1_regen.xlsx"
    g41.gerar(v40, regen)
    if entregue.exists():
        ok_ca07, rel_ca07 = cp.comparar_xlsx(regen, entregue, cp.FORMULAS_ESPERADAS_V41, estrutura=True)
    else:
        ok_ca07, rel_ca07 = False, [f"não existe: {entregue}"]
    fantasma = tmp / "nao_existe.xlsx"
    saida_excel = RAIZ / "excel" / "_teste_recusa_V4_1.xlsx"
    rec_excel = raises(lambda: g41.gerar(fantasma, saida_excel), SystemExit) and not saida_excel.exists()
    viva_antes = VIVA.stat().st_mtime_ns if VIVA.exists() else None
    rec_viva = raises(lambda: g41.gerar(fantasma, VIVA), SystemExit) and \
        (VIVA.stat().st_mtime_ns if VIVA.exists() else None) == viva_antes
    b40 = v40.read_bytes()
    rec_origem = raises(lambda: g41.gerar(v40, v40), SystemExit) and v40.read_bytes() == b40
    check("TC-WB41-002: CA-07 da V4.1: regeneração a partir da tag v4.0 igual à excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx "
          f"(células, {cp.FORMULAS_ESPERADAS_V41} fórmulas, nomes definidos, validações, formatação condicional, colunas "
          "ocultas); recusa saída em excel/ (e a viva) e saída = origem sem abrir nem criar arquivo",
          ok_ca07 and rec_excel and rec_viva and rec_origem,
          f"recusas={rec_excel}/{rec_viva}/{rec_origem} | "
          + " ; ".join(r for r in rel_ca07 if not r.startswith("  DIF"))[:400]
          + ("" if ok_ca07 else " | " + " ; ".join(rel_ca07[:8])))

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
