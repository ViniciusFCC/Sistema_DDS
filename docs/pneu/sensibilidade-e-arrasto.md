# Sensibilidade do pneu e arrasto induzido (pneu-1)

**DEMONSTRATIVO.** O caso é o da planilha: dados de outro carro (T09/E03, TX/E05) e o `.tir` do R25B do TTC no lugar do R60A. Não é recomendação para o T11. Decisões registradas no EDR-075 (`docs/Engineering_Decision_Register.md`).

Rótulos obrigatórios (spec §9), válidos para tudo o que está abaixo:

- caso de outro carro (T09/E03), demonstrativo, não o T11; valores editados marcados;
- pneu R25B do TTC no lugar do R60A; μ absoluto do TTC não transferível;
- pressão de ensaio ≠ pressão fria nem quente (a confirmar);
- amplitudes de λ exploratórias (EDR-055), não faixa do pneu;
- banda heurística, não intervalo de confiança;
- Validation = NOT_VALIDATED; VERIFIED não é validado;
- Fx·κ fora (sem fonte); traçado do enduro a confirmar;
- o `fator_neutro` do caso (24_CURVA B34, 4/3 na V4.4) difere do 1,0 do `relatorio_pressao`: a regra do NEUTRO não é a daquele relatório.

Dos valores do caso, só `R_m` é "● Dado do T11". Todos os outros são de outro carro, estimativas ou valores demonstrativos.

## 1. O que este estudo responde

O roteiro do modelo de pneu (`roteiro-modelo-de-pneu.md`) lista 18 degraus de melhoria. O item 16 pergunta quais deles mudam alguma decisão do carro. O item 15 pergunta quanto pesa o arrasto induzido pela deriva. O estudo responde as duas perguntas em Python, sobre um caso em arquivo (`data/casos/caso_pneu1_demonstrativo.json`) que a equipe pode editar. Ele não mexe na planilha.

## 2. Resposta curta

No caso demonstrativo, **nenhum degrau pôde ser avaliado**. A causa é uma só: o carro não chega ao limite de aderência até 2 g. Das 7 corridas do tornado de λ, 6 dão `a_y limite = N/A`, e nas 8 corridas da pressão todas dão N/A. Sem a_y limite, não há veredito (frente ou traseira saindo primeiro), e os dois critérios da regra de "muda decisão" ficam sem base.

Isso não quer dizer "o pneu não importa", e sim "este caso não permite dizer". Na tabela por degrau, a palavra para isso é **não avaliado**. Ela é diferente de **não** (avaliado, e nada mudou).

Para o estudo dar uma resposta, falta um caso em que algum eixo sature antes de 2 g. Isso depende de dados do T11: massa, posição do CG, rigidezes, balanço aerodinâmico, o traçado de curva que interessa e o pneu real. O `R_m` já é do T11; os demais campos ainda são de outro carro. Quando a equipe editar o caso, basta rodar a ferramenta de novo (seção 8).

## 3. Como a decisão é medida

Um fator "muda decisão" se, dentro da faixa dele, (1) o veredito não fica com um sinal só, ou (2) o a_y limite ou o Cα sai da banda heurística do EDR-071. A banda é uma faixa de trabalho, não um intervalo de confiança.

- **λ (LMUY, LFZO, LKY):** vale o critério 1, pela robustez da combinação das 27 combinações (3 × 3 × 3) em cada pressão. Não existe banda para λ; a variação do a_y limite no tornado aparece como tamanho de efeito.
- **Pressão:** critério 1 (o veredito difere entre as quatro pressões) e critério 2 (a escolha de pressão do EDR-071 distingue pressões em a_y limite ou em Cα). Só conta como "distingue" a pressão decidível, com banda medida, que fica fora do conjunto de indistinguíveis. A pressão não resolvida (8 e 14 psi, com banda só como limite inferior) dá "não avaliado".
- **KT (rigidez vertical):** critério 1 (o veredito difere entre a variante a, KT do caso, e a variante b, KT do perfil) e critério 2 (a diferença de a_y limite entre a e b passa da banda).

Cada decisão tem um de quatro estados: **sim** (algum critério deu sim), **não** (todos foram avaliados e deram não), **não avaliado** (nenhum deu sim e algum ficou sem avaliação) e **não medido aqui** (degrau fora do estudo, spec §6.1).

