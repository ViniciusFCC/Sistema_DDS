# Engineering Standard V2.0 — FSAE EV Suspension System

**Atualização V3.0 (2026-10-19):** revisão metodológica contra Milliken, Gillespie, Seward e Pacejka (`docs/revisao-metodologica.md`; EDR-045 a EDR-049). Fichas alteradas: SUS-009, 103, 205, 206, 207, 208, 301, 302, 406 e 501; novas: SUS-211 e SUS-212. Onde uma ficha abaixo diz o contrário, vale a forma V3.0.

**Atualização V3.0, 2ª rodada da revisão metodológica (2026-10-19):** SUS-010 e SUS-011 ganham a forma da planilha (razão h_u / raio como entrada, EDR-050). Direção (cap. 19 da Milliken; EDR-052): fichas novas SUS-414 (Ackermann), SUS-415 (roll steer) e SUS-416 (efeitos do esterço pelo pino mestre); SUS-408, 410, 413 e 601 revistas. SUS-412 ganha a definição primária pela linha de força (EDR-053). Textos de célula N/A e TBD (EDR-035, aprovados): **N/A** = não se aplica, ou não dá para calcular na configuração atual (sem número inventado); **TBD** = dado, meta, requisito ou decisão pendente (Lifecycle OPEN). Não são estados novos.

**Versão:** V2.0 (2026-10-09). Base: `engineering-standard-V1.0`. Alterações desta versão: Bloco E.2 (SUS-407 a SUS-413, solver cinemático 3D), notas de achados em SUS-406/SUS-301/SUS-302, log de validação V2.0. Ver `registro-de-versoes-V2.0.md`.
**Numeração de Test Cases (decisão do usuário, 2026-10-09):** canônica = a da arquitetura (seção 17.7), deste Standard e do Python (`TC-001` a `TC-012`); os casos de kinematics usam o namespace próprio `TC-KIN-xxx`. A numeração do Guide (Apêndice D) diverge e deve ser alinhada a esta.

Primeiras 8 fichas (Blocos A, B, C, D da ordem definida). Cada ficha segue o template da seção 14 do documento de arquitetura consolidada. Status inicial de todas: `Lifecycle = DRAFT`, `Validation = NOT_VALIDATED` — passam a `CHECKED`/`PASS` só depois de rodar os Test Cases correspondentes.

---

## SUS-001 — Vehicle Mass

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Massa total do veículo na condição de setup especificada, incluindo piloto (conforme regulamento FSAE). Deve ser declarada por Setup, não como valor único do projeto. |
| Equation | `m = m_car + m_driver` (soma direta; não é um cálculo, é a massa medida/declarada) |
| Variables | `m` [kg] |
| Units | kg (SI e interface — sem conversão necessária) |
| Sign Convention | N/A (escalar positivo) |
| Assumptions | Massa constante durante a manobra (hipótese quase-estática; sem consumo de energia/deslocamento de bateria modelado) |
| Reference/Source | Medição em balança calibrada, ou CAD mass properties como estimativa provisória |
| Validity Domain | Válido apenas para o Setup em que foi medido/declarado |
| Data Type | INPUT |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de veículo/pesagem |
| Revision | Setup-specific (`S-XXX`) |
| Validation Method | Comparação com pesagem em balança calibrada |

---

## SUS-002 — CG Height

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Altura do centro de gravidade do veículo completo, medida a partir do **plano do solo** (não da origem estrutural do CAD). |
| Equation | `h_CG = Σ(m_i · z_i) / Σm_i` (soma ponderada por componente) ou obtida diretamente por tilt-table test |
| Variables | `h_CG` [m]; `m_i`, `z_i` por componente, se calculado por soma |
| Units | m internamente; mm na interface |
| Sign Convention | Positivo para cima a partir do solo |
| Assumptions | Veículo em repouso, sobre superfície plana e nivelada, na condição de ride height do Setup |
| Reference/Source | Tilt-table test, ou soma de massas/alturas de componentes (CAD) como estimativa provisória |
| Validity Domain | Válido apenas no ride height estático do Setup declarado |
| Data Type | INPUT (tilt-table) ou MODEL (soma de componentes) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de veículo/dinâmica |
| Revision | Setup-specific |
| Validation Method | Comparação tilt-table vs. soma de componentes (cross-check interno) |

**⚠️ Gap encontrado ao escrever esta ficha:** a origem do sistema de coordenadas (seção 4 do documento consolidado) é um ponto estrutural do CAD, **não necessariamente o plano do solo**. Se a origem não estiver no solo, é preciso um offset documentado: `Z_ground = Z_origin − Z_ground_offset`. Sem isso, `h_CG` (e, mais adiante, `h_s`, `h_uF`, `h_uR` do modelo de Milliken) fica ambíguo entre "altura acima da origem do CAD" e "altura acima do solo" — que são fisicamente diferentes e a fórmula de load transfer exige a segunda. Recomendo congelar este offset como `SUS-000` (Ground Plane Reference) antes de qualquer ficha de load transfer entrar em `CHECKED`.

---

## SUS-003 — Wheelbase

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Distância longitudinal entre os eixos dianteiro e traseiro, medida entre os centros das rodas em vista lateral, no ride height de referência. |
| Equation | `L = abs(X_rear_axle − X_front_axle)` (a partir dos hardpoints/wheel centers) |
| Variables | `L` [m] |
| Units | m internamente; mm na interface |
| Sign Convention | Escalar positivo; eixo X conforme ISO 8855 (seção 4) |
| Assumptions | `L` tratado como constante no ride height estático — variação real de wheelbase com o curso de suspensão (efeito de camber/caster) não é modelada na V1 |
| Reference/Source | CAD (Master Geometry) |
| Validity Domain | Válido no KOP de ride height estático |
| Data Type | REFERENCE (hardpoints.csv) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV (`G-REV-X`) |
| Validation Method | Comparação hardpoints.csv vs. medição física do chassi |

---

## SUS-101 — Static Fz (por canto)

| Campo | Conteúdo |
|---|---|
| Domain | Loads (Bloco B) |
| Definition | Carga vertical estática em cada canto (FL/FR/RL/RR), sem manobra (`a_x = a_y = 0`), assumindo simetria lateral perfeita. |
| Equation | `W_f = m·g·(b/L)`; `W_r = m·g·(a/L)`; por canto: `Fz_FL = Fz_FR = W_f/2`; `Fz_RL = Fz_RR = W_r/2`, onde `a` = distância longitudinal do CG ao eixo dianteiro, `b` = distância do CG ao eixo traseiro, `a+b=L` |
| Variables | `m` [kg], `g` = 9,81 m/s², `a`, `b`, `L` [m] |
| Units | N (SI); daN ou kgf na interface, se preferido pela equipe |
| Sign Convention | Fz positivo para cima (reação do solo no pneu) |
| Assumptions | Simetria lateral de massa perfeita (sem offset lateral de CG); superfície plana e nivelada |
| Reference/Source | Equilíbrio de corpo rígido — Milliken, RCVD, cap. de static loads |
| Validity Domain | Repouso, sem aceleração |
| Data Type | MODEL |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV (`D-REV-X`) |
| Validation Method | TC-004 (`ΣFz = W`); comparação com pesagem em 4 balanças de canto, se disponível |

**⚠️ Gap encontrado ao escrever esta ficha:** `a` e `b` dependem da **posição longitudinal do CG**, que não tem ID próprio na Dependency Matrix atual — ela lista "CG longitudinal" como dependência solta, sem parâmetro formalizado. Recomendo criar **`SUS-006` — CG Longitudinal Position** (Data Type: INPUT, medido por pesagem em balanças dianteira/traseira ou por soma de componentes) antes de congelar esta ficha como `CHECKED`.

---

## SUS-102 — Longitudinal ΔFz

| Campo | Conteúdo |
|---|---|
| Domain | Loads (Bloco C) |
| Definition | Transferência de carga longitudinal decorrente do equilíbrio de corpo rígido durante aceleração/frenagem. |
| Equation | `ΔFz_front = −m·a_x·h_CG/L`; `ΔFz_rear = +m·a_x·h_CG/L` (por eixo); por canto, dividir por 2 assumindo simetria lateral |
| Variables | `m` [kg], `a_x` [m/s²], `h_CG` [m], `L` [m] |
| Units | N (SI) |
| Sign Convention | `a_x` positivo = aceleração para frente (+X, ISO 8855). `a_x > 0` transfere carga para o eixo traseiro; `a_x < 0` (frenagem) transfere para o dianteiro |
| Assumptions | Quase-estático (sem resposta transiente de pitch modelada); não inclui a partição geométrica/elástica de anti-dive/anti-squat — esta fórmula dá a **magnitude total**, que `SUS-301`/`SUS-302` nunca alteram (ver seção 17.3/17.4 do documento de arquitetura) |
| Reference/Source | Milliken, RCVD — longitudinal load transfer |
| Validity Domain | Quase-estático; requer `h_CG` medido a partir do solo (ver gap de `SUS-002`) |
| Data Type | MODEL |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV |
| Validation Method | TC-002 (`a_x=0 → ΔFz=0`), TC-003 (simetria), comparação com solução analítica de corpo livre |

---

## SUS-201 — Motion Ratio (`MR_RH`)

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D) |
| Definition | Razão entre o deslocamento da roda e o deslocamento da mola, avaliada no ride height de referência. Convenção: `MR [wheel/spring]`. |
| Equation | `MR_RH = Δx_wheel / Δx_spring` |
| Variables | `Δx_wheel`, `Δx_spring` [mm ou m, mesma unidade] |
| Units | Adimensional |
| Sign Convention | `MR > 0` sempre (razão de magnitudes); nunca escrever só "MR" — sempre `MR [wheel/spring]` em Excel/Python (`motion_ratio_wheel_spring`) |
| Assumptions | Avaliado em um único ponto (ride height estático); `MR(z)` real varia ao longo do curso em geometrias push-rod/rocker — não modelado na V1 |
| Reference/Source | OptimumKinematics (REFERENCE); geometria local do linkage (MODEL/cross-check) |
| Validity Domain | Válido apenas no ride height de referência |
| Data Type | REFERENCE (oficial) + MODEL (cross-check, nunca substitui o REFERENCE) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (`K-REV-X`) |
| Validation Method | TC-009 (`MR=1 → Kw=Ks`), TC-011 (comparação direta com OptimumKinematics) |

---

## SUS-202 — Wheel Rate

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D) |
| Definition | Rigidez vertical equivalente na roda, resultante da mola atuando através da razão de movimento. |
| Equation (Analysis Mode) | `K_wheel = K_spring / MR_RH²` |
| Equation (Design Mode — reverso) | `K_spring = K_wheel · MR_RH²`, usado quando `K_wheel` vem de um cálculo de frequência-alvo (`SUS-205` invertido) |
| Variables | `K_spring`, `K_wheel` [N/mm ou N/m], `MR_RH` [adimensional] |
| Units | N/m (SI); N/mm na interface |
| Sign Convention | N/A (rigidezes positivas) |
| Assumptions | `MR_RH` tratado como constante local (pequenos deslocamentos em torno do ride height) |
| Reference/Source | Relação padrão de motion ratio — consistente com `SUS-201` |
| Validity Domain | Pequenos deslocamentos em torno do ride height |
| Data Type | MODEL (Analysis: `K_spring` é INPUT, `K_wheel` calculado; Design: `K_wheel` vem de `SUS-205`, `K_spring` calculado) |
| Target/Requirement | Ligado a `TARGET-XXX` quando em Design Mode |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | TC-009, comparação com cálculo manual (piloto end-to-end) |

---

