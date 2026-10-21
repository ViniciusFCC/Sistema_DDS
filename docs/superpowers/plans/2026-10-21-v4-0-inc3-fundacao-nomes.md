# V4.0, incremento 3 (fundação, parte 1: nomes definidos e dados por chave): plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar a planilha V4.0 a partir do arquivo da tag `v3.0` com nomes definidos em todas as entradas e nos resultados, sem reescrever nenhuma fórmula, e criar a ponte de dados por chave. O extrator lê a V3.0 viva pelos endereços, e o injetor grava na V4.0 pelos nomes, sem perder entrada e sem sobrescrever preenchimento em silêncio. Essa ponte é o que leva o preenchimento da equipe, que já começou na pasta compartilhada, para a V4.0.

**Architecture:**
- `python/nomes_v4_0.py` gera, de forma determinística, a tabela de nomes (`data/nomes_V4_0.csv`) a partir da V3.0 e de `atualizar_planilha.celulas_de_entrada()`.
- `python/gerar_v4_0.py` copia a V3.0 da tag, acrescenta os nomes e muda só a versão no 00_README e o 15_CHANGELOG. Cada célula alterada fica registrada.
- `python/dados_planilha.py` lê por endereço, lê por nome e injeta.
- `tools/migrar_dados_v3_v4.py` é a interface de linha de comando da migração.
- Testes sem motor de recálculo (`tests/test_v4_0.py`) e com motor (`tests/test_workbook_v4_0.py`, EDR-044).

**Tech Stack:** Python 3.13, openpyxl, `tests/recalculo_planilha.py` (Excel via COM ou LibreOffice), scripts de teste com `check()`.

**Spec:** `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` §8.2 (nomes definidos, dados por chave, equivalência por valor) e §10, incremento 3 (decisão D13 do usuário: nomes sem reescrever fórmulas; a reescrita fica para o incremento 7). EDR-051, EDR-054 e a decisão do usuário de 2026-10-20 (a viva oficial fica na pasta compartilhada da equipe).

## Contexto da versão (usuário, 2026-10-21)
A V4.0 cobre os incrementos 1 a 3. Este incremento entrega o arquivo `excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx`, mantendo o padrão de nome (EDR-054: "Fase1" é a etapa 1 do Guia). A partir do incremento 4, a versão passa a V4.1, numa conversa nova.

## Autorizações a pedir antes de executar (CLAUDE.md)
1. IDs de teste **TC-WB40-001 a TC-WB40-012**.
2. **EDR-058**, "Fonte de verdade da V4.0: gerada da tag `v3.0` com nomes definidos; dados da equipe migram por chave". O EDR-051 não muda de status, porque continua valendo para a V3.0 viva.
3. Dados que só o usuário tem, e que não bloqueiam a execução (ficam "a informar" no EDR-058): o caminho da pasta compartilhada da viva e o responsável pelos retratos `dados:` (EDR-051).

## Global Constraints
- A V3.0 de partida é o arquivo da tag `v3.0`, extraído por `git show v3.0:excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx` para uma pasta temporária. Nunca o da árvore: a viva pode estar sendo preenchida.
- Nenhuma ferramenta salva ou recalcula `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`. Gravação só em `build/` ou em pasta temporária. A V4.0 de referência é gerada em `build/` e copiada para `excel/` num commit próprio.
- Nenhuma fórmula muda: a V4.0 tem as mesmas 387 fórmulas da V3.0, com texto idêntico. As únicas células alteradas são A3 do 00_README (versão) e a linha nova do 15_CHANGELOG, registradas em `alteracoes_v4_0()` com antes e depois. Os nomes definidos são acréscimos no nível do workbook.
- Regras de nome (as do Excel, conferidas no teste por regex e por recálculo):
  - começa por letra;
  - só tem letras ASCII, dígitos e `_`, com até 255 caracteres;
  - não pode parecer referência A1 ou R1C1.
  
  Convenção: `<papel>_<aba2>_<slug>`.
  - **papel:** `ent` (valor de entrada), `org` (Origem, coluna E ou I), `fte` (Fonte, coluna F ou J), `res` (resultado com fórmula);
  - **aba2:** os dois dígitos da aba (`05`, `10`…);
  - **slug:** o rótulo da coluna A da linha, sem acento, em minúsculas, com qualquer não alfanumérico trocado por `_`, `_` repetidos colapsados e até 40 caracteres.
  
  Em colisão, acrescente `_<célula>` (por exemplo `_c86`). Na 10_TIRE, o slug inclui a coluna do caso (`_b`…`_f`).
