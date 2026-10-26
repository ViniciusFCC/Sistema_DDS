"""
Teste da V4.2 no motor de recálculo (incremento 5, metas e coerência; EDR-044): motor, equivalência com a V4.1 e origens do T11
(TC-WB42-005) e a coerência das fichas da 03_TARGETS e o bloco de metas do 14_DASHBOARD contra o oráculo `metas.py` (TC-WB42-006).
Recalcula CÓPIAS (gerar_v4_2.copia_v42: a V4.2 como o gerador a monta, da tag v4.1, + valores de teste) pelo Excel (COM) ou pelo
LibreOffice (recalculo_planilha.py; DDS_RECALC=excel|libreoffice força um; nesta fase, só Excel). A V4.1 e a V4.2 de referência
e a viva do Drive nunca são abertas para escrita. Sem motor: NÃO EXECUTÁVEL (código 3), que nunca conta como aprovado.
Uso: uv run python -X utf8 tests/test_workbook_v4_2.py
Namespace TC-WB42-xxx (IDs autorizados: 001 a 006; este script tem o 005 e o 006; o 001 a 004 estão em tests/test_v4_2.py).

TC-WB42-005: (1) a V4.2 como gerada (cópia C0, entradas nominais) recalculada tem 0 erro e 117627 fórmulas, e todo `res` dos 1145
nomes da V4.1 (data/nomes_V4_0.csv e data/nomes_V4_1.csv) tem o mesmo valor da V4.1 da tag `v4.1` recalculada (texto: igualdade
exata, com os rótulos de dado de origem mapeados pela decisão 1 do EDR-062 e 14_DASHBOARD B28 = 7 TARGETs em vez de 5; número: rel. <= 1e-12, a tolerância do TC-WB41-003), inclusive 16_EQUILIBRIO B188 e B189 (as duas mostram "DEMONSTRATIVO · " com
as entradas nominais). (2) ORG_T11: todas as células de Origem em "● Dado do T11" (nomes org_*), sobre o C4 (hipóteses h2, h3, h7,
h8 e h9 ligadas): pior origem do K e do veredito = T11, K e veredito sem o prefixo e iguais a `texto_k` / `texto_veredito` com
`origem_do_carro=T11` calculados pelo Python do caso lido da cópia (a pior origem vem da construção do caso, com `ORIGENS_V42`, e
não da fórmula). (3) ORG_TXCOLADO: o mesmo, com "● Dado do TX" (rótulo da V4.1) colado numa Origem da 05_VEHICLE que entra na pior
origem do K (Review Focus 1): o MATCH falha, a pior origem é "? A confirmar" e os textos levam o prefixo. (4) KAPPA_PICO: h9 ligada
(R, CdA, Crr e ρ de teste, h3 ligada porque a h3 é estrita) e KPUMAX da 10_TIRE = 0,05, abaixo do κ do pico de Fx (calculado à parte
em equilibrio._kappa_pico_fx): veredito N/A com o motivo "pico de Fx fora da forma fechada" (decisão 4 do EDR-060, deferida do
incremento 4). Valores de teste só nas cópias; o tempo de recálculo de cada cópia vai ao log.

TC-WB42-006: cada cópia tem as sete fichas da 03_TARGETS preenchidas (valores de TESTE, só nas cópias; não são metas da equipe) para
forçar os quatro estados e cada motivo de CONFLITO:
- C_MISTA: Ciclo de vida "Open" (001) e Papel "meta" (002) colados fora do vocabulário; duas METAs na λ_f (003 e 006); compromisso com
  EDR fora do formato ("edr-061", 004); compromisso com "EDR-061" (005, COMPROMISSO DECLARADO); Congelamento "F9" (007);
- C_FOCO5 (Review Focus 5): Papel META nas sete fichas, Target TBD: 003, 006 e 007 em CONFLITO (sobredeterminação) e 001, 002, 004
  e 005 NÃO AVALIÁVEL; B50 = CONFLITO;
- C_COMPROMISSO: sete fichas válidas, uma com compromisso e EDR (B50 = COMPROMISSO DECLARADO, B51 = 1), com as origens das raízes
  da frequência dianteira em "● Dado do T11" (a pior origem da ficha 001 muda e a das outras não);
- C_COERENTE: a mesma sem o compromisso (B50 = COERENTE, B51 = 0);
- C_INICIAL: a V4.2 como gerada (Papel TBD, Target TBD): sete NÃO AVALIÁVEL, B50 = NÃO AVALIÁVEL.
Em cada cópia: 0 erro e 117627 fórmulas; a coluna Coerência (O5:O11) igual a `metas.texto_coerencia` das fichas lidas da cópia
(`aba_metas.fichas_da_planilha`) e ao texto esperado escrito aqui, de forma independente; a Alavanca (I) igual a `metas.alavanca`; as
auxiliares U iguais à contagem do oráculo; B50 e B51 iguais a `metas.pior_coerencia` e `metas.compromissos`; a pior origem (L) de
cada meta igual a uma construção independente (raízes de `raizes.Grafo` e a lista `origens.ORIGENS_V42`; para o K e o limite,
`aba_equilibrio.termos_pior_origem`). O tempo de recálculo de cada cópia vai ao log.
"Passou" = a planilha reproduz o oráculo; não é validação física.
"""
import csv, math, os, sys, tempfile, time
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
from pathlib import Path
import openpyxl
import aba_equilibrio as ae
import aba_metas
import caso_planilha as cpl
import equilibrio as eq
import equilibrio_linear as el
import tire_model as tm
import gerar_v4_2 as g42
import metas
import origens
import recalculo_planilha as rc
from nomes_v4_0 import ler_tabela
from raizes import Grafo

