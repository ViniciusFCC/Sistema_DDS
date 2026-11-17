# Revisão anônima (rodada 2)

## 1. Por letra

**A**
- **Mais grave:** quase não trata de viabilidade nem de estrutura. Delega a formulação. O "CSV no schema de hardpoints"
  resolve o rastreio, mas não diz se o candidato aguenta carga.
- **Mais forte:** dois achados novos e verificáveis.
  - O repositório já tem `kinematics_model.Corner` (76 checks) e `hardpoints.py`.
  - A cápsula de tubo quadrado com meia-largura superestima a folga em até 5,18 mm. Isso corrige o GEO e o PRÁTICA:
    aprovaria o que bate.

**B**
- **Mais grave:** a "chance de ~1e-6" multiplica taxas como se as restrições fossem independentes. É ordem de
  grandeza, não medida.
- **Mais forte:** prova por limites, sem busca, que "pivô e olhal em nós de hoje" é conjunto vazio, porque
  |Pv_x| ≤ 150 e os nós do FH estão em X = −202.
  - Mede o ganho da eliminação por construção: as quatro quase-igualdades juntas passam de 0/3000 para 16/1000.
  - Mostra a igualdade escondida 23 + 62,4 = 61 × 1,40.

**C**
- **Mais grave:** a "evidência contra" usa amostra numa caixa em torno da v20 e não separa a falta de nó da
  formulação. Fica no "pode ser os dois", sem o teste que decide.
- **Mais forte:** variação de MR convergida em ~6,1 %, contra 5,2 % e 4,0 %. E concorda de forma independente (341
  pontos).
  - Achou o bug do aro.
  - Monte Carlo mostra que a v20 viola cada restrição em cerca de metade das amostras com ±1 mm.
  - Arquitetura gerador × verificador com convergência de resolução e certificado do que não foi modelado.

**D**
- **Mais grave:** mantém o `kinlib` como "ativo" sem validação, quando A mostra um módulo testado no repositório e C
  e E acham bugs nele.
  - "Congelar a partir de julho de 2027" é uma data sem fonte.
- **Mais forte:** com o MR imposto por construção, ainda não há solução viável. Ela só aparece ao soltar os 4 % de
  variação.
  - O desbloqueio é, então, decisão da equipe (MR × curso inteiro do DNM). O teste de 1 h com 50 sementes é barato e
    decisivo.

**E**
- **Mais grave:** o "eixo a 74° que zera a carga axial" é linearização de 1ª ordem num só ponto. Ele vira veto de
  conceito sem conferir a carga axial que o conceito B, de fato, produziria.
- **Mais forte:** o MR é regressivo no fim do bump (taxa na roda ~−9 a −11 %, conferi pelos MR citados). Os 90°
  estáticos ficam a 27 % do curso, com 47° no bump. Expõe a troca de conceito, eixo do rocker × direção do
  amortecedor, que nenhuma busca resolve.

**F**
- **Mais grave:** todos os números estruturais são por kN, sem envelope do T11.
  - O pórtico próprio só foi conferido à mão (±10 %).
  - A ride rate admissível (10 a 64 N/mm) depende de um p = 5 % ilustrativo.
  - Não trata a cinemática nem a colisão.
- **Mais forte:** quantifica que a v20 não é estruturalmente aprovável, com 145 a 393 MPa por kN no Q–E e pontas sem
  nó.
  - Troca "distância ao nó" por tensão e rigidez (Ke) com matriz de influência barata no laço.
  - Mostra que pivô e olhal no mesmo subconjunto fecham a força do amortecedor localmente.

**G**
- **Mais grave:** a parte do método é emprestada do LIT. "δ = 0,5 mm → 0 % cumpre" repete o resultado de margem zero,
  sem uma proposta de margem.
- **Mais forte:** `X_FIM = 350` implica pedal em X 450, o que deixa 32 mm até a face do FBH contra os 25 mm do F.8.6.3.
  - A procedência de cada restrição (REGRA, MARGEM, PREFERÊNCIA) e o "kit de fixação" fabricável e acessível são o
    que torna o "aprovado" defensável na inspeção.

## 2. Ranking

RANKING: B > C > E > A > F > G > D

## 3. Divergências para o presidente decidir

1. **Base da cinemática.**
   - D mantém o `kinlib`; A migra para o `Corner` do repositório; C e E querem validar primeiro.
   - Posição: comparar `kinlib` × `Corner` × OptimumK na v20, construir sobre o módulo testado e aposentar o `kinlib`.
     Ele já teve um bug de segmento.
2. **Causa da força bruta sem solução.**
   - B e D dizem quase-igualdades e conflito de metas; C e F dizem falta de nó no CAD.
   - Posição: as duas são reais e independentes. B prova o vazio com os nós atuais e D mostra conflito MR × curso
     mesmo sem o tubo.
   - A fase I sobre o esqueleto obrigatório (F.6.2.3) separa as duas. A primeira decisão é da equipe: MR ≤ 4 % com o
     curso inteiro do DNM.
3. **Critério do nó.**
   - Objetivo ou filtro "distância ao nó" (D, E) contra tensão e Ke calculados (F, G, C).
   - Posição: tensão e Ke. A distância ao nó só entra no relatório, porque não há número em regra nem em literatura.
4. **Estrutura no laço ou só nos finalistas** (F contra D).
   - Posição: matriz de influência do pórtico no laço, como restrição dura, assim que existir o envelope de cargas do
     T11. Até lá, só no relatório. FEA de casca só nos finalistas.
5. **Raio da cápsula de tubo quadrado** (meia-largura no GEO e no PRÁTICA, raio envolvente em A).
   - Posição: raio envolvente na busca e BRep exato no verificador. O conceito de E (direção do amortecedor × carga
     axial) também deve ser decisão explícita da equipe antes da busca.
