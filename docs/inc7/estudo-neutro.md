# Estudo da faixa do NEUTRO (incremento 7, Task 6)

- **Data:** 2026-10-29. Código nos commits a98252c, f42566a e 82d31c6 (`python/estudo_neutro.py`), branch `claude/inc7-plano-0926f7`.
- **Situação:** estudo para a decisão do usuário sobre o EDR-065 item 2 (spec §4.3). A regra do `analise_par` não
  mudou: o TC-NEU-001 confere que o veredito do caso-base é o mesmo de antes do estudo.
- **Todos os números são de casos SINTÉTICOS.** Nenhum é resultado do carro, do T11 ou do TX.

## O que se mediu

A regra de hoje declara NEUTRO quando |Δ| <= faixa, com Δ = S_r − S_f (a_y de saturação de cada eixo) e
faixa = max(|S_F,h − S_F,h/2|, |S_R,h − S_R,h/2|, 1e-9 g). A spec §4.3 levantou três dúvidas sobre essa faixa: o
serrote do máximo discreto em α, o erro de Δ, que pode chegar a e_F + e_R, e o ramo em que só um eixo satura. O estudo
mede as duas primeiras. Para a terceira, a spec §4.3 diz que "O ramo de um eixo só continua com o passo.", mas o
código de hoje usa nesse ramo a `_resolucao`, que nem sempre é o passo. Ela fica fora das alternativas deste estudo
e entra nas perguntas ao usuário como PENDING_CONFIRMATION.

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

**Varredura perto do neutro (sintética).** λ_f de +4 % a +7 % (relativo), em passos de 0,5 %, sete casos, só sem
refino (`estudo_neutro.casos_perto_do_neutro`). Entre o caso-base (LOOSE) e λ_f +10 % (PUSH) o Δ troca de sinal; a
revisão da Task 6 estimou, por interpolação, Δ_h/8 = 0 perto de +4,8 % e Δ_h = 0 perto de +5,6 %, e a varredura
existe para medir isso. Um caso de conferência em λ_f +4,85 % (Tabela 9) testa a janela de sinal errado que
a Tabela 8 sugere.

**Grades.** h = (0,05 g em a_y; 25 pontos de α), h/2 = (0,025 g; 49), h/4 = (0,0125 g; 97), h/8 = (0,00625 g; 193).
É a regra do refinamento do `analise_par` (passo/2 e 2n − 1 pontos) aplicada três vezes, então cada grade contém os
pontos das anteriores. O TC-NEU-001 confere isso.

**Grandezas** (todas em g):
- d1 = |S_h − S_h/2|, d2 = |S_h/2 − S_h/4|, d3 = |S_h/4 − S_h/8|;
- ordem observada p = log2(d1/d2) e razão d1/d2. Se d1 ou d2 der menos de 1e-9 g, p fica indefinido e o eixo conta
  como "diferença nula";
- e_F = d1_F e e_R = d1_R são as estimativas que a regra já tem, a partir das grades h e h/2;
- erro real de cada eixo = |S_h − S_h/8| e erro de Δ = |Δ_h − Δ_h/8|, com a h/8 tomada como referência;
- violação de (c): erro de Δ > e_F + e_R;
- erro real / d1: quantas vezes o erro real de um eixo é maior que a estimativa que a regra tem dele;
- classe do veredito na varredura: NEUTRO, "certo" ou "ERRADO" contra o sinal de Δ_h/8 (PUSH se Δ_h/8 > 0). A h/8
  não convergiu por completo, então esse "sinal real" é o da melhor grade calculada.

**Alternativas** (spec §4.3), calculadas na grade h:
1. faixa = max(f_F·e_F, f_R·e_R), com f = 2^p/(2^p − 1) e o p medido de cada eixo. A coluna "com 4/3" usa
   4/3·max(e_F, e_R), o fator do EDR-065 item 2. Com p indefinido ou p <= 0 o fator não existe e a alternativa não
   se aplica ao caso;
2. faixa = e_F + e_R;
3. refino do pico da capacidade por parábola de 3 pontos (o máximo da grade e os dois vizinhos), com a regra de hoje
   para a faixa. Só existe no estudo (`estudo_neutro._capacidade_refinada`). Na planilha e no `equilibrio` seria
   mudança de fórmula, que exige aprovação.

