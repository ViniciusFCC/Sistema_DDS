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


# ---------------------------------------------------------------------------
# Parcelas de K de um caso (passo 1 da spec §6) e tabela linear de 0 a 0,4 g
# ---------------------------------------------------------------------------
#
# Montagem do K de um CasoEquilibrio com o pneu PAC2002 (V4.0, inc. 2; spec §6). Convenções dos Global Constraints:
# C_α = −∂Fy_ISO/∂α e C_γ = −∂Fy_ISO/∂γ na roda FR (tire_model.rigidez_deriva e rigidez_camber), C do eixo = soma
# das duas rodas; gradiente de camber do eixo = (∂γ_R/∂φ − ∂γ_L/∂φ)/2; roll steer na convenção do SUS-415. O
# espelhamento da roda esquerda em wheel_forces dá ∂Fy_FL/∂α = ∂Fy_FR/∂α na mesma (Fz, γ), então a rigidez de deriva
# da roda esquerda é rigidez_deriva(ds, Fz_FL, γ_FL), com γ na convenção do projeto.
#
# Entrada do pneu fora da faixa do .tir: as regras do EDR-056 (Fz e γ limitados à faixa, com aviso em `limites`;
# Fz <= 0 = descolamento, parcela N/A). Os auxiliares de limitação são os mesmos de equilibrio.capacidade_eixo.

import dataclasses as _dc

import numpy as _np

import equilibrio as _eq
import tire_model as _tm
from suspension_model import lateral_dfz, static_fz_corner

MOTIVO_SEM_SENSIBILIDADE = "polinômio sem sensibilidade à carga no trecho"


@_dc.dataclass(frozen=True)
class ParcelasK:
    """Parcelas do gradiente de subesterço K num a_y [m/s²], todas em rad/(m/s²) (K > 0 = subesterço).

    Uma parcela None é N/A (motivo em `motivo`); com qualquer parcela N/A, k_total também é None (nunca "K total"
    com parcela faltando, spec §6). dphi_day é o gradiente de rolagem ∂φ/∂a_y [rad/(m/s²)]. `limites` traz os
    avisos de entrada do pneu limitada à faixa do .tir (EDR-056, item 1), no formato de equilibrio._entrada_limitada.
    """
    ay_ms2: float
    k_pneus: float | None
    k_transferencia: float | None
    k_deslocamento: float | None
    k_camber: float | None
    k_roll_steer: float | None
    k_total: float | None
    dphi_day: float | None
    motivo: str | None
    limites: tuple[str, ...] = ()


def _pesos_eixo(caso) -> tuple[float, float]:
    """W_f, W_r [N]: cargas estáticas de eixo sem aerodinâmica (m·G·b/L e m·G·a/L).

    São os W do Gillespie eq. 6-15: a força exigida de cada eixo é W·a_y/G (equilibrio.forca_exigida), e a
    downforce não muda a força exigida, só a rigidez (via Fz, em `_rigidez_eixo`).
    """
    st = static_fz_corner(caso.cfg)
    return st["FL"] + st["FR"], st["RL"] + st["RR"]


def _rigidez_eixo(caso, eixo: str, fz: dict, gam: dict):
    """(C_α do eixo [N/rad], avisos de limitação, motivo de N/A) com Fz e γ dados por roda.

    Fz <= 0 em alguma roda: N/A por descolamento (equilibrio._descolamento). Fz e γ fora da faixa: limitados
    (equilibrio._entrada_limitada, EDR-056). C_α do eixo <= 0: N/A (nunca divisão por zero; Review Focus 3).
    """
    rodas = _eq._rodas(eixo)
    desc = _eq._descolamento(fz, rodas)
    if desc is not None:
        return None, (), desc
    fz_u, gam_u, lims = _eq._entrada_limitada(caso, rodas, fz, gam)
    c = sum(_tm.rigidez_deriva(caso.ds, fz_u[r], gam_u[r]) for r in rodas)
    if not c > 0.0:
        return None, tuple(lim.texto for lim in lims), f"C_α do eixo {eixo} = {_eq._num(c, '.1f')} N/rad ≤ 0"
    return c, tuple(lim.texto for lim in lims), None


