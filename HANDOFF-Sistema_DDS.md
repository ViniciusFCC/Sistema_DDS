# Sistema_DDS — Documento de transferência (handoff) para o projeto no Claude Code

> **Retrato histórico (nota de 2026-10-20).** Este documento descreve o projeto como chegou do claude.ai em
> 2026-10-18 (planilha V2.4, nomes de arquivo com versão, testes descritos como pytest) e não é mais atualizado.
> Estado atual: `CLAUDE.md` (planilha V3.0 fechada, tag `v3.0`; testes são scripts com `check()`) e
> `docs/registro-de-versoes-V3_0.md`. A ordem das fontes de verdade que vale é a do `CLAUDE.md`
> (`docs/Engineering_Decision_Register.md` primeiro); a frase abaixo que manda valer `importado-claude-ai/` era
> a regra da migração.

**Gerado em:** 2026-10-18, a partir do Projeto "Sistema_DDS" do claude.ai (conhecimento do projeto + arquivos gerados nas conversas "Estruturação Planilha DDS", "Implementação 07_Kinematics" e "Implementação 08_Tire").
**Versão de trabalho mais recente encontrada:** **V2.4** (2026-10-14).
**Fonte de verdade:** este documento **resume e indexa**; ele **não substitui** os originais. Em caso de divergência, valem os arquivos originais em `importado-claude-ai/`, nesta ordem: `Engineering_Decision_Register.md` (V2.4) → `engineering-standard-V2.0` → `arquitetura-consolidada-V2.0` → `data-contract-V2_4` → registros de versões.

> Convenção deste documento: **[FATO]** = consta nos documentos; **[PENDENTE]** = aguarda decisão ou dado; **[NOTA DA MIGRAÇÃO]** = observação feita agora, ao consolidar (não é decisão do projeto).

---

## 0. Como usar

1. Abra o novo projeto no Claude Code apontando para `Documentos\Sistema_DDS`.
2. Leia a seção 12 (regras de trabalho do usuário): ela deve virar o `CLAUDE.md` do projeto.
3. Os originais estão em `importado-claude-ai/`:
   - `conhecimento/`: os 38 documentos do conhecimento do Projeto (até a V2.1). Nomes repetidos levam o prefixo `dup-<uuid>`.
   - `arquivos/`: planilhas e CSVs anexados ao Projeto (até a V2.1).
   - `saidas-conversas/<plan|kin|tire>/`: arquivos gerados em cada conversa. **A pasta `tire/` tem a V2.2 a V2.4, que não estavam no conhecimento do Projeto.**
4. O inventário completo, com a versão mais recente de cada artefato, está na seção 14.

---

## 1. Visão geral

- **O que é:** sistema de **dimensionamento e dinâmica da suspensão** do carro de **Fórmula SAE Elétrico** da equipe Tupã ("Tupã Suspension System"). [FATO]
- **Carro atual:** TX/E05. O **T09/E03** é referência histórica e não deve ser usado como baseline (EDR-012). [FATO]
- **Composição:**
  - planilha Excel (`FSAE_EV_Suspension_Fase1_V*.xlsx`), que é a interface e a orquestração;
  - modelos em Python (suspensão, cinemática 3D, hardpoints, pneu), cada um com testes pytest e testes de mutação;
  - documentação de engenharia versionada.
- **Espinha dorsal teórica:** Milliken (*Race Car Vehicle Dynamics*). [FATO]
- **Escopo (DEC-017):**
  - **V1.0 "Engineering Core":** veículo, cargas estáticas, transferência longitudinal, lateral e combinada, rigidez de rolagem, wheel rate, spring rate, motion ratio, frequência natural, anti-dive, anti-squat, bump/rebound e steering básicos, aero básico; setups, targets, referências, Python, Excel, validação e metadados de revisão.
  - **V1.1 "Engineering Intelligence":** sensibilidade, plausibilidade avançada, rastreamento automático de dependências, rastreabilidade formal de requisitos, propagação de incerteza e relatórios automáticos.
- **Bloqueio principal:** **não há hardpoints reais do CAD.** Toda a cinemática foi exercitada só com geometria **sintética**. O CAD da equipe é o **Autodesk Fusion**. [FATO + NOTA DA MIGRAÇÃO]

---

## 2. Arquitetura

### 2.1 Fluxo físico (causalidade linear, arquitetura §1.1)
```
Vehicle Definition + Vehicle State → Load Transfer (Δ) → soma com Static Load → Fz BY CORNER
Fz BY CORNER + Tire Reference + Kinematic Reference → Tire Forces / Tire Utilization
Tire Forces + Suspension Geometry (Suspension Model) → Suspension Loads → FEA
```
- O **Static Load Model** sai direto da Vehicle Definition, em paralelo ao Vehicle State.
- **O pneu nunca é usado para calcular a transferência de carga:** ele consome o Fz por canto já calculado.
- **Kinematic Reference (OptimumKinematics/Lotus)** é a autoridade. O **MODEL/CHECK em Python** corre em paralelo como verificação cruzada e nunca substitui a referência (DEC-002/003).
- **Design Mode** (fluxo reverso): requisitos e targets levam ao desempenho exigido, depois à rigidez exigida e por fim à mola, à MR e ao setup. Usa **relações analíticas fechadas, sem Goal Seek** (EDR-014).
- **O acoplamento Vehicle State → KOP não é resolvido na V1:** a V1 usa KOP prescrito ou selecionado manualmente.

