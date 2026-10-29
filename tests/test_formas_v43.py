"""
Testes das formas v43 do equilíbrio (incremento 7; EDR-066, EDR-067, decisão D1 do plano).
TC-ACK-001: Ackermann com o centro da curva na linha do eixo traseiro (spec §3.1 e §4.1; Task 3).
TC-FXI-001 e 002: Fx exigido por arrasto induzido (spec §4.2; decisões D2 e D3; Task 4).
TC-ACK-002 entra na Task 5.
Roda como script: uv run python -X utf8 tests/test_formas_v43.py

O veículo (L, b, bitolas) e os raios abaixo são entradas SINTÉTICAS de teste (o veiculo_base do
tests/test_equilibrio.py), não do carro; o .tir é o provisório do TTC.
"""
import dataclasses
import math
import os

import equilibrio as eq
import tire_model as tm
from suspension_model import G, VehicleConfig

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def veiculo_base(**over) -> VehicleConfig:
    """Veículo de teste (números plausíveis, NÃO é setup real): o mesmo de tests/test_equilibrio.py."""
    base = dict(mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
                cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
                unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
                roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0)
    base.update(over)
    return VehicleConfig(**base)


def oraculo_angulos(L: float, t_f: float, t_r: float, b: float, R: float, sentido: int) -> dict:
    """Ângulo [rad] da velocidade de cada roda pelo produto vetorial v = ω ẑ × (P − C), sem a fórmula atan(L/…).

    Referencial do carro real (ISO 8855): origem no meio do eixo traseiro, X para a frente, Y para a esquerda.
    sentido = +1: curva à esquerda, C = (0, +R_c), ω > 0; sentido = −1: curva à direita, C = (0, −R_c), ω < 0.
    R_c = √(R² − b²) (CG na linha central, spec §3.1). O ângulo é atan2(v_y, v_x) em relação ao eixo X do carro.
    """
    R_c = math.sqrt(R * R - b * b)
    cx, cy, w = 0.0, sentido * R_c, float(sentido)
    pos = {"FL": (L, t_f / 2), "FR": (L, -t_f / 2), "RL": (0.0, t_r / 2), "RR": (0.0, -t_r / 2)}
    out = {}
    for c, (x, y) in pos.items():
        rx, ry = x - cx, y - cy
        vx, vy = -w * ry, w * rx          # ω ẑ × (rx, ry, 0) = (−ω·ry, ω·rx, 0)
        out[c] = math.atan2(vy, vx)
    return out


cfg = veiculo_base()
ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
L, B, TF, TR = cfg.wheelbase, cfg.cg_to_rear, cfg.track_front, cfg.track_rear
R_TESTE = 8.0     # sintético de teste: raio do skidpad usado só nos testes, não é dado do carro
R_GRANDE = 20.0   # sintético de teste: raio grande, para o termo de 1ª ordem de (c) (ver o comentário lá)
TROCA = {"FL": "FR", "FR": "FL", "RL": "RR", "RR": "RL"}

# (e) Valores congelados da forma v42, medidos com o código de ANTES da Task 3 (commit 291532b, 2026-10-29), no caso
# abaixo (veiculo_base, R = 8 m, 100 % de Ackermann, toe FL = 0,2°, FR = 0,1°, a_y = 1 g), pelo script
# equilibrio.deriva_ackermann / deriva_total / capacidade_eixo(…, 25) / fy_eixo(…, α = −0,05) / grade_alfa(…, 25)[-1]
# (repr dos floats; a comparação é exata).
TOE_TESTE = {"FL": math.radians(0.2), "FR": math.radians(0.1), "RL": 0.0, "RR": 0.0}   # sintético de teste
CONGELADO_V42 = {
    "ack": {"FL": -0.014273408420030609, "FR": 0.014273408420030581, "RL": 0.0, "RR": 0.0},
    "tot": {"FL": -0.01776406692401927, "FR": 0.01601873767202491, "RL": 0.0, "RR": 0.0},
    "capF": (2920.8713318073756, -0.13218558874948957),
    "capR": (3439.6658790858064, -0.13218558874948957),
    "fyF": 2099.6224774341163,
    "grade": -0.2440349330759807,
}


