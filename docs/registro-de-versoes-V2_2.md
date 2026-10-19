# Registro de versões — Sistema_DDS — V2.2 (pneu)

Data: 2026-10-12. Regra de versionamento (EDR-017): decimal sobe a cada implementação. Arquivos `.py` usam `_V2_2`. Arquivos anteriores (V2.0, V2.1) permanecem como histórico, sem alteração.

## Mapa V2.1 → V2.2
| Anterior | V2.2 | Mudança |
|---|---|---|
| `FSAE_EV_Suspension_Fase1_V2_1.xlsx` | `FSAE_EV_Suspension_Fase1_V2_2.xlsx` | `10_TIRE` implementada; `13_VALIDATION` l.35–44; `14_DASHBOARD` l.32–38; `04_DECISION_REGISTER` DR-013 (+ texto de DR-011 E15); `01_SETUP` B11 (Tire REV); `00_README`; `15_CHANGELOG`. **As 88 fórmulas da V2.1 não foram alteradas** (TC-WB22-001). Total V2.2: 339 fórmulas. |
| — | `tire_model_V2_2.py`, `test_tire_model_V2_2.py`, `test_workbook_V2_2.py`, `build_workbook_V2_2.py`, `mutation_tire.py` | Novos |
| — | `Hoosier_R25B_13x7_TTC_provisional.tir` + `.meta.json` | Dataset **provisório** (arquivo limpo; hash do arquivo limpo, não do original colado) |
| `data-contract-V2_0` | `data-contract-V2_2` | Só a seção 7 (pneu) foi acrescentada; proposta |
| `Engineering_Decision_Register.md` (V2.1-PARCIAL) | V2.2-PARCIAL | EDR-037..041; índice, rastreabilidade e mapa atualizados; texto desatualizado do EDR-015 corrigido |

## Resultados de código (2026-10-12)
- `test_tire_model_V2_2.py`: **34/34**. Teste de mutação: **17/17** detectados. Na primeira rodada, só 7 de 13 mutantes foram detectados (os testes de limite analítico não enxergavam E, camber, dependência de carga nem fatores L* iguais a 1); isso levou à segunda transcrição independente (TC-TIRE-009) e ao teste de escala.
- `test_workbook_V2_2.py`: **15/15** (recálculo em cópia no LibreOffice): Excel == Python a ~4e-15 relativo em 25 pontos aleatórios (rodas esquerdas e direitas), mais um cenário com todos os coeficientes P*/R* e L* perturbados em ±10%; limites de Fz, α, γ e κ; dataset inválido; entrada ausente e `N/A` de upstream sem `#VALUE!`; preservação das 88 fórmulas da V2.1.
- Regressão dos módulos existentes: suspensão **42/42**, hardpoints **35/35**, kinematics **53/53**.
- O entregável **não** passa pelo recálculo do LibreOffice (mesma decisão da V2.0: ele remove aspas de nomes de aba iniciados por dígito). Foi salvo com `fullCalcOnLoad`; os valores aparecem ao abrir no Excel.

## O que NÃO foi verificado (limites)
1. **Equações da Magic Formula (H1):** reproduzidas de memória do formato publicado (PAC2002/MF 5.2), sem fonte primária consultada. Não achei implementação independente disponível (mfeval e similares não estão no PyPI do ambiente). Excel, Python e a segunda transcrição de teste compartilham a mesma origem das equações: concordância entre eles **não** detecta erro comum de origem.
2. **Convenção de sinais (H3/H4, EDR-039):** inferida por avaliação do modelo; o `.tir` não declara os eixos. Espelhamento das rodas esquerdas é decisão de projeto provisória.
3. **Dataset:** provisório; μ_eff do dashboard é derivado dele, com Fz de `09_LOADS` (placeholder) e α/γ/κ arbitrários. Nada disso é resultado do carro.
4. Mx, My, Mz, pressão, relaxamento e raio carregado não importados. Formatos MF 6.1.2/6.2 não suportados (EDR-040).
5. Guide: lido por OCR em parte (PDF só de imagem, 153 páginas); li só os trechos de pneu, targets e revisões. A conversa "estruturação Planilha DDS" não estava disponível.

## Pendências
- Decidir: EDR-039 (convenção/espelhamento), EDR-040 (formato do dataset), além das já abertas (EDR-018, 023–027, 033–036).
- Atualizar fichas SUS-501..503 no Standard (nível 2, convenção, espelhamento, faixa/N/A); Standard e Arquitetura não foram alterados nesta versão.
- Comparar com OptimumTire 2 (varredura de α, κ, γ: sinais de Fy, Fx e Mz) e trocar o dataset por dado real (nova Tire REV; resultados antigos viram STALE).
