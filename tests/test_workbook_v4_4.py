"""
Teste da V4.4 no motor de recálculo (incremento 8, parte 8b; EDR-070, EDR-044): equivalência por valor V4.3 x V4.4
(TC-WB44-005), tolerância zero. O TC-WB44-006 (cobertura de ramos) entra aqui no Task 16.
Uso: uv run python -X utf8 tests/test_workbook_v4_4.py

Recalcula CÓPIAS, no mesmo motor (Excel via COM; LibreOffice de reserva; DDS_RECALC=excel|libreoffice força um): a V4.3 da tag
v4.3 (`gerar_v4_4.copia_v43`) e a V4.4 (excel/…V4_4.xlsx, ou o arquivo de DDS_V44, que é o que a mutação usa), as duas com os
mesmos valores escritos por nome. Compara todas as células de todas as abas (menos a `zz_COBERTURA` e EXCLUIDAS_VALOR): números,
textos, booleanos e erros idênticos (`dados_planilha.iguais`; vazio == vazio). Nenhum arquivo de excel/ e nenhuma viva é
gravado ou recalculado. Sem motor: NÃO EXECUTÁVEL (código 3).

Casos (`casos()`): NOMINAL (sem alteração), P01 a P30 (entradas numéricas `ent` das tabelas V4.0 a V4.3 em v·(1 + U(−0,20; 0,20)),
`random.Random(SEMENTE + i)`; inteiro continua inteiro, sinal e zero se mantêm, vazio continua vazio; entradas de lista só com
opção válida) e os dirigidos D3: DIR_ORIGENS_VAZIAS, DIR_CHAVES_INVERTIDAS, DIR_NUMERICAS_VAZIAS, DIR_DIREITA (o DIR_ESQUERDA do D3 não mudava nada) e os
dirigidos da cobertura (`casos_dirigidos_cobertura`). Os 24 nomes novos da
V4.4 não são perturbados. Os valores são sintéticos de teste (não são dados do carro). DDS_CASOS44 (lista separada por vírgula)
restringe os casos; vazio = todos. "Passou" = a V4.4 reproduz a V4.3; não é validação física.
"""
import hashlib
import json
import math
import os
import random
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.worksheet.formula import ArrayFormula

import aba_equilibrio as ae
import dados_planilha as dp
import gerar_v4_4 as g44
import raizes
import recalculo_planilha as rc
import reescrita_nomes as rn
from nomes_v4_0 import ler_tabela

RAIZ = Path(__file__).resolve().parent.parent
SEMENTE = 20261109
N_PERTURBADOS = 30
FAIXA = 0.20
V43_EXCEL = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_3.xlsx"   # só leitura
V44_PADRAO = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_4.xlsx"   # só leitura
ABA_COBERTURA = "zz_COBERTURA"
ROTULO = "valores sintéticos de teste (não são dados do carro)"
LIMITE_S = 120.0   # A4: acima disso, parar e avisar (não reduzir N). Subiu de 60 s a pedido do usuário (2026-11-09, "Sim, 120 s"): média medida 46,4 s, P15 71,2 s
VOLATEIS = re.compile(r"\b(NOW|TODAY|RAND|RANDBETWEEN|OFFSET|INDIRECT|INFO|CELL)\s*\(", re.I)

# Células de X2 a X5 com valor diferente de propósito (alteracoes()); o fecho de dependentes é somado em runtime.
EXCLUIDAS_BASE = {("16_EQUILIBRIO", "F188"), ("14_DASHBOARD", "B48"), ("00_README", "A3"),
                  ("15_CHANGELOG", "A24"), ("15_CHANGELOG", "B24"), ("15_CHANGELOG", "C24")}
EXCLUIDAS_VALOR = set(EXCLUIDAS_BASE)

results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL"))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def caminho_v44() -> Path:
    p = os.environ.get("DDS_V44", "").strip()
    return Path(p).resolve() if p else V44_PADRAO


# ---------------------------------------------------------------- entradas e perturbação
def _eh_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _opcoes(wb, dv) -> list:
    f = (dv.formula1 or "").strip()
    if f.startswith('"') and f.endswith('"'):
        return f[1:-1].split(",")
    ref = f[1:] if f.startswith("=") else f
    nomes = raizes.nomes_definidos(wb)
    ref = nomes.get(ref, ref)
    m = re.fullmatch(r"(?:'([^']+)'|([^!']+))!\$?([A-Z]+)\$?(\d+)(?::\$?([A-Z]+)\$?(\d+))?", ref)
    if not m:
        raise ValueError(f"fonte de validação de lista não reconhecida: {dv.formula1!r}")
    aba = m.group(1) or m.group(2)
    a, b = f"{m.group(3)}{m.group(4)}", f"{m.group(5) or m.group(3)}{m.group(6) or m.group(4)}"
    cels = wb[aba][a:b]
    return [c.value for lin in cels for c in lin if c.value is not None]


