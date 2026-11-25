"""
Testes do adaptador do Fusion (fase 2 do posicionador) que rodam FORA do Fusion: a regra de obstáculos, a cena que mede pela
API (FixoFusion) com um oráculo falso no lugar da API, e o pipeline de ponta a ponta sobre os dados reais da sondagem do
T11 (cópia com nomes corrigidos, 2026-11-24). Sem ID de TC (aguarda autorização; os IDs TC-POS-100 a 141 são do EDR-077).
A: a regra promove só o que é dianteiro, fora do objeto da busca e fora do regulamento; traseiro, misto e vazio não.
B: no T11 real a regra não promove nada e acha o misto (amortecedores).
C: Quadro: ida e volta carro ↔ CAD; caixa do corpo no carro contém a do CAD.
D: FixoFusion: saturação, filtro por caixa sem chamar o oráculo, folga = d_fino − raio contra a folga por SDF do núcleo.
E: pipeline de ponta a ponta (oráculo falso por caixas): identificação, cena, hardpoints vivos, caixa de busca, busca curta e saídas.
F: identificação com FALHA bloqueia (ErroIdentificacao); nenhum módulo do adaptador além de api.py importa adsk, numpy ou scipy.
G: o hook `folga_segmento` do núcleo usa o método do primitivo quando ele existe e não muda os primitivos comuns.
Roda como script: uv run python -X utf8 tests/test_posicionador_fusion_adaptador.py
"""
import copy
import json
import math
import os
import random
import re
import tempfile

from posicionador import config as pc
from posicionador import identificacao as idf
from posicionador.fusion import cena as fc
from posicionador.fusion import obstaculos as ob
from posicionador.fusion import pipeline as pl
from posicionador.puro import geometria as pg

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SONDAGEM = os.path.join(RAIZ, "docs", "posicionador", "fusion", "fusion_sondagem3_copia_nomes_corrigidos_2026-11-24.json")
DADOS = os.path.join(RAIZ, "data", "posicionador")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


with open(SONDAGEM, encoding="utf-8") as f:
    GEO0 = json.load(f)["geometria_por_componente"]


def com_ids(geo):
    """Cópia da geometria com o campo `id` em cada corpo (como `api.ler_geometria`) e a lista de caixas por id (mm)."""
    g, caixas = copy.deepcopy(geo), []
    for t in g["topos"].values():
        for o in t["ocorrencias"]:
            for c in o["corpos"]:
                c["id"] = len(caixas)
                caixas.append((c["min_mm"], c["max_mm"]))
    return g, caixas


class OraculoFalso:
    """Distâncias exatas até a caixa de cada corpo (CAD, cm), com a semântica da API: 0 ao tocar ou cruzar."""

    def __init__(self, caixas_mm):
        self.cx = [([v / 10.0 for v in lo], [v / 10.0 for v in hi]) for lo, hi in caixas_mm]
        self.n_chamadas, self.n_erros, self.tempo_s, self.ultimo_erro = 0, 0, 0.0, None
        self.pedidos = []

    def _d(self, i, p):
        lo, hi = self.cx[i]
        return math.sqrt(sum(max(lo[k] - p[k], p[k] - hi[k], 0.0) ** 2 for k in range(3)))

    def dist_ponto(self, i, p):
        self.n_chamadas += 1
        self.pedidos.append(("p", i))
        return self._d(i, p)

    def dist_segmento(self, i, a, b, r):
        self.n_chamadas += 1
        self.pedidos.append(("s", i))
        n = max(int(math.dist(a, b) / 0.05), 1)               # passo de 0,5 mm
        d = min(self._d(i, [a[k] + (b[k] - a[k]) * j / n for k in range(3)]) for j in range(n + 1))
        return max(d - r, 0.0) if d > 0.0 else 0.0            # cilindro fino: a distância sai menor que a do eixo em até r


# ---- A
def linha(nome, caixa, n=3):
    return {"componente": nome, "n_corpos": n, "caixa_carro_mm": caixa}


class ResFalso:
    def __init__(self, linhas):
        self.tabela_ignorados = linhas
        self.tabela_componentes, self.reconhecimento = [], {}


casos = {
    "IGNORAR_SUPORTE_SENSOR": ([[100.0, 0.0, 0.0], [150.0, 50.0, 50.0]], "promovido"),
    "IGNORAR_TRAS_SUPORTE": ([[-1500.0, 0.0, 0.0], [-1400.0, 50.0, 50.0]], "ignorado"),
    "IGNORAR_ATUACAO_X": ([[-40.0, 0.0, 0.0], [10.0, 50.0, 50.0]], "ignorado"),
    "IGNORAR_PUSH_ROD_FE": ([[-22.0, 0.0, 0.0], [4.0, 50.0, 50.0]], "ignorado"),
    "IGNORAR_GABARITO_T1_2": ([[331.0, -100.0, 0.0], [338.0, 100.0, 300.0]], "ignorado"),
    "IGNORAR_MISTO": ([[-1599.0, -50.0, 0.0], [261.0, 50.0, 50.0]], "misto"),
    "IGNORAR_SEM_TRAS_ATRAS": ([[-1800.0, 0.0, 0.0], [-1600.0, 50.0, 50.0]], "ignorado"),
}
dec = {n: ob._decidir_ignorado(linha(n, c)).destino for n, (c, _) in casos.items()}
vazio = ob._decidir_ignorado(linha("IGNORAR_PLANOS", None, 0)).destino
check("A regra de obstáculos", all(dec[n] == esp for n, (_, esp) in casos.items()) and vazio == "ignorado",
      f"{dec}; vazio={vazio}")

