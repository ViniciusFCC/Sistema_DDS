# Subprojeto A — pneu com variação de pressão: plano de implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou
> superpowers:executing-plans para executar este plano tarefa a tarefa. Os passos usam caixas (`- [ ]`) para
> acompanhamento.

**Objetivo:** comparar os quatro perfis R25B (8, 10, 12 e 14 psi) no pneu e no carro, apoiar a escolha da pressão
com uma banda heurística e uma regra simétrica, e expor a pressão contínua (A2) por interpolação rotulada das saídas.

**Arquitetura:** a camada estática (`tire_model_static`) só ganha uma recusa e uma mensagem nova. Dois módulos novos:
`tire_pressure` (A2, métricas e indicadores do pneu, com o avaliador passado como função) e `comparacao_pressao`
(o caso do equilíbrio rodado com o `ds` de cada perfil e a escolha). Um relatório em `tools/` junta tudo em `build/`.
Nada entra na planilha.

**Tecnologia:** Python 3.13 (uv), numpy/scipy já no projeto; matplotlib **só** no relatório, por
`uv run --with matplotlib` (não entra no `pyproject.toml`). Testes são scripts com `check()`, não pytest.

**Spec:** `docs/superpowers/specs/2026-11-02-pneu-estado-design.md` (commits b889db9 e 9aa73d3). Quem executa lê
a spec e este plano.

## Restrições globais

- Antes de todo `uv run` no Git Bash: `export UV_SYSTEM_CERTS=1`. Nunca `python`/`python3` direto.
- Os `.tir` ficam fora do Git, em `references/ttc/round6_hoosier_r25b_20p5x7_13_7in/` da raiz do repositório
  principal (de um worktree: `../../../references/...`) ou em `DDS_TTC_DIR`. Sem eles o teste sai **NÃO EXECUTÁVEL**
  com código 3, que nunca conta como aprovado. Não versione `*.tir`.
- As chaves de `StaticTireFamily.profiles` não são inteiras: 7.999992, 10.000062, 11.999987 e 14.000058 psi. Toda
  comparação de pressão usa `ts.PRESSURE_TOLERANCE_PSI` (1e-3), e os pesos da interpolação usam as chaves reais.
- IDs autorizados (usuário, 2026-11-03): **EDR-071** e **TC-TIRE-011** em diante. Nenhum outro ID novo. EDR-068 e
  EDR-069 estão em uso em outras branches.
- Rótulos em toda saída do A (spec §5): R25B ≠ R60A (nem a tendência se transfere com certeza); μ absoluto do TTC não
  transferível; pressão de ensaio ≠ pressão fria (a confirmar); Validation = NOT_VALIDATED; INTERPOLADO quando for o
  caso; caso demonstrativo T09/E03 com coeficientes de 12 psi como linha de base, não o T11.
- Fora do escopo (spec §4): A2 no carro, ajuste PP*/QPZ, `ds` por eixo, raio carregado e altura de rodagem,
  qualquer mudança na planilha.
- Nenhum coeficiente, alvo ou limite inventado. "Banda" é faixa heurística, nunca intervalo de confiança.
- Commits separados por propósito (documentação do EDR, código, registro na suíte). Mensagens terminam com
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Contagens que não podem mudar: `tests/test_tire_static.py` 87/87 e `tests/test_tire_model.py` 43/43.

## Foco da revisão

Entradas que a spec implica, nenhum teste dos grupos da §10 cobre, e que mais provavelmente quebrariam o uso real.
Cada uma ganhou um teste na tarefa dona do código:

1. **Pressão pedida como 8, 10, 12 ou 14 inteiros** (as chaves reais são 7.999992 etc.): `evaluate_interpolated(F, 12.0, ...)`
   tem de cair no nó exato, bit a bit, e `14.0` não pode ser recusado como "fora de [8, 14]". Teste na Tarefa 3.
2. **Fz de operação acima do teto comum de 1521 N** (a roda externa no a_y limite passa disso): a grade das métricas
   avalia em 1521 N e rotula, sem exceção. Teste na Tarefa 4.
3. **Caso cujo `ds` difere do perfil de 12 psi em coeficiente que não é λ** (a equipe editou a 10_TIRE): o
   `perfil_ajustado` trocaria esse coeficiente pelo do `.tir` em silêncio. `comparar_carro` tem de listar a
   diferença nos rótulos. Teste na Tarefa 6.
4. **a_y_lim N/A** (descolamento, ou pico na borda que impede a saturação, provável a 14 psi): `escolher_pressao` não
   pode quebrar nem tratar N/A como valor; a pressão vira "não decidível" com o motivo. Teste na Tarefa 7.
5. **Banda indisponível** (o LOO de 10 psi precisa de 8 e 12; se um deles for N/A, não existe): a pressão vira "não
   decidível (banda indisponível)" e nunca é declarada a melhor. Teste na Tarefa 7.

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `docs/Engineering_Decision_Register.md` | Modificar | EDR-071 (índice, §5, §6), emenda do item 6 do EDR-067 |
| `python/tire_model_static.py` | Modificar | `__version__` 4.2.0, guarda QPZ1-2/QPX1, mensagem do `at_pressure`, overlays da 4.1.0 aceitos |
| `python/tire_pressure.py` | Criar | `evaluate_interpolated` (A2), faixas, métricas do pneu, LOO, assimetria, monotonicidade |
| `python/comparacao_pressao.py` | Criar | `perfil_ajustado`, `kphi_com_kt`, `comparar_carro`, bandas, `escolher_pressao` |
| `tools/relatorio_pressao.py` | Criar | `.md` e PNG em `build/` com a família real e o caso da V4.1 |
| `tests/test_tire_pressure.py` | Criar | Grupos 1 a 13 da §10 da spec, IDs TC-TIRE-011 a TC-TIRE-023 |
| `tools/rodar_testes.py` | Modificar | Registro do conjunto "pneu com pressão" |
| `CLAUDE.md` | Modificar | Contagem esperada do novo teste na linha "Esperado" |

Correspondência entre grupo da §10 e ID: grupo *n* → `TC-TIRE-0(10+n)`, com subitens `a`, `b`, … no nome do
`check()`, como em `tests/test_tire_model.py` (`"TC-TIRE-011a: ..."`).

---

### Tarefa 1: EDR-071 (decisão registrada antes do código)

O CLAUDE.md manda registrar a decisão antes ou durante a implementação; por isso o EDR vem primeiro, como APPROVED,
e a Tarefa 9 o passa a VERIFIED com a evidência.

**Arquivos:**
- Modificar: `docs/Engineering_Decision_Register.md` (linha 3, cabeçalho; linha 36, contagem; índice após a linha
  103; nova seção após o EDR-067, antes de `## 6.`; linha nova na tabela §6 após a 1563; EDR-067 linha 1494 em diante)