def entradas_perturbaveis(wb43) -> tuple[list[str], dict[str, list]]:
    """(nomes numéricos `ent` das tabelas V4.0 a V4.3, nome -> opções da lista para `ent`/`org` com validação de lista).
    Célula com fórmula não é entrada. Fonte de lista que não é nome definido, intervalo ou lista literal -> ValueError."""
    papel = {}
    for v in range(4):
        for n in ler_tabela(RAIZ / "data" / f"nomes_V4_{v}.csv"):
            papel[n.nome] = n.papel
    destinos = dp._destinos(wb43)   # só dados e sem fórmula
    por_celula = {}
    for nome, (aba, cel) in destinos.items():
        if papel.get(nome) in ("ent", "org"):
            por_celula[nome] = (aba, cel)
    listas, numericos = {}, []
    for nome in sorted(por_celula):
        aba, cel = por_celula[nome]
        ws = wb43[aba]
        dv = next((d for d in ws.data_validations.dataValidation if d.type == "list" and cel in d.sqref), None)
        v = ws[cel].value
        if dv is not None:
            ops = _opcoes(wb43, dv)
            if _eh_num(v):   # lista literal "0,1" numa célula numérica: opções do mesmo tipo
                ops = [(int(o) if isinstance(v, int) else float(o)) for o in ops]
            listas[nome] = ops
        elif papel[nome] == "ent" and _eh_num(v):
            numericos.append(nome)
    return numericos, listas


def perturbar(valores: dict, numericos, listas, rng) -> dict:
    """nome -> novo valor. v·(1 + U(−FAIXA, FAIXA)); int -> round; 0 -> 0; None fica None; lista -> rng.choice(opções)."""
    out = {}
    for nome in numericos:
        v = valores[nome]
        if v is None or v == 0:
            out[nome] = v
            continue
        f = v * (1 + rng.uniform(-FAIXA, FAIXA))
        out[nome] = round(f) if isinstance(v, int) else f
    for nome in sorted(listas):
        v = valores[nome]
        out[nome] = None if v is None else rng.choice(listas[nome])
    return out


def _valores_v43():
    wb = openpyxl.load_workbook(V43_EXCEL)
    try:
        numericos, listas = entradas_perturbaveis(wb)
        vals = {}
        for n in list(numericos) + list(listas):
            aba, cel = ae._destino(wb, n)
            vals[n] = wb[aba][cel].value
        return numericos, listas, vals
    finally:
        wb.close()


def casos_dirigidos_cobertura(vals: dict, listas: dict) -> list[tuple[str, dict]]:
    """Casos dirigidos acrescentados pela cobertura de ramos (TC-WB44-006, spec 4.3 item 3). Só valores válidos do sentido da
    entrada: esvaziar, opção de lista, chave 0/1, sinal, escala dos pontos de operação do pneu, aceleração lateral, ficha de
    meta preenchida. Chave `aba!célula` altera célula sem nome (entrada de origem do pneu). Valores sintéticos de teste."""
    out = []
    eixos = "ent_10_sistema_de_eixos_do_arquivo_declarado_sa"
    pneu = [n for n in vals if n.startswith(("ent_10_angulo_de_deriva", "ent_10_camber_gama", "ent_10_slip_ratio"))]
    out.append(("DIR_EIXOS_SAE", {eixos: "SAE_CALSPAN"}))
    out.append(("DIR_EIXOS_VAZIO", {eixos: None}))
    for k, rot in ((10, "X10"), (-10, "XM10")):
        for conv in ("ISO", "SAE"):
            alt = {n: vals[n] * k for n in pneu}
            if conv == "SAE":
                alt[eixos] = "SAE_CALSPAN"
            out.append((f"DIR_PNEU_{rot}_{conv}", alt))
    out.append(("DIR_PNEU_FZMAX_BAIXO", {"ent_10_fzmax": 600}))
    ay = "ent_08_aceleracao_lateral_em_g_entrada_de_a_y"
    for g in (1.8, 2.4, 3.0):   # ay positivo: rodas da esquerda internas; negativo (sinal da entrada): rodas da direita internas
        out.append((f"DIR_AY_{str(g).replace('.', '_')}", {ay: g}))
        out.append((f"DIR_AY_NEG_{str(g).replace('.', '_')}", {ay: -g}))

    def campo(c, valor):
        return {f"ent_03_target_{i + 1:03d}_{c}{5 + i}": valor for i in range(7)}

    # Linhas 7, 10 e 11 dividem a alavanca "distribuição de rolagem": no máximo uma META por alavanca, senão CONFLITO.
    outro = next(o for o in listas["ent_03_target_001_h5"] if o not in ("META", "TBD"))
    papel = campo("h", "META")
    papel.update({"ent_03_target_006_h10": outro, "ent_03_target_007_h11": outro})
    out.append(("DIR_FICHAS_META", dict(campo("h", "META"), **campo("c", "valor de teste"))))   # todas META: CONFLITO na alavanca comum
    alt = dict(papel, **campo("c", "valor de teste"))
    out.append(("DIR_FICHAS_ALTERNADAS", alt))
    com_m = dict(alt, **campo("m", "compromisso de teste"))
    out.append(("DIR_FICHAS_COMPROMISSO", com_m))
    out.append(("DIR_FICHAS_COMPROMISSO_EDR", dict(com_m, **campo("n", "EDR-001"))))
    out.append(("DIR_FICHAS_PAPEL_VAZIO", campo("h", None)))
    out.append(("DIR_FICHAS_CICLO_VAZIO", campo("d", None)))
    out.append(("DIR_FICHAS_CONGELAMENTO_VAZIO", campo("j", None)))
    out.append(("DIR_PNEU_LADOS_TROCADOS", {f"10_TIRE!{c}21": ("R" if c in "BD" else "L") for c in "BCDEF"}))
    out.append(("DIR_CHAVE_H2V_VAZIA", {"ent_24_chave_h2v_forma_do_ackermann": None}))
    origem = listas["org_10_i84"][0]
    out.append(("DIR_ORIGENS_PNEU", {"10_TIRE!I11": origem, "10_TIRE!I21": origem, "10_TIRE!I176": origem}))
    out.append(("DIR_RAIO_MANUAL", {"ent_24_modo_do_raio_r": "Manual", "ent_24_r_manual": 9.0}))
    out.append(("DIR_RAIO_MANUAL_SEM_R", {"ent_24_modo_do_raio_r": "Manual"}))
    out.append(("DIR_MOLAS_MOLES", {n: vals[n] * 0.005 for n in vals
                                    if n.startswith(("ent_06_spring_rate", "ent_06_k_arb"))}))
    return out


