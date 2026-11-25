r"""
Monta o pacote autônomo do posicionador para o Fusion (fase 2): uma pasta `T11_posicionador/` pronta para copiar em
`%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\` (ou adicionar em Scripts and Add-ins > "+"), mais o .zip.
Contém o script, o manifesto, os módulos Python necessários (sem numpy/scipy), os dados e o LEIA-ME. Só biblioteca padrão.

Uso: uv run python -X utf8 tools/empacotar_fusion.py [--saida PASTA]        (padrão: build/fusion/)
"""
import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE_SCRIPT = RAIZ / "docs" / "posicionador" / "fusion" / "T11_posicionador"
MODULOS = ["__init__.py", "config.py", "reconhecimento.py", "identificacao.py"]
DADOS = ["config_T11.json", "hardpoints_T11_v20_1_cad.csv", "hardpoints_T11_v20_1_cad.meta.json", "origem_v20_script.json"]


def montar(destino_pai):
    pasta = Path(destino_pai) / "T11_posicionador"
    if pasta.exists():
        shutil.rmtree(pasta)
    (pasta / "python" / "posicionador").mkdir(parents=True)
    (pasta / "data" / "posicionador").mkdir(parents=True)
    for nome in ("T11_posicionador.py", "T11_posicionador.manifest", "LEIA-ME.md", "posicionador_config.json"):
        shutil.copy2(FONTE_SCRIPT / nome, pasta / nome)
    pk = RAIZ / "python" / "posicionador"
    for m in MODULOS:
        shutil.copy2(pk / m, pasta / "python" / "posicionador" / m)
    for sub in ("puro", "fusion"):
        shutil.copytree(pk / sub, pasta / "python" / "posicionador" / sub, ignore=shutil.ignore_patterns("__pycache__"))
    for d in DADOS:
        shutil.copy2(RAIZ / "data" / "posicionador" / d, pasta / "data" / "posicionador" / d)
    zpath = Path(destino_pai) / "T11_posicionador.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pasta.rglob("*")):
            if f.is_file():
                z.write(f, Path("T11_posicionador") / f.relative_to(pasta))
    return pasta, zpath


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default=str(RAIZ / "build" / "fusion"))
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    pasta, z = montar(a.saida)
    print(f"pacote: {pasta}\nzip: {z} ({z.stat().st_size / 1024:.0f} KB)")
    sys.exit(0)
