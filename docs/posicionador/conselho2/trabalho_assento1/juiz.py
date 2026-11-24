"""Parte 3: o juiz do posicionador (varredura.avaliar_convergido, cena só com o aro) nos resultados de fase.py."""
import json, sys
from pathlib import Path
import fase
from posicionador import varredura as vr

cena = vr.cena_sem_cad(fase.cfg)
for l in open(Path(__file__).with_name("runs.jsonl")):
    r = json.loads(l)
    if r["objetivo"] != "viavel" and sys.argv[1:] != ["todos"]:
        continue
    c = fase.construir(r["x"])
    av = vr.avaliar_convergido(c, cena, fase.cfg)
    viol = [(x.nome, round(x.folga * 1e3, 3) if x.folga is not None else None) for x in av.restricoes if x.estado == "VIOLADA"]
    var = av.restricao("variação de MR").valor
    lmin = av.restricao("comprimento do amortecedor (mínimo)").valor
    print(f"{r['modo']:<6} s{r['semente']} {r['objetivo']:<6} cap {r['cap']}: δ = {r['x'][7]:+.2f}°  {av.veredito:<11} "
          f"n = {av.resolucoes} var = {var * 100:.3f} %  Lmin = {lmin * 1e3:.3f} mm  violadas: {viol}")
