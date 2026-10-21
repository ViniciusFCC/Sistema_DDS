# V4.0, incremento 1: viabilidade da análise de par na planilha e robustez ao pneu

Gerado por `tools/relatorio_inc1.py`. Não edite à mão: para atualizar, gere um relatório novo com outro nome.

Todos os números deste relatório são **demonstrativos**: o caso vem da planilha V3.0 com valores do T09, estimativas e entradas arbitrárias, e o pneu é o `.tir` provisório do TTC (R25B), não o pneu do carro. Nada aqui é resultado do TX nem validação física (Validation = NOT_VALIDATED).

## 1. Origem

- Data: 2026-10-21T00:09:06
- Commit: `960244a574fb23ab9b62fb81e90ba459d1d026e7` (ramo `feat/v4-0-inc1-viabilidade`; árvore sem mudanças pendentes ao iniciar)
- Planilha viva: `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`
  - SHA-256 antes: `659fcf01f006b68a0e8a3c6df9da48e9b1b304764713b1fff975264d5e9db56b`
  - SHA-256 depois: `659fcf01f006b68a0e8a3c6df9da48e9b1b304764713b1fff975264d5e9db56b` (igual: a viva não foi alterada; só uma cópia temporária foi recalculada)
- Motor de recálculo da cópia: excel (Excel 16.0 via COM, PID 38720); 387 fórmulas, 0 erros, 0,5 s
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
- Grade da análise de par: a_y de 0 a 2,0 g em passos de 0,05 g; 25 valores de α por eixo; κ = 0 (sem tração)

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

- Veredito: **DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g**
- a_y de saturação do eixo dianteiro: —
- a_y de saturação do eixo traseiro: —
- a_y_lim: —
- C_N: — (só existe em PUSH ou LOOSE)
- Primeira a_y em que alguma roda sai da faixa do pneu: **1,55 g** (Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX])

Cargas verticais por roda na transição (curva à esquerda: FR e RR são as externas):

| a_y | Fz_FL [N] | Fz_FR [N] | Fz_RL [N] | Fz_RR [N] | Faixa do pneu |
|---|---|---|---|---|---|
| 1,50 g (última linha válida) | 268,0 | 1415,7 | 315,0 | 1506,2 | [100, 1521] N |
| 1,55 g (primeira linha fora) | 248,8 | 1434,8 | 295,1 | 1526,0 | [100, 1521] N |

Causa: Fz_RR = 1526,0 N passa de FZMAX = 1521 N.
A roda que sai da faixa é uma roda **externa**, por excesso de carga. A roda interna mais leve tem 248,8 N nessa linha, acima de FZMIN = 100 N.

**Correção do plano.** O "Risco conhecido" do plano previa que a roda interna cairia abaixo de FZMIN antes de o eixo saturar (medido no veículo de teste de `tests/test_suspension_model.py`). No caso da planilha viva a causa é outra: RR (externa) passa de FZMAX.

Fração da capacidade usada por eixo na última linha válida (1,50 g), req/cap. Indica qual eixo está mais perto do limite, sem extrapolar o pneu. **Não é veredito.**

| Eixo | Força exigida [N] | Capacidade [N] | req/cap |
|---|---|---|---|
| Dianteiro | 2255,5 | 4211,7 | 53,6 % |
| Traseiro | 2401,8 | 4528,1 | 53,0 % |

Linhas da grade até a primeira linha fora da faixa (capacidade = máximo de Fy do eixo na grade de α):

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
| 1,55 | 249 | 1435 | 295 | 1526 | 2331 | 4199 | 2482 | — | Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] |

### Decisão pendente do usuário: política da faixa do pneu ("Risco conhecido", item c)

O plano deixou para o usuário como tratar uma roda fora da faixa de carga do pneu. As opções escritas no plano são: (1) Fy = 0 só quando Fz ≤ 0 (descolamento, que é física e não extrapolação) e N/A entre 0 e FZMIN; (2) manter o N/A. Esta decisão não foi tomada neste incremento.

Com os números acima, a opção (1) não muda o resultado do caso da planilha: ela trata a roda interna com pouca carga, e aqui a análise para porque a roda externa passa de FZMAX. Qualquer política que permita seguir além desse ponto teria de dizer o que fazer acima de FZMAX, o que seria extrapolar o pneu; a decisão continua sendo do usuário.

### Nota sobre a resolução da grade de a_y

Cenário do TC-EQ-011 de `tests/test_equilibrio.py`, recalculado aqui: veículo de teste simétrico (`veiculo_simetrico`, NÃO é setup real) com LMUY = 0,45 (escala só de teste, não é pneu).

| λ_f | Passo [g] | a_y sat. F | a_y sat. R | Diferença | Veredito |
|---|---|---|---|---|---|
| 0,5 | 0,05 | 1,1715 g | 1,1715 g | 0,0000 g | NEUTRO |
| 0,5 | 0,01 | 1,1715 g | 1,1715 g | 0,0000 g | NEUTRO |
| 0,7 | 0,05 | 1,1490 g | 1,1889 g | 0,0399 g | NEUTRO |
| 0,7 | 0,01 | 1,1490 g | 1,1889 g | 0,0399 g | PUSH |

De λ_f = 0,5 para 0,7 (passo 0,01 g), a saturação dianteira muda -0,0225 g e a traseira 0,0174 g; a diferença entre os eixos fica em 0,0399 g. Com o passo padrão de 0,05 g, uma diferença menor que o passo dá NEUTRO (critério |S_f − S_r| < passo de `analise_par`). O passo padrão não separa um efeito desse tamanho.

## 4. Robustez ao pneu: varredura exploratória (EDR-055)