def casos() -> list[tuple[str, dict]]:
    numericos, listas, vals = _valores_v43()
    out = [("NOMINAL", {})]
    for i in range(1, N_PERTURBADOS + 1):
        out.append((f"P{i:02d}", perturbar(vals, numericos, listas, random.Random(SEMENTE + i))))
    org = [n for n in listas if n.startswith("org_")]
    out.append(("DIR_ORIGENS_VAZIAS", {n: None for n in org}))
    out.append(("DIR_CHAVES_INVERTIDAS", {n: (1 - v) for n, v in vals.items() if "chave_h" in n and v in (0, 1)}))
    out.append(("DIR_NUMERICAS_VAZIAS", {n: None for n in numericos}))
    # DIR_ESQUERDA (D3) não mudava nada: o valor nominal já é "Esquerda". A outra opção da lista é a que exercita o ramo.
    out.append(("DIR_DIREITA", {"ent_16_sentido_da_curva": "Direita"}))
    out += casos_dirigidos_cobertura(vals, listas)
    sub = [x.strip() for x in os.environ.get("DDS_CASOS44", "").split(",") if x.strip()]
    if sub:
        desc = set(sub) - {n for n, _ in out}
        if desc:
            raise ValueError(f"DDS_CASOS44 com caso desconhecido: {sorted(desc)}")
        out = [c for c in out if c[0] in sub]
    return out


# ---------------------------------------------------------------- leitura e comparação
def iguais_celula(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return dp.iguais(a, b)


def valores_recalculados(caminho: Path, cobertura: dict | None = None) -> dict[tuple[str, str], object]:
    """Valores recalculados de todas as abas, menos a `zz_COBERTURA`; os valores dela vão para `cobertura` (célula -> valor)."""
    wb = openpyxl.load_workbook(caminho, data_only=True)
    out = {}
    try:
        for ws in wb.worksheets:
            if ws.title == ABA_COBERTURA:
                if cobertura is not None:
                    for lin in ws.iter_rows(min_col=2, max_col=3):
                        for c in lin:
                            cobertura[c.coordinate] = c.value
                continue
            for lin in ws.iter_rows():
                for c in lin:
                    if c.value is not None:
                        out[(ws.title, c.coordinate)] = c.value
    finally:
        wb.close()
    return out


def _eh_erro(v) -> bool:
    return isinstance(v, str) and v.startswith("#") and any(e in v for e in rc.ERROS)


def _formula(v):
    v = v.text if isinstance(v, ArrayFormula) else v
    return v if isinstance(v, str) and v.startswith("=") else None


def formulas(caminho: Path) -> dict[tuple[str, str], str]:
    wb = openpyxl.load_workbook(caminho)
    out = {}
    try:
        for ws in wb.worksheets:
            for lin in ws.iter_rows():
                for c in lin:
                    f = _formula(c.value)
                    if f:
                        out[(ws.title, c.coordinate)] = f
        return out, raizes.nomes_definidos(wb)
    finally:
        wb.close()


def fecho_dependentes(forms: dict, nomes: dict, sementes: set) -> set:
    """Células que dependem, direta ou indiretamente, das sementes (grafo de `raizes.referencias`)."""
    dependentes: dict = {}
    for no, f in forms.items():
        for r in set(raizes.referencias(f, no[0], [], nomes)):
            dependentes.setdefault(r, []).append(no)
    achadas, pilha = set(), list(sementes)
    while pilha:
        for d in dependentes.get(pilha.pop(), []):
            if d not in achadas and d not in sementes:
                achadas.add(d)
                pilha.append(d)
    return achadas


def aplicar_celulas(wb, alteracoes: dict) -> None:
    """Chaves `aba!célula` (entradas sem nome definido); as demais (nomes) quem aplica é o gerador."""
    for chave, valor in alteracoes.items():
        if "!" in chave:
            aba, cel = chave.split("!")
            wb[aba][cel].value = valor


def so_nomes(alteracoes: dict) -> dict:
    return {k: v for k, v in alteracoes.items() if "!" not in k}


def copia_v44_de_arquivo(origem: Path, alteracoes: dict, destino: Path) -> Path:
    wb = openpyxl.load_workbook(origem)
    try:
        for nome, valor in so_nomes(alteracoes).items():
            aba, cel = ae._destino(wb, nome)
            wb[aba][cel].value = valor
        aplicar_celulas(wb, alteracoes)
        wb.calculation.fullCalcOnLoad = True
        wb.save(destino)
    finally:
        wb.close()
    return destino


# ---------------------------------------------------------------- pré-checagem pura
def pre_checagem() -> bool:
    ok = True

    def p(nome, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'ok' if cond else 'FALHOU'}] {nome}")

    vals = {"a": 5, "b": -3, "c": 0, "d": None, "e": 2.5, "f": -0.75, "g": 1, "L": "x", "L0": None}
    nums, ls = ["a", "b", "c", "d", "e", "f", "g"], {"L": ["x", "y", "z"], "L0": ["x", "y"]}
    tipos = bool_ok = sinal = lista = det = True
    r1 = None
    for s in range(200):
        r = perturbar(vals, nums, ls, random.Random(s))
        tipos = tipos and isinstance(r["a"], int) and isinstance(r["g"], int) and isinstance(r["e"], float)
        sinal = sinal and r["a"] > 0 > r["b"] and r["e"] > 0 > r["f"] and r["g"] == 1
        bool_ok = bool_ok and r["c"] == 0 and r["d"] is None and r["L0"] is None
        lista = lista and r["L"] in ls["L"]
        det = det and r == perturbar(vals, nums, ls, random.Random(s))
        r1 = r
    p("perturbar mantém int, float, sinal, zero e None", tipos and sinal and bool_ok)
    p("perturbar: opção de lista sempre válida", lista)
    p("a mesma semente dá o mesmo caso", det)
    p("faixa ±20 %", all(abs(perturbar(vals, ["e"], {}, random.Random(s))["e"] / 2.5 - 1) <= FAIXA for s in range(200)))
    p("iguais_celula(True, 1) é False", iguais_celula(True, 1) is False)
    p("iguais_celula('#N/A', '#N/A') é True", iguais_celula("#N/A", "#N/A") is True)
    p("iguais_celula(None, None) é True e (None, 0) é False", iguais_celula(None, None) and not iguais_celula(None, 0))
    p("iguais_celula(1, 1.0) é True e (1, 1.0000001) é False", iguais_celula(1, 1.0) and not iguais_celula(1, 1.0000001))
    return ok and pre_checagem_ramos_unitaria()


