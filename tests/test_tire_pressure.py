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

# ---------------------------------------------------------------------------------------------------------
# Grupos 4 a 7 (TC-TIRE-014 a 017) e TC-TIRE-012e a 012g: métricas do pneu por pressão
# ---------------------------------------------------------------------------------------------------------
import time

_T_METRICAS = time.perf_counter()
PERFIS = [FAMILIA.profiles[p] for p in P]
FZS = (300.0, 700.0, 1054.0, 1500.0)

# TC-TIRE-014a/b: Cα e Cγ contra tire_model (mesmo passo 1e-6, mesma roda FR em ISO_TYDEX)
ok_ca, ok_cg, ok_caz = True, True, True
for pr in PERFIS:
    av, fx_ = tp.avaliador_perfil(pr), tp.faixa_do_perfil(pr)
    for fz in (300.0, 1054.0, 1500.0):
        for g in (0.0, 0.03):
            m = tp.metricas_pneu(av, fx_, fz_n=fz, camber_rad=g)
            ref = tm.rigidez_deriva(pr.dataset, fz, g)
            ok_ca &= abs(m.c_alpha_n_rad - ref) <= 1e-9 * abs(ref)
            ok_caz &= abs(m.c_alpha_por_fz_1_rad - ref / fz) <= 1e-9 * abs(ref / fz)
        m0 = tp.metricas_pneu(av, fx_, fz_n=fz, camber_rad=0.0)
        refg = tm.rigidez_camber(pr.dataset, fz)
        ok_cg &= abs(m0.c_gamma_n_rad - refg) <= 1e-9 * abs(refg)
check("TC-TIRE-014a: c_alpha_n_rad == tire_model.rigidez_deriva (1e-9 relativo), 4 perfis, Fz 300/1054/1500, γ 0 e 0,03", ok_ca)
check("TC-TIRE-014a: c_alpha_por_fz_1_rad == Cα/Fz", ok_caz)
check("TC-TIRE-014b: c_gamma_n_rad em γ = 0 == tire_model.rigidez_camber (1e-9 relativo)", ok_cg)


# TC-TIRE-015a/b: picos contra varredura fina independente (4001 pontos, sem refino)
def varredura(pr, fz, g, eixo, sinal):
    """(valor máximo, argumento) de |Fy|/Fz (eixo "a") ou |Fx|/Fz (eixo "k") em 4001 pontos, escrita aqui."""
    f = tp.faixa_do_perfil(pr)
    if eixo == "a":
        lim = f.alfa_max_rad if sinal > 0 else f.alfa_min_rad
    else:
        lim = f.kappa_max if sinal > 0 else f.kappa_min
    melhor = (-1.0, 0.0)
    for i in range(4001):
        x = lim * i / 4000.0
        if eixo == "a":
            r = ts.evaluate_static(pr, fz_n=fz, alpha_rad=x, camber_rad=g, kappa=0.0, vx_mps=VX)
            v = abs(r.fy_n) / fz
        else:
            r = ts.evaluate_static(pr, fz_n=fz, alpha_rad=0.0, camber_rad=g, kappa=x, vx_mps=VX)
            v = abs(r.fx_n) / fz
        if v > melhor[0]:
            melhor = (v, x)
    return melhor


ok_my, ok_mx, ok_ay, ok_kx = True, True, True, True
dif_my, dif_ay = [], []
for pr in PERFIS[:3]:  # 8, 10 e 12 psi
    av, fx_ = tp.avaliador_perfil(pr), tp.faixa_do_perfil(pr)
    for fz in (300.0, 1054.0, 1500.0):
        for sinal in (+1, -1):
            pk = tp.pico_mu_y(av, fx_, fz_n=fz, camber_rad=0.0, sinal=sinal)
            mu_ref, a_ref = varredura(pr, fz, 0.0, "a", sinal)
            ok_my &= abs(pk.mu - mu_ref) <= 1e-4 and not pk.borda
            ok_ay &= abs(pk.argumento - a_ref) <= fx_.alfa_max_rad / 4000.0 + 1e-6
            dif_my.append(abs(pk.mu - mu_ref))
            dif_ay.append(abs(pk.argumento - a_ref))
            pk = tp.pico_mu_x(av, fx_, fz_n=fz, camber_rad=0.0, sinal=sinal)
            mu_ref, k_ref = varredura(pr, fz, 0.0, "k", sinal)
            ok_mx &= abs(pk.mu - mu_ref) <= 1e-4 and not pk.borda
            ok_kx &= abs(pk.argumento - k_ref) <= fx_.kappa_max / 4000.0 + 1e-6
