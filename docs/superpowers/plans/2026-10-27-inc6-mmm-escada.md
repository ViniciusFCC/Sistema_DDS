# Incremento 6 (MMM e escada de hipóteses, só Python): plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o MMM quase estático em raio fixo (`python/mmm.py`) e a escada de hipóteses (`python/escada.py`), com os testes TC-MMM e TC-ESC, a mutação e o relatório `docs/inc6/escada-hipoteses.md`, sem nenhuma mudança na planilha.

**Architecture:**
- `python/mmm.py` (novo, física pura): `Hipoteses` (variantes), `VARIANTES` (contrato), cinemática por roda, trim parametrizado por A_Y (desacoplado com Brent; acoplado com Newton 2-D), limite por bisseção, ponto e diagrama, sensibilidade.
- `python/escada.py` (novo, orquestração): degrau 1 e degrau 2, sem veredito de tolerância.
- `tools/relatorio_escada.py` (novo): relatório sobre o caso da planilha V4.2, em cópia recalculada.
- `python/equilibrio.py`: só nomes públicos novos, sem número mudado.

Dependência: escada → mmm → equilibrio.

**Tech Stack:** Python 3.13 (stdlib: `math`, `dataclasses`, `typing.Literal`), `tire_model` (PAC2002), `suspension_model`, `kinematics_model`, scripts com `check()`.

**Spec:** `docs/superpowers/specs/2026-10-27-inc6-mmm-escada-design.md` (o "adendo"; §n abaixo = seção do adendo), sobre a spec base `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` §7.4-§7.6.

## Decisões do plano (o controlador escolheu onde uma opção domina; vão no EDR-064)

1. **As chaves da planilha já existem.** A V4.1 já tem h2, h3, h7, h8 e h9 (`caso_planilha.caso_da_planilha_v41`). Por isso a variante "planilha" de cada hipótese é o `CasoEquilibrio` como a planilha o monta (campo None = hipótese da planilha desligada). `Hipoteses.planilha()` só escolhe as fórmulas da planilha. A variante Python de uma hipótese cuja chave está desligada no caso não liga nada e devolve o mesmo resultado, com `motivo = "hipótese desligada no caso (<campo>)"`. O desvio A1 do adendo é corrigido nesse sentido (Task 9).
2. **O MMM exige `raio_m`.** Sem ele, `trim`, `limite`, `ponto` e `sensibilidade` lançam `ValueError("MMM em raio fixo exige raio_m (raio do skidpad), que está faltando.")`.
   - Os testes usam R = 8,5 m, rotulado "sintético de teste" (o mesmo R do veículo de teste dos checks).
   - O relatório sobre a planilha usa o R da planilha. Se estiver vazio, sai com código 3 e a mensagem "informe --raio"; com `--raio`, o relatório escreve o valor e a origem que o usuário der (`--origem-raio`). Nenhum R é escolhido pelo código.
3. **Saturação por eixo nas variantes acopladas.** Além de T não existe trim, então o a_y de saturação do eixo que **não** satura não tem definição física no MMM.
   - Variantes desacopladas: os dois `ay_sat_*` saem por bisseção por eixo.
   - Variantes acopladas: o eixo que satura tem `ay_sat = T`, e o outro sai `None` com `motivo_sat = "acoplado: além de T não há trim"`.
   - NEUTRO quando a folga do outro eixo em T for ≤ (força exigida dele por m/s²) × `resolucao_ms2`. É o equivalente em força ao |S_r − S_f| ≤ R do `analise_par`.
4. **Hipótese 12 (jacking).** O Python não tem modelo de jacking (o EDR-053 só existe em texto), e o jacking não muda a soma das Fz, só a altura e o camber. A sensibilidade passa a ser **por 10 mm de altura do CG** (`cfg.cg_height`). O camber já é coberto pela hipótese 4. Isso corrige o §4.3 do adendo (Task 9).
5. **h_cp só por sensibilidade.** `Hipoteses.h_cp_m: float | None = None`. None deixa a parcela D·h_cp/L fora (sem dado). Só `sensibilidade(..., "h_cp", passo)` liga essa parcela, e só com `transf_long="regime"`.
6. **Tolerância dos oráculos numéricos.** Os testes usam a tolerância que o próprio teste justifica (resíduo do solver 1e-6 N; K relativo 1e-2, pelo passo finito). Se um oráculo falhar, o implementador **para e reporta**: nunca afrouxa a tolerância nem ajusta para bater (CLAUDE.md).

