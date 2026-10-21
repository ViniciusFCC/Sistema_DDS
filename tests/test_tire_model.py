"""
Test Cases do tire_model_V2_4.py (namespace TC-TIRE-xxx). python3 test_tire_model_V2_4.py
Dataset: .tir TTC PROVISÓRIO (não necessariamente o pneu real). Verificação = limites analíticos e invariantes;
NÃO há comparação com implementação independente nem com OptimumTire (não disponíveis) -> Validation = NOT_VALIDATED.
"""
import math, os, tempfile, shutil
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name  # tudo que o teste cria em temp fica aqui e é apagado no fim
import tire_model as t

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
LD = lambda path, ax="ISO_TYDEX": t.load_dataset(path, source_axis_system=ax)   # EDR-039 (revisão de 2026-10-19): o .tir PAC2002 está no eixo W do TYDEX
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def raises(fn, exc):
    try:
        fn(); return False
    except exc:
        return True


ds = LD(TIR); p = ds.p
check("TC-TIRE-001a: parser lê valores exatos (inclui notação científica)", p["PKY1"] == -58.2664 and abs(p["RVY4"] - 2.75688e-05) < 1e-15 and p["FNOMIN"] == 1054 and p["FZMAX"] == 1521)
check("TC-TIRE-001b: metadados: PAC2002, lado Right, unidades SI/rad", ds.strings["PROPERTY_FILE_FORMAT"] == "PAC2002" and ds.side == "Right" and ds.strings["ANGLE"] == "radians")

# --- limites analíticos (independem da implementação das equações de combinação) ---
fz = 700.0
_, ix = t.pure_fx0(p, fz, 0.0, 0.0)
h = 1e-6
k0 = -ix["SHx"]
slope = (t.pure_fx0(p, fz, 0.0, k0 + h)[0] - t.pure_fx0(p, fz, 0.0, k0 - h)[0]) / (2 * h)
check("TC-TIRE-002a: dFx0/dκ em κx=0 == Kx = BCD (limite analítico)", abs(slope / ix["Kx"] - 1) < 1e-5, f"{slope:.1f} vs {ix['Kx']:.1f}")
_, iy = t.pure_fy0(p, fz, 0.0, 0.0)
a0 = -iy["SHy"]
slope = (t.pure_fy0(p, fz, a0 + h, 0.0)[0] - t.pure_fy0(p, fz, a0 - h, 0.0)[0]) / (2 * h)
check("TC-TIRE-002b: dFy0/dα em αy=0 == Ky = BCD (limite analítico)", abs(slope / iy["Ky"] - 1) < 1e-5, f"{slope:.1f} vs {iy['Ky']:.1f}")
fzn = p["FNOMIN"]
_, ixn = t.pure_fx0(p, fzn, 0.0, 0.0); _, iyn = t.pure_fy0(p, fzn, 0.0, 0.0)
check("TC-TIRE-002c: Fz=FNOMIN, γ=0 -> μx=PDX1 e μy=PDY1 (dfz=0)", abs(ixn["Dx"] / fzn - p["PDX1"]) < 1e-12 and abs(iyn["muy"] - p["PDY1"]) < 1e-12)
ks = [i / 1000 * 0.25 for i in range(-1000, 1001)]
dev = [t.pure_fx0(p, fz, 0.0, k)[0] - ix["SVx"] for k in ks]
check("TC-TIRE-002d: |Fx0 - SVx| <= |Dx| e atinge >= 90% de |Dx| na faixa de κ", max(abs(d) for d in dev) <= abs(ix["Dx"]) * (1 + 1e-9) and max(abs(d) for d in dev) >= 0.9 * abs(ix["Dx"]),
      f"pico={max(abs(d) for d in dev):.1f} Dx={ix['Dx']:.1f}")
als = [i / 1000 * p["ALPMAX"] for i in range(-1000, 1001)]
devy = [t.pure_fy0(p, fz, a, 0.0)[0] - iy["SVy"] for a in als]
check("TC-TIRE-002e: |Fy0 - SVy| <= |Dy| e atinge >= 90% de |Dy| na faixa de α", max(abs(d) for d in devy) <= abs(iy["Dy"]) * (1 + 1e-9) and max(abs(d) for d in devy) >= 0.9 * abs(iy["Dy"]),
      f"pico={max(abs(d) for d in devy):.1f} Dy={iy['Dy']:.1f}")

