# Hardpoint Schema V2.0 — hardpoints.csv + hardpoints.meta.json

**Status: PROPOSTA (hipótese de projeto), aguardando aprovação.** Origem do que **não** é proposta nova: colunas `Point_ID | X | Y | Z | Component | Status` (arquitetura, seção 8), unidade no nome do campo (seção 10), eixos ISO 8855 e adapter Lotus (seção 17.1), `SUS-000` (plano do solo), categorias Design Intent / As-Built (seção 8). **Proposta desta versão:** convenção de `Point_ID`, vocabulário de `Component` e `Status`, e todos os critérios de validação. Implementação: `hardpoints_V2_0.py` (21 testes, `test_hardpoints_V2_0.py`).

## 1. Arquivos
| Arquivo | Conteúdo |
|---|---|
| `hardpoints.csv` | Uma linha por ponto. Colunas exatas: `Point_ID,X_m,Y_m,Z_m,Component,Status` |
| `hardpoints.meta.json` | Metadados obrigatórios (seção 4) |

Exemplos **sintéticos** (não representam o carro): `hardpoints_synthetic_V2.0.csv` e `.meta.json`.

## 2. Convenções
- **Eixos:** X frente, Y esquerda, Z cima (ISO 8855). Cantos esquerdos têm `Y > 0`; direitos, `Y < 0`. Lotus (X trás, Y direita) exige `lotus_to_iso8855` antes (`X=-X, Y=-Y, Z=Z`); o loader rejeita dado em convenção Lotus.
- **Unidade:** metros, sempre. Coordenada com módulo > 5 m é bloqueada (provável mm lido como m).
- **Solo:** `ground_plane_z_m` (SUS-000) está no meta. `CONTACT_PATCH.Z` deve coincidir com ele (tolerância 1 mm).
- **Curso:** `z` = deslocamento vertical do centro da roda, bump positivo, no referencial do chassi (hipótese de convenção; confirmar com o OptimumKinematics).
- **Camber/toe:** camber + = topo para fora; toe + = toe-out (arquitetura 17.2). `SPINDLE_PT` fica para fora do centro da roda; o eixo da roda é `SPINDLE_PT − WHEEL_CENTER`.

## 3. Pontos por canto
`Point_ID = <FL|FR|RL|RR>_<CHAVE>`. `Component` = corpo rígido ao qual o ponto pertence.

| Chave | Component | Significado |
|---|---|---|
| `LCA_IN_F`, `LCA_IN_R` | CHASSIS | Pivôs internos dianteiro e traseiro do braço inferior |
| `LCA_OUT` | UPRIGHT | Ball joint externo inferior |
| `UCA_IN_F`, `UCA_IN_R`, `UCA_OUT` | CHASSIS, CHASSIS, UPRIGHT | Idem, braço superior (`UCA_OUT` acima de `LCA_OUT`) |
| `TIE_IN` | RACK | Ponta interna da barra de direção (posição com cremalheira centrada) |
| `TIE_OUT` | UPRIGHT | Ponta externa da barra de direção |
| `WHEEL_CENTER`, `SPINDLE_PT`, `CONTACT_PATCH` | WHEEL | Centro da roda; ponto externo no eixo da roda; contact patch estático |
| `PUSH_OUT` *(grupo opcional)* | LCA, UCA ou UPRIGHT | Ponta externa do pushrod/pullrod (o Component diz onde ela se fixa) |
| `PUSH_IN` | ROCKER | Ponta interna do pushrod no rocker |
| `ROCKER_AXIS_A`, `ROCKER_AXIS_B` | CHASSIS | Dois pontos do eixo do rocker |
| `ROCKER_SPRING` | ROCKER | Fixação da mola/amortecedor no rocker |
| `SPRING_CHASSIS` | CHASSIS | Fixação da mola/amortecedor no chassi |

O grupo pushrod/rocker/mola é **tudo ou nada** (sem ele, sem MR). Sem barra de direção compatível o solver não fecha: a barra é obrigatória.

## 4. Metadados obrigatórios (`.meta.json`)
`schema_version` (`V2.x`), `geometry_rev` (`G-REV-X`, arquitetura seção 8), `coordinate_system` (`ISO8855_X_FORWARD_Y_LEFT_Z_UP`), `units` (`m`), `ground_plane_z_m`, `kop` (ponto de operação cinemático, ex.: ride height), `source`, `freeze_level` (F0..F4), `timestamp`.

## 5. Status por ponto
`SYNTHETIC` (teste; **não representa o carro**), `PROVISIONAL`, `DESIGN_INTENT` (CAD), `AS_BUILT` (medido). Um conjunto com qualquer `SYNTHETIC` não pode alimentar resultado do carro nem preencher campos REFERENCE.

## 6. Validações (todas com teste)
Cabeçalho exato; 6 campos por linha; chave e Component compatíveis; Status no vocabulário; sem `Point_ID` duplicado; coordenadas finitas e < 5 m; lado × sinal de Y; `SPINDLE_PT` outboard; contact patch no solo; `UCA_OUT` acima de `LCA_OUT`; sem elos de comprimento nulo; pontos obrigatórios completos; grupo pushrod tudo-ou-nada; eixo dianteiro com X maior que o traseiro; meta completo e coerente.

## 7. Limites e incertezas conhecidos
- **Orientação da roda por dois pontos amplifica erro de coordenada** (σ_ângulo ≈ σ_coord·√2 / distância). Com base de 0,08 m e σ = 0,5 mm, o camber estático tem σ ≈ 0,5° (Monte Carlo, N=300). Use `SPINDLE_PT` ≥ 0,15 m do centro da roda ou informe camber/toe estáticos como dado separado.
- O CSV grava 9 casas decimais (nm). Com 6 casas (µm) o camber estático da geometria sintética saía com erro de ≈ 1e-4°.
- `CONTACT_PATCH` é tratado como ponto solidário à roda (SUS-411).
- Sem hardpoints reais do carro, nenhuma comparação com o OptimumKinematics foi feita.
