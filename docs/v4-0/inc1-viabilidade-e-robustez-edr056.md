# V4.0, incremento 1: viabilidade da análise de par na planilha e robustez ao pneu

Gerado por `tools/relatorio_inc1.py`. Não edite à mão: para atualizar, gere um relatório novo com outro nome.

Todos os números deste relatório são **demonstrativos**: o caso vem da planilha V3.0 com valores do T09, estimativas e entradas arbitrárias, e o pneu é o `.tir` provisório do TTC (R25B), não o pneu do carro. Nada aqui é resultado do TX nem validação física (Validation = NOT_VALIDATED).

## 1. Origem

- Data: 2026-10-21T00:58:48
- Commit: `20686a26b12349421e49df7c87db6c6f657b1f03` (ramo `feat/v4-0-regras-limite`; árvore sem mudanças pendentes ao iniciar)
- Planilha viva: `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`
  - SHA-256 antes: `659fcf01f006b68a0e8a3c6df9da48e9b1b304764713b1fff975264d5e9db56b`
  - SHA-256 depois: `659fcf01f006b68a0e8a3c6df9da48e9b1b304764713b1fff975264d5e9db56b` (igual: a viva não foi alterada; só uma cópia temporária foi recalculada)
- Motor de recálculo da cópia: excel (Excel 16.0 via COM, PID 36316); 387 fórmulas, 0 erros, 1,4 s
- Pneu: `data/Hoosier_R25B_13x7_TTC_provisional.tir` (SHA-256 `f3bc80fda4145d53da06f69c8c0fcffbddfbbf73f4aab4149e1caa386c77c796`), carregado em ISO_TYDEX (EDR-039)
- Varredura: `data/varredura_pneu_exploratoria.json` (EDR-055, origem "○ Arbitrário / demonstrativo")
- Experimento de viabilidade: `build/exp_viabilidade_par.json` (Task 6, `tests/exp_viabilidade_par.py`; fora do Git; SHA-256 `e04a1b6eb27cf46c9c52ca95c8884da7831769d917a44c645276f01c3d49b1db`, modificado em 2026-10-20T19:29:35)
- Python 3.13.16, openpyxl 3.1.5, numpy 2.5.4

## 2. Caso

Entradas lidas da cópia recalculada (`caso_planilha.ENTRADAS_CASO`). Pior origem do caso: **○ Arbitrário / demonstrativo** (pior rótulo entre as raízes das entradas e o pneu; `caso_planilha.pior_origem_do_caso`).

