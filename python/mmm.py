"""
MMM em raio fixo (Milliken Moment Method) e escada de hipóteses: física (incremento 6, Task 2).

Fixado A_Y e o raio R do skidpad, ficam determinados V = √(A_Y·R), a downforce, as cargas, o camber e as
forças exigidas por eixo (equilibrio.forca_exigida). Este módulo acha o trim (β, δ) que as entrega.
Nesta etapa só existe o caminho desacoplado (variantes da planilha): cada eixo depende de uma incógnita só,
e o α_ref de cada eixo sai de uma raiz 1-D (Brent) no ramo ascendente da soma do eixo, o mesmo critério de
equilibrio.capacidade_eixo. As variantes acopladas (alfa cinemático, cos δ do trim, balanço de Fx, PAC2002
combinado, diferencial travado, transferência longitudinal) lançam NotImplementedError("Task 4").

Convenções (CLAUDE.md): SI, eixos ISO 8855 (X frente, Y esquerda, Z cima), curva à esquerda (a direita sai de
equilibrio.espelhar), α < 0 dá Fy > 0 à esquerda. O módulo não conhece a origem dos dados e não sabe se a
geometria é sintética: quem o chama carrega esse rótulo.

Referência: Milliken, Race Car Vehicle Dynamics, p. 306-307 (T, Q, P; α_F = β + a/R − δ, α_R = β − b/R);
adendo da especificação do incremento 6 (docs/superpowers/specs/2026-10-27-inc6-mmm-escada-design.md), §2 e §4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from typing import Literal

import equilibrio as eq
from equilibrio import CANTOS, G
from tire_model import wheel_forces

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
    """
    alfa: Literal["planilha", "cinematico"] = "planilha"
    cos_delta: Literal["ref", "trim"] = "ref"
    sentido: Literal["entrada", "dois"] = "entrada"
    fx_exigido: Literal["edr057", "balanco"] = "edr057"
    tracao: Literal["elipse", "pac2002"] = "elipse"
    diferencial: Literal["aberto", "travado"] = "aberto"
    transf_long: Literal["nao", "regime"] = "nao"
    h_cp_m: float | None = None

    def __post_init__(self):
        for campo, validos in _VALORES.items():
            v = getattr(self, campo)
            if v not in validos:
                raise ValueError(f"Hipoteses.{campo} deve ser um de {validos}; recebido {v!r}.")
        h = self.h_cp_m
        if h is not None and not (isinstance(h, (int, float)) and math.isfinite(h)):
            raise ValueError(f"Hipoteses.h_cp_m exige número finito ou None; recebido {h!r}.")

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

assert set(VARIANTES) == {f.name for f in fields(Hipoteses)} - {"h_cp_m"}

# Campos cuja variante Python o trim ainda não resolve (acoplada: Task 4). O "sentido" não é do trim.
_ACOPLADOS = ("alfa", "cos_delta", "fx_exigido", "tracao", "diferencial", "transf_long")


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
    variantes sem κ por roda. residuo_N = |ΣFy − m·A_Y|. eixo_sem_raiz é "F", "R" ou "F+R" quando faltou raiz no
    ramo ascendente, e None nos demais motivos (descolamento, toe, pico na borda, tração acima do atrito).
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


def _falha(ay_ms2: float, motivo: str, eixo_sem_raiz: str | None = None) -> Trim:
    return Trim(ay_ms2, None, None, None, None, None, None, None, False, None, motivo, eixo_sem_raiz)


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
    ValueError (decisão 2 do plano). Variante acoplada: NotImplementedError("Task 4").
    """
    R = _exige_raio(caso)
    pedidos = [c for c in _ACOPLADOS if getattr(hip, c) != VARIANTES[c]["planilha"]]
    if pedidos:
        raise NotImplementedError("Task 4")
    if not ay_ms2 > 0.0:
        raise ValueError(f"ay_ms2 deve ser > 0; recebido {ay_ms2!r}.")
    cfg = caso.cfg
    raiz = {e: _raiz_eixo(caso, e, ay_ms2, n_alfa) for e in ("F", "R")}
    ruins = [e for e in ("F", "R") if "motivo" in raiz[e]]
    if ruins:
        sem = [e for e in ruins if raiz[e]["sem_raiz"]]
        return _falha(ay_ms2, "; ".join(raiz[e]["motivo"] for e in ruins), "+".join(sem) if sem else None)
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
        return _falha(ay_ms2, f"Brent não convergiu: |ΣFy − m·A_Y| = {residuo:.3e} N")
    return Trim(ay_ms2, beta, delta, alfa, fz, fy, fx, None, True, residuo, None)


# ---------------------------------------------------------------------------
# C_N (adendo §2.2)
# ---------------------------------------------------------------------------

def momento_n(trim_: Trim, caso: eq.CasoEquilibrio) -> float:
    """N = Σ(x_i·Fy_i − y_i·Fx_i) [N·m] no ISO 8855, sem o Mz (hipótese 14)."""
    if not trim_.convergiu:
        raise ValueError("momento_n exige um trim que convergiu.")
    pos = posicoes(caso)
    return sum(pos[c][0] * trim_.fy[c] - pos[c][1] * trim_.fx[c] for c in CANTOS)


def cn(trim_: Trim, caso: eq.CasoEquilibrio) -> tuple[float, float]:
    """(cn_iso, cn_estabilizante) com C_N = N/(W·L), W = m·G (Milliken, cap. 8).

    cn_iso tem o sinal do ISO (sobra da traseira em curva à esquerda dá N < 0). cn_estabilizante = −cn_iso numa
    curva à esquerda, a grandeza da planilha (positivo = push). Nenhum código troca o sinal fora desta função.
    """
    cfg = caso.cfg
    cn_iso = momento_n(trim_, caso) / (cfg.mass_total * G * cfg.wheelbase)
    return cn_iso, -cn_iso
