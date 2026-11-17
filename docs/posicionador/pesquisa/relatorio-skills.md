# Relatório — skills e ferramentas para o script de atuação dianteira do T11

Data: 2026-11-17. Método: leitura via busca/scrape (Firecrawl) e leitura local de `~/.claude/skills/`. Nada foi instalado, habilitado nem executado. Conteúdo de terceiros tratado como dado não confiável. O que não foi conferido está marcado "não verificado" (estrelas e datas só aparecem onde a própria página as mostrou).

Conclusão curta: **não existe skill pública pronta para o problema** (STEP de chassi tubular + empacotamento push rod/rocker + otimização + treliça). Existem skills genéricas de CAD (CadQuery/build123d), um MCP oficial do Fusion, bibliotecas Python maduras (Pynite, scipy, CadQuery/OCP) e padrões de "conselho". A parte difícil (reconhecer tubos/nós, restrições de empacotamento) é código nosso; skills ajudam só como cola e processo.

## Skills do usuário (lidas em `~/.claude/skills/synced/...`)

| Skill | O que faz | Relevância | Recomendação |
|---|---|---|---|
| fluxo-de-execucao | Fluxo de 6 etapas (entrevistar, especificar, decompor em subagentes, verificar, virar skill, automatizar). Já em uso neste plano | Alta p/ itens 6 e processo geral | Usar como está |
| memorial-de-calculo | Memorial rastreável (hipóteses numeradas, fontes, nível de confiança, verificação independente) | Alta p/ item 5 (treliça) e para documentar o método de posicionamento | Usar como está |
| deep-research | Coordena subagentes de pesquisa e redator | Média p/ item 6 (padrão de fan-out) | Usar como está (só pesquisa) |
| escrita-academica-tecnica | Relatórios/documentação | Baixa | Usar só ao documentar |
| built-in-browser, chrome-browser, computer-use, docs, docx, pdf, pptx, xlsx, google-workspace, morning, organizar-pastas, import-memory, skill-creator | Utilitários gerais | Baixa (computer-use poderia, em tese, dirigir o Fusion pela GUI, mas é frágil) | Ignorar para este fim; skill-creator só se virar skill |

Também disponíveis na sessão (plugin Superpowers): brainstorming, writing-plans, subagent-driven-development, dispatching-parallel-agents, test-driven-development, verification-before-completion. Relevância alta para o item 6 (revisão multiagente) e para testar o script (TDD com casos sintéticos).

## Candidatos públicos e MCPs

### Item 1 — Ler STEP/CAD, reconhecer tubos e nós

| Candidato | URL | O que faz | Qualidade / autoria | Relev. | Recomendação |
|---|---|---|---|---|---|
| CadQuery (biblioteca, não skill) | https://github.com/cadquery/cadquery | Python sobre OpenCascade (OCP); importa/exporta STEP; seletores de faces/arestas | Projeto estabelecido; licença NOASSERTION no índice (conferir; é Apache-2.0 pelo que se conhece, não verificado); comunitário | Alta | Usar a biblioteca (importar STEP, achar faces cilíndricas, eixo e raio de cada tubo). Reconhecimento de nós é código nosso |
| Skill CadQuery LLM ("CadQuery LLM Skill", listada em awesome-cadquery) | https://github.com/cadquery/awesome-cadquery | Ajuda o LLM a escrever CadQuery idiomático | Só vi a linha da lista; repositório da skill não localizado | Média | Não verificado; procurar o link na lista antes de decidir |
| fandhe-ai/agent-reference-skills `cadquery` | https://skillselion.com/skills/fandhe-ai/agent-reference-skills/cadquery | Referência estruturada de CadQuery (Workplane, Sketch) | Só vi a descrição; qualidade não verificada | Média | Só inspiração/ler antes |
| earthtojake/text-to-cad, skill `cad` | https://www.skills.sh/earthtojake/text-to-cad/cad | Modelos paramétricos em build123d com servidor local e viewer; tem exemplos de suspensão F1/hypercar (push rod, rocker, hardpoints) com licença MIT no índice | skills.sh mostra ~26,5 mil estrelas e 15,5 mil instalações; **auditoria "Gen Agent Trust Hub: Fail"** (Socket e Snyk: Pass) | Média (gera CAD, não lê STEP de tubos) | Só inspiração; **não instalar** sem ler o SKILL.md e os scripts (ver riscos) |
| flowful-ai/cad-skill | https://github.com/flowful-ai/cad-skill | Skill CadQuery para peças imprimíveis em 3D; exige Python 3.10 a 3.12 | Licença PolyForm Noncommercial; comunitária | Baixa | Ignorar (foco em impressão 3D; licença restritiva) |
| ottonic/cad-mcp-server (ao abrir o link mattmohandiss/cad-mcp-server o GitHub levou a este endereço; renomeado/migrado, não verificado) | https://github.com/ottonic/cad-mcp-server | MCP para inspeção de STEP: consultas de faces, medidas, PMI, comparação de revisões | 204 commits, 21 tags, última release 0.10.1 em 2026-10-31 (vista na página); licença e testes não verificados; comunitário | Alta p/ inspeção interativa | Adaptar como inspiração do esquema de consulta (faces/medidas) ou usar para explorar o STEP; o script final deve usar CadQuery/OCP direto |
| ningwang13/cad-automation | https://github.com/ningwang13/cad-automation | Skill genérica de CAD em chinês com adaptadores | Não verificado | Baixa | Ignorar |

