"""Aba 24_CURVA e as alterações de células existentes fora das grades da V4.3 (incremento 7, parte 7b; EDR-066 e
EDR-069).

Catálogo aprovado pelo usuário célula a célula em 2026-11-03 (`.superpowers/sdd/2026-10-29-inc7-fisica-planilha-plans/
catalogo-v43.md`); cada fórmula abaixo é o texto do catálogo, com os `{nomes}` trocados pelos nomes definidos (regras
do EDR-058):
- C-A: a aba nova `24_CURVA`, depois da `23_LISTAS`: o modo do raio R (Linha central, Rente aos cones ou Manual), os
  diâmetros do skidpad, a meia largura do pneu, o R manual, as chaves `h2v` (forma do Ackermann) e `h9v` (forma do Fx
  exigido), o R usado e o seu motivo, o centro da curva (R_c, θ_FL, θ_FR, θ̄_F), as verificações novas, o fator da
  faixa do NEUTRO (C-F1, C-F5) e a situação da aba (B37, lida pelo status da 16_EQUILIBRIO);
- C-B: `16_EQUILIBRIO!B9` deixa de ser entrada e passa a `={R usado}` (o nome `ent_16_raio_do_skidpad_r` continua
  nela, D4: nenhuma fórmula que a lê muda de texto); E9 passa à pior origem do R; A9 e F9 avisam; B65 (verificação do
  R), B173 (tempo de volta) e E173, B78 (status), F142 (observação do NEUTRO);
- C-C1 e C-C2: Δα das rodas dianteiras com o Ackermann do centro da curva único (B114, B115);
- C-F2: as duas células da diferença S − S2 (B137, B138) e as do bloco "cálculo por linha" da 20_EQ_TROCA multiplicam
  o |S − S2| pelo fator da faixa do NEUTRO (24_CURVA B34);
- C-D: o aviso na 14_DASHBOARD A48:D48; e a versão (00_README A3, 15_CHANGELOG linha 23). As colunas novas das grades
  (C-G, C-E2) saem de `aba_equilibrio.linha_grade_v43`, aplicadas por `gerar_v4_3`.

Nenhuma função salva a planilha viva nem a de referência.
"""
from __future__ import annotations

import copy

from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, PatternFill
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

import aba_equilibrio as ae
import origens
import skidpad
from aba_equilibrio import Entrada, Verificacao
from atualizar_planilha import COR_ORIGEM, CONF, NOME_LISTA, ORIGENS_LISTA
from nomes_v4_0 import NOME_VALIDO, Nome, parece_referencia, slug
from raizes import Grafo, linha

ABA24 = "24_CURVA"
MODOS24 = ("Linha central", "Rente aos cones", "Manual")
LISTA_MODOS = ",".join(MODOS24)

FONTE_DIAMETROS_24 = (f"{skidpad.FONTE_DIAMETROS} (o regulamento da competição do T11; "
                      "FSAE Brasil a conferir no inc. 9)")
FONTE_MEIA_LARGURA = ("WIDTH/2 do Hoosier_R25B_13x7_TTC_provisional.tir (0,1778 m / 2; SUS-1011). "
                      "Provisório até o pneu do T11.")

ENTRADAS24 = (
    Entrada("modo", "Modo do raio R", "Linha central", "-", "SUS-1009; EDR-069 (D5)",
            "Linha central: R = (D_int + D_ext)/4. Rente aos cones: o R que deixa a roda interna de cada eixo "
            "encostada "
            "no círculo interno (limite geométrico, não é a trajetória real). Manual: o R digitado abaixo. Escolha de "
            "modelo, não dado do carro: não entra na pior origem.", "lista_modo"),
    Entrada("dint", "Diâmetro do círculo interno", skidpad.D_INTERNO_M, "m", "SUS-1009; spec §3.2",
            FONTE_DIAMETROS_24, "positivo"),
    Entrada("dext", "Diâmetro do círculo externo", skidpad.D_EXTERNO_M, "m", "SUS-1009; spec §3.2",
            FONTE_DIAMETROS_24, "positivo"),
    Entrada("w", "Meia largura do pneu", 0.0889, "m", "SUS-1011; spec §3.2", FONTE_MEIA_LARGURA, "positivo"),
    Entrada("rman", "R manual", None, "m", "SUS-1009; EDR-069 (D4)",
            "R digitado (modo Manual). Na migração da V4.2, recebe o B9 da viva.", "positivo"),
    Entrada("h2v", "Chave h2v: forma do Ackermann", 1, "0/1", "EDR-066; spec §4.1",
            "1 = centro da curva no eixo traseiro (V4.3, EDR-066); 0 = velocidades paralelas (V4.2)", "chave"),
    Entrada("h9v", "Chave h9v: forma do Fx exigido", 1, "0/1", "EDR-066; spec §4.2",
            "1 = arrasto induzido (V4.3, EDR-066); 0 = F_yf·tan(L/R) (V4.2)", "chave"),
)
ORIGEM24 = {"modo": CONF, "dint": origens.T11, "dext": origens.T11, "w": skidpad.ORIGEM_MEIA_LARGURA, "rman": CONF,
            "h2v": CONF, "h9v": CONF}
