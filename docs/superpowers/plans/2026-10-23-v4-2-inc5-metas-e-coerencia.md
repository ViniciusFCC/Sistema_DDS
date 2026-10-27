# V4.2, incremento 5 (metas e coerência; projeto T11; viva no Drive): plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx` a partir da V4.1 da tag `v4.1`, com (1) o processo de metas da spec §4-§5 (fichas na 03_TARGETS, aba `23_LISTAS` com vocabulário e relações L/E/M, META/CONSEQUÊNCIA, sobredeterminação, estados de coerência, TARGET-006 e 007 em TBD, `docs/metas/`, F0-F4 no EDR-034); (2) a lista `Origens` e o prefixo D16 voltados ao **T11**; (3) a viva do Drive coberta por conferência, retrato e migração por nome; (4) as pendências do EDR-060.

**Architecture:**
- `python/origens.py` (novo): rótulos de origem por versão e o mapa V4.1 → V4.2. Nenhuma constante da V3.0-V4.1 muda (`atualizar_planilha.TX` etc. continuam regenerando as versões antigas, CA-07).
- `python/metas.py` (novo, oráculo puro): vocabulários, relações, `estado_coerencia`, `pior_coerencia`. A planilha só vale se reproduzir esse resultado (EDR-004).
- `python/aba_metas.py` (novo): escreve as colunas novas da 03_TARGETS, a `23_LISTAS` e as linhas 49-51 do 14_DASHBOARD por famílias de fórmula (catálogo G1-G6).
- `python/gerar_v4_2.py` (novo): extrai a V4.1 da tag `v4.1`, aplica as alterações aprovadas, chama `aba_metas`, acrescenta os nomes de `data/nomes_V4_2.csv`, grava o registro de células. Mesmo padrão de recusas de `gerar_v4_1.py`.
- `python/viva.py` (novo) e `tools/conferir_viva.py`, `tools/retrato_viva.py`, `tools/migrar_viva.py` (novos): a viva do Drive é lida só por cópia local; nada grava no Drive.

**Tech Stack:** Python 3.13, openpyxl, `tests/recalculo_planilha.py` (Excel via COM; LibreOffice só na suíte final), scripts com `check()`.

**Spec:** `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` §4, §5, §7.3 item 7 (D16), §7.6 item 3, §8.2, §8.3, §9 itens 6 e 7, §10 linha 5, §11. Guia: G.1, G.3, F.3 (folhas 136-137), §3.2 e §3.12 (folhas 23-24). Decisões anteriores: EDR-034, EDR-035, EDR-051, EDR-058, EDR-060.

## Decisões do plano (o controlador escolheu onde uma opção domina; vão nos EDRs indicados)
1. **Origens para o T11 (EDR-062).** A lista continua com **6 rótulos nas mesmas posições**; mudam só os dois primeiros:
   posição 1 `● Dado do TX` → **`● Dado do T11`** (medido no T11 ou em documento do projeto T11); posição 2 `◐ Dado do T09` → **`◐ Dado de outro carro (TX, T09)`** (valor do TX/E05 ou do T09/E03; o carro vai na Fonte). Por quê: todas as fórmulas de pior origem usam o índice na lista (`IFERROR(MATCH(…,Origens,0),6)`, 6 = `? A confirmar`) e as cores usam o símbolo; com 6 posições nenhuma delas muda. Uma 7ª posição obrigaria a reescrever todas as fórmulas de pior origem. TX e T09 são, os dois, "não é o carro" para o T11; a diferença entre eles fica na Fonte.
   Duas substituições diferentes, nunca misturadas: (a) **dado** (célula de Origem com valor e a coluna oculta H): `● Dado do TX` e `◐ Dado do T09` → `◐ Dado de outro carro (TX, T09)`; (b) **regra** (texto explicativo e o literal do D16 nas fórmulas 16_EQUILIBRIO B188 e B189): `● Dado do TX` → `● Dado do T11`. Só o T11 tira o prefixo "DEMONSTRATIVO · ". O 04_DECISION_REGISTER e o 15_CHANGELOG ficam (registro histórico).
