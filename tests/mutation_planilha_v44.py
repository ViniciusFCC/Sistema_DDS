"""Mutação da planilha V4.4 (incremento 8, parte 8b, Task 17): quatro erros plantados numa CÓPIA da V4.4 de excel/ (openpyxl, em
pasta temporária; excel/ nunca é gravada), que a equivalência por valor V4.3 x V4.4 (TC-WB44-005, tests/test_workbook_v4_4.py)
tem de pegar. O arquivo mutado vai ao teste pela variável DDS_V44 e os casos, por DDS_CASOS44:
  1) 09_LOADS!B4: `ent_05_wheelbase_l` -> `ent_05_front_track_t_f` (nome trocado por outro do mesmo papel);
  2) 09_LOADS!B5: `ent_05_wheelbase_l` -> `'05_VEHICLE'!$B$7` (nome trocado pelo endereço da célula vizinha, a bitola dianteira);
  3) 09_LOADS!B21: `<=0` -> `>=0` (operador no ramo de instabilidade de rolagem, pouco usado);
  4) 09_LOADS!B4: `9.81` -> `9.8` (constante).
Cada mutante confere antes que o trecho aparece exatamente uma vez na fórmula (senão, código 2: a lista está desatualizada).
Padrão de tests/mutation_planilha_v43.py: pré-checagem do original (o teste com a V4.4 intacta tem de sair com código 0 e
`N PASS, 0 FAIL, de N testes`); "detectado" = o teste termina dentro do tempo, sai com código != 0 e tem [FAIL] de TC-WB44-005.
Os casos são NOMINAL, P01, P02 e P03 (DDS_CASOS44). Com DDS_CASOS44 definido o TC-WB44-006 (cobertura) sai PULADO, sem
contar como PASS nem FAIL: a cobertura só fecha com o conjunto completo e vem do lado V4.3, que o mutante não toca. O motor é
o Excel (DDS_RECALC=excel).
Roda como script: uv run python -X utf8 tests/mutation_planilha_v44.py
Código de saída: 0 = todos detectados; 1 = algum mutante escapou; 2 = pré-checagem falhou ou lista desatualizada; 3 = sem motor.
Tempo (EDR-068): orçamento DDS_ORCAMENTO_S (padrão 10000 s); cada rodada tem min(TIMEOUT, restante). Cada caso leva ~65 s
(duas cópias recalculadas no Excel); medido em 2026-11-10: ~185 s por rodada, 5 rodadas ≈ 16 min. TIMEOUT = 1800 s por rodada.
"""
import os, re, shutil, sys, tempfile

import openpyxl

