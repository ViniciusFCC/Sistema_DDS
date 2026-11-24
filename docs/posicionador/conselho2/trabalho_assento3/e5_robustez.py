"""E5: robustez (perturbação SINTÉTICA do benchmark: ±1 mm pivô, ±0,5° az/el/φB, ±0,5 mm r1/r2, uniforme, 40 amostras,
n = 11) das soluções de margem máxima de E3, cada uma com a sua configuração. Saída: e5_saida.txt."""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[4]
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(R / "python")); sys.path.insert(0, str(R / "tools"))
import hardpoints as hp
import benchmark_posicionador as B
from posicionador import busca as bu, config as pc, mecanismo as mec, varredura as vr

hs = hp.load_hardpoints(str(R / "data/posicionador/hardpoints_T11_v10.csv"), str(R / "data/posicionador/hardpoints_T11_v10.meta.json"))
rng = np.random.default_rng(20261123)
P = rng.uniform(-1, 1, size=(40, 8)) * np.array([1.0] * 3 + [0.5] * 2 + [0.5, 0.5, 0.5])
for o in json.load(open(AQUI / "e3_resultados.json")):
    if o["veredito"] != "CONDICIONAL" or o["rotulo"] != "semente 3":
        continue
    vr.TOL_MR0 = 0.02 if o["variante"] == "tol_mr0_0.02" else 0.01
    cfg = pc.carregar(str(AQUI / f"cfg_{o['variante']}.json"))
    cena = vr.cena_sem_cad(cfg)
    fx = bu.faixas(cfg, (np.array([-0.15, 0.0, 0.0601]), np.array([0.15, 0.3257, 1.2574])))
    xs = np.asarray(B.x_script_de(bu.variaveis_de(np.asarray(o["x"][:7]), fx), o["x"][7]))
    cont, ok = Counter(), 0
    for d in P:
        xp = xs + d
        c = mec.construir(hs, mec.Variaveis.da_semente_do_script(xp), cfg, r2_m=xp[7] / 1e3)
        av = bu._com_olhal(vr.avaliar(c, cena, cfg, 11), c, cfg)
        v = [r.nome for r in av.restricoes if r.estado == "VIOLADA"]
        ok += not v
        cont.update(v)
    print(f"{o['variante']:15s} sem violação em {ok}/40; violadas: {dict(cont)}")
