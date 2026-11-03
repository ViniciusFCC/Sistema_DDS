"""
Análise de par (equilíbrio de um eixo ou do carro em curva) — núcleo do V4.0, incremento 1.

Referência: Milliken, Race Car Vehicle Dynamics, §7.1 (p. 283-286), e a especificação da
V4.0 (docs/). Este módulo reúne o caso (veículo, pneu, aero, toe e camber por roda) e calcula
as cargas verticais e o camber de cada roda para uma aceleração lateral dada.

Convenções (CLAUDE.md): SI, eixos ISO 8855 (a_y > 0 = curva à esquerda, rodas FR/RR externas),
camber + = topo da roda para fora, toe + = toe-out (EDR-002). Toe, camber estático e ganho de
camber têm padrão 0: "sem dado" (EDR-036), nunca valor inventado.

Regras do veredito no limite (EDR-056): entrada do pneu fora da faixa do .tir limitada ao valor da faixa,
com aviso (convenção do PAC2002, help do Adams 2024.1, p. 83); Fz <= 0 é descolamento e invalida a linha;
NEUTRO só dentro da resolução numérica medida por refinamento de grade, e PUSH/LOOSE pelo eixo que
satura primeiro (Milliken, §8.6, p. 320).
"""

from __future__ import annotations

import copy
import functools
import itertools
import math
import dataclasses
from dataclasses import dataclass, field
from typing import Literal

import origens
from kinematics_model import ackermann_inner_ideal_deg
from suspension_model import (G, VehicleConfig, combined_fz_corner, downforce_por_velocidade, lateral_dfz,
                              static_fz_corner, static_fz_corner_cg_lateral)
from tire_model import AXIS_TRANSFORMS, TireDataset, pure_fx0, wheel_forces

CANTOS = ("FL", "FR", "RL", "RR")


@dataclass(frozen=True)
class Formas:
    """Forma das fórmulas novas do incremento 7 (EDR-066; decisão D1 do plano): "v42" é a de hoje, "v43" a nova.

    ackermann: Δα do Ackermann (hipótese 2, SUS-414; ver deriva_ackermann). fx: Fx exigido na traseira (hipótese 9,
    EDR-057; ver fx_exigido_traseira). Não é campo do CasoEquilibrio: entra como argumento só de palavra-chave
    (formas=FORMAS_V42) nas funções que usam a fórmula, e o padrão FORMAS_V42 mantém todas as chamadas de hoje.
    """
    ackermann: Literal["v42", "v43"] = "v42"
    fx: Literal["v42", "v43"] = "v42"

    def __post_init__(self):
        for nome in ("ackermann", "fx"):
            v = getattr(self, nome)
            if v not in ("v42", "v43"):
                raise ValueError(f"Formas.{nome} deve ser 'v42' ou 'v43'; recebido {v!r}.")


FORMAS_V42 = Formas()
FORMAS_V43 = Formas("v43", "v43")


def _zeros() -> dict:
    return {c: 0.0 for c in CANTOS}


def _num(x: float, fmt: str) -> str:
    """Número formatado com vírgula decimal, para os textos de motivo e de aviso (exibição em português)."""
    return format(x, fmt).replace(".", ",")


@dataclass(frozen=True)
class CasoEquilibrio:
    """Entradas da análise de par. Os dicionários por roda levam as quatro chaves de CANTOS.

    ganho_camber é dγ/dφ em rad/rad (γ por rad de rolagem), na convenção do projeto.
    roll_steer é o coeficiente de roll steer de cada eixo, ε [rad/rad], chaves "F" e "R", na convenção do
    SUS-415 (kinematics_model.roll_steer_coefficient: ε > 0 esterça para a direita numa rolagem para a
    direita). Padrão 0 = "sem dado"; só entra na parcela de roll steer do gradiente K (V4.0, inc. 2).
    raio_m é o raio R do skidpad [m] ("a confirmar"; None = sem dado). Com ele, a dianteira esterça
    δ_ref = L/R e a força do eixo dianteiro na direção do carro leva cos δ_ref (spec 7.1, item 3).
    ackermann_pct é o % Ackermann da geometria (SUS-414; 100 = Ackermann exato, 0 = paralelo, < 0 =
    reverso); None desliga a hipótese 2 (spec 7.4). Exige raio_m.
    cg_lateral_m é o deslocamento lateral do CG [m] (+ = para a esquerda, ISO; spec 7.4, hipótese 7). Padrão 0 =
    "sem dado" (0 até medir). Entra na carga estática (suspension_model.static_fz_corner_cg_lateral).
    cza_m2 [m²] e rho_kg_m3 [kg/m³] ligam a hipótese 8 (aero com V = √(a_y·R)): a downforce de cada a_y passa a
    ser 0,5·ρ·CzA·a_y·R, no lugar de downforce_N, com o mesmo aero_balance_front. None = sem dado (EDR-013: aero
    fixo por Setup). cza_m2 exige raio_m e rho_kg_m3, e não aceita downforce_N ≠ 0 junto (a downforce contaria
    duas vezes).
    cda_m2 [m²] e crr [-] ligam a hipótese 9 (tração na traseira; spec 7.4): o eixo traseiro precisa de
    Fx = 0,5·ρ·CdA·a_y·R + Crr·m·G + F_yf·tan δ_ref, dividido igual entre RL e RR (diferencial aberto, hipótese 10),
    e a capacidade lateral de cada roda traseira cai pela elipse de atrito (ver capacidade_eixo). None = sem dado
    (desligado). cda_m2 exige raio_m e rho_kg_m3; crr sozinho só usa a massa (sem raio_m, os termos de arrasto e de
    F_yf·tan δ_ref ficam fora, como o cos δ_ref).
    """
    cfg: VehicleConfig
    ds: TireDataset
    downforce_N: float = 0.0
    aero_balance_front: float = 0.5
    toe_rad: dict = field(default_factory=_zeros)
    camber_estatico_rad: dict = field(default_factory=_zeros)
    ganho_camber: dict = field(default_factory=_zeros)
    roll_steer: dict = field(default_factory=lambda: {"F": 0.0, "R": 0.0})
    raio_m: float | None = None
    ackermann_pct: float | None = None
    cg_lateral_m: float = 0.0
    cza_m2: float | None = None
    rho_kg_m3: float | None = None
    cda_m2: float | None = None
    crr: float | None = None

    def __post_init__(self):
        for nome in ("toe_rad", "camber_estatico_rad", "ganho_camber"):
            d = getattr(self, nome)
            if set(d) != set(CANTOS):
                raise ValueError(f"{nome} exige exatamente as chaves {CANTOS}; recebido {sorted(d)}.")
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in d.values()):
                raise ValueError(f"{nome} exige valores numéricos finitos; recebido {d}.")
        rs = self.roll_steer
        if set(rs) != {"F", "R"}:
            raise ValueError(f"roll_steer exige exatamente as chaves ('F', 'R'); recebido {sorted(rs)}.")
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in rs.values()):
            raise ValueError(f"roll_steer exige valores numéricos finitos; recebido {rs}.")
        for nome in ("raio_m", "ackermann_pct", "cza_m2", "rho_kg_m3", "cda_m2", "crr"):
            v = getattr(self, nome)
            if v is not None and not (isinstance(v, (int, float)) and math.isfinite(v)):
                raise ValueError(f"{nome} exige número finito ou None; recebido {v!r}.")
        if not (isinstance(self.cg_lateral_m, (int, float)) and math.isfinite(self.cg_lateral_m)):
            raise ValueError(f"cg_lateral_m exige número finito; recebido {self.cg_lateral_m!r}.")
        if self.raio_m is not None and self.raio_m <= 0.0:
            raise ValueError(f"raio_m deve ser > 0; recebido {self.raio_m!r}.")
        if self.rho_kg_m3 is not None and self.rho_kg_m3 <= 0.0:
            raise ValueError(f"rho_kg_m3 deve ser > 0; recebido {self.rho_kg_m3!r}.")
        for nome in ("cda_m2", "crr"):
            v = getattr(self, nome)
            if v is not None and v < 0.0:
                raise ValueError(f"{nome} deve ser >= 0; recebido {v!r}.")
        # Entradas que só têm sentido com o raio da curva (spec 7.1 e 7.4).
        if self.raio_m is None:
            falta = [nome for nome in ("ackermann_pct", "cza_m2", "cda_m2") if getattr(self, nome) is not None]
            if falta:
                raise ValueError(f"{', '.join(falta)} exige(m) raio_m (raio do skidpad), que está faltando.")
        if self.cza_m2 is not None:
            if self.rho_kg_m3 is None:
                raise ValueError("cza_m2 exige rho_kg_m3 (densidade do ar), que está faltando.")
            if self.downforce_N != 0.0:
                raise ValueError(f"cza_m2 substitui downforce_N (hipótese 8); recebido downforce_N = "
                                 f"{self.downforce_N!r} junto: a downforce contaria duas vezes.")
        if self.cda_m2 is not None and self.rho_kg_m3 is None:
            raise ValueError("cda_m2 exige rho_kg_m3 (densidade do ar), que está faltando.")


