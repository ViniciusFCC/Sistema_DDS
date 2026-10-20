# V4.0, incremento 1 (viabilidade e robustez ao pneu): plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Responder, com número e para o caso demonstrativo da planilha, duas perguntas: (1) a análise de par do Milliken §7.1 cabe na planilha (tempo de recálculo e exatidão no Excel e no LibreOffice)? (2) o veredito push/loose resiste à incerteza do pneu?

**Architecture:** O núcleo da análise de par vai para `python/equilibrio.py` (funções puras, SI). Ele é a implementação MODEL, testada, e será o oráculo da aba de equilíbrio do incremento 4. A varredura de robustez usa esse núcleo trocando os fatores de escala λ do PAC2002 numa cópia do dataset. `python/caso_planilha.py` monta o caso demonstrativo a partir de uma cópia recalculada da planilha e calcula a pior origem das entradas. Um experimento descartável gera a mesma análise como fórmulas numa pasta temporária, recalcula pelos dois motores (EDR-044), mede o tempo e compara com o Python. Uma ferramenta junta tudo num relatório de evidência.

**Tech Stack:** Python 3.13 (`uv`), openpyxl, `tests/recalculo_planilha.py` (Excel via COM ou LibreOffice), testes como scripts com `check()`.

**Spec:** `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` (aprovada pelo usuário em 2026-10-20). Seções usadas: 7.1, 7.2 (C_N), 7.3 (textos, D15, D16), 7.4 (hipóteses), 7.6 (robustez), 9, 10 (incremento 1).

## Escopo deste plano

- **Dentro:** a análise de par no limite com as hipóteses 1, 2 (só o toe estático), 4 (camber estático + ganho linear, entradas com padrão 0), 5 e 6 (as que `suspension_model.lateral_dfz` já tem) e aero fixo por Setup (EDR-013). Também a varredura de robustez, o caso da planilha, o protótipo de viabilidade e o relatório.
- **Fora (incremento 2, plano próprio):** K linear e decomposição do Gillespie, C_γ, ∂γ/∂φ do `kinematics_model`, cos δ e Ackermann, CG lateral, aero com V = √(a_y·R), força de tração, diferencial, oráculos do Gillespie p. 231-233 e do modelo bicicleta, testes do pneu em ISO_TYDEX e a extensão da mutação. O relatório lista essas hipóteses como "não incluídas", com o efeito esperado tirado da tabela 7.4 da spec.
- **Por que o núcleo já sai "de verdade" (e não como script descartável):** a spec chama de exploratória a *varredura*, não o cálculo. Se o veredito de robustez saísse de um código sem teste, um avaliador o derrubaria com uma pergunta. E o incremento 2 teria de reescrever o mesmo cálculo. Descartável fica só o protótipo da planilha.
- **Incrementos 2 a 7:** cada um ganha o próprio plano depois do relatório deste. O "vai ou não vai" decide o desenho do 4.

## Risco conhecido antes de começar (medido em 2026-10-20 ao escrever o plano)

O `.tir` provisório (R25B, TTC) tem pico de Fy ≈ 2,52·Fz em FNOMIN: na roda FR com Fz = 1054 N, o máximo numérico é 2655,35 N, igual a |Dy| + SVy, com α ≈ −7,8°. A faixa válida é FZMIN = 100 N, FZMAX = 1521 N e |α| ≤ 15°. No veículo de teste de `tests/test_suspension_model.py`, a roda RL fica abaixo de 100 N perto de 1,55 g, enquanto um eixo com esse μ só saturaria perto de 2,3 g. Por isso, com o pneu sem escala, o resultado mais provável da análise de par é `N/A` (faixa do pneu), também no caso da planilha.

O que o plano faz com isso:
- (a) Os testes de veredito usam um dataset de teste com `LMUY = 0.5`, rotulado no código como "escala só de teste, não é pneu". Cada um desses testes confere antes a pré-condição: a saturação existe dentro da faixa.
- (b) O relatório mostra, para o caso da planilha, a primeira a_y em que uma roda sai da faixa e, nessa última linha válida, a fração da capacidade usada por eixo. Nada é extrapolado.
- (c) Como tratar a roda interna abaixo de FZMIN é decisão do usuário, e ela vai junto com o relatório. Uma opção é Fy = 0 só quando Fz ≤ 0 (descolamento, que é física e não extrapolação) e N/A entre 0 e FZMIN. A outra é manter o N/A. Esta decisão não é tomada neste incremento.

## Autorizações que o executor pede ao usuário antes de começar (CLAUDE.md: IDs só com autorização)

1. O namespace de testes **TC-EQ-001 a TC-EQ-020** para `tests/test_equilibrio.py`.
2. O **EDR-055**, que registra a amplitude da varredura do pneu (Task 7). Os valores são decisão do usuário.
3. O registro de `tests/test_equilibrio.py` em `tools/rodar_testes.py`, com 20 testes esperados (muda a lista de CA-05).

