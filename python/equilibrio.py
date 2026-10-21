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

from kinematics_model import ackermann_inner_ideal_deg
from suspension_model import (G, VehicleConfig, combined_fz_corner, downforce_por_velocidade, lateral_dfz,
                              static_fz_corner, static_fz_corner_cg_lateral)
from tire_model import AXIS_TRANSFORMS, TireDataset, pure_fx0, wheel_forces

CANTOS = ("FL", "FR", "RL", "RR")


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


def deriva_ackermann(caso: CasoEquilibrio) -> dict:
    """Δα [rad] por roda do esterçamento além de δ_ref: Δα = −(δ_roda − δ_ref) nas rodas dianteiras.

    Esterço a mais que o da condição média reduz o α da roda (curva à esquerda, ISO). Zero atrás, sem
    ackermann_pct e sem raio_m (spec 7.4, hipótese 2).
    """
    saida = _zeros()
    if caso.raio_m is None or caso.ackermann_pct is None:
        return saida
    d_ref = caso.cfg.wheelbase / caso.raio_m
    for c, d in esterco_rodas(caso).items():
        saida[c] = -(d - d_ref)
    return saida


def deriva_total(caso: CasoEquilibrio) -> dict:
    """Δα [rad] por roda: toe estático (deriva_toe) + Ackermann (deriva_ackermann)."""
    toe = deriva_toe(caso)
    if caso.raio_m is None or caso.ackermann_pct is None:
        return toe
    ack = deriva_ackermann(caso)
    return {c: toe[c] + ack[c] for c in CANTOS}


def _cos_dianteira(caso: CasoEquilibrio, rodas: tuple) -> float:
    """cos δ_ref para o eixo dianteiro com raio_m (spec 7.1, item 3); 1 no traseiro e sem raio_m."""
    if caso.raio_m is None or rodas != _RODAS_DO_EIXO["F"]:
        return 1.0
    return math.cos(caso.cfg.wheelbase / caso.raio_m)


def grade_alfa(caso: CasoEquilibrio, n_alfa: int) -> list:
    """n_alfa valores de α_ref [rad], igualmente espaçados de 0 a −A (curva à esquerda: α ≤ 0).

    A = min(|ALPMIN|, ALPMAX) − max|Δα| (toe + Ackermann), para que nenhuma roda saia da faixa de α do pneu.
    """
    if n_alfa < 2:
        raise ValueError(f"n_alfa deve ser >= 2; recebido {n_alfa}.")
    p = caso.ds.p
    amplitude = min(abs(p["ALPMIN"]), p["ALPMAX"]) - max(abs(v) for v in deriva_total(caso).values())
    if amplitude <= 0.0:
        raise ValueError("toe consome toda a faixa de α do pneu; a grade de α ficaria vazia.")
    return [-amplitude * i / (n_alfa - 1) for i in range(n_alfa)]


def fy_eixo(caso: CasoEquilibrio, eixo: str, ay_ms2: float, alfa_ref: float) -> float:
    """Σ Fy [N, ISO] das duas rodas do eixo ('F' ou 'R'), com α_roda = α_ref + Δα (toe + Ackermann; κ = 0).

    Com raio_m, a soma da dianteira leva cos δ_ref (força na direção do carro; spec 7.1, item 3).

    Lança TireRangeError se alguma roda sair da faixa do pneu; quem quer um resultado sem
    exceção usa capacidade_eixo.
    """
    rodas = _rodas(eixo)
    fz = cargas(caso, ay_ms2)
    gam = camber(caso, ay_ms2)
    dal = deriva_total(caso)
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


def _descolamento(fz: dict, rodas: tuple) -> str | None:
    """Motivo de N/A quando alguma roda do eixo tem Fz <= 0, ou None.

    Fz <= 0 não é limite do pneu: é o fim do domínio do modelo linear de transferência de carga
    (SUS-104; EDR-056, item 1). Por isso não se limita ao FZMIN: a capacidade fica None.
    """
    for c in rodas:
        if fz[c] <= 0.0:
            return (f"Fz_{c} = {_num(fz[c], '.1f')} N ≤ 0: descolamento, fora do domínio do modelo de transferência "
                    f"de carga (SUS-104)")
    return None


