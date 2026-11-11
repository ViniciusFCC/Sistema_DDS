# Incremento 9 (pendências do inc. 8, regras da competição, coerência completa e V5.0) — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** fechar as pendências do inc. 8 (9a), preparar em Python as fontes e os oráculos da V5.0 — regulamento 2027
provisório, parcela de tração no K, coerência completa, chave 0, CA-07 por texto, contador por Origem (9b) — e gerar a V5.0
a partir da tag `v4.4`, em dois passes conferidos separadamente (9c).

**Architecture:** a 9a só mexe em ferramentas e testes, sem valor novo. A 9b acrescenta `python/regulamento.py` com
`data/regulamento.csv`, a função da parcela de tração em `python/equilibrio_linear.py`, as regras novas em
`python/metas.py`, `python/ca07_texto.py` e `python/origens.py`, e termina num relatório para o passo do usuário. A 9c
acrescenta `python/nomes_v5_0.py` e `python/gerar_v5_0.py`, este com `passe_estrutura` e `passe_fisica` em blocos
nomeados, e os testes `tests/test_v5_0.py`, `tests/test_workbook_v5_0.py` e `tests/mutation_planilha_v50.py`. Há uma
única suíte inteira, no fim.

**Tech Stack:** Python 3.13 (uv), openpyxl (`Tokenizer`), Excel via COM (`tests/recalculo_planilha.py`) com o LibreOffice de
reserva (EDR-044), testes em script com `check()` (não pytest).

**Spec:** `docs/superpowers/specs/2026-11-11-inc9-v5-0-coerencia-design.md` (commits fa2d041, 62c9671 e 5fe2dfb; a seção 11,
C1 a C10, vale sobre o resto). Entrada: `docs/passagem-2026-11-11.md`.

## Itens para a aprovação do usuário (antes da execução)

**Aprovação (usuário, 2026-11-11): A1 a A3 aprovados como estão.** D1 a D4 não foram revertidas. Os IDs da A2 estão
autorizados; os SUS continuam para o Task 15. Cada download da A3 ainda pede o "sim" na hora (nome, fonte, tamanho).

O plano só é executado depois que o usuário aprova A1 a A3. As decisões D1 a D4 são do controlador e ficam registradas
para o usuário saber; qualquer uma pode ser revertida na aprovação.

### A1. O ramo antigo do Python fica enquanto as referências V4.3 e V4.4 forem testadas (muda a U9 do inc. 7)

A U9 dizia que, na V5.0, sairiam o ramo antigo do Python e o do gerador. A leitura do código mostrou que os testes das
referências que a suíte continua rodando dependem desse ramo:
- `tests/test_workbook_v4_3.py`: o TC-WB43-003, chave 0 igual à V4.2, e o TC-WB43-004, células novas contra o Python
  com `formas`; mais os casos `H2V_0`, `H9V_0`, `CHAVE_H2V_*` e `GEO_*_H2V0`, nas linhas 725 a 738;
- `tests/test_v4_3.py`, linhas 205 a 334;
- `tests/mutation_planilha_v43.py`;
- o `DIR_CHAVE_H2V_VAZIA` do TC-WB44-006.

Tirar `FORMAS_V42` do Python quebra essas conferências, ou obriga a aposentá-las.

**Recomendação.** A chave 0 sai da **planilha V5.0** e do **gerador da V5.0**, que é o que a equipe vê. No Python,
`FORMAS_V42` fica, documentada como "só para as referências V4.3 e V4.4". Todo código novo da V5.0 passa a
`FORMAS_V43` de forma explícita, sem mudar o padrão das funções existentes; mudar esse padrão alteraria os 28 + 18
checks atuais.

O que cai por esta escolha é a linha "planilha" da escada, que usa as formas da V4.2, num relatório novo. A
aposentadoria do ramo no Python fica para quando a V4.3 e a V4.4 deixarem de ser testadas na suíte, numa decisão
própria.

**Alternativa recusada pelo controlador:** tirar o ramo e aposentar as conferências da V4.3 e da V4.4 que usam a
chave 0. A suíte perderia a regressão "V4.3 com chave 0 = V4.2", que a spec do inc. 7 (linha 159) chama de "a prova
mais forte".

Com a A1 aprovada, o C3 da spec (o teste de caracterização antes de apagar) perde o objeto: o ramo continua e o TC-WB43
segue rodando.

### A2. IDs a autorizar agora (spec §9 e C1 a C10)

| Tipo | IDs | Para quê |
|---|---|---|
| EDR | EDR-071 | Física do K: parcela de tração e escolha do estudo |
| EDR | EDR-072 | Coerência completa: malha fechada, custo, efeito no objetivo, motivos do NÃO AVALIÁVEL |
| EDR | EDR-073 | Regulamento 2027 provisório; fecha a condição do EDR-069 |
| EDR | EDR-074 | V5.0: retirada da chave 0 na planilha, CA-07 contra a V4.4, dois passes |
| TC | TC-REG-001 e 002 | `data/regulamento.csv` × nota de fontes; leitura por nome |
| TC | TC-KTR-001 a 003 | Oráculo da parcela de tração (sinais, vazio = V4.4, ponto de avaliação) |
| TC | TC-COE-001 a 004 | Oráculo da coerência (malha fechada, custo, motivos, efeito no objetivo) |
| TC | TC-ORG-001 | Contador por Origem |
| TC | TC-WB50-001 a 008 | Estrutura, CA-07, regeneração, migração, passe de estrutura, equivalência, cobertura e dependentes da V5.0 |

Os SUS (por volta de SUS-1012 a 1015) ficam para o passo do usuário (Task 15), porque dependem do estudo do K. TC-KTR,
TC-COE e TC-ORG não estavam na §9 da spec. O controlador os separou para não mudar as contagens dos testes que já
existem (equilíbrio linear 18, V4.2 4).

### A3. Downloads do regulamento (Task 5)

São quatro arquivos, todos para `references/regulamento/`, fora do Git:
1. o rascunho das FSAE Rules 2027, de `fsaeonline.com`;
2. o Rules Addendum V1.0 da FSAEB 2026;
3. o Handbook V2.1 da FSAEB 2026;
4. o Dynamic Events Procedures da FSAEB 2026.

Os três últimos vêm de `arquivos.saebrasil.org.br`.

O download é autorizado desde a U7 do inc. 7, mas cada arquivo ainda pede o "sim" do usuário na hora, com o nome, a
fonte e o tamanho. Isso segue a regra de segurança da sessão.

### Decisões do controlador (registradas)

