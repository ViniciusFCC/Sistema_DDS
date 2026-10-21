"""
kinematics_model_V2_0.py — Kinematics V2.0.

Parte 1 (herdada da V1.0, funções inalteradas): SUS-402 (Roll Center, interseção 2D vista frontal),
SUS-403 (IC frontal) e SUS-406 (IC lateral -> tan(phi) -> Anti-Dive/Anti-Squat, método V1).
Parte 2 (nova na V2.0): solver cinemático 3D de double wishbone a partir de hardpoints
(camber, toe, caster, KPI, scrub, trail, track/wheelbase change, MR, esterçamento, IC e RC
cinemáticos, anti-dive/squat com sinal físico).

IMPORTANTE — limites deliberados:
- Data Type = MODEL, propósito = cross-check (nunca autoritativo). O OptimumKinematics
  continua sendo a REFERENCE oficial (SUS-401/403/404/405; DR-009).
- Corpos rígidos, juntas esféricas ideais, sem compliance/folga; roda sem rotação própria.
- Contact patch tratado como ponto solidário à roda (aproximação; ver SUS-411).
- Sem hardpoints reais do carro: toda validação numérica é por geometria SINTÉTICA e por
  verificações independentes (ver test_kinematics_model_V2_0.py). TC-011 segue NOT_VALIDATED.
"""

__version__ = "V2.0"

import math
from dataclasses import dataclass


@dataclass
class Hardpoint:
    """Um hardpoint, projetado em vista frontal (Y, Z). X e ignorado neste modulo."""
    y: float
    z: float


def line_intersection(p1: Hardpoint, p2: Hardpoint, p3: Hardpoint, p4: Hardpoint,
                      view: str = "frontal") -> Hardpoint:
    """Interseção de duas retas 2D, cada uma definida por dois pontos (Y,Z).

    Levanta ValueError se as retas forem paralelas (IC no infinito -
    braços paralelos em vista frontal, wheel travel puramente vertical).
    """
    x1, y1 = p1.y, p1.z
    x2, y2 = p2.y, p2.z
    x3, y3 = p3.y, p3.z
    x4, y4 = p4.y, p4.z
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        raise ValueError(
            f"Retas paralelas em vista {view} - Instant Center no infinito "
            "(braços paralelos entre si; geometria de swing-axle degenerada para este metodo 2D)"
        )
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return Hardpoint(y=px, z=py)


def instant_center_front_view(lca_outer: Hardpoint, lca_inner: Hardpoint,
                               uca_outer: Hardpoint, uca_inner: Hardpoint) -> Hardpoint:
    """SUS-403: Instant Center em vista frontal.

    IC = interseção da reta do braço inferior (LCA_outer-LCA_inner) com a
    reta do braço superior (UCA_outer-UCA_inner).
    """
    return line_intersection(lca_outer, lca_inner, uca_outer, uca_inner)


def roll_center_height(contact_patch: Hardpoint, instant_center: Hardpoint) -> float:
    """SUS-402: Roll Center height (Z), na posição Y=0 (centerline).

    RC = onde a reta (Contact Patch -> Instant Center) cruza Y=0.
    contact_patch.z deve ser 0 (solo, ja convertido via SUS-000).
    """
    y_cp, z_cp = contact_patch.y, contact_patch.z
    y_ic, z_ic = instant_center.y, instant_center.z
    if abs(y_ic - y_cp) < 1e-9:
        raise ValueError("Instant Center tem o mesmo Y do contact patch - reta vertical, RC indefinido neste metodo")
    return z_cp + (z_ic - z_cp) / (y_ic - y_cp) * (0 - y_cp)


def roll_center_model_check(lca_outer: Hardpoint, lca_inner: Hardpoint,
                             uca_outer: Hardpoint, uca_inner: Hardpoint,
                             contact_patch: Hardpoint) -> dict:
    """SUS-402 completo: retorna o IC (SUS-403) e o RC (SUS-402) a partir dos hardpoints.

    Uso pretendido: cross-check contra o RC REFERENCE do OptimumKinematics (SUS-401).
    NUNCA usar o resultado daqui como REFERENCE - e MODEL/CHECK.
    """
    ic = instant_center_front_view(lca_outer, lca_inner, uca_outer, uca_inner)
    rc = roll_center_height(contact_patch, ic)
    return {"instant_center": ic, "roll_center_height": rc}


# =====================================================================
# SUS-406 — Instant Center (vista lateral) -> Anti-Dive / Anti-Squat
# LEGADO (EDR-048): o método do ponto médio das buchas e a forma tan(phi) = Z_IC/|d| sem sinal NÃO
# aparecem na literatura (Gillespie p. 249: IC na interseção projetada dos eixos dos braços; Milliken
# p. 612-620) e dão %AD sem sentido em geometria realista (-680,7 contra 36,3; TC-KIN-114). Ficam só
# para os testes de regressão. Use kinematic_centers + force_line_slope + anti_*_percent_signed, com o
# ponto de reação de REACTION_POINT.
# =====================================================================

# Ponto de reação da linha de força lateral, por efeito (EDR-048; Milliken p. 618-619, Fig. 17.12, 17.13
# e 17.15; Gillespie eq. 7-17 a 7-19). Configuração do carro informada pelo usuário em 2026-10-19:
# freios dentro da roda, em volta do cubo (outboard, sem redução planetária) e motor no chassi, atrás,
# com o torque de tração reagido pelo chassi.
REACTION_POINT = {
    "anti_dive_front": "contact_patch",   # freio outboard: torque reagido pela manga
    "anti_lift_rear": "contact_patch",    # idem, na frenagem
    "anti_squat_rear": "wheel_center",    # motor no chassi + semieixos: Milliken Fig. 17.15(b)
}

def side_view_inner_midpoint(bushing_front: Hardpoint, bushing_rear: Hardpoint) -> Hardpoint:
    """Passo 0 do SUS-406: ponto medio das buchas dianteira/traseira do braco,
    representando o eixo de pivo interno em vista lateral (projecao X-Z).

    Diferente do SUS-402: o eixo de pivo (~paralelo a X) projeta como uma RETA
    ao longo de X em vista lateral, nao um ponto - por isso usamos o ponto medio
    como aproximacao de primeira ordem, em vez do "mesmo ponto" usado no SUS-402.
    """
    return Hardpoint(y=(bushing_front.y + bushing_rear.y) / 2,
                      z=(bushing_front.z + bushing_rear.z) / 2)


