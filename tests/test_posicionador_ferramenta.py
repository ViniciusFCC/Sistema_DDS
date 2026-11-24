"""
Testes da ferramenta de linha de comando do posicionador (EDR-076, Task 8: tools/posicionar_atuacao.py).
TC-POS-080: `--avaliar-v20` sem STEP → código 0; `relatorio.md` diz INVIAVEL e cita a variação de MR; o relatório e o
            `resultado.json` trazem o rótulo "VERIFIED ≠ validado", o SHA-256 da configuração e os itens A_CONFIRMAR.
TC-POS-081: STEP real do chassi (data/cad/T11_chassi_2026-11-17.step), `--amostras 200 --semente 0` → código 0; cada
            conjunto `candidato_NN.csv`, com o seu meta, carrega com `hardpoints.load_hardpoints` (Status PROVISIONAL), e
            `candidatos.csv` lista um conjunto por linha; sem candidato, `resultado.json` traz só a `fase1`. O relatório
            carrega o SHA-256 do STEP e diz que a transformação STEP → carro é a HIPÓTESE da configuração. A caixa de busca
            derivada do envelope do chassi (decisão R8, HIPOTESE) contém o pivô da v20 (`FL_ROCKER_AXIS_A` de
            data/posicionador/hardpoints_T11_v20_script.csv).
TC-POS-082: busca sem STEP com configuração SINTÉTICA folgada e `--caixa` SINTÉTICA (revisão final, M8, M3, I2, M5) →
            código 0 e ao menos um candidato; cada `candidato_NN.csv` carrega com `load_hardpoints` (Status PROVISIONAL) e
            tem um sufixo só no `geometry_rev`; `candidatos.csv` tem uma linha por candidato; nenhum candidato é VIAVEL;
            o relatório traz os limites da fase (por que não há VIAVEL e a incerteza) e o `resultado.json` traz a lista
            fixa do que não está modelado.
TC-POS-083: entrada inválida → código 2 com mensagem (M2, I3): `--caixa` invertida (mín > máx) e com mín = máx num eixo, e
            configuração SINTÉTICA com item obrigatório `mr_alvo` nulo (A_CONFIRMAR).
As saídas vão para uma pasta temporária, nunca para o repositório. O TC-POS-081 precisa do extra opcional "cad"
(`uv sync --extra cad`); sem ele, os TC-POS-080, 082 e 083 rodam e o script sai NÃO EXECUTÁVEL (código 3), que nunca conta
como PASS (ou com código 1, se algum deles falhou).
Roda como script: uv run python -X utf8 tests/test_posicionador_ferramenta.py
"""
import copy
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