**O que "não muda" significa.** Quando a ferramenta der "não" para um fator, a frase é: não muda neste caso demonstrativo, nesta faixa exploratória. Não é "não importa para o T11". Neste relatório nenhum degrau deu "não": os que entram no estudo deram "não avaliado".

## 4. Valores usados

A origem de cada valor segue a lista Origens da planilha. Valores editados com `--set` aparecem como "✎ Editado pelo usuário"; nenhum foi editado neste relatório. Os cinco últimos valores (`m`, `a`, `b`, `huF`, `huR`) são recalculados pela regra das células da V4.4, indicada na última coluna.

| chave | valor | unidade | origem | editado | calculado por |
|---|---|---|---|---|---|
| m_sem_piloto_kg | 248,5000 | kg | ◐ Dado de outro carro (TX, T09) | não |  |
| m_piloto_kg | 68 | kg | ○ Estimativa | não |  |
| h_cg_m | 0,3150 | m | ◐ Dado de outro carro (TX, T09) | não |  |
| L_m | 1,5940 | m | ◐ Dado de outro carro (TX, T09) | não |  |
| tF_m | 1,2770 | m | ◐ Dado de outro carro (TX, T09) | não |  |
| tR_m | 1,2710 | m | ◐ Dado de outro carro (TX, T09) | não |  |
| f_dianteira | 0,4843 | - | ◐ Dado de outro carro (TX, T09) | não |  |
| muF_kg | 15 | kg | ○ Arbitrário / demonstrativo | não |  |
| muR_kg | 18 | kg | ○ Arbitrário / demonstrativo | não |  |
| d_pneu_F_pol | 20 | in | ◐ Dado de outro carro (TX, T09) | não |  |
| d_pneu_R_pol | 20 | in | ◐ Dado de outro carro (TX, T09) | não |  |
| razao_hns_F | 1 | - | ○ Estimativa | não |  |
| razao_hns_R | 1 | - | ○ Estimativa | não |  |
| KsF_N_m | 49909,2400 | N/m | ◐ Dado de outro carro (TX, T09) | não |  |
| MRF | 1,7600 | - | ◐ Dado de outro carro (TX, T09) | não |  |
| KarbF_Nm_rad | 5012,3200 | N*m/rad | ◐ Dado de outro carro (TX, T09) | não |  |
| zF_m | 0,0675 | m | ◐ Dado de outro carro (TX, T09) | não |  |
| KTF_N_m | 120312 | N/m | ◐ Provisório (.tir TTC) | não |  |
| KsR_N_m | 57052,2200 | N/m | ◐ Dado de outro carro (TX, T09) | não |  |
| MRR | 1,7600 | - | ◐ Dado de outro carro (TX, T09) | não |  |
| KarbR_Nm_rad | 10,7800 | N*m/rad | ◐ Dado de outro carro (TX, T09) | não |  |
| zR_m | 0,1100 | m | ◐ Dado de outro carro (TX, T09) | não |  |
| KTR_N_m | 120312 | N/m | ◐ Provisório (.tir TTC) | não |  |
| DF_N | 400 | N | ○ Estimativa | não |  |
| bal_dianteira | 0,4500 | - | ○ Estimativa | não |  |
| dgF_grau_mm | -0,6000 | deg/mm | ○ Arbitrário / demonstrativo | não |  |
| dgR_grau_mm | -0,5000 | deg/mm | ○ Arbitrário / demonstrativo | não |  |
| epsF_rad_rad | 0 | °/° | ○ Arbitrário / demonstrativo | não |  |
| epsR_rad_rad | 0 | °/° | ○ Arbitrário / demonstrativo | não |  |
| gsFL_grau | -1,5000 | ° | ○ Arbitrário / demonstrativo | não |  |
| gsFR_grau | -1,5000 | ° | ○ Arbitrário / demonstrativo | não |  |
| gsRL_grau | -1 | ° | ○ Arbitrário / demonstrativo | não |  |
| gsRR_grau | -1 | ° | ○ Arbitrário / demonstrativo | não |  |
| eixos_tir | ISO_TYDEX | - | ◐ Provisório (.tir TTC) | não |  |
| sentido | Esquerda | - | ? A confirmar | não |  |
| toeFL_grau | 0 | ° | ? A confirmar | não |  |
| toeFR_grau | 0 | ° | ? A confirmar | não |  |
| toeRL_grau | 0 | ° | ? A confirmar | não |  |
| toeRR_grau | 0 | ° | ? A confirmar | não |  |
| R_m | 9,1250 | m | ● Dado do T11 | não |  |
| cg_lateral_m | 0 | m | ? A confirmar | não |  |
| cza_m2 | — | m² | ? A confirmar | não |  |
| rho_kg_m3 | — | kg/m³ | ? A confirmar | não |  |
| cda_m2 | — | m² | ? A confirmar | não |  |
| crr | — | - | ? A confirmar | não |  |
| h2 | 0 | 0/1 | ? A confirmar | não |  |
| h3 | 0 | 0/1 | ? A confirmar | não |  |
| h7 | 0 | 0/1 | ? A confirmar | não |  |
| h8 | 0 | 0/1 | ? A confirmar | não |  |
| h9 | 0 | 0/1 | ? A confirmar | não |  |
| h2v | 1 | 0/1 | ? A confirmar | não |  |
| h9v | 1 | 0/1 | ? A confirmar | não |  |
| fator_neutro | 1,3333 | - | ○ Estimativa | não |  |
| ackermann_pct | — | % | ? A confirmar | não |  |
| crr_referencia | — | - | ? A confirmar | não |  |
| lambda_LFZO | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LCX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LMUX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LEX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LKX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LHX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LVX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LGAX | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LCY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LMUY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LEY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LKY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LHY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LVY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LGAY | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| lambda_LKYG | 1 | - | ◐ Provisório (.tir TTC) | não |  |
| m | 316,5000 | kg | ○ Estimativa | não | 05_VEHICLE B4 |
| a | 0,8220 | m | ◐ Dado de outro carro (TX, T09) | não | 05_VEHICLE B9 |
| b | 0,7720 | m | ◐ Dado de outro carro (TX, T09) | não | 05_VEHICLE B10 |
| huF | 0,2540 | m | ○ Estimativa | não | 05_VEHICLE B16 |
| huR | 0,2540 | m | ○ Estimativa | não | 05_VEHICLE B17 |

