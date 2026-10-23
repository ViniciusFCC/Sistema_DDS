# Incremento 4 (V4.1): custo de recálculo da tabela de troca da barra dianteira (portão)

Gerado por `uv run python -X utf8 tests/test_workbook_v4_1.py --medir`. É uma medição feita antes de a tabela existir; ela não implementa a tabela. Os valores de K_φF das cópias são de TESTE: só dão um custo, não um resultado do carro.

## O que foi medido e como

- Base: a V4.1 como gerada (V4.0 da tag `v4.0` + `aba_equilibrio.montar`), com as abas 16, 17, 18 e 19 (1073, 6826, 16058 e 2817 células com fórmula). A linha "0" é essa base, que já traz uma análise na grade pedida e outra na refinada (as do K_ARB dianteiro da 06).
- Uma linha da tabela de troca = uma análise de par completa com o K_ARB dianteiro trocado. Para medir, cada linha é uma cópia das abas 17 (e 18) dentro do mesmo arquivo (`M<i>_17`, `M<i>_18`), feita por `copy_worksheet` e reescrita no texto das fórmulas: os nomes do resumo da própria aba viram células locais, e o K_φF e o denominador da rolagem (16) passam a ler duas células próprias (H1 e I1), com K_φF·(1 + 0,05·i). Isso troca só a entrada da cadeia; o resto (cargas, termos do PAC2002, Fy por α, capacidade, bisseção da saturação) é o mesmo cálculo. A cópia i = 0 tem de reproduzir a original, e a cópia i ≥ 1 tem de diferir dela (conferência abaixo). `montar` não foi alterado.
- Variantes: P = grade pedida (17) por linha; R = pedida + refinada (17 + 18) por linha; RK = R + o K da 1ª linha do passo 1 (a linha de a_y = 0 do cálculo auxiliar da 19, 330 células com fórmula, lendo a cópia da 17; sem a tabela de 0 a 0,4 g). "Linhas" são linhas extras além da base; o total de análises é 1 + linhas.
- Motores: excel, libreoffice; 3 recálculos por arquivo (mín / média / máx, em segundos; LibreOffice com 3). O tempo do motor é abrir, recalcular tudo (CalculateFull no Excel, calculateAll no LibreOffice), gravar e fechar; o do LibreOffice inclui as duas partidas do programa. Erros = células com #VALUE!, #DIV/0! etc. depois do recálculo.
- No Excel, além disso: `CalculateFull` sozinho e o recálculo automático ao trocar o K_ARB dianteiro (06_SUSPENSION) numa cópia aberta, que é o que a equipe sentiria ao editar. O arquivo não é gravado.

## Resultados: excel

| Variante | Linhas extras | Análises pedida / refinada | Fórmulas | Erros | Motor mín / média / máx (s) | Δ média vs. base (s) | Δ por linha (s) |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 1 / 1 | 27161 | 0 | 1.3 / 3.3 / 4.9 | +0.0 | - |
| P1 | 1 | 2 / 1 | 33989 | 0 | 1.3 / 2.0 / 2.9 | -1.3 | -1.3 |
| P3 | 3 | 4 / 1 | 47645 | 0 | 1.5 / 2.1 / 3.2 | -1.2 | -0.4 |
| P5 | 5 | 6 / 1 | 61301 | 0 | 1.6 / 2.6 / 4.4 | -0.7 | -0.1 |
| R1 | 1 | 2 / 2 | 50049 | 0 | 1.9 / 2.8 / 3.4 | -0.5 | -0.5 |
| R3 | 3 | 4 / 4 | 95825 | 0 | 2.4 / 3.9 / 6.1 | +0.6 | 0.2 |
| R5 | 5 | 6 / 6 | 141601 | 0 | 2.9 / 5.1 / 9.0 | +1.7 | 0.3 |
| RK1 | 1 | 2 / 2 | 50378 | 0 | 1.6 / 2.4 / 3.7 | -0.9 | -0.9 |
| RK3 | 3 | 4 / 4 | 96812 | 0 | 2.9 / 4.2 / 6.6 | +0.9 | 0.3 |
| RK5 | 5 | 6 / 6 | 143246 | 0 | 3.3 / 5.3 / 9.1 | +2.0 | 0.4 |

