"""
MMM em raio fixo (Milliken Moment Method) e escada de hipóteses: física (incremento 6, Tasks 2 e 3).

Fixado A_Y e o raio R do skidpad, ficam determinados V = √(A_Y·R), a downforce, as cargas, o camber e as
forças exigidas por eixo (equilibrio.forca_exigida). Este módulo acha o trim (β, δ) que as entrega.
Nesta etapa só existe o caminho desacoplado (variantes da planilha): cada eixo depende de uma incógnita só,
e o α_ref de cada eixo sai de uma raiz 1-D (Brent) no ramo ascendente da soma do eixo, o mesmo critério de
equilibrio.capacidade_eixo. As variantes acopladas (alfa cinemático, cos δ do trim, balanço de Fx, PAC2002
combinado, diferencial travado, transferência longitudinal) lançam NotImplementedError("Task 4").
A Task 3 acrescenta o limite (T, saturação por eixo, veredito, Q e P), o gradiente K e o stability index.

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


def _checa_desacoplada(hip: Hipoteses) -> None:
    """NotImplementedError("Task 4") se alguma hipótese acoplada estiver na variante Python."""
    if any(getattr(hip, c) != VARIANTES[c]["planilha"] for c in _ACOPLADOS):
        raise NotImplementedError("Task 4")


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
    _checa_desacoplada(hip)
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
    return _momento(caso, trim_.fy, trim_.fx)


def _momento(caso: eq.CasoEquilibrio, fy: dict, fx: dict) -> float:
    """N = Σ(x_i·Fy_i − y_i·Fx_i) [N·m] a partir das forças por roda."""
    pos = posicoes(caso)
    return sum(pos[c][0] * fy[c] - pos[c][1] * fx[c] for c in CANTOS)


def cn(trim_: Trim, caso: eq.CasoEquilibrio) -> tuple[float, float]:
    """(cn_iso, cn_estabilizante) com C_N = N/(W·L), W = m·G (Milliken, cap. 8).

    cn_iso tem o sinal do ISO (sobra da traseira em curva à esquerda dá N < 0). cn_estabilizante = −cn_iso numa
    curva à esquerda, a grandeza da planilha (positivo = push). Nenhum código troca o sinal fora desta função.
    """
    cfg = caso.cfg
    cn_iso = momento_n(trim_, caso) / (cfg.mass_total * G * cfg.wheelbase)
    return cn_iso, -cn_iso


# ---------------------------------------------------------------------------
# Trim lateral em (β, δ) fixos (base do stability index; a Task 5 publica este solver como `ponto`)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _PontoLateral:
    """Resultado de _trim_lateral. ay_ms2 e cn_iso são None quando não há raiz (motivo diz por quê).
    n_raizes conta as trocas de sinal de ΣFy − m·A_Y na varredura (aero forte pode dar mais de uma)."""
    ay_ms2: float | None
    cn_iso: float | None
    n_raizes: int
    motivo: str | None


def _balanco_lateral(caso: eq.CasoEquilibrio, hip: Hipoteses, beta_rad: float, delta_rad: float,
                     ay_ms2: float) -> tuple:
    """(ΣFy − m·A_Y [N], (fy, fx), None) com (β, δ) fixos e as cargas de A_Y, ou (None, None, motivo) se o ponto
    sai do domínio (descolamento ou tração acima do atrito). Mesma física do trim (Fz e γ limitados à faixa,
    elipse da traseira, cos δ_ref na frente); o α de cada roda vem de alfa_rodas, e não de uma raiz por eixo."""
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
        f_pneu = wheel_forces(caso.ds, c, fz_u[c], alfa[c], gam_u[c], 0.0)[1]
        if not frente and fatores is not None:
            f_pneu *= fatores[c]
        fy[c] = f_pneu * (cos_ref if frente else 1.0)
        fx[c] = 0.0 if frente else fx_roda
    return sum(fy.values()) - cfg.mass_total * ay_ms2, (fy, fx), None


def _trim_lateral(caso: eq.CasoEquilibrio, hip: Hipoteses, beta_rad: float, delta_rad: float,
                  ay_ref_ms2: float | None = None, ay_max_ms2: float = 3.0 * G,
                  passo_ms2: float = 0.02 * G) -> _PontoLateral:
    """A_Y em que ΣFy(A_Y; β, δ) = m·A_Y, com C_N (ISO) nesse A_Y.

    Varre A_Y em passos de passo_ms2 a partir de 0 até ay_max_ms2 ou até o primeiro descolamento; cada troca de sinal
    de ΣFy − m·A_Y é uma raiz (Brent dentro do intervalo). Com ay_ref_ms2, devolve a raiz mais próxima dele; sem,
    a menor. Sem raiz: ay_ms2 e cn_iso None, com motivo.
    """
    _exige_raio(caso)
    _checa_desacoplada(hip)
    n = math.floor(ay_max_ms2 / passo_ms2 + 1e-9)
    grade, motivo_fim = [], None
    for k in range(n + 1):
        ay = k * passo_ms2
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
        return _PontoLateral(None, None, 0, f"sem raiz de ΣFy = m·A_Y em [0, {ate} g]"
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
    return _PontoLateral(ay_raiz, _momento(caso, fy, fx) / (cfg.mass_total * G * cfg.wheelbase),
                         len(intervalos), None)


# ---------------------------------------------------------------------------
# K e stability index (adendo §2.4)
# ---------------------------------------------------------------------------

AY_REF_G = 0.05          # a_y [g] em que o limite() avalia K e o stability index (regime linear baixo)
_H_K_G = 0.01            # passo da diferença central de K [g]
_H_BETA_RAD = 1e-4       # passo em β do stability index [rad]


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
            raise ValueError(f"k_trim: sem trim em a_y = {eq._num(t.ay_ms2 / G, '.3f')} g ({t.motivo})")
    return (t_mais.delta_rad - t_menos.delta_rad) / (2.0 * h)


def stability_index(caso: eq.CasoEquilibrio, hip: Hipoteses, ay_ms2: float, n_alfa: int = 401,
                    h_beta_rad: float = _H_BETA_RAD) -> float:
    """Stability index [1/(m/s²)]: dC_N/dA_Y numa linha de δ constante, no trim de ay_ms2 (Milliken cap. 5, p. 204).

    No trim (β*, δ*) daquele A_Y, β* ± h com δ* fixo; o A_Y de cada lado vem do trim lateral (ΣFy = m·A_Y, Brent,
    raiz mais próxima de ay_ms2) e SI = ΔC_N/ΔA_Y. O C_N é o cn_estabilizante (positivo = push), de modo que
    SI > 0 é um carro estável (subesterço) e SI < 0 instável. Lança ValueError se não houver trim em ay_ms2 ou raiz
    lateral num dos lados.
    """
    t = trim(caso, hip, ay_ms2, n_alfa)
    if not t.convergiu:
        raise ValueError(f"stability_index: sem trim em a_y = {eq._num(ay_ms2 / G, '.3f')} g ({t.motivo})")
    mais = _trim_lateral(caso, hip, t.beta_rad + h_beta_rad, t.delta_rad, ay_ref_ms2=ay_ms2)
    menos = _trim_lateral(caso, hip, t.beta_rad - h_beta_rad, t.delta_rad, ay_ref_ms2=ay_ms2)
    for lado in (mais, menos):
        if lado.ay_ms2 is None:
            raise ValueError(f"stability_index: {lado.motivo}")
    d_ay = mais.ay_ms2 - menos.ay_ms2
    if d_ay == 0.0:
        raise ValueError("stability_index: A_Y não varia com β (ΔA_Y = 0).")
    return -(mais.cn_iso - menos.cn_iso) / d_ay


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
    capacidade do outro eixo cai com A_Y (carga transferida). Nas variantes acopladas (Task 4), onde o eixo que não
    satura não tem S, é a regra da folga que decide.
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
             n_alfa: int) -> tuple[float | None, str | None]:
    """(cn_p, motivo): C_N (ISO) em P, o A_Y_P com m·A_P = Fy_f,max(A_P) + Fy_r,max(A_P) (ponto fixo por bisseção),
    com as capacidades de capacidade_eixo (Milliken p. 306: soma vetorial dos pontos de saturação, fora do trim).
    Procura a partir de ay_ini (em T a soma das capacidades já é >= m·A_Y) e para na primeira troca de sinal.
    Capacidade inválida (motivo) nunca entra: devolve (None, motivo)."""
    cfg = caso.cfg
    W = cfg.mass_total * G

    def caps(ay: float) -> tuple:
        cf, cr = eq.capacidade_eixo(caso, "F", ay, n_alfa), eq.capacidade_eixo(caso, "R", ay, n_alfa)
        for e, c in (("F", cf), ("R", cr)):
            if c.fy_max_N is None or c.motivo is not None:
                return None, f"P: eixo {e}: {c.motivo} em a_y = {_g(ay)}"
        return (cf.fy_max_N, cr.fy_max_N), None

    def g(ay: float) -> tuple:
        v, motivo = caps(ay)
        return (None, motivo) if v is None else (v[0] + v[1] - cfg.mass_total * ay, None)

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


def limite(caso: eq.CasoEquilibrio, hip: Hipoteses, resolucao_ms2: float = 0.01, ay_max_g: float = 2.0,
           n_alfa: int = 401) -> Limite:
    """T, saturação por eixo, veredito, Q, P, K e stability index em raio fixo (curva à esquerda; a direita, com
    equilibrio.espelhar). Só variantes desacopladas (as acopladas lançam NotImplementedError("Task 4")). Sem raio_m
    lança ValueError (decisão 2 do plano). O campo `sentido` de Hipoteses não age aqui: os dois sentidos são dois
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
    _checa_desacoplada(hip)
    if not (isinstance(resolucao_ms2, (int, float)) and math.isfinite(resolucao_ms2) and resolucao_ms2 > 0.0):
        raise ValueError(f"resolucao_ms2 deve ser > 0 e finito; recebido {resolucao_ms2!r}.")
    if not (isinstance(ay_max_g, (int, float)) and math.isfinite(ay_max_g) and ay_max_g > 0.0):
        raise ValueError(f"ay_max_g deve ser > 0 e finito; recebido {ay_max_g!r}.")
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
            cn_iso_q = -cn_est_q
        cn_p, motivo_p = _ponto_p(caso, ay_t, ay_max, passo, tol, n_alfa)
        if cn_p is None:
            motivo_sat = "; ".join(x for x in (motivo_sat, motivo_p) if x)
        avisos = []
        for e in ("F", "R"):
            for texto in eq.capacidade_eixo(caso, e, ay_t, n_alfa).limites:
                if texto not in avisos:
                    avisos.append(texto)
        limitacoes = tuple(avisos)

    try:
        k = k_trim(caso, hip, AY_REF_G * G, n_alfa)
    except ValueError:
        k = None
    try:
        si = stability_index(caso, hip, AY_REF_G * G, n_alfa)
    except ValueError:
        si = None
    return Limite(ay_t_ms2=ay_t, ay_sat_f=ef.sat, ay_sat_r=er.sat, motivo_sat=motivo_sat, eixo_satura=eixo,
                  veredito=veredito, cn_iso_q=cn_iso_q, cn_estabilizante_q=cn_est_q, cn_p=cn_p,
                  stability_index=si, k_rad_por_ms2=k, resolucao_ms2=float(resolucao_ms2),
                  motivo=motivo, limitacoes=limitacoes)