2. **Python do D16:** `equilibrio.texto_veredito` e `equilibrio_linear.texto_k` ganham `origem_do_carro: str = origens.T11` (keyword-only). Quem testa a V4.1 (`tests/test_workbook_v4_1.py`, `tools/relatorio_inc4.py`, testes puros que esperam o TX) passa `origens.TX_V41` explicitamente. `raizes`/`aba_equilibrio.pior_origem_de_valores` ganham `lista=ORIGENS_LISTA` para receber `origens.ORIGENS_V42`.
3. **Viva no Drive (EDR-063, revê EDR-051 item 2 e EDR-058 item 6).** (a) O CA-07 "viva × referência" da suíte deixa de olhar `excel/…V3_0.xlsx` (que não é mais viva) e passa a: "`excel/…V3_0.xlsx` igual ao arquivo da tag `v3.0` (SHA-256)", no resumo. (b) A viva do Drive vira uma seção **informativa** do log, fora do resumo: a suíte verifica o repositório, e a viva muda sem commit (mesmo commit daria resultados diferentes). Ela é conferida contra a referência da **versão dela** (lida na 00_README A3: V4.1 → tag `v4.1`; V4.2 → tag `v4.2` ou, antes da tag, `excel/`). Sem Drive montado: "NÃO EXECUTÁVEL", sem falha. (c) `tools/conferir_viva.py` dá o mesmo veredito com código de saída (0 igual, 1 diverge, 3 não lida) e roda antes de todo retrato e de toda troca. (d) **Retrato `dados:`** = `data/viva/retrato-viva.json` (dados por nome, valores com tipo, SHA-256 e versão da viva), não o .xlsx: com o CA-07 da viva passando, viva = referência da tag + entradas, então o JSON e a tag reconstroem a viva; o .xlsx (3,2 MB) inflaria o Git a cada retrato e o Drive já guarda o histórico do arquivo. (e) **Troca por versão** (diretriz do usuário, 2026-10-23: "a cada versão que terminarmos, o arquivo no drive precisa ser alterado para a mais recente e os dados preenchidos devem se manter"): `tools/migrar_viva.py` leva os dados da viva para uma cópia da versão nova pelo nome, com o mapa de rótulos; a troca no Drive é a Task 8, depois do merge e da tag.
4. **Fichas e coerência (EDR-061).** Colunas novas na 03_TARGETS (H:Q, catálogo abaixo); linhas 10 e 11 = TARGET-006 e 007; as notas A11 e A12 descem para A14 e A15. Estado de coerência pela ordem de regras, a primeira que bate decide:
   1. campo fora do vocabulário (Papel, Ciclo de vida, Congelamento) → `CONFLITO: <campo> fora do vocabulário`;
   2. Papel = META e outra META na mesma alavanca → `CONFLITO: sobredeterminação (<alavanca>; escolha qual manda)` (spec §5 itens 1b e 2);
   3. Papel = TBD ou Target = TBD/vazio → `NÃO AVALIÁVEL: meta sem valor ou papel (TBD)` (extensão do NÃO AVALIÁVEL da spec §4.4 a meta sem valor: "COERENTE" numa meta vazia diria "ok" onde nada foi avaliado, §5 item 8);
   4. Compromisso declarado preenchido: com EDR no formato `EDR-ddd` → `COMPROMISSO DECLARADO`; sem EDR ou fora do formato → `CONFLITO: compromisso sem EDR` (spec §5 item 1c);
   5. senão → `COERENTE (regras avaliadas: vocabulário e sobredeterminação)`. O efeito no objetivo, a malha fechada e o custo ficam para o incremento 7 (spec §10).
   O texto final é `<estado> · <pior origem da grandeza>` (spec §4.4). Que o EDR citado existe e está aprovado é conferido fora da planilha (`conferir_viva` e TC-WB42-001), porque uma cópia do status do EDR na planilha envelheceria em silêncio. Pior coerência no dashboard: CONFLITO > NÃO AVALIÁVEL > COMPROMISSO DECLARADO > COERENTE.
5. **Alavanca por relação, não digitada.** A coluna Alavanca da 03_TARGETS é fórmula sobre a tabela de relações da 23_LISTAS (uma fonte só, spec §5 item 8). Alavancas: TARGET-001 "mola dianteira", 002 "mola traseira", 003/006/007 "distribuição de rolagem λ_f (barras)", 004 "geometria dianteira (anti-dive)", 005 "geometria traseira (anti-squat)". Com isso a regra 2 da spec ("com meta de K ou de limite, o λ_f passa a CONSEQUÊNCIA") sai da regra geral de sobredeterminação, sem caso especial.
6. **Valores iniciais** (nenhum inventado): Papel `TBD` nas 7 fichas; Ciclo de vida OPEN nas 5 atuais (como hoje) e TBD nas 2 novas (sem discussão aberta); Congelamento F0; Target `TBD`; Owner `TBD`; compromisso, EDR do compromisso e objetivo vazios ("TBD"). Coerência inicial das 7: NÃO AVALIÁVEL.
7. **Congelamento F0-F4 (EDR-034).** Decisão proposta: adotar os níveis F0-F4 do Guia §3.2 com a promoção proporcional ao uso (§3.12) e os critérios de descongelar (§3.13); vale para fichas de meta e para parâmetros, ao lado (nunca no lugar) do Lifecycle. O status do EDR-034 passa de AWAITING_DECISION a APPROVED com a autorização do usuário.
8. **`equilibrio.veredito_robusto` (EDR-060 item 8 x).** Manter a regra estrita (mistura com N/A = NÃO CONCLUSIVO): a spec §7.6 item 3 só mostra o veredito quando ele "for o mesmo em toda a varredura", e um ponto N/A não tem veredito. Corrigir o **motivo**, que hoje diz "o sinal depende do pneu" também quando não houve inversão: PUSH e LOOSE juntos, ou NEUTRO em algum ponto → `o sinal depende do pneu`; um só sinal misturado com N/A → `N/A em parte da varredura (sem inversão de sinal)`. `texto_veredito` passa a mostrar `? NÃO CONCLUSIVO: <motivo>`. Nota na spec §7.6 item 3. O relatório do incremento 4 não é regenerado (é evidência da V4.1).
9. **Deferidas do incremento 4:** emenda da h7 na 21_COBERTURA F12 (texto da spec §7.4); teste do κ do pico de Fx fora da forma fechada (decisão 4 do EDR-060) no TC-WB42-005; linha no EDR-060 item 8 (xi) sobre `angulos_necessarios` (grade de 401 pontos) × planilha (25 colunas de α): perto da saturação pode dar N/A de um lado, nunca outra raiz; medição do recálculo da V4.1 sem Excel residual (Task 6).

