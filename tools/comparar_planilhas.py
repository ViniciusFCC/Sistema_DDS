"""CA-07 e CA-08: compara a planilha e o layout regenerados com os entregues.

Uso:
    uv run python -X utf8 tools/comparar_planilhas.py GERADA.xlsx GERADO_layout.json

CA-07: mesmas abas, na mesma ordem; em cada célula, o texto da fórmula é
idêntico, e nas células sem fórmula o valor é igual. A V2.4 entregue deve ter
347 fórmulas. Todas as diferenças são listadas (o esperado é nenhuma).
CA-08: o JSON regenerado é igual ao entregue (data/layout_V2_4.json).
Só lê os arquivos; nunca salva nenhuma planilha.
"""
import json
import sys
from pathlib import Path

import openpyxl
from openpyxl.worksheet.formula import ArrayFormula

RAIZ = Path(__file__).resolve().parent.parent
ENTREGUE_XLSX = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V2_4.xlsx"
ENTREGUE_JSON = RAIZ / "data" / "layout_V2_4.json"
FORMULAS_ESPERADAS = 347  # SPEC CA-07
# V3.0 (EDR-045 a EDR-049): gerada da V2.4 por python/atualizar_planilha.py; 9 fórmulas novas.
ENTREGUE_XLSX_V30 = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V3_0.xlsx"
FORMULAS_ESPERADAS_V30 = 387  # 356 + 6 da 1ª rodada de feedback (EDR-050) + 19 (pior origem no 14_DASHBOARD) e 6 (direção, EDR-052) da 2ª rodada da revisão metodológica
# V4.0 (incremento 3, EDR-058): gerada da tag v3.0 por python/gerar_v4_0.py; só acrescenta nomes definidos.
ENTREGUE_XLSX_V40 = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_0.xlsx"
FORMULAS_ESPERADAS_V40 = FORMULAS_ESPERADAS_V30  # nenhuma fórmula muda na V4.0


def _formula(v) -> str | None:
    """Texto da fórmula da célula, ou None se a célula não tiver fórmula."""
    if isinstance(v, ArrayFormula):
        return f"{{{v.ref}}}{v.text}"
    if isinstance(v, str) and v.startswith("="):
        return v
    return None


def celulas(caminho: Path) -> tuple[list[str], dict[tuple[str, str], object]]:
    wb = openpyxl.load_workbook(caminho, data_only=False)
    out = {}
    for ws in wb.worksheets:
        for linha in ws.iter_rows():
            for c in linha:
                if c.value is not None:
                    out[(ws.title, c.coordinate)] = c.value
    return wb.sheetnames, out


def comparar_xlsx(gerada: Path, entregue: Path = ENTREGUE_XLSX,
                  esperadas: int = FORMULAS_ESPERADAS, estrutura: bool = False) -> tuple[bool, list[str]]:
    """CA-07: gerada x entregue, célula a célula. Com `estrutura=True` (CA-07 da V4.0), compara também os nomes
    definidos, as validações de dados, a formatação condicional e as colunas ocultas (`_estrutura`)."""
    rel = []
    abas_e, ent = celulas(entregue)
    abas_g, ger = celulas(gerada)
    ok = True
    if abas_e != abas_g:
        rel.append(f"FAIL: abas diferem\n  entregue: {abas_e}\n  gerada:   {abas_g}")
        ok = False
    n_form_e = sum(1 for v in ent.values() if _formula(v) is not None)
    n_form_g = sum(1 for v in ger.values() if _formula(v) is not None)
    rel.append(f"fórmulas: entregue {n_form_e} | gerada {n_form_g} | esperado {esperadas}")
    if n_form_e != esperadas or n_form_g != esperadas:
        rel.append("FAIL: número de fórmulas diferente do esperado")
        ok = False
    difs = []
    for chave in sorted(set(ent) | set(ger)):
        ve, vg = ent.get(chave), ger.get(chave)
        fe, fg = _formula(ve), _formula(vg)
        if fe is not None or fg is not None:
            if fe != fg:
                difs.append(f"{chave[0]}!{chave[1]} fórmula: entregue={fe!r} gerada={fg!r}")
        elif ve != vg or type(ve) is not type(vg):
            extra = ""
            if isinstance(ve, (int, float)) and isinstance(vg, (int, float)):
                extra = f" (dif={vg - ve:.3e})"
            difs.append(f"{chave[0]}!{chave[1]} valor: entregue={ve!r} gerada={vg!r}{extra}")
    if estrutura:
        difs.extend(_difs_estrutura(_estrutura(entregue), _estrutura(gerada), "entregue", "gerada"))
    rel.append(f"células comparadas: {len(set(ent) | set(ger))} | diferenças: {len(difs)}")
    rel.extend(f"  DIF {d}" for d in difs)
    if difs:
        ok = False
    rel.append("CA-07 PASS" if ok else "CA-07 FAIL")
    return ok, rel


