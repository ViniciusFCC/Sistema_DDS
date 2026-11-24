"""E1: forma da curva de MR e identidade curso do amortecedor = ∫ dz / MR, nas 6 soluções finais do posicionador
(benchmark/resultados.json). Cena sem CAD (o juiz do benchmark). Saída: e1_saida.txt."""
import json, sys
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R / "python")); sys.path.insert(0, str(R / "tools"))
import benchmark_posicionador as B
from posicionador import mecanismo as mec, varredura as vr

cfg, hs, cena = B._juiz()
d = json.load(open(R / "docs/posicionador/benchmark/resultados.json"))
sols = [(b["rotulo"], b["x"]) for b in d["buscas"] if b["ferramenta"] == "posicionador"] + [("v20", d["x_v20"])]
for rot, x in sols:
    v = mec.Variaveis.da_semente_do_script(x)
    c = mec.construir(hs, v, cfg, r2_m=x[7] / 1000)
    av = vr.avaliar(c, cena, cfg, 201)
    dz, mr, ls = (np.asarray(av.curvas[k]) for k in ("dz_m", "MR [wheel/spring]", "Ls_m"))
    integ = np.trapezoid(1 / mr, dz)
    i0 = np.argmin(abs(dz))
    p = np.polyfit(dz, mr, 1)
    print(f"{rot:10s} MR(-23)={mr[0]:.4f} MR(0)={mr[i0]:.4f} MR(+62.4)={mr[-1]:.4f} min={mr.min():.4f} max={mr.max():.4f} "
          f"var={mr.max()/mr.min()-1:.4f} incl={p[0]*1e-3*1e3:+.5f}/mm  curso amort={1e3*(ls.max()-ls.min()):.3f} mm "
          f"∫dz/MR={1e3*integ:.3f} mm  MR harm={(dz[-1]-dz[0])/integ:.4f}  Lmin={1e3*ls.min():.3f}")
