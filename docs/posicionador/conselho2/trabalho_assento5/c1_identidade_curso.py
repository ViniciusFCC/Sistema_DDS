"""Checagem independente 1: o curso usado do amortecedor é a integral de dz/MR (identidade cinemática)?
E qual o mínimo teórico dado MR(0) e a variação máxima. Lê resultados.json do benchmark; não altera nada."""
import json, sys
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(RAIZ / "python"), str(RAIZ / "tools")]
import benchmark_posicionador as bp
from posicionador import mecanismo as mec, varredura as vr
import kinematics_model as km

d = json.loads((RAIZ / "docs/posicionador/benchmark/resultados.json").read_text(encoding="utf-8"))
cfg, hs, cena = bp._juiz()
droop, bump = cfg.valor("curso_droop_m"), cfg.valor("curso_bump_m")
print(f"curso roda total = {(droop+bump)*1e3:.2f} mm ; /MR_alvo = {(droop+bump)/1.4*1e3:.3f} mm ; stroke = 61")
print(f"mínimo teórico (MR(0)=1,41 mínimo da curva, var 4%): {(droop+bump)/(1.41*1.04)*1e3:.2f} mm")
for i in [0, 13, 15, 16, 17, 18]:
    b = d["buscas"][i]
    x = b["x"]
    con = mec.construir(hs, mec.Variaveis.da_semente_do_script(x), cfg, r2_m=x[7] / 1e3)
    c = km.Corner(con.hardpoints, "FL")
    dz = np.linspace(-droop, bump, 801)
    mr = np.array([km.motion_ratio(c, float(z))["mr_wheel_per_spring"] for z in dz])
    s0 = c.solve(0.0); sols = []
    q, ph = s0.q, s0.phi
    ls = []
    for z in dz:  # continuação
        pass
    a = vr.avaliar(con, cena, cfg, 801)
    ls = a.curvas["Ls_m"]
    usado = ls.max() - ls.min()
    integ = np.trapezoid(1.0 / mr, dz)
    hm = (droop + bump) / integ
    imin = np.argmin(mr)
    print(f"[{i:2d}] {b['ferramenta']:12s} var={mr.max()/mr.min()-1:.4f} MR(0)={np.interp(0,dz,mr):.4f} "
          f"MR(-23)={mr[0]:.4f} MR(+62)={mr[-1]:.4f} argmin dz={dz[imin]*1e3:+.1f}mm | Ls max={ls.max()*1e3:.3f} "
          f"usado={usado*1e3:.3f} ∫dz/MR={integ*1e3:.3f} mm  MR harm={hm:.4f}  dMR/dz(bump)={'+' if mr[-1]>mr[len(mr)//3] else '-'}")
