"""Mutação da planilha V4.3 (incremento 7, parte 7b, Task 13): quatro erros plantados nos GERADORES (python/aba_curva.py e
python/aba_equilibrio.py), que o TC-WB43-004 (tests/test_workbook_v4_3.py) tem de pegar:
  a) sinal de θ no Δα do Ackermann (C-C1: `+IF(h2v=1, θ_i − θ̄_F, 0)` vira `θ̄_F − θ_i`; B114 e B115);
  b) aF ↔ aR no Fx por arrasto induzido (C-G5: `req_F·aF + req_R·aR` vira `req_F·aR + req_R·aF`);
  c) sem o limite no pico no α do arrasto (C-G4 e C-G4b: o ramo `req >= cap` vira falso);
  d) modo do R trocado (C-A14: "Linha central" e "Rente aos cones" trocados no R usado).
Padrão de tests/mutation_planilha_equilibrio.py: pré-checagem do original; "detectado" = o teste sai com código != 0 e alguma
linha [FAIL] de TC-WB43-003 ou 004 (o 005 só confere a barra de fórmulas). A cópia mutada do gerador fica numa pasta
temporária posta no PYTHONPATH antes do python/ instalado; o teste roda do repositório (data/ e a tag v4.2 são só leitura) e
gera as planilhas em pastas temporárias dele. A sonda confirma que o módulo importado é a cópia. Cada rodada roda o
test_workbook_v4_3.py só com os casos de CASOS (variável DDS_CASOS: M_MAN_D, M_LC_E, M_RC_D, LOOSE_PICO e FX_ASSIM; o 003 e o 005 não
rodam): M_MAN_D (Ackermann e Fx com h2v = h9v = 1, aba 20 e B48), M_LC_E e M_RC_D (modos do R, nos dois sentidos) e LOOSE_PICO
(força traseira acima do pico) e FX_ASSIM (veículo com a != b: nos casos simétricos req_F = req_R e a troca aF <-> aR no Fx é
invisível). O motor é o Excel (DDS_RECALC=excel).
Roda como script: uv run python -X utf8 tests/mutation_planilha_v43.py
Código de saída: 0 = todos detectados; 1 = algum mutante escapou; 2 = pré-checagem falhou; 3 = sem motor de recálculo.
Tempo (EDR-068): orçamento do script DDS_ORCAMENTO_S (padrão 10000 s); cada rodada tem min(TIMEOUT, restante). Base do TIMEOUT: a
Task 8 mediu o recálculo da V4.3 em ~1,3 a 1,5 vezes o da V4.2 (abrir ~14 s, total ~16 s por cópia) e o teste leva ~100 s por caso
(recálculo ~23 s e o Python da comparação); 4 casos ≈ 7 min medidos; a mutação da V4.1 usou 1500 s por rodada para 5 casos de ~60
s. TIMEOUT = 1800 s (folga de 4x sobre o medido), 5 rodadas cabem em 9000 s < 10000 s.
"""
import os, re, shutil, sys, tempfile