def instant_center_side_view(lca_outer: Hardpoint, lca_bushing_front: Hardpoint, lca_bushing_rear: Hardpoint,
                              uca_outer: Hardpoint, uca_bushing_front: Hardpoint, uca_bushing_rear: Hardpoint) -> Hardpoint:
    """SUS-406: Instant Center em vista lateral (projecao X-Z; usar hp.y para X, hp.z para Z).

    IC = interseccao da reta do braco inferior (LCA_outer -> ponto medio das buchas LCA)
         com a reta do braco superior (UCA_outer -> ponto medio das buchas UCA).
    """
    lca_inner_mid = side_view_inner_midpoint(lca_bushing_front, lca_bushing_rear)
    uca_inner_mid = side_view_inner_midpoint(uca_bushing_front, uca_bushing_rear)
    return line_intersection(lca_outer, lca_inner_mid, uca_outer, uca_inner_mid, view="lateral")


def tan_phi_from_ic(instant_center: Hardpoint, contact_patch_x: float) -> float:
    """SUS-406, passo 2: tan(phi) = Z_IC / |X_IC - X_CP|.

    d e sempre tomado em modulo (SUS-406, Sign Convention) - a formula de
    SUS-301/302 ja assume tan(phi) >= 0.
    """
    d = abs(instant_center.y - contact_patch_x)
    if d < 1e-9:
        raise ValueError("Instant Center na mesma posicao X do contact patch - tan(phi) indefinido (assintota)")
    return instant_center.z / d


def anti_dive_squat_model_check(lca_outer: Hardpoint, lca_bushing_front: Hardpoint, lca_bushing_rear: Hardpoint,
                                 uca_outer: Hardpoint, uca_bushing_front: Hardpoint, uca_bushing_rear: Hardpoint,
                                 contact_patch_x: float, force_fraction: float,
                                 wheelbase: float, cg_height: float) -> dict:
    """LEGADO (EDR-048), não usar em cálculo novo. SUS-406 V1 + SUS-301/302 V1: IC lateral -> tan(phi) -> %AD ou %AS.

    force_fraction = FB_f (Anti-Dive, frenagem) ou TF_r (Anti-Squat, tracao).
    NUNCA usar para alterar a magnitude do load transfer longitudinal (SUS-102) -
    ver hipotese congelada na secao 17.3/DR-006.
    """
    ic = instant_center_side_view(lca_outer, lca_bushing_front, lca_bushing_rear,
                                   uca_outer, uca_bushing_front, uca_bushing_rear)
    tan_phi = tan_phi_from_ic(ic, contact_patch_x)
    pct = force_fraction * tan_phi * (wheelbase / cg_height) * 100
    return {"instant_center": ic, "tan_phi": tan_phi, "percent": pct}


# =====================================================================
# V2.0 — Solver cinemático 3D de double wishbone (MODEL / cross-check)
# =====================================================================
# Escopo: um canto por vez, corpos rígidos, juntas esféricas ideais, sem compliance
# nem folga, roda sem rotação própria. Entrada: HardpointSet (hardpoints_V2_0.py).
# Natureza: Data Type = MODEL, propósito = cross-check. NÃO substitui o OptimumKinematics
# (REFERENCE, SUS-401/403/404/405) — DR-009. Ver hardpoint-schema-V2.0.md e as fichas
# SUS-407 a SUS-413 do Engineering Standard V2.0.
#
# Formulação: pose da manga (upright) = 6 incógnitas (vetor de rotação + translação).
# 5 restrições de comprimento fixo (2 do LCA, 2 do UCA, 1 da barra de direção) + 1
# restrição de curso (Z do centro da roda) fecham o sistema 6x6, resolvido por Newton
# com continuação (mantém o ramo da solução).

import numpy as np

from hardpoints import HardpointSet, HardpointError  # noqa: F401

_PARALLEL_REL_TOL = 1e-9


class KinematicsError(RuntimeError):
    """Falha numérica ou geométrica do solver (não convergiu, singular, configuração impossível)."""


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n < 1e-14:
        raise KinematicsError("vetor de comprimento nulo")
    return v / n


def _skew(v):
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def _rot_vec(w):
    """Rodrigues: matriz de rotação do vetor de rotação w (regra da mão direita)."""
    th = float(np.linalg.norm(w))
    K = _skew(w)
    if th < 1e-12:
        return np.eye(3) + K + 0.5 * (K @ K)
    return np.eye(3) + (np.sin(th) / th) * K + ((1.0 - np.cos(th)) / th ** 2) * (K @ K)


def _rot_axis(u, theta):
    return _rot_vec(np.asarray(u, dtype=float) * theta)


@dataclass
class Solution:
    q: np.ndarray          # [wx, wy, wz, tx, ty, tz] da manga
    travel: float          # curso da roda [m] (Z do centro da roda, bump positivo)
    steer: float           # deslocamento da cremalheira [m]
    phi: float = 0.0       # ângulo do rocker [rad] (0 se não há pushrod)


