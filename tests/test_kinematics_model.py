"""
Test Cases do kinematics_model_V2_0.py (V2.1: + TC-KIN-118, convenção de sinal AD/AS). Roda como script: python3 test_kinematics_model_V2_1.py
Parte 1: TC-KIN-001..006 (herdados da V1.0; funções 2D inalteradas).
Parte 2: TC-KIN-101.. (solver 3D V2.0). Verificações independentes usam scipy (só nos testes).
Toda geometria aqui é SINTÉTICA ou de fixture analítica — nenhuma representa o carro.
"""
import os, csv, tempfile
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name  # tudo que o teste cria em temp fica aqui e é apagado no fim
import numpy as np
from scipy.optimize import brentq, least_squares

from kinematics_model import (
    Hardpoint, instant_center_front_view, roll_center_height, roll_center_model_check,
    side_view_inner_midpoint, instant_center_side_view, tan_phi_from_ic, anti_dive_squat_model_check,
    line_intersection,
    Corner, KinematicsError, sweep, steer_sweep, steering_ratio, motion_ratio, kinematic_centers,
    roll_center_height_kinematic, axle_roll_center, force_line_slope, anti_dive_percent_signed,
    anti_squat_percent_signed, ic_methods_at_reference, full_sweep, write_sweep_csv, _rot_vec,
)
from hardpoints import load_hardpoints, build_hardpoint_set, HardpointSet

HERE = os.path.dirname(os.path.abspath(__file__))
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status))
    print(f"[{status}] {name}  {detail}")


# =====================================================================
# PARTE 1 — herdados da V1.0
# =====================================================================
lca_outer = Hardpoint(y=0.65, z=0.25)
lca_inner = Hardpoint(y=0.20, z=0.28)
uca_outer = Hardpoint(y=0.60, z=0.55)
uca_inner = Hardpoint(y=0.20, z=0.50)
contact_patch = Hardpoint(y=0.65, z=0.0)
result = roll_center_model_check(lca_outer, lca_inner, uca_outer, uca_inner, contact_patch)
ic = result["instant_center"]; rc = result["roll_center_height"]
check("TC-KIN-001a: Instant Center Y", abs(ic.y - (-0.94783)) < 1e-4, f"IC.y={ic.y:.5f}")
check("TC-KIN-001b: Instant Center Z", abs(ic.z - 0.35652) < 1e-4, f"IC.z={ic.z:.5f}")
check("TC-KIN-001c: Roll Center height", abs(rc - 0.14503) < 1e-4, f"RC={rc:.5f} m")
try:
    instant_center_front_view(Hardpoint(0.65, 0.30), Hardpoint(0.20, 0.30), Hardpoint(0.60, 0.55), Hardpoint(0.20, 0.55))
    check("TC-KIN-002: braços paralelos levanta ValueError", False, "não levantou erro - BUG")
except ValueError as e:
    check("TC-KIN-002: braços paralelos levanta ValueError", True, str(e)[:60])
mirror = lambda hp: Hardpoint(y=-hp.y, z=hp.z)
rm = roll_center_model_check(mirror(lca_outer), mirror(lca_inner), mirror(uca_outer), mirror(uca_inner), mirror(contact_patch))
check("TC-KIN-003: RC height igual ao espelhar geometria (Y -> -Y)", abs(rm["roll_center_height"] - rc) < 1e-9,
      f"original={rc:.5f}  espelhado={rm['roll_center_height']:.5f}")
mid = side_view_inner_midpoint(Hardpoint(y=0.10, z=0.24), Hardpoint(y=-0.10, z=0.26))
check("TC-KIN-004: ponto médio das buchas (vista lateral)", abs(mid.y) < 1e-9 and abs(mid.z - 0.25) < 1e-9)
ic_sv = line_intersection(Hardpoint(2.0, 2.0), Hardpoint(0.0, 1.0), Hardpoint(1.0, 2.5), Hardpoint(0.0, 3.0))
check("TC-KIN-005a: Instant Center lateral (X)", abs(ic_sv.y - 2.0) < 1e-6)
check("TC-KIN-005b: Instant Center lateral (Z)", abs(ic_sv.z - 2.0) < 1e-6)
tan_phi = tan_phi_from_ic(ic_sv, contact_patch_x=0.6)
check("TC-KIN-005c: tan(phi)", abs(tan_phi - (2.0 / 1.4)) < 1e-6, f"tan(phi)={tan_phi:.5f}")
pct = 0.60 * tan_phi * (1.55 / 0.315) * 100
check("TC-KIN-005d: %AD a partir de tan(phi)", abs(pct - 0.60 * (2.0 / 1.4) * (1.55 / 0.315) * 100) < 1e-6,
      f"%AD={pct:.3f} (só verificação matemática - geometria não representa carro real)")
try:
    instant_center_side_view(
        Hardpoint(y=0.75, z=0.20), Hardpoint(y=0.10, z=0.24), Hardpoint(y=-0.10, z=0.24),
        Hardpoint(y=0.70, z=0.50), Hardpoint(y=0.10, z=0.5373333333333333), Hardpoint(y=-0.10, z=0.5373333333333333))
    check("TC-KIN-006: braços paralelos (vista lateral) levanta ValueError", False, "não levantou erro - BUG")
except ValueError as e:
    check("TC-KIN-006: braços paralelos (vista lateral) levanta ValueError", "lateral" in str(e), str(e)[:60])


# =====================================================================
# PARTE 2 — solver 3D V2.0
# =====================================================================
META = {"schema_version": "V2.0", "geometry_rev": "G-REV-TEST", "coordinate_system": "ISO8855_X_FORWARD_Y_LEFT_Z_UP",
        "units": "m", "ground_plane_z_m": 0.0, "kop": "RH", "source": "SYNTHETIC test fixture",
        "freeze_level": "F0", "timestamp": "2026-10-09T00:00:00-03:00"}
COMP = {"LCA_IN_F": "CHASSIS", "LCA_IN_R": "CHASSIS", "LCA_OUT": "UPRIGHT", "UCA_IN_F": "CHASSIS", "UCA_IN_R": "CHASSIS",
        "UCA_OUT": "UPRIGHT", "TIE_IN": "RACK", "TIE_OUT": "UPRIGHT", "WHEEL_CENTER": "WHEEL", "SPINDLE_PT": "WHEEL",
        "CONTACT_PATCH": "WHEEL", "PUSH_IN": "ROCKER", "ROCKER_AXIS_A": "CHASSIS", "ROCKER_AXIS_B": "CHASSIS",
        "ROCKER_SPRING": "ROCKER", "SPRING_CHASSIS": "CHASSIS"}


