"""
Testes do módulo mmm (Milliken Moment Method em raio fixo, incremento 6, Tasks 2 e 3).
TC-MMM-001: cinemática por roda (sinais e limite de raio grande).
TC-MMM-002: limite (T, eixo limitante, veredito, Q) com pneu de brinquedo, derivado à mão.
TC-MMM-004: K da curva de trim contra o oráculo linear (parcelas_k).
TC-MMM-005: carro simétrico (δ = L/R, Q = 0, NEUTRO, stability index nulo e com sinal pela rigidez de rolagem).
TC-MMM-006: CG lateral e espelhar contra analise_par_dois_sentidos.
TC-MMM-007: trim desacoplado (resíduos, A_Y acima do limite, caso sem raio) e o limite sem número de T
            (descolamento, toe que consome a faixa de α, pico na borda da grade); Task 4: trim da variante Python
            completa com os resíduos de força e momento em eixos do carro (adendo §2.5) e o limite acoplado
            (saturação por eixo da decisão 3 do plano, derivado à mão com o pneu de brinquedo).
TC-MMM-008: α cinemático (Ackermann 100 %, sinal de y em R finito) contra a variante planilha.
TC-MMM-009: diferencial travado (contribuição de Fx ao N) e tração acima do atrito (PAC2002).
TC-MMM-011: contrato de Hipoteses e VARIANTES.
Roda como script: uv run python -X utf8 tests/test_mmm.py
O veículo, o raio e os números abaixo são entradas de teste, não do carro.
"""

import contextlib
import dataclasses
import math
import os
import time

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
# calculada com a rigidez do eixo na carga de A_Y, então os dois só coincidem quando A_Y → 0, com diferença O(A_Y^p)
# (p ≈ 2 esperado). O carro-base (K ≈ 0) passa direto em 0,05 g (relativo 1e-2). O segundo caso (rolagem mais rígida
# na frente, R grande, K maior) é um oráculo de convergência: e_rel(A) = |K_trim − K_lin|/|K_lin| em 0,05, 0,025 e
# 0,0125 g (0,0125 g é o menor A seguro: k_trim exige A > passo de 0,01 g) deve cair monotonicamente, e a diferença
# assinada d(A) = (K_trim − K_lin)/|K_lin|, extrapolada para A → 0 pelo polinômio quadrático pelos três pontos
# (d = d0 + c1·A + c2·A²), deve ficar em |d(0)| ≤ 1e-2 (a tolerância não é afrouxada). Richardson com a ordem
# observada dos mesmos pontos daria d(0) = 0 por construção quando d tem sinal constante: não testaria nada. A ordem
# observada p = log2(e(0,025)/e(0,0125)) entra só como informação.
caso_k4 = eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE)
k_mmm = mmm.k_trim(caso_k4, hip_pl, 0.05 * G)
k_lin = eql.parcelas_k(caso_k4, 0.05 * G).k_total
caso_k4b = eq.CasoEquilibrio(cfg=veiculo_sim(0.7), ds=ds_teste, raio_m=R_GRANDE)
d_conv = []  # d(A) assinada em 0,05, 0,025 e 0,0125 g
for g_a in (0.05, 0.025, 0.0125):
    k_t_b = mmm.k_trim(caso_k4b, hip_pl, g_a * G)
    k_l_b = eql.parcelas_k(caso_k4b, g_a * G).k_total
    d_conv.append((k_t_b - k_l_b) / abs(k_l_b))
e_conv = [abs(d) for d in d_conv]
ok_conv = e_conv[0] > e_conv[1] > e_conv[2] > 0.0
p_obs = math.log2(e_conv[1] / e_conv[2]) if ok_conv else math.nan
# Lagrange em u = A/0,0125 g = 4, 2, 1 avaliado em u = 0: d(0) = (8/3)·d(1) − 2·d(2) + (1/3)·d(4).
d_zero = (8.0 / 3.0) * d_conv[2] - 2.0 * d_conv[1] + d_conv[0] / 3.0
check("TC-MMM-004: K da curva de trim em 0,05 g = parcelas_k.k_total (relativo 1e-2); com rolagem mais rígida na "
      "frente (λf=0,7), erro relativo cai com A_Y (0,05 > 0,025 > 0,0125 g) e a diferença extrapolada a A_Y → 0 é ≤ 1e-2",
      k_lin is not None and abs(k_mmm - k_lin) <= 1e-2 * abs(k_lin)
      and ok_conv and abs(d_zero) <= 1e-2,
      f"K_trim={k_mmm:.6e} rad/(m/s²), K_linear={k_lin:.6e}, relativo={abs(k_mmm - k_lin) / abs(k_lin):.2e}; "
      f"λf=0,7: e_rel(0,05; 0,025; 0,0125 g)=({e_conv[0]:.2e}; {e_conv[1]:.2e}; {e_conv[2]:.2e}), "
      f"d assinada=({d_conv[0]:.2e}; {d_conv[1]:.2e}; {d_conv[2]:.2e}), ordem observada p={p_obs:.3f}, "
      f"d(0) extrapolada (quadrática)={d_zero:.2e} (limite 1e-2)")


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