As tabelas abaixo saem de `uv run python -X utf8 python/estudo_neutro.py`, que grava em
`build/estudo-neutro-tabelas.md` (cerca de 5 min). Foram copiadas sem edição.

## Tabelas

### Tabela 1. Saturação por grade, sem refino [g] (sintético)

| Caso | Eixo | S_h | S_h/2 | S_h/4 | S_h/8 | d1 = \|S_h − S_h/2\| | d2 = \|S_h/2 − S_h/4\| | d3 = \|S_h/4 − S_h/8\| | razão d1/d2 | p | dif. nula | erro real \|S_h − S_h/8\| | erro real / d1 | sinal de S_h − S_h/8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base (sintético) | F | 1,4763736 | 1,4763843 | 1,4763847 | 1,4763848 | 1,08e-05 | 3,16e-07 | 1,58e-07 | 34,1 | 5,09 | não | 1,12e-05 | 1,04 | − |
| base (sintético) | R | 1,4684588 | 1,4697438 | 1,4697458 | 1,4697468 | 1,29e-03 | 2,00e-06 | 1,00e-06 | 641 | 9,33 | não | 1,29e-03 | 1,00 | − |
| λ_f +10 % (sintético) | F | 1,4697492 | 1,4697598 | 1,4697612 | 1,4697619 | 1,06e-05 | 1,40e-06 | 7,00e-07 | 7,55 | 2,92 | não | 1,27e-05 | 1,20 | − |
| λ_f +10 % (sintético) | R | 1,4759114 | 1,4767838 | 1,4767844 | 1,4768728 | 8,72e-04 | 5,98e-07 | 8,84e-05 | 1,46e+03 | 10,51 | não | 9,61e-04 | 1,10 | − |
| λ_f −10 % (sintético) | F | 1,4825975 | 1,4826042 | 1,4826056 | 1,4826061 | 6,69e-06 | 1,46e-06 | 4,70e-07 | 4,57 | 2,19 | não | 8,62e-06 | 1,29 | − |
| λ_f −10 % (sintético) | R | 1,4611986 | 1,4623665 | 1,4623718 | 1,4623719 | 1,17e-03 | 5,35e-06 | 2,77e-08 | 218 | 7,77 | não | 1,17e-03 | 1,00 | − |
| toe +0,1° (sintético) | F | 1,4759172 | 1,4759284 | 1,4759687 | 1,4760534 | 1,12e-05 | 4,03e-05 | 8,47e-05 | 0,278 | -1,85 | não | 1,36e-04 | 12,15 | − |
| toe +0,1° (sintético) | R | 1,4685352 | 1,4692146 | 1,4692229 | 1,4693053 | 6,79e-04 | 8,25e-06 | 8,24e-05 | 82,4 | 6,36 | não | 7,70e-04 | 1,13 | − |
| toe −0,1° (sintético) | F | 1,4764670 | 1,4764776 | 1,4764779 | 1,4764818 | 1,06e-05 | 3,34e-07 | 3,89e-06 | 31,8 | 4,99 | não | 1,49e-05 | 1,40 | − |
| toe −0,1° (sintético) | R | 1,4692169 | 1,4700061 | 1,4700191 | 1,4701046 | 7,89e-04 | 1,30e-05 | 8,54e-05 | 60,6 | 5,92 | não | 8,88e-04 | 1,12 | − |
| R +10 % (sintético) | F | 1,4804493 | 1,4804583 | 1,4804595 | 1,4804601 | 8,94e-06 | 1,25e-06 | 6,25e-07 | 7,15 | 2,84 | não | 1,08e-05 | 1,21 | − |
| R +10 % (sintético) | R | 1,4684588 | 1,4697438 | 1,4697458 | 1,4697468 | 1,29e-03 | 2,00e-06 | 1,00e-06 | 641 | 9,33 | não | 1,29e-03 | 1,00 | − |
| R −10 % (sintético) | F | 1,4708691 | 1,4708786 | 1,4708796 | 1,4708800 | 9,49e-06 | 9,36e-07 | 4,68e-07 | 10,1 | 3,34 | não | 1,09e-05 | 1,15 | − |
| R −10 % (sintético) | R | 1,4684588 | 1,4697438 | 1,4697458 | 1,4697468 | 1,29e-03 | 2,00e-06 | 1,00e-06 | 641 | 9,33 | não | 1,29e-03 | 1,00 | − |