## Autorizações a pedir antes de executar (CLAUDE.md)
1. **IDs de meta:** TARGET-006 "Gradiente de subesterço K (SUS-1001)" e TARGET-007 "Comportamento no limite: push/loose e C_N (SUS-1004)" (spec §11), ambos TBD.
2. **EDRs novos:** EDR-061 "Processo de metas e coerência (V4.2)" (decisões 4-6); EDR-062 "Projeto T11: Origens e prefixo D16" (decisões 1-2); EDR-063 "Viva da equipe no Drive: conferência, retrato por nome e troca a cada versão" (decisão 3). **EDR-034 decidido** com F0-F4 (decisão 7). **EDR-060** item 8: (x) resolvido pela decisão 8, (xi) acrescentado.
3. **IDs de teste** TC-WB42-001 a 006 (tabela "Contagem de testes").
4. **Fórmulas novas**, por família (catálogo G1-G6).
5. **Alterações em células existentes** (antes e depois no registro de células):
   - (a) rótulos de origem da decisão 1: 00_README A43:A44 e B43:D44 (significado), as células de Origem e a coluna oculta H com `● Dado do TX`/`◐ Dado do T09` (34 células na V4.1: 05_VEHICLE 16, 06_SUSPENSION 16, 00_README 2) e os textos explicativos que citam `● Dado do TX` ou "Dado do TX" (00_README, 14_DASHBOARD A40, 16_EQUILIBRIO A2, 20_EQ_TROCA A2, 22_CADEIA A2);
   - (b) **fórmulas existentes** 16_EQUILIBRIO B188 (K) e B189 (veredito): o literal `"● Dado do TX"` do `EXACT` passa a `"● Dado do T11"`; nada mais muda nelas;
   - (c) 03_TARGETS: A11 e A12 descem para A14 e A15; A3 e cabeçalho H4:Q4; linhas 10 e 11 novas;
   - (d) 21_COBERTURA F12: emenda da h7;
   - (e) 00_README A3 (V4.2) e a linha 22 do 15_CHANGELOG.

## Global Constraints
- A V4.2 parte do arquivo `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` da tag `v4.1` (`git show v4.1:…`), numa pasta temporária. Saída em `build/`; a cópia para `excel/` é um commit próprio (Task 7). Nenhuma ferramenta salva ou recalcula a viva do Drive nem a de referência; ferramentas leem a viva só por cópia local.
- As 117569 fórmulas da V4.1 ficam com texto idêntico, salvo B188 e B189 da 16_EQUILIBRIO. Os 1145 nomes da V4.1 ficam iguais.
- Aba nova `23_LISTAS` no fim (depois da 22_CADEIA). Linhas novas do 14_DASHBOARD: 49 (título), 50 (pior coerência), 51 (compromissos declarados).
- Toda entrada nova tem nome `ent_03_*` (regras de nome do EDR-058) e entra em `aba_metas.celulas_de_entrada_v42()` = `celulas_de_entrada_v41()` ∪ 03_TARGETS {C:G das linhas 10-11} ∪ {H, J, M, N, Q das linhas 5-11}. Todo resultado novo tem nome `res_03_*` ou `res_14_*`, em `data/nomes_V4_2.csv`. Listas de vocabulário têm nome definido como `Origens` (fora do CSV): `Lista_Papel`, `Lista_Ciclo_Meta`, `Lista_Congelamento`, `Lista_Coerencia`; validação de dados nas entradas com lista.
- Vocabulários exatos: Papel {`META`, `CONSEQUÊNCIA`, `TBD`}; Ciclo de vida da meta (G.1) {`TBD`, `OPEN`, `PROPOSED`, `APPROVED`, `FROZEN`, `STALE`}, com o significado do Guia; Congelamento {`F0`…`F4`}, com significado e uso do Guia §3.2; Coerência {`COERENTE`, `COMPROMISSO DECLARADO`, `CONFLITO`, `NÃO AVALIÁVEL`}; Fonte {`L`, `E`, `M`}.
- Relação sem fonte não existe. L = livro e página já citados na spec e conferidos na imagem do PDF (`references/pdf/`); se a página não se confirmar, a relação fica só com a fonte M. E = EDR existente e APPROVED. M = nome do resultado e nome da entrada da alavanca, e a entrada tem de ser raiz do resultado no grafo (`raizes.Grafo`).
- Textos de exibição iguais aos do oráculo (`metas.texto_coerencia`). Nada de valor-alvo inventado: toda meta continua TBD (03_TARGETS A11 vigente).
- Branch `feat/v4-2-inc5-metas` (da ponta de `main`, 440b64a). Commits separados por propósito (código, cópia para `excel/`, documentação), com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Durante as tarefas, teste de planilha só no Excel; LibreOffice só na suíte final (Task 7).
- Implementadores e revisões de tarefa em Sonnet; revisão final num despacho em Opus.

