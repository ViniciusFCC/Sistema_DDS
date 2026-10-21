<!--
Documento recebido do usuário em 2026-10-20 (colado na conversa), registrado sem alteração de conteúdo.
A origem do roadmap V0–V5 não está nos arquivos do projeto (busca em docs/, HANDOFF, importado-claude-ai e
Sistema_DDS_CONTEXTO_COMPLETO.md sem ocorrência de "CarSim", "V5" ou "Engineering Loop"); o próprio texto diz
"o roadmap discutido". A comparação com o Definitive Guide e os complementos estão em docs/arquitetura-planejada.md.
-->

# Tupã Suspension System
## Arquitetura planejada, roadmap de versões e fases de engenharia

**Tipo:** Referência-mestra de arquitetura planejada  
**Projeto:** Tupã Formula SAE EV — Suspension System  
**Idioma:** Português (Brasil)

**Escopo:** registrar o que foi concebido para o sistema, suas versões, fases, módulos, integrações, convenções e governança.

**Importante:** este documento não é um relatório de progresso nem uma lista do que falta implementar. O objetivo é descrever a arquitetura pretendida. As decisões estabelecidas, os planos, as propostas e os pontos ainda sem definição são diferenciados para evitar que hipóteses sejam interpretadas como decisões aprovadas.

---

# 1. Propósito e visão geral

O **Tupã Suspension System** foi concebido como um sistema integrado de engenharia para dimensionar, analisar, comparar, otimizar e validar a suspensão de um veículo Formula SAE elétrico.

O sistema não deve ser entendido como apenas uma planilha Excel, um script Python ou um modelo de cinemática. A arquitetura reúne:

1. **Padrão técnico de engenharia:** equações, hipóteses, convenções, critérios de validade e limites de aplicação.
2. **Modelos computacionais:** cálculos de dinâmica veicular, suspensão e, progressivamente, pneus e veículo completo.
3. **Ferramentas especializadas de referência:** caracterização e verificação de domínios específicos.
4. **Interface Excel:** entradas, configuração, comparação de cenários, rastreabilidade, validação e visualização.
5. **Integração e contratos de dados:** intercâmbio entre CAD, ferramentas de referência, Python, Excel e simulação de veículo.
6. **Verificação e validação:** distinção entre consistência matemática, concordância entre implementações e correspondência com o veículo físico.
7. **Ciclo de engenharia experimental:** comparação das previsões com medições reais e atualização controlada dos modelos.

## 1.1 Objetivos

- Dimensionar a suspensão a partir de metas físicas e restrições de projeto.
- Relacionar objetivos de dinâmica veicular a parâmetros de suspensão e componentes.
- Tornar explícitas as hipóteses, fontes e limitações dos cálculos.
- Integrar geometria, cinemática, rigidez, pneus, cargas e desempenho.
- Permitir análise de sensibilidade e comparação de alternativas.
- Evitar que dados demonstrativos sejam confundidos com dados reais ou metas aprovadas.
- Preservar rastreabilidade entre requisitos, metas, parâmetros, equações, resultados e evidências.
- Usar ferramentas especializadas quando agregarem autoridade técnica, sem duplicá-las desnecessariamente.
- Correlacionar os modelos com ensaios físicos.
- Preservar e ampliar o conhecimento técnico entre gerações do veículo.

## 1.2 O que o sistema não pretende ser

O sistema não pretende:

- Ser apenas uma planilha com fórmulas sem documentação técnica.
- Tratar concordância entre Excel e Python como prova de validade física.
- Substituir o OptimumKinematics por um clone próprio de cinemática 3D.
- Tratar valores sintéticos como dados reais do carro.
- Considerar um resultado validado apenas porque o código executou sem erros.
- Incorporar todas as análises avançadas desde a primeira versão.
- Alterar automaticamente o padrão técnico sempre que uma implementação for modificada.
- Tratar uma ferramenta como autoridade universal para todos os domínios.

---

# 2. Versões versus fases

## 2.1 Versões: evolução das capacidades do sistema

Uma **versão** representa uma camada de capacidade que o sistema deve adquirir ao longo da sua evolução: o que será capaz de modelar, calcular, integrar ou validar.

O roadmap discutido estabelece as versões V0–V5. Elas são cumulativas em intenção: as capacidades anteriores formam a base das posteriores, salvo mudança formal de arquitetura.

## 2.2 Fases: processo de desenvolvimento e engenharia

Uma **fase** representa um conjunto de atividades que transforma uma necessidade em formulação, implementação e evidência aceitável.

A nomenclatura formal das fases específicas do Suspension System não está consolidada em uma única lista numerada no contexto disponível. Por isso, a seção de fases deste documento apresenta um processo de trabalho proposto, não uma declaração de que todas essas fases já foram formalmente aprovadas.

As fases do Suspension System também não devem ser confundidas com as fases organizacionais do projeto anual do carro — Pré-design, Design, Fabricação e Testes/Validação.

## 2.3 Classificação das informações

- **Decisão estabelecida:** base técnica ou arquitetural definida.
- **Planejado:** capacidade prevista no roadmap.
- **Proposta:** solução organizacional ou técnica que pode exigir aprovação.
- **A definir:** informação ainda insuficiente para declarar uma decisão final.

---

# PARTE I — ROADMAP DE VERSÕES

## 3. Visão geral

| Versão | Nome conceitual | Papel principal |
|---|---|---|
| **V0** | Foundation / Engineering Framework | Governança, convenções, rastreabilidade, contratos e arquitetura técnica. |
| **V1** | Vehicle Dynamics & Suspension Sizing | Núcleo de dinâmica veicular e dimensionamento inicial da suspensão. |
| **V2** | Kinematics Integration | Geometria 3D e cinemática a partir de hardpoints e posições operacionais. |
| **V3** | Tire + CarSim + Vehicle Performance | Modelo de pneu e análise do desempenho do veículo completo. |
| **V4** | Optimization / Multidisciplinary Design | Exploração paramétrica e otimização com objetivos e restrições concorrentes. |
| **V5** | Experimental Validation & Engineering Loop | Correlação com ensaios físicos e ciclo controlado de melhoria dos modelos. |