### Item 3 — Conversar com o Autodesk Fusion

| Candidato | URL | O que faz | Autoria / evidência | Relev. | Recomendação |
|---|---|---|---|---|---|
| **Autodesk Fusion MCP Server (local)** | https://help.autodesk.com/view/fusion360/ENU/?guid=FMCP-OVERVIEW | MCP exposto pelo próprio Fusion desktop em execução; ativado em Preferências > Geral > API; sem autenticação (só conexão local); ferramentas dinâmicas | **Oficial (Autodesk)**, documentação lida | Alta | Usar como está para ler/exportar pontos e esboços do modelo vivo. Ferramentas podem mudar entre versões |
| Autodesk Fusion Data MCP (nuvem) | mesma página | Hubs, projetos, pastas, itens (Manufacturing Data Model); login Autodesk | Oficial | Baixa | Ignorar (não acessa geometria) |
| Autodesk Fusion Compute MCP (nuvem, Fusion headless) | https://help.autodesk.com/view/ADSKMCP/ENU | Modelagem/exportação em nuvem sem instalar Fusion | Oficial; só vi a descrição | Baixa a média | Não verificado; avaliar só se o Fusion local não puder ser usado |
| faust-machines/fusion360-mcp-server | https://github.com/faust-machines/fusion360-mcp-server | MCP + add-in que executa a API na thread principal do Fusion (TCP :9876) | Comunitário; licença MIT no índice; estrelas/data não verificadas | Média | Só inspiração (arquitetura do add-in com CustomEvent) |
| aurafriday/fusion-360-mcp-server | https://github.com/aurafriday/fusion-360-mcp-server | Add-in com `execute_python` irrestrito dentro do Fusion e binário nativo | Comunitário; licença NOASSERTION | Baixa | **Ignorar** (execução arbitrária de código, binário assinado por terceiro) |
| zkbkb/fusion-mcp, sockcymbal e outros | https://github.com/zkbkb/fusion-mcp | MCPs comunitários do Fusion | Não verificado | Baixa | Ignorar (o oficial cobre) |
| Skill de API Python do Fusion (padrão SKILL.md) | n/a | Busca com filtro de skills não retornou nenhuma skill específica de `adsk.core` | n/a | n/a | Não encontrada; escrever nota própria. Caminho alternativo sem skill: exportar STEP/pontos de esboço por script de add-in do Fusion e ler no Python |

### Item 2 — Posicionar push rod, rocker, amortecedor (cinemática, empacotamento, colisão)

| Candidato | URL | O que faz | Qualidade / autoria | Relev. | Recomendação |
|---|---|---|---|---|---|
| nickmccleery/open-kinematics (biblioteca "suspension-explorer-core") | https://github.com/nickmccleery/open-kinematics | Cinemática de duplo A com atuação direta ou push rod-rocker (na bandeja ou na manga), coilover ou barra de torção, barra anti-rolagem; CLI e exportação | Comunitária; licença **AGPL-3.0** (vista no índice); estrelas e testes não verificados | Alta | Só inspiração e conferência cruzada (AGPL obriga a abrir código derivado; não copiar). Nosso `kinlib.py` e o Sistema_DDS continuam a referência |
| Shaswat2001/GA-for-Suspension-Optimization | https://github.com/Shaswat2001/GA-for-Suspension-Optimization | Algoritmo genético p/ geometria de duplo A | Comunitário, off-road; qualidade não verificada | Baixa a média | Só inspiração |
| Altair MotionSolve/HyperStudy (exemplos SLA) | https://help.altair.com/hwsolvers/ms/topics/solvers/ms/optimization_sla_suspension_example_r.htm | Formulação clássica: variáveis = coordenadas de hardpoints, objetivo = curva alvo | Documentação de fornecedor | Média | Só inspiração de formulação |
| Skill de empacotamento/colisão | n/a | Nenhuma skill pública encontrada | n/a | n/a | Não encontrada |