# ---------------- TC-MMM-003 : força bruta numa grade β × δ via ponto ----------------
# Pneu com escala de teste (ds_teste, LMUY = 0,5, sintético de teste) e downforce de 400 N (sintético de teste), para o
# carro saturar abaixo de 3 g. Sem capacidade_eixo: só `ponto` (trim lateral em (β, δ) fixos). Faixa da grade: o trim
# (limite -> T; trim em A_Y = 0,01·G, 0,1·T, ..., 0,999·T) dá o (β, δ) de cada A_Y de 0 a T; a faixa de cada variável é a
# do mínimo ao máximo desses trims, estendida em 30 % da amplitude para cada lado (margem para o cruzamento de C_N = 0
# acima de T e para a interpolação). Cruzamentos de C_N = 0: entre vizinhos da grade (em β e em δ) com C_N de sinais
# opostos, A_Y por interpolação linear no ponto de C_N = 0. O maior A_Y desses cruzamentos é o T da força bruta.
caso_003 = eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45)
lim_003 = mmm.limite(caso_003, hip_pl)
T3 = lim_003.ay_t_ms2
trs_003 = [mmm.trim(caso_003, hip_pl, a) for a in [0.01 * G] + [f * T3 for f in (0.1, 0.25, 0.5, 0.75, 0.9, 0.999)]]
N3 = 41


def faixa_003(vals, margem=0.3):
    lo, hi = min(vals), max(vals)
    return lo - margem * (hi - lo), hi + margem * (hi - lo)


b_lo, b_hi = faixa_003([t_.beta_rad for t_ in trs_003])
d_lo, d_hi = faixa_003([t_.delta_rad for t_ in trs_003])
betas_003 = [b_lo + (b_hi - b_lo) * i / (N3 - 1) for i in range(N3)]
deltas_003 = [d_lo + (d_hi - d_lo) * i / (N3 - 1) for i in range(N3)]
t_ini = time.time()
pts_003 = mmm.diagrama(caso_003, hip_pl, betas_003, deltas_003)
seg_003 = time.time() - t_ini
grade_003 = [[pts_003[i * N3 + j] for j in range(N3)] for i in range(N3)]
cruz_003 = []


def cruza(p, q):
    if p.ay_ms2 is None or q.ay_ms2 is None or not p.cn_iso * q.cn_iso < 0.0:
        return
    w = -p.cn_iso / (q.cn_iso - p.cn_iso)
    cruz_003.append(p.ay_ms2 + w * (q.ay_ms2 - p.ay_ms2))


for i in range(N3):
    for j in range(N3):
        if i + 1 < N3:
            cruza(grade_003[i][j], grade_003[i + 1][j])
        if j + 1 < N3:
            cruza(grade_003[i][j], grade_003[i][j + 1])
t_bruta = max(cruz_003) if cruz_003 else None
res_003 = lim_003.resolucao_ms2
check("TC-MMM-003: força bruta 41 × 41 em β × δ via ponto (sem capacidade_eixo): o maior A_Y nos cruzamentos de C_N = 0 "
      "(interpolação linear entre vizinhos) fica em [0,97·T, T + resolucao_ms2]",
      t_bruta is not None and 0.97 * T3 <= t_bruta <= T3 + res_003,
      f"T={T3 / G:.5f} g; força bruta={t_bruta / G:.5f} g (razão {t_bruta / T3:.5f}; {len(cruz_003)} cruzamentos); "
      f"β=[{math.degrees(b_lo):.3f}°, {math.degrees(b_hi):.3f}°], δ=[{math.degrees(d_lo):.3f}°, "
      f"{math.degrees(d_hi):.3f}°]; {sum(p.ay_ms2 is None for p in pts_003)} pontos sem raiz; diagrama em {seg_003:.1f} s; "
      f"rótulo: {mmm.ROTULO_DIAGRAMA}")


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

# ---- Task 4: variantes acopladas ----
# Eixos do carro (adendo §2.5): a_x = −A·sen β e a_y = A·cos β, com A = V²/R o A_Y do trim. Resíduos calculados AQUI, das
# forças por roda do Trim e do δ_i de cada roda dianteira, sem helper do módulo:
#   longitudinal: ΣFx_carro − D − RR + m·A·sen β = 0, com a dianteira em −Fy_roda·sen δ_i (Fx_roda dianteiro = 0 em κ = 0,
#                 Fy_roda = fy_carro/cos δ_i) e a traseira em Fx; D = ½ρ·CdA·A·R e RR = Crr·m·g saem dos campos do caso;
#   lateral:      ΣFy_carro − m·A·cos β = 0 (a_y = A·cos β, §2.5);
#   guinada:      N = Σ(x_i·Fy_i − y_i·Fx_i) = 0 (x = +a em FL e FR, −b atrás; y = +t/2 em FL e RL, −t/2 em FR e RR).
CANTOS_T = ("FL", "FR", "RL", "RR")


def residuos_carro(caso_x, tr):
    c_, m_, A_, b_ = caso_x.cfg, caso_x.cfg.mass_total, tr.ay_ms2, tr.beta_rad
    d_ar = 0.5 * caso_x.rho_kg_m3 * caso_x.cda_m2 * A_ * caso_x.raio_m
    rr_ = caso_x.crr * m_ * G
    xs_ = {"FL": c_.cg_to_front, "FR": c_.cg_to_front, "RL": -c_.cg_to_rear, "RR": -c_.cg_to_rear}
    ys_ = {"FL": c_.track_front / 2, "FR": -c_.track_front / 2, "RL": c_.track_rear / 2, "RR": -c_.track_rear / 2}
    fx_car = {c: -(tr.fy[c] / math.cos(tr.delta_rodas[c])) * math.sin(tr.delta_rodas[c]) for c in ("FL", "FR")}
    fx_car.update({c: tr.fx[c] for c in ("RL", "RR")})
    dif_fx = max(abs(fx_car[c] - tr.fx[c]) for c in ("FL", "FR"))   # o Trim.fx dianteiro é o da reconstituição
    res_x = sum(fx_car.values()) - d_ar - rr_ + m_ * A_ * math.sin(b_)
    res_y = sum(tr.fy.values()) - m_ * A_ * math.cos(b_)
    n_ = sum(xs_[c] * tr.fy[c] - ys_[c] * fx_car[c] for c in CANTOS_T)
    return abs(res_x), abs(res_y), abs(n_), dif_fx


