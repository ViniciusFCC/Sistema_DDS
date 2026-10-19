# Data Contract V2.4 — Excel ↔ Python

**Versão:** V2.4 (2026-10-14). Base: `data-contract-V2.0` (alterações: seção 7, pneu, criada na V2.2 e revisada na V2.4 com o sistema de eixos do arquivo; seções 1–6 inalteradas). Histórico V2.0: base `data-contract-V1.0`. Alterações: seção 5 atualizada (aviso Fz<0 e validações agora implementadas; Python segue sem JSON I/O) e nova seção 6 (Kinematics V2.0: hardpoints e resultados; PROPOSTA). As seções 1–4 não foram alteradas. Ver `registro-de-versoes-V2.0.md`.

Fronteira única entre interface (Excel) e motor físico (Python). Excel nunca edita `results.json`; o fluxo é sempre `Excel → input.json → Python → results.json → Excel`.

---

## 1. Excel → Python (`input.json`)

### 1.1 Identificação e revisão (estrutura, não campo único)

```json
{
  "setup_id": "S-003",
  "revisions": {
    "geometry_rev": "G-REV-C",
    "kinematics_rev": "K-REV-B",
    "tire_rev": "T-REV-A",
    "dynamics_script_version": "V2.0"
  },
  "timestamp": "2026-09-05T14:30:00-03:00"
}
```
Nunca um `model_revision` único — cada domínio mantém a própria revisão (`DEC-012`), mesmo que nesta fase só `dynamics_script_version` mude com frequência.

### 1.2 Vehicle (Bloco A)

| Campo (`input.json`) | SUS-ID | Unidade no nome | Tipo | Origem |
|---|---|---|---|---|
| `mass_total_kg` | SUS-001 | kg | float | INPUT |
| `cg_height_m` | SUS-002 | m | float | INPUT |
| `wheelbase_m` | SUS-003 | m | float | REFERENCE (hardpoints) |
| `track_front_m` | SUS-004 | m | float | REFERENCE (hardpoints) |
| `track_rear_m` | SUS-005 | m | float | REFERENCE (hardpoints) |
| `cg_to_front_m` | SUS-006 (a) | m | float | INPUT (pesagem) |
| `cg_to_rear_m` | SUS-006 (b) | m | float | INPUT (pesagem) |
| `unsprung_mass_front_kg` | SUS-007 | kg | float | INPUT |
| `unsprung_mass_rear_kg` | SUS-008 | kg | float | INPUT |
| `unsprung_cg_height_front_m` | SUS-010 | m | float | INPUT |
| `unsprung_cg_height_rear_m` | SUS-011 | m | float | INPUT |
| `ground_plane_z_m` | SUS-000 | m | float | INPUT — constante ligada à `geometry_rev`, não reenviada por Setup (ver nota 1.5) |

### 1.3 Suspension (Bloco D/F — atenção aos itens marcados PROVISÓRIO)

| Campo | SUS-ID | Unidade no nome | Tipo | Origem |
|---|---|---|---|---|
| `spring_rate_front_N_per_m` | SUS-203 | N/m | float | INPUT (Analysis Mode) |
| `spring_rate_rear_N_per_m` | SUS-203 | N/m | float | INPUT (Analysis Mode) |
| `motion_ratio_front_wheel_per_spring` | SUS-201 | adimensional | float | REFERENCE + MODEL/CHECK |
| `motion_ratio_rear_wheel_per_spring` | SUS-201 | adimensional | float | REFERENCE + MODEL/CHECK |
| `k_arb_front_Nm_per_rad` | SUS-206 (termo ARB) | N·m/rad | float | INPUT (0 se não houver ARB) |
| `k_arb_rear_Nm_per_rad` | SUS-207 (termo ARB) | N·m/rad | float | INPUT (0 se não houver ARB) |
| `roll_center_front_m` | SUS-401-F | m | float | **PROVISÓRIO (Fase 1): INPUT manual em `06_SUSPENSION`. Fase 2: REFERENCE via `07_KINEMATICS`** |
| `roll_center_rear_m` | SUS-401-R | m | float | **PROVISÓRIO (Fase 1), mesma nota acima** |

`roll_stiffness_front/rear` **não é enviado** — é calculado pelo Python a partir de `spring_rate`, `motion_ratio`, `track` e `k_arb` (`SUS-206`/`SUS-207`), consistente com "Excel não precisa saber como o Python calcula".

