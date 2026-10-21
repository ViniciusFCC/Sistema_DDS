# V4.0, incremento 2 (equilíbrio linear e hipóteses do limite no Python): plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar no Python o passo 1 da spec (gradiente de subesterço K com as parcelas do Gillespie cap. 6, verificado pelos exemplos resolvidos do livro) e as hipóteses do limite que a planilha do incremento 4 vai implementar (Ackermann, cos δ, CG lateral, aero com a velocidade, tração com elipse de atrito e diferencial aberto). Inclui também os testes do pneu em ISO_TYDEX, a mutação estendida ao equilíbrio e as dívidas menores do incremento 1.

**Architecture:**
- `python/tire_model.py` ganha a rigidez de deriva e a de camber do PAC2002.
- `python/kinematics_model.py` ganha o gradiente de camber no solo por rolagem.
- `python/suspension_model.py` ganha a carga estática com CG lateral e a downforce em função da velocidade.
- O módulo novo `python/equilibrio_linear.py` tem as funções puras do Gillespie, as parcelas de K de um `CasoEquilibrio` e a tabela linear.
- `python/equilibrio.py` ganha os campos e as hipóteses do limite, todos com padrão que mantém o comportamento atual.
- Cada hipótese nova tem a entrada desligada por padrão (valor `None` ou 0, "sem dado"), para que os testes TC-EQ-001..020 e o relatório do EDR-056 não mudem.

**Tech Stack:** Python 3.13 (`uv`), scripts de teste com `check()`, `tools/rodar_testes.py`.

**Spec:** `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md`. Seções usadas: §6 (passo 1), §7.1, 7.4 (hipóteses 2, 3, 7, 8, 9, 10), §8.1, §9 (itens 1, 2, 8, 11) e §10 (incremento 2). Também os EDR-039, 055 e 056 e o relatório `docs/v4-0/inc1-viabilidade-e-robustez-edr056.md`.

## Fontes conferidas na imagem do PDF ao escrever o plano (2026-10-21)
- **Gillespie, *Fundamentals of Vehicle Dynamics*, pp. 231-234 (exemplos resolvidos do cap. 6), folhas 151-152 do PDF:**
  - **Exemplo 1:** W_f = 1901 lb, W_r = 1552 lb, L = 100,6 in.
    - Rigidez por pneu: 232 lb/deg na frente (950 lb por pneu) e 195 lb/deg atrás (776 lb por pneu).
    - K = 950/232 − 776/195 = 0,11 deg/g.
    - c = 4,62 ft; c' = 8,38 ft · 232/(232+195) = 4,55 ft.
    - V_char = √(57,3·L·g/K) = 393 ft/s = 268 mph, mas **calculada com L = 110,6 in**. É errata do livro: com o L do problema (100,6 in) dá cerca de 375 ft/s.
  - **Exemplo 2:**
    - dφ/da_y = W·h1/(K_φf + K_φr − W·h1) = 2750·10/(1500 + 1606 − 480) = 10,5 deg/g;
    - K_camber = (0,1·1,0 − 0,1·0)·10,5 = 1,05 deg/g;
    - roll steer traseiro com ε_r = +0,122 rad/rad (SAE: positivo esterça para a direita numa rolagem para a direita): o livro escreve "+0,122 radians (10,5 deg/g) = 1,28 deg/g" e diz, na p. 235, que o carro fica **sobresterçante**. Pela eq. 6-57, K_roll steer = (ε_f − ε_r)·dφ/da_y = −1,28 deg/g. A função existente `kinematics_model.roll_steer_understeer_deg_per_g` (SUS-415, EDR-052) já usa essa forma.
- **Gillespie, pp. 215-219 (folhas 142-144 do PDF):** C_α = a·Fz − b·Fz² (eq. 6-36 a 6-38); K_llt = W_f/C_αf · 2b·ΔFz_f²/C_αf − W_r/C_αr · 2b·ΔFz_r²/C_αr (eq. 6-49, p. 217; a eq. 6-47 é só a aproximação 1/(C − 2b·ΔFz²); citação corrigida em 2026-10-21, EDR-057); γ_g = γ_b + φ (eq. 6-50); K_camber (eq. 6-56). O executor confere essas equações na imagem antes de implementar (CLAUDE.md).
- **Milliken §2.7 (elipse de atrito):** o executor localiza e confere na imagem do PDF (OCR em `references/md/milliken-rcvd/livro.md`, a partir da linha 2416) antes da Task 7.

## Autorizações a pedir ao usuário antes de começar (CLAUDE.md: IDs só com autorização)
1. IDs de teste **TC-EQ-021 a TC-EQ-048**: 28 checks em `tests/test_equilibrio_linear.py` (novo), `tests/test_equilibrio.py` e `tests/test_kinematics_model.py`, distribuídos na tabela de contagem abaixo.
2. **EDR-057**: registra as escolhas de método deste incremento (Task 10):
   - δ de referência = L/R e cos δ de referência, pela spec 7.1;
   - definição de sinal de C_α e C_γ;
   - elipse de atrito com Fx_max pelo pico de Fx do PAC2002 e diferencial aberto com Fx igual nas duas rodas;
   - hipóteses do Python ainda fora (spec 7.4: 11 a 16).
