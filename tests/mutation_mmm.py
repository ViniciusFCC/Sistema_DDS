"""Mutação do MMM (V4.2, inc. 6, Task 8): cinco mutações dos termos novos de python/mmm.py.

Padrão de tests/mutation_equilibrio.py: pré-checagem do original; uma mutação está "detectada" quando algum dos
testes (test_mmm.py, depois test_escada.py) sai com código != 0 e com [FAIL] na saída. Para poupar tempo
(test_mmm.py ~2 min, test_escada.py ~6 min), o test_escada.py só roda se o test_mmm.py não pegou o mutante.
A cópia mutada fica numa pasta temporária posta no PYTHONPATH, que vem antes do python/ instalado pelo uv
(.pth do site-packages); os testes rodam do repositório (precisam de data/ e excel/, só leitura). A sonda
confirma que o mmm importado (por si e pelo escada) é a cópia. O arquivo do repositório não muda.
Roda como script: uv run python -X utf8 tests/mutation_mmm.py
"""
import os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TESTES = [os.path.join('tests', 'test_mmm.py'), os.path.join('tests', 'test_escada.py')]
src = open(os.path.join(ROOT, 'python', 'mmm.py'), encoding='utf-8').read()
RE_RESUMO = re.compile(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$')


def preparar(fonte):
    """Cria a pasta temporária com a cópia de mmm.py e devolve (pasta, env), depois de conferir a origem."""
    d = tempfile.mkdtemp(prefix='dds_mut_mmm_')
    with open(os.path.join(d, 'mmm.py'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(fonte)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=d + os.pathsep + os.environ.get('PYTHONPATH', ''))
    sonda = subprocess.run([sys.executable, '-X', 'utf8', '-c',
                            'import mmm, escada; print(mmm.__file__); print(escada.mmm.__file__)'],
                           cwd=ROOT, env=env, capture_output=True, text=True)
    origens = sonda.stdout.split()
    alvo = os.path.normcase(os.path.abspath(os.path.join(d, 'mmm.py')))
    if sonda.returncode != 0 or len(origens) != 2 or any(os.path.normcase(os.path.abspath(o)) != alvo for o in origens):
        shutil.rmtree(d, ignore_errors=True)
        print('ERRO: o mmm importado não é a cópia temporária ->', origens or sonda.stderr[-500:]); sys.exit(2)
    return d, env


def rodar_teste(env, t):
    return subprocess.run([sys.executable, '-X', 'utf8', t], cwd=ROOT, env=env, capture_output=True,
                          text=True, encoding='utf-8', errors='replace')


def pegou(o):
    return o.returncode != 0 and '[FAIL]' in o.stdout


def rodar(fonte, parar_no_primeiro_fail):
    """Roda os testes em ordem com a cópia `fonte`; devolve [(teste, saída)]. Para após o primeiro que pegar."""
    d, env = preparar(fonte)
    try:
        res = []
        for t in TESTES:
            o = rodar_teste(env, t)
            res.append((t, o))
            if parar_no_primeiro_fail and pegou(o):
                break
        return res
    finally:
        shutil.rmtree(d, ignore_errors=True)


muts = {
    # alfa_rodas, caminho padrão (alfa_ref None): α_F = β + a/R − δ (Milliken p. 307), o usado pelo trim
    # da planilha. O caminho cinemático usa x_i/R das posições e não tem o literal a/R.
    "alfa_rodas: sinal do termo a/R":
        ('alfa_ref = {"F": beta_rad + cfg.cg_to_front / R - delta_rad,',
         'alfa_ref = {"F": beta_rad - cfg.cg_to_front / R - delta_rad,'),
    "alfa_rodas: b/R no lugar de a/R":
        ('alfa_ref = {"F": beta_rad + cfg.cg_to_front / R - delta_rad,',
         'alfa_ref = {"F": beta_rad + cfg.cg_to_rear / R - delta_rad,'),
    "_estabilizante: cn_estabilizante = +cn_iso (fonte única do sinal)":
        ("    return -cn_iso\n", "    return cn_iso\n"),
    "balanço: sem o termo −m·A·sen β em fx_exigido='balanco'":
        ("for c in _FRENTE) - m * ay_ms2 * math.sin(beta_rad)\n", "for c in _FRENTE)\n"),
    "cos_delta='trim': cos δ_ref = L/R no lugar do δ do trim":
        ("            fy[c] = fy_pneu[c] * math.cos(steer[c])    # + Fx_pneu·sen δ_i",
         "            fy[c] = fy_pneu[c] * math.cos(L / R)    # + Fx_pneu·sen δ_i"),
}

t0 = time.time()
d0, env0 = preparar(src)
try:
    outs = [(t, rodar_teste(env0, t)) for t in TESTES]
finally:
    shutil.rmtree(d0, ignore_errors=True)
for t, out in outs:
    resumo = (out.stdout.strip().splitlines() or [''])[-1]
    m = RE_RESUMO.match(resumo)
    if out.returncode != 0 or not m or m.group(1) != m.group(2) or int(m.group(1)) == 0:
        print('PRE-CHECAGEM FALHOU: original ->', t, resumo, '| código', out.returncode); print(out.stderr[-2000:]); sys.exit(2)
print('PRE-CHECAGEM OK: original ->', ' | '.join(
    f"{os.path.basename(t)}: {(o.stdout.strip().splitlines() or [''])[-1]}" for t, o in outs), flush=True)

det = 0
for name, (a, b) in muts.items():
    assert src.count(a) == 1, name
    ti = time.time()
    res = rodar(src.replace(a, b, 1), True)
    pegos = [t for t, o in res if pegou(o)]
    ok = bool(pegos)
    det += ok
    falhas = [l.split('  ')[0] for t, o in res if pegou(o) for l in o.stdout.splitlines() if l.startswith('[FAIL]')]
    print(('DETECTADO     ' if ok else 'NÃO DETECTADO '), name, '->',
          '; '.join(falhas) if falhas else 'nenhum FAIL',
          f"[{', '.join(os.path.basename(t) for t in pegos) or '-'}; {time.time() - ti:.0f} s]", flush=True)
print(f"{det}/{len(muts)} mutantes mortos" if det == len(muts) else f"{det}/{len(muts)} mutantes mortos (SOBREVIVENTES)")
print(det, '/', len(muts))  # linha de resumo no formato que tools/rodar_testes.py (RE_MUTACAO) lê
print(f"tempo total: {time.time() - t0:.0f} s")
sys.exit(0 if det == len(muts) else 1)