def _rigidez_camber_eixo(caso, eixo: str, fz: dict, gam: dict) -> float:
    """C_γ do eixo [N/rad] = soma de rigidez_camber nas duas rodas, com Fz limitado à faixa (EDR-056).

    rigidez_camber é avaliada em γ = 0 (definição dos Global Constraints). Exige Fz > 0 (quem chama verifica).
    """
    rodas = _eq._rodas(eixo)
    fz_u, _, _ = _eq._entrada_limitada(caso, rodas, fz, gam)
    return sum(_tm.rigidez_camber(caso.ds, fz_u[r]) for r in rodas)


# Passo da diferença central em a_y para dF0/da_y [m/s²]. F0 é suave em Fz e ΔFz é linear em a_y, então o erro de
# truncamento é O(h²) e desprezível; 1e-4·G fica longe do ruído de arredondamento (F0 ~ 10 N).
_H_AY_DESLOCAMENTO = 1e-4 * G


def _forca_deslocamento(caso, eixo: str, ay_fz: float, gam: dict):
    """(F0 do eixo [N, ISO], motivo): Σ Fy das duas rodas em α_ref = 0 (κ = 0), com o Fz de a_y = ay_fz e o γ dado,
    limitados à faixa (EDR-056).

    É a força que o pneu dá sem deriva: deslocamentos PHY*/PVY* do PAC2002 (ply steer e conicidade), com o
    espelhamento esquerda/direita de wheel_forces. O γ é passado fixo por quem chama (o da linha) para que a
    derivada em a_y não conte de novo o empuxo de camber, que já é a parcela k_camber. O toe estático entra como em
    fy_eixo (α_roda = α_ref + Δα_toe), o mesmo modelo do passo 2. Fz <= 0: (None, motivo de descolamento).
    """
    rodas = _eq._rodas(eixo)
    fz = _eq.cargas(caso, ay_fz)
    desc = _eq._descolamento(fz, rodas)
    if desc is not None:
        return None, desc
    fz_u, gam_u, _ = _eq._entrada_limitada(caso, rodas, fz, gam)
    return _eq._fy_eixo_limitado(caso, rodas, fz_u, gam_u, 0.0), None


def _parcela_deslocamento(caso, ay_ms2: float, c_f: float, c_r: float):
    """(k_deslocamento [rad/(m/s²)], motivo): parcela do deslocamento do pneu que varia com a carga.

    F0 é a Fy do eixo em α_ref = 0, com o toe estático (α_roda = Δα_toe) e o γ da linha: além dos deslocamentos
    PHY/PVY do PAC2002, a parcela inclui o efeito do toe estático e a variação, com a carga, do empuxo do camber
    estático (EDR-057). Só a variação do γ com a_y fica fora (é a parcela k_camber).

    Cada eixo dá Fy_eixo = −C_eixo·α + F0_eixo(a_y) (α ISO, C_α = −∂Fy/∂α) e precisa dar W·a_y/G. Logo
    −α = (W·a_y/G − F0)/C, e o K do Gillespie (ângulos positivos), −d(α_f − α_r)/da_y, recebe do F0 a parcela
    k_deslocamento = −(dF0_f/da_y)/C_f + (dF0_r/da_y)/C_r, com C de eixo da linha. dF0/da_y por diferença central
    no Fz de a_y ± _H_AY_DESLOCAMENTO, com o γ da linha fixo (o empuxo de camber variando com a_y é k_camber); em
    a_y = 0, a diferença central em torno de 0 é o próprio limite a_y → 0. Com o dataset sem deslocamentos, F0 não
    depende de Fz e a parcela some. As parcelas do Gillespie (pp. 202-226) usam só o C_α e não têm este termo; ele
    existe no pneu PAC2002 e no passo 2 (ruling do controlador, Task 4).
    """
    h = _H_AY_DESLOCAMENTO
    gam = _eq.camber(caso, ay_ms2)
    k = 0.0
    for eixo, c, sinal in (("F", c_f, -1.0), ("R", c_r, 1.0)):
        f_mais, m1 = _forca_deslocamento(caso, eixo, ay_ms2 + h, gam)
        f_menos, m2 = _forca_deslocamento(caso, eixo, ay_ms2 - h, gam)
        if m1 is not None or m2 is not None:
            return None, (m1 or m2) + " (vizinhança da diferença central do deslocamento do pneu)"
        k += sinal * (f_mais - f_menos) / (2.0 * h) / c
    return k, None