def make_hs(pts, side="L", push_body="UPRIGHT"):
    """pts: chave -> xyz do canto esquerdo (FL). side='R' espelha em Y e usa o prefixo FR."""
    rows = []
    for k, xyz in pts.items():
        comp = push_body if k == "PUSH_OUT" else COMP[k]
        x, y, z = xyz
        if side == "R":
            y = -y
        rows.append([f"F{side}_{k}", f"{x:.12f}", f"{y:.12f}", f"{z:.12f}", comp, "SYNTHETIC"])
    return build_hardpoint_set(rows, META)


def planar(**kw):
    p = {"LCA_IN_F": (0.15, 0.20, 0.14), "LCA_IN_R": (-0.15, 0.20, 0.14), "LCA_OUT": (0.0, 0.56, 0.16),
         "UCA_IN_F": (0.15, 0.25, 0.32), "UCA_IN_R": (-0.15, 0.25, 0.32), "UCA_OUT": (0.0, 0.53, 0.33),
         "TIE_IN": (-0.10, 0.20, 0.14), "TIE_OUT": (-0.10, 0.56, 0.16),   # barra = cópia paralela do LCA em Y-Z -> compatível, bump steer nulo
         "WHEEL_CENTER": (0.0, 0.62, 0.23), "SPINDLE_PT": (0.0, 0.70, 0.23), "CONTACT_PATCH": (0.0, 0.62, 0.0)}
    p.update(kw)
    return p


def parallelogram():
    return planar(LCA_IN_F=(0.15, 0.20, 0.14), LCA_IN_R=(-0.15, 0.20, 0.14), LCA_OUT=(0.0, 0.60, 0.14),
                  UCA_IN_F=(0.15, 0.20, 0.34), UCA_IN_R=(-0.15, 0.20, 0.34), UCA_OUT=(0.0, 0.60, 0.34),
                  TIE_IN=(-0.10, 0.20, 0.14), TIE_OUT=(-0.10, 0.60, 0.14),
                  WHEEL_CENTER=(0.0, 0.65, 0.24), SPINDLE_PT=(0.0, 0.75, 0.24), CONTACT_PATCH=(0.0, 0.65, 0.0))


synth_hs = load_hardpoints(os.path.join(HERE, "..", "data", "hardpoints_synthetic_V2.0.csv"),
                           os.path.join(HERE, "..", "data", "hardpoints_synthetic_V2.0.meta.json"))
FL = Corner(synth_hs, "FL")
FR = Corner(synth_hs, "FR")
TR = [-0.040, -0.030, -0.020, -0.010, 0.0, 0.010, 0.020, 0.030, 0.040]

# ---- TC-KIN-101: preservação de comprimentos, medida DIRETAMENTE nos pontos em pose (não pelo resíduo do solver)
worst = 0.0
sw = sweep(FL, TR)
for sol, m in sw:
    P = lambda k: FL.pt(sol, k)
    pairs = [("LCA_OUT", "LCA_IN_F"), ("LCA_OUT", "LCA_IN_R"), ("UCA_OUT", "UCA_IN_F"), ("UCA_OUT", "UCA_IN_R"),
             ("LCA_OUT", "UCA_OUT"), ("TIE_OUT", "TIE_IN"), ("LCA_OUT", "WHEEL_CENTER"), ("UCA_OUT", "CONTACT_PATCH"),
             ("PUSH_OUT", "LCA_OUT"), ("PUSH_OUT", "LCA_IN_F"), ("PUSH_OUT", "PUSH_IN"),
             ("PUSH_IN", "ROCKER_AXIS_A"), ("PUSH_IN", "ROCKER_SPRING"), ("ROCKER_SPRING", "ROCKER_AXIS_B")]
    sol0 = FL.solve(0.0)
    for a, b in pairs:
        d = np.linalg.norm(P(a) - P(b)); d0 = np.linalg.norm(FL.pt(sol0, a) - FL.pt(sol0, b))
        worst = max(worst, abs(d - d0))
check("TC-KIN-101: comprimentos de todos os elos/corpos rígidos preservados em ±40 mm", worst < 1e-10, f"pior erro={worst:.2e} m")

# ---- TC-KIN-102: pose de referência reproduz a entrada
s0 = FL.solve(0.0)
m0 = FL.metrics(s0)
check("TC-KIN-102a: q=0 na referência", np.linalg.norm(s0.q) < 1e-10, f"|q|={np.linalg.norm(s0.q):.2e}")
check("TC-KIN-102b: camber de referência = -1.5° (valor usado para construir a geometria sintética)",
      abs(m0["camber_deg"] - (-1.5)) < 1e-6 and abs(m0["toe_deg"]) < 1e-6,
      f"camber={m0['camber_deg']:.9f} toe={m0['toe_deg']:.2e}")

# ---- TC-KIN-103: mecanismo plano vs four-bar 2D independente (brentq) -----------------
pl = planar()
hs_pl = make_hs(pl)
Cpl = Corner(hs_pl, "FL")
OL, BL0 = np.array(pl["LCA_IN_F"][1:]), np.array(pl["LCA_OUT"][1:])
OU, BU0 = np.array(pl["UCA_IN_F"][1:]), np.array(pl["UCA_OUT"][1:])
WC0 = np.array(pl["WHEEL_CENTER"][1:])
rL, rU, d = np.linalg.norm(BL0 - OL), np.linalg.norm(BU0 - OU), np.linalg.norm(BU0 - BL0)
phiL0 = np.arctan2(*(BL0 - OL)[::-1])
psi0 = np.arctan2(*(BU0 - BL0)[::-1])


def fourbar(phi):
    BL = OL + rL * np.array([np.cos(phi), np.sin(phi)])
    # interseção de círculos: |B-OU|=rU, |B-BL|=d; escolhe o ponto mais próximo de BU0
    D = np.linalg.norm(OU - BL); a = (rU ** 2 - d ** 2 + D ** 2) / (2 * D); h = np.sqrt(max(rU ** 2 - a ** 2, 0.0))
    e = (BL - OU) / D; n = np.array([-e[1], e[0]])
    cands = [OU + a * e + h * n, OU + a * e - h * n]
    BU = min(cands, key=lambda c: np.linalg.norm(c - BU0))
    psi = np.arctan2(*(BU - BL)[::-1]); alpha = psi - psi0
    R = np.array([[np.cos(alpha), -np.sin(alpha)], [np.sin(alpha), np.cos(alpha)]])
    return BL, BU, alpha, BL + R @ (WC0 - BL0)


err_a = err_p = 0.0
for t in (-0.040, -0.020, 0.020, 0.040):
    phi = brentq(lambda p: fourbar(p)[3][1] - pl["WHEEL_CENTER"][2] - t, phiL0 - 0.4, phiL0 + 0.4)
    BL, BU, alpha, WC = fourbar(phi)
    sol = Cpl.solve(t)
    wc3 = Cpl.pt(sol, "WHEEL_CENTER")
    err_p = max(err_p, abs(wc3[1] - WC[0]), abs(wc3[2] - WC[1]))
    # rotação da manga em torno de X obtida do 3D: ângulo do vetor LCA_OUT->UCA_OUT projetado em Y-Z
    v3 = Cpl.pt(sol, "UCA_OUT") - Cpl.pt(sol, "LCA_OUT")
    alpha3 = np.arctan2(v3[2], v3[1]) - psi0
    err_a = max(err_a, abs(alpha3 - alpha))