Sem o item 1, as Tasks 1 a 5 não começam. Sem o item 2, a Task 8 roda com a varredura vazia e o relatório diz "robustez não avaliada".

## Global Constraints

- SI no núcleo. a_y em m/s² dentro das funções; a entrada da grade é em g, convertida por `suspension_model.G` (9.81). Ângulos em rad.
- Eixos ISO 8855. Curva à esquerda: a_y > 0, as rodas da direita (FR, RR) são as externas, α de referência ≤ 0 e Fy > 0 (para a esquerda). Camber + = topo para fora; toe + = toe-out (EDR-002).
- `.tir` carregado com `source_axis_system="ISO_TYDEX"` (EDR-039 revisto).
- Nunca extrapolar o pneu: Fz fora de [FZMIN, FZMAX] ou α fora de [ALPMIN, ALPMAX] dá capacidade `None` com motivo, nunca exceção nem número.
- Nenhum valor inventado. Toe, camber estático e ganho de camber têm padrão 0, e o relatório escreve "sem dado (EDR-036)". As amplitudes da varredura vêm só do EDR-055.
- Textos de exibição exatos (spec 7.3): `"▲ PUSH: sai de frente (final understeer)"`, `"▼ LOOSE: sai de traseira (final oversteer)"`, `"● NEUTRO no limite"`, `"N/A: <motivo>"`, `"? NÃO CONCLUSIVO: o sinal depende do pneu"`. Prefixo `"DEMONSTRATIVO · "` sempre que a pior origem ≠ `"● Dado do TX"` (D16).
- Testes são scripts com `check()` e terminam com `N PASS, 0 FAIL, de T testes` (padrão de `tests/test_suspension_model.py`). Rodar com `uv run python -X utf8 tests/<script>.py`; no Git Bash, antes, `export UV_SYSTEM_CERTS=1`.
- A planilha viva e a de referência nunca são salvas por ferramenta. Só cópias em pasta temporária são abertas por motor de recálculo (EDR-044). O protótipo não é planilha da equipe e não vai para o Git (`build/` está no `.gitignore`).
- Commits separados por propósito (CLAUDE.md), em Conventional Commits com descrição em português, na branch `feat/v4-0-inc1-viabilidade`. Ela sai da ponta de `docs/v4-0-arquitetura-e-spec`, que tem a spec. Sem push nem PR sem pedido do usuário.
- Nenhuma fórmula da planilha V3.0 muda. Nenhum `.py` existente muda, exceto `tools/rodar_testes.py` (Task 9).

## Review Focus

1. **A roda interna sai da faixa do pneu antes de o eixo saturar.** Com FZMIN = 100 N no `.tir`, isso é provável em a_y alto. Esperado: veredito `N/A` com o motivo "Fz … fora da faixa do pneu em a_y = x g", e nunca um veredito tirado de pontos extrapolados. Exceção: se um eixo já saturou e o outro continua válido além dessa a_y, o veredito sai (Task 3, TC-EQ-013).
2. **O pico da curva do eixo cai na borda da grade de α** (pneu pouco rígido ou toe grande). Esperado: capacidade marcada com o motivo "pico na borda da grade de α", e a linha não serve para saturação (Task 2, TC-EQ-006).
3. **Nenhum eixo satura até o a_y máximo da grade** (muita downforce, grade curta). Esperado: `N/A: não satura até <a_y_max> g` (Task 3, TC-EQ-014).
4. **Planilha sem valores calculados** (gerada pelo openpyxl e nunca recalculada). Esperado: `ValueError` dizendo que a cópia precisa ser recalculada, e nunca zeros nem `None` passados ao modelo (Task 5, TC-EQ-019).
5. **Fator da varredura com nome errado** (`"LMUX "`, `"PDY2"`). Esperado: `ValueError`, porque só fatores λ que existem no `.tir` são aceitos. Um erro de digitação não pode virar "robusto" em silêncio (Task 4, TC-EQ-018).

---

### Task 1: Caso, cargas e camber por roda

**Files:**
- Create: `python/equilibrio.py`
- Test: `tests/test_equilibrio.py` (criado aqui; as tasks seguintes acrescentam checks antes do bloco de resumo)

**Interfaces:**
- Consumes: `suspension_model.VehicleConfig`, `combined_fz_corner(cfg, ax, ay, downforce_total, aero_balance_front, warn=False)`, `lateral_dfz(cfg, ay)["roll_angle_rad"]`, `G`; `tire_model.TireDataset`.
- Produces:
  - `CANTOS = ("FL", "FR", "RL", "RR")`
  - `@dataclass(frozen=True) class CasoEquilibrio`, com os campos `cfg: VehicleConfig`, `ds: TireDataset`, `downforce_N: float = 0.0`, `aero_balance_front: float = 0.5`, `toe_rad: dict[str, float]`, `camber_estatico_rad: dict[str, float]` e `ganho_camber: dict[str, float]` (dγ/dφ em rad/rad, por roda, convenção do projeto). Os três dicionários têm `default_factory` com 0.0 nos quatro cantos, e `__post_init__` exige as quatro chaves e valores finitos.
  - `cargas(caso, ay_ms2: float) -> dict[str, float]`, que delega a `combined_fz_corner(cfg, 0.0, ay, downforce_N, aero_balance_front, warn=False)`.
  - `camber(caso, ay_ms2: float) -> dict[str, float]`: γ = camber_estatico + ganho_camber·φ, com φ = `lateral_dfz(cfg, ay)["roll_angle_rad"]`.