def _juntar(*itens):
    """Concatena sem repetir, na ordem."""
    saida = []
    for it in itens:
        for s in it:
            if s not in saida:
                saida.append(s)
    return tuple(saida)


def parcelas_k(caso, ay_ms2: float) -> ParcelasK:
    """Parcelas do gradiente de subesterço K em a_y [m/s²] (Gillespie cap. 6; spec §6), em rad/(m/s²).

    - k_pneus (eq. 6-15): (W_f/C_f − W_r/C_r)/G, com C de eixo na carga estática por roda (com a aerodinâmica do
      caso) e γ estático.
    - k_transferencia (pp. 215-217): (W_f/C_f(a_y) − W_r/C_r(a_y))/G − k_pneus, com C de eixo nas cargas e no γ
      dessa a_y (forma exata pelo PAC2002, sem o polinômio do livro). Com a_y → 0, tende a 0. Como o γ também
      muda com a_y, a parcela inclui a variação de C_α com o camber (efeito de 2ª ordem, pequeno).
    - k_deslocamento: −(dF0_f/da_y)/C_f + (dF0_r/da_y)/C_r, com F0 a Fy do eixo em α = 0 (deslocamentos do
      PAC2002 variando com a carga; ver `_parcela_deslocamento`). Termo fora do Gillespie, presente no pneu. Inclui
      o efeito do toe estático (F0 é avaliada com α_roda = Δα_toe) e a variação, com a carga, do empuxo do camber
      estático (γ da linha fixo); EDR-057.
    - k_camber (eq. 6-56, pp. 218-219): (C_γf/C_αf·∂γ_f/∂φ − C_γr/C_αr·∂γ_r/∂φ)·∂φ/∂a_y, com C_γ e C_α de eixo na
      carga estática, ∂γ/∂φ do eixo = (ganho_camber[R] − ganho_camber[L])/2 e ∂φ/∂a_y = φ(a_y)/a_y de
      lateral_dfz (linear em a_y; em a_y = 0 usa a_y = 1e-6·G).
    - k_roll_steer (eq. 6-57, SUS-415): (ε_f − ε_r)·∂φ/∂a_y, com ε = caso.roll_steer.
    W_f e W_r são os pesos de eixo sem aerodinâmica (`_pesos_eixo`). O C_α é a inclinação em α = 0, sem o toe; o
    toe estático entra no K pela parcela k_deslocamento. Fz <= 0 ou C_α <= 0: a parcela fica None, com motivo, e
    k_total também.
    """
    cfg = caso.cfg
    W_f, W_r = _pesos_eixo(caso)
    ay_ref = ay_ms2 if ay_ms2 != 0.0 else 1e-6 * G
    dphi = lateral_dfz(cfg, ay_ref)["roll_angle_rad"] / ay_ref
    motivos = []

    fz0, gam0 = _eq.cargas(caso, 0.0), _eq.camber(caso, 0.0)
    cf0, lf0, mf0 = _rigidez_eixo(caso, "F", fz0, gam0)
    cr0, lr0, mr0 = _rigidez_eixo(caso, "R", fz0, gam0)
    motivos += [m for m in (mf0, mr0) if m is not None]
    k_pneus = gradiente_pneus(W_f, W_r, cf0, cr0) if (cf0 is not None and cr0 is not None) else None

    fz, gam = _eq.cargas(caso, ay_ms2), _eq.camber(caso, ay_ms2)
    cf, lf, mf = _rigidez_eixo(caso, "F", fz, gam)
    cr, lr, mr = _rigidez_eixo(caso, "R", fz, gam)
    motivos += [m for m in (mf, mr) if m is not None and m not in motivos]
    if k_pneus is not None and cf is not None and cr is not None:
        k_transf = gradiente_pneus(W_f, W_r, cf, cr) - k_pneus
    else:
        k_transf = None

    k_desl = None
    if cf is not None and cr is not None:
        k_desl, m_desl = _parcela_deslocamento(caso, ay_ms2, cf, cr)
        if m_desl is not None and m_desl not in motivos:
            motivos.append(m_desl)

    if cf0 is not None and cr0 is not None:
        g = caso.ganho_camber
        dgf = (g["FR"] - g["FL"]) / 2.0
        dgr = (g["RR"] - g["RL"]) / 2.0
        cgf = _rigidez_camber_eixo(caso, "F", fz0, gam0)
        cgr = _rigidez_camber_eixo(caso, "R", fz0, gam0)
        k_camber = parcela_camber(cgf, cf0, dgf, cgr, cr0, dgr, dphi)
    else:
        k_camber = None

    k_rs = (caso.roll_steer["F"] - caso.roll_steer["R"]) * dphi
    partes = (k_pneus, k_transf, k_desl, k_camber, k_rs)
    k_total = None if any(x is None for x in partes) else sum(partes)
    return ParcelasK(ay_ms2=ay_ms2, k_pneus=k_pneus, k_transferencia=k_transf, k_deslocamento=k_desl,
                     k_camber=k_camber,
                     k_roll_steer=k_rs, k_total=k_total, dphi_day=dphi,
                     motivo="; ".join(motivos) if motivos else None,
                     limites=_juntar(lf0, lr0, lf, lr))


