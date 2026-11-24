# Parte C: literatura sobre o método de posicionamento do push rod, do rocker e do amortecedor (T11, dianteira)

Data: 2026-11-17. Modo rigoroso: só trabalhos acadêmicos, livros técnicos e documentos oficiais. Fórum, blog e vídeo
serviram no máximo para achar a fonte primária e não entram como evidência.

Rótulos usados:
- **[F]**: fato tirado de uma fonte. A tabela do fim diz onde foi conferido.
- **[I]**: inferência minha a partir das fontes ou do REGISTRO.
- **[H]**: hipótese ainda não testada.

Limitações desta rodada (leia antes de usar):
- Os créditos do Firecrawl acabaram no meio da pesquisa. Daí em diante usei Crossref, Semantic Scholar e OpenAlex,
  além de busca web e leitura direta de PDFs. A OpenAlex e a Semantic Scholar também bloquearam por limite de uso.
- Vários repositórios recusaram o acesso automático (HTTP 403): skemman.is, scholarworks.calstate.edu,
  upcommons.upc.edu, espace.library.uq.edu.au, SSRN e Springer. Os trabalhos que estão nesses repositórios aparecem
  aqui só pelos metadados ou pelo resumo.
- Os livros (Milliken, Seward, Dixon, Smith, Staniforth, Reimpell) não estão nesta máquina: `references/` só tem o
  `INDEX.md`.
  - Os números de página de Milliken e Seward citados abaixo foram conferidos **pelo projeto**, na imagem da página
    (`docs/revisao-metodologica.md`). Não os reconferi.
  - Do Dixon e dos capítulos do Seward conferi só título e paginação, pelo Crossref.
  - Smith, Staniforth e Reimpell **não foram verificados**.

---

## 0. Resposta à pergunta central

### Método recomendado

A recomendação é reformular o problema, não só trocar o algoritmo. Em ordem:

1. **Tirar as quase-igualdades do espaço de busca por construção.** A forma do problema é o que faz a força bruta e o
   Nelder-Mead falharem, mais do que o algoritmo [I].
   - Quem já resolve isso por construção: o plano do rocker passando pela junta e pela perpendicularidade do push rod
     (o script já faz); a razão entre os braços do rocker, tirada do MR-alvo; o comprimento estendido e o curso,
     escolhidos num catálogo de amortecedores.
   - O que vira variável discreta: o ponto do amortecedor no chassi e o pivô do rocker passam a ser escolhidos numa
     lista de nós e tubos candidatos, tirados do STEP. Para o pivô entra também uma posição contínua ao longo do tubo.
   - Base: eliminação de variáveis (Nocedal & Wright 1999, §15.2, p. 424-432; GENOCOP em Coello 2002, p. 1259)
     [F].
2. **Restrições explícitas, não penalidade com tolerância fixa.**
   - Cada limite vira uma desigualdade normalizada g_i(x) ≤ 0. O problema é resolvido com um solver de restrições:
     SQP ou pontos interiores quando a avaliação é suave; quando não é, um método sem derivada com regras de
     viabilidade.
   - Um mínimo de penalidade quadrática com parâmetro fixo costuma ser inviável. A viabilidade só chega no limite em
     que a penalidade cresce sem fim (Nocedal & Wright 1999, p. 490). Isso combina com os achados 1 e 2 do REGISTRO:
     restrições exatamente no limite e MR fora do limite na avaliação fina [F + I].
3. **Viabilidade primeiro, desempenho depois** (duas fases).
   - Fase I: minimizar a violação normalizada, que diz também quais restrições não se satisfazem juntas.
   - Fase II: otimizar o desempenho só entre os pontos viáveis.
   - Base: regras de Deb e algoritmos de duas fases (Coello 2002, p. 1263); o mesmo esquema aplicado a duplo A em
     Arshad et al. 2025 [F].
