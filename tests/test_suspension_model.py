"""
Test Cases TC-001 a TC-010 (herdados da V1.0) + TC-SUS-V2-xxx (validação de entradas e aviso de Fz<0) do Engineering Standard V2.1, mais o piloto
end-to-end (MR -> Wheel Rate -> Natural Frequency).
Roda como script: python3 test_suspension_model_V2_1.py
"""

import math
import copy
from suspension_model import (
    VehicleConfig, static_fz_corner, longitudinal_dfz, lateral_dfz,
    combined_fz_corner, sprung_mass_total, sprung_cg_height, G,
    wheel_rate, spring_rate_from_wheel_rate, natural_frequency,
    wheel_rate_from_target_frequency, roll_stiffness_axle,
    roll_stiffness_distribution,
)

TOL = 1e-6
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def baseline_config(**overrides) -> VehicleConfig:
    """Veículo FSAE EV de referência para os testes (números plausíveis, não um setup real)."""
    base = dict(
        mass_total=250.0,
        cg_height=0.300,
        wheelbase=1.550,
        track_front=1.200,
        track_rear=1.150,
        cg_to_front=0.837,   # a  (=> Wf/W = b/L = 46%)
        cg_to_rear=0.713,    # b
        unsprung_mass_front=15.0,
        unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230,
        unsprung_cg_height_rear=0.230,
        roll_center_front=0.030,
        roll_center_rear=0.050,
        roll_stiffness_front=20826.4,
        roll_stiffness_rear=26450.0,
    )
    base.update(overrides)
    return VehicleConfig(**base)


# ---------------- TC-001 : a_y = 0 ----------------
cfg = baseline_config()
lat = lateral_dfz(cfg, ay=0.0)
check("TC-001a: ay=0 -> dFz_front_axle=0", abs(lat["front_axle"]) < TOL, f"dFzF={lat['front_axle']:.6f}")
check("TC-001b: ay=0 -> dFz_rear_axle=0", abs(lat["rear_axle"]) < TOL, f"dFzR={lat['rear_axle']:.6f}")

fz = combined_fz_corner(cfg, ax=0.0, ay=0.0)
check("TC-001c: ay=0 -> Fz_FL=Fz_FR", abs(fz["FL"] - fz["FR"]) < TOL, f"FL={fz['FL']:.3f} FR={fz['FR']:.3f}")
check("TC-001d: ay=0 -> Fz_RL=Fz_RR", abs(fz["RL"] - fz["RR"]) < TOL, f"RL={fz['RL']:.3f} RR={fz['RR']:.3f}")

# ---------------- TC-002 : a_x = 0 ----------------
long_ = longitudinal_dfz(cfg, ax=0.0)
check("TC-002: ax=0 -> dFz_long=0",
      abs(long_["front_per_corner"]) < TOL and abs(long_["rear_per_corner"]) < TOL,
      f"front={long_['front_per_corner']:.6f} rear={long_['rear_per_corner']:.6f}")

# ---------------- TC-003 : simetria em frenagem pura ----------------
fz_brake = combined_fz_corner(cfg, ax=-5.0, ay=0.0)
check("TC-003a: frenagem pura -> Fz_FL=Fz_FR", abs(fz_brake["FL"] - fz_brake["FR"]) < TOL,
      f"FL={fz_brake['FL']:.3f} FR={fz_brake['FR']:.3f}")
check("TC-003b: frenagem pura -> Fz_RL=Fz_RR", abs(fz_brake["RL"] - fz_brake["RR"]) < TOL,
      f"RL={fz_brake['RL']:.3f} RR={fz_brake['RR']:.3f}")

# ---------------- TC-004 : conservação de carga vertical ----------------
downforce = 400.0
aero_balance_f = 0.45
fz_full = combined_fz_corner(cfg, ax=-3.0, ay=8.0, downforce_total=downforce, aero_balance_front=aero_balance_f)
total_fz = sum(fz_full.values())
expected = cfg.mass_total * G + downforce
check("TC-004: sum(Fz) = W + Fz_aero", abs(total_fz - expected) < 1e-6,
      f"sum={total_fz:.4f} expected={expected:.4f}")

