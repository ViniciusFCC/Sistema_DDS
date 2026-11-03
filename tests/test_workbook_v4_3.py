"""
Teste da V4.3 no motor de recálculo (incremento 7, parte 7b: centro da curva, raio do skidpad e Fx por arrasto induzido; projeto
T11; EDR-044, EDR-066, EDR-069): regressão por valor contra a V4.2 (TC-WB43-003), células novas × Python (TC-WB43-004) e barra de
fórmulas (TC-WB43-005). Recalcula CÓPIAS (`gerar_v4_3.copia_v43`: a V4.3 como o gerador a monta, da tag v4.2, + valores de teste, e
a V4.2 da tag v4.2 + os mesmos valores) pelo Excel (COM) ou pelo LibreOffice (recalculo_planilha.py; DDS_RECALC=excel|libreoffice
força um; as fórmulas de matriz dos grafos de `MATCH(TRUE,INDEX(...))` rodam nos dois). A V4.2 e a V4.3 de excel/ e a viva do Drive
nunca são abertas para escrita. Sem motor: NÃO EXECUTÁVEL (código 3), que nunca conta como aprovado.
Uso: uv run python -X utf8 tests/test_workbook_v4_3.py
Namespace TC-WB43-xxx (IDs autorizados: 001 a 006; este script tem o 003, o 004 e o 005; o 001, o 002 e o 006 estão em
tests/test_v4_3.py). DDS_CASOS (mutação da planilha) = lista de casos do 004 que rodam (ou "TC004" para todos), e "TC003"/"TC005" para os outros dois: vazio =
tudo; com a lista, o 003 e o 005 só rodam se nomeados.

TC-WB43-003 (regressão por valor, decisão B do catálogo): a V4.3 com h2v = h9v = 0, modo "Manual" e R manual = o B9 da V4.2 (as
Origens do R em 24_CURVA E8 = as de 16_EQUILIBRIO E9), e a V4.2, recalculadas no Excel com as mesmas entradas, dão os mesmos valores em
todas as células da V4.2 (rel. <= 1e-9; texto exato), fora de:
- as células excluídas pela decisão B: 16_EQUILIBRIO B137 e B138 (diferenças S − S2, que ganham o fator 4/3 sem chave), mais as mesmas
  linhas do bloco "cálculo por linha" da 20_EQ_TROCA (as que `aba_curva.alteracoes_v4_3` altera na 20_EQ_TROCA), e o FECHO TRANSITIVO
  delas (B139, os textos de exibição do veredito, o 14_DASHBOARD do veredito etc.), calculado por um grafo de dependências de TODAS as
  fórmulas da V4.3 (`raizes.referencias`, nomes definidos expandidos); a lista (por aba) vai ao log;
- as células de texto constante que o gerador reescreve (A9, F9, F142, versão e changelog: o texto é outro, o valor é o texto).
Casos: C1_H (V4.2 nominal com R = 8 m, h2, h3 e h9 ligadas, ρ, CdA e Crr de teste), C4b (h2, h3, h7, h8 e h9; a V4.2 do TC-WB41-004),
ORG_TX_H (C3 + R e h2, h3, h9 + todas as Origens em ● Dado do TX; E9 da V4.2 = E8 da V4.3) e, a mais, MANUAL_VAZIO: modo Manual com o
R manual vazio e h2 = h3 = h8 = h9 = 0 (sobre o C3, que satura: sem a saturação o B173 é só "N/A"), contra a V4.2 com B9 vazio. Neste último só mudam o texto da B173 (e as células que dependem
dela), pelo motivo entre parênteses (C-B4 e C-B7), e o E173 (pior origem do R, C-B7b); o que mudar fora desse fecho é falha. As
mudanças intencionais vão ao log.

TC-WB43-004 (células novas e veredito × Python, mudança intencional da V4.2 -> V4.3): com h2v = h9v = 1 (e as outras formas),
`caso_da_planilha_v43` + `equilibrio.analise_par(caso, formas=formas, fator_neutro=B34)` e `equilibrio_linear.tabela_linear(formas=)`
reproduzem a planilha: grades 17 e 18 (capacidade, motivo e folga por linha, 1e-9 relativo; as colunas novas aF, aR e fxr contra
`alfas_de_arrasto` e `fx_exigido_traseira` com a réplica de grade, `n_alfa` da grade), a mini-grade da 19 (3 linhas, mesmas colunas),
o K da 19 e os ângulos (K em °/g <= 1e-6, ângulos 1e-8), o resumo (S, S2, resolução, a_y limite, C_N, veredito, motivo, limitações, tempo
de volta, pior origem, situação, `ok`), a 24_CURVA (R usado, motivo e θ contra `skidpad.raio` e `equilibrio.angulos_velocidade`), a
pior origem do R (E173 = a pior entre a das 16 e a do R) e o 14_DASHBOARD B48 (texto esperado escrito aqui), nos dois sentidos de curva
e nos três modos do R; mais os casos do conselho (status, `ok` e motivo iguais aos de `motivo_das_entradas(...,
verificacoes=VERIFICACOES_V43)`): LOOSE_PICO e PUSH_PICO (força acima do pico), dianteira descolada (C-G6), geometria, chaves, modo
inválido, diâmetros, R_in' <= L, Manual vazio, fator 0,5, a faixa 4/3 (veredito que muda da V4.2 para a V4.3 e eixo saturado numa grade só), a aba 20 (as linhas
extras leem a situação da 24_CURVA: C-B11) e o aviso do 14_DASHBOARD B48 (padrão, h2v = 0, chave inválida).
Valores de teste só nas cópias. Mudanças de valor da V4.2 -> V4.3 com o padrão 1 (h2v = h9v = 1) são intencionais (EDR-066) e listadas no log
do 004; nenhuma tolerância foi afrouxada.

TC-WB43-005 (barra de fórmulas): abre a V4.3 pelo Excel (COM, só leitura, em cópia) e confere, em 16_EQUILIBRIO B84 e B9 e em 17_EQ_PAR
BP24, `HasFormula` True e `FormulaHidden` False, e que a aba não tem proteção (`ProtectContents` False).
"Passou" = a planilha reproduz o Python e a V4.2; não é validação física.
"""
import dataclasses, math, os, sys, tempfile, time
from types import SimpleNamespace
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
from collections import defaultdict
from pathlib import Path
import openpyxl
import aba_curva as ac
import aba_equilibrio as ae
import caso_planilha as cp
import dados_planilha as dp
import equilibrio as eq
import equilibrio_linear as el
import gerar_v4_3 as g43
import origens
import raizes
import recalculo_planilha as rc
import skidpad
from suspension_model import G

MOTOR, DETALHE = rc.escolher()
if MOTOR is None:
    print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({DETALHE})"); sys.exit(3)
print(f"MOTOR: {MOTOR} ({DETALHE})")
_RAIZ = Path(__file__).resolve().parent.parent
TIR = _RAIZ / "data" / "Hoosier_R25B_13x7_TTC_provisional.tir"
TOL_REL = 1e-9
TOL_K = 1e-6        # °/g
TOL_ANG = 1e-8      # relativo a max(|α|, 1e-3)
TOL_ANG_ABS = 5e-11  # rad: piso absoluto (resolução do Newton da planilha e da bisseção do Python em α ~ 1e-3; só vale junto do relativo)
FORMULAS = 146373   # V4.3 (tools/comparar_planilhas.FORMULAS_ESPERADAS_V43)
SUB = set(filter(None, os.environ.get("DDS_CASOS", "").split(",")))   # vazio = tudo
results = []
DIF_MAX = [0.0, ""]   # maior |a − b|/escala visto (para o log: diferença entre motores é relatada, não ajustada)
ENT = ae.NOME_ENT
N24 = ac.NOME24
N_ORG24 = "org_24_r_manual"


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def perto(a, b, escala=None, onde="") -> bool:
    """|a − b| <= TOL_REL·escala (escala padrão: max(|a|, |b|)); a da planilha, b do Python."""
    if not (num(a) and num(b)):
        return False
    e = max(abs(a), abs(b)) if escala is None else escala
    if e > 0 and abs(a - b) / e > DIF_MAX[0]:
        DIF_MAX[:] = [abs(a - b) / e, onde]
    return a == b or abs(a - b) <= TOL_REL * e


def valor(wb, nome):
    aba, cel = ae._destino(wb, nome)
    return wb[aba][cel].value