class Corner:
    """Um canto de double wishbone. Todas as coordenadas em ISO 8855 (X frente, Y esquerda, Z cima)."""

    def __init__(self, hs: "HardpointSet", name: str, rack_dir=(0.0, 1.0, 0.0)):
        if name not in hs.corners_present():
            raise KinematicsError(f"canto {name} ausente no conjunto de hardpoints")
        cp = hs.corner_points(name)
        self.name = name
        self.side = +1 if name.endswith("L") else -1
        self.p0 = {k: p.xyz.copy() for k, p in cp.items()}
        self.comp = {k: p.component for k, p in cp.items()}
        self.ground_z = float(hs.meta["ground_plane_z_m"])
        self.rack_dir = _unit(rack_dir)
        self.c0 = self.p0["WHEEL_CENTER"].copy()
        d = lambda a, b: float(np.linalg.norm(self.p0[a] - self.p0[b]))
        self.L = {"LF": d("LCA_OUT", "LCA_IN_F"), "LR": d("LCA_OUT", "LCA_IN_R"),
                  "UF": d("UCA_OUT", "UCA_IN_F"), "UR": d("UCA_OUT", "UCA_IN_R"),
                  "T": d("TIE_OUT", "TIE_IN")}
        self.has_push = "PUSH_OUT" in self.p0
        if self.has_push:
            self.Lpush = d("PUSH_OUT", "PUSH_IN")
        a = _unit(self.p0["SPINDLE_PT"] - self.c0)
        if self.side * a[1] <= 0:
            raise KinematicsError("SPINDLE_PT deve estar para fora do centro da roda")

    # ---------------- pose ----------------
    def _upright_pt(self, q, P0):
        return self.c0 + _rot_vec(q[:3]) @ (P0 - self.c0) + q[3:6]

    def _res(self, q, travel, steer):
        p0, L = self.p0, self.L
        PL = self._upright_pt(q, p0["LCA_OUT"])
        PU = self._upright_pt(q, p0["UCA_OUT"])
        PT = self._upright_pt(q, p0["TIE_OUT"])
        WC = self._upright_pt(q, p0["WHEEL_CENTER"])
        Tin = p0["TIE_IN"] + steer * self.rack_dir

        def dist_res(P, A, l0):
            return (np.dot(P - A, P - A) - l0 * l0) / (2.0 * l0)

        return np.array([
            dist_res(PL, p0["LCA_IN_F"], L["LF"]), dist_res(PL, p0["LCA_IN_R"], L["LR"]),
            dist_res(PU, p0["UCA_IN_F"], L["UF"]), dist_res(PU, p0["UCA_IN_R"], L["UR"]),
            dist_res(PT, Tin, L["T"]),
            WC[2] - self.c0[2] - travel,
        ])

    def solve(self, travel=0.0, steer=0.0, q0=None, phi0=0.0, tol=1e-12, maxit=80):
        """Resolve a pose da manga para o curso/esterçamento dados. Levanta KinematicsError se falhar."""
        q = np.zeros(6) if q0 is None else np.array(q0, dtype=float)
        eps = 1e-7
        for _ in range(maxit):
            r = self._res(q, travel, steer)
            n0 = float(np.linalg.norm(r))
            if n0 < tol:
                break
            J = np.empty((6, 6))
            for j in range(6):
                dq = np.zeros(6)
                dq[j] = eps
                J[:, j] = (self._res(q + dq, travel, steer) - self._res(q - dq, travel, steer)) / (2 * eps)
            if np.linalg.cond(J) > 1e10:
                raise KinematicsError("jacobiano singular/mal condicionado: configuração degenerada ou curso fora do alcance")
            try:
                dq = np.linalg.solve(J, -r)
            except np.linalg.LinAlgError:
                raise KinematicsError("jacobiano singular")
            a = 1.0
            while a > 1e-4:
                qn = q + a * dq
                if np.linalg.norm(self._res(qn, travel, steer)) < n0:
                    break
                a *= 0.5
            q = qn
        if np.linalg.norm(self._res(q, travel, steer)) > 1e-10:
            raise KinematicsError(f"Newton não convergiu para curso={travel*1e3:.2f} mm, cremalheira={steer*1e3:.2f} mm "
                                  "(fora do alcance cinemático ou geometria inconsistente)")
        sol = Solution(q=q, travel=float(travel), steer=float(steer))
        if self.has_push:
            sol.phi = self._solve_rocker(sol, phi0)
        return sol

    # ---------------- pontos em pose ----------------
    def _wb_angle(self, sol, which):
        A = self.p0[f"{which}_IN_F"]
        u = _unit(self.p0[f"{which}_IN_R"] - A)
        v0 = self.p0[f"{which}_OUT"] - A
        v = self._upright_pt(sol.q, self.p0[f"{which}_OUT"]) - A
        v0p, vp = v0 - (v0 @ u) * u, v - (v @ u) * u
        return float(np.arctan2(u @ np.cross(v0p, vp), v0p @ vp))

    def _rocker_pt(self, key, phi):
        A = self.p0["ROCKER_AXIS_A"]
        u = _unit(self.p0["ROCKER_AXIS_B"] - A)
        return A + _rot_axis(u, phi) @ (self.p0[key] - A)

    def _push_out(self, sol):
        comp = self.comp["PUSH_OUT"]
        if comp == "UPRIGHT":
            return self._upright_pt(sol.q, self.p0["PUSH_OUT"])
        A = self.p0[f"{comp}_IN_F"]
        u = _unit(self.p0[f"{comp}_IN_R"] - A)
        return A + _rot_axis(u, self._wb_angle(sol, comp)) @ (self.p0["PUSH_OUT"] - A)

    def _solve_rocker(self, sol, phi0):
        po = self._push_out(sol)
        f = lambda ph: float(np.linalg.norm(self._rocker_pt("PUSH_IN", ph) - po)) - self.Lpush
        phi, h = float(phi0), 1e-7
        for _ in range(80):
            fv = f(phi)
            if abs(fv) < 1e-13:
                return phi
            d = (f(phi + h) - f(phi - h)) / (2 * h)
            if abs(d) < 1e-12:
                raise KinematicsError("rocker singular (pushrod alinhado com o braço do rocker)")
            step = -fv / d
            while abs(step) > 0.5:
                step *= 0.5
            phi += step
        if abs(f(phi)) > 1e-10:
            raise KinematicsError("rocker não convergiu (pushrod incompatível com o curso)")
        return phi

    def pt(self, sol, key):
        comp, P0 = self.comp[key], self.p0[key]
        if comp in ("UPRIGHT", "WHEEL"):
            return self._upright_pt(sol.q, P0)
        if comp == "CHASSIS":
            return P0.copy()
        if comp == "RACK":
            return P0 + sol.steer * self.rack_dir
        if comp in ("LCA", "UCA"):
            A = self.p0[f"{comp}_IN_F"]
            u = _unit(self.p0[f"{comp}_IN_R"] - A)
            return A + _rot_axis(u, self._wb_angle(sol, comp)) @ (P0 - A)
        if comp == "ROCKER":
            return self._rocker_pt(key, sol.phi)
        raise KinematicsError(f"component {comp} não tratado")

    def spring_length(self, sol):
        if not self.has_push:
            raise KinematicsError("canto sem grupo pushrod/rocker/mola")
        return float(np.linalg.norm(self.pt(sol, "ROCKER_SPRING") - self.pt(sol, "SPRING_CHASSIS")))

    # ---------------- métricas de pose ----------------
    def metrics(self, sol):
        """Ângulos e distâncias na pose. Camber>0 = topo para fora; toe>0 = toe-out (arquitetura 17.2)."""
        wc, sp, cpt = (self.pt(sol, k) for k in ("WHEEL_CENTER", "SPINDLE_PT", "CONTACT_PATCH"))
        a = _unit(sp - wc)
        lo, up = self.pt(sol, "LCA_OUT"), self.pt(sol, "UCA_OUT")
        k = _unit(up - lo)
        t = (cpt[2] - lo[2]) / k[2]
        inter = lo + t * k                         # interseção do pino mestre com o solo (Z do contact patch)
        kc = lo + ((wc[2] - lo[2]) / k[2]) * k     # pino mestre na altura do centro da roda (spindle length, Milliken 19.1)
        cp0 = self.p0["CONTACT_PATCH"]
        return {
            "travel_m": sol.travel,
            "camber_deg": float(np.degrees(np.arcsin(-a[2]))),
            "toe_deg": float(np.degrees(np.arcsin(-a[0] / np.hypot(a[0], a[1])))),
            "caster_deg": float(np.degrees(np.arctan2(-k[0], k[2]))),
            "kpi_deg": float(np.degrees(np.arctan2(-self.side * k[1], k[2]))),
            "scrub_radius_m": float(self.side * (cpt[1] - inter[1])),
            "mech_trail_m": float(inter[0] - cpt[0]),
            "spindle_length_m": float(self.side * (wc[1] - kc[1])),
            "track_change_m": float(self.side * (cpt[1] - cp0[1])),
            "wheelbase_change_m": float(cpt[0] - cp0[0]),
            "wheel_center": wc, "contact_patch": cpt,
        }


