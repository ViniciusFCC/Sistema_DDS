"""
Testes da ferramenta de linha de comando do posicionador (EDR-076, Task 8: tools/posicionar_atuacao.py).
TC-POS-080: `--avaliar-v20` sem STEP → código 0; `relatorio.md` diz INVIAVEL e cita a variação de MR; o relatório e o
            `resultado.json` trazem o rótulo "VERIFIED ≠ validado", o SHA-256 da configuração e os itens A_CONFIRMAR.
TC-POS-081: STEP real do chassi (data/cad/T11_chassi_2026-11-17.step), `--amostras 200 --semente 0` → código 0; cada
            conjunto `candidato_NN.csv`, com o seu meta, carrega com `hardpoints.load_hardpoints` (Status PROVISIONAL), e
            `candidatos.csv` lista um conjunto por linha; sem candidato, `resultado.json` traz só a `fase1`. O relatório
            carrega o SHA-256 do STEP e diz que a transformação STEP → carro é a HIPÓTESE da configuração.
As saídas vão para uma pasta temporária, nunca para o repositório. O TC-POS-081 precisa do extra opcional "cad"
(`uv sync --extra cad`); sem ele, o TC-POS-080 roda e o script sai NÃO EXECUTÁVEL (código 3), que nunca conta como PASS.
Roda como script: uv run python -X utf8 tests/test_posicionador_ferramenta.py
"""
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

if not cs.OCP_DISPONIVEL:
    print("NÃO EXECUTÁVEL: cadquery-ocp ausente para o TC-POS-081 (instale com `uv sync --extra cad`)")
    raise SystemExit(3)

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
    ok81 = (r81.returncode == 0 and saidas_ok and sha_step in rel and res.get("step_sha256") == sha_step
            and "transformacao_step_m" in rel and ROTULO in rel and sha_cfg in rel)
    check("TC-POS-081 STEP real, 200 amostras, semente 0: conjuntos carregam com load_hardpoints (ou só fase1)", ok81,
          f"código {r81.returncode}; {modo}; erros {erros[:3]}; SHA do STEP no relatório={sha_step in rel}; "
          f"transformação da configuração citada={'transformacao_step_m' in rel}; {dt81:.1f} s; "
          f"stderr (fim): {r81.stderr.strip()[-300:]!r}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
