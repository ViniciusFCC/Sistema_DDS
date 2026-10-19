"""CA-02: copia o inventário do SPEC §4.1 (opcional) e verifica o MANIFEST.sha256.

Uso:
    uv run python -X utf8 tools/verificar_manifest.py --copiar   (só no commit 0)
    uv run python -X utf8 tools/verificar_manifest.py

Formato do MANIFEST.sha256 (uma linha por arquivo, separador de dois espaços):
    <sha256>  <destino relativo à raiz>  <origem relativa à raiz>
Verificação: o hash do destino e o da origem batem com o registrado. O .tir está
no manifesto mesmo fora do Git; se ele faltar (clone novo), a linha é SKIP.
Só lê importado-claude-ai/; nunca escreve nela.
"""
import argparse
import hashlib
import shutil
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
        d = RAIZ / destino
        if not o.exists():
            print(f"FAIL: origem ausente: {origem}")
            ok = False
            continue
        if sha256_arquivo(o) != h:
            print(f"FAIL: hash da origem difere: {origem}")
            ok = False
        if not d.exists():
            print(f"SKIP: destino ausente (fora do Git?): {destino}")
            n_skip += 1
            continue
        if sha256_arquivo(d) != h:
            print(f"FAIL: hash do destino difere: {destino}")
            ok = False
        else:
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
