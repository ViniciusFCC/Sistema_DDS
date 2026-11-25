"""
O núcleo puro dá o mesmo resultado no Python do repositório (3.13) e no Python 3.14 embutido no Fusion (fase 2, EDR-077).
Roda `tests/_nucleo_puro_resumo.py` (só biblioteca padrão: construção da v20, avaliação convergida com e sem obstáculos,
Nelder-Mead, brentq e uma busca com semente) nos dois interpretadores e compara tudo (tolerância 1e-9). Sem o Python do
Fusion (o `python.exe` em `%LOCALAPPDATA%\\Autodesk\\webdeploy\\production\\*\\Python\\`), sai NÃO EXECUTÁVEL (código 3).
Cena sintética de teste, não dado do carro. Sem ID de TC (aguarda autorização).
Roda como script: uv run python -X utf8 tests/test_posicionador_puro_interpretadores.py
"""
import glob
import json
import os
import subprocess
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TRABALHADOR = os.path.join(RAIZ, "tests", "_nucleo_puro_resumo.py")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def python_do_fusion():
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Autodesk", "webdeploy", "production", "*", "Python", "python.exe")
    achados = [p for p in glob.glob(base) if os.path.isfile(p)]
    return achados[0] if achados else None


def rodar(python):
    r = subprocess.run([python, "-I", "-X", "utf8", TRABALHADOR], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"{python}: código {r.returncode}\n{r.stderr[-1500:]}")
    return json.loads(r.stdout)


def difs(a, b, caminho=""):
    out = []
    if isinstance(a, dict):
        if set(a) != set(b):
            return [f"{caminho}: chaves {sorted(set(a) ^ set(b))}"]
        for k in a:
            out += difs(a[k], b[k], f"{caminho}/{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            return [f"{caminho}: tamanhos {len(a)} × {len(b)}"]
        for i, (x, y) in enumerate(zip(a, b)):
            out += difs(x, y, f"{caminho}[{i}]")
    elif isinstance(a, float) and isinstance(b, (int, float)):
        if abs(a - b) > 1e-9:
            out.append(f"{caminho}: {a} × {b}")
    elif a != b:
        out.append(f"{caminho}: {a!r} × {b!r}")
    return out


fusion = python_do_fusion()
if fusion is None:
    print("NÃO EXECUTÁVEL: Python embutido do Fusion não encontrado")
    sys.exit(3)
a, b = rodar(sys.executable), rodar(fusion)
va, vb = a.pop("python"), b.pop("python")
d = difs(a, b)
check("O núcleo puro no Python do Fusion = no Python do repositório", not d and va != vb and vb.startswith("3.14"),
      f"{va} × {vb}; diferenças: {d[:5]}; v20 com fixos {a['v20_com_fixos']['veredito']}; busca: {a['busca']['estatisticas'].get('n_amostras')} amostras")
n_fail = sum(1 for r in results if r[1] == "FAIL")
print(f"\n{len(results) - n_fail} PASS, {n_fail} FAIL, de {len(results)} testes")
sys.exit(1 if n_fail else 0)