## 5. Sensibilidade ao λ, à pressão e ao KT

Os nós de pressão (8, 10, 12 e 14 psi) são as pressões nominais gravadas nos `.tir` do TTC (7,999992, 10,000062, 11,999987 e 14,000058 psi), que não são inteiras; nas tabelas aparecem arredondadas a 0,1 psi. Os pontos entre eles (8,5; 9,0; ...) são interpolados e marcados como tal na saída da ferramenta.

### 5.1 Tornado de λ (12 psi, KT variante a)

Cada linha muda um fator por vez, nas amplitudes exploratórias do EDR-055 (0,8 e 1,2). A única corrida que chega a um a_y limite é a de LMUY × 0,8 (1,949 g, veredito LOOSE). K é o gradiente de subesterço; C_f e C_r são as rigidezes de deriva dianteira e traseira.

| corrida | pressão (psi) | KT | fatores λ | a_y limite (g) | veredito | K (°/g) | C_f (N/rad) | C_r (N/rad) | observação |
|---|---|---|---|---|---|---|---|---|---|
| 12,0 psi, variante a | 12,0 | a | — | N/A | N/A | -0,136 | 87685 | 94101 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante a; LFZO × 0,8 | 12,0 | a | LFZO=0,80 | N/A | N/A | -0,150 | 80109 | 84865 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante a; LFZO × 1,2 | 12,0 | a | LFZO=1,20 | N/A | N/A | -0,128 | 92403 | 99984 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante a; LMUY × 0,8 | 12,0 | a | LMUY=0,80 | 1,949 | LOOSE | -0,149 | 87170 | 93804 |  |
| 12,0 psi, variante a; LMUY × 1,2 | 12,0 | a | LMUY=1,20 | N/A | N/A | -0,123 | 87966 | 94262 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante a; LKY × 0,8 | 12,0 | a | LKY=0,80 | N/A | N/A | -0,117 | 70413 | 75433 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante a; LKY × 1,2 | 12,0 | a | LKY=1,20 | N/A | N/A | -0,149 | 104738 | 112642 | não avaliado: o carro não chega ao limite até 2,0 g |

