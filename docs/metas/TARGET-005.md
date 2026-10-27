# TARGET-005: Anti-squat

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 9. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-005, anti-squat, calculado pelo SUS-302 (unidade: %). |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | geometria traseira (anti-squat); entrada `ent_07_altura_do_ic_lateral_traseiro_z_icr` (07_KINEMATICS B12). Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | AS_r[%] = TF_r·s_r·(L/h_CG)·100, com s_r = dz/dx da linha centro da roda traseiro até o IC lateral (motor no chassi, com semieixos; EDR-048). Positivo é anti, negativo é pro-squat. Anti-squat nunca reduz a transferência de carga longitudinal (EDR-010). O Standard cita Milliken Fig. 17.15b e Gillespie eq. 7-19, **não reconferidas na imagem do PDF** nesta versão (relação só com fonte M). |
| Modelo | `kinematics_model.anti_squat_percent_signed`; planilha: `res_06_anti_squat_tf_r_dz_dx_l_h100_anti_pro_sq`. |
| Compromisso | sem tabela de troca para esta meta ainda; o custo (o que piora quando ela melhora) é a confirmar. Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura (nenhuma página conferida para esta grandeza). |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_005`, que usa fórmula de pior origem do grafo em 03_TARGETS L9 (o 14_DASHBOARD não tem linha do SUS-302)). |
| Verificação no carro | a definir pela equipe (a confirmar); nenhum teste está registrado. |
| Estados | Ciclo de vida: OPEN. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- Mesma ressalva do TARGET-004 sobre a linha geométrica.
- Nomes na planilha: entradas `ent_03_target_005_*` (H, J, M, N, Q) e resultados `res_03_alavanca_target_005`,
  `res_03_valor_atual_do_modelo_target_005`, `res_03_pior_origem_da_grandeza_target_005` e `res_03_coerencia_target_005`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