- Os resultados nomeados são todas as células com fórmula das abas 05, 06, 07, 08, 09, 10, 11, 13 e 14. Os IDs SUS da linha, se algum texto da linha casar com `SUS-\d{3}` (ou `SUS-\d{3}-[FR]`), vão na coluna `sus_id` da tabela, sem criar ID.
- SI e textos sem mudança. Planilhas abertas pelo openpyxl em leitura, salvo o gerador e o injetor (que gravam cópias).
- Fim de linha LF nos arquivos de texto. Branch `feat/v4-0-inc3-fundacao`, criada da ponta de `feat/v4-0-inc2-equilibrio-linear`. Commits separados por propósito, com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Push e PR só com pedido.

## Contagem de testes (fim)
| Script | Testes | IDs |
|---|---|---|
| `tests/test_v4_0.py` (novo, sem motor) | 9 | TC-WB40-001..009 |
| `tests/test_workbook_v4_0.py` (novo, motor; NÃO EXECUTÁVEL sem Excel ou LibreOffice) | 3 | TC-WB40-010..012 |

## Review Focus
1. **Rótulo da coluna A vazio ou repetido** (linhas sem texto, ou rótulos iguais na 10_TIRE). Esperado: o nome cai na regra de colisão, sempre único e determinístico, nunca vazio (Task 1, TC-WB40-001).
2. **Nome que o Excel recusa** (por exemplo, um slug que vira algo como `res_05_x1` com cara de referência). Esperado: o teste do motor monta `=nome` numa cópia e não acha nenhum `#NAME?`; a regex do TC-WB40-001 pega antes (Tasks 1 e 4).
3. **Viva com uma entrada que a V4.0 não tem** (célula de entrada fora da tabela). Esperado: erro que lista as células, nunca descarte em silêncio (Task 3, TC-WB40-009).
4. **Destino já preenchido de forma diferente da base** (conflito na injeção). Esperado: o conflito vai para o relatório e a célula não é sobrescrita; a ferramenta sai com código ≠ 0 (Task 3, TC-WB40-007).
5. **Saída apontada para a planilha viva ou para `excel/`**. Esperado: recusa antes de abrir qualquer arquivo para escrita (Tasks 2 e 3, TC-WB40-008).

---

### Task 1: Tabela de nomes da V4.0

**Files:** Create `python/nomes_v4_0.py`, `data/nomes_V4_0.csv` (gerado e commitado), `tests/test_v4_0.py` (cabeçalho `check()` e resumo como em `tests/test_equilibrio.py`).

**Interfaces:**
- Consumes: `atualizar_planilha.celulas_de_entrada() -> set[tuple[aba, celula]]`, `atualizar_planilha.ABAS_ORIGEM`, as linhas de origem da 10_TIRE (colunas I e J e a linha 84; veja `raizes.celula_origem`).
- Produces:
  - `@dataclass(frozen=True) class Nome`: `nome: str`, `aba: str`, `celula: str`, `papel: str` (`ent`/`org`/`fte`/`res`), `sus_id: str` (vazio se não houver), `rotulo: str`.
  - `tabela_nomes(caminho_v30: Path) -> list[Nome]`: ordenada por (aba, linha, coluna), determinística.
  - `ler_tabela(caminho_csv: Path) -> list[Nome]` e `escrever_tabela(nomes, caminho_csv)`, em UTF-8, LF, com o cabeçalho `nome,aba,celula,papel,sus_id,rotulo`.
  - `NOME_VALIDO: re.Pattern` e `parece_referencia(nome: str) -> bool` (A1 até XFD1048576 e R1C1).
  - CLI: `uv run python -X utf8 python/nomes_v4_0.py --v30 <arquivo> --saida data/nomes_V4_0.csv`.
- [ ] **Step 1: testes que falham:**
  - `TC-WB40-001`: na tabela gerada da V3.0 da tag, os nomes são únicos e casam com `NOME_VALIDO`; nenhum `parece_referencia`; cada (aba, célula) existe na V3.0. Toda célula de `celulas_de_entrada()` aparece exatamente uma vez como `ent`, `org` ou `fte`. Toda célula com fórmula das abas listadas aparece como `res`. A tabela gerada é igual a `data/nomes_V4_0.csv`, para pegar CSV desatualizado.
  - `TC-WB40-009`: `verificar_cobertura(tabela, celulas)` (função da Task 1) levanta `ValueError` que lista as células, quando uma entrada não tem nome.
- [ ] **Step 2:** ver falhar. **Step 3:** implementar e gerar o CSV. **Step 4:** `2 PASS, 0 FAIL, de 2 testes`. **Step 5: Commit** `feat: tabela de nomes definidos da V4.0`.

### Task 2: Gerador da V4.0 e comparação com a V3.0

**Files:** Create `python/gerar_v4_0.py`; Modify `tools/comparar_planilhas.py` (função nova `comparar_v40(v40, v30, alteradas) -> (ok, linhas)`); Test `tests/test_v4_0.py`.