| Entrada | Célula | ID | Valor | Unidade | Pior origem das raízes |
|---|---|---|---|---|---|
| Massa total (com piloto) | `05_VEHICLE!B4` (fórmula) | SUS-001 | 316,5000 | kg | ○ Estimativa |
| Altura do CG (total) | `05_VEHICLE!B5` | SUS-002 | 0,3150 | m | ● Dado do TX |
| Wheelbase (L) | `05_VEHICLE!B6` | SUS-003 | 1,5940 | m | ● Dado do TX |
| Front Track (t_F) | `05_VEHICLE!B7` | SUS-004 | 1,2770 | m | ● Dado do TX |
| Rear Track (t_R) | `05_VEHICLE!B8` | SUS-005 | 1,2710 | m | ● Dado do TX |
| CG -> eixo dianteiro (a) | `05_VEHICLE!B9` (fórmula) | SUS-006 | 0,8220 | m | ● Dado do TX |
| CG -> eixo traseiro (b) | `05_VEHICLE!B10` (fórmula) | SUS-006 | 0,7720 | m | ● Dado do TX |
| Massa não-suspensa dianteira | `05_VEHICLE!B14` | SUS-007 | 15,0000 | kg | ○ Arbitrário / demonstrativo |
| Massa não-suspensa traseira | `05_VEHICLE!B15` | SUS-008 | 18,0000 | kg | ○ Arbitrário / demonstrativo |
| Altura CG não-suspenso dianteiro | `05_VEHICLE!B16` (fórmula) | SUS-010 | 0,2540 | m | ○ Estimativa |
| Altura CG não-suspenso traseiro | `05_VEHICLE!B17` (fórmula) | SUS-011 | 0,2540 | m | ○ Estimativa |
| Spring Rate dianteiro | `06_SUSPENSION!B4` | SUS-203 | 49909,2400 | N/m | ◐ Dado do T09 |
| Spring Rate traseiro | `06_SUSPENSION!B5` | SUS-203 | 57052,2200 | N/m | ◐ Dado do T09 |
| Motion Ratio dianteiro [wheel/spring] | `06_SUSPENSION!B6` | SUS-201 | 1,7600 | - | ◐ Dado do T09 |
| Motion Ratio traseiro [wheel/spring] | `06_SUSPENSION!B7` | SUS-201 | 1,7600 | - | ◐ Dado do T09 |
| K_ARB dianteiro | `06_SUSPENSION!B10` | SUS-206 | 5012,3200 | N*m/rad | ◐ Dado do T09 |
| K_ARB traseiro | `06_SUSPENSION!B11` | SUS-207 | 10,7800 | N*m/rad | ◐ Dado do T09 |
| Roll Center dianteiro (RH estático) | `06_SUSPENSION!B14` | SUS-401-F | 0,0675 | m | ◐ Dado do T09 |
| Roll Center traseiro (RH estático) | `06_SUSPENSION!B15` | SUS-401-R | 0,1100 | m | ◐ Dado do T09 |
| Rigidez vertical do pneu - dianteiro (K_T) | `06_SUSPENSION!B47` | SUS-211 | 120312,0000 | N/m | ◐ Provisório (.tir TTC) |
| Rigidez vertical do pneu - traseiro (K_T) | `06_SUSPENSION!B48` | SUS-211 | 120312,0000 | N/m | ◐ Provisório (.tir TTC) |
| Downforce total | `08_VEHICLE_STATE!B8` | SUS-701 | 400,0000 | N | ○ Estimativa |
| Aero Balance (fração dianteira) | `08_VEHICLE_STATE!B9` | SUS-702 | 0,4500 | - | ○ Estimativa |

Derivados usados pelo Python (`caso_planilha.caso_da_planilha`):

- K_φ dianteiro = 15316,0 N·m/rad; K_φ traseiro = 12909,8 N·m/rad (λ_f = 0,543)
- Downforce = 400,0 N e balanço dianteiro = 0,450, fixos (EDR-013)
- Toe estático: sem dado (EDR-036); usado 0 nas quatro rodas
- Camber estático: sem dado (EDR-036); usado 0 nas quatro rodas
- Ganho de camber: sem dado (EDR-036); usado 0 nas quatro rodas
- Pneu: FZMIN = 100 N, FZMAX = 1521 N, ALPMIN/ALPMAX = -0,2618/0,2618 rad, CAMMIN/CAMMAX = -0,0698/0,0698 rad, FNOMIN = 1054 N, LFZO = 1,00, LMUY = 1,00, LKY = 1,00
- Grade da análise de par (valores passados a `analise_par`): a_y de 0 a 2,00 g em passos de 0,05 g (41 linhas); 25 valores de α por eixo; κ = 0 (sem tração)

### Hipóteses incluídas no incremento 1 (spec, tabela 7.4)

