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

from suspension_model import G, VehicleConfig, combined_fz_corner, lateral_dfz
from tire_model import AXIS_TRANSFORMS, TireDataset, wheel_forces

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
    # γ que o pneu recebe (ds.axis_system pode inverter o sinal); fora de [CAMMIN, CAMMAX] não se extrapola.
    s_g = AXIS_TRANSFORMS[caso.ds.axis_system][2]
    gam = camber(caso, ay_ms2)
    for c in rodas:
        if not (p["CAMMIN"] <= s_g * gam[c] <= p["CAMMAX"]):
            return Capacidade(None, None,
                              f"camber_{c} = {math.degrees(gam[c]):.2f}° fora da faixa do pneu [CAMMIN, CAMMAX]")
    try:
        alfas = grade_alfa(caso, n_alfa)  # |α_roda| fica dentro de [ALPMIN, ALPMAX] por construção
    except ValueError:
        if n_alfa < 2:
            raise
        return Capacidade(None, None, "toe consome a faixa de α")
    fys = [fy_eixo(caso, eixo, ay_ms2, a) for a in alfas]
    i = max(range(len(fys)), key=fys.__getitem__)
    motivo = "pico na borda da grade de α" if i == len(fys) - 1 else None
    return Capacidade(fys[i], alfas[i], motivo)


# ---------------------------------------------------------------------------
# Análise de par: saturação, veredito e C_N (Milliken §7.1 p. 283-286; §8.4 p. 311-312)
# ---------------------------------------------------------------------------

PUSH = "PUSH"
LOOSE = "LOOSE"
NEUTRO = "NEUTRO"
NA = "N/A"
NAO_CONCLUSIVO = "NÃO CONCLUSIVO"


def forca_exigida(caso: CasoEquilibrio, ay_ms2: float) -> tuple[float, float]:
    """(F_yf, F_yr) [N] que os eixos precisam dar em a_y: (m·a_y·b/L, m·a_y·a/L).

    Equilíbrio de forças e de momento de guinada em regime (r = 0), Milliken §7.1. A downforce
    muda a capacidade (via Fz), não a força exigida.
    """
    cfg = caso.cfg
    m_ay = cfg.mass_total * ay_ms2
    return (m_ay * cfg.cg_to_rear / cfg.wheelbase, m_ay * cfg.cg_to_front / cfg.wheelbase)


@dataclass(frozen=True)
class LinhaPar:
    """Uma linha da grade de a_y: cargas, capacidade e força exigida de cada eixo."""
    ay_ms2: float
    fz: dict
    cap_f: Capacidade
    cap_r: Capacidade
    req_f: float
    req_r: float


@dataclass(frozen=True)
class ResultadoPar:
    """Resultado da análise de par. veredito ∈ {PUSH, LOOSE, NEUTRO, N/A}; c_n só em PUSH/LOOSE."""
    linhas: tuple
    passo_ms2: float
    ay_sat_f: float | None
    ay_sat_r: float | None
    ay_lim: float | None
    veredito: str
    motivo: str | None
    c_n: float | None


@dataclass(frozen=True)
class _Saturacao:
    ay_sat: float | None      # a_y de saturação [m/s²], ou None
    k: int | None             # índice k do intervalo (k, k+1) em que a folga troca de sinal
    ay_valido: float | None   # último a_y da parte válida contínua (desde k = 0), ou None
    motivo: str | None        # por que não saturou (None quando saturou)


def _folga(linha: LinhaPar, eixo: str) -> float:
    cap, req = (linha.cap_f, linha.req_f) if eixo == "F" else (linha.cap_r, linha.req_r)
    return cap.fy_max_N - req


def _saturacao(linhas: tuple, eixo: str, ay_max_g: float) -> _Saturacao:
    """Primeira troca de sinal da folga entre linhas consecutivas válidas, interpolada linearmente.

    A busca para na primeira linha inválida (capacidade com motivo): nada além dela é usado.
    """
    ay_valido = None
    m_ant = None
    for k, ln in enumerate(linhas):
        cap = ln.cap_f if eixo == "F" else ln.cap_r
        if cap.motivo is not None:
            return _Saturacao(None, None, ay_valido, f"{cap.motivo} em a_y = {ln.ay_ms2 / G:g} g")
        m = _folga(ln, eixo)
        if m_ant is not None and m_ant > 0.0 >= m:
            a0 = linhas[k - 1].ay_ms2
            ay_sat = a0 + (ln.ay_ms2 - a0) * m_ant / (m_ant - m)
            # ay_valido segue até a última linha válida conhecida (a busca para aqui, mas a
            # linha k é válida)
            return _Saturacao(ay_sat, k - 1, ln.ay_ms2, None)
        ay_valido = ln.ay_ms2
        m_ant = m
    return _Saturacao(None, None, ay_valido, f"não satura até {ay_max_g:g} g")