# ---------------- varreduras ----------------

def sweep(corner: Corner, travels, steer=0.0):
    """Resolve uma lista de cursos [m] com continuação a partir do curso 0. Retorna lista de (Solution, métricas)
    na mesma ordem de `travels`."""
    ref = corner.solve(0.0, steer)
    out = {}
    pos = sorted(t for t in set(travels) if t >= 0.0)
    neg = sorted((t for t in set(travels) if t < 0.0), reverse=True)
    for group in (pos, neg):
        cur = ref
        for t in group:
            cur = corner.solve(t, steer, q0=cur.q, phi0=cur.phi)
            out[t] = cur
    res = []
    for t in travels:
        s = out[t]
        m = corner.metrics(s)
        if corner.has_push:
            m["spring_length_m"] = corner.spring_length(s)
        res.append((s, m))
    return res


def steer_sweep(corner: Corner, rack_positions, travel=0.0):
    """Yaw da roda (positivo = esquerda, ISO 8855) em função do deslocamento da cremalheira [m] (+Y)."""
    ref = corner.solve(travel, 0.0)
    toe0 = corner.metrics(ref)["toe_deg"]
    rows, cur = [], ref
    for s in sorted(rack_positions, key=abs):
        cur = corner.solve(travel, s, q0=cur.q, phi0=cur.phi)
        rows.append((s, corner.side * (corner.metrics(cur)["toe_deg"] - toe0)))
    return sorted(rows)


def steering_ratio(corner: Corner, rack_travel_per_rev_m, ds=1e-4):
    """SUS-601 (MODEL): razão volante/roda = (360/c) / (dδ/ds), com c = curso de cremalheira por volta do pinhão."""
    a = steer_sweep(corner, [-ds, ds])
    dyaw = (a[1][1] - a[0][1]) / (2 * ds)          # deg/m
    if abs(dyaw) < 1e-9:
        raise KinematicsError("roda não esterça com a cremalheira (dδ/ds ≈ 0)")
    return abs((360.0 / rack_travel_per_rev_m) / dyaw)


def motion_ratio(corner: Corner, travel=0.0, dz=1e-5):
    """SUS-409 (MODEL/CHECK): MR [wheel/spring] = |d(curso da roda)/d(comprimento da mola)|. Curso = Z do centro da roda."""
    s0 = corner.solve(travel)
    sp = corner.solve(travel + dz, q0=s0.q, phi0=s0.phi)
    sm = corner.solve(travel - dz, q0=s0.q, phi0=s0.phi)
    dL = (corner.spring_length(sp) - corner.spring_length(sm)) / (2 * dz)
    if abs(dL) < 1e-12:
        raise KinematicsError("mola sem variação de comprimento (MR infinito)")
    return {"mr_wheel_per_spring": abs(1.0 / dL), "dLspring_dz": dL, "spring_length_m": corner.spring_length(s0)}


# ---------------- centros instantâneos cinemáticos (SUS-412) ----------------

def _ic_from_velocities(p1, v1, p2, v2):
    """IC de um movimento plano a partir de dois pontos e suas velocidades projetadas: interseção das normais.
    Retorna {'point': ndarray|None, 'direction': ndarray|None}; 'direction' só se as normais forem paralelas (IC no infinito)."""
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-12 or n2 < 1e-12:
        raise KinematicsError("velocidade projetada nula num ball joint: IC indefinido nesta vista")
    A = np.array([v1, v2])
    det = A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]
    if abs(det) < _PARALLEL_REL_TOL * n1 * n2:
        d = np.array([-v1[1], v1[0]]) / n1
        return {"point": None, "direction": d}
    b = np.array([v1 @ p1, v2 @ p2])
    return {"point": np.linalg.solve(A, b), "direction": None}


def _line_dir(ic, ref):
    return (ic["point"] - ref) if ic["point"] is not None else ic["direction"]


def kinematic_centers(corner: Corner, travel=0.0, steer=0.0, dz=1e-5):
    """IC frontal (Y,Z) e lateral (X,Z) a partir das velocidades 3D dos dois ball joints (diferença central da pose).
    Reduz ao método 2D da V1 quando o mecanismo é plano. Retorna também o contact patch e o centro da roda na pose."""
    s0 = corner.solve(travel, steer)
    sp = corner.solve(travel + dz, steer, q0=s0.q, phi0=s0.phi)
    sm = corner.solve(travel - dz, steer, q0=s0.q, phi0=s0.phi)
    PL, PU = corner.pt(s0, "LCA_OUT"), corner.pt(s0, "UCA_OUT")
    vL = (corner.pt(sp, "LCA_OUT") - corner.pt(sm, "LCA_OUT")) / (2 * dz)
    vU = (corner.pt(sp, "UCA_OUT") - corner.pt(sm, "UCA_OUT")) / (2 * dz)
    fr, sd = [1, 2], [0, 2]
    return {
        "front": _ic_from_velocities(PL[fr], vL[fr], PU[fr], vU[fr]),
        "side": _ic_from_velocities(PL[sd], vL[sd], PU[sd], vU[sd]),
        "contact_patch": corner.pt(s0, "CONTACT_PATCH"), "wheel_center": corner.pt(s0, "WHEEL_CENTER"),
        "solution": s0,
    }