## Catálogo de fórmulas novas (aprovação por família)
| # | Onde | Fórmula (forma) | Oráculo |
|---|---|---|---|
| G1 | 03_TARGETS I5:I11 (Alavanca) | `INDEX(<coluna Alavanca das relações>, MATCH(A<r>, <coluna Meta das relações>, 0))`, com IFERROR → "sem relação na 23_LISTAS" | `metas.RELACOES` |
| G2 | 03_TARGETS K5:K11 (Valor atual do modelo) e L5:L11 (Pior origem) | `=nome` do resultado da grandeza (SUS-205 F/R, SUS-208, SUS-301, SUS-302, `res_16_k_total` em °/g, texto do veredito no limite) e da célula de pior origem já existente (14_DASHBOARD coluna E ou 16_EQUILIBRIO coluna E) | REF |
| G3 | 03_TARGETS, auxiliares ocultas R:T | vocabulário: `ISNUMBER(MATCH(<campo>, Lista_*, 0))` para Papel, Ciclo, Congelamento | `metas.campo_valido` |
| G4 | 03_TARGETS, auxiliar oculta U | outras METAs na alavanca: `COUNTIFS($I$5:$I$11, I<r>, $H$5:$H$11, "META") - (H<r>="META")` | `metas.sobredeterminadas` |
| G5 | 03_TARGETS O5:O11 (Coerência) | cadeia IF da decisão 4, `& " · " & L<r>`; formato do EDR por `AND(LEN(N<r>)=7, LEFT(N<r>,4)="EDR-", ISNUMBER(--MID(N<r>,5,3)))` | `metas.estado_coerencia`, `metas.texto_coerencia` |
| G6 | 14_DASHBOARD B50 e B51 | pior coerência pela ordem da decisão 4 (`IF(COUNTIF(O5:O11,"CONFLITO*")>0,…)`); `COUNTIF(O5:O11,"COMPROMISSO DECLARADO*")` | `metas.pior_coerencia` |

Fora das famílias: textos fixos da 23_LISTAS e de `docs/metas/`, as alterações do item 5 e as listas da 23_LISTAS.

Colunas da 03_TARGETS (cabeçalho na linha 4): H Papel (entrada, lista), I Alavanca (G1), J Congelamento (entrada, lista), K Valor atual do modelo (G2), L Pior origem da grandeza (G2), M Compromisso declarado (entrada, texto), N EDR do compromisso (entrada, texto), O Coerência (G5), P Ficha (texto `docs/metas/TARGET-00x.md`), Q Objetivo atendido (entrada, texto; "TBD: lista de objetivos da equipe a definir em EDR", spec §4.1).

## Contagem de testes (poucos checks, asserções agrupadas)
| Check | O que junta | Script |
|---|---|---|
| TC-WB42-001 | estrutura: abas e ordem (+23_LISTAS); 117569 fórmulas da V4.1 idênticas fora de B188/B189; nenhum rótulo antigo fora do 04 e do 15; dados de origem mapeados para "outro carro"; nomes (1145 antigos iguais, novos válidos e únicos); entradas novas em `celulas_de_entrada_v42()` com validação; toda relação com fonte válida (L na lista conferida, E existente e APPROVED no EDR, M com a entrada como raiz do resultado); toda célula nova numa família G1-G6 | `tests/test_v4_2.py` |
| TC-WB42-002 | CA-07 da V4.2: duas regenerações idênticas e, se existir, igual a `excel/…V4_2.xlsx` (com nomes); recusas do gerador (saída em `excel/`, saída = origem) | `tests/test_v4_2.py` |
| TC-WB42-003 | oráculo `metas.py`: cada estado de coerência forçado; ordem das regras; 7 METAs ao mesmo tempo (Review Focus 5); EDR em formato inválido (`EDR-61`, `edr-061`); pior coerência e contador | `tests/test_v4_2.py` |
| TC-WB42-004 | fluxo da viva sem motor: `migrar_viva` (dado mantido, rótulo mapeado, conflito listado e não sobrescrito, célula fora dos nomes = código 2); `conferir_viva` (viva fiel 0, fórmula trocada 1, arquivo ausente ou de 0 byte 3; EDR citado inexistente = 1); `retrato_viva` ida e volta (JSON → injetar → mesmos dados) | `tests/test_v4_2.py` |
| TC-WB42-005 | motor: 0 erros; equivalência por valor com a V4.1 em todo `res` antigo (as duas versões mostram "DEMONSTRATIVO" com as entradas nominais); cópia com todas as origens `● Dado do T11` → sem prefixo em K e veredito, igual a `texto_k`/`texto_veredito` com `origem_do_carro=T11`; cópia com `● Dado do TX` colado numa Origem → pior origem `? A confirmar` e prefixo; cópia com h9 ligada e KPUMAX abaixo do κ do pico → N/A "pico de Fx fora da forma fechada"; tempo de recálculo no log | `tests/test_workbook_v4_2.py` |
| TC-WB42-006 | coerência na planilha × `metas.py` em uma cópia com as 7 fichas preenchidas para forçar os 4 estados (inclusive campo fora do vocabulário colado, duas METAs na alavanca λ_f, compromisso com e sem EDR), mais o dashboard (B50, B51) | `tests/test_workbook_v4_2.py` |

Esperado no fim: `test_v4_2.py` 4/4, `test_workbook_v4_2.py` 2/2; `test_equilibrio.py` 28/28 e `test_equilibrio_linear.py` 18/18 (asserções estendidas, sem check novo). Sem mutação nova: o TC-WB42-006 força cada estado contra o oráculo.