### Tabela 2. Erro de Δ contra e_F + e_R, sem refino [g] (sintético)

| Caso | Ramo | Δ_h | Δ_h/8 | erro real F | erro real R | e_F = d1_F | e_R = d1_R | erro de Δ | \|erro real R − erro real F\| | e_F + e_R | violação de (c) | resolução atual | erro de Δ / resolução | erro real F / e_F | erro real R / e_R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base (sintético) | dois | -0,0079148 | -0,0066380 | 1,12e-05 | 1,29e-03 | 1,08e-05 | 1,29e-03 | 1,28e-03 | 1,28e-03 | 1,30e-03 | não | 1,29e-03 | 0,99 | 1,04 | 1,00 |
| λ_f +10 % (sintético) | dois | 0,0061622 | 0,0071109 | 1,27e-05 | 9,61e-04 | 1,06e-05 | 8,72e-04 | 9,49e-04 | 9,49e-04 | 8,83e-04 | SIM | 8,72e-04 | 1,09 | 1,20 | 1,10 |
| λ_f −10 % (sintético) | dois | -0,0213988 | -0,0202342 | 8,62e-06 | 1,17e-03 | 6,69e-06 | 1,17e-03 | 1,16e-03 | 1,16e-03 | 1,17e-03 | não | 1,17e-03 | 1,00 | 1,29 | 1,00 |
| toe +0,1° (sintético) | dois | -0,0073819 | -0,0067482 | 1,36e-04 | 7,70e-04 | 1,12e-05 | 6,79e-04 | 6,34e-04 | 6,34e-04 | 6,91e-04 | não | 6,79e-04 | 0,93 | 12,15 | 1,13 |
| toe −0,1° (sintético) | dois | -0,0072501 | -0,0063772 | 1,49e-05 | 8,88e-04 | 1,06e-05 | 7,89e-04 | 8,73e-04 | 8,73e-04 | 8,00e-04 | SIM | 7,89e-04 | 1,11 | 1,40 | 1,12 |
| R +10 % (sintético) | dois | -0,0119906 | -0,0107133 | 1,08e-05 | 1,29e-03 | 8,94e-06 | 1,29e-03 | 1,28e-03 | 1,28e-03 | 1,29e-03 | não | 1,29e-03 | 0,99 | 1,21 | 1,00 |
| R −10 % (sintético) | dois | -0,0024104 | -0,0011332 | 1,09e-05 | 1,29e-03 | 9,49e-06 | 1,29e-03 | 1,28e-03 | 1,28e-03 | 1,29e-03 | não | 1,29e-03 | 0,99 | 1,15 | 1,00 |

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

- sem refino: d1 < 1e-9 g em 0 de 14 eixos; dif. nula (d1 ou d2 < 1e-9 g) em 0 de 14; S_h < S_h/8 em 14 de 14; violações de (c): 2 (λ_f +10 % (sintético), toe −0,1° (sintético)).
- com refino: d1 < 1e-9 g em 0 de 14 eixos; dif. nula (d1 ou d2 < 1e-9 g) em 0 de 14; S_h < S_h/8 em 3 de 14; violações de (c): 1 (toe +0,1° (sintético)).

### Tabela 6. Pico da Fy do eixo no caso-base, na a_y de saturação da grade h/8 (sintético)

| Eixo | a_y [g] | Pico denso (24001 pontos) [N] | Grade h (25 pontos): erro [N] | Parábola de 3 pontos: erro [N] | α do pico denso / grade / parábola [rad] |
|---|---|---|---|---|---|
| F | 1,4763848 | 1665,5848 | -0,0012 | +0,1206 | -0,06532 / -0,06545 / -0,06676 |
| R | 1,4697468 | 1946,4821 | -1,9001 | +1,0010 | -0,07034 / -0,06545 / -0,07075 |

Passo da grade h em α: 0,01091 rad.

### Tabela 7. Varredura de λ_f perto do neutro, sem refino [g] (sintético)

Classe: NEUTRO; "certo" ou "ERRADO" contra o sinal de Δ_h/8 (a h/8 não convergiu por completo). A alternativa 3 (refino) não foi calculada nesta varredura.