check("TC-KIN-103a: posição do centro da roda, 3D vs four-bar 2D independente", err_p < 1e-9, f"erro máx={err_p:.2e} m")
check("TC-KIN-103b: rotação da manga (camber), 3D vs four-bar 2D independente", err_a < 1e-9, f"erro máx={err_a:.2e} rad")
toe_pl = max(abs(Cpl.metrics(Cpl.solve(x))["toe_deg"]) for x in (-0.04, 0.04))
check("TC-KIN-103c: mecanismo plano com barra compatível -> toe nulo (a manga não gira em torno do pino mestre)", toe_pl < 1e-7, f"toe máx={toe_pl:.1e}°")

# ---- TC-KIN-104: paralelogramo -> camber constante e bump steer nulo (resultado analítico) ----------
Cpar = Corner(make_hs(parallelogram()), "FL")
swp = sweep(Cpar, [-0.03, 0.0, 0.03])
cam = [m["camber_deg"] for _, m in swp]; toe = [m["toe_deg"] for _, m in swp]; trk = [m["track_change_m"] for _, m in swp]
check("TC-KIN-104a: paralelogramo -> variação de camber nula", max(abs(c - cam[1]) for c in cam) < 1e-7, f"camber={cam}")
check("TC-KIN-104b: paralelogramo com barra de direção paralela -> bump steer nulo", max(abs(x) for x in toe) < 1e-7, f"toe={toe}")
check("TC-KIN-104c: paralelogramo -> track change não nulo (arco dos braços ≈ L(1-cos θ))", abs(trk[0]) > 5e-4 and abs(trk[2]) > 5e-4,
      f"track change=±{abs(trk[0])*1e3:.3f} mm")

# ---- TC-KIN-105: espelhamento FL x FR ------------------------------------------------------------
swR = sweep(FR, TR)
keys = ["camber_deg", "toe_deg", "caster_deg", "kpi_deg", "scrub_radius_m", "mech_trail_m", "track_change_m", "spring_length_m"]
dev = max(abs(a[1][k] - b[1][k]) for a, b in zip(sw, swR) for k in keys)
check("TC-KIN-105: canto direito espelhado reproduz o esquerdo (camber, toe, caster, KPI, scrub, trail, track, mola)", dev < 1e-9, f"dif máx={dev:.2e}")

# ---- TC-KIN-106: sinais de camber e toe (casos analíticos, esquerda e direita) ----------------------
def axis_case(ang_cam_deg, ang_toe_deg, side):
    ac, at = np.radians(ang_cam_deg), np.radians(ang_toe_deg)
    # eixo para fora com camber>0 (ponta para baixo) e toe-out>0 (ponta para trás); y_out = +1 esquerda
    a = np.array([-np.sin(at) * np.cos(ac), np.cos(at) * np.cos(ac), -np.sin(ac)])
    p = planar(SPINDLE_PT=tuple(np.array(pl["WHEEL_CENTER"]) + 0.08 * a))
    return Corner(make_hs(p, side=side), "FL" if side == "L" else "FR")

okc = okt = True
for side in ("L", "R"):
    mm = axis_case(5.0, 0.0, side).metrics(axis_case(5.0, 0.0, side).solve(0.0))
    okc &= abs(mm["camber_deg"] - 5.0) < 1e-9 and abs(mm["toe_deg"]) < 1e-9
    mm = axis_case(0.0, 1.0, side).metrics(axis_case(0.0, 1.0, side).solve(0.0))
    okt &= abs(mm["toe_deg"] - 1.0) < 1e-9 and abs(mm["camber_deg"]) < 1e-9
check("TC-KIN-106a: camber positivo = topo para fora (esq. e dir.)", okc)
check("TC-KIN-106b: toe positivo = toe-out (esq. e dir.)", okt)

# ---- TC-KIN-107: IC e RC cinemáticos == V1 2D no mecanismo plano (dois métodos independentes) ----------
errs_ic = errs_rc = 0.0
for t in (-0.030, 0.0, 0.030):
    sol = Cpl.solve(t)
    k = kinematic_centers(Cpl, t)
    P = lambda key: Cpl.pt(sol, key)
    cpz = P("CONTACT_PATCH")[2]
    h = lambda key: Hardpoint(y=float(P(key)[1]), z=float(P(key)[2] - cpz))
    ic2 = instant_center_front_view(h("LCA_OUT"), h("LCA_IN_F"), h("UCA_OUT"), h("UCA_IN_F"))
    rc2 = roll_center_height(h("CONTACT_PATCH"), ic2)
    errs_ic = max(errs_ic, abs(k["front"]["point"][0] - ic2.y), abs(k["front"]["point"][1] - (ic2.z + cpz)))
    errs_rc = max(errs_rc, abs(roll_center_height_kinematic(Cpl, t) - rc2))
check("TC-KIN-107a: IC frontal por velocidade dos ball joints == interseção 2D (V1), 3 cursos", errs_ic < 2e-6, f"erro máx={errs_ic:.2e} m")
check("TC-KIN-107b: RC cinemático == RC da V1 aplicada à geometria em pose, 3 cursos", errs_rc < 2e-6, f"erro máx={errs_rc:.2e} m")

# ---- TC-KIN-108: MR analítico (pushrod vertical, rocker 1:1.5) ---------------------------------------
mrp = parallelogram()
mrp.update({"PUSH_OUT": (0.05, 0.62, 0.30), "PUSH_IN": (0.05, 0.62, 0.55),
            "ROCKER_AXIS_A": (-0.10, 0.56, 0.55), "ROCKER_AXIS_B": (0.20, 0.56, 0.55),
            "ROCKER_SPRING": (0.05, 0.52, 0.55), "SPRING_CHASSIS": (0.05, 0.52, 0.35)})
Cmr = Corner(make_hs(mrp, push_body="UPRIGHT"), "FL")
mr = motion_ratio(Cmr)
check("TC-KIN-108a: MR = r1/r2 = 0,06/0,04 = 1,5 (analítico, 1ª ordem)", abs(mr["mr_wheel_per_spring"] - 1.5) < 1e-6,
      f"MR={mr['mr_wheel_per_spring']:.8f}")
check("TC-KIN-108b: mola comprime em bump (dL/dz<0)", mr["dLspring_dz"] < 0, f"dL/dz={mr['dLspring_dz']:.5f}")

