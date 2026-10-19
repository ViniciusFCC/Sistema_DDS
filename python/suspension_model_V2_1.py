"""
Suspension & Vehicle Dynamics Model — FSAE EV
Implementa as fichas do Engineering Standard V2.0 (SUS-000 a SUS-208, SUS-701/702).

V2.1: cross-check de MR [wheel/spring] contra MR geométrico/de referência (mr_crosscheck). O comportamento do limiar
absoluto MR_WARN_THRESHOLD NÃO foi alterado (decisão pendente, EDR-027).
V2.0: validação de entradas (bloqueios do Guide, Apêndice D.2) e aviso de plausibilidade para Fz<0 (SUS-104; Guide D.4).
Os valores de retorno das funções para entradas válidas são idênticos aos da V1.0 (verificado em test_suspension_model_V2_0.py).

Referência: Milliken & Milliken, Race Car Vehicle Dynamics.
Convenção de sinal: ISO 8855 (X-frente, Y-esquerda, Z-cima).
"""

from dataclasses import dataclass, fields
import math
import warnings

__version__ = "V2.1"

# HIPÓTESE (sem fonte no projeto): abaixo deste MR emite aviso. O Guide (D.2) pede o teste de fronteira "MR muito pequeno"
# mas não define o limite. Revisar com dado real da equipe.
MR_WARN_THRESHOLD = 0.2


class FzLiftoffWarning(UserWarning):
    """Fz negativo em algum canto: perda de contato; o modelo linear (SUS-104) não deve ser extrapolado."""


class SmallMotionRatioWarning(UserWarning):
    """MR abaixo de MR_WARN_THRESHOLD: wheel rate muito sensível ao MR (K_w = K_s/MR^2)."""


def _req(cond, msg):
    if not cond:
        raise ValueError(msg)

G = 9.81  # m/s^2


@dataclass
class VehicleConfig:
    """Inputs de veículo (Bloco A do Engineering Standard)."""
    mass_total: float                  # SUS-001 [kg], inclui piloto
    cg_height: float                   # SUS-002 [m], acima do solo (SUS-000 já aplicado)
    wheelbase: float                   # SUS-003 [m]
    track_front: float                 # SUS-004 [m]
    track_rear: float                  # SUS-005 [m]
    cg_to_front: float                 # SUS-006 "a" [m]
    cg_to_rear: float                  # SUS-006 "b" [m]
    unsprung_mass_front: float         # SUS-007 [kg], ambas as rodas
    unsprung_mass_rear: float          # SUS-008 [kg], ambas as rodas
    unsprung_cg_height_front: float    # SUS-010 [m]
    unsprung_cg_height_rear: float     # SUS-011 [m]
    roll_center_front: float           # SUS-401-F [m], REFERENCE (OptimumKinematics)
    roll_center_rear: float            # SUS-401-R [m], REFERENCE (OptimumKinematics)
    roll_stiffness_front: float        # SUS-206 [N*m/rad]
    roll_stiffness_rear: float         # SUS-207 [N*m/rad]

    def __post_init__(self):
        for f in fields(self):
            v = getattr(self, f.name)
            _req(isinstance(v, (int, float)) and math.isfinite(v), f"{f.name}: valor deve ser número finito (recebido {v!r}).")
        _req(self.mass_total > 0, "SUS-001 mass_total deve ser > 0 (massa zero é bloqueada). Corrija a entrada de massa.")
        _req(self.cg_height > 0, "SUS-002 cg_height deve ser > 0 (altura acima do solo, SUS-000).")
        _req(self.wheelbase > 0, "SUS-003 wheelbase deve ser > 0 (L zero é bloqueado).")
        _req(self.track_front > 0, "SUS-004 track_front deve ser > 0.")
        _req(self.track_rear > 0, "SUS-005 track_rear deve ser > 0.")
        _req(self.cg_to_front > 0 and self.cg_to_rear > 0, "SUS-006 cg_to_front (a) e cg_to_rear (b) devem ser > 0.")
        _req(self.unsprung_mass_front >= 0 and self.unsprung_mass_rear >= 0, "SUS-007/008 massas não-suspensas devem ser >= 0.")
        _req(self.mass_total - self.unsprung_mass_front - self.unsprung_mass_rear > 0,
             "SUS-009 massa suspensa total <= 0: massas não-suspensas (SUS-007/008) maiores ou iguais à massa total (SUS-001).")
        _req(self.unsprung_cg_height_front >= 0 and self.unsprung_cg_height_rear >= 0, "SUS-010/011 alturas não-suspensas devem ser >= 0.")
        _req(self.roll_stiffness_front >= 0 and self.roll_stiffness_rear >= 0
             and (self.roll_stiffness_front + self.roll_stiffness_rear) > 0,
             "SUS-206/207 rigidezes de rolagem devem ser >= 0 com soma > 0.")
        if abs((self.cg_to_front + self.cg_to_rear) - self.wheelbase) > 1e-6:
            raise ValueError(
                f"SUS-006 inconsistente com SUS-003: a+b={self.cg_to_front + self.cg_to_rear} "
                f"!= L={self.wheelbase}"
            )
        ms = self.mass_total - self.unsprung_mass_front - self.unsprung_mass_rear
        hs = (self.mass_total * self.cg_height - self.unsprung_mass_front * self.unsprung_cg_height_front
              - self.unsprung_mass_rear * self.unsprung_cg_height_rear) / ms
        _req(hs > 0, f"SUS-012 h_s={hs:.4f} m <= 0: inconsistência entre SUS-002, 007, 008, 010 e 011 (CG suspenso abaixo do solo).")