# --- TC-ACK-001 ---------------------------------------------------------------------------------------------------
def tc_ack_001() -> tuple[bool, str]:
    partes, det = {}, []
    v42, v43 = eq.FORMAS_V42, eq.FORMAS_V43
    caso100 = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, ackermann_pct=100.0)
    caso0 = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, ackermann_pct=0.0)
    R_c = math.sqrt(R_TESTE ** 2 - B ** 2)

    # (a) oráculo independente dos ângulos da velocidade; R <= b recusa com a mensagem do plano
    th = eq.angulos_velocidade(caso100)
    ora = oraculo_angulos(L, TF, TR, B, R_TESTE, +1)
    erro_a = max(abs(th[c] - ora[c]) for c in eq.CANTOS)
    try:
        eq.angulos_velocidade(eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=B))
        recusa = False
    except ValueError as exc:
        recusa = "R ≤ b: o centro da curva não fica na linha do eixo traseiro" in str(exc)
    partes["a"] = erro_a <= 1e-12 and th["RL"] == 0.0 and th["RR"] == 0.0 and th["FL"] > th["FR"] > 0.0 and recusa
    det.append(f"(a) erro={erro_a:.1e}, θ_FL={th['FL']:.6f}, θ_FR={th['FR']:.6f} rad")

    # (b) 100 % de Ackermann: diferença FL−FR do Δα v43 <= |δ̄ − θ̄_F| <= cota de 2ª ordem
    d43 = eq.deriva_ackermann(caso100, formas=v43)
    dl = eq.esterco_rodas(caso100)
    d_ref = L / R_TESTE
    th_med = (th["FL"] + th["FR"]) / 2
    forma = all(abs(d43[c] - (-(dl[c] - d_ref) + (th[c] - th_med))) <= 1e-15 for c in ("FL", "FR"))
    dif_b = abs(d43["FL"] - d43["FR"])
    d_med = (dl["FL"] + dl["FR"]) / 2
    lado = abs(d_med - th_med)
    cota = (L / R_TESTE) * (TF / (2 * R_c)) ** 2 + abs(d_ref - math.atan(L / R_c))
    partes["b"] = forma and d43["RL"] == 0.0 and d43["RR"] == 0.0 and dif_b <= lado <= cota
    det.append(f"(b) |ΔFL−ΔFR|={dif_b:.3e} <= |δ̄−θ̄|={lado:.3e} <= cota={cota:.3e} rad")

    # (c) 0 % (paralelo): ΔFL − ΔFR = θ_FL − θ_FR (exato) ≈ L·t_f/R_c² (1 % relativo). O termo de 1ª ordem despreza
    # L²/R_c² (o valor exato é atan(L·t_f/(R_c² + L² − t_f²/4))): em R = 8 m isso dá ~3 %, por isso a comparação a 1 %
    # é feita em R_GRANDE = 20 m, e em R = 8 m confere-se a forma fechada exata.
    d0 = eq.deriva_ackermann(caso0, formas=v43)
    th0 = eq.angulos_velocidade(caso0)
    exato_8 = math.atan(L * TF / (R_c ** 2 + L ** 2 - TF ** 2 / 4))
    c8 = (abs((d0["FL"] - d0["FR"]) - (th0["FL"] - th0["FR"])) <= 1e-15
          and abs((d0["FL"] - d0["FR"]) - exato_8) <= 1e-12)
    rel_8 = (d0["FL"] - d0["FR"]) / (L * TF / R_c ** 2) - 1
    caso0g = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_GRANDE, ackermann_pct=0.0)
    d0g = eq.deriva_ackermann(caso0g, formas=v43)
    R_cg = math.sqrt(R_GRANDE ** 2 - B ** 2)
    rel_g = (d0g["FL"] - d0g["FR"]) / (L * TF / R_cg ** 2) - 1
    partes["c"] = c8 and abs(rel_g) <= 0.01 and d0["FL"] > 0.0 > d0["FR"]
    det.append(f"(c) R=8: ΔFL−ΔFR={d0['FL'] - d0['FR']:.6e} (rel. à 1ª ordem {rel_8:+.2%}); R=20: rel. {rel_g:+.3%}")

    # (d) curva à direita: espelhar dá a troca L↔R da esquerda; ângulos conferidos com o oráculo da curva à direita
    esp = eq.espelhar(eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, ackermann_pct=100.0, toe_rad=TOE_TESTE,
                                        cg_lateral_m=0.0))
    d_dir_real = {c: eq.deriva_ackermann(esp, formas=v43)[TROCA[c]] for c in eq.CANTOS}   # espelho FL = real FR
    d_esq_troca = {c: d43[TROCA[c]] for c in eq.CANTOS}
    ora_dir = oraculo_angulos(L, TF, TR, B, R_TESTE, -1)     # carro real, curva à direita
    th_esp = eq.angulos_velocidade(esp)
    erro_d = max(abs(th_esp[c] - (-ora_dir[TROCA[c]])) for c in eq.CANTOS)   # espelho: y → −y, ângulo → −ângulo
    partes["d"] = d_dir_real == d_esq_troca and erro_d <= 1e-12
    det.append(f"(d) troca L↔R exata={d_dir_real == d_esq_troca}, erro do oráculo à direita={erro_d:.1e}")

    # (e) v42 igual ao congelado; sem ackermann_pct, zero nas duas formas; Formas inválida recusada
    caso_toe = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, ackermann_pct=100.0, toe_rad=TOE_TESTE)
    capF = eq.capacidade_eixo(caso_toe, "F", 1.0 * G, 25)
    capR = eq.capacidade_eixo(caso_toe, "R", 1.0 * G, 25, formas=v42)
    e_ok = (eq.deriva_ackermann(caso_toe) == CONGELADO_V42["ack"]
            and eq.deriva_ackermann(caso_toe, formas=v42) == CONGELADO_V42["ack"]
            and eq.deriva_total(caso_toe) == CONGELADO_V42["tot"]
            and (capF.fy_max_N, capF.alfa_pico_rad) == CONGELADO_V42["capF"]
            and (capR.fy_max_N, capR.alfa_pico_rad) == CONGELADO_V42["capR"]
            and eq.fy_eixo(caso_toe, "F", 1.0 * G, -0.05) == CONGELADO_V42["fyF"]
            and eq.grade_alfa(caso_toe, 25)[-1] == CONGELADO_V42["grade"])
    sem_h2 = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE)
    zero = all(v == 0.0 for f in (v42, v43) for v in eq.deriva_ackermann(sem_h2, formas=f).values())
    try:
        eq.Formas("v44")
        recusa_f = False
    except ValueError:
        recusa_f = True
    partes["e"] = e_ok and zero and recusa_f and v42 == eq.Formas() and v43 == eq.Formas("v43", "v43")
    det.append(f"(e) congelado={e_ok}, zero sem h2={zero}, Formas inválida recusada={recusa_f}")

    # (f) repasse de `formas` (D1): a v43 chega a deriva_total, grade_alfa, fy_eixo, capacidade_eixo e analise_par
    tot43 = eq.deriva_total(caso_toe, formas=v43)
    d43t = eq.deriva_ackermann(caso_toe, formas=v43)
    toe = eq.deriva_toe(caso_toe)
    a_ref, ay = -0.05, 1.0 * G
    fz, gam = eq.cargas(caso_toe, ay), eq.camber(caso_toe, ay)
    fy_man = sum(tm.wheel_forces(ds, c, fz[c], a_ref + tot43[c], gam[c], 0.0)[1]
                 for c in ("FL", "FR")) * math.cos(d_ref)
    cap43 = eq.capacidade_eixo(caso_toe, "F", ay, 25, formas=v43)
    par43 = eq.analise_par(caso_toe, ay_max_g=1.0, passo_g=0.5, n_alfa=5, formas=v43)
    dois = eq.analise_par_dois_sentidos(caso_toe, ay_max_g=1.0, passo_g=0.5, n_alfa=5, formas=v43)
    partes["f"] = (all(tot43[c] == toe[c] + d43t[c] for c in eq.CANTOS) and tot43 != CONGELADO_V42["tot"]
                   and eq.fy_eixo(caso_toe, "F", ay, a_ref, formas=v43) == fy_man
                   and cap43.fy_max_N != CONGELADO_V42["capF"][0]
                   and par43.linhas[2].cap_f == cap43
                   and dois["esquerda"].linhas[2].cap_f == cap43)
    det.append(f"(f) repasse ok={partes['f']}")
    return all(partes.values()), "; ".join(det) + f" | partes={partes}"