def recalcular(caminho: Path) -> tuple[dict, float]:
    t0 = time.perf_counter()
    if MOTOR == "excel":
        rc._excel_recalc(str(caminho.resolve()), 1800)
    else:
        rc._libreoffice(str(caminho.resolve()), 1800)
    t_motor = time.perf_counter() - t0
    return resumo_tolerante(str(caminho.resolve())), t_motor


# Fórmulas da V4.3 que dão "" (R vazio, diâmetro inválido…): o openpyxl lê o texto vazio como None, e rc._resumo trata isso como
# "fórmula não recalculada". Aqui só as células da 24_CURVA e a B9 da 16 podem ficar sem valor; qualquer outra continua erro.
SEM_VALOR_OK = {(ae.ABA16, "B9")}


def resumo_tolerante(caminho: str) -> dict:
    """`rc._resumo`, aceitando sem valor só as células de SEM_VALOR_OK e da 24_CURVA (fórmulas que devolvem "")."""
    try:
        return rc._resumo(caminho)
    except RuntimeError as e:
        if "sem valor" not in str(e):
            raise
    wbf = openpyxl.load_workbook(caminho)
    wbv = openpyxl.load_workbook(caminho, data_only=True)
    n, sem, erros = 0, [], {}
    try:
        for ws in wbf.worksheets:
            for lin in ws.iter_rows():
                for c in lin:
                    v = c.value.text if hasattr(c.value, "text") else c.value
                    if isinstance(v, str) and v.startswith("="):
                        n += 1
                        val = wbv[ws.title][c.coordinate].value
                        if val is None:
                            sem.append((ws.title, c.coordinate))
                        elif isinstance(val, str) and any(x in val for x in rc.ERROS):
                            erros.setdefault(val, []).append(f"{ws.title}!{c.coordinate}")
    finally:
        wbf.close(); wbv.close()
    ruins = [x for x in sem if x[0] != ac.ABA24 and x not in SEM_VALOR_OK]
    if ruins:
        raise RuntimeError(f"{len(ruins)} fórmula(s) sem valor depois do recálculo: {ruins[:5]}")
    return {"status": "success" if not erros else "errors_found", "total_errors": sum(len(v) for v in erros.values()),
            "error_summary": {e: {"count": len(l), "locations": l[:100]} for e, l in erros.items()}, "total_formulas": n,
            "vazias": sem}


def copia42(tmp: Path, alteracoes: dict, nome: str) -> Path:
    """A V4.2 da tag v4.2 (extraída em `tmp`) + `alteracoes` (nome -> valor; None esvazia), gravada em `tmp/nome`."""
    origem = g43.extrair_v42(tmp)
    wb = openpyxl.load_workbook(origem)
    try:
        for n, v in alteracoes.items():
            aba, cel = ae._destino(wb, n)
            wb[aba][cel].value = v
        wb.calculation.fullCalcOnLoad = True
        wb.save(tmp / nome)
    finally:
        wb.close()
    return tmp / nome


# --- Casos (valores de TESTE, só nas cópias; os da V4.1 de tests/test_workbook_v4_1.py) ---
C2 = {"ent_05_rear_track_t_r": 1.277, "ent_05_fracao_de_peso_no_eixo_dianteiro_f": 0.5,
      "ent_05_massa_nao_suspensa_traseira": 15, "ent_06_spring_rate_traseiro": 49909.24,
      "ent_06_k_arb_traseiro": 5012.32, "ent_06_roll_center_traseiro_rh_estatico": 0.0675,
      "ent_07_camber_gain_traseiro_dcamber_dz": -0.6, "ent_10_camber_gama_projeto_topo_para_fora_d": -1.5,
      "ent_10_camber_gama_projeto_topo_para_fora_e": -1.5, "ent_08_aero_balance_fracao_dianteira": 0.5,
      "ent_10_lmuy": 0.45}   # t_R = t_F, a = b, massas, molas, MR, barras, RC, camber e aero iguais nos eixos
C3 = {**C2, "ent_06_k_arb_dianteiro": 5012.32 * 3}
C3b = {**C2, "ent_06_k_arb_traseiro": 5012.32 * 3}
R_TESTE = 8.0
H9 = {ENT["rho"]: 1.2, ENT["cda"]: 1.0, ENT["crr"]: 0.015}
H239 = {ENT["h2"]: 1, ENT["h3"]: 1, ENT["h9"]: 1, **H9}
C4 = {**C3, ENT["h2"]: 1, ENT["h3"]: 1, ENT["cg"]: 0.010, ENT["h7"]: 1, ENT["sentido"]: "Direita",
      ENT["h8"]: 1, ENT["rho"]: 1.2, ENT["cza"]: 2.0, "ent_08_downforce_total": 0, ENT["h9"]: 1, ENT["cda"]: 1.0,
      ENT["crr"]: 0.015, ENT["toeFL"]: 0.25, ENT["toeFR"]: 0.10,
      "ent_10_camber_gama_projeto_topo_para_fora_b": -1.5, "ent_10_camber_gama_projeto_topo_para_fora_c": -1.0}
C4b = {**C4, "ent_07_angulo_da_roda_dianteira_interna_deltai": 22}
MODOS = {"Linha central": "linha_central", "Rente aos cones": "rente_aos_cones", "Manual": "manual"}
GRANDEZAS_SKP = {"L": "L", "b": "b", "tF": "tF", "tR": "tR"}


def v43_do_caso(alt42: dict, modo="Manual", h2v=0, h9v=0, org=None) -> dict:
    """Alterações da V4.3 equivalentes às da V4.2 `alt42` (R -> R manual, modo, chaves de forma e, com `org`, as Origens
    da 24_CURVA)."""
    alt = {n: v for n, v in alt42.items() if n not in (ENT["R"], "org_16_raio_do_skidpad_r")}
    alt[N24["modo"]] = modo
    alt[N24["h2v"]], alt[N24["h9v"]] = h2v, h9v
    if ENT["R"] in alt42:
        alt[N24["rman"]] = alt42[ENT["R"]]
    if "org_16_raio_do_skidpad_r" in alt42:
        alt[N_ORG24] = alt42["org_16_raio_do_skidpad_r"]
    if org is not None:
        for n in sorted(org):
            alt.setdefault(n, org[n])
    return alt


def nomes_org(wb_ref) -> list[str]:
    return sorted(n for n in dp.ler_por_nome(wb_ref) if n.startswith("org_"))


# =====================================================================================================================
# TC-WB43-003
# =====================================================================================================================
def fecho(seeds, rev) -> set:
    """Fecho transitivo dos dependentes de `seeds` (inclusive eles) no grafo reverso `rev` (célula -> dependentes)."""
    visto, fila = set(seeds), list(seeds)
    while fila:
        no = fila.pop()
        for d in rev.get(no, ()):
            if d not in visto:
                visto.add(d)
                fila.append(d)
    return visto


def grafo_reverso(wb_formulas) -> dict:
    """célula -> conjunto de células-fórmula que a leem, de TODAS as fórmulas (nomes definidos expandidos)."""
    g = raizes.Grafo(wb_formulas)
    rev = defaultdict(set)
    for no, f in g.formulas.items():
        for ref in raizes.referencias(f, no[0], [], g.nomes):
            rev[ref].add(no)
    return rev


def resumo_por_aba(celulas) -> str:
    por = defaultdict(list)
    for a, c in celulas:
        por[a].append(c)
    return "; ".join(f"{a}: {len(cs)} ({', '.join(sorted(cs, key=lambda x: (raizes.linha(x), x))[:12])}"
                     f"{'…' if len(cs) > 12 else ''})" for a, cs in sorted(por.items()))