def _entrada_limitada(caso: CasoEquilibrio, rodas: tuple, fz: dict, gam: dict) -> tuple[dict, dict, list]:
    """Fz e γ que o pneu recebe, limitados à faixa do .tir, e a lista de _Limite (EDR-056, item 1).

    Convenção do PAC2002 (help do Adams 2024.1, p. 83, "Validity Range of the Tire Model Input"): uma
    entrada além da faixa de validade é avaliada no valor mínimo ou máximo da faixa, com aviso. Exige
    Fz > 0 em todas as rodas (quem chama verifica _descolamento antes). A faixa de γ vale no referencial
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


def _fy_eixo_limitado(caso: CasoEquilibrio, rodas: tuple, fz_u: dict, gam_u: dict, alfa_ref: float,
                      fatores: dict | None = None) -> float:
    """Σ Fy [N, ISO] do eixo com Fz e γ já limitados à faixa (uso interno de capacidade_eixo).

    fatores (opcional): fator da elipse de atrito por roda, que multiplica a Fy de cada roda antes da soma.
    """
    dal = deriva_total(caso)
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


def fx_exigido_traseira(caso: CasoEquilibrio, ay_ms2: float) -> float:
    """Fx [N] que o eixo traseiro precisa dar em a_y para manter a velocidade (spec 7.4, hipótese 9).

    Fx = 0,5·ρ·CdA·V² + Crr·m·G + |F_yf|·tan δ_ref, com V² = |a_y|·R e F_yf a força lateral exigida na dianteira
    (forca_exigida): arrasto aerodinâmico, resistência ao rolamento (sobre m·G, sem a downforce) e a componente
    para trás da força das rodas dianteiras esterçadas de δ_ref = L/R. F_yf é a componente da força do pneu na
    direção lateral do carro (F_yf = F_pneu·cos δ_ref, o mesmo cos δ_ref de _cos_dianteira); a componente para trás
    é F_pneu·sen δ_ref = F_yf·tan δ_ref (EDR-057). Cada termo só entra com o dado dele (cda_m2; crr; raio_m para o
    termo de δ_ref). 0 com a hipótese desligada.
    """
    cfg = caso.cfg
    fx = 0.0
    if caso.cda_m2 is not None:
        fx += 0.5 * caso.rho_kg_m3 * caso.cda_m2 * abs(ay_ms2) * caso.raio_m
    if caso.crr is not None:
        fx += caso.crr * cfg.mass_total * G
    if tracao_ativa(caso) and caso.raio_m is not None:
        fx += abs(forca_exigida(caso, ay_ms2)[0]) * math.tan(cfg.wheelbase / caso.raio_m)
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


def _elipse_traseira(caso: CasoEquilibrio, ay_ms2: float, rodas: tuple, fz_u: dict,
                     gam_u: dict) -> tuple[dict | None, str | None]:
    """(fatores por roda, motivo) da elipse de atrito no eixo traseiro; (None, None) sem tração.

    Diferencial aberto (hipótese 10): Fx igual nas duas rodas, Fx_roda = Fx_exigido/2. Fator da roda c:
    √(1 − (Fx_roda/Fx_max,c)²), com Fx_max,c = fx_max_puro na Fz e no γ que o pneu recebe (já limitados à faixa,
    EDR-056). Fx_roda > Fx_max em alguma roda: (None, "tração excede o atrito longitudinal em <canto>").
    """
    if not tracao_ativa(caso):
        return None, None
    fx_roda = fx_exigido_traseira(caso, ay_ms2) / 2.0
    fatores = {}
    for c in rodas:
        fx_max = fx_max_puro(caso.ds, fz_u[c], gam_u[c])
        if fx_roda > fx_max:
            return None, f"tração excede o atrito longitudinal em {c}"
        fatores[c] = math.sqrt(1.0 - (fx_roda / fx_max) ** 2)
    return fatores, None


def capacidade_eixo(caso: CasoEquilibrio, eixo: str, ay_ms2: float, n_alfa: int) -> Capacidade:
    """Máximo da Fy do eixo sobre grade_alfa, com a entrada do pneu limitada à faixa do .tir (EDR-056).

    - Fz <= 0 em alguma roda: None com motivo de descolamento (SUS-104); a linha fica inválida.
    - Fz > 0 fora de [FZMIN, FZMAX] ou γ fora de [CAMMIN, CAMMAX]: avaliado no limite (convenção do
      PAC2002, help do Adams p. 83); a capacidade é válida e leva o aviso em `limites`.
    - α: a grade fica dentro da faixa por construção; toe que consome a faixa dá None.
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
    desc = _descolamento(fz, rodas)
    if desc is not None:
        return Capacidade(None, None, desc)
    fz_u, gam_u, lims = _entrada_limitada(caso, rodas, fz, camber(caso, ay_ms2))
    try:
        alfas = grade_alfa(caso, n_alfa)  # |α_roda| fica dentro de [ALPMIN, ALPMAX] por construção
    except ValueError:
        if n_alfa < 2:
            raise
        return Capacidade(None, None, "toe consome a faixa de α")
    fatores = None
    if eixo == "R":
        fatores, motivo_tracao = _elipse_traseira(caso, ay_ms2, rodas, fz_u, gam_u)
        if motivo_tracao is not None:
            return Capacidade(None, None, motivo_tracao)
    fys = [_fy_eixo_limitado(caso, rodas, fz_u, gam_u, a, fatores) for a in alfas]
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


