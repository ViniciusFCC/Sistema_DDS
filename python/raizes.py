"""Raízes das fórmulas da planilha V3.0 e a origem de cada raiz (EDR-035; FB-03, fases 1 e 2).

Usado por `tools/mapa_raizes.py` (mapa em CSV) e por `atualizar_planilha.py` (coluna de pior origem do 14_DASHBOARD).

Regras (nada é inferido):
- Raiz = célula referenciada que não é fórmula. Constantes dentro da fórmula (9.81, 0.0254) não são raízes.
- Origem da raiz: coluna E da linha nas abas de entrada (05/06/07/08/11); na 10_TIRE, coluna I da linha (casos) e I84
  para os coeficientes B86:B175. Qualquer outra raiz fica "sem rótulo".
- Referência que o parser não reconhece interrompe (nunca é ignorada em silêncio); coluna inteira (COUNTIF de IDs) é
  registrada à parte e não vira raiz.
- Ordem de "pior origem" (usuário, 2026-10-19, fase 2 do FB-03): "? A confirmar" (origem desconhecida não conta como
  boa), Arbitrário, Estimativa, Provisório (.tir TTC), Dado do T09, Dado do TX.
"""
import re

from openpyxl.formula import Tokenizer
from openpyxl.utils import column_index_from_string, get_column_letter

from atualizar_planilha import ABAS_ORIGEM, ORIGENS_LISTA, TX, T09, TTC, EST, ARB, CONF

SEM_ROTULO = "sem rótulo de origem"
PIOR_PRIMEIRO = (CONF, ARB, EST, TTC, T09, TX)
TIER = {TX: "T3", T09: "T2", TTC: "T2", EST: "T1", ARB: "T1", CONF: "?"}
COEF_TIRE = set(range(86, 176)) | {177}            # 10_TIRE: coeficientes do .tir (177 = LKYG); origem em I84
COLUNA = re.compile(r"^(?:(?P<aba>'[^']+'|[^!']+)!)?\$?(?P<c1>[A-Z]{1,3}):\$?(?P<c2>[A-Z]{1,3})$")
REF = re.compile(r"^(?:(?P<aba>'[^']+'|[^!']+)!)?\$?(?P<c1>[A-Z]{1,3})\$?(?P<r1>\d+)(?::\$?(?P<c2>[A-Z]{1,3})\$?(?P<r2>\d+))?$")


def linha(cel: str) -> int:
    return int(re.sub(r"[A-Z]", "", cel))


def chave(no: tuple[str, str]):
    return (no[0], linha(no[1]), no[1])


def nomes_definidos(wb) -> dict[str, str]:
    """Nomes definidos da pasta (ex.: 'Origens') -> referência ('00_README'!$A$43:$A$48)."""
    return {n: d.attr_text for n, d in wb.defined_names.items()}


def referencias(formula: str, aba_atual: str, colunas: list | None = None,
                nomes: dict[str, str] | None = None) -> list[tuple[str, str]]:
    """Células referenciadas; nomes definidos são expandidos. Coluna inteira não vira raiz: vai para `colunas`."""
    out = []
    for tok in Tokenizer(formula).items:
        if tok.type != "OPERAND" or tok.subtype != "RANGE":
            continue
        if nomes and tok.value in nomes:
            out += referencias("=" + nomes[tok.value], aba_atual, colunas)
            continue
        m = REF.match(tok.value)
        if not m:
            mc = COLUNA.match(tok.value)
            if mc is None:
                raise ValueError(f"referência não reconhecida {tok.value!r} em {formula!r}")
            if colunas is not None:
                colunas.append(f"{(mc['aba'] or aba_atual).strip(chr(39))}!{mc['c1']}:{mc['c2']}")
            continue
        aba = (m["aba"] or aba_atual).strip("'")
        c1, r1 = column_index_from_string(m["c1"]), int(m["r1"])
        c2, r2 = (column_index_from_string(m["c2"]), int(m["r2"])) if m["c2"] else (c1, r1)
        for c in range(min(c1, c2), max(c1, c2) + 1):
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out.append((aba, f"{get_column_letter(c)}{r}"))
    return out


def celula_origem(aba: str, cel: str) -> tuple[str, str] | None:
    """Célula da coluna Origem que vale para a raiz (aba, cel); None se a aba não tem coluna Origem."""
    r = linha(cel)
    if aba in ABAS_ORIGEM:
        return aba, f"E{r}"
    if aba == "10_TIRE":
        return aba, f"I{84 if r in COEF_TIRE else r}"
    return None


def origem_da_raiz(wb, aba: str, cel: str, lista=ORIGENS_LISTA) -> str:
    """Rótulo de origem da raiz, ou SEM_ROTULO se vazio ou fora de `lista`. O padrão é a lista da V4.1; numa planilha da
    V4.2 passe `lista=origens.ORIGENS_V42` (senão `● Dado do T11` contaria como sem rótulo). Os chamadores atuais
    (caso_planilha, mapa_raizes, relatorio_inc1) leem planilhas da V4.1."""
    co = celula_origem(aba, cel)
    v = wb[co[0]][co[1]].value if co else None
    return v if v in lista else SEM_ROTULO


class Grafo:
    """Fórmulas de uma pasta openpyxl (carregada sem data_only) e o fecho até as raízes."""

    def __init__(self, wb):
        self.wb = wb
        self.formulas = {(ws.title, c.coordinate): c.value for ws in wb.worksheets for lin in ws.iter_rows() for c in lin
                         if isinstance(c.value, str) and c.value.startswith("=")}
        self._memo: dict = {}
        self.colunas: dict = {}
        self.nomes = nomes_definidos(wb)

    def raizes(self, no, pilha=()):
        if no in self._memo:
            return self._memo[no]
        if no not in self.formulas:
            return {no}
        if no in pilha:
            raise RuntimeError(f"referência circular em {no}")
        acc = set()
        cols = self.colunas.setdefault(no, [])
        for ref in referencias(self.formulas[no], no[0], cols, self.nomes):
            acc |= self.raizes(ref, pilha + (no,))
        self._memo[no] = acc
        return acc

    def raizes_preenchidas(self, no) -> list[tuple[str, str]]:
        return sorted((x for x in self.raizes(no) if self.wb[x[0]][x[1]].value is not None), key=chave)

    def celulas_origem(self, no) -> list[tuple[str, str]]:
        """Células de Origem (distintas) das raízes de `no`; raízes sem coluna Origem ficam de fora."""
        return sorted({co for x in self.raizes_preenchidas(no) if (co := celula_origem(*x))}, key=chave)