3. Registro de `tests/test_equilibrio_linear.py` e de `tests/mutation_equilibrio.py` na suíte (`tools/rodar_testes.py`).

## Global Constraints
- SI no núcleo: K em rad/(m/s²); a conversão para °/g fica numa função de apresentação. a_y em m/s²; a entrada de grades fica em g, convertida por `suspension_model.G` (9.81).
- ISO 8855. Curva à esquerda: a_y > 0. Camber + = topo para fora; toe + = toe-out (EDR-002). Roll steer: a convenção do SUS-415 (`kinematics_model.roll_steer_coefficient`).
- Sinais definidos aqui, para uso em todo o plano:
  - **C_α = −∂Fy_ISO/∂α**, na roda FR, com α = 0 e κ = 0, em N/rad (> 0);
  - **C_γ = −∂Fy_ISO/∂γ_projeto**, na roda FR, com α = 0 e γ = 0, em N/rad. Camber com topo para fora na roda direita empurra para a direita, então C_γ > 0 é o caso normal;
  - **gradiente de camber do eixo:** ∂γ_eixo/∂φ = (∂γ_R/∂φ − ∂γ_L/∂φ)/2, com γ no solo e na convenção do projeto, φ > 0 rolando para a direita. Para braços paralelos iguais, dá 1,0 (Gillespie p. 234).
- `.tir` em `ISO_TYDEX` (EDR-039). Pneu fora da faixa: as regras do EDR-056 (limitar com aviso; Fz ≤ 0 = N/A). Nada extrapolado em silêncio.
- Nenhum valor inventado:
  - entradas novas (R, % Ackermann, CG lateral, CzA, ρ, CdA, Crr, ε_f/ε_r) têm padrão `None` ou 0 = "sem dado" e não mudam o resultado atual;
  - números de teste são entradas de teste rotuladas;
  - os valores do livro entram com unidade de origem (lb, in, ft) e são convertidos dentro do teste.
- Texto de K na exibição (spec §6), exato:
  - `"K = <valor> °/g (pneus + transferência + camber + roll steer; sem compliance, torque de alinhamento e tração)"`, com o valor de sinal explícito e duas casas decimais, vírgula como separador;
  - em seguida `" · Subesterço"` para K > 0, `" · Sobresterço"` para K < 0 e `" · Neutro"` só para K == 0 exato. Banda de neutro só por EDR;
  - prefixo `"DEMONSTRATIVO · "` se a pior origem ≠ `"● Dado do TX"` (D16).
- Testes: scripts com `check()` e linha final `N PASS, 0 FAIL, de T testes`. No Git Bash: `export UV_SYSTEM_CERTS=1`, depois `uv run python -X utf8 tests/<script>.py`. Nunca `python -` com stdin. Processo travado: encerrar só pelo PID.
- Fim de linha LF (o repo tem `* -text` e `core.autocrlf=true`; `file` não pode acusar CRLF).
- Branch `feat/v4-0-inc2-equilibrio-linear`, criada da ponta da branch deste plano (`docs/v4-0-plano-inc2`, que sai da `main` em `edd26a2`). Commits separados por propósito, com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Push e PR só com pedido do usuário.
- Nenhuma fórmula da planilha muda. Nenhum teste existente é enfraquecido; mudar o esperado de um teste existente exige dizer por que no commit.

## Contagem de testes (esperado no fim)
| Script | Antes | Depois | IDs novos |
|---|---|---|---|
| `tests/test_equilibrio_linear.py` (novo) | — | 18 | TC-EQ-021..038 |
| `tests/test_equilibrio.py` | 20 | 28 | TC-EQ-039..046 |
| `tests/test_kinematics_model.py` | 74 | 76 | TC-EQ-047..048 (gradiente de camber) |
| `tests/mutation_equilibrio.py` (novo) | — | 6/6 | — |
| `tests/test_tire_model.py`, `tests/test_tire_oracles.py` | 43, 5 | 43, 5 | — (troca de eixo, Task 8) |

## Review Focus
1. **Raio de curva ausente com uma hipótese que precisa dele** (Ackermann, cos δ ou aero com velocidade ligados sem R). Esperado: `ValueError` na construção do caso, com a lista do que falta. Nunca um R implícito (Task 5, TC-EQ-039).
2. **Tração que passa do atrito longitudinal da roda** (Fx exigido > Fx_max). Esperado: capacidade `None` com o motivo "tração excede o atrito longitudinal", nunca raiz de número negativo (Task 7, TC-EQ-044).
3. **K com C_α ≤ 0 ou rigidez nula** (roda descolada, ou Fz limitado ao FZMIN numa linha). Esperado: a parcela fica N/A com motivo, nunca divisão por zero (Task 4, TC-EQ-033).
4. **CG lateral que inverte o sentido pior** (y_cg > 0 piora a curva à direita). Esperado: `analise_par_dois_sentidos` devolve os dois sentidos e o relatório usa o pior, nunca só a esquerda (Task 6, TC-EQ-042).
5. **Ajuste do polinômio C_α = a·Fz − b·Fz² com b ≤ 0**, isto é, sem sensibilidade à carga no trecho ajustado. Esperado: o cruzamento K_llt aproximado × exato diz "polinômio sem sensibilidade à carga no trecho", sem comparar (Task 4, TC-EQ-036).

