# Arquitetura planejada do Sistema_DDS: roadmap, fases e onde o projeto está

**Data:** 2026-10-20. **Situação:** registro de leitura, sem decisão nova. Este documento não aprova nada: as
escolhas que ele levanta (seção 7) ficam como pendências do usuário.

**Fontes.**

| Sigla | Documento | Onde está | Observação |
|---|---|---|---|
| [GUIA] | *Guia Definitivo de Dimensionamento Dinâmico da Suspensão*, EESC-USP Tupã, Mecânica. Escopo declarado: "V1 do sistema de dimensionamento dinâmico" | `references/pdf/Definitive_Guide_DDS.pdf`; OCR em `references/md/definitive-guide/livro.md` (fora do Git) | Recebido do usuário em 2026-10-20 (a cópia em `importado-claude-ai/` tem 304 bytes e não abre). 153 folhas, sem camada de texto. Citações por seção; os trechos usados aqui foram conferidos na imagem da página (folhas 23-25, 32-34, 43-44, 136-137) |
| [ROADMAP] | *Tupã Suspension System: arquitetura planejada, roadmap de versões e fases de engenharia* | `docs/arquitetura-planejada-roadmap-V0-V5.md` | Recebido do usuário em 2026-10-20, registrado sem alteração. A origem não aparece nos arquivos do projeto; o texto fala em "roadmap discutido" |

## 1. Três numerações com a letra V

O projeto usa hoje três numerações diferentes que começam por "V". Confundi-las leva a conclusões erradas
("a planilha V3.0 é a etapa V3 do roadmap"), por isso elas vêm antes de tudo.

| Numeração | O que mede | Valores | Fonte |
|---|---|---|---|
| Roadmap do Guia | Capacidade do sistema; o Guia chama cada uma de **Fase** | V1.0, V1.1, V2, V3 | [GUIA] §8.9 |
| Roadmap V0-V5 | Capacidade do sistema | V0 a V5 | [ROADMAP] §3 |
| Versão dos artefatos | Revisão da planilha e dos documentos | V1.0, V2.0 a V2.4, V3.0; a próxima é a V4.0 (usuário, 2026-10-20) | EDR-017, EDR-043 |

A planilha se chama `FSAE_EV_Suspension_Fase1_V3_0.xlsx`: **Fase 1** é a etapa do roadmap (V1 do Guia) e
**V3_0** é a revisão do arquivo. É a mesma lógica dos textos da planilha que dizem "PROVISÓRIO até a Fase 2
(OptimumKinematics)": Fase 2 é a etapa V2 do Guia (cinemática e acoplamentos).

**Colisão a resolver.** A próxima planilha (V4.0) não tem relação com a etapa V4 do [ROADMAP] (otimização), e a
planilha V3.0 não pertence à etapa V3 (pneu e CarSim). A seção 7 propõe uma forma de separar os nomes.

## 2. O roadmap do Guia

### 2.1 Escopo da V1 ([GUIA] §1.4 e §1.5)

| Domínio | Incluído na V1 | Tratamento |
|---|---|---|
| Veículo | massa, CG, entre-eixos, bitolas, massas não suspensas | INPUT conforme a proveniência |
| Cargas | estática, longitudinal, lateral, combinada | quase-estático |
| Rigidez | MR, wheel rate, spring rate, rigidez de rolagem e distribuição | pontual no ride height |
| Frequência | frequência natural não amortecida | massa-mola |
| Anti-geometria | anti-dive, anti-squat | geometria de referência e cálculo reduzido |
| Cinemática | hardpoints, camber, toe, RC e curvas de referência | OptimumKinematics/Lotus como REFERENCE |
| Pneu | interface e consumo de dados | OptimumTire/TTC como REFERENCE, escopo reduzido |
| Direção | geometria e relação básicas | — |
| Aero | downforce e balanço fixos | entradas por Setup |
| Design Mode | frequência e rigidez reversas | a partir de target |

Fora da V1: solver cinemático 3D interno que substitua a ferramenta; amortecedor e dinâmica transitória;
compliance; aero dependente de velocidade; ajuste de pneu dentro do Excel; otimização paramétrica completa.

### 2.2 Etapas seguintes ([GUIA] §8.4 a §8.9)

| Etapa | Entregável | O que inclui | Critério de saída |
|---|---|---|---|
| V1.0 | núcleo físico e workbook | escopo da seção 2.1 | testes analíticos e rastreabilidade |
| V1.1 | inteligência de engenharia | análise de sensibilidade; checagens de plausibilidade avançadas; rastreamento automático de dependências; rastreabilidade formal de requisitos; propagação de incerteza; relatórios automáticos | checagens e sensibilidade |
| V2 | cinemática e acoplamentos | MR(z); RC(φ); solver cinemático interno só com justificativa; compliance; acoplamento veículo-pneu mais completo | referência externa e validação |
| V3 | pista | instrumentação de suspensão; cargas de roda; validação em pista; identificação de parâmetros; correlação sistemática simulação × pista | correlação com sensores |

