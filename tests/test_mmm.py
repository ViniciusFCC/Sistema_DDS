"""
Testes do módulo mmm (Milliken Moment Method em raio fixo, incremento 6, Tasks 2 e 3).
TC-MMM-001: cinemática por roda (sinais e limite de raio grande).
TC-MMM-002: limite (T, eixo limitante, veredito, Q) com pneu de brinquedo, derivado à mão.
TC-MMM-004: K da curva de trim contra o oráculo linear (parcelas_k).
TC-MMM-005: carro simétrico (δ = L/R, Q = 0, NEUTRO, stability index nulo e com sinal pela rigidez de rolagem).
TC-MMM-006: CG lateral e espelhar contra analise_par_dois_sentidos.
TC-MMM-007: trim desacoplado (resíduos, A_Y acima do limite, caso sem raio) e o limite sem número de T
            (descolamento, toe que consome a faixa de α, pico na borda da grade).
TC-MMM-011: contrato de Hipoteses e VARIANTES.
Roda como script: uv run python -X utf8 tests/test_mmm.py
O veículo, o raio e os números abaixo são entradas de teste, não do carro.
"""

import contextlib
import dataclasses
import math
import os

import equilibrio as eq
import equilibrio_linear as eql
import mmm
import tire_model as tm
from suspension_model import VehicleConfig, G

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []

MSG_SEM_RAIO = "MMM em raio fixo exige raio_m (raio do skidpad), que está faltando."


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
        mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
        cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
        roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0,
    )
    base.update(over)
    return VehicleConfig(**base)


cfg = veiculo_base()
ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
R_TESTE = 8.5   # sintético de teste: raio do skidpad usado só nos testes, não é dado do carro
L = cfg.wheelbase
A_CG, B_CG = cfg.cg_to_front, cfg.cg_to_rear

# ---------------- TC-MMM-001 : cinemática por roda ----------------
# "A_Y → 0": a cinemática exata não depende de V (V se cancela, adendo §2.1) e, com R fixo em 8,5 m, a
# diferença entre a tangente exata e as fórmulas de ângulo pequeno do Milliken é de ordem (L/R)³ ≈ 1e-3 rad.
# Por isso o limite |α| < 1e-9 é verificado chamando a função cinemática diretamente com um raio muito grande
# (R = 1e6 m, sintético de teste), onde δ = L/R e β = b/R zeram as quatro deriva a menos de O(1/R²).
caso_grande = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=1e6)
hip_c = mmm.Hipoteses(alfa="cinematico")
al0 = mmm.alfa_rodas(caso_grande, hip_c, B_CG / 1e6, L / 1e6)
max_al0 = max(abs(v) for v in al0.values())
# Com δ + 0,01 rad: α_FL e α_FR < 0 e a Fy dianteira (ISO) > 0. Também com R grande: com R = 8,5 m o efeito das
# velocidades não paralelas nas duas dianteiras (≈ L·t/R², adendo §7) passa de 0,01 rad e deixa α_FL > 0
# (informativo no detalhe); o teste de sinal precisa de um passo maior que esse efeito, ou de R grande.
al1 = mmm.alfa_rodas(caso_grande, hip_c, B_CG / 1e6, L / 1e6 + 0.01)
caso_r = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE)
al85 = mmm.alfa_rodas(caso_r, hip_c, B_CG / R_TESTE, L / R_TESTE + 0.01)
fz_a = eq.cargas(caso_grande, 1e-6)
fy_f = sum(tm.wheel_forces(ds, c, fz_a[c], al1[c], 0.0, 0.0)[1] for c in ("FL", "FR"))
check("TC-MMM-001: δ=L/R, β=b/R, toe 0: |α|<1e-9 nas 4 rodas (R grande); com δ+0,01 rad α_FL, α_FR<0 e Fy diant.>0",
      max_al0 < 1e-9 and al1["FL"] < 0 and al1["FR"] < 0 and fy_f > 0,
      f"max|α|={max_al0:.2e} rad; α_FL={al1['FL']:.4f} α_FR={al1['FR']:.4f} rad, Fy_diant={fy_f:.1f} N (R=1e6 m); "
      f"informativo R=8,5 m: α_FL={al85['FL']:.4f} α_FR={al85['FR']:.4f} rad")

# Pneu com escala de teste (LMUY = 0,5): o mesmo expediente do test_equilibrio.py, para o eixo saturar antes da
# roda interna descolar. Escala só de teste, não é pneu do carro.
ds_teste = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.5})
hip_pl = mmm.Hipoteses.planilha()
R_GRANDE = 1e6   # sintético de teste: com R grande cos δ_ref = 1 e a hipótese 3 (cos δ_ref) não quebra a simetria


