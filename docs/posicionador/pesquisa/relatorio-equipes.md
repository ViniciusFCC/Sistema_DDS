# Equipes de topo e o empacotamento da atuação (push/pull rod, rocker, amortecedor): o que se sabe publicamente

Data: 2026-11-17. Parte "topo" do plano (complementa `pratica/RELATORIO_PRATICA.md`; o que já estava lá — UM-Rolla, NAU, Cal Poly, ferramentas, bibliotecas, Fusion API — não é repetido).
Nada foi instalado nem executado. Firecrawl sem créditos: usei WebSearch/WebFetch e curl. Os arquivos brutos baixados estão em `topo/raw/` (resultados do FSG26, JSON do ranking, handbook, PDFs).

Rótulos: **[OFICIAL]** organizador/regulamento/ranking operado pelo organizador; **[JUIZ]** texto de juiz de design em veículo próprio (DesignJudges, IMechE Head Design Judge); **[EQUIPE]** publicado pela própria equipe ou sua universidade (indício, não prova); **[ACADÊMICA]** artigo/tese/relatório de curso; **[IMPRENSA]** nota de imprensa/notícia; "não verificado" = não consegui abrir ou conferir.

## 0. Resposta curta

1. **Não encontrei nenhuma equipe de topo que publique o método de empacotamento da atuação** (como escolhe pontos de rocker, pushrod e amortecedor contra tubos e nós). O que existe publicamente é: (a) prescrições de juízes e organizadores, (b) newsletters e páginas de equipe com ordem de projeto em alto nível, (c) trabalhos acadêmicos, a maioria de equipes fora do topo. Design reports e design spec sheets das equipes de topo, que contêm o método, não estão publicados (ou não achei). Isto é uma lacuna de evidência, não prova de que elas não têm método.
2. **Padrão que se repete nas fontes**: empacotamento primeiro (piloto, gabaritos, powertrain, roda/freio) → pontos da suspensão "se projetam sozinhos" dentro do que sobra → chassi e suspensão iteram juntos → congelamento com data (CAD-lock/design freeze) → verificação de montagem no CAD completo e em carro real → FEA local nos pontos que ficaram fora do ideal. Fixar em nó é "ideal", não regra dura.
3. **Juízes**: pesam o entendimento e a justificativa da equipe, não a ferramenta. No FSG26, "Suspension components" vale 5 de 150 pontos e "Package" 5 de 150.
4. **Tupã**: o escopo U1–U4 está alinhado ao que juízes e equipes dizem (pontos limitados pelo espaço, nó como preferência). O que sobra de rigor (certificador independente, mutação, hash, CA-7 contra OptimumKinematics, adaptador Fusion) não é cobrado por juiz nenhum e é o principal risco de sobre-engenharia (seção 6).

## 1. Quem é "topo" e de onde vem o ranking

**Ranking mundial [OFICIAL]**: FS World / World Ranking List, operado pela Formula Student Germany GmbH (fs-world.org), posição "as of 06 Sep 2026" (lido por curl em 2026-11-17 do endpoint de dados da página; nomes cruzados com a lista de universidades do mesmo site).

| # | Elétrico (EV), pontos de 1000 | Combustão (CV), pontos de 1000 |
|---|---|---|
| 1 | ETH Zürich 851 | UPV València 689 |
| 2 | UAS Graz 643 | Purdue West Lafayette 593 |
| 3 | TU UAS Tallinn 640 | K-State Manhattan 578 |
| 4 | PT Milano (Dynamis PRC) 635 | UNIMORE Modena 573 |
| 5 | RWTH Aachen 635 | Georgia Tech 557 |
| 6 | TU München 631 | Texas A&M 549 |
| 7 | NTNU Trondheim 621 | Alabama Tuscaloosa 546 |
| 8 | U Stuttgart 608 | UConn 529 |
| 9 | UAS Esslingen 583 | UC Berkeley 510 |
| 10 | IT Karlsruhe 580 | Thessaloniki 499 |

Observações: (i) é ranking por universidade, o mesmo nome pode juntar times diferentes; (ii) a página anunciava revisão da fórmula (não verificado quando); (iii) a lista tem ainda a Driverless Cup (ETH 1º), fora do escopo.

**Evento de Design (juízes) [OFICIAL], resultados recentes**

