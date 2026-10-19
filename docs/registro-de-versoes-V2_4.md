# Registro de versões — Sistema_DDS — V2.4 (sistema de eixos do arquivo de pneu)

Data: 2026-10-14. Motivo: o usuário informou que o TTC usa a convenção SAE e que os dados foram baixados direto do TTC; autorizou a mudança proposta (EDR-039).

## Mapa V2.3 → V2.4
| Anterior | V2.4 | Mudança |
|---|---|---|
| `FSAE_EV_Suspension_Fase1_V2_3.xlsx` | `FSAE_EV_Suspension_Fase1_V2_4.xlsx` | `10_TIRE`: sistema de eixos declarado (`SAE_CALSPAN`), fatores s_α, s_Fy, s_γ e transformação para ISO; novas linhas de cálculo (α e γ no referencial do arquivo); dataset inválido se o eixo não for reconhecido. Textos de `10_TIRE`, DR-013, dashboard, README e changelog (linha 15) ajustados. 347 fórmulas; as 88 da V2.1 intactas. |
| `tire_model_V2_2.py` | `tire_model_V2_4.py` | `load_dataset` exige `source_axis_system`; `AXIS_TRANSFORMS`; `wheel_forces` espelha e depois transforma; `project_sign_report`. `combined_forces` (referencial do arquivo) inalterada. |
| `test_tire_model_V2_2.py`, `test_tire_oracles_V2_2.py`, `test_workbook_V2_2.py`, `mutation_tire.py` | `..._V2_4` | Adaptados e ampliados (TC-TIRE-010, TC-WB24-004c..f, mutantes da transformação). |
| `data-contract-V2_2` | `data-contract-V2_4` | Seção 7: `source_axis_system` obrigatório e transformação. |
| `Hoosier_..._provisional.meta.json` | mesmo nome, `schema_version V2.4-PROPOSAL` | Eixo SAE_CALSPAN, `USER_ASSERTED`, evidência e transformação; retirada a frase 'compatível com ISO'. |
| `Engineering_Decision_Register.md` | V2.4-PARCIAL | EDR-039 revisto (PENDING_CONFIRMATION → APPROVED_WITH_CONDITIONS). |

## Resultados de código (2026-10-14)
- `test_tire_model_V2_4.py`: **43/43**. `test_tire_oracles_V2_4.py`: **5/5** (a avaliação no referencial do arquivo não mudou). Mutação: **23/23**.
- `test_workbook_V2_4.py`: **19/19** (Excel == Python a ~4e-15 relativo; modos SAE e ISO; eixo desconhecido invalida o dataset).

## Efeito da mudança (564 N, roda direita, resultado de código)
| Caso | V2.2/V2.3 | V2.4 |
|---|---|---|
| Fy, α=4° | −1436 N | −1390 N (−3%) |
| Fy, camber +3° (topo p/ fora), α=0 | −141 N | −183 N (+30%) |
| Fy, α=0, γ=0, κ=0 | +28 N | −28 N (inverte) |
| Fx, α=4°, κ=0 | 49,5 N | 57,4 N |

## Limites
1. A declaração SAE é do usuário. A fonte secundária (tese UNCC 2015) a apoia para o dado bruto, mas o `.tir` tem Fz positivo (dado bruto é negativo), ou seja, foi processado, e não sabemos se α e Fy também foram convertidos.
2. **O sinal de camber é inferência** (empuxo de camber aponta para o lado da inclinação). A definição de IA do TTC não foi verificada. Se ela contradisser a inferência, o efeito do camber inverte de sinal. É o maior risco aberto e afeta qualquer otimização de camber.
3. As equações continuam verificadas só por código de terceiros e limites analíticos; não validadas contra o livro, medição ou OptimumTire.
4. `tire_comparison_grid_V2_3.csv` segue no referencial do arquivo (sem transformação), o que é o adequado para comparar com o OptimumTire/Adams usando o mesmo `.tir`.

## Para fechar
Confirmar IA e SA no documento do TTC (envie a página) e/ou rodar a grade no OptimumTire 2/Adams.
