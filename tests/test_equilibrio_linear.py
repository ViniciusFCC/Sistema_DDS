"""
Testes do equilíbrio linear (V4.0, incremento 2).
TC-EQ-021..023: rigidez de deriva e de camber do PAC2002. TC-EQ-024..030: oráculos do Gillespie cap. 6 (IDs autorizados pelo usuário).
Roda como script: uv run python -X utf8 tests/test_equilibrio_linear.py
O dataset sem deslocamentos (ds0) é só de teste; não representa o pneu do carro.
"""

import dataclasses
import math
import os

import tire_model as tm

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
FZ0 = ds.p["FNOMIN"]

# ---------------- TC-EQ-021 : C_alpha = |Ky| sem deslocamentos ----------------
# Cópia só de teste: zera todos os PHY*, PVY* e RHY* (deslocamentos), sem tocar em ds.p.
p0 = {k: (0.0 if k.startswith(("PHY", "PVY", "RHY")) else v) for k, v in ds.p.items()}
ds0 = dataclasses.replace(ds, p=p0)
c_ref = abs(tm.pure_fy0(ds0.p, FZ0, 0.0, 0.0)[1]["Ky"])
c_num = tm.rigidez_deriva(ds0, FZ0)
err_021 = abs(c_num - c_ref) / c_ref
c_real = tm.rigidez_deriva(ds, FZ0)
check("TC-EQ-021: rigidez_deriva = |Ky| do PAC2002 sem deslocamentos (erro rel. < 1e-6); com o ds real, > 0",
      err_021 < 1e-6 and c_real > 0,
      f"C_alpha(ds0)={c_num:.3f} Ky={c_ref:.3f} err={err_021:.2e}; C_alpha(ds)={c_real:.3f} N/rad")

# ---------------- TC-EQ-022 : C_gamma por diferença central com outro passo ----------------
c_g = tm.rigidez_camber(ds, FZ0)
h2 = 1e-5
fy_p = tm.wheel_forces(ds, "FR", FZ0, 0.0, +h2, 0.0)[1]
fy_m = tm.wheel_forces(ds, "FR", FZ0, 0.0, -h2, 0.0)[1]
c_g2 = -(fy_p - fy_m) / (2 * h2)
err_022 = abs(c_g - c_g2) / abs(c_g2)
check("TC-EQ-022: rigidez_camber > 0 e igual à diferença central com passo 1e-5 (erro rel. < 1e-4)",
      c_g > 0 and err_022 < 1e-4,
      f"C_gamma={c_g:.3f} N/rad (passo 1e-5: {c_g2:.3f}) err={err_022:.2e}")

# ---------------- TC-EQ-023 : sensibilidade à carga (Gillespie p. 215) ----------------
c_meio = tm.rigidez_deriva(ds, 0.5 * FZ0)
c_nom = tm.rigidez_deriva(ds, FZ0)
cresce = c_nom > c_meio
razao_cai = (c_nom / FZ0) < (c_meio / (0.5 * FZ0))
check("TC-EQ-023: C_alpha cresce de 0,5*FNOMIN para FNOMIN e C_alpha/Fz cai (Gillespie p. 215; conferido no .tir atual)",
      cresce and razao_cai,
      f"C(0,5Fn)={c_meio:.1f} C(Fn)={c_nom:.1f} N/rad; C/Fz: {c_meio/(0.5*FZ0):.3f} -> {c_nom/FZ0:.3f} rad^-1")

# ---------------- Oráculos do Gillespie cap. 6 (exemplos resolvidos, pp. 231-235) ----------------
# Valores do livro em lb, in, ft e lb/deg; a conversão para SI é feita aqui, no teste.
import equilibrio_linear as el
import kinematics_model as km
from suspension_model import G

LB = 4.4482216
IN = 0.0254
FT = 0.3048
LBDEG = LB * 57.29578  # lb/deg -> N/rad