hip_pc = mmm.Hipoteses.python_completo()
# Escala de teste do pneu (LMUY = 0,6, sintético de teste): com o pneu cheio o carro-base não satura até 2 g, e com 0,5 o
# diferencial travado (Δκ ≈ t/R, adendo §6) tira a traseira do ramo ascendente já em 0,8 g.
ds_pc = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.6})
caso_pc = eq.CasoEquilibrio(cfg=cfg, ds=ds_pc, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
                            rho_kg_m3=1.2, cda_m2=1.0, crr=0.02)   # sintético de teste
caso_pc_ack = eq.CasoEquilibrio(   # idem com toe e Ackermann 50 % (δ_i diferentes nas duas dianteiras), sintético de teste
    cfg=cfg, ds=ds_pc, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
    toe_rad={"FL": 0.003, "FR": 0.003, "RL": 0.002, "RR": 0.002}, ackermann_pct=50.0,
    rho_kg_m3=1.2, cda_m2=1.0, crr=0.02)
lim_pc = mmm.limite(caso_pc, hip_pc)
res_pc, det_pc = [], []
for caso_x, f_t in ((caso_pc, 0.5), (caso_pc_ack, 0.5)):
    t_x = lim_pc.ay_t_ms2 if caso_x is caso_pc else mmm.limite(caso_x, hip_pc).ay_t_ms2
    tr_x = mmm.trim(caso_x, hip_pc, f_t * t_x)
    r_x = residuos_carro(caso_x, tr_x) if tr_x.convergiu else (math.inf,) * 4
    res_pc.append((tr_x.convergiu, *r_x))
    det_pc.append(f"T={t_x / G:.4f} g, δ_FL={math.degrees(tr_x.delta_rodas['FL']):.3f}° "
                  f"δ_FR={math.degrees(tr_x.delta_rodas['FR']):.3f}°, β={math.degrees(tr_x.beta_rad):.3f}°, "
                  f"resíduos(Fx,Fy,N,Δfx)={[f'{v:.1e}' for v in r_x]}")
ok_pc = all(c and rx < 1e-6 and ry < 1e-6 and rn < 1e-6 and dfx < 1e-9 for c, rx, ry, rn, dfx in res_pc)
# Review Focus: o par de rodas dianteiras com Ackermann tem δ_i diferentes (se fossem iguais, o teste do δ_i por roda
# não distinguiria a roda), e o δ do trim é maior que L/R (a hipótese 3 muda o resultado: sen δ_trim ≠ sen δ_ref).
tr_ack = mmm.trim(caso_pc_ack, hip_pc, 0.5 * mmm.limite(caso_pc_ack, hip_pc).ay_t_ms2)
ok_pc = ok_pc and abs(tr_ack.delta_rodas["FL"] - tr_ack.delta_rodas["FR"]) > 1e-3 and tr_ack.delta_rodas["FL"] > tr_ack.delta_rodas["FR"]

# Limite acoplado (decisão 3 do plano), pneu de brinquedo e cos δ do trim, derivado à mão (R = 8,5 m). O brinquedo satura
# cada roda em |α| = α0 (patamar) e, no regime linear, Fy_roda = μ·Fz·s com s = −α/α0 (0 <= s <= 1). Sem toe, Ackermann, aero
# nem tração, e só com cos_delta = "trim": a frente tem as duas rodas com o mesmo s_f, e a traseira s_r.
# O caminho acoplado aplica SEMPRE a_y = A·cos β (adendo §2.5; antes só com tração ativa ou regime), e a transferência lateral
# de carga segue a_y = A·cos β. Esta derivação tinha a_y = A; o fator cos β entra abaixo e é a única mudança dela.
#   Forças nos eixos do carro: F_f = cos δ·μ·W_f·s_f; F_r = μ·W_r·s_r; a parcela longitudinal da dianteira, −Fy_roda·sen δ,
#   tem braço y_i e entra no momento: N_x = Σ y_i·Fy_roda,i·sen δ = −sen δ·μ·s_f·t_f·c_f·a_y, onde c_f é a transferência lateral de
#   carga de UMA roda dianteira por m/s² (Fz_FL − Fz_FR = −2·c_f·a_y; a roda interna é a FL) e a_y = A·cos β.
#   Equilíbrio: (1) F_f + F_r = m·a_y e (2) N = a·F_f − b·F_r + N_x = 0. Cinemática: α_F = β + a/R − δ, α_R = β − b/R, logo
#   δ = L/R + α0·(s_f − s_r) e β = b/R − α0·s_r. No limite a frente satura: s_f = 1.
#   De (2) com a·W_f = b·W_r: s_r = cos δ − sen δ·t_f·c_f·a_y/(b·W_r); de (1): a_y = μ·g·(cos δ·b/L + (a/L)·s_r), o que dá
#       a_y = μ·g·cos δ / (1 + μ·t_f·c_f·sen δ/(b·m))   e   A = a_y/cos β.
#   Ponto fixo em (δ, β) por iteração (δ → a_y → s_r → δ, β). A frente satura primeiro (PUSH) e a traseira ainda tem a folga
#   μ·W_r·(1 − s_r); Q (cn_estabilizante) = folga·b/(W·L). A diferença para o resultado sem N_x é de ~0,5 %.
a0_t = 0.1
c_f = (eq.cargas(caso_b85, 1.0)["FR"] - eq.cargas(caso_b85, 1.0)["FL"]) / 2.0
d_star = L_b / R_TESTE
for _ in range(500):
    ay_it = MU_B * G * math.cos(d_star) / (1.0 + MU_B * cfg_b.track_front * c_f * math.sin(d_star) / (b_b * m_b))
    W_f_t, W_r_t = W_b * b_b / L_b, W_b * a_b / L_b
    s_r_it = (m_b * ay_it / MU_B - math.cos(d_star) * W_f_t) / W_r_t
    d_star = L_b / R_TESTE + a0_t * (1.0 - s_r_it)
    beta_star = b_b / R_TESTE - a0_t * s_r_it