# ---------------- TC-005 : conservação do momento lateral (Milliken) ----------------
ay_test = 1.2 * G
lat2 = lateral_dfz(cfg, ay=ay_test)
lhs = cfg.track_front * lat2["front_axle"] + cfg.track_rear * lat2["rear_axle"]
rhs = cfg.mass_total * ay_test * cfg.cg_height
check("TC-005: t_F*dFzF + t_R*dFzR = m*ay*h_CG", abs(lhs - rhs) < 1e-6,
      f"lhs={lhs:.4f} rhs={rhs:.4f} (dFzF={lat2['front_axle']:.2f}N, dFzR={lat2['rear_axle']:.2f}N)")

# ---------------- TC-006 : distribuição de rigidez de rolagem ----------------
total_kphi = cfg.roll_stiffness_front + cfg.roll_stiffness_rear
cfg_stiffer_front = baseline_config(
    roll_stiffness_front=total_kphi * 0.60,
    roll_stiffness_rear=total_kphi * 0.40,
)
lat_stiffer_front = lateral_dfz(cfg_stiffer_front, ay=ay_test)
check(
    "TC-006: mais rigidez dianteira (mesmo total) -> dFzF sobe, dFzR desce",
    lat_stiffer_front["front_axle"] > lat2["front_axle"] and lat_stiffer_front["rear_axle"] < lat2["rear_axle"],
    f"antes: F={lat2['front_axle']:.2f} R={lat2['rear_axle']:.2f} | "
    f"depois: F={lat_stiffer_front['front_axle']:.2f} R={lat_stiffer_front['rear_axle']:.2f}"
)

# ---------------- TC-007 : RC=0 remove parcela geométrica ----------------
cfg_rc0 = baseline_config(roll_center_front=0.0, roll_center_rear=0.0)
lat_rc0 = lateral_dfz(cfg_rc0, ay=ay_test)
ms = sprung_mass_total(cfg_rc0)
hs = sprung_cg_height(cfg_rc0)
lam = roll_stiffness_distribution(cfg_rc0.roll_stiffness_front, cfg_rc0.roll_stiffness_rear)
expected_F_elastic_only = (ay_test / cfg_rc0.track_front) * (lam["lambda_f"] * ms * hs
                                                              + cfg_rc0.unsprung_mass_front * cfg_rc0.unsprung_cg_height_front)
check("TC-007: z_F=z_R=0 -> parcela geométrica desaparece",
      abs(lat_rc0["front_axle"] - expected_F_elastic_only) < TOL,
      f"calc={lat_rc0['front_axle']:.4f} esperado={expected_F_elastic_only:.4f}")

# ---------------- TC-008 : massa não-suspensa = 0 ----------------
cfg_no_unsprung = baseline_config(unsprung_mass_front=0.0, unsprung_mass_rear=0.0)
lat_no_unsprung = lateral_dfz(cfg_no_unsprung, ay=ay_test)
ms2 = sprung_mass_total(cfg_no_unsprung)
hs2 = sprung_cg_height(cfg_no_unsprung)
a, b, L = cfg_no_unsprung.cg_to_front, cfg_no_unsprung.cg_to_rear, cfg_no_unsprung.wheelbase
zs2 = (b / L) * cfg_no_unsprung.roll_center_front + (a / L) * cfg_no_unsprung.roll_center_rear
lam2 = roll_stiffness_distribution(cfg_no_unsprung.roll_stiffness_front, cfg_no_unsprung.roll_stiffness_rear)
expected_F_no_unsprung = (ay_test / cfg_no_unsprung.track_front) * (
    lam2["lambda_f"] * ms2 * (hs2 - zs2) + (b / L) * ms2 * cfg_no_unsprung.roll_center_front
)
check("TC-008: massa não-suspensa=0 -> parcela correspondente desaparece",
      abs(lat_no_unsprung["front_axle"] - expected_F_no_unsprung) < TOL,
      f"calc={lat_no_unsprung['front_axle']:.4f} esperado={expected_F_no_unsprung:.4f}")