| Caso | Δ_h | Δ_h/8 | sinal real (h/8) | Atual: faixa / veredito / classe | Alt. 1 (p medido) | Alt. 1 com 4/3 | Alt. 2 (e_F + e_R) | p_F / p_R |
|---|---|---|---|---|---|---|---|---|
| λ_f +4,0 % (sintético) | -0,0023040 | -0,0011534 | LOOSE | 1,14e-03 / LOOSE / certo | 1,14e-03 / LOOSE / certo | 1,51e-03 / LOOSE / certo | 1,15e-03 / LOOSE / certo | 5,29 / 10,35 |
| λ_f +4,5 % (sintético) | -0,0015988 | -0,0004652 | LOOSE | 1,11e-03 / LOOSE / certo | 1,11e-03 / LOOSE / certo | 1,48e-03 / LOOSE / certo | 1,12e-03 / LOOSE / certo | 4,92 / 10,56 |
| λ_f +5,0 % (sintético) | -0,0008936 | 0,0002231 | PUSH | 1,09e-03 / NEUTRO / NEUTRO | 1,09e-03 / NEUTRO / NEUTRO | 1,46e-03 / NEUTRO / NEUTRO | 1,10e-03 / NEUTRO / NEUTRO | 4,62 / 10,82 |
| λ_f +5,5 % (sintético) | -0,0001884 | 0,0009115 | PUSH | 1,07e-03 / NEUTRO / NEUTRO | 1,07e-03 / NEUTRO / NEUTRO | 1,43e-03 / NEUTRO / NEUTRO | 1,08e-03 / NEUTRO / NEUTRO | 4,37 / 11,14 |
| λ_f +6,0 % (sintético) | 0,0005170 | 0,0016000 | PUSH | 1,05e-03 / NEUTRO / NEUTRO | 1,05e-03 / NEUTRO / NEUTRO | 1,40e-03 / NEUTRO / NEUTRO | 1,06e-03 / NEUTRO / NEUTRO | 4,14 / 11,55 |
| λ_f +6,5 % (sintético) | 0,0012225 | 0,0022886 | PUSH | 1,03e-03 / PUSH / certo | 1,03e-03 / PUSH / certo | 1,37e-03 / NEUTRO / NEUTRO | 1,04e-03 / PUSH / certo | 3,94 / 12,16 |
| λ_f +7,0 % (sintético) | 0,0019280 | 0,0029774 | PUSH | 1,00e-03 / PUSH / certo | 1,00e-03 / PUSH / certo | 1,34e-03 / PUSH / certo | 1,02e-03 / PUSH / certo | 3,76 / 13,28 |

- Cruzamento de zero por interpolação linear entre casos vizinhos: Δ_h = 0 em λ_f +5,63 %; Δ_h/8 = 0 em λ_f +4,84 %.
- Sinal errado / NEUTRO em 7 casos: regra atual 0 / 3; alt. 1 (p medido) 0 / 3; alt. 1 com 4/3 0 / 4; alt. 2 0 / 3.

### Tabela 8. Margem = faixa − erro de Δ na varredura, sem refino [g] (sintético)

| Caso | erro de Δ | e_F + e_R | violação de (c) | margem: hoje | margem: alt. 1 (p medido) | margem: alt. 1 com 4/3 | margem: alt. 2 |
|---|---|---|---|---|---|---|---|
| λ_f +4,0 % (sintético) | 1,15e-03 | 1,15e-03 | SIM | -1,54e-05 | -1,46e-05 | 3,63e-04 | -3,86e-06 |
| λ_f +4,5 % (sintético) | 1,13e-03 | 1,12e-03 | SIM | -2,04e-05 | -1,97e-05 | 3,51e-04 | -8,89e-06 |
| λ_f +5,0 % (sintético) | 1,12e-03 | 1,10e-03 | SIM | -2,54e-05 | -2,48e-05 | 3,38e-04 | -1,39e-05 |
| λ_f +5,5 % (sintético) | 1,10e-03 | 1,08e-03 | SIM | -3,03e-05 | -2,98e-05 | 3,26e-04 | -1,89e-05 |
| λ_f +6,0 % (sintético) | 1,08e-03 | 1,06e-03 | SIM | -3,52e-05 | -3,49e-05 | 3,14e-04 | -2,40e-05 |
| λ_f +6,5 % (sintético) | 1,07e-03 | 1,04e-03 | SIM | -4,02e-05 | -4,00e-05 | 3,02e-04 | -2,90e-05 |
| λ_f +7,0 % (sintético) | 1,05e-03 | 1,02e-03 | SIM | -4,51e-05 | -4,50e-05 | 2,90e-04 | -3,40e-05 |