def roll_center_height_kinematic(corner: Corner, travel=0.0, steer=0.0):
    """SUS-412: RC (altura acima do solo, na linha de centro Y=0) = linha contact patch -> IC frontal cruzando Y=0.
    O solo, no referencial do chassi, passa pelo Z do contact patch na pose."""
    c = kinematic_centers(corner, travel, steer)
    cp = c["contact_patch"][[1, 2]]
    d = _line_dir(c["front"], cp)
    if abs(d[0]) < 1e-12:
        raise KinematicsError("linha contact patch->IC vertical: RC indefinido neste método")
    return float(d[1] / d[0] * (0.0 - cp[0]))


def axle_roll_center(corner_left: Corner, corner_right: Corner, travel=0.0):
    """RC do eixo = interseção das linhas contact patch->IC dos dois lados (Y, Z acima do solo). Curso de heave simétrico."""
    pts = []
    for c in (corner_left, corner_right):
        k = kinematic_centers(c, travel)
        cp = k["contact_patch"][[1, 2]]
        pts.append((cp, _line_dir(k["front"], cp)))
    (p1, d1), (p2, d2) = pts
    A = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]])
    if abs(np.linalg.det(A)) < 1e-12 * np.linalg.norm(d1) * np.linalg.norm(d2):
        raise KinematicsError("linhas contact patch->IC paralelas: RC do eixo indefinido")
    t = np.linalg.solve(A, p2 - p1)
    y, z = p1 + t[0] * d1
    return float(y), float(z - p1[1])          # (Y, altura acima do solo; solo = Z do contact patch esquerdo)


def force_line_slope(ic_side, ref_xz):
    """Inclinação dz/dx da linha (ponto de reação -> IC lateral) em vista lateral (ISO 8855: x para frente).
    Retorna None se a linha for vertical (inclinação infinita)."""
    d = _line_dir(ic_side, np.asarray(ref_xz, dtype=float))
    if abs(d[0]) < 1e-12:
        return None
    return float(d[1] / d[0])


def anti_dive_percent_signed(slope, fb_f, wheelbase, cg_height):
    """%AD (SUS-301) com sinal físico: positivo se o IC lateral está ATRÁS e ACIMA do ponto de reação (a linha sobe para trás).
    AD = FB_f * (-slope) * L/h * 100. Diferença para a V1: a V1 usa |d| e assume tan(phi)>=0."""
    return fb_f * (-slope) * (wheelbase / cg_height) * 100.0


def anti_squat_percent_signed(slope, tf_r, wheelbase, cg_height):
    """%AS (SUS-302) com sinal físico: positivo se o IC lateral está À FRENTE e ACIMA do ponto de reação.
    AS = TF_r * slope * L/h * 100."""
    return tf_r * slope * (wheelbase / cg_height) * 100.0


# ---------------- comparação de métodos de IC no pose de referência (diagnóstico de incerteza) ----------------

def ic_methods_at_reference(corner: Corner):
    """Compara definições de IC na pose de referência, para quantificar a incerteza de método.
    Retorna dict com, para cada vista, o IC (ou direção) por método. Métodos:
      - 'kinematic'      : normais às velocidades dos ball joints (solver; V2)
      - 'v1_outer_to_inner': linha ball joint externo -> ponto interno representativo (V1: SUS-402 frontal / SUS-406 lateral)
      - 'pivot_axes'     : (só lateral) retas pelos eixos de pivô projetados (construção usual de fóruns/cursos)
    """
    p = corner.p0
    out = {"front": {}, "side": {}}
    k = kinematic_centers(corner)
    out["front"]["kinematic"], out["side"]["kinematic"] = k["front"], k["side"]

    def hp(a, i):
        return Hardpoint(y=float(a[i[0]]), z=float(a[i[1]]))
    fr, sd = (1, 2), (0, 2)
    mid = lambda a, b: (p[a] + p[b]) / 2
    for view, idx in (("front", fr), ("side", sd)):
        try:
            ic = line_intersection(hp(p["LCA_OUT"], idx), hp(mid("LCA_IN_F", "LCA_IN_R"), idx),
                                   hp(p["UCA_OUT"], idx), hp(mid("UCA_IN_F", "UCA_IN_R"), idx), view=view)
            out[view]["v1_outer_to_inner"] = {"point": np.array([ic.y, ic.z]), "direction": None}
        except ValueError:
            d = (p["LCA_OUT"] - mid("LCA_IN_F", "LCA_IN_R"))[list(idx)]
            out[view]["v1_outer_to_inner"] = {"point": None, "direction": d / np.linalg.norm(d)}
    try:
        ic = line_intersection(hp(p["LCA_IN_F"], sd), hp(p["LCA_IN_R"], sd),
                               hp(p["UCA_IN_F"], sd), hp(p["UCA_IN_R"], sd), view="lateral")
        out["side"]["pivot_axes"] = {"point": np.array([ic.y, ic.z]), "direction": None}
    except ValueError:
        d = (p["LCA_IN_F"] - p["LCA_IN_R"])[list(sd)]
        out["side"]["pivot_axes"] = {"point": None, "direction": d / np.linalg.norm(d)}
    return out


# ---------------- linha de força pelo trabalho virtual (definição primária do MODEL; EDR-053) ----------------
# SAE J670 (Gillespie, Apêndice A): o RC é o ponto, no plano transversal, em que forças laterais na massa suspensa não
# produzem rolagem. Pelo trabalho virtual (corpo rígido, pequeno deslocamento, cremalheira fixa), a força aplicada num
# ponto do conjunto não suspenso não carrega a mola quando é perpendicular à velocidade desse ponto em relação ao curso.
# Logo a linha de força passa pelo ponto de reação e é perpendicular à velocidade dele: contact patch para o anti-dive
# (freio no cubo) e para o RC; centro da roda para o anti-squat com motor no chassi (EDR-048). No mecanismo plano coincide
# com a construção clássica (Milliken p. 612-620; Gillespie p. 249). Ver docs/revisao-metodologica.md §8.