# ---------------- TC-009 : MR=1 -> Kw=Ks ----------------
ks_test = 40000.0
kw_test = wheel_rate(ks_test, mr_wheel_spring=1.0)
check("TC-009: MR=1 -> Kw=Ks", abs(kw_test - ks_test) < TOL, f"Kw={kw_test}")

# ---------------- TC-010 : cálculo inverso de frequência ----------------
f_target = 2.5  # Hz
m_corner = 30.0  # kg
kw_from_target = wheel_rate_from_target_frequency(f_target, m_corner)
f_check = natural_frequency(kw_from_target, m_corner)
check("TC-010: cálculo inverso retorna exatamente f_target", abs(f_check - f_target) < 1e-9,
      f"f_target={f_target} f_check={f_check:.9f}")

# ---------------- Piloto end-to-end: MR -> Wheel Rate -> Natural Frequency ----------------
print("\n--- Piloto end-to-end (MR -> Wheel Rate -> Natural Frequency) ---")
MR = 0.8
Ks_mm = 100.0       # N/mm
ms_pilot = 50.0     # kg

Ks_m = Ks_mm * 1000.0  # N/m
Kw = wheel_rate(Ks_m, MR)
fn = natural_frequency(Kw, ms_pilot)
print(f"MR={MR}, Ks={Ks_mm} N/mm, ms={ms_pilot} kg")
print(f"Kw calculado = {Kw:.4f} N/m ({Kw/1000:.4f} N/mm)")
print(f"fn calculado = {fn:.4f} Hz  (esperado ~8.90 Hz)")
check("Piloto: fn bate com o valor verificado manualmente na especificação",
      abs(fn - 8.90) < 0.01, f"fn={fn:.4f}")

# Design Mode: inverte a partir de uma frequência-alvo
f_target_pilot = fn  # deve fechar o ciclo exatamente
Kw_design = wheel_rate_from_target_frequency(f_target_pilot, ms_pilot)
Ks_design = spring_rate_from_wheel_rate(Kw_design, MR)
check("Piloto Design Mode: ciclo fechado (Analysis -> Design -> mesmo Ks)",
      abs(Ks_design - Ks_m) < 1e-6, f"Ks original={Ks_m} Ks recalculado={Ks_design:.6f}")


# =====================================================================
# V2.0 — validação de entradas (Guide D.2) e aviso de Fz<0 (SUS-104, Guide D.4)
# =====================================================================
import warnings
import suspension_model as sm


def raises(fn, exc=ValueError, needle=None):
    try:
        fn()
        return False
    except exc as e:
        return needle is None or needle in str(e)


check("TC-SUS-V2-001a: massa zero bloqueada (SUS-001)", raises(lambda: baseline_config(mass_total=0.0), needle="mass_total deve ser > 0"))
check("TC-SUS-V2-001b: L zero bloqueado (SUS-003)", raises(lambda: baseline_config(wheelbase=0.0, cg_to_front=0.0, cg_to_rear=0.0), needle="SUS-003"))
check("TC-SUS-V2-001c: track não positivo bloqueado (SUS-004/005)",
      raises(lambda: baseline_config(track_front=0.0)) and raises(lambda: baseline_config(track_rear=-1.0)))
check("TC-SUS-V2-001d: aero balance fora de [0,1] bloqueado (SUS-702)",
      raises(lambda: sm.aero_fz_corner(400.0, 1.1)) and raises(lambda: sm.aero_fz_corner(400.0, -0.1)))
check("TC-SUS-V2-001e: spring rate não positivo bloqueado (SUS-203/202)",
      raises(lambda: wheel_rate(0.0, 1.0)) and raises(lambda: wheel_rate(-5.0, 1.0)))