def downforce(caso: CasoEquilibrio, ay_ms2: float) -> float:
    """Downforce total [N] em a_y: downforce_N fixo (EDR-013) ou, com cza_m2, 0,5·ρ·CzA·V² com V = √(|a_y|·R)
    (spec 7.4, hipótese 8; curva em regime de raio R)."""
    if caso.cza_m2 is None:
        return caso.downforce_N
    return downforce_por_velocidade(caso.rho_kg_m3, caso.cza_m2, math.sqrt(abs(ay_ms2) * caso.raio_m))


def cargas(caso: CasoEquilibrio, ay_ms2: float) -> dict:
    """Fz [N] por roda em a_y [m/s²] (a_x = 0), com a aerodinâmica do caso (`downforce`) e o CG lateral.

    O CG lateral (hipótese 7) soma à estática a parcela de static_fz_corner_cg_lateral; a transferência lateral
    por a_y (SUS-103) não muda. Com cg_lateral_m = 0 e sem cza_m2 o resultado é o de combined_fz_corner.
    """
    fz = combined_fz_corner(caso.cfg, 0.0, ay_ms2, downforce(caso, ay_ms2),
                            caso.aero_balance_front, warn=False)
    if caso.cg_lateral_m != 0.0:
        st = static_fz_corner(caso.cfg)
        st_y = static_fz_corner_cg_lateral(caso.cfg, caso.cg_lateral_m)
        fz = {c: fz[c] + (st_y[c] - st[c]) for c in CANTOS}
    return fz


def cargas_rotacionadas(caso: CasoEquilibrio, ay_lateral_ms2: float, ay_aero_ms2: float) -> dict:
    """Fz [N] por roda com a parte lateral em `ay_lateral_ms2` e a aerodinâmica em `ay_aero_ms2` (a_x = 0).

    No MMM em raio fixo a velocidade é V² = A·R (a aero e a resistência dependem de A), mas a aceleração lateral no
    eixo do carro é a_y = A·cos β (adendo §2.5): a transferência lateral de carga e o camber seguem a_y, e a
    downforce segue A. `cargas(caso, ay)` é o caso particular com os dois iguais. Função acrescentada (incremento 6)."""
    fz = combined_fz_corner(caso.cfg, 0.0, ay_lateral_ms2, downforce(caso, ay_aero_ms2),
                            caso.aero_balance_front, warn=False)
    if caso.cg_lateral_m != 0.0:
        st = static_fz_corner(caso.cfg)
        st_y = static_fz_corner_cg_lateral(caso.cfg, caso.cg_lateral_m)
        fz = {c: fz[c] + (st_y[c] - st[c]) for c in CANTOS}
    return fz


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


@functools.lru_cache(maxsize=256)
def _esterco_ackermann(L: float, t: float, raio: float, pct: float) -> tuple[float, float]:
    """(δ_interna, δ_externa) [rad] de uma curva à esquerda com δ_ref = L/R e Ackermann pct % (SUS-414).

    δ_i = δ_o + pct/100·(δ_i,Ack(δ_o) − δ_o), com δ_i,Ack de kinematics_model.ackermann_inner_ideal_deg
    (cot δ_o − cot δ_i = t/L). δ_o sai de (δ_o + δ_i)/2 = δ_ref por bissecção; o lado esquerdo cresce
    com δ_o, então a raiz é única. pct = 0 é paralelo: δ_i = δ_o = δ_ref, sem iteração.
    """
    d_ref = L / raio
    if pct == 0.0:
        return d_ref, d_ref

    def interna(d_o: float) -> float:
        ideal = math.radians(ackermann_inner_ideal_deg(math.degrees(d_o), L, t))
        return d_o + pct / 100.0 * (ideal - d_o)

    lo = 1e-12
    hi = math.atan(L / t) * (1.0 - 1e-9)   # além disso cot δ_i ≤ 0: Ackermann sem solução
    if (hi + interna(hi)) / 2.0 < d_ref:
        raise ValueError(f"L/R = {math.degrees(d_ref):.2f}° está fora do que a geometria de Ackermann "
                         f"(L = {L} m, t = {t} m) alcança; revise o raio.")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if (mid + interna(mid)) / 2.0 < d_ref:
            lo = mid
        else:
            hi = mid
    d_o = 0.5 * (lo + hi)
    return interna(d_o), d_o


def esterco_rodas(caso: CasoEquilibrio) -> dict:
    """δ [rad] das rodas dianteiras em curva à esquerda ({"FL": interna, "FR": externa}); {} sem raio_m.

    Sem ackermann_pct (hipótese 2 desligada) as duas valem δ_ref = L/R. Com ele, a interna e a externa
    seguem o % Ackermann da geometria (spec 7.4, hipótese 2; SUS-414) com média δ_ref.
    """
    if caso.raio_m is None:
        return {}
    cfg = caso.cfg
    if caso.ackermann_pct is None:
        d_ref = cfg.wheelbase / caso.raio_m
        return {"FL": d_ref, "FR": d_ref}
    d_i, d_o = _esterco_ackermann(cfg.wheelbase, cfg.track_front, caso.raio_m, float(caso.ackermann_pct))
    return {"FL": d_i, "FR": d_o}


def angulos_velocidade(caso: CasoEquilibrio) -> dict:
    """θ [rad] da velocidade de cada roda, em relação ao eixo X do carro, na curva à esquerda (spec §3.1; EDR-069).

    Centro da curva na linha do eixo traseiro: C = (0, R_c) no referencial com origem no meio do eixo traseiro (ISO
    8855), R_c = √(R² − b²) (b = cg_to_rear; CG na linha central). A velocidade da roda é perpendicular a C → roda:
    θ_FL = atan(L/(R_c − t_f/2)), θ_FR = atan(L/(R_c + t_f/2)) (o par do Ackermann ideal, cot θ_FR − cot θ_FL = t_f/L) e
    θ_RL = θ_RR = 0. A curva à direita é a de espelhar(caso). Exige raio_m; R ≤ b (centro fora da linha do eixo
    traseiro) e R_c ≤ t_f/2 (roda dianteira interna no centro da curva ou além) dão ValueError.
    Limitação (spec §3.1): o α real da traseira desloca o centro para a frente da linha do eixo; a diferença para o
    Python "cinemático" (β real, mmm.alfa_rodas) é medida pela escada, não corrigida.
    """
    if caso.raio_m is None:
        raise ValueError("angulos_velocidade exige raio_m (raio do skidpad), que está faltando.")
    cfg = caso.cfg
    L, b, t = cfg.wheelbase, cfg.cg_to_rear, cfg.track_front
    if caso.raio_m <= b:
        raise ValueError(f"R ≤ b: o centro da curva não fica na linha do eixo traseiro (R = {caso.raio_m!r} m, "
                         f"b = {b!r} m).")
    r_c = math.sqrt(caso.raio_m ** 2 - b ** 2)
    if r_c <= t / 2.0:
        raise ValueError(f"R_c = {r_c!r} m ≤ t_f/2 = {t / 2.0!r} m: a roda dianteira interna fica no centro da curva "
                         f"ou além; revise o raio.")
    return {"FL": math.atan(L / (r_c - t / 2.0)), "FR": math.atan(L / (r_c + t / 2.0)), "RL": 0.0, "RR": 0.0}


def deriva_ackermann(caso: CasoEquilibrio, *, formas: Formas = FORMAS_V42) -> dict:
    """Δα [rad] por roda do Ackermann (hipótese 2, SUS-414), na convenção do código (curva à esquerda: α < 0).

    - Forma v42 (de hoje): Δα_i = −(δ_i − δ_ref) nas dianteiras, δ_ref = L/R. Esterço a mais que o da condição média
      reduz o α da roda; supõe velocidades paralelas nas rodas do eixo.
    - Forma v43 (EDR-066; centro da curva na linha do eixo traseiro, angulos_velocidade):
      Δα_i = −(δ_i − δ_ref) + (θ_i − θ̄_F) nas dianteiras, θ̄_F = (θ_FL + θ_FR)/2. O α da roda é θ_i − δ_i a menos
      de um termo comum ao eixo: o termo novo é a parte própria da roda no ângulo da velocidade. A spec §4.1 escreve a
      mesma forma com o sinal de |α|. Com δ_i = θ_i (Ackermann que segue a geometria) o termo some.
      Cota medida (TC-ACK-001 (b); veiculo_base dos testes, L = 1,55 m, b = 0,713 m, t_f = 1,2 m, R = 8 m, sintéticos):
      com 100 % de Ackermann, |Δα_FL − Δα_FR| = 1,723e-4 rad ≤ |δ̄ − θ̄_F| = 5,960e-4 rad ≤ (L/R)·(t_f/(2R_c))²
      + |δ_ref − atan(L/R_c)| = 2,724e-3 rad (na v42, 2,855e-2 rad). O resíduo vem de δ̄ = δ_ref = L/R (bisseção de
      esterco_rodas) diferir de θ̄_F; os pares (δ_FL, δ_FR) e (θ_FL, θ_FR) estão na mesma curva de Ackermann
      (cot δ_FR − cot δ_FL = t_f/L), e a diferença entre os espalhamentos é ≈ (2·t_f·θ̄_F/L)·|δ̄ − θ̄_F|. A cota é a
      desigualdade triangular: θ̄_F − atan(L/R_c) é de 2ª ordem em t_f/(2R_c) e δ_ref − atan(L/R_c) é a diferença entre
      L/R e o ângulo da linha central. Com 0 % (paralelo) sobra Δα_FL − Δα_FR = θ_FL − θ_FR
      = atan(L·t_f/(R_c² + L² − t_f²/4)) ≈ L·t_f/R_c² (−3,1 % em R = 8 m, pelo L²; −0,5 % em R = 20 m), o termo que a
      v42 zera.
    Zero atrás, sem ackermann_pct e sem raio_m, nas duas formas (spec 7.4, hipótese 2).
    """
    saida = _zeros()
    if caso.raio_m is None or caso.ackermann_pct is None:
        return saida
    d_ref = caso.cfg.wheelbase / caso.raio_m
    for c, d in esterco_rodas(caso).items():
        saida[c] = -(d - d_ref)
    if formas.ackermann == "v43":
        th = angulos_velocidade(caso)
        th_med = (th["FL"] + th["FR"]) / 2.0
        for c in _RODAS_DO_EIXO["F"]:
            saida[c] += th[c] - th_med
    return saida