## Autorizações a pedir antes de executar (CLAUDE.md)

1. **EDRs novos**:
   - EDR-064 "Método do MMM e da escada no Python" (adendo §2, §3.2 e desvios A1-A5; decisões 1-6 deste plano);
   - EDR-065 "Tolerância da escada e regra do NEUTRO" (decisão do usuário, adendo §5.3; nasce PROPOSED e fica sem número até o usuário decidir);
   - EDR-066 "Achados da escada sobre fórmulas da planilha" (adendo §7; reabre parcialmente o EDR-057 e o SUS-414 sem alterá-los).
2. **IDs de teste**: TC-MMM-001 a 011 e TC-ESC-001 a 003 (tabela abaixo).
3. **Raio para o relatório** (decisão 2): o R da planilha está vazio. O usuário informa o valor e a origem, ou o relatório fica sem rodar. O R do regulamento só entra com a fonte conferida.
4. **Nenhum SUS-** e nenhuma fórmula da planilha mudam.

## Global Constraints

- Branch `feat/inc6-mmm-escada` (já criada, com o adendo no commit 2910072). Commits separados por propósito (reorganização, código, documentação), com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Conferir LF (`file`, `grep -c $'\r'`) antes de cada commit.
- `uv run python -X utf8 ...` (no Git Bash, `export UV_SYSTEM_CERTS=1` antes). Nunca `python` direto.
- Núcleo em ISO 8855 e SI. Curva à esquerda; a direita via `equilibrio.espelhar`. α < 0 dá Fy > 0 à esquerda.
- Nenhum número do Python vai para a planilha. A planilha viva e a de referência nunca são abertas para escrita; o relatório lê uma cópia recalculada (como `tools/relatorio_inc4.py`).
- O `mmm.py` e o `escada.py` não conhecem a origem dos dados. Todo número do relatório (Task 7) leva a pior origem do caso (`caso_planilha.pior_origem_do_caso_v41`) e a marca "geometria sintética" no cabeçalho. Nenhum número é resultado do carro.
- `equilibrio.py`: só adição. `tests/test_equilibrio.py` 28/28 e `tests/test_equilibrio_linear.py` 18/18 depois de toda tarefa que o toque.
- Por tarefa, só os testes da tarefa e a regressão citada. A suíte inteira (`tools/rodar_testes.py`, ~90 min) roda uma vez, na Task 9, em segundo plano.
- Implementadores e revisões de tarefa em Sonnet; revisão final num despacho em Opus.

## Contagem de testes