def volateis(caminho: Path) -> int:
    forms, _ = formulas(caminho)
    return sum(1 for f in forms.values() if VOLATEIS.search(f))


# ---------------------------------------------------------------- ramos (TC-WB44-006)
IFS_ALVO = ("IF", "IFERROR")
FUNCS_MATRIZ = ("SUMPRODUCT", "MMULT", "MINVERSE", "MDETERM", "TRANSPOSE", "LINEST", "LOGEST", "FREQUENCY")
MOTIVO_MATRIZ = "condição avaliada em matriz; não medível por célula"
OPERANDO_CEL = re.compile(r"^\$?[A-Z]{1,3}\$?\d+(:\$?[A-Z]{1,3}\$?\d+)?$|^\$?[A-Z]{1,3}:\$?[A-Z]{1,3}$|^\$?\d+:\$?\d+$")
LIMITE_FORMULA = 8000   # o Excel aceita 8192 caracteres por fórmula
CONTAGEM_ESPERADA = {"IF": 462, "IFERROR": 350}   # medição da V4.3 nas ABAS_ALVO (spec 4.4)
PASTA_COBERTURA = RAIZ / "build" / "cobertura-v44-casos"
RELATORIO_COBERTURA = RAIZ / "build" / "cobertura-v44.md"

MOTIVO_A = "ID fixo da meta (coluna A, não é entrada) fora da relação da 23_LISTAS; só editando o ID"
MOTIVO_B = "CONFLITO de META na alavanca: nas linhas 5, 6, 8 e 9 a alavanca é única, então só há uma META possível"
MOTIVO_C = "coluna F da 10_TIRE é o caso VERIF de valor fixo (F22:F25), não é entrada; mesma família de fórmula das colunas B a E, que estão cobertas"
MOTIVO_D = "impossível por aritmética: dentro de κ < KPUMIN (KPUMIN < 0) κ já é negativo; dentro de κ > KPUMAX (KPUMAX > 0) κ não é negativo; KPUMIN/KPUMAX < 0 só em .tir de faixa incoerente"
MOTIVO_E = "identidade algébrica da soma das cargas (peso + aero); só falha se o modelo estiver errado"

# (aba, cel, indice, lado) -> motivo. Aprovado pelo usuário em 2026-11-09 ("Aprovo como está"): 72 lados, motivos A a E.
NAO_COBERTOS: dict[tuple[str, str, int, str], str] = {
    ('03_TARGETS', 'I10', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'I11', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'I5', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'I6', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'I7', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'I8', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'I9', 0, 'ERRO'): MOTIVO_A,
    ('03_TARGETS', 'U10', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'U11', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'U5', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'U6', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'U7', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'U8', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'U9', 0, 'V'): MOTIVO_A,
    ('03_TARGETS', 'O5', 3, 'V'): MOTIVO_B,
    ('03_TARGETS', 'O6', 3, 'V'): MOTIVO_B,
    ('03_TARGETS', 'O8', 3, 'V'): MOTIVO_B,
    ('03_TARGETS', 'O9', 3, 'V'): MOTIVO_B,
    ('10_TIRE', 'F26', 0, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 2, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 4, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 5, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 6, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 7, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 7, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 8, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 8, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 9, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 10, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 10, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 11, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 11, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 12, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 13, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 13, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 14, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 14, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 15, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 16, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 16, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 17, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 17, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 18, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 19, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 19, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 20, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 20, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 21, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 22, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 22, 'V'): MOTIVO_C,
    ('10_TIRE', 'F26', 23, 'F'): MOTIVO_C,
    ('10_TIRE', 'F26', 23, 'V'): MOTIVO_C,
    ('10_TIRE', 'F36', 0, 'F'): MOTIVO_C,
    ('10_TIRE', 'F37', 0, 'F'): MOTIVO_C,
    ('10_TIRE', 'B26', 19, 'F'): MOTIVO_D,
    ('10_TIRE', 'B26', 20, 'F'): MOTIVO_D,
    ('10_TIRE', 'B26', 22, 'V'): MOTIVO_D,
    ('10_TIRE', 'B26', 23, 'V'): MOTIVO_D,
    ('10_TIRE', 'C26', 19, 'F'): MOTIVO_D,
    ('10_TIRE', 'C26', 20, 'F'): MOTIVO_D,
    ('10_TIRE', 'C26', 22, 'V'): MOTIVO_D,
    ('10_TIRE', 'C26', 23, 'V'): MOTIVO_D,
    ('10_TIRE', 'D26', 19, 'F'): MOTIVO_D,
    ('10_TIRE', 'D26', 20, 'F'): MOTIVO_D,
    ('10_TIRE', 'D26', 22, 'V'): MOTIVO_D,
    ('10_TIRE', 'D26', 23, 'V'): MOTIVO_D,
    ('10_TIRE', 'E26', 19, 'F'): MOTIVO_D,
    ('10_TIRE', 'E26', 20, 'F'): MOTIVO_D,
    ('10_TIRE', 'E26', 22, 'V'): MOTIVO_D,
    ('10_TIRE', 'E26', 23, 'V'): MOTIVO_D,
    ('13_VALIDATION', 'B5', 0, 'F'): MOTIVO_E,
    ('13_VALIDATION', 'B7', 0, 'F'): MOTIVO_E,
}