- [ ] **Step 1: Escrever os testes que falham.** Copie de `tests/test_suspension_model.py` o cabeçalho `check()` e o resumo final. Crie `veiculo_base(**over)` com os mesmos números de `baseline_config` desse arquivo (veículo de teste, rotulado como "não é setup real") e `ds = tm.load_dataset(<data/Hoosier_R25B_13x7_TTC_provisional.tir>, source_axis_system="ISO_TYDEX")`. Checks:
  - `TC-EQ-001`: em a_y = 0, `cargas(caso_com_DF_400_bal_0.45, 0.0)` é igual, em cada canto, a `static_fz_corner(cfg)[c] + aero_fz_corner(400, 0.45)[c]` (tolerância 1e-9 N).
  - `TC-EQ-002`: em a_y = 1,2·G, a soma dos quatro Fz é m·G + 400 (1e-9), `FR > FL` e `RR > RL`.
  - `TC-EQ-003`: com `camber_estatico_rad` = {FL: −0,01, FR: −0,01, RL: −0,02, RR: −0,02} e `ganho_camber` = {FL: 0,5, FR: −0,5, RL: 0,3, RR: −0,3}, `camber(caso, 1,0·G)[c] == estatico[c] + ganho[c]·φ` (1e-15), com φ de `lateral_dfz`. Também: `CasoEquilibrio(..., toe_rad={"FL": 0.0})` levanta `ValueError` (faltam cantos).
- [ ] **Step 2: Rodar e ver falhar.** `uv run python -X utf8 tests/test_equilibrio.py`. Esperado: `ModuleNotFoundError: equilibrio`.
- [ ] **Step 3: Implementar** `CANTOS`, `CasoEquilibrio`, `cargas` e `camber` em `python/equilibrio.py`, com a docstring do módulo citando Milliken §7.1 (p. 283-286) e a spec. Os valores que esses números testam são entradas de teste, não do carro.
- [ ] **Step 4: Rodar e ver passar.** Esperado: `3 PASS, 0 FAIL, de 3 testes`.
- [ ] **Step 5: Commit.** `git add python/equilibrio.py tests/test_equilibrio.py` e `git commit -m "feat: caso de equilíbrio com cargas e camber por roda (V4.0, inc. 1)"`

### Task 2: Curva do eixo e capacidade

