# Equipes de Formula Student: como posicionam push/pull rod, rocker e amortecedor em relação ao chassi

Data: 2026-11-17. Pesquisa acadêmica (teses, dissertações, TCCs, artigos revisados e SAE Technical Papers). Este
relatório aprofunda `lit/RELATORIO_LIT.md` e `pratica/RELATORIO_PRATICA.md` e não repete o que já está lá. De lá vêm
Gaffney & Salinas 1997, Waterman 2011, Peixoto 2026 (§6–7 e Ap. E), OptimumG, Borowski & Rudolph 2025 (só o resumo) e
DesignJudges. Daqui em diante cito só os trechos novos.

Rótulos:
- **[F]**: fato conferido na fonte, com página.
- **[I]**: inferência minha.
- **NV**: não verificado.

Os PDFs baixados estão em `topo/dl/` (`upc/`, `stuttgart/`, `feup/`, `vut/`, `monash/`).

## 0. Limites do levantamento (leia antes)

**Quem de fato publicou.** Das equipes da lista, encontrei texto completo e público sobre o processo de posicionar
rocker e amortecedor de três fontes:
- **ETSEIB Motorsport (UPC)**: Ventura Lecha 2025.
- **FEUP (FSFEUP)**: Peixoto 2026, já lido na parte C; aqui li as §3.2, 3.6 e 3.7.
- **Universidade de Stuttgart**: a tese de doutorado de Borowski 2026, orientada por S. Rudolph.
  - Atenção: os casos de estudo são das equipes de Weingarten, Kiel, Pforzheim e Darmstadt, **não** do Rennteam nem do
    GreenTeam de Stuttgart.

Encontrei também equipes fora da lista que têm material útil:
- **TU Brno Racing** (Urban 2020, VUT).
- **Monash Motorsport** (Mapson 2011, FYP).
- **Dynamics UPC Manresa**, que usa chassi tubular (Pagerols 2024 e Bernabeu 2023).

**Sem material público encontrado.** Busquei nos repositórios e na web, sem achar texto acadêmico sobre o tema, das
equipes de:
- **TU Delft (DUT)**: o repositório da TU Delft tem 88 resultados para "formula student suspension". O único da DUT é um
  artigo de revista (Leonardo Times 2011) sem conteúdo técnico.
- **ETH (AMZ)**: o repositório devolveu HTTP 403.
- **KIT, TUM, Michigan, Cornell, UW e Oxford Brookes**: a dissertação de Oxford Brookes está restrita à instituição, e o
  eCommons de Cornell não tem nada sobre FSAE.
- **Chalmers**: o ODR tem 1259 itens "formula student", nenhum sobre suspensão ou chassi.
- **Equipes brasileiras de topo**: os resultados foram TCCs da UFSC Joinville (HTTP 403), da UFU, do CEFET-RJ e da UFPB,
  de equipes que não verifiquei como de topo, e nenhum trata do posicionamento contra o chassi.

**Ranking.** Não conferi nesta sessão a posição de nenhuma equipe em ranking mundial (NV). Chamo as fontes de "equipes
com publicação", não de "equipes de topo", exceto onde a própria fonte se compara ao topo.

**O que a ausência significa.** Que não se ache publicação não quer dizer que a equipe não use o método. As equipes
guardam o processo: Borowski 2026a, p. 15, diz que os dados das equipes estão sob confidencialidade "to preserve the
competitiveness of the teams".

---

## 1. Sequência de projeto, esqueleto no CAD, espaço reservado e congelamento

**ETSEIB, CAT17x, monocoque** (Ventura Lecha 2025):
- [F] A ordem é dinâmica em regime → cinemática das bandejas → cinemática do bellcrank → projeto mecânico.
  - "The wishbone pickup points are determined first, as they are largely independent of the bellcrank design, whereas
    the bellcrank kinematics are inherently dependent on the wishbone geometry" (p. 53).
  - O fluxograma da Fig. 38 (p. 45) tem duas portas de decisão, "Chassis Pickup Points accepted and check for collisions
    passed?": uma depois de otimizar as bandejas e outra depois de otimizar os rockers.
  - Quando a resposta é "No", o fluxo volta para "Set the constraints of the location of the … pickup points".