## SUS-205 — Natural Frequency

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D) |
| Definition | Frequência natural não-amortecida do sistema massa-mola de um canto da suspensão (modelo simplificado de 1 grau de liberdade). |
| Equation (Analysis Mode) | **V3.0 (EDR-045):** `f_n = (1/2π)·√(K_R / m_sprung,corner)`, com a ride rate `K_R = SUS-212` (mola na roda em série com o pneu) |
| Equation (Design Mode — reverso) | **V3.0:** `K_R = (2π·f_target)²·m_sprung,corner`; `K_wheel = K_R·K_T/(K_T − K_R)` (exige `K_T > K_R`) |
| Variables | `K_wheel` [N/m], `m_sprung,corner` [kg] |
| Units | Hz |
| Sign Convention | N/A |
| Assumptions | Sistema massa-mola de 1 GDL, sem amortecimento, **sem acoplamento com outros cantos/eixos** (não modela modos de ride/pitch/roll do veículo completo — limitação conhecida e documentada da V1) |
| Reference/Source | Gillespie eq. 5-8/5-9 (p. 148); Seward eq. 4.1, 4.2 e 4.4 (p. 95-97); Milliken p. 588, 591 e 601 |
| Validity Domain | Pequenas oscilações em torno do ride height; `MR_RH` constante |
| Data Type | MODEL (Analysis) / MODEL calculado a partir de `TARGET-XXX` (Design) |
| Target/Requirement | `TARGET-XXX` (ex.: "frequência dianteira-alvo = 2,5 Hz") quando em Design Mode |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | TC-010 (cálculo inverso retorna exatamente `f_target`); piloto end-to-end (`MR=0.8`, `Ks=100 N/mm`, `ms=50 kg` → `fn≈8.90 Hz`, já verificado) |

**⚠️ Gap encontrado ao escrever esta ficha:** `m_sprung,corner` (massa suspensa por canto — **não** a massa total do canto, exclui roda/manga de eixo/parcela não-suspensa da suspensão) também não tem ID próprio. Ela depende de massa total (`SUS-001`), distribuição estática (`SUS-101`, que por sua vez depende do gap de `SUS-006` acima) e das massas não-suspensas por eixo, que também não têm ID. Recomendo criar **`SUS-007` — Front Unsprung Mass**, **`SUS-008` — Rear Unsprung Mass** (ambos INPUT) e **`SUS-009` — Sprung Mass per Corner** (CALCULATED, derivado de `SUS-001`, `SUS-006`, `SUS-007`, `SUS-008`) antes de `SUS-205` poder ser considerado `CHECKED`.

---

## SUS-000 — Ground Plane Reference

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle / Reference Frame (Bloco A) |
| Definition | Coordenada Z (no sistema de coordenadas da equipe, seção 4) do plano do solo/superfície de rolagem, no ride height do Setup. Resolve a ambiguidade entre "altura a partir da origem do CAD" e "altura a partir do solo", necessária para `h_CG`, `h_s`, `h_uF`, `h_uR`. |
| Equation | `h_above_ground(ponto) = Z_ponto,CAD − SUS-000` |
| Variables | `SUS-000 = Z_ground` [m] — normalmente **negativo**, já que a origem do CAD (seção 4) fica acima do solo |
| Units | m internamente; mm na interface |
| Sign Convention | Segue o eixo Z da seção 4 (positivo para cima); solo abaixo da origem ⇒ `Z_ground < 0` |
| Assumptions | Solo plano e nivelado sob o veículo (sem inclinação de pista modelada); válido apenas no ride height do Setup — muda se o ride height mudar |
| Reference/Source | Medição direta (da origem definida no CAD até o solo, carro no ride height de referência) ou CAD com pneus/rodas corretamente dimensionados |
| Validity Domain | Ride height do Setup declarado |
| Data Type | INPUT (medido) ou REFERENCE (se do CAD) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão/veículo |
| Revision | Geometry REV |
| Validation Method | Comparação entre medição física e valor do CAD |

---

## SUS-006 — CG Longitudinal Position

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Posição longitudinal do CG, expressa como `a` (distância do CG ao eixo dianteiro) e `b` (distância do CG ao eixo traseiro), com `a+b=L` (`SUS-003`). |
| Equation | `b = (W_f_medido/W_total)·L`; `a = (W_r_medido/W_total)·L = L−b` |
| Variables | `W_f_medido`, `W_r_medido` [N] (pesagem em balanças de eixo), `W_total = W_f+W_r`, `L` (`SUS-003`) |
| Units | m internamente; mm na interface |
| Sign Convention | `a`, `b` sempre positivos, medidos ao longo de X |
| Assumptions | Veículo nivelado durante a pesagem; simetria lateral (não captura offset lateral de CG) |
| Reference/Source | Pesagem em balanças dianteira/traseira (INPUT); soma de componentes do CAD como estimativa provisória (MODEL) |
| Validity Domain | Ride height/Setup em que a pesagem foi feita |
| Data Type | INPUT (pesagem) / MODEL (estimativa por CAD) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de veículo/pesagem |
| Revision | Setup-specific |
| Validation Method | Checagem `a+b=L`; cross-check pesagem vs. soma de componentes do CAD |

**Nota importante para o Bloco F (Milliken):** o modelo de transferência lateral usa `a/L` e `b/L` também para posicionar o termo geométrico da massa suspensa (`(b/L)·m_s·z_F`, `(a/L)·m_s·z_R`). A V1 usa a posição do CG **total** (`SUS-006`) como aproximação da posição longitudinal do CG da massa **suspensa** especificamente — são fisicamente diferentes (a massa não-suspensa tem seu próprio CG, geralmente perto das rodas), mas a diferença costuma ser pequena em carros FSAE porque a massa não-suspensa é uma fração pequena do total. **Isso deve constar como hipótese explícita na ficha de `SUS-103` (Milliken) quando ela for escrita — é uma aproximação conhecida, não um erro, mas precisa estar documentada.**

---

## SUS-007 — Front Unsprung Mass

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Massa não-suspensa total do eixo dianteiro (as duas rodas: pneu, roda, manga de eixo, freio, e a parcela de braços de suspensão atribuída como não-suspensa). |
| Equation | `m_uF` = soma direta dos componentes não-suspensos dianteiros |
| Variables | `m_uF` [kg] |
| Units | kg |
| Sign Convention | N/A |
| Assumptions | **Precisa ser congelada uma convenção de partição para braços de suspensão** (prática comum: metade da massa de cada braço conta como não-suspensa, metade como suspensa) — sem essa convenção documentada, duas pessoas da equipe podem chegar a `m_uF` diferentes com a mesma peça física |
| Reference/Source | Pesagem/estimativa de componentes (catálogo de peças + CAD) |
| Validity Domain | Válido para a configuração de suspensão do Setup declarado |
| Data Type | INPUT |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | Comparação entre soma de componentes e pesagem direta (roda+pneu+manga desmontados), quando possível |

---

## SUS-008 — Rear Unsprung Mass

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Análogo a `SUS-007`, para o eixo traseiro. Em veículos com motor/redução no cubo ou próximo a ele, avaliar se esses componentes contam como não-suspensos. |
| Equation | `m_uR` = soma direta dos componentes não-suspensos traseiros |
| Variables | `m_uR` [kg] |
| Units | kg |
| Sign Convention | N/A |
| Assumptions | Mesma convenção de partição de braços definida em `SUS-007`, aplicada de forma consistente |
| Reference/Source | Pesagem/estimativa de componentes |
| Validity Domain | Configuração de suspensão do Setup declarado |
| Data Type | INPUT |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | Comparação entre soma de componentes e pesagem direta |

---

## SUS-009 — Sprung Mass per Corner

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D) |
| Definition | Massa suspensa associada a um canto específico, usada diretamente em `SUS-205` (frequência natural). |
| Equation | `m_sprung,total = SUS-001 − SUS-007 − SUS-008`; **V3.0 (EDR-047):** por eixo, `m_sprung,front = m·b/L − m_uF` e `m_sprung,rear = m·a/L − m_uR`; CG suspenso a `a_s = L·m_sprung,rear/m_sprung,total` do eixo dianteiro; por canto (simetria lateral): `m_sprung,corner = m_sprung,front/2` ou `m_sprung,rear/2` |
| Variables | `SUS-001`, `SUS-007`, `SUS-008`, `a`, `b`, `L` (`SUS-006`, `SUS-003`) |
| Units | kg |
| Sign Convention | N/A |
| Assumptions | Distribuição longitudinal da massa suspensa aproximada pela mesma fração `a/L`, `b/L` da massa total (mesma aproximação documentada em `SUS-006`); simetria lateral perfeita |
| Reference/Source | Milliken p. 601 (Tab. 16.3: W_SF = W_F − W_UF) e p. 602-603; Seward eq. 5.14. Hipótese: CG não suspenso sobre o eixo |
| Validity Domain | Mesma do Setup/ride height das massas de origem |
| Data Type | CALCULATED |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | Checagem `m_sprung,front + m_sprung,rear = m_sprung,total`; TC-008 do modelo de Milliken (zerar massa não-suspensa) usa este mesmo `m_sprung,total` como referência cruzada |

---

## Bloco F — Transferência Lateral de Carga (Milliken)

### SUS-004 — Front Track

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Distância lateral entre os centros das rodas dianteiras, no ride height de referência. |
| Equation | `t_F = abs(Y_FL − Y_FR)` (a partir dos hardpoints/wheel centers) |
| Variables | `t_F` [m] |
| Units | m internamente; mm na interface |
| Sign Convention | Escalar positivo; eixo Y conforme ISO 8855 |
| Assumptions | Tratado como constante no ride height estático (variação com curso/camber não modelada na V1) |
| Reference/Source | CAD (Master Geometry) |
| Validity Domain | Válido no KOP de ride height estático |
| Data Type | REFERENCE (hardpoints.csv) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | Comparação hardpoints.csv vs. medição física |

### SUS-005 — Rear Track

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Distância lateral entre os centros das rodas traseiras, no ride height de referência. |
| Equation | `t_R = abs(Y_RL − Y_RR)` (a partir dos hardpoints/wheel centers) |
| Variables | `t_R` [m] |
| Units | m internamente; mm na interface |
| Sign Convention | Escalar positivo; eixo Y conforme ISO 8855 |
| Assumptions | Tratado como constante no ride height estático (variação com curso/camber não modelada na V1) |
| Reference/Source | CAD (Master Geometry) |
| Validity Domain | Válido no KOP de ride height estático |
| Data Type | REFERENCE (hardpoints.csv) |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | Comparação hardpoints.csv vs. medição física |

---

### SUS-010 — Front Unsprung CG Height

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Altura do CG da massa não-suspensa dianteira (`h_uF`) acima do solo. Aproximação usual: próxima da altura do centro da roda, ajustada pela massa de manga de eixo/freio/parcela de braços. |
| Equation | `h_uF` = estimado por componente ou aproximado pela altura do centro da roda dianteira |
| Planilha V3.0 (2ª rodada da revisão metodológica, EDR-050) | `= B33·0,0254/2 · B35` (05_VEHICLE): raio sem carga do pneu × razão h_u / raio (B35, entrada, ○ Estimativa, 1,0). Milliken p. 672: a altura do centro da roda é "boa primeira aproximação" (o livro usa o raio carregado). A altura do centro da roda em si não sai desta ficha (07_KINEMATICS B14 usa o raio direto). |
| Units | m internamente; mm na interface |
| Sign Convention | Medido a partir do solo (`SUS-000`), não da origem do CAD |
| Assumptions | Mesma convenção de partição de braços de suspensão definida em `SUS-007` |
| Reference/Source | Estimativa por componente (CAD) ou aproximação pelo raio da roda |
| Data Type | INPUT |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | Comparação entre estimativa por componente e aproximação simplificada (raio da roda) |

