
"""Testes sem motor de recálculo da V4.3 (incremento 7, parte 7b: centro da curva, raio do skidpad e Fx por arrasto
induzido; projeto T11): estrutura do arquivo gerado e CA-07.
Uso: uv run python -X utf8 tests/test_v4_3.py
Namespace TC-WB43-xxx (IDs autorizados: 001 a 006; este script tem o 001, o 002 e o 006; o 003 a 005 (recálculo pelo
Excel e barra de fórmulas) ficam em tests/test_workbook_v4_3.py). A V4.2 de partida é o arquivo da tag v4.2, extraído para uma pasta
temporária; nada é gravado em excel/.

TC-WB43-001 (estrutura da V4.3 gerada da tag v4.2 por gerar_v4_3.gerar, um check):
- abas na ordem da V4.2, mais a `24_CURVA` no fim; fórmulas e valores da V4.2 iguais em todas as células fora do
  registro; o diff de texto V4.2 -> V4.3 é exatamente o registro de células do gerador (antes e depois de cada
  célula), e o número de fórmulas da V4.3 é o da V4.2 mais as novas;
- nomes definidos: os da V4.2 mais exatamente os de data/nomes_V4_3.csv (= `aba_curva.NOMES_V43`), cada um numa célula
  só e sem apelido (D4: um nome por célula nas células com nome); `ent_16_raio_do_skidpad_r` continua na 16_EQUILIBRIO
  B9, que agora é `=res_24_r_usado`, com o estilo das células de resultado e sem a validação numérica (C-B2), e a E9
  sem a lista de Origens;
- a 24_CURVA: as validações da C-A20 (modo, chaves "0,1", decimal > 0 e lista de Origens), as fórmulas só nas linhas
  do catálogo e as colunas novas das grades nos endereços de `colunas_v43` (17: a partir de FI; 18: GO; as pedidas das
  20a a 20d e a mini-grade da 19, sem as colunas x: ES; as finas das 20a a 20d: GO), com o cabeçalho na linha
  anterior;
- todo leitor de `{R}` (16_EQUILIBRIO B9, nome `ent_16_raio_do_skidpad_r`) está guardado por `raio`, `h2`, `h8`, `h9`,
  `ok` ou pelo próprio `ISNUMBER({R})`, e nenhum usa `ISBLANK({R})` (a lista de leitores sai da planilha gerada);
- nenhuma aba tem `ProtectContents` e nenhuma célula com fórmula tem `protection.hidden` (C-B1);
- 00_README A3 diz "V4.3" e a linha 23 do 15_CHANGELOG está no formato da 22; validações, formatação condicional e
  colunas ocultas das outras abas iguais às da V4.2.
TC-WB43-002 (CA-07): duas regenerações (uma da tag, outra do arquivo extraído) iguais, com estrutura, e iguais a
excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx se ele existir (a cópia vai a excel/ num commit próprio, Task 14); o gerador
recusa saída em excel/ e saída = origem antes de abrir qualquer arquivo; data/nomes_V4_3.csv = aba_curva.NOMES_V43 e o
gerador recusa um CSV diferente; o texto da 24_CURVA B34 é `=4/3` e `equilibrio.FATOR_NEUTRO == 4/3`.
TC-WB43-006 (migração V4.2 -> V4.3, sem motor; catálogo C-M1 a C-M4; tools/migrar_viva.py, em cópias de pasta temporária):
- C-M1: `dados_planilha._destinos` da V4.3 não tem `ent_16_raio_do_skidpad_r` nem `org_16_raio_do_skidpad_r` (B9 e E9 são
  fórmula); os da V4.2 continuam todos (nenhum nome de dado da V4.2 tem fórmula);
- viva V4.2 sintética (a da tag com dados de teste), migrada para a V4.3 gerada, com código 0 e 0 conflito (C-M2, C-M3):
  B9 = 8,3 vai ao R manual (24_CURVA B8) e põe o modo em "Manual", as entradas novas ficam no padrão e o resto da V4.3
  igual; B9 vazio deixa o modo em "Linha central" e B8 vazio; E9 trocado pela equipe vai a E8 e a E9 da V4.3 continua
  fórmula; F9 trocado vai a F8, sem conflito;
- C-M4: viva V4.3 com B9 ou E9 sobrescritos por número dá código 2 ("célula alterada fora dos nomes de dado") e não grava
  a saída; uma viva V4.3 só com dado na 24_CURVA migra com código 0.
"Passou" = estrutura e regeneração conferidas; não é validação física.
"""
import re
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

import aba_curva as ac
import aba_equilibrio as ae
import dados_planilha as dp
import equilibrio
import origens
import skidpad
import gerar_v4_3 as g43

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import comparar_planilhas as cp  # noqa: E402
import migrar_viva as migr_viva  # noqa: E402
from nomes_v4_0 import ler_tabela  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CSV43 = RAIZ / "data" / "nomes_V4_3.csv"
CATALOGO = RAIZ / "docs" / "superpowers" / "plans" / "2026-10-29-inc7-fisica-planilha.md"   # versionado
results = []

FORMULAS_V42 = 117627          # as da V4.2 (cp.FORMULAS_ESPERADAS_V42)
ABAS_AUX = tuple(ae.AUX20.values())


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


