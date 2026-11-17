# Resposta: verificação e evidência contra as conclusões

Rótulos: [F] fato de fonte (relatório citado); [C] resultado de código rodado agora (scripts e saídas em
`conselho/assento5_trabalho/`, v1 a v5); [K] cálculo; [I] inferência; [H] hipótese.

## Q1. O método atual é adequado?

Não, e os relatórios ainda subestimam o problema. Há três erros nos próprios números de partida:

1. **A variação de MR da v20 não é 5,2 %.** Esse valor também depende da resolução: com 11 pontos dá 4,00 %, com 25
   dá 5,19 %, com 51 dá 5,70 % e com 201 dá 6,08 % [C v2]. A derivada local em dz = +62,4 é 1,469, contra o mínimo
   1,384 [C v2]. O valor convergido fica perto de 6,1 a 6,2 %, ou seja, 50 % acima do limite de 4 %. O achado 1 do
   REGISTRO está certo na direção e errado no número.
2. **A folga ao aro é medida no segmento errado.** `corner()` faz `P['PO'] = P['UO']`, e o `kinlib.pose` gira PO com
   a bandeja superior. Com `ARM='L'`, `rim_clearance(s, A)` mede então o segmento rótula superior → rocker, não o
   push rod real O → A [C v1]. O "19,9 mm com rack ±30" do REGISTRO (achado 4) e o `diag.py` herdam o erro. No
   segmento real, a folga mínima é 44,8 mm [C v1]. Aqui o erro foi conservador, mas é um **bug de restrição**: em
   outra geometria ele pode aprovar o que bate. O ponto O fica a 67 mm do eixo da roda, 58 mm para dentro [C v1].
   Essa é a zona da manga e do freio (freio em volta do cubo [F REGISTRO]), que o script não modela.
3. **A v20 está em cima das fronteiras, não dentro.** O curso mínimo do amortecedor é 148,94 mm, contra 149 de
   limite [C v2]. Com perturbação de ±1 mm no pivô e de ±0,5 mm/° nos braços e ângulos, a v20 viola cada restrição em
   cerca de metade das 40 amostras: pernas 19, erro ao FH 19, Lsmin 23 e MRvar 22 [C v5]. Uma aprovação que não
   resiste à tolerância de fabricação não é aprovação.

Também estão certos o "fim no FBH" que cai no ar, 44,7 mm fora do quadro [F GEO §6c], e a coplanaridade só no
estático, com até 4,58° [C diag].

## Evidência contra a conclusão mais atraente

A conclusão mais atraente é: "reformular (eliminar as igualdades, usar restrições explícitas, fase I/II, multi-start)
resolve a força bruta sem solução", com confiança "alta" [F LIT §0]. Minha amostra aleatória de 2000 pontos numa
caixa em torno da v20 dá [C v4]:

- 0 pontos viáveis;
- 1 viável sem a meta de MR;
- 28 viáveis sem MR e sem as duas restrições de curso;
- 123 viáveis sem MR, curso e erro ao FH.