| # | Hipótese | Base | Como entra no incremento 1 |
|---|---|---|---|
| 1 | α comum por eixo com deslocamento por roda | Milliken §7.1 | α_ref comum por eixo mais o Δα de toe de cada roda (`equilibrio.fy_eixo`). |
| 2 | Toe e Ackermann por roda | §7.1 | Só o toe estático por roda; o Ackermann fica para o incremento 2. Toe: sem dado (EDR-036). |
| 4 | Camber em curva | Gillespie eq. 6-50; §7.2 | Camber estático mais ganho linear dγ/dφ por roda (`equilibrio.camber`). Camber: sem dado (EDR-036). |
| 5 | Três massas, RC fixo, rolagem linear | EDR-009/011 | Três massas, RC fixo e rolagem linear (`suspension_model.lateral_dfz`). |
| 6 | Termo gravitacional da rolagem | EDR-046 | Termo gravitacional da rolagem, m_s·g·h2 (EDR-046, `suspension_model.lateral_dfz`). |
| 8 (parte) | Aero fixo por Setup | EDR-013 | Downforce e balanço da aba 08_VEHICLE_STATE, constantes em a_y. |

### Hipóteses não incluídas (incremento 2 ou depois)

O efeito é o da coluna "Efeito se ignorada" da tabela 7.4 da spec, copiado do arquivo por este script.

| # | Hipótese | Base | Efeito se ignorada |
|---|---|---|---|
| 2 (parte) | Ackermann por roda (SUS-414, precisa do raio R). | §7.1 | Muda a capacidade da frente |
| 3 | cos δ na frente | §7.1 | Superestima a frente (ordem de 1,5 % com δ ≈ 10°, estimativa a medir) |
| 7 | CG lateral, dois sentidos de curva | §7.2 | Um sentido piora |
| 8 (parte) | Dependência da downforce com a velocidade (V = √(a_y·R)); o incremento 1 usa downforce e balanço fixos do Setup (EDR-013). | Milliken cap. 3; EDR-013 | Subestima a_y em alta velocidade |
| 9 | Força de tração na traseira | Gillespie p. 222; §7.1 | Superestima a traseira (puxa para push) |
| 10 | Diferencial | Milliken cap. 20 | Travado puxa para push |
| 11 | Transferência longitudinal pela tração | cap. 18 | Pequena; medida |
| 12 | Jacking | Milliken p. 615 | Altura e camber |
| 13 | Compliance | §7.1; cap. 23 | Desconhecido, declarado |
| 14 | Mz no momento de guinada | Gillespie p. 222 | Pequeno no linear (< 0,5 °/g, Gillespie) |
| 15 | Pressão, temperatura, superfície | Milliken cap. 2 | Mais no a_y absoluto que no equilíbrio; rotular "pneu de teste" |
| 16 | Amortecedor e transiente | Milliken p. 283 | Declarado |

## 3. Resultado nominal (pneu sem escala)

Regras do veredito no limite: EDR-056 (APPROVED_WITH_CONDITIONS; a condição é o usuário conferir este relatório). Entrada do pneu fora da faixa do `.tir` entra limitada ao valor da faixa, com aviso; Fz ≤ 0 (descolamento) invalida a linha; NEUTRO só dentro da resolução numérica medida; PUSH/LOOSE pelo eixo que satura primeiro.

- Veredito: **DEMONSTRATIVO · N/A: não satura até 2 g**
- a_y de saturação do eixo dianteiro (S_f): —
- a_y de saturação do eixo traseiro (S_r): —
- S_r − S_f: — (um dos eixos não satura)
- Resolução numérica medida (grade pedida contra grade refinada): — (nenhum eixo satura em nenhuma das grades)
- a_y_lim: —
- C_N: — (só existe em PUSH ou LOOSE)

### Limitações da entrada do pneu (convenção do PAC2002, EDR-056)

Linhas válidas em que o pneu foi avaliado no limite da faixa do `.tir`, e não no valor real. É a convenção do PAC2002 (help do Adams 2024.1, p. 83; EDR-056). Entram as linhas usadas no veredito (sem a_y_lim, todas as linhas da grade). Limitar Fz ao FZMAX **subestima** a força da roda externa, porque a carga real é maior que a usada; o excesso mostra o tamanho do efeito.

