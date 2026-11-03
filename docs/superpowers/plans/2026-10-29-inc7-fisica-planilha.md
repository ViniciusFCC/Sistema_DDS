# Incremento 7: física da planilha, raio do skidpad e V4.3 (plano de implementação)

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou
> superpowers:executing-plans para executar este plano tarefa por tarefa. Os passos usam caixas (`- [ ]`).

**Objetivo:** levar à planilha (V4.3) o raio do skidpad por dois métodos e o modo manual, o Ackermann com o centro da
curva na linha do eixo traseiro e o Fx exigido por arrasto induzido (EDR-066), atrás de chaves com padrão 1. Antes
disso, corrigir o executor dos testes e estudar a faixa do NEUTRO.

**Arquitetura:** a parte 7a (só Python, PR próprio) põe a física nova ao lado da antiga, por adição.
`equilibrio.Formas` escolhe a forma de cada fórmula, com padrão igual ao de hoje, e `mmm.VARIANTES` ganha a coluna
`planilha_v43`. A escada compara as duas formas da planilha e o relatório roda com os dois R. Depois vem o passo do
usuário: a tolerância do EDR-065, a faixa do NEUTRO e a aprovação célula a célula do catálogo da seção "Catálogo das
células da V4.3". A parte 7b gera a V4.3 a partir da tag `v4.2`, com uma aba nova (`24_CURVA`), sem inserir linhas nem
colunas nas abas existentes. As fórmulas existentes que mudam são só as do catálogo.

**Tecnologia:** Python 3.13 (stdlib, openpyxl), Excel via COM para recálculo de cópias (EDR-044), `uv`.

**Spec (fonte de verdade do desenho):** `docs/superpowers/specs/2026-10-29-inc7-fisica-planilha-design.md` (U1 a U9,
§2 escopo, §3 geometria, §4 fórmulas e NEUTRO, §5 arquitetura, §6 verificação, §7 V4.3, §8 ordem). Passagem:
`docs/passagem-2026-10-29.md`. O executor lê a spec e este plano.

## Restrições globais

- `uv run python -X utf8 ...`; no Git Bash, `export UV_SYSTEM_CERTS=1` antes. Nunca `python` direto.
- Testes são scripts com `check()`, não pytest: "passou" = última linha `N PASS, 0 FAIL, de T testes` com N = T = o
  esperado.
- ISO 8855 (X frente, Y esquerda, Z cima); α < 0 dá Fy > 0 à esquerda (convenção do projeto, `mmm.alfa_rodas`); toe + =
  toe-out (EDR-002). SI no núcleo.
- Nenhuma fórmula existente da planilha muda fora do catálogo aprovado pelo usuário. Mudança de planilha só pelo
  gerador; a saída vai para `build/`; a cópia para `excel/` é um commit próprio.
- A planilha viva do Drive nunca é gravada nem recalculada; ferramentas trabalham em cópia. Não salvar planilha de
  referência pelo LibreOffice.
- Nada de valor inventado: valor sem fonte é "a confirmar"; sintético ou demonstrativo é rotulado.
- Commits separados por propósito (executor, física Python, estudo, relatório, gerador, cópia, dados). Push, PR, merge,
  tag e Drive só com a confirmação do usuário.
- Comandos de mais de ~2 min (escada ~6 min por rodada, mutações, suíte inteira) rodam em segundo plano.
- Docstrings e textos em português, no estilo dos módulos vizinhos (densidade de comentário igual à de `equilibrio.py`).
- Encerrar processo só por PID, nunca por nome de programa.

## IDs autorizados (usuário, 2026-10-29: "lista enxuta")

> Nota: renumerado de EDR-067 para EDR-069 em 2026-11-02 (colisão com o EDR-067 do PR #25, modelo estático de pneu; autorização do usuário).

EDR-069 (centro de curva único, raio do skidpad, decomposição 7-9, regulamento FSAE Brasil no inc. 9); EDR-068
(executor dos testes); revisão do EDR-065 item 2 (faixa do NEUTRO, depois do estudo); SUS-1009 (raio do skidpad R),
SUS-1010 (eixo que manda), SUS-1011 (meia largura do pneu); chaves `h2v` (forma do Ackermann) e `h9v` (forma do Fx
exigido); TC-RUN-001, TC-SKP-001 e 002, TC-ACK-001 e 002, TC-FXI-001 e 002, TC-NEU-001 e 002, TC-WB43-001 a 006.
Nenhum outro ID é criado. A aprovação de um ID não valida a equação.

## Decisões deste plano (registrar no EDR-069; as marcadas com ★ vão à aprovação célula a célula)

- **D1. `equilibrio.Formas` em vez de campo no caso.** `@dataclass(frozen=True) class Formas: ackermann:
  Literal["v42", "v43"] = "v42"; fx: Literal["v42", "v43"] = "v42"`, com `FORMAS_V42 = Formas()` e
  `FORMAS_V43 = Formas("v43", "v43")`. Entra como argumento só de palavra-chave (`formas=FORMAS_V42`) nas funções que
  usam a fórmula: `deriva_ackermann`, `deriva_total`, `grade_alfa`, `fy_eixo`, `fy_eixo_limitado`,
  `fx_exigido_traseira`, `elipse_traseira`, `capacidade_eixo`, `_varredura`, `analise_par` e
  `analise_par_dois_sentidos`. O padrão `FORMAS_V42` mantém todas as chamadas de hoje (spec §5).
- **D2. Duas réplicas do Fx novo em uma função:** `n_alfa: int | None`. Com um inteiro, é a réplica de grade (busca na
  grade de `grade_alfa(caso, n_alfa)` e interpolação linear, igual à célula); com None, é a réplica contínua (bisseção de
  200 iterações na curva, entre 0 e o α do pico de `capacidade_eixo(..., 401)`), usada como física. `equilibrio` não
  importa `mmm` (evita import circular), por isso a bisseção não usa `mmm._brent`.
- **D3. Sem curva dianteira, sem Fx (V4.3).** Se a capacidade dianteira da linha for inválida (descolamento, toe), o
  Fx da forma v43 não existe. A capacidade traseira da linha sai None com
  `MSG_FX_SEM_FRENTE = "Fx exigido (h9v) indisponível: a curva dianteira é inválida nesta linha"`. É conservador, e a
  planilha faz o mesmo (catálogo C-G4).
- **D4 ★. O R continua no endereço de hoje.** `16_EQUILIBRIO!B9` (nome `ent_16_raio_do_skidpad_r`, lido por milhares de
  fórmulas) deixa de ser entrada e passa a ser a fórmula que escolhe o R pelo modo. O nome fica igual, para que nenhuma
  fórmula que o cita mude de texto. O prefixo `ent_` fica errado até a reescrita para nomes do inc. 8. **Sem apelido**
  (decisão D do conselho, 2026-11-02): um segundo nome para a B9 quebraria o invariante "um nome por célula"
  (`tests/test_v4_0.py:101-108`) e repetiria o `{rusado}` da 24_CURVA. Um nome `ent_`/`org_` cuja célula é fórmula não é
  dado (`dados_planilha._destinos`, catálogo C-M1). O R digitado passa a ser a entrada nova `24_CURVA` "R manual". A `E9`
  (origem) vira a fórmula da pior origem do R. O `migrar_viva` leva B9, E9 e F9 da viva V4.2 para 24_CURVA B8, E8 e F8 e,
  com número em B9, põe o modo em "Manual" (C-M2, C-M3).
- **D5 ★. Modo padrão "Linha central".** O R deixa de vir vazio: 9,125 m com a fonte do regulamento. Ele só entra no
  resultado com h2, h3, h8 ou h9 ligada (padrão 0), mas o tempo de volta passa a ter valor. A alternativa, "Manual" com
  o R vazio, mantém o comportamento da V4.2.
- **D6 ★. Origem dos diâmetros do skidpad:** `● Dado do T11`, com a Fonte "Formula SAE Rules 2026 v1.0, D.10.1.1 (o
  regulamento da competição do T11; FSAE Brasil a conferir no inc. 9)". Não há rótulo de "regulamento" na lista Origens
  e o usuário pediu para não criar nomenclatura nova. A alternativa é tirar os diâmetros da pior origem, como as chaves.
- **D7. As bitolas já existem.** `05_VEHICLE` B7 (`ent_05_front_track_t_f`) e B8 (`ent_05_rear_track_t_r`). A V4.3 não
  cria uma entrada de bitola. Os 1300 mm do T11 (U3) são dado da equipe, entram por um commit `dados:` e não pelo
  gerador.
- **D8. Aba nova `24_CURVA`, depois da `23_LISTAS`:** entradas e resultados do R, as duas chaves e os θ. Nada se insere
  na 16, cujas colunas H a L estão ocupadas pela bisseção.
- **D9. Os avisos da V4.3 vão para a `14_DASHBOARD` A48:B48.** A linha está vazia na V4.2 e fica entre o bloco do
  equilíbrio (40-47) e o das metas (49-51), isto é, junto do veredito.
- **D10. Escada:** `degrau_2(caso, ay_max_g=2.0, incluir_v43=False)`. Com True, entra a linha `"planilha V4.3"` logo
  depois da `"planilha"` (que é a V4.2), com referência `"planilha"`. O padrão False mantém o TC-ESC-002 sem mudança.

## Foco da revisão (o que nenhum teste de tarefa pega sozinho)

1. Curva à direita: θ_i e o Fx novo no espelho. Esperado: o mesmo resultado do espelho da esquerda (TC-ACK-001 e
   TC-WB43-004 nos dois sentidos).
2. Força exigida acima do pico (LOOSE) e curva dianteira inválida na linha. Esperado: α limitado ao pico e Fx
   indisponível com motivo, nunca exceção nem #VALUE! (TC-FXI-002, TC-WB43-004 caso `LOOSE_PICO`).
3. Executor: um neto que herda a saída e trava. Esperado: o item termina dentro do orçamento, conta como FAIL, e o
   processo e o Excel daquele PID não sobram (TC-RUN-001).
4. Viva da V4.2 sem as entradas novas, com B9 preenchido ou vazio. Esperado: as entradas novas recebem o padrão, o R
   digitado vai para o R manual com o modo "Manual", e nada disso conta como conflito (TC-WB43-006).
5. R impossível: R ≤ b, R_in' ≤ L, bitola traseira vazia, meia largura vazia. Esperado: "a confirmar" com o motivo,
   nunca raiz de número negativo (TC-SKP-002, TC-WB43-004 modos).

## Delegação (gestor-tokens; o usuário autoriza o lote antes da execução)