def _twist(corner: Corner, travel=0.0, steer=0.0, dz=1e-5):
    """Movimento instantâneo do conjunto não suspenso por unidade de curso: ω [rad/m] e v(ponto) [m/m] por diferença central."""
    s0 = corner.solve(travel, steer)
    sp = corner.solve(travel + dz, steer, q0=s0.q, phi0=s0.phi)
    sm = corner.solve(travel - dz, steer, q0=s0.q, phi0=s0.phi)
    Rp, Rm = _rot_vec(sp.q[:3]), _rot_vec(sm.q[:3])
    D = Rp @ Rm.T
    W = (D - D.T) / (4 * dz)
    w = np.array([W[2, 1], W[0, 2], W[1, 0]])
    vel = lambda key: (corner.pt(sp, key) - corner.pt(sm, key)) / (2 * dz)
    return s0, w, vel


def force_lines_vw(corner: Corner, travel=0.0, steer=0.0, dz=1e-5):
    """SUS-412 (definição primária, EDR-053): linhas de força pelo trabalho virtual, na pose.
    Retorna inclinações e ICs no plano que contém o ponto de reação (únicos nesse plano):
      - 'side_slope_cp' = dz/dx da linha pelo contact patch (anti-dive com freio no cubo);
      - 'side_slope_wc' = dz/dx da linha pelo centro da roda (anti-squat com motor no chassi);
      - 'rc_height_m'   = altura acima do solo onde a linha frontal pelo contact patch cruza Y = 0;
      - 'ic_front' (Y, Z) no plano X = X_cp; 'ic_side_cp' (X, Z) no plano Y = Y_cp; 'ic_side_wc' no plano Y = Y_wc.
    None quando a linha é vertical ou o IC está no infinito (ω nulo na vista)."""
    s0, w, vel = _twist(corner, travel, steer, dz)
    cp, wc = corner.pt(s0, "CONTACT_PATCH"), corner.pt(s0, "WHEEL_CENTER")
    vcp, vwc = vel("CONTACT_PATCH"), vel("WHEEL_CENTER")
    slope = lambda num, den: None if abs(den) < 1e-12 else float(-num / den)

    def ic_front(P, v):
        return None if abs(w[0]) < 1e-12 else np.array([P[1] - v[2] / w[0], P[2] + v[1] / w[0]])

    def ic_side(P, v):
        return None if abs(w[1]) < 1e-12 else np.array([P[0] + v[2] / w[1], P[2] - v[0] / w[1]])

    sf = slope(vcp[1], vcp[2])                     # dz/dy da linha frontal pelo contact patch
    return {
        "side_slope_cp": slope(vcp[0], vcp[2]), "side_slope_wc": slope(vwc[0], vwc[2]),
        "rc_height_m": None if sf is None else float(sf * (0.0 - cp[1])),
        "front_slope_cp": sf,
        "ic_front": ic_front(cp, vcp), "ic_side_cp": ic_side(cp, vcp), "ic_side_wc": ic_side(wc, vwc),
        "omega_per_m": w, "v_cp": vcp, "v_wc": vwc, "contact_patch": cp, "wheel_center": wc,
    }


def axle_roll_center_vw(corner_left: Corner, corner_right: Corner, travel=0.0):
    """RC do eixo (EDR-053): interseção das linhas de força frontais pelos contact patches. (Y, altura acima do solo)."""
    lines = []
    for c in (corner_left, corner_right):
        f = force_lines_vw(c, travel)
        if f["front_slope_cp"] is None:
            raise KinematicsError("linha de força frontal vertical: RC do eixo indefinido")
        lines.append((f["contact_patch"][1], f["contact_patch"][2], f["front_slope_cp"]))
    (y1, z1, m1), (y2, z2, m2) = lines
    if abs(m1 - m2) < 1e-12:
        raise KinematicsError("linhas de força frontais paralelas: RC do eixo indefinido")
    y = (z2 - z1 + m1 * y1 - m2 * y2) / (m1 - m2)
    return float(y), float(m1 * (y - y1))


def instant_screw_axis(corner: Corner, travel=0.0, steer=0.0, dz=1e-5):
    """Diagnóstico: eixo instantâneo (helicoide) do conjunto não suspenso. Direção ω, ponto mais próximo do centro da roda
    e passo [m/rad]. O passo diferente de zero é o que separa a leitura literal "eixo × plano" da linha de força."""
    s0, w, vel = _twist(corner, travel, steer, dz)
    P, v = corner.pt(s0, "WHEEL_CENTER"), vel("WHEEL_CENTER")
    ww = float(w @ w)
    if ww < 1e-18:
        raise KinematicsError("conjunto não gira com o curso: eixo instantâneo indefinido")
    return {"omega_per_m": w, "point": P + np.cross(w, v) / ww, "pitch_m_per_rad": float((w @ v) / ww), "solution": s0}


def reference_literal_centers(corner: Corner, travel=0.0, steer=0.0, dz=1e-5):
    """Diagnóstico (EDR-053): leitura literal do help do OptimumKinematics (§7.3.3.13, 7.3.3.16, 7.3.3.23): IC = eixo
    instantâneo ∩ plano vertical pelo contact patch; RC do canto = plano (eixo + contact patch) ∩ plano central, na estação
    X do contact patch. NÃO é a REFERENCE: o help não diz o que o programa faz com o passo; serve para identificar a
    definição dele quando houver dados."""
    ax = instant_screw_axis(corner, travel, steer, dz)
    w, a0, s0 = ax["omega_per_m"], ax["point"], ax["solution"]
    cp = corner.pt(s0, "CONTACT_PATCH")
    out = {"pitch_m_per_rad": ax["pitch_m_per_rad"]}
    for nome, i, cols in (("ic_front", 0, [1, 2]), ("ic_side", 1, [0, 2])):
        out[nome] = None if abs(w[i]) < 1e-12 else (a0 + (cp[i] - a0[i]) / w[i] * w)[cols]
    n = np.cross(w, cp - a0)
    out["rc_height_m"] = None if abs(n[2]) < 1e-12 else float(n[1] * cp[1] / n[2])
    return out


# ---------------- direção (cap. 19 da Milliken; Gillespie cap. 6 e 8; Seward 6.3) — EDR-052 ----------------