Regra de entrada de qualquer funcionalidade nova ([GUIA] §8.8): pergunta de engenharia clara, benefício
esperado, especificação, implementação, teste e responsável. "Ser mais sofisticado não é requisito suficiente."
O que não fazer ([GUIA] §8.7): complexidade sem validação; exemplo virando target; copiar números de ciclos
anteriores; solver duplicado sem fronteira de autoridade; referência usada fora do ponto de operação.

## 3. O roadmap V0-V5 e as fases A-J ([ROADMAP])

O [ROADMAP] reorganiza e estende o do Guia em seis capacidades: V0 (fundação e governança), V1 (dinâmica e
dimensionamento), V2 (cinemática), V3 (pneu, CarSim e desempenho do veículo), V4 (otimização e projeto
multidisciplinar, com FEA no longo prazo) e V5 (validação experimental e ciclo de melhoria). Separa essas
capacidades de um processo de trabalho em dez fases, de A (definição do problema e do envelope) a J
(congelamento, liberação e manutenção), declarado como proposta e não como nomenclatura aprovada (§10).

### 3.1 Correspondência entre os dois roadmaps

| [ROADMAP] | [GUIA] | Diferença |
|---|---|---|
| V0 Foundation | caps. 2, 3, 5 e apêndices da V1 | O Guia trata a governança como parte da V1; o [ROADMAP] a separa como etapa própria |
| V1 Sizing | V1.0 | Mesmo conteúdo |
| — | V1.1 inteligência | O [ROADMAP] não tem etapa própria: sensibilidade e rastreamento aparecem em V0 (matriz de dependências) e V4 (§8.5) |
| V2 Kinematics | V2 cinemática e acoplamentos | O Guia põe na V2 a compliance e o acoplamento veículo-pneu; o [ROADMAP] deixa a compliance para V5 ("se incluída no escopo") e o acoplamento para V3 |
| V3 Tire + CarSim | — | Novo: modelo de pneu como núcleo e CarSim como veículo completo. No Guia o pneu é só interface na V1 e o CarSim não aparece |
| V4 Optimization | — (fora do escopo da V1, §1.5) | Novo |
| V5 Experimental | V3 pista | Mesmo papel; o [ROADMAP] detalha o ciclo de 10 passos e a instrumentação |

### 3.2 Fases A-J e o fluxo de engenharia do Guia

O Guia não tem fases de processo, mas tem um **fluxo de 8 etapas** para cada pergunta de projeto
([GUIA] §7.2-7.9): definir a pergunta, definir o caso, verificar dados, calcular, verificar, interpretar,
decidir, registrar. As fases A-J do [ROADMAP] valem para uma capacidade inteira; o fluxo do Guia vale para uma
pergunta. Os dois se encaixam: o fluxo é o que se repete dentro das fases D a I.

## 4. O que o Guia acrescenta ao [ROADMAP]

O [ROADMAP] lista como "a definir" (§36) alguns pontos que o Guia já resolve ou detalha. Ficam registrados
aqui como complemento, sem alterar o texto recebido.

1. **Critério de promoção** ([GUIA] §3.2 e §3.12). Níveis de congelamento F0 (exploração), F1 (conceito
   definido), F2 (especificado: pode ser implementado), F3 (implementado e verificado internamente: alimenta
   análises internas) e F4 (congelado para o uso definido: baseline do ciclo). A promoção F0 → F4 "deve ser
   proporcional ao uso": um parâmetro que só estuda tendência não precisa da evidência de um que define hardware
   fabricado. Isso responde em parte ao EDR-034 (critérios de promoção), registrado como AWAITING_DECISION e
   cuja proposta citada nunca foi escrita.
2. **Ciclo de vida das metas** ([GUIA] G.1): TBD, OPEN, PROPOSED, APPROVED, FROZEN, STALE. É diferente do ciclo de
   vida de parâmetros (OPEN, DRAFT, CHECKED, FROZEN, STALE; §3.3).
3. **Como escolher metas** ([GUIA] G.3), em oito passos: definir o requisito de comportamento; avaliar pneus e uso
   do carro; avaliar massa e envelope de suspensão; comparar literatura e experiência anterior; estudar
   sensibilidade; propor faixa; validar contra embalagem e hardware; aprovar e congelar. Regra de promoção de
   uma meta ([GUIA] F.3): responsável, justificativa, faixa ou valor, fonte ou racional, revisão e estado.
4. **Marcadores D, S, I, V, P, R** ([GUIA] §3.5): decidido, especificado, implementado, verificado,
   proveniência, revisão.
5. **Classes de proveniência** ([GUIA] §3.6): MEASURED, CALCULATED, REFERENCED, ESTIMATED, ASSUMED,
   PROVISIONAL, PLACEHOLDER, UNKNOWN. A V3.0 adotou outro conjunto (os 6 rótulos de Origem, EDR-035); a
   correspondência entre os dois não está registrada.