@dataclass(frozen=True)
class Ramo:
    aba: str
    cel: str
    tipo: str                 # "IF" ou "IFERROR"
    indice: int               # ordem de aparição do IF/IFERROR na fórmula (começa em 0, conta os dois tipos)
    condicao: str             # IF: a condição; IFERROR: o primeiro argumento (operandos sem aba já qualificados)
    caminho: tuple[str, ...]  # condições dos ramos externos que levam a este
    matriz: bool

    def lados(self) -> tuple[tuple[str, str], tuple[str, str]]:
        """((nome do lado 1, condição), (nome do lado 2, condição)). `IF(c,TRUE,FALSE)` imita o IF (célula vazia = FALSE),
        o que `AND(c)` e `NOT(c)` não fazem com referência a célula vazia."""
        if self.tipo == "IF":
            return ("V", f"IF({self.condicao},TRUE,FALSE)"), ("F", f"IF({self.condicao},FALSE,TRUE)")
        return ("ERRO", f"ISERROR({self.condicao})"), ("OK", f"NOT(ISERROR({self.condicao}))")

    def formula_lado(self, lado: str) -> str:
        cond = dict(self.lados())[lado]
        return '=IFERROR(AND(' + ",".join(self.caminho + (cond,)) + '),"ERRO")'


def _qualificar(valor: str, aba: str) -> str:
    return f"'{aba}'!{valor}" if OPERANDO_CEL.match(valor) else valor


def _par(itens, i: int) -> tuple[int, list[int]]:
    """Posição do fecho do FUNC OPEN em `i` e as posições dos separadores de argumento do próprio nível."""
    prof, seps = 0, []
    for j in range(i, len(itens)):
        t = itens[j]
        if t.subtype == "OPEN" and t.type in ("FUNC", "PAREN", "ARRAY"):
            prof += 1
        elif t.subtype == "CLOSE" and t.type in ("FUNC", "PAREN", "ARRAY"):
            prof -= 1
            if prof == 0:
                return j, seps
        elif t.type == "SEP" and t.subtype == "ARG" and prof == 1:
            seps.append(j)
    raise ValueError("função sem fecho na fórmula")


def ramos(formula, aba: str, cel: str = "", forma_matricial: bool = False) -> list[Ramo]:
    """Todos os IF e IFERROR da fórmula, com o caminho de condições que leva a cada um (spec 4.4). Texto que não é fórmula: []."""
    f = formula.text if isinstance(formula, ArrayFormula) else formula
    if not (isinstance(f, str) and f.startswith("=")):
        return []
    itens = Tokenizer(f).items
    if "=" + "".join(t.value for t in itens) != f:
        raise ValueError(f"remontagem dos tokens difere da fórmula original em {aba}!{cel}: {f!r}")
    saida: list[Ramo] = []

    def texto(lo, hi):
        return "".join(_qualificar(t.value, aba) if (t.type == "OPERAND" and t.subtype == "RANGE") else t.value
                       for t in itens[lo:hi]).strip()

    def varrer(lo, hi, caminho, matriz):
        i = lo
        while i < hi:
            t = itens[i]
            if not (t.type == "FUNC" and t.subtype == "OPEN"):
                i += 1
                continue
            fim, seps = _par(itens, i)
            nome = t.value[:-1].upper()
            cortes = [i] + seps + [fim]
            args = [(cortes[k] + 1, cortes[k + 1]) for k in range(len(cortes) - 1)]
            if nome in IFS_ALVO:
                x = texto(*args[0])
                saida.append(Ramo(aba, cel, nome, len(saida), x, caminho, matriz))
                if nome == "IF":
                    filhos = [(1, caminho + (f"IF({x},TRUE,FALSE)",)), (2, caminho + (f"IF({x},FALSE,TRUE)",))]
                else:
                    filhos = [(1, caminho + (f"ISERROR({x})",))]
                varrer(*args[0], caminho, matriz)
                for k, cam in filhos:
                    if k < len(args):
                        varrer(*args[k], cam, matriz)
            else:
                m = matriz or nome in FUNCS_MATRIZ
                for a in args:
                    varrer(*a, caminho, m)
            i = fim + 1

    varrer(0, len(itens), (), forma_matricial)
    return saida


