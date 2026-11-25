"""
Núcleo puro do posicionador, estágio 2: geometria, regulamento e varredura contra o pacote de referência (numpy), na cena
real do STEP do T11 (precisa do extra `cad`: sem ele sai NÃO EXECUTÁVEL, código 3). TC-POS-134 a 136 (EDR-077).
V1: primitivos do STEP convertidos para o núcleo puro dão a mesma sdf (pontos sorteados) e a mesma folga_segmento.
V2: `avaliar` puro = `avaliar` numpy em candidatos construídos pelo mesmo mecanismo: mesmos nomes de restrição, mesmos
    estados e mesmo veredito; folgas a 1e-6 m e curvas de MR a 1e-7.
V3: o texto NAO_MODELADO_FASE1 do núcleo é igual ao do original.
Os candidatos sorteados são sintéticos de teste, não dado do carro.
Roda como script: uv run python -X utf8 tests/test_posicionador_puro_varredura.py
"""
import json
import os
import random
import sys
import time

import numpy as np

import hardpoints as hp
from posicionador import cad_step as cs
from posicionador import config as pc
from posicionador import geometria as gn
from posicionador import mecanismo as mec
from posicionador import varredura as vr
from posicionador.puro import geometria as pg
from posicionador.puro import mecanismo as pmec
from posicionador.puro import varredura as pvr
from posicionador.puro import dados as pdados

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DADOS = os.path.join(RAIZ, "data", "posicionador")
STEP = os.path.join(RAIZ, "data", "cad", "T11_chassi_2026-11-17.step")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


if not cs.OCP_DISPONIVEL:
    print("NÃO EXECUTÁVEL: cadquery-ocp ausente (uv sync --extra cad)")
    raise SystemExit(3)


def t(a):
    return tuple(float(x) for x in a)


def converter(p):
    if isinstance(p, gn.Esfera):
        return pg.Esfera(t(p.c), float(p.r))
    if isinstance(p, gn.Capsula):
        return pg.Capsula(t(p.a), t(p.b), float(p.r))
    if isinstance(p, gn.Caixa):
        return pg.Caixa(t(p.centro), tuple(t(e) for e in p.eixos), t(p.meias))
    raise TypeError(type(p))


cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
it = cfg.item("transformacao_step_m")
R = np.asarray(it.valor["rotacao"], dtype=float).reshape(3, 3)
tr = np.asarray(it.valor["translacao_m"], dtype=float).reshape(3)
t0 = time.time()
montagem = cs.ler_step(STEP)
cena = vr.cena_do_step(montagem, R, tr, cfg, ref_hipotese=f"{it.origem}: {it.fonte}")
fixos_p = [converter(o) for o in cena.fixos]
cena_p = pvr.cena_de(fixos_p, [n.pos_m for n in cena.nos], cfg, pecas_moveis=cena.pecas_moveis,
                     ref_hipotese=cena.ref_hipotese, nao_modelado=[x for x in cena.nao_modelado if x not in vr.NAO_MODELADO_FASE1])
print(f"cena: {len(cena.fixos)} primitivos fixos, {len(cena.nos)} nós ({time.time() - t0:.1f} s)")

# V1
rng = random.Random(3)
pior = 0.0
for ob, ob_p in zip(cena.fixos, fixos_p):
    for _ in range(3):
        p = (rng.uniform(-0.4, 1.6), rng.uniform(-0.1, 0.6), rng.uniform(0.0, 1.3))
        pior = max(pior, abs(float(ob.sdf(np.array([p]))[0]) - ob_p.sdf(p)))
    a, b = (rng.uniform(-0.3, 0.3), 0.3, 0.5), (rng.uniform(0.0, 0.5), 0.4, 0.7)
    pior = max(pior, abs(gn.folga_segmento(ob, np.array(a), np.array(b), 0.01) - pg.folga_segmento(ob_p, a, b, 0.01)))
check("TC-POS-134 V1 primitivos puros = numpy (sdf e folga_segmento)", pior < 1e-9, f"{len(fixos_p)} primitivos; pior diferença {pior:.2e} m")

# candidatos
hs_v10 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"), os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
v10 = pdados.carregar_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"))
with open(os.path.join(DADOS, "origem_v20_script.json"), encoding="utf-8") as f:
    x = json.load(f)["x_semente"]
cands = [(mec.Variaveis.da_semente_do_script(x), pmec.Variaveis.da_semente_do_script(x), x[7] / 1000.0)]
rng = random.Random(11)
while len(cands) < 6:
    piv = (rng.uniform(-0.15, 0.15), rng.uniform(0.05, 0.33), rng.uniform(0.2, 1.0))
    az, el = rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4)
    r1, phi = rng.uniform(0.055, 0.08), rng.uniform(0.5, 2.5)
    vn = mec.Variaveis(np.array(piv), az, el, r1, phi)
    if mec.construir(hs_v10, vn, cfg).hardpoints is not None:
        cands.append((vn, pmec.Variaveis(piv, az, el, r1, phi), None))

# V2
n_ok, ruins, pior_f, pior_mr, tn, tp = 0, [], 0.0, 0.0, 0.0, 0.0
vereditos = []
for i, (vn, vp, r2) in enumerate(cands):
    cn, cp = mec.construir(hs_v10, vn, cfg, r2_m=r2), pmec.construir(v10, vp, cfg, r2_m=r2)
    t1 = time.time()
    an = vr.avaliar(cn, cena, cfg, 11)
    t2 = time.time()
    ap = pvr.avaliar(cp, cena_p, cfg, 11)
    t3 = time.time()
    tn += t2 - t1
    tp += t3 - t2
    vereditos.append((an.veredito, ap.veredito))
    if an.veredito != ap.veredito or an.estados() != ap.estados():
        dif = [k for k in set(an.estados()) | set(ap.estados()) if an.estados().get(k) != ap.estados().get(k)]
        ruins.append(f"cand {i}: {an.veredito}/{ap.veredito}, estados diferentes em {dif[:4]}")
        continue
    n_ok += 1
    for ra, rb in zip(an.restricoes, ap.restricoes):
        if ra.folga is not None and rb.folga is not None:
            pior_f = max(pior_f, abs(ra.folga - rb.folga))
    if an.curvas:
        pior_mr = max(pior_mr, float(np.max(np.abs(np.array(an.curvas["MR [wheel/spring]"]) - np.array(ap.curvas["MR [wheel/spring]"])))))
check("TC-POS-135 V2 avaliar puro = numpy na cena do STEP", not ruins and pior_f < 1e-6 and pior_mr < 1e-7,
      f"{n_ok}/{len(cands)} candidatos iguais (vereditos {vereditos}); pior folga {pior_f:.2e} m; pior MR {pior_mr:.2e}; "
      f"tempo numpy {tn:.1f} s × puro {tp:.1f} s; divergências {ruins[:3]}")

# V3
check("TC-POS-136 V3 NAO_MODELADO_FASE1 igual ao original", tuple(pvr.NAO_MODELADO_FASE1) == tuple(vr.NAO_MODELADO_FASE1))

n_fail = sum(1 for r in results if r[1] == "FAIL")
print(f"\n{len(results) - n_fail} PASS, {n_fail} FAIL, de {len(results)} testes")
sys.exit(1 if n_fail else 0)
