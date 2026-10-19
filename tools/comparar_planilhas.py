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
FORMULAS_ESPERADAS_V30 = 381  # 356 + 6 da 1ª rodada de feedback (EDR-050) + 19 da 2ª rodada da revisão metodológica (pior origem no 14_DASHBOARD)


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