| Tarefa | Agente | Modelo | Effort | Por quê |
|---|---|---|---|---|
| 1 Executor dos testes | general-purpose | sonnet | medium | desenho fixado aqui; conferível pelo TC-RUN-001 |
| 2 `skidpad.py` | general-purpose | sonnet | medium | geometria fechada na spec §3.2; oráculo por `hypot` |
| 3 Ackermann v43 | general-purpose | opus | high | física e convenção de sinal |
| 4 Fx v43 (duas réplicas e oráculo) | general-purpose | opus | high | física (balanço vetorial, O(ε³), elipse) |
| 5 Variantes no `mmm` e escada | general-purpose | sonnet | medium | plumbing especificado; regressão conferível |
| 6 Estudo do NEUTRO | general-purpose | opus | high | estudo numérico, ordem observada |
| 7 Mutação Python e relatório com dois R | general-purpose | sonnet | medium | mecânico, com a lista de mutantes fixada |
| 8 Recálculo medido e diagnóstico da barra de fórmulas | general-purpose | opus | high | depuração sem causa conhecida (COM) |
| 9 Faixa do NEUTRO decidida | general-purpose | sonnet | medium | regra escolhida pelo usuário |
| 10 a 12 Gerador da V4.3 e testes estruturais | general-purpose | sonnet | medium | células fixadas no catálogo |
| 13 Testes no Excel, mutação da planilha, migração | general-purpose | sonnet | medium | especificado; o Excel confere |
| 14 Suíte inteira e resumo | general-purpose | haiku | low | rodar e resumir a saída |
| Revisor por tarefa | general-purpose | o mesmo modelo da tarefa | medium (high nas 3, 4, 6 e 8) | — |
| Revisão final da branch (7a e 7b) | pr-review-toolkit:code-reviewer | opus | high | revisão crítica |

Ficam com a sessão principal: os registros no EDR, o texto do catálogo levado ao usuário e as decisões do passo do
usuário.

## Mapa de arquivos

| Arquivo | O quê |
|---|---|
| `python/executor_testes.py` (novo) | executa um comando com tempo-limite que encerra a árvore; orçamento |
| `tests/mutation_*.py`, `tools/rodar_testes.py` | passam a usar o executor |
| `tests/test_executor.py` (novo) | TC-RUN-001 |
| `python/skidpad.py` (novo) | R pelos dois métodos, eixo que manda, meia largura do `.tir` |
| `tests/test_skidpad.py` (novo) | TC-SKP-001 e 002 |
| `python/equilibrio.py` | `Formas`, θ por roda, Ackermann v43, Fx v43, `FATOR_NEUTRO` (Task 9) |
| `tests/test_formas_v43.py` (novo) | TC-ACK-001 e 002, TC-FXI-001 e 002 |
| `python/mmm.py`, `python/escada.py` | coluna `planilha_v43`, `Hipoteses.planilha_v43()`, linha da escada |
| `python/estudo_neutro.py` (novo), `tests/test_neutro.py` (novo) | estudo (TC-NEU-001) e regra decidida (TC-NEU-002) |
| `tests/mutation_inc7.py` (novo) | mutação Python do inc. 7 |
| `tools/relatorio_escada.py`, `docs/inc6/escada-hipoteses.md` | relatório com os dois R |
| `docs/inc7/estudo-neutro.md` (novo) | resultado do estudo para o usuário decidir |
| `python/aba_curva.py` (novo) | aba 24_CURVA e as células da V4.3 por família |
| `python/aba_equilibrio.py` | só funções novas chamadas pelo gerador da V4.3 (colunas novas das grades) |
| `python/gerar_v4_3.py` (novo), `data/nomes_V4_3.csv` (novo) | gerador da tag `v4.2` |
| `python/caso_planilha.py` | `caso_da_planilha_v43` (devolve o caso e as `Formas` lidas das chaves) |
| `tests/test_v4_3.py`, `tests/test_workbook_v4_3.py`, `tests/mutation_planilha_v43.py` (novos) | TC-WB43 e mutação |
| `python/dados_planilha.py` | `_destinos`: nome de dado com fórmula não é destino (C-M1) |
| `python/equilibrio_linear.py` | `formas=` repassado (C-E) |
| `tools/migrar_viva.py` | entradas novas com padrão; B9, E9, F9 → 24_CURVA B8, E8, F8; modo "Manual" (C-M2, C-M3) |
| `docs/registro-de-versoes-V4_3.md`, `docs/registro-de-versoes-V4_3-celulas.md` | registro |

---

# Parte 7a (só Python, PR próprio)

### Task 1: Executor dos testes (EDR-068)

**Arquivos:** Create `python/executor_testes.py`, `tests/test_executor.py`. Modify `tests/mutation_planilha_equilibrio.py`
(linhas 30 e 52-59), `tests/mutation_mmm.py`, `tests/mutation_equilibrio.py`, `tests/mutation_tire.py`,
`tools/rodar_testes.py:51-70` (`rodar`) e `TIMEOUT_MUTACAO`; `docs/Engineering_Decision_Register.md` (EDR-068).

**Interfaces:**
- Produz: `executar(cmd: list[str], *, cwd: Path | str, env: dict | None = None, timeout_s: float) -> Execucao`;
  `@dataclass(frozen=True) class Execucao: returncode: int; stdout: str; stderr: str; tempo_s: float; estourou: bool`;
  `class Orcamento: def __init__(self, total_s: float); def restante(self) -> float; def cabe(self, s: float) -> bool`;
  `orcamento_do_ambiente(padrao_s: float) -> Orcamento` (lê `DDS_ORCAMENTO_S`); `CODIGO_TEMPO = 124`.

- [ ] **Passo 1: diagnóstico que reproduz a causa provável.** Script descartável no scratchpad: um filho Python que
  lança um neto (`subprocess.Popen` sem redirecionar, herdando a saída), grava o PID do neto e dorme 60 s. Chamar com
  `subprocess.run(..., capture_output=True, timeout=3)` e medir o tempo até voltar. Esperado: ≈ 60 s e não 3 s
  (o neto segura o pipe). Anotar o tempo medido e a árvore (`tasklist /FI "PID eq <neto>"`) no EDR-068. Se voltar em
  ~3 s, a causa não é essa: parar e usar superpowers:systematic-debugging antes do Passo 3.
- [ ] **Passo 2: escrever o TC-RUN-001 em `tests/test_executor.py`** (um check com todas as afirmações):
  (a) o filho travado do Passo 1 com `timeout_s=3`: `estourou is True`, `returncode == CODIGO_TEMPO`,
  `tempo_s < 15`, e o neto não existe mais (`tasklist /FI "PID eq <pid>" /NH` sem o PID);
  (b) um filho que imprime `"ok á"` e sai com 0: `stdout.strip() == "ok á"`, `returncode == 0`, `estourou is False`;
  (c) `Orcamento(10).cabe(11) is False` e `cabe(5) is True`;
  (d) a regra da mutação: com `DDS_ORCAMENTO_S=5` e um mutante falso que trava, `mutation_planilha_equilibrio.rodar`
  devolve TIMEOUT contado como não detectado (FAIL) em menos de 15 s, sem 2ª tentativa (não cabe).
- [ ] **Passo 3: rodar e ver falhar** (`uv run python -X utf8 tests/test_executor.py`; ImportError de `executor_testes`).
- [ ] **Passo 4: implementar `executor_testes.py`.** `Popen` com stdout e stderr em `tempfile.TemporaryFile` (nunca
  pipe), `creationflags=CREATE_NEW_PROCESS_GROUP` no Windows. No tempo-limite, `taskkill /PID <pid> /T /F` (por PID;
  em POSIX, `os.killpg`), espera de 10 s, e lê os arquivos. O Excel do teste já está num Job Object
  (`tests/recalculo_planilha.py:55`) e morre com o neto. Hora de início e de fim por execução no `stderr` devolvido.
- [ ] **Passo 5: adotar nos chamadores.** `mutation_planilha_equilibrio.rodar`: orçamento total de
  `orcamento_do_ambiente(7000)`; tempo de cada rodada `min(TIMEOUT, restante)`; a 2ª tentativa só se
  `cabe(TIMEOUT)`; tempo esgotado = mutante "NÃO DETECTADO (tempo)" (FAIL), e a pré-checagem esgotada sai com código 2.
  Imprimir `tempo por rodada: X s`. `rodar_testes.rodar` usa `executar` e passa `DDS_ORCAMENTO_S = timeout − 200` ao
  item, para que a soma interna fique menor que a externa. Os outros três scripts de mutação trocam `subprocess.run` por
  `executar` (sem mudar a lógica).
- [ ] **Passo 6: rodar** `tests/test_executor.py` (esperado `1 PASS, 0 FAIL, de 1 testes`) e, em segundo plano,
  `tests/mutation_equilibrio.py` (esperado `6 / 6`) para conferir a adoção.
- [ ] **Passo 7: EDR-068 e `rodar_testes.TESTES`** (acrescentar `("executor dos testes", "tests/test_executor.py", 1,
  "plano do inc. 7 (TC-RUN-001)")` e `"executor_testes"` em `MODULOS`). Commit:
  `fix(testes): executor com tempo-limite que encerra a árvore (EDR-068, TC-RUN-001)`.

### Task 2: Raio do skidpad (`python/skidpad.py`; EDR-069, SUS-1009 a 1011)

**Arquivos:** Create `python/skidpad.py`, `tests/test_skidpad.py`; Modify `docs/Engineering_Decision_Register.md`
(EDR-069 com D1 a D10) e o registro dos SUS (onde estão os SUS-1001 a 1008).

**Interfaces:**
- Produz:
  - `D_INTERNO_M = 15.25`, `D_EXTERNO_M = 21.25`, `FONTE_DIAMETROS = "Formula SAE Rules 2026 v1.0 (10/09/2025), D.10.1.1"`;
  - `raio_linha_central(d_int: float, d_ext: float) -> float`;
  - `@dataclass(frozen=True) class RaioRente: raio_m: float | None; raio_c_m: float | None; eixo: str | None;
    motivo: str | None; sem_meia_largura: bool`, com `eixo` em `{"traseiro", "dianteiro", "empate"}`;
  - `raio_rente_aos_cones(d_int: float, L: float, b: float, t_f: float, t_r: float | None,
    meia_largura: float | None) -> RaioRente`;
  - `meia_largura_do_tir(ds: TireDataset) -> float` (`ds.p["WIDTH"] / 2`; KeyError vira ValueError com
    "WIDTH ausente no .tir");
  - `ORIGEM_MEIA_LARGURA = atualizar_planilha.TTC` (`"◐ Provisório (.tir TTC)"`);
  - `raio(modo: str, *, d_int, d_ext, L, b, t_f, t_r, meia_largura, r_manual) -> tuple[float | None, str | None]`, com
    `modo` em `{"linha_central", "rente_aos_cones", "manual"}`, que devolve (R, motivo).