- [F] A cooperação com o chassi aparece no texto:
  - "the placement of the pickup points directly influences the monocoque's shape" (p. 53).
  - Entre as restrições das bandejas está "Additional constraints on the position of the points as required by the
    chassis department" (p. 56).
  - "If, due to monocoque requirements, the pickup points needed to be adjusted, modifications to the parameter
    ranges—particularly the Y and Z ranges for the axial positions of the bellcranks—were necessary" (p. 67-68).
- [I] É um processo concorrente com portão. A suspensão propõe, o chassi aceita ou devolve restrições, e o otimizador
  roda de novo.

**TU Brno, Dragon X** (Urban 2020):
- [F] Hierarquia explícita: "chassis has to accommodate the suspension pickup points, and so the suspension is superior"
  (p. 12).
- [F] Esqueleto paramétrico no CAD (p. 34-35):
  - "In Creo Parametric … are constructed sketches in the plane of roll damper and heave damper … leverages of the
    bellcrank are parametrized via angles and lengths … this sketch influences the kinematic skeleton of the model which
    changes the position of the dampers. Then a check of interference with other parts is made."
  - Os hardpoints vão para o Adams, que mede o installation ratio. Se não bater, o fluxo volta ao esboço (laço da Fig.
    26).
  - É o único relato acadêmico que achei de esboço-mestre ("kinematic skeleton") dirigindo o rocker no CAD.
- [F] O laço das bandejas tem quatro nós: pontos externos, pontos internos, razões de instalação e "Collisions with other
  parts", mais as forças nas barras (Fig. 71, p. 70).

**FEUP** (Peixoto 2026):
- [F] Os pontos internos foram postos "within the admissible chassis-side regions defined by the monocoque interface"
  (p. 49).
- [F] As regiões são planos de restrição: parede lateral quase vertical, piso abaixo do gabarito da caixa de pedais e
  cremalheira abaixo do piso (p. 41-42).
- [F] Os hardpoints iniciais eram os do chassi tubular (FSFEUP03) e foram refinados em iterações sucessivas (§3.6, p.
  49-52).
- [F] O rocker entra depois: "Once a feasible baseline geometry is defined, the suspension concept must be connected to
  the inboard elastic system" (p. 53).
- [F] O mecanismo é desenhado como "rigid bodies of arbitrary shape" e só depois é empacotado contra o monocoque (cap. 7,
  p. 54).

**Dynamics UPC Manresa, chassi tubular** (Pagerols 2024):
- [F] A geometria "se diseña a la par con el chasis" (resumo).
- [F] O ponto do push rod na manga e o do amortecedor no chassi são definidos antes do motion ratio, e o do amortecedor
  "mainly because of packaging decisions – as close to the center as possible" (p. 52 do PDF).

**Monash 2011** (Mapson 2011):
- [F] "With the shock and wishbone pickup points largely fixed by stiffness and packaging considerations, the choice of
  bellcrank points was critical" (p. 53).

**Stuttgart** (Borowski 2026b):
- [F] A tese descreve a prática comum das equipes:
  - Subtimes isolados, integração tardia e manual no CAD.
  - "3D-Kollisionsprüfungen [werden] manuell durchgeführt, wobei primär statische Einfederungszustände … abgeprüft
    werden" (p. 16).
  - A fase de projeto da suspensão "nie länger als 3 Monate" (p. 5).

**Congelamento de hardpoints.** Nenhuma fonte lida dá data ou critério formal de congelamento (não encontrado). O
congelamento de fato aparece só como restrição herdada:
- Na ETSEIB, os pontos da manga ficaram iguais aos do CAT16x, para não refazer a manga (p. 54).
- Na FEUP, a geometria segue iterando ("the kinematics should continue to be iterated", resumo).

**"Space claim" com esse nome.** Não encontrado. O equivalente funcional é:
- os planos admissíveis do monocoque (Peixoto);
- o envelope do aro de 215 mm, com 8 mm de margem para tolerância e deflexão (Peixoto p. 39);
- as faixas de variáveis limitadas "to prevent collisions" (Ventura p. 54 e 64).