### 5.2 Pressão (a: KT do caso; b: KT do perfil)

| corrida | pressão (psi) | KT | fatores λ | a_y limite (g) | veredito | K (°/g) | C_f (N/rad) | C_r (N/rad) | observação |
|---|---|---|---|---|---|---|---|---|---|
| 8,0 psi, variante a | 8,0 | a | — | N/A | N/A | -0,193 | 83844 | 87550 | não avaliado: o carro não chega ao limite até 2,0 g |
| 10,0 psi, variante a | 10,0 | a | — | N/A | N/A | -0,153 | 90260 | 96109 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante a | 12,0 | a | — | N/A | N/A | -0,136 | 87685 | 94101 | não avaliado: o carro não chega ao limite até 2,0 g |
| 14,0 psi, variante a | 14,0 | a | — | N/A | N/A | -0,117 | 81080 | 87329 | não avaliado: o carro não chega ao limite até 2,0 g; α na borda da grade |
| 8,0 psi, variante b | 8,0 | b | — | N/A | N/A | -0,199 | 83844 | 87550 | não avaliado: o carro não chega ao limite até 2,0 g |
| 10,0 psi, variante b | 10,0 | b | — | N/A | N/A | -0,155 | 90260 | 96109 | não avaliado: o carro não chega ao limite até 2,0 g |
| 12,0 psi, variante b | 12,0 | b | — | N/A | N/A | -0,136 | 87685 | 94101 | não avaliado: o carro não chega ao limite até 2,0 g |
| 14,0 psi, variante b | 14,0 | b | — | N/A | N/A | -0,117 | 81080 | 87329 | não avaliado: o carro não chega ao limite até 2,0 g; α na borda da grade |

A 14 psi o α fica na borda da grade, e a ferramenta avisa na coluna de observação.


### 5.3 Combinação de λ (robustez por pressão)

Aqui entram as 27 combinações de LMUY, LFZO e LKY (0,8, 1,0 e 1,2 cada), conforme `data/varredura_pneu_exploratoria.json`. A robustez diz se o veredito se mantém em todas elas. Como o a_y limite é N/A em parte ou em toda a varredura, a resposta é NÃO CONCLUSIVO ou N/A, e não um veredito.

| pressão (psi) | robustez | motivo |
|---|---|---|
| 8,0 | NÃO CONCLUSIVO | N/A em parte da varredura (sem inversão de sinal) |
| 10,0 | NÃO CONCLUSIVO | N/A em parte da varredura (sem inversão de sinal) |
| 12,0 | NÃO CONCLUSIVO | N/A em parte da varredura (sem inversão de sinal) |
| 14,0 | N/A | N/A em toda a varredura |

- hipótese: a perda TTC→pista é a mesma em todas as pressões
- robustez no sentido esquerdo (a varredura de λ cobre só a curva à esquerda; o a_y_lim e o veredito vêm do pior dos dois sentidos)

O pneu por pressão (Cα, μ_y de pico e se há borda, nos 13 pontos de 8,0 a 14,0 psi, para os eixos F e R) está na seção 6 do `relatorio.md` gerado.

## 6. Arrasto induzido

D = Σ −F_y,i·sen α_i, somado roda a roda, em N (equivale a J/m, energia por distância percorrida). D/(m·g) é o mesmo valor como fração do peso. D/D_1ª ordem é a razão com a forma linearizada Σ F_y exigida·|α|, que o código já usa.

Fonte: Milliken & Milliken, RCVD, §2.9, p. 64 a 67 (D = F_x·cos α − F_y·sen α nas p. 64 e 65; bicicleta na Fig. 2.36, p. 67). Somar roda a roda, em vez de usar as duas rodas da bicicleta do Milliken, é escolha do Claude, não do livro. A resistência ao rolamento está a confirmar: sem Crr com fonte, o D sai como tamanho de efeito e não como decisão.

A grade vai de 0 a 2,00 g, porque o carro não satura antes disso. O ponto de 2,00 g é o último a_y resolvido.