# ---------------- TC-MMM-002 : pneu de brinquedo (derivado à mão) ----------------
@contextlib.contextmanager
def pneu_de_brinquedo(lei):
    """Troca wheel_forces no mmm e no equilibrio e restaura ao sair, mesmo com erro. As duas trocas são
    necessárias: o _raiz_eixo resolve a raiz de cada eixo pelo equilibrio (capacidade_eixo, fy_eixo_limitado), e a
    reavaliação por roda do trim e do stability index usa o wheel_forces do mmm. O equilibrio não guarda cache de
    wheel_forces (o único lru_cache dele é o de _esterco_ackermann, que não depende do pneu)."""
    orig_mmm, orig_eq = mmm.wheel_forces, eq.wheel_forces
    mmm.wheel_forces = lei
    eq.wheel_forces = lei
    try:
        yield
    finally:
        mmm.wheel_forces, eq.wheel_forces = orig_mmm, orig_eq


MU_B = 1.5   # brinquedo de teste: coeficiente de atrito


def lei_saturada(a0_f, a0_r, mu_r_de_fz=None):
    """Brinquedo de teste: Fy = μ·Fz·clip(−α/α0, −1, 1) (linear até α0 e depois constante), sem sensibilidade à carga.
    Com mu_r_de_fz, as rodas traseiras usam μ(Fz) no lugar de MU_B (sensibilidade à carga só na traseira).

    Por que o patamar e não a tanh do brief: a tanh é crescente em toda a grade de α, então o máximo da grade cai na
    borda e capacidade_eixo devolve "pico na borda da grade de α" em qualquer A_Y (é exatamente o que o TC-MMM-007
    verifica com a tanh). O patamar tem o pico no primeiro ponto da grade com |α| >= α0, dentro da grade, e a
    capacidade é exatamente μ·Fz por roda (mesmo valor em todo o patamar), o que permite derivar T à mão."""
    def lei(ds_, c, fz, a, g, k):
        a0 = a0_f if c in ("FL", "FR") else a0_r
        mu = mu_r_de_fz(fz) if (mu_r_de_fz is not None and c in ("RL", "RR")) else MU_B
        return (0.0, mu * fz * max(-1.0, min(1.0, -a / a0)), {})
    return lei


def lei_tanh(ds_, c, fz, a, g, k):
    """Brinquedo de teste do brief: Fy = μ·Fz·tanh(−α/α0), μ = 1,5 e α0 = 0,1 rad. Monótona em toda a grade."""
    return (0.0, MU_B * fz * math.tanh(-a / 0.1), {})


# Veículo do brinquedo (sintético de teste): CG baixo e bitola larga, para nenhuma roda descolar nem sair da faixa
# de Fz do .tir (100 a 1521 N) até 1,6 g.
cfg_b = veiculo_base(cg_height=0.20, track_front=1.6, track_rear=1.6)
m_b, a_b, b_b, L_b = cfg_b.mass_total, cfg_b.cg_to_front, cfg_b.cg_to_rear, cfg_b.wheelbase
W_b = m_b * G
caso_b85 = eq.CasoEquilibrio(cfg=cfg_b, ds=ds, raio_m=R_TESTE)
caso_bg = eq.CasoEquilibrio(cfg=cfg_b, ds=ds, raio_m=R_GRANDE)
cos_ref = math.cos(L_b / R_TESTE)