## Review Focus
1. **Rótulo antigo colado na viva** (alguém cola `● Dado do TX` de outra planilha). Esperado: a validação recusa na digitação; colado, o MATCH falha e conta como `? A confirmar` (o pior), nunca como dado do T11. Teste: TC-WB42-005.
2. **Viva do Drive bloqueada ou "só online"** (arquivo aberto por alguém, placeholder do Drive de 0 byte, H: desmontado). Esperado: as ferramentas copiam antes de ler e saem com código 3 e mensagem; nunca PASS, nunca gravação no Drive. Teste: TC-WB42-004.
3. **EDR do compromisso digitado errado** (`EDR-61`, `edr-061`, `EDR-999` inexistente). Esperado: formato errado → CONFLITO na planilha; inexistente ou não aprovado → `conferir_viva` código 1 com a linha. Teste: TC-WB42-003, 004 e 006.
4. **Migração com a mesma célula mudada pela equipe e pela V4.2** (Origem mapeada pela decisão 1 e trocada pela equipe; valor que a V4.2 também mudou). Esperado: os valores `org_` são mapeados antes da comparação; dado da equipe = valor da viva diferente da referência da V4.1 mapeada; se a V4.2 também mudou essa célula em relação à V4.1 mapeada, é conflito listado, nunca sobrescrito. Teste: TC-WB42-004.
5. **Papel META nas 7 fichas de uma vez.** Esperado: 003, 006 e 007 em CONFLITO de sobredeterminação (λ_f); 001, 002, 004 e 005 NÃO AVALIÁVEL (Target TBD); dashboard B50 = CONFLITO. Teste: TC-WB42-003 e 006.

---

### Task 1: Origens do T11 e textos do Python (sem planilha nova)

**Files:**
- Create: `python/origens.py`
- Modify: `python/equilibrio.py` (`veredito_robusto`, `texto_veredito`), `python/equilibrio_linear.py` (`texto_k`), `python/aba_equilibrio.py` (`pior_origem_de_valores`), `python/caso_planilha.py` (callers de pior origem, se usarem `ORIGENS_LISTA`)
- Modify (callers da V4.1): `tests/test_workbook_v4_1.py`, `tools/relatorio_inc4.py`, `tools/relatorio_inc1.py`
- Test: `tests/test_equilibrio.py`, `tests/test_equilibrio_linear.py` (estender os checks que já cobrem `veredito_robusto`, `texto_veredito` e `texto_k`; achar com `grep -n "veredito_robusto\|texto_veredito\|texto_k" tests/`)

**Interfaces:**
- Produces: `origens.TX_V41 = "● Dado do TX"`, `origens.T09_V41 = "◐ Dado do T09"`, `origens.T11 = "● Dado do T11"`, `origens.OUTRO_CARRO = "◐ Dado de outro carro (TX, T09)"`, `origens.ORIGENS_V42 = (T11, OUTRO_CARRO, TTC, EST, ARB, CONF)` (os 4 últimos importados de `atualizar_planilha`), `origens.MAPA_DADO_V41_V42 = {TX_V41: OUTRO_CARRO, T09_V41: OUTRO_CARRO}`, `origens.MAPA_REGRA_V41_V42 = {TX_V41: T11}`, `origens.SIGNIFICADO_V42: dict[str, tuple[str, str]]` (texto da 00_README B:D e E para T11 e OUTRO_CARRO; os outros iguais a `atualizar_planilha.SIGNIFICADO`).
- Produces: `texto_veredito(res, pior_origem, robusto=None, *, origem_do_carro=origens.T11)`, `texto_k(..., *, origem_do_carro=origens.T11)`; `veredito_robusto(vereditos) -> (veredito, motivo)` com os motivos da decisão 8; `pior_origem_de_valores(termos, origem_de, chaves, lista=ORIGENS_LISTA)`.

- [ ] **Step 1:** Estender os checks: `texto_veredito(..., pior_origem=T11)` sem prefixo e com `TX_V41` com prefixo; `origem_do_carro=TX_V41` reproduz o comportamento antigo; `veredito_robusto([LOOSE, NA, LOOSE]) == (NAO_CONCLUSIVO, "N/A em parte da varredura (sem inversão de sinal)")`; `veredito_robusto([PUSH, LOOSE])[1] == "o sinal depende do pneu"`; `veredito_robusto([PUSH, NEUTRO])[1] == "o sinal depende do pneu"`; `texto_veredito` com robusto NÃO CONCLUSIVO = `"? NÃO CONCLUSIVO: " + motivo` (com o prefixo D16 quando couber). `tests/test_equilibrio.py` e `tests/test_equilibrio_linear.py` falham.
- [ ] **Step 2:** Implementar; passar `origem_do_carro=origens.TX_V41` nos callers da V4.1 (o texto que eles geram não muda).
- [ ] **Step 3:** `uv run python -X utf8 tests/test_equilibrio.py` → `28 PASS, 0 FAIL, de 28 testes`; `tests/test_equilibrio_linear.py` → 18/18; `tests/test_workbook_v4_1.py` (Excel) → 5/5.
- [ ] **Step 4:** Commit `feat(v4.2): origens do T11 e motivo do NÃO CONCLUSIVO (EDR-062, EDR-060)`.

### Task 2: Gerador da V4.2 com as alterações aprovadas (sem metas ainda)

**Files:**
- Create: `python/gerar_v4_2.py`, `tests/test_v4_2.py`, `data/nomes_V4_2.csv` (cabeçalho só, nesta tarefa)
- Modify: `tools/rodar_testes.py` (TESTES: `tests/test_v4_2.py` com a contagem da tarefa; MODULOS: `origens`, `gerar_v4_2`)

