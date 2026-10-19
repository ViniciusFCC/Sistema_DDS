"""Test Cases do hardpoints_V2_0.py (schema, leitura e validação) — V2.1: + TC-HP-101..104 (inversões isoladas, tolerância do solo, metadados, sensibilidade angular). python3 test_hardpoints_V2_1.py"""
import os, csv, json, tempfile, copy
import numpy as np
from hardpoints_V2_0 import (load_hardpoints, build_hardpoint_set, write_hardpoints, lotus_to_iso8855, HardpointError,
                             CSV_COLUMNS, REQUIRED_KEYS, PUSH_KEYS)

HERE = os.path.dirname(os.path.abspath(__file__))
CSVP, METAP = os.path.join(HERE, "hardpoints_synthetic_V2.0.csv"), os.path.join(HERE, "hardpoints_synthetic_V2.0.meta.json")
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def rows_meta():
    with open(CSVP, newline="") as f:
        r = list(csv.reader(f))
    return r[1:], json.load(open(METAP))


def fails(rows, meta, needle=None):
    try:
        build_hardpoint_set(rows, meta); return False
    except HardpointError as e:
        return needle is None or needle in str(e)


rows, meta = rows_meta()
hs = build_hardpoint_set(rows, meta)
check("TC-HP-001: arquivo sintético carrega; 2 cantos (FL, FR); todos Status=SYNTHETIC", hs.corners_present() == ["FL", "FR"] and hs.status_summary() == {"SYNTHETIC": len(rows)}, str(hs.status_summary()))
tmp = tempfile.mkdtemp()
write_hardpoints(os.path.join(tmp, "a.csv"), os.path.join(tmp, "a.json"), hs)
hs2 = load_hardpoints(os.path.join(tmp, "a.csv"), os.path.join(tmp, "a.json"))
check("TC-HP-002: escrita -> leitura reproduz as coordenadas (≤1e-9 m)", max(np.abs(hs.points[k].xyz - hs2.points[k].xyz).max() for k in hs.points) < 1e-9)
with open(CSVP) as f:
    hdr = next(csv.reader(f))
check("TC-HP-003: cabeçalho com unidade no nome (arquitetura §10)", hdr == CSV_COLUMNS and all(c.endswith("_m") for c in hdr[1:4]))

bad = copy.deepcopy(rows); bad[0][1] = "450"          # 450 m: provável mm
check("TC-HP-004: coordenada de 450 (mm lido como m) é bloqueada", fails(bad, meta, "mm"))
bad = [r for r in rows if r[0] != "FL_TIE_IN"]
check("TC-HP-005: ponto obrigatório ausente é bloqueado e nomeado", fails(bad, meta, "TIE_IN"))
bad = [r for r in rows if r[0] != "FL_PUSH_IN"]
check("TC-HP-006: grupo pushrod/rocker incompleto (tudo-ou-nada) é bloqueado", fails(bad, meta, "tudo-ou-nada"))
bad = copy.deepcopy(rows); bad[0][4] = "WHEEL"
check("TC-HP-007: Component incompatível com a chave é bloqueado", fails(bad, meta, "Component"))
bad = copy.deepcopy(rows); bad[0][5] = "FINAL"
check("TC-HP-008: Status fora do vocabulário é bloqueado", fails(bad, meta, "Status"))
bad = rows + [rows[0]]
check("TC-HP-009: Point_ID duplicado é bloqueado", fails(bad, meta, "duplicado"))
bad = copy.deepcopy(rows)
for r in bad:
    if r[0].startswith("FL_"):
        r[2] = str(-float(r[2]))
check("TC-HP-010: lado esquerdo com Y<0 (convenção Lotus/espelhada) é bloqueado com dica de conversão", fails(bad, meta, "Lotus"))
# Lotus -> ISO 8855: aplicar o adapter a um conjunto 'na convenção Lotus' recupera o original
lotus_rows = copy.deepcopy(rows)
for r in lotus_rows:
    v = lotus_to_iso8855(np.array([float(r[1]), float(r[2]), float(r[3])]))   # (-x,-y,z) é involutivo
    r[1], r[2], r[3] = f"{v[0]:.9f}", f"{v[1]:.9f}", f"{v[2]:.9f}"
check("TC-HP-011a: dado em convenção Lotus (X,Y invertidos) é rejeitado pelo teste de lado/eixo", fails(lotus_rows, meta))
back = copy.deepcopy(lotus_rows)
for r in back:
    v = lotus_to_iso8855(np.array([float(r[1]), float(r[2]), float(r[3])])); r[1], r[2], r[3] = f"{v[0]:.9f}", f"{v[1]:.9f}", f"{v[2]:.9f}"