def todos_os_ramos(wb43) -> list[Ramo]:
    out = []
    for aba in rn.ABAS_ALVO:
        for lin in wb43[aba].iter_rows():
            for c in lin:
                out += ramos(c.value, aba, c.coordinate, isinstance(c.value, ArrayFormula))
    return out


def aba_cobertura(wb43) -> dict[str, tuple[Ramo, str, str]]:
    """Célula da `zz_COBERTURA` -> (ramo, lado, fórmula da célula). Uma linha por ramo, os dois lados nas colunas B e C.
    O ramo `matriz=True` fica de fora (vai ao log com MOTIVO_MATRIZ)."""
    out = {}
    linha = 0
    for r in todos_os_ramos(wb43):
        if r.matriz:
            continue
        linha += 1
        for col, (lado, _) in zip("BC", r.lados()):
            out[f"{col}{linha}"] = (r, lado, r.formula_lado(lado))
    return out


def montar_cobertura(wb) -> None:
    """Acrescenta a `zz_COBERTURA` (só na cópia da V4.3 de teste). Uma célula por lado de ramo."""
    ws = wb.create_sheet(ABA_COBERTURA)
    for cel, (r, lado, f) in aba_cobertura(wb).items():
        ws[cel] = f
        ws[f"A{cel[1:]}"] = f"{r.aba}!{r.cel} #{r.indice} {r.tipo}"


def assinatura_layout(cob: dict) -> str:
    h = hashlib.sha256()
    for cel, (r, lado, f) in cob.items():
        h.update(f"{cel}|{r.aba}|{r.cel}|{r.tipo}|{r.indice}|{lado}|{f}\n".encode())
    return h.hexdigest()[:16]


def pre_checagem_ramos(wb43) -> bool:
    """As contagens de `ramos` batem com 462 IF e 350 IFERROR e com a contagem independente por expressão regular;
    nenhuma fórmula da aba auxiliar passa de LIMITE_FORMULA caracteres."""
    rs = todos_os_ramos(wb43)
    n = {t: sum(1 for r in rs if r.tipo == t) for t in IFS_ALVO}
    rx = {t: 0 for t in IFS_ALVO}
    for aba in rn.ABAS_ALVO:
        for lin in wb43[aba].iter_rows():
            for c in lin:
                f = c.value.text if isinstance(c.value, ArrayFormula) else c.value
                if isinstance(f, str) and f.startswith("="):
                    sem_texto = re.sub(r'"[^"]*"', '""', f)
                    for t in IFS_ALVO:
                        rx[t] += len(re.findall(rf"(?<![A-Za-z0-9_.]){t}\(", sem_texto))
    ok = n == CONTAGEM_ESPERADA and rx == CONTAGEM_ESPERADA
    print(f"  [{'ok' if ok else 'FALHOU'}] ramos: IF {n['IF']}, IFERROR {n['IFERROR']} "
          f"(esperado {CONTAGEM_ESPERADA}; regex {rx}); {sum(1 for r in rs if r.matriz)} em matriz")
    maior = max((len(f) for _, _, f in aba_cobertura(wb43).values()), default=0)
    ok_len = maior <= LIMITE_FORMULA
    print(f"  [{'ok' if ok_len else 'FALHOU'}] maior fórmula da zz_COBERTURA: {maior} caracteres (limite {LIMITE_FORMULA})")
    return ok and ok_len


def pre_checagem_ramos_unitaria() -> bool:
    ok = True

    def p(nome, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'ok' if cond else 'FALHOU'}] {nome}")

    r = ramos('=IF(A1>0,IF(B2="x",1,2),IFERROR(C3,0))+SUM(D4)', "05_VEHICLE", "Z1")
    p("ramos: 3 ramos na ordem de aparição", [(x.tipo, x.indice) for x in r] == [("IF", 0), ("IF", 1), ("IFERROR", 2)])
    p("ramos: operando sem aba ganha a aba", r[0].condicao == "'05_VEHICLE'!A1>0")
    p("ramos: texto entre aspas não é tocado", r[1].condicao == "'05_VEHICLE'!B2=\"x\"")
    p("ramos: caminho do IF aninhado é a condição externa", r[1].caminho == ("IF('05_VEHICLE'!A1>0,TRUE,FALSE)",))
    p("ramos: caminho do ramo no falso externo", r[2].caminho == ("IF('05_VEHICLE'!A1>0,FALSE,TRUE)",))
    r = ramos("=IFERROR(IF(A1,B1,C1),IF(D1,1,2))", "X", "A2")
    p("ramos: IF dentro do x do IFERROR mantém o caminho", r[1].caminho == ())
    p("ramos: IF dentro do y do IFERROR ganha ISERROR(x)", r[2].caminho[0].startswith("ISERROR(IF("))
    r = ramos("=SUMPRODUCT(IF(A1:A3>0,1,0))+IF(B1,1,2)", "X", "A3")
    p("ramos: dentro de SUMPRODUCT é matriz", r[0].matriz and not r[1].matriz)
    r = ramos("=IF('05_VEHICLE'!$B$7>NomeX,Origens,0)", "X", "A4")
    p("ramos: operando já com aba e nome definido ficam como estão", r[0].condicao == "'05_VEHICLE'!$B$7>NomeX")
    p("ramos: IF de dois argumentos; texto sem '=' não tem ramo", len(ramos("=IF(A1,1)", "X")) == 1 and ramos("texto IF(", "X") == [])
    r = ramos("=IF(A1,1,2)", "X", "A5")[0]
    p("fórmula do lado verdadeiro", r.formula_lado("V") == "=IFERROR(AND(IF('X'!A1,TRUE,FALSE)),\"ERRO\")")
    p("fórmula do lado falso", r.formula_lado("F") == "=IFERROR(AND(IF('X'!A1,FALSE,TRUE)),\"ERRO\")")
    return ok