T_acopl = ay_it / math.cos(beta_star)
T_acopl_sem_rot = ay_it   # o valor da derivação antiga (a_y = A), só para o detalhe
Q_acopl = MU_B * W_r_t * (1.0 - s_r_it) * b_b / (W_b * L_b)
hip_cd = mmm.Hipoteses(cos_delta="trim")
with pneu_de_brinquedo(lei_saturada(a0_t, a0_t)):
    lim_cd = mmm.limite(caso_b85, hip_cd)
    lim_cd_g = mmm.limite(caso_bg, hip_cd)
MSG_ACOPLADO = "acoplado: além de T não há trim"
ok_lim_a = (lim_cd.ay_t_ms2 is not None and abs(lim_cd.ay_t_ms2 - T_acopl) < 1e-4
            and lim_cd.veredito == eq.PUSH and lim_cd.eixo_satura == "F"
            and lim_cd.ay_sat_f is not None and abs(lim_cd.ay_sat_f - lim_cd.ay_t_ms2) < 1e-12
            and lim_cd.ay_sat_r is None and lim_cd.motivo_sat == MSG_ACOPLADO
            and abs(lim_cd.cn_estabilizante_q - Q_acopl) < 1e-5)
# R grande: cos δ = 1, os dois eixos saturam juntos com a_y = μ·g e a folga do outro eixo em T é ≤ (força exigida por
# m/s²)·res -> NEUTRO; o eixo que satura tem ay_sat = T e o outro None com o mesmo motivo. Com a rotação sempre ligada no
# caminho acoplado (a_y = A·cos β), o A de T é μ·g/cos β, e no brinquedo as duas traseiras saturam em α_R = −α0 (s_r = 1): com
# R grande β = b/R − α0 ≈ −0,1 rad, logo T = μ·g/cos(b/R − α0). Antes do EDR-064 esta linha esperava T = μ·g (a_y = A).
T_n_rot = T_a_g / math.cos(b_b / R_GRANDE - a0_t)
ok_lim_n = (lim_cd_g.ay_t_ms2 is not None and abs(lim_cd_g.ay_t_ms2 - T_n_rot) < 1e-4 and lim_cd_g.veredito == eq.NEUTRO
            and lim_cd_g.motivo_sat == MSG_ACOPLADO
            and sorted(x is None for x in (lim_cd_g.ay_sat_f, lim_cd_g.ay_sat_r)) == [False, True])
# A variante Python completa no limite não pode lançar nem devolver T sem motivo; o trim em A_Y acima de T não converge.
tr_acima = mmm.trim(caso_pc, hip_pc, 1.05 * lim_pc.ay_t_ms2)
ok_acima = (not tr_acima.convergiu and bool(tr_acima.motivo) and tr_acima.fy is None and tr_acima.delta_rodas is None
            and lim_pc.ay_t_ms2 is not None and lim_pc.veredito in (eq.PUSH, eq.LOOSE, eq.NEUTRO))
ok_acopl = (mmm.trim(caso_t, mmm.Hipoteses(cos_delta="trim"), 1.0 * G).convergiu
            and mmm.trim(caso_t, mmm.Hipoteses(cos_delta="trim"), 1.0 * G).delta_rodas is not None
            and mmm.trim(caso_t, hip_pl, 1.0 * G).delta_rodas is None)

# Rotação β sempre no caminho acoplado (adendo §2.5, EDR-064): mesmo com as hipóteses da planilha, o trim acoplado (a linha
# de controle mmm.planilha_acoplada()) fecha ΣFy = m·A·cos β (a_y = A·cos β), e o desacoplado fecha ΣFy = m·A. A diferença
# entre os dois é o viés da rotação (fator cos β); o N fecha em 1e-6 N·m. A linha de controle fica fora de VARIANTES e de
# fields(Hipoteses) (subclasse privada) e leva o trim ao Newton 2-D (delta_rodas não é None).
tr_ctrl = mmm.trim(caso_t, mmm.planilha_acoplada(), 1.0 * G)
tr_desac = mmm.trim(caso_t, hip_pl, 1.0 * G)
res_y_ctrl = abs(sum(tr_ctrl.fy.values()) - cfg.mass_total * tr_ctrl.ay_ms2 * math.cos(tr_ctrl.beta_rad))
res_y_desac = abs(sum(tr_desac.fy.values()) - cfg.mass_total * tr_desac.ay_ms2)
res_y_sem_cos = abs(sum(tr_ctrl.fy.values()) - cfg.mass_total * tr_ctrl.ay_ms2)   # sem o cos β: tem de passar de 1e-3 N
ok_rot = (tr_ctrl.convergiu and tr_desac.convergiu and tr_ctrl.delta_rodas is not None and abs(tr_ctrl.beta_rad) > 1e-3
          and res_y_ctrl < 1e-6 and res_y_desac < 1e-6 and res_y_sem_cos > 1e-3
          and abs(mmm.cn(tr_ctrl, caso_t)[0] * cfg.mass_total * G * cfg.wheelbase) < 1e-6)

# Estrutura da falha (Trim.causa): o limite acoplado decide por ela, e não pelo texto do motivo. Descolamento é "dominio";
# eixo sem raiz (caso_larga a 3 g) é a saturação, causa None com eixo_sem_raiz.
ok_causa = (tr_alto.causa == "dominio" and tr_alto.eixo_sem_raiz is None
            and tr_raiz.causa is None and tr_raiz.eixo_sem_raiz is not None
            and mmm.trim(caso_larga, mmm.planilha_acoplada(), 3.0 * G).causa is None
            and mmm.trim(caso_t, hip_pl, 1.0 * G).causa is None
            and mmm.CAUSA_DOBRA == "dobra" and mmm.CAUSA_DOMINIO == "dominio")

