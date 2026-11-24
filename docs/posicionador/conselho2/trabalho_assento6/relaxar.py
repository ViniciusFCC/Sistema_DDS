import json, sys, copy, time, pathlib
from multiprocessing import Pool
import numpy as np
R = pathlib.Path("/home/user/Sistema_DDS"); sys.path.insert(0, str(R/"tools")); sys.path.insert(0, str(R/"python"))
CAIXA = ([-0.15, 0.0, 0.0601], [0.15, 0.3257, 1.2574])
VARS = {"base": {}, "bump-1mm": {"curso_bump_m": 0.0614}, "droop-1mm": {"curso_droop_m": 0.022},
        "MRalvo1.44": {"mr_alvo": 1.44}, "MRvar5%": {"mr_var_max": 0.05}, "MRvar6%": {"mr_var_max": 0.06}}
def job(a):
    nome, sem = a
    from posicionador import config as pc, busca as bu, varredura as vr
    import hardpoints as hp
    cfgj = json.load(open(R/"data/posicionador/config_T11.json"))
    for k, v in VARS[nome].items(): cfgj["itens"][k]["valor"] = v
    p = pathlib.Path(f"/tmp/claude-0/cfg_{nome}.json".replace("%","p")); json.dump(cfgj, open(p,"w"))
    cfg = pc.carregar(str(p))
    hs = hp.load_hardpoints(str(R/"data/posicionador/hardpoints_T11_v10.csv"), str(R/"data/posicionador/hardpoints_T11_v10.meta.json"))
    cena = vr.cena_sem_cad(cfg)
    t=time.time(); res = bu.buscar(hs, cena, cfg, CAIXA, n_amostras=300, n_refinos=8, semente=sem)
    m = res.candidatos[0] if res.candidatos else (res.fase1.melhor if res.fase1 else None)
    out = dict(nome=nome, sem=sem, n_viaveis=len(res.candidatos), t=round(time.time()-t))
    if m is not None:
        av = m.avaliacao
        out["veredito"]=av.veredito; out["viol"]=bu.violacao(av)
        out["violadas"]=[(r.nome, round(r.folga,5) if r.folga is not None else None) for r in av.restricoes if r.estado=="VIOLADA"]
        r = av.restricao("variação de MR"); out["varMR"]=r.valor if r else None
    return out
if __name__=="__main__":
    jobs=[(n,s) for n in VARS for s in (0,1)]
    with Pool(4) as p: rs=p.map(job, jobs)
    json.dump(rs, open("relaxar.json","w"), indent=1)
    for r in rs: print(r)
