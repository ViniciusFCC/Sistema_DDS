# Registro de versões — Sistema_DDS — V4.2 (incremento 5)

Data: 2026-10-26. A V4.2 cobre o incremento 5 da especificação
`docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` (metas e coerência) e ajusta a planilha ao projeto T11.
Decisões: EDR-061 (processo de metas e coerência), EDR-062 (Origens e prefixo D16 para o T11) e EDR-063 (viva no Drive:
conferência, retrato por nome e troca a cada versão), com o EDR-034 decidido (F0 a F4) e o EDR-060 item 8 (x) resolvido e
(xi) acrescentado. Plano: `docs/superpowers/plans/2026-10-23-v4-2-inc5-metas-e-coerencia.md`.

## O que entrou

| Item | Entrou |
|---|---|
| Planilha de referência | `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx`, gerada da tag `v4.1` por `python/gerar_v4_2.py`, com 117627 fórmulas (as 117569 da V4.1 e 58 novas) e 1220 nomes definidos (os 1145 da V4.1 e 75 de `data/nomes_V4_2.csv`). A cópia para `excel/` é um commit próprio (Task 7b); até lá a planilha sai em `build/`. |
| Aba nova | `23_LISTAS`, no fim (depois da `22_CADEIA`): vocabulários de Papel, ciclo de vida da meta, Congelamento (F0 a F4), Coerência e Fonte, e a tabela de relações com a fonte de cada linha (sete M e três L). |
| Fichas de meta | `03_TARGETS` colunas H a Q (Papel, Alavanca, Congelamento, Valor atual do modelo, Pior origem, Compromisso declarado, EDR do compromisso, Coerência, Ficha, Objetivo atendido) e auxiliares ocultas R:U; linhas 10 e 11 para o TARGET-006 e o TARGET-007; fichas completas em `docs/metas/`. |
| Dashboard | `14_DASHBOARD` linhas 49 (título), 50 (pior coerência das fichas) e 51 (compromissos declarados). |
| Origens do T11 | Lista Origens com `● Dado do T11` e `◐ Dado de outro carro (TX, T09)` nas posições 1 e 2; prefixo DEMONSTRATIVO do D16 pelo T11. |
| Python | `python/metas.py` (oráculo de coerência), `python/aba_metas.py` (fórmulas das fichas), `python/origens.py`, `python/gerar_v4_2.py`, `python/viva.py`; `origem_do_carro` em `equilibrio.texto_veredito` e `equilibrio_linear.texto_k`; motivo do NÃO CONCLUSIVO corrigido em `equilibrio.veredito_robusto` (EDR-060 item 8 (x)). |
| Ferramentas | `tools/conferir_viva.py`, `tools/retrato_viva.py`, `tools/migrar_viva.py` (viva do Drive, só por cópia) e `tools/medir_recalculo.py` (recálculo da V4.1 pelo Excel). |
| IDs | TARGET-006 e TARGET-007 (EDR-061); EDR-061, EDR-062 e EDR-063; TC-WB42-001 a TC-WB42-006. |
| Documentos | `docs/metas/README.md` e `docs/metas/TARGET-001.md` a `TARGET-007.md`; `docs/registro-de-versoes-V4_2-celulas.md` (gerado); `docs/v4-2/medicao-recalculo-v4-1.md`. |

Decisões de forma, todas nos EDRs: a lista Origens continua com seis rótulos nas mesmas posições (nenhuma fórmula de pior
origem muda); a alavanca de cada meta vem da tabela de relações, não é digitada; toda meta continua TBD e nenhum valor-alvo
foi inventado; a coerência de uma meta sem valor ou papel é NÃO AVALIÁVEL, nunca COERENTE; o retrato dos dados da viva é um
JSON por nome, não o .xlsx.

## Células existentes alteradas

O antes e o depois de cada célula estão em `docs/registro-de-versoes-V4_2-celulas.md` (gerado por `python/gerar_v4_2.py`).
São 55 células, em resumo:

- Dado: 32 células de Origem (`05_VEHICLE` 16 e `06_SUSPENSION` 16) com `● Dado do TX` ou `◐ Dado do T09` passam a
  `◐ Dado de outro carro (TX, T09)`. Ninguém vira `● Dado do T11`, porque o T11 ainda não tem dado.
- Lista e regra: `00_README` A43, B43, E43, A44, B44 e E44 (lista Origens e significado) e A49; `14_DASHBOARD` A40,
  `16_EQUILIBRIO` A2, `20_EQ_TROCA` A2 e `22_CADEIA` A2 (textos que explicam a Origem).
- Fórmulas: `16_EQUILIBRIO` B188 (K) e B189 (veredito). Só o literal `"● Dado do TX"` do `EXACT` passa a `"● Dado do T11"`.
  Todas as outras fórmulas da V4.1 ficam com texto idêntico.