# Conferência de margem do limite acoplado (I2): com a capacidade dos eixos trocada por um valor enorme (sintético de
# teste), a dobra do Newton em T não é a saturação de nenhum eixo (margem >> força por m/s² · resolucao_ms2), e o limite
# tem de dar N/A com motivo, sem eixo limitante nem T. Sem a conferência o código declararia PUSH/LOOSE com esse T.
_orig_caps = mmm._capacidades_acopladas
mmm._capacidades_acopladas = lambda *a, **k: ((1e7, 1e7), None)
try:
    with pneu_de_brinquedo(lei_saturada(0.1, 0.1)):
        lim_margem = mmm.limite(caso_b85, mmm.Hipoteses(cos_delta="trim"))
finally:
    mmm._capacidades_acopladas = _orig_caps
ok_margem = (mmm._capacidades_acopladas is _orig_caps and lim_margem.veredito == eq.NA and lim_margem.ay_t_ms2 is None
             and lim_margem.eixo_satura is None and "nenhum eixo está no pico" in (lim_margem.motivo or ""))

# Ruling da revisão da Task 4: com transf_long="regime", a Fz traseira do Trim difere da de transf_long="nao" (as cargas
# de eq.cargas no mesmo A_Y) por (m·a_x·h + D·h_cp)/L, com a_x = −A·sen β (A e β do próprio Trim), dividida igual entre as
# duas rodas traseiras, tirada igual das dianteiras (ΣFz conservada). D = ½ρ·CdA·A·R dos campos do caso. Calculado AQUI,
# sem helper do módulo; tolerância 1e-6 N. Com h_cp_m = None a parcela D·h_cp falta; o h_cp_m sintético de teste é de 0,4 m.
def resid_regime(h_cp):
    hip_r = mmm.Hipoteses(transf_long="regime", h_cp_m=h_cp)
    tr_r = mmm.trim(caso_pc, hip_r, 0.8 * G)
    if not tr_r.convergiu:
        return math.inf, math.inf, tr_r
    m_, h_, L_ = caso_pc.cfg.mass_total, caso_pc.cfg.cg_height, caso_pc.cfg.wheelbase
    A_, a_x = tr_r.ay_ms2, -tr_r.ay_ms2 * math.sin(tr_r.beta_rad)
    D_ = 0.5 * caso_pc.rho_kg_m3 * caso_pc.cda_m2 * A_ * caso_pc.raio_m
    d_fz = (m_ * a_x * h_ + (D_ * h_cp if h_cp is not None else 0.0)) / L_
    # Cargas-base na aceleração lateral do carro, a_y = A·cos β (adendo §2.5, sempre no caminho acoplado). O caso_pc tem
    # downforce fixa (sem CzA), então eq.cargas(caso, a_y) é exato; antes do EDR-064 esta linha usava eq.cargas(caso_pc, A_)
    # (a_y = A), a relação antiga, e a transferência lateral diferia em ~A·(1 − cos β) (alguns décimos de N).
    base_ = eq.cargas(caso_pc, A_ * math.cos(tr_r.beta_rad))
    erro = max(abs(tr_r.fz[c] - base_[c] - (d_fz / 2.0 if c in ("RL", "RR") else -d_fz / 2.0)) for c in CANTOS_T)
    return erro, abs(sum(tr_r.fz.values()) - sum(base_.values())), tr_r


ok_regime, det_regime = True, []
for h_cp_t in (None, 0.4):   # 0,4 m: sintético de teste
    e_fz, e_soma, tr_r = resid_regime(h_cp_t)
    ok_regime = ok_regime and e_fz < 1e-6 and e_soma < 1e-6 and tr_r.convergiu and abs(tr_r.beta_rad) > 1e-3
    det_regime.append(f"h_cp={h_cp_t}: |ΔFz − (m·a_x·h + D·h_cp)/L|={e_fz:.1e} N, |ΔΣFz|={e_soma:.1e} N, "
                      f"β={math.degrees(tr_r.beta_rad):.3f}°" if tr_r.convergiu else f"h_cp={h_cp_t}: sem trim")

