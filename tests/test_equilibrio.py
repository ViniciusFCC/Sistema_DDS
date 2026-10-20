"""
Testes do módulo equilibrio (análise de par, Milliken §7.1; V4.0, incremento 1).
TC-EQ-001..003 (IDs autorizados pelo usuário): caso, cargas e camber por roda.
TC-EQ-004..008 (idem): curva do eixo, capacidade, borda da grade, faixa do pneu e sinal do toe.
Roda como script: uv run python -X utf8 tests/test_equilibrio.py
O veículo e os números de camber abaixo são entradas de teste, não do carro.
"""

import dataclasses
import math
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

# ---------------- TC-EQ-004 : fy_eixo = soma das duas rodas ----------------
caso0 = eq.CasoEquilibrio(cfg=cfg, ds=ds)
fz0 = eq.cargas(caso0, 0.0)
dif = 0.0
for a in eq.grade_alfa(caso0, 25):
    esperado = (tm.wheel_forces(ds, "FL", fz0["FL"], a, 0.0, 0.0)[1]
                + tm.wheel_forces(ds, "FR", fz0["FR"], a, 0.0, 0.0)[1])
    dif = max(dif, abs(eq.fy_eixo(caso0, "F", 0.0, a) - esperado))
check("TC-EQ-004: fy_eixo = Fy(FL) + Fy(FR) em cada alfa da grade (a_y=0, toe e camber 0)",
      dif < TOL, f"max dif={dif:.2e} N")

# ---------------- TC-EQ-005 : máximo numérico = forma fechada |Dy| + SVy ----------------
fnom = ds.p["FNOMIN"]
info = tm.pure_fy0(ds.p, fnom, 0.0, 0.0)[1]
fechada = abs(info["Dy"]) + info["SVy"]
N = 4001
alfas = [i * ds.p["ALPMIN"] / (N - 1) for i in range(N)]
fys = [tm.wheel_forces(ds, "FR", fnom, a, 0.0, 0.0)[1] for a in alfas]
fmax = max(fys)
i_pico = fys.index(fmax)
rel = abs(fmax - fechada) / fechada
check("TC-EQ-005: max numérico de Fy (FR, FNOMIN, gamma=0) = |Dy|+SVy (erro rel < 1e-4); pico fora da borda",
      rel < 1e-4 and i_pico < N - 1,
      f"num={fmax:.3f} N, fechada={fechada:.3f} N, rel={rel:.2e}, idx={i_pico}, "
      f"alfa={math.degrees(alfas[i_pico]):.2f} deg")

# ---------------- TC-EQ-006 : pico na borda da grade ----------------
# Dataset de teste (PKY1 x 0,05): pneu pouco rígido, pico além da faixa de alfa. Não é pneu.
ds_mole = dataclasses.replace(ds, p={**ds.p, "PKY1": ds.p["PKY1"] * 0.05})
caso_mole = eq.CasoEquilibrio(cfg=cfg, ds=ds_mole)
cap_mole = eq.capacidade_eixo(caso_mole, "F", 0.0, 200)
check("TC-EQ-006: pneu pouco rígido -> motivo 'pico na borda da grade de α' (valor mantido)",
      cap_mole.motivo == "pico na borda da grade de α" and cap_mole.fy_max_N is not None,
      f"motivo={cap_mole.motivo!r}, fy_max={cap_mole.fy_max_N}")

# ---------------- TC-EQ-007 : Fz fora da faixa -> None com motivo, sem exceção ----------------
fz2 = eq.cargas(caso0, 2.0 * G)
try:
    cap_fora = eq.capacidade_eixo(caso0, "F", 2.0 * G, 25)
    sem_excecao = True
except Exception:  # o check precisa registrar qualquer exceção como falha
    cap_fora = None
    sem_excecao = False
def _cap_sem_excecao(caso_x, ay):
    try:
        return eq.capacidade_eixo(caso_x, "F", ay, 25)
    except Exception:  # o check precisa registrar qualquer exceção como falha
        return None


# camber estático além de CAMMAX numa roda dianteira, e toe maior que a faixa de α
cam_fora = ds.p["CAMMAX"] + math.radians(1.0)
cap_cam = _cap_sem_excecao(eq.CasoEquilibrio(
    cfg=cfg, ds=ds, camber_estatico_rad={"FL": 0.0, "FR": cam_fora, "RL": 0.0, "RR": 0.0}), 0.0)
toe_grande = 2.0 * min(abs(ds.p["ALPMIN"]), ds.p["ALPMAX"])
cap_toe = _cap_sem_excecao(eq.CasoEquilibrio(
    cfg=cfg, ds=ds, toe_rad={"FL": toe_grande, "FR": toe_grande, "RL": 0.0, "RR": 0.0}), 0.0)
check("TC-EQ-007: Fz, camber ou toe fora da faixa do pneu -> fy_max None com motivo, sem exceção",
      fz2["FL"] < ds.p["FZMIN"] and sem_excecao and cap_fora.fy_max_N is None
      and cap_fora.alfa_pico_rad is None and "fora da faixa do pneu" in (cap_fora.motivo or "")
      and cap_cam is not None and cap_cam.fy_max_N is None and cap_cam.alfa_pico_rad is None
      and cap_cam.motivo.startswith("camber_FR = ") and "fora da faixa do pneu" in cap_cam.motivo
      and cap_toe is not None and cap_toe.fy_max_N is None and cap_toe.motivo == "toe consome a faixa de α",
      f"Fz_FL={fz2['FL']:.1f} N, FZMIN={ds.p['FZMIN']}, motivos={getattr(cap_fora, 'motivo', None)!r}; "
      f"{getattr(cap_cam, 'motivo', None)!r}; {getattr(cap_toe, 'motivo', None)!r}")

# ---------------- TC-EQ-008 : sinal do toe (EDR-002) ----------------
um_grau = math.radians(1.0)
caso_toe = eq.CasoEquilibrio(cfg=cfg, ds=ds, toe_rad={"FL": um_grau, "FR": um_grau, "RL": 0.0, "RR": 0.0})
fzt = eq.cargas(caso_toe, 0.0)
dal = eq.deriva_toe(caso_toe)
fy_fl = tm.wheel_forces(ds, "FL", fzt["FL"], dal["FL"], 0.0, 0.0)[1]
fy_fr = tm.wheel_forces(ds, "FR", fzt["FR"], dal["FR"], 0.0, 0.0)[1]
fy_ax = eq.fy_eixo(caso_toe, "F", 0.0, 0.0)
check("TC-EQ-008: toe-out simétrico de 1 grau -> Fy(FL) > 0, Fy(FR) < 0, soma ~ 0",
      dal["FL"] < 0 < dal["FR"] and fy_fl > 0 and fy_fr < 0 and abs(fy_ax) < TOL,
      f"FL={fy_fl:.3f} N, FR={fy_fr:.3f} N, soma={fy_ax:.2e}")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