check("TC-TIRE-015a: μy pico (dois sentidos) contra varredura de 4001 pontos, |Δμ| <= 1e-4, 8/10/12 psi", ok_my,
      f"máx |Δμ| = {max(dif_my):.2e}")
check("TC-TIRE-015a: α do pico dentro de ALPMAX/4000 + 1e-6 da varredura", ok_ay, f"máx |Δα| = {max(dif_ay):.2e} rad")
check("TC-TIRE-015b: μx pico (tração e frenagem) contra varredura de 4001 pontos, |Δμ| <= 1e-4", ok_mx)
check("TC-TIRE-015b: κ do pico dentro de KPUMAX/4000 + 1e-6 da varredura", ok_kx)

# TC-TIRE-015c: penalidade de transferência
pr12 = FAMILIA.profiles[P[2]]
av12, fx12 = tp.avaliador_perfil(pr12), tp.faixa_do_perfil(pr12)
pen = tp.penalidade_transferencia(av12, fx12, fz0_n=1054.0, dfz_n=300.0, camber_rad=0.0)


def fy_max(sinal, fz):
    return tp.pico_mu_y(av12, fx12, fz_n=fz, camber_rad=0.0, sinal=sinal).mu * fz


ok_pen = set(pen) == {"alfa_pos", "alfa_neg"} and all(
    abs(pen[k] - (fy_max(s, 1354.0) + fy_max(s, 754.0) - 2.0 * fy_max(s, 1054.0))) <= 1e-9
    for k, s in (("alfa_pos", +1), ("alfa_neg", -1)))
check("TC-TIRE-015c: penalidade_transferencia == 3 chamadas a pico_mu_y (mesma definição), nos dois sentidos", ok_pen, str(pen))
check("TC-TIRE-015c: a penalidade é negativa (Fy_max côncavo em Fz)", pen["alfa_pos"] < 0.0 and pen["alfa_neg"] < 0.0)
recusa("TC-TIRE-015c: Fz0 + ΔFz > FZMAX -> ValueError",
       lambda: tp.penalidade_transferencia(av12, fx12, fz0_n=1400.0, dfz_n=300.0, camber_rad=0.0), ValueError, "Fz")
recusa("TC-TIRE-015c: Fz0 − ΔFz < FZMIN -> ValueError",
       lambda: tp.penalidade_transferencia(av12, fx12, fz0_n=300.0, dfz_n=300.0, camber_rad=0.0), ValueError, "Fz")

# TC-TIRE-015d: intervalo do pico interpolado
ok_int, ok_nos = True, True
for q in (9.0, 11.0, 13.0):
    for sinal in (+1, -1):
        inf, sup = tp.intervalo_pico_mu_y(FAMILIA, q, fz_n=1054.0, camber_rad=0.0, sinal=sinal)
        ok_int &= inf <= sup + 1e-12 and inf > 0.0
for q, pr in zip(P, PERFIS, strict=True):
    for sinal in (+1, -1):
        inf, sup = tp.intervalo_pico_mu_y(FAMILIA, q, fz_n=1054.0, camber_rad=0.0, sinal=sinal)
        pk = tp.pico_mu_y(tp.avaliador_perfil(pr), tp.faixa_do_perfil(pr), fz_n=1054.0, camber_rad=0.0, sinal=sinal)
        ok_nos &= inf == sup == pk.mu
