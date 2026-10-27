# TARGET-007: Comportamento no limite: push/loose e C_N

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 11. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-007, comportamento no limite (push, loose ou neutro, e C_N residual), calculado pelo SUS-1004. ID autorizado em 2026-10-23. |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | distribuição de rolagem λ_f (barras); entrada `ent_06_k_arb_dianteiro`. Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | Análise de par, Milliken §7.1 (p. 283-286, conferida na imagem do PDF em 2026-10-23): transferência lateral de carga FLT, diagrama de potencial e curva de coeficiente de curva, que mostra o efeito da transferência de carga na capacidade lateral de cada eixo. Regras do veredito no EDR-056 (entrada do pneu limitada à faixa, neutro pelo momento desbalanceado, eixo que satura primeiro). Regime limite × regime linear: Milliken p. 313-315. |
| Modelo | `equilibrio.analise_par` e `equilibrio.texto_veredito`; planilha: `res_16_veredito_no_limite_push_loose_neutro_ou` (16_EQUILIBRIO). |
| Compromisso | Push por preferência de piloto ou segurança é troca de valor: nunca conflito automático, mas exige justificativa com EDR (COMPROMISSO DECLARADO, spec §5, item 1c). A nota 35 do Milliken (p. 313) trata de curva limitada por potência e não justifica push no skidpad. Custo: tabela de troca da 20_EQ_TROCA; limiar não definido. Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura (nenhuma página conferida para esta grandeza). O veredito depende do pneu: o `.tir` do TTC é provisório (EDR-038) e a robustez à varredura do pneu fica no relatório `docs/v4-1/inc4-equilibrio-na-planilha.md` (EDR-055), não na planilha. |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_007`, que usa `res_14_equilibrio_no_limite_push_loose_e42` (14_DASHBOARD E42)). |
| Verificação no carro | ensaio de raio constante (Gillespie p. 227-228, como lista a spec §4.3); procedimento e responsável a confirmar. |
| Estados | Ciclo de vida: TBD. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- Com o veredito mostrado como `? NÃO CONCLUSIVO: <motivo>` quando a varredura do pneu inverte o sinal ou tem N/A em parte dela (EDR-060 item 8, x).
- Nomes na planilha: entradas `ent_03_target_007_*` (H, J, M, N, Q, mais C:G) e resultados `res_03_alavanca_target_007`,
  `res_03_valor_atual_do_modelo_target_007`, `res_03_pior_origem_da_grandeza_target_007` e `res_03_coerencia_target_007`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