check("TC-SUS-V2-001f: MR não positivo bloqueado (SUS-201)", raises(lambda: wheel_rate(1000.0, 0.0)) and raises(lambda: wheel_rate(1000.0, -1.0)))
check("TC-SUS-V2-001g: NaN/inf bloqueados", raises(lambda: baseline_config(mass_total=float("nan"))) and raises(lambda: baseline_config(cg_height=float("inf"))))
check("TC-SUS-V2-001h: massas não-suspensas >= massa total bloqueadas (SUS-009)", raises(lambda: baseline_config(unsprung_mass_front=130.0, unsprung_mass_rear=120.0)))
check("TC-SUS-V2-001i: h_s <= 0 bloqueado (SUS-012)", raises(lambda: baseline_config(unsprung_cg_height_front=9.0, unsprung_cg_height_rear=9.0)))
check("TC-SUS-V2-001j: entradas válidas dos testes herdados continuam aceitas (massa não-suspensa 0, RC 0, RC negativo)",
      baseline_config(unsprung_mass_front=0.0, unsprung_mass_rear=0.0) is not None and baseline_config(roll_center_front=-0.02) is not None)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    wheel_rate(40000.0, 0.1)
check("TC-SUS-V2-002: MR muito pequeno emite SmallMotionRatioWarning (limite 0,2 é HIPÓTESE sem fonte)",
      any(issubclass(x.category, sm.SmallMotionRatioWarning) for x in w))

# Fz < 0: aviso acionável, valores inalterados
with warnings.catch_warnings():
    warnings.simplefilter("error")        # qualquer aviso vira erro: caso normal não pode avisar
    fz_ok = combined_fz_corner(cfg, ax=-3.0, ay=8.0, downforce_total=400.0, aero_balance_front=0.45)
check("TC-SUS-V2-003a: caso normal não emite aviso", min(fz_ok.values()) > 0)
ay_lift = 35.0
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    fz_lift = combined_fz_corner(cfg, ax=0.0, ay=ay_lift)
neg = [k for k, v in fz_lift.items() if v < 0]
liftw = [x for x in w if issubclass(x.category, sm.FzLiftoffWarning)]
check("TC-SUS-V2-003b: Fz<0 emite FzLiftoffWarning por canto negativo, com ação sugerida", len(neg) >= 1 and len(liftw) == len(neg)
      and all("Reduza" in str(x.message) for x in liftw), f"cantos negativos={neg}, Fz={ {k: round(v,1) for k,v in fz_lift.items()} }")
with warnings.catch_warnings():
    warnings.simplefilter("error")
    fz_nowarn = combined_fz_corner(cfg, ax=0.0, ay=ay_lift, warn=False)
check("TC-SUS-V2-003c: warn=False suprime o aviso e NÃO altera os valores (nenhum clamp silencioso)", all(abs(fz_nowarn[k] - fz_lift[k]) < 1e-12 for k in fz_lift))
check("TC-SUS-V2-003d: Fz == 0 é fronteira válida (sem aviso); Fz<0 gera registro", sm.fz_plausibility({"FL": 0.0, "FR": 100.0}) == []
      and len(sm.fz_plausibility({"FL": -0.001})) == 1)
tot = sum(fz_lift.values())
check("TC-SUS-V2-003e: conservação ΣFz = W continua valendo mesmo com Fz<0 (superposição linear)", abs(tot - cfg.mass_total * G) < 1e-6, f"ΣFz={tot:.4f}")

# Regressão contra a V1.0 (se o arquivo estiver em tests/regressao/): mesmos valores para entradas válidas
try:
    import importlib, os, sys
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "regressao"))  # EDR-043: V1.0 congelada, no fim da busca
    v1 = importlib.import_module("suspension_model_V1_0")
except ImportError:
    v1 = None
if v1 is not None:
    base = dict(mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
                cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
                unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
                roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0)
    c1, c2 = v1.VehicleConfig(**base), sm.VehicleConfig(**base)
    dev = 0.0
    for ax_, ay_ in [(0, 0), (-5, 0), (3, 4), (-3, 8), (0, 11)]:
        a, b = v1.combined_fz_corner(c1, ax_, ay_, 300.0, 0.4), sm.combined_fz_corner(c2, ax_, ay_, 300.0, 0.4)
        dev = max(dev, max(abs(a[k] - b[k]) for k in a))
    check("TC-SUS-V2-004: regressão — Fz combinado idêntico ao da V1.0 para entradas válidas", dev == 0.0, f"dif máx={dev:.1e}")
