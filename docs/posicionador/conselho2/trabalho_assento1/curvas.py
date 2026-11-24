"""Parte 1: curvas MR(dz) e Ls(dz) dos 6 melhores do posicionador (benchmark); identidade curso = ∫dz/MR."""
import json, sys
from pathlib import Path
import numpy as np
RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "python"))
import hardpoints as hp, kinematics_model as km
from posicionador import config as pc, mecanismo as mec

cfg = pc.carregar(str(RAIZ / "data/posicionador/config_T11.json"))
hs = hp.load_hardpoints(str(RAIZ / "data/posicionador/hardpoints_T11_v10.csv"),
                        str(RAIZ / "data/posicionador/hardpoints_T11_v10.meta.json"))
res = json.load(open(RAIZ / "docs/posicionador/benchmark/resultados.json"))
droop, bump = cfg.valor("curso_droop_m"), cfg.valor("curso_bump_m")


def curvas(c, n=201):
    canto = km.Corner(c.hardpoints, "FL")
    dzs = np.linspace(-droop, bump, n)
    s0 = canto.solve(0.0); sol = {}
    for g in (sorted(d for d in dzs if d >= 0), sorted((d for d in dzs if d < 0), reverse=True)):
        cur = s0
        for d in g:
            cur = canto.solve(float(d), q0=cur.q, phi0=cur.phi); sol[float(d)] = cur
    ls = np.array([canto.spring_length(sol[float(d)]) for d in dzs])
    mr = np.array([km.motion_ratio(canto, float(d))["mr_wheel_per_spring"] for d in dzs])
    th = np.array([sol[float(d)].phi for d in dzs])
    return dzs, ls, mr, th


saida = []
for b in res["buscas"] + [{"rotulo": "v20", "x": res["x_v20"], "ferramenta": "v20"}]:
    if b["ferramenta"] == "script":
        continue
    x = b["x"]
    v = mec.Variaveis.da_semente_do_script(x)
    c = mec.construir(hs, v, cfg, r2_m=x[7] / 1000)
    dzs, ls, mr, th = curvas(c)
    curso = ls.max() - ls.min()
    integ = np.trapezoid(1 / mr, dzs)
    H = (bump + droop) / integ
    i0 = np.argmin(abs(dzs))
    p = np.polyfit(dzs * 1e3, mr, 2)
    linha = dict(rotulo=b["rotulo"], mr0=float(mr[i0]), var=float(mr.max() / mr.min() - 1), curso_mm=curso * 1e3,
                 integ_mm=integ * 1e3, harm=H, mr_min=float(mr.min()), mr_max=float(mr.max()),
                 dz_min_mr=float(dzs[mr.argmin()] * 1e3), dz_max_mr=float(dzs[mr.argmax()] * 1e3),
                 inclin_por_m=float(p[1] * 1e3), curv=float(p[0] * 1e6), giro_graus=float(np.degrees(th.max() - th.min())),
                 Lmin_mm=float(ls.min() * 1e3), Lmax_mm=float(ls.max() * 1e3))
    saida.append(linha)
    print(f"{linha['rotulo']:<12} MR0={linha['mr0']:.4f} var={linha['var']*100:.2f}% curso={linha['curso_mm']:.3f} "
          f"∫dz/MR={linha['integ_mm']:.3f} H={H:.4f} MRmin {linha['mr_min']:.4f}@{linha['dz_min_mr']:.1f} "
          f"MRmax {linha['mr_max']:.4f}@{linha['dz_max_mr']:.1f} dMR/dz={linha['inclin_por_m']:.3f}/m "
          f"giro={linha['giro_graus']:.1f}° L=[{linha['Lmin_mm']:.2f};{linha['Lmax_mm']:.2f}]")
json.dump(saida, open(Path(__file__).with_name("curvas.json"), "w"), indent=1)
