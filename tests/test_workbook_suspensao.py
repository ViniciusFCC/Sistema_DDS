"""
Teste de integração das abas de suspensão da planilha V2.5 (EDR-045 a EDR-048): Excel x Python.
Recalcula CÓPIAS pelo Excel (COM) ou pelo LibreOffice (EDR-044; recalculo_planilha.py); a entregue nunca é salva.
Uso: uv run python -X utf8 tests/test_workbook_suspensao.py [<V2_5.xlsx>]   (padrão: excel/FSAE_EV_Suspension_Fase1_V2_5.xlsx)
Namespace TC-WB25-xxx. "Passou" = Excel reproduz o suspension_model/kinematics_model (tol. 1e-9 relativa), não validação física.
"""
import math, os, random, shutil, sys, tempfile, warnings
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
import openpyxl
import suspension_model as sm
import kinematics_model as km
import recalculo_planilha as rc

MOTOR, DETALHE = rc.escolher()
if MOTOR is None:
    print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({DETALHE})"); sys.exit(3)
print(f"MOTOR: {MOTOR} ({DETALHE})")
_RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
V25 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_RAIZ, "excel", "FSAE_EV_Suspension_Fase1_V2_5.xlsx")
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


# entradas (aba, célula) e o nome usado no cálculo Python
ENTRADAS = {
    "m": ("05_VEHICLE", "B4"), "h": ("05_VEHICLE", "B5"), "L": ("05_VEHICLE", "B6"), "tF": ("05_VEHICLE", "B7"), "tR": ("05_VEHICLE", "B8"),
    "a": ("05_VEHICLE", "B9"), "b": ("05_VEHICLE", "B10"), "muF": ("05_VEHICLE", "B14"), "muR": ("05_VEHICLE", "B15"),
    "huF": ("05_VEHICLE", "B16"), "huR": ("05_VEHICLE", "B17"),
    "KsF": ("06_SUSPENSION", "B4"), "KsR": ("06_SUSPENSION", "B5"), "MRF": ("06_SUSPENSION", "B6"), "MRR": ("06_SUSPENSION", "B7"),
    "KarbF": ("06_SUSPENSION", "B10"), "KarbR": ("06_SUSPENSION", "B11"), "zF": ("06_SUSPENSION", "B14"), "zR": ("06_SUSPENSION", "B15"),
    "FBf": ("06_SUSPENSION", "B36"), "TFr": ("06_SUSPENSION", "B37"), "KTF": ("06_SUSPENSION", "B47"), "KTR": ("06_SUSPENSION", "B48"),
    "zICF": ("07_KINEMATICS", "B10"), "dxF": ("07_KINEMATICS", "B11"), "zICR": ("07_KINEMATICS", "B12"), "dxR": ("07_KINEMATICS", "B13"),
    "ax": ("08_VEHICLE_STATE", "B4"), "ay": ("08_VEHICLE_STATE", "B5"), "DF": ("08_VEHICLE_STATE", "B8"), "bal": ("08_VEHICLE_STATE", "B9"),
    "fF": ("11_DESIGN", "B4"), "fR": ("11_DESIGN", "B5"), "lam": ("11_DESIGN", "B18"),
}
SAIDAS = {   # nome -> (aba, célula)
    "msF": ("05_VEHICLE", "B25"), "msR": ("05_VEHICLE", "B26"), "a_s": ("05_VEHICLE", "B27"), "hs": ("05_VEHICLE", "B24"),
    "KwF": ("06_SUSPENSION", "B18"), "KwR": ("06_SUSPENSION", "B19"), "KphiF": ("06_SUSPENSION", "B22"), "KphiR": ("06_SUSPENSION", "B23"),
    "lamF": ("06_SUSPENSION", "B24"), "mcF": ("06_SUSPENSION", "B28"), "mcR": ("06_SUSPENSION", "B29"),
    "fnF": ("06_SUSPENSION", "B32"), "fnR": ("06_SUSPENSION", "B33"), "KRF": ("06_SUSPENSION", "B49"), "KRR": ("06_SUSPENSION", "B50"),
    "AD": ("06_SUSPENSION", "B40"), "AS": ("06_SUSPENSION", "B41"),
    "zs": ("09_LOADS", "B18"), "dFzF": ("09_LOADS", "B19"), "dFzR": ("09_LOADS", "B20"), "phi": ("09_LOADS", "B21"),
    "FL": ("09_LOADS", "B31"), "FR": ("09_LOADS", "B32"), "RL": ("09_LOADS", "B33"), "RR": ("09_LOADS", "B34"),
    "KwFd": ("11_DESIGN", "B8"), "KwRd": ("11_DESIGN", "B9"), "KsFd": ("11_DESIGN", "B10"), "KsRd": ("11_DESIGN", "B11"),
    "KphiFd": ("11_DESIGN", "B19"), "KarbFd": ("11_DESIGN", "B20"), "tc005": ("13_VALIDATION", "B6"),
}