def comparar_v42_v43(nome, c42, c43, fora: set, intencional: set, constantes: list, falhas: list, mudancas: list):
    """Compara os valores recalculados de c42 (V4.2) e c43 (V4.3) em toda célula da V4.2. `fora`: excluídas (decisão B);
    `intencional`: células que podem mudar neste caso (C-B4, C-B7, C-B7b) e que vão a `mudancas`."""
    v42, v43 = openpyxl.load_workbook(c42, data_only=True), openpyxl.load_workbook(c43, data_only=True)
    f42, f43 = openpyxl.load_workbook(c42), openpyxl.load_workbook(c43)
    n_comp = n_const = 0
    try:
        for ws in v42.worksheets:
            ws43, wf42, wf43 = v43[ws.title], f42[ws.title], f43[ws.title]
            for lin in ws.iter_rows():
                for c in lin:
                    a = c.value
                    if a is None or (ws.title, c.coordinate) in fora:
                        continue
                    t42, t43 = wf42[c.coordinate].value, wf43[c.coordinate].value
                    e_f42 = isinstance(t42, str) and t42.startswith("=")
                    e_f43 = isinstance(t43, str) and t43.startswith("=")
                    if not e_f42 and not e_f43 and t42 != t43:      # texto constante que o gerador reescreve
                        constantes.append((ws.title, c.coordinate))
                        n_const += 1
                        continue
                    b = ws43[c.coordinate].value
                    n_comp += 1
                    if num(a) and num(b):
                        igual = a == b or abs(a - b) <= TOL_REL * max(abs(a), abs(b))
                    else:
                        igual = a == b
                    if not igual:
                        if (ws.title, c.coordinate) in intencional:
                            mudancas.append((nome, ws.title, c.coordinate, a, b))
                        else:
                            falhas.append(f"{nome} {ws.title}!{c.coordinate}: V4.2 {a!r} V4.3 {b!r}")
    finally:
        for w in (v42, v43, f42, f43):
            w.close()
    return n_comp, n_const


def tc_wb43_003(tmp: Path) -> None:
    falhas, notas, tempos = [], [], []
    if SUB and "TC003" not in SUB:
        return
    ref42 = g43.extrair_v42(tmp)
    # --- células excluídas (decisão B) e o fecho transitivo, do grafo de fórmulas da V4.3 ---
    t0 = time.perf_counter()
    wb_alt = openpyxl.load_workbook(ref42)
    try:
        alt = ac.alteracoes_v4_3(wb_alt, ac.mapa_v43())
    finally:
        wb_alt.close()
    sementes20 = [(a["aba"], a["cel"]) for a in alt if a["aba"] == ae.ABA20]
    cop_formulas = g43.copia_v43(tmp, {}, "V4_3_formulas.xlsx")
    wbf = openpyxl.load_workbook(cop_formulas)
    try:
        rev = grafo_reverso(wbf)
        n_formulas = sum(1 for ws in wbf.worksheets for lin in ws.iter_rows() for c in lin
                         if isinstance(c.value, str) and c.value.startswith("="))
    finally:
        wbf.close()
    sementes = [(ae.ABA16, "B137"), (ae.ABA16, "B138"), (ae.ABA16, "B139"), *sementes20]
    fora = fecho(sementes, rev)
    # as células que o C-B4, C-B7 e C-B7b mudam (e o que depende delas): só no caso do R manual vazio
    intencional = fecho([(ae.ABA16, "B65"), (ae.ABA16, "B173"), (ae.ABA16, "E173")], rev) - fora
    print(f"  grafo de dependências ({n_formulas} fórmulas) em {time.perf_counter() - t0:.0f} s")
    print(f"  EXCLUÍDAS (decisão B: 16 B137 a B139 e as linhas dif da 20_EQ_TROCA {sorted(c for a, c in sementes20)}, mais o "
          f"fecho transitivo): {len(fora)} células: {resumo_por_aba(sorted(fora))}")
    print(f"  mudança intencional permitida no caso MANUAL_VAZIO (C-B4, C-B7, C-B7b: 16 B65, B173, E173 e o que depende): "
          f"{len(intencional)} células: {resumo_por_aba(sorted(intencional))}")
    org42 = nomes_org(ref42)
    todos_tx = {n: origens.OUTRO_CARRO for n in org42}
    casos = [("C1_H", {**H239, ENT["R"]: R_TESTE}, False),
             ("C4b", {**C4b, ENT["R"]: R_TESTE}, False),
             ("ORG_TX_H", {**C3, **H239, ENT["R"]: R_TESTE, **todos_tx}, False),
             ("MANUAL_VAZIO", {**C3}, True)]
    mudancas, constantes, n_cmp = [], [], []
    for nome, alt42, vazio in casos:
        if SUB and "TC003" not in SUB:
            break
        c42 = copia42(tmp, alt42, f"V4_2_{nome}.xlsx")
        org43 = {n: origens.OUTRO_CARRO for n in nomes_org(cop_formulas) if n.startswith("org_24_")} \
            if nome == "ORG_TX_H" else None
        c43 = g43.copia_v43(tmp, v43_do_caso(alt42, org=org43), f"V4_3_{nome}.xlsx")
        i42, t = recalcular(c42); tempos.append(t)
        i43, t = recalcular(c43); tempos.append(t)
        if i42["total_errors"] or i42["total_formulas"] != 117627:
            falhas.append(f"{nome} V4.2: {i42['total_errors']} erro(s) {i42['error_summary']}, {i42['total_formulas']} fórmulas")
        if i43["total_errors"] or i43["total_formulas"] != FORMULAS:
            falhas.append(f"{nome} V4.3: {i43['total_errors']} erro(s) {i43['error_summary']}, {i43['total_formulas']} fórmulas")
        n, n_const = comparar_v42_v43(nome, c42, c43, fora, intencional if vazio else set(), constantes, falhas, mudancas)
        n_cmp.append((nome, n, n_const))
        print(f"  {nome}: V4.2 {tempos[-2]:.0f} s, V4.3 {tempos[-1]:.0f} s; {n} células comparadas, {n_const} de texto constante "
              f"reescrito pelo gerador")
    for m in mudancas:
        print(f"  MUDANÇA INTENCIONAL (C-B4/C-B7/C-B7b) {m[0]} {m[1]}!{m[2]}: V4.2 {m[3]!r} -> V4.3 {m[4]!r}")
    consts = sorted(set(constantes))
    print(f"  texto constante reescrito (fora da comparação, {len(consts)} células): {resumo_por_aba(consts)}")
    for f in falhas[:10]:
        print("   FALHA:", f)
    if SUB and "TC003" not in SUB:
        return
    # o B173 e o E173 estão dentro do fecho excluído (dependem de B139); no MANUAL_VAZIO a mudança é conferida direto
    v42m = openpyxl.load_workbook(tmp / "V4_2_MANUAL_VAZIO.xlsx", data_only=True)[ae.ABA16]
    v43m = openpyxl.load_workbook(tmp / "V4_3_MANUAL_VAZIO.xlsx", data_only=True)[ae.ABA16]
    for cel in ("B65", "B173", "E173"):
        print(f"  MANUAL_VAZIO 16 {cel}: V4.2 {v42m[cel].value!r} -> V4.3 {v43m[cel].value!r}")
    mot = " (R manual vazio: a confirmar)"
    if not (isinstance(v42m["B173"].value, str) and v43m["B173"].value == v42m["B173"].value + mot):
        falhas.append(f"MANUAL_VAZIO: B173 {v42m['B173'].value!r} -> {v43m['B173'].value!r}, esperado o texto da V4.2 + {mot!r} (C-B7)")
    if v43m["B65"].value != v42m["B65"].value:
        falhas.append(f"MANUAL_VAZIO: B65 {v42m['B65'].value!r} -> {v43m['B65'].value!r} (h2 = h3 = h8 = h9 = 0: sem mudança)")
    check("TC-WB43-003: V4.3 com h2v = h9v = 0, modo Manual e R manual = o B9 da V4.2 == V4.2, recalculadas no Excel, em todas as "
          "células da V4.2 (rel. <= 1e-9) fora das excluídas pela decisão B (16 B137 a B139, as linhas dif da 20_EQ_TROCA e o fecho "
          "transitivo no grafo de fórmulas; lista no log) e dos textos constantes reescritos; casos C1_H, C4b, ORG_TX_H e MANUAL_VAZIO "
          "(só o texto do B173 pelo motivo do R manual vazio e o E173)",
          not falhas, f"{len(falhas)} divergência(s): {falhas[:6]}; {len(fora)} excluídas; comparações {n_cmp}; "
          f"{len(mudancas)} mudança(s) intencional(is); recálculo (s) {[round(t) for t in tempos]}")


# =====================================================================================================================
# TC-WB43-004
# =====================================================================================================================
VEIC = {k: cp.ENTRADAS_CASO[k] for k in ("L", "b", "tF", "tR")}
SEM_OBS = "-"
BASE = {k: v for k, v in C4b.items() if k != ENT["R"]}      # h2, h3, h7, h8, h9, sentido Direita, toe e camber de teste
BASE_SEM_DELTA = {k: v for k, v in BASE.items() if k != "ent_07_angulo_da_roda_dianteira_interna_deltai"}   # % Ackermann do 07 = 0
ESQUERDA = {ENT["sentido"]: "Esquerda"}
MAN8 = {N24["modo"]: "Manual", N24["rman"]: R_TESTE}


