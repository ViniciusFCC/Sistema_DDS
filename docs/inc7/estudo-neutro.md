# Estudo da faixa do NEUTRO (incremento 7, Task 6)

- **Data:** 2026-10-29. Código no commit a98252c (`python/estudo_neutro.py`), branch `claude/inc7-plano-0926f7`.
- **Situação:** estudo para a decisão do usuário sobre o EDR-065 item 2 (spec §4.3). A regra do `analise_par` não
  mudou: o TC-NEU-001 confere que o veredito do caso-base é o mesmo de antes do estudo.
- **Todos os números são de casos SINTÉTICOS.** Nenhum é resultado do carro, do T11 ou do TX.

## O que se mediu

A regra de hoje declara NEUTRO quando |Δ| <= faixa, com Δ = S_r − S_f (a_y de saturação de cada eixo) e
faixa = max(|S_F,h − S_F,h/2|, |S_R,h − S_R,h/2|, 1e-9 g). A spec §4.3 levantou três dúvidas sobre essa faixa: o
serrote do máximo discreto em α, o erro de Δ, que pode chegar a e_F + e_R, e o ramo em que só um eixo satura. O estudo
mede as duas primeiras. A terceira ficou sem medida, porque nenhum caso caiu nesse ramo.

**Caso-base (sintético).** O `veiculo_base` de `tests/test_escada.py` (250 kg, L = 1,550 m, b = 0,713 m), o `.tir`
provisório do TTC com LMUY = 0,5 (escala de teste), R = 8,5 m, downforce de 400 N com 45 % na frente, toe zero, formas
da V4.2 (`FORMAS_V42`), a_y até 2,0 g. É o `casos["base"]` do `test_escada.py`, reproduzido em
`estudo_neutro.caso_base_sintetico()` (importar o teste rodaria a escada inteira).

**Casos perturbados (sintéticos).** Seis, um parâmetro por vez:
- λ_f ± 10 % (relativo). O λ_f não é campo do `CasoEquilibrio` nem do `VehicleConfig`. O equivalente usado é
  λ_f = K_φf/(K_φf + K_φr), com `roll_stiffness_front` e `roll_stiffness_rear`: λ_f vezes 1,1 ou 0,9, mantida a soma.
  No caso-base λ_f = 0,4405.
- toe ± 0,1°: somado ao `toe_rad` das quatro rodas (toe + = toe-out, EDR-002). Outra escolha (só a frente, por
  exemplo) daria outros números.
- R ± 10 %: `raio_m` = 9,35 m e 7,65 m.

**Grades.** h = (0,05 g em a_y; 25 pontos de α), h/2 = (0,025 g; 49), h/4 = (0,0125 g; 97), h/8 = (0,00625 g; 193).
É a regra do refinamento do `analise_par` (passo/2 e 2n − 1 pontos) aplicada três vezes, então cada grade contém os
pontos das anteriores. O TC-NEU-001 confere isso.

**Grandezas** (todas em g):
- d1 = |S_h − S_h/2|, d2 = |S_h/2 − S_h/4|, d3 = |S_h/4 − S_h/8|;
- ordem observada p = log2(d1/d2) e razão d1/d2. Se d1 ou d2 der menos de 1e-9 g, p fica indefinido e o eixo conta
  como "diferença nula";
- e_F = d1_F e e_R = d1_R são as estimativas que a regra já tem, a partir das grades h e h/2;
- erro real de cada eixo = |S_h − S_h/8| e erro de Δ = |Δ_h − Δ_h/8|, com a h/8 tomada como referência;
- violação de (c): erro de Δ > e_F + e_R.

**Alternativas** (spec §4.3), calculadas na grade h:
1. faixa = max(f_F·e_F, f_R·e_R), com f = 2^p/(2^p − 1) e o p medido de cada eixo. A coluna "com 4/3" usa
   4/3·max(e_F, e_R), o fator do EDR-065 item 2. Com p indefinido ou p <= 0 o fator não existe e a alternativa não
   se aplica ao caso;
2. faixa = e_F + e_R;
3. refino do pico da capacidade por parábola de 3 pontos (o máximo da grade e os dois vizinhos), com a regra de hoje
   para a faixa. Só existe no estudo (`estudo_neutro._capacidade_refinada`). Na planilha e no `equilibrio` seria
   mudança de fórmula, que exige aprovação.