Isso apoia o achado 6 (quase-igualdades estrangulam o espaço). Mas os motivos do Murilo ("perto de um nó", "sem nó
na outra ponta", "saía do chassi") apontam para outra explicação, mais simples. Entre o FH e o FBH, abaixo dos braces,
**não existe nó**: o nó triangulado mais próximo do pivô está a 237 mm [F GEO §3, §6a]. Uma restrição de nó contra um
conjunto de nós vazio dá conjunto viável vazio para qualquer algoritmo [I].

O código da força bruta e o número 1,1 milhão não estão disponíveis: não dá para reproduzir [H]. A confiança "alta"
do LIT vem de teoria geral, sem precedente para este caso; ele mesmo admite isso [F LIT §0, item 4 do "contra"]. Eu
a rebaixo para média.

Os demais relatórios conferem. A tabela de flexão do LIT bate com F·a·b²/L² (53, 142 e 212 MPa) [K]. A derivação
Ke ≥ RR(1−p)/p está correta [K]. A figura confirma os chanfros nos quatro cantos do gabarito [F REGRAS §2.3]. Ressalva
minha: para peças em |Y| > 175 mm, que é o caso de todo o rocker da v20, o gabarito nem toca; a margem é de 30,6 mm
[C v3]. A discussão da altura livre (D5) só importa para peças internas.

## Q2. Método e arquitetura

Separar **gerador** de **verificador**:

- O gerador pode ser qualquer um: enumeração de nós candidatos com multi-start local, ou o OptimumK.
- Quem aprova é só um verificador independente e determinístico, com estas regras:
  1. Restrições duras como desigualdades com **margem explícita** (tolerância de fabricação), nunca "custo ≈ 0".
  2. Avaliação no envelope inteiro (curso × cremalheira com curso real × rolagem), com **convergência de resolução
     provada**: n e 2n pontos dão o mesmo veredito.
  3. Robustez por Monte Carlo de tolerâncias: o candidato aprovado tem de passar em todas as amostras.
  4. Cada restrição testa a peça real (o bug do aro mostra o risco).
- Objetivos (MR, linearidade, ângulos, flexão no tubo) ficam fora das duras.
- A saída é um certificado por candidato, com estes campos:
  - a margem de cada restrição;
  - o SHA do STEP;
  - a lista do que **não** foi modelado: manga, freio, coluna, pedais, pernas da LCA, AIP.
  - "Viável" quer dizer "viável contra o modelado", nunca "válido".

## Q3. Uso do CAD

- Nós e tubos saem do STEP pelo `step_tubos.py` [F GEO], com teste de regressão sobre um STEP sintético de nós
  conhecidos.
- O critério "triangulado" é geométrico e tem artefato (N25/N27) [F GEO §7]: não serve para aprovar estrutura. O
  esforço no tubo receptor tem de vir de cálculo (Pynite ou viga).
- O Z da transformação depende só do FH [F GEO §5]. Até existir um ponto de referência nomeado no CAD, todo
  resultado em Z sai rotulado como condicional.
- Tubos que faltam entram como "nós propostos", isto é, pedidos ao chassi, e não como hipótese silenciosa.

## Q4. Coordenação

- Contrato de interface versionado: hardpoints e nós com nome e SHA do STEP.
- A suspensão emite pedidos de nó, cada um com carga e envelope. O chassi aceita ou recusa.
- Toda nova versão do STEP roda o verificador de novo sobre todos os candidatos aprovados (regressão), e o
  resultado é publicado como diff.
- Ninguém altera limite para "passar": a mudança de limite é decisão registrada.

## Q5. Riscos e o teste que derrubaria a recomendação

Riscos:

1. O kinlib nunca foi comparado com a REFERENCE (OptimumK, EDR-004). Os resíduos internos são de 10⁻¹² a 10⁻¹⁴
   [C v2], mas isso prova consistência, não correção.
2. Envelopes não modelados (freio, manga) invalidam aprovações.
3. O conjunto viável pode ser vazio de fato.

Testes, em ordem:

- **(a) Kinlib contra a referência.** Comparar no OptimumK, ou no open-kinematics como segundo modelo [F PRÁTICA §2],
  as curvas de MR, camber e toe da v20. Divergência acima da tolerância derruba tudo o que vem depois.
- **(b) Casos de resposta conhecida.** Um rocker planar com MR analítico e um caso de colisão forçada. Mutação: o
  verificador tem de reprovar 100 % das violações injetadas, como já se faz no projeto.
- **(c) Fase I sobre o CAD atual.** Se der vazio só por falta de nó, a prioridade passa a ser o chassi propor a caixa
  dianteira, não o algoritmo.
- **(d) Finalistas.** Interferência exata (OCC ou Fusion) com o CAD completo.

Nada disso é validação física: VERIFIED ≠ validado.

**Recomendação em uma frase:** adotar arquitetura gerador + verificador independente, em que só aprova o que passa
em restrições duras com margem, em resolução convergida, sob Monte Carlo de tolerâncias e com certificado do que não
foi modelado; antes de otimizar, conferir o kinlib contra a referência e rodar a fase I para saber se falta nó no
chassi ou falta método.

**Confiança e principal incerteza:** média. A principal incerteza é se a falha da força bruta vem da formulação ou
da ausência de nós na caixa dianteira (o código e os dados do Murilo não estão disponíveis), e se o kinlib bate com
a REFERENCE.