check("TC-MMM-007: no trim |ΣFy−m·A_Y|<1e-6 N e |N|<1e-6 N·m; A_Y acima do limite -> convergiu=False com motivo e "
      "campos None; sem raio_m -> ValueError; limite: descolamento, toe que consome a faixa e pico na borda -> N/A com o "
      "motivo de capacidade_eixo e sem T; variante Python completa em 0,5·T: resíduos Fx, Fy, N em eixos do carro (§2.5) "
      "< 1e-6, com Ackermann também; limite acoplado: eixo que satura com ay_sat = T e o outro None (decisão 3), T e Q à mão; "
      "transf_long=regime: ΔFz traseira = (m·a_x·h + D·h_cp)/L com e sem h_cp (1e-6 N); rotação β sempre no acoplado "
      "(planilha_acoplada fecha ΣFy = m·A·cos β, o desacoplado ΣFy = m·A); Trim.causa estruturada; conferência de margem "
      "do limite acoplado (capacidade enorme -> N/A, sem eixo limitante)",
      ok_res and ok_alto and ok_raio and ok_acopl and ok_desc and ok_toe and ok_pc and ok_lim_a and ok_lim_n and ok_acima
      and ok_regime and ok_rot and ok_causa and ok_margem,
      f"resíduos(F,N)={[(f'{rf:.1e}', f'{rn:.1e}') for _, rf, rn in rs]}; motivo(5g)={tr_alto.motivo!r}; "
      f"eixo_sem_raiz={tr_alto.eixo_sem_raiz}; descolamento: {lim_desc.motivo!r}; toe: {lim_toe.motivo!r}; "
      f"borda: {lim_borda.motivo!r}; completo: {det_pc[0]}; com Ackermann: {det_pc[1]}; "
      f"limite acoplado (cos δ trim, brinquedo): T={lim_cd.ay_t_ms2:.6f} (mão {T_acopl:.6f}) Q={lim_cd.cn_estabilizante_q:.6f} "
      f"(mão {Q_acopl:.6f}) {lim_cd.veredito}; R grande T={lim_cd_g.ay_t_ms2:.6f} (mão μ·g/cos β = {T_n_rot:.6f}; sem rotação "
      f"{T_a_g:.6f}) {lim_cd_g.veredito}; "
      f"acima de T: {tr_acima.motivo!r}; regime (ΔFz traseira): {det_regime}; rotação (planilha_acoplada): "
      f"β={math.degrees(tr_ctrl.beta_rad):.3f}°, |ΣFy − m·A·cos β|={res_y_ctrl:.1e} N, sem o cos β={res_y_sem_cos:.2f} N, "
      f"desacoplado |ΣFy − m·A|={res_y_desac:.1e} N; T(cos δ trim, 8,5 m) com a rotação={T_acopl:.6f}, sem ela "
      f"(derivação antiga)={T_acopl_sem_rot:.6f}; margem: {lim_margem.motivo!r}")

# ---------------- TC-MMM-008 : α cinemático ----------------
# Ackermann 100 % em R = 8,5 m e β pequeno. Com o centro instantâneo na linha do eixo traseiro, sen β = b/R, o raio do
# ponto médio do eixo traseiro é ρ = R·cos β e as duas rodas dianteiras têm δ_i = atan(L/(ρ − t/2)) (FL, interna, y = +t/2)
# e δ_o = atan(L/(ρ + t/2)) (FR, externa): a geometria de Ackermann exata (cot δ_o − cot δ_i = t/L). Com δ = (δ_i + δ_o)/2
# a velocidade de cada roda é perpendicular ao raio até o centro e α_FL = α_FR = 0. Se o sinal de y estivesse trocado
# (FL em −t/2), α_FL e α_FR sairiam ≈ ±½·L·t/R² ≈ ±0,013 rad, e o teste falharia.
t_f = cfg.track_front
caso_ack = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, ackermann_pct=100.0)
beta_ack = math.asin(B_CG / R_TESTE)
rho_ack = R_TESTE * math.cos(beta_ack)
d_i_ack = math.atan(L / (rho_ack - t_f / 2.0))
d_o_ack = math.atan(L / (rho_ack + t_f / 2.0))
delta_ack = 0.5 * (d_i_ack + d_o_ack)
al_cin = mmm.alfa_rodas(caso_ack, hip_c, beta_ack, delta_ack)
al_pla = mmm.alfa_rodas(caso_ack, mmm.Hipoteses.planilha(), beta_ack, L / R_TESTE)
dif_cin = al_cin["FL"] - al_cin["FR"]
dif_pla = al_pla["FL"] - al_pla["FR"]
ref_pla = L * t_f / R_TESTE ** 2
ok_008 = (abs(dif_cin) < 1e-4 and max(abs(al_cin[c]) for c in ("FL", "FR", "RL", "RR")) < 1e-4
          and abs(abs(dif_pla) - ref_pla) <= 5e-2 * ref_pla
          and dif_pla < 0 and al_pla["FL"] < al_pla["FR"])   # planilha: a roda interna (FL) esterça mais, α_FL < α_FR
check("TC-MMM-008: α cinemático, Ackermann 100 %, β pequeno: |α_FL − α_FR| < 1e-4 rad (e as quatro α ≈ 0, o que fixa o "
      "sinal de y: FL em +t/2); a variante planilha dá |α_FL − α_FR| ≈ L·t/R² (relativo 5e-2) com α_FL < α_FR (interna)",
      ok_008,
      f"cinemático: α_FL={al_cin['FL']:.2e} α_FR={al_cin['FR']:.2e} α_RL={al_cin['RL']:.2e} α_RR={al_cin['RR']:.2e} rad; "
      f"planilha: α_FL − α_FR={dif_pla:.5f} rad (L·t/R²={ref_pla:.5f}, relativo "
      f"{abs(abs(dif_pla) - ref_pla) / ref_pla:.2e}); δ_i={math.degrees(d_i_ack):.3f}° δ_o={math.degrees(d_o_ack):.3f}°")

# ---------------- TC-MMM-009 : diferencial travado e tração acima do atrito ----------------
# Contribuição de Fx ao N (traseira): −Σ y_i·Fx_i = −(t/2)·(Fx_RL − Fx_RR). Aberto: Fx igual nas duas rodas, contribuição
# nula (1e-9). Travado (ω comum, mesmo raio de rolamento): em curva à esquerda a roda interna (RL, y = +t/2) tem V_x menor,
# κ maior e Fx maior que a externa, então Fx_RL > Fx_RR e a contribuição é < 0 (push, N < 0 no ISO).
caso_tr = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
                            rho_kg_m3=1.2, cda_m2=1.0, crr=0.02)   # sintético de teste
t_r2 = cfg.track_rear / 2.0


def n_fx(tr):
    return -(t_r2 * tr.fx["RL"] - t_r2 * tr.fx["RR"])


