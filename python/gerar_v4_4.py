"""Gera a planilha V4.4 (incremento 8, parte 8b: fórmulas das abas 03 a 14 por nome, valores iguais aos da V4.3;
projeto T11) a partir da V4.3 da tag v4.3.

Uso:
    uv run python -X utf8 python/gerar_v4_4.py [--v43 ARQ] [--saida build/FSAE_EV_Suspension_Fase1_V4_4.xlsx]
                                               [--registro docs/registro-de-versoes-V4_4-celulas.md]
                                               [--nomes-csv data/nomes_V4_4.csv]

Sem --v43, o arquivo da tag v4.3 é extraído (git show, binário) para uma pasta temporária: nunca se usa a V4.3 da
árvore nem a viva do Drive. A saída nunca fica em excel/ nem por cima da origem: a recusa vem antes de abrir qualquer
arquivo; a cópia para excel/ é um commit próprio.

O que esta etapa muda em relação à V4.3 (EDR-070, EDR-066; exceções aprovadas pelo usuário em 2026-11-09, itens A1 a A3):
- 24 nomes novos (`nomes_v4_4.NOMES_V44`, data/nomes_V4_4.csv), no escopo da pasta de trabalho;
- X1, a regra da troca (`reescrita_nomes.trocar_formula`): em toda fórmula das abas 03 a 14, cada operando de célula
  única que é destino exato de um nome vira esse nome; nada mais muda no texto da fórmula;
- X2 a X5 (`alteracoes`): limitação do K (16_EQUILIBRIO F188), texto do aviso do R (14_DASHBOARD B48), versão
  (00_README A3) e linha 24 do 15_CHANGELOG. Essas células ficam fora do catálogo da regra da troca.

As demais células ficam iguais, com o mesmo texto.
"""
from __future__ import annotations

import argparse
import copy
import subprocess
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.workbook.defined_name import DefinedName

import aba_curva
import aba_equilibrio as ae
import reescrita_nomes as rn
from atualizar_planilha import escrever_registro
from nomes_v4_0 import ler_tabela
from nomes_v4_4 import NOMES_V44, conferir_tabela

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PASTA_EXCEL = RAIZ / "excel"
SAIDA_PADRAO = RAIZ / "build" / "FSAE_EV_Suspension_Fase1_V4_4.xlsx"
CSV_NOMES = RAIZ / "data" / "nomes_V4_4.csv"
TAG_V43 = "v4.3"
CAMINHO_V43 = "excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx"
REGISTRO = "docs/registro-de-versoes-V4_4-celulas.md"
LINHA_CHANGELOG = 24

TEXTO_K_V43 = ("regimes diferentes (Milliken p. 313-315): o K vale no regime linear (a_y pequeno) e o veredito, no limite. "
               "Subesterço no linear com LOOSE no limite não é erro.")
TEXTO_K_V44 = (TEXTO_K_V43 + " Limitação (EDR-066): o K não inclui o arrasto, a resistência ao rolamento nem o Fx exigido "
               "pelo balanço completo (hipóteses 10 e 9b da escada); num caso sintético, sem dado do carro, a diferença "
               "foi ΔK = +1,57 °/g. A confirmar com dados do T11.")
TRECHO_B48_V43 = "diâmetros do regulamento FSAE 2026 D.10.1.1"
TRECHO_B48_V44 = "diâmetros da 24_CURVA B5 e B6"
TEXTO_A3_V44 = ("Versão do workbook: V4.4 (incremento 8: fórmulas das abas 03 a 14 por nome, valores iguais aos da V4.3; "
                "projeto T11) | Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated")
TEXTO_CHANGELOG = (
    "2026-11",
    "V4.4, fundação parte 2 (incremento 8): as fórmulas das abas 03 a 14 leem por nome toda célula única (24 nomes "
    "novos, data/nomes_V4_4.csv), com valores iguais aos da V4.3 (TC-WB44-005); aviso do R na 14_DASHBOARD B48 cita os "
    "diametros da 24_CURVA; limitacao do K na 16_EQUILIBRIO F188. Gerada da tag v4.3 por python/gerar_v4_4.py.",
    "EDR-070, EDR-066. Registro celula a celula: " + REGISTRO + ". NOT_VALIDATED fisicamente.")


def extrair_v43(pasta: Path) -> Path:
    """Arquivo da tag v4.3 numa pasta (binário, `git show`); nunca a V4.3 da árvore nem a viva."""
    destino = Path(pasta) / "V4_3_tag.xlsx"
    destino.write_bytes(subprocess.run(["git", "show", f"{TAG_V43}:{CAMINHO_V43}"], cwd=RAIZ, capture_output=True,
                                       check=True).stdout)
    return destino


def _recusar(caminho_v43: Path, saida: Path) -> None:
    """Recusa saída dentro de excel/ ou igual à origem. Só compara caminhos: não abre nenhum arquivo."""
    s = saida.resolve()
    if s == Path(caminho_v43).resolve():
        raise SystemExit(f"saída igual à origem: recusado ({saida})")
    if s.parent == PASTA_EXCEL.resolve() or PASTA_EXCEL.resolve() in s.parents:
        raise SystemExit(f"saída em excel/ recusada ({saida}): gere em build/ ou numa pasta temporária; a cópia "
                         "para excel/ é um passo à parte, num commit próprio")