def angulos_necessarios(caso, ay_ms2: float, n_alfa: int = 401) -> tuple[float, float] | None:
    """(α_f, α_r) [rad, ISO]: α de referência de cada eixo em que fy_eixo iguala a força exigida em a_y.

    Mesmo modelo do passo 2 (equilibrio.capacidade_eixo): Fy do eixo com Fz e γ limitados à faixa (EDR-056) e o
    toe estático em cada roda. Bissecção até |ΔF| < 1e-9·força exigida (1e-9 N se a força for nula), entre α = 0 e
    o α do pico na grade de n_alfa pontos quando a Fy do eixo em α = 0 fica abaixo da exigência (o caso normal da
    curva à esquerda, α < 0), ou entre 0 e +A quando ela já passa da exigência (carro assimétrico em L/R: CG
    lateral, toe ou camber assimétricos e os deslocamentos do pneu variando com Fz), com A a amplitude de
    `equilibrio.grade_alfa` (faixa de α do pneu menos o maior |Δα| de toe e Ackermann; a grade vai de 0 a −A).
    Devolve None se algum eixo não tiver capacidade (descolamento, toe), se a exigência passar da capacidade
    (α < 0), ou se a Fy do eixo em +A ainda passar da exigência.
    """
    if not (ay_ms2 >= 0.0 and math.isfinite(ay_ms2)):
        raise ValueError(f"angulos_necessarios cobre a curva à esquerda (a_y >= 0); recebido {ay_ms2!r}.")
    saida = []
    for eixo, req in zip(("F", "R"), _eq.forca_exigida(caso, ay_ms2)):
        cap = _eq.capacidade_eixo(caso, eixo, ay_ms2, n_alfa)
        if cap.fy_max_N is None or req > cap.fy_max_N:
            return None
        rodas = _eq._rodas(eixo)
        fz_u, gam_u, _ = _eq._entrada_limitada(caso, rodas, _eq.cargas(caso, ay_ms2), _eq.camber(caso, ay_ms2))

        def folga(a, rodas=rodas, fz_u=fz_u, gam_u=gam_u, req=req):
            return _eq._fy_eixo_limitado(caso, rodas, fz_u, gam_u, a) - req

        tol = 1e-9 * abs(req) if req != 0.0 else 1e-9
        f_0 = folga(0.0)
        if abs(f_0) < tol:
            saida.append(0.0)
            continue
        if f_0 < 0.0:
            # raiz em α < 0, entre 0 (falta força) e o pico (já checado: capacidade >= exigência)
            neg, pos = 0.0, cap.alfa_pico_rad
        else:
            # Fy em α = 0 já passa da exigência (deslocamentos do pneu com carro assimétrico em L/R): raiz em α > 0,
            # até +A, o simétrico da borda da grade (mesma faixa de α do pneu, com o Δα de toe e Ackermann)
            a_max = -_eq.grade_alfa(caso, 3)[-1]
            if folga(a_max) > 0.0:
                return None
            neg, pos = a_max, 0.0
        meio = pos
        for _ in range(200):
            meio = 0.5 * (neg + pos)
            f_m = folga(meio)
            if abs(f_m) < tol or meio in (neg, pos):
                break
            if f_m < 0.0:
                neg = meio
            else:
                pos = meio
        saida.append(meio)
    return saida[0], saida[1]