| Check | Verifica | Script |
|---|---|---|
| TC-MMM-001 | δ = L/R, β = b/R, toe nulo, A_Y → 0: \|α\| < 1e-9 nas quatro rodas (`alfa="cinematico"`); com δ + 0,01 rad, α_FL e α_FR < 0 e Fy dianteira > 0 | `tests/test_mmm.py` |
| TC-MMM-002 | Pneu de brinquedo (Fy = μ·Fz·tanh(−α/α0), sem sensibilidade à carga, em `ds` falso): T = μ·g e NEUTRO; com a sensibilidade à carga só na traseira, PUSH ou LOOSE com T e eixo limitante derivados à mão no próprio teste (derivação em comentário) | `tests/test_mmm.py` |
| TC-MMM-003 | Força bruta numa grade β × δ (41 × 41, cobrindo o trim de 0 a T) via `ponto`, sem `capacidade_eixo`: o maior A_Y nos cruzamentos de C_N = 0 (interpolação linear entre vizinhos da grade) fica em [0,97·T, T + `resolucao_ms2`] | `tests/test_mmm.py` |
| TC-MMM-004 | Caso sem aero, toe, Ackermann nem roll steer: K da curva de trim em 0,05 g = `parcelas_k(caso, 0,05·G).k_total` (relativo 1e-2) | `tests/test_mmm.py` |
| TC-MMM-005 | a = b e eixos iguais: δ do trim = L/R (1e-6) em três A_Y; `cn_estabilizante` em Q com \|·\| < 1e-6; veredito NEUTRO | `tests/test_mmm.py` |
| TC-MMM-006 | Caso com CG lateral ≠ 0 e `espelhar`: T e veredito de cada sentido iguais aos de `analise_par_dois_sentidos`; `cn_iso` com sinais opostos entre push e loose; `cn_estabilizante` > 0 no push | `tests/test_mmm.py` |
| TC-MMM-007 | No trim: \|ΣFy − m·A_Y\| < 1e-6 N e \|N\| < 1e-6 N·m; A_Y acima do limite dá `convergiu=False` com `motivo` e campos None; caso sem `raio_m` dá o `ValueError` da decisão 2 (Review Focus 1) | `tests/test_mmm.py` |
| TC-MMM-008 | `alfa="cinematico"`, Ackermann 100 %, β pequeno: \|α_FL − α_FR\| < 1e-4 rad; a variante "planilha" dá \|α_FL − α_FR\| ≈ L·t/R² (relativo 5e-2) | `tests/test_mmm.py` |
| TC-MMM-009 | `diferencial="travado"`: contribuição de Fx ao N < 0 (push) em curva à esquerda; aberto: contribuição nula (1e-9); Fx exigido acima do atrito → `motivo` "tração excede…" (Review Focus 4) | `tests/test_mmm.py` |
| TC-MMM-010 | CzA alto: `ponto` com `n_raizes ≥ 2` e o A_Y escolhido é a menor raiz (documentado) | `tests/test_mmm.py` |
| TC-MMM-011 | `set(VARIANTES) == campos de Hipoteses` exceto `h_cp_m`; cada hipótese listada em `VARIANTES` ∈ {1, 2, 3, 7, 9, 10, 11}; `Hipoteses(alfa="x")` dá ValueError | `tests/test_mmm.py` |
| TC-ESC-001 | Degrau 1 nos casos do `test_equilibrio.py` (base, simétrico, com toe, com Ackermann 50 %, com tração), nos dois sentidos: mesmo veredito; \|ay_sat − S\| ≤ `resolucao_ms2` em cada eixo; `cn_estabilizante` vs `c_n` dentro da folga equivalente | `tests/test_escada.py` |
| TC-ESC-002 | Degrau 2: linhas `planilha`, `1+2`, `3`, `7`, `9a`, `9b`, `10`, `10+9b`, `11`, `todas` (a `10+9b` é o travado com o PAC2002 combinado, adendo §6); a linha `planilha` tem Δ = 0; nenhuma linha tem campo de veredito de tolerância; `inverte` ∈ {"não", "sim", "NEUTRO ↔ PUSH", "NEUTRO ↔ LOOSE", "N/A"} | `tests/test_escada.py` |
| TC-ESC-003 | Sensibilidades: cada linha com `unidade` igual a `mmm.UNIDADES[parametro]`; o sinal da de `cg_lateral` troca com o sentido; nenhuma linha tem faixa | `tests/test_escada.py` |

Esperado no fim: `test_mmm.py` 11/11, `test_escada.py` 3/3, `tests/mutation_mmm.py` 5/5, `test_equilibrio.py` 28/28 e `test_equilibrio_linear.py` 18/18 (sem check novo).

## Review Focus

1. **Caso sem raio** (a planilha de hoje tem R vazio). Esperado: `ValueError` com a mensagem da decisão 2, nunca R padrão; o relatório sai com código 3. Testes: TC-MMM-007 e Task 7, passo 2.
2. **Descolamento antes da saturação** (Fz ≤ 0 numa roda com A_Y alto). Esperado: `limite` para no último A_Y com Fz > 0, com `veredito = NA` e o motivo de `equilibrio._descolamento`, como o `analise_par`. Teste: acrescentado ao TC-MMM-007 (caso com bitola estreita e CG alto).
3. **Toe que consome a faixa de α do pneu, ou pico na borda da faixa.** Esperado: o motivo de `capacidade_eixo` ("toe consome a faixa de α", "pico na borda da grade de α") e nenhum número de T. Teste: acrescentado ao TC-MMM-007.
4. **Tração acima do atrito com `tracao="pac2002"`** (sem κ em [KPUMIN, KPUMAX] que dê o Fx). Esperado: `motivo = "tração excede o atrito longitudinal em <canto>"`, igual ao texto da elipse. Teste: TC-MMM-009.
5. **CG lateral ≠ 0** (a planilha usa 0 até medir). Esperado: o pior sentido fica registrado na linha `7` do degrau 2, e o sinal da sensibilidade troca com o sentido. Testes: TC-MMM-006 e TC-ESC-003.

---

### Task 1: Nomes públicos no `equilibrio.py` (reorganização, sem número mudado)

**Files:**
- Modify: `python/equilibrio.py`: `_entrada_limitada` (l. 324), `_fy_eixo_limitado` (l. 355), `_elipse_traseira` (l. 452), `_descolamento` (l. 311)
- Test: `tests/test_equilibrio.py`, `tests/test_equilibrio_linear.py` (sem check novo)

