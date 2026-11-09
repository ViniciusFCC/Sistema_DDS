"""Testes da V4.4 (incremento 8, parte 8b: fórmulas das abas 03 a 14 por nome, valores iguais aos da V4.3).
Uso: uv run python -X utf8 tests/test_v4_4.py
Namespace TC-WB44-xxx (IDs autorizados: 001 a 006). Neste momento só há o esqueleto e a pré-checagem pura da regra da
troca (`reescrita_nomes.trocar_formula`, `destinos_unicos`), impressa fora da contagem; os TC entram no Task 14.
"Passou" = estrutura e regeneração conferidas; não é validação física.
"""
import sys

import openpyxl
from openpyxl.workbook.defined_name import DefinedName

import reescrita_nomes as rn

results = []
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


def main():
    pass


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