ROTULOS_ORIGEM = ("● Dado do TX", "◐ Dado do T09", "◐ Provisório (.tir TTC)", "○ Estimativa",
                  "○ Arbitrário / demonstrativo", "? A confirmar")


def _estrutura(caminho: Path) -> dict:
    """Validações de dados, formatação condicional, nomes definidos e colunas ocultas, normalizados para a forma que
    o Excel grava ao salvar (lista "=Origens" vira "Origens"; colunas G e H ocultas viram a faixa G:H)."""
    from openpyxl.utils import get_column_letter
    wb = openpyxl.load_workbook(caminho)
    out = {"nomes": {n: d.attr_text for n, d in wb.defined_names.items()}}
    for ws in wb.worksheets:
        dv = sorted((" ".join(sorted(str(v.sqref).split())), (v.formula1 or "").lstrip("=")) for v in ws.data_validations.dataValidation)
        cf = sorted((str(k.sqref), tuple(sorted(str(r.formula) for r in v))) for k, v in ws.conditional_formatting._cf_rules.items())
        ocultas = sorted({get_column_letter(i) for d in ws.column_dimensions.values() if d.hidden
                          for i in range(d.min or 1, (d.max or d.min or 1) + 1)})
        out[ws.title] = {"validação": dv, "formatação condicional": cf, "colunas ocultas": ocultas}
    return out


def _difs_estrutura(ea: dict, eb: dict, rotulo_a: str, rotulo_b: str) -> list[str]:
    """Diferenças entre duas saídas de `_estrutura`: nomes (um a um) e, por aba, cada campo que difere."""
    difs = []
    na, nb = ea.get("nomes", {}), eb.get("nomes", {})
    for n in sorted(set(na) | set(nb)):
        if na.get(n) != nb.get(n):
            difs.append(f"nome definido {n}: {rotulo_a}={na.get(n)!r} {rotulo_b}={nb.get(n)!r}")
    for k in sorted((set(ea) | set(eb)) - {"nomes"}):
        if ea.get(k) != eb.get(k):
            for campo in sorted(set(ea.get(k, {})) | set(eb.get(k, {}))):
                if ea.get(k, {}).get(campo) != eb.get(k, {}).get(campo):
                    difs.append(f"{k}: {campo} difere ({rotulo_a} x {rotulo_b})")
    return difs


def comparar_v40(v40: Path, v30: Path, alteradas: set[tuple[str, str]],
                 nomes: dict[str, str] | None = None,
                 esperadas: int = FORMULAS_ESPERADAS_V40) -> tuple[bool, list[str]]:
    """V4.0 x V3.0 da tag (incremento 3, EDR-058): mesmas abas na mesma ordem; fórmulas com texto idêntico em todas as
    células (`esperadas` nas duas); valores iguais fora de `alteradas` (as células de `gerar_v4_0.alteracoes_v4_0()`);
    validações, formatação condicional e colunas ocultas iguais. Nomes definidos: os da V3.0 ficam iguais; com `nomes`
    ({nome: destino}), a V4.0 tem exatamente os da V3.0 mais esses. Só lê os arquivos."""
    rel, ok = [], True
    abas_3, c3 = celulas(v30)
    abas_4, c4 = celulas(v40)
    if abas_3 != abas_4:
        rel.append(f"FAIL: abas diferem\n  V3.0: {abas_3}\n  V4.0: {abas_4}")
        ok = False
    n3 = sum(1 for v in c3.values() if _formula(v) is not None)
    n4 = sum(1 for v in c4.values() if _formula(v) is not None)
    rel.append(f"fórmulas: V3.0 {n3} | V4.0 {n4} | esperado {esperadas}")
    if n3 != esperadas or n4 != esperadas:
        rel.append("FAIL: número de fórmulas diferente do esperado")
        ok = False
    difs = []
    for chave in sorted(set(c3) | set(c4)):
        v3, v4 = c3.get(chave), c4.get(chave)
        f3, f4 = _formula(v3), _formula(v4)
        if f3 is not None or f4 is not None:
            if f3 != f4:
                difs.append(f"{chave[0]}!{chave[1]} fórmula: V3.0={f3!r} V4.0={f4!r}")
        elif chave not in alteradas and (v3 != v4 or type(v3) is not type(v4)):
            difs.append(f"{chave[0]}!{chave[1]} valor (fora das alteradas): V3.0={v3!r} V4.0={v4!r}")
    e3, e4 = _estrutura(v30), _estrutura(v40)
    n_nomes = len(e4["nomes"])
    if nomes is not None:
        e3 = {**e3, "nomes": {**e3["nomes"], **nomes}}
    else:
        e4 = {**e4, "nomes": {k: v for k, v in e4["nomes"].items() if k in e3["nomes"]}}
    difs.extend(_difs_estrutura(e3, e4, "esperado", "V4.0"))
    rel.append(f"células comparadas: {len(set(c3) | set(c4))} (alteradas: {len(alteradas)}) | nomes na V4.0: "
               f"{n_nomes} | diferenças: {len(difs)}")
    rel.extend(f"  DIF {d}" for d in difs)
    if difs:
        ok = False
    rel.append("V4.0 x V3.0 PASS" if ok else "V4.0 x V3.0 FAIL")
    return ok, rel


