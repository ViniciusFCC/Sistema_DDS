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


def lido_pid(caminho):
    try:
        with open(caminho) as fh:
            return int(fh.read())
    except (OSError, ValueError):
        return None


def existe(pid):
    saida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True).stdout.decode("cp850", "replace")
    return any(l.split()[1:2] == [str(pid)] for l in saida.splitlines() if l.strip())


with tempfile.TemporaryDirectory() as d:
    # (a) filho travado com neto
    script, pidf = os.path.join(d, "filho.py"), os.path.join(d, "neto.pid")
    with open(script, "w") as fh:
        fh.write(FILHO_COM_NETO)
    a = ex.executar([sys.executable, "-X", "utf8", script, pidf], cwd=d, timeout_s=3)
    neto = lido_pid(pidf)
    time.sleep(1)
    vivo = neto is None or existe(neto)    # sem arquivo de PID: FAIL (vivo=True), não exceção
    ok_a = neto is not None and a.estourou is True and a.returncode == ex.CODIGO_TEMPO and a.tempo_s < 15 and not vivo
    if neto is not None and vivo:
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
    os.environ["DDS_ORCAMENTO_S"] = "8"
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
    ok_d = (abs(orc.total_s - 8) < 1e-9 and r.estourou is True and r.returncode == ex.CODIGO_TEMPO and dur < 15
            and mp.detectado(r) is False and r.stderr.count("TIMEOUT") == 1)

    # (e) exceção durante a espera (como Ctrl+C): o finally encerra a árvore, o neto não sobra e a exceção sobe
    pid_e = os.path.join(d, "neto_e.pid")

    class PopenInterrompido(subprocess.Popen):
        interrompido = False

        def wait(self, timeout=None):
            if PopenInterrompido.interrompido:     # só a 1ª espera (a do executor); o taskkill também usa Popen
                return super().wait(timeout)
            PopenInterrompido.interrompido = True
            for _ in range(200):               # espera o filho gravar o PID do neto, depois "interrompe"
                if os.path.exists(pid_e) and os.path.getsize(pid_e) > 0:
                    break
                time.sleep(0.05)
            raise KeyboardInterrupt

    original_popen = ex.subprocess.Popen
    ex.subprocess.Popen = PopenInterrompido
    levantou = False
    try:
        ex.executar([sys.executable, "-X", "utf8", script, pid_e], cwd=d, timeout_s=60)
    except KeyboardInterrupt:
        levantou = True
    finally:
        ex.subprocess.Popen = original_popen
    neto_e = lido_pid(pid_e)
    time.sleep(1)
    vivo_e = neto_e is None or existe(neto_e)
    if neto_e is not None and vivo_e:
        subprocess.run(["taskkill", "/PID", str(neto_e), "/T", "/F"], capture_output=True)
    ok_e = levantou and neto_e is not None and not vivo_e

    check("TC-RUN-001 executor: tempo-limite encerra a árvore, saída UTF-8, orçamento e regra da mutação",
          ok_a and ok_b and ok_c and ok_d and ok_e,
          f"(a) estourou={a.estourou}, código={a.returncode}, {a.tempo_s:.1f} s, neto {neto} vivo={vivo}; "
          f"(b) {b.stdout.strip()!r}, código={b.returncode}; (c) {ok_c}; "
          f"(d) estourou={r.estourou}, {dur:.1f} s, detectado={mp.detectado(r)}, orçamento={orc.total_s:g}; (e) levantou={levantou}, neto {neto_e} vivo={vivo_e}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
