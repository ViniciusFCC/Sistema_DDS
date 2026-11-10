# Registro de versões — Sistema_DDS — V4.4 (incremento 8, parte 8b)

Data: 2026-11-10. A V4.4 é a parte 8b do incremento 8, a fundação parte 2: as fórmulas das abas 03 a 14 passam a ler por
nome toda célula única, e os valores calculados continuam os da V4.3. Decisões: EDR-070 (a V4.4 e a verificação por valor) e
EDR-066 (limitação do K e correção do aviso do R). Spec: `docs/superpowers/specs/2026-11-09-inc8-fundacao-nomes-design.md`;
plano: `docs/superpowers/plans/2026-11-09-inc8-fundacao-nomes.md`. O usuário aprovou os itens A1 a A5 em 2026-11-09; as
decisões D1 a D6 do controlador não foram revertidas.

## O que entrou

| Item | Entrou |
|---|---|
| Planilha de referência | `excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx`, gerada da tag `v4.3` por `python/gerar_v4_4.py`, com 146373 fórmulas (as mesmas da V4.3), 29 abas e 1290 nomes definidos (os 1266 da V4.3 e 24 novos, de `data/nomes_V4_4.csv`). A cópia para `excel/` é um commit próprio (`excel: V4.4 de referência gerada por python/gerar_v4_4.py`). |
| Regra da troca | Nas abas 03 a 14, cada operando que é referência a uma única célula (com ou sem aba, com ou sem `$`) e destino exato de um nome definido é trocado por esse nome. Texto entre aspas, funções e operadores não mudam. Intervalos, colunas inteiras e a linha própria da ficha da 03_TARGETS que não tem nome ficam por endereço (`python/reescrita_nomes.py`). |
| Nomes novos | 24 células soltas ganham nome (`data/nomes_V4_4.csv`, regras do EDR-058): 10_TIRE B20:F20, B21:F21, F22:F25, B176, I11, I21 e I176; 13_VALIDATION B37:B39; 16_EQUILIBRIO E188:E190. O invariante dos nomes (spec §3.5) não admite folga, por isso toda célula solta dessas três abas recebeu nome. |
| Células reescritas | 422 fórmulas das abas 03 a 14 (2787 trocas de operando, contadas pelo TC-WB44-002), mais 6 células das exceções X2 a X5: 428 células diferentes da V4.3. O catálogo, com a fórmula antes e depois de cada uma, é `docs/registro-de-versoes-V4_4-celulas.md` (gerado, nunca editado à mão). |
| Exceções | X2: 16_EQUILIBRIO F188 (limitação do K, EDR-066). X3: 14_DASHBOARD B48 (o trecho `diâmetros do regulamento FSAE 2026 D.10.1.1` passa a `diâmetros da 24_CURVA B5 e B6`, pendência 6). X4: 00_README A3 (versão). X5: 15_CHANGELOG A24:C24 (linha nova, com "24 nomes novos"). |
| Python | `python/reescrita_nomes.py`, `python/nomes_v4_4.py`, `python/gerar_v4_4.py` e `REFERENCIAS["V4.4"]` em `python/viva.py`. |
| Ferramentas | `tools/rodar_testes.py` com `test_v4_4`, `test_workbook_v4_4` (limite de 7200 s), a mutação `mutation_planilha_v44` e o bloco CA-07 da V4.4; `FORMULAS_ESPERADAS_V44` em `tools/comparar_planilhas.py`. |
| IDs | Só os já aprovados: EDR-070 e TC-WB44-001 a 006. Nenhum SUS-, REQ- ou outro TC-. |
| Documentos | `docs/registro-de-versoes-V4_4-celulas.md` (gerado) e este registro. |

A V4.4 não muda nenhum valor em relação à V4.3: a equivalência por valor (TC-WB44-005) compara todas as células de todas as
abas, com tolerância zero. "Passou" quer dizer que a V4.4 reproduz a V4.3; não é validação física (Validation =
NOT_VALIDATED, EDR-022).

## Medição na V4.3 (2026-11-09, Task 11)

Feita com o `Tokenizer` do openpyxl sobre `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`, nas abas 03 a 14: 454 fórmulas e 3274
operandos de referência. Desses, 412 já são nome; 2664 são endereço de célula única que tem nome (trocáveis); 35 são a linha
própria da ficha da 03_TARGETS sem nome; 36 são intervalos; 4 são colunas inteiras; e 123 são referências a 24 células soltas,
que não tinham nome. A soma fecha em 3274. Há 462 `IF` e 350 `IFERROR`, e nenhuma função volátil ou indireta. Trocas previstas
e feitas: 2664 + 123 = 2787.