def tabela_linear(caso, ay_max_g: float = 0.4, passo_g: float = 0.05, pior_origem: str | None = None,
                  n_alfa: int = 401) -> list:
    """Tabela do passo 1 de a_y = 0 a ay_max_g (faixa linear até 0,4 g, Milliken p. 315; spec §6).

    Uma linha por a_y_k = k·passo (k = 0…⌊ay_max/passo⌋), com as parcelas (`parcelas_k`), o K tangente medido no
    modelo do passo 2 (`k_inclinacao`) e o texto de exibição (`texto_k`). k_inclinacao [rad/(m/s²)] é a
    diferença de (α_f − α_r) entre a linha e a anterior dividida pela diferença de a_y. Na primeira linha é a
    estimativa da derivada em a_y → 0 (a SAE define o gradiente como derivada, Gillespie p. 227): com S(h) a
    secante [(α_f − α_r)(h) − (α_f − α_r)(0)]/h de a_y = 0 a h (o ângulo em a_y = 0 é nulo só com o carro simétrico
    em L/R; com CG lateral, toe ou camber assimétricos ele não é, e a secante desconta o valor medido), a extrapolação de
    Richardson 2·S(0,005·G) − S(0,01·G). Ela remove o termo de 2ª ordem de α(a_y) (por exemplo, o dos termos de
    camber do PAC2002, PKY3·|γ| e PVY3/PVY4, com γ e ΔFz proporcionais a a_y), que daria um erro de 1ª ordem em h
    numa secante simples (ruling C do controlador, Task 4). O α aqui é o ISO,
    negativo na curva à esquerda: o K do Gillespie (ângulos de deriva positivos) é −Δ(α_f − α_r)/Δa_y, e é esse o
    sinal guardado (K > 0 = subesterço, como as parcelas). Sem ângulos (None de `angulos_necessarios`),
    k_inclinacao fica None com `motivo_inclinacao`.
    pior_origem vai para `texto_k`; None (não informado) conta como diferente do TX e dá "DEMONSTRATIVO" (D16).
    """
    if not (isinstance(ay_max_g, (int, float)) and ay_max_g > 0 and math.isfinite(ay_max_g)):
        raise ValueError(f"ay_max_g deve ser > 0 e finito; recebido {ay_max_g!r}.")
    if not (isinstance(passo_g, (int, float)) and passo_g > 0 and math.isfinite(passo_g)):
        raise ValueError(f"passo_g deve ser > 0 e finito; recebido {passo_g!r}.")
    n = math.floor(ay_max_g / passo_g + 1e-9)   # mesma folga de arredondamento de equilibrio._varredura
    linhas = []
    ang_ant, ay_ant = None, None
    for k in range(n + 1):
        ay = k * passo_g * G
        p = parcelas_k(caso, ay)
        ang = angulos_necessarios(caso, ay, n_alfa)
        k_incl, motivo_incl = None, None
        if k == 0:
            secantes = []
            if ang is not None:   # ang = ângulos em a_y = 0 (≠ 0 com CG lateral ou outra assimetria L/R)
                for ay1 in (0.005 * G, 0.01 * G):
                    ang1 = angulos_necessarios(caso, ay1, n_alfa)
                    if ang1 is None:
                        break
                    secantes.append(-((ang1[0] - ang1[1]) - (ang[0] - ang[1])) / ay1)
            if len(secantes) == 2:
                k_incl = 2.0 * secantes[0] - secantes[1]   # Richardson: tira o termo de 1ª ordem em h
            else:
                motivo_incl = "ângulos necessários indisponíveis em 0, 0,005 g ou 0,01 g"
        elif ang is not None and ang_ant is not None:
            k_incl = -((ang[0] - ang[1]) - (ang_ant[0] - ang_ant[1])) / (ay - ay_ant)
        else:
            motivo_incl = "ângulos necessários indisponíveis nesta linha ou na anterior"
        linhas.append({"ay_ms2": ay, "ay_g": k * passo_g, "parcelas": p, "k_inclinacao": k_incl,
                       "motivo_inclinacao": motivo_incl, "texto_k": texto_k(p, pior_origem)})
        ang_ant, ay_ant = ang, ay
    return linhas