# Derivação à mão (sem o código do mmm). Sem aero, a soma das Fz de um eixo não depende de A_Y (a transferência
# lateral só passa carga de uma roda para a outra do mesmo eixo): W_f = m·g·b/L e W_r = m·g·a/L. Em cada roda o
# patamar vale μ·Fz, logo a capacidade do eixo é μ·W_eixo, e a força exigida é m·A_Y·b/L (frente) e m·A_Y·a/L
# (traseira), isto é, W_eixo·A_Y/g. Na frente a força na direção do carro leva cos δ_ref (hipótese 3, δ_ref = L/R).
#   frente:   cos δ_ref·μ·W_f >= W_f·A_Y/g  ->  A_Y <= cos δ_ref·μ·g
#   traseira: μ·W_r          >= W_r·A_Y/g  ->  A_Y <= μ·g
# R = 1e6 m: cos δ_ref = 1, os dois eixos saturam juntos em T = μ·g -> NEUTRO. R = 8,5 m: a frente satura antes,
# T = cos δ_ref·μ·g, PUSH, eixo F; a traseira ainda tem folga μ·W_r·(1 − cos δ_ref) e, com a folga vezes o braço b
# sobre W·L, Q (cn_estabilizante) = μ·(1 − cos δ_ref)·a·b/L².
T_a_g = MU_B * G
T_a_85 = cos_ref * MU_B * G
Q_a_85 = MU_B * (1 - cos_ref) * a_b * b_b / L_b ** 2
# P (cn_p, sinal ISO): A_P com m·A_P = soma das capacidades e cn_p = (a·Fy_f,max − b·Fy_r,max)/(W·L).
# R = 8,5 m: Fy_f,max = cos δ_ref·μ·W_f e Fy_r,max = μ·W_r, com W_f = W·b/L e W_r = W·a/L; logo
#   cn_p = μ·(a·cos δ_ref·b − b·a)/L² = μ·(cos δ_ref − 1)·a·b/L²   (< 0: a frente, mais fraca, não sustenta a traseira)
# e R grande (cos δ_ref = 1): cn_p = 0.
P_a_85 = MU_B * (cos_ref - 1) * a_b * b_b / L_b ** 2
with pneu_de_brinquedo(lei_saturada(0.1, 0.1)):
    lim_a_g = mmm.limite(caso_bg, hip_pl)
    lim_a_85 = mmm.limite(caso_b85, hip_pl)
ok_a = (lim_a_g.ay_t_ms2 is not None and abs(lim_a_g.ay_t_ms2 - T_a_g) < 1e-4
        and lim_a_g.veredito == eq.NEUTRO and abs(lim_a_g.cn_estabilizante_q) < 1e-6
        and lim_a_85.ay_t_ms2 is not None and abs(lim_a_85.ay_t_ms2 - T_a_85) < 1e-4
        and lim_a_85.veredito == eq.PUSH and lim_a_85.eixo_satura == "F"
        and abs(lim_a_85.ay_sat_f - T_a_85) < 1e-4 and abs(lim_a_85.ay_sat_r - T_a_g) < 1e-4
        and abs(lim_a_85.cn_estabilizante_q - Q_a_85) < 1e-6
        and abs(lim_a_85.cn_estabilizante_q + lim_a_85.cn_iso_q) < 1e-15
        and lim_a_g.cn_p is not None and abs(lim_a_g.cn_p) < 1e-6
        and lim_a_85.cn_p is not None and abs(lim_a_85.cn_p - P_a_85) < 1e-6)

# Sensibilidade à carga só na traseira: μ_r(Fz) = μ0 − κ·Fz (κ = 3e-4 por N, brinquedo de teste), com μ0 escolhido
# para μ_r = μ na carga estática de uma roda traseira F0 = m·g·a/(2L). Capacidade do eixo traseiro (duas rodas
# F0 ± Δ, Δ = c_r·A_Y, c_r a transferência lateral por m/s² de uma roda do eixo, que é linear em A_Y):
#   Σ(μ0·Fz − κ·Fz²) = 2·μ0·F0 − κ·(2·F0² + 2·Δ²) = 3·F0 − 2·κ·c_r²·A_Y²    (porque μ0 − κ·F0 = μ)
# Exigida: m·A_Y·a/L = 2·F0·A_Y/g. Igualando: 2·κ·c_r²·A² + (2·F0/g)·A − 3·F0 = 0, cuja raiz positiva é
#   T_r = [−(2·F0/g) + √((2·F0/g)² + 24·κ·c_r²·F0)] / (4·κ·c_r²).
# A frente (sem sensibilidade) segue em μ·g, então a traseira satura antes: LOOSE, eixo limitante "R". Em T_r a
# folga da frente é μ·W_f − W_f·T_r/g, e Q (cn_estabilizante, LOOSE) = −folga·a/(W·L) = −(b/L)(a/L)(μ − T_r/g).
KAPPA = 3e-4
F0_r = m_b * G * a_b / (2.0 * L_b)
c_r = eq.cargas(caso_bg, 1.0)["RR"] - eq.cargas(caso_bg, 0.0)["RR"]   # ΔFz por m/s² de uma roda traseira
mu0_r = MU_B + KAPPA * F0_r
den_r = 4.0 * KAPPA * c_r ** 2
T_r = (-(2.0 * F0_r / G) + math.sqrt((2.0 * F0_r / G) ** 2 + 24.0 * KAPPA * c_r ** 2 * F0_r)) / den_r
Q_b = -(b_b / L_b) * (a_b / L_b) * (MU_B - T_r / G)
# P neste caso (R grande, cos δ_ref = 1): Fy_f,max = μ·W_f (W_f = m·g·b/L) e Fy_r,max(A) = 3·F0 − 2·κ·c_r²·A². De
# m·A_P = Fy_f,max + Fy_r,max sai 2·κ·c_r²·A² + m·A − (μ·W_f + 3·F0) = 0, e cn_p = (a·μ·W_f − b·Fy_r,max(A_P))/(W·L).
W_f_b = m_b * G * b_b / L_b
A_P = (-m_b + math.sqrt(m_b ** 2 + 8.0 * KAPPA * c_r ** 2 * (MU_B * W_f_b + 3.0 * F0_r))) / den_r
P_b = (a_b * MU_B * W_f_b - b_b * (3.0 * F0_r - 2.0 * KAPPA * c_r ** 2 * A_P ** 2)) / (W_b * L_b)
with pneu_de_brinquedo(lei_saturada(0.1, 0.1, lambda fz: mu0_r - KAPPA * fz)):
    lim_b = mmm.limite(caso_bg, hip_pl)