- [ ] **Passo 1: Escrever o EDR-071 no formato do EDR-067** (mesmos campos, na mesma ordem: Date, Status, Context,
  Question, Alternatives, Decision, Rationale, Evidence, Assumptions, Consequences, Affected_Artifacts,
  Affected_Tests, Dependencies, Approval_Conditions, Reopening_Criteria, Related_Decisions,
  Source_Conversation_or_Document). Título: "Pneu com variação de pressão: interpolação rotulada de saídas,
  comparação e escolha com banda heurística".
  - Status: `APPROVED (2026-11-03; spec aprovada sem mudanças e ID autorizado: "Autorizo")`.
  - Alternatives: as três abordagens da spec (1 família discreta + interpolação de saídas; 2 PP*/QPZ ajustados no
    OptimumTire = ajuste de ajustes; 3 só A1).
  - Decision, itens numerados: (1) abordagem 1; (2) A2 = interpolação linear das saídas Fx, Fy, Mx, My, Mz no mesmo
    ponto, μ_eff recalculado, sem estimar parâmetro (compatível com o EDR-015), pico como intervalo
    [max(mistura), mistura(max)]; **emenda o item 6 do EDR-067** ("sem interpolar" passa a "sem interpolar
    coeficientes; saídas só pela rota rotulada `tire_pressure.evaluate_interpolated`"); (3) métricas e indicadores
    da spec §6, Cα como principal, sem ranking; (4) regra da banda e regra simétrica da spec §8, palavra por palavra,
    incluindo extremos nunca melhores sozinhos, borda = "não decidível" e o desfecho "todas indistinguíveis";
    (5) critérios de lista fechada (`a_y_lim`, `C_alpha_operacao`; `K`, `TARGET-006` e `TARGET-007` recusados
    enquanto a meta for TBD); (6) guarda QPZ1-2/QPX1 no loader; (7) variantes de KT (a) e (b); FZMAX reescrito para
    o teto comum 1521 N; (8) A3 e B só registrados (spec §12) e degraus futuros.
  - Evidence: "a preencher na Tarefa 9 (tests/test_tire_pressure.py)". Assumptions: os rótulos da spec §5 e "a
    perda TTC→pista é a mesma em todas as pressões".
  - Source: spec, commits b889db9 e 9aa73d3; conversa de 2026-11-02 a 2026-11-03 com dois conselhos.

- [ ] **Passo 2: Ajustar as partes que dependem do registro**
  - Linha 36: "Total: 65 registros. APPROVED: 28 · …" e acrescentar "; em 2026-11-03, EDR-071 entrou como APPROVED"
    ao parêntese. Linha 3: acrescentar "EDR-071 acrescentado em 2026-11-03, pneu com variação de pressão; os IDs
    EDR-068 e EDR-069 estão em uso em outras branches".
  - Índice: `| EDR-071 | Pneu com variação de pressão: interpolação rotulada de saídas, comparação e escolha | APPROVED |`
    logo após a linha do EDR-067.
  - §6: `| EDR-071 | — | python/tire_pressure.py; python/comparacao_pressao.py; python/tire_model_static.py; tools/relatorio_pressao.py; tools/rodar_testes.py. | TC-TIRE-011 a TC-TIRE-023 (tests/test_tire_pressure.py) |`.
  - EDR-067: no item 6 da Decision, acrescentar ao fim "(emendado pelo EDR-071, 2026-11-03: saídas interpoladas só
    pela rota rotulada)"; em Related_Decisions, acrescentar EDR-071.

- [ ] **Passo 3: Conferir a contagem**

Run: `grep -c "^| EDR-" docs/Engineering_Decision_Register.md` antes e depois. Esperado: o número sobe 2 (índice e
§6). Conferir à mão que a soma dos estados da linha 36 dá 65.

- [ ] **Passo 4: Commit**

```bash
git add docs/Engineering_Decision_Register.md
git commit -m "docs: EDR-071, pneu com variação de pressão (emenda o item 6 do EDR-067)"
```

---

### Tarefa 2: guarda QPZ1-2/QPX1, mensagem do `at_pressure` e versão 4.2.0

**Arquivos:**
- Criar: `tests/test_tire_pressure.py` (esqueleto + grupo 13)
- Modificar: `python/tire_model_static.py:1-17` (docstring), `:33` (`__version__`), `:129-137` (`at_pressure`),
  `:186-196` (chaves recusadas), `:315` (`load_revision`)

**Interfaces:**
- Produz: `ts.__version__ == "4.2.0-static"`; `ts.VERSOES_DE_OVERLAY_ACEITAS: tuple[str, ...] = ("4.1.0-static", "4.2.0-static")`
  (as equações não mudaram da 4.1.0 para a 4.2.0, então um overlay da 4.1.0 continua válido; o da 4.0.1 segue
  recusado, como exige o Overlay-7 do teste estático); `ts.PRESSURE_CORRECTION_KEYS = ("PPX1", …, "PPY4", "QPZ1", "QPZ2", "QPX1")`.
- Produz, no teste: `achar_diretorio_ttc()`, `check()`, `recusa(nome, fn, tipo, trecho)` e `encerrar()`, que as
  tarefas seguintes usam.

- [ ] **Passo 1: Criar o esqueleto do teste**

Copie de `tests/test_tire_static.py` as linhas 1-63 (docstring adaptada, `check`, `tem_quatro_tir`,
`achar_diretorio_ttc`, o `SystemExit(3)` com "NÃO EXECUTÁVEL") e o `encerrar()` do fim. Não importe o
`test_tire_static` (importá-lo rodaria os 87 testes). A docstring diz: grupos 1 a 13 da §10 da spec, IDs
TC-TIRE-011 a 023, "passou" = concordância com a definição, não validação física (NOT_VALIDATED). Carregue
`FAMILIA = ts.load_profile_family(TTC, source_axis_system="ISO_TYDEX")` e `P = FAMILIA.pressures_psi`.

- [ ] **Passo 2: Escrever o grupo 13 (TC-TIRE-023), que deve falhar**

```python
# TC-TIRE-023a..c: cópia do .tir de 12 psi com a linha da chave trocada para "= 0.1" (o original nunca é editado)
for chave in ("QPZ1", "QPZ2", "QPX1"):
    copia = tmpd / f"{chave}.tir"   # mesma técnica do Erro-8 do teste estático
    recusa(f"TC-TIRE-023{letra}: load_profile recusa {chave} != 0", lambda: ts.load_profile(copia, source_axis_system="ISO_TYDEX"),
           ts.StaticTireError, chave)
# TC-TIRE-023d: o original segue carregando e QPZ1 = QPZ2 = QPX1 = 0 nos quatro perfis
# TC-TIRE-023e: FAMILIA.at_pressure(13.0) levanta StaticTireError com "Interpolação" E "tire_pressure.evaluate_interpolated" na mensagem
# TC-TIRE-023f: overlay salvo pela 4.2.0 com model_version trocado para "4.1.0-static" é aceito por load_revision
#               e dá o mesmo evaluate_static que o overlay original (bit a bit)
check("TC-TIRE-023g: versão do módulo", ts.__version__ == "4.2.0-static")
```

- [ ] **Passo 3: Rodar e ver falhar**

Run: `export UV_SYSTEM_CERTS=1; uv run python -X utf8 tests/test_tire_pressure.py`
Esperado: FAIL em 023a-c (carrega sem recusar), 023e (mensagem antiga), 023f (versão diferente) e 023g.

