"""Recálculo de cópias da planilha para o test_workbook (EDR-044).

Substitui o recalc.py da skill xlsx do sandbox (/mnt/skills, LibreOffice), que não
existe nesta máquina. Dois motores, com o mesmo resultado no experimento
(docs/migracao/experimento-recalculo-libreoffice-x-excel.md):
- Excel via COM (pywin32): instância própria e invisível, CalculateFull + Save;
- LibreOffice headless: a mesma macro do recalc.py (calculateAll + store).
Padrão: Excel quando houver; senão LibreOffice. DDS_RECALC=excel|libreoffice força
um motor. Só abre os arquivos que recebe (cópias); o EDR-008 continua valendo para
a planilha entregue.

recalcular() devolve o mesmo dicionário do recalc.py: status, total_errors,
error_summary e total_formulas. Uma falha do motor interrompe o teste com exceção
(RuntimeError, com_error ou TimeoutExpired), e toda fórmula precisa ter valor depois
do recálculo: o teste nunca segue com uma planilha não recalculada.

A instância do Excel entra num Job Object do Windows com KILL_ON_JOB_CLOSE: se o
Python morrer sem rodar o atexit (timeout do rodar_testes, terminal fechado), o
Windows encerra essa instância junto. Encerramentos forçados usam só o PID dela,
nunca o nome do programa; o Excel aberto pelo usuário não é tocado.
"""
import atexit
import os
import threading
import shutil
import subprocess
import tempfile
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.formula import ArrayFormula

ERROS = ["#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A",  # recalc.py
         "#SPILL!", "#CALC!", "#FIELD!", "#BLOCKED!", "#CONNECT!", "#BUSY!", "#UNKNOWN!", "#GETTING_DATA"]  # Excel
MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>"""
_SOFFICE_WINDOWS = [r"C:\Program Files\LibreOffice\program\soffice.exe",
                    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]
_excel = None
_excel_pid = None
_excel_job = None  # mantém o Job Object vivo enquanto o Python viver


def _soffice() -> str | None:
    return shutil.which("soffice") or next((p for p in _SOFFICE_WINDOWS if os.path.exists(p)), None)


def _proteger_contra_orfao(pid: int):
    """Põe a instância num Job Object que o Windows encerra quando este processo morre."""
    import win32api, win32con, win32job
    job = win32job.CreateJobObject(None, "")
    info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    info["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)
    h = win32api.OpenProcess(win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE, False, pid)
    try:
        win32job.AssignProcessToJobObject(job, h)
    finally:
        win32api.CloseHandle(h)
    return job


def _abrir_excel():
    global _excel, _excel_pid, _excel_job
    if _excel is None:
        import win32com.client, win32process
        _excel = win32com.client.DispatchEx("Excel.Application")  # nunca a instância do usuário
        atexit.register(_fechar_excel)  # antes de qualquer outra chamada que possa falhar
        try:
            _excel_pid = win32process.GetWindowThreadProcessId(_excel.Hwnd)[1]
            _excel_job = _proteger_contra_orfao(_excel_pid)
            _excel.Visible = False
            _excel.DisplayAlerts = False
            _excel.ScreenUpdating = False
            _excel.EnableEvents = False
            _excel.AskToUpdateLinks = False
        except Exception:
            _fechar_excel()
            raise
    return _excel


def _matar_excel():
    """Encerra a instância do teste pelo PID guardado (nunca por nome)."""
    if _excel_pid:
        import win32api, win32con
        try:
            h = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, _excel_pid)
            win32api.TerminateProcess(h, 1)
            win32api.CloseHandle(h)
        except Exception:
            pass  # já tinha saído


def _fechar_excel():
    global _excel, _excel_pid
    xl, _excel = _excel, None
    if xl is not None:
        try:
            xl.Quit()
        except Exception:
            _matar_excel()
    _excel_pid = None


def escolher() -> tuple[str | None, str]:
    """(motor, detalhe) ou (None, motivo). O motor só é escolhido se de fato abrir.

    Um DDS_RECALC inválido, ou um motor pedido por DDS_RECALC que não abre, é erro (e
    não "sem motor"): nada pode transformar o teste em NÃO EXECUTÁVEL sem ninguém
    perceber. Se o Excel falhar e o LibreOffice assumir, o motivo vai no detalhe."""
    pedido = os.environ.get("DDS_RECALC", "").strip().lower()
    if pedido not in ("", "excel", "libreoffice"):
        raise ValueError(f"DDS_RECALC inválido: {pedido!r} (use excel ou libreoffice)")
    motivos = []
    if pedido in ("", "excel"):
        try:
            xl = _abrir_excel()
            return "excel", f"Excel {xl.Version} via COM, PID {_excel_pid}"
        except Exception as e:  # sem pywin32, sem Excel ou COM indisponível
            if pedido == "excel":
                raise RuntimeError(f"DDS_RECALC=excel, mas o Excel não abriu: {type(e).__name__}: {e}") from e
            motivos.append(f"Excel indisponível ({type(e).__name__}: {e})")
    if pedido in ("", "libreoffice"):
        so = _soffice()
        if so:
            extra = f"; {'; '.join(motivos)}" if motivos else ""
            return "libreoffice", f"LibreOffice em {so}{extra}"
        if pedido == "libreoffice":
            raise RuntimeError("DDS_RECALC=libreoffice, mas o soffice não foi encontrado")
        motivos.append("LibreOffice (soffice) não encontrado")
    return None, "; ".join(motivos)


def _resumo(caminho: str) -> dict:
    wb = load_workbook(caminho, data_only=True)
    det = {e: [] for e in ERROS}
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str):
                    for e in ERROS:
                        if e in c.value:
                            det[e].append(f"{ws.title}!{c.coordinate}")
                            break
    wb.close()
    wbf = load_workbook(caminho, data_only=False)
    wbv = load_workbook(caminho, data_only=True)
    n, sem_valor = 0, []
    for ws in wbf.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value.text if isinstance(c.value, ArrayFormula) else c.value
                if isinstance(v, str) and v.startswith("="):
                    n += 1
                    if wbv[ws.title][c.coordinate].value is None:
                        sem_valor.append(f"{ws.title}!{c.coordinate}")
    wbf.close()
    wbv.close()
    if sem_valor:  # o openpyxl apaga o cache ao salvar: fórmula sem valor = não recalculada
        raise RuntimeError(f"{len(sem_valor)} fórmula(s) sem valor depois do recálculo: {sem_valor[:5]}")
    total = sum(len(v) for v in det.values())
    return {"status": "success" if total == 0 else "errors_found", "total_errors": total,
            "error_summary": {e: {"count": len(l), "locations": l[:100]} for e, l in det.items() if l},
            "total_formulas": n}


def _libreoffice(caminho: str, timeout: int) -> None:
    so = _soffice()
    antes = os.stat(caminho).st_mtime_ns
    with tempfile.TemporaryDirectory(prefix="lo_perfil_", ignore_cleanup_errors=True) as perfil:
        url = Path(perfil).as_uri()
        subprocess.run([so, "--headless", "--terminate_after_init", f"-env:UserInstallation={url}"],
                       capture_output=True, timeout=timeout)
        pasta = Path(perfil) / "user" / "basic" / "Standard"
        if not pasta.exists():
            raise RuntimeError("o LibreOffice não criou o perfil temporário")
        (pasta / "Module1.xba").write_text(MACRO, encoding="utf-8")
        r = subprocess.run([so, "--headless", "--norestore", f"-env:UserInstallation={url}",
                            "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
                            caminho], capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            raise RuntimeError(f"soffice saiu com {r.returncode}: {r.stderr.strip()}")
    if os.stat(caminho).st_mtime_ns == antes:
        raise RuntimeError("o LibreOffice não regravou o arquivo (outra instância aberta?)")


def _excel_recalc(caminho: str, timeout: int) -> None:
    antes = os.stat(caminho).st_mtime_ns
    xl = _abrir_excel()
    vigia = threading.Timer(timeout, _matar_excel)  # o COM não tem timeout próprio
    vigia.start()
    try:
        wb = xl.Workbooks.Open(caminho, UpdateLinks=0, ReadOnly=False)
        try:
            if wb.ReadOnly:
                raise RuntimeError(f"o Excel abriu {caminho} somente para leitura")
            xl.CalculateFull()
            wb.Save()
        finally:
            wb.Close(SaveChanges=False)
    except Exception as e:
        if vigia.finished.is_set() and not vigia.is_alive():
            raise RuntimeError(f"o Excel passou de {timeout} s e foi encerrado (PID {_excel_pid})") from e
        raise
    finally:
        vigia.cancel()
    if os.stat(caminho).st_mtime_ns == antes:
        raise RuntimeError("o Excel não regravou o arquivo")


def recalcular(caminho: str, motor: str, timeout: int = 120) -> dict:
    caminho = str(Path(caminho).resolve())
    if motor == "excel":
        _excel_recalc(caminho, timeout)
    elif motor == "libreoffice":
        _libreoffice(caminho, timeout)
    else:
        raise RuntimeError(f"motor desconhecido: {motor!r}")
    return _resumo(caminho)