- Violações de (c): 7 de 7. Margem negativa: hoje 7; alt. 1 (p medido) 7; alt. 1 com 4/3 0; alt. 2 7 de 7.

### Tabela 9. Caso de conferência λ_f +4,85 %, sem refino [g] (sintético)

Classe: NEUTRO; "certo" ou "ERRADO" contra o sinal de Δ_h/8 (a h/8 não convergiu por completo). A alternativa 3 (refino) não foi calculada nesta varredura.

| Caso | Δ_h | Δ_h/8 | sinal real (h/8) | Atual: faixa / veredito / classe | Alt. 1 (p medido) | Alt. 1 com 4/3 | Alt. 2 (e_F + e_R) | p_F / p_R |
|---|---|---|---|---|---|---|---|---|
| λ_f +4,85 % (sintético) | -0,0011052 | 0,0000166 | PUSH | 1,10e-03 / LOOSE / ERRADO | 1,10e-03 / LOOSE / ERRADO | 1,46e-03 / NEUTRO / NEUTRO | 1,11e-03 / NEUTRO / NEUTRO | 4,71 / 10,74 |

- Sinal errado / NEUTRO em 1 caso: regra atual 1 / 0; alt. 1 (p medido) 1 / 0; alt. 1 com 4/3 0 / 1; alt. 2 0 / 1.

Margem do caso de conferência [g] (sintético)

| Caso | erro de Δ | e_F + e_R | violação de (c) | margem: hoje | margem: alt. 1 (p medido) | margem: alt. 1 com 4/3 | margem: alt. 2 |
|---|---|---|---|---|---|---|---|
| λ_f +4,85 % (sintético) | 1,12e-03 | 1,11e-03 | SIM | -2,39e-05 | -2,32e-05 | 3,42e-04 | -1,24e-05 |

- Violações de (c): 1 de 1. Margem negativa: hoje 1; alt. 1 (p medido) 1; alt. 1 com 4/3 0; alt. 2 1 de 1.

## O que os números mostram

1. **Não há p ≈ 2 estável.** Sem refino, p vai de −1,85 (toe +0,1°, frente) a 10,51 (λ_f +10 %, traseira). Na
   traseira fica entre 5,92 e 10,51 nos sete casos; na frente, entre −1,85 e 5,09. O mais próximo de 2 é 2,19
   (λ_f −10 %, frente). Na varredura perto do neutro, a traseira vai de 10,35 a 13,28 e a frente de 3,76 a 5,29. A
   convergência também não é monótona: em cinco dos catorze eixos dos sete casos, d3 é maior que d2 (por exemplo
   λ_f +10 %, traseira: d2 = 5,98e-07 e d3 = 8,84e-05). O fator 4/3 supõe erro liso com p = 2, e isso não aparece em
   nenhum dos casos.

2. **O erro da traseira na grade h vem quase todo do pico em α.** Na traseira, d1 fica entre 6,8e-04 e 1,29e-03 g e
   d2 entre 6e-07 e 1,3e-05 g: a grade h destoa e, da h/2 em diante, as saturações quase não mudam. A Tabela 6 mostra
   a causa no caso-base: na a_y de saturação, a grade de 25 pontos erra o pico da Fy traseira em 1,90 N; na frente,
   em 0,0012 N, porque um ponto da grade cai quase em cima do pico. A frente acerta pela posição do pico, não por
   convergência.

