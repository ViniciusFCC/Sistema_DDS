"""Testes da V4.4 (incremento 8, parte 8b: fórmulas das abas 03 a 14 por nome, valores iguais aos da V4.3).
Uso: uv run python -X utf8 tests/test_v4_4.py
Namespace TC-WB44-xxx (IDs autorizados: 001 a 006; este script tem o 001 a 004; o 005 e o 006 (equivalência por valor e
cobertura de ramos, com recálculo) ficam em tests/test_workbook_v4_4.py). As pré-checagens (regra da troca, tabela de nomes
e gerador) saem fora da contagem. O 002 e o 003 têm a própria leitura dos tokens (openpyxl `Tokenizer`) e NÃO usam
`reescrita_nomes`, para não repetir um erro do gerador. A V4.3 de partida é o arquivo da tag v4.3, extraído para pasta
temporária; nada é gravado em excel/.

TC-WB44-001 (regeneração, CA-07): `gerar(None, tmp)` bate com excel/…V4_4.xlsx por conteúdo (`comparar_xlsx`, com estrutura;
o arquivo de excel/ não é reproduzível byte a byte), 1290 nomes, data/nomes_V4_4.csv = NOMES_V44, 00_README A3 da V4.4.
TC-WB44-002 (regra da troca): V4.3 da tag x V4.4 de excel/, célula a célula. Nas abas 03 a 14, mesmos tokens, cada par igual
ou (referência a uma célula na V4.3, nome da V4.4 cujo destino é essa célula); fora delas, valor idêntico; as exceções X2 a X5
(`alteracoes()`) têm o `novo` na V4.4 e o `antes` na V4.3. Esperado: 2787 trocas e nenhuma diferença fora da regra.
TC-WB44-003 (invariante): nas abas 03 a 14 da V4.4, todo operando de célula única é nome ou linha própria da ficha da 03.
TC-WB44-004 (migração por nome): nomes da V4.3 com o mesmo destino na V4.4, os 24 novos ausentes da V4.3; viva V4.3 com
valores SINTÉTICOS DE TESTE em todos os nomes de dado migra para a V4.4 com código 0, 0 conflito e todos os dados levados.
"Passou" = estrutura, regra e migração conferidas; não é validação física.
"""
import re
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.formula import ArrayFormula

import reescrita_nomes as rn   # só nas pré-checagens; o 002 e o 003 não o usam
import dados_planilha as dp
import gerar_v4_4 as g
import origens
from nomes_v4_0 import ler_tabela
from nomes_v4_4 import NOMES_V44

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import comparar_planilhas as cp  # noqa: E402
import migrar_viva as migr_viva  # noqa: E402

results = []
V44 = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_4.xlsx"   # só leitura
V43 = "excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx"   # só leitura
CSV = "data/nomes_V4_4.csv"


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def raises(fn, exc=Exception):
    try:
        fn()
    except exc:
        return True
    return False