- [ ] **Passo 4: Implementar em `python/tire_model_static.py`**
  - `load_profile`: troque a tupla local `pp_keys` por `PRESSURE_CORRECTION_KEYS`; mensagem: "Correções de pressão
    PP*/QPZ1-2/QPX1 não implementadas nesta versão estática: {nonzero}" (o dicionário mantém o nome da chave, que o
    teste procura).
  - `at_pressure`: mantenha as duas primeiras frases e troque a última por "Interpolação entre perfis só pela rota
    rotulada tire_pressure.evaluate_interpolated (saídas interpoladas, INTERPOLADO; EDR-071)." A palavra
    "Interpolação" tem de continuar (`tests/test_tire_static.py:231`).
  - `load_revision`: `payload.get("model_version") not in VERSOES_DE_OVERLAY_ACEITAS`. `save_revision` continua
    gravando `__version__`.
  - Docstring do módulo: a frase "this module deliberately does not interpolate them" passa a dizer que as saídas
    só se interpolam em `tire_pressure.py` (EDR-071) e que os coeficientes nunca se interpolam; cite que a 4.2.0 só
    acrescentou a recusa de QPZ1-2/QPX1, sem mudar equação.
  - Não mude o texto "Pressão suportada somente nos perfis nominais disponíveis; sem interpolação." de
    `evaluate_static`: ele descreve o resultado exato, que continua sem interpolação.

- [ ] **Passo 5: Rodar o novo teste e as contagens que não podem mudar**

Run: `uv run python -X utf8 tests/test_tire_pressure.py` → todos PASS.
Run: `uv run python -X utf8 tests/test_tire_static.py` → `87 PASS, 0 FAIL, de 87 testes`.
Run: `uv run python -X utf8 tests/test_tire_model.py` → `43 PASS, 0 FAIL, de 43 testes`.

- [ ] **Passo 6: Commit**

```bash
git add python/tire_model_static.py tests/test_tire_pressure.py
git commit -m "feat: tire_model_static 4.2.0 recusa QPZ1-2/QPX1 e aponta a rota interpolada (EDR-071)"
```

---

### Tarefa 3: A2, `evaluate_interpolated` (grupos 1 a 3)

**Arquivos:**
- Criar: `python/tire_pressure.py`
- Modificar: `tests/test_tire_pressure.py` (grupos 1, 2 e 3)

**Interfaces:**
- Consome: `ts.StaticTireFamily`, `ts.StaticTireProfile`, `ts.evaluate_static(profile, *, fz_n, alpha_rad, camber_rad, kappa, vx_mps) -> StaticTireResult`,
  `ts.PRESSURE_TOLERANCE_PSI`, `ts.revise_profile(profile, changes, *, reason, revision_id)`.
- Produz:
  - `class TireInterpolationError(ts.StaticTireError)`.
  - `@dataclass(frozen=True) class Faixa: fz_min_n, fz_max_n, alfa_min_rad, alfa_max_rad, camber_min_rad, camber_max_rad, kappa_min, kappa_max` (floats).
  - `faixa_do_perfil(profile) -> Faixa` (FZMIN, FZMAX, ALPMIN, …, KPUMAX do `.tir`); `faixa_comum(perfis: Iterable[StaticTireProfile]) -> Faixa` (interseção).
  - `vizinhos(family, pressure_psi) -> tuple[float, float, float]`: `(p_lo, p_hi, w)`; nó exato (dentro da tolerância) devolve `(p, p, 0.0)`.
  - `@dataclass(frozen=True) class InterpolatedTireResult`: `fx_n, fy_n, fz_n, mx_nm, my_nm, mz_nm, mu_effective, pressure_psi, speed_mps`;
    `rotulo: str = "INTERPOLADO"`; `vizinhos_psi: tuple[float, float]`; `pesos: tuple[float, float]` (1−w, w);
    `sha256: tuple[str, str]`; `revision_id: str`; `loo_trecho: Mapping[float, Mapping[str, float]]` (nó interno → {"fx_n", "fy_n", "mz_n"} → erro LOO no mesmo ponto, previsto − real, N ou N·m);
    `avisos: tuple[str, ...]`; `limitations: tuple[str, ...]`.
  - `evaluate_interpolated(family, pressure_psi, *, fz_n, alpha_rad, camber_rad, kappa, vx_mps, diagnostico: bool = True) -> StaticTireResult | InterpolatedTireResult`.
    No nó exato devolve **o próprio** `evaluate_static` (mesmo tipo, bit a bit). `diagnostico=False` pula
    `loo_trecho` e o aviso de pico (as varreduras das métricas usam assim, por custo).
  - `avaliador_perfil(profile) -> Avaliador` e `avaliador_interpolado(family, pressure_psi) -> Avaliador`, com
    `Avaliador = Callable[[float, float, float, float, float], StaticTireResult | InterpolatedTireResult]`,
    argumentos posicionais `(fz_n, alpha_rad, camber_rad, kappa, vx_mps)`; o interpolado usa `diagnostico=False`.

- [ ] **Passo 1: Escrever os grupos 1 a 3**

```python
PONTOS = [(fz, a, g, k) for fz in (300.0, 1054.0, 1500.0) for a in (-0.15, 0.0, 0.08) for g in (0.0, 0.03) for k in (-0.05, 0.0, 0.1)]
# TC-TIRE-011a: para cada chave real de FAMILIA e cada ponto, evaluate_interpolated(F, p, ...) == evaluate_static(F.at_pressure(p), ...)
#               (dataclass igual: ==, sem tolerância)
# TC-TIRE-011b: idem pedindo 8.0, 10.0, 12.0 e 14.0 inteiros (Foco da revisão, item 1)
# TC-TIRE-012a: em p = 9.0, 11.0, 13.0 e 12.5, cada componente X ∈ {fx_n, fy_n, mx_nm, my_nm, mz_nm} vale
#               (1−w)·X_lo + w·X_hi com |erro| <= 1e-9·max(1, |X_lo|, |X_hi|), e fica entre min e max dos vizinhos
# TC-TIRE-012b: mu_effective do interpolado <= (1−w)·μ_lo + w·μ_hi + 1e-12 (só a cota superior vale)
# TC-TIRE-012c: rotulo == "INTERPOLADO", pesos somam 1, vizinhos_psi e sha256 batem com os perfis vizinhos
# TC-TIRE-012d: em 9.0 loo_trecho tem só a chave do nó de 10 psi; em 11.0, 10 e 12; em 13.0, só 12
# (TC-TIRE-012e, o aviso de pico, entra na Tarefa 4, que cria a busca de pico)
# TC-TIRE-013a: 7.5 e 14.5 psi -> TireInterpolationError com "[8, 14]"
# TC-TIRE-013b: 13.0 psi com Fz = 1530 N (dentro do FZMAX 1546 do 14 psi, fora do 1521 do 12 psi) -> TireInterpolationError com "interseção"
# TC-TIRE-013c: família com o 12 psi revisado (revise_profile, revision_id="R-TESTE", PDY1 × 0,99) e 13.0 psi -> TireInterpolationError com "revision_id"
```