- **D1. Função nova, sem mexer no K atual:** a parcela de tração é uma função à parte (`k_com_tracao`).
  `ParcelasK` e `parcelas_k` não mudam, o que mantém os 18 checks do equilíbrio linear.
- **D2. Contador num módulo próprio:** o contador por Origem fica em `python/origens.py`, e não em `metas.py`, porque
  não é coerência de meta.
- **D3. Quem faz a física:** as tarefas de física (Tasks 7, 8 e 10) são feitas pelo controlador da sessão. Isso segue a
  regra de custo, que permite só Sonnet nos subagentes, e substitui o "Opus nas tarefas de física" do §8 da spec. A
  revisão de cada tarefa continua num subagente Sonnet.
- **D4. Relatórios da escada:** o relatório da escada do inc. 6 (`docs/inc6/escada-hipoteses.md`) não é regravado. A
  escada da V5.0 vai para `docs/inc9/escada-v5.md`.

## Global Constraints

- **IDs:** os únicos IDs novos são os da A2, depois de aprovada. Os SUS só no Task 15.
- **Fórmulas existentes:** nenhuma fórmula ou texto existente da planilha muda sem estar num bloco aprovado no Task 15.
  Uma diferença fora do catálogo é FAIL, nunca uma exceção acrescentada depois.
- **Ambiente:**
  - `export UV_SYSTEM_CERTS=1` antes de todo `uv`;
  - nunca `python` ou `python3` direto;
  - um `uv run` por vez;
  - arquivos em LF;
  - o Excel se encerra só pelo PID dos processos próprios, nunca pelo nome.
- **Geração:** a V5.0 sai de `python/gerar_v5_0.py`, da tag `v4.4`, em `build/`, nunca em `excel/`. A cópia para
  `excel/` vai num commit próprio.
- **Viva e referências:**
  - a viva do Drive nunca é gravada, recalculada nem salva por ferramenta;
  - a V4.4 de `excel/` e a da tag só são lidas, ou copiadas para `build/`;
  - no LibreOffice, só cópias.
- **Valores sem fonte:** valor sem fonte fica "a confirmar". CdA, Crr e o valor real do setup começam vazios. Vazio dá
  exatamente o resultado da V4.4.
- **Valores sintéticos:** os casos sintéticos levam esse rótulo no log e nunca aparecem como resultado do carro. Toda
  célula de resultado nova que dependa de entrada DEMONSTRATIVA traz o prefixo D16 (spec V4.0 §7.3, item 7).
- **Regulamento:** o de 2027 é PROVISÓRIO até a versão final. Os documentos da FSAEB 2026 são PROVISÓRIOS até sair a
  edição 2027.
- **Tolerância:** zero no passe de estrutura contra a V4.4 (números, textos, booleanos e erros idênticos). Nunca
  afrouxar.
- **Commits:** separados por propósito (cópia, higiene, engenharia, documentação), cada um terminando com
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Testes durante o incremento:** só rodam os testes afetados. A suíte inteira roda uma vez, no Task 24, no Excel e no
  LibreOffice.
- **Ações com "sim" do usuário:** push, PR, merge, tag, download e escrita no Drive. Depois de gravar no Drive, conferir
  no navegador.
- **Subagentes:** só Sonnet, inclusive nas revisões.

## Review Focus

1. **Entrada nova vazia.** Com CdA, Crr e o valor real do setup vazios, a V5.0 tem de dar os mesmos valores da V4.4 em
   toda célula que já existia, e o K não pode virar 0 nem erro. Teste: TC-KTR-002 (Task 8) e TC-WB50-005, o passe de
   estrutura (Task 20).
2. **Viva com a chave mexida.** Uma viva com B9 = 0, B10 = 0 ou texto nas chaves tem de virar conflito listado na
   migração antes da troca, e não sumir em silêncio. Teste: TC-WB50-004 com uma viva sintética com B9 = 0 (Task 19).
3. **Texto colado em entrada numérica nova.** CdA = "0,9" como texto, ou Crr negativo, dá N/A com motivo e nunca um K
   numérico. Teste: caso dirigido no TC-WB50-006 (Task 20).
4. **Ficha sem target e sem setup ao mesmo tempo.** O motivo é o da precedência (TBD vem antes de setup), e o dashboard
   conta essa ficha uma só vez. Teste: TC-COE-003 (Task 9) e TC-WB50-006.
5. **R inválido ou ausente.** Sem R utilizável, o efeito no objetivo e o Δt dão N/A, nunca um número com R = 0. Teste:
   TC-COE-004 (Task 9) e um caso dirigido no TC-WB50-007 (Task 20).

## Arquivos por parte (C9) e ordem de merge

| Parte | Arquivos que cria ou muda | Não toca |
|---|---|---|
| 9a | `tools/rodar_testes.py`, `tests/test_executor.py`, `tests/test_v4_4.py`, `tests/test_workbook_v4_4.py`, `python/reescrita_nomes.py` (só docstring e testes), `python/nomes_v4_4.py`, `python/gerar_v4_4.py` (só a conferência do SHA), `tests/test_workbook_v4_3.py` (branch do TC-WB43-005) | `python/equilibrio*.py`, `python/escada.py`, `python/metas.py`, `python/aba_*.py`, `data/` |
| 9b | `python/regulamento.py`, `data/regulamento.csv`, `python/equilibrio_linear.py` (só adição), `python/equilibrio.py` e `python/escada.py` (minors T4, T5 e T9; linha da escada), `python/metas.py`, `python/ca07_texto.py`, `python/origens.py`, `tools/estudo_k_tracao.py`, `tests/test_regulamento.py`, `tests/test_k_tracao.py`, `tests/test_coerencia.py`, `tests/test_origens.py`, `tests/test_v4_3.py` (T9), `docs/regulamento/`, `docs/inc9/`, `docs/Engineering_Decision_Register.md` (triagem e rascunhos) | `excel/`, `tools/rodar_testes.py` (até o Task 23) |
| 9c | `python/nomes_v5_0.py`, `data/nomes_V5_0.csv`, `python/gerar_v5_0.py`, `python/aba_*.py` (funções novas, só por adição), `tests/test_v5_0.py`, `tests/test_workbook_v5_0.py`, `tests/mutation_planilha_v50.py`, `tools/rodar_testes.py`, `docs/registro-de-versoes-V5_0*.md`, `CLAUDE.md`, `excel/FSAE_EV_Suspension_Fase1_V5_0.xlsx` | — |

O merge segue esta ordem: os PRs da 9a, depois a 9b (um PR, com o relatório do passo), e por fim a 9c. A 9c parte de
uma `main` que já tem as duas anteriores.

---