# ---- TC-KIN-109: esterçamento analítico (pino mestre vertical, barra atrás: yaw = -s/e) -------------
s_rack, e_off = 1e-3, 0.10
yaw = steer_sweep(Cpar, [-s_rack, s_rack])
check("TC-KIN-109a: yaw = -s/e (cremalheira +Y com barra atrás do pino -> roda esterça para a direita)",
      abs(yaw[1][1] - np.degrees(-s_rack / e_off)) < 5e-4 * abs(np.degrees(s_rack / e_off)),
      f"yaw={yaw[1][1]:.5f}° esperado={np.degrees(-s_rack/e_off):.5f}°")
sr = steering_ratio(Cpar, rack_travel_per_rev_m=0.060)
check("TC-KIN-109b: razão de direção analítica (360/0,060)/(57,2958/0,10)=10,47", abs(sr - 10.4720) < 1e-2, f"SR={sr:.4f}")

# ---- TC-KIN-110: IC lateral e anti-dive/squat (fórmula fechada para eixos em planos X-Z) ----------------
def side_fixture(zLF, zLR, zUF, zUR, flip=False):
    p = planar(LCA_IN_F=(0.15, 0.20, zLF), LCA_IN_R=(-0.15, 0.20, zLR), UCA_IN_F=(0.15, 0.25, zUF), UCA_IN_R=(-0.15, 0.25, zUR))
    if flip:   # espelha X: o IC passa de atrás para a frente do contact patch
        p = {k: (-v[0], v[1], v[2]) for k, v in p.items()}
        p["LCA_IN_F"], p["LCA_IN_R"] = p["LCA_IN_R"], p["LCA_IN_F"]
        p["UCA_IN_F"], p["UCA_IN_R"] = p["UCA_IN_R"], p["UCA_IN_F"]
    return Corner(make_hs(p), "FL")

def closed_form_side_ic(C):
    # retas pelos ball joints externos, paralelas aos eixos de pivô projetados em X-Z (válido p/ eixos em planos X-Z)
    lines = []
    for w in ("LCA", "UCA"):
        u = (C.p0[f"{w}_IN_R"] - C.p0[f"{w}_IN_F"])[[0, 2]]; P = C.p0[f"{w}_OUT"][[0, 2]]
        lines.append((P, u / np.linalg.norm(u)))
    (p1, d1), (p2, d2) = lines
    A = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]])
    if abs(np.linalg.det(A)) < 1e-14:
        return None, d1
    t = np.linalg.solve(A, p2 - p1)
    return p1 + t[0] * d1, None

Cb = side_fixture(0.12, 0.16, 0.34, 0.30)
kb = kinematic_centers(Cb)
cf, _ = closed_form_side_ic(Cb)
check("TC-KIN-110a: IC lateral cinemático == fórmula fechada (eixos em planos X-Z)", np.linalg.norm(kb["side"]["point"] - cf) < 1e-5,
      f"IC cinemático={kb['side']['point']} fechada={cf}")
cp_xz = kb["contact_patch"][[0, 2]]
sl = force_line_slope(kb["side"], cp_xz)
L_, h_ = 1.55, 0.315
ad = anti_dive_percent_signed(sl, 0.60, L_, h_)
check("TC-KIN-110b: IC atrás e acima do contact patch -> anti-dive POSITIVO (frente)", kb["side"]["point"][0] < cp_xz[0] and ad > 0, f"IC.x={kb['side']['point'][0]:.3f} %AD={ad:.2f}")
Cf = side_fixture(0.12, 0.16, 0.34, 0.30, flip=True)
kf = kinematic_centers(Cf)
slf = force_line_slope(kf["side"], kf["contact_patch"][[0, 2]])
adf = anti_dive_percent_signed(slf, 0.60, L_, h_)
check("TC-KIN-110c: IC à frente e acima do contact patch -> %AD NEGATIVO (pro-dive na frente)", kf["side"]["point"][0] > kf["contact_patch"][0] and adf < 0 and abs(adf + ad) < 1e-6,
      f"IC.x={kf['side']['point'][0]:.3f} %AD={adf:.2f}")
v1_tan = tan_phi_from_ic(Hardpoint(y=float(kf['side']['point'][0]), z=float(kf['side']['point'][1])), contact_patch_x=float(kf['contact_patch'][0]))
check("TC-KIN-110d: CARACTERIZAÇÃO — tan(phi) da V1 usa |d| e dá sinal positivo para o mesmo caso pro-dive", v1_tan > 0 and adf < 0,
      f"V1 tan(phi)={v1_tan:.4f} (>0) x signed %AD={adf:.2f} (<0)")
asq = anti_squat_percent_signed(slf, 1.0, L_, h_)
check("TC-KIN-110e: mesmo caso (IC à frente e acima) -> anti-squat POSITIVO no eixo traseiro", asq > 0, f"%AS={asq:.2f}")

# ---- TC-KIN-111: eixos paralelos e inclinados em vista lateral -> IC no infinito, %AD pela inclinação -----
Cpa = side_fixture(0.135, 0.150, 0.335, 0.350)       # ambos: dz/dx = (zF-zR)/0.30 = -0.05
kp = kinematic_centers(Cpa)
slp = force_line_slope(kp["side"], kp["contact_patch"][[0, 2]])
check("TC-KIN-111a: eixos paralelos -> IC lateral no infinito (point=None, direction definida)", kp["side"]["point"] is None and kp["side"]["direction"] is not None)
check("TC-KIN-111b: inclinação da linha de força = inclinação dos eixos (-0,05)", slp is not None and abs(slp - (-0.05)) < 1e-6, f"slope={slp}")
check("TC-KIN-111c: %AD = FB_f·(0,05)·L/h·100", abs(anti_dive_percent_signed(slp, 0.6, L_, h_) - 0.6 * 0.05 * L_ / h_ * 100) < 1e-4)

# ---- TC-KIN-112: solver independente (scipy, formulação por distâncias entre 4 pontos da manga) ---------
def solve_indep(C, travel):
    keys = ["LCA_OUT", "UCA_OUT", "TIE_OUT", "WHEEL_CENTER"]
    ref = {k: C.p0[k] for k in keys}
    pairs = [(a, b) for i, a in enumerate(keys) for b in keys[i + 1:]]
    d0 = {p: np.linalg.norm(ref[p[0]] - ref[p[1]]) for p in pairs}
    def F(x):
        P = {k: x[3 * i:3 * i + 3] for i, k in enumerate(keys)}
        r = []
        for k, inn, L in (("LCA_OUT", "LCA_IN_F", C.L["LF"]), ("LCA_OUT", "LCA_IN_R", C.L["LR"]),
                          ("UCA_OUT", "UCA_IN_F", C.L["UF"]), ("UCA_OUT", "UCA_IN_R", C.L["UR"]),
                          ("TIE_OUT", "TIE_IN", C.L["T"])):
            r.append(np.linalg.norm(P[k] - C.p0[inn]) - L)
        for p in pairs:
            r.append(np.linalg.norm(P[p[0]] - P[p[1]]) - d0[p])
        r.append(P["WHEEL_CENTER"][2] - ref["WHEEL_CENTER"][2] - travel)
        return np.array(r)
    x0 = np.concatenate([ref[k] for k in keys])
    s = least_squares(F, x0, xtol=1e-15, ftol=1e-15, gtol=1e-15)
    return {k: s.x[3 * i:3 * i + 3] for i, k in enumerate(keys)}, np.max(np.abs(F(s.x)))