def esperado_R(modo, dint, dext, w, rman, veic) -> tuple:
    """(R, motivo) esperados da 24_CURVA (B20 e B21): `skidpad.raio` e os textos fixos do catálogo (C-A14 e C-A15)."""
    if modo not in MODOS:
        return None, skidpad.MOTIVO_MODO_INVALIDO
    m = MODOS[modo]
    if m == "manual":
        return skidpad.raio("manual", d_int=dint, d_ext=dext, L=veic["L"], b=veic["b"], t_f=veic["tF"], t_r=veic["tR"],
                            meia_largura=w, r_manual=rman if num(rman) else None)
    if not (num(dint) and num(dext) and dint > 0 and dext > dint):
        return None, skidpad.MOTIVO_DIAMETROS
    return skidpad.raio(m, d_int=dint, d_ext=dext, L=veic["L"], b=veic["b"], t_f=veic["tF"],
                        t_r=veic["tR"] if num(veic["tR"]) else None, meia_largura=w if num(w) else None, r_manual=None)


def fmt3(x) -> str:
    return f"{x:.3f}".replace(".", ",")


def texto_b48(r24, R, modo, sit24, h2v, h9v) -> str:
    """O texto esperado do 14_DASHBOARD B48 (catálogo C-D1), escrito à parte da fórmula."""
    if sit24 != "-":
        ini = "24_CURVA: " + sit24
    elif h2v == 1 and h9v == 1:
        ini = ("V4.3: Ackermann com o centro da curva no eixo traseiro e Fx por arrasto induzido (mudou em relação à V4.2; "
               "para voltar à V4.2, h2v = 0 e h9v = 0 em 24_CURVA B9 e B10)")
    else:
        ini = f"forma da V4.2 em uso (h2v = {h2v}, h9v = {h9v}): resultado não comparável com a V4.3 padrão"
    if num(R):
        fim = fmt3(R) + " m (" + ("manual" if modo == "Manual" else modo.lower() + ", diâmetros do regulamento FSAE 2026 D.10.1.1") + ")"
    else:
        fim = r24["motivo_r"]
    return f"{ini}. R = {fim}"


def pior_r_independente(wbf, modo) -> str:
    """Pior origem esperada do R por modo, de rótulos (a lista Origens da V4.2), sem usar a fórmula `_formula_pior`."""
    lista = origens.ORIGENS_V42
    e = lambda chave: wbf[ac.ABA24][f"E{ac.LINHA24[chave]}"].value
    if modo == "Manual":
        rot = [e("rman")]
    elif modo in ("Linha central", "Rente aos cones"):
        rot = [e("dint"), e("dext")]
        if modo == "Rente aos cones":
            g = raizes.Grafo(wbf)
            rot += [e("w")]
            for k in ("b", "L", "tF", "tR"):
                for a, c in g.celulas_origem(ae._destino(wbf, ae.V40[k])):
                    rot.append(wbf[a][c].value)
    else:
        return origens.CONF
    return lista[max(lista.index(r) if r in lista else len(lista) - 1 for r in rot)]


def comparar_grade(ws, linhas, n_alfa, pedida, caso, formas, falhas, rotulo, flags):
    """Uma grade (17, 18 ou a mini-grade da 19): `linhas` = [(linha da planilha, a_y, fz|None, cap_f, cap_r, req_f, req_r)].
    Compara o que a V4.2 já comparava (Fz, γ, capacidade, motivo, folga) e as colunas novas da V4.3 (aF, aR, fxr)."""
    cl = ae._colunas(n_alfa, pedida)
    cn = ae.colunas_v43(n_alfa, pedida)
    h9, h9v = eq.tracao_ativa(caso), formas.fx == "v43"
    for k, (r, ay, fz, cap_f, cap_r, req_f, req_r) in enumerate(linhas):
        v = lambda n: ws[f"{cl[n]}{r}"].value
        if fz is not None:
            gam = eq.camber(caso, ay)
            for c in eq.CANTOS:
                if not perto(v("Fz_" + c), fz[c], onde=f"{rotulo} Fz"):
                    falhas.append(f"{rotulo} k={k} Fz_{c}: planilha {v('Fz_' + c)!r} Python {fz[c]!r}")
                if not perto(v("gam_" + c), gam[c], max(abs(gam[c]), 1e-3), f"{rotulo} γ"):
                    falhas.append(f"{rotulo} k={k} γ_{c}: planilha {v('gam_' + c)!r} Python {gam[c]!r}")
        for e, cap, req in (("F", cap_f, req_f), ("R", cap_r, req_r)):
            val, mot = v("cap_" + e), v("mot_" + e)
            if (cap.motivo or "-") != mot:
                falhas.append(f"{rotulo} k={k} motivo {e}: planilha {mot!r} Python {cap.motivo!r}")
            if cap.fy_max_N is None:
                if val != "N/A":
                    falhas.append(f"{rotulo} k={k} cap {e}: planilha {val!r}, Python None")
                continue
            if not perto(val, cap.fy_max_N, onde=f"{rotulo} cap"):
                falhas.append(f"{rotulo} k={k} cap {e}: planilha {val!r} Python {cap.fy_max_N!r}")
            if pedida and req is not None:
                f_sh = v("folga_" + e)
                if cap.motivo is None:
                    if not perto(f_sh, cap.fy_max_N - req, max(abs(cap.fy_max_N), abs(req)), f"{rotulo} folga"):
                        falhas.append(f"{rotulo} k={k} folga {e}: planilha {f_sh!r} Python {cap.fy_max_N - req!r}")
                elif f_sh != "N/A":
                    falhas.append(f"{rotulo} k={k} folga {e}: planilha {f_sh!r}, Python sem folga ({cap.motivo})")
        # colunas novas
        aF, aR, fxs = ws[f"{cn['aF']}{r}"].value, ws[f"{cn['aR']}{r}"].value, v("fxr")
        fx_py = eq.fx_exigido_traseira(caso, ay, formas=formas, n_alfa=n_alfa)
        if h9 and h9v:
            al = eq.alfas_de_arrasto(caso, ay, formas=formas, n_alfa=n_alfa)
            if isinstance(al, str):
                flags["semF"] += 1
                sem_ok = (aF == "semF") if al == eq.MSG_FX_SEM_FRENTE else (aR == "semF")
                if not (sem_ok and fxs == "semF" and fx_py == al):
                    falhas.append(f"{rotulo} k={k} sem curva ({al}): aF {aF!r} aR {aR!r} fxr {fxs!r} Python {fx_py!r}")
            else:
                flags["alfa"] += 1
                if not (perto(aF, al[0], max(abs(al[0]), 1e-9), f"{rotulo} aF") and perto(aR, al[1], max(abs(al[1]), 1e-9),
                                                                                        f"{rotulo} aR")):
                    falhas.append(f"{rotulo} k={k} aF/aR: planilha {aF!r}/{aR!r} Python {al[0]!r}/{al[1]!r}")
                if not perto(fxs, fx_py, max(abs(fx_py), 1e-9), f"{rotulo} fxr"):
                    falhas.append(f"{rotulo} k={k} fxr: planilha {fxs!r} Python {fx_py!r}")
                cap0 = ws[f"{cn['cap0_R']}{r}"].value
                if req_r is not None and num(cap0) and req_r >= cap0:
                    flags["pico_R"] += 1
                if req_f is not None and cap_f.fy_max_N is not None and req_f >= cap_f.fy_max_N and cap_f.motivo is None:
                    flags["pico_F"] += 1
        else:
            if not (aF == "-" and aR == "-" and ws[f"{cn['cap0_R']}{r}"].value == "-"):
                falhas.append(f"{rotulo} k={k} colunas novas sem h9/h9v: aF {aF!r} aR {aR!r}")
            fx0 = fx_py if num(fx_py) else None
            if fx0 is None or not perto(fxs, fx0, max(abs(fx0), 1e-9), f"{rotulo} fxr v42") and not (fxs == fx0 == 0):
                falhas.append(f"{rotulo} k={k} fxr (forma V4.2 ou h9 desligada): planilha {fxs!r} Python {fx_py!r}")