### SUS-011 — Rear Unsprung CG Height

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Altura do CG da massa não-suspensa traseira (`h_uR`) acima do solo. Aproximação usual: próxima da altura do centro da roda, ajustada pela massa de manga de eixo/freio/parcela de braços (e, se aplicável, componentes de trem de força próximos ao cubo). |
| Equation | `h_uR` = estimado por componente ou aproximado pela altura do centro da roda traseira |
| Planilha V3.0 (2ª rodada da revisão metodológica, EDR-050) | `= B34·0,0254/2 · B36` (05_VEHICLE): raio sem carga do pneu × razão h_u / raio (B36, entrada, ○ Estimativa, 1,0). Milliken p. 672: a altura do centro da roda é "boa primeira aproximação" (o livro usa o raio carregado). A altura do centro da roda em si não sai desta ficha (07_KINEMATICS B14 usa o raio direto). |
| Variables | `h_uR` [m] |
| Units | m internamente; mm na interface |
| Sign Convention | Medido a partir do solo (`SUS-000`), não da origem do CAD |
| Assumptions | Mesma convenção de partição de braços de suspensão definida em `SUS-008` |
| Reference/Source | Estimativa por componente (CAD) ou aproximação pelo raio da roda |
| Data Type | INPUT |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | Comparação entre estimativa por componente e aproximação simplificada (raio da roda) |

---

### SUS-012 — Sprung Mass CG Height

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle (Bloco A) |
| Definition | Altura do CG **apenas da massa suspensa** (`h_s`) — diferente de `SUS-002`, que é a altura do CG do veículo completo. |
| Equation | `h_s = (SUS-001 · SUS-002 − SUS-007 · SUS-010 − SUS-008 · SUS-011) / m_sprung,total`, onde `m_sprung,total` é a primeira etapa de cálculo de `SUS-009` (massa suspensa total, antes da distribuição por canto) |
| Variables | `SUS-001, 002, 007, 008, 010, 011`, `m_sprung,total` |
| Units | m internamente; mm na interface |
| Sign Convention | Medido a partir do solo (`SUS-000`) |
| Assumptions | Decorre diretamente da definição de CG composto — não é uma equação de literatura nova, é a mesma identidade verificada algebricamente na seção 17.4 do documento de arquitetura (`m_s·h_s + m_uF·h_uF + m_uR·h_uR = m·h_CG`), isolando `h_s` |
| Reference/Source | Derivado (identidade de CG composto) |
| Data Type | CALCULATED |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV |
| Validation Method | Checagem reversa: `SUS-001·SUS-002 = m_sprung,total·h_s + SUS-007·SUS-010 + SUS-008·SUS-011` deve fechar exatamente |

---

### SUS-206 — Front Roll Stiffness (`K_φF`)

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D, revisado) |
| Definition | Rigidez de rolagem do eixo dianteiro (momento por ângulo de rolagem), incluindo contribuição da mola (via wheel rate) e do anti-roll bar. |
| Equation | **V3.0 (EDR-045):** `K_φF = série(K_wheel,F·t_F²/2 + K_ARB,F ; K_T,F·t_F²/2)`, `série(x;y) = x·y/(x+y)`. Forma V2.4 (sem pneu): `K_φF = (K_wheel,F · t_F²) / 2 + K_ARB,F`, onde `K_ARB,F` é um input simplificado da contribuição do ARB (V1 não modela a cinemática interna da barra — se não houver ARB, `K_ARB,F = 0`) |
| Variables | `K_wheel,F` (`SUS-202`, avaliado no canto dianteiro), `t_F` (`SUS-004`), `K_ARB,F` [N·m/rad] |
| Units | N·m/rad (SI); N·m/° na interface, se preferido |
| Sign Convention | N/A (rigidez positiva) |
| Assumptions | ARB tratado como rigidez adicional simplificada (input direto), sem modelar motion ratio próprio da barra — simplificação deliberada da V1, documentada aqui explicitamente |
| Reference/Source | Gillespie eq. 6-26 (p. 211-212); Milliken p. 589-592 (barra referida à roda, pneu em série) e p. 680; Seward eq. 4.5 |
| Data Type | MODEL (parte spring) + INPUT (parte ARB) |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | Comparação com cálculo manual; TC-006 (alterar distribuição mantendo total constante); TC-SUS-V30-004/005 (Milliken p. 592) |

### SUS-207 — Rear Roll Stiffness (`K_φR`)

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D, revisado) |
| Definition | Rigidez de rolagem do eixo traseiro (momento por ângulo de rolagem), incluindo contribuição da mola (via wheel rate) e do anti-roll bar. |
| Equation | **V3.0 (EDR-045):** `K_φR = série(K_wheel,R·t_R²/2 + K_ARB,R ; K_T,R·t_R²/2)`. Forma V2.4 (sem pneu): `K_φR = (K_wheel,R · t_R²) / 2 + K_ARB,R`, onde `K_ARB,R` é um input simplificado da contribuição do ARB (V1 não modela a cinemática interna da barra — se não houver ARB, `K_ARB,R = 0`) |
| Variables | `K_wheel,R` (`SUS-202`, avaliado no canto traseiro), `t_R` (`SUS-005`), `K_ARB,R` [N·m/rad] |
| Units | N·m/rad (SI); N·m/° na interface, se preferido |
| Sign Convention | N/A (rigidez positiva) |
| Assumptions | Mesma simplificação de ARB documentada em `SUS-206` |
| Reference/Source | Gillespie eq. 6-26; Milliken p. 589-592 e p. 680; Seward eq. 4.5 |
| Data Type | MODEL (parte spring) + INPUT (parte ARB) |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | Comparação com cálculo manual; TC-006 (alterar distribuição mantendo total constante) |

### SUS-208 — Roll Stiffness Distribution (`λ_f`, `λ_r`)

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness (Bloco D, revisado) |
| Definition | Fração da rigidez de rolagem total atribuída a cada eixo — determina como o momento elástico de rolagem se divide entre dianteira e traseira. |
| Equation | Analysis Mode: `λ_f = K_φF/(K_φF+K_φR)`; `λ_r = K_φR/(K_φF+K_φR)`; `λ_f+λ_r=1`. Design Mode (reverso): dado um `λ_f` alvo e mantendo `K_φR` fixo (rigidez traseira congelada), `K_φF,required = (λ_f/(1-λ_f)) · K_φR`; e o ARB dianteiro necessário: `K_ARB,F,required = K_φF,required − K_φF,no_ARB` (onde `K_φF,no_ARB = K_wheel,F·t_F²/2`, `SUS-206`). **V3.0 (EDR-045):** com o pneu em série, `K_susp = K_φF,required·K_φT/(K_φT − K_φF,required)` com `K_φT = K_T,F·t_F²/2`, e `K_ARB,F,required = K_susp − K_wheel,F·t_F²/2` (Milliken p. 592). |
| Variables | `SUS-206`, `SUS-207` (Analysis); adicionalmente `λ_f target (TARGET-XXX)` (Design) |
| Units | Adimensional |
| Data Type | CALCULATED (Analysis) / CALCULATED a partir de TARGET (Design) |
| Lifecycle/Validation Status | CHECKED / PASS (Analysis — verificado 7/7 no T09 Reference Case, incluindo a decomposição sem-ARB); Design Mode reverso: DRAFT / NOT_VALIDATED (fórmula nova, ainda não exercitada com dado real) |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | Checagem `λ_f+λ_r=1`; TC-006 |

### SUS-211 — Tire Vertical Stiffness (`K_T`) — *novo ID, V3.0*

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness / Tire |
| Definition | Rigidez vertical do pneu na carga de operação, por eixo. |
| Equation | INPUT (medido ou do dataset do pneu) |
| Units | N/m (SI); N/mm na interface |
| Assumptions | Linear; igual nos dois lados do eixo |
| Reference/Source | Dataset do pneu (`VERTICAL_STIFFNESS` do .tir) ou medição. **Valor atual: 120 312 N/m do .tir TTC PROVISÓRIO (EDR-038), não é o pneu do carro** |
| Data Type | INPUT |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de pneus |
| Revision | Tire REV |
| Validation Method | Medição de rigidez vertical do pneu real |

### SUS-212 — Ride Rate (`K_R`) — *novo ID, V3.0*

| Campo | Conteúdo |
|---|---|
| Domain | Stiffness |
| Definition | Rigidez vertical efetiva do canto: wheel rate em série com o pneu. |
| Equation | `K_R = K_wheel·K_T/(K_wheel + K_T)`; reverso: `K_wheel = K_R·K_T/(K_T − K_R)` |
| Units | N/m |
| Reference/Source | Milliken p. 591; Gillespie eq. 5-8; Seward eq. 4.1 e 4.4 |
| Data Type | CALCULATED |
| Lifecycle/Validation Status | CHECKED (TC-SUS-V30-001..003, exemplos publicados) / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | TC-SUS-V30-001..003; TC-WB30-002 |

**Nota:** `SUS-204` (Total Roll Stiffness, definida de forma genérica na Dependency Matrix original) passa a ser `SUS-204 = SUS-206 + SUS-207` — mantém o ID, mas a definição agora é explícita como soma dos dois componentes por eixo.

---

### SUS-103 — Lateral ΔFz (modelo de duas molas de Milliken)

| Campo | Conteúdo |
|---|---|
| Domain | Loads (Bloco F) |
| Definition | Transferência de carga lateral por eixo, separando contribuição elástica (rigidez de rolagem), geométrica (altura do roll center) e de massa não-suspensa. |
| Equation | **V3.0 (EDR-046/047), fórmula completa da Milliken (p. 682):** `φ = m_s·a_y·h2/(K_φF + K_φR − m_s·g·h2)`, `h2 = h_s − z_s` (vertical) <br> `ΔFz_F = [K_φF·φ + a_y·(m_s,F·z_F + m_uF·h_uF)]/t_F` <br> `ΔFz_R = [K_φR·φ + a_y·(m_s,R·z_R + m_uR·h_uR)]/t_R` <br> com `z_s = z_F + (z_R − z_F)·a_s/L` e `m_s,F`, `m_s,R`, `a_s` de SUS-009. Bloqueio se `m_s·g·h2 ≥ K_φF + K_φR` (instabilidade de rolagem). <br> Forma V2.4: `ΔFz_F = (a_y/t_F)[λ_f·m_s·(h_s−z_s) + (b/L)·m_s·z_F + m_uF·h_uF]`, com `z_s = (b/L)·z_F + (a/L)·z_R` |
| Variables | `a_y` [m/s²]; `t_F, t_R` (`SUS-004/005`); `λ_f, λ_r` (`SUS-208`); `m_s` (`SUS-009`, total); `h_s` (`SUS-012`); `z_F, z_R` = `SUS-401` avaliado no eixo dianteiro e traseiro respectivamente (RC estático, REFERENCE); `a, b, L` (`SUS-006, SUS-003`); `m_uF, m_uR` (`SUS-007/008`); `h_uF, h_uR` (`SUS-010/011`) |
| Units | N (SI) |
| Sign Convention | `a_y > 0` = aceleração lateral para a esquerda (convenção ISO 8855, curva à esquerda). Para `a_y > 0`, a carga **aumenta no lado direito** (outer) e **diminui no lado esquerdo** (inner): `Fz_FR = Fz_F,static + ΔFz_F`; `Fz_FL = Fz_F,static − ΔFz_F` (e análogo para o eixo traseiro) |
| Assumptions | RC estático no ride height de referência (`z_F`, `z_R` não variam com o ângulo de rolagem real — limitação conhecida, já documentada em `SUS-401`); posição longitudinal do CG suspenso aproximada pela posição do CG total (nota já registrada em `SUS-006`); ARB tratado como rigidez aditiva simplificada (`SUS-206/207`); regime quase-estático linear, sem não-linearidade de pneu na resposta de rolagem |
| Reference/Source | Milliken & Milliken, *Race Car Vehicle Dynamics* — modelo de duas molas ("two-spring" analogy) para transferência lateral de carga (Reference Theory, não é "validada" diretamente — validamos transcrição/implementação/aplicação, não a teoria em si). Transcrição conferida termo a termo contra a reprodução secundária de Danielsson & González Coca, *Chalmers University of Technology*, 2015:68 (Eq. 2.15–2.16, creditada a Sampo, derivada de Milliken) — fórmula idêntica, sem divergência de sinal, hipótese ou estrutura. |
| Validity Domain | Quase-estático, pequenos ângulos de rolagem, RC tratado como ponto fixo |
| Data Type | MODEL + REFERENCE (RC/IC via OptimumKinematics) |
| Target/Requirement | — |
| Lifecycle Status | **CHECKED** (cross-referenciado contra fonte externa publicada, além do cross-check interno Python↔Excel e da verificação algébrica de conservação) |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV |
| Validation Method | TC-001 (`a_y=0 → ΔFz=0`), **TC-005 (V3.0: `t_F·ΔF_zF + t_R·ΔF_zR = m·a_y·h_CG + m_s·g·h2·φ`)**, TC-SUS-V30-009/010 (exemplo da Milliken p. 683-684 reproduzido: 590,8/483,4 lb/g e −2,0 °/g), TC-006 (distribuição de rigidez), TC-007 (`z_F=z_R=0` remove parcela geométrica), TC-008 (`m_uF=m_uR=0` remove parcela não-suspensa) |

