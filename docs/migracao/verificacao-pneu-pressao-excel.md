# Verificação da V3.0 nesta máquina

Gerado por `tools/rodar_testes.py`. Não edite à mão: rode de novo.

## Ambiente (CA-10)

- Data: 2026-11-11T11:42:32
- Commit: `0b421df`
- Sistema: Windows-11-10.0.26300-SP0
- Python: 3.13.17 (C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\.venv\Scripts\python.exe)
- numpy 2.5.4, scipy 1.18.1, openpyxl 3.1.5 (fixados no `uv.lock`)
- Execução: `sys.executable -X utf8 <script>`, cwd=raiz do repositório, `PYTHONUTF8=1`
- Módulos importados de (PASS): `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\tire_model.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\tire_model_static.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\suspension_model.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\kinematics_model.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\hardpoints.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\atualizar_planilha.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\equilibrio.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\equilibrio_linear.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\caso_planilha.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\nomes_v4_0.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\gerar_v4_0.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\dados_planilha.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\aba_equilibrio.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\gerar_v4_1.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\origens.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\gerar_v4_2.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\metas.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\aba_metas.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\viva.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\mmm.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\escada.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\executor_testes.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\skidpad.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\aba_curva.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\gerar_v4_3.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\estudo_neutro.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\reescrita_nomes.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\nomes_v4_4.py`, `C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\python\gerar_v4_4.py`

## Resumo

| CA | Item | Status |
|---|---|---|
| CA-10 | módulos importados de python/ | **PASS** |
| CA-05 | pneu | **PASS** |
| CA-05 | oráculos | **PASS** |
| CA-05 | pneu estático | **PASS** |
| CA-05 | pneu com pressão | **PASS** |
| CA-05 | suspensão | **PASS** |
| CA-05 | cinemática | **PASS** |
| CA-05 | hardpoints | **PASS** |
| CA-05 | equilíbrio | **PASS** |
| CA-05 | equilíbrio linear | **PASS** |
| CA-05 | V4.0 (nomes e dados) | **PASS** |
| CA-05 | V4.1 (estrutura e CA-07) | **PASS** |
| CA-05 | V4.2 (estrutura, CA-07, oráculo das metas e fluxo da viva) | **PASS** |
| CA-05 | MMM em raio fixo | **PASS** |
| CA-05 | escada de hipóteses | **PASS** |
| CA-05 | executor dos testes | **PASS** |
| CA-05 | raio do skidpad | **PASS** |
| CA-05 | formas v43 | **PASS** |
| CA-05 | estudo do NEUTRO | **PASS** |
| CA-05 | V4.3 (estrutura, CA-07, migração e verificações) | **PASS** |
| CA-05 | V4.4 (regeneração, regra, invariante e migração) | **PASS** |
| CA-06 | mutação (mutation_tire.py) | **PASS** |
| CA-06 | mutação (mutation_equilibrio.py) | **PASS** |
| CA-06 | mutação (mutation_planilha_equilibrio.py) | **PASS** |
| CA-06 | mutação (mutation_mmm.py) | **PASS** |
| CA-06 | mutação (mutation_inc7.py) | **PASS** |
| CA-06 | mutação (mutation_planilha_v43.py) | **PASS** |
| CA-06 | mutação (mutation_planilha_v44.py) | **PASS** |
| CA-07 | autoteste do comparador | **PASS** |
| CA-07 | planilha vs V2.4 entregue | **PASS** |
| CA-08 | layout vs entregue | **PASS** |
| CA-07 | planilha vs V3.0 de referência | **PASS** |
| CA-07 | planilha vs V4.0 de referência (com nomes definidos) | **PASS** |
| CA-07 | planilha vs V4.1 de referência (equilíbrio em fórmulas) | **PASS** |
| CA-07 | V3.0 de excel/ = arquivo da tag v3.0 (SHA-256) | **PASS** |
| CA-07 | planilha vs V4.2 de referência (metas e coerência) | **PASS** |
| CA-07 | planilha vs V4.3 de referência (centro da curva, R e arrasto induzido) | **PASS** |
| CA-07 | planilha vs V4.4 de referência (fórmulas por nome) | **PASS** |
| versão | 00_README!A3 = versão no nome do arquivo | **PASS** |
| CA-09 | planilha Excel x Python (test_workbook) | **PASS** |
| CA-09 | planilha Excel x Python (test_workbook_suspensao) | **PASS** |
| CA-09 | planilha Excel x Python (test_workbook_v4_0) | **PASS** |
| CA-09 | planilha Excel x Python (test_workbook_v4_1) | **FAIL** |
| CA-09 | planilha Excel x Python (test_workbook_v4_2) | **PASS** |
| CA-09 | planilha Excel x Python (test_workbook_v4_3) | **PASS** |
| CA-09 | planilha Excel x Python (test_workbook_v4_4) | **PASS** |

## Testes (CA-05)