from executor_testes import CODIGO_TEMPO, Execucao, executar, orcamento_do_ambiente

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TESTE = os.path.join('tests', 'test_workbook_v4_4.py')
V44 = os.path.join(ROOT, 'excel', 'FSAE_EV_Suspension_Fase1_V4_4.xlsx')
RE_RESUMO = re.compile(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$')
RE_FAIL = re.compile(r'^\[FAIL\] (TC-WB44-005[^ ]*)')
TIMEOUT = 1800
ORCAMENTO = orcamento_do_ambiente(10000)
CASOS = 'NOMINAL,P01,P02,P03'

# nome -> (aba, célula, trecho exato da fórmula da V4.4, trecho mutado)
muts = {
    "nome trocado por outro do mesmo papel (B4: L -> t_F)":
        ('09_LOADS', 'B4', 'ent_05_wheelbase_l', 'ent_05_front_track_t_f'),
    "nome trocado pelo endereço da vizinha (B5: L -> '05_VEHICLE'!$B$7)":
        ('09_LOADS', 'B5', 'ent_05_wheelbase_l', "'05_VEHICLE'!$B$7"),
    "operador no ramo de instabilidade de rolagem (B21: <=0 -> >=0)":
        ('09_LOADS', 'B21', '<=0', '>=0'),
    "constante (B4: 9.81 -> 9.8)":
        ('09_LOADS', 'B4', '9.81', '9.8'),
}


def tempo_esgotado():
    return Execucao(CODIGO_TEMPO, '', '', 0.0, True)


def rodar(arquivo=None, orcamento=None):
    """Roda o teste com a V4.4 de `arquivo` (None = a de excel/, intacta). Devolve Execucao."""
    orcamento = orcamento or ORCAMENTO
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', DDS_RECALC='excel', DDS_CASOS44=CASOS)
    if arquivo:
        env['DDS_V44'] = arquivo
    else:
        env.pop('DDS_V44', None)
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


def falhas_005(out):
    return [mm.group(1) for mm in (RE_FAIL.match(l) for l in out.stdout.splitlines()) if mm]


def detectado(out, falhas=None):
    """Detectado = o teste terminou (sem estourar o tempo), saiu com código != 0 e tem [FAIL] de TC-WB44-005."""
    if falhas is None:
        falhas = falhas_005(out)
    return (not out.estourou) and out.returncode != 0 and bool(falhas)


def formula(aba, cel):
    wb = openpyxl.load_workbook(V44)
    try:
        return wb[aba][cel].value
    finally:
        wb.close()


def mutar(aba, cel, a, b, destino):
    """Grava em `destino` uma cópia da V4.4 com `a` -> `b` na fórmula de aba!cel (uma ocorrência exata). Nunca grava em excel/."""
    wb = openpyxl.load_workbook(V44)
    try:
        f = wb[aba][cel].value
        if not isinstance(f, str) or f.count(a) != 1:
            print(f'ERRO: {aba}!{cel}: lista de mutantes desatualizada ({a!r})'); sys.exit(2)
        wb[aba][cel].value = f.replace(a, b, 1)
        wb.save(destino)
    finally:
        wb.close()


def resumo(out):
    return (out.stdout.strip().splitlines() or [''])[-1]


def main():
    for nome, (aba, cel, a, b) in muts.items():   # a lista confere antes de gastar tempo no Excel
        f = formula(aba, cel)
        if not isinstance(f, str) or f.count(a) != 1:
            print('ERRO: lista de mutantes desatualizada ->', nome); sys.exit(2)

    out = rodar()
    if out.estourou:
        print('PRE-CHECAGEM FALHOU: tempo esgotado (orçamento de', ORCAMENTO.total_s, 's)'); sys.exit(2)
    if out.stdout.startswith('NÃO EXECUTÁVEL'):
        print(out.stdout.strip().splitlines()[0]); sys.exit(3)
    m = RE_RESUMO.match(resumo(out))
    if out.returncode != 0 or not m or m.group(1) != m.group(2) or int(m.group(1)) == 0:
        print('PRE-CHECAGEM FALHOU: original ->', resumo(out), '| código', out.returncode); print(out.stdout[-3000:], out.stderr[-2000:])
        sys.exit(2)
    print('PRE-CHECAGEM OK: original ->', resumo(out), '|', next((l for l in out.stdout.splitlines() if l.startswith('MOTOR:')), 'MOTOR: ?'), flush=True)
    det = 0
    for nome, (aba, cel, a, b) in muts.items():
        d = tempfile.mkdtemp(prefix='dds_mut_v44_')
        try:
            arq = os.path.join(d, 'V4_4_mutada.xlsx')
            mutar(aba, cel, a, b, arq)
            out = rodar(arq)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        falhas = falhas_005(out)
        ok = detectado(out, falhas)
        det += ok
        if out.estourou:
            print('NÃO DETECTADO (tempo)', nome, '->', 'tempo esgotado, o mutante não foi avaliado', flush=True)
            continue
        extra = '' if ok or out.returncode == 0 else f' (código {out.returncode}, sem [FAIL] de TC-WB44-005: {resumo(out)}; {out.stderr[-300:].strip()})'
        print(('DETECTADO     ' if ok else 'NÃO DETECTADO '), nome, '->', '; '.join(falhas) if falhas else 'nenhum FAIL de TC-WB44-005', extra, flush=True)
    print(det, '/', len(muts))
    sys.exit(0 if det == len(muts) else 1)


if __name__ == '__main__':
    main()