# --- combinação ---
fx_a, fy_a, ia = t.combined_forces(ds, fz, 0.0, 0.0, 0.10)
check("TC-TIRE-003a: α=0 -> Gxα=1 e Fx combinado == Fx0", abs(ia["Gxa"] - 1) < 1e-12 and abs(fx_a - ia["fx0"]) < 1e-9)
fx_b, fy_b, ib = t.combined_forces(ds, fz, math.radians(4), 0.0, 0.0)
check("TC-TIRE-003b: κ=0 -> SVyκ=0 e Gyκ=1 -> Fy combinado == Fy0", abs(ib["SVyk"]) < 1e-12 and abs(ib["Gyk"] - 1) < 1e-12 and abs(fy_b - ib["fy0"]) < 1e-9)
fx_c, fy_c, ic = t.combined_forces(ds, fz, math.radians(4), 0.0, 0.10)
fx_0, _, i0 = t.combined_forces(ds, fz, 0.0, 0.0, 0.10)
_, fy_0, i1 = t.combined_forces(ds, fz, math.radians(4), 0.0, 0.0)
check("TC-TIRE-003c: combinação REDUZ a força: |Fx(κ,α)|<|Fx(κ,0)| e |Fy(α,κ)|<|Fy(α,0)| para α=4°, κ=0,1", abs(fx_c) < abs(fx_0) and abs(fy_c) < abs(fy_0), f"Fx {fx_c:.0f}<{fx_0:.0f}; Fy {fy_c:.0f}<{fy_0:.0f}")
check("TC-TIRE-003d: elipse de atrito: sqrt((Fx/Fx0max)²+(Fy/Fy0max)²) <= ~1,1 (plausibilidade, não limite exato)",
      math.hypot(fx_c / abs(ix["Dx"]), fy_c / abs(iy["Dy"])) <= 1.1, f"{math.hypot(fx_c / abs(ix['Dx']), fy_c / abs(iy['Dy'])):.3f}")

# --- sinais empíricos (convenção do arquivo; H3) ---
sr = t.sign_report(ds)
check("TC-TIRE-004a: CARACTERIZAÇÃO — Fy < 0 para α>0 (cornering stiffness negativa; compatível com ISO), Fy < 0 para camber>0", sr["Fy(alpha=+4deg, gamma=0, kappa=0)"] < 0 and sr["Fy(alpha=0, gamma=+3deg, kappa=0)"] < 0, str({k: round(v, 1) for k, v in sr.items()}))
check("TC-TIRE-004b: CARACTERIZAÇÃO — Fx > 0 para κ>0 e Fx < 0 para κ<0 (κ=-1 = roda travada em frenagem, ISO)", sr["Fx(kappa=+0.10)"] > 0 and sr["Fx(kappa=-0.10)"] < 0)

# --- espelhamento por lado (H4) ---
args = (700.0, math.radians(3), math.radians(1.5), 0.05)
fxl, fyl, _ = t.wheel_forces(ds, "FL", *args)
fxr, fyr, _ = t.wheel_forces(ds, "FR", args[0], -args[1], args[2], args[3])
check("TC-TIRE-005a: Fy_FL(α) = -Fy_FR(-α) e Fx igual (mesmo γ do projeto, mesmo κ)", abs(fyl + fyr) < 1e-9 and abs(fxl - fxr) < 1e-9)
fxl2, fyl2, _ = t.wheel_forces(ds, "RL", *args); fxr2, fyr2, _ = t.wheel_forces(ds, "RR", *args)
check("TC-TIRE-005b: mesmo α>0 (ISO) -> rodas esquerda e direita geram Fy de mesmo sinal (ambas se opõem à velocidade lateral)", fyl2 * fyr2 > 0)
check("TC-TIRE-005c: canto inválido bloqueado", raises(lambda: t.wheel_forces(ds, "XX", *args), ValueError))