No Excel, a diferença do tempo de motor em relação à base (e por isso a coluna "Δ por linha") fica dentro da variação da própria base entre repetições; não é interpretável como custo por linha. Use a tabela do CalculateFull abaixo.

## Resultados: libreoffice

| Variante | Linhas extras | Análises pedida / refinada | Fórmulas | Erros | Motor mín / média / máx (s) | Δ média vs. base (s) | Δ por linha (s) |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 1 / 1 | 27161 | 0 | 6.1 / 6.3 / 6.8 | +0.0 | - |
| P1 | 1 | 2 / 1 | 33989 | 0 | 6.7 / 6.7 / 6.7 | +0.3 | 0.3 |
| P3 | 3 | 4 / 1 | 47645 | 0 | 6.7 / 7.2 / 7.5 | +0.8 | 0.3 |
| P5 | 5 | 6 / 1 | 61301 | 0 | 7.2 / 7.4 / 7.6 | +1.1 | 0.2 |
| R1 | 1 | 2 / 2 | 50049 | 0 | 7.4 / 7.6 / 7.9 | +1.3 | 1.3 |
| R3 | 3 | 4 / 4 | 95825 | 0 | 9.4 / 9.5 / 9.6 | +3.1 | 1.0 |
| R5 | 5 | 6 / 6 | 141601 | 0 | 11.0 / 11.7 / 12.1 | +5.4 | 1.1 |
| RK1 | 1 | 2 / 2 | 50378 | 0 | 7.2 / 7.4 / 7.8 | +1.1 | 1.1 |
| RK3 | 3 | 4 / 4 | 96812 | 0 | 9.5 / 9.6 / 9.9 | +3.3 | 1.1 |
| RK5 | 5 | 6 / 6 | 143246 | 0 | 11.1 / 11.4 / 11.8 | +5.0 | 1.0 |

## Excel: CalculateFull sozinho e troca de uma entrada

| Variante | CalculateFull mín / média / máx (s) | Troca do K_ARB dianteiro, recálculo automático, mín / média / máx (s) |
|---|---|---|
| 0 | 0.0 / 0.0 / 0.0 | 0.1 / 0.1 / 0.1 |
| P1 | 0.0 / 0.0 / 0.0 | 0.1 / 0.1 / 0.1 |
| P3 | 0.0 / 0.1 / 0.1 | 0.1 / 0.1 / 0.1 |
| P5 | 0.1 / 0.1 / 0.1 | 0.1 / 0.1 / 0.1 |
| R1 | 0.0 / 0.0 / 0.0 | 0.1 / 0.1 / 0.1 |
| R3 | 0.2 / 0.2 / 0.2 | 0.2 / 0.3 / 0.3 |
| R5 | 0.1 / 0.2 / 0.2 | 0.4 / 0.4 / 0.4 |
| RK1 | 0.0 / 0.1 / 0.1 | 0.1 / 0.1 / 0.1 |
| RK3 | 0.1 / 0.2 / 0.2 | 0.2 / 0.2 / 0.3 |
| RK5 | 0.2 / 0.3 / 0.3 | 0.3 / 0.4 / 0.4 |

## Conferência das cópias

Arquivo RK3, depois do recálculo de cada motor. Com K_φF × 1 (i = 0), a cópia tem de dar o mesmo que a aba original (resumo da 17 e da 18, e o K total da linha de a_y = 0 da 19; células vazias dos dois lados não contam como iguais). Com i ≥ 1, a cópia tem de diferir da original: é a prova de que a troca de K_φF pegou.