**Interfaces:**
- Produces: `entrada_limitada(caso, rodas, fz, gam) -> tuple[dict, dict, list]`, `fy_eixo_limitado(caso, rodas, fz_u, gam_u, alfa_ref, fatores=None) -> float`, `elipse_traseira(caso, ay_ms2, rodas, fz_u, gam_u) -> tuple[dict | None, str | None]`, `descolamento(fz, rodas) -> str | None`, mais `RODAS_DO_EIXO = _RODAS_DO_EIXO`. Os nomes com `_` ficam como apelidos (`_entrada_limitada = entrada_limitada` etc.), para nenhum chamador mudar.

- [ ] **Step 1:** Renomear as quatro funções para os nomes públicos, deixar os apelidos privados e não mudar nenhum corpo.
- [ ] **Step 2:** `uv run python -X utf8 tests/test_equilibrio.py` → `28 PASS, 0 FAIL, de 28 testes`; `tests/test_equilibrio_linear.py` → `18 PASS, 0 FAIL, de 18 testes`.
- [ ] **Step 3:** Commit `refactor(equilibrio): nomes públicos para a física por roda usada pelo MMM`.

### Task 2: `mmm.py`: hipóteses, cinemática e trim desacoplado

**Files:**
- Create: `python/mmm.py`, `tests/test_mmm.py` (cabeçalho `check()` igual ao de `tests/test_equilibrio.py`, l. 25-44, e o resumo final igual)

**Interfaces:**
- Consumes: Task 1; `equilibrio.cargas`, `camber`, `deriva_total`, `forca_exigida`, `esterco_rodas`, `CANTOS`, `G`; `tire_model.wheel_forces(ds, canto, fz, alpha, gamma, kappa) -> (fx, fy, info)`.
- Produces:
  - `Hipoteses` (frozen): `alfa: Literal["planilha","cinematico"] = "planilha"`, `cos_delta: Literal["ref","trim"] = "ref"`, `sentido: Literal["entrada","dois"] = "entrada"`, `fx_exigido: Literal["edr057","balanco"] = "edr057"`, `tracao: Literal["elipse","pac2002"] = "elipse"`, `diferencial: Literal["aberto","travado"] = "aberto"`, `transf_long: Literal["nao","regime"] = "nao"`, `h_cp_m: float | None = None`. `__post_init__` valida cada valor contra o Literal (ValueError com o campo). Construtores `Hipoteses.planilha()` e `Hipoteses.python_completo()`.
  - `VARIANTES: dict[str, dict]`, campo → `{"hipoteses": (1, 2), "planilha": "planilha", "python": "cinematico", "nome": "1+2"}`, com as linhas da tabela do adendo §3.2 (nomes `1+2`, `3`, `7`, `9a`, `9b`, `10`, `11`).
  - `alfa_rodas(caso, hip, beta_rad, delta_rad, alfa_ref: dict | None = None) -> dict` (canto → α [rad]).
    - `alfa="planilha"`: α_roda = α_ref do eixo + `deriva_total(caso)[c]`, com α_ref do eixo dado em `{"F": .., "R": ..}`.
    - `"cinematico"`: a fórmula exata do adendo §2.1, com x = +a na frente e −b atrás, y = ±t/2 (FL e RL em +t/2), δ_i = δ (mais o Ackermann pela geometria SUS-414 aplicada ao δ do trim: média das dianteiras = δ, interna e externa por `kinematics_model.ackermann_inner_ideal_deg`, no mesmo esquema de bisseção de `equilibrio._esterco_ackermann`, com δ como argumento) e menos `deriva_toe`.
  - `Trim` (frozen): `ay_ms2: float`, `beta_rad`, `delta_rad: float | None`, `alfa`, `fz`, `fy`, `fx`, `kappa: dict | None`, `convergiu: bool`, `residuo_N: float | None`, `motivo: str | None`, `eixo_sem_raiz: str | None`.
  - `trim(caso, hip, ay_ms2, n_alfa: int = 401) -> Trim`. Nesta tarefa só o caminho desacoplado:
    - em cada eixo, α_ref no ramo ascendente da soma (de 0 até o α do pico de `capacidade_eixo(caso, eixo, ay, n_alfa)`) por Brent, com Fy_eixo(α_ref) = força exigida;
    - β = α_R,ref + b/R; δ = β + a/R − α_F,ref.
    
    Variante acoplada pedida → `NotImplementedError("Task 4")`.
  - `cn(trim, caso) -> tuple[float, float]` = `(cn_iso, cn_estabilizante)`, com N = Σ(x_i·Fy_i − y_i·Fx_i) e cn_estabilizante = −cn_iso (curva à esquerda).
  - O `mmm.py` importa `wheel_forces` como nome do módulo (`from tire_model import wheel_forces`), para o teste do pneu de brinquedo (Task 3) poder substituí-lo.

