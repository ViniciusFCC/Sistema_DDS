"""Medição do recálculo da planilha pelo Excel (COM), sem instância residual (V4.2, Task 6).

Uso (Git Bash, depois de export UV_SYSTEM_CERTS=1):
    uv run python -X utf8 tools/medir_recalculo.py [ARQ] [--n 3] [--saida docs/v4-2/medicao-recalculo-v4-1.md]

Sem ARQ, extrai `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` da tag `v4.1` (git show). O arquivo medido é sempre uma
CÓPIA em pasta temporária: a planilha de excel/ e a viva do Drive nunca são abertas (EDR-044, EDR-063); ARQ dentro de
excel/ ou da pasta do Drive é recusado (passe uma cópia local), assim como --saida nesses lugares.

Dois cenários, cada execução sobre uma cópia NOVA do arquivo de origem do cenário e numa instância nova do Excel
(DispatchEx, no Job Object de tests/recalculo_planilha.py):
  A) arquivo da tag: sem valores em cache e com fullCalcOnLoad (o Excel calcula tudo dentro de Workbooks.Open);
  B) arquivo já salvo pelo Excel, como a viva: a cópia gravada pela 1ª execução de A, copiada de novo a cada execução.
Mede em separado abrir, CalculateFull, gravar e fechar (Workbook.Close + Application.Quit) e confere que o PID da
instância saiu. Conta os processos EXCEL.EXE antes e depois; se já houver algum antes (pode ser do usuário), avisa,
mede assim mesmo e registra o número. Nunca encerra processo por nome.

Saída: 0 = gravado; 1 = sobrou instância da ferramenta; 2 = recusa; 3 = NÃO EXECUTÁVEL (sem Excel/pywin32). UTF-8, LF.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))    # recalculo_planilha mora em tests/
sys.path.insert(0, str(RAIZ / "python"))

import recalculo_planilha as rc  # noqa: E402
import viva  # noqa: E402

ORIGEM_TAG = "v4.1:excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx"
SAIDA_PADRAO = RAIZ / "docs" / "v4-2" / "medicao-recalculo-v4-1.md"
_CALC = {-4105: "automático", -4135: "manual", 2: "semiautomático"}


def _tasklist(filtro: str) -> list[str]:
    r = subprocess.run(["tasklist", "/FI", filtro, "/FO", "CSV", "/NH"], capture_output=True, text=True, errors="replace")
    return [ln for ln in r.stdout.splitlines() if ln.lower().startswith('"excel.exe"')]


def contar_excel() -> int:
    """Número de processos EXCEL.EXE no sistema (qualquer dono)."""
    return len(_tasklist("IMAGENAME eq EXCEL.EXE"))


def pid_vivo(pid: int) -> bool:
    return bool(_tasklist(f"PID eq {pid}"))


def esperar_saida(pid: int | None, tentativas: int = 60) -> bool:
    """O Quit é assíncrono: espera até tentativas x 0,5 s o PID sair. True se saiu."""
    for _ in range(tentativas):
        if not pid or not pid_vivo(pid):
            return True
        time.sleep(0.5)
    return not pid_vivo(pid)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def estado_do_arquivo(p: Path) -> dict:
    """Lido do próprio arquivo: calcPr do workbook.xml e fórmulas com/sem valor em cache (<v>)."""
    com = sem = 0
    with zipfile.ZipFile(p) as z:
        m = re.search(r"<calcPr[^>]*/?>", z.read("xl/workbook.xml").decode("utf-8"))
        for n in z.namelist():
            if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"):
                for c in re.finditer(r"<c [^>]*?(?<!/)>(.*?)</c>", z.read(n).decode("utf-8"), re.S):
                    if "<f" in c.group(1):
                        if "<v>" in c.group(1):
                            com += 1
                        else:
                            sem += 1
    return {"calcPr": m.group(0) if m else "(ausente)", "com_v": com, "sem_v": sem}


def _ler_config(xl) -> dict:
    """Lê modo de cálculo e threads numa função à parte: os objetos COM intermediários morrem ao sair dela
    (referência viva impediria o Quit de encerrar o processo)."""
    r = {"calculation": _CALC.get(xl.Calculation, str(xl.Calculation))}
    try:
        mt = xl.MultiThreadedCalculation
        r["threads"] = f"{mt.ThreadCount} threads ({'ligado' if mt.Enabled else 'desligado'})"
    except Exception:
        r["threads"] = "não lido"
    return r


def uma_execucao(copia: Path) -> dict:
    """Instância nova: abrir, CalculateFull, gravar, fechar. Tempos em segundos."""
    xl = rc._abrir_excel()
    pid = rc._excel_pid
    t = {"pid": pid}
    wb = None
    try:
        t0 = time.perf_counter()
        wb = xl.Workbooks.Open(str(copia), UpdateLinks=0, ReadOnly=False)
        t["abrir"] = time.perf_counter() - t0
        if wb.ReadOnly:
            raise RuntimeError("o Excel abriu a cópia somente para leitura")
        t.update(_ler_config(xl))
        t0 = time.perf_counter()
        xl.CalculateFull()
        t["calcular"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        wb.Save()
        t["gravar"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        wb.Close(SaveChanges=False)
        wb = None
        gc.collect()
        rc._fechar_excel()               # Application.Quit; cai no PID se o Quit falhar
        xl = None
        t["fechar"] = time.perf_counter() - t0
    finally:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        xl = None
        gc.collect()
        rc._fechar_excel()               # idempotente (zera _excel): no caminho normal, a segunda chamada não faz nada
        # também no caminho de exceção: confere que o PID desta instância saiu antes de a exceção seguir adiante
        t["saiu"] = esperar_saida(pid)
        if not t["saiu"]:
            print(f"AVISO: a instância PID {pid} não saiu", file=sys.stderr)
    return t


def fmt(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def cenario(origem: Path, n: int, pasta: Path, nome: str, guardar: Path | None = None) -> list[dict]:
    execs = []
    for i in range(n):
        copia = pasta / f"{nome}_{i + 1}.xlsx"
        shutil.copyfile(origem, copia)            # cópia nova do arquivo de origem do cenário
        e = uma_execucao(copia)
        if i == 0 and guardar is not None:
            shutil.copyfile(copia, guardar)       # o que o Excel gravou na 1ª execução
        execs.append(e)
        print(f"cenário {nome}, execução {i + 1}: abrir {fmt(e['abrir'])} s, calcular {fmt(e['calcular'])} s, "
              f"gravar {fmt(e['gravar'])} s, fechar {fmt(e['fechar'])} s, saiu={e['saiu']}")
    return execs


def tabela(execs: list[dict]) -> list[str]:
    L = ["| Execução | Abrir | CalculateFull | Gravar | Fechar | Total | Instância saiu |", "|---|---|---|---|---|---|---|"]
    for i, e in enumerate(execs, 1):
        tot = e["abrir"] + e["calcular"] + e["gravar"] + e["fechar"]
        L.append(f"| {i} | {fmt(e['abrir'])} | {fmt(e['calcular'])} | {fmt(e['gravar'])} | {fmt(e['fechar'])} | "
                 f"{fmt(tot)} | {'sim' if e['saiu'] else 'não'} |")
    if len(execs) > 1:
        L.append("| Mediana | " + " | ".join(fmt(statistics.median(e[k] for e in execs))
                 for k in ("abrir", "calcular", "gravar", "fechar")) + " | "
                 + fmt(statistics.median(e["abrir"] + e["calcular"] + e["gravar"] + e["fechar"] for e in execs)) + " | |")
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arq", nargs="?", help="planilha a medir (copiada antes); padrão: V4.1 da tag v4.1")
    ap.add_argument("--n", type=int, default=3, help="execuções por cenário")
    ap.add_argument("--saida", default=str(SAIDA_PADRAO))
    a = ap.parse_args()

    msg = viva.recusa_de_saida(Path(a.saida), [])
    if msg:
        print(f"recusado: {msg}", file=sys.stderr)
        return 2
    if a.arq:
        for pasta_proibida, nome in ((RAIZ / "excel", "excel/"), (viva.PASTA_DRIVE, "a pasta do Drive")):
            if viva.dentro(Path(a.arq), pasta_proibida):
                print(f"recusado: {a.arq} está em {nome}; passe uma cópia local", file=sys.stderr)
                return 2

    with tempfile.TemporaryDirectory(prefix="medir_recalculo_") as d:
        pasta = Path(d)
        origem_a = pasta / "origem_A.xlsx"
        if a.arq:
            shutil.copyfile(a.arq, origem_a)
            rotulo = Path(a.arq).name
        else:
            origem_a.write_bytes(subprocess.run(["git", "show", ORIGEM_TAG], cwd=RAIZ, capture_output=True,
                                                check=True).stdout)
            rotulo = f"`{ORIGEM_TAG}` (tag v4.1)"
        sha_origem = sha(origem_a)
        est_a = estado_do_arquivo(origem_a)

        antes = contar_excel()
        if antes:
            print(f"AVISO: {antes} processo(s) EXCEL.EXE já existiam antes (não serão tocados).", file=sys.stderr)
        try:
            motor, detalhe = rc.escolher()
        except Exception as e:
            print(f"NÃO EXECUTÁVEL: {e}", file=sys.stderr)
            return 3
        sonda = rc._excel_pid
        if motor != "excel":
            print(f"NÃO EXECUTÁVEL: {detalhe}", file=sys.stderr)
            return 3
        rc._fechar_excel()               # a sonda de escolher() abriu uma instância; cada execução abre a sua
        sonda_saiu = esperar_saida(sonda)
        if not sonda_saiu:
            print(f"a instância de sondagem (PID {sonda}) não saiu", file=sys.stderr)

        origem_b = pasta / "origem_B.xlsx"
        execs_a = cenario(origem_a, a.n, pasta, "A", guardar=origem_b)
        est_b = estado_do_arquivo(origem_b)
        execs_b = cenario(origem_b, a.n, pasta, "B")
        depois = contar_excel()

    todas = execs_a + execs_b
    ok_pids = sonda_saiu and all(e["saiu"] for e in todas)   # a falha da sondagem também dá código 1
    sobra = depois - antes
    calc = sorted({e["calculation"] for e in todas})
    thr = sorted({e["threads"] for e in todas})

    def est(e: dict) -> str:
        return (f"`{e['calcPr']}`; fórmulas com valor em cache: {e['com_v']}; fórmulas sem valor em cache: {e['sem_v']}")

    linhas = [
        "# Medição do recálculo da V4.1 sem Excel residual",
        "",
        "Gerado por `tools/medir_recalculo.py`. Não edite à mão: rode de novo.",
        "",
        f"- Data: {dt.date.today().isoformat()}.",
        f"- Arquivo de origem: {rotulo}, SHA-256 `{sha_origem}`. A planilha de `excel/` e a viva do Drive não foram abertas.",
        f"- Motor: {detalhe.split(', PID')[0]}; Windows {platform.version()}; Python {platform.python_version()}.",
        f"- Núcleos lógicos (`os.cpu_count`): {os.cpu_count()}. Cálculo multithread do Excel: {'; '.join(thr)}. "
        f"`Application.Calculation` lido com a pasta aberta: {'; '.join(calc)}.",
        f"- Execuções: {a.n} por cenário, cada uma numa instância nova do Excel (invisível, alertas desligados) e sobre uma "
        "cópia nova do arquivo de origem do cenário.",
        "",
        "## O que cada coluna mede",
        "",
        "- Abrir: `Workbooks.Open`. No cenário A inclui o cálculo de carga (o arquivo pede `fullCalcOnLoad` e nenhuma fórmula tem valor em cache).",
        "- CalculateFull: recálculo completo a quente, depois da carga.",
        "- Gravar: `Workbook.Save`.",
        "- Fechar: `Workbook.Close` mais `Application.Quit`.",
        "- Total: soma das quatro colunas.",
        "- A 1ª execução de cada cenário pode incluir o custo da partida a frio do Excel; esse custo não é separado.",
        "",
        "## Cenário A: arquivo da tag (sem cache, com fullCalcOnLoad)",
        "",
        f"Estado do arquivo de origem, lido dele: {est(est_a)}.",
        "",
        *tabela(execs_a),
        "",
        "## Cenário B: arquivo já salvo pelo Excel (como a viva)",
        "",
        "Origem: a cópia gravada pela 1ª execução do cenário A, copiada de novo a cada execução.",
        f"Estado do arquivo de origem, lido dele: {est(est_b)}.",
        "",
        *tabela(execs_b),
        "",
        "## Processos EXCEL.EXE",
        "",
        f"- Antes da medição: {antes}.",
        f"- Depois da medição: {depois}.",
        f"- Diferença: {sobra:+d}. " + ("Nenhuma instância da ferramenta ficou viva."
                                        if ok_pids and sobra <= 0 else "SOBROU instância: investigar."),
        "- A ferramenta confere o PID de cada instância depois do `Quit` (inclusive a da sondagem inicial) e nunca encerra processo por nome.",
        "",
        "## Limites",
        "",
        "- Os tempos são desta máquina e desta sessão (outros programas abertos mudam o resultado); só a ordem de grandeza vale.",
        "- Mede o Excel via COM; o LibreOffice não entra (CLAUDE.md: não recalcular a planilha por ele).",
        "",
    ]
    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(linhas), encoding="utf-8", newline="\n")
    print(f"EXCEL.EXE antes {antes}, depois {depois}; gravado em {saida}")
    return 0 if ok_pids and sobra <= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