- excel, i = 0: 21 de 21 itens iguais
- excel, i = 1 (K_φF × 1.05): K total (LH24) original -0.0002426155247456089, cópia -0.00023923791185836074; Fz_FL da 17 em a_y = 1,0 g (H44) original 459.25949491782916, cópia 453.16794174296234. Difere nos dois itens (K total e carga de uma roda na grade): a troca pegou.
- excel, i = 2 (K_φF × 1.10): K total (LH24) original -0.0002426155247456089, cópia -0.00023603801019163662; Fz_FL da 17 em a_y = 1,0 g (H44) original 459.25949491782916, cópia 447.3968922490428. Difere nos dois itens (K total e carga de uma roda na grade): a troca pegou.
- libreoffice, i = 0: 21 de 21 itens iguais
- libreoffice, i = 1 (K_φF × 1.05): K total (LH24) original -0.000242615524740981, cópia -0.00023923791185383; Fz_FL da 17 em a_y = 1,0 g (H44) original 459.259494917829, cópia 453.167941742962. Difere nos dois itens (K total e carga de uma roda na grade): a troca pegou.
- libreoffice, i = 2 (K_φF × 1.10): K total (LH24) original -0.000242615524740981, cópia -0.000236038010188519; Fz_FL da 17 em a_y = 1,0 g (H44) original 459.259494917829, cópia 447.396892249043. Difere nos dois itens (K total e carga de uma roda na grade): a troca pegou.

Células da linha de a_y = 0 da 19 que citam outra linha e por isso não foram copiadas: ['LR24'].

## Leitura dos números

Fatos desta execução; não são limiar nem recomendação (spec §9, item 10).

- Maior recálculo medido no Excel (máximo das repetições): 0.4 s (troca do K_ARB dianteiro, variante RK5); CalculateFull máximo 0.3 s (variante RK5), troca do K_ARB máxima 0.4 s (variante RK5).
- Excel, variante P, médias com 1, 3 e 5 linhas: CalculateFull 0.03 / 0.05 / 0.10 s; troca do K_ARB 0.08 / 0.10 / 0.11 s (não decresce com as linhas).
- Excel, variante R, médias com 1, 3 e 5 linhas: CalculateFull 0.04 / 0.18 / 0.17 s; troca do K_ARB 0.09 / 0.27 / 0.38 s (não cresce de forma monótona com as linhas).
- Excel, variante RK, médias com 1, 3 e 5 linhas: CalculateFull 0.06 / 0.15 / 0.26 s; troca do K_ARB 0.13 / 0.24 / 0.37 s (não decresce com as linhas).
- Tempo de motor do Excel (abrir, recalcular, gravar): a base variou de 1.3 a 4.9 s entre as 3 repetições, e a diferença das médias das variantes em relação à base ficou entre -1.3 e +2.0 s; essa diferença está dentro da variação da própria base, então o tempo de motor do Excel não separa as variantes.
- LibreOffice (tempo total, que inclui as duas partidas do programa): maior tempo medido 12.1 s (variante R5); base 6.3 s; nas variantes R e RK a diferença por linha extra ficou entre 1.0 e 1.3 s.
- Tamanho: a 18 tem 16058 células com fórmula e a 17 tem 6826 (razão 2.4). A variante com mais fórmulas (143246) ficou sem erro de fórmula: 0 erros somados em todas as medições.

## Limites desta medição

- Um computador, um Excel e um LibreOffice (os da máquina do projeto); o tempo da equipe depende do computador de cada um.
- As cópias levam também as 10 células de pior origem (coluna E, linhas 4 a 13) de cada aba, que uma linha real talvez não precise; é pouco perto da grade.
- A cópia da 19 cobre só o K da 1ª linha (parcelas em a_y = 0). Os ângulos de Richardson (kI) e a tabela de 0 a 0,4 g não entram.
- Não há limiar de tempo registrado (spec §9, item 10): o tempo, sozinho, não decide o tamanho.

## Decisão pedida ao usuário

1. Quantos valores de K_ARB dianteiro a tabela de troca deve ter? A grade é de exibição, rotulada, e não uma meta. O valor digitado na 06 (×1) é a base e conta como um deles; o total de análises é 1 + linhas extras.
2. Cada linha deve também medir a resolução (rodar a grade refinada, variantes R e RK), ou basta a grade pedida (P)?

A resposta entra no EDR-060. A Task 5 (a tabela) só começa depois dela.

## Decisão do usuário (2026-10-22)

- 5 valores de K_ARB dianteiro: ×0,5; ×0,75; ×1; ×1,5; ×2 do valor digitado na 06 (o ×1 é a base). A grade é de exibição, rotulada, e não uma meta.
- Cada linha mede a resolução e o K da 1ª linha (variante RK), porque o EDR-056 só admite NEUTRO dentro da resolução medida (ruling do controlador).