def python_ref(x):
    """Mesmo cálculo pelos módulos Python (fonte da verdade do MODEL)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        KwF, KwR = sm.wheel_rate(x["KsF"], x["MRF"]), sm.wheel_rate(x["KsR"], x["MRR"])
    KphiF = sm.roll_stiffness_axle(KwF, x["tF"], x["KarbF"], x["KTF"])
    KphiR = sm.roll_stiffness_axle(KwR, x["tR"], x["KarbR"], x["KTR"])
    cfg = sm.VehicleConfig(mass_total=x["m"], cg_height=x["h"], wheelbase=x["L"], track_front=x["tF"], track_rear=x["tR"],
                           cg_to_front=x["a"], cg_to_rear=x["b"], unsprung_mass_front=x["muF"], unsprung_mass_rear=x["muR"],
                           unsprung_cg_height_front=x["huF"], unsprung_cg_height_rear=x["huR"], roll_center_front=x["zF"],
                           roll_center_rear=x["zR"], roll_stiffness_front=KphiF, roll_stiffness_rear=KphiR)
    ax_ = sm.sprung_mass_axle(cfg); mc = sm.sprung_mass_per_corner(cfg); lat = sm.lateral_dfz(cfg, x["ay"])
    fz = sm.combined_fz_corner(cfg, x["ax"], x["ay"], x["DF"], x["bal"], warn=False)
    KRF, KRR = sm.ride_rate(KwF, x["KTF"]), sm.ride_rate(KwR, x["KTR"])
    KwFd = sm.wheel_rate_from_target_frequency(x["fF"], mc["FL"], x["KTF"])
    KwRd = sm.wheel_rate_from_target_frequency(x["fR"], mc["RL"], x["KTR"])
    KphiFd = x["lam"] / (1 - x["lam"]) * KphiR
    ms = sm.sprung_mass_total(cfg)
    return {
        "msF": ax_["front"], "msR": ax_["rear"], "a_s": sm.sprung_cg_to_front(cfg), "hs": sm.sprung_cg_height(cfg),
        "KwF": KwF, "KwR": KwR, "KphiF": KphiF, "KphiR": KphiR, "lamF": KphiF / (KphiF + KphiR), "mcF": mc["FL"], "mcR": mc["RL"],
        "fnF": sm.natural_frequency(KRF, mc["FL"]), "fnR": sm.natural_frequency(KRR, mc["RL"]), "KRF": KRF, "KRR": KRR,
        "AD": km.anti_dive_percent_signed(x["zICF"] / x["dxF"], x["FBf"], x["L"], x["h"]),
        "AS": km.anti_squat_percent_signed((x["zICR"] - x["huR"]) / x["dxR"], x["TFr"], x["L"], x["h"]),
        "zs": lat["z_s"], "dFzF": lat["front_axle"], "dFzR": lat["rear_axle"], "phi": lat["roll_angle_rad"], **fz,
        "KwFd": KwFd, "KwRd": KwRd, "KsFd": sm.spring_rate_from_wheel_rate(KwFd, x["MRF"]), "KsRd": sm.spring_rate_from_wheel_rate(KwRd, x["MRR"]),
        "KphiFd": KphiFd, "KarbFd": sm.arb_required(KphiFd, KwF, x["tF"], x["KTF"]),
        "tc005": x["tF"] * lat["front_axle"] + x["tR"] * lat["rear_axle"] - x["m"] * x["ay"] * x["h"] - ms * 9.81 * lat["h2"] * lat["roll_angle_rad"],
    }


def scenario(mods):
    d = tempfile.mkdtemp(); f = os.path.join(d, "t.xlsx"); shutil.copy(V25, f)
    wb = openpyxl.load_workbook(f)
    for (aba, cel), val in mods.items():
        wb[aba][cel].value = val
    wb.save(f)
    info = rc.recalcular(f, MOTOR, 120)
    return info, openpyxl.load_workbook(f, data_only=True)


def ler_entradas(wbv):
    return {k: wbv[a][c].value for k, (a, c) in ENTRADAS.items()}


def comparar(wbv, x):
    ref = python_ref(x)
    pior, ruins = 0.0, []
    for k, (a, c) in SAIDAS.items():
        ev, pv = wbv[a][c].value, ref[k]
        if not isinstance(ev, (int, float)):
            ruins.append((k, ev)); continue
        escala = 1.0 if k == "tc005" else max(1.0, abs(pv))
        pior = max(pior, abs(ev - pv) / escala)
    return pior, ruins


# ---------- base ----------
info, wbv = scenario({})
check("TC-WB25-001: recálculo da V2.5 sem erros de fórmula (#REF!, #VALUE!, …)", info["total_errors"] == 0, f"fórmulas={info['total_formulas']}")
x0 = ler_entradas(wbv)
pior, ruins = comparar(wbv, x0)
check("TC-WB25-002: base — 05/06/09/11/13 do Excel == suspension_model/kinematics_model (33 saídas, tol. 1e-9)", pior < 1e-9 and not ruins, f"pior dif={pior:.2e}; {ruins}")
v = wbv["13_VALIDATION"]
check("TC-WB25-003: 13_VALIDATION: TC-004, TC-005 (com termo gravitacional) e λ_f+λ_r=1 PASS",
      v["B5"].value == "PASS" and v["B7"].value == "PASS" and abs(v["B8"].value - 1) < 1e-12, f"TC-005 resíduo={v['B6'].value:.2e}")
check("TC-WB25-004: K_T de 06_SUSPENSION é o VERTICAL_STIFFNESS do .tir provisório (120312 N/m) e está rotulado PROVISÓRIO",
      x0["KTF"] == x0["KTR"] == 120312.0 and "PROVISÓRIO" in str(wbv["06_SUSPENSION"]["A46"].value))

# ---------- perturbações aleatórias de todas as entradas ----------
rnd = random.Random(20261019)
pior_all, ruins_all = 0.0, []
for s in range(3):
    x = {k: (v_ * rnd.uniform(0.85, 1.15) if isinstance(v_, (int, float)) else v_) for k, v_ in x0.items()}
    x["b"] = x["L"] - x["a"]                     # SUS-006: a + b = L
    x["ay"] = x0["ay"] * rnd.choice((-1, 1)) * rnd.uniform(0.3, 1.1); x["ax"] = x0["ax"] * rnd.uniform(-1, 1)
    x["bal"] = min(max(x["bal"], 0.0), 1.0); x["lam"] = min(max(x["lam"], 0.3), 0.7)
    mods = {ENTRADAS[k]: x[k] for k in x if ENTRADAS[k] != ("07_KINEMATICS", "B14")}
    info, wbv = scenario(mods)
    x["huR"] = wbv["05_VEHICLE"]["B17"].value
    p_, r_ = comparar(wbv, ler_entradas(wbv))
    pior_all = max(pior_all, p_); ruins_all += r_ + ([("erros", info["total_errors"])] if info["total_errors"] else [])
check("TC-WB25-005: 3 cenários com TODAS as entradas perturbadas (±15 %, a_y com os dois sinais): Excel == Python",
      pior_all < 1e-9 and not ruins_all, f"pior dif={pior_all:.2e}; {ruins_all}")

# ---------- casos-limite ----------
info, wbv = scenario({("08_VEHICLE_STATE", "B5"): 0.0})
l = wbv["09_LOADS"]
check("TC-WB25-006: a_y = 0 -> φ = 0 e ΔFz lateral = 0 nos dois eixos", l["B21"].value == 0 and l["B19"].value == 0 and l["B20"].value == 0)
info, wbv = scenario({("06_SUSPENSION", "B47"): 1e15, ("06_SUSPENSION", "B48"): 1e15})
s_ = wbv["06_SUSPENSION"]
kphi_rig = s_["B20"].value + s_["B10"].value
check("TC-WB25-007: pneu quase rígido (K_T = 1e15) recupera K_φ = K_W·t²/2 + K_ARB e K_R = K_W (forma da V2.4)",
      abs(s_["B22"].value / kphi_rig - 1) < 1e-9 and abs(s_["B49"].value / s_["B18"].value - 1) < 1e-9)
info, wbv = scenario({("06_SUSPENSION", "B4"): 100.0, ("06_SUSPENSION", "B5"): 100.0,
                      ("06_SUSPENSION", "B10"): 0.0, ("06_SUSPENSION", "B11"): 0.0})
check("TC-WB25-008: rigidez de rolagem abaixo de m_s·g·h2 -> φ = 'N/A - instabilidade…' e ΔFz lateral 'N/A' (sem número falso)",
      str(wbv["09_LOADS"]["B21"].value).startswith("N/A - instabilidade") and wbv["09_LOADS"]["B19"].value == "N/A")
info, wbv = scenario({("07_KINEMATICS", "B11"): 2.5})
check("TC-WB25-009: IC lateral dianteiro À FRENTE do contact patch -> anti-dive negativo (pro-dive, Milliken p. 620)",
      wbv["06_SUSPENSION"]["B40"].value < 0, f"AD={wbv['06_SUSPENSION']['B40'].value:.2f} %")

print("\n--- Resumo ---"); p = sum(1 for _, s in results if s == "PASS"); f = len(results) - p
print(f"{p} PASS, {f} FAIL, de {len(results)} testes")
sys.exit(1 if f else 0)
