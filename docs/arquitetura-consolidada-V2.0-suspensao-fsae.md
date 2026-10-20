# Arquitetura Consolidada V2.0 — Sistema de Dimensionamento e Dinâmica Veicular (Suspensão) | FSAE EV

**Versão:** V2.0 (2026-10-09). Base: `arquitetura-consolidada-V1.0`. Mudanças desta versão: IDs SUS-407..413 no adendo da Dependency Matrix (17.5), namespaces de Test Cases novos (17.7), nota de anti-dive com sinal (17.3). Nenhuma decisão física congelada foi alterada. Ver `registro-de-versoes-V2.0.md`.

**Status deste documento:** base de referência para o Engineering Standard. Ainda não é o Standard em si — é o "contrato" estrutural que o Standard vai preencher equação por equação.

---

## 1. Grafo físico consolidado (corrigido)

Correções aplicadas em relação à última versão: (1) `Static Load Model` ramifica direto de `Vehicle Definition`, em paralelo a `Vehicle State`, não depois dele; (2) duas setas cruzadas adicionadas onde os dois caminhos fisicamente se encontram (`Fz by Corner`/`Load Transfer` → `Suspension Model`, e `Tire Model` → `Suspension Loads`); (3) ramo de cross-check (MODEL/CHECK) do Python reintroduzido em paralelo ao REFERENCE do OptimumKinematics, conforme DEC-002/DEC-003; (4) acoplamento Vehicle State → KOP mantido como seta pontilhada, explicitamente fora de escopo da V1.

```
                    ┌─────────────────────────┐
                    │   VEHICLE DEFINITION     │
                    │ Mass / CG / Wheelbase /  │
                    │ Track / Aero (basic)     │
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 ▼                                 ▼
       ┌────────────────────┐           ┌──────────────────────┐
       │  STATIC LOAD MODEL │           │     VEHICLE STATE     │
       │  Fz static/corner  │           │ ax / ay / v / steer / │
       │  (não depende de   │           │ aero / setup          │
       │   manobra)         │           └──────────┬────────────┘
       └─────────┬──────────┘                      │
                 │                                 ▼
                 │                      ┌──────────────────────┐
                 │                      │   LOAD TRANSFER       │
                 │                      │ Longitudinal          │
                 │                      │ Lateral (sprung+      │
                 │                      │  unsprung)            │
                 │                      │ Combined (superpos.)  │
                 │                      └──────────┬────────────┘
                 └───────────────┬──────────────────┘
                                 ▼
                     ┌─────────────────────┐
                     │   Fz BY CORNER      │
                     │   FL / FR / RL / RR │
                     └──────┬───────┬──────┘
                            │       │
                            ▼       │
                  ┌──────────────┐ │
                  │  TIRE MODEL  │ │
                  │ OptimumTire  │ │
                  │ Fx / Fy / µ  │ │
                  └──────┬───────┘ │
                         │         │
        (cross para SUSPENSION MODEL e FEA, ver abaixo) 
                         │         │
                         │         │  ── seta cruzada nova ──▶ [para SUSPENSION MODEL: componente
                         │         │                            longitudinal de Load Transfer,
                         │         │                            necessária para anti-dive/squat]
                         └─────────┴───────────────────────────┐
                                                                 │
CAD / HARDPOINTS                                                │
       │                                                        │
       ▼                                                        │
OptimumKinematics / Lotus ───────────┐                          │
       │                             │ (cross-check paralelo,   │
       │                             │  DEC-002/DEC-003)        │
       ▼                             ▼                          │
┌─────────────────────────┐  ┌──────────────────────────┐       │
│  KINEMATIC REFERENCE     │  │   MODEL / CHECK (Python) │       │
│ KOP → RC / IC / Camber / │  │ RC e MR simplificados no │       │
│  Toe / MR / etc.         │  │ ride height — sanity     │       │
│  (autoridade)            │  │ check, nunca substitui   │       │
└────────────┬─────────────┘  │ o REFERENCE              │       │
             │                └──────────────────────────┘       │
             ▼                                                   │
     ┌─────────────────┐    ◄── seta cruzada nova: Fz by Corner /│
     │ SUSPENSION MODEL │        Load Transfer entram aqui ───────┘
     │ Wheel Rate       │
     │ Spring Rate      │
     │ Roll Stiffness   │
     │ Anti-dive        │◄── consome IC (Kinematic Reference) + parcela
     │ Anti-squat       │    longitudinal de Load Transfer (Vehicle Dynamics Path)
     │ Natural Frequency│
     └────────┬─────────┘
              │
              ▼
      Suspension Loads  ◄── seta cruzada nova: Tire Model (Fx/Fy/Fz no
              │              contato) entra aqui junto com a geometria
              ▼
            FEA


             DESIGN MODE
                  ▲
                  │
         TARGETS / REQUIREMENTS
                  │
                  ▼
        Required Performance
                  │
                  ▼
         Required Stiffness
                  │
                  ▼
          Spring / MR / Setup
                  │
                  └──────→ SUSPENSION MODEL (fluxo reverso — relações
                                              analíticas fechadas, sem
                                              Goal Seek/solver genérico)


VEHICLE STATE ┄┄┄┄(acoplamento NÃO resolvido na V1)┄┄┄┄▶ KINEMATIC OPERATING POINT
   (a_y, a_x geram roll/pitch reais, que deslocariam a suspensão e
    mudariam o KOP efetivo — V1 usa KOP prescrito/selecionado manualmente,
    não calculado a partir do Vehicle State)
```

### 1.1 Causalidade linear explícita (elimina ambiguidade visual do ASCII acima)