def pre_checagem() -> bool:
    """Pré-checagem pura da regra da troca (fora da contagem). Devolve True se tudo bate."""
    d = {("05_VEHICLE", "B7"): "ent_05_front_track_t_f", ("09_LOADS", "B22"): "res_09_b22",
         ("13_VALIDATION", "B37"): "ent_13_b37"}
    casos = [
        (rn.trocar_formula("='05_VEHICLE'!$B$7*2", "09_LOADS", d), "=ent_05_front_track_t_f*2"),
        (rn.trocar_formula("=B$22+1", "09_LOADS", d), "=res_09_b22+1"),
        (rn.trocar_formula("=$B22+1", "09_LOADS", d), "=res_09_b22+1"),
        (rn.trocar_formula("=SUM('10_TIRE'!$B$168:$B$175)", "09_LOADS", d), "=SUM('10_TIRE'!$B$168:$B$175)"),
        (rn.trocar_formula("=COUNTIF('02_REQUIREMENTS'!A:A,B1)", "09_LOADS", d), "=COUNTIF('02_REQUIREMENTS'!A:A,B1)"),
        (rn.trocar_formula('=IF(A1>0,"B37 e h2v = 0 em 24_CURVA B9",B37)', "13_VALIDATION", d),
         '=IF(A1>0,"B37 e h2v = 0 em 24_CURVA B9",ent_13_b37)'),
        (rn.trocar_formula('=IF( A1 > 0 , "x" , 1 )', "13_VALIDATION", d), '=IF( A1 > 0 , "x" , 1 )'),
        (rn.trocar_formula("='05_VEHICLE'!B7 + '05_VEHICLE'!$B$7", "09_LOADS", d),
         "=ent_05_front_track_t_f + ent_05_front_track_t_f"),
    ]
    ok = True
    for i, (got, esperado) in enumerate(casos, 1):
        if got != esperado:
            ok = False
            print(f"  pré-checagem {i}: obtido {got!r}, esperado {esperado!r}")
    # linha própria da 03 (EDR-070, §3.3/§3.5): com nome é trocada como qualquer célula; sem nome fica por endereço
    d03 = {("03_TARGETS", "A5"): "nome_a5"}
    if (rn.trocar_formula("=A5*2", "03_TARGETS", d03, "H5") != "=nome_a5*2"          # com nome: trocada
            or rn.trocar_formula("=A5*2", "03_TARGETS", {}, "H5") != "=A5*2"            # sem nome: fica por endereço
            or not rn.eh_linha_propria_03("03_TARGETS", "H5", "A5")
            or rn.eh_linha_propria_03("03_TARGETS", "H5", "A6")                         # outra linha: não
            or rn.eh_linha_propria_03("03_TARGETS", "B5", "A5")):                       # fora de H:Q: não
        ok = False
        print("  pré-checagem: linha própria da 03 (A5 em H5, com e sem nome)")
    f = '=IF(A1>0,"B7",1) + SUM(A1:B2)'
    if rn.trocar_formula(f, "09_LOADS", d) != f:
        ok = False
        print("  pré-checagem: fórmula sem troca não voltou idêntica")
    wb = openpyxl.Workbook()
    wb.active.title = "05_VEHICLE"
    wb.defined_names["n1"] = DefinedName("n1", attr_text="'05_VEHICLE'!$B$7")
    wb.defined_names["n_rng"] = DefinedName("n_rng", attr_text="'05_VEHICLE'!$B$7:$B$9")
    if rn.destinos_unicos(wb) != {("05_VEHICLE", "B7"): "n1"}:
        ok = False
        print("  pré-checagem: destinos_unicos não devolveu só a célula única")
    wb.defined_names["n2"] = DefinedName("n2", attr_text="'05_VEHICLE'!B7")
    if not raises(lambda: rn.destinos_unicos(wb), ValueError):
        ok = False
        print("  pré-checagem: dois nomes na mesma célula não deram ValueError")
    return ok


def pre_checagem_nomes() -> bool:
    """Pré-checagem da tabela dos 24 nomes novos (A1), fora da contagem. Devolve True se tudo bate."""
    import nomes_v4_4 as n44
    from nomes_v4_0 import ler_tabela
    from raizes import nomes_definidos

    wb = openpyxl.load_workbook(V43)
    ok = True
    derivada = n44.tabela_v44(wb)
    if derivada != n44.NOMES_V44:
        ok = False
        print("  nomes: tabela_v44(V4.3) difere de NOMES_V44:", [n.nome for n in set(derivada) ^ set(n44.NOMES_V44)][:6])
    if len(n44.NOMES_V44) != 24 or len(n44.CELULAS_V44) != 24:
        ok = False
        print("  nomes: esperados 24 nomes e 24 células")
    if set(nomes_definidos(wb)) & {n.nome for n in n44.NOMES_V44}:
        ok = False
        print("  nomes: algum nome novo já existe na V4.3")
    med = rn.medir(wb, rn.destinos_unicos(wb))
    if set(n44.CELULAS_V44) != set(med.soltas):
        ok = False
        print("  nomes: CELULAS_V44 difere das soltas medidas")
    if tuple((n.aba, n.celula) for n in n44.NOMES_V44) != n44.CELULAS_V44:
        ok = False
        print("  nomes: CELULAS_V44 fora da ordem de NOMES_V44")
    if ler_tabela(CSV) != n44.NOMES_V44:
        ok = False
        print("  nomes: data/nomes_V4_4.csv difere de NOMES_V44")
    if not raises(lambda: n44.conferir_tabela(list(n44.NOMES_V44[:-1])), ValueError):
        ok = False
        print("  nomes: conferir_tabela aceitou tabela diferente")
    n44.conferir_tabela(ler_tabela(CSV))
    return ok


