# Engineering Decision Register — Sistema_DDS (Tupã Suspension System)

**Versão do registro:** V2.4-PARCIAL (2026-10-14). **Estado do documento:** em construção; mantido a cada decisão relevante.
**Escopo:** registra as decisões de engenharia tomadas (ou pendentes) nas conversas do projeto, com rastreabilidade para artefatos, parâmetros e testes. **Não substitui** o Engineering Standard, o registro de versões, as fichas de validação nem a documentação técnica: conecta-os.

## 1. Convenções e governança

**Namespace.** `EDR-xxx` (Engineering Decision Record). Não reutiliza `DR-xxx` (aba `04_DECISION_REGISTER` da planilha, resumo) nem `DEC-xxx` (citados na arquitetura, cujos registros individuais não estão disponíveis). Em caso de divergência entre este arquivo e `04_DECISION_REGISTER`, vale este arquivo. IDs são estáveis: uma decisão substituída recebe o estado SUPERSEDED e aponta a sucessora; o ID não é reutilizado.

**Campo `Status` do registro (`Record_Status`).** É uma terceira coisa, **distinta** do Lifecycle Status (OPEN/DRAFT/CHECKED/FROZEN/STALE) e do Validation Status (NOT_VALIDATED/PASS/WARNING/FAIL) de parâmetros (arquitetura §3). Nenhum nome desses é reutilizado aqui.

| Estado | Significado |
|---|---|
| PROPOSED | Proposta em elaboração; ainda não apresentada para decisão. |
| AWAITING_DECISION | Apresentada ao usuário com alternativas; decisão não tomada. |
| PENDING_CONFIRMATION | A decisão efetiva não pode ser determinada pela evidência disponível (ex.: instrução ambígua ou aprovação implícita). **Não preencher a lacuna por inferência.** |
| APPROVED_WITH_CONDITIONS | Aprovada pelo usuário com condições registradas em `Approval_Conditions`. |
| APPROVED | Aprovada sem condições pendentes. |
| IMPLEMENTED | Implementada nos artefatos (pode não estar verificada). |
| VERIFIED | Implementação verificada por testes/inspeção. **Não implica validação física.** |
| SUPERSEDED | Substituída por outra decisão (campo `Related_Decisions`). |
| REOPENED | Reaberta por nova evidência ou mudança upstream. |

**Transições e critérios.** PROPOSED → AWAITING_DECISION (decisão apresentada com alternativas e evidências) → APPROVED ou APPROVED_WITH_CONDITIONS (decisão explícita do usuário; recomendação do assistente **não** conta) → IMPLEMENTED (artefatos alterados e registrados) → VERIFIED (testes pertinentes executados e resultados registrados). Qualquer estado → REOPENED quando: nova evidência contradiz as premissas; uma dependência upstream muda de revisão (decisão dependente vira candidata a STALE no artefato); uma condição de aprovação deixa de valer. APPROVED/IMPLEMENTED → SUPERSEDED quando outra decisão a substitui explicitamente. Uma decisão pode estar APPROVED e não implementada; uma implementação pode estar VERIFIED sem validação física.

**Regra de atualização.** A partir da V2.1, toda decisão relevante é registrada antes ou durante sua implementação, e este arquivo é atualizado quando: uma decisão for tomada ou alterada; uma condição de aprovação for satisfeita; uma implementação for concluída; uma validação produzir evidência; uma dependência mudar; uma decisão for substituída ou reaberta.

**Limites de proveniência.** Datas e autoria exatas de turnos anteriores não estão disponíveis; onde faltam, consta "Não registrada". Decisões herdadas da arquitetura citam o documento, pois os registros DEC individuais não foram fornecidos. "Usuário (instrução na conversa)" indica instrução textual do usuário na conversa Sistema_DDS.

**Referência cruzada.** Registro de versões: `registro-de-versoes-V2.1.md`. Auditoria: `audit-report-V2.1.md`. Mapa de dependências da planilha: `placeholder-dependency-map-V2.1.csv`. Geometry Brief: `geometry-brief-V2.1.md`. Critérios de promoção: `kinematics-exploratory-and-promotion-V2.1.md`.

## 2. Índice

Total: 42 registros. APPROVED: 19 · APPROVED_WITH_CONDITIONS: 5 · AWAITING_DECISION: 9 · IMPLEMENTED: 4 · PENDING_CONFIRMATION: 2 · VERIFIED: 3

| ID | Título | Status |
|---|---|---|
| EDR-001 | Sistema de coordenadas ISO 8855 (X frente, Y esquerda, Z cima) | APPROVED |
| EDR-002 | Convenções de camber e toe (camber + = topo para fora; toe + = toe-out) | APPROVED |
| EDR-003 | Motion Ratio definido como wheel/spring | APPROVED |
| EDR-004 | Hierarquia de autoridade das ferramentas | APPROVED |
| EDR-005 | Namespaces e faixas de ID (SUS-0XX a 8XX; REQ/TARGET/VAL separados) | APPROVED |
| EDR-006 | Taxonomia de Data Type (INPUT, TARGET, REFERENCE, MODEL, CALCULATED, REQUIREMENT) | APPROVED |
| EDR-007 | Ciclo de vida e validação como duas dimensões independentes | APPROVED |
| EDR-008 | Relação Excel–Python–CAD e intercâmbio de dados | APPROVED |
| EDR-009 | RC estático no ride height de referência (V1); RC(z) permanece na REFERENCE | APPROVED |
| EDR-010 | Anti-dive/anti-squat não alteram a magnitude da transferência de carga longitudinal | APPROVED |
| EDR-011 | Transferência lateral pelo modelo de duas molas de Milliken | APPROVED |
| EDR-012 | Separar referência histórica (T09) do baseline do carro atual (TX/E05) | APPROVED |
| EDR-013 | Aero fixo por Setup (sem mapa aerodinâmico) | APPROVED |
| EDR-014 | Design Mode explícito, sem goal seek opaco | APPROVED |
| EDR-015 | Pneu como REFERENCE, sem ajuste próprio na V1 | APPROVED |
| EDR-016 | Numeração canônica de Test Cases | IMPLEMENTED |
| EDR-017 | Regra de versionamento dos artefatos | APPROVED |
| EDR-018 | Consolidação do Decision Register da planilha (versão mais completa) | PENDING_CONFIRMATION |
| EDR-019 | Tratamento do Guide, de valores de teste e foco | APPROVED |
| EDR-020 | Solver cinemático 3D como MODEL/cross-check (Kinematics V2) | IMPLEMENTED |
| EDR-021 | Aviso de Fz<0 e validações de entrada no Python | VERIFIED |
| EDR-022 | Valores de teste e demonstrativos sem rastreabilidade obrigatória | APPROVED |
| EDR-023 | D1 — Identificadores SUS-407 a SUS-413 | AWAITING_DECISION |
| EDR-024 | D2 — Schema de hardpoints V2.0 | AWAITING_DECISION |
| EDR-025 | D3 / Decisão A — Tratamento de placeholders na planilha | AWAITING_DECISION |
| EDR-026 | D4 — Convenção de sinal de AD/AS (positivo = anti; negativo = pro; zero = sem efeito líquido) | PENDING_CONFIRMATION |
| EDR-027 | D4-MR / D6 / Decisão B — Limiar absoluto de MR e cross-check | AWAITING_DECISION |
| EDR-028 | D5 — IC lateral: funcionalidade exploratória | APPROVED_WITH_CONDITIONS |
| EDR-029 | D8 — Roll Center: funcionalidade exploratória e procedimento de validação | APPROVED_WITH_CONDITIONS |
| EDR-030 | D7 — Camber/toe estáticos: referência x calculado; sem distância mínima universal | APPROVED_WITH_CONDITIONS |
| EDR-031 | REQ-001/REQ-002 e proveniência do REQ-003 em 13_VALIDATION | VERIFIED |
| EDR-032 | Geometry Brief — estrutura de interface especificação→CAD | IMPLEMENTED |
| EDR-033 | Escopo de AD/AS e anti-lift (frenagem regenerativa) | AWAITING_DECISION |
| EDR-034 | Critérios de promoção DRAFT/CHECKED/FROZEN/STALE | AWAITING_DECISION |
| EDR-035 | Semântica de N/A e TBD (e proveniência de dados) | AWAITING_DECISION |
| EDR-036 | Decisão C — IDs para camber e toe estáticos (referência e calculado) | AWAITING_DECISION |
| EDR-037 | Escopo da implementação do pneu em 10_TIRE (V2.2) | IMPLEMENTED |
| EDR-038 | Dataset .tir TTC como dado PROVISÓRIO de desenvolvimento | APPROVED |
| EDR-039 | Sistema de eixos do arquivo de pneu (SAE→ISO), convenção de sinais e espelhamento esquerdo | APPROVED_WITH_CONDITIONS |
| EDR-040 | Formato do dataset de pneu (PAC2002 x MF 5.2 x 6.1.2 x 6.2) e origem (OptimumTire 2) | AWAITING_DECISION |
| EDR-041 | Entradas α/γ/κ demonstrativas e N/A como estado de saída sem dado | APPROVED_WITH_CONDITIONS |
| EDR-042 | Verificação das equações do pneu contra fontes de terceiros; caminho até a fonte primária | VERIFIED |

## 3. Decisões que dependem do usuário (agora)

- **EDR-018** (PENDING_CONFIRMATION): Consolidação do Decision Register da planilha (versão mais completa)
- **EDR-023** (AWAITING_DECISION): D1 — Identificadores SUS-407 a SUS-413
- **EDR-024** (AWAITING_DECISION): D2 — Schema de hardpoints V2.0
- **EDR-025** (AWAITING_DECISION): D3 / Decisão A — Tratamento de placeholders na planilha
- **EDR-026** (PENDING_CONFIRMATION): D4 — Convenção de sinal de AD/AS (positivo = anti; negativo = pro; zero = sem efeito líquido)
- **EDR-027** (AWAITING_DECISION): D4-MR / D6 / Decisão B — Limiar absoluto de MR e cross-check
- **EDR-033** (AWAITING_DECISION): Escopo de AD/AS e anti-lift (frenagem regenerativa)
- **EDR-034** (AWAITING_DECISION): Critérios de promoção DRAFT/CHECKED/FROZEN/STALE
- **EDR-035** (AWAITING_DECISION): Semântica de N/A e TBD (e proveniência de dados)
- **EDR-036** (AWAITING_DECISION): Decisão C — IDs para camber e toe estáticos (referência e calculado)
- **EDR-040** (AWAITING_DECISION): Formato do dataset de pneu e origem (OptimumTire 2)