```
Vehicle Definition + Vehicle State → Load Transfer (Δ) → soma com Static Load → Fz BY CORNER
Fz BY CORNER + Tire Reference (REFERENCE) + Kinematic Reference → Tire Forces / Tire Utilization
Tire Forces + Suspension Geometry (Suspension Model) → Suspension Loads → FEA
```
O pneu nunca é usado para calcular Load Transfer — ele consome `Fz BY CORNER` já calculado, na direção oposta à que poderia ser mal-lida no ASCII acima. Essa causalidade já estava correta na versão anterior do grafo; esta seção só remove a ambiguidade visual.

### 1.2 Grafo executivo (visão simplificada — derivada da seção 1, não substituta)

Útil para comunicar o propósito da V1 sem o detalhe de cross-check e revisão. **A versão canônica para o Engineering Standard continua sendo a seção 1** (inclui o ramo MODEL/CHECK do Python e a seta explícita Kinematic Reference → Suspension Model, ambos omitidos aqui por simplicidade):

```
                VEHICLE
                   │
          ┌────────┴────────┐
          ↓                 ↓
     STATIC LOAD       VEHICLE STATE
          │                 │
          └───────┬─────────┘
                  ↓
          Fz BY CORNER  (soma static + Δload transfer)
                  │
       ┌──────────┴──────────┐
       ↓                     ↓
 TIRE REFERENCE        SUSPENSION MODEL ◄── Kinematic Reference (RC/IC/MR/Camber/Toe)
       │                     │
       └──────────┬──────────┘
                  ↓
          SUSPENSION LOADS
                  ↓
                 FEA

TARGET / REQUIREMENT → DESIGN MODE → Required Performance → Required Stiffness
                                                                    → Spring/MR/Setup → SUSPENSION MODEL
```
V1 responde, para um dado Vehicle + Setup + Vehicle State + Kinematic Operating Point: *"quais forças e cargas o veículo produz, como se distribuem entre os quatro pneus, e o que isso exige de rigidez e componentes de suspensão"* — e, no sentido inverso, *"dado um requisito de comportamento, quais valores de rigidez/mola/MR são necessários"*.

---

## 2. Faixas de ID por domínio (resolve a colisão SUS-001/002 encontrada)

| Faixa | Domínio | Exemplos |
|---|---|---|
| `SUS-0XX` | Vehicle Definition (inputs de veículo) | SUS-001 Vehicle Mass, SUS-002 CG Height, SUS-003 Wheelbase, SUS-004 Front Track, SUS-005 Rear Track |
| `SUS-1XX` | Static Load / Load Transfer / Fz por canto | SUS-101 Static Fz, SUS-102 Longitudinal ΔFz, SUS-103 Lateral ΔFz, SUS-104 Combined Fz by corner |
| `SUS-2XX` | Suspension Stiffness (MR, spring/wheel rate, roll stiffness, frequência) | SUS-201 Motion Ratio, SUS-202 Wheel Rate, SUS-203 Spring Rate, SUS-204 Roll Stiffness (front/rear/total), SUS-205 Natural Frequency |
| `SUS-3XX` | Anti-geometry (anti-dive/anti-squat) | SUS-301 Anti-Dive %, SUS-302 Anti-Squat % |
| `SUS-4XX` | Kinematics (REFERENCE consumido: RC, IC, camber, toe, e o cross-check MODEL/CHECK) | SUS-401 Roll Center (REFERENCE), SUS-402 Roll Center (MODEL/CHECK), SUS-403 Instant Center, SUS-404 Camber gain, SUS-405 Toe curve |
| `SUS-5XX` | Tire Model (consumido do OptimumTire) | SUS-501 Fy(Fz, α, γ), SUS-502 Fx(Fz, slip), SUS-503 μ efetivo |
| `SUS-6XX` | Steering (reduzido) | SUS-601 Steering ratio |
| `SUS-7XX` | Aero (reduzido) | SUS-701 Downforce, SUS-702 Aero balance |
| `SUS-8XX` | Setup / Configuration | SUS-801 Setup definition, SUS-802 Setup comparison |
| `SUS-9XX` | Requirements / Targets | SUS-901 Requirement, SUS-902 Target |
| `REQ-XXX` | Requirements (namespace próprio) | REQ-001 = "frequência dianteira entre X e Y Hz" |
| `VAL-XXX` | Validation Matrix (namespace próprio) | VAL-014 = validação de SUS-205 |

**Correção de nomenclatura:** não usar o mesmo ID em Requirement, Standard e Validation. Cada namespace é independente (`REQ-XXX`, `SUS-XXX`, `VAL-XXX`); uma tabela de rastreabilidade separada conecta os três (ex.: `REQ-001 → SUS-205, SUS-204 → VAL-014, VAL-015`). Isso evita forçar 1:1 quando um requisito depende de vários parâmetros, ou quando o mesmo parâmetro é validado contra mais de uma referência.

Cada domínio reserva um bloco de 100 IDs — suficiente para a V1 e com folga para V1.1, sem precisar renumerar depois.

---

## 3. Taxonomia final (Data Type / Metadata / Status)

### Data Type (natureza do dado)
- INPUT
- TARGET
- REFERENCE
- MODEL
- CALCULATED
- REQUIREMENT

*(AUTHORITY não é um Data Type — é metadado, ver abaixo.)*

### Metadata (propriedades do parâmetro/domínio, não do valor em si)
- Authority
- Source
- Owner
- Revision (independente por domínio — Geometry REV, Kinematics REV, Tire REV, Dynamics REV, Setup)
- Status
- Freeze level
- Provenance
- Timestamp