def comparar_k43(nome, wb, caso, formas, falhas):
    """O K da 19 (parcelas e K tangente por linha, K em °/g) e os ângulos do Newton contra `equilibrio_linear` com as formas
    da planilha (TC-WB41-005 com `formas=`)."""
    lin = [{q: valor(wb, ae.NOME19[(q, k)]) for q in ae.QTD19} for k in range(ae.N_LIN19)]
    tab = el.tabela_linear(caso, formas=formas)
    if len(tab) != ae.N_LIN19:
        falhas.append(f"{nome}: tabela_linear com {len(tab)} linhas, planilha com {ae.N_LIN19}")
        return
    for k, (ln, row) in enumerate(zip(lin, tab)):
        p = row["parcelas"]
        for q, py in (("kP", p.k_pneus), ("kT", p.k_transferencia), ("kD", p.k_deslocamento), ("kC", p.k_camber),
                      ("kRS", p.k_roll_steer), ("kTot", p.k_total), ("kI", row["k_inclinacao"])):
            if py is None:
                ok = ln[q] == "N/A"
            else:
                ok = num(ln[q]) and abs(el.para_graus_por_g(ln[q]) - el.para_graus_por_g(py)) <= TOL_K
            if not ok:
                falhas.append(f"{nome} 19 linha {k} {q}: planilha {ln[q]!r} Python {py!r}")
        if ln["mot"] != (p.motivo or "-"):
            falhas.append(f"{nome} 19 linha {k} motivo: planilha {ln['mot']!r} Python {p.motivo!r}")
    ws19 = wb[ae.ABA19]
    for p_i, ay in enumerate(ae.PONTOS19_AY):
        py = el.angulos_necessarios(caso, ay, formas=formas)
        sh = (ws19[ae.celula_aux19("ang_F", p_i)].value, ws19[ae.celula_aux19("ang_R", p_i)].value)
        if py is None:
            if all(num(x) for x in sh):
                falhas.append(f"{nome} 19 ponto {p_i}: Python sem ângulos, planilha {sh!r}")
            continue
        for e, a_sh, a_py in (("F", sh[0], py[0]), ("R", sh[1], py[1])):
            if not num(a_sh) or (abs(a_sh - a_py) / max(abs(a_py), 1e-3) > TOL_ANG and abs(a_sh - a_py) > TOL_ANG_ABS):
                falhas.append(f"{nome} 19 ponto {p_i} α_{e}: planilha {a_sh!r} Python {a_py!r}")


def caso_com_karb(copia, fator, passo1):
    """caso_da_planilha_v43 com o K_ARB dianteiro × fator (como o TC-WB41-006): troca o `_cfg` só durante a chamada."""
    orig = cp._cfg
    cp._cfg = lambda x: orig({**x, "KarbF": x["KarbF"] * fator})
    try:
        return cp.caso_da_planilha_v43(copia, TIR, passo1=passo1)
    finally:
        cp._cfg = orig


def comparar_troca43(nome, wb, copia, status, falhas):
    """20_EQ_TROCA (as linhas extras ×0,5; 0,75; 1,5; 2 leem a situação da 24_CURVA, C-B11; a ×1 é a da 16) contra
    `analise_par` com `formas` e o fator da faixa, caso a caso."""
    cols = {0: "B", 1: "C", 3: "D", 4: "E"}
    ws = wb[ae.ABA20]
    for j, f in enumerate(ae.FATORES20):
        s = {q: valor(wb, ae.NOME20[(q, j)]) for q in ("sf", "sr", "aylim", "resol", "ver", "mot")}
        onde = f"{nome} 20 linha {j} (×{f:g})"
        if j in cols:
            st_sh = ws[f"{cols[j]}24"].value
            if status != "OK" and st_sh != status:
                falhas.append(f"{onde}: situação da linha {st_sh!r}, esperado {status!r} (a das entradas da 16/24)")
            if status == "OK" and st_sh != "OK":
                falhas.append(f"{onde}: situação da linha {st_sh!r}, esperado OK")
            if ws[f"{cols[j]}25"].value != (1 if st_sh == "OK" else 0):
                falhas.append(f"{onde}: linha válida {ws[cols[j] + '25'].value!r} com situação {st_sh!r}")
        try:
            caso, formas = caso_com_karb(copia, f, False)
            fator = cp.fator_neutro_da_planilha(copia)
        except ValueError as e:
            if not (s["ver"] == eq.NA and s["mot"] == str(e)):
                falhas.append(f"{onde}: Python N/A ({e}); planilha veredito {s['ver']!r} motivo {s['mot']!r}")
            continue
        r = eq.analise_par(caso, formas=formas, fator_neutro=fator)
        for q, py in (("sf", r.ay_sat_f), ("sr", r.ay_sat_r), ("aylim", r.ay_lim), ("resol", r.resolucao_ms2)):
            if not (s[q] == "N/A" if py is None else perto(s[q], py, onde=f"{onde} {q}")):
                falhas.append(f"{onde} {q}: planilha {s[q]!r} Python {py!r}")
        if s["ver"] != r.veredito or s["mot"] != (r.motivo or "-"):
            falhas.append(f"{onde} veredito/motivo: planilha {s['ver']!r}/{s['mot']!r} Python {r.veredito!r}/{r.motivo!r}")