def deriva_total(caso: CasoEquilibrio, *, formas: Formas = FORMAS_V42) -> dict:
    """Δα [rad] por roda: toe estático (deriva_toe) + Ackermann (deriva_ackermann, na forma de `formas`)."""
    toe = deriva_toe(caso)
    if caso.raio_m is None or caso.ackermann_pct is None:
        return toe
    ack = deriva_ackermann(caso, formas=formas)
    return {c: toe[c] + ack[c] for c in CANTOS}


def _cos_dianteira(caso: CasoEquilibrio, rodas: tuple) -> float:
    """cos δ_ref para o eixo dianteiro com raio_m (spec 7.1, item 3); 1 no traseiro e sem raio_m."""
    if caso.raio_m is None or rodas != _RODAS_DO_EIXO["F"]:
        return 1.0
    return math.cos(caso.cfg.wheelbase / caso.raio_m)


# Começo da mensagem do ValueError de grade_alfa quando o toe consome a faixa de α. capacidade_eixo usa o prefixo para
# separar esse caso (motivo "toe consome a faixa de α") dos outros ValueError da grade, como os de geometria de
# angulos_velocidade na forma v43, que chegam ao motivo com a mensagem original.
_MSG_TOE_GRADE = "toe consome toda a faixa de α do pneu"


def _motivo_grade(exc: ValueError) -> str:
    """Motivo de capacidade para um ValueError de grade_alfa: o texto de sempre para o toe; a mensagem original para
    os outros (geometria da forma v43: R ≤ b, R_c ≤ t_f/2; Ackermann fora do alcance)."""
    return "toe consome a faixa de α" if str(exc).startswith(_MSG_TOE_GRADE) else str(exc)


def grade_alfa(caso: CasoEquilibrio, n_alfa: int, *, formas: Formas = FORMAS_V42) -> list:
    """n_alfa valores de α_ref [rad], igualmente espaçados de 0 a −A (curva à esquerda: α ≤ 0).

    A = min(|ALPMIN|, ALPMAX) − max|Δα| (toe + Ackermann), para que nenhuma roda saia da faixa de α do pneu.
    """
    if n_alfa < 2:
        raise ValueError(f"n_alfa deve ser >= 2; recebido {n_alfa}.")
    p = caso.ds.p
    amplitude = min(abs(p["ALPMIN"]), p["ALPMAX"]) - max(abs(v) for v in deriva_total(caso, formas=formas).values())
    if amplitude <= 0.0:
        raise ValueError(f"{_MSG_TOE_GRADE}; a grade de α ficaria vazia.")
    return [-amplitude * i / (n_alfa - 1) for i in range(n_alfa)]


def fy_eixo(caso: CasoEquilibrio, eixo: str, ay_ms2: float, alfa_ref: float, *,
            formas: Formas = FORMAS_V42) -> float:
    """Σ Fy [N, ISO] das duas rodas do eixo ('F' ou 'R'), com α_roda = α_ref + Δα (toe + Ackermann; κ = 0).

    Com raio_m, a soma da dianteira leva cos δ_ref (força na direção do carro; spec 7.1, item 3).

    Lança TireRangeError se alguma roda sair da faixa do pneu; quem quer um resultado sem
    exceção usa capacidade_eixo.
    """
    rodas = _rodas(eixo)
    fz = cargas(caso, ay_ms2)
    gam = camber(caso, ay_ms2)
    dal = deriva_total(caso, formas=formas)
    soma = sum(wheel_forces(caso.ds, c, fz[c], alfa_ref + dal[c], gam[c], 0.0)[1] for c in rodas)
    return soma * _cos_dianteira(caso, rodas)


@dataclass(frozen=True)
class Capacidade:
    """Capacidade lateral de um eixo. fy_max_N e alfa_pico_rad são None quando o caso sai do domínio.

    Com motivo = "pico na borda da grade de α" o valor fica registrado, mas não serve para saturação.
    limites traz os avisos de entrada do pneu limitada à faixa do .tir (EDR-056), um por roda e
    grandeza, no formato "Fz_FR = 1526,0 N → 1521,0 N (FZMAX)" ou "γ_FL = 4,50° → 4,00° (CAMMAX)" (vírgula decimal,
    _num).
    """
    fy_max_N: float | None
    alfa_pico_rad: float | None
    motivo: str | None
    limites: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Limite:
    """Uma entrada do pneu limitada à faixa: valor real e usado na convenção do projeto (N ou rad)."""
    canto: str
    nome: str          # FZMIN, FZMAX, CAMMIN ou CAMMAX (limite do .tir que foi aplicado)
    real: float
    usado: float
    texto: str


def descolamento(fz: dict, rodas: tuple) -> str | None:
    """Motivo de N/A quando alguma roda do eixo tem Fz <= 0, ou None.

    Fz <= 0 não é limite do pneu: é o fim do domínio do modelo linear de transferência de carga
    (SUS-104; EDR-056, item 1). Por isso não se limita ao FZMIN: a capacidade fica None.
    """
    for c in rodas:
        if fz[c] <= 0.0:
            return (f"Fz_{c} = {_num(fz[c], '.1f')} N ≤ 0: descolamento, fora do domínio do modelo de transferência "
                    f"de carga (SUS-104)")
    return None


def entrada_limitada(caso: CasoEquilibrio, rodas: tuple, fz: dict, gam: dict) -> tuple[dict, dict, list]:
    """Fz e γ que o pneu recebe, limitados à faixa do .tir, e a lista de _Limite (EDR-056, item 1).

    Convenção do PAC2002 (help do Adams 2024.1, p. 83, "Validity Range of the Tire Model Input"): uma
    entrada além da faixa de validade é avaliada no valor mínimo ou máximo da faixa, com aviso. Exige
    Fz > 0 em todas as rodas (quem chama verifica descolamento antes). A faixa de γ vale no referencial
    do pneu, s_g·γ (ds.axis_system pode inverter o sinal); o γ usado volta à convenção do projeto.
    """
    p = caso.ds.p
    s_g = AXIS_TRANSFORMS[caso.ds.axis_system][2]
    fz_u, gam_u, lims = {}, {}, []
    for c in rodas:
        f = fz[c]
        if f < p["FZMIN"] or f > p["FZMAX"]:
            nome = "FZMIN" if f < p["FZMIN"] else "FZMAX"
            fz_u[c] = p[nome]
            lims.append(_Limite(c, nome, f, p[nome], f"Fz_{c} = {_num(f, '.1f')} N → {_num(p[nome], '.1f')} N ({nome})"))
        else:
            fz_u[c] = f
        g_pneu = s_g * gam[c]
        if g_pneu < p["CAMMIN"] or g_pneu > p["CAMMAX"]:
            nome = "CAMMIN" if g_pneu < p["CAMMIN"] else "CAMMAX"
            gam_u[c] = p[nome] / s_g
            lims.append(_Limite(c, nome, gam[c], gam_u[c],
                                f"γ_{c} = {_num(math.degrees(gam[c]), '.2f')}° → "
                                f"{_num(math.degrees(gam_u[c]), '.2f')}° ({nome})"))
        else:
            gam_u[c] = gam[c]
    return fz_u, gam_u, lims


def fy_eixo_limitado(caso: CasoEquilibrio, rodas: tuple, fz_u: dict, gam_u: dict, alfa_ref: float,
                      fatores: dict | None = None, *, formas: Formas = FORMAS_V42) -> float:
    """Σ Fy [N, ISO] do eixo com Fz e γ já limitados à faixa (uso interno de capacidade_eixo).

    fatores (opcional): fator da elipse de atrito por roda, que multiplica a Fy de cada roda antes da soma.
    """
    dal = deriva_total(caso, formas=formas)
    if fatores is None:
        soma = sum(wheel_forces(caso.ds, c, fz_u[c], alfa_ref + dal[c], gam_u[c], 0.0)[1] for c in rodas)
    else:
        soma = sum(fatores[c] * wheel_forces(caso.ds, c, fz_u[c], alfa_ref + dal[c], gam_u[c], 0.0)[1]
                   for c in rodas)
    return soma * _cos_dianteira(caso, rodas)