**Files:**
- Modify: `python/equilibrio.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Consumes: Task 1; `tire_model.wheel_forces(ds, corner, fz, alpha, gamma, kappa)` (ISO, κ = 0), `tire_model.in_range`, `pure_fy0(p, fz, alpha, gamma)[1]` (dicionário com `"Dy"` e `"SVy"`).
- Produces:
  - `deriva_toe(caso) -> dict[str, float]`: Δα por roda vindo do toe estático, com Δα_FL = −toe_FL, Δα_FR = +toe_FR, Δα_RL = −toe_RL e Δα_RR = +toe_RR. Toe-out na roda esquerda aponta a roda para a esquerda; o carro em linha reta fica com α < 0 e Fy > 0 nessa roda.
  - `grade_alfa(caso, n_alfa: int) -> list[float]`: n_alfa pontos igualmente espaçados de 0 a −A, com A = min(|ALPMIN|, ALPMAX) − max|Δα|. Assim nenhuma roda sai da faixa de α.
  - `fy_eixo(caso, eixo: str, ay_ms2: float, alfa_ref: float) -> float`: soma de Fy (ISO, N) das duas rodas do eixo (`"F"` ou `"R"`), com α_roda = alfa_ref + Δα_roda, γ de `camber()` e Fz de `cargas()`.
  - `@dataclass(frozen=True) class Capacidade`, com os campos `fy_max_N: float | None`, `alfa_pico_rad: float | None` e `motivo: str | None`.
  - `capacidade_eixo(caso, eixo: str, ay_ms2: float, n_alfa: int) -> Capacidade`. Se alguma roda do eixo tiver Fz fora de [FZMIN, FZMAX], devolve `Capacidade(None, None, "Fz_<canto> = <x> N fora da faixa do pneu [FZMIN, FZMAX]")`. Senão, devolve o máximo de `fy_eixo` sobre `grade_alfa`. Se o máximo cair no último ponto da grade, `motivo = "pico na borda da grade de α"`, e o valor fica registrado mas não serve para saturação.

- [ ] **Step 1: Escrever os testes que falham.**
  - `TC-EQ-004`: eixo dianteiro, a_y = 0, toe e camber 0: para cada α de `grade_alfa(caso, 25)`, `fy_eixo == wheel_forces(ds,"FL",fz,α,0,0)[1] + wheel_forces(ds,"FR",fz,α,0,0)[1]` (1e-9).
  - `TC-EQ-005`: com uma roda só, compare o máximo numérico com a forma fechada. Use uma grade fina de α (4001 pontos de 0 a ALPMIN) e a roda FR, com Fz = FNOMIN e γ = 0. O máximo de `wheel_forces(...)[1]` deve ser igual a `abs(Dy) + SVy`, tirados de `pure_fy0(ds.p, FNOMIN, 0.0, 0.0)[1]`, com erro relativo < 1e-4. No `.tir` atual, PDY1 e PKY1 são negativos, e o valor medido ao escrever o plano foi 2655,348 N contra 2655,348 N. O check também exige que o índice do pico não seja o último da grade. A forma fechada vale porque PCY1 = 1,4199 ≥ 1 (spec 7.1).
  - `TC-EQ-006`: um dataset com `PKY1` multiplicado por 0,05 (cópia de `ds.p`; o `ds` original fica intacto) faz `capacidade_eixo(...).motivo == "pico na borda da grade de α"`.
  - `TC-EQ-007`: no veículo de teste, a roda FL tem Fz ≈ 32 N < FZMIN em a_y = 2,0·G. O check confere essa pré-condição por `cargas()` e então exige que `capacidade_eixo(caso,"F",2.0*G,25)` voltar com `fy_max_N is None` e um motivo que contém `"fora da faixa do pneu"`, sem exceção.
  - `TC-EQ-008`: toe-out simétrico de 1° na frente, a_y = 0, α_ref = 0: a contribuição da FL é > 0, a da FR é < 0 e `fy_eixo` é ≈ 0 (1e-9). Isso confere o sinal da `deriva_toe` contra o EDR-002.
- [ ] **Step 2: Rodar e ver falhar.** Esperado: `AttributeError` ou `ImportError` para `capacidade_eixo`.
- [ ] **Step 3: Implementar** `deriva_toe`, `grade_alfa`, `fy_eixo`, `Capacidade` e `capacidade_eixo`. Os termos que dependem só de Fz não precisam de cache no Python: a otimização "uma vez por linha" é da planilha (Task 6).
- [ ] **Step 4: Rodar e ver passar.** Esperado: `8 PASS, 0 FAIL, de 8 testes`.
- [ ] **Step 5: Commit.** `git commit -m "feat: curva e capacidade lateral do eixo pelo PAC2002 (V4.0, inc. 1)"`

### Task 3: Análise de par: saturação, veredito e C_N

**Files:**
- Modify: `python/equilibrio.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Consumes: Tasks 1 e 2.
- Produces:
  - Constantes `PUSH = "PUSH"`, `LOOSE = "LOOSE"`, `NEUTRO = "NEUTRO"`, `NA = "N/A"` e `NAO_CONCLUSIVO = "NÃO CONCLUSIVO"`.
  - `forca_exigida(caso, ay_ms2) -> tuple[float, float]`, que devolve (F_yf, F_yr) = (m·a_y·b/L, m·a_y·a/L) (spec 7.1, item 5).
  - `@dataclass(frozen=True) class LinhaPar`, com os campos `ay_ms2`, `fz: dict[str, float]`, `cap_f: Capacidade`, `cap_r: Capacidade`, `req_f: float` e `req_r: float`.
  - `@dataclass(frozen=True) class ResultadoPar`, com os campos `linhas: tuple[LinhaPar, ...]`, `passo_ms2: float`, `ay_sat_f: float | None`, `ay_sat_r: float | None`, `ay_lim: float | None`, `veredito: str` (um dos quatro primeiros acima), `motivo: str | None` e `c_n: float | None`.
  - `analise_par(caso, ay_max_g: float = 2.0, passo_g: float = 0.05, n_alfa: int = 25) -> ResultadoPar`.

