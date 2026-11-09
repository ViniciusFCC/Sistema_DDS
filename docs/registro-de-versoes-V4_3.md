# Registro de versões — Sistema_DDS — V4.3 (incremento 7, parte 7b)

Data: 2026-11-09. A V4.3 é a parte 7b do incremento 7: leva à planilha o centro de curva único, o raio do skidpad como
fórmula, as duas formas do EDR-066 atrás de chaves e a faixa do NEUTRO do EDR-065. Decisões: EDR-065 (itens 2 e 3),
EDR-066 (C-B11, C-B1 e C-M1), EDR-068 (executor dos testes) e EDR-069 (centro de curva e raio do skidpad). Catálogo
aprovado pelo usuário célula a célula em 2026-11-03; a C-B11 recebeu aprovação própria no mesmo dia. Plano do incremento 7:
`docs/superpowers/plans/2026-10-29-inc7-fisica-planilha.md` (Task 14 é este fechamento).

## O que entrou

| Item | Entrou |
|---|---|
| Planilha de referência | `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`, gerada da tag `v4.2` por `python/gerar_v4_3.py`, com 146373 fórmulas (as 117627 da V4.2 e 28746 novas), 29 abas e 1266 nomes definidos no arquivo (os 1225 da V4.2 e 41 novos, de `aba_curva.NOMES_V43`). Contagens lidas do arquivo com openpyxl, só leitura. A cópia para `excel/` é um commit próprio (`copia: V4.3 de referência`). |
| Aba nova | `24_CURVA`, no fim: modo do R (Linha central, Rente aos cones, Manual), diâmetros do skidpad, meia largura do pneu, R manual, chaves `h2v` e `h9v`, R usado, motivo, centro da curva, ângulos de Ackermann, fator da faixa do NEUTRO e situação (1ª falha). |
| R do skidpad | 16_EQUILIBRIO B9 passa a fórmula (`=res_24_r_usado`) e E9 passa a ser a pior origem do R; o R digitado fica em 24_CURVA B8, com o modo em B4 (EDR-069, D4). B65 e B173 deixam de usar `ISBLANK`. |
| Ackermann (h2v) | 16_EQUILIBRIO B114 e B115: centro da curva no eixo traseiro, com `h2v` = 1 (EDR-066, achado 1). Com `h2v` = 0 o valor é o da V4.2. |
| Fx exigido (h9v) | Colunas novas nas grades 17, 18, 20a a 20d e na mini-grade da 19 (arrasto induzido, `fy0_R`, `cap0_R`, `idx0_R`, `j_F`, `j_R`, `aF`, `aR`) e troca de `fxr`, `fat` e `pre_R` (EDR-066, achado 2). Com `h9v` = 0 o valor é o da V4.2. |
| Faixa do NEUTRO | 16_EQUILIBRIO B137 e B138 (e as linhas de `_regras_limite` da 20_EQ_TROCA): fator fixo 4/3 só no \|S − S2\| (EDR-065 item 2); a observação F142 explica. |
| Item 3 do EDR-065 | Decidido em 2026-11-09: só não inverter o veredito. A tolerância numérica fica **a confirmar** com o T11; nenhum valor foi inventado. |
| Situação e avisos | 16_EQUILIBRIO B78 (`status`) lê a situação da 24_CURVA; as linhas extras das 20a a 20d também (C-B11, EDR-066); 14_DASHBOARD A48:D48 avisa qual forma está em uso. |
| Migração | `dados_planilha._destinos` ignora nome de dado cuja célula é fórmula (C-M1, parâmetro `incluir_formulas` no `migrar_viva`); `migrar_viva` V4.2 para V4.3 leva o B9, E9 e F9 da viva à 24_CURVA B8, E8 e F8 e põe o modo em Manual quando há número (C-M2 a C-M4). |
| Barra de fórmulas | C-B1: o problema não foi reproduzido no arquivo (sem proteção, sem `FormulaHidden`, sem matriz); o gerador não muda. O LEIA-ME do Drive ensina a reativar a barra (`docs/inc7/recalculo-e-barra-de-formulas.md`). |
| Python | `python/aba_curva.py`, `python/gerar_v4_3.py`, `python/skidpad.py`, `Formas` (`FORMAS_V42` e `FORMAS_V43`) em `equilibrio` e `equilibrio_linear`, `estudo_neutro`, `caso_planilha.caso_da_planilha_v43`, `python/executor_testes.py` (EDR-068) e `REFERENCIAS["V4.3"]` em `python/viva.py`. |
| Ferramentas | `tools/rodar_testes.py` com a V4.3 na suíte (testes, planilha e mutações) e a opção `--pular-recentes ARQ`. |
| IDs | Nenhum ID novo nesta parte além dos já registrados: EDR-068 e EDR-069; TC-RUN-001, TC-SKP-001 e 002, TC-ACK-001 e 002, TC-FXI-001 e 002, TC-NEU-001 e 002, TC-WB43-001 a 006. |
| Documentos | `docs/registro-de-versoes-V4_3-celulas.md` (gerado, antes e depois de cada célula existente alterada), `docs/inc7/estudo-neutro.md`, `docs/inc7/conselho-catalogo-v43.md`, `docs/inc7/recalculo-e-barra-de-formulas.md`. |

