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
# Grupos 1 a 3 (TC-TIRE-011 a 013): A2, evaluate_interpolated
# ---------------------------------------------------------------------------------------------------------
import tire_model as tm
import tire_pressure as tp

VX = 11.176
PONTOS = [(fz, a, g, k) for fz in (300.0, 1054.0, 1500.0) for a in (-0.15, 0.0, 0.08) for g in (0.0, 0.03)
          for k in (-0.05, 0.0, 0.1)]


def interp(p, pt, **extra):
    fz, a, g, k = pt
    return tp.evaluate_interpolated(FAMILIA, p, fz_n=fz, alpha_rad=a, camber_rad=g, kappa=k, vx_mps=VX, **extra)


def estatico(p, pt):
    fz, a, g, k = pt
    return ts.evaluate_static(FAMILIA.at_pressure(p), fz_n=fz, alpha_rad=a, camber_rad=g, kappa=k, vx_mps=VX)


check("TC-TIRE-011a: nó exato (chaves reais) == evaluate_static, dataclass igual, sem tolerância",
      all(interp(p, pt) == estatico(p, pt) for p in P for pt in PONTOS))
check("TC-TIRE-011b: pedir 8, 10, 12 e 14 inteiros cai no nó exato (bit a bit) e 14.0 não é recusado",
      all(interp(float(q), pt) == estatico(float(q), pt) and type(interp(float(q), pt)) is ts.StaticTireResult
          for q in (8, 10, 12, 14) for pt in PONTOS))

ok_mix, ok_entre, ok_mu, ok_rot, ok_viz = True, True, True, True, True
ok_loo = {}
for q in (9.0, 11.0, 13.0, 12.5):
    lo, hi, w = tp.vizinhos(FAMILIA, q)
    for pt in PONTOS:
        r, rl, rh = interp(q, pt), estatico(lo, pt), estatico(hi, pt)
        for c in ("fx_n", "fy_n", "mx_nm", "my_nm", "mz_nm"):
            xl, xh, x = getattr(rl, c), getattr(rh, c), getattr(r, c)
            tol = 1e-9 * max(1.0, abs(xl), abs(xh))
            ok_mix &= abs(x - ((1 - w) * xl + w * xh)) <= tol
            ok_entre &= min(xl, xh) - tol <= x <= max(xl, xh) + tol
        ok_mu &= r.mu_effective <= (1 - w) * rl.mu_effective + w * rh.mu_effective + 1e-12
        ok_mu &= abs(r.mu_effective - tm.mu_effective(r.fx_n, r.fy_n, r.fz_n)) <= 1e-12
        ok_rot &= r.rotulo == "INTERPOLADO" and abs(sum(r.pesos) - 1.0) <= 1e-15 and r.pesos == (1 - w, w)
        ok_viz &= (r.vizinhos_psi == (lo, hi)
                   and r.sha256 == (FAMILIA.profiles[lo].base_sha256, FAMILIA.profiles[hi].base_sha256)
                   and r.pressure_psi == q)
    ok_loo[q] = sorted(interp(q, PONTOS[13]).loo_trecho)
check("TC-TIRE-012a: componentes = (1-w)·X_lo + w·X_hi (1e-9 relativo) em 9, 11, 13 e 12,5 psi", ok_mix)
check("TC-TIRE-012a: componentes entre o mínimo e o máximo dos vizinhos", ok_entre)
check("TC-TIRE-012b: mu_effective <= mistura dos mu dos vizinhos (+1e-12) e = mu_effective(Fx, Fy, Fz)", ok_mu)
check("TC-TIRE-012c: rotulo INTERPOLADO e pesos somam 1", ok_rot)
check("TC-TIRE-012c: vizinhos_psi e sha256 batem com os perfis vizinhos", ok_viz)


def chaves_aprox(ks, alvos):
    return len(ks) == len(alvos) and all(abs(k - a) <= ts.PRESSURE_TOLERANCE_PSI for k, a in zip(ks, alvos, strict=True))


check("TC-TIRE-012d: loo_trecho em 9 psi só tem o nó de 10", chaves_aprox(ok_loo[9.0], [10.0]), str(ok_loo[9.0]))
check("TC-TIRE-012d: loo_trecho em 11 psi tem os nós de 10 e 12", chaves_aprox(ok_loo[11.0], [10.0, 12.0]), str(ok_loo[11.0]))
check("TC-TIRE-012d: loo_trecho em 13 psi só tem o nó de 12", chaves_aprox(ok_loo[13.0], [12.0]), str(ok_loo[13.0]))
r_dg = interp(11.0, PONTOS[13])
check("TC-TIRE-012d: loo_trecho tem fx_n, fy_n e mz_n finitos; diagnostico=False o deixa vazio",
      all(set(v) == {"fx_n", "fy_n", "mz_n"} and all(math.isfinite(x) for x in v.values()) for v in r_dg.loo_trecho.values())
      and interp(11.0, PONTOS[13], diagnostico=False).loo_trecho == {})

PT0 = (1054.0, 0.05, 0.0, 0.0)
recusa("TC-TIRE-013a: 7,5 psi -> TireInterpolationError com [8, 14]", lambda: interp(7.5, PT0),
       tp.TireInterpolationError, "[8, 14]")
recusa("TC-TIRE-013a: 14,5 psi -> TireInterpolationError com [8, 14]", lambda: interp(14.5, PT0),
       tp.TireInterpolationError, "[8, 14]")
recusa("TC-TIRE-013b: 13 psi com Fz = 1530 N (fora do FZMAX do 12 psi) -> interseção",
       lambda: interp(13.0, (1530.0, 0.05, 0.0, 0.0)), tp.TireInterpolationError, "interseção")
rev12 = ts.revise_profile(FAMILIA.at_pressure(12.0), {"PDY1": FAMILIA.at_pressure(12.0).parameters["PDY1"] * 0.99},
                          reason="teste de revisões diferentes", revision_id="R-TESTE")
fam_rev = ts.StaticTireFamily(profiles={**{p: FAMILIA.profiles[p] for p in P}, P[2]: rev12})
recusa("TC-TIRE-013c: 12 psi revisado e 13 psi -> TireInterpolationError com revision_id",
       lambda: tp.evaluate_interpolated(fam_rev, 13.0, fz_n=1054.0, alpha_rad=0.05, camber_rad=0.0, kappa=0.0, vx_mps=VX),
       tp.TireInterpolationError, "revision_id")


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
