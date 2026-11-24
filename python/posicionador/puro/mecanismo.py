"""
Mecanismo de atuação por construção em Python puro: porte de `posicionador.mecanismo` (a regra e o raciocínio estão na
docstring de lá). Mesma regra, mesmos números; entrada e saída em dicionários {id: (xyz, componente)} em vez de
`HardpointSet`. `construir` nunca levanta exceção por geometria ruim: devolve `Construcao(pontos=None, motivo=...)`.
"""
import math
from dataclasses import dataclass

from posicionador.puro import linalg as la
from posicionador.puro.cinematica import Canto, ErroCinematica, razao_de_movimento
from posicionador.puro.otimizacao import brentq

LADO_ROCKER = -1
EIXO_B_M = 0.05
JUNTA = "FL_LCA_OUT"
TOL_PLANO_M = 1e-9
FAIXA_R2 = (0.2, 3.0)


@dataclass(frozen=True)
class Variaveis:
    pivo_m: tuple
    az_rad: float
    el_rad: float
    r1_m: float
    phi_b_rad: float
    delta_rad: float = 0.0

    @classmethod
    def da_semente_do_script(cls, x):
        return cls(pivo_m=tuple(float(v) / 1000.0 for v in x[0:3]), az_rad=math.radians(x[3]),
                   el_rad=math.radians(x[4]), r1_m=float(x[5]) / 1000.0, phi_b_rad=math.radians(x[6]),
                   delta_rad=math.radians(x[8]) if len(x) > 8 else 0.0)


@dataclass
class Construcao:
    pontos: "dict | None"        # v10 + grupo pushrod, {id: (xyz, componente)}; None se a geometria não fecha
    r2_m: "float | None"
    motivo: "str | None"


def direcao_amortecedor(az_rad, el_rad):
    ce = math.cos(el_rad)
    return (ce * math.cos(az_rad), ce * math.sin(az_rad), math.sin(el_rad))


def canto_fl(pontos):
    """Canto FL a partir dos pontos {FL_<chave>: (xyz, comp)}."""
    return Canto({k[3:]: v for k, v in pontos.items() if k.startswith("FL_")}, lado=+1)


def _grupo(Pv, n, A0, O0, B0, C):
    return {"FL_PUSH_OUT": (O0, "LCA"), "FL_PUSH_IN": (A0, "ROCKER"), "FL_ROCKER_AXIS_A": (Pv, "CHASSIS"),
            "FL_ROCKER_AXIS_B": (la.add(Pv, la.mul(n, EIXO_B_M)), "CHASSIS"), "FL_ROCKER_SPRING": (B0, "ROCKER"),
            "FL_SPRING_CHASSIS": (C, "CHASSIS")}