LINHA24_ENTRADA0 = 4
LINHA24 = {e.chave: LINHA24_ENTRADA0 + i for i, e in enumerate(ENTRADAS24)}


def _nome_ent24(e: Entrada, papel: str = "ent") -> str:
    return f"{papel}_24_{slug(e.rotulo)}"


# Resultados da 24_CURVA: chave, linha, rótulo, unidade, referência (a fórmula vem de `_formula24`). A B34 é a
# constante do modelo (fator da faixa do NEUTRO, C-F1); as demais linhas de dado (B4 a B10) estão em ENTRADAS24.
RES24 = (
    ("vh2v", 11, "Verificação: chave h2v deve ser 0 ou 1", "-", "EDR-066"),
    ("vh9v", 12, "Verificação: chave h9v deve ser 0 ou 1", "-", "EDR-066"),
    ("rlc", 13, "R da linha central", "m", "SUS-1009"),
    ("rin", 14, "R_in' (raio interno + meia largura)", "m", "SUS-1009; spec §3.2"),
    ("lim_tras", 15, "Limite traseiro R_in' + t_r/2", "m", "SUS-1009; spec §3.2"),
    ("lim_diant", 16, "Limite dianteiro t_f/2 + √(R_in'² − L²)", "m", "SUS-1009; spec §3.2"),
    ("rc", 17, "R_c rente aos cones", "m", "SUS-1009; spec §3.2"),
    ("rrente", 18, "R rente aos cones", "m", "SUS-1009; spec §3.2"),
    ("eixo", 19, "Eixo que manda (SUS-1010)", "-", "SUS-1010; spec §3.2"),
    ("rusado", 20, "R usado", "m", "SUS-1009; EDR-069"),
    ("motivo_r", 21, "Motivo do R", "-", "SUS-1009; EDR-069"),
    ("rcc", 22, "R_c do centro da curva", "m", "EDR-069; spec §3.1"),
    ("pior_r", 23, "Pior origem do R", "-", "SUS-1009; D16"),
    ("thFL", 25, "θ_FL", "rad", "EDR-066; spec §3.1 e §4.1"),
    ("thFR", 26, "θ_FR", "rad", "EDR-066; spec §3.1 e §4.1"),
    ("thm", 27, "θ̄_F", "rad", "EDR-066; spec §4.1"),
    ("vgeo", 28, "Verificação: geometria do centro da curva", "-", "EDR-066; spec §3.1"),
    ("fator", 34, "Fator da faixa do NEUTRO", "-", "EDR-065 (item 2)"),
    ("vfat", 35, "Verificação: fator da faixa do NEUTRO", "-", "EDR-065 (item 2)"),
    ("sit24", 37, "Situação da 24_CURVA", "-", "EDR-066; EDR-069"),
)
LINHA24_RES = {k: lin for k, lin, *_ in RES24}
TEXTO_A30 = ("Só no Python (python/mmm.py e a escada de hipóteses, sem chave nesta planilha): a hipótese 7 com os dois "
             "sentidos de curva num só caso (sentido) e as hipóteses acopladas: cos_delta, tracao, diferencial e "
             "transf_long.")
TEXTO_A31 = ("Limitação do centro da curva no eixo traseiro (spec §3.1): o α real da traseira desloca o centro para a "
             "frente da linha do eixo traseiro, e a planilha não corrige isso.")
TEXTO_A32 = ("A diferença para o Python cinemático (β real, mmm.alfa_rodas) é medida pela escada de hipóteses "
             "(python/escada.py), não corrigida aqui.")


def _nomes_v43() -> list[Nome]:
    """Nomes da V4.3 (data/nomes_V4_3.csv): `ent_`, `org_` e `fte_` `24_<slug do rótulo>` nas entradas B4 a B10 e
    `res_24_<slug>` em cada resultado de coluna B (EDR-058). Um nome por célula, sem apelido (D4)."""
    out = []
    for e in ENTRADAS24:
        r = LINHA24[e.chave]
        for papel, col in (("ent", "B"), ("org", "E"), ("fte", "F")):
            out.append(Nome(_nome_ent24(e, papel), ABA24, f"{col}{r}", papel, "", e.rotulo))
    for _, lin, rotulo, _, _ in RES24:
        out.append(Nome(ae._nome_res(ABA24, rotulo), ABA24, f"B{lin}", "res", "", rotulo))
    vistos = set()
    for n in out:
        if n.nome in vistos or not NOME_VALIDO.fullmatch(n.nome) or parece_referencia(n.nome):
            raise ValueError(f"nome inválido ou repetido na V4.3: {n.nome}")
        vistos.add(n.nome)
    return out


