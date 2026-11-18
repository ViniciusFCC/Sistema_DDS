"""
Testes do mapa de espaço livre e da busca com diagnóstico do posicionador (EDR-076, TC-POS-070 a 073).
TC-POS-070: cena SINTÉTICA sem obstáculos e metas folgadas (MR_VAR_MAX 0,5; curso do amortecedor livre) → pelo menos um
            candidato VIAVEL ou CONDICIONAL, e todos os devolvidos foram reavaliados por `avaliar_convergido`.
TC-POS-071: metas impossíveis (MR_VAR_MAX 0,0001) → nenhum viável e `fase1` cita a variação de MR entre os conflitos.
TC-POS-072: `mapa` numa cena com uma `Capsula` SINTÉTICA: a folga de um ponto da grade é a sdf analítica; os pontos dentro
            da cápsula ficam fora de `livres(0)`.
TC-POS-073: mesma `semente` → mesma lista de candidatos (determinismo).
Dados: v10 de data/posicionador/ e a configuração do T11; as configurações alteradas, as caixas de busca, as cenas e os
nós são SINTÉTICOS de teste, não do carro (a caixa de busca do T11 não tem Y nem Z sem o STEP).
Roda como script: uv run python -X utf8 tests/test_posicionador_busca.py
"""
import copy
import json
import os
import tempfile
import time

import numpy as np

import hardpoints as hp
from posicionador import busca as bu
from posicionador import config as pc
from posicionador import espaco_livre as el
from posicionador import varredura as vr
from posicionador.cad_step import No
from posicionador.geometria import Capsula

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DADOS = os.path.join(RAIZ, "data", "posicionador")

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


hs_v10 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"),
                            os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
CAMINHO_CFG = os.path.join(DADOS, "config_T11.json")
with open(CAMINHO_CFG, encoding="utf-8") as f:
    bruto = json.load(f)


def cfg_sintetica(valores, tc):
    d = copy.deepcopy(bruto)
    for nome, valor in valores.items():
        d["itens"][nome].update(valor=valor, origem="HIPOTESE", fonte=f"SINTÉTICO de teste ({tc})")
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "config_sintetica.json")
        with open(p, "w", encoding="utf-8") as g:
            json.dump(d, g)
        return pc.carregar(p)


# Caixa SINTÉTICA de busca do pivô: X da configuração do T11 (±150 mm); Y e Z em volta do pivô da v20 do Murilo
# (−57; 290; 476 mm), porque sem STEP a configuração não tem Y nem Z.
CAIXA = (np.array([-0.15, 0.24, 0.42]), np.array([0.15, 0.34, 0.53]))
# Metas SINTÉTICAS folgadas (TC-POS-070 e 073): variação de MR 0,5 e curso do amortecedor igual ao olho a olho (o
# comprimento mínimo do amortecedor deixa de limitar).
FOLGADAS = {"mr_var_max": 0.5, "curso_amortecedor_m": 0.21}


def resumo(res):
    return [(c.avaliacao.veredito, round(float(c.avaliacao.restricao("variação de MR").valor), 6),
             tuple(float(v) for v in np.round(c.variaveis.pivo_m * 1e3, 3))) for c in res.candidatos]


# --- TC-POS-072 ---------------------------------------------------------------------------------------------------
t0 = time.perf_counter()
cap = Capsula(np.array([0.0, 0.0, 0.0]), np.array([0.10, 0.0, 0.0]), 0.02)        # SINTÉTICA
no = No(pos_m=np.array([0.05, 0.05, 0.0]), n_ramos=3, triangulado=True)             # SINTÉTICO
cena72 = vr.Cena(fixos=[cap], nos=[no], aro=(0.158, 0.10), regras={})
caixa72 = (np.array([-0.05, -0.05, -0.05]), np.array([0.15, 0.05, 0.05]))
m72 = el.mapa(cena72, caixa72, passo_m=0.01)
g = m72.grade.reshape(-1, 3)
sdf = cap.sdf(g)
folga = m72.folga_m.reshape(-1)
dist = m72.dist_no_m.reshape(-1)
livres0 = m72.livres(0.0)
livres1 = m72.livres(0.01)
dentro = g[sdf < 0.0]
fora = g[sdf >= 0.0]
chave = lambda pts: {tuple(np.round(p, 9)) for p in pts}  # noqa: E731
L0 = chave(livres0)
i_pt = int(np.argmin(np.linalg.norm(g - np.array([0.05, 0.03, 0.0]), axis=1)))   # ponto da grade a 10 mm da cápsula
m72r = el.mapa(cena72, caixa72, passo_m=0.01, raio_m=0.005)
ok72 = (m72.grade.shape == (21, 11, 11, 3) and m72.folga_m.shape == (21, 11, 11)
        and np.allclose(folga, sdf, atol=1e-12, rtol=0.0) and abs(folga[i_pt] - 0.01) < 1e-12
        and len(dentro) > 0 and not (chave(dentro) & L0) and chave(fora) == L0
        and chave(livres1) == chave(g[sdf >= 0.01])
        and np.allclose(dist, np.linalg.norm(g - no.pos_m, axis=1), atol=1e-12, rtol=0.0)
        and np.allclose(m72r.folga_m, m72.folga_m - 0.005, atol=1e-12, rtol=0.0))
