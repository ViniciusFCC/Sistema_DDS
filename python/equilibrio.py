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
from tire_model import TireDataset, wheel_forces

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


# ---------------------------------------------------------------------------
# Curva de Fy do eixo e capacidade lateral (Milliken §7.1)
# ---------------------------------------------------------------------------

_RODAS_DO_EIXO = {"F": ("FL", "FR"), "R": ("RL", "RR")}


def _rodas(eixo: str) -> tuple:
    if eixo not in _RODAS_DO_EIXO:
        raise ValueError(f"eixo deve ser 'F' ou 'R'; recebido {eixo!r}.")
    return _RODAS_DO_EIXO[eixo]


def deriva_toe(caso: CasoEquilibrio) -> dict:
    """Δα [rad] por roda vindo do toe estático (toe + = toe-out, EDR-002).

    Toe-out aponta a roda esquerda para a esquerda: o carro em linha reta fica com α < 0 e
    Fy > 0 nela. Por isso Δα_FL = −toe_FL e Δα_FR = +toe_FR (idem atrás).
    """
    sinal = {"FL": -1.0, "FR": 1.0, "RL": -1.0, "RR": 1.0}
    return {c: sinal[c] * caso.toe_rad[c] for c in CANTOS}


def grade_alfa(caso: CasoEquilibrio, n_alfa: int) -> list:
    """n_alfa valores de α_ref [rad], igualmente espaçados de 0 a −A (curva à esquerda: α ≤ 0).

    A = min(|ALPMIN|, ALPMAX) − max|Δα|, para que nenhuma roda saia da faixa de α do pneu.
    """
    if n_alfa < 2:
        raise ValueError(f"n_alfa deve ser >= 2; recebido {n_alfa}.")
    p = caso.ds.p
    amplitude = min(abs(p["ALPMIN"]), p["ALPMAX"]) - max(abs(v) for v in deriva_toe(caso).values())
    if amplitude <= 0.0:
        raise ValueError("toe consome toda a faixa de α do pneu; a grade de α ficaria vazia.")
    return [-amplitude * i / (n_alfa - 1) for i in range(n_alfa)]


def fy_eixo(caso: CasoEquilibrio, eixo: str, ay_ms2: float, alfa_ref: float) -> float:
    """Σ Fy [N, ISO] das duas rodas do eixo ('F' ou 'R'), com α_roda = α_ref + Δα_toe (κ = 0).

    Lança TireRangeError se alguma roda sair da faixa do pneu; quem quer um resultado sem
    exceção usa capacidade_eixo.
    """
    rodas = _rodas(eixo)
    fz = cargas(caso, ay_ms2)
    gam = camber(caso, ay_ms2)
    dal = deriva_toe(caso)
    return sum(wheel_forces(caso.ds, c, fz[c], alfa_ref + dal[c], gam[c], 0.0)[1] for c in rodas)


@dataclass(frozen=True)
class Capacidade:
    """Capacidade lateral de um eixo. fy_max_N e alfa_pico_rad são None quando o pneu não cobre o caso.

    Com motivo = "pico na borda da grade de α" o valor fica registrado, mas não serve para saturação.
    """
    fy_max_N: float | None
    alfa_pico_rad: float | None
    motivo: str | None


def capacidade_eixo(caso: CasoEquilibrio, eixo: str, ay_ms2: float, n_alfa: int) -> Capacidade:
    """Máximo de fy_eixo sobre grade_alfa. Nunca extrapola o pneu e nunca lança por faixa de Fz."""
    rodas = _rodas(eixo)
    p = caso.ds.p
    fz = cargas(caso, ay_ms2)
    for c in rodas:
        if not (p["FZMIN"] <= fz[c] <= p["FZMAX"]):
            return Capacidade(None, None,
                              f"Fz_{c} = {fz[c]:.1f} N fora da faixa do pneu [FZMIN, FZMAX]")
    alfas = grade_alfa(caso, n_alfa)  # |α_roda| fica dentro de [ALPMIN, ALPMAX] por construção
    fys = [fy_eixo(caso, eixo, ay_ms2, a) for a in alfas]
    i = max(range(len(fys)), key=fys.__getitem__)
    motivo = "pico na borda da grade de α" if i == len(fys) - 1 else None
    return Capacidade(fys[i], alfas[i], motivo)
