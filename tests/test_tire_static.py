"""
Testes do modelo estático de pneu PAC2002 (python/tire_model_static.py), sobre os .tir do TTC Round 6
(Hoosier R25B 20.5x7-13 em aro de 7 in; 8, 10, 12 e 14 psi; eixo ISO_TYDEX).

Os .tir ficam FORA do Git (references/ttc/round6_hoosier_r25b_20p5x7_13_7in/, ou o diretório da variável de
ambiente DDS_TTC_DIR). Sem eles o script diz NÃO EXECUTÁVEL e sai com código 3: isso nunca conta como aprovado.

Mx e Mz são conferidos contra transcrições independentes, escritas aqui, das equações do help do Adams
(MSC Adams Tire, PAC2002: Mx eq. 109, p. 48; Mz eqs. 100-108, p. 47). "Passou" = concordância com a transcrição
da equação, não validação contra medição (Validation = NOT_VALIDATED).

Uso: uv run python -X utf8 tests/test_tire_static.py
"""
import hashlib
import math
import os
import sys
import tempfile
from pathlib import Path

import tire_model as base
import tire_model_static as ts

HERE = Path(__file__).resolve().parent
DEG = math.pi / 180.0
SUBDIR = Path("references") / "ttc" / "round6_hoosier_r25b_20p5x7_13_7in"
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL"))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def achar_diretorio_ttc():
    """DDS_TTC_DIR, a raiz deste checkout ou a raiz do repositório principal (worktrees ficam em .claude/worktrees/x)."""
    candidatos = []
    env = os.environ.get("DDS_TTC_DIR")
    if env:
        candidatos.append(Path(env))
    raiz = HERE.parent
    candidatos.append(raiz / SUBDIR)
    if len(raiz.parents) >= 3 and raiz.parent.name == "worktrees":
        candidatos.append(raiz.parents[2] / SUBDIR)
    for c in candidatos:
        if c.is_dir() and any(c.glob("*PAC02_UM4.tir")):
            return c
    return None


TTC = achar_diretorio_ttc()
if TTC is None:
    print("NÃO EXECUTÁVEL: .tir do TTC Round 6 não encontrados (defina DDS_TTC_DIR ou coloque em "
          f"{SUBDIR}). Não conta como aprovado.")
    raise SystemExit(3)

FAMILIA = ts.load_profile_family(TTC, source_axis_system="ISO_TYDEX")
P12 = FAMILIA.at_pressure(12.0)


class Par(dict):
    """Parâmetros do .tir; ausente = default do help (fator L* = 1, demais coeficientes = 0)."""

    def __missing__(self, chave):
        return 1.0 if chave.startswith("L") else 0.0


# ---------------------------------------------------------------------------------------------------------
# Transcrições independentes (não reutilizam _mx nem _mz do módulo)
# ---------------------------------------------------------------------------------------------------------
def mx_eq109(P, fz, fy, gam):
    """Help do Adams, eq. 109 (p. 48), com dpi = 0 (perfil em IP = IP_NOM):
    Mx = R0 Fz { QSX3 Fy/F'z0 + QSX4 cos[QSX5 atan((QSX6 Fz/F'z0)^2)] sin[QSX7 gam + QSX8 atan(QSX9 Fy/F'z0)]
                 + [QSX10 atan(QSX11 Fz/F'z0) - QSX2 (1 + QPX1 dpi)] gam + QSX1 LVMX } LMX"""
    fz0 = P["LFZO"] * P["FNOMIN"]
    R0 = P["UNLOADED_RADIUS"]
    chave = (P["QSX3"] * fy / fz0
             + P["QSX4"] * math.cos(P["QSX5"] * math.atan((P["QSX6"] * fz / fz0) ** 2))
             * math.sin(P["QSX7"] * gam + P["QSX8"] * math.atan(P["QSX9"] * fy / fz0))
             + (P["QSX10"] * math.atan(P["QSX11"] * fz / fz0) - P["QSX2"]) * gam
             + P["QSX1"] * P["LVMX"])
    return R0 * fz * chave * P["LMX"]


