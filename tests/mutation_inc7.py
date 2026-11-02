"""Mutação Python do incremento 7 (Task 7): cinco mutações, uma por ponto novo da física do inc. 7.

Padrão de tests/mutation_mmm.py: pré-checagem do original; cópia mutada de UM módulo numa pasta temporária posta no
PYTHONPATH (vem antes do python/ instalado pelo uv); sonda que confirma que o módulo importado é a cópia; executor da
Task 1 (python/executor_testes.py, que encerra a árvore do processo no tempo-limite). Uma mutação está "detectada"
quando algum dos testes do inc. 7 (TC-ACK/TC-FXI em test_formas_v43.py, TC-SKP em test_skidpad.py, TC-NEU em
test_neutro.py) sai com código != 0 e com [FAIL] na saída. Os testes rodam do repositório (precisam de data/, só
leitura); os arquivos do repositório não mudam.
Roda como script: uv run python -X utf8 tests/mutation_inc7.py
"""
import os, re, shutil, sys, tempfile, time

from executor_testes import executar

TIMEOUT_SONDA = 120      # s
TIMEOUT_TESTE = 1800     # s por teste

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TESTES = [os.path.join('tests', t) for t in ('test_formas_v43.py', 'test_skidpad.py', 'test_neutro.py')]
RE_RESUMO = re.compile(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$')


def ler(modulo):
    return open(os.path.join(ROOT, 'python', modulo + '.py'), encoding='utf-8').read()


def preparar(modulo, fonte):
    """Cria a pasta temporária com a cópia do módulo e devolve (pasta, env), depois de conferir a origem."""
    d = tempfile.mkdtemp(prefix='dds_mut_inc7_')
    with open(os.path.join(d, modulo + '.py'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(fonte)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=d + os.pathsep + os.environ.get('PYTHONPATH', ''))
    sonda = executar([sys.executable, '-X', 'utf8', '-c', f'import {modulo}; print({modulo}.__file__)'],
                     cwd=ROOT, env=env, timeout_s=TIMEOUT_SONDA)
    origens = sonda.stdout.split()
    alvo = os.path.normcase(os.path.abspath(os.path.join(d, modulo + '.py')))
    if sonda.returncode != 0 or len(origens) != 1 or os.path.normcase(os.path.abspath(origens[0])) != alvo:
        shutil.rmtree(d, ignore_errors=True)
        print(f'ERRO: o {modulo} importado não é a cópia temporária ->', origens or sonda.stderr[-500:]); sys.exit(2)
    return d, env


def rodar_teste(env, t):
    return executar([sys.executable, '-X', 'utf8', t], cwd=ROOT, env=env, timeout_s=TIMEOUT_TESTE)


def pegou(o):
    return o.returncode != 0 and '[FAIL]' in o.stdout


def rodar(modulo, fonte):
    """Roda os testes em ordem com a cópia `fonte` de `modulo`; devolve [(teste, saída)]. Para após o primeiro que pegar."""
    d, env = preparar(modulo, fonte)
    try:
        res = []
        for t in TESTES:
            o = rodar_teste(env, t)
            res.append((t, o))
            if pegou(o):
                break
        return res
    finally:
        shutil.rmtree(d, ignore_errors=True)


# nome -> (módulo, trecho original, trecho mutado); cada trecho aparece uma única vez no módulo
muts = {
    "deriva_ackermann v43: sinal do termo (θ_i − θ̄_F)":
        ('equilibrio', "saida[c] += th[c] - th_med", "saida[c] += th_med - th[c]"),
    "fx_exigido_traseira v43: α_F e α_R trocados":
        ('equilibrio', "fx += req_f * alfas[0] + req_r * alfas[1]", "fx += req_f * alfas[1] + req_r * alfas[0]"),
    "alfas_de_arrasto: sem o limite no pico (réplica de grade)":
        ('equilibrio',
         "    if req >= fys[i_pico]:\n        return abs(alfas[i_pico])\n    j = next(",
         "    j = next("),
    "raio_linha_central: (d_int + d_ext)/2 no lugar de /4":
        ('skidpad', "return (d_int + d_ext) / 4.0", "return (d_int + d_ext) / 2.0"),
    "estudo_neutro: soma_erros sem o e_R":
        ('estudo_neutro', "soma_erros = max(est_f + est_r, TOL_DIF_G)", "soma_erros = max(est_f, TOL_DIF_G)"),
}

t0 = time.time()
fontes = {m: ler(m) for m, _, _ in muts.values()}
for nome, (m, a, b) in muts.items():
    assert fontes[m].count(a) == 1, nome

# pré-checagem: os três testes passam no original (sem cópia mutada no PYTHONPATH)
env0 = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
outs = [(t, rodar_teste(env0, t)) for t in TESTES]
for t, out in outs:
    resumo = (out.stdout.strip().splitlines() or [''])[-1]
    m = RE_RESUMO.match(resumo)
    if out.returncode != 0 or not m or m.group(1) != m.group(2) or int(m.group(1)) == 0:
        print('PRE-CHECAGEM FALHOU: original ->', t, resumo, '| código', out.returncode); print(out.stderr[-2000:]); sys.exit(2)
print('PRE-CHECAGEM OK: original ->', ' | '.join(
    f"{os.path.basename(t)}: {(o.stdout.strip().splitlines() or [''])[-1]}" for t, o in outs), flush=True)

det = 0
for nome, (m, a, b) in muts.items():
    ti = time.time()
    res = rodar(m, fontes[m].replace(a, b, 1))
    pegos = [t for t, o in res if pegou(o)]
    ok = bool(pegos)
    det += ok
    falhas = [l.split('  ')[0] for t, o in res if pegou(o) for l in o.stdout.splitlines() if l.startswith('[FAIL]')]
    print(('DETECTADO     ' if ok else 'NÃO DETECTADO '), nome, '->',
          '; '.join(falhas) if falhas else 'nenhum FAIL',
          f"[{', '.join(os.path.basename(t) for t in pegos) or '-'}; {time.time() - ti:.0f} s]", flush=True)
print(f"{det}/{len(muts)} mutantes mortos" if det == len(muts) else f"{det}/{len(muts)} mutantes mortos (SOBREVIVENTES)")
print(det, '/', len(muts))  # linha de resumo no formato que tools/rodar_testes.py (RE_MUTACAO) lê
print(f"tempo total: {time.time() - t0:.0f} s")
sys.exit(0 if det == len(muts) else 1)