**Síntese [I].** Em todas as fontes a sequência é bandejas → atuação, e o chassi aceita ou devolve restrições. Nenhuma
trata o chassi como fixo nem como totalmente livre. O esqueleto paramétrico no CAD aparece em uma equipe (TU Brno, Creo).

## 2. Como escolhem os pontos de atuação

| Equipe / fonte | Ferramenta | Otimização formal? | Colisão no laço? |
|---|---|---|---|
| ETSEIB CAT17x (Ventura 2025) | MATLAB próprio (corpo rígido, Newton-Raphson, tabela de consulta da bandeja) + DEFT-Funnel (sem derivada) | Sim. 16 variáveis por eixo no bellcrank (Tab. 16, p. 64); objetivo de desacoplamento; restrições de curso, variação de MR, simetria e comprimento do amortecedor (p. 66-67) | **Não.** Faixas de variáveis "constrained to prevent collisions" (p. 64), e depois o portão "check for collisions passed?" (Fig. 38). Orçamento lista licença SolidWorks (Tab. 25, p. 97) |
| TU Brno Dragon X (Urban 2020) | Creo (esboço paramétrico) + Adams Car + MATLAB | Não. Laço manual (Fig. 26, p. 34-35) | Colisão no Adams com envelope do aro e checagem no CAD por outros membros (p. 78-79) |
| FEUP (Peixoto 2026) | Iteração manual, MATLAB, Adams, Siemens NX | Não para os hardpoints (§3.6) | Não. Folga verificada no fim (NX Motion, cap. 7; ver parte C) |
| Manresa DYN-08 (Pagerols 2024) | Lotus Shark (OptimumKinematics também usado) | Não. Manual: "the suspension points are being manually moved" (p. 90 do PDF) | Montagem móvel no CAD (p. 76 do PDF) |
| Weingarten e outras (Borowski 2026a/b) | Linguagem de projeto em grafo, compilador proprietário DC43 (IILS) com BREP próprio | Sim. Enxame de partículas (PMSO) | **Sim.** Colisão dinâmica por malha triangulada em todos os estados, como restrição (tese p. 121-123) |
| Monash 2011 (Mapson 2011) | Excel (cargas), MATLAB (pneu); ferramenta cinemática não declarada | Não declarada | NV |

**Pormenores com evidência**

- **Antes era força bruta.** [F] Na ETSEIB, antes do CAT17x, "the team relied on a brute-force design space exploration
  approach without any optimization algorithms, simplifying the kinematics to a 2D representation" (p. 44).
  - O processo era demorado e "prone to suboptimal outcomes" (p. 45).
  - Com o DEFT-Funnel, a iteração passou "from several weeks to only a few days" (p. 45).
  - É a mesma transição que a Tupã vive com o script do Murilo.

- **Restrições demais impedem a solução.** [F] A ETSEIB descreve o mesmo sintoma de 1,1 milhão de combinações sem
  solução. Nas bandejas, as restrições "often resulted in the algorithm failing to find a solution that satisfied all the
  constraints simultaneously. Fine-tuning these parameters through iterative, progressively restrictive runs was
  necessary" (p. 57). No bellcrank:
  - "Over-constraining any of the parameters could prevent the optimization algorithm from finding viable solutions" (p.
    67).
  - A saída deles: "a small margin of flexibility is allowed for each constraint", o que também "helps identify trends in
    the direction the constraints tend to shift" (p. 57).

- **Igualdades por construção.** [F] A ETSEIB faz isso em três passos (p. 62-63):
  - Eixo do bellcrank paralelo ao X ("to avoid introducing axial forces"), definido só por Y e Z.
  - Ponto do push rod na bandeja e no bellcrank com o mesmo X ("the pushrod must remain parallel to the Y-Z plane").
  - Pontos do push rod e do amortecedor em coordenadas polares em torno do eixo do bellcrank.
  - Para as bandejas, otimiza o eixo (4 parâmetros), não os 6 pontos (p. 54).
  - O X dos pontos, que não altera a cinemática, fica para depois. "The positions along the X-axis were determined based
    on the monocoque geometry constraints and the physical dimensions of the dampers" (p. 68).