| Conjunto | Script | Esperado | Obtido | Código | Status | Fonte do esperado |
|---|---|---|---|---|---|---|
| pneu | `tests/test_tire_model.py` | 43 | 43 PASS, 0 FAIL, de 43 | 0 | **PASS** | registro-de-versoes-V2_4.md:16 |
| oráculos | `tests/test_tire_oracles.py` | 5 | 5 PASS, 0 FAIL, de 5 | 0 | **PASS** | registro-de-versoes-V2_4.md:16 |
| pneu estático | `tests/test_tire_static.py` | 87 | 87 PASS, 0 FAIL, de 87 | 0 | **PASS** | EDR-067; PR #25 (precisa dos .tir do TTC Round 6, fora do Git) |
| pneu com pressão | `tests/test_tire_pressure.py` | 109 | 109 PASS, 0 FAIL, de 109 | 0 | **PASS** | EDR-071 (precisa dos .tir do TTC Round 6, fora do Git) |
| suspensão | `tests/test_suspension_model.py` | 54 | 54 PASS, 0 FAIL, de 54 | 0 | **PASS** | registro-de-versoes-V3_0.md |
| cinemática | `tests/test_kinematics_model.py` | 76 | 76 PASS, 0 FAIL, de 76 | 0 | **PASS** | registro-de-versoes-V3_0.md; plano do incremento 2 da V4.0 |
| hardpoints | `tests/test_hardpoints.py` | 35 | 35 PASS, 0 FAIL, de 35 | 0 | **PASS** | HANDOFF §6.2 |
| equilíbrio | `tests/test_equilibrio.py` | 28 | 28 PASS, 0 FAIL, de 28 | 0 | **PASS** | planos dos incrementos 1 e 2 da V4.0 |
| equilíbrio linear | `tests/test_equilibrio_linear.py` | 18 | 18 PASS, 0 FAIL, de 18 | 0 | **PASS** | plano do incremento 2 da V4.0 |
| V4.0 (nomes e dados) | `tests/test_v4_0.py` | 4 | 4 PASS, 0 FAIL, de 4 | 0 | **PASS** | plano do incremento 3 da V4.0 |
| V4.1 (estrutura e CA-07) | `tests/test_v4_1.py` | 2 | 2 PASS, 0 FAIL, de 2 | 0 | **PASS** | plano do incremento 4 da V4.1 (TC-WB41-001 e 002) |
| V4.2 (estrutura, CA-07, oráculo das metas e fluxo da viva) | `tests/test_v4_2.py` | 4 | 4 PASS, 0 FAIL, de 4 | 0 | **PASS** | plano do incremento 5 da V4.2 (TC-WB42-001 a 004) |
| MMM em raio fixo | `tests/test_mmm.py` | 11 | 11 PASS, 0 FAIL, de 11 | 0 | **PASS** | plano do incremento 6 (TC-MMM-001 a 011) |
| escada de hipóteses | `tests/test_escada.py` | 3 | 3 PASS, 0 FAIL, de 3 | 0 | **PASS** | plano do incremento 6 (TC-ESC-001 a 003) |
| executor dos testes | `tests/test_executor.py` | 1 | 1 PASS, 0 FAIL, de 1 | 0 | **PASS** | plano do inc. 7 (TC-RUN-001) |
| raio do skidpad | `tests/test_skidpad.py` | 2 | 2 PASS, 0 FAIL, de 2 | 0 | **PASS** | plano do inc. 7 (TC-SKP-001 e 002) |
| formas v43 | `tests/test_formas_v43.py` | 4 | 4 PASS, 0 FAIL, de 4 | 0 | **PASS** | plano do inc. 7 (TC-ACK-001, TC-FXI-001 e 002, TC-ACK-002) |
| estudo do NEUTRO | `tests/test_neutro.py` | 2 | 2 PASS, 0 FAIL, de 2 | 0 | **PASS** | plano do inc. 7 (TC-NEU-001 e 002) |
| V4.3 (estrutura, CA-07, migração e verificações) | `tests/test_v4_3.py` | 3 | 3 PASS, 0 FAIL, de 3 | 0 | **PASS** | plano do inc. 7 (TC-WB43-001, 002 e 006) |
| V4.4 (regeneração, regra, invariante e migração) | `tests/test_v4_4.py` | 4 | 4 PASS, 0 FAIL, de 4 | 0 | **PASS** | plano do inc. 8 (TC-WB44-001 a 004) |

<details><summary>tests/test_tire_model.py: stderr (final)</summary>

```text
[executor] início 11:42:32, fim 11:42:33, 0.3 s
```

</details>

<details><summary>tests/test_tire_oracles.py: stderr (final)</summary>

```text
[executor] início 11:42:33, fim 11:42:33, 0.5 s
```

</details>

<details><summary>tests/test_tire_static.py: stderr (final)</summary>

```text
[executor] início 11:42:33, fim 11:42:35, 1.7 s
```

</details>

<details><summary>tests/test_tire_pressure.py: stderr (final)</summary>

```text
[executor] início 11:42:35, fim 11:42:58, 23.6 s
```

</details>

<details><summary>tests/test_suspension_model.py: stderr (final)</summary>

```text
[executor] início 11:42:58, fim 11:42:59, 0.4 s
```

</details>

<details><summary>tests/test_kinematics_model.py: stderr (final)</summary>

```text
[executor] início 11:42:59, fim 11:43:02, 2.7 s
```

</details>

<details><summary>tests/test_hardpoints.py: stderr (final)</summary>

```text
[executor] início 11:43:02, fim 11:43:02, 0.5 s
```

</details>

<details><summary>tests/test_equilibrio.py: stderr (final)</summary>

```text
[executor] início 11:43:02, fim 11:43:13, 11.2 s
```

</details>

<details><summary>tests/test_equilibrio_linear.py: stderr (final)</summary>

```text
[executor] início 11:43:13, fim 11:43:16, 2.8 s
```

</details>

<details><summary>tests/test_v4_0.py: stderr (final)</summary>

```text
[executor] início 11:43:16, fim 11:43:32, 16.0 s
```

</details>

<details><summary>tests/test_v4_1.py: stderr (final)</summary>

```text
[executor] início 11:43:32, fim 11:43:55, 23.3 s
```

</details>

<details><summary>tests/test_v4_2.py: stderr (final)</summary>