### Status — duas dimensões independentes, nunca misturadas em uma lista única

**Lifecycle Status** (maturidade do parâmetro/equação em si):
- OPEN — não definido ainda
- DRAFT — em elaboração
- CHECKED — cross-checado internamente (ex. Python ↔ MATLAB)
- FROZEN — aceito como base de projeto
- STALE — foi FROZEN, mas uma dependência upstream mudou de revisão

**Validation Status** (resultado da comparação MODEL vs. REFERENCE, independente do lifecycle):
- NOT_VALIDATED — ainda não comparado
- PASS — validado dentro da tolerância
- WARNING — divergência acima da tolerância numérica, mas dentro da tolerância de engenharia
- FAIL — divergência acima da tolerância de engenharia (não significa necessariamente "modelo errado", significa "não validado")

Um parâmetro pode legitimamente estar em `Lifecycle = FROZEN` e `Validation = STALE` ao mesmo tempo (era válido, uma dependência mudou) — por isso as duas dimensões não podem ser uma lista única.

---

## 4. Convenções físicas congeladas (DEC-001)

- Sistema de eixos: **ISO 8855** — X positivo para frente, Y positivo para a esquerda, Z positivo para cima (destrógiro). Origem definida pelo CAD, ponto estrutural de referência (não necessariamente o CG).
- Todas as convenções angulares derivam estritamente da regra da mão direita sobre esse sistema, sem exceções "intuitivas":
  - Roll positivo: lado esquerdo sobe / lado direito desce
  - Pitch positivo: **nariz desce** / traseira sobe (consistente com ISO 8855 — confirmado contra a literatura)
  - Yaw positivo: anti-horário visto de cima (nariz vira para a esquerda)
  - Momentos (roll, pitch, yaw): regra da mão direita em torno de +X, +Y, +Z respectivamente
- Camber, toe e demais convenções geométricas: a formalizar com diagrama explícito no Standard, verificadas contra a convenção real exportada pelo OptimumKinematics/Lotus da equipe (pendência de verificação prática — confirmar configuração Z-up/Z-down do software antes do freeze final desse item).
- Unidades: SI puro no núcleo de cálculo (kg, m, N, N·m, m/s, m/s², N/m, Hz, rad); conversão para unidades de interface (mm, N/mm, °, km/h) só na camada de apresentação (Excel).

---

## 5. Definições congeladas de Motion Ratio, RC, IC e Anti-geometry

- **Motion Ratio:** `MR = Δwheel travel / Δspring travel` (convenção wheel/spring, não a inversa). Nomenclatura obrigatória em todo lugar: `MR [wheel/spring]` no Excel, `motion_ratio_wheel_spring` no Python — nunca só "MR". Relação: `k_wheel = k_spring / MR²`. V1 usa `MR_RH` (valor no ride height estático) como MODEL principal; arquitetura preparada para `MR(z)` futuramente. Valor pode vir como REFERENCE do OptimumKinematics e ser cross-checado por um cálculo geométrico simplificado em Python (MODEL/CHECK).
- **Roll Center:** autoridade é o OptimumKinematics (`RC_official = RC_OptimumKinematics`), incluindo a curva `RC(z)`. V1 usa `RC_static = RC(z_RH)` (o ponto da curva no ride height de referência) como entrada do Load Transfer Model — a migração de RC durante rolagem é uma limitação conhecida e documentada, não modelada diretamente na V1. Importante: `RC(z)` continua existindo por completo no dataset REFERENCE mesmo que a V1 só consuma o ponto estático — "V1 usa RC estático" não significa "o sistema só conhece RC estático". Cálculo geométrico simplificado em Python existe apenas como sanity check (MODEL/CHECK), nunca substitui o REFERENCE.
- **Cautela de nomenclatura (Motion Ratio):** manter apenas `MR_RH` (valor no ride height, V1) e `MR(z)` (curva, arquitetura preparada) como termos oficiais. Evitar introduzir "MR_effective" sem definição fechada — esse termo tende a sugerir efeitos não-geométricos (compliance de buchas, folga, atrito), que estão explicitamente fora do escopo da V1. Se um dia for necessário, precisa ser uma decisão própria, não um sinônimo informal de `MR(z)`.
- **Instant Center → Anti-dive/Anti-squat:** OptimumKinematics fornece o IC (REFERENCE); Python calcula o percentual de anti-dive/anti-squat a partir do IC + geometria + a parcela de transferência longitudinal de carga vinda do Vehicle Dynamics Path (MODEL). A metodologia exata (dentre as abordagens da literatura — side-view swing arm, força longitudinal, referências tipo Milliken) ainda está **em aberto**, a ser fechada em etapa de pesquisa técnica específica antes de virar equação no Standard.
- **Hipótese congelada de anti-dive/anti-squat** (texto para entrar literalmente no Standard):
  > *"Anti-dive e anti-squat não alteram a magnitude da transferência de carga longitudinal determinada pelo equilíbrio de corpo rígido do veículo. Eles descrevem a parcela da reação longitudinal transmitida geometricamente pela suspensão, em oposição à parcela associada à reação elástica, influenciando a atitude de pitch e o curso de suspensão, bem como a distribuição de esforços nos componentes da suspensão."*
  > Sequência de cálculo: aceleração longitudinal → transferência global de carga → forças nos pneus → caminhos de carga → anti-dive/anti-squat → atitude/curso/forças nos componentes. `ΔFz,long` nunca é descontado por `(1 − %AD)`.

---

## 6. Kinematic Operating Point (KOP) vs. Vehicle State (VS)

