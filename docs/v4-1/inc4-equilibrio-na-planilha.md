# V4.1, incremento 4: equilíbrio na planilha, caso nominal, robustez ao pneu e tempos

Gerado por `tools/relatorio_inc4.py`. Não edite à mão: rode o script de novo (`--sobrescrever`).

Todos os números deste relatório são **demonstrativos**: o caso vem da planilha V4.1 de referência, com valores do T09/E03, estimativas e entradas arbitrárias, e o pneu é o `.tir` provisório do TTC (R25B), não o pneu do carro. Nada aqui é resultado do TX nem validação física (Validation = NOT_VALIDATED, EDR-022). Este é o documento que a célula de robustez da `16_EQUILIBRIO` cita; a decisão sobre ele está no EDR-060.

## 1. Origem

- Data: 2026-10-22T22:27:26
- Commit: `158916667eceba8363c623dceeeef31027ce9ba2` (ramo `feat/v4-1-inc4-equilibrio`; árvore sem mudanças pendentes)
- Planilha: `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` (SHA-256 antes `4193ffc5a8dffe824e0fae18a2c53d65117bf51a1956d22cb24c40cf355fdd3b`; depois igual: só uma cópia temporária foi recalculada)
- Motor de recálculo da cópia: excel (Excel 16.0 via COM, PID 20780); 117569 fórmulas, 0 erros, 20,4 s (abrir, recalcular tudo, gravar e fechar)
- Pneu: `data/Hoosier_R25B_13x7_TTC_provisional.tir` (SHA-256 `f3bc80fda4145d53da06f69c8c0fcffbddfbbf73f4aab4149e1caa386c77c796`), em ISO_TYDEX (EDR-039)
- Varredura: `data/varredura_pneu_exploratoria.json` (EDR-055, origem "○ Arbitrário / demonstrativo")
- Python 3.13.16, openpyxl 3.1.5, numpy 2.5.4

## 2. Caso da V4.1

Entradas lidas da cópia recalculada pelos nomes definidos (`caso_planilha.caso_da_planilha_v41`). Pior origem do limite: **? A confirmar**; pior origem do K (inclui o roll steer): **? A confirmar** (regra de `aba_equilibrio`; chaves e sentido são escolhas de modelagem e ficam fora dela). Por isso o texto de exibição leva o prefixo "DEMONSTRATIVO · " (D16).

Situação das entradas na planilha: **OK**.

Entradas novas da `16_EQUILIBRIO` (valor digitado; vazio = "a confirmar", EDR-036):

| Entrada | Valor | Unidade |
|---|---|---|
| Sentido da curva | Esquerda | - |
| Toe FL | 0 | ° |
| Toe FR | 0 | ° |
| Toe RL | 0 | ° |
| Toe RR | 0 | ° |
| Raio do skidpad R | vazio (a confirmar) | m |
| CG lateral (y_CG) | 0 | m |
| CzA | vazio (a confirmar) | m² |
| ρ (densidade do ar) | vazio (a confirmar) | kg/m³ |
| CdA | vazio (a confirmar) | m² |
| Crr (resistência ao rolamento) | vazio (a confirmar) | - |
| Chave h2: Ackermann (SUS-414) | 0 | 0/1 |
| Chave h3: cos δ_ref na frente | 0 | 0/1 |
| Chave h7: CG lateral | 0 | 0/1 |
| Chave h8: aero com V = √(a_y·R) | 0 | 0/1 |
| Chave h9: tração na traseira | 0 | 0/1 |

Chaves h2, h3, h7, h8 e h9 desligadas: o limite é o da análise de par básica (rolagem de três massas, SUS-103, downforce fixa do Setup, EDR-013; sem tração).

## 3. Resultado nominal

Grade da análise de par: a_y de 0 a 2,00 g em passos de 0,05 g (41 linhas), 25 valores de α por eixo, κ = 0.

| Grandeza | Python (`analise_par`) | Planilha (16_EQUILIBRIO) |
|---|---|---|
| Texto de exibição | DEMONSTRATIVO · N/A: não satura até 2 g | DEMONSTRATIVO · N/A: não satura até 2 g |
| S_f | — | N/A |
| S_r | — | N/A |
| a_y limite | — | N/A |
| Resolução numérica | — | N/A |
| C_N | — | N/A |
| Veredito / motivo | N/A / não satura até 2 g | N/A / não satura até 2 g |
| Avisos de limitação do pneu | Fz_FL = 76,7 N → 100,0 N (FZMIN); γ_FL = 13,80° → 4,00° (CAMMAX); Fz_FR = 1607,0 N → 1521,0 N (FZMAX); γ_FR = -16,80° → -4,00° (CAMMIN); γ_RL = 11,23° → 4,00° (CAMMAX); Fz_RR = 1704,7 N → 1521,0 N (FZMAX); γ_RR = -13,23° → -4,00° (CAMMIN) | Fz_FL = 76,7 N → 100,0 N (FZMIN); γ_FL = 13,80° → 4,00° (CAMMAX); Fz_FR = 1607,0 N → 1521,0 N (FZMAX); γ_FR = -16,80° → -4,00° (CAMMIN); γ_RL = 11,23° → 4,00° (CAMMAX); Fz_RR = 1704,7 N → 1521,0 N (FZMAX); γ_RR = -13,23° → -4,00° (CAMMIN) |

