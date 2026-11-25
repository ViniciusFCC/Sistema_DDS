"""
Trabalhador do teste `test_posicionador_puro_interpretadores.py`: roda o núcleo puro (sem numpy/scipy/adsk) e imprime um
resumo em JSON no stdout. Só biblioteca padrão, para valer no Python 3.13 do repositório e no 3.14 embutido no Fusion.
Cena sintética de teste (cápsulas e uma caixa ao redor da região de busca): não é dado do carro.
Uso: <python> -I -X utf8 tests/_nucleo_puro_resumo.py
"""
import json
import math
import os
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "python"))
DADOS = os.path.join(RAIZ, "data", "posicionador")

from posicionador import config as pc  # noqa: E402
from posicionador.puro import busca as bp  # noqa: E402
from posicionador.puro import dados as pdados  # noqa: E402
from posicionador.puro import geometria as pg  # noqa: E402
from posicionador.puro import mecanismo as pmec  # noqa: E402
from posicionador.puro import varredura as pvr  # noqa: E402
from posicionador.puro.otimizacao import brentq, nelder_mead  # noqa: E402


def arred(x, n=9):
    if isinstance(x, float):
        return x if not math.isfinite(x) else round(x, n)
    if isinstance(x, (list, tuple)):
        return [arred(v, n) for v in x]
    return x


def resumo_av(av):
    return {"veredito": av.veredito, "estados": av.estados(),
            "folgas": {r.nome: arred(r.folga) for r in av.restricoes},
            "mr": arred(av.curvas.get("MR [wheel/spring]", [])), "resolucoes": av.resolucoes}


def main():
    cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
    v10 = pdados.carregar_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"))
    with open(os.path.join(DADOS, "origem_v20_script.json"), encoding="utf-8") as f:
        x20 = json.load(f)["x_semente"]
    fixos = [pg.Capsula((0.10, 0.20, 0.30), (0.10, 0.20, 0.55), 0.012), pg.Capsula((-0.20, 0.10, 0.20), (0.15, 0.10, 0.20), 0.012),
             pg.Caixa((-0.10, 0.05, 0.45), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.03, 0.02, 0.02))]
    cena = pvr.cena_de(fixos, [(0.0, 0.2, 0.3)], cfg)
    caixa = ((-0.15, 0.0, 0.06), (0.15, 0.326, 0.60))
    out = {"python": sys.version.split()[0]}
    out["brentq"] = arred(brentq(lambda x: math.cos(x) - x, 0.0, 1.0, xtol=1e-13, rtol=1e-12), 12)
    xp, fp, nf = nelder_mead(lambda v: (1 - v[0]) ** 2 + 100 * (v[1] - v[0] ** 2) ** 2, [-1.2, 1.0],
                             [[-1.2, 1.0], [-0.9, 1.0], [-1.2, 1.3]], 300)
    out["nelder_mead"] = {"x": arred(xp, 9), "f": arred(fp, 12), "n": nf}
    c20 = pmec.construir(v10, pmec.Variaveis.da_semente_do_script(x20), cfg, r2_m=x20[7] / 1000.0)
    out["v20_sem_fixos"] = resumo_av(bp.avaliar_convergido(c20, pvr.cena_de([], [], cfg), cfg))
    out["v20_com_fixos"] = resumo_av(bp.avaliar_convergido(c20, cena, cfg))
    res = bp.buscar(v10, cena, cfg, caixa, n_amostras=40, n_refinos=2, semente=3, passo_m=0.03, max_aval_refino=20, n_finalistas=2)
    melhor = res.candidatos[0] if res.candidatos else (res.fase1.melhor if res.fase1 else None)
    out["busca"] = {"estatisticas": {k: (arred(v) if k != "tempo_s" else None) for k, v in res.estatisticas.items()},
                    "n_candidatos": len(res.candidatos),
                    "melhor": None if melhor is None else {"violacao": arred(melhor.violacao), "origem": melhor.origem,
                                                            "variaveis": arred(list(melhor.variaveis.pivo_m)
                                                                               + [melhor.variaveis.az_rad, melhor.variaveis.el_rad,
                                                                                  melhor.variaveis.r1_m, melhor.variaveis.phi_b_rad]),
                                                            "veredito": melhor.avaliacao.veredito}}
    json.dump(out, sys.stdout, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    main()
