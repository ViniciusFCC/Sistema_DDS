"""
MMM em raio fixo (Milliken Moment Method) e escada de hipóteses: física (incremento 6, Tasks 2 a 5).

Fixado A_Y e o raio R do skidpad, ficam determinados V = √(A_Y·R), a downforce, as cargas, o camber e as
forças exigidas por eixo (equilibrio.forca_exigida). Este módulo acha o trim (β, δ) que as entrega.
Há dois caminhos. Desacoplado (variantes da planilha): cada eixo depende de uma incógnita só, e o α_ref de cada
eixo sai de uma raiz 1-D (Brent) no ramo ascendente da soma do eixo, o mesmo critério de equilibrio.capacidade_eixo.
Acoplado (qualquer variante Python de alfa, cos_delta, fx_exigido, tracao, diferencial ou transf_long, ou a linha de
controle planilha_acoplada()): Newton 2-D em (β, δ) com jacobiano por diferença finita, semeado no trim desacoplado da
planilha (adendo §4.1, item 2). Só o caminho acoplado aplica a rotação a_y = A·cos β, a_x = −A·sen β (adendo §2.5); o
parâmetro do trim é A = V²/R (A_Y), e a_y do carro é A·cos β. O desacoplado (planilha) usa a_y = A. A opção
Hipoteses.rotacao_beta=False desliga a rotação no caminho acoplado (a_y = A, a_x = 0, como a planilha): é a linha de
controle planilha_acoplada(rotacao=False), que mede só o viés do método (EDR-064, decisão 2.6 revista).
O limite (T, saturação por eixo, veredito, Q e P), o gradiente K e o stability index valem nos dois caminhos.

Convenções (CLAUDE.md): SI, eixos ISO 8855 (X frente, Y esquerda, Z cima), curva à esquerda (a direita sai de
equilibrio.espelhar), α < 0 dá Fy > 0 à esquerda. O módulo não conhece a origem dos dados e não sabe se a
geometria é sintética: quem o chama carrega esse rótulo.

Referência: Milliken, Race Car Vehicle Dynamics, p. 306-307 (T, Q, P; α_F = β + a/R − δ, α_R = β − b/R);
adendo da especificação do incremento 6 (docs/superpowers/specs/2026-10-27-inc6-mmm-escada-design.md), §2 e §4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace
from typing import Literal

import equilibrio as eq
from equilibrio import CANTOS, G
from tire_model import AXIS_TRANSFORMS, TireRangeError, pure_fx0, wheel_forces

MSG_SEM_RAIO = "MMM em raio fixo exige raio_m (raio do skidpad), que está faltando."


# ---------------------------------------------------------------------------
# Hipóteses e variantes (adendo §3.2)
# ---------------------------------------------------------------------------

_VALORES = {
    "alfa": ("planilha", "cinematico"),
    "cos_delta": ("ref", "trim"),
    "sentido": ("entrada", "dois"),
    "fx_exigido": ("edr057", "balanco"),
    "tracao": ("elipse", "pac2002"),
    "diferencial": ("aberto", "travado"),
    "transf_long": ("nao", "regime"),
}


@dataclass(frozen=True)
class Hipoteses:
    """Uma variante por hipótese. O padrão é a planilha (V4.2): `Hipoteses.planilha()`.

    h_cp_m (altura do centro de pressão, hipótese 11) é None por padrão: sem dado, a parcela D·h_cp/L fica fora
    e só uma sensibilidade a liga (decisão 5 do plano). Cada valor é validado contra o Literal do campo.

    rotacao_beta (padrão True) só age no caminho acoplado (Newton 2-D): True usa os eixos do carro do adendo §2.5,
    a_y = A·cos β e a_x = −A·sen β; False usa a_y = A e a_x = 0, a simplificação da planilha. Com False, TODO termo que
    depende da aceleração do carro segue a_x = 0: a transferência lateral e o camber (a_y = A), a parcela m·a_x·h de
    transf_long="regime" (zero) e o termo m·a_x do balanço de fx_exigido="balanco" (zero, no lugar de −m·A·sen β). Assim a
    opção é uma só simplificação cinemática, aplicada de forma consistente. O desacoplado usa a_y = A sempre e ignora o
    campo. Não é uma hipótese numerada da escada (fica fora de VARIANTES, como h_cp_m): a linha de controle
    "planilha (acoplado, sem rotação)" a desliga com as hipóteses da planilha, que não usam "balanco" nem "regime"
    (EDR-064, decisão 2.6 revista).
    """
    alfa: Literal["planilha", "cinematico"] = "planilha"
    cos_delta: Literal["ref", "trim"] = "ref"
    sentido: Literal["entrada", "dois"] = "entrada"
    fx_exigido: Literal["edr057", "balanco"] = "edr057"
    tracao: Literal["elipse", "pac2002"] = "elipse"
    diferencial: Literal["aberto", "travado"] = "aberto"
    transf_long: Literal["nao", "regime"] = "nao"
    h_cp_m: float | None = None
    rotacao_beta: bool = True

    def __post_init__(self):
        for campo, validos in _VALORES.items():
            v = getattr(self, campo)
            if v not in validos:
                raise ValueError(f"Hipoteses.{campo} deve ser um de {validos}; recebido {v!r}.")
        h = self.h_cp_m
        if h is not None and not (isinstance(h, (int, float)) and math.isfinite(h)):
            raise ValueError(f"Hipoteses.h_cp_m exige número finito ou None; recebido {h!r}.")
        if not isinstance(self.rotacao_beta, bool):
            raise ValueError(f"Hipoteses.rotacao_beta exige bool; recebido {self.rotacao_beta!r}.")

    @classmethod
    def planilha(cls) -> "Hipoteses":
        """As fórmulas da planilha em cada hipótese (as chaves do caso decidem o que está ligado)."""
        return cls()

    @classmethod
    def python_completo(cls) -> "Hipoteses":
        """A variante Python de todas as hipóteses do escopo (hipóteses 1, 2, 3, 7, 9, 10 e 11)."""
        return cls(**{campo: VARIANTES[campo]["python"] for campo in VARIANTES})


# campo -> hipóteses que ele cobre, variante da planilha, variante Python e nome na tabela da escada.
VARIANTES: dict[str, dict] = {
    "alfa": {"hipoteses": (1, 2), "planilha": "planilha", "python": "cinematico", "nome": "1+2"},
    "cos_delta": {"hipoteses": (3,), "planilha": "ref", "python": "trim", "nome": "3"},
    "sentido": {"hipoteses": (7,), "planilha": "entrada", "python": "dois", "nome": "7"},
    "fx_exigido": {"hipoteses": (9,), "planilha": "edr057", "python": "balanco", "nome": "9a"},
    "tracao": {"hipoteses": (9,), "planilha": "elipse", "python": "pac2002", "nome": "9b"},
    "diferencial": {"hipoteses": (10,), "planilha": "aberto", "python": "travado", "nome": "10"},
    "transf_long": {"hipoteses": (11,), "planilha": "nao", "python": "regime", "nome": "11"},
}

# Campos de Hipoteses que não são hipótese numerada da escada (não têm linha própria em VARIANTES).
FORA_DE_VARIANTES = ("h_cp_m", "rotacao_beta")

assert set(VARIANTES) == {f.name for f in fields(Hipoteses)} - set(FORA_DE_VARIANTES)

# Campos cuja variante Python leva o trim ao caminho acoplado (Newton 2-D). O "sentido" não é do trim.
_ACOPLADOS = ("alfa", "cos_delta", "fx_exigido", "tracao", "diferencial", "transf_long")


@dataclass(frozen=True)
class _HipPlanilhaAcoplada(Hipoteses):
    """Hipóteses da planilha forçadas pelo caminho acoplado (Newton 2-D). Com rotacao_beta=True (a_y = A·cos β,
    a_x = −A·sen β) é a linha de controle "planilha (acoplado)" da escada; com rotacao_beta=False (a_y = A, a_x = 0) é a
    "planilha (acoplado, sem rotação)". Nenhuma hipótese muda. Subclasse (e não campo de Hipoteses) para não entrar no
    contrato de VARIANTES; `replace` a preserva."""
    forcar_acoplado: bool = True


def planilha_acoplada(rotacao: bool = True) -> Hipoteses:
    """Hipoteses.planilha() resolvida pelo caminho acoplado (linhas de controle da escada, EDR-064, decisão 2.6 revista).

    rotacao=False: a_y = A e a_x = 0, as mesmas da planilha; a diferença para a `planilha` (desacoplada) é só o método.
    rotacao=True (padrão): a_y = A·cos β e a_x = −A·sen β; a diferença para a de rotacao=False é o efeito da simplificação
    a_y = A da planilha."""
    return _HipPlanilhaAcoplada(rotacao_beta=rotacao)


def _e_acoplada(hip: Hipoteses) -> bool:
    """True se alguma hipótese acoplada está na variante Python, ou se o caminho acoplado foi forçado (planilha_acoplada):
    o trim e o limite usam o Newton 2-D."""
    return getattr(hip, "forcar_acoplado", False) or any(getattr(hip, c) != VARIANTES[c]["planilha"] for c in _ACOPLADOS)


# ---------------------------------------------------------------------------
# Cinemática por roda (adendo §2.1)
# ---------------------------------------------------------------------------

def _exige_raio(caso: eq.CasoEquilibrio) -> float:
    if caso.raio_m is None:
        raise ValueError(MSG_SEM_RAIO)
    return caso.raio_m


def posicoes(caso: eq.CasoEquilibrio) -> dict:
    """(x, y) [m] de cada roda no ISO 8855 com o CG na origem: x = +a na frente e −b atrás, y = ±t/2
    (FL e RL em +t/2)."""
    cfg = caso.cfg
    tf, tr = cfg.track_front / 2.0, cfg.track_rear / 2.0
    return {"FL": (cfg.cg_to_front, tf), "FR": (cfg.cg_to_front, -tf),
            "RL": (-cfg.cg_to_rear, tr), "RR": (-cfg.cg_to_rear, -tr)}


def _esterco_ack_delta(caso: eq.CasoEquilibrio, delta_rad: float) -> dict:
    """δ [rad] de FL (interna) e FR (externa) com média δ_trim e o Ackermann do caso (SUS-414).

    Reusa a bisseção de equilibrio._esterco_ackermann, cujo argumento é o raio: δ_ref = L/raio, então o raio
    equivalente é L/δ. Sem ackermann_pct (hipótese 2 desligada), as duas valem δ.
    """
    if caso.ackermann_pct is None or delta_rad <= 0.0:
        return {"FL": delta_rad, "FR": delta_rad}
    cfg = caso.cfg
    d_i, d_o = eq._esterco_ackermann(cfg.wheelbase, cfg.track_front, cfg.wheelbase / delta_rad,
                                     float(caso.ackermann_pct))
    return {"FL": d_i, "FR": d_o}


def alfa_rodas(caso: eq.CasoEquilibrio, hip: Hipoteses, beta_rad: float, delta_rad: float,
               alfa_ref: dict | None = None) -> dict:
    """α [rad] por roda (canto -> α), convenção do projeto (α < 0 dá Fy > 0 à esquerda).

    - alfa="planilha": α_roda = α_ref do eixo + deriva_total(caso)[c] (toe e Ackermann com velocidades paralelas).
      alfa_ref = {"F": .., "R": ..}; sem ele, vem das fórmulas de ângulo pequeno do Milliken (p. 307),
      α_F = β + a/R − δ e α_R = β − b/R.
    - alfa="cinematico": α_i = atan2(sen β + x_i/R, cos β − y_i/R) − δ_i, com δ_i = δ (mais o Ackermann pela
      geometria SUS-414 aplicado ao δ do trim) menos deriva_toe. V se cancela (adendo §2.1).
    """
    R = _exige_raio(caso)
    cfg = caso.cfg
    if hip.alfa == "planilha":
        if alfa_ref is None:
            alfa_ref = {"F": beta_rad + cfg.cg_to_front / R - delta_rad, "R": beta_rad - cfg.cg_to_rear / R}
        dal = eq.deriva_total(caso)
        return {c: alfa_ref["F" if c in eq.RODAS_DO_EIXO["F"] else "R"] + dal[c] for c in CANTOS}
    toe = eq.deriva_toe(caso)
    d_frente = _esterco_ack_delta(caso, delta_rad)
    saida = {}
    for c, (x, y) in posicoes(caso).items():
        d_i = d_frente.get(c, 0.0) - toe[c]
        saida[c] = math.atan2(math.sin(beta_rad) + x / R, math.cos(beta_rad) - y / R) - d_i
    return saida


# ---------------------------------------------------------------------------
# Brent (stdlib: o projeto não usa scipy)
# ---------------------------------------------------------------------------

def _brent(f, a: float, b: float, tol: float = 1e-14, maxit: int = 200) -> float:
    """Raiz de f em [a, b] pelo método de Brent. Exige f(a)·f(b) <= 0; tol é a tolerância em x."""
    fa, fb = f(a), f(b)
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    if fa * fb > 0.0:
        raise ValueError("Brent exige um intervalo com troca de sinal.")
    if abs(fa) < abs(fb):
        a, b, fa, fb = b, a, fb, fa
    c, fc = a, fa
    d = c
    usou_bissecao = True
    for _ in range(maxit):
        if fb == 0.0 or abs(b - a) < tol:
            return b
        if fa != fc and fb != fc:   # interpolação quadrática inversa
            s = (a * fb * fc / ((fa - fb) * (fa - fc)) + b * fa * fc / ((fb - fa) * (fb - fc))
                 + c * fa * fb / ((fc - fa) * (fc - fb)))
        else:                         # secante
            s = b - fb * (b - a) / (fb - fa)
        lim = (3.0 * a + b) / 4.0
        fora = not (min(lim, b) < s < max(lim, b))
        if (fora
                or (usou_bissecao and abs(s - b) >= abs(b - c) / 2.0)
                or (not usou_bissecao and abs(s - b) >= abs(c - d) / 2.0)
                or (usou_bissecao and abs(b - c) < tol)
                or (not usou_bissecao and abs(c - d) < tol)):
            s = (a + b) / 2.0
            usou_bissecao = True
        else:
            usou_bissecao = False
        fs = f(s)
        d, c, fc = c, b, fb
        if fa * fs < 0.0:
            b, fb = s, fs
        else:
            a, fa = s, fs
        if abs(fa) < abs(fb):
            a, b, fa, fb = b, a, fb, fa
    return b


# ---------------------------------------------------------------------------
# Trim em raio fixo (adendo §4.1), caminho desacoplado
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Trim:
    """Resultado do trim em A_Y. Convergiu=False deixa todos os campos numéricos (menos ay_ms2) em None.

    alfa [rad], fz [N], fy [N] e fx [N] são dicionários por roda (CANTOS). fy e fx estão nos eixos do carro
    (ISO), os que entram no momento N: na variante cos_delta="ref" a Fy dianteira leva cos δ_ref
    (equilibrio.fy_eixo) e a parcela F·sen δ da dianteira não entra (é a hipótese 3). kappa é None nas
    variantes sem κ por roda. residuo_N = |ΣFy − m·A_Y| (acoplado: |ΣFy − m·a_y| com a_y da §2.5). eixo_sem_raiz é
    "F", "R" ou "F+R" quando faltou raiz no ramo ascendente (acoplado: o eixo saiu do ramo), e None nos demais motivos
    (descolamento, toe, pico na borda, tração acima do atrito, Newton sem convergir).

    causa (só com convergiu=False) classifica a falha de forma estruturada, sem depender do texto do motivo: "dominio"
    (o ponto saiu do domínio da física), "dobra" (o Newton acoplado não acha trim) ou None (um eixo saiu do ramo
    ascendente: é a saturação, e eixo_sem_raiz diz qual).

    Acoplado: delta_rodas é o esterço [rad] de cada roda dianteira (traseiras 0), o ângulo com que as forças do pneu
    foram giradas (cos_delta="trim") e que entra no termo F_yf·sen δ do balanço; fy e fx dianteiros já estão nos
    eixos do carro. kappa tem as quatro rodas (dianteiras 0). No desacoplado delta_rodas é None.
    """
    ay_ms2: float
    beta_rad: float | None
    delta_rad: float | None
    alfa: dict | None
    fz: dict | None
    fy: dict | None
    fx: dict | None
    kappa: dict | None
    convergiu: bool
    residuo_N: float | None
    motivo: str | None
    eixo_sem_raiz: str | None = None
    delta_rodas: dict | None = None
    causa: str | None = None


CAUSA_DOBRA = "dobra"       # o Newton acoplado não achou trim (jacobiano singular, resíduo que não diminui, sem convergir)
CAUSA_DOMINIO = "dominio"   # o ponto saiu do domínio da física (descolamento, faixa do pneu, toe, tração acima do atrito)


def _falha(ay_ms2: float, motivo: str, eixo_sem_raiz: str | None = None, causa: str | None = None) -> Trim:
    return Trim(ay_ms2, None, None, None, None, None, None, None, False, None, motivo, eixo_sem_raiz, None, causa)


def _raiz_eixo(caso: eq.CasoEquilibrio, eixo: str, ay_ms2: float, n_alfa: int) -> dict:
    """α_ref [rad] do eixo no ramo ascendente da soma (de 0 ao α do pico) com Fy_eixo(α_ref) = força exigida.

    Devolve {"alfa_ref", "fz_u", "gam_u", "fatores"} ou {"motivo": str, "sem_raiz": bool}.
    """
    cap = eq.capacidade_eixo(caso, eixo, ay_ms2, n_alfa)
    if cap.fy_max_N is None:
        return {"motivo": f"eixo {eixo}: {cap.motivo}", "sem_raiz": False}
    if cap.motivo is not None:   # pico na borda da grade de α: o valor não serve para saturação
        return {"motivo": f"eixo {eixo}: {cap.motivo}", "sem_raiz": False}
    exigida = eq.forca_exigida(caso, ay_ms2)[0 if eixo == "F" else 1]
    if exigida > cap.fy_max_N:
        return {"motivo": f"sem trim: o eixo {eixo} não alcança a força exigida (exigida "
                          f"{exigida:.1f} N > capacidade {cap.fy_max_N:.1f} N)", "sem_raiz": True}
    rodas = eq.RODAS_DO_EIXO[eixo]
    fz_u, gam_u, _ = eq.entrada_limitada(caso, rodas, eq.cargas(caso, ay_ms2), eq.camber(caso, ay_ms2))
    fatores = eq.elipse_traseira(caso, ay_ms2, rodas, fz_u, gam_u)[0] if eixo == "R" else None

    def f(a: float) -> float:
        return eq.fy_eixo_limitado(caso, rodas, fz_u, gam_u, a, fatores) - exigida

    alto = 0.0
    if f(alto) > 0.0:   # a Fy do toe em α_ref = 0 já passa da exigida: sobe o α_ref até a borda da grade
        alto = -eq.grade_alfa(caso, 2)[-1]
        if f(alto) > 0.0:
            return {"motivo": f"sem trim: o eixo {eixo} dá mais que a força exigida mesmo com α_ref = "
                              f"{math.degrees(alto):.2f}°", "sem_raiz": True}
    a_ref = _brent(f, cap.alfa_pico_rad, alto)
    return {"alfa_ref": a_ref, "fz_u": fz_u, "gam_u": gam_u, "fatores": fatores}


def trim(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, n_alfa: int = 401) -> Trim:
    """Trim em raio fixo no A_Y dado (curva à esquerda), caminho desacoplado.

    Em cada eixo, α_ref é a raiz de Fy_eixo(α_ref) = força exigida no ramo ascendente da soma do eixo (o critério
    de capacidade_eixo, não roda a roda). Depois β = α_R,ref + b/R e δ = β + a/R − α_F,ref (Milliken p. 307).
    Sem raiz num eixo, ou com o domínio do pneu violado, devolve convergiu=False com motivo. Sem raio_m lança
    ValueError (decisão 2 do plano). Variante acoplada: Newton 2-D (_trim_acoplado).
    """
    R = _exige_raio(caso)
    if not ay_ms2 > 0.0:
        raise ValueError(f"ay_ms2 deve ser > 0; recebido {ay_ms2!r}.")
    if _e_acoplada(hip):
        return _trim_acoplado(caso, hip, ay_ms2, n_alfa)
    cfg = caso.cfg
    raiz = {e: _raiz_eixo(caso, e, ay_ms2, n_alfa) for e in ("F", "R")}
    ruins = [e for e in ("F", "R") if "motivo" in raiz[e]]
    if ruins:
        sem = [e for e in ruins if raiz[e]["sem_raiz"]]
        return _falha(ay_ms2, "; ".join(raiz[e]["motivo"] for e in ruins), "+".join(sem) if sem else None,
                      None if sem else CAUSA_DOMINIO)
    a_f, a_r = raiz["F"]["alfa_ref"], raiz["R"]["alfa_ref"]
    beta = a_r + cfg.cg_to_rear / R
    delta = beta + cfg.cg_to_front / R - a_f
    alfa = alfa_rodas(caso, Hipoteses.planilha(), beta, delta, {"F": a_f, "R": a_r})
    fz = eq.cargas(caso, ay_ms2)
    cos_ref = math.cos(cfg.wheelbase / R)
    fx_roda = eq.fx_exigido_traseira(caso, ay_ms2) / 2.0 if eq.tracao_ativa(caso) else 0.0
    fy, fx = {}, {}
    for c in CANTOS:
        eixo = "F" if c in eq.RODAS_DO_EIXO["F"] else "R"
        r = raiz[eixo]
        f_pneu = wheel_forces(caso.ds, c, r["fz_u"][c], alfa[c], r["gam_u"][c], 0.0)[1]
        if r["fatores"] is not None:
            f_pneu *= r["fatores"][c]
        fy[c] = f_pneu * (cos_ref if eixo == "F" else 1.0)
        fx[c] = fx_roda if eixo == "R" else 0.0
    residuo = abs(sum(fy.values()) - cfg.mass_total * ay_ms2)
    if residuo >= 1e-6:
        return _falha(ay_ms2, f"Brent não convergiu: |ΣFy − m·A_Y| = {residuo:.3e} N", None, CAUSA_DOMINIO)
    return Trim(ay_ms2, beta, delta, alfa, fz, fy, fx, None, True, residuo, None)


# ---------------------------------------------------------------------------
# Trim acoplado: Newton 2-D em (β, δ) (adendo §2.1, §2.5, §2.6 e §4.1, item 2)
# ---------------------------------------------------------------------------

_FRENTE = eq.RODAS_DO_EIXO["F"]
_TRASEIRA = eq.RODAS_DO_EIXO["R"]
_MSG_TRACAO = "tração excede o atrito longitudinal em {}"   # o mesmo texto de equilibrio.elipse_traseira
_H_FD_RAD = 1e-6                    # passo da diferença finita do jacobiano [rad]
_PASSO_MAX_RAD = math.radians(0.5)  # passo máximo de β ou δ por iteração do Newton
_MAX_ITER_NEWTON = 50
_TOL_NEWTON = 1e-7                  # |ΣFy − m·a_y| [N] e |N| [N·m] na convergência (os testes exigem 1e-6)
_N_VARREDURA = 32                   # pontos da varredura que antecede o Brent do κ (primeira raiz do ramo ascendente)


class _Falha(Exception):
    """O ponto (β, δ, A_Y) sai do domínio da física por roda; `motivo` é o texto que o chamador devolve."""

    def __init__(self, motivo: str):
        super().__init__(motivo)
        self.motivo = motivo


@dataclass(frozen=True)
class _Aval:
    """Física por roda num ponto (β, δ, A_Y) do caminho acoplado. r_y = ΣFy − m·a_y [N] e n = N [N·m] são os resíduos
    do Newton; fy e fx estão nos eixos do carro; f_frente e f_traseira são as somas de fy por eixo."""
    r_y: float
    n: float
    alfa: dict
    fz: dict
    fy: dict
    fx: dict
    kappa: dict
    delta: dict
    f_frente: float
    f_traseira: float
    limites: tuple


def _steer_frente(caso: eq.CasoEquilibrio, hip: Hipoteses, delta_rad: float) -> dict:
    """Esterço δ_i [rad] das rodas dianteiras com o toe e o Ackermann da variante `alfa` (o mesmo ângulo que sai de α):
    planilha: δ_i = δ − Δα_i (deriva_total); cinemático: Ackermann pela geometria aplicado ao δ do trim, mais o toe."""
    if hip.alfa == "planilha":
        dal = eq.deriva_total(caso)
        return {c: delta_rad - dal[c] for c in _FRENTE}
    toe = eq.deriva_toe(caso)
    d_frente = _esterco_ack_delta(caso, delta_rad)
    return {c: d_frente[c] - toe[c] for c in _FRENTE}


def _wf(caso: eq.CasoEquilibrio, c: str, fz: float, alfa: float, gam: float, kappa: float) -> tuple:
    try:
        return wheel_forces(caso.ds, c, fz, alfa, gam, kappa)
    except TireRangeError as e:
        raise _Falha(f"pneu fora da faixa em {c}: {e}") from None


_PHI = (math.sqrt(5.0) - 1.0) / 2.0


def _golden_min(g, a: float, b: float, n_iter: int) -> tuple[float, float]:
    """(x, g(x)) do mínimo de g (unimodal) em [a, b] por seção áurea."""
    c, d = b - _PHI * (b - a), a + _PHI * (b - a)
    gc, gd = g(c), g(d)
    for _ in range(n_iter):
        if gc < gd:
            b, d, gd = d, c, gc
            c = b - _PHI * (b - a)
            gc = g(c)
        else:
            a, c, gc = c, d, gd
            d = a + _PHI * (b - a)
            gd = g(d)
    return (c, gc) if gc < gd else (d, gd)


def _raiz_primeira(f, x0: float, x_up: float, x_dn: float, n: int = _N_VARREDURA) -> float | None:
    """Primeira raiz de f a partir de x0 (o ramo ascendente), ou None. Anda para x_up se f(x0) < 0 e para x_dn se > 0.

    Varre n passos até a primeira troca de sinal e refina com Brent. Sem troca na grade, uma seção áurea procura o
    extremo perto do ponto mais próximo de cruzar (o pico da curva pode cair entre dois pontos da grade): se ele cruza,
    Brent; senão a curva não alcança o alvo (None)."""
    f0 = f(x0)
    if f0 == 0.0:
        return x0
    s = 1.0 if f0 > 0.0 else -1.0
    x1 = x_dn if s > 0.0 else x_up
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    valores = [f0]
    for i in range(1, n + 1):
        v = f(xs[i])
        if s * v <= 0.0:
            return xs[i] if v == 0.0 else _brent(f, xs[i - 1], xs[i], tol=1e-15)
        valores.append(v)
    i = min(range(n + 1), key=lambda k: s * valores[k])
    a, b = xs[max(i - 1, 0)], xs[min(i + 1, n)]
    xm, gm = _golden_min(lambda x: s * f(x), a, b, 40)
    if gm <= 0.0:
        return _brent(f, a, xm, tol=1e-15) if f(a) * f(xm) < 0.0 else xm
    return None


def _kappa_para_fx(caso: eq.CasoEquilibrio, c: str, fz: float, alfa: float, gam: float, fx_alvo: float) -> float:
    """κ da roda traseira c com wheel_forces(...)[0] = fx_alvo (Brent no ramo ascendente de 0 até KPUMAX; alvo < 0, até
    KPUMIN). Sem raiz o Fx combinado não alcança o alvo: _Falha("tração excede o atrito longitudinal em <canto>")."""
    p = caso.ds.p
    k = _raiz_primeira(lambda kk: _wf(caso, c, fz, alfa, gam, kk)[0] - fx_alvo, 0.0, p["KPUMAX"], p["KPUMIN"])
    if k is None:
        raise _Falha(_MSG_TRACAO.format(c))
    return k


def _fx_puro(caso: eq.CasoEquilibrio, c: str, fz: float, gam: float, kappa: float) -> float:
    """Fx [N] de escorregamento longitudinal puro (PAC2002, α-independente) da roda c: o Fx da elipse de atrito, cujo pico
    é eq.fx_max_puro. Fora de [KPUMIN, KPUMAX] o pneu não é avaliado (como wheel_forces)."""
    p = caso.ds.p
    if not p["KPUMIN"] <= kappa <= p["KPUMAX"]:
        raise _Falha(f"pneu fora da faixa em {c}: kappa={kappa:.3f} fora de [{p['KPUMIN']}, {p['KPUMAX']}]")
    return pure_fx0(p, fz, AXIS_TRANSFORMS[caso.ds.axis_system][2] * gam, kappa)[0]


def _kappa_travado(caso: eq.CasoEquilibrio, fx_roda, beta_rad: float, fx_r: float) -> dict:
    """κ das rodas traseiras com o diferencial travado: ω comum e o mesmo raio de rolamento (suposição declarada),
    κ_i = (ω·R_e − V_x,i)/V_x,i com V_x,i = V·(cos β − y_i/R) (V cancela: w = ω·R_e/V), e w resolvido por Brent para
    ΣFx = Fx_r, com fx_roda(c, κ) o Fx da roda (combinado no PAC2002, puro na elipse). Sem raiz:
    _Falha("tração excede o atrito longitudinal em <canto>"), com o canto da roda interna (a de menor V_x, a primeira a
    esgotar o κ)."""
    R = caso.raio_m
    pos = posicoes(caso)
    den = {c: math.cos(beta_rad) - pos[c][1] / R for c in _TRASEIRA}
    if min(den.values()) <= 0.1:
        raise _Falha("diferencial travado: velocidade longitudinal de uma roda traseira quase nula (raio pequeno demais)")
    p = caso.ds.p
    w_up = min(den[c] * (1.0 + p["KPUMAX"]) for c in _TRASEIRA)
    w_dn = max(den[c] * (1.0 + p["KPUMIN"]) for c in _TRASEIRA)
    w0 = 0.5 * (den["RL"] + den["RR"])

    def f(w: float) -> float:
        return sum(fx_roda(c, w / den[c] - 1.0) for c in _TRASEIRA) - fx_r

    w = _raiz_primeira(f, w0, w_up, w_dn)
    if w is None:
        raise _Falha(_MSG_TRACAO.format(min(den, key=den.get)))
    return {c: w / den[c] - 1.0 for c in _TRASEIRA}


def _fator_elipse(caso: eq.CasoEquilibrio, c: str, fx: float, fz_u: dict, gam_u: dict) -> float:
    """Fator √(1 − (Fx/Fx_max)²) da elipse de atrito da roda c (a mesma de equilibrio.elipse_traseira)."""
    fx_max = eq.fx_max_puro(caso.ds, fz_u[c], gam_u[c])
    if abs(fx) > fx_max:
        raise _Falha(_MSG_TRACAO.format(c))
    return math.sqrt(1.0 - (fx / fx_max) ** 2)


def _avalia(caso: eq.CasoEquilibrio, hip: Hipoteses, beta_rad: float, delta_rad: float, ay_ms2: float) -> _Aval:
    """Forças por roda, resíduos e somas por eixo em (β, δ, A_Y), curva à esquerda, no caminho acoplado.

    - Cargas: eq.cargas_rotacionadas (transferência lateral e camber em a_y = A·cos β, aero em A; ver o bullet dos eixos
      do carro) mais, em transf_long="regime", ΔFz_traseira =
      (m·a_x·h + D·h_cp)/L com a_x = −A·sen β (§2.6), meio a meio nas rodas traseiras e tirada meio a meio das
      dianteiras (a soma das Fz fica m·g); a parcela D·h_cp só com h_cp_m (decisão 5 do plano).
    - α: alfa_rodas (planilha ou cinemático). Dianteira em κ = 0 e Fx do pneu dianteiro nulo (a resistência ao
      rolamento já está em Crr): fy_carro = Fy·cos δ_i (cos_delta="trim") ou Fy·cos δ_ref (cos_delta="ref", sem a
      parcela de Fx da dianteira, como na planilha).
    - Fx exigido na traseira: sem tração ativa no caso, 0; "edr057" é eq.fx_exigido_traseira; "balanco" é
      D + RR + Σ Fy_pneu,i·sen δ_i + m·a_x (§2.5; com a rotação, m·a_x = −m·A·sen β; sem ela, 0), com D e RR dos campos do
      caso (None = termo fora).
    - Tração: aberto, Fx_r/2 em cada roda; travado, κ comum pela cinemática (_kappa_travado). tracao="pac2002" usa o Fx e
      o Fy combinados do wheel_forces em κ; "elipse" usa o Fx puro (_fx_puro) e Fy(κ = 0) vezes o fator da elipse.
    - Eixos do carro (adendo §2.5), no caminho acoplado com hip.rotacao_beta (padrão): a_y = A·cos β e a_x = −A·sen β, com
      A o A_Y do trim (V² = A·R). A parte lateral das cargas e o camber seguem a_y; a aerodinâmica (downforce, arrasto)
      segue A. Com rotacao_beta=False, a_y = A e a_x = 0 (a simplificação da planilha) em todos os termos: cargas, camber,
      regime e balanço. A rotação não é uma hipótese numerada: as duas linhas de controle da escada ("planilha (acoplado,
      sem rotação)" e "planilha (acoplado)") separam o viés do método do efeito da rotação.
    - O arrasto D entra inteiro no eixo x do carro (no lugar de D·cos β); a componente lateral −D·sen β, que o arrasto
      teria no eixo y porque a velocidade faz o ângulo β com o carro, fica fora do balanço lateral (2ª ordem em β, e D é
      uma fração pequena de m·A). Declarado no EDR-064.
    Levanta _Falha se o ponto sair do domínio (descolamento, faixa do pneu, tração acima do atrito).
    """
    cfg = caso.cfg
    R = caso.raio_m
    m, L = cfg.mass_total, cfg.wheelbase
    if hip.rotacao_beta:
        ay_car, ax_car = ay_ms2 * math.cos(beta_rad), -ay_ms2 * math.sin(beta_rad)
    else:   # a simplificação da planilha: a aceleração do carro é A, toda no eixo y dele
        ay_car, ax_car = ay_ms2, 0.0
    arrasto = 0.5 * caso.rho_kg_m3 * caso.cda_m2 * ay_ms2 * R if caso.cda_m2 is not None else 0.0
    fz = dict(eq.cargas_rotacionadas(caso, ay_car, ay_ms2))
    if hip.transf_long == "regime":
        extra = arrasto * hip.h_cp_m if hip.h_cp_m is not None else 0.0
        d_fz = (m * ax_car * cfg.cg_height + extra) / L
        for c in _TRASEIRA:
            fz[c] += d_fz / 2.0
        for c in _FRENTE:
            fz[c] -= d_fz / 2.0
    desc = eq.descolamento(fz, CANTOS)
    if desc is not None:
        raise _Falha(desc)
    fz_u, gam_u, lims = eq.entrada_limitada(caso, CANTOS, fz, eq.camber(caso, ay_car))
    alfa = alfa_rodas(caso, hip, beta_rad, delta_rad)
    steer = _steer_frente(caso, hip, delta_rad)
    cos_ref = math.cos(L / R)

    fy_pneu = {c: _wf(caso, c, fz_u[c], alfa[c], gam_u[c], 0.0)[1] for c in _FRENTE}
    fy, fx = {}, {}
    for c in _FRENTE:
        if hip.cos_delta == "trim":
            fy[c] = fy_pneu[c] * math.cos(steer[c])    # + Fx_pneu·sen δ_i, com Fx_pneu dianteiro = 0
            fx[c] = -fy_pneu[c] * math.sin(steer[c])   # + Fx_pneu·cos δ_i
        else:
            fy[c] = fy_pneu[c] * cos_ref
            fx[c] = 0.0

    ativa = eq.tracao_ativa(caso)
    if not ativa:
        fx_r = 0.0
    elif hip.fx_exigido == "edr057":
        fx_r = eq.fx_exigido_traseira(caso, ay_ms2)
    else:
        rr = caso.crr * m * G if caso.crr is not None else 0.0
        fx_r = arrasto + rr + sum(fy_pneu[c] * math.sin(steer[c]) for c in _FRENTE) + m * ax_car

    def fx_roda(c: str, k: float) -> float:
        if hip.tracao == "pac2002":
            return _wf(caso, c, fz_u[c], alfa[c], gam_u[c], k)[0]
        return _fx_puro(caso, c, fz_u[c], gam_u[c], k)

    kappa = {c: 0.0 for c in CANTOS}
    if ativa:
        if hip.diferencial == "travado":
            kappa.update(_kappa_travado(caso, fx_roda, beta_rad, fx_r))
        elif hip.tracao == "pac2002":
            for c in _TRASEIRA:
                kappa[c] = _kappa_para_fx(caso, c, fz_u[c], alfa[c], gam_u[c], fx_r / 2.0)
    for c in _TRASEIRA:
        if not ativa:
            fx[c], fy[c] = 0.0, _wf(caso, c, fz_u[c], alfa[c], gam_u[c], 0.0)[1]
        elif hip.tracao == "pac2002":
            fx_w, fy_w = _wf(caso, c, fz_u[c], alfa[c], gam_u[c], kappa[c])[:2]
            fx[c], fy[c] = (fx_r / 2.0 if hip.diferencial == "aberto" else fx_w), fy_w
        else:
            fx_w = fx_r / 2.0 if hip.diferencial == "aberto" else fx_roda(c, kappa[c])
            fy[c] = _wf(caso, c, fz_u[c], alfa[c], gam_u[c], 0.0)[1] * _fator_elipse(caso, c, fx_w, fz_u, gam_u)
            fx[c] = fx_w

    r_y = sum(fy.values()) - m * ay_car
    n = _momento(caso, fy, fx)
    return _Aval(r_y, n, alfa, fz, fy, fx, kappa, {**steer, "RL": 0.0, "RR": 0.0},
                 sum(fy[c] for c in _FRENTE), sum(fy[c] for c in _TRASEIRA), tuple(lim.texto for lim in lims))


def _eixos_fora_do_ramo(s_frente: float, s_traseira: float) -> str | None:
    """"F", "R" ou "F+R" para o(s) eixo(s) cuja inclinação deixou de ser ascendente (∂Fy_f/∂δ <= 0; ∂Fy_r/∂β >= 0), ou
    None. Em curva à esquerda a Fy do eixo cresce com δ na frente e cai com β atrás (α_R = β − b/R)."""
    fora = [e for e, ruim in (("F", not s_frente > 0.0), ("R", not s_traseira < 0.0)) if ruim]
    return "+".join(fora) if fora else None


def _motivo_fora_do_ramo(eixo: str, caso: eq.CasoEquilibrio | None = None, hip: Hipoteses | None = None,
                         aval: "_Aval | None" = None) -> str:
    """Motivo de "um eixo saiu do ramo ascendente". Com o diferencial travado e tração ativa, o texto genérico engana: o
    travado reparte o Fx pela cinemática (κ comum), com Fx diferente nas duas traseiras, e o Fx de cada roda reduz a Fy dela
    (elipse de atrito ou pneu combinado PAC2002, conforme hip.tracao). Esse Fx pode tirar o eixo R do ramo antes do pico de
    Fy, mas a causa não foi isolada (não se mediu o mesmo ponto sem o Fx). Nesse caso o motivo leva o Fx e o κ por roda
    traseira no ponto da falha, para quem lê julgar."""
    base = f"sem trim: o eixo {eixo} saiu do ramo ascendente da soma do eixo (dFy/dα ≤ 0)"
    if caso is None or hip is None or aval is None or hip.diferencial != "travado" or not eq.tracao_ativa(caso):
        return base
    fx = ", ".join(f"{c} {aval.fx[c]:.0f} N (κ = {aval.kappa[c]:.3f})" for c in _TRASEIRA)
    reducao = "pela elipse de atrito" if hip.tracao == "elipse" else "pelo pneu combinado (PAC2002)"
    return f"{base}; diferencial travado, Fx por roda traseira: {fx} (o Fx de cada roda reduz a Fy dela {reducao})"


def _newton(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, beta0: float, delta0: float) -> tuple:
    """(_Aval, (β, δ), None, None, None) no trim, ou (None, None, motivo, eixo_sem_raiz, causa).

    Newton 2-D em x = (β, δ) para r = (ΣFy − m·a_y, N) = 0, com jacobiano por diferença finita (passo 1e-6 rad), passo
    limitado a 0,5° por iteração, no máximo 50 iterações e retrocesso (passo/2, até 8 vezes) enquanto o ponto de teste
    sair do domínio (faixa do pneu, tração acima do atrito), sair do ramo ascendente de um eixo, ou não reduzir o resíduo.
    A inclinação de cada eixo sai das mesmas avaliações do jacobiano (∂Fy_f/∂δ > 0 e ∂Fy_r/∂β < 0 no ramo ascendente).
    Sem passo possível porque o pico de um eixo bloqueia, ou sem convergir com o pico bloqueando o último passo: não há
    trim e o eixo vai em eixo_sem_raiz. Sem convergir em 50 iterações com os dois eixos livres, o motivo é o resíduo e
    eixo_sem_raiz é None. O ponto inicial fora do domínio é falha direta."""
    h = _H_FD_RAD
    L = caso.cfg.wheelbase

    def amostra(x: list) -> tuple:
        a0 = _avalia(caso, hip, x[0], x[1], ay_ms2)
        ab = _avalia(caso, hip, x[0] + h, x[1], ay_ms2)
        ad = _avalia(caso, hip, x[0], x[1] + h, ay_ms2)
        fora = _eixos_fora_do_ramo((ad.f_frente - a0.f_frente) / h, (ab.f_traseira - a0.f_traseira) / h)
        jac = [[(ab.r_y - a0.r_y) / h, (ad.r_y - a0.r_y) / h], [(ab.n - a0.n) / h, (ad.n - a0.n) / h]]
        return a0, jac, fora

    def convergiu(a: _Aval) -> bool:
        return abs(a.r_y) < _TOL_NEWTON and abs(a.n) < _TOL_NEWTON

    def merito(a: _Aval) -> float:
        return math.hypot(a.r_y, a.n / L)

    x = [beta0, delta0]
    try:
        a0, j, fora = amostra(x)
    except _Falha as e:
        return None, None, e.motivo, None, CAUSA_DOMINIO
    if fora is not None:
        return None, None, _motivo_fora_do_ramo(fora, caso, hip, a0), fora, None
    bloqueio, aval_bloq = None, None   # eixo(s) em que o pico bloqueou o último passo, e o ponto onde bloqueou
    for _ in range(_MAX_ITER_NEWTON):
        if convergiu(a0):
            return a0, (x[0], x[1]), None, None, None
        det = j[0][0] * j[1][1] - j[0][1] * j[1][0]
        if not math.isfinite(det) or det == 0.0:
            return None, None, "Newton: jacobiano singular", None, CAUSA_DOBRA
        dx = [(-a0.r_y * j[1][1] + a0.n * j[0][1]) / det, (-j[0][0] * a0.n + j[1][0] * a0.r_y) / det]
        escala = max(1.0, max(abs(dx[0]), abs(dx[1])) / _PASSO_MAX_RAD)
        tropeco, aval_trop, motivo_falha, aceito = None, None, None, None
        for k in range(9):
            xt = [x[0] + dx[0] / escala / 2 ** k, x[1] + dx[1] / escala / 2 ** k]
            try:
                at, jt, fora_t = amostra(xt)
            except _Falha as e:
                motivo_falha = e.motivo
                continue
            if fora_t is not None:
                tropeco, aval_trop = fora_t, at
                continue
            if convergiu(at) or merito(at) < merito(a0) * (1.0 - 1e-4):
                aceito = (xt, at, jt)
                break
        if aceito is None:
            if tropeco is not None:
                return None, None, _motivo_fora_do_ramo(tropeco, caso, hip, aval_trop), tropeco, None
            if motivo_falha:
                return None, None, motivo_falha, None, CAUSA_DOMINIO
            return None, None, "Newton: o resíduo não diminui ao longo do passo", None, CAUSA_DOBRA
        bloqueio, aval_bloq = tropeco, aval_trop
        x, a0, j = aceito
    if convergiu(a0):
        return a0, (x[0], x[1]), None, None, None
    if bloqueio is not None:
        return None, None, _motivo_fora_do_ramo(bloqueio, caso, hip, aval_bloq), bloqueio, None
    return None, None, (f"Newton não convergiu em {_MAX_ITER_NEWTON} iterações "
                        f"(|ΣFy − m·a_y| = {abs(a0.r_y):.3e} N, |N| = {abs(a0.n):.3e} N·m)"), None, CAUSA_DOBRA


_ESCALAS_SEMENTE = (1.0, 0.99, 0.97, 0.94, 0.9, 0.8)


def _semente(caso: eq.CasoEquilibrio, ay_ms2: float, n_alfa: int) -> tuple:
    """(trim desacoplado da planilha que serve de chute inicial, o trim em A_Y). O chute é o de A_Y; se a planilha não
    tem trim ali (a variante acoplada pode alcançar um pouco mais), cai para escalas menores de A_Y, que dão um (β, δ)
    próximo. O Newton é o único solver: a semente só diz de onde partir."""
    planilha = Hipoteses.planilha()
    primeiro = None
    for f in _ESCALAS_SEMENTE:
        t = trim(caso, planilha, ay_ms2 * f, n_alfa)
        if primeiro is None:
            primeiro = t
        if t.convergiu:
            return t, primeiro
    return None, primeiro


def _trim_acoplado(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, n_alfa: int) -> Trim:
    semente, primeiro = _semente(caso, ay_ms2, n_alfa)
    if semente is None:
        return _falha(ay_ms2, primeiro.motivo, primeiro.eixo_sem_raiz, primeiro.causa)
    aval, x, motivo, eixo, causa = _newton(caso, hip, ay_ms2, semente.beta_rad, semente.delta_rad)
    if aval is None:
        return _falha(ay_ms2, motivo, eixo, causa)
    com_kappa = eq.tracao_ativa(caso) and (hip.tracao == "pac2002" or hip.diferencial == "travado")
    return Trim(ay_ms2, x[0], x[1], aval.alfa, aval.fz, aval.fy, aval.fx, aval.kappa if com_kappa else None, True,
                abs(aval.r_y), None, None, aval.delta, None)


# ---------------------------------------------------------------------------
# C_N (adendo §2.2)
# ---------------------------------------------------------------------------

def momento_n(trim_: Trim, caso: eq.CasoEquilibrio) -> float:
    """N = Σ(x_i·Fy_i − y_i·Fx_i) [N·m] no ISO 8855, sem o Mz (hipótese 14)."""
    if not trim_.convergiu:
        raise ValueError("momento_n exige um trim que convergiu.")
    return _momento(caso, trim_.fy, trim_.fx)


def _momento(caso: eq.CasoEquilibrio, fy: dict, fx: dict) -> float:
    """N = Σ(x_i·Fy_i − y_i·Fx_i) [N·m] a partir das forças por roda."""
    pos = posicoes(caso)
    return sum(pos[c][0] * fy[c] - pos[c][1] * fx[c] for c in CANTOS)


def _estabilizante(cn_iso):
    """Única fonte do sinal do C_N estabilizante: −C_N do ISO (positivo = push, curva à esquerda).

    Serve nos dois sentidos (a negação é sua própria inversa). Nenhum outro código nega um C_N para isto."""
    return -cn_iso


def cn(trim_: Trim, caso: eq.CasoEquilibrio) -> tuple[float, float]:
    """(cn_iso, cn_estabilizante) com C_N = N/(W·L), W = m·G (Milliken, cap. 8).

    cn_iso tem o sinal do ISO (sobra da traseira em curva à esquerda dá N < 0). cn_estabilizante = −cn_iso numa
    curva à esquerda, a grandeza da planilha (positivo = push). Nenhum código troca o sinal fora desta função.
    """
    cfg = caso.cfg
    cn_iso = momento_n(trim_, caso) / (cfg.mass_total * G * cfg.wheelbase)
    return cn_iso, _estabilizante(cn_iso)


# ---------------------------------------------------------------------------
# Ponto e diagrama em raio fixo com trim lateral (adendo §4.2)
# ---------------------------------------------------------------------------

ROTULO_DIAGRAMA = "raio fixo com trim lateral (V = √(A_Y·R))"
_AY_MAX_PONTO_G = 3.0      # a varredura do ponto vai de 0 a 3·G ...
_N_PASSOS_PONTO = 60       # ... em 61 pontos (passo de 0,05·G)


@dataclass(frozen=True)
class PontoMMM:
    """Um ponto do diagrama de raio fixo com trim lateral. ay_ms2 e cn_iso são None quando não há raiz (motivo diz por
    quê). n_raizes conta as trocas de sinal de ΣFy − m·A_Y na varredura em A_Y (aero forte pode dar mais de uma)."""
    beta_rad: float
    delta_rad: float
    ay_ms2: float | None
    cn_iso: float | None
    n_raizes: int
    motivo: str | None


def _balanco_lateral(caso: eq.CasoEquilibrio, hip: Hipoteses, beta_rad: float, delta_rad: float,
                     ay_ms2: float) -> tuple:
    """(ΣFy − m·A_Y [N], (fy, fx), None) com (β, δ) fixos e as cargas de A_Y, ou (None, None, motivo) se o ponto
    sai do domínio (descolamento ou tração acima do atrito). Mesma física do trim (Fz e γ limitados à faixa,
    elipse da traseira, cos δ_ref na frente); o α de cada roda vem de alfa_rodas, e não de uma raiz por eixo.
    Variante acoplada: _avalia (o resíduo é ΣFy − m·a_y, com a_y da §2.5)."""
    if _e_acoplada(hip):
        try:
            a = _avalia(caso, hip, beta_rad, delta_rad, ay_ms2)
        except _Falha as e:
            return None, None, e.motivo
        return a.r_y, (a.fy, a.fx), None
    cfg = caso.cfg
    R = caso.raio_m
    fz = eq.cargas(caso, ay_ms2)
    desc = eq.descolamento(fz, CANTOS)
    if desc is not None:
        return None, None, desc
    fz_u, gam_u, _ = eq.entrada_limitada(caso, CANTOS, fz, eq.camber(caso, ay_ms2))
    fatores, motivo_tracao = eq.elipse_traseira(caso, ay_ms2, eq.RODAS_DO_EIXO["R"], fz_u, gam_u)
    if motivo_tracao is not None:
        return None, None, motivo_tracao
    alfa = alfa_rodas(caso, hip, beta_rad, delta_rad)
    cos_ref = math.cos(cfg.wheelbase / R)
    fx_roda = eq.fx_exigido_traseira(caso, ay_ms2) / 2.0 if eq.tracao_ativa(caso) else 0.0
    fy, fx = {}, {}
    for c in CANTOS:
        frente = c in eq.RODAS_DO_EIXO["F"]
        try:
            f_pneu = wheel_forces(caso.ds, c, fz_u[c], alfa[c], gam_u[c], 0.0)[1]
        except TireRangeError as e:   # α fora do .tir numa grade de (β, δ): o ponto sai do domínio, não é erro
            return None, None, f"pneu fora da faixa em {c}: {e}"
        if not frente and fatores is not None:
            f_pneu *= fatores[c]
        fy[c] = f_pneu * (cos_ref if frente else 1.0)
        fx[c] = 0.0 if frente else fx_roda
    return sum(fy.values()) - cfg.mass_total * ay_ms2, (fy, fx), None


def ponto(caso: eq.CasoEquilibrio, hip: Hipoteses, beta_rad: float, delta_rad: float,
          ay_ref_ms2: float | None = None) -> PontoMMM:
    """Trim lateral em (β, δ) fixos: o A_Y em que ΣFy(A_Y) = m·A_Y, com o C_N (ISO) nesse A_Y.

    Resolve por Brent no intervalo [0, A_desc], onde A_desc é o primeiro A_Y com alguma Fz <= 0 (ou com o ponto fora
    do domínio, o mesmo critério do trim). Uma varredura prévia de 0 a 3·G em 61 pontos (passo de 0,05·G) acha os
    intervalos e conta em `n_raizes` as trocas de sinal de ΣFy − m·A_Y: com aero forte (CzA alto) pode haver mais de
    uma raiz. **A raiz devolvida é a menor** (a primeira da varredura); só o stability index, que precisa da raiz
    vizinha do trim, passa `ay_ref_ms2` e recebe a mais próxima dele. Sem raiz: ay_ms2 e cn_iso None, com motivo.
    Sem raio_m lança ValueError (decisão 2 do plano).
    """
    _exige_raio(caso)
    passo = _AY_MAX_PONTO_G * G / _N_PASSOS_PONTO
    grade, motivo_fim = [], None
    for k in range(_N_PASSOS_PONTO + 1):
        ay = k * passo
        r, _, motivo = _balanco_lateral(caso, hip, beta_rad, delta_rad, ay)
        if r is None:
            motivo_fim = f"{motivo} em a_y = {eq._num(ay / G, '.3f')} g"
            break
        grade.append((ay, r))
    intervalos = []
    if grade and grade[0][1] == 0.0:
        intervalos.append((grade[0][0], grade[0][0]))
    for (a0, r0), (a1, r1) in zip(grade, grade[1:]):
        if r0 * r1 < 0.0:
            intervalos.append((a0, a1))
        elif r1 == 0.0:
            intervalos.append((a1, a1))
    if not intervalos:
        ate = eq._num(grade[-1][0] / G, ".3f") if grade else "0"
        return PontoMMM(beta_rad, delta_rad, None, None, 0, f"sem raiz de ΣFy = m·A_Y em [0, {ate} g]"
                        + (f"; {motivo_fim}" if motivo_fim else ""))
    if ay_ref_ms2 is None:
        a, b = intervalos[0]
    else:
        a, b = min(intervalos, key=lambda iv: abs(0.5 * (iv[0] + iv[1]) - ay_ref_ms2))

    def f(ay: float) -> float:
        return _balanco_lateral(caso, hip, beta_rad, delta_rad, ay)[0]

    ay_raiz = a if a == b else _brent(f, a, b)
    _, (fy, fx), _ = _balanco_lateral(caso, hip, beta_rad, delta_rad, ay_raiz)
    cfg = caso.cfg
    return PontoMMM(beta_rad, delta_rad, ay_raiz, _momento(caso, fy, fx) / (cfg.mass_total * G * cfg.wheelbase),
                    len(intervalos), None)


def diagrama(caso: eq.CasoEquilibrio, hip: Hipoteses, betas, deltas) -> list[PontoMMM]:
    """O `ponto` em cada par da grade β × δ (β externo, δ interno), no diagrama de **raio fixo com trim lateral**
    (V = √(A_Y·R) em cada ponto; ROTULO_DIAGRAMA): C_N contra A_Y. Não se compara diretamente com a Fig. 8.7 do
    Milliken, que é a velocidade constante (60 mph, p. 308). A escada usa só a curva de trim; isto é exibição."""
    return [ponto(caso, hip, b, d) for b in betas for d in deltas]


# ---------------------------------------------------------------------------
# K e stability index (adendo §2.4)
# ---------------------------------------------------------------------------

AY_REF_G = 0.05          # a_y [g] em que o limite() avalia K e o stability index (regime linear baixo)
_H_K_G = 0.01            # passo da diferença central de K [g]
_H_BETA_RAD = 1e-4       # passo em β do stability index [rad]


class _SemNumero(ValueError):
    """K ou stability index sem número por falta de trim, de raiz lateral ou de variação de A_Y (caso esperado do limite;
    os outros ValueError, de argumento ou de bug, não são engolidos por _k_e_si). Subclasse de ValueError."""


def k_trim(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, n_alfa: int = 401) -> float:
    """K = dδ/dA_Y [rad/(m/s²)] na curva de trim, por diferença central (passo 0,01·G).

    K > 0 é subesterço (δ cresce com A_Y). É o K do oráculo linear (equilibrio_linear.parcelas_k), não o stability
    index (adendo §2.4). Lança ValueError se algum dos dois trims (A_Y ± passo) não existir.
    """
    h = _H_K_G * G
    if not ay_ms2 - h > 0.0:
        raise ValueError(f"k_trim exige ay_ms2 > {h:.4f} m/s² (passo da diferença central); recebido {ay_ms2!r}.")
    t_mais, t_menos = trim(caso, hip, ay_ms2 + h, n_alfa), trim(caso, hip, ay_ms2 - h, n_alfa)
    for t in (t_mais, t_menos):
        if not t.convergiu:
            raise _SemNumero(f"k_trim: sem trim em a_y = {eq._num(t.ay_ms2 / G, '.3f')} g ({t.motivo})")
    return (t_mais.delta_rad - t_menos.delta_rad) / (2.0 * h)


def stability_index(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, n_alfa: int = 401,
                    h_beta_rad: float = _H_BETA_RAD) -> float:
    """Stability index [1/(m/s²)]: dC_N/dA_Y numa linha de δ constante, no trim de ay_ms2 (Milliken cap. 5, p. 204).

    No trim (β*, δ*) daquele A_Y, β* ± h com δ* fixo; o A_Y de cada lado vem do trim lateral (ΣFy = m·A_Y, Brent,
    raiz mais próxima de ay_ms2) e SI = ΔC_N/ΔA_Y. O C_N é o cn_estabilizante (positivo = push), de modo que
    SI > 0 é um carro estável (subesterço) e SI < 0 instável. Sinal: positivo = estabilizante (o sinal do C_N
    estabilizante, o da planilha); o Milliken usa o C_N do ISO, de sinal oposto, então o SI dele tem o sinal trocado.
    Lança ValueError se não houver trim em ay_ms2 ou raiz
    lateral num dos lados.
    """
    t = trim(caso, hip, ay_ms2, n_alfa)
    if not t.convergiu:
        raise _SemNumero(f"stability_index: sem trim em a_y = {eq._num(ay_ms2 / G, '.3f')} g ({t.motivo})")
    mais = ponto(caso, hip, t.beta_rad + h_beta_rad, t.delta_rad, ay_ref_ms2=ay_ms2)
    menos = ponto(caso, hip, t.beta_rad - h_beta_rad, t.delta_rad, ay_ref_ms2=ay_ms2)
    for lado in (mais, menos):
        if lado.ay_ms2 is None:
            raise _SemNumero(f"stability_index: {lado.motivo}")
    d_ay = mais.ay_ms2 - menos.ay_ms2
    if d_ay == 0.0:
        raise _SemNumero("stability_index: A_Y não varia com β (ΔA_Y = 0).")
    return _estabilizante(mais.cn_iso - menos.cn_iso) / d_ay


# ---------------------------------------------------------------------------
# Limite: T, saturação por eixo, veredito, Q e P (adendo §2.3 e §4.1, itens 3 e 4)
# ---------------------------------------------------------------------------

_FRACAO_TOL = 1e-4           # tolerância da bisseção = resolucao_ms2 · esta fração (a resolução declarada é a folga)
_PASSO_VARREDURA_G = 0.05    # passo da varredura de fallback, o mesmo grão do analise_par


@dataclass(frozen=True)
class Limite:
    """Limite do carro em raio fixo (curva à esquerda).

    ay_t_ms2 é o T (maior A_Y com trim). ay_sat_f e ay_sat_r são o A_Y de saturação de cada eixo, por bisseção por
    eixo nas variantes desacopladas; None no eixo que não satura (motivo_sat diz por quê). eixo_satura é "F" ou "R",
    o de menor saturação. Q é o momento residual em T vindo do eixo que ainda tem folga: cn_iso_q com o sinal do ISO e
    cn_estabilizante_q = −cn_iso_q (positivo = push, a grandeza da planilha). cn_p é o C_N em P (soma vetorial das
    capacidades, fora do trim; só alcançável num transiente) no sinal do ISO, como cn_iso_q. stability_index [1/(m/s²)]
    e k_rad_por_ms2 [rad/(m/s²)] valem em AY_REF_G (0,05·G). resolucao_ms2 é a folga numérica do veredito (a
    bisseção roda bem abaixo dela). Veredito N/A: T, eixo_satura, Q e P ficam None e motivo diz por quê.
    limitacoes são os avisos de entrada do pneu limitada à faixa do .tir (EDR-056) em T.

    folga_outro_N e folga_outro_fracao (decisão 1.3 revista, EDR-064): só nas variantes acopladas com T. A folga em T do
    eixo que não satura (o de ay_sat None), nos eixos do carro: capacidade acoplada do eixo em T (_capacidades_acopladas,
    o pico do ramo ascendente) menos a força que ele faz no trim de T, que é a força exigida dele; é a mesma margem que a
    regra do NEUTRO e o Q usam. Em N e em fração da capacidade do eixo. None nas desacopladas (lá os dois ay_sat existem e
    a folga do outro eixo vira o Q e o veredito pela regra do analise_par) e quando não há T (N/A).
    """
    ay_t_ms2: float | None
    ay_sat_f: float | None
    ay_sat_r: float | None
    motivo_sat: str | None
    eixo_satura: str | None
    veredito: str
    cn_iso_q: float | None
    cn_estabilizante_q: float | None
    cn_p: float | None
    stability_index: float | None
    k_rad_por_ms2: float | None
    resolucao_ms2: float
    motivo: str | None
    limitacoes: tuple[str, ...] = ()
    folga_outro_N: float | None = None
    folga_outro_fracao: float | None = None


@dataclass(frozen=True)
class _Eixo:
    """Saturação de um eixo. sat: A_Y em que o eixo deixa de ter raiz (None se não satura); valido_ate: último A_Y
    com raiz (None se já inválido no início); motivo: por que não saturou (None quando saturou)."""
    sat: float | None
    valido_ate: float | None
    motivo: str | None


def _estado_eixo(caso: eq.CasoEquilibrio, eixo: str, ay_ms2: float, n_alfa: int) -> tuple[str, str | None]:
    """("ok" | "sat" | "invalido", motivo): o eixo tem raiz, falta raiz (satura) ou saiu do domínio (descolamento,
    toe que consome a faixa, pico na borda, tração acima do atrito)."""
    r = _raiz_eixo(caso, eixo, ay_ms2, n_alfa)
    if "alfa_ref" in r:
        return "ok", None
    return ("sat" if r["sem_raiz"] else "invalido"), r["motivo"]


def _transicao(pred, semente: float | None, ay_lo: float, ay_max: float, passo: float) -> tuple:
    """(estado, a, b) com pred(a) verdadeiro e pred(b) falso, ou estado "falha_inicial" (pred(ay_lo) falso) ou
    "nao_satura" (pred verdadeiro até ay_max).

    O intervalo inicial vem da semente (a saturação do analise_par) ± 2 passos e é validado; se não valer, varre a
    partir de ay_lo em passos de passo até a primeira falha. Com mais de uma transição, vale a primeira da varredura.
    """
    if not pred(ay_lo):
        return "falha_inicial", None, ay_lo
    if semente is not None:
        a, b = max(ay_lo, semente - 2.0 * passo), min(ay_max, semente + 2.0 * passo)
        if a < b and pred(a) and not pred(b):
            return "ok", a, b
    a = ay_lo
    while a < ay_max:
        b = min(a + passo, ay_max)
        if not pred(b):
            return "ok", a, b
        a = b
    return "nao_satura", ay_max, None


def _bissecta(pred, a: float, b: float, tol: float) -> tuple[float, float]:
    """Estreita [a, b] (pred(a) verdadeiro, pred(b) falso) até b − a <= tol."""
    while b - a > tol:
        meio = 0.5 * (a + b)
        if pred(meio):
            a = meio
        else:
            b = meio
    return a, b


def _g(ay_ms2: float) -> str:
    return eq._num(ay_ms2 / G, ".3f") + " g"


def _analisa_eixo(caso: eq.CasoEquilibrio, eixo: str, semente: float | None, ay_lo: float, ay_max: float,
                  passo: float, tol: float, n_alfa: int) -> _Eixo:
    """Saturação do eixo por bisseção sobre "tem raiz" (_raiz_eixo), o mesmo critério do trim e da capacidade."""
    cache: dict = {}

    def estado(ay: float) -> tuple[str, str | None]:
        if ay not in cache:
            cache[ay] = _estado_eixo(caso, eixo, ay, n_alfa)
        return cache[ay]

    def pred(ay: float) -> bool:
        return estado(ay)[0] == "ok"

    est, a, b = _transicao(pred, semente, ay_lo, ay_max, passo)
    if est == "falha_inicial":
        return _Eixo(None, None, f"{estado(ay_lo)[1]} em a_y = {_g(ay_lo)} (início da varredura)")
    if est == "nao_satura":
        return _Eixo(None, ay_max, f"eixo {eixo}: não satura até {_g(ay_max)}")
    a, b = _bissecta(pred, a, b, tol)
    tipo, motivo = estado(b)
    if tipo == "sat":
        return _Eixo(a, a, None)
    return _Eixo(None, a, f"{motivo}; último a_y válido = {_g(a)}")


def _veredito(ef: _Eixo, er: _Eixo, res: float) -> tuple[str, str | None]:
    """(veredito, motivo) pela mesma regra do analise_par (EDR-056), com a saturação de cada eixo por bisseção:
    os dois saturam: |S_r − S_f| <= res -> NEUTRO, senão o menor define PUSH (frente) ou LOOSE (traseira); só um
    satura: vale se o outro segue válido até S + res; senão N/A com o motivo do outro; nenhum satura: N/A com o motivo
    do eixo cuja parte válida acaba antes.

    Sobre a decisão 3 do plano ("folga do outro eixo em T <= força exigida por m/s² · res"): no caminho desacoplado
    as duas saturações existem, e |S_r − S_f| <= res é o equivalente exato do analise_par. A regra da folga coincide
    com ela até primeira ordem (folga ≈ (dF_exigida/dA_Y − dC/dA_Y)·|S_r − S_f|), mas dá NEUTRO a menos quando a
    capacidade do outro eixo cai com A_Y (carga transferida). Nas variantes acopladas (_limite_acoplado), onde o eixo
    que não satura não tem S, é a regra da folga que decide.
    """
    s_f, s_r = ef.sat, er.sat
    v_f = ef.valido_ate if ef.valido_ate is not None else -math.inf
    v_r = er.valido_ate if er.valido_ate is not None else -math.inf
    if s_f is not None and s_r is not None:
        if abs(s_r - s_f) <= res:
            return eq.NEUTRO, None
        return (eq.PUSH if s_r > s_f else eq.LOOSE), None
    if s_f is not None and v_r >= s_f + res:
        return eq.PUSH, None
    if s_r is not None and v_f >= s_r + res:
        return eq.LOOSE, None
    if s_f is not None:
        return eq.NA, er.motivo
    if s_r is not None:
        return eq.NA, ef.motivo
    return eq.NA, (ef.motivo if v_f <= v_r else er.motivo)


def _ponto_p(caso: eq.CasoEquilibrio, ay_ini: float, ay_max: float, passo: float, tol: float,
             n_alfa: int, caps_fn=None, fator_ay: float = 1.0) -> tuple[float | None, str | None]:
    """(cn_p, motivo): C_N (ISO) em P, o A_Y_P com m·A_P = Fy_f,max(A_P) + Fy_r,max(A_P) (ponto fixo por bisseção),
    com as capacidades de capacidade_eixo (Milliken p. 306: soma vetorial dos pontos de saturação, fora do trim).
    Procura a partir de ay_ini (em T a soma das capacidades já é >= m·A_Y) e para na primeira troca de sinal.
    Capacidade inválida (motivo) nunca entra: devolve (None, motivo). caps_fn (variantes acopladas) devolve
    ((Fy_f,max, Fy_r,max), None) ou (None, motivo) no lugar de capacidade_eixo; fator_ay (cos β nelas) multiplica m·A_Y."""
    cfg = caso.cfg
    W = cfg.mass_total * G

    def caps(ay: float) -> tuple:
        if caps_fn is not None:
            return caps_fn(ay)
        cf, cr = eq.capacidade_eixo(caso, "F", ay, n_alfa), eq.capacidade_eixo(caso, "R", ay, n_alfa)
        for e, c in (("F", cf), ("R", cr)):
            if c.fy_max_N is None or c.motivo is not None:
                return None, f"P: eixo {e}: {c.motivo} em a_y = {_g(ay)}"
        return (cf.fy_max_N, cr.fy_max_N), None

    def g(ay: float) -> tuple:
        v, motivo = caps(ay)
        return (None, motivo) if v is None else (v[0] + v[1] - fator_ay * cfg.mass_total * ay, None)

    def cn_em(ay: float) -> float:
        fy_f, fy_r = caps(ay)[0]
        return (cfg.cg_to_front * fy_f - cfg.cg_to_rear * fy_r) / (W * cfg.wheelbase)

    a = ay_ini
    ga, motivo = g(a)
    if ga is None:
        return None, motivo
    if ga <= 0.0:
        return cn_em(a), None
    while a < ay_max:
        b = min(a + passo, ay_max)
        gb, motivo = g(b)
        if gb is None:
            return None, motivo
        if gb <= 0.0:
            while b - a > tol:
                meio = 0.5 * (a + b)
                gm, motivo = g(meio)
                if gm is None:
                    return None, motivo
                if gm > 0.0:
                    a = meio
                else:
                    b = meio
            return cn_em(a), None
        a = b
    return None, f"P: a soma das capacidades não cruza m·A_Y até {_g(ay_max)}"


# ---------------------------------------------------------------------------
# Limite acoplado: T pelo trim, capacidade de cada eixo no T e saturação por eixo (decisão 3 do plano)
# ---------------------------------------------------------------------------

_MSG_ACOPLADO = "acoplado: além de T não há trim"
_PASSO_PICO_RAD = math.radians(0.25)   # passo da marcha até o pico da Fy do eixo
_MAX_PASSOS_PICO = 240


def _pico(f, x0: float, sentido: float) -> tuple[float | None, str | None]:
    """(máximo de f, None) ao longo de x0 + sentido·s (s >= 0), ou (None, motivo). Marcha em passos de 0,25° até f deixar de
    crescer e refina o pico por seção áurea. Sair da faixa do pneu antes do pico é "pico na borda"; um f sem pico, idem."""
    xs, fs = [x0], [f(x0)]
    x = x0
    for k in range(1, _MAX_PASSOS_PICO + 1):
        x = x0 + sentido * k * _PASSO_PICO_RAD
        try:
            v = f(x)
        except _Falha as e:
            return None, f"pico na borda da faixa do pneu ({e.motivo})"
        if v <= fs[-1]:
            break
        xs.append(x)
        fs.append(v)
    else:
        return None, "pico na borda da faixa do pneu (a Fy do eixo não deixa de crescer)"
    a = xs[-2] if len(xs) >= 2 else x0 - sentido * _PASSO_PICO_RAD
    _, gm = _golden_min(lambda y: -f(y), min(a, x), max(a, x), 20)
    return max(max(fs), -gm), None


def _capacidades_acopladas(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, beta_rad: float,
                           delta_rad: float) -> tuple:
    """((Fy_f,max, Fy_r,max), None) ou (None, motivo): a Fy de cada eixo, nos eixos do carro, no máximo do ramo ascendente
    (δ para a frente, β para a traseira, o outro ângulo e A_Y fixos), na física da variante. É a capacidade do eixo que a
    folga em T e o ponto P usam nas variantes acopladas, no lugar de equilibrio.capacidade_eixo (que é a da planilha)."""
    try:
        pf, mf = _pico(lambda d: _avalia(caso, hip, beta_rad, d, ay_ms2).f_frente, delta_rad, +1.0)
        pr, mr = _pico(lambda b: _avalia(caso, hip, b, delta_rad, ay_ms2).f_traseira, beta_rad, -1.0)
    except _Falha as e:
        return None, e.motivo
    for eixo, v, mo in (("F", pf, mf), ("R", pr, mr)):
        if v is None:
            return None, f"eixo {eixo}: {mo}"
    return (pf, pr), None


def _k_e_si(caso: eq.CasoEquilibrio, hip: Hipoteses, n_alfa: int, motivo_sat: str | None) -> tuple:
    """(K, stability index, motivo_sat) em AY_REF_G; o que não existir vira None e o motivo entra em motivo_sat."""
    try:
        k = k_trim(caso, hip, AY_REF_G * G, n_alfa)
    except _SemNumero as e:
        k = None
        motivo_sat = "; ".join(x for x in (motivo_sat, f"K indisponível: {e}") if x)
    try:
        si = stability_index(caso, hip, AY_REF_G * G, n_alfa)
    except _SemNumero as e:
        si = None
        motivo_sat = "; ".join(x for x in (motivo_sat, f"stability index indisponível: {e}") if x)
    return k, si, motivo_sat


def _limite_acoplado(caso: eq.CasoEquilibrio, hip: Hipoteses, resolucao_ms2: float, ay_max_g: float,
                     n_alfa: int) -> Limite:
    """Limite de uma variante acoplada (decisão 3 do plano).

    T: bisseção em A_Y sobre a existência de trim (o Newton), com o intervalo inicial da saturação do analise_par. Além de
    T não existe trim, então só o eixo que satura tem ay_sat = T; o outro sai None com motivo_sat = "acoplado: além de T
    não há trim", e a folga dele em T vai em folga_outro_N e folga_outro_fracao (decisão 1.3 revista). O eixo que satura
    é o de menor folga em T (capacidade acoplada menos a força que ele faz no trim), e o outro eixo dá a folga de Q. NEUTRO quando essa folga é <= (força do eixo por m/s²) · resolucao_ms2, o equivalente em
    força ao |S_r − S_f| <= res do analise_par. N/A (sem T) quando o trim acima de T falha por um motivo de domínio
    (descolamento, faixa do pneu, tração acima do atrito). A falha do próprio Newton (resíduo que não diminui, jacobiano
    singular) colada em T é a dobra do trim, onde o eixo que satura não tem raiz: vale como saturação, e as folgas dizem qual.
    O que decide o domínio é Trim.causa ("dominio" ou "dobra"), não o texto do motivo.

    Conferência de margem: o eixo declarado saturado tem de estar de fato no pico em T, isto é, margem[eixo] <= (força do
    eixo por m/s²) · resolucao_ms2. Senão a dobra do Newton não é a saturação dele e o resultado é N/A com motivo.

    Precisão de T neste caminho: T é a última raiz da bisseção sobre "existe trim" e a dobra do Newton pode cair até
    ~resolucao_ms2 antes do pico do eixo (medido no TC-ESC-002: margem de 0,46 N na linha 3, ≈ 0,004 m/s²). Por isso a
    precisão declarada de T acoplado é da ordem de resolucao_ms2, e não da tolerância da bisseção (resolucao_ms2·1e-4)."""
    cfg = caso.cfg
    W, L = cfg.mass_total * G, cfg.wheelbase
    ay_max = ay_max_g * G
    ay_lo = min(AY_REF_G * G, 0.1 * ay_max)
    passo = _PASSO_VARREDURA_G * G
    tol = resolucao_ms2 * _FRACAO_TOL

    par = eq.analise_par(caso, ay_max_g=ay_max_g)
    conhecidas = [s for s in (par.ay_sat_f, par.ay_sat_r) if s is not None]
    cache: dict = {}

    def tr(ay: float) -> Trim:
        if ay not in cache:
            cache[ay] = trim(caso, hip, ay, n_alfa)
        return cache[ay]

    def pred(ay: float) -> bool:
        return tr(ay).convergiu

    veredito, motivo = eq.NA, None
    ay_t = eixo = ay_sat_f = ay_sat_r = motivo_sat = cn_iso_q = cn_est_q = cn_p = folga_n = folga_frac = None
    limitacoes: tuple = ()
    est, a, b = _transicao(pred, min(conhecidas) if conhecidas else None, ay_lo, ay_max, passo)
    if est == "falha_inicial":
        motivo = f"{tr(ay_lo).motivo} em a_y = {_g(ay_lo)} (início da varredura)"
    elif est == "nao_satura":
        motivo = f"o trim existe até {_g(ay_max)}: nenhum eixo satura na faixa"
    else:
        a, b = _bissecta(pred, a, b, tol)
        t_alto = tr(b)
        if t_alto.causa == CAUSA_DOMINIO:
            motivo = f"{t_alto.motivo}; último a_y válido = {_g(a)}"
        else:
            t_t = tr(a)
            caps, motivo_cap = _capacidades_acopladas(caso, hip, a, t_t.beta_rad, t_t.delta_rad)
            if caps is None:
                motivo = f"capacidade dos eixos em T: {motivo_cap}"
            else:
                aval = _avalia(caso, hip, t_t.beta_rad, t_t.delta_rad, a)
                forca = {"F": aval.f_frente, "R": aval.f_traseira}
                margem = {"F": max(0.0, caps[0] - forca["F"]), "R": max(0.0, caps[1] - forca["R"])}
                eixo = "F" if margem["F"] <= margem["R"] else "R"
                outro = "R" if eixo == "F" else "F"
                tol_eixo = {e: (forca[e] / a) * resolucao_ms2 for e in ("F", "R")}   # força por m/s² · resolucao_ms2
                neutro = margem[outro] <= tol_eixo[outro]
                if margem[eixo] > tol_eixo[eixo]:
                    # O trim deixa de existir acima de T, mas o eixo que seria o limitante ainda tem folga: a dobra do
                    # Newton não é a saturação dele, e declará-la assim daria um T que não é o do eixo.
                    motivo = (f"o trim deixa de existir acima de T = {_g(a)}, mas nenhum eixo está no pico (menor folga: "
                              f"eixo {eixo}, {margem[eixo]:.3f} N > {tol_eixo[eixo]:.3f} N = força por m/s² do eixo · "
                              f"{resolucao_ms2:g} m/s²)")
                    eixo = None
                elif not neutro and t_alto.eixo_sem_raiz in ("F", "R") and t_alto.eixo_sem_raiz != eixo:
                    eixo = None
                    motivo = (f"o trim e as folgas discordam (o trim acima de T perde o eixo {t_alto.eixo_sem_raiz}; "
                              f"a menor folga em T é a do outro eixo)")
                else:
                    ay_t = a
                    veredito = eq.NEUTRO if neutro else (eq.PUSH if eixo == "F" else eq.LOOSE)
                    ay_sat_f, ay_sat_r = (a, None) if eixo == "F" else (None, a)
                    motivo_sat = _MSG_ACOPLADO
                    folga = margem[outro]
                    folga_n, folga_frac = folga, folga / caps[0 if outro == "F" else 1]
                    cn_est_q = folga * cfg.cg_to_rear / (W * L) if outro == "R" else -folga * cfg.cg_to_front / (W * L)
                    cn_iso_q = _estabilizante(cn_est_q)
                    # a_y = A·cos β no caminho acoplado com a rotação (adendo §2.5); sem ela, a_y = A
                    fator_ay = math.cos(t_t.beta_rad) if hip.rotacao_beta else 1.0
                    cn_p, motivo_p = _ponto_p(
                        caso, a, ay_max, passo, tol, n_alfa,
                        caps_fn=lambda ay: _capacidades_acopladas(caso, hip, ay, t_t.beta_rad, t_t.delta_rad),
                        fator_ay=fator_ay)
                    if cn_p is None:
                        motivo_sat = "; ".join(x for x in (motivo_sat, motivo_p) if x)
                    limitacoes = aval.limites
    k, si, motivo_sat = _k_e_si(caso, hip, n_alfa, motivo_sat)
    return Limite(ay_t_ms2=ay_t, ay_sat_f=ay_sat_f, ay_sat_r=ay_sat_r, motivo_sat=motivo_sat, eixo_satura=eixo,
                  veredito=veredito, cn_iso_q=cn_iso_q, cn_estabilizante_q=cn_est_q, cn_p=cn_p,
                  stability_index=si, k_rad_por_ms2=k, resolucao_ms2=float(resolucao_ms2),
                  motivo=motivo, limitacoes=limitacoes, folga_outro_N=folga_n, folga_outro_fracao=folga_frac)


def limite(caso: eq.CasoEquilibrio, hip: Hipoteses, resolucao_ms2: float = 0.01, ay_max_g: float = 2.0,
           n_alfa: int = 401) -> Limite:
    """T, saturação por eixo, veredito, Q, P, K e stability index em raio fixo (curva à esquerda; a direita, com
    equilibrio.espelhar). Variantes acopladas seguem _limite_acoplado (T pelo Newton, saturação por eixo da decisão 3
    do plano); o método abaixo é o das desacopladas. Sem raio_m lança ValueError (decisão 2 do plano). O campo `sentido` de Hipoteses não age aqui: os dois sentidos são dois
    chamados (a escada, Task 6, chama o limite() do caso e o do espelhado).

    Método:
    1. Saturação por eixo (desacoplado): bisseção em A_Y sobre "o eixo tem raiz" (_raiz_eixo, o ramo ascendente da soma
       do eixo, o critério de capacidade_eixo). O intervalo inicial vem da saturação do analise_par (± 2 passos) e é
       validado (raiz na ponta baixa, sem raiz na alta); se não valer, varre de 0,05 g em 0,05 g. A tolerância da
       bisseção é resolucao_ms2 · 1e-4.
    2. Veredito (_veredito): a regra do analise_par (EDR-056) com `resolucao_ms2` no lugar da resolução por refinamento
       de grade. N/A quando o eixo que não satura deixa de ser válido (descolamento, toe, pico na borda, tração acima do
       atrito) antes de S + resolucao_ms2: não há número de T, e o motivo é o do eixo (de capacidade_eixo).
    3. T: bisseção em A_Y sobre trim(...).convergiu, com o intervalo inicial de analise_par.ay_lim, validado. T é o
       maior A_Y com trim dentro da tolerância e deve coincidir com min(S_f, S_r) (senão N/A).
    4. Q: folga do outro eixo em T (capacidade_eixo − força exigida), vezes o braço até o CG, sobre W·L, igual ao c_n do
       analise_par. P: _ponto_p. K e stability index em AY_REF_G (None se o trim não existir em volta).

    Comparação com analise_par (spec §5.1): a física por roda é a mesma, mas o analise_par usa n_alfa = 25 e interpola
    a saturação entre linhas de 0,05 g, e o limite usa n_alfa = 401 por padrão. Medido no caso do TC-MMM-006, a
    diferença entre as duas saturações é de ~3e-3 m/s² e vem da grade de α (a de 25 pontos subestima o pico), cem vezes
    a resolucao_ms2 que o analise_par calcula. Com a mesma grade (n_alfa) nos dois lados e passo de 0,01 g no
    analise_par, a diferença fica dentro da resolucao_ms2 dele; com n_alfa = 25 nos dois e passo de 0,05 g, ela é de
    1,3 a 1,7 vezes a resolucao_ms2 (a interpolação em A_Y). Quem compara com o analise_par deve usar a mesma grade.
    """
    _exige_raio(caso)
    if not (isinstance(resolucao_ms2, (int, float)) and math.isfinite(resolucao_ms2) and resolucao_ms2 > 0.0):
        raise ValueError(f"resolucao_ms2 deve ser > 0 e finito; recebido {resolucao_ms2!r}.")
    if not (isinstance(ay_max_g, (int, float)) and math.isfinite(ay_max_g) and ay_max_g > 0.0):
        raise ValueError(f"ay_max_g deve ser > 0 e finito; recebido {ay_max_g!r}.")
    if _e_acoplada(hip):
        return _limite_acoplado(caso, hip, resolucao_ms2, ay_max_g, n_alfa)
    cfg = caso.cfg
    W, L = cfg.mass_total * G, cfg.wheelbase
    ay_max = ay_max_g * G
    ay_lo = min(AY_REF_G * G, 0.1 * ay_max)
    passo = _PASSO_VARREDURA_G * G
    tol = resolucao_ms2 * _FRACAO_TOL

    par = eq.analise_par(caso, ay_max_g=ay_max_g)
    ef = _analisa_eixo(caso, "F", par.ay_sat_f, ay_lo, ay_max, passo, tol, n_alfa)
    er = _analisa_eixo(caso, "R", par.ay_sat_r, ay_lo, ay_max, passo, tol, n_alfa)
    veredito, motivo = _veredito(ef, er, resolucao_ms2)
    motivo_sat = "; ".join(e.motivo for e in (ef, er) if e.motivo is not None) or None

    ay_t = eixo = cn_iso_q = cn_est_q = cn_p = None
    limitacoes: tuple = ()
    if veredito != eq.NA:
        conhecidas = [e.sat for e in (ef, er) if e.sat is not None]
        cache: dict = {}

        def tr(ay: float) -> Trim:
            if ay not in cache:
                cache[ay] = trim(caso, hip, ay, n_alfa)
            return cache[ay]

        est, a, b = _transicao(lambda ay: tr(ay).convergiu, min(conhecidas), ay_lo, ay_max, passo)
        if est == "ok":
            ay_t = _bissecta(lambda ay: tr(ay).convergiu, a, b, tol)[0]
        if ay_t is None or abs(ay_t - min(conhecidas)) > resolucao_ms2:
            veredito = eq.NA
            motivo = (f"o trim e a saturação por eixo discordam (T = {'-' if ay_t is None else _g(ay_t)}, "
                      f"saturação = {_g(min(conhecidas))})")
            ay_t = None
    if veredito != eq.NA:
        if veredito == eq.PUSH:
            eixo = "F"
        elif veredito == eq.LOOSE:
            eixo = "R"
        else:
            eixo = "F" if (ef.sat <= er.sat) else "R"
        outro = "R" if eixo == "F" else "F"
        cap_o = eq.capacidade_eixo(caso, outro, ay_t, n_alfa)
        if cap_o.fy_max_N is not None and cap_o.motivo is None:
            exigida = eq.forca_exigida(caso, ay_t)[0 if outro == "F" else 1]
            folga = cap_o.fy_max_N - exigida
            cn_est_q = folga * cfg.cg_to_rear / (W * L) if outro == "R" else -folga * cfg.cg_to_front / (W * L)
            cn_iso_q = _estabilizante(cn_est_q)
        cn_p, motivo_p = _ponto_p(caso, ay_t, ay_max, passo, tol, n_alfa)
        if cn_p is None:
            motivo_sat = "; ".join(x for x in (motivo_sat, motivo_p) if x)
        avisos = []
        for e in ("F", "R"):
            for texto in eq.capacidade_eixo(caso, e, ay_t, n_alfa).limites:
                if texto not in avisos:
                    avisos.append(texto)
        limitacoes = tuple(avisos)

    k, si, motivo_sat = _k_e_si(caso, hip, n_alfa, motivo_sat)
    return Limite(ay_t_ms2=ay_t, ay_sat_f=ef.sat, ay_sat_r=er.sat, motivo_sat=motivo_sat, eixo_satura=eixo,
                  veredito=veredito, cn_iso_q=cn_iso_q, cn_estabilizante_q=cn_est_q, cn_p=cn_p,
                  stability_index=si, k_rad_por_ms2=k, resolucao_ms2=float(resolucao_ms2),
                  motivo=motivo, limitacoes=limitacoes)


# ---------------------------------------------------------------------------
# Sensibilidades por unidade (adendo §4.3; decisão 4 do plano troca o jacking pela altura do CG)
# ---------------------------------------------------------------------------

UNIDADES = {"ganho_camber_F": "por 0,1 °/°", "ganho_camber_R": "por 0,1 °/°",
            "rc_F": "por 10 mm", "rc_R": "por 10 mm",
            "kphi_F": "por 1 kN·m/rad", "kphi_R": "por 1 kN·m/rad",
            "h_cg": "por 10 mm", "cg_lateral": "por 10 mm", "h_cp": "por 10 mm"}

# Passo de cada parâmetro na unidade SI do campo: ganho_camber em rad/rad (nas duas rodas do eixo), cfg.roll_center_front
# e _rear [m], cfg.roll_stiffness_front e _rear [N·m/rad], cfg.cg_height [m], cg_lateral_m [m] e h_cp_m [m].
_PASSOS = {"ganho_camber_F": 0.1, "ganho_camber_R": 0.1, "rc_F": 0.010, "rc_R": 0.010,
           "kphi_F": 1000.0, "kphi_R": 1000.0, "h_cg": 0.010, "cg_lateral": 0.010, "h_cp": 0.010}

_CAMPO_CFG = {"rc_F": "roll_center_front", "rc_R": "roll_center_rear",
              "kphi_F": "roll_stiffness_front", "kphi_R": "roll_stiffness_rear", "h_cg": "cg_height"}

assert set(UNIDADES) == set(_PASSOS)


def _desloca(caso: eq.CasoEquilibrio, hip: Hipoteses, parametro: str, d: float) -> tuple:
    """(caso, hip) com o parâmetro deslocado de d (unidade SI do campo), sem alterar os objetos recebidos."""
    if parametro.startswith("ganho_camber_"):
        ganho = dict(caso.ganho_camber)
        for c in eq.RODAS_DO_EIXO[parametro[-1]]:
            ganho[c] += d
        return replace(caso, ganho_camber=ganho), hip
    if parametro in _CAMPO_CFG:
        campo = _CAMPO_CFG[parametro]
        return replace(caso, cfg=replace(caso.cfg, **{campo: getattr(caso.cfg, campo) + d})), hip
    if parametro == "cg_lateral":
        return replace(caso, cg_lateral_m=caso.cg_lateral_m + d), hip
    return caso, replace(hip, h_cp_m=(hip.h_cp_m if hip.h_cp_m is not None else 0.0) + d)   # h_cp


def sensibilidade(caso: eq.CasoEquilibrio, hip: Hipoteses, parametro: str, ay_max_g: float = 2.0) -> dict:
    """Variação de T, de C_N estabilizante em Q e de K por unidade do parâmetro, por diferença central de ± um passo
    (a unidade é o passo: d = (valor(+passo) − valor(−passo))/2), mais o veredito de cada lado. Nenhuma faixa é afirmada.

    parametro ∈ UNIDADES (passos em _PASSOS, na unidade SI do campo; `unidade` devolve o texto de UNIDADES). `cg_lateral`
    parte do valor do caso. `h_cp` parte de hip.h_cp_m (None conta como 0) e exige transf_long="regime", senão o
    resultado é vazio com motivo "h_cp só com transf_long=regime". Um valor None (T, Q ou K de um dos lados sem número)
    deixa a derivada correspondente None, com o motivo de cada lado. O caso e as hipóteses recebidos não são alterados.
    A sensibilidade de h_cp é em torno de h_cp = 0 quando hip.h_cp_m é None (a parcela D·h_cp/L sai da derivada de uma
    altura que o projeto ainda não mediu). ay_max_g é a faixa de busca da saturação do limite (rotulada; padrão 2,0 g).
    Chaves: parametro, unidade, d_ay_t [m/s²], d_cn_estabilizante_q, d_k [rad/(m/s²)], veredito_menos, veredito_mais, motivo.
    """
    if parametro not in UNIDADES:
        raise ValueError(f"parametro deve ser um de {tuple(UNIDADES)}; recebido {parametro!r}.")
    _exige_raio(caso)
    res = {"parametro": parametro, "unidade": UNIDADES[parametro], "d_ay_t": None, "d_cn_estabilizante_q": None,
           "d_k": None, "veredito_menos": None, "veredito_mais": None, "motivo": None}
    if parametro == "h_cp" and hip.transf_long != "regime":
        res["motivo"] = "h_cp só com transf_long=regime"
        return res
    passo = _PASSOS[parametro]
    lados = {}
    for nome, sinal in (("menos", -1.0), ("mais", 1.0)):
        caso_x, hip_x = _desloca(caso, hip, parametro, sinal * passo)
        lados[nome] = limite(caso_x, hip_x, ay_max_g=ay_max_g)
    res["veredito_menos"], res["veredito_mais"] = lados["menos"].veredito, lados["mais"].veredito
    for chave, campo in (("d_ay_t", "ay_t_ms2"), ("d_cn_estabilizante_q", "cn_estabilizante_q"),
                         ("d_k", "k_rad_por_ms2")):
        v_menos, v_mais = getattr(lados["menos"], campo), getattr(lados["mais"], campo)
        if v_menos is not None and v_mais is not None:
            res[chave] = (v_mais - v_menos) / 2.0
    faltas = [f"lado {nome}: {lados[nome].motivo or lados[nome].motivo_sat}" for nome in ("menos", "mais")
              if lados[nome].ay_t_ms2 is None or lados[nome].cn_estabilizante_q is None
              or lados[nome].k_rad_por_ms2 is None]
    res["motivo"] = "; ".join(faltas) or None
    return res