check("TC-TIRE-015d: intervalo_pico_mu_y em 9, 11 e 13 psi (dois sentidos): inferior <= superior + 1e-12", ok_int)
check("TC-TIRE-015d: nos quatro nós exatos, inferior == superior == pico_mu_y do perfil", ok_nos)

# TC-TIRE-012e: aviso de pico
ROT_BORDA = "limitante inferior, sem pico interior"
PT_E = (1054.0, 0.05, 0.0, 0.0)
r13, r11 = interp(13.0, PT_E), interp(11.0, PT_E)
check("TC-TIRE-012e: 13 psi (12 tem pico interior, 14 não): avisos contém 'pico interior'",
      any("pico interior" in a for a in r13.avisos), str(r13.avisos))
check("TC-TIRE-012e: o aviso nomeia as pressões (12 e 14 psi)",
      any("12 psi" in a and "14 psi" in a for a in r13.avisos), str(r13.avisos))
check("TC-TIRE-012e: 11 psi (10 e 12 com pico interior): nenhum aviso de pico",
      not any("pico" in a for a in r11.avisos), str(r11.avisos))
check("TC-TIRE-012e: diagnostico=False não calcula o aviso", interp(13.0, PT_E, diagnostico=False).avisos == ())

# TC-TIRE-012f: valor e sinal do loo_trecho (recalculado no teste)
pt_f = (1054.0, -0.1, 0.0, 0.0)
r_f = interp(11.0, pt_f)
a8, a10, a12 = (estatico(P[i], pt_f) for i in (0, 1, 2))
w_f = (P[1] - P[0]) / (P[2] - P[0])
esp = {"fx_n": (1 - w_f) * a8.fx_n + w_f * a12.fx_n - a10.fx_n,
       "fy_n": (1 - w_f) * a8.fy_n + w_f * a12.fy_n - a10.fy_n,
       "mz_n": (1 - w_f) * a8.mz_nm + w_f * a12.mz_nm - a10.mz_nm}
no10 = next(v for k, v in r_f.loo_trecho.items() if abs(k - P[1]) <= ts.PRESSURE_TOLERANCE_PSI)
check("TC-TIRE-012f: valor e sinal do loo_trecho do nó de 10 psi (1e-9 relativo, recalculado no teste)",
      all(abs(no10[c] - esp[c]) <= 1e-9 * abs(esp[c]) for c in esp) and all(abs(esp[c]) > 1e-3 for c in esp),
      f"{no10} vs {esp}")

# TC-TIRE-012g: peso w independente
check("TC-TIRE-012g: w(9,0) = 0,5 e w(12,5) = 0,25 (1e-4)",
      abs(tp.vizinhos(FAMILIA, 9.0)[2] - 0.5) <= 1e-4 and abs(tp.vizinhos(FAMILIA, 12.5)[2] - 0.25) <= 1e-4,
      f"{tp.vizinhos(FAMILIA, 9.0)[2]}, {tp.vizinhos(FAMILIA, 12.5)[2]}")

# TC-TIRE-016: borda nos 14 psi
m14 = {fz: tp.metricas_pneu(tp.avaliador_perfil(PERFIS[3]), tp.faixa_do_perfil(PERFIS[3]), fz_n=fz, camber_rad=0.0)
       for fz in FZS}
check("TC-TIRE-016a: a 14 psi, Fz 300/700/1054/1500, γ 0: mu_y_pos.borda e mu_y_neg.borda True",
      all(m.mu_y_pos.borda and m.mu_y_neg.borda for m in m14.values()),
      str({fz: (m.mu_y_pos.borda, m.mu_y_neg.borda) for fz, m in m14.items()}))
check("TC-TIRE-016a: o rótulo 'limitante inferior, sem pico interior' está em rotulos",
      all(ROT_BORDA in m.rotulos for m in m14.values()))
bordas_outros = {}
for pr, q in zip(PERFIS[:3], P[:3], strict=True):
    for fz in FZS:
        m = tp.metricas_pneu(tp.avaliador_perfil(pr), tp.faixa_do_perfil(pr), fz_n=fz, camber_rad=0.0)
        bordas_outros[(round(q), fz)] = (m.mu_y_pos.borda, m.mu_y_neg.borda, m.mu_x_tracao.borda,
                                         m.mu_x_frenagem.borda, ROT_BORDA in m.rotulos)