**Nota de indexação para o Bloco E:** ao escrever as fichas de `SUS-401` a `SUS-405` (ainda pendentes), lembrar que RC, IC, camber e toe são grandezas **por eixo** (e, em alguns casos, por canto) — a Dependency Matrix original não deixou essa indexação explícita. Recomendo usar sufixo `-F`/`-R` (ex. `SUS-401-F`, `SUS-401-R`) quando essas fichas forem escritas, exatamente como fizemos aqui ao referenciar "`SUS-401` avaliado no eixo dianteiro e traseiro".

---

## Status atualizado

*(Seção histórica da V0.1 — o estado atual está em "Status V1.0 e Log de Validação — kinematics", ao final.)*

18 fichas escritas (`SUS-000, 001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012, 101, 102, 201, 202, 205, 206, 207, 208, 103` — 22, na verdade). O Bloco F está fechado com todos os pré-requisitos resolvidos na mesma iteração, sem gaps pendentes para trás. Os únicos itens que ficam como nota para blocos futuros (não bloqueiam nada agora): a indexação `-F`/`-R` do Bloco E (Kinematics Reference, ainda não escrito) e a simplificação do ARB em `SUS-206/207` (aceitável para V1, candidata a refinamento em V1.1 se a equipe usar ARBs ajustáveis com frequência).

Próximo bloco fisicamente novo: **Bloco H — Anti-geometry** (`SUS-301`/`SUS-302`, metodologia de Milliken já definida na seção 17.3, mas equação ainda `DRAFT → CHECKED`) — ou, alternativamente, **Bloco E — Kinematics Reference**, que é pré-requisito direto de `SUS-401` (já consumido aqui) e de `SUS-301/302` (via Instant Center).

---

## Bloco E — Kinematics Reference

**Nota de indexação, aplicada a todas as fichas abaixo:** RC, IC, camber e toe são grandezas **por eixo** (dianteiro/traseiro), e o Instant Center tem duas projeções geometricamente distintas usadas para propósitos diferentes — isso não estava explícito na Dependency Matrix original e só apareceu ao escrever as fichas de verdade. Convenção adotada: sufixo `-F`/`-R` para eixo, e `SUS-403` (vista frontal) vs. `SUS-406` (vista lateral, novo ID) para as duas projeções do IC.

### SUS-401 — Roll Center (REFERENCE)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E) |
| Definition | Altura do roll center de um eixo (`SUS-401-F`, `SUS-401-R`), no Kinematic Operating Point de referência (ride height estático). |
| Equation | Não é uma fórmula — valor exportado diretamente do OptimumKinematics |
| Variables | `z_F`, `z_R` [m] |
| Units | m internamente; mm na interface. **Verificar se o export do OptimumKinematics reporta relativo à origem do CAD ou ao solo** — se necessário, aplicar `SUS-000` na importação |
| Sign Convention | Altura acima do solo, conforme `SUS-000` |
| Assumptions | V1 usa apenas o ponto no ride height estático; `RC(z)` completo permanece disponível no REFERENCE, mas não é consumido diretamente pelo modelo quase-estático (ver seção 17.4) |
| Reference/Source | OptimumKinematics — autoridade de cinemática |
| Data Type | REFERENCE |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV |
| Validation Method | TC-011 (comparação direta com export do OptimumKinematics — aqui é a própria fonte, então o teste real é de importação/conversão de unidade e referência de solo, não de física) |

### SUS-402 — Roll Center (Model/Check)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E) |
| Definition | Cálculo geométrico simplificado do roll center por interseção de retas em vista frontal (2D), usado como sanity check do `SUS-401`. **Nunca substitui o REFERENCE.** |
| Equation | Passo 1 — Instant Center (mesmo ponto de `SUS-403`): `IC = intersecção(reta[LCA_outer, LCA_inner], reta[UCA_outer, UCA_inner])` em coordenadas (Y,Z). Interseção de duas retas por dois pontos cada, forma geral: dados `(x1,y1)-(x2,y2)` e `(x3,y3)-(x4,y4)`, `denom = (x1-x2)(y3-y4)-(y1-y2)(x3-x4)`; `Px = ((x1y2-y1x2)(x3-x4)-(x1-x2)(x3y4-y3x4))/denom`; `Py = ((x1y2-y1x2)(y3-y4)-(y1-y2)(x3y4-y3x4))/denom`. Passo 2 — Roll Center: reta de `Contact Patch (Y_CP, 0)` a `IC (Y_IC, Z_IC)`, avaliada em `Y=0` (centerline): `RC_height = Z_CP + (Z_IC-Z_CP)/(Y_IC-Y_CP) · (0-Y_CP)` |
| Variables | `LCA_outer`, `LCA_inner`, `UCA_outer`, `UCA_inner` (hardpoints, projeção Y-Z), `Contact Patch (Y_CP, 0)` |
| Units | m (coordenadas); m (RC height) |
| Data Type | MODEL *(flag: propósito = cross-check; nunca autoritativo)* |
| Assumptions | Vista frontal 2D (projeção Y-Z, ignora componente X dos hardpoints); suspensão simétrica esquerda/direita; pivôs internos do braço (front/rear) tratados como um único ponto representativo (eixo de pivô assumido ~paralelo a X) — simplificação de primeira ordem, não substitui um solver 3D; **caso especial:** braços com retas paralelas em vista frontal (denom≈0) → IC no infinito, tratar como aviso, não como erro silencioso |
| Reference/Source | Método clássico de construção geométrica de roll center (Milliken, RCVD; também descrito em Puhn, *How to Make Your Car Handle*) |
| Lifecycle/Validation Status | **CHECKED** (fórmula verificada com caso de teste sintético — ver `kinematics_model_V2_0.py`/`test_kinematics_model_V2_0.py`) / NOT_VALIDATED (ainda sem hardpoints reais do TX/T09 para comparar contra `SUS-401`) |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | Caso de teste sintético (geometria arbitrária, verifica só a matemática da interseção); comparação com `SUS-401` quando houver REFERENCE real — divergência segue o processo da seção 9 (units → coordinates → hardpoints → ... → tolerância) |
| Implementation Note | Implementado **apenas em Python** (`kinematics_model_V2_0.py`), não em fórmula nativa do Excel — a dupla interseção de retas 2D produziria uma fórmula de planilha muito longa e ilegível para o ganho que traria; decisão registrada em `DR-009`. O Excel consome o resultado como valor de referência a atualizar manualmente até existir bridge. |

### SUS-403 — Instant Center (vista frontal)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E) |
| Definition | Instant center em vista frontal (usado para derivar/checar o roll center). Por eixo: `SUS-403-F`, `SUS-403-R`. |
| Equation | Valor exportado do OptimumKinematics; usado como entrada de `SUS-402` |
| Units | Coordenadas Y/Z [m], no sistema da equipe |
| Reference/Source | OptimumKinematics |
| Data Type | REFERENCE |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV |
| Validation Method | TC-011 |

### SUS-406 — Instant Center (vista lateral)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E) |
| Definition | Instant center em vista lateral (side-view), geometricamente distinto do `SUS-403` (vista frontal) — é a entrada direta de anti-dive (`SUS-301`) e anti-squat (`SUS-302`). Por eixo: `SUS-406-F` (frenagem), `SUS-406-R` (tração). |
| Equation | **V3.0 (EDR-048): o método abaixo é LEGADO** (não aparece na literatura e falha em geometria realista, TC-KIN-114). O IC lateral do MODEL é o cinemático de SUS-412; a linha de força vai do ponto de reação ao IC, com sinal (`s = dz/dx`), e o ponto de reação segue a Milliken p. 618-619: contact patch para freio no cubo e centro da roda para torque reagido pelo chassi. Método V1: **Passo 0 — pré-processamento (diferente do `SUS-402`):** o eixo de pivô interno de cada braço é assumido ~paralelo a X (mesma hipótese do `SUS-402`), o que faz esse eixo projetar como uma **reta ao longo de X** em vista lateral, não um ponto — o oposto do que acontece em vista frontal. Solução: usar o **ponto médio** das buchas dianteira/traseira do braço como ponto representativo: `inner_mid = ((X_bucha_frente+X_bucha_tras)/2, (Z_bucha_frente+Z_bucha_tras)/2)`. **Passo 1 — Instant Center lateral:** mesma fórmula de interseção de retas do `SUS-402` (duas retas por dois pontos cada), aplicada a `(X,Z)` em vez de `(Y,Z)`: `IC = interseção(reta[LCA_outer, LCA_inner_mid], reta[UCA_outer, UCA_inner_mid])`. **Passo 2 — ângulo para Anti-Dive/Anti-Squat:** `d = \|X_IC − X_CP\|` (distância horizontal absoluta entre o contact patch do eixo e o IC); `tan(φ) = Z_IC / d`. |
| Variables | `LCA_bushing_front`, `LCA_bushing_rear`, `LCA_outer`, `UCA_bushing_front`, `UCA_bushing_rear`, `UCA_outer` (hardpoints, projeção X-Z), `Contact Patch (X_CP, 0)` do eixo correspondente |
| Units | m (coordenadas); adimensional (`tan φ`) |
| Sign Convention | `d` é sempre tomado em módulo (`\|X_IC−X_CP\|`) — a direção (IC à frente ou atrás do contact patch) não entra com sinal na fórmula de `SUS-301`/`SUS-302`, que já assume `tan(φ)≥0`. Se o IC ficar exatamente na mesma posição X do contact patch (`d≈0`), o ângulo não é definido (assíntota) — tratar como aviso, não dividir por zero silenciosamente. |
| Data Type | MODEL *(mesmo propósito de `SUS-402`: cross-check, nunca substitui REFERENCE do OptimumKinematics quando existir)* |
| Assumptions | Vista lateral 2D (projeção X-Z, ignora Y); eixo de pivô interno aproximado pelo ponto médio das duas buchas — aproximação de primeira ordem, exata apenas se o eixo for simétrico em torno do ponto médio; a linha relevante para `SUS-301`/`SUS-302` (contact patch→IC vs. wheel center→IC) ainda depende da configuração real de freio/trem de força — **permanece em aberto**, mesma ressalva da seção 17.3 |
| Reference/Source | Mesmo método clássico de construção geométrica (Milliken, RCVD), aplicado à projeção lateral em vez de frontal |
| Lifecycle/Validation Status | **CHECKED** (fórmula verificada com dois testes sintéticos independentes — pré-processamento isolado e interseção+ângulo+fórmula de Anti-Dive — ver `kinematics_model_V2_0.py`/`test_kinematics_model_V2_0.py`) / NOT_VALIDATED (sem hardpoints reais do TX/T09 para comparar) |
| Owner | Responsável de suspensão |
| Revision | Dynamics REV |
| Validation Method | Casos de teste sintéticos (geometria arbitrária); comparação com REFERENCE do OptimumKinematics quando existir, seguindo o processo de divergência da seção 9 |
| Implementation Note | Implementado **apenas em Python** (`kinematics_model_V2_0.py`), mesma decisão e mesmo motivo do `SUS-402` (`DR-009`) — a interseção de retas 2D não compensa como fórmula nativa do Excel. Ainda **não conectado** ao `06_SUSPENSION`/`07_KINEMATICS` do Excel — essa conexão fica para depois do hardpoint schema (V2, item 3), para não introduzir hardpoints fictícios como se fossem reais na planilha. |