def analise_par(caso: CasoEquilibrio, ay_max_g: float = 2.0, passo_g: float = 0.05,
                n_alfa: int = 25) -> ResultadoPar:
    """Varre a_y_k = k·passo (k = 0…⌊ay_max/passo⌋) e decide PUSH/LOOSE/NEUTRO pelo eixo que satura antes.

    Milliken §7.1 (p. 283-286): no limite, o eixo que satura primeiro define o comportamento final
    (dianteiro = push, final understeer; traseiro = loose, final oversteer). C_N (spec 7.2;
    Milliken §8.4, p. 311-312) é o momento de guinada adimensional que sobra no limite: a folga do
    eixo não saturado em a_y_lim vezes o braço até o CG, sobre W·L, com W = m·G.

    Capacidade com motivo (fora da faixa do pneu, pico na borda da grade de α, toe) nunca entra
    no cálculo: a busca do eixo para nela e o veredito sai N/A se ela impedir a decisão.
    """
    if not (isinstance(ay_max_g, (int, float)) and ay_max_g > 0 and math.isfinite(ay_max_g)):
        raise ValueError(f"ay_max_g deve ser > 0 e finito; recebido {ay_max_g!r}.")
    if not (isinstance(passo_g, (int, float)) and passo_g > 0 and math.isfinite(passo_g)):
        raise ValueError(f"passo_g deve ser > 0 e finito; recebido {passo_g!r}.")
    if not (isinstance(n_alfa, int) and n_alfa >= 3):
        raise ValueError(f"n_alfa deve ser um inteiro >= 3; recebido {n_alfa!r}.")

    # ⌊ay_max/passo⌋ com folga de arredondamento: 0.3/0.05 = 5.999…, que deve dar 6.
    n = math.floor(ay_max_g / passo_g + 1e-9)
    linhas = []
    for k in range(n + 1):
        ay = k * passo_g * G
        req_f, req_r = forca_exigida(caso, ay)
        linhas.append(LinhaPar(ay_ms2=ay, fz=cargas(caso, ay),
                               cap_f=capacidade_eixo(caso, "F", ay, n_alfa),
                               cap_r=capacidade_eixo(caso, "R", ay, n_alfa),
                               req_f=req_f, req_r=req_r))
    linhas = tuple(linhas)
    passo_ms2 = passo_g * G

    sf = _saturacao(linhas, "F", ay_max_g)
    sr = _saturacao(linhas, "R", ay_max_g)
    S_f, S_r = sf.ay_sat, sr.ay_sat
    V_f = sf.ay_valido if sf.ay_valido is not None else -math.inf
    V_r = sr.ay_valido if sr.ay_valido is not None else -math.inf

    motivo = None
    if S_f is not None and S_r is not None and abs(S_f - S_r) < passo_ms2:
        veredito = NEUTRO
    elif (S_f is not None and S_r is not None and S_f < S_r) or (S_f is not None and S_r is None and V_r > S_f):
        veredito = PUSH
    elif (S_f is not None and S_r is not None and S_r < S_f) or (S_r is not None and S_f is None and V_f > S_r):
        veredito = LOOSE
    else:
        veredito = NA
        if S_f is not None:        # o traseiro não chegou válido até S_f
            motivo = sr.motivo
        elif S_r is not None:      # o dianteiro não chegou válido até S_r
            motivo = sf.motivo
        else:                      # nenhum saturou: vale o eixo cuja parte válida acaba antes
            motivo = sf.motivo if V_f <= V_r else sr.motivo

    conhecidas = [s for s in (S_f, S_r) if s is not None]
    ay_lim = min(conhecidas) if conhecidas else None

    c_n = None
    if veredito in (PUSH, LOOSE):
        cfg = caso.cfg
        W = cfg.mass_total * G
        # A folga do eixo não saturado é interpolada no mesmo intervalo (k, k+1) em que o eixo
        # saturado trocou de sinal; as duas linhas são válidas para ele (V > a_y_lim).
        sat, outro = (sf, "R") if veredito == PUSH else (sr, "F")
        la, lb = linhas[sat.k], linhas[sat.k + 1]
        ma, mb = _folga(la, outro), _folga(lb, outro)
        folga = ma + (mb - ma) * (ay_lim - la.ay_ms2) / (lb.ay_ms2 - la.ay_ms2)
        if veredito == PUSH:
            c_n = folga * cfg.cg_to_rear / (W * cfg.wheelbase)
        else:
            c_n = -folga * cfg.cg_to_front / (W * cfg.wheelbase)

    return ResultadoPar(linhas=linhas, passo_ms2=passo_ms2, ay_sat_f=S_f, ay_sat_r=S_r, ay_lim=ay_lim,
                        veredito=veredito, motivo=motivo, c_n=c_n)