def pre_checagem_gerador() -> bool:
    """Pré-checagem do gerador (fora da contagem): nomes, fórmulas, catálogo e recusa de excel/. True se tudo bate."""
    import tempfile
    from pathlib import Path

    import gerar_v4_4 as g
    sys.path.insert(0, "tools")
    import comparar_planilhas as cp
    from raizes import nomes_definidos

    ok = True
    if not raises(lambda: g.gerar(None, Path("excel") / "x_V4_4.xlsx"), SystemExit):
        ok = False
        print("  gerador: saída em excel/ não deu SystemExit")
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "V4_4.xlsx"
        catalogo, excecoes = g.gerar(None, saida, Path(tmp) / "reg.md")
        wb = openpyxl.load_workbook(saida)
        n_nomes = len(nomes_definidos(wb))
        wb.close()
        _, cel = cp.celulas(saida)
        n_form = sum(1 for v in cel.values() if isinstance(v, str) and v.startswith("="))
        exc = {(a["aba"], a["cel"]) for a in g.alteracoes()}
        if n_nomes != 1290:
            ok = False
            print(f"  gerador: {n_nomes} nomes (esperado 1290)")
        if n_form != 146373:
            ok = False
            print(f"  gerador: {n_form} fórmulas (esperado 146373)")
        if len(catalogo) != 422:
            ok = False
            print(f"  gerador: catálogo com {len(catalogo)} linhas (esperado 422)")
        if any((r["aba"], r["cel"]) in exc for r in catalogo) or len(excecoes) != len(exc):
            ok = False
            print("  gerador: exceção no catálogo ou registro de exceções incompleto")
        if bytes([13]) in (Path(tmp) / "reg.md").read_bytes():
            ok = False
            print("  gerador: registro com CR")
    return ok


# --- leitura própria dos tokens (independente de reescrita_nomes) ---
ABAS_03_A_14 = ("03_TARGETS", "04_DECISION_REGISTER", "05_VEHICLE", "06_SUSPENSION", "07_KINEMATICS", "08_VEHICLE_STATE",
                "09_LOADS", "10_TIRE", "11_DESIGN", "12_COMPARISON", "13_VALIDATION", "14_DASHBOARD")
RE_CEL = re.compile(r"^(?:(?P<aba>'[^']+'|[^!']+)!)?\$?(?P<c>[A-Z]{1,3})\$?(?P<r>\d+)$")
RE_INTERVALO = re.compile(r"^(?:(?:'[^']+'|[^!']+)!)?\$?[A-Z]{1,3}\$?\d+:\$?[A-Z]{1,3}\$?\d+$")
RE_COLUNA = re.compile(r"^(?:(?:'[^']+'|[^!']+)!)?\$?[A-Z]{1,3}:\$?[A-Z]{1,3}$")


def cel_unica(valor: str, aba: str):
    """(aba, célula) se o operando é referência a uma célula só (com ou sem aba e `$`); senão None."""
    m = RE_CEL.match(valor)
    if not m:
        return None
    return (m["aba"] or aba).strip("'"), f"{m['c']}{m['r']}"


def destinos_nomes(wb) -> dict:
    """nome -> (aba, célula) dos nomes cujo destino é uma célula só (aspas e `$` normalizados)."""
    out = {}
    for n, d in wb.defined_names.items():
        alvo = cel_unica(d.attr_text, "")
        if alvo is not None and alvo[0]:
            out[n] = alvo
    return out


def texto(v):
    """Forma comparável do conteúdo de uma célula (fórmula matricial com o intervalo; None = vazia)."""
    if isinstance(v, ArrayFormula):
        return ("array", v.ref, v.text)
    return v if v is None else (type(v).__name__, v)


def conteudos(wb) -> dict:
    return {(ws.title, c.coordinate): c.value for ws in wb.worksheets for lin in ws.iter_rows() for c in lin
            if c.value is not None}