ok_b = (lim_b.ay_t_ms2 is not None and abs(lim_b.ay_t_ms2 - T_r) < 1e-4 and T_r < T_a_g - 0.1
        and lim_b.veredito == eq.LOOSE and lim_b.eixo_satura == "R"
        and abs(lim_b.ay_sat_r - T_r) < 1e-4 and abs(lim_b.ay_sat_f - T_a_g) < 1e-4
        and abs(lim_b.cn_estabilizante_q - Q_b) < 1e-6 and lim_b.cn_estabilizante_q < 0
        and lim_b.cn_p is not None and abs(lim_b.cn_p - P_b) < 1e-6)


# Stability index no brinquedo linear (A_Y = 0,5 g, α < α0 em todas as rodas, Fz do eixo constante). Com C_f e C_r a
# rigidez de eixo (μ·W_eixo/α0), c = cos δ_ref, F_f = −c·C_f·(β + a/R − δ), F_r = −C_r·(β − b/R), N = a·F_f − b·F_r e
# A_Y = (F_f + F_r)/m em δ fixo (explícito em β):
#   dN/dβ = −a·c·C_f + b·C_r  e  dA_Y/dβ = −(c·C_f + C_r)/m
#   SI (cn_estabilizante) = −(dN/dβ)/(W·L)/(dA_Y/dβ) = (b·C_r − a·c·C_f)/(g·L·(c·C_f + C_r))
# Rigidez maior na frente (α0 menor) dá SI < 0; maior atrás, SI > 0; igual e c = 1, SI = 0.
def si_a_mao(a0_f, a0_r, c):
    c_f = MU_B * (m_b * G * b_b / L_b) / a0_f
    c_r_ = MU_B * (m_b * G * a_b / L_b) / a0_r
    return (b_b * c_r_ - a_b * c * c_f) / (G * L_b * (c * c_f + c_r_))


si_resultados = {}
for nome, (a0f, a0r, caso_si, c_si) in {"frente_rigida": (0.07, 0.13, caso_b85, cos_ref),
                                        "traseira_rigida": (0.13, 0.07, caso_b85, cos_ref),
                                        "simetrico_Rgrande": (0.1, 0.1, caso_bg, 1.0)}.items():
    with pneu_de_brinquedo(lei_saturada(a0f, a0r)):
        si_resultados[nome] = (mmm.stability_index(caso_si, hip_pl, 0.5 * G), si_a_mao(a0f, a0r, c_si))
ok_si = (all(abs(v - ref) <= 1e-6 * max(abs(ref), 1e-3) for v, ref in si_resultados.values())
         and si_resultados["frente_rigida"][0] < 0 < si_resultados["traseira_rigida"][0]
         and abs(si_resultados["simetrico_Rgrande"][0]) < 1e-8)