# ---- B
res_real = idf.verificar(GEO0)
cl = ob.classificar(res_real)
tipos = {}
for d in cl.decisoes:
    tipos[d.destino] = tipos.get(d.destino, 0) + 1
check("B T11 real: nenhum promovido, 1 misto (amortecedores), chassi como obstáculo",
      res_real.ok and not cl.promovidos and [d.componente for d in cl.mistos] == ["IGNORAR_AMORTECEDORES_DNM_ARQUIVO:1"]
      and cl.nomes("obstaculo") == ["CHASSI_T11_V20:1"], f"{tipos}; obstáculos {cl.obstaculos}; texto {ob.texto(cl)[:2]}")

# ---- C
geo, caixas = com_ids(GEO0)
q = pl.quadro_do_cad(geo, idf.verificar(geo))
ok_ida, pior = True, 0.0
rng = random.Random(1)
for _ in range(50):
    p = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0, 1))
    cad_cm = q.para_cad_cm(p)
    volta = q.para_carro_m([v * 10.0 for v in cad_cm])
    pior = max(pior, max(abs(a - b) for a, b in zip(p, volta)))
lo_c, hi_c = q.caixa_carro_m((100.0, 200.0, 300.0), (150.0, 260.0, 340.0))
check("C quadro: ida e volta e caixa", pior < 1e-12 and all(l <= h for l, h in zip(lo_c, hi_c)), f"pior {pior:.2e} m; caixa {lo_c}..{hi_c}")

# ---- D
orac = OraculoFalso([((0.0, 0.0, 0.0), (100.0, 100.0, 100.0))])          # um corpo: caixa 0..100 mm (CAD)
quadro_id = fc.Quadro((0.0, 0.0, 0.0), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
fx = fc.FixoFusion(0, "caixa", (0.0, 0.0, 0.0), (0.1, 0.1, 0.1), quadro_id, orac, fc.Contagem(), 0.05)
longe = fx.folga_segmento((0.5, 0.5, 0.5), (0.6, 0.5, 0.5), 0.01)
n_longe = orac.n_chamadas
perto = fx.folga_segmento((0.130, 0.05, 0.05), (0.2, 0.05, 0.05), 0.01)     # eixo a 30 mm da caixa, raio 10 mm → folga 20 mm
dentro = fx.folga_segmento((0.05, 0.05, 0.05), (0.2, 0.05, 0.05), 0.01)     # eixo dentro: d = 0 → folga = −raio
casca = fx.folga_segmento((0.108, 0.05, 0.05), (0.2, 0.05, 0.05), 0.01)     # raio entra 2 mm no corpo → folga −2 mm
ponto_longe = fx.sdf((0.5, 0.5, 0.5))
check("D1 FixoFusion: saturação, filtro por caixa e sinais",
      longe == 0.05 and n_longe == 0 and ponto_longe == 0.05 and abs(perto - 0.02) < 5e-4 and dentro == -0.01 and abs(casca + 0.002) < 5e-4,
      f"longe {longe} (chamadas {n_longe}); perto {perto:.5f}; dentro {dentro}; casca {casca:.5f}")

# contra a folga por SDF do núcleo (Caixa) em segmentos sorteados (sintéticos de teste)
caixa_pg = pg.Caixa((0.05, 0.05, 0.05), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), (0.05, 0.05, 0.05))
pior_d, n_cmp, n_sat, n_dentro, dentro_ok = 0.0, 0, 0, 0, True
rng = random.Random(7)
for _ in range(300):
    a = tuple(rng.uniform(-0.1, 0.25) for _ in range(3))
    b = tuple(rng.uniform(-0.1, 0.25) for _ in range(3))
    r = rng.uniform(0.002, 0.02)
    f1 = fx.folga_segmento(a, b, r)
    f2 = min(pg.folga_segmento(caixa_pg, a, b, r, 0.0005), 0.05)
    if f1 == 0.05 and f2 == 0.05:
        n_sat += 1
        continue
    if min(caixa_pg.sdf(tuple(a[k] + (b[k] - a[k]) * j / 400 for k in range(3))) for j in range(401)) < 0.0:
        # o eixo atravessa o corpo: a API só diz "tocam" (d = 0), então a folga é −raio, sem a profundidade que a SDF dá
        n_dentro += 1
        dentro_ok = dentro_ok and abs(f1 + r) < 1e-12 and f1 < 0.0 and f2 < 0.0
        continue
    n_cmp += 1
    pior_d = max(pior_d, abs(f1 - f2))