- [ ] **Passo 2: Rodar e ver falhar** (`ModuleNotFoundError: tire_pressure`).

- [ ] **Passo 3: Implementar `python/tire_pressure.py`**
  - Docstring de módulo com os rótulos da spec §5 e a §3 (A2 não estima parâmetro, EDR-015 e EDR-071).
  - `vizinhos`: pressão fora de `[min − tol, max + tol]` → `TireInterpolationError("... fora de [8, 14] psi ...")`
    citando as chaves reais; nó dentro da tolerância → nó exato.
  - Recusas na ordem: faixa de pressão; `revision_id` diferentes entre vizinhos; ponto fora de
    `faixa_comum((lo, hi))` (mensagem com "interseção" e a grandeza que saiu). Depois, `evaluate_static` nos dois.
  - `mu_effective` recalculado com `tire_model.mu_effective(fx, fy, fz)`.
  - `loo_trecho`: para cada vizinho que é nó interno da família (tem um perfil de cada lado), avalia os três perfis
    (anterior, nó, seguinte) no mesmo ponto e grava `previsto − real` de fx, fy e mz, com o `w` do nó entre os
    seus vizinhos. Ponto fora da faixa de algum dos três: a chave fica fora e entra um aviso "LOO do nó X psi não
    calculado: ponto fora da faixa de Y psi".
  - O aviso de pico não entra nesta tarefa (depende da busca de pico da Tarefa 4).
  - `limitations`: as do `evaluate_static` dos vizinhos (sem repetir) mais "Saídas interpoladas linearmente entre
    perfis independentes (EDR-071); não é medição nem ajuste".

- [ ] **Passo 4: Rodar** → grupos 1 a 3 e 13 PASS.

- [ ] **Passo 5: Commit**

```bash
git add python/tire_pressure.py tests/test_tire_pressure.py
git commit -m "feat: tire_pressure.evaluate_interpolated, A2 rotulado (EDR-071)"
```

---

### Tarefa 4: métricas do pneu (grupos 4 a 7)

**Arquivos:**
- Modificar: `python/tire_pressure.py`, `tests/test_tire_pressure.py`

**Interfaces:**
- Consome: `Avaliador`, `Faixa`, `avaliador_perfil`, `avaliador_interpolado` (Tarefa 3); `tire_model._H_RIGIDEZ` (1e-6).
- Produz:
  - `@dataclass(frozen=True) class Pico: mu: float; argumento: float; borda: bool` (`argumento` = α [rad] ou κ;
    `borda=True` = máximo no limite da faixa, rótulo "limitante inferior, sem pico interior").
  - `pico_mu_y(avaliador, faixa, *, fz_n, camber_rad, sinal: int) -> Pico` (sinal +1: α ∈ [0, ALPMAX]; −1: α ∈ [ALPMIN, 0]; κ = 0).
  - `pico_mu_x(avaliador, faixa, *, fz_n, camber_rad, sinal: int) -> Pico` (+1 tração κ ∈ [0, KPUMAX]; −1 frenagem κ ∈ [KPUMIN, 0]; α = 0).
  - `@dataclass(frozen=True) class MetricasPneu`: `fz_n, camber_rad, c_alpha_n_rad, c_alpha_por_fz_1_rad, c_gamma_n_rad, c_kappa_n,`
    `mu_y_pos: Pico, mu_y_neg: Pico, mu_x_tracao: Pico, mu_x_frenagem: Pico, fy_alpha0_n, t0_m, alfa_pico_mz_rad, rotulos: tuple[str, ...]`.
  - `metricas_pneu(avaliador, faixa, *, fz_n, camber_rad, vx_mps: float = 11.176) -> MetricasPneu`.
  - `penalidade_transferencia(avaliador, faixa, *, fz0_n, dfz_n, camber_rad) -> dict[str, float]`, chaves `"alfa_pos"`, `"alfa_neg"`:
    Fy_max(Fz0+ΔFz) + Fy_max(Fz0−ΔFz) − 2·Fy_max(Fz0), com Fy_max = `pico_mu_y(...).mu · Fz` em cada sentido. Fz0 ± ΔFz fora de `[fz_min, fz_max]` → `ValueError`.
  - `teto_comum_fz(family) -> float` (mínimo dos FZMAX; 1521 N com estes dados) e
    `grade_fz(family, fz_operacao: Sequence[float] = (), n: int = 8) -> list[tuple[float, tuple[str, ...]]]`:
    `n` valores igualmente espaçados de max(FZMIN) ao teto, mais as Fz de operação; uma Fz acima do teto entra como o
    teto com o rótulo "Fz de operação X N acima do teto comum: avaliada em 1521 N".
  - `rigidez_vertical(profile) -> tuple[float, str]`: `VERTICAL_STIFFNESS` e o rótulo "valor do arquivo, linear, origem não verificada".
  - `intervalo_pico_mu_y(family, pressure_psi, *, fz_n, camber_rad, sinal: int) -> tuple[float, float]`: pico do μy da
    curva interpolada como intervalo `(max_α mistura, (1−w)·μ_lo + w·μ_hi)` (spec §3); no nó exato, os dois iguais.
    A busca usa `avaliador_interpolado` e a `faixa_comum` dos vizinhos.
  - Em `evaluate_interpolated`, com `diagnostico=True`: compara `pico_mu_y` dos dois vizinhos nos dois sentidos de α
    em (fz, γ); se um tem `borda` e o outro não, aviso "a mistura junta uma curva com pico interior (X psi) e outra
    sem pico interior (Y psi)".

- [ ] **Passo 1: Escrever os grupos 4 a 7**

```python
# TC-TIRE-014a: para cada perfil e Fz ∈ {300, 1054, 1500}, γ ∈ {0, 0.03}:
#               metricas_pneu(avaliador_perfil(pr), ...).c_alpha_n_rad == tire_model.rigidez_deriva(pr.dataset, fz, γ)
#               (|dif| <= 1e-9·|Cα|; mesmo passo 1e-6 e mesma roda FR em ISO_TYDEX)
# TC-TIRE-014b: c_gamma_n_rad em γ = 0 == tire_model.rigidez_camber(pr.dataset, fz) (mesma tolerância)
# TC-TIRE-015a: μy pico (dois sentidos) contra varredura fina independente escrita no teste
#               (4001 pontos em α, sem refino): |μ − μ_ref| <= 1e-4 e |α − α_ref| <= ALPMAX/4000 + 1e-6, perfis 8, 10 e 12 psi
# TC-TIRE-015b: idem μx tração e frenagem (4001 pontos em κ)
# TC-TIRE-015c: penalidade_transferencia confere com 3 chamadas a pico_mu_y (mesma definição) e recusa Fz0 + ΔFz > teto
# TC-TIRE-015d: intervalo_pico_mu_y em 9, 11 e 13 psi (Fz 1054, γ 0, dois sentidos): inferior <= superior + 1e-12;
#               nos nós exatos, inferior == superior == pico_mu_y do perfil
# TC-TIRE-012e: evaluate_interpolated em 13.0 psi, Fz 1054, γ 0: avisos contém "pico interior" (12 psi tem, 14 psi não);
#               em 11.0 psi, nenhum aviso de pico
# TC-TIRE-016a: a 14 psi, Fz ∈ {300, 700, 1054, 1500}, γ = 0: mu_y_pos.borda e mu_y_neg.borda são True e o rótulo
#               "limitante inferior, sem pico interior" está em rotulos (achado do conselho, reproduzido em 2026-11-03)
# TC-TIRE-016b: a 8, 10 e 12 psi, mesmas Fz: nenhuma borda em μy; μx sem borda nos quatro perfis
# TC-TIRE-017a: t0 = −(∂Mz/∂α)/(∂Fy/∂α) em α = 0 contra diferença finita independente no teste (passo 1e-4, avaliando
#               evaluate_static direto): |dif| <= 1e-6 m; rótulo "pendente do item 3 do EDR-067"
# TC-TIRE-017b: grade_fz com fz_operacao = [1600.0] devolve 1521 com o rótulo de "acima do teto" (Foco da revisão, item 2)
```