# Restauração dos dois wheel_forces fora do bloco (a falha de um check não pode deixar o brinquedo ligado).
ok_restaura = mmm.wheel_forces is tm.wheel_forces and eq.wheel_forces is tm.wheel_forces
check("TC-MMM-002: pneu de brinquedo (μ=1,5, α0=0,1 rad; derivado à mão): R grande T=μ·g e NEUTRO; R=8,5 m "
      "T=cos δ_ref·μ·g, PUSH, Q à mão; sensibilidade à carga só na traseira -> LOOSE, eixo R, T e Q à mão; "
      "SI troca de sinal com a rigidez de eixo e é ≈ 0 no simétrico",
      ok_a and ok_b and ok_si and ok_restaura,
      f"T(R grande)={lim_a_g.ay_t_ms2:.6f} (mão {T_a_g:.6f}); T(8,5 m)={lim_a_85.ay_t_ms2:.6f} (mão {T_a_85:.6f}) "
      f"Q={lim_a_85.cn_estabilizante_q:.6f} (mão {Q_a_85:.6f}) P={lim_a_85.cn_p:.6f} (mão {P_a_85:.6f}), P(R grande)={lim_a_g.cn_p:.1e}; T_traseira={lim_b.ay_t_ms2:.6f} (mão {T_r:.6f}) "
      f"Q={lim_b.cn_estabilizante_q:.6f} (mão {Q_b:.6f}) P={lim_b.cn_p:.6f} (mão {P_b:.6f}); SI(frente rígida, traseira rígida, simétrico)="
      f"{[f'{v:.6e}' for v, _ in si_resultados.values()]} (mão {[f'{r:.6e}' for _, r in si_resultados.values()]})")

k_soma_t = 20826.4 + 26450.0


def veiculo_sim(lambda_f=0.5):
    """a = b, eixos iguais (bitola, RC, massas não suspensas) e a distribuição de rolagem lambda_f (sintético de
    teste, o mesmo desenho do veiculo_simetrico do test_equilibrio.py)."""
    return veiculo_base(cg_to_front=L / 2, cg_to_rear=L / 2, track_rear=1.200,
                        roll_stiffness_front=lambda_f * k_soma_t, roll_stiffness_rear=(1 - lambda_f) * k_soma_t,
                        roll_center_rear=0.030, unsprung_mass_rear=15.0, unsprung_cg_height_rear=0.230)


# ---------------- TC-MMM-004 : K da curva de trim contra o oráculo linear ----------------
# Caso sem aero, toe, Ackermann nem roll steer (CasoEquilibrio padrão). K = dδ/dA_Y por diferença central do trim
# comparado a equilibrio_linear.parcelas_k(...).k_total (Gillespie, cap. 6), relativo 1e-2. O stability index é outra
# grandeza (adendo §2.4) e não entra aqui. O K do trim é a tangente dδ/dA_Y e o do oráculo linear é a razão (secante)
# calculada com a rigidez do eixo na carga de A_Y, então os dois só coincidem quando A_Y → 0: o carro-base (K ≈ 0)
# passa em 0,05 g, e o segundo caso (rolagem mais rígida na frente, R grande, K maior) passa em 0,0125 g, perto do
# limite em que o passo da diferença central (0,01 g) permite. Em 0,05 g esse segundo caso difere 5,8 %: informativo.
caso_k4 = eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE)
k_mmm = mmm.k_trim(caso_k4, hip_pl, 0.05 * G)
k_lin = eql.parcelas_k(caso_k4, 0.05 * G).k_total
caso_k4b = eq.CasoEquilibrio(cfg=veiculo_sim(0.7), ds=ds_teste, raio_m=R_GRANDE)
k_mmm_b = mmm.k_trim(caso_k4b, hip_pl, 0.0125 * G)
k_lin_b = eql.parcelas_k(caso_k4b, 0.0125 * G).k_total
k_mmm_b5 = mmm.k_trim(caso_k4b, hip_pl, 0.05 * G)
k_lin_b5 = eql.parcelas_k(caso_k4b, 0.05 * G).k_total
check("TC-MMM-004: K da curva de trim em 0,05 g = parcelas_k.k_total (relativo 1e-2); idem em 0,0125 g com rolagem "
      "mais rígida na frente",
      k_lin is not None and abs(k_mmm - k_lin) <= 1e-2 * abs(k_lin)
      and k_lin_b is not None and abs(k_mmm_b - k_lin_b) <= 1e-2 * abs(k_lin_b),
      f"K_trim={k_mmm:.6e} rad/(m/s²), K_linear={k_lin:.6e}, relativo={abs(k_mmm - k_lin) / abs(k_lin):.2e}; "
      f"λf=0,7 a 0,0125 g: {k_mmm_b:.6e} vs {k_lin_b:.6e}, relativo={abs(k_mmm_b - k_lin_b) / abs(k_lin_b):.2e}; "
      f"informativo a 0,05 g: relativo={abs(k_mmm_b5 - k_lin_b5) / abs(k_lin_b5):.2e}")


