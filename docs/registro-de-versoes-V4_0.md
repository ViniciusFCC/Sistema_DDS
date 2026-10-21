# Registro de versões — Sistema_DDS — V4.0 (incrementos 1 a 3)

Data: 2026-10-21. A V4.0 cobre os incrementos 1 a 3 da especificação
`docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md`. Do incremento 4 em diante a versão
passa a V4.1, numa conversa nova (usuário, 2026-10-21). Decisões: EDR-055, EDR-056, EDR-057 e EDR-058.

## O que entrou

| Incremento | Plano | Entrou |
|---|---|---|
| 1. Viabilidade e robustez | `docs/superpowers/plans/2026-10-20-v4-0-inc1-viabilidade-robustez.md` | Análise de par do Milliken no Python (`python/equilibrio.py`), caso demonstrativo lido da planilha e pior origem (`python/caso_planilha.py`), varredura de robustez ao pneu (EDR-055) e regras do veredito no limite (EDR-056). Relatórios em `docs/v4-0/`. |
| 2. Equilíbrio linear e hipóteses do limite | `docs/superpowers/plans/2026-10-21-v4-0-inc2-equilibrio-linear-e-hipoteses.md` | Gradiente de subesterço K pelas parcelas do Gillespie cap. 6 (`python/equilibrio_linear.py`), com os exemplos resolvidos do livro como oráculos; hipóteses do limite no Python, desligadas por padrão (Ackermann, cos δ, CG lateral, aero com a velocidade, tração com elipse de atrito, diferencial aberto); testes do pneu em ISO_TYDEX; mutação do equilíbrio (EDR-057). |
| 3. Fundação da planilha | `docs/superpowers/plans/2026-10-21-v4-0-inc3-fundacao-nomes.md` | `excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx`, gerada da tag `v3.0` por `python/gerar_v4_0.py`, com 698 nomes definidos (ent 195, org 58, fte 58, res 387) de `data/nomes_V4_0.csv` (`python/nomes_v4_0.py`). As 387 fórmulas são as da V3.0, com o mesmo texto (D13); só mudam 00_README A3 e a linha 20 do 15_CHANGELOG (`docs/registro-de-versoes-V4_0-celulas.md`). Dados por chave entre a V3.0 viva e a V4.0: `python/dados_planilha.py` e `tools/migrar_dados_v3_v4.py` (EDR-058). |

A V4.0 não muda nenhum cálculo da planilha: os resultados lidos pelos nomes são iguais aos da V3.0 nos mesmos
endereços (TC-WB40-005). As entradas da planilha continuam demonstrativas (T09/E03) e o pneu continua o
provisório do TTC (EDR-038); nada disso é resultado do carro.

## Testes (`tools/rodar_testes.py`)

Esperado ao fim da V4.0: pneu 43, oráculos 5, suspensão 54, cinemática 76, hardpoints 35, equilíbrio 28,
equilíbrio linear 18, V4.0 nomes e dados 4 (`tests/test_v4_0.py`, TC-WB40-001 a 004); mutação 25/25 do pneu e
6/6 do equilíbrio; autoteste do comparador 15/15; CA-07 com a V2.4 (347 fórmulas), a V3.0 (387) e a V4.0 (387
fórmulas e 698 nomes) regeneradas sem diferença; `tests/test_workbook.py` 19/19, `tests/test_workbook_suspensao.py`
15/15 e `tests/test_workbook_v4_0.py` 2/2 (TC-WB40-005 e 006), no Excel via COM ou no LibreOffice.

## Como migrar os dados da equipe

A viva da equipe continua a V3.0. Quando o usuário fornecer o arquivo da pasta compartilhada:

```text
export UV_SYSTEM_CERTS=1
uv run python -X utf8 tools/migrar_dados_v3_v4.py <viva_V3_0.xlsx>
```

- Saída: `build/V4_0_com_dados.xlsx`; relatório: `build/migracao-V3-V4.md` (`--saida` e `--relatorio` mudam os
  caminhos; nenhum dos dois pode ficar em `excel/`).
- A viva é comparada com a V3.0 da tag `v3.0`. Célula alterada fora dos nomes de dado (`ent`, `org`, `fte`) é
  erro e sai com código 2, sem gravar a saída.
- Conflito (destino da V4.0 diferente da base) vai para o relatório e a célula não é sobrescrita; a ferramenta sai
  com código 1. Sem conflito nem falta, sai com 0.
- A viva e a V4.0 de origem só são lidas; nada é recalculado.

## Pendências

- Caminho da pasta compartilhada da viva e responsável pelos retratos `dados:` (EDR-051): a informar (usuário,
  2026-10-21). A migração roda quando o usuário fornecer o arquivo; a troca da viva para a V4.0 é decisão dele.
- Pneu do carro (R60A) ou dataset do OptimumTire: o equilíbrio usa o `.tir` provisório do TTC (EDR-038, EDR-055).
- EDR-057 está APPROVED_WITH_CONDITIONS: o usuário confere as escolhas de método no relatório do incremento 2.
- A reescrita das 387 fórmulas para nomes fica para o incremento 7 (D13).