# ---------------------------------------------------------------------------
# Tração na traseira: elipse de atrito e diferencial aberto (spec 7.4, hipóteses 9 e 10)
# ---------------------------------------------------------------------------

def tracao_ativa(caso: CasoEquilibrio) -> bool:
    """True quando a hipótese 9 está ligada (cda_m2 ou crr informado)."""
    return caso.cda_m2 is not None or caso.crr is not None


MSG_FX_SEM_FRENTE = "Fx exigido (h9v) indisponível: a curva dianteira é inválida nesta linha"


def _curva_sem_elipse(caso: CasoEquilibrio, eixo: str, ay_ms2: float, *, formas: Formas):
    """Σ Fy do eixo em função de α_ref [N], sem o fator da elipse (entrada do pneu limitada à faixa, EDR-056), ou o
    motivo (str) de a curva não existir: descolamento (SUS-104) ou ValueError da grade (toe, geometria v43).

    A grade é testada aqui (com n = 2: a amplitude não depende de n) para o motivo sair antes de qualquer avaliação.
    """
    rodas = _rodas(eixo)
    fz = cargas(caso, ay_ms2)
    desc = descolamento(fz, rodas)
    if desc is not None:
        return desc
    try:
        grade_alfa(caso, 2, formas=formas)
    except ValueError as exc:
        return _motivo_grade(exc)
    fz_u, gam_u, _ = entrada_limitada(caso, rodas, fz, camber(caso, ay_ms2))
    return lambda a: fy_eixo_limitado(caso, rodas, fz_u, gam_u, a, None, formas=formas)


def _alfa_na_grade(curva, alfas: list, req: float) -> float:
    """|α| [rad] em que a curva alcança req na grade (réplica da célula; catálogo C-G3 e C-G4 do plano).

    req >= pico da grade: |α| do pico (o primeiro máximo; sem isso a busca falha e um LOOSE vira N/A). Senão, j = o
    primeiro ponto da grade com Fy >= req: j = 0 dá 0; com j > 0, interpolação linear em |α| entre j − 1 e j.
    """
    fys = [curva(a) for a in alfas]
    i_pico = max(range(len(fys)), key=fys.__getitem__)
    if req >= fys[i_pico]:
        return abs(alfas[i_pico])
    j = next(k for k, f in enumerate(fys) if f >= req)
    if j == 0:
        return 0.0
    a0, a1 = abs(alfas[j - 1]), abs(alfas[j])
    return a0 + (a1 - a0) * (req - fys[j - 1]) / (fys[j] - fys[j - 1])


def _alfa_continuo(curva, alfas_pico: list, req: float) -> float:
    """|α| [rad] em que a curva alcança req, por bisseção de 200 iterações entre 0 e o α do pico (réplica contínua, D2).

    O pico é o primeiro máximo da curva em alfas_pico (grade_alfa de 401 pontos). req >= pico: |α| do pico; a curva já
    alcança req em α = 0: 0. A bisseção é própria (equilibrio não importa mmm, então não usa mmm._brent).
    """
    fys = [curva(a) for a in alfas_pico]
    i_pico = max(range(len(fys)), key=fys.__getitem__)
    a_pico = abs(alfas_pico[i_pico])
    if req >= fys[i_pico]:
        return a_pico
    if curva(0.0) >= req:
        return 0.0
    lo, hi = 0.0, a_pico
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if curva(-mid) >= req:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def alfas_de_arrasto(caso: CasoEquilibrio, ay_ms2: float, *, formas: Formas,
                     n_alfa: int | None) -> tuple[float, float] | str:
    """(|α_F|, |α_R|) [rad] do arrasto induzido em a_y (forma v43 do Fx exigido; EDR-066, spec §4.2), ou o motivo.

    Cada α é o primeiro em que a força do eixo alcança a exigida (forca_exigida; a_y >= 0, curva à esquerda): se a
    força em α_ref = 0 já alcança, 0; se não alcança até o pico, o α do pico. α_F vem da curva dianteira (com
    cos δ_ref, como em fy_eixo_limitado); α_R vem da curva traseira SEM o fator da elipse, que depende do próprio Fx
    (sem referência circular; aproximação rotulada, spec §4.2).
    - n_alfa inteiro: réplica de grade (busca em grade_alfa(caso, n_alfa) e interpolação linear, igual à célula).
    - n_alfa None: réplica contínua (bisseção de 200 iterações entre 0 e o α do pico na grade de 401 pontos), usada
      como física (decisão D2). O pico vem da mesma curva da busca: na traseira, sem a elipse (capacidade_eixo do eixo
      traseiro poria a elipse, e a v43 dela chamaria esta função de novo).
    Curva dianteira inválida (descolamento, toe, geometria): MSG_FX_SEM_FRENTE (decisão D3). Curva traseira inválida
    (descolamento): o motivo dela (capacidade_eixo já para antes, nesse caso).
    """
    req = forca_exigida(caso, ay_ms2)
    saida = []
    for eixo, r in zip(("F", "R"), req):
        curva = _curva_sem_elipse(caso, eixo, ay_ms2, formas=formas)
        if isinstance(curva, str):
            return MSG_FX_SEM_FRENTE if eixo == "F" else curva
        if n_alfa is None:
            saida.append(_alfa_continuo(curva, grade_alfa(caso, 401, formas=formas), r))
        else:
            saida.append(_alfa_na_grade(curva, grade_alfa(caso, n_alfa, formas=formas), r))
    return saida[0], saida[1]


def cinematica_rigida(caso: CasoEquilibrio, alfa_f: float, alfa_r: float) -> dict:
    """Cinemática exata de corpo rígido do modelo de bicicleta em regime, curva à esquerda (uso: fx_balanco_exato).

    Referencial do carro (ISO 8855): origem no meio do eixo traseiro, X para a frente, Y para a esquerda; CG em (b, 0),
    eixo dianteiro em (L, 0). alfa_f e alfa_r são |α_F| e |α_R| [rad]. Com rotação anti-horária (ω > 0), a velocidade
    de um ponto P é ω·ẑ × (P − C) = ω·(−(P − C)_y, (P − C)_x).
    - A roda traseira (sem esterço) precisa da velocidade para fora da curva, a −|α_R| do eixo X, para dar Fy para a
      esquerda: a direção é (cos α_R, −sen α_R). Então P − C = −s·(sen α_R, cos α_R) com s > 0, isto é,
      C = (s·sen α_R, s·cos α_R): o centro fica na reta pela roda traseira perpendicular à velocidade dela (à frente
      do eixo quando α_R > 0).
    - |C − CG| = R: (s·sen α_R − b)² + (s·cos α_R)² = R², ou s² − 2·b·s·sen α_R + b² − R² = 0, cuja raiz positiva é
      s = b·sen α_R + √(R² − b²·cos² α_R).
    - CG: velocidade ∝ (C_y, b − C_x), β = atan2(b − C_x, C_y). Eixo dianteiro: θ_f = atan2(L − C_x, C_y); a roda
      dianteira também precisa da velocidade a |α_F| para fora do plano dela, então δ = θ_f + α_F.
    Com α = 0: C = (0, R_c), δ = atan(L/R_c) e β = atan(b/R_c) (a geometria da spec §3.1). Devolve {"C": (C_x, C_y),
    "s", "beta", "theta_f", "delta"}. Exige raio_m > b.
    """
    if caso.raio_m is None:
        raise ValueError("cinematica_rigida exige raio_m (raio do skidpad), que está faltando.")
    cfg = caso.cfg
    L, b, R = cfg.wheelbase, cfg.cg_to_rear, caso.raio_m
    if R <= b:
        raise ValueError(f"R ≤ b: o centro da curva não fica na linha do eixo traseiro (R = {R!r} m, b = {b!r} m).")
    s = b * math.sin(alfa_r) + math.sqrt(R * R - (b * math.cos(alfa_r)) ** 2)
    cx, cy = s * math.sin(alfa_r), s * math.cos(alfa_r)
    theta_f = math.atan2(L - cx, cy)
    return {"C": (cx, cy), "s": s, "beta": math.atan2(b - cx, cy), "theta_f": theta_f, "delta": theta_f + alfa_f}