# --- guardas de faixa ---
check("TC-TIRE-006a: Fz=0 bloqueado (liftoff)", raises(lambda: t.combined_forces(ds, 0.0, 0, 0, 0), t.TireRangeError))
check("TC-TIRE-006b: Fz<0 bloqueado", raises(lambda: t.combined_forces(ds, -50.0, 0, 0, 0), t.TireRangeError))
check("TC-TIRE-006c: 0<Fz<FZMIN bloqueado; Fz>FZMAX bloqueado", raises(lambda: t.combined_forces(ds, 50.0, 0, 0, 0), t.TireRangeError) and raises(lambda: t.combined_forces(ds, 1600.0, 0, 0, 0), t.TireRangeError))
check("TC-TIRE-006d: limites exatos aceitos (FZMIN, FZMAX, ±ALPMAX, ±CAMMAX, ±KPUMAX); fora por 1e-6 bloqueado",
      t.in_range(ds, 100, p["ALPMAX"], p["CAMMAX"], p["KPUMAX"]) == [] and t.in_range(ds, 1521, p["ALPMIN"], p["CAMMIN"], p["KPUMIN"]) == []
      and t.in_range(ds, 700, p["ALPMAX"] + 1e-6, 0, 0) != [] and t.in_range(ds, 700, 0, 0, p["KPUMAX"] + 1e-6) != [])
check("TC-TIRE-006e: α em graus passado como rad (4 em vez de 0,07) é bloqueado", raises(lambda: t.combined_forces(ds, 700, 4.0, 0, 0), t.TireRangeError))
check("TC-TIRE-006f: NaN bloqueado", raises(lambda: t.combined_forces(ds, 700, float("nan"), 0, 0), t.TireRangeError))

# --- SUS-503 ---
check("TC-TIRE-007a: μ_eff(3,4;5)=1", abs(t.mu_effective(3, 4, 5) - 1) < 1e-15)
check("TC-TIRE-007b: μ_eff com Fz<=0 bloqueado", raises(lambda: t.mu_effective(1, 1, 0.0), ValueError) and raises(lambda: t.mu_effective(1, 1, -5.0), ValueError))
fxm, fym, _ = t.combined_forces(ds, 564.0, math.radians(4), 0.0, 0.0)
check("TC-TIRE-007c: μ_eff em α=4°, Fz=564 N dentro de (0, 3,5) — plausibilidade, não validação", 0 < t.mu_effective(fxm, fym, 564.0) < 3.5, f"μ={t.mu_effective(fxm, fym, 564.0):.3f}")

# --- loader: arquivos inválidos ---
def variant(edit):
    d = tempfile.mkdtemp(); f = os.path.join(d, "v.tir")
    txt = open(TIR, encoding="utf-8").read()
    open(f, "w", encoding="utf-8").write(edit(txt)); return f
check("TC-TIRE-008a: IP != IP_NOM rejeitado", raises(lambda: LD(variant(lambda s: s.replace("IP                       =  82737 ", "IP                       =  90000 ", 1))), t.TireDataError))
check("TC-TIRE-008b: PP* != 0 rejeitado", raises(lambda: LD(variant(lambda s: s.replace("PPY1                     =  0 ", "PPY1                     =  0.1 ", 1))), t.TireDataError))
check("TC-TIRE-008c: coeficiente ausente rejeitado e nomeado", raises(lambda: LD(variant(lambda s: s.replace("PKY1 ", "XKY1 ", 1))), t.TireDataError))
check("TC-TIRE-008d: unidade angular em graus rejeitada", raises(lambda: LD(variant(lambda s: s.replace("'radians'", "'degrees'", 1))), t.TireDataError))
check("TC-TIRE-008e: TYRESIDE desconhecido rejeitado", raises(lambda: LD(variant(lambda s: s.replace("'Right'                  $Mounted", "'Both'                  $Mounted", 1))), t.TireDataError))
check("TC-TIRE-008f: formato diferente de PAC2002 rejeitado (ex.: MF 6.2)", raises(lambda: LD(variant(lambda s: s.replace("'PAC2002'", "'MF_62'", 1))), t.TireDataError))


