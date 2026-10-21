"""
Equilíbrio linear de curva: funções do Gillespie, cap. 6 (V4.0, incremento 2).

Fonte: T. D. Gillespie, Fundamentals of Vehicle Dynamics, cap. 6, eqs. 6-15, 6-18, 6-32, 6-49 (deduzida em 6-41 a 6-48) e 6-56,
exemplos resolvidos das pp. 231-235 (conferidos na imagem do PDF). O livro usa lb, in, ft e g = 32,2 ft/s².
Aqui tudo é SI: força em N, rigidez em N/rad (ou N·m/rad), K em rad/(m/s²). A conversão para °/g é só de
apresentação (`para_graus_por_g`).

Unidades de K. No livro, K em rad/g é W/C, com W e C na mesma unidade de força. Em SI, W = m·g e C em N/rad;
dividir por G = 9,81 m/s² (suspension_model.G) dá K em rad/(m/s²), e `para_graus_por_g` multiplica por G de volta:
o g da conversão se cancela, e o resultado em °/g não depende do g que o livro usa.

Convenção de sinal: K > 0 é subesterço, K < 0 é sobresterço. C_α do eixo é a soma dos dois pneus.

Errata do livro (p. 232, exemplo 1): a V_char impressa, 393 ft/s, foi calculada com L = 110,6 in; o problema
dá L = 100,6 in, que resulta em cerca de 375 ft/s. O teste TC-EQ-025 registra os dois valores.
"""

import math

from suspension_model import G


def gradiente_pneus(W_f_N, W_r_N, C_f_N_rad, C_r_N_rad):
    """Eq. 6-15, parcela dos pneus: K = (W_f/C_f − W_r/C_r)/G [rad/(m/s²)].
    W_f e W_r são as cargas estáticas nos eixos [N]; C_f e C_r, as rigidezes de deriva de EIXO (dois pneus) [N/rad].
    Em rad/g é W_f/C_f − W_r/C_r."""
    return (W_f_N / C_f_N_rad - W_r_N / C_r_N_rad) / G


def para_graus_por_g(K):
    """Converte K de rad/(m/s²) para °/g: degrees(K)·G. Só para apresentação."""
    return math.degrees(K) * G


def velocidade_caracteristica(L_m, K):
    """Eq. 6-18: V_char = √(L/K) [m/s], com K em rad/(m/s²) e K > 0 (subesterço). Para K ≤ 0 não existe: None."""
    if K > 0:
        return math.sqrt(L_m / K)
    return None


def velocidade_critica(L_m, K):
    """Velocidade crítica de um carro sobresterçante: V_crit = √(−L/K) [m/s], com K < 0. Para K ≥ 0 não existe: None."""
    if K < 0:
        return math.sqrt(-L_m / K)
    return None


def ponto_neutro_ate_traseiro(L_m, C_f, C_r):
    """Gillespie p. 233: distância do eixo traseiro ao ponto de esterço neutro, c' = L·C_f/(C_f + C_r) [m].
    C_f e C_r na mesma unidade (por eixo ou por pneu; só a razão importa)."""
    return L_m * C_f / (C_f + C_r)


def gradiente_rolagem(W_N, h1_m, K_phi_f, K_phi_r):
    """Eq. 6-32: dφ/da_y = W·h1/(K_φf + K_φr − W·h1)/G [rad/(m/s²)].
    W [N] é o peso suspenso, h1 [m] a distância do CG ao eixo de rolagem, K_φ as rigidezes de rolagem [N·m/rad].
    ValueError se o denominador for ≤ 0 (rolagem sem equilíbrio linear)."""
    den = K_phi_f + K_phi_r - W_N * h1_m
    if den <= 0:
        raise ValueError(f"K_phi_f + K_phi_r − W·h1 = {den:.4g} ≤ 0: sem equilíbrio linear de rolagem")
    return W_N * h1_m / den / G


def parcela_camber(Cg_f, Ca_f, dgf, Cg_r, Ca_r, dgr, dphi_day):
    """Eq. 6-56: K_camber = (C_γf/C_αf·∂γ_f/∂φ − C_γr/C_αr·∂γ_r/∂φ)·∂φ/∂a_y.
    Cada razão C_γ/C_α é adimensional (mesmas unidades no numerador e no denominador). ∂γ/∂φ é o gradiente de camber
    do eixo em relação à rolagem (rad/rad). A unidade do resultado é a de `dphi_day` (°/g entra, °/g sai)."""
    return (Cg_f / Ca_f * dgf - Cg_r / Ca_r * dgr) * dphi_day


def parcela_transferencia_aprox(W_f_N, C_f, b_f, dFz_f, W_r_N, C_r, b_r, dFz_r):
    """Eq. 6-49 (K_llt, p. 217; aproximação 6-47 na p. 216), dividida por G [rad/(m/s²)]:
    K_llt = [W_f/C_f · 2·b_f·ΔFz_f²/C_f − W_r/C_r · 2·b_r·ΔFz_r²/C_r]/G.
    C_f e C_r são as rigidezes de deriva de EIXO [N/rad], como em `gradiente_pneus`; b_f e b_r vêm de
    C_α = a·Fz − b·Fz² por PNEU [rad⁻¹·N⁻¹], e ΔFz é a transferência de carga POR PNEU [N] no eixo. Com a carga
    dos dois pneus em Fz ± ΔFz, o eixo perde 2·b·ΔFz² de rigidez, e a perda relativa é 2·b·ΔFz²/C.
    O resultado vale no ΔFz da a_y dada; ΔFz cresce com a_y, então a parcela não é constante."""
    f = W_f_N / C_f * 2.0 * b_f * dFz_f**2 / C_f
    r = W_r_N / C_r * 2.0 * b_r * dFz_r**2 / C_r
    return (f - r) / G