NOMES_V43: list[Nome] = _nomes_v43()
NOME24: dict[str, str] = {e.chave: _nome_ent24(e) for e in ENTRADAS24}
NOME24.update({k: ae._nome_res(ABA24, rot) for k, _, rot, _, _ in RES24})


def celulas_de_entrada_v43() -> set[tuple[str, str]]:
    """Células de entrada da V4.3: as da V4.2 (`aba_metas.celulas_de_entrada_v42()`, que inclui as da V4.1 e as das
    fichas da 03_TARGETS) menos 16_EQUILIBRIO B9 e E9 (que viraram fórmula: o R usado e a pior origem dele) mais
    valor (B), Origem (E) e Fonte (F) de cada entrada da 24_CURVA. A F9 fica (texto de aviso, com o nome
    `fte_16_raio_do_skidpad_r`)."""
    import aba_metas
    base = aba_metas.celulas_de_entrada_v42() - {(ae.ABA16, f"{c}{ae.LINHA_ENTRADA['R']}") for c in "BE"}
    return base | {(ABA24, f"{c}{LINHA24[e.chave]}") for e in ENTRADAS24 for c in "BEF"}


def mapa_v43() -> ae._Subst:
    """Mapa de nomes das fórmulas da V4.3: o da V4.2 (`aba_equilibrio._mapa_base`) e os nomes da 24_CURVA. Sem `PIOR`
    e `PIOR_K`: o gerador nunca regenera a pior origem das 16 a 22 (E173 lê a fórmula que já está na V4.2)."""
    m = ae._mapa_base(ae._colunas(ae.N_ALFA, True), [], [])
    m.pop("PIOR")
    m.pop("PIOR_K")
    repetidas = set(m) & set(NOME24)
    if repetidas:
        raise ValueError(f"chaves de fórmula repetidas na V4.3: {sorted(repetidas)}")
    m.update(NOME24)
    return m


# ---------------------------------------------------------------------------------------------------------------------
# Fórmulas da 24_CURVA (catálogo C-A, C-F1, C-F5)
# ---------------------------------------------------------------------------------------------------------------------
def termos_pior_r(wb) -> dict[str, list]:
    """Termos (aba, célula de Origem, None) da pior origem do R por modo (C-A17): Linha central: E5 e E6; Rente aos
    cones: E5, E6, E7 e as origens das raízes de b, L, t_f e t_r; Manual: E8. Raízes pelo grafo de fórmulas
    (`raizes.Grafo`)."""
    e = lambda chave: (ABA24, f"E{LINHA24[chave]}", None)
    g = Grafo(wb)
    achados: dict = {}
    for chave in ("b", "L", "tF", "tR"):
        for raiz in g.raizes_preenchidas(ae._destino(wb, ae.V40[chave])):
            aba, cel = ae._origem_da_raiz(*raiz)
            achados[(aba, cel)] = (aba, cel, None)
    raizes = [achados[k] for k in sorted(achados, key=lambda t: (t[0], linha(t[1]), t[1]))]
    return {"Linha central": [e("dint"), e("dext")], "Rente aos cones": [e("dint"), e("dext"), e("w"), *raizes],
            "Manual": [e("rman")]}