```text
viva com 1 célula(s) alterada(s) fora dos nomes de dado (ent/org/fte): 01_SETUP!A1
viva com comentários, hiperlinks, imagens ou gráficos diferentes da referência (1): 00_README!Z99 (comentário). Estes objetos não são migrados por esta ferramenta: leve-os à mão ou obtenha aprovação para deixá-los de fora.
viva não lida: viva de 0 byte (placeholder do Drive 'só online' ou arquivo vazio): C:\Users\vferr\AppData\Local\Temp\dds_v42_02gytl0y\viva_t\zero\FSAE_EV_Suspension_Fase1_V4_1.xlsx
viva não lida: viva ausente ou inacessível (C:\Users\vferr\AppData\Local\Temp\dds_v42_02gytl0y\viva_t\ausente\FSAE_EV_Suspension_Fase1_V4_1.xlsx): [WinError 3] O sistema não pode encontrar o caminho especificado: 'C:\\Users\\vferr\\AppData\\Local\\Temp\\dds_v42_02gytl0y\\viva_t\\ausente\\FSAE_EV_Suspension_Fase1_V4_1.xlsx'
a viva é da versão V4.2, mais nova que o destino (V4.1): migrar para trás perderia dados; use como destino a versão da viva ou uma mais nova
erro de dado na migração: valores com fórmula não são migrados como dado: ['ent_05_altura_do_cg_total']
saída em excel/ recusada (C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\excel\_migrar_teste.xlsx): a cópia para excel/ é um commit próprio
saída por cima de um arquivo de entrada: recusado (C:\Users\vferr\AppData\Local\Temp\dds_v42_02gytl0y\viva_t\fiel\FSAE_EV_Suspension_Fase1_V4_1.xlsx)
saída por cima de um arquivo de entrada: recusado (C:\Users\vferr\AppData\Local\Temp\dds_v42_02gytl0y\V4_2.xlsx)
relatório em excel/ recusada (C:\Users\vferr\Documents\Sistema_DDS\.claude\worktrees\elegant-tesla-cfe8e8\excel\_relatorio_teste.md): a cópia para excel/ é um commit próprio
saída na pasta do Drive recusada (H:\.shortcut-targets-by-id\1Kytf4APy0OtH5Aq5PqlOwH5UY65YMX5U\T11 - Tupã\2. Projeto\Mecanica\Suspensao\Documentacao\Planilha DDS\FSAE_EV_Suspension_Fase1_V4_2.xlsx): a viva do Drive é só leitura
relatório na pasta do Drive recusada (H:\.shortcut-targets-by-id\1Kytf4APy0OtH5Aq5PqlOwH5UY65YMX5U\T11 - Tupã\2. Projeto\Mecanica\Suspensao\Documentacao\Planilha DDS\relatorio.md): a viva do Drive é só leitura
recusado: o relatório deve ser .md e a saída .xlsx (C:\Users\vferr\AppData\Local\Temp\dds_v42_02gytl0y\viva_t\r7.md, C:\Users\vferr\AppData\Local\Temp\dds_v42_02gytl0y\viva_t\s7.txt)
destino (--para) na pasta do Drive recusado (H:\.shortcut-targets-by-id\1Kytf4APy0OtH5Aq5PqlOwH5UY65YMX5U\T11 - Tupã\2. Projeto\Mecanica\Suspensao\Documentacao\Planilha DDS\FSAE_EV_Suspension_Fase1_V4_2.xlsx): a viva do Drive é só leitura, e a cópia de destino sai da referência
[executor] início 11:43:55, fim 11:52:09, 493.7 s
```

</details>

<details><summary>tests/test_mmm.py: stderr (final)</summary>

```text
[executor] início 11:52:09, fim 11:53:17, 68.4 s
```

</details>

<details><summary>tests/test_escada.py: stderr (final)</summary>

```text
[executor] início 11:53:17, fim 12:06:35, 797.7 s
```

</details>

<details><summary>tests/test_executor.py: stderr (final)</summary>

```text
[executor] início 12:06:35, fim 12:06:57, 22.2 s
```

</details>

<details><summary>tests/test_skidpad.py: stderr (final)</summary>

```text
[executor] início 12:06:57, fim 12:06:58, 0.5 s
```

</details>

<details><summary>tests/test_formas_v43.py: stderr (final)</summary>

```text
[executor] início 12:06:58, fim 12:15:01, 483.4 s
```

</details>

<details><summary>tests/test_neutro.py: stderr (final)</summary>

```text
[executor] início 12:15:01, fim 12:15:55, 54.1 s
```

</details>

<details><summary>tests/test_v4_3.py: stderr (final)</summary>

```text
viva com 1 célula(s) alterada(s) fora dos nomes de dado (ent/org/fte): 16_EQUILIBRIO!B9
viva com 1 célula(s) alterada(s) fora dos nomes de dado (ent/org/fte): 16_EQUILIBRIO!E9
[executor] início 12:15:55, fim 12:24:06, 490.6 s
```

</details>

<details><summary>tests/test_v4_4.py: stderr (final)</summary>

```text
[executor] início 12:24:06, fim 12:26:19, 132.8 s
```

</details>

## Mutação (CA-06)

### `tests/mutation_tire.py`

- Esperado: 25/25 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> 43 PASS, 0 FAIL, de 43 testes
- Obtido: 25/25 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_tire.py: saída</summary>

```text
PRE-CHECAGEM OK: original -> 43 PASS, 0 FAIL, de 43 testes
DETECTADO      Ex sinal PEX4
DETECTADO      Ky PKY2*fz
DETECTADO      Bx sem Cx
DETECTADO      SVx sem LMUX
DETECTADO      Gxa sem denominador
DETECTADO      Gyk sem denominador
DETECTADO      SVyk RVY5 sinal
DETECTADO      espelho esquerdo Fy
DETECTADO      faixa Fz
DETECTADO      camber PDY3
DETECTADO      mu_eff
DETECTADO      Ey sem min/sinal
DETECTADO      LKY ignorado
DETECTADO      LFZO extra em Ky (forma Racer, EDR-049)
DETECTADO      PHY3 camber
DETECTADO      LKYG ignorado em SHy
DETECTADO      RVY3 camber
DETECTADO      kappa-range
DETECTADO      s_F removido (Fy sem inverter)
DETECTADO      s_alpha removido
DETECTADO      s_gamma removido
DETECTADO      SAE com sinais ISO
DETECTADO      espelho depois da transformacao
DETECTADO      loader aceita eixo None
DETECTADO      gamma SAE so s_g=+1
25 / 25
```