check("TC-HP-011b: adapter Lotus->ISO8855 aplicado de volta recupera o conjunto válido", not fails(back, meta))
m2 = dict(meta); m2["units"] = "mm"
check("TC-HP-012a: units != 'm' bloqueado", fails(rows, m2, "units"))
m2 = dict(meta); m2["coordinate_system"] = "LOTUS"
check("TC-HP-012b: coordinate_system diferente de ISO 8855 bloqueado", fails(rows, m2, "coordinate_system"))
m2 = {k: v for k, v in meta.items() if k != "geometry_rev"}
check("TC-HP-012c: meta sem campo obrigatório bloqueado", fails(rows, m2, "geometry_rev"))
m2 = dict(meta); m2["ground_plane_z_m"] = 0.05
check("TC-HP-013: contact patch fora do solo SUS-000 (>1 mm) bloqueado", fails(rows, m2, "SUS-000"))
bad = copy.deepcopy(rows)
for r in bad:
    if r[0] == "FL_UCA_OUT":
        r[3] = "0.100"
check("TC-HP-014: UCA_OUT abaixo de LCA_OUT bloqueado", fails(bad, meta, "UCA_OUT"))
bad = copy.deepcopy(rows)
for r in bad:
    if r[0] == "FL_LCA_IN_R":
        r[1:4] = [x for x in [r2 for r2 in rows if r2[0] == "FL_LCA_IN_F"][0][1:4]]
check("TC-HP-015: elo de comprimento nulo (pivôs coincidentes) bloqueado", fails(bad, meta, "coincidem"))
bad = copy.deepcopy(rows)
for r in bad:
    if r[0] == "FL_SPINDLE_PT":
        r[2] = "0.5"
check("TC-HP-016: SPINDLE_PT para dentro do centro da roda bloqueado", fails(bad, meta, "outboard"))
check("TC-HP-017: linha malformada (campos != 6) bloqueada", fails([["FL_LCA_OUT", "1", "2"]], meta, "6 campos"))
check("TC-HP-018: chave desconhecida bloqueada", fails([["FL_FOO", "0", "0.5", "0.1", "CHASSIS", "SYNTHETIC"]], meta, "desconhecida"))


# =====================================================================
# V2.1 — auditoria D2 (EDR-024) e D7 (EDR-030). Testes de CARACTERIZAÇÃO documentam o comportamento ATUAL,
# inclusive lacunas conhecidas (GAP-HP-xxx); não alteram o módulo.
# =====================================================================
def two_axles(rows):
    out = copy.deepcopy(rows)
    for r in rows:                      # eixo traseiro SINTÉTICO de teste: cópia do dianteiro deslocada 1,55 m para trás
        c = copy.deepcopy(r); c[0] = "R" + r[0][1:]; c[1] = str(float(r[1]) - 1.55); out.append(c)
    return out

def flip(rows, axes):
    out = copy.deepcopy(rows)
    for r in out:
        for ax in axes:
            i = {"X": 1, "Y": 2, "Z": 3}[ax]; r[i] = str(-float(r[i]))
    return out

check("TC-HP-101a: Y invertido isolado (eixo único) é rejeitado (checagem de lado)", fails(flip(rows, "Y"), meta))
check("TC-HP-101b: Z invertido isolado é rejeitado (solo/contact patch ou UCA abaixo de LCA)", fails(flip(rows, "Z"), meta))
check("TC-HP-101c: CARACTERIZAÇÃO (GAP-HP-001) — X invertido isolado em eixo ÚNICO é ACEITO: a checagem de lado só enxerga Y",
      not fails(flip(rows, "X"), meta))
check("TC-HP-101d: X invertido isolado com DOIS eixos é rejeitado (ordem dianteiro/traseiro)", fails(flip(two_axles(rows), "X"), meta, "X maior"))
check("TC-HP-101e: X e Y invertidos (Lotus) em eixo único é rejeitado pelo Y", fails(flip(rows, "XY"), meta))
check("TC-HP-101f: conjunto de dois eixos sintético válido é aceito (fixture de teste)", not fails(two_axles(rows), meta))

def shift_cp(rows, dz):
    out = copy.deepcopy(rows)
    for r in out:
        if r[0].endswith("_CONTACT_PATCH"):
            r[3] = str(float(r[3]) + dz)
    return out
check("TC-HP-102a: contact patch 0,4 mm acima do solo é aceito", not fails(shift_cp(rows, 0.0004), meta))
check("TC-HP-102b: 1,0 mm (limite exato) aceito; 1,2 mm rejeitado — CARACTERIZAÇÃO: regra rígida de 1 mm, sem modo warning (GAP-HP-003)",
      not fails(shift_cp(rows, 0.0010), meta) and fails(shift_cp(rows, 0.0012), meta, "SUS-000"))