- [ ] **Passo 2: Rodar e ver falhar** (`AttributeError` nas funções novas).

- [ ] **Passo 3: Implementar**
  - Derivadas (Cα, Cγ, Cκ, ∂Mz/∂α, ∂Fy/∂α) por diferença central com `h = tire_model._H_RIGIDEZ` sobre o avaliador.
    Sinais: Cα = −∂Fy/∂α; Cγ = −∂Fy/∂γ (como `rigidez_camber`); Cκ = +∂Fx/∂κ em κ = 0 (Fx > 0 para κ > 0 no
    `.tir`, TC-TIRE-004b; a spec escreve "−∂Fx/∂κ", mas com essa convenção daria negativo: implemente o positivo e
    registre a troca de sinal na docstring).
  - Busca de pico: grade grossa de 121 pontos no intervalo e, se o máximo for interior, refino por
    `scipy.optimize.minimize_scalar(method="bounded")` entre os vizinhos do máximo, `xatol=1e-7`. `borda=True`
    quando o máximo da grade grossa está no extremo do intervalo (|α| = ALPMAX ou |κ| = KPU*); aí não refina.
  - `alfa_pico_mz_rad`: argmax de |Mz| em α ∈ [0, ALPMAX], mesma busca.
  - Rótulos de `MetricasPneu`: "Cγ: μy(γ) sem informação de pressão (PDY3 = 2 nos quatro perfis)"; "Cκ e μx:
    ajuste longitudinal mal condicionado (PKX2/PKX3 instáveis)"; borda, quando houver; "t0 e α do pico de Mz:
    anexo, pendentes do item 3 do EDR-067; fora do A1-escolha"; "menor carga ensaiada a confirmar: FZMIN do .tir é
    o limite declarado, não a carga medida" (o valor da menor carga ensaiada não está nos dados; não invente).

- [ ] **Passo 4: Rodar** → grupos 1 a 7 e 13 PASS.

- [ ] **Passo 5: Commit**

```bash
git add python/tire_pressure.py tests/test_tire_pressure.py
git commit -m "feat: métricas do pneu por pressão (Cα, picos com borda, t0) em tire_pressure"
```

---

### Tarefa 5: indicadores de incerteza (grupo 8 e reprodução dos achados)

**Arquivos:**
- Modificar: `python/tire_pressure.py`, `tests/test_tire_pressure.py`

**Interfaces:**
- Produz:
  - `@dataclass(frozen=True) class ErroLOO: psi: float; previsto: float; real: float; erro: float; erro_rel: float | None`
    (`erro = previsto − real`; `erro_rel = erro/|real|`, None se real = 0).
  - `erro_loo(valores: Mapping[float, float | None]) -> dict[float, ErroLOO]`: só nós internos; o previsto usa o `w`
    das chaves reais; nó com vizinho None fica fora. 8 e 14 psi nunca aparecem (declarado na docstring).
  - `@dataclass(frozen=True) class Assimetria: dif_mu_pico: float; dif_rel: float; fy_alpha0_n: float; rotulo: str`
    (`dif_mu_pico = |μy_pos − μy_neg|`; rótulo "em parte física: conicidade e ply-steer").
  - `assimetria_alfa(metricas: MetricasPneu) -> Assimetria`.
  - `monotonicidade(valores: Mapping[float, float]) -> str` ∈ {"crescente", "decrescente", "constante", "não monotônica"}.

- [ ] **Passo 1: Escrever o grupo 8 e a reprodução**

```python
NOS = (7.999992, 10.000062, 11.999987, 14.000058)   # as chaves reais
lin = {p: 3.0 + 2.0 * p for p in NOS}
quad = {p: 0.5 * p * p for p in NOS}
# TC-TIRE-018a: erro_loo(lin) tem chaves só nos dois nós internos e |erro| <= 1e-12
# TC-TIRE-018b: erro_loo(quad)[p_k].erro == 0.5·(p_k − p_lo)·(p_hi − p_k) (erro analítico da interpolação linear de a·p²), |dif| <= 1e-12
# TC-TIRE-018c: erro_loo com um vizinho None não tem o nó afetado
# TC-TIRE-018d: monotonicidade(lin) == "crescente"; de valores (3, 1, 2, 0) == "não monotônica"
# TC-TIRE-018e: reprodução (Fz = 1054 N, γ = 0, metricas_pneu nos quatro perfis; números do MODEL, não validação):
#   erro_rel do μy (α > 0) a 10 psi em [−0,050, −0,044]; do Cα a 10 psi em [−0,068, −0,061];
#   do μx tração a 12 psi em [−0,099, −0,093]; do μx frenagem a 12 psi em [−0,109, −0,102];
#   e os quatro |erro_rel| ficam em [0,04, 0,11] (o "4 a 11 %" do conselho)
# TC-TIRE-018f: PKY2 cresce com a pressão (monotonicidade == "crescente") e o Cα em 1054 N NÃO é monotônico
#               (registro do achado: Cα 46,6k / 53,2k / 53,0k / 49,6k N/rad em 8/10/12/14 psi)
# TC-TIRE-018g: assimetria_alfa em 12 psi, 1054 N: dif_mu_pico >= 0 e fy_alpha0_n == metricas.fy_alpha0_n
```

As janelas de 018e vêm de uma varredura de 4001 pontos feita nesta sessão (μy −4,71 %, Cα −6,47 %, μx −9,59 % e
−10,56 %). Se a implementação cair fora, investigue a busca de pico antes de mexer na janela.

- [ ] **Passo 2: Rodar e ver falhar.**
- [ ] **Passo 3: Implementar as quatro funções.**
- [ ] **Passo 4: Rodar** → grupos 1 a 8 e 13 PASS.
- [ ] **Passo 5: Commit**

```bash
git add python/tire_pressure.py tests/test_tire_pressure.py
git commit -m "feat: indicadores LOO, assimetria ±α e monotonicidade; reprodução dos achados do conselho"
```

---

### Tarefa 6: A1-carro, `comparar_carro` (grupos 9 a 11)