- **KOP** — descreve *onde a suspensão está* (posição de curso: ride height, +20/+40 mm bump, −20/−40 mm rebound etc.). Usado para consultar curvas do OptimumKinematics (camber, toe, RC, IC, MR).
- **VS** — descreve *o que o veículo está fazendo* (a_x, a_y, velocidade, steering, aero, setup). Usado para load transfer, combined loading, Fz por pneu, utilização de pneu, cargas de suspensão.
- Existe uma relação física real entre os dois (VS gera roll/pitch reais, que deslocam a suspensão e mudariam o KOP efetivo), mas esse acoplamento iterativo **não é resolvido na V1** — é representado no grafo como dependência pontuada, explicitamente fora de escopo.
- **Hipótese congelada** (texto para o Standard): *"V1 utiliza Kinematic Operating Points prescritos ou selecionados pelo usuário para representar a geometria da suspensão. O acoplamento iterativo completo entre estado dinâmico do veículo e posição instantânea da suspensão está fora do escopo da V1."*

---

## 7. Hierarquia de dados (DEC-008)

```
PROJECT
│
├── VEHICLE            (massa, CG, wheelbase etc.)
│
├── SETUP              (combinação de parâmetros)
│   ├── FRONT AXLE     (roll stiffness, axle load, track)
│   │   ├── FL         (wheel load, spring, damper, MR)
│   │   └── FR
│   └── REAR AXLE
│       ├── RL
│       └── RR
│
└── REFERENCES         (OptimumKinematics, OptimumTire, Lotus, CAD)
```

---

## 8. Sistema de revisão e dependências (DEC-011, DEC-012)

- Cada domínio tem revisão própria e independente: `Geometry G-REV-X`, `Kinematics K-REV-X`, `Tire T-REV-X`, `Dynamics D-REV-X`, `Setup S-XXX`. Nunca uma letra de revisão única compartilhada.
- Cada resultado registra suas dependências de revisão (ex.: `D-REV-D` foi calculado com `Geometry G-REV-C`, `Kinematics K-REV-B`, `Tire T-REV-A`).
- Se uma dependência avança de revisão, o resultado que dependia da revisão antiga não é apagado — vira `STALE`.
- Hardpoints entram no sistema via arquivo intermediário padronizado (`hardpoints.csv`, campos `Point_ID | X | Y | Z | Component | Status`) — Geometry Contract único, consumido por Python, OptimumKinematics e Excel. Não digitar hardpoints manualmente em mais de um lugar.
- Design Intent (CAD) vs. As-Built (peça fabricada/medida) são registrados como duas categorias distintas quando divergirem — arquitetura preparada para isso na V1, sem desenvolvimento profundo ainda (prepara caminho para tolerance analysis futura).

---

## 9. Processo de divergência entre ferramentas (DEC-013)

```
MODEL ≠ REFERENCE
        ↓
    INVESTIGAR
        ↓
1. Units → 2. Coordinate system → 3. Hardpoints → 4. Configuration
→ 5. Assumptions → 6. Equations → 7. Solver settings → 8. Interpolation
        ↓
Causa encontrada?
   ↙ SIM              ↘ NÃO
 Corrigir modelo    Aplicar tolerância de engenharia
   ↓                     ↓
 Revalidar          PASS / WARNING / FAIL / OPEN (se não houver base de tolerância)
```

- Nunca corrigir o resultado só para fazê-lo coincidir com a referência.
- Tolerância nunca é um percentual universal — é definida por parâmetro, com duas camadas: *numerical agreement* (arredondamento/discretização/interpolação/solver) e *engineering agreement* (erro máximo aceitável para aquela decisão de projeto).
- `FAIL` não significa "nosso modelo está errado" — significa "não pode ser considerado validado".

---

## 10. Data Architecture (DEC-015, DEC-016)

- Python externo ao Excel (sem xlwings/PyXLL/macros complexas na V1).
- Intercâmbio: JSON para configuração (`vehicle.json`, `setup.json`), CSV para dados tabulares/curvas (`hardpoints.csv`, `kinematics.csv`, `tire_model.csv`), JSON para resultados (`results.json`).
- Cada arquivo de intercâmbio carrega metadado mínimo: revisão de origem por domínio, versão do script, timestamp, freeze level.
- Controle de versão: Git para código Python, Engineering Standard, JSON, CSV, documentação e templates. Excel versionado à parte, com cuidado (não é código-fonte tradicional).
- Estrutura de repositório:
```
Suspension-System/
├── docs/
├── python/
├── data/
├── references/
├── excel/
└── tests/
```
- Releases versionadas (`V1.0.0`, `V1.0.1`, `V1.1.0`).
- **Regra não negociável:** nenhum arquivo de intercâmbio depende de unidade implícita. O schema do arquivo declara a unidade de cada campo explicitamente (ex. `X_m: 0.450`, não `X: 0.450`). Evita o erro clássico de importar 450 mm como 450 m.

---

## 11. Requirements ≠ Targets (DEC-020)

- **Requirement:** algo que precisa ser satisfeito (ex.: frequência dianteira entre X e Y Hz).
- **Target:** algo que se quer atingir dentro do requirement (ex.: frequência-alvo = 2,5 Hz).
- Cadeia de rastreabilidade com namespaces independentes (seção 2): `REQ-XXX → SUS-XXX (Engineering Standard) → VAL-XXX (Validation)`, conectados por uma tabela de rastreabilidade separada, não pelo mesmo ID repetido. Um `REQ` pode apontar para vários `SUS`, e um `SUS` pode ser checado por vários `VAL`.

---

## 12. Test Cases obrigatórios (DEC-021)

