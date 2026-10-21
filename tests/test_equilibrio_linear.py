"""
Testes do equilíbrio linear (V4.0, incremento 2).
TC-EQ-021..023 (IDs autorizados pelo usuário): rigidez de deriva e de camber do PAC2002.
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

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