tr_ab = mmm.trim(caso_tr, hip_pl, 0.8 * G)
tr_ab_pac = mmm.trim(caso_tr, mmm.Hipoteses(tracao="pac2002"), 0.8 * G)
tr_tv = mmm.trim(caso_tr, mmm.Hipoteses(diferencial="travado"), 0.8 * G)
tr_tv_pac = mmm.trim(caso_tr, mmm.Hipoteses(diferencial="travado", tracao="pac2002"), 0.8 * G)
fx_total = eq.fx_exigido_traseira(caso_tr, 0.8 * G)
ok_009a = (all(t.convergiu for t in (tr_ab, tr_ab_pac, tr_tv, tr_tv_pac))
           and abs(n_fx(tr_ab)) < 1e-9 and abs(n_fx(tr_ab_pac)) < 1e-9
           and n_fx(tr_tv) < -1e-3 and n_fx(tr_tv_pac) < -1e-3
           and abs(tr_tv.fx["RL"] + tr_tv.fx["RR"] - fx_total) < 1e-6
           and tr_tv.kappa["RL"] > tr_tv.kappa["RR"] and tr_tv_pac.kappa["RL"] > tr_tv_pac.kappa["RR"])
# Tração acima do atrito: com PAC2002 o Fx combinado (α ≠ 0) é menor que o pico puro que a elipse usa. Procura-se, em
# Crr crescente (sintético de teste), um caso em que a elipse (semente) ainda sustenta o Fx e o PAC2002 não (Brent sem
# raiz), e outro bem acima do atrito. No primeiro o motivo é exatamente "tração excede o atrito longitudinal em <canto>"
# (sai do Brent da variante); no segundo a semente desacoplada já falha, e o motivo dela leva o prefixo "eixo R: ".
MSG_TRACAO = "tração excede o atrito longitudinal em "
janela = None
for crr_x in [0.2 + 0.005 * k for k in range(0, 200)]:
    caso_x = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
                               rho_kg_m3=1.2, cda_m2=1.0, crr=crr_x)
    if mmm.trim(caso_x, hip_pl, 0.8 * G).convergiu:
        t_p = mmm.trim(caso_x, mmm.Hipoteses(tracao="pac2002"), 0.8 * G)
        if not t_p.convergiu:
            janela = (crr_x, t_p.motivo)
            break
caso_muito = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
                               rho_kg_m3=1.2, cda_m2=1.0, crr=2.0)
t_muito = mmm.trim(caso_muito, mmm.Hipoteses(tracao="pac2002"), 0.8 * G)
ok_009b = (janela is not None and janela[1] in (MSG_TRACAO + "RL", MSG_TRACAO + "RR")
           and not t_muito.convergiu and t_muito.motivo.endswith((MSG_TRACAO + "RL", MSG_TRACAO + "RR"))
           and t_muito.fy is None and t_muito.kappa is None)
check("TC-MMM-009: diferencial travado: contribuição de Fx ao N < 0 (push) em curva à esquerda, com a soma de Fx = Fx "
      "exigido; aberto: nula (1e-9); Fx exigido acima do atrito (PAC2002, Brent sem raiz) -> motivo "
      "'tração excede o atrito longitudinal em <canto>'",
      ok_009a and ok_009b,
      f"N_Fx(aberto)={n_fx(tr_ab):.1e}, N_Fx(aberto,PAC)={n_fx(tr_ab_pac):.1e}, N_Fx(travado)={n_fx(tr_tv):.3f} N·m, "
      f"N_Fx(travado,PAC)={n_fx(tr_tv_pac):.3f} N·m; κ travado RL={tr_tv.kappa['RL']:.4f} RR={tr_tv.kappa['RR']:.4f}; "
      f"janela de Crr (elipse ok, PAC sem raiz)={janela}; Crr=2: {t_muito.motivo!r}")

# ---------------- TC-MMM-010 : várias raízes de ΣFy(A_Y) − m·A_Y ----------------
# CzA = 200 m² (sintético de teste, absurdo de propósito) com ρ = 1,2 kg/m³: a downforce cresce tanto com A_Y que ΣFy − m·A_Y
# troca de sinal mais de uma vez. (β, δ) = (8°, 20°) (sintético de teste, achado por varredura). `ponto` devolve a MENOR raiz
# (documentado na docstring) e n_raizes >= 2. A conferência é independente do módulo: ΣFy(A_Y) é refeito AQUI de eq.cargas,
# eq.entrada_limitada, mmm.alfa_rodas e wheel_forces (sem aero na tração; o caso não tem CdA), numa varredura de 0,002·G, e a
# menor troca de sinal é refinada por bisseção.
caso_010 = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, cza_m2=200.0, rho_kg_m3=1.2, aero_balance_front=0.45)
b_010, d_010 = math.radians(8.0), math.radians(20.0)
p_010 = mmm.ponto(caso_010, hip_pl, b_010, d_010)


def f_010(ay):
    fz_ = eq.cargas(caso_010, ay)
    fz_u_, gam_u_, _ = eq.entrada_limitada(caso_010, CANTOS_T, fz_, eq.camber(caso_010, ay))
    al_ = mmm.alfa_rodas(caso_010, hip_pl, b_010, d_010)
    cos_ref_ = math.cos(L / R_TESTE)
    soma = sum(tm.wheel_forces(ds, c, fz_u_[c], al_[c], gam_u_[c], 0.0)[1] * (cos_ref_ if c in ("FL", "FR") else 1.0)
               for c in CANTOS_T)
    return soma - cfg.mass_total * ay


passo_010 = 0.002 * G
ay_010 = [k * passo_010 for k in range(int(1.0 * G / passo_010))]   # até 1 g: a menor raiz cai bem antes
v_010 = [f_010(a) for a in ay_010]
trocas_010 = [k for k in range(len(ay_010) - 1) if v_010[k] * v_010[k + 1] < 0.0]
lo_, hi_ = ay_010[trocas_010[0]], ay_010[trocas_010[0] + 1]
for _ in range(60):
    mid_ = 0.5 * (lo_ + hi_)
    if f_010(lo_) * f_010(mid_) <= 0.0:
        hi_ = mid_
    else:
        lo_ = mid_