def _formula24(chave: str, pior: dict[str, list]) -> str:
    """Fórmula (com {nomes}) do resultado `chave` da 24_CURVA, no texto do catálogo."""
    if chave in ("vh2v", "vh9v"):
        return "=" + ae._cond_verif(ae.VERIFICACOES_24[0 if chave == "vh2v" else 1])
    ok_diam = "AND(ISNUMBER({dint}),ISNUMBER({dext}),{dint}>0,{dext}>{dint})"
    f = {
        "rlc": f'=IF({ok_diam},({{dint}}+{{dext}})/4,"")',
        "rin": f'=IF({ok_diam},{{dint}}/2+IF(ISNUMBER({{w}}),{{w}},0),"")',
        "lim_tras": '=IF(AND(ISNUMBER({rin}),ISNUMBER({tR})),{rin}+{tR}/2,"")',
        "lim_diant": ('=IF(AND(ISNUMBER({rin}),ISNUMBER({L}),ISNUMBER({tF})),IF({rin}>{L},{tF}/2+SQRT({rin}^2-{L}^2),'
                      '"- (R_in\' ≤ L)"),"")'),
        "rc": '=IF(AND(ISNUMBER({lim_tras}),{lim_diant}<>""),MAX({lim_tras},{lim_diant}),"")',
        "rrente": '=IF(AND(ISNUMBER({rc}),ISNUMBER({b})),SQRT({b}^2+{rc}^2),"")',
        "eixo": ('=IF(NOT(ISNUMBER({rc})),"-",IF(NOT(ISNUMBER({lim_diant})),"traseiro",IF(ABS({lim_tras}-{lim_diant})<='
                 '1E-9,'
                 '"empate",IF({lim_tras}>{lim_diant},"traseiro","dianteiro"))))'),
        "rusado": ('=IFERROR(IF(EXACT({modo},"Manual"),IF(ISNUMBER({rman}),{rman},""),IF(EXACT({modo},"Linha central"),'
                   '{rlc},IF(EXACT({modo},"Rente aos cones"),{rrente},""))),"")'),
        "motivo_r": (f'=IF(NOT(OR(EXACT({{modo}},"Linha central"),EXACT({{modo}},"Rente aos '
                     f'cones"),EXACT({{modo}},"Manual"))),'
                     f'"{skidpad.MOTIVO_MODO_INVALIDO}",IF(ISNUMBER({{rusado}}),IF(AND(EXACT({{modo}},"Rente aos '
                     f'cones"),'
                     f'NOT(ISNUMBER({{w}}))),"{skidpad.MOTIVO_SEM_MEIA_LARGURA}","-"),IF(EXACT({{modo}},"Manual"),'
                     f'"{skidpad.MOTIVO_MANUAL_VAZIO}",IF(NOT(ISNUMBER({{rin}})),"{skidpad.MOTIVO_DIAMETROS}",'
                     f'IF(NOT(ISNUMBER({{tR}})),"{skidpad.MOTIVO_BITOLA_TRASEIRA}","{skidpad.MOTIVO_VEICULO}")))))'),
        "rcc": ('=IF(NOT(ISNUMBER({rusado})),"-",IF(NOT(ISNUMBER({b})),"-",IF({rusado}<={b},"R ≤ b: a confirmar",'
                'SQRT({rusado}^2-{b}^2))))'),
        "pior_r": ('=IF(EXACT({modo},"Linha central"),' + ae._formula_pior(pior["Linha central"])
                   + ',IF(EXACT({modo},"Rente aos cones"),' + ae._formula_pior(pior["Rente aos cones"])
                   + ',IF(EXACT({modo},"Manual"),' + ae._formula_pior(pior["Manual"]) + f',"{CONF}")))'),
        "thFL": ('=IF(AND({h2v}=1,ISNUMBER({rcc}),ISNUMBER({L}),ISNUMBER({tF})),IF({rcc}>{tF}/2,ATAN({L}/({rcc}-{tF}/2)'
                 '),'
                 '"-"),"-")'),
        "thFR": ('=IF(AND({h2v}=1,ISNUMBER({rcc}),ISNUMBER({L}),ISNUMBER({tF})),IF({rcc}>{tF}/2,ATAN({L}/({rcc}+{tF}/2)'
                 '),'
                 '"-"),"-")'),
        "thm": '=IF(AND(ISNUMBER({thFL}),ISNUMBER({thFR})),({thFL}+{thFR})/2,"-")',
        "vgeo": "=" + ae._cond_verif_v43(ae.VERIFICACOES_24[3]),
        "fator": "=4/3",
        "vfat": "=" + ae._cond_verif_v43(ae.VERIFICACOES_24[2]),
        "sit24": '=IF({vh2v}<>"-",{vh2v},IF({vh9v}<>"-",{vh9v},IF({vfat}<>"-",{vfat},{vgeo})))',
    }
    return f[chave]


FAMILIA24 = {k: ("C-F" if k in ("fator", "vfat") else "C-A") for k in LINHA24_RES}