3. **A diferença nula literal não ocorreu; a subestimação do d1 ocorreu.** d1 < 1e-9 g em 0 de 14 eixos, com e sem
   refino. Mas o mecanismo (i) da spec §4.3 (d1 pequeno com erro real bem maior) aconteceu em toe +0,1°, na frente:
   d1 = 1,12e-05, d2 = 4,03e-05, d3 = 8,47e-05, e o erro real contra a h/8 é 1,36e-04, 12,15 vezes o d1. As quatro
   saturações desse eixo crescem de grade em grade sem parar (1,4759172; 1,4759284; 1,4759687; 1,4760534), então o
   erro contra a solução convergida deve ser maior que esse, mas isso não foi medido: a h/8 não convergiu. Nos outros
   eixos, erro real / d1 fica entre 1,04 e 1,40 na frente e entre 1,00 e 1,13 na traseira.

4. **O erro de Δ tem sinal fixo e é uma diferença, não uma soma.** Nos 14 eixos dos sete casos, S_h < S_h/8 (coluna
   de sinal da Tabela 1). Quando os dois eixos têm o mesmo sinal,
   Δ_h − Δ_h/8 = (S_R,h − S_R,h/8) − (S_F,h − S_F,h/8) = erro real F − erro real R, e por isso
   erro de Δ = |erro real R − erro real F|. As duas colunas da Tabela 2 batem nos sete casos. Os erros dos dois eixos
   se descontam: em toe +0,1° o erro grande da frente (1,36e-04) reduz o erro de Δ para 6,34e-04, abaixo do erro da
   traseira (7,70e-04). Daí também Δ_h < Δ_h/8 em todos os casos calculados (os sete e os sete da varredura), com
   diferença de 6,34e-04 a 1,28e-03 g. O sinal tem uma explicação parcial: a grade de α da h está contida na da h/8,
   então na mesma a_y a capacidade da h nunca é maior que a da h/8, e menos capacidade antecipa a saturação. Para S
   isso não é garantia, porque a interpolação linear em a_y também entra; o sinal fixo foi observado, não provado.

5. **e_F + e_R contra o erro de Δ.** Nos sete casos de base, sem refino, a razão entre o erro de Δ e a faixa de
   hoje vai de 0,93 a 1,11, e há duas violações de (c): λ_f +10 % (erro de Δ 9,49e-04 contra 8,83e-04) e
   toe −0,1° (8,73e-04 contra 8,00e-04). Nos dois casos o excesso (6,6e-05 e 7,3e-05) é da mesma ordem do d3 da
   traseira (8,84e-05 e 8,54e-05), ou seja, a própria referência h/8 ainda não convergiu nesse nível. Na varredura
   perto do neutro (Tabela 8), (c) é violada nos 7 casos, e também no caso de conferência de +4,85 % (Tabela 9): o
   excesso do erro de Δ sobre e_F + e_R vai de 3,9e-06 (+4,0 %) a 3,4e-05 g (+7,0 %) e cresce com o λ_f. A mesma
   ressalva da h/8 vale aqui; os d3 dos casos da varredura não estão nas tabelas. Os números não permitem afirmar que
   essas violações são reais, nem que não são.

6. **Nos sete casos, nenhum veredito muda, por construção.** As cinco faixas (hoje, alternativa 1 com p medido,
   alternativa 1 com 4/3, alternativa 2 e alternativa 3) dão o mesmo veredito: PUSH em λ_f +10 % e LOOSE nos outros
   seis. O menor |Δ_h| é o de R −10 % (0,0024104 g), 1,4 vez a maior faixa (1,71e-03, alternativa 1 com 4/3). Com Δ
   tão longe da faixa, nenhuma regra poderia mudar o veredito; esses casos não distinguem as alternativas.