# ---------------- TC-MMM-005 : carro simétrico ----------------
# A hipótese 3 (cos δ_ref só na frente) quebra a simetria por (1/cos δ_ref − 1)·|α| com R = 8,5 m: α_F > α_R e
# δ ≠ L/R. O teste da simetria usa R grande (cos δ_ref = 1, como o TC-MMM-001); o desvio com R = 8,5 m entra só como
# informação no detalhe.
caso_s = eq.CasoEquilibrio(cfg=veiculo_sim(0.5), ds=ds_teste, raio_m=R_GRANDE)
d_delta = []
for g_ay in (0.3, 0.8, 1.2):
    t_s = mmm.trim(caso_s, hip_pl, g_ay * G)
    d_delta.append(abs(t_s.delta_rad - L / R_GRANDE) if t_s.convergiu else math.inf)
lim_s = mmm.limite(caso_s, hip_pl)
si_s = mmm.stability_index(caso_s, hip_pl, 0.8 * G)
t_s85 = mmm.trim(eq.CasoEquilibrio(cfg=veiculo_sim(0.5), ds=ds_teste, raio_m=R_TESTE), hip_pl, 0.8 * G)
desvio_85 = t_s85.delta_rad - L / R_TESTE
# Rigidez de rolagem maior na frente: mais transferência de carga na frente, menos aderência na frente (subesterço,
# Gillespie p. 214), então SI (cn_estabilizante) > 0 e K > 0; maior atrás, o contrário.
casos_lf = {lf: eq.CasoEquilibrio(cfg=veiculo_sim(lf), ds=ds_teste, raio_m=R_GRANDE) for lf in (0.7, 0.3)}
si_lf = {lf: mmm.stability_index(c_, hip_pl, 0.8 * G) for lf, c_ in casos_lf.items()}
k_lf = {lf: mmm.k_trim(c_, hip_pl, 0.8 * G) for lf, c_ in casos_lf.items()}
ok_005 = (max(d_delta) < 1e-6 and lim_s.veredito == eq.NEUTRO and abs(lim_s.cn_estabilizante_q) < 1e-6
          and abs(si_s) < 1e-8 and si_lf[0.7] > 0 > si_lf[0.3] and k_lf[0.7] > 0 > k_lf[0.3])
check("TC-MMM-005: a = b e eixos iguais (R grande): δ do trim = L/R (1e-6) em 3 A_Y; |cn_estabilizante| em Q < 1e-6; "
      "NEUTRO; SI ≈ 0; rolagem mais rígida na frente -> SI e K > 0, na traseira -> < 0",
      ok_005,
      f"max|δ − L/R|={max(d_delta):.2e} rad; Q={lim_s.cn_estabilizante_q:.2e}; veredito={lim_s.veredito}; "
      f"SI sim={si_s:.2e}, SI(λf=0,7)={si_lf[0.7]:.3e}, SI(λf=0,3)={si_lf[0.3]:.3e}; "
      f"K(0,7)={k_lf[0.7]:.3e}, K(0,3)={k_lf[0.3]:.3e}; informativo R=8,5 m: δ − L/R={desvio_85:.3e} rad")


# ---------------- TC-MMM-006 : CG lateral e espelhar ----------------
# Roll stiffness dianteira de 23700 N·m/rad (sintético de teste): perto do neutro com o pneu de teste, para o CG
# lateral de 0,06 m (sintético de teste) decidir o veredito em cada sentido (esquerda PUSH, direita LOOSE).
caso_cg = eq.CasoEquilibrio(cfg=veiculo_base(roll_stiffness_front=23700.0), ds=ds_teste, raio_m=R_TESTE,
                            cg_lateral_m=0.06)
# O oráculo é analise_par_dois_sentidos com a MESMA grade de α do limite (n_alfa = 401) e passo de a_y de 0,01 g, e a
# tolerância é a resolucao_ms2 que o próprio analise_par calcula (spec §5.1). Com a grade padrão dele (n_alfa = 25,
# passo 0,05 g) a diferença é de ~3e-3 m/s², 100 vezes a resolucao_ms2 dele: vem da grade de α (a coarse subestima o
# pico), e não da física; ver o detalhe (informativo).
ref_cg = eq.analise_par_dois_sentidos(caso_cg, n_alfa=401, passo_g=0.01)
ref_cg_padrao = eq.analise_par_dois_sentidos(caso_cg)
lim_esq = mmm.limite(caso_cg, hip_pl)
lim_dir = mmm.limite(eq.espelhar(caso_cg), hip_pl)
ok_006 = True
dets_006 = []
for lim_x, ref_x, ref_p in ((lim_esq, ref_cg["esquerda"], ref_cg_padrao["esquerda"]),
                            (lim_dir, ref_cg["direita"], ref_cg_padrao["direita"])):
    dif_t = abs(lim_x.ay_t_ms2 - ref_x.ay_lim) if lim_x.ay_t_ms2 is not None and ref_x.ay_lim is not None else math.inf
    ok_006 = (ok_006 and lim_x.veredito == ref_x.veredito == ref_p.veredito and dif_t <= ref_x.resolucao_ms2)
    dets_006.append(f"{lim_x.veredito} T={lim_x.ay_t_ms2:.6f}, analise_par {ref_x.veredito} {ref_x.ay_lim:.6f}, "
                    f"|dif|={dif_t:.2e} (res {ref_x.resolucao_ms2:.2e}); informativo grade padrão: "
                    f"|dif|={abs(lim_x.ay_t_ms2 - ref_p.ay_lim):.2e} (res {ref_p.resolucao_ms2:.2e})")