**Arquivos:**
- Criar: `python/comparacao_pressao.py`
- Modificar: `tests/test_tire_pressure.py`

**Interfaces:**
- Consome: `equilibrio.CasoEquilibrio`, `analise_par_dois_sentidos(caso, **kw) -> {"esquerda", "direita", "pior"}`,
  `ResultadoPar` (`ay_lim`, `veredito`, `resolucao_ms2`, `linhas` com `cap_f`/`cap_r: Capacidade`, `motivo`),
  `FATORES_LAMBDA`, `com_fatores`, `varredura_pneu`, `veredito_robusto`; `equilibrio_linear.parcelas_k(caso, ay_ms2) -> ParcelasK`;
  `suspension_model.roll_stiffness_axle(k_wheel, track, k_arb, k_tire)`; `teto_comum_fz` (Tarefa 4).
- Produz:
  - `perfil_ajustado(ds_caso: TireDataset, profile: StaticTireProfile, teto_fz_n: float) -> tuple[TireDataset, tuple[str, ...]]`:
    `TireDataset` novo com `p` = `dict` mutável do perfil; cada nome de `FATORES_LAMBDA` com valor ≠ 1 em `ds_caso`
    é copiado (valor absoluto); nome ausente no perfil → `ValueError` com o nome; `FZMAX` = `teto_fz_n` quando
    maior, rótulo "FZMAX X → 1521 N (teto comum da família)"; rótulo com os λ copiados.
  - `diferencas_fora_de_lambda(ds_caso, profile, teto_fz_n) -> dict[str, tuple[float, float]]`: coeficientes do caso
    ≠ do perfil, fora de `FATORES_LAMBDA` e de FZMAX.
  - `kphi_com_kt(kphi_n_m_rad: float, track_m: float, kt_antigo_n_m: float, kt_novo_n_m: float) -> float`: inverte a série
    `K_φ = serie(k_susp, KT·t²/2)` para achar `k_susp` e refaz com o KT novo.
  - `@dataclass(frozen=True) class ResultadoCarro`: `pressao_psi, variante_kt: str` ("a" ou "b"), `ay_lim_ms2: float | None`,
    `sentido_pior: str`, `eixo_satura: str | None` ("F" para PUSH, "R" para LOOSE, "ambos" para NEUTRO, None em N/A),
    `veredito: str`, `k_rad_ms2: float | None`, `k_motivo: str | None`, `resolucao_ms2: float | None`, `borda_alfa: bool`,
    `robustez: tuple | None`, `rotulos: tuple[str, ...]`, `par: dict` (a saída de `analise_par_dois_sentidos`), `caso: CasoEquilibrio`.
  - `comparar_carro(caso, family, *, kt_caso_n_m: Mapping[str, float] | None = None, fatores_lambda: Mapping[str, Sequence[float]] | None = None, **kw_analise) -> list[ResultadoCarro]`:
    uma entrada por pressão (ordem crescente) na variante "a" e, com `kt_caso_n_m = {"F": KTF, "R": KTR}`, outra na "b".

- [ ] **Passo 1: Escrever os grupos 9 a 11**