---

### Task 1: Rigidez de deriva e de camber do PAC2002

**Files:**
- Modify: `python/tire_model.py` (funções novas no fim; nada existente muda)
- Create: `tests/test_equilibrio_linear.py` (cabeçalho `check()` e resumo copiados de `tests/test_equilibrio.py`)

**Interfaces:**
- Produces:
  - `rigidez_deriva(ds, fz: float, gamma: float = 0.0) -> float`: C_α em N/rad, pela definição dos Global Constraints, por diferença central em α com passo `h = 1e-6` rad em `wheel_forces(ds, "FR", fz, ±h, gamma, 0.0)`.
  - `rigidez_camber(ds, fz: float) -> float`: C_γ em N/rad, diferença central em γ com o mesmo `h`, α = 0.
  - As duas seguem o EDR-056 (Fz e γ limitados à faixa) **por quem chama**; aqui, fora da faixa levanta `TireRangeError`, como `wheel_forces`.

- [ ] **Step 1: Testes que falham** (`tests/test_equilibrio_linear.py`):
  - `TC-EQ-021`: com um dataset de teste sem deslocamentos (cópia de `ds` com todos os `PHY*`, `PVY*` e `RHY*` iguais a 0, rotulada "só de teste"), `rigidez_deriva(ds0, FNOMIN) == abs(pure_fy0(ds0.p, FNOMIN, 0, 0)[1]["Ky"])` com erro relativo < 1e-6. Com o `ds` real, `rigidez_deriva > 0`.
  - `TC-EQ-022`: `rigidez_camber(ds, FNOMIN) > 0`, e igual à diferença central de `wheel_forces(...)[1]` feita no teste com outro passo (1e-5), com erro relativo < 1e-4.
  - `TC-EQ-023`: `rigidez_deriva(ds, fz)` cresce de 0,5·FNOMIN para FNOMIN (sensibilidade à carga com o sinal esperado do PAC2002) e a razão C_α/Fz cai (Gillespie p. 215: o coeficiente de deriva diminui com a carga). As duas afirmações são conferidas no `.tir` atual e registradas no detalhe. Se o `.tir` não mostrar isso, o teste falha e o executor relata; não ajuste.
- [ ] **Step 2:** Rodar e ver falhar (`AttributeError`).
- [ ] **Step 3:** Implementar as duas funções em `python/tire_model.py`, com docstring citando o Gillespie p. 215 e a definição de sinal.
- [ ] **Step 4:** Rodar e ver passar: `3 PASS, 0 FAIL, de 3 testes`. Rodar também `tests/test_tire_model.py` (43) e `tests/test_tire_oracles.py` (5).
- [ ] **Step 5: Commit** `feat: rigidez de deriva e de camber do PAC2002 (V4.0, inc. 2)`

### Task 2: Gradiente de camber no solo por rolagem

**Files:**
- Modify: `python/kinematics_model.py` (funções novas perto de `roll_steer_coefficient`, linha ~736)
- Test: `tests/test_kinematics_model.py` (2 checks novos antes do resumo)

**Interfaces:**
- Produces:
  - `camber_gradient_from_body(dgamma_body_dz_left: float, dgamma_body_dz_right: float, track: float) -> dict`: devolve `{"L": ∂γ_L/∂φ, "R": ∂γ_R/∂φ, "eixo": (R − L)/2}` em rad/rad. Na rolagem φ (para a direita), o curso da roda direita é +(t/2)·φ e o da esquerda −(t/2)·φ, como em `roll_steer_coefficient`. Camber no solo pela eq. 6-50 com o sinal de cada lado: γ_R,solo = γ_R,corpo + φ e γ_L,solo = γ_L,corpo − φ (convenção do projeto, topo para fora +).
  - `camber_gradient(corner_left, corner_right, track, dphi=1e-3) -> dict`: mesmo retorno, com dγ_corpo/dz de cada canto por diferença central na `sweep` (`metrics["camber_deg"]`, em graus → rad).
- [ ] **Step 1: Testes que falham:**
  - `TC-EQ-047`: `camber_gradient_from_body(0, 0, t)["eixo"] == 1.0` e `["R"] == 1.0`, `["L"] == −1.0` (braços paralelos iguais, Gillespie p. 234).
  - `TC-EQ-048`: com os cantos sintéticos esquerdo e direito de `data/hardpoints_synthetic_4cantos_V2.0.csv` (rotulados sintéticos, mesmo carregamento de `tests/test_kinematics_model.py` TC-KIN-129), `camber_gradient(...)` é igual a `camber_gradient_from_body` alimentada com as derivadas tiradas da `sweep` no próprio teste (erro < 1e-9). Também: o gradiente do eixo é < 1, porque o braço desigual reduz o camber positivo da roda externa; o número fica registrado no detalhe. Se der ≥ 1, relate (é achado sobre a geometria sintética, não defeito de código).