def ackermann_inner_ideal_deg(delta_outer_deg, wheelbase, track):
    """SUS-414: ângulo da roda interna para Ackermann exato, dado o da externa: cot δo − cot δi = t/L
    (Gillespie eq. 8-1 e 8-2, p. 277-278; confere com a Tab. 6.2 do Seward)."""
    if not 0.0 < abs(delta_outer_deg) < 90.0:
        raise ValueError("δo deve estar entre 0 e 90° em módulo")
    c = 1.0 / math.tan(math.radians(abs(delta_outer_deg))) - track / wheelbase
    if c <= 0:
        raise ValueError("δo grande demais para a geometria (cot δi ≤ 0)")
    return math.copysign(math.degrees(math.atan(1.0 / c)), delta_outer_deg)


def ackermann_percent(delta_inner_deg, delta_outer_deg, wheelbase, track):
    """SUS-414: % Ackermann = (δi − δo)/(δi,Ack − δo)·100 no mesmo δo. 100 % = Ackermann exato (Seward, glossário); 0 % =
    paralelo; < 0 = reverso (Milliken p. 714-716). Forma do projeto (EDR-052): a literatura define os extremos, não a razão."""
    ideal = ackermann_inner_ideal_deg(delta_outer_deg, wheelbase, track)
    return (abs(delta_inner_deg) - abs(delta_outer_deg)) / (abs(ideal) - abs(delta_outer_deg)) * 100.0


def turn_radius_outer_m(delta_outer_deg, wheelbase):
    """SUS-414: raio da trajetória da roda dianteira externa em Ackermann, L/sin δo (Seward, Tab. 6.2)."""
    return wheelbase / math.sin(math.radians(abs(delta_outer_deg)))


def ackermann_from_kinematics(corner_left: Corner, corner_right: Corner, rack, wheelbase, track):
    """SUS-414 (MODEL): ângulos das rodas para um curso de cremalheira e o % Ackermann da geometria (toe estático
    descontado: steer_sweep dá o yaw relativo ao curso zero)."""
    yl = steer_sweep(corner_left, [rack])[0][1]
    yr = steer_sweep(corner_right, [rack])[0][1]
    if abs(yl) < 1e-9 or abs(yr) < 1e-9 or yl * yr <= 0:
        raise KinematicsError("rodas não esterçam no mesmo sentido com esse curso de cremalheira")
    right_turn = (yl + yr) < 0                     # yaw ISO + = esquerda
    inner, outer = (abs(yr), abs(yl)) if right_turn else (abs(yl), abs(yr))
    return {"turn": "direita" if right_turn else "esquerda", "delta_inner_deg": inner, "delta_outer_deg": outer,
            "delta_inner_ackermann_deg": ackermann_inner_ideal_deg(outer, wheelbase, track),
            "ackermann_percent": ackermann_percent(inner, outer, wheelbase, track)}


def steering_ratio_overall(corner_left: Corner, corner_right: Corner, rack_travel_per_rev_m, ds=1e-4):
    """SUS-601 (MODEL): razão total = gradiente do ângulo do volante sobre o ângulo médio das rodas dianteiras
    (SAE J670 9.4.6, Gillespie p. 293 e Apêndice A; Milliken p. 716). (360/c) / |d(yaw médio)/ds|."""
    a = steer_sweep(corner_left, [-ds, ds])
    b = steer_sweep(corner_right, [-ds, ds])
    d = ((a[1][1] - a[0][1]) + (b[1][1] - b[0][1])) / (4 * ds)
    if abs(d) < 1e-9:
        raise KinematicsError("rodas não esterçam com a cremalheira")
    return abs((360.0 / rack_travel_per_rev_m) / d)


def steering_ratio_rack_approx(rack_travel_per_rev_m, steering_arm_m):
    """SUS-601: aproximação do Milliken (p. 718) para cremalheira com barra perpendicular ao braço de direção:
    SR = 360 / asin(c/braço) [graus]. O livro imprime asin(c/braço)/360, que é o inverso da razão que ele mesmo define
    na p. 716 (volante/roda); adotada a forma coerente com a definição (EDR-052)."""
    r = rack_travel_per_rev_m / steering_arm_m
    if not 0.0 < r < 1.0:
        raise ValueError("c/braço deve estar entre 0 e 1")
    return 360.0 / math.degrees(math.asin(r))


def ride_steer(corner: Corner, travels):
    """SUS-408 (Milliken 19.4): toe em função do curso. Devolve a inclinação no curso zero [°/mm, toe-out +] por diferença
    central, o coeficiente quadrático do ajuste [°/mm²] e o maior desvio da reta [°] (curva = 'a evitar', Fig. 19.9)."""
    ts = sorted(set(list(travels) + [0.0]))
    rows = sweep(corner, ts)
    z = np.array([m["travel_m"] for _, m in rows]) * 1e3
    toe = np.array([m["toe_deg"] for _, m in rows])
    h = 1e-2
    a = sweep(corner, [-h * 1e-3, h * 1e-3])
    slope0 = (a[1][1]["toe_deg"] - a[0][1]["toe_deg"]) / (2 * h)
    c2, c1, c0 = np.polyfit(z, toe, 2)
    lin = np.polyfit(z, toe, 1)
    return {"slope_deg_per_mm": float(slope0), "quad_deg_per_mm2": float(c2),
            "max_dev_from_linear_deg": float(np.max(np.abs(toe - np.polyval(lin, z)))), "toe_curve": list(zip(z, toe))}


def roll_steer_coefficient(corner_left: Corner, corner_right: Corner, track, dphi=1e-3):
    """SUS-415 (Gillespie p. 220 e 281-282): ε = graus de esterço por grau de rolagem do eixo; ε > 0 esterça para a
    DIREITA numa rolagem para a direita (lado direito para baixo). Rolagem φ da massa suspensa: curso da roda direita
    = +(t/2)·φ (bump), da esquerda = −(t/2)·φ. Esterço do eixo = média do yaw ISO das duas rodas; ε = −Δyaw/Δφ."""
    def yaw_avg(phi):
        tot = 0.0
        for c, z in ((corner_left, -0.5 * track * phi), (corner_right, 0.5 * track * phi)):
            s = c.solve(z)
            tot += c.side * c.metrics(s)["toe_deg"]
        return tot / 2.0
    d = (yaw_avg(dphi) - yaw_avg(-dphi)) / (2 * dphi)     # deg de yaw por rad de rolagem
    return float(-math.radians(d))                         # rad/rad = °/°