| Evento | Resultado | Fonte |
|---|---|---|
| FSG 2026 (Hockenheim, EV; carros numerados) | 1 TU München (car 31) 150; 2 ETH Zürich (33) 149; 3 U Stuttgart (26) 139; 4 Chalmers (95) 130; 5 empate KIT (76) e TalTech (124) 120. Finalistas: Stuttgart, München, ETH, Chalmers. | PDF oficial "FSG26 Engineering Design Results v2", baixado e lido |
| FSG 2025 | EV: ETH Zürich, KIT, TU Delft. CV: UPV València, U Stuttgart, Federico II Napoli | resumo oficial do dia 6, via busca (PDF não aberto) |
| FSAE Michigan 2026 (lista de carros IC; EV não conferido) | 1 UPV 150; 2 UNIMORE 131; 3 Purdue 126; **4 Escola de Engenharia de São Carlos (EESC-USP) 122**; 5 USC 116 | PDF oficial de resultados SAE (`FSAE_2026_MI5_results`), lido. EESC-USP foi 9º geral. |
| FS UK 2025 | Engineering Design: WUT Racing (Wuhan Univ. of Technology); campeã geral FSBizkaia (UPV/EHU) | IMechE via busca (não aberto) |
| FS UK 2026 | Oxford Brookes Racing diz que o time elétrico venceu Design; um post de LinkedIn de outra equipe fala em 3º lugar de Design. **Conflito, não resolvido.** Campeã geral: ECU Racing | notícias de universidades [EQUIPE]/[IMPRENSA]; não confirmar sem a página do IMechE |

**Brasil (Fórmula SAE Brasil) [IMPRENSA], Mecânica Online + Ford**: 2026 (22ª, Tatuí): combustão 1º EESC USP Fórmula SAE (920,3), 2º Fórmula Cefast (CEFET-MG), 3º Poli Racing; elétrico 1º Fórmula FEI Elétrico, 2º B'Energy Racing (Facens), 3º Unicamp E-Racing. 2025 (21ª): combustão 1º EESC USP (882,2; venceu também a prova de Design na combustão), 2º Mauá Racing (759), 3º Cefast (647,9); elétrico 1º FEI (662), 2º UFPR (423,1), 3º B'Energy (366,9). Vencedor da prova de Design elétrica: não informado nas fontes. No ranking mundial (CV): EESC-USP São Carlos #21, Mauá #70, CEFET-MG #84, Poli-USP #116; no EV, FEI #421 (9 pontos). Uma das buscas afirmou que a EESC USP Fórmula SAE (combustão) e a Tupã (elétrica) são equipes distintas da mesma escola; **não verificado**.

## 2. Processo por equipe e fonte (tabela pedida)

Legenda de confiança: A = método descrito de forma verificável; B = indício indireto; C = só menção.

