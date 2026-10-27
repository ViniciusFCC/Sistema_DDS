"""Mutação do equilíbrio (V4.0, inc. 2; spec §9, item 8): seis mutações em python/equilibrio.py.

Padrão de tests/mutation_tire.py: pré-checagem do original; "detectado" = algum dos dois testes
(test_equilibrio.py ou test_equilibrio_linear.py) sai com código != 0 e com [FAIL] na saída.
A cópia mutada fica numa pasta temporária posta no PYTHONPATH, que vem antes do python/ instalado
pelo uv (.pth do site-packages); os testes rodam do repositório (precisam de data/ e excel/, só
leitura). A sonda confirma que o equilibrio importado é a cópia. O arquivo do repositório não muda.
Roda como script: uv run python -X utf8 tests/mutation_equilibrio.py
"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TESTES = [os.path.join('tests', 'test_equilibrio.py'), os.path.join('tests', 'test_equilibrio_linear.py')]
src = open(os.path.join(ROOT, 'python', 'equilibrio.py'), encoding='utf-8').read()
RE_RESUMO = re.compile(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$')


def rodar(fonte):
    """Roda os dois testes com a cópia `fonte` de equilibrio.py na frente do caminho de import."""
    d = tempfile.mkdtemp(prefix='dds_mut_eq_')
    try:
        with open(os.path.join(d, 'equilibrio.py'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(fonte)
        env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
                   PYTHONPATH=d + os.pathsep + os.environ.get('PYTHONPATH', ''))
        sonda = subprocess.run([sys.executable, '-X', 'utf8', '-c',
                                'import equilibrio, equilibrio_linear; print(equilibrio.__file__); '
                                'print(equilibrio_linear._eq.__file__)'],
                               cwd=ROOT, env=env, capture_output=True, text=True)
        origens = sonda.stdout.split()
        alvo = os.path.normcase(os.path.abspath(os.path.join(d, 'equilibrio.py')))
        if sonda.returncode != 0 or len(origens) != 2 or any(os.path.normcase(os.path.abspath(o)) != alvo for o in origens):
            print('ERRO: o equilibrio importado não é a cópia temporária ->', origens or sonda.stderr[-500:]); sys.exit(2)
        return [subprocess.run([sys.executable, '-X', 'utf8', t], cwd=ROOT, env=env, capture_output=True,
                               text=True, encoding='utf-8', errors='replace') for t in TESTES]
    finally:
        shutil.rmtree(d, ignore_errors=True)


muts = {
    "forca_exigida com a e b trocados":
        ("return (m_ay * cfg.cg_to_rear / cfg.wheelbase, m_ay * cfg.cg_to_front / cfg.wheelbase)",
         "return (m_ay * cfg.cg_to_front / cfg.wheelbase, m_ay * cfg.cg_to_rear / cfg.wheelbase)"),
    "sem cos δ na dianteira":
        ("    return math.cos(caso.cfg.wheelbase / caso.raio_m)", "    return 1.0"),
    "Ackermann com sinal invertido":
        ("        saida[c] = -(d - d_ref)", "        saida[c] = (d - d_ref)"),
    "ganho de camber com sinal invertido":
        ("caso.camber_estatico_rad[c] + caso.ganho_camber[c] * phi",
         "caso.camber_estatico_rad[c] - caso.ganho_camber[c] * phi"),
    "NEUTRO pelo passo de exibição (regra anterior ao EDR-056)":
        ("        if abs(delta) <= res:", "        if abs(delta) < passo_ms2:"),
    "texto_veredito sem o prefixo DEMONSTRATIVO":
        ('return texto if pior_origem == origem_do_carro else "DEMONSTRATIVO · " + texto\n',
         'return texto\n'),
}

outs = rodar(src)
for t, out in zip(TESTES, outs):
    resumo = (out.stdout.strip().splitlines() or [''])[-1]
    m = RE_RESUMO.match(resumo)
    if out.returncode != 0 or not m or m.group(1) != m.group(2) or int(m.group(1)) == 0:
        print('PRE-CHECAGEM FALHOU: original ->', t, resumo, '| código', out.returncode); print(out.stderr[-2000:]); sys.exit(2)
print('PRE-CHECAGEM OK: original ->', ' | '.join(
    f"{os.path.basename(t)}: {(o.stdout.strip().splitlines() or [''])[-1]}" for t, o in zip(TESTES, outs)))
det = 0
for name, (a, b) in muts.items():
    # a mutação 6 mira o texto_veredito de equilibrio.py (o texto_k de equilibrio_linear.py fica intacto)
    assert src.count(a) == 1, name
    outs = rodar(src.replace(a, b, 1))
    pegos = [t for t, o in zip(TESTES, outs) if o.returncode != 0 and '[FAIL]' in o.stdout]
    ok = bool(pegos)
    det += ok
    falhas = [l.split('  ')[0] for o in outs for l in o.stdout.splitlines() if l.startswith('[FAIL]')]
    print(('DETECTADO     ' if ok else 'NÃO DETECTADO '), name, '->', '; '.join(falhas) if falhas else 'nenhum FAIL')
print(det, '/', len(muts))