- [ ] **Step 2:** Rodar `tests/test_kinematics_model.py` e ver os 2 falharem.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** `76 PASS, 0 FAIL, de 76 testes`.
- [ ] **Step 5: Commit** `feat: gradiente de camber no solo por rolagem (V4.0, inc. 2)`

### Task 3: Funções do Gillespie e oráculos dos exemplos resolvidos

**Files:**
- Create: `python/equilibrio_linear.py`
- Test: `tests/test_equilibrio_linear.py`

**Interfaces:**
- Produces, todas puras e em SI:
  - `gradiente_pneus(W_f_N, W_r_N, C_f_N_rad, C_r_N_rad) -> float`: K = (W_f/C_f − W_r/C_r)/G em rad/(m/s²), com C de **eixo** (dois pneus). Eq. 6-15.
  - `para_graus_por_g(K: float) -> float`: = degrees(K)·G.
  - `velocidade_caracteristica(L_m, K) -> float | None`: √(L/K) se K > 0; senão None. Eq. 6-18.
  - `velocidade_critica(L_m, K) -> float | None`: √(−L/K) se K < 0; senão None.
  - `ponto_neutro_ate_traseiro(L_m, C_f, C_r) -> float`: L·C_f/(C_f + C_r) (p. 233).
  - `gradiente_rolagem(W_N, h1_m, K_phi_f, K_phi_r) -> float`: W·h1/(K_φf + K_φr − W·h1)/G em rad/(m/s²). Eq. 6-32. Levanta `ValueError` se o denominador ≤ 0.
  - `parcela_camber(Cg_f, Ca_f, dgf, Cg_r, Ca_r, dgr, dphi_day) -> float`: (Cg_f/Ca_f·dgf − Cg_r/Ca_r·dgr)·dphi_day. Eq. 6-56.
  - `parcela_transferencia_aprox(W_f_N, C_f, b_f, dFz_f, W_r_N, C_r, b_r, dFz_r) -> float`: forma da eq. 6-49 (p. 217; citação corrigida em 2026-10-21, antes 6-47), dividida por G (rad/(m/s²)) e avaliada no ΔFz da a_y dada; `b` por pneu em 1/N·(N/rad), coerente com C_α = a·Fz − b·Fz² por pneu.
- [ ] **Step 1: Testes que falham** (valores do livro com conversão no teste: 1 lb = 4,4482216 N; 1 in = 0,0254 m; 1 ft = 0,3048 m; rigidez em lb/deg → N/rad pela multiplicação por 4,4482216·57,29578):
  - `TC-EQ-024`: exemplo 1, K = 0,11 deg/g ± 0,005, com C de eixo = 2 × (232 e 195 lb/deg) e W_f = 1901 lb, W_r = 1552 lb (via `gradiente_pneus` e `para_graus_por_g`).
  - `TC-EQ-025`: `velocidade_caracteristica` com L = 110,6 in e K = 0,11 deg/g dá 393 ft/s ± 1 (conta impressa). Com L = 100,6 in dá 375 ft/s ± 1. O detalhe do check diz "errata do Gillespie p. 232: V_char usa 110,6 in; o problema dá 100,6 in".
  - `TC-EQ-026`: `ponto_neutro_ate_traseiro(8,38 ft, 232, 195)` = 4,55 ft ± 0,01.
  - `TC-EQ-027`: exemplo 2, `gradiente_rolagem` com W = 2750 lb, h1 = 10 in, K_φf = 1500 e K_φr = 1606 in·lb/deg dá 10,5 deg/g ± 0,05.
  - `TC-EQ-028`: `parcela_camber(0,1, 1, 1,0, 0,1, 1, 0, dphi)` com dphi = 10,5 deg/g (convertido) dá 1,05 deg/g ± 0,005.
  - `TC-EQ-029`: `kinematics_model.roll_steer_understeer_deg_per_g(0.0, 0.122, 10.5)` = −1,281 ± 0,001 deg/g. O detalhe registra que o livro imprime 1,28 e diz sobresterço (p. 235).
  - `TC-EQ-030`: `velocidade_critica(L, −|K|)` = `velocidade_caracteristica(L, |K|)` e `velocidade_caracteristica(L, −|K|) is None`.
- [ ] **Step 2:** Ver falhar.
- [ ] **Step 3:** Implementar `python/equilibrio_linear.py` (docstring: Gillespie cap. 6, equações citadas, errata).
- [ ] **Step 4:** `10 PASS, 0 FAIL, de 10 testes`.
- [ ] **Step 5: Commit** `feat: funções do Gillespie cap. 6 com oráculos dos exemplos resolvidos (V4.0, inc. 2)`

### Task 4: Parcelas de K de um caso e tabela linear

**Files:**
- Modify: `python/equilibrio_linear.py`; `python/equilibrio.py` (campo novo em `CasoEquilibrio`)
- Test: `tests/test_equilibrio_linear.py`

