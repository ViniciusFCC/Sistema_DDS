"""Rejulga as 6 soluções finais do posicionador (benchmark) variando o curso de bump e a margem de fim de curso.
Valores de curso/margem aqui são CENÁRIOS para a equipe decidir, não dado do carro. Config original nunca é editada."""
import copy, json, sys, time
from pathlib import Path
RAIZ = Path("/home/user/Sistema_DDS")
sys.path.insert(0, str(RAIZ / "python")); sys.path.insert(0, str(RAIZ / "tools"))
import benchmark_posicionador as bp
from posicionador import config as pc, varredura as vr
import hardpoints as hp

OUT = Path(__file__).parent
base = json.load(open(RAIZ / "data/posicionador/config_T11.json"))
res = json.load(open(RAIZ / "docs/posicionador/benchmark/resultados.json"))
sols = [b for b in res["buscas"] if b["ferramenta"] == "posicionador"]
hs = hp.load_hardpoints(str(RAIZ / "data/posicionador/hardpoints_T11_v10.csv"),
                        str(RAIZ / "data/posicionador/hardpoints_T11_v10.meta.json"))

def cfg_com(bump_mm, margem_mm):
    d = copy.deepcopy(base)
    d["itens"]["curso_bump_m"]["valor"] = bump_mm / 1000
    d["itens"]["curso_bump_m"]["fonte"] = "CENARIO assento 7"
    if margem_mm is not None:
        d["itens"]["margem_curso_amortecedor_m"] = dict(valor=margem_mm / 1000, unidade="m", origem="HIPOTESE",
                                                        fonte="CENARIO assento 7 (valor a confirmar)")
    p = OUT / f"cfg_b{bump_mm}_m{margem_mm}.json"; json.dump(d, open(p, "w"), indent=1)
    c = pc.carregar(str(p)); return (c, hs, vr.cena_sem_cad(c))

cen = [(62.4, None), (61.4, None), (60.4, None), (62.4, 1.0), (62.4, 2.0), (59.4, 2.0), (58.0, 3.0), (56.6, 4.0)]
linhas = []
t0 = time.time()
for bump, marg in cen:
    J = cfg_com(bump, marg)
    for s in sols:
        j = bp.julgar_x(s["x"], J)
        r = {x["nome"]: x for x in j["restricoes"]}
        lmin = r.get("comprimento do amortecedor (mínimo)", {})
        viol = [x["nome"] for x in j["restricoes"] if x["estado"] == "VIOLADA"]
        linhas.append(dict(bump=bump, margem=marg, semente=s["rotulo"], veredito=j["veredito"], var_mr=j["var_mr"],
                           lmin_mm=None if lmin.get("valor") is None else lmin["valor"] * 1e3,
                           folga_lmin_mm=None if lmin.get("folga") is None else lmin["folga"] * 1e3,
                           violadas=viol, curso_roda_total_mm=23.0 + bump))
        L = linhas[-1]
        print(f"bump {bump:5.1f} marg {marg} {L['semente']:9s} {L['veredito']:11s} varMR {L['var_mr']*100:5.2f}% "
              f"Lmin {L['lmin_mm']:.2f} folga {L['folga_lmin_mm']:+.2f} viol {viol}", flush=True)
print("tempo", time.time() - t0)
json.dump(linhas, open(OUT / "rejulgar_curso.json", "w"), indent=1, ensure_ascii=False)