| Roda | Grandeza | Limite aplicado | Primeira a_y | a_y do maior excesso | Valor real | Valor usado | Excesso (% do limite) |
|---|---|---|---|---|---|---|---|
| FL | Fz | FZMIN | 1,95 g | 2,00 g | 76,7 N | 100,0 N | 23,3 % |
| FR | Fz | FZMAX | 1,80 g | 2,00 g | 1607,0 N | 1521,0 N | 5,7 % |
| RR | Fz | FZMAX | 1,55 g | 2,00 g | 1704,7 N | 1521,0 N | 12,1 % |

### Fim do domínio

Todas as linhas da grade têm capacidade válida: o domínio não termina dentro da grade.

Sem saturação, a fração da capacidade usada por eixo na última linha da grade (2,00 g), req/cap, mostra a folga que sobra. **Não é veredito.**

| Eixo | Força exigida [N] | Capacidade [N] | req/cap |
|---|---|---|---|
| Dianteiro | 3007,4 | 3958,4 | 76,0 % |
| Traseiro | 3202,4 | 4005,4 | 80,0 % |

Linhas da grade até a primeira linha inválida (capacidade = máximo de Fy do eixo na grade de α, com a entrada do pneu limitada à faixa; "lim." marca capacidade calculada com limitação):

| a_y [g] | Fz_FL | Fz_FR | Fz_RL | Fz_RR | req_F [N] | cap_F [N] | req_R [N] | cap_R [N] | Observação |
|---|---|---|---|---|---|---|---|---|---|
| 0,00 | 842 | 842 | 911 | 911 | 0 | 4399 | 0 | 4721 |  |
| 0,05 | 823 | 861 | 891 | 930 | 75 | 4399 | 80 | 4722 |  |
| 0,10 | 804 | 880 | 871 | 950 | 150 | 4399 | 160 | 4722 |  |
| 0,15 | 784 | 899 | 851 | 970 | 226 | 4399 | 240 | 4722 |  |
| 0,20 | 765 | 918 | 831 | 990 | 301 | 4397 | 320 | 4721 |  |
| 0,25 | 746 | 937 | 811 | 1010 | 376 | 4396 | 400 | 4720 |  |
| 0,30 | 727 | 957 | 791 | 1030 | 451 | 4394 | 480 | 4718 |  |
| 0,35 | 708 | 976 | 772 | 1050 | 526 | 4391 | 560 | 4715 |  |
| 0,40 | 689 | 995 | 752 | 1069 | 601 | 4389 | 640 | 4713 |  |
| 0,45 | 670 | 1014 | 732 | 1089 | 677 | 4385 | 721 | 4709 |  |
| 0,50 | 651 | 1033 | 712 | 1109 | 752 | 4381 | 801 | 4705 |  |
| 0,55 | 631 | 1052 | 692 | 1129 | 827 | 4377 | 881 | 4701 |  |
| 0,60 | 612 | 1071 | 672 | 1149 | 902 | 4372 | 961 | 4696 |  |
| 0,65 | 593 | 1091 | 652 | 1169 | 977 | 4367 | 1041 | 4690 |  |
| 0,70 | 574 | 1110 | 633 | 1189 | 1053 | 4361 | 1121 | 4684 |  |
| 0,75 | 555 | 1129 | 613 | 1208 | 1128 | 4355 | 1201 | 4678 |  |
| 0,80 | 536 | 1148 | 593 | 1228 | 1203 | 4348 | 1281 | 4671 |  |
| 0,85 | 517 | 1167 | 573 | 1248 | 1278 | 4341 | 1361 | 4664 |  |
| 0,90 | 498 | 1186 | 553 | 1268 | 1353 | 4334 | 1441 | 4656 |  |
| 0,95 | 478 | 1205 | 533 | 1288 | 1429 | 4325 | 1521 | 4648 |  |
| 1,00 | 459 | 1224 | 514 | 1308 | 1504 | 4317 | 1601 | 4640 |  |
| 1,05 | 440 | 1244 | 494 | 1328 | 1579 | 4308 | 1681 | 4631 |  |
| 1,10 | 421 | 1263 | 474 | 1347 | 1654 | 4300 | 1761 | 4621 |  |
| 1,15 | 402 | 1282 | 454 | 1367 | 1729 | 4290 | 1841 | 4611 |  |
| 1,20 | 383 | 1301 | 434 | 1387 | 1804 | 4280 | 1921 | 4601 |  |
| 1,25 | 364 | 1320 | 414 | 1407 | 1880 | 4270 | 2001 | 4590 |  |
| 1,30 | 344 | 1339 | 394 | 1427 | 1955 | 4259 | 2082 | 4578 |  |
| 1,35 | 325 | 1358 | 375 | 1447 | 2030 | 4248 | 2162 | 4566 |  |
| 1,40 | 306 | 1377 | 355 | 1466 | 2105 | 4237 | 2242 | 4554 |  |
| 1,45 | 287 | 1397 | 335 | 1486 | 2180 | 4224 | 2322 | 4541 |  |
| 1,50 | 268 | 1416 | 315 | 1506 | 2256 | 4212 | 2402 | 4528 |  |
| 1,55 | 249 | 1435 | 295 | 1526 | 2331 | 4199 | 2482 | 4504 | R lim.: Fz_RR = 1526.0 N → 1521.0 N (FZMAX) |
| 1,60 | 230 | 1454 | 275 | 1546 | 2406 | 4185 | 2562 | 4450 | R lim.: Fz_RR = 1545.9 N → 1521.0 N (FZMAX) |
| 1,65 | 211 | 1473 | 255 | 1566 | 2481 | 4172 | 2642 | 4395 | R lim.: Fz_RR = 1565.8 N → 1521.0 N (FZMAX) |
| 1,70 | 191 | 1492 | 236 | 1586 | 2556 | 4158 | 2722 | 4341 | R lim.: Fz_RR = 1585.6 N → 1521.0 N (FZMAX) |
| 1,75 | 172 | 1511 | 216 | 1605 | 2631 | 4144 | 2802 | 4285 | R lim.: Fz_RR = 1605.5 N → 1521.0 N (FZMAX) |
| 1,80 | 153 | 1530 | 196 | 1625 | 2707 | 4110 | 2882 | 4230 | F lim.: Fz_FR = 1530.5 N → 1521.0 N (FZMAX); R lim.: Fz_RR = 1625.3 N → 1521.0 N (FZMAX) |
| 1,85 | 134 | 1550 | 176 | 1645 | 2782 | 4056 | 2962 | 4174 | F lim.: Fz_FR = 1549.6 N → 1521.0 N (FZMAX); R lim.: Fz_RR = 1645.2 N → 1521.0 N (FZMAX) |
| 1,90 | 115 | 1569 | 156 | 1665 | 2857 | 4001 | 3042 | 4118 | F lim.: Fz_FR = 1568.8 N → 1521.0 N (FZMAX); R lim.: Fz_RR = 1665.0 N → 1521.0 N (FZMAX) |
| 1,95 | 96 | 1588 | 136 | 1685 | 2932 | 3958 | 3122 | 4062 | F lim.: Fz_FL = 95.8 N → 100.0 N (FZMIN), Fz_FR = 1587.9 N → 1521.0 N (FZMAX); R lim.: Fz_RR = 1684.9 N → 1521.0 N (FZMAX) |
| 2,00 | 77 | 1607 | 116 | 1705 | 3007 | 3958 | 3202 | 4005 | F lim.: Fz_FL = 76.7 N → 100.0 N (FZMIN), Fz_FR = 1607.0 N → 1521.0 N (FZMAX); R lim.: Fz_RR = 1704.7 N → 1521.0 N (FZMAX) |