def fx_balanco_exato(caso: CasoEquilibrio, ay_ms2: float, alfa_f: float, alfa_r: float) -> float:
    """Oráculo do Fx da curva [N]: balanço longitudinal em X do carro, modelo de bicicleta desacoplado em regime.

    O balanço e a cinemática são exatos para corpo rígido (cinematica_rigida: centro da curva na reta pela roda
    traseira perpendicular à velocidade dela, a |C − CG| = R). Não usa a fórmula do arrasto induzido. alfa_f e alfa_r
    são |α_F| e |α_R| [rad]. Em X: Fx_r − F_pneu,f·sen δ = −m·A·sen β (a aceleração do CG é ω × v, de módulo A,
    perpendicular à velocidade). Em Y: F_yf + F_yr = m·A·cos β = m·a_y, com F_yf = F_pneu,f·cos δ (a componente
    lateral do carro, a de forca_exigida; as forças ficam na linha central, então o momento em torno do CG só tem
    F_yf·a − F_yr·b). Então F_pneu,f = F_yf/cos δ, A = a_y/cos β e
    Fx_r = F_pneu,f·sen δ − m·A·sen β = F_yf·tan δ − m·a_y·tan β (sem as resistências). Em α = 0 os termos em b/R se
    cancelam: F_yf·L/R_c = m·a_y·b/R_c.
    Resto contra o arrasto induzido F_yf·|α_F| + F_yr·|α_R| (TC-FXI-001 (b); veiculo_base dos testes, R = 8 m, 1 g,
    α contínuos do caso, todos sintéticos): 0,7078 N; razão ao escalar juntos os α por 1/2 e o L/R por 1/2 (R → 2R)
    = 8,051 (O(ε³) com α e L/R da mesma ordem); só os α por 1/2, com R fixo = 1,902 (o resto tem termos α·(L/R)² e
    α²·(L/R)). Em R = 9,125 m: 0,5325 N, 8,039 e 1,888. A cinemática aproximada usada antes (δ = atan(L/R_c) + α_F − α_R,
    β = atan(b/R_c) − α_R, que desloca todas as velocidades pelo mesmo α_R) errava O(α·(L/R)²) e dava 0,2607 N
    (R = 8 m) e 0,1897 N (R = 9,125 m).
    """
    cin = cinematica_rigida(caso, alfa_f, alfa_r)
    f_yf = forca_exigida(caso, ay_ms2)[0]
    return f_yf * math.tan(cin["delta"]) - caso.cfg.mass_total * ay_ms2 * math.tan(cin["beta"])


def fx_exigido_traseira(caso: CasoEquilibrio, ay_ms2: float, *, formas: Formas = FORMAS_V42,
                        n_alfa: int | None = None) -> float | str:
    """Fx [N] que o eixo traseiro precisa dar em a_y para manter a velocidade (spec 7.4, hipótese 9).

    Forma v42 (formas.fx = "v42"; n_alfa não entra): Fx = 0,5·ρ·CdA·V² + Crr·m·G + |F_yf|·tan δ_ref, com V² = |a_y|·R
    e F_yf a força lateral exigida na dianteira (forca_exigida): arrasto aerodinâmico, resistência ao rolamento (sobre
    m·G, sem a downforce) e a componente para trás da força das rodas dianteiras esterçadas de δ_ref = L/R. F_yf é a
    componente da força do pneu na direção lateral do carro (F_yf = F_pneu·cos δ_ref, o mesmo cos δ_ref de
    _cos_dianteira); a componente para trás é F_pneu·sen δ_ref = F_yf·tan δ_ref (EDR-057). Cada termo só entra com o
    dado dele (cda_m2; crr; raio_m para o termo da curva). 0 com a hipótese desligada.
    Forma v43 (EDR-066, spec §4.2): o termo da curva vira o arrasto induzido F_yf·|α_F| + F_yr·|α_R|, com os α de
    alfas_de_arrasto (n_alfa inteiro: réplica de grade, a da célula; None: réplica contínua). No balanço
    F_yf·tan δ − m·a_y·tan β (fx_balanco_exato), com δ ≈ L/R + α_F − α_R e β ≈ b/R − α_R, os termos em b/R se
    cancelam (o termo da v42 é a parte que se cancela) e sobra o arrasto induzido; a diferença é de 3ª ordem com α e
    L/R da mesma ordem. Entra com a mesma condição do termo da v42 (tração ativa e raio_m). Exige a_y >= 0 (curva à
    esquerda; a direita é espelhar(caso)): com a_y < 0 dá ValueError, porque F_yf < 0 zeraria o termo. Curva dianteira inválida:
    devolve o motivo MSG_FX_SEM_FRENTE (str), em vez de um número (decisão D3). Omissão rotulada (spec §4.2):
    Σ F_yi·(δ_i − δ̄) por roda.
    """
    cfg = caso.cfg
    fx = 0.0
    if caso.cda_m2 is not None:
        fx += 0.5 * caso.rho_kg_m3 * caso.cda_m2 * abs(ay_ms2) * caso.raio_m
    if caso.crr is not None:
        fx += caso.crr * cfg.mass_total * G
    if tracao_ativa(caso) and caso.raio_m is not None:
        req_f, req_r = forca_exigida(caso, ay_ms2)
        if formas.fx == "v43":
            if ay_ms2 < 0.0:   # com req_f < 0 o arrasto induzido zeraria sem aviso
                raise ValueError(f"Fx exigido na forma v43 exige a_y >= 0 (curva à esquerda; a direita é "
                                 f"espelhar(caso)); recebido a_y = {ay_ms2!r} m/s².")
            alfas = alfas_de_arrasto(caso, ay_ms2, formas=formas, n_alfa=n_alfa)
            if isinstance(alfas, str):
                return alfas
            fx += req_f * alfas[0] + req_r * alfas[1]
        else:
            fx += abs(req_f) * math.tan(cfg.wheelbase / caso.raio_m)
    return fx


def fx_max_puro(ds: TireDataset, fz: float, gamma: float) -> float:
    """Pico de Fx puro em tração [N] do PAC2002 na carga fz [N] e no camber gamma [rad, convenção do projeto].

    Com Cx = PCX1·LCX > 1 o seno da fórmula mágica chega a 1 em κ_pico, e o pico é |Dx| + SVx (mesma forma fechada
    do pico de Fy, TC-EQ-005). A forma fechada só vale se κ_pico cair na faixa de tração do .tir, [0, KPUMAX] ∩
    [KPUMIN, KPUMAX] (κ ≥ 0 é tração; fora da faixa o pneu é avaliado no limite, EDR-056). κ_pico vem de
    Cx·atan(φ) = π/2, φ = (1 − Ex)·u + Ex·atan(u), u = Bx·(κ + SHx): φ é crescente em u para Ex ≤ 1 (o PAC2002 já
    limita Ex a 1), e u sai por bisseção. Com Cx ≤ 1 (o seno só chega a 1 no infinito) ou κ_pico fora da faixa:
    máximo numérico de pure_fx0 sobre κ em [max(0, KPUMIN), KPUMAX] (2001 pontos; a mesma faixa de tração, para
    nenhum κ sair da faixa do .tir). γ vai ao pneu no referencial do arquivo
    (s_g·γ; o Fx não depende do lado).
    """
    p = ds.p
    g_pneu = AXIS_TRANSFORMS[ds.axis_system][2] * gamma
    kappa_pico = _kappa_pico_fx(p, fz, g_pneu)
    if kappa_pico is not None and max(0.0, p["KPUMIN"]) <= kappa_pico <= p["KPUMAX"]:
        _, info = pure_fx0(p, fz, g_pneu, 0.0)
        return abs(info["Dx"]) + info["SVx"]
    n = 2000
    k_ini = max(0.0, p["KPUMIN"])
    return max(pure_fx0(p, fz, g_pneu, k_ini + (p["KPUMAX"] - k_ini) * i / n)[0] for i in range(n + 1))


def _kappa_pico_fx(p: dict, fz: float, g_pneu: float) -> float | None:
    """κ do pico de Fx puro (ramo de tração) do PAC2002, ou None se o seno não chega a 1 (Cx ≤ 1) ou Bx ≤ 0.

    Resolve Cx·atan(φ) = π/2 com φ(u) = (1 − Ex)·u + Ex·atan(u), u = Bx·(κ + SHx), Ex do ramo κ + SHx > 0
    (pure_fx0), por bisseção em u > 0 (φ é crescente para Ex ≤ 1). κ_pico = u/Bx − SHx.
    """
    _, info = pure_fx0(p, fz, g_pneu, p["KPUMAX"])   # Ex e Bx do ramo de tração (κ + SHx > 0)
    cx, bx, ex, shx = info["Cx"], info["Bx"], info["Ex"], info["SHx"]
    if cx <= 1.0 or bx <= 0.0:
        return None
    alvo = math.tan(math.pi / (2.0 * cx))

    def phi(u: float) -> float:
        return (1.0 - ex) * u + ex * math.atan(u)

    lo, hi = 0.0, 1.0
    while phi(hi) < alvo:
        hi *= 2.0
        if hi > 1e12:
            return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if phi(mid) < alvo:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi) / bx - shx