## 4. Proposta de IDs para camber/toe estáticos (Decisão C — NÃO criados)

Proposta apresentada para decisão; números **provisórios**, dependentes da resolução de D1 (EDR-023). Segue o padrão SUS-401/402 (um ID por fonte) e a regra de que uma estimativa geométrica **não substitui silenciosamente** um valor de referência.

| ID proposto | Nome e definição | Unidade | Tipo de dado | Origem / método | Dependências | Faixa |
|---|---|---|---|---|---|---|
| SUS-414 | Static Camber (Reference): camber estático por canto no ride height do Setup | ° | INPUT / REFERENCE | Medição, especificação ou export de ferramenta de referência, com fonte, configuração (KOP) e incerteza declaradas | SUS-000, Setup S-XXX, KOP | SUS-4XX |
| SUS-415 | Static Toe (Reference): toe estático por canto (+ = toe-out) | ° | INPUT / REFERENCE | Idem | SUS-000, Setup, KOP | SUS-4XX |
| SUS-416 | Static Camber (Model/Check): camber em z=0 derivado dos hardpoints | ° | MODEL (cross-check) | `asin(−â_z)`, `â=(SPINDLE_PT−WHEEL_CENTER)/\|·\|`; σ_γ ≈ √2·σ_z/d (1ª ordem) | hardpoints.csv | SUS-4XX |
| SUS-417 | Static Toe (Model/Check): toe em z=0 derivado dos hardpoints | ° | MODEL (cross-check) | `asin(−â_x/√(â_x²+â_y²))` | hardpoints.csv | SUS-4XX |

Impactos: Standard (novas fichas), Data Contract §6 (campos com unidade e proveniência), Geometry Brief (campos de camber/toe estáticos), rastreabilidade. Alternativa mais enxuta (2 IDs: apenas SUS-414/415, usando SUS-407/408 em z=0 como calculado) reduz IDs mas mistura "curva" e "valor estático" no mesmo ID, contrariando a exigência de significado único. Recomendação preliminar do prompt: Opção A, condicionada a D1.

## 5. Registros

### EDR-001 — Sistema de coordenadas ISO 8855 (X frente, Y esquerda, Z cima)

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Ambiguidade de eixos entre CAD, OptimumKinematics e Lotus.
- **Question:** Qual sistema de eixos é a autoridade do projeto?
- **Alternatives:** Convenção Lotus (X trás, Y direita) ou a do OptimumKinematics default.
- **Decision:** ISO 8855 destro; ferramentas externas se adaptam (arquitetura 17.1).
- **Rationale:** Uma única autoridade evita erros de sinal.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível), §4 e §17.1; DR-001 (planilha).
- **Assumptions:** OptimumKinematics configurado explicitamente (não confiar no default).
- **Consequences:** Adapter Lotus obrigatório: X=-X, Y=-Y, Z=Z.
- **Affected_Artifacts:** arquitetura §4/§17.1; Standard; Data Contract; hardpoints_V2_0.py (lotus_to_iso8855); planilha 00_README.
- **Affected_Tests:** TC-HP-010, TC-HP-011a/b, TC-HP-101a-e
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Mudança de ferramenta de referência ou de convenção de exportação.
- **Related_Decisions:** EDR-002, EDR-024, DR-001
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-002 — Convenções de camber e toe (camber + = topo para fora; toe + = toe-out)

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Lotus usa toe + = toe-in.
- **Question:** Qual convenção de camber/toe?
- **Alternatives:** Convenção do Lotus.
- **Decision:** Camber + = topo para fora; toe + = toe-out (igual ao OptimumKinematics; Lotus exige inversão de sinal do toe).
- **Rationale:** Coincide com a ferramenta de referência de cinemática.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível), §17.2; test_kinematics TC-KIN-106a/b (esq. e dir.).
- **Assumptions:** Verificar a convenção real exportada pelo OptimumKinematics da equipe.
- **Consequences:** Importação direta do OptimumKinematics; inversão do toe do Lotus.
- **Affected_Artifacts:** arquitetura §17.2; Standard SUS-404/405/407/408; kinematics_model_V2_0.py.
- **Affected_Tests:** TC-KIN-106a, TC-KIN-106b
- **Dependencies:** EDR-001
- **Approval_Conditions:** —
- **Reopening_Criteria:** Divergência encontrada contra o export real do OptimumKinematics.
- **Related_Decisions:** EDR-001
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-003 — Motion Ratio definido como wheel/spring

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Risco de fator invertido entre fontes.
- **Question:** Qual a convenção de MR?
- **Alternatives:** spring/wheel.
- **Decision:** MR = Δwheel travel / Δspring travel; nome explícito `MR [wheel/spring]` / `motion_ratio_wheel_spring`; K_wheel = K_spring/MR².
- **Rationale:** Evita fator invertido.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §5; DR-002 (planilha); test_suspension TC-009, TC-010.
- **Assumptions:** E03 não especifica a direção do 1,76: assumida wheel/spring (comentário de 06_SUSPENSION B6).
- **Consequences:** Inversão não é detectada por limiar absoluto (ver EDR-027).
- **Affected_Artifacts:** Standard SUS-201/202/409; suspension_model; planilha 06_SUSPENSION.
- **Affected_Tests:** TC-009, TC-SUS-V21-001..005
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Confirmação de que o 1,76 do E03 está na convenção oposta.
- **Related_Decisions:** EDR-027
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-004 — Hierarquia de autoridade das ferramentas

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Várias ferramentas calculam as mesmas grandezas.
- **Question:** Quem é autoridade de quê?
- **Alternatives:** Python como autoridade.
- **Decision:** Milliken (framework) → OptimumKinematics (cinemática) → OptimumTire (pneu) → Lotus (cross-check independente) → Python (modelo) → Excel (interface/orquestração); CAD = master geometry; FEA = estrutural.
- **Rationale:** Python é autoridade só por implementar equação previamente congelada.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §17; memória de projeto.
- **Assumptions:** OptimumKinematics e OptimumTire ainda não disponíveis.
- **Consequences:** Todo MODEL de cinemática é cross-check, nunca REFERENCE.
- **Affected_Artifacts:** Todos.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Mudança de ferramentas da equipe.
- **Related_Decisions:** EDR-020, DR-009
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-005 — Namespaces e faixas de ID (SUS-0XX a 8XX; REQ/TARGET/VAL separados)

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Colisão SUS-001/002 e esquemas de ID conflitantes.
- **Question:** Como identificar parâmetros sem colisão?
- **Alternatives:** Esquema VEH/KIN/DYN/TIR/FREQ.
- **Decision:** SUS-XXX por faixa de domínio; REQ-XXX, TARGET-XXX, VAL-XXX com namespaces próprios, sem reutilizar IDs.
- **Rationale:** Evita colisões e 1:1 forçado.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §2 e §18.
- **Assumptions:** —
- **Consequences:** Novos IDs devem respeitar faixas (ver EDR-023).
- **Affected_Artifacts:** arquitetura; Standard; Data Contract; planilha.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Necessidade de grandeza sem faixa adequada.
- **Related_Decisions:** EDR-023, EDR-036
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-006 — Taxonomia de Data Type (INPUT, TARGET, REFERENCE, MODEL, CALCULATED, REQUIREMENT)

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Mistura de natureza do dado e metadados.
- **Question:** Quais tipos de dado existem?
- **Alternatives:** Sétimo tipo 'MODEL/CHECK'.
- **Decision:** Seis tipos; 'cross-check' é flag de metadado de MODEL, não tipo novo.
- **Rationale:** Mantém a taxonomia fechada.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §3 e §18.
- **Assumptions:** —
- **Consequences:** MODELs de cinemática V2 levam a flag cross-check.
- **Affected_Artifacts:** arquitetura; Standard.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Caso que a taxonomia não consiga representar (demonstrado).
- **Related_Decisions:** EDR-007
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-007 — Ciclo de vida e validação como duas dimensões independentes

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Lista única de status misturava maturidade e resultado de validação.
- **Question:** Como representar estado de um parâmetro?
- **Alternatives:** Lista única.
- **Decision:** Lifecycle: OPEN, DRAFT, CHECKED, FROZEN, STALE. Validation: NOT_VALIDATED, PASS, WARNING, FAIL.
- **Rationale:** Um parâmetro pode ser FROZEN e STALE/NOT_VALIDATED ao mesmo tempo.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §3; DEC-010 referenciada.
- **Assumptions:** —
- **Consequences:** Estados do registro de decisões (este arquivo) são uma terceira coisa e não reutilizam esses nomes.
- **Affected_Artifacts:** arquitetura; Standard; Data Contract §2.1.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Estado necessário que não caiba nas duas dimensões (demonstrado).
- **Related_Decisions:** EDR-034, EDR-035
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-008 — Relação Excel–Python–CAD e intercâmbio de dados

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Excel como interface; modelos em Python.
- **Question:** Como trocar dados?
- **Alternatives:** xlwings/PyXLL/macros.
- **Decision:** Python externo ao Excel; JSON de configuração/resultados e CSV tabular; unidade explícita no nome do campo; hardpoints.csv único; sem bridge automático por ora (Excel é segunda implementação/cross-check; DR-008).
- **Rationale:** Evita unidade implícita (450 mm lido como 450 m) e dupla digitação.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §8, §10; Data Contract; DR-008.
- **Assumptions:** Bridge não implementado: o Python não faz JSON I/O (Data Contract V2.0 §5).
- **Consequences:** Resultados de kinematics entram na planilha por atualização manual.
- **Affected_Artifacts:** Data Contract; hardpoints_V2_0.py; planilha.
- **Affected_Tests:** TC-HP-003
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Implementação do bridge.
- **Related_Decisions:** EDR-024
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-009 — RC estático no ride height de referência (V1); RC(z) permanece na REFERENCE

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Migração de RC com a rolagem.
- **Question:** Como o modelo quase-estático usa o RC?
- **Alternatives:** RC(z) iterativo.
- **Decision:** V1 usa RC_static = RC(z_RH) (REFERENCE do OptimumKinematics); migração é limitação conhecida.
- **Rationale:** Escopo controlável.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §5/§6/§17.4; DR-005.
- **Assumptions:** —
- **Consequences:** O cálculo de RC cinemático da V2 é exploratório (EDR-029).
- **Affected_Artifacts:** Standard SUS-103/401/402; planilha 06_SUSPENSION.
- **Affected_Tests:** TC-007
- **Dependencies:** EDR-004
- **Approval_Conditions:** —
- **Reopening_Criteria:** Decisão de modelar RC(z) no load transfer.
- **Related_Decisions:** EDR-029
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-010 — Anti-dive/anti-squat não alteram a magnitude da transferência de carga longitudinal

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Risco de descontar ΔFz por (1−%AD).
- **Question:** Como AD/AS entram na cadeia de cálculo?
- **Alternatives:** Descontar do load transfer.
- **Decision:** AD/AS descrevem a partição geométrica vs elástica; ΔFz_long nunca é descontado.
- **Rationale:** Equilíbrio de corpo rígido.
- **Evidence:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível) §5; DR-006.
- **Assumptions:** —
- **Consequences:** SUS-301/302 nunca alimentam SUS-102.
- **Affected_Artifacts:** Standard SUS-102/301/302.
- **Affected_Tests:** TC-002, TC-003
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-026, EDR-033
- **Source_Conversation_or_Document:** arquitetura-consolidada-V2.0 (decisão registrada no documento; registro DEC individual não disponível)