check("TC-POS-072 mapa com cápsula SINTÉTICA: folga = sdf analítica; dentro fora de livres(0)", ok72,
      f"grade {m72.grade.shape}; |folga − sdf| máx = {np.abs(folga - sdf).max():.2e} m; folga em "
      f"{np.round(g[i_pt] * 1e3, 1)} mm = {folga[i_pt] * 1e3:.3f} mm (esperado 10); {len(dentro)} pontos dentro, "
      f"{len(chave(dentro) & L0)} deles em livres(0); livres(0) = {len(livres0)} pontos, livres(10 mm) = {len(livres1)}; "
      f"{time.perf_counter() - t0:.2f} s")

# --- TC-POS-070 ---------------------------------------------------------------------------------------------------
cfg70 = cfg_sintetica(FOLGADAS, "TC-POS-070")
cena70 = vr.cena_sem_cad(cfg70)            # SINTÉTICA: sem obstáculos fixos nem nós
t0 = time.perf_counter()
res70 = bu.buscar(hs_v10, cena70, cfg70, CAIXA, n_amostras=60, n_refinos=2, semente=1, max_aval_refino=25)
dt70 = time.perf_counter() - t0
vered = [c.avaliacao.veredito for c in res70.candidatos]
reav = [c.avaliacao.resolucoes for c in res70.candidatos]
ok70 = (len(res70.candidatos) >= 1 and all(v in ("VIAVEL", "CONDICIONAL") for v in vered)
        and all(len(r) >= 2 for r in reav) and res70.fase1 is None)
mrs = [c.avaliacao.restricao("variação de MR").valor for c in res70.candidatos]
check("TC-POS-070 cena SINTÉTICA sem obstáculos e metas folgadas: candidatos viáveis reavaliados", ok70,
      f"{len(res70.candidatos)} candidatos ({dict((v, vered.count(v)) for v in set(vered))}); resoluções "
      f"{reav[:3]}...; variação de MR (ordem): {[round(float(v), 4) for v in mrs[:5]]}; estatísticas "
      f"{res70.estatisticas}; {dt70:.1f} s")

# --- TC-POS-071 ---------------------------------------------------------------------------------------------------
cfg71 = cfg_sintetica({"mr_var_max": 0.0001}, "TC-POS-071")
cena71 = vr.cena_sem_cad(cfg71)
t0 = time.perf_counter()
res71 = bu.buscar(hs_v10, cena71, cfg71, CAIXA, n_amostras=60, n_refinos=2, semente=2, max_aval_refino=25)
dt71 = time.perf_counter() - t0
f1 = res71.fase1
cita = f1 is not None and any("variação de MR" in (a, b) for a, b, _ in f1.conflitos)
ok71 = (len(res71.candidatos) == 0 and f1 is not None and f1.melhor is not None and cita)
check("TC-POS-071 metas impossíveis: nenhum viável e a fase 1 cita a variação de MR", ok71,
      f"{len(res71.candidatos)} candidatos; conflitos: "
      f"{None if f1 is None else [(a, b, round(x, 3)) for a, b, x in f1.conflitos[:4]]}; melhor: "
      f"{None if f1 is None or f1.melhor is None else (f1.melhor.avaliacao.veredito, round(f1.melhor.violacao, 4))}; "
      f"falhas: {None if f1 is None else f1.falhas}; {dt71:.1f} s")

# --- TC-POS-073 ---------------------------------------------------------------------------------------------------
t0 = time.perf_counter()
caixa_none = (np.array([-0.15, None, None]), np.array([0.15, None, None]))
try:
    bu.buscar(hs_v10, cena70, cfg70, caixa_none, n_amostras=5)
    erro_none = None
except ValueError as e:
    erro_none = str(e)
a = bu.buscar(hs_v10, cena70, cfg70, CAIXA, n_amostras=30, n_refinos=1, semente=7, max_aval_refino=15)
b = bu.buscar(hs_v10, cena70, cfg70, CAIXA, n_amostras=30, n_refinos=1, semente=7, max_aval_refino=15)
ra, rb = resumo(a), resumo(b)
iguais_vars = all(np.array_equal(x.variaveis.pivo_m, y.variaveis.pivo_m)
                  and (x.variaveis.az_rad, x.variaveis.el_rad, x.variaveis.r1_m, x.variaveis.phi_b_rad)
                  == (y.variaveis.az_rad, y.variaveis.el_rad, y.variaveis.r1_m, y.variaveis.phi_b_rad)
                  for x, y in zip(a.candidatos, b.candidatos))
ok73 = len(ra) >= 1 and ra == rb and iguais_vars and erro_none is not None and "caixa" in erro_none
check("TC-POS-073 mesma semente → mesma lista de candidatos; caixa com None → ValueError", ok73,
      f"{len(ra)} e {len(rb)} candidatos; primeiros: {ra[:2]}; ValueError: {erro_none!r}; "
      f"{time.perf_counter() - t0:.1f} s")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