def montar_24(wb) -> list[dict]:
    """Escreve a aba 24_CURVA no fim do workbook da V4.2 (aberto pelo openpyxl, com os nomes da V4.2) e devolve o
    registro [{aba, cel, familia, formula}] de toda célula com fórmula escrita. Não acrescenta os nomes nem salva."""
    if ABA24 in wb.sheetnames:
        raise ValueError(f"a aba {ABA24} já existe")
    if wb.sheetnames[-1] != "23_LISTAS":
        raise ValueError(f"a última aba deveria ser 23_LISTAS; é {wb.sheetnames[-1]}")
    est = ae._estilos(wb)
    ws = wb.create_sheet(ABA24)
    mapa = mapa_v43()
    registro: list[dict] = []
    ctx = ae._Ctx(wb, registro, mapa)
    pior = termos_pior_r(wb)
    ws["A1"] = ("24_CURVA — raio do skidpad R, centro da curva e formas da V4.3 (EDR-066 e EDR-069; SUS-1009 a "
                "SUS-1011)")
    ae._estilo(ws["A1"], est, "titulo")
    ws["A2"] = ("Entradas (B4 a B10) e resultados. O R usado (B20) vai à 16_EQUILIBRIO B9, que deixou de ser entrada. "
                "As chaves "
                "h2v e h9v escolhem a forma V4.3 (1) ou a da V4.2 (0). Resultados DEMONSTRATIVOS enquanto a pior "
                "origem "
                "(B23, ou a coluna E da 16) não for \"" + origens.T11 + "\" (D16).")
    for col, t in zip("ABCDEF", ("Entrada / resultado", "Valor", "Unidade", "Referência",
                                 "Origem (entradas) / pior origem (resultados)", "Fonte / observação")):
        ws[f"{col}3"] = t
        ae._estilo(ws[f"{col}3"], est, "cab")
    for e in ENTRADAS24:
        r = LINHA24[e.chave]
        ws[f"A{r}"], ws[f"B{r}"], ws[f"C{r}"], ws[f"D{r}"] = e.rotulo, e.padrao, e.unidade, e.ref
        ws[f"E{r}"], ws[f"F{r}"] = ORIGEM24[e.chave], e.fonte
        for col, k in (("A", "rotulo"), ("B", "ent"), ("C", "un"), ("D", "id"), ("E", "org"), ("F", "fte")):
            ae._estilo(ws[f"{col}{r}"], est, k)
        ws[f"F{r}"].alignment = Alignment(wrap_text=True, vertical="top")
    for chave, lin, rotulo, unidade, ref in RES24:
        ws[f"A{lin}"], ws[f"C{lin}"], ws[f"D{lin}"] = rotulo, unidade, ref
        ae._estilo(ws[f"A{lin}"], est, "rotulo")
        ctx.put(ws, f"B{lin}", FAMILIA24[chave], _formula24(chave, pior))
        ae._estilo(ws[f"B{lin}"], est, "calc")
    ws["F20"] = "Vazio ('') com o modo inválido ou sem os dados do modo (o motivo está em B21): nunca erro."
    ws["F34"] = "EDR-065 item 2; docs/inc7/estudo-neutro.md (casos sintéticos)"
    ws["E34"] = "○ Estimativa"
    ae._estilo(ws["E34"], est, "org")
    ae._estilo(ws["F34"], est, "fte")
    for lin, t in ((24, "Centro da curva (EDR-069) e ângulos da velocidade das rodas dianteiras (EDR-066, h2v)"),
                   (29, "Limitações e hipóteses só do Python"),
                   (33, "Faixa do NEUTRO (EDR-065, item 2): fator sobre |S − S2| (16_EQUILIBRIO B137 e B138)"),
                   (36, "Situação das verificações da 24_CURVA (lida pelo status da 16_EQUILIBRIO, B78)")):
        ws[f"A{lin}"] = t
        ae._estilo(ws[f"A{lin}"], est, "secao")
    for lin, t in ((30, TEXTO_A30), (31, TEXTO_A31), (32, TEXTO_A32)):
        ws[f"A{lin}"] = t
    _validacoes24(ws)
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 62, 22
    ws.column_dimensions["D"].width, ws.column_dimensions["E"].width, ws.column_dimensions["F"].width = 30, 30, 80
    return registro


def _validacoes24(ws) -> None:
    def dv(**kw):
        d = DataValidation(allow_blank=True, showErrorMessage=True, errorTitle="Entrada inválida", **kw)
        ws.add_data_validation(d)
        return d

    modo = dv(type="list", formula1=f'"{LISTA_MODOS}"', error="Escolha Linha central, Rente aos cones ou Manual.")
    chave = dv(type="list", formula1='"0,1"', error="Chave de hipótese: 0 (desligada) ou 1 (ligada).")
    positivo = dv(type="decimal", operator="greaterThan", formula1="0", error="Digite um número > 0 (sem unidade).")
    org = dv(type="list", formula1=f"={NOME_LISTA}",
             error="Escolha uma das origens da lista (00_README, 'Como preencher').")
    for e in ENTRADAS24:
        r = LINHA24[e.chave]
        {"lista_modo": modo, "chave": chave, "positivo": positivo}[e.validacao].add(f"B{r}")
        org.add(f"E{r}")
    r0, r1 = LINHA24_ENTRADA0, LINHA24_ENTRADA0 + len(ENTRADAS24) - 1
    for simb, cor in COR_ORIGEM.items():
        regra = FormulaRule(formula=[f'LEFT($E{r0},1)="{simb}"'],
                            fill=PatternFill("solid", start_color=cor, end_color=cor))
        ws.conditional_formatting.add(f"E{r0}:E{r1}", regra)