def norm(v):
    """Forma comparável de um valor de célula: o texto da fórmula, ou o valor com o tipo (None fica None)."""
    if v is None:
        return None
    f = formula(v)
    return ("F", f) if f is not None else ("V", v, type(v).__name__)


def sqref_celulas(sqref) -> set[str]:
    """Células de um `sqref` (as validações destas abas só listam células soltas, sem faixa)."""
    return set(str(sqref).split())


def estrutura_igual_menos(e42: dict, e43: dict, aba_diferente: str) -> bool:
    """Todas as abas da V4.2 com validação, formatação condicional e colunas ocultas iguais, salvo a `aba_diferente`."""
    return all(e42[a] == e43[a] for a in e42 if a not in ("nomes", aba_diferente))


def main() -> None:
    nomes_csv = ler_tabela(CSV43)
    with tempfile.TemporaryDirectory(prefix="dds_t43_") as tmp:
        tmp = Path(tmp)
        v42 = g43.extrair_v42(tmp)
        regen1, regen2 = tmp / "V4_3_regen1.xlsx", tmp / "V4_3_regen2.xlsx"
        reg, celulas_reg, novas24 = g43.gerar(None, regen1, tmp / "registro.md")

        # ---------------- TC-WB43-001 ----------------
        wb42 = openpyxl.load_workbook(v42)
        wb43 = openpyxl.load_workbook(regen1)
        c42, c43 = celulas(wb42), celulas(wb43)
        abas_ok = wb43.sheetnames == wb42.sheetnames + [ac.ABA24]
        # diff de texto: fora da 24_CURVA, só as células do registro mudam, com o antes e o depois do registro
        chaves = {k for k in set(c42) | set(c43) if k[0] != ac.ABA24}
        difs = {k for k in chaves if norm(c42.get(k)) != norm(c43.get(k))}
        so_reg = sorted(set(celulas_reg) - difs)
        so_dif = sorted(difs - set(celulas_reg))
        valores_ok = all(norm(c42.get(k)) == norm(a) and norm(c43.get(k)) == norm(n)
                         for k, (a, n) in celulas_reg.items())
        diff_ok = not so_reg and not so_dif and valores_ok and len(celulas_reg) > 0
        n_f42 = sum(1 for v in c42.values() if formula(v) is not None)
        n_f43 = sum(1 for v in c43.values() if formula(v) is not None)
        delta = sum((formula(n) is not None) - (formula(a) is not None)
                    for a, n in celulas_reg.values()) + len(novas24)
        n_form_ok = n_f42 == FORMULAS_V42 == cp.FORMULAS_ESPERADAS_V42 \
            and n_f43 == n_f42 + delta == cp.FORMULAS_ESPERADAS_V43
        f24 = {k[1]: v for k, v in c43.items() if k[0] == ac.ABA24 and formula(v) is not None}
        f24_ok = set(f24) == {f"B{lin}" for lin in ac.LINHA24_RES.values()} == {n["cel"] for n in novas24} \
            and all(f24[n["cel"]] == n["formula"] for n in novas24) and f24["B34"] == "=4/3"
        # nomes
        n42 = {n: d.attr_text for n, d in wb42.defined_names.items()}
        n43 = {n: d.attr_text for n, d in wb43.defined_names.items()}
        esperados_n = {n.nome: f"'{n.aba}'!${re.sub(r'[0-9]', '', n.celula)}${re.sub(r'[A-Z]', '', n.celula)}"
                       for n in nomes_csv}
        novos_n = {k: v for k, v in n43.items() if k not in n42}
        destinos = [v for k, v in n43.items() if ":" not in v]
        nomes_ok = {k: n43.get(k) for k in n42} == n42 and novos_n == esperados_n and nomes_csv == list(ac.NOMES_V43) \
            and len(destinos) == len(set(destinos)) and len(nomes_csv) == 41 \
            and n43["ent_16_raio_do_skidpad_r"] == "'16_EQUILIBRIO'!$B$9" \
            and ae.NOME_ENT["R"] == "ent_16_raio_do_skidpad_r"
        # B9: fórmula, estilo de resultado, sem validação numérica; E9 sem a lista de Origens (C-B2, C-B3)
        s16 = wb43["16_EQUILIBRIO"]
        r9 = ae.LINHA_ENTRADA["R"]
        dv_b9 = [dv for dv in s16.data_validations.dataValidation if f"B{r9}" in dv.sqref or f"E{r9}" in dv.sqref]
        b9_ok = s16[f"B{r9}"].value == "=res_24_r_usado" and r9 == 9 \
            and list(s16[f"B{r9}"]._style) == list(s16[f"B{ae.LINHAS16['ok']}"]._style) \
            and list(s16[f"B{r9}"]._style) != list(wb42["16_EQUILIBRIO"][f"B{r9}"]._style) \
            and not dv_b9 and s16[f"E{r9}"].value == "=res_24_pior_origem_do_r" \
            and s16[f"A{r9}"].value == ac.TEXTO_A9 and s16[f"F{r9}"].value == ac.TEXTO_F9 \
            and wb42["16_EQUILIBRIO"][f"B{r9}"].value is None
        # 24_CURVA: validações da C-A20 e entradas
        w24 = wb43[ac.ABA24]
        dv24 = sorted((" ".join(sorted(sqref_celulas(dv.sqref))), dv.type, dv.formula1)
                      for dv in w24.data_validations.dataValidation)
        dv24_ok = dv24 == sorted([("B4", "list", f'"{ac.LISTA_MODOS}"'), ("B10 B9", "list", '"0,1"'),
                                  ("B5 B6 B7 B8", "decimal", "0"),
                                  ("E10 E4 E5 E6 E7 E8 E9", "list", "=Origens")]) \
            and w24["B4"].value == "Linha central" and w24["B9"].value == 1 and w24["B10"].value == 1 \
            and w24["B8"].value is None \
            and [w24[f"B{r}"].value for r in (5, 6, 7)] == [15.25, 21.25, 0.0889] \
            and [w24[f"E{r}"].value for r in range(4, 11)] == [
                "? A confirmar", "● Dado do T11", "● Dado do T11", "◐ Provisório (.tir TTC)", "? A confirmar",
                "? A confirmar", "? A confirmar"] \
            and all(isinstance(w24[f"F{r}"].value, str) and w24[f"F{r}"].value for r in range(4, 11))
        # colunas novas das grades (endereços de colunas_v43)
        def letra(n_alfa, pedida, chave):
            return ae.colunas_v43(n_alfa, pedida)[chave]
        esperadas_col = {ae.ABA17: ("FI", 23, 24, 64, 25, True), ae.ABA18: ("GO", 23, 24, 104, 49, False),
                         ae.ABA19: ("ES", ae.LINHA_MINI19 - 1, ae.LINHA_MINI19, ae.LINHA_MINI19 + 2, 25, False)}
        for aux in ABAS_AUX:
            esperadas_col[(aux, "pedida")] = ("ES", 23, 24, 64, 25, False)
            esperadas_col[(aux, "fina")] = ("GO", 93, 94, 174, 49, False)
        col_ok = True
        for chave_, (c0, linha_cab, p0, p1, n_alfa, pedida) in esperadas_col.items():
            aba = chave_ if isinstance(chave_, str) else chave_[0]
            ws = wb43[aba]
            cn = ae.colunas_v43(n_alfa, pedida)
            antes_c0 = get_column_letter(column_index_from_string(c0) - 1)     # a última coluna da V4.2 da grade
            col_ok &= cn[("fy0", "R", 0)] == c0 and ws[f"{c0}{linha_cab}"].value == "fy0_R_0" \
                and [ws[f"{l}{linha_cab}"].value for l in list(cn.values())[-6:]] == [
                    "cap0_R", "idx0_R", "j_F", "j_R", "aF", "aR"] \
                and all(formula(ws[f"{l}{r}"].value) is not None for l in cn.values() for r in range(p0, p1 + 1)) \
                and all(ws[f"{l}{p1 + 1}"].value is None for l in cn.values()) \
                and ws[f"{antes_c0}{linha_cab}"].value is not None
        # leitores de {R}: guardados por raio, h8, h9 ou ok (C-B4 e C-B7, B65 e B173 da 16, têm o ISNUMBER({R}) como
        # guarda catalogada) e sem ISBLANK; o detector é exercitado em fórmulas mutadas
        nome_R = ae.NOME_ENT["R"]
        guardas = [ae.NOME_ENT["h8"], ae.NOME_ENT["h9"], ae.NOME16["raio"], ae.NOME16["ok"]]
        excecoes = {("16_EQUILIBRIO", f"B{ae.LINHAS16['tvolta']}"), ("16_EQUILIBRIO", "B65"),
                    ("24_CURVA", "B28")}   # B28 (C-A21): guardada por h2, h2v e ISNUMBER({R}); é a única só com h2

        def checar_leitores(formulas: dict):
            lei = [(k, f) for k, f in formulas.items() if nome_R in f and k != ("16_EQUILIBRIO", f"B{r9}")]
            sem = [k for k, f in lei if not any(g in f for g in guardas)
                   and not (k in excecoes and f"ISNUMBER({nome_R})" in f)]
            return lei, sem, [k for k, f in formulas.items() if f"ISBLANK({nome_R})" in f]

        f43 = {k: formula(v) for k, v in c43.items() if formula(v) is not None}
        leitores, sem_guarda, isblank = checar_leitores(f43)
        fora_grade = sorted({f"{a}!{c}" for (a, c), _ in leitores if a not in (ae.ABA17, ae.ABA18, ae.ABA19, *ABAS_AUX)
                             and not (a == "16_EQUILIBRIO" and c[0] in "IJKL")})
        x1 = ("X", "A1")
        mut = checar_leitores({x1: f"=IF(A1>0,{nome_R},0)", ("X", "A2"): f"=IF(ISBLANK({nome_R}),1,0)",
                               ("X", "A3"): f"=IF({ae.NOME16['ok']}=1,{nome_R},0)"})
        pega = mut[1] == [x1, ("X", "A2")] and mut[2] == [("X", "A2")]
        leitores_ok = len(leitores) > 100 and not sem_guarda and not isblank
        # texto literal do catálogo (catalogo-v43.md) em células-chave, com os {nomes} trocados pelos nomes reais
        plano = CATALOGO.read_text(encoding="utf-8")       # o catálogo é a seção "# Catálogo das células da V4.3"
        cat = " ".join(plano[plano.index("# Catálogo das células da V4.3"):].split())
        nm = {**ae.NOME_ENT, **ae.NOME16, **ac.NOME24, "b": ae.V40["b"], "L": ae.V40["L"], "tF": ae.V40["tF"],
              "tR": ae.V40["tR"], "m": ae.V40["m"]}
        motivos = {"MOTIVO_MODO_INVALIDO": skidpad.MOTIVO_MODO_INVALIDO,
                   "MOTIVO_SEM_MEIA_LARGURA": skidpad.MOTIVO_SEM_MEIA_LARGURA,
                   "MOTIVO_MANUAL_VAZIO": skidpad.MOTIVO_MANUAL_VAZIO, "MOTIVO_DIAMETROS": skidpad.MOTIVO_DIAMETROS,
                   "MOTIVO_BITOLA_TRASEIRA": skidpad.MOTIVO_BITOLA_TRASEIRA, "MOTIVO_VEICULO": skidpad.MOTIVO_VEICULO}

        def sub(t, extra=None):
            t = re.sub(r"\{(\w+)\}", lambda m_: (extra or {}).get(m_.group(1)) or nm[m_.group(1)], t)
            return re.sub(r"MOTIVO_[A-Z_]+", lambda m_: '"' + motivos[m_.group(0)] + '"', t)

        gvf = f"'16_EQUILIBRIO'!$G${ae.LINHAS16['vf' + str(len(ae.VERIFICACOES) - 1)]}"
        gvf_ant = f"'16_EQUILIBRIO'!$G${ae.LINHAS16['vf' + str(ae.I_DEN - 1)]}"
        s16_, s24_ = wb43["16_EQUILIBRIO"], wb43[ac.ABA24]
        lit = [
            ('=IF(OR({h2}=1,{h3}=1,{h8}=1,{h9}=1),IF(ISNUMBER({R}),"-",IF(ISERROR({R}),"raio do skidpad R com erro",'
             'IF({R}="","raio do skidpad R a confirmar ("&{motivo_r}&")","raio do skidpad R não é número"))),"-")',
             s16_["B65"], None),
            ("={rusado}", s16_["B9"], None),
            ('=IF({G_vfN}="-",IF({sit24}="-","OK",{sit24}),{G_vfN})', s16_["B78"], {"G_vfN": gvf}),
            ('=IF(AND(ISNUMBER({S_F}),ISNUMBER({S2_F})),IF(ISNUMBER({fator}),{fator}*ABS({S_F}-{S2_F}),"-"),'
             'IF(OR(ISNUMBER({S_F}),ISNUMBER({S2_F})),0.05*9.81,"-"))', s16_["B137"], None),
            ('=IF(ISNUMBER({aylim}),IF(ISNUMBER({R}),IF({R}>0,2*PI()*SQRT({R}/{aylim}),"N/A: raio do skidpad R deve '
             'ser > 0"),'
             'IF(ISERROR({R}),"N/A: raio do skidpad R com erro",IF({R}="","N/A: raio do skidpad R a confirmar ("&'
             '{motivo_r}&")","N/A: raio do skidpad R não é número"))),"N/A")', s16_["B173"], None),
            ('=IFERROR(IF(EXACT({modo},"Manual"),IF(ISNUMBER({rman}),{rman},""),IF(EXACT({modo},"Linha central"),{rlc},'
             'IF(EXACT({modo},"Rente aos cones"),{rrente},""))),"")', s24_["B20"], None),
            ('=IF(NOT(OR(EXACT({modo},"Linha central"),EXACT({modo},"Rente aos cones"),EXACT({modo},"Manual"))),'
             'MOTIVO_MODO_INVALIDO,IF(ISNUMBER({rusado}),IF(AND(EXACT({modo},"Rente aos cones"),NOT(ISNUMBER({w}))),'
             'MOTIVO_SEM_MEIA_LARGURA,"-"),IF(EXACT({modo},"Manual"),MOTIVO_MANUAL_VAZIO,IF(NOT(ISNUMBER({rin})),'
             'MOTIVO_DIAMETROS,IF(NOT(ISNUMBER({tR})),MOTIVO_BITOLA_TRASEIRA,MOTIVO_VEICULO)))))', s24_["B21"], None),
            ("=4/3", s24_["B34"], None),
        ]
        cat_ok = cat is not None
        cat_det = []
        for tpl, cel_, extra in lit:
            ok_c = cel_.value == sub(tpl, extra) and (cat is None or tpl in cat)
            cat_ok &= ok_c
            if not ok_c:
                cat_det.append(cel_.coordinate)
        # C-B11: status das linhas extras das 20a a 20d, texto literal do catálogo com os nomes de cada linha
        tpl11 = ('=IF({G_vf_den_ant}<>"-",{G_vf_den_ant},IF({vden}<>"-",{vden},IF({vf_ack}<>"-",{vf_ack},'
                 'IF({sit24}<>"-",{sit24},"OK"))))')
        m20_ = ae._Subst(ac.mapa_v43())
        m20_.update(ae.V40_20)
        for j_ in ae.EXTRAS20:
            ml_ = ae._mapa_linha(m20_, j_)
            exp11 = tpl11.format_map({"G_vf_den_ant": gvf_ant, "vf_ack": ml_[f"vf{ae.I_ACK}"],
                                      "vden": ml_["vden"], "sit24": ml_["sit24"]})
            cel11 = wb43[ae.ABA20][f"{ae.COL_BLOCO[j_]}{ae.LINHA_BLOCO['status']}"]
            ok_c = cel11.value == exp11 and (cat is None or tpl11 in cat)
            cat_ok &= ok_c
            if not ok_c:
                cat_det.append(f"20 status linha {j_}: {cel11.value[:80]} != {exp11[:80]}")
        # B114: o catálogo escreve o acréscimo `+IF({h2v}=1,{thFL}-{thm},0)` sobre o texto da V4.2
        da = f"B{ae.LINHAS16['da_FL']}"
        ack = "(-(" + nm["di"] + "-" + nm["dref"] + "))"
        antes_da = wb42["16_EQUILIBRIO"][da].value
        ok_c = s16_[da].value == antes_da.replace(ack, ack + sub("+IF({h2v}=1,{thFL}-{thm},0)")) \
            and (cat is None or "+IF({h2v}=1,{thFL}-{thm},0)" in cat)
        cat_ok &= ok_c
        if not ok_c:
            cat_det.append(da)
        # grade da 17, linha 30: aF, aR e fxr pelas fórmulas do catálogo (abreviações trocadas pelas células da linha)
        g17, cl17, cn17, r_ = wb43[ae.ABA17], ae._colunas(ae.N_ALFA, True), ae.colunas_v43(ae.N_ALFA, True), 30
        cel17 = lambda n: f"{cl17[n]}{r_}" if n in cl17 else f"{cn17[n]}{r_}"
        faixa = lambda n0, n1: f"{cel17(n0)}:{cel17(n1)}"
        alfa_ref = f"$B${ae.LINHA_ALFA + 1}:${get_column_letter(1 + ae.N_ALFA)}${ae.LINHA_ALFA + 1}"
        af = ('=IF(AND({h9}=1,{h9v}=1),IF(pre_F<>"-","semF",IF(req_F>=cap_F,ABS(INDEX(alfa,idx_F)),IF(j_F<=1,0,'
              'ABS(INDEX(alfa,j_F-1)+(INDEX(alfa,j_F)-INDEX(alfa,j_F-1))*(req_F-INDEX(fyF,j_F-1))/(INDEX(fyF,j_F)-'
              'INDEX(fyF,j_F-1)))))),"-")')
        ar = (af.replace('pre_F<>"-"', "NOT(ISNUMBER(cap0_R))").replace("cap_F", "cap0_R").replace("idx_F", "idx0_R")
              .replace("j_F", "j_R").replace("req_F", "req_R").replace("fyF", "fy0R"))
        fx = ('=IF(AND(ISNUMBER(phi),{h9}=1),IF(AND({h9v}=1,OR(aF="semF",aR="semF")),"semF",0.5*{rho}*{cda}*ABS(ay)*{R}'
              '+'
              '{crr}*{m}*9.81+IF({h9v}=1,req_F*aF+req_R*aR,ABS(req_F)*{tanf})),0)')
        cel_map = {"pre_F": cel17("pre_F"), "req_F": cel17("req_F"), "cap_F": cel17("cap_F"), "idx_F": cel17("idx_F"),
                   "j_F": cel17("j_F"), "j_R": cel17("j_R"), "cap0_R": cel17("cap0_R"), "idx0_R": cel17("idx0_R"),
                   "req_R": cel17("req_R"), "aF": cel17("aF"), "aR": cel17("aR"), "phi": cel17("phi"),
                   "ay": cel17("ay"), "alfa": alfa_ref, "fyF": faixa(("fy", "F", 0), ("fy", "F", ae.N_ALFA - 1)),
                   "fy0R": faixa(("fy0", "R", 0), ("fy0", "R", ae.N_ALFA - 1))}
        tok = re.compile(r"\b(" + "|".join(sorted(cel_map, key=len, reverse=True)) + r")\b")
        for nome_c, tpl in (("aF", af), ("aR", ar), ("fxr", fx)):
            alvo_c = g17[cel17(nome_c)].value
            esperado_c = sub(tok.sub(lambda m_: cel_map[m_.group(1)], tpl))
            ok_c = alvo_c == esperado_c
            cat_ok &= ok_c
            if not ok_c:
                cat_det.append(f"17 {nome_c}: {alvo_c[:80]} != {esperado_c[:80]}")
        if cat is not None:   # as fórmulas de aF e de fxr, no texto do catálogo
            cat_ok &= 'IF(pre_F<>"-","semF",IF(req_F>=cap_F,ABS(INDEX(alfa,idx_F))' in cat \
                and "IF({h9v}=1,req_F*aF+req_R*aR,ABS(req_F)*{tanf})" in cat
        # proteção (C-B1)
        protegidas = [ws.title for ws in wb43.worksheets if ws.protection.sheet]
        ocultas = [k for k, v in c43.items() if formula(v) is not None and wb43[k[0]][k[1]].protection.hidden]
        sec = wb43.security      # objeto vazio por padrão no openpyxl; protegido só com bloqueio ou senha da pasta
        prot_ok = not protegidas and not ocultas and not (sec.lockStructure or sec.lockWindows or sec.workbookPassword
                                                          or sec.workbookHashValue)
        # versão e changelog
        a3 = c43[("00_README", "A3")]
        ch = wb43["15_CHANGELOG"]
        a3_ok = a3.startswith("Versão do workbook: V4.3 (incremento 7: centro da curva, raio do skidpad e Fx por "
                              "arrasto induzido") \
            and "V4.2" not in a3 and a3.endswith("| Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated")
        ch_ok = ch["A23"].value == "2026-11" and ch["B23"].value.startswith("V4.3, ") \
            and "EDR-069" in ch["C23"].value \
            and "docs/registro-de-versoes-V4_3-celulas.md" in ch["C23"].value \
            and all(ch[f"{c}24"].value is None for c in "ABC") \
            and all(list(ch[f"{c}23"]._style) == list(ch[f"{c}22"]._style) for c in "ABC") \
            and ch["A22"].value == "2026-10" and c42[("15_CHANGELOG", "B22")].startswith("V4.2, ")
        # estrutura das outras abas
        e42, e43 = cp._estrutura(v42), cp._estrutura(regen1)
        e16_42, e16_43 = e42["16_EQUILIBRIO"], e43["16_EQUILIBRIO"]
        dv16_ok = e16_43["formatação condicional"] == e16_42["formatação condicional"] \
            and e16_43["colunas ocultas"] == e16_42["colunas ocultas"] \
            and {c for s, _ in e16_43["validação"] for c in s.split()} == \
            {c for s, _ in e16_42["validação"] for c in s.split()} - {f"B{r9}", f"E{r9}"}
        est_ok = estrutura_igual_menos(e42, e43, "16_EQUILIBRIO") and set(e43) == set(e42) | {ac.ABA24} and dv16_ok
        # ainda: os nomes dos resultados novos guardam o resultado do catálogo (rótulos únicos e dentro de 40
        # caracteres de slug)
        reg_md = (tmp / "registro.md").read_text(encoding="utf-8")
        reg_md_ok = reg_md.startswith("# Registro de células da V4.3") and reg_md.count("\n| ") >= 60 \
            and "\r" not in reg_md and "| 16_EQUILIBRIO | B9 |" in reg_md and "colunas FI a GM" in reg_md \
            and "colunas ES a FW" in reg_md
        ok_001 = abas_ok and diff_ok and n_form_ok and f24_ok and nomes_ok and b9_ok and dv24_ok and col_ok \
            and leitores_ok and pega and cat_ok and prot_ok and a3_ok and ch_ok and est_ok and reg_md_ok
        check("TC-WB43-001: estrutura da V4.3 gerada da tag v4.2: abas (+24_CURVA no fim); diff de texto V4.2 -> "
              "V4.3 = exatamente o registro de células; nomes = os da V4.2 + data/nomes_V4_3.csv, um por célula; "
              "ent_16_raio_do_skidpad_r continua em B9 (fórmula, estilo de resultado, sem validação); validações da "
              "24_CURVA; colunas novas das grades nos endereços de colunas_v43; todo leitor de {R} guardado e "
              "nenhum ISBLANK; nenhuma proteção; A3 e changelog",
              ok_001,
              f"abas={abas_ok} diff={diff_ok} (registro {len(celulas_reg)}; só no registro {so_reg[:3]}; só no "
              f"diff {so_dif[:3]}) fórmulas={n_form_ok} ({n_f42}->{n_f43}, +{delta}) 24_CURVA={f24_ok} "
              f"nomes={nomes_ok} ({len(n43)}) B9={b9_ok} validações24={dv24_ok} colunas={col_ok} "
              f"leitores={leitores_ok} ({len(leitores)} células; sem guarda {sem_guarda[:3]}; ISBLANK "
              f"{isblank[:3]}; fora das grades {fora_grade}) proteção={prot_ok} ({protegidas}/{len(ocultas)}) "
              f"catálogo={cat_ok} {cat_det[:3]} A3={a3_ok} changelog={ch_ok} estrutura={est_ok} "
              f"registro.md={reg_md_ok}")
        wb42.close()
        wb43.close()

        # ---------------- TC-WB43-002 ----------------
        g43.gerar(v42, regen2)
        ok_dup, rel_dup = cp.comparar_xlsx(regen1, regen2, cp.FORMULAS_ESPERADAS_V43, estrutura=True)
        entregue = cp.ENTREGUE_XLSX_V43
        if entregue.exists():
            ok_ent, rel_ent = cp.comparar_xlsx(regen1, entregue, cp.FORMULAS_ESPERADAS_V43, estrutura=True)
        else:
            ok_ent, rel_ent = True, ["excel/…V4_3.xlsx ainda não existe (vai a excel/ num commit próprio): "
                                     "comparação adiada"]
        fantasma = tmp / "nao_existe.xlsx"
        saida_excel = RAIZ / "excel" / "_teste_recusa_V4_3.xlsx"
        rec_excel = raises(lambda: g43.gerar(fantasma, saida_excel), SystemExit) and not saida_excel.exists()
        b42 = v42.read_bytes()
        rec_origem = raises(lambda: g43.gerar(v42, v42), SystemExit) and v42.read_bytes() == b42
        csv_ok = ler_tabela(CSV43) == list(ac.NOMES_V43) and CSV43.read_bytes().endswith(b"\n") \
            and raises(lambda: g43.gerar(v42, tmp / "csv_ruim.xlsx", nomes=list(ac.NOMES_V43)[:-1]), ValueError) \
            and not (tmp / "csv_ruim.xlsx").exists()
        wbr = openpyxl.load_workbook(regen1)
        num, den = wbr[ac.ABA24]["B34"].value[1:].split("/")     # o texto é "=4/3": a constante, sem avaliar
        fator_ok = wbr[ac.ABA24]["B34"].value == "=4/3" and equilibrio.FATOR_NEUTRO == 4 / 3 \
            and float(num) / float(den) == equilibrio.FATOR_NEUTRO
        wbr.close()
        check("TC-WB43-002: CA-07 da V4.3: duas regenerações (da tag e do arquivo extraído) iguais, com estrutura "
              f"({cp.FORMULAS_ESPERADAS_V43} fórmulas); igual a excel/…V4_3.xlsx se existir; recusa saída em excel/ e "
              f"saída = origem "
              "sem abrir nem criar arquivo; data/nomes_V4_3.csv = aba_curva.NOMES_V43 e o gerador recusa um CSV "
              "diferente; "
              "24_CURVA B34 = `=4/3` = equilibrio.FATOR_NEUTRO",
              ok_dup and ok_ent and rec_excel and rec_origem and csv_ok and fator_ok,
              f"regen={ok_dup} entregue={ok_ent} recusas={rec_excel}/{rec_origem} csv={csv_ok} fator={fator_ok} | "
              + " ; ".join(r for r in rel_ent if not r.startswith("  DIF"))[:300]
              + ("" if ok_dup else " | " + " ; ".join(rel_dup[:6])))

        # ---------------- TC-WB43-006 ----------------
        tc_wb43_006(tmp, v42, regen1)


