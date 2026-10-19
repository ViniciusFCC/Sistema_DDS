# Registro de versões — Sistema_DDS — V2.3 (verificação das equações do pneu)

Data: 2026-10-13. Sem alteração de fórmulas em relação à V2.2.

| Anterior | V2.3 | Mudança |
|---|---|---|
| `FSAE_EV_Suspension_Fase1_V2_2.xlsx` | `FSAE_EV_Suspension_Fase1_V2_3.xlsx` | Novo metadado em `10_TIRE` (verificação das equações), texto de DR-013, `13_VALIDATION` l.44, README e changelog (linha 14; linha 13 corrigida de "31/31" para "34/34, mutação 17/17"). 339 fórmulas, as mesmas da V2.2. |
| — | `test_tire_oracles_V2_2.py` | Compara o módulo com duas implementações de terceiros: `CalcMF52()` do Racer v0.8.9 e ramo MF 5.2 do MFeval (port Julia). |
| — | `tire_comparison_grid_V2_3.csv` | 75 pontos (Fz, α, γ, κ → Fx, Fy no referencial do arquivo) para comparar com OptimumTire 2/Adams. |
| `Engineering_Decision_Register.md` V2.2 | V2.3-PARCIAL | EDR-042; H1 do EDR-037 atualizada. |
| `build_workbook_V2_2.py` | `build_workbook_V2_3.py` | Gera a V2.3 (`layout_V2_3.json`). |

`tire_model_V2_2.py`, `test_tire_model_V2_2.py` e `test_workbook_V2_2.py` permanecem inalterados.

## Resultados (resultado de código, 2026-10-13)
- Oráculos: 5/5. Dif máx 3,4e-7 N (Racer) e 3,4e-4 N (MFeval; ε=1e-3 no B) em 3000 pontos; os dois oráculos concordam entre si.
- Pneu 34/34; planilha V2.3 15/15.

## O que ficou provado e o que não
- **Provado:** o módulo (e, por herança, a planilha, já igual ao Python a ~4e-15) coincide com duas implementações publicadas de terceiros para o dataset atual.
- **Não provado:** concordância com o livro (Pacejka, 2ª/3ª ed.; fonte primária, paga) ou com a documentação TNO/Adams PAC2002; concordância com medição ou com o OptimumTire 2. Viés de transcrição meu nos oráculos não é excluível.
- **Divergências entre as fontes de terceiros** (irrelevantes com L*=1, relevantes se o dataset real trouxer L*≠1): fator LFZO extra em Ky (Racer sim, MFeval não) e uso de LGAX/LGAY (Racer sim, MFeval não). O módulo segue o Racer.
- Não implementados: condições Bxα>0 e Gxα>0 que o livro registra.

## Próximos passos para chegar à validação
1. Conferir no livro (Apêndice de MF 5.2, ou 3ª ed., cap. 4) as equações de Fx0, Fy0 e combinação, incluindo LFZO, LGAX e LGAY (biblioteca da EESC).
2. Rodar `tire_comparison_grid_V2_3.csv` no OptimumTire 2 (ou Adams) com o mesmo `.tir` e devolver Fx e Fy: esse é o teste capaz de detectar erro de equação e de convenção de sinal.
3. Quando houver dataset real, repetir com ele (nova Tire REV).
