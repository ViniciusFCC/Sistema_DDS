# TARGET-002: Frequência natural traseira

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 6. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-002, frequência natural traseira, calculada pelo SUS-205 (unidade: Hz). |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | mola traseira (entrada `ent_06_spring_rate_traseiro`). Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | Mesma equação do TARGET-001, com a massa suspensa e a ride rate do eixo traseiro: f_n = (1/2π)·√(K_R / m_sprung,corner). Fonte citada na ficha SUS-205 do Engineering Standard: Gillespie eq. 5-8/5-9 (p. 148), Seward (p. 95-97), Milliken p. 588, 591 e 601, **não reconferidas na imagem do PDF** nesta versão (relação só com fonte M). |
| Modelo | `suspension_model.natural_frequency`; planilha: `res_06_frequencia_natural_traseira` (06_SUSPENSION B33, mostrada no 14_DASHBOARD B16). |
| Compromisso | sem tabela de troca para esta meta ainda; o custo (o que piora quando ela melhora) é a confirmar. Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura (nenhuma página conferida para esta grandeza). |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_002`, que usa `res_14_frequencia_natural_traseira_e16` (14_DASHBOARD E16)). |
| Verificação no carro | a definir pela equipe (a confirmar); nenhum teste está registrado. |
| Estados | Ciclo de vida: OPEN. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- Mesma regra do TARGET-001: a mola é consequência do Design Mode, não alvo digitado.
- Nomes na planilha: entradas `ent_03_target_002_*` (H, J, M, N, Q) e resultados `res_03_alavanca_target_002`,
  `res_03_valor_atual_do_modelo_target_002`, `res_03_pior_origem_da_grandeza_target_002` e `res_03_coerencia_target_002`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
