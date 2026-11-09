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
opção válida) e os dirigidos D3: DIR_ORIGENS_VAZIAS, DIR_CHAVES_INVERTIDAS, DIR_NUMERICAS_VAZIAS, DIR_ESQUERDA. Os 24 nomes novos da
V4.4 não são perturbados. Os valores são sintéticos de teste (não são dados do carro). DDS_CASOS44 (lista separada por vírgula)
restringe os casos; vazio = todos. "Passou" = a V4.4 reproduz a V4.3; não é validação física.
"""
import math
import os
import random
import re
import sys
import tempfile
import time
from pathlib import Path

import openpyxl
from openpyxl.worksheet.formula import ArrayFormula

import aba_equilibrio as ae
import dados_planilha as dp
import gerar_v4_4 as g44
import raizes
import recalculo_planilha as rc
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


def casos() -> list[tuple[str, dict]]:
    numericos, listas, vals = _valores_v43()
    out = [("NOMINAL", {})]
    for i in range(1, N_PERTURBADOS + 1):
        out.append((f"P{i:02d}", perturbar(vals, numericos, listas, random.Random(SEMENTE + i))))
    org = [n for n in listas if n.startswith("org_")]
    out.append(("DIR_ORIGENS_VAZIAS", {n: None for n in org}))
    out.append(("DIR_CHAVES_INVERTIDAS", {n: (1 - v) for n, v in vals.items() if "chave_h" in n and v in (0, 1)}))
    out.append(("DIR_NUMERICAS_VAZIAS", {n: None for n in numericos}))
    out.append(("DIR_ESQUERDA", {"ent_16_sentido_da_curva": "Esquerda"}))
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


def valores_recalculados(caminho: Path) -> dict[tuple[str, str], object]:
    wb = openpyxl.load_workbook(caminho, data_only=True)
    out = {}
    try:
        for ws in wb.worksheets:
            if ws.title == ABA_COBERTURA:
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


def copia_v44_de_arquivo(origem: Path, alteracoes: dict, destino: Path) -> Path:
    wb = openpyxl.load_workbook(origem)
    try:
        for nome, valor in alteracoes.items():
            aba, cel = ae._destino(wb, nome)
            wb[aba][cel].value = valor
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
    return ok


def volateis(caminho: Path) -> int:
    forms, _ = formulas(caminho)
    return sum(1 for f in forms.values() if VOLATEIS.search(f))


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
    dif_total, fora_do_limite = 0, []
    tempos = []
    for nome, alt in lista_casos:
        t0 = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="dds_t15_", ignore_cleanup_errors=True) as d:
            d = Path(d)
            a = g44.copia_v43(d, alt, nome="v43.xlsx")
            b = copia_v44_de_arquivo(v44, alt, d / "v44.xlsx")
            for arq in (a, b):
                if motor == "excel":
                    rc._excel_recalc(str(arq.resolve()), 1800)
                else:
                    rc._libreoffice(str(arq.resolve()), 1800)
            va, vb = valores_recalculados(a), valores_recalculados(b)
        chaves = (set(va) | set(vb)) - EXCLUIDAS_VALOR
        difs = [(k, va.get(k), vb.get(k)) for k in sorted(chaves) if not iguais_celula(va.get(k), vb.get(k))]
        ea = sum(1 for k, v in va.items() if _eh_erro(v) and k not in EXCLUIDAS_VALOR)
        eb = sum(1 for k, v in vb.items() if _eh_erro(v) and k not in EXCLUIDAS_VALOR)
        dt = time.perf_counter() - t0
        tempos.append(dt)
        aviso = ""
        if max(ea, eb) > 0.5 * n_form:
            aviso = "  AVISO: mais de 50 % das fórmulas dão erro"
        print(f"CASO {nome}: motor {motor}, {dt:.1f} s, {len(chaves)} células comparadas, erros V4.3 {ea} / V4.4 {eb}, "
              f"{len(difs)} diferença(s); {ROTULO}{aviso}")
        for k, x, y in difs[:20]:
            print(f"    DIF {k[0]}!{k[1]}: V4.3={x!r} V4.4={y!r}")
        dif_total += len(difs)
        if difs:
            fora_do_limite.append(nome)
        if dt > LIMITE_S:
            print(f"PARE: {dt:.1f} s no caso {nome} passa do limite de {LIMITE_S:.0f} s (A4); N não é reduzido.")
            break
    check("TC-WB44-005", dif_total == 0 and len(tempos) == len(lista_casos),
          f"{len(tempos)} de {len(lista_casos)} caso(s), {dif_total} diferença(s)"
          + (f", casos com diferença: {fora_do_limite}" if fora_do_limite else ""))
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