- [ ] **Passo 1: testes.** **TC-SKP-001 (geometria):**
  (a) `raio_linha_central(15.25, 21.25) == 9.125`;
  (b) para (L, b, t_f, t_r, w) = (1.53, 0.765, 1.3, 1.3, 0.0889) (L e b sintéticos, rotulados no teste), a roda interna
  do eixo que manda fica a `hypot(x_i, R_c − t_i/2) == d_int/2 + w` (1e-12), a outra fica a ≥ esse valor, e
  `R == hypot(b, R_c)`;
  (c) um caso de empate construído (t_r escolhido para que os dois limites coincidam) dá `eixo == "empate"`;
  (d) R_in' ≤ L: a dianteira não restringe e o eixo é o traseiro.
  **TC-SKP-002 (entradas e modos):**
  `t_r=None` → `raio_m is None` com `motivo == "bitola traseira vazia: R rente aos cones a confirmar"`;
  `meia_largura=None` → usa 0 e `sem_meia_largura is True`;
  `raio("manual", r_manual=None, ...)` → `(None, "R manual vazio: a confirmar")`;
  `raio("manual", r_manual=8.0)` → `(8.0, None)`;
  `meia_largura_do_tir` do `.tir` em uso == 0.0889;
  modo inválido → ValueError.
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar.** As fórmulas são as da spec §3.2: R_c = max(R_in' + t_r/2, t_f/2 + √(R_in'² − L²)), com
  o termo dianteiro só se R_in' > L; empate quando a diferença dos dois limites é ≤ 1e-9 m; R = √(b² + R_c²). Sem
  constante física nova.
- [ ] **Passo 4: rodar** (`2 PASS, 0 FAIL, de 2 testes`); acrescentar em `rodar_testes.TESTES` e `MODULOS`.
- [ ] **Passo 5: commit** `feat(skidpad): R pelos dois métodos e modo manual (EDR-069, SUS-1009 a 1011)`. O EDR-069
  e os SUS vão num commit `docs:` separado.

### Task 3: Ackermann com o centro no eixo traseiro (forma v43)

**Arquivos:** Modify `python/equilibrio.py` (`Formas`, `angulos_velocidade`, `deriva_ackermann` e as funções da D1);
Create `tests/test_formas_v43.py` (TC-ACK-001).

**Interfaces:**
- Produz: `Formas`, `FORMAS_V42`, `FORMAS_V43` (D1); `angulos_velocidade(caso: CasoEquilibrio) -> dict` (θ [rad] por
  canto na curva à esquerda: θ_FL = atan(L/(R_c − t_f/2)), θ_FR = atan(L/(R_c + t_f/2)), θ_RL = θ_RR = 0, com
  R_c = √(R² − b²); R ≤ b dá ValueError "R ≤ b: o centro da curva não fica na linha do eixo traseiro");
  `deriva_ackermann(caso, *, formas=FORMAS_V42)`.
- **Sinal (na convenção do código):** v42, Δα_i = −(δ_i − δ_ref), como hoje. v43, Δα_i = −(δ_i − δ_ref) + (θ_i − θ̄_F)
  nas dianteiras e 0 nas traseiras, com θ̄_F = (θ_FL + θ_FR)/2. A spec §4.1 escreve a mesma forma com o sinal de |α|; com
  δ_i = θ_i, o termo some. Sem `ackermann_pct` (h2 desligada), zero nas duas formas.

- [ ] **Passo 1: TC-ACK-001 (física, um check).**
  (a) Oráculo independente: com ω × r a partir de C = (0, R_c) no referencial do eixo traseiro, o ângulo da velocidade
  de cada roda é `atan2(v_y, v_x)`, sem a fórmula atan(L/…). Ele coincide com `angulos_velocidade` (1e-12).
  (b) Com 100 % de Ackermann, a diferença do Δα v43 entre FL e FR é ≤ a cota de 2ª ordem
  |δ̄ − θ̄_F| ≤ (L/R)·(t_f/(2R_c))² + |δ_ref − atan(L/R_c)|. A cota é medida e o valor entra no docstring.
  (c) Com 0 %: Δα_FL − Δα_FR = (θ_FL − θ_FR) ≈ L·t_f/R_c² (1 % relativo só com R ≳ 15 m; a forma exata é atan(L·t_f/(R_c² + L² − t_f²/4))).
  (d) Curva à direita: `deriva_ackermann(espelhar(caso), formas=FORMAS_V43)` é a troca L↔R da esquerda.
  (e) `formas=FORMAS_V42` é igual ao valor de hoje (comparar com um valor congelado antes da mudança).
- [ ] **Passo 2: rodar e ver falhar.**
- [ ] **Passo 3: implementar `Formas`, `angulos_velocidade` e passar `formas` pelas funções da D1** (só palavra-chave,
  padrão `FORMAS_V42`).
- [ ] **Passo 4: rodar o TC-ACK-001 e as regressões** `tests/test_equilibrio.py` (28),
  `tests/test_equilibrio_linear.py` (18) e `tests/test_mmm.py` (11). Nenhuma muda.
- [ ] **Passo 5: commit** `feat(equilibrio): Ackermann com centro no eixo traseiro (forma v43, EDR-066)`.

### Task 4: Fx exigido por arrasto induzido (forma v43)

**Arquivos:** Modify `python/equilibrio.py` (`alfas_de_arrasto`, `fx_exigido_traseira`, `elipse_traseira`,
`capacidade_eixo`); `tests/test_formas_v43.py` (TC-FXI-001 e 002).

**Interfaces:**
- Consome: `Formas` (Task 3).
- Produz:
  - `alfas_de_arrasto(caso, ay_ms2, *, formas, n_alfa: int | None) -> tuple[float, float] | str` devolve (|α_F|, |α_R|)
    ou o motivo `MSG_FX_SEM_FRENTE`. α_F vem da curva dianteira (com cos δ_ref); α_R vem da curva traseira sem o fator
    da elipse. Cada α é o primeiro em que a força do eixo alcança a exigida (`forca_exigida`); se a força em α_ref = 0
    já alcança, α = 0; se não alcança até o pico, α é o do pico.
  - `fx_exigido_traseira(caso, ay_ms2, *, formas=FORMAS_V42, n_alfa: int | None = None) -> float | str`. Na v42 é
    o de hoje. Na v43, F_yf·|α_F| + F_yr·|α_R| + arrasto + Crr·m·G, e o motivo (str) quando falta a curva dianteira.
  - `elipse_traseira(..., *, formas=FORMAS_V42, n_alfa=None)` devolve `(None, MSG_FX_SEM_FRENTE)` nesse caso.
  - `capacidade_eixo` passa `formas` e o próprio `n_alfa` (réplica de grade, igual à célula).
  - Oráculo: `fx_balanco_exato(caso, ay_ms2, alfa_f: float, alfa_r: float) -> float`.

- [ ] **Passo 1: TC-FXI-001 (equivalência e física, um check).**
  (a) Réplica de grade × contínua: |Δ| ≤ cota do passo, (F_yf + F_yr)·h_α/2 com h_α o passo da grade.
  (b) Oráculo exato: `fx_balanco_exato` faz o balanço longitudinal em X do carro, F_pneu,f·sen δ − m·A·sen β, com
  δ = atan(L/R_c) + α_F − α_R e β = atan(b/R_c) − α_R. A diferença para o arrasto induzido cai como O(ε³), ε = max(α, L/R), com α e L/R
  escalados juntos (R → 2R); com R fixo, o resto tem termos α(L/R)² e a razão tende a 2. A razão das diferenças fica em [6, 10].
  (c) `formas=FORMAS_V42` é igual ao valor de hoje.
- [ ] **Passo 2: TC-FXI-002 (elipse, pico, sem frente; um check).**
  (a) Ponto fixo com a elipse (α_R da curva com o fator de cada iteração, até |ΔFx| < 1e-6 N) contra a aproximação sem
  elipse: o erro relativo é medido e impresso, e o check só exige que o ponto fixo convirja e que o erro seja finito.
  Não se supõe cota.
  (b) Caso LOOSE com a força traseira exigida acima do pico: α_R = α do pico, o veredito não vira N/A por isso
  (`analise_par(..., formas=FORMAS_V43)` dá LOOSE).
  (c) Caso com descolamento da dianteira numa linha: a capacidade traseira dessa linha sai None com `MSG_FX_SEM_FRENTE`.
- [ ] **Passo 3: rodar e ver falhar.**
- [ ] **Passo 4: implementar.** Interpolação linear entre os pontos j−1 e j da grade, em |α|. A bisseção da réplica
  contínua tem 200 iterações.
- [ ] **Passo 5: rodar TC-FXI-001/002 e as regressões da Task 3.**
- [ ] **Passo 6: commit** `feat(equilibrio): Fx exigido por arrasto induzido (forma v43, EDR-066)`.

### Task 5: Variantes no `mmm` e linha "planilha V4.3" da escada (TC-ACK-002)

**Arquivos:** Modify `python/mmm.py:41-145`, `alfa_rodas`, `_raiz_eixo`, `trim`, os caminhos que chamam
`eq.deriva_total`, `eq.fx_exigido_traseira`, `eq.capacidade_eixo` e `eq.analise_par`; `python/escada.py` (`degrau_2`,
D10); `tests/test_formas_v43.py` (TC-ACK-002).

**Interfaces:**
- Consome: `eq.Formas`, `FORMAS_V42`, `FORMAS_V43`.
- Produz:
  - `_VALORES["alfa"] = ("planilha", "eixo_traseiro", "cinematico")`; `_VALORES["fx_exigido"] = ("edr057", "arrasto",
    "balanco")`;
  - em cada entrada de `VARIANTES`, a chave `"planilha_v43"` (alfa: `"eixo_traseiro"`; fx_exigido: `"arrasto"`; nas
    outras, o mesmo valor de `"planilha"`);
  - `Hipoteses.planilha_v43()`;
  - `formas_de(hip: Hipoteses) -> eq.Formas`;
  - `_e_acoplada`, em que uma variante só leva ao acoplado se não estiver em `{VARIANTES[c]["planilha"],
    VARIANTES[c]["planilha_v43"]}`.
  - No acoplado, `fx_exigido="arrasto"` usa `eq.fx_exigido_traseira(caso, ay, formas=FORMAS_V43, n_alfa=None)`.
  - `escada.NOME_PLANILHA_V43 = "planilha V4.3"`.

- [ ] **Passo 1: TC-ACK-002 (contrato e regressão, um check).**
  (a) O `assert` de `mmm.py:114` continua valendo.
  (b) `Hipoteses.planilha()` não muda, e `formas_de(Hipoteses.planilha()) == eq.FORMAS_V42`.
  (c) `_e_acoplada(Hipoteses.planilha_v43()) is False`.
  (d) `mmm.limite(caso, Hipoteses.planilha_v43())` é igual ao limite montado com `eq.analise_par(caso,
    formas=FORMAS_V43)` (mesmo veredito; saturações a 2·resolução, o critério `escada._julga`).
  (e) `degrau_2(caso, incluir_v43=True)` tem a linha "planilha V4.3" em 2º lugar, com `referencia == "planilha"`.
  Para baratear, roda `degrau_2` com `ay_max_g=1.0` num caso pequeno.
- [ ] **Passo 2: rodar e ver falhar.** **Passo 3: implementar.**
- [ ] **Passo 4: regressão** `tests/test_mmm.py` (11) e, em segundo plano, `tests/test_escada.py` (3, ~6 min) sem
  mudança.
- [ ] **Passo 5: commit** `feat(mmm): variante planilha_v43 e linha da escada (EDR-066)`.