def alteracoes() -> list[dict]:
    """As exceções X2 a X5 (A3): [{aba, cel, antes, novo, motivo, edr}]. `antes` é o texto da V4.3 (None = célula vazia)."""
    antes_b48 = aba_curva.TEXTO_B48.format_map(aba_curva.mapa_v43())
    if antes_b48.count(TRECHO_B48_V43) != 1:
        raise ValueError("o trecho dos diâmetros do regulamento tem de aparecer uma vez no aviso da B48")
    novo_b48 = antes_b48.replace(TRECHO_B48_V43, TRECHO_B48_V44)
    out = [
        {"aba": "16_EQUILIBRIO", "cel": "F188", "antes": TEXTO_K_V43, "novo": TEXTO_K_V44,
         "motivo": "X2: limitação do K (pendência 13)", "edr": "EDR-066"},
        {"aba": "14_DASHBOARD", "cel": "B48", "antes": antes_b48, "novo": novo_b48,
         "motivo": "X3: o texto valia só enquanto B5 e B6 fossem os do regulamento (pendência 6)", "edr": "EDR-066"},
        {"aba": "00_README", "cel": "A3", "antes": aba_curva.TEXTO_A3, "novo": TEXTO_A3_V44,
         "motivo": "X4: versão", "edr": "EDR-070"},
    ]
    for col, novo in zip("ABC", TEXTO_CHANGELOG):
        out.append({"aba": "15_CHANGELOG", "cel": f"{col}{LINHA_CHANGELOG}", "antes": None, "novo": novo,
                    "motivo": "X5: changelog", "edr": "EDR-070"})
    return out


def acrescentar_nomes(wb) -> None:
    """Os 24 nomes novos no escopo da pasta de trabalho; recusa nome já existente."""
    existentes = set(wb.defined_names)
    for n in NOMES_V44:
        if n.nome in existentes:
            raise ValueError(f"nome já definido: {n.nome}")
        existentes.add(n.nome)
        col = "".join(ch for ch in n.celula if ch.isalpha())
        wb.defined_names[n.nome] = DefinedName(n.nome, attr_text=f"'{n.aba}'!${col}${n.celula[len(col):]}")


def montar_v44(wb) -> tuple[list[dict], list[dict]]:
    """Workbook da V4.3 (aberto, da tag v4.3) -> V4.4 em memória: os 24 nomes, a regra da troca (X1) nas fórmulas das
    abas 03 a 14 que não são exceção, e as exceções X2 a X5. Devolve (catálogo [{aba, cel, v43, v44}] das reescritas,
    registro das exceções [{aba, cel, antes, novo, ref}]). Não salva.

    As exceções que estão numa aba-alvo (a B48 da 14_DASHBOARD) recebem a regra da troca depois do texto da exceção,
    para cumprirem o invariante e a exceção; na V4.3 a B48 já lê tudo por nome, então a regra não muda nada nela."""
    exc = alteracoes()
    exc_cel = {(a["aba"], a["cel"]) for a in exc}
    acrescentar_nomes(wb)
    destinos = rn.destinos_unicos(wb)
    catalogo = []
    for ws in wb.worksheets:
        if ws.title not in rn.ABAS_ALVO:
            continue
        for lin in ws.iter_rows():
            for c in lin:
                if (ws.title, c.coordinate) in exc_cel or not (isinstance(c.value, str) and c.value.startswith("=")):
                    continue
                novo = rn.trocar_formula(c.value, ws.title, destinos, c.coordinate)
                if novo != c.value:
                    catalogo.append({"aba": ws.title, "cel": c.coordinate, "v43": c.value, "v44": novo})
                    c.value = novo
    registro = []
    for a in exc:
        c = wb[a["aba"]][a["cel"]]
        if c.value != a["antes"]:
            raise ValueError(f"{a['aba']}!{a['cel']}: a origem não é a V4.3 esperada ({c.value!r} != {a['antes']!r})")
        novo = a["novo"]
        if a["aba"] in rn.ABAS_ALVO:
            novo = rn.trocar_formula(novo, a["aba"], destinos, a["cel"])
        c.value = novo
        registro.append({"aba": a["aba"], "cel": a["cel"], "antes": a["antes"], "novo": novo,
                         "ref": f"{a['motivo']}; {a['edr']}"})
    ch = wb["15_CHANGELOG"]
    for col in "ABCDE":
        ch[f"{col}{LINHA_CHANGELOG}"]._style = copy.copy(ch[f"{col}{LINHA_CHANGELOG - 1}"]._style)
    wb.calculation.fullCalcOnLoad = True
    return catalogo, registro