check("TC-TIRE-016b: a 8, 10 e 12 psi, Fz 300/700/1054/1500: nenhuma borda em μy e μx, sem o rótulo",
      not any(any(v) for v in bordas_outros.values()), str({k: v for k, v in bordas_outros.items() if any(v)}))
check("TC-TIRE-016b: a 14 psi, μx sem borda",
      all(not m.mu_x_tracao.borda and not m.mu_x_frenagem.borda for m in m14.values()))

# TC-TIRE-017a: t0 contra diferença finita independente (passo 1e-4, evaluate_static direto)
ok_t0, ok_t0_rot = True, True
for pr in PERFIS:
    for fz in (300.0, 1054.0, 1500.0):
        h = 1e-4
        rp = ts.evaluate_static(pr, fz_n=fz, alpha_rad=h, camber_rad=0.0, kappa=0.0, vx_mps=VX)
        rm = ts.evaluate_static(pr, fz_n=fz, alpha_rad=-h, camber_rad=0.0, kappa=0.0, vx_mps=VX)
        t0_ref = -((rp.mz_nm - rm.mz_nm) / (2 * h)) / ((rp.fy_n - rm.fy_n) / (2 * h))
        m = tp.metricas_pneu(tp.avaliador_perfil(pr), tp.faixa_do_perfil(pr), fz_n=fz, camber_rad=0.0)
        ok_t0 &= abs(m.t0_m - t0_ref) <= 1e-6
        ok_t0_rot &= any("pendentes do item 3 do EDR-067" in r for r in m.rotulos)
check("TC-TIRE-017a: t0 = −(∂Mz/∂α)/(∂Fy/∂α) contra diferença finita independente (1e-6 m)", ok_t0)
check("TC-TIRE-017a: rótulo 'pendentes do item 3 do EDR-067' nas métricas", ok_t0_rot)

# TC-TIRE-017b: grade de Fz e teto
check("TC-TIRE-017b: teto_comum_fz == 1521 N", tp.teto_comum_fz(FAMILIA) == 1521.0)
g0 = tp.grade_fz(FAMILIA)
check("TC-TIRE-017b: grade_fz padrão tem 8 valores de 100 N a 1521 N, crescentes",
      len(g0) == 8 and g0[0][0] == 100.0 and g0[-1][0] == 1521.0 and all(a[0] < b[0] for a, b in zip(g0, g0[1:], strict=False)))
g1 = tp.grade_fz(FAMILIA, fz_operacao=[1600.0])
fz_acima = [x for x in g1 if any("acima do teto comum" in r for r in x[1])]
check("TC-TIRE-017b: grade_fz com fz_operacao = [1600] devolve 1521 com o rótulo de 'acima do teto'",
      len(g1) == 9 and len(fz_acima) == 1 and fz_acima[0][0] == 1521.0
      and "Fz de operação 1600 N acima do teto comum: avaliada em 1521 N" in fz_acima[0][1], str(g1[-1]))
g2 = tp.grade_fz(FAMILIA, fz_operacao=[1054.0])
check("TC-TIRE-017b: Fz de operação dentro do teto entra sem o rótulo de 'acima do teto'",
      len(g2) == 9 and g2[-1][0] == 1054.0 and not any("acima do teto" in r for r in g2[-1][1]))

# Rigidez vertical
kz, rot_kz = tp.rigidez_vertical(PERFIS[2])
check("TC-TIRE-017b: rigidez_vertical == VERTICAL_STIFFNESS do arquivo, com o rótulo de origem não verificada",
      kz == PERFIS[2].parameters["VERTICAL_STIFFNESS"] and rot_kz == "valor do arquivo, linear, origem não verificada")
print(f"tempo dos grupos 4 a 7: {time.perf_counter() - _T_METRICAS:.1f} s")