- Emenda da h7: `21_COBERTURA` D12 (texto da spec §7.4, linha 7; deferida do incremento 4). O plano dizia F12, mas a F12 é a
  fórmula "Chave agora"; o texto está na coluna D.
- `03_TARGETS`: A3, A11 e A12, e as notas que descem para A14 e A15.
- Versão: `00_README` A3 (V4.2) e `15_CHANGELOG` linha 22.

A planilha viva da equipe continua a V4.1 no Drive até a troca (Task 8). A V4.2 não a substitui sozinha.

## Testes (`tools/rodar_testes.py`)

A contagem final da suíte da V4.2 ainda não está aqui: a Task 7b roda a suíte inteira e preenche este registro e o CLAUDE.md.
Os scripts novos e o que cobrem:

| Teste | O que junta | Script |
|---|---|---|
| TC-WB42-001 | estrutura: abas e ordem, 117569 fórmulas da V4.1 idênticas fora de B188 e B189, nenhum rótulo antigo fora do 04 e do 15, nomes, entradas novas com validação, fonte de cada relação, toda célula nova numa família G1-G6 | `tests/test_v4_2.py` |
| TC-WB42-002 | CA-07 da V4.2: regenerações idênticas e recusas do gerador | `tests/test_v4_2.py` |
| TC-WB42-003 | oráculo `metas.py`: cada estado de coerência, ordem das regras, sete METAs ao mesmo tempo, EDR em formato inválido | `tests/test_v4_2.py` |
| TC-WB42-004 | fluxo da viva sem motor: `migrar_viva`, `conferir_viva`, `retrato_viva` | `tests/test_v4_2.py` |
| TC-WB42-005 | motor: 0 erros, equivalência por valor com a V4.1, origens do T11, κ do pico de Fx fora da forma fechada | `tests/test_workbook_v4_2.py` |
| TC-WB42-006 | coerência na planilha contra `metas.py` com as sete fichas preenchidas, mais o dashboard | `tests/test_workbook_v4_2.py` |

Teste de planilha só no Excel durante as tarefas; o LibreOffice entra só na suíte final. "Passou" é a planilha reproduzir o
oráculo em Python nos casos de teste (valores de teste rotulados, só em cópias); não é validação física (Validation =
NOT_VALIDATED, EDR-022).

## Pendências

- **Contagens finais da suíte** e a cópia da V4.2 para `excel/`: Task 7b (commit próprio).
- **22_CADEIA, etapa 8:** o texto "Incremento 5 (ainda não existe nesta planilha)" fica desatualizado na V4.2. A célula é
  existente e fora da autorização 5; decisão do usuário sobre incluí-la numa próxima versão.
- **Medição do recálculo** (`docs/v4-2/medicao-recalculo-v4-1.md`): no arquivo da tag (sem valores em cache, cenário A) a
  mediana foi de 10,98 s; no arquivo já salvo pelo Excel, como a viva (cenário B), 2,64 s.
- **Troca da viva no Drive** depois do merge e da tag `v4.2` (Task 8): `tools/conferir_viva.py`, depois
  `tools/migrar_viva.py`, e o usuário troca o arquivo. Responsável pela planilha e pelos retratos `dados:`: o usuário.
  O primeiro retrato (`data/viva/retrato-viva.json`) ainda não foi gerado.
- **Projeto T11:** a planilha ainda não tem dado do T11. Freio dentro da roda e motor no chassi, atrás (usuário, 2026-10-19),
  foram ditos antes de o T11 ser informado: confirmar se valem para o T11 (EDR-048).
- **Metas:** todas TBD. Papel, valor, responsável, compromisso, EDR e a lista de objetivos da equipe são decisão da equipe.
  Quem revisa a promoção de cada meta: a confirmar. O limiar de custo da tabela de troca depende de EDR da equipe (spec §5,
  item 5).
- **Fontes L:** as três páginas (Gillespie p. 214, Milliken §7.1 p. 283-286, Milliken p. 313-315) foram conferidas na imagem do
  PDF pelo implementador da Task 3 e serão reamostradas na revisão final. As páginas citadas só pelo Engineering Standard
  (frequência natural, anti-dive e anti-squat) não foram reconferidas e não aparecem como fonte L.
- Pneu do carro (R60A) ou dataset do OptimumTire: o equilíbrio continua usando o `.tir` provisório do TTC (EDR-038, EDR-055).
- Limitações conhecidas do EDR-060 (item 8) continuam; o item (xi) foi acrescentado.
- Reescrita das 387 fórmulas antigas para nomes: incremento 7 (D13). Efeito no objetivo e malha fechada da coerência:
  incremento 7 (spec §10).