def comparar43(nome, copia, falhas, flags=None, com_k=True, com_troca=False, b48=None, esperado_status=None):
    """Compara a cópia recalculada da V4.3 com o Python (caso lido por `caso_da_planilha_v43` + `analise_par(formas=)`).
    Devolve (resumo, dict com res/caso/formas/r16/r24)."""
    flags = flags if flags is not None else defaultdict(int)
    wb = openpyxl.load_workbook(copia, data_only=True)
    wbf = openpyxl.load_workbook(copia)
    try:
        r16 = {k: valor(wb, n) for k, n in ae.NOME16.items()}
        r24 = {k: valor(wb, n) for k, n in N24.items()}
        d14 = wb["14_DASHBOARD"]["B48"].value
        e173 = wb[ae.ABA16]["E173"].value
        e9 = wb[ae.ABA16]["E9"].value
        # --- 24_CURVA: R usado, motivo, θ e geometria contra skidpad e equilibrio ---
        veic = {k: valor(wb, n) for k, n in VEIC.items()}
        R_py, mot_py = esperado_R(r24["modo"], r24["dint"], r24["dext"], r24["w"], r24["rman"], veic)
        R_sh = r16["R"] if "R" in r16 else valor(wb, ENT["R"])
        R_sh = valor(wb, ENT["R"])
        if R_py is None:
            if R_sh not in ("", None) or r24["rusado"] not in ("", None):
                falhas.append(f"{nome} R usado: planilha {r24['rusado']!r}/{R_sh!r}, esperado vazio ({mot_py})")
        elif not (perto(r24["rusado"], R_py, onde=f"{nome} R") and perto(R_sh, R_py, onde=f"{nome} R 16 B9")):
            falhas.append(f"{nome} R usado: planilha {r24['rusado']!r}/{R_sh!r} Python {R_py!r} ({r24['modo']})")
        if r24["motivo_r"] != (mot_py or "-"):
            falhas.append(f"{nome} motivo do R: planilha {r24['motivo_r']!r} Python {mot_py!r}")
        b, tF, L = veic["b"], veic["tF"], veic["L"]
        if num(R_sh) and num(b):
            rcc_py = "R ≤ b: a confirmar" if R_sh <= b else math.sqrt(R_sh ** 2 - b ** 2)
        else:
            rcc_py = "-"
        if not (r24["rcc"] == rcc_py if isinstance(rcc_py, str) else perto(r24["rcc"], rcc_py, onde=f"{nome} R_c")):
            falhas.append(f"{nome} R_c: planilha {r24['rcc']!r} Python {rcc_py!r}")
        h2v, h9v = r24["h2v"], r24["h9v"]
        if h2v == 1 and num(rcc_py) and num(tF) and rcc_py > tF / 2:
            th = (math.atan(L / (rcc_py - tF / 2)), math.atan(L / (rcc_py + tF / 2)))
            ok_th = perto(r24["thFL"], th[0], onde=f"{nome} θFL") and perto(r24["thFR"], th[1], onde=f"{nome} θFR") \
                and perto(r24["thm"], (th[0] + th[1]) / 2, onde=f"{nome} θm")
        else:
            ok_th = (r24["thFL"], r24["thFR"], r24["thm"]) == ("-", "-", "-")
        if not ok_th:
            falhas.append(f"{nome} θ: planilha {r24['thFL']!r}/{r24['thFR']!r}/{r24['thm']!r} (h2v {h2v!r}, R_c {rcc_py!r})")
        h2 = valor(wb, ENT["h2"])
        geo = ac and (eq.MSG_GEOMETRIA if (h2 == 1 and h2v == 1 and num(R_sh) and num(b) and num(tF)
                                           and (R_sh <= b or math.sqrt(max(R_sh ** 2 - b ** 2, 0)) <= tF / 2)) else "-")
        if r24["vgeo"] != geo:
            falhas.append(f"{nome} geometria (B28): planilha {r24['vgeo']!r}, esperado {geo!r}")
        # --- pior origem do R e E173 ---
        pr = pior_r_independente(wbf, r24["modo"])
        if r24["pior_r"] != pr or e9 != pr:
            falhas.append(f"{nome} pior origem do R: 24 B23 {r24['pior_r']!r}, 16 E9 {e9!r}, esperado {pr!r}")
        chaves = {k: valor(wb, ENT[k]) for k in ("h2", "h3", "h7", "h8", "h9")}
        termos = ae.termos_pior_origem(wbf, False)
        pior16 = ae.pior_origem_de_valores(termos, lambda a, c: wb[a][c].value, chaves, lista=origens.ORIGENS_V42)
        if r16["pior"] != pior16:
            falhas.append(f"{nome} pior origem da 16: planilha {r16['pior']!r}, independente {pior16!r}")
        lista = origens.ORIGENS_V42
        e173_esp = lista[max(lista.index(r16["pior"]), lista.index(pr))]
        if e173 != e173_esp:
            falhas.append(f"{nome} E173 (pior origem do tempo de volta): planilha {e173!r}, esperado {e173_esp!r}")
        # --- caso e análise de par ---
        try:
            caso, formas = cp.caso_da_planilha_v43(copia, TIR, passo1=False)
            fator = cp.fator_neutro_da_planilha(copia)
        except ValueError as e:
            ok = r16["status"] == str(e) and r16["ver"] == eq.NA and r16["mot"] == str(e) and r16["ok"] == 0
            if not ok:
                falhas.append(f"{nome}: Python ValueError({e!s}); planilha situação={r16['status']!r} veredito={r16['ver']!r} "
                              f"motivo={r16['mot']!r} ok={r16['ok']!r}")
            if esperado_status is not None and str(e) != esperado_status:
                falhas.append(f"{nome}: o Python deu {str(e)!r}, esperado {esperado_status!r}")
            if b48 is not None:
                esp48 = texto_b48(r24, R_sh, r24["modo"], r24["sit24"], h2v, h9v)
                if d14 != esp48:
                    falhas.append(f"{nome} 14_DASHBOARD B48: {d14!r}, esperado {esp48!r}")
            if com_troca:
                comparar_troca43(nome, wb, copia, r16["status"], falhas)
            return f"{nome}: N/A pelas entradas ({e})", {"r16": r16, "r24": r24, "erro": str(e), "d14": d14, "wb": None}
        if esperado_status is not None and esperado_status != "OK":
            falhas.append(f"{nome}: o Python aceitou o caso, esperado {esperado_status!r}")
        if r16["status"] != "OK" or r16["ok"] != 1:
            falhas.append(f"{nome}: Python aceitou o caso; planilha situação {r16['status']!r} ok {r16['ok']!r}")
        res = eq.analise_par(caso, formas=formas, fator_neutro=fator)
        fina, sf2, sr2 = eq._varredura(caso, ae.AY_MAX_G, ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1, formas=formas)
        lp = [(ae.PRIMEIRA_LINHA + k, ln.ay_ms2, ln.fz, ln.cap_f, ln.cap_r, ln.req_f, ln.req_r)
              for k, ln in enumerate(res.linhas)]
        lf = [(ae.PRIMEIRA_LINHA + k, ln.ay_ms2, ln.fz, ln.cap_f, ln.cap_r, ln.req_f, ln.req_r) for k, ln in enumerate(fina)]
        comparar_grade(wb[ae.ABA17], lp, ae.N_ALFA, True, caso, formas, falhas, f"{nome} 17", flags)
        comparar_grade(wb[ae.ABA18], lf, 2 * ae.N_ALFA - 1, False, caso, formas, falhas, f"{nome} 18", flags)
        # mini-grade da 19: a_y lido da própria linha; capacidade pelo Python
        ws19, clm = wb[ae.ABA19], ae.CL_MINI
        lm = []
        for j in range(3):
            r = ae.LINHA_MINI19 + j
            ay = ws19[f"{clm['ay']}{r}"].value
            cf = eq.capacidade_eixo(caso, "F", ay, ae.N_ALFA, formas=formas)
            cr = eq.capacidade_eixo(caso, "R", ay, ae.N_ALFA, formas=formas)
            lm.append((r, ay, None, cf, cr, None, None))
        comparar_grade(ws19, lm, ae.N_ALFA, False, caso, formas, falhas, f"{nome} 19-mini", flags)
        # resumo
        pares = [("S_F", res.ay_sat_f), ("S_R", res.ay_sat_r), ("S2_F", sf2.ay_sat), ("S2_R", sr2.ay_sat),
                 ("resol", res.resolucao_ms2), ("aylim", res.ay_lim), ("cn", res.c_n)]
        for k, py in pares:
            if not (r16[k] == "N/A" if py is None else perto(r16[k], py, onde=f"{nome} {k}")):
                falhas.append(f"{nome} {k}: planilha {r16[k]!r} Python {py!r}")
        if r16["ver"] != res.veredito or r16["mot"] != (res.motivo or "-"):
            falhas.append(f"{nome} veredito/motivo: planilha {r16['ver']!r}/{r16['mot']!r} Python {res.veredito!r}/{res.motivo!r}")
        lims = tuple(x for x in (r16[f"lim_{c}_{lim}"] for c in ae.CANTOS for lim in ae.LIMITES) if x != "-")
        if lims != res.limitacoes or r16["lims"] != ("; ".join(res.limitacoes) or "nenhuma"):
            falhas.append(f"{nome} limitações: planilha {lims!r} / {r16['lims']!r} Python {res.limitacoes!r}")
        if num(R_sh) and R_sh > 0 and res.ay_lim is not None:
            t_py = 2 * math.pi * math.sqrt(R_sh / res.ay_lim)
            if not perto(r16["tvolta"], t_py, onde=f"{nome} tvolta"):
                falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r} Python {t_py!r}")
        elif res.ay_lim is not None and R_sh in ("", None):
            esp = f"N/A: raio do skidpad R a confirmar ({r24['motivo_r']})"
            if r16["tvolta"] != esp:
                falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r}, esperado {esp!r}")
        elif not (isinstance(r16["tvolta"], str) and r16["tvolta"].startswith("N/A")):
            falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r}, esperado N/A")
        if b48 is not None:
            esp48 = texto_b48(r24, R_sh, r24["modo"], r24["sit24"], h2v, h9v)
            if d14 != esp48:
                falhas.append(f"{nome} 14_DASHBOARD B48: {d14!r}, esperado {esp48!r}")
        if com_k:
            try:
                caso1, formas1 = cp.caso_da_planilha_v43(copia, TIR, passo1=True)
                comparar_k43(nome, wb, caso1, formas1, falhas)
            except ValueError as e:
                flags["k_sem_roll_steer"] += 1
                print(f"   ({nome}: K da 19 não comparado: {e})")
        if com_troca:
            comparar_troca43(nome, wb, copia, r16["status"], falhas)
        g = lambda x: f"{x / G:.4f} g" if x is not None else "None"
        return (f"{nome}: {res.veredito} (motivo {res.motivo!r}); S_f {g(res.ay_sat_f)}, S_r {g(res.ay_sat_r)}, resolução "
                f"{g(res.resolucao_ms2)}, R {R_sh!r} ({r24['modo']}), formas {formas.ackermann}/{formas.fx}",
                {"res": res, "caso": caso, "formas": formas, "r16": r16, "r24": r24, "d14": d14, "wb": None, "fator": fator})
    finally:
        wb.close()
        wbf.close()