### 2.2 Hierarquia de autoridade das ferramentas (EDR-004)
Milliken (framework) → **OptimumKinematics** (cinemática) → **OptimumTire** (pneu) → **Lotus** (verificação cruzada independente) → **Python** (implementação do modelo) → **Excel** (interface e orquestração). **O CAD é a geometria mestre**, e a **FEA** cuida do estrutural. "O Python é autoridade só por implementar uma equação previamente congelada."

### 2.3 KOP × Vehicle State (arquitetura §6)
- **KOP** é *onde a suspensão está* (posição de curso). Serve para consultar curvas de camber, toe, RC, IC e MR.
- **VS** é *o que o veículo faz* (a_x, a_y, v, esterçamento, aero, setup). Serve para a transferência de carga, o Fz e a utilização do pneu.

### 2.4 Hierarquia de dados (DEC-008)
`PROJECT → VEHICLE | SETUP (FRONT AXLE: FL, FR; REAR AXLE: RL, RR) | REFERENCES (OptimumKinematics, OptimumTire, Lotus, CAD)`

### 2.5 Revisão por domínio e dependências (DEC-011/012)
- **Revisões independentes por domínio:** `G-REV` (geometria), `K-REV` (cinemática), `T-REV` (pneu), `D-REV` (dinâmica) e `S-XXX` (setup).
- Cada resultado registra as revisões de que depende. Se uma dependência avança, o resultado **não é apagado**: vira **STALE**.
- Os hardpoints entram por um arquivo único, `hardpoints.csv` (Geometry Contract), e nunca são digitados em dois lugares.
- *Design Intent* (CAD) e *As-Built* (medido) são categorias distintas.

### 2.6 Processo de divergência MODEL × REFERENCE (DEC-013)
1. Investigar, nesta ordem: unidades → sistema de coordenadas → hardpoints → configuração → hipóteses → equações → configuração do solver → interpolação.
2. Causa encontrada: corrigir o modelo e revalidar. Sem causa: aplicar a tolerância de engenharia → PASS, WARNING, FAIL ou OPEN.
3. **Nunca ajustar o resultado para bater com a referência.** A tolerância é definida **por parâmetro**, em duas camadas: concordância numérica e concordância de engenharia.
4. **FAIL significa "não validado"**, e não "modelo errado".

### 2.7 Arquitetura de dados (DEC-015/016)
- **O Python é externo ao Excel**, sem xlwings, PyXLL ou macros complexas na V1. Não há ponte automática: os resultados de cinemática entram na planilha por **atualização manual** (EDR-008).
- **Intercâmbio:** JSON para configuração e resultados; CSV para dados tabulares. **A unidade vai explícita no nome do campo** (`X_m: 0.450`). É regra não negociável.
- **A arquitetura já prevê Git** para o código, o Standard, os JSON, os CSV e a documentação, com o Excel versionado à parte. A estrutura de repositório proposta é `Suspension-System/{docs, python, data, references, excel, tests}`, com releases `V1.0.0`, `V1.0.1`, `V1.1.0`. [FATO]

---

## 3. Convenções congeladas

| Tema | Convenção | Fonte |
|---|---|---|
| Eixos | **ISO 8855** destro: X para frente, Y para a esquerda, Z para cima. Origem no ponto estrutural do CAD | EDR-001, arq. §4 |
| Ângulos | Roll +: lado esquerdo sobe. Pitch +: **nariz desce**. Yaw +: anti-horário visto de cima. Momentos pela regra da mão direita | arq. §4 |
| Lotus | Adaptador obrigatório: X = −X, Y = −Y, Z = Z. O toe do Lotus tem o sinal invertido | EDR-001/002 |
| Camber e toe | Camber + = topo da roda para fora. Toe + = **toe-out** (igual ao OptimumKinematics) | EDR-002 |
| Motion Ratio | **MR = Δwheel / Δspring** (wheel/spring). Nome obrigatório: `MR [wheel/spring]` ou `motion_ratio_wheel_spring`. K_wheel = K_spring / MR². Termos oficiais: `MR_RH` e `MR(z)`; evitar "MR_effective" | EDR-003, arq. §5 |
| Roll Center | Autoridade: OptimumKinematics, com a curva RC(z) completa. A V1 consome `RC_static = RC(z_RH)`. O RC do Python é só verificação cruzada | EDR-009, arq. §5 |
| Anti-dive e anti-squat | **Não alteram a magnitude** da transferência longitudinal. ΔFz,long **nunca** é descontado por (1 − %AD). Descrevem a partição entre geométrica e elástica | EDR-010, arq. §5 |
| Transferência lateral | Modelo de **duas molas de Milliken**: elástica (rigidez de rolagem), geométrica (RC) e não-suspensa | EDR-011 |
| Aero | Downforce e balanço **fixos por setup**, sem mapa aerodinâmico | EDR-013 |
| Unidades | **SI puro no núcleo de cálculo.** Conversão (mm, N/mm, °, km/h) só na apresentação, no Excel | arq. §4 |
| Pneu (arquivo) | `.tir` PAC2002 em **ISO_TYDEX** (eixo W do TYDEX, help do Adams p. 7): sem transformação na roda direita. Rodas esquerdas espelhadas antes. Até a V2.4: SAE_CALSPAN (α_arq = −α_ISO; Fy_ISO = −Fy_arq; γ_arq = −γ_proj) | EDR-039 (revisto em 2026-10-19) |

---

## 4. Taxonomia, estados e identificadores