Nenhum resultado do Python é considerado confiável sem passar por casos de teste, incluindo no mínimo:
- Veículo idealizado sem aceleração lateral → transferência lateral esperada = 0
- Massa simétrica + frenagem → verificação de simetria do resultado
- Curva sem aero → comparação com solução analítica conhecida
- Comparação direta contra solução analítica de livro-texto
- Comparação contra saída do OptimumKinematics (para os parâmetros REFERENCE+MODEL)

---

## 13. Escopo V1.0 vs. V1.1 (DEC-017)

**V1.0 — Engineering Core (tem que funcionar muito bem):**
Física: vehicle, static loads, load transfer longitudinal/lateral/combined, roll stiffness, wheel rate, spring rate, motion ratio, natural frequency, anti-dive, anti-squat, bump/rebound básico, steering básico, aero básico.
Sistema: setups, targets, references, Python, Excel, validation (com status OPEN/PASS/WARNING/FAIL/STALE), revision metadata.

**V1.1 — Engineering Intelligence (depois que o núcleo estiver rodando):**
Sensitivity analysis, plausibility checks avançadas, dependency tracking automatizado, requirements traceability formal, uncertainty propagation, relatórios automatizados.

---

## 14. Template de campos do Engineering Standard (para preencher equação por equação)

| Campo | Descrição |
|---|---|
| ID | `SUS-XXX` na faixa correta (seção 2) |
| Parameter | Nome do parâmetro |
| Domain | Vehicle / Loads / Stiffness / Anti-geometry / Kinematics / Tire / Steering / Aero |
| Definition | Definição textual não ambígua |
| Equation | Fórmula formal com variáveis nomeadas |
| Variables | Tabela de variáveis, unidades, origem (Data Type) |
| Units | SI internamente; unidade de interface separadamente |
| Sign Convention | Referência à seção 4 |
| Assumptions | Hipóteses específicas desta fórmula |
| Reference/Source | Livro-texto, norma, documentação da ferramenta — nunca inventado |
| Validity Domain | Faixa de aplicabilidade (ex. "válido só no ride height estático") |
| Input/Calculated/Reference | Data Type (seção 3) |
| Target / Requirement | Se aplicável, IDs vinculados (seção 11) |
| Status | Seção 3 |
| Owner | Responsável pela definição |
| Freeze Level | OPEN/DRAFT/CHECKED/FROZEN |
| Revision | Revisão própria do domínio (seção 8) |
| Validation Method | Test case aplicável (seção 12) |

---

## 15. Estrutura da Validation Matrix

| Campo |
|---|
| SUS-ID validado |
| Our Model (valor) |
| Reference Tool + valor |
| Error (%) |
| Numerical tolerance |
| Engineering tolerance |
| Tolerance basis |
| Operating Point — **especificar se é KOP, VS, ou ambos** |
| Geometry/Kinematics/Tire/Dynamics revision usada |
| Status (seção 3) |

---

## 16. Ordem de trabalho a partir daqui

1. Fechar a pendência prática de convenção de eixos do OptimumKinematics/Lotus da equipe (Z-up/Z-down real configurado).
2. Fechar a metodologia única de anti-dive/anti-squat (pesquisa técnica dedicada, seção 5).
3. Preencher a Dependency Matrix completa (todo `SUS-XXX` da V1.0, com "depende de" e "fonte" explícitos) usando as faixas da seção 2.
4. Escrever o Engineering Standard equação por equação, usando o template da seção 14, na ordem: Vehicle → Static Loads → Load Transfer → Kinematics (REFERENCE+MODEL/CHECK) → Suspension Stiffness → Anti-geometry → Tire → Design Mode.
5. Rodar o piloto end-to-end de um único parâmetro simples (wheel rate + natural frequency) atravessando todo o fluxo de dados antes de expandir aos demais.
6. Só então iniciar Python e Excel da V1.0.

Confira esta estrutura com calma — qualquer ajuste aqui é barato; ajustes depois que o Standard estiver escrito e o piloto rodando já custam retrabalho real.

---

## 17. Fechamento final (Milliken como espinha dorsal) — V1.0 pronta para o Engineering Standard

Hierarquia de referência definitiva: **Milliken** (framework matemático de vehicle dynamics) → **OptimumKinematics** (autoridade de kinematics) → **OptimumTire** (autoridade de pneu) → **Lotus** (cross-check independente) → **Python** (implementação do modelo) → **Excel** (interface/orquestração). Python é autoridade porque implementa uma equação previamente congelada, não porque "calculou".

### 17.1 Coordenadas com ferramentas externas
- Convenção da equipe (ISO 8855, já congelada): X-frente / Y-esquerda / Z-cima é a autoridade. Ferramentas externas se adaptam a ela, não o contrário.
- OptimumKinematics: configurar explicitamente Longitudinal=X+, Lateral=Y+, Vertical=Z+ no projeto — nunca confiar no default do software.
- Lotus (default): X-trás / Y-direita / Z-cima → adapter obrigatório e documentado no arquivo de intercâmbio: `X_target = -X_source; Y_target = -Y_source; Z_target = Z_source`.

### 17.2 Camber / Toe finais
- Camber positivo = topo da roda para fora (coincide com OptimumKinematics e Lotus — importação direta, sem conversão).
- Toe positivo = toe-out (coincide com OptimumKinematics). Lotus usa toe positivo = toe-in → `δ_toe,Tupã = −δ_toe,Lotus`.
- Nomenclatura obrigatória: nunca uma coluna "Camber" ou "Toe" sozinha — sempre `Camber [deg]`, `Camber_Positive = Wheel top outward`, `Toe_Positive = Toe-out` documentados ao lado do valor.

