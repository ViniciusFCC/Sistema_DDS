# TARGET-004: Anti-dive

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 8. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-004, anti-dive, calculado pelo SUS-301 (unidade: %). |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | geometria dianteira (anti-dive); entrada `ent_07_altura_do_ic_lateral_dianteiro_z_icf` (07_KINEMATICS B10). Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | AD_f[%] = FB_f·(−s_f)·(L/h_CG)·100, com s_f = dz/dx da linha contact patch dianteiro até o IC lateral (freio dentro da roda, em volta do cubo; EDR-048). Positivo é anti, negativo é pro-dive (EDR-026). Anti-dive nunca reduz a transferência de carga longitudinal (EDR-010). O Standard cita Milliken p. 618, Fig. 17.12; a página vem do Standard e **não foi reconferida na imagem do PDF** nesta versão (relação só com fonte M). |
| Modelo | `kinematics_model.anti_dive_percent_signed`; planilha: `res_06_anti_dive_fb_f_dz_dx_l_h100_anti_pro_div`. |
| Compromisso | sem tabela de troca para esta meta ainda; o custo (o que piora quando ela melhora) é a confirmar. Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura (nenhuma página conferida para esta grandeza). |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_004`, que usa fórmula de pior origem do grafo em 03_TARGETS L8 (o 14_DASHBOARD não tem linha do SUS-301)). |
| Verificação no carro | a definir pela equipe (a confirmar); nenhum teste está registrado. |
| Estados | Ciclo de vida: OPEN. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- A linha geométrica (contact patch ou centro da roda) depende da configuração real de freio e trem de força; freio dentro da roda e motor no chassi, atrás, vêm do usuário (2026-10-19), a confirmar para o T11 (EDR-048).
- Nomes na planilha: entradas `ent_03_target_004_*` (H, J, M, N, Q) e resultados `res_03_alavanca_target_004`,
  `res_03_valor_atual_do_modelo_target_004`, `res_03_pior_origem_da_grandeza_target_004` e `res_03_coerencia_target_004`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