> **Nota V2.0 sobre SUS-406 (achados verificados por teste; PROPOSTA aguardando aprovação, nada foi alterado na equação acima).**
> 1. **Mal condicionamento (cálculo + teste TC-KIN-114).** O método V1 (reta ball joint externo → ponto médio das buchas) depende da diferença de X entre o ball joint e o ponto médio. Na geometria sintética realista (`hardpoints_synthetic_V2.0.csv`, FB_f=0,6, L=1,55 m, h_CG=0,315 m) o %AD vale −680,7 pelo método V1, 36,3 pelo IC cinemático e 38,0 pelas retas dos eixos de pivô. Variando o X de LCA_OUT em ±5 mm, o método V1 vai de −935 a −596 e o cinemático de 36,4 a 36,2.
> 2. **Sinal (derivação + teste TC-KIN-110).** A forma `tan φ = Z_IC/|X_IC − X_CP|` ignora de que lado do contact patch o IC está. Pelo equilíbrio da linha de força, na frente o anti-dive é positivo quando o IC está **atrás e acima** do ponto de reação; um IC à frente e acima dá pro-dive, mas a forma V1 devolve valor positivo (TC-KIN-110d reproduz isso). A forma com sinal usa a inclinação `s = dz/dx` da linha (ponto de reação → IC): `AD = FB_f·(−s)·L/h·100` (frente) e `AS = TF_r·s·L/h·100` (traseira). Isso também trata IC no infinito (eixos paralelos e inclinados dão %AD ≠ 0, TC-KIN-111).
> 3. **Incerteza de método (inferência).** Para um movimento 3D, "o IC em vista lateral" é uma convenção: a projeção do movimento da manga não é um movimento plano rígido. O solver V2.0 usa as normais às velocidades projetadas dos dois ball joints (SUS-412). Fontes consultadas (fóruns FSAE e material de cursos) descrevem só a construção por eixos de pivô, de forma qualitativa. **Nenhuma fonte primária (Milliken RCVD) foi consultada nesta etapa.** Confirmar a convenção contra o OptimumKinematics/Lotus (TC-011/TC-012) antes de congelar.

### SUS-404 — Camber Gain

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E) |
| Definition | Variação de camber com o curso de suspensão (`dCamber/dz`), por eixo. Curva completa disponível como REFERENCE; V1 consome o valor no KOP de referência quando necessário para outros cálculos. |
| Equation | Curva exportada do OptimumKinematics |
| Sign Convention | Camber positivo = topo da roda para fora (seção 17.2) |
| Units | °/mm ou °/m |
| Reference/Source | OptimumKinematics |
| Data Type | REFERENCE |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV |
| Validation Method | teste de sinal de camber/toe (TC ainda não numerado; `TC-010` é o cálculo inverso de frequência), TC-011 |

### SUS-405 — Toe Curve

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E) |
| Definition | Variação de toe com o curso de suspensão (`dToe/dz`), por eixo. Curva completa disponível como REFERENCE; V1 consome o valor no KOP de referência quando necessário para outros cálculos. |
| Equation | Curva exportada do OptimumKinematics |
| Variables | `Toe(z)` por eixo |
| Sign Convention | Toe positivo = toe-out (seção 17.2) |
| Units | °/mm ou °/m |
| Reference/Source | OptimumKinematics |
| Data Type | REFERENCE |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV |
| Validation Method | teste de sinal de camber/toe (TC ainda não numerado; `TC-010` é o cálculo inverso de frequência), TC-011 |

---

## Bloco E.2 — Kinematics Model (V2.0)

**Natureza.** Fichas MODEL/cross-check de grandezas cuja REFERENCE é o OptimumKinematics (DR-009: o solver nunca substitui a REFERENCE). Implementação: `hardpoints_V2_0.py` (schema, ver `hardpoint-schema-V2.0.md`) e `kinematics_model_V2_0.py`. `SUS-407`/`SUS-408` são o cross-check MODEL de `SUS-404`/`SUS-405`; `SUS-409` é o de `SUS-201` (MR(z)); `SUS-412` estende `SUS-402`/`SUS-403`/`SUS-406` ao mecanismo 3D. **IDs `SUS-407` a `SUS-413` são PROPOSTA desta versão** (faixa `SUS-4XX` da arquitetura; aguardam aprovação).

**Formulação comum.** Manga (upright) como corpo rígido, pose = vetor de rotação + translação (6 incógnitas). Cinco restrições de comprimento fixo (2 do LCA via pivôs F/R, 2 do UCA, 1 da barra de direção) mais a restrição de curso fecham o sistema 6×6, resolvido por Newton com continuação. **Curso `z`** = deslocamento vertical do centro da roda (bump positivo) no referencial do chassi (convenção adotada por hipótese; OptimumKinematics pode usar outra definição — verificar). **Hipóteses gerais:** corpos rígidos, juntas esféricas ideais, sem compliance/folga, roda sem rotação própria, contact patch tratado como ponto solidário à roda. **Verificação:** soluções independentes (TC-KIN-103 four-bar 2D por `brentq`; TC-KIN-112 formulação por distâncias via `scipy.optimize.least_squares`) e casos analíticos; **sem hardpoints reais, TC-011 permanece NOT_VALIDATED.**

### SUS-407 — Camber Gain (Model/Check)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E.2) |
| Definition | Camber da roda em função do curso e seu gradiente (`dγ/dz`), calculados a partir dos hardpoints. Cross-check de `SUS-404`. |
| Equation | `â = (SPINDLE_PT − WHEEL_CENTER)/\|·\|` na pose resolvida; `γ(z) = asin(−â_z)`; camber gain = diferença central de `γ(z)`. |
| Variables | `WHEEL_CENTER`, `SPINDLE_PT` (hardpoints, m); `z` [m]; `γ` [°] |
| Units | ° ; °/mm na interface |
| Sign Convention | Camber positivo = topo da roda para fora (arquitetura 17.2); `SPINDLE_PT` deve estar para fora do centro da roda (validado no schema). |
| Assumptions | Hipóteses gerais do Bloco E.2. **Incerteza de entrada (cálculo, Monte Carlo σ=0,5 mm em todos os hardpoints, N=300):** o camber estático derivado de `SPINDLE_PT − WHEEL_CENTER` com base de 0,08 m tem σ ≈ 0,5° (o erro de coordenada é amplificado pela base curta); o ganho de camber tem σ ≈ 0,008 °/10 mm (≈4%). Recomenda-se base ≥ 0,15 m ou informar o camber estático como dado separado. |
| Reference/Source | Derivação própria (restrições de comprimento fixo); sem fonte primária consultada. Verificação: TC-KIN-101, 102, 103, 104, 105, 106a, 112. |
| Validity Domain | ±40 mm testado em geometria sintética; fora disso, validar. |
| Data Type | MODEL *(flag: cross-check; nunca autoritativo)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED (sem REFERENCE real; TC-011 pendente) |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-101/102/103/104/105/106/112; TC-011 quando houver export do OptimumKinematics |

### SUS-408 — Toe Curve / Bump Steer (Model/Check)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E.2) |
| Definition | Toe da roda em função do curso (bump steer = `dδ/dz`). Cross-check de `SUS-405`. |
| Equation | `δ = asin(−â_x / √(â_x² + â_y²))` |
| Variables | `â` como em SUS-407 |
| Units | ° ; °/mm na interface |
| Sign Convention | Toe positivo = toe-out, esquerda e direita (arquitetura 17.2). Yaw da roda (ISO 8855, + esquerda) = `lado·δ`, com lado = +1 (esquerda) / −1 (direita). |
| Assumptions | Hipóteses gerais do Bloco E.2. A manga pode girar em torno do pino mestre para satisfazer a barra de direção; isso é o bump steer. Em mecanismo plano com barra compatível o toe é nulo (TC-KIN-103c). |
| Reference/Source | Derivação própria; TC-KIN-103c, 104b, 106b. |
| Validity Domain | Como SUS-407 |
| Data Type | MODEL *(cross-check)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-103c, 104b, 106b, 109, 125; TC-011 |
| Revisão 2026-10-19 (EDR-052) | Ride steer como na Milliken 19.4 (p. 721-725): inclinação no curso zero [°/mm, toe-out +], coeficiente quadrático e maior desvio da reta (curva = "a evitar", Fig. 19.9). Sinal de manobra: na frente, esterçar para fora da curva é subesterço; atrás, para dentro (Milliken p. 721). `kinematics_model.ride_steer`. O roll steer sai das mesmas curvas (SUS-415) |

### SUS-409 — Motion Ratio MR(z) (Model/Check)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics / Stiffness (Bloco E.2) |
| Definition | Razão `MR [wheel/spring]` em função do curso, a partir da geometria pushrod/pullrod + rocker + mola/amortecedor. Cross-check de `SUS-201` (REFERENCE). |
| Equation | `MR(z) = \|dz / dL_mola\|`, `L_mola = \|ROCKER_SPRING − SPRING_CHASSIS\|` na pose; derivada por diferença central. `K_wheel = K_spring / MR²` (SUS-202). |
| Variables | `z` [m]; `L_mola` [m] |
| Units | Adimensional |
| Sign Convention | `MR > 0` (módulo). A mola comprime em bump quando `dL/dz < 0` (TC-KIN-108b). |
| Assumptions | Hipóteses gerais do Bloco E.2. `K_wheel = K_spring/MR²` omite o termo de pré-carga `F_mola·d²L/dz²` (segunda ordem), **não modelado**. Pushrod pode ser montado no LCA, UCA ou manga (Component do ponto `PUSH_OUT`). Incerteza (Monte Carlo σ=0,5 mm): MR σ ≈ 0,016 (1,4%) na geometria sintética. |
| Reference/Source | Derivação própria; caso analítico MR = r1/r2 (TC-KIN-108a). |
| Validity Domain | ±40 mm testado em geometria sintética |
| Data Type | MODEL *(cross-check)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-101, 108a/b; TC-011 |

