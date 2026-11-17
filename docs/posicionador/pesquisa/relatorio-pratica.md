# Prática de equipes e ferramentas: posição de push rod, rocker e amortecedor com o chassi tubular

Data: 2026-11-17. Parte E do plano (REGISTRO.md). Nada instalado nem executado; só leitura.
Rótulos de fonte: [OFICIAL] documentação do fabricante; [ACADÊMICA] tese, artigo ou paper técnico SAE; [COMUNITÁRIA] blog, design report, fórum (só indício); [CÓDIGO] repositório lido, sem rodar.
O que não foi conferido está escrito "não verificado".

## 1. Ferramentas de cinemática e o que fazem neste problema

| Ferramenta | O que faz no problema (rocker, MR, hardpoints) | Colisão com chassi? | Licença | Fonte |
|---|---|---|---|---|
| OptimumKinematics (OptimumG) | Solver cinemático com 400+ canais; módulo de otimização multiobjetivo que move pontos do rocker e a fixação do coilover dentro de regiões (esfera, caixa, cilindro), com fronteiras "hard" ou "soft"; objetivos usados no caso: MR em heave, ângulo rocker–push rod, ângulo rocker–coilover, comprimento do push rod, comprimento do coilover. Módulo Forces dá reações em cada ponto (exportáveis para FEA). | O caso de estudo trata empacotamento só como volumes de busca desenhados à mão ("não queremos componentes colidindo", mas a restrição é a região). Detecção de colisão com geometria CAD: **não encontrada na documentação lida; não verificado**. | Pago por módulo e por ano: Main US$795, Forces US$200, Optimization US$995 (página oficial). Há teste de 14 dias e link "Student Version" (students.optimumg.com); condições e preço da versão estudante: **não verificado**. | [OFICIAL] optimumg.com/product/optimumkinematics/ e /motion-ratio-optimization/ |
| Lotus Suspension Analysis (SHARK) | Citado em design reports de Formula Student como ferramenta de geometria. Situação atual, licença e recursos de colisão: **não verificado** (a busca não devolveu página do fabricante). | não verificado | não verificado | [COMUNITÁRIA] (indício de uso) |
| Adams/Car (MSC) | Multicorpos completo. Licença estudantil: **não verificado**. | Não lido na doc da MSC. | não verificado | — |
| Altair MotionView/MotionSolve | A doc oficial descreve o processo: o time de cinemática faz empacotamento com hardpoints, define folgas entre componentes durante o curso, e geometria CAD de suspensão e chassi pode ser importada no HyperView para medir folga e contato durante o movimento da suspensão; há exemplo de otimização de hardpoints com 26 variáveis. Licença: **não verificado**. | Sim, por pós-processamento em CAD importado (doc). | não verificado | [OFICIAL] help.altair.com (Suspension Design Process; Application Area 3 e 5) |
| SusProg3D | Não achei página oficial nem doc. Tudo sobre ele: **não verificado**. | — | — | — |

Leitura para o T11: nenhuma das ferramentas lidas escolhe nós do chassi. As que otimizam (OptimumKinematics, MotionSolve) otimizam pontos dentro de volumes que o projetista define; a colisão com tubos é checada no CAD. Isso coincide com o que o seu script do Murilo já faz (otimizar dentro de caixas) e muda só onde a colisão é calculada.

## 2. Bibliotecas abertas em Python (GitHub)

Estrelas, data do último push e licença vêm da busca do GitHub em 2026-11-17 (não conferi README de todas; não rodei nada).

