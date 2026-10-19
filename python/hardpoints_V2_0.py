"""
hardpoints_V2_0.py — schema, leitura e validação de hardpoints (V2.0).

Implementa a proposta de schema descrita em hardpoint-schema-V2.0.md. ORIGEM DO SCHEMA:
os campos `Point_ID | X | Y | Z | Component | Status` vêm da arquitetura consolidada (seção 8);
a regra de unidade explícita no nome do campo (X_m) vem da seção 10; a convenção de
eixos (ISO 8855) e o adapter Lotus vêm da seção 17.1. A convenção de Point_ID, o
vocabulário de Component/Status e os critérios de validação são PROPOSTA desta versão
(hipótese de projeto, a aprovar pelo usuário).

Este módulo NÃO resolve cinemática. Só carrega, valida e entrega pontos ao solver
(kinematics_model_V2_0.py).
"""

import csv
import json
import math
import re
from dataclasses import dataclass, field

import numpy as np

__version__ = "V2.0"
SCHEMA_VERSION = "V2.0"

CSV_COLUMNS = ["Point_ID", "X_m", "Y_m", "Z_m", "Component", "Status"]
COORDINATE_SYSTEM = "ISO8855_X_FORWARD_Y_LEFT_Z_UP"
CORNERS = ("FL", "FR", "RL", "RR")

COMPONENTS = {"CHASSIS", "RACK", "LCA", "UCA", "UPRIGHT", "WHEEL", "ROCKER"}
# SYNTHETIC = geometria de teste, NÃO representa carro; DESIGN_INTENT/AS_BUILT conforme arquitetura seção 8.
STATUS_VALUES = {"SYNTHETIC", "PROVISIONAL", "DESIGN_INTENT", "AS_BUILT"}

# chave do ponto -> conjunto de Components aceitos (Component = corpo rígido ao qual o ponto pertence)
REQUIRED_KEYS = {
    "LCA_IN_F": {"CHASSIS"}, "LCA_IN_R": {"CHASSIS"}, "LCA_OUT": {"UPRIGHT"},
    "UCA_IN_F": {"CHASSIS"}, "UCA_IN_R": {"CHASSIS"}, "UCA_OUT": {"UPRIGHT"},
    "TIE_IN": {"RACK"}, "TIE_OUT": {"UPRIGHT"},
    "WHEEL_CENTER": {"WHEEL"}, "SPINDLE_PT": {"WHEEL"}, "CONTACT_PATCH": {"WHEEL"},
}
# grupo opcional (tudo ou nada): pushrod/pullrod + rocker + mola/amortecedor
PUSH_KEYS = {
    "PUSH_OUT": {"LCA", "UCA", "UPRIGHT"}, "PUSH_IN": {"ROCKER"},
    "ROCKER_AXIS_A": {"CHASSIS"}, "ROCKER_AXIS_B": {"CHASSIS"},
    "ROCKER_SPRING": {"ROCKER"}, "SPRING_CHASSIS": {"CHASSIS"},
}
ALL_KEYS = {**REQUIRED_KEYS, **PUSH_KEYS}

META_REQUIRED = ["schema_version", "geometry_rev", "coordinate_system", "units",
                 "ground_plane_z_m", "kop", "source", "freeze_level", "timestamp"]

MAX_ABS_COORD_M = 5.0      # acima disso, quase certamente mm interpretado como m
GROUND_TOL_M = 1e-3        # tolerância do contact patch em relação ao SUS-000
MIN_LINK_M = 1e-6


class HardpointError(ValueError):
    """Erro de schema/validação de hardpoints (mensagem indica a causa e a próxima ação)."""


@dataclass
class Point:
    xyz: np.ndarray
    component: str
    status: str