**Interfaces:**
- `alteracoes_v4_0() -> list[dict]`: `{aba, cel, novo, ref}` com 00_README A3 (`"Versão do workbook: V4.0 (fundação: nomes definidos; fórmulas iguais à V3.0) | Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated"`) e a linha do 15_CHANGELOG (A, B, C da próxima linha livre; texto curto citando o EDR-058 e este plano).
- `gerar(caminho_v30: Path, saida: Path, tabela: list[Nome]) -> list[dict]`: copia, acrescenta os `DefinedName` (escopo do workbook, `'aba'!$C$L`), aplica `alteracoes_v4_0()` e devolve o registro (aba, célula, antes, depois, ref). Recusa `saida` dentro de `excel/` e `saida == caminho_v30` com `SystemExit`, antes de abrir qualquer arquivo.
- CLI: `uv run python -X utf8 python/gerar_v4_0.py [--v30 ARQ] [--saida build/FSAE_EV_Suspension_Fase1_V4_0.xlsx] [--registro docs/registro-de-versoes-V4_0-celulas.md]`. Sem `--v30`, extrai o arquivo da tag `v3.0` para uma pasta temporária.
- [ ] **Step 1: testes que falham:**
  - `TC-WB40-002`: os nomes definidos da V4.0 gerada são exatamente os da tabela (nome → destino).
  - `TC-WB40-003`: `comparar_v40(v40, v30_tag, celulas de alteracoes_v4_0())` passa: mesmas abas e ordem; 387 fórmulas com texto idêntico; valores iguais fora das células alteradas.
  - `TC-WB40-008` (parte do gerador): saída em `excel/…` e saída = origem levantam `SystemExit`, sem criar arquivo.
- [ ] **Step 2:** ver falhar. **Step 3:** implementar. **Step 4:** rodar `tests/test_v4_0.py` (`5 PASS…` com 001, 002, 003, 008, 009). Gerar a referência: `uv run python -X utf8 python/gerar_v4_0.py --registro docs/registro-de-versoes-V4_0-celulas.md`, depois copiar `build/FSAE_EV_Suspension_Fase1_V4_0.xlsx` para `excel/`.
- [ ] **Step 5: Commits:** `feat: gerador da V4.0 a partir da tag v3.0 (nomes definidos)`; depois, separado, `feat: planilha V4.0 de referência gerada (fundação, parte 1)`, com o xlsx e o registro de células.
- [ ] **Step 6:** acrescentar o `TC-WB40-004`: a regeneração (`gerar` em pasta temporária a partir da tag) é igual à `excel/…V4_0.xlsx` por `comparar_planilhas` (CA-07 da V4.0, comparando também os nomes definidos). `6 PASS`. Commit `test: CA-07 da V4.0`.

### Task 3: Dados por chave (extrator, injetor, migração)

**Files:** Create `python/dados_planilha.py`, `tools/migrar_dados_v3_v4.py`; Test `tests/test_v4_0.py`.

**Interfaces:**
- `ler_por_endereco(xlsx_v30: Path, tabela) -> dict[str, object]`: valores das células `ent`, `org` e `fte`, por nome, lidos pelo endereço da tabela (para a viva V3.0).
- `ler_por_nome(xlsx_v40: Path) -> dict[str, object]`: o mesmo, resolvendo os nomes definidos da própria planilha.
- `@dataclass RelatorioInjecao`: `escritas: list[str]`, `iguais: list[str]`, `conflitos: list[tuple[str, object, object, object]]` (nome, base, destino, novo), `faltando: list[str]`.
- `injetar(xlsx_v40: Path, dados: dict, saida: Path, base: dict | None = None) -> RelatorioInjecao`. Para cada nome de entrada: o destino igual ao novo vai para `iguais`; o destino igual à base (padrão: `ler_por_nome` da própria V4.0 de origem) é escrito; qualquer outro caso é `conflito`, e a célula não é escrita. Nome sem célula vai para `faltando`. Recusa `saida` em `excel/` e `saida == xlsx_v40`. Grava só a cópia; nunca recalcula.
- `tools/migrar_dados_v3_v4.py VIVA_V3.xlsx [--v40 excel/…V4_0.xlsx] [--saida build/V4_0_com_dados.xlsx] [--relatorio build/migracao-V3-V4.md]`:
  - chama `verificar_cobertura` sobre as células com valor da viva (Review Focus 3);
  - escreve o relatório em Markdown (contagens e a lista de conflitos e faltas);
  - sai com código 1 se houver conflito ou falta, 0 se não houver.
