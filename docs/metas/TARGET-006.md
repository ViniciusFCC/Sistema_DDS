# TARGET-006: Gradiente de subesterço K

Ficha completa da meta (spec §4.3). A ficha curta está na `03_TARGETS`, linha 10. Os dados desta página são os que a
planilha V4.2 mostra (`python/metas.py`, `python/aba_metas.py`); se divergirem, vale a planilha e este arquivo está desatualizado.
Nenhum valor-alvo foi definido pela equipe: a meta é **TBD**.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | TBD: lista de objetivos da equipe a definir em EDR (coluna Q da 03_TARGETS). |
| Grandeza | TARGET-006, gradiente de subesterço K, calculado pelo SUS-1001 (unidade: °/g). ID autorizado em 2026-10-23. |
| Papel | TBD (coluna H). META ou CONSEQUÊNCIA só depois de a equipe decidir. |
| Alavanca | distribuição de rolagem λ_f (barras); entrada `ent_06_k_arb_dianteiro`. Vem da tabela de relações da 23_LISTAS (coluna I). |
| Método | K pelas parcelas (pneus, rolagem, deslocamento com a carga: ply steer, conicidade, toe e camber estático), no regime linear, como no EDR-057 (Gillespie cap. 6). Fontes L da relação: **Gillespie p. 214** (conferida na imagem do PDF em 2026-10-23, itens 2 a 4): projetistas buscam mais rigidez de rolagem na frente para garantir subesterço no limite, e barra só atrás pode induzir sobresterço; é prática de projeto, não uma equação. **Milliken p. 313-315** (§8.5, conferida): o subesterço no regime linear e o push/loose no limite são situações físicas diferentes e não se confundem (relação informativa com o TARGET-007). |
| Modelo | `equilibrio_linear` (`texto_k`, parcelas de K); planilha: `res_16_k_total_em_g` (16_EQUILIBRIO), `res_14_gradiente_de_subesterco_k_linear_e41` no 14_DASHBOARD. |
| Compromisso | K e λ_f estão ligados: com meta de K, o λ_f passa a CONSEQUÊNCIA. O custo de mudar o K está na tabela de troca da barra dianteira (20_EQ_TROCA, EDR-060 item 6; cinco valores de K_ARB dianteiro, grade de exibição). Limiar de custo: não definido (spec §5, item 5; só por EDR da equipe). Coluna M (declarado) e N (EDR): vazias. |
| Faixa da literatura | sem faixa na literatura para o valor de K. O Milliken (p. 313-315) dá só a faixa do regime linear, de 0 a 0,3-0,4 g de aceleração lateral, que não é faixa de K. Faixa de outro tipo de carro não vale (spec §4.3). |
| Valor escolhido | TBD. Valor, justificativa, responsável (Owner: TBD) e EDR: nenhum definido. |
| Sensibilidade | Ainda não calculada na planilha. A coluna L mostra a pior origem das entradas da grandeza (`res_03_pior_origem_da_grandeza_target_006`, que usa `res_14_gradiente_de_subesterco_k_linear_e41` (14_DASHBOARD E41)). |
| Verificação no carro | ensaio de raio constante (Gillespie p. 227-228, como lista a spec §4.3); procedimento e responsável a confirmar. |
| Estados | Ciclo de vida: TBD. Congelamento: F0. Validação: NOT_VALIDATED. Coerência inicial: NÃO AVALIÁVEL (meta sem valor ou papel). |

## Notas

- O K vale no regime linear. Subesterço linear com loose no limite não é erro.
- Nomes na planilha: entradas `ent_03_target_006_*` (H, J, M, N, Q, mais C:G) e resultados `res_03_alavanca_target_006`,
  `res_03_valor_atual_do_modelo_target_006`, `res_03_pior_origem_da_grandeza_target_006` e `res_03_coerencia_target_006`.
- Processo, estados e regra de coerência: `docs/metas/README.md`. Decisões: EDR-061 (processo e coerência) e EDR-034 (congelamento F0-F4).