MOTOR, DETALHE = rc.escolher()
if MOTOR is None:
    print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({DETALHE})"); sys.exit(3)
print(f"MOTOR: {MOTOR} ({DETALHE})")
results = []
FORMULAS = 117627
FORMULAS_V41 = 117569
TOL_EQUIV = 1e-12
_RAIZ = Path(__file__).resolve().parent.parent
# nomes das células de 03_TARGETS: C:G das linhas 5 a 9 são da V4.0; o resto, de aba_metas.NOMES_V42
NM = {(n.aba, n.celula): n.nome for n in [*ler_tabela(_RAIZ / "data" / "nomes_V4_0.csv"), *aba_metas.NOMES_V42]}
ALV_LAMBDA = "distribuição de rolagem λ_f (barras)"


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def recalcular(caminho: Path) -> tuple[dict, float]:
    t0 = time.perf_counter()
    if MOTOR == "excel":
        rc._excel_recalc(str(caminho.resolve()), 1800)
    else:
        rc._libreoffice(str(caminho.resolve()), 1800)
    t_motor = time.perf_counter() - t0
    return rc._resumo(str(caminho.resolve())), t_motor


def alvo(n: int) -> str:
    return f"TARGET-00{n}"


def alt(**linhas) -> dict:
    """Alterações por nome definido: alt(r5={"H": "META", "C": 2.5}, ...) -> {nome: valor}; r<n> = TARGET-00<n>."""
    out = {}
    for chave, campos in linhas.items():
        r = 4 + int(chave[1:])
        for col, v in campos.items():
            out[NM[("03_TARGETS", f"{col}{r}")]] = v
    return out


def valida(h, c, **extra):
    return {"H": h, "C": c, **extra}