# TC-EQ-024: exemplo 1 (eq. 6-15), com C de eixo = 2 x C por pneu. O livro usa 950 e 776 lb por pneu (arredondados) e
# imprime K = 0,11 deg/g arredondando cada termo (4,09 - 3,98); a conta exata dá 0,1153.
K1 = el.gradiente_pneus(2 * 950 * LB, 2 * 776 * LB, 2 * 232 * LBDEG, 2 * 195 * LBDEG)
K1_dpg = el.para_graus_por_g(K1)
K1_exato = el.para_graus_por_g(el.gradiente_pneus(1901 * LB, 1552 * LB, 2 * 232 * LBDEG, 2 * 195 * LBDEG))
# Termos separados (W_r = 0 ou W_f = 0 zera o outro termo); o livro arredonda cada um antes de subtrair.
t_f = el.para_graus_por_g(el.gradiente_pneus(2 * 950 * LB, 0.0, 2 * 232 * LBDEG, 1.0))
t_r = -el.para_graus_por_g(el.gradiente_pneus(0.0, 2 * 776 * LB, 1.0, 2 * 195 * LBDEG))
K1_impresso = round(t_f, 2) - round(t_r, 2)
check("TC-EQ-024: exemplo 1 do Gillespie (p. 232), K = 950/232 - 776/195 = 0,1153 +- 0,0005 deg/g; termos arredondados (4,09 - 3,98) dão o 0,11 impresso",
      abs(K1_dpg - 0.1153) < 0.0005 and abs(K1_impresso - 0.11) < 1e-9,
      f"K={K1_dpg:.4f} deg/g com 950 e 776 lb por pneu; termos {t_f:.2f} - {t_r:.2f} = {K1_impresso:.2f} (livro imprime 0,11); "
      f"com os pesos exatos 1901/2 e 1552/2: {K1_exato:.4f} deg/g")

# TC-EQ-025: velocidade característica (eq. 6-18) e errata da p. 232
K_book = 0.11 * math.pi / 180 / G  # 0,11 deg/g em rad/(m/s^2)
v_impressa = el.velocidade_caracteristica(110.6 * IN, K_book) / FT
v_problema = el.velocidade_caracteristica(100.6 * IN, K_book) / FT
check("TC-EQ-025: V_char = 393 ft/s com L = 110,6 in (conta impressa) e 375 ft/s com L = 100,6 in, +- 1",
      abs(v_impressa - 393) < 1 and abs(v_problema - 375) < 1,
      f"errata do Gillespie p. 232: V_char usa 110,6 in; o problema dá 100,6 in. "
      f"L=110,6 in: {v_impressa:.1f} ft/s; L=100,6 in: {v_problema:.1f} ft/s")

# TC-EQ-026: ponto neutro (p. 233)
c_neutro_ft = el.ponto_neutro_ate_traseiro(8.38 * FT, 232, 195) / FT
check("TC-EQ-026: ponto neutro a 4,55 ft do eixo traseiro (c' = L C_f/(C_f+C_r), p. 233) +- 0,01",
      abs(c_neutro_ft - 4.55) < 0.01,
      f"c'={c_neutro_ft:.3f} ft; livro 4,55")

# TC-EQ-027: exemplo 2, gradiente de rolagem (eq. 6-32), K_phi em in.lb/deg -> N.m/rad
KPHI = LB * IN * 57.29578
dphi = el.para_graus_por_g(el.gradiente_rolagem(2750 * LB, 10 * IN, 1500 * KPHI, 1606 * KPHI))
check("TC-EQ-027: exemplo 2 (p. 234), dphi/da_y = W h1/(K_phi_f + K_phi_r - W h1) = 10,5 deg/g +- 0,05",
      abs(dphi - 10.5) < 0.05,
      f"dphi/da_y={dphi:.3f} deg/g; livro 10,5")

# TC-EQ-028: parcela de camber (eq. 6-56), Cg/Ca = 0,1, dgamma/dphi = 1 na frente
k_cam = el.parcela_camber(0.1, 1.0, 1.0, 0.1, 1.0, 0.0, 10.5)
check("TC-EQ-028: K_camber = (0,1 x 1,0 - 0,1 x 0) x 10,5 = 1,05 deg/g +- 0,005 (p. 234)",
      abs(k_cam - 1.05) < 0.005, f"K_camber={k_cam:.4f} deg/g; livro 1,05")

# TC-EQ-029: roll steer traseiro (eq. 6-57), eps_r = +0,122 rad/rad (SAE)
k_rs = km.roll_steer_understeer_deg_per_g(0.0, 0.122, 10.5)
check("TC-EQ-029: roll steer = (eps_f - eps_r) dphi/da_y = -1,281 +- 0,001 deg/g (SUS-415)",
      abs(k_rs - (-1.281)) < 0.001,
      f"K_rs={k_rs:.4f} deg/g; o livro imprime 1,28 e diz sobresterço (p. 235), coerente com o sinal negativo")

# TC-EQ-030: velocidade crítica vs característica
L_t, K_t = 2.5, 0.0021
check("TC-EQ-030: V_crit(L, -|K|) = V_char(L, |K|); V_char(L, -|K|) e V_crit(L, +|K|) = None",
      math.isclose(el.velocidade_critica(L_t, -K_t), el.velocidade_caracteristica(L_t, K_t), rel_tol=1e-12)
      and el.velocidade_caracteristica(L_t, -K_t) is None and el.velocidade_critica(L_t, K_t) is None,
      f"V={el.velocidade_caracteristica(L_t, K_t):.3f} m/s")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