### EDR-011 — Transferência lateral pelo modelo de duas molas de Milliken

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Escolha do modelo de load transfer.
- **Question:** Qual modelo lateral?
- **Alternatives:** Modelos simplificados sem RC.
- **Decision:** Modelo de duas molas (elástica por rigidez de rolagem, geométrica por RC, não-suspensa).
- **Rationale:** Framework de referência do projeto.
- **Evidence:** Standard SUS-103 (CHECKED): transcrição conferida contra reprodução secundária (Chalmers 2015:68); conservação de momento verificada (TC-005). Fonte primária não consultada nesta etapa.
- **Assumptions:** Teoria de referência não é 'validada' por teste; valida-se transcrição/implementação/aplicação.
- **Consequences:** Validation Status permanece NOT_VALIDATED.
- **Affected_Artifacts:** Standard SUS-103; suspension_model; planilha 09_LOADS.
- **Affected_Tests:** TC-001, TC-005..008
- **Dependencies:** EDR-009
- **Approval_Conditions:** —
- **Reopening_Criteria:** Divergência contra dado real de Fz.
- **Related_Decisions:** EDR-009
- **Source_Conversation_or_Document:** Standard SUS-103; DR-003

### EDR-012 — Separar referência histórica (T09) do baseline do carro atual (TX/E05)

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Dados de carros diferentes misturados.
- **Question:** Como tratar dados do T09/E03?
- **Alternatives:** Usar T09 como baseline.
- **Decision:** T09/E03 servem como referência histórica; powertrain só do E05/TX.
- **Rationale:** Evitar contaminação.
- **Evidence:** DR-004 (planilha); memória do projeto.
- **Assumptions:** —
- **Consequences:** OBSERVAÇÃO DE AUDITORIA: 06_SUSPENSION usa spring rate, MR, ARB e RC de T09/E03 (comentários de B4–B7, B10, B11, B14, B15). Se o Setup S-001 pretende representar o TX, há tensão com esta decisão; o usuário precisa esclarecer.
- **Affected_Artifacts:** planilha 06_SUSPENSION; mapa de dependências.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Esclarecimento sobre o propósito de S-001.
- **Related_Decisions:** EDR-025
- **Source_Conversation_or_Document:** DR-004; comentários de células

### EDR-013 — Aero fixo por Setup (sem mapa aerodinâmico)

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Escopo V1.
- **Question:** Aero variável?
- **Alternatives:** F_aero(v).
- **Decision:** Downforce e balanço fixos por Setup.
- **Rationale:** Escopo controlável.
- **Evidence:** DR-007; planilha 00_README (limitação conhecida).
- **Assumptions:** —
- **Consequences:** —
- **Affected_Artifacts:** Standard SUS-701/702.
- **Affected_Tests:** TC-004
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Dados de túnel/CFD.
- **Related_Decisions:** —
- **Source_Conversation_or_Document:** DR-007

### EDR-014 — Design Mode explícito, sem goal seek opaco

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Cálculo reverso.
- **Question:** Como resolver o sentido inverso?
- **Alternatives:** Goal Seek/solver genérico.
- **Decision:** Relações analíticas fechadas, indicando qual variável é alvo e qual é resolvida.
- **Rationale:** Evita uso da equação no sentido errado.
- **Evidence:** Guide Apêndice E.1 (DR-010 do Guide); planilha DR-010.
- **Assumptions:** Valores de 11_DESIGN (2,5/2,7 Hz; λ_f 0,55) são demonstrativos, não TARGET.
- **Consequences:** —
- **Affected_Artifacts:** Standard SUS-202/205/208; planilha 11_DESIGN.
- **Affected_Tests:** TC-010
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-025
- **Source_Conversation_or_Document:** DR-010

### EDR-015 — Pneu como REFERENCE, sem ajuste próprio na V1

- **Date:** Não registrada
- **Status:** APPROVED
- **Context:** Modelo de pneu.
- **Question:** A V1 ajusta o pneu?
- **Alternatives:** Fit próprio.
- **Decision:** Tire consumido do OptimumTire/TTC; níveis 1 (lookup) ou 2 (paramétrico), DEC-007.
- **Rationale:** Sem fit próprio na V1.
- **Evidence:** DR-011 (planilha V2.0; no Guide é DR-008); Standard SUS-501..503.
- **Assumptions:** Convenção de sinal de α e slip a verificar.
- **Consequences:** 10_TIRE implementada na V2.2 com dataset provisório (EDR-037; era WAITING INPUT até a V2.1). Cargas verticais por canto NÃO dependem do pneu (arquitetura §1.1).
- **Affected_Artifacts:** Standard; planilha 10_TIRE.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Disponibilidade do OptimumTire.
- **Related_Decisions:** EDR-032
- **Source_Conversation_or_Document:** DR-011; arquitetura §1.1

### EDR-016 — Numeração canônica de Test Cases

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** IMPLEMENTED
- **Context:** Guide, arquitetura/Standard/Python usam numerações de TC diferentes.
- **Question:** Qual numeração é a canônica?
- **Alternatives:** Numeração do Guide (Apêndice D).
- **Decision:** Canônica = arquitetura §17.7 / Standard / Python (TC-001..012); Guide a alinhar depois. Namespaces próprios: TC-KIN, TC-HP, TC-SUS-V2/V21, TC-WB.
- **Rationale:** Três de quatro documentos concordam.
- **Evidence:** Resposta do usuário ('3. Confirmo') ao registro de decisões anterior; Standard V1.0+ e arquitetura V1.0+ atualizados.
- **Assumptions:** —
- **Consequences:** Guide permanece divergente (fora de escopo agora).
- **Affected_Artifacts:** arquitetura; Standard; Data Contract; testes.
- **Affected_Tests:** todos
- **Dependencies:** —
- **Approval_Conditions:** Alinhar o Guide quando o foco voltar a ele.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-019
- **Source_Conversation_or_Document:** Conversa Sistema_DDS

### EDR-017 — Regra de versionamento dos artefatos

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** APPROVED
- **Context:** Problemas de versionamento.
- **Question:** Como versionar?
- **Alternatives:** —
- **Decision:** Inicia em V1.0; o decimal sobe a cada pequena implementação (V1.0→V1.1...). Arquivos .py usam _V1_0 (ponto impede import). Arquivos históricos nunca são sobrescritos.
- **Rationale:** Rastreabilidade.
- **Evidence:** Mensagem do usuário ('Vamos de V1 e mudamos os decimais...').
- **Assumptions:** A numeração V2.x foi adotada pelo assistente para a rodada de Kinematics; confirmação explícita do usuário para 'V2' não registrada.
- **Consequences:** Arquivos de teste podem ter versão diferente do módulo que testam.
- **Affected_Artifacts:** Todos.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** —
- **Related_Decisions:** —
- **Source_Conversation_or_Document:** Conversa Sistema_DDS

### EDR-018 — Consolidação do Decision Register da planilha (versão mais completa)

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** PENDING_CONFIRMATION
- **Context:** Planilha (DR-001..009) e Guide (DR-001..010) divergiam.
- **Question:** Qual versão é a mais completa?
- **Alternatives:** Manter a do Guide.
- **Decision:** O usuário DELEGOU a avaliação ('avalie qual é a mais completa e implemente'). Implementado: base da planilha + DR-010 (Design Mode) e DR-011 (Tire; era DR-008 no Guide); colunas Status/Origem.
- **Rationale:** Planilha traz Why/Constraints/Owner.
- **Evidence:** planilha V1.0+/V2.0 04_DECISION_REGISTER.
- **Assumptions:** DR-009 do Guide interpretado como a mesma decisão do DR-009 da planilha (interpretação do assistente).
- **Consequences:** Guide a alinhar.
- **Affected_Artifacts:** planilha 04_DECISION_REGISTER; registro de versões.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** Confirmação explícita do usuário sobre o resultado e sobre a interpretação do DR-009.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-019
- **Source_Conversation_or_Document:** Conversa Sistema_DDS

### EDR-019 — Tratamento do Guide, de valores de teste e foco

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** APPROVED
- **Context:** Divergências entre Guide e demais documentos.
- **Question:** Como lidar com o Guide?
- **Alternatives:** —
- **Decision:** Divergências são esperadas até certo ponto (o Guide considera só as últimas versões); valores usados para testar fórmulas não têm necessariamente rastreabilidade; os códigos não entram no Guide; o foco é completar a planilha, não o Guide.
- **Rationale:** Declarado pelo usuário.
- **Evidence:** Mensagens do usuário.
- **Assumptions:** —
- **Consequences:** Alinhamento do Guide fica pendente.
- **Affected_Artifacts:** Guide (fora de escopo).
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** Mudança de foco do projeto.
- **Related_Decisions:** EDR-016, EDR-018
- **Source_Conversation_or_Document:** Conversa Sistema_DDS

