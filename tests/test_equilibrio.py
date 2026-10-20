"""
Testes do módulo equilibrio (análise de par, Milliken §7.1; V4.0, incremento 1).
TC-EQ-001..003 (IDs autorizados pelo usuário): caso, cargas e camber por roda.
Roda como script: uv run python -X utf8 tests/test_equilibrio.py
O veículo e os números de camber abaixo são entradas de teste, não do carro.
"""

import os

import equilibrio as eq
import suspension_model as sm
import tire_model as tm
from suspension_model import VehicleConfig, G

TOL = 1e-9
HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []


def raises(fn, exc=ValueError, needle=None):
    try:
        fn()
        return False
    except exc as e:
        return needle is None or needle in str(e)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def veiculo_base(**over) -> VehicleConfig:
    """Veículo de teste (números plausíveis, NÃO é setup real)."""
    base = dict(
        mass_total=250.0,
        cg_height=0.300,
        wheelbase=1.550,
        track_front=1.200,
        track_rear=1.150,
        cg_to_front=0.837,
        cg_to_rear=0.713,
        unsprung_mass_front=15.0,
        unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230,
        unsprung_cg_height_rear=0.230,
        roll_center_front=0.030,
        roll_center_rear=0.050,
        roll_stiffness_front=20826.4,
        roll_stiffness_rear=26450.0,
    )
    base.update(over)
    return VehicleConfig(**base)


cfg = veiculo_base()
ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")

# ---------------- TC-EQ-001 : a_y = 0 ----------------
caso = eq.CasoEquilibrio(cfg=cfg, ds=ds, downforce_N=400.0, aero_balance_front=0.45)
c0 = eq.cargas(caso, 0.0)
est = sm.static_fz_corner(cfg)
aer = sm.aero_fz_corner(400.0, 0.45)
dif = max(abs(c0[c] - (est[c] + aer[c])) for c in eq.CANTOS)
check("TC-EQ-001: a_y=0 -> Fz = estático + aero em cada canto", dif < TOL, f"max dif={dif:.2e} N")

# ---------------- TC-EQ-002 : a_y = 1,2 g ----------------
c12 = eq.cargas(caso, 1.2 * G)
soma = sum(c12.values())
check("TC-EQ-002: a_y=1,2g -> soma = m·G + DF; FR>FL e RR>RL",
      abs(soma - (cfg.mass_total * G + 400.0)) < TOL and c12["FR"] > c12["FL"] and c12["RR"] > c12["RL"],
      f"soma={soma:.6f} FL={c12['FL']:.1f} FR={c12['FR']:.1f} RL={c12['RL']:.1f} RR={c12['RR']:.1f}")

# ---------------- TC-EQ-003 : camber por roda e validação ----------------
estatico = {"FL": -0.01, "FR": -0.01, "RL": -0.02, "RR": -0.02}
ganho = {"FL": 0.5, "FR": -0.5, "RL": 0.3, "RR": -0.3}
caso_c = eq.CasoEquilibrio(cfg=cfg, ds=ds, camber_estatico_rad=estatico, ganho_camber=ganho)
phi = sm.lateral_dfz(cfg, 1.0 * G)["roll_angle_rad"]
gam = eq.camber(caso_c, 1.0 * G)
dif = max(abs(gam[c] - (estatico[c] + ganho[c] * phi)) for c in eq.CANTOS)
erro_toe = raises(lambda: eq.CasoEquilibrio(cfg=cfg, ds=ds, toe_rad={"FL": 0.0}), ValueError, "toe_rad")
check("TC-EQ-003: camber = estático + ganho·φ (φ de lateral_dfz); toe_rad com cantos faltando -> ValueError",
      dif < 1e-15 and phi != 0.0 and erro_toe, f"phi={phi:.6f} rad, max dif={dif:.2e}")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
