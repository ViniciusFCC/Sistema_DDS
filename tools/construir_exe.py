"""
Constrói o executável único do posicionador (`posicionador_T11.exe` no Windows; `posicionador_T11` em Linux/macOS) com o
PyInstaller, a partir de `tools/posicionador_exe.py`.

Uso, na raiz do repositório, num Python com numpy, scipy, cadquery-ocp e pyinstaller:
    python tools/construir_exe.py [--saida dist]

Vai dentro do executável: o código de `python/` e `tools/`, os dados de `data/posicionador/`, o STEP de exemplo de
`data/cad/` e as bibliotecas do OpenCascade e do vtk (`cadquery_ocp.libs`, `vtk.libs`). O matplotlib fica de fora (só serve às
figuras, que a ferramenta já trata como opcionais). Para o executável rodar, o Windows precisa só de si mesmo: nada a instalar.

Observação: um executável "onefile" se descompacta numa pasta temporária a cada execução, o que leva alguns segundos antes de
o programa começar. É o preço de ter um arquivo só.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEP = ";" if os.name == "nt" else ":"


def _bibliotecas_ocp():
    """Pastas `*.libs` irmãs do pacote OCP (DLLs/SOs do OpenCascade e do vtk, com nome de hash)."""
    import OCP
    sp = Path(OCP.__file__).resolve().parent.parent
    return [p for p in (sp / "cadquery_ocp.libs", sp / "vtk.libs") if p.is_dir()]


def comando(saida):
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--name", "posicionador_T11",
           "--distpath", str(saida), "--workpath", str(RAIZ / "build" / "pyinstaller"), "--specpath", str(RAIZ / "build"),
           "--paths", str(RAIZ / "python"), "--paths", str(RAIZ / "tools"),
           "--add-data", f"{RAIZ / 'data' / 'posicionador'}{SEP}data/posicionador",
           "--add-data", f"{RAIZ / 'data' / 'cad'}{SEP}data/cad",
           "--hidden-import", "OCP", "--collect-binaries", "OCP",
           "--exclude-module", "matplotlib", "--exclude-module", "PIL", "--exclude-module", "IPython",
           str(RAIZ / "tools" / "posicionador_exe.py")]
    # As pastas `*.libs` mantêm o nome e ficam ao lado do pacote OCP dentro do executável: o `OCP/__init__.py` do Windows chama
    # `os.add_dll_directory(<pacote>/../cadquery_ocp.libs)` e `.../vtk.libs` (o do vtk sem checar se existe), e no Linux o RPATH
    # do OpenCascade é `$ORIGIN/../cadquery_ocp.libs`. Achatar as bibliotecas na raiz quebra a importação.
    for pasta in _bibliotecas_ocp():
        for arq in sorted(pasta.iterdir()):
            if arq.is_file():
                binaria = arq.suffix.lower() in (".dll", ".pyd", ".so") or ".so." in arq.name
                cmd[-1:-1] = ["--add-binary" if binaria else "--add-data", f"{arq}{SEP}{pasta.name}"]
    return cmd


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--saida", default=str(RAIZ / "dist"))
    a = ap.parse_args()
    cmd = comando(Path(a.saida))
    print(f"PyInstaller com {sum(c in ('--add-binary', '--add-data') for c in cmd) - 2} arquivos de bibliotecas do OpenCascade/vtk")
    r = subprocess.run(cmd, cwd=RAIZ)
    if r.returncode:
        raise SystemExit(r.returncode)
    exe = Path(a.saida) / ("posicionador_T11.exe" if os.name == "nt" else "posicionador_T11")
    print(f"executável: {exe} ({exe.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