def _varredura(caso: CasoEquilibrio, ay_max_g: float, passo_g: float, n_alfa: int) -> tuple:
    """Linhas da grade a_y_k = k·passo (k = 0…⌊ay_max/passo⌋) e a saturação de cada eixo."""
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
    return linhas, _saturacao(linhas, "F"), _saturacao(linhas, "R")


# Piso da resolução: ruído de ponto flutuante, para que duas saturações iguais por simetria (diferença
# de ~1e-15 m/s²) não dependam de arredondamento. É tolerância numérica, não banda de engenharia
# (banda de neutro de engenharia só por EDR da equipe; EDR-056, item 2).
_PISO_RESOLUCAO_MS2 = 1e-9 * G


def _resolucao(pedida: tuple, refinada: tuple, passo_ms2: float) -> float | None:
    """Resolução numérica das saturações (EDR-056, item 2): max|S − S_refinado| sobre os eixos.

    Se um eixo satura numa grade e não na outra, a resolução é o passo da grade pedida. None quando
    nenhum eixo satura em nenhuma das grades.
    """
    difs = []
    for s, s_ref in zip(pedida, refinada):
        if s is not None and s_ref is not None:
            difs.append(abs(s - s_ref))
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
            _, _, lims = _entrada_limitada(caso, _rodas(eixo), ln.fz, camber(caso, ln.ay_ms2))
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
                n_alfa: int = 25) -> ResultadoPar:
    """Varre a_y_k = k·passo (k = 0…⌊ay_max/passo⌋) e decide PUSH/LOOSE/NEUTRO pelo eixo que satura antes.

    Milliken §7.1 (p. 283-286) e §8.6 (p. 320; EDR-056): o eixo que satura primeiro define o
    comportamento no limite (dianteiro = push, final understeer; traseiro = loose, final oversteer);
    o cruzamento das fronteiras sobre N = 0 é neutro. Regras (EDR-056, item 2 e 3), com S, V e a folga
    da grade pedida e a resolução numérica R medida contra uma grade refinada (passo/2, 2·n_alfa − 1):
    - os dois eixos saturam: Δ = S_r − S_f; |Δ| <= R -> NEUTRO; Δ > R -> PUSH; Δ < −R -> LOOSE;
    - só a frente satura: PUSH se a traseira segue válida até V_r >= S_f + R; senão N/A com o motivo
      da traseira (simétrico para LOOSE);
    - nenhum satura: N/A com o motivo do eixo cuja parte válida acaba antes.
    C_N (spec 7.2; Milliken §8.4, p. 311-312) é o momento de guinada adimensional que sobra no limite:
    a folga do eixo não saturado em a_y_lim vezes o braço até o CG, sobre W·L, com W = m·G.

    Entrada do pneu fora da faixa entra limitada, com aviso (EDR-056, item 1; ver capacidade_eixo).
    Capacidade com motivo (descolamento, pico na borda da grade de α, toe) nunca entra no cálculo:
    a busca do eixo para nela e o veredito sai N/A se ela impedir a decisão.
    """
    if not (isinstance(ay_max_g, (int, float)) and ay_max_g > 0 and math.isfinite(ay_max_g)):
        raise ValueError(f"ay_max_g deve ser > 0 e finito; recebido {ay_max_g!r}.")
    if not (isinstance(passo_g, (int, float)) and passo_g > 0 and math.isfinite(passo_g)):
        raise ValueError(f"passo_g deve ser > 0 e finito; recebido {passo_g!r}.")
    if not (isinstance(n_alfa, int) and n_alfa >= 3):
        raise ValueError(f"n_alfa deve ser um inteiro >= 3; recebido {n_alfa!r}.")

    linhas, sf, sr = _varredura(caso, ay_max_g, passo_g, n_alfa)
    _, sf_ref, sr_ref = _varredura(caso, ay_max_g, passo_g / 2.0, 2 * n_alfa - 1)
    passo_ms2 = passo_g * G
    S_f, S_r = sf.ay_sat, sr.ay_sat
    V_f = sf.ay_valido if sf.ay_valido is not None else -math.inf
    V_r = sr.ay_valido if sr.ay_valido is not None else -math.inf
    res = _resolucao((S_f, S_r), (sf_ref.ay_sat, sr_ref.ay_sat), passo_ms2)

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