# ---------------------------------------------------------------------------------------------------------------------
# Alterações em células existentes (C-B, C-C1/C2, C-F2 e C-D; as grades ficam com `linha_grade_v43`)
# ---------------------------------------------------------------------------------------------------------------------
REF_B = "catálogo C-B (aprovado em 2026-11-03); EDR-069 (D4); teste: TC-WB43-001"
REF_C = "catálogo C-C (aprovado em 2026-11-03); EDR-066; teste: TC-WB43-001"
REF_F = "catálogo C-F (aprovado em 2026-11-03); EDR-065 item 2 (revisto); teste: TC-WB43-001"
REF_D = "catálogo C-D (aprovado em 2026-11-03); EDR-066 e EDR-069; teste: TC-WB43-001"
REF_VERSAO = "catálogo C-B6 (aprovado em 2026-11-03); padrão das versões; teste: TC-WB43-001"

TEXTO_A9 = "R usado (fórmula; ver 24_CURVA)"
TEXTO_F9 = ("Não digite aqui: o R manual fica em 24_CURVA B8 (modo em B4). Fórmula da V4.3 (EDR-069, D4); exigido por "
            "h2, h3, h8 e "
            "h9 e pelo tempo de volta.")
TEXTO_F142 = ("NEUTRO: |S_r − S_f| ≤ resolução (B139); com o eixo saturado nas duas grades, a diferença entra "
              "multiplicada pelo "
              "fator 4/3 da 24_CURVA B34 (EDR-065 item 2)")
TEXTO_A3 = ("Versão do workbook: V4.3 (incremento 7: centro da curva, raio do skidpad e Fx por arrasto induzido; "
            "projeto T11) | "
            "Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated")
LINHA_CHANGELOG = 23   # a V4.2 usou a 22
REGISTRO = "docs/registro-de-versoes-V4_3-celulas.md"

TEXTO_B48 = (
    '=IF({sit24}<>"-","24_CURVA: "&{sit24},IF(AND({h2v}=1,{h9v}=1),"V4.3: Ackermann com o centro da curva no eixo '
    'traseiro e '
    'Fx por arrasto induzido (mudou em relação à V4.2; para voltar à V4.2, h2v = 0 e h9v = 0 em 24_CURVA B9 e '
    'B10)","forma da '
    'V4.2 em uso (h2v = "&{h2v}&", h9v = "&{h9v}&"): resultado não comparável com a V4.3 padrão"))&". R = '
    '"&IF(ISNUMBER({rusado}),'
    'SUBSTITUTE(FIXED({rusado},3,TRUE),".",",")&" m ("&IF(EXACT({modo},"Manual"),"manual",LOWER({modo})&", diâmetros '
    'do '
    'regulamento FSAE 2026 D.10.1.1")&")",{motivo_r})')


def _changelog() -> list[tuple[str, str]]:
    lin = LINHA_CHANGELOG
    return [
        (f"A{lin}", "2026-11"),
        (f"B{lin}", "V4.3, centro da curva, raio do skidpad e Fx por arrasto induzido (incremento 7, parte 7b): aba "
         f"24_CURVA (modo do "
                    "raio R, diametros do skidpad, chaves h2v e h9v, fator da faixa do NEUTRO), 16_EQUILIBRIO B9 passa "
                    "a formula "
                    "(R usado), Ackermann com o centro da curva no eixo traseiro (B114 e B115), Fx exigido por arrasto "
                    "induzido "
                    "nas grades (17, 18, 19, 20a a 20d), faixa do NEUTRO com o fator 4/3 e aviso na 14_DASHBOARD. "
                    "Gerada da tag "
                    "v4.2 por python/gerar_v4_3.py."),
        (f"C{lin}", f"EDR-069, EDR-066, EDR-065 (item 2 revisto), SUS-1009 a SUS-1011. Registro celula a celula: "
         f"{REGISTRO}. "
                    "NOT_VALIDATED fisicamente."),
    ]


def _template16(chave: str) -> str:
    return ae._LAYOUT16_POR_CHAVE[chave].formula


def _celula16(chave: str) -> str:
    return f"B{ae.LINHAS16[chave]}"