# casos do 004: nome -> (alterações, opções do comparador)
CASOS4 = {
    "M_MAN_D": ({**BASE, **MAN8}, dict(b48=True, com_troca=True)),
    "M_MAN_E": ({**BASE, **MAN8, **ESQUERDA}, {}),
    "M_LC_D": ({**BASE}, dict(b48=True)),
    "M_LC_E": ({**BASE, **ESQUERDA}, {}),
    "M_RC_D": ({**BASE, N24["modo"]: "Rente aos cones"}, dict(b48=True)),
    "M_RC_E": ({**BASE, N24["modo"]: "Rente aos cones", **ESQUERDA}, {}),
    "LOOSE_PICO": ({**C3b, **H239, **MAN8}, dict(pico="R")),
    "PUSH_PICO": ({**C3, **H239, **MAN8}, dict(pico="F")),
    "FRENTE_DESCOLADA": ({**C2, "ent_05_fracao_de_peso_no_eixo_dianteiro_f": 0.3, "ent_05_altura_do_cg_total": 0.6, **H239,
                          **MAN8}, dict(sem_frente=True, com_k=False)),
    # veículo padrão (a != b: nos casos simétricos req_F = req_R e a troca aF <-> aR no Fx é invisível, como a a <-> b da V4.1)
    "FX_ASSIM": ({**H239, **MAN8}, {}),
    "H2V_0": ({**BASE, **MAN8, N24["h2v"]: 0}, dict(b48=True)),
    "H9V_0": ({**BASE, **MAN8, N24["h9v"]: 0}, {}),
    "CHAVE_H2V_2": ({**BASE, **MAN8, N24["h2v"]: 2}, dict(b48=True, com_troca=True, status="chave h2v deve ser 0 ou 1")),
    "CHAVE_H2V_VAZIA": ({**BASE, **MAN8, N24["h2v"]: None}, dict(status="chave h2v deve ser 0 ou 1")),
    "CHAVE_H9V_TEXTO": ({**BASE, **MAN8, N24["h9v"]: "1"}, dict(status="chave h9v deve ser 0 ou 1")),
    "GEO_RB": ({**BASE_SEM_DELTA, N24["modo"]: "Manual", N24["rman"]: 0.1}, dict(status=eq.MSG_GEOMETRIA, com_troca=True,
                                                                                b48=True, b114="N/A")),
    "GEO_RC": ({**BASE_SEM_DELTA, N24["modo"]: "Manual", N24["rman"]: 0.84}, dict(status=eq.MSG_GEOMETRIA, b114="N/A")),
    "GEO_RB_H2V0": ({**BASE, N24["modo"]: "Manual", N24["rman"]: 0.1, N24["h2v"]: 0}, {}),
    "GEO_RC_H2V0": ({**BASE, N24["modo"]: "Manual", N24["rman"]: 0.84, N24["h2v"]: 0}, {}),
    "MODO_ERRADO": ({**BASE, N24["modo"]: "linha central"}, dict(modo_invalido=True)),
    "MODO_TEXTO": ({**BASE, N24["modo"]: "qualquer coisa"}, dict(modo_invalido=True)),
    "MODO_INV_H0": ({**C3, N24["modo"]: "linha central"}, dict(modo_invalido=True, b173=True)),
    "DINT_VAZIO": ({**BASE, N24["dint"]: None}, {}),
    "DEXT_LE_DINT": ({**BASE, N24["dext"]: 10.0}, {}),
    "RIN_LE_L": ({N24["modo"]: "Rente aos cones", N24["dint"]: 2.0}, dict(eixo="traseiro")),
    "BITOLA_TR_VAZIA": ({N24["modo"]: "Rente aos cones", "ent_05_rear_track_t_r": None}, dict(erros_v42=True)),
    "MEIA_LARG_VAZIA": ({N24["modo"]: "Rente aos cones", N24["w"]: None}, {}),
    "MANUAL_VAZIO_H2": ({**BASE, N24["modo"]: "Manual"}, dict(b65=True)),
    "MANUAL_VAZIO_H0": ({**C3, N24["modo"]: "Manual"}, dict(b173=True)),
    "FATOR_05": ({**BASE, **MAN8, N24["fator"]: 0.5}, dict(status=eq.MSG_FATOR, menos_formulas=1)),
}


LKY_RF3 = 0.9   # escala só de teste (a do RF3 do TC-WB41-004): põe o pico traseiro em 2 g entre dois α da grade pedida


def lmuy_rf3(caso_c3) -> float:
    """LMUY (valor da 10_TIRE) em que, com LKY × LKY_RF3, o eixo traseiro do C3 satura na grade pedida e não na refinada
    (a mesma bisseção do TC-WB41-004; meio da janela entre os dois limiares). Valor de TESTE."""
    def satura(f, passo, n):
        cs = dataclasses.replace(caso_c3, ds=eq.com_fatores(caso_c3.ds, {"LMUY": f, "LKY": LKY_RF3}))
        return eq._varredura(cs, ae.AY_MAX_G, passo, n)[2].ay_sat is not None

    def limiar(passo, n):
        lo, hi = 1.3, 2.0
        if not satura(lo, passo, n) or satura(hi, passo, n):
            raise RuntimeError("RF3: o intervalo do fator de LMUY não cerca a saturação traseira em 2 g")
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if satura(mid, passo, n) else (lo, mid)
        return lo
    f_ped, f_fina = limiar(ae.PASSO_G, ae.N_ALFA), limiar(ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1)
    if not f_fina < f_ped:
        raise RuntimeError(f"RF3: sem janela entre as grades (fator pedida {f_ped}, refinada {f_fina})")
    return caso_c3.ds.p["LMUY"] * 0.5 * (f_ped + f_fina)


def casos_dinamicos(tmp: Path) -> dict:
    """NEUTRO_43 (a faixa 4/3 muda o veredito da V4.2 para a V4.3) e RF3_43 (eixo saturado numa grade só: resolução = passo,
    sem o fator), construídos do caso lido de uma cópia recalculada (valores de TESTE)."""
    out = {}
    quer = lambda n: not SUB or n in SUB or "TC004" in SUB
    if quer("NEUTRO_43"):
        base = g43.copia_v43(tmp, dict(C2), "V4_3_NEUTRO_BASE.xlsx")
        recalcular(base)

        def ver(f, fn):
            caso, formas = caso_com_karb(base, f, False)
            return eq.analise_par(caso, formas=formas, fator_neutro=fn).veredito
        lo, hi = 1.0, 3.0
        if ver(lo, 1.0) != eq.NEUTRO or ver(hi, 1.0) == eq.NEUTRO:
            raise RuntimeError("NEUTRO_43: o intervalo de K_ARB dianteiro não cerca a borda do NEUTRO")
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if ver(mid, 1.0) == eq.NEUTRO else (lo, mid)
        f_alvo = hi          # a primeira fora da faixa sem o fator
        if ver(f_alvo, eq.FATOR_NEUTRO) != eq.NEUTRO:
            raise RuntimeError(f"NEUTRO_43: com o fator 4/3 o veredito em ×{f_alvo} não é NEUTRO")
        alt = {**C2, "ent_06_k_arb_dianteiro": 5012.32 * f_alvo}

        def pos(copia, dados, falhas):
            res = dados["res"]
            sem_fator = eq.analise_par(dados["caso"], formas=dados["formas"], fator_neutro=1.0).veredito
            c42 = copia42(tmp, alt, "V4_2_NEUTRO_43.xlsx")
            recalcular(c42)
            wb = openpyxl.load_workbook(c42, data_only=True)
            ver42 = valor(wb, ae.NOME16["ver"])
            wb.close()
            print(f"   NEUTRO_43: K_ARB dianteiro ×{f_alvo:.6f}: V4.3 {res.veredito} (4/3), Python sem o fator {sem_fator}, V4.2 na planilha {ver42}")
            if not (res.veredito == eq.NEUTRO and dados["r16"]["ver"] == eq.NEUTRO and sem_fator != eq.NEUTRO
                    and ver42 == sem_fator):
                falhas.append(f"NEUTRO_43: V4.3 {res.veredito}/{dados['r16']['ver']}, sem o fator {sem_fator}, V4.2 {ver42}")
        out["NEUTRO_43"] = (alt, dict(pos=pos))
    if quer("RF3_43"):
        base = g43.copia_v43(tmp, dict(C3), "V4_3_RF3_BASE.xlsx")
        recalcular(base)
        caso_c3, _ = cp.caso_da_planilha_v43(base, TIR, passo1=False)
        lky = caso_c3.ds.p["LKY"] * LKY_RF3
        alt = {**C3, "ent_10_lmuy": lmuy_rf3(caso_c3), "ent_10_lky": lky}

        def pos_rf3(copia, dados, falhas):
            caso, formas = dados["caso"], dados["formas"]
            r = dados["res"]
            _, _, sr2 = eq._varredura(caso, ae.AY_MAX_G, ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1, formas=formas)
            ok = r.ay_sat_r is not None and sr2.ay_sat is None and r.resolucao_ms2 == ae.PASSO_G * G                 and perto(dados["r16"]["resol"], ae.PASSO_G * G, onde="RF3_43 resol")
            print(f"   RF3_43: S_r {r.ay_sat_r}, S_r refinada {sr2.ay_sat}, resolução {r.resolucao_ms2} (passo {ae.PASSO_G * G}), planilha "
                  f"{dados['r16']['resol']}")
            if not ok:
                falhas.append(f"RF3_43: o caso não ficou com a traseira saturando só na grade pedida (S_r {r.ay_sat_r}, refinada "
                              f"{sr2.ay_sat}, resolução {r.resolucao_ms2}, planilha {dados['r16']['resol']})")
        out["RF3_43"] = (alt, dict(pos=pos_rf3))
    return out