try:
    ok_001, det_001 = tc_ack_001()
except Exception as exc:   # RED: a interface nova ainda não existe
    ok_001, det_001 = False, f"exceção {type(exc).__name__}: {exc}"
check("TC-ACK-001 Ackermann v43: oráculo ω×r, 100 % dentro da cota de 2ª ordem, 0 % = θ_FL − θ_FR, "
      "curva à direita por espelho e v42 congelada", ok_001, det_001)


# --- TC-FXI-001 e 002 (Task 4): Fx exigido por arrasto induzido ----------------------------------------------------
# Entradas SINTÉTICAS de teste (as do TC-EQ-045 de tests/test_equilibrio.py; não são do carro): R = 8 m,
# ρ = 1,2 kg/m³, CdA = 1,0 m², Crr = 0,015.
RHO_T, CDA_T, CRR_T = 1.2, 1.0, 0.015
caso_tr = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, rho_kg_m3=RHO_T, cda_m2=CDA_T, crr=CRR_T)
# Valores congelados da forma v42, medidos com o código de ANTES da Task 4 (commit ae7d8bb, 2026-10-29), em caso_tr e
# a_y = 1 g: eq.fx_exigido_traseira (algébrico: comparação exata) e eq.capacidade_eixo(…, "R", …, 25) (a força passa
# pelo pneu: 1e-12 relativo; o α do pico é um ponto da grade: exato). repr dos floats.
FX_V42_1G = 305.2313495211916
CAPR_V42_1G = (3422.7516463176694, -0.1308995)
_K_SOMA = cfg.roll_stiffness_front + cfg.roll_stiffness_rear