# Parte 9a — pendências do inc. 8 (sessão S1, Sonnet; roda em paralelo com a S2)

### Task 1: branch do TC-WB43-005 atualizada e PR próprio

**Files:** branch `claude/adoring-morse-84a3d8` (commits ab2cb30, 3028748 e 2b9cd26); `tools/rodar_testes.py`,
`tests/test_executor.py` e `tests/test_workbook_v4_3.py`, conforme o merge.

- [ ] **Step 1:** numa worktree da branch, trazer `origin/main` (`git merge origin/main`). Num conflito em
  `tools/rodar_testes.py`, manter o `TIMEOUT_PLANILHAS` da `main`
  (`{"tests/test_workbook_v4_3.py": 7200, "tests/test_workbook_v4_4.py": 7200}`) e a regra da branch para o PULADO do
  TC-WB43-005.
- [ ] **Step 2:** `uv run python -X utf8 tests/test_executor.py` deve dar `1 PASS, 0 FAIL, de 1 testes`.
- [ ] **Step 3:** `DDS_RECALC=libreoffice uv run python -X utf8 tests/test_workbook_v4_3.py` deve dar 2 PASS e 1 PULADO,
  com o código de saída que o executor aceita. Depois o mesmo no Excel, que deve dar 3/3. O Excel roda em segundo
  plano, porque leva até 45 min.
- [ ] **Step 4:** commit do merge. **Push e PR só com o "sim" do usuário.** Descrição no padrão do PR #37, com o
  "🤖 Generated with [Claude Code](https://claude.com/claude-code)".

### Task 2: minors do executor e das ferramentas (T1, T14, T18)

**Files:** `tools/rodar_testes.py`, `tests/test_executor.py`, `tests/test_v4_4.py`.

- [ ] **Step 1: testes antes.** Três checks dentro do TC-RUN-001 (a contagem continua 1):
  - (k) `argumentos_planilha(ref30=None)` não contém o texto `"None"`;
  - (l) o check (j) lê o limite de `TIMEOUT_PLANILHAS`, e não um número fixo no teste;
  - em `test_v4_4.py`, o `except BaseException` que engole o Ctrl+C vira `except Exception`, e um caso com
    `KeyboardInterrupt` simulado propaga a exceção.
- [ ] **Step 2:** rodar → (k) e (l) falham.
- [ ] **Step 3:** corrigir `argumentos_planilha`, que omite o argumento quando `ref30 is None`. Corrigir também as
  junções da linha `mig_ok` (T14) e o comentário que cita `igual_ao_padrao`, que não existe: o comentário passa a
  citar a função real.
- [ ] **Step 4:** `test_executor` dá 1/1 e `test_v4_4` dá 4/4.
- [ ] **Step 5:** commit `fix: minors do executor e do test_v4_4 (pendências T1, T14 e T18 do PR #37)`.

### Task 3: minors da V4.4 (T11, T12/T15, T13, T16)

**Files:** `python/reescrita_nomes.py`, `python/nomes_v4_4.py`, `python/gerar_v4_4.py`, `tests/test_v4_4.py`,
`tests/test_workbook_v4_4.py`.

- [ ] **Step 1: testes antes** (dentro do TC-WB44-001 a 003 e do 006, sem mudar as contagens):
  - **T11:** casos unitários de `trocar_formula` com espaço duplo, com `_xlfn.`, com nome em maiúsculas diferentes
    (`ENT_05_...` contra `ent_05_...`) e com nome de escopo de aba. Cada caso afirma o comportamento atual, e a
    docstring passa a declarar esses limites.
  - **T12/T15:** `gerar_v4_4.extrair_v43` confere o SHA da V4.3 de `excel/` contra o blob da tag `v4.3`
    (`git rev-parse v4.3:excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx` contra o hash do arquivo) e levanta `ValueError` se
    divergir.
  - **T13:** a pré-checagem confere o texto de X2 a X5, e não só a presença.
  - **T16:** o TC-WB44-006 falha quando um item de `NAO_COBERTOS` passa a ser coberto (item obsoleto). O cache de
    cobertura passa a ser invalidado também pelo SHA da V4.4.
- [ ] **Step 2:** rodar → os casos novos falham onde o código ainda não confere.
- [ ] **Step 3:** implementar. `nomes_v4_4` deixa de importar funções privadas: as funções usadas viram públicas no
  módulo de origem, com o mesmo nome sem o `_`, e o nome antigo fica como alias. O `docProps/core.xml` não
  reproduzível fica só documentado (docstring de `gerar_v4_4.gerar`).
- [ ] **Step 4:** `test_v4_4` dá 4/4. O `test_workbook_v4_4` roda só com `DDS_CASOS44=2`, para o teste rápido do cache
  e do obsoleto, e o 006 sai PULADO, como já é a regra.
- [ ] **Step 5:** commit `fix: minors da V4.4 (pendências T11, T12, T13, T15 e T16 do PR #37)`.

### Task 4: registro dos minors e PR da 9a

- [ ] **Step 1:** em `.superpowers/sdd/2026-11-11-inc9/progress.md` (ledger novo), registrar a situação de cada minor:
  - feitos na 9a: T1, T11 a T16 e T18;
  - passados para a 9b: T4, T5 e T9;
  - passado para a 9c: T17, o mutante identidade;
  - T6 vai só como registro: a conversão para LF já está feita.

  Registrar também a conferência item a item do parágrafo da 8a no `docs/registro-de-versoes-V4_4.md` (T18), com as
  correções que a conferência trouxer.
- [ ] **Step 2:** commit `docs: minors do PR #37 conferidos (ledger do incremento 9)`. **Push e PR só com o "sim".**

---

# Parte 9b — Python e fontes (sessões S2 e S3)

### Task 5: regulamento como dado (TC-REG-001 e 002)

**Files:**
- Create: `data/regulamento.csv`, `python/regulamento.py`, `docs/regulamento/fontes-2027.md`, `tests/test_regulamento.py`.
- Fora do Git: `references/regulamento/*.pdf` e as conversões `.md`.

**Interfaces:**
- Produces:
  - `regulamento.Regra` (dataclass frozen): `chave: str, valor: float | str, unidade: str, documento: str, edicao: str,
    regra: str, pagina: str, status: str` (`"PROVISÓRIO"` ou `"FINAL"`);
  - `regulamento.ler(caminho: Path = CSV) -> dict[str, Regra]`;
  - `regulamento.valor(chave: str) -> float | str`.

- [ ] **Step 1:** pedir o "sim" do usuário para cada um dos quatro downloads da A3, com o nome, a fonte e o tamanho
  (tamanho conferido por `HEAD` antes). Gravar cada arquivo numa pasta nova, vazia; não rodar nada de dentro dela.
