"""Checagem 2: o que acontece com os 5 melhores do posicionador (benchmark) sob relaxamentos SÓ DE TESTE (config copiada):
(a) MR(0) construído em 1,41 (dentro da tolerância ±0,01 que o juiz já aceita);
(b) curso de bump 62,4 → 61,4 mm (hipótese do benchmark);
(c) margem de curso do amortecedor = 2 mm (A_CONFIRMAR hoje; valor ilustrativo, NÃO é dado da equipe).
Juiz: avaliar_convergido + restrição do olhal. Não altera o repositório."""
import json, sys, copy
from pathlib import Path
import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path[:0] = [str(RAIZ / "python"), str(RAIZ / "tools")]
import benchmark_posicionador as bp
from posicionador import mecanismo as mec, varredura as vr, busca as bu, config as pc

d = json.loads((RAIZ / "docs/posicionador/benchmark/resultados.json").read_text(encoding="utf-8"))
base = json.loads((RAIZ / "data/posicionador/config_T11.json").read_text(encoding="utf-8"))
_, hs, _ = bp._juiz()


def cfg_com(**mud):
    c = copy.deepcopy(base)
    for k, v in mud.items():
        c["itens"][k]["valor"] = v
        if c["itens"][k]["origem"] == "A_CONFIRMAR":
            c["itens"][k]["origem"] = "HIPOTESE"
    p = AQUI / f"cfg_{'_'.join(mud) or 'base'}.json"
    p.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    return pc.carregar(str(p))


cenarios = {"base": cfg_com(), "MR0=1,41": cfg_com(mr_alvo=1.41), "bump 61,4": cfg_com(curso_bump_m=0.0614),
            "margem 2 mm": cfg_com(margem_curso_amortecedor_m=0.002)}
for i in [13, 15, 16, 17]:
    x = d["buscas"][i]["x"]
    v = mec.Variaveis.da_semente_do_script(x)
    for nome, cfg in cenarios.items():
        cena = vr.cena_sem_cad(cfg)
        # r2 re-resolvido para MR(0) = mr_alvo do cenário (o posicionador o faz por construção)
        con = mec.construir(hs, v, cfg)
        if con.hardpoints is None:
            print(i, nome, "construção:", con.motivo); continue
        av = bu._com_olhal(vr.avaliar_convergido(con, cena, cfg), con, cfg)
        vio = {r.nome: (round(r.valor, 5) if isinstance(r.valor, float) else r.valor, round(r.folga * 1e3, 3) if r.folga is not None and abs(r.folga) < 1 else r.folga)
               for r in av.restricoes if r.estado == "VIOLADA"}
        var = av.restricao("variação de MR").valor
        lmin = av.restricao("comprimento do amortecedor (mínimo)")
        print(f"[{i}] {nome:12s} {av.veredito:11s} r2={con.r2_m*1e3:.2f} var={var:.4f} Lmin folga={lmin.folga*1e3:+.3f} mm  violadas={vio}")