### SUS-410 — Kingpin Geometry (caster, KPI, scrub radius, mechanical trail)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E.2) |
| Definition | Geometria do eixo do pino mestre (reta `LCA_OUT → UCA_OUT`) e sua interseção com o solo. |
| Equation | `k̂ = (UCA_OUT − LCA_OUT)/\|·\|`; caster `= atan2(−k_x, k_z)`; KPI `= atan2(−lado·k_y, k_z)`; interseção `I` com o plano do contact patch (`z = z_CP`); scrub `= lado·(y_CP − y_I)`; trail `= x_I − x_CP`. |
| Variables | `LCA_OUT`, `UCA_OUT`, `CONTACT_PATCH` (m) |
| Units | ° ; m (mm na interface) |
| Sign Convention | Caster + = topo para trás; KPI + = topo para dentro; scrub + = interseção inboard do contact patch; trail + = interseção à frente do contact patch. |
| Assumptions | Hipóteses gerais. Trail medido no contact patch (não no centro da roda). Convenções conferidas (2026-10-19, EDR-052) com a Milliken Fig. 19.1 (p. 710: KPI, scrub, spindle length, caster, trail), o Gillespie Fig. 8.8 (p. 283-284: scrub + com a roda para fora da interseção; caster + com a interseção à frente do contact patch) e o OptimumKinematics §7.3.3.12 (scrub). **Spindle length** (Milliken 19.1): distância horizontal do pino mestre ao centro da roda, na altura do centro, `lado·(y_WC − y_K)`; + = roda para fora (TC-KIN-121). |
| Reference/Source | Definições geométricas; caso analítico (14,0362°, 11,3099°, +22 mm, +35 mm) em TC-KIN-117a, esquerda e direita. |
| Validity Domain | Como SUS-407 |
| Data Type | MODEL *(cross-check)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-117a; TC-011 |

### SUS-411 — Contact Patch Travel (track change, wheelbase change)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E.2) |
| Definition | Deslocamento do contact patch com o curso: `track_change = lado·(y_CP − y_CP,0)` (positivo para fora) e `wheelbase_change = x_CP − x_CP,0`. |
| Equation | Ponto `CONTACT_PATCH` solidário à roda, transportado pela pose da manga. |
| Variables | `CONTACT_PATCH` (m) |
| Units | m (mm na interface) |
| Sign Convention | Track change + = contact patch para fora; wheelbase change + = para frente. |
| Assumptions | **Aproximação:** contact patch fixo na roda. Contra um disco fino (ponto mais baixo), a diferença de track change calculada é 12 a 30 µm em ±30 mm (cálculo, geometria sintética); a geometria real do pneu (crown/seção) **não foi modelada** e pode alterar isso. Em paralelogramo o track change = −L(1−cos θ) (TC-KIN-117b). |
| Reference/Source | Derivação própria; TC-KIN-104c, 117b. |
| Validity Domain | Como SUS-407 |
| Data Type | MODEL *(cross-check)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-104c, 117b |

### SUS-412 — Instant Centers e Roll Center cinemáticos (3D)

| Campo | Conteúdo |
|---|---|
| Domain | Kinematics (Bloco E.2) |
| Definition | IC frontal (Y,Z) e lateral (X,Z) da manga, RC por canto e RC do eixo, calculados a partir do movimento 3D resolvido. Estende `SUS-402`/`SUS-403`/`SUS-406` (2D). |
| Equation | Velocidades `v_L`, `v_U` dos ball joints por diferença central da pose (`dz = 1e-5 m`). IC = interseção das retas por `P_L` e `P_U` normais às velocidades projetadas no plano da vista. Normais paralelas: IC no infinito, retorna a direção. RC por canto = cruzamento em `Y=0` da reta `CP → IC` frontal, altura acima do solo (solo = `z_CP` na pose). RC do eixo = interseção das retas dos dois lados. Inclinação da linha de força lateral `s = dz/dx` (ponto de reação → IC), com `reaction_point` = `contact_patch` ou `wheel_center`. |
| Variables | Pose da manga; `LCA_OUT`, `UCA_OUT`, `CONTACT_PATCH`, `WHEEL_CENTER` |
| Units | m ; adimensional (`s`) |
| Sign Convention | ISO 8855. Anti-dive/squat com sinal: ver notas de SUS-406 e SUS-301/302. |
| Assumptions | Hipóteses gerais. **Incerteza de método:** a projeção do movimento 3D numa vista não é movimento plano rígido; o IC depende de quais pontos definem as normais (aqui, os dois ball joints). Reduz exatamente ao método 2D da V1 em mecanismo plano (TC-KIN-107, erro ≤ 4e-8 m) e à fórmula fechada por eixos em planos X-Z (TC-KIN-110a). Diferença de método na geometria sintética: IC frontal cinemático vs V1 = 34,6 mm (TC-KIN-114b). Passo da diferença finita: IC estável a 1e-8 m para `dz ≤ 1e-4 m`. Incerteza de entrada (Monte Carlo σ=0,5 mm): RC σ ≈ 1,9 mm (13% do valor nominal de 14,8 mm); %AD cinemático σ ≈ 1,0 ponto. O RC migra de +59 mm (−30 mm) a −29 mm (+30 mm) na geometria sintética (V1/Standard usa RC estático, limitação conhecida). |
| Reference/Source | Derivação própria; verificação TC-KIN-107, 110, 111, 113, 114. Fontes secundárias consultadas só descrevem a construção qualitativa; fonte primária não consultada. |
| Revisão 2026-10-19 (EDR-053) | **Definição primária:** linha de força pelo trabalho virtual (SAE J670: RC é onde força lateral não produz rolagem; Gillespie, Apêndice A). A linha passa pelo ponto de reação e é perpendicular à velocidade dele por unidade de curso: inclinação lateral = −v_x/v_z (contact patch para o anti-dive; centro da roda para o anti-squat, EDR-048); RC do canto = (−v_y/v_z)·(0 − y_cp); RC do eixo = interseção das duas linhas. IC exibido = centro instantâneo no plano que contém o ponto de reação (X = X_cp na frontal; Y = Y_cp ou Y_wc na lateral), único nesse plano. `kinematics_model.force_lines_vw`, `axle_roll_center_vw`; colunas `rc_height_vw_m` e `side_force_line_slope_vw` da varredura. O método dos ball joints (acima) fica como legado: depende do par de pontos fora do plano da vista. Diagnóstico da REFERENCE: `reference_literal_centers` (eixo instantâneo ∩ plano pelo contact patch, com o passo). TC-KIN-120a-c, 128. Sintético FL: RC 17,7 (primária) × 14,8 (legado) × −142,6 mm (leitura literal) |
| Validity Domain | Como SUS-407; IC exige velocidades projetadas não nulas |
| Data Type | MODEL *(cross-check; nunca substitui SUS-401/403/406 REFERENCE)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-107/110/111/113/114; TC-011 e TC-012 (comparação com OptimumKinematics e Lotus) quando houver dados |

### SUS-413 — Steering Kinematics (yaw vs cremalheira; razão de direção)

| Campo | Conteúdo |
|---|---|
| Domain | Steering / Kinematics (Bloco E.2) |
| Definition | Yaw da roda em função do deslocamento da cremalheira `s` (+Y) e razão de direção. Cross-check de `SUS-601`. |
| Equation | Yaw `= lado·(δ(s) − δ(0))`; `SR = (360/c) / (dyaw/ds)`, com `c` = curso de cremalheira por volta do pinhão (INPUT). |
| Variables | `s` [m]; `c` [m/volta]; yaw [°] |
| Units | °/m ; adimensional |
| Sign Convention | Yaw + = esquerda (ISO 8855). Com a barra de direção atrás do pino mestre, cremalheira para +Y esterça para a direita (`yaw = −s/e`, TC-KIN-109a). |
| Assumptions | Cremalheira ao longo de Y (parâmetro `rack_dir`); sem Ackermann dinâmico nem compliance. `c` não consta nos documentos; é entrada do usuário. |
| Reference/Source | Caso analítico (pino vertical): `yaw = −s/e`, SR = 10,47 para c = 0,060 m e e = 0,10 m (TC-KIN-109a/b; valores de teste, não do carro). |
| Validity Domain | Pequenos deslocamentos de cremalheira |
| Data Type | MODEL *(cross-check)* |
| Lifecycle Status | CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Kinematics REV (modelo); hardpoints: Geometry REV (`G-REV-X`) |
| Validation Method | TC-KIN-109a/b, 124a |
| Revisão 2026-10-19 (EDR-052) | Razão total do eixo (SAE J670 9.4.6: gradiente do volante sobre o ângulo **médio** das rodas dianteiras; Gillespie p. 293): `steering_ratio_overall`. Com Ackermann, a razão difere entre lados (Milliken p. 716) |


### SUS-414 — Ackermann (geometria e % Ackermann) — *novo ID, V3.0 (EDR-052)*

| Campo | Conteúdo |
|---|---|
| Domain | Steering (Bloco E.2) |
| Definition | Diferença entre os ângulos das rodas dianteiras interna e externa num esterço. Ackermann exato = as duas rodas tangentes a trajetórias com o mesmo centro (Milliken 19.2, p. 713-716; Seward 6.3.1). |
| Equation | Ackermann exato: `cot δo − cot δi = t/L` (Gillespie eq. 8-1 e 8-2, p. 277-278). % Ackermann `= (δi − δo)/(δi,Ack − δo)·100` no mesmo δo. Raio da roda externa `= L/sin δo` (Seward, Tab. 6.2). |
| Variables | `δo`, `δi` [°]; `L` = SUS-003; `t` = SUS-004 |
| Units | ° ; % ; m |
| Sign Convention | Ângulos em módulo. 100 % = Ackermann exato; 0 % = paralelo; < 0 = reverso (Milliken p. 714-716). |
| Assumptions | `t` = bitola (a literatura usa a bitola; o centro de giro real é o pino mestre). A razão (% Ackermann) é forma do projeto: a literatura define os extremos. Sem compliance (Milliken p. 715: em curva rápida a compliance pode superar o Ackermann). |
| Reference/Source | Gillespie p. 277-278; Seward Tab. 6.2 (reproduzida em TC-KIN-122a); Milliken p. 713-716 (recomenda paralelo ou um pouco de reverso para corrida). |
| Data Type | INPUT (δo, δi medidos) e MODEL (`ackermann_from_kinematics`, a partir da geometria) |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de steering |
| Revision | Geometry REV |
| Validation Method | TC-KIN-122a/b, 123; TC-WB30-015 (planilha 07_KINEMATICS B72:B76) |


### SUS-415 — Roll steer e contribuição ao gradiente de subesterço — *novo ID, V3.0 (EDR-052)*

| Campo | Conteúdo |
|---|---|
| Domain | Steering / Handling (Bloco E.2) |
| Definition | Esterço das rodas de um eixo em relação à massa suspensa devido à rolagem dela (Gillespie p. 220; Milliken 19.4). |
| Equation | `ε` = graus de esterço por grau de rolagem; `K_roll steer = (ε_f − ε_r)·∂φ/∂a_y` (Gillespie eq. 6-57). Do solver: rolagem φ → curso da roda direita `+(t/2)φ`, esquerda `−(t/2)φ`; esterço do eixo = média do yaw ISO; `ε = −Δyaw/Δφ`. Eixo simétrico e linear: `ε = b·t/2`, b = toe-out por curso (TC-KIN-126a). |
| Variables | `ε_f`, `ε_r` [°/°]; `∂φ/∂a_y` [°/g] (planilha: φ de 09_LOADS B21 / a_y de 08 B11) |
| Units | °/° ; °/g |
| Sign Convention | `ε > 0` esterça para a direita numa rolagem para a direita (lado direito para baixo), como no Gillespie. Na frente, ε > 0 = subesterço; atrás, sobresterço. `K > 0` = subesterço. |
| Assumptions | Cinemática pura (sem compliance; Milliken p. 724-726 lembra que a compliance pode dominar). Pequenas rolagens. |
| Reference/Source | Gillespie p. 220 (eq. 6-57, conferida na imagem) e p. 281-282; Milliken p. 721-725. |
| Data Type | MODEL (`roll_steer_coefficient`, `roll_steer_understeer_deg_per_g`); INPUT na planilha até haver hardpoints |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de suspensão |
| Revision | Geometry REV |
| Validation Method | TC-KIN-126a/b; TC-WB30-015 (07_KINEMATICS B82:B85) |


### SUS-416 — Efeitos do esterço pelo pino mestre (camber e elevação) — *novo ID, V3.0 (EDR-052)*

