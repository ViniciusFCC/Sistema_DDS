# Registro de versões — Sistema_DDS — V2.5 (revisão metodológica contra a literatura)

Data: 2026-10-19. Motivo: o usuário pediu que as fórmulas e métodos seguissem a literatura,
principalmente o Milliken, e autorizou todas as propostas da revisão
(`docs/revisao-metodologica.md`, P-01 a P-07). Decisões: EDR-045 a EDR-049; EDR-026 aprovado.

## Mapa V2.4 → V2.5

| Anterior | V2.5 | Mudança |
|---|---|---|
| `FSAE_EV_Suspension_Fase1_V2_4.xlsx` | `FSAE_EV_Suspension_Fase1_V2_5.xlsx` | Gerada da V2.4 por `python/atualizar_planilha.py` (openpyxl, sem recálculo nem gravação pelo Excel). 356 fórmulas (347 + 9 novas). Lista célula a célula abaixo. A V2.4 fica em `excel/` como histórico. |
| `suspension_model` V2.1 | V2.5 | Pneu em série (`ride_rate`, `wheel_rate_from_ride_rate`, `roll_stiffness_axle(..., k_tire)`, `arb_required`); `natural_frequency` recebe a ride rate; `wheel_rate_from_target_frequency(f, m, k_tire)`; massa suspensa por eixo (`sprung_mass_axle`, `sprung_cg_to_front`); `lateral_dfz` com termo gravitacional e CG suspenso em a_s (devolve também `a_s`, `h2`, `roll_angle_rad`); bloqueio de instabilidade de rolagem. |
| `tire_model` V2.4 | V2.5 | Ky com um único λFz0 (EDR-049). |
| `kinematics_model` | idem | `REACTION_POINT` do carro (EDR-048); funções do método V1 do SUS-406 marcadas como legado. |
| — | `python/atualizar_planilha.py` | Novo: gera a V2.5 e o registro de alterações. |
| — | `tests/test_workbook_suspensao.py` | Novo: Excel × Python das abas de suspensão (TC-WB25-001..009). |
| `tests/test_workbook.py` | idem | Passa a testar a V2.5 (10_TIRE); TC-WB24-001/002 aceitam só as células da lista de alterações. |
| testes de suspensão, pneu, oráculos, cinemática e mutação | idem | Identidades atualizadas (TC-005, TC-007, TC-008, TC-010, piloto, TC-SUS-V2-004, TC-TIRE-ORC-004) e oráculos da literatura (TC-SUS-V25-001..011, TC-KIN-119, mutante "LFZO extra em Ky"). |
| `tools/rodar_testes.py`, `tools/comparar_planilhas.py` | idem | Contagens novas; CA-07 também regenera a V2.5 e compara com a entregue (356 fórmulas, 0 diferença); CA-09 roda os dois testes de planilha. |
| Engineering Standard V2.0 | com nota V2.5 | Fichas SUS-009, 103, 205-208, 301, 302, 406 atualizadas; novas SUS-211 (K_T) e SUS-212 (ride rate). |
| `Engineering_Decision_Register.md` | idem | EDR-045 a EDR-049 (VERIFIED); EDR-026 APPROVED_WITH_CONDITIONS. |

## Resultados de código (2026-10-19, `tools/rodar_testes.py`)

- Pneu 43/43, oráculos 5/5, suspensão 54/54, cinemática 54/54, hardpoints 35/35, mutação 24/24.
- Planilha: V2.4 regenerada com 347 fórmulas e 0 diferença; V2.5 regenerada com 356 fórmulas e 0 diferença.
- `test_workbook` 19/19 (V2.5, pneu) e `test_workbook_suspensao` 9/9 (V2.5, suspensão), pelo Excel via COM.
- Exemplos publicados reproduzidos pelo modelo: Milliken p. 683 (590,8/483,4 lb/g e −2,0 °/g), p. 592 (barra 19 904 lb·ft/rad; K_W 476/254 lb/in), Tab. 16.3 e p. 602-603 (massas e h_s); Seward Ex. 4.1; Gillespie p. 154.

## Efeito nos valores da planilha (recalculada pelo Excel; entradas DEMONSTRATIVAS)

