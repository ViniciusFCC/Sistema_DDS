"""Static PAC2002 tire analysis, V4 local development model.

This is a new local-only layer over the existing Fx/Fy implementation, whose
outputs have been compared with independent code transcriptions but not
validated against tire measurements. This layer adds fixed-pressure profile
families, non-destructive coefficient revisions, and PAC2002 steady-state
moments. It does not implement transient response, thermal evolution, or wear.

Source for the moment equations: MSC Adams Tire User Guide 2022.3,
"Using the PAC2002 Tire Model", Eqs. 100-110 (Mx is Eq. 109), and the PAC2002
parameter tables. In 4.1.0 the Mx (Eq. 109) and the sign of s*Fx in Mz (Eq. 100)
were corrected (EDR-067); results and overlays produced before 4.1.0 are not valid. Forces and moments are returned in the explicitly declared
tire-file axes. The four Round 6 profiles are separate fixed-pressure fits; their PP*
coefficients are zero, so this module deliberately does not interpolate them.

Physical validation status: NOT_VALIDATED. The code must not be interpreted as
validated for the team's R60A or as a measured vehicle result.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

import tire_model as _base

__version__ = "4.1.0-static"
SUPPORTED_FORMATS = {"PAC2002"}
PRESSURE_TOLERANCE_PSI = 1e-3
MOMENT_COEFFICIENTS = (
    *(f"QSX{i}" for i in range(1, 12)),
    *(f"QSY{i}" for i in range(1, 9)),
    "QBZ1", "QBZ2", "QBZ3", "QBZ4", "QBZ5", "QBZ9", "QBZ10", "QCZ1",
    "QDZ1", "QDZ2", "QDZ3", "QDZ4", "QDZ6", "QDZ7", "QDZ8", "QDZ9",
    *(f"QEZ{i}" for i in range(1, 6)),
    *(f"QHZ{i}" for i in range(1, 5)),
    "SSZ1", "SSZ2", "SSZ3", "SSZ4",
)
# Fatores de escala usados nos momentos (Mx, My e Mz); ausente no .tir vale 1 (default do help do Adams).
MOMENT_SCALING_FACTORS = (
    "LMX", "LVMX", "LMY", "LS", "LTR", "LKY", "LMUY", "LGAZ", "LRES", "LMUGAMMA",
)
# Parâmetros sem os quais o perfil não pode ser avaliado nem validado contra as faixas declaradas.
REQUIRED_PARAMETERS = (
    "FNOMIN", "LFZO", "UNLOADED_RADIUS", "FZMIN", "FZMAX",
    "ALPMIN", "ALPMAX", "CAMMIN", "CAMMAX", "KPUMIN", "KPUMAX",
)


class StaticTireError(ValueError):
    """Invalid dataset, unsupported operating point, or invalid revision."""


def _clone_dataset(dataset: _base.TireDataset) -> _base.TireDataset:
    return _base.TireDataset(
        p=dict(dataset.p),
        strings=dict(dataset.strings),
        source=dataset.source,
        axis_system=dataset.axis_system,
        convention_status=dataset.convention_status,
    )


def _validate_parameter_ranges(params: Mapping[str, float]) -> None:
    """Reject revisions that make declared operating limits self-inconsistent."""
    for lower, upper in (("FZMIN", "FZMAX"), ("ALPMIN", "ALPMAX"),
                         ("CAMMIN", "CAMMAX"), ("KPUMIN", "KPUMAX")):
        if lower in params and upper in params and not params[lower] < params[upper]:
            raise StaticTireError(f"Faixa inválida após revisão: {lower} deve ser menor que {upper}.")
    if "FZMIN" in params and params["FZMIN"] <= 0:
        raise StaticTireError("FZMIN deve permanecer positivo.")
    for key in ("FNOMIN", "LFZO", "UNLOADED_RADIUS", "LONGVL", "LMUY"):
        if key in params and params[key] <= 0:
            raise StaticTireError(f"{key} deve permanecer positivo.")


def _get(p: Mapping[str, float], key: str, default: float = 0.0) -> float:
    return float(p.get(key, default))


def _mf_cos(B: float, C: float, D: float, E: float, x: float) -> float:
    z = B * x
    return D * math.cos(C * math.atan(z - E * (z - math.atan(z))))


@dataclass(frozen=True)
class StaticTireProfile:
    """One PAC2002 steady-state calibration at its nominal inflation pressure."""

    dataset: _base.TireDataset
    source_path: Path
    inflation_pa: float
    inflation_psi: float
    base_sha256: str
    revision_id: str = "BASE"
    revision_reason: str = "Original .tir parameters"
    overrides: Mapping[str, float] = field(default_factory=dict)
    revision_parent_id: str | None = None
    revision_timestamp_utc: str | None = None

    def __post_init__(self) -> None:
        dataset = _clone_dataset(self.dataset)
        dataset.p = MappingProxyType(dict(dataset.p))
        dataset.strings = MappingProxyType(dict(dataset.strings))
        object.__setattr__(self, "dataset", dataset)
        object.__setattr__(self, "overrides", MappingProxyType(dict(self.overrides)))

    @property
    def parameters(self) -> Mapping[str, float]:
        return self.dataset.p


@dataclass(frozen=True)
class StaticTireFamily:
    """A set of independently fitted static profiles indexed by inflation psi."""

    profiles: Mapping[float, StaticTireProfile]

    @property
    def pressures_psi(self) -> tuple[float, ...]:
        return tuple(sorted(self.profiles))

    def at_pressure(self, pressure_psi: float) -> StaticTireProfile:
        for available in self.pressures_psi:
            if abs(available - pressure_psi) <= PRESSURE_TOLERANCE_PSI:
                return self.profiles[available]
        raise StaticTireError(
            f"Pressão {pressure_psi:g} psi não tem perfil calibrado. "
            f"Perfis disponíveis: {', '.join(f'{p:g}' for p in self.pressures_psi)} psi. "
            "Interpolação entre perfis não está habilitada."
        )


@dataclass(frozen=True)
class StaticTireResult:
    """Steady-state contact forces and moments in the declared tire-file axes."""

    fx_n: float
    fy_n: float
    fz_n: float
    mx_nm: float
    my_nm: float
    mz_nm: float
    mu_effective: float
    pressure_psi: float
    speed_mps: float
    revision_id: str
    source_tir: str
    source_sha256: str
    axis_system: str
    limitations: tuple[str, ...] = ()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_profile(
    path: str | Path, *, source_axis_system: str | None = None
) -> StaticTireProfile:
    """Load a fixed-pressure PAC2002 .tir as a static profile.

    ``IP`` is the profile pressure and must equal ``IP_NOM``. A family of .tir
    files at different nominal pressures is supported; a single profile with
    nonzero ``PP*`` pressure corrections is deliberately rejected until those
    terms have an independently verified implementation.
    """
    path = Path(path)
    if source_axis_system not in _base.AXIS_TRANSFORMS:
        raise StaticTireError(
            "Declare o sistema de eixos do .tir explicitamente: ISO_TYDEX ou SAE_CALSPAN."
        )
    p_raw, strings = _base.parse_tir(path)
    fmt = strings.get("PROPERTY_FILE_FORMAT")
    if fmt not in SUPPORTED_FORMATS:
        raise StaticTireError(f"Formato {fmt!r} não suportado nesta versão estática.")
    if p_raw.get("IP") is None or p_raw.get("IP_NOM") is None or p_raw["IP_NOM"] <= 0:
        raise StaticTireError("O .tir precisa declarar IP e IP_NOM positivos em Pa.")
    if not math.isclose(p_raw["IP"], p_raw["IP_NOM"], rel_tol=0, abs_tol=1e-9):
        raise StaticTireError("Cada perfil desta versão deve estar avaliado na pressão nominal IP=IP_NOM.")
    pp_keys = ("PPX1", "PPX2", "PPX3", "PPX4", "PPY1", "PPY2", "PPY3", "PPY4")
    missing_required = [k for k in REQUIRED_PARAMETERS if k not in p_raw]
    if missing_required:
        raise StaticTireError(
            f"O .tir não declara parâmetros obrigatórios: {', '.join(missing_required)}."
        )
    nonzero = {k: p_raw[k] for k in pp_keys if p_raw.get(k, 0.0) != 0.0}
    if nonzero:
        raise StaticTireError(
            f"Correções de pressão PP* não implementadas nesta versão estática: {nonzero}"
        )
    _validate_parameter_ranges(p_raw)
    dataset = _base.load_dataset(
        str(path), source=str(path), source_axis_system=source_axis_system
    )
    pressure_psi = p_raw["IP"] / 6894.757293168
    return StaticTireProfile(
        dataset=dataset,
        source_path=path.resolve(),
        inflation_pa=p_raw["IP"],
        inflation_psi=pressure_psi,
        base_sha256=_sha256(path),
    )


def load_profile_family(
    directory: str | Path, *, source_axis_system: str | None = None
) -> StaticTireFamily:
    """Load `*_psi_PAC02_UM4.tir` files as independent pressure profiles."""
    directory = Path(directory)
    paths = sorted(directory.glob("*PAC02_UM4.tir"))
    if not paths:
        raise StaticTireError(f"Nenhum perfil *PAC02_UM4.tir encontrado em {directory}.")
    profiles: dict[float, StaticTireProfile] = {}
    for path in paths:
        profile = load_profile(path, source_axis_system=source_axis_system)
        key = round(profile.inflation_psi, 6)
        if key in profiles:
            raise StaticTireError(f"Mais de um .tir nominal para {key} psi em {directory}.")
        profiles[key] = profile
    return StaticTireFamily(profiles=profiles)


def revise_profile(
    profile: StaticTireProfile,
    changes: Mapping[str, float],
    *,
    reason: str,
    revision_id: str,
) -> StaticTireProfile:
    """Return an in-memory parameter revision without modifying the source .tir."""
    if (not isinstance(revision_id, str) or not isinstance(reason, str)
            or not revision_id.strip() or not reason.strip()):
        raise StaticTireError("Toda revisão precisa de revision_id e justificativa (textos não vazios).")
    normalized: dict[str, float] = {}
    for key, value in changes.items():
        if isinstance(value, bool):
            raise StaticTireError(f"Valor inválido para {key}: {value!r}; use um número.")
        try:
            normalized[str(key).upper()] = float(value)
        except (TypeError, ValueError) as exc:
            raise StaticTireError(f"Valor inválido para {key}: {value!r}; use um número.") from exc
    if not normalized:
        raise StaticTireError("A revisão precisa alterar ao menos um parâmetro.")
    if {"IP", "IP_NOM"}.intersection(normalized):
        raise StaticTireError(
            "IP/IP_NOM definem o perfil calibrado; selecione outro .tir nominal em vez de alterá-los."
        )
    unknown = sorted(set(normalized) - set(profile.dataset.p))
    if unknown:
        raise StaticTireError(f"Parâmetros ausentes no .tir: {unknown}")
    if any(not math.isfinite(v) for v in normalized.values()):
        raise StaticTireError("Os parâmetros revisados devem ser finitos.")
    dataset = _clone_dataset(profile.dataset)
    dataset.p.update(normalized)
    _validate_parameter_ranges(dataset.p)
    return StaticTireProfile(
        dataset=dataset,
        source_path=profile.source_path,
        inflation_pa=profile.inflation_pa,
        inflation_psi=profile.inflation_psi,
        base_sha256=profile.base_sha256,
        revision_id=revision_id,
        revision_reason=reason,
        overrides={**profile.overrides, **normalized},
        revision_parent_id=profile.revision_id,
        revision_timestamp_utc=datetime.now(UTC).isoformat(),
    )


def save_revision(profile: StaticTireProfile, path: str | Path) -> Path:
    """Save a small JSON overlay with provenance; the original .tir is untouched."""
    path = Path(path)
    if path.exists():
        raise StaticTireError(f"O arquivo de revisão já existe; use um novo caminho: {path}")
    payload = {
        "schema": "Sistema_DDS.StaticTireRevision.v1",
        "model_version": __version__,
        "revision_id": profile.revision_id,
        "parent_revision_id": profile.revision_parent_id,
        "created_at_utc": profile.revision_timestamp_utc,
        "reason": profile.revision_reason,
        "source_tir": profile.source_path.name,
        "source_sha256": profile.base_sha256,
        "pressure_psi": profile.inflation_psi,
        "axis_system": profile.dataset.axis_system,
        "validation_status": "NOT_VALIDATED",
        "overrides": dict(profile.overrides),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_revision(profile: StaticTireProfile, path: str | Path) -> StaticTireProfile:
    """Apply a saved JSON overlay only to its exact source .tir content."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StaticTireError(f"Não foi possível ler o overlay JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise StaticTireError("O overlay JSON deve conter um objeto na raiz.")
    if payload.get("schema") != "Sistema_DDS.StaticTireRevision.v1":
        raise StaticTireError("Schema de revisão incompatível.")
    if payload.get("model_version") != __version__:
        raise StaticTireError("A revisão foi criada por outra versão do modelo.")
    if payload.get("source_sha256") != profile.base_sha256:
        raise StaticTireError("O hash do .tir não corresponde ao da revisão; overlay recusado.")
    if payload.get("axis_system") != profile.dataset.axis_system:
        raise StaticTireError("O sistema de eixos do overlay não corresponde ao perfil carregado.")
    try:
        overlay_pressure = float(payload.get("pressure_psi", math.nan))
    except (TypeError, ValueError) as exc:
        raise StaticTireError("Pressão inválida no overlay.") from exc
    if not math.isfinite(overlay_pressure) or not math.isclose(overlay_pressure, profile.inflation_psi, abs_tol=PRESSURE_TOLERANCE_PSI):
        raise StaticTireError("A pressão nominal do overlay não corresponde ao perfil.")
    if not isinstance(payload.get("overrides"), dict):
        raise StaticTireError("O campo overrides do overlay deve ser um objeto.")
    for key in ("reason", "revision_id"):
        if not isinstance(payload.get(key), str):
            raise StaticTireError(f"O campo {key} do overlay deve ser um texto.")
    for key in ("parent_revision_id", "created_at_utc"):
        if payload.get(key) is not None and not isinstance(payload[key], str):
            raise StaticTireError(f"O campo {key} do overlay deve ser texto ou nulo.")
    revised = revise_profile(
        profile,
        payload["overrides"],
        reason=payload["reason"],
        revision_id=payload["revision_id"],
    )
    return StaticTireProfile(
        dataset=_clone_dataset(revised.dataset),
        source_path=revised.source_path,
        inflation_pa=revised.inflation_pa,
        inflation_psi=revised.inflation_psi,
        base_sha256=revised.base_sha256,
        revision_id=revised.revision_id,
        revision_reason=revised.revision_reason,
        overrides=revised.overrides,
        revision_parent_id=payload.get("parent_revision_id"),
        revision_timestamp_utc=payload.get("created_at_utc"),
    )