def elipse_traseira(caso: CasoEquilibrio, ay_ms2: float, rodas: tuple, fz_u: dict,
                     gam_u: dict, *, formas: Formas = FORMAS_V42,
                     n_alfa: int | None = None) -> tuple[dict | None, str | None]:
    """(fatores por roda, motivo) da elipse de atrito no eixo traseiro; (None, None) sem tração.

    Diferencial aberto (hipótese 10): Fx igual nas duas rodas, Fx_roda = Fx_exigido/2. Fator da roda c:
    √(1 − (Fx_roda/Fx_max,c)²), com Fx_max,c = fx_max_puro na Fz e no γ que o pneu recebe (já limitados à faixa,
    EDR-056). Fx_roda > Fx_max em alguma roda: (None, "tração excede o atrito longitudinal em <canto>").
    formas e n_alfa vão a fx_exigido_traseira; na forma v43 sem curva dianteira: (None, MSG_FX_SEM_FRENTE).
    """
    if not tracao_ativa(caso):
        return None, None
    fx = fx_exigido_traseira(caso, ay_ms2, formas=formas, n_alfa=n_alfa)
    if isinstance(fx, str):
        return None, fx
    fx_roda = fx / 2.0
    fatores = {}
    for c in rodas:
        fx_max = fx_max_puro(caso.ds, fz_u[c], gam_u[c])
        if fx_roda > fx_max:
            return None, f"tração excede o atrito longitudinal em {c}"
        fatores[c] = math.sqrt(1.0 - (fx_roda / fx_max) ** 2)
    return fatores, None


# Nomes públicos (incremento 6, MMM): a física por roda que o mmm.py reutiliza. Os apelidos com _ mantêm
# os chamadores antigos (equilibrio_linear, testes) sem mudança.
_entrada_limitada = entrada_limitada
_fy_eixo_limitado = fy_eixo_limitado
_elipse_traseira = elipse_traseira
_descolamento = descolamento
RODAS_DO_EIXO = _RODAS_DO_EIXO


def capacidade_eixo(caso: CasoEquilibrio, eixo: str, ay_ms2: float, n_alfa: int, *,
                    formas: Formas = FORMAS_V42) -> Capacidade:
    """Máximo da Fy do eixo sobre grade_alfa, com a entrada do pneu limitada à faixa do .tir (EDR-056).

    - Fz <= 0 em alguma roda: None com motivo de descolamento (SUS-104); a linha fica inválida.
    - Fz > 0 fora de [FZMIN, FZMAX] ou γ fora de [CAMMIN, CAMMAX]: avaliado no limite (convenção do
      PAC2002, help do Adams p. 83); a capacidade é válida e leva o aviso em `limites`.
    - α: a grade fica dentro da faixa por construção; toe que consome a faixa dá None ("toe consome a faixa de α").
      Outro ValueError da grade (geometria da forma v43 em angulos_velocidade; Ackermann fora do alcance) dá None
      com a mensagem original no motivo.
    - Forma v43 do Fx (EDR-066): a curva dianteira inválida na linha deixa a traseira sem Fx exigido; a capacidade
      traseira sai None com MSG_FX_SEM_FRENTE (decisão D3).
    - Tração na traseira (spec 7.4, hipóteses 9 e 10; só com cda_m2 ou crr): a Fy de cada roda traseira é
      multiplicada por √(1 − (Fx/Fx_max)²) antes da soma do eixo e do máximo sobre α (a mesma ordem da curva do
      eixo: escala por roda, e não do máximo depois). Fx > Fx_max em alguma roda: None com o motivo
      "tração excede o atrito longitudinal em <canto>".
      A elipse de atrito é a simplificação da planilha (spec 7.4, h9, coluna Planilha). O limite de um pneu é o
      círculo de atrito F_R² = Fx² + Fy² (Milliken, Race Car Vehicle Dynamics, §2.7, p. 59), que "may be slightly
      elliptical"; Gillespie (Fundamentals of Vehicle Dynamics, pp. 364-365) diz que, com limites lateral e
      longitudinal diferentes, o limite é uma elipse. Nenhum dos dois imprime a fórmula: a elipse normalizada
      (Fx/Fx_max)² + (Fy/Fy_max)² ≤ 1, com semi-eixos iguais aos picos de escorregamento puro do PAC2002 na carga
      e no γ da roda, é a elipse com esses dois eixos e volta ao círculo do Milliken quando eles são iguais. A
      referência do Python na escada de modelos (incremento 6) é o modelo combinado do PAC2002 (spec 7.4, h9,
      coluna Python); o EDR-057 registra esta escolha.
    Nunca extrapola o pneu e nunca lança por faixa.
    """
    rodas = _rodas(eixo)
    fz = cargas(caso, ay_ms2)
    desc = descolamento(fz, rodas)
    if desc is not None:
        return Capacidade(None, None, desc)
    fz_u, gam_u, lims = entrada_limitada(caso, rodas, fz, camber(caso, ay_ms2))
    try:
        alfas = grade_alfa(caso, n_alfa, formas=formas)  # |α_roda| fica dentro de [ALPMIN, ALPMAX] por construção
    except ValueError as exc:
        if n_alfa < 2:
            raise
        return Capacidade(None, None, _motivo_grade(exc))
    fatores = None
    if eixo == "R":
        # n_alfa vai junto: na forma v43 o Fx exigido usa a réplica de grade, com a grade desta capacidade (a célula)
        fatores, motivo_tracao = elipse_traseira(caso, ay_ms2, rodas, fz_u, gam_u, formas=formas, n_alfa=n_alfa)
        if motivo_tracao is not None:
            return Capacidade(None, None, motivo_tracao)
    fys = [fy_eixo_limitado(caso, rodas, fz_u, gam_u, a, fatores, formas=formas) for a in alfas]
    i = max(range(len(fys)), key=fys.__getitem__)
    motivo = "pico na borda da grade de α" if i == len(fys) - 1 else None
    return Capacidade(fys[i], alfas[i], motivo, tuple(lim.texto for lim in lims))


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
    """Resultado da análise de par. veredito ∈ {PUSH, LOOSE, NEUTRO, N/A}; c_n só em PUSH/LOOSE.

    resolucao_ms2: resolução numérica das saturações (EDR-056, item 2), medida contra a grade
    refinada; None quando nenhum eixo satura em nenhuma das grades.
    limitacoes: avisos de entrada do pneu limitada à faixa (EDR-056, item 1) nas capacidades válidas
    usadas no veredito, um por roda e limite (o de maior excesso).
    """
    linhas: tuple
    passo_ms2: float
    ay_sat_f: float | None
    ay_sat_r: float | None
    ay_lim: float | None
    veredito: str
    motivo: str | None
    c_n: float | None
    resolucao_ms2: float | None = None
    limitacoes: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Saturacao:
    ay_sat: float | None      # a_y de saturação [m/s²], ou None
    k: int | None             # índice k do intervalo (k, k+1) em que a folga troca de sinal
    ay_valido: float | None   # último a_y da parte válida contínua (desde k = 0), ou None
    motivo: str | None        # por que não saturou (None quando saturou)


def _folga(linha: LinhaPar, eixo: str) -> float:
    cap, req = (linha.cap_f, linha.req_f) if eixo == "F" else (linha.cap_r, linha.req_r)
    return cap.fy_max_N - req


def _saturacao(linhas: tuple, eixo: str) -> _Saturacao:
    """Primeira troca de sinal da folga entre linhas consecutivas válidas, interpolada linearmente.

    A busca para na primeira linha inválida (capacidade com motivo): nada além dela é usado. Sem troca de sinal, o
    motivo "não satura até <x> g" cita a última linha varrida (linhas[-1]), e não ay_max_g: com ay_max_g = 0,33 e
    passo 0,05, a grade para em 0,3 g.
    """
    ay_valido = None
    m_ant = None
    for k, ln in enumerate(linhas):
        cap = ln.cap_f if eixo == "F" else ln.cap_r
        if cap.motivo is not None:
            return _Saturacao(None, None, ay_valido, f"{cap.motivo} em a_y = {_num(ln.ay_ms2 / G, 'g')} g")
        m = _folga(ln, eixo)
        if m_ant is not None and m_ant > 0.0 >= m:
            a0 = linhas[k - 1].ay_ms2
            ay_sat = a0 + (ln.ay_ms2 - a0) * m_ant / (m_ant - m)
            # ay_valido segue até a última linha válida conhecida (a busca para aqui, mas a
            # linha k é válida)
            return _Saturacao(ay_sat, k - 1, ln.ay_ms2, None)
        ay_valido = ln.ay_ms2
        m_ant = m
    return _Saturacao(None, None, ay_valido, f"não satura até {_num(linhas[-1].ay_ms2 / G, 'g')} g")


def _varredura(caso: CasoEquilibrio, ay_max_g: float, passo_g: float, n_alfa: int, *,
               formas: Formas = FORMAS_V42) -> tuple:
    """Linhas da grade a_y_k = k·passo (k = 0…⌊ay_max/passo⌋) e a saturação de cada eixo."""
    # ⌊ay_max/passo⌋ com folga de arredondamento: 0.3/0.05 = 5.999…, que deve dar 6.
    n = math.floor(ay_max_g / passo_g + 1e-9)
    linhas = []
    for k in range(n + 1):
        ay = k * passo_g * G
        req_f, req_r = forca_exigida(caso, ay)
        linhas.append(LinhaPar(ay_ms2=ay, fz=cargas(caso, ay),
                               cap_f=capacidade_eixo(caso, "F", ay, n_alfa, formas=formas),
                               cap_r=capacidade_eixo(caso, "R", ay, n_alfa, formas=formas),
                               req_f=req_f, req_r=req_r))
    linhas = tuple(linhas)
    return linhas, _saturacao(linhas, "F"), _saturacao(linhas, "R")