### Nota sobre a resolução: cenário do TC-EQ-011

Cenário do TC-EQ-011 de `tests/test_equilibrio.py`, recalculado aqui: veículo de teste simétrico (`veiculo_simetrico`, NÃO é setup real) com LMUY = 0,45 (escala só de teste, não é pneu). Mostra o que o veredito faz quando o passo da grade muda de 0,05 g para 0,01 g.

| λ_f | Passo [g] | S_f | S_r | S_r − S_f [g] | Resolução [g] | Veredito |
|---|---|---|---|---|---|---|
| 0,5 | 0,05 | 1,1715 g | 1,1715 g | 0,0000 | 0,0004 | DEMONSTRATIVO · ● NEUTRO no limite |
| 0,5 | 0,01 | 1,1715 g | 1,1715 g | 0,0000 | 0,0004 | DEMONSTRATIVO · ● NEUTRO no limite |
| 0,7 | 0,05 | 1,1490 g | 1,1889 g | 0,0399 | 0,0015 | DEMONSTRATIVO · ▲ PUSH: sai de frente (final understeer) |
| 0,7 | 0,01 | 1,1490 g | 1,1889 g | 0,0399 | 0,0015 | DEMONSTRATIVO · ▲ PUSH: sai de frente (final understeer) |

- λ_f = 0,5: NEUTRO com 0,05 g e NEUTRO com 0,01 g (o veredito não depende do passo da grade).
- λ_f = 0,7: PUSH com 0,05 g e PUSH com 0,01 g (o veredito não depende do passo da grade).
- De λ_f = 0,5 para 0,7 (passo 0,01 g), a saturação dianteira muda -0,0225 g e a traseira 0,0174 g; S_r − S_f passa de 0,0000 g para 0,0399 g.