# ---------- SUS-009 / SUS-012 : massa suspensa e altura do CG suspenso ----------

def sprung_mass_total(cfg: VehicleConfig) -> float:
    """SUS-009, primeira etapa: massa suspensa total."""
    return cfg.mass_total - cfg.unsprung_mass_front - cfg.unsprung_mass_rear


def sprung_mass_per_corner(cfg: VehicleConfig) -> dict:
    """SUS-009: distribuição por canto (aproxima a posição longitudinal do CG
    suspenso pela do CG total — hipótese documentada em SUS-006)."""
    ms = sprung_mass_total(cfg)
    L = cfg.wheelbase
    ms_front = ms * (cfg.cg_to_rear / L)   # b/L
    ms_rear = ms * (cfg.cg_to_front / L)   # a/L
    return {"FL": ms_front / 2, "FR": ms_front / 2,
            "RL": ms_rear / 2, "RR": ms_rear / 2}


def sprung_cg_height(cfg: VehicleConfig) -> float:
    """SUS-012: h_s a partir da identidade de CG composto
    (m_s*h_s + m_uF*h_uF + m_uR*h_uR = m*h_CG)."""
    ms = sprung_mass_total(cfg)
    return (cfg.mass_total * cfg.cg_height
            - cfg.unsprung_mass_front * cfg.unsprung_cg_height_front
            - cfg.unsprung_mass_rear * cfg.unsprung_cg_height_rear) / ms


# ---------- SUS-101 : carga estática ----------

def static_fz_corner(cfg: VehicleConfig) -> dict:
    L = cfg.wheelbase
    Wf = cfg.mass_total * G * (cfg.cg_to_rear / L)   # b/L
    Wr = cfg.mass_total * G * (cfg.cg_to_front / L)  # a/L
    return {"FL": Wf / 2, "FR": Wf / 2, "RL": Wr / 2, "RR": Wr / 2}


# ---------- SUS-102 : transferência longitudinal ----------

def longitudinal_dfz(cfg: VehicleConfig, ax: float) -> dict:
    """ax > 0 = aceleração para frente (ISO 8855) -> transfere para o eixo traseiro."""
    L = cfg.wheelbase
    dfz_front_axle = -cfg.mass_total * ax * cfg.cg_height / L
    dfz_rear_axle = +cfg.mass_total * ax * cfg.cg_height / L
    return {"front_per_corner": dfz_front_axle / 2,
            "rear_per_corner": dfz_rear_axle / 2}


# ---------- SUS-103 : modelo de duas molas de Milliken ----------

def lateral_dfz(cfg: VehicleConfig, ay: float) -> dict:
    """ay > 0 = aceleração para a esquerda (ISO 8855) -> lado direito ganha carga."""
    a, b, L = cfg.cg_to_front, cfg.cg_to_rear, cfg.wheelbase
    tF, tR = cfg.track_front, cfg.track_rear
    zF, zR = cfg.roll_center_front, cfg.roll_center_rear
    ms = sprung_mass_total(cfg)
    hs = sprung_cg_height(cfg)

    KphiF, KphiR = cfg.roll_stiffness_front, cfg.roll_stiffness_rear
    lambda_f = KphiF / (KphiF + KphiR)
    lambda_r = KphiR / (KphiF + KphiR)

    zs = (b / L) * zF + (a / L) * zR

    dFzF = (ay / tF) * (lambda_f * ms * (hs - zs) + (b / L) * ms * zF
                        + cfg.unsprung_mass_front * cfg.unsprung_cg_height_front)
    dFzR = (ay / tR) * (lambda_r * ms * (hs - zs) + (a / L) * ms * zR
                        + cfg.unsprung_mass_rear * cfg.unsprung_cg_height_rear)

    return {"front_axle": dFzF, "rear_axle": dFzR,
            "lambda_f": lambda_f, "lambda_r": lambda_r, "z_s": zs}