### Task 6: Estudo da faixa do NEUTRO (TC-NEU-001; sem mudar a regra)

**Arquivos:** Create `python/estudo_neutro.py`, `tests/test_neutro.py`, `docs/inc7/estudo-neutro.md`.

**Interfaces:**
- Produz:
  - `@dataclass(frozen=True) class Convergencia: eixo: str; s: tuple[float | None, ...]; p: float | None;
    razao: float | None; dif_nula: bool`, com s nas grades h, h/2, h/4 e h/8 e p = log2(|s_h − s_h/2| /
    |s_h/2 − s_h/4|);
  - `estudar(caso, *, formas=FORMAS_V42, passo_g=0.05, n_alfa=25) -> dict` com as chaves `"F"`, `"R"`
    (`Convergencia`), `"erro_delta"`, `"soma_erros"` e `"ramo"` (`"dois"` ou `"um"`);
  - `casos_perturbados(caso) -> dict[str, CasoEquilibrio]`: λ_f ± 10 %, toe ± 0,1°, R ± 10 %, todos rotulados
    "sintético".

- [ ] **Passo 1: TC-NEU-001 (um check).** No caso V4.2 sintético de `test_escada.veiculo_base`:
  (a) as grades são aninhadas (a h/2k contém os pontos da h);
  (b) `estudar` é determinístico (duas chamadas iguais);
  (c) `erro_delta`, medido contra a grade h/8 como referência, é ≤ `soma_erros`, ou o caso é listado como violação.
  A regra não muda: `analise_par` dá o mesmo veredito de antes.
- [ ] **Passo 2: rodar e ver falhar; implementar; rodar.**
- [ ] **Passo 3: gerar `docs/inc7/estudo-neutro.md`** (em segundo plano: 4 grades × casos). Tabelas de p por eixo e
  caso, a frequência de diferença ≈ 0 (< 1e-9 g), o erro de Δ contra e_F + e_R e as três alternativas da spec §4.3, com
  o efeito de cada uma nos casos. Sem recomendação disfarçada de decisão.
- [ ] **Passo 4: commits** `feat(estudo): convergência das saturações (TC-NEU-001)` e `docs(inc7): estudo da faixa
  do NEUTRO`.

### Task 7: Mutação Python e relatório da escada com os dois R

**Arquivos:** Create `tests/mutation_inc7.py`; Modify `tools/relatorio_escada.py` (opção `--metodo-raio`),
`docs/inc6/escada-hipoteses.md`, `tools/rodar_testes.py` (`MUTACAO`).

- [ ] **Passo 1: `mutation_inc7.py`** no padrão de `tests/mutation_mmm.py` (cópia mutada no PYTHONPATH, sonda, executor
  da Task 1). Cinco mutantes, cada um mirando exatamente um ponto: sinal de θ_i em `deriva_ackermann` v43; α_F ↔ α_R
  em `fx_exigido_traseira` v43; sem o limite no pico em `alfas_de_arrasto`; método de R trocado
  (`raio_linha_central` → `(d_int + d_ext)/2`); `soma_erros` sem o e_R no estudo. Detectado = algum FAIL dos TC-ACK,
  TC-FXI, TC-SKP ou TC-NEU. Esperado `5 / 5`.
- [ ] **Passo 2: `relatorio_escada.py --metodo-raio {linha_central,rente_aos_cones}`.** O R sai de `skidpad.raio` com
  as bitolas do caso, mais a provisória `--bitola-m 1.3` (U3, rotulada "provisória do T11") quando o caso não tiver
  bitola. A origem do R vai automaticamente para `--origem-raio`. O relatório roda `degrau_2(..., incluir_v43=True)`.
- [ ] **Passo 3: gerar o relatório com as duas rodadas** (em segundo plano, ~6 min cada), num arquivo só com duas
  seções. A tolerância do EDR-065 continua pendente e o relatório não classifica nada como "dentro da tolerância".
- [ ] **Passo 4: suíte inteira em segundo plano** (`tools/rodar_testes.py`), conferindo as contagens novas.
  Commits: `test(inc7): mutação Python` e `docs(inc6): relatório da escada com os dois R`.
- [ ] **Passo 5: revisão final da 7a** (code-reviewer opus/high) e PR da 7a só com a confirmação do usuário.

---

## Passo do usuário (entre a 7a e a 7b)

Levar ao usuário, numa mensagem: o relatório da escada (tolerância do EDR-065), o estudo do NEUTRO (escolha entre as
alternativas 1, 2 e 3), as decisões D4, D5 e D6 e o catálogo abaixo, para a aprovação célula a célula. As escolhas vão
ao EDR (EDR-065 item 2 revisto; EDR-069). Sem essa aprovação a 7b não começa. Se a alternativa 3 (refino parabólico)
for escolhida, o catálogo ganha a família C-F12b (fórmulas de `cap_` e `idx_` em todas as grades), escrita e aprovada
num adendo antes da Task 11.

---

# Parte 7b (V4.3, PR próprio)

### Task 8: Recálculo medido e diagnóstico da barra de fórmulas

**Arquivos:** Modify `tools/medir_recalculo.py` (aceitar `--arquivo`); Create `build/prototipo_v43.xlsx` (só em
`build/`, nunca commitado).

- [ ] **Passo 1: protótipo.** Um script descartável aplica à V4.2 da tag só as colunas novas das grades (C-G1 a C-G4)
  e mede o recálculo no Excel com `tools/medir_recalculo.py`, contra a V4.2. Registrar os dois tempos. Se o aumento
  passar de 2×, levar ao usuário antes de aprovar o C-G (alternativa: limitar as colunas novas à grade pedida).
- [ ] **Passo 2: diagnóstico da barra de fórmulas** (spec §7), no Excel via COM, numa cópia da V4.2 e numa cópia
  baixada do Drive (somente leitura). Conferir, nesta ordem:
  - `ws.ProtectContents`;
  - `Range.FormulaHidden`;
  - `Application.DisplayFormulaBar`;
  - `Application.ProtectedViewWindows.Count` (Modo de Exibição Protegido, marca da internet `Zone.Identifier`);
  - `Range.HasArray`;
  - `Range.HasFormula` numa célula nomeada (B84) e numa não nomeada (17_EQ_PAR BP24).
  Registrar o resultado. Se a causa for do gerador, a correção vai para a Task 10 (C-B1). Se for do ambiente, vai para
  o LEIA-ME (Task 14). Se nada reproduzir, registrar "não reproduzido", com o que foi conferido, e levar ao usuário.
- [ ] **Passo 3: `MATCH/INDEX` no LibreOffice (ajuste 9 do conselho).** Recalcular uma cópia do protótipo também pelo
  LibreOffice (EDR-044; nunca a referência nem a viva) e comparar, linha a linha, `j_F`, `j_R`, `aF` e `aR` com os do
  Excel. Casos: requisito abaixo do primeiro ponto (j = 1), no meio da grade, acima do pico (`IFERROR` → 0) e a coluna
  "-". Se o LibreOffice não avaliar a forma ou divergir, escolher uma forma sem matriz equivalente (por exemplo, colunas
  auxiliares 0/1 por α), medir de novo o recálculo, registrar a escolha como adendo da C-G3 e levá-la ao usuário antes
  da Task 11.
- [ ] **Passo 4: commit** `docs(inc7): tempo de recálculo, diagnóstico da barra de fórmulas e MATCH/INDEX no LibreOffice`.

### Task 9: Faixa do NEUTRO decidida (TC-NEU-002)

**Arquivos:** Modify `python/equilibrio.py` (`FATOR_NEUTRO` e `_resolucao` ou a regra do veredito), `python/mmm.py`
(regra da folga das acopladas lendo a mesma constante), `tests/test_neutro.py`.

- [ ] **Passo 1: TC-NEU-002**, com a regra escolhida pelo usuário: o veredito do `analise_par` e o do `mmm.limite`
  (acoplado) usam a mesma `FATOR_NEUTRO` (uma fonte só, EDR-064 1.3).
  **Decisão do usuário (2026-11-02): alternativa 1 com `FATOR_NEUTRO = 4/3` fixo, só no |S − S2|** (EDR-065 item 2;
  decisão A do conselho). Em `_resolucao`, o fator multiplica a diferença |S − S2| de cada eixo que satura nas duas
  grades; o passo (eixo que satura numa grade só) e o piso 1E-9 ficam sem o fator. O ramo de um eixo só (push1/loose1)
  lê a mesma resolução. A planilha faz o mesmo (catálogo C-F2). Casos: um NEUTRO na borda da faixa nova; um PUSH logo
  fora dela; um eixo que satura numa grade só (a resolução é o passo, igual à de hoje).
- [ ] **Passo 2: implementar; regressões 28/18/11/3** (as que mudarem de veredito são listadas e justificadas, não
  afrouxadas).
- [ ] **Passo 3: commit** `feat(equilibrio): faixa do NEUTRO (EDR-065 item 2 revisto)`.

### Task 10: Aba `24_CURVA`, R, chaves e avisos (`python/aba_curva.py`)

**Arquivos:** Create `python/aba_curva.py`.

**Interfaces:**
- Produz: `montar_24(wb) -> list[dict]` (registro de células no formato de `gerar_v4_2.aplicar`);
  `alteracoes_v4_3(wb) -> list[dict]` (C-B, C-D); `ENTRADAS24` (dataclass `aba_equilibrio.Entrada`);
  `celulas_de_entrada_v43() -> set[tuple[str, str]]` (as da V4.1 menos `("16_EQUILIBRIO", "B9")` mais as da 24).

- [ ] **Passo 1:** células C-A1 a C-A22, C-B1 a C-B10, C-F1, C-F5 e C-D1 a C-D2 do catálogo, com nomes pelas regras do
  EDR-058 (`nomes_v4_0`, `_nome_ent` e `_nome_res` com o prefixo 24) e a pior origem do R por
  `aba_equilibrio._formula_pior`, sobre as raízes (`python/raizes.py`) dos termos do C-A17.
- [ ] **Passo 1b (Python, só por adição):** `aba_equilibrio.VERIFICACOES_24` e `VERIFICACOES_V43` (a lista da 16 com o
  item "num" do R trocado pelo tipo `num_r` da C-B4, mais as da 24); `motivo_das_entradas(x, verificacoes=VERIFICACOES)`
  passa a tratar `""` como vazio (ajuste 5) e a receber `motivo_r`, `b` e `tF` em `x` quando a lista da V4.3 é usada.
  Constantes novas com o texto do catálogo: `skidpad.MOTIVO_MODO_INVALIDO`, `MOTIVO_DIAMETROS`, `MOTIVO_VEICULO`,
  `equilibrio.MSG_GEOMETRIA`, `MSG_FATOR`. `VERIFICACOES`, `_cond_verif` e o texto de `angulos_velocidade` não mudam
  (a regeneração da V4.1 e da V4.2 fica igual).
- [ ] **Passo 2:** o teste é o TC-WB43-001 (Task 12). Commit junto com a Task 12.

### Task 11: Colunas novas das grades, F3, F9 e F12 (aba_equilibrio, só funções novas)