# ---------------------------------------------------------------------------------------------------------
# Grupo 8 (TC-TIRE-018): indicadores de incerteza e reprodução dos achados do conselho
# ---------------------------------------------------------------------------------------------------------
NOS = (7.999992, 10.000062, 11.999987, 14.000058)   # as chaves reais
lin = {p: 3.0 + 2.0 * p for p in NOS}
quad = {p: 0.5 * p * p for p in NOS}

loo_lin = tp.erro_loo(lin)
check("TC-TIRE-018a: erro_loo(lin) só tem os dois nós internos e |erro| <= 1e-12",
      set(loo_lin) == {NOS[1], NOS[2]} and all(abs(e.erro) <= 1e-12 for e in loo_lin.values()), str(loo_lin))

loo_quad = tp.erro_loo(quad)
dif_quad = []
for k in (1, 2):
    analitico = 0.5 * (NOS[k] - NOS[k - 1]) * (NOS[k + 1] - NOS[k])
    dif_quad.append(abs(loo_quad[NOS[k]].erro - analitico))
check("TC-TIRE-018b: erro_loo(quad)[p_k].erro == 0,5·(p_k − p_lo)·(p_hi − p_k) (1e-12)",
      max(dif_quad) <= 1e-12, str(dif_quad))
check("TC-TIRE-018b: erro_rel = erro/|real| e previsto − real = erro",
      all(abs(e.erro_rel - e.erro / abs(e.real)) <= 1e-15 and e.erro == e.previsto - e.real
          for e in loo_quad.values()))

loo_none = tp.erro_loo({NOS[0]: 1.0, NOS[1]: 2.0, NOS[2]: None, NOS[3]: 4.0})
check("TC-TIRE-018c: com o vizinho de 12 psi None, nenhum nó interno sobra (10 psi precisa do 12; 12 está None)",
      loo_none == {}, str(loo_none))
loo_none2 = tp.erro_loo({NOS[0]: 1.0, NOS[1]: 2.0, NOS[2]: 3.0, NOS[3]: None})
check("TC-TIRE-018c: com 14 psi None só o nó de 12 psi sai; o de 10 psi continua",
      set(loo_none2) == {NOS[1]}, str(set(loo_none2)))
check("TC-TIRE-018c: real = 0 dá erro_rel None",
      tp.erro_loo({NOS[0]: 1.0, NOS[1]: 0.0, NOS[2]: 1.0, NOS[3]: 2.0})[NOS[1]].erro_rel is None)

check("TC-TIRE-018d: monotonicidade(lin) == 'crescente'", tp.monotonicidade(lin) == "crescente")
check("TC-TIRE-018d: monotonicidade (3, 1, 2, 0) == 'não monotônica'",
      tp.monotonicidade(dict(zip(NOS, (3.0, 1.0, 2.0, 0.0), strict=True))) == "não monotônica")
check("TC-TIRE-018d: decrescente e constante",
      tp.monotonicidade(dict(zip(NOS, (4.0, 3.0, 2.0, 1.0), strict=True))) == "decrescente"
      and tp.monotonicidade(dict(zip(NOS, (2.0, 2.0, 2.0, 2.0), strict=True))) == "constante")
check("TC-TIRE-018d: ordena por pressão, não pela ordem de inserção",
      tp.monotonicidade({NOS[3]: 4.0, NOS[0]: 1.0, NOS[2]: 3.0, NOS[1]: 2.0}) == "crescente")

M1054 = {q: tp.metricas_pneu(tp.avaliador_perfil(pr), tp.faixa_do_perfil(pr), fz_n=1054.0, camber_rad=0.0)
         for q, pr in zip(P, PERFIS, strict=True)}
