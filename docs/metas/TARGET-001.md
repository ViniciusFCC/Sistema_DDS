# TARGET-001: Frequência natural dianteira

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 5. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-001, frequência natural dianteira, calculada pelo SUS-205 (unidade: Hz). |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | mola dianteira (entrada `ent_06_spring_rate_dianteiro`). Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | f_n = (1/2π)·√(K_R / m_sprung,corner), com a ride rate K_R (SUS-212, mola na roda em série com o pneu). Modo reverso (Design Mode): K_R = (2π·f_alvo)²·m_sprung,corner. Fonte citada na ficha SUS-205 do Engineering Standard: Gillespie eq. 5-8/5-9 (p. 148), Seward eq. 4.1, 4.2 e 4.4 (p. 95-97), Milliken p. 588, 591 e 601. Essas páginas vêm do Standard e **não foram reconferidas na imagem do PDF** nesta versão; por isso a relação da 23_LISTAS tem só a fonte M. |
| Modelo | `suspension_model.natural_frequency` (e `wheel_rate_from_target_frequency` no sentido reverso); planilha: `res_06_frequencia_natural_dianteira` (06_SUSPENSION B32, mostrada no 14_DASHBOARD B15). |
| Compromisso | sem tabela de troca para esta meta ainda; o custo (o que piora quando ela melhora) é a confirmar. Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura (nenhuma página conferida para esta grandeza). |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_001`, que usa `res_14_frequencia_natural_dianteira_e15` (14_DASHBOARD E15)). |
| Verificação no carro | a definir pela equipe (a confirmar); nenhum teste está registrado. |
| Estados | Ciclo de vida: OPEN. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- A mola é alavanca de TARGET-001 apenas. Mola, MR e rigidez na roda não viram Target (nota A15 da 03_TARGETS): saem do Design Mode a partir da frequência.
- Nomes na planilha: entradas `ent_03_target_001_*` (H, J, M, N, Q) e resultados `res_03_alavanca_target_001`,
  `res_03_valor_atual_do_modelo_target_001`, `res_03_pior_origem_da_grandeza_target_001` e `res_03_coerencia_target_001`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
