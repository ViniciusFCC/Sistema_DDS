"""Parte 4: refino dos dois melhores com δ livre (n = 61 no avaliador rápido, margens pequenas) e juiz completo."""
import json, sys
import numpy as np
from scipy.optimize import minimize
import fase
from posicionador import varredura as vr
fase.NRAP = 61
cena = vr.cena_sem_cad(fase.cfg)
runs = [json.loads(l) for l in open("runs.jsonl")]
sem = int(sys.argv[1]); modo = sys.argv[2] if len(sys.argv) > 2 else "dlivre"
r0 = next(r for r in runs if r["modo"] == modo and r["objetivo"] == "viavel" and r["semente"] == sem)
x0 = np.array(r0["x"])
def f(z):
    x = z if modo == "dlivre" else np.concatenate([z, [0.0]])
    c = fase.construir(x)
    if c is None: return 1e6
    try: m = fase.medir(c)
    except Exception: return 1e6
    p = max(0, m["var"] - 0.0390) * 1000 + max(0, 149.05 - m["lmin_mm"]) * 10 + max(0, m["lmax_mm"] - 210) * 10
    for rr in (m["r1"], m["r2"]): p += max(0, 55.05 - rr, rr - 79.95)
    p += max(0, m["giro"] - 60) + max(0, m["ang"] - 29.9)
    return p
z0 = x0 if modo == "dlivre" else x0[:7]
passo = np.array([4, 4, 4, 1, 1, 1, 2, 2])[:len(z0)]
simp = np.vstack([z0] + [z0 + np.eye(len(z0))[i] * passo[i] for i in range(len(z0))])
r = minimize(f, z0, method="Nelder-Mead", options=dict(maxfev=500, initial_simplex=simp, fatol=1e-9, xatol=1e-4))
x = r.x if modo == "dlivre" else np.concatenate([r.x, [0.0]])
av = vr.avaliar_convergido(fase.construir(x), cena, fase.cfg)
viol = [(q.nome, q.folga) for q in av.restricoes if q.estado == "VIOLADA"]
print(json.dumps(dict(sem=sem, modo=modo, x=list(map(float, x)), f=float(r.fun), veredito=av.veredito, n=av.resolucoes,
      var=av.restricao("variação de MR").valor, lmin=av.restricao("comprimento do amortecedor (mínimo)").valor,
      folgas={q.nome: q.folga for q in av.restricoes if q.folga is not None}, viol=viol, motivo=av.motivo)))