**Interfaces:**
- Consumes: Tasks 1 e 3; `equilibrio.cargas`, `equilibrio.camber`, `equilibrio.capacidade_eixo` (regras do EDR-056), `suspension_model.lateral_dfz`, `suspension_model.static_fz_corner`.
- Produces:
  - Campo novo em `CasoEquilibrio`: `roll_steer: dict[str, float]`, com chaves `"F"` e `"R"` em rad/rad (convenção do SUS-415) e padrão 0 = "sem dado".
  - `@dataclass(frozen=True) ParcelasK`, com os campos `ay_ms2`, `k_pneus`, `k_transferencia`, `k_camber`, `k_roll_steer`, `k_total`, `dphi_day` (todos float | None, em rad/(m/s²); dphi_day em rad/(m/s²)) e `motivo: str | None`.
  - `parcelas_k(caso, ay_ms2: float) -> ParcelasK`. Regras:
    - `k_pneus` usa a carga estática por roda, com C de eixo = soma de `rigidez_deriva` das duas rodas e γ estático;
    - `k_pneus + k_transferencia` = (W_f/C_f(a_y) − W_r/C_r(a_y))/G, com C do eixo = soma das rigidezes das rodas nas cargas e γ dessa a_y. Logo `k_transferencia` é a diferença. Com a_y → 0, `k_transferencia → 0`;
    - `k_camber` usa C_γ e C_α de eixo na carga estática, o gradiente de eixo `(ganho_camber["FR"] − ganho_camber["FL"])/2` (e o traseiro igual) e `dphi_day = lateral_dfz(cfg, ay)["roll_angle_rad"]/ay`. Em a_y = 0, use o limite com a_y = 1e-6·G;
    - `k_roll_steer = (roll_steer["F"] − roll_steer["R"])·dphi_day`;
    - Fz e γ fora da faixa seguem o EDR-056 (limitar); Fz ≤ 0 ou C ≤ 0 dão a parcela `None` e `motivo`, e `k_total` também `None`.
  - `angulos_necessarios(caso, ay_ms2, n_alfa=401) -> tuple[float, float] | None`: α de referência de cada eixo em que `fy_eixo` (com os valores limitados do EDR-056) é igual à força exigida (`equilibrio.forca_exigida`). Bissecção entre 0 e o α do pico na grade, até |ΔF| < 1e-9·força. Devolve None se a exigência passar da capacidade.
  - `tabela_linear(caso, ay_max_g=0.4, passo_g=0.05) -> list[dict]`: por linha, as parcelas, o `k_inclinacao` (diferença de α_f − α_r entre a linha e a anterior, dividida pela diferença de a_y; na primeira linha, (α_f − α_r)/a_y com a_y = 0,01·G) e os textos `texto_k` (abaixo). A faixa linear de 0 a 0,4 g é a da spec §6 (Milliken p. 315).
  - `texto_k(p: ParcelasK, pior_origem: str) -> str`: o texto exato dos Global Constraints, ou `"N/A: " + p.motivo`.
- [ ] **Step 1: Testes que falham:**
  - `TC-EQ-031`: caso simétrico do `tests/test_equilibrio.py` (TC-EQ-010) → `k_pneus == 0` (|·| < 1e-12), `k_total ≈ 0` e `texto_k` termina em "Neutro" só se `k_total == 0` exato. Senão, o sinal manda.
  - `TC-EQ-032`: veículo de teste com λ_f 0,7 contra 0,5 (mesma escala de teste LMUY 0,45 do TC-EQ-011) → `k_transferencia` em 0,3 g maior com λ_f 0,7 (Gillespie p. 214, mais transferência na frente = mais subesterço).
  - `TC-EQ-033`: um caso com roda descolada em 0,4 g (só de teste) → parcela `None` e `motivo` contém "descolamento", sem exceção.
  - `TC-EQ-034`: consistência passo 1 × passo 2 (spec §6 e §9 item 2). No veículo de teste, sem roll steer: `|k_inclinacao(primeira linha) − (k_pneus + k_camber)| / |k_pneus + k_camber| < 1e-3`, com o ganho de camber ligado (valores de teste) e desligado.
  - `TC-EQ-035`: sinal do camber amarrado ao EDR-002 (spec §6). Ganho de camber de eixo +1 na frente (braços paralelos, só de teste) → `k_camber > 0` (subesterço, como no exemplo 2 do Gillespie).
  - `TC-EQ-036`: cruzamento com a forma do livro (spec §6, último item). Ajuste por mínimos quadrados de C_α = a·Fz − b·Fz² a `rigidez_deriva` nas cargas de FZMIN a FZMAX (21 pontos); compare `parcela_transferencia_aprox` com `k_transferencia` em 0,2 g:
    - se b > 0: mesmo sinal, e diferença relativa ≤ 2·max(ε, r), com ε = 2b·ΔFz²/C (do eixo mais carregado) e r = resíduo relativo máximo do ajuste. Os números ficam no detalhe;
    - se b ≤ 0: o check confere que a função de cruzamento devolve o motivo "polinômio sem sensibilidade à carga no trecho" (Review Focus 5).
  - `TC-EQ-037`: `texto_k` com pior origem `"◐ Dado do T09"` e K = +0,123 °/g (ParcelasK construída no teste) é exatamente `"DEMONSTRATIVO · K = +0,12 °/g (pneus + transferência + camber + roll steer; sem compliance, torque de alinhamento e tração) · Subesterço"`.
  - `TC-EQ-038`: `tabela_linear` tem `int(0.4/0.05)+1` linhas, com a_y crescente, e `k_roll_steer` igual a (ε_f − ε_r)·dphi_day linha a linha.
