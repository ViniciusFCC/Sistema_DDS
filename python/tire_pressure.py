"""
Subprojeto A (pneu com variação de pressão): A2, interpolação rotulada das saídas entre perfis vizinhos.

Base: docs/superpowers/specs/2026-11-02-pneu-estado-design.md (§3, §5, §9), EDR-071.

A2 NÃO estima parâmetro nenhum (compatível com o EDR-015): avalia o `evaluate_static` dos dois perfis vizinhos no
mesmo ponto (Fz, alfa, gama, kappa, vx) e interpola linearmente as SAÍDAS,
    w = (p - p_lo)/(p_hi - p_lo),  X(p) = (1 - w)·X(p_lo) + w·X(p_hi),  X em {Fx, Fy, Mx, My, Mz},
com mu_eff recalculado de Fx, Fy e Fz. O modelo de pressão do PAC2002 (PP*, QPZ1-2, QPX1) não é usado: vale zero
nos quatro .tir.

Rótulos que valem para toda saída deste módulo (spec §5):
- R25B != R60A (nem a tendência se transfere com certeza);
- mu absoluto do TTC não transferível;
- pressão de ensaio != pressão fria (a confirmar);
- Validation = NOT_VALIDATED;
- INTERPOLADO quando o resultado vem da mistura (em nó exato o resultado é o próprio `evaluate_static`);
- caso demonstrativo T09/E03 com coeficientes de 12 psi como linha de base, não o T11.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

import tire_model as _base
import tire_model_static as ts


class TireInterpolationError(ts.StaticTireError):
    """Pressão, faixa ou revisão que a interpolação rotulada não aceita."""


@dataclass(frozen=True)
class Faixa:
    """Faixa de validade (FZMIN.. etc. do .tir): Fz em N, ângulos em rad, kappa adimensional."""

    fz_min_n: float
    fz_max_n: float
    alfa_min_rad: float
    alfa_max_rad: float
    camber_min_rad: float
    camber_max_rad: float
    kappa_min: float
    kappa_max: float


def faixa_do_perfil(profile: ts.StaticTireProfile) -> Faixa:
    p = profile.parameters
    return Faixa(
        fz_min_n=float(p["FZMIN"]), fz_max_n=float(p["FZMAX"]),
        alfa_min_rad=float(p["ALPMIN"]), alfa_max_rad=float(p["ALPMAX"]),
        camber_min_rad=float(p["CAMMIN"]), camber_max_rad=float(p["CAMMAX"]),
        kappa_min=float(p["KPUMIN"]), kappa_max=float(p["KPUMAX"]),
    )


def faixa_comum(perfis: Iterable[ts.StaticTireProfile]) -> Faixa:
    """Interseção das faixas dos perfis."""
    fs = [faixa_do_perfil(p) for p in perfis]
    if not fs:
        raise TireInterpolationError("faixa_comum precisa de ao menos um perfil.")
    return Faixa(
        fz_min_n=max(f.fz_min_n for f in fs), fz_max_n=min(f.fz_max_n for f in fs),
        alfa_min_rad=max(f.alfa_min_rad for f in fs), alfa_max_rad=min(f.alfa_max_rad for f in fs),
        camber_min_rad=max(f.camber_min_rad for f in fs), camber_max_rad=min(f.camber_max_rad for f in fs),
        kappa_min=max(f.kappa_min for f in fs), kappa_max=min(f.kappa_max for f in fs),
    )


def _fora_da_faixa(f: Faixa, fz_n: float, alpha_rad: float, camber_rad: float, kappa: float) -> list[str]:
    """Grandezas fora da faixa (limite inclusivo: ponto exatamente no limite está dentro)."""
    fora = []
    if not (f.fz_min_n <= fz_n <= f.fz_max_n):
        fora.append(f"Fz={fz_n:g} N fora de [{f.fz_min_n:g}, {f.fz_max_n:g}] N")
    if not (f.alfa_min_rad <= alpha_rad <= f.alfa_max_rad):
        fora.append(f"alfa={math.degrees(alpha_rad):.2f}° fora de "
                    f"[{math.degrees(f.alfa_min_rad):.1f}, {math.degrees(f.alfa_max_rad):.1f}]°")
    if not (f.camber_min_rad <= camber_rad <= f.camber_max_rad):
        fora.append(f"camber={math.degrees(camber_rad):.2f}° fora de "
                    f"[{math.degrees(f.camber_min_rad):.1f}, {math.degrees(f.camber_max_rad):.1f}]°")
    if not (f.kappa_min <= kappa <= f.kappa_max):
        fora.append(f"kappa={kappa:g} fora de [{f.kappa_min:g}, {f.kappa_max:g}]")
    return fora


def vizinhos(family: ts.StaticTireFamily, pressure_psi: float) -> tuple[float, float, float]:
    """(p_lo, p_hi, w) com as chaves reais da família. Nó exato (dentro da tolerância) devolve (p, p, 0.0)."""
    if not math.isfinite(pressure_psi):
        raise TireInterpolationError("Pressão deve ser finita.")
    ps = family.pressures_psi
    tol = ts.PRESSURE_TOLERANCE_PSI
    if pressure_psi < ps[0] - tol or pressure_psi > ps[-1] + tol:
        raise TireInterpolationError(
            f"Pressão {pressure_psi:g} psi fora de [{ps[0]:.0f}, {ps[-1]:.0f}] psi (chaves reais da família: "
            f"{', '.join(f'{p:.6f}' for p in ps)}); sem extrapolação."
        )
    for p in ps:
        if abs(p - pressure_psi) <= tol:
            return p, p, 0.0
    hi = next(p for p in ps if p > pressure_psi)
    lo = max(p for p in ps if p < pressure_psi)
    return lo, hi, (pressure_psi - lo) / (hi - lo)


@dataclass(frozen=True)
class InterpolatedTireResult:
    fx_n: float
    fy_n: float
    fz_n: float
    mx_nm: float
    my_nm: float
    mz_nm: float
    mu_effective: float
    pressure_psi: float
    speed_mps: float
    rotulo: str = "INTERPOLADO"
    vizinhos_psi: tuple[float, float] = (0.0, 0.0)
    pesos: tuple[float, float] = (1.0, 0.0)
    sha256: tuple[str, str] = ("", "")
    revision_id: str = ""
    loo_trecho: Mapping[float, Mapping[str, float]] = field(default_factory=dict)
    avisos: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


Avaliador = Callable[[float, float, float, float, float], "ts.StaticTireResult | InterpolatedTireResult"]

_LIMITACAO_A2 = "Saídas interpoladas linearmente entre perfis independentes (EDR-071); não é medição nem ajuste."


def _mix(w: float, a: float, b: float) -> float:
    return (1.0 - w) * a + w * b


def _loo_trecho(family, ps_viz, pt, avisos) -> dict[float, dict[str, float]]:
    """Erro LOO (previsto - real) de fx, fy e mz em cada vizinho que é nó interno da família."""
    ps = family.pressures_psi
    fz_n, alpha_rad, camber_rad, kappa, vx_mps = pt
    kw = dict(fz_n=fz_n, alpha_rad=alpha_rad, camber_rad=camber_rad, kappa=kappa, vx_mps=vx_mps)
    loo: dict[float, dict[str, float]] = {}
    for p in sorted(set(ps_viz)):
        i = ps.index(p)
        if i == 0 or i == len(ps) - 1:
            continue
        a, n, b = family.profiles[ps[i - 1]], family.profiles[p], family.profiles[ps[i + 1]]
        fora = next((q for q in (a, n, b)
                     if _fora_da_faixa(faixa_do_perfil(q), fz_n, alpha_rad, camber_rad, kappa)), None)
        if fora is not None:
            avisos.append(f"LOO do nó {p:g} psi não calculado: ponto fora da faixa de {fora.inflation_psi:g} psi")
            continue
        w = (p - ps[i - 1]) / (ps[i + 1] - ps[i - 1])
        ra, rn, rb = (ts.evaluate_static(q, **kw) for q in (a, n, b))
        loo[p] = {
            "fx_n": _mix(w, ra.fx_n, rb.fx_n) - rn.fx_n,
            "fy_n": _mix(w, ra.fy_n, rb.fy_n) - rn.fy_n,
            "mz_n": _mix(w, ra.mz_nm, rb.mz_nm) - rn.mz_nm,
        }
    return loo


def _aviso_pico(family, p_lo, p_hi, fz_n, camber_rad) -> str:
    """Aviso se um vizinho tem pico de μy interior e o outro não (máximo na borda ALPMAX), em algum sentido de α,
    avaliado em (Fz, γ) do ponto pedido, κ = 0, na faixa comum dos vizinhos."""
    lo, hi = family.profiles[p_lo], family.profiles[p_hi]
    faixa = faixa_comum((lo, hi))
    if not (faixa.fz_min_n <= fz_n <= faixa.fz_max_n and faixa.camber_min_rad <= camber_rad <= faixa.camber_max_rad):
        return ""
    for sinal in (1, -1):
        b_lo = pico_mu_y(avaliador_perfil(lo), faixa, fz_n=fz_n, camber_rad=camber_rad, sinal=sinal).borda
        b_hi = pico_mu_y(avaliador_perfil(hi), faixa, fz_n=fz_n, camber_rad=camber_rad, sinal=sinal).borda
        if b_lo != b_hi:
            interior, sem = (p_hi, p_lo) if b_lo else (p_lo, p_hi)
            return (f"a mistura junta uma curva com pico interior ({interior:.3g} psi) e outra sem pico interior "
                    f"({sem:.3g} psi)")
    return ""


def evaluate_interpolated(
    family: ts.StaticTireFamily,
    pressure_psi: float,
    *,
    fz_n: float,
    alpha_rad: float,
    camber_rad: float,
    kappa: float,
    vx_mps: float,
    diagnostico: bool = True,
) -> ts.StaticTireResult | InterpolatedTireResult:
    """A2: saídas interpoladas entre os dois perfis vizinhos. No nó exato devolve o próprio `evaluate_static`.

    Recusas, nesta ordem: pressão fora da família; `revision_id` diferentes entre os vizinhos; ponto fora da
    interseção das faixas dos vizinhos. `diagnostico=False` pula `loo_trecho` (varreduras das métricas).
    """
    p_lo, p_hi, w = vizinhos(family, pressure_psi)
    lo, hi = family.profiles[p_lo], family.profiles[p_hi]
    kw = dict(fz_n=fz_n, alpha_rad=alpha_rad, camber_rad=camber_rad, kappa=kappa, vx_mps=vx_mps)
    if p_lo == p_hi:
        return ts.evaluate_static(lo, **kw)
    if lo.revision_id != hi.revision_id:
        raise TireInterpolationError(
            f"Vizinhos com revision_id diferentes ({lo.revision_id!r} a {p_lo:g} psi, {hi.revision_id!r} a "
            f"{p_hi:g} psi): a mistura juntaria calibrações de origens distintas."
        )
    fora = _fora_da_faixa(faixa_comum((lo, hi)), fz_n, alpha_rad, camber_rad, kappa)
    if fora:
        raise TireInterpolationError(
            f"Ponto fora da interseção das faixas dos vizinhos {p_lo:g} e {p_hi:g} psi: " + "; ".join(fora)
        )
    r_lo, r_hi = ts.evaluate_static(lo, **kw), ts.evaluate_static(hi, **kw)
    fx, fy = _mix(w, r_lo.fx_n, r_hi.fx_n), _mix(w, r_lo.fy_n, r_hi.fy_n)
    avisos: list[str] = []
    loo = {}
    if diagnostico:
        loo = _loo_trecho(family, (p_lo, p_hi), (fz_n, alpha_rad, camber_rad, kappa, vx_mps), avisos)
        aviso = _aviso_pico(family, p_lo, p_hi, fz_n, camber_rad)
        if aviso:
            avisos.append(aviso)
    limitations = list(r_lo.limitations)
    limitations += [x for x in r_hi.limitations if x not in limitations]
    limitations.append(_LIMITACAO_A2)
    return InterpolatedTireResult(
        fx_n=fx, fy_n=fy, fz_n=fz_n,
        mx_nm=_mix(w, r_lo.mx_nm, r_hi.mx_nm),
        my_nm=_mix(w, r_lo.my_nm, r_hi.my_nm),
        mz_nm=_mix(w, r_lo.mz_nm, r_hi.mz_nm),
        mu_effective=_base.mu_effective(fx, fy, fz_n),
        pressure_psi=pressure_psi, speed_mps=vx_mps,
        vizinhos_psi=(p_lo, p_hi), pesos=(1.0 - w, w),
        sha256=(lo.base_sha256, hi.base_sha256),
        revision_id=lo.revision_id,
        loo_trecho=loo, avisos=tuple(avisos), limitations=tuple(limitations),
    )


def avaliador_perfil(profile: ts.StaticTireProfile) -> Avaliador:
    def av(fz_n, alpha_rad, camber_rad, kappa, vx_mps):
        return ts.evaluate_static(profile, fz_n=fz_n, alpha_rad=alpha_rad, camber_rad=camber_rad,
                                  kappa=kappa, vx_mps=vx_mps)
    return av


def avaliador_interpolado(family: ts.StaticTireFamily, pressure_psi: float) -> Avaliador:
    def av(fz_n, alpha_rad, camber_rad, kappa, vx_mps):
        return evaluate_interpolated(family, pressure_psi, fz_n=fz_n, alpha_rad=alpha_rad,
                                     camber_rad=camber_rad, kappa=kappa, vx_mps=vx_mps, diagnostico=False)
    return av


# ---------------------------------------------------------------------------------------------------------
# Métricas do pneu por pressão (spec §6): o avaliador é passado como função, então valem para um perfil
# (`avaliador_perfil`) e para a curva interpolada (`avaliador_interpolado`).
# ---------------------------------------------------------------------------------------------------------
_VX_PADRAO = 11.176          # m/s; Fx e Fy do PAC2002 não dependem de Vx, só o My
_N_GRADE_PICO = 121          # pontos da grade grossa da busca de pico
_XATOL_PICO = 1e-7
_ROT_BORDA = "limitante inferior, sem pico interior"
_ROT_T0 = "t0 e α do pico de Mz: anexo, pendentes do item 3 do EDR-067; fora do A1-escolha"


@dataclass(frozen=True)
class Pico:
    """Máximo de uma curva. `argumento` é α [rad] ou κ. `borda=True`: o máximo está no limite da faixa, então
    `mu` é só um limitante inferior do pico (rótulo "limitante inferior, sem pico interior")."""

    mu: float
    argumento: float
    borda: bool


def _buscar_pico(f: Callable[[float], float], a: float, b: float, *, extremo_distante: int) -> Pico:
    """Máximo de f em [a, b]: grade grossa de 121 pontos e, se o máximo for interior, refino (bounded, xatol 1e-7)
    entre os vizinhos do máximo. `extremo_distante` é o índice da grade (0 ou 120) do extremo oposto a zero, onde
    a faixa termina: máximo da grade aí é `borda=True`, sem refino.
    Limitação: um pico verdadeiro dentro do último passo da grade (faixa/120) também sai como borda."""
    from scipy.optimize import minimize_scalar

    xs = [a + (b - a) * i / (_N_GRADE_PICO - 1) for i in range(_N_GRADE_PICO)]
    ys = [f(x) for x in xs]
    i = max(range(_N_GRADE_PICO), key=ys.__getitem__)
    if i == extremo_distante:
        return Pico(mu=ys[i], argumento=xs[i], borda=True)
    lo, hi = xs[max(i - 1, 0)], xs[min(i + 1, _N_GRADE_PICO - 1)]
    res = minimize_scalar(lambda x: -f(x), bounds=(lo, hi), method="bounded", options={"xatol": _XATOL_PICO})
    if -res.fun > ys[i]:
        return Pico(mu=-float(res.fun), argumento=float(res.x), borda=False)
    return Pico(mu=ys[i], argumento=xs[i], borda=False)


def pico_mu_y(avaliador: Avaliador, faixa: Faixa, *, fz_n: float, camber_rad: float, sinal: int) -> Pico:
    """Pico de |Fy|/Fz em κ = 0. sinal +1: α em [0, ALPMAX]; -1: α em [ALPMIN, 0]."""
    if sinal not in (1, -1):
        raise ValueError("sinal deve ser +1 ou -1.")

    def mu(alfa: float) -> float:
        return abs(avaliador(fz_n, alfa, camber_rad, 0.0, _VX_PADRAO).fy_n) / fz_n

    if sinal > 0:
        return _buscar_pico(mu, 0.0, faixa.alfa_max_rad, extremo_distante=_N_GRADE_PICO - 1)
    return _buscar_pico(mu, faixa.alfa_min_rad, 0.0, extremo_distante=0)


def pico_mu_x(avaliador: Avaliador, faixa: Faixa, *, fz_n: float, camber_rad: float, sinal: int) -> Pico:
    """Pico de |Fx|/Fz em α = 0. sinal +1 (tração): κ em [0, KPUMAX]; -1 (frenagem): κ em [KPUMIN, 0]."""
    if sinal not in (1, -1):
        raise ValueError("sinal deve ser +1 ou -1.")

    def mu(kappa: float) -> float:
        return abs(avaliador(fz_n, 0.0, camber_rad, kappa, _VX_PADRAO).fx_n) / fz_n

    if sinal > 0:
        return _buscar_pico(mu, 0.0, faixa.kappa_max, extremo_distante=_N_GRADE_PICO - 1)
    return _buscar_pico(mu, faixa.kappa_min, 0.0, extremo_distante=0)


@dataclass(frozen=True)
class MetricasPneu:
    fz_n: float
    camber_rad: float
    c_alpha_n_rad: float
    c_alpha_por_fz_1_rad: float
    c_gamma_n_rad: float
    c_kappa_n: float
    mu_y_pos: Pico
    mu_y_neg: Pico
    mu_x_tracao: Pico
    mu_x_frenagem: Pico
    fy_alpha0_n: float
    t0_m: float
    alfa_pico_mz_rad: float
    rotulos: tuple[str, ...]


def metricas_pneu(avaliador: Avaliador, faixa: Faixa, *, fz_n: float, camber_rad: float,
                  vx_mps: float = _VX_PADRAO) -> MetricasPneu:
    """Métricas da spec §6 num ponto (Fz, γ). Derivadas por diferença central com o passo de `tire_model`
    (`_H_RIGIDEZ` = 1e-6), em α = 0 e κ = 0, com γ = `camber_rad` (em γ = 0 coincidem com
    `tire_model.rigidez_deriva` e `rigidez_camber`; ISO_TYDEX, roda FR).

    Sinais: Cα = −∂Fy/∂α; Cγ = −∂Fy/∂γ (como `rigidez_camber`). Cκ = +∂Fx/∂κ em κ = 0: no `.tir` Fx > 0 para
    κ > 0 (TC-TIRE-004b), então a rigidez longitudinal positiva é +∂Fx/∂κ. A spec §6 escreve "−∂Fx/∂κ", que dá
    negativo com esta convenção; a troca de sinal é decisão do controlador, a confirmar com o usuário.
    t0 = −(∂Mz/∂α)/(∂Fy/∂α) em α = 0 (spec §6, anexo)."""
    h = _base._H_RIGIDEZ

    def av(alfa: float, gama: float, kappa: float):
        return avaliador(fz_n, alfa, gama, kappa, vx_mps)

    r_ap, r_am = av(+h, camber_rad, 0.0), av(-h, camber_rad, 0.0)
    fy_a = (r_ap.fy_n - r_am.fy_n) / (2.0 * h)
    mz_a = (r_ap.mz_nm - r_am.mz_nm) / (2.0 * h)
    fy_g = (av(0.0, camber_rad + h, 0.0).fy_n - av(0.0, camber_rad - h, 0.0).fy_n) / (2.0 * h)
    fx_k = (av(0.0, camber_rad, +h).fx_n - av(0.0, camber_rad, -h).fx_n) / (2.0 * h)
    c_alpha = -fy_a

    kw = dict(fz_n=fz_n, camber_rad=camber_rad)
    mu_y_pos, mu_y_neg = pico_mu_y(avaliador, faixa, sinal=1, **kw), pico_mu_y(avaliador, faixa, sinal=-1, **kw)
    mu_x_tr, mu_x_fr = pico_mu_x(avaliador, faixa, sinal=1, **kw), pico_mu_x(avaliador, faixa, sinal=-1, **kw)
    pico_mz = _buscar_pico(lambda alfa: abs(av(alfa, camber_rad, 0.0).mz_nm), 0.0, faixa.alfa_max_rad,
                           extremo_distante=_N_GRADE_PICO - 1)

    rotulos = [
        "Cγ: μy(γ) sem informação de pressão (PDY3 = 2 nos quatro perfis)",
        "Cκ e μx: ajuste longitudinal mal condicionado (PKX2/PKX3 instáveis)",
    ]
    na_borda = [nome for nome, pk in (("μy α>0", mu_y_pos), ("μy α<0", mu_y_neg), ("μx tração", mu_x_tr),
                                      ("μx frenagem", mu_x_fr)) if pk.borda]
    if na_borda:
        rotulos += [_ROT_BORDA, "pico na borda da faixa em: " + ", ".join(na_borda)]
    rotulos.append(_ROT_T0)
    if pico_mz.borda:
        rotulos.append("α do pico de Mz na borda da faixa (ALPMAX): limitante, sem pico interior")
    rotulos.append("menor carga ensaiada a confirmar: FZMIN do .tir é o limite declarado, não a carga medida")

    return MetricasPneu(
        fz_n=fz_n, camber_rad=camber_rad,
        c_alpha_n_rad=c_alpha, c_alpha_por_fz_1_rad=c_alpha / fz_n,
        c_gamma_n_rad=-fy_g, c_kappa_n=fx_k,
        mu_y_pos=mu_y_pos, mu_y_neg=mu_y_neg, mu_x_tracao=mu_x_tr, mu_x_frenagem=mu_x_fr,
        fy_alpha0_n=av(0.0, camber_rad, 0.0).fy_n,
        t0_m=-mz_a / fy_a, alfa_pico_mz_rad=pico_mz.argumento,
        rotulos=tuple(rotulos),
    )


def penalidade_transferencia(avaliador: Avaliador, faixa: Faixa, *, fz0_n: float, dfz_n: float,
                             camber_rad: float) -> dict[str, float]:
    """Fy_max(Fz0+ΔFz) + Fy_max(Fz0−ΔFz) − 2·Fy_max(Fz0), por sentido de α, com Fy_max = μy pico · Fz.
    Fz0 ± ΔFz fora de [FZMIN, FZMAX] da faixa: ValueError."""
    for fz in (fz0_n + dfz_n, fz0_n - dfz_n):
        if not (faixa.fz_min_n <= fz <= faixa.fz_max_n):
            raise ValueError(f"Fz = {fz:g} N (Fz0 ± ΔFz) fora de [{faixa.fz_min_n:g}, {faixa.fz_max_n:g}] N.")

    def fy_max(fz: float, sinal: int) -> float:
        return pico_mu_y(avaliador, faixa, fz_n=fz, camber_rad=camber_rad, sinal=sinal).mu * fz

    return {
        chave: fy_max(fz0_n + dfz_n, s) + fy_max(fz0_n - dfz_n, s) - 2.0 * fy_max(fz0_n, s)
        for chave, s in (("alfa_pos", 1), ("alfa_neg", -1))
    }


def teto_comum_fz(family: ts.StaticTireFamily) -> float:
    """Menor FZMAX entre os perfis (1521 N com os .tir do TTC Round 6)."""
    return min(float(p.parameters["FZMAX"]) for p in family.profiles.values())


def grade_fz(family: ts.StaticTireFamily, fz_operacao: Sequence[float] = (),
             n: int = 8) -> list[tuple[float, tuple[str, ...]]]:
    """`n` valores igualmente espaçados de max(FZMIN) ao teto comum, mais as Fz de operação. Fz de operação acima
    do teto entra como o teto, com rótulo; abaixo de max(FZMIN), idem no piso."""
    piso = max(float(p.parameters["FZMIN"]) for p in family.profiles.values())
    teto = teto_comum_fz(family)
    grade: list[tuple[float, tuple[str, ...]]] = [(piso + (teto - piso) * i / (n - 1), ()) for i in range(n)]
    for fz in fz_operacao:
        if fz > teto:
            grade.append((teto, (f"Fz de operação {fz:g} N acima do teto comum: avaliada em {teto:.0f} N",)))
        elif fz < piso:
            grade.append((piso, (f"Fz de operação {fz:g} N abaixo do piso comum: avaliada em {piso:.0f} N",)))
        else:
            grade.append((float(fz), (f"Fz de operação {fz:g} N",)))
    return grade


def rigidez_vertical(profile: ts.StaticTireProfile) -> tuple[float, str]:
    return float(profile.parameters["VERTICAL_STIFFNESS"]), "valor do arquivo, linear, origem não verificada"


def intervalo_pico_mu_y(family: ts.StaticTireFamily, pressure_psi: float, *, fz_n: float, camber_rad: float,
                        sinal: int) -> tuple[float, float]:
    """Pico de μy da curva interpolada como intervalo (inferior, superior) (spec §3):
    inferior = max_α da mistura; superior = (1−w)·μ_lo + w·μ_hi (cota: o máximo da soma é no máximo a soma dos
    máximos). Nos nós exatos os dois são o pico do perfil. A busca usa a faixa comum dos vizinhos."""
    p_lo, p_hi, w = vizinhos(family, pressure_psi)
    lo, hi = family.profiles[p_lo], family.profiles[p_hi]
    kw = dict(fz_n=fz_n, camber_rad=camber_rad, sinal=sinal)
    if p_lo == p_hi:
        mu = pico_mu_y(avaliador_perfil(lo), faixa_do_perfil(lo), **kw).mu
        return mu, mu
    faixa = faixa_comum((lo, hi))
    inferior = pico_mu_y(avaliador_interpolado(family, pressure_psi), faixa, **kw).mu
    superior = _mix(w, pico_mu_y(avaliador_perfil(lo), faixa, **kw).mu, pico_mu_y(avaliador_perfil(hi), faixa, **kw).mu)
    return inferior, superior


# ---------------------------------------------------------------------------------------------------------
# Indicadores de incerteza (spec §6)
# ---------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ErroLOO:
    psi: float
    previsto: float
    real: float
    erro: float               # previsto − real
    erro_rel: float | None    # erro/|real|; None se real = 0


def erro_loo(valores: Mapping[float, float | None]) -> dict[float, ErroLOO]:
    """Erro deixando um perfil de fora: o valor do nó interno p_k é previsto por interpolação linear entre os
    nós vizinhos, (1−w)·v(p_lo) + w·v(p_hi), com w = (p_k − p_lo)/(p_hi − p_lo) calculado com as chaves reais.
    Só nós internos entram: 8 e 14 psi (os extremos) nunca aparecem, porque não têm vizinho dos dois lados
    (extrapolar não é LOO). Nó cujo valor ou cujo vizinho é None fica fora."""
    ps = sorted(valores)
    saida: dict[float, ErroLOO] = {}
    for i in range(1, len(ps) - 1):
        p_lo, p_k, p_hi = ps[i - 1], ps[i], ps[i + 1]
        v_lo, v_k, v_hi = valores[p_lo], valores[p_k], valores[p_hi]
        if v_lo is None or v_k is None or v_hi is None:
            continue
        w = (p_k - p_lo) / (p_hi - p_lo)
        previsto = _mix(w, v_lo, v_hi)
        erro = previsto - v_k
        saida[p_k] = ErroLOO(p_k, previsto, v_k, erro, None if v_k == 0 else erro / abs(v_k))
    return saida


@dataclass(frozen=True)
class Assimetria:
    dif_mu_pico: float    # |μy(α>0) − μy(α<0)|
    dif_rel: float        # dif_mu_pico dividida pela média dos dois picos
    fy_alpha0_n: float    # Fy em α = 0
    rotulo: str


def assimetria_alfa(metricas: MetricasPneu) -> Assimetria:
    """Assimetria ±α: diferença entre os picos de μy para α > 0 e α < 0, e Fy em α = 0 (já em `metricas`).
    Em parte é física (conicidade e ply-steer), então não é só erro de ajuste."""
    a, b = metricas.mu_y_pos.mu, metricas.mu_y_neg.mu
    dif = abs(a - b)
    media = 0.5 * (a + b)
    return Assimetria(dif, dif / media if media else 0.0, metricas.fy_alpha0_n,
                      "em parte física: conicidade e ply-steer")


def monotonicidade(valores: Mapping[float, float]) -> str:
    """'crescente' e 'decrescente' pedem diferenças estritas entre pressões consecutivas (ordenadas por
    pressão); 'constante' vale só quando todas são exatamente zero; o resto é 'não monotônica'."""
    seq = [valores[p] for p in sorted(valores)]
    difs = [b - a for a, b in zip(seq, seq[1:], strict=False)]
    if difs and all(d == 0 for d in difs):
        return "constante"
    if all(d > 0 for d in difs):
        return "crescente"
    if all(d < 0 for d in difs):
        return "decrescente"
    return "não monotônica"