def veiculo_simetrico(lambda_f: float, **over) -> VehicleConfig:
    """Carro simétrico de teste (a = b = L/2), o mesmo de tests/test_equilibrio.py (TC-EQ-010 a 013); NÃO é o carro."""
    return veiculo_base(**{**dict(cg_to_front=L / 2, cg_to_rear=L / 2, track_rear=TF,
                                  roll_stiffness_front=lambda_f * _K_SOMA, roll_stiffness_rear=(1 - lambda_f) * _K_SOMA,
                                  roll_center_rear=cfg.roll_center_front, unsprung_mass_rear=cfg.unsprung_mass_front,
                                  unsprung_cg_height_rear=cfg.unsprung_cg_height_front), **over})


def _resistencias(caso, ay: float) -> float:
    """Arrasto aerodinâmico + rolamento [N], escritos aqui de novo (não vêm do equilibrio)."""
    r = 0.0
    if caso.cda_m2 is not None:
        r += 0.5 * caso.rho_kg_m3 * caso.cda_m2 * abs(ay) * caso.raio_m
    if caso.crr is not None:
        r += caso.crr * caso.cfg.mass_total * G
    return r


def _curva(caso, eixo: str, ay: float, fatores=None, formas=eq.FORMAS_V43):
    """Σ Fy do eixo em função de α_ref, com a entrada do pneu limitada à faixa (fatores: elipse por roda, ou None)."""
    rodas = eq.RODAS_DO_EIXO[eixo]
    fz_u, gam_u, _ = eq.entrada_limitada(caso, rodas, eq.cargas(caso, ay), eq.camber(caso, ay))
    return lambda a: eq.fy_eixo_limitado(caso, rodas, fz_u, gam_u, a, fatores, formas=formas)