| Repositório | Estrelas | Último push | Licença | O que cobre | Observação |
|---|---|---|---|---|---|
| suspension-explorer/suspension-explorer-core (antes nickmccleery/open-kinematics) | 37 | 2026-10-04 | AGPL-3.0 (≥0.6.0; há licença comercial alternativa) | Solver geométrico de duplo A; atuação direta ou push/pull rod com rocker, montado no braço ou na manga; mola, coilover ou barra de torção; barra anti-rolagem; shims. Eixos X frente, Y esquerda (compatível com o seu padrão). | [CÓDIGO]. O README diz que usar para carro de Formula Student não obriga a divulgar. Não vi colisão nem leitura de CAD. É o candidato aberto mais próximo para checar o seu `kinlib.py`. |
| ZZzyy714227/Labsus | 120 | 2026-11-16 | MIT | Achado com a busca "fsae suspension". Conteúdo: **não verificado**. | Ler README antes de qualquer uso. |
| mark-bak/BiKinematics | 7 | 2024-03-13 | sem licença declarada | Suspensão de bicicleta (4 barras, leverage ratio). | Não serve ao duplo A. |
| CAdityaNarayanan/Double-Wishbone-Simulator | 1 | 2026-06-16 | sem licença | Solver 3D duplo A (Tkinter, SciPy, NumPy). | Sem licença: não reutilizar código. |
| ColinSpilker/FSAE-Suspension-Calc | 2 | 2026-05-10 | sem licença | Solver 2D. | Idem. |
| jzerez/optimum-J | 3 | 2021-07-20 | sem licença | Clone do estilo OptimumKinematics. | Parado desde 2021. |
| SimonFrankTUM/AdvancedDualTrackModel | 17 | 2025-09-26 | BSD-3-Clause | Dinâmica veicular com cinemática de duplo A. | Dinâmica, não empacotamento. |

Conclusão: não encontrei biblioteca aberta madura que escolha pontos de push rod/rocker contra chassi tubular. O que existe resolve a cinemática; o empacotamento contra tubos é código a escrever. Busca por "bellcrank"/"rocker" não foi feita em separado (a busca de desenvolvedor por "pushrod rocker motion ratio" devolveu só o open-kinematics como relevante e um modelo de CAD de F1 gerado por código, `earthtojake/text-to-cad`, MIT, que mostra o padrão build123d + hardpoints como "lei", mas não é ferramenta de síntese).

## 3. Integração com o Fusion