- [ ] **Step 2:** Ver falhar.
- [ ] **Step 3:** Implementar. Para o ajuste do TC-EQ-036, crie `ajuste_polinomio_rigidez(ds, n=21) -> tuple[float, float, float]` (a, b, resíduo relativo máximo) e `cruzamento_transferencia(caso, ay_ms2) -> dict` (aprox, exato, ε, r, motivo) em `equilibrio_linear.py`. Use `numpy.linalg.lstsq`; numpy já é dependência.
- [ ] **Step 4:** `18 PASS, 0 FAIL, de 18 testes`, e `tests/test_equilibrio.py` continua 20/20.
- [ ] **Step 5: Commit** `feat: parcelas do gradiente de subesterço e tabela linear (V4.0, inc. 2)`

### Task 5: Ackermann e cos δ no limite (hipóteses 2 e 3)

**Files:**
- Modify: `python/equilibrio.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Produces:
  - Campos novos em `CasoEquilibrio` (último lugar, com padrão): `raio_m: float | None = None` (R do skidpad, "a confirmar") e `ackermann_pct: float | None = None` (% Ackermann da geometria, SUS-414; None = hipótese desligada).
  - `__post_init__`: `ackermann_pct` não None exige `raio_m`, e o mesmo vale para `cza_m2` e `cda_m2` (Tasks 6 e 7). Senão `ValueError` com a lista do que falta.
  - Com `raio_m` definido: δ_ref = L/R (rad) para a frente. O deslocamento de α de cada roda dianteira soma ao do toe: Δα_roda += −(δ_roda − δ_ref), com δ_externa e δ_interna dados por `ackermann_pct`. A interna fica `δ_o + pct/100·(δ_i,Ack − δ_o)`, com `kinematics_model.ackermann_inner_ideal_deg`. A externa δ_o sai da condição média (δ_o + δ_i)/2 = δ_ref, resolvida por bissecção.
  - A força do eixo dianteiro na direção do carro é multiplicada por cos δ_ref (spec 7.1, item 3). A traseira não muda.
- [ ] **Step 1: Testes que falham:**
  - `TC-EQ-039`: `CasoEquilibrio(..., ackermann_pct=100.0)` sem `raio_m` levanta `ValueError` que cita "raio_m".
  - `TC-EQ-040`: com R = 8,0 m (só de teste) e `ackermann_pct=None`, a capacidade dianteira em a_y = 0 é a anterior × cos(L/R) (erro relativo < 1e-12), e a traseira não muda.
  - `TC-EQ-041`: com R = 8,0 m, `ackermann_pct=0` → as duas rodas com δ = δ_ref, Δα extra nulo. Com `ackermann_pct=100` → δ_i − δ_o igual ao Ackermann ideal (`ackermann_inner_ideal_deg`) dentro de 1e-9 rad, média δ_ref, e os Δα das rodas FL e FR com sinais opostos.
- [ ] **Step 2:** Ver falhar. **Step 3:** Implementar. **Step 4:** `23 PASS, 0 FAIL, de 23 testes`; TC-EQ-001..020 inalterados. **Step 5: Commit** `feat: Ackermann e cos δ na análise de par (V4.0, inc. 2)`

### Task 6: CG lateral e aero com a velocidade (hipóteses 7 e 8), dois sentidos de curva

**Files:**
- Modify: `python/suspension_model.py` (funções novas); `python/equilibrio.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Produces:
  - `suspension_model.static_fz_corner_cg_lateral(cfg, y_cg_m: float) -> dict`: estática com CG deslocado y (+ = esquerda, ISO). Por eixo, ΔFz = W_eixo·y/t_eixo para a esquerda; soma igual à de `static_fz_corner`.
  - `suspension_model.downforce_por_velocidade(rho_kg_m3, cza_m2, v_ms) -> float` = 0,5·ρ·CzA·V².
  - Campos em `CasoEquilibrio`: `cg_lateral_m: float = 0.0`, `cza_m2: float | None = None`, `rho_kg_m3: float | None = None`. `cza_m2` exige `raio_m` e `rho_kg_m3`.
  - `cargas(caso, ay)` passa a somar a parcela de CG lateral à estática e, com `cza_m2`, usa downforce = `downforce_por_velocidade(ρ, CzA, √(a_y·R))` com `aero_balance_front`, no lugar de `downforce_N`.
  - `analise_par_dois_sentidos(caso, **kw) -> dict[str, ResultadoPar]` com chaves `"esquerda"` e `"direita"`. A direita é o caso espelhado (y_cg → −y_cg; toe, camber estático e ganho de camber trocados entre L e R), analisado como curva à esquerda. Inclui também `"pior"`: o de menor `ay_lim`; N/A conta como pior.