### 17.3 Anti-dive / Anti-squat — metodologia Milliken
Frente (frenagem):
$$ AD_f[\%] = FB_f \cdot \tan(\phi_f) \cdot \frac{L}{h_{CG}} \cdot 100 $$
Traseira (tração, RWD — generalizável a AWD com `TF_r`):
$$ AS_r[\%] = TF_r \cdot \tan(\phi_r) \cdot \frac{L}{h_{CG}} \cdot 100 $$
onde `φ_f`/`φ_r` = ângulo (side view) da linha contact patch → Instant Center; `FB_f`/`TF_r` = fração de força de frenagem/tração no eixo; `L` = wheelbase; `h_CG` = altura do CG. IC vem do OptimumKinematics (REFERENCE); Python calcula %AD/%AS (MODEL). **Nota V2.0:** as fórmulas acima valem com `tan φ` assinado pela posição do IC lateral em relação ao ponto de reação (o Standard V2.0 traz o achado e a proposta; nada foi congelado). **Status: metodologia FROZEN; equação como fórmula final fica `DRAFT → CHECKED` até passar pelo primeiro Test Case**, porque a definição geométrica exata do IC (contact patch vs. wheel center) ainda depende da configuração real de freio/trem de força da equipe. `SUS-301`/`SUS-302` nunca alimentam `SUS-102` (anti-geometry não altera a magnitude do load transfer longitudinal).

### 17.4 Transferência lateral — modelo de duas molas de Milliken (FROZEN, verificado)
$$ \Delta F_{zF} = \frac{a_y}{t_F}\left[\frac{K_{\phi F}}{K_{\phi F}+K_{\phi R}}m_s(h_s-z_s) + \frac{b}{L}m_s z_F + m_{uF}h_{uF}\right] $$
$$ \Delta F_{zR} = \frac{a_y}{t_R}\left[\frac{K_{\phi R}}{K_{\phi F}+K_{\phi R}}m_s(h_s-z_s) + \frac{a}{L}m_s z_R + m_{uR}h_{uR}\right] $$
com `z_s = (b/L)z_F + (a/L)z_R` (altura do roll axis na posição longitudinal do CG). `z_F`, `z_R` = `RC_static` (REFERENCE do OptimumKinematics, ride height estático — DEC-006). **Verificação feita:** somando `t_F·ΔF_zF + t_R·ΔF_zR` algebricamente, os termos se recombinam exatamente em `a_y·(m_s·h_s + m_uF·h_uF + m_uR·h_uR) = m·a_y·h_CG` (por definição de CG composto) — ou seja, a fórmula satisfaz a conservação global de momento por construção, não por coincidência. Zerando `z_F=z_R=0` a parcela geométrica desaparece; zerando `m_uF=m_uR=0` a parcela de massa não-suspensa desaparece — ambos os limites batem com a expectativa física. `SUS-103` nunca depende de `SUS-501` (Tire Model): causalidade é `Vehicle State → Load Transfer → Fz by Corner → Tire Model`, nunca o inverso.

### 17.5 Dependency Matrix v1 (namespace único `SUS-XXX`, faixas da seção 2 — `VEH/KIN/DYN/TIR/FREQ` de versões anteriores descartado)

| ID | Parâmetro | Depende de | Data Type |
|---|---|---|---|
| SUS-001 | Vehicle Mass | — | INPUT |
| SUS-002 | CG Height | — | INPUT |
| SUS-003 | Wheelbase | — | INPUT |
| SUS-004 | Front Track | — | INPUT |
| SUS-005 | Rear Track | — | INPUT |
| SUS-101 | Static Fz (corner) | SUS-001, 003, CG longitudinal | MODEL |
| SUS-102 | Longitudinal ΔFz | SUS-001, 002, 003, a_x | MODEL |
| SUS-103 | Lateral ΔFz | SUS-001, 002, 004, 005, K_φF/R, SUS-401 (RC), massas susp./não-susp., a_y | MODEL + REFERENCE |
| SUS-104 | Combined Fz/corner | SUS-101, 102, 103 | MODEL |
| SUS-201 | Motion Ratio (`MR_RH`) | hardpoints/geometria da mola | REFERENCE + MODEL (cross-check) |
| SUS-202 | Wheel Rate | SUS-203, SUS-201 — **Design Mode: dependência reversa a partir de SUS-205** | MODEL |
| SUS-203 | Spring Rate | Analysis: INPUT direto — **Design Mode: calculado a partir de SUS-202** | INPUT/MODEL (depende do modo ativo) |
| SUS-204 | Roll Stiffness (front/rear/total) | wheel rates + geometria/ARB | MODEL |
| SUS-205 | Natural Frequency | SUS-202 + massa suspensa por canto — **Design Mode: TARGET de entrada, não saída** | MODEL |
| SUS-301 | Anti-Dive | SUS-406-F (IC lateral), SUS-003, SUS-002, SUS-013 (brake bias) | REFERENCE + MODEL |
| SUS-302 | Anti-Squat | SUS-406-R (IC lateral traseiro), SUS-003, SUS-002, SUS-014 (fração de tração) | REFERENCE + MODEL |
| SUS-401 | Roll Center (REFERENCE) | hardpoints + KOP | REFERENCE |
| SUS-402 | Roll Center (cross-check) | hardpoints + KOP | MODEL *(flag: cross-check, nunca substitui SUS-401)* |
| SUS-403 | Instant Center | hardpoints + KOP | REFERENCE |
| SUS-404 | Camber Gain | hardpoints + KOP | REFERENCE |
| SUS-405 | Toe Curve | hardpoints + KOP | REFERENCE |
| SUS-501 | Fy(Fz, α, γ) | SUS-104 (Fz), tire coefficients | REFERENCE |
| SUS-502 | Fx(Fz, slip) | SUS-104 (Fz), tire coefficients | REFERENCE |
| SUS-503 | μ efetivo | SUS-501, SUS-502, SUS-104 | CALCULATED |
| SUS-601 | Steering Ratio | geometria de steering | INPUT/MODEL |
| SUS-701 | Downforce | setup/aero input | INPUT |
| SUS-702 | Aero Balance | setup/aero input | INPUT |
| SUS-801 | Setup Definition | vehicle + parâmetros escolhidos | INPUT |
| SUS-802 | Setup Comparison | saídas de SUS-801 | CALCULATED |
| `REQ-XXX` | Requirement (namespace próprio, fora de SUS) | decisão de engenharia | REQUIREMENT |
| `TARGET-XXX` | Target (namespace próprio, fora de SUS) | REQ-XXX + decisão de projeto | TARGET |
| `VAL-XXX` | Validation (namespace próprio) | SUS-XXX validado | — |

