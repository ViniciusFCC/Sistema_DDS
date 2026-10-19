"""CA-02: copia o inventário do SPEC §4.1 (opcional) e verifica o MANIFEST.sha256.

Uso:
    uv run python -X utf8 tools/verificar_manifest.py --copiar   (só no commit 0)
    uv run python -X utf8 tools/verificar_manifest.py

Formato do MANIFEST.sha256 (uma linha por arquivo, separador de dois espaços):
    <sha256>  <destino relativo à raiz>  <origem relativa à raiz>
Verificação: o hash da origem e o da cópia batem com o registrado. A cópia é
conferida no blob do commit que adicionou o arquivo, porque depois dele os
arquivos podem ter sido editados (o EDR, pelo EDR-043) ou renomeados (EDR-043).
Precisa do histórico completo; git falhando ou clone raso dão FAIL. Só um arquivo
ignorado pelo Git (o .tir) pode ser SKIP: ele é procurado pelo nome em python/ e
data/, e falta num clone novo.
Só lê importado-claude-ai/; nunca escreve nela.
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = "importado-claude-ai/saidas-conversas"
MANIFEST = RAIZ / "MANIFEST.sha256"

# SPEC §4.1: destino -> arquivos de origem (relativos a ORIGEM)
INVENTARIO = {
    "python": [
        "tire/tire_model_V2_4.py", "tire/test_tire_model_V2_4.py",
        "tire/test_tire_oracles_V2_4.py", "tire/mutation_tire_V2_4.py",
        "tire/build_workbook_V2_4.py", "tire/test_workbook_V2_4.py",
        "tire/layout_V2_4.json", "tire/Hoosier_R25B_13x7_TTC_provisional.meta.json",
        "kin/suspension_model_V2_1.py", "kin/test_suspension_model_V2_1.py",
        "kin/suspension_model_V1_0.py",  # dependência do TC-SUS-V2-004 (divergência 01)
        "kin/kinematics_model_V2_0.py", "kin/test_kinematics_model_V2_1.py",
        "kin/hardpoints_V2_0.py", "kin/test_hardpoints_V2_1.py",
        "kin/hardpoints_synthetic_V2.0.csv", "kin/hardpoints_synthetic_V2.0.meta.json",
        "tire/Hoosier_R25B_13x7_TTC_provisional.tir",  # fora do Git (D4)
    ],
    "excel": [
        "tire/FSAE_EV_Suspension_Fase1_V2_4.xlsx", "kin/FSAE_EV_Suspension_Fase1_V2.1.xlsx",
    ],
    "data": [
        "kin/kinematics_sweep_synthetic_V2.0.csv", "kin/placeholder-dependency-map-V2.1.csv",
        "tire/tire_comparison_grid_V2_3.csv",
    ],
    "docs": [
        "tire/Engineering_Decision_Register.md", "tire/data-contract-V2_4-excel-python.md",
        "kin/engineering-standard-V2.0-suspensao-fsae.md",
        "kin/arquitetura-consolidada-V2.0-suspensao-fsae.md", "kin/hardpoint-schema-V2.0.md",
        "kin/registro-de-versoes-V1.0.md", "kin/registro-de-versoes-V2.0.md",
        "tire/registro-de-versoes-V2_2.md", "tire/registro-de-versoes-V2_3.md",
        "tire/registro-de-versoes-V2_4.md",
    ],
}


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True)


def bytes_destino(destino: str) -> tuple[bytes | None, str]:
    """Conteúdo da cópia fiel de `destino`.

    Versionado: o blob do commit que adicionou o arquivo (edições posteriores, como a
    do docs/Engineering_Decision_Register.md pelo EDR-043, não contam). Precisa do
    histórico completo: em clone raso ou com o git falhando, levanta RuntimeError
    (vira FAIL, nunca SKIP). Fora do Git (ignorado, como o .tir): o arquivo achado
    pelo nome em python/ ou data/; se faltar, devolve None (SKIP).
    """
    raso = _git("rev-parse", "--is-shallow-repository")
    if raso.returncode != 0:
        raise RuntimeError(f"git indisponível: {raso.stderr.decode(errors='replace').strip()}")
    if raso.stdout.decode().strip() == "true":
        raise RuntimeError("clone raso: o commit que adicionou o arquivo pode faltar (use o histórico completo)")
    log = _git("log", "--diff-filter=A", "--format=%H", "--", destino)
    if log.returncode != 0:
        raise RuntimeError(f"git log falhou: {log.stderr.decode(errors='replace').strip()}")
    commits = log.stdout.decode().split()
    if commits:
        blob = _git("show", f"{commits[-1]}:{destino}")
        if blob.returncode != 0:
            raise RuntimeError(f"git show falhou: {blob.stderr.decode(errors='replace').strip()}")
        return blob.stdout, f"git {commits[-1][:7]}"
    if _git("check-ignore", "-q", "--no-index", destino).returncode != 0:
        raise RuntimeError("não está no Git e não é um arquivo ignorado (.gitignore)")
    for pasta in ("python", "data"):
        alt = RAIZ / pasta / Path(destino).name
        if alt.exists():
            return alt.read_bytes(), f"{pasta}/ (fora do Git)"
    return None, "ausente (fora do Git)"


def pares() -> list[tuple[str, str]]:
    out = []
    for destino, arquivos in INVENTARIO.items():
        for a in arquivos:
            out.append((f"{destino}/{Path(a).name}", f"{ORIGEM}/{a}"))
    nomes = [d for d, _ in out]
    assert len(nomes) == len(set(nomes)), "destinos duplicados no inventário"
    return out


def copiar() -> None:
    linhas = []
    for destino, origem in pares():
        d, o = RAIZ / destino, RAIZ / origem
        if d.exists():
            sys.exit(f"ERRO: {destino} já existe; não sobrescrevo.")
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(o, d)  # cópia byte a byte, sem metadados
        linhas.append(f"{sha256_arquivo(d)}  {destino}  {origem}")
    MANIFEST.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    print(f"copiados {len(linhas)} arquivos; MANIFEST.sha256 gravado")


def verificar() -> bool:
    ok, n_ok, n_skip = True, 0, 0
    linhas = MANIFEST.read_text(encoding="utf-8").splitlines()
    esperado = {d: o for d, o in pares()}
    registrados = {}
    for linha in linhas:
        h, destino, origem = linha.split("  ")
        registrados[destino] = origem
        o = RAIZ / origem
        if not o.exists():
            print(f"FAIL: origem ausente: {origem}")
            ok = False
            continue
        if sha256_arquivo(o) != h:
            print(f"FAIL: hash da origem difere: {origem}")
            ok = False
        try:
            conteudo, onde = bytes_destino(destino)
        except RuntimeError as e:
            print(f"FAIL: {destino}: {e}")
            ok = False
            continue
        if conteudo is None:
            print(f"SKIP: {destino}: {onde}")
            n_skip += 1
            continue
        if hashlib.sha256(conteudo).hexdigest() != h:
            print(f"FAIL: hash do destino difere: {destino} ({onde})")
            ok = False
        else:
            print(f"ok    {destino} ({onde})")
            n_ok += 1
    if registrados != esperado:
        print("FAIL: MANIFEST não corresponde ao inventário do SPEC §4.1")
        ok = False
    print(f"{n_ok} iguais, {n_skip} ausentes, de {len(linhas)} no manifesto")
    print("CA-02 PASS" if ok else "CA-02 FAIL")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--copiar", action="store_true")
    a = ap.parse_args()
    if a.copiar:
        copiar()
    sys.exit(0 if verificar() else 1)


if __name__ == "__main__":
    main()
