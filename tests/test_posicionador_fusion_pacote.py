"""
Pacote autônomo do Fusion (`tools/empacotar_fusion.py`): monta o pacote numa pasta temporária e roda o pipeline (sem a ponte
`api.py`, que precisa do Fusion) num interpretador limpo (`-I`), só com a pasta do pacote no caminho, com um oráculo mudo.
Prova que não falta módulo nem dado no pacote e que ele não importa numpy/scipy. Usa o Python 3.14 do Fusion se existir.
Sem ID de TC. Roda como script: uv run python -X utf8 tests/test_posicionador_fusion_pacote.py
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
import zipfile

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import empacotar_fusion as ef  # noqa: E402

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


FILHO = r'''
import json, sys, os
pasta = sys.argv[1]
sys.path.insert(0, os.path.join(pasta, "python"))
from posicionador import config as pc
from posicionador.fusion import pipeline as pl
geo = json.load(open(sys.argv[2], encoding="utf-8"))["geometria_por_componente"]
n = 0
for t in geo["topos"].values():
    for o in t["ocorrencias"]:
        for c in o["corpos"]:
            c["id"] = n; n += 1
class Mudo:
    n_chamadas = n_erros = 0; tempo_s = 0.0; ultimo_erro = None
    def dist_ponto(self, i, p): return 1e3
    def dist_segmento(self, i, a, b, r): return 1e3
cfg = pc.carregar(os.path.join(pasta, "data", "posicionador", "config_T11.json"))
d, res = pl.executar(geo, Mudo(), cfg, os.path.join(pasta, "data", "posicionador", "hardpoints_T11_v20_1_cad.csv"),
                     os.path.join(pasta, "saida"), {"n_amostras": 6, "n_refinos": 1, "semente": 0, "passo_m": 0.05, "max_aval_refino": 4, "n_finalistas": 1})
bad = sorted(m for m in sys.modules if m.split(".")[0] in ("numpy", "scipy", "adsk"))
print(json.dumps({"corpos": d["obstaculos"]["n_corpos_na_cena"], "amostras": d["estatisticas"]["n_amostras"], "proibidos": bad,
                  "arquivos": sorted(os.listdir(os.path.join(pasta, "saida")))}))
'''


def python_do_fusion():
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Autodesk", "webdeploy", "production", "*", "Python", "python.exe")
    achados = [p for p in glob.glob(base) if os.path.isfile(p)]
    return achados[0] if achados else sys.executable


with tempfile.TemporaryDirectory() as tmp:
    pasta, z = ef.montar(tmp)
    com = sorted(str(p.relative_to(pasta)).replace("\\", "/") for p in pasta.rglob("*") if p.is_file())
    with zipfile.ZipFile(z) as zf:
        no_zip = sorted(n for n in zf.namelist())
    essenciais = ["T11_posicionador.py", "T11_posicionador.manifest", "LEIA-ME.md", "posicionador_config.json",
                  "python/posicionador/fusion/api.py", "python/posicionador/puro/busca.py", "data/posicionador/config_T11.json",
                  "data/posicionador/hardpoints_T11_v20_1_cad.csv", "data/posicionador/origem_v20_script.json"]
    check("pacote contém os arquivos essenciais e o zip tem os mesmos", all(e in com for e in essenciais) and len(no_zip) == len(com),
          f"{len(com)} arquivos; faltando {[e for e in essenciais if e not in com]}")
    sond = os.path.join(RAIZ, "docs", "posicionador", "fusion", "fusion_sondagem3_copia_nomes_corrigidos_2026-11-24.json")
    py = python_do_fusion()
    r = subprocess.run([py, "-I", "-X", "utf8", "-c", FILHO, str(pasta), sond], capture_output=True, text=True, timeout=600)
    ok = r.returncode == 0
    out = json.loads(r.stdout.strip().splitlines()[-1]) if ok else {}
    check("pacote roda sozinho num interpretador limpo, sem numpy/scipy",
          ok and out.get("corpos") == 27 and not out.get("proibidos") and "resultado.json" in out.get("arquivos", []),
          f"{py}; {out if ok else r.stderr[-800:]}")
n_fail = sum(1 for x in results if x[1] == "FAIL")
print(f"\n{len(results) - n_fail} PASS, {n_fail} FAIL, de {len(results)} testes")
sys.exit(1 if n_fail else 0)