def tc_wb43_006(tmp: Path, v42: Path, v43: Path) -> None:
    """TC-WB43-006: migração da viva V4.2 para a V4.3 (C-M1 a C-M4) em cópias; nada vai ao Drive nem a excel/."""
    base = tmp / "viva_t"
    base.mkdir()
    cont = [0]
    R, ORG_R, FTE_R = (f"{p}_16_raio_do_skidpad_r" for p in ("ent", "org", "fte"))
    N_RMAN, N_MODO = ac.NOME24["rman"], ac.NOME24["modo"]
    N_ORG, N_FTE = "org_24_r_manual", "fte_24_r_manual"

    def pasta() -> Path:
        cont[0] += 1
        d = base / f"tmp_{cont[0]}"
        d.mkdir()
        return d

    def viva_v42(nome: str, dados: dict) -> Path:
        d = base / nome
        d.mkdir()
        arq = d / "FSAE_EV_Suspension_Fase1_V4_2.xlsx"
        dp.injetar(v42, dados, arq)
        return arq

    def viva_v43(nome: str, edicoes: dict) -> Path:
        d = base / nome
        d.mkdir()
        arq = d / "FSAE_EV_Suspension_Fase1_V4_3.xlsx"
        wb = openpyxl.load_workbook(v43)
        try:
            for (aba, cel), valor in edicoes.items():
                wb[aba][cel].value = valor
            wb.save(arq)
        finally:
            wb.close()
        return arq

    def migrar(viva: Path, nome: str, referencia=None):
        s, r = base / f"mig_{nome}" / "saida.xlsx", base / f"mig_{nome}" / "relatorio.md"
        cod = migr_viva.migrar(viva, v43, s, r, pasta(), referencia_antiga=referencia)
        return cod, s, (r.read_text(encoding="utf-8") if r.exists() else "")

    # C-M1: os nomes de B9 e E9 não são destinos na V4.3; na V4.2 são
    wb43 = openpyxl.load_workbook(v43)
    wb42 = openpyxl.load_workbook(v42)
    try:
        dest43, dest42 = dp._destinos(wb43), dp._destinos(wb42)
        formulas_43 = [n for n, (a, c) in dest43.items() if dp._eh_formula(wb43[a][c].value)]
    finally:
        wb43.close()
        wb42.close()
    m1_ok = R not in dest43 and ORG_R not in dest43 and FTE_R in dest43 and dest42[R] == (ae.ABA16, "B9") \
        and dest42[ORG_R] == (ae.ABA16, "E9") and not formulas_43 \
        and dest43[N_RMAN] == (ac.ABA24, "B8") and dest43[N_ORG] == (ac.ABA24, "E8") \
        and dest43[N_FTE] == (ac.ABA24, "F8") and dest43[N_MODO] == (ac.ABA24, "B4")
    d43 = dp.ler_por_nome(v43)

    def igual_ao_padrao(saida: Path, excecoes: set) -> bool:
        ds = dp.ler_por_nome(saida)
        return set(ds) == set(d43) and all(dp.iguais(ds[n], d43[n]) for n in d43 if n not in excecoes)

    def sem_conflito(texto: str) -> bool:
        return "| Conflitos (não escritos) | 0 |" in texto and "| Faltando na versão nova | 0 |" in texto \
            and "Resultado: **PASS**" in texto

    def b9_formula(saida: Path) -> bool:
        wb = openpyxl.load_workbook(saida)
        try:
            return all(dp._eh_formula(wb[ae.ABA16][c].value) for c in ("B9", "E9"))
        finally:
            wb.close()

    # B9 = 8,3 (E9 e F9 intactos): o R vira o manual, o modo vira Manual, as entradas novas no padrão
    cod_a, s_a, t_a = migrar(viva_v42("b9", {R: 8.3}), "b9")
    da = dp.ler_por_nome(s_a) if s_a.exists() else {}
    a_ok = cod_a == 0 and da.get(N_RMAN) == 8.3 and da.get(N_MODO) == "Manual" and sem_conflito(t_a) \
        and igual_ao_padrao(s_a, {N_RMAN, N_MODO}) and b9_formula(s_a) and f"`{N_RMAN}`" in t_a \
        and f"`{N_MODO}`" in t_a and f"`{R}`" not in t_a.split("## Escritas")[1]
    # B9 vazio e outro dado qualquer da equipe: o modo fica no padrão e o R manual vazio
    d42 = dp.ler_por_nome(v42)
    outro = next(n for n in sorted(d43) if n.startswith("ent_") and isinstance(d43[n], (int, float))
                 and not isinstance(d43[n], bool) and n in d42)
    cod_b, s_b, t_b = migrar(viva_v42("b9_vazio", {outro: d43[outro] + 1.5}), "b9_vazio")
    db = dp.ler_por_nome(s_b) if s_b.exists() else {}
    b_ok = cod_b == 0 and db.get(N_MODO) == "Linha central" and db.get(N_RMAN) is None and sem_conflito(t_b) \
        and dp.iguais(db.get(outro), d43[outro] + 1.5) and igual_ao_padrao(s_b, {outro})
    # E9 trocado pela equipe: vai à E8; a E9 da V4.3 continua fórmula
    cod_c, s_c, t_c = migrar(viva_v42("e9", {ORG_R: origens.OUTRO_CARRO}), "e9")
    dc = dp.ler_por_nome(s_c) if s_c.exists() else {}
    c_ok = cod_c == 0 and dc.get(N_ORG) == origens.OUTRO_CARRO and dc.get(N_MODO) == "Linha central" \
        and sem_conflito(t_c) and igual_ao_padrao(s_c, {N_ORG}) and b9_formula(s_c)
    # F9 trocado pela equipe: vai à F8, sem conflito (o F8 padrão difere do F9 da V4.2)
    texto_f = "fonte da equipe: regulamento da prova"
    cod_d, s_d, t_d = migrar(viva_v42("f9", {FTE_R: texto_f}), "f9")
    dd = dp.ler_por_nome(s_d) if s_d.exists() else {}
    d_ok = cod_d == 0 and dd.get(N_FTE) == texto_f and sem_conflito(t_d) and igual_ao_padrao(s_d, {N_FTE}) \
        and dd.get(FTE_R) == d43[FTE_R]
    # C-M4: viva V4.3 com B9 ou E9 sobrescritos por número
    rec_b9, s_e1, t_e1 = migrar(viva_v43("v43_b9", {(ae.ABA16, "B9"): 9.0}), "v43_b9", referencia=v43)
    rec_e9, s_e2, t_e2 = migrar(viva_v43("v43_e9", {(ae.ABA16, "E9"): 7}), "v43_e9", referencia=v43)
    cod_ok, s_ok, t_ok = migrar(viva_v43("v43_ok", {(ac.ABA24, "B8"): 8.5, (ac.ABA24, "B4"): "Manual"}), "v43_ok",
                                referencia=v43)
    dok = dp.ler_por_nome(s_ok) if s_ok.exists() else {}
    m4_ok = rec_b9 == 2 and "fora dos nomes de dado" in t_e1 and "16_EQUILIBRIO!B9" in t_e1 and not s_e1.exists() \
        and rec_e9 == 2 and "fora dos nomes de dado" in t_e2 and "16_EQUILIBRIO!E9" in t_e2 and not s_e2.exists() \
        and cod_ok == 0 and dok.get(N_RMAN) == 8.5 and dok.get(N_MODO) == "Manual"
    # o redirecionamento só vale para V4.2 -> V4.3
    red_ok = set(migr_viva.REDIRECIONAMENTOS) == {("V4.2", "V4.3")} \
        and migr_viva.REDIRECIONAMENTOS[("V4.2", "V4.3")] == {R: N_RMAN, ORG_R: N_ORG, FTE_R: N_FTE}
    check("TC-WB43-006: migração V4.2 -> V4.3 (C-M1 a C-M4): nomes de B9 e E9 fora dos destinos da V4.3; B9 = 8,3 vai ao R "
          "manual com o modo Manual e as entradas novas no padrão, sem conflito; B9 vazio mantém o modo Linha central; E9 e "
          "F9 da equipe vão à E8 e F8 (E9 continua fórmula); viva V4.3 com B9 ou E9 sobrescritos dá código 2",
          m1_ok and a_ok and b_ok and c_ok and d_ok and m4_ok and red_ok,
          f"C-M1={m1_ok} B9={a_ok}({cod_a}) vazio={b_ok}({cod_b}) E9={c_ok}({cod_c}) F9={d_ok}({cod_d}) "
          f"C-M4={m4_ok}({rec_b9},{rec_e9},{cod_ok}) redirecionamentos={red_ok}")


main()
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print("\n--- Resumo ---")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
sys.exit(1 if n_fail else 0)