7. **Perto do neutro (Tabelas 7, 8 e 9).** Por interpolação linear entre os casos da varredura, Δ_h = 0 em
   λ_f +5,63 % e Δ_h/8 = 0 em λ_f +4,84 %, perto da estimativa da revisão (+5,6 % e +4,8 %). Entre os dois pontos,
   Δ_h e Δ_h/8 têm sinais opostos. Nos sete casos da varredura nenhuma regra deu sinal errado:
   - regra de hoje, alternativa 1 com p medido e alternativa 2: NEUTRO em +5,0 %, +5,5 % e +6,0 %, sinal certo nos
     outros quatro;
   - alternativa 1 com 4/3: NEUTRO também em +6,5 %, onde Δ_h/8 = 2,29e-03 indica PUSH.

   Isso não quer dizer que haja folga. A margem que decide o sinal é faixa − erro de Δ (Tabela 8), e ela é negativa
   nos 7 casos para a regra de hoje (de −1,54e-05 a −4,51e-05 g), para a alternativa 1 com p medido (de −1,46e-05 a
   −4,50e-05 g, quase igual à de hoje) e para a alternativa 2 (de −3,86e-06 a −3,40e-05 g). Com 4/3 ela é positiva
   nos 7 (de 2,90e-04 a 3,63e-04 g). Em +5,0 %, por exemplo, o erro de Δ é 1,12e-03 contra a faixa de hoje de
   1,09e-03 (margem −2,54e-05 g).

   Margem negativa abre uma janela de sinal errado logo depois de Δ_h/8 = 0: enquanto 0 < Δ_h/8 < −margem, o Δ_h é
   negativo e |Δ_h| passa da faixa, e a regra dá LOOSE com a h/8 indicando PUSH. Pela interpolação da Tabela 7, essa
   janela vai de λ_f +4,84 % a cerca de +4,86 % para a regra de hoje e a alternativa 1 com p medido, e é mais
   estreita para a alternativa 2. A 4/3 não tem essa janela. É uma estimativa por interpolação, com a h/8 como
   referência não convergida.

   **Caso de conferência λ_f +4,85 % (Tabela 9).** Δ_h = −0,0011052 e Δ_h/8 = +0,0000166, então a h/8 indica PUSH.
   A regra de hoje e a alternativa 1 com p medido (faixa 1,10e-03) dão LOOSE, sinal errado. A alternativa 2 (faixa
   1,11e-03) e a 4/3 (faixa 1,46e-03) dão NEUTRO. Isso bate com a margem: a da alternativa 2 é −1,24e-05, menor em
   módulo que o Δ_h/8 desse caso, e a de hoje é −2,39e-05, maior. Ressalva: o Δ_h/8 de 1,66e-05 g é menor que
   diferenças d3 vistas na Tabela 1 (até 8,84e-05 g), então o "sinal real" desse caso é o da h/8, não o de uma
   solução convergida. A alternativa 3 não entrou na varredura nem na conferência.

8. **Refino por parábola (alternativa 3).** O erro de Δ cai em seis dos sete casos (no caso-base, de 1,28e-03 para
   1,33e-04) e sobe em toe +0,1° (de 6,34e-04 para 7,30e-04), que passa a violar (c): 7,30e-04 contra 7,11e-04. O
   serrote não some: com refino, p vai de −0,08 a 6,05. Pela Tabela 6, a parábola passa do pico denso em +0,12 N na
   frente e +1,00 N na traseira, e na frente o vértice se afasta do pico (α de −0,06676 contra −0,06532 rad). A curva
   Fy(α) do eixo não é quadrática na escala do passo de 0,0109 rad (assimetria possível, não medida). O refino
   melhora a traseira (erro real de 1,29e-03 para 2,24e-04 no caso-base) e piora a frente (de 1,12e-05 para
   9,11e-05). Com refino o sinal de S_h − S_h/8 deixa de ser fixo (Tabela 4).

9. **R ± 10 % não mexe na traseira.** As saturações traseiras de R +10 % e R −10 % são idênticas às do caso-base em
   todas as grades. Na forma V4.2, sem Ackermann, sem aero dependente de V e sem tração, o R entra só na frente
   (δ_ref = L/R e cos δ_ref, hipótese 3). As duas perturbações de R só testam a frente.

## O que os números não sustentam

- Nenhum valor de p para a alternativa 1. O p medido varia demais entre casos e eixos e, num caso (toe +0,1°,
  frente), sai negativo, o que deixa o fator sem definição.
- Que o fator 4/3 seja a correção certa. Ele cobre o erro de Δ nos sete casos (a menor folga é a de λ_f +10 %:
  1,16e-03 contra 9,49e-04), mas cobre porque é maior, e não porque o erro siga c·h².
- O sinal "real" dentro da janela de sinal errado. O Δ_h/8 do caso de conferência (1,66e-05 g) é menor que a
  incerteza que a própria h/8 mostra nos casos de base; uma grade mais fina poderia mudar esse sinal.
- A largura exata da janela: ela sai de interpolação entre casos com passo de 0,5 % e de um único caso de
  conferência.