### EDR-020 — Solver cinemático 3D como MODEL/cross-check (Kinematics V2)

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** IMPLEMENTED
- **Context:** Pedido de Kinematics o mais completa possível; DR-009 previa o solver interno para a V2.
- **Question:** Implementar o solver 3D?
- **Alternatives:** Manter só 2D da V1.
- **Decision:** Implementado kinematics_model_V2_0.py como MODEL/cross-check, nunca REFERENCE (DR-012, DRAFT).
- **Rationale:** Pedido do usuário; formulação verificada por solver independente.
- **Evidence:** test_kinematics_model_V2_0: 47/47; mutação 14/14 detectados. Nenhuma comparação com OptimumKinematics/Lotus/carro real.
- **Assumptions:** Hipóteses gerais do Bloco E.2 (corpos rígidos, juntas ideais, curso = Z do centro da roda).
- **Consequences:** IDs SUS-407..413 propostos (EDR-023).
- **Affected_Artifacts:** kinematics_model_V2_0.py; Standard V2.0 Bloco E.2; planilha 07_KINEMATICS/04.
- **Affected_Tests:** TC-KIN-001..006, 101..117
- **Dependencies:** EDR-004, EDR-024
- **Approval_Conditions:** Validação externa pendente (TC-011/012).
- **Reopening_Criteria:** Divergência contra OptimumKinematics/Lotus.
- **Related_Decisions:** EDR-023, EDR-028, EDR-029
- **Source_Conversation_or_Document:** Conversa Sistema_DDS; DR-012

### EDR-021 — Aviso de Fz<0 e validações de entrada no Python

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** VERIFIED
- **Context:** Standard SUS-104 e Guide D.2 especificavam o comportamento; só a planilha o tinha.
- **Question:** Implementar no Python?
- **Alternatives:** —
- **Decision:** FzLiftoffWarning por canto (sem clamp), bloqueios do Guide D.2 com ID da ficha; limiar de aviso de MR provisório (EDR-027).
- **Rationale:** Spec existente.
- **Evidence:** test_suspension_model_V2_0: 33/33; mutação 6/6 detectados; regressão idêntica à V1.0.
- **Assumptions:** —
- **Consequences:** Verificado por testes; não é validação física.
- **Affected_Artifacts:** suspension_model_V2_0.py (V2_1 mantém); Data Contract §5.
- **Affected_Tests:** TC-SUS-V2-001..004
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-027
- **Source_Conversation_or_Document:** Conversa Sistema_DDS

### EDR-022 — Valores de teste e demonstrativos sem rastreabilidade obrigatória

- **Date:** Sessão 2026-10-09/10 (data/hora exatas do turno não registradas)
- **Status:** APPROVED
- **Context:** Valores usados para testar fórmulas.
- **Question:** Exigir rastreabilidade para valores de teste?
- **Alternatives:** Exigir.
- **Decision:** Não necessariamente; valores sintéticos devem ser identificados como tais (Status SYNTHETIC; rótulos).
- **Rationale:** Declarado pelo usuário.
- **Evidence:** Mensagem do usuário.
- **Assumptions:** —
- **Consequences:** Interage com EDR-025: valores sem proveniência não podem aparecer como resultado do carro.
- **Affected_Artifacts:** testes; hardpoints sintéticos.
- **Affected_Tests:** —
- **Dependencies:** —
- **Approval_Conditions:** —
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-025
- **Source_Conversation_or_Document:** Conversa Sistema_DDS

### EDR-023 — D1 — Identificadores SUS-407 a SUS-413

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** IDs propostos na V2.0 (Standard Bloco E.2).
- **Question:** Aprovar SUS-407..413?
- **Alternatives:** (a) aprovar como estão; (b) dividir IDs agrupados e realocar fora de faixa; (c) adiar.
- **Decision:** PENDENTE. Condições já declaradas pelo usuário: no máximo CHECKED nesta etapa; não renumerar IDs existentes; não criar IDs sem autorização; aprovação de ID não valida equação.
- **Rationale:** Auditoria confirmou 4 inconsistências estruturais (ver Evidence).
- **Evidence:** Confirmado em Standard V2.0: SUS-410 agrupa caster, KPI, scrub e trail (4 grandezas); SUS-412 agrupa IC frontal, IC lateral, RC por canto, RC do eixo e inclinação (5); SUS-411 agrupa track e wheelbase change (2); SUS-413 agrupa yaw(s) e razão de direção (2). SUS-409 (MR, Domain 'Kinematics / Stiffness') fica fora da faixa 2XX onde está SUS-201; SUS-413 (Domain 'Steering / Kinematics') fora da faixa 6XX onde está SUS-601. A arquitetura não define IDs compostos; sufixo -F/-R existe só como indexação por eixo. Sem colisão: SUS-407..413 não aparecem em nenhum outro documento. Guide tem 0 menções.
- **Assumptions:** Cada ID = um parâmetro inequívoco (exigência de D1).
- **Consequences:** Proposta (NÃO aplicada): dividir SUS-410/411/412/413 em IDs individuais; realocar MR cross-check (SUS-409→faixa 2XX, ex. SUS-209) e direção (SUS-413→faixa 6XX, ex. SUS-602) — ou documentar exceção de faixa. Requer autorização para criar IDs.
- **Affected_Artifacts:** Standard V2.0 Bloco E.2; arquitetura adendo; Data Contract §6; Geometry Brief; testes.
- **Affected_Tests:** TC-KIN-101..117
- **Dependencies:** EDR-005, EDR-036
- **Approval_Conditions:** Resolver as 4 inconsistências antes de qualquer congelamento.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-005, EDR-020, EDR-036
- **Source_Conversation_or_Document:** Prompt D1; auditoria V2.1

### EDR-024 — D2 — Schema de hardpoints V2.0

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** Schema proposto na V2.0 (hardpoint-schema-V2.0.md).
- **Question:** Aprovar como contrato oficial?
- **Alternatives:** (a) aprovar V2.0; (b) V2.1 com campos de origem/transformação, depois aprovar; (c) adiar.
- **Decision:** PENDENTE. Condição declarada: não congelar antes da primeira importação real de aceitação.
- **Rationale:** Auditoria encontrou lacunas.
- **Evidence:** TC-HP-101c: X invertido isolado em eixo único é ACEITO (GAP-HP-001). TC-HP-103a/b: .meta.json não registra convenção/transformação de origem; 'UNKNOWN' é aceito silenciosamente (GAP-HP-002). TC-HP-102b: tolerância de 1 mm do contact patch é erro rígido (GAP-HP-003). Y e Z invertidos, e X invertido com dois eixos, são rejeitados (TC-HP-101a/b/d). Vocabulários de Component/Status são proposta do assistente.
- **Assumptions:** Formato real do export do OptimumKinematics desconhecido.
- **Consequences:** Proposta (NÃO aplicada): meta com source_coordinate_system, target_coordinate_system, transform_applied (eixos/sinais), unidades de origem/destino, ferramenta/versão, id/versão do arquivo e convention_status ∈ {TUPA, TRANSFORMED, KNOWN_NOT_CONVERTED, UNKNOWN}; UNKNOWN rejeitado; tolerância do solo configurável (erro/warning); bump para schema V2.1 com migração explícita.
- **Affected_Artifacts:** hardpoint-schema; hardpoints_V2_0.py; Data Contract §6.
- **Affected_Tests:** TC-HP-001..018, TC-HP-101..104
- **Dependencies:** EDR-001, EDR-008
- **Approval_Conditions:** Congelar só após importação real que cubra campos, unidades, coordenadas, transformações, completude, regras geométricas e proveniência; achados corrigidos e registrados.
- **Reopening_Criteria:** Qualquer falha na importação real.
- **Related_Decisions:** EDR-001, EDR-008, EDR-020
- **Source_Conversation_or_Document:** Prompt D2; auditoria V2.1

### EDR-025 — D3 / Decisão A — Tratamento de placeholders na planilha

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** Planilha mostra números dependentes de dados não reais.
- **Question:** Opção A (marcar, manter fórmulas) ou B (proteger só células terminais)?
- **Alternatives:** A: proveniência visível + fórmulas intactas. B: guardar terminais com IF(origem válida; cálculo; 'N/A'). B': B com sensibilidade quantificada por saída.
- **Decision:** PENDENTE. Recomendação preliminar do prompt: B com proteção seletiva e preservação dos testes matemáticos. Recomendação refinada do assistente: B' (ver Evidence).
- **Rationale:** Mapa auditável confirma 45/84 fórmulas dependentes de dado que não é do veículo.
- **Evidence:** placeholder-dependency-map-V2.1.csv: 45 fórmulas com raiz T1 (placeholder, arbitrário, estimativa ou alvo demonstrativo); 23 só com T2 (dado de outro veículo/hipótese/caso de carga sem proveniência); 16 só com T3. Das 45: 22 intermediárias, 17 terminais e 6 verificações de identidade/espelhos (TC-004/005 e λ). REQ-004 (13_VALIDATION B21/B22; dashboard B23/B24) retorna PASS a partir dos placeholders de curso 60/65 mm (07_KINEMATICS B31/B32). Anti-dive/squat (06_SUSPENSION B40/B41) dependem totalmente de placeholders. Sensibilidade (Python com os valores da planilha): trocar a massa não-suspensa arbitrária (15/18 kg) por 0 ou 2× altera Fz em ≤ 2,3 N (0,2%) e a frequência natural em 5,4% a 6,4%. Proteger o Fz por mera ascendência esconderia um dado quase insensível; a frequência é sensível. Proveniência existe nos 35 comentários de célula (não é legível por máquina nem visível sem passar o mouse).
- **Assumptions:** Classificação T1/T2/T3 baseada em comentários e preenchimentos; as massas não-suspensas são ARBITRÁRIAS segundo o comentário de 05_VEHICLE B14/B15.
- **Consequences:** B exige alterar fórmulas terminais (lista a registrar por célula: aba, célula, fórmula anterior/nova, dependências, justificativa, teste). Verificações de identidade (TC-004/005) permanecem intactas.
- **Affected_Artifacts:** planilha 06, 09, 11, 13, 14; testes de planilha.
- **Affected_Tests:** TC-WB-xxx (a criar após decisão)
- **Dependencies:** EDR-022, EDR-035
- **Approval_Conditions:** Definir a regra de elegibilidade (por origem e/ou sensibilidade) antes de alterar.
- **Reopening_Criteria:** Novos dados reais substituindo placeholders.
- **Related_Decisions:** EDR-022, EDR-035
- **Source_Conversation_or_Document:** Prompt D3/Decisão A; auditoria V2.1

