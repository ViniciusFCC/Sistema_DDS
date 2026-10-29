"""
Teste do executor dos testes (EDR-068, incremento 7, Task 1).
TC-RUN-001: (a) filho com neto que dorme: o tempo-limite volta em segundos e encerra o neto (o `subprocess.run` com
            capture_output esperava o neto soltar o pipe: 60,5 s medidos para um timeout de 3 s); (b) saída normal em
            UTF-8; (c) Orcamento; (d) a regra da mutação da planilha: com DDS_ORCAMENTO_S=5 e um teste que trava, o
            mutante conta como NÃO detectado (tempo), em poucos segundos e sem 2ª tentativa.
Roda como script: uv run python -X utf8 tests/test_executor.py
"""
import os
import subprocess
import sys
import tempfile
import time

import executor_testes as ex

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
results = []

FILHO_COM_NETO = (
    "import subprocess, sys, time\n"
    "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"   # herda stdout/stderr
    "open(sys.argv[1], 'w').write(str(p.pid))\n"
    "time.sleep(60)\n"
)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def existe(pid):
    saida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True).stdout.decode("cp850", "replace")
    return any(l.split()[1:2] == [str(pid)] for l in saida.splitlines() if l.strip())


with tempfile.TemporaryDirectory() as d:
    # (a) filho travado com neto
    script, pidf = os.path.join(d, "filho.py"), os.path.join(d, "neto.pid")
    with open(script, "w") as fh:
        fh.write(FILHO_COM_NETO)
    a = ex.executar([sys.executable, "-X", "utf8", script, pidf], cwd=d, timeout_s=3)
    neto = int(open(pidf).read())
    time.sleep(1)
    vivo = existe(neto)
    ok_a = a.estourou is True and a.returncode == ex.CODIGO_TEMPO and a.tempo_s < 15 and not vivo
    if vivo:
        subprocess.run(["taskkill", "/PID", str(neto), "/T", "/F"], capture_output=True)   # limpeza por PID
    # (b) saída normal
    b = ex.executar([sys.executable, "-X", "utf8", "-c", 'print("ok \\xe1")'], cwd=d, timeout_s=30)
    ok_b = b.stdout.strip() == "ok á" and b.returncode == 0 and b.estourou is False
    # (c) orçamento
    o = ex.Orcamento(10)
    ok_c = o.cabe(11) is False and o.cabe(5) is True
    # (d) regra da mutação da planilha
    import mutation_planilha_equilibrio as mp
    trava = os.path.join(d, "trava.py")
    with open(trava, "w") as fh:
        fh.write("import time\ntime.sleep(60)\n")
    antigo = os.environ.get("DDS_ORCAMENTO_S")
    os.environ["DDS_ORCAMENTO_S"] = "5"
    try:
        orc = ex.orcamento_do_ambiente(7000)
    finally:
        if antigo is None:
            del os.environ["DDS_ORCAMENTO_S"]
        else:
            os.environ["DDS_ORCAMENTO_S"] = antigo
    t0 = time.monotonic()
    r = mp.rodar(mp.src, teste=trava, orcamento=orc)
    dur = time.monotonic() - t0
    ok_d = (abs(orc.total_s - 5) < 1e-9 and r.estourou is True and r.returncode == ex.CODIGO_TEMPO and dur < 15
            and mp.detectado(r) is False and r.stderr.count("TIMEOUT") == 1)

    check("TC-RUN-001 executor: tempo-limite encerra a árvore, saída UTF-8, orçamento e regra da mutação",
          ok_a and ok_b and ok_c and ok_d,
          f"(a) estourou={a.estourou}, código={a.returncode}, {a.tempo_s:.1f} s, neto {neto} vivo={vivo}; "
          f"(b) {b.stdout.strip()!r}, código={b.returncode}; (c) {ok_c}; "
          f"(d) estourou={r.estourou}, {dur:.1f} s, detectado={mp.detectado(r)}, orçamento={orc.total_s:g}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