def alteracoes_v4_3(wb, mapa: dict | None = None) -> list[dict]:
    """Células existentes que a V4.3 muda fora das grades (catálogo C-B, C-C1 e C-C2, C-F2 e C-D, e a versão), cada
    uma com aba, cel, antes (lido de `wb`, a V4.2 aberta; ValueError se não for o esperado), novo e ref. As
    fórmulas saem com os nomes definidos de `mapa` (padrão `mapa_v43()`). Não grava nada."""
    m = mapa_v43() if mapa is None else mapa
    fmt = lambda t: t.format_map(m) if "{" in t else t
    out: list[dict] = []
    ws16, ws14 = wb[ae.ABA16], wb[ae.ABA14]

    def troca(ws, cel, novo, ref, antes=None):
        """antes: texto esperado na V4.2; None = a célula tem de estar vazia; ... = sem conferência aqui."""
        atual = ws[cel].value
        if antes is not ... and atual != antes:
            raise ValueError(f"{ws.title}!{cel}: a V4.2 não tem o texto esperado ({atual!r} != {antes!r})")
        out.append({"aba": ws.title, "cel": cel, "antes": atual, "novo": novo, "ref": ref})

    r9 = ae.LINHA_ENTRADA["R"]
    # C-B2, C-B3, C-B9, C-B5: a B9 deixa de ser entrada (nome ent_16_raio_do_skidpad_r continua nela)
    troca(ws16, f"B{r9}", "={rusado}".format_map(m), REF_B, None)   # a entrada vazia da V4.2
    troca(ws16, f"E{r9}", "={pior_r}".format_map(m), REF_B, CONF)
    troca(ws16, f"A{r9}", TEXTO_A9, REF_B, "Raio do skidpad R")
    troca(ws16, f"F{r9}", TEXTO_F9, REF_B, ae.ENTRADAS16[ae.LINHA_ENTRADA["R"] - ae.LINHA_ENTRADA0].fonte)
    # C-B4: verificação "num" do R
    i_r = next(i for i, vf in enumerate(ae.VERIFICACOES) if (vf.tipo, vf.nome) == ("num", "R"))
    troca(ws16, _celula16(f"vf{i_r}"), fmt("=" + ae._cond_verif_v43(ae.VERIFICACOES_V43[i_r])), REF_B,
          fmt(_template16(f"vf{i_r}")))
    # C-B7: tempo de volta (B173) e a pior origem dele (E173, C-B7b)
    tv = (f'=IF(ISNUMBER({{aylim}}),IF(ISNUMBER({{R}}),IF({{R}}>0,2*PI()*SQRT({{R}}/{{aylim}}),"N/A: raio do skidpad R '
          f'deve ser '
          f'> 0"),IF(ISERROR({{R}}),"N/A: raio do skidpad R com erro",IF({{R}}="","N/A: raio do skidpad R a confirmar '
          f'("&'
          f'{{motivo_r}}&")","N/A: raio do skidpad R não é número"))),"N/A")')
    troca(ws16, _celula16("tvolta"), fmt(tv), REF_B, fmt(_template16("tvolta")))
    e173 = f"E{ae.LINHAS16['tvolta']}"
    pior16 = ws16[e173].value
    if not (isinstance(pior16, str) and pior16.startswith("=INDEX(Origens,MAX(")):
        raise ValueError(f"{ws16.title}!{e173}: a V4.2 não tem a pior origem da 16 esperada: {pior16!r}")
    n = len(ORIGENS_LISTA)
    troca(ws16, e173, f"=INDEX({NOME_LISTA},MAX(IFERROR(MATCH({pior16[1:]},{NOME_LISTA},0),{n}),"
                      f"IFERROR(MATCH({m['pior_r']},{NOME_LISTA},0),{n})))", REF_B, ...)
    # C-B8: status
    ult = f"G_vf{len(ae.VERIFICACOES) - 1}"
    st = f'=IF({{{ult}}}="-",IF({{sit24}}="-","OK",{{sit24}}),{{{ult}}})'
    troca(ws16, _celula16("status"), fmt(st), REF_B, fmt(_template16("status")))
    # C-B10: observação do veredito
    troca(ws16, f"F{ae.LINHAS16['ver']}", TEXTO_F142, REF_B, None)
    # C-C1, C-C2: Δα das rodas dianteiras com o Ackermann do centro da curva
    for c, th in (("FL", "thFL"), ("FR", "thFR")):
        antes = _template16(f"da_{c}")
        d = "{di}" if c == "FL" else "{do}"
        ack = f"(-({d}-{{dref}}))"
        if antes.count(ack) != 1:
            raise ValueError(f"da_{c}: o texto da V4.2 não é o esperado: {antes!r}")
        novo = antes.replace(ack, ack + f"+IF({{h2v}}=1,{{{th}}}-{{thm}},0)")
        troca(ws16, _celula16(f"da_{c}"), fmt(novo), REF_C, fmt(antes))
    # C-F2: |S − S2| vezes o fator, na 16 (B137, B138) e no bloco "cálculo por linha" da 20_EQ_TROCA
    ws20 = wb[ae.ABA20]
    m20 = ae._Subst(m)
    m20.update(ae.V40_20)
    for e in "FR":
        antes = _template16(f"dif_{e}")
        corpo = f"ABS({{S_{e}}}-{{S2_{e}}})"
        if antes.count(corpo) != 1:
            raise ValueError(f"dif_{e}: o texto da V4.2 não é o esperado: {antes!r}")
        novo = antes.replace(corpo, f'IF(ISNUMBER({{fator}}),{{fator}}*{corpo},"-")')
        troca(ws16, _celula16(f"dif_{e}"), fmt(novo), REF_F, fmt(antes))
        for j in ae.EXTRAS20:
            ml = ae._mapa_linha(m20, j)
            cel20 = f"{ae.COL_BLOCO[j]}{ae.LINHA_BLOCO[f'dif_{e}']}"
            troca(ws20, cel20, novo.format_map(ml), REF_F, antes.format_map(ml))
    # C-B11: status das linhas extras das 20a a 20d lê a 24_CURVA como último teste (a mesma troca da C-B8)
    g_ant, ack11 = f"{{G_vf{ae.I_DEN - 1}}}", f"{{vf{ae.I_ACK}}}"
    ant11 = f'=IF({g_ant}<>"-",{g_ant},IF({{vden}}<>"-",{{vden}},IF({ack11}<>"-",{ack11},"OK")))'
    nov11 = (f'=IF({g_ant}<>"-",{g_ant},IF({{vden}}<>"-",{{vden}},IF({ack11}<>"-",{ack11},'
             f'IF({{sit24}}<>"-",{{sit24}},"OK"))))')
    for j in ae.EXTRAS20:
        ml = ae._mapa_linha(m20, j)
        cel20 = f"{ae.COL_BLOCO[j]}{ae.LINHA_BLOCO['status']}"
        troca(ws20, cel20, nov11.format_map(ml), REF_B, ant11.format_map(ml))
    # C-D1 e C-D2: aviso na 14_DASHBOARD (linha vazia entre o equilíbrio e as metas)
    for col, novo in (("A", "Formas da V4.3 (24_CURVA)"), ("B", fmt(TEXTO_B48)), ("C", "-"), ("D", "EDR-066; EDR-069")):
        troca(ws14, f"{col}48", novo, REF_D, None)
    # C-B6: versão e changelog
    if "V4.2" not in wb["00_README"]["A3"].value:
        raise ValueError("00_README A3 não é a da V4.2")
    troca(wb["00_README"], "A3", TEXTO_A3, REF_VERSAO, ...)
    for cel, novo in _changelog():
        troca(wb["15_CHANGELOG"], cel, novo, REF_VERSAO, None)
    return out