def mz_eq100(P, fz, alpha, gam, kappa, fx, fy, info):
    """Help do Adams, eqs. 100-108 (p. 47). Devolve (termo de trilha, resíduo, s*Fx) separados, para isolar o
    termo de Fx. O Fy do termo de trilha é o Fy com a cambagem real, F'y = Fy - SVyk (Pacejka 4.E71)."""
    fz0 = P["LFZO"] * P["FNOMIN"]
    R0 = P["UNLOADED_RADIUS"]
    dfz = (fz - fz0) / fz0
    gz = gam * P["LGAZ"]
    Kx, Ky = info["Kx"], info["Ky"]
    # eq. 45-46: ângulos de trilha e de resíduo (com deslocamentos)
    a_t = alpha + P["QHZ1"] + P["QHZ2"] * dfz + (P["QHZ3"] + P["QHZ4"] * dfz) * gz
    a_r = alpha + info["SHy"] + info["SVy"] / Ky

    def a_eq(a):                                                                     # eqs. 106 e 107
        return math.atan(math.sqrt(math.tan(a) ** 2 + (Kx / Ky) ** 2 * kappa ** 2) * (1 if a > 0 else -1 if a < 0 else 0))

    Bt = (P["QBZ1"] + P["QBZ2"] * dfz + P["QBZ3"] * dfz ** 2) * (1 + P["QBZ4"] * gz + P["QBZ5"] * abs(gz)) * P["LKY"] / P["LMUY"]
    Ct = P["QCZ1"]
    Dt = fz * (P["QDZ1"] + P["QDZ2"] * dfz) * (1 + P["QDZ3"] * gz + P["QDZ4"] * gz ** 2) * (R0 / fz0) * P["LTR"]
    Et = (P["QEZ1"] + P["QEZ2"] * dfz + P["QEZ3"] * dfz ** 2) * (1 + (P["QEZ4"] + P["QEZ5"] * gz) * (2 / math.pi) * math.atan(Bt * Ct * a_t))
    Et = min(Et, 1.0)
    at = a_eq(a_t)
    t = Dt * math.cos(Ct * math.atan(Bt * at - Et * (Bt * at - math.atan(Bt * at)))) * math.cos(alpha)      # eq. 102
    Br = P["QBZ9"] * P["LKY"] / P["LMUY"] + P["QBZ10"] * info["By"] * info["Cy"]
    Dr = fz * R0 * P["LMUGAMMA"] * P["LRES"] * (P["QDZ6"] + P["QDZ7"] * dfz + (P["QDZ8"] + P["QDZ9"] * dfz) * gz)
    Mzr = Dr * math.cos(math.atan(Br * a_eq(a_r))) * math.cos(alpha)                                     # eq. 104
    s = (P["SSZ1"] + P["SSZ2"] * fy / fz0 + (P["SSZ3"] + P["SSZ4"] * dfz) * gam) * R0 * P["LS"]         # eq. 108
    Fy_linha = fy - info["SVyk"]                                                                       # eq. 103
    return -t * Fy_linha, Mzr, s * fx


def operar(profile, fz, alpha_deg, gam_deg, kappa, vx=10.0):
    return ts.evaluate_static(profile, fz_n=fz, alpha_rad=alpha_deg * DEG, camber_rad=gam_deg * DEG,
                              kappa=kappa, vx_mps=vx)


def forcas(profile, fz, alpha_deg, gam_deg, kappa):
    return base.combined_forces(profile.dataset, fz, alpha_deg * DEG, gam_deg * DEG, kappa)


# ---------------------------------------------------------------------------------------------------------
# Mx (eq. 109)
# ---------------------------------------------------------------------------------------------------------
P = Par(P12.dataset.p)
pontos = [(fz, a, g, k) for fz in (500.0, 1054.0, 1500.0) for a in (0.0, 4.0, 8.0)
          for g in (0.0, -2.0, -3.0) for k in (0.0, 0.08, -0.10)]
worst_mx = 0.0
for fz, a, g, k in pontos:
    r = operar(P12, fz, a, g, k)
    ref = mx_eq109(P, fz, r.fy_n, g * DEG)
    worst_mx = max(worst_mx, abs(r.mx_nm - ref))
check("estático /Mx-1: Mx do módulo == transcrição independente da eq. 109 em 81 pontos (12 psi); tol. 1e-9 N.m",
      worst_mx < 1e-9, f"dif máx={worst_mx:.2e} N.m")

for (fz, a, g, k), esperado in (((1054.0, 4.0, 0.0, 0.0), -38.6), ((1054.0, 0.0, 0.0, 0.0), -1.2),
                                ((1500.0, 8.0, 0.0, 0.0), -83.0)):
    mx = operar(P12, fz, a, g, k).mx_nm
    check(f"estático /Mx-2: valor de referência da transcrição, Fz={fz:g} N, alpha={a:g}, gamma={g:g} -> {esperado} N.m (tol. 0,1)",
          abs(mx - esperado) < 0.1, f"Mx={mx:.3f}")