def _validate(profile: StaticTireProfile, fz: float, alpha: float, gamma: float, kappa: float, vx: float) -> None:
    if not all(math.isfinite(v) for v in (fz, alpha, gamma, kappa, vx)):
        raise StaticTireError("Entradas devem ser finitas.")
    if vx < 0:
        raise StaticTireError("Vx deve ser >= 0 m/s.")
    if fz <= 0:
        raise StaticTireError("Fz deve ser > 0 N para avaliação estática.")
    violations = _base.in_range(profile.dataset, fz, alpha, gamma, kappa)
    if violations:
        raise _base.TireRangeError("; ".join(violations))


def inspect_profile(profile: StaticTireProfile) -> dict[str, object]:
    """Return source, format, nominal conditions, and declared-domain metadata."""
    p = profile.dataset.p
    return {
        "source": str(profile.source_path),
        "sha256": profile.base_sha256,
        "format": profile.dataset.strings.get("PROPERTY_FILE_FORMAT"),
        "tire_version": profile.dataset.strings.get("TIRE_VERSION"),
        "side": profile.dataset.side,
        "axis_system": profile.dataset.axis_system,
        "pressure_pa": profile.inflation_pa,
        "pressure_psi": profile.inflation_psi,
        "nominal_load_n": p.get("FNOMIN"),
        "reference_speed_mps": p.get("LONGVL"),
        "declared_ranges": {
            "fz_n": (p.get("FZMIN"), p.get("FZMAX")),
            "alpha_rad": (p.get("ALPMIN"), p.get("ALPMAX")),
            "camber_rad": (p.get("CAMMIN"), p.get("CAMMAX")),
            "kappa": (p.get("KPUMIN"), p.get("KPUMAX")),
        },
        "validation_status": "NOT_VALIDATED",
    }