menor_010 = 0.5 * (lo_ + hi_)
check("TC-MMM-010: CzA alto (200 m², sintético de teste): ponto com n_raizes ≥ 2, e o A_Y devolvido é a menor raiz "
      "(refeita fora do módulo por varredura + bisseção, 1e-6)",
      p_010.n_raizes >= 2 and len(trocas_010) >= 1 and p_010.ay_ms2 is not None and abs(p_010.ay_ms2 - menor_010) < 1e-6
      and abs(f_010(p_010.ay_ms2)) < 1e-6,
      f"n_raizes={p_010.n_raizes}; A_Y devolvido={p_010.ay_ms2 / G:.6f} g; menor raiz independente={menor_010 / G:.6f} g; "
      f"{len(trocas_010)} trocas de sinal em [0, 1 g] (passo 0,002 g)")

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
# A linha de controle da escada tem as hipóteses da planilha em todos os campos, mas força o caminho acoplado; fica fora do
# contrato de campos e de VARIANTES, e `_SemNumero` (o erro esperado de K e do SI) é um ValueError.
hip_ctrl = mmm.planilha_acoplada()
ok_ctrl = (all(getattr(hip_ctrl, k) == getattr(hip_pl, k) for k in mmm.VARIANTES) and hip_ctrl != hip_pl
           and mmm._e_acoplada(hip_ctrl) and not mmm._e_acoplada(hip_pl)
           and {f.name for f in dataclasses.fields(mmm.Hipoteses)} == campos
           and issubclass(mmm._SemNumero, ValueError)
           and raises(lambda: mmm.k_trim(caso_t, hip_pl, 0.001 * G), ValueError, "exige ay_ms2"))
# Contrato de UNIDADES e sensibilidade (Task 5): chaves, passos dos textos, h_cp só com regime, caso e hipóteses intactos.
unid_esperadas = {"ganho_camber_F": "por 0,1 °/°", "ganho_camber_R": "por 0,1 °/°", "rc_F": "por 10 mm", "rc_R": "por 10 mm",
                  "kphi_F": "por 1 kN·m/rad", "kphi_R": "por 1 kN·m/rad", "h_cg": "por 10 mm", "cg_lateral": "por 10 mm",
                  "h_cp": "por 10 mm"}
chaves_sens = {"parametro", "unidade", "d_ay_t", "d_cn_estabilizante_q", "d_k", "veredito_menos", "veredito_mais", "motivo"}
caso_s11 = eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, cg_lateral_m=0.005)   # 0,005 m: sintético de teste
sens_cg = mmm.sensibilidade(caso_s11, hip_pl, "h_cg")
sens_hcp_nao = mmm.sensibilidade(caso_s11, hip_pl, "h_cp")
sens_lat = mmm.sensibilidade(caso_s11, hip_pl, "cg_lateral")
# h_cg: o T cai com a altura do CG (mais transferência de carga): d_ay_t < 0, e a diferença central confere com dois limites.
lim_m = mmm.limite(dataclasses.replace(caso_s11, cfg=dataclasses.replace(cfg, cg_height=cfg.cg_height - 0.010)),
                   hip_pl)
lim_p = mmm.limite(dataclasses.replace(caso_s11, cfg=dataclasses.replace(cfg, cg_height=cfg.cg_height + 0.010)), hip_pl)
ok_sens = (set(mmm.UNIDADES) == set(unid_esperadas) and all(mmm.UNIDADES[k] == v for k, v in unid_esperadas.items())
           and set(sens_cg) == chaves_sens and sens_cg["unidade"] == "por 10 mm" and sens_cg["parametro"] == "h_cg"
           and sens_cg["d_ay_t"] is not None and sens_cg["d_ay_t"] < 0.0
           and abs(sens_cg["d_ay_t"] - (lim_p.ay_t_ms2 - lim_m.ay_t_ms2) / 2.0) < 1e-12
           and sens_cg["veredito_menos"] == lim_m.veredito and sens_cg["veredito_mais"] == lim_p.veredito
           and sens_hcp_nao["motivo"] == "h_cp só com transf_long=regime" and sens_hcp_nao["d_ay_t"] is None
           and sens_lat["d_ay_t"] is not None
           and raises(lambda: mmm.sensibilidade(caso_s11, hip_pl, "x"), ValueError, "parametro")
           and raises(lambda: mmm.sensibilidade(eq.CasoEquilibrio(cfg=cfg, ds=ds_teste), hip_pl, "h_cg"), ValueError, MSG_SEM_RAIO)
           and caso_s11.cfg.cg_height == cfg.cg_height and caso_s11.cg_lateral_m == 0.005
           and hip_pl == mmm.Hipoteses.planilha())
check("TC-MMM-011: VARIANTES = campos de Hipoteses (sem h_cp_m); hipóteses ⊂ {1,2,3,7,9,10,11}; "
      "Hipoteses(alfa='x') -> ValueError; UNIDADES e sensibilidade (chaves, unidade, diferença central de h_cg conferida "
      "com dois limites, h_cp sem regime com motivo, caso intacto)",
      ok_campos and ok_hip and ok_valor and ok_py and ok_nomes and ok_var and ok_sens and ok_ctrl,
      f"campos={sorted(campos)}; sens h_cg: d_ay_t={sens_cg['d_ay_t']}, d_cn_q={sens_cg['d_cn_estabilizante_q']}, "
      f"d_k={sens_cg['d_k']}, vereditos=({sens_cg['veredito_menos']}, {sens_cg['veredito_mais']}), motivo={sens_cg['motivo']!r}")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