</details>

<details><summary>tests/mutation_tire.py: stderr (final)</summary>

```text
[executor] início 12:26:19, fim 12:26:26, 7.7 s
```

</details>

### `tests/mutation_equilibrio.py`

- Esperado: 6/6 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> test_equilibrio.py: 28 PASS, 0 FAIL, de 28 testes | test_equilibrio_linear.py: 18 PASS, 0 FAIL, de 18 testes
- Obtido: 6/6 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_equilibrio.py: saída</summary>

```text
PRE-CHECAGEM OK: original -> test_equilibrio.py: 28 PASS, 0 FAIL, de 28 testes | test_equilibrio_linear.py: 18 PASS, 0 FAIL, de 18 testes
DETECTADO      forca_exigida com a e b trocados -> [FAIL] TC-EQ-009: forca_exigida = (m·a_y·b/L, m·a_y·a/L) com a != b; [FAIL] TC-EQ-042: simétrico com y_cg = 0 -> esquerda == direita (ResultadoPar inteiro) e espelhar(caso) == caso; y_cg = +0,02 m (só de teste) -> soma estática igual, esquerda ganha W_eixo·y/t por eixo, cargas(a_y=0) = estática deslocada; dois sentidos (LMUY 0,45) -> pior = direita; tabela_linear: y_cg = −0,02 m -> 1ª linha com k_inclinacao numérico, y_cg = 0 -> 1ª linha igual à de antes; [FAIL] TC-EQ-045: Crr = 0,015, CdA = 1,0 m² (só de teste) -> capacidade traseira = máx_α Σ Fy_c·√(1 − (Fx/Fx_max,c)²) (erro rel < 1e-9), Fx = 0,5·ρ·CdA·a_y·R + Crr·m·G + F_yf·tan δ_ref dividido igual entre RL e RR; frente igual; Fx_max fechado = máximo numérico em [0, KPUMAX] e, com o pico fora da faixa, o numérico; [FAIL] TC-EQ-034: k_inclinacao da 1ª linha (passo 2, Richardson das secantes de 0,005 e 0,01 g) = k_pneus + k_deslocamento + k_camber (passo 1), rel < 1e-3, com e sem ganho de camber, também com toe dianteiro 0,25°, R = 8,0 m e R = 8,0 m com Ackermann 100 %, e com a aerodinâmica da h8 (R 8 m, ρ 1,2, CzA 2,0) somada a toe, camber estático e CG lateral (derivada de um lado em a_y = 0), e com FORMAS_V43 (Ackermann 100 %, R 8 m) (veículo e entradas de teste, .tir real, sem roll steer: o passo 2 não tem roll steer)
DETECTADO      sem cos δ na dianteira -> [FAIL] TC-EQ-040: R = 8 m sem Ackermann -> capacidade dianteira × cos(L/R) (erro < 1e-12); traseira igual; [FAIL] TC-EQ-046: tração (Crr 0,015, CdA 1,0, R 8 m; só de teste) -> S_r e C_N caem (rumo a loose), S_f e capacidades dianteiras iguais, veredito segue PUSH neste caso; só Crr (sem R) -> queda de S_r abaixo da resolução, segue NEUTRO
DETECTADO      Ackermann com sinal invertido -> [FAIL] TC-EQ-041: Ackermann 0 % -> δ = δ_ref e Δα extra nulo; 100 % -> δ_i = ideal (1e-9), média δ_ref, Δα de FL e FR com sinais opostos
DETECTADO      ganho de camber com sinal invertido -> [FAIL] TC-EQ-003: camber = estático + ganho·φ (φ de lateral_dfz); toe_rad com cantos faltando -> ValueError; [FAIL] TC-EQ-034: k_inclinacao da 1ª linha (passo 2, Richardson das secantes de 0,005 e 0,01 g) = k_pneus + k_deslocamento + k_camber (passo 1), rel < 1e-3, com e sem ganho de camber, também com toe dianteiro 0,25°, R = 8,0 m e R = 8,0 m com Ackermann 100 %, e com a aerodinâmica da h8 (R 8 m, ρ 1,2, CzA 2,0) somada a toe, camber estático e CG lateral (derivada de um lado em a_y = 0), e com FORMAS_V43 (Ackermann 100 %, R 8 m) (veículo e entradas de teste, .tir real, sem roll steer: o passo 2 não tem roll steer)
DETECTADO      NEUTRO pelo passo de exibição (regra anterior ao EDR-056) -> [FAIL] TC-EQ-011: lambda_f = 0,7 -> PUSH; lambda_f = 0,3 -> LOOSE, o mesmo na grade padrão (0,05 g) e na de 0,01 g, com resolução numérica < 0,01 g (LMUY 0,45; pré-condição: duas saturações, nenhuma capacidade inválida antes delas); [FAIL] TC-EQ-046: tração (Crr 0,015, CdA 1,0, R 8 m; só de teste) -> S_r e C_N caem (rumo a loose), S_f e capacidades dianteiras iguais, veredito segue PUSH neste caso; só Crr (sem R) -> queda de S_r abaixo da resolução, segue NEUTRO
DETECTADO      texto_veredito sem o prefixo DEMONSTRATIVO -> [FAIL] TC-EQ-018: nome de fator inválido (inclusive LONGVL, que não é fator de escala) e valor 0 ou NaN -> ValueError; textos exatos de 7.3 e prefixo DEMONSTRATIVO
6 / 6
```