- [ ] **Step 1:** Escrever TC-MMM-001, TC-MMM-007 (só a parte de resíduo, A_Y acima do limite e sem raio) e TC-MMM-011. Rodar `uv run python -X utf8 tests/test_mmm.py` → falha (módulo ausente).
- [ ] **Step 2:** Implementar `Hipoteses`, `VARIANTES`, `alfa_rodas`, `Trim`, `trim` desacoplado e `cn`. Brent em stdlib (escrever `_brent(f, a, b, tol)` em `mmm.py`; sem scipy, que o projeto não usa).
- [ ] **Step 3:** `tests/test_mmm.py` → `3 PASS, 0 FAIL, de 3 testes`.
- [ ] **Step 4:** Commit `feat(mmm): hipóteses como variantes, cinemática por roda e trim desacoplado`.

### Task 3: `mmm.py`: limite, Q, P, K e stability index

**Files:**
- Modify: `python/mmm.py`, `tests/test_mmm.py`

**Interfaces:**
- Consumes: Task 2; `equilibrio.analise_par` (só para o intervalo inicial da bisseção), `equilibrio.PUSH/LOOSE/NEUTRO/NA`, `equilibrio_linear.parcelas_k` (só no teste).
- Produces:
  - `Limite` (frozen): `ay_t_ms2: float | None`, `ay_sat_f`, `ay_sat_r: float | None`, `motivo_sat: str | None`, `eixo_satura: str | None` ("F" ou "R"), `veredito: str`, `cn_iso_q`, `cn_estabilizante_q`, `cn_p: float | None`, `stability_index: float | None` (por m/s²), `k_rad_por_ms2: float | None` (em 0,05·G), `resolucao_ms2: float`, `motivo: str | None`, `limitacoes: tuple[str, ...]`.
  - `limite(caso, hip, resolucao_ms2: float = 0.01, ay_max_g: float = 2.0) -> Limite`:
    - bisseção em A_Y sobre `trim(...).convergiu`, com o intervalo inicial tirado de `analise_par(caso)` (ou [0, ay_max]);
    - veredito pela decisão 3;
    - Q = folga do outro eixo em T;
    - P = (a·Fy_f,max − b·Fy_r,max)/(W·L) no A_Y_P que satisfaz m·A_P = Fy_f,max(A_P) + Fy_r,max(A_P) (ponto fixo com bisseção), com as capacidades de `capacidade_eixo`;
    - descolamento e toe → `NA` com o motivo de `capacidade_eixo` (Review Focus 2 e 3).
  - `k_trim(caso, hip, ay_ms2) -> float`: dδ/dA_Y por diferença central (passo 0,01·G) na curva de trim.
  - `stability_index(caso, hip, ay_ms2) -> float`: no trim (β*, δ*) daquele A_Y, β* ± h com δ* fixo, A_Y de cada lado pelo trim lateral (ΣFy = m·A_Y, Brent), SI = ΔC_N/ΔA_Y. Usa o `ponto` da Task 5: nesta tarefa, escrever o `_trim_lateral(caso, hip, beta, delta)` privado que a Task 5 publica como `ponto`.

- [ ] **Step 1:** Escrever TC-MMM-002 (pneu de brinquedo: o `ds` real do `.tir`, para `grade_alfa` ter ALPMIN e ALPMAX, com `mmm.wheel_forces` e `equilibrio.wheel_forces` trocados dentro do teste por `lambda ds, c, fz, a, g, k: (0.0, μ·fz·math.tanh(−a/α0), {})`, μ = 1,5 e α0 = 0,1 rad, rotulados "brinquedo de teste", e restaurados no fim), TC-MMM-004, TC-MMM-005, TC-MMM-006 e as partes de Review Focus 2 e 3 no TC-MMM-007. No TC-MMM-002 e no 005, o SI troca de sinal entre um carro com rigidez de eixo maior na frente e outro com ela maior atrás, e fica ≈ 0 no simétrico. Rodar → falham.
- [ ] **Step 2:** Implementar `Limite`, `limite`, `k_trim`, `stability_index`.
- [ ] **Step 3:** `tests/test_mmm.py` → `7 PASS, 0 FAIL, de 7 testes`. Se o TC-MMM-004 passar de 1e-2, parar e reportar (decisão 6).
- [ ] **Step 4:** Commit `feat(mmm): limite em trim, Q, P, K e stability index`.