**Interfaces:**
- Consumes: `origens.*` (Task 1); padrão de `gerar_v4_1.py` (extração da tag, `_recusar`, `escrever_registro`).
- Produces: `gerar_v4_2.gerar(v41: Path | None, saida: Path, registro: Path | None) -> None`; `gerar_v4_2.alteracoes_v4_2(wb) -> list[dict]` (aba, cel, antes, novo, ref); CLI `python/gerar_v4_2.py [--v41 ARQ] [--saida build/FSAE_EV_Suspension_Fase1_V4_2.xlsx] [--registro docs/registro-de-versoes-V4_2-celulas.md] [--nomes-csv data/nomes_V4_2.csv]`; `REGISTRO = "docs/registro-de-versoes-V4_2-celulas.md"`.

- [ ] **Step 1:** Escrever em `tests/test_v4_2.py` o TC-WB42-001 (parte desta tarefa: abas e ordem; 117569 fórmulas iguais fora de 16_EQUILIBRIO B188/B189, e nelas só o literal trocado; nenhuma ocorrência de "Dado do TX" nem "Dado do T09" em valor, fórmula, validação ou regra de formatação condicional fora do 04_DECISION_REGISTER e do 15_CHANGELOG, exceto dentro de `OUTRO_CARRO`; as 34 células de dado com `OUTRO_CARRO`; 00_README A43:A48 == `ORIGENS_V42`; `Origens` ainda `'00_README'!$A$43:$A$48`; 1145 nomes iguais; 21_COBERTURA F12 com a emenda da h7; A3 com "V4.2") e o TC-WB42-002 (duas regenerações iguais pelo `comparar_planilhas.comparar_xlsx(..., estrutura=True)`; igual a `excel/…V4_2.xlsx` se existir; recusas). Rodar: falha (gerador não existe).
- [ ] **Step 2:** Implementar `gerar_v4_2.py`: substituição de **dado** só em células de Origem (colunas E e H das abas de `ABAS_ORIGEM`, I da 10_TIRE, E da 16_EQUILIBRIO) com o valor exatamente igual a um rótulo antigo; substituição de **regra** nos textos e nos dois literais do D16; 00_README A43:D44 por `SIGNIFICADO_V42`; cada célula alterada no registro com antes e depois. Texto da h7 (F12): o da spec §7.4 linha 7 ("Sim (entrada, 0 até medir; um sentido por vez, pela entrada "Sentido da curva": o outro se vê trocando o sentido; EDR-060, 2026-10-22)").
- [ ] **Step 3:** `uv run python -X utf8 tests/test_v4_2.py` → `2 PASS, 0 FAIL, de 2 testes`.
- [ ] **Step 4:** Commit `feat(v4.2): gerador da V4.2 a partir da tag v4.1, origens do T11 e D16 (EDR-062)`.

### Task 3: Oráculo e fichas na planilha (metas.py, aba_metas.py)

**Files:**
- Create: `python/metas.py`, `python/aba_metas.py`, `tests/test_workbook_v4_2.py`
- Modify: `python/gerar_v4_2.py` (chama `aba_metas.montar(wb)`, nomes de `aba_metas.NOMES_V42`), `data/nomes_V4_2.csv`, `tests/test_v4_2.py` (TC-WB42-001 completo, TC-WB42-003), `tools/rodar_testes.py` (PLANILHAS: `tests/test_workbook_v4_2.py`, 2; MODULOS: `metas`, `aba_metas`)

**Interfaces:**
- Produces (`metas.py`): `VOCAB: dict[str, tuple[str, ...]]` (chaves `papel`, `ciclo`, `congelamento`, `coerencia`, `fonte`); `@dataclass(frozen=True) Relacao(n: int, tipo: str, meta: str, alavanca: str, fonte_tipo: str, fonte: str, resultado: str | None, entrada: str | None)`; `RELACOES: tuple[Relacao, ...]`; `@dataclass Ficha(target: str, valor: object, papel: object, ciclo: object, congelamento: object, compromisso: object, edr: object, pior_origem: str)`; `alavanca(target) -> str | None`; `campo_valido(campo: str, valor) -> bool`; `edr_no_formato(v) -> bool`; `sobredeterminadas(fichas: list[Ficha]) -> set[str]`; `estado_coerencia(f: Ficha, fichas: list[Ficha]) -> tuple[str, str]` (estado, motivo); `texto_coerencia(f, fichas) -> str` (texto exato de G5); `pior_coerencia(textos: list[str]) -> str`; `compromissos(textos) -> int`.
- Produces (`aba_metas.py`): `montar(wb) -> list[dict]` (registro); `NOMES_V42: list[Nome]`; `LISTAS_V42: dict[str, str]` (nome → referência); `celulas_de_entrada_v42() -> set[tuple[str, str]]`; `LINHA_TARGET = {"TARGET-001": 5, …, "TARGET-007": 11}`; `fichas_da_planilha(xlsx_recalculado: Path) -> list[metas.Ficha]`.
- Relações (decisão 5; `n` interno, sem prefixo REL-): uma por meta (tipo `alavanca`), M com o resultado da grandeza (SUS-205 F/R no 11_DESIGN, que já deriva a mola do alvo de frequência; SUS-208 λ_f; SUS-301/302; `res_16_k_total`; veredito no limite) e a entrada da alavanca (mola F/R, K_ARB dianteiro, entradas de geometria do anti-dive/anti-squat), achadas pelo grafo; para 006 também L "Gillespie p. 214" e para 007 L "Milliken §7.1, p. 283-286", **só** se a página se confirmar na imagem do PDF; uma relação tipo `regime` (006 × 007, L "Milliken p. 313-315": subesterço linear com loose no limite não é erro), informativa, fora das fórmulas.

