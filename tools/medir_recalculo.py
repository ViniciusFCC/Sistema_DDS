"""Medição do recálculo da planilha pelo Excel (COM), sem instância residual (V4.2, Task 6).

Uso (Git Bash, depois de export UV_SYSTEM_CERTS=1):
    uv run python -X utf8 tools/medir_recalculo.py [ARQ] [--n 3] [--saida docs/v4-2/medicao-recalculo-v4-1.md]

Sem ARQ, extrai `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` da tag `v4.1` (git show). O arquivo medido é sempre uma
CÓPIA em pasta temporária: a planilha de excel/ e a viva do Drive nunca são abertas (EDR-044, EDR-063).

Por execução, numa instância nova do Excel (DispatchEx, no Job Object de tests/recalculo_planilha.py), mede em
separado: abrir, CalculateFull, gravar e fechar (Workbook.Close + Application.Quit). Depois confere que o PID da
instância saiu. Conta os processos EXCEL.EXE antes e depois; se já houver algum antes (pode ser do usuário), avisa,
mede assim mesmo e registra o número. Nunca encerra processo por nome.

Saída: 0 = gravado; 1 = sobrou instância da ferramenta; 3 = NÃO EXECUTÁVEL (sem Excel/pywin32). Texto em UTF-8, LF.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))   # recalculo_planilha mora em tests/

import recalculo_planilha as rc  # noqa: E402

ORIGEM_TAG = "v4.1:excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx"
SAIDA_PADRAO = RAIZ / "docs" / "v4-2" / "medicao-recalculo-v4-1.md"


def contar_excel() -> int:
    """Número de processos EXCEL.EXE no sistema (qualquer dono)."""
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE", "/FO", "CSV", "/NH"],
                       capture_output=True, text=True, errors="replace")
    return sum(1 for ln in r.stdout.splitlines() if ln.lower().startswith('"excel.exe"'))


def pid_vivo(pid: int) -> bool:
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                       capture_output=True, text=True, errors="replace")
    return any(ln.lower().startswith('"excel.exe"') for ln in r.stdout.splitlines())


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


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
        t0 = time.perf_counter()
        xl.CalculateFull()
        t["calcular"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        wb.Save()
        t["gravar"] = time.perf_counter() - t0
        t0 = time.perf_counter()
        wb.Close(SaveChanges=False)
        wb = None
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
        rc._fechar_excel()
    # a instância precisa sair (o Quit é assíncrono: espera até 30 s)
    for _ in range(60):
        if not pid_vivo(pid):
            break
        time.sleep(0.5)
    t["saiu"] = not pid_vivo(pid)
    return t


def fmt(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arq", nargs="?", help="planilha a medir (copiada antes); padrão: V4.1 da tag v4.1")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--saida", default=str(SAIDA_PADRAO))
    a = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="medir_recalculo_") as pasta:
        copia = Path(pasta) / "medida.xlsx"
        if a.arq:
            origem = Path(a.arq)
            if "Google" in str(origem) or str(origem).upper().startswith("H:"):
                print("recusado: a viva do Drive nunca é aberta; passe uma cópia local", file=sys.stderr)
                return 2
            shutil.copyfile(origem, copia)
            rotulo = origem.name
        else:
            dados = subprocess.run(["git", "show", ORIGEM_TAG], cwd=RAIZ, capture_output=True, check=True).stdout
            copia.write_bytes(dados)
            rotulo = f"{ORIGEM_TAG} (tag v4.1)"
        sha_origem = sha(copia)

        antes = contar_excel()
        if antes:
            print(f"AVISO: {antes} processo(s) EXCEL.EXE já existiam antes (não serão tocados).", file=sys.stderr)
        try:
            motor, detalhe = rc.escolher()
        except Exception as e:
            print(f"NÃO EXECUTÁVEL: {e}", file=sys.stderr)
            return 3
        if motor != "excel":
            print(f"NÃO EXECUTÁVEL: {detalhe}", file=sys.stderr)
            return 3
        versao_excel = detalhe
        rc._fechar_excel()               # a sonda de escolher() abriu uma instância; cada execução abre a sua
        time.sleep(1)

        execs = []
        for i in range(a.n):
            e = uma_execucao(copia)
            execs.append(e)
            print(f"execução {i + 1}: abrir {fmt(e['abrir'])} s, calcular {fmt(e['calcular'])} s, "
                  f"gravar {fmt(e['gravar'])} s, fechar {fmt(e['fechar'])} s, saiu={e['saiu']}")
        depois = contar_excel()

    ok_pids = all(e["saiu"] for e in execs)
    sobra = depois - antes
    linhas = [
        "# Medição do recálculo da V4.1 sem Excel residual",
        "",
        "Gerado por `tools/medir_recalculo.py`. Não edite à mão: rode de novo.",
        "",
        f"- Data: {dt.date.today().isoformat()}.",
        f"- Arquivo medido: {rotulo}, em cópia temporária (SHA-256 `{sha_origem}`). A planilha de `excel/` e a viva do Drive não foram abertas.",
        f"- Motor: {versao_excel.split(', PID')[0]}; Windows {platform.version()}; Python {platform.python_version()}.",
        f"- Execuções: {a.n}, cada uma numa instância nova do Excel (invisível, alertas desligados).",
        "",
        "## Tempos por execução (segundos)",
        "",
        "| Execução | Abrir | CalculateFull | Gravar | Fechar | Total | Instância saiu |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(execs, 1):
        tot = e["abrir"] + e["calcular"] + e["gravar"] + e["fechar"]
        linhas.append(f"| {i} | {fmt(e['abrir'])} | {fmt(e['calcular'])} | {fmt(e['gravar'])} | {fmt(e['fechar'])} | "
                      f"{fmt(tot)} | {'sim' if e['saiu'] else 'não'} |")
    if len(execs) > 1:
        linhas.append("| Mediana | " + " | ".join(
            fmt(statistics.median(e[k] for e in execs)) for k in ("abrir", "calcular", "gravar", "fechar")) +
            " | " + fmt(statistics.median(e['abrir'] + e['calcular'] + e['gravar'] + e['fechar'] for e in execs)) + " | |")
    linhas += [
        "",
        "## Processos EXCEL.EXE",
        "",
        f"- Antes da medição: {antes}.",
        f"- Depois da medição: {depois}.",
        f"- Diferença: {sobra:+d}. " + ("Nenhuma instância da ferramenta ficou viva."
                                        if ok_pids and sobra <= 0 else "SOBROU instância: investigar."),
        "- A ferramenta confere o PID de cada instância depois do `Quit` e nunca encerra processo por nome.",
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