### Task 4: `mmm.py`: variantes acopladas

**Files:**
- Modify: `python/mmm.py`, `tests/test_mmm.py`

**Interfaces:**
- Consumes: Tasks 2-3; `tire_model.wheel_forces` com κ ≠ 0; `equilibrio.fx_exigido_traseira`, `equilibrio.elipse_traseira`, `equilibrio.entrada_limitada`.
- Produces: `trim` aceita todas as variantes. O caminho acoplado é Newton 2-D em (β, δ) com jacobiano por diferença finita (passo 1e-6 rad), a partir do trim desacoplado da variante planilha, com passo limitado a 0,5° por iteração e no máximo 50 iterações. Sai do ramo ascendente de algum eixo ou não converge → `convergiu=False` com motivo. Física por variante:
  - `cos_delta="trim"`: força do eixo dianteiro nos eixos do carro = Σ(Fy·cos δ_i + Fx·sen δ_i);
  - `fx_exigido="balanco"`: Fx_r = D + RR + F_yf,pneu·sen δ − m·A·sen β (adendo §2.5), com D e RR dos campos `cda_m2`, `rho_kg_m3` e `crr` (`None` = termo fora, como em `fx_exigido_traseira`);
  - `tracao="pac2002"`: κ de cada roda traseira por Brent em [0, KPUMAX] com `wheel_forces(...)[0]` = Fx da roda (aberto: Fx_r/2 em cada; sem raiz → "tração excede o atrito longitudinal em <canto>");
  - `diferencial="travado"`: ω comum, raio de rolamento igual nos dois lados; κ_i = (ω·R_e − V_x,i)/V_x,i, com V_x,i = V·cos β − r·y_i; ω·R_e resolvido para ΣFx = Fx_r. Fx_i entra no N;
  - `transf_long="regime"`: ΔFz_traseira = (m·a_x·h + D·h_cp)/L com a_x = −A·sen β, a parcela de h_cp só com `h_cp_m` não None, repartida igual entre as rodas do eixo e somada às `cargas`;
  - `alfa="cinematico"`: `alfa_rodas` exato (Task 2) com o δ do trim.
  - `sentido="dois"` não muda o trim: é tratado em `escada` (Task 6).

- [ ] **Step 1:** Escrever TC-MMM-008 e TC-MMM-009. Acrescentar ao TC-MMM-007: com `Hipoteses.python_completo()` no caso base de teste (com `cda_m2`, `crr`, `rho_kg_m3` e R = 8,5 m, rotulados "sintético de teste"), o trim em 0,5·T converge com os resíduos da Task 2. Rodar → falham.
- [ ] **Step 2:** Implementar.
- [ ] **Step 3:** `tests/test_mmm.py` → `9 PASS, 0 FAIL, de 9 testes`.
- [ ] **Step 4:** Commit `feat(mmm): variantes acopladas (cinemática, cos δ, balanço, PAC2002, travado, transferência)`.

### Task 5: `mmm.py`: ponto, diagrama e sensibilidade

**Files:**
- Modify: `python/mmm.py`, `tests/test_mmm.py`

