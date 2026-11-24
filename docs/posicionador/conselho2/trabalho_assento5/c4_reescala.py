"""Checagem 4: a busca não achou viável por conflito ou pela escala do objetivo? Refino Nelder-Mead a partir dos 4 melhores
do benchmark (sem CAD, config base, NADA relaxado), com objetivo reescalado: violação do comprimento mínimo em mm (não
em fração de 149 mm) e as demais como no posicionador; viável → maximiza a menor folga normalizada (margem). Juiz final:
avaliar_convergido + olhal (o mesmo do benchmark)."""
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[3]
sys.path[:0] = [str(RAIZ / "python"), str(RAIZ / "tools")]
import benchmark_posicionador as bp
from posicionador import mecanismo as mec, varredura as vr, busca as bu
d = json.loads((RAIZ / "docs/posicionador/benchmark/resultados.json").read_text(encoding="utf-8"))
cfg, hs, cena = bp._juiz()
ESC = {"comprimento do amortecedor (mínimo)": 1e-3, "variação de MR": 0.004, "MR(0)": 0.01}  # 1 mm; 0,4 p.p.; 0,01

def obj(av):
    if bu.tipo_falha(av) is not None: return 1e6
    worst, slack = 0.0, np.inf
    for r in av.restricoes:
        if r.folga is None or r.estado == "NAO_VERIFICAVEL": continue
        e = ESC.get(r.nome)
        if e is None:
            e = bu.ESCALA_LIMITE_NULO if not r.limite or (not isinstance(r.limite,(list,tuple)) and float(r.limite)==0) else (abs(float(r.limite)) if not isinstance(r.limite,(list,tuple)) else abs(float(r.limite[1])))
        f = float(r.folga) / e
        slack = min(slack, f)
        if r.estado == "VIOLADA": worst = max(worst, -f)
    return worst if worst > 0 else -min(slack, 1.0)

def ev(xs, n=11):
    x = np.asarray(xs, float).copy(); x[7] = 0  # r2 re-resolvido por construção
    v = mec.Variaveis.da_semente_do_script(x)
    c = mec.construir(hs, v, cfg)
    if c.hardpoints is None: return None, None
    return c, bu._com_olhal(vr.avaliar(c, cena, cfg, n), c, cfg)

for i in [13, 15, 16, 17]:
    t = time.time(); x0 = np.asarray(d["buscas"][i]["x"][:7], float)
    best = [None, 1e9]
    def f(x7):
        c, av = ev(list(x7) + [0])
        o = 1e6 if av is None else obj(av)
        if o < best[1]: best[:] = [x7.copy(), o]
        return o
    step = np.array([5, 5, 5, 2, 2, 2, 5.0])
    sim = [x0] + [x0 + np.eye(7)[j] * step[j] for j in range(7)]
    minimize(f, x0, method="Nelder-Mead", options={"maxfev": 260, "initial_simplex": np.array(sim), "xatol": 1e-4, "fatol": 1e-7})
    c, _ = ev(list(best[0]) + [0])
    av = bu._com_olhal(vr.avaliar_convergido(c, cena, cfg), c, cfg)
    var = av.restricao("variação de MR"); lm = av.restricao("comprimento do amortecedor (mínimo)")
    vio = [r.nome for r in av.restricoes if r.estado == "VIOLADA"]
    ap = [(r.nome, round(r.folga*1e3, 2)) for r in av.restricoes if r.folga is not None and r.estado=="OK" and abs(r.folga) < 2e-3]
    print(f"[{i}] obj={best[1]:+.4f} juiz={av.veredito} var={var.valor:.4f} Lmin folga={lm.folga*1e3:+.3f} mm violadas={vio} "
          f"apertadas(<2e-3 SI)={ap} x={np.round(best[0],2).tolist()} r2={c.r2_m*1e3:.2f} {time.time()-t:.0f}s", flush=True)