| Equipe (posição) | Fonte e tipo | O que fazem (do que está escrito) | Conf. |
|---|---|---|---|
| AMZ / ETH Zürich (EV #1; Design 2º FSG26, 1º FSG25) | Newsletters do site da equipe, `amzracing.ch/en/news/*` [EQUIPE] | Fase de projeto de cerca de 3 meses, "design freeze" no fim do ano; depois um "boot camp" em que "tudo é checado de novo para que as peças se encaixem e as regras sejam cumpridas", otimização final de massa, desenhos para parceiros. Carro inteiro no CAD "até a menor arruela" para planejar a montagem. Montagem planejada antes: "todo o conjunto foi analisado e quebrado em etapas" porque ~30 membros fixam peças no monocoque. Nada sobre método de pontos de suspensão. | B |
| TUfast / TU München (EV #6; Design 1º FSG26) | Busca em site/blog/GitHub | Nada técnico encontrado (site e GitHub não acessíveis daqui, GitHub deu 403). | C |
| GreenTeam / U Stuttgart (EV #8; Design 3º FSG26) | Busca | Nada de método encontrado. Pesquisadores da U Stuttgart (Rudolph) publicam automação com "design languages" aplicada a suspensão de Formula Student (ver seção 4), mas o paper nomeia equipes de Kiel, Pforzheim e Darmstadt, não o GreenTeam. | C |
| Chalmers (EV #11; Design 4º FSG26) | Site da equipe [EQUIPE] | "Projeta e fabrica a maior parte do carro, incluindo suspensão, chassi de fibra de carbono" e só. | C |
| TU Delft / DUT (EV #22; Design 3º FSG25) | Páginas por carro `fsteamdelft.nl/team/dut2x` [EQUIPE] | Descrevem layouts (DUT25: duplo A, frente direta, pushrod com rocker atrás; DUT26: "conceito de suspensão completamente novo", heave e roll desacoplados; monocoque composto). Nenhum método de posicionamento. | C |
| Revolve NTNU (EV #7) | Página da equipe e blog [EQUIPE]; resumo "Gnist" (SlideShare, não abri; só via busca) | Monocoque modelado em SolidWorks, Abaqus para resistência e rigidez, FiberSim para laminação. Grupo de suspensão: "projeto começa em CAD e é verificado em FEM". Resumo do carro Gnist (via busca, não aberto): ordem de projeto com modelo de suspensão e empacotamento **antes** do monocoque, e monocoque com suportes de suspensão integrados. Blog não menciona empacotamento nem hardpoints. | B/C |
| UPV València (CV #1; Design 1º Michigan 2026 e FSG25) | Notícias da universidade [EQUIPE/IMPRENSA] | Monocoque de carbono; "toda a equipe trabalhando para encaixar tudo no novo monocoque". Sem método de suspensão publicado. | C |
| UNIMORE / MoRe Modena (CV #4; Design 2º Michigan 2026) | Tese de mestrado "Development of a Suspension Kinematics Design Tool" (F. P. Cotugno, UniMoRe, 2025-26, com supervisor de empresa) [ACADÊMICA] | Ferramenta em Python que preserva as planilhas Excel de engenharia validadas, importa geometria inicial e curvas-alvo, atualiza coordenadas de hardpoints escolhidos e avalia no modelo original. Que a tese seja da equipe MoRe: **não verificado**; cobre rocker: **não verificado** (só li o resumo da busca). | B |
| Georgia Tech (CV #5) | Página da equipe [EQUIPE] | Pushrod/amortecedor "direto" por simplicidade e massa; suspensão e chassi trabalham juntos "porque os dois projetos são intimamente relacionados"; simulações de dinâmica "feitas inteiramente em casa". | C |
| Oxford Brookes (EV #40) | Slides de patrocinador TriMech 2025 [EQUIPE] | Só componentes: rocker com FEA a 3 g de bump com amortecedor comprimido (rígido), massa 510 g para 257 g; bandejas com carga estimada à mão do contato do pneu. Nada de empacotamento. | B (para FEA de rocker) |
| UAS Kiel, U Pforzheim, UAS Darmstadt (EV #43, #48, #82) | Borowski e Rudolph (SAE 2025-01-0270; *Vehicles* 8(1):24, 2026; "variants" via CORE) [ACADÊMICA] | Automação com "graph-based design languages": modelos gerados automaticamente, simulação 1D de volta, otimização cinemática por enxame de partículas, otimização 3D da barra anti-rolagem; resumo cita CAD, análise estrutural e **detecção de colisão 3D**; reporta avaliar **mais de 104 variantes de suspensão em dias**, contra algumas dezenas à mão; motivação citada: ferramentas heterogêneas, troca manual de dados, integração tardia, alta rotatividade. Equipes do meio da lista, não do topo. Li só resumos; MDPI e CORE deram 403. | A (resumo) |
| EESC-USP combustão (CV #21; Design 4º Michigan 2026; 1ª no Brasil) | Nenhum material de projeto encontrado | Resultados sim, método não. A mesma escola da Tupã. Há um artigo da Tupã sobre barras de suspensão compósitas (anais Even3), que não trata de empacotamento. | C |
| FEI, Cefast (CEFET-MG), Poli Racing, Mauá, B'Energy | Busca | Nenhum design report ou artigo de projeto de suspensão encontrado. Só TCCs/artigos de outras universidades (UnB-Gama, UFV, UFU, UFC, UFTM, UNESP). | C |

Fontes de organização usadas na tabela: FS World (ranking), PDFs de resultados do FSG26 e do FSAE Michigan 2026 (seção 1).

## 3. Padrões comuns (e o quanto cada um é sustentado)

Peso das fontes: os itens 1 a 5 vêm sobretudo de juízes e organizadores (prescrição), não de observação das equipes de topo; marcados.

1. **Empacotamento global antes dos pontos de suspensão.** [JUIZ] IMechE (Anderson, Head Design Judge): "Most of (first time) 'design' is conceptual, packaging and stiffness"; gabaritos de cockpit limitam os pontos internos dianteiros e roda/pneu/freio limitam os externos, então "wishbone lengths are fairly limited". DesignJudges (Yaeger, "Simple Kinematic Philosophies"): "The chassis, driver, templates, and powertrain will limit your pickup locations to a certain range. A lot of it will wind up 'designing itself'." DesignJudges (Jones, "Conceptual and Objective Design"): posicionar os sistemas principais primeiro em CAD de blocos e só depois construir o chassi, senão o carro "cresce irreversivelmente". [EQUIPE] Revolve (resumo Gnist): suspensão e empacotamento antes do monocoque (B).
2. **Chassi e suspensão em paralelo, com pontos ainda incompletos.** [JUIZ] IMechE Parte 3: "você não precisa saber a localização exata de todos os pontos de suspensão para começar a estrutura básica do chassi"; admite fazer anteparas com os suportes já fixados (menos elegante e leve que montar a estrutura e depois os suportes, mas adequado). [JUIZ] DesignJudges (Yaeger, "Engineering A Lighter Chassis"): no chassi tubular, o powertrain ocupa espaços e "por último a suspensão precisa de pontos de fixação", o que **inverte** a ordem de UM-Rolla. As duas ordens aparecem; a escolha depende do tipo de chassi (monocoque tende a suspensão antes, B).
3. **Congelamento com data.** [JUIZ] IMechE Parte 3: design freeze é "a data após a qual nada muda salvo emergência" e deve ser posta "muito antes do que você imagina". [EQUIPE] AMZ: congelamento no fim do ano e "boot camp" de verificação cruzada antes dos desenhos. [ACADÊMICA] artigo de KBE para Formula Student (design society; página deu 503, só trecho da busca): "CAD-lock" cerca de 3 meses depois das primeiras reuniões por sistema.
4. **Fixação em nó é ideal, não restrição dura.** [JUIZ] DesignJudges (Yaeger): "Ideally, every suspension attachment should be at a node", mas "muitos projetistas se amarram em nós" e isso leva a geometria "terrível do ponto de vista de impacto, rigidez torcional e fabricação"; saída: mover pickup ao longo do eixo da bandeja (sem efeito cinemático com eixo paralelo ao plano central), ou deixar fora do nó e reforçar; "Torsional stiffness comes from triangulating the front and rear rocker mounts / shock pickups"; "use FEA for design judges when the tubes and the mounts want to be in different places". [JUIZ] IMechE Parte 3: pontos de montagem locais (inclusive "upper spring or rocker pivot mounts") exigem análise própria, e "o arranjo tipo rocker pode significar forças locais significativamente maiores". Nenhuma fonte dá distância numérica aceitável do nó.
5. **Interferência verificada no CAD completo, ao longo do curso, mais teste físico.** [OFICIAL] documentação Altair (já em `pratica/`): folgas e contato medidos em CAD importado durante o movimento. [EQUIPE] AMZ: modelo com todas as peças; [ACADÊMICA] NAU: "test-fit" da montagem final para movimento e folga. [JUIZ] IMechE: mock-up em escala real para ergonomia ("nothing beats a full size mock up you can actually sit in"). Não achei equipe que descreva varredura automatizada curso × esterço de rocker e pushrod contra tubos; o mais próximo é o paper de Borowski e Rudolph (colisão 3D automatizada).
6. **Cinemática em ferramenta e CAD paramétrico.** [JUIZ] Yaeger: "Go make a bunch of parametric sketches", "Really watch the input/output ratio through suspension travel in rocker design" (rockers mudam a razão sem querer), "The worst design decision you can make is causing binding". Ferramentas citadas por equipes: SolidWorks (Revolve), em casa (Georgia Tech), OptimumKinematics/Lotus (relatório anterior), Python sobre Excel (Cotugno).
7. **Automação no CAD**: só vi o trabalho de Borowski e Rudolph (equipes de nível médio), mais a Fusion API (relatório anterior). Equipe de topo descrevendo automação de posicionamento de pontos: não encontrada.

## 4. O que os juízes cobram (material oficial e de juízes)

**Estrutura de nota [OFICIAL]**
- **FSG26 Event Handbook v1.5** (lido): Engineering Design = 150 pontos. Overall Vehicle Concept 20 (metas e recursos 10; subsistemas e conhecimento transversal 5; **Package 5**). Mechanical/Structural 15 (**Suspension components 5**; **Primary structure 5**; **Actuators integration 5**). Vehicle Performance 30 (dinâmica e pneus 10, aero 10, otimização 10). Software 10, Powertrain 25, LV 10, Driver Interface 10, Autonomous 20, TVSD 10 (Tabela 4, DE 6.4.1; a soma dá 150).
- Formato (DE 6.3): estações em linha de produção; 15 min de julgamento por estação; **sem apresentação**, começa direto com perguntas; até 18 membros acompanhando o carro; **dois juízes por categoria: um foca em entendimento fundamental e explicação do sistema, o outro em raciocínio de engenharia detalhado**; sem feedback verbal; folhas escritas liberadas depois das finais (sessão de feedback no evento).
- **FSG "Best Practices to excel" (Weingart, artigo do evento de 2019, PDF de 2022)**: juízes começam com perguntas gerais e "mergulham rápido nos detalhes"; conhecimento avançado só nas finais; para chegar à final é preciso básico e intermediário fortes **e sinergia entre categorias**; o paradoxo que citam como exemplo: "excelente análise FEA, mas má explicação da suspensão" derruba a nota.
- **FSAE Michigan, "Design Event Description" (2022; oficial SAE)**: "não julgamos o carro tanto quanto a equipe"; cerca de **80 %** da nota é a capacidade de **projetar, construir, refinar/validar e, principalmente, entender** o carro; a ficha de pontuação com perguntas-exemplo é pública antes do evento ("teams have the exam questions in advance"); primeira rodada de ~45 min; finais para ~10 % das equipes; quem fala com o juiz tem de cobrir Suspensão/Dinâmica, Sistemas e Manufaturabilidade/Serviço. Exige Design Briefing, Design Spec Sheet de 2 páginas e desenhos 3 vistas.
- **FSG ZF Best Suspension Design Award (2008, FSG)**: critérios de Design incluem "entendimento fundamental, metas e sua realização, modelagem, simulação **e empacotamento**"; Fabricação; Teste (validação da simulação). Se o prêmio continua hoje: **não verificado**.
- **JSAE 2021 (ficha de nota, via busca, não abri)**: Suspensão vale 25 de 150 com os eixos Projeto, Construção, Refinamento/Validação, Entendimento. Michigan 2026 (pesos por categoria): **não verificado**.

**O que juízes escrevem [JUIZ]**
- DesignJudges, Jones ("Faculty Advisor's Perspective"): julga-se "como o processo de projeto levou às conclusões"; simulação impressionante vale pouco se não mudou o projeto; "o carro no chão é a verdade, não as histórias"; apresentações escritas depois da fabricação têm processo "meio falso".
- DesignJudges, Warren ("Field Guide"): perguntam "por quê" até não haver mais fundo; fixadores, limpeza e acesso ("difícil julgar um carro que não se vê nem alcança"); manufaturabilidade e serviço aparecem em toda categoria.
- IMechE (Anderson, relatório): incluir "as desvantagens da solução escolhida, não só os pontos bons"; imagens reais de peças e jigs convencem mais que renders; "não é possível nos convencer" de que algo foi otimizado com base em afirmações sem suporte; hipóteses de carga devem ser justificadas.
- Kaz Technologies (consultor/juiz, seminário 2012–13; **[JUIZ/comunitário]**): bom empacotamento é "bem pensado, bem integrado e com poucas surpresas — é onde o trabalho antecipado se paga"; perguntas a se fazer: como o subsistema suporta as metas e **como se integra aos outros**.
- Não achei material oficial ou de juiz que trate **especificamente** de rocker/pushrod ou de nós. O que vale para o assunto é indireto: justificativa, alternativas, integração, carga local.

## 5. Comparação com a SPEC da Tupã

Premissas: a SPEC aprovável é a de `SPEC_posicionador.md` com U1–U4; escopo proposto: onde os pontos PODEM ficar, sem colidir, ao longo de curso × esterço, nó como preferência.

### 5.1 O que as equipes/juízes fazem e a SPEC não faz

| Prática (fonte) | Situação na SPEC | Comentário |
|---|---|---|
| Empacotamento global em CAD antes (piloto, gabaritos, powertrain, roda/freio) e mock-up em escala (JUIZ) | A SPEC assume um CAD que já existe. Peças ausentes tornam regras NÃO VERIFICÁVEIS (§10). | Não é falha da ferramenta, mas o valor dela depende de a equipe ter o esqueleto de empacotamento. Vale uma regra de entrada: o programa se recusa a certificar (só a mapear) se faltarem classes de peça (pedal, coluna, manga/freio). |
| Congelamento com data e verificação cruzada final ("boot camp") (AMZ, IMechE) | Há "STALE quando o CAD muda" e hash. Não há conceito de data de congelamento nem de liberação. | Prática de gestão; a SPEC não precisa codificá-la, só a equipe. Registrar no EDR/cronograma. |
| FEA/análise local nos pontos fora de nó (DesignJudges, IMechE) | Fora do escopo por U1 (σ, rigidez, FEA). | Coerente com U1, mas **o juiz vai cobrar a justificativa** do ponto fora de nó e da carga local no rocker. Saída barata e informativa: reação estimada em cada ponto (pushrod ≈ 150 % da carga vertical, regra de bolso comunitária) e distância ao nó; sem entrar no laço. |
| Mover pickup da bandeja ao longo do eixo sem efeito cinemático (DesignJudges) | A4 fixa bandejas. | Só vale para pontos de bandeja com eixo paralelo ao plano central; não é rocker. Fica como opção futura, não como falta. |
| Reportar alternativas e desvantagens (IMechE, DesignJudges, Michigan: "comparação com outras opções") | Lista de candidatos com margens por restrição: **cobre bem**. | Ponto forte para a documentação do ED. |
| Checar razão de entrada/saída do rocker ao longo do curso e binding (Yaeger) | MR e curso do amortecedor já são metas; ângulo 90° como opção. | Acrescentar de forma explícita o ângulo de transmissão pushrod–rocker e rocker–amortecedor ao longo do curso como flag (já quase implícito). |

### 5.2 O que a SPEC propõe e as equipes de topo não mostram

| Proposta da SPEC | Vantagem real | Excesso provável |
|---|---|---|
| Mapa de espaço livre dos pontos do chassi + varredura curso × esterço contra peças RODA_/DIR_ e volumes do regulamento | Responde exatamente "onde posso pôr", que Yaeger descreve como o que "se projeta sozinho" e o que a equipe hoje faz à mão. Útil e novo (nenhuma ferramenta pública faz isso, segundo `pratica/`). | Nenhum, é o núcleo (E1 + parte de E2). |
| Volumes do regulamento gerados do R27 (T.1.2, F.8.x, V.3.2.4) | Evita retrabalho e erro de inspeção. | Moderado: manter só os que dependem de posição de ponto da atuação. |
| Fase I (diagnóstico de conflito) | Compatível com o histórico do Murilo (1,1 milhão de combinações sem solução): diz *por que* é vazio. | Nenhum. |
| Certificador independente com malha n e 2n, tolerância δ, geometria exata nos finalistas | Dá confiança num modelo que muda toda semana? Só se o CAD estiver completo. | **Excesso no estágio atual**: chassi incompleto, manga/pinça/disco/cremalheira não modelados (o achado 4 do REGISTRO) e δ desconhecido. Certificar sobre modelo incompleto produz falsa confiança. Manter n e 2n (barato); adiar geometria exata e δ. |
| Mutação do certificador 100 %, hash do CAD, status STALE | Disciplina de verificação do projeto; compatível com o padrão do Sistema_DDS. | Nenhum juiz cobra; custo de manutenção alto para equipe com rotatividade (o próprio Borowski/Rudolph cita "alta rotatividade" como problema das equipes). |
| CA-7: kinlib × `kinematics_model` × OptimumKinematics | Importante porque a cinemática do script do Murilo não foi validada. | Tolerar OptimumKinematics só se a licença existir; senão comparar com `kinematics_model` e com `suspension-explorer-core` como verificador externo (já em `pratica/`). |
| Adaptador Fusion (E3), rodando dentro do design vivo | Reduz iteração humana (U4). | Maior risco de prazo: ambiente Python do Fusion, `analyzeInterference` lento e exige design direto (já no relatório anterior). Nenhuma equipe de topo descreve fazer isso. |

### 5.3 Riscos de sobre-engenharia (diretos)

1. **Peso na nota é pequeno e o critério é entendimento.** Suspensão 5/150 e Package 5/150 no FSG26; ~80 % do Michigan é "entender". Um programa que a equipe não consegue explicar em 15 minutos vale menos que uma planilha entendida. Pergunta de teste: quem do time explica o mapa de espaço livre sem o Claude?
2. **Verificação mais forte que o modelo.** O certificado vale o CAD que recebe; hoje o CAD é incompleto por definição. Priorize cobertura de peças antes de rigor de tolerância.
3. **Escopo U1 correto, mas a cobrança do juiz vai ao lado.** O juiz perguntará por que o ponto está fora de nó e qual a carga local no rocker; U1 tira isso do programa. Cobrir no documento da equipe, não no código.
4. **Metas quase-igualdade.** O achado 6 do REGISTRO (conjunto viável de medida quase nula) continua o risco técnico principal. Nenhuma fonte de topo resolve isso; a mitigação é da SPEC (igualdades por construção, margens).
5. **Falta de evidência de que o método de topo seja mais simples.** Como as equipes de topo não publicam, é possível que o fluxo manual (esqueleto + iteração + congelamento) vença a automação; a SPEC deve ser vista como ferramenta de diagnóstico e de espaço, não substituto do fluxo.

### 5.4 Recomendação enxuta (decisões abertas A1–A4 do usuário continuam dele)

- Fazer E0 e E1 e a parte de varredura de E2 (cápsulas, curso × esterço, volumes mínimos do regulamento, Fase I). Entregar o mapa de espaço livre e os candidatos com margem. Postergar o adaptador Fusion até o fluxo STEP funcionar e o CAD estar mais completo.
- Impor "cobertura mínima de peças" como condição para marcar algo como candidato; sem ela, só mapa.
- Registrar no EDR a data de congelamento dos pontos (prática comum, IMechE/AMZ).
- Pedir à equipe de combustão da EESC-USP (4ª no Design do Michigan 2026) o Design Briefing e o Design Spec Sheet: é a única fonte de topo brasileira acessível, mesma escola.

## 6. Limites desta pesquisa

- Não consegui abrir: sites e GitHub de TUfast, GreenTeam, KA-RaceIng, UPV (host sem resposta ou 403); MDPI e CORE (403; **não** contornei com cabeçalho falso, o sistema negou e deixei como "não aberto"); SAE Mobilus (carregamento dinâmico); KBE design society (503); SlideShare Gnist; ficha JSAE (resposta não-PDF); página IMechE de resultados do FS UK 2026.
- Itens vindos só de resumo de busca, não do texto: FSG25 Design, FS UK 2025, FS UK 2026, JSAE 2021, resumos dos artigos Borowski e Rudolph, Cotugno, Revolve/Gnist, UPV.
- "Equipes de topo" foi definido pelo ranking FS World de 06 Sep 2026 e pelos pódios de Design recentes; Design e ranking nem sempre coincidem (TU Graz 3º no quesito ED, 14º no geral EV).
- A ausência de método publicado não significa que a equipe não tenha um.
- Nenhum ID SUS-/EDR-/TC- foi criado ou alterado.

## 7. Fontes (resumo)

- [OFICIAL] FS World ranking e dados: fs-world.org (`/ranking/ev/433/data`, `/ranking/cv/432/data`, `/university`).
- [OFICIAL] FSG26 Engineering Design Results v2 (PDF) e FSG26 Event Handbook v1.5 (formulastudent.de); FSG Best Practices (`20220717_DesignReport_BestPractice.pdf`); FSG ZF Best Suspension Design Award (2008).
- [OFICIAL] FSAE Michigan: `FSAE_2026_MI5_results.pdf`; "Design Event Description" 2022 (fsaeonline.com).
- [JUIZ] designjudges.com: Warren (Field Guide), Jones (Faculty Advisor's Perspective; Conceptual and Objective Design), Yaeger (Simple Kinematic Philosophies; Engineering A Lighter Chassis Part 1), Bachman (Strong, Stiff, Light Structures); IMechE: Anderson, Fundamentals Partes 1–3, Judges' Advice Design Report, Design Event Guidance; Kaz Technologies, "What the judges are looking for".
- [EQUIPE] amzracing.ch (newsletters), revolve.no, fsteamdelft.nl, chalmersformulastudent.se, gtms.gatech.edu, TriMech/Oxford Brookes (PDF).
- [ACADÊMICA] Borowski e Rudolph (SAE 2025-01-0270; Vehicles 8(1):24); Cotugno (UniMoRe); Rocha e Ávila (UnB, CILAMCE 2016; chassi em CAD, suspensão nos espaços livres, depois pushrod e rocker).
- [IMPRENSA] Mecânica Online e Ford (resultados FSAE Brasil 2025 e 2026).