worst = 0.0; res_max = 0.0
for t in (-0.030, 0.020, 0.040):
    P, rmax = solve_indep(FL, t); sol = FL.solve(t)
    res_max = max(res_max, rmax)
    for k in P:
        worst = max(worst, np.linalg.norm(P[k] - FL.pt(sol, k)))
check("TC-KIN-112: pose da manga, Newton (Rodrigues) vs scipy least_squares (distâncias entre pontos)", worst < 1e-8 and res_max < 1e-9,
      f"dif máx={worst:.2e} m, resíduo scipy={res_max:.1e}")

# ---- TC-KIN-113: RC do eixo ----------------------------------------------------------------------------------
yA, zA = axle_roll_center(FL, FR, 0.0)
rcL = roll_center_height_kinematic(FL, 0.0)
check("TC-KIN-113: RC do eixo simétrico em Y=0 e igual ao RC de um canto", abs(yA) < 1e-9 and abs(zA - rcL) < 1e-9, f"Y={yA:.2e} Z={zA*1e3:.3f} mm")

# ---- TC-KIN-114: CARACTERIZAÇÃO da incerteza de método (IC lateral, geometria sintética realista) -----------
meth = ic_methods_at_reference(FL)
cpxz = FL.p0["CONTACT_PATCH"][[0, 2]]
slopes = {n: force_line_slope(i, cpxz) for n, i in meth["side"].items()}
ad_by = {n: anti_dive_percent_signed(s, 0.6, L_, h_) for n, s in slopes.items()}
spread_front = np.linalg.norm(meth["front"]["kinematic"]["point"] - meth["front"]["v1_outer_to_inner"]["point"])
check("TC-KIN-114a: métodos de IC lateral dão %AD distintos (cinemático, eixos de pivô, V1 outer->inner); V1 > 10x o cinemático",
      abs(ad_by["v1_outer_to_inner"]) > 10 * abs(ad_by["kinematic"]),
      "%AD: " + ", ".join(f"{n}={v:.1f}" for n, v in ad_by.items()))
check("TC-KIN-114b: IC frontal, cinemático vs V1 (outer->ponto médio interno): diferença registrada (< 0,1 m)", spread_front < 0.1, f"|ΔIC|={spread_front*1e3:.1f} mm")

# ---- TC-KIN-115: erros explícitos -----------------------------------------------------------------------------
def raises(fn, exc):
    try:
        fn(); return False
    except exc:
        return True
check("TC-KIN-115a: curso impossível (+0,5 m) levanta KinematicsError, não retorna resposta silenciosa", raises(lambda: FL.solve(0.5), KinematicsError))
check("TC-KIN-115b: spring_length sem grupo pushrod levanta KinematicsError", raises(lambda: Cpar.spring_length(Cpar.solve(0.0)), KinematicsError))
check("TC-KIN-115c: canto inexistente levanta KinematicsError", raises(lambda: Corner(make_hs(planar()), "RL"), KinematicsError))

# ---- TC-KIN-116: varredura completa e CSV com unidade no nome ----------------------------------------------------
rows = full_sweep(FL, [-0.02, 0.0, 0.02])
tmp = os.path.join(tempfile.gettempdir(), "sweep_test.csv")
write_sweep_csv(rows, tmp)
with open(tmp) as f:
    hdr = next(csv.reader(f))
check("TC-KIN-116: full_sweep/CSV: colunas com unidade e todos os campos esperados",
      all(c in hdr for c in ["travel_m", "camber_deg", "toe_deg", "rc_height_m", "mr_wheel_per_spring", "side_force_line_slope"]) and len(rows) == 3,
      f"{len(hdr)} colunas")

# ---- TC-KIN-117: geometria do pino mestre e sinais (caso analítico, esquerda e direita) -----------------------------
# Pino mestre: LCA_OUT (0, 0.60, 0.14) -> UCA_OUT (-0.05, 0.56, 0.34): topo 50 mm para trás e 40 mm para dentro, 200 mm de altura.
# Esperado: caster = atan(0,05/0,20) = 14,0362° (+, topo para trás); KPI = atan(0,04/0,20) = 11,3099° (+, topo para dentro);
# interseção com o solo (z=0): s=-0,7 -> (0,035; 0,628; 0); CP (0; 0,65; 0) -> scrub = +22 mm (interseção inboard do CP), trail = +35 mm (à frente do CP).
kp_fix = parallelogram()
kp_fix["UCA_OUT"] = (-0.05, 0.56, 0.34)
ok_k = True; det = []
for side in ("L", "R"):
    Ck = Corner(make_hs(kp_fix, side=side), "FL" if side == "L" else "FR")
    mk = Ck.metrics(Ck.solve(0.0))
    ok_k &= (abs(mk["caster_deg"] - np.degrees(np.arctan(0.05 / 0.20))) < 1e-9 and abs(mk["kpi_deg"] - np.degrees(np.arctan(0.04 / 0.20))) < 1e-9
             and abs(mk["scrub_radius_m"] - 0.022) < 1e-9 and abs(mk["mech_trail_m"] - 0.035) < 1e-9)
    det.append((side, round(mk["caster_deg"], 4), round(mk["kpi_deg"], 4), round(mk["scrub_radius_m"] * 1e3, 3), round(mk["mech_trail_m"] * 1e3, 3)))
check("TC-KIN-117a: caster, KPI, scrub e trail analíticos (+ topo atrás, + topo dentro, + interseção inboard/à frente), esq. e dir.", ok_k, str(det))
ok_t = True
for side in ("L", "R"):
    Ct = Corner(make_hs(parallelogram(), side=side), "FL" if side == "L" else "FR")
    for tt in (-0.03, 0.03):
        ok_t &= abs(Ct.metrics(Ct.solve(tt))["track_change_m"] - (-0.4 * (1 - np.cos(np.arcsin(0.03 / 0.40))))) < 1e-9
check("TC-KIN-117b: track change = -L(1-cos θ) (contact patch vai para dentro em bump e em rebound), esq. e dir.", ok_t)