O caso de teste usa o `veiculo_base()` de `tests/test_equilibrio.py:45-65` (copie a função; "números plausíveis,
NÃO é setup real") e `ds = tm.load_dataset(<12 psi>, source_axis_system="ISO_TYDEX")` escalado por
`eq.com_fatores(ds, {"LMUY": 0.9, "LKY": 1.1})`. Grade curta para o tempo: `kw = {"ay_max_g": 2.0, "passo_g": 0.1, "n_alfa": 13}`.

```python
# TC-TIRE-019a: para cada ResultadoCarro da variante "a", r.par == analise_par_dois_sentidos(replace(caso, ds=ds_do_perfil), **kw)
#               (ds_do_perfil de perfil_ajustado; mesma chamada, mesmo resultado)
# TC-TIRE-019b: os quatro ds dão Fy diferentes no mesmo ponto (Fz 1054, α −0,1, γ 0): 4 valores distintos
# TC-TIRE-019c: comparar_carro(caso, "<caminho>.tir") e comparar_carro(caso, Path(...)) -> TypeError com "10_TIRE"
# TC-TIRE-019d: borda_alfa da pressão de 14 psi é igual ao recálculo no teste (alguma linha do sentido pior com a_y <= ay_lim,
#               ou todas se ay_lim for None, tem cap_f ou cap_r com motivo "pico na borda da grade de α"); o valor vai no detalhe
# TC-TIRE-020a: âncora: o ResultadoCarro de 12 psi, variante "a", tem ay_lim igual ao de analise_par_dois_sentidos(caso, **kw)
#               dentro de resolucao_ms2 (com estes dados é igual bit a bit: o .tir provisório da planilha é o de 12 psi)
# TC-TIRE-021a: o ds de 8 psi tem LMUY = 0,9 e LKY = 1,1; perfil sem "LTR" (perfil montado no teste sem a chave) e caso com
#               LTR = 0,9 -> ValueError com "LTR"
# TC-TIRE-021b: FZMAX do ds de 8, 10 e 14 psi == 1521 e o rótulo "teto comum" está em rotulos; o de 12 psi não ganha rótulo de FZMAX
# TC-TIRE-021c: kphi_com_kt(roll_stiffness_axle(kw, t, karb, kt1), t, kt1, kt2) == roll_stiffness_axle(kw, t, karb, kt2) (rel 1e-12)
# TC-TIRE-021d: com kt_caso_n_m, a variante "b" de 8 psi tem roll_stiffness_front/rear diferentes da "a" e iguais a
#               kphi_com_kt(..., VERTICAL_STIFFNESS de 8 psi)
# TC-TIRE-021e: caso com PDY1 do ds trocado (≠ .tir, não é λ): rotulos de todos os ResultadoCarro citam "PDY1" (Foco da revisão, item 3)
```

- [ ] **Passo 2: Rodar e ver falhar.**

- [ ] **Passo 3: Implementar `python/comparacao_pressao.py`**
  - Recusa: `family` que não for `ts.StaticTireFamily` → `TypeError("passe a família de perfis (load_profile_family), não um .tir: caso_da_planilha_v41 grava a 10_TIRE (coeficientes de 12 psi) por cima do .tir e devolveria 12 psi em silêncio")`.
  - Por pressão: `ds_p, rot = perfil_ajustado(...)`; `caso_p = dataclasses.replace(caso, ds=ds_p)`; variante "b":
    `cfg` com `dataclasses.replace(caso.cfg, roll_stiffness_front=kphi_com_kt(cfg.roll_stiffness_front, cfg.track_front, KTF, VS), roll_stiffness_rear=...)`,
    com `VS = profile.parameters["VERTICAL_STIFFNESS"]`.
  - `ay_lim_ms2` e `veredito` do sentido pior (`par[par["pior"]]`; em "empate", a "esquerda").
  - `k_rad_ms2 = parcelas_k(caso_p, 0.0).k_total` (o K da faixa linear, Gillespie; em a_y = 0). Rótulo: "K com o
    roll steer do caso"; se o caso tiver `roll_steer` {0, 0}, "roll steer 0 = sem dado".
  - `robustez`: só com `fatores_lambda`: `veredito_robusto([r.veredito for _, r in varredura_pneu(caso_p, fatores_lambda, **kw)])`,
    rótulo "hipótese: a perda TTC→pista é a mesma em todas as pressões".
  - Rótulos fixos: os da Restrições globais; "resolucao_ms2 é tolerância numérica, não critério de diferença"; "ds
    único nas 4 rodas; sem raio carregado, altura de rodagem e cinemática decorrente"; "Fy em α = 0 como no modelo
    (invertido pelo espelhamento nas rodas esquerdas)"; as diferenças de `diferencas_fora_de_lambda`, se houver.

- [ ] **Passo 4: Rodar** → grupos 1 a 11 e 13 PASS. Anote o tempo do script; se passar de 5 min, reduza `kw` no teste
  (nunca o número de pressões).

- [ ] **Passo 5: Commit**

```bash
git add python/comparacao_pressao.py tests/test_tire_pressure.py
git commit -m "feat: comparar_carro roda o caso com o ds de cada pressão (λ, teto 1521 N, variantes de KT)"
```

---

### Tarefa 7: A1-escolha, bandas e `escolher_pressao` (grupo 12)

**Arquivos:**
- Modificar: `python/comparacao_pressao.py`, `tests/test_tire_pressure.py`

**Interfaces:**
- Consome: `ResultadoCarro`, `erro_loo`, `ErroLOO`, `metricas_pneu`, `avaliador_perfil`, `faixa_do_perfil`, `teto_comum_fz`.
- Produz:
  - `CRITERIOS = {"a_y_lim": "máximo", "C_alpha_operacao": "máximo"}`; `CRITERIOS_TBD = ("K", "TARGET-006", "TARGET-007")`.
  - `PISO_NUMERICO_REL = 1e-6` (piso da banda do pneu, relativo ao valor; escolha heurística declarada, dominada pelo LOO).
  - `@dataclass(frozen=True) class Banda: valor: float | None; medida: bool; componentes: Mapping[str, float]; rotulo: str`.
  - `banda_carro(resultados: Sequence[ResultadoCarro], grandeza: str = "ay_lim_ms2") -> dict[float, Banda]`: nós internos
    `max(|LOO|, resolucao_ms2)`; 8 e 14 psi: o maior |LOO| interno, `medida=False`, rótulo "limite inferior (banda não
    medida)"; sem LOO disponível: `valor=None`, rótulo "banda indisponível".
  - `banda_pneu(valores: Mapping[float, float], assimetria: Mapping[float, float] | None) -> dict[float, Banda]`:
    `max(|LOO|, assimetria, PISO_NUMERICO_REL·|X|)`; assimetria None = componente ausente, declarado ("não se aplica
    ao Cα": a derivada em α = 0 não tem lado); extremos como no carro.
  - `@dataclass(frozen=True) class Veredito: melhor: float | None; indistinguiveis: tuple[float, ...]; nao_decidiveis: Mapping[float, str]; desfecho: str; valores: Mapping[float, float | None]; bandas: Mapping[float, Banda]`.
  - `decidir(valores: Mapping[float, float | None], bandas: Mapping[float, Banda], nao_decidiveis: Mapping[float, str]) -> Veredito` (sentido "máximo").
  - `@dataclass(frozen=True) class Escolha: criterio: str; sentido: str; vereditos: Mapping[str, Veredito]; veredito_muda_com_kt: bool | None; rotulos: tuple[str, ...]`.
  - `escolher_pressao(criterio: str, *, resultados_carro: Sequence[ResultadoCarro] | None = None, family: StaticTireFamily | None = None, fz_estatica_eixo_n: Mapping[str, float] | None = None, camber_eixo_rad: Mapping[str, float] | None = None) -> Escolha`.
    `a_y_lim`: um `Veredito` por variante presente (chaves "KT (a)", "KT (b)"), `veredito_muda_com_kt` quando as
    duas existem. `C_alpha_operacao`: um por eixo ("eixo F", "eixo R"), Cα de `metricas_pneu` na Fz estática do eixo
    (limitada ao teto, com rótulo) e no camber estático médio do eixo; `veredito_muda_com_kt = None`.

Regra de `decidir`, que fixa o que a spec §8 deixa implícito:
1. Não decidível: valor None (motivo do N/A), `borda_alfa` (só para `a_y_lim`; Cα nunca) ou banda None. Continua
   listado com o motivo; não é excluído.
2. Entre os decidíveis, `x*` = maior valor. `indistinguiveis` = {q : |x* − x_q| ≤ max(banda_x*, banda_q)} (inclui `x*`).
3. `melhor = x*` só se `indistinguiveis == {x*}`, a banda de `x*` for medida (nunca 8 ou 14 psi sozinhos) **e** não
   houver pressão não decidível. Motivo da última condição: com pico na borda o valor é limitante inferior, e a
   pressão não decidível pode superar `x*`. Com ela presente o desfecho é "veredito suspenso: X psi não decidível".
4. `desfecho` ∈ {"melhor: X psi", "indistinguíveis: …", "todas indistinguíveis" (todas as decidíveis no conjunto,
   resultado válido e esperado com estes dados), "extremo sem banda medida: X psi não é declarada a melhor sozinha",
   "veredito suspenso: …", "nenhuma pressão decidível"}.

- [ ] **Passo 1: Escrever o grupo 12 com valores sintéticos** (`Banda` e valores à mão; `ResultadoCarro` construído no teste)

```python
B = lambda v, medida=True: Banda(v, medida, {"loo": v}, "")
P8, P10, P12, P14 = NOS
# TC-TIRE-022a veredito: valores {8: 10, 10: 20, 12: 12, 14: 11}, bandas 1 -> melhor == P10, desfecho "melhor"
# TC-TIRE-022b empate parcial: {10: 20, 12: 19.5}, bandas 1 -> melhor None, indistinguiveis == (P10, P12)
# TC-TIRE-022c empate total: os quatro dentro de 1 -> "todas indistinguíveis"
# TC-TIRE-022d simetria: trocar as bandas de 10 e 12 (0.2 e 1 vs 1 e 0.2) não muda o conjunto (usa o max das duas)
# TC-TIRE-022e borda: 14 psi com borda_alfa e valor 30 -> 14 em nao_decidiveis, melhor None, "veredito suspenso"
# TC-TIRE-022f extremo: 8 psi com o maior valor, isolado, banda medida=False -> melhor None, "extremo sem banda medida"
# TC-TIRE-022g recusa: escolher_pressao("K") e ("TARGET-007") -> ValueError com "meta TBD"; ("sei_la") -> ValueError com a lista de CRITERIOS
# TC-TIRE-022h N/A: ay_lim None em 12 psi -> 12 em nao_decidiveis com o motivo; nada quebra (Foco da revisão, item 4)
# TC-TIRE-022i banda indisponível: banda_carro com 8 psi N/A -> banda de 10 psi None e 10 em nao_decidiveis (Foco da revisão, item 5)
# TC-TIRE-022j KT: resultados das variantes a e b com vereditos diferentes -> veredito_muda_com_kt is True
# TC-TIRE-022k pneu real: escolher_pressao("C_alpha_operacao", family=FAMILIA, fz_estatica_eixo_n={"F": 700, "R": 800},
#               camber_eixo_rad={"F": 0, "R": 0}) devolve "eixo F" e "eixo R", sem exceção, com bandas de 8 e 14 medida=False
```

- [ ] **Passo 2: Rodar e ver falhar.**
- [ ] **Passo 3: Implementar** as funções acima em `comparacao_pressao.py`.
- [ ] **Passo 4: Rodar** → `N PASS, 0 FAIL, de N testes` (todos os grupos). Anote N para a Tarefa 9.
- [ ] **Passo 5: Commit**

```bash
git add python/comparacao_pressao.py tests/test_tire_pressure.py
git commit -m "feat: escolher_pressao com banda heurística e regra simétrica (EDR-071)"
```

---

### Tarefa 8: relatório `tools/relatorio_pressao.py`

**Arquivos:**
- Criar: `tools/relatorio_pressao.py`

**Interfaces:**
- Consome: tudo das Tarefas 3 a 7; `caso_planilha.caso_da_planilha_v41(xlsx, tir, passo1=...)`,
  `caso_planilha.endereco_da_entrada(wb, "KTF" | "KTR")`, `tests/recalculo_planilha.py` (`rc.escolher()`,
  `rc.recalcular(caminho, motor, timeout=900)`), como em `tools/relatorio_inc4.py:147-200`.
- Produz: `build/relatorio-pressao.md` e `build/pressao-*.png` (nada versionado); código 0 ok, 2 recusado, 3 NÃO EXECUTÁVEL.

- [ ] **Passo 1: Escrever o script** no molde do `relatorio_inc4.py` (argparse com `--planilha`, padrão
  `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx`; `--saida`, padrão `build/relatorio-pressao.md`).
  - Cópia da planilha em pasta temporária, recalculada pelo motor (EDR-044); a original nunca é aberta para escrita.
  - O `.tir` do caso é o de 12 psi da família real (mesmo conteúdo do `data/Hoosier_R25B_13x7_TTC_provisional.tir`,
    que não existe em worktrees); SHA de cada `.tir` no cabeçalho.
  - Caso: `passo1=True`; se der `ValueError` (roll steer sem número), `passo1=False` e o rótulo "K sem roll steer
    (roll steer sem dado na planilha)".
  - KTF/KTR lidos da cópia recalculada por `endereco_da_entrada`.
  - Seções: (1) rótulos da spec §5 e proveniência (commit, ramo, motor, SHA); (2) A1-pneu: tabela por pressão em
    `grade_fz` (Fz de operação = as 4 rodas em a_y = 0 e no a_y limite do 12 psi), γ ∈ {0, camber estático}, com
    Cα, Cα/Fz, Cγ, Cκ, μy ±, μx tração/frenagem, borda, |LOO|, assimetria, monotonicidade, rigidez vertical e o
    anexo t0; (3) A1-carro: `comparar_carro` nas variantes (a) e (b) com a robustez de
    `data/varredura_pneu_exploratoria.json` (`["fatores"]`), sem ranking; (4) A1-escolha: `escolher_pressao` com
    `a_y_lim` e `C_alpha_operacao`; (5) A2: uma curva Fy(α) interpolada a 9, 11 e 13 psi com o intervalo do pico
    e os avisos; (6) A3 e B (texto da spec §12); (7) limitações.
  - PNG: `import matplotlib` dentro de `try`; sem ele, o `.md` diz "PNG não gerado: rode com
    `uv run --with matplotlib python -X utf8 tools/relatorio_pressao.py`" e o código continua 0.
  - Recusa sobrescrever sem `--sobrescrever`.

- [ ] **Passo 2: Rodar**

Run: `uv run --with matplotlib python -X utf8 tools/relatorio_pressao.py --sobrescrever`
Esperado: código 0 (ou 3 sem motor de recálculo, relatado como NÃO EXECUTÁVEL), `build/relatorio-pressao.md` com as
sete seções e os PNG. Confira à mão que 14 psi aparece com borda e que nenhuma tabela ordena as pressões.

- [ ] **Passo 3: Commit**

```bash
git add tools/relatorio_pressao.py
git commit -m "feat: relatorio_pressao (A1, A1-escolha e A2 em build/, nada versionado)"
```

---

### Tarefa 9: registro na suíte, EDR-071 VERIFIED e verificação final

**Arquivos:**
- Modificar: `tools/rodar_testes.py:38` (nova linha em `TESTES`), `CLAUDE.md` (linha "Esperado na V4.2"),
  `docs/Engineering_Decision_Register.md` (EDR-071: Status, Evidence, Affected_Tests; contagem da linha 36)

- [ ] **Passo 1: Registrar o teste**, logo após o "pneu estático":
  `("pneu com pressão", "tests/test_tire_pressure.py", N, "EDR-071 (precisa dos .tir do TTC Round 6, fora do Git)")`,
  com o N da Tarefa 7. No `CLAUDE.md`, acrescente "pneu com pressão N (`tests/test_tire_pressure.py`, EDR-071; mesmos
  `.tir`)" depois do "pneu estático 87".