ok_006 = (ok_006 and lim_esq.veredito == eq.PUSH and lim_dir.veredito == eq.LOOSE
          and lim_esq.cn_iso_q * lim_dir.cn_iso_q < 0 and lim_esq.cn_iso_q < 0 < lim_dir.cn_iso_q
          and lim_esq.cn_estabilizante_q > 0 > lim_dir.cn_estabilizante_q)
check("TC-MMM-006: CG lateral ≠ 0 + espelhar: T e veredito de cada sentido = analise_par_dois_sentidos (mesma grade de "
      "α, dentro da resolucao_ms2 dele); cn_iso com sinais opostos entre push e loose; cn_estabilizante > 0 no push",
      ok_006,
      f"esquerda: {dets_006[0]}; direita: {dets_006[1]}; cn_iso(esq,dir)=({lim_esq.cn_iso_q:.5f}, "
      f"{lim_dir.cn_iso_q:.5f}); cn_est=({lim_esq.cn_estabilizante_q:.5f}, {lim_dir.cn_estabilizante_q:.5f})")


# ---------------- TC-MMM-007 : trim desacoplado ----------------
def resíduos(caso_x, tr):
    soma_fy = sum(tr.fy.values())
    n_nm = mmm.cn(tr, caso_x)[0] * caso_x.cfg.mass_total * G * caso_x.cfg.wheelbase
    return abs(soma_fy - caso_x.cfg.mass_total * tr.ay_ms2), abs(n_nm)


caso_t = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45)
caso_k = eq.CasoEquilibrio(   # toe, Ackermann 50 % e tração na traseira (valores de teste)
    cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
    toe_rad={"FL": 0.003, "FR": 0.003, "RL": 0.002, "RR": 0.002}, ackermann_pct=50.0,
    rho_kg_m3=1.2, cda_m2=1.0, crr=0.02)
rs = []
for caso_x, g_ay in ((caso_t, 0.5), (caso_t, 1.0), (caso_k, 0.8)):
    tr = mmm.trim(caso_x, hip_pl, g_ay * G)
    rs.append((tr.convergiu, *(resíduos(caso_x, tr) if tr.convergiu else (math.inf, math.inf))))
ok_res = all(c and rf < 1e-6 and rn < 1e-6 for c, rf, rn in rs)
tr_alto = mmm.trim(caso_t, hip_pl, 5.0 * G)
ok_alto = (not tr_alto.convergiu and bool(tr_alto.motivo) and tr_alto.delta_rad is None and tr_alto.beta_rad is None
           and tr_alto.alfa is None and tr_alto.fz is None and tr_alto.fy is None and tr_alto.fx is None
           and tr_alto.kappa is None and tr_alto.residuo_N is None)
# Sem raiz de verdade (sem descolamento): bitola larga de teste (2,4 m / 2,3 m, sintética) e 3 g, acima da capacidade.
caso_larga = eq.CasoEquilibrio(cfg=veiculo_base(track_front=2.4, track_rear=2.3), ds=ds, raio_m=R_TESTE,
                               downforce_N=400.0, aero_balance_front=0.45)
tr_raiz = mmm.trim(caso_larga, hip_pl, 3.0 * G)
ok_raiz = (not tr_raiz.convergiu and tr_raiz.eixo_sem_raiz in ("F", "R", "F+R") and bool(tr_raiz.motivo)
           and tr_raiz.fy is None and mmm.trim(caso_larga, hip_pl, 1.8 * G).convergiu)
ok_alto = ok_alto and ok_raiz
caso_sem = eq.CasoEquilibrio(cfg=cfg, ds=ds)
ok_raio = raises(lambda: mmm.trim(caso_sem, hip_pl, 1.0 * G), ValueError, MSG_SEM_RAIO)
ok_acopl = raises(lambda: mmm.trim(caso_t, mmm.Hipoteses(cos_delta="trim"), 1.0 * G), NotImplementedError, "Task 4")