- [ ] **Step 2:** converter cada PDF para `.md` uma vez, com o docling ou o markitdown (se os dois MCP falharem,
  `uv run --with docling` num script fora da pasta). Ler a D.1.1, a D.10 inteira e o Addendum na parte da D.10 e da
  pontuação.
- [ ] **Step 3: teste antes.** `tests/test_regulamento.py`:
  - **TC-REG-001:** toda linha do CSV tem documento, edição, regra e página não vazios e status no vocabulário. Toda
    chave citada em `docs/regulamento/fontes-2027.md` existe no CSV, e o inverso também.
  - **TC-REG-002:** `ler()` recusa chave repetida e valor numérico com vírgula decimal, levantando `ValueError`.
- [ ] **Step 4:** escrever o CSV, apenas com as chaves que a V5.0 usa:
  - `skidpad_diametro_interno_m`, `skidpad_diametro_externo_m`, `skidpad_largura_faixa_m`, `skidpad_posicao_cones`
    (texto) e `skidpad_penalidade_cone_s`;
  - `skidpad_tempo` (texto: como o tempo é tomado);
  - `pontos_max_<prova>` para cada prova dinâmica e o total;
  - `skidpad_tmax_regra` (texto, só se a regra definir Tmax).

  Cada valor sai do texto do rascunho de 2027, com a página. Se o Addendum mudar algum, vale o do Addendum, com a nota.
  Escrever também a nota de fontes, com citações de no máximo 15 palavras.
- [ ] **Step 5:** `uv run python -X utf8 tests/test_regulamento.py` deve dar `2 PASS, 0 FAIL, de 2 testes`.
- [ ] **Step 6:** commit `feat: regulamento 2027 provisório como dado (data/regulamento.csv, TC-REG)`.

### Task 6: conferência da D.10 contra a 24_CURVA e o skidpad.py

**Files:** Create `docs/regulamento/conferencia-d10.md`.

- [ ] **Step 1:** montar a tabela grandeza × regulamento × planilha × diferença, com as grandezas:
  - os dois diâmetros, comparados com a 24_CURVA B5 e B6 da V4.4;
  - a largura da faixa;
  - a posição dos cones, comparada com o método "Rente aos cones" de `python/skidpad.py`;
  - a penalidade por cone, que decide se o R rente aos cones, de 8,385 m, tem sentido;
  - como o tempo é tomado;
  - a largura de pista do T11, que fica "a confirmar".
- [ ] **Step 2:** para cada diferença, escrever a mudança proposta como bloco candidato do Task 15, sem corrigir nada. Se
  a regra define Tmax como múltiplo de Tmin, registrar a pergunta do D6 ao usuário (spec C7).
- [ ] **Step 3:** commit `docs: conferência da D.10 (rascunho 2027) contra a 24_CURVA`.

### Task 7: estudo da parcela de tração (feito pelo controlador; D3)

**Files:** Create `tools/estudo_k_tracao.py`, `docs/inc9/estudo-k-tracao.md`.

**Interfaces:**
- Consumes: `equilibrio.fx_exigido_traseira(caso, ay_ms2, formas=FORMAS_V43)`; o caso sintético da escada
  (`tools/relatorio_escada.py --caso-sintetico`); `tire_model` (o PAC2002 combinado já implementado).

- [ ] **Step 1:** conferir na **imagem** do PDF do Gillespie a dedução da eq. 6-62 à 6-67 (p. 223-224) e o texto da
  p. 299. Registrar as páginas e as equações no estudo, com a conferência de sinais da convenção do projeto (EDR-002;
  K > 0 = subesterço).
- [ ] **Step 2:** conferir no `.tir` em uso a existência dos coeficientes do peso combinado lateral (`RBY1`, `RBY2`,
  `RCY1`, `RHY1` e afins, conforme o `tire_model`). Se faltarem, a forma (ii) sai do estudo, com o motivo.
- [ ] **Step 3:** procurar dupla contagem, conferindo se `equilibrio.analise_par` ou o MMM completo já embutem a
  componente lateral do Fx ou a perda de rigidez. O resultado vai para o estudo, com o arquivo e a linha.
- [ ] **Step 4:** o script calcula, nos dois R provisórios e no caso sintético:
  - a conta de ordem de grandeza (Fx/Fz no a_y do skidpad, por termo da v43);
  - ΔK_direto, ΔK_rigidez e ΔK_líquido, cada um com o sinal;
  - se algum eixo satura;
  - a comparação das formas (i) e (ii) com a linha `todas`.

  Saída em Markdown com o rótulo "caso sintético, não é dado do carro".
- [ ] **Step 5:** escrever a escolha pela regra da spec §4.2:
  1. não inverter o veredito;
  2. ficar o mais perto do Python completo;
  3. em empate, a forma mais simples;
  4. sem saturação, a forma (i);
  5. se a parcela for desprezível, dizer isso.

  A escolha vai para o estudo e para o rascunho do EDR-071 (Task 14).
- [ ] **Step 6:** commit `docs: estudo da parcela de tração no K (inc. 9, caso sintético)`.

### Task 8: oráculo da parcela de tração (TC-KTR-001 a 003; feito pelo controlador)

**Files:** Modify `python/equilibrio_linear.py` (só adição); Create `tests/test_k_tracao.py`.

**Interfaces:**
- Produces:
  - `ParcelaTracao` (dataclass frozen): `ay_ms2: float, fx_r_N: float | None, fx_f_N: float | None,
    k_direto: float | None, k_rigidez: float | None, k_tracao: float | None, forma: str, motivo: str | None`, com os K
    em rad/(m/s²) e K > 0 = subesterço;
  - `parcela_tracao(caso, ay_ms2: float, *, forma: str) -> ParcelaTracao`, onde `forma` vale `"direta"` ou
    `"direta+rigidez"` (a escolhida no Task 7). Com CdA e Crr ausentes no caso, `k_tracao = 0.0` e
    `motivo = "sem CdA e Crr: parcela de tração não avaliada"`;
  - `k_com_tracao(caso, ay_ms2: float, *, forma: str, formas=FORMAS_V43) -> tuple[float | None, ParcelasK,
    ParcelaTracao]`, que soma `parcelas_k(...).k_total` e `k_tracao`; com uma das duas `None`, o total é `None`.