# --- TC-TIRE-009: segunda transcrição das equações, escrita à parte (notação de Pacejka), comparada em pontos aleatórios ---
import random
def ref_forces(P, Fz, al, ga, ka):
    """Transcrição independente (estrutura diferente do módulo). Mesmas equações-fonte (H1): NÃO é validação física."""
    atan, sin, cos, exp = math.atan, math.sin, math.cos, math.exp
    sg = lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
    Fz0 = P["FNOMIN"] * P["LFZO"]; d = Fz / Fz0 - 1.0
    # Fx0
    gx = ga * P["LGAX"]; Shx = (P["PHX1"] + P["PHX2"] * d) * P["LHX"]; kx = ka + Shx
    Cx = P["PCX1"] * P["LCX"]; Dx = (P["PDX1"] + P["PDX2"] * d) * (1 - P["PDX3"] * gx ** 2) * P["LMUX"] * Fz
    Ex = (P["PEX1"] + P["PEX2"] * d + P["PEX3"] * d * d) * (1 - P["PEX4"] * sg(kx)) * P["LEX"]; Ex = Ex if Ex < 1 else 1.0
    Kx = Fz * (P["PKX1"] + P["PKX2"] * d) * exp(P["PKX3"] * d) * P["LKX"]; Bx = Kx / (Cx * Dx + 1e-6)
    Svx = Fz * (P["PVX1"] + P["PVX2"] * d) * P["LVX"] * P["LMUX"]
    u = Bx * kx; Fx0 = Dx * sin(Cx * atan(u - Ex * (u - atan(u)))) + Svx
    # Fy0
    gy = ga * P["LGAY"]
    Ky = P["PKY1"] * Fz0 * sin(2 * atan(Fz / (P["PKY2"] * Fz0))) * (1 - P["PKY3"] * abs(gy)) * P["LKY"]   # EDR-049
    Shy = (P["PHY1"] + P["PHY2"] * d) * P["LHY"] + P["PHY3"] * gy * P["LKYG"]; ay = al + Shy   # λKyγ: Adams eq. 41
    Cy = P["PCY1"] * P["LCY"]; muy = (P["PDY1"] + P["PDY2"] * d) * (1 - P["PDY3"] * gy ** 2) * P["LMUY"]; Dy = muy * Fz
    Ey = (P["PEY1"] + P["PEY2"] * d) * (1 - (P["PEY3"] + P["PEY4"] * gy) * sg(ay)) * P["LEY"]; Ey = Ey if Ey < 1 else 1.0
    By = Ky / (Cy * Dy + 1e-6)
    Svy = Fz * ((P["PVY1"] + P["PVY2"] * d) * P["LVY"] + (P["PVY3"] + P["PVY4"] * d) * gy * P["LKYG"]) * P["LMUY"]   # Adams eq. 42
    v = By * ay; Fy0 = Dy * sin(Cy * atan(v - Ey * (v - atan(v)))) + Svy
    # combinação
    Shxa = P["RHX1"]; Bxa = P["RBX1"] * cos(atan(P["RBX2"] * ka)) * P["LXAL"]; Cxa = P["RCX1"]
    Exa = P["REX1"] + P["REX2"] * d; Exa = Exa if Exa < 1 else 1.0
    H = lambda B, C, E, x: cos(C * atan(B * x - E * (B * x - atan(B * x))))
    Gxa = H(Bxa, Cxa, Exa, al + Shxa) / H(Bxa, Cxa, Exa, Shxa)
    Shyk = P["RHY1"] + P["RHY2"] * d; Byk = P["RBY1"] * cos(atan(P["RBY2"] * (al - P["RBY3"]))) * P["LYKA"]; Cyk = P["RCY1"]
    Eyk = P["REY1"] + P["REY2"] * d; Eyk = Eyk if Eyk < 1 else 1.0
    Gyk = H(Byk, Cyk, Eyk, ka + Shyk) / H(Byk, Cyk, Eyk, Shyk)
    Dvyk = muy * Fz * (P["RVY1"] + P["RVY2"] * d + P["RVY3"] * ga) * cos(atan(P["RVY4"] * al))
    Svyk = Dvyk * sin(P["RVY5"] * atan(P["RVY6"] * ka)) * P["LVYKA"]
    return Gxa * Fx0, Gyk * Fy0 + Svyk

rnd = random.Random(7)
def rand_pts(n):
    return [(rnd.uniform(100, 1521), rnd.uniform(-1, 1) * p["ALPMAX"], rnd.uniform(-1, 1) * p["CAMMAX"], rnd.uniform(-1, 1) * p["KPUMAX"]) for _ in range(n)]
dev = 0.0
for fz_, a_, g_, k_ in rand_pts(400):
    fx_m, fy_m, _ = t.combined_forces(ds, fz_, a_, g_, k_)
    fx_r, fy_r = ref_forces(p, fz_, a_, g_, k_)
    dev = max(dev, abs(fx_m - fx_r), abs(fy_m - fy_r))
