"""
Testes das formas v43 do equilíbrio (incremento 7; EDR-066, EDR-067, decisão D1 do plano).
TC-ACK-001: Ackermann com o centro da curva na linha do eixo traseiro (spec §3.1 e §4.1; Task 3).
TC-ACK-002 e TC-FXI entram nas Tasks 4 e 5.
Roda como script: uv run python -X utf8 tests/test_formas_v43.py

O veículo (L, b, bitolas) e os raios abaixo são entradas SINTÉTICAS de teste (o veiculo_base do
tests/test_equilibrio.py), não do carro; o .tir é o provisório do TTC.
"""
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

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