## 4. Robustez ao pneu: varredura exploratória (EDR-055)

Fatores λ do PAC2002 multiplicados pelos valores de `data/varredura_pneu_exploratoria.json`: LFZO × 0,8, 1,0, 1,2; LMUY × 0,8, 1,0, 1,2; LKY × 0,8, 1,0, 1,2 (27 combinações). Rótulo: "○ Arbitrário / demonstrativo" (valores exploratórios; não são faixa do pneu (EDR-022)). Os fatores não alteram FZMIN/FZMAX. Tempo do Python para as 27 análises: 13,5 s.

| LFZO | LMUY | LKY | Veredito | S_f [g] | S_r [g] | S_r − S_f [g] | Resolução [g] | a_y_lim | Primeira a_y inválida | Limitações |
|---|---|---|---|---|---|---|---|---|---|---|
| 0,8 | 0,8 | 0,8 | DEMONSTRATIVO · ▼ LOOSE: sai de traseira (final oversteer) | — | 1,9566 | — | 3,6e-06 | 1,9566 g | — | 3 |
| 0,8 | 0,8 | 1,0 | DEMONSTRATIVO · ▼ LOOSE: sai de traseira (final oversteer) | — | 1,9565 | — | 0,0002 | 1,9565 g | — | 3 |
| 0,8 | 0,8 | 1,2 | DEMONSTRATIVO · ▼ LOOSE: sai de traseira (final oversteer) | — | 1,9562 | — | 0,0004 | 1,9562 g | — | 3 |
| 0,8 | 1,0 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 0,8 | 1,0 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 0,8 | 1,0 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 0,8 | 1,2 | 0,8 | DEMONSTRATIVO · N/A: pico na borda da grade de α em a_y = 1.8 g | — | — | — | — | — | 1,80 g | 1 |
| 0,8 | 1,2 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 0,8 | 1,2 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 0,8 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 0,8 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 0,8 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 1,0 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 1,0 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 1,0 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 1,2 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 1,2 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,0 | 1,2 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 0,8 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 0,8 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 0,8 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 1,0 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 1,0 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 1,0 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 1,2 | 0,8 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 1,2 | 1,0 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |
| 1,2 | 1,2 | 1,2 | DEMONSTRATIVO · N/A: não satura até 2 g | — | — | — | — | — | — | 3 |