**Interfaces:**
- Consumes: Tasks 2-4.
- Produces:
  - `PontoMMM` (frozen): `beta_rad`, `delta_rad`, `ay_ms2: float | None`, `cn_iso: float | None`, `n_raizes: int`, `motivo: str | None`.
  - `ponto(caso, hip, beta_rad, delta_rad) -> PontoMMM`: ΣFy(A_Y) − m·A_Y = 0 em [0, A_desc]. A_desc é o primeiro A_Y com Fz ≤ 0 (varredura de 0 a 3·G em 61 passos, que também conta as trocas de sinal). A raiz devolvida é a menor, e a docstring diz isso.
  - `diagrama(caso, hip, betas, deltas) -> list[PontoMMM]`: rótulo "raio fixo com trim lateral (V = √(A_Y·R))".
  - `UNIDADES = {"ganho_camber_F": "por 0,1 °/°", "ganho_camber_R": "por 0,1 °/°", "rc_F": "por 10 mm", "rc_R": "por 10 mm", "kphi_F": "por 1 kN·m/rad", "kphi_R": "por 1 kN·m/rad", "h_cg": "por 10 mm", "cg_lateral": "por 10 mm", "h_cp": "por 10 mm"}` com os passos `{0.1, 0.1, 0.010, 0.010, 1000.0, 1000.0, 0.010, 0.010, 0.010}` na unidade SI do campo (`ganho_camber` em rad/rad nas duas rodas do eixo; `cfg.roll_center_front/rear`; `cfg.roll_stiffness_front/rear`; `cfg.cg_height`; `cg_lateral_m`; `h_cp_m`).
  - `sensibilidade(caso, hip, parametro) -> dict` com as chaves `parametro`, `unidade`, `d_ay_t`, `d_cn_estabilizante_q`, `d_k`, `veredito_menos`, `veredito_mais`, `motivo`, por diferença central de ± um passo.
    - `h_cp` exige `transf_long="regime"` (senão `motivo` = "h_cp só com transf_long=regime").
    - `cg_lateral` parte do valor do caso.

- [ ] **Step 1:** Escrever TC-MMM-003 e TC-MMM-010. Rodar → falham.
- [ ] **Step 2:** Implementar. O `stability_index` da Task 3 passa a usar `ponto`.
- [ ] **Step 3:** `tests/test_mmm.py` → `11 PASS, 0 FAIL, de 11 testes`; `tests/test_equilibrio.py` 28/28.
- [ ] **Step 4:** Commit `feat(mmm): ponto, diagrama de raio fixo e sensibilidades por unidade`.

### Task 6: `escada.py` e `tests/test_escada.py`

**Files:**
- Create: `python/escada.py`, `tests/test_escada.py`

**Interfaces:**
- Consumes: `mmm.Hipoteses`, `VARIANTES`, `limite`, `sensibilidade`, `UNIDADES`; `equilibrio.analise_par`, `espelhar`.
- Produces:
  - `ComparacaoDegrau1` (frozen): `sentido`, `veredito_mmm`, `veredito_par`, `d_ay_sat_f`, `d_ay_sat_r`, `cn_mmm`, `cn_par`, `resolucao_ms2`, `ok: bool`, `motivo`.
  - `degrau_1(caso) -> tuple[ComparacaoDegrau1, ComparacaoDegrau1]` (esquerda, direita via `espelhar`).
  - `LinhaEscada` (frozen): `nome` (de `VARIANTES[...]["nome"]`, mais `planilha` e `todas`), `hipoteses: tuple[int, ...]`, `limite: mmm.Limite`, `pior_sentido: str | None` (só na linha `7`), `d_ay_t`, `d_cn_estabilizante_q`, `d_k: float | None`, `inverte: str`.
  - `degrau_2(caso) -> tuple[LinhaEscada, ...]`: planilha, uma variante por vez (a `7` roda os dois sentidos e guarda o pior: menor T, com N/A contando como pior, como `equilibrio._chave_pior`), `10+9b` e `todas`.
  - `sensibilidades(caso) -> tuple[dict, ...]`: uma por chave de `UNIDADES`, com `hip = Hipoteses.planilha()` e, para `h_cp`, `transf_long="regime"`.
  - Nenhuma função decide "dentro da tolerância": não existe parâmetro de tolerância (EDR-065 pendente).

- [ ] **Step 1:** Escrever TC-ESC-001 a 003, com os casos montados como em `tests/test_equilibrio.py` (`veiculo_base`, R = 8,5 m "sintético de teste"). Rodar → falham.
- [ ] **Step 2:** Implementar.
- [ ] **Step 3:** `tests/test_escada.py` → `3 PASS, 0 FAIL, de 3 testes`; `tests/test_mmm.py` 11/11.
- [ ] **Step 4:** Commit `feat(escada): degraus 1 e 2 e sensibilidades, sem veredito de tolerância`.

### Task 7: Relatório da escada e conferência do `.tir` combinado (controlador)

**Files:**
- Create: `tools/relatorio_escada.py`, `docs/inc6/escada-hipoteses.md`