m2 = dict(meta); m2["source_coordinate_system"] = "UNKNOWN"
check("TC-HP-103a: CARACTERIZAÇÃO (GAP-HP-002) — convenção de origem declarada 'UNKNOWN' no meta é aceita silenciosamente (campo ignorado)", not fails(rows, m2))
from hardpoints_V2_0 import META_REQUIRED
check("TC-HP-103b: CARACTERIZAÇÃO (GAP-HP-002) — META_REQUIRED não inclui convenção de origem, transformação aplicada, ferramenta/versão de origem nem estado de conhecimento",
      not any(k in META_REQUIRED for k in ("source_coordinate_system", "transform_applied", "source_tool", "source_tool_version", "convention_status")))

# ---- D7: verificação numérica da relação de propagação de incerteza angular (hipótese a verificar) ----
rng = np.random.default_rng(20261010)
def mc_sigma(d, sigma, N=60000, comp="z"):
    n = rng.normal(0.0, sigma, size=(N, 2))              # erro de coordenada (m) nos dois pontos, 1 componente
    if comp == "z":                                       # camber: eixo (0, cos γ, -sin γ) com γ=0 -> a_z = Δz/|Δ|
        a = np.stack([np.zeros(N), np.full(N, d), n[:, 1] - n[:, 0]], axis=1)
        ang = np.degrees(np.arcsin(-a[:, 2] / np.linalg.norm(a, axis=1)))
    else:                                                 # toe: a_x = Δx / |Δ_xy|
        a = np.stack([n[:, 1] - n[:, 0], np.full(N, d), np.zeros(N)], axis=1)
        ang = np.degrees(np.arcsin(-a[:, 0] / np.hypot(a[:, 0], a[:, 1])))
    return float(np.std(ang))
ok_c = ok_t = True; det = []
for d in (0.08, 0.16, 0.32):
    pred = np.degrees(np.sqrt(2) * 1e-4 / d)
    sc, st = mc_sigma(d, 1e-4, comp="z"), mc_sigma(d, 1e-4, comp="x")
    ok_c &= abs(sc / pred - 1) < 0.03; ok_t &= abs(st / pred - 1) < 0.03
    det.append((d, round(pred, 4), round(sc, 4)))
check("TC-HP-104a: σ_camber ≈ √2·σ_z/d (1ª ordem; só erro em Z entra), 3 distâncias, tolerância 3% (Monte Carlo, N=60000)", ok_c, f"(d, previsto°, MC°)={det}")
check("TC-HP-104b: σ_toe ≈ √2·σ_x/d (1ª ordem; só erro em X entra), 3 distâncias", ok_t)
dmin = np.sqrt(2) * 1e-4 / np.radians(0.05)
check("TC-HP-104c: d_min = √2·σ_coord/σ_γ,alvo reproduz o σ_γ alvo (exemplo ARITMÉTICO σ=0,1 mm, alvo 0,05°; não é critério do Tupã)",
      abs(mc_sigma(dmin, 1e-4) / 0.05 - 1) < 0.03, f"d_min={dmin:.4f} m")
# arredondamento do CSV: 6 vs 9 casas na geometria sintética
from hardpoints_V2_0 import load_hardpoints
hsx = load_hardpoints(CSVP, METAP).corner_points("FL")
def cam(wc, sp):
    a = sp - wc; return np.degrees(np.arcsin(-a[2] / np.linalg.norm(a)))
c_ref = cam(hsx["WHEEL_CENTER"].xyz, hsx["SPINDLE_PT"].xyz)
c6 = cam(np.round(hsx["WHEEL_CENTER"].xyz, 6), np.round(hsx["SPINDLE_PT"].xyz, 6))
c9 = cam(np.round(hsx["WHEEL_CENTER"].xyz, 9), np.round(hsx["SPINDLE_PT"].xyz, 9))
check("TC-HP-104d: arredondamento do CSV: 6 casas decimais gera erro angular ≥1e-5° e <5e-4° na base de 0,08 m; 9 casas <1e-6°",
      1e-5 < abs(c6 - c_ref) < 5e-4 and abs(c9 - c_ref) < 1e-6, f"erro 6 casas={abs(c6-c_ref):.2e}°, 9 casas={abs(c9-c_ref):.1e}°")

print("\n--- Resumo ---")
p = sum(1 for _, s in results if s == "PASS"); f = len(results) - p
print(f"{p} PASS, {f} FAIL, de {len(results)} testes")
if f: raise SystemExit(1)
