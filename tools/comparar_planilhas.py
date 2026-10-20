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
                  esperadas: int = FORMULAS_ESPERADAS) -> tuple[bool, list[str]]:
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