# --- cenários (valores de TESTE) e o texto esperado (sem a pior origem) de cada ficha, escrito aqui sem usar metas.py ---
SOBRE = f"CONFLITO: sobredeterminação ({ALV_LAMBDA}; escolha qual manda)"
NAO_AV = "NÃO AVALIÁVEL: meta sem valor ou papel (TBD)"
COER = "COERENTE (regras avaliadas: vocabulário e sobredeterminação)"
CENARIOS = {
    "C_MISTA": (
        alt(r1={"D": "Open", "H": "CONSEQUÊNCIA", "C": 2.5}, r2={"H": "meta", "C": 2.7},
            r3={"H": "META", "C": 0.55}, r6={"H": "META", "C": 1.2},
            r4={"H": "META", "C": 12, "M": "custo declarado", "N": "edr-061"},
            r5={"H": "CONSEQUÊNCIA", "C": 30, "M": "custo declarado", "N": "EDR-061"},
            r7={"H": "CONSEQUÊNCIA", "C": "PUSH", "J": "F9"}),
        ["CONFLITO: Ciclo de vida fora do vocabulário", "CONFLITO: Papel fora do vocabulário", SOBRE,
         "CONFLITO: compromisso sem EDR", "COMPROMISSO DECLARADO", SOBRE, "CONFLITO: Congelamento fora do vocabulário"],
        "CONFLITO", 1),
    "C_FOCO5": (
        alt(**{f"r{i}": {"H": "META"} for i in range(1, 8)}),
        [NAO_AV, NAO_AV, SOBRE, NAO_AV, NAO_AV, SOBRE, SOBRE], "CONFLITO", 0),
    "C_COMPROMISSO": (
        alt(r1={"H": "CONSEQUÊNCIA", "C": 2.5}, r2={"H": "META", "C": 2.7}, r3={"H": "META", "C": 0.55},
            r4={"H": "META", "C": 0}, r5={"H": "META", "C": 30, "M": "custo declarado", "N": "EDR-061"},
            r6={"H": "CONSEQUÊNCIA", "C": 1.5}, r7={"H": "CONSEQUÊNCIA", "C": "PUSH"}),
        [COER, COER, COER, COER, "COMPROMISSO DECLARADO", COER, COER], "COMPROMISSO DECLARADO", 1),
    "C_COERENTE": (
        alt(r1={"H": "CONSEQUÊNCIA", "C": 2.5}, r2={"H": "META", "C": 2.7}, r3={"H": "META", "C": 0.55},
            r4={"H": "META", "C": 0}, r5={"H": "META", "C": 30}, r6={"H": "CONSEQUÊNCIA", "C": 1.5},
            r7={"H": "CONSEQUÊNCIA", "C": "PUSH"}),
        [COER] * 7, "COERENTE", 0),
    "C_INICIAL": ({}, [NAO_AV] * 7, "NÃO AVALIÁVEL", 0),
}


def pior_origem_independente(copia_formulas: Path, wb_valores) -> dict[str, str]:
    """Pior origem esperada de cada meta, sem usar as fórmulas G2: raízes (raizes.Grafo) das grandezas e a lista V4.2."""
    wb = openpyxl.load_workbook(copia_formulas)
    try:
        g = Grafo(wb)
        lista = origens.ORIGENS_V42
        out = {}
        for r in metas.RELACOES:
            if r.tipo != "alavanca" or r.fonte_tipo != "M":
                continue
            no = ae._destino(wb, r.resultado)
            if r.meta in ("TARGET-006", "TARGET-007"):
                termos = ae.termos_pior_origem(wb, linear=(r.meta == "TARGET-006"))
                chaves = {k: cpl._valor_por_nome(wb, ae.NOME_ENT[k]) for k in ("h2", "h3", "h7", "h8", "h9")}
            else:
                termos = [(a, c, None) for a, c in g.celulas_origem(no)]
                chaves = {}
            out[r.meta] = ae.pior_origem_de_valores(termos, lambda a, c: wb_valores[a][c].value, chaves, lista=lista)
        return out
    finally:
        wb.close()