def _pico(caso, eixo: str, ay: float, n: int, fatores=None) -> tuple[float, float]:
    """(|α| do pico, força do pico) da curva do eixo na grade_alfa de n pontos (o primeiro máximo)."""
    f = _curva(caso, eixo, ay, fatores)
    alfas = eq.grade_alfa(caso, n, formas=eq.FORMAS_V43)
    fys = [f(a) for a in alfas]
    i = max(range(n), key=fys.__getitem__)
    return abs(alfas[i]), fys[i]


def _bissecao(f, req: float, a_pico: float) -> float:
    """|α| em [0, a_pico] em que f(−|α|) alcança req (bisseção própria do teste; 0 se já alcança, pico se não)."""
    if f(-a_pico) <= req:
        return a_pico
    if f(0.0) >= req:
        return 0.0
    lo, hi = 0.0, a_pico
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if f(-mid) >= req else (mid, hi)
    return 0.5 * (lo + hi)


def ponto_fixo(caso, ay: float, tol: float = 1e-6, max_it: int = 100) -> tuple[float | None, int]:
    """Forma exata no desacoplado (spec §4.2): o α_R sai da curva traseira COM o fator da elipse da iteração.

    Fx_{k+1} = resistências + F_yf·|α_F| + F_yr·|α_R(Fx_k)|, partindo da forma sem elipse, até |ΔFx| < tol [N].
    Fator da roda c: √(1 − (Fx_k/2 / Fx_max,c)²) (diferencial aberto). Devolve (Fx, iterações) ou (None, max_it).
    """
    v43 = eq.FORMAS_V43
    req_f, req_r = eq.forca_exigida(caso, ay)
    a_f = eq.alfas_de_arrasto(caso, ay, formas=v43, n_alfa=None)[0]
    res = _resistencias(caso, ay)
    rodas = eq.RODAS_DO_EIXO["R"]
    fz_u, gam_u, _ = eq.entrada_limitada(caso, rodas, eq.cargas(caso, ay), eq.camber(caso, ay))
    fx = eq.fx_exigido_traseira(caso, ay, formas=v43)
    for it in range(1, max_it + 1):
        fat = {c: math.sqrt(1.0 - (fx / 2.0 / eq.fx_max_puro(caso.ds, fz_u[c], gam_u[c])) ** 2) for c in rodas}
        a_r = _bissecao(_curva(caso, "R", ay, fat), req_r, _pico(caso, "R", ay, 401, fat)[0])
        novo = res + req_f * a_f + req_r * a_r
        if abs(novo - fx) < tol:
            return novo, it
        fx = novo
    return None, max_it