---

## 4. V0 — Foundation / Engineering Framework

### 4.1 Objetivo

Estabelecer a estrutura necessária para que os cálculos posteriores sejam tecnicamente rastreáveis, reproduzíveis e governados.

V0 não é definida pela quantidade de equações implementadas, mas pela existência de uma linguagem técnica e de uma arquitetura comuns.

### 4.2 Capacidades planejadas

- Definir propósito, limites e arquitetura geral.
- Organizar requisitos e metas de engenharia.
- Definir coordenadas, sinais e unidades.
- Criar identificadores persistentes para requisitos, metas, parâmetros e validações.
- Registrar hipóteses, fontes, autoridade técnica e validade.
- Manter registros de decisões e mudanças.
- Criar uma matriz de dependências entre entradas, análises e saídas.
- Separar padrão técnico, modelo computacional, interface e evidência experimental.
- Definir contratos de dados para Excel–Python e outras integrações.
- Organizar documentação e repositório.

### 4.3 Artefatos conceituais

- **Engineering Standard:** referência normativa das equações, hipóteses, convenções e critérios de validade.
- **Architecture/System Design:** módulos, limites, responsabilidades e dependências.
- **Data Contract:** formatos, unidades, IDs, campos e regras de validação do intercâmbio.
- **Engineering Decision Register (EDR):** decisões, alternativas, justificativas e consequências.
- **Requirements/Targets Register:** requisitos e metas rastreáveis.
- **Validation Register:** testes, critérios de aceitação e evidências.
- **Version Register/Changelog:** histórico e impacto das mudanças.
- **Dependency Matrix:** relações entre parâmetros, análises e resultados.

### 4.4 Princípios de arquitetura

1. O Engineering Standard é a fonte normativa das formulações.
2. Excel e Python implementam o Standard, mas não o substituem.
3. Alterar uma implementação não altera automaticamente o Standard.
4. Mudanças em equações, hipóteses, convenções, validade, autoridade, requisitos ou decisões exigem revisão técnica.
5. Uma alteração no Standard deve identificar as implementações, os testes, as validações, as dependências e os documentos afetados.
6. O núcleo computacional utiliza unidades SI.
7. A interface pode exibir unidades mais convenientes, como mm, N/mm, graus e km/h.
8. Contratos de intercâmbio devem declarar unidades explicitamente.
9. Dados e resultados devem preservar origem, revisão e validade.

V0 não valida os modelos físicos por si só. Ela cria a estrutura necessária para que essa validação seja possível e rastreável.

---

## 5. V1 — Vehicle Dynamics & Suspension Sizing

### 5.1 Objetivo

Construir o núcleo físico inicial que converte parâmetros do veículo e metas de dinâmica em grandezas úteis ao dimensionamento da suspensão, sem exigir uma simulação dinâmica completa do veículo.

### 5.2 Configuração do veículo

O sistema deve representar, conforme os dados disponíveis:

- Massa total e distribuição de massa.
- Massa suspensa e massas não suspensas por eixo ou canto.
- Altura do centro de gravidade.
- Distâncias entre centro de gravidade e eixos.
- Entre-eixos e bitolas.
- Alturas relevantes das massas não suspensas e centros de rolagem fornecidos.
- Rigidez de rolagem dianteira e traseira.
- Condições de carga e configuração da análise.

### 5.3 Cargas estáticas

Capacidades previstas:

- Cargas estáticas por eixo e por canto.
- Distribuição longitudinal de peso.
- Verificações de coerência entre massa, gravidade e soma das cargas verticais.
- Separação entre carga vertical no pneu (`Fz`) e massa suspensa utilizada no cálculo da frequência natural.

`Fz` representa uma força vertical no contato pneu-solo, não uma massa.

### 5.4 Transferência longitudinal de carga

- Cálculo da transferência de carga devido à aceleração longitudinal.
- Convenção de sinais explícita para aceleração e frenagem.
- Distribuição coerente das parcelas por eixo e canto.
- Separação entre transferência rígida de corpo e efeitos de anti-dive/anti-squat.

### 5.5 Transferência lateral de carga

- Formulação baseada na estrutura de Milliken & Milliken adotada no Engineering Standard.
- Separação entre contribuições elásticas, geométricas e de massas não suspensas.
- Cálculo por eixo e aplicação coerente às cargas de cada canto.
- Uso inicial de centros de rolagem estáticos.
- Verificações de conservação e plausibilidade.

### 5.6 Cargas aerodinâmicas

- Representação de cargas aerodinâmicas por eixo ou canto.
- Integração com cargas estáticas e transferências.
- Separação explícita entre cenários com e sem aero.
- Possibilidade de futura integração com dados aerodinâmicos mais detalhados.

### 5.7 Spring rate, wheel rate e frequência natural

- Conversão entre rigidez da mola e rigidez equivalente na roda.
- Cálculo direto e inverso da frequência natural não amortecida em um modelo equivalente de um grau de liberdade.
- Uso da massa suspensa equivalente por canto.
- Dimensionamento inverso da wheel rate a partir de uma frequência-alvo.
- Conversão da wheel rate requerida em spring rate a partir do Motion Ratio correspondente à posição de trabalho.

### 5.8 Rigidez de rolagem

- Rigidez de rolagem por eixo.
- Distribuição de rigidez de rolagem entre dianteira e traseira.
- Relação entre distribuição de rigidez e distribuição da transferência lateral elástica.
- Exploração inicial de configurações de molas e barras antirrolagem quando os parâmetros forem conhecidos.

