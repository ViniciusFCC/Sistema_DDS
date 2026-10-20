"""
Análise de par (equilíbrio de um eixo ou do carro em curva) — núcleo do V4.0, incremento 1.

Referência: Milliken, Race Car Vehicle Dynamics, §7.1 (p. 283-286), e a especificação da
V4.0 (docs/). Este módulo reúne o caso (veículo, pneu, aero, toe e camber por roda) e calcula
as cargas verticais e o camber de cada roda para uma aceleração lateral dada.

Convenções (CLAUDE.md): SI, eixos ISO 8855 (a_y > 0 = curva à esquerda, rodas FR/RR externas),
camber + = topo da roda para fora, toe + = toe-out (EDR-002). Toe, camber estático e ganho de
camber têm padrão 0: "sem dado" (EDR-036), nunca valor inventado.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from suspension_model import VehicleConfig, combined_fz_corner, lateral_dfz
from tire_model import TireDataset

CANTOS = ("FL", "FR", "RL", "RR")


def _zeros() -> dict:
    return {c: 0.0 for c in CANTOS}


@dataclass(frozen=True)
class CasoEquilibrio:
    """Entradas da análise de par. Os dicionários por roda levam as quatro chaves de CANTOS.

    ganho_camber é dγ/dφ em rad/rad (γ por rad de rolagem), na convenção do projeto.
    """
    cfg: VehicleConfig
    ds: TireDataset
    downforce_N: float = 0.0
    aero_balance_front: float = 0.5
    toe_rad: dict = field(default_factory=_zeros)
    camber_estatico_rad: dict = field(default_factory=_zeros)
    ganho_camber: dict = field(default_factory=_zeros)

    def __post_init__(self):
        for nome in ("toe_rad", "camber_estatico_rad", "ganho_camber"):
            d = getattr(self, nome)
            if set(d) != set(CANTOS):
                raise ValueError(f"{nome} exige exatamente as chaves {CANTOS}; recebido {sorted(d)}.")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in d.values()):
                raise ValueError(f"{nome} exige valores numéricos finitos; recebido {d}.")


def cargas(caso: CasoEquilibrio, ay_ms2: float) -> dict:
    """Fz [N] por roda em a_y [m/s²] (a_x = 0), com a aerodinâmica do caso."""
    return combined_fz_corner(caso.cfg, 0.0, ay_ms2, caso.downforce_N,
                              caso.aero_balance_front, warn=False)


def camber(caso: CasoEquilibrio, ay_ms2: float) -> dict:
    """γ [rad] por roda: γ = camber_estático + ganho_camber·φ, com φ a rolagem de lateral_dfz."""
    phi = lateral_dfz(caso.cfg, ay_ms2)["roll_angle_rad"]
    return {c: caso.camber_estatico_rad[c] + caso.ganho_camber[c] * phi for c in CANTOS}