- **O X livre usado para cair em nó.** [F] Manresa (tubular): "the X coordinate in the inner Pick-Up points does not
  affect the suspension geometry … the X coordinate can be placed where needed in order to be in a chassis node" (p. 76
  do PDF).

- **Restrição de catálogo.** [F] A ETSEIB escolhe o amortecedor (Multimatic) antes da otimização, "as their
  specifications influence the constraints" (p. 65), e o comprimento do amortecedor de rolagem é restrição de igualdade:
  211 mm em repouso (p. 67).

- **Colisão com roda, manga e direção.**
  - [F] TU Brno, colisão com o aro no Adams com envelope do aro (p. 78), combinando três coisas:
    - curso extremo com esterço máximo (bump 25 mm na bandeja inferior, rebound 25 mm na superior);
    - camber extremo (−1° nos braços inferiores e −4° nos superiores), porque "different camber angles also influence the
      clearance".
  - [F] Weingarten (Borowski 2026b): a direção é o caso mais difícil.
    - A cremalheira mudou de posição por regra, e o aro é de 10".
    - Uma solução "kollisionsfrei und gleichzeitig die kinematischen Vorgaben erfüllende … nur sehr schwer zu finden"
      (p. 121-122).
    - Usaram PMSO com colisão em todos os estados de esterço, rodando a noite inteira num notebook (p. 122).
  - [F] Manresa DYN-07: o push rod interferia com os semieixos e foi resolvido mexendo nos Y da manga (Bernabeu 2023, p.
    14 do PDF).

- **Gabaritos do regulamento.**
  - [F] FEUP: piso do monocoque abaixo do gabarito da caixa de pedais, com margem e espessura (Peixoto p. 41).
  - Nenhuma outra fonte lida modela gabaritos como volume no otimizador (não encontrado).

## 3. Fixação em nó, esforço, chapas e insertos; monocoque × tubular

- **Tubular.**
  - [F] Manresa: pôr o ponto "in the tube nodes of the tubular frame; that way, the compliance is very much reduced"
    (Pagerols p. 55 do PDF), deslizando o X para isso (p. 76 do PDF).
  - [F] Os suportes do rocker e do amortecedor são chapas de aço S355 de 5 mm soldadas ao chassi: em U na dianteira e um
    par de chapas na traseira (Bernabeu, §2.3, p. 19 do PDF).
  - [F] Para soldar na posição, usam "bancadas de chapas planas que encajarán a los tubos del chasis" (gabaritos de
    montagem, p. 46 do PDF).
  - [F] Monash 2011: "on the front, packaging difficulties made the linkage less than ideal, with significantly more out
    of plane loading", e os bellcranks foram feitos em chapa 4130 com "shear plates" para ganhar rigidez fora do plano
    (p. 53).
  - [F] Na traseira, push rod, bellcrank e amortecedor formam "a neat planar mechanism" (p. 37).
  - [I] É evidência de equipe estudante de que o desvio do plano cobra um preço estrutural no rocker. É o achado 3 do
    REGISTRO.
- **Cálculo de esforço.** [F]
  - ETSEIB: cargas no bellcrank ao longo do curso (§7.2.3); a distância da fixação à parede reduzida a 14 mm, "limited
    by the need to avoid contact between the spherical bearing and the monocoque wall during suspension movement" (p.
    76).
  - Manresa: força no push rod = carga de projeto × sen γ, com compromisso entre MR linear e força (p. 74 do PDF).
  - FEUP: exige rigidez da fixação, Ke (parte C).
  - Nenhuma fonte usa "distância ao nó" como restrição numérica (não encontrado). A rigidez entra por FEA ou por exigência
    de rigidez depois do posicionamento.