**Arquivos:** Modify `python/aba_equilibrio.py`: acrescentar `colunas_v43(n_alfa, pedida) -> dict` (as colunas depois
da última de `_colunas`) e `linha_grade_v43(ctx, ws, cl, k, r, n_alfa)`; nenhuma função existente muda de
comportamento.

- [ ] **Passo 1:** células C-C1 a C-C3, C-G1 a C-G6 e C-F2 a C-F4 do catálogo, aplicadas pelo gerador da V4.3 nas abas
  17, 18, 20a a 20d (pedida: linhas 24-64; fina: 94-174 nas 20a-d; 24-104 na 18) e na mini-grade da 19 (C-E2), com
  `linha_grade_v43` sobre `CL_MINI`; `_linha_grade` não é editado no lugar (decisão C).
- [ ] **Passo 1b (C-E, Python):** `equilibrio_linear` ganha `formas: Formas = FORMAS_V42` (só de palavra-chave) nas
  funções listadas na C-E, repassado a `_fy_eixo_limitado`, `capacidade_eixo` e `deriva_total`. Regressão: os 18 testes
  do equilíbrio linear e os 28 do equilíbrio sem mudança.
- [ ] **Passo 2:** os endereços exatos de cada família saem do gerador no `docs/registro-de-versoes-V4_3-celulas.md`;
  o TC-WB43-001 confere que o diff de texto V4.2 → V4.3 é exatamente esse registro. Commit junto com a Task 12.

### Task 12: `gerar_v4_3.py`, tabela de nomes e testes estruturais (TC-WB43-001 e 002)

**Arquivos:** Create `python/gerar_v4_3.py` (padrão de `gerar_v4_2.py`: `extrair_v42`, `_recusar`, `aplicar`,
`escrever_registro_v43`, `gerar(v42, saida, registro, csv_nomes)`, `copia_v43`), `data/nomes_V4_3.csv`,
`tests/test_v4_3.py`; Modify `python/caso_planilha.py` (`caso_da_planilha_v43(xlsx_recalculado, tir) ->
tuple[CasoEquilibrio, Formas]`).

- [ ] **Passo 1: TC-WB43-001 (estrutura, sem motor, um check).** Abas na ordem (+ `24_CURVA` no fim); as fórmulas da
  V4.2 iguais fora do registro de células; o diff de texto é exatamente o registro; os nomes são os da V4.2 mais os do
  CSV, sem apelido (um nome por célula, D4); `ent_16_raio_do_skidpad_r` continua em B9, com estilo de resultado e sem
  validação numérica (C-B2); as validações da C-A20 (chaves `"0,1"`); todo leitor de `{R}` está guardado por `raio`,
  `h8`, `h9` ou `ok`, e nenhum usa `ISBLANK({R})` (lista do catálogo, refeita a partir do gerador); nenhuma aba tem
  `ProtectContents` e nenhuma célula com fórmula tem `protection.hidden` (C-B1); A3 diz "V4.3"; a linha 23 do
  15_CHANGELOG.
  **TC-WB43-002 (CA-07):** duas regenerações iguais, e iguais a `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx` quando ele
  existir; o texto de 24_CURVA B34 é `=4/3` e `equilibrio.FATOR_NEUTRO == 4/3`.
- [ ] **Passo 2: rodar e ver falhar; implementar; rodar** (`2 PASS, 0 FAIL, de 2 testes`).
- [ ] **Passo 3: commit** `feat(v4.3): gerador da V4.3 (24_CURVA, h2v, h9v, R; TC-WB43-001 e 002)`.

### Task 13: Testes no Excel, mutação da planilha e migração (TC-WB43-003 a 006)

**Arquivos:** Create `tests/test_workbook_v4_3.py`, `tests/mutation_planilha_v43.py`; Modify `tools/migrar_viva.py`.

- [ ] **Passo 1: TC-WB43-003 (regressão por valor).** A V4.3 com h2v = h9v = 0, modo "Manual" e R manual = o B9 da
  V4.2, e a V4.2, recalculadas no Excel com as mesmas entradas (casos C1, C4b, ORG_TX do `test_workbook_v4_1`, com h2 e
  h9 ligadas): mesmos valores fora das células novas (1e-9 relativo). **Excluídas** (decisão B): 16 B137 a B139 e as
  células que dependem delas (fecho transitivo pelo `raizes.Grafo`: B140 a B143, os textos de exibição do veredito, o
  14_DASHBOARD do veredito e as mesmas linhas de `_regras_limite` na 20_EQ_TROCA), porque o 4/3 não tem chave. A lista
  excluída sai do grafo e é impressa no log. Caso a mais: modo "Manual" com o R manual vazio e h2 = h3 = h8 = h9 = 0
  contra a V4.2 com B9 vazio; mudam só os textos da B65 e da B173 (o motivo entre parênteses, C-B4/C-B7), listados como
  mudança intencional.
- [ ] **Passo 2: TC-WB43-004 (célula × Python, mudança intencional).** Com h2v = h9v = 1, nos dois sentidos de curva e
  nos três modos de R, as células novas e o veredito batem com `caso_da_planilha_v43` + `analise_par(formas=...)`
  (réplica de grade: 1e-9 relativo nos α e no Fx; o veredito igual). Inclui o caso `LOOSE_PICO` (força acima do pico)
  e um caso com a dianteira descolada (motivo C-G6). Casos novos do conselho, cada um com o `status`, o `ok` e o motivo
  iguais aos de `motivo_das_entradas(..., verificacoes=VERIFICACOES_V43)` e aos do Python:
  - geometria: R ≤ b e R_c ≤ t_f/2 com h2 = h2v = 1 (`MSG_GEOMETRIA`, `ok` = 0, B114 "N/A"); os mesmos com h2v = 0
    (sem efeito);
  - chaves: h2v = 2, h2v vazia e h9v = "1" (texto) → "chave h2v/h9v deve ser 0 ou 1";
  - modo do R: "linha central" (caixa errada) e um texto qualquer → R `""` e `MOTIVO_MODO_INVALIDO`; com h2 = 1, o
    `status` cita esse motivo na B65;
  - diâmetros: D_int vazio e D_ext ≤ D_int → `MOTIVO_DIAMETROS`; R_in' ≤ L (C-A11b em texto, eixo "traseiro");
  - Manual com o R manual vazio e h2 = 1 → B65 e B173 com "(R manual vazio: a confirmar)";
  - fator: cópia com 24_CURVA B34 = 0,5 → `MSG_FATOR`, `ok` = 0;
  - 4/3: um caso perto do neutro em que o veredito muda da V4.2 para a V4.3 (mesmo do TC-NEU-002) e um com um eixo
    saturado numa grade só (resolução = passo, sem o fator);
  - aba 19: K e a mini-grade com h2v = h9v = 1 contra `equilibrio_linear` com `formas=FORMAS_V43` (C-E);
  - 14_DASHBOARD B48 nos três estados (padrão, h2v = 0, chave inválida) e o E173 com a pior origem do R.
  Os testes da V4.2 que mudam de valor com o padrão 1 ficam listados aqui como mudança intencional.
- [ ] **Passo 3: TC-WB43-005 (barra de fórmulas):** abre a V4.3 pelo Excel via COM e confere, em B84, B9 e 17_EQ_PAR
  BP24, `HasFormula` True, `FormulaHidden` False e a aba sem proteção.
- [ ] **Passo 4: TC-WB43-006 (migração, sem motor; fica em `tests/test_v4_3.py`, que passa a ter 3 TCs):** implementar
  antes C-M1 a C-M4 (`dados_planilha._destinos` e o redirecionamento V4.2 → V4.3 no `migrar_viva`). Casos, numa viva
  V4.2 de teste:
  - B9 = 8,3 → R manual (24_CURVA B8) 8,3, modo "Manual", as entradas novas no padrão, 0 conflitos, código 0;
  - B9 vazio → o modo fica no padrão "Linha central" (D5), B8 vazio;
  - E9 trocado pela equipe (por exemplo `◐ Dado de outro carro (TX, T09)`) → vai para 24_CURVA E8, e a E9 da V4.3
    continua fórmula;
  - F9 trocado pela equipe → vai para 24_CURVA F8, sem conflito;
  - os nomes `ent_16_raio_do_skidpad_r` e `org_16_raio_do_skidpad_r` não aparecem como destino na V4.3 (C-M1);
  - viva V4.3 de teste com B9 ou E9 sobrescritos por um número → código 2, "célula alterada fora dos nomes de dado"
    (C-M4).
  A regressão da migração V4.1 → V4.2 (`tests/test_v4_2.py`, TC-WB42-004) continua passando.
- [ ] **Passo 5: `mutation_planilha_v43.py`** (padrão de `mutation_planilha_equilibrio.py`, com o executor da Task 1 e
  o orçamento medido na Task 8): sinal de θ no C-C1; aF ↔ aR no C-G5; sem o limite no pico no C-G4; modo de R trocado
  no C-A14. Esperado `4 / 4`. (Os endereços antigos, C-F2 e C-A13, eram os da versão do catálogo antes do conselho.)
- [ ] **Passo 6: commits** `test(v4.3): ...`, `feat(viva): migração para a V4.3`.

### Task 15: Caso sintético para a tolerância do EDR-065 (usuário, 2026-11-02)

Última tarefa da 7b, porque a V4.3 não depende dela. Um caso sintético rotulado, com Ackermann (h2) e tração (h9)
ligados e um eixo que sature antes de 2 g, rodado pelo `tools/relatorio_escada.py` com `incluir_v43=True`; a tabela
vai ao usuário para decidir a tolerância do EDR-065 item 3. Nenhum valor do caso é dado do carro; nenhum ID novo.
Commit `docs(inc6): escada num caso sintético que satura`.

### Task 14: Cópia, registro, suíte inteira e fechamento

- [ ] **Passo 1:** `uv run python -X utf8 python/gerar_v4_3.py` → `build/`; a cópia para `excel/` é um commit próprio
  (`copia: V4.3 de referência`).
- [ ] **Passo 2:** `docs/registro-de-versoes-V4_3.md`; CLAUDE.md (contagens: executor 1, skidpad 2, formas 4,
  NEUTRO 2, `test_v4_3` 3 (001, 002, 006), `test_workbook_v4_3` 3 (003 a 005), mutação inc7 5/5 e planilha V4.3 4/4); `tools/rodar_testes.py` (PLANILHAS, MUTACAO, `versao_planilhas` com a V4.2 obrigatória).
- [ ] **Passo 3: suíte inteira em segundo plano** (haiku/low resume a saída). Só depois disso o trabalho é dado como
  verificado.
- [ ] **Passo 4:** revisão final (opus/high); PR da 7b, Drive (`conferir_viva`, `migrar_viva`, LEIA-ME e .docx) e tag,
  cada um só com a confirmação do usuário. O LEIA-ME e os .docx do Drive avisam que a 16 B9 virou fórmula e que o R
  digitado fica em 24_CURVA B8 (ajuste 10).

---

# Catálogo das células da V4.3 (para a aprovação célula a célula)