def _mx(profile: StaticTireProfile, fz: float, fy: float, gamma: float) -> float:
    """PAC2002 overturning moment Mx, Eq. 109, Adams Tire User Guide 2022.3."""
    p = profile.dataset.p
    fz0 = p["LFZO"] * p["FNOMIN"]
    r0 = p["UNLOADED_RADIUS"]
    # These files are fitted and evaluated at IP=IP_NOM, so dpi=0.
    fy_n = fy / fz0
    fz_n = fz / fz0
    coupling = (
        _get(p, "QSX3") * fy_n
        + _get(p, "QSX4")
        * math.cos(_get(p, "QSX5") * math.atan((_get(p, "QSX6") * fz_n) ** 2))
        * math.sin(
            _get(p, "QSX7") * gamma
            + _get(p, "QSX8") * math.atan(_get(p, "QSX9") * fy_n)
        )
        + (_get(p, "QSX10") * math.atan(_get(p, "QSX11") * fz_n) - _get(p, "QSX2")) * gamma
        + _get(p, "QSX1") * _get(p, "LVMX", 1.0)
    )
    return r0 * fz * coupling * _get(p, "LMX", 1.0)


def _my(profile: StaticTireProfile, fz: float, fx: float, gamma: float, vx: float) -> float:
    """PAC2002 rolling-resistance moment My, Eq. 110, Adams Tire User Guide 2022.3."""
    p = profile.dataset.p
    fz0 = p["LFZO"] * p["FNOMIN"]
    r0 = p["UNLOADED_RADIUS"]
    vref = _get(p, "LONGVL")
    if vref <= 0:
        raise StaticTireError("LONGVL precisa ser positivo para calcular My.")
    if fz0 <= 0:
        raise StaticTireError("F'z0 precisa ser positivo para calcular My.")
    load_ratio = fz / fz0
    speed_ratio = vx / vref
    gamma_z = gamma
    terms = (
        _get(p, "QSY1")
        + _get(p, "QSY2") * (fx / fz0)
        + _get(p, "QSY3") * speed_ratio
        + _get(p, "QSY4") * speed_ratio**4
        + _get(p, "QSY5") * gamma_z**2
        + _get(p, "QSY6") * load_ratio * gamma_z**2
    )
    # Each supplied .tir is at IP=IP_NOM; the pressure ratio is therefore 1.
    return (
        -r0
        * fz
        * _get(p, "LMY", 1.0)
        * terms
        * load_ratio ** _get(p, "QSY7")
    )