| Grandeza | Célula | V2.4 | V2.5 |
|---|---|---|---|
| K_φF [N·m/rad] | 06_SUSPENSION!B22 | 18 149,7 | 15 316,0 |
| K_φR [N·m/rad] | 06_SUSPENSION!B23 | 14 887,5 | 12 909,8 |
| λ_f | 06_SUSPENSION!B24 | 0,5494 | 0,5426 |
| massa suspensa por canto F [kg] | 06_SUSPENSION!B28 | 68,649 | 69,140 |
| f_n F / R [Hz] | 06_SUSPENSION!B32/B33 | 2,438 / 2,526 | 2,282 / 2,361 |
| anti-dive [%] | 06_SUSPENSION!B40 | 24,29 | 24,29 (mesmo IC placeholder, agora com sinal) |
| anti-squat [%] | 06_SUSPENSION!B41 | 63,25 | −1,01 (linha pelo centro da roda; IC placeholder) |
| ΔFz lateral F / R [N] | 09_LOADS!B19/B20 | 454,6 / 466,6 | 459,1 / 476,5 |
| φ [rad] | 09_LOADS!B21 | — | 0,0282 (1,62°) |
| Fz FL / FR / RL / RR [N] | 09_LOADS!B31:B34 | 543,6 / 1452,8 / 287,6 / 1220,9 | 539,1 / 1457,3 / 277,7 / 1230,7 |
| spring rate necessário F [N/m] | 11_DESIGN!B10 | 52 468,7 | 61 574,9 |
| K_ARB necessário F [N·m/rad] | 11_DESIGN!B20 | 5 058,5 | 5 665,7 |

Os números de 07_KINEMATICS (IC lateral) continuam PLACEHOLDER e o K_T é do .tir
PROVISÓRIO: nada desta tabela é resultado do carro.

## Limites

1. K_T (SUS-211) vem do .tir TTC provisório. Trocar pelo pneu real muda frequência e rigidez de rolagem.
2. Os ICs de 07_KINEMATICS e a altura do centro da roda traseira (B14 = SUS-011) são placeholders: o anti-squat negativo da tabela não diz nada sobre o carro.
3. Continua tudo NOT_VALIDATED fisicamente: a referência é o OptimumKinematics/OptimumTire e medição (EDR-004).
4. Frenagem regenerativa (motor no chassi) e anti-lift traseiro: escopo no EDR-033, sem decisão.

## Alterações célula a célula (gerado por `python/atualizar_planilha.py --registro`)