check("TC-TIRE-009a: módulo == segunda transcrição independente em 400 pontos aleatórios (dataset original), dif < 1e-9 N", dev < 1e-9, f"dif máx={dev:.2e} N")
# escalas e FNOMIN/LFZO distintos de 1 (os L* do arquivo são todos 1: mutações neles seriam equivalentes sem este teste)
p2 = dict(p)
for i, k in enumerate(("LFZO", "LCX", "LMUX", "LEX", "LKX", "LHX", "LVX", "LGAX", "LCY", "LMUY", "LEY", "LKY", "LHY", "LVY", "LGAY", "LXAL", "LYKA", "LVYKA", "LKYG")):
    p2[k] = 1.0 + 0.03 * (i + 1) * (1 if i % 2 == 0 else -1)
ds2 = t.TireDataset(p=p2, strings=ds.strings)
dev2 = 0.0
for fz_, a_, g_, k_ in rand_pts(400):
    fx_m, fy_m, _ = t.combined_forces(ds2, fz_, a_, g_, k_, check_range=False)
    fx_r, fy_r = ref_forces(p2, fz_, a_, g_, k_)
    dev2 = max(dev2, abs(fx_m - fx_r), abs(fy_m - fy_r))
check("TC-TIRE-009b: idem com todos os fatores L* e LFZO ≠ 1 (distintos), dif < 1e-9 N", dev2 < 1e-9, f"dif máx={dev2:.2e} N")
sens = sum(1 for k in ("LMUX", "LKY", "LVYKA", "LYKA", "LXAL", "LVX", "LGAY", "LKYG") if abs(t.combined_forces(t.TireDataset(p={**p, k: p[k] * 1.1}, strings=ds.strings), 700, 0.05, 0.03, 0.08)[0] - t.combined_forces(ds, 700, 0.05, 0.03, 0.08)[0]) + abs(t.combined_forces(t.TireDataset(p={**p, k: p[k] * 1.1}, strings=ds.strings), 700, 0.05, 0.03, 0.08)[1] - t.combined_forces(ds, 700, 0.05, 0.03, 0.08)[1]) > 1e-9)
check("TC-TIRE-009c: sensibilidade — alterar cada L* testado muda Fx ou Fy (nenhum fator ignorado)", sens == 8, f"{sens}/8")


# --- TC-TIRE-010: sistema de eixos do arquivo (V2.4): transformação SAE_CALSPAN -> ISO, invariantes físicos ---
# O modo SAE_CALSPAN é pedido explicitamente (dsS); dsI é o modo do arquivo (ISO_TYDEX, EDR-039).
dsS = LD(TIR, "SAE_CALSPAN"); dsI = LD(TIR, "ISO_TYDEX")
import math as _m
corners = ("FL", "FR", "RL", "RR")
ok = True; det = []
for cn in corners:
    for a_deg in (3, 6, 12, -3, -6, -12):
        for dsx in (dsS, dsI):
            fy = t.wheel_forces(dsx, cn, 700.0, _m.radians(a_deg), 0.0, 0.0)[1]
            ok &= (fy * a_deg < 0)
check("TC-TIRE-010a: |α|≥3°, γ=0: Fy (ISO, projeto) tem sinal oposto a α_ISO nos 4 cantos, nos dois modos de eixo (SAE_CALSPAN e ISO_TYDEX)", ok)
ok_010b, det_010b = True, []
for nome_dx, dx in (("SAE_CALSPAN", dsS), ("ISO_TYDEX", dsI)):
    fyR = t.wheel_forces(dx, "FR", 700.0, 0.0, _m.radians(3), 0.0)[1]; fyL = t.wheel_forces(dx, "FL", 700.0, 0.0, _m.radians(3), 0.0)[1]
    fyR_n = t.wheel_forces(dx, "FR", 700.0, 0.0, _m.radians(-3), 0.0)[1]; fyL_n = t.wheel_forces(dx, "FL", 700.0, 0.0, _m.radians(-3), 0.0)[1]
    ok_010b = ok_010b and fyR < 0 and fyL > 0 and fyR_n > 0 and fyL_n < 0
    det_010b.append(f"{nome_dx}: R+={fyR:.0f} L+={fyL:.0f} R-={fyR_n:.0f} L-={fyL_n:.0f}")
check("TC-TIRE-010b: empuxo de camber aponta para o lado da inclinação: roda direita γ>0 (topo p/ direita=fora) -> Fy<0 (direita); roda esquerda γ>0 (topo p/ esquerda=fora) -> Fy>0; inverte com γ<0, nos dois modos de eixo (SAE_CALSPAN e ISO_TYDEX)",
      ok_010b, "; ".join(det_010b))