def tc_fxi_001() -> tuple[bool, str]:
    partes, det = {}, []
    v42, v43 = eq.FORMAS_V42, eq.FORMAS_V43
    ay = 1.0 * G
    req_f, req_r = eq.forca_exigida(caso_tr, ay)
    res = _resistencias(caso_tr, ay)
    sem_lim = not eq.capacidade_eixo(caso_tr, "F", ay, 25).limites and not eq.capacidade_eixo(caso_tr, "R", ay, 25).limites

    # (a) réplica de grade × contínua: |Δ| <= (F_yf + F_yr)·h_α/2. No α contínuo a curva do eixo alcança a força
    # exigida (resíduo; fy_eixo sem limitação vale porque nenhuma entrada sai da faixa neste caso); o Fx é a soma.
    n = 25
    a_g = eq.alfas_de_arrasto(caso_tr, ay, formas=v43, n_alfa=n)
    a_c = eq.alfas_de_arrasto(caso_tr, ay, formas=v43, n_alfa=None)
    fx_g = eq.fx_exigido_traseira(caso_tr, ay, formas=v43, n_alfa=n)
    fx_c = eq.fx_exigido_traseira(caso_tr, ay, formas=v43)
    h = abs(eq.grade_alfa(caso_tr, n, formas=v43)[1])
    cota = (req_f + req_r) * h / 2.0
    resid_f = abs(eq.fy_eixo(caso_tr, "F", ay, -a_c[0], formas=v43) - req_f)
    resid_r = abs(eq.fy_eixo(caso_tr, "R", ay, -a_c[1], formas=v43) - req_r)
    soma_c = abs(fx_c - (res + req_f * a_c[0] + req_r * a_c[1])) <= 1e-12 * fx_c
    soma_g = abs(fx_g - (res + req_f * a_g[0] + req_r * a_g[1])) <= 1e-12 * fx_g
    partes["a"] = (sem_lim and abs(fx_g - fx_c) <= cota and resid_f <= 1e-6 * req_f and resid_r <= 1e-6 * req_r
                   and soma_c and soma_g and a_c[0] > 0.0 and a_c[1] > 0.0)
    det.append(f"(a) α_F={a_c[0]:.6f}, α_R={a_c[1]:.6f} rad (grade {a_g[0]:.6f}, {a_g[1]:.6f}); Fx contínuo="
               f"{fx_c:.4f} N, grade={fx_g:.4f} N, |Δ|={abs(fx_g - fx_c):.3e} <= cota={cota:.3e} N; "
               f"resíduos F={resid_f:.1e}, R={resid_r:.1e} N")

    # (b) oráculo: balanço vetorial exato em X (eq.fx_balanco_exato), independente da fórmula do arrasto induzido.
    # Em α = 0 os termos em b/R se cancelam exatamente. A diferença para o arrasto induzido tem termos
    # α·(L/R)² e α²·(L/R), além de α³: é O(ε³) com α e L/R da mesma ordem ε (a derivação de 1ª ordem da spec §4.2).
    # Por isso a razão em [6, 10] é medida escalando JUNTOS os α por 1/2 e o L/R por 1/2 (R → 2R). A razão com R
    # fixo (só os α por 1/2) é medida e impressa, sem cota: ela não cai como α³ (ver o relatório da Task 4).
    a_f, a_r = a_c
    zero = eq.fx_balanco_exato(caso_tr, ay, 0.0, 0.0)
    d1 = eq.fx_balanco_exato(caso_tr, ay, a_f, a_r) - (req_f * a_f + req_r * a_r)
    d_alfa = eq.fx_balanco_exato(caso_tr, ay, a_f / 2, a_r / 2) - (req_f * a_f / 2 + req_r * a_r / 2)
    caso_2r = dataclasses.replace(caso_tr, raio_m=2.0 * R_TESTE)
    d_conj = eq.fx_balanco_exato(caso_2r, ay, a_f / 2, a_r / 2) - (req_f * a_f / 2 + req_r * a_r / 2)
    razao_alfa, razao_conj = d1 / d_alfa, d1 / d_conj
    partes["b"] = abs(zero) <= 1e-9 * cfg.mass_total * ay and d1 != 0.0 and 6.0 <= razao_conj <= 10.0
    det.append(f"(b) oráculo em α=0: {zero:.1e} N; diferença={d1:.4e} N; razão (α e L/R por 1/2)={razao_conj:.3f}; "
               f"razão só α por 1/2 (R fixo)={razao_alfa:.3f}")

    # (c) a forma v42 é a de hoje (congelada); n_alfa não muda a v42
    fx42 = (eq.fx_exigido_traseira(caso_tr, ay), eq.fx_exigido_traseira(caso_tr, ay, formas=v42),
            eq.fx_exigido_traseira(caso_tr, ay, formas=v42, n_alfa=n))
    cr = eq.capacidade_eixo(caso_tr, "R", ay, 25)
    partes["c"] = (all(v == FX_V42_1G for v in fx42) and abs(cr.fy_max_N / CAPR_V42_1G[0] - 1.0) <= 1e-12
                   and cr.alfa_pico_rad == CAPR_V42_1G[1] and fx_c != FX_V42_1G)
    det.append(f"(c) v42={fx42[0]!r} N (congelado {FX_V42_1G!r}), cap R={cr.fy_max_N!r}")
    return all(partes.values()), "; ".join(det) + f" | partes={partes}"


