"""CA-01: cria (opcional) e verifica o backup zip de importado-claude-ai/.

Uso:
    uv run python -X utf8 tools/verificar_backup.py --criar  ZIP
    uv run python -X utf8 tools/verificar_backup.py          ZIP

Verificação: mesmo número de arquivos e mesmo SHA-256 de cada arquivo entre o
zip e a pasta, e o SHA-256 do zip igual ao registrado no .txt ao lado.
Só lê importado-claude-ai/; nunca escreve nela.
"""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "importado-claude-ai"


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def hashes_pasta() -> dict[str, str]:
    return {
        p.relative_to(RAIZ).as_posix(): sha256_arquivo(p)
        for p in sorted(PASTA.rglob("*"))
        if p.is_file()
    }


def criar(zip_path: Path) -> None:
    if zip_path.exists():
        sys.exit(f"ERRO: {zip_path} já existe; não sobrescrevo.")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PASTA.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(RAIZ).as_posix())
    txt = zip_path.with_suffix(".sha256.txt")
    txt.write_text(f"{sha256_arquivo(zip_path)}  {zip_path.name}\n", encoding="utf-8")
    print(f"criado: {zip_path}\ncriado: {txt}")


def verificar(zip_path: Path) -> bool:
    ok = True
    txt = zip_path.with_suffix(".sha256.txt")
    registrado = txt.read_text(encoding="utf-8").split()[0]
    atual = sha256_arquivo(zip_path)
    print(f"SHA-256 do zip: {atual}")
    if atual != registrado:
        print(f"FAIL: SHA-256 do zip difere do registrado ({registrado})")
        ok = False
    pasta = hashes_pasta()
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:
            print("FAIL: zip corrompido")
            ok = False
        arq = {i.filename: sha256_bytes(z.read(i)) for i in z.infolist() if not i.is_dir()}
    print(f"arquivos na pasta: {len(pasta)} | no zip: {len(arq)}")
    for nome in sorted(set(pasta) | set(arq)):
        if pasta.get(nome) != arq.get(nome):
            print(f"FAIL: {nome}: pasta={pasta.get(nome)} zip={arq.get(nome)}")
            ok = False
    print("CA-01 PASS" if ok else "CA-01 FAIL")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip", type=Path)
    ap.add_argument("--criar", action="store_true")
    a = ap.parse_args()
    if a.criar:
        criar(a.zip)
    sys.exit(0 if verificar(a.zip) else 1)


if __name__ == "__main__":
    main()