As tabelas abaixo saem de `uv run python -X utf8 python/estudo_neutro.py`, que grava em
`build/estudo-neutro-tabelas.md` (cerca de 4 min). Foram copiadas sem edição.

## Tabelas

### Tabela 1. Saturação por grade, sem refino [g] (sintético)

| Caso | Eixo | S_h | S_h/2 | S_h/4 | S_h/8 | d1 = \|S_h − S_h/2\| | d2 = \|S_h/2 − S_h/4\| | d3 = \|S_h/4 − S_h/8\| | razão d1/d2 | p | dif. nula |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base (sintético) | F | 1,4763736 | 1,4763843 | 1,4763847 | 1,4763848 | 1,08e-05 | 3,16e-07 | 1,58e-07 | 34,1 | 5,09 | não |
| base (sintético) | R | 1,4684588 | 1,4697438 | 1,4697458 | 1,4697468 | 1,29e-03 | 2,00e-06 | 1,00e-06 | 641 | 9,33 | não |
| λ_f +10 % (sintético) | F | 1,4697492 | 1,4697598 | 1,4697612 | 1,4697619 | 1,06e-05 | 1,40e-06 | 7,00e-07 | 7,55 | 2,92 | não |
| λ_f +10 % (sintético) | R | 1,4759114 | 1,4767838 | 1,4767844 | 1,4768728 | 8,72e-04 | 5,98e-07 | 8,84e-05 | 1,46e+03 | 10,51 | não |
| λ_f −10 % (sintético) | F | 1,4825975 | 1,4826042 | 1,4826056 | 1,4826061 | 6,69e-06 | 1,46e-06 | 4,70e-07 | 4,57 | 2,19 | não |
| λ_f −10 % (sintético) | R | 1,4611986 | 1,4623665 | 1,4623718 | 1,4623719 | 1,17e-03 | 5,35e-06 | 2,77e-08 | 218 | 7,77 | não |
| toe +0,1° (sintético) | F | 1,4759172 | 1,4759284 | 1,4759687 | 1,4760534 | 1,12e-05 | 4,03e-05 | 8,47e-05 | 0,278 | -1,85 | não |
| toe +0,1° (sintético) | R | 1,4685352 | 1,4692146 | 1,4692229 | 1,4693053 | 6,79e-04 | 8,25e-06 | 8,24e-05 | 82,4 | 6,36 | não |
| toe −0,1° (sintético) | F | 1,4764670 | 1,4764776 | 1,4764779 | 1,4764818 | 1,06e-05 | 3,34e-07 | 3,89e-06 | 31,8 | 4,99 | não |
| toe −0,1° (sintético) | R | 1,4692169 | 1,4700061 | 1,4700191 | 1,4701046 | 7,89e-04 | 1,30e-05 | 8,54e-05 | 60,6 | 5,92 | não |
| R +10 % (sintético) | F | 1,4804493 | 1,4804583 | 1,4804595 | 1,4804601 | 8,94e-06 | 1,25e-06 | 6,25e-07 | 7,15 | 2,84 | não |
| R +10 % (sintético) | R | 1,4684588 | 1,4697438 | 1,4697458 | 1,4697468 | 1,29e-03 | 2,00e-06 | 1,00e-06 | 641 | 9,33 | não |
| R −10 % (sintético) | F | 1,4708691 | 1,4708786 | 1,4708796 | 1,4708800 | 9,49e-06 | 9,36e-07 | 4,68e-07 | 10,1 | 3,34 | não |
| R −10 % (sintético) | R | 1,4684588 | 1,4697438 | 1,4697458 | 1,4697468 | 1,29e-03 | 2,00e-06 | 1,00e-06 | 641 | 9,33 | não |

### Tabela 2. Erro de Δ contra e_F + e_R, sem refino [g] (sintético)