def tokens(v):
    f = v.text if isinstance(v, ArrayFormula) else v
    if not (isinstance(f, str) and f.startswith("=")):
        return None
    return Tokenizer(f).items


def rodar(tc: str, fn) -> None:
    """Roda um TC; qualquer exceção (inclusive SystemExit) vira FAIL com o tipo e a mensagem, nunca aborta o script."""
    try:
        fn()
    except BaseException as e:   # falha ruidosa, nunca silenciosa
        check(f"TC-WB44-{tc}", False, f"exceção {type(e).__name__}: {str(e)[:300]}")


def main():
    if not V44.exists():
        for n in ("001", "002", "003", "004"):
            check(f"TC-WB44-{n}", False, "falta a cópia excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx (Task 13, Step 6)")
        return
    with tempfile.TemporaryDirectory(prefix="dds_t44_") as tmp:
        tmp = Path(tmp)
        est = {}

        def abrir():
            est["v43"] = g.extrair_v43(tmp)
            est["wb43"] = openpyxl.load_workbook(est["v43"])
            est["wb44"] = openpyxl.load_workbook(V44)
            est["c43"], est["c44"] = conteudos(est["wb43"]), conteudos(est["wb44"])
            est["nomes44"] = destinos_nomes(est["wb44"])

        try:
            rodar("001", lambda: tc_001(tmp, openpyxl_44()))
            try:
                abrir()
            except BaseException as e:
                for n in ("002", "003", "004"):
                    check(f"TC-WB44-{n}", False, f"não abriu as planilhas: {type(e).__name__}: {str(e)[:300]}")
                return
            rodar("002", lambda: tc_002(est["c43"], est["c44"], est["nomes44"]))
            rodar("003", lambda: tc_003(est["wb44"], est["c44"]))
            rodar("004", lambda: tc_004(tmp, est["v43"], est["wb43"], est["wb44"]))
        finally:
            for k in ("wb43", "wb44"):
                if k in est:
                    est[k].close()


def openpyxl_44():
    """Abre a V4.4 de excel/ só para o TC-001 (nomes e A3); fecha ao sair do TC."""
    return openpyxl.load_workbook(V44)


def tc_001(tmp: Path, wb44) -> None:
    try:
        _tc_001(tmp, wb44)
    finally:
        wb44.close()


def _tc_001(tmp: Path, wb44) -> None:
    regen = tmp / "V4_4_regen.xlsx"
    g.gerar(None, regen)
    ok_cmp, rel = cp.comparar_xlsx(regen, V44, cp.FORMULAS_ESPERADAS_V44, estrutura=True)
    n_nomes = len(wb44.defined_names)
    csv_ok = ler_tabela(RAIZ / "data" / "nomes_V4_4.csv") == NOMES_V44
    a3 = wb44["00_README"]["A3"].value
    a3_ok = isinstance(a3, str) and a3.startswith("Versão do workbook: V4.4")
    check("TC-WB44-001: regeneração da V4.4 da tag v4.3 igual a excel/…V4_4.xlsx por conteúdo "
          f"({cp.FORMULAS_ESPERADAS_V44} fórmulas, com estrutura); 1290 nomes; data/nomes_V4_4.csv = NOMES_V44; "
          "00_README A3 da V4.4",
          ok_cmp and n_nomes == 1290 and csv_ok and a3_ok,
          f"comparação={ok_cmp} nomes={n_nomes} csv={csv_ok} A3={a3_ok} | "
          + " ; ".join(r for r in rel if not r.startswith("  DIF"))[:300] + ("" if ok_cmp else " | " + " ; ".join(rel[:6])))