| a_y (g) | α frente | α trás | D (N) | D/(m·g) | D/D_1ª ordem |
|---|---|---|---|---|---|
| 0,00 | 0,00° | 0,00° | 0,000 | 0,00000 | — |
| 0,10 | -0,02° | -0,03° | 0,141 | 0,00005 | 1,0000 |
| 0,20 | -0,04° | -0,07° | 0,575 | 0,00019 | 1,0000 |
| 0,30 | -0,06° | -0,11° | 1,384 | 0,00045 | 1,0000 |
| 0,40 | -0,12° | -0,15° | 2,967 | 0,00096 | 1,0000 |
| 0,50 | -0,20° | -0,21° | 5,516 | 0,00178 | 1,0000 |
| 0,60 | -0,28° | -0,30° | 9,525 | 0,00307 | 1,0000 |
| 0,70 | -0,38° | -0,40° | 14,954 | 0,00482 | 1,0000 |
| 0,80 | -0,51° | -0,52° | 22,320 | 0,00719 | 1,0000 |
| 0,90 | -0,65° | -0,66° | 31,826 | 0,01025 | 1,0000 |
| 1,00 | -0,80° | -0,80° | 43,379 | 0,01397 | 1,0000 |
| 1,10 | -0,95° | -0,96° | 57,171 | 0,01841 | 1,0000 |
| 1,20 | -1,12° | -1,14° | 73,501 | 0,02367 | 0,9999 |
| 1,30 | -1,31° | -1,32° | 92,731 | 0,02987 | 0,9999 |
| 1,40 | -1,51° | -1,53° | 115,305 | 0,03714 | 0,9999 |
| 1,50 | -1,74° | -1,75° | 141,764 | 0,04566 | 0,9998 |
| 1,60 | -1,98° | -2,02° | 173,678 | 0,05594 | 0,9998 |
| 1,70 | -2,26° | -2,35° | 212,283 | 0,06837 | 0,9997 |
| 1,80 | -2,59° | -2,73° | 259,466 | 0,08357 | 0,9996 |
| 1,90 | -3,01° | -3,20° | 320,278 | 0,10315 | 0,9995 |
| 2,00 | -3,42° | -3,82° | 392,338 | 0,12636 | 0,9993 |

Leitura: o arrasto cresce rápido com a aceleração lateral, de 0,141 N a 0,10 g a 392,338 N a 2,00 g, e D/(m·g) chega a 0,12636 nesse ponto. A forma linearizada acompanha o cálculo roda a roda (razão de 1,0000 até 1,10 g e 0,9993 a 2,00 g). O α sai com sinal negativo porque a curva é à esquerda, no eixo ISO do projeto.

**Energia do enduro.** Sem o traçado do enduro não existe energia total. D vale por condição (a_y e R). A energia é Σ D × comprimento de cada trecho de curva, e o traçado está a confirmar.

## 7. Decisões por degrau

Os degraus são os do roteiro. "Não medido aqui" quer dizer que o degrau está fora do estudo (spec §6.1); "não avaliado" quer dizer que está dentro, mas o caso não deu base para decidir.