def relatorio_cobertura(cob: dict, cobertos: set, parcial: bool, matriz: list[Ramo], origem: str) -> list:
    """Grava build/cobertura-v44.md e devolve a lista dos lados descobertos que não estão em NAO_COBERTOS."""
    todos = [(cel, r, lado) for cel, (r, lado, _) in cob.items()]
    desc = [(cel, r, lado) for cel, r, lado in todos if cel not in cobertos]
    aprov = [(c, r, l) for c, r, l in desc if (r.aba, r.cel, r.indice, l) in NAO_COBERTOS]
    falta = [(c, r, l) for c, r, l in desc if (r.aba, r.cel, r.indice, l) not in NAO_COBERTOS]
    L = ["# Cobertura de ramos da V4.3 nas abas 03 a 14 (TC-WB44-006)", "",
         f"Medição: {origem}; valores sintéticos de teste, não dados do carro.", "",
         f"- Lados medidos: {len(todos)} ({len(cob) // 2} ramos); cobertos: {len(todos) - len(desc)}; descobertos: {len(desc)} "
         f"(na lista aprovada: {len(aprov)}; fora dela: {len(falta)}).",
         f"- Ramos `matriz=True` (fora da aba auxiliar): {len(matriz)}.",
         f"- Medição parcial (nem todos os casos): {'sim' if parcial else 'não'}.", ""]
    L += ["## Lados descobertos fora da lista aprovada (proposta de NAO_COBERTOS)", "",
          "| aba | célula | tipo | índice | lado | condição | caminho |", "|---|---|---|---|---|---|---|"]
    for c, r, l in falta:
        L.append(f"| {r.aba} | {r.cel} | {r.tipo} | {r.indice} | {l} | `{r.condicao[:140]}` | "
                 f"{len(r.caminho)} nível(is) |")
    L += ["", "## Lados descobertos na lista aprovada", ""]
    for c, r, l in aprov:
        L.append(f"- {r.aba}!{r.cel} #{r.indice} {r.tipo} {l}: {NAO_COBERTOS[(r.aba, r.cel, r.indice, l)]}")
    L += ["", f"## Ramos em matriz ({MOTIVO_MATRIZ})", ""]
    for r in matriz:
        L.append(f"- {r.aba}!{r.cel} #{r.indice} {r.tipo}: `{r.condicao[:140]}`")
    L.append("")
    RELATORIO_COBERTURA.parent.mkdir(exist_ok=True)
    RELATORIO_COBERTURA.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return falta