def tc_002(c43: dict, c44: dict, nomes44: dict) -> None:
    exc = {(a["aba"], a["cel"]): a for a in g.alteracoes()}
    trocas, erros, n_exc_ok, n_form = 0, [], 0, 0
    for chave in sorted(set(c43) | set(c44)):
        aba, cel = chave
        a, b = c43.get(chave), c44.get(chave)
        if chave in exc:
            e = exc[chave]
            if texto(b) == texto(e["novo"]) and texto(a) == texto(e["antes"]):
                n_exc_ok += 1
            else:
                erros.append(f"exceção {aba}!{cel} fora do antes/novo")
            continue
        if texto(a) == texto(b):
            continue
        ta, tb = (tokens(a), tokens(b)) if aba in ABAS_03_A_14 else (None, None)
        if ta is None or tb is None or len(ta) != len(tb):
            erros.append(f"{aba}!{cel}: difere fora da regra ({str(a)[:40]!r} -> {str(b)[:40]!r})")
            continue
        if isinstance(a, ArrayFormula) != isinstance(b, ArrayFormula) or (isinstance(a, ArrayFormula) and a.ref != b.ref):
            erros.append(f"{aba}!{cel}: fórmula matricial mudou")
            continue
        n_form += 1
        for x, y in zip(ta, tb):
            if (x.type, x.subtype) != (y.type, y.subtype):
                erros.append(f"{aba}!{cel}: tipo de token mudou ({x.value!r} -> {y.value!r})")
            elif x.value != y.value:
                alvo = cel_unica(x.value, aba) if x.type == "OPERAND" and x.subtype == "RANGE" else None
                if alvo is not None and nomes44.get(y.value) == alvo:
                    trocas += 1
                else:
                    erros.append(f"{aba}!{cel}: {x.value!r} -> {y.value!r} fora da regra")
    check("TC-WB44-002: V4.3 (tag) x V4.4 (excel/): nas abas 03 a 14 só operando de célula única vira o nome cujo destino é "
          "essa célula; fora delas e fora das exceções X2 a X5, valor idêntico; as exceções têm o antes e o novo; "
          "2787 trocas e nenhuma diferença fora da regra",
          not erros and trocas == 2787 and n_exc_ok == len(exc),
          f"trocas={trocas} (esperado 2787) fórmulas alteradas={n_form} exceções={n_exc_ok}/{len(exc)} "
          f"fora da regra={len(erros)} {erros[:4]}")


def tc_003(wb44, c44: dict) -> None:
    nomes = set(wb44.defined_names)
    n = {"nome": 0, "propria": 0, "intervalo": 0, "coluna": 0, "solta": 0, "outro": 0}
    soltas = []
    for (aba, cel), v in c44.items():
        if aba not in ABAS_03_A_14:
            continue
        toks = tokens(v)
        if toks is None:
            continue
        for t in toks:
            if not (t.type == "OPERAND" and t.subtype == "RANGE"):
                continue
            x = t.value
            if x in nomes:
                n["nome"] += 1
            elif RE_COLUNA.match(x):
                n["coluna"] += 1
            elif RE_INTERVALO.match(x):
                n["intervalo"] += 1
            elif RE_CEL.match(x):
                m, mf = RE_CEL.match(x), RE_CEL.match(cel)
                # linha própria (spec §3.5): sem aba, mesma linha da célula, que está em H:Q da 03_TARGETS
                if aba == "03_TARGETS" and not m["aba"] and m["r"] == mf["r"] and len(mf["c"]) == 1 and "H" <= mf["c"] <= "Q":
                    n["propria"] += 1
                else:
                    n["solta"] += 1
                    soltas.append(f"{aba}!{cel}:{x}")
            else:
                n["outro"] += 1
                soltas.append(f"{aba}!{cel}:{x}?")
    ok = n["solta"] == 0 and n["outro"] == 0 and (n["propria"], n["intervalo"], n["coluna"]) == (35, 36, 4)
    check("TC-WB44-003: invariante dos nomes: nas abas 03 a 14 da V4.4, todo operando de célula única é nome (ou, na 03, a "
          "própria linha da ficha); por endereço só intervalo e coluna inteira",
          ok, f"linha própria={n['propria']} (esperado 35) intervalos={n['intervalo']} (36) colunas={n['coluna']} (4) "
              f"células soltas={n['solta']} (0) outros={n['outro']} já nome={n['nome']} {soltas[:4]}")