- [ ] **Step 1: testes antes.**
  - **TC-KTR-001 (sinais):** num caso RWD sintético com CdA = 0,9 e Crr = 0,015 (rotulados como sintéticos de teste),
    `k_direto > 0` (subesterço, eq. 6-67 termo 3) e, na forma com rigidez, `k_rigidez < 0`.
  - **TC-KTR-002 (vazio):** sem CdA e Crr, `k_com_tracao(...)[0] == parcelas_k(..., formas=FORMAS_V43).k_total`
    exatamente, e `motivo` igual ao texto acima.
  - **TC-KTR-003 (ponto de avaliação):** a parcela é secante no a_y pedido. `parcela_tracao(caso, a)` difere entre
    a = 0,1 g e a = 1,2 g quando o Fx depende de a_y, e o Fx traseiro é igual a `fx_exigido_traseira(caso, a,
    formas=FORMAS_V43)`.
- [ ] **Step 2:** rodar → falha (`ImportError`).
- [ ] **Step 3:** implementar pela forma escolhida, com as equações do estudo. O Fx traseiro vem de
  `fx_exigido_traseira`, nunca de uma conta reescrita. O Fx dianteiro é `−Crr·W_f`.
- [ ] **Step 4:** `test_k_tracao` dá 3/3, e `test_equilibrio_linear` continua 18/18.
- [ ] **Step 5:** commit `feat: parcela de tração no K (oráculo, TC-KTR)`.

### Task 9: coerência completa no oráculo (TC-COE-001 a 004)

**Files:** Modify `python/metas.py`; Create `tests/test_coerencia.py`.

**Interfaces:**
- Produces:
  - `Ficha` ganha os campos `valor_setup: object = None`, `resultado_com_setup: object = None` e
    `custo_ms2: object = None`, todos com padrão, para não quebrar quem constrói `Ficha` hoje;
  - constantes `MOTIVO_TBD = "meta sem valor ou papel (TBD)"`, `MOTIVO_SEM_SETUP = "sem valor real do setup"`,
    `MOTIVO_RESIDUO = "resíduo da malha fechada"` e `MOTIVO_CUSTO = "custo sem justificativa"`;
  - `residuo(f: Ficha) -> float | None` (resultado com o setup menos o target);
  - `TOL_RESIDUO: float`, medida no Task 10 (até lá, o Task 9 usa um parâmetro `tol` explícito nos testes);
  - `estado_coerencia(f, fichas, *, tol=TOL_RESIDUO) -> tuple[str, str]`, que mantém a ordem das regras existentes e
    acrescenta, depois do TBD: sem setup → NÃO AVALIÁVEL (`MOTIVO_SEM_SETUP`); |resíduo| > tol → CONFLITO
    (`MOTIVO_RESIDUO`); custo > 0 sem EDR → CONFLITO (`MOTIVO_CUSTO`); custo > 0 com EDR → COMPROMISSO DECLARADO;
    senão COERENTE;
  - `contagem_por_motivo(textos: list[str]) -> dict[str, int]`;
  - `efeito_objetivo_s(R_m, ay_atual_ms2, ay_neutro_ms2) -> tuple[float | None, float | None]`, que devolve (Δt em s,
    Δt em %), com Δt = t(atual) − t(neutro) e t = 2π·√(R/a_y). Dá `(None, None)` com R ou a_y inválidos (≤ 0, vazio,
    texto).

- [ ] **Step 1: testes antes.**
  - **TC-COE-001 (malha fechada):** ficha completa sem setup dá NÃO AVALIÁVEL com `MOTIVO_SEM_SETUP`; com resíduo
    dentro de `tol`, COERENTE; fora de `tol`, CONFLITO com `MOTIVO_RESIDUO`.
  - **TC-COE-002 (custo):** custo > 0 sem EDR dá CONFLITO; com `EDR-0xx` no formato, COMPROMISSO DECLARADO; custo ≤ 0
    não muda o estado.
  - **TC-COE-003 (motivos):** ficha TBD e sem setup dá `MOTIVO_TBD` (a precedência vale);
    `contagem_por_motivo` conta cada ficha uma vez.
  - **TC-COE-004 (efeito):** R = 9,125 m, a_y de 1,5 g e de 1,45 g dá o Δt da fórmula, com 6 casas; R = 0, R vazio ou
    a_y = 0 dá `(None, None)`.
  - Os 4 checks do `test_v4_2` (o oráculo das metas, TC-WB42-003) continuam passando sem mudança, porque os campos
    novos têm padrão `None` e, sem setup, a regra nova só entra depois do TBD.

  **Atenção:** se uma ficha da V4.2 completa e sem setup mudar de COERENTE para NÃO AVALIÁVEL, isso é mudança
  intencional (spec §4.3, C4). Ela vale só para a V5.0. O `test_v4_2` lê as fichas da V4.2 e passa a chamar
  `estado_coerencia(..., regras="v42")`, um parâmetro com padrão `"v50"` que desliga as regras novas. Isso entra neste
  mesmo task.
- [ ] **Step 2:** rodar → falha.
- [ ] **Step 3:** implementar.
- [ ] **Step 4:** `test_coerencia` dá 4/4 e `test_v4_2` dá 4/4.
- [ ] **Step 5:** ficha-exemplo `docs/metas/ficha-exemplo.md` (spec §4.3): TARGET-003 (λ_f), rotulada DEMONSTRATIVA, com
  os quatro estados mostrados mudando um campo de cada vez (TBD → NÃO AVALIÁVEL; sem setup → NÃO AVALIÁVEL com o outro
  motivo; resíduo fora → CONFLITO; custo com EDR → COMPROMISSO DECLARADO). Cada estado é conferido por `estado_coerencia`
  num check do TC-COE-003.
- [ ] **Step 6:** commit `feat: coerência completa no oráculo das metas (TC-COE) e ficha-exemplo`.

### Task 10: tolerância do resíduo, medida (C6; controlador)

- [ ] **Step 1:** medir a resolução numérica do modelo direto das alavancas da 03_TARGETS: λ_f, K e o a_y de saturação.
  A grade é refinada (passo ÷ 2 e ÷ 4) no caso demonstrativo da V4.4, como no EDR-056. A medida registra, por
  grandeza, a variação do resultado com o refinamento.
- [ ] **Step 2:** `TOL_RESIDUO` vira um dict por grandeza (`dict[str, float]`), com o valor medido e o rótulo
  "resolução numérica medida em 2026-11-xx". O estudo vai para `docs/inc9/tolerancia-residuo.md`, e o TC-COE-001
  passa a usar o valor medido.
- [ ] **Step 3:** commit `docs: tolerância do resíduo da malha fechada medida por refinamento (inc. 9)`.

### Task 11: escada sem a linha da V4.2 e minors T4, T5 e T9 (A1)