### 4.1 Faixas de ID (EDR-005, arq. §2)
| Faixa | Domínio |
|---|---|
| SUS-0XX | Definição do veículo (massa, CG, entre-eixos, bitolas…) |
| SUS-1XX | Carga estática, transferência de carga, Fz por canto |
| SUS-2XX | Rigidez da suspensão (MR, wheel/spring rate, rigidez de rolagem, frequência) |
| SUS-3XX | Anti-geometria (anti-dive, anti-squat) |
| SUS-4XX | Cinemática (REFERENCE e MODEL/CHECK) |
| SUS-5XX | Modelo de pneu |
| SUS-6XX | Direção (escopo reduzido) |
| SUS-7XX | Aero (escopo reduzido) |
| SUS-8XX | Setup e configuração |
| SUS-9XX | Requisitos e targets |
| REQ-XXX / TARGET-XXX / VAL-XXX | Namespaces próprios, ligados por uma tabela de rastreabilidade, sem reutilizar IDs |

### 4.2 Data Type (EDR-006)
INPUT, TARGET, REFERENCE, MODEL, CALCULATED, REQUIREMENT. *Cross-check* é uma flag de metadado do MODEL, e não um sétimo tipo. *Authority* também é metadado.
**Metadados:** Authority, Source, Owner, Revision, Status, Freeze level, Provenance, Timestamp.

### 4.3 Estados: três dimensões independentes, nunca misturadas
- **Lifecycle** (maturidade): OPEN → DRAFT → CHECKED → FROZEN → STALE.
- **Validation** (comparação com a referência): NOT_VALIDATED, PASS, WARNING, FAIL. Um parâmetro pode estar FROZEN e STALE ao mesmo tempo.
- **Registro de decisões** (`Record_Status`): PROPOSED → AWAITING_DECISION → APPROVED ou APPROVED_WITH_CONDITIONS → IMPLEMENTED → VERIFIED. Existem também PENDING_CONFIRMATION, SUPERSEDED e REOPENED.
  - **Recomendação do assistente não conta como aprovação.**
  - **VERIFIED não implica validação física.**

### 4.4 Namespaces de decisão
`EDR-xxx`, o registro de engenharia, é a **fonte de verdade**. `DR-xxx` é o resumo na aba `04_DECISION_REGISTER`. `DEC-xxx` são as decisões citadas na arquitetura, e os registros individuais delas não estão disponíveis.

### 4.5 Test Cases (EDR-016)
A numeração canônica vem da arquitetura §17.7, do Standard e do Python: TC-001..012. Namespaces próprios: TC-KIN, TC-HP, TC-SUS-V2/V21, TC-WB, TC-TIRE e TC-TIRE-ORC. **O Guide usa outra numeração e ainda precisa ser alinhado.**

---

## 5. Engineering Standard V2.0: fichas por bloco

| Bloco | Fichas |
|---|---|
| Veículo | SUS-000 (plano de referência do solo), 001 (massa), 002 (altura do CG), 003 (entre-eixos), 006 (posição longitudinal do CG), 007/008 (massas não-suspensas F/R), 009 (massa suspensa por canto) |
| Cargas | SUS-101 (Fz estático por canto), 102 (ΔFz longitudinal) |
| F: transferência lateral (Milliken) | SUS-004/005 (bitolas), 010/011 (CG não-suspenso F/R), 012 (CG suspenso), 206/207 (rigidez de rolagem F/R), 208 (distribuição λ), **103 (ΔFz lateral, duas molas, CHECKED)** |
| Rigidez | SUS-201 (MR_RH), 202 (wheel rate), 205 (frequência natural). **SUS-203 e 204 estão sem ficha** |
| E: cinemática REFERENCE | SUS-401 (RC REFERENCE), 402 (RC Model/Check), 403 (IC frontal), 406 (IC lateral), 404 (camber gain), 405 (curva de toe) |
| **E.2: cinemática MODEL (V2.0)** | SUS-407 (camber gain), 408 (toe / bump steer), 409 (MR(z)), 410 (geometria do pino-mestre: caster, KPI, scrub, trail), 411 (variação de bitola e entre-eixos), 412 (IC e RC cinemáticos 3D), 413 (cinemática de direção). **Esses IDs ainda não foram aprovados (EDR-023)** |
| H: anti-geometria | SUS-013 (fração de frenagem dianteira FB_f), 014 (fração de tração traseira TF_r), 301 (anti-dive), 302 (anti-squat) |
| G: carregamento combinado | SUS-104 (Fz combinado por canto) |
| I: pneu | SUS-501 Fy(Fz, α, γ), 502 Fx(Fz, slip), 503 μ efetivo. **Precisam ser atualizadas** para a convenção, o espelhamento, o nível 2 e o N/A |
| Direção e aero | SUS-601 (relação de direção), 701 (downforce), 702 (balanço aero) |
| J: Design Mode | Nota de localização (aba 11_DESIGN), sem ficha nova |

Cada ficha segue o template da arquitetura §14: ID, Parameter, Domain, Definition, Equation, Variables, Units, Sign Convention, Assumptions, Reference/Source (**nunca inventada**), Validity Domain, Data Type, Target/Requirement, Status, Owner, Freeze Level, Revision e Validation Method.

---

## 6. Estado atual dos artefatos (V2.4)

### 6.1 Planilha `FSAE_EV_Suspension_Fase1_V2_4.xlsx` (gerada por `build_workbook_V2_4.py`)
- **Abas citadas nos documentos:**
  - 00_README, 01_SETUP, 02_REQUIREMENTS, 03_TARGETS, 04_DECISION_REGISTER, 05_VEHICLE;
  - 06_SUSPENSION, 07_KINEMATICS, 08_VEHICLE_STATE, 09_LOADS, 10_TIRE, 11_DESIGN;
  - 13_VALIDATION, 14_DASHBOARD, 15_CHANGELOG.
  - A arquitetura fala em 16 abas; a aba 12 não aparece nos trechos lidos.