- [ ] **Step 1: Testes que falham:**
  - `TC-EQ-042`: carro simétrico com y_cg = 0 → esquerda e direita têm o mesmo `ResultadoPar` (igualdade dos campos de veredito e saturações). Com y_cg = +0,02 m (só de teste, cenário LMUY 0,45 do TC-EQ-011 para haver saturação) → a soma das cargas estáticas não muda e o lado esquerdo ganha W_eixo·y/t por eixo. O esperado é `pior == "direita"`, com `ay_lim` da direita ≤ `ay_lim` da esquerda: na curva à direita, as rodas externas são as esquerdas, que já estão mais carregadas, e a sensibilidade à carga reduz a capacidade. Os números vão no detalhe. Se der o contrário, relate; não ajuste.
  - `TC-EQ-043`: com CzA = 3,0 m², ρ = 1,2 kg/m³ e R = 8,0 m (só de teste), a soma dos Fz na linha a_y é m·G + 0,5·1,2·3,0·(a_y·8,0) (erro < 1e-9 N), e a divisão frente/traseira segue `aero_balance_front`.
- [ ] **Step 2:** Ver falhar. **Step 3:** Implementar. **Step 4:** `25 PASS, 0 FAIL, de 25 testes`. **Step 5: Commit** `feat: CG lateral, aero com a velocidade e dois sentidos de curva (V4.0, inc. 2)`

### Task 7: Tração na traseira com elipse de atrito e diferencial aberto (hipóteses 9 e 10, variante da planilha)

**Files:**
- Modify: `python/equilibrio.py`
- Test: `tests/test_equilibrio.py`

**Interfaces:**
- Antes de codificar: confira o Milliken §2.7 na imagem do PDF. Use a forma da elipse (Fx/Fx_max)² + (Fy/Fy_max)² ≤ 1 só se o livro a der assim; cite a página no docstring. Se a forma for outra, pare e relate.
- Produces:
  - Campos: `cda_m2: float | None = None`, `crr: float | None = None` (exigem `raio_m` e `rho_kg_m3`; `crr` sozinho exige só a massa).
  - Fx exigido no eixo traseiro na linha a_y = 0,5·ρ·CdA·V² + Crr·m·G + F_yf·sen δ_ref, com V² = a_y·R e F_yf = força exigida dianteira (spec 7.4, h9). Diferencial aberto: Fx igual nas duas rodas traseiras (h10).
  - Fx_max por roda = pico de Fx puro do PAC2002 na carga (e γ) da roda: `abs(Dx) + SVx` de `pure_fx0`, pela mesma forma fechada do Fy (C ≥ 1). Confirme PCX1 ≥ 1 no `.tir` atual; senão, máximo numérico em κ.
  - Capacidade lateral de cada roda traseira multiplicada por √(1 − (Fx/Fx_max)²). Se Fx > Fx_max em alguma roda, a capacidade é `None` com o motivo `"tração excede o atrito longitudinal em <canto>"`, e a linha é inválida.
- [ ] **Step 1: Testes que falham:**
  - `TC-EQ-044`: Fx exigido maior que Fx_max (CdA enorme, só de teste) → capacidade traseira `None` com o motivo acima, sem exceção.
  - `TC-EQ-045`: com Crr = 0,015 e CdA = 1,0 (só de teste), a capacidade traseira numa linha é a anterior × √(1 − (Fx/Fx_max)²) por roda (erro < 1e-9 relativo, recomposto no teste), e a frente não muda.
  - `TC-EQ-046`: no veículo de teste com LMUY 0,45 (cenário do TC-EQ-011, λ_f 0,5, NEUTRO sem tração), ligar a tração leva o veredito para LOOSE (spec 7.4 h9: ignorar a tração "superestima a traseira, puxa para push"). Se não levar, relate com os números; não ajuste.
- [ ] **Step 2:** Ver falhar. **Step 3:** Implementar. **Step 4:** `28 PASS, 0 FAIL, de 28 testes`. **Step 5: Commit** `feat: tração na traseira com elipse de atrito e diferencial aberto (V4.0, inc. 2)`

### Task 8: Testes do pneu em ISO_TYDEX

**Files:**
- Modify: `tests/test_tire_model.py:12` (padrão de `LD`); `tests/test_tire_oracles.py:14`

**Interfaces:** nenhuma nova.
- [ ] **Step 1:** Leia os dois scripts inteiros e classifique cada check:
  - os que avaliam no referencial do arquivo (`combined_forces`, `pure_fy0`), indiferentes ao eixo;
  - os que testam de propósito a transformação SAE_CALSPAN;
  - os que dependem do padrão.
- [ ] **Step 2:** Mude o padrão para `"ISO_TYDEX"` (EDR-039). Os checks que testam a transformação SAE passam a pedir `"SAE_CALSPAN"` explicitamente. Ajuste um valor esperado só quando a mudança de eixo o altera por definição (sinal de Fy ISO, por exemplo), com a justificativa no commit.
- [ ] **Step 3:** `43 PASS` e `5 PASS`, mesmas contagens. Rodar `tests/mutation_tire.py`: 25/25 detectadas, com a pré-checagem passando.
- [ ] **Step 4: Commit** `test: testes do pneu carregam o .tir em ISO_TYDEX (EDR-039)`

