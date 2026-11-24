"""Checagem 3: erro de discretização da variação de MR e do Lmin vs n (o critério de convergência do juiz compara só estados)."""
import json, sys
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
sys.path[:0] = [str(RAIZ / "python"), str(RAIZ / "tools")]
import benchmark_posicionador as bp
from posicionador import mecanismo as mec, varredura as vr
d = json.loads((RAIZ / "docs/posicionador/benchmark/resultados.json").read_text(encoding="utf-8"))
cfg, hs, cena = bp._juiz()
for i in [13, 16, 0]:
    x = d["buscas"][i]["x"]
    con = mec.construir(hs, mec.Variaveis.da_semente_do_script(x), cfg, r2_m=x[7]/1e3)
    ref = vr.avaliar(con, cena, cfg, 801)
    vr_ = ref.restricao("variação de MR").valor; lr = ref.restricao("comprimento do amortecedor (mínimo)").valor
    out = []
    for n in (11, 25, 50, 100, 200):
        a = vr.avaliar(con, cena, cfg, n)
        out.append(f"n={n}: Δvar={(a.restricao('variação de MR').valor-vr_)*1e4:+.2f}e-4 ΔLmin={(a.restricao('comprimento do amortecedor (mínimo)').valor-lr)*1e6:+.1f}µm")
    print(f"[{i}] var(801)={vr_:.5f} Lmin(801)={lr*1e3:.4f}mm | " + " ; ".join(out))