- **Fórmulas:** 347 no total. **As 88 da V2.1 estão intactas** (as 84 originais mais 4 de REQ-001/002).
- **07_KINEMATICS:** tem dois blocos.
  - Placeholders antigos (curso de 60/65 mm), que alimentam o anti-dive/squat e o REQ-004.
  - Bloco de resultados do solver, só com N/A.
- **10_TIRE (V2.2 a V2.4):**
  - Calcula Fx e Fy (puros e combinados) e o μ_eff por canto, a partir de um `.tir` PAC2002/MF 5.2 (nível 2, sem ajuste próprio).
  - Dá N/A fora da faixa do dataset ou com Fz ≤ 0, e um dataset inválido bloqueia tudo.
  - O sistema de eixos do arquivo é declarado (`SAE_CALSPAN` até a V2.4; `ISO_TYDEX` na V3.0, EDR-039 revisto).
- **Placeholders (mapa `placeholder-dependency-map-V2.1.csv`):** 45 das 84 fórmulas dependem de dado que não é do veículo (T1: placeholder, estimativa ou alvo demonstrativo). Mais 23 dependem só de T2 (outro veículo, hipótese) e 16 só de T3 (fonte do TX registrada).
- **Verificação:** Excel == Python com diferença relativa de ~4e-15 (testes de planilha). **O arquivo entregue não passa pelo recálculo do LibreOffice**, que remove as aspas de abas iniciadas por dígito. Por isso foi salvo com `fullCalcOnLoad`.

### 6.2 Python (versão mais recente de cada módulo)
| Módulo | Versão | Testes (último resultado registrado) | Observação |
|---|---|---|---|
| `suspension_model` | V2_1 | 42/42 | Bloqueios de entrada (Guide D.2), `FzLiftoffWarning`, `SmallMotionRatioWarning` (limiar 0,2 **provisório**), `mr_crosscheck` |
| `kinematics_model` | V2_0 (testes em V2_1) | 53/53 | Funções 2D da V1, solver 3D, IC e RC cinemáticos, MR(z), esterçamento, saída CSV, %AD/%AS com sinal. **MODEL/cross-check, nunca REFERENCE** |
| `hardpoints` | V2_0 (testes em V2_1) | 35/35 | Schema, loader, validações e `lotus_to_iso8855` |
| `tire_model` | V2_4 | 43/43, oráculos 5/5, mutação 23/23 | `load_dataset` exige `source_axis_system`; `AXIS_TRANSFORMS`; `wheel_forces` espelha e depois transforma |
| `build_workbook` | V2_4 | `test_workbook_V2_4`: 19/19 | Gera a planilha e o `layout_V2_4.json` |
| Testes de mutação | `mutation_tire_V2_4.py` | — | Também houve mutação em kinematics (14/14) e nas validações (6/6) na V2.0 |

### 6.3 Dados
- `hardpoints_synthetic_V2.0.csv` + `.meta.json` e `kinematics_sweep_synthetic_V2.0.csv`: **sintéticos, não representam o carro.**
- `Hoosier_R25B_13x7_TTC_provisional.tir` + `.meta.json`: dataset **provisório** (T-REV-A), rotulado como tal. O hash registrado é do arquivo **limpo**, sem os prefixos do chat.
- `tire_comparison_grid_V2_3.csv`: 75 pontos (Fz, α, γ, κ → Fx, Fy) no referencial do arquivo, para comparar com o OptimumTire 2 ou o Adams.

---

## 7. Histórico de versões

| Versão | Data | Conteúdo principal |
|---|---|---|
| v0.1 | — | Primeira arquitetura consolidada, Standard v0.1, data contract v0.1, `suspension_model.py` e `kinematics_model.py` iniciais (conversa "Estruturação Planilha DDS"). Duas revisões de arquitetura registradas (`revisao-` e `segunda-revisao-arquitetura`) |
| V1.0 | — | Standard e arquitetura V1.0 (Milliken como espinha dorsal, Dependency Matrix SUS-XXX), modelos V1_0, planilha V1.0 com 84 fórmulas, piloto end-to-end (wheel rate e frequência natural) |
| **V2.0** | 2026-10-09 | Cinemática completa no Python (solver 3D, IC/RC, MR, esterçamento, CSV), módulo e schema de hardpoints, bloqueios de entrada no modelo de suspensão. Bloco E.2 (SUS-407..413). `07_KINEMATICS` com N/A e schema, DR-012. **0 fórmulas alteradas.** Testes: kinematics 47, hardpoints 21, suspensão 33 |
| **V2.1 (parcial)** | 2026-10-10 | REQ-001/002 em `13_VALIDATION` (TC-WB 11/11), cross-check de MR, testes de hardpoints (35) e de sinal de AD/AS (53), mapa de dependências de placeholders, Engineering Decision Register (36 registros). **Não concluídos:** relatório de auditoria, Geometry Brief, documento de critérios de promoção e do estado exploratório, registro de versões V2.1 e regressão final (ver seção 11) |
| **V2.2** | 2026-10-12 | Implementação do pneu em `10_TIRE`, `tire_model_V2_2`, dataset `.tir` provisório, data contract §7, EDR-037..041. 339 fórmulas. Testes: pneu 34/34, mutação 17/17, planilha 15/15 |
| **V2.3** | 2026-10-13 | Verificação das equações do pneu contra dois oráculos de terceiros (Racer `CalcMF52`, port Julia do MFeval), com diferença máxima de 3,4e-7 N e 3,4e-4 N. Grade de comparação com 75 pontos. EDR-042. Sem mudança de fórmulas |
| **V2.4** | 2026-10-14 | Sistema de eixos do `.tir` declarado (SAE_CALSPAN) e transformação para ISO. 347 fórmulas. EDR-039 → APPROVED_WITH_CONDITIONS. Efeito (564 N, roda direita): Fy a α=4° −3%; empuxo de camber a +3° +30%; Fy em deriva zero inverte o sinal |