- [ ] **Step 1: testes que falham:**
  - `TC-WB40-005`: `ler_por_nome(V4.0 ref) == ler_por_endereco(V3.0 tag, tabela)` em todas as entradas (equivalência dos dados por chave).
  - `TC-WB40-006` (ida e volta): numa cópia temporária da V3.0 da tag, muda 5 entradas de abas diferentes, com valor, Origem e Fonte (valores de teste rotulados). `injetar` na V4.0 → `ler_por_nome(saida)` tem exatamente os valores novos, e o resto fica igual. `escritas` lista os 15 nomes (valor, origem e fonte de cada).
  - `TC-WB40-007` (conflito): numa cópia da V4.0, uma das 5 células já foi mudada para outro valor. `injetar` com a base da V4.0 de referência lista o conflito com os três valores, não escreve a célula e escreve as outras 14. A CLI sai com código 1.
  - `TC-WB40-008` (parte do injetor): saída em `excel/…` levanta `SystemExit`.
- [ ] **Step 2:** ver falhar. **Step 3:** implementar. **Step 4:** `tests/test_v4_0.py`: `9 PASS, 0 FAIL, de 9 testes`. **Step 5: Commit** `feat: dados por chave entre a V3.0 viva e a V4.0 (extrator, injetor, migração)`.

### Task 4: Equivalência por valor e nomes no motor de recálculo

**Files:** Create `tests/test_workbook_v4_0.py`, no padrão de `tests/test_workbook_suspensao.py`: motor de `tests/recalculo_planilha.py`; sem motor, sai NÃO EXECUTÁVEL com código 3.

**Interfaces:** só usa as anteriores.
- [ ] **Step 1: testes:**
  - `TC-WB40-010`: a cópia recalculada da V4.0 tem 0 erros de fórmula, e o total de fórmulas é 387.
  - `TC-WB40-011` (equivalência por valor, spec §8.2): recalcula cópias da V4.0 e da V3.0 da tag. Para cada nome `res`, o valor da V4.0 (pelo nome) é igual ao da V3.0 (pelo endereço), com erro relativo ≤ 1e-12, ou igual para textos.
  - `TC-WB40-012` (nomes válidos para o motor): numa cópia da V4.0, uma aba temporária `ZZ_NOMES` recebe `=<nome>` para cada nome da tabela. Depois de recalcular, nenhuma célula dá `#NAME?`, e cada uma é igual ao valor do destino. A aba existe só na cópia.
- [ ] **Step 2:** rodar com `DDS_RECALC=excel` e com `DDS_RECALC=libreoffice`: `3 PASS, 0 FAIL, de 3 testes` nos dois motores. Qualquer diferença entre motores é relatada, não ajustada.
- [ ] **Step 3: Commit** `test: equivalência por valor e nomes da V4.0 no motor de recálculo`.

### Task 5: EDR-058, registro na suíte e documentação

**Files:** Modify `docs/Engineering_Decision_Register.md` (EDR-058, índice, contagens, versão, §6); Create `docs/registro-de-versoes-V4_0.md` (resumo da V4.0: incrementos 1-3, contagens, como migrar, pendências); Modify `tools/rodar_testes.py`, `CLAUDE.md`.

- [ ] **Step 1: EDR-058** (Record_Status conforme o usuário), com estes fatos:
  - a V4.0 é gerada da tag `v3.0`;
  - os nomes seguem as regras desta página;
  - as fórmulas são idênticas (D13; a reescrita fica para o incremento 7);
  - a migração é por chave, com conflito listado e nunca sobrescrito;
  - a viva oficial fica na pasta compartilhada da equipe (usuário, 2026-10-20), com caminho e responsável "a informar" se o usuário não tiver dado;
  - a partir do incremento 4 a versão é V4.1 (usuário, 2026-10-21).
  
  Related: EDR-043, 044, 050, 051, 054.
- [ ] **Step 2: `tools/rodar_testes.py`:**
  - `TESTES` += `("V4.0 (nomes e dados)", "tests/test_v4_0.py", 9, "plano do incremento 3 da V4.0")`;
  - `PLANILHAS` += `("tests/test_workbook_v4_0.py", 3, "V4.0; plano do incremento 3")`;
  - CA-07 += regeneração da V4.0 contra `excel/…V4_0.xlsx`;
  - a verificação de versão do 00_README!A3 passa a valer também para a V4.0.
- [ ] **Step 3: `CLAUDE.md`:** em "Situação atual" e "Comandos", a V4.0 de referência, o gerador, a migração (`tools/migrar_dados_v3_v4.py`) e os esperados novos. A V3.0 continua sendo a viva da equipe até o usuário decidir a troca.
- [ ] **Step 4:** suíte inteira em segundo plano: tudo PASS.
- [ ] **Step 5: Commits:** `docs: EDR-058 (fonte de verdade da V4.0)`; `docs: registro de versões da V4.0`; `test: registra a V4.0 na suíte`.
