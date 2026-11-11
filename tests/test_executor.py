"""
Teste do executor dos testes (EDR-068, incremento 7, Task 1).
TC-RUN-001: (a) filho com neto que dorme: o tempo-limite volta em segundos e encerra o neto (o `subprocess.run` com
            capture_output esperava o neto soltar o pipe: 60,5 s medidos para um timeout de 3 s); (b) saída normal em
            UTF-8; (c) Orcamento; (d) a regra da mutação da planilha: com DDS_ORCAMENTO_S=8 e um teste que trava, o
            mutante conta como NÃO detectado (tempo), em poucos segundos e sem 2ª tentativa; (e) o Ctrl+C simulado
            durante a espera; (f) a opção --pular-recentes do rodar_testes (módulos locais transitivos, diff do commit).
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


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
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

    # (f) --pular-recentes: só pula com o código do teste e dos módulos locais (transitivos) sem diff desde o commit
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import rodar_testes as rt
    rep = os.path.join(d, "rep")
    for sub in ("python", "tests"):
        os.makedirs(os.path.join(rep, sub))

    def escreve(rel, txt):
        with open(os.path.join(rep, rel), "w", encoding="utf-8") as fh:
            fh.write(txt)

    def g(*args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=rep,
                              capture_output=True, text=True)

    escreve("python/folha.py", "X = 1\n")
    escreve("python/meio.py", "import folha\nimport os\n")
    escreve("tests/t.py", "import meio\nfrom json import loads\n")
    escreve("tests/outro.py", "X = 1\n")
    g("init", "-q")
    g("add", "-A")
    g("commit", "-q", "-m", "a")
    c0 = g("rev-parse", "HEAD").stdout.strip()
    mods = rt.modulos_locais("tests/t.py", rep)
    ok_f1 = mods == ["python/folha.py", "python/meio.py"] and rt.modulos_locais("tests/outro.py", rep) == []
    ok_f2 = rt.pode_pular("tests/t.py", c0, rep) is True
    escreve("python/folha.py", "X = 2\n")                      # mudança não commitada num módulo transitivo
    ok_f3 = rt.pode_pular("tests/t.py", c0, rep) is False and rt.pode_pular("tests/outro.py", c0, rep) is True
    g("commit", "-q", "-am", "b")                              # agora commitada: continua sem poder pular
    ok_f4 = rt.pode_pular("tests/t.py", c0, rep) is False
    ok_f5 = rt.pode_pular("tests/t.py", "0" * 40, rep) is False      # commit desconhecido: roda
    arq = os.path.join(d, "recentes.json")
    with open(arq, "w") as fh:
        fh.write('{"tests/outro.py": "%s"}' % c0)
    ok_f6 = rt.ler_recentes(arq) == {"tests/outro.py": c0}
    

    # (g) o laço do CA-05 com a opção: um teste que roda ANTES de um pulado não pode apagar a lista de pulados (defeito achado
    # na revisão: a variável dos [SKIP] sobrescrevia a lista); o pulado nunca vira PASS
    def script_pass(nome):
        caminho = os.path.join(d, nome)
        with open(caminho, "w", encoding="utf-8") as fh:
            fh.write("print('[PASS] x')\nprint('1 PASS, 0 FAIL, de 1 testes')\n")
        return caminho

    sa, sb, sc = script_pass("ga.py"), script_pass("gb.py"), script_pass("gc.py")
    fakes = [("a", sa, 1, "f"), ("b", sb, 1, "f"), ("c", sc, 1, "f")]
    lista_p, resumo_g, md_g = [], [], []
    try:
        rt.rodar_lista_testes(fakes, lambda s: "abc1234" if s == sb else None, lista_p, resumo_g, md_g)
        ok_g = (lista_p == [(sb, "abc1234")] and [x[2] for x in resumo_g] == ["PASS", "PULADO", "PASS"]
                and sum("PULADO (passou em abc1234" in l for l in md_g) == 1)
    except Exception as e:      # noqa: BLE001  (o defeito aparece aqui como AttributeError)
        ok_g = False
        print("  (g) exceção:", type(e).__name__, e)
    # (h) entradas declaradas, arquivo não rastreado e chave desconhecida
    escreve("data.csv", "1\n")
    escreve("tests/mut.py", "import folha\n")
    g("add", "-A")
    g("commit", "-q", "-m", "c")
    c1 = g("rev-parse", "HEAD").stdout.strip()
    dec = ("data.csv", "python/meio.py")
    ok_h1 = rt.pode_pular("tests/mut.py", c1, rep, declaradas=dec) is True
    escreve("data.csv", "2\n")                                  # declarado mudou na árvore: roda
    ok_h2 = rt.pode_pular("tests/mut.py", c1, rep, declaradas=dec) is False
    g("checkout", "--", "data.csv")
    ok_h3 = rt.pode_pular("tests/mut.py", c1, rep, declaradas=("nao_existe.csv",)) is False   # declarado inexistente: roda
    escreve("python/novo.py", "Y = 1\n")                        # módulo novo não rastreado no conjunto: roda
    escreve("tests/mut.py", "import folha\nimport novo\n")
    ok_h4 = rt.pode_pular("tests/mut.py", c1, rep) is False
    ok_h5 = rt.chaves_desconhecidas({"tests/test_executor.py": "x", "tests/nada.py": "y"}) == ["tests/nada.py"]

    # (i) laço da mutação (CA-06): PASS com a pré-checagem e o placar; FAIL sem placar completo ou sem pré-checagem; PULADO
    def script_texto(nome, linhas, codigo=0):
        caminho = os.path.join(d, nome)
        corpo = "".join(f"print({l!r})\n" for l in linhas) + f"raise SystemExit({codigo})\n"
        with open(caminho, "w", encoding="utf-8") as fh:
            fh.write(corpo)
        return caminho

    ma = script_texto("ma.py", ["PRE-CHECAGEM OK: x", "2 / 2"])
    mb = script_texto("mb.py", ["PRE-CHECAGEM OK: x", "1 / 2"])
    mc = script_texto("mc.py", ["2 / 2"])
    md_py = script_texto("md.py", ["PRE-CHECAGEM OK: x", "2 / 2"])
    pulados_i, resumo_i, md_i = [], [], []
    try:
        rt.rodar_lista_mutacao([(ma, 2), (mb, 2), (mc, 2), (md_py, 2)], lambda s: "abc1234" if s == md_py else None,
                               pulados_i, resumo_i, md_i)
        ok_i = ([x[2] for x in resumo_i] == ["PASS", "FAIL", "FAIL", "PULADO"] and pulados_i == [(md_py, "abc1234")]
                and any("AUSENTE" in l for l in md_i))
    except Exception as e:      # noqa: BLE001
        ok_i = False
        print("  (i) exceção:", type(e).__name__, e)
    # (j) laço das planilhas (CA-09): PASS com o resumo, NÃO EXECUTÁVEL com código 3, PULADO
    pa = script_texto("pa.py", ["MOTOR: excel", "1 PASS, 0 FAIL, de 1 testes"])
    pb = script_texto("pb.py", ["NÃO EXECUTÁVEL: sem motor"], codigo=3)
    pc = script_texto("pc.py", ["MOTOR: excel", "1 PASS, 0 FAIL, de 1 testes"])
    pulados_j, resumo_j, md_j = [], [], []
    try:
        rt.rodar_lista_planilhas([(pa, 1, "f"), (pb, 1, "f"), (pc, 1, "f")], lambda s: "abc1234" if s == pc else None,
                                 pulados_j, resumo_j, md_j)
        ok_j = ([x[2] for x in resumo_j] == ["PASS", "NÃO EXECUTÁVEL", "PULADO"] and pulados_j == [(pc, "abc1234")]
                and any("MOTOR: excel" in l for l in md_j) and pa not in rt.TIMEOUT_PLANILHAS
                and rt.TIMEOUT_PLANILHAS == {"tests/test_workbook_v4_3.py": 7200, "tests/test_workbook_v4_4.py": 7200})
    except Exception as e:      # noqa: BLE001
        ok_j = False
        print("  (j) exceção:", type(e).__name__, e)
    ok_f = all((ok_f1, ok_f2, ok_f3, ok_f4, ok_f5, ok_f6, ok_g, ok_h1, ok_h2, ok_h3, ok_h4, ok_h5, ok_i, ok_j))

    check("TC-RUN-001 executor: tempo-limite encerra a árvore, saída UTF-8, orçamento, regra da mutação e --pular-recentes",
          ok_a and ok_b and ok_c and ok_d and ok_e and ok_f,
          f"(a) estourou={a.estourou}, código={a.returncode}, {a.tempo_s:.1f} s, neto {neto} vivo={vivo}; "
          f"(b) {b.stdout.strip()!r}, código={b.returncode}; (c) {ok_c}; "
          f"(d) estourou={r.estourou}, {dur:.1f} s, detectado={mp.detectado(r)}, orçamento={orc.total_s:g}; (e) levantou={levantou}, neto {neto_e} vivo={vivo_e}; "
          f"(f) {[ok_f1, ok_f2, ok_f3, ok_f4, ok_f5, ok_f6, ok_g, ok_h1, ok_h2, ok_h3, ok_h4, ok_h5, ok_i, ok_j]}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