Regras (as que os testes não determinam sozinhos):
- Grade: a_y_k = k·passo, para k = 0, …, ⌊ay_max/passo⌋. Os parâmetros são validados (`ay_max_g > 0`, `passo_g > 0`, `n_alfa ≥ 3`); se não forem válidos, sai `ValueError`.
- Saturação de um eixo: a primeira troca de sinal da folga m_k = cap_k − req_k entre linhas consecutivas *válidas* (capacidade com `motivo is None`), interpolada linearmente: a_y_sat = a_y_k + (a_y_{k+1} − a_y_k)·m_k/(m_k − m_{k+1}). Se aparecer uma linha inválida antes da troca, a busca para nela: a saturação do eixo fica `None` e o motivo dele é o da linha inválida. Se a grade acabar sem troca, o motivo é `"não satura até <ay_max_g> g"`.
- Veredito: sejam S_f e S_r as saturações e V_f e V_r o último a_y válido de cada eixo. Se as duas saturações existem e |S_f − S_r| < passo, o veredito é NEUTRO. Se S_f < S_r, ou se S_f existe, S_r é `None` e V_r > S_f, o veredito é PUSH. O caso simétrico dá LOOSE. Em qualquer outro caso, é N/A, com o motivo do eixo que impediu a decisão. a_y_lim = min das saturações conhecidas.
- C_N (spec 7.2; Milliken §8.4, p. 311-312): em a_y_lim, folga do eixo não saturado, interpolada entre linhas. Em PUSH, C_N = +folga_r·b/(W·L); em LOOSE, C_N = −folga_f·a/(W·L), com W = m·G. Em NEUTRO ou N/A, `c_n = None`.

- [ ] **Step 1: Escrever os testes que falham.** Os TC-EQ-010 a 012 usam `ds_teste` (cópia de `ds` com `p["LMUY"] = 0.5`, comentário "escala só de teste, não é pneu"; ver "Risco conhecido") e conferem, como pré-condição, que as duas saturações existem.
  - `TC-EQ-009`: com a ≠ b (por exemplo a = 0,85, b = 0,70), `forca_exigida(caso, 9.81) == (m·9.81·b/L, m·9.81·a/L)` (1e-9).
  - `TC-EQ-010`: carro simétrico (a = b, bitolas iguais, K_φF = K_φR, z_F = z_R, massas e alturas não suspensas iguais, DF = 0) dá `veredito == NEUTRO`, `abs(ay_sat_f − ay_sat_r) < passo_ms2` e `c_n is None`.
  - `TC-EQ-011`: o mesmo carro com λ_f = 0,7 (K_φF = 0,7·soma) dá PUSH, e com λ_f = 0,3 dá LOOSE (Gillespie p. 214: mais rigidez de rolagem à frente empurra para push). Se falhar, isso é achado de física ou do pneu, não de código. Investigue com `superpowers:systematic-debugging` e nunca ajuste o teste para passar (CLAUDE.md, ordem de investigação).
  - `TC-EQ-012`: no PUSH do TC-EQ-011, `c_n > 0`; no LOOSE, `c_n < 0`. E `c_n` bate (1e-12) com a recomposição feita no teste a partir de `linhas` (folga interpolada em `ay_lim`, vezes b ou a, dividida por W·L).
  - `TC-EQ-013`: no veículo de teste com o `ds` sem escala (a roda sai da faixa antes de saturar, ver "Risco conhecido"), ou o veredito é `N/A` e `motivo` contém `"fora da faixa do pneu"`, ou o veredito é PUSH/LOOSE e o eixo não saturado é válido além de `ay_lim` (o teste confere pelas `linhas`). Nos dois ramos, nenhuma capacidade inválida entra no cálculo.
  - `TC-EQ-014`: `analise_par(caso_base, ay_max_g=0.3)` dá `veredito == NA` e `motivo` contém `"não satura até 0.3 g"`.
  - `TC-EQ-015`: `ay_max_g=0`, `passo_g=-0.05` e `n_alfa=2` levantam `ValueError` cada um.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** `forca_exigida`, `LinhaPar`, `ResultadoPar` e `analise_par` com as regras acima.
- [ ] **Step 4: Rodar e ver passar.** Esperado: `15 PASS, 0 FAIL, de 15 testes`.
- [ ] **Step 5: Commit.** `git commit -m "feat: análise de par no limite com push/loose e C_N (V4.0, inc. 1)"`

### Task 4: Varredura de robustez ao pneu e texto do veredito