def comparar_viva(viva: Path, referencia: Path, entradas: set[tuple[str, str]],
                  esperadas: int = FORMULAS_ESPERADAS_V30) -> tuple[bool, list[str]]:
    """CA-07, planilha viva (EDR-051, fechamento da V3.0): tudo igual à referência (a V3.0 da tag) menos as células de
    entrada, que a equipe preenche. Nas entradas, a Origem tem de ser um dos 6 rótulos (ou vazia) e o valor de uma
    entrada numérica não pode virar fórmula. Confere também validações, formatação condicional, nomes e colunas ocultas.
    Só lê os arquivos."""
    rel, ok = [], True
    abas_r, ref = celulas(referencia)
    abas_v, viv = celulas(viva)
    if abas_r != abas_v:
        rel.append(f"FAIL: abas diferem\n  referência: {abas_r}\n  viva:       {abas_v}")
        ok = False
    n_form = sum(1 for v in viv.values() if _formula(v) is not None)
    rel.append(f"fórmulas: viva {n_form} | esperado {esperadas}")
    if n_form != esperadas:
        rel.append("FAIL: número de fórmulas diferente do esperado")
        ok = False
    difs = []
    for chave in sorted(set(ref) | set(viv)):
        vr, vv = ref.get(chave), viv.get(chave)
        if chave in entradas:
            if _formula(vv) is not None and _formula(vr) is None:
                difs.append(f"{chave[0]}!{chave[1]} entrada virou fórmula: {vv!r}")
            continue
        fr, fv = _formula(vr), _formula(vv)
        if fr is not None or fv is not None:
            if fr != fv:
                difs.append(f"{chave[0]}!{chave[1]} fórmula: referência={fr!r} viva={fv!r}")
        elif vr != vv or type(vr) is not type(vv):
            difs.append(f"{chave[0]}!{chave[1]} estrutura (fora das entradas): referência={vr!r} viva={vv!r}")
    origens = {c for c in entradas if c[1][0] in "EI" and c[0] != "03_TARGETS"}
    for chave in sorted(origens):
        v = viv.get(chave)
        if isinstance(ref.get(chave), str) and ref[chave] in ROTULOS_ORIGEM and v is not None and v not in ROTULOS_ORIGEM:
            difs.append(f"{chave[0]}!{chave[1]} origem fora da lista: {v!r}")
    er, ev = _estrutura(referencia), _estrutura(viva)
    for k in sorted(set(er) | set(ev)):
        if er.get(k) != ev.get(k):
            if k == "nomes":
                difs.append(f"nomes definidos: referência={er.get(k)} viva={ev.get(k)}")
            else:
                for campo in er.get(k, {}):
                    if er[k][campo] != ev.get(k, {}).get(campo):
                        difs.append(f"{k}: {campo} difere da referência")
    rel.append(f"células comparadas: {len(set(ref) | set(viv))} (entradas livres: {len(entradas)}) | diferenças: {len(difs)}")
    rel.extend(f"  DIF {d}" for d in difs)
    if difs:
        ok = False
    rel.append("CA-07 (viva) PASS" if ok else "CA-07 (viva) FAIL")
    return ok, rel


def _diff_json(a, b, caminho: str, out: list[str]) -> None:
    if type(a) is not type(b):
        out.append(f"{caminho}: tipo {type(a).__name__} != {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{caminho}.{k}: só em {'gerado' if k not in a else 'entregue'}")
            else:
                _diff_json(a[k], b[k], f"{caminho}.{k}", out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{caminho}: tamanho {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            _diff_json(x, y, f"{caminho}[{i}]", out)
    elif a != b:
        extra = f" (dif={b - a:.3e})" if isinstance(a, float) else ""
        out.append(f"{caminho}: entregue={a!r} gerado={b!r}{extra}")


def comparar_json(gerado: Path) -> tuple[bool, list[str]]:
    a = json.loads(ENTREGUE_JSON.read_text(encoding="utf-8"))
    b = json.loads(gerado.read_text(encoding="utf-8"))
    difs: list[str] = []
    _diff_json(a, b, "$", difs)
    rel = [f"diferenças no layout: {len(difs)}"] + [f"  DIF {d}" for d in difs]
    ok = not difs
    rel.append("CA-08 PASS" if ok else "CA-08 FAIL")
    return ok, rel


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    ok7, r7 = comparar_xlsx(Path(sys.argv[1]))
    ok8, r8 = comparar_json(Path(sys.argv[2]))
    print("\n".join(r7 + r8))
    sys.exit(0 if ok7 and ok8 else 1)


if __name__ == "__main__":
    main()