# ---- TC-KIN-118: CONVENÇÃO de sinal de AD/AS (EDR-026). Verifica a convenção de saída, NÃO valida o método geométrico. ----
Lw, hc = 1.55, 0.315
ad = lambda s, fb=0.6: anti_dive_percent_signed(s, fb, Lw, hc)
asq = lambda s, tf=1.0: anti_squat_percent_signed(s, tf, Lw, hc)
check("TC-KIN-118a: inclinação nula -> %AD = %AS = 0 (sem efeito geométrico líquido)", ad(0.0) == 0.0 and asq(0.0) == 0.0)
check("TC-KIN-118b: convenção — frente: linha sobe para trás (s<0) -> AD>0; sobe para frente (s>0) -> AD<0 (pro-dive)", ad(-0.1) > 0 and ad(0.1) < 0)
check("TC-KIN-118c: convenção — traseira: linha sobe para frente (s>0) -> AS>0; sobe para trás (s<0) -> AS<0 (pro-squat)", asq(0.1) > 0 and asq(-0.1) < 0)
check("TC-KIN-118d: antissimetria AD(s) = -AD(-s) e AS(s) = -AS(-s)", abs(ad(0.07) + ad(-0.07)) < 1e-12 and abs(asq(0.07) + asq(-0.07)) < 1e-12)
check("TC-KIN-118e: linear em FB_f/TF_r e em L/h; fração de força nula -> resultado nulo", abs(ad(-0.1, 0.3) * 2 - ad(-0.1, 0.6)) < 1e-12 and ad(-0.1, 0.0) == 0.0 and asq(0.1, 0.0) == 0.0)
check("TC-KIN-118f: AD (frente) e AS (traseira) são espelhos: AD(s) = AS(-s) para frações iguais", abs(ad(0.05, 1.0) - asq(-0.05, 1.0)) < 1e-12)

# ---------------- TC-KIN-119: ponto de reação do carro atual (EDR-048) ----------------
import kinematics_model as _km
_rp = _km.REACTION_POINT
_kc = kinematic_centers(FL)
_s_cp = force_line_slope(_kc["side"], _kc["contact_patch"][[0, 2]])
_s_wc = force_line_slope(_kc["side"], _kc["wheel_center"][[0, 2]])
check("TC-KIN-119: REACTION_POINT (freio outboard -> contact patch; motor no chassi -> centro da roda) e as duas linhas diferem",
      _rp == {"anti_dive_front": "contact_patch", "anti_lift_rear": "contact_patch", "anti_squat_rear": "wheel_center"}
      and len(full_sweep(FL, [0.0], reaction_point=_rp["anti_squat_rear"])) == 1 and abs(_s_cp - _s_wc) > 1e-3,
      f"inclinação contact patch={_s_cp:.4f}, centro da roda={_s_wc:.4f}")

# =====================================================================
# 2ª rodada da revisão metodológica (2026-10-19): linha de força pelo trabalho virtual (EDR-053) e direção (EDR-052)
# =====================================================================
import math
import kinematics_model as km

# ---- TC-KIN-120: linha de força pelo trabalho virtual (definição primária, EDR-053) ----
fpl = km.force_lines_vw(Cpl)
kpl = kinematic_centers(Cpl)
cp_pl = kpl["contact_patch"]
same = (abs(fpl["rc_height_m"] - roll_center_height_kinematic(Cpl)) < 1e-9
        and abs(fpl["side_slope_cp"] - force_line_slope(kpl["side"], cp_pl[[0, 2]])) < 1e-9
        and abs(fpl["side_slope_wc"] - force_line_slope(kpl["side"], kpl["wheel_center"][[0, 2]])) < 1e-9)
check("TC-KIN-120a: mecanismo plano — RC e inclinações laterais (contact patch e centro da roda) pelo trabalho virtual == método dos ball joints",
      same, f"RC={fpl['rc_height_m']*1e3:.4f} mm")
s0_, w_, vel_ = km._twist(FL)
cp_, vcp_ = FL.pt(s0_, "CONTACT_PATCH"), vel_("CONTACT_PATCH")
rig = max(np.linalg.norm(vel_(k) - (vcp_ + np.cross(w_, FL.pt(s0_, k) - cp_))) for k in ("LCA_OUT", "UCA_OUT", "TIE_OUT", "WHEEL_CENTER", "SPINDLE_PT"))
fFL = km.force_lines_vw(FL)
# IC frontal no plano X = X_cp: as normais às velocidades de dois pontos desse plano (corpo rígido) cruzam no IC devolvido
P1, P2 = cp_ + np.array([0, 0.05, 0.10]), cp_ + np.array([0, -0.04, 0.25])
v1, v2 = vcp_ + np.cross(w_, P1 - cp_), vcp_ + np.cross(w_, P2 - cp_)
icp = km._ic_from_velocities(P1[[1, 2]], v1[[1, 2]], P2[[1, 2]], v2[[1, 2]])["point"]
check("TC-KIN-120b: corpo rígido — v(P) = v_cp + ω×(P−cp) nos 5 pontos da manga, e o IC frontal no plano X = X_cp não depende dos pontos usados",
      rig < 1e-6 and np.linalg.norm(icp - fFL["ic_front"]) < 1e-6, f"resíduo rígido={rig:.1e}; |ΔIC|={np.linalg.norm(icp - fFL['ic_front']):.1e} m")
lit = km.reference_literal_centers(FL)
check("TC-KIN-120c: CARACTERIZAÇÃO (sintético FL) — RC: trabalho virtual 17,7 mm, ball joints 14,8 mm, leitura literal do help −142,6 mm; passo −0,47 m/rad",
      abs(fFL["rc_height_m"] - 0.01769) < 1e-4 and abs(roll_center_height_kinematic(FL) - 0.01479) < 1e-4
      and abs(lit["rc_height_m"] + 0.1426) < 1e-3 and abs(lit["pitch_m_per_rad"] + 0.4724) < 1e-3,
      f"vw={fFL['rc_height_m']*1e3:.2f} atual={roll_center_height_kinematic(FL)*1e3:.2f} literal={lit['rc_height_m']*1e3:.1f} mm; passo={lit['pitch_m_per_rad']:.4f}")

# ---- TC-KIN-121: spindle length (Milliken 19.1, Fig. 19.1), caso analítico ----
m_pl = Cpl.metrics(Cpl.solve(0.0))
sl_ref = 0.62 - (0.56 + (0.23 - 0.16) / (0.33 - 0.16) * (0.53 - 0.56))
check("TC-KIN-121: spindle length = distância horizontal do pino mestre ao centro da roda, na altura do centro (plano analítico; + = roda para fora)",
      abs(m_pl["spindle_length_m"] - sl_ref) < 1e-12, f"{m_pl['spindle_length_m']*1e3:.4f} mm (esperado {sl_ref*1e3:.4f})")