### EDR-026 — D4 — Convenção de sinal de AD/AS (positivo = anti; negativo = pro; zero = sem efeito líquido)

- **Date:** 2026-10-10
- **Status:** PENDING_CONFIRMATION
- **Context:** Forma V1 usa |d| e assume tan φ ≥ 0.
- **Question:** Adotar convenção de saída?
- **Alternatives:** Manter forma V1.
- **Decision:** O usuário instruiu 'Adote' no prompt anterior e chama de 'proposta' no atual: decisão efetiva não determinável. NÃO registrada como aprovada. A aprovação da convenção não valida o método geométrico.
- **Rationale:** —
- **Evidence:** anti_dive_percent_signed/anti_squat_percent_signed respeitam a convenção: TC-KIN-110b-e, TC-KIN-118a-f (zero, sinais, antissimetria, linearidade). A forma V1 devolve sinal positivo para IC à frente e acima na frente (TC-KIN-110d).
- **Assumptions:** Linha de força definida por (ponto de reação → IC lateral); reação em contact patch ou centro da roda depende da configuração real (em aberto).
- **Consequences:** Se aprovada: documentar no Standard, Python, Data Contract e planilha (planilha apenas documentada; resultados dela seguem placeholder).
- **Affected_Artifacts:** Standard SUS-301/302/406; kinematics_model; Data Contract; planilha 06/07.
- **Affected_Tests:** TC-KIN-110, TC-KIN-118
- **Dependencies:** EDR-028, EDR-033
- **Approval_Conditions:** Método de cálculo permanece PROVISÓRIO/NÃO VALIDADO até derivação completa e comparação independente.
- **Reopening_Criteria:** Comparação externa discordante.
- **Related_Decisions:** EDR-010, EDR-028, EDR-033
- **Source_Conversation_or_Document:** Prompts D4

### EDR-027 — D4-MR / D6 / Decisão B — Limiar absoluto de MR e cross-check

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** Limiar 0,2 emite SmallMotionRatioWarning em wheel_rate().
- **Question:** Opção A (desligar por padrão) ou B (manter 0,2 provisório)?
- **Alternatives:** A: default None + cross-check. B: manter 0,2 configurável + cross-check.
- **Decision:** PARCIAL. Decidido pelo usuário: NÃO oficializar 0,2 como limite de engenharia. Pendente: valor padrão (A ou B). Recomendação preliminar do prompt: A, com aviso claro de ausência de referência.
- **Rationale:** O limiar não detecta a inversão relevante.
- **Evidence:** TC-SUS-V21-004: com MR=1,76 e inverso 0,568 nenhum aviso é emitido; K_w erra 9,6× (=1,76^4). Cross-check implementado e testado (mr_crosscheck; TC-SUS-V21-001..005): sem referência → NOT_EXECUTED; sem tolerância → TOLERANCE_NOT_SET (sem tolerância padrão); inversão → INVERSION_SUSPECTED só como suspeita; MR≈1 → não distingue.
- **Assumptions:** A tolerância de comparação depende de incerteza real dos hardpoints, diferenças de definição e ponto de operação: NÃO definida.
- **Consequences:** Comportamento do limiar NÃO foi alterado nesta rodada (aguarda a decisão).
- **Affected_Artifacts:** suspension_model_V2_1.py; Standard; Data Contract.
- **Affected_Tests:** TC-SUS-V2-002, TC-SUS-V21-001..005
- **Dependencies:** EDR-003
- **Approval_Conditions:** Separar erro de entrada, condição numérica crítica e alerta configurável (categorias do prompt D6).
- **Reopening_Criteria:** Primeiro MR geométrico real disponível.
- **Related_Decisions:** EDR-003, EDR-021
- **Source_Conversation_or_Document:** Prompts D6/D4-MR/Decisão B

### EDR-028 — D5 — IC lateral: funcionalidade exploratória

- **Date:** 2026-10-10
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** IC lateral por normais às velocidades dos ball joints (SUS-412).
- **Question:** Qual o estado oficial?
- **Alternatives:** Declarar definição oficial.
- **Decision:** Mantido EXPLORATÓRIO (diretiva do usuário): sem definição oficial validada; resultado identificado como convenção interna do modelo; validação PENDENTE.
- **Rationale:** Convenção 3D não equivalente entre ferramentas por nome.
- **Evidence:** TC-KIN-107 (== 2D em mecanismo plano), TC-KIN-110a (== fórmula fechada), TC-KIN-114 (spread entre métodos: %AD 36,3/38,0/−680,7 na geometria sintética).
- **Assumptions:** Projeção 3D→plano não é movimento rígido plano.
- **Consequences:** Documentado em kinematics-exploratory-and-promotion-V2.1.md.
- **Affected_Artifacts:** Standard SUS-406/412; kinematics_model; documento exploratório.
- **Affected_Tests:** TC-KIN-107, 110, 111, 114
- **Dependencies:** EDR-004, EDR-026
- **Approval_Conditions:** Promoção só pelos critérios de EDR-034 e comparação com OptimumKinematics/Lotus.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-026, EDR-034
- **Source_Conversation_or_Document:** Prompts D5/8.3

### EDR-029 — D8 — Roll Center: funcionalidade exploratória e procedimento de validação

- **Date:** 2026-10-10
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** RC cinemático (SUS-412) e RC estático de referência (SUS-401).
- **Question:** Estado oficial?
- **Alternatives:** Declarar referência validada.
- **Decision:** Mantido EXPLORATÓRIO (diretiva do usuário). Procedimento de validação documentado; nenhuma comparação executada.
- **Rationale:** Sem hardpoints reais nem referência.
- **Evidence:** Sensibilidade na geometria SINTÉTICA com σ=0,5 mm arbitrário (RC σ≈1,9 mm, 13%): ilustra o mecanismo, NÃO se aplica ao Tupã; migração +59/−29 mm em ±30 mm também é sintética.
- **Assumptions:** —
- **Consequences:** Não usar para decisões de setup.
- **Affected_Artifacts:** Standard SUS-401/402/412; documento exploratório.
- **Affected_Tests:** TC-KIN-107b, 113
- **Dependencies:** EDR-009, EDR-024
- **Approval_Conditions:** Executar o procedimento (7 passos) com dados reais.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-009, EDR-028
- **Source_Conversation_or_Document:** Prompts D8/8.4

### EDR-030 — D7 — Camber/toe estáticos: referência x calculado; sem distância mínima universal

- **Date:** 2026-10-10
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** Camber estático derivado de SPINDLE_PT−WHEEL_CENTER; V2.0 recomendou ≥0,15 m sem justificativa.
- **Question:** Como tratar camber/toe estáticos?
- **Alternatives:** Aceitar a recomendação de 0,15 m.
- **Decision:** Diretivas do usuário: separar valor de referência de valor calculado, registrar proveniência, impedir substituição silenciosa, e NÃO adotar 0,15 m universal. A recomendação de 0,15 m da V2.0 era injustificada: CORRIGIDA na documentação V2.1. Criação de IDs depende da Decisão C.
- **Rationale:** O critério depende da incerteza das coordenadas e da tolerância angular.
- **Evidence:** TC-HP-104a/b: σ_ângulo ≈ √2·σ_coord/d verificado por Monte Carlo (3%), para erro em Z (camber) e em X (toe), no caso idealizado de uma componente por vez; TC-HP-104c: d_min = √2·σ/σ_γ,alvo reproduz o alvo; TC-HP-104d: CSV com 6 casas gera erro de 1,2e-4° na base de 0,08 m. O σ=0,5 mm do Monte Carlo da V2.0 foi arbitrário.
- **Assumptions:** Relação de 1ª ordem; sem correlação entre erros; não considera outros erros de CAD.
- **Consequences:** d_min é função da tolerância de ângulo escolhida pela equipe (não definida).
- **Affected_Artifacts:** hardpoint-schema-V2.1; Standard V2.1 (SUS-407); Data Contract; Geometry Brief.
- **Affected_Tests:** TC-HP-104a-d
- **Dependencies:** EDR-036
- **Approval_Conditions:** Dados reais de incerteza do CAD; tolerância angular definida pela equipe.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-036
- **Source_Conversation_or_Document:** Prompts D7

### EDR-031 — REQ-001/REQ-002 e proveniência do REQ-003 em 13_VALIDATION

- **Date:** 2026-10-10
- **Status:** VERIFIED
- **Context:** 13_VALIDATION só checava REQ-003 e REQ-004.
- **Question:** Implementar REQ-001/002?
- **Alternatives:** —
- **Decision:** Autorizado condicionalmente pelo prompt (se definidos e sem decisão nova). Auditoria confirmou definições em 02_REQUIREMENTS (>=1525 mm, V.1.2; menor/maior >=0,75, V.1.3.2). Implementado em 13_VALIDATION linhas 28-33; comentário de proveniência em REQ-003 (B19). REQ-004 NÃO alterado (depende da Decisão A).
- **Rationale:** Requisitos suficientemente definidos.
- **Evidence:** test_workbook_V2_1: 11/11 (limites exatos 1525 mm e 0,75; ordem das bitolas; ausência → 'N/A'; 0 erros de recálculo; 84 fórmulas anteriores idênticas).
- **Assumptions:** Dados de entrada vêm de E05 Key Parameters (especificação), NOT_VALIDATED.
- **Consequences:** Dashboard não foi estendido (pendente).
- **Affected_Artifacts:** planilha V2.1 13_VALIDATION, 15_CHANGELOG.
- **Affected_Tests:** TC-WB-001..005
- **Dependencies:** EDR-025
- **Approval_Conditions:** —
- **Reopening_Criteria:** Mudança do texto do Rulebook.
- **Related_Decisions:** EDR-025
- **Source_Conversation_or_Document:** Prompt §10

