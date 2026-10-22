# Incremento 4 (V4.1): custo de recálculo da tabela de troca da barra dianteira (portão)

Gerado por `uv run python -X utf8 tests/test_workbook_v4_1.py --medir`. É uma medição feita antes de a tabela existir; ela não implementa a tabela. Os valores de K_φF das cópias são de TESTE: só dão um custo, não um resultado do carro.

## O que foi medido e como

- Base: a V4.1 como gerada (V4.0 da tag `v4.0` + `aba_equilibrio.montar`), com as abas 16, 17, 18 e 19 (1073, 6826, 16058 e 2817 células com fórmula). A linha "0" é essa base, que já traz uma análise na grade pedida e outra na refinada (as do K_ARB dianteiro da 06).
- Uma linha da tabela de troca = uma análise de par completa com o K_ARB dianteiro trocado. Para medir, cada linha é uma cópia das abas 17 (e 18) dentro do mesmo arquivo (`M<i>_17`, `M<i>_18`), feita por `copy_worksheet` e reescrita no texto das fórmulas: os nomes do resumo da própria aba viram células locais, e o K_φF e o denominador da rolagem (16) passam a ler duas células próprias (H1 e I1), com K_φF·(1 + 0,05·i). Isso troca só a entrada da cadeia; o resto (cargas, termos do PAC2002, Fy por α, capacidade, bisseção da saturação) é o mesmo cálculo. A cópia i = 0 tem de reproduzir a original (conferência abaixo). `montar` não foi alterado.
- Variantes: P = grade pedida (17) por linha; R = pedida + refinada (17 + 18) por linha; RK = R + o K da 1ª linha do passo 1 (a linha de a_y = 0 do cálculo auxiliar da 19, 330 células com fórmula, lendo a cópia da 17; sem a tabela de 0 a 0,4 g). "Linhas" são linhas extras além da base; o total de análises é 1 + linhas.
- Motores: excel, libreoffice; 3 recálculos por arquivo (mín / média / máx, em segundos; LibreOffice com 3). O tempo do motor é abrir, recalcular tudo (CalculateFull no Excel, calculateAll no LibreOffice), gravar e fechar; o do LibreOffice inclui as duas partidas do programa. Erros = células com #VALUE!, #DIV/0! etc. depois do recálculo.
- No Excel, além disso: `CalculateFull` sozinho e o recálculo automático ao trocar o K_ARB dianteiro (06_SUSPENSION) numa cópia aberta, que é o que a equipe sentiria ao editar. O arquivo não é gravado.

## Resultados: excel

| Variante | Linhas extras | Análises pedida / refinada | Fórmulas | Erros | Motor mín / média / máx (s) | Δ média vs. base (s) | Δ por linha (s) |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 1 / 1 | 27161 | 0 | 1.2 / 3.8 / 7.3 | +0.0 | - |
| P1 | 1 | 2 / 1 | 33989 | 0 | 2.9 / 4.6 / 6.3 | +0.8 | 0.8 |
| P3 | 3 | 4 / 1 | 47645 | 0 | 3.4 / 4.7 / 7.0 | +0.9 | 0.3 |
| P5 | 5 | 6 / 1 | 61301 | 0 | 2.6 / 4.0 / 6.2 | +0.2 | 0.0 |
| R1 | 1 | 2 / 2 | 50049 | 0 | 2.7 / 3.8 / 5.3 | +0.0 | 0.0 |
| R3 | 3 | 4 / 4 | 95825 | 0 | 3.5 / 5.4 / 9.2 | +1.6 | 0.5 |
| R5 | 5 | 6 / 6 | 141601 | 0 | 4.0 / 7.2 / 13.0 | +3.4 | 0.7 |
| RK1 | 1 | 2 / 2 | 50378 | 0 | 2.2 / 3.7 / 6.3 | -0.1 | -0.1 |
| RK3 | 3 | 4 / 4 | 96812 | 0 | 3.9 / 6.1 / 10.1 | +2.3 | 0.8 |
| RK5 | 5 | 6 / 6 | 143246 | 0 | 4.0 / 10.1 / 16.3 | +6.3 | 1.3 |

## Resultados: libreoffice

