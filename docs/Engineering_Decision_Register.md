# Engineering Decision Register — Sistema_DDS (Tupã Suspension System)

**Versão do registro:** V2.4-PARCIAL (2026-10-14; EDR-043 acrescentado, implementado e VERIFIED, EDR-017 substituído e EDR-044 acrescentado e VERIFIED, em 2026-10-19; EDR-045 a EDR-049 acrescentados e EDR-026 aprovado com a revisão metodológica, em 2026-10-19; EDR-025 e EDR-035 decididos e EDR-050 e EDR-051 acrescentados na 2ª rodada da V3.0, em 2026-10-19). **Estado do documento:** em construção; mantido a cada decisão relevante.
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

Total: 44 registros. APPROVED: 18 · APPROVED_WITH_CONDITIONS: 5 · AWAITING_DECISION: 9 · IMPLEMENTED: 4 · PENDING_CONFIRMATION: 2 · SUPERSEDED: 1 · VERIFIED: 5

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
| EDR-017 | Regra de versionamento dos artefatos | SUPERSEDED (por EDR-043) |
| EDR-018 | Consolidação do Decision Register da planilha (versão mais completa) | PENDING_CONFIRMATION |
| EDR-019 | Tratamento do Guide, de valores de teste e foco | APPROVED |
| EDR-020 | Solver cinemático 3D como MODEL/cross-check (Kinematics V2) | IMPLEMENTED |
| EDR-021 | Aviso de Fz<0 e validações de entrada no Python | VERIFIED |
| EDR-022 | Valores de teste e demonstrativos sem rastreabilidade obrigatória | APPROVED |
| EDR-023 | D1 — Identificadores SUS-407 a SUS-413 | AWAITING_DECISION |
| EDR-024 | D2 — Schema de hardpoints V2.0 | AWAITING_DECISION |
| EDR-025 | D3 / Decisão A — Tratamento de placeholders na planilha | VERIFIED |
| EDR-026 | D4 — Convenção de sinal de AD/AS (positivo = anti; negativo = pro; zero = sem efeito líquido) | APPROVED_WITH_CONDITIONS |
| EDR-027 | D4-MR / D6 / Decisão B — Limiar absoluto de MR e cross-check | AWAITING_DECISION |
| EDR-028 | D5 — IC lateral: funcionalidade exploratória | APPROVED_WITH_CONDITIONS |
| EDR-029 | D8 — Roll Center: funcionalidade exploratória e procedimento de validação | APPROVED_WITH_CONDITIONS |
| EDR-030 | D7 — Camber/toe estáticos: referência x calculado; sem distância mínima universal | APPROVED_WITH_CONDITIONS |
| EDR-031 | REQ-001/REQ-002 e proveniência do REQ-003 em 13_VALIDATION | VERIFIED |
| EDR-032 | Geometry Brief — estrutura de interface especificação→CAD | IMPLEMENTED |
| EDR-033 | Escopo de AD/AS e anti-lift (frenagem regenerativa) | AWAITING_DECISION |
| EDR-034 | Critérios de promoção DRAFT/CHECKED/FROZEN/STALE | AWAITING_DECISION |
| EDR-035 | Semântica de N/A e TBD (e proveniência de dados) | APPROVED_WITH_CONDITIONS |
| EDR-036 | Decisão C — IDs para camber e toe estáticos (referência e calculado) | AWAITING_DECISION |
| EDR-037 | Escopo da implementação do pneu em 10_TIRE (V2.2) | IMPLEMENTED |
| EDR-038 | Dataset .tir TTC como dado PROVISÓRIO de desenvolvimento | APPROVED |
| EDR-039 | Sistema de eixos do arquivo de pneu (SAE→ISO), convenção de sinais e espelhamento esquerdo | APPROVED_WITH_CONDITIONS |
| EDR-040 | Formato do dataset de pneu (PAC2002 x MF 5.2 x 6.1.2 x 6.2) e origem (OptimumTire 2) | AWAITING_DECISION |
| EDR-041 | Entradas α/γ/κ demonstrativas e N/A como estado de saída sem dado | APPROVED_WITH_CONDITIONS |
| EDR-042 | Verificação das equações do pneu contra fontes de terceiros; caminho até a fonte primária | VERIFIED |
| EDR-043 | Versionamento por Git e nomes estáveis (substitui o EDR-017) | VERIFIED |
| EDR-044 | Recálculo da planilha no teste via Excel (COM), com LibreOffice como alternativa | VERIFIED |
| EDR-045 | Pneu em série na frequência natural e na rigidez de rolagem (novos SUS-211 e SUS-212) | VERIFIED |
| EDR-046 | Termo gravitacional da rolagem na transferência lateral (SUS-103) | VERIFIED |
| EDR-047 | Massa suspensa por eixo exata e CG suspenso em a_s | VERIFIED |
| EDR-048 | Anti-dive/anti-squat: IC lateral pelo movimento, forma com sinal e ponto de reação do carro | VERIFIED |
| EDR-049 | Ky com um único λFz0 | VERIFIED |
| EDR-050 | Valor derivado entra como fórmula, não digitado | VERIFIED |
| EDR-051 | Fonte de verdade da planilha: gerada durante o desenvolvimento, viva depois de fechada a V3.0 | APPROVED_WITH_CONDITIONS |

## 3. Decisões que dependem do usuário (agora)

- **EDR-018** (PENDING_CONFIRMATION): Consolidação do Decision Register da planilha (versão mais completa)
- **EDR-023** (AWAITING_DECISION): D1 — Identificadores SUS-407 a SUS-413
- **EDR-024** (AWAITING_DECISION): D2 — Schema de hardpoints V2.0
- **EDR-025** (AWAITING_DECISION): D3 / Decisão A — Tratamento de placeholders na planilha
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
- **Status:** SUPERSEDED (por EDR-043, 2026-10-19)
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
- **Related_Decisions:** Substituído pelo EDR-043 (versionamento por Git e nomes estáveis; a planilha mantém a versão no nome).
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

