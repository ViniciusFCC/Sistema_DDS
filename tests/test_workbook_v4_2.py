"""
Teste da V4.2 no motor de recálculo (incremento 5, metas e coerência; EDR-044): a coerência das fichas da 03_TARGETS e o bloco de
metas do 14_DASHBOARD contra o oráculo `metas.py` (TC-WB42-006). O TC-WB42-005 (motor, equivalência com a V4.1, origens do T11) entra
na Task seguinte neste mesmo script.
Recalcula CÓPIAS (gerar_v4_2.copia_v42: a V4.2 como o gerador a monta, da tag v4.1, + valores de teste) pelo Excel (COM) ou pelo
LibreOffice (recalculo_planilha.py; DDS_RECALC=excel|libreoffice força um; nesta fase, só Excel). A V4.1 e a V4.2 de referência
e a viva do Drive nunca são abertas para escrita. Sem motor: NÃO EXECUTÁVEL (código 3), que nunca conta como aprovado.
Uso: uv run python -X utf8 tests/test_workbook_v4_2.py
Namespace TC-WB42-xxx (IDs autorizados: 001 a 006; este script tem o 006 nesta etapa; o 001 a 003 estão em tests/test_v4_2.py).

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
import os, sys, tempfile, time
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
from pathlib import Path
import openpyxl
import aba_equilibrio as ae
import aba_metas
import caso_planilha as cpl
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

print("\n--- Resumo ---")
n_pass = sum(1 for _, s in results if s == "PASS")
n_fail = sum(1 for _, s in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