**Files:**
- Modify: `python/equilibrio.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Consumes: Task 3.
- Produces:
  - `com_fatores(ds, fatores: dict[str, float]) -> TireDataset`: cópia com `p[nome] *= valor`. Ela aceita só nomes que começam com `"L"` e existem em `ds.p`; com qualquer outro nome, sai `ValueError`. O `ds` de entrada nunca é alterado.
  - `varredura_pneu(caso, fatores: dict[str, list[float]], **kw) -> list[tuple[dict[str, float], ResultadoPar]]`: produto cartesiano das listas. Cada combinação roda `analise_par(replace(caso, ds=com_fatores(...)), **kw)`. Dicionário vazio dá lista vazia.
  - `veredito_robusto(vereditos: list[str]) -> tuple[str, str]`. Lista vazia dá `(NA, "robustez ao pneu não avaliada")`. Todos iguais a PUSH, ou todos iguais a LOOSE, dá `(esse, "mesmo sinal na varredura exploratória do pneu")`. Todos N/A dá `(NA, "N/A em toda a varredura")`. Qualquer outra mistura (sinais diferentes, ou com NEUTRO, ou com N/A) dá `(NAO_CONCLUSIVO, "o sinal depende do pneu")`. Spec 7.6, item 3: NEUTRO conta como inversão.
  - `texto_veredito(res: ResultadoPar, pior_origem: str, robusto: tuple[str, str] | None = None) -> str`: monta o texto exato de 7.3 (Global Constraints). Se `robusto` vier e for `NAO_CONCLUSIVO`, o texto é `"? NÃO CONCLUSIVO: o sinal depende do pneu"` no lugar do nominal. O prefixo `"DEMONSTRATIVO · "` entra quando `pior_origem != "● Dado do TX"`.

- [ ] **Step 1: Escrever os testes que falham.**
  - `TC-EQ-016`: as cinco combinações de `veredito_robusto` acima (`[PUSH,PUSH]`, `[PUSH,LOOSE]`, `[PUSH,NEUTRO]`, `[NA,NA]`, `[]`) dão os pares esperados, e `[PUSH,NA]` dá `NAO_CONCLUSIVO`. Este é o caso "construído para inverter" da spec §9, item 12.
  - `TC-EQ-017`: `varredura_pneu(caso, {"LMUY": [1.0]})` devolve um item cujo `ResultadoPar` é igual a `analise_par(caso)`. E, depois de `varredura_pneu(caso, {"LFZO": [0.9, 1.1], "LKY": [0.9, 1.1]})` (4 itens, valores só de teste), `ds.p` continua igual a uma cópia feita antes.
  - `TC-EQ-018`: `com_fatores(ds, {"PDY2": 1.1})`, `{"LMUX ": 1.0}` e `{"LXYZ": 1.0}` levantam `ValueError`. E `texto_veredito` dá exatamente `"DEMONSTRATIVO · ▲ PUSH: sai de frente (final understeer)"` para um PUSH com pior origem `"◐ Dado do T09"`, `"▼ LOOSE: sai de traseira (final oversteer)"` para um LOOSE com `"● Dado do TX"`, e `"DEMONSTRATIVO · ? NÃO CONCLUSIVO: o sinal depende do pneu"` com `robusto=(NAO_CONCLUSIVO, …)`.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** `com_fatores`, `varredura_pneu`, `veredito_robusto` e `texto_veredito` (use `dataclasses.replace` para o caso e `copy.deepcopy` do `p`).
- [ ] **Step 4: Rodar e ver passar.** Esperado: `18 PASS, 0 FAIL, de 18 testes`.
- [ ] **Step 5: Commit.** `git commit -m "feat: robustez do veredito ao pneu e texto com prefixo demonstrativo (V4.0, inc. 1)"`

### Task 5: Caso demonstrativo lido da planilha e pior origem

**Files:**
- Create: `python/caso_planilha.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Consumes: `equilibrio.CasoEquilibrio`; `suspension_model` (`wheel_rate`, `roll_stiffness_axle`, `VehicleConfig`); `raizes.Grafo`, `raizes.origem_da_raiz`, `raizes.PIOR_PRIMEIRO`; o mapa de células de `tests/test_workbook_suspensao.py` (`ENTRADAS`, linhas 32-42).
- Produces:
  - `ENTRADAS_CASO: dict[str, tuple[str, str]]`: as chaves m, h, L, tF, tR, a, b, muF, muR, huF, huR, KsF, KsR, MRF, MRR, KarbF, KarbR, zF, zR, KTF, KTR, DF e bal, com as mesmas células do `ENTRADAS` de `tests/test_workbook_suspensao.py`. É uma cópia consciente; o incremento 3 troca as duas pelo nome definido.
  - `caso_da_planilha(xlsx_recalculado: Path, tir: Path) -> CasoEquilibrio`. Abre com `data_only=True`, monta o `VehicleConfig` como em `python_ref()` daquele teste (linhas 64-74) e carrega o `.tir` em ISO_TYDEX. Toe, camber e ganho ficam 0. Se qualquer entrada vier `None` ou não numérica, levanta `ValueError("a cópia precisa ser recalculada (Excel ou LibreOffice) antes da leitura: <aba>!<célula> sem valor")`.
  - `pior_origem_do_caso(xlsx_formulas: Path) -> str`: pior rótulo, na ordem de `raizes.PIOR_PRIMEIRO`, entre as origens das raízes de todas as células de `ENTRADAS_CASO` (pelo `Grafo`) e `"◐ Provisório (.tir TTC)"` (o pneu). Uma raiz sem rótulo conta como `"? A confirmar"`.

