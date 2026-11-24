"""E4: as soluções sem violação de E2 (B e C) e de E3 julgadas com a cena do STEP (avaliar_convergido, cena_do_step do
posicionar_atuacao: referencial HIPOTESE). Separa 'cabe na cinemática' de 'cabe no chassi'. Saída: e4_saida.txt."""
import json, sys, time
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[4]
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(R / "python")); sys.path.insert(0, str(R / "tools"))
import hardpoints as hp
import posicionar_atuacao as pa
from posicionador import busca as bu, config as pc, mecanismo as mec, varredura as vr

cfg = pc.carregar(str(R / "data/posicionador/config_T11.json"))
hs = hp.load_hardpoints(str(R / "data/posicionador/hardpoints_T11_v10.csv"), str(R / "data/posicionador/hardpoints_T11_v10.meta.json"))
t = time.time()
cena = pa.cena_do_step(str(R / "data/cad/T11_chassi_2026-11-17.step"), cfg)[0]
print(f"cena STEP em {time.time()-t:.0f} s; fixos {len(cena.fixos)}")
fx = bu.faixas(cfg, (np.array([-0.15, 0.0, 0.0601]), np.array([0.15, 0.3257, 1.2574])))
cands = []
for o in json.load(open(AQUI / "e2_resultados.json")):
    if o.get("veredito") == "CONDICIONAL":
        cands.append((f"E2/{o['modo']} {o['rotulo']}", o["modo"], o["x"]))
e3 = AQUI / "e3_resultados.json"
if e3.exists():
    for o in json.load(open(e3)):
        if o["veredito"] == "CONDICIONAL" and o["variante"] == "base":
            cands.append((f"E3/base {o['rotulo']}", "B", o["x"]))
for rot, modo, x in cands:
    v = bu.variaveis_de(np.asarray(x[:7]), fx)
    if modo == "B":
        c = mec.construir(hs, v, cfg, r2_m=x[7])
    else:  # C: reconstrói com o r2 que o juiz mediu em E2
        r2 = next(o["r2_mm"] for o in json.load(open(AQUI / "e2_resultados.json")) if o["modo"] == "C" and f"E2/C {o['rotulo']}" == rot) / 1e3
        c = mec.construir(hs, v, cfg, r2_m=r2)
    t = time.time()
    av = bu.avaliar_convergido(c, cena, cfg)
    vio = [(r.nome, r.folga) for r in av.restricoes if r.estado == "VIOLADA"]
    fix = [(r.nome, r.folga) for r in av.restricoes if "fixos" in r.nome or "chassi" in r.nome.lower()]
    print(f"{rot:18s} {av.veredito:11s} {time.time()-t:.0f}s violadas={vio}")
    for n, fo in fix:
        print(f"      {n}: folga {fo}")