import hardpoints as hp
from posicionador import cad_step as cs
from posicionador import config as pc
from posicionador import varredura as vr

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FERRAMENTA = os.path.join(RAIZ, "tools", "posicionar_atuacao.py")
CFG = os.path.join(RAIZ, "data", "posicionador", "config_T11.json")
STEP_REAL = os.path.join(RAIZ, "data", "cad", "T11_chassi_2026-11-17.step")
ROTULO = "VERIFIED ≠ validado"

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def sha256(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rodar(*args, timeout=1500):
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-X", "utf8", FERRAMENTA, *args], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout, env=dict(os.environ, PYTHONUTF8="1"))
    return r, time.perf_counter() - t0


def ler(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


a_confirmar = pc.carregar(CFG).a_confirmar()
sha_cfg = sha256(CFG)

# --- TC-POS-080 ---------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    r80, dt80 = rodar("--avaliar-v20", "--config", CFG, "--saida", tmp)
    rel = ler(os.path.join(tmp, "relatorio.md"))
    try:
        res = json.loads(ler(os.path.join(tmp, "resultado.json")))
    except json.JSONDecodeError:
        res = {}
    ok80 = (r80.returncode == 0 and "INVIAVEL" in rel and "variação de MR" in rel and ROTULO in rel
            and sha_cfg in rel and all(n in rel for n in a_confirmar) and res.get("modo") == "avaliar-v20"
            and res.get("config_sha256") == sha_cfg and ROTULO in res.get("rotulo", "")
            and (res.get("v20") or {}).get("veredito") == "INVIAVEL")
    check("TC-POS-080 --avaliar-v20 sem STEP: INVIAVEL e variação de MR no relatório", ok80,
          f"código {r80.returncode}; INVIAVEL={'INVIAVEL' in rel}; variação de MR={'variação de MR' in rel}; "
          f"rótulo={ROTULO in rel}; SHA da config={sha_cfg in rel}; A_CONFIRMAR listados="
          f"{[n for n in a_confirmar if n in rel]}; veredito no JSON={(res.get('v20') or {}).get('veredito')}; "
          f"{dt80:.1f} s; stderr: {r80.stderr.strip()[-300:]!r}")

# --- TC-POS-082 ---------------------------------------------------------------------------------------------------
with open(CFG, encoding="utf-8") as f:
    bruto = json.load(f)


def cfg_sintetica(pasta, valores, tc, origem="HIPOTESE"):
    """Grava em `pasta` uma cópia SINTÉTICA da configuração do T11 com os valores trocados; devolve o caminho."""
    d = copy.deepcopy(bruto)
    for nome, valor in valores.items():
        d["itens"][nome].update(valor=valor, origem=origem, fonte=f"SINTÉTICO de teste ({tc})")
    p = os.path.join(pasta, f"config_{tc}.json")
    with open(p, "w", encoding="utf-8") as g:
        json.dump(d, g)
    return p


CAIXA = "-0.15,0.24,0.42,0.15,0.34,0.53"     # SINTÉTICA (a mesma do tests/test_posicionador_busca.py)
meta10 = json.loads(ler(os.path.join(RAIZ, "data", "posicionador", "hardpoints_T11_v10.meta.json")))
with tempfile.TemporaryDirectory() as tmp:
    cfg82 = cfg_sintetica(tmp, {"mr_var_max": 0.5, "curso_amortecedor_m": 0.21}, "TC-POS-082")
    saida = os.path.join(tmp, "saida")
    r82, dt82 = rodar("--config", cfg82, "--saida", saida, f"--caixa={CAIXA}", "--amostras", "60", "--refinos", "2",
                      "--semente", "1")
    rel = ler(os.path.join(saida, "relatorio.md"))
    try:
        res = json.loads(ler(os.path.join(saida, "resultado.json")))
    except json.JSONDecodeError:
        res = {}
    cands = res.get("candidatos") or []
    erros, revs = [], []
    for k, c in enumerate(cands, start=1):
        try:
            hs = hp.load_hardpoints(os.path.join(saida, c["arquivo_csv"]), os.path.join(saida, c["arquivo_meta"]))
            revs.append(hs.meta["geometry_rev"])
            if set(p.status for p in hs.points.values()) != {"PROVISIONAL"}:
                erros.append(f"{c['arquivo_csv']}: Status {hs.status_summary()}")
            if hs.meta["geometry_rev"] != f"{meta10['geometry_rev']} + atuação do posicionador, candidato {k:02d}":
                erros.append(f"{c['arquivo_csv']}: geometry_rev {hs.meta['geometry_rev']!r}")
        except Exception as e:  # noqa: BLE001
            erros.append(f"{c.get('arquivo_csv')}: {type(e).__name__}: {e}")
    linhas = []
    if os.path.exists(os.path.join(saida, "candidatos.csv")):
        with open(os.path.join(saida, "candidatos.csv"), newline="", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
    vered = [(c.get("avaliacao") or {}).get("veredito") for c in cands]
    nm = res.get("nao_modelado") or []
    ok82 = (r82.returncode == 0 and len(cands) >= 1 and not erros and len(linhas) == len(cands)
            and all(v == "CONDICIONAL" for v in vered) and "Limites desta fase" in rel and vr.NOME_MANGA in rel
            and "δ" in rel and all(x in nm for x in vr.NAO_MODELADO_FASE1))
    check("TC-POS-082 busca sem STEP, configuração SINTÉTICA folgada: conjuntos por candidato e não modelado", ok82,
          f"código {r82.returncode}; {len(cands)} candidatos {vered}; erros {erros[:3]}; linhas do candidatos.csv "
          f"{len(linhas)}; geometry_rev {revs[:1]}; limites da fase no relatório={'Limites desta fase' in rel}; "
          f"não modelado no JSON: {sum(x in nm for x in vr.NAO_MODELADO_FASE1)}/{len(vr.NAO_MODELADO_FASE1)}; {dt82:.1f} s; "
          f"stderr (fim): {r82.stderr.strip()[-200:]!r}")

# --- TC-POS-083 ---------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    inv, _ = rodar("--config", CFG, "--saida", os.path.join(tmp, "a"), "--caixa=0.15,0.24,0.42,-0.15,0.34,0.53",
                   "--amostras", "1", timeout=300)
    igual, _ = rodar("--config", CFG, "--saida", os.path.join(tmp, "b"), "--caixa=-0.15,0.30,0.42,0.15,0.30,0.53",
                     "--amostras", "1", timeout=300)
    cfg83 = cfg_sintetica(tmp, {"mr_alvo": None}, "TC-POS-083", origem="A_CONFIRMAR")
    nulo, _ = rodar("--config", cfg83, "--saida", os.path.join(tmp, "c"), "--avaliar-v20", timeout=300)
ok83 = (inv.returncode == 2 and "mín ≥ máx em X" in inv.stderr and igual.returncode == 2 and "mín ≥ máx em Y"
        in igual.stderr and nulo.returncode == 2 and "'mr_alvo'" in nulo.stderr and "Traceback" not in
        inv.stderr + igual.stderr + nulo.stderr)
check("TC-POS-083 --caixa invertida ou com mín = máx e item obrigatório nulo: código 2 com mensagem", ok83,
      f"invertida: {inv.returncode} {inv.stderr.strip()[-160:]!r}; mín = máx: {igual.returncode} "
      f"{igual.stderr.strip()[-120:]!r}; mr_alvo nulo: {nulo.returncode} {nulo.stderr.strip()[-160:]!r}")

if not cs.OCP_DISPONIVEL:
    print("NÃO EXECUTÁVEL: cadquery-ocp ausente para o TC-POS-081 (instale com `uv sync --extra cad`)")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    raise SystemExit(1 if n_fail else 3)

# --- TC-POS-081 ---------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    r81, dt81 = rodar("--step", STEP_REAL, "--config", CFG, "--saida", tmp, "--amostras", "200", "--semente", "0")
    rel = ler(os.path.join(tmp, "relatorio.md"))
    try:
        res = json.loads(ler(os.path.join(tmp, "resultado.json")))
    except json.JSONDecodeError:
        res = {}
    cands = res.get("candidatos") or []
    carregados, erros, linhas = 0, [], []
    for c in cands:
        try:
            hs = hp.load_hardpoints(os.path.join(tmp, c["arquivo_csv"]), os.path.join(tmp, c["arquivo_meta"]))
            if set(p.status for p in hs.points.values()) == {"PROVISIONAL"}:
                carregados += 1
            else:
                erros.append(f"{c['arquivo_csv']}: Status {hs.status_summary()}")
        except Exception as e:  # noqa: BLE001
            erros.append(f"{c.get('arquivo_csv')}: {type(e).__name__}: {e}")
    if os.path.exists(os.path.join(tmp, "candidatos.csv")):
        with open(os.path.join(tmp, "candidatos.csv"), newline="", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
    if cands:
        saidas_ok = carregados == len(cands) and not erros and len(linhas) == len(cands)
        modo = f"{len(cands)} candidatos, {carregados} carregados"
    else:
        saidas_ok = res.get("fase1") is not None and not linhas
        modo = f"sem candidato; fase1: {(res.get('fase1') or {}).get('motivo', '')[:200]!r}"
    sha_step = sha256(STEP_REAL)
    hs20 = hp.load_hardpoints(os.path.join(RAIZ, "data", "posicionador", "hardpoints_T11_v20_script.csv"),
                              os.path.join(RAIZ, "data", "posicionador", "hardpoints_T11_v20_script.meta.json"))
    pv20 = hs20.points["FL_ROCKER_AXIS_A"].xyz
    cx = res.get("caixa_busca_pivo_m") or {}
    try:
        lo, hi = [float(v) for v in cx["min_m"]], [float(v) for v in cx["max_m"]]
        dentro = all(a <= p <= b for a, p, b in zip(lo, pv20, hi))
    except (KeyError, TypeError, ValueError):
        lo = hi = None
        dentro = False
    ok81 = (r81.returncode == 0 and saidas_ok and sha_step in rel and res.get("step_sha256") == sha_step
            and "transformacao_step_m" in rel and ROTULO in rel and sha_cfg in rel and dentro
            and cx.get("origem") == "HIPOTESE")
    check("TC-POS-081 STEP real, 200 amostras, semente 0: conjuntos carregam com load_hardpoints (ou só fase1)", ok81,
          f"código {r81.returncode}; {modo}; erros {erros[:3]}; SHA do STEP no relatório={sha_step in rel}; "
          f"transformação da configuração citada={'transformacao_step_m' in rel}; caixa {lo} a {hi} m "
          f"({cx.get('origem')}), pivô da v20 {[round(float(v), 4) for v in pv20]} dentro={dentro}; {dt81:.1f} s; "
          f"stderr (fim): {r81.stderr.strip()[-300:]!r}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