### 1.4 Vehicle State + Aero (Setup-level, conforme decisão de aero fixo)

| Campo | SUS-ID | Unidade no nome | Tipo | Origem |
|---|---|---|---|---|
| `ax_m_s2` | — (Vehicle State) | m/s² | float | INPUT |
| `ay_m_s2` | — (Vehicle State) | m/s² | float | INPUT |
| `downforce_total_N` | SUS-701 | N | float | INPUT (constante por Setup) |
| `aero_balance_front_fraction` | SUS-702 | adimensional (0–1) | float | INPUT (constante por Setup) |

### 1.5 Nota sobre `ground_plane_z_m`

Diferente dos demais campos (que mudam por Setup), `SUS-000` é uma constante de geometria — muda só quando `geometry_rev` muda, não a cada execução. Recomendo armazená-lo junto ao `hardpoints.csv` (ou em um `geometry.json` separado por `geometry_rev`), não repeti-lo em todo `input.json` de Setup. Mantenho aqui na tabela por completude, mas a implementação real deve evitar essa duplicação.

---

## 2. Python → Excel (`results.json`)

### 2.1 Meta (status estruturado, nunca campo único)

```json
{
  "setup_id": "S-003",
  "revisions": { "...": "mesma estrutura da seção 1.1" },
  "validation": {
    "tc_passed": ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007", "TC-008", "TC-009", "TC-010"],
    "tc_failed": [],
    "lifecycle_status_by_sus_id": { "SUS-101": "CHECKED", "SUS-103": "CHECKED", "SUS-301": "DRAFT" },
    "validation_status_by_sus_id": { "SUS-101": "PASS", "SUS-103": "PASS", "SUS-301": "NOT_VALIDATED" }
  }
}
```
`lifecycle_status` e `validation_status` são objetos separados, por `SUS-ID` — nunca um único status geral do arquivo (regressaria a correção do `DEC-010`).

### 2.2 Resultados físicos

| Campo | SUS-ID | Unidade no nome |
|---|---|---|
| `sprung_mass_total_kg` | SUS-009 | kg |
| `sprung_cg_height_m` | SUS-012 | m |
| `static_fz_FL_N`, `_FR_N`, `_RL_N`, `_RR_N` | SUS-101 | N |
| `delta_fz_long_front_per_corner_N`, `_rear_per_corner_N` | SUS-102 | N |
| `delta_fz_lat_front_axle_N`, `_rear_axle_N` | SUS-103 | N |
| `lambda_f_fraction`, `lambda_r_fraction` | SUS-208 | adimensional |
| `roll_stiffness_front_Nm_per_rad`, `_rear_Nm_per_rad` | SUS-206/207 (calculado) | N·m/rad |
| `fz_FL_N`, `fz_FR_N`, `fz_RL_N`, `fz_RR_N` | SUS-104 | N |
| `wheel_rate_front_N_per_m`, `_rear_N_per_m` | SUS-202 | N/m |
| `natural_frequency_front_Hz`, `_rear_Hz` | SUS-205 | Hz |

---

## 3. Regra de segurança (fluxo unidirecional)

```
EXCEL (INPUT/TARGET) → input.json → PYTHON (Physical Model) → results.json → EXCEL (OUTPUT/STATUS)
```
Excel nunca escreve em `results.json`. Se alguém "corrigir" um `fz_FR` direto na planilha, está editando uma cópia de exibição, não o modelo — a próxima execução do Python sobrescreve. Células de `results.json` no Excel devem ser protegidas (travadas) e visualmente distintas de INPUT.

---

## 4. Ordem de implementação (mantida, com o ajuste da seção 1.3)

1. Este Data Contract (fechado aqui).
2. Field Map completo (seção 1–2 acima já cobre isso).
3. Estrutura física do workbook (8 abas da Fase 1 no contrato original; o workbook atual tem 16 abas, `00_README` a `15_CHANGELOG`, e os nomes de aba neste documento já seguem a numeração atual).
4. Interface de `01_SETUP` / `05_VEHICLE` / `08_VEHICLE_STATE` (inputs).
5. Bridge: Excel gera `input.json`, consome `results.json`.
6. `09_LOADS` — primeira saída real, incluindo o campo `roll_center_front/rear` marcado como provisório em `06_SUSPENSION`.
7. `06_SUSPENSION` + `11_DESIGN` — MR, Wheel Rate, Natural Frequency, Design Mode.
8. `13_VALIDATION` — exibindo `validation.tc_passed`/`tc_failed` e os dois status por `SUS-ID`.
9. `14_DASHBOARD`.