### 5.9 Anti-dive e anti-squat

- Cálculo geométrico de acordo com uma convenção documentada.
- Configuração de frenagem e tração como parâmetros explícitos.
- Preservação do sinal geométrico para distinguir anti-dive de pro-dive.
- Separação entre transferência total de carga longitudinal e partição das reações geométricas/elásticas.

### 5.10 Verificações de plausibilidade

- Equilíbrio estático e soma de cargas.
- Coerência de sinais em aceleração, frenagem e curvas.
- Aviso para `Fz` negativo, indicando possível perda de contato.
- Preservação do resultado calculado, sem truncamento silencioso para zero.
- Verificação de entradas inválidas e testes de regressão.

### 5.11 Limites planejados

- A superposição linear é a hipótese inicial para combinar carregamentos.
- A resposta do pneu é não linear e pertence a um domínio de modelagem separado.
- Anti-dive e anti-squat não reduzem a transferência rígida total longitudinal.
- O centro de rolagem é inicialmente tratado como estático.
- V1 não pretende representar toda a dinâmica transitória do veículo.
- Consistência matemática não substitui dados reais nem validação independente.

### 5.12 Sequência de dimensionamento

1. Definir requisitos, metas e condições de referência.
2. Determinar os parâmetros do veículo.
3. Calcular cargas e massas equivalentes.
4. Estabelecer metas de frequência natural e comportamento de rolagem.
5. Calcular wheel rates requeridas.
6. Derivar spring rates a partir do MR.
7. Verificar restrições e plausibilidade.
8. Propagar metas e resultados para os domínios de cinemática e pneus.

### 5.13 Papel de Excel e Python

O Excel é a interface de configuração, uso, comparação, registro e apresentação dos resultados. Python executa os cálculos definidos pelo Standard.

---

## 6. V2 — Kinematics Integration

### 6.1 Objetivo

Integrar geometria 3D e cinemática para que os parâmetros sejam calculados a partir de hardpoints e posições operacionais, em vez de serem tratados apenas como constantes fornecidas.

A referência especializada planejada é o **OptimumKinematics**. O **Lotus Suspension Analysis** pode servir como cross-check independente, mediante adaptação explícita das convenções.

### 6.2 Geometria e hardpoints

- Representação de hardpoints 3D da suspensão.
- Contrato de dados versionado com unidades e sistema de coordenadas declarados.
- Validação de completude e plausibilidade.
- Intercâmbio por arquivo estruturado, planejado como `hardpoints.csv`, em vez de redigitação manual.
- Identificação de pontos e componentes.
- Versionamento independente da geometria.
- Adaptadores documentados para coordenadas e sinais de ferramentas externas.

### 6.3 Capacidades cinemáticas previstas

Para uma arquitetura double wishbone com pushrod/pullrod e rocker, conforme a geometria real:

- Deslocamento de roda em bump/rebound.
- Cambagem em função do curso.
- Toe em função do curso.
- Caster e KPI.
- Scrub radius e trail.
- Variação de bitola.
- Motion Ratio e sua variação ao longo do curso.
- Relação entre esterçamento e resposta cinemática, conforme os dados disponíveis.
- Centros instantâneos e centro de rolagem cinemático.
- Construções geométricas para anti-dive e anti-squat.
- Comparação entre posições operacionais.

A validade de cada saída depende da geometria e da definição operacional. O sistema não deve inventar resultados que os dados não suportam.

### 6.4 KOP e VS

- **KOP — Kinematic Operating Point:** posição operacional da suspensão, como ride height, bump/rebound ou ponto de roll/steer.
- **VS — Vehicle State:** estado do veículo, incluindo acelerações, velocidade, esterçamento, aero e setup.

V2 relaciona a cinemática a KOPs. O acoplamento iterativo completo entre VS e KOP não pertence ao núcleo inicial de V1 e pode ser incorporado em uma evolução posterior.

### 6.5 Motion Ratio

Convenção estabelecida:

\[
MR=\frac{\Delta x_{\mathrm{wheel}}}{\Delta x_{\mathrm{spring}}}
\]

Ou seja, `wheel/spring`.

- O valor inicial de referência é `MR_RH`, no ride height.
- A arquitetura deve permitir `MR(z)`.
- O MR depende da geometria e da posição de trabalho.
- A spring rate é derivada da wheel rate desejada e do MR correspondente.
- Evitar o termo ambíguo `MR_effective` sem definição matemática e operacional.

### 6.6 Centros de rolagem

- Referência planejada: `RC_official = RC_OptimumKinematics`.
- O modelo interno simplificado serve como sanity check geométrico, não como substituto da ferramenta.
- O uso inicial é `RC_static = RC(z_RH)`.
- A migração dinâmica iterativa completa fica fora do modelo inicial.

### 6.7 Cuidados e limites

- Geometria sintética testa o solver, mas não caracteriza o carro.
- A qualidade metrológica dos hardpoints limita a validade.
- Pequenas bases geométricas podem amplificar ruído em cambagem e toe.
- O centro de rolagem pode ser sensível a pequenas variações geométricas.
- Definições de centro instantâneo em 3D e convenções de curso devem ser alinhadas com a referência.
- O modelo de contato com o solo e a geometria real do pneu limitam algumas saídas.

---

## 7. V3 — Tire + CarSim + Vehicle Performance

### 7.1 Objetivo

Adicionar um modelo explícito de pneu e evoluir para a análise de desempenho do veículo completo.

O **OptimumTire** é a referência planejada para o domínio de pneus. O **CarSim** é a camada planejada de simulação do veículo completo.

### 7.2 Modelo de pneu