- **O que não se transfere ao chassi tubular da Tupã [I].**
  - ETSEIB, FEUP (nova), TU Brno e o CAT17x são monocoque. Neles a fixação é inserto ou suporte colado na parede, e a
    restrição de empacotamento vira planos admissíveis da parede.
  - No tubular, a restrição real é tubo e nó discretos. Valem as fontes de Manresa e Monash (e Waterman e Gaffney, na
    parte C).
  - O uso do grau de liberdade invariante (X) para cair em nó é transferível e barato.

## 4. Verificação

- [F] ETSEIB:
  - checagem de colisão como portão do processo (Fig. 38, p. 45);
  - curso combinado de verificação calculado dos casos de carga: 35 mm de jounce e 25 mm de rebound (p. 51-52);
  - verificação pós-otimização das curvas de MR e de comprimento do amortecedor (p. 68-70).
- [F] TU Brno:
  - Adams com envelope do aro, curso × esterço × camber (p. 78-79), e checagem duplicada no CAD por outros membros;
  - "a basic compliance measuring" no carro (introdução, p. 11).
- [F] Borowski 2026b:
  - **contraexemplo real**: no Stinger23EV (Weingarten), uma colisão não vista entre a bandeja inferior e a camisa de
    arrefecimento do motor em rebound total;
  - foi descoberta na fabricação e obrigou a trocar uma bandeja de CFRP/alumínio por uma de aço mais pesada (p. 16-17);
  - o autor atribui o erro à checagem manual e estática.
- [F] Borowski 2026a: a colisão é calculada triangulando o BREP e testando interpenetração em todos os estados de
  movimento (p. 12-13).
- [F] FEUP: NX Motion no fim (parte C).
- [F] Manresa: montagem móvel no CAD (p. 76 do PDF); interferência push rod × semieixo achada no carro anterior
  (Bernabeu p. 14 do PDF).
- **Protótipo e medição.** Só achei a medição de compliance da TU Brno e os gabaritos de solda de Manresa. Protótipo
  físico de empacotamento (mock-up): não encontrado.

## 5. Automação dentro do CAD

- [F] **Nenhuma** fonte lida roda o posicionamento dentro de um CAD comercial por API: NX Open, CATIA Knowledgeware,
  SolidWorks API, Fusion ou Onshape não aparecem. A busca específica também não achou nada.
- [F] O mais próximo:
  - TU Brno: esboço paramétrico no Creo alterado à mão (p. 34-35).
  - Borowski: modelo de geometria próprio, gerado por código (BREP do DC43), que exporta CAD (2026a p. 12). A geometria
    sai do grafo, não de um CAD aberto. O ganho relatado é de "mehrere Stunden" para 5 min por iteração e de "mehrere
    Monate" para 2 semanas no projeto cinemático (2026a p. 13).
    - Ressalva 1, conflito de interesse declarado: o autor é empregado da IILS, dona do DC43, e as equipes receberam
      licença e coaching gratuitos (2026a p. 15).
    - Ressalva 2: as equipes são de universidades de ciências aplicadas, sem ranking conferido.
  - Artigo complementar (Borowski et al. 2026, três equipes): ">10⁴ suspension variants within days instead of a few
    dozen manually created variants" (resumo).
- [I] A versão final da Tupã, rodando dentro do Fusion, **não tem precedente acadêmico encontrado** em Formula Student. O
  precedente mais forte de automação (Stuttgart/IILS) fez o caminho inverso: tirou a geometria do CAD e a gerou por
  código.

---

## 6. Comparação com a SPEC da Tupã

