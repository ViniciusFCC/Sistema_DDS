"""
Testes do subprojeto A (pneu com variação de pressão): grupos 1 a 13 da §10 da spec
docs/superpowers/specs/2026-11-02-pneu-estado-design.md, IDs TC-TIRE-011 a TC-TIRE-023 (EDR-071).

Os .tir ficam FORA do Git (references/ttc/round6_hoosier_r25b_20p5x7_13_7in/, ou o diretório da variável de
ambiente DDS_TTC_DIR). Sem eles o script diz NÃO EXECUTÁVEL e sai com código 3: isso nunca conta como aprovado.

"Passou" = concordância com a definição, não validação física (Validation = NOT_VALIDATED).

Uso: uv run python -X utf8 tests/test_tire_pressure.py
"""
import json
import math
import os
import tempfile
from pathlib import Path

import tire_model_static as ts

HERE = Path(__file__).resolve().parent
DEG = math.pi / 180.0
SUBDIR = Path("references") / "ttc" / "round6_hoosier_r25b_20p5x7_13_7in"
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL"))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def recusa(nome, fn, tipo, trecho):
    """Passa se fn() levanta `tipo` com `trecho` na mensagem."""
    try:
        fn()
        check(nome, False, "não lançou")
    except tipo as exc:
        check(nome, trecho in str(exc), str(exc))


def tem_quatro_tir(c):
    return c.is_dir() and len(list(c.glob("*PAC02_UM4.tir"))) >= 4


def achar_diretorio_ttc():
    """DDS_TTC_DIR (se definido, só ele: inválido = NÃO EXECUTÁVEL, sem cair para outra pasta), a raiz deste
    checkout ou a raiz do repositório principal (worktrees ficam em .claude/worktrees/x)."""
    env = os.environ.get("DDS_TTC_DIR")
    if env:
        if tem_quatro_tir(Path(env)):
            return Path(env)
        print(f"NÃO EXECUTÁVEL: DDS_TTC_DIR={env} não é uma pasta com os quatro .tir *PAC02_UM4.tir do TTC "
              "Round 6; nenhuma outra pasta foi tentada. Não conta como aprovado.")
        raise SystemExit(3)
    raiz = HERE.parent
    candidatos = [raiz / SUBDIR]
    if len(raiz.parents) >= 3 and raiz.parent.name == "worktrees":
        candidatos.append(raiz.parents[2] / SUBDIR)
    for c in candidatos:
        if tem_quatro_tir(c):
            return c
    return None


TTC = achar_diretorio_ttc()
if TTC is None:
    print("NÃO EXECUTÁVEL: .tir do TTC Round 6 não encontrados (defina DDS_TTC_DIR ou coloque em "
          f"{SUBDIR}). Não conta como aprovado.")
    raise SystemExit(3)

FAMILIA = ts.load_profile_family(TTC, source_axis_system="ISO_TYDEX")
P = FAMILIA.pressures_psi


def encerrar():
    print("\n--- Resumo ---")
    n = sum(1 for _, s in results if s == "PASS")
    f = len(results) - n
    print(f"{n} PASS, {f} FAIL, de {len(results)} testes")
    if f:
        raise SystemExit(1)


# ---------------------------------------------------------------------------------------------------------
# Grupo 13 (TC-TIRE-023): guarda QPZ1-2/QPX1, mensagem do at_pressure, versão 4.2.0 e overlays da 4.1.0
# ---------------------------------------------------------------------------------------------------------
P12 = FAMILIA.at_pressure(12.0)
with tempfile.TemporaryDirectory() as tmp:
    tmpd = Path(tmp)
    linhas_12 = P12.source_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    for letra, chave in (("a", "QPZ1"), ("b", "QPZ2"), ("c", "QPX1")):
        # cópia do .tir de 12 psi com a linha da chave trocada para "= 0.1" (o original nunca é editado)
        novas = [("%-25s=  0.1\n" % chave) if ln.lstrip().startswith(chave + " ") or ln.lstrip().startswith(chave + "=")
                 else ln for ln in linhas_12]
        check(f"TC-TIRE-023{letra}: a cópia de teste mudou exatamente a linha de {chave}",
              sum(1 for a, b in zip(linhas_12, novas, strict=True) if a != b) == 1)
        copia = tmpd / f"{chave}_{P12.source_path.name}"
        copia.write_text("".join(novas), encoding="utf-8")
        recusa(f"TC-TIRE-023{letra}: load_profile recusa {chave} != 0",
               lambda copia=copia: ts.load_profile(copia, source_axis_system="ISO_TYDEX"),
               ts.StaticTireError, chave)

    # TC-TIRE-023d: o original segue carregando e QPZ1 = QPZ2 = QPX1 = 0 nos quatro perfis
    check("TC-TIRE-023d: QPZ1 = QPZ2 = QPX1 = 0 nos quatro perfis do original",
          len(P) == 4 and all(FAMILIA.profiles[p].dataset.p.get(k, 0.0) == 0.0
                              for p in P for k in ("QPZ1", "QPZ2", "QPX1")))

    # TC-TIRE-023e: mensagem nova do at_pressure
    try:
        FAMILIA.at_pressure(13.0)
        check("TC-TIRE-023e: at_pressure(13.0) levanta StaticTireError", False, "não lançou")
    except ts.StaticTireError as exc:
        msg = str(exc)
        check("TC-TIRE-023e: at_pressure(13.0) aponta a rota rotulada (Interpolação e tire_pressure.evaluate_interpolated)",
              "Interpolação" in msg and "tire_pressure.evaluate_interpolated" in msg, msg)

    # TC-TIRE-023f: overlay salvo pela 4.2.0 com model_version "4.1.0-static" é aceito e reproduz o original
    rev = ts.revise_profile(P12, {"PDY1": P12.dataset.p["PDY1"] * 1.05}, reason="overlay da 4.1.0", revision_id="T-023F")
    arq = tmpd / "rev.json"
    ts.save_revision(rev, arq)
    payload = json.loads(arq.read_text(encoding="utf-8"))
    arq41 = tmpd / "rev41.json"
    arq41.write_text(json.dumps({**payload, "model_version": "4.1.0-static"}), encoding="utf-8")
    try:
        de_41 = ts.load_revision(P12, arq41)
        pt = dict(fz_n=1054.0, alpha_rad=4.0 * DEG, camber_rad=-2.0 * DEG, kappa=0.05, vx_mps=11.0)
        r_orig, r_41 = ts.evaluate_static(rev, **pt), ts.evaluate_static(de_41, **pt)
        check("TC-TIRE-023f: overlay com model_version 4.1.0-static é aceito e dá o mesmo evaluate_static (bit a bit)",
              (r_orig.fx_n, r_orig.fy_n, r_orig.mx_nm, r_orig.my_nm, r_orig.mz_nm)
              == (r_41.fx_n, r_41.fy_n, r_41.mx_nm, r_41.my_nm, r_41.mz_nm))
    except ts.StaticTireError as exc:
        check("TC-TIRE-023f: overlay com model_version 4.1.0-static é aceito", False, str(exc))
    # o overlay da 4.0.1 segue recusado
    arq40 = tmpd / "rev40.json"
    arq40.write_text(json.dumps({**payload, "model_version": "4.0.1-static"}), encoding="utf-8")
    recusa("TC-TIRE-023f: overlay com model_version 4.0.1-static segue recusado",
           lambda: ts.load_revision(P12, arq40), ts.StaticTireError, "outra versão")

check("TC-TIRE-023g: versão do módulo", ts.__version__ == "4.2.0-static")


encerrar()