Revisto em 2026-11-03 com os ajustes 1 a 10 e as decisões A a D de `docs/inc7/conselho-catalogo-v43.md`.

Notação: `{x}` é o nome definido gerado pelas regras do EDR-058; o texto final da célula leva o nome, como na V4.2.
"Antes" é o texto da V4.2 da tag. "Dep." são as células que ela lê. "Testes" é o TC que cobre a célula (003 = TC-WB43-003
etc.; "mut." = `mutation_planilha_v43.py`).

Nomes novos usados nas fórmulas (aba 24_CURVA, prefixo 24; o texto exato sai de `_nome_ent`/`_nome_res`): `{modo}` B4,
`{dint}` B5, `{dext}` B6, `{w}` B7, `{rman}` B8, `{h2v}` B9, `{h9v}` B10, `{vh2v}` B11, `{vh9v}` B12, `{rlc}` B13, `{rin}` B14, `{lim_tras}` B15,
`{lim_diant}` B16, `{rc}` B17, `{rrente}` B18, `{eixo}` B19, `{rusado}` B20, `{motivo_r}` B21, `{rcc}` B22, `{pior_r}` B23,
`{thFL}` B25, `{thFR}` B26, `{thm}` B27, `{vgeo}` B28, `{fator}` B34, `{vfat}` B35, `{sit24}` B37. Nomes que já existem:
`{R}` (16 B9, `ent_16_raio_do_skidpad_r`), `{L}`, `{b}`, `{tF}`, `{tR}`, `{h2}`…`{h9}`, `{ok}`, `{status}`.

Textos fixos novos (constantes Python com o mesmo texto; nenhum ID novo): `skidpad.MOTIVO_MODO_INVALIDO` = "modo do R
inválido (use Linha central, Rente aos cones ou Manual)"; `skidpad.MOTIVO_DIAMETROS` = "diâmetros do skidpad a confirmar
(D_ext > D_int > 0)"; `skidpad.MOTIVO_VEICULO` = "L, b ou t_f a confirmar (05_VEHICLE)"; `equilibrio.MSG_GEOMETRIA` =
"geometria do centro da curva inválida (R ≤ b ou R_c ≤ t_f/2)"; `equilibrio.MSG_FATOR` = "fator da faixa do NEUTRO
(24_CURVA B34) deve ser número ≥ 1". As constantes que já existem (`MOTIVO_MANUAL_VAZIO`, `MOTIVO_BITOLA_TRASEIRA`,
`MOTIVO_SEM_MEIA_LARGURA`) entram nas células com o mesmo texto.

Leitores do R (16 B9) conferidos no gerador (`aba_equilibrio.py` 661, 662, 665, 698, 700, 753, 1092-1110, 1248, 1289): todos
estão dentro de `raio = 1`, `h8 = 1` ou `h9 = 1` e de `ok`, e o `ok` exige R número > 0 quando `raio = 1` (B65, B66).
Por isso o `""` que a B9 passa a ter com o R vazio não chega a nenhuma conta. As duas exceções são as que testavam
`ISBLANK`, e elas mudam aqui (C-B4 e C-B7). O TC-WB43-001 refaz essa lista a partir do gerador e falha se aparecer um
leitor novo sem guarda.

## C-A. Aba nova `24_CURVA` (todas novas; antes: não existe)

Colunas como na 16: A rótulo, B valor, C unidade, D referência, E Origem, F Fonte. Linha 1: título; linha 3: cabeçalho.
As entradas (B4 a B10) têm nomes `ent_`/`org_`/`fte_` (são dado e migram nas próximas versões). As demais linhas são
resultados `res_`, com estilo de resultado.

| # | Célula | Rótulo | Conteúdo novo | Dep. | Justificativa | Testes |
|---|---|---|---|---|---|---|
| C-A1 | B4 | Modo do raio R | entrada; lista `"Linha central,Rente aos cones,Manual"`; padrão "Linha central" (D5) | — | U2, U4 | 004, 006 |
| C-A2 | B5 | Diâmetro do círculo interno | 15,25 m; E = `● Dado do T11` (D6); F = `skidpad.FONTE_DIAMETROS` (FSAE 2026 D.10.1.1) | — | spec §3.2 | 004 |
| C-A3 | B6 | Diâmetro do círculo externo | 21,25 m; idem | — | idem | 004 |
| C-A4 | B7 | Meia largura do pneu | 0,0889 m; E = `◐ Provisório (.tir TTC)`; F = WIDTH/2 do `Hoosier_R25B_13x7_TTC_provisional.tir` (SUS-1011) | — | spec §3.2 | 004 |
| C-A5 | B8 | R manual | entrada vazia; E = `? A confirmar`; F = "R digitado (modo Manual). Na migração da V4.2, recebe o B9 da viva." | — | modo manual; D4 | 003, 006 |
| C-A6 | B9 | Chave h2v: forma do Ackermann | 1; lista `"0,1"` (como as chaves da 16, `aba_equilibrio.py:1121`); F = "1 = centro da curva no eixo traseiro (V4.3, EDR-066); 0 = velocidades paralelas (V4.2)" | — | U6; ajuste 1 | 003, 004 |
| C-A7 | B10 | Chave h9v: forma do Fx exigido | 1; lista `"0,1"`; F = "1 = arrasto induzido (V4.3, EDR-066); 0 = F_yf·tan(L/R) (V4.2)" | — | U6; ajuste 1 | 003, 004 |
| C-A8a | B11 | Verificação: chave h2v deve ser 0 ou 1 | `=IF(ISNUMBER({h2v}),IF(OR({h2v}=0,{h2v}=1),"-","chave h2v deve ser 0 ou 1"),"chave h2v deve ser 0 ou 1")` (o mesmo texto de `_cond_verif` tipo "chave") | A6 | ajuste 1: chave vazia ou texto não vira 0 em silêncio | 004 |
| C-A8b | B12 | Verificação: chave h9v deve ser 0 ou 1 | idem com `{h9v}` | A7 | idem | 004 |
| C-A9 | B13 | R da linha central | `=IF(AND(ISNUMBER({dint}),ISNUMBER({dext}),{dint}>0,{dext}>{dint}),({dint}+{dext})/4,"")` | A2, A3 | SUS-1009; ajuste 3 | 004 |
| C-A10 | B14 | R_in' (raio interno + meia largura) | `=IF(AND(ISNUMBER({dint}),ISNUMBER({dext}),{dint}>0,{dext}>{dint}),{dint}/2+IF(ISNUMBER({w}),{w},0),"")` | A2, A3, A4 | §3.2; ajuste 3 | 004 |
| C-A11a | B15 | Limite traseiro R_in' + t_r/2 | `=IF(AND(ISNUMBER({rin}),ISNUMBER({tR})),{rin}+{tR}/2,"")` | A10, 05 B8 | `skidpad.raio_rente_aos_cones` (`lim_tras`); ajuste 10 | 004 |
| C-A11b | B16 | Limite dianteiro t_f/2 + √(R_in'² − L²) | `=IF(AND(ISNUMBER({rin}),ISNUMBER({L}),ISNUMBER({tF})),IF({rin}>{L},{tF}/2+SQRT({rin}^2-{L}^2),"- (R_in' ≤ L)"),"")` | A10, 05 B6, B7 | `lim_diant` (−∞ no Python vira texto: o MAX de referências ignora texto); ajuste 10 | 004 |
| C-A11 | B17 | R_c rente aos cones | `=IF(AND(ISNUMBER({lim_tras}),{lim_diant}<>""),MAX({lim_tras},{lim_diant}),"")` | A11a, A11b | §3.2 | 004 |
| C-A12 | B18 | R rente aos cones | `=IF(AND(ISNUMBER({rc}),ISNUMBER({b})),SQRT({b}^2+{rc}^2),"")` | A11, res_05 b | §3.2; ajuste 3 | 004 |
| C-A13 | B19 | Eixo que manda (SUS-1010) | `=IF(NOT(ISNUMBER({rc})),"-",IF(NOT(ISNUMBER({lim_diant})),"traseiro",IF(ABS({lim_tras}-{lim_diant})<=1E-9,"empate",IF({lim_tras}>{lim_diant},"traseiro","dianteiro"))))` | A11a, A11b, A11 | §3.2 (`TOL_EMPATE_M`) | 004 |
| C-A14 | B20 | R usado | `=IFERROR(IF(EXACT({modo},"Manual"),IF(ISNUMBER({rman}),{rman},""),IF(EXACT({modo},"Linha central"),{rlc},IF(EXACT({modo},"Rente aos cones"),{rrente},""))),"")` | A1, A5, A9, A12 | U4; ajustes 2 e 5: os três ramos explícitos, modo inválido dá `""`, nunca erro | 003, 004, mut. |
| C-A15 | B21 | Motivo do R | `=IF(NOT(OR(EXACT({modo},"Linha central"),EXACT({modo},"Rente aos cones"),EXACT({modo},"Manual"))),MOTIVO_MODO_INVALIDO,IF(ISNUMBER({rusado}),IF(AND(EXACT({modo},"Rente aos cones"),NOT(ISNUMBER({w}))),MOTIVO_SEM_MEIA_LARGURA,"-"),IF(EXACT({modo},"Manual"),MOTIVO_MANUAL_VAZIO,IF(NOT(ISNUMBER({rin})),MOTIVO_DIAMETROS,IF(NOT(ISNUMBER({tR})),MOTIVO_BITOLA_TRASEIRA,MOTIVO_VEICULO)))))` (constantes = os textos entre aspas) | A1, A4, A5, A10, A14 | ajuste 2: o modo inválido é testado primeiro (o Python levanta ValueError, `skidpad.py:84`); ajuste 3 | 004 |
| C-A16 | B22 | R_c do centro da curva | `=IF(NOT(ISNUMBER({rusado})),"-",IF(NOT(ISNUMBER({b})),"-",IF({rusado}<={b},"R ≤ b: a confirmar",SQRT({rusado}^2-{b}^2))))` | A14, res_05 b | §3.1; ajuste 3: R vazio dá "-", R ≤ b tem mensagem própria | 004 |
| C-A17 | B23 | Pior origem do R | `_formula_pior` por modo: Linha central → E5, E6; Rente → E5, E6, E7 e as raízes de b, L, t_F, t_R; Manual → E8; modo inválido → `? A confirmar` | A1… | §3.2 | 004 |
| C-A18 | B25, B26 | θ_FL, θ_FR | `=IF(AND({h2v}=1,ISNUMBER({rcc}),ISNUMBER({L}),ISNUMBER({tF})),IF({rcc}>{tF}/2,ATAN({L}/({rcc}-{tF}/2)),"-"),"-")`; a FR com `+{tF}/2` no denominador e a mesma guarda (`rcc > tF/2`, como `equilibrio.angulos_velocidade`) | A16, A6 | §3.1, §4.1; ajuste 4 | 004, mut. |
| C-A18b | B27 | θ̄_F | `=IF(AND(ISNUMBER({thFL}),ISNUMBER({thFR})),({thFL}+{thFR})/2,"-")` | A18 | ajuste 4 (guarda na média) | 004 |
| C-A21 | B28 | Verificação: geometria do centro da curva | `=IF(AND({h2}=1,{h2v}=1,ISNUMBER({R}),ISNUMBER({b}),ISNUMBER({tF})),IF({R}<={b},MSG_GEOMETRIA,IF(SQRT({R}^2-{b}^2)<={tF}/2,MSG_GEOMETRIA,"-")),"-")` | 16 B9, res_05 b, 05 B6, A6 | ajuste 4: R ≤ b ou R_c ≤ t_f/2 leva `ok` a 0 antes da B114; mesma condição do Python (`equilibrio.py:280-286`) | 004 |
| C-A19 | A30:A32 | Texto: hipóteses só no Python (h7 `sentido` e as acopladas: `cos_delta`, `tracao`, `diferencial`, `transf_long`) e limitação do centro no eixo traseiro (α_R desloca o centro; medido pela escada) | texto | — | U6, §3.1 | 001 |
| C-A22 | B37 | Situação da 24_CURVA (1ª falha) | `=IF({vh2v}<>"-",{vh2v},IF({vh9v}<>"-",{vh9v},IF({vfat}<>"-",{vfat},{vgeo})))` (B11, B12, B35, B28, nesta ordem) | A8a, A8b, F5, A21 | ajustes 1, 4 e 10: as verificações novas levam `ok` a 0 sem inserir linhas na 16 (D8) | 004 |
| C-A20 | — | Validações | B4: lista dos três modos; B9, B10: lista `"0,1"`; B5, B6, B7, B8: decimal > 0 (ajuste 3; a B7 entra pela mesma razão); E4:E10: lista Origens | — | ajustes 1 e 3 | 001 |

