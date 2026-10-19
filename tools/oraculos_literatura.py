"""Confronto numérico dos modelos com exemplos publicados (revisão metodológica).

Uso: uv run python -X utf8 tools/oraculos_literatura.py

Não altera nenhum modelo nem a planilha. As funções "milliken_*" abaixo transcrevem
as fórmulas do livro para servir de oráculo; não são a implementação do projeto.

Fontes (cópias locais em references/, fora do Git):
- [MIL] Milliken & Milliken, Race Car Vehicle Dynamics, SAE 1995 (5ª impressão).
  p. 591-592 (taxas em série), p. 596 (taxa geométrica), p. 601-603 (massa e CG suspensos),
  p. 612-613 (eixo instantâneo), p. 682-683 (transferência
  lateral, fórmula completa e exemplo), p. 702-703 (forma com CG deslocado).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import suspension_model as sm  # noqa: E402

# ---------------------------------------------------------------- Milliken p. 683
# Dados do exemplo (lb, ft, lb-ft/rad). A_Y em g: com massa "em lb" e a_y = 1, o
# modelo linear devolve diretamente ΔW/A_Y em lb/g.
MIL683 = dict(l=9.5, a=4.56, b=4.94, h=1.5, zRF=0.25, zRR=0.625, zWF=1.0, zWR=1.0,
              W=3500.0, WuF=200.0, WuR=300.0, KF=67600.0, KR=36100.0, t=5.0)
MIL683_LIVRO = {"full": (590.8, 483.4), "simplified": (579.3, 470.7)}


def milliken_sprung_long(d):
    """[MIL] p. 603 (a_s = W_SF/W_S, com W_SF = W_F − W_uF da p. 601): b_s = (W·b − W_uF·ℓ)/W_s ; a_s = ℓ − b_s."""
    Ws = d["W"] - d["WuF"] - d["WuR"]
    bs = (d["W"] * d["b"] - d["WuF"] * d["l"]) / Ws
    return Ws, d["l"] - bs, bs


def milliken_hs(d, Ws):
    """[MIL] p. 602: h_s = (W·h − W_uF·R_LF − W_uR·R_LR)/W_s (R_L ≈ altura do CG não-suspenso)."""
    return (d["W"] * d["h"] - d["WuF"] * d["zWF"] - d["WuR"] * d["zWR"]) / Ws


def milliken_full(d, variante):
    """[MIL] p. 682. variante='impressa' usa K_F' = K_F − (ℓ−a_s)W_s h2/ℓ (como impresso);
    variante='consistente' usa K_F (forma da §18.10, p. 703, e dos números da p. 683)."""
    Ws, a_s, b_s = milliken_sprung_long(d)
    hs = milliken_hs(d, Ws)
    l = d["l"]
    z_at_cg = d["zRF"] + (d["zRR"] - d["zRF"]) * a_s / l
    h2 = hs - z_at_cg          # vertical; o exemplo da p. 683 (h2 = 1,16 ft) e o Seward (p. 133) usam a vertical
    den = d["KF"] + d["KR"] - Ws * h2
    if variante == "impressa":
        KFp = d["KF"] - (l - a_s) * Ws * h2 / l
        KRp = d["KR"] - a_s * Ws * h2 / l
    else:
        KFp, KRp = d["KF"], d["KR"]
    dWF = Ws / d["t"] * (h2 * KFp / den + (l - a_s) / l * d["zRF"]) + d["WuF"] / d["t"] * d["zWF"]
    dWR = Ws / d["t"] * (h2 * KRp / den + a_s / l * d["zRR"]) + d["WuR"] / d["t"] * d["zWR"]
    phi = -Ws * h2 / den                           # rad/g
    return dict(dWF=dWF, dWR=dWR, phi=phi, a_s=a_s, h2=h2, hs=hs,
                momento=d["t"] * (dWF + dWR))


def modelo_atual_sus103(d):
    """SUS-103 como implementado (suspension_model.lateral_dfz, V2.5), nas unidades do exemplo (massa em lb/g, a_y = G)."""
    cfg = sm.VehicleConfig(
        mass_total=d["W"] / sm.G, cg_height=d["h"], wheelbase=d["l"], track_front=d["t"], track_rear=d["t"],
        cg_to_front=d["a"], cg_to_rear=d["b"], unsprung_mass_front=d["WuF"] / sm.G, unsprung_mass_rear=d["WuR"] / sm.G,
        unsprung_cg_height_front=d["zWF"], unsprung_cg_height_rear=d["zWR"],
        roll_center_front=d["zRF"], roll_center_rear=d["zRR"],
        roll_stiffness_front=d["KF"], roll_stiffness_rear=d["KR"])
    r = sm.lateral_dfz(cfg, sm.G)
    return dict(dWF=r["front_axle"], dWR=r["rear_axle"], momento=d["t"] * (r["front_axle"] + r["rear_axle"]))


# ------------------------------------------------- Milliken p. 591-592: pneu em série
def serie(k1, k2):
    """[MIL] p. 591: S = S1·S2/(S1+S2)."""
    return k1 * k2 / (k1 + k2)


def efeito_pneu_planilha():
    """Valores de entrada da planilha V2.4 (05/06_SUSPENSION) e K_T do .tir PROVISÓRIO
    (VERTICAL_STIFFNESS = 120312 N/m, EDR-038). Resultado demonstrativo, não do carro."""
    m, L, a, b = 316.5, 1.594, 0.82203, 0.77197
    tF, tR = 1.277, 1.271
    muF, muR = 15.0, 18.0
    Ks = (49909.24, 57052.22)
    MR = (1.76, 1.76)
    Karb = (5012.32, 10.78)
    KT = 120312.0
    ms = m - muF - muR
    out = {}
    # massa suspensa por canto: forma atual (SUS-009) e forma do livro (p. 601, Tabela 16.3: W_SF = W_F − W_UF)
    msc_atual = (ms * (b / L) / 2, ms * (a / L) / 2)
    msc_livro = ((m * b / L - muF) / 2, (m * a / L - muR) / 2)
    for i, (eixo, t) in enumerate((("F", tF), ("R", tR))):
        Kw = Ks[i] / MR[i] ** 2
        Kride = serie(Kw, KT)
        f_atual = math.sqrt(Kw / msc_atual[i]) / (2 * math.pi)
        f_livro = math.sqrt(Kride / msc_livro[i]) / (2 * math.pi)
        Kphi_atual = Kw * t ** 2 / 2 + Karb[i]
        Kphi_livro = serie(Kw * t ** 2 / 2 + Karb[i], KT * t ** 2 / 2)   # p. 592 (barra referida à roda)
        out[eixo] = dict(Kw=Kw, Kride=Kride, m_canto_atual=msc_atual[i], m_canto_livro=msc_livro[i],
                         f_atual=f_atual, f_livro=f_livro, Kphi_atual=Kphi_atual, Kphi_livro=Kphi_livro)
    lf_atual = out["F"]["Kphi_atual"] / (out["F"]["Kphi_atual"] + out["R"]["Kphi_atual"])
    lf_livro = out["F"]["Kphi_livro"] / (out["F"]["Kphi_livro"] + out["R"]["Kphi_livro"])
    return out, lf_atual, lf_livro


# ------------------------------- Milliken p. 612-613, Fig. 17.6: eixo instantâneo
def ic_por_eixo_instantaneo(corner, dz=1e-5):
    """[MIL] p. 612-613 (Fig. 17.6): os ICs frontal e lateral são os pontos onde o EIXO
    INSTANTÂNEO da manga atravessa os planos verticais (transversal e longitudinal) pelo
    centro da roda. Aqui o eixo vem do helicoide instantâneo da pose (ω e v por diferença
    central). Só diagnóstico: não altera o kinematics_model."""
    import numpy as np
    import kinematics_model as km
    s0 = corner.solve(0.0)
    sp = corner.solve(dz, q0=s0.q, phi0=s0.phi)
    sm = corner.solve(-dz, q0=s0.q, phi0=s0.phi)
    Rp, Rm = km._rot_vec(sp.q[:3]), km._rot_vec(sm.q[:3])
    W = (Rp @ Rm.T - (Rp @ Rm.T).T) / (4 * dz)           # ω^ por unidade de curso
    w = np.array([W[2, 1], W[0, 2], W[1, 0]])
    P = corner.pt(s0, "WHEEL_CENTER")
    v = (corner.pt(sp, "WHEEL_CENTER") - corner.pt(sm, "WHEEL_CENTER")) / (2 * dz)
    a0 = P + np.cross(w, v) / (w @ w)                     # ponto do eixo mais próximo de P
    passo = (w @ v) / (w @ w)                             # passo do helicoide [m/rad]
    out = {"w": w, "passo_m_rad": passo}
    for nome, eixo in (("front", 0), ("side", 1)):
        if abs(w[eixo]) < 1e-12:
            out[nome] = None
            continue
        t = (P[eixo] - a0[eixo]) / w[eixo]
        q = a0 + t * w
        out[nome] = q[[1, 2]] if nome == "front" else q[[0, 2]]
    return out


def comparar_ic_lateral():
    """Compara, na geometria SINTÉTICA (data/hardpoints_synthetic_V2.0.csv), os métodos de
    IC lateral do projeto com a definição de Milliken por eixo instantâneo."""
    import kinematics_model as km
    from hardpoints import load_hardpoints
    raiz = Path(__file__).resolve().parents[1] / "data"
    hs = load_hardpoints(raiz / "hardpoints_synthetic_V2.0.csv", raiz / "hardpoints_synthetic_V2.0.meta.json")
    fl = km.Corner(hs, "FL")
    m = km.ic_methods_at_reference(fl)
    ia = ic_por_eixo_instantaneo(fl)
    k = km.kinematic_centers(fl)
    cp = k["contact_patch"][[0, 2]]
    L, h, fb = 1.55, 0.315, 0.6       # mesmos valores do TC-KIN-114 (registro V2.0); sintéticos
    linhas = []
    for nome, ic in (("kinematic (SUS-412)", m["side"]["kinematic"]),
                     ("v1 ponto médio (SUS-406)", m["side"]["v1_outer_to_inner"]),
                     ("eixos de pivô", m["side"]["pivot_axes"]),
                     ("eixo instantâneo (Milliken Fig. 17.6)", {"point": ia["side"], "direction": None})):
        s = km.force_line_slope(ic, cp)
        ad = km.anti_dive_percent_signed(s, fb, L, h) if s is not None else float("nan")
        pt = ic["point"]
        txt = f"({pt[0]:+.4f}, {pt[1]:+.4f}) m" if pt is not None else "infinito"
        linhas.append((nome, txt, ad))
    return linhas, ia


# ------------------------------------- Milliken p. 596: termo de taxa geométrica
def taxa_geometrica():
    """[MIL] p. 596: K_W = F_s·(ΔIR/Δδ) + K_s·IR², IR = Δmola/Δroda = 1/MR [wheel/spring].
    Geometria SINTÉTICA (FL) + K_s e peso suspenso por canto da planilha V2.4: DEMONSTRATIVO."""
    import kinematics_model as km
    from hardpoints import load_hardpoints
    raiz = Path(__file__).resolve().parents[1] / "data"
    hs = load_hardpoints(raiz / "hardpoints_synthetic_V2.0.csv", raiz / "hardpoints_synthetic_V2.0.meta.json")
    fl = km.Corner(hs, "FL")
    dz = 2e-3
    ir = {z: 1.0 / km.motion_ratio(fl, z)["mr_wheel_per_spring"] for z in (-dz, 0.0, dz)}
    dir_dz = (ir[dz] - ir[-dz]) / (2 * dz)                 # IR = |dL/dz|; sinal: IR cresce em bump se > 0
    Ks = 49909.24                                          # N/m, 06_SUSPENSION!B4
    Fw = 68.65 * 9.81                                      # N, peso suspenso por canto dianteiro (SUS-009 atual)
    Fs = Fw / ir[0.0]                                      # trabalho virtual: F_w dz = F_s dL
    geo = Fs * dir_dz
    elast = Ks * ir[0.0] ** 2
    return dict(MR=1 / ir[0.0], IR=ir[0.0], dIR_dz=dir_dz, Fs=Fs, geo=geo, elast=elast)


def main():
    d = MIL683
    print("== Milliken p. 683: transferência lateral por g (lb/g) ==")
    print(f"Livro (fórmula completa):   F={MIL683_LIVRO['full'][0]:.1f}  R={MIL683_LIVRO['full'][1]:.1f}")
    print(f"Livro (simplificada):       F={MIL683_LIVRO['simplified'][0]:.1f}  R={MIL683_LIVRO['simplified'][1]:.1f}")
    for v in ("impressa", "consistente"):
        r = milliken_full(d, v)
        print(f"Fórmula p.682 {v:12s}: F={r['dWF']:.1f}  R={r['dWR']:.1f}  "
              f"t·ΣΔW={r['momento']:.1f}  φ/A_Y={math.degrees(r['phi']):.3f} °/g  "
              f"(a_s={r['a_s']:.3f} ft, h2={r['h2']:.3f} ft)")
    r = modelo_atual_sus103(d)
    print(f"SUS-103 modelo (V2.5):     F={r['dWF']:.1f}  R={r['dWR']:.1f}  t·ΣΔW={r['momento']:.1f}")
    print(f"W·h = {d['W'] * d['h']:.1f} lb·ft/g")
    rc = milliken_full(d, "consistente")
    print(f"W·h + W_s·h2·|φ| = {d['W'] * d['h'] + (d['W'] - d['WuF'] - d['WuR']) * rc['h2'] * abs(rc['phi']):.1f}")

    print("\n== Efeito do pneu em série e da massa suspensa por eixo (valores da planilha V2.4; DEMONSTRATIVO) ==")
    out, lf_a, lf_l = efeito_pneu_planilha()
    for e in ("F", "R"):
        o = out[e]
        print(f"{e}: K_wheel={o['Kw']:.0f} N/m  K_ride={o['Kride']:.0f} N/m ({100 * (o['Kride'] / o['Kw'] - 1):+.1f} %)  "
              f"m_canto V2.4={o['m_canto_atual']:.2f} kg V2.5={o["m_canto_livro"]:.2f} kg  "
              f"f_n V2.4={o['f_atual']:.3f} Hz V2.5={o['f_livro']:.3f} Hz  "
              f"K_phi V2.4={o['Kphi_atual']:.0f} V2.5={o['Kphi_livro']:.0f} N·m/rad "
              f"({100 * (o['Kphi_livro'] / o['Kphi_atual'] - 1):+.1f} %)")
    print(f"lambda_f V2.4={lf_a:.4f}  V2.5 (pneu em série)={lf_l:.4f}")

    print("\n== IC lateral FL, geometria SINTÉTICA: métodos do projeto x eixo instantâneo (Milliken) ==")
    linhas, ia = comparar_ic_lateral()
    for nome, txt, ad in linhas:
        print(f"{nome:40s} IC={txt:28s} %AD (contact patch, com sinal) = {ad:8.1f}")
    tg = taxa_geometrica()
    print("\n== Taxa geométrica (Milliken p. 596), geometria SINTÉTICA FL; DEMONSTRATIVO ==")
    print(f"MR={tg['MR']:.4f}  IR={tg['IR']:.4f}  dIR/dz={tg['dIR_dz']:+.4f} 1/m  F_s={tg['Fs']:.0f} N  "
          f"termo geométrico={tg['geo']:+.0f} N/m  K_s·IR²={tg['elast']:.0f} N/m  "
          f"({100 * tg['geo'] / tg['elast']:+.2f} % do wheel rate elástico)")
    fr = ia["front"]
    print(f"IC frontal pelo eixo instantâneo: (Y={fr[0]:+.4f}, Z={fr[1]:+.4f}) m; passo do helicoide = {ia['passo_m_rad']:+.5f} m/rad")


if __name__ == "__main__":
    main()