| Caso | Ramo | Δ_h | Δ_h/8 | erro real F | erro real R | e_F = d1_F | e_R = d1_R | erro de Δ | e_F + e_R | violação de (c) | resolução atual | erro de Δ / resolução |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base (sintético) | dois | -0,0079148 | -0,0066380 | 1,12e-05 | 1,29e-03 | 1,08e-05 | 1,29e-03 | 1,28e-03 | 1,30e-03 | não | 1,29e-03 | 0,99 |
| λ_f +10 % (sintético) | dois | 0,0061622 | 0,0071109 | 1,27e-05 | 9,61e-04 | 1,06e-05 | 8,72e-04 | 9,49e-04 | 8,83e-04 | SIM | 8,72e-04 | 1,09 |
| λ_f −10 % (sintético) | dois | -0,0213988 | -0,0202342 | 8,62e-06 | 1,17e-03 | 6,69e-06 | 1,17e-03 | 1,16e-03 | 1,17e-03 | não | 1,17e-03 | 1,00 |
| toe +0,1° (sintético) | dois | -0,0073819 | -0,0067482 | 1,36e-04 | 7,70e-04 | 1,12e-05 | 6,79e-04 | 6,34e-04 | 6,91e-04 | não | 6,79e-04 | 0,93 |
| toe −0,1° (sintético) | dois | -0,0072501 | -0,0063772 | 1,49e-05 | 8,88e-04 | 1,06e-05 | 7,89e-04 | 8,73e-04 | 8,00e-04 | SIM | 7,89e-04 | 1,11 |
| R +10 % (sintético) | dois | -0,0119906 | -0,0107133 | 1,08e-05 | 1,29e-03 | 8,94e-06 | 1,29e-03 | 1,28e-03 | 1,29e-03 | não | 1,29e-03 | 0,99 |
| R −10 % (sintético) | dois | -0,0024104 | -0,0011332 | 1,09e-05 | 1,29e-03 | 9,49e-06 | 1,29e-03 | 1,28e-03 | 1,29e-03 | não | 1,29e-03 | 0,99 |

### Tabela 3. Faixa e veredito de cada regra na grade h (sintético)

| Caso | Δ_h | Atual: faixa / veredito | Alt. 1 (p medido): faixa / veredito | Alt. 1 com 4/3: faixa / veredito | Alt. 2 (e_F + e_R): faixa / veredito | Alt. 3 (refino, regra atual): Δ_h / faixa / veredito | Δ_h/8 sem refino |
|---|---|---|---|---|---|---|---|
| base (sintético) | -0,0079148 | 1,29e-03 / LOOSE | 1,29e-03 / LOOSE | 1,71e-03 / LOOSE | 1,30e-03 / LOOSE | -0,0064913 / 2,38e-04 / LOOSE | -0,0066380 |
| λ_f +10 % (sintético) | 0,0061622 | 8,72e-04 / PUSH | 8,73e-04 / PUSH | 1,16e-03 / PUSH | 8,83e-04 / PUSH | 0,0075622 / 6,74e-04 / PUSH | 0,0071109 |
| λ_f −10 % (sintético) | -0,0213988 | 1,17e-03 / LOOSE | 1,17e-03 / LOOSE | 1,56e-03 / LOOSE | 1,17e-03 / LOOSE | -0,0206865 / 4,30e-04 / LOOSE | -0,0202342 |
| toe +0,1° (sintético) | -0,0073819 | 6,79e-04 / LOOSE | não se aplica | 9,06e-04 / LOOSE | 6,91e-04 / LOOSE | -0,0074793 / 4,20e-04 / LOOSE | -0,0067482 |
| toe −0,1° (sintético) | -0,0072501 | 7,89e-04 / LOOSE | 8,02e-04 / LOOSE | 1,05e-03 / LOOSE | 8,00e-04 / LOOSE | -0,0058021 / 6,33e-04 / LOOSE | -0,0063772 |
| R +10 % (sintético) | -0,0119906 | 1,29e-03 / LOOSE | 1,29e-03 / LOOSE | 1,71e-03 / LOOSE | 1,29e-03 / LOOSE | -0,0105702 / 2,38e-04 / LOOSE | -0,0107133 |
| R −10 % (sintético) | -0,0024104 | 1,29e-03 / LOOSE | 1,29e-03 / LOOSE | 1,71e-03 / LOOSE | 1,29e-03 / LOOSE | -0,0009827 / 2,38e-04 / LOOSE | -0,0011332 |