from executor_testes import CODIGO_TEMPO, Execucao, executar, orcamento_do_ambiente

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TESTE = os.path.join('tests', 'test_workbook_v4_3.py')
RE_RESUMO = re.compile(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$')
RE_FAIL = re.compile(r'^\[FAIL\] (TC-WB43-00[34][^ ]*)')
RAIZ_ORIG = "RAIZ = Path(__file__).resolve().parent.parent"
TIMEOUT = 1800
ORCAMENTO = orcamento_do_ambiente(10000)
CASOS = 'M_MAN_D,M_LC_E,M_RC_D,LOOSE_PICO,FX_ASSIM'
FONTES = {m: open(os.path.join(ROOT, 'python', m + '.py'), encoding='utf-8').read() for m in ('aba_curva', 'aba_equilibrio')}


def tempo_esgotado():
    return Execucao(CODIGO_TEMPO, '', '', 0.0, True)


def rodar(modulo, fonte, orcamento=None):
    """Roda o teste com a cópia `fonte` do módulo `modulo` na frente do caminho de import. Devolve Execucao."""
    orcamento = orcamento or ORCAMENTO
    if RAIZ_ORIG in fonte:    # a cópia fica fora de python/: RAIZ tem de continuar apontando o repositório
        fonte = fonte.replace(RAIZ_ORIG, f"RAIZ = Path({ROOT!r})")
    d = tempfile.mkdtemp(prefix='dds_mut_v43_')
    try:
        with open(os.path.join(d, modulo + '.py'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(fonte)
        env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', DDS_RECALC='excel', DDS_CASOS=CASOS,
                   PYTHONPATH=d + os.pathsep + os.environ.get('PYTHONPATH', ''))
        sonda = executar([sys.executable, '-X', 'utf8', '-c', f'import {modulo}; print({modulo}.__file__)'],
                         cwd=ROOT, env=env, timeout_s=max(1.0, min(120, orcamento.restante())))
        alvo = os.path.normcase(os.path.abspath(os.path.join(d, modulo + '.py')))
        if sonda.estourou or sonda.returncode != 0 or os.path.normcase(os.path.abspath(sonda.stdout.strip())) != alvo:
            print(f'ERRO: o {modulo} importado não é a cópia temporária ->', sonda.stdout.strip() or sonda.stderr[-500:])
            sys.exit(2)
        out = tempo_esgotado()
        for tentativa in (1, 2):
            if orcamento.restante() <= 0:
                break
            out = executar([sys.executable, '-X', 'utf8', TESTE], cwd=ROOT, env=env,
                           timeout_s=min(TIMEOUT, orcamento.restante()))
            print(f'  tempo por rodada: {out.tempo_s:.0f} s (tentativa {tentativa}, orçamento restante {orcamento.restante():.0f} s)', flush=True)
            if not out.estourou:
                return out
            print('  (tempo esgotado na tentativa', tentativa, ')', flush=True)
            if tentativa == 1 and not orcamento.cabe(TIMEOUT):
                break
        return out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def falhas_003_004(out):
    return [mm.group(1) for mm in (RE_FAIL.match(l) for l in out.stdout.splitlines()) if mm]


def detectado(out, falhas=None):
    """Detectado = o teste terminou (sem estourar o tempo), saiu com código != 0 e tem [FAIL] de 003 ou 004."""
    if falhas is None:
        falhas = falhas_003_004(out)
    return (not out.estourou) and out.returncode != 0 and bool(falhas)


# nome -> (módulo, trecho exato do gerador, trecho mutado)
muts = {
    "sinal de θ no Δα do Ackermann (C-C1)":
        ("aba_curva", 'f"+IF({{h2v}}=1,{{{th}}}-{{thm}},0)"', 'f"+IF({{h2v}}=1,{{thm}}-{{{th}}},0)"'),
    "aF e aR trocados no Fx por arrasto (C-G5)":
        ("aba_equilibrio", "{req_f}*{aF}+{req_r}*{aR}", "{req_f}*{aR}+{req_r}*{aF}"),
    "sem o limite no pico no α do arrasto (C-G4)":
        ("aba_equilibrio", 'IF({req}>={cap},ABS(INDEX({alfa_ref},{idx})),', 'IF(FALSE,0,'),
    "modo do R trocado (C-A14)":
        ("aba_curva", '{rlc},IF(EXACT({modo},"Rente aos cones"),{rrente},""',
         '{rrente},IF(EXACT({modo},"Rente aos cones"),{rlc},""'),
}


def resumo(out):
    return (out.stdout.strip().splitlines() or [''])[-1]


def main():
    for nome, (mod, a, b) in muts.items():
        assert FONTES[mod].count(a) == 1, (nome, FONTES[mod].count(a))   # cada mutação mira exatamente um ponto do gerador

    out = rodar('aba_equilibrio', FONTES['aba_equilibrio'])
    if out.estourou:
        print('PRE-CHECAGEM FALHOU: tempo esgotado (orçamento de', ORCAMENTO.total_s, 's)'); sys.exit(2)
    if out.stdout.startswith('NÃO EXECUTÁVEL'):
        print(out.stdout.strip().splitlines()[0]); sys.exit(3)
    m = RE_RESUMO.match(resumo(out))
    if out.returncode != 0 or not m or m.group(1) != m.group(2) or int(m.group(1)) == 0:
        print('PRE-CHECAGEM FALHOU: original ->', resumo(out), '| código', out.returncode); print(out.stdout[-3000:], out.stderr[-2000:])
        sys.exit(2)
    print('PRE-CHECAGEM OK: original ->', resumo(out), '|', next((l for l in out.stdout.splitlines() if l.startswith('MOTOR:')), 'MOTOR: ?'))
    det = 0
    for nome, (mod, a, b) in muts.items():
        out = rodar(mod, FONTES[mod].replace(a, b, 1))
        falhas = falhas_003_004(out)
        ok = detectado(out, falhas)
        det += ok
        if out.estourou:
            print('NÃO DETECTADO (tempo)', nome, '->', 'tempo esgotado, o mutante não foi avaliado')
            continue
        extra = '' if ok or out.returncode == 0 else f' (código {out.returncode}, sem [FAIL] de 003/004: {resumo(out)}; {out.stderr[-300:].strip()})'
        print(('DETECTADO     ' if ok else 'NÃO DETECTADO '), nome, '->', '; '.join(falhas) if falhas else 'nenhum FAIL de 003/004', extra)
    print(det, '/', len(muts))
    sys.exit(0 if det == len(muts) else 1)


if __name__ == '__main__':
    main()