loo_mu_y = tp.erro_loo({q: m.mu_y_pos.mu for q, m in M1054.items()})
loo_ca = tp.erro_loo({q: m.c_alpha_n_rad for q, m in M1054.items()})
loo_mx_t = tp.erro_loo({q: m.mu_x_tracao.mu for q, m in M1054.items()})
loo_mx_f = tp.erro_loo({q: m.mu_x_frenagem.mu for q, m in M1054.items()})
e_mu_y, e_ca = loo_mu_y[P[1]].erro_rel, loo_ca[P[1]].erro_rel
e_mx_t, e_mx_f = loo_mx_t[P[2]].erro_rel, loo_mx_f[P[2]].erro_rel
print(f"018e: erro_rel μy(10 psi) {e_mu_y:+.5f}; Cα(10 psi) {e_ca:+.5f}; μx tração(12 psi) {e_mx_t:+.5f}; "
      f"μx frenagem(12 psi) {e_mx_f:+.5f}")
print("018e: Cα [N/rad] 8/10/12/14 psi: " + " / ".join(f"{m.c_alpha_n_rad:.1f}" for m in M1054.values()))
check("TC-TIRE-018e: erro_rel do μy (α > 0) a 10 psi em [−0,050, −0,044]", -0.050 <= e_mu_y <= -0.044, f"{e_mu_y:+.5f}")
check("TC-TIRE-018e: erro_rel do Cα a 10 psi em [−0,068, −0,061]", -0.068 <= e_ca <= -0.061, f"{e_ca:+.5f}")
check("TC-TIRE-018e: erro_rel do μx tração a 12 psi em [−0,099, −0,093]", -0.099 <= e_mx_t <= -0.093, f"{e_mx_t:+.5f}")
check("TC-TIRE-018e: erro_rel do μx frenagem a 12 psi em [−0,109, −0,102]", -0.109 <= e_mx_f <= -0.102, f"{e_mx_f:+.5f}")
check("TC-TIRE-018e: os quatro |erro_rel| em [0,04, 0,11] (o '4 a 11 %' do conselho)",
      all(0.04 <= abs(x) <= 0.11 for x in (e_mu_y, e_ca, e_mx_t, e_mx_f)))

pky2 = {q: pr.parameters["PKY2"] for q, pr in zip(P, PERFIS, strict=True)}
ca_1054 = {q: m.c_alpha_n_rad for q, m in M1054.items()}
check("TC-TIRE-018f: PKY2 cresce com a pressão", tp.monotonicidade(pky2) == "crescente", str(pky2))
check("TC-TIRE-018f: Cα em 1054 N não é monotônico (registro: 46,6k / 53,2k / 53,0k / 49,6k N/rad)",
      tp.monotonicidade(ca_1054) == "não monotônica", str(ca_1054))

a12 = tp.assimetria_alfa(M1054[P[2]])
check("TC-TIRE-018g: assimetria_alfa a 12 psi, 1054 N: dif_mu_pico >= 0 e fy_alpha0_n == metricas.fy_alpha0_n",
      a12.dif_mu_pico >= 0 and a12.fy_alpha0_n == M1054[P[2]].fy_alpha0_n, str(a12))
check("TC-TIRE-018g: dif_mu_pico = |μy+ − μy−|, dif_rel coerente e rótulo de origem física",
      abs(a12.dif_mu_pico - abs(M1054[P[2]].mu_y_pos.mu - M1054[P[2]].mu_y_neg.mu)) <= 1e-15
      and a12.rotulo == "em parte física: conicidade e ply-steer" and a12.dif_rel >= 0)

ok_ck, det_ck = True, []
for q, pr in zip(P, PERFIS, strict=True):
    h = 1e-4
    rp = ts.evaluate_static(pr, fz_n=1054.0, alpha_rad=0.0, camber_rad=0.0, kappa=+h, vx_mps=VX)
    rm = ts.evaluate_static(pr, fz_n=1054.0, alpha_rad=0.0, camber_rad=0.0, kappa=-h, vx_mps=VX)
    ref = (rp.fx_n - rm.fx_n) / (2 * h)
    ck = M1054[q].c_kappa_n
    ok_ck &= ck > 0 and abs(ck - ref) <= 1e-3 * abs(ref)
    det_ck.append((round(q), ck, ref))
check("TC-TIRE-018h: sinal e valor de Cκ (> 0 e igual à diferença central independente, tol. rel. 1e-3)",
      ok_ck, str(det_ck))


encerrar()