### Tabela 4. Com refino do pico por parábola (alternativa 3) [g] (sintético)

| Caso | Eixo | S_h | S_h/2 | S_h/4 | S_h/8 | d1 | d2 | p | dif. nula | erro real \|S_h − S_h/8\| |
|---|---|---|---|---|---|---|---|---|---|---|
| base (sintético) | F | 1,4764766 | 1,4763875 | 1,4763848 | 1,4763855 | 8,91e-05 | 2,77e-06 | 5,00 | não | 9,11e-05 |
| base (sintético) | R | 1,4699853 | 1,4697468 | 1,4697575 | 1,4697616 | 2,38e-04 | 1,07e-05 | 4,48 | não | 2,24e-04 |
| λ_f +10 % (sintético) | F | 1,4699462 | 1,4697932 | 1,4697750 | 1,4697721 | 1,53e-04 | 1,82e-05 | 3,07 | não | 1,74e-04 |
| λ_f +10 % (sintético) | R | 1,4775084 | 1,4768344 | 1,4768642 | 1,4768729 | 6,74e-04 | 2,98e-05 | 4,50 | não | 6,35e-04 |
| λ_f −10 % (sintético) | F | 1,4826396 | 1,4826082 | 1,4826223 | 1,4826273 | 3,14e-05 | 1,41e-05 | 1,15 | não | 1,22e-05 |
| λ_f −10 % (sintético) | R | 1,4619531 | 1,4623832 | 1,4623767 | 1,4623750 | 4,30e-04 | 6,47e-06 | 6,05 | não | 4,22e-04 |
| toe +0,1° (sintético) | F | 1,4764092 | 1,4761184 | 1,4760446 | 1,4760544 | 2,91e-04 | 7,37e-05 | 1,98 | não | 3,55e-04 |
| toe +0,1° (sintético) | R | 1,4689298 | 1,4693503 | 1,4693041 | 1,4693053 | 4,20e-04 | 4,61e-05 | 3,19 | não | 3,75e-04 |
| toe −0,1° (sintético) | F | 1,4764988 | 1,4764845 | 1,4764997 | 1,4765075 | 1,44e-05 | 1,52e-05 | -0,08 | não | 8,68e-06 |
| toe −0,1° (sintético) | R | 1,4706967 | 1,4700642 | 1,4701025 | 1,4701047 | 6,33e-04 | 3,83e-05 | 4,04 | não | 5,92e-04 |
| R +10 % (sintético) | F | 1,4805554 | 1,4804621 | 1,4804596 | 1,4804606 | 9,34e-05 | 2,51e-06 | 5,22 | não | 9,48e-05 |
| R +10 % (sintético) | R | 1,4699853 | 1,4697468 | 1,4697575 | 1,4697616 | 2,38e-04 | 1,07e-05 | 4,48 | não | 2,24e-04 |
| R −10 % (sintético) | F | 1,4709680 | 1,4708812 | 1,4708798 | 1,4708811 | 8,68e-05 | 1,40e-06 | 5,96 | não | 8,70e-05 |
| R −10 % (sintético) | R | 1,4699853 | 1,4697468 | 1,4697575 | 1,4697616 | 2,38e-04 | 1,07e-05 | 4,48 | não | 2,24e-04 |

### Tabela 5. Erro de Δ com refino [g] (sintético)

| Caso | Δ_h | Δ_h/8 | erro de Δ | e_F + e_R | violação de (c) | erro de Δ sem refino |
|---|---|---|---|---|---|---|
| base (sintético) | -0,0064913 | -0,0066239 | 1,33e-04 | 3,28e-04 | não | 1,28e-03 |
| λ_f +10 % (sintético) | 0,0075622 | 0,0071008 | 4,61e-04 | 8,27e-04 | não | 9,49e-04 |
| λ_f −10 % (sintético) | -0,0206865 | -0,0202524 | 4,34e-04 | 4,61e-04 | não | 1,16e-03 |
| toe +0,1° (sintético) | -0,0074793 | -0,0067491 | 7,30e-04 | 7,11e-04 | SIM | 6,34e-04 |
| toe −0,1° (sintético) | -0,0058021 | -0,0064028 | 6,01e-04 | 6,47e-04 | não | 8,73e-04 |
| R +10 % (sintético) | -0,0105702 | -0,0106990 | 1,29e-04 | 3,32e-04 | não | 1,28e-03 |
| R −10 % (sintético) | -0,0009827 | -0,0011194 | 1,37e-04 | 3,25e-04 | não | 1,28e-03 |