- Importar datasets e seus metadados.
- Ler unidades, faixas de validade e revisão.
- Representar forças longitudinais e laterais conforme as variáveis suportadas.
- Considerar carga vertical, ângulo de deriva, cambagem e slip ratio quando aplicável.
- Avaliar forças puras e combinadas.
- Calcular coeficientes efetivos quando a definição for explícita.
- Bloquear extrapolação silenciosa fora das faixas de validade.
- Rejeitar dados incompatíveis com o formato ou modelo declarado.
- Distinguir dados medidos, ajustados, fornecidos e demonstrativos.
- Preservar origem e revisão dos dados.
- Comparar a implementação interna com a ferramenta de referência em pontos e varreduras selecionados.

### 7.3 Formulação e autoridade

Uma formulação Pacejka/Magic Formula pode ser utilizada, mas a família e a versão precisam ser declaradas, por exemplo PAC2002/MF 5.2, MF 6.1.2 ou MF 6.2.

Essas famílias não devem ser presumidas equivalentes: equações, parâmetros e variáveis suportadas podem diferir.

### 7.4 Limites que devem ser declarados

- Momentos de pneu (`Mx`, `My`, `Mz`) quando não implementados.
- Efeitos de pressão quando não suportados.
- Relaxação e transientes.
- Extrapolação fora das faixas de carga, deriva, cambagem ou slip.
- Hipóteses de espelhamento entre pneus esquerdo e direito.
- Convenções de sinal não declaradas no dataset.

### 7.5 Integração física

Fluxo conceitual:

1. Estado do veículo e condição de operação.
2. Transferência de carga e `Fz` por canto.
3. Estado cinemático da suspensão no KOP.
4. Estado do pneu.
5. Forças e respostas do pneu.
6. Resposta do veículo e métricas de desempenho.

O modelo de pneu recebe as cargas verticais; não é a autoridade para calcular a transferência rígida de carga do veículo.

### 7.6 CarSim

CarSim está previsto para:

- Avaliar o veículo em condições operacionais mais completas.
- Estudar os efeitos combinados de suspensão, pneus, configuração e estado.
- Analisar eventos e comportamento dinâmico.
- Comparar tendências com os modelos internos.
- Preparar a correlação com dados experimentais.

CarSim não substitui automaticamente todos os modelos internos nem as ferramentas especializadas de domínio.

---

## 8. V4 — Optimization / Multidisciplinary Design

### 8.1 Objetivo

Transformar o sistema em um ambiente estruturado de exploração de projeto, comparação de alternativas e otimização.

### 8.2 Variáveis potenciais

- Spring rate e wheel rate.
- Distribuição de rigidez de rolagem.
- Geometria do rocker e pontos que alterem MR.
- Hardpoints e parâmetros cinemáticos.
- Configuração de barras antirrolagem.
- Características e seleção de pneus.
- Parâmetros de setup.
- Parâmetros estruturais, quando os modelos suportarem.

Nem todas as variáveis precisam ser otimizadas simultaneamente. Cada variável deve ser habilitada apenas quando o modelo que a avalia for adequado ao uso pretendido.

### 8.3 Objetivos e restrições possíveis

- Desempenho dinâmico.
- Consistência de comportamento.
- Massa.
- Rigidez e integridade estrutural.
- Curso e envelope operacional.
- Sensibilidade a fabricação e setup.
- Embalagem, montagem e manutenção.
- Custo, fabricação e regulamento.

Objetivos, pesos e limites devem vir de requisitos ou decisões explícitas, não de valores padrão inventados pelo software.

### 8.4 Otimização estrutural e FEA

A visão de longo prazo inclui otimização paramétrica e possível integração com análise por elementos finitos (FEA), conectando geometria, cargas, rigidez, tensões, fadiga, massa e fabricação.

FEA é referência estrutural para os problemas que modela, mas não substitui validação física nem avaliação do desempenho do veículo.

### 8.5 Estratégia de otimização

- Começar com varreduras e estudos de sensibilidade interpretáveis.
- Comparar alternativas sob condições idênticas.
- Preservar a origem, os inputs e a revisão de cada candidato.
- Separar restrições duras de preferências.
- Reavaliar candidatos com ferramentas de referência.
- Não declarar um ótimo confiável fora do domínio validado.
- Considerar robustez e sensibilidade, não apenas o melhor resultado nominal.

A arquitetura não fixa um algoritmo de otimização específico. A escolha depende da dimensionalidade, do custo computacional, do comportamento do modelo e dos dados disponíveis.

---

## 9. V5 — Experimental Validation & Engineering Loop

### 9.1 Objetivo

Fechar o ciclo entre previsão, medição física, correlação, atualização controlada e conhecimento de engenharia.

A validação experimental não é um apêndice: é a etapa que avalia se o modelo representa adequadamente o sistema real dentro de um domínio declarado.

### 9.2 Ciclo planejado

1. Definir a grandeza a validar e sua finalidade.
2. Definir a referência experimental e a instrumentação.
3. Calibrar sensores e registrar incertezas.
4. Criar um procedimento repetível.
5. Registrar configuração do carro, condições e dados brutos.
6. Processar dados com scripts rastreáveis.
7. Comparar medição, previsão e referência independente.
8. Quantificar erro, dispersão e limitações.
9. Decidir aceitação, restrição de uso, recalibração ou inadequação.
10. Registrar mudanças e repetir os testes afetados.

### 9.3 Grandezas de interesse

- MR e sua variação ao longo do curso.
- Wheel rate e frequência natural.
- Rigidez de rolagem e distribuição entre eixos.
- Cambagem, toe e centros de rolagem.
- Cargas verticais e transferência de carga, conforme a instrumentação.
- Forças de pneu, quando mensuráveis.
- Deformação e tensão em componentes, com strain gauges.
- Rigidez estrutural e compliance, se incluídas no escopo.
- Resposta dinâmica do veículo e correlação com CarSim.
- Dados de setup e sensores para contextualizar os ensaios.