**Files:** `python/escada.py`, `python/equilibrio.py` (linhas longas), `tools/relatorio_escada.py`, `tests/test_escada.py`,
`tests/test_v4_3.py` (T9), `docs/inc9/escada-v5.md`.

**Interfaces:**
- Produces: `escada.linhas_degrau2(..., incluir_v42: bool = True)`, com o nome real da função conferido no código. O
  relatório da V5.0 chama com `incluir_v42=False` e `incluir_v43=True`.
- [ ] **Step 1: teste antes** (dentro do TC-ESC-002, sem mudar a contagem): com `incluir_v42=False`, nenhuma linha se
  chama `"planilha"` e as Δ das outras linhas não mudam.
- [ ] **Step 2:** implementar. A docstring de `FORMAS_V42` em `equilibrio.py` passa a dizer "só para as referências V4.3
  e V4.4 (A1 do plano do inc. 9)". As linhas longas de `escada.py` e `equilibrio.py` (T4 e T5) quebram só onde passam de
  120 colunas. A `guarda_h2_h2v` do `test_v4_3` (T9) passa a conferir por nome de chave, via Tokenizer, e não por
  substring.
- [ ] **Step 3:** `test_escada` 3/3 (~6 min, em segundo plano) e `test_v4_3` 3/3.
- [ ] **Step 4:** gerar `docs/inc9/escada-v5.md` com `tools/relatorio_escada.py` (opção nova `--sem-v42`, saída
  obrigatória fora de `docs/inc6/`; com `docs/inc6/`, código 2).
- [ ] **Step 5:** commits separados: `refactor: linhas longas e guarda do h2v (pendências T4, T5 e T9)` e
  `feat: escada sem a linha da V4.2 e relatório da V5.0`.

### Task 12: CA-07 por texto contra a V4.4 (`python/ca07_texto.py`)

**Interfaces:**
- Produces:
  - `comparar(ref: Path, nova: Path, catalogo: set[tuple[str, str]], nomes_removidos: set[str] = frozenset(),
    nomes_novos: set[str] = frozenset()) -> list[dict]`. Devolve as diferenças fora do catálogo, cada uma
    `{aba, cel, ref, nova}`, e também os nomes definidos acrescentados ou removidos que não estão declarados (com
    `cel = "<nome>"`);
  - `ler_ref_da_tag(tag: str, caminho: str, pasta: Path) -> Path`, que extrai o arquivo da tag e confere o SHA do
    blob.
- [ ] **Step 1: testes antes**, com planilhas sintéticas mínimas em pasta temporária e sem ID novo. Os checks entram no
  TC-WB50-002 quando ele existir (Task 19); até lá, no `tests/test_ca07_texto.py`, que o Task 19 incorpora e apaga. Os
  casos: igual dá `[]`; célula fora do catálogo dá uma diferença; célula no catálogo não dá diferença; nome removido
  sem declaração dá uma diferença; aba nova dá uma diferença por célula.
- [ ] **Step 2:** implementar, independente do gerador: o módulo não importa `gerar_v5_0`.
- [ ] **Step 3:** testes OK; commit `feat: CA-07 por texto contra a referência (ca07_texto)`.

### Task 13: contador por Origem e roteiro de entrada (TC-ORG-001)

**Files:** Create `python/origens.py`, `tests/test_origens.py`, `docs/v5-0/roteiro-entrada-t11.md`.

**Interfaces:**
- Produces:
  - `origens.celulas_com_origem(wb) -> list[tuple[str, str, str]]`, que devolve (aba, célula de entrada, nome da
    célula de Origem), a partir de `atualizar_planilha.celulas_de_entrada()` e dos nomes `org_*`;
  - `origens.contar(valores: dict[str, object]) -> dict[str, int]`, com chave = texto da Origem e mais `"(vazia)"`.
- [ ] **Step 1: teste antes.** O TC-ORG-001, na V4.4 de `excel/`, confere que cada `org_*` tem uma entrada
  correspondente, que a soma das contagens = número de entradas com Origem, e que nenhum texto fica fora de
  `Lista_Origens`, a não ser `"(vazia)"`.
- [ ] **Step 2:** implementar. Escrever o roteiro (sem valores): a ordem de entrada é massa e geometria, pneu, mola e
  barra, depois aero. Para cada grupo, o roteiro traz a aba, a unidade, onde obter o dado (CAD, ficha do pneu, medição)
  e a Origem e a Fonte a escolher.
- [ ] **Step 3:** testes OK; commit `feat: contador por Origem e roteiro de entrada do T11`.

### Task 14: triagem dos EDRs e rascunhos dos EDR-071 a 073

- [ ] **Step 1:** nos corpos de EDR-023, 024, 033, 036 e 040, acrescentar a linha `**Triagem (2026-11-xx, inc. 9):**
  aguarda <dado>; reabre com <critério>`, pela tabela da spec §4.7. O status não muda.
- [ ] **Step 2:** escrever os EDR-071 (estudo do K), 072 (coerência) e 073 (regulamento e condição do EDR-069) como
  PROPOSED, com alternativas e evidências, e o índice com a contagem conferida.
- [ ] **Step 3:** commit `docs: triagem dos EDRs em AWAITING_DECISION e EDR-071 a 073 propostos`.

### Task 15: relatório do passo do usuário (C10) — PARADA

**Files:** Create `docs/inc9/passo-usuario.md`.

- [ ] **Step 1:** o relatório lista os blocos candidatos da V5.0:
  - `B-CHAVE0` (retirada de B9 e B10 e das fórmulas que as leem, com os 6 nomes);
  - `B-K-TRACAO`, `B-COERENCIA`, `B-ORIGENS`, `B-REGULAMENTO` (e os vindos do Task 6), `B-TEXTOS`.

  Para cada bloco: uma linha em linguagem simples ("o que muda para a equipe"); depois aba, célula, fórmula ou texto
  anterior e novo, dependências, justificativa e teste. As fórmulas novas saem de funções-rascunho do Task 18, num
  módulo de pré-visualização que roda sem gerar a planilha. Acrescentar os SUS propostos, as recomendações para o
  EDR-023 e o EDR-036, a escolha do estudo do K e a pergunta do D6 (se o Task 6 a levantou).
- [ ] **Step 2:** commit e **parar**. O PR da 9b só com o "sim"; a 9c começa só depois da aprovação do usuário, bloco a
  bloco, registrada no relatório.

---

# Parte 9c — V5.0 (sessões S4 e S5)

### Task 16: nomes novos (`data/nomes_V5_0.csv`, `python/nomes_v5_0.py`)