| Campo | Conteúdo |
|---|---|
| Domain | Steering (Bloco E.2) |
| Definition | Variação de camber e elevação do carro quando a roda gira em torno do pino mestre (Milliken 19.1, p. 710-713). |
| Equation | Manga girada de ψ em torno da reta LCA_OUT → UCA_OUT, ball joints parados: camber e toe pela pose girada; elevação = −ΔZ do contact patch no referencial do chassi. |
| Variables | ψ [°] (+ = em torno do eixo orientado para cima) |
| Units | ° ; m |
| Sign Convention | Elevação + = o carro sobe. Camber + = topo para fora. |
| Assumptions | Efeito geométrico (o livro descreve assim). Com KPI e spindle length positivos o carro sobe nos dois sentidos (TC-KIN-127b); com caster positivo a roda externa ganha camber negativo e a interna positivo, e a elevação muda entre os lados, o que dá o peso diagonal (TC-KIN-127a; Milliken p. 712-713). |
| Reference/Source | Milliken 19.1, p. 710-713. |
| Data Type | MODEL (`steer_effects`) |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de steering |
| Revision | Geometry REV |
| Validation Method | TC-KIN-127a/b |

---

## Bloco H — Anti-geometry

### SUS-013 — Front Brake Force Fraction (`FB_f`) — *novo ID*

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle/Setup (Bloco A) |
| Definition | Fração da força de frenagem total reagida pelo eixo dianteiro (brake bias). |
| Equation | `FB_f` = definido pelo balanço de freio do Setup (proporcional ou fixo, conforme sistema de freio da equipe) |
| Units | Adimensional (fração, 0 a 1) |
| Reference/Source | Especificação do sistema de freio (proporcionador, balance bar) |
| Data Type | INPUT (por Setup) |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de freios |
| Revision | Setup-specific |
| Validation Method | Medição de brake bias no banco de testes, se disponível |

### SUS-014 — Rear Traction Force Fraction (`TF_r`) — *novo ID*

| Campo | Conteúdo |
|---|---|
| Domain | Vehicle/Setup (Bloco A) |
| Definition | Fração da força de tração reagida pelo eixo traseiro. |
| Equation | `TF_r = 1` para RWD (valor fixo, documentado como hipótese da V1); generalizável para AWD em versão futura |
| Units | Adimensional |
| Data Type | INPUT (fixo em 1 para a configuração atual da equipe) |
| Lifecycle/Validation Status | FROZEN (valor trivial para RWD) / NOT_VALIDATED |
| Owner | Responsável de trem de força |
| Revision | Setup-specific |
| Validation Method | N/A para RWD; revisitar se a equipe migrar para AWD |

### SUS-301 — Anti-Dive

| Campo | Conteúdo |
|---|---|
| Domain | Anti-geometry (Bloco H) |
| Definition | Percentual da transferência de carga longitudinal (por frenagem) reagido geometricamente pela suspensão dianteira, em vez de elasticamente pela mola. |
| Equation | **V3.0 (EDR-048):** `AD_f[%] = FB_f·(−s_f)·(L/h_CG)·100`, `s_f = dz/dx` da linha contact patch dianteiro → IC lateral (freio dentro da roda, em volta do cubo: Milliken p. 618, Fig. 17.12). + = anti, − = pro-dive (EDR-026). Forma V1: `AD_f[%] = FB_f · tan(φ_f) · (L/h_CG) · 100` |
| Variables | `FB_f` (`SUS-013`); `φ_f` = ângulo, em vista lateral, da linha contact patch→IC dianteiro (derivado de `SUS-406-F`); `L` (`SUS-003`); `h_CG` (`SUS-002` — CG **total**, não `SUS-012`, pois aqui a referência é a geometria do veículo completo, não da massa suspensa isolada) |
| Units | % |
| Sign Convention | Conforme seção 17.3 — `SUS-301` nunca alimenta `SUS-102` (não altera a magnitude do load transfer longitudinal) |
| Assumptions | A linha relevante (contact patch vs. wheel center) ainda depende da configuração real de freio da equipe — ver `SUS-406` |
| Reference/Source | Milliken, RCVD — anti-dive/anti-lift |
| Data Type | REFERENCE (IC) + MODEL (percentual) |
| Lifecycle Status | **DRAFT → CHECKED** (metodologia FROZEN, fórmula final pendente de confirmação da linha geométrica) |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV |
| Validation Method | Implementação só após Test Case dedicado que confirme a linha geométrica correta para a configuração de freio real |

### SUS-302 — Anti-Squat

| Campo | Conteúdo |
|---|---|
| Domain | Anti-geometry (Bloco H) |
| Definition | Percentual da transferência de carga longitudinal (por tração) reagido geometricamente pela suspensão traseira. |
| Equation | **V3.0 (EDR-048):** `AS_r[%] = TF_r·s_r·(L/h_CG)·100`, `s_r = dz/dx` da linha **centro da roda** traseiro → IC lateral (motor no chassi com semieixos: Milliken Fig. 17.15b; Gillespie eq. 7-19). + = anti, − = pro-squat. Forma V1: `AS_r[%] = TF_r · tan(φ_r) · (L/h_CG) · 100` |
| Variables | `TF_r` (`SUS-014`, =1 para RWD); `φ_r` = ângulo, em vista lateral, da linha relevante → IC traseiro (derivado de `SUS-406-R`); `L`, `h_CG` (`SUS-003`, `SUS-002`) |
| Units | % |
| Sign Convention | `SUS-302` nunca alimenta `SUS-102` |
| Assumptions | Mesma ressalva de `SUS-301` quanto à linha geométrica (contact patch vs. wheel center) — a literatura distingue reação de torque via cubo vs. via suspensão |
| Reference/Source | Milliken, RCVD — anti-squat |
| Data Type | REFERENCE (IC) + MODEL (percentual) |
| Lifecycle Status | DRAFT → CHECKED |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV |
| Validation Method | Test Case dedicado, análogo a `SUS-301` |

---


> **Nota V2.0 sobre SUS-301/SUS-302.** Mesmo achado de sinal da nota de SUS-406: as equações acima, com `tan φ ≥ 0`, estão corretas só quando o IC lateral está do lado que produz anti-dive/anti-squat. O módulo `kinematics_model_V2_0.py` oferece `anti_dive_percent_signed` e `anti_squat_percent_signed` (inclinação com sinal), além do parâmetro `reaction_point` (`contact_patch` ou `wheel_center`) para a configuração de freio/trem de força, que continua **em aberto** (decisão da equipe). A planilha (`06_SUSPENSION`) mantém a forma V1 com placeholders: **não use** seus %AD/%AS como valores do carro.

---

## Bloco G — Combined Loading

### SUS-104 — Combined Fz por canto

| Campo | Conteúdo |
|---|---|
| Domain | Loads (Bloco G) |
| Definition | Carga vertical final em cada canto (FL/FR/RL/RR), combinando estático + transferência longitudinal + transferência lateral + parcela aerodinâmica, por superposição linear. |
| Equation | `Fz_FL = Fz_FL,static + ΔFz_long,F − ΔFz_F + Fz_aero,FL` <br> `Fz_FR = Fz_FR,static + ΔFz_long,F + ΔFz_F + Fz_aero,FR` <br> `Fz_RL = Fz_RL,static + ΔFz_long,R − ΔFz_R + Fz_aero,RL` <br> `Fz_RR = Fz_RR,static + ΔFz_long,R + ΔFz_R + Fz_aero,RR` <br> onde `ΔFz_long,F/R` é a metade do `SUS-102` por eixo (mesmo sinal para os dois lados), `±ΔFz_F/R` (`SUS-103`) segue a convenção de `a_y>0` = lado direito ganha carga (Bloco F), e `Fz_aero,corner = SUS-702-derivado / 2` (distribuição lateral simétrica: `Fz_aero,FL = Fz_aero,FR = Fz_aero,F/2`; `Fz_aero,RL = Fz_aero,RR = Fz_aero,R/2`, com `Fz_aero,F`/`Fz_aero,R` definidos na ficha `SUS-702`) |
| Variables | `SUS-101` (por canto), `SUS-102`, `SUS-103`, `SUS-701`, `SUS-702` |
| Units | N |
| Sign Convention | Herdada de `SUS-102` (`a_x`) e `SUS-103` (`a_y`) |
| Assumptions | Superposição linear (hipótese já documentada na arquitetura). **Válido apenas enquanto `Fz_corner ≥ 0`** — um resultado negativo indica perda de contato do pneu (liftoff), que extrapola o domínio de validade deste modelo linear e não deve ser aceito como resultado físico; deve gerar um `WARNING` de plausibilidade, não um valor negativo silencioso |
| Reference/Source | Soma direta das fichas anteriores — não introduz física nova |
| Data Type | MODEL |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de dinâmica |
| Revision | Dynamics REV |
| Validation Method | TC-004 (`ΣFz=W`), TC-003 (simetria em frenagem pura) |

---

## Bloco I — Tire Model

### SUS-501 — `Fy(Fz, α, γ)`

| Campo | Conteúdo |
|---|---|
| Domain | Tire (Bloco I) |
| Definition | Força lateral do pneu em função de carga vertical, ângulo de deriva (`α`) e camber (`γ`), conforme dataset/modelo do OptimumTire (nível 1 lookup ou nível 2 paramétrico, DEC-007). |
| Equation | Não reimplementada — consumida diretamente do dataset exportado (tabela ou coeficientes) |
| Variables | `Fz` (`SUS-104`), `α`, `γ` (`SUS-404`, se aplicável no ponto de operação) |
| Units | N (força); ° ou rad (`α`, `γ`, conforme exportação) |
| Sign Convention | **Verificar explicitamente a convenção de sinal de `α` exportada pelo OptimumTire/TTC contra a convenção do veículo (ISO 8855) antes de consumir diretamente** — mesma classe de risco já identificada para camber/toe |
| Reference/Source | TTC → OptimumTire — autoridade de caracterização de pneu |
| Data Type | REFERENCE |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de pneus |
| Revision | Tire REV |
| Validation Method | Comparação do pipeline consumido contra a curva bruta exportada do OptimumTire |

### SUS-502 — `Fx(Fz, slip)`

| Campo | Conteúdo |
|---|---|
| Domain | Tire (Bloco I) |
| Definition | Força longitudinal do pneu em função de carga vertical e razão de escorregamento (slip ratio), conforme dataset/modelo do OptimumTire (nível 1 lookup ou nível 2 paramétrico, DEC-007). |
| Equation | Não reimplementada — consumida diretamente do dataset exportado (tabela ou coeficientes) |
| Variables | `Fz` (`SUS-104`), `slip ratio` |
| Units | N (força); adimensional (slip ratio) |
| Sign Convention | Verificar explicitamente a convenção de sinal de slip ratio exportada pelo OptimumTire/TTC contra a convenção do veículo (ISO 8855) antes de consumir diretamente — mesma classe de risco já identificada para `SUS-501` |
| Reference/Source | TTC → OptimumTire — autoridade de caracterização de pneu |
| Data Type | REFERENCE |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de pneus |
| Revision | Tire REV |
| Validation Method | Comparação do pipeline consumido contra a curva bruta exportada do OptimumTire |

### SUS-503 — `μ` efetivo

| Campo | Conteúdo |
|---|---|
| Domain | Tire (Bloco I) |
| Definition | Coeficiente de atrito efetivo instantâneo, derivado das forças do pneu já calculadas. |
| Equation | `μ_eff = √(Fx² + Fy²) / Fz` |
| Variables | `SUS-501`, `SUS-502`, `SUS-104` |
| Units | Adimensional |
| Data Type | CALCULATED |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de pneus |
| Revision | Dynamics REV |
| Validation Method | Checagem de faixa plausível (`0 < μ_eff < μ_max` do dataset do pneu) |