def texto_k(p: ParcelasK, pior_origem: str | None) -> str:
    """Texto exato de exibição do K (spec §6; Global Constraints).

    "K = <±x,xx> °/g (pneus + transferência + deslocamento do pneu + camber + roll steer; sem compliance, torque de
    alinhamento e tração)"
    seguido de " · Subesterço" (K > 0), " · Sobresterço" (K < 0) ou " · Neutro" (só K == 0 exato; banda de neutro
    só por EDR). K None: "N/A: " + motivo. Prefixo "DEMONSTRATIVO · " se a pior origem não for "● Dado do TX"
    (D16), também no N/A, como em equilibrio.texto_veredito.
    """
    if p.k_total is None:
        texto = "N/A: " + (p.motivo or "")
    else:
        valor = f"{para_graus_por_g(p.k_total):+.2f}".replace(".", ",")
        if p.k_total > 0.0:
            rotulo = "Subesterço"
        elif p.k_total < 0.0:
            rotulo = "Sobresterço"
        else:
            rotulo = "Neutro"
        texto = (f"K = {valor} °/g (pneus + transferência + deslocamento do pneu + camber + roll steer; sem "
                 f"compliance, torque de alinhamento e tração) · {rotulo}")
    return texto if pior_origem == "● Dado do TX" else "DEMONSTRATIVO · " + texto


# ---------------------------------------------------------------------------
# Verificação cruzada pela forma do livro: C_α = a·Fz − b·Fz² e K_llt aproximado (spec §6, último item)
# ---------------------------------------------------------------------------

def ajuste_polinomio_rigidez(ds, n: int = 21) -> tuple[float, float, float]:
    """Ajuste por mínimos quadrados de C_α = a·Fz − b·Fz² (Gillespie eqs. 6-36 a 6-38, p. 215) a rigidez_deriva.

    n cargas igualmente espaçadas de FZMIN a FZMAX do .tir, γ = 0. Devolve (a [1/rad], b [1/(rad·N)], r), com r
    o resíduo relativo máximo, max|C_ajuste − C|/C. Sem termo constante, como no livro (C_α(0) = 0).
    """
    if n < 3:
        raise ValueError(f"n deve ser >= 3; recebido {n}.")
    fz_min, fz_max = ds.p["FZMIN"], ds.p["FZMAX"]
    fz = _np.array([fz_min + (fz_max - fz_min) * i / (n - 1) for i in range(n)])
    c = _np.array([_tm.rigidez_deriva(ds, float(f)) for f in fz])
    A = _np.column_stack((fz, -fz ** 2))
    (a, b), *_ = _np.linalg.lstsq(A, c, rcond=None)
    r = float(_np.max(_np.abs(A @ _np.array([a, b]) - c) / _np.abs(c)))
    return float(a), float(b), r


# Passo da diferença central de 2ª ordem de rigidez_deriva em Fz [N] para o b local. C_α(Fz) é suave: o erro de
# truncamento é O(h²) relativo à escala de variação de C (centenas de N); o ruído de arredondamento de rigidez_deriva
# (~1e-7 N/rad) dividido por h² = 400 N² fica ~1e-9, contra b ~ 2e-2 1/(rad·N).
_H_FZ_B_LOCAL = 20.0