@dataclass
class HardpointSet:
    meta: dict
    points: dict = field(default_factory=dict)   # Point_ID -> Point

    def corners_present(self):
        return [c for c in CORNERS if any(k.startswith(c + "_") for k in self.points)]

    def corner_points(self, corner):
        return {k[len(corner) + 1:]: p for k, p in self.points.items() if k.startswith(corner + "_")}

    def status_summary(self):
        out = {}
        for p in self.points.values():
            out[p.status] = out.get(p.status, 0) + 1
        return out


def lotus_to_iso8855(xyz):
    """Adapter Lotus -> ISO 8855 (arquitetura 17.1): X=-X, Y=-Y, Z=Z."""
    a = np.asarray(xyz, dtype=float)
    return a * np.array([-1.0, -1.0, 1.0])


def _validate_meta(meta):
    missing = [k for k in META_REQUIRED if k not in meta]
    if missing:
        raise HardpointError(f"meta sem campos obrigatórios {missing}. Preencha o .meta.json conforme o schema.")
    if str(meta["schema_version"]).split(".")[0] != SCHEMA_VERSION.split(".")[0]:
        raise HardpointError(f"schema_version {meta['schema_version']} incompatível com {SCHEMA_VERSION}.")
    if meta["coordinate_system"] != COORDINATE_SYSTEM:
        raise HardpointError(
            f"coordinate_system={meta['coordinate_system']!r}; esperado {COORDINATE_SYSTEM!r}. "
            "Converta antes (ex.: lotus_to_iso8855).")
    if meta["units"] != "m":
        raise HardpointError(f"units={meta['units']!r}; o contrato exige 'm' (sem unidade implícita).")
    g = meta["ground_plane_z_m"]
    if not isinstance(g, (int, float)) or not math.isfinite(g):
        raise HardpointError("ground_plane_z_m (SUS-000) deve ser número finito.")


def _parse_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        try:
            header = next(rd)
        except StopIteration:
            raise HardpointError("CSV vazio.")
        if [h.strip() for h in header] != CSV_COLUMNS:
            raise HardpointError(f"cabeçalho {header} != {CSV_COLUMNS}. Unidade deve estar no nome (X_m, Y_m, Z_m).")
        rows = [r for r in rd if r and any(c.strip() for c in r)]
    return rows


def build_hardpoint_set(rows, meta):
    """Valida e monta um HardpointSet a partir de linhas já lidas (listas de 6 strings)."""
    _validate_meta(meta)
    hs = HardpointSet(meta=dict(meta))
    for i, r in enumerate(rows, start=2):
        if len(r) != 6:
            raise HardpointError(f"linha {i}: esperado 6 campos, veio {len(r)}.")
        pid, x, y, z, comp, st = [c.strip() for c in r]
        m = re.fullmatch(r"(FL|FR|RL|RR)_([A-Z_]+)", pid)
        if not m:
            raise HardpointError(f"linha {i}: Point_ID {pid!r} fora do padrão <FL|FR|RL|RR>_<CHAVE>.")
        key = m.group(2)
        if key not in ALL_KEYS:
            raise HardpointError(f"linha {i}: chave {key!r} desconhecida. Chaves válidas: {sorted(ALL_KEYS)}.")
        if pid in hs.points:
            raise HardpointError(f"linha {i}: Point_ID duplicado {pid!r}.")
        try:
            xyz = np.array([float(x), float(y), float(z)])
        except ValueError:
            raise HardpointError(f"linha {i}: coordenadas não numéricas em {pid}.")
        if not np.all(np.isfinite(xyz)):
            raise HardpointError(f"linha {i}: coordenada não finita em {pid}.")
        if np.max(np.abs(xyz)) > MAX_ABS_COORD_M:
            raise HardpointError(f"linha {i}: |coord|>{MAX_ABS_COORD_M} m em {pid}: provável mm lido como m. Verifique a unidade.")
        if comp not in COMPONENTS:
            raise HardpointError(f"linha {i}: Component {comp!r} fora de {sorted(COMPONENTS)}.")
        if comp not in ALL_KEYS[key]:
            raise HardpointError(f"linha {i}: {pid} deve ter Component em {sorted(ALL_KEYS[key])}, veio {comp!r}.")
        if st not in STATUS_VALUES:
            raise HardpointError(f"linha {i}: Status {st!r} fora de {sorted(STATUS_VALUES)}.")
        hs.points[pid] = Point(xyz, comp, st)
    _validate_set(hs)
    return hs


