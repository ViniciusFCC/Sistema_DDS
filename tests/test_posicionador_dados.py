"""
Testes dos dados do T11 e das curvas de referência do script atual (posicionador, EDR-076, Task 1).
TC-POS-001: load_hardpoints aceita v10 e v20 e o Corner resolve; o v20 tem push.
TC-POS-002: origem_v20_script.json com os três SHA-256 e a semente de 8 números.
Roda como script: uv run python -X utf8 tests/test_posicionador_dados.py
"""
import json
import os
import re

import hardpoints as hp
import kinematics_model as km

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "posicionador")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def p(nome):
    return os.path.join(RAIZ, nome)


# --- TC-POS-001 ---------------------------------------------------------------------------------------------------
try:
    hs10 = hp.load_hardpoints(p("hardpoints_T11_v10.csv"), p("hardpoints_T11_v10.meta.json"))
    hs20 = hp.load_hardpoints(p("hardpoints_T11_v20_script.csv"), p("hardpoints_T11_v20_script.meta.json"))
    c10, c20 = km.Corner(hs10, "FL"), km.Corner(hs20, "FL")
    s10, s20 = c10.solve(0.0), c20.solve(0.0)
    ok1 = (s10 is not None and s20 is not None and c20.has_push and not c10.has_push)
    det1 = f"v10 {len(hs10.points)} pontos, v20 {len(hs20.points)}; has_push v10={c10.has_push} v20={c20.has_push}"
except Exception as e:   # noqa: BLE001
    ok1, det1 = False, f"{type(e).__name__}: {e}"
check("TC-POS-001 v10 e v20 carregam e resolvem em dz=0", ok1, det1)

# --- TC-POS-002 ---------------------------------------------------------------------------------------------------
o = json.load(open(p("origem_v20_script.json"), encoding="utf-8"))
hexa = all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) for v in o["arquivos"].values())
ok2 = (set(o["arquivos"]) == {"t11_atuacao.py", "kinlib.py", "geometria_T11.json"} and hexa and len(o["x_semente"]) == 8
       and all(isinstance(v, (int, float)) for v in o["x_semente"]) and "unidades" in o and "config_do_script" in o)
check("TC-POS-002 origem com 3 SHA-256 e x_semente de 8 números", ok2, f"arquivos={list(o['arquivos'])}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