Esta medição substitui a da §3.1 da spec (2862 referências, 198 sem nome, 9 células soltas). A diferença foi achada na
preparação do plano: as "9 células soltas" eram 9 referências a 6 células (13_VALIDATION B37:B39 e 16_EQUILIBRIO E188:E190),
e das 118 referências da 10_TIRE, 114 apontam para 17 células únicas sem nome. O total de células sem nome é 24, e não 23 (o
plano somou errado; a tabela A1 aprovada tem 24 linhas). O arquivo tem, portanto, 1290 nomes, e não 1289.

## Limitação do K (pendência 13)

O K do gradiente de subesterço exibido na planilha (16_EQUILIBRIO B188, lido pelo 14_DASHBOARD B41) não inclui o arrasto, a
resistência ao rolamento nem o Fx exigido pelo balanço completo (hipóteses 10 e 9b da escada). Num caso sintético, sem dado
do carro, a diferença foi ΔK = +1,57 °/g (EDR-065 item 3, `docs/inc6/escada-caso-sintetico.md`). A frase foi acrescentada
ao fim do texto da 16_EQUILIBRIO F188 (X2) e registrada no item 5 do EDR-066. O valor vale até haver dados do T11: a
confirmar. Nenhuma física nova entrou; ela é escopo da V5.0.

## Verificação da V4.4 no lugar do CA-07 por texto

- **TC-WB44-001** (`tests/test_v4_4.py`): `gerar_v4_4` da tag `v4.3` bate com `excel/…V4_4.xlsx` por conteúdo, com estrutura.
- **TC-WB44-002**: regra da troca, célula a célula, nas abas 03 a 14, com o alinhamento de tokens. Fora das exceções,
  qualquer diferença é FAIL.
- **TC-WB44-003**: invariante dos nomes (nas abas 03 a 14, todo operando de célula única é nome ou linha própria da 03).
- **TC-WB44-004**: migração por nome (os nomes da V4.3 existem na V4.4 com o mesmo destino e os 24 novos não existiam na V4.3).
- **TC-WB44-005** (`tests/test_workbook_v4_4.py`): equivalência por valor V4.3 x V4.4, tolerância zero, no mesmo motor, em
  cópias. Casos: o nominal, 30 perturbados (semente `20261109`, faixa de ±20 %, N escolhido em A4), 4 dirigidos do D3
  (`DIR_ORIGENS_VAZIAS`, `DIR_CHAVES_INVERTIDAS`, `DIR_NUMERICAS_VAZIAS` e `DIR_DIREITA`, que substituiu o `DIR_ESQUERDA`
  porque "Esquerda" já é o valor nominal) e 26 dirigidos da cobertura: 61 casos. Os valores perturbados são sintéticos de
  teste, rotulados assim no log; nunca dado do carro. No Excel: 61 casos, 0 diferença. O caso `DIR_NUMERICAS_VAZIAS` dá 893
  células com erro, iguais nas duas versões.
- **TC-WB44-006**: cobertura de ramos. 1624 lados em 812 ramos (`IF` e `IFERROR`), 1552 cobertos e 72 não cobertos, que o
  usuário aprovou como estão em 2026-11-09, com os motivos A (14), B (4), C (36), D (16) e E (2), definidos em
  `tests/test_workbook_v4_4.py`. Nenhum ramo em matriz. Com `DDS_CASOS44` definido, o TC-WB44-006 sai PULADO e não conta
  como PASS: a cobertura com um subconjunto de casos nunca fecha.
- **Mutação** `tests/mutation_planilha_v44.py`: 4 mutantes (nome trocado por outro de mesmo papel, nome trocado pelo
  endereço da vizinha, operador de um ramo de `IF` e uma constante), todos detectados pelo TC-WB44-005: 4/4.

## Medição do recálculo e escolha do N (A4)

Medição de 2026-11-09 (`tools/medir_recalculo.py`, cópia da tag `v4.3`, Excel 16.0, 20 threads, 3 execuções; log em
`build/medicao-recalculo-v4-3.md`, fora do Git). Cenário A (arquivo gravado pelo openpyxl, sem cache, como as cópias de
teste): abrir 8,51 s (inclui o cálculo de carga), `CalculateFull` 0,11 s, gravar 1,41 s, fechar 0,36 s, total 10,39 s
(mediana). Cenário B (já salvo pelo Excel): 3,19 s. O openpyxl leva 1,0 s para abrir, 1,5 s para gravar e 1,0 s para abrir com
`data_only`. Com isso, o custo previsto por caso era de cerca de 30 s e o N escolhido foi 30 perturbados.