### EDR-032 — Geometry Brief — estrutura de interface especificação→CAD

- **Date:** 2026-10-10
- **Status:** IMPLEMENTED
- **Context:** A planilha vem antes como especificação; hoje contribui pouco.
- **Question:** Criar a estrutura do brief?
- **Alternatives:** Aba nova na planilha; artefato separado.
- **Decision:** Estrutura criada como artefato separado (geometry-brief-V2.1.md), com campos pendentes explícitos. Aba nova NÃO criada (alteraria a arquitetura de 16 abas).
- **Rationale:** Não duplicar hardpoints; não inventar targets.
- **Evidence:** geometry-brief-V2.1.md.
- **Assumptions:** Cargas verticais por canto não dependem do pneu (arquitetura §1.1): CORRIGE afirmação anterior do assistente.
- **Consequences:** Nenhum target/limite numérico foi criado.
- **Affected_Artifacts:** geometry-brief-V2.1.md; (futuro) planilha.
- **Affected_Tests:** Verificação estrutural manual
- **Dependencies:** EDR-023, EDR-025, EDR-036
- **Approval_Conditions:** Integração na planilha depende de decisão sobre aba nova.
- **Reopening_Criteria:** Targets definidos pela equipe.
- **Related_Decisions:** EDR-015
- **Source_Conversation_or_Document:** Prompt §11

### EDR-033 — Escopo de AD/AS e anti-lift (frenagem regenerativa)

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** SUS-301 cobre frenagem dianteira; SUS-302, tração traseira.
- **Question:** As fichas cobrem a configuração real?
- **Alternatives:** Ampliar fichas; manter escopo.
- **Decision:** PENDENTE: análise de escopo apresentada primeiro (prompt 8.2). Nenhuma ficha ampliada.
- **Rationale:** Não presumir distribuição de frenagem ou torque regenerativo.
- **Evidence:** Fichas SUS-301/302: só frenagem na frente e tração atrás. Documentos do projeto só definem TF_r = 1 (RWD, hipótese da V1) e REQ-006 (até 90% do curso do pedal regenerativo, EV); não definem posição do motor, split de freio hidráulico/regenerativo nem eixo regenerativo. INFERÊNCIA (sem fonte primária): frenagem no eixo traseiro (inclusive regenerativa) também submete a geometria traseira (anti-lift), não coberta.
- **Assumptions:** —
- **Consequences:** Casos de carga a avaliar: frenagem hidráulica F/R, frenagem regenerativa no eixo motriz, tração, e tração dianteira se houver AWD.
- **Affected_Artifacts:** Standard SUS-301/302/013/014 (futuro).
- **Affected_Tests:** —
- **Dependencies:** EDR-026
- **Approval_Conditions:** Dados reais de powertrain e freio da equipe.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-010, EDR-026
- **Source_Conversation_or_Document:** Prompt 8.2

### EDR-034 — Critérios de promoção DRAFT/CHECKED/FROZEN/STALE

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** Critérios implícitos na arquitetura.
- **Question:** Formalizar critérios?
- **Alternatives:** —
- **Decision:** PENDENTE: proposta redigida em kinematics-exploratory-and-promotion-V2.1.md §F, usando a taxonomia oficial (sem estados novos).
- **Rationale:** —
- **Evidence:** Documento citado.
- **Assumptions:** —
- **Consequences:** Define quando IC, RC e AD/AS podem ser promovidos.
- **Affected_Artifacts:** documento exploratório; Standard.
- **Affected_Tests:** —
- **Dependencies:** EDR-007
- **Approval_Conditions:** —
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-007, EDR-028, EDR-029
- **Source_Conversation_or_Document:** Prompt 8.5

### EDR-035 — Semântica de N/A e TBD (e proveniência de dados)

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** N/A e TBD não são estados oficiais (arquitetura §3).
- **Question:** Como formalizar sem criar dimensão nova?
- **Alternatives:** Nova dimensão 'estado do dado'; usar metadados existentes.
- **Decision:** PENDENTE. Proposta: N/A = não aplicável/não calculável na configuração atual; TBD = dado, requisito ou decisão pendente (equivale a Lifecycle OPEN para parâmetros); proveniência pelo metadado Source/Provenance já previsto na arquitetura §3 (hoje só em comentários de célula).
- **Rationale:** —
- **Evidence:** N/A e TBD já existiam na V1.0 (8 N/A, 10 TBD, ex.: 03_TARGETS); na V2.0 há 34 N/A, dos quais 26 foram adicionados pelo assistente no bloco de resultados do solver. CORRIGE afirmação anterior de que seriam prática estabelecida em 34 células.
- **Assumptions:** —
- **Consequences:** Usados em campos do Geometry Brief e de 07_KINEMATICS.
- **Affected_Artifacts:** Standard; Data Contract; planilha.
- **Affected_Tests:** TC-WB-004a/b
- **Dependencies:** EDR-007, EDR-025
- **Approval_Conditions:** Demonstrar insuficiência da arquitetura antes de criar qualquer estado novo.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-007, EDR-025
- **Source_Conversation_or_Document:** Prompt D3/6.1

### EDR-036 — Decisão C — IDs para camber e toe estáticos (referência e calculado)

- **Date:** 2026-10-10
- **Status:** AWAITING_DECISION
- **Context:** Camber/toe estáticos não têm ID; SUS-407/408 são curvas de MODEL.
- **Question:** Opção A (autorizar IDs distintos) ou B (documentar e adiar)?
- **Alternatives:** A: criar IDs agora. B: documentar a proposta e adiar para a revisão formal.
- **Decision:** PENDENTE. Recomendação preliminar do prompt: A, condicionada à resolução das inconsistências de D1.
- **Rationale:** Segue o padrão SUS-401/402 (um ID por fonte).
- **Evidence:** Faixas: SUS-4XX = Kinematics (REFERENCE + MODEL/CHECK); SUS-8XX = Setup (SUS-801 Setup definition). Nenhum ID existente cobre camber/toe estáticos. PROPOSTA (não criada): ver tabela abaixo.
- **Assumptions:** A faixa 4XX acomoda as grandezas como REFERENCE/INPUT (medidas/especificadas) e MODEL (calculadas dos hardpoints).
- **Consequences:** Se A: 4 IDs novos; atualizar Standard, Data Contract, Brief, rastreabilidade.
- **Affected_Artifacts:** Standard; Data Contract; Geometry Brief.
- **Affected_Tests:** —
- **Dependencies:** EDR-023, EDR-030
- **Approval_Conditions:** D1 resolvido; autorização explícita.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-023, EDR-030
- **Source_Conversation_or_Document:** Prompts D7/Decisão C

### EDR-037 — Escopo da implementação do pneu em 10_TIRE (V2.2)

- **Date:** 2026-10-12
- **Status:** IMPLEMENTED
- **Context:** Pedido do usuário: implementar na planilha tudo referente a tire, após receber um .tir TTC. Proposta de escopo apresentada (infraestrutura de entrada, fórmulas e guardas, verificação com dataset) e aceita ('execute as três propostas').
- **Question:** O que implementar sem dado real de pneu?
- **Alternatives:** Só estrutura vazia (N/A); lookup nível 1; avaliação paramétrica nível 2.
- **Decision:** 10_TIRE avalia Fx, Fy (puros e combinados) e μ_eff por canto (FL/FR/RL/RR + coluna VERIF) a partir dos coeficientes do .tir (nível 2, sem fit próprio; Mx/My/Mz, pressão e relaxamento fora). Fora da faixa do dataset ou com Fz≤0, saída N/A (sem extrapolar). Dataset inválido (IP≠IP_NOM, PP*≠0, faixas incoerentes) bloqueia tudo. A proposta inicial de nível 1 (lookup) foi substituída por nível 2 porque o dado recebido é paramétrico.
- **Rationale:** Guia: o workbook não apresenta μ próprio como medido; DR-011: sem fit próprio.
- **Evidence:** test_tire_model_V2_2.py 34/34 (limites analíticos, sinais, simetria, guardas, segunda transcrição independente em 800 pontos, sensibilidade a L*); teste de mutação 17/17 detectados (13 iniciais: 7 detectados; testes ampliados após o resultado); test_workbook_V2_2.py 15/15 (Excel recalculado == Python a ~4e-15 relativo em 25 pontos mais cenário com todos os coeficientes perturbados; faixas; dataset inválido; 88 fórmulas da V2.1 preservadas). Excel e Python reproduzem a MESMA transcrição das equações: isso não valida a física nem a origem das equações (H1).
- **Assumptions:** H1 equações PAC2002/MF 5.2 reproduzidas de memória do formato publicado, sem fonte primária (livro) consultada; na V2.3 foram verificadas contra duas implementações de terceiros (EDR-042); H2 pressão omitida; H3 convenção inferida; H4 espelhamento.
- **Consequences:** Validation = NOT_VALIDATED. Fichas SUS-501..503 do Standard ainda descrevem 'lookup ou paramétrico' e não registram a convenção nem o espelhamento (a atualizar).
- **Affected_Artifacts:** FSAE_EV_Suspension_Fase1_V2_2.xlsx (10_TIRE, 13_VALIDATION l.35-44, 14_DASHBOARD l.32-38, 04 DR-013, 01_SETUP, README, 15_CHANGELOG); tire_model_V2_2.py; data-contract-V2.2.
- **Affected_Tests:** TC-TIRE-001..009, TC-WB22-001..007
- **Dependencies:** EDR-015, EDR-038, EDR-039
- **Approval_Conditions:** Comparação com OptimumTire/TTC reais e implementação independente antes de qualquer promoção além de CHECKED interno.
- **Reopening_Criteria:** Dataset real; divergência contra OptimumTire; mudança de formato.
- **Related_Decisions:** EDR-015, EDR-038, EDR-039, EDR-040, EDR-041
- **Source_Conversation_or_Document:** Conversa Sistema_DDS (2026-10-12); DR-013

### EDR-038 — Dataset .tir TTC como dado PROVISÓRIO de desenvolvimento

