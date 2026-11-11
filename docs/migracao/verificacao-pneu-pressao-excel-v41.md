# Pneu com pressão (EDR-071), suíte única no Excel: complemento do test_workbook_v4_1

- Commit: 0b421df (árvore sem mudanças pendentes; o único arquivo fora do Git era o `.tir` do TTC em `data/`, ignorado).
- Data: 2026-11-11, início 17:06:17, fim 17:36:35. Motor: Excel (Excel 16.0 via COM, PID 52852).
- Por que este log existe: na suíte única no Excel (`verificacao-pneu-pressao-excel.md`, mesmo commit, 2026-11-11 de 11:42 a 17:05)
  todos os itens deram PASS, menos o CA-09 `tests/test_workbook_v4_1.py`, que estourou o tempo-limite padrão de 1800 s (TIMEOUT
  depois de 1800,6 s, de 15:00:35 a 15:30:36; "MOTOR: (não informado)": o Excel não respondeu antes de qualquer conferência, então
  nenhuma conferência falhou). Nenhuma dependência desse item mudou na branch: `git diff --name-only 3cc91f0 0b421df` não toca o script,
  seus imports locais, `excel/*V4_1*` nem `data/nomes_V4_1.csv`. Na suíte única do incremento 8 esse mesmo item passou em 885,3 s. Por
  isso só ele foi refeito (decisão do usuário em 2026-11-11, em vez de repetir a suíte inteira), como no complemento do incremento 8
  (`verificacao-inc8-excel-v43.md`).
- Como rodou: direto, por `uv run python -X utf8 tests/test_workbook_v4_1.py`, sob `timeout 2400`, sozinho na máquina. Não passou pela
  função `rodar()` do executor (`tools/rodar_testes.py`), então não há linha `[executor]` com o tempo; o tempo abaixo vem do relógio do
  comando.

| CA | Item | Script | Esperado | Obtido | Código | Tempo | Resultado |
|---|---|---|---|---|---|---|---|
| CA-09 | planilha Excel x Python (test_workbook_v4_1) | `tests/test_workbook_v4_1.py` | 5 | 5 PASS, 0 FAIL, de 5 testes | 0 | ~1818 s (17:06:17 a 17:36:35) | **PASS** |

Tempo: cerca de 1818 s, contra 885,3 s na suíte única do incremento 8 e mais de 1800 s na suíte de 0b421df, sem mudança de código no
teste nem na V4.1: o tempo desse item varia muito entre rodadas e o limite padrão de 1800 s não tinha margem.

Do stdout de `tests/test_workbook_v4_1.py` ficam abaixo só a linha MOTOR e a linha de resumo; foram omitidas as demais linhas (11409 bytes
no total: tempos de recálculo por caso, contagens de células com fórmula, vereditos por caso e as linhas `[PASS] TC-WB41-003`, `004`,
`005`, `006 (parte 1)` e `006 (parte 2)`).

```text
MOTOR: excel (Excel 16.0 via COM, PID 52852)
...
--- Resumo ---
5 PASS, 0 FAIL, de 5 testes
```