| Aba | Célula | Antes | Depois | Fonte / EDR |
|---|---|---|---|---|
| 05_VEHICLE | A25 | (vazia) | Massa suspensa - eixo dianteiro (m·b/L − m_uF) | EDR-047 |
| 05_VEHICLE | B25 | (vazia) | `='05_VEHICLE'!$B$4*'05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6-'05_VEHICLE'!$B$14` | EDR-047; Milliken p. 601-603; Seward eq. 5.14 |
| 05_VEHICLE | C25 | (vazia) | kg | EDR-047 |
| 05_VEHICLE | D25 | (vazia) | SUS-009 | EDR-047 |
| 05_VEHICLE | A26 | (vazia) | Massa suspensa - eixo traseiro (m·a/L − m_uR) | EDR-047 |
| 05_VEHICLE | B26 | (vazia) | `='05_VEHICLE'!$B$4*'05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6-'05_VEHICLE'!$B$15` | EDR-047; Milliken p. 601-603; Seward eq. 5.14 |
| 05_VEHICLE | C26 | (vazia) | kg | EDR-047 |
| 05_VEHICLE | D26 | (vazia) | SUS-009 | EDR-047 |
| 05_VEHICLE | A27 | (vazia) | CG suspenso -> eixo dianteiro (a_s = L·m_s,R/m_s) | EDR-047 |
| 05_VEHICLE | B27 | (vazia) | `='05_VEHICLE'!$B$6*'05_VEHICLE'!$B$26/'05_VEHICLE'!$B$23` | EDR-047; Milliken p. 601-603; Seward eq. 5.14 |
| 05_VEHICLE | C27 | (vazia) | m | EDR-047 |
| 05_VEHICLE | D27 | (vazia) | SUS-009 | EDR-047 |
| 06_SUSPENSION | A2 | (vazia) | Mola, MR, barra e roll center (B4:B15): valores DEMONSTRATIVOS herdados do T09/E03, para referência e teste das fórmulas; não são o TX/E05 (EDR-012/022). | EDR-012/022 |
| 06_SUSPENSION | A46 | (vazia) | Pneu em série e ride rate (EDR-045) — K_T PROVISÓRIO: rigidez vertical do .tir TTC, não é o pneu do carro | EDR-045 |
| 06_SUSPENSION | A47 | (vazia) | Rigidez vertical do pneu - dianteiro (K_T) | EDR-045 |
| 06_SUSPENSION | B47 | (vazia) | 120312.0 | EDR-045 (valor: .tir provisório, EDR-038) |
| 06_SUSPENSION | C47 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D47 | (vazia) | SUS-211 | EDR-045 |
| 06_SUSPENSION | A48 | (vazia) | Rigidez vertical do pneu - traseiro (K_T) | EDR-045 |
| 06_SUSPENSION | B48 | (vazia) | 120312.0 | EDR-045 (valor: .tir provisório, EDR-038) |
| 06_SUSPENSION | C48 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D48 | (vazia) | SUS-211 | EDR-045 |
| 06_SUSPENSION | A49 | (vazia) | Ride rate dianteiro K_R = K_W·K_T/(K_W+K_T) | EDR-045 |
| 06_SUSPENSION | B49 | (vazia) | `='06_SUSPENSION'!$B$18*'06_SUSPENSION'!$B$47/('06_SUSPENSION'!$B$18+'06_SUSPENSION'!$B$47)` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C49 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D49 | (vazia) | SUS-212 | EDR-045 |
| 06_SUSPENSION | A50 | (vazia) | Ride rate traseiro K_R = K_W·K_T/(K_W+K_T) | EDR-045 |
| 06_SUSPENSION | B50 | (vazia) | `='06_SUSPENSION'!$B$19*'06_SUSPENSION'!$B$48/('06_SUSPENSION'!$B$19+'06_SUSPENSION'!$B$48)` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C50 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D50 | (vazia) | SUS-212 | EDR-045 |
| 06_SUSPENSION | A51 | (vazia) | Rigidez de rolagem do par de pneus - dianteira (K_T·t_F²/2) | EDR-045 |
| 06_SUSPENSION | B51 | (vazia) | `='06_SUSPENSION'!$B$47*'05_VEHICLE'!$B$7^2/2` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C51 | (vazia) | N*m/rad | EDR-045 |
| 06_SUSPENSION | D51 | (vazia) | SUS-206 | EDR-045 |
| 06_SUSPENSION | A52 | (vazia) | Rigidez de rolagem do par de pneus - traseira (K_T·t_R²/2) | EDR-045 |
| 06_SUSPENSION | B52 | (vazia) | `='06_SUSPENSION'!$B$48*'05_VEHICLE'!$B$8^2/2` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C52 | (vazia) | N*m/rad | EDR-045 |
| 06_SUSPENSION | D52 | (vazia) | SUS-207 | EDR-045 |
| 06_SUSPENSION | A20 | Roll Stiffness sem ARB - dianteira | Roll Stiffness sem ARB e sem pneu (K_W·t_F²/2) - dianteira | EDR-045 |
| 06_SUSPENSION | A21 | Roll Stiffness sem ARB - traseira | Roll Stiffness sem ARB e sem pneu (K_W·t_R²/2) - traseira | EDR-045 |
| 06_SUSPENSION | A22 | Roll Stiffness dianteira (K_phiF) | Roll Stiffness dianteira K_phiF = (K_W·t²/2 + K_ARB) em série com K_T·t²/2 | EDR-045 |
| 06_SUSPENSION | B22 | `='06_SUSPENSION'!$B$20+'06_SUSPENSION'!$B$10` | `=1/(1/('06_SUSPENSION'!$B$20+'06_SUSPENSION'!$B$10)+1/'06_SUSPENSION'!$B$51)` | EDR-045; Milliken p. 592 e p. 680 |
| 06_SUSPENSION | A23 | Roll Stiffness traseira (K_phiR) | Roll Stiffness traseira K_phiR = (K_W·t²/2 + K_ARB) em série com K_T·t²/2 | EDR-045 |
| 06_SUSPENSION | B23 | `='06_SUSPENSION'!$B$21+'06_SUSPENSION'!$B$11` | `=1/(1/('06_SUSPENSION'!$B$21+'06_SUSPENSION'!$B$11)+1/'06_SUSPENSION'!$B$52)` | EDR-045; Milliken p. 592 e p. 680 |
| 06_SUSPENSION | A27 | Massa suspensa por canto (SUS-009, distribuição) | Massa suspensa por canto (SUS-009, por eixo: (m·b/L − m_uF)/2 e (m·a/L − m_uR)/2) | EDR-047 |
| 06_SUSPENSION | B28 | `='05_VEHICLE'!$B$23*('05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6)/2` | `='05_VEHICLE'!$B$25/2` | EDR-047; Milliken p. 601, Tab. 16.3 |
| 06_SUSPENSION | B29 | `='05_VEHICLE'!$B$23*('05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6)/2` | `='05_VEHICLE'!$B$26/2` | EDR-047; Milliken p. 601, Tab. 16.3 |
| 06_SUSPENSION | A31 | Frequência Natural (SUS-205) | Frequência Natural (SUS-205) — com a ride rate (pneu em série) | EDR-045 |
| 06_SUSPENSION | B32 | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$18/'06_SUSPENSION'!$B$28)` | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$49/'06_SUSPENSION'!$B$28)` | EDR-045; Gillespie eq. 5-9; Seward eq. 4.2 |
| 06_SUSPENSION | B33 | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$19/'06_SUSPENSION'!$B$29)` | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$50/'06_SUSPENSION'!$B$29)` | EDR-045; Gillespie eq. 5-9; Seward eq. 4.2 |
| 06_SUSPENSION | A34 | Anti-Dive / Anti-Squat (SUS-301/302) — Lifecycle: DRAFT->CHECKED | Anti-Dive / Anti-Squat (SUS-301/302) — com sinal (EDR-026/048) | EDR-048 |
| 06_SUSPENSION | A35 | Metodologia FROZEN (Milliken); linha geométrica (contact patch vs. wheel center) pendente de confirmação com a config. real de freio/trem de força. | Milliken p. 618-619: freio no cubo (outboard) -> linha pelo contact patch; motor no chassi com semieixos -> linha pelo centro da roda (Fig. 17.15b). + = anti, − = pro (p. 620). IC de 07_KINEMATICS ainda é PLACEHOLDER. | EDR-048 |
| 06_SUSPENSION | A38 | tan(phi_f) — dianteiro (a partir do IC lateral) | Inclinação dz/dx da linha contact patch -> IC lateral dianteiro (com sinal; freio no cubo) | EDR-048 |
| 06_SUSPENSION | A39 | tan(phi_r) — traseiro (a partir do IC lateral) | Inclinação dz/dx da linha centro da roda -> IC lateral traseiro (com sinal; motor no chassi) | EDR-048 |
| 06_SUSPENSION | B39 | `='07_KINEMATICS'!$B$12/'07_KINEMATICS'!$B$13` | `=('07_KINEMATICS'!$B$12-'07_KINEMATICS'!$B$14)/'07_KINEMATICS'!$B$13` | EDR-048; Milliken Fig. 17.15(b); Gillespie eq. 7-19 |
| 06_SUSPENSION | A40 | Anti-Dive (%) | Anti-Dive (%) = FB_f·(−dz/dx)·L/h·100 (+ = anti, − = pro-dive) | EDR-048 |
| 06_SUSPENSION | B40 | `='06_SUSPENSION'!$B$36*'06_SUSPENSION'!$B$38*('05_VEHICLE'!$B$6/'05_VEHICLE'!$B$5)*100` | `='06_SUSPENSION'!$B$36*(-'06_SUSPENSION'!$B$38)*('05_VEHICLE'!$B$6/'05_VEHICLE'!$B$5)*100` | EDR-048; Milliken p. 618 |
| 06_SUSPENSION | A41 | Anti-Squat (%) | Anti-Squat (%) = TF_r·(dz/dx)·L/h·100 (+ = anti, − = pro-squat) | EDR-048 |
| 07_KINEMATICS | A11 | Distância contact patch->IC, dianteiro (vista lateral) | Δx do IC lateral dianteiro ao contact patch (x_IC − x_CP; ISO: + = à frente) | EDR-048 |
| 07_KINEMATICS | B11 | 2.5 | -2.5 | EDR-048: mesmo PLACEHOLDER (2,5 m), agora com sinal: IC atrás do contact patch (Milliken p. 617) |
| 07_KINEMATICS | A13 | Distância contact patch->IC, traseiro (vista lateral) | Δx do IC lateral traseiro ao centro da roda (x_IC − x_WC; ISO: + = à frente) | EDR-048 |
| 07_KINEMATICS | A14 | (vazia) | Altura do centro da roda traseira (ponto de reação do anti-squat) | EDR-048 |
| 07_KINEMATICS | B14 | (vazia) | `='05_VEHICLE'!$B$17` | EDR-048: PLACEHOLDER = SUS-011 (aproximado pela altura do centro da roda) |
| 07_KINEMATICS | C14 | (vazia) | m | EDR-048 |
| 07_KINEMATICS | D14 | (vazia) | SUS-406-R | EDR-048 |
| 09_LOADS | A17 | Transferência Lateral — Milliken two-spring (SUS-103) | Transferência Lateral — Milliken, três massas, com termo gravitacional (SUS-103) | EDR-046 |
| 09_LOADS | A18 | Altura do roll axis no CG (z_s) | Altura do roll axis no CG suspenso (z_s, em a_s) | EDR-047 |
| 09_LOADS | B18 | `=('05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6)*'06_SUSPENSION'!$B$14+('05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6)*'06_SUSPENSION'!$B$15` | `='06_SUSPENSION'!$B$14+('06_SUSPENSION'!$B$15-'06_SUSPENSION'!$B$14)*'05_VEHICLE'!$B$27/'05_VEHICLE'!$B$6` | EDR-047; Milliken p. 603 |
| 09_LOADS | B19 | `=('08_VEHICLE_STATE'!$B$5/'05_VEHICLE'!$B$7)*('06_SUSPENSION'!$B$24*'05_VEHICLE'!$B$23*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)+('05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6)*'05_VEHICLE'!$B$23*'06_SUSPENSION'!$B$14+'05_VEHICLE'!$B$14*'05_VEHICLE'!$B$16)` | `=IF(ISNUMBER('09_LOADS'!$B$21),('06_SUSPENSION'!$B$22*'09_LOADS'!$B$21+'08_VEHICLE_STATE'!$B$5*('05_VEHICLE'!$B$25*'06_SUSPENSION'!$B$14+'05_VEHICLE'!$B$14*'05_VEHICLE'!$B$16))/'05_VEHICLE'!$B$7,"N/A")` | EDR-046/047; Milliken p. 604 e p. 682 |
| 09_LOADS | B20 | `=('08_VEHICLE_STATE'!$B$5/'05_VEHICLE'!$B$8)*('06_SUSPENSION'!$B$25*'05_VEHICLE'!$B$23*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)+('05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6)*'05_VEHICLE'!$B$23*'06_SUSPENSION'!$B$15+'05_VEHICLE'!$B$15*'05_VEHICLE'!$B$17)` | `=IF(ISNUMBER('09_LOADS'!$B$21),('06_SUSPENSION'!$B$23*'09_LOADS'!$B$21+'08_VEHICLE_STATE'!$B$5*('05_VEHICLE'!$B$26*'06_SUSPENSION'!$B$15+'05_VEHICLE'!$B$15*'05_VEHICLE'!$B$17))/'05_VEHICLE'!$B$8,"N/A")` | EDR-046/047; Milliken p. 604 e p. 682 |
| 09_LOADS | A21 | (vazia) | Ângulo de rolagem φ = m_s·a_y·h2/(K_φF+K_φR − m_s·g·h2) (+ = para fora da curva) | EDR-046 |
| 09_LOADS | B21 | (vazia) | `=IF('06_SUSPENSION'!$B$22+'06_SUSPENSION'!$B$23-'05_VEHICLE'!$B$23*9.81*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)<=0,"N/A - instabilidade de rolagem (m_s·g·h2 >= K_φ, Milliken p. 682)",'05_VEHICLE'!$B$23*'08_VEHICLE_STATE'!$B$5*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)/('06_SUSPENSION'!$B$22+'06_SUSPENSION'!$B$23-'05_VEHICLE'!$B$23*9.81*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)))` | EDR-046; Milliken p. 682; Gillespie eq. 6-31 |
| 09_LOADS | C21 | (vazia) | rad | EDR-046 |
| 09_LOADS | D21 | (vazia) | SUS-103 | EDR-046 |
| 11_DESIGN | A7 | Rigidez necessária (equação reversa, SUS-202/205) | Rigidez necessária (equação reversa, SUS-205/212/202; pneu em série) | EDR-045 |
| 11_DESIGN | A8 | Wheel Rate necessário - dianteira | Wheel Rate necessário - dianteira (K_R alvo -> K_W = K_R·K_T/(K_T − K_R)) | EDR-045 |
| 11_DESIGN | B8 | `=(2*PI()*'11_DESIGN'!$B$4)^2*'06_SUSPENSION'!$B$28` | `=(2*PI()*'11_DESIGN'!$B$4)^2*'06_SUSPENSION'!$B$28*'06_SUSPENSION'!$B$47/('06_SUSPENSION'!$B$47-(2*PI()*'11_DESIGN'!$B$4)^2*'06_SUSPENSION'!$B$28)` | EDR-045; Milliken p. 591; Seward eq. 4.4 |
| 11_DESIGN | A9 | Wheel Rate necessário - traseira | Wheel Rate necessário - traseira (K_R alvo -> K_W = K_R·K_T/(K_T − K_R)) | EDR-045 |
| 11_DESIGN | B9 | `=(2*PI()*'11_DESIGN'!$B$5)^2*'06_SUSPENSION'!$B$29` | `=(2*PI()*'11_DESIGN'!$B$5)^2*'06_SUSPENSION'!$B$29*'06_SUSPENSION'!$B$48/('06_SUSPENSION'!$B$48-(2*PI()*'11_DESIGN'!$B$5)^2*'06_SUSPENSION'!$B$29)` | EDR-045; Milliken p. 591; Seward eq. 4.4 |
| 11_DESIGN | A20 | K_ARB dianteiro necessário | K_ARB dianteiro necessário (com o pneu em série) | EDR-045 |
| 11_DESIGN | B20 | `='11_DESIGN'!$B$19-'06_SUSPENSION'!$B$20` | `='11_DESIGN'!$B$19*'06_SUSPENSION'!$B$51/('06_SUSPENSION'!$B$51-'11_DESIGN'!$B$19)-'06_SUSPENSION'!$B$20` | EDR-045; Milliken p. 592 |
| 13_VALIDATION | A6 | TC-005: t_F*dFzF + t_R*dFzR - m*ay*h_CG [deve ser ~0] | TC-005: t_F*dFzF + t_R*dFzR - m*ay*h_CG - m_s*g*h2*φ [deve ser ~0] | EDR-046 |
| 13_VALIDATION | B6 | `='05_VEHICLE'!$B$7*'09_LOADS'!$B$19+'05_VEHICLE'!$B$8*'09_LOADS'!$B$20-'05_VEHICLE'!$B$4*'08_VEHICLE_STATE'!$B$5*'05_VEHICLE'!$B$5` | `='05_VEHICLE'!$B$7*'09_LOADS'!$B$19+'05_VEHICLE'!$B$8*'09_LOADS'!$B$20-'05_VEHICLE'!$B$4*'08_VEHICLE_STATE'!$B$5*'05_VEHICLE'!$B$5-'05_VEHICLE'!$B$23*9.81*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)*'09_LOADS'!$B$21` | EDR-046; Milliken p. 682-683 |
| 13_VALIDATION | A26 | Piloto de referência: MR=0.8, Ks=100 N/mm, ms=50 kg -> fn=8.897 Hz (verificado) | Piloto de referência: MR=0.8, Ks=100 N/mm, ms=50 kg, pneu rígido -> fn=8.897 Hz (verificado) | EDR-045 |
| 10_TIRE | A56 | Ky = PKY1·F'z0·sin(2·atan(Fz/(PKY2·F'z0)))·(1−PKY3·\|γy\|)·LFZO·LKY | Ky = PKY1·F'z0·sin(2·atan(Fz/(PKY2·F'z0)))·(1−PKY3·\|γy\|)·LKY  (um λFz0, EDR-049) | EDR-049 |
| 10_TIRE | B56 | `=IF(B$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(B$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(B$55))*$B$97*$B$108)` | `=IF(B$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(B$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(B$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | C56 | `=IF(C$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(C$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(C$55))*$B$97*$B$108)` | `=IF(C$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(C$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(C$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | D56 | `=IF(D$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(D$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(D$55))*$B$97*$B$108)` | `=IF(D$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(D$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(D$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | E56 | `=IF(E$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(E$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(E$55))*$B$97*$B$108)` | `=IF(E$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(E$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(E$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | F56 | `=IF(F$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(F$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(F$55))*$B$97*$B$108)` | `=IF(F$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(F$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(F$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 06_SUSPENSION | B4 (comentário) | Back-calculado da planilha detalhada T09 ('Ride Rate' front=16112.23 N/m, confirmado ser exatamente o Wheel Rate) x MR=1.76. CORRIGE valor anterior (baseado no spec sheet resumido, que arredondava F/R como iguais). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Back-calculado da planilha detalhada T09 ('Ride Rate' front=16112.23 N/m, confirmado ser exatamente o Wheel Rate) x MR=1.76. CORRIGE valor anterior (baseado no spec sheet resumido, que arredondava F/R como iguais). | EDR-012/022 |
| 06_SUSPENSION | B5 (comentário) | Back-calculado da planilha detalhada T09 ('Ride Rate' rear=18418.2 N/m) x MR=1.76. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Back-calculado da planilha detalhada T09 ('Ride Rate' rear=18418.2 N/m) x MR=1.76. | EDR-012/022 |
| 06_SUSPENSION | B6 (comentário) | Fonte: E03 (1.76:1). Assumido como convencao wheel/spring (igual a nossa) - E03 nao especifica a direcao explicitamente. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (1.76:1). Assumido como convencao wheel/spring (igual a nossa) - E03 nao especifica a direcao explicitamente. | EDR-012/022 |
| 06_SUSPENSION | B7 (comentário) | Fonte: E03 (1.76:1, mesmo valor da dianteira). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (1.76:1, mesmo valor da dianteira). | EDR-012/022 |
| 06_SUSPENSION | B10 (comentário) | Fonte: planilha detalhada T09 (AntiRoll Bar Rate front). Valor direto, ja nao e mais back-calculado - resolve a inconsistencia identificada anteriormente. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (AntiRoll Bar Rate front). Valor direto, ja nao e mais back-calculado - resolve a inconsistencia identificada anteriormente. | EDR-012/022 |
| 06_SUSPENSION | B11 (comentário) | Fonte: planilha detalhada T09 (AntiRoll Bar Rate rear, ~0, consistente com 'sem ARB' declarado). Inconsistencia anterior estava no Wheel Rate do spec sheet resumido, ja corrigida em SUS-203. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (AntiRoll Bar Rate rear, ~0, consistente com 'sem ARB' declarado). Inconsistencia anterior estava no Wheel Rate do spec sheet resumido, ja corrigida em SUS-203. | EDR-012/022 |
| 06_SUSPENSION | B14 (comentário) | Fonte: planilha detalhada T09 (0.0675m) - mais precisa que o spec sheet resumido do E03 (60mm, arredondado). PROVISORIO ate Fase 2 (OptimumKinematics). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (0.0675m) - mais precisa que o spec sheet resumido do E03 (60mm, arredondado). PROVISORIO ate Fase 2 (OptimumKinematics). | EDR-012/022 |
| 06_SUSPENSION | B15 (comentário) | Fonte: E03 (110mm, Roll center height above ground static). PROVISORIO ate Fase 2 (OptimumKinematics). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (110mm, Roll center height above ground static). PROVISORIO ate Fase 2 (OptimumKinematics). | EDR-012/022 |
| 10_TIRE | B16 | (texto V2.4) | (texto V2.5) | EDR-042/049 |
| 00_README | A3 | Versão do workbook: V2.4 ... | Versão do workbook: V2.5 ... | EDR-043 |
| 15_CHANGELOG | A16:C16 | (vazia) | (linha V2.5) | EDR-043 |