- [ ] **Passo 2: Rodar a suíte**

Run: `uv run python -X utf8 tools/rodar_testes.py`
Esperado: "pneu com pressão" N/N PASS, "pneu estático" 87/87, "pneu" 43/43 e os demais itens como no log anterior
(`build/verificacao-ultima.md`). Item que falhar e não for deste plano: relate, não conserte.

- [ ] **Passo 3: Commit do registro**

```bash
git add tools/rodar_testes.py CLAUDE.md
git commit -m "test: registra tests/test_tire_pressure.py na suíte (EDR-071)"
```

- [ ] **Passo 4: EDR-071 para VERIFIED**: Status "VERIFIED (data; implementado e verificado; não implica validação
  física)"; Evidence com N/N, a suíte, os números reproduzidos do TC-TIRE-018e e a borda do TC-TIRE-016a;
  Affected_Tests "TC-TIRE-011 a TC-TIRE-023"; linha 36: APPROVED 27, VERIFIED 17.

```bash
git add docs/Engineering_Decision_Register.md
git commit -m "docs: EDR-071 VERIFIED com a evidência de tests/test_tire_pressure.py"
```

---

## Cobertura da spec

| Spec | Tarefa |
|---|---|
| §3 equações e recusa do modelo de pressão do PAC2002; guarda QPZ/QPX1 | 2 |
| §3 e §9 A2 | 3 (cota do pico: 3 e 4) |
| §5 arquitetura e rótulos | 2 a 8 |
| §6 métricas e indicadores | 4 e 5 |
| §7 A1-carro | 6 |
| §8 A1-escolha | 7 |
| §10 grupos 1 a 13 | 3 (1-3), 4 (4-7), 5 (8), 6 (9-11), 7 (12), 2 (13) |
| §11 IDs | 1 e 9 |
| §12 A3 e B | 1 (EDR) e 8 (relatório) |
