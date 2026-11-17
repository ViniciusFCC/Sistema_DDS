# Revisão anônima (rodada 2)

## 1. Avaliação por letra

**A**
- *Mais grave:* fala pouco da cinemática. Propõe o `Corner` sem conferir se ele modela push rod na bandeja inferior.
- *Mais forte:* mediu cápsula contra BRep. A meia largura do tubo quadrado superestima a folga em até 5,18 mm. Achou `hardpoints.py` e `kinematics_model` no repositório.

**B**
- *Mais grave:* a prova de vazio por branch-and-bound é promessa, não demonstração.
- *Mais forte:* mediu o estrangulamento (0/3000 sem construção, 16/1000 com ela). Provou o vazio sem busca: |Pv_x| ≤ 150 exclui os nós do FH, em X = −202.

**C**
- *Mais grave:* a arquitetura do gerador fica genérica.
- *Mais forte:* convergência do MR (4,00 → 6,08 %), bug do aro (44,8 mm), Monte Carlo de ±1 mm (cerca de metade viola cada restrição). Separa "viável contra o modelado" de "válido".

**D**
- *Mais grave:* manda manter o `kinlib` e o `avaliar`, que têm o bug do aro. O teste reavalia em 25 pontos, o que ainda subestima o MR (5,2 contra 6,1 %).
- *Mais forte:* o MR por construção, com o limite de 4 % relaxado, dá 14 soluções. O vazio vira decisão da equipe. Sequência barata.

**E**
- *Mais grave:* tudo vem do `kinlib` não validado. A incompatibilidade é de 1ª ordem. O uso do CAD fica raso.
- *Mais forte:* é a única que mostra o conflito entre "amortecedor ≤ 30° de X" e a coplanaridade no curso (eixo ideal a 74°). Também traz o MR regressivo no fim do bump e os 90° fora do meio do curso.

**F**
- *Mais grave:* a escala para o T11 usa a carga de outro carro. O Q–E com as pontas no ar é um caso degenerado, então "inviável" vale para a v20, não para o método.
- *Mais forte:* cargas por kN (pivô 2,49), Ke, e a regra de pôr pivô e olhal no mesmo subconjunto, onde as componentes axiais quase se anulam. Troca a distância ao nó por σ e Ke.

**G**
- *Mais grave:* "pedal em X 450 é improvável" depende de dado que o T11 ainda não tem.
- *Mais forte:* procedência de cada restrição (regra, margem ou preferência), kit de fixação fabricável, nó que não é regra, e 0 % viável com δ = 0,5 mm.

## 2. Ranking

RANKING: B > C > A > E > F > G > D

## 3. Divergências para o presidente

1. **Causa do vazio:** formulação (B, D), falta de nós (C, F) ou conceito (E).
   - *Posição:* as três somam.
   - Rodar a fase I no STEP atual, com e sem nós propostos, para separá-las.
2. **Manter o `kinlib` (D) ou migrar para o `Corner` (A).**
   - *Posição:* migrar.
   - Antes, comparar `kinlib`, `Corner` e OptimumK na v20 (MR denso, Ls, ângulos).
3. **Estrutura no laço:** σ e Ke no laço (F) ou FEA só nos finalistas (D).
   - *Posição:* os vetores de reação sempre no laço, que são baratos.
   - σ e Ke no laço só se o teste de F, com cargas reais, mostrar que a estrutura decide.
4. **Conceito do rocker:** decisão prévia (E) ou variável do otimizador.
   - *Posição:* enumerar os dois conceitos.
   - O limite de carga axial e o sinal da curva de MR são decididos antes, pela equipe.
5. **Cápsula de tubo quadrado (meia largura ou diagonal) e δ (±1 ou 0,5 mm).**
   - *Posição:* raio envolvente na busca e aprovação só por verificador exato.
   - δ medido pela equipe, com margem de curso do amortecedor. A v20 (61,00 de 61 mm) reprova em qualquer δ.