**Adendo V1.0 — IDs criados no Engineering Standard depois desta matriz** (dependências conforme as fichas do Standard):

| ID | Parâmetro | Depende de | Data Type |
|---|---|---|---|
| SUS-000 | Ground Plane Reference | — | INPUT/REFERENCE |
| SUS-006 | CG Longitudinal Position (a, b) | SUS-003, pesagem | INPUT/MODEL |
| SUS-007 | Front Unsprung Mass | — | INPUT |
| SUS-008 | Rear Unsprung Mass | — | INPUT |
| SUS-009 | Sprung Mass per Corner | SUS-001, 003, 006, 007, 008 | CALCULATED |
| SUS-010 | Front Unsprung CG Height | SUS-000 | INPUT |
| SUS-011 | Rear Unsprung CG Height | SUS-000 | INPUT |
| SUS-012 | Sprung Mass CG Height | SUS-001, 002, 007, 008, 010, 011, SUS-009 (massa suspensa total) | CALCULATED |
| SUS-013 | Front Brake Force Fraction | — | INPUT (por Setup) |
| SUS-014 | Rear Traction Force Fraction | — | INPUT (=1 para RWD) |
| SUS-206 | Front Roll Stiffness | SUS-202 (F), SUS-004, K_ARB,F | MODEL + INPUT |
| SUS-207 | Rear Roll Stiffness | SUS-202 (R), SUS-005, K_ARB,R | MODEL + INPUT |
| SUS-208 | Roll Stiffness Distribution | SUS-206, SUS-207 (Design Mode: λ_f alvo) | CALCULATED |
| SUS-406 | Instant Center (vista lateral) | hardpoints (buchas e outer dos braços) + KOP | MODEL *(cross-check)* |

`SUS-204 = SUS-206 + SUS-207` (nota do Standard). `SUS-203` e `SUS-204` continuam sem ficha própria.

**Adendo V2.0 — Kinematics Model (PROPOSTA de IDs; aguardam aprovação):**

| ID | Parâmetro | Depende de | Data Type |
|---|---|---|---|
| SUS-407 | Camber Gain (Model/Check) — cross-check de SUS-404 | hardpoints.csv (schema V2.0) | MODEL *(cross-check)* |
| SUS-408 | Toe Curve / Bump Steer (Model/Check) — cross-check de SUS-405 | hardpoints.csv | MODEL *(cross-check)* |
| SUS-409 | Motion Ratio MR(z) (Model/Check) — cross-check de SUS-201 | hardpoints.csv (grupo pushrod/rocker) | MODEL *(cross-check)* |
| SUS-410 | Kingpin Geometry (caster, KPI, scrub, trail) | hardpoints.csv | MODEL |
| SUS-411 | Contact Patch Travel (track/wheelbase change) | hardpoints.csv | MODEL |
| SUS-412 | Instant Centers e Roll Center cinemáticos (3D) — estende SUS-402/403/406 | hardpoints.csv | MODEL *(cross-check)* |
| SUS-413 | Steering Kinematics — cross-check de SUS-601 | hardpoints.csv, curso de cremalheira por volta (INPUT) | MODEL *(cross-check)* |
| SUS-414 | Ackermann (geometria e % Ackermann) — V3.0, EDR-052 | δo, δi; SUS-003, SUS-004; hardpoints.csv | INPUT/MODEL |
| SUS-415 | Roll steer e contribuição ao gradiente de subesterço — V3.0, EDR-052 | hardpoints.csv; φ e a_y (SUS-103) | MODEL |
| SUS-416 | Efeitos do esterço pelo pino mestre (camber, elevação) — V3.0, EDR-052 | hardpoints.csv | MODEL |

`hardpoints.csv` + `hardpoints.meta.json` (schema V2.0, ver `hardpoint-schema-V2.0.md`) é o Geometry Contract da seção 8, com unidade no nome do campo (seção 10).

Cadeia de rastreabilidade final: `REQ-XXX → TARGET-XXX → SUS-XXX (Engineering Standard) → VAL-XXX`, ou `REQ-XXX → SUS-XXX → VAL-XXX` quando não há Target intermediário — três a quatro namespaces independentes, nunca IDs reciclados entre eles.

### 17.6 Ordem de escrita do Engineering Standard