# ---- TC-KIN-122: Ackermann exato (Gillespie eq. 8-1/8-2) contra a Tab. 6.2 do Seward (bitola 1200 mm, entre-eixos 1600 mm) ----
seward = {10: 11.5, 15: 18.5, 20: 26.6, 25: 35.6}           # δo -> δi (texto p. 162 para 10°; tabela para os demais)
raio = {5: 18.4, 20: 4.7, 25: 3.8}
ok_s = all(abs(km.ackermann_inner_ideal_deg(o, 1.6, 1.2) - i) < 0.06 for o, i in seward.items())
ok_r = all(abs(km.turn_radius_outer_m(o, 1.6) - r) < 0.06 for o, r in raio.items())
check("TC-KIN-122a: δi de Ackermann (cot δo − cot δi = t/L) e raio externo L/sin δo reproduzem a Tab. 6.2 do Seward (arredondada a 0,1)",
      ok_s and ok_r, str({o: round(km.ackermann_inner_ideal_deg(o, 1.6, 1.2), 2) for o in seward}))
ai = km.ackermann_inner_ideal_deg(12, 1.55, 1.2)
check("TC-KIN-122b: % Ackermann: δi = ideal -> 100; δi = δo (paralelo) -> 0; δi < δo (reverso) -> negativo",
      abs(km.ackermann_percent(ai, 12, 1.55, 1.2) - 100) < 1e-9 and abs(km.ackermann_percent(12, 12, 1.55, 1.2)) < 1e-12
      and km.ackermann_percent(11, 12, 1.55, 1.2) < 0)

# ---- TC-KIN-123: Ackermann da geometria (sintético FL/FR) ----
tr_ = float(FL.p0["CONTACT_PATCH"][1] - FR.p0["CONTACT_PATCH"][1])
akR, akL = km.ackermann_from_kinematics(FL, FR, 0.01, 1.55, tr_), km.ackermann_from_kinematics(FL, FR, -0.01, 1.55, tr_)
check("TC-KIN-123: Ackermann da geometria: curva para a direita e para a esquerda dão o mesmo % (geometria simétrica); roda interna esterça mais",
      akR["turn"] == "direita" and akL["turn"] == "esquerda" and abs(akR["ackermann_percent"] - akL["ackermann_percent"]) < 1e-6
      and akR["delta_inner_deg"] > akR["delta_outer_deg"], f"%Ack={akR['ackermann_percent']:.2f} (SINTÉTICO)")

# ---- TC-KIN-124: relação de direção ----
check("TC-KIN-124a: SR total (média das duas rodas, SAE J670 9.4.6) == SR por roda na geometria simétrica, no centro",
      abs(km.steering_ratio_overall(FL, FR, 0.06) - steering_ratio(FL, 0.06)) < 1e-6)
sr_grad = 360.0 * 0.10 / (0.001 * math.degrees(1.0))        # gradiente no centro do caso analítico do TC-KIN-109 (e = 0,10 m)
check("TC-KIN-124b: aproximação do Milliken p. 718, SR = 360/asin(c/braço): tende ao gradiente no centro quando c -> 0 (c = 1 mm, braço = 0,10 m)",
      abs(km.steering_ratio_rack_approx(0.001, 0.10) / sr_grad - 1) < 1e-4, f"{km.steering_ratio_rack_approx(0.001, 0.10):.2f} vs {sr_grad:.2f}")

# ---- TC-KIN-125: ride steer (Milliken 19.4) ----
rs_pl = km.ride_steer(Cpl, TR)
check("TC-KIN-125a: mecanismo plano com barra compatível: ride steer nulo (inclinação e curvatura)",
      abs(rs_pl["slope_deg_per_mm"]) < 1e-8 and abs(rs_pl["quad_deg_per_mm2"]) < 1e-10)
rs_fl = km.ride_steer(FL, TR)
toe_fd = (sweep(FL, [1e-4])[0][1]["toe_deg"] - sweep(FL, [-1e-4])[0][1]["toe_deg"]) / 0.2
check("TC-KIN-125b: sintético: inclinação do ride steer no curso zero == diferença central do toe (°/mm)",
      abs(rs_fl["slope_deg_per_mm"] - toe_fd) < 1e-6, f"{rs_fl['slope_deg_per_mm']:.5f} °/mm (SINTÉTICO)")

# ---- TC-KIN-126: roll steer (Gillespie p. 220, eq. 6-57) ----
eps_f = km.roll_steer_coefficient(FL, FR, tr_)
b_rad = math.radians(rs_fl["slope_deg_per_mm"] * 1e3)        # rad de toe por m de curso
check("TC-KIN-126a: eixo simétrico e linear: ε = b·t/2 (b = toe-out por curso); toe-in em bump -> ε < 0 (rolagem esterça para dentro da curva)",
      abs(eps_f - b_rad * tr_ / 2) < 1e-4 * abs(eps_f) and eps_f < 0, f"ε={eps_f:.5f} °/°")
check("TC-KIN-126b: K_roll steer = (ε_f − ε_r)·∂φ/∂a_y: linear; ε_f > ε_r -> subesterço (K > 0)",
      km.roll_steer_understeer_deg_per_g(0.1, 0.0, 2.0) > 0 and abs(km.roll_steer_understeer_deg_per_g(0.1, 0.05, 2.0) - 0.1) < 1e-12
      and km.roll_steer_understeer_deg_per_g(0.0, 0.1, 2.0) < 0)

# ---- TC-KIN-127: efeitos do esterço (Milliken 19.1) ----
eL, eR = km.steer_effects(FL, -10.0), km.steer_effects(FR, -10.0)  # curva para a direita: FL externa, FR interna
check("TC-KIN-127a: caster positivo (sintético): roda externa ganha camber negativo e a interna positivo; elevação diferente nos dois lados (peso diagonal)",
      eL["yaw_deg"] < 0 and eR["yaw_deg"] < 0 and eL["dcamber_deg"] < 0 and eR["dcamber_deg"] > 0 and abs(eL["lift_m"] - eR["lift_m"]) > 1e-4,
      f"Δγ ext={eL['dcamber_deg']:.3f}° int={eR['dcamber_deg']:.3f}°; elevação ext={eL['lift_m']*1e3:.2f} int={eR['lift_m']*1e3:.2f} mm")
lift_p, lift_n = km.steer_effects(Cpl, 10.0)["lift_m"], km.steer_effects(Cpl, -10.0)["lift_m"]
check("TC-KIN-127b: só KPI e spindle length (caster zero, plano analítico): o carro sobe para os dois lados de esterço",
      Cpl.metrics(Cpl.solve(0.0))["caster_deg"] == 0.0 and lift_p > 0 and lift_n > 0 and abs(lift_p - lift_n) < 1e-12,
      f"{lift_p*1e3:.3f} / {lift_n*1e3:.3f} mm")