- **Date:** 2026-10-12
- **Status:** APPROVED
- **Context:** Usuário forneceu um .tir (PAC2002, Hoosier R25B 13x7, TTC/Stackpole) 'apenas para possibilitar o andamento do desenvolvimento'; 'pode incluir na planilha, mas não necessariamente correspondem aos pneus que de fato serão utilizados'.
- **Question:** Como tratar o dataset?
- **Alternatives:** Não incluir; incluir sem rótulo.
- **Decision:** Incluído, rotulado PROVISÓRIO (T-REV-A) em 10_TIRE, 01_SETUP, dashboard e README. Metadados e hash do arquivo limpo em Hoosier_R25B_13x7_TTC_provisional.meta.json.
- **Rationale:** Declarado pelo usuário; EDR-022.
- **Evidence:** O arquivo chegou colado de chat (prefixos '[data] autor:' removidos; valores não alterados; o hash registrado é do arquivo limpo, não do original recebido). Proveniência declarada no cabeçalho do .tir (Stackpole, cliente TTC, 2020-10-13); não verificada.
- **Assumptions:** Os valores colados estão íntegros (nenhum campo omitido além dos grupos não importados).
- **Consequences:** Trocar o dataset exige nova Tire REV e reexecução de 13_VALIDATION (resultados antigos STALE).
- **Affected_Artifacts:** 10_TIRE; 01_SETUP B11; meta.json.
- **Affected_Tests:** TC-WB22-006
- **Dependencies:** EDR-022
- **Approval_Conditions:** —
- **Reopening_Criteria:** Dataset real do pneu escolhido.
- **Related_Decisions:** EDR-037, EDR-022
- **Source_Conversation_or_Document:** Mensagem do usuário (2026-10-12)

### EDR-039 — Sistema de eixos do arquivo de pneu (SAE→ISO), convenção de sinais e espelhamento esquerdo

- **Date:** 2026-10-12 (aberto); 2026-10-14 (decisão)
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** O .tir não declara o sistema de eixos. Em 2026-10-12 o usuário respondeu 'não tenho certeza'. Em 2026-10-14 informou que o TTC usa a convenção SAE e que o projeto usa ISO, e, perguntado se a implementação deveria ser alterada (declarar o sistema, transformar para ISO, corrigir textos), respondeu: 'Pode mudar porque sei que de fato existe essa convenção e os dados foram baixados diretamente do TTC'.
- **Question:** Qual o sistema de eixos do arquivo e como convertê-lo para a convenção do projeto (ISO 8855)?
- **Alternatives:** (a) só documentar; (b) transformação explícita com metadado obrigatório; (c) exigir confirmação documental antes de qualquer uso.
- **Decision:** (b). Sistema de eixos do arquivo = SAE_CALSPAN (declarado pelo usuário), campo obrigatório; ausente/UNKNOWN rejeita o dataset. Transformação para roda direita ISO: α_arquivo = −α_ISO; Fy_ISO = −Fy_arquivo; γ_arquivo = −γ_projeto; Fx e κ iguais. Espelhamento das rodas esquerdas aplicado antes (H4). Modo ISO_TYDEX = identidade. A afirmação 'compatível com ISO' das versões V2.2/V2.3 foi retirada.
- **Rationale:** A declaração vem de quem baixou os dados; torna a convenção explícita e testável, em vez de implícita.
- **Evidence:** (1) Declaração do usuário (base da decisão). (2) Fonte secundária: tese UNCC 2015 sobre dados TTC — α>0 corresponde a curva à esquerda, α>0 gera Fy<0 e Mz<0, Fz negativo no dado bruto; o .tir tem Fz positivo, logo foi processado (não se sabe se outros sinais também foram convertidos). (3) Resultado de código: entre SAE e ISO α e Fy trocam de sinal juntos, então a parte ímpar de Fy(α) é a mesma; mudam os termos assimétricos. Efeito medido (564 N, roda direita): Fy a α=4° vai de −1436 N (V2.2) para −1390 N (−3%); empuxo de camber a +3° de −141 N para −183 N (+30%); Fy em zero slip de +28 N para −28 N (inverte); Fx a α=4° de 49,5 N para 57,4 N. (4) tire_model_V2_4: 43/43 testes (invariantes físicos nos 4 cantos, empuxo de camber para o lado da inclinação, offset, parte ímpar invariante, loader); mutação 23/23; planilha V2.4 19/19.
- **Assumptions:** (i) O arquivo conserva a convenção SAE do dado bruto (declaração do usuário; não confirmada em documento do TTC). (ii) **Sinal de camber:** γ_arquivo = −γ_projeto é INFERÊNCIA (o empuxo de camber aponta para o lado da inclinação; os termos de camber do arquivo dão Fy_arquivo<0 para γ_arquivo>0). A definição de inclinação (IA) do TTC não foi verificada e, se contradisser a inferência, o efeito do camber inverte de sinal. (iii) Espelhamento (H4) é decisão de projeto provisória.
- **Consequences:** Valores de Fy, Fx e μ de 10_TIRE e do dashboard mudaram na V2.4. O resultado em Fy de rodas com camber ou deriva próximas de zero é o mais sensível.
- **Affected_Artifacts:** tire_model_V2_4.py; planilha V2.4 (10_TIRE m_axis, s_α, s_Fy, s_γ; 13_VALIDATION referência Python; 14_DASHBOARD; DR-013); data-contract-V2_4; Hoosier_R25B_13x7_TTC_provisional.meta.json.
- **Affected_Tests:** TC-TIRE-010a..i, TC-WB24-004c..f
- **Dependencies:** EDR-001, EDR-002, EDR-038, EDR-040
- **Approval_Conditions:** Confirmar a definição de IA e SA no documento do TTC e/ou comparar a grade tire_comparison_grid_V2_3.csv com o OptimumTire 2/Adams (sinais de Fy, Fx e Mz numa varredura de α, κ e γ) antes de FROZEN.
- **Reopening_Criteria:** Documento do TTC ou comparação contradizendo a transformação, em especial o sinal do camber.
- **Related_Decisions:** EDR-001, EDR-002, EDR-037, EDR-040, EDR-042
- **Source_Conversation_or_Document:** Conversa Sistema_DDS (2026-10-12 e 2026-10-14)

### EDR-040 — Formato do dataset de pneu (PAC2002 x MF 5.2 x 6.1.2 x 6.2) e origem (OptimumTire 2)

- **Date:** 2026-10-12
- **Status:** AWAITING_DECISION
- **Context:** Usuário: a forma de uso do pneu não está definida; OptimumTire 2 exporta .tir em PAC2002, MF 5.2, MF 6.1.2 e MF 6.2; a extensão .tir não garante compatibilidade matemática nem de sinais.
- **Question:** Qual formato será a referência do projeto?
- **Alternatives:** (a) PAC2002/MF 5.2 (suportado hoje); (b) MF 6.1.2/6.2 (exige novas equações e parâmetros — não implementadas); (c) lookup (nível 1) de curvas exportadas.
- **Decision:** PENDENTE. O loader aceita apenas PAC2002/MF 5.2-like e rejeita os demais (TC-TIRE-008f), inclusive FITTYP/MF_62.
- **Rationale:** Não implementar MF 6.x sem equações verificadas e sem escolha do usuário.
- **Evidence:** Informação do usuário sobre o OptimumTire 2; MF-Tyre 6.2 (TNO) citado pelo usuário como referência de convenções, não consultada diretamente.
- **Assumptions:** —
- **Consequences:** Trocar de formato implica nova avaliação de equações, novo schema e testes.
- **Affected_Artifacts:** tire_model_V2_2.py (load_dataset); 10_TIRE; Data Contract §7.
- **Affected_Tests:** TC-TIRE-008f
- **Dependencies:** EDR-015
- **Approval_Conditions:** Escolha do formato e dataset real.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-015, EDR-037, EDR-039
- **Source_Conversation_or_Document:** Mensagem do usuário (2026-10-12)

### EDR-041 — Entradas α/γ/κ demonstrativas e N/A como estado de saída sem dado

- **Date:** 2026-10-12
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** Não há modelo de slip nem de camber estático aprovado; EDR-035 (N/A/TBD) e EDR-036 (IDs de camber) estão sem decisão. Pergunta ao usuário sobre depender dessas decisões: 'por enquanto sim'.
- **Question:** Como alimentar α, γ, κ e como representar a ausência de dado?
- **Alternatives:** Deixar vazio (tudo N/A); valores demonstrativos.
- **Decision:** Valores demonstrativos arbitrários (célula azul, fundo amarelo, comentário), com sinal coerente com 08_VEHICLE_STATE; saídas 'N/A' quando faltar entrada ou sair da faixa. Camber de entrada manual (sem ID, aguardando EDR-036).
- **Rationale:** EDR-022 (valores de teste identificados como tais); permite exercitar a planilha.
- **Evidence:** TC-WB22-005c (entrada ausente → N/A sem erro).
- **Assumptions:** O Fz de 09_LOADS usado nas colunas FL..RR é ele próprio placeholder (EDR-025); FR do caso demonstrativo está a ~5% de FZMAX.
- **Consequences:** Os μ_eff do dashboard são demonstrativos e dependem de placeholders.
- **Affected_Artifacts:** 10_TIRE; 14_DASHBOARD.
- **Affected_Tests:** TC-WB22-005
- **Dependencies:** EDR-025, EDR-035, EDR-036
- **Approval_Conditions:** Substituir por casos de carga reais e por modelo de slip quando existirem; revisar quando EDR-035/036 forem decididos.
- **Reopening_Criteria:** Decisão de EDR-025/035/036.
- **Related_Decisions:** EDR-022, EDR-025, EDR-035, EDR-036
- **Source_Conversation_or_Document:** Conversa Sistema_DDS (2026-10-12)

### EDR-042 — Verificação das equações do pneu contra fontes de terceiros; caminho até a fonte primária