| Aspecto | Prática documentada | SPEC Tupã | Igual / diferente | Melhor ou pior para a Tupã, e por quê | Confiança |
|---|---|---|---|---|---|
| Ordem | Bandejas antes da atuação; chassi aceita ou devolve restrições (ETSEIB Fig. 38; TU Brno p. 12; FEUP p. 53) | Bandejas e direção fixas (v10); só a atuação é posicionada | Igual na ordem | Melhor: escopo pequeno, como pede U1 | Alta |
| Papel do chassi | Negociado: portão "accepted?" e restrições pedidas pelo chassi (ETSEIB p. 56, 67-68) | Obstáculo fixo; o programa não dita tubos (U1) | Diferente, mais rígido | Risco: com o chassi incompleto, tratá-lo como fixo pode dar conjunto vazio. Mitigado porque o mapa de espaço livre e a Fase I dão ao chassi a informação que o portão da ETSEIB daria | Média |
| Igualdades por construção | ETSEIB: eixo ∥ X, X comum do push rod, polares em torno do eixo, X decidido depois (p. 62-68) | Braço pelo MR-alvo, olhal pelo comprimento, 90° opcional | Igual em espírito | A ETSEIB vai além: separa graus de liberdade invariantes (X) para empacotar e cair em nó. **Sugestão: copiar** (pivô e olhal deslizam ao longo do próprio eixo ou linha) | Alta |
| Tratamento de restrições | Margem pequena em cada restrição; endurecer aos poucos; restrição demais = sem solução (ETSEIB p. 57, 67) | Desigualdades com procedência; Fase I mostra conflitos | Mais sofisticado | Melhor: a ETSEIB fez à mão o que a Fase I automatiza. É evidência de que o problema é a forma das restrições, não o algoritmo | Alta |
| Colisão | ETSEIB: só caixas de variáveis + portão depois. TU Brno: Adams + CAD, manual. Weingarten: colisão por malha no laço (PMSO) | Cápsulas no laço, curso × esterço, certificador | Mais sofisticado que ETSEIB, FEUP e TU Brno; parecido com Borowski | Melhor: o caso Weingarten mostra o custo de checar só estático. **Lacuna da SPEC: não varre camber estático nem ajuste**; a TU Brno testa camber extremo (p. 78). Incluir a faixa de camber e de ajuste na varredura | Média-alta |
| Gabaritos e regras | FEUP: plano do piso abaixo do gabarito de pedais (p. 41); nenhuma fonte modela gabarito no otimizador | Volumes gerados das regras (T.1.2, F.8.x, V.3.2.4) | Mais sofisticado | Melhor, se os volumes forem conferidos contra o regulamento (CA-3). Sem precedente para validar o código | Média |
| Nó | Preferência: deslizar X para cair em nó (Manresa); rigidez por FEA ou Ke depois (FEUP); nenhum limite numérico | Proximidade como preferência (U3) | Igual | Adequado. Tratar nó como restrição dura não tem apoio nas fontes | Alta |
| Plano do rocker | Monash: fora do plano na dianteira → bellcrank reforçado (p. 53); ETSEIB impõe paralelismo por construção | "Mesmo plano" só no estático (achado 3) | Pior hoje | Medir o desvio ao longo do curso e reportar a carga lateral, como já está nas correções | Média |
| Catálogo de amortecedor | Escolhido antes; comprimento como restrição (ETSEIB p. 65-67) | Comprimento do amortecedor resolvido por construção | Igual | Adequado | Alta |
| Ferramenta e plataforma | MATLAB + otimizador sem derivada (ETSEIB); CAD paramétrico + Adams (TU Brno); código próprio com BREP (Stuttgart/IILS). Nenhuma API de CAD | Python + STEP (V1) → add-in Fusion (final) | V1 igual ao padrão; a final é inédita | V1 melhor (reprodutível, sem licença). Final: sem precedente; risco de licença e de desempenho. O caso Borowski sugere manter o núcleo fora do CAD e usar o CAD só para entrada e visualização | Média |
| Saída | Um ponto ótimo por rodada (ETSEIB; "results consistent across multiple iterations", p. 67) | Lista de candidatos certificados + mapa | Mais rica | Melhor para negociar com o chassi | Média |

### Evidência contra a proposta da Tupã

1. **Equipes com publicação fazem sem colisão automática no laço.**
   - ETSEIB, FEUP, TU Brno e Manresa resolvem a colisão com caixas de variáveis e checagem posterior, manual ou no
     Adams/CAD, e entregam carros.
   - [I] Para uma equipe estudante, um laço "otimizador sem derivada + caixas + portão de colisão no CAD" pode bastar. O
     caminho mais barato seria corrigir o script do Murilo nessa direção, antes de construir o certificador e os volumes
     de regra.