INTRO_REGISTRO = (
    "# Registro de células da V4.4 (gerado por python/gerar_v4_4.py)\n\n"
    "Gerado por `python/gerar_v4_4.py` da tag `v4.3`; não edite à mão (regere com `uv run python -X utf8 "
    f"python/gerar_v4_4.py --registro {REGISTRO}`). A primeira tabela lista toda fórmula das abas 03 a 14 que a regra da "
    "troca (EDR-070) reescreve: cada operando de célula única que é destino exato de um nome vira esse nome, e nada mais "
    "muda no texto. A segunda tabela traz as exceções X2 a X5 (limitação do K, aviso do R, versão e changelog), que "
    "ficam fora da primeira. As demais células ficam iguais às da V4.3.\n\n"
    "## Fórmulas reescritas pela regra da troca\n\n")


def _cel_md(v: str) -> str:
    return "`" + v.replace("|", "\\|") + "`"


def escrever_registro_v44(catalogo: list[dict], registro: list[dict], caminho: Path) -> None:
    """Catálogo em Markdown (introdução fixa, tabela `Aba | Célula | V4.3 | V4.4`, tabela das exceções), LF."""
    caminho = Path(caminho)
    linhas = ["| Aba | Célula | V4.3 | V4.4 |", "|---|---|---|---|"]
    linhas += [f"| {r['aba']} | {r['cel']} | {_cel_md(r['v43'])} | {_cel_md(r['v44'])} |" for r in catalogo]
    with tempfile.TemporaryDirectory(prefix="dds_reg44_") as tmp:
        excecoes = Path(tmp) / "exc.md"
        escrever_registro(registro, excecoes)
        texto_exc = excecoes.read_text(encoding="utf-8")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(INTRO_REGISTRO + "\n".join(linhas) + "\n\n## Exceções X2 a X5\n\n" + texto_exc,
                       encoding="utf-8", newline="\n")


def gerar(v43: Path | None, saida: Path, registro: Path | None = None,
          csv_nomes: Path | None = None) -> tuple[list[dict], list[dict]]:
    """Abre a V4.3 (`v43`, ou a extraída da tag v4.3), aplica `montar_v44` e grava `saida`. Com `registro`, grava também
    o catálogo (.md). A tabela de nomes lida de `csv_nomes` (padrão data/nomes_V4_4.csv) tem de ser `NOMES_V44`
    (ValueError, antes de abrir a planilha). A recusa de `saida` vem antes de abrir qualquer arquivo."""
    saida = Path(saida)
    with tempfile.TemporaryDirectory(prefix="dds_v44_") as tmp:
        if v43 is None:
            _recusar(Path(tmp) / "V4_3_tag.xlsx", saida)
            origem = extrair_v43(Path(tmp))
        else:
            _recusar(Path(v43), saida)
            origem = Path(v43)
        conferir_tabela(ler_tabela(csv_nomes or CSV_NOMES))
        wb = openpyxl.load_workbook(origem)
        try:
            catalogo, excecoes = montar_v44(wb)
            saida.parent.mkdir(parents=True, exist_ok=True)
            wb.save(saida)
        finally:
            wb.close()
    if registro is not None:
        escrever_registro_v44(catalogo, excecoes, Path(registro))
    return catalogo, excecoes


def _copia(tmp: Path, montar, alteracoes_: dict | None, nome: str) -> Path:
    tmp = Path(tmp)
    saida = (tmp / nome).resolve()
    _recusar(tmp / "V4_3_tag.xlsx", saida)
    wb = openpyxl.load_workbook(extrair_v43(tmp))
    try:
        if montar is not None:
            montar(wb)
        for nome_def, valor in (alteracoes_ or {}).items():
            aba, cel = ae._destino(wb, nome_def)
            wb[aba][cel].value = valor
        wb.calculation.fullCalcOnLoad = True
        wb.save(saida)
    finally:
        wb.close()
    return saida


def copia_v43(tmp: Path, alteracoes: dict | None = None, nome: str = "V4_3_copia.xlsx") -> Path:
    """Helper de teste: a V4.3 da tag v4.3 + `alteracoes` (nome definido -> valor; None esvazia a célula), gravada em
    `tmp/nome`. Os valores de teste ficam só nessa cópia. Recusa caminho em excel/."""
    return _copia(tmp, None, alteracoes, nome)


def copia_v44(tmp: Path, alteracoes: dict | None = None, nome: str = "V4_4_copia.xlsx") -> Path:
    """Helper de teste: a V4.4 como o gerador a monta (V4.3 da tag + `montar_v44`) + `alteracoes` (por nome)."""
    return _copia(tmp, montar_v44, alteracoes, nome)


def main() -> None:
    p = argparse.ArgumentParser(description="Gera a V4.4 (fórmulas das abas 03 a 14 por nome) da V4.3 da tag v4.3.")
    p.add_argument("--v43", type=Path, default=None, help="arquivo da V4.3 (padrão: extraído da tag v4.3)")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    p.add_argument("--registro", type=Path, default=None, help="catálogo célula a célula (.md)")
    p.add_argument("--nomes-csv", type=Path, default=None, help="CSV dos nomes novos (padrão data/nomes_V4_4.csv)")
    a = p.parse_args()
    gerar(a.v43, a.saida, a.registro, csv_nomes=a.nomes_csv)
    print(f"salvo {a.saida}")


if __name__ == "__main__":
    main()
