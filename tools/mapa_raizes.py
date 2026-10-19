"""Mapa de raízes da planilha V3.0: para cada fórmula, as entradas de que ela depende e a pior origem entre elas.

Refaz, a partir das fórmulas e da coluna Origem atuais (EDR-035), o mapa da auditoria V2.1
(data/placeholder-dependency-map-V2.1.csv), que não conhece as fórmulas da V3.0. É a base da fase 2 do FB-03
(pior origem ao vivo no 14_DASHBOARD, aprovada pelo usuário em 2026-10-19 e gerada por atualizar_planilha.py).

Uso:
    uv run python -X utf8 tools/mapa_raizes.py [V3_0.xlsx] [--saida data/placeholder-dependency-map-V3.0.csv]

Regras e ordem de "pior origem": python/raizes.py (a mesma lógica gera a coluna de pior origem do 14_DASHBOARD).
O CSV guarda também o tier e a contagem por rótulo.
"""
import argparse
import csv
import sys
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))
from raizes import PIOR_PRIMEIRO, SEM_ROTULO, TIER, Grafo, chave, linha, origem_da_raiz  # noqa: E402
from atualizar_planilha import TX  # noqa: E402


def mapa(caminho: Path) -> list[dict]:
    wb = openpyxl.load_workbook(caminho)
    g = Grafo(wb)
    linhas = []
    for (aba, cel), f in sorted(g.formulas.items(), key=lambda kv: chave(kv[0])):
        todas = sorted(g.raizes((aba, cel)), key=chave)
        vazias = [x for x in todas if wb[x[0]][x[1]].value is None]
        rz = g.raizes_preenchidas((aba, cel))
        org = {x: origem_da_raiz(wb, *x) for x in rz}
        rotuladas = [o for o in org.values() if o != SEM_ROTULO]
        pior = next((o for o in PIOR_PRIMEIRO if o in rotuladas), "")
        linhas.append({
            "sheet": aba, "cell": cel, "label": wb[aba][f"A{linha(cel)}"].value or "",
            "pior_origem": pior, "tier_pior": TIER.get(pior, ""), "n_raizes": len(rz),
            **{f"n_{o}": rotuladas.count(o) for o in PIOR_PRIMEIRO},
            "n_sem_rotulo": len(rz) - len(rotuladas),
            "raizes_nao_TX": "; ".join(f"{a}!{c}[{org[(a, c)]}]" for a, c in rz if org[(a, c)] not in (TX, SEM_ROTULO)),
            "raizes_sem_rotulo": "; ".join(f"{a}!{c}" for a, c in rz if org[(a, c)] == SEM_ROTULO),
            "refs_vazias": "; ".join(f"{a}!{c}" for a, c in vazias),
            "refs_coluna_inteira": "; ".join(g.colunas.get((aba, cel), [])),
            "formula": f,
        })
    return linhas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("planilha", nargs="?", default=str(RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V3_0.xlsx"))
    ap.add_argument("--saida", default=str(RAIZ / "build" / "placeholder-dependency-map-V3.0.csv"))
    a = ap.parse_args()
    linhas = mapa(Path(a.planilha))
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    with open(a.saida, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    print("fórmulas", len(linhas), "->", a.saida)


if __name__ == "__main__":
    main()
