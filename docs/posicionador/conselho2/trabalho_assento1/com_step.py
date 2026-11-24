"""Parte 5: o candidato com δ livre que sai CONDICIONAL sem CAD, avaliado com o STEP do chassi (transformação HIPOTESE)."""
import json, sys
from pathlib import Path
import fase
sys.path.insert(0, str(fase.RAIZ / "tools"))
import posicionar_atuacao as pa
from posicionador import varredura as vr
cena = pa.cena_do_step(fase.RAIZ / "data/cad/T11_chassi_2026-11-17.step", fase.cfg)[0]
for l in open("refino.jsonl"):
    r = json.loads(l)
    av = vr.avaliar_convergido(fase.construir(r["x"]), cena, fase.cfg)
    print(r["modo"], r["sem"], av.veredito, av.resolucoes,
          [(q.nome, round(q.folga * 1e3, 2)) for q in av.restricoes if q.estado == "VIOLADA"])
    print("   NV:", [q.nome for q in av.restricoes if q.estado == "NAO_VERIFICAVEL"])