Fase 2 substitui os campos `roll_center_front/rear` provisórios por REFERENCE real de `07_KINEMATICS`, sem mudar o resto do contrato — exatamente a vantagem arquitetural que motivou este documento.


---

## 5. Estado de implementação e escopo não coberto (V1.0)

Verificado em 2026-10-09 contra `suspension_model_V2_0.py` e `kinematics_model_V2_0.py` (fatos dos arquivos):

1. **O fluxo `input.json → Python → results.json` ainda não está implementado.** Os módulos Python não leem nem escrevem JSON; operam sobre `VehicleConfig` e funções. O Excel funciona como segunda implementação independente das mesmas equações (cross-check), conforme `DR-008` do workbook.
2. **Divergência com a seção 1.3:** o contrato diz que o Python calcula a rigidez de rolagem a partir de `spring_rate`, `motion_ratio`, `track` e `k_arb`. No código, `VehicleConfig` recebe `roll_stiffness_front/rear` direto; existe `roll_stiffness_axle(k_wheel, track, k_arb)`, mas não há função que orquestre o cálculo a partir dos campos do contrato.
3. **`ground_plane_z_m` (SUS-000)** não é usado no Python: `cg_height` e as alturas não-suspensas já entram medidas acima do solo.
4. **Campos ainda não definidos neste contrato** (exigem nome com unidade, conforme seção 10 da arquitetura): `SUS-013`/`SUS-014` (`FB_f`, `TF_r`), resultado de `SUS-301`/`SUS-302` e Tire. Hardpoints e resultados de kinematics: ver seção 6 (proposta V2.0).
5. **`validation.tc_passed`/`tc_failed`** (seção 2.1) lista `TC-001` a `TC-010`; a V2.0 tem também `TC-KIN-001..006` e `101..117`, `TC-HP-001..018` e `TC-SUS-V2-001..004` (namespaces próprios) e o piloto end-to-end.
6. **Atualizado na V2.0:** o aviso de `Fz < 0` (SUS-104) e os bloqueios de entrada do Guide (D.2) agora existem no Python (`FzLiftoffWarning`; `ValueError` com o ID da ficha). Continua sem JSON I/O.


---

## 6. Kinematics V2.0 — hardpoints e resultados (PROPOSTA, aguarda aprovação)

### 6.1 Entrada: `hardpoints.csv` + `hardpoints.meta.json`
Schema completo em `hardpoint-schema-V2.0.md`. Colunas: `Point_ID, X_m, Y_m, Z_m, Component, Status` (unidade no nome, arquitetura seção 10). O `.meta.json` carrega `schema_version`, `geometry_rev`, `coordinate_system` (`ISO8855_X_FORWARD_Y_LEFT_Z_UP`), `units` (`m`), `ground_plane_z_m` (SUS-000), `kop`, `source`, `freeze_level`, `timestamp`. Por isso `ground_plane_z_m` **não** é reenviado no `input.json` de Setup: vive junto da geometria (seção 1.5).

### 6.2 Saída: `kinematics_sweep.csv` (uma linha por curso) — nomes de campo com unidade
| Campo | SUS-ID | Unidade |
|---|---|---|
| `travel_m` | — (curso, Z do centro da roda, bump +) | m |
| `camber_deg` | SUS-407 | ° |
| `toe_deg` | SUS-408 | ° (+ = toe-out) |
| `caster_deg`, `kpi_deg` | SUS-410 | ° |
| `scrub_radius_m`, `mech_trail_m` | SUS-410 | m |
| `track_change_m`, `wheelbase_change_m` | SUS-411 | m |
| `spring_length_m`, `mr_wheel_per_spring` | SUS-409 | m ; adimensional |
| `rc_height_m` | SUS-412 | m (acima do solo) |
| `ic_front_y_m`, `ic_front_z_m`, `ic_side_x_m`, `ic_side_z_m` | SUS-412 | m (vazio = IC no infinito) |
| `side_force_line_slope` | SUS-412 → SUS-301/302 | adimensional (dz/dx) |