| Variante | Linhas extras | Análises pedida / refinada | Fórmulas | Erros | Motor mín / média / máx (s) | Δ média vs. base (s) | Δ por linha (s) |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 1 / 1 | 27161 | 0 | 6.4 / 6.8 / 7.2 | +0.0 | - |
| P1 | 1 | 2 / 1 | 33989 | 0 | 6.5 / 7.7 / 9.6 | +0.9 | 0.9 |
| P3 | 3 | 4 / 1 | 47645 | 0 | 7.4 / 7.7 / 7.8 | +0.8 | 0.3 |
| P5 | 5 | 6 / 1 | 61301 | 0 | 7.1 / 7.8 / 8.2 | +1.0 | 0.2 |
| R1 | 1 | 2 / 2 | 50049 | 0 | 7.0 / 7.6 / 8.3 | +0.8 | 0.8 |
| R3 | 3 | 4 / 4 | 95825 | 0 | 9.3 / 9.4 / 9.6 | +2.6 | 0.9 |
| R5 | 5 | 6 / 6 | 141601 | 0 | 11.2 / 11.3 / 11.6 | +4.5 | 0.9 |
| RK1 | 1 | 2 / 2 | 50378 | 0 | 7.2 / 7.6 / 8.4 | +0.8 | 0.8 |
| RK3 | 3 | 4 / 4 | 96812 | 0 | 9.6 / 9.9 / 10.1 | +3.1 | 1.0 |
| RK5 | 5 | 6 / 6 | 143246 | 0 | 12.4 / 12.6 / 13.0 | +5.8 | 1.2 |

## Excel: CalculateFull sozinho e troca de uma entrada

| Variante | CalculateFull mín / média / máx (s) | Troca do K_ARB dianteiro, recálculo automático, mín / média / máx (s) |
|---|---|---|
| 0 | 0.0 / 0.1 / 0.2 | 0.1 / 0.1 / 0.1 |
| P1 | 0.0 / 0.1 / 0.2 | 0.1 / 0.1 / 0.1 |
| P3 | 0.0 / 0.1 / 0.1 | 0.1 / 0.1 / 0.2 |
| P5 | 0.1 / 0.1 / 0.2 | 0.1 / 0.1 / 0.1 |
| R1 | 0.0 / 0.1 / 0.2 | 0.1 / 0.2 / 0.2 |
| R3 | 0.2 / 0.3 / 0.5 | 0.3 / 0.3 / 0.4 |
| R5 | 0.2 / 0.4 / 0.6 | 0.4 / 0.5 / 0.7 |
| RK1 | 0.1 / 0.1 / 0.1 | 0.1 / 0.2 / 0.2 |
| RK3 | 0.2 / 0.2 / 0.4 | 0.3 / 0.3 / 0.3 |
| RK5 | 0.2 / 0.2 / 0.3 | 0.4 / 0.4 / 0.6 |

## Conferência das cópias

Com K_φF × 1 (i = 0), a cópia tem de dar o mesmo que a aba original (resumo da 17 e da 18, e o K total da linha de a_y = 0 da 19). Arquivo RK1, depois do recálculo de cada motor:

- excel: 21 de 21 itens iguais
- libreoffice: 21 de 21 itens iguais

Células da linha de a_y = 0 da 19 que citam outra linha e por isso não foram copiadas: ['LR24'].

## Leitura dos números (sugestão, não limiar)

- A coluna "Motor" inclui abrir e gravar o arquivo, que domina e oscila de uma execução para outra (no Excel, a base foi de 1,2 a 7,3 s). O recálculo em si, o que a equipe sentiria ao editar, está na tabela do `CalculateFull` e da troca do K_ARB: nesta medição ficou abaixo de 1 s em todas as variantes, inclusive 5 linhas com pedida + refinada (cerca de 140 mil fórmulas).
- O custo cresce aproximadamente com o número de linhas e com o tamanho da grade (a refinada pesa cerca de 2,4 vezes a pedida em células). Nenhuma variante deu erro de fórmula.
- Sugestão: com esses números, o tempo de recálculo parece não ser o fator limitante até 5 linhas; o tamanho da tabela pode ser decidido pelo que ela precisa mostrar. Sem limiar registrado, isso não decide sozinho.

## Limites desta medição

- Um computador, um Excel e um LibreOffice (os da máquina do projeto); o tempo da equipe depende do computador de cada um.
- As cópias levam também as 10 células de pior origem (coluna E, linhas 4 a 13) de cada aba, que uma linha real talvez não precise; é pouco perto da grade.
- A cópia da 19 cobre só o K da 1ª linha (parcelas em a_y = 0). Os ângulos de Richardson (kI) e a tabela de 0 a 0,4 g não entram.
- Não há limiar de tempo registrado (spec §9, item 10): o tempo, sozinho, não decide o tamanho.

## Decisão pedida ao usuário

1. Quantos valores de K_ARB dianteiro a tabela de troca deve ter? A grade é de exibição, rotulada, e não uma meta.
2. Cada linha deve também medir a resolução (rodar a grade refinada, variantes R e RK), ou basta a grade pedida (P)?

A resposta entra no EDR-060. A Task 5 (a tabela) só começa depois dela.