- Qualquer conclusão sobre as formas da V4.3, sobre o raio do skidpad do T11 ou sobre outro pneu: o estudo usou só
  as formas da V4.2 e o pneu de escala.

O ramo de um eixo só não foi estudado. Nenhum caso caiu nele, e cortar a varredura em ay_max_g = 1,47 não o produz
no caso-base: com passo de 0,05 g a última linha da grade h é 1,45 g, e as duas saturações (1,4764 e 1,4685 g) ficam
acima dela, então nenhum eixo satura. A regra desse ramo está nas perguntas (PENDING_CONFIRMATION): a spec §4.3 diz
que ele "continua com o passo", e o código de hoje usa a `_resolucao`, que é o d1 do eixo que satura e só vale o
passo quando um eixo satura numa das duas grades e não na outra.

## As três alternativas e o efeito nos casos

**Alternativa 1: fator 2^p/(2^p − 1) com o p medido, só no ramo de Richardson.** Com os p medidos (todos acima de
2,8, menos dois), o fator fica entre 1,00 e 1,28 e a faixa quase não muda em relação à de hoje, porque é o e_R, com p
alto, que manda nela (Tabelas 3 e 7). Em toe +0,1° o p da frente é negativo e a alternativa não se aplica. Não cobre
as duas violações de (c). Na varredura dá as mesmas classes da regra de hoje, e a margem faixa − erro de Δ é
negativa nos 7 casos, quase igual à de hoje. No caso de conferência de +4,85 % dá LOOSE com a h/8 indicando PUSH. Com
4/3 fixo, a faixa cresce um terço, cobre o erro de Δ nos sete casos de base, tem margem positiva nos 7 da varredura
(de 2,90e-04 a 3,63e-04 g), dá NEUTRO em +4,85 % e põe mais um caso em NEUTRO na varredura (+6,5 %, que a h/8 indica
PUSH). Nos casos de base cobre o erro porque é maior, não porque o p medido seja 2. Para
valer na planilha, o p teria de ser uma constante nomeada (a spec §4.3 pede uma fonte só para a célula e para o
`mmm`). Os números daqui não indicam qual valor.

**Alternativa 2: faixa de Δ igual a e_F + e_R.** A faixa cresce pouco em relação à de hoje (no máximo 1,7 %, em
toe +0,1°), porque o e_F é de 61 a 175 vezes menor que o e_R nestes casos. Usa a soma, e o erro de Δ medido é a
diferença dos erros dos eixos (item 4). Não cobre as duas violações de (c) dos casos de base, que vêm de e_R
subestimado. Na varredura dá as mesmas classes da regra de hoje, viola (c) nos 7 casos e tem margem negativa nos 7,
menor em módulo que a de hoje (de −3,86e-06 a −3,40e-05 g). No caso de conferência de +4,85 % dá NEUTRO.

**Alternativa 3: refino do pico por parábola.** Muda a fórmula da capacidade no Python e na planilha, e só entra com
aprovação. Diminui o erro de Δ em seis dos sete casos, aumenta em um e cria uma violação nele. Não traz p ≈ 2: o
serrote diminui na traseira, mas a parábola erra porque a curva não é quadrática na escala do passo, e na frente o
erro cresce. Nos sete casos não muda nenhum veredito. Não foi calculada na varredura perto do neutro.

## Perguntas para a decisão do usuário

- Qual das três alternativas (ou nenhuma) vai para o EDR-065 item 2.
- Na alternativa 1: qual p usar, como a constante nomeada que a spec pede, e o que fazer quando o p medido sai
  indefinido ou negativo.
- PENDING_CONFIRMATION, ramo de um eixo só: a spec §4.3 diz que ele "continua com o passo"; o código de hoje usa a
  `_resolucao` (o d1 do eixo que satura; o passo só quando um eixo satura numa das duas grades e não na outra).
  Manter a `_resolucao`, como o código faz, ou passar a usar o passo, como a spec diz ao pé da letra?
- Se o estudo deve crescer antes da decisão: a alternativa 3 na varredura perto do neutro, mais casos na janela de
  +4,84 % a +4,86 %, as formas da V4.3, ou uma grade h/16 para fechar a dúvida sobre as violações de (c) e sobre o
  sinal dentro da janela.