def construir(v10, v: Variaveis, cfg, r2_m=None):
    """v10 = {id: (xyz, componente)} dos pontos fixos. `cfg` = posicionador.config.Config (só stdlib; `cfg.valor`)."""
    J = la.vec(v10[JUNTA][0])
    Pv = la.vec(v.pivo_m)
    r1 = float(v.r1_m)
    dj = float(cfg.valor("dj_m"))
    droop = float(cfg.valor("curso_droop_m"))
    eye = float(cfg.valor("olho_a_olho_m"))
    mr_alvo = float(cfg.valor("mr_alvo"))

    ud = direcao_amortecedor(v.az_rad, v.el_rad)
    n = la.cross(la.sub(Pv, J), ud)
    if la.norm(n) < TOL_PLANO_M:
        return Construcao(None, r2_m, "plano degenerado: pivô sobre a junta LCA_OUT ou alinhado com ela na direção do "
                                      "amortecedor ((Pv − J) × ud ≈ 0)")
    n = la.unit(n)
    d = la.sub(Pv, J)
    L = la.norm(d)
    if not r1 > 0.0:
        return Construcao(None, r2_m, f"braço r1 = {r1 * 1e3:.3f} mm não positivo")
    if r1 >= L:
        return Construcao(None, r2_m, f"braço r1 = {r1 * 1e3:.3f} mm ≥ distância pivô–junta {L * 1e3:.3f} mm: "
                                      "o push rod não tangencia o círculo do rocker")
    beta = math.asin(r1 / L)
    u = la.mul(d, 1.0 / L)
    perp = la.cross(n, u)
    A0 = la.add(J, la.mul(la.add(la.mul(u, math.cos(beta)), la.mul(perp, LADO_ROCKER * math.sin(beta))),
                          math.sqrt(L * L - r1 * r1)))
    if v.delta_rad:
        A0 = la.add(Pv, la.matvec(la.rot_eixo(n, float(v.delta_rad)), la.sub(A0, Pv)))
    lj = la.norm(la.sub(A0, J))
    if dj >= lj:
        return Construcao(None, r2_m, f"DJ = {dj * 1e3:.1f} mm ≥ distância junta–rocker {lj * 1e3:.3f} mm: "
                                      "push rod de comprimento nulo ou negativo")
    O0 = la.add(J, la.mul(la.sub(A0, J), dj / lj))
    e_b = la.matvec(la.rot_eixo(n, v.phi_b_rad), la.mul(la.sub(A0, Pv), 1.0 / r1))

    def conjunto(r2, C=None):
        B0 = la.add(Pv, la.mul(e_b, r2))
        if C is None:
            C = la.add(B0, la.mul(ud, eye))
        p = dict(v10)
        p.update(_grupo(Pv, n, A0, O0, B0, C))
        return p, B0

    if r2_m is None:
        def f(r2):
            p, _ = conjunto(r2)
            return razao_de_movimento(canto_fl(p), 0.0)["mr_wheel_per_spring"] - mr_alvo

        a, b = FAIXA_R2[0] * r1, FAIXA_R2[1] * r1
        try:
            fa, fb = f(a), f(b)
        except ErroCinematica as e:
            return Construcao(None, None, f"MR(0) não calculável nas pontas de r2 em [{a * 1e3:.2f}; {b * 1e3:.2f}] mm: {e}")
        if fa * fb > 0.0:
            return Construcao(None, None, f"sem r2 em [{a * 1e3:.2f}; {b * 1e3:.2f}] mm com MR(0) = {mr_alvo}: "
                                          f"MR(0) − alvo = {fa:+.4f} e {fb:+.4f} nas pontas")
        try:
            r2 = float(brentq(f, a, b, xtol=1e-13, rtol=1e-12))
        except (ErroCinematica, ValueError) as e:
            return Construcao(None, None, f"r2 não resolvido (brentq): {e}")
    else:
        r2 = float(r2_m)
        if not r2 > 0.0:
            return Construcao(None, r2, f"braço r2 = {r2 * 1e3:.3f} mm não positivo")

    try:
        p_prov, B0 = conjunto(r2)
        canto = canto_fl(p_prov)
        s0 = canto.resolver(0.0)
        sd = canto.resolver(-droop, q0=s0.q, phi0=s0.phi)
        Bd = canto.ponto(sd, "ROCKER_SPRING")
    except ErroCinematica as e:
        return Construcao(None, r2, f"cinemática falhou no estático ou no droop (dz = −{droop * 1e3:.1f} mm): {e}")
    w = la.sub(B0, Bd)
    pb = la.dot(w, ud)
    disc = pb * pb - (la.dot(w, w) - eye * eye)
    if disc < 0.0:
        return Construcao(None, r2, "nenhum ponto da reta do amortecedor fica a EYE do olhal do rocker no droop")
    t = -pb + math.sqrt(disc)
    if t <= 0.0:
        return Construcao(None, r2, f"olhal no chassi atrás do olhal do rocker na reta do amortecedor (t = {t * 1e3:.3f} mm)")
    p_final, _ = conjunto(r2, la.add(B0, la.mul(ud, t)))
    return Construcao(p_final, r2, None)