- [ ] **Step 1: Escrever os testes que falham.**
  - `TC-EQ-019`: uma pasta criada pelo openpyxl em diretório temporário, com as abas e as células de `ENTRADAS_CASO` contendo fórmulas simples (`"=1+1"`) e sem valor calculado, faz `caso_da_planilha` levantar `ValueError` com `"precisa ser recalculada"` na mensagem.
  - `TC-EQ-020`: `pior_origem_do_caso(excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx)` (só leitura, sem `data_only`) devolve um rótulo de `raizes.PIOR_PRIMEIRO` diferente de `"● Dado do TX"`, porque mola, MR, barra e RC são do T09 (CLAUDE.md). E o arquivo não muda (hash SHA-256 igual antes e depois).
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** `python/caso_planilha.py`.
- [ ] **Step 4: Rodar e ver passar.** Esperado: `20 PASS, 0 FAIL, de 20 testes`.
- [ ] **Step 5: Commit.** `git commit -m "feat: caso de equilíbrio lido da planilha com pior origem (V4.0, inc. 1)"`

### Task 6: Protótipo descartável da análise de par na planilha (viabilidade)

**Files:**
- Create: `tests/exp_viabilidade_par.py`. É um experimento: fica fora da suíte e não entra em `rodar_testes.py`. O recálculo de cópias pelo motor está coberto pelo EDR-044.
- Saída: `build/exp_viabilidade_par.json` e o `.xlsx` gerado em pasta temporária (nada no Git).

**Interfaces:**
- Consumes: `equilibrio.analise_par`, `equilibrio.grade_alfa`, `equilibrio.deriva_toe`, `equilibrio.camber`; `tests/recalculo_planilha.escolher()` e `recalcular(caminho, motor, timeout)`; o caso de teste `veiculo_base` e, se houver motor, o caso de `caso_planilha`.
- Produces: o JSON `{"motor": str, "linhas": int, "n_alfa": int, "celulas_formula": int, "t_recalculo_s": float, "t_base_s": float, "dif_rel_max_capacidade": float, "dif_ay_sat_f": float, "dif_ay_sat_r": float, "pico_na_borda": int, "erros_formula": int}`, um por motor (`DDS_RECALC=excel` e `DDS_RECALC=libreoffice`).

Desenho da aba (spec 7.1, item 4):
- Coeficientes do `.tir` como constantes num bloco.
- Uma linha por a_y da grade de `analise_par`, com Fz e γ das quatro rodas escritos como constantes vindas do Python. As fórmulas de Fz já estão provadas iguais na CA-09, e o custo que se quer medir é o da grade de α.
- Por linha e por roda, uma vez: dfz, γy, Ky, SHy, μy, Dy, By, SVy e três variantes de Ey (sgn −1, 0, +1). Cada termo fica numa célula com guarda `IF(OR(Fz<FZMIN,Fz>FZMAX),"N/A",…)`.
- Por célula de α: `Dy·SIN(Cy·ATAN(By·x − Ey·(By·x − ATAN(By·x)))) + SVy`, com x = α_eq + SHy e Ey = `CHOOSE(SIGN(x)+2, Ey_neg, Ey_0, Ey_pos)`. O espelhamento da roda esquerda segue `wheel_forces` (α do arquivo = −α na roda L, e Fy_L = −Fy). A soma por eixo fica em cada coluna.
- Capacidade = `MAX` da linha; folga e saturação por fórmula (interpolação da Task 3, numa coluna auxiliar com `MIN`).

- [ ] **Step 1: Escrever o experimento.** Ele gera a pasta, mede `t_base_s` (recálculo de uma pasta só com o bloco de coeficientes) e `t_recalculo_s` (pasta completa) com `time.perf_counter()` em volta de `recalcular`. Depois compara capacidades e saturações com `analise_par` e conta os picos no último índice de α. Sem motor, ele imprime `NÃO EXECUTÁVEL` e sai com o código 3 (padrão do `test_workbook`).
- [ ] **Step 2: Rodar com os dois motores.** `DDS_RECALC=excel uv run python -X utf8 tests/exp_viabilidade_par.py` e depois o mesmo com `DDS_RECALC=libreoffice`. Esperado: `erros_formula == 0` e `dif_rel_max_capacidade < 1e-9` (mesmo critério da CA-09). Uma diferença maior é divergência a investigar na ordem do CLAUDE.md, nunca a ajustar.
- [ ] **Step 3: Commit.** `git add tests/exp_viabilidade_par.py` e `git commit -m "test: experimento de viabilidade da análise de par na planilha (V4.0, inc. 1)"`

### Task 7: EDR-055, amplitude da varredura do pneu (decisão do usuário)

**Files:**
- Modify: `docs/Engineering_Decision_Register.md` (índice, §3 se ficar pendente, registro novo, rastreabilidade)
- Create: `data/varredura_pneu_exploratoria.json`

**Interfaces:**
- Produces: o JSON `{"edr": "EDR-055", "origem": "○ Arbitrário / demonstrativo", "fatores": {"<Lxxx>": [<multiplicadores>], ...}, "nota": "valores exploratórios; não são faixa do pneu (EDR-022)"}`, lido pela Task 8.