Um arquivo por canto (prefixo no nome do arquivo, ex.: `kinematics_sweep_FL.csv`). `kinematics_sweep_synthetic_V2.0.csv` é um **exemplo gerado com geometria sintética**; não representa o carro.

### 6.3 Fluxo e regras
`hardpoints.csv → Python (hardpoints_V2_0.py, kinematics_model_V2_0.py) → kinematics_sweep_<canto>.csv → Excel (07_KINEMATICS, somente leitura)`. O Excel **não** recalcula cinemática (DR-009) e não deve receber hardpoints digitados à mão (arquitetura seção 8). Sem hardpoints reais (`Status` ≠ `SYNTHETIC`), os campos no Excel ficam **N/A**. O bridge automático continua não implementado (DR-008 da planilha).


---

## 7. Pneu V2.2 — dataset, entradas e resultados (PROPOSTA, aguarda aprovação; dataset PROVISÓRIO)

### 7.1 Dataset: `<dataset_id>.tir` + `<dataset_id>.meta.json`
O `.tir` é consumido sem alteração de valores. O `.meta.json` (exemplo: `Hoosier_R25B_13x7_TTC_provisional.meta.json`) carrega, como mínimo proposto: `schema_version`, `dataset_id`, `tire_rev` (T-REV-X), `provisional` (bool; true bloqueia uso como resultado do carro), `source_chain`, `cleaned_file_sha256`, `property_file_format`, `tyreside`, `units`, `convention_status`, `convention_evidence`, `mirroring_rule_for_left_wheels`, `pressure_effects`, `imported_sections`, `not_imported`, `validation_status`, `validity_ranges`.
`source_axis_system` ∈ {`SAE_CALSPAN`, `ISO_TYDEX`}: **obrigatório**; ausente ou `UNKNOWN` é rejeitado. `convention_status` ∈ {`USER_ASSERTED`, `CONFIRMED`, `UNKNOWN`}; o estado atual é `USER_ASSERTED` (dados do TTC, SAE; EDR-039). Transformação para ISO 8855 (roda direita): `alpha_file = −alpha_ISO`, `Fy_ISO = −Fy_file`, `gamma_file = −gamma_project` (inferência: o sinal de IA do TTC não foi verificado), `Fx` e `kappa` iguais; o espelhamento das rodas esquerdas é aplicado antes. Regras do loader (`tire_model_V2_2.load_dataset`), todas com teste: formato ≠ PAC2002/MF 5.2-like, unidades ≠ meter/newton/radians, `IP`≠`IP_NOM`, qualquer `PP*`≠0, coeficiente ausente, `TYRESIDE` desconhecido e `FZMAX`≤`FZMIN` são **rejeitados**.

### 7.2 Entradas por canto (Excel → Python), unidade no nome
| Campo | SUS-ID | Unidade | Origem |
|---|---|---|---|
| `fz_<FL|FR|RL|RR>_N` | SUS-104 | N | CALCULATED (09_LOADS) |
| `slip_angle_iso_<canto>_deg` | SUS-501 | ° (ISO 8855: + = velocidade para a esquerda) | INPUT (demonstrativo na V2.2) |
| `camber_project_<canto>_deg` | — (EDR-036 sem decisão) | ° (+ = topo para fora, nos dois lados) | INPUT manual |
| `slip_ratio_<canto>` | SUS-502 | adimensional (ISO: −1 = roda travada em frenagem) | INPUT (demonstrativo na V2.2) |

### 7.3 Resultados (Python → Excel)
| Campo | SUS-ID | Unidade |
|---|---|---|
| `tire_fx_<canto>_N` | SUS-502 | N (referencial do dataset; + = para frente) |
| `tire_fy_<canto>_N` | SUS-501 | N (convenção do projeto; rodas L com espelhamento H4) |
| `mu_eff_<canto>` | SUS-503 | adimensional (derivado do dataset, **não** medido) |
| `tire_status_<canto>` | SUS-501 | texto: `OK` ou `N/A - <motivo>` (liftoff, Fz/α/γ/κ fora da faixa, entrada ausente, dataset inválido) |

Resultado fora da faixa do dataset é **N/A**, nunca valor extrapolado. Python e Excel hoje são duas implementações da mesma transcrição das equações (DR-008); o bridge JSON continua não implementado (seção 5).
