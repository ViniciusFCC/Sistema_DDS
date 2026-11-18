"""Captura, uma vez, os dados do T11 e a solução v20 do script de atuação (Murilo) para o posicionador (EDR-076).

Uso: uv run python -I -X utf8 tools/capturar_v20_murilo.py PASTA_DO_SCRIPT [--saida data/posicionador]
O script (t11_atuacao.py, kinlib.py, geometria_T11.json) nunca entra no repositório: só as saídas e o SHA-256 da origem.
Escreve hardpoints_T11_v10, hardpoints_T11_v20_murilo (csv + meta), curvas_kinlib_v20.csv e origem_v20_murilo.json.
"""
import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np

import hardpoints as hp

ARQUIVOS = ("t11_atuacao.py", "kinlib.py", "geometria_T11.json")
CONFIG = ("DROOP", "BUMP", "EYE", "STROKE", "MR_ALVO", "MR_VAR_MAX", "DJ", "ARM", "LADO_ROCKER", "BRACO_MIN", "BRACO_MAX",
          "GIRO_MAX", "AMORT_ANG_MAX", "FOLGA_ARO", "FOLGA_PERNAS", "FOLGA_PROD_AMORT", "DENTRO_MIN", "Z_GAB", "MEIA_LARG",
          "CHANFRO", "FOLGA_GAB", "R_MOLA", "R_JUNTA", "R_PIVO", "R_PROD", "R_TUBO", "DOFF", "FH0", "FH1", "ERRO_FH_MAX",
          "X_FBH", "X_FIM_GABARITO")
N_PONTOS, DZ_MIN_M, DZ_MAX_M = 401, -0.023, 0.0624
V10_MAP = (("LCA_IN_F", "LF", "CHASSIS"), ("LCA_IN_R", "LR", "CHASSIS"), ("LCA_OUT", "LO", "UPRIGHT"),
           ("UCA_IN_F", "UF", "CHASSIS"), ("UCA_IN_R", "UR", "CHASSIS"), ("UCA_OUT", "UO", "UPRIGHT"),
           ("TIE_IN", "TI", "RACK"), ("TIE_OUT", "TO", "UPRIGHT"), ("WHEEL_CENTER", "WC", "WHEEL"))


def sha256(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _num(v):
    if isinstance(v, np.ndarray):
        return [float(a) for a in v]
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    return v


def _meta(rev, source):
    return {"schema_version": "V2.0", "geometry_rev": rev, "coordinate_system": hp.COORDINATE_SYSTEM, "units": "m",
            "ground_plane_z_m": 0.0, "kop": "altura estática de projeto (v10)", "source": source, "freeze_level": "F0",
            "timestamp": "2026-11-17T00:00:00-03:00"}


def _linhas(pontos):
    return [[pid, f"{xyz[0]:.9f}", f"{xyz[1]:.9f}", f"{xyz[2]:.9f}", comp, "PROVISIONAL"] for pid, xyz, comp in pontos]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "posicionador"))
    a = ap.parse_args(argv)
    pasta = os.path.abspath(a.pasta)
    sys.dont_write_bytecode = True
    sys.path.insert(0, pasta)
    import t11_atuacao as t   # noqa: E402  (script de terceiros, lido de fora do repositório)

    x = [float(v) for v in t.carregar_x()]
    c = t.corner()
    g = t.avaliar(np.array(x), c, final=True)
    if g is None:
        raise SystemExit("avaliar(final=True) devolveu None para a semente v20")
    dz_m = np.linspace(DZ_MIN_M, DZ_MAX_M, N_PONTOS)
    r = t.varrer(c, g, list(dz_m * 1000.0))
    if r is None:
        raise SystemExit("varrer falhou em algum ponto da faixa")

    P = {k: np.array(v, float) / 1000.0 for k, v in t.GEO["dianteira"].items()}
    wc = P["WC"]
    v10 = [(f"FL_{k}", P[m], comp) for k, m, comp in V10_MAP]
    v10 += [("FL_SPINDLE_PT", wc + np.array([0.0, 0.05, 0.0]), "WHEEL"), ("FL_CONTACT_PATCH", np.array([wc[0], wc[1], 0.0]), "WHEEL")]
    mm = lambda k: np.asarray(g[k], float) / 1000.0
    pv, n = mm("Pv"), np.asarray(g["n"], float)
    v20 = v10 + [("FL_PUSH_OUT", mm("O0"), "LCA"), ("FL_PUSH_IN", mm("A0"), "ROCKER"), ("FL_ROCKER_AXIS_A", pv, "CHASSIS"),
                 ("FL_ROCKER_AXIS_B", pv + 0.05 * n, "CHASSIS"), ("FL_ROCKER_SPRING", mm("B0"), "ROCKER"),
                 ("FL_SPRING_CHASSIS", mm("C"), "CHASSIS")]
    src10 = ("geometria_T11.json do script de atuação (Murilo), recebido 2026-11-17; SPINDLE_PT e CONTACT_PATCH são HIPÓTESE "
             "do kinlib (camber e toe estáticos nulos, solo em Z = 0)")
    src20 = ("v10 mais a solução v20 (semente de t11_atuacao.py, avaliar(final=True)) do script de atuação (Murilo), recebido "
             "2026-11-17; " + src10.split("; ", 1)[1])
    os.makedirs(a.saida, exist_ok=True)
    for nome, pts, rev, src in (("hardpoints_T11_v10", v10, "T11-v10 (LR −6 mm)", src10),
                                ("hardpoints_T11_v20_murilo", v20, "T11-v20 (Murilo)", src20)):
        hs = hp.build_hardpoint_set(_linhas(pts), _meta(rev, src))
        hp.write_hardpoints(os.path.join(a.saida, nome + ".csv"), os.path.join(a.saida, nome + ".meta.json"), hs)

    C = np.asarray(g["C"], float)
    with open(os.path.join(a.saida, "curvas_kinlib_v20.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dz_m", "Ls_m", "theta_rocker_rad"])
        for q in r:
            w.writerow([f"{q['dz'] / 1000.0:.9f}", f"{np.linalg.norm(np.asarray(q['B']) - C) / 1000.0:.9f}", f"{q['th']:.12f}"])

    origem = {"arquivos": {nm: sha256(os.path.join(pasta, nm)) for nm in ARQUIVOS}, "x_semente": x,
              "config_do_script": {k: _num(getattr(t, k)) for k in CONFIG},
              "unidades": "config_do_script nas unidades do script: comprimentos em mm, ângulos em graus (MR_ALVO e MR_VAR_MAX "
                          "adimensionais; DENTRO_MIN em %; ARM e LADO_ROCKER são seletores); x_semente: [X, Y, Z do pivô do rocker em mm, "
                          "azimute e elevação do amortecedor em graus, r1 em mm, ângulo entre braços em graus, r2 em mm]",
              "data": "2026-11-17"}
    with open(os.path.join(a.saida, "origem_v20_murilo.json"), "w", encoding="utf-8") as f:
        json.dump(origem, f, indent=2, ensure_ascii=False)
    print(f"gerado em {os.path.abspath(a.saida)}: MR={g['MR']:.4f}, {len(r)} pontos de curva")


if __name__ == "__main__":
    main()
