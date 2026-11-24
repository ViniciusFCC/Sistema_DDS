"""E3: quanto de margem uniforme cabe (centro de Chebyshev aproximado) e quanto cada relaxamento compra.
Parametrização B (r2 livre, 8 variáveis), Nelder-Mead, n = 11, cena sem CAD (juiz do benchmark), partindo das duas
soluções CONDICIONAL de E2/B (sementes 3 e 5). Objetivo: 1 + violação se viola; senão −(menor folga normalizada das
restrições numéricas OK, mesma escala de busca.violacao_restricao). Finais reavaliados por avaliar_convergido.
Relaxamentos (PROPOSTAS de teste, nunca valor do carro): config copiada em cfg_<nome>.json nesta pasta.
Saída: e3_saida.txt / e3_resultados.json."""
import copy, json, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
R = Path(__file__).resolve().parents[4]
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(R / "python")); sys.path.insert(0, str(R / "tools"))
MAXFEV = 250
VARIANTES = {"base": {}, "tol_mr0_0.02": {"_TOL_MR0": 0.02}, "braco_max_85mm": {"braco_max_m": 0.085},
             "var_mr_5pct": {"mr_var_max": 0.05}, "bump_61.4mm": {"curso_bump_m": 0.0614}}


def cfg_de(nome):
    from posicionador import config as pc
    base = json.load(open(R / "data/posicionador/config_T11.json"))
    d = copy.deepcopy(base)
    for k, v in VARIANTES[nome].items():
        if not k.startswith("_"):
            d["itens"][k]["valor"] = v
            d["itens"][k]["fonte"] = "TESTE do conselho (relaxamento hipotético; não é dado do carro). " + d["itens"][k]["fonte"]
    p = AQUI / f"cfg_{nome}.json"
    json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
    return pc.carregar(str(p))


def folga_min(av):
    from posicionador import busca as bu
    best, quem = np.inf, None
    for r in av.restricoes:
        if r.estado != "OK" or r.folga is None or r.nome == "comprimento do amortecedor (máximo)":
            continue  # o máximo é igualdade por construção (C posto a EYE no droop); ver e3a_* (rodada degenerada)
        neg = copy.copy(r); neg.estado = "VIOLADA"; neg.folga = -float(r.folga)
        s = bu.violacao_restricao(neg)
        if s < best:
            best, quem = s, r.nome
    return best, quem


def job(arg):
    import hardpoints as hp
    from posicionador import busca as bu, mecanismo as mec, varredura as vr
    nome, rot, xb = arg
    if "_TOL_MR0" in VARIANTES[nome]:
        vr.TOL_MR0 = VARIANTES[nome]["_TOL_MR0"]
    cfg = cfg_de(nome)
    hs = hp.load_hardpoints(str(R / "data/posicionador/hardpoints_T11_v10.csv"),
                            str(R / "data/posicionador/hardpoints_T11_v10.meta.json"))
    cena = vr.cena_sem_cad(cfg)
    caixa = (np.array([-0.15, 0.0, 0.0601]), np.array([0.15, 0.3257, 1.2574]))
    fx = bu.faixas(cfg, caixa)
    lo = np.append(fx.lo, float(cfg.valor("braco_min_m"))); hi = np.append(fx.hi, float(cfg.valor("braco_max_m")))
    x0 = np.clip(np.asarray(xb, float), lo, hi)
    best = {"f": np.inf, "c": None, "x": x0}

    def f(x):
        xc = np.clip(x, lo, hi)
        c = mec.construir(hs, bu.variaveis_de(xc[:7], fx), cfg, r2_m=xc[7])
        av = bu._com_olhal(vr.avaliar(c, cena, cfg, 11), c, cfg)
        v = bu.violacao(av)
        o = 1e6 if not np.isfinite(v) else (1.0 + v if v > 0 else -folga_min(av)[0])
        if o < best["f"]:
            best.update(f=o, c=c, x=xc.copy())
        return o
    t0 = time.perf_counter()
    passo = 0.05 * (hi - lo)
    simp = [x0] + [x0 + np.eye(8)[j] * (passo[j] if x0[j] + passo[j] <= hi[j] else -passo[j]) for j in range(8)]
    minimize(f, x0, method="Nelder-Mead", options={"maxfev": MAXFEV, "initial_simplex": np.array(simp)})
    av = bu.avaliar_convergido(best["c"], cena, cfg)
    s, quem = folga_min(av) if av.veredito != "INVIAVEL" else (None, None)
    g = lambda n: av.restricao(n)
    ativos = sorted(((bu.violacao_restricao(type("r", (), dict(estado="VIOLADA", folga=-float(r.folga), limite=r.limite,
                    valor=r.valor))()), r.nome, float(r.folga)) for r in av.restricoes
                    if r.estado == "OK" and r.folga is not None))[:5]
    return dict(variante=nome, rotulo=rot, veredito=av.veredito, folga_min_norm=s, restricao_mais_apertada=quem,
                mr0=float(g("MR(0)").valor), var_mr=float(g("variação de MR").valor),
                lmin_mm=1e3 * float(g("comprimento do amortecedor (mínimo)").valor),
                r2_mm=1e3 * float(g("braço r2 (amortecedor)").valor), cinco_mais_apertadas=ativos,
                violadas=[r.nome for r in av.restricoes if r.estado == "VIOLADA"], tempo_s=time.perf_counter() - t0,
                x=[float(a) for a in best["x"]])


if __name__ == "__main__":
    e2 = json.load(open(AQUI / "e2_resultados.json"))
    starts = [(o["rotulo"], o["x"]) for o in e2 if o["modo"] == "B" and o["veredito"] == "CONDICIONAL"]
    args = [(n, r, x) for n in VARIANTES for r, x in starts]
    with mp.get_context("spawn").Pool(4) as p:
        res = p.map(job, args)
    json.dump(res, open(AQUI / "e3_resultados.json", "w"), indent=1, ensure_ascii=False)
    for o in res:
        print(f"{o['variante']:15s} {o['rotulo']:9s} {o['veredito']:11s} folga_min={o['folga_min_norm']} "
              f"({o['restricao_mais_apertada']}) MR0={o['mr0']:.4f} var={100*o['var_mr']:.2f}% Lmin={o['lmin_mm']:.3f} "
              f"r2={o['r2_mm']:.2f} violadas={o['violadas']}")
        for s, nm, fo in o["cinco_mais_apertadas"]:
            print(f"      {nm}: folga {fo:.5g} (norm {s:.4f})")
