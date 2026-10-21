"""Gera a planilha V4.0 (incremento 3, fundação: nomes definidos) a partir da V3.0 da tag v3.0.

Uso:
    uv run python -X utf8 python/gerar_v4_0.py [--v30 ARQ] [--saida build/FSAE_EV_Suspension_Fase1_V4_0.xlsx]
                                               [--registro docs/registro-de-versoes-V4_0-celulas.md]

Sem --v30, o arquivo da tag v3.0 é extraído (git show, binário) para uma pasta temporária: nunca se usa a V3.0 da
árvore, que é a planilha viva da equipe (EDR-051). A tabela de nomes vem de data/nomes_V4_0.csv.

O que muda em relação à V3.0 (EDR-058; plano docs/superpowers/plans/2026-10-21-v4-0-inc3-fundacao-nomes.md):
- um nome definido, no escopo do workbook, para cada linha da tabela (`'aba'!$C$L`); o nome `Origens` fica;
- as células de `alteracoes_v4_0()`: a versão na 00_README A3 e a linha nova do 15_CHANGELOG.
Nenhuma fórmula muda. A saída nunca fica em excel/ nem por cima da origem: a recusa vem antes de abrir qualquer
arquivo. A V4.0 de referência é gerada em build/ e copiada para excel/ num commit próprio.
"""
from __future__ import annotations

import argparse
import copy
import subprocess
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.workbook.defined_name import DefinedName

from atualizar_planilha import escrever_registro
from nomes_v4_0 import Nome, _partes, ler_tabela

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PASTA_EXCEL = RAIZ / "excel"
TAG_V30 = "v3.0"
CAMINHO_V30 = "excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx"
SAIDA_PADRAO = RAIZ / "build" / "FSAE_EV_Suspension_Fase1_V4_0.xlsx"
CSV_NOMES = RAIZ / "data" / "nomes_V4_0.csv"
PLANO = "docs/superpowers/plans/2026-10-21-v4-0-inc3-fundacao-nomes.md"
REF = "EDR-058; " + PLANO

TEXTO_A3 = ("Versão do workbook: V4.0 (fundação: nomes definidos; fórmulas iguais à V3.0) "
            "| Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated")
LINHA_CHANGELOG = 20   # primeira linha livre do 15_CHANGELOG na V3.0 da tag (a 19 é o fechamento da V3.0)


def alteracoes_v4_0() -> list[dict]:
    """Células que a V4.0 muda em relação à V3.0, com o texto novo e a referência. Fora delas, tudo igual."""
    lin = LINHA_CHANGELOG
    return [
        {"aba": "00_README", "cel": "A3", "novo": TEXTO_A3, "ref": REF},
        {"aba": "15_CHANGELOG", "cel": f"A{lin}", "novo": "2026-10", "ref": REF},
        {"aba": "15_CHANGELOG", "cel": f"B{lin}",
         "novo": ("V4.0, fundacao (incremento 3): nomes definidos no workbook para cada entrada, Origem, Fonte e "
                  "resultado (data/nomes_V4_0.csv); formulas iguais as 387 da V3.0. Gerada da tag v3.0 por "
                  "python/gerar_v4_0.py."),
         "ref": REF},
        {"aba": "15_CHANGELOG", "cel": f"C{lin}",
         "novo": ("EDR-058 (fonte de verdade da V4.0: gerada da tag v3.0; dados da equipe migram por chave). Plano: "
                  f"{PLANO}. Registro celula a celula: docs/registro-de-versoes-V4_0-celulas.md. "
                  "NOT_VALIDATED fisicamente."),
         "ref": REF},
    ]


def _destino(n: Nome) -> str:
    col, lin = _partes(n.celula)
    return f"'{n.aba}'!${col}${lin}"