</details>

<details><summary>tests/mutation_equilibrio.py: stderr (final)</summary>

```text
[executor] início 12:26:26, fim 12:28:23, 116.4 s
```

</details>

### `tests/mutation_planilha_equilibrio.py`

- Esperado: 5/5 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> 4 PASS, 0 FAIL, de 4 testes | MOTOR: excel (Excel 16.0 via COM, PID 41580)
- Obtido: 5/5 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_planilha_equilibrio.py: saída</summary>

```text
tempo por rodada: 663 s (tentativa 1, orçamento restante 6336 s)
PRE-CHECAGEM OK: original -> 4 PASS, 0 FAIL, de 4 testes | MOTOR: excel (Excel 16.0 via COM, PID 41580)
  tempo por rodada: 559 s (tentativa 1, orçamento restante 5777 s)
DETECTADO      força exigida com a e b trocados -> TC-WB41-004:; TC-WB41-005: 
  tempo por rodada: 211 s (tentativa 1, orçamento restante 5565 s)
DETECTADO      sem cos δ na dianteira -> TC-WB41-004:; TC-WB41-005:; TC-WB41-006; TC-WB41-006 
  tempo por rodada: 214 s (tentativa 1, orçamento restante 5350 s)
DETECTADO      Ackermann com sinal invertido -> TC-WB41-004:; TC-WB41-005:; TC-WB41-006; TC-WB41-006 
  tempo por rodada: 214 s (tentativa 1, orçamento restante 5136 s)
DETECTADO      ganho de camber com sinal invertido -> TC-WB41-004:; TC-WB41-005:; TC-WB41-006; TC-WB41-006 
  tempo por rodada: 216 s (tentativa 1, orçamento restante 4919 s)
DETECTADO      pior origem trocada pela melhor (MAX -> MIN) -> TC-WB41-004:; TC-WB41-005:; TC-WB41-006; TC-WB41-006 
5 / 5
```

</details>

<details><summary>tests/mutation_planilha_equilibrio.py: stderr (final)</summary>

```text
[executor] início 12:28:23, fim 13:03:04, 2080.8 s
```

</details>

### `tests/mutation_mmm.py`

- Esperado: 5/5 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> test_mmm.py: 11 PASS, 0 FAIL, de 11 testes | test_escada.py: 3 PASS, 0 FAIL, de 3 testes
- Obtido: 5/5 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_mmm.py: saída</summary>