def _mz(
    profile: StaticTireProfile,
    fz: float,
    alpha: float,
    gamma: float,
    kappa: float,
    fx: float,
    fy: float,
    info: Mapping[str, float],
) -> float:
    """PAC2002 aligning moment Mz, Eqs. 100-108, Adams Tire User Guide 2022.3.

    Eq. 100: Mz = -t*F'y + Mzr + s*Fx (o termo de Fx entra com sinal positivo).
    O Fy do termo de trilha usa a cambagem real (F'y = Fy - SVyk, como na
    Eq. 4.E71 do Pacejka). O help do Adams escreve F'y,gamma=0 na Eq. 103, mas o
    Pacejka só usa Fy em gamma=0 no modelo de motocicleta (seção 11.6). A escolha
    entre as duas formas está PENDENTE até a comparação com o OptimumTire
    (EDR-067, item 3): a diferença chega a ~18 N·m (~28 % do Mz) com |alpha|
    pequeno e cambagem. Até lá o código usa o Fy com cambagem real.
    """
    p = profile.dataset.p
    fz0 = p["LFZO"] * p["FNOMIN"]
    r0 = p["UNLOADED_RADIUS"]
    dfz = (fz - fz0) / fz0
    gamma_z = gamma * _get(p, "LGAZ", 1.0)
    kx, ky = float(info["Kx"]), float(info["Ky"])
    if abs(ky) < 1e-12:
        raise StaticTireError("Ky≈0; não é possível calcular os ângulos equivalentes de Mz.")
    stiffness_ratio = kx / ky
    alpha_t = alpha + _get(p, "QHZ1") + _get(p, "QHZ2") * dfz + (
        _get(p, "QHZ3") + _get(p, "QHZ4") * dfz
    ) * gamma_z
    alpha_r = alpha + float(info["SHy"]) + float(info["SVy"]) / ky

    def equivalent_angle(angle: float) -> float:
        sign = 1.0 if angle > 0 else (-1.0 if angle < 0 else 0.0)
        val = math.sqrt(math.tan(angle) ** 2 + (stiffness_ratio * kappa) ** 2)
        return math.atan(sign * val)

    alpha_t_eq = equivalent_angle(alpha_t)
    alpha_r_eq = equivalent_angle(alpha_r)
    bt = (
        (_get(p, "QBZ1") + _get(p, "QBZ2") * dfz + _get(p, "QBZ3") * dfz**2)
        * (1.0 + _get(p, "QBZ4") * gamma_z + _get(p, "QBZ5") * abs(gamma_z))
        * _get(p, "LKY", 1.0)
        / _get(p, "LMUY", 1.0)
    )
    ct = _get(p, "QCZ1")
    dt = (
        fz
        * (_get(p, "QDZ1") + _get(p, "QDZ2") * dfz)
        * (1.0 + _get(p, "QDZ3") * gamma_z + _get(p, "QDZ4") * gamma_z**2)
        * (r0 / fz0)
        * _get(p, "LTR", 1.0)
    )
    et = min(
        (_get(p, "QEZ1") + _get(p, "QEZ2") * dfz + _get(p, "QEZ3") * dfz**2)
        * (
            1.0
            + (
                _get(p, "QEZ4")
                + _get(p, "QEZ5") * gamma_z
            )
            * (2.0 / math.pi)
            * math.atan(bt * ct * alpha_t)
        ),
        1.0,
    )
    trail = _mf_cos(bt, ct, dt, et, alpha_t_eq) * math.cos(alpha)

    br = (
        _get(p, "QBZ9") * _get(p, "LKY", 1.0) / _get(p, "LMUY", 1.0)
        + _get(p, "QBZ10") * float(info["By"]) * float(info["Cy"])
    )
    dr = fz * r0 * _get(p, "LMUGAMMA", 1.0) * _get(p, "LRES", 1.0) * (
        _get(p, "QDZ6") + _get(p, "QDZ7") * dfz
        + (_get(p, "QDZ8") + _get(p, "QDZ9") * dfz) * gamma_z
    )
    residual = dr * math.cos(math.atan(br * alpha_r_eq)) * math.cos(alpha)
    offset = r0 * (
        _get(p, "SSZ1")
        + _get(p, "SSZ2") * (fy / fz0)
        + (_get(p, "SSZ3") + _get(p, "SSZ4") * dfz) * gamma
    ) * _get(p, "LS", 1.0)
    # F'y = Fy - SVyk com a cambagem real (Pacejka 4.E71; o Adams escreve F'y,gamma=0 na
    # Eq. 103). Escolha pendente até a comparação com o OptimumTire (EDR-067, item 3).
    fy_without_kappa_shift = fy - float(info["SVyk"])
    return -trail * fy_without_kappa_shift + residual + offset * fx