### 3.1 API Python (documentação oficial)
- Scripts e add-ins em Python usam `adsk.core` e `adsk.fusion`. [OFICIAL] help.autodesk.com (Fusion API Reference e User's Manual).
- Checagem de interferência (nome confirmado na doc): `design.createInterferenceInput(ObjectCollection)` retorna `InterferenceInput`; `areCoincidentFacesIncluded` (padrão False); `design.analyzeInterference(input)` retorna `InterferenceResults`; cada `InterferenceResult` tem `entityOne`, `entityTwo` (BRepBody) e `interferenceBody` (com `.volume`); `results.createBodies(True)` cria corpos do volume interferente, **só em design direto (DirectDesignType), não em paramétrico**. Unidade interna do Fusion: centímetros (a API reporta volume em cm³ no exemplo). Entradas são ocorrências (occurrences) de componentes, não corpos soltos: cada tubo/peça deve estar num componente ou o conjunto deve ser organizado assim. Fonte: "Analyze Interference API Sample" e "InterferenceInput.areCoincidentFacesIncluded" [OFICIAL].
- Para o seu uso (varrer posições candidatas e checar colisão em cada curso), o custo prático é mover ocorrências e rodar `analyzeInterference` por candidato dentro do Fusion; é lento comparado a colisão em Python fora do Fusion. Tempo por chamada: não medido.
- Leitura de pontos de esboço e corpos: a API expõe esboços, `SketchPoint`, `BRepBody`, ocorrências e juntas; não abri cada página de referência neste levantamento (só listei pelo menu de amostras: Measure, ExportManager, STLExport, Import Manager). Tratar como "existe, detalhe a ler na doc no momento de implementar".
- Exportação: existem amostras oficiais "ExportManager API Sample", "Export to other formats API Sample" e "STLExport API Sample". Que STEP seja exportável por script: confirmado por indício [COMUNITÁRIA] (ExportKit Pro afirma que STEP, F3D/F3Z, USD e PDF funcionam em todos os tipos de licença); a página oficial de `createSTEPExportOptions` não foi aberta. Você já exportou STEP do Fusion manualmente (geo/chassi.step), então o caminho existe.

### 3.2 Licença educacional
- Oficial: plano estudantil gratuito para alunos e educadores qualificados, 1 ano renovável; uso "solely for Educational Purposes", proibido para fins comerciais ou lucrativos; a página diz "full features and functionality" [OFICIAL] autodesk.com/education/edu-software/fusion.
- A página não menciona scripts, add-ins nem exportação STEP. Que a licença educacional permita scripts e add-ins: **não verificado em texto oficial**. Um comentário de Reddit sobre o plano pessoal diz "no limits to scripts and add-ins" (isso é plano pessoal, não educacional, e é fonte [COMUNITÁRIA]). Sugestão: confirmar com um teste de 5 minutos (rodar o script "Hello World" do menu Utilities > Add-Ins) antes de depender disso.
- Aviso para equipe: uso em competição estudantil é educacional, mas patrocínio ou venda de serviço com o código pode tocar a cláusula comercial. Não é aconselhamento jurídico.

### 3.3 MCPs de Fusion
- **Oficial:** "Autodesk Fusion MCP Server", exposto pelo próprio Fusion, local, só desktop, sem autenticação; habilita em Preferences > General > API; cliente MCP com Streamable HTTP (Claude Desktop, Cursor, VS Code). Ferramentas são descobertas dinamicamente e "podem mudar". Há também "Fusion Data MCP" e "Fusion Compute MCP" (nuvem). [OFICIAL] help.autodesk.com/view/ADSKMCP; anúncio em autodesk.com/products/fusion-360/blog (2026-05-07). A lista exata de ferramentas do servidor oficial: **não verificada**. Disponibilidade para plano educacional: **não verificada**.
- **Comunitários (não oficiais):** `faust-machines/fusion360-mcp-server` (MIT; add-in + servidor TCP; ferramentas incluem `check_interference`, `create_section_analysis`, `execute_code` que roda Python arbitrário dentro do Fusion; unidades cm); `zkbkb/fusion-mcp` (licença não declarada claramente: "NOASSERTION"); `neka-nat/freecad-mcp` é para FreeCAD (3372 estrelas, MIT), não Fusion. Para este caso o MCP é conveniência de exploração (ler o modelo interativamente), não o caminho do script reprodutível. `execute_code` abre execução arbitrária: usar só com código revisado.

## 4. Geometria fora do Fusion

| Opção | Para que serve aqui | Vantagens | Limites |
|---|---|---|---|
| OpenCascade via CadQuery/OCP, build123d, pythonocc | Ler o STEP, extrair eixos de tubo (cilindros), fazer interseções booleanas e distância mínima exata entre sólidos BRep | CadQuery 6125★ (push 2026-11-16, licença marcada "other"; verificar), build123d 3742★ (Apache-2.0, push 2026-11-16), pythonocc-core 2001★ (LGPL-3.0, push 2026-11-17). Resolução exata, sem tesselação; leem STEP AP214 como o seu. `cadquery-ocp` (binding OCP): estrelas não verificadas. | Booleanas BRep em muitos candidatos são lentas (o próprio `text-to-cad` usa filtro por malha antes de medir com o kernel, [CÓDIGO]); instalação binária pesada. |
| trimesh + python-fcl | Colisão e distância mínima rápidas entre malhas ou primitivas | trimesh 3724★ (MIT, push 2026-11-13). `CollisionManager` oferece `in_collision_single`, `min_distance_single`; para malhas convexas usa `Convex`, mais rápido e preciso do que BVH, e dá distância com sinal; [OFICIAL do projeto] trimesh.org/trimesh.collision.html. | Precisa de `python-fcl` instalado; repositório oficial do python-fcl não conferido (a busca devolveu forks): estrelas e licença do python-fcl **não verificados** (FCL em si: 1775★, push 2026-11-15, licença "other"). BVH de malha não convexa dá distância menos confiável (discussão no repositório do trimesh). Malha tesselada tem erro de corda: usar tolerância. |
| FreeCAD (Python) | Alternativa ao OCC para ler STEP e medir distância | 35537★, LGPL-2.1, ativo | Ambiente próprio; mais pesado que build123d para um script. |

Tubo como cápsula, malha ou BRep:
- **Cápsula (segmento + raio):** a distância entre um ponto/segmento e o eixo do tubo é fórmula fechada, vetorizável em NumPy, milhões de candidatos por segundo. Serve ao laço de otimização. Limite: ignora solda, curvatura de tubo dobrado e nós (cada junta tem volume maior que a soma das cápsulas).
- **Malha (trimesh + FCL):** boa para peças de forma livre (aro, pinça, manga, gabarito); erro de tesselação controlável; colisão rápida. Bom para validar um candidato já escolhido.
- **BRep (OCC):** exato; use para o conjunto final e para extrair eixos e diâmetros dos cilindros do STEP; caro por candidato.
- Padrão que o próprio código do `text-to-cad` adota (filtro grosso por caixa e malha, medida exata só nos pares duvidosos) é o modelo de pipeline em camadas [CÓDIGO].

## 5. Práticas descritas por equipes e literatura

Sequência de projeto e acoplamento:
- UM-Rolla (Gaffney e Salinas, SAE 1997) [ACADÊMICA/SAE]: define pista, entre-eixos, pneu e roda; parâmetros de suspensão (camber, caster, KPI, raio de scrub, centro de rolagem); modela a cinemática; entra os pontos no CAD sólido e checa interferência ao longo do curso **antes** de projetar o chassi; modela componentes maiores como pontos de montagem e volumes aproximados, "com espaço suficiente para sistemas ainda não projetados"; só então "liga os pontos" com tubos por triangulação. Também escreve que a suspensão deve ser projetada **concorrentemente** com o chassi e que o ponto de fixação dos braços pode mover-se ao longo do eixo de rotação do braço sem alterar a cinemática.
- NAU (Initial Design Report, capstone 2025–26) [ACADÊMICA/relatório de curso, uso como indício]: o subtime de suspensão e o de chassi se influenciam; o problema principal é "figuring out the mounting points"; usam vários softwares de cinemática para otimizar os pontos. 
- Cal Poly (projeto de chassi híbrido) [ACADÊMICA/relatório]: "design suspension point location for chassis stiffness; design suspension and chassis together" e menciona pick-ups de suspensão, de ARB e de rocker como parte do projeto do chassi. Detalhe não lido (só trecho).
- MIT, Harvey 2018, "The Optimization of a Formula SAE Vehicle's Suspension Kinematics" [ACADÊMICA]: citada por outros relatórios; **não lida por mim** (só a referência).
- Resumo da sequência observada nas fontes: (1) parâmetros de carro; (2) geometria de cinemática; (3) hardpoints e checagem de interferência no CAD; (4) chassi como "ligar os pontos" com triangulação; com iteração concorrente. Ou seja, nas fontes lidas a cinemática vem primeiro e o chassi se fecha em volta; mas todas dizem que é iterativo. Nenhuma fonte lida trata de resolver rocker, amortecedor e nós com otimização conjunta automática.

Nós, abas (tabs) e distância do nó:
- Regra de bolso ("ideal: toda fixação de suspensão em um nó"): DesignJudges, "Engineering A Lighter Chassis, Part 1", Skitter Yaeger, 2023, atualizado 2026 [COMUNITÁRIA, autor ligado a juízes de projeto da competição]. O mesmo texto diz que muitos projetistas "se amarram em nós" tentando pôr toda fixação em nó e que isso pode levar a geometria extrema de chassi; para o braço superior propõe: mover pickups ao longo do eixo do braço (sem efeito cinemático quando o eixo é paralelo ao plano central), retificar caminhos de carga, ou afastar do nó em local já rígido (ex.: aro frontal) e compensar com material e FEA; e tratar `Torsional stiffness comes from triangulating the front and rear rocker mounts / shock pickups`. Valor numérico de distância aceitável do nó: **a fonte não dá**.
- Estimativas de carga do mesmo texto (como ponto de partida): braço inferior ~150 % da força de pneu; superior ~50 % em sentido oposto; push rod ~150 % da carga vertical (direto: ~120 %). Fonte comunitária; use só como ordem de grandeza e confira com seu cálculo.
- UM-Rolla [ACADÊMICA/SAE]: tabs soldadas no meio de um único trecho de tubo fizeram o tubo dobrar como viga biapoiada e falharam (tubo fraturado ou aba rompida); no carro de 1996 todos os componentes muito carregados foram ligados a pontos triangulados. É evidência direta do seu item "fixação fora de nó causa flexão".
- Regra de regulamento sobre pontos de fixação, SES e distância do nó: é a parte D do plano (regras/RELATORIO_REGRAS.md), não duplico.
- "Spaces claim" / volumes reservados: o termo aparece na prática de Altair (doc oficial: folgas e contato medidos em CAD importado ao longo do movimento) e em UM-Rolla (volumes aproximados de componentes). Não achei design report de equipe que formalize "espaço reservado" com nome; o uso é implícito.
- Comunitárias: não achei, neste levantamento, apresentações de equipes conhecidas (por exemplo, MIT, TU Graz, Delft) sobre o método de posicionar rocker contra chassi; a busca devolveu relatórios de curso e vídeos. Lacuna declarada.

## 6. Recomendação de pilha para o T11 (equipe estudante, Fusion educacional, Python)

Princípio: o Fusion fornece geometria e conferência visual; o Python (que o Sistema_DDS já tem) faz a busca. Separar em camadas, cada uma com sua verificação.

**Camada A: entrada do CAD (feita uma vez por rodada de chassi).**
- Exportar STEP do Fusion (já feito manualmente). Opcional: um script Fusion de ~50 linhas (API Python oficial) que exporta STEP e os pontos de esboço marcados (nomes de pontos como `UCA_in_F`) para JSON, em mm. Pré-condição a testar: scripts rodam na sua licença educacional.
- Ler o STEP em Python com build123d ou CadQuery/OCP (cilindros → eixo, raio, extremos), montar `tubos.json` e `nos.json` (nós = interseções de eixos dentro de tolerância). Parte A do plano já faz isso.

**Camada B: busca de candidatos em Python, sem Fusion.**
- Tubo = cápsula (NumPy, vetorizado); gabarito, aro, manga e freio = malha ou primitiva simples; checagem rápida na cinemática inteira (curso, esterço).
- Restrições como funções de folga contínuas e **desigualdades com margem**, não quase-igualdades (achado 6 do REGISTRO). Variáveis discretas para "em qual nó" e "qual tubo", variáveis contínuas só para o que sobra. Isso transforma a força bruta de 1,1 milhão em enumeração pelos nós candidatos e otimização local (SciPy) dentro de cada combinação. É uma recomendação minha; as fontes lidas não validam esse método.
- Cinemática de apoio: o próprio `kinlib.py` já usado; conferir contra suspension-explorer-core (AGPL; usar só como verificador externo, não incorporar, para evitar a obrigação de licença) e, se a equipe tiver licença, contra OptimumKinematics (módulo Main) como REFERENCE (EDR-004).

**Camada C: verificação exata do candidato final.**
- Interferência exata e distâncias mínimas: OCC (build123d) ao longo do curso, ou `analyzeInterference` no Fusion em design direto, com os componentes montados em ocorrências. Uso do Fusion aqui é a segunda opinião visual para a equipe.

**Opcional: MCP do Fusion.** O servidor oficial é local e sem autenticação; use para inspeção interativa. Não colocar no caminho do resultado: as ferramentas mudam e a execução não é reprodutível.

### Prós
- Reaproveita o que existe (kinlib, STEP, parte A do plano); sem licença paga; Python em tudo o que importa para decisão; busca rápida porque cápsula e NumPy dispensam o Fusion.
- Fusion fica só como fonte de geometria e conferência; troca de versão do Fusion quebra pouco.

### Contras
- Código novo para ler STEP, extrair nós e montar restrições; ninguém no GitHub resolve isto pronto.
- Duas fontes de verdade de geometria (STEP exportado e CAD vivo) exigem disciplina de versão: cada rodada de busca registra o hash do STEP.
- Cápsula ignora o volume da solda e o raio de dobra.

### Riscos
1. Licença educacional: permissão para scripts/add-ins e MCP **não confirmada em texto oficial**; uso estritamente educacional. Mitigação: teste de 5 minutos; manter a Camada A funcionando só com exportação manual de STEP.
2. `analyzeInterference` exige design direto para criar corpos de interferência; modelo paramétrico do chassi precisaria de cópia direta. Custo por chamada desconhecido.
3. Modelos incompletos: o chassi ainda não tem todos os tubos; qualquer candidato "viável" pode virar inviável quando um tubo novo aparecer. Mitigação: reservar volumes (cápsulas fantasma) para tubos previstos e reexecutar a cada versão do STEP.
4. Licenças de código: suspension-explorer-core é AGPL; ZZzyy714227/Labsus e outros sem licença não devem ser copiados.
5. Dado numérico de "distância aceitável do nó": nenhuma fonte lida dá número; deve vir do regulamento (parte D) ou de FEA da própria equipe (a prática descrita por DesignJudges e UM-Rolla é comparar nó contra fora-de-nó por FEA). Não inventar limite.
6. Fontes comunitárias (DesignJudges, MCPs de terceiros, ExportKit, Reddit) são só indício; as afirmações de licença e o nome das chamadas de interferência são as que têm base oficial.

## Fontes consultadas
- OFICIAL: optimumg.com/product/optimumkinematics/; optimumg.com/motion-ratio-optimization/; help.autodesk.com (Fusion API: Analyze Interference API Sample; InterferenceInput.areCoincidentFacesIncluded); help.autodesk.com/view/ADSKMCP (Autodesk Fusion MCP Server); autodesk.com/products/fusion-360/blog (anúncio Fusion MCP); autodesk.com/education/edu-software/fusion; help.altair.com/hwdesktop (Suspension Design Process) e hwsolvers (Application Areas 3 e 5); trimesh.org/trimesh.collision.html.
- ACADÊMICA: Gaffney e Salinas, "Introduction to Formula SAE Suspension and Frame Design" (SAE, 1997, racing.byu.edu); NAU Formula SAE Suspension Initial Design Report (ceias.nau.edu); Cal Poly, Formula SAE Hybrid Carbon Fiber Monocoque/Steel Tube Frame Chassis (digitalcommons.calpoly.edu); referenciada e não lida: W. Harvey, MIT 2018.
- COMUNITÁRIA: designjudges.com "Engineering A Lighter Chassis, Part 1"; exportkitpro.com; reddit r/Fusion360 e r/FSAE (o r/FSAE sobre Lotus Shark não foi aberto: o scraper recusou); repositórios GitHub citados na seção 2 e 3.3.
- Não consegui abrir: Reddit r/FSAE (Lotus Shark em 2024); páginas oficiais de SHARK, SusProg3D e Adams Car; página oficial de `createSTEPExportOptions`.
