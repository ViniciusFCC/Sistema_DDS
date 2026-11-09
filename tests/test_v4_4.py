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


def main():
    pass


if __name__ == "__main__":
    ok_pre = pre_checagem()
    print(f"Pré-checagem da regra da troca (fora da contagem): {'OK' if ok_pre else 'FALHOU'}")
    main()
    n_pass = sum(1 for _, s, _ in results if s == "PASS")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    print("\n--- Resumo ---")
    print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
    sys.exit(1 if (n_fail or not ok_pre) else 0)