# Piso da resolução: ruído de ponto flutuante, para que duas saturações iguais por simetria (diferença
# de ~1e-15 m/s²) não dependam de arredondamento. É tolerância numérica, não banda de engenharia
# (banda de neutro de engenharia só por EDR da equipe; EDR-056, item 2).
_PISO_RESOLUCAO_MS2 = 1e-9 * G


# Fator da faixa do NEUTRO (EDR-065, item 2, decisão do usuário de 2026-11-02): o |S − S2| entre a grade pedida e a
# refinada subestima o erro de S em cerca de 4/3 (Richardson com p = 2: 2^p/(2^p − 1) = 4/3; ver
# docs/inc7/estudo-neutro.md). Fonte única: o analise_par e a regra da folga do mmm.limite usam a faixa calculada
# em _resolucao (o mmm a recebe pronta em resolucao_ms2, sem fator próprio), e a célula da planilha (família F12)
# repete este valor.
FATOR_NEUTRO = 4.0 / 3.0


def _resolucao(pedida: tuple, refinada: tuple, passo_ms2: float, fator_neutro: float = FATOR_NEUTRO) -> float | None:
    """Faixa numérica do NEUTRO (EDR-056, item 2; fator do EDR-065, item 2): max sobre os eixos, no mínimo o piso.

    Eixo que satura nas duas grades contribui FATOR_NEUTRO·|S − S_refinado|. Eixo que satura numa grade e não na
    outra contribui o passo da grade pedida, sem o fator (o passo é um limite, não uma estimativa do |S − S2|). O
    piso de 1e-9 g também fica sem o fator. O ramo de um eixo só (PUSH/LOOSE por um eixo, em analise_par) lê esta
    mesma faixa. None quando nenhum eixo satura em nenhuma das grades.
    fator_neutro (só para comparar com planilhas anteriores à V4.3, que não têm o 4/3): 1.0 devolve a regra
    histórica.
    """
    difs = []
    for s, s_ref in zip(pedida, refinada):
        if s is not None and s_ref is not None:
            difs.append(fator_neutro * abs(s - s_ref))
        elif s is not None or s_ref is not None:
            difs.append(passo_ms2)
    if not difs:
        return None
    return max(max(difs), _PISO_RESOLUCAO_MS2)


def _limitacoes_detalhe(caso: CasoEquilibrio, linhas: tuple, ay_lim: float | None) -> list[dict]:
    """Limitações de entrada do pneu (EDR-056, item 1) das capacidades válidas usadas no veredito, estruturadas.

    Entram as linhas até a_y_lim, incluída a primeira linha com a_y >= a_y_lim (ela fecha o intervalo
    da interpolação da saturação e do C_N); sem a_y_lim, todas as linhas. Só capacidades válidas
    (motivo None). Uma entrada por roda e limite, na ordem de CANTOS e FZMIN, FZMAX, CAMMIN, CAMMAX:
    {"canto", "nome", "primeira_ay" [m/s²], "pior" (_Limite de maior excesso |real − usado|; no empate, o
    primeiro), "pior_ay" [m/s²]}.
    """
    por_chave: dict = {}
    for ln in linhas:
        for eixo, cap in (("F", ln.cap_f), ("R", ln.cap_r)):
            if cap.motivo is not None or cap.fy_max_N is None or not cap.limites:
                continue
            _, _, lims = entrada_limitada(caso, _rodas(eixo), ln.fz, camber(caso, ln.ay_ms2))
            for lim in lims:
                d = por_chave.get((lim.canto, lim.nome))
                if d is None:
                    por_chave[(lim.canto, lim.nome)] = {"canto": lim.canto, "nome": lim.nome,
                                                        "primeira_ay": ln.ay_ms2, "pior": lim, "pior_ay": ln.ay_ms2}
                elif abs(lim.real - lim.usado) > abs(d["pior"].real - d["pior"].usado):
                    d["pior"], d["pior_ay"] = lim, ln.ay_ms2
        if ay_lim is not None and ln.ay_ms2 >= ay_lim:
            break
    ordem = {nome: i for i, nome in enumerate(("FZMIN", "FZMAX", "CAMMIN", "CAMMAX"))}
    return [por_chave[k] for k in sorted(por_chave, key=lambda k: (CANTOS.index(k[0]), ordem[k[1]]))]


def _limitacoes(caso: CasoEquilibrio, linhas: tuple, ay_lim: float | None) -> tuple[str, ...]:
    """Avisos de limitação (EDR-056, item 1) usados no veredito: o texto do pior caso de cada roda e limite."""
    return tuple(d["pior"].texto for d in _limitacoes_detalhe(caso, linhas, ay_lim))


def limitacoes_detalhe(res: ResultadoPar, caso: CasoEquilibrio) -> list[dict]:
    """Detalhe estruturado de res.limitacoes (mesmas linhas e mesma escolha; ver _limitacoes_detalhe).

    caso tem de ser o caso que gerou res. Cada dict traz canto, nome do limite (FZMIN/FZMAX/CAMMIN/CAMMAX), a
    primeira a_y em que o limite aparece, o _Limite de maior excesso (campos real, usado e texto) e a a_y dele.
    """
    return _limitacoes_detalhe(caso, res.linhas, res.ay_lim)


def analise_par(caso: CasoEquilibrio, ay_max_g: float = 2.0, passo_g: float = 0.05,
                n_alfa: int = 25, *, formas: Formas = FORMAS_V42,
                fator_neutro: float = FATOR_NEUTRO) -> ResultadoPar:
    """Varre a_y_k = k·passo (k = 0…⌊ay_max/passo⌋) e decide PUSH/LOOSE/NEUTRO pelo eixo que satura antes.

    Milliken §7.1 (p. 283-286) e §8.6 (p. 320; EDR-056): o eixo que satura primeiro define o
    comportamento no limite (dianteiro = push, final understeer; traseiro = loose, final oversteer);
    o cruzamento das fronteiras sobre N = 0 é neutro. Regras (EDR-056, item 2 e 3), com S, V e a folga
    da grade pedida e a faixa numérica R (fator_neutro·|S − S2| contra uma grade refinada passo/2, 2·n_alfa − 1;
    ver _resolucao):
    - os dois eixos saturam: Δ = S_r − S_f; |Δ| <= R -> NEUTRO; Δ > R -> PUSH; Δ < −R -> LOOSE;
    - só a frente satura: PUSH se a traseira segue válida até V_r >= S_f + R; senão N/A com o motivo
      da traseira (simétrico para LOOSE);
    - nenhum satura: N/A com o motivo do eixo cuja parte válida acaba antes.
    C_N (spec 7.2; Milliken §8.4, p. 311-312) é o momento de guinada adimensional que sobra no limite:
    a folga do eixo não saturado em a_y_lim vezes o braço até o CG, sobre W·L, com W = m·G.

    Entrada do pneu fora da faixa entra limitada, com aviso (EDR-056, item 1; ver capacidade_eixo).
    Capacidade com motivo (descolamento, pico na borda da grade de α, toe) nunca entra no cálculo:
    a busca do eixo para nela e o veredito sai N/A se ela impedir a decisão.
    formas (decisão D1 do plano do inc. 7): forma das fórmulas do EDR-066, repassada a capacidade_eixo; o padrão
    FORMAS_V42 é o comportamento de hoje.
    fator_neutro (EDR-065 item 2): FATOR_NEUTRO = 4/3 desde a V4.3; quem compara com uma planilha V4.1 ou V4.2, que não
    tem o fator, passa fator_neutro=1.0 (regra histórica). Vale também em analise_par_dois_sentidos e
    varredura_pneu (**kw).
    """
    if not (isinstance(ay_max_g, (int, float)) and ay_max_g > 0 and math.isfinite(ay_max_g)):
        raise ValueError(f"ay_max_g deve ser > 0 e finito; recebido {ay_max_g!r}.")
    if not (isinstance(passo_g, (int, float)) and passo_g > 0 and math.isfinite(passo_g)):
        raise ValueError(f"passo_g deve ser > 0 e finito; recebido {passo_g!r}.")
    if not (isinstance(n_alfa, int) and n_alfa >= 3):
        raise ValueError(f"n_alfa deve ser um inteiro >= 3; recebido {n_alfa!r}.")

    linhas, sf, sr = _varredura(caso, ay_max_g, passo_g, n_alfa, formas=formas)
    _, sf_ref, sr_ref = _varredura(caso, ay_max_g, passo_g / 2.0, 2 * n_alfa - 1, formas=formas)
    passo_ms2 = passo_g * G
    S_f, S_r = sf.ay_sat, sr.ay_sat
    V_f = sf.ay_valido if sf.ay_valido is not None else -math.inf
    V_r = sr.ay_valido if sr.ay_valido is not None else -math.inf
    res = _resolucao((S_f, S_r), (sf_ref.ay_sat, sr_ref.ay_sat), passo_ms2, fator_neutro)

    motivo = None
    if S_f is not None and S_r is not None:
        delta = S_r - S_f
        if abs(delta) <= res:
            veredito = NEUTRO
        else:
            veredito = PUSH if delta > 0.0 else LOOSE
    elif S_f is not None and V_r >= S_f + res:
        veredito = PUSH
    elif S_r is not None and V_f >= S_r + res:
        veredito = LOOSE
    else:
        veredito = NA
        if S_f is not None:        # o traseiro não chegou válido até S_f + R
            motivo = sr.motivo
        elif S_r is not None:      # o dianteiro não chegou válido até S_r + R
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
                        veredito=veredito, motivo=motivo, c_n=c_n, resolucao_ms2=res,
                        limitacoes=_limitacoes(caso, linhas, ay_lim))