### 9.4 Instrumentação potencial

- Potenciômetros de suspensão.
- Sensores de ângulo de direção.
- Sensores de pressão de freio dianteira/traseira.
- RPM.
- Temperatura e pressão dos pneus.
- APPS/BPS para reconstrução do estado operacional.
- Extensômetros para validação estrutural.
- Sensores de posição de roda, inclusive soluções ópticas/laser quando apropriadas.

A seleção final depende de requisitos de precisão, taxa de amostragem, calibração, montagem, sincronização, segurança e incerteza.

### 9.5 Ciclo de aprendizado

Os resultados experimentais podem levar a:

- Aceitar um modelo em determinado domínio.
- Restringir explicitamente seu uso.
- Atualizar parâmetros identificados por ensaio.
- Revisar hipóteses ou formulações.
- Criar novos testes de regressão.
- Alterar a seleção de ferramentas de referência.
- Rever metas de projeto ou decisões de arquitetura.

Uma alteração de modelo não deve apagar a versão anterior nem ocultar a razão da mudança.

---

# PARTE II — FASES DE ENGENHARIA

## 10. Modelo de fases proposto

As fases abaixo organizam o processo de trabalho a partir dos princípios discutidos. Não substituem V0–V5 e não devem ser interpretadas como uma nomenclatura formal já aprovada.

Cada versão pode atravessar várias fases; uma fase também pode se repetir quando um novo domínio ou revisão for introduzido.

## 11. Fase A — Definição do problema e do envelope

**Objetivo:** definir o que o sistema deve responder, para qual veículo e em quais condições.

**Atividades:**
- Identificar requisitos do veículo e do regulamento.
- Definir metas de dinâmica e critérios de desempenho.
- Definir condições de referência.
- Estabelecer restrições físicas, de embalagem, fabricação, custo e segurança.
- Identificar variáveis de projeto e variáveis de estado.
- Distinguir dados reais, referências, metas, hipóteses e valores demonstrativos.

**Saídas:** requisitos rastreáveis, metas, envelope de operação, premissas e lacunas de dados.

## 12. Fase B — Padronização e arquitetura

**Objetivo:** estabelecer uma linguagem técnica comum.

**Atividades:** coordenadas, sinais, unidades, IDs, estados, contratos de dados, rastreabilidade, autoridades técnicas, dependências e governança de mudanças.

**Saídas:** Engineering Standard, Architecture/System Design, Data Contract, Dependency Matrix, Decision Register e estrutura de versões.

## 13. Fase C — Formulação física

**Objetivo:** definir equações, hipóteses e limites antes de tratar a implementação como referência.

**Atividades:** formular cargas, dinâmica veicular, rigidez, frequência, MR, anti-dive/anti-squat, cinemática, pneu e critérios de validade.

**Saídas:** formulações documentadas, referências, hipóteses, limitações e casos analíticos.

## 14. Fase D — Implementação computacional e interface

**Objetivo:** converter formulações aprovadas em módulos computacionais e interface.

**Atividades:** implementar Python, construir interface Excel, criar importação/exportação, validar entradas, implementar erros/avisos, separar dados sintéticos e reais e expor rastreabilidade.

**Saídas:** módulos, workbook, interfaces, testes de software e documentação de uso.

## 15. Fase E — Verificação matemática e computacional

**Objetivo:** demonstrar que a implementação resolve a formulação especificada nos casos avaliados.

**Atividades:**
- Testes unitários.
- Testes de propriedades físicas e casos-limite.
- Verificações de conservação.
- Testes de sinais e simetria.
- Testes de inversão direta/inversa.
- Testes de regressão.
- Comparação independente quando disponível.
- Verificação do contrato de dados.

**Saídas:** evidência de testes, defeitos e correções, cobertura de casos críticos e limitações não cobertas.

**Limite:** passar nos testes demonstra consistência computacional nos casos cobertos. Não prova, por si só, que a formulação representa o carro real.

## 16. Fase F — Comparação com ferramenta de referência

**Objetivo:** comparar o modelo com uma ferramenta especializada independente no domínio correspondente.

**Atividades:** selecionar pontos representativos, alinhar inputs/unidades/convenções, comparar cinemática com OptimumKinematics/Lotus, pneus com OptimumTire e veículo completo com CarSim quando aplicável, investigar divergências.

**Saídas:** matriz de comparação, erros, diferenças de formulação, domínio de uso e evidência independente.

A referência deve ser usada em gates de validação, mudanças estruturais, resultados fora do envelope, candidatos selecionados e verificações estratégicas — não necessariamente em toda iteração interna.

## 17. Fase G — Integração entre domínios

**Objetivo:** conectar modelos que antes eram analisados separadamente sem esconder dependências.

**Atividades:** integrar geometria, cinemática, cargas, pneus e estado do veículo; definir KOP/VS; estabelecer interfaces; propagar revisões; marcar resultados derivados obsoletos; explicitar acoplamentos iterativos.

**Saídas:** fluxo de dados integrado, contratos entre módulos, matriz de dependências, testes de integração e simplificações declaradas.

## 18. Fase H — Exploração paramétrica e otimização

**Objetivo:** comparar alternativas com critérios de engenharia explícitos.

**Atividades:** varreduras paramétricas, sensibilidades, trade-offs, definição de objetivos/restrições, seleção de candidatos, FEA quando necessária e preservação da origem de cada candidato.

**Saídas:** comparações reproduzíveis, candidatos priorizados, justificativa técnica e limitações.

## 19. Fase I — Validação experimental

**Objetivo:** avaliar a correspondência entre previsões e comportamento físico.

