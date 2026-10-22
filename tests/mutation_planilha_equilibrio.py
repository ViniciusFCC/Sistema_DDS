"""Mutação da planilha do equilíbrio (V4.1, inc. 4, Task 8; plano, "Contagem de testes", item Mutação): cinco erros
plantados no GERADOR (python/aba_equilibrio.py), que os testes da planilha (TC-WB41-004 a 006, em
tests/test_workbook_v4_1.py) têm de pegar:
  a) a e b trocados na força lateral exigida de cada eixo (req_F usa {b}, req_R usa {a});
  b) sem cos δ_ref na soma de Fy da dianteira (o cos δ só aparece com R e h3/h2/h8/h9 ligadas: casos C4, C4b, RF1);
  c) Ackermann invertido (o sinal do Δα da roda dianteira com h2; só o C4b tem % Ackermann ≠ 0, mas o sinal já
     aparece no C4, onde δ_ref ≠ δ da roda);
  d) sinal do ganho de camber em rolagem (∂γ/∂φ de cada roda; o ganho é ≠ 0 em todos os casos);
  e) pior origem trocada pela melhor (MAX vira MIN na fórmula do INDEX; casos ORG_TX / ORG_T09 e o prefixo D16).

Padrão de tests/mutation_equilibrio.py: pré-checagem do original; "detectado" = o teste sai com código != 0 e alguma
linha [FAIL] de TC-WB41-004, 005 ou 006 (o TC-WB41-003 não conta: ele não exercita a lógica mutada). A cópia mutada do
gerador fica numa pasta temporária posta no PYTHONPATH, antes do python/ instalado pelo uv; o teste roda do repositório
(precisa de data/, só leitura) e gera todas as planilhas em pastas temporárias dele. A sonda confirma que o
aba_equilibrio importado é a cópia. O arquivo do repositório não muda. Cada mutante roda o test_workbook_v4_1.py inteiro
(~11 recálculos de cópias): leva minutos por mutante. DDS_RECALC=excel|libreoffice vale como no teste.
Roda como script: uv run python -X utf8 tests/mutation_planilha_equilibrio.py
Código de saída: 0 = todos detectados; 1 = algum mutante escapou; 2 = pré-checagem falhou; 3 = sem motor de recálculo.
"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TESTE = os.path.join('tests', 'test_workbook_v4_1.py')
src = open(os.path.join(ROOT, 'python', 'aba_equilibrio.py'), encoding='utf-8').read()
RE_RESUMO = re.compile(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$')
RE_FAIL_004_006 = re.compile(r'^\[FAIL\] (TC-WB41-00[456][^ ]*)')
RAIZ_ORIG = "RAIZ = Path(__file__).resolve().parent.parent"
TIMEOUT = 1500   # uma rodada com 5 casos leva ~5 min; mais que isso é o Excel travado: mata e repete uma vez
# Menor conjunto de casos que torna os cinco mutantes observáveis (DDS_CASOS; o TC-WB41-003 e os demais casos não rodam):
# C1 (a ≠ b: nos casos simétricos a troca a↔b é invisível), C3 (ganho de camber), C4b (R, cos δ, Ackermann com % > 0), ORG_TX e ORG_T09 (pior origem, prefixo D16)
CASOS = 'C1,C3,C4b,ORG_TX,ORG_T09'


def rodar(fonte):
    """Roda o teste da planilha com a cópia `fonte` de aba_equilibrio.py na frente do caminho de import."""
    assert fonte.count(RAIZ_ORIG) == 1
    # a cópia fica fora de python/: RAIZ tem de continuar apontando o repositório (data/, excel/, tag v4.0)
    fonte = fonte.replace(RAIZ_ORIG, f"RAIZ = Path({ROOT!r})")
    d = tempfile.mkdtemp(prefix='dds_mut_pl_')
    try:
        with open(os.path.join(d, 'aba_equilibrio.py'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(fonte)
        env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', DDS_RECALC='excel', DDS_CASOS=CASOS,
                   PYTHONPATH=d + os.pathsep + os.environ.get('PYTHONPATH', ''))
        sonda = subprocess.run([sys.executable, '-X', 'utf8', '-c', 'import aba_equilibrio; print(aba_equilibrio.__file__)'],
                               cwd=ROOT, env=env, capture_output=True, text=True)
        alvo = os.path.normcase(os.path.abspath(os.path.join(d, 'aba_equilibrio.py')))
        if sonda.returncode != 0 or os.path.normcase(os.path.abspath(sonda.stdout.strip())) != alvo:
            print('ERRO: o aba_equilibrio importado não é a cópia temporária ->', sonda.stdout.strip() or sonda.stderr[-500:])
            sys.exit(2)
        for tentativa in (1, 2):
            try:
                return subprocess.run([sys.executable, '-X', 'utf8', TESTE], cwd=ROOT, env=env, capture_output=True,
                                      text=True, encoding='utf-8', errors='replace', timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                print('  (tempo esgotado na tentativa', tentativa, ')', flush=True)
        print('ERRO: o teste travou duas vezes'); sys.exit(2)
    finally:
        shutil.rmtree(d, ignore_errors=True)


muts = {
    "força exigida com a e b trocados":
        ('braco = "{b}" if e == "F" else "{a}"', 'braco = "{a}" if e == "F" else "{b}"'),
    "sem cos δ na dianteira":
        ('''IF({{raio}}=1,COS({{L}}/{{R}}),1),"N/A")''', '''IF({{raio}}=1,1,1),"N/A")'''),
    "Ackermann com sinal invertido":
        ("{s}{{toe_{c}}}+(-({d}-{{dref}}))", "{s}{{toe_{c}}}+({d}-{{dref}})"),
    "ganho de camber com sinal invertido":
        ("IF({{dir}}=1,-{{g{troca[c]}}},{{g{c}}})", "IF({{dir}}=1,{{g{troca[c]}}},-{{g{c}}})"),
    "pior origem trocada pela melhor (MAX -> MIN)":
        ('return f"INDEX({NOME_LISTA},MAX({\',\'.join(partes)}))"', 'return f"INDEX({NOME_LISTA},MIN({\',\'.join(partes)}))"'),
}


def resumo(out):
    return (out.stdout.strip().splitlines() or [''])[-1]


for nome, (a, b) in muts.items():
    assert src.count(a) == 1, (nome, src.count(a))   # cada mutação mira exatamente um ponto do gerador

out = rodar(src)
if out.stdout.startswith('NÃO EXECUTÁVEL'):
    print(out.stdout.strip().splitlines()[0]); sys.exit(3)
m = RE_RESUMO.match(resumo(out))
if out.returncode != 0 or not m or m.group(1) != m.group(2) or int(m.group(1)) == 0:
    print('PRE-CHECAGEM FALHOU: original ->', resumo(out), '| código', out.returncode); print(out.stdout[-3000:], out.stderr[-2000:])
    sys.exit(2)
print('PRE-CHECAGEM OK: original ->', resumo(out), '|', next((l for l in out.stdout.splitlines() if l.startswith('MOTOR:')), 'MOTOR: ?'))
det = 0
for nome, (a, b) in muts.items():
    out = rodar(src.replace(a, b, 1))
    falhas = [mm.group(1) for mm in (RE_FAIL_004_006.match(l) for l in out.stdout.splitlines()) if mm]
    ok = out.returncode != 0 and bool(falhas)
    det += ok
    extra = '' if ok or out.returncode == 0 else f' (código {out.returncode}, sem [FAIL] de 004-006: {resumo(out)}; {out.stderr[-300:].strip()})'
    print(('DETECTADO     ' if ok else 'NÃO DETECTADO '), nome, '->', '; '.join(falhas) if falhas else 'nenhum FAIL de 004-006', extra)
print(det, '/', len(muts))
sys.exit(0 if det == len(muts) else 1)