- **Date:** 2026-10-13
- **Status:** VERIFIED
- **Context:** O usuário pediu encontrar fonte primária e validar as equações usadas (H1 do EDR-037: equações reproduzidas de memória).
- **Question:** As equações implementadas coincidem com fontes publicadas?
- **Alternatives:** Aguardar o livro; usar implementações de terceiros como oráculo; comparar com o OptimumTire 2.
- **Decision:** Executada a verificação possível no ambiente: transcrição de (A) `RPacejka::CalcMF52()` do Racer v0.8.9 (código publicado, www.racer.nl/reference/pacejka.htm) e (B) ramo MF 5.2 do MFeval (port Julia matheusft/MFeval_julia, MIT, que cita Pacejka 2012 eqs. 4.E9–4.E67), comparadas ao módulo em 3000 pontos aleatórios no .tir provisório. Fonte primária (Pacejka, *Tyre and Vehicle Dynamics*, 2ª/3ª ed.; documentação TNO MF-Tyre 5.2 / Adams PAC2002) NÃO consultada diretamente: livro pago; relatório DTIC ADA535124 bloqueado no acesso.
- **Rationale:** Duas implementações de terceiros, escritas sem relação com o meu código, são o oráculo independente disponível; reduzem o risco de erro de transcrição, não o de erro comum de origem.
- **Evidence:** test_tire_oracles_V2_2.py 5/5 (resultado de código): dif máx 3,4e-7 N vs Racer e 3,4e-4 N vs MFeval (ε diferente, 1e-3); os oráculos concordam entre si (3,4e-4 N). Trechos do livro (3ª ed.) vistos via ScienceDirect Topics para combinação (4.E54–4.E57, 4.E64–4.E66) coincidem com as fórmulas de Gxα, Gyκ e SVyκ. Divergências ENTRE as fontes, só visíveis com L*≠1 (o .tir tem L*=1): (i) Racer aplica um fator LFZO extra em Ky; MFeval não — o módulo segue o Racer (dif 111 N com LFZO=1,1 contra o MFeval); (ii) Racer aplica LGAX/LGAY ao camber; MFeval não — o módulo segue o Racer. Não implementados (irrelevantes aqui): condições Bxα>0 e Gxα>0 citadas no livro; limitador de Exα no Racer não existe, no MFeval existe (o módulo limita).
- **Assumptions:** As transcrições dos oráculos foram feitas por mim a partir do código exibido; viés de transcrição não pode ser excluído. 'MFeval' aqui = o port Julia, não o MATLAB original (não obtido).
- **Consequences:** Validation continua NOT_VALIDATED: comparação com código não é medição. Grade para comparar com o OptimumTire 2/Adams: tire_comparison_grid_V2_3.csv (resultado de código, 75 pontos).
- **Affected_Artifacts:** test_tire_oracles_V2_2.py; planilha V2.3 (10_TIRE metadado, DR-013, 13_VALIDATION l.44, README, changelog); tire_comparison_grid_V2_3.csv.
- **Affected_Tests:** TC-TIRE-ORC-001..005
- **Dependencies:** EDR-037, EDR-039, EDR-040
- **Approval_Conditions:** Promoção além de CHECKED interno só com: (a) conferência no livro (Appendix de MF 5.2), (b) comparação com OptimumTire 2/Adams usando a grade CSV, (c) para LFZO/LGAX/LGAY≠1, decisão da fonte de referência.
- **Reopening_Criteria:** Divergência na comparação com OptimumTire/Adams; acesso à fonte primária contradizendo as fontes de terceiros.
- **Related_Decisions:** EDR-037, EDR-039, EDR-040
- **Source_Conversation_or_Document:** Conversa Sistema_DDS (2026-10-13)

## 6. Tabela de rastreabilidade

| Decisão | Parâmetros / requisitos | Artefatos afetados | Testes |
|---|---|---|---|
| EDR-001 | SUS-000, SUS-401..406 | arquitetura §4/§17.1; Standard; Data Contract; hardpoints_V2_0.py (lotus_to_iso8855); planilha 00_README. | TC-HP-010, TC-HP-011a/b, TC-HP-101a-e |
| EDR-002 | SUS-404, SUS-405, SUS-407, SUS-408 | arquitetura §17.2; Standard SUS-404/405/407/408; kinematics_model_V2_0.py. | TC-KIN-106a, TC-KIN-106b |
| EDR-003 | SUS-201, SUS-202, SUS-409 | Standard SUS-201/202/409; suspension_model; planilha 06_SUSPENSION. | TC-009, TC-SUS-V21-001..005 |
| EDR-004 | SUS-401..406 | Todos. | — |
| EDR-005 | todos | arquitetura; Standard; Data Contract; planilha. | — |
| EDR-006 | todos | arquitetura; Standard. | — |
| EDR-007 | todos | arquitetura; Standard; Data Contract §2.1. | — |
| EDR-008 | — | Data Contract; hardpoints_V2_0.py; planilha. | TC-HP-003 |
| EDR-009 | SUS-103, SUS-401 | Standard SUS-103/401/402; planilha 06_SUSPENSION. | TC-007 |
| EDR-010 | SUS-102, SUS-301, SUS-302 | Standard SUS-102/301/302. | TC-002, TC-003 |
| EDR-011 | SUS-103, SUS-104 | Standard SUS-103; suspension_model; planilha 09_LOADS. | TC-001, TC-005..008 |
| EDR-012 | SUS-201, SUS-203, SUS-206, SUS-207, SUS-401 | planilha 06_SUSPENSION; mapa de dependências. | — |
| EDR-013 | SUS-701, SUS-702 | Standard SUS-701/702. | TC-004 |
| EDR-014 | SUS-202, SUS-205, SUS-208 | Standard SUS-202/205/208; planilha 11_DESIGN. | TC-010 |
| EDR-015 | SUS-501..503 | Standard; planilha 10_TIRE. | — |
| EDR-016 | — | arquitetura; Standard; Data Contract; testes. | todos |
| EDR-017 | — | Todos. | — |
| EDR-018 | — | planilha 04_DECISION_REGISTER; registro de versões. | — |
| EDR-019 | — | Guide (fora de escopo). | — |
| EDR-020 | SUS-407..413 | kinematics_model_V2_0.py; Standard V2.0 Bloco E.2; planilha 07_KINEMATICS/04. | TC-KIN-001..006, 101..117 |
| EDR-021 | SUS-104, SUS-001..005, SUS-702 | suspension_model_V2_0.py (V2_1 mantém); Data Contract §5. | TC-SUS-V2-001..004 |
| EDR-022 | — | testes; hardpoints sintéticos. | — |
| EDR-023 | SUS-407..413 | Standard V2.0 Bloco E.2; arquitetura adendo; Data Contract §6; Geometry Brief; testes. | TC-KIN-101..117 |
| EDR-024 | hardpoints.csv/.meta.json | hardpoint-schema; hardpoints_V2_0.py; Data Contract §6. | TC-HP-001..018, TC-HP-101..104 |
| EDR-025 | SUS-205, SUS-301, SUS-302, SUS-104, REQ-004 | planilha 06, 09, 11, 13, 14; testes de planilha. | TC-WB-xxx (a criar após decisão) |
| EDR-026 | SUS-301, SUS-302, SUS-406, SUS-412 | Standard SUS-301/302/406; kinematics_model; Data Contract; planilha 06/07. | TC-KIN-110, TC-KIN-118 |
| EDR-027 | SUS-201, SUS-202, SUS-409 | suspension_model_V2_1.py; Standard; Data Contract. | TC-SUS-V2-002, TC-SUS-V21-001..005 |
| EDR-028 | SUS-406, SUS-412 | Standard SUS-406/412; kinematics_model; documento exploratório. | TC-KIN-107, 110, 111, 114 |
| EDR-029 | SUS-401, SUS-402, SUS-412 | Standard SUS-401/402/412; documento exploratório. | TC-KIN-107b, 113 |
| EDR-030 | camber/toe estáticos; SUS-407, SUS-408 | hardpoint-schema-V2.1; Standard V2.1 (SUS-407); Data Contract; Geometry Brief. | TC-HP-104a-d |
| EDR-031 | REQ-001, REQ-002, REQ-003, SUS-003, SUS-004, SUS-005 | planilha V2.1 13_VALIDATION, 15_CHANGELOG. | TC-WB-001..005 |
| EDR-032 | REQ-001..006, TARGET-001..005 | geometry-brief-V2.1.md; (futuro) planilha. | Verificação estrutural manual |
| EDR-033 | SUS-013, SUS-014, SUS-301, SUS-302 | Standard SUS-301/302/013/014 (futuro). | — |
| EDR-034 | — | documento exploratório; Standard. | — |
| EDR-035 | — | Standard; Data Contract; planilha. | TC-WB-004a/b |
| EDR-036 | SUS-4XX proposto | Standard; Data Contract; Geometry Brief. | — |
| EDR-037 | SUS-501, SUS-502, SUS-503 | planilha V2.2 (10_TIRE, 13, 14, 04, 01, 00, 15); tire_model_V2_2.py. | TC-TIRE-001..009, TC-WB22-001..007 |
| EDR-038 | SUS-501..503 | 10_TIRE; 01_SETUP B11; meta.json. | TC-WB22-006 |
| EDR-039 | SUS-501, SUS-502, SUS-404 | 10_TIRE; tire_model_V2_4.py; data-contract-V2_4; Standard (a atualizar). | TC-TIRE-004/005/010, TC-WB22-007, TC-WB24-004c..f |
| EDR-040 | SUS-501..503 | tire_model_V2_2.py; Data Contract §7. | TC-TIRE-008f |
| EDR-041 | SUS-501, SUS-502 | 10_TIRE; 14_DASHBOARD. | TC-WB22-005 |
| EDR-042 | SUS-501, SUS-502 | test_tire_oracles_V2_2.py; planilha V2.3; grade CSV. | TC-TIRE-ORC-001..005 |

## 7. Mapa EDR ↔ DR (planilha) ↔ DEC (arquitetura)

| EDR | DR (planilha) | DEC citado na arquitetura |
|---|---|---|
| EDR-001, 002 | DR-001 | DEC-001 |
| EDR-003 | DR-002 | — |
| EDR-004 | — | DEC-002, DEC-003 |
| EDR-005, 006, 007 | — | DEC-010 (estados) |
| EDR-008 | DR-008 | DEC-015, DEC-016 |
| EDR-009 | DR-005 | DEC-006 |
| EDR-010 | DR-006 | — |
| EDR-011 | DR-003 | — |
| EDR-012 | DR-004 | — |
| EDR-013 | DR-007 | — |
| EDR-014 | DR-010 | — |
| EDR-015 | DR-011 | DEC-007 |
| EDR-020 | DR-009, DR-012 | DEC-003 |
| EDR-037..041 | DR-013 (EDR-037); DR-011 (contexto) | DEC-007 (nível 1 ou 2) |