def tc_004(tmp: Path, v43: Path, wb43, wb44) -> None:
    n43 = {k: d.attr_text for k, d in wb43.defined_names.items()}
    n44 = {k: d.attr_text for k, d in wb44.defined_names.items()}
    perdidos = [k for k in n43 if n44.get(k) != n43[k]]
    novos = {n.nome for n in NOMES_V44}
    nomes_ok = not perdidos and not (novos & set(n43)) and novos <= set(n44) and len(n44) == len(n43) + len(novos)
    # SINTÉTICO DE TESTE: perturba todo nome de dado da V4.3 (nunca dado do carro) e migra para a V4.4 de excel/
    base = dp.ler_por_nome(v43)
    sint = {}
    for nome, v in base.items():
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            sint[nome] = round(v + 1.5, 4)   # arredondado: o openpyxl grava 15 algarismos
        elif nome.startswith("org_"):
            sint[nome] = next(o for o in origens.ORIGENS_V42 if o != v)   # opção válida diferente: o dado muda de fato
        else:
            sint[nome] = f"{v} (teste sintético)"
    viva = g.copia_v43(tmp, sint, nome="viva_sintetica_V4_3.xlsx")
    pasta = tmp / "mig"
    pasta.mkdir()
    saida, rel = pasta / "saida.xlsx", pasta / "relatorio.md"
    cod = migr_viva.migrar(viva, V44, saida, rel, pasta / "cp", referencia_antiga=v43)
    txt = rel.read_text(encoding="utf-8") if rel.exists() else ""
    escritos = dp.ler_por_nome(saida) if saida.exists() else {}
    levados = sum(1 for k, v in sint.items() if k in escritos and dp.iguais(escritos[k], v))
    sem_mudanca = sum(1 for k, v in sint.items() if dp.iguais(v, base[k]))   # sintético igual ao da V4.3: não provaria nada
    intocados = [k for k in base if k not in sint]
    intocados_ok = bool(escritos) and set(base) <= set(escritos) and all(
        k in escritos and dp.iguais(escritos[k], base[k]) for k in intocados)
    # tudo o que não foi perturbado fica igual à V4.3 (igual_ao_padrao): nomes de dado fora do conjunto sintético
    mig_ok = cod == 0 and "| Conflitos (não escritos) | 0 |" in txt and "| Faltando na versão nova | 0 |" in txt         and "Resultado: **PASS**" in txt and levados == len(sint) and sem_mudanca == 0 and intocados_ok and len(sint) > 100
    check("TC-WB44-004: migração por nome: os nomes da V4.3 existem na V4.4 com o mesmo destino e os 24 novos não existem na "
          "V4.3; viva V4.3 com valores SINTÉTICOS DE TESTE em todos os nomes de dado migra para a V4.4 com código 0, "
          "0 conflito, Faltando 0, Resultado PASS, todos os dados levados e os intocados iguais aos da V4.3",
          nomes_ok and mig_ok,
          f"nomes={nomes_ok} (perdidos/alterados {len(perdidos)}) migração código={cod} dados sintéticos levados="
          f"{levados}/{len(sint)} (sem mudança: {sem_mudanca}; intocados iguais a V4.3: {len(intocados)}={intocados_ok}; "
          "valores de teste, não do carro)")


if __name__ == "__main__":
    ok_pre = pre_checagem()
    try:
        ok_nomes = pre_checagem_nomes()
    except Exception as e:   # falha ruidosa, nunca silenciosa
        ok_nomes = False
        print(f"  nomes: {type(e).__name__}: {e}")
    print(f"Pré-checagem dos 24 nomes novos (fora da contagem): {'OK' if ok_nomes else 'FALHOU'}")
    try:
        ok_ger = pre_checagem_gerador()
    except BaseException as e:   # falha ruidosa, nunca silenciosa
        ok_ger = False
        print(f"  gerador: {type(e).__name__}: {e}")
    print(f"Pré-checagem do gerador da V4.4 (fora da contagem): {'OK' if ok_ger else 'FALHOU'}")
    ok_pre = ok_pre and ok_nomes and ok_ger
    print(f"Pré-checagem da regra da troca (fora da contagem): {'OK' if ok_pre else 'FALHOU'}")
    main()
    n_pass = sum(1 for _, s, _ in results if s == "PASS")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    print("\n--- Resumo ---")
    print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
    sys.exit(1 if (n_fail or not ok_pre) else 0)