# o termo QSX10 so atua com camber (multiplica gamma) e o QSX6 entra ao quadrado: sensibilidade da correção
r0 = operar(P12, 1054.0, 0.0, 0.0, 0.0)
rg = operar(P12, 1054.0, 0.0, -3.0, 0.0)
rev = ts.revise_profile(P12, {"QSX10": P["QSX10"] + 0.01}, reason="teste de sensibilidade", revision_id="T-QSX10")
d0 = operar(rev, 1054.0, 0.0, 0.0, 0.0).mx_nm - r0.mx_nm
dg = operar(rev, 1054.0, 0.0, -3.0, 0.0).mx_nm - rg.mx_nm
check("estático /Mx-3: QSX10 multiplica gamma (sem camber, mudar QSX10 não altera Mx; com camber altera)",
      abs(d0) < 1e-12 and abs(dg) > 1e-3, f"dMx(gamma=0)={d0:.2e}; dMx(gamma=-3)={dg:.4f}")

# ---------------------------------------------------------------------------------------------------------
# Mz (eqs. 100-108): sinal do termo s*Fx
# ---------------------------------------------------------------------------------------------------------
worst_mz = 0.0
worst_sfx = 0.0
for fz, a, g, k in pontos:
    fx, fy, info = forcas(P12, fz, a, g, k)
    trilha, mzr, sfx = mz_eq100(P, fz, a * DEG, g * DEG, k, fx, fy, info)
    r = operar(P12, fz, a, g, k)
    worst_mz = max(worst_mz, abs(r.mz_nm - (trilha + mzr + sfx)))
check("estático /Mz-1: Mz do módulo == -t F'y + Mzr + s Fx da transcrição independente em 81 pontos; tol. 1e-9 N.m",
      worst_mz < 1e-9, f"dif máx={worst_mz:.2e} N.m")

# Isola s*Fx sem depender da transcrição de s: zera SSZ1..SSZ4 por revisão (s = 0) e compara
zerado = ts.revise_profile(P12, {"SSZ1": 0.0, "SSZ2": 0.0, "SSZ3": 0.0, "SSZ4": 0.0}, reason="s = 0 para isolar s*Fx",
                           revision_id="T-S0")
for fz, a, g, k in ((1054.0, 4.0, 0.0, 0.08), (1054.0, 4.0, -2.0, -0.10), (1500.0, 8.0, -3.0, 0.08)):
    fx, fy, info = forcas(P12, fz, a, g, k)
    s = (P["SSZ1"] + P["SSZ2"] * fy / (P["LFZO"] * P["FNOMIN"])
         + (P["SSZ3"] + P["SSZ4"] * (fz - P["LFZO"] * P["FNOMIN"]) / (P["LFZO"] * P["FNOMIN"])) * g * DEG) * P["UNLOADED_RADIUS"] * P["LS"]
    dif = operar(P12, fz, a, g, k).mz_nm - operar(zerado, fz, a, g, k).mz_nm
    check(f"estático /Mz-2: Mz - Mz(s=0) == +s*Fx (sinal positivo), Fz={fz:g}, alpha={a:g}, gamma={g:g}, kappa={k:g}",
          abs(dif - s * fx) < 1e-9 and abs(dif) > 0.1, f"dif={dif:.4f} N.m; s*Fx={s * fx:.4f} N.m")

for (fz, a, g, k), esperado in (((1054.0, 4.0, 0.0, 0.08), 7.5), ((1054.0, 4.0, -2.0, -0.10), 46.9)):
    mz = operar(P12, fz, a, g, k).mz_nm
    check(f"estático /Mz-3: valor de referência (só a correção do sinal), Fz={fz:g}, alpha={a:g}, gamma={g:g}, kappa={k:g} -> {esperado} N.m (tol. 0,1)",
          abs(mz - esperado) < 0.1, f"Mz={mz:.3f}")


# ---------------------------------------------------------------------------------------------------------
def encerrar():
    print("\n--- Resumo ---")
    n = sum(1 for _, s in results if s == "PASS")
    f = len(results) - n
    print(f"{n} PASS, {f} FAIL, de {len(results)} testes")
    if f:
        raise SystemExit(1)


encerrar()