# ---------------------------------------------------------------------------
# Dois sentidos de curva (spec 7.4, hipótese 7)
# ---------------------------------------------------------------------------

_TROCA_LR = {"FL": "FR", "FR": "FL", "RL": "RR", "RR": "RL"}


def espelhar(caso: CasoEquilibrio) -> CasoEquilibrio:
    """Caso espelhado no plano XZ: a curva à direita do carro real vista como curva à esquerda.

    - toe e camber estático: trocados entre L e R (as convenções toe-out + e topo para fora + valem por roda e são
      simétricas no espelho, EDR-002);
    - ganho de camber: trocado entre L e R e com o sinal invertido. O ganho é dγ/dφ com φ > 0 rolando para a direita
      (ISO); no espelho a rolagem troca de sinal (φ_espelho = −φ_real), então ganho_espelho[FR] = −ganho[FL]. Um eixo
      de braços simétricos (FL = −g, FR = +g; gradiente de eixo (g_R − g_L)/2 = g) fica igual ao espelhar, como
      deve. Só trocar, sem o sinal, inverteria o gradiente de eixo;
    - roll steer: igual (coeficiente por eixo; ε·φ troca de sinal junto com φ e o esterço também espelha);
    - CG lateral: y → −y. Ackermann, raio e aero ficam (geometria simétrica; a roda interna da análise é sempre FL).
    """
    def troca(d: dict) -> dict:
        return {c: d[_TROCA_LR[c]] for c in CANTOS}

    return dataclasses.replace(caso, toe_rad=troca(caso.toe_rad),
                               camber_estatico_rad=troca(caso.camber_estatico_rad),
                               ganho_camber={c: -v for c, v in troca(caso.ganho_camber).items()},
                               cg_lateral_m=-caso.cg_lateral_m)


def _chave_pior(r: ResultadoPar) -> float:
    """a_y_lim para ordenar do pior ao melhor; N/A (ou sem a_y_lim) conta como pior (−inf)."""
    return -math.inf if (r.veredito == NA or r.ay_lim is None) else r.ay_lim


def analise_par_dois_sentidos(caso: CasoEquilibrio, *, formas: Formas = FORMAS_V42, **kw) -> dict:
    """analise_par nos dois sentidos de curva (spec 7.4, hipótese 7: com CG lateral ou assimetria, um sentido piora).

    Devolve {"esquerda": ResultadoPar, "direita": ResultadoPar, "pior": str}. A direita é analise_par(espelhar(caso)),
    uma curva à esquerda do carro espelhado; os cantos dela estão no referencial espelhado (FR do espelho = FL real).
    "pior" é o sentido de menor a_y_lim; N/A conta como pior. "empate" quando os dois a_y_lim são iguais
    (bit a bit) ou os dois são N/A; a diferença dentro da resolução numérica não vira empate, e quem lê compara com
    resolucao_ms2. **kw vai para analise_par.
    """
    esq = analise_par(caso, formas=formas, **kw)
    dir_ = analise_par(espelhar(caso), formas=formas, **kw)
    ke, kd = _chave_pior(esq), _chave_pior(dir_)
    pior = "empate" if ke == kd else ("esquerda" if ke < kd else "direita")
    return {"esquerda": esq, "direita": dir_, "pior": pior}


# ---------------------------------------------------------------------------
# Robustez do veredito ao pneu e texto de exibição (spec 7.3 e 7.6)
# ---------------------------------------------------------------------------

# Fatores de escala do PAC2002 (help do Adams 2024.1, "User Scaling Factors", pp. 23-25: tabelas de pure slip,
# combined slip e transient response, conferidas na imagem em 2026-10-20), na ordem das tabelas. LONGVL não é fator
# de escala (é a velocidade de medição) e fica fora. A tabela imprime "LKG" para λKyγ; o .tir do projeto e o
# tire_model usam o nome "LKYG" para esse mesmo fator (EDR-042), e é ele que entra aqui: um "LKG" no .tir não é lido
# pelo tire_model e viraria um fator sem efeito.
FATORES_LAMBDA = ("LFZO", "LIP", "LCZ", "LCX", "LMUX", "LEX", "LKX", "LHX", "LVX", "LGAX",
                  "LCY", "LMUY", "LEY", "LKY", "LHY", "LVY", "LGAY", "LKYG", "LTR", "LRES", "LGAZ",
                  "LMX", "LVMX", "LMY",
                  "LXAL", "LYKA", "LVYKA", "LS",
                  "LSGKP", "LSGAL", "LGYR")


def com_fatores(ds: TireDataset, fatores: dict) -> TireDataset:
    """Cópia do dataset com p[nome] *= valor. Só aceita nomes de FATORES_LAMBDA que existam em ds.p, com valor
    finito e > 0.

    Um nome errado ("LMUX ", "PDY2", "LONGVL") ou um valor 0, negativo ou não finito levanta ValueError: um erro de
    digitação não pode virar "robusto" em silêncio (spec 7.6). O ds de entrada nunca é alterado.
    """
    p = copy.deepcopy(ds.p)
    for nome, valor in fatores.items():
        if not (isinstance(nome, str) and nome in FATORES_LAMBDA and nome in ds.p):
            raise ValueError(f"fator de pneu inválido: {nome!r}; só são aceitos os fatores de escala do PAC2002 "
                             f"(FATORES_LAMBDA) que existam no .tir.")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or valor <= 0.0:
            raise ValueError(f"fator de pneu {nome} = {valor!r}: o valor deve ser finito e > 0.")
        p[nome] = p[nome] * valor
    return dataclasses.replace(ds, p=p)


def varredura_pneu(caso: CasoEquilibrio, fatores: dict, **kw) -> list:
    """Produto cartesiano das listas de fatores; cada combinação roda analise_par com o pneu escalado.

    Devolve [(combinação, ResultadoPar), ...]. Dicionário vazio dá lista vazia. As amplitudes vêm
    de quem chama (EDR-055); esta função não escolhe valor nenhum. **kw vai para analise_par.
    """
    if not fatores:
        return []
    nomes = list(fatores)
    saida = []
    for valores in itertools.product(*(fatores[n] for n in nomes)):
        comb = dict(zip(nomes, valores))
        saida.append((comb, analise_par(dataclasses.replace(caso, ds=com_fatores(caso.ds, comb)), **kw)))
    return saida


def veredito_robusto(vereditos: list) -> tuple:
    """Resume os vereditos da varredura (spec 7.6, item 3): só PUSH puro ou LOOSE puro é robusto.

    Qualquer mistura (inclusive com N/A) é NÃO CONCLUSIVO, porque um ponto N/A não tem veredito. O motivo distingue
    os dois casos (EDR-060 item 8 x): PUSH e LOOSE juntos, ou NEUTRO em algum ponto, é "o sinal depende do pneu";
    um só sinal misturado com N/A é "N/A em parte da varredura (sem inversão de sinal)".
    """
    if not vereditos:
        return (NA, "robustez ao pneu não avaliada")
    unicos = set(vereditos)
    if unicos == {PUSH} or unicos == {LOOSE}:
        return (vereditos[0], "mesmo sinal na varredura exploratória do pneu")
    if unicos == {NA}:
        return (NA, "N/A em toda a varredura")
    if (PUSH in unicos and LOOSE in unicos) or NEUTRO in unicos:
        return (NAO_CONCLUSIVO, "o sinal depende do pneu")
    return (NAO_CONCLUSIVO, "N/A em parte da varredura (sem inversão de sinal)")


_ROTULO = {PUSH: "▲ PUSH: sai de frente (final understeer)",
           LOOSE: "▼ LOOSE: sai de traseira (final oversteer)",
           NEUTRO: "● NEUTRO no limite"}


def texto_veredito(res: ResultadoPar, pior_origem: str, robusto: tuple | None = None, *,
                   origem_do_carro: str = origens.T11) -> str:
    """Texto exato de exibição (spec 7.3). Prefixo "DEMONSTRATIVO · " se a pior origem não for a do carro do projeto
    (D16; `origem_do_carro`, T11 na V4.2, `origens.TX_V41` para reproduzir a V4.1). Com robustez NÃO CONCLUSIVO o
    texto é "? NÃO CONCLUSIVO: " + motivo (EDR-060 item 8 x)."""
    if robusto is not None and robusto[0] == NAO_CONCLUSIVO:
        texto = "? NÃO CONCLUSIVO: " + robusto[1]
    elif res.veredito == NA:
        texto = "N/A: " + (res.motivo or "")
    else:
        texto = _ROTULO[res.veredito]
    return texto if pior_origem == origem_do_carro else "DEMONSTRATIVO · " + texto