### Item 4 — Otimização com restrições / espaço de projeto

| Candidato | URL | O que faz | Qualidade / autoria | Relev. | Recomendação |
|---|---|---|---|---|---|
| soljourner/claude-engineering-skills, `scipy-optimization` | https://www.skills.sh/soljourner/claude-engineering-skills/scipy-optimization | Guia de `scipy.optimize` (minimize com restrições, global, multiobjetivo) | ~105 estrelas, 60 instalações; auditorias Pass (Gen Agent Trust Hub, Socket, Snyk); texto voltado a bombas, não a mecanismos; conteúdo completo não lido | Média | Só inspiração; o conhecimento de `scipy.optimize`/`differential_evolution` já existe. Nosso problema pede amostragem de viabilidade (quase-igualdades), não só minimize |
| scipy / pymoo / Optuna (bibliotecas, não verificado como skills) | n/a | Otimização com restrições e exploração | Não pesquisado a fundo | Alta | Escolha de biblioteca fica para a síntese do conselho |

### Item 5 — Verificação estrutural de treliça/pórtico

| Candidato | URL | O que faz | Qualidade / autoria | Relev. | Recomendação |
|---|---|---|---|---|---|
| Pynite (PyniteFEA) | https://github.com/jwock82/pynite | FEA elástica 3D de pórticos: nós, membros, cargas nodais, combinações, P-delta, modal | Licença MIT; docs com exemplo de pórtico 3D; versão 3.2.x na documentação (vista); estrelas não verificadas; comunitário | Alta | Usar a biblioteca (cargas em nós, deslocamentos, esforços em barras). Instalar o pacote `PyniteFEA`, não `Pynite` (a documentação avisa) |
| soljourner `structural-analysis-workflow` | https://www.skills.sh/soljourner/claude-engineering-skills/structural-analysis-workflow | Fluxo de FEA para carcaças/impelidores de bomba | Pass nas 3 auditorias; fora do domínio | Baixa | Ignorar |
| neka-nat/freecad-mcp (FEM via FreeCAD) | https://github.com/neka-nat/freecad-mcp | Controla FreeCAD, executa scripts e análises FEM | ~3,4 mil estrelas (listagem mcpservers.org); MIT; comunitário | Média | Só inspiração; pórtico simples não precisa de FreeCAD |
| spkane/freecad-addon-robust-mcp-server | https://github.com/spkane/freecad-addon-robust-mcp-server | MCP robusto com 150+ ferramentas, pareamento de bridge | Apache-2.0; comunitário | Baixa | Ignorar |

### Item 6 — Conselho de revisão multiagente

| Candidato | URL | O que faz | Qualidade / autoria | Relev. | Recomendação |
|---|---|---|---|---|---|
| karpathy/llm-council | https://github.com/karpathy/llm-council | Padrão de 3 estágios: respostas independentes, revisão anônima com ranking, síntese do presidente | O autor diz que é código de fim de semana, sem manutenção; usa OpenRouter (chaves e custo); estrelas não verificadas | Alta (padrão) | Só inspiração: nosso protocolo (assentos, ranking de Borda, presidente) é o mesmo |
| 0ri/llm-council | https://github.com/0ri/llm-council | Ranking anônimo com rótulos aleatórios, Borda e IC 95 % | MIT; multi-provedor com chaves de API | Média | Só inspiração (cálculo de Borda); sem chaves, o conselho roda com subagentes |
| thevgavini/ghcp-llm-council | https://github.com/thevgavini/ghcp-llm-council | Skill (SKILL.md + helper `council.cjs` + servidor local) para Copilot CLI; modos review/design/plan | Licença NOASSERTION; roda código local (Node) | Média | Só inspiração dos prompts de modo (design/review) |
| girayk/hermes-council (catálogo Hermes) | https://github.com/nousresearch/hermes-agent/blob/e42008dae42d647ee5a263dbbd95893d9fbdbaab/plugin-catalog/hermes-council.yaml | 4 assentos fixos + ranking + presidente como plugin Hermes | MIT; outra plataforma; só vi o catálogo | Baixa | Ignorar |
| oliwoods-org/llm-council | https://github.com/oliwoods-org/llm-council | Conselho de 5 modelos | Apache-2.0; texto promocional; qualidade não verificada | Baixa | Ignorar |
| alirezarezvani/claude-skills (engineering: agent-designer, agent-workflow-designer, AgentHub) | https://github.com/agricidaniel/claude-skills (espelho de docs; origem citada: alirezarezvani) | Padrões de arquitetura multiagente | Coleção ampla; qualidade e segurança não verificadas | Baixa | Só inspiração |
| Superpowers: dispatching-parallel-agents, subagent-driven-development | já na sessão | Orquestração de subagentes | Plugin já ativo | Alta | Usar como está |