**Interfaces:**
- Consumes: `escada.degrau_1/degrau_2/sensibilidades`; `caso_planilha.caso_da_planilha_v41(xlsx_recalculado, tir, passo1=False)` e `pior_origem_do_caso_v41`; recálculo de cópia como em `tools/relatorio_inc4.py`.
- Produces: `uv run python -X utf8 tools/relatorio_escada.py [--raio R --origem-raio TEXTO] [--sobrescrever]`.
  - Lê `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx` numa cópia recalculada e monta o caso.
  - Sem R no caso nem `--raio`: sai com código 3 e "informe --raio".
  - Com `--raio`: aplica o valor só ao caso do relatório e escreve no topo `R = <valor> m (origem: <texto>)`.
  - O relatório traz: tabelas do degrau 1, do degrau 2 e das sensibilidades; pior origem; "geometria sintética"; "sem veredito: tolerância pendente (EDR-065)"; os achados do adendo §7 com os números medidos nas linhas `1+2` e `9a`; e a nota do `.tir` (passo 1).

- [ ] **Step 1:** Conferir a origem dos coeficientes combinados do `.tir` (`REX1`, `RBY*`, `RCY1`, `RVY*`, `RBX*`, `RCX1` em `data/Hoosier_R25B_13x7_TTC_provisional.tir` e o `.meta.json` ao lado) contra os valores padrão do help do Adams (`references/pdf/Adams_2024_1_PAC2002_help.pdf`; usar o `.md` convertido se houver, conferindo na imagem). Escrever a conclusão em uma frase no relatório ("ajustados ao TTC" / "valores padrão do formato" / "não determinado"), com a fonte.
- [ ] **Step 2:** Implementar a ferramenta. Rodar sem `--raio` → código 3 (Review Focus 1).
- [ ] **Step 3:** Pedir ao usuário o R e a origem (autorização 3). Com a resposta, rodar `--raio ... --origem-raio ... --sobrescrever` e passar o texto do relatório pelo `humanizer-pt`. Sem resposta, o relatório fica para depois e a Task 9 registra isso.
- [ ] **Step 4:** Commit `feat(tools): relatório da escada de hipóteses` (e, se gerado, `docs(inc6): relatório da escada com R informado pelo usuário`, em commit separado).

### Task 8: Mutação do MMM

**Files:**
- Create: `tests/mutation_mmm.py` (padrão de `tests/mutation_equilibrio.py`: aplica o mutante no texto do módulo em memória, roda `test_mmm.py` e `test_escada.py` num subprocesso e espera FAIL)

**Interfaces:**
- Mutantes (cada um precisa ser pego):
  1. sinal do termo a/R em `alfa_rodas`;
  2. b/R no lugar de a/R;
  3. `cn_estabilizante = +cn_iso`;
  4. retirada do −m·A·sen β no `fx_exigido="balanco"`;
  5. δ_ref = L/R no lugar do δ do trim em `cos_delta="trim"`.

- [ ] **Step 1:** Escrever e rodar `uv run python -X utf8 tests/mutation_mmm.py` → `5/5 mutantes mortos`. Um mutante vivo: parar e reportar qual TC devia pegá-lo (não enfraquecer o mutante).
- [ ] **Step 2:** Commit `test(mmm): mutação dos termos novos (5/5)`.

### Task 9: EDRs, documentação, suíte e PR (controlador)

**Files:**
- Modify:
  - `docs/Engineering_Decision_Register.md` (EDR-064, 065 PROPOSED, 066; índice);
  - adendo (A1 pela decisão 1; §4.3, hipótese 12, pela decisão 4; §3.3, o rótulo de origem fica no relatório e não nos `dataclass`, pelo Global Constraint);
  - spec base §7.5 (nota: as chaves h2-h9 já existem, e as variantes Python não vão para a planilha);
  - `CLAUDE.md` (Situação atual: incremento 6; Comandos: contagens `test_mmm` 11, `test_escada` 3, mutação 5/5);
  - `tools/rodar_testes.py` (entradas de `test_mmm.py`, `test_escada.py` e `MUTACAO += ("tests/mutation_mmm.py", 5)`);
  - `MAPA.md` (regenerar com `--sobrescrever`).

- [ ] **Step 1:** Escrever os EDRs e as notas e passar o texto em português pelo `humanizer-pt`. Commit `docs: EDR-064 a 066, adendo e contagens do incremento 6`.
- [ ] **Step 2:** Suíte inteira em segundo plano: `uv run python -X utf8 tools/rodar_testes.py` → todos os itens do resumo PASS, com as contagens novas.
- [ ] **Step 3:** Revisão final (Opus, um despacho) sobre `main...HEAD`; correções; commit.
- [ ] **Step 4:** Push e PR (`gh pr create`) depois da confirmação do usuário. O merge fica com o usuário.