def _recusar(caminho_v30: Path, saida: Path) -> None:
    """Recusa saída dentro de excel/ ou igual à origem. Só compara caminhos: não abre nenhum arquivo."""
    s = saida.resolve()
    if s == caminho_v30.resolve():
        raise SystemExit(f"saída igual à origem: recusado ({saida})")
    if s.parent == PASTA_EXCEL.resolve() or PASTA_EXCEL.resolve() in s.parents:
        raise SystemExit(f"saída em excel/ recusada ({saida}): gere em build/ ou numa pasta temporária; a cópia "
                         "para excel/ é um passo à parte, num commit próprio")


def gerar(caminho_v30: Path, saida: Path, tabela: list[Nome]) -> list[dict]:
    """Copia a V3.0, acrescenta os nomes definidos (escopo do workbook), aplica `alteracoes_v4_0()` e grava `saida`.
    Devolve o registro (aba, cel, antes, novo, ref), com o "antes" lido da origem, e uma linha final de resumo dos
    nomes (aba "(workbook)")."""
    caminho_v30, saida = Path(caminho_v30), Path(saida)
    _recusar(caminho_v30, saida)
    nomes = [n.nome for n in tabela]
    if len(set(nomes)) != len(nomes):
        raise ValueError("tabela com nomes repetidos")
    wb = openpyxl.load_workbook(caminho_v30)
    try:
        existentes = list(wb.defined_names)
        repetidos = sorted(set(existentes) & set(nomes))
        if repetidos:
            raise ValueError(f"nomes já definidos na origem: {repetidos[:5]}")
        for n in tabela:
            wb.defined_names[n.nome] = DefinedName(n.nome, attr_text=_destino(n))
        registro = []
        changelog = wb["15_CHANGELOG"]
        for col in "ABCDE":   # mesma formatação da linha anterior, como na V3.0
            changelog[f"{col}{LINHA_CHANGELOG}"]._style = copy.copy(changelog[f"{col}{LINHA_CHANGELOG - 1}"]._style)
        for alt in alteracoes_v4_0():
            c = wb[alt["aba"]][alt["cel"]]
            antes = c.value
            if alt["aba"] == "15_CHANGELOG" and antes is not None:
                raise ValueError(f"15_CHANGELOG!{alt['cel']} já preenchida na origem: {antes!r}")
            c.value = alt["novo"]
            registro.append({**alt, "antes": antes})
        registro.append({"aba": "(workbook)", "cel": "nomes definidos", "antes": ", ".join(existentes) or None,
                         "novo": f"{len(tabela)} nomes de data/nomes_V4_0.csv acrescentados (escopo do workbook)",
                         "ref": REF})
        wb.calculation.fullCalcOnLoad = True
        saida.parent.mkdir(parents=True, exist_ok=True)
        wb.save(saida)
    finally:
        wb.close()
    return registro


def extrair_v30(pasta: Path) -> Path:
    """Arquivo da tag v3.0 numa pasta temporária (binário, sem passar por texto)."""
    destino = Path(pasta) / "V3_0_tag.xlsx"
    with open(destino, "wb") as f:
        subprocess.run(["git", "show", f"{TAG_V30}:{CAMINHO_V30}"], cwd=RAIZ, stdout=f, check=True)
    return destino


def main() -> None:
    p = argparse.ArgumentParser(description="Gera a V4.0 (nomes definidos) a partir da V3.0 da tag v3.0.")
    p.add_argument("--v30", type=Path, default=None, help="arquivo da V3.0 (padrão: extraído da tag v3.0)")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    p.add_argument("--registro", type=Path, default=None, help="registro célula a célula (.md)")
    p.add_argument("--nomes", type=Path, default=CSV_NOMES, help="tabela de nomes (CSV)")
    a = p.parse_args()
    tabela = ler_tabela(a.nomes)
    with tempfile.TemporaryDirectory() as tmp:
        if a.v30 is None:
            _recusar(Path(tmp) / "V3_0_tag.xlsx", a.saida)
            v30 = extrair_v30(Path(tmp))
        else:
            v30 = a.v30
        reg = gerar(v30, a.saida, tabela)
    if a.registro:
        escrever_registro(reg, a.registro)
    print(f"salvo {a.saida}: {len(tabela)} nomes definidos, {len(reg) - 1} células alteradas")


if __name__ == "__main__":
    main()