**Regra de versionamento (EDR-017):** começa em V1.0 e o decimal sobe a cada pequena implementação. Arquivos `.py` usam `_V1_0`, porque o ponto impede o `import`. **Arquivos históricos nunca são sobrescritos.** A numeração V2.x foi adotada pelo assistente para a rodada de cinemática, sem confirmação explícita registrada.
[NOTA DA MIGRAÇÃO] Com Git, a regra pode virar **tags e releases** (`v2.4.0`) em vez de cópias com sufixo. Isso precisa ser decidido por você: veja a seção 13.

---

## 8. Registro de decisões (EDR-001 a EDR-042)

Totais na V2.4: **42** registros. APPROVED 19 · APPROVED_WITH_CONDITIONS 5 · AWAITING_DECISION 9 · IMPLEMENTED 4 · PENDING_CONFIRMATION 2 · VERIFIED 3. Os detalhes completos (contexto, evidência, hipóteses, consequências, critérios de reabertura) estão em `saidas-conversas/tire/Engineering_Decision_Register.md`.

### 8.1 Decididas
| ID | Decisão | Alternativas descartadas | Considerações e condições |
|---|---|---|---|
| EDR-001 | ISO 8855 (X para frente, Y para a esquerda, Z para cima) | Convenção Lotus; default do OptimumKinematics | O OptimumKinematics precisa ser configurado explicitamente; adaptador Lotus obrigatório |
| EDR-002 | Camber + = topo para fora; toe + = toe-out | Convenção Lotus (toe + = toe-in) | Confirmar contra o export real do OptimumKinematics da equipe |
| EDR-003 | MR = wheel/spring; K_w = K_s/MR² | spring/wheel | O valor 1,76 do E03 foi **assumido** como wheel/spring. Uma inversão não é detectada por limiar (ver 027) |
| EDR-004 | Hierarquia: Milliken → OptimumKinematics → OptimumTire → Lotus → Python → Excel | Python como autoridade | Todo MODEL de cinemática é verificação cruzada |
| EDR-005 | Faixas SUS-0XX a 9XX; REQ, TARGET e VAL separados | Esquema VEH/KIN/DYN/TIR/FREQ | Novos IDs respeitam as faixas |
| EDR-006 | Seis Data Types | Sétimo tipo "MODEL/CHECK" | Cross-check é flag de metadado |
| EDR-007 | Lifecycle e Validation independentes | Lista única | — |
| EDR-008 | Python externo; JSON e CSV com unidade no nome; `hardpoints.csv` único; **sem ponte** | xlwings, PyXLL, macros | A atualização da cinemática na planilha é manual |
| EDR-009 | V1 usa RC_static = RC(z_RH) | RC(z) iterativo | A migração do RC é limitação conhecida |
| EDR-010 | AD/AS não alteram a magnitude de ΔFz,long | Descontar (1 − %AD) | SUS-301/302 nunca alimentam SUS-102 |
| EDR-011 | Duas molas de Milliken | Modelos sem RC | A ficha SUS-103 está CHECKED contra uma reprodução secundária (Chalmers 2015); fonte primária não consultada |
| EDR-012 | T09/E03 só como referência histórica; powertrain só do TX/E05 | T09 como baseline | **Tensão aberta:** `06_SUSPENSION` usa spring rate, MR, ARB e RC do T09/E03. É preciso esclarecer o propósito do S-001 |
| EDR-013 | Aero fixo por setup | F_aero(v) | Reabrir com dados de túnel ou CFD |
| EDR-014 | Design Mode explícito, com relações fechadas | Goal Seek | Os valores de 11_DESIGN (2,5/2,7 Hz; λ_f 0,55) são **demonstrativos** |
| EDR-015 | Pneu como REFERENCE, sem ajuste próprio | Ajuste próprio | Níveis 1 (lookup) ou 2 (paramétrico) |
| EDR-016 | Numeração canônica de TC (arquitetura, Standard, Python) | Numeração do Guide | IMPLEMENTED. Alinhar o Guide depois |
| EDR-017 | Regra de versionamento V1.0 → V1.1… | — | Ver seção 7 |
| EDR-019 | Divergências do Guide são esperadas; valores de teste sem rastreabilidade obrigatória; código fora do Guide; foco na planilha | — | — |
| EDR-020 | Solver 3D como MODEL/cross-check | Manter só o 2D | IMPLEMENTED. Validação externa (TC-011/012) pendente |
| EDR-021 | `FzLiftoffWarning` sem clamp; bloqueios de entrada | — | VERIFIED (não é validação física) |
| EDR-022 | Valores de teste podem ser sintéticos, desde que rotulados | Exigir rastreabilidade | Valor sem proveniência nunca aparece como resultado do carro |
| EDR-028 | **IC lateral fica EXPLORATÓRIO** | Declarar definição oficial | Com condições: promoção só pelos critérios de 034 e comparação com OptimumKinematics/Lotus |
| EDR-029 | **RC cinemático fica EXPLORATÓRIO**; procedimento de validação em 7 passos documentado | Declarar referência | Com condições: **não usar em decisões de setup** |
| EDR-030 | Camber/toe estáticos: separar referência de calculado; **sem distância mínima universal** (a recomendação de 0,15 m foi retirada por falta de justificativa) | Aceitar 0,15 m | Com condições: σ_γ ≈ √2·σ_coord/d. O d_min depende da tolerância angular que a equipe definir |
| EDR-031 | REQ-001 (≥ 1525 mm) e REQ-002 (razão de bitolas ≥ 0,75) em `13_VALIDATION` | — | VERIFIED. REQ-004 não foi alterado (depende de 025) |
| EDR-032 | Geometry Brief como artefato separado (sem aba nova) | Aba nova na planilha | Marcado como IMPLEMENTED, mas **o arquivo não foi encontrado** (ver seção 11) |
| EDR-037 | `10_TIRE` com nível 2 (Fx, Fy, μ_eff por canto; N/A fora da faixa) | Estrutura vazia; lookup nível 1 | IMPLEMENTED. Validation = NOT_VALIDATED |
| EDR-038 | `.tir` TTC Hoosier R25B como dado **provisório** (T-REV-A) | Não incluir; incluir sem rótulo | Trocar o dataset exige nova T-REV, e os resultados antigos viram STALE |
| EDR-039 | `.tir` em ISO_TYDEX (revisto em 2026-10-19 pelo help do Adams; até a V2.4, SAE_CALSPAN); espelhamento à esquerda | Só documentar; exigir documento antes | VERIFIED: o sistema de eixos vem da documentação do formato (Adams p. 7), não mais de inferência. Falta comparar a grade com o OptimumTire 2/Adams antes de FROZEN |
| EDR-041 | α, γ, κ demonstrativos (destacados); N/A quando falta entrada | Tudo N/A | Com condições: os μ_eff do dashboard são demonstrativos |
| EDR-042 | Equações do pneu verificadas contra dois oráculos de terceiros | Esperar o livro | VERIFIED. **Fonte primária (Pacejka; TNO/Adams) não consultada.** Divergências entre os oráculos (LFZO em Ky, LGAX/LGAY) só aparecem com L* ≠ 1; o módulo segue o Racer |

