"""
Núcleo puro do posicionador, estágio 3: mapa de espaço livre, Nelder-Mead e busca contra o pacote de referência (numpy/scipy),
na cena real do STEP (precisa do extra `cad`; sem ele, NÃO EXECUTÁVEL, código 3). TC-POS-137 a 141 (EDR-077).
B1: Nelder-Mead puro = scipy (mesmo mínimo, número de avaliações informado) em funções de teste.
B2: mapa de espaço livre: mesmos pontos livres (r_pivo) e mesma folga onde ela vale menos que o corte, numa caixa do T11.
B3: violação, objetivo e estados do núcleo puro = busca numpy em pontos dados (mesma avaliação).
B4: busca puro de ponta a ponta (30 amostras, 2 refinos, semente 0): termina, devolve resultado coerente, e o melhor
    candidato reavaliado pelo original tem o mesmo veredito e estados. A semente não reproduz o numpy (outro gerador).
B5: a v20 avaliada pelo núcleo puro (avaliar_convergido) = original (veredito e estados).
A caixa e os pontos sorteados são sintéticos de teste, não dado do carro.
Roda como script: uv run python -X utf8 tests/test_posicionador_puro_busca.py
"""
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import minimize

import hardpoints as hp
from posicionador import busca as bn
from posicionador import cad_step as cs
from posicionador import config as pc
from posicionador import espaco_livre as eln
from posicionador import geometria as gn
from posicionador import mecanismo as mec
from posicionador import varredura as vr
from posicionador.puro import busca as bp
from posicionador.puro import dados as pdados
from posicionador.puro import espaco_livre as elp
from posicionador.puro import geometria as pg
from posicionador.puro import mecanismo as pmec
from posicionador.puro import varredura as pvr
from posicionador.puro.otimizacao import nelder_mead

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
    sys.exit(3)

# B1
rosen = lambda v: (1 - v[0]) ** 2 + 100 * (v[1] - v[0] ** 2) ** 2   # noqa: E731
quad = lambda v: sum((a - b) ** 2 for a, b in zip(v, (1.0, -2.0, 0.5)))   # noqa: E731
pior, difs = 0.0, []
for f, x0 in ((rosen, [-1.2, 1.0]), (quad, [0.0, 0.0, 0.0])):
    n = len(x0)
    simplex = [list(x0)] + [[x0[k] + (0.3 if k == j else 0.0) for k in range(n)] for j in range(n)]
    xp, fp, nfp = nelder_mead(f, list(x0), simplex, 400)
    r = minimize(lambda v: f(list(v)), x0, method="Nelder-Mead",
                 options={"maxfev": 400, "initial_simplex": np.array(simplex), "xatol": 1e-6, "fatol": 1e-9})
    pior = max(pior, float(np.max(np.abs(np.array(xp) - r.x))), abs(fp - r.fun))
    difs.append((nfp, int(r.nfev)))
check("TC-POS-137 B1 Nelder-Mead puro = scipy", pior < 1e-9, f"pior diferença {pior:.2e}; avaliações (puro, scipy) {difs}")

# cena
cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
it = cfg.item("transformacao_step_m")
R = np.asarray(it.valor["rotacao"], dtype=float).reshape(3, 3)
tr = np.asarray(it.valor["translacao_m"], dtype=float).reshape(3)
cena = vr.cena_do_step(cs.ler_step(STEP), R, tr, cfg, ref_hipotese=f"{it.origem}: {it.fonte}")


def t(a):
    return tuple(float(x) for x in a)


def converter(p):
    if isinstance(p, gn.Esfera):
        return pg.Esfera(t(p.c), float(p.r))
    if isinstance(p, gn.Capsula):
        return pg.Capsula(t(p.a), t(p.b), float(p.r))
    return pg.Caixa(t(p.centro), tuple(t(e) for e in p.eixos), t(p.meias))


cena_p = pvr.cena_de([converter(o) for o in cena.fixos], [n.pos_m for n in cena.nos], cfg, pecas_moveis=cena.pecas_moveis,
                     ref_hipotese=cena.ref_hipotese, nao_modelado=[x for x in cena.nao_modelado if x not in vr.NAO_MODELADO_FASE1])
hs_v10 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"), os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
v10 = pdados.carregar_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"))
with open(os.path.join(DADOS, "origem_v20_script.json"), encoding="utf-8") as f:
    x20 = json.load(f)["x_semente"]
caixa = ((-0.15, 0.0, 0.06), (0.15, 0.326, 0.60))