**Interfaces:**
- Produces: `NOMES_V50: list[Nome]` (os nomes novos dos blocos aprovados, pela regra do EDR-058);
  `REMOVIDOS_V50: set[str]` (os 6 nomes das chaves, se `B-CHAVE0` for aprovado); `conferir_tabela(wb) -> list[str]`;
  `celulas_de_entrada_v50() -> set[tuple[str, str]]` (as de entrada da V4.4 − B9/B10 + CdA, Crr e valor real do setup, C8),
  usada por `migrar_viva` e pelo contador por Origem.
- [ ] **Step 1:** teste antes (será o TC-WB50-001, Task 19): sem colisão com os 1290 da V4.4; cada nome novo aponta
  para uma célula vazia ou de bloco aprovado.
- [ ] **Step 2:** implementar; commit `feat(v5.0): nomes novos da V5.0`.

### Task 17: gerador, `passe_estrutura` e catálogos (C1)

**Files:** Create `python/gerar_v5_0.py`, `docs/registro-de-versoes-V5_0-celulas.md` (gerado).

**Interfaces:**
- Consumes: `gerar_v4_4.extrair_v43`, como padrão de extração da tag (aqui `extrair_v44`); `ca07_texto`;
  `nomes_v5_0`; as funções de bloco do Task 18.
- Produces:
  - `TAG_V44 = "v4.4"`, `CAMINHO_V44 = "excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx"`,
    `SAIDA_PADRAO = build/FSAE_EV_Suspension_Fase1_V5_0.xlsx` e
    `SAIDA_ESTRUTURA = build/FSAE_EV_Suspension_Fase1_V5_0_estrutura.xlsx`;
  - `Bloco` (dataclass): `nome: str, passe: str ("estrutura" | "fisica"), aplicar: Callable[[Workbook], list[dict]]`;
  - `BLOCOS: tuple[Bloco, ...]` (só os aprovados no Task 15);
  - `passe_estrutura(wb) -> list[dict]` e `passe_fisica(wb) -> list[dict]`, que devolvem o catálogo com as chaves
    `aba, cel, antes, novo, bloco, motivo, edr`;
  - `dependentes(wb, celulas: set[tuple[str, str]]) -> set[tuple[str, str]]`, o fecho pelo grafo de precedentes,
    pelo leitor de `python/raizes.py`, com nomes resolvidos;
  - `gerar(v44: Path | None, saida: Path, *, so_estrutura: bool = False, registro: Path | None = None) -> dict`;
  - `copia_v50(tmp, alteracoes=None, nome=..., so_estrutura=False) -> Path`, no padrão de `copia_v44`.
- [ ] **Step 1:** pré-checagem em `tests/test_v5_0.py`. `gerar(so_estrutura=True)` gera 1290 nomes − os removidos + os
  novos do passe de estrutura. O catálogo de estrutura só tem células de blocos `estrutura`. `_recusar` com a saída em
  `excel/` levanta `SystemExit`.
- [ ] **Step 2:** rodar → falha.
- [ ] **Step 3:** implementar o `passe_estrutura` (o bloco `B-CHAVE0`, com as fórmulas de forma única aprovadas, e os
  textos do `B-TEXTOS`) e os dois catálogos. O catálogo de células segue o padrão do V4.4, com a coluna Bloco, e
  ganha a seção "Dependentes por valor".
- [ ] **Step 4:** rodar → OK. Commit `feat(v5.0): gerador, passe de estrutura e catálogos`.

### Task 18: `passe_fisica` (blocos B-K-TRACAO, B-COERENCIA, B-ORIGENS, B-REGULAMENTO)

**Files:** `python/aba_equilibrio.py`, `python/aba_metas.py` e `python/aba_curva.py` (só funções novas, com sufixo
`_v50`), `python/gerar_v5_0.py`.

- [ ] **Step 1:** para cada bloco, uma função `bloco_<nome>(wb) -> list[dict]`, que escreve as fórmulas aprovadas no
  Task 15 lendo por nome:
  - **B-K-TRACAO:** as entradas CdA e Crr com Origem e Fonte; a célula de resultado da parcela de tração; o K com a
    parcela; o texto da F188 com o ponto de avaliação. O D16 vem da pior origem, que passa a incluir CdA e Crr.
  - **B-COERENCIA:** o valor real do setup, o resíduo, o efeito no objetivo (s e %) com "DEMONSTRATIVO (R provisório
    da 24_CURVA)", o estado com as regras novas e, no 14_DASHBOARD, a contagem por motivo.
  - **B-ORIGENS:** o contador por Origem no 14_DASHBOARD, o roteiro na 00_README e a hierarquia entre provas pelos pontos
    máximos (`pontos_max_*` por nome, com a fonte e "PROVISÓRIO").
  - **B-REGULAMENTO:** um bloco de células com os valores de `data/regulamento.csv`, todas com nome. A 24_CURVA B5 e B6
    e os textos passam a ler esses nomes, só se o Task 15 aprovou.
- [ ] **Step 2:** teste antes (TC-WB50-003, Task 19). A regeneração dá 0 diferença contra `excel/` depois da cópia, e
  toda fórmula nova lê por nome (sem endereço de célula única com nome, a regra da V4.4).
- [ ] **Step 3:** implementar; `gerar` completo; commit `feat(v5.0): passe de física e coerência`.
- [ ] **Step 4:** cópia `build/FSAE_EV_Suspension_Fase1_V5_0.xlsx` → `excel/`, num commit próprio:
  `excel: V5.0 de referência gerada por python/gerar_v5_0.py (cópia de build/)`.

### Task 19: `tests/test_v5_0.py` (TC-WB50-001 a 004)

- [ ] **Step 1:** os testes:
  - **TC-WB50-001 (estrutura e nomes):** 1290 − removidos + novos, sem colisão, todos com destino válido.
  - **TC-WB50-002 (CA-07 contra a V4.4):** `ca07_texto.comparar(ref da tag v4.4, V5.0 de excel/, catálogo, REMOVIDOS,
    novos)` dá `[]`. Os checks do Task 12 entram aqui, e o `tests/test_ca07_texto.py` sai.
  - **TC-WB50-003 (regeneração):** a regeneração dá 0 diferença contra `excel/`, e as fórmulas novas leem por nome.
  - **TC-WB50-004 (migração):** `migrar_viva` da V4.4 sintética com dados para a V5.0 leva os dados por nome. Os casos:
    - viva com B9 = 0 dá conflito listado, código 1;
    - viva com B10 = "1" (texto) dá conflito;
    - entradas novas vazias não dão conflito.