def analise_par_dois_sentidos(caso: CasoEquilibrio, **kw) -> dict:
    """analise_par nos dois sentidos de curva (spec 7.4, hipótese 7: com CG lateral ou assimetria, um sentido piora).

    Devolve {"esquerda": ResultadoPar, "direita": ResultadoPar, "pior": str}. A direita é analise_par(espelhar(caso)),
    uma curva à esquerda do carro espelhado; os cantos dela estão no referencial espelhado (FR do espelho = FL real).
    "pior" é o sentido de menor a_y_lim; N/A conta como pior. "empate" quando os dois a_y_lim são iguais
    (bit a bit) ou os dois são N/A; a diferença dentro da resolução numérica não vira empate, e quem lê compara com
    resolucao_ms2. **kw vai para analise_par.
    """
    esq = analise_par(caso, **kw)
    dir_ = analise_par(espelhar(caso), **kw)
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

    NEUTRO conta como inversão; qualquer mistura (inclusive com N/A) é NÃO CONCLUSIVO.
    """
    if not vereditos:
        return (NA, "robustez ao pneu não avaliada")
    unicos = set(vereditos)
    if unicos == {PUSH} or unicos == {LOOSE}:
        return (vereditos[0], "mesmo sinal na varredura exploratória do pneu")
    if unicos == {NA}:
        return (NA, "N/A em toda a varredura")
    return (NAO_CONCLUSIVO, "o sinal depende do pneu")


_ROTULO = {PUSH: "▲ PUSH: sai de frente (final understeer)",
           LOOSE: "▼ LOOSE: sai de traseira (final oversteer)",
           NEUTRO: "● NEUTRO no limite"}


def texto_veredito(res: ResultadoPar, pior_origem: str, robusto: tuple | None = None) -> str:
    """Texto exato de exibição (spec 7.3). Prefixo "DEMONSTRATIVO · " se a pior origem não for o TX (D16)."""
    if robusto is not None and robusto[0] == NAO_CONCLUSIVO:
        texto = "? NÃO CONCLUSIVO: o sinal depende do pneu"
    elif res.veredito == NA:
        texto = "N/A: " + (res.motivo or "")
    else:
        texto = _ROTULO[res.veredito]
    return texto if pior_origem == "● Dado do TX" else "DEMONSTRATIVO · " + texto
