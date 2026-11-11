# Reverificação do pneu com pressão depois do ajuste do conselho (EDR-071, PR #41)

- Data: 2026-11-11.
- Commit verificado: 3b643b8 (`fix: extremos com banda só de limite inferior ficam não resolvidos, não excluídos (EDR-071)`); o commit seguinte (5110981) só muda documentação (EDR, spec, CLAUDE.md).
- Comandos (com `UV_SYSTEM_CERTS=1`; `.tir` do TTC copiados para `data/` só durante a execução, sem versionar):
  - `uv run python -X utf8 tests/test_tire_pressure.py`
  - `uv run python -X utf8 tests/test_tire_static.py`
  - `uv run python -X utf8 tools/relatorio_pressao.py --sobrescrever` (Excel, 123,3 s, saída em `build/`)

## Resultados
- `tests/test_tire_pressure.py`: `110 PASS, 0 FAIL, de 110 testes` (check novo TC-TIRE-022m; 022a, 022d e 022f ajustados para usar bandas hipotéticas medidas ou 14 psi medida, para que o desfecho "melhor" continue exercitado).
- `tests/test_tire_static.py`: `87 PASS, 0 FAIL, de 87 testes`.
- Relatório, Cα na Fz estática:
  - eixo F: indistinguíveis: 10, 12 psi; 8, 14 psi não resolvidos: banda só limite inferior (a diferença não prova que sejam piores).
  - eixo R: o mesmo desfecho.
  - Antes do ajuste, 8 e 14 psi saíam "fora do conjunto com banda não medida (limite inferior)".

## Escopo da verificação
A suíte inteira (`tools/rodar_testes.py`) não foi repetida, por decisão do usuário (2026-11-11): nenhum outro item importa os módulos tocados. Conferido com `grep -rln "comparacao_pressao\|tire_pressure\|tire_model_static" python tests tools`: só os próprios módulos, `tests/test_tire_pressure.py`, `tests/test_tire_static.py`, `tools/relatorio_pressao.py` e a tabela de `tools/rodar_testes.py` (que só guarda o N esperado, agora 110).