with tempfile.TemporaryDirectory(prefix="dds_wb42_") as tmp:
    tmp = Path(tmp)
    ok_geral, detalhes, tempos = True, [], []
    for nome, (alteracoes, esperado, b50, b51) in CENARIOS.items():
        copia = g42.copia_v42(tmp, alteracoes, f"V4_2_{nome}.xlsx")
        if nome == "C_COMPROMISSO":   # a pior origem da ficha 001 muda quando as raízes dela viram "● Dado do T11"
            wbx = openpyxl.load_workbook(copia)
            for a_, c_ in Grafo(wbx).celulas_origem(ae._destino(wbx, "res_06_frequencia_natural_dianteira")):
                wbx[a_][c_].value = origens.T11
            wbx.save(copia)
            wbx.close()
        res, t = recalcular(copia)
        tempos.append((nome, t))
        wbv = openpyxl.load_workbook(copia, data_only=True)
        fichas = aba_metas.fichas_da_planilha(copia)
        t3 = wbv["03_TARGETS"]
        textos = [t3[f"O{r}"].value for r in aba_metas.LINHAS]
        po = [f.pior_origem for f in fichas]
        espera_oraculo = [metas.texto_coerencia(f, fichas) for f in fichas]
        espera_indep = [f"{e} · {p}" for e, p in zip(esperado, po)]
        alav_ok = [t3[f"I{r}"].value for r in aba_metas.LINHAS] == [metas.alavanca(alvo(i)) for i in range(1, 8)]
        n_outras = [sum(1 for g in fichas if g is not f and g.papel == "META" and metas.alavanca(g.target) == metas.alavanca(f.target))
                    for f in fichas]
        u_ok = [t3[f"U{r}"].value for r in aba_metas.LINHAS] == n_outras
        d14 = wbv["14_DASHBOARD"]
        dash_ok = d14["B50"].value == b50 == metas.pior_coerencia(textos) and d14["B51"].value == b51 == metas.compromissos(textos)
        pior = pior_origem_independente(copia, wbv)
        l_ok = all(f.pior_origem == pior[f.target] for f in fichas if f.target in pior) and len(pior) == 7
        if nome == "C_COMPROMISSO":
            l_ok &= fichas[0].pior_origem == origens.T11 and all(f.pior_origem != origens.T11 for f in fichas[1:3])
        ok = res["total_errors"] == 0 and res["total_formulas"] == FORMULAS and textos == espera_oraculo == espera_indep \
            and alav_ok and u_ok and dash_ok and l_ok and all(f.pior_origem in origens.ORIGENS_V42 for f in fichas)
        ok_geral &= ok
        detalhes.append(f"{nome}: {'ok' if ok else 'FALHA'} erros={res['total_errors']} fórmulas={res['total_formulas']} "
                        f"coerência={textos == espera_oraculo}/{textos == espera_indep} alavanca={alav_ok} U={u_ok} "
                        f"dashboard={dash_ok} (B50={d14['B50'].value!r} B51={d14['B51'].value!r}) L={l_ok} recálculo={t:.0f}s")
        if not ok:
            detalhes.append(f"   textos={textos}; esperado={espera_indep}; pior={pior}")
        wbv.close()
    for d in detalhes:
        print("  ", d)
    check("TC-WB42-006: coerência das fichas (03_TARGETS O5:O11, com auxiliares G3 e G4, Alavanca G1 e pior origem G2) e o bloco de metas "
          "do 14_DASHBOARD (B50, B51) na planilha recalculada = metas.py e o texto esperado escrito à parte, em 5 cópias que forçam os 4 "
          "estados, campo fora do vocabulário colado (Ciclo, Papel, Congelamento), duas METAs na λ_f, compromisso com e sem EDR e as 7 "
          "METAs (Review Focus 5); 0 erros e 117627 fórmulas",
          ok_geral, f"tempos={[(n, round(t)) for n, t in tempos]}")


# --- TC-WB42-005: motor, equivalência com a V4.1 e origens do T11 ---
TIR = _RAIZ / "data" / "Hoosier_R25B_13x7_TTC_provisional.tir"
ENT = ae.NOME_ENT
C2 = {"ent_05_rear_track_t_r": 1.277, "ent_05_fracao_de_peso_no_eixo_dianteiro_f": 0.5,
      "ent_05_massa_nao_suspensa_traseira": 15, "ent_06_spring_rate_traseiro": 49909.24,
      "ent_06_k_arb_traseiro": 5012.32, "ent_06_roll_center_traseiro_rh_estatico": 0.0675,
      "ent_07_camber_gain_traseiro_dcamber_dz": -0.6, "ent_10_camber_gama_projeto_topo_para_fora_d": -1.5,
      "ent_10_camber_gama_projeto_topo_para_fora_e": -1.5, "ent_08_aero_balance_fracao_dianteira": 0.5,
      "ent_10_lmuy": 0.45}   # os mesmos valores de teste do TC-WB41-004 (caso simétrico)