- [ ] **Step 1:** TC-WB42-003 em `tests/test_v4_2.py` com as asserções da tabela de testes e do Review Focus 3 e 5 (valores exatos: por exemplo `estado_coerencia` com Papel "meta" minúsculo → `("CONFLITO", "Papel fora do vocabulário")`; 7 METAs → `sobredeterminadas == {"TARGET-003", "TARGET-006", "TARGET-007"}`). Falha.
- [ ] **Step 2:** Implementar `metas.py`. Rodar o TC-WB42-003: passa.
- [ ] **Step 3:** Estender o TC-WB42-001 (23_LISTAS e as quatro listas com nome; 03_TARGETS H4:Q4 e linhas 10-11; A14/A15 com as notas antigas; validação nas entradas com lista; famílias G1-G6; fontes das relações: L na lista conferida `metas.FONTES_L` e presente na spec; E existente e APPROVED; M com `entrada` entre as raízes de `resultado`; nomes novos). Falha.
- [ ] **Step 4:** Implementar `aba_metas.py` e ligar no gerador. TC-WB42-001 e 002 passam.
- [ ] **Step 5:** `tests/test_workbook_v4_2.py` com o TC-WB42-006 (Excel): uma cópia, 7 fichas preenchidas para cobrir os 4 estados; `metas.texto_coerencia` igual à O5:O11 recalculada; B50/B51 iguais a `pior_coerencia`/`compromissos`. Passa no Excel.
- [ ] **Step 6:** Commit `feat(v4.2): fichas de meta, 23_LISTAS e estados de coerência (EDR-061)`.

### Task 4: Equivalência e D16 no motor; κ do pico

**Files:**
- Modify: `tests/test_workbook_v4_2.py` (TC-WB42-005)

**Interfaces:**
- Consumes: `caso_planilha.caso_da_planilha_v41` (a V4.2 tem as mesmas entradas da 16), `equilibrio.texto_veredito`/`equilibrio_linear.texto_k` com `origem_do_carro`, `aba_equilibrio.pior_origem_de_valores(..., lista=ORIGENS_V42)`.

- [ ] **Step 1:** TC-WB42-005 com as asserções da tabela (equivalência com a V4.1 recalculada em todo `res` dos 1145 nomes; três cópias: todas as origens T11; `● Dado do TX` colado numa Origem da 05_VEHICLE; h9 ligada com R, CdA, Crr, ρ de teste e KPUMAX = 0,05 < κ do pico). Os três casos numa recalculada só quando não interferem (o h9 muda o veredito: cópia própria).
- [ ] **Step 2:** Rodar no Excel: `2 PASS, 0 FAIL, de 2 testes`. Se um caso falhar por defeito do gerador, corrigir no gerador (Task 2/3) e registrar.
- [ ] **Step 3:** Commit `test(v4.2): equivalência com a V4.1, D16 do T11 e κ do pico (TC-WB42-005)`.

### Task 5: Viva no Drive (conferir, retrato, migrar) e CA-07

**Files:**
- Create: `python/viva.py`, `tools/conferir_viva.py`, `tools/retrato_viva.py`, `tools/migrar_viva.py`, `data/viva/.gitkeep`
- Modify: `tools/comparar_planilhas.py` (`comparar_viva(..., rotulos=ROTULOS_ORIGEM, esperadas=…)`), `tools/rodar_testes.py` (CA-07 da decisão 3a e 3b; V4.2 na regeneração), `tests/test_v4_2.py` (TC-WB42-004)

**Interfaces:**
- Produces (`viva.py`): `PASTA_DRIVE = Path(r"H:\.shortcut-targets-by-id\1Kytf4APy0OtH5Aq5PqlOwH5UY65YMX5U\T11 - Tupã\2. Projeto\Mecanica\Suspensao\Documentacao\Planilha DDS")`; `localizar_viva() -> Path | None` (variável `DDS_VIVA` primeiro; senão o único `FSAE_EV_Suspension_Fase1_V*.xlsx` da pasta; mais de um → `ValueError`); `class VivaIlegivel(Exception)`; `copia_local(viva: Path, pasta: Path) -> Path` (0 byte, bloqueio ou erro de leitura → `VivaIlegivel`); `versao(xlsx: Path) -> str` (de 00_README A3, "V4.1"); `@dataclass Referencia(versao, tag, caminho_excel, entradas: Callable[[], set], rotulos: tuple[str, ...], formulas: int)`; `REFERENCIAS = {"V4.1": …, "V4.2": …}`; `arquivo_de_referencia(versao, pasta) -> Path` (blob da tag; sem a tag, o de `excel/`); `edrs_citados(xlsx) -> list[tuple[str, str]]` (célula, EDR) da 03_TARGETS N5:N11 e F5:F11; `edrs_aprovados(edr_md: Path) -> dict[str, str]` (ID → status).
- CLIs: `conferir_viva.py [ARQ]` (0/1/3; imprime o relatório; nunca grava fora de `build/`); `retrato_viva.py [ARQ] [--saida data/viva/retrato-viva.json]` (exige conferência 0; JSON: `{"versao", "sha256", "data", "dados": {nome: valor}}`, chaves ordenadas, uma por linha); `migrar_viva.py VIVA --para REF_NOVA.xlsx [--saida build/<nome>_com_dados.xlsx]` (relatório em `build/migracao-viva.md`; 0 ok, 1 conflito, 2 célula alterada fora dos nomes ou objeto não migrável, 3 ilegível; usa `dados_planilha.ler_por_nome`, `celulas_alteradas`, `objetos_alterados` e `injetar` com a base = referência da versão da viva mapeada por `MAPA_DADO_V41_V42`).