- sem refino: d1 < 1e-9 g em 0 de 14 eixos; dif. nula (d1 ou d2 < 1e-9 g) em 0 de 14; violações de (c): 2 (λ_f +10 % (sintético), toe −0,1° (sintético)).
- com refino: d1 < 1e-9 g em 0 de 14 eixos; dif. nula (d1 ou d2 < 1e-9 g) em 0 de 14; violações de (c): 1 (toe +0,1° (sintético)).

### Tabela 6. Pico da Fy do eixo no caso-base, na a_y de saturação da grade h/8 (sintético)

| Eixo | a_y [g] | Pico denso (24001 pontos) [N] | Grade h (25 pontos): erro [N] | Parábola de 3 pontos: erro [N] | α do pico denso / grade / parábola [rad] |
|---|---|---|---|---|---|
| F | 1,4763848 | 1665,5848 | -0,0012 | +0,1206 | -0,06532 / -0,06545 / -0,06676 |
| R | 1,4697468 | 1946,4821 | -1,9001 | +1,0010 | -0,07034 / -0,06545 / -0,07075 |

Passo da grade h em α: 0,01091 rad.

## O que os números mostram

1. **Não há p ≈ 2 estável.** Sem refino, p vai de −1,85 (toe +0,1°, frente) a 10,51 (λ_f +10 %, traseira). Na
   traseira fica entre 5,92 e 10,51 nos sete casos; na frente, entre −1,85 e 5,09. O mais próximo de 2 é 2,19
   (λ_f −10 %, frente). A convergência também não é monótona: em cinco dos catorze eixos d3 é maior que d2 (por
   exemplo λ_f +10 %, traseira: d2 = 5,98e-07 e d3 = 8,84e-05). O fator 4/3 supõe erro liso com p = 2, e isso não
   aparece em nenhum dos casos.

2. **O erro da traseira na grade h vem quase todo do pico em α.** Na traseira, d1 fica entre 6,8e-04 e 1,29e-03 g e d2
   entre 6e-07 e 1,3e-05 g: a grade h destoa e, da h/2 em diante, as saturações quase não mudam. A Tabela 6 mostra a causa no
   caso-base: na a_y de saturação, a grade de 25 pontos erra o pico da Fy traseira em 1,90 N; na frente, em
   0,0012 N, porque um ponto da grade cai quase em cima do pico. É o mecanismo (i) da spec §4.3. A frente acerta pela
   posição do pico, não por convergência.

3. **Diferença nula: nenhum caso.** d1 < 1e-9 g em 0 de 14 eixos, com e sem refino, e nenhum p ficou indefinido por
   isso. A situação da spec §4.3 (i), em que |S_h − S_h/2| cai no piso de 1e-9 g com erro real diferente de zero,
   não aconteceu nestes sete casos. Sete casos não bastam para dizer que ela é rara.

4. **e_F + e_R contra o erro de Δ.** Sem refino, a razão entre o erro de Δ e a faixa de hoje vai de 0,93 a 1,11. Há
   duas violações de (c): λ_f +10 % (erro de Δ 9,49e-04 contra 8,83e-04) e toe −0,1° (8,73e-04 contra 8,00e-04).
   Nos dois casos o excesso (6,6e-05 e 7,3e-05) é da mesma ordem do d3 da traseira (8,84e-05 e 8,54e-05), ou seja,
   a própria referência h/8 ainda não convergiu nesse nível. Os números não permitem afirmar que essas violações são
   reais, nem que não são.

5. **Nenhum veredito muda.** Nos sete casos, as cinco faixas (hoje, alternativa 1 com p medido, alternativa 1 com
   4/3, alternativa 2 e alternativa 3) dão o mesmo veredito: PUSH em λ_f +10 % e LOOSE nos outros seis. O |Δ_h| mais
   próximo da faixa é o de R −10 % (0,0024104 g), cerca de 1,4 vez a maior faixa (1,71e-03, alternativa 1 com 4/3).
   Por isso estes casos não distinguem as alternativas pelo veredito, só pela faixa.