```text
PRE-CHECAGEM OK: original -> test_mmm.py: 11 PASS, 0 FAIL, de 11 testes | test_escada.py: 3 PASS, 0 FAIL, de 3 testes
DETECTADO      alfa_rodas: sinal do termo a/R -> [FAIL] TC-MMM-002: pneu de brinquedo (μ=1,5, α0=0,1 rad; derivado à mão): R grande T=μ·g e NEUTRO; R=8,5 m T=cos δ_ref·μ·g, PUSH, Q à mão; sensibilidade à carga só na traseira -> LOOSE, eixo R, T e Q à mão; SI troca de sinal com a rigidez de eixo e é ≈ 0 no simétrico; [FAIL] TC-MMM-005: a = b e eixos iguais (R grande): δ do trim = L/R (1e-6) em 3 A_Y; |cn_estabilizante| em Q < 1e-6; NEUTRO; SI ≈ 0; rolagem mais rígida na frente -> SI e K > 0, na traseira -> < 0; [FAIL] TC-MMM-003: força bruta 41 × 41 em β × δ via ponto (sem capacidade_eixo): o maior A_Y nos cruzamentos de C_N = 0 (interpolação linear entre vizinhos) fica em [0,97·T, T + resolucao_ms2] [test_mmm.py; 165 s]
DETECTADO      alfa_rodas: b/R no lugar de a/R -> [FAIL] TC-MMM-007: no trim |ΣFy−m·A_Y|<1e-6 N e |N|<1e-6 N·m; A_Y acima do limite -> convergiu=False com motivo e campos None; sem raio_m -> ValueError; limite: descolamento, toe que consome a faixa e pico na borda -> N/A com o motivo de capacidade_eixo e sem T; variante Python completa em 0,5·T: resíduos Fx, Fy, N em eixos do carro (§2.5) < 1e-6, com Ackermann também; limite acoplado: eixo que satura com ay_sat = T e o outro None (decisão 3), T e Q à mão; transf_long=regime: ΔFz traseira = (m·a_x·h + D·h_cp)/L com e sem h_cp (1e-6 N); rotação β sempre no acoplado (planilha_acoplada fecha ΣFy = m·A·cos β, o desacoplado ΣFy = m·A); sem rotação (rotacao_beta=False) o Newton dá o trim desacoplado e a_x = 0 no regime; Trim.causa estruturada; conferência de margem do limite acoplado (capacidade enorme -> N/A, sem eixo limitante); folga do outro eixo em T à mão (N e fração), NEUTRO com fração <= res/T e None nas desacopladas [test_mmm.py; 213 s]
DETECTADO      _estabilizante: cn_estabilizante = +cn_iso (fonte única do sinal) -> [FAIL] TC-MMM-002: pneu de brinquedo (μ=1,5, α0=0,1 rad; derivado à mão): R grande T=μ·g e NEUTRO; R=8,5 m T=cos δ_ref·μ·g, PUSH, Q à mão; sensibilidade à carga só na traseira -> LOOSE, eixo R, T e Q à mão; SI troca de sinal com a rigidez de eixo e é ≈ 0 no simétrico; [FAIL] TC-MMM-005: a = b e eixos iguais (R grande): δ do trim = L/R (1e-6) em 3 A_Y; |cn_estabilizante| em Q < 1e-6; NEUTRO; SI ≈ 0; rolagem mais rígida na frente -> SI e K > 0, na traseira -> < 0; [FAIL] TC-MMM-006: CG lateral ≠ 0 + espelhar: T e veredito de cada sentido = analise_par_dois_sentidos (mesma grade de α, dentro da resolucao_ms2 dele); cn_iso com sinais opostos entre push e loose; cn_estabilizante > 0 no push [test_mmm.py; 207 s]
DETECTADO      balanço: sem o termo −m·A·sen β em fx_exigido='balanco' -> [FAIL] TC-MMM-007: no trim |ΣFy−m·A_Y|<1e-6 N e |N|<1e-6 N·m; A_Y acima do limite -> convergiu=False com motivo e campos None; sem raio_m -> ValueError; limite: descolamento, toe que consome a faixa e pico na borda -> N/A com o motivo de capacidade_eixo e sem T; variante Python completa em 0,5·T: resíduos Fx, Fy, N em eixos do carro (§2.5) < 1e-6, com Ackermann também; limite acoplado: eixo que satura com ay_sat = T e o outro None (decisão 3), T e Q à mão; transf_long=regime: ΔFz traseira = (m·a_x·h + D·h_cp)/L com e sem h_cp (1e-6 N); rotação β sempre no acoplado (planilha_acoplada fecha ΣFy = m·A·cos β, o desacoplado ΣFy = m·A); sem rotação (rotacao_beta=False) o Newton dá o trim desacoplado e a_x = 0 no regime; Trim.causa estruturada; conferência de margem do limite acoplado (capacidade enorme -> N/A, sem eixo limitante); folga do outro eixo em T à mão (N e fração), NEUTRO com fração <= res/T e None nas desacopladas [test_mmm.py; 201 s]
DETECTADO      cos_delta='trim': cos δ_ref = L/R no lugar do δ do trim -> [FAIL] TC-MMM-007: no trim |ΣFy−m·A_Y|<1e-6 N e |N|<1e-6 N·m; A_Y acima do limite -> convergiu=False com motivo e campos None; sem raio_m -> ValueError; limite: descolamento, toe que consome a faixa e pico na borda -> N/A com o motivo de capacidade_eixo e sem T; variante Python completa em 0,5·T: resíduos Fx, Fy, N em eixos do carro (§2.5) < 1e-6, com Ackermann também; limite acoplado: eixo que satura com ay_sat = T e o outro None (decisão 3), T e Q à mão; transf_long=regime: ΔFz traseira = (m·a_x·h + D·h_cp)/L com e sem h_cp (1e-6 N); rotação β sempre no acoplado (planilha_acoplada fecha ΣFy = m·A·cos β, o desacoplado ΣFy = m·A); sem rotação (rotacao_beta=False) o Newton dá o trim desacoplado e a_x = 0 no regime; Trim.causa estruturada; conferência de margem do limite acoplado (capacidade enorme -> N/A, sem eixo limitante); folga do outro eixo em T à mão (N e fração), NEUTRO com fração <= res/T e None nas desacopladas [test_mmm.py; 213 s]
5/5 mutantes mortos
5 / 5
tempo total: 1695 s
```

</details>

<details><summary>tests/mutation_mmm.py: stderr (final)</summary>

```text
[executor] início 13:03:04, fim 13:31:18, 1695.0 s
```

</details>

### `tests/mutation_inc7.py`

- Esperado: 5/5 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> test_formas_v43.py: 4 PASS, 0 FAIL, de 4 testes | test_skidpad.py: 2 PASS, 0 FAIL, de 2 testes | test_neutro.py: 2 PASS, 0 FAIL, de 2 testes
- Obtido: 5/5 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_inc7.py: saída</summary>

```text
PRE-CHECAGEM OK: original -> test_formas_v43.py: 4 PASS, 0 FAIL, de 4 testes | test_skidpad.py: 2 PASS, 0 FAIL, de 2 testes | test_neutro.py: 2 PASS, 0 FAIL, de 2 testes
DETECTADO      deriva_ackermann v43: sinal do termo (θ_i − θ̄_F) -> [FAIL] TC-ACK-001 Ackermann v43: oráculo ω×r, 100 % dentro da cota de 2ª ordem, 0 % = θ_FL − θ_FR, curva à direita por espelho e v42 congelada  [test_formas_v43.py; 195 s]
DETECTADO      fx_exigido_traseira v43: α_F e α_R trocados -> [FAIL] TC-FXI-001 Fx v43: grade × contínua dentro da cota, oráculo vetorial O(ε³) e v42 congelada  [test_formas_v43.py; 123 s]
DETECTADO      _alfa_na_grade: sem o limite no pico (réplica de grade) -> [FAIL] TC-FXI-002 Fx v43: ponto fixo com a elipse (erro medido), LOOSE com F_yr acima do pico, sem frente sem Fx e erro de geometria com a mensagem original; [FAIL] TC-ACK-002 planilha_v43 no mmm: contrato, V4.2 intacta, desacoplada, limite = analise_par v43 e linha da escada  [test_formas_v43.py; 5 s]
DETECTADO      raio_linha_central: (d_int + d_ext)/2 no lugar de /4 -> [FAIL] TC-SKP-001 geometria: linha central, rente aos cones (traseiro, dianteiro, empate) e R_in' <= L; [FAIL] TC-SKP-002 entradas vazias, meia largura do .tir e modos  [test_skidpad.py; 125 s]
DETECTADO      estudo_neutro: soma_erros sem o e_R -> [FAIL] TC-NEU-001 estudo do NEUTRO: grades aninhadas, determinismo, erro de Δ × e_F + e_R e regra sem mudança  [test_neutro.py; 534 s]
5/5 mutantes mortos
5 / 5
tempo total: 1518 s
```