# ---------------------------------------------------------------- TC-WB44-005
def main():
    t_ini = time.perf_counter()
    motor, detalhe = rc.escolher()
    if motor is None:
        print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({detalhe})")
        sys.exit(3)
    print(f"MOTOR: {motor} ({detalhe})")
    v44 = caminho_v44()
    print(f"V4.4 sob teste: {v44}")
    print(f"Casos: {ROTULO}; semente {SEMENTE}; N = {N_PERTURBADOS}; faixa ±{FAIXA:.0%}")

    nv43 = volateis(V43_EXCEL)
    nv44 = volateis(v44)
    check("TC-WB44-005 sem funções voláteis", nv43 == 0 and nv44 == 0, f"V4.3 {nv43}, V4.4 {nv44}")

    forms44, nomes44 = formulas(v44)
    fecho = fecho_dependentes(forms44, nomes44, EXCLUIDAS_BASE)
    EXCLUIDAS_VALOR.update(fecho)
    check("TC-WB44-005 fecho de dependentes das exceções X2 a X5 vazio", not fecho,
          f"{len(fecho)} célula(s) {sorted(fecho)[:8]}")
    n_form = len(forms44)
    del forms44

    lista_casos = casos()
    wb43 = openpyxl.load_workbook(V43_EXCEL)
    try:
        ok_ramos = pre_checagem_ramos(wb43)
        cob = aba_cobertura(wb43)
        matriz = [r for r in todos_os_ramos(wb43) if r.matriz]
    finally:
        wb43.close()
    check("TC-WB44-006 pré-checagem: contagem de ramos e tamanho das fórmulas", ok_ramos,
          f"{len(cob)} lados em {len(cob) // 2} ramos; {len(matriz)} ramo(s) em matriz")
    assin = assinatura_layout(cob)
    PASTA_COBERTURA.mkdir(parents=True, exist_ok=True)
    medidos_agora = set()
    dif_total, fora_do_limite = 0, []
    tempos = []
    nominal = None          # valores da V4.3 no caso NOMINAL, para provar que a perturbação chega às saídas
    sem_efeito = []
    for nome, alt in lista_casos:
        t0 = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="dds_t15_", ignore_cleanup_errors=True) as d:
            d = Path(d)
            a = g44._copia(d, lambda wb: (montar_cobertura(wb), aplicar_celulas(wb, alt)), so_nomes(alt), "v43.xlsx")   # V4.3 + zz_COBERTURA (só nesta cópia, D4)
            b = copia_v44_de_arquivo(v44, alt, d / "v44.xlsx")
            for arq in (a, b):
                if motor == "excel":
                    rc._excel_recalc(str(arq.resolve()), 1800)
                else:
                    rc._libreoffice(str(arq.resolve()), 1800)
            cov = {}
            va, vb = valores_recalculados(a, cov), valores_recalculados(b)
        (PASTA_COBERTURA / f"{nome}.json").write_text(
            json.dumps({"layout": assin, "verdadeiros": sorted(c for c, v in cov.items() if v is True)}), encoding="utf-8")
        medidos_agora.add(nome)
        n_err = sum(1 for v in cov.values() if v == "ERRO")
        print(f"COBERTURA {nome}: {sum(1 for v in cov.values() if v is True)} lado(s) verdadeiro(s) de {len(cob)}, "
              f"{n_err} célula(s) da zz_COBERTURA em erro (condição não avaliável, nunca conta como coberta)")
        chaves = (set(va) | set(vb)) - EXCLUIDAS_VALOR
        difs = [(k, va.get(k), vb.get(k)) for k in sorted(chaves) if not iguais_celula(va.get(k), vb.get(k))]
        ea = sum(1 for k, v in va.items() if _eh_erro(v) and k not in EXCLUIDAS_VALOR)
        eb = sum(1 for k, v in vb.items() if _eh_erro(v) and k not in EXCLUIDAS_VALOR)
        dt = time.perf_counter() - t0
        tempos.append(dt)
        aviso = ""
        if max(ea, eb) > 0.5 * n_form:
            aviso = "  AVISO: mais de 50 % das fórmulas dão erro"
        if nome == "NOMINAL":
            nominal = {k: v for k, v in va.items() if k not in EXCLUIDAS_VALOR}
            efeito = ""
        elif nominal is not None:
            n_ef = sum(1 for k in (set(va) | set(nominal)) - EXCLUIDAS_VALOR
                       if not iguais_celula(va.get(k), nominal.get(k)))
            efeito = f", {n_ef} célula(s) da V4.3 diferem do NOMINAL"
            if n_ef == 0:
                sem_efeito.append(nome)
        else:
            efeito = ", efeito não medido (sem NOMINAL na execução)"
        print(f"CASO {nome}: motor {motor}, {dt:.1f} s, {len(chaves)} células comparadas, erros V4.3 {ea} / V4.4 {eb}, "
              f"{len(difs)} diferença(s){efeito}; {ROTULO}{aviso}")
        for k, x, y in difs[:20]:
            print(f"    DIF {k[0]}!{k[1]}: V4.3={x!r} V4.4={y!r}")
        dif_total += len(difs)
        if difs:
            fora_do_limite.append(nome)
        if dt > LIMITE_S:
            print(f"PARE: {dt:.1f} s no caso {nome} passa do limite de {LIMITE_S:.0f} s (A4); N não é reduzido.")
            break
    check("TC-WB44-005", dif_total == 0 and len(tempos) == len(lista_casos) and not sem_efeito,
          f"{len(tempos)} de {len(lista_casos)} caso(s), {dif_total} diferença(s)"
          + (f", casos com diferença: {fora_do_limite}" if fora_do_limite else "")
          + (f", casos sem efeito nas saídas (iguais ao NOMINAL): {sem_efeito}" if sem_efeito else ""))

    if os.environ.get("DDS_CASOS44", "").strip():
        # Subconjunto de casos (a mutação usa NOMINAL,P01,P02,P03): a união dos lados verdadeiros não fecha, então o TC-WB44-006
        # não é avaliado (nem conta como PASS ou FAIL). Sem DDS_CASOS44, a rodada completa o exige inteiro.
        print(f"TC-WB44-006 PULADO: DDS_CASOS44 restringe os casos ({len(lista_casos)}); a cobertura só vale na rodada completa")
    else:
        # TC-WB44-006: união dos lados verdadeiros por caso (arquivos de casos anteriores valem se o layout da aba é o mesmo)
        cobertos, faltam_caso = set(), []
        for nome, _ in lista_casos:
            arq = PASTA_COBERTURA / f"{nome}.json"
            dados = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
            if dados is None or dados["layout"] != assin:
                faltam_caso.append(nome)
            else:
                cobertos |= set(dados["verdadeiros"])
        antigos = len(lista_casos) - len(faltam_caso) - len(medidos_agora & {n for n, _ in lista_casos})
        falta = relatorio_cobertura(cob, cobertos, bool(faltam_caso), matriz,
                                    f"{len(medidos_agora)} caso(s) nesta execução, {antigos} de execuções anteriores, mesmo layout {assin}")
        check("TC-WB44-006", not falta and not faltam_caso,
              f"{len(cob)} lados, {len(cobertos & set(cob))} cobertos, {len(falta)} descoberto(s) fora de NAO_COBERTOS "
              f"({len(NAO_COBERTOS)} aprovados), {len(matriz)} ramo(s) em matriz; casos sem medição: {faltam_caso}; "
              f"relatório {RELATORIO_COBERTURA.relative_to(RAIZ)}")
    print(f"Tempo por caso: média {sum(tempos) / max(1, len(tempos)):.1f} s, máximo {max(tempos, default=0):.1f} s; "
          f"total {time.perf_counter() - t_ini:.0f} s")


if __name__ == "__main__":
    ok_pre = pre_checagem()
    print(f"Pré-checagem pura (fora da contagem): {'OK' if ok_pre else 'FALHOU'}")
    if not ok_pre:
        sys.exit(2)
    main()
    n_pass = sum(1 for _, s in results if s == "PASS")
    n_fail = sum(1 for _, s in results if s == "FAIL")
    print("\n--- Resumo ---")
    print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
    sys.exit(1 if n_fail else 0)