# ---- TC-KIN-128: diagnóstico da leitura literal no mecanismo plano ----
lit_pl = km.reference_literal_centers(Cpl)
check("TC-KIN-128: mecanismo plano: passo nulo e a leitura literal (eixo × plano) coincide com o trabalho virtual no RC",
      abs(lit_pl["pitch_m_per_rad"]) < 1e-8 and abs(lit_pl["rc_height_m"] - fpl["rc_height_m"]) < 1e-8,
      f"passo={lit_pl['pitch_m_per_rad']:.1e}")

# ---- TC-KIN-129: cantos traseiros sintéticos (anti-squat, RC e roll steer traseiros; usuário, 2026-10-20) ----
hs4 = load_hardpoints(os.path.join(HERE, "..", "data", "hardpoints_synthetic_4cantos_V2.0.csv"),
                      os.path.join(HERE, "..", "data", "hardpoints_synthetic_4cantos_V2.0.meta.json"))
RL_, RR_ = Corner(hs4, "RL"), Corner(hs4, "RR")
same_front = all(np.allclose(hs4.points[k].xyz, synth_hs.points[k].xyz, atol=0) and hs4.points[k].component == synth_hs.points[k].component
                 for k in synth_hs.points) and len(hs4.points) == len(synth_hs.points) + 22
worst4 = 0.0
s0r = RL_.solve(0.0)
for sol, m in sweep(RL_, TR):
    for a, b in (("LCA_OUT", "LCA_IN_F"), ("LCA_OUT", "LCA_IN_R"), ("UCA_OUT", "UCA_IN_F"), ("UCA_OUT", "UCA_IN_R"),
                 ("TIE_OUT", "TIE_IN"), ("LCA_OUT", "UCA_OUT"), ("LCA_OUT", "WHEEL_CENTER")):
        worst4 = max(worst4, abs(np.linalg.norm(RL_.pt(sol, a) - RL_.pt(sol, b)) - np.linalg.norm(RL_.pt(s0r, a) - RL_.pt(s0r, b))))
check("TC-KIN-129a: arquivo de 4 cantos: dianteiros idênticos ao sintético original; traseiros válidos (X traseiro < dianteiro) e comprimentos preservados em ±40 mm",
      same_front and worst4 < 1e-10, f"pior erro={worst4:.1e} m")
fRL, fRR = km.force_lines_vw(RL_), km.force_lines_vw(RR_)
as_vw = anti_squat_percent_signed(fRL["side_slope_wc"], 1.0, 1.55, 0.315)
piv = ic_methods_at_reference(RL_)["side"]["pivot_axes"]
as_piv = anti_squat_percent_signed(force_line_slope(piv, RL_.p0["WHEEL_CENTER"][[0, 2]]), 1.0, 1.55, 0.315)
check("TC-KIN-129b: anti-squat traseiro pela linha de força no centro da roda (motor no chassi): positivo, igual nos dois lados e "
      "perto da construção clássica pelos eixos de pivô (Gillespie p. 249) — CARACTERIZAÇÃO, SINTÉTICO",
      as_vw > 0 and abs(fRL["side_slope_wc"] - fRR["side_slope_wc"]) < 1e-9 and abs(as_vw - as_piv) < 2.0,
      f"AS linha de força={as_vw:.2f} %, eixos de pivô={as_piv:.2f} %")
tr_r = float(RL_.p0["CONTACT_PATCH"][1] - RR_.p0["CONTACT_PATCH"][1])
yr, zr = km.axle_roll_center_vw(RL_, RR_)
check("TC-KIN-129c: RC traseiro do eixo (linhas de força) no plano central e igual ao RC por canto (geometria simétrica)",
      abs(yr) < 1e-9 and abs(zr - fRL["rc_height_m"]) < 1e-9, f"RC traseiro={zr*1e3:.2f} mm")
rs_r = km.ride_steer(RL_, TR)
eps_r = km.roll_steer_coefficient(RL_, RR_, tr_r)
K_rs = km.roll_steer_understeer_deg_per_g(eps_f, eps_r, 1.0)
check("TC-KIN-129d: roll steer traseiro ε_r = b·t/2 (eixo simétrico, inclinação local) e contribuição K = (ε_f − ε_r)·∂φ/∂a_y de ponta a ponta",
      abs(eps_r - math.radians(rs_r["slope_deg_per_mm"] * 1e3) * tr_r / 2) < 1e-4 * abs(eps_r) and abs(K_rs - (eps_f - eps_r)) < 1e-12,
      f"ε_r={eps_r:.4f} °/°; K={K_rs:.4f} °/g por °/g de rolagem; curvatura do toe={rs_r['max_dev_from_linear_deg']:.3f}° (SINTÉTICO)")

# ---- TC-EQ-047/048: gradiente de camber no solo por rolagem (V4.0, inc. 2; Gillespie eq. 6-50 p. 218, exemplo p. 234) ----
g_par = km.camber_gradient_from_body(0.0, 0.0, 1.2)
check("TC-EQ-047: braços paralelos iguais (dγ_corpo/dz = 0): gradiente do eixo = 1,0, R = +1, L = −1 (Gillespie p. 234)",
      abs(g_par["eixo"] - 1.0) < 1e-12 and abs(g_par["R"] - 1.0) < 1e-12 and abs(g_par["L"] + 1.0) < 1e-12,
      f"eixo={g_par['eixo']:.6f}, R={g_par['R']:.6f}, L={g_par['L']:.6f}")
FL_, FR_ = Corner(hs4, "FL"), Corner(hs4, "FR")
tr_f = float(FL_.p0["CONTACT_PATCH"][1] - FR_.p0["CONTACT_PATCH"][1])
h_eq = 0.5 * tr_f * 1e-3   # m, mesmo passo de curso da função (dphi = 1e-3): derivadas centrais com passos diferentes diferem pela curvatura


def _dg_dz(c):
    a = sweep(c, [-h_eq, h_eq])
    return math.radians(a[1][1]["camber_deg"] - a[0][1]["camber_deg"]) / (2 * h_eq)


g_ref = km.camber_gradient_from_body(_dg_dz(FL_), _dg_dz(FR_), tr_f)
g_fun = km.camber_gradient(FL_, FR_, tr_f)
err_eq = max(abs(g_fun[k] - g_ref[k]) for k in ("L", "R", "eixo"))
check("TC-EQ-048: camber_gradient (sweep, diferença central) = camber_gradient_from_body com derivadas da sweep (erro < 1e-9) e "
      "gradiente do eixo < 1 (braço desigual reduz o camber positivo da roda externa) — SINTÉTICO",
      err_eq < 1e-9 and g_fun["eixo"] < 1.0,
      f"eixo={g_fun['eixo']:.4f} rad/rad (L={g_fun['L']:.4f}, R={g_fun['R']:.4f}); erro={err_eq:.1e} (SINTÉTICO)")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s in results if s == "PASS")
n_fail = sum(1 for _, s in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
