# Revisão anônima (rodada 2)

Conferi duas afirmações no código. A afirmação de A sobre o repositório é verdadeira: `python/kinematics_model.py`
tem `Corner`, `sweep`, `steer_sweep` e `motion_ratio`, e `hardpoints.py` tem `PUSH_OUT`, `ROCKER_AXIS_A/B` e
`SPRING_CHASSIS`. As contas de F também batem: Ke·p/(1−p) dá 10 e 64 N/mm com p = 5 %. As de E também: (1,384/1,468)²
dá 11 % de queda na taxa da roda.

## 1. Avaliação por resposta

**A.**
- Fraqueza: não avalia se existe solução viável. A troca do kinlib pelo `Corner` do repositório fica sem o teste de
  equivalência feito, só proposto.
- Ponto forte: dois achados verificados que ninguém mais viu:
  - o repositório já tem cinemática testada e um schema de hardpoints;
  - a cápsula do tubo quadrado com meia largura superestima a folga em até 5,18 mm contra o BRep, ou seja, aprova o
    que bate. Também propõe o teste de ida e volta do datum pelo STEP.

**B.**
- Fraqueza: a chance de 1e-6 vem do produto de taxas, o que supõe restrições independentes, e elas são acopladas
  (MR e curso).
- Ponto forte: prova o vazio sem busca. Com |Pv_x| ≤ 150, os nós do FH (X −202) e do FBH ficam fora. Também acha a
  igualdade escondida 23 + 62,4 = 61 × 1,40, e testa a construção (0/3000 vira 16/1000). Tem a arquitetura mais
  completa e põe o certificador como único que aprova.

**C.**
- Fraqueza: o argumento de "nenhum nó na zona" fica em inferência, quando os próprios limites do script davam a prova
  (B). Não diz o que fazer com carga nem com regra, e o Monte Carlo como critério depende de um δ que não existe.
- Ponto forte: o critério de aprovação é o mais operacional (convergência n × 2n, margem, mutação, "viável contra o
  modelado"). Corrige o MR para cerca de 6,1 % e o aro para 44,8 mm, e mostra a v20 caindo em cerca de metade das
  amostras com ±1 mm.

**D.**
- Fraquezas:
  - ainda cita 4,00 → 5,2 % (o convergido é cerca de 6,1 %);
  - manda manter o kinlib sem citar o bug do aro;
  - diz "menos de uma hora" e logo depois calcula 3,5 h.
- Ponto forte: o teste de derrubada mais barato e decisivo (tirar o tubo ao FH e rodar o Nelder-Mead com 50
  sementes). Também os dados bloqueantes, cada um com responsável.

**E.**
- Fraqueza: o eixo a 74° e o "≥ 66° do X" saem de primeira ordem no kinlib não validado e não foram mostrados com
  folga numérica. É uma conclusão de conceito forte apoiada num só cálculo.
- Ponto forte: a única que mostra o sinal do MR, regressivo (taxa na roda cai cerca de 11 % no fim do bump). Mostra
  também os 90° a 27 % do curso e o conflito "mesmo plano" × "amortecedor para a frente", que nenhuma busca resolve.

**F.**
- Fraqueza: a escala absoluta (300 a 800 MPa) usa a carga de outro carro, e o p = 5 % é ilustrativo. Põe um pórtico
  no laço antes de existir o envelope de cargas do T11.
- Ponto forte: troca "perto do nó" por tensão e Ke com números: de 145 a 393 MPa por kN, e RR admissível de 10 a
  64 N/mm. Dá o princípio de fechar a força do amortecedor no mesmo subconjunto triangulado.

**G.**
- Fraqueza: dá peso ao gabarito, que não toca nenhuma peça da v20 (|Y| > 175; margem de 30,6 mm). O "nem
  conservador nem liberal" vale só para peças internas.
- Ponto forte: mostra 0 % viável com δ = 0,5 mm. Mostra também que `X_FIM = 350` implica pedal a 32 mm do FBH,
  incompatível com F.8.6.3. Propõe a procedência da restrição (REGRA, MARGEM, PREFERÊNCIA) e o estado NÃO
  VERIFICÁVEL, que impede "aprovado".

## 2. Ranking

RANKING: B > A > E > F > G > C > D

## 3. Divergências para o presidente

1. **Causa da "força bruta sem solução".** Uns dizem formulação (B, D), outros falta de nós (C, F) e outros conceito
   (E). Posição: as três somam. B prova o vazio nos nós de hoje, e o LHS mostra o estrangulamento pelas
   quase-igualdades. Decide-se com a fase I contra o esqueleto obrigatório F.6.2.3, antes de escolher algoritmo.
2. **Refatorar o kinlib (D) ou migrar para o `Corner` do repositório (A).** Posição: migrar, mas só depois de
   comparar kinlib × `Corner` × OptimumK na v20 (MR, camber, toe, Ls nos 25 pontos). O kinlib tem o bug do aro e
   estado global.
3. **Estrutura no laço (F) ou só nos finalistas (A, D).** Posição: no laço, a estática do rocker em forma fechada e
   uma viga ou matriz de influência barata, como restrição dura, assim que o envelope de cargas existir. FEA só nos
   finalistas.
4. **Robustez à tolerância como restrição dura (C, E, G).** Posição: obrigatória, porque a v20 cai com 0,5 a 1 mm. O
   δ entra rotulado "a confirmar" até ser medido no TX.
5. **Raio da cápsula do tubo quadrado** (A contra GEO e PRATICA). Posição: meia-diagonal mais 0,2 mm na busca, BRep
   exato no verificador. A meia largura é não conservadora e deve ser proibida.