def ajustar_estilos(wb) -> None:
    """Estilos e validações das células que `alteracoes_v4_3` reescreve (não mudam o texto): a B9 da 16 vira resultado
    (estilo de resultado, sem a validação numérica, C-B2), a E9 sem a lista de Origens (é fórmula), a linha 23 do
    changelog com o formato da 22 e a linha 48 da 14_DASHBOARD com o das linhas 41 a 47."""
    est = ae._estilos(wb)
    ws16 = wb[ae.ABA16]
    r9 = ae.LINHA_ENTRADA["R"]
    ae._estilo(ws16[f"B{r9}"], est, "calc")
    for dv in ws16.data_validations.dataValidation:
        for cel in (f"B{r9}", f"E{r9}"):
            if cel in dv.sqref:
                dv.sqref.remove(cel)
    ws16.data_validations.dataValidation = [dv for dv in ws16.data_validations.dataValidation
                                            if len(dv.sqref.ranges) > 0]
    ws14 = wb[ae.ABA14]
    for col in "ABCDE":
        ws14[f"{col}48"]._style = copy.copy(ws14[f"{col}47"]._style)
    ws14["B48"].alignment = Alignment(wrap_text=True, vertical="top")
    ch = wb["15_CHANGELOG"]
    for col in "ABCDE":
        ch[f"{col}{LINHA_CHANGELOG}"]._style = copy.copy(ch[f"{col}{LINHA_CHANGELOG - 1}"]._style)


def acrescentar_nomes(wb) -> None:
    """Nomes definidos da V4.3 (NOMES_V43) no escopo do workbook; recusa nome já existente."""
    existentes = set(wb.defined_names)
    for n in NOMES_V43:
        if n.nome in existentes:
            raise ValueError(f"nome já definido: {n.nome}")
        existentes.add(n.nome)
        col = "".join(ch for ch in n.celula if ch.isalpha())
        wb.defined_names[n.nome] = DefinedName(n.nome, attr_text=f"'{n.aba}'!${col}${n.celula[len(col):]}")