As chaves `h2v` e `h9v` valem 1 por padrão na V4.3: o resultado muda em relação à V4.2 e o 14_DASHBOARD B48 avisa. Para
voltar à forma da V4.2, `h2v` = 0 e `h9v` = 0 em 24_CURVA B9 e B10.

## Células existentes alteradas

O antes e o depois de cada célula estão em `docs/registro-de-versoes-V4_3-celulas.md` (gerado por `python/gerar_v4_3.py`).
Em resumo: 16_EQUILIBRIO A9, B9, E9, F9, B65, B78, B114, B115, B137, B138, B173, E173 e F142; as células equivalentes de B137 e
B138 nas linhas de `_regras_limite` da 20_EQ_TROCA; o `status` das linhas extras das 20a a 20d (C-B11); as trocas de
`fxr`, `fat` e `pre_R` nas grades; 00_README A3 e 15_CHANGELOG (versão). 14_DASHBOARD A48:D48 são células novas. Toda
fórmula alterada foi aprovada célula a célula em 2026-11-03.

## Testes (`tools/rodar_testes.py`)

Suíte inteira de 2026-11-09 (06:15 a 08:30) sobre o commit e94abf0, com `--pular-recentes` (`build/verificacao-ultima.md`,
motor Excel 16.0 via COM): todos os itens PASS, 0 FAIL, código 0. Dois itens PULADO, que não contam como PASS:
`test_escada` (3/3 em 7b7db2e) e `test_v4_3` (3/3 em c122c47), sem mudança de código desde então. Mutações 25/25, 6/6,
5/5, 5/5, 5/5 do inc. 7 e 4/4 da planilha V4.3; `test_workbook_v4_3` 3/3; regenerações V2.4 a V4.2 com 0 diferença. A
regeneração da V4.3 contra `excel/` é coberta pelo TC-WB43-002 (no `test_v4_3`). O LibreOffice não rodou nesta suíte.
Contagens: executor 1, skidpad 2, formas 4, NEUTRO 2, `test_v4_3` 3
(TC-WB43-001, 002 e 006), `test_workbook_v4_3` 3 (TC-WB43-003 a 005), mutação do inc. 7 5/5 e da planilha V4.3 4/4. Nesta
parte rodaram `tests/test_executor.py` (1/1, com o caso novo da opção `--pular-recentes`) e `tests/test_v4_3.py` (3/3). O 3/3 de
c122c47 citado acima é de fora da suíte, que pulou o item; na rodada de correção da revisão final (2026-11-09), sem pular,
`test_v4_3` deu 3/3, `test_executor` 1/1 e `test_escada` 3/3. A suíte inteira não foi repetida depois dessa rodada, e o item
"planilha vs V4.3 de referência" que a suíte ganhou nela (regeneração da V4.3 contra `excel/`, 0 diferença) foi conferido à parte.
"Passou" é a planilha reproduzir o oráculo em Python nos casos de teste; não é validação física (Validation =
NOT_VALIDATED, EDR-022).

## Pendências

- **Suíte no LibreOffice** e revisão final: a confirmar (a suíte no Excel passou em 2026-11-09).
- **Tolerância do NEUTRO** (EDR-065 item 3): valor a confirmar com o T11.
- **Drive:** a viva continua a V4.2 até a troca (`conferir_viva`, `migrar_viva`); LEIA-ME e .docx do Drive precisam avisar que
  a 16 B9 virou fórmula e que o R digitado fica em 24_CURVA B8. Cada passo só com a confirmação do usuário.
- **Pneu e T11:** o equilíbrio continua usando o `.tir` provisório do TTC (EDR-038, EDR-055); a planilha ainda não tem dado do
  T11. Os diâmetros do skidpad (FSAE 2026 D.10.1.1) e a meia largura do pneu são provisórios e rotulados como tal.
- **Limitações** da escada e do centro da curva no eixo traseiro (α_R desloca o centro; texto em 24_CURVA A30:A32) continuam.