**Atividades:** definir procedimento, selecionar e calibrar sensores, registrar condições e dados brutos, estimar incertezas, processar dados, comparar modelo e experimento e diagnosticar discrepâncias.

**Saídas:** relatório de ensaio, dados brutos/processados, estimativa de incerteza, métricas de correlação e decisão de aceitação, restrição ou revisão.

## 20. Fase J — Congelamento, liberação e manutenção

**Objetivo:** garantir que uma configuração possa ser utilizada de forma controlada e que mudanças preservem a rastreabilidade.

**Atividades:** consolidar revisões, registrar limites, revisar testes afetados, identificar resultados obsoletos, congelar configurações e preservar versões anteriores.

**Saídas:** pacote identificável por revisão, changelog, dependências, evidência de validação aplicável e documentação de uso.

---

# PARTE III — ARQUITETURA FUNCIONAL E DE DADOS

## 21. Camadas lógicas

1. **Requisitos, metas e decisões:** objetivos e restrições.
2. **Engineering Standard:** formulações, hipóteses, convenções e validade.
3. **Dados e referências:** parâmetros do veículo, hardpoints, datasets de pneus, componentes e exports de ferramentas.
4. **Modelos internos:** cálculos em Python.
5. **Ferramentas especializadas:** referências e simuladores externos.
6. **Interface de engenharia:** Excel para configuração, entradas, resultados, comparação e dashboard.
7. **Verificação e validação:** testes matemáticos, comparação independente e correlação experimental.
8. **Decisão e otimização:** comparação de configurações dentro dos domínios válidos.

## 22. Domínios e responsabilidades

| Domínio | Responsabilidade principal | Referência/ferramenta planejada |
|---|---|---|
| Requisitos e metas | Objetivos e restrições | Registros de engenharia |
| Dinâmica veicular básica | Cargas e transferências | Engineering Standard + Python |
| Dimensionamento | Wheel rate, spring rate, frequência e rolagem | Python + Excel |
| Geometria e cinemática | Resposta a partir de hardpoints | OptimumKinematics; Lotus cross-check |
| Pneus | Forças e respostas | OptimumTire + modelo interno |
| Veículo completo | Resposta combinada | CarSim |
| Estruturas | Tensões, rigidez e fadiga no modelo estrutural | FEA, por exemplo ANSYS |
| Interface e rastreabilidade | Entradas, resultados, comparação e histórico | Excel |
| Automação e modelos | Cálculos e testes | Python |
| Validação física | Comparação com o carro | Instrumentação e ensaios |

A autoridade é específica por domínio. Nenhuma ferramenta é automaticamente autoridade para o sistema inteiro.

## 23. Modelo, referência, autoridade e validação

- **Modelo:** ferramenta de previsão e exploração que implementa uma formulação.
- **Referência:** ferramenta ou fonte especializada usada para caracterizar ou verificar um domínio.
- **Experimento:** evidência física obtida por medição.
- **Autoridade técnica:** referência aceita para um domínio ou decisão.
- **Verificação:** demonstra que a implementação está de acordo com a formulação ou referência nos casos avaliados.
- **Validação:** avalia se o modelo é adequado para representar o sistema físico e para a finalidade pretendida.

A concordância Excel–Python pode detectar divergência de implementação, mas não necessariamente um erro de formulação compartilhado. A concordância com uma ferramenta de referência também não elimina a necessidade de validação física.

## 24. Fluxo de dados

Fluxo conceitual:

1. Requisitos e metas.
2. Configuração do veículo e condições de referência.
3. Geometria e hardpoints.
4. Cinemática no KOP.
5. Cargas e estado do veículo.
6. Estado e forças do pneu.
7. Simulação do veículo completo.
8. Exploração e otimização.
9. Experimento e correlação.
10. Governança das revisões e evidências.

O fluxo não precisa ser inteiramente linear. Acoplamentos que exigem iteração devem ser declarados explicitamente.

## 25. Revisões e dependências

Convenções de revisão discutidas:

- Geometria: `G-REV-X`
- Cinemática: `K-REV-X`
- Pneus: `T-REV-X`
- Dinâmica: `D-REV-X`
- Setup: `S-XXX`

O formato final deve ser consistente e inequívoco.

Quando uma revisão upstream muda, resultados que dependem dela podem ficar obsoletos. O sistema deve identificar essa condição, em vez de apresentar o resultado antigo como se fosse atual.

`STALE` significa que uma dependência mudou e o resultado precisa ser reavaliado; não significa, por si só, que o resultado anterior estava errado.

### 25.1 Contrato de hardpoints

Deve declarar:

- Sistema de coordenadas.
- Unidades.
- Identificadores dos pontos e componentes.
- Campos obrigatórios.
- Revisão de origem.
- Regras de completude e plausibilidade.

Convenções incompatíveis devem ser rejeitadas quando não houver conversão explícita e documentada.

### 25.2 Integração Excel–Python

A integração inicial é planejada por arquivos estruturados, como JSON/CSV. O Excel mantém a interface e o registro de engenharia; Python executa os modelos.

Macros, xlwings e PyXLL não são pressupostos da arquitetura inicial.

---

# PARTE IV — CONVENÇÕES TÉCNICAS TRANSVERSAIS

## 26. Coordenadas e sinais

A convenção mestre planejada é um sistema cartesiano destrógiro:

- `X`: para a frente do veículo.
- `Y`: para a esquerda do veículo.
- `Z`: para cima.

Convenções associadas:

- Roll positivo: lado esquerdo sobe e lado direito desce.
- Pitch positivo: nariz para baixo e traseira para cima, conforme a convenção definida no projeto.
- Yaw positivo: nariz gira para a esquerda, visto de cima.
- Momentos seguem a regra da mão direita.
- Cambagem positiva: topo da roda para fora; negativa: topo para dentro.
- Toe positivo no Tupã: toe-out; toe negativo: toe-in.