Contagem: LOOSE = 3, N/A = 24.

"Limitações" é o número de avisos de entrada limitada (`ResultadoPar.limitacoes`) usados no veredito de cada combinação.

Veredito robusto (`veredito_robusto`): **NÃO CONCLUSIVO** (o sinal depende do pneu).

Texto de exibição com a robustez (`texto_veredito`, pior origem ○ Arbitrário / demonstrativo): **DEMONSTRATIVO · ? NÃO CONCLUSIVO: o sinal depende do pneu**

## 5. Viabilidade da análise de par em fórmulas (Task 6)

Dados de `build/exp_viabilidade_par.json`. O protótipo é uma pasta de trabalho gerada pelo openpyxl numa pasta temporária (não é planilha da equipe), com uma grade de 2.0 g / 0.05 g × 25 valores de α. "Base" é o recálculo da pasta de trabalho só com a aba de coeficientes; "recálculo" é o da cheia. Tolerância da comparação: 1e-09 (a mesma da CA-09). Casos `teste_*` usam o veículo de teste e escalas só de teste (não são o carro).

| Motor | Caso | Linhas | Células de fórmula | Base [s] | Recálculo [s] | Leitura openpyxl [s] | Erros | Dif. rel. máx. capacidade | Dif. a_y sat. F | Dif. a_y sat. R | Picos na borda (planilha/Python) | Aprovado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| excel | `teste_LMUY045` | 41 | 4677 | 0,078 | 0,474 | 0,149 | 0 | 2.9e-16 | 0.0e+00 | 1.6e-16 | 0/0 | sim |
| excel | `teste_LMUY045_toe_camber` | 41 | 4677 | 0,088 | 0,447 | 0,139 | 0 | 3.1e-16 | 0.0e+00 | 1.6e-16 | 0/0 | sim |
| excel | `teste_LMUY045_LKY023_borda` | 41 | 4677 | 0,087 | 0,588 | 0,124 | 0 | 3.0e-16 | 1.5e-16 | 0.0e+00 | 12/12 | sim |
| excel | `planilha_viva` | 41 | 4677 | 0,083 | 0,460 | 0,142 | 0 | 4.2e-16 | 0.0e+00 | 0.0e+00 | 0/0 | sim |
| libreoffice | `teste_LMUY045` | 41 | 4677 | 3,784 | 4,299 | 0,176 | 0 | 3.5e-15 | 6.1e-16 | 4.5e-15 | 0/0 | sim |
| libreoffice | `teste_LMUY045_toe_camber` | 41 | 4677 | 3,795 | 4,293 | 0,138 | 0 | 3.6e-15 | 2.0e-15 | 4.4e-15 | 0/0 | sim |
| libreoffice | `teste_LMUY045_LKY023_borda` | 41 | 4677 | 3,767 | 4,297 | 0,145 | 0 | 3.6e-15 | 3.1e-15 | 0.0e+00 | 12/12 | sim |
| libreoffice | `planilha_viva` | 41 | 4677 | 3,826 | 4,315 | 0,170 | 0 | 1.1e-15 | 0.0e+00 | 0.0e+00 | 0/0 | sim |

Conferência: o JSON da Task 6 foi gerado com a regra **anterior ao EDR-056** (faixa do pneu = N/A). Ele prova o tempo de recálculo e a exatidão das fórmulas, que não dependem da regra de faixa; o veredito e o motivo que ele registra para `planilha_viva` são os da regra antiga. Com a regra nova, o veredito e o motivo do caso `planilha_viva` no JSON **NÃO coincidem** com a análise deste relatório (JSON: N/A; Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g. Este relatório: N/A; não satura até 2 g). A diferença é esperada e não indica erro das fórmulas. Levar a regra nova para as fórmulas é mudança de fórmula e fica para o incremento que gerar a aba (aprovação própria).

## 6. Vai ou não vai: os números

