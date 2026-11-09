"""Gera a planilha V4.3 (incremento 7, parte 7b: centro da curva, raio do skidpad e Fx por arrasto induzido; projeto
T11) a partir da V4.2 da tag v4.2.

Uso:
    uv run python -X utf8 python/gerar_v4_3.py [--v42 ARQ] [--saida build/FSAE_EV_Suspension_Fase1_V4_3.xlsx]
                                               [--registro docs/registro-de-versoes-V4_3-celulas.md]
                                               [--nomes-csv data/nomes_V4_3.csv]

Sem --v42, o arquivo da tag v4.2 é extraído (git show, binário) para uma pasta temporária: nunca se usa a V4.2 da
árvore nem a viva do Drive. A tabela dos nomes que a V4.3 acrescenta vem de data/nomes_V4_3.csv (a completa é a de
data/nomes_V4_0.csv, mais data/nomes_V4_1.csv, data/nomes_V4_2.csv e essa); o gerador recusa um CSV diferente de
`aba_curva.NOMES_V43`, porque as fórmulas usam esses nomes. Com --nomes-csv CAMINHO, o CSV é regravado em CAMINHO a
partir de NOMES_V43 e é esse CSV que o gerador lê.

O que esta etapa muda em relação à V4.2 (catálogo aprovado pelo usuário célula a célula em 2026-11-03; EDR-069,
EDR-066):
- aba nova `24_CURVA` no fim (`aba_curva.montar_24`; C-A, C-F1, C-F5);
- as células existentes fora das grades (`aba_curva.alteracoes_v4_3`): 16_EQUILIBRIO B9 vira fórmula (R usado), A9,
  E9, F9, B65, B78, B114, B115, B137, B138, B173, E173 e F142; o bloco "cálculo por linha" da 20_EQ_TROCA (faixa do
  NEUTRO); o aviso da 14_DASHBOARD A48:D48; a versão (00_README A3) e a linha 23 do 15_CHANGELOG;
- as colunas novas das grades (F9, `aba_equilibrio.linha_grade_v43`): nas abas 17, 18, 20a a 20d e na mini-grade da
  19, depois da última coluna de cada grade (a posição sai de `colunas_v43`; o registro diz as letras), e a troca de
  `fxr`, `fat` e `pre_R`.

As fórmulas da V4.2 que não estão no registro ficam iguais, com o mesmo texto. A saída nunca fica em excel/ nem por
cima da origem: a recusa vem antes de abrir qualquer arquivo. Nenhuma célula é protegida (sem ProtectContents e sem
hidden: C-B1).
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter as COL

import aba_curva
import aba_equilibrio as ae
from atualizar_planilha import escrever_registro
from nomes_v4_0 import escrever_tabela, ler_tabela

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
PASTA_EXCEL = RAIZ / "excel"
SAIDA_PADRAO = RAIZ / "build" / "FSAE_EV_Suspension_Fase1_V4_3.xlsx"
CSV_NOMES = RAIZ / "data" / "nomes_V4_3.csv"
TAG_V42 = "v4.2"
CAMINHO_V42 = "excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx"
REGISTRO = aba_curva.REGISTRO
REF_GRADES = "catálogo C-G e C-E2 (aprovado em 2026-11-03); EDR-066; teste: TC-WB43-001"
REF_24 = "catálogo C-A, C-F1 e C-F5 (aprovado em 2026-11-03); EDR-066 e EDR-069; teste: TC-WB43-001"


def extrair_v42(pasta: Path) -> Path:
    """Arquivo da tag v4.2 numa pasta (binário, `git show`); nunca a V4.2 da árvore nem a viva."""
    destino = Path(pasta) / "V4_2_tag.xlsx"
    destino.write_bytes(subprocess.run(["git", "show", f"{TAG_V42}:{CAMINHO_V42}"], cwd=RAIZ, capture_output=True,
                                       check=True).stdout)
    return destino


def _recusar(caminho_v42: Path, saida: Path) -> None:
    """Recusa saída dentro de excel/ ou igual à origem. Só compara caminhos: não abre nenhum arquivo."""
    s = saida.resolve()
    if s == Path(caminho_v42).resolve():
        raise SystemExit(f"saída igual à origem: recusado ({saida})")
    if s.parent == PASTA_EXCEL.resolve() or PASTA_EXCEL.resolve() in s.parents:
        raise SystemExit(f"saída em excel/ recusada ({saida}): gere em build/ ou numa pasta temporária; a cópia "
                         "para excel/ é um passo à parte, num commit próprio")


def aplicar(wb, alteracoes: list[dict]) -> list[dict]:
    """Grava `alteracoes` em `wb` (cada "antes" tem de bater com a célula) e devolve o registro (cópia das "
    "alterações)."""
    registro = []
    for alt in alteracoes:
        c = wb[alt["aba"]][alt["cel"]]
        if c.value != alt["antes"]:
            raise ValueError(f"{alt['aba']}!{alt['cel']}: a origem não é a V4.2 esperada "
                             f"({c.value!r} != {alt['antes']!r})")
        c.value = alt["novo"]
        registro.append(dict(alt))
    wb.calculation.fullCalcOnLoad = True
    return registro


def _blocos_de_grade(wb, m: dict):
    """(ws, ctx-mapa, grade, linha de dados 0, n_lin, n_alfa, cl, alfa_arq, alfa_ref, rotulo) de cada grade que recebe
    as colunas novas: 17 e 18; a pedida e a refinada de cada aba 20a a 20d (com o mapa da linha: `_mapa_linha`); e
    a mini-grade da 19."""
    blocos = []
    for aba in (ae.ABA17, ae.ABA18):
        blocos.append((wb[aba], m, aba, aba, 0))
    m20 = ae._Subst(m)
    m20.update(ae.V40_20)
    for j, aux in ae.AUX20.items():
        ml = ae._mapa_linha(m20, j)
        blocos.append((wb[aux], ml, aux, ae.ABA17, 0))
        blocos.append((wb[aux], ml, aux, ae.ABA18, ae.DESLOC_FINA20))
    saida = []
    for ws, mapa, aba, grade, d in blocos:
        passo, n_lin, n_alfa, pedida = ae.GRADES[grade]
        lim = pedida and aba == grade               # as colunas x (limitações) só na 17 principal
        ra = ae.LINHA_ALFA + d
        alfa_arq = {(roda, i): f"${COL(2 + i)}${ra + 2 + j}" for i in range(n_alfa) for j, roda in enumerate(ae.CANTOS)}
        alfa_ref = f"${COL(2)}${ra + 1}:${COL(1 + n_alfa)}${ra + 1}"
        saida.append((ws, mapa, ae._colunas(n_alfa, lim), ae.PRIMEIRA_LINHA + d, n_lin, n_alfa, alfa_arq, alfa_ref,
                      f"{aba} (grade {'pedida' if pedida else 'refinada'}, a_y = k·{passo} g)"))
    ws = wb[ae.ABA19]
    alfa17 = {(roda, i): f"'{ae.ABA17}'!${COL(2 + i)}${ae.LINHA_ALFA + 2 + j}" for i in range(ae.N_ALFA)
              for j, roda in enumerate(ae.CANTOS)}
    alfa_ref = f"'{ae.ABA17}'!$B${ae.LINHA_ALFA + 1}:${COL(1 + ae.N_ALFA)}${ae.LINHA_ALFA + 1}"
    saida.append((ws, m, ae.CL_MINI, ae.LINHA_MINI19, 3, ae.N_ALFA, alfa17, alfa_ref,
                  f"{ae.ABA19} (mini-grade, a_y = k·0,005 g)"))
    return saida


def montar_grades(wb, m: dict) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Colunas novas e trocas de `fxr`, `fat` e `pre_R` em todas as grades (`ae.linha_grade_v43`), mais o cabeçalho
    das colunas novas. Devolve (fórmulas novas [{aba, cel, familia, formula}], trocas [{aba, cel, antes, novo,
    familia}], cabeçalhos [{aba, cel, texto}], resumo por grade [{aba, cel, antes, novo, ref}] para o registro
    .md)."""
    novas: list[dict] = []
    trocas: list[dict] = []
    cabecalhos: list[dict] = []
    resumo: list[dict] = []
    for ws, mapa, cl, p0, n_lin, n_alfa, alfa_arq, alfa_ref, rotulo in _blocos_de_grade(wb, m):
        ctx = ae._Ctx(wb, novas, mapa, trocas)
        pedida = ("x", "FL", "FZMIN") in cl
        cn = ae.colunas_v43(n_alfa, pedida)
        for n, letra in cn.items():
            cel = f"{letra}{p0 - 1}"
            if ws[cel].value is not None:
                raise ValueError(f"{ws.title}!{cel} já preenchida; o cabeçalho das colunas da V4.3 só usa "
                                 "células vazias")
            ws[cel] = ae._cabecalho(n)
            cabecalhos.append({"aba": ws.title, "cel": cel, "texto": ae._cabecalho(n)})
        n0, t0 = len(novas), len(trocas)
        for k in range(n_lin):
            ae.linha_grade_v43(ctx, ws, cl, k, p0 + k, n_alfa, alfa_arq, alfa_ref)
        letras = list(cn.values())
        ex = novas[n0]
        resumo.append({
            "aba": ws.title, "cel": f"{rotulo}: {len(novas) - n0} células novas, colunas {letras[0]} a {letras[-1]} "
                                    f"(cabeçalho na linha {p0 - 1}), linhas {p0} a {p0 + n_lin - 1}", "antes": None,
            "novo": f"família F9; exemplo {ex['cel']}: {ex['formula']}", "ref": REF_GRADES})
        t = trocas[t0]
        colunas_troca = sorted({"".join(ch for ch in x["cel"] if ch.isalpha()) for x in trocas[t0:]})
        resumo.append({
            "aba": ws.title, "cel": f"{rotulo}: {len(trocas) - t0} fórmulas trocadas (fxr, fat_RL, fat_RR e pre_R), "
            "colunas "
                                    f"{', '.join(colunas_troca)}, linhas {p0} a {p0 + n_lin - 1}",
            "antes": f"exemplo {t['cel']}: {t['antes']}", "novo": f"exemplo {t['cel']}: {t['novo']}",
            "ref": REF_GRADES})
    return novas, trocas, cabecalhos, resumo


def montar_v43(wb) -> tuple[list[dict], dict, list[dict]]:
    """Workbook da V4.2 (aberto, da tag v4.2) -> V4.3 em memória: as alterações em células existentes
    (`aba_curva.alteracoes_v4_3`), a 24_CURVA, as colunas novas das grades, os estilos e os nomes da V4.3. Devolve
    (registro para o .md, células [(aba, cel) -> (antes, novo)] de toda célula que muda ou nasce fora da 24_CURVA,
    fórmulas da 24_CURVA [{aba, cel, familia, formula}]). Não salva. Usado por `gerar` e por `copia_v43`."""
    m = aba_curva.mapa_v43()
    reg = aplicar(wb, aba_curva.alteracoes_v4_3(wb, m))
    aba_curva.ajustar_estilos(wb)
    novas24 = aba_curva.montar_24(wb)
    novas, trocas, cabecalhos, resumo = montar_grades(wb, m)
    aba_curva.acrescentar_nomes(wb)
    celulas = {(a["aba"], a["cel"]): (a["antes"], a["novo"]) for a in reg}
    for novo in (*[(n["aba"], n["cel"], None, n["formula"]) for n in novas],
                 *[(t["aba"], t["cel"], t["antes"], t["novo"]) for t in trocas],
                 *[(c["aba"], c["cel"], None, c["texto"]) for c in cabecalhos]):
        if novo[:2] in celulas:
            raise ValueError(f"{novo[0]}!{novo[1]} alterada duas vezes")
        celulas[novo[:2]] = novo[2:]
    reg24 = [{"aba": n["aba"], "cel": n["cel"], "antes": None, "novo": n["formula"], "ref": REF_24} for n in novas24]
    return reg + reg24 + resumo, celulas, novas24


INTRO_REGISTRO = (
    "# Registro de células da V4.3 (gerado por python/gerar_v4_3.py)\n\n"
    "Gerado da tag v4.2; não edite à mão (regere com `uv run python -X utf8 python/gerar_v4_3.py --registro "
    f"{REGISTRO}`). Catálogo aprovado pelo usuário célula a célula em 2026-11-03. As linhas, em ordem: as células "
    f"existentes que a "
    "V4.3 muda fora das grades (16_EQUILIBRIO, 20_EQ_TROCA, 14_DASHBOARD, versão e changelog), com o texto de antes e "
    "o de depois; "
    "as fórmulas da aba nova 24_CURVA; e, por grade, as colunas novas (as letras vêm de `colunas_v43`: depois da "
    "última coluna de "
    "cada grade, então nas pedidas das abas 20a a 20d, que não têm as colunas x, elas começam antes das da 17) e as "
    "fórmulas "
    "trocadas (`fxr`, `fat_RL`, `fat_RR` e `pre_R`), com um exemplo. As demais fórmulas da V4.2 ficam iguais.\n\n")


def escrever_registro_v43(registro: list[dict], caminho: Path) -> None:
    """Registro em Markdown: a introdução e a tabela de `atualizar_planilha.escrever_registro`, LF."""
    caminho = Path(caminho)
    escrever_registro(registro, caminho)
    caminho.write_text(INTRO_REGISTRO + caminho.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def conferir_tabela(tabela: list) -> None:
    """A tabela (data/nomes_V4_3.csv) tem de ser exatamente `aba_curva.NOMES_V43`: as fórmulas usam esses nomes."""
    if list(tabela) != list(aba_curva.NOMES_V43):
        dif = sorted(n.nome for n in set(tabela) ^ set(aba_curva.NOMES_V43))[:5]
        raise ValueError(f"data/nomes_V4_3.csv difere de aba_curva.NOMES_V43 (regrave com --nomes-csv): {dif}")


def gerar(v42: Path | None, saida: Path, registro: Path | None = None, csv_nomes: Path | None = None,
          nomes: list | None = None) -> tuple[list[dict], dict, list[dict]]:
    """Abre a V4.2 (`v42`, ou a extraída da tag v4.2), aplica `montar_v43` e grava `saida`. Com `registro`, grava
    também o registro célula a célula (.md). A tabela de nomes é `nomes`, ou a lida de `csv_nomes` (padrão:
    data/nomes_V4_3.csv), e tem de ser `aba_curva.NOMES_V43` (ValueError, antes de abrir a planilha). A recusa de
    `saida` vem antes de abrir qualquer arquivo. Devolve o mesmo que `montar_v43`."""
    saida = Path(saida)
    with tempfile.TemporaryDirectory(prefix="dds_v43_") as tmp:
        if v42 is None:
            _recusar(Path(tmp) / "V4_2_tag.xlsx", saida)
            origem = extrair_v42(Path(tmp))
        else:
            _recusar(Path(v42), saida)
            origem = Path(v42)
        conferir_tabela(ler_tabela(csv_nomes or CSV_NOMES) if nomes is None else nomes)
        wb = openpyxl.load_workbook(origem)
        try:
            reg, celulas, novas24 = montar_v43(wb)
            saida.parent.mkdir(parents=True, exist_ok=True)
            wb.save(saida)
        finally:
            wb.close()
    if registro is not None:
        escrever_registro_v43(reg, Path(registro))
    return reg, celulas, novas24


def copia_v43(tmp: Path, alteracoes: dict | None = None, nome: str = "V4_3_copia.xlsx") -> Path:
    """Helper de teste: a V4.3 como o gerador a monta (V4.2 da tag v4.2 + `montar_v43`) + `alteracoes` (nome definido
    -> valor; None esvazia a célula), gravada em `tmp/nome`. Os valores de teste ficam só nessa cópia. Recusa
    caminho em excel/."""
    tmp = Path(tmp)
    saida = (tmp / nome).resolve()
    _recusar(tmp / "V4_2_tag.xlsx", saida)
    origem = extrair_v42(tmp)
    wb = openpyxl.load_workbook(origem)
    try:
        montar_v43(wb)
        for nome_def, valor in (alteracoes or {}).items():
            aba, cel = ae._destino(wb, nome_def)
            wb[aba][cel].value = valor
        wb.calculation.fullCalcOnLoad = True
        wb.save(saida)
    finally:
        wb.close()
    return saida


def main() -> None:
    p = argparse.ArgumentParser(description="Gera a V4.3 (centro da curva, R do skidpad e Fx por arrasto induzido) da "
                                            "V4.2 da tag v4.2.")
    p.add_argument("--v42", type=Path, default=None, help="arquivo da V4.2 (padrão: extraído da tag v4.2)")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    p.add_argument("--registro", type=Path, default=None, help="registro célula a célula (.md)")
    p.add_argument("--nomes-csv", type=Path, default=None,
                   help="regrava a tabela de nomes da V4.3 (CSV) em CAMINHO, a partir de aba_curva.NOMES_V43, e gera "
                        "lendo esse CSV")
    a = p.parse_args()
    if a.nomes_csv is not None:
        escrever_tabela(aba_curva.NOMES_V43, a.nomes_csv)
    gerar(a.v42, a.saida, a.registro, csv_nomes=a.nomes_csv)
    print(f"salvo {a.saida}")


if __name__ == "__main__":
    main()