K do passo 1 (gradiente de subesterço, parcelas do Gillespie cap. 6): Python `DEMONSTRATIVO · K = -0,14 °/g (pneus + transferência + deslocamento com a carga (ply steer, conicidade, toe e camber estático) + camber + roll steer; sem compliance, torque de alinhamento e tração) · Sobresterço`; planilha `DEMONSTRATIVO · K = -0,14 °/g (pneus + transferência + deslocamento com a carga (ply steer, conicidade, toe e camber estático) + camber + roll steer; sem compliance, torque de alinhamento e tração) · Sobresterço`. Velocidades característica e crítica (Gillespie pp. 203-204): planilha N/A / 81,056 m/s (V_char só existe com K > 0 e V_crit só com K < 0; o outro fica N/A).

Parcelas de K em a_y = 0, em °/g: pneus 0,0076, transferência de carga 0,0000, deslocamento com a carga -0,0235, camber -0,1205, roll steer 0,0000, total -0,1364 (Python).

Tempo de volta no skidpad (SUS-1007): planilha `N/A` (precisa do raio R, que está vazio).

## 4. Limitações do modelo e deste relatório

- A planilha mostra o veredito nominal de **um** sentido de curva por vez (h7); troque o sentido para ver o outro (decisão 2 do EDR-060).
- A robustez ao pneu **não é recalculada na planilha**: a seção 5 abaixo é o único lugar em que ela existe, e vale para as entradas deste momento (decisão 1 do EDR-060).
- Pneu provisório do TTC (EDR-038); geometria sintética (não há hardpoints do CAD); mola, MR, barra e RC são valores demonstrativos do T09/E03, não do TX.
- Diferencial aberto é o único implementado (h10); as hipóteses 11 a 16 da spec ficam fora (aba `21_COBERTURA`).
- Pior origem do K conservadora e "Neutro" só com K = 0 exato; outras limitações conhecidas estão no EDR-060.
- O ganho de camber em rolagem sai das entradas SUS-404 da 07_KINEMATICS (autorização 7 do plano); o valor demonstrativo atual (−0,6 °/mm) dá ∂γ/∂φ ≈ −5,7 rad/rad, implausível, e por isso o camber em curva fica limitado ao CAMMIN/CAMMAX do pneu, com o aviso de limitação da seção 3. A causa é o dado demonstrativo, não o método.
- No caso demonstrativo nenhuma linha da tabela de troca satura até 2 g (seção 6), então o a_y do neutro e o custo ficam N/A. O cruzamento por interpolação é exercitado nos testes (TR1 do TC-WB41-006, com valores de teste) e passa a aparecer na planilha quando as entradas forem reais.
- Passou nos testes = a planilha reproduz o oráculo em Python; não é validação física.

## 5. Robustez ao pneu (EDR-055)

`equilibrio.varredura_pneu` sobre `caso_planilha.caso_da_planilha_v41`: LFZO, LMUY e LKY × {0,8; 1,0; 1,2} em produto cartesiano (27 combinações). Os multiplicadores são exploratórios, origem "○ Arbitrário / demonstrativo", e nunca uma faixa do pneu (EDR-022). Tempo da varredura no Python: 7,2 s.

| LFZO | LMUY | LKY | Veredito | a_y limite | C_N | Motivo do N/A |
|---|---|---|---|---|---|---|
| 0,8 | 0,8 | 0,8 | LOOSE | 1,926 g | -0,0180 | - |
| 0,8 | 0,8 | 1,0 | LOOSE | 1,926 g | -0,0179 | - |
| 0,8 | 0,8 | 1,2 | LOOSE | 1,926 g | -0,0180 | - |
| 0,8 | 1,0 | 0,8 | N/A | — | — | não satura até 2 g |
| 0,8 | 1,0 | 1,0 | N/A | — | — | não satura até 2 g |
| 0,8 | 1,0 | 1,2 | N/A | — | — | não satura até 2 g |
| 0,8 | 1,2 | 0,8 | N/A | — | — | pico na borda da grade de α em a_y = 1,2 g |
| 0,8 | 1,2 | 1,0 | N/A | — | — | não satura até 2 g |
| 0,8 | 1,2 | 1,2 | N/A | — | — | não satura até 2 g |
| 1,0 | 0,8 | 0,8 | LOOSE | 1,949 g | -0,0189 | - |
| 1,0 | 0,8 | 1,0 | LOOSE | 1,949 g | -0,0189 | - |
| 1,0 | 0,8 | 1,2 | LOOSE | 1,949 g | -0,0189 | - |
| 1,0 | 1,0 | 0,8 | N/A | — | — | não satura até 2 g |
| 1,0 | 1,0 | 1,0 | N/A | — | — | não satura até 2 g |
| 1,0 | 1,0 | 1,2 | N/A | — | — | não satura até 2 g |
| 1,0 | 1,2 | 0,8 | N/A | — | — | não satura até 2 g |
| 1,0 | 1,2 | 1,0 | N/A | — | — | não satura até 2 g |
| 1,0 | 1,2 | 1,2 | N/A | — | — | não satura até 2 g |
| 1,2 | 0,8 | 0,8 | LOOSE | 1,964 g | -0,0210 | - |
| 1,2 | 0,8 | 1,0 | LOOSE | 1,964 g | -0,0210 | - |
| 1,2 | 0,8 | 1,2 | LOOSE | 1,964 g | -0,0210 | - |
| 1,2 | 1,0 | 0,8 | N/A | — | — | não satura até 2 g |
| 1,2 | 1,0 | 1,0 | N/A | — | — | não satura até 2 g |
| 1,2 | 1,0 | 1,2 | N/A | — | — | não satura até 2 g |
| 1,2 | 1,2 | 0,8 | N/A | — | — | não satura até 2 g |
| 1,2 | 1,2 | 1,0 | N/A | — | — | não satura até 2 g |
| 1,2 | 1,2 | 1,2 | N/A | — | — | não satura até 2 g |

