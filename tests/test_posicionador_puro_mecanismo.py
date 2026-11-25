"""
Núcleo puro do posicionador (sem numpy/scipy) contra o pacote de referência `posicionador` (numpy/scipy), estágio 1:
álgebra, brentq, cinemática do canto e construção do mecanismo. TC-POS-130 a 133 (EDR-077).
P1: brentq puro = scipy em funções com raiz conhecida.
P2: Canto.resolver/razao_de_movimento = Corner.solve/motion_ratio nos hardpoints da v20 (curso e cremalheira variados).
P3: construir (r2 da v20, r2 resolvido) = mecanismo.construir em 40 casos sorteados (semente fixa): ou os dois falham
    ou os pontos coincidem a 1e-8 m (diferença medida 1,6e-9 m: o r2 vem do brentq sobre um MR de derivada numérica). Os casos sorteados são sintéticos de teste, não dado do carro.
P4: nenhum módulo de posicionador/puro importa numpy, scipy ou adsk.
Roda como script: uv run python -X utf8 tests/test_posicionador_puro_mecanismo.py
"""
import json
import math
import os
import random
import re

import numpy as np
from scipy.optimize import brentq as brentq_sp

import hardpoints as hp
import kinematics_model as km
from posicionador import config as pc
from posicionador import mecanismo as mec
from posicionador.puro import cinematica as pcin
from posicionador.puro import dados as pdados
from posicionador.puro import mecanismo as pmec
from posicionador.puro.otimizacao import brentq

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DADOS = os.path.join(RAIZ, "data", "posicionador")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


# P1
casos = [(lambda x: x ** 3 - 2 * x - 5, 2.0, 3.0), (lambda x: math.cos(x) - x, 0.0, 1.0),
         (lambda x: math.exp(x) - 10, 0.0, 5.0), (lambda x: 1e-3 * (x - 0.123456789), -1.0, 1.0)]
dif = max(abs(brentq(f, a, b, xtol=1e-13, rtol=1e-12) - brentq_sp(f, a, b, xtol=1e-13, rtol=1e-12)) for f, a, b in casos)
raised = False
try:
    brentq(lambda x: x * x + 1, -1, 1)
except ValueError:
    raised = True
check("TC-POS-130 P1 brentq puro = scipy", dif < 1e-11 and raised, f"maior diferença {dif:.2e}; sem mudança de sinal levanta ValueError={raised}")

# dados
hs_v10 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"), os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
hs_v20 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v20_script.csv"),
                            os.path.join(DADOS, "hardpoints_T11_v20_script.meta.json"))
v10 = pdados.carregar_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"))
v20 = pdados.carregar_hardpoints(os.path.join(DADOS, "hardpoints_T11_v20_script.csv"))
cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
with open(os.path.join(DADOS, "origem_v20_script.json"), encoding="utf-8") as f:
    x = json.load(f)["x_semente"]

# P2
ref = km.Corner(hs_v20, "FL")
puro = pcin.Canto({k[3:]: val for k, val in v20.items() if k.startswith("FL_")})
pior = 0.0
q_r = q_p = None
for curso, cr in [(0.0, 0.0), (-0.023, 0.0), (0.0624, 0.0), (0.02, 0.01), (-0.01, -0.02)]:
    sr, sp = ref.solve(curso, cr), puro.resolver(curso, cr)
    for k in ("WHEEL_CENTER", "PUSH_IN", "ROCKER_SPRING", "UCA_OUT"):
        pior = max(pior, float(np.linalg.norm(ref.pt(sr, k) - np.array(puro.ponto(sp, k)))))
    pior = max(pior, abs(ref.spring_length(sr) - puro.comprimento_mola(sp)))
mr_r, mr_p = km.motion_ratio(ref, 0.0)["mr_wheel_per_spring"], pcin.razao_de_movimento(puro, 0.0)["mr_wheel_per_spring"]
check("TC-POS-131 P2 cinemática do canto = km.Corner", pior < 1e-9 and abs(mr_r - mr_p) < 1e-8,
      f"pior erro de ponto {pior:.2e} m; MR numpy {mr_r:.9f}, puro {mr_p:.9f}")

# P3
v_sem = mec.Variaveis.da_semente_do_script(x)
vp_sem = pmec.Variaveis.da_semente_do_script(x)
rng = random.Random(7)
pares = [(v_sem, vp_sem, x[7] / 1000.0), (v_sem, vp_sem, None)]
for _ in range(38):
    piv = (rng.uniform(-0.15, 0.15), rng.uniform(0.0, 0.33), rng.uniform(0.06, 1.2))
    az, el = rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)
    r1, phi = rng.uniform(0.055, 0.08), rng.uniform(0.3, 2.8)
    pares.append((mec.Variaveis(np.array(piv), az, el, r1, phi), pmec.Variaveis(piv, az, el, r1, phi), None))
n_ok = n_falha = 0
pior = 0.0
ruim = []
for i, (vn, vp, r2) in enumerate(pares):
    cn, cp = mec.construir(hs_v10, vn, cfg, r2_m=r2), pmec.construir(v10, vp, cfg, r2_m=r2)
    if (cn.hardpoints is None) != (cp.pontos is None):
        ruim.append(f"caso {i}: numpy {cn.motivo!r} × puro {cp.motivo!r}")
        continue
    if cn.hardpoints is None:
        n_falha += 1
        continue
    n_ok += 1
    d = max(float(np.linalg.norm(cn.hardpoints.points[k].xyz - np.array(p[0]))) for k, p in cp.pontos.items())
    pior = max(pior, d, abs(cn.r2_m - cp.r2_m))
    if set(cp.pontos) != set(cn.hardpoints.points):
        ruim.append(f"caso {i}: conjuntos de pontos diferentes")
check("TC-POS-132 P3 construir puro = numpy", not ruim and pior < 1e-8 and n_ok >= 5,
      f"{n_ok} construídos e {n_falha} recusados nos dois; pior diferença {pior:.2e} m; divergências: {ruim[:3]}")

# P4
pasta = os.path.join(RAIZ, "python", "posicionador", "puro")
proibidos = []
for nome in os.listdir(pasta):
    if nome.endswith(".py"):
        with open(os.path.join(pasta, nome), encoding="utf-8") as fh:
            for lin in fh:
                if re.match(r"\s*(import|from)\s+(numpy|scipy|adsk|matplotlib)\b", lin):
                    proibidos.append(f"{nome}: {lin.strip()}")
check("TC-POS-133 P4 puro não importa numpy/scipy/adsk", not proibidos, f"{proibidos}")

n_fail = sum(1 for r in results if r[1] == "FAIL")
print(f"\n{len(results) - n_fail} PASS, {n_fail} FAIL, de {len(results)} testes")
raise SystemExit(1 if n_fail else 0)