# ---------- SUS-701 / SUS-702 : aero ----------

def aero_fz_corner(downforce_total: float, aero_balance_front: float) -> dict:
    _req(isinstance(aero_balance_front, (int, float)) and 0.0 <= aero_balance_front <= 1.0,
         f"SUS-702 aero_balance_front={aero_balance_front!r} fora de [0,1] (fração dianteira da downforce).")
    _req(math.isfinite(downforce_total), "SUS-701 downforce_total deve ser finito.")
    fz_aero_f = downforce_total * aero_balance_front
    fz_aero_r = downforce_total * (1 - aero_balance_front)
    return {"FL": fz_aero_f / 2, "FR": fz_aero_f / 2,
            "RL": fz_aero_r / 2, "RR": fz_aero_r / 2}


# ---------- SUS-104 : Fz combinado por canto ----------

def fz_plausibility(fz: dict) -> list:
    """Lista de avisos acionáveis para Fz<0 (SUS-104; Guide D.4). Fz == 0 é a fronteira do domínio e não gera aviso."""
    out = []
    for corner, v in fz.items():
        if v < 0:
            out.append({"corner": corner, "fz_N": v,
                        "action": "Perda de contato (liftoff): o modelo linear de SUS-104 não deve ser extrapolado. "
                                  "Reduza a/aceleração, revise rigidez de rolagem/altura do CG, ou trate este ponto como fora do domínio."})
    return out


def combined_fz_corner(cfg: VehicleConfig, ax: float, ay: float,
                        downforce_total: float = 0.0,
                        aero_balance_front: float = 0.5,
                        warn: bool = True) -> dict:
    fz_static = static_fz_corner(cfg)
    long_ = longitudinal_dfz(cfg, ax)
    lat_ = lateral_dfz(cfg, ay)
    aero = aero_fz_corner(downforce_total, aero_balance_front)

    dFzF, dFzR = lat_["front_axle"], lat_["rear_axle"]

    fz = {
        "FL": fz_static["FL"] + long_["front_per_corner"] - dFzF + aero["FL"],
        "FR": fz_static["FR"] + long_["front_per_corner"] + dFzF + aero["FR"],
        "RL": fz_static["RL"] + long_["rear_per_corner"] - dFzR + aero["RL"],
        "RR": fz_static["RR"] + long_["rear_per_corner"] + dFzR + aero["RR"],
    }
    if warn:
        for w in fz_plausibility(fz):
            warnings.warn(FzLiftoffWarning(f"Fz_{w['corner']} = {w['fz_N']:.1f} N < 0. {w['action']}"), stacklevel=2)
    return fz


# ---------- SUS-201 / SUS-202 : motion ratio e wheel rate ----------

def wheel_rate(k_spring: float, mr_wheel_spring: float) -> float:
    """SUS-202, Analysis Mode. MR = wheel/spring."""
    _req(k_spring > 0, "SUS-203/202 k_spring deve ser > 0 (rigidez de mola não positiva é bloqueada).")
    _req(mr_wheel_spring > 0, "SUS-201 MR [wheel/spring] deve ser > 0.")
    if mr_wheel_spring < MR_WARN_THRESHOLD:
        warnings.warn(SmallMotionRatioWarning(
            f"MR={mr_wheel_spring} < {MR_WARN_THRESHOLD} (limite hipotético): K_w = K_s/MR^2 fica muito sensível. "
            "Confirme o MR (convenção wheel/spring, não a inversa)."), stacklevel=2)
    return k_spring / mr_wheel_spring ** 2


def spring_rate_from_wheel_rate(k_wheel: float, mr_wheel_spring: float) -> float:
    """SUS-202, Design Mode (reverso)."""
    _req(k_wheel > 0, "SUS-202 k_wheel deve ser > 0.")
    _req(mr_wheel_spring > 0, "SUS-201 MR [wheel/spring] deve ser > 0.")
    return k_wheel * mr_wheel_spring ** 2


# ---------- SUS-205 : frequência natural ----------

def natural_frequency(k_wheel: float, m_sprung_corner: float) -> float:
    _req(k_wheel > 0 and m_sprung_corner > 0, "SUS-205 k_wheel e m_sprung_corner devem ser > 0.")
    return (1 / (2 * math.pi)) * math.sqrt(k_wheel / m_sprung_corner)


