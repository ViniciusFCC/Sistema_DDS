"""Medição e regra da troca de endereço por nome nas abas 03 a 14 (incremento 8, parte 8b; spec §3.3 a §3.5; EDR-070).

Regra (§3.3): numa fórmula das abas 03 a 14, cada operando que é referência a UMA célula (com ou sem aba, com ou sem `$`)
e que é o destino exato de um nome definido é trocado por esse nome. Nada mais muda no texto da fórmula. Intervalo, coluna
inteira e, na 03_TARGETS, a referência à própria linha da ficha (H:Q) não são tocados.

A troca é mecânica, sobre os tokens OPERAND/RANGE do `Tokenizer` do openpyxl: texto entre aspas, nomes de função e
operadores nunca são tocados. Antes de trocar, a remontagem dos tokens originais tem de ser igual à fórmula original
(senão `ValueError`), para nunca alterar texto fora dos operandos.
"""
from dataclasses import dataclass, field

from openpyxl.formula import Tokenizer

from raizes import COLUNA, REF, nomes_definidos

ABAS_ALVO = ("03_TARGETS", "04_DECISION_REGISTER", "05_VEHICLE", "06_SUSPENSION", "07_KINEMATICS", "08_VEHICLE_STATE",
             "09_LOADS", "10_TIRE", "11_DESIGN", "12_COMPARISON", "13_VALIDATION", "14_DASHBOARD")
FAIXA_FICHA_03 = ("H", "Q")           # fichas de meta da 03_TARGETS (V4.2): colunas H:Q
VOLATEIS = ("NOW", "TODAY", "RAND", "RANDBETWEEN", "OFFSET", "INDIRECT", "CELL", "INFO")


def _eh_aba_alvo(titulo: str) -> bool:
    return titulo[:2].isdigit() and 3 <= int(titulo[:2]) <= 14


def destinos_unicos(wb) -> dict[tuple[str, str], str]:
    """(aba, célula sem `$`) -> nome, para todo nome definido cujo destino é uma célula única.
    `ValueError` se dois nomes apontam para a mesma célula (spec §3.3)."""
    out: dict[tuple[str, str], str] = {}
    for nome, ref in nomes_definidos(wb).items():
        m = REF.match(ref)
        if not m or m["c2"]:
            continue
        aba = (m["aba"] or "").strip("'")
        chave = (aba, f"{m['c1']}{m['r1']}")
        if chave in out:
            raise ValueError(f"destino ambíguo {chave}: {out[chave]!r} e {nome!r}")
        out[chave] = nome
    return out


def _tokens(formula: str, cel: str = ""):
    """Tokens da fórmula, conferindo que a remontagem é igual ao original."""
    itens = Tokenizer(formula).items
    if "=" + "".join(t.value for t in itens) != formula:
        raise ValueError(f"remontagem dos tokens difere da fórmula original em {cel or '?'}: {formula!r}")
    return itens


def _celula_do_token(valor: str, aba: str):
    """(aba, célula) de um operando de célula única; None se for intervalo, coluna inteira ou outra coisa."""
    m = REF.match(valor)
    if not m or m["c2"]:
        return None
    return (m["aba"] or aba).strip("'"), f"{m['c1']}{m['r1']}"


def trocar_formula(formula: str, aba: str, destinos: dict, cel: str = "") -> str:
    """Troca por nome cada operando de célula única que é destino exato de um nome (spec §3.3). Texto que não é fórmula
    volta igual. `cel` só serve para a mensagem de erro."""
    if not (isinstance(formula, str) and formula.startswith("=")):
        return formula
    saida = []
    for t in _tokens(formula, cel):
        v = t.value
        if t.type == "OPERAND" and t.subtype == "RANGE":
            alvo = _celula_do_token(v, aba)
            if alvo is not None and alvo in destinos:
                v = destinos[alvo]
        saida.append(v)
    return "=" + "".join(saida)


def eh_linha_propria_03(aba: str, cel_formula: str, token: str) -> bool:
    """Referência sem aba, na mesma linha da célula da fórmula, que está em H:Q da 03_TARGETS."""
    if aba != "03_TARGETS":
        return False
    m = REF.match(token)
    mf = REF.match(cel_formula)
    if not m or m["aba"] or m["c2"] or not mf:
        return False
    col = mf["c1"]
    return m["r1"] == mf["r1"] and len(col) == 1 and FAIXA_FICHA_03[0] <= col <= FAIXA_FICHA_03[1]


@dataclass
class Medicao:
    formulas: int = 0
    operandos: int = 0
    ja_nome: int = 0
    trocaveis: int = 0
    linha_propria_03: int = 0
    intervalos: int = 0
    colunas: int = 0
    soltas: dict = field(default_factory=dict)      # (aba, célula) -> quem cita ("aba!célula", uma entrada por referência)
    volateis: dict = field(default_factory=dict)
    ifs: int = 0
    iferrors: int = 0

    def resumo(self) -> str:
        n_ref = sum(len(v) for v in self.soltas.values())
        return (f"formulas {self.formulas}, operandos {self.operandos}, ja_nome {self.ja_nome}, trocaveis {self.trocaveis}, "
                f"linha_propria_03 {self.linha_propria_03}, intervalos {self.intervalos}, colunas {self.colunas}, "
                f"soltas {len(self.soltas)} células ({n_ref} referências), volateis {self.volateis}, IF {self.ifs}, "
                f"IFERROR {self.iferrors}")


def medir(wb, destinos: dict) -> Medicao:
    """Classifica cada operando RANGE das fórmulas das abas 03 a 14, na ordem: já é nome, coluna inteira, intervalo,
    trocável, linha própria da 03, solta."""
    nomes = set(nomes_definidos(wb))
    med = Medicao()
    for ws in wb.worksheets:
        if not _eh_aba_alvo(ws.title):
            continue
        for lin in ws.iter_rows():
            for c in lin:
                f = c.value
                if not (isinstance(f, str) and f.startswith("=")):
                    continue
                med.formulas += 1
                for t in _tokens(f, f"{ws.title}!{c.coordinate}"):
                    if t.type == "FUNC" and t.subtype == "OPEN":
                        fn = t.value[:-1].upper()
                        if fn == "IF":
                            med.ifs += 1
                        elif fn == "IFERROR":
                            med.iferrors += 1
                        elif fn in VOLATEIS:
                            med.volateis[fn] = med.volateis.get(fn, 0) + 1
                    if not (t.type == "OPERAND" and t.subtype == "RANGE"):
                        continue
                    med.operandos += 1
                    v = t.value
                    alvo = _celula_do_token(v, ws.title)
                    if v in nomes:
                        med.ja_nome += 1
                    elif COLUNA.match(v):
                        med.colunas += 1
                    elif (m := REF.match(v)) and m["c2"]:
                        med.intervalos += 1
                    elif alvo is not None and alvo in destinos:
                        med.trocaveis += 1
                    elif eh_linha_propria_03(ws.title, c.coordinate, v):
                        med.linha_propria_03 += 1
                    elif alvo is not None:
                        med.soltas.setdefault(alvo, []).append(f"{ws.title}!{c.coordinate}")
                    else:
                        raise ValueError(f"operando não classificado {v!r} em {ws.title}!{c.coordinate}")
    return med