# B2
t0 = time.time()
mn = eln.mapa(cena, caixa, passo_m=0.02, raio_m=0.0)
tn = time.time() - t0
t0 = time.time()
mp = elp.mapa(cena_p, caixa, passo_m=0.02, raio_m=0.0)
tp = time.time() - t0
r_pivo = float(cfg.valor("r_pivo_m"))
ln, lp = mn.livres(r_pivo), mp.livres(r_pivo)
fn = mn.folga_m.reshape(-1)
pior = max((abs(a - b) for a, b in zip(fn, mp.folga_m) if a < elp.CORTE_M - 1e-12), default=0.0)
iguais = len(ln) == len(lp) and all(np.allclose(a, b) for a, b in zip(ln, lp))
dn = mn.dist_no_m.reshape(-1)
pior_d = max(abs(a - b) for a, b in zip(dn, mp.dist_no_m))
check("TC-POS-138 B2 mapa de espaço livre puro = numpy", iguais and pior < 1e-9 and pior_d < 1e-9,
      f"{len(fn)} pontos, {len(lp)} livres (numpy {len(ln)}); pior folga {pior:.2e}; pior dist. ao nó {pior_d:.2e}; "
      f"tempo numpy {tn:.1f} s × puro {tp:.1f} s")

# B3
fxn = bn.faixas(cfg, caixa)
fxp = bp.faixas(cfg, caixa)
rng = np.random.default_rng(5)
pior_o, n_cmp, ruins = 0.0, 0, []
for _ in range(8):
    x = np.concatenate([rng.uniform(caixa[0], caixa[1]),
                        [rng.uniform(), rng.uniform(-np.pi, np.pi), rng.uniform(0.055, 0.08), rng.uniform(0.5, 2.5)]])
    cn = bn._avaliar_x(hs_v10, x, fxn, cena, cfg, 11, "amostra")
    cp = bp._avaliar_x(v10, list(x), fxp, cena_p, cfg, 11, "amostra")
    n_cmp += 1
    if cn.avaliacao.veredito != cp.avaliacao.veredito or cn.avaliacao.estados() != cp.avaliacao.estados():
        ruins.append("estados")
        continue
    a, b = bn._objetivo(cn.avaliacao), bp._objetivo(cp.avaliacao)
    pior_o = max(pior_o, abs(a - b) if math.isfinite(a) and math.isfinite(b) else 0.0)
    va, vb = bn.violacao(cn.avaliacao), bp.violacao(cp.avaliacao)
    if (math.isinf(va) != math.isinf(vb)) or (math.isfinite(va) and abs(va - vb) > 1e-6):
        ruins.append(f"violação {va} × {vb}")
check("TC-POS-139 B3 violação, objetivo e estados = numpy", not ruins and pior_o < 1e-6, f"{n_cmp} pontos; pior objetivo {pior_o:.2e}; {ruins[:3]}")

# B4
progresso = []
t0 = time.time()
res = bp.buscar(v10, cena_p, cfg, caixa, n_amostras=30, n_refinos=2, semente=0, passo_m=0.02, max_aval_refino=25,
                n_finalistas=3, progresso=lambda fase, i, n, mv: progresso.append((fase, i)))
tb = time.time() - t0
coer = (res.estatisticas["n_amostras"] == 30 and progresso[-1] == ("refinos", 2)) and (bool(res.candidatos) or res.fase1 is not None)
ok_reav = True
alvo = res.candidatos[0] if res.candidatos else (res.fase1.melhor if res.fase1 else None)
if alvo is not None:
    cn = mec.construir(hs_v10, mec.Variaveis(np.array(alvo.variaveis.pivo_m), alvo.variaveis.az_rad, alvo.variaveis.el_rad,
                                              alvo.variaveis.r1_m, alvo.variaveis.phi_b_rad, alvo.variaveis.delta_rad), cfg)
    an = bn._com_olhal(vr.avaliar(cn, cena, cfg, 11), cn, cfg)
    ap = bp._com_olhal(pvr.avaliar(alvo.construcao, cena_p, cfg, 11), alvo.construcao, cfg)
    ok_reav = an.veredito == ap.veredito and an.estados() == ap.estados()
melhor_v = res.fase1.melhor.violacao if res.fase1 and res.fase1.melhor else None
check("TC-POS-140 B4 busca puro de ponta a ponta", coer and ok_reav,
      f"{tb:.0f} s; viáveis {len(res.candidatos)}; falhas {res.estatisticas.get('falhas')}; melhor violação {melhor_v}; "
      f"reavaliação igual ao original={ok_reav}")

# B5
cn20 = mec.construir(hs_v10, mec.Variaveis.da_semente_do_script(x20), cfg, r2_m=x20[7] / 1000.0)
cp20 = pmec.construir(v10, pmec.Variaveis.da_semente_do_script(x20), cfg, r2_m=x20[7] / 1000.0)
an = bn.avaliar_convergido(cn20, cena, cfg)
ap = bp.avaliar_convergido(cp20, cena_p, cfg)
check("TC-POS-141 B5 v20 convergida = original", an.veredito == ap.veredito and an.estados() == ap.estados(),
      f"{an.veredito} × {ap.veredito}; resoluções {an.resolucoes} × {ap.resolucoes}")

n_fail = sum(1 for r in results if r[1] == "FAIL")
print(f"\n{len(results) - n_fail} PASS, {n_fail} FAIL, de {len(results)} testes")
sys.exit(1 if n_fail else 0)