- [ ] **Step 2:** rodar → OK (`4 PASS, 0 FAIL, de 4 testes`). Commit `test(v5.0): TC-WB50-001 a 004`.

### Task 20: `tests/test_workbook_v5_0.py` (TC-WB50-005 a 008)

- [ ] **Step 1:** os testes, no padrão de `tests/test_workbook_v4_4.py`, Excel via COM ou LibreOffice:
  - **TC-WB50-005 (passe de estrutura):** `copia_v50(so_estrutura=True)` contra a V4.4, com tolerância zero, em todas
    as células, nos 61 casos do TC-WB44-005 (as mesmas perturbações).
  - **TC-WB50-006 (equivalência com o oráculo):** nos casos sintéticos com CdA e Crr preenchidos (rotulados), o K da
    planilha = `k_com_tracao` com erro absoluto ≤ 1e-5 °/g (o critério da A5 do inc. 8), e o estado de cada ficha =
    `metas.estado_coerencia`. Os casos dirigidos: CdA em texto, Crr < 0, ficha TBD sem setup.
  - **TC-WB50-007 (fora dos catálogos):** em cada caso, toda célula fora do catálogo de fórmulas e do de dependentes
    tem o mesmo valor da V4.4. Também o caso dirigido de R inválido, em que o efeito e o Δt dão N/A.
  - **TC-WB50-008 (cobertura de ramos):** no padrão do TC-WB44-006, só para as fórmulas novas; com `DDS_CASOS50` sai
    PULADO.
- [ ] **Step 2:** rodar no Excel, em segundo plano, com o tempo medido por caso. O limite em `tools/rodar_testes.py` é
  `TIMEOUT_PLANILHAS["tests/test_workbook_v5_0.py"] = 7200`, ajustado no Task 23 pelo tempo medido × 2.
- [ ] **Step 3:** commit `test(v5.0): TC-WB50-005 a 008`.

### Task 21: mutação da planilha V5.0 (`tests/mutation_planilha_v50.py`)

- [ ] **Step 1:** os mutantes, no padrão de `tests/mutation_planilha_v44.py`:
  - (a) o sinal da parcela de tração;
  - (b) a troca de CdA por Crr;
  - (c) a ordem de precedência TBD e sem setup trocada;
  - (d) o sinal do resíduo (target − resultado);
  - (e) o contador que ignora `"(vazia)"`;
  - (f) o **mutante identidade** (T17): a regeneração sem mudança, que tem de sobreviver, para provar que a mutação não
    reprova o que está certo.

  Esperado: 5 mortos e o identidade vivo, "5/5 + identidade".
- [ ] **Step 2:** rodar (Excel, em segundo plano); commit `test(v5.0): mutação da planilha V5.0`.

### Task 22: escada com a linha da planilha V5.0

- [ ] **Step 1:** em `escada.py`, a linha `"planilha V5.0"` usa `k_com_tracao` e as formas v43. Teste dentro do
  TC-ESC-002: a linha não inverte o veredito contra `todas` no caso sintético (EDR-065 item 3), e o ΔK é registrado.
- [ ] **Step 2:** regenerar `docs/inc9/escada-v5.md`; commit `feat: linha da planilha V5.0 na escada`.

### Task 23: executor, registro de versões, EDRs, CLAUDE.md e LEIA-ME

- [ ] **Step 1:** em `tools/rodar_testes.py`, os itens novos são:
  - `tests/test_regulamento.py`, `test_k_tracao.py`, `test_coerencia.py`, `test_origens.py`, `test_v5_0.py`;
  - `tests/test_workbook_v5_0.py`, com o limite medido;
  - `tests/mutation_planilha_v50.py`.

  A `DEPENDENCIAS` de cada um inclui `excel/FSAE_EV_Suspension_Fase1_V5_0.xlsx` e `data/regulamento.csv`.
- [ ] **Step 2:** `docs/registro-de-versoes-V5_0.md`, o EDR-074 (IMPLEMENTED) e os EDR-071 a 073 passados a IMPLEMENTED,
  com o índice e a contagem conferidos. No CLAUDE.md: a situação da V5.0, os comandos e as contagens esperadas. O
  LEIA-ME do Drive vai em `build/drive-v5.0/`, com uma seção "o que mudou para você" de meia página (C10).
- [ ] **Step 3:** commits separados (executor, documentos).

### Task 24: suíte única do incremento

- [ ] **Step 1:** numa árvore sem mudanças, `uv run python -X utf8 tools/rodar_testes.py --saida
  docs/migracao/verificacao-inc9-excel.md --titulo "..."`, com `DDS_RECALC=excel`, em segundo plano (~4 h). Depois o
  mesmo no LibreOffice (`verificacao-inc9-libreoffice.md`).
- [ ] **Step 2:** todos os itens PASS, ou PULADO pela regra. Qualquer FAIL volta ao task dono, e a suíte é refeita só
  com a aprovação do usuário. Os EDR-071 a 074 passam a VERIFIED; commit dos logs.

### Task 25: fechamento (cada passo com o "sim" do usuário)

- [ ] **Step 1:** revisão final da branch, com um subagente Sonnet; os minors vão para o PR.
- [ ] **Step 2:** PR, merge e tag `v5.0` no merge.
- [ ] **Step 3:** troca da viva:
  1. conferir a cota do Drive, que precisa estar abaixo de 90% (C10); acima disso, a troca para até o usuário liberar
     espaço;
  2. `tools/conferir_viva.py`, que tem de dar código 0;
  3. `tools/migrar_viva.py VIVA --para excel/FSAE_EV_Suspension_Fase1_V5_0.xlsx`, sem nenhum conflito pendente;
  4. trocar a planilha, deixando a pasta só com a V5.0, mais o LEIA-ME, o registro e o EDR em .docx;
  5. conferir no navegador.
- [ ] **Step 4:** CLAUDE.md e memória com a viva na V5.0; passagem do fim do incremento 9.

## Ordem e sessões

| Sessão | Tasks | Modelo | Depende de |
|---|---|---|---|
| S1 (9a) | 1 a 4 | Sonnet | — (paralela à S2) |
| S2 (9b-1) | 5, 6, 12, 13, 14 | Sonnet; o controlador lê o regulamento | A2 e A3 aprovados |
| S3 (9b-2) | 7 a 11, 15 | controlador (física) e Sonnet (resto) | S2 (Task 6 e 14) |
| Passo do usuário | aprovação dos blocos e dos SUS | — | Task 15 |
| S4 (9c-1) | 16 a 22 | Sonnet | merge da 9a e da 9b; passo do usuário |
| S5 (9c-2) | 23 a 25 | Sonnet; suíte em segundo plano | S4 |