6. **Classes de papel** ([GUIA] §2.2): além de TARGET, REFERENCE, MODEL, INPUT e CALCULATED, o Guia usa ASSUMED e
   PROVISIONAL.
7. **Regras de descarte de resultado** ([GUIA] §7.16): violação de conservação, entrada sem proveniência,
   revisão STALE, unidade ambígua, Design Mode sem target, Fz negativo sem tratamento, divergência externa sem
   investigação.
8. **Testes sintéticos mínimos** ([GUIA] §5.9), **campos de proveniência de cada execução** (§5.10: revisão do
   workbook, Setup, revisões de geometria, cinemática e pneu, versão do script, data) e a exigência de que um
   cross-check use um caminho de cálculo diferente (§5.14.2).
9. **Validação progressiva** ([GUIA] §7.14): checagens analíticas, depois simulação, bancada e pista.
10. **Decisão de fabricação** ([GUIA] §7.13): resultado do Design Mode não é especificação de mola comprável
    (comprimento, pré-carga, faixa, embalagem, taxa real do fornecedor).

## 5. Onde o projeto está em cada etapa (2026-10-20, commit `7af299d`, tag `v3.0`)

Estado medido pela suíte inteira, que passou nesse commit. "Pronto" quer dizer implementado e verificado
(VERIFIED); nada está validado fisicamente.

| Etapa ([ROADMAP] / [GUIA]) | Situação | Evidência | Falta |
|---|---|---|---|
| V0 / governança da V1 | Quase completa | Standard, arquitetura V2.0, data contract V2.4, EDR com 53 registros, REQ-001 a 006 com fonte no regulamento, TARGET-001 a 005 (estrutura), 13_VALIDATION, changelog, mapa de dependências e pior origem ao vivo, Git com tags | Registro de validação (VAL-) não é usado; revisões por domínio só em parte (01_SETUP tem `G-REV-A`, cinemática "TBD (Fase 2)"); STALE não é automático; ponte JSON Excel-Python não existe (por decisão, EDR-008) |
| V1 Sizing / V1.0 | Forma pronta, dados não | Equações revisadas contra o Milliken (EDR-045 a 053); Python × planilha 19/19 e 15/15; mutação 25/25 | Metas TBD; mola, MR, barra e RC demonstrativos (T09); passo 1 da sequência de dimensionamento ([ROADMAP] §5.12, metas) ausente |
| — / V1.1 | Em parte | Pior origem e mapa de raízes (rastreamento de dependências); aviso de Fz < 0 | Sensibilidade, incerteza, rastreabilidade formal, relatórios |
| V2 Kinematics / V2 | Modelo pronto, referência não | Solver 3D como MODEL/cross-check (EDR-020), MR(z), IC/RC pelo trabalho virtual (EDR-053), direção (EDR-052), schema de hardpoints | Hardpoints reais; comparação com o OptimumKinematics (critério de saída); compliance; EDR-024 |
| V3 Tire + CarSim / — | Pneu em forma, CarSim nada | PAC2002 na planilha e no Python, conferido contra o help do Adams e o Pacejka | Pneu real (R60A); comparação com o OptimumTire; CarSim (acesso não informado) |
| V4 Optimization / — | Só o Design Mode reverso | 11_DESIGN | Tudo |
| V5 Experimental / V3 pista | Nada | — | Tudo |

## 6. Onde entra o bloco de metas e equilíbrio (planilha V4.0)

O bloco desenhado em 2026-10-20 (`docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md`) cobre:

- o passo 1 da sequência de dimensionamento ([ROADMAP] §5.12) e o processo G.3 do Guia (metas);
- sensibilidade e rastreamento entre fichas (V1.1 do Guia);
- o acoplamento veículo-pneu em regime permanente: análise de par e MMM do Milliken (V2 do Guia; parte
  "Vehicle Performance" da V3 do [ROADMAP], sem CarSim);
- a tabela de troca, que é a "varredura interpretável" com que o [ROADMAP] manda começar a otimização (§8.5).

Ele não pula etapas: nada nele depende de CarSim, de otimização formal ou de dado de pista.

## 7. Pendências que este registro levanta (decisão do usuário)

1. **Qual roadmap é o canônico.** O Guia é o documento técnico da V1; o [ROADMAP] é mais recente e mais amplo,
   mas não tem origem registrada no projeto. Uma saída é adotar o [ROADMAP] como plano, com os complementos da
   seção 4, por um EDR.
2. **Como separar as três numerações** (seção 1). Uma possibilidade: chamar as etapas do roadmap de "Fase 0" a
   "Fase 5" (como o Guia e o nome do arquivo já fazem) e reservar "V" para a revisão dos artefatos.
3. **Correspondência entre as classes de proveniência do Guia e os 6 rótulos de Origem da V3.0** (seção 4,
   item 5).
4. **EDR-034:** usar os níveis F0-F4 e a promoção proporcional ao uso do Guia como base.