def _validate_set(hs):
    g = hs.meta["ground_plane_z_m"]
    corners = hs.corners_present()
    if not corners:
        raise HardpointError("nenhum canto (FL/FR/RL/RR) presente.")
    for c in corners:
        pts = hs.corner_points(c)
        miss = [k for k in REQUIRED_KEYS if k not in pts]
        if miss:
            raise HardpointError(f"canto {c}: pontos obrigatórios ausentes {miss}.")
        has_push = [k for k in PUSH_KEYS if k in pts]
        if has_push and len(has_push) != len(PUSH_KEYS):
            raise HardpointError(f"canto {c}: grupo pushrod/rocker é tudo-ou-nada; ausentes "
                                 f"{[k for k in PUSH_KEYS if k not in pts]}.")
        side = +1 if c.endswith("L") else -1
        wc, sp, cp = pts["WHEEL_CENTER"].xyz, pts["SPINDLE_PT"].xyz, pts["CONTACT_PATCH"].xyz
        if side * wc[1] <= 0:
            raise HardpointError(f"canto {c}: WHEEL_CENTER.Y={wc[1]:.4f} com sinal errado para ISO 8855 "
                                 "(esquerda Y>0, direita Y<0). Suspeita: convenção Lotus não convertida.")
        if side * (sp[1] - wc[1]) <= 0:
            raise HardpointError(f"canto {c}: SPINDLE_PT deve estar para fora (outboard) do WHEEL_CENTER.")
        if abs(cp[2] - g) > GROUND_TOL_M:
            raise HardpointError(f"canto {c}: CONTACT_PATCH.Z={cp[2]:.4f} difere do solo SUS-000 ({g:.4f}) em mais de {GROUND_TOL_M} m.")
        # elos degenerados
        for a, b in (("LCA_IN_F", "LCA_IN_R"), ("UCA_IN_F", "UCA_IN_R"), ("LCA_OUT", "UCA_OUT"),
                     ("TIE_IN", "TIE_OUT"), ("LCA_OUT", "LCA_IN_F"), ("UCA_OUT", "UCA_IN_F"),
                     ("WHEEL_CENTER", "SPINDLE_PT")):
            if np.linalg.norm(pts[a].xyz - pts[b].xyz) < MIN_LINK_M:
                raise HardpointError(f"canto {c}: {a} e {b} coincidem (elo de comprimento nulo).")
        if pts["UCA_OUT"].xyz[2] <= pts["LCA_OUT"].xyz[2]:
            raise HardpointError(f"canto {c}: UCA_OUT deve estar acima de LCA_OUT (eixo do pino mestre).")
    fronts = [c for c in corners if c[0] == "F"]
    rears = [c for c in corners if c[0] == "R"]
    if fronts and rears:
        xf = np.mean([hs.corner_points(c)["WHEEL_CENTER"].xyz[0] for c in fronts])
        xr = np.mean([hs.corner_points(c)["WHEEL_CENTER"].xyz[0] for c in rears])
        if xf <= xr:
            raise HardpointError("eixo dianteiro deve ter X maior que o traseiro (X para frente, ISO 8855).")


def load_hardpoints(csv_path, meta_path):
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)
    return build_hardpoint_set(_parse_rows(csv_path), meta)


def write_hardpoints(csv_path, meta_path, hs):
    _validate_meta(hs.meta)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLUMNS)
        for pid, p in hs.points.items():
            w.writerow([pid, f"{p.xyz[0]:.9f}", f"{p.xyz[1]:.9f}", f"{p.xyz[2]:.9f}", p.component, p.status])
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(hs.meta, f, indent=2, ensure_ascii=False)