Fatores λ do PAC2002 multiplicados pelos valores de `data/varredura_pneu_exploratoria.json`: LFZO × 0,8, 1,0, 1,2; LMUY × 0,8, 1,0, 1,2; LKY × 0,8, 1,0, 1,2 (27 combinações). Rótulo: "○ Arbitrário / demonstrativo" (valores exploratórios; não são faixa do pneu (EDR-022)). Os fatores não alteram FZMIN/FZMAX. Tempo do Python para as 27 análises: 1,0 s.

| LFZO | LMUY | LKY | Veredito | a_y_lim | Primeira a_y fora da faixa | req/cap F | req/cap R |
|---|---|---|---|---|---|---|---|
| 0,8 | 0,8 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 69,0 % | 68,5 % |
| 0,8 | 0,8 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 69,0 % | 68,5 % |
| 0,8 | 0,8 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 69,0 % | 68,5 % |
| 0,8 | 1,0 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 55,2 % | 54,8 % |
| 0,8 | 1,0 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 55,2 % | 54,8 % |
| 0,8 | 1,0 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 55,2 % | 54,8 % |
| 0,8 | 1,2 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 46,0 % | 45,7 % |
| 0,8 | 1,2 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 46,0 % | 45,7 % |
| 0,8 | 1,2 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 46,0 % | 45,7 % |
| 1,0 | 0,8 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 66,9 % | 66,3 % |
| 1,0 | 0,8 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 66,9 % | 66,3 % |
| 1,0 | 0,8 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 66,9 % | 66,3 % |
| 1,0 | 1,0 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 53,6 % | 53,0 % |
| 1,0 | 1,0 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 53,6 % | 53,0 % |
| 1,0 | 1,0 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 53,5 % | 53,0 % |
| 1,0 | 1,2 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 44,6 % | 44,2 % |
| 1,0 | 1,2 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 44,6 % | 44,2 % |
| 1,0 | 1,2 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 44,6 % | 44,2 % |
| 1,2 | 0,8 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 65,7 % | 64,9 % |
| 1,2 | 0,8 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 65,6 % | 64,9 % |
| 1,2 | 0,8 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 65,6 % | 64,9 % |
| 1,2 | 1,0 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 52,5 % | 51,9 % |
| 1,2 | 1,0 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 52,5 % | 51,9 % |
| 1,2 | 1,0 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 52,5 % | 51,9 % |
| 1,2 | 1,2 | 0,8 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 43,8 % | 43,3 % |
| 1,2 | 1,2 | 1,0 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 43,8 % | 43,3 % |
| 1,2 | 1,2 | 1,2 | DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g | — | 1,55 g | 43,8 % | 43,3 % |

Contagem: N/A = 27.

Veredito robusto (`veredito_robusto`): **N/A** (N/A em toda a varredura).

Texto de exibição com a robustez (`texto_veredito`, pior origem ○ Arbitrário / demonstrativo): **DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g**

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

Conferência: o veredito e o motivo do caso `planilha_viva` no JSON **coincidem** com a análise deste relatório (N/A; Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g).

## 6. Vai ou não vai: os números

Não há limiar registrado para decidir (spec §9, item 10: limite de desempenho só por decisão registrada). Os números abaixo não são veredito de viabilidade.

- Veredito nominal do caso da planilha: DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g
- Veredito com a varredura (27 combinações): DEMONSTRATIVO · N/A: Fz_RR = 1526.0 N fora da faixa do pneu [FZMIN, FZMAX] em a_y = 1.55 g (veredito robusto: N/A; nota: N/A em toda a varredura)
- Primeira a_y fora da faixa do pneu: 1,55 g; Fz_RR = 1526,0 N > FZMAX
- req/cap em 1,50 g: dianteiro 53,6 %, traseiro 53,0 %
- Recálculo do protótipo (excel): 0,45 a 0,59 s por caso; 4677 células de fórmula; 0 erros; diferença relativa máxima da capacidade 4.2e-16
- Recálculo do protótipo (libreoffice): 4,29 a 4,32 s por caso; 4677 células de fórmula; 0 erros; diferença relativa máxima da capacidade 3.6e-15
- Casos aprovados no experimento: 8 de 8
- Estimativa linear, **não medida**: a varredura de 27 combinações em fórmulas teria da ordem de 27 × 4677 = 126279 células de fórmula.
- Varredura no Python: 1,0 s para 27 análises

### Recomendação (não é decisão)

O que os números sugerem, para o usuário decidir:

1. A análise de par cabe em fórmulas nos dois motores: as fórmulas reproduziram o Python em todos os casos, com 0 erros. O recálculo do protótipo levou cerca de 0,6 s no Excel e 4,3 s no LibreOffice. Se esse tempo é aceitável é decisão da equipe.
2. A varredura em fórmulas multiplicaria o protótipo por 27 (estimativa acima, não medida). A spec (7.6, item 4) prevê a alternativa de o Python gerar o relatório da varredura e a planilha mostrar só o veredito nominal com o aviso "robustez ao pneu: ver relatório".
3. Com os dados demonstrativos atuais e o `.tir` provisório, o incremento 1 não produz veredito de equilíbrio no limite para o caso da planilha: o resultado é N/A no nominal e nas 27 combinações, porque uma roda sai da faixa de carga do pneu antes de qualquer eixo saturar. A fração req/cap na última linha válida mostra o quanto falta, sem dar o sinal de push ou loose. Antes de usar o veredito, o usuário precisa decidir a política da faixa do pneu (incluindo o lado de FZMAX, que a opção (1) do plano não cobre) ou usar o pneu do carro quando houver dado dele (hoje o .tir é o R25B provisório, EDR-022).

A decisão de seguir, ajustar ou parar é do usuário.