### 8.2 Aguardando você
| ID | Pergunta | Alternativas | Recomendação registrada e condições |
|---|---|---|---|
| **EDR-018** (pend. confirmação) | O Decision Register consolidado da planilha está correto? | Manter o do Guide | Confirmar o resultado e a interpretação do DR-009 |
| **EDR-023** | Aprovar os IDs SUS-407..413? | (a) como estão; (b) dividir os IDs agrupados e realocar fora da faixa; (c) adiar | A auditoria achou 4 inconsistências: SUS-410 agrupa 4 grandezas, 412 agrupa 5, 411 e 413 agrupam 2 cada; 409 e 413 estão fora de faixa. Proposta: dividir e realocar (409 → 2XX, 413 → 6XX). No máximo CHECKED, sem renumerar existentes |
| **EDR-024** | Aprovar o schema de hardpoints V2.0? | (a) V2.0; (b) V2.1 com metadados de origem e transformação; (c) adiar | Lacunas: X invertido num só eixo é aceito; UNKNOWN é aceito em silêncio; tolerância de 1 mm do contact patch é rígida. **Não congelar antes de uma importação real** |
| **EDR-025** (Decisão A) | Placeholders na planilha | A: marcar proveniência, manter fórmulas. B: proteger só as células terminais com IF(origem válida). B': B com sensibilidade por saída | Recomendação do assistente: **B'**. REQ-004 dá PASS a partir de placeholders; AD/AS dependem 100% deles. Definir a regra de elegibilidade antes de alterar |
| **EDR-026** (pend. confirmação) | Convenção de sinal de AD/AS: + = anti, − = pro, 0 = neutro | Forma V1 com \|d\| | Houve "Adote" num prompt e "proposta" no seguinte, então **não está registrada como aprovada**. O método continua provisório |
| **EDR-027** (Decisão B) | Limiar absoluto de MR | A: desligar por padrão e usar o cross-check. B: manter 0,2 configurável | Decidido: 0,2 **não** é limite de engenharia. Pendente: o padrão. O limiar não detecta a inversão 1,76 ↔ 0,568, que erra K_w em 9,6 vezes. Recomendação do prompt: A |
| **EDR-033** | Escopo de AD/AS e anti-lift (frenagem regenerativa) | Ampliar fichas; manter | Faltam dados reais de powertrain e freio (posição do motor, divisão entre freio hidráulico e regenerativo, AWD ou não) |
| **EDR-034** | Critérios de promoção DRAFT/CHECKED/FROZEN/STALE | — | A proposta estaria em `kinematics-exploratory-and-promotion-V2.1.md` §F, **arquivo não encontrado** |
| **EDR-035** | Semântica de N/A e TBD | Nova dimensão; metadados existentes | Proposta: N/A = não calculável na configuração atual; TBD = pendente (equivale a OPEN); proveniência pelo metadado Source/Provenance |
| **EDR-036** (Decisão C) | IDs para camber e toe estáticos | A: criar 4 IDs (SUS-414..417, referência e modelo); B: adiar | Recomendação: A, condicionada à resolução do 023 |
| **EDR-040** | Formato de referência do dataset de pneu | (a) PAC2002/MF 5.2 (suportado); (b) MF 6.1.2/6.2; (c) lookup | O loader hoje rejeita MF 6.x. Depende da escolha e de um dataset real |

---

## 9. Achados técnicos e riscos abertos