else:
    print("[SKIP] TC-SUS-V2-004: suspension_model_V1_0.py não encontrado em tests/regressao/")


# =====================================================================
# V2.1 — cross-check de MR e caracterização do limiar absoluto (EDR-027)
# =====================================================================
cc = sm.mr_crosscheck
r = cc(1.76)
check("TC-SUS-V21-001: sem MR geométrico/referência, o cross-check informa NOT_EXECUTED (não finge que passou)", r["status"] == "NOT_EXECUTED" and "NÃO executado" in r["reason"])
r = cc(1.76, 1.76)
check("TC-SUS-V21-002: com referência e sem tolerância -> TOLERANCE_NOT_SET (sem tolerância padrão inventada) e diferenças calculadas", r["status"] == "TOLERANCE_NOT_SET" and r["rel_diff_direct"] == 0.0)
check("TC-SUS-V21-003a: MR igual ao geométrico -> MATCH", cc(1.76, 1.76, rel_tol=0.02)["status"] == "MATCH")
r = cc(1.0 / 1.76, 1.76, rel_tol=0.02)
check("TC-SUS-V21-003b: MR invertido (0,568 contra 1,76) -> INVERSION_SUSPECTED, com ressalva de investigação", r["status"] == "INVERSION_SUSPECTED" and "investigar" in r["reason"].lower(), f"direto={r['rel_diff_direct']:.3f} se invertido={r['rel_diff_if_inverted']:.1e}")
check("TC-SUS-V21-003c: discrepância que NÃO é inversão (2,5 contra 1,76) -> MISMATCH, não inversão", cc(2.5, 1.76, rel_tol=0.02)["status"] == "MISMATCH")
check("TC-SUS-V21-003d: MR ≈ 1 (1,02 contra 1,0, tol 5%) -> não distingue inversão", cc(1.02, 1.0, rel_tol=0.05)["status"] == "MATCH_INVERSION_NOT_DISTINGUISHABLE")
check("TC-SUS-V21-003e: entradas inválidas bloqueadas (MR<=0, NaN, tolerância negativa)",
      raises(lambda: cc(0.0, 1.0)) and raises(lambda: cc(float("nan"), 1.0)) and raises(lambda: cc(1.0, -1.0)) and raises(lambda: cc(1.0, 1.0, rel_tol=-0.1)))
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    kw_ok = wheel_rate(49909.24, 1.76); kw_inv = wheel_rate(49909.24, 1.0 / 1.76)
check("TC-SUS-V21-004: CARACTERIZAÇÃO — limiar absoluto 0,2 não avisa na inversão 1,76->0,568 (K_w errado em ~9,6x)",
      len(w) == 0 and abs(kw_inv / kw_ok - 1.76 ** 4) < 1e-6, f"K_w={kw_ok:.0f} x {kw_inv:.0f} N/m, razão={kw_inv/kw_ok:.3f} (=1,76^4)")
try:
    import os, kinematics_model as km, hardpoints as hp
    H = os.path.dirname(os.path.abspath(__file__))
    cn = km.Corner(hp.load_hardpoints(os.path.join(H, "..", "data", "hardpoints_synthetic_V2.0.csv"), os.path.join(H, "..", "data", "hardpoints_synthetic_V2.0.meta.json")), "FL")
    mr_geo = km.motion_ratio(cn)["mr_wheel_per_spring"]
    check("TC-SUS-V21-005: ponta a ponta (MR geométrico do solver, geometria SINTÉTICA): correto -> MATCH; inverso -> INVERSION_SUSPECTED",
          cc(mr_geo, mr_geo, 1e-6)["status"] == "MATCH" and cc(1.0 / mr_geo, mr_geo, 1e-6)["status"] == "INVERSION_SUSPECTED", f"MR geométrico (sintético)={mr_geo:.4f}")
except ImportError:
    print("[SKIP] TC-SUS-V21-005: módulos kinematics_model/hardpoints não encontrados (rode após o uv sync)")
# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