2. **Recomendação explícita a favor do manual.** Pagerols recomenda à equipe o Lotus Shark, de movimento manual, porque
   ajuda a entender o efeito de cada ponto (p. 90 do PDF). É argumento de formação, relevante para equipe com rotatividade
   alta.
3. **Automação forte com colisão no laço só aparece com ferramenta proprietária e apoio externo** (Borowski, com conflito
   de interesse declarado), e custa uma noite de cálculo por rodada (p. 122).
4. **O conjunto viável pode ser vazio mesmo com otimizador.**
   - A ETSEIB precisou relaxar restrições aos poucos (p. 57 e 67).
   - Nenhuma ferramenta substitui a decisão da equipe sobre o que relaxar (ABERTO A3 da SPEC).
   - [I] Isso reforça a Fase I, mas também mostra que o gargalo é a decisão humana, não o código.
5. **Precedente fraco para rodar dentro do CAD.** Não achei equipe que posicione rocker por API de CAD. O único caso
   "tudo-em-um" fez o contrário e tirou a geometria do CAD.

### Leitura geral [I]

A SPEC está alinhada com o que as fontes mostram de melhor:
- igualdades por construção, como a ETSEIB;
- bandejas antes da atuação;
- nó como preferência;
- colisão em todos os estados, a lição de Weingarten.

Em colisão, regras e diagnóstico ela é mais ambiciosa que as equipes com publicação. Para o contexto da Tupã é
defensável: chassi tubular ainda incompleto, sem Adams, falha documentada da força bruta.

Três ajustes saem diretamente das fontes:
1. Explorar graus de liberdade invariantes (X / ao longo do eixo) para empacotar e cair em nó.
2. Varrer também a faixa de camber e de ajuste na verificação de folga.
3. Manter a versão Fusion como camada de entrada e visualização, sem pôr o núcleo dentro do Fusion.

Confiança: média. São seis fontes de equipes, nenhuma das maiores da lista, e só uma (Manresa) com chassi tubular e
detalhe de suportes.

---

## 7. Referências e status de verificação

Status:
- **TC**: texto completo lido nas páginas citadas.
- **R**: só o resumo.
- **M**: só os metadados.
- **NV**: não verificado.
- **"p. do PDF"**: página física do arquivo, quando o documento não imprime número.