**Bloco A** — Reference frame (sistema de coordenadas, convenções de sinal, dimensões, massas) → **Bloco B** — Static (carga estática por eixo/canto) → **Bloco C** — Longitudinal dynamics (transferência longitudinal, Fz de canto) → **Bloco D** — Suspension stiffness (MR, wheel rate, spring rate, roll stiffness, frequência natural) → **Bloco E** — Kinematics Reference (KOP, RC, IC, camber, toe) → **Bloco F** — Lateral dynamics (roll axis no CG, momento de rolagem suspenso, Milliken LLT, distribuição por eixo, Fz de canto) → **Bloco G** — Combined (Fz combinado longitudinal+lateral) → **Bloco H** — Anti-geometry (anti-dive, anti-squat) → **Bloco I** — Tire (Fy, Fx, μ) → **Bloco J** — Design Mode (frequência-alvo → wheel rate → spring rate; rigidez de rolagem alvo → distribuição por eixo).

### 17.7 Test Cases obrigatórios

`TC-001` a_y=0 → ΔFz lateral=0 em ambos os eixos, F_zL=F_zR · `TC-002` a_x=0 → ΔFz longitudinal=0 · `TC-003` veículo simétrico + frenagem pura → F_zFL=F_zFR, F_zRL=F_zRR · `TC-004` conservação: ΣFz = W (+ F_z,aero se houver) · `TC-005` conservação de momento lateral: `t_F·ΔF_zF + t_R·ΔF_zR = m·a_y·h_CG` (detecta erro de implementação do Milliken — **já verificado algebricamente nesta seção**) · `TC-006` alterar distribuição de roll stiffness mantendo o total constante → transferência dianteira sobe, traseira desce · `TC-007` z_F=z_R=0 → parcela geométrica desaparece · `TC-008` m_uF=m_uR=0 → parcela de massa não-suspensa desaparece · `TC-009` MR=1 → K_w=K_s · `TC-010` cálculo inverso de frequência retorna exatamente o f_n de entrada · `TC-011` comparação direta com OptimumKinematics (MR, RC, IC, camber, toe, mesmo hardpoint/KOP) · `TC-012` comparação com Lotus após transformação de coordenadas — mesma física dentro da tolerância, não igualdade bit-a-bit.

**Nota V2.0:** os testes de kinematics e de hardpoints usam os namespaces `TC-KIN-xxx` (001..006 herdados; 101..117 novos) e `TC-HP-xxx`; os testes novos da suspensão, `TC-SUS-V2-xxx`. Nenhum desses reutiliza ids de `TC-001`..`TC-012`.

**Nota V1.0 (decisão do usuário, 2026-10-09):** esta é a numeração canônica de Test Cases do projeto (concorda com o Engineering Standard e com o Python). Os testes de kinematics usam o namespace `TC-KIN-xxx` (`TC-KIN-001` a `TC-KIN-006`). A numeração do Guide (Apêndice D) diverge e deve ser alinhada a esta.

### 17.8 Piloto end-to-end — cálculo de referência verificado

Caminho: `MR_RH → Wheel Rate → Natural Frequency`, via Python → JSON → Excel → comparação manual. Caso de teste (`MR=0.8`, `K_s=100 N/mm`, `m_s=50 kg`): `K_w = 100/0.8² = 156.25 N/mm = 156250 N/m` → `f_n = (1/2π)√(156250/50) ≈ 8.90 Hz` — **recalculado e confirmado correto**. Três setups no piloto: baseline (`K_s0`), mola mais rígida (`1.2·K_s0`), e Design Mode com frequência-alvo (`K_w=(2πf)²m` → `K_s=K_w·MR²`), testando Analysis Mode e Design Mode sem Goal Seek/solver.

---

## 18. Correções aplicadas nesta rodada (carta branca) — o que mudou e por quê

1. **Namespace de ID unificado.** O esquema alternativo `VEH-XXX/KIN-XXX/DYN-XXX/TIR-XXX/FREQ-XXX` foi descartado; só existe o namespace único `SUS-XXX` por faixa (seção 2) mais `REQ-XXX`/`TARGET-XXX`/`VAL-XXX`. Motivo: as duas últimas mensagens propuseram esquemas incompatíveis; manter os dois em paralelo geraria colisão de referência no Standard.
2. **`SUS-9XX` (Requirement/Target) aposentado.** Requirement e Target passam a ter namespaces próprios (`REQ-XXX`, `TARGET-XXX`), fora do bloco SUS. Motivo: a própria especificação se contradisse (Target ora como `SUS-902`, ora como `TARGET-XXX` separado); e conceitualmente Requirement/Target são objetos de governança, não parâmetros físicos do modelo — mesmo argumento já usado para tirar AUTHORITY da lista de Data Type.
3. **"MODEL/CHECK" não é um Data Type novo.** RC e MR de cross-check continuam `Data Type = MODEL`, com uma flag de metadado ("propósito: cross-check, nunca substitui REFERENCE"), em vez de uma sétima categoria informal. Motivo: manter a taxonomia de 6 Data Types fechada na seção 3, sem inflar por conveniência de rotulagem.
4. **Dependências de Design Mode explicitadas.** `SUS-202`, `SUS-203` e `SUS-205` agora registram a dependência reversa do Design Mode ao lado da dependência normal de Analysis Mode. Motivo: a Dependency Matrix, como estava, só mostrava um sentido e daria a entender que Spring Rate é sempre uma variável livre — o que contradiz o próprio Design Mode que já tínhamos congelado.

Nenhuma decisão física (Milliken, convenções de sinal, RC/IC, unidades) foi alterada — só nomenclatura e estrutura de rastreamento, exatamente os pontos "baratos agora, caros depois" que este documento existe para pegar antes do Standard.
