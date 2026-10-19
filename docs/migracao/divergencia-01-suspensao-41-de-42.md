# Divergência 01: suspensão roda 41 testes, o esperado é 42

- Data: 2026-10-18
- Etapa: passo 5 da fase A (originais rodados antes da portabilidade, commit `16cd4f0`)
- Situação: **RESOLVIDA pela opção A**, aprovada pelo usuário em 2026-10-18. O
  arquivo foi copiado byte a byte num commit de cópia próprio, e o SPEC §4.1 foi emendado.
  A confirmação do 42/42 está no log da reprodução (`verificacao-V2.4-local.md`).
- Log completo: [verificacao-V2.4-antes-portabilidade.md](verificacao-V2.4-antes-portabilidade.md)

## O que divergiu

`test_suspension_model_V2_1.py` terminou com `41 PASS, 0 FAIL, de 41 testes`
(código 0). O esperado é 42 (HANDOFF §6.2, linha 178: "V2_1 | 42/42").

## Causa (verificada)

O script tem 42 chamadas `check(...)`. Uma delas, a `TC-SUS-V2-004` (linha 240),
só roda se `suspension_model_V1_0.py` estiver na mesma pasta. Sem ele, o script
imprime (linha 242):

    [SKIP] TC-SUS-V2-004: suspension_model_V1_0.py não encontrado ao lado

O teste compara o Fz combinado da V2.1 com o da V1.0 (regressão, `dev == 0.0`).
O `suspension_model_V1_0.py` existe na importação
(`importado-claude-ai/saidas-conversas/kin/` e `conhecimento/`, os dois com
SHA-256 `14635ac0…6fee7508`), mas não está no inventário do SPEC §4.1, que deixa
as versões anteriores só em `importado-claude-ai/` (SPEC §4.1, última linha).

Conclusão: a diferença vem do inventário de cópia, não do código nem da fonte
do número. Nenhuma equação foi tocada e nenhum teste falhou.

Os outros scripts não têm `SKIP` nem dependências desse tipo (busca por "skip"
em `python/test_*.py`).

## Opções (decisão do usuário; nada foi aplicado)

| Opção | O que muda | Efeito |
|---|---|---|
| A (recomendada) | Emendar o SPEC §4.1: copiar `kin/suspension_model_V1_0.py` para `python/`, byte a byte, num commit de cópia próprio, com o `MANIFEST.sha256` e o inventário de `tools/verificar_manifest.py` atualizados | O teste roda como no sandbox; o esperado 42 continua valendo. Abre exceção à regra "versões anteriores só em importado-claude-ai/" para um arquivo que é dependência de teste |
| B | Manter o inventário e registrar 41 + 1 SKIP como resultado da fase A | O CA-05 da suspensão fica como divergência registrada, sem reproduzir o 42/42 |

A opção A não ajusta resultado: restaura uma dependência que o próprio teste
procura. Mesmo assim, ela muda o SPEC aprovado, então precisa do "sim" do usuário.

## Observação da mutação (sem relação com a divergência)

No "antes", a mutação original deu 23/23 com código 0, mas sem pré-checagem do
original, então o CA-06 conta como FAIL. Mecanismo do falso positivo previsto no
P6, verificado: chamado sem o modo UTF-8, o `python3`
(`WindowsApps\python3.EXE`) quebra com `UnicodeEncodeError` ao imprimir "κ"
(`test_tire_model_V2_4.py:36`) e sai com código 1 em qualquer mutante. Na
execução pela `tools/rodar_testes.py`, o `PYTHONUTF8=1` herdado evita esse
erro, então o 23/23 do "antes" pode ser genuíno. Sem a pré-checagem, porém, não
dá para provar.