C3 = {**C2, "ent_06_k_arb_dianteiro": 5012.32 * 3}
C4 = {**C3, ENT["R"]: 8.0, ENT["h2"]: 1, ENT["h3"]: 1, ENT["cg"]: 0.010, ENT["h7"]: 1, ENT["sentido"]: "Direita",
      ENT["h8"]: 1, ENT["rho"]: 1.2, ENT["cza"]: 2.0, "ent_08_downforce_total": 0, ENT["h9"]: 1, ENT["cda"]: 1.0,
      ENT["crr"]: 0.015, ENT["toeFL"]: 0.25, ENT["toeFR"]: 0.10,
      "ent_10_camber_gama_projeto_topo_para_fora_b": -1.5, "ent_10_camber_gama_projeto_topo_para_fora_c": -1.0}
KPUMAX_TESTE = 0.05
C_KAPPA = {**C3, ENT["R"]: 8.0, ENT["h3"]: 1, ENT["rho"]: 1.2, ENT["h9"]: 1, ENT["cda"]: 1.0, ENT["crr"]: 0.015,
           ae.nome_coef("KPUMAX"): KPUMAX_TESTE}
PREFIXO = "DEMONSTRATIVO · "


def num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def iguais(a, b) -> bool:
    if num(a) and num(b):
        return a == b or abs(a - b) <= TOL_EQUIV * max(abs(a), abs(b))
    return type(a) is type(b) and a == b


def nomes_da_v41(papel: str) -> list[dict]:
    """Nomes de papel `papel` da V4.1 (nomes_V4_0.csv + nomes_V4_1.csv), como dicionários nome/aba/celula."""
    out = []
    for arq in ("nomes_V4_0.csv", "nomes_V4_1.csv"):
        with open(_RAIZ / "data" / arq, encoding="utf-8", newline="") as f:
            out += [ln for ln in csv.DictReader(f) if ln["papel"] == papel]
    return out


ORG = nomes_da_v41("org") + [{"nome": n.nome, "aba": n.aba, "celula": n.celula} for n in aba_metas.NOMES_V42 if n.papel == "org"]
ORG_POR_CELULA = {(n["aba"], n["celula"]): n["nome"] for n in ORG}


def textos_esperados(copia: Path, pior_ver: str, pior_k: str, origem=origens.T11) -> tuple[str, str]:
    """(veredito, K) que o Python dá ao caso lido da cópia recalculada, com a pior origem dada por construção."""
    res = eq.analise_par(cpl.caso_da_planilha_v41(copia, TIR, passo1=False))
    p = el.parcelas_k(cpl.caso_da_planilha_v41(copia, TIR), 0.0)
    return eq.texto_veredito(res, pior_ver, origem_do_carro=origem), el.texto_k(p, pior_k, origem_do_carro=origem)


def ler_textos(copia: Path) -> dict:
    wb = openpyxl.load_workbook(copia, data_only=True)
    try:
        out = {k: cpl._valor_por_nome(wb, ae.NOME16[k]) for k in ("txt_ver", "txt_k")}
        out.update({k: wb[ae.ABA16][f"E{ae.LINHAS16[k]}"].value for k in ("ver", "kTot")})   # pior origem (coluna E)
        out.update({"14_" + k: cpl._valor_por_nome(wb, n) for k, n in ae.NOME14.items() if k in ("txt_ver", "txt_k")})
        return out
    finally:
        wb.close()


def pior_independente(copia: Path, linear: bool, lista=origens.ORIGENS_V42) -> str:
    wb = openpyxl.load_workbook(copia)
    try:
        termos = ae.termos_pior_origem(wb, linear)
        chaves = {k: cpl._valor_por_nome(wb, ae.NOME_ENT[k]) for k in ("h2", "h3", "h7", "h8", "h9")}
        return ae.pior_origem_de_valores(termos, lambda a, c: wb[a][c].value, chaves, lista=lista)
    finally:
        wb.close()


