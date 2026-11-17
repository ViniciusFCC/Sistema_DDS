# Revisão anônima (rodada 2)

Critério: utilidade para o objetivo do usuário, que é um script cujas aprovações sejam válidas. Peso a correção
técnica, a evidência medida e o custo de adotar a ideia numa equipe estudante com prazo.

## 1. Avaliação por letra

**A**
- Fraqueza: propõe trocar a cinemática pelo `kinematics_model.Corner` antes de compará-lo com o `kinlib`. O próprio
  teste 5 que A propõe deveria vir antes da recomendação. Os 5 módulos também custam caro antes de a Fase I responder.
- Ponto forte: mediu que a cápsula com meia largura superestima a folga do tubo quadrado em até 5,18 mm, ou seja,
  aprova o que bate. Também achou o `Corner` e o `hardpoints.py` já testados no repositório (76 e 35 checks).

**B**
- Fraqueza: aceita os 5,2 % de variação de MR (C e E mostram cerca de 6,1 % convergido) e não pega o bug do aro. O
  branch-and-bound para provar o vazio é excesso para o prazo.
- Ponto forte: é o argumento mais completo e medido.
  - O produto das taxas das restrições dá cerca de 1e-6, o que explica o 1,1 milhão sem solução.
  - Com as construções, a viabilidade conjunta sobe de 0/3000 para 16/1000.
  - Mostra por limites, sem busca, que "pivô em nó existente" é vazio: os nós estão em X −202 e o script exige
    |Pv_x| ≤ 150.

**C**
- Fraqueza: diz pouco sobre como gerar candidatos e usar o CAD. O Monte Carlo de tolerâncias como aprovação ainda não
  tem δ medido.
- Ponto forte:
  - o bug do aro, confirmado na Correção (44,8 mm no segmento real);
  - a variação de MR que muda com a malha (4,00 / 5,19 / 6,08 % com 11 / 25 / 201 pontos);
  - a v20 viola cada restrição em cerca de metade das perturbações de ±1 mm;
  - a separação gerador × verificador.

**D**
- Fraqueza: recomenda manter o `avaliar` como ativo sem ver que ele tem o bug do aro e o MR grosso. Os "25 pontos de
  reavaliação" não bastam (o valor convergido é cerca de 6,1 %). Há uma contradição interna no custo do teste ("menos
  de uma hora" contra "≈ 3,5 h em um núcleo").
- Ponto forte: o LHS com o MR imposto por construção mostra que o vazio persiste mesmo sem a restrição do tubo. Daí a
  conclusão de que o primeiro desbloqueio é uma decisão da equipe sobre limites. Traz ainda a lista de dados
  bloqueantes com responsável.

**E**
- Fraqueza: fala pouco de CAD e de coordenação. Os conceitos A e B não foram testados em empacotamento.
- Ponto forte: acha um conflito de conceito escondido. O eixo que zera a carga axial fica a 74° do eixo da v20, o que
  exige o amortecedor a pelo menos 66° de X, contra o limite de 30°. Mostra também o MR regressivo (cerca de 11 % de
  taxa a menos no bump) e o push rod a 30,8 mm do tirante.

**F**
- Fraqueza: o pórtico no laço vem antes de existir o envelope de cargas do T11. Os 300 a 800 MPa usam carga de outro
  carro, e o material e a parede são supostos.
- Ponto forte: dá números de carga e flexão (145 a 393 MPa por kN no Q–E) que tornam o arranjo da v20 inviável como
  estrutura. A regra "pivô e olhal no mesmo subconjunto triangulado" é barata e útil.

**G**
- Fraqueza: a robustez como restrição dura com δ desconhecido, mais o kit de fabricação, amplia o escopo antes de
  existir um candidato viável.
- Ponto forte: a procedência de cada restrição (REGRA, MARGEM ou PREFERÊNCIA, com artigo). `X_FIM = 350` implica o
  pedal em X 450, o que deixa só 32 mm até o FBH.

## 2. Ranking

RANKING: B > C > A > E > F > G > D

## 3. Divergências para o presidente

1. **Base de código: refatorar o `kinlib`/`avaliar` (D), migrar para o `Corner` do repositório (A) ou corrigir o
   avaliador primeiro (E).** Minha posição mudou: comparar `kinlib` × `Corner` na v20 (MR e Ls nos 25 pontos). Se
   baterem, migrar para o `Corner` testado e deixar o `kinlib` só como conferência. Duas cinemáticas sem teste são um
   risco maior que o custo da migração.
2. **Causa raiz: quase-igualdades (B, D), falta de nós (C, F) ou conceito incompatível (E).** São as três, e em
   camadas. Proponho a ordem:
   1. o chassi esboça os membros obrigatórios da F.6.2.3, sem o que não há hospedeiro;
   2. as construções de B;
   3. a decisão de conceito de E, antes da busca.
3. **Estrutura no laço (F) ou só nos finalistas (A, D).** As cargas vetoriais saem em forma fechada e entram no laço,
   porque são baratas. O pórtico só entra depois do envelope de cargas do T11, e o teste do próprio F decide.
4. **Robustez e tolerância como restrição dura (C, E, G) ou margem fixa.** Dura, sim, mas com δ declarado como
   parâmetro "a medir" e rotulado. A margem de curso do amortecedor é obrigatória já: a v20 usa 100 % do curso.
5. **Raio da cápsula do tubo quadrado: meia largura (GEO, PRÁTICA) ou meia-diagonal (A).** Meia-diagonal, mais
   0,2 mm, com verificação BRep nos finalistas. O valor de A foi medido, e o oposto aprova colisão.