- [ ] **Step 1:** TC-WB42-004 com as asserções da tabela e do Review Focus 2 e 4, sobre cópias em pasta temporária (a "viva" de teste é a V4.1 da tag com dados de teste injetados; `DDS_VIVA` aponta para ela). Falha.
- [ ] **Step 2:** Implementar `viva.py` e as três CLIs; `comparar_viva` com `rotulos` e a conferência de EDR para a V4.2.
- [ ] **Step 3:** `rodar_testes.py`: trocar o CA-07 da viva V3.0 por "V3.0 de excel/ = tag v3.0 (SHA-256)" no resumo; seção "Viva da equipe (informativo, EDR-063)" no log, com `conferir_viva` sobre a viva localizada (ou NÃO EXECUTÁVEL), fora do resumo; regeneração da V4.2 comparada com `excel/` quando existir.
- [ ] **Step 4:** `uv run python -X utf8 tests/test_v4_2.py` → `4 PASS, 0 FAIL, de 4 testes`; `uv run python -X utf8 tools/conferir_viva.py` sobre a viva real do Drive (só leitura) → código 0 (é a cópia da V4.1).
- [ ] **Step 5:** Commit `feat(v4.2): viva no Drive: conferência, retrato por nome e migração (EDR-063)`.

### Task 6: Medição do recálculo da V4.1 sem Excel residual

**Files:**
- Create: `tools/medir_recalculo.py`, `docs/v4-2/medicao-recalculo-v4-1.md` (gerado)

**Interfaces:**
- Consumes: `tests/recalculo_planilha.py` (abrir, recalcular e gravar pelo COM).
- Produces: CLI `tools/medir_recalculo.py [ARQ] [--n 3] [--saida docs/v4-2/medicao-recalculo-v4-1.md]`: conta os processos `EXCEL.EXE` antes (se houver, avisa e mede assim mesmo, registrando o número); por execução, numa instância nova, mede separado abrir, `CalculateFull`, gravar e fechar; confere que a instância saiu; grava a tabela com vírgula decimal e `newline="\n"`.

- [ ] **Step 1:** Implementar e rodar com `--n 3` sobre uma cópia da V4.1 da tag. Esperado: tabela com os quatro tempos por execução e a contagem de EXCEL.EXE antes e depois.
- [ ] **Step 2:** Commit `tools: medição do recálculo da V4.1 sem Excel residual`.

### Task 7: Documentação, cópia para excel/ e suíte final (controlador)

**Files:**
- Create: `docs/metas/README.md` (três níveis, G.3, F.3, ficha, os quatro grupos de estados com F0-F4, lógica entre fichas §5, coerência da decisão 4), `docs/metas/TARGET-001.md` … `TARGET-007.md` (campos da spec §4.3; valor TBD; método com página só onde conferida; "sem faixa na literatura" onde não houver), `docs/registro-de-versoes-V4_2.md`, `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx` (cópia do `build/`, commit próprio)
- Modify: `docs/Engineering_Decision_Register.md` (EDR-034, 060, 061, 062, 063; índice), spec (§7.6 item 3, nota; §8.2, nota sobre a viva no Drive), `CLAUDE.md` (Situação atual, Comandos, contagens), `tools/rodar_testes.py` (contagens finais)

- [ ] **Step 1:** Escrever os documentos e passar o texto em português pelo `humanizer-pt`.
- [ ] **Step 2:** Gerar a V4.2 em `build/`, copiar para `excel/`; commit `excel: V4.2 de referência`.
- [ ] **Step 3:** `uv run python -X utf8 tools/rodar_testes.py` (Excel) → todos os itens do resumo PASS; depois `DDS_RECALC=libreoffice` nos scripts de planilha (V3.0 19/19 e 15/15, V4.0 2/2, V4.1 5/5, V4.2 2/2).
- [ ] **Step 4:** Revisão final (Opus, um despacho) sobre `main...HEAD`; correções; commit; push e PR (`gh pr create`), com o pedido de merge e tag ao usuário.

### Task 8: Troca da viva no Drive (depois do merge e da tag `v4.2`, a pedido do usuário)

- [ ] **Step 1:** `tools/conferir_viva.py` → 0; `tools/retrato_viva.py` → commit `dados: retrato da viva V4.1 AAAA-MM-DD` se houver dado da equipe.
- [ ] **Step 2:** `tools/migrar_viva.py <viva> --para excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx` → código 0 (com 1, mostrar os conflitos ao usuário e parar).
- [ ] **Step 3:** Avisar o usuário do que vai mudar; mover a V4.1 do Drive para `Planilha DDS\_anteriores\` e gravar a V4.2 com os dados em `Planilha DDS\`; `tools/conferir_viva.py` → 0 na nova; atualizar o `CLAUDE.md` (viva = V4.2).