def b_local(ds, fz: float) -> float:
    """b local [1/(rad·N)] da forma C_α = a·Fz − b·Fz² (Gillespie eqs. 6-36 a 6-38): b = −½·d²C_α/dFz² no Fz dado.

    Diferença central com passo _H_FZ_B_LOCAL. O centro do estêncil é levado para dentro de [FZMIN + h, FZMAX − h]
    se for preciso, para que nenhuma avaliação saia da faixa do .tir (nada extrapolado, EDR-056).
    """
    h = _H_FZ_B_LOCAL
    centro = min(max(fz, ds.p["FZMIN"] + h), ds.p["FZMAX"] - h)
    c2 = (_tm.rigidez_deriva(ds, centro + h) - 2.0 * _tm.rigidez_deriva(ds, centro)
          + _tm.rigidez_deriva(ds, centro - h)) / h ** 2
    return -0.5 * c2


def cruzamento_transferencia(caso, ay_ms2: float) -> dict:
    """K_llt aproximado do livro (eq. 6-49, `parcela_transferencia_aprox`) contra o exato (`parcelas_k`) em a_y.

    O aproximado usa o b LOCAL de cada eixo (`b_local` no Fz estático por roda do eixo, limitado à faixa), o C_α de
    eixo do PAC2002 na carga estática, os pesos de eixo e ΔFz por pneu de lateral_dfz. O b do ajuste global
    (`ajuste_polinomio_rigidez`) não serve: o resíduo r mede o erro em C, não na curvatura, e o K_llt é a diferença
    de dois termos que amplia o erro de b (ruling do controlador, Task 4). O ajuste global fica só como informação
    (a_global, b_global, r). A aproximação de 1ª ordem vale com C ≫ 2b·ΔFz² (eq. 6-47): o erro relativo esperado é
    da ordem de ε = 2b·ΔFz²/C do eixo mais carregado (maior carga estática de eixo, W). Devolve aprox, exato, eps,
    eps_f, eps_r, b_f, b_r, a_global, b_global, r e motivo. Com b local <= 0 em algum eixo, o polinômio não tem
    sensibilidade à carga no trecho e não há comparação (aprox None; Review Focus 5).
    """
    a_g, b_g, r = ajuste_polinomio_rigidez(caso.ds)
    p = parcelas_k(caso, ay_ms2)
    saida = {"aprox": None, "exato": p.k_transferencia, "eps": None, "eps_f": None, "eps_r": None,
             "b_f": None, "b_r": None, "a_global": a_g, "b_global": b_g, "r": r, "motivo": None}
    fz0, gam0 = _eq.cargas(caso, 0.0), _eq.camber(caso, 0.0)
    for eixo, chave in (("F", "b_f"), ("R", "b_r")):
        rodas = _eq._rodas(eixo)
        if _eq._descolamento(fz0, rodas) is None:
            fz_u, _, _ = _eq._entrada_limitada(caso, rodas, fz0, gam0)
            saida[chave] = b_local(caso.ds, fz_u[rodas[1]])   # roda externa; estático: as duas iguais
    if saida["b_f"] is not None and saida["b_r"] is not None and (saida["b_f"] <= 0.0 or saida["b_r"] <= 0.0):
        saida["motivo"] = MOTIVO_SEM_SENSIBILIDADE
        return saida
    if p.k_transferencia is None or p.k_pneus is None:
        saida["motivo"] = p.motivo
        return saida
    W_f, W_r = _pesos_eixo(caso)
    cf, _, _ = _rigidez_eixo(caso, "F", fz0, gam0)
    cr, _, _ = _rigidez_eixo(caso, "R", fz0, gam0)
    lat = lateral_dfz(caso.cfg, ay_ms2)
    dff, dfr = lat["front_axle"], lat["rear_axle"]
    bf, br = saida["b_f"], saida["b_r"]
    saida["aprox"] = parcela_transferencia_aprox(W_f, cf, bf, dff, W_r, cr, br, dfr)
    saida["eps_f"] = 2.0 * bf * dff ** 2 / cf
    saida["eps_r"] = 2.0 * br * dfr ** 2 / cr
    saida["eps"] = saida["eps_f"] if W_f >= W_r else saida["eps_r"]
    return saida
