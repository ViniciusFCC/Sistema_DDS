# TARGET-003: Distribuição de rigidez de rolagem λ_f

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 7. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-003, distribuição de rigidez de rolagem λ_f, calculada pelo SUS-208 (adimensional). |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | distribuição de rolagem λ_f (barras); entrada `ent_06_k_arb_dianteiro`. Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | λ_f = K_φF/(K_φF + K_φR), λ_r = 1 − λ_f. Modo reverso (Design Mode): K_φF,necessária = λ_f/(1 − λ_f)·K_φR, com a rigidez traseira fixa, e a barra dianteira necessária como a diferença para a rigidez de rolagem sem barra. Equação da ficha SUS-208 do Engineering Standard (EDR-045); sem página de livro conferida. |
| Modelo | `suspension_model.roll_stiffness_distribution` (e `arb_required` no reverso); planilha: `res_06_distribuicao_de_rigidez_dianteira_lambda`. |
| Compromisso | O λ_f é a alavanca comum de TARGET-003, 006 e 007. Com meta de K ou de limite, o λ_f passa a CONSEQUÊNCIA (spec §5, item 2); duas METAs nessa alavanca dão CONFLITO de sobredeterminação. A tabela de troca da barra dianteira (20_EQ_TROCA) mostra o que muda no K e no limite quando o λ_f varia; é grade de exibição, não meta. Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura (nenhuma página conferida para esta grandeza). Para o efeito do λ_f no subesterço, ver TARGET-006 (Gillespie p. 214). |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_003`, que usa `res_14_distribuicao_de_rigidez_dianteira_e17` (14_DASHBOARD E17)). |
| Verificação no carro | a definir pela equipe (a confirmar); nenhum teste está registrado. |
| Estados | Ciclo de vida: OPEN. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- Alavanca compartilhada com TARGET-006 e 007.
- Nomes na planilha: entradas `ent_03_target_003_*` (H, J, M, N, Q) e resultados `res_03_alavanca_target_003`,
  `res_03_valor_atual_do_modelo_target_003`, `res_03_pior_origem_da_grandeza_target_003` e `res_03_coerencia_target_003`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