check("D2 folga do FixoFusion = folga por SDF do núcleo (≤ 1 mm; eixo dentro do corpo: −raio, ambos negativos)",
      pior_d < 1e-3 and n_cmp > 100 and n_dentro > 10 and dentro_ok,
      f"{n_cmp} segmentos comparados, {n_sat} saturados, {n_dentro} com o eixo dentro; pior diferença {pior_d * 1e3:.3f} mm")

# ---- E
cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
orac = OraculoFalso(caixas)
caminho_hp = os.path.join(DADOS, "hardpoints_T11_v20_1_cad.csv")
with tempfile.TemporaryDirectory() as tmp:
    params = {"n_amostras": 12, "n_refinos": 1, "semente": 0, "passo_m": 0.05, "max_aval_refino": 6, "n_finalistas": 1}
    d, res = pl.executar(geo, orac, cfg, caminho_hp, tmp, params)
    arquivos = sorted(os.listdir(tmp))
    with open(os.path.join(tmp, "resultado.json"), encoding="utf-8") as f:
        lido = json.load(f)
    md = open(os.path.join(tmp, "relatorio.md"), encoding="utf-8").read()
env = d["caixa_busca_pivo_m"]
dif_max = max(m for _, m in [(x["id"], x["mm"]) for x in d["hp_diferencas_mm"]])
check("E pipeline de ponta a ponta (oráculo falso)",
      "resultado.json" in arquivos and "relatorio.md" in arquivos and lido["obstaculos"]["promovidos"] == []
      and d["obstaculos"]["n_corpos_na_cena"] == 27 and env["origem"] == "HIPOTESE" and dif_max < 0.5
      and "Promovidos pela regra" in md and d["estatisticas"]["n_amostras"] == 12 and orac.n_chamadas > 0
      and d["contagem"]["segmentos_pedidos"] > d["contagem"]["segmentos_medidos"],
      f"{arquivos}; corpos {d['obstaculos']['n_corpos_na_cena']}; caixa {env['min_m']}..{env['max_m']}; hp dif máx {dif_max:.3f} mm; "
      f"chamadas {orac.n_chamadas}; contagem {d['contagem']}; viáveis {d['estatisticas'].get('n_viaveis')}")

# ---- F
geo_ruim = copy.deepcopy(geo)
nome_bandeja = next(n for n, r in res_real.reconhecimento.items() if r.categoria == "BANDEJA_FE")
for o in geo_ruim["topos"][nome_bandeja]["ocorrencias"]:
    for c in o["corpos"]:
        lo, hi = c["min_mm"][1], c["max_mm"][1]
        c["min_mm"][1], c["max_mm"][1] = -hi, -lo
try:
    pl.preparar(geo_ruim, OraculoFalso(caixas), cfg, caminho_hp)
    bloqueou = False
except pl.ErroIdentificacao as e:
    bloqueou = "LADO" in str(e)
fonte = {}
for nome in ("api.py", "cena.py", "obstaculos.py", "pipeline.py", "__init__.py"):
    with open(os.path.join(RAIZ, "python", "posicionador", "fusion", nome), encoding="utf-8") as f:
        fonte[nome] = f.read()
imp = lambda t: sorted(set(re.findall(r"^\s*(?:import|from)\s+(adsk|numpy|scipy)\b", t, re.M)))  # noqa: E731
check("F identificação com FALHA bloqueia; só api.py importa adsk; nenhum importa numpy/scipy",
      bloqueou and imp(fonte["api.py"]) == ["adsk"] and all(imp(t) == [] for n, t in fonte.items() if n != "api.py"),
      f"bloqueou={bloqueou}; imports {{ {', '.join(f'{n}: {imp(t)}' for n, t in fonte.items())} }}")

# ---- G
class Proprio:
    def folga_segmento(self, a, b, raio, passo):
        return ("proprio", raio, passo)


esf = pg.Esfera((0.0, 0.0, 0.0), 0.1)
check("G hook de folga_segmento no núcleo",
      pg.folga_segmento(Proprio(), (0, 0, 0), (1, 0, 0), 0.5, 0.01) == ("proprio", 0.5, 0.01)
      and abs(pg.folga_segmento(esf, (0.3, 0, 0), (0.5, 0, 0), 0.0, 0.01) - (0.2 - 0.005)) < 1e-12,
      "primitivo com o método usa o dele; esfera segue a amostragem da SDF")

n_fail = sum(1 for r in results if r[1] == "FAIL")
print(f"\n{len(results) - n_fail} PASS, {n_fail} FAIL, de {len(results)} testes")
raise SystemExit(1 if n_fail else 0)