1. **IC lateral da V1 mal condicionado:** na geometria sintética, %AD de −680,7 contra 36,3 (cinemático) e 38,0 (eixos de pivô) (TC-KIN-114).
2. **`tan φ` com `|d|` ignora o sinal:** um IC à frente e acima, na frente, é pro-dive, mas a forma V1 dá positivo (TC-KIN-110d).
3. **Camber estático pela base `SPINDLE_PT − WHEEL_CENTER` de 0,08 m:** σ ≈ 0,5° para σ = 0,5 mm nos hardpoints (σ arbitrário, sintético).
4. **RC cinemático muito sensível:** σ ≈ 1,9 mm (13%) para σ = 0,5 mm, com migração de +59 a −29 mm em ±30 mm de curso. Dados sintéticos: **não se aplica ao Tupã**.
5. **A inversão de MR não é detectável por limiar** (EDR-027).
6. **Sinal do camber no pneu é inferido** (EDR-039). Se a definição de IA do TTC contradisser a inferência, o efeito de camber inverte de sinal, o que afeta qualquer otimização de camber.
7. **Equações do pneu sem fonte primária:** foram verificadas contra código de terceiros, e não contra o livro nem contra medição.
8. **`06_SUSPENSION` usa dados do T09/E03**, em tensão com o EDR-012.
9. **Sensibilidade da massa não-suspensa (arbitrária, 15/18 kg):** quase não muda o Fz (≤ 0,2%), mas muda a frequência natural em 5,4% a 6,4%.
10. **O LibreOffice não serve para recalcular o entregável.** [NOTA DA MIGRAÇÃO] O Excel está instalado na sua máquina.

---

## 10. Pendências por tipo

**Dados da equipe (sem como contornar):**
- Hardpoints reais do CAD (Fusion), sem os quais TC-011/012 seguem NOT_VALIDATED.
- Referência do OptimumKinematics e definição do curso.
- Configuração real de freio e trem de força (`reaction_point`).
- Curso de cremalheira por volta.
- Tolerância angular de camber e toe.
- Dataset real de pneu e o formato escolhido.
- Documento do TTC com as definições de IA e SA.

**Decisões suas:** EDR-018, 023, 024, 025, 026, 027, 033, 034, 035, 036 e 040 (seção 8.2). Também falta decidir os placeholders de `07_KINEMATICS`, que alimentam SUS-301/302: manter ou migrar para N/A/TBD.

**Trabalho técnico sem depender de dados:**
- Fichas SUS-203 e SUS-204.
- TC de sinal para SUS-404/405.
- Atualizar as fichas SUS-501..503.
- Zona de importação de `kinematics_sweep_<canto>.csv` na planilha (é estrutura nova, então exige aprovação).
- Consumir o `.meta.json` do pneu no Python.
- Alinhar o Guide (numeração de TC e DR).
- Concluir os documentos da V2.1 (seção 11).

**Para a validação do pneu:**
1. Conferir Fx0, Fy0 e a combinação no livro de Pacejka (biblioteca da EESC).
2. Rodar `tire_comparison_grid_V2_3.csv` no OptimumTire 2 ou no Adams.

---

## 11. Lacunas encontradas na migração (conferir)

| Item | Situação |
|---|---|
| **Definitive_Guide_DDS.pdf** (153 páginas, só imagem) | **Não veio na exportação**: o servidor respondeu "arquivo não encontrado". Na cópia do conhecimento do Projeto ele tem só 304 caracteres. **Baixe o PDF original à mão**, de onde você o tiver |
| `audit-report-V2.1.md`, `geometry-brief-V2.1.md`, `kinematics-exploratory-and-promotion-V2.1.md`, `registro-de-versoes-V2.1.md`, `hardpoint-schema-V2.1.md` | Citados no EDR, mas **não existem** entre os arquivos gerados. A conversa de cinemática terminou com eles "ainda a escrever" |
| `build_workbook_V2_3.py`, `layout_V2_3.json` | Não estavam na pasta de entrega (o registro V2.4 confirma). A V2.4 os substitui |
| `build_workbook.py` original e a pasta `latex_src/` (conversa "Estruturação") | O download falhou. Podem ser a fonte LaTeX do Guide. Verifique se você tem cópia |
| Registros DEC individuais | Nunca foram fornecidos ao projeto (o próprio EDR diz isso) |
| Planilhas | V1.0 a V2.4 estão todas disponíveis (`arquivos/` e `saidas-conversas/`) |

---

## 12. Regras de trabalho do usuário (base para o `CLAUDE.md` do projeto)

- **Nunca alterar fórmulas existentes da planilha sem aprovação explícita.** Toda mudança de fórmula registra a aba, a célula, a fórmula anterior e a nova, as dependências, a justificativa e o teste.
- **Recomendação do assistente não é aprovação.** Instrução ambígua vira PENDING_CONFIRMATION.
- **Não preencher lacunas por inferência**, e não inventar referências, coeficientes, targets nem limites.
- **Não criar nem renumerar IDs sem autorização.** Aprovar um ID não valida a equação.
- **Valores sintéticos ou demonstrativos sempre rotulados.** Nunca apresentados como resultado do carro.
- **Distinguir "resultado de código" de "validação física".** VERIFIED ≠ validado.
- **Toda decisão relevante entra no EDR** antes ou durante a implementação.
- **Arquivos históricos nunca são sobrescritos.** Com Git, isso passa a valer pelo histórico.
- **Unidade explícita** em todo campo de intercâmbio, e SI no núcleo.
- **Divergência MODEL × REFERENCE:** seguir o processo da seção 2.6, e nunca "ajustar para bater".
- **Foco declarado:** completar a planilha. O Guide fica para depois (EDR-019).

---