- [ ] **Step 1: Apresentar ao usuário.** Para cada fator candidato (LFZO, LMUY, LKY, LKYG), diga o que ele escala, citando o help do Adams (PAC2002) conferido na imagem do PDF em `references/`. Diga também por que ele pode mudar o sinal: o equilíbrio depende da *diferença* entre os eixos. Um λ que escala os dois eixos por igual (LMUY) tende a não mudar o sinal; LFZO muda a sensibilidade à carga. Peça os multiplicadores. Não proponha números como se fossem dados: se o usuário pedir sugestão, apresente-a como "arbitrária, para explorar", com o motivo.
- [ ] **Step 2: Registrar o EDR-055** (Record_Status conforme a resposta), no formato dos EDR-053/054, com o índice e as contagens atualizados. Grave o JSON.
- [ ] **Step 3: Commit separado.** `git commit -m "docs: EDR-055 (amplitude exploratória da varredura do pneu)"`

### Task 8: Relatório de viabilidade e robustez (evidência)

**Files:**
- Create: `tools/relatorio_inc1.py`
- Create, como saída registrada (só numa árvore sem mudanças pendentes): `docs/v4-0/inc1-viabilidade-e-robustez.md`

**Interfaces:**
- Consumes: Tasks 3 a 7; `build/exp_viabilidade_par.json`; uma cópia **temporária** da planilha viva recalculada por `recalcular` (a viva nunca é aberta pelo motor nem salva).
- Produces: um relatório em Markdown com:
  1. Origem: commit, hash do arquivo da viva, motor e data.
  2. Caso: entradas e pior origem; as hipóteses incluídas e as não incluídas, com o efeito tirado da tabela 7.4 da spec.
  3. Resultado nominal: `texto_veredito`, saturações, a_y_lim, C_N e a primeira a_y em que alguma roda sai da faixa do pneu. Se o veredito for N/A por faixa, mostra também, na última linha válida, a fração da capacidade usada por eixo (req/cap). Essa fração indica qual eixo está mais perto do limite, sem extrapolar o pneu, e não é veredito. Mostra também a decisão pendente (c) de "Risco conhecido".
  4. Varredura: tabela com combinação, veredito e a_y_lim, mais o veredito robusto.
  5. Viabilidade: os dois motores, tempos, número de fórmulas, diferenças e picos na borda.
  6. "Vai ou não vai": só os números. Não há limiar sem decisão registrada (spec §9, item 10). A recomendação vai separada, marcada como recomendação, e a decisão fica para o usuário.

- [ ] **Step 1: Escrever `tools/relatorio_inc1.py`** com `--saida <caminho>`. Ele recusa sobrescrever um arquivo existente e recusa rodar com a árvore suja (o mesmo cuidado de `rodar_testes.py --saida`).
- [ ] **Step 2: Rodar.** `uv run python -X utf8 tools/relatorio_inc1.py --saida docs/v4-0/inc1-viabilidade-e-robustez.md`. Esperado: o arquivo criado, todo veredito com o prefixo `DEMONSTRATIVO · ` (os dados são do T09 ou provisórios) e nenhuma célula da viva alterada (hash igual antes e depois).
- [ ] **Step 3: Commits separados.** Primeiro `git add tools/relatorio_inc1.py` com `git commit -m "feat: relatório do incremento 1 da V4.0"`. Depois `git add docs/v4-0/inc1-viabilidade-e-robustez.md` com `git commit -m "docs: evidência do incremento 1 (viabilidade e robustez ao pneu)"`.

### Task 9: Suíte, registro e fechamento do incremento

**Files:**
- Modify: `tools/rodar_testes.py:34-39` (acrescentar `("equilíbrio", "tests/test_equilibrio.py", 20, "plano do incremento 1 da V4.0")` em `TESTES`)
- Modify: `CLAUDE.md` (linha "Esperado na V3.0": acrescentar "equilíbrio 20 (V4.0, incremento 1)")

- [ ] **Step 1: Registrar e rodar a suíte inteira em segundo plano.** `uv run python -X utf8 tools/rodar_testes.py`. Esperado: todos os itens anteriores PASS, iguais aos de 2026-10-20 (pneu 43, oráculos 5, suspensão 54, cinemática 74, hardpoints 35, mutação 25/25, comparador 15/15, V2.4 347 e V3.0 387 com 0 diferença, viva × referência, CA-09 19/19 e 15/15), mais `equilíbrio 20 PASS`.
- [ ] **Step 2: Commit.** `git commit -m "test: registra o teste de equilíbrio na suíte (V4.0, inc. 1)"`
- [ ] **Step 3: Revisão do branch** com o `pr-review-toolkit` (preferência do usuário). Mostre os achados por gravidade; push e PR só com pedido do usuário.
- [ ] **Step 4: Levar ao usuário a decisão do relatório:** "vai" (aba de equilíbrio por fórmulas no incremento 4) ou "não vai" (tabela gerada pelo Python, spec §10, linha 1). Só depois dela se escreve o plano do incremento 2.