- **Date:** 2026-10-10 (decisão em 2026-10-19)
- **Status:** VERIFIED
- **Context:** Planilha mostra números dependentes de dados não reais.
- **Question:** Opção A (marcar, manter fórmulas) ou B (proteger só células terminais)?
- **Alternatives:** A: proveniência visível + fórmulas intactas. B: guardar terminais com IF(origem válida; cálculo; 'N/A'). B': B com sensibilidade quantificada por saída.
- **Decision:** **A** (usuário, 2026-10-19, 2ª rodada da V3.0): proveniência visível em cada entrada, fórmulas intactas; nenhuma fórmula terminal ganha IF de proteção. A forma da proveniência está no EDR-035. Histórico: a recomendação preliminar do prompt era B com proteção seletiva; a do assistente, B' (ver Evidence). B e B' ficam rejeitadas por ora: escondem números que a equipe usa para comparar e mudam fórmulas terminais.
- **Rationale:** Mapa auditável confirma 45/84 fórmulas dependentes de dado que não é do veículo.
- **Evidence:** Implementação da opção A na V3.0 (2ª rodada): TC-WB30-010 a 012 PASS, pelo Excel via COM e pelo LibreOffice; nenhuma fórmula terminal alterada (CA-07). Auditoria anterior: placeholder-dependency-map-V2.1.csv: 45 fórmulas com raiz T1 (placeholder, arbitrário, estimativa ou alvo demonstrativo); 23 só com T2 (dado de outro veículo/hipótese/caso de carga sem proveniência); 16 só com T3. Das 45: 22 intermediárias, 17 terminais e 6 verificações de identidade/espelhos (TC-004/005 e λ). REQ-004 (13_VALIDATION B21/B22; dashboard B23/B24) retorna PASS a partir dos placeholders de curso 60/65 mm (07_KINEMATICS B31/B32). Anti-dive/squat (06_SUSPENSION B40/B41) dependem totalmente de placeholders. Sensibilidade (Python com os valores da planilha): trocar a massa não-suspensa arbitrária (15/18 kg) por 0 ou 2× altera Fz em ≤ 2,3 N (0,2%) e a frequência natural em 5,4% a 6,4%. Proteger o Fz por mera ascendência esconderia um dado quase insensível; a frequência é sensível. Proveniência existe nos 35 comentários de célula (não é legível por máquina nem visível sem passar o mouse).
- **Assumptions:** Classificação T1/T2/T3 baseada em comentários e preenchimentos; as massas não-suspensas são ARBITRÁRIAS segundo o comentário de 05_VEHICLE B14/B15.
- **Consequences:** B exige alterar fórmulas terminais (lista a registrar por célula: aba, célula, fórmula anterior/nova, dependências, justificativa, teste). Verificações de identidade (TC-004/005) permanecem intactas.
- **Affected_Artifacts:** planilha 06, 09, 11, 13, 14; testes de planilha.
- **Affected_Tests:** TC-WB30-010 a TC-WB30-012 (origem visível; ver EDR-035)
- **Dependencies:** EDR-022, EDR-035
- **Approval_Conditions:** — (a regra de elegibilidade só seria necessária para B/B').
- **Reopening_Criteria:** Novos dados reais substituindo placeholders.
- **Related_Decisions:** EDR-022, EDR-035
- **Source_Conversation_or_Document:** Prompt D3/Decisão A; auditoria V2.1; decisão do usuário na 2ª rodada da V3.0 (2026-10-19), a partir de feedback da equipe (2026-10-14) e de consulta a um conselho de quatro lentes.

### EDR-026 — D4 — Convenção de sinal de AD/AS (positivo = anti; negativo = pro; zero = sem efeito líquido)

- **Date:** 2026-10-10 (aprovado em 2026-10-19)
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** Forma V1 usa |d| e assume tan φ ≥ 0.
- **Question:** Adotar convenção de saída?
- **Alternatives:** Manter forma V1.
- **Decision:** Até 2026-10-18: o usuário instruiu 'Adote' num prompt e chamou de 'proposta' no seguinte, e a decisão não era determinável. Em 2026-10-19 o usuário autorizou todas as propostas da revisão metodológica que seguem a literatura, entre elas a forma com sinal (P-05/P-07); a Milliken p. 620 trata o "anti" negativo como pro-dive/squat/lift. Convenção adotada (EDR-048). A aprovação da convenção não valida o método geométrico.
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

- **Date:** 2026-10-10 (parte de proveniência decidida em 2026-10-19)
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** N/A e TBD não são estados oficiais (arquitetura §3). Na 2ª rodada da V3.0, feedback da equipe (2026-10-14): quem preenche a planilha não consegue distinguir o que é dado firme do que é estimado, nem de onde veio cada valor, e quer isso na própria planilha, sem documento separado.
- **Question:** Como formalizar sem criar dimensão nova?
- **Alternatives:** Nova dimensão 'estado do dado'; usar metadados existentes.
- **Decision:** **Proveniência (aprovada pelo usuário em 2026-10-19):** pelo metadado Provenance da arquitetura §3, sem estado novo, visível em cada linha de entrada da planilha: coluna E "Origem" (lista suspensa) e coluna F "Fonte" (texto); na 10_TIRE, colunas H e I. Rótulos (usuário, 2026-10-19: "Hipótese" e "Estimativa" se fundem; "Dado do T09" no lugar de "Outro carro"), com símbolo para leitura em P&B e por daltônicos: `● Dado do TX` (medido ou documento do TX/E05; tier T3 da auditoria V2.1), `◐ Dado do T09` (T09/E03; T2), `◐ Provisório (.tir TTC)` (T2), `○ Estimativa` (inclui hipótese de modelo e caso de carga sem fonte; T1 = a pior das categorias fundidas), `○ Arbitrário / demonstrativo` (arbitrário, placeholder, alvo demonstrativo; T1), `? A confirmar` (sem origem registrada; nunca preenchido por inferência). A cor da origem fica só na coluna E (formatação condicional), separada do código de papel da célula (fonte azul = entrada etc.); o fundo amarelo "hipótese-chave" sai da planilha (usuário, 2026-10-19). Aviso sem macro: o gerador grava em colunas ocultas G/H o valor e a origem com que gerou cada linha; a formatação condicional marca "valor mudou e a origem não" e "Dado do TX sem fonte". Resultado com selo estático de pior origem não é usado (fica velho em silêncio); pior origem viva nos resultados principais fica para uma fase 2, com aprovação. **N/A e TBD:** continua a proposta original, sem decisão: N/A = não aplicável/não calculável na configuração atual; TBD = dado, requisito ou decisão pendente (equivale a Lifecycle OPEN para parâmetros).
- **Rationale:** O comentário de célula só aparece ao passar o mouse e não sai na impressão (EDR-025). Uma coluna de origem ao lado do valor resolve o pedido "abrir a planilha e já estar lá" e é editável sem Python. O vocabulário curto é para quem preenche; o mapeamento para as categorias da auditoria V2.1 mantém a rastreabilidade. Conselho de quatro lentes (2026-10-19; veredito na conversa): o modo de falha dominante é o rótulo que fica velho quando o valor muda, daí o aviso.
- **Evidence:** Parte de proveniência implementada e verificada: TC-WB30-010 (toda entrada com Origem e Fonte; origens iguais às categorias da auditoria V2.1), 011 (lista `Origens`, sem fundo amarelo, legenda), 012 (cores e avisos; semântica avaliada pelo motor de recálculo); conferência no Excel por COM (lista `=Origens` e cores exibidas). Histórico: N/A e TBD já existiam na V1.0 (8 N/A, 10 TBD, ex.: 03_TARGETS); na V2.0 há 34 N/A, dos quais 26 foram adicionados pelo assistente no bloco de resultados do solver. CORRIGE afirmação anterior de que seriam prática estabelecida em 34 células.
- **Assumptions:** —
- **Consequences:** Usados em campos do Geometry Brief e de 07_KINEMATICS.
- **Affected_Artifacts:** Standard; Data Contract; planilha.
- **Affected_Tests:** TC-WB-004a/b; TC-WB30-010 a TC-WB30-012
- **Dependencies:** EDR-007, EDR-025
- **Approval_Conditions:** Demonstrar insuficiência da arquitetura antes de criar qualquer estado novo. Aprovada só a parte de proveniência; a semântica de N/A e TBD continua sem decisão.
- **Reopening_Criteria:** —
- **Related_Decisions:** EDR-007, EDR-025, EDR-051
- **Source_Conversation_or_Document:** Prompt D3/6.1; feedback da equipe (2026-10-14) e decisão do usuário (2026-10-19), 2ª rodada da V3.0

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

### EDR-043 — Versionamento por Git e nomes estáveis (substitui o EDR-017)

- **Date:** 2026-10-19 (proposta em 2026-10-18)
- **Status:** VERIFIED
- **Context:** O EDR-017 versiona pelo nome do arquivo (`tire_model_V2_4.py`, `test_suspension_model_V2_1.py`) e nunca sobrescreve os históricos. Com o projeto no Git (repositório privado ViniciusFCC/Sistema_DDS, tag `v2.4.1`), isso gera três problemas: (1) toda versão nova exige mudar os imports de todos os scripts que usam o módulo; (2) teste e módulo têm versões diferentes no nome (`test_kinematics_model_V2_1.py` testa `kinematics_model_V2_0.py`), como o próprio EDR-017 previa em Consequences; (3) o histórico passa a existir em dobro, no nome e no Git. A fase A da migração provou a reprodução com os nomes originais, o que torna a renomeação verificável.
- **Question:** Como versionar código, testes, dados e planilha a partir da V2.4.1?
- **Alternatives:** (a) manter o EDR-017 (versão no nome de tudo); (b) híbrido: Git com tags para código, testes, dados e docs, com nomes estáveis, e a planilha entregue mantendo a versão no nome; (c) Git para tudo, inclusive a planilha com nome estável.
- **Decision:** (b). (1) Código e testes sem versão no nome: `tire_model.py`, `suspension_model.py`, `kinematics_model.py`, `hardpoints.py`, `build_workbook.py`, `mutation_tire.py`, e os testes em `tests/` (`test_tire_model.py`, `test_tire_oracles.py`, `test_suspension_model.py`, `test_kinematics_model.py`, `test_hardpoints.py`, `test_workbook.py`). (2) Os arquivos de dados mantêm o sufixo `_V2.0` (`hardpoints_synthetic_V2.0.csv` e `.meta.json`), porque ali ele é a versão do schema de hardpoints (EDR-024), e não a revisão do arquivo. (3) A planilha continua `FSAE_EV_Suspension_Fase1_V2_x.xlsx`; a versão gravada dentro dela tem aprovação própria (SPEC §11, passo 3). (4) Versão do projeto: tag Git anotada `vX.Y.Z` a cada entrega; `X.Y` acompanha a versão da planilha (V2.4 → `v2.4.z`) e `Z` sobe em mudanças sem efeito na planilha; o decimal continua subindo a cada pequena implementação, como no EDR-017. (5) Históricos: "nunca sobrescrever" passa a ser garantido pelas tags do Git, por `importado-claude-ai/` (somente leitura) e pelo backup na OneDrive; a referência V1.0 do `TC-SUS-V2-004` fica congelada em `tests/regressao/suspension_model_V1_0.py`, com o nome original. (6) Os testes em `tests/` acham os módulos de `python/` porque o `uv sync` instala o projeto em modo editável, com `python/` no caminho de import (configuração do `pyproject.toml`).
- **Rationale:** Nomes estáveis acabam com a mudança de imports a cada versão e com o descompasso entre teste e módulo. O Git guarda o histórico com hash e data, em vez de cópias. A planilha fica fora da regra porque circula fora do Git. Os dados mantêm o sufixo porque ele identifica o schema.
- **Evidence:** Fase A da migração: CA-01 a CA-12 e tag `v2.4.1` (`docs/migracao/verificacao-V2.4-local.md`). Proposta: `docs/migracao/proposta-EDR-043.md`. Veredito do conselho (D1), registrado no SPEC §3. Implementação (PR #1, branch `refactor/nomes-estaveis`): mesmo resultado da fase A, registrado em `docs/migracao/verificacao-EDR-043-nomes-estaveis.md`, gerado numa árvore sem mudanças pendentes; revisão com o pr-review-toolkit.
- **Assumptions:** H1: a equipe não depende dos nomes `_V2_x` dos `.py` fora deste repositório (não verificado). H2: a confirmação do "V2", ausente no EDR-017, passa a valer com esta decisão.
- **Consequences:** A renomeação é um commit próprio de reestruturação: nos scripts de engenharia, ele só move arquivos e ajusta imports e caminhos; além disso, o `pyproject.toml` passa a instalar o projeto em modo editável e as ferramentas de `tools/` seguem os caminhos novos. Nenhuma equação muda, e os testes precisam dar o mesmo resultado da fase A (43, 5, 42, 53, 35; mutação 23/23; planilha com 347 fórmulas e 0 diferença). O `MANIFEST.sha256` continua valendo para a cópia fiel (conferida no blob do commit que adicionou cada arquivo). Os docstrings antigos e os textos gravados nas células da planilha por `build_workbook.py` mantêm os nomes `_V2_x` de propósito: mudar esses textos altera a planilha gerada e quebra a igualdade com a V2.4 entregue (CA-07).
- **Affected_Artifacts:** `python/*.py`; testes (para `tests/`); dados lidos pelos testes (para `data/`); `tools/rodar_testes.py`; `tools/comparar_planilhas.py`; `tools/verificar_manifest.py`; `pyproject.toml`; `uv.lock`; `CLAUDE.md`; `python/README.md`; SPEC.
- **Affected_Tests:** Todos os da fase A; o critério é o mesmo resultado.
- **Dependencies:** EDR-017; EDR-024; SPEC D1 e E1.
- **Approval_Conditions:** —
- **Reopening_Criteria:** A equipe precisar dos `.py` versionados fora do Git; qualquer diferença de resultado depois da renomeação (vale o processo de divergência, §2.6 do handoff).
- **Related_Decisions:** Substitui o EDR-017 (SUPERSEDED).
- **Source_Conversation_or_Document:** Usuário (instrução na conversa, 2026-10-19: "Autorizo o EDR-043 com a regra híbrida e as três recomendações"); SPEC §3 e §11.

### EDR-044 — Recálculo da planilha no teste via Excel (COM), com LibreOffice como alternativa

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** O `test_workbook` (19 testes Excel × Python da planilha) recalcula cópias da planilha com o `recalc.py` da skill xlsx, que roda o LibreOffice em `/mnt/skills` (sandbox do claude.ai). Nesta máquina ele não roda (SPEC D2) e ficou NÃO EXECUTÁVEL na fase A. O EDR-008 proíbe xlwings/PyXLL/macros como ponte Excel–Python e o CLAUDE.md exige EDR próprio para qualquer uso em teste.
- **Question:** Que motor recalcula a planilha no teste?
- **Alternatives:** (a) só Excel via COM (pywin32); (b) só LibreOffice (headless, mesma macro do `recalc.py`); (c) Excel quando houver, LibreOffice quando não houver; (d) não integrar.
- **Decision:** (c). O teste usa o Excel via COM (instância própria e invisível, `CalculateFull` + `Save`, sempre em cópias) quando o Excel e o `pywin32` existem; senão, o LibreOffice headless com a macro `calculateAll()` + `store()`. A variável `DDS_RECALC=excel|libreoffice` força um motor. O log registra qual motor rodou. O `pywin32` é dependência só de desenvolvimento e só no Windows. Sem nenhum motor, o teste sai como NÃO EXECUTÁVEL (nunca como aprovado).
- **Rationale:** O Excel é o programa da equipe e é ~7 vezes mais rápido; o LibreOffice mantém o teste executável fora do Windows e é o motor do resultado original. Os dois dão o mesmo resultado (experimento).
- **Evidence:** `docs/migracao/experimento-recalculo-libreoffice-x-excel.md`: `test_workbook` 19/19 com os dois motores, reproduzindo o 19/19 do sandbox (`registro-de-versoes-V2_4.md:17`); nas 347 fórmulas, diferença relativa máxima LibreOffice × Excel de 4,0e-15 e textos idênticos; 0,9 s (Excel) contra 6,3 s (LibreOffice) por recálculo. Implementação (PR #4): `test_workbook` 19/19 pelo Excel no `tools/rodar_testes.py` (`docs/migracao/verificacao-EDR-044-planilha.md`, árvore sem mudanças pendentes) e 19/19 com `DDS_RECALC=libreoffice`; `DDS_RECALC` inválido dá FAIL.
- **Assumptions:** H1: o comportamento numérico do Excel do Office 16 e do LibreOffice 26.8 vale para as versões que a equipe usa (não verificado em outras versões). H2: a mesma macro do `recalc.py` equivale ao arquivo usado no sandbox em 2026-10-14 (o arquivo exato não foi obtido).
- **Consequences:** Não altera o EDR-008: a planilha entregue continua sem ponte automática; o COM só abre cópias temporárias dentro do teste. Nenhum check, tolerância ou fórmula muda. O CA-09 deixa de ser NÃO EXECUTÁVEL quando há motor.
- **Affected_Artifacts:** `tests/test_workbook.py`; `tests/recalculo_planilha.py`; `pyproject.toml`; `uv.lock`; `tools/rodar_testes.py`; `CLAUDE.md`; SPEC (D2, §11).
- **Affected_Tests:** TC-WB24-001..007 (19 testes).
- **Dependencies:** EDR-008; EDR-043; SPEC D2.
- **Approval_Conditions:** —
- **Reopening_Criteria:** Diferença entre os motores que mude algum check; o EDR-008 passar a permitir uma ponte (o recálculo poderia virar parte dela); necessidade de rodar o teste num CI.
- **Related_Decisions:** EDR-008, EDR-043.
- **Source_Conversation_or_Document:** Usuário (instrução na conversa, 2026-10-19: experimento com os dois motores e escolha "Excel, com LibreOffice opcional").

### EDR-045 — Pneu em série na frequência natural e na rigidez de rolagem (SUS-205/206/207/208; novos SUS-211 e SUS-212)

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** A revisão metodológica (`docs/revisao-metodologica.md`, propostas P-01/P-02) mostrou que as três fontes de dinâmica põem a rigidez vertical do pneu em série com a mola, e o projeto não.
- **Question:** SUS-205 e SUS-206/207 devem incluir o pneu?
- **Alternatives:** (a) manter K_W (forma da V2.4, igual à planilha histórica do T09); (b) pôr o pneu em série, como a literatura.
- **Decision:** (b). Novos IDs: SUS-211 (rigidez vertical do pneu, K_T, INPUT por eixo) e SUS-212 (ride rate, K_R = K_W·K_T/(K_W+K_T), CALCULATED). SUS-205 usa K_R; SUS-206/207 = (K_W·t²/2 + K_ARB) em série com K_T·t²/2 (barra referida à roda); o modo Design inverte as duas séries (K_W = K_R·K_T/(K_T − K_R); K_ARB pela inversa da série). Os IDs são SUS-211/212, e não SUS-209/210, porque o EDR-023 cita SUS-209 numa proposta ainda aberta.
- **Rationale:** Milliken p. 588-592 e p. 680 ("tire deflection rates are included in the front and rear roll rate values"); Gillespie eq. 5-8/5-9; Seward eq. 4.1, 4.2, 4.4 e 4.5.
- **Evidence:** `test_suspension_model.py` 54/54, com os exemplos publicados: Seward Ex. 4.1 (K_R 18,2 e 100 N/mm; f_s 2,05 e 4,8 Hz), Gillespie p. 154 (RR 127 lb/in; 1,14 Hz), Milliken p. 592 (K_W 476/254 lb/in; barra 19 904 lb·ft/rad). Planilha V3.0: `test_workbook_suspensao.py` 9/9 (Excel = Python).
- **Assumptions:** K_T é o `VERTICAL_STIFFNESS` do .tir TTC PROVISÓRIO (120 312 N/m, EDR-038), não o pneu do carro: a equipe ainda não tem o valor (usuário, 2026-10-19). Rigidez do pneu linear e igual nos dois lados do eixo.
- **Consequences:** Com os valores da planilha, f_n cai cerca de 6 % e K_φ de 13 a 16 % (demonstrativo). A planilha histórica do T09 (caso A3) usava a forma sem pneu: o caso T09 deixa de bater por construção.
- **Affected_Artifacts:** `python/suspension_model.py`; planilha V3.0 (06_SUSPENSION B22, B23, B32, B33 e l. 46-52; 11_DESIGN B8, B9, B20); Standard SUS-205/206/207/208/211/212.
- **Affected_Tests:** TC-010, piloto, TC-SUS-V30-001..006; TC-WB30-002..007.
- **Dependencies:** EDR-038 (dataset provisório); EDR-003.
- **Approval_Conditions:** —
- **Reopening_Criteria:** Rigidez vertical medida do pneu real; comparação com o OptimumKinematics ou medição de frequência discordante.
- **Related_Decisions:** EDR-014, EDR-038, EDR-046.
- **Source_Conversation_or_Document:** Usuário (instrução na conversa, 2026-10-19): seguir a literatura, principalmente o Milliken; "Todas as propostas que corroboram para com isso estão autorizadas."

### EDR-046 — Termo gravitacional da rolagem na transferência lateral (SUS-103)

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** Proposta P-03 da revisão. SUS-103 usava a forma sem o deslocamento lateral do CG suspenso com a rolagem.
- **Question:** Incluir o termo W_s·h2 da Milliken p. 682?
- **Alternatives:** (a) manter a forma simplificada; (b) fórmula completa da Milliken.
- **Decision:** (b): φ = m_s·a_y·h2/(K_φF + K_φR − m_s·g·h2); ΔFz_F = [K_φF·φ + a_y·(m_s,F·z_F + m_uF·h_uF)]/t_F (análogo atrás), com h2 na vertical. Se m_s·g·h2 ≥ K_φF + K_φR, o Python bloqueia e a planilha devolve "N/A - instabilidade". TC-005 passa a t_F·ΔF_F + t_R·ΔF_R = m·a_y·h + m_s·g·h2·φ.
- **Rationale:** Milliken p. 682-684 e §18.10 (p. 703); Gillespie eq. 6-31 a 6-34. A forma impressa de K_F' na p. 682 não reproduz o exemplo da p. 683; a forma sem essa correção reproduz exatamente e é a coerente com o equilíbrio do carro (ver a revisão).
- **Evidence:** TC-SUS-V30-009 (590,81/483,39 contra 590,8/483,4 lb/g do livro) e TC-SUS-V30-010 (−1,99 °/g contra −2,0 °/g); TC-005 com a nova identidade (resíduo ~1e-13); TC-WB30-003, 006 e 008.
- **Assumptions:** Regime permanente, pequenos ângulos, RC fixo (EDR-009).
- **Consequences:** Muda 09_LOADS B19-B21 e 13_VALIDATION B6. Efeito típico de +2 a +3 % na transferência elástica.
- **Affected_Artifacts:** `suspension_model.lateral_dfz`; planilha V3.0; Standard SUS-103.
- **Affected_Tests:** TC-005, TC-007, TC-008, TC-SUS-V2-004, TC-SUS-V30-009..011; TC-WB30-003/006/008.
- **Dependencies:** EDR-011, EDR-047.
- **Approval_Conditions:** —
- **Reopening_Criteria:** REFERENCE (OptimumKinematics ou medição) discordante.
- **Related_Decisions:** EDR-011, EDR-045, EDR-047.
- **Source_Conversation_or_Document:** Usuário, 2026-10-19 (mesma autorização do EDR-045).

### EDR-047 — Massa suspensa por eixo exata e CG suspenso em a_s (SUS-009, SUS-103)

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** Proposta P-04. A V2.4 distribuía a massa suspensa pela posição do CG total (aproximação documentada em SUS-006).
- **Question:** Usar a distribuição da própria massa suspensa?
- **Alternatives:** (a) manter a aproximação; (b) forma da fonte.
- **Decision:** (b): m_s,F = m·b/L − m_uF, m_s,R = m·a/L − m_uR; a_s = L·m_s,R/m_s; z_s = z_F + (z_R − z_F)·a_s/L; parcela geométrica de SUS-103 = m_s,F·z_F na frente (análogo atrás).
- **Rationale:** Milliken p. 601 (Tab. 16.3: W_SF = W_F − W_UF) e p. 602-603 (h_s, a_s); Seward eq. 5.14.
- **Evidence:** TC-SUS-V30-007/008 (979,5/1163 lb; h_s 15,56 in; 45,7 %); TC-SUS-V30-009 (a_s 4,37 ft como no livro).
- **Assumptions:** CG das massas não suspensas sobre o eixo (Seward Fig. 5.9).
- **Consequences:** 05_VEHICLE l. 25-27 (novas); 06_SUSPENSION B28/B29; 09_LOADS B18-B20. Diferença de ~0,7 % na massa por canto com os valores da planilha.
- **Affected_Artifacts:** `suspension_model` (sprung_mass_axle, sprung_cg_to_front, sprung_mass_per_corner, lateral_dfz); planilha V3.0; Standard SUS-006/009/103.
- **Affected_Tests:** TC-SUS-V30-007..009; TC-WB30-002/005.
- **Dependencies:** EDR-011.
- **Approval_Conditions:** —
- **Reopening_Criteria:** Medição das massas não suspensas com CG fora do eixo.
- **Related_Decisions:** EDR-046.
- **Source_Conversation_or_Document:** Usuário, 2026-10-19.

### EDR-048 — Anti-dive/anti-squat: IC lateral pelo movimento, forma com sinal e ponto de reação do carro (SUS-301/302/406)

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** Propostas P-05 e P-07. O método V1 de SUS-406 (ponto médio das buchas, tan φ = Z_IC/|d|) não aparece na literatura e dá %AD sem sentido em geometria realista (−680,7, TC-KIN-114). A linha de reação (contact patch ou centro da roda) estava em aberto.
- **Question:** Que construção e que ponto de reação usar?
- **Alternatives:** IC: V1, eixos de pivô ou cinemático (SUS-412). Reação: contact patch ou centro da roda.
- **Decision:** IC lateral pelo solver cinemático (SUS-412), que reduz à construção clássica no caso plano; as funções V1 ficam só como legado de regressão. %AD/%AS com sinal (EDR-026): AD = FB_f·(−s)·L/h·100, AS = TF_r·s·L/h·100, s = dz/dx da linha ponto de reação → IC. Ponto de reação pela regra da Milliken (p. 618-619, Fig. 17.12, 17.13 e 17.15), com a configuração informada pelo usuário em 2026-10-19 (freio dentro da roda, em volta do cubo, sem planetária; motor no chassi, atrás): anti-dive dianteiro e anti-lift traseiro pelo **contact patch**; anti-squat traseiro pelo **centro da roda**. Na planilha, 07_KINEMATICS passa a pedir o Δx com sinal e a altura do centro da roda traseira.
- **Rationale:** Milliken p. 612-620; Gillespie p. 249 (IC na interseção projetada dos eixos dos braços) e eq. 7-17 a 7-19 (tração independente: e − r). O IC cinemático e o dos eixos de pivô diferem pouco (36,3 × 38,0 %AD, sintético); a escolha entre os dois cabe à REFERENCE (TC-011).
- **Evidence:** TC-KIN-110/111/114/118 (existentes) e TC-KIN-119 (novo); TC-WB30-002/009 (planilha com sinal; IC à frente dá pro-dive).
- **Assumptions:** Os valores de 07_KINEMATICS continuam PLACEHOLDER (sem hardpoints reais). A altura do centro da roda traseira usa SUS-011 até haver o CAD. A frenagem regenerativa pelo motor no chassi reage pelo chassi, então o anti-lift traseiro sob regeneração seria pelo centro da roda: o escopo fica no EDR-033 (sem decisão).
- **Consequences:** 06_SUSPENSION B38-B41 e 07_KINEMATICS B11/B13/B14. O %AS placeholder muda bastante (a linha agora sai do centro da roda): é placeholder, não resultado.
- **Affected_Artifacts:** `kinematics_model` (REACTION_POINT, docstrings de legado); planilha V3.0; Standard SUS-301/302/406.
- **Affected_Tests:** TC-KIN-119; TC-WB30-002/005/009.
- **Dependencies:** EDR-026, EDR-033, EDR-010.
- **Approval_Conditions:** Método geométrico continua NOT_VALIDATED até a comparação com OptimumKinematics/Lotus (TC-011/012).
- **Reopening_Criteria:** Mudança na configuração de freio ou motor (por exemplo, motor no cubo); REFERENCE discordante.
- **Related_Decisions:** EDR-010, EDR-026, EDR-028, EDR-033.
- **Source_Conversation_or_Document:** Usuário, 2026-10-19 ("O motor fica no empacotamento do chassi, na parte traseira. O freio fica dentro do empacotamento de roda ao redor do cubo").

### EDR-049 — Ky com um único λFz0 (SUS-501)

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** Proposta P-06; divergência (i) do EDR-042 entre o Racer (dois λFz0) e o MFeval (um).
- **Question:** Qual forma seguir?
- **Alternatives:** Racer; MFeval.
- **Decision:** Um único λFz0 (dentro de F'z0), como Pacejka (2006) eq. 4.E25 (com γ = 0) e Seward eq. 5.9. Sem efeito numérico com o .tir atual (LFZO = 1).
- **Rationale:** Duas fontes publicadas contra uma implementação de terceiros.
- **Evidence:** test_tire_model 43/43 (transcrição independente atualizada); TC-TIRE-ORC-004 invertido (agora concorda com o MFeval e diverge do Racer); mutação 24/24 (novo mutante "LFZO extra em Ky"); test_workbook 19/19 com os L* perturbados.
- **Assumptions:** —
- **Consequences:** 10_TIRE, linha de Ky (B:F); `tire_model.pure_fy0`.
- **Affected_Artifacts:** `tire_model.py`; planilha V3.0 (10_TIRE); EDR-042.
- **Affected_Tests:** TC-TIRE-009, TC-TIRE-ORC-004, mutação.
- **Dependencies:** EDR-042.
- **Approval_Conditions:** —
- **Reopening_Criteria:** Documentação TNO/Adams do PAC2002 com outra forma.
- **Related_Decisions:** EDR-042.
- **Source_Conversation_or_Document:** Usuário, 2026-10-19.

### EDR-050 — Valor derivado entra como fórmula, não digitado (05_VEHICLE, 08_VEHICLE_STATE)

- **Date:** 2026-10-19
- **Status:** VERIFIED
- **Context:** Feedback da equipe (2026-10-14), 2ª rodada da V3.0: alguns números calculados estavam digitados na célula, não como fórmula. Inventário das 124 constantes numéricas da V3.0: 05_VEHICLE B4 (316,5 = 248,5 kg medidos + 68 kg de piloto), B9/B10 (a, b = L × 51,57 % e L × 48,43 %, digitados arredondados), B16/B17 (0,254 = diâmetro 20,0 in / 2) e 08_VEHICLE_STATE B5 (11,772 = 1,2 g × 9,81).
- **Question:** Como tratar valor que é resultado de conta?
- **Alternatives:** (a) manter digitado com a conta no comentário; (b) fórmula.
- **Decision:** (b), com a regra do usuário (2026-10-19): se todas as parcelas já estão na planilha, a célula referencia as células e mostra só o resultado da conta; se há parcela externa (medição, documento, referência), a parcela externa vira entrada própria, com origem (EDR-035), e a célula vira a conta. Aplicado: 05_VEHICLE B30 (massa medida sem piloto), B31 (massa do piloto), B32 (fração de peso no eixo dianteiro), B33/B34 (diâmetro do pneu) como entradas novas; B4 = B30 + B31; B9 = L·(1 − f); B10 = L·f; B16/B17 = diâmetro·0,0254/2 (conversão de polegada só na planilha); 08_VEHICLE_STATE B11 (a_y em g) e B5 = B11·9,81 (mesmo g das fórmulas existentes). Ficam de propósito como valor: as molas de 06_SUSPENSION B4/B5 (no carro real são entrada de catálogo; a conta sobre o T09 fica registrada na Fonte), 13_VALIDATION B37:B39 (referência externa do Python) e o caso VERIF da 10_TIRE (caso fixo de teste).
- **Rationale:** Valor digitado esconde a conta e as parcelas, e cada parcela tem origem diferente (a massa mistura medida e referência). Nenhum caso do inventário tinha todas as parcelas dentro da planilha.
- **Evidence:** `tools/rodar_testes.py` inteiro PASS (2026-10-19), CA-07 da V3.0 com 362 fórmulas e 0 diferença; TC-WB30-013 (as cinco células são fórmula e reproduzem os valores anteriores; a e b diferem do digitado em 4,2 µm, o arredondamento antigo); TC-WB30-002/005 (Excel = Python com as entradas novas).
- **Assumptions:** g = 9,81 m/s², o mesmo valor literal das fórmulas existentes (09_LOADS, 13_VALIDATION).
- **Consequences:** +6 fórmulas na V3.0 (356 → 362). Resultados mudam só pelo arredondamento de a e b (ordem de 1e-5 relativo).
- **Affected_Artifacts:** `python/atualizar_planilha.py`; planilha V3.0 (05_VEHICLE l. 4, 9, 10, 16, 17, 29-34; 08_VEHICLE_STATE l. 5 e 11); `tests/test_workbook_suspensao.py`; `tools/comparar_planilhas.py`.
- **Affected_Tests:** TC-WB30-002, 005, 006, 013; CA-07.
- **Dependencies:** EDR-035.
- **Approval_Conditions:** —
- **Reopening_Criteria:** Valor medido que substitua a conta (por exemplo, a e b medidos direto na balança por eixo).
- **Related_Decisions:** EDR-035, EDR-051.
- **Source_Conversation_or_Document:** Feedback da equipe (2026-10-14); usuário, 2026-10-19 ("caso o valor tenha vindo inteiramente de uma fórmula, apenas referencie a célula [...]; para os que têm algum componente externo, siga a metodologia proposta").

### EDR-051 — Fonte de verdade da planilha: gerada durante o desenvolvimento, viva depois de fechada a V3.0

- **Date:** 2026-10-19
- **Status:** APPROVED_WITH_CONDITIONS
- **Context:** O `atualizar_planilha.py` refaz a V3.0 inteira a partir da V2.4 a cada geração, e o CA-07 compara a planilha regenerada com a entregue. Com a coluna de origem editável (EDR-035) e o preenchimento pela equipe, a próxima geração apagaria o que fosse preenchido, ou o CA-07 falharia por motivo legítimo.
- **Question:** Depois que a equipe começar a preencher, qual é a fonte de verdade dos valores e das origens?
- **Alternatives:** (a) CSV versionado no Git com valores e origens, lido e escrito pelo script; (b) planilha gerada enquanto a V3.0 está em desenvolvimento e planilha viva depois do fechamento; (c) decidir depois.
- **Decision:** (b) (usuário, 2026-10-19). Enquanto a V3.0 estiver em desenvolvimento (até terminar a implementação do feedback), a planilha entregue é saída do `atualizar_planilha.py` e não é preenchida pela equipe. Ao fechar a V3.0, a planilha entregue vira o arquivo vivo da equipe e a regeneração para para ela.
- **Rationale:** Escolha do usuário. Mantém a planilha como interface única da equipe (EDR-019), sem um segundo arquivo de dados para manter.
- **Evidence:** —
- **Assumptions:** A equipe não preenche a planilha entregue antes do fechamento da V3.0 (aviso na 00_README).
- **Consequences:** O aviso de origem desatualizada (EDR-035) compara com o valor gravado na geração; depois do fechamento, ele passa a comparar com o valor da versão fechada. O CA-07 vale para a V3.0 até o fechamento.
- **Affected_Artifacts:** planilha V3.0 (00_README); `tools/comparar_planilhas.py` e `tools/rodar_testes.py` no fechamento.
- **Affected_Tests:** CA-07.
- **Dependencies:** EDR-035, EDR-043.
- **Approval_Conditions:** No fechamento da V3.0, definir e aprovar: como o CA-07 trata a planilha viva (por exemplo, comparar só as fórmulas, ou comparar a regeneração com a versão marcada pela tag) e de que arquivo parte a próxima versão gerada (a viva, para não perder o preenchimento).
- **Reopening_Criteria:** Necessidade de rodar o Python sobre os dados preenchidos (ponte Excel → input.json, Fase 2), que favorece a alternativa (a).
- **Related_Decisions:** EDR-008, EDR-035, EDR-043, EDR-044.
- **Source_Conversation_or_Document:** Usuário, 2026-10-19 (escolha "Planilha viva ao fim").

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
| EDR-025 | SUS-205, SUS-301, SUS-302, SUS-104, REQ-004 | planilha 06, 09, 11, 13, 14; testes de planilha. | TC-WB30-010..012 |
| EDR-026 | SUS-301, SUS-302, SUS-406, SUS-412 | Standard SUS-301/302/406; kinematics_model; Data Contract; planilha 06/07. | TC-KIN-110, TC-KIN-118 |
| EDR-027 | SUS-201, SUS-202, SUS-409 | suspension_model_V2_1.py; Standard; Data Contract. | TC-SUS-V2-002, TC-SUS-V21-001..005 |
| EDR-028 | SUS-406, SUS-412 | Standard SUS-406/412; kinematics_model; documento exploratório. | TC-KIN-107, 110, 111, 114 |
| EDR-029 | SUS-401, SUS-402, SUS-412 | Standard SUS-401/402/412; documento exploratório. | TC-KIN-107b, 113 |
| EDR-030 | camber/toe estáticos; SUS-407, SUS-408 | hardpoint-schema-V2.1; Standard V2.1 (SUS-407); Data Contract; Geometry Brief. | TC-HP-104a-d |
| EDR-031 | REQ-001, REQ-002, REQ-003, SUS-003, SUS-004, SUS-005 | planilha V2.1 13_VALIDATION, 15_CHANGELOG. | TC-WB-001..005 |
| EDR-032 | REQ-001..006, TARGET-001..005 | geometry-brief-V2.1.md; (futuro) planilha. | Verificação estrutural manual |
| EDR-033 | SUS-013, SUS-014, SUS-301, SUS-302 | Standard SUS-301/302/013/014 (futuro). | — |
| EDR-034 | — | documento exploratório; Standard. | — |
| EDR-035 | — | Standard; Data Contract; planilha V3.0 (colunas de origem). | TC-WB-004a/b, TC-WB30-010..012 |
| EDR-036 | SUS-4XX proposto | Standard; Data Contract; Geometry Brief. | — |
| EDR-037 | SUS-501, SUS-502, SUS-503 | planilha V2.2 (10_TIRE, 13, 14, 04, 01, 00, 15); tire_model_V2_2.py. | TC-TIRE-001..009, TC-WB22-001..007 |
| EDR-038 | SUS-501..503 | 10_TIRE; 01_SETUP B11; meta.json. | TC-WB22-006 |
| EDR-039 | SUS-501, SUS-502, SUS-404 | 10_TIRE; tire_model_V2_4.py; data-contract-V2_4; Standard (a atualizar). | TC-TIRE-004/005/010, TC-WB22-007, TC-WB24-004c..f |
| EDR-040 | SUS-501..503 | tire_model_V2_2.py; Data Contract §7. | TC-TIRE-008f |
| EDR-041 | SUS-501, SUS-502 | 10_TIRE; 14_DASHBOARD. | TC-WB22-005 |
| EDR-042 | SUS-501, SUS-502 | test_tire_oracles_V2_2.py; planilha V2.3; grade CSV. | TC-TIRE-ORC-001..005 |
| EDR-043 | — | python/*.py; tests/; data/; tools/; pyproject.toml; CLAUDE.md. | Todos os da fase A (mesmo resultado) |
| EDR-044 | SUS-501..503 | tests/test_workbook.py; tests/recalculo_planilha.py; pyproject.toml; tools/rodar_testes.py. | TC-WB24-001..007 |
| EDR-045 | SUS-205..208, SUS-211, SUS-212 | suspension_model; planilha V3.0 (06, 11); Standard. | TC-010, TC-SUS-V30-001..006, TC-WB30 |
| EDR-046 | SUS-103 | suspension_model; planilha V3.0 (09, 13); Standard. | TC-005, TC-SUS-V30-009..011, TC-WB30 |
| EDR-047 | SUS-006, SUS-009, SUS-103 | suspension_model; planilha V3.0 (05, 06, 09); Standard. | TC-SUS-V30-007..009, TC-WB30 |
| EDR-048 | SUS-301, SUS-302, SUS-406 | kinematics_model; planilha V3.0 (06, 07); Standard. | TC-KIN-119, TC-WB30-009 |
| EDR-049 | SUS-501 | tire_model; planilha V3.0 (10_TIRE). | TC-TIRE-009, TC-TIRE-ORC-004, mutação |
| EDR-050 | SUS-001, SUS-006, SUS-010, SUS-011 | planilha V3.0 (05, 08); atualizar_planilha. | TC-WB30-013, CA-07 |
| EDR-051 | — | planilha V3.0 (00_README); CA-07 no fechamento. | CA-07 |

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