| degrau | nome | muda decisão | frase |
|---|---|---|---|
| 1 | A2 no carro | não avaliado | não avaliado: o carro não chega ao limite até 2 g em nenhuma pressão |
| 2 | Ajuste PP*/QPZ do PAC2002 | não avaliado | não avaliado: o carro não chega ao limite até 2 g em nenhuma pressão (nos perfis interpolados entre os .tir, não num ajuste PP*/QPZ) |
| 3 | A3: pressão em operação | não avaliado | não avaliado: o carro não chega ao limite até 2 g em nenhuma pressão (pressão de ensaio, a fria; pressão quente e temperatura não estão no modelo) |
| 4 | B: transiente do pneu | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 5 | C: dinâmica do veículo | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 6 | Pneu substituto do T11 | não avaliado | não avaliado: o λ exploratório (LMUY, LFZO, LKY), a 8,0, 10,0 e 12,0 psi: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal); a 14,0 psi: N/A em toda a varredura; nenhum critério avaliado deu sim |
| 7 | Resistência ao rolamento | não avaliado | não avaliado: sem Crr com fonte e sem regra de decisão para energia; o arrasto sai como tamanho de efeito |
| 8 | λμ e λKy calibrados no skidpad | não avaliado | não avaliado: o λ exploratório (LMUY, LFZO, LKY), a 8,0, 10,0 e 12,0 psi: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal); a 14,0 psi: N/A em toda a varredura; nenhum critério avaliado deu sim |
| 9 | Mz, trilha pneumática e Mx | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 10 | Deslizamento combinado validado | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 11 | Temperatura como estado, com ciclos térmicos | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 12 | Rigidez vertical do pneu | não avaliado | não avaliado: N/A (a) e N/A (b); nenhum critério avaliado deu sim |
| 13 | Raio carregado e raio de rolamento | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 14 | Comparação com o OptimumTire | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 15 | Arrasto induzido pela deriva | não avaliado | não avaliado: sem Crr com fonte e sem regra de decisão para energia; o arrasto sai como tamanho de efeito |
| 16 | Estudo de sensibilidade | não medido aqui | este estudo |
| 17 | Instrumentação e contrato de dados de ensaio | não medido aqui | o degrau não entra neste estudo (spec §6.1) |
| 18 | Ciclo de engenharia (V5 do roadmap) | não medido aqui | o degrau não entra neste estudo (spec §6.1) |

### Detalhe dos critérios

- Degrau 1: vereditos entre pressões (não avaliado: N/A a 8,0, 10,0, 12,0, 14,0 psi); a_y_lim, KT (a) (não avaliado: menos de 2 pressões decidíveis (0); não decidíveis: 8,0, 10,0, 12,0, 14,0 psi (nenhuma pressão decidível)); a_y_lim, KT (b) (não avaliado: menos de 2 pressões decidíveis (0); não decidíveis: 8,0, 10,0, 12,0, 14,0 psi (nenhuma pressão decidível)); Cα, eixo F (não avaliado: as pressões 8,0 e 14,0 psi diferem, mas a banda ali é só limite inferior: não resolvida); Cα, eixo R (não avaliado: as pressões 8,0 e 14,0 psi diferem, mas a banda ali é só limite inferior: não resolvida)
- Degrau 2: vereditos entre pressões (não avaliado: N/A a 8,0, 10,0, 12,0, 14,0 psi); a_y_lim, KT (a) (não avaliado: menos de 2 pressões decidíveis (0); não decidíveis: 8,0, 10,0, 12,0, 14,0 psi (nenhuma pressão decidível)); a_y_lim, KT (b) (não avaliado: menos de 2 pressões decidíveis (0); não decidíveis: 8,0, 10,0, 12,0, 14,0 psi (nenhuma pressão decidível)); Cα, eixo F (não avaliado: as pressões 8,0 e 14,0 psi diferem, mas a banda ali é só limite inferior: não resolvida); Cα, eixo R (não avaliado: as pressões 8,0 e 14,0 psi diferem, mas a banda ali é só limite inferior: não resolvida)
- Degrau 3: vereditos entre pressões (não avaliado: N/A a 8,0, 10,0, 12,0, 14,0 psi); a_y_lim, KT (a) (não avaliado: menos de 2 pressões decidíveis (0); não decidíveis: 8,0, 10,0, 12,0, 14,0 psi (nenhuma pressão decidível)); a_y_lim, KT (b) (não avaliado: menos de 2 pressões decidíveis (0); não decidíveis: 8,0, 10,0, 12,0, 14,0 psi (nenhuma pressão decidível)); Cα, eixo F (não avaliado: as pressões 8,0 e 14,0 psi diferem, mas a banda ali é só limite inferior: não resolvida); Cα, eixo R (não avaliado: as pressões 8,0 e 14,0 psi diferem, mas a banda ali é só limite inferior: não resolvida)
- Degrau 6: robustez de λ a 8,0 psi (não avaliado: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal)); robustez de λ a 10,0 psi (não avaliado: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal)); robustez de λ a 12,0 psi (não avaliado: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal)); robustez de λ a 14,0 psi (não avaliado: N/A, N/A em toda a varredura)
- Degrau 7: arrasto × rolamento (não avaliado: sem Crr com fonte e sem regra de decisão para energia; o arrasto sai como tamanho de efeito)
- Degrau 8: robustez de λ a 8,0 psi (não avaliado: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal)); robustez de λ a 10,0 psi (não avaliado: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal)); robustez de λ a 12,0 psi (não avaliado: NÃO CONCLUSIVO, N/A em parte da varredura (sem inversão de sinal)); robustez de λ a 14,0 psi (não avaliado: N/A, N/A em toda a varredura)
- Degrau 12: veredito de a e b a 8,0 psi (não avaliado: N/A (a) e N/A (b)); a_y_lim de a e b a 8,0 psi (não avaliado: a_y_lim ou banda indisponível); veredito de a e b a 10,0 psi (não avaliado: N/A (a) e N/A (b)); a_y_lim de a e b a 10,0 psi (não avaliado: a_y_lim ou banda indisponível); veredito de a e b a 12,0 psi (não avaliado: N/A (a) e N/A (b)); a_y_lim de a e b a 12,0 psi (não avaliado: a_y_lim ou banda indisponível); veredito de a e b a 14,0 psi (não avaliado: N/A (a) e N/A (b)); a_y_lim de a e b a 14,0 psi (não avaliado: a_y_lim ou banda indisponível)
- Degrau 15: arrasto × rolamento (não avaliado: sem Crr com fonte e sem regra de decisão para energia; o arrasto sai como tamanho de efeito)