def tc_fxi_002() -> tuple[bool, str]:
    partes, det = {}, []
    v42, v43 = eq.FORMAS_V42, eq.FORMAS_V43

    # (a) ponto fixo com a elipse × aproximação sem elipse (a da planilha): o erro relativo é medido e impresso; o
    # check só exige que o ponto fixo convirja e que o erro seja finito (sem cota suposta).
    ay = 1.0 * G
    fx_pf, it = ponto_fixo(caso_tr, ay)
    fx_ap = eq.fx_exigido_traseira(caso_tr, ay, formas=v43)
    erro = (fx_ap - fx_pf) / fx_pf if fx_pf is not None else math.nan
    partes["a"] = fx_pf is not None and math.isfinite(erro)
    det.append(f"(a) a_y=1 g: Fx ponto fixo={fx_pf!r} N em {it} iterações; sem elipse={fx_ap!r} N; "
               f"ERRO RELATIVO da aproximação sem elipse = {erro:+.3e}")

    # (b) LOOSE com a força traseira exigida acima do pico (LMUY = 0,45, escala só de teste do TC-EQ-011; carro
    # simétrico com λ_f = 0,3): α_R = α do pico (grade e contínuo), a capacidade da linha segue válida e o veredito é
    # LOOSE, não N/A.
    ds_l = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.45})
    caso_l = eq.CasoEquilibrio(cfg=veiculo_simetrico(0.3), ds=ds_l, raio_m=R_TESTE, rho_kg_m3=RHO_T, cda_m2=CDA_T,
                               crr=CRR_T)
    r = eq.analise_par(caso_l, formas=v43)
    # A linha escolhida tem a F_yr exigida acima dos dois picos sem elipse: o da grade de 25 (réplica de grade) e o da
    # de 401 (réplica contínua), que pode ser um pouco maior.
    linha = None
    for ln in r.linhas:
        a_p, fy_p = _pico(caso_l, "R", ln.ay_ms2, 25)
        a_p401, fy_p401 = _pico(caso_l, "R", ln.ay_ms2, 401)
        if ln.cap_r.motivo is None and ln.req_r >= max(fy_p, fy_p401):
            linha = (ln, a_p, fy_p, a_p401, fy_p401)
            break
    b_ok = r.veredito == eq.LOOSE and linha is not None
    if linha is not None:
        ln, a_p, fy_p, a_p401, fy_p401 = linha
        a_rg = eq.alfas_de_arrasto(caso_l, ln.ay_ms2, formas=v43, n_alfa=25)[1]
        a_rc = eq.alfas_de_arrasto(caso_l, ln.ay_ms2, formas=v43, n_alfa=None)[1]
        b_ok = b_ok and a_rg == a_p and a_rc == a_p401 and ln.cap_r.fy_max_N is not None
        det.append(f"(b) {r.veredito} (S_f={r.ay_sat_f / G:.4f} g, S_r={r.ay_sat_r / G:.4f} g); a_y={ln.ay_ms2 / G:.2f} g: "
                   f"F_yr exigida={ln.req_r:.1f} N >= picos sem elipse {fy_p:.1f} (25) e {fy_p401:.1f} N (401); "
                   f"α_R grade={a_rg:.6f} (pico {a_p:.6f}), contínuo={a_rc:.6f} (pico {a_p401:.6f}) rad; "
                   f"cap R da linha={ln.cap_r.fy_max_N:.1f} N")
    else:
        det.append(f"(b) veredito={r.veredito}; nenhuma linha válida com F_yr exigida acima do pico")
    partes["b"] = b_ok

    # (c) dianteira descolada numa linha (CG alto, h = 0,45 m, λ_f = 0,7: só de teste): a capacidade traseira dessa
    # linha sai None com MSG_FX_SEM_FRENTE (D3); na v42 ela é válida.
    caso_d = eq.CasoEquilibrio(cfg=veiculo_simetrico(0.7, cg_height=0.45), ds=ds, raio_m=R_TESTE, rho_kg_m3=RHO_T,
                               cda_m2=CDA_T, crr=CRR_T)
    ay_d = 1.0 * G
    fz_d = eq.cargas(caso_d, ay_d)
    rodas_r = eq.RODAS_DO_EIXO["R"]
    fz_u, gam_u, _ = eq.entrada_limitada(caso_d, rodas_r, fz_d, eq.camber(caso_d, ay_d))
    msg = eq.MSG_FX_SEM_FRENTE
    cap43 = eq.capacidade_eixo(caso_d, "R", ay_d, 25, formas=v43)
    cap42 = eq.capacidade_eixo(caso_d, "R", ay_d, 25, formas=v42)
    partes["c"] = (fz_d["FL"] <= 0.0 < min(fz_d["RL"], fz_d["RR"])
                   and msg == "Fx exigido (h9v) indisponível: a curva dianteira é inválida nesta linha"
                   and cap43 == eq.Capacidade(None, None, msg) and cap42.fy_max_N is not None
                   and eq.elipse_traseira(caso_d, ay_d, rodas_r, fz_u, gam_u, formas=v43, n_alfa=25) == (None, msg)
                   and eq.fx_exigido_traseira(caso_d, ay_d, formas=v43) == msg
                   and eq.alfas_de_arrasto(caso_d, ay_d, formas=v43, n_alfa=None) == msg)
    det.append(f"(c) Fz_FL={fz_d['FL']:.1f} N; cap R v43={cap43}; v42 válida={cap42.fy_max_N is not None}")

    # (d) achado da revisão da Task 3: o ValueError de geometria de angulos_velocidade (R <= b) chega ao motivo da
    # capacidade com a mensagem original, e não como "toe consome a faixa de α"; a v42 do mesmo caso é válida.
    caso_g = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=B, ackermann_pct=0.0)
    mot = eq.capacidade_eixo(caso_g, "F", 0.0, 25, formas=v43).motivo or ""
    partes["d"] = (mot.startswith("R ≤ b: o centro da curva não fica na linha do eixo traseiro")
                   and eq.capacidade_eixo(caso_g, "F", 0.0, 25).fy_max_N is not None)
    det.append(f"(d) motivo v43 com R = b: {mot!r}")
    return all(partes.values()), "; ".join(det) + f" | partes={partes}"


for _nome, _fn in (("TC-FXI-001 Fx v43: grade × contínua dentro da cota, oráculo vetorial O(ε³) e v42 congelada",
                    tc_fxi_001),
                   ("TC-FXI-002 Fx v43: ponto fixo com a elipse (erro medido), LOOSE com F_yr acima do pico, "
                    "sem frente sem Fx e erro de geometria com a mensagem original", tc_fxi_002)):
    try:
        _ok, _det = _fn()
    except Exception as exc:   # RED: a interface nova ainda não existe
        _ok, _det = False, f"exceção {type(exc).__name__}: {exc}"
    check(_nome, _ok, _det)

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
