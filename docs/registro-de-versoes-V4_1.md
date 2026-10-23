# Registro de versões — Sistema_DDS — V4.1 (incremento 4)

Data: 2026-10-22. A V4.1 cobre o incremento 4 da especificação
`docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` (equilíbrio na planilha). Decisões: EDR-059
(faixa de ID SUS-10XX) e EDR-060 (método, fórmulas e alterações em células existentes), com o EDR-055, o EDR-056, o
EDR-057 e o EDR-058 por baixo. Plano: `docs/superpowers/plans/2026-10-21-v4-1-inc4-equilibrio-na-planilha.md`.

## O que entrou

| Item | Entrou |
|---|---|
| Planilha de referência | `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx`, gerada da tag `v4.0` por `python/gerar_v4_1.py` (famílias de fórmula em `python/aba_equilibrio.py`), com 117569 fórmulas (as 387 da V4.0 e 117182 novas) e 1145 nomes definidos (os 698 da V4.0 e 447 de `data/nomes_V4_1.csv`). |
| Abas novas | `16_EQUILIBRIO` (entradas, chaves, resultados e exibição), `17_EQ_PAR` (grade pedida), `18_EQ_PAR_FINA` (grade refinada), `19_EQ_LINEAR` (passo 1, K pelas parcelas), `20_EQ_TROCA` e `20a_TROCA` a `20d_TROCA` (tabela de troca da barra dianteira), `21_COBERTURA` (o que o modelo cobre) e `22_CADEIA` (cadeia de decisão), mais um bloco novo no `14_DASHBOARD` (linhas 40 a 47). |
| Python | `caso_planilha.caso_da_planilha_v41` (caso lido da planilha pelos nomes) e `pior_origem_do_caso_v41`; derivada de um lado em a_y = 0 no deslocamento com a carga (`equilibrio_linear`), rótulo novo da parcela; `tools/relatorio_inc4.py`. |
| IDs | SUS-1001 a SUS-1008 (EDR-059); TC-WB41-001 a TC-WB41-006. |
| Relatório | `docs/v4-1/inc4-equilibrio-na-planilha.md` (caso nominal, robustez ao pneu do EDR-055, tabela de troca, tempos); `docs/v4-1/inc4-viabilidade-tabela-de-troca.md` (portão da Task 4). |

Decisões de forma, todas no EDR-060: a robustez ao pneu fica no relatório e não na planilha; um sentido de curva por
vez; tabela de troca com 5 valores de K_ARB dianteiro (×0,5; 0,75; 1; 1,5; 2), grade de exibição e não meta; chaves
h2, h3, h7, h8 e h9 desligadas por padrão, e h3 estrita; diferencial aberto sem chave.

## Células existentes alteradas

O antes e o depois de cada célula estão em `docs/registro-de-versoes-V4_1-celulas.md` (gerado). Em resumo:

- `10_TIRE` (EDR-056): 215 fórmulas, mais o status B26:F26, a nota I26 e o rótulo A31. Fz, α, γ e κ fora da faixa do
  `.tir` entram limitados ao limite, com aviso na linha de status; só Fz ≤ 0 continua N/A. Dentro da faixa nenhum valor
  muda (TC-WB41-003). Antes, a V3.0 e a V4.0 davam N/A fora da faixa.
- `13_VALIDATION` B40:B43 e C43: com o caso VERIF limitado, B40:B42 mostram "N/A - caso VERIF limitado à faixa
  (EDR-056)" em vez de "FAIL - Excel diverge"; B43 conta "OK" e "OK - limitado …" como válidos; a C43 diz quantos
  foram limitados.
- Textos: `13_VALIDATION` A25, `00_README` A8, A37 e A53 e `14_DASHBOARD` A19 (spec §12.1 e consequência da limitação
  do pneu); `00_README` A3 (V4.1) e `15_CHANGELOG` linha 21.

A planilha viva da equipe continua a V3.0. A V4.1 não a substitui.

## Testes (`tools/rodar_testes.py`)

Esperado ao fim da V4.1: pneu 43, oráculos 5, suspensão 54, cinemática 76, hardpoints 35, equilíbrio 28, equilíbrio
linear 18, V4.0 nomes e dados 4, V4.1 estrutura e CA-07 2 (`tests/test_v4_1.py`, TC-WB41-001 e 002); mutação 25/25
do pneu, 6/6 do equilíbrio e 5/5 da planilha do equilíbrio (`tests/mutation_planilha_equilibrio.py`, só Excel, minutos);
autoteste do comparador 15/15; CA-07 com a V2.4 (347 fórmulas), a V3.0 (387), a V4.0 (387 fórmulas e 698 nomes) e a
V4.1 (117569 fórmulas e 1145 nomes) regeneradas sem diferença; `tests/test_workbook.py` 19/19,
`tests/test_workbook_suspensao.py` 15/15, `tests/test_workbook_v4_0.py` 2/2 e `tests/test_workbook_v4_1.py` 5/5
(TC-WB41-003 a 006, o 006 em duas partes), no Excel via COM ou no LibreOffice. Obtido em 2026-10-22 (suíte inteira no Excel; os quatro scripts de planilha também no LibreOffice): tudo PASS, com esses números. Detalhes na seção Evidence do EDR-060.

"Passou" é a planilha reproduzir o oráculo em Python nos casos de teste (valores de teste rotulados, só em cópias);
não é validação física (Validation = NOT_VALIDATED, EDR-022).

## Pendências

- EDR-060 aprovado em 2026-10-22: o usuário conferiu o relatório `docs/v4-1/inc4-equilibrio-na-planilha.md`;
  os itens PENDING_CONFIRMATION do item 8 continuam pendentes.
- PR #17 mesclado em 2026-10-22; tag da V4.1 a definir com o usuário. O nome da versão do incremento 5 em diante também.
- Caminho da pasta compartilhada da viva e responsável pelos retratos `dados:` (EDR-051, EDR-058): a informar; a troca
  da viva para a V4.0 ou a V4.1 é decisão do usuário.
- Pneu do carro (R60A) ou dataset do OptimumTire: o equilíbrio usa o `.tir` provisório do TTC (EDR-038, EDR-055).
- Limitações conhecidas do EDR-060 (item 8): grades extras da tabela de troca sob o {ok} global; pior origem do K
  conservadora na tabela de troca; "Neutro" só com K = 0 exato; rótulo "Δt" com o tempo de volta absoluto; κ limitado
  só na `10_TIRE` (o Python do pneu levanta `TireRangeError`); troca a↔b pega só pelo caso C1 na mutação; CA-07 sem
  notas de célula.
- Entradas do caso ainda demonstrativas (T09/E03): R, CzA, ρ, CdA e Crr vazios; toe e CG lateral em 0, "a confirmar".
- Incremento 5 (metas e coerência) em diante: spec §10.
- Reescrita das 387 fórmulas antigas para nomes: incremento 7 (D13).