f0_file = t.combined_forces(ds, 700.0, 0.0, 0.0, 0.0)[1]
check("TC-TIRE-010c: offset de Fy em zero slip: SAE_CALSPAN -> Fy_ISO = −Fy_arquivo; ISO_TYDEX -> = +Fy_arquivo (roda direita)",
      abs(t.wheel_forces(dsS, "FR", 700.0, 0, 0, 0)[1] + f0_file) < 1e-9 and abs(t.wheel_forces(dsI, "FR", 700.0, 0, 0, 0)[1] - f0_file) < 1e-9, f"Fy_arquivo(0,0,0)={f0_file:.2f} N")
check("TC-TIRE-010d: Fx não depende do modo de eixos quando α=0 (X e κ iguais em SAE e ISO)",
      all(abs(t.wheel_forces(dsS, "FR", fz_, 0.0, g_, k_)[0] - t.wheel_forces(dsI, "FR", fz_, 0.0, g_, k_)[0]) < 1e-9 for fz_, g_, k_ in ((300, 0.0, 0.1), (700, 0.03, -0.15), (1200, -0.02, 0.2))))
psym = dict(p)
for k in ("PHY1", "PHY2", "PHY3", "PVY1", "PVY2", "PVY3", "PVY4", "PEY3", "PEY4"):
    psym[k] = 0.0
dsym_s = t.TireDataset(p=psym, strings=ds.strings, axis_system="SAE_CALSPAN"); dsym_i = t.TireDataset(p=psym, strings=ds.strings, axis_system="ISO_TYDEX")
dd = max(abs(t.wheel_forces(dsym_s, "FR", fz_, _m.radians(a_), 0.0, 0.0)[1] - t.wheel_forces(dsym_i, "FR", fz_, _m.radians(a_), 0.0, 0.0)[1]) for fz_ in (300, 700, 1200) for a_ in (-12, -5, 2, 9))
check("TC-TIRE-010e: sem termos assimétricos (SHy, SVy, PEY3/4 = 0; γ=0, κ=0), SAE_CALSPAN e ISO_TYDEX dão o MESMO Fy (parte ímpar invariante à convenção)", dd < 1e-9, f"dif máx={dd:.1e} N")
dd2 = max(abs(t.wheel_forces(dsS, "FR", 564.0, _m.radians(a_), 0.0, 0.0)[1] - t.wheel_forces(dsI, "FR", 564.0, _m.radians(a_), 0.0, 0.0)[1]) for a_ in (4, -4))
check("TC-TIRE-010f: CARACTERIZAÇÃO — com os termos reais do arquivo, os dois modos diferem (efeito da convenção nos termos assimétricos), mas por menos de 10% de |Fy| a 4°", 1.0 < dd2 < 0.1 * 1440, f"dif máx a ±4°, 564 N = {dd2:.1f} N")
check("TC-TIRE-010g: sistema de eixos ausente ou 'UNKNOWN' rejeitado pelo loader; modo inválido rejeitado",
      raises(lambda: t.load_dataset(TIR), t.TireDataError) and raises(lambda: t.load_dataset(TIR, source_axis_system="UNKNOWN"), t.TireDataError) and raises(lambda: t.load_dataset(TIR, source_axis_system="sae"), t.TireDataError))
check("TC-TIRE-010h: espelhamento antes da transformação: Fy_FL(α, γ) = −Fy_FR(−α, γ) e Fx igual, também em ISO_TYDEX",
      all(abs(t.wheel_forces(dx, "FL", 700.0, _m.radians(3), _m.radians(1.5), 0.05)[1] + t.wheel_forces(dx, "FR", 700.0, _m.radians(-3), _m.radians(1.5), 0.05)[1]) < 1e-9 for dx in (dsS, dsI)))
psr = t.project_sign_report(dsS)
check("TC-TIRE-010i: CARACTERIZAÇÃO — sinais no projeto (SAE_CALSPAN, roda direita): Fy<0 para α_ISO>0; Fy<0 para camber topo-para-fora; Fx<0 em frenagem", psr["Fy_ISO(alpha_ISO=+4deg)"] < 0 and psr["Fy_ISO(gamma=+3deg topo p/ fora)"] < 0 and psr["Fx(kappa=-0.10)"] < 0, str({k: round(v, 1) for k, v in psr.items()}))

print("\n--- Resumo ---")
n_pass = sum(1 for _, s in results if s == "PASS"); n_fail = len(results) - n_pass
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail:
    raise SystemExit(1)