</details>

<details><summary>tests/mutation_inc7.py: stderr (final)</summary>

```text
[executor] início 13:31:19, fim 13:56:36, 1517.7 s
```

</details>

### `tests/mutation_planilha_v43.py`

- Esperado: 4/4 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> 1 PASS, 0 FAIL, de 1 testes | MOTOR: excel (Excel 16.0 via COM, PID 50524)
- Obtido: 4/4 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_planilha_v43.py: saída</summary>

```text
tempo por rodada: 564 s (tentativa 1, orçamento restante 9435 s)
PRE-CHECAGEM OK: original -> 1 PASS, 0 FAIL, de 1 testes | MOTOR: excel (Excel 16.0 via COM, PID 50524)
  tempo por rodada: 560 s (tentativa 1, orçamento restante 8874 s)
DETECTADO      sinal de θ no Δα do Ackermann (C-C1) -> TC-WB43-004: 
  tempo por rodada: 563 s (tentativa 1, orçamento restante 8311 s)
DETECTADO      aF e aR trocados no Fx por arrasto (C-G5) -> TC-WB43-004: 
  tempo por rodada: 556 s (tentativa 1, orçamento restante 7754 s)
DETECTADO      sem o limite no pico no α do arrasto (C-G4) -> TC-WB43-004: 
  tempo por rodada: 285 s (tentativa 1, orçamento restante 7469 s)
DETECTADO      modo do R trocado (C-A14) -> TC-WB43-004: 
4 / 4
```

</details>

<details><summary>tests/mutation_planilha_v43.py: stderr (final)</summary>

```text
[executor] início 13:56:36, fim 14:38:47, 2531.0 s
```

</details>

### `tests/mutation_planilha_v44.py`

- Esperado: 4/4 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> 4 PASS, 0 FAIL, de 4 testes | MOTOR: excel (Excel 16.0 via COM, PID 11712)
- Obtido: 4/4 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_planilha_v44.py: saída</summary>

```text
tempo por rodada: 171 s (tentativa 1, orçamento restante 6825 s)
PRE-CHECAGEM OK: original -> 4 PASS, 0 FAIL, de 4 testes | MOTOR: excel (Excel 16.0 via COM, PID 11712)
  tempo por rodada: 175 s (tentativa 1, orçamento restante 6647 s)
DETECTADO      nome trocado por outro do mesmo papel (B4: L -> t_F) -> TC-WB44-005 
  tempo por rodada: 216 s (tentativa 1, orçamento restante 6428 s)
DETECTADO      nome trocado pelo endereço da vizinha (B5: L -> '05_VEHICLE'!$B$7) -> TC-WB44-005 
  tempo por rodada: 170 s (tentativa 1, orçamento restante 6255 s)
DETECTADO      operador no ramo de instabilidade de rolagem (B21: <=0 -> >=0) -> TC-WB44-005 
  tempo por rodada: 364 s (tentativa 1, orçamento restante 5882 s)
DETECTADO      constante (B4: 9.81 -> 9.8) -> TC-WB44-005 
4 / 4
```

</details>

<details><summary>tests/mutation_planilha_v44.py: stderr (final)</summary>

```text
[executor] início 14:38:47, fim 14:57:26, 1119.1 s
```

</details>

## Planilha regenerada (CA-07, CA-08)

- Autoteste do comparador (`tools/test_comparar_planilhas.py`): 15 PASS, 0 FAIL, de 15 (esperado 15): **PASS**
- Build: `python/build_workbook.py <tmp>/FSAE_EV_Suspension_Fase1_V2_4.xlsx --layout <tmp>/layout_V2_4.json`, código 0

<details><summary>build: stdout</summary>

```text
salvo C:\Users\vferr\AppData\Local\Temp\dds_build_tobz8lt1\FSAE_EV_Suspension_Fase1_V2_4.xlsx linhas 177 ref 1526.9250569300661 -1131.8643128749413 2.715269352685693
```

</details>

<details><summary>build: stderr (final)</summary>

```text
[executor] início 14:57:34, fim 14:57:35, 1.1 s
```

</details>

- V3.0: `python/atualizar_planilha.py <tmp>/V2_4.xlsx <tmp>/V3_0.xlsx`, código 0
- V4.0: `python/gerar_v4_0.py --v30 <referência da V3.0> --saida <tmp>/V4_0.xlsx`, código 0
- V4.1: `python/gerar_v4_1.py --saida <tmp>/V4_1.xlsx` (a V4.0 sai da tag `v4.0`), código 0
- V4.2: `python/gerar_v4_2.py --saida <tmp>/V4_2.xlsx` (a V4.1 sai da tag `v4.1`), código 0
- V4.3: `python/gerar_v4_3.py --saida <tmp>/V4_3.xlsx` (a V4.2 sai da tag `v4.2`), código 0
- V4.4: `python/gerar_v4_4.py --saida <tmp>/V4_4.xlsx` (a V4.3 sai da tag `v4.3`), código 0
- Referência da V3.0: tag `v3.0`. A regeneração e os testes CA-09 usam a referência; a V3.0 de excel/ tem de ser igual ao arquivo da tag (a viva da equipe é outro arquivo, no Drive).