def wheel_rate_from_target_frequency(f_target: float, m_sprung_corner: float) -> float:
    """SUS-205, Design Mode (reverso)."""
    _req(f_target > 0 and m_sprung_corner > 0, "SUS-205 f_target e m_sprung_corner devem ser > 0.")
    return (2 * math.pi * f_target) ** 2 * m_sprung_corner


# ---------- SUS-206 / SUS-207 : rigidez de rolagem por eixo ----------

def roll_stiffness_axle(k_wheel: float, track: float, k_arb: float = 0.0) -> float:
    _req(k_wheel > 0 and track > 0 and k_arb >= 0, "SUS-206/207 k_wheel e track devem ser > 0 e k_arb >= 0.")
    return (k_wheel * track ** 2) / 2 + k_arb


# ---------- SUS-208 : distribuição de rigidez de rolagem ----------

def roll_stiffness_distribution(k_phi_f: float, k_phi_r: float) -> dict:
    _req(k_phi_f >= 0 and k_phi_r >= 0 and (k_phi_f + k_phi_r) > 0, "SUS-208 rigidezes de rolagem devem ser >= 0 com soma > 0.")
    total = k_phi_f + k_phi_r
    return {"lambda_f": k_phi_f / total, "lambda_r": k_phi_r / total}


# ---------- V2.1 : cross-check de Motion Ratio (SUS-201 x SUS-409) ----------

def mr_crosscheck(mr_input: float, mr_geometric=None, rel_tol=None) -> dict:
    """Compara o MR [wheel/spring] de entrada com o MR geométrico (SUS-409) ou de uma referência.

    NÃO há tolerância padrão: ela deve ser definida a partir de incerteza geométrica, sensibilidade numérica e
    diferenças de definição (ex.: ponto de operação, definição de curso), que dependem de dados reais ainda
    indisponíveis. Sem tolerância, o resultado traz as diferenças relativas mas status 'TOLERANCE_NOT_SET'.

    Status: NOT_EXECUTED (sem referência) | TOLERANCE_NOT_SET | MATCH | INVERSION_SUSPECTED | MISMATCH |
            MATCH_INVERSION_NOT_DISTINGUISHABLE (MR próximo de 1: direto e inverso coincidem na tolerância).
    'INVERSION_SUSPECTED' é só uma suspeita: investigar unidades, sinais, configuração, ponto de operação e
    método do solver antes de concluir. Toda outra discrepância é 'MISMATCH' (não é classificada como inversão).
    """
    _req(isinstance(mr_input, (int, float)) and math.isfinite(mr_input) and mr_input > 0, "SUS-201 mr_input deve ser finito e > 0.")
    if mr_geometric is None:
        return {"status": "NOT_EXECUTED", "reason": "MR geométrico/de referência não fornecido: cross-check NÃO executado.",
                "rel_diff_direct": None, "rel_diff_if_inverted": None}
    _req(isinstance(mr_geometric, (int, float)) and math.isfinite(mr_geometric) and mr_geometric > 0, "SUS-409 mr_geometric deve ser finito e > 0.")
    direct = abs(mr_input - mr_geometric) / mr_geometric
    inverted = abs(1.0 / mr_input - mr_geometric) / mr_geometric
    out = {"rel_diff_direct": direct, "rel_diff_if_inverted": inverted}
    if rel_tol is None:
        return {**out, "status": "TOLERANCE_NOT_SET", "reason": "Tolerância não definida (sem valor padrão por falta de dados reais)."}
    _req(isinstance(rel_tol, (int, float)) and math.isfinite(rel_tol) and rel_tol >= 0, "rel_tol deve ser finito e >= 0.")
    if direct <= rel_tol and inverted <= rel_tol:
        return {**out, "status": "MATCH_INVERSION_NOT_DISTINGUISHABLE", "reason": "MR ≈ 1 dentro da tolerância: o cross-check não distingue inversão."}
    if direct <= rel_tol:
        return {**out, "status": "MATCH", "reason": "MR de entrada coincide com o MR geométrico dentro da tolerância."}
    if inverted <= rel_tol:
        return {**out, "status": "INVERSION_SUSPECTED",
                "reason": "O inverso do MR de entrada coincide com o MR geométrico: investigar convenção wheel/spring, unidades, configuração e ponto de operação."}
    return {**out, "status": "MISMATCH", "reason": "Discrepância não explicada por inversão: investigar unidades, sinais, configuração, ponto de operação e solver."}