with tempfile.TemporaryDirectory(prefix="dds_wb42_005_") as tmp5:
    tmp5 = Path(tmp5)
    falhas5, tempos5, notas5 = [], [], []
    todas_t11 = {n["nome"]: origens.T11 for n in ORG}

    # (1) equivalência com a V4.1 da tag
    (tmp5 / "tag").mkdir()   # copia_v42 regrava V4_1_tag.xlsx em tmp5: a V4.1 recalculada fica em outra pasta
    v41 = g42.extrair_v41(tmp5 / "tag")
    info41, t = recalcular(v41); tempos5.append(("V4.1 da tag", t))
    c0 = g42.copia_v42(tmp5, {}, "V4_2_C0.xlsx")
    info0, t = recalcular(c0); tempos5.append(("C0 nominal", t))
    if info41["total_errors"] or info41["total_formulas"] != FORMULAS_V41:
        falhas5.append(f"V4.1 da tag: {info41['total_errors']} erro(s), {info41['total_formulas']} fórmulas")
    if info0["total_errors"] or info0["total_formulas"] != FORMULAS:
        falhas5.append(f"C0: {info0['total_errors']} erro(s) {info0['error_summary']}, {info0['total_formulas']} fórmulas")
    res41 = nomes_da_v41("res")
    if len(res41) < 600:
        falhas5.append(f"só {len(res41)} nomes res lidos")
    w41, w42 = openpyxl.load_workbook(v41, data_only=True), openpyxl.load_workbook(c0, data_only=True)
    n_dif = 0
    for n in res41:
        a, b = w42[n["aba"]][n["celula"]].value, w41[n["aba"]][n["celula"]].value
        b = origens.MAPA_DADO_V41_V42.get(b, b)   # rótulo de dado da V4.1 -> V4.2 (decisão 1, EDR-062): único texto que muda
        if (n["aba"], n["celula"]) == ("14_DASHBOARD", "B28"):
            b = 7   # TARGETs registrados: 5 na V4.1; 7 na V4.2 (TARGET-006 e 007, autorização 1)
        if not iguais(a, b):
            n_dif += 1
            if n_dif <= 10:
                falhas5.append(f"equivalência {n['nome']} ({n['aba']}!{n['celula']}): V4.2={a!r} V4.1={b!r}")
    for cel in ("B188", "B189"):
        a, b = w42["16_EQUILIBRIO"][cel].value, w41["16_EQUILIBRIO"][cel].value
        if not (iguais(a, b) and isinstance(a, str) and a.startswith(PREFIXO)):
            falhas5.append(f"16_EQUILIBRIO {cel}: V4.2={a!r} V4.1={b!r} (esperado igual e com o prefixo DEMONSTRATIVO)")
    w41.close(); w42.close()
    if n_dif > 10:
        falhas5.append(f"... {n_dif} diferenças no total")
    notas5.append(f"{len(res41)} nomes res comparados, {n_dif} diferença(s)")

    # (2) ORG_T11 e (3) ORG_TXCOLADO, sobre o C4
    wbt = openpyxl.load_workbook(c0)
    try:
        termos_k = ae.termos_pior_origem(wbt, True)
        termos_v = ae.termos_pior_origem(wbt, False)
    finally:
        wbt.close()
    fora = sorted({(a, c) for a, c, _ in (*termos_k, *termos_v)} - set(ORG_POR_CELULA))
    if fora:
        falhas5.append(f"células de Origem da pior origem sem nome org_*: {fora}")
    cel05 = next(((a, c) for a, c, cond in termos_k if a == "05_VEHICLE" and cond is None), None)
    if cel05 is None:
        falhas5.append("nenhuma Origem incondicional da 05_VEHICLE entra na pior origem do K")
    casos5 = [("ORG_T11", {**C4, **todas_t11}, origens.T11),
              ("ORG_TXCOLADO", {**C4, **todas_t11, ORG_POR_CELULA.get(cel05, "?"): origens.TX_V41}, origens.CONF)]
    for nome, alt5, pior in casos5:
        copia = g42.copia_v42(tmp5, alt5, f"V4_2_{nome}.xlsx")
        info, t = recalcular(copia); tempos5.append((nome, t))
        if info["total_errors"] or info["total_formulas"] != FORMULAS:
            falhas5.append(f"{nome}: {info['total_errors']} erro(s) {info['error_summary']}, {info['total_formulas']} fórmulas")
        pv, pk = pior_independente(copia, False), pior_independente(copia, True)
        if (pv, pk) != (pior, pior):
            falhas5.append(f"{nome}: pior origem independente (veredito, K) = {(pv, pk)!r}, esperado {pior!r}")
        sh = ler_textos(copia)
        if (sh["ver"], sh["kTot"]) != (pior, pior):
            falhas5.append(f"{nome}: pior origem na planilha (veredito, K) = {(sh['ver'], sh['kTot'])!r}, esperado {pior!r}")
        ev, ek = textos_esperados(copia, pv, pk)
        if (sh["txt_ver"], sh["txt_k"]) != (ev, ek):
            falhas5.append(f"{nome}: textos da 16 {(sh['txt_ver'], sh['txt_k'])!r}, Python {(ev, ek)!r}")
        if (sh["14_txt_ver"], sh["14_txt_k"]) != (sh["txt_ver"], sh["txt_k"]):
            falhas5.append(f"{nome}: o 14_DASHBOARD não repete a 16: {(sh['14_txt_ver'], sh['14_txt_k'])!r}")
        com_prefixo = (sh["txt_ver"].startswith(PREFIXO), sh["txt_k"].startswith(PREFIXO))
        if com_prefixo != (pior != origens.T11,) * 2:
            falhas5.append(f"{nome}: prefixo D16 {com_prefixo} para a pior origem {pior!r}")
        notas5.append(f"{nome}: pior={sh['ver']!r} veredito={sh['txt_ver']!r} K={sh['txt_k'][:48]!r}")

    # (4) h9 com KPUMAX abaixo do κ do pico de Fx
    ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
    kpico = [eq._kappa_pico_fx(ds.p, fz, 0.0) for fz in (400.0, 800.0, 1200.0, 1600.0)]
    if not all(k is not None and KPUMAX_TESTE < k <= ds.p["KPUMAX"] for k in kpico):
        falhas5.append(f"κ do pico de Fx {kpico} não fica entre {KPUMAX_TESTE} e o KPUMAX do .tir ({ds.p['KPUMAX']})")
    copia = g42.copia_v42(tmp5, C_KAPPA, "V4_2_KAPPA_PICO.xlsx")
    info, t = recalcular(copia); tempos5.append(("KAPPA_PICO", t))
    if info["total_errors"] or info["total_formulas"] != FORMULAS:
        falhas5.append(f"KAPPA_PICO: {info['total_errors']} erro(s) {info['error_summary']}, {info['total_formulas']} fórmulas")
    sh = ler_textos(copia)
    motivo = "pico de Fx fora da forma fechada"
    esperado_ver = PREFIXO + "N/A: " + motivo   # a planilha acrescenta onde ("em a_y = 0 g")
    if not (sh["txt_ver"].startswith(esperado_ver) and sh["14_txt_ver"] == sh["txt_ver"]):
        falhas5.append(f"KAPPA_PICO: veredito {sh['txt_ver']!r} (14: {sh['14_txt_ver']!r}), esperado começar por {esperado_ver!r}")
    notas5.append(f"KAPPA_PICO: κ do pico {[round(k, 4) for k in kpico]}, KPUMAX do .tir {ds.p['KPUMAX']}, veredito {sh['txt_ver']!r}")

    for n in notas5:
        print("  ", n)
    for f in falhas5:
        print("   FALHA:", f)
    check("TC-WB42-005: motor sem erro (117627 fórmulas); todo res da V4.1 (786 nomes) igual ao da V4.1 recalculada (B188 e B189 com o "
          "prefixo DEMONSTRATIVO nas duas); com todas as Origens em ● Dado do T11, K e veredito sem prefixo e iguais ao Python com "
          "origem_do_carro=T11; ● Dado do TX colado numa Origem da 05_VEHICLE = ? A confirmar, com prefixo; h9 com KPUMAX abaixo do "
          "κ do pico = N/A \"pico de Fx fora da forma fechada\"",
          not falhas5, f"recálculo (s)={[(n, round(t)) for n, t in tempos5]}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s in results if s == "PASS")
n_fail = sum(1 for _, s in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