def camber_gradient_from_body(dgamma_body_dz_left, dgamma_body_dz_right, track):
    """V4.0 inc. 2 (Gillespie eq. 6-50, p. 218; eq. 6-51; exemplo resolvido, p. 234): gradiente de camber no solo por
    rolagem, ∂γ/∂φ [rad/rad], a partir de dγ_corpo/dz [rad/m] de cada roda (camber do projeto, topo para fora +).
    Rolagem φ para a direita: curso da roda direita = +(t/2)·φ, da esquerda = −(t/2)·φ (como em
    `roll_steer_coefficient`). A eq. 6-50, γ_solo = γ_corpo + φ, vale com o sinal de cada lado na convenção do projeto:
    γ_R,solo = γ_R,corpo + φ e γ_L,solo = γ_L,corpo − φ. Logo ∂γ_R/∂φ = (t/2)·dγ_R/dz + 1 e
    ∂γ_L/∂φ = −(t/2)·dγ_L/dz − 1. Gradiente do eixo = (R − L)/2; braços paralelos iguais (dγ_corpo/dz = 0) dão 1,0
    (Gillespie p. 234)."""
    half = 0.5 * track
    g_r = half * dgamma_body_dz_right + 1.0
    g_l = -half * dgamma_body_dz_left - 1.0
    return {"L": float(g_l), "R": float(g_r), "eixo": float((g_r - g_l) / 2.0)}


def camber_gradient(corner_left: Corner, corner_right: Corner, track, dphi=1e-3):
    """V4.0 inc. 2: gradiente de camber no solo do eixo (ver `camber_gradient_from_body`), com dγ_corpo/dz de cada canto
    por diferença central na `sweep` (curso ±(t/2)·dphi; `metrics["camber_deg"]` em graus, convertido para rad)."""
    def dg_dz(corner, z):
        a = sweep(corner, [-z, z])
        return math.radians(a[1][1]["camber_deg"] - a[0][1]["camber_deg"]) / (2.0 * z)
    z = 0.5 * track * dphi
    return camber_gradient_from_body(dg_dz(corner_left, z), dg_dz(corner_right, z), track)


def roll_steer_understeer_deg_per_g(eps_front, eps_rear, roll_gradient_deg_per_g):
    """SUS-415: contribuição do roll steer ao gradiente de subesterço, K = (ε_f − ε_r)·∂φ/∂a_y (Gillespie eq. 6-57).
    K > 0 = subesterço."""
    return (eps_front - eps_rear) * roll_gradient_deg_per_g


def steer_effects(corner: Corner, kingpin_rotation_deg, travel=0.0):
    """SUS-416 (Milliken 19.1): efeito geométrico do esterço, com a manga girando em torno do pino mestre (reta
    LCA_OUT -> UCA_OUT) e os ball joints parados, como o livro descreve. Rotação + = em torno do eixo orientado para cima
    (yaw para a esquerda). Devolve yaw da roda [°], variação de camber [°] (topo para fora +) e elevação do carro [m] =
    −ΔZ do contact patch no referencial do chassi (o pneu desce, o carro sobe). KPI com spindle length positivo levanta o
    carro nos dois sentidos; caster levanta de um lado e baixa do outro (peso diagonal)."""
    s0 = corner.solve(travel, 0.0)
    lo, up = corner.pt(s0, "LCA_OUT"), corner.pt(s0, "UCA_OUT")
    k = _unit(up - lo)
    R = _rot_axis(k, math.radians(kingpin_rotation_deg))
    wc, sp, cp = (corner.pt(s0, n) for n in ("WHEEL_CENTER", "SPINDLE_PT", "CONTACT_PATCH"))
    rot = lambda P: lo + R @ (P - lo)

    def ang(w, s):
        a = _unit(s - w)
        return math.degrees(math.asin(-a[2])), math.degrees(math.asin(-a[0] / math.hypot(a[0], a[1])))

    cam0, toe0 = ang(wc, sp)
    cam1, toe1 = ang(rot(wc), rot(sp))
    return {"yaw_deg": corner.side * (toe1 - toe0), "dcamber_deg": cam1 - cam0, "lift_m": float(-(rot(cp)[2] - cp[2]))}


def full_sweep(corner: Corner, travels, steer=0.0, reaction_point="contact_patch"):
    """Varredura completa (uma linha por curso): métricas de pose + MR (se há mola) + IC/RC cinemáticos + inclinação
    da linha de força lateral. reaction_point: 'contact_patch' (freio/tração reagidos pela manga) ou 'wheel_center'
    (reagidos pelo chassi, ex.: freio/motor inboard). Para o carro atual, ver REACTION_POINT (EDR-048)."""
    if reaction_point not in ("contact_patch", "wheel_center"):
        raise ValueError("reaction_point deve ser 'contact_patch' ou 'wheel_center'")
    rows = []
    for (s, m), t in zip(sweep(corner, travels, steer), travels):
        k = kinematic_centers(corner, t, steer)
        cp = k["contact_patch"]
        ref = cp if reaction_point == "contact_patch" else k["wheel_center"]
        row = {kk: v for kk, v in m.items() if not isinstance(v, np.ndarray)}
        d = _line_dir(k["front"], cp[[1, 2]])
        row["rc_height_m"] = float(d[1] / d[0] * (0.0 - cp[1])) if abs(d[0]) > 1e-12 else None   # acima do solo
        row["ic_front_y_m"] = None if k["front"]["point"] is None else float(k["front"]["point"][0])
        row["ic_front_z_m"] = None if k["front"]["point"] is None else float(k["front"]["point"][1])
        row["ic_side_x_m"] = None if k["side"]["point"] is None else float(k["side"]["point"][0])
        row["ic_side_z_m"] = None if k["side"]["point"] is None else float(k["side"]["point"][1])
        row["side_force_line_slope"] = force_line_slope(k["side"], ref[[0, 2]])
        f = force_lines_vw(corner, t, steer)                       # definição primária (EDR-053)
        row["rc_height_vw_m"] = f["rc_height_m"]
        row["side_force_line_slope_vw"] = f["side_slope_cp"] if reaction_point == "contact_patch" else f["side_slope_wc"]
        if corner.has_push:
            row["mr_wheel_per_spring"] = motion_ratio(corner, t)["mr_wheel_per_spring"]
        rows.append(row)
    return rows


def write_sweep_csv(rows, path):
    """Exporta a varredura de full_sweep em CSV com unidade no nome da coluna (arquitetura, seção 10).
    Campos sem valor (IC no infinito) ficam vazios."""
    import csv
    cols = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r[c] is None else f"{r[c]:.9g}" for c in cols])