### Task 9: Mutação do equilíbrio

**Files:**
- Create: `tests/mutation_equilibrio.py` (padrão de `tests/mutation_tire.py`: pré-checagem do original e uma linha por mutação com DETECTADA ou NÃO DETECTADA; linha final `N/M mutações detectadas`, no mesmo formato que `tools/rodar_testes.py` lê de `mutation_tire.py`)
- Modify: `tools/rodar_testes.py` (`MUTACAO` vira lista de scripts e esperados; o log mostra os dois)

**Interfaces:** as mutações são aplicadas em cópias do código-fonte, em memória ou em pasta temporária, como em `mutation_tire.py`; nunca no arquivo do repositório.
- [ ] **Step 1:** Seis mutações (spec §9, item 8), cada uma detectada por `tests/test_equilibrio.py` e `tests/test_equilibrio_linear.py`:
  1. trocar a por b em `forca_exigida`;
  2. tirar o cos δ da frente;
  3. inverter o sinal do Ackermann;
  4. inverter o sinal do ganho de camber em `camber()`;
  5. trocar o critério de NEUTRO pelo passo de exibição (regra anterior ao EDR-056);
  6. remover o prefixo `"DEMONSTRATIVO · "` do `texto_veredito`.
- [ ] **Step 2:** Rodar: `6/6` com a pré-checagem passando. Uma mutação não detectada é lacuna de teste: acrescente asserção no check existente que cobre aquela regra (sem ID novo) e relate.
- [ ] **Step 3: Commit** `test: mutação do equilíbrio (V4.0, inc. 2)`

### Task 10: Dívidas do incremento 1, registro e EDR-057

**Files:**
- Modify: `python/equilibrio.py`; `python/caso_planilha.py`; `tools/relatorio_inc1.py`; `tests/test_equilibrio.py`; `tools/rodar_testes.py`; `CLAUDE.md`; `docs/Engineering_Decision_Register.md`

**Interfaces:**
- `com_fatores` aceita só os nomes da tabela de fatores de escala do PAC2002 (help do Adams pp. 23-25, conferidas na imagem em 2026-10-20). A tupla `FATORES_LAMBDA` fica em `python/equilibrio.py`, transcrita da tabela; `LONGVL` não entra. O valor tem de ser finito e > 0.
- O motivo `"não satura até <x> g"` usa a última linha varrida (`linhas[-1].ay_ms2/G`), não `ay_max_g`.
- Função pública `limitacoes_detalhe(res: ResultadoPar, caso) -> list[dict]`. `tools/relatorio_inc1.py` passa a usá-la no lugar de `eq._entrada_limitada` e `eq._rodas`.
- `caso_planilha.pior_origem_do_caso` lê a origem do pneu da célula de origem da 10_TIRE (`raizes.celula_origem("10_TIRE", "B86")` → I84), não da constante. Ganha também `pior_origem_entradas(xlsx) -> str` (sem o pneu).
- Números nos motivos com vírgula decimal.
- [ ] **Step 1: Asserções** dentro dos checks existentes, sem IDs novos:
  - TC-EQ-018: `com_fatores(ds, {"LONGVL": 1.0})`, `{"LMUY": 0}` e `{"LMUY": float("nan")}` levantam `ValueError`;
  - TC-EQ-017: `varredura_pneu(caso, {"LMUY": [0.5]})` é igual a `analise_par` com o dataset escalado à mão;
  - TC-EQ-014: o motivo usa a última linha varrida com `ay_max_g` = 0,33 e passo 0,05 (diz "0,3 g");
  - TC-EQ-020: `pior_origem_entradas(viva) == "○ Arbitrário / demonstrativo"` (valor conhecido em 2026-10-21; SUS-007/008), e o arquivo não muda.
- [ ] **Step 2:** Implementar; rodar `tests/test_equilibrio.py` (28) e `tests/test_equilibrio_linear.py` (18).
- [ ] **Step 3:** EDR-057, no formato do EDR-056 e com a autorização do usuário: as escolhas de método deste plano (ver "Autorizações", item 2), com as fontes desta página.
- [ ] **Step 4:** `tools/rodar_testes.py`:
  - `("equilíbrio", "tests/test_equilibrio.py", 28, ...)`;
  - `("equilíbrio linear", "tests/test_equilibrio_linear.py", 18, "plano do incremento 2 da V4.0")`;
  - cinemática 76;
  - mutação do equilíbrio 6.
  No `CLAUDE.md`, a linha dos esperados atualizada. Suíte inteira em segundo plano: tudo PASS.
- [ ] **Step 5:** Commits separados:
  1. `fix: dívidas do incremento 1 (fatores λ, motivo, API das limitações, origem do pneu)`;
  2. `docs: EDR-057 (método do equilíbrio no incremento 2)`;
  3. `test: registra os testes do incremento 2 na suíte`.
