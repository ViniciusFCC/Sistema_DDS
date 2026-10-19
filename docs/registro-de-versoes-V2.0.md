# Registro de versões — Sistema_DDS — V2.0

Data: 2026-10-09. Regra (usuário): V1.0 → V1.1 a cada pequena implementação; esta rodada é a V2.0 por trazer a implementação completa de Kinematics. Arquivos `.py` usam `_V2_0` (ponto no nome impede `import`). Os arquivos `*_V1_0*` e `registro-de-versoes-V1.0.md` ficam na pasta como histórico.

## Mapa V1.0 → V2.0
| V1.0 | V2.0 | Mudança |
|---|---|---|
| `engineering-standard-V1.0-...md` | `engineering-standard-V2.0-...md` | Bloco E.2 (SUS-407..413); notas de achados em SUS-406/301/302; log V2.0 |
| `arquitetura-consolidada-V1.0-...md` | `arquitetura-consolidada-V2.0-...md` | IDs 407..413 no adendo; namespaces de TC; nota de sinal do anti-dive |
| `data-contract-V1.0-...md` | `data-contract-V2.0-...md` | Seção 5 atualizada; seção 6 (hardpoints e resultados de kinematics) |
| `suspension_model_V1_0.py` | `suspension_model_V2_0.py` | Bloqueios de entrada (Guide D.2); `FzLiftoffWarning`; `SmallMotionRatioWarning` |
| `test_suspension_model_V1_0.py` | `test_suspension_model_V2_0.py` | 16 herdados + 17 novos |
| `kinematics_model_V1_0.py` | `kinematics_model_V2_0.py` | Funções 2D inalteradas + solver 3D, IC/RC cinemáticos, MR, esterçamento, CSV |
| `test_kinematics_model_V1_0.py` | `test_kinematics_model_V2_0.py` | 11 herdados + 36 novos |
| `FSAE_EV_Suspension_Fase1_V1.0.xlsx` | `FSAE_EV_Suspension_Fase1_V2.0.xlsx` | `07_KINEMATICS` (blocos N/A + schema), DR-012, README, changelog; **0 fórmulas alteradas** |
| — | `hardpoints_V2_0.py`, `test_hardpoints_V2_0.py` | Novo: schema, loader e validações (21 testes) |
| — | `hardpoint-schema-V2.0.md` | Novo: especificação do schema (proposta) |
| — | `hardpoints_synthetic_V2.0.csv/.meta.json`, `kinematics_sweep_synthetic_V2.0.csv` | Novo: geometria e saída **sintéticas** (não representam o carro) |

## Resultados de código (2026-10-09)
- Kinematics: **47/47** · Hardpoints: **21/21** · Suspensão: **33/33** (regressão idêntica à V1.0).
- Teste de mutação: 14 bugs distintos no kinematics e 6 nas validações; todos detectados (3 passavam, o que levou ao `TC-KIN-117`).
- Planilha recalculada em cópia: 84 fórmulas, 0 erros. O entregável **não** passa pelo recálculo do LibreOffice (ele remove aspas de abas que começam com dígito).

## Achados que mudam decisões (nada foi aplicado às fórmulas; todos aguardam aprovação)
1. IC lateral da V1 (outer → ponto médio das buchas) é mal condicionado: %AD de −680,7 contra 36,3 (cinemático) e 38,0 (eixos de pivô) na geometria sintética.
2. `tan φ` com `|d|` ignora o sinal: IC à frente e acima na frente é pro-dive, mas a forma V1 dá positivo.
3. Camber estático por `SPINDLE_PT − WHEEL_CENTER` com base de 0,08 m tem σ ≈ 0,5° para σ = 0,5 mm nos hardpoints.
4. RC cinemático tem σ ≈ 1,9 mm (13%) para σ = 0,5 mm nos hardpoints, e migra de +59 a −29 mm em ±30 mm de curso (sintético).

## Pendências abertas
- Aprovar: IDs SUS-407..413, schema de hardpoints, IC lateral cinemático, %AD/%AS com sinal.
- Dados da equipe: hardpoints reais (sem eles TC-011/TC-012 seguem NOT_VALIDATED), configuração real de freio/trem de força (`reaction_point`), definição de curso do OptimumKinematics, curso de cremalheira por volta.
- Placeholders de `07_KINEMATICS` (alimentam SUS-301/302 na planilha): manter ou migrar para N/A/TBD? Sem resposta ainda; mantidos.
- `SUS-203`/`SUS-204` sem ficha; TC de sinal para SUS-404/405; limite de MR (0,2) é hipótese.
- Guide: numeração de TC e DR diverge; a cópia do Guide no projeto está em branco (304 bytes).