A ordem das verificações da 24 no Python é `VERIFICACOES_24 = (chave h2v, chave h9v, fator, geometria)`, lida depois das
`VERIFICACOES` da 16 (`motivo_das_entradas(x, verificacoes=VERIFICACOES_V43)`). As listas e o `_cond_verif` da V4.1/V4.2
não mudam (a regeneração da V4.1 e da V4.2 continua igual, CA-07).

## C-B. Células existentes fora das grades

| # | Aba!Célula | Antes | Depois | Dep. | Justificativa | Testes |
|---|---|---|---|---|---|---|
| C-B1 | todas | (proteção a confirmar na Task 8) | sem `ProtectContents` e sem `protection.hidden` em célula com fórmula, se a Task 8 indicar o gerador | — | §7 barra de fórmulas | 001, 005 |
| C-B2 | 16_EQUILIBRIO!B9 | entrada vazia (`None`), estilo de entrada, validação "positivo" | `={rusado}` (D4); estilo de resultado; sem a validação numérica (`aba_equilibrio.py:1052`) | C-A14 | U4; ajuste 6; nenhuma fórmula que lê B9 muda de texto | 001, 003, 004 |
| C-B3 | 16_EQUILIBRIO!E9 | `? A confirmar` (lista Origens) | `={pior_r}` (fórmula; a validação de lista sai) | C-A17 | D16 e a pior origem continuam pela E9 | 004 |
| C-B9 | 16_EQUILIBRIO!A9 | "Raio do skidpad R" | "R usado (fórmula; ver 24_CURVA)" (o nome definido não muda) | — | ajuste 6: a B9 não pode parecer entrada | 001 |
| C-B5 | 16_EQUILIBRIO!F9 | "A confirmar (regulamento). Vazio = sem dado. Exigido por h2, h3, h8 e h9 e pelo tempo de volta." | "Não digite aqui: o R manual fica em 24_CURVA B8 (modo em B4). Fórmula da V4.3 (EDR-069, D4); exigido por h2, h3, h8 e h9 e pelo tempo de volta." | — | D4; ajuste 6 | 001 |
| C-B4 | 16_EQUILIBRIO!B65 (verificação "num" do R) | `=IF(OR({h2}=1,{h3}=1,{h8}=1,{h9}=1),IF(ISBLANK({R}),"raio do skidpad R a confirmar",IF(ISNUMBER({R}),"-","raio do skidpad R não é número")),"-")` | `=IF(OR({h2}=1,{h3}=1,{h8}=1,{h9}=1),IF(ISNUMBER({R}),"-",IF(ISERROR({R}),"raio do skidpad R com erro",IF({R}="","raio do skidpad R a confirmar ("&{motivo_r}&")","raio do skidpad R não é número"))),"-")` | C-B2, C-A15 | ajuste 5: a B9 é fórmula e o `ISBLANK` nunca seria verdadeiro; a ordem ISNUMBER, ISERROR, `=""` evita erro na comparação | 004 |
| C-B7 | 16_EQUILIBRIO!B173 (`tvolta`, `aba_equilibrio.py:752-754`) | `=IF(ISNUMBER({aylim}),IF(ISBLANK({R}),"N/A: raio do skidpad R a confirmar",IF(ISNUMBER({R}),IF({R}>0,2*PI()*SQRT({R}/{aylim}),"N/A: raio do skidpad R deve ser > 0"),"N/A: raio do skidpad R não é número")),"N/A")` | `=IF(ISNUMBER({aylim}),IF(ISNUMBER({R}),IF({R}>0,2*PI()*SQRT({R}/{aylim}),"N/A: raio do skidpad R deve ser > 0"),IF(ISERROR({R}),"N/A: raio do skidpad R com erro",IF({R}="","N/A: raio do skidpad R a confirmar ("&{motivo_r}&")","N/A: raio do skidpad R não é número"))),"N/A")` | C-B2, C-A15, aylim | ajuste 5 (a mesma troca do `ISBLANK`) | 003, 004 |
| C-B7b | 16_EQUILIBRIO!E173 | `={PIOR}` | `_formula_pior` sobre `{PIOR}` e `{pior_r}`, sem condição: o tempo de volta usa o R mesmo com h2, h3, h8 e h9 em 0 | C-A17 | risco do conselho: o tempo de volta passa a ter valor com o R do regulamento (D5), e a origem tem de aparecer | 004 |
| C-B8 | 16_EQUILIBRIO!B78 (`status`) | `=IF({G_vfN}="-","OK",{G_vfN})` (N = última verificação da 16) | `=IF({G_vfN}="-",IF({sit24}="-","OK",{sit24}),{G_vfN})` | C-A22 | ajustes 1, 4 e 10: as verificações da 24 levam `ok` (B80) a 0; as da 16 continuam primeiro | 003, 004 |
| C-B10 | 16_EQUILIBRIO!F142 (observação do veredito) | vazia | "NEUTRO: \|S_r − S_f\| ≤ resolução (B139); com o eixo saturado nas duas grades, a diferença entra multiplicada pelo fator 4/3 da 24_CURVA B34 (EDR-065 item 2)" | — | ajuste 10: o texto cita a faixa com o fator; a fórmula da B142 não muda | 001 |
| C-B6 | 00_README!A3 e 15_CHANGELOG linha 23 | V4.2 | V4.3 (texto no gerador) | — | padrão das versões | 001 |

## C-C. F3: Ackermann (16_EQUILIBRIO)

| # | Célula | Antes | Depois | Dep. | Justificativa | Testes |
|---|---|---|---|---|---|---|
| C-C1 | B114 (Δα FL) | `=IF(ok,IF(h2=1,-toe_FL+(-(di-dref)),-toe_FL),"N/A")` | `=IF(ok,IF(h2=1,-toe_FL+(-(di-dref))+IF({h2v}=1,{thFL}-{thm},0),-toe_FL),"N/A")` | C-A6, C-A18, C-A18b | spec §4.1 (EDR-066); com h2 = h2v = 1, o `ok` garante a geometria válida (C-A21) e θ numérico | 003, 004, mut. |
| C-C2 | B115 (Δα FR) | idem com `toe_FR` e `do` | idem com `+IF({h2v}=1,{thFR}-{thm},0)` | idem | idem | 003, 004 |
| C-C3 | B116, B117 (traseiras) | sem mudança (θ = 0 atrás) | — | — | — | 003 |

Com h2v = 0, o valor é o da V4.2 (TC-WB43-003). A amplitude da grade (B118) muda de valor, não de texto.

## C-G. F9: Fx exigido nas grades (17, 18, 20a a 20d e a mini-grade da 19; uma família por coluna, em todas as linhas de dados)

Colunas novas depois da última da V4.2 (17 e as pedidas das 20a-d: a partir de FI; 18 e as finas das 20a-d: a partir
de GO; mini-grade da 19: depois da última de `CL_MINI`): `fy0_R_0 … fy0_R_{n−1}`, `cap0_R`, `idx0_R`, `j_F`, `j_R`, `aF`,
`aR`. O α de cada coluna i é o da linha 17 (α_ref) da mesma coluna de `fy_F_i`. Antes: as colunas novas não existem.
Justificativa comum: spec §4.2 (EDR-066) e D3; α_R da curva sem a elipse (sem referência circular); α limitado ao pico.

| # | Coluna | Antes | Depois (linha r) | Dep. | Testes |
|---|---|---|---|---|---|
| C-G1 | `fy0_R_i` | nova | `=IF(AND({h9}=1,{h9v}=1,ISNUMBER(Fz_RL),Fz_RL>0,ISNUMBER(Fz_RR),Fz_RR>0,ISNUMBER({amp}),{amp}>0),fyL_i+fyR_i,"-")`, com fyL_i e fyR_i as mesmas expressões da soma traseira de `_linha_grade`, sem `fat` (ajuste 10: `ISNUMBER({amp})`) | termos MF da linha | 003, 004 |
| C-G2 | `cap0_R`, `idx0_R` | nova | `=IF(ISNUMBER(fy0_R_0),MAX(faixa),"-")`; `=IF(ISNUMBER(cap0_R),MATCH(cap0_R,faixa,0),"-")` | C-G1 | 004 |
| C-G3 | `j_F`, `j_R` | nova | `=IFERROR(MATCH(TRUE,INDEX(faixa_fy_F>=req_F,0),0),0)` (na traseira, `faixa_fy0_R` e `req_R`). **Condicionada à Task 8:** o protótipo roda no Excel e no LibreOffice (EDR-044); se o LibreOffice não avaliar a forma, a Task 8 escolhe uma forma sem matriz equivalente, registra-a aqui como adendo e a leva ao usuário (ajuste 9) | fy_F, C-G1 | 004, Task 8 |
| C-G4 | `aF` | nova | `=IF(AND({h9}=1,{h9v}=1),IF(pre_F<>"-","semF",IF(req_F>=cap_F,ABS(INDEX(alfa,idx_F)),IF(j_F<=1,0,ABS(INDEX(alfa,j_F-1)+(INDEX(alfa,j_F)-INDEX(alfa,j_F-1))*(req_F-INDEX(fyF,j_F-1))/(INDEX(fyF,j_F)-INDEX(fyF,j_F-1)))))),"-")` | C-G3 | 004 (`LOOSE_PICO`) |
| C-G4b | `aR` | nova | igual, com `cap0_R`, `idx0_R`, `j_R`, `req_R` e `fy0_R`, e o primeiro teste `NOT(ISNUMBER(cap0_R))` no lugar de `pre_F<>"-"` (o `pre_R` depende de `fat`, que depende de `aR`: usá-lo seria referência circular; com a traseira descolada, o `pre_R` já dá o descolamento antes do texto de tração) | C-G2, C-G3 | 004, mut. |
| C-G5 | `fxr` (BP, existente) | `=IF(AND(ISNUMBER(phi),{h9}=1),0.5*rho*cda*ABS(ay)*R+crr*m*9.81+ABS(req_F)*{tanf},0)` | `=IF(AND(ISNUMBER(phi),{h9}=1),IF(AND({h9v}=1,OR(aF="semF",aR="semF")),"semF",0.5*rho*cda*ABS(ay)*R+crr*m*9.81+IF({h9v}=1,req_F*aF+req_R*aR,ABS(req_F)*{tanf})),0)` | C-G4 | 003, 004, mut. |
| C-G6 | `fat_RL`, `fat_RR` (BW, CD; existentes) e `pre_R` (DL / EJ) | `fat` e `pre_R` da V4.2 | `fat`: primeiro teste `IF({C("fxr")}="semF","semF", <fórmula de hoje>)`; `pre_R`: no texto de tração, antes de "fora", `IF(OR(fat_RL="semF",fat_RR="semF"),"Fx exigido (h9v) indisponível: a curva dianteira é inválida nesta linha", …)` (`MSG_FX_SEM_FRENTE`) | C-G5 | 003, 004 |