# Review Focus 2: descolamento antes da saturação. Bitola estreita e CG alto (sintético de teste): a roda interna
# descola antes de qualquer eixo saturar. O limite não dá número de T: veredito N/A com o motivo de
# equilibrio.descolamento e o último A_Y válido; o analise_par também dá N/A com o mesmo motivo.
caso_desc = eq.CasoEquilibrio(cfg=veiculo_base(track_front=0.9, track_rear=0.9, cg_height=0.45), ds=ds_teste,
                              raio_m=R_TESTE)
lim_desc = mmm.limite(caso_desc, hip_pl)
par_desc = eq.analise_par(caso_desc)
ok_desc = (lim_desc.veredito == eq.NA and lim_desc.ay_t_ms2 is None and lim_desc.cn_iso_q is None
           and lim_desc.cn_estabilizante_q is None and lim_desc.cn_p is None and lim_desc.eixo_satura is None
           and "descolamento" in (lim_desc.motivo or "") and "último a_y válido" in lim_desc.motivo
           and par_desc.veredito == eq.NA and "descolamento" in (par_desc.motivo or ""))
# Review Focus 3: toe que consome a faixa de α (o toe de 0,30 rad passa de |ALPMIN| = 0,2618 rad) e pico na borda da
# grade de α (a tanh do brief é crescente em toda a grade). Nenhum número de T; o motivo é o de capacidade_eixo.
caso_toe = eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, toe_rad={c_: 0.30 for c_ in eq.CANTOS})
lim_toe = mmm.limite(caso_toe, hip_pl)
with pneu_de_brinquedo(lei_tanh):
    lim_borda = mmm.limite(caso_bg, hip_pl)
ok_toe = (lim_toe.veredito == eq.NA and lim_toe.ay_t_ms2 is None and "toe consome a faixa de α" in (lim_toe.motivo or "")
          and lim_borda.veredito == eq.NA and lim_borda.ay_t_ms2 is None and lim_borda.cn_p is None
          and "pico na borda da grade de α" in (lim_borda.motivo or ""))
check("TC-MMM-007: no trim |ΣFy−m·A_Y|<1e-6 N e |N|<1e-6 N·m; A_Y acima do limite -> convergiu=False com motivo e "
      "campos None; sem raio_m -> ValueError; acoplada -> NotImplementedError (Task 4); limite: descolamento, toe "
      "que consome a faixa e pico na borda -> N/A com o motivo de capacidade_eixo e sem T",
      ok_res and ok_alto and ok_raio and ok_acopl and ok_desc and ok_toe,
      f"resíduos(F,N)={[(f'{rf:.1e}', f'{rn:.1e}') for _, rf, rn in rs]}; motivo(5g)={tr_alto.motivo!r}; "
      f"eixo_sem_raiz={tr_alto.eixo_sem_raiz}; descolamento: {lim_desc.motivo!r}; toe: {lim_toe.motivo!r}; "
      f"borda: {lim_borda.motivo!r}")

# ---------------- TC-MMM-011 : contrato de Hipoteses e VARIANTES ----------------
campos = {f.name for f in dataclasses.fields(mmm.Hipoteses)}
ok_campos = set(mmm.VARIANTES) == campos - {"h_cp_m"}
ok_hip = all(set(v["hipoteses"]) <= {1, 2, 3, 7, 9, 10, 11} for v in mmm.VARIANTES.values())
ok_valor = raises(lambda: mmm.Hipoteses(alfa="x"), ValueError, "alfa")
ok_py = mmm.Hipoteses.python_completo() == mmm.Hipoteses(
    alfa="cinematico", cos_delta="trim", sentido="dois", fx_exigido="balanco", tracao="pac2002",
    diferencial="travado", transf_long="regime")
ok_nomes = {v["nome"] for v in mmm.VARIANTES.values()} == {"1+2", "3", "7", "9a", "9b", "10", "11"}
ok_var = all(v["planilha"] == getattr(hip_pl, k) and v["python"] == getattr(mmm.Hipoteses.python_completo(), k)
             for k, v in mmm.VARIANTES.items())
check("TC-MMM-011: VARIANTES = campos de Hipoteses (sem h_cp_m); hipóteses ⊂ {1,2,3,7,9,10,11}; "
      "Hipoteses(alfa='x') -> ValueError",
      ok_campos and ok_hip and ok_valor and ok_py and ok_nomes and ok_var,
      f"campos={sorted(campos)}")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