Resumo (`veredito_robusto`, spec 7.6 item 3): **NÃO CONCLUSIVO**, o sinal depende do pneu. Texto de exibição com a robustez: `DEMONSTRATIVO · ? NÃO CONCLUSIVO: o sinal depende do pneu`.

Contagem por veredito: LOOSE 9, N/A 18.

Robusto aqui significa apenas "o sinal não mudou com esta perturbação demonstrativa"; não valida o pneu.

## 6. Tabela de troca da barra dianteira (20_EQ_TROCA)

K_ARB dianteiro × {0,5; 0,75; 1; 1,5; 2} do valor da `06_SUSPENSION` (grade de exibição rotulada, **não é meta** nem faixa de projeto; decisão do usuário de 2026-10-22). Valores da planilha recalculada; a coluna "Python" confere o veredito e o a_y limite de cada linha.

| Fator | K_φF [N·m/rad] | λ_f | K [°/g] | S_f [g] | S_r [g] | a_y limite [g] | Veredito (planilha) | Python |
|---|---|---|---|---|---|---|---|---|
| ×0,50 | 13492,0 | 0,5110 | -0,1413 | N/A | N/A | N/A | N/A | N/A, a_y_lim — |
| ×0,75 | 14413,9 | 0,5275 | -0,1387 | N/A | N/A | N/A | N/A | N/A, a_y_lim — |
| ×1,00 | 15316,0 | 0,5426 | -0,1364 | N/A | N/A | N/A | N/A | N/A, a_y_lim — |
| ×1,50 | 17063,0 | 0,5693 | -0,1322 | N/A | N/A | N/A | N/A | N/A, a_y_lim — |
| ×2,00 | 18737,8 | 0,5921 | -0,1286 | N/A | N/A | N/A | N/A | N/A, a_y_lim — |

a_y do acerto neutro (cruzamento das saturações, spec 5 item 4): planilha N/A (motivo `neutro fora da faixa da tabela (S_r − S_f sem troca de sinal entre linhas vizinhas e nenhuma linha NEUTRO; sem extrapolação)`); Python — (neutro fora da faixa da tabela). Custo do comportamento = a_y do neutro − a_y limite atual: planilha N/A. Veredito do custo: `N/A` (a spec §5 item 5 não define limiar; nenhum número aqui diz se o custo é grande ou pequeno).

## 7. Tempos de recálculo

- Cópia da V4.1 inteira (117569 fórmulas): 20,4 s no motor excel (abrir, recalcular tudo, gravar e fechar; uma execução, incluindo a partida do programa). As medições anteriores do incremento (Tasks 5 e 6, mesmo motor) deram 8,8 s no Excel e 10,6 s no LibreOffice para a V4.1 da época (117532 a 117568 fórmulas); a diferença para esta execução não foi investigada: em 2026-10-22, quatro execuções deste mesmo relatório deram 22,9 s, 66,5 s, 67,9 s e 66,7 s no mesmo computador. O tempo medido aqui não é um limite nem uma garantia.
- Fórmulas por aba nova: 16_EQUILIBRIO 1080, 17_EQ_PAR 6826, 18_EQ_PAR_FINA 16058, 19_EQ_LINEAR 2817, 20_EQ_TROCA 227, 20a_TROCA 22536, 20b_TROCA 22536, 20c_TROCA 22536, 20d_TROCA 22536, 21_COBERTURA 5, 22_CADEIA 17.
- Medição do portão da Task 4, com o Excel recalculando só a troca do K_ARB (recálculo automático): `docs/v4-1/inc4-viabilidade-tabela-de-troca.md`. Lá, o recálculo completo (CalculateFull) com a tabela de 5 linhas e a grade refinada ficou em cerca de 0,3 s e a troca de uma entrada em cerca de 0,4 s; no LibreOffice, o recálculo com abrir e gravar ficou entre 11 e 12 s. Sem limiar registrado, o tempo não decide nada sozinho (spec §9, item 10).