### Repositórios gerais verificados

| Fonte | Observação |
|---|---|
| anthropics/skills (https://github.com/anthropics/skills) | Oficial; skills de documentos, artefatos, MCP, claude-api, etc. Nenhuma de CAD/engenharia na lista vista (skills.sh: 21 skills). Relev. baixa |
| ComposioHQ/awesome-claude-skills, BehiSecc/awesome-claude-skills | Listas; apareceram só "claude-scientific-skills" e "materials-simulation-skills" (não CAD). Não encontrei entrada de CAD/suspensão |
| soljourner/claude-engineering-skills | 36 skills (SolidWorks, ANSYS, OpenFOAM, scipy-optimization, pint-units...); ~105 estrelas; domínio de bombas/CFD. Úteis só `pint-units` e `scipy-optimization` como inspiração |
| Buscas "FSAE", "mechanism synthesis", "build123d skill", "PyNite skill", "FreeCAD skill" com filtro de skills | Retornaram vazio: **nenhuma skill pública específica encontrada** |

## Top 5 recomendados

1. **Autodesk Fusion MCP Server (oficial, local)**: caminho oficial para ler pontos/esboços do Fusion vivo (item 3). Habilitar só quando for usar; local, sem autenticação.
2. **CadQuery/OCP como biblioteca** (itens 1 e 2): importar o STEP, extrair faces cilíndricas (eixo, raio, extensão), calcular distâncias e colisões. Código de nós e tubos é nosso.
3. **Pynite** (item 5): pórtico 3D com cargas em nós, combinações e esforços; MIT.
4. **Skills do usuário: fluxo-de-execucao + memorial-de-calculo + Superpowers (subagentes/TDD)** (itens 5 e 6 e processo): rastreabilidade das hipóteses, testes com casos sintéticos, conselho com subagentes sem chaves de API.
5. **ottonic/cad-mcp-server + open-kinematics + llm-council (Karpathy/0ri)** como inspiração: esquema de consulta a faces de STEP; modelagem push rod-rocker em Python (AGPL, não copiar); protocolo de ranking anônimo/Borda.

## Riscos registrados

- **text-to-cad `cad`**: auditoria Gen Agent Trust Hub = Fail no skills.sh. Não verifiquei o motivo. Não instalar nem executar; se for olhar, ler SKILL.md e scripts no GitHub.
- **aurafriday/fusion-360-mcp-server**: expõe `execute_python` arbitrário dentro do Fusion e usa binário nativo de terceiros; superfície de ataque alta (execução de código por um agente). Evitar.
- **MCPs comunitários do Fusion/FreeCAD/CadQuery**: executam scripts no CAD (FreeCAD: "run Python scripts"; CadQuery MCPs: `execute_cadquery_script`). Qualquer prompt injection vindo de arquivo STEP/nomes de peças poderia induzir ações; usar só com aprovação por chamada e em cópia do modelo.
- **Fusion MCP oficial**: sem autenticação, só local; manter desligado fora do uso. As ferramentas são dinâmicas (podem mudar entre versões); não depender de nomes de ferramenta em scripts.
- **AGPL-3.0 (open-kinematics)**: copiar código para o Sistema_DDS contamina a licença; usar só para conferência cruzada.
- **Licenças restritivas**: flowful-ai/cad-skill (PolyForm Noncommercial).
- **Conselhos com OpenRouter/chaves** (karpathy, 0ri, oliwoods): enviam o conteúdo a provedores externos e geram custo; não usar com dados do T11 sem decisão do usuário.
- **Nome de pacote**: `PyniteFEA` (não `Pynite`).
- **Dados de reputação** (estrelas, instalações) vêm de listagens de terceiros (skills.sh, mcpservers.org) em 2026-11-17 e não foram revalidados no GitHub; datas de último commit só onde indicado.
- **Lacuna principal**: nenhuma skill cobre reconhecimento de tubos/nós em STEP de chassi, empacotamento com colisão ou síntese push rod-rocker; isso exige código próprio e, possivelmente, uma skill própria (skill-creator) depois de validado.