def tc_wb43_004(tmp: Path) -> None:
    falhas, resumos, tempos = [], [], []
    flags = defaultdict(int)
    infos = {}
    casos = dict(CASOS4)
    casos.update(casos_dinamicos(tmp))
    for nome, (alt, op) in casos.items():
        if SUB and nome not in SUB and "TC004" not in SUB:
            continue
        copia = g43.copia_v43(tmp, alt, f"V4_3_{nome}.xlsx")
        info, t = recalcular(copia); tempos.append(t)
        if op.get("erros_v42"):   # esvaziar a bitola traseira já dá erro em abas da V4.2: o conjunto de erros tem de ser o dela
            i42, _ = recalcular(copia42(tmp, {k: v for k, v in alt.items() if k.startswith("ent_05")}, f"V4_2_{nome}.xlsx"))
            e43 = {loc for d in info["error_summary"].values() for loc in d["locations"]}
            e42 = {loc for d in i42["error_summary"].values() for loc in d["locations"]}
            if e43 != e42 or any(x.split("!")[0] in (ae.ABA16, ae.ABA17, ae.ABA18, ac.ABA24) for x in e43):
                falhas.append(f"{nome}: erros da V4.3 {sorted(e43 - e42)[:5]} fora dos da V4.2; ou em 16/17/18/24: {sorted(e43)[:8]}")
            print(f"  {nome}: {len(e43)} erro(s) de fórmula, os mesmos da V4.2 (bitola traseira vazia; nenhum na 16, 17, 18 ou 24)")
        elif info["total_errors"] or info["total_formulas"] != FORMULAS - op.get("menos_formulas", 0):
            falhas.append(f"{nome}: {info['total_errors']} erro(s) {info['error_summary']}, {info['total_formulas']} fórmulas")
        print(f"  {nome}: recalculado em {t:.1f} s; {info['total_formulas']} fórmulas, {info['total_errors']} erros", flush=True)
        f0 = len(falhas)
        fl = defaultdict(int)
        resumo, dados = comparar43(nome, copia, falhas, fl, com_k=op.get("com_k", True), com_troca=op.get("com_troca", False),
                                   b48=op.get("b48"), esperado_status=op.get("status"))
        for k, v in fl.items():
            flags[k] += v
        resumos.append(resumo + (" [FALHA]" if len(falhas) > f0 else ""))
        infos[nome] = (dados, fl)
        r16, r24 = dados["r16"], dados["r24"]
        # verificações específicas de cada caso
        if op.get("pico") == "R" and fl["pico_R"] == 0:
            falhas.append(f"{nome}: nenhuma linha com a força traseira acima do pico (LOOSE_PICO não exerceu a C-G4b)")
        if op.get("pico") == "F" and fl["pico_F"] == 0:
            falhas.append(f"{nome}: nenhuma linha com a força dianteira acima do pico (PUSH_PICO não exerceu a C-G4)")
        if op.get("sem_frente") and not (fl["semF"] > 0 and fl["alfa"] > 0):
            falhas.append(f"{nome}: a dianteira descolada deve dar linhas com e sem curva (semF {fl['semF']}, α {fl['alfa']})")
        if op.get("b114") is not None:
            wb = openpyxl.load_workbook(copia, data_only=True)
            b114 = wb[ae.ABA16]["B114"].value
            wb.close()
            if b114 != op["b114"]:
                falhas.append(f"{nome}: 16 B114 {b114!r}, esperado {op['b114']!r}")
        if op.get("pos"):
            op["pos"](copia, dados, falhas)
        if op.get("modo_invalido") and not (r24["rusado"] in ("", None) and r24["motivo_r"] == skidpad.MOTIVO_MODO_INVALIDO):
            falhas.append(f"{nome}: modo inválido: R usado {r24['rusado']!r} motivo {r24['motivo_r']!r}")
        if op.get("eixo") and not (r24["eixo"] == op["eixo"] and str(r24["lim_diant"]).startswith("- (R_in'")):
            falhas.append(f"{nome}: eixo {r24['eixo']!r} lim_diant {r24['lim_diant']!r}, esperado {op['eixo']!r} e texto do limite")
        if op.get("b65") or op.get("b173"):
            wb = openpyxl.load_workbook(copia, data_only=True)
            b65, b173 = wb[ae.ABA16]["B65"].value, wb[ae.ABA16]["B173"].value
            wb.close()
            if op.get("b65") and b65 != "raio do skidpad R a confirmar (R manual vazio: a confirmar)":
                falhas.append(f"{nome}: B65 {b65!r}")
            if op.get("b173") and not (isinstance(b173, str) and b173.startswith("N/A: raio do skidpad R a confirmar (")
                                       and b173.endswith(f"({r24['motivo_r']})")):
                falhas.append(f"{nome}: B173 {b173!r}")
    for r in resumos:
        print("  " + r)
    print(f"  MAIOR diferença relativa planilha × Python ({MOTOR}): {DIF_MAX[0]:.2e} ({DIF_MAX[1]}); colunas novas: {dict(flags)}")
    for f in falhas[:12]:
        print("   FALHA:", f)
    check("TC-WB43-004: V4.3 em fórmulas (24_CURVA, 16 a 20 e a mini-grade da 19) == caso_da_planilha_v43 + analise_par(formas=, "
          "fator_neutro=) + tabela_linear(formas=): grades 17/18 e mini-grade (aF, aR, fxr; capacidade, motivo, folga), K e ângulos, "
          "resumo, tempo de volta, R usado/motivo/θ/geometria/pior origem do R, E173, B48 e a aba 20; dois sentidos, três modos do R, "
          "LOOSE_PICO/PUSH_PICO, dianteira descolada, geometria, chaves, modo, diâmetros, R_in' <= L, Manual vazio, fator",
          not falhas, f"{len(falhas)} divergência(s): {falhas[:6]}; recálculo (s) {[round(t) for t in tempos]}")


def tc_wb43_005(tmp: Path) -> None:
    """TC-WB43-005: barra de fórmulas (Excel via COM, só leitura, em cópia)."""
    copia = g43.copia_v43(tmp, {}, "V4_3_barra.xlsx")
    xl = rc._abrir_excel()
    wb = xl.Workbooks.Open(str(copia.resolve()), UpdateLinks=0, ReadOnly=True)
    achados = []
    try:
        for aba, cel in ((ae.ABA16, "B84"), (ae.ABA16, "B9"), (ae.ABA17, "BP24")):
            ws = wb.Worksheets(aba)
            r = ws.Range(cel)
            tem, oculta, prot = bool(r.HasFormula), bool(r.FormulaHidden), bool(ws.ProtectContents)
            achados.append(f"{aba}!{cel}: HasFormula={tem} FormulaHidden={oculta} ProtectContents={prot}")
            if not (tem and not oculta and not prot):
                falhas_005.append(achados[-1])
    finally:
        wb.Close(False)
    print("  " + "; ".join(achados))


falhas_005: list = []
with tempfile.TemporaryDirectory(prefix="dds_wb43_") as _t:
    _t = Path(_t)
    tc_wb43_003(_t)
    if not SUB or "TC005" in SUB:
        if MOTOR != "excel":
            print("TC-WB43-005 NÃO EXECUTÁVEL: só no Excel (COM)"); sys.exit(3)
        tc_wb43_005(_t)
        check("TC-WB43-005: no Excel, 16_EQUILIBRIO B84 e B9 e 17_EQ_PAR BP24 com HasFormula True, FormulaHidden False e a aba sem "
              "proteção", not falhas_005, f"{falhas_005}")
    tc_wb43_004(_t)

print("\n--- Resumo ---"); p = sum(1 for _, s in results if s == "PASS"); f = len(results) - p
print(f"{p} PASS, {f} FAIL, de {len(results)} testes")
sys.exit(1 if f else 0)