def evaluate_static(
    profile: StaticTireProfile,
    *,
    fz_n: float,
    alpha_rad: float,
    camber_rad: float,
    kappa: float,
    vx_mps: float,
) -> StaticTireResult:
    """Evaluate Fx/Fy and Mx/My/Mz at one steady-state operating point.

    ``alpha_rad`` and ``camber_rad`` use the axis convention explicitly supplied
    when loading the .tir; ``kappa`` is dimensionless, ``fz_n`` is positive load
    in N, and ``vx_mps`` is the longitudinal speed for the rolling moment.
    This is a single-tire local-frame calculation. Wheel mirroring and conversion
    to vehicle ISO 8855 coordinates belong to the caller.
    """
    _validate(profile, fz_n, alpha_rad, camber_rad, kappa, vx_mps)
    fx, fy, info = _base.combined_forces(
        profile.dataset, fz_n, alpha_rad, camber_rad, kappa
    )
    mx = _mx(profile, fz_n, fy, camber_rad)
    my = _my(profile, fz_n, fx, camber_rad, vx_mps)
    mz = _mz(profile, fz_n, alpha_rad, camber_rad, kappa, fx, fy, info)
    limitations = [
        "Dataset TTC R25B; não representa o R60A da equipe.",
        "Pressão suportada somente nos perfis nominais disponíveis; sem interpolação.",
        "Validation = NOT_VALIDATED contra medição independente.",
    ]
    vref = profile.dataset.p.get("LONGVL")
    if vref is not None and vx_mps > vref:
        # LONGVL é a velocidade de medição do TTC, não um limite: Fx/Fy do PAC2002 não dependem de Vx;
        # o resultado afetado é o My (QSY3*Vx/Vref e QSY4*(Vx/Vref)^4 extrapolam).
        limitations.append(
            f"Vx={vx_mps:g} m/s acima de LONGVL={vref:g} m/s (Vx/LONGVL={vx_mps / vref:.2f}; "
            "velocidade de medição do TTC): My extrapola os termos QSY3 e QSY4 fora dos dados medidos."
        )
    if all(_get(profile.dataset.p, f"QSY{i}") == 0.0 for i in range(1, 9)):
        limitations.append("QSY1..QSY8 são zero no .tir; My resulta zero da parametrização.")
    missing_moments = [key for key in MOMENT_COEFFICIENTS if key not in profile.dataset.p]
    if missing_moments:
        limitations.append(
            "Coeficientes de momento ausentes foram tratados como zero nesta implementação: "
            + ", ".join(missing_moments)
            + "."
        )
    missing_scaling = [key for key in MOMENT_SCALING_FACTORS if key not in profile.dataset.p]
    if missing_scaling:
        limitations.append(
            "Fatores de escala ausentes no .tir foram assumidos iguais a 1: "
            + ", ".join(missing_scaling)
            + "."
        )
    return StaticTireResult(
        fx_n=fx,
        fy_n=fy,
        fz_n=fz_n,
        mx_nm=mx,
        my_nm=my,
        mz_nm=mz,
        mu_effective=_base.mu_effective(fx, fy, fz_n),
        pressure_psi=profile.inflation_psi,
        speed_mps=vx_mps,
        revision_id=profile.revision_id,
        source_tir=profile.source_path.name,
        source_sha256=profile.base_sha256,
        axis_system=profile.dataset.axis_system,
        limitations=tuple(limitations),
    )
