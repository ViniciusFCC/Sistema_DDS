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
error_summary e total_formulas. Uma falha do motor levanta RuntimeError, para o
teste nunca seguir com uma planilha não recalculada.
"""
import atexit
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.formula import ArrayFormula

ERROS = ["#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A"]
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


def _soffice() -> str | None:
    return shutil.which("soffice") or next((p for p in _SOFFICE_WINDOWS if os.path.exists(p)), None)


def _abrir_excel():
    global _excel
    if _excel is None:
        import win32com.client
        _excel = win32com.client.DispatchEx("Excel.Application")  # nunca a instância do usuário
        _excel.Visible = False
        _excel.DisplayAlerts = False
        _excel.ScreenUpdating = False
        _excel.EnableEvents = False
        _excel.AskToUpdateLinks = False
        atexit.register(_fechar_excel)
    return _excel


def _fechar_excel():
    global _excel
    if _excel is not None:
        _excel.Quit()
        _excel = None


def escolher() -> tuple[str | None, str]:
    """(motor, detalhe) ou (None, motivo). O motor só é escolhido se de fato abrir.
    Um DDS_RECALC inválido é erro (ValueError), e não "sem motor": um erro de digitação
    não pode transformar o teste em NÃO EXECUTÁVEL sem ninguém perceber."""
    pedido = os.environ.get("DDS_RECALC", "").strip().lower()
    if pedido not in ("", "excel", "libreoffice"):
        raise ValueError(f"DDS_RECALC inválido: {pedido!r} (use excel ou libreoffice)")
    motivos = []
    if pedido in ("", "excel"):
        try:
            xl = _abrir_excel()
            return "excel", f"Excel {xl.Version} via COM"
        except Exception as e:  # sem pywin32, sem Excel ou COM indisponível
            motivos.append(f"Excel indisponível ({type(e).__name__}: {e})")
    if pedido in ("", "libreoffice"):
        so = _soffice()
        if so:
            return "libreoffice", f"LibreOffice em {so}"
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
    n = 0
    for ws in wbf.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value.text if isinstance(c.value, ArrayFormula) else c.value
                n += isinstance(v, str) and v.startswith("=")
    wbf.close()
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


def _excel_recalc(caminho: str) -> None:
    wb = _abrir_excel().Workbooks.Open(caminho, UpdateLinks=0, ReadOnly=False)
    try:
        _excel.CalculateFull()
        wb.Save()
    finally:
        wb.Close(SaveChanges=False)


def recalcular(caminho: str, motor: str, timeout: int = 120) -> dict:
    caminho = str(Path(caminho).resolve())
    if motor == "excel":
        _excel_recalc(caminho)
    elif motor == "libreoffice":
        _libreoffice(caminho, timeout)
    else:
        raise RuntimeError(f"motor desconhecido: {motor!r}")
    return _resumo(caminho)