4. **Busca global por enumeração e multi-start.**
   - Enumera as combinações discretas: par de nós, braço da bandeja (`ARM`), lado do rocker (`LADO_ROCKER`).
   - Para cada combinação, parte de vários pontos (amostragem por hipercubo latino, LHS) com o solver local da fase
     II.
   - Base: Nocedal & Wright 1999, p. 9 ("global optimization algorithms proceed by solving a sequence of local
     optimization problems"); Ugray et al. 2007, só pelos metadados [F].
5. **Entregar uma lista de candidatos viáveis, não um ótimo único.**
   - A saída é um conjunto não dominado, com MR, linearidade, ângulos, folgas e flexão no tubo receptor, para a
     equipe decidir. Isso é síntese multiobjetivo, como em Sancibrian et al. 2010 e NSGA-II [F].
   - O OptimumKinematics, a REFERENCE do projeto, resolve esse mesmo problema com algoritmo genético, objetivos
     ponderados e **volumes de busca esféricos rígidos** em torno dos pontos (OptimumG, estudo de caso) [F].
6. **Colisão por cápsulas, varrendo curso e esterço; interferência exata no CAD só nos finalistas.**
   - Tubos e barras viram cápsulas, isto é, segmentos inflados por um raio (Larsen et al. 2000, linha varrida por
     esfera).
   - Cagan et al. 2002: aproximação grosseira no início da busca e exata no fim.
   - Peixoto 2026 conferiu a folga ao longo do curso no NX Motion, só na geometria final [F].
7. **Trocar "perto do nó" por um critério de esforço.**
   - Do lado da roda: força no push rod pelo equilíbrio de seis barras de duas forças (Peixoto 2026, Ap. E).
   - No rocker: estática do rocker [I].
   - No tubo receptor: flexão pela distância ao nó.
   - Na fixação: rigidez exigida por Ke ≥ RR(1 − p)/p (Peixoto 2026, eq. 7.1) [F].

### Nível de confiança

- **Alto** que a reformulação dos itens 1 a 3 resolve a falha "1,1 milhão de combinações sem solução" ou, se o
  conjunto viável for vazio, a torna diagnosticável. É resultado geral de otimização com restrições, com precedentes em
  suspensão. Mas nenhum artigo trata exatamente o caso push rod–rocker–amortecedor com nós de chassi.
- **Médio** quanto à escolha do solver local (SQP × método sem derivada):
  - Depende de a avaliação continuar suave depois de trocar o "1e6 quando a cinemática falha" por uma restrição.
  - Depende também de a colisão entrar como distância contínua (cápsulas) e não como sim/não.
- **Baixo** sobre qualquer regra numérica de distância máxima ao nó: não achei nenhuma na literatura.

### Quando outro método venceria

1. **Avaliação caixa-preta, descontínua ou com CAD no laço**: interferência exata do Fusion ou cinemática que falha
   em partes do espaço.
   - Vencem os métodos populacionais sem derivada (algoritmo genético, evolução diferencial, CMA-ES) com regras de
     viabilidade de Deb.
   - É o caminho do OptimumKinematics (algoritmo genético) e de Borowski & Rudolph 2025 (enxame de partículas com
     detecção de colisão 3D) [F].
2. **Conjunto viável vazio.** Pelos relatos (a) a (e) do script de atuação, é provável [H]. Nenhum algoritmo resolve.
   - O produto útil passa a ser a fase I: a solução de menor violação e a lista das restrições em conflito.
   - Com isso a equipe decide o que relaxar: tolerância do MR, curso, gabarito, ou um nó novo no chassi.
3. **Chassi ainda livre.** Se a equipe aceita mover ou criar nós, o problema vira codesign (seção 5).
   - Formulação bi-nível: a suspensão escolhe pontos e o chassi oferece nós com um custo (massa, número de tubos).
   - Ou a otimização conjunta de nós e pontos (patente Purdue/Ramani; Zhu et al. 2009 para layout com topologia)
     [F].
4. **A equipe quer só um "bom o bastante" rápido a partir da v20.**
   - O Nelder-Mead atual com penalidade crescente (continuação) e várias sementes pode bastar. A penalidade crescente
     é o que o TrajOpt faz (Schulman et al. 2014) e o que Nocedal & Wright descrevem no Framework 17.1 [F].
   - Coello 2002 (p. 1279) recomenda começar por penalidade e passar a técnicas que separam restrição e objetivo só em
     espaços muito restritos [F]. Pelo REGISTRO, o caso atual é exatamente um espaço muito restrito.

---

## Diagnóstico do método atual à luz da literatura

| Característica do script (REGISTRO) | O que a literatura diz | Efeito esperado |
|---|---|---|
| Custo = Σ(violação/tolerância)², tolerância fixa | O minimizador da penalidade quadrática fica em geral inviável e só se aproxima da viabilidade quando o parâmetro cresce sem limite (N&W 1999, §17.1, p. 490) [F] | Restrições paradas no limite e MR de 5,2 % > 4 % na avaliação fina (achados 1 e 2) [I] |
| Penalidade do tipo max(0, g)² | Tem 2ª derivada descontínua (N&W 1999, Exercício 17.1) [F]; a Hessiana fica mal condicionada quando o peso cresce (p. 493) [F] | Dificulta qualquer método local [I] |
| Custo 1e6 quando a cinemática falha | Descontinuidade; "death penalty" sem informação de distância ao viável. Richardson et al., via Coello 2002 p. 1249: penalidades que dependem da distância à viabilidade funcionam melhor que as que só contam violações [F] | O simplex não sabe para onde voltar [I] |
| Nelder-Mead local a partir de uma semente | O NM pode convergir para um ponto **não estacionário** mesmo em funções suaves e estritamente convexas de 2 variáveis (McKinnon 1998, resumo) [F]; métodos determinísticos locais tendem a ótimos locais ruins em layout 3D (Cagan et al., preprint, p. 21) [F] | Depende da semente; nenhuma garantia [I] |
| Várias quase-igualdades (MR ±0,01; Ls ±1 mm; 90°; distância ao FH ≤ 8 mm em 2 condições) | Penalidade mal escolhida faz o algoritmo convergir para ponto inviável (peso baixo) ou viável ruim (peso alto) (Coello 2002, p. 1251) [F]; com poucas soluções viáveis, penalidades que só contam violações "are not likely to produce any solutions" (Richardson, via Coello p. 1249) [F] | Conjunto viável de medida quase nula em 8D; a força bruta não acha nada (achado 6) [I/H] |
| Perpendicularidade amortecedor–braço imposta no estático | Peixoto 2026, §6.3.2, p. 123: a condição de 90° só vale em uma posição; colocá-la no meio do intervalo varrido (não no estático) reduz a variação do MR, porque d(sen θ)/dθ = 0 em 90° [F] | Muda a restrição de 90° de "no estático" para "no meio do curso", o que alivia a variação do MR [I] |
| Coplanaridade só no estático | O OptimumKinematics trata o ângulo push rod–plano do rocker como objetivo a zerar "to reduce pivot bending moments" (OptimumG) [F] | O achado 3 (até 4,6°, cerca de 8 % de carga lateral) deve entrar como restrição ou objetivo **ao longo do curso**, não só no estático [I] |

Precedente a favor do método atual: Hwang & Shih (1987) sintetizaram a curva de *leverage ratio* da suspensão de
moto com um "constrained flexible polyhedron method", da família do Nelder-Mead [F, resumo]. Métodos de simplex
funcionam em problemas pequenos com boa semente. O problema do T11 não é o simplex em si: é a forma do custo e das
restrições [I].

**Diagnóstico recomendado antes de reescrever** [I]:
1. Amostrar o espaço por hipercubo latino (McKay et al. 1979).
2. Para cada amostra, registrar **quais** restrições viola.
3. Fazer a matriz de coocorrência das restrições satisfeitas.

Se duas restrições nunca são satisfeitas juntas em nenhuma amostra, o conflito é de projeto e não de algoritmo. É a
mesma informação que a fase I dá, sem otimizador.

---

## 1. Projeto do conjunto push/pull rod, rocker e amortecedor

**Motion ratio e installation ratio.**
- [F] As duas fontes clássicas usam razões **inversas** (conferido pelo projeto na imagem; `docs/revisao-metodologica.md`,
  linha SUS-201):
  - Seward 2014, eq. 4.6, p. 101: R_m = roda/mola.
  - Milliken & Milliken 1995, p. 595-596: IR = mola/roda.
- [F] Milliken p. 596: K_W = F_s·dIR/dδ + K_s·IR². O primeiro termo é a taxa geométrica da progressividade. O projeto
  conferiu, e o omite por hipótese (SUS-202).
- [F] O EDR do projeto registra que nenhuma das fontes consultadas (Milliken, Gillespie, Seward, Pacejka, helps do
  OptimumKinematics e do Adams) dá limiar de MR (`docs/Engineering_Decision_Register.md`, linha 676).
- [F] Dixon 2009 tem um capítulo inteiro sobre isso: "Installation Ratios", cap. 14, p. 271-298 (Crossref). O conteúdo
  não foi lido.

**Linearidade e progressividade.**
- [F] Peixoto 2026, §2.2.10, p. 16-18, citando Trzesniowski 2023, Milliken e Seward:
  - O MR não é constante ao longo do curso.
  - Um rocker não linear serve para quem quer taxa progressiva, mas "a smooth and nearly linear response is normally
    preferred in the early stages of the design".
  - Pequenas mudanças no rocker, no ponto do push rod ou na inclinação do amortecedor mudam muito a rigidez na roda,
    porque WR = K/MR².
- [I] Daí o critério do script, "variação do MR ≤ 4 %", ser escolha da equipe e não da literatura. O valor tem de
  ficar "a confirmar" com a fonte do T11.

**Ângulo de transmissão.**
- [F] Peixoto 2026, §6.3.2, p. 123:
  - Cada barra é posta perpendicular ao seu braço no estático. O braço efetivo é r·sen θ, e sen θ é estacionário em
    90°, o que dá a menor sensibilidade do MR ao giro.
  - Isso afasta o mecanismo do alinhamento barra–braço, em que o momento colapsa.
  - O autor reconhece que pôr os 90° no meio do intervalo varrido daria menor variação do MR.
- [F] Mecanismos planares clássicos (Shigley/Uicker, Norton) dão faixas de ângulo de transmissão aceitável. Não
  verifiquei nenhuma delas: **não verificado**.

**Giro do rocker.**
- [F] Peixoto 2026, §6.2.1, p. 120: o curso total da roda corresponde a cerca de 48° de giro do bellcrank nos dois
  eixos. É um caso, não uma regra.

**Plano do rocker e cargas fora do plano.**
- [F] Peixoto 2026, p. 120: os dois pontos do push rod ficam no plano normal ao eixo do pivô, então a força do push
  rod não tem componente axial na geometria nominal, e os rolamentos só localizam axialmente.
- [F] OptimumG: um dos objetivos da otimização é zerar o ângulo push rod–plano do rocker "to reduce pivot bending
  moments", e outro é reduzir o ângulo rocker–amortecedor "to limit pivot loads".
- [I] A literatura trata o desvio do plano como objetivo, não como restrição com número. O limite tem de ser decisão
  da equipe, a partir da carga lateral resultante no pivô.

**Fixação do push rod: bandeja ou manga.**
- [F] Na literatura acadêmica verificada só achei o modelo usual:
  - Peixoto 2026, Ap. E.4, p. 195: o push rod é uma barra de duas forças presa à manga.
  - Os seis membros da manga formam um sistema determinado de 6 equações.
- [F] Os argumentos "na manga alivia a flexão da bandeja" e "o tirante reage parte do momento" só apareceram em
  fóruns (Eng-Tips, F1Technical). Não entram como evidência.
- **Não verificado** em Seward cap. 3 ("Suspension links", p. 61-89) nem em Smith ou Staniforth.
- [I] Com o push rod na bandeja, "apontado para a junta, a 35 mm dela" como no script, a bandeja inferior passa a
  trabalhar em flexão nessa distância. O modelo de seis barras de duas forças deixa de valer exatamente para ela.

**Cargas no push rod a partir da carga na roda.**
- [F] Peixoto 2026, Ap. E:
  - Para cada canto e caso de carga, resolve-se A·T = −[F_c; r_c×F_c + M_c], com A montada pelos unitários u_j das
    seis barras e por p_j×u_j (eq. E.5, p. 195).
  - A força no push rod sai só da geometria externa, "independent of the rocker design".
  - O condicionamento de A, com as linhas de momento adimensionalizadas, é usado como checagem.
  - Razão força no push rod por carga vertical: 1,22 (dianteira) e 1,42 (traseira), Tab. 6.1, p. 116.
  - Força de projeto no push rod dianteiro: 2994 N (p. 117).

---

## 2. Métodos de síntese e otimização com restrições de empacotamento

### 2.1 Fundamentos

**Penalidade, barreira e Lagrangiano aumentado** (Nocedal & Wright 1999, cap. 17) [F]:
- A penalidade exterior só é viável no limite (p. 490).
- A Hessiana fica mal condicionada (p. 493).
- O método dos multiplicadores (§17.4) "tends to avoid the ill conditioning" (p. 493).
- O cap. 18 trata SQP.
- Para pontos interiores em programação não linear: Wächter & Biegler 2006 (IPOPT), só pelos metadados.

**Eliminação de variáveis** (N&W §15.2, p. 424-432) [F]:
- Eliminar igualdades dá um problema menor e mais fácil.
- O livro avisa (p. 425 e 431) que a eliminação "may alter the problem or introduce ill-conditioning" e "is not always
  beneficial if inequality constraints are present".
- Coello 2002, p. 1259: o GENOCOP elimina as igualdades junto com o mesmo número de variáveis e reduz o espaço de
  busca.

**Regras de viabilidade e duas fases** [F]:
- Deb 2000, via Coello 2002, p. 1263. O original não foi lido; as regras foram conferidas na descrição de Coello.
  1. Viável sempre vence inviável.
  2. Entre viáveis, vence o melhor objetivo.
  3. Entre inviáveis, vence a menor violação.
  - Não há fator de penalidade.
- CONGA e "behavioral memory" (Coello p. 1263): primeiro achar viáveis, depois refinar.

**Multi-start e global** [F]:
- N&W p. 9: algoritmos globais bem-sucedidos resolvem uma sequência de problemas locais.
- Só pelos metadados: Ugray et al. 2007 (scatter search com solvers NLP locais), Storn & Price 1997 (evolução
  diferencial), Deb et al. 2002 (NSGA-II).
- Hansen & Ostermeier 2001 (CMA-ES): resumo pelo Crossref.
- McKay et al. 1979 (LHS): só pelos metadados.

**Penalidade com coeficiente crescente funciona** [F]:
- O TrajOpt (Schulman et al. 2014, resumo) evita colisões com uma penalidade *hinge* cujos coeficientes "increase … in
  an outer loop as necessary", dentro de otimização convexa sequencial.
- A distância de colisão vem de checagem convexa.
- [I] É o análogo mais próximo de "folga entre cápsulas como restrição num solver de gradiente".

### 2.2 Aplicados a suspensão

| Trabalho | Método | Restrições | O que mostra |
|---|---|---|---|
| Sancibrian et al. 2010 (VSD) | síntese dimensional multiobjetivo de RSSR–SS, gradiente com Jacobiano exato | igualdade e desigualdade, tratadas pelo método [F, resumo] | gradiente com restrições explícitas funciona para duplo A |
| Arshad, Lodi & Liu 2025 (Mathematics) | fase 1: busca de viabilidade (QUBO + recozimento simulado); fase 2: SQP | fechamento de malha como igualdades exatas na fase 2 [F, texto completo] | o esquema "viabilidade primeiro" aplicado a duplo A. Ressalvas: os comparativos da Tab. 4 (algoritmo genético e enxame com RMSE de cerca de 20°, em 0,75 s) parecem linhas de base fracas, e os autores admitem que separar viabilidade e desempenho só vale com acoplamento moderado (p. 15) [I] |
| Yi, Park & Hong 2014 (SAE 2014-01-0394) | DoE para sensibilidade, divisão em dois subproblemas independentes, gradiente | metas de K&C [F, resumo] | decompor o problema pela sensibilidade acelera e estabiliza |
| Avi, Carboni & Stella Costa 2021 (SAE 2020-36-0154, Formula SAE, Brasil) | algoritmo genético, objetivos ponderados | não detalhado [F, resumo] | devolve uma solução "subótima, baseada nas funções-peso" |
| Borowski & Rudolph 2025 (SAE 2025-01-0270, Formula Student) | laço interno de cinemática e volta simulada; laço externo de forma 3D da barra anti-rolagem **com detecção de colisão 3D**; enxame de partículas multi-enxame | colisão 3D no laço [F, resumo] | o CAD/colisão no laço é viável, mas aplicado à barra, não ao rocker |
| Hwang & Shih 1987 (J. Chinese Soc. Mech. Eng.) | "constrained flexible polyhedron method with dynamic centroid" | curva de *leverage ratio* desejada [F, resumo na imagem da p. 43] | síntese de curva de razão por simplex com restrições: precedente do método atual |
| OptimumG, estudo de caso do OptimumKinematics (documento do fornecedor) | algoritmo genético (população 100, 200 gerações), 5 objetivos ponderados, "4 work like constraints" | volumes esféricos rígidos em torno do pivô e do ponto do push rod no rocker; folga de empacotamento [F, página lida] | o fluxo da REFERENCE do projeto: alvo de MR em heave ponderado para compressão, ângulo push rod–plano a zerar, comprimento do push rod mantido |
| Ventura Lecha 2025 (TFG UPC), via Peixoto 2026 p. 31-32 | DEFT-Funnel (sem derivada), escolhido porque as funções vêm de equações resolvidas numericamente | pontos do bellcrank otimizados para desacoplamento [F, fonte secundária] | otimização sem derivada do bellcrank em Formula Student |
| Thomas et al. 2022 (arXiv 2206.09022, preprint) | otimização bayesiana como "inversa generalizada"; critério de duas camadas: satisfaz tudo ou solução de norma mínima | especificações-alvo [F, resumo] | trata a satisfação das especificações como alvo e devolve a "menos inviável" quando não há solução |

[I] Nenhum trabalho verificado otimiza ao mesmo tempo o rocker e **os nós de um chassi tubular** com colisão. O caso do
T11 combina blocos que existem em separado.

---

## 3. Colisão e empacotamento com CAD

- [F] Cagan, Shimada & Yin 2002 (preprint de 2000, p. 21 e 24):
  - Em layout 3D é comum deixar os objetos se atravessarem e penalizar o grau de sobreposição para levar o projeto ao
    viável.
  - Como a interferência é calculada em toda iteração, a representação geométrica é decisiva.
  - Modelos de volume envolvente e de várias resoluções (*sphere tree*, *octree*, *OBB tree*) aproximam sem grande
    perda; a análise grosseira serve no início e a exata no fim.
- [F] Larsen et al. 2000: família de volumes "core primitive shape grown outward by some offset" (ponto, linha,
  retângulo), com algoritmos de distância exata e aproximada.
- [I] Linha varrida por esfera é a cápsula. Para tubos de raio conhecido, distância entre segmentos menos os raios dá a
  folga: exata para cápsula, conservadora para cilindro de ponta reta. É contínua e serve como restrição num solver.
- [F] Também disponíveis: GJK (Gilbert, Johnson & Keerthi 1988) para distância entre convexos; volumes varridos
  (Abdel-Malek et al. 2006). Os dois só pelos metadados.
- [F] Varredura ao longo do curso, na prática acadêmica de Formula Student: Peixoto 2026, §7.1.2, p. 139-141.
  - Folga verificada no NX Motion sobre o modelo integrado, percorrendo todo o curso. Nenhuma interferência.
  - Registrou as duas menores folgas: 2,5 mm (elemento de heave × bellcrank no rebound total) e 3 mm (bandeja superior
    × carcaça do motor no bump total).
  - Deixou as duas como restrições para revisões futuras, porque "neither is a local fix".
- [F] CAD no laço: Borowski & Rudolph 2025 executam "full 3D collision detection" dentro do laço de otimização, com
  geração automática de modelo por linguagens de projeto baseadas em grafos (resumo).
- [I] Para o T11:
  - Cápsulas no laço, varrendo curso × esterço.
  - Esterço com o curso real da cremalheira (hoje desconhecido: achado 4 do REGISTRO) ou, até lá, com envelope
    declarado "a confirmar".
  - Interferência exata pelo Fusion só nos candidatos finais.
- [I] O aro como cilindro 13" é hipótese herdada do TX e precisa entrar com origem. A manga, a pinça e o disco
  (freio dentro da roda) precisam de envelope próprio: o REGISTRO diz que hoje não entram.

---

## 4. Estrutura: cargas em nós triangulados

**Princípio.**
- [F] Waterman 2011 (TCC, UWA):
  - p. 9: numa treliça triangulada os membros ficam em tração ou compressão pura e não precisam ser
    superdimensionados para flexão.
  - p. 15: o chassi deve ser feito "so that bending moments are not introduced into any of the chassis members".
  - p. 28: "the A-arms do not mount directly to the nodes but are … mounted as close as is practical so that minimal
    bending is introduced into the chassis".
- [F] Schweighardt, Vehovszky & Feszty 2020 (Manufacturing Technology 20(1), p. 3 do artigo) dizem que, "according to
  the Formula Student rules", só nós podem ser pontos de entrada de força e de fixação dos dispositivos aerodinâmicos.
  É afirmação sobre o regulamento: **conferir na Parte D** (regulamento oficial).
- Seward 2014, cap. 2 ("Chassis structure", p. 33-60): **conteúdo não verificado nesta sessão**. Conferir no OCR local
  (`references/md/seward-rcd/`).

**Carga fora do nó, em ordem de grandeza** [I, cálculo meu].
Hipóteses: tubo de 25,4 mm com as paredes indicadas abaixo; vão de 400 mm engastado nos dois nós; força de 3 kN
perpendicular ao tubo. A força é da ordem da do push rod dianteiro de Peixoto (2994 N), mas a reação real no pivô do
rocker soma push rod e amortecedor e precisa ser calculada. Sem concentração de tensão na solda.
Fórmula de viga biengastada com carga concentrada: momento máximo F·a·b²/L² na extremidade mais próxima.

| distância ao nó a | parede 1,24 mm | 1,65 mm | 2,11 mm |
|---|---|---|---|
| 10 mm | 53 MPa | 42 MPa | 34 MPa |
| 30 mm | 142 MPa | 112 MPa | 93 MPa |
| 50 mm | 212 MPa | 167 MPa | 138 MPa |

Conclusão [I]: a distância "tolerável" depende da força, da parede, do vão e da fadiga. Um número fixo é arbitrário.
O script deve calcular a flexão no tubo receptor para o envelope de cargas e restringir a tensão e a deflexão.

**Regra de distância máxima ao nó.** Nenhuma fonte acadêmica verificada dá um número. Waterman diz "as close as is
practical". **Não encontrado.**

**Rigidez da fixação** [F] (Peixoto 2026, §7.2, p. 142):
- Com o caminho estrutural Ke em série com a ride rate RR: 1/RR_eff = 1/RR + 1/Ke, e ΔRR/RR ≈ RR/Ke.
- Para perda admissível p: Ke ≥ RR(1 − p)/p.
- Tab. 7.4, p. 143: o push rod responde por 86 % da flexibilidade axial das barras.
- [F] Bortoluzzi et al. 2016 (SAE 2016-36-0239, resumo): modelo de molas e modelo multicorpos com elementos finitos do
  chassi e da suspensão de Formula SAE.
  - Usado para fixar a meta de rigidez torcional e a geometria final dos pontos de fixação, evitando
    superdimensionamento.
  - Correlação com bancada de 98,2 % e 9 % a menos de massa.
- [F] Riley & George 2002 (SAE 2002-01-3300, resumo): caminhos de carga, meta de rigidez do chassi relativa às molas e
  à barra, e diretrizes de modelagem por elementos finitos.

**Cargas nas fixações a partir das cargas de roda** [F] (Peixoto 2026, Ap. E, p. 193-196):
- Cinco casos base: aceleração +1,6 g; frenagem −1,8 g; lateral 1,6 g; combinados (0,72; 0,72) e (−1,12; 1,12) g.
- Cada caso se repete com +1,5× a carga estática numa roda de cada vez, o que dá 25 casos. Os casos com bump numa roda
  governam o bellcrank.
- Equilíbrio da manga com seis barras de duas forças.
- As forças de cada ponto interno estão na Tab. 7.1, p. 139.
- [I] Os valores em g são do carro deles (FSFEUP03 e o protótipo novo), não do T11: o método se transfere, os números
  não.

---

## 5. Codesign chassi–suspensão

- [F] **US 7.725.299 B2** (Purdue Research Foundation; Ramani, Devanathan, Subramaniam, Cunningham, Peters; concedida
  em 2010-05-25):
  - Configuradores de chassi e de suspensão acoplados.
  - "The coupling between the chassis and the suspension configurators exists as suspension mounting points on the
    chassis", junto com as cargas de suspensão no chassi e a rigidez torcional do chassi sobre a suspensão.
  - O chassi sai de otimização topológica, esqueletização e otimização dos vértices.
  - "This problem lends itself to GA based optimization", com variáveis {r, θ, φ} por nó em relação à posição inicial.
  - Tubos limitados pelas regras de Formula SAE.
  - É documento oficial (patente), não revisado por pares.
- [F] Otimização integrada de layout de componentes e da topologia da estrutura de suporte:
  - Zhu, Zhang & Beckers 2009 (IJNME, resumo): componentes móveis com restrições de não sobreposição pelo "finite
    circle method", que aproxima cada componente por círculos (análogo 2D das cápsulas e esferas). Layout e topologia
    são otimizados juntos.
  - Continuação: Zhu et al. 2014 e 2016 (SMO), só pelos metadados.
- [F] Otimização simultânea de geometria (posição dos nós) e topologia de treliças: Achtziger 2007 (SMO), só pelos
  metadados.
- [F] Empacotamento automotivo bi-nível multiobjetivo: Dandurand et al. 2014 (SMO), só pelos metadados.
- [I] Para o T11, com o chassi incompleto, a forma mais simples que a literatura apoia é **bi-nível com biblioteca de
  nós candidatos**:
  1. O nível da suspensão escolhe entre os nós existentes (tirados do STEP) e "nós propostos": um ponto num tubo
     existente, que exige um tubo novo para triangular.
  2. Cada nó proposto carrega um custo (massa e número de tubos) e o tubo que precisa ser criado.
  3. O nível do chassi recebe a lista de nós propostos dos melhores candidatos.

  Otimizar nós e pontos juntos, como a patente faz, só compensa se a equipe aceitar que o otimizador mova a
  triangulação do chassi. Isso pede modelo estrutural (elementos finitos de barras) no laço: aumenta o custo e o
  risco [I].

---

## Evidência contra a abordagem recomendada

1. Coello 2002, p. 1279:
   - Para iniciantes, começar por penalidade estática ou dinâmica, "easiest to implement and … quite efficient".
   - A maioria dos estudos comparativos é inconclusiva, e o teorema "no free lunch" diz que a melhor técnica explora
     conhecimento do domínio [F].
   - A recomendação só se sustenta porque o espaço do T11 é muito restrito (achado 6) [I].
2. Busca de viabilidade pura amostra o viável quase ao acaso. Com região viável **disjunta**, pode cair num pedaço ruim
   sem sair dele (Coello 2002, p. 1267) [F]. A enumeração discreta e o multi-start existem para isso [I].
3. Eliminação de variáveis pode alterar o problema ou introduzir mau condicionamento, e nem sempre ajuda com
   desigualdades (N&W p. 425 e 431) [F]. Exemplo [I]: fixar 90° no estático elimina uma variável, mas piora a variação
   do MR (Peixoto p. 123).
4. Arshad et al. 2025 admitem que separar viabilidade e desempenho vale só com acoplamento moderado (p. 15) [F]. No
   rocker o acoplamento é forte: o MR depende dos mesmos pontos que a folga [I].
5. A REFERENCE do projeto (OptimumKinematics) usa algoritmo genético com objetivos ponderados, isto é, penalidade [F].
   Penalidade não é errada em si: o problema é o peso fixo com Nelder-Mead e quase-igualdades [I].
6. Métodos locais com gradiente param em ótimos locais ruins em layout 3D (Cagan et al., preprint p. 21) [F]. Por isso
   a busca global (enumeração e multi-start) é parte do método, não opcional [I].

---

## Tabela de referências e status de verificação

Status:
- **TC**: texto completo lido, nas páginas citadas.
- **R**: só resumo.
- **M**: só metadados (título, veículo, páginas).
- **P**: conferido pelo projeto em sessão anterior, na imagem da página.
- **S**: fonte secundária.
- **NV**: não verificado.

| # | Referência | DOI / URL | Status | Onde conferi |
|---|---|---|---|---|
| 1 | Nocedal, J.; Wright, S. J. *Numerical Optimization*. Springer, 1999 (1ª ed.) | ISBN 0-387-98793-2 | TC | p. 9; §15.2 p. 424-432; §17.1 p. 490 e 493; Exerc. 17.1. PDF da página de disciplina do IME-Unicamp |
| 2 | Coello Coello, C. A. (2002). Theoretical and numerical constraint-handling techniques used with evolutionary algorithms: a survey. *CMAME* 191(11-12):1245-1287 | 10.1016/S0045-7825(01)00323-1 | TC | p. 1246, 1249, 1251, 1259, 1263, 1267, 1279 |
| 3 | Deb, K. (2000). An efficient constraint handling method for genetic algorithms. *CMAME* 186(2-4):311-338 | 10.1016/S0045-7825(99)00389-8 | S | regras conferidas na descrição de Coello 2002, p. 1263 |
| 4 | McKinnon, K. I. M. (1998). Convergence of the Nelder–Mead simplex method to a nonstationary point. *SIAM J. Optim.* 9(1):148-158 | 10.1137/S1052623496303482 | R | resumo (OpenAlex) |
| 5 | Cagan, J.; Shimada, K.; Yin, S. (2002). A survey of computational approaches to three-dimensional layout problems. *Computer-Aided Design* 34(8):597-611 | 10.1016/S0010-4485(01)00109-9 | TC (preprint) | preprint de 2000, andrew.cmu.edu, p. 21 e 24 (paginação do preprint) |
| 6 | Sancibrian, R.; García, P.; Viadero, F.; Fernández, A.; De-Juan, A. (2010). Kinematic design of double-wishbone suspension systems using a multiobjective optimisation approach. *Vehicle System Dynamics* 48(7):793-813 | 10.1080/00423110903156574 | R | resumo (OpenAlex) |
| 7 | Arshad, M. W.; Lodi, S.; Liu, D. Q. (2025). An advanced hybrid optimization algorithm for vehicle suspension design using a QUBO-SQP framework. *Mathematics* 13:3843 | 10.3390/math13233843 | TC | resumo; §1-3; §4.5 (Tab. 4); §4.6 e limitações (p. 13-15) |
| 8 | Peixoto, G. (2026). *Design of a Roll-Heave Decoupled Suspension for a Formula Student Prototype*. Dissertação de mestrado, FEUP, Univ. do Porto | repositorio-aberto.up.pt/bitstream/10216/176853/2/799361.pdf | TC | §2.2.10 p. 16-18; p. 31-33; §6.1-6.3 p. 117-123; §7.1-7.2 p. 137-143; Ap. E p. 193-196 |
| 9 | Ventura Lecha, M. (2025). *Design and optimization of a mode-decoupled suspension system for a Formula Student single-seater*. TFG, ETSEIB-UPC | upcommons.upc.edu (HTTP 403) | S | descrito em Peixoto 2026, p. 31-32 |
| 10 | Hwang, W.-M.; Shih, J.-M. (1987). Optimal synthesis of suspension mechanism with variable leverage ratio for motorcycle. *J. Chinese Soc. Mech. Eng.* 8(1):43-50 | wumrc.engin.umich.edu (PDF digitalizado) | R | resumo, na imagem da p. 43 |
| 11 | OptimumG. *Motion Ratio Optimization Using OptimumKinematics* (estudo de caso; documento do fornecedor) | optimumg.com/motion-ratio-optimization/ | TC (página) | página web lida em 2026-11-17 |
| 12 | Borowski, J.; Rudolph, S. (2025). Automation and optimization of the design and development process for a Formula Student racing car suspension. SAE 2025-01-0270 | 10.4271/2025-01-0270 | R | resumo (Crossref) |
| 13 | Avi, A. G.; Carboni, A. P.; Stella Costa, P. H. (2021). Multi-objective optimization of the kinematic behaviour in double wishbone suspension systems using genetic algorithm. SAE 2020-36-0154 | 10.4271/2020-36-0154 | R | resumo (Crossref) |
| 14 | Yi, Y.-S.; Park, J.; Hong, K.-J. (2014). Design optimization of suspension kinematic and compliance characteristics. SAE 2014-01-0394 | 10.4271/2014-01-0394 | R | resumo (Crossref) |
| 15 | Thomas, S. S. et al. (2022). Designing MacPherson suspension architectures using Bayesian optimization. arXiv:2206.09022 (preprint) | arxiv.org/abs/2206.09022 | R | resumo |
| 16 | Schulman, J. et al. (2014). Motion planning with sequential convex optimization and convex collision checking. *IJRR* 33(9):1251-1270 | 10.1177/0278364914528132 | R | resumo (Crossref) |
| 17 | Larsen, E.; Gottschalk, S.; Lin, M. C.; Manocha, D. (2000). Fast distance queries with rectangular swept sphere volumes. *Proc. IEEE ICRA*, p. 3719-3726 | 10.1109/ROBOT.2000.845311 | R+ | TR99-018 da UNC (resumo e introdução) |
| 18 | Gilbert, E. G.; Johnson, D. W.; Keerthi, S. S. (1988). A fast procedure for computing the distance between complex objects in three-dimensional space. *IEEE J. Robotics Autom.* 4(2):193-203 | 10.1109/56.2083 | M | Crossref |
| 19 | Abdel-Malek, K.; Yang, J.; Blackmore, D.; Joy, K. (2006). Swept volumes: foundation, perspectives, and applications. *Int. J. Shape Modeling* 12(1):87-127 | 10.1142/S0218654306000858 | M | Crossref |
| 20 | Waterman, B. J. (2011). *Design and Construction of a Space-frame Chassis*. TCC, Univ. of Western Australia | robotics.ee.uwa.edu.au/theses/2011-REV-SAE-SpaceFrame-Waterman.pdf | TC | p. 9, 15, 28 |
| 21 | Schweighardt, A.; Vehovszky, B.; Feszty, D. (2020). Modal analysis of the tubular space frame of a Formula Student race car. *Manufacturing Technology* 20(1) | 10.21062/mft.2020.013 | TC | p. 3 do artigo (afirmação atribuída ao regulamento) |
| 22 | Riley, W. B.; George, A. R. (2002). Design, analysis and testing of a Formula SAE car chassis. SAE 2002-01-3300 | 10.4271/2002-01-3300 | R | resumo (Crossref) |
| 23 | Bortoluzzi, L. I.; Schommer, A.; Martins, M.; Buenos, A. A. (2016). Formula SAE chassis design to improve suspension tuning. SAE 2016-36-0239 | 10.4271/2016-36-0239 | R | resumo (Crossref) |
| 24 | Auer, B.; McCombs, J.; Odom, E. (2006). Design and optimization of a Formula SAE frame. SAE 2006-01-1009 | 10.4271/2006-01-1009 | R | resumo (Crossref) |
| 25 | Gaffney, E. F.; Salinas, A. R. (1997). Introduction to Formula SAE suspension and frame design. SAE 971584 | 10.4271/971584 | R | resumo (Crossref) |
| 26 | Ramani, K. et al. (2010). *Multi-tier and multi-domain distributed rapid product configuration and design system*. US 7.725.299 B2 (Purdue Research Foundation) | patents.google.com/patent/US7725299B2 | TC (página) | trechos lidos no Google Patents |
| 27 | Zhu, J.; Zhang, W.; Beckers, P. (2009). Integrated layout design of multi-component system. *IJNME* 78(6):631-651 | 10.1002/nme.2499 | R | resumo (Crossref) |
| 28 | Achtziger, W. (2007). On simultaneous optimization of truss geometry and topology. *SMO* 33:285-304 | 10.1007/s00158-006-0092-0 | M | Crossref |
| 29 | Dandurand, B.; Guarneri, P.; Fadel, G. M.; Wiecek, M. M. (2014). Bilevel multiobjective packaging optimization for automotive design. *SMO* 50:663-682 | 10.1007/s00158-014-1120-0 | M | Crossref |
| 30 | Deb, K.; Pratap, A.; Agarwal, S.; Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE TEC* 6(2):182-197 | 10.1109/4235.996017 | M | Crossref |
| 31 | Storn, R.; Price, K. (1997). Differential evolution. *J. Global Optim.* 11(4):341-359 | 10.1023/A:1008202821328 | M | Crossref |
| 32 | Hansen, N.; Ostermeier, A. (2001). Completely derandomized self-adaptation in evolution strategies. *Evol. Comput.* 9(2):159-195 | 10.1162/106365601750190398 | R | resumo (Crossref) |
| 33 | McKay, M. D.; Beckman, R. J.; Conover, W. J. (1979). A comparison of three methods for selecting values of input variables… *Technometrics* 21(2):239-245 | 10.2307/1268522 | M | Crossref |
| 34 | Ugray, Z. et al. (2007). Scatter search and local NLP solvers: a multistart framework for global optimization. *INFORMS J. Comput.* 19(3):328-340 | 10.1287/ijoc.1060.0175 | M | Crossref (SSRN com HTTP 403) |
| 35 | Wächter, A.; Biegler, L. T. (2006). On the implementation of an interior-point filter line-search algorithm… *Math. Program.* 106:25-57 | 10.1007/s10107-004-0559-y | M | Crossref |
| 36 | Milliken, W. F.; Milliken, D. L. (1995). *Race Car Vehicle Dynamics*. SAE R-146 | ISBN 1-56091-526-9 | P | p. 595-596 (IR, K_W com dIR/dδ), conferido pelo projeto em `docs/revisao-metodologica.md` |
| 37 | Seward, D. (2014). *Race Car Design*. Palgrave | 10.1007/978-1-137-03015-3 | P / M | eq. 4.6, p. 101 (P); caps. 2 (p. 33-60), 3 (p. 61-89) e 4 (p. 90-118): só títulos e páginas (Crossref). Conteúdo sobre chassi e rocker NV |
| 38 | Dixon, J. C. (2009). *Suspension Geometry and Computation*. Wiley. Cap. 14 "Installation Ratios", p. 271-298 | 10.1002/9780470682906.ch14 | M | Crossref |
| 39 | Smith, C. *Tune to Win* (1978); Smith, C. *Racing Chassis and Suspension Design*, SAE PT-90 (2004); Staniforth, A. *Competition Car Suspension*; Reimpell, J. et al. *The Automotive Chassis* | 10.4271/pt-90 (só o PT-90) | NV | não acessados nesta sessão |
| 40 | Trzesniowski, M. (2023). *Suspension System*. Springer Vieweg | 10.1007/978-3-658-39847-7 | S | citado por Peixoto 2026 [5] |

Fontes informais vistas e **descartadas como evidência**: fóruns fsae.com, Eng-Tips, F1Technical, LocostUSA e Reddit;
blog waveydynamics; vídeos; artigos de periódicos de baixo rigor editorial (IJERA, IRJET, IJIRSET, IJRET) encontrados
nas buscas.