Ferramentas com convenções diferentes devem usar adaptadores documentados.

Uma norma ISO específica só deve ser declarada formalmente adotada quando houver referência direta e verificada no Engineering Standard.

## 27. Motion Ratio e wheel rate

Convenção estabelecida:

\[
MR = \frac{\Delta x_{\mathrm{wheel}}}{\Delta x_{\mathrm{spring}}}
\]

Portanto:

\[
K_w = \frac{K_s}{MR^2}
\qquad\text{e}\qquad
K_s = K_w MR^2
\]

- Nome de código explícito, como `motion_ratio_wheel_spring`.
- Rótulo Excel: `MR [wheel/spring]`.
- Evitar `MR` sem convenção quando houver risco de ambiguidade.
- MR inicialmente no ride height, com arquitetura preparada para `MR(z)`.
- MR depende da geometria e da posição de trabalho; não é propriedade isolada da mola.

## 28. Cargas e transferência

`Fz` é força vertical no contato pneu-solo, não massa.

A carga por canto combina carga estática, transferência longitudinal, transferência lateral e contribuição aerodinâmica. Parcelas por eixo e por canto precisam ser distinguidas matematicamente.

Cargas negativas calculadas devem gerar aviso de plausibilidade/perda de contato, sem truncamento silencioso.

Anti-dive e anti-squat descrevem contribuições geométricas na distribuição das reações e na atitude de pitch, mas não reduzem a transferência rígida total de carga longitudinal.

A sequência conceitual é:

**Estado de aceleração → transferência global de carga → forças de pneu → caminhos de carga da suspensão → contribuição geométrica/elástica → atitude e cargas nos componentes.**

## 29. Tipos, estados e identificadores

### Tipos de dados

- `INPUT`
- `TARGET`
- `REQUIREMENT`
- `REFERENCE`
- `MODEL`
- `CALCULATED`

`AUTHORITY` é metadado, não tipo de dado. `CROSS_CHECK` é propósito/flag, não um tipo separado `MODEL/CHECK`.

### Estados de ciclo de vida

- `OPEN`
- `DRAFT`
- `CHECKED`
- `FROZEN`
- `STALE`

### Estados de validação

- `NOT_VALIDATED`
- `PASS`
- `WARNING`
- `FAIL`

`FROZEN + STALE` é válido: uma configuração congelada pode ficar obsoleta quando uma dependência upstream muda.

### Famílias de IDs discutidas

- `REQ-XXX`: requisitos.
- `TARGET-XXX`: metas.
- `SUS-0XX` a `SUS-8XX`: parâmetros e modelos do domínio de suspensão.
- `VAL-XXX`: validações.

Relação de rastreabilidade:

**`REQ → TARGET` (quando aplicável) `→ SUS → Engineering Standard → VAL`**

A Dependency Matrix deve cobrir:

- **Analysis:** entradas que produzem cada saída.
- **Design:** quais entradas precisam ser definidas para alcançar uma meta.

O modo Design é bidirecional: calcular a partir de entradas e ajudar a determinar as entradas necessárias para metas estabelecidas.

---

# PARTE V — EXCEL, PYTHON E GOVERNANÇA

## 30. Papel e organização do Excel

Excel é o **System of Record de uso e interface de engenharia**: reúne configuração, entradas, metas, decisões, resultados, comparações, validação, dashboard e histórico.

| Aba | Função conceitual |
|---|---|
| `00_README` | Instruções, escopo e avisos |
| `01_SETUP` | Configuração geral e metadados |
| `02_REQUIREMENTS` | Requisitos |
| `03_TARGETS` | Metas |
| `04_DECISION_REGISTER` | Registro de decisões |
| `05_VEHICLE` | Parâmetros do veículo |
| `06_SUSPENSION` | Dimensionamento da suspensão |
| `07_KINEMATICS` | Geometria e resultados cinemáticos |
| `08_VEHICLE_STATE` | Estado e condições do veículo |
| `09_LOADS` | Cargas e transferências |
| `10_TIRE` | Dados e resultados de pneus |
| `11_DESIGN` | Estudos e entradas de projeto |
| `12_COMPARISON` | Comparação de alternativas e referências |
| `13_VALIDATION` | Testes e evidências |
| `14_DASHBOARD` | Síntese visual |
| `15_CHANGELOG` | Histórico de mudanças |

A função de cada aba deve permanecer estável, ainda que o layout evolua.

## 31. Papel do Python

Python implementa modelos internos, automação, verificações e testes.

Os módulos devem ser separados por domínio, ter interfaces explícitas, poder ser testados sem depender da planilha e produzir resultados e avisos rastreáveis.

## 32. Organização de repositório proposta

```text
Suspension-System/
├── docs/
│   ├── Engineering_Standard
│   ├── Architecture
│   ├── Data_Contract
│   ├── Validation
│   ├── Decision_Register
│   └── Version_Register
├── python/
│   ├── vehicle_dynamics/
│   ├── suspension/
│   ├── kinematics/
│   ├── tire/
│   ├── integration/
│   └── tests/
├── data/
│   ├── vehicle/
│   ├── hardpoints/
│   ├── tires/
│   └── interchange/
├── references/
│   ├── tool_exports/
│   └── source_documents/
├── excel/
└── tests/
    ├── analytical/
    ├── regression/
    ├── cross_reference/
    └── integration/
```

Essa estrutura é uma proposta para separar código, dados, documentos, referências e testes. A organização física pode mudar sem alterar os princípios de arquitetura.

## 33. Governança de mudanças

Toda mudança relevante deve registrar:

1. O que mudou e por quê.
2. Qual decisão ou evidência fundamentou a mudança.
3. Quais equações, hipóteses ou convenções foram afetadas.
4. Quais módulos e interfaces foram afetados.
5. Quais testes precisam ser atualizados.
6. Quais resultados e validações ficaram obsoletos.
7. Qual novo domínio de validade ou limitação se aplica.
8. Quais revisões de dados e modelos devem acompanhar o resultado.

O changelog deve incluir, no mínimo, data, revisão, mudança, motivo, impacto e validação.

---

# PARTE VI — COBERTURA E LIMITES

## 34. Mapa de capacidades por versão

| Capacidade | V0 | V1 | V2 | V3 | V4 | V5 |
|---|---|---|---|---|---|---|
| Governança e rastreabilidade | Define | Mantém | Mantém | Mantém | Mantém | Mantém |
| Contratos e convenções | Define | Usa | Estende à geometria | Estende a pneus/simulação | Estende à otimização | Estende a ensaios |
| Cargas e transferências | — | Núcleo | Relaciona à geometria | Acopla ao pneu | Exploração | Correlação |
| Spring/wheel rate e frequência | — | Núcleo | Usa MR cinemático | Integra ao desempenho | Variáveis | Validação física |
| Cinemática 3D | — | Simplificada | Núcleo | Estado de suspensão | Otimização | Correlação |
| Modelo de pneu | — | Fora do núcleo | Interface preparada | Núcleo | Otimização | Correlação |
| Veículo completo | — | Fora do núcleo | Acoplamento preparado | CarSim | Candidatos | Correlação |
| Otimização | — | Estudos básicos | Exploração cinemática | Exploração integrada | Núcleo | Informada por dados |
| Referência independente | Estratégia | Física básica | Kinematics | Tire/CarSim | Candidatos | Mantém |
| Validação experimental | Estrutura | Preparação | Preparação cinemática | Preparação dinâmica | Seleção de ensaios | Núcleo |

A matriz descreve a intenção arquitetural, não o status de implementação.

## 35. Decisões que formam a base arquitetural

1. O sistema reúne padrão técnico, modelos, referências, interface e validação.
2. O Engineering Standard é a fonte normativa.
3. Excel é interface/registro; Python executa os modelos.
4. A integração inicial Excel–Python usa JSON/CSV, sem dependência de macros, xlwings ou PyXLL.
5. Ferramentas especializadas não são substituídas por clones sem justificativa.
6. OptimumKinematics é a referência planejada de cinemática; Lotus pode ser cross-check.
7. OptimumTire é a referência planejada de pneus.
8. CarSim é a camada de veículo completo.
9. FEA é referência estrutural para os problemas que efetivamente modela.
10. MR segue a convenção wheel/spring.
11. KOP e VS são conceitos distintos.
12. Cargas/transferência e resposta do pneu são conectadas, mas não intercambiáveis.
13. Anti-dive/anti-squat não reduzem a transferência rígida longitudinal total.
14. Resultados derivados são rastreados por revisão e podem ficar `STALE`.
15. Verificação matemática, comparação com referência e validação experimental são evidências diferentes.
16. Dados sintéticos não devem parecer dados reais ou metas aprovadas.

## 36. Pontos que permanecem a definir

Não declarar como resolvidos sem decisão documentada:

- Nomenclatura formal e critérios de encerramento das fases próprias do sistema.
- Critérios quantitativos de aceitação para cada módulo e grandeza.
- Funções-objetivo, pesos e algoritmos de otimização.
- Escopo exato da integração CarSim e variáveis trocadas.
- Versões e formulações de pneu suportadas e formato final de referência.
- Convenções de sinal e espelhamento de pneu quando não declaradas no dataset.
- Definições de grandezas cinemáticas 3D dependentes da ferramenta de referência.
- Instrumentação final e orçamento de incerteza para cada ensaio.
- Nível de acoplamento iterativo entre estado dinâmico, cinemática, pneu e veículo.
- Variáveis estruturais e extensão da integração com FEA.
- Adoção formal de normas externas: exige fonte direta e registro explícito.

## 37. Critério de maturidade técnica

Uma capacidade é tecnicamente madura quando seu escopo está explícito e existe evidência compatível com a finalidade:

1. Formulação documentada.
2. Implementação rastreável.
3. Testes computacionais adequados.
4. Comparação independente quando houver referência apropriada.
5. Domínio de validade declarado.
6. Validação experimental quando a finalidade exigir representação do veículo físico.
7. Revisões e dependências registradas.

Nem todo cálculo exige o mesmo nível de evidência, mas o nível deve ser explícito.

---

# 38. Síntese final

A arquitetura pretendida evolui por seis grandes capacidades:

- **V0 — Foundation:** linguagem técnica, governança, contratos e rastreabilidade.
- **V1 — Sizing:** cálculos fundamentais de dinâmica veicular e dimensionamento.
- **V2 — Kinematics:** geometria 3D e cinemática baseada em hardpoints e posição.
- **V3 — Tire & Vehicle Performance:** resposta do pneu e simulação do veículo completo.
- **V4 — Optimization:** exploração e otimização com objetivos e restrições explícitos.
- **V5 — Experimental Loop:** correlação com medições e melhoria controlada dos modelos.

As fases organizam o processo para transformar cada capacidade em algo confiável: definir o problema, padronizar, formular, implementar, verificar, comparar com referências, integrar, otimizar, validar fisicamente e manter sob controle de versões.

**Princípio integrador:** requisitos e metas orientam modelos; modelos geram previsões; referências verificam domínios específicos; experimentos avaliam a correspondência com o veículo real; a governança preserva decisões, limitações e evidências.

O resultado pretendido não é somente escolher componentes, mas construir um sistema de engenharia reproduzível, explicável, extensível e capaz de acumular conhecimento entre gerações do veículo.