`16_EQUILIBRIO!B86` (tanf) não muda: continua sendo o termo da h9v = 0. Na mini-grade da 19, as colunas novas saem de
`linha_grade_v43` sobre `CL_MINI`, e as trocas C-G5 e C-G6 se aplicam às colunas `fxr`, `fat` e `pre_R` dela. O
`_linha_grade` não é editado no lugar (decisão C).

## C-E. Aba 19 (K linear): segue a V4.3 (decisão C)

| # | Célula | Antes | Depois | Dep. | Justificativa | Testes |
|---|---|---|---|---|---|---|
| C-E1 | 19_EQ_LINEAR, células que leem `{da_FL}`/`{da_FR}` (`aba_equilibrio.py:1418`) e as linhas K das 20 que repetem a `_linha19` | — | texto sem mudança; o valor muda com h2v = 1 (via C-C1/C-C2) | C-C1, C-C2 | a 19 acompanha o Ackermann da 16 | 003, 004 |
| C-E2 | mini-grade da 19 (3 linhas a partir de `LINHA_MINI19`) | colunas de `_colunas(N_ALFA, False)` | as mesmas, mais as colunas C-G1 a C-G4b e as trocas C-G5/C-G6 | C-G | a capacidade nos pontos de Richardson usa o Fx da V4.3 | 003, 004 |

No Python, `equilibrio_linear` ganha `formas: Formas = FORMAS_V42` (só de palavra-chave) em `tabela_linear`,
`parcelas_k`, `angulos_necessarios`, `_rigidez_eixo`, `_rigidez_camber_eixo`, `_forca_deslocamento` e
`_parcela_deslocamento`, repassado a `_eq._fy_eixo_limitado` (hoje sem `formas`, `equilibrio_linear.py:177-178`),
`capacidade_eixo` e `deriva_total`. Com o padrão, os 18 testes do equilíbrio linear não mudam.

## C-F. F12: faixa do NEUTRO (16_EQUILIBRIO B137, B138 e as mesmas linhas de `_regras_limite` no bloco "cálculo por linha" da 20_EQ_TROCA)

Decidido pelo usuário em 2026-11-02 (EDR-065 item 2 e decisão A do conselho): fator fixo 4/3 **só no |S − S2|** de cada
eixo (o d1 de Richardson, que o estudo mostrou subestimado). O passo (0,05 g), usado quando o eixo satura numa grade e
não na outra, fica sem o fator. A resolução (B139) e o veredito (B142) não mudam de texto; o ramo de um eixo só (push1,
loose1) lê a mesma resolução. O fator não tem chave (decisão B): por isso o TC-WB43-003 exclui B137 a B139 e o que
depende delas, e o TC-WB43-004 e o TC-NEU-002 cobrem o 4/3.

| # | Célula | Antes | Depois | Dep. | Justificativa | Testes |
|---|---|---|---|---|---|---|
| C-F1 | 24_CURVA B34 (nova) | não existe | rótulo "Fator da faixa do NEUTRO"; `=4/3`; nome `res_` (constante do modelo, não é dado e não migra); E = `○ Estimativa`; F = "EDR-065 item 2; docs/inc7/estudo-neutro.md (casos sintéticos)". Fica fora da pior origem, como o passo e o 1E-9 da resolução | — | igual a `equilibrio.FATOR_NEUTRO` (TC-WB43-002 confere o texto `=4/3` e a constante) | 002 |
| C-F5 | 24_CURVA B35 (nova) | não existe | `=IF(ISNUMBER({fator}),IF({fator}>=1,"-",MSG_FATOR),MSG_FATOR)` (entra na C-A22) | C-F1 | ajuste 10: `ISNUMBER` e ≥ 1 | 004 |
| C-F2 | B137 / B138 (dif_F, dif_R) | `=IF(AND(ISNUMBER({S_F}),ISNUMBER({S2_F})),ABS({S_F}-{S2_F}),IF(OR(ISNUMBER({S_F}),ISNUMBER({S2_F})),0.05*9.81,"-"))` (e o R) | `=IF(AND(ISNUMBER({S_F}),ISNUMBER({S2_F})),IF(ISNUMBER({fator}),{fator}*ABS({S_F}-{S2_F}),"-"),IF(OR(ISNUMBER({S_F}),ISNUMBER({S2_F})),0.05*9.81,"-"))` (e o R) | C-F1 | decisão A; com o fator inválido o `ok` já é 0 (C-F5) e a célula dá "-" em vez de #VALUE! | 004, mut. |
| C-F3 | B139 (resol) | `MAX(dif_F, dif_R, 1E-9*9.81)` | sem mudança | — | — | 004 |
| C-F4 | B142 (ver) | — | sem mudança de texto (a observação F142 é a C-B10) | — | — | 004 |

Justificativa: `docs/inc7/estudo-neutro.md` (Tabela 8): única alternativa com margem faixa − erro de Δ positiva nos 7
casos sintéticos perto do neutro.

## C-D. Avisos (14_DASHBOARD)

| # | Célula | Antes | Depois | Dep. | Justificativa | Testes |
|---|---|---|---|---|---|---|
| C-D1 | A48 / B48 | vazias | "Formas da V4.3 (24_CURVA)" / `=IF({sit24}<>"-","24_CURVA: "&{sit24},IF(AND({h2v}=1,{h9v}=1),"V4.3: Ackermann com o centro da curva no eixo traseiro e Fx por arrasto induzido (mudou em relação à V4.2; para voltar à V4.2, h2v = 0 e h9v = 0 em 24_CURVA B9 e B10)","forma da V4.2 em uso (h2v = "&{h2v}&", h9v = "&{h9v}&"): resultado não comparável com a V4.3 padrão"))&". R = "&IF(ISNUMBER({rusado}),SUBSTITUTE(FIXED({rusado},3,TRUE),".",",")&" m ("&IF(EXACT({modo},"Manual"),"manual",LOWER({modo})&", diâmetros do regulamento FSAE 2026 D.10.1.1")&")",{motivo_r})` | C-A1, A6, A7, A14, A15, A22 | ajuste 8: o que mudou, como voltar, chave inválida, modo do R inválido e o R do regulamento como tal | 004 |
| C-D2 | C48 / D48 | vazias | "-" / "EDR-066; EDR-069" (padrão das linhas 41-47) | — | — | 001 |

## C-M. Migração e nomes (`dados_planilha`, `migrar_viva`; sem célula nova)

| # | Onde | Antes | Depois | Justificativa | Testes |
|---|---|---|---|---|---|
| C-M1 | `dados_planilha._destinos(wb)` (`dados_planilha.py:65-80`), usado por `ler_por_nome`, `injetar` e `migrar_viva` | todo nome `ent_`/`org_`/`fte_` é destino | um nome `ent_`/`org_`/`fte_` cuja célula, no workbook lido, é fórmula (texto que começa com "=" ou `ArrayFormula`) não é dado e sai dos destinos. `eh_dado(nome)` continua só pelo nome; a regra única fica no `_destinos`. Na V4.2 nenhum nome de dado tem fórmula, então nada muda para ela | ajuste 7: na V4.3, B9 (`ent_`) e E9 (`org_`) são fórmulas | 006 |
| C-M2 | `migrar_viva` V4.2 → V4.3 | o nome vai para a mesma célula | redirecionamento fixo por par de versões: `ent_16_raio_do_skidpad_r` → R manual (24_CURVA B8); `org_16_…` (E9) → 24_CURVA E8; `fte_16_…` (F9) → 24_CURVA F8. Nos nomes redirecionados, a base da comparação é o padrão da V4.3 (a célula nova ainda não tem dado da equipe), então o valor da equipe é escrito sem conflito | ajuste 7; o F9 entra porque o F8 padrão difere do F9 da V4.2 e daria conflito falso | 006 |
| C-M3 | `migrar_viva`, modo do R | — | se a viva tem número em B9, o modo (24_CURVA B4) recebe "Manual"; com B9 vazio, o modo fica no padrão "Linha central" (D5) | D4 | 006 |
| C-M4 | viva V4.3 com B9 ou E9 sobrescritos à mão | — | a célula alterada não tem nome de dado (C-M1) e o `migrar_viva` sai com código 2, "célula alterada fora dos nomes de dado" | protege as fórmulas | 006 |

---

## Autoverificação (feita ao escrever)

- Cobertura da spec: §2 itens 1-5 → Tasks 1, 2, 3-5, 6, 7; §3 → Task 2 e C-A; §4.1 → Task 3 e C-C; §4.2 → Task 4 e
  C-G; §4.3 → Tasks 6 e 9 e C-F; §5 → D1, D10, Task 5 e C-A6/7 (chave 0 até a V5.0); §6.1 → Task 1; §6.2 → Tasks 2 a 7;
  §6.3 → Tasks 8, 12 e 13; §7 → Tasks 8 a 14 e o catálogo; §8 → ordem das tasks; §9 → IDs autorizados (lista enxuta).
- Lacunas assumidas: a alternativa 3 do NEUTRO tem só o gancho do adendo, e os endereços das linhas F12 na 20_EQ_TROCA
  saem do gerador (registro de células). As duas coisas são decididas no passo do usuário.
- Nomes consistentes: `Formas`, `FORMAS_V42`, `FORMAS_V43`, `formas=`, `n_alfa`, `MSG_FX_SEM_FRENTE`, `planilha_v43`,
  `eixo_traseiro`, `arrasto`, `NOME_PLANILHA_V43`, `h2v` e `h9v` são os mesmos em todas as tasks.
