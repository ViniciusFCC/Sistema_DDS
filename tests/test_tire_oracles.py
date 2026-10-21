"""
Comparação do tire_model_V2_4 com DUAS implementações de terceiros (oráculos), transcritas de código publicado:
  A) Racer v0.8.9 RPacejka::CalcMF52()  (http://www.racer.nl/reference/pacejka.htm; 'Pacejka MF5.2 (~2006)')
  B) MFeval (Marco Furlan; port Julia matheusft/MFeval_julia, MIT) — ramo MF5.2 de Fx0.jl, Fy0.jl, combined_slip.jl,
     que cita Pacejka (2012), eqs. 4.E9-4.E67; modo 111 (alpha* = alpha, gamma* = gamma).
As transcrições mantêm a estrutura e as peculiaridades de cada fonte. Concordância = a MINHA transcrição bate com
código de terceiros; NÃO é validação contra medição, nem contra o livro (não consultado diretamente).
Namespace TC-TIRE-ORC-xxx. python3 test_tire_oracles_V2_4.py
"""
import math, os, random
import tire_model as t

HERE = os.path.dirname(os.path.abspath(__file__))
ds = t.load_dataset(os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir"), source_axis_system="ISO_TYDEX"); p = ds.p
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def racer_mf52(P, Fz, alpha, gamma, k):
    """Transcrição de RPacejka::CalcMF52 (Fx, Fy antes do 'negate for Racer'). Fz em N. Sem Mz."""
    atan, sin, cos, exp = math.atan, math.sin, math.cos, math.exp
    Fz0_der = P["LFZO"] * P["FNOMIN"]; dfz = (Fz - Fz0_der) / Fz0_der
    Shx = (P["PHX1"] + P["PHX2"] * dfz) * P["LHX"]; Svx = Fz * (P["PVX1"] + P["PVX2"] * dfz) * P["LVX"] * P["LMUX"]
    kx = k + Shx; sign_kx = -1.0 if kx < 0 else 1.0
    gamma_x = gamma * P["LGAX"]
    Cx = P["PCX1"] * P["LCX"]; mux = (P["PDX1"] + P["PDX2"] * dfz) * (1 - P["PDX3"] * gamma_x ** 2) * P["LMUX"]
    Ex = (P["PEX1"] + P["PEX2"] * dfz + P["PEX3"] * dfz * dfz) * (1 - P["PEX4"] * sign_kx) * P["LEX"]
    if Ex > 1: Ex = 1.0
    Dx = mux * Fz; Kx = Fz * (P["PKX1"] + P["PKX2"] * dfz) * exp(P["PKX3"] * dfz) * P["LKX"]
    tmp = Cx * Dx; Bx = Kx / (tmp + 0.001) if abs(tmp) < 0.001 else Kx / tmp
    tmp = Bx * kx; Fx0 = Dx * sin(Cx * atan(tmp - Ex * (tmp - atan(tmp)))) + Svx
    gamma_y = gamma * P["LGAY"]
    Cy = P["PCY1"] * P["LCY"]; localMuy = (P["PDY1"] + P["PDY2"] * dfz) * (1 - P["PDY3"] * gamma_y ** 2) * P["LMUY"]
    Dy = localMuy * Fz
    Ky = P["PKY1"] * Fz0_der * sin(2 * atan(Fz / (P["PKY2"] * Fz0_der))) * (1 - P["PKY3"] * abs(gamma_y)) * P["LFZO"] * P["LKY"]
    tmp = Cy * Dy; By = Ky / (tmp + 0.001) if abs(tmp) < 0.001 else Ky / tmp
    Shy = (P["PHY1"] + P["PHY2"] * dfz) * P["LHY"] + P["PHY3"] * gamma_y
    Svy = Fz * ((P["PVY1"] + P["PVY2"] * dfz) * P["LVY"] + (P["PVY3"] + P["PVY4"] * dfz) * gamma_y) * P["LMUY"]
    say = alpha + Shy; sign_alpha_y = -1.0 if say < 0 else 1.0
    Ey = (P["PEY1"] + P["PEY2"] * dfz) * (1 - (P["PEY3"] + P["PEY4"] * gamma_y) * sign_alpha_y) * P["LEY"]
    if Ey > 1: Ey = 1.0
    tmp = By * say; Fy0 = Dy * sin(Cy * atan(tmp - Ey * (tmp - atan(tmp)))) + Svy
    Shxa = P["RHX1"]; Exa = P["REX1"] + P["REX2"] * dfz; Cxa = P["RCX1"]      # (sem limitador de Exa: peculiaridade do Racer)
    Bxa = P["RBX1"] * cos(atan(P["RBX2"] * k)) * P["LXAL"]; alpha_s = alpha + Shxa
    Gxa0 = cos(Cxa * atan(Bxa * Shxa - Exa * (Bxa * Shxa - atan(Bxa * Shxa))))
    Gxa = cos(Cxa * atan(Bxa * alpha_s - Exa * (Bxa * alpha_s - atan(Bxa * alpha_s)))) / Gxa0
    Fx = Gxa * Fx0
    Dvyk = localMuy * Fz * (P["RVY1"] + P["RVY2"] * dfz + P["RVY3"] * gamma) * cos(atan(P["RVY4"] * alpha))   # muy: ambíguo no fonte; usa-se o local
    Svyk = Dvyk * sin(P["RVY5"] * atan(P["RVY6"] * k)) * P["LVYKA"]
    Shyk = P["RHY1"] + P["RHY2"] * dfz; Eyk = P["REY1"] + P["REY2"] * dfz; Cyk = P["RCY1"]
    Byk = P["RBY1"] * cos(atan(P["RBY2"] * (alpha - P["RBY3"]))) * P["LYKA"]; ks = k + Shyk
    Gyk0 = cos(Cyk * atan(Byk * Shyk - Eyk * (Byk * Shyk - atan(Byk * Shyk))))
    Gyk = cos(Cyk * atan(Byk * ks - Eyk * (Byk * ks - atan(Byk * ks)))) / Gyk0
    return Fx, Gyk * Fy0 + Svyk


def mfeval_mf52(P, Fz, alpha, gamma, k, eps=1e-3):
    """Transcrição do ramo MF5.2 de MFeval (Fx0.jl, Fy0.jl, combined_slip.jl), modo 111, LMUV=0, Amu=1, dpi=0, sem turn slip.
    Peculiaridades da fonte: sem LGAX/LGAY; sem fator LFZO extra em Ky; PKY4 = 2 e PEY5 = 0 (não existem no .tir PAC2002);
    camber do SVy/Shy via LKYC (= 1 aqui); epsilon = 1e-3 (valor adotado pelo port; não verificado no MATLAB)."""
    atan, sin, cos, exp = math.atan, math.sin, math.cos, math.exp
    sg = lambda x: 1.0 if x >= 0 else -1.0
    Fz0p = P["LFZO"] * P["FNOMIN"]; dfz = (Fz - Fz0p) / Fz0p
    a_, g_ = alpha, gamma
    Cx = P["PCX1"] * P["LCX"]; mux = (P["PDX1"] + P["PDX2"] * dfz) * (1 - P["PDX3"] * g_ ** 2) * P["LMUX"]; Dx = mux * Fz
    Kxk = Fz * (P["PKX1"] + P["PKX2"] * dfz) * exp(P["PKX3"] * dfz) * P["LKX"]
    Bx = Kxk / (Cx * Dx + eps * sg(Dx)); SHx = (P["PHX1"] + P["PHX2"] * dfz) * P["LHX"]
    SVx = Fz * (P["PVX1"] + P["PVX2"] * dfz) * P["LVX"] * P["LMUX"]; kx = k + SHx
    Ex = min((P["PEX1"] + P["PEX2"] * dfz + P["PEX3"] * dfz ** 2) * (1 - P["PEX4"] * sg(kx)) * P["LEX"], 1.0)
    Fx0 = Dx * sin(Cx * atan(Bx * kx - Ex * (Bx * kx - atan(Bx * kx)))) + SVx
    PKY4 = 2.0
    Kya = P["PKY1"] * Fz0p * (1 - P["PKY3"] * abs(g_)) * sin(PKY4 * atan((Fz / Fz0p) / P["PKY2"])) * P["LKY"]
    SVyg = Fz * (P["PVY3"] + P["PVY4"] * dfz) * g_ * 1.0 * P["LMUY"]
    SHy = (P["PHY1"] + P["PHY2"] * dfz) * P["LHY"] + P["PHY3"] * g_ * 1.0
    SVy = Fz * (P["PVY1"] + P["PVY2"] * dfz) * P["LVY"] * P["LMUY"] + SVyg
    ay = a_ + SHy; Cy = P["PCY1"] * P["LCY"]
    muy = (P["PDY1"] + P["PDY2"] * dfz) * (1 - P["PDY3"] * g_ ** 2) * P["LMUY"]; Dy = muy * Fz
    Ey = min((P["PEY1"] + P["PEY2"] * dfz) * (1 + 0.0 * g_ ** 2 - (P["PEY3"] + P["PEY4"] * g_) * sg(ay)) * P["LEY"], 1.0)
    By = Kya / (Cy * Dy + eps * sg(Dy))
    Fy0 = Dy * sin(Cy * atan(By * ay - Ey * (By * ay - atan(By * ay)))) + SVy
    Cxa = P["RCX1"]; Exa = min(P["REX1"] + P["REX2"] * dfz, 1.0); SHxa = P["RHX1"]
    Bxa = (P["RBX1"] + 0.0 * g_ ** 2) * cos(atan(P["RBX2"] * k)) * P["LXAL"]; als = a_ + SHxa
    Gxa0 = cos(Cxa * atan(Bxa * SHxa - Exa * (Bxa * SHxa - atan(Bxa * SHxa))))
    Gxa = cos(Cxa * atan(Bxa * als - Exa * (Bxa * als - atan(Bxa * als)))) / Gxa0
    DVyk = muy * Fz * (P["RVY1"] + P["RVY2"] * dfz + P["RVY3"] * g_) * cos(atan(P["RVY4"] * a_))
    SVyk = DVyk * sin(P["RVY5"] * atan(P["RVY6"] * k)) * P["LVYKA"]
    SHyk = P["RHY1"] + P["RHY2"] * dfz; Eyk = min(P["REY1"] + P["REY2"] * dfz, 1.0); Cyk = P["RCY1"]
    Byk = (P["RBY1"] + 0.0 * g_ ** 2) * cos(atan(P["RBY2"] * (a_ - P["RBY3"]))) * P["LYKA"]; ks = k + SHyk
    Gyk0 = cos(Cyk * atan(Byk * SHyk - Eyk * (Byk * SHyk - atan(Byk * SHyk))))
    Gyk = cos(Cyk * atan(Byk * ks - Eyk * (Byk * ks - atan(Byk * ks)))) / Gyk0
    return Gxa * Fx0, Gyk * Fy0 + SVyk


rnd = random.Random(2026)
pts = [(rnd.uniform(100, 1521), rnd.uniform(-1, 1) * p["ALPMAX"], rnd.uniform(-1, 1) * p["CAMMAX"], rnd.uniform(-1, 1) * p["KPUMAX"]) for _ in range(3000)]


def worst(fn, P=p, dsx=ds, pts_=pts):
    wx = wy = 0.0; scale = 1.0
    for fz, a, g, k in pts_:
        fx, fy, _ = t.combined_forces(dsx, fz, a, g, k, check_range=False)
        ox, oy = fn(P, fz, a, g, k)
        wx = max(wx, abs(fx - ox)); wy = max(wy, abs(fy - oy))
    return wx, wy


wx, wy = worst(racer_mf52)
check("TC-TIRE-ORC-001: módulo == Racer CalcMF52 em 3000 pontos (dataset TTC provisório); tol. 0,05 N (guarda de divisão difere: ε=1e-6 vs. 0,001 só se |Cx·Dx|<0,001)", wx < 0.05 and wy < 0.05, f"dif máx Fx={wx:.2e} N, Fy={wy:.2e} N")
wx2, wy2 = worst(mfeval_mf52)
check("TC-TIRE-ORC-002: módulo == ramo MF5.2 do MFeval em 3000 pontos; tol. 0,1 N (MFeval usa ε=1e-3 em B)", wx2 < 0.1 and wy2 < 0.1, f"dif máx Fx={wx2:.2e} N, Fy={wy2:.2e} N")
wx3 = max(abs(racer_mf52(p, *pt)[0] - mfeval_mf52(p, *pt)[0]) for pt in pts)
wy3 = max(abs(racer_mf52(p, *pt)[1] - mfeval_mf52(p, *pt)[1]) for pt in pts)
check("TC-TIRE-ORC-003: os dois oráculos concordam entre si (confirma que são transcrições coerentes de fontes distintas)", wx3 < 0.1 and wy3 < 0.1, f"dif máx Fx={wx3:.2e}, Fy={wy3:.2e} N")

# --- onde as fontes divergem (caracterização; só aparece com L* != 1 ou casos de borda) ---
p2 = dict(p); p2["LFZO"] = 1.1
ds2 = t.TireDataset(p=p2, strings=ds.strings)
d_lfzo = max(abs(t.combined_forces(ds2, fz, a, g, k, check_range=False)[1] - mfeval_mf52(p2, fz, a, g, k)[1]) for fz, a, g, k in pts[:200])
d_lfzo_r = max(abs(t.combined_forces(ds2, fz, a, g, k, check_range=False)[1] - racer_mf52(p2, fz, a, g, k)[1]) for fz, a, g, k in pts[:200])
check("TC-TIRE-ORC-004: CARACTERIZAÇÃO — com LFZO≠1 o módulo concorda com o MFeval (um só λFz0 em Ky, como Pacejka 4.E25 e Seward 5.9; EDR-049) e DIVERGE do Racer (fator LFZO extra)",
      d_lfzo < 0.1 and d_lfzo_r > 1.0, f"Fy: dif vs MFeval={d_lfzo:.2e} N; vs Racer={d_lfzo_r:.1f} N")
p3 = dict(p); p3["LGAY"] = 1.5; p3["LGAX"] = 1.5
ds3 = t.TireDataset(p=p3, strings=ds.strings)
d_lga_r = max(abs(t.combined_forces(ds3, fz, a, g, k, check_range=False)[1] - racer_mf52(p3, fz, a, g, k)[1]) for fz, a, g, k in pts[:200])
d_lga_m = max(abs(t.combined_forces(ds3, fz, a, g, k, check_range=False)[1] - mfeval_mf52(p3, fz, a, g, k)[1]) for fz, a, g, k in pts[:200])
check("TC-TIRE-ORC-005: CARACTERIZAÇÃO — com LGAY/LGAX≠1 o módulo concorda com o Racer (que aplica γy=γ·LGAY) e diverge do MFeval (que não os usa)",
      d_lga_r < 0.05 and d_lga_m > 1.0, f"Fy: dif vs Racer={d_lga_r:.2e} N; vs MFeval={d_lga_m:.1f} N")

print("\n--- Resumo ---"); n = sum(1 for _, s in results if s == "PASS"); f = len(results) - n
print(f"{n} PASS, {f} FAIL, de {len(results)} testes")
if f: raise SystemExit(1)