```text
fórmulas: entregue 347 | gerada 347 | esperado 347
células comparadas: 2042 | diferenças: 0
CA-07 PASS
diferenças no layout: 0
CA-08 PASS
--- V3.0 (regeneração vs referência) ---
fórmulas: entregue 387 | gerada 387 | esperado 387
células comparadas: 2488 | diferenças: 0
CA-07 PASS
--- V3.0 de excel/ = tag v3.0 --- SHA-256 de `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`: 659fcf01f006b68a0e8a3c6df9da48e9b1b304764713b1fff975264d5e9db56b; da referência: 659fcf01f006b68a0e8a3c6df9da48e9b1b304764713b1fff975264d5e9db56b
--- V4.0 (regeneração vs excel/) ---
fórmulas: entregue 387 | gerada 387 | esperado 387
células comparadas: 2491 | diferenças: 0
CA-07 PASS
--- V4.1 (regeneração vs excel/) ---
fórmulas: entregue 117569 | gerada 117569 | esperado 117569
células comparadas: 125788 | diferenças: 0
CA-07 PASS
--- V4.2 (regeneração vs excel/) ---
fórmulas: entregue 117627 | gerada 117627 | esperado 117627
células comparadas: 126072 | diferenças: 0
CA-07 PASS
--- V4.3 (regeneração vs excel/) ---
fórmulas: entregue 146373 | gerada 146373 | esperado 146373
células comparadas: 155404 | diferenças: 0
CA-07 PASS
--- V4.4 (regeneração vs excel/) ---
fórmulas: entregue 146373 | gerada 146373 | esperado 146373
células comparadas: 155407 | diferenças: 0
CA-07 PASS
```

## Viva da equipe (informativo, EDR-063)

Fora do resumo e sem efeito no código de saída: a viva é o arquivo que a equipe preenche no Google Drive e muda sem commit. Conferida (em cópia local) contra a referência da versão dela, lida na 00_README A3; `tools/conferir_viva.py` dá o mesmo veredito com código de saída.

- Status: **VIVA FIEL (código 0)**

```text
viva: H:\.shortcut-targets-by-id\1Kytf4APy0OtH5Aq5PqlOwH5UY65YMX5U\T11 - Tupã\2. Projeto\Mecanica\Suspensao\Documentacao\Planilha DDS\FSAE_EV_Suspension_Fase1_V4_4.xlsx
versão da viva (00_README A3): V4.4; referência: C:\Users\vferr\AppData\Local\Temp\dds_viva_4i7lt2e7\referencia_v4.4.xlsx
SHA-256 da cópia: a1c03cabca3c49308c6cf2e2131fd158caca230e751c57cbe91c7081c16ed711
fórmulas: viva 146373 | esperado 146373
células comparadas: 155407 (entradas livres: 423) | diferenças: 0
CA-07 (viva) PASS
```

## Versão gravada na planilha (fase B, passo 3)

A versão escrita em `00_README!A3` precisa ser a mesma do nome do arquivo.

- `excel/FSAE_EV_Suspension_Fase1_V2.1.xlsx`: A3 diz V2.1: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V2_4.xlsx`: A3 diz V2.4: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`: A3 diz V3.0: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx`: A3 diz V4.0: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx`: A3 diz V4.1: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx`: A3 diz V4.2: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`: A3 diz V4.3: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx`: A3 diz V4.4: **PASS**

## Teste da planilha (CA-09)

- `tests/test_workbook.py`: esperado 19 (pneu (10_TIRE) da V3.0; registro-de-versoes-V3_0.md); obtido 19 PASS, 0 FAIL, de 19; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 45192)

<details><summary>tests/test_workbook.py: stderr (final)</summary>

```text
[executor] início 14:59:32, fim 15:00:01, 28.7 s
```

</details>

- `tests/test_workbook_suspensao.py`: esperado 15 (suspensão da V3.0 (15 com a 2ª rodada da revisão metodológica); registro-de-versoes-V3_0.md); obtido 15 PASS, 0 FAIL, de 15; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 8500)

<details><summary>tests/test_workbook_suspensao.py: stderr (final)</summary>

```text
[executor] início 15:00:01, fim 15:00:26, 25.3 s
```

</details>

- `tests/test_workbook_v4_0.py`: esperado 2 (V4.0; plano do incremento 3); obtido 2 PASS, 0 FAIL, de 2; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 10296)

<details><summary>tests/test_workbook_v4_0.py: stderr (final)</summary>

```text
[executor] início 15:00:26, fim 15:00:35, 8.7 s
```

</details>

- `tests/test_workbook_v4_1.py`: esperado 5 (V4.1 (TC-WB41-003 a 006, parte 1 e 2 do 006); plano do incremento 4); obtido sem linha de resumo; código 124: **FAIL**
- MOTOR: (não informado)

<details><summary>tests/test_workbook_v4_1.py: stderr (final)</summary>

```text
[executor] início 15:00:35, fim 15:30:36, 1800.6 s; TIMEOUT depois de 1800 s (árvore do PID 47384 encerrada)
```

</details>

- `tests/test_workbook_v4_2.py`: esperado 2 (V4.2 (TC-WB42-005 e 006); plano do incremento 5); obtido 2 PASS, 0 FAIL, de 2; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 948)

<details><summary>tests/test_workbook_v4_2.py: stderr (final)</summary>

```text
[executor] início 15:30:36, fim 15:42:37, 721.0 s
```

</details>

- `tests/test_workbook_v4_3.py`: esperado 3 (V4.3 (TC-WB43-003 a 005); plano do inc. 7); obtido 3 PASS, 0 FAIL, de 3; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 19000)

<details><summary>tests/test_workbook_v4_3.py: stderr (final)</summary>

```text
[executor] início 15:42:37, fim 16:36:03, 3206.2 s
```

</details>

- `tests/test_workbook_v4_4.py`: esperado 5 (V4.4 (TC-WB44-005 e 006 e 3 checagens de apoio); plano do inc. 8); obtido 5 PASS, 0 FAIL, de 5; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 49216)

<details><summary>tests/test_workbook_v4_4.py: stderr (final)</summary>

```text
[executor] início 16:36:03, fim 17:05:20, 1757.0 s
```

</details>

