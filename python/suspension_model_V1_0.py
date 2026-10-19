"""
Suspension & Vehicle Dynamics Model — FSAE EV
Implementa as fichas do Engineering Standard V1.0 (SUS-000 a SUS-208, SUS-701/702).

Referência: Milliken & Milliken, Race Car Vehicle Dynamics.
Convenção de sinal: ISO 8855 (X-frente, Y-esquerda, Z-cima).
"""

from dataclasses import dataclass
import math

__version__ = "V1.0"

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
        if abs((self.cg_to_front + self.cg_to_rear) - self.wheelbase) > 1e-6:
            raise ValueError(
                f"SUS-006 inconsistente com SUS-003: a+b={self.cg_to_front + self.cg_to_rear} "
                f"!= L={self.wheelbase}"
            )


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
    fz_aero_f = downforce_total * aero_balance_front
    fz_aero_r = downforce_total * (1 - aero_balance_front)
    return {"FL": fz_aero_f / 2, "FR": fz_aero_f / 2,
            "RL": fz_aero_r / 2, "RR": fz_aero_r / 2}


# ---------- SUS-104 : Fz combinado por canto ----------

def combined_fz_corner(cfg: VehicleConfig, ax: float, ay: float,
                        downforce_total: float = 0.0,
                        aero_balance_front: float = 0.5) -> dict:
    fz_static = static_fz_corner(cfg)
    long_ = longitudinal_dfz(cfg, ax)
    lat_ = lateral_dfz(cfg, ay)
    aero = aero_fz_corner(downforce_total, aero_balance_front)

    dFzF, dFzR = lat_["front_axle"], lat_["rear_axle"]

    return {
        "FL": fz_static["FL"] + long_["front_per_corner"] - dFzF + aero["FL"],
        "FR": fz_static["FR"] + long_["front_per_corner"] + dFzF + aero["FR"],
        "RL": fz_static["RL"] + long_["rear_per_corner"] - dFzR + aero["RL"],
        "RR": fz_static["RR"] + long_["rear_per_corner"] + dFzR + aero["RR"],
    }


# ---------- SUS-201 / SUS-202 : motion ratio e wheel rate ----------

def wheel_rate(k_spring: float, mr_wheel_spring: float) -> float:
    """SUS-202, Analysis Mode. MR = wheel/spring."""
    return k_spring / mr_wheel_spring ** 2


def spring_rate_from_wheel_rate(k_wheel: float, mr_wheel_spring: float) -> float:
    """SUS-202, Design Mode (reverso)."""
    return k_wheel * mr_wheel_spring ** 2


# ---------- SUS-205 : frequência natural ----------

def natural_frequency(k_wheel: float, m_sprung_corner: float) -> float:
    return (1 / (2 * math.pi)) * math.sqrt(k_wheel / m_sprung_corner)


def wheel_rate_from_target_frequency(f_target: float, m_sprung_corner: float) -> float:
    """SUS-205, Design Mode (reverso)."""
    return (2 * math.pi * f_target) ** 2 * m_sprung_corner


# ---------- SUS-206 / SUS-207 : rigidez de rolagem por eixo ----------

def roll_stiffness_axle(k_wheel: float, track: float, k_arb: float = 0.0) -> float:
    return (k_wheel * track ** 2) / 2 + k_arb


# ---------- SUS-208 : distribuição de rigidez de rolagem ----------

def roll_stiffness_distribution(k_phi_f: float, k_phi_r: float) -> dict:
    total = k_phi_f + k_phi_r
    return {"lambda_f": k_phi_f / total, "lambda_r": k_phi_r / total}