| # | Referência | Acesso | Status | Onde conferi |
|---|---|---|---|---|
| 1 | Ventura Lecha, M. (2025). *Design and optimization of a mode-decoupled suspension system for a Formula Student single-seater*. TFG, ETSEIB-UPC. hdl 2117/427967 | upcommons.upc.edu (API DSpace; `topo/dl/upc/2117_427967__main.pdf`) | TC | p. 39-40, 43-45 (Fig. 38 vista na imagem), 51-57, 62-70, 76, 97 |
| 2 | Borowski, J. (2026b). *Digitaler Entwurf eines Formula Student Fahrzeugs am Beispiel von Fahrwerk und Antriebsstrang zur 3D-Geometrie- und Kinematikerstellung*. Dissertação, Univ. Stuttgart (orient. S. Rudolph). hdl 11682/18074 | elib.uni-stuttgart.de (`topo/dl/stuttgart/`) | TC (trechos) | p. 5-6, 12, 16-17, 29, 31-32, 121-123 |
| 3 | Borowski, J.; Rudolph, S. (2026a). Graph-based design languages for engineering automation: a Formula Student race car case study. *Vehicles* 8(1):24. doi:10.3390/vehicles8010024 | elib Stuttgart (PDF da editora) | TC (trechos) | resumo; p. 12-13, 15 (dados, agradecimentos, conflito de interesse) |
| 4 | Borowski, J.; Emsmann, H.; Kneule, J.; Ruess, R.; Rudolph, S. (2026). Managing design variants in Formula Student race cars: a digital engineering approach across multiple teams. *Vehicles* 8:43 | elib Stuttgart (hdl 11682/18147) | R + afiliações | resumo; afiliações (Kiel, Pforzheim, Darmstadt); §2.1-2.3 por busca de termos |
| 5 | Borowski, J.; Rudolph, S. (2025). Automation and optimization of the design and development process for a Formula Student racing car suspension. SAE 2025-01-0270. doi:10.4271/2025-01-0270 | Crossref | R | resumo |
| 6 | Urban, M. (2020). *Design of Formula Student wheel suspensions* (Návrh zavěšení kol Formule Student). Dissertação de mestrado, VUT Brno (orient. P. Porteš) | vut.cz (file_id 213460; `topo/dl/vut/`) | TC (trechos) | resumo; p. 11, 12, 34-35, 69-70, 78-79 |
| 7 | Peixoto, G. (2026). *Design of a roll-heave decoupled suspension for a Formula Student prototype*. Dissertação de mestrado, FEUP | repositorio-aberto.up.pt/bitstream/10216/176853/2/799361.pdf | TC | resumo; §3.2 p. 39-42; §3.6 p. 49-52; §3.7 p. 53-54; §6.3.2 p. 123 |
| 8 | Pagerols Gallardo, A. (2024). *Diseño de la geometría del sistema de suspensión para un vehículo de Formula Student*. TFG, EPSEM-UPC (Dynamics UPC Manresa). hdl 2117/414361 | upcommons (`topo/dl/upc/`) | TC (trechos) | resumo; p. do PDF 52, 55, 74, 76, 90 |
| 9 | Bernabeu Meseguer, J. (2023). *Diseño, simulación y fabricación de rockers para un Formula Student*. TFG, UPC (Dynamics UPC Manresa). hdl 2117/393371 | upcommons (`topo/dl/upc/`) | TC (trechos) | resumo; p. do PDF 14, 19, 46 |
| 10 | Mapson, A. (2011). *Design, manufacture and testing of suspension for a Formula SAE car*. Final Year Project, Monash University (Monash Motorsport, coleção de FYPs no site da equipe) | mmsbeta.squarespace.com (`topo/dl/monash/`) | TC (trechos) | p. 37, 53. Tipo de chassi do carro de 2011 não declarado nos trechos lidos: NV |
| 11 | de Paula Eduardo, G. (2005). Formula SAE suspension design. SAE 2005-01-3994 | Crossref | R | resumo ("dimensional approach was developed on CAD concerning dimensional restrictions"; benchmarking de equipes de topo). Instituição: NV |
| 12 | Prusinowski, A. J. (2008). Exploring the effect of manufacturing tolerances on the front suspension performance of a Formula SAE vehicle relative to design targets. SAE 2008-01-2952 | Crossref | R | resumo (Adams + DOE de tolerâncias). Útil ao δ da SPEC; não lido |
| 13 | Jawad, B. A.; Baumann, J. (2002). Design of Formula SAE suspension. SAE 2002-01-3310 | Crossref | R | resumo (sem conteúdo de empacotamento) |
| 14 | Kortenhorst, J. (2011). The DUT racing team; design, produce and race your own car. *Leonardo Times* | repository.tudelft.nl | R | resumo (sem conteúdo técnico; não é acadêmico revisado) |
| 15 | Bouman, N. D. D. (2026). *Multidisciplinary optimisation of Formula 1 suspension systems*. Dissertação de mestrado, TU Delft | repository.tudelft.nl | R | resumo (F1, não FS: 49 variáveis, 52 restrições, NSGA-II). Só como contexto |

Já registradas nas partes C e E e não repetidas aqui: Gaffney & Salinas 1997; Waterman 2011; OptimumG; DesignJudges.

Buscas sem resultado útil:
- Chalmers ODR (API DSpace).
- Cornell eCommons (API DSpace).
- TU Delft (`/search/data`).
- IST Scholar: só achei teses de FST sobre monocoque e ligação da suspensão, não lidas (M).
- TU Graz.
- ETH (HTTP 403), Michigan Deep Blue (403), UFSC (403), USP BDTA (conexão recusada).
- Buscas web por KA-RaceIng, TUfast, AMZ, DUT, UW, MRacing, Oxford Brookes e equipes brasileiras de topo.
- Busca por automação de hardpoints via API de CAD em FS: só achei uma macro comunitária de SolidWorks que exporta
  hardpoints (GitHub sunfish-labs; não acadêmica, não usada como evidência).
