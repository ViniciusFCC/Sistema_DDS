"""Parte 6: alavanca MR(0) dentro da tolerância do juiz (± 0,01): controle δ = 0 reconstruído com MR(0) = 1,405 e 1,41.
E a sensibilidade do candidato δ livre (s5) a δ e ao pivô."""
import json
import numpy as np
import fase
from posicionador import varredura as vr
cena = vr.cena_sem_cad(fase.cfg)
R = [json.loads(l) for l in open("refino.jsonl")]
for r in R:
    if r["modo"] != "d0": continue
    for alvo in (1.405, 1.41):
        av = vr.avaliar_convergido(fase.construir(r["x"], mr_alvo=alvo), cena, fase.cfg)
        print("d0", r["sem"], alvo, av.veredito, "var %.3f%%" % (av.restricao("variação de MR").valor * 100),
              "Lmin %.3f" % (av.restricao("comprimento do amortecedor (mínimo)").valor * 1e3),
              [(q.nome, round(q.folga * 1e3, 3)) for q in av.restricoes if q.estado == "VIOLADA"])
s5 = next(r for r in R if r["modo"] == "dlivre" and r["sem"] == 5)
print("x s5 (pivô mm, az°, el°, r1 mm, φB°, δ°):", [round(v, 3) for v in s5["x"]])
for i, nome, h in ((7, "δ", 0.5), (0, "Pv_x", 0.5), (1, "Pv_y", 0.5), (2, "Pv_z", 0.5), (6, "φB", 0.5), (5, "r1", 0.5)):
    out = []
    for s in (-1, 1):
        x = np.array(s5["x"]); x[i] += s * h
        m = fase.medir(fase.construir(x), n=101)
        out.append("%+.1f: var %.3f%% Lmin %.3f" % (s * h, m["var"] * 100, m["lmin_mm"]))
    print(nome, out)
