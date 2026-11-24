"""E2: o mesmo refino Nelder-Mead do posicionador (objetivo busca._objetivo, n = 11, cena sem CAD = juiz do benchmark),
partindo das 6 soluções finais, em três parametrizações:
  A  "r2 pelo MR(0) = 1,40" (a atual; 7 variáveis) — controle: mesmo orçamento extra;
  B  "r2 livre" (8 variáveis; MR(0) vira restrição conferida em [1,39; 1,41]);
  C  "r2 pelo curso": r2 resolvido para que o curso usado do amortecedor = STROKE − folga_num (60,95 mm), 7 variáveis.
Finalistas reavaliados por busca.avaliar_convergido (o juiz). Saída: e2_saida.txt / e2_resultados.json."""
import json, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, brentq
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R / "python")); sys.path.insert(0, str(R / "tools"))

MAXFEV = int(sys.argv[1]) if len(sys.argv) > 1 else 300
ALVO_CURSO = 0.06095


def _ctx():
    import benchmark_posicionador as B
    return B._juiz()


def curso_usado(c, cena, cfg, n=11):
    from posicionador import varredura as vr
    av = vr.avaliar(c, cena, cfg, n)
    ls = av.curvas.get("Ls_m")
    return None if ls is None or len(ls) == 0 else float(np.max(ls) - np.min(ls))


def construir(modo, hs, cfg, cena, v, r2=None):
    from posicionador import mecanismo as mec
    if modo == "A":
        return mec.construir(hs, v, cfg)
    if modo == "B":
        return mec.construir(hs, v, cfg, r2_m=r2)
    # C: r2 tal que o curso usado = ALVO_CURSO (kinematics: curso cresce quando r2 cresce, MR cai)
    def g(r):
        c = mec.construir(hs, v, cfg, r2_m=r)
        if c.hardpoints is None:
            raise ValueError(c.motivo)
        s = curso_usado(c, cena, cfg, 11)
        if s is None:
            raise ValueError("sem curva")
        return s - ALVO_CURSO
    a, b = 0.6 * v.r1_m, 1.6 * v.r1_m
    try:
        ga, gb = g(a), g(b)
        if ga * gb > 0:
            return mec.Construcao(None, None, "sem r2 pelo curso")
        r = brentq(g, a, b, xtol=1e-7)
    except Exception as e:  # noqa
        return mec.Construcao(None, None, f"r2 pelo curso: {e}")
    return mec.construir(hs, v, cfg, r2_m=r)


def job(arg):
    from posicionador import busca as bu, mecanismo as mec, varredura as vr
    modo, rot, x0s = arg
    cfg, hs, cena = _ctx()
    caixa = ([-0.15, 0.0, 0.0601], [0.15, 0.3257, 1.2574])
    fx = bu.faixas(cfg, (np.array(caixa[0]), np.array(caixa[1])))
    v0 = mec.Variaveis.da_semente_do_script(x0s)
    x0 = bu._x_de(v0, fx)
    lo, hi = fx.lo.copy(), fx.hi.copy()
    if modo == "B":
        x0 = np.append(x0, x0s[7] / 1000); lo = np.append(lo, 0.055); hi = np.append(hi, 0.08)
    best = {"f": np.inf, "x": x0, "c": None}
    nf = [0]

    def f(x):
        nf[0] += 1
        xc = np.clip(x, lo, hi)
        v = bu.variaveis_de(xc[:7], fx)
        c = construir(modo, hs, cfg, cena, v, xc[7] if modo == "B" else None)
        av = bu._com_olhal(vr.avaliar(c, cena, cfg, 11), c, cfg)
        o = bu._objetivo(av)
        if o < best["f"]:
            best.update(f=o, x=xc.copy(), c=c)
        return o
    t0 = time.perf_counter()
    passo = 0.10 * (hi - lo)
    simp = [x0.copy()] + [x0 + np.eye(len(x0))[j] * (passo[j] if x0[j] + passo[j] <= hi[j] else -passo[j])
                          for j in range(len(x0))]
    minimize(f, x0, method="Nelder-Mead", options={"maxfev": MAXFEV if modo != "C" else MAXFEV // 3, "initial_simplex": np.array(simp),
                                                   "xatol": 1e-7, "fatol": 1e-10})
    c = best["c"]
    out = dict(modo=modo, rotulo=rot, f_rapido=best["f"], nfev=nf[0], tempo_s=time.perf_counter() - t0)
    if c is None or c.hardpoints is None:
        out.update(veredito="sem construção"); return out
    av = bu.avaliar_convergido(c, cena, cfg)
    vio = [(r.nome, r.valor, r.folga) for r in av.restricoes if r.estado == "VIOLADA"]
    m0 = av.restricao("MR(0)"); vm = av.restricao("variação de MR"); lm = av.restricao("comprimento do amortecedor (mínimo)")
    r2 = av.restricao("braço r2 (amortecedor)")
    out.update(veredito=av.veredito, violacao=bu.violacao(av), violadas=[(a, float(b) if np.isscalar(b) else None,
               float(cc) if cc is not None else None) for a, b, cc in vio],
               mr0=float(m0.valor), var_mr=float(vm.valor), lmin_mm=1e3 * float(lm.valor), r2_mm=1e3 * float(r2.valor),
               x=[float(a) for a in best["x"]],
               nao_verif=[r.nome for r in av.restricoes if r.estado == "NAO_VERIFICAVEL"])
    return out


if __name__ == "__main__":
    d = json.load(open(R / "docs/posicionador/benchmark/resultados.json"))
    sols = [(b["rotulo"], b["x"]) for b in d["buscas"] if b["ferramenta"] == "posicionador"]
    args = [(m, r, x) for m in "ABC" for r, x in sols]
    with mp.get_context("spawn").Pool(4) as p:
        res = p.map(job, args)
    with open(Path(__file__).with_name("e2_resultados.json"), "w") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    for o in res:
        if "mr0" not in o:
            print(o); continue
        print(f"{o['modo']} {o['rotulo']:9s} {o['veredito']:11s} viol={o['violacao']:.4f} MR0={o['mr0']:.4f} "
              f"var={100*o['var_mr']:.2f}% Lmin={o['lmin_mm']:.3f} r2={o['r2_mm']:.2f} nfev={o['nfev']} "
              f"t={o['tempo_s']:.0f}s violadas={[v[0] for v in o['violadas']]}")