## 8. Tempos de execução

Tempos medidos na execução completa, em segundos.

| parte | tempo (s) |
|---|---|
| tornado | 3,6 |
| pressao | 3,9 |
| combinacao | 26,9 |
| pneu | 2,7 |
| arrasto | 0,4 |
| total | 37,6 |

A combinação das 27 combinações de λ é a parte lenta (26,9 s dos 37,6 s). Com `--rapido` ela não roda.

## 9. Como rodar

No Git Bash, a partir da raiz do repositório:

```
export UV_SYSTEM_CERTS=1
uv run python -X utf8 tools/relatorio_pneu1.py [--caso ARQ] [--set CHAVE=VALOR] [--rapido] [--saida DIR]
```

- `--caso ARQ` usa outro caso em JSON no lugar do demonstrativo;
- `--set CHAVE=VALOR` edita um campo (a origem passa a "✎ Editado pelo usuário"); pode repetir;
- `--rapido` pula a combinação de λ (a seção 5.3 fica "não avaliado: combinação não rodada");
- `--saida DIR` muda a pasta de saída (padrão `build/pneu1/`, que não é versionada). Saem `relatorio.md` e `resultados.json`.

Os `.tir` do TTC Round 6 ficam fora do Git. A ferramenta os procura em `DDS_TTC_DIR` ou em `references/ttc/round6_hoosier_r25b_20p5x7_13_7in`. Sem eles, sai com código 3 (NÃO EXECUTÁVEL). Entrada inválida sai com código 2 e uma mensagem em português. A gravação de um caso editado (`salvar_caso`) recusa sobrescrever o demonstrativo; use outro caminho.

Teste: `tests/test_sensibilidade_pneu.py` (20 verificações, mesmos `.tir`). A conferência com a planilha, `tests/test_caso_pneu1_equivalencia.py`, só roda com uma cópia recalculada da V4.4 em `DDS_COPIA_V44_RECALC`.

## 10. Pendências

- **Traçado do enduro:** sem ele não há energia por volta; o D só vale por condição.
- **Crr com fonte:** sem ele, os degraus 7 e 15 ficam "não avaliado" e não existe razão arrasto/rolamento.
- **Fx·κ:** o Milliken não separa esse termo (p. 65). Sem fonte conferida, ele está fora; se vier uma fonte, o usuário aprova antes do uso.
- **Conferência com a planilha (spec §5.4):** falta rodar `tests/test_caso_pneu1_equivalencia.py` com uma cópia recalculada da V4.4.
- **Origem dos campos:** confirmar, campo a campo, que a origem "◐ Dado de outro carro (TX, T09)" vinda das colunas `org_` da V4.4 está certa.
- **Caso do T11:** o estudo só responde quando algum eixo sature antes de 2 g.
- **Ackermann:** `ackermann_pct` entra como "? A confirmar" (sem valor), porque o código não reimplementa a aba 07.