6. **Refino por parábola (alternativa 3).** O erro de Δ cai em seis dos sete casos (no caso-base, de 1,28e-03 para
   1,33e-04) e sobe em toe +0,1° (de 6,34e-04 para 7,30e-04), que passa a violar (c): 7,30e-04 contra 7,11e-04. O
   serrote não some: com refino, p vai de −0,08 a 6,05. Pela Tabela 6, a parábola passa do pico verdadeiro em
   +0,12 N na frente e +1,00 N na traseira. A curva Fy(α) do eixo não é simétrica perto do pico e, com passo de
   0,0109 rad, o vértice da parábola sai do lado errado na frente. O refino melhora a traseira (erro real de
   1,29e-03 para 2,24e-04 no caso-base) e piora a frente (de 1,12e-05 para 9,11e-05).

7. **R ± 10 % não mexe na traseira.** As saturações traseiras de R +10 % e R −10 % são idênticas às do caso-base em
   todas as grades. Na forma V4.2, sem Ackermann, sem aero dependente de V e sem tração, o R entra só na frente
   (δ_ref = L/R e cos δ_ref, hipótese 3). As duas perturbações de R só testam a frente.

## O que os números não sustentam

- Nenhum valor de p para a alternativa 1. O p medido varia demais entre casos e eixos e, num caso (toe +0,1°,
  frente), sai negativo, o que deixa o fator sem definição.
- Que o fator 4/3 seja a correção certa. Ele cobre o erro de Δ nos sete casos (a menor folga é a de λ_f +10 %:
  1,16e-03 contra 9,49e-04), mas cobre porque é maior, e não porque o erro siga c·h².
- Uma conclusão sobre o ramo de um eixo só (spec §4.3 (iii)): nenhum caso caiu nele.
- Qualquer conclusão sobre as formas da V4.3, sobre o raio do skidpad do T11 ou sobre outro pneu: o estudo usou só
  as formas da V4.2 e o pneu de escala.

## As três alternativas e o efeito nos casos

**Alternativa 1: fator 2^p/(2^p − 1) com o p medido, só no ramo de Richardson.** Com os p medidos (todos acima de
2,8, menos dois), o fator fica entre 1,00 e 1,28 e a faixa quase não muda em relação à de hoje, porque é o e_R, com p
alto, que manda nela (Tabela 3). Em toe +0,1° o p da frente é negativo e a alternativa não se aplica. Também não cobre
as duas violações de (c). Com 4/3 fixo, a faixa cresce um terço e cobre o erro de Δ nos sete casos, sem mudar nenhum
veredito. Para valer na planilha, o p teria de ser uma constante nomeada (a spec §4.3 pede uma fonte só para a célula
e para o `mmm`). Os números daqui não indicam qual valor.

**Alternativa 2: faixa de Δ igual a e_F + e_R.** A faixa cresce pouco em relação à de hoje (no máximo 1,7 %, em
toe +0,1°), porque o e_F é de 61 a 175 vezes menor que o e_R nestes casos. Responde à dúvida (ii) da spec
pela forma (soma em vez de máximo), mas não cobre as duas violações de (c), que vêm de e_R subestimado, e não da soma.
Não muda nenhum veredito.

**Alternativa 3: refino do pico por parábola.** Muda a fórmula da capacidade no Python e na planilha, e só entra com
aprovação. Diminui o erro de Δ em seis dos sete casos, aumenta em um e cria uma violação nele. Não traz p ≈ 2: o
serrote diminui na traseira, mas a parábola erra pela assimetria da curva, e na frente o erro cresce. Não muda nenhum
veredito.

## Perguntas para a decisão do usuário

- Qual das três alternativas (ou nenhuma) vai para o EDR-065 item 2.
- Na alternativa 1: qual p usar, como a constante nomeada que a spec pede, e o que fazer quando o p medido sai
  indefinido ou negativo.
- Se o estudo deve crescer antes da decisão: mais casos perto do neutro (|Δ| da ordem da faixa), um caso no ramo de
  um eixo só, as formas da V4.3, ou uma grade h/16 para fechar a dúvida sobre as duas violações de (c).