O tempo real por caso foi maior que o previsto: na rodada final de 61 casos, média de 66,1 s e máximo de 89,0 s. Na rodada
anterior de 35 casos, a média foi de 45,1 s e o máximo, de 75,4 s (P09). Antes disso, uma rodada parcial passou de 60 s, o
limite de A4, e a execução parou e avisou. O usuário aprovou o limite de **120 s por caso** (`LIMITE_S`) em 2026-11-09, sem
reduzir N. O item da suíte tem limite de 7200 s (`TIMEOUT_PLANILHAS`), porque o LibreOffice é mais lento e ainda não foi
medido nesta planilha.

## Células existentes alteradas

Veja `docs/registro-de-versoes-V4_4-celulas.md`. Em resumo: as 422 fórmulas das abas 03 a 14 reescritas pela regra (nenhuma
muda de valor) e as 6 células das exceções X2 a X5.

## Parte 8a: pendências do incremento 7

Tratadas antes da 8b, um commit por propósito (spec §6): laços de mutação e de planilhas do executor em funções, com teste
(TC-RUN-001 i, j; pendência 3); quebra de linhas longas (7); tolerância do `FORMAS_V43` em
`tests/test_equilibrio_linear.py`, agora por erro absoluto de 1e-5 °/g (medido 1,83e-6 °/g; pendência 4); recusa do
`--caso-sintetico` com `--saida` no relatório da planilha (5); a guarda da B28 da 24_CURVA por regra e a grade da 17 sem
regex (8); regeneração de `docs/inc6/escada-hipoteses.md` (8); V4.3 em Comandos do CLAUDE.md, EDR-064 APPROVED no índice e a
forma exata atan(L·t/(R_c² + L² − t²/4)) na §4.1 da spec do inc. 7 (9, 10 e 11). A pendência 6 virou a exceção X3. As
pendências 1 e 2 (suíte no LibreOffice e item "planilha vs V4.3 de referência") e a promoção do EDR-064 a VERIFIED ficam para
a suíte única; a 12 (auditoria do LEIA-ME e aviso dos campos dos `.docx`) ficou para o fechamento (D5).

## Testes (`tools/rodar_testes.py`)

Contagens esperadas: `test_v4_4` 4 (TC-WB44-001 a 004), `test_workbook_v4_4` 5 (TC-WB44-005, TC-WB44-006 e 3 checagens de
apoio: ausência de funções voláteis, fecho de dependentes das exceções vazio e pré-checagem da contagem de ramos), mutação da
planilha V4.4 4/4. Medido nos Tasks 14 a 17: `test_workbook_v4_4` 5 PASS de 5 no Excel (61 casos, 0 diferença; 1552 de 1624
lados cobertos, 72 aprovados) e a mutação 4/4. A suíte única, sem `--pular-recentes`, no Excel e no LibreOffice, ainda não
rodou: **a confirmar** (Task 19). Só depois dela o EDR-070 passa de IMPLEMENTED a VERIFIED.

## CA-07 daqui em diante

A V3.0 a V4.3 mantêm os testes como estão (por texto ou por SHA), porque são referências congeladas. A V4.4 usa os TC-WB44-001
a 006 no lugar do CA-07 por texto contra a versão anterior. **A V4.5 volta ao CA-07 por texto, contra a V4.4** (spec §4.1); a
equivalência por valor fica disponível para as versões em que a física muda, como a V5.0.

## Pendências

- **Suíte única e LibreOffice:** a confirmar (Task 19).
- **Drive:** a viva continua a V4.3 até a troca (`conferir_viva`, `migrar_viva` por nome, conflito listado e nunca
  sobrescrito). A troca, o LEIA-ME e os `.docx` do Drive só com a confirmação do usuário (Task 20).
- **Tolerância do NEUTRO e K:** valores a confirmar com o T11 (EDR-065 item 3; limitação do K).
- **Diâmetros do skidpad:** a conferência com a FSAE Brasil fica para o incremento 9 (EDR-069).
- **Pneu e T11:** o equilíbrio continua usando o `.tir` provisório do TTC (EDR-038, EDR-055); a planilha ainda não tem dado do
  T11.
- **Minors adiados nas revisões:** ficam no ledger do incremento (`.superpowers/sdd/2026-11-09-inc8-fundacao-nomes/progress.md`).
