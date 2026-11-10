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
from collections.abc import Callable, Iterable, Mapping
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
    loo = _loo_trecho(family, (p_lo, p_hi), (fz_n, alpha_rad, camber_rad, kappa, vx_mps), avisos) if diagnostico else {}
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
