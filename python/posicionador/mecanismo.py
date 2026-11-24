"""
Mecanismo de atuação por construção (push rod + rocker + amortecedor) do posicionador (EDR-076).

Reproduz a regra `montar(x, J)` do script de atuação do script de atuação (t11_atuacao.py, sha256 na origem da v20,
`data/posicionador/origem_v20_script.json`), em SI e nos eixos ISO 8855 do canto FL:
- J = junta `LCA_OUT` (push rod só na bandeja inferior, usuário 2026-11-17);
- direção do amortecedor ud = (cos el · cos az, cos el · sin az, sin el);
- plano do mecanismo contém J, o pivô Pv e ud; eixo do rocker = n = unit((Pv − J) × ud);
- ponto do push rod no rocker A0: o push rod, saindo de J, é tangente ao círculo de raio r1 em volta de Pv (fica
  perpendicular ao braço r1 no estático), na tangente LADO_ROCKER = −1 do script;
- ponto do push rod na bandeja O0 = J + DJ · unit(A0 − J) (sobre a linha que passa pelo centro da junta);
- olhal do rocker B0 = Pv + r2 · Rot(n, φB) · (A0 − Pv)/r1;
- r2: dado, ou resolvido para MR(0) = MR_ALVO (brentq em [0,2·r1; 3·r1]); MR(0) não depende de onde o olhal C fica na
  reta do amortecedor, só da direção ud;
- olhal no chassi C = B0 + t·ud, com t tal que |B(dz = −DROOP) − C| = EYE (troca a regra do script,
  C = B0 + (EYE − DROOP/MR_ALVO)·ud, pela exata).

`construir` nunca levanta exceção por geometria ruim: devolve `Construcao(hardpoints=None, motivo=...)`.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

import hardpoints as hp
import kinematics_model as km

LADO_ROCKER = -1          # t11_atuacao.py, bloco CONFIGURAÇÃO: qual das duas tangentes do push rod ao círculo do rocker
EIXO_B_M = 0.05           # ROCKER_AXIS_B = Pv + 0,05 m · n (o comprimento só define a direção do eixo)
JUNTA = "FL_LCA_OUT"
TOL_PLANO_M = 1e-9        # |(Pv − J) × ud| abaixo disso: plano degenerado
FAIXA_R2 = (0.2, 3.0)     # r2 em [0,2·r1; 3·r1]
SUFIXO_REV = " + atuação por construção (posicionador)"    # no geometry_rev do conjunto construído (uma vez só)
SUFIXO_FONTE = "; grupo pushrod por posicionador.mecanismo.construir (EDR-076)"


@dataclass(frozen=True)
class Variaveis:
    pivo_m: np.ndarray    # pivô do rocker (X, Y, Z) [m]
    az_rad: float         # azimute do amortecedor (0 = para a frente, + = para a esquerda)
    el_rad: float         # elevação do amortecedor (+ = subindo para a frente)
    r1_m: float           # braço do rocker do lado do push rod
    phi_b_rad: float      # ângulo entre os braços do rocker, no plano (em volta de n)

    @classmethod
    def da_semente_do_script(cls, x):
        """x do script (8 números: pivô em mm, az e el em °, r1 em mm, φB em °, r2 em mm) → Variaveis em SI.
        O r2 (x[7]) não entra: passe `r2_m = x[7]/1000` a `construir` para forçá-lo."""
        return cls(pivo_m=np.asarray(x[0:3], dtype=float) / 1000.0, az_rad=float(np.radians(x[3])),
                   el_rad=float(np.radians(x[4])), r1_m=float(x[5]) / 1000.0, phi_b_rad=float(np.radians(x[6])))


@dataclass
class Construcao:
    hardpoints: "hp.HardpointSet | None"   # v10 + grupo pushrod (None se a geometria não fecha)
    r2_m: float | None
    motivo: str | None                     # por que não fechou (None se fechou)


def _unit(v):
    return v / np.linalg.norm(v)


def _rot(eixo, ang):
    """Rodrigues: rotação de `ang` em volta de `eixo` (mesma convenção de kinlib.rot)."""
    k = _unit(eixo)
    K = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return np.eye(3) + np.sin(ang) * K + (1.0 - np.cos(ang)) * K @ K


def direcao_amortecedor(az_rad, el_rad):
    ce = np.cos(el_rad)
    return np.array([ce * np.cos(az_rad), ce * np.sin(az_rad), np.sin(el_rad)])


def _montar_conjunto(hs_v10, pontos):
    """v10 + grupo pushrod, validado pelo schema (build_hardpoint_set)."""
    st = hs_v10.points[JUNTA].status
    linhas = [[pid, repr(float(p.xyz[0])), repr(float(p.xyz[1])), repr(float(p.xyz[2])), p.component, p.status]
              for pid, p in hs_v10.points.items()]
    for chave, (xyz, comp) in pontos.items():
        linhas.append([f"FL_{chave}", repr(float(xyz[0])), repr(float(xyz[1])), repr(float(xyz[2])), comp, st])
    meta = dict(hs_v10.meta)
    if not str(meta["geometry_rev"]).endswith(SUFIXO_REV):
        meta["geometry_rev"] = f"{meta['geometry_rev']}{SUFIXO_REV}"
    if not str(meta["source"]).endswith(SUFIXO_FONTE):
        meta["source"] = f"{meta['source']}{SUFIXO_FONTE}"
    return hp.build_hardpoint_set(linhas, meta)


def _pontos(Pv, n, A0, O0, B0, C):
    return {"PUSH_OUT": (O0, "LCA"), "PUSH_IN": (A0, "ROCKER"), "ROCKER_AXIS_A": (Pv, "CHASSIS"),
            "ROCKER_AXIS_B": (Pv + EIXO_B_M * n, "CHASSIS"), "ROCKER_SPRING": (B0, "ROCKER"),
            "SPRING_CHASSIS": (C, "CHASSIS")}


def construir(hs_v10, v: Variaveis, cfg, r2_m=None):
    """Constrói o grupo pushrod sobre os pontos fixos `hs_v10`. Com `r2_m` dado, não resolve o MR."""
    J = hs_v10.points[JUNTA].xyz.astype(float)
    Pv = np.asarray(v.pivo_m, dtype=float)
    r1 = float(v.r1_m)
    dj = float(cfg.valor("dj_m"))
    droop = float(cfg.valor("curso_droop_m"))
    eye = float(cfg.valor("olho_a_olho_m"))
    mr_alvo = float(cfg.valor("mr_alvo"))

    ud = direcao_amortecedor(v.az_rad, v.el_rad)
    n = np.cross(Pv - J, ud)
    if np.linalg.norm(n) < TOL_PLANO_M:
        return Construcao(None, r2_m, "plano degenerado: pivô sobre a junta LCA_OUT ou alinhado com ela na direção do "
                                      "amortecedor ((Pv − J) × ud ≈ 0)")
    n = _unit(n)
    d = Pv - J
    L = float(np.linalg.norm(d))
    if not r1 > 0.0:
        return Construcao(None, r2_m, f"braço r1 = {r1 * 1e3:.3f} mm não positivo")
    if r1 >= L:
        return Construcao(None, r2_m, f"braço r1 = {r1 * 1e3:.3f} mm ≥ distância pivô–junta {L * 1e3:.3f} mm: "
                                      "o push rod não tangencia o círculo do rocker")
    beta = np.arcsin(r1 / L)
    u = d / L
    perp = np.cross(n, u)
    A0 = J + np.sqrt(L * L - r1 * r1) * (np.cos(beta) * u + LADO_ROCKER * np.sin(beta) * perp)
    lj = float(np.linalg.norm(A0 - J))
    if dj >= lj:
        return Construcao(None, r2_m, f"DJ = {dj * 1e3:.1f} mm ≥ distância junta–rocker {lj * 1e3:.3f} mm: "
                                      "push rod de comprimento nulo ou negativo")
    O0 = J + dj * (A0 - J) / lj
    e_b = _rot(n, v.phi_b_rad) @ ((A0 - Pv) / r1)          # direção unitária do braço r2

    def conjunto(r2, C=None):
        B0 = Pv + r2 * e_b
        if C is None:
            C = B0 + eye * ud                               # provisório: qualquer ponto da reta B0 + t·ud serve ao MR(0)
        return _montar_conjunto(hs_v10, _pontos(Pv, n, A0, O0, B0, C)), B0

    if r2_m is None:
        def f(r2):
            hs_r2, _ = conjunto(r2)
            return km.motion_ratio(km.Corner(hs_r2, "FL"), 0.0)["mr_wheel_per_spring"] - mr_alvo

        a, b = FAIXA_R2[0] * r1, FAIXA_R2[1] * r1
        try:
            fa, fb = f(a), f(b)
        except (km.KinematicsError, hp.HardpointError) as e:
            return Construcao(None, None, f"MR(0) não calculável nas pontas de r2 em [{a * 1e3:.2f}; {b * 1e3:.2f}] mm: {e}")
        if fa * fb > 0.0:
            return Construcao(None, None, f"sem r2 em [{a * 1e3:.2f}; {b * 1e3:.2f}] mm com MR(0) = {mr_alvo}: "
                                          f"MR(0) − alvo = {fa:+.4f} e {fb:+.4f} nas pontas")
        try:
            r2 = float(brentq(f, a, b, xtol=1e-13, rtol=1e-12))
        except (km.KinematicsError, hp.HardpointError, ValueError) as e:
            return Construcao(None, None, f"r2 não resolvido (brentq): {e}")
    else:
        r2 = float(r2_m)
        if not r2 > 0.0:
            return Construcao(None, r2, f"braço r2 = {r2 * 1e3:.3f} mm não positivo")

    # olhal no chassi: a posição do rocker não depende de C, então resolve o droop com o C provisório
    try:
        hs_prov, B0 = conjunto(r2)
        canto = km.Corner(hs_prov, "FL")
        s0 = canto.solve(0.0)
        sd = canto.solve(-droop, q0=s0.q, phi0=s0.phi)
        Bd = canto.pt(sd, "ROCKER_SPRING")
    except km.KinematicsError as e:
        return Construcao(None, r2, f"cinemática falhou no estático ou no droop (dz = −{droop * 1e3:.1f} mm): {e}")
    except hp.HardpointError as e:
        return Construcao(None, r2, f"conjunto de hardpoints inválido: {e}")
    w = B0 - Bd
    pb = float(w @ ud)
    disc = pb * pb - (float(w @ w) - eye * eye)
    if disc < 0.0:
        return Construcao(None, r2, "nenhum ponto da reta do amortecedor fica a EYE do olhal do rocker no droop")
    t = -pb + np.sqrt(disc)                                  # raiz maior: C à frente de B0 na direção ud
    if t <= 0.0:
        return Construcao(None, r2, f"olhal no chassi atrás do olhal do rocker na reta do amortecedor (t = {t * 1e3:.3f} mm)")
    try:
        hs_final, _ = conjunto(r2, B0 + t * ud)
    except hp.HardpointError as e:
        return Construcao(None, r2, f"conjunto de hardpoints inválido: {e}")
    return Construcao(hs_final, r2, None)