Não há limiar registrado para decidir (spec §9, item 10: limite de desempenho só por decisão registrada). Os números abaixo não são veredito de viabilidade.

- Veredito nominal do caso da planilha: DEMONSTRATIVO · N/A: não satura até 2 g
- Veredito com a varredura (27 combinações): DEMONSTRATIVO · ? NÃO CONCLUSIVO: o sinal depende do pneu (veredito robusto: NÃO CONCLUSIVO; nota: o sinal depende do pneu)
- S_f = —, S_r = —, a_y_lim = —, resolução = — g
- Limitações de entrada do pneu nas linhas usadas no veredito: 3: Fz_FL = 76.7 N → 100.0 N (FZMIN); Fz_FR = 1607.0 N → 1521.0 N (FZMAX); Fz_RR = 1704.7 N → 1521.0 N (FZMAX)
- Recálculo do protótipo (excel): 0,45 a 0,59 s por caso; 4677 células de fórmula; 0 erros; diferença relativa máxima da capacidade 4.2e-16
- Recálculo do protótipo (libreoffice): 4,29 a 4,32 s por caso; 4677 células de fórmula; 0 erros; diferença relativa máxima da capacidade 3.6e-15
- Casos aprovados no experimento: 8 de 8
- Estimativa linear, **não medida**: a varredura de 27 combinações em fórmulas teria da ordem de 27 × 4677 = 126279 células de fórmula.
- Varredura no Python: 13,5 s para 27 análises

### Recomendação (não é decisão)

O que os números sugerem, para o usuário decidir:

1. A análise de par cabe em fórmulas nos dois motores: as fórmulas reproduziram o Python em todos os casos, com 0 erros. O recálculo do protótipo levou cerca de 0,6 s no Excel e 4,3 s no LibreOffice. Se esse tempo é aceitável é decisão da equipe.
2. A varredura em fórmulas multiplicaria o protótipo por 27 (estimativa acima, não medida). A spec (7.6, item 4) prevê a alternativa de o Python gerar o relatório da varredura e a planilha mostrar só o veredito nominal com o aviso "robustez ao pneu: ver relatório".
3. Com os dados demonstrativos atuais e o `.tir` provisório, o veredito do caso da planilha é DEMONSTRATIVO · N/A: não satura até 2 g no nominal e DEMONSTRATIVO · ? NÃO CONCLUSIVO: o sinal depende do pneu na varredura de 27 combinações (LOOSE = 3, N/A = 24). O resultado nominal usa 3 entrada(s) do pneu limitada(s) à faixa (seção 3); onde Fz foi limitado ao FZMAX, a força da roda externa está subestimada. Antes de usar o veredito para decidir algo do carro, é preciso o pneu do carro (hoje o .tir é o R25B provisório, EDR-022) e dados do TX no lugar dos demonstrativos.

### Decisões e pendências

Passam a valer pelo EDR-056 (APPROVED_WITH_CONDITIONS; o usuário confere este relatório): faixa do pneu limitada com aviso (convenção do PAC2002) e Fz ≤ 0 como descolamento (N/A); NEUTRO só dentro da resolução numérica medida; PUSH/LOOSE pelo eixo que satura primeiro. Deixam de ser pendentes a política de faixa e o critério de neutro.

Continuam pendentes:

- Pneu real (R60A): os números daqui usam o `.tir` provisório do R25B.
- Banda de neutro de engenharia: só por EDR da equipe (spec 7.3, item 4); hoje NEUTRO é só a resolução numérica.
- Alinhamento da aba 10_TIRE da V4.0 à regra da faixa: a V3.0 devolve N/A fora da faixa (DR-013, EDR-037, EDR-041); mudar é mudança de fórmula e entra na aprovação do incremento que gerar a aba.
- Descolamento (Fz ≤ 0) no modelo de transferência de carga: hoje a linha é inválida; tratar a roda interna levantada exige outro modelo.

A decisão de seguir, ajustar ou parar é do usuário.