---

## Steering e Aero (escopo reduzido, sem física nova)

### SUS-601 — Steering Ratio

| Campo | Conteúdo |
|---|---|
| Domain | Steering |
| Definition | Razão entre o ângulo do volante e o ângulo médio das rodas dianteiras. |
| Equation | `SR = Δsteering_wheel / Δwheel_angle,avg` |
| Data Type | INPUT (medido) ou MODEL (geometria da cremalheira) |
| Assumptions | V3.0 (EDR-052): Ackermann (SUS-414), ride steer (SUS-408) e roll steer (SUS-415) passam a ser calculados. Aproximação para cremalheira (Milliken p. 718): SR ≈ 360/asin(c/braço) [°], com a barra quase perpendicular ao braço; o livro imprime asin(c/braço)/360, inverso da razão definida na p. 716 (errata adotada). `steering_ratio_rack_approx` (TC-KIN-124b); planilha 07_KINEMATICS B78:B80 |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de steering |
| Revision | Geometry REV |
| Validation Method | Comparação com medição física da cremalheira |

### SUS-701 — Downforce

| Campo | Conteúdo |
|---|---|
| Domain | Aero |
| Definition | Força de downforce aerodinâmica, valor fixo por Setup (sem modelo de centro de pressão variável). |
| Data Type | INPUT |
| Assumptions | Valor único por Setup/velocidade de referência — sem mapa aerodinâmico completo (fora do escopo da V1) |
| Lifecycle/Validation Status | DRAFT / NOT_VALIDATED |
| Owner | Responsável de aero |
| Revision | Setup-specific |
| Validation Method | Comparação com dados de túnel de vento/CFD externo, se disponível |

### SUS-702 — Aero Balance

| Campo | Conteúdo |
|---|---|
| Domain | Aero |
| Definition | Fração da downforce total atuando no eixo dianteiro, valor fixo por Setup. |
| Equation | `Fz_aero,F = SUS-701 · SUS-702`; `Fz_aero,R = SUS-701 · (1 − SUS-702)` |
| Variables | `SUS-701` (downforce total), `SUS-702` (fração dianteira, 0 a 1) |
| Units | Adimensional (fração) |
| Assumptions | Valor único por Setup/velocidade de referência — sem mapa aerodinâmico completo nem centro de pressão variável (fora do escopo da V1) |
| Reference/Source | Dados de túnel de vento/CFD externo, ou estimativa da equipe |
| Data Type | INPUT |
| Target/Requirement | — |
| Lifecycle Status | DRAFT |
| Validation Status | NOT_VALIDATED |
| Owner | Responsável de aero |
| Revision | Setup-specific |
| Validation Method | Comparação com dados de túnel de vento/CFD externo, se disponível |

---

## Bloco J — Design Mode (nota de localização, não uma ficha nova)

Design Mode não tem parâmetros físicos próprios — é o modo reverso de cálculo já embutido nas fichas que o suportam. Não introduz `SUS-XXX` novos; consolidado aqui apenas como referência de onde encontrá-lo:
- `SUS-202` (Wheel Rate) — equação reversa `K_spring = K_wheel · MR_RH²`, acionada quando `K_wheel` vem de `SUS-205` em vez de `SUS-201`.
- `SUS-205` (Natural Frequency) — equação reversa `K_wheel = (2π·f_target)² · m_sprung,corner`, acionada a partir de um `TARGET-XXX` de frequência.
- `SUS-206`/`SUS-207` (Roll Stiffness) — mesma lógica se a equipe quiser definir um `TARGET-XXX` de roll gradient e resolver a distribuição de rigidez necessária (a equação reversa para uma distribuição `λ_f` alvo está em `SUS-208`; a equação reversa para um roll gradient alvo continua não escrita).

---

## Status final — V1.0 fisicamente completa

39 fichas escritas por extenso (contagem V1.0 por cabeçalhos; a versão anterior dizia 38) (nenhuma mais como referência "análoga a outra ficha" — as cinco que estavam nesse estado, `SUS-005`, `SUS-011`, `SUS-405`, `SUS-502`, `SUS-702`, foram completadas integralmente nesta revisão), cobrindo o escopo físico da V1.0 nos blocos A, B, C, D, E, F, G, H, I, Steering/Aero, com Design Mode (Bloco J) documentado como modo reverso dentro das fichas que o suportam, não como bloco de parâmetros próprios.

Status da especificação: todas as grandezas necessárias para o escopo físico V1.0 foram identificadas e formalizadas; as fichas permanecem `DRAFT`/`NOT_VALIDATED` até a execução dos respectivos Test Cases. Nenhuma física nova falta para a V1.0. O que resta agora não é mais "o que calcular", e sim "confirmar que calcula certo":

1. Rodar o piloto end-to-end (`MR → Wheel Rate → Natural Frequency`, base já completa desde as primeiras 13 fichas).
2. Implementar `SUS-101` a `SUS-104` em Python e rodar `TC-001` a `TC-008` (testes de conservação e limites, todos já verificáveis analiticamente).
3. Confirmar a linha geométrica de `SUS-301`/`SUS-302` com a configuração real de freio/trem de força antes de tirar esses dois itens de `DRAFT`.
4. Só então mover cada ficha de `DRAFT` para `CHECKED`/`FROZEN` conforme os Test Cases forem passando — nenhuma ficha deveria chegar ao Excel/Python final ainda em `DRAFT`.

A partir daqui, o trabalho deixa de ser "arquitetura" ou "engenharia declarada" e passa a ser implementação e verificação — exatamente o ponto em que vale começar a escrever código, não mais documentos de especificação.

---

## Log de Validação — piloto Python executado

Implementação em `suspension_model_V2_0.py` + `test_suspension_model_V2_0.py`, executada com sucesso: **16/16 testes PASS** (`TC-001` a `TC-010`, mais o piloto end-to-end e o fechamento do ciclo Design Mode).

Resultados de referência (veículo de teste, não um setup real): `TC-005` fechou exatamente (`882.9 = 882.9`, sem diferença de arredondamento); o piloto `MR=0.8, Ks=100 N/mm, ms=50 kg` deu `fn = 8.897 Hz`, consistente com o valor verificado manualmente na seção 17.8.

Fichas que passam de `DRAFT`/`NOT_VALIDATED` para `CHECKED`/`PASS` com base nesta execução:

| ID | Test Case(s) que validou |
|---|---|
| `SUS-009` | Usado corretamente em TC-007/TC-008 (massa suspensa e distribuição) |
| `SUS-012` | Usado corretamente em TC-005/TC-007/TC-008 (h_s fecha a conservação) |
| `SUS-101` | TC-001c/d, TC-003, TC-004 |
| `SUS-102` | TC-002, TC-003 |
| `SUS-103` | TC-001a/b, TC-005, TC-006, TC-007, TC-008 |
| `SUS-104` | TC-001c/d, TC-003, TC-004 |
| `SUS-201`/`SUS-202` | TC-009, piloto |
| `SUS-205` | TC-010, piloto, ciclo Design Mode |
| `SUS-208` | TC-006 |

**Importante:** `CHECKED`/`PASS` aqui significa "cross-check interno consistente" (Python contra as próprias equações e contra os limites analíticos esperados) — ainda **não** é `REFERENCE-validated` (comparação com OptimumKinematics/Lotus/TTC, que depende de dados reais da equipe ainda não disponíveis nesta conversa). Continuam em `DRAFT`: todas as fichas REFERENCE (Bloco E, Tire Model) e `SUS-301`/`SUS-302` (aguardando confirmação da linha geométrica de freio/trem de força).


---

## Status V1.0 e Log de Validação — kinematics

Execução em 2026-10-09 (resultado de código):
- `suspension_model_V1_0.py` + `test_suspension_model_V1_0.py`: **16/16 PASS** (mesmo resultado do log anterior).
- `kinematics_model_V1_0.py` + `test_kinematics_model_V1_0.py`: **11/11 PASS** (`TC-KIN-001` a `TC-KIN-006`; SUS-402, SUS-403 e SUS-406). O "5/5" citado em documentos anteriores era a contagem antes da inclusão do SUS-406.
- Os valores de referência do `TC-KIN-001` (IC = −0,94783 / 0,35652; RC = 0,14503 m) foram reproduzidos por cálculo independente, fora do módulo. As retas do `TC-KIN-006` conferem como paralelas (mesma inclinação).
- `TC-KIN-005d` dá %AD = 421,8: é verificação matemática com geometria sintética, não representa um carro.

Status das fichas de kinematics: `SUS-402` e `SUS-406` permanecem `CHECKED` / `NOT_VALIDATED` (geometria sintética, sem hardpoints reais). `SUS-401`, `SUS-403`, `SUS-404`, `SUS-405` permanecem `DRAFT` (REFERENCE sem dado do OptimumKinematics).

Pendências conhecidas, não resolvidas na V1.0:
- `SUS-203` (Spring Rate) e `SUS-204` (Roll Stiffness total) existem na Dependency Matrix da arquitetura (seção 17.5), mas não têm ficha própria.
- `SUS-404`/`SUS-405` não têm Test Case de sinal numerado.
- `TC-011` e `TC-012` (comparação com OptimumKinematics e com Lotus) dependem de dados reais.
- Aviso de plausibilidade para `Fz < 0` (`SUS-104`) está especificado, mas não implementado no `suspension_model_V1_0.py` (existe na planilha). **Resolvido na V2.0** (`FzLiftoffWarning`, ver log V2.0).


---

## Status V2.0 e Log de Validação (resultado de código, 2026-10-09)

| Suíte | Resultado |
|---|---|
| `test_kinematics_model_V2_0.py` | **47/47 PASS** (11 herdados TC-KIN-001..006 + 36 novos, TC-KIN-101..117) |
| `test_hardpoints_V2_0.py` | **21/21 PASS** (schema, validações, adapter Lotus) |
| `test_suspension_model_V2_0.py` | **33/33 PASS** (16 herdados + 17 novos: bloqueios do Guide D.2, aviso Fz<0, MR pequeno, regressão idêntica à V1.0) |

**Teste de mutação (resultado de código).** Injetados 14 bugs distintos no kinematics (sinais de camber, toe, KPI, caster, scrub, trail, track, lado; MR invertido; resíduo errado; cremalheira ignorada; IC e RC deslocados; sinal do anti-dive) e 6 nas validações da suspensão: **todos detectados**. Antes da rodada de correção, 3 mutantes (sinais de KPI, scrub e caster) passavam sem detecção; foi acrescentado `TC-KIN-117`.

**Incertezas quantificadas** (geometria sintética; ver SUS-407, 409, 411 e 412): propagação de σ=0,5 mm nos hardpoints (RC 13%, camber estático σ 0,5°, ganho de camber 4%, MR 1,4%, %AD 2,7%); método de IC lateral (%AD 36,3 / 38,0 / −680,7); passo FD; contact patch fixo vs disco fino.

**Limites desta validação.** Toda geometria é sintética ou fixture analítica. **Nenhum resultado foi comparado com OptimumKinematics, Lotus ou dado real do carro:** `TC-011` e `TC-012` seguem NOT_VALIDATED, e as fichas SUS-407 a SUS-413 estão `CHECKED` apenas no sentido de cross-check interno.

**Pendências (decisão ou dado da equipe):** aprovação dos IDs SUS-407..413 e do schema de hardpoints; adoção do IC lateral cinemático e do %AD com sinal (propostas nas notas de SUS-406/301/302); configuração real de freio/trem de força (`reaction_point`); definição de curso `z` usada pelo OptimumKinematics; `SUS-203`/`SUS-204` sem ficha; TC de sinal para SUS-404/405; limite de aviso de MR (0,2 é hipótese).