## 13. Plano para o novo projeto no Claude Code [NOTA DA MIGRAÇÃO]

### 13.1 Estrutura proposta (segue a arquitetura §10)
```
Sistema_DDS/
├── CLAUDE.md                 ← regras da seção 12 + comandos
├── docs/                     ← Standard, arquitetura, data contract, EDR, registros
├── python/                   ← suspension, kinematics, hardpoints, tire, build_workbook
├── tests/
├── data/                     ← hardpoints, sweeps, .tir + .meta.json (sintéticos marcados)
├── excel/                    ← planilha gerada (versão atual)
├── references/               ← material didático e acadêmico (PDF + .md convertido, Zotero)
└── importado-claude-ai/      ← originais desta migração (somente leitura)
```

### 13.2 Decisões que a migração levanta (precisam de você)
1. **Versionamento:** trocar o sufixo `_V2_4` no nome dos arquivos por Git com tags (`v2.4.0`), mantendo os nomes de módulo estáveis (`tire_model.py`)? Isso mudaria o EDR-017.
2. **Recalcular a planilha no Excel via xlwings:** o EDR-008 e o DEC-015 vetam xlwings como **ponte** na V1. Usá-lo **só para verificação em teste**, recalculando e comparando com o Python, é diferente, mas é uma mudança de prática. Precisa de uma decisão sua e de um EDR.
3. **Material didático e acadêmico em `references/`:** converter uma vez para `.md` (MarkItDown ou Docling) e catalogar no Zotero. Isso pode destravar a fonte primária do pneu (Pacejka) e do Milliken.

### 13.3 Ferramentas planejadas (instalar quando o projeto existir)
- **xlwings** (verificação), **hypothesis** (testes de propriedades da cinemática), **pint** (unidades), **sympy** (relações fechadas do Design Mode), **pytest-cov**, **plotly** e **streamlit** (visualização 3D dos hardpoints e das varreduras).
- **MFeval**, que avalia a Magic Formula 6.1/6.2 em MATLAB e Python: oráculo para o 10_TIRE.
- **Vehicle Dynamics Blockset**, que você já tem no MATLAB R2025b: verificação cruzada de transferência de carga e forças do pneu.
- **Servidor MCP do MATLAB**, que já está no catálogo.
- **Script na API do Fusion** para exportar `hardpoints.csv` no schema. Destrava o principal bloqueio.
- **GitHub Actions** (testes a cada push), plugin **Scientific-Coding-Skill**, e o **Lotus Suspension Analysis** como referência opcional (acesso a confirmar).
- **Skills do setup que se aplicam:** `fluxo-github`, `claude-md-projeto`, `council` (para as 11 decisões pendentes), `otimizacao-codigo`, `fluxo-documentos` (para refazer o Guide em Quarto) e `memorial-de-calculo`.

---

## 14. Inventário: versão mais recente de cada artefato

| Artefato | Arquivo mais recente | Local em `importado-claude-ai/` |
|---|---|---|
| Registro de decisões | `Engineering_Decision_Register.md` (V2.4-PARCIAL, 42 EDR) | `saidas-conversas/tire/` |
| Engineering Standard | `engineering-standard-V2.0-suspensao-fsae.md` | `saidas-conversas/kin/` (também em `conhecimento/`) |
| Arquitetura | `arquitetura-consolidada-V2.0-suspensao-fsae.md` | `saidas-conversas/kin/` |
| Data contract | `data-contract-V2_4-excel-python.md` | `saidas-conversas/tire/` |
| Schema de hardpoints | `hardpoint-schema-V2.0.md` | `saidas-conversas/kin/` |
| Registros de versões | V1.0, V2.0 (`kin/`); V2_2, V2_3, V2_4 (`tire/`) | — |
| Revisões de arquitetura (v0.1) | `revisao-` e `segunda-revisao-arquitetura-suspensao-fsae.md` | `saidas-conversas/plan/` |
| Planilha | `FSAE_EV_Suspension_Fase1_V2_4.xlsx` | `saidas-conversas/tire/` |
| Gerador da planilha | `build_workbook_V2_4.py` + `layout_V2_4.json` | `saidas-conversas/tire/` |
| Suspensão | `suspension_model_V2_1.py` + `test_suspension_model_V2_1.py` | `saidas-conversas/kin/` |
| Cinemática | `kinematics_model_V2_0.py` + `test_kinematics_model_V2_1.py` | `saidas-conversas/kin/` |
| Hardpoints | `hardpoints_V2_0.py` + `test_hardpoints_V2_1.py` | `saidas-conversas/kin/` |
| Pneu | `tire_model_V2_4.py`, `test_tire_model_V2_4.py`, `test_tire_oracles_V2_4.py`, `mutation_tire_V2_4.py` | `saidas-conversas/tire/` |
| Testes da planilha | `test_workbook_V2_4.py` | `saidas-conversas/tire/` |
| Caso de referência T09 | `test_t09_reference_case.py` | `saidas-conversas/plan/` |
| Dados do pneu | `Hoosier_R25B_13x7_TTC_provisional.tir` + `.meta.json`, `tire_comparison_grid_V2_3.csv` | `saidas-conversas/tire/` |
| Dados sintéticos e mapa | `hardpoints_synthetic_V2.0.csv/.meta.json`, `kinematics_sweep_synthetic_V2.0.csv`, `placeholder-dependency-map-V2.1.csv` | `saidas-conversas/kin/` |
| Histórico | Todas as versões anteriores (v0.1, V1.0, V2.0 a V2.3) | `conhecimento/`, `arquivos/`, `saidas-conversas/` |
