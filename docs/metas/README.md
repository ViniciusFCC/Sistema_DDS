# Metas e coerência das fichas (V4.2)

Processo das metas da planilha, para a equipe Tupã. Vale a partir da V4.2 (incremento 5; EDR-061). A especificação é
`docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` (§4 e §5); as regras em código estão em
`python/metas.py` (oráculo) e `python/aba_metas.py` (fórmulas da planilha). Toda meta continua **TBD**: nenhum valor-alvo
foi definido pela equipe, e nada aqui o inventa.

## Os três níveis (spec §4.1)

1. **Objetivo:** o que o carro precisa fazer (prova ou uso). A lista de objetivos é decisão da equipe, registrada em EDR;
   enquanto não existe, a coluna "Objetivo atendido" da 03_TARGETS diz "TBD: lista de objetivos da equipe a definir em EDR".
2. **Comportamento:** grandeza física que se mede no carro (gradiente de subesterço, push/loose no limite, frequências).
   É aqui que as metas (TARGET-xxx) ficam.
3. **Parâmetro:** hardware ou acerto (mola, barra, MR, geometria). Sai do modelo no Design Mode e não é digitado como meta.

## Processo de uma meta (spec §4.2)

Cada meta segue os oito passos do Guia G.3: definir o requisito de comportamento; avaliar pneus e uso do carro; avaliar
massa e envelope de suspensão; comparar literatura e experiência anterior; estudar sensibilidade; propor faixa; validar
contra embalagem e hardware; aprovar e congelar. A ficha é o registro desses passos. Pela regra de promoção do Guia F.3,
uma meta só entra como decisão com responsável, justificativa, faixa ou valor, fonte ou racional, revisão e estado.

## A ficha (spec §4.3)

Duas partes. A **ficha curta** fica na aba `03_TARGETS` (linhas 5 a 11) e a **ficha completa** em `docs/metas/TARGET-00x.md`.

Colunas da 03_TARGETS na V4.2 (cabeçalho na linha 4):

| Coluna | Campo | Como é preenchida |
|---|---|---|
| A:G | ID, Parameter, Target, Status (ciclo de vida da meta), Owner, Decision, Revision | entrada (C:G das linhas 10 e 11 são novas) |
| H | Papel | entrada, lista: META, CONSEQUÊNCIA, TBD |
| I | Alavanca | fórmula sobre a tabela de relações da 23_LISTAS (não é digitada) |
| J | Congelamento | entrada, lista: F0 a F4 |
| K | Valor atual do modelo | fórmula: `=nome` do resultado da grandeza |
| L | Pior origem da grandeza | fórmula: a pior origem das entradas da grandeza |
| M | Compromisso declarado | entrada, texto |
| N | EDR do compromisso | entrada, texto no formato `EDR-ddd` |
| O | Coerência | fórmula: estado de coerência, "·" e a pior origem |
| P | Ficha | texto: `docs/metas/TARGET-00x.md` |
| Q | Objetivo atendido | entrada, texto |
| R:U | auxiliares ocultas | fórmulas de vocabulário e de sobredeterminação |

As linhas 10 e 11 são o TARGET-006 (gradiente de subesterço K, SUS-1001) e o TARGET-007 (comportamento no limite: push/loose
e C_N, SUS-1004). As notas que ficavam em A11 e A12 passaram para A14 e A15.

## Estados: quatro grupos independentes (spec §4.4)

Os quatro grupos nunca se misturam. Cada um tem seu vocabulário, que a 23_LISTAS guarda e a validação de dados usa.

**Ciclo de vida da meta** (Guia G.1), coluna Status (D): `TBD` valor ainda não definido; `OPEN` discussão ativa; `PROPOSED`
proposta submetida; `APPROVED` decisão tomada; `FROZEN` baseline do ciclo; `STALE` não representa a configuração atual.

**Congelamento** (Guia §3.2; EDR-034 decidido na V4.2), coluna J. A promoção é proporcional ao uso (Guia §3.12) e os critérios
para descongelar são os do Guia §3.13. Vale para fichas de meta e para parâmetros, ao lado do ciclo de vida e nunca no lugar dele.

| Nível | Significado | Uso |
|---|---|---|
| F0 | Aberto; exploração. | Somente para investigação. |
| F1 | Conceito definido. | Para discussão arquitetural. |
| F2 | Especificado. | Pode ser implementado. |
| F3 | Implementado e verificado internamente. | Pode alimentar análises internas. |
| F4 | Congelado para o uso definido. | Pode ser usado como baseline do ciclo. |

**Validação** (modelo contra referência): NOT_VALIDATED, PASS, WARNING, FAIL (FAIL quer dizer "não validado", não "modelo
errado"). **Registro de decisão** (EDR): PROPOSED até VERIFIED, como no registro; VERIFIED não implica validação física.
Esses dois já existiam e não mudam.

**Coerência da ficha** (novo): `COERENTE`, `COMPROMISSO DECLARADO`, `CONFLITO`, `NÃO AVALIÁVEL`. Ao lado de cada estado a
planilha mostra a pior origem das entradas da grandeza ("NÃO AVALIÁVEL: meta sem valor ou papel (TBD) · ○ ...").

## Papel, alavanca e a lógica entre fichas (spec §5)

- **Papel.** META é o valor que a equipe escolhe e manda na alavanca. CONSEQUÊNCIA é resultado do modelo, dadas as METAs e as
  outras alavancas. TBD é papel ainda não definido.
- **Alavanca por relação.** A coluna I vem da tabela de relações da 23_LISTAS, uma fonte só. As alavancas são: TARGET-001
  mola dianteira; TARGET-002 mola traseira; TARGET-003, 006 e 007 distribuição de rolagem λ_f (barras); TARGET-004
  geometria dianteira (anti-dive); TARGET-005 geometria traseira (anti-squat).
- **Fonte de cada relação.** Relação sem fonte não existe, e a falta de linha significa "não avaliado", nunca "ok". Fonte
  `L` é livro e página, conferidos na imagem do PDF; `E` é EDR existente e aprovado; `M` é cálculo da planilha (nome do
  resultado e nome da entrada da alavanca, e a entrada tem de ser raiz do resultado no grafo de fórmulas). Na V4.2 há sete
  relações M e três L: Gillespie p. 214, Milliken §7.1 p. 283-286 e Milliken p. 313-315. Nenhuma relação E por enquanto.
- **Três tipos de incoerência** (spec §5, item 1): erro de categoria (campo fora do vocabulário), impossibilidade (duas METAs
  na mesma alavanca) e troca de valor (custo declarado, que nunca é conflito automático).
- **Tabela de troca e custo** (spec §5, itens 3 a 5): a tabela de troca da barra dianteira está na 20_EQ_TROCA (EDR-060, item 6)
  e é grade de exibição, não meta. O limiar de custo só existe por EDR da equipe; até lá a célula diz "limiar não definido".

## Coerência: a regra da V4.2 (EDR-061)

A primeira regra que bate decide:

1. campo fora do vocabulário (Papel, Ciclo de vida, Congelamento): `CONFLITO: <campo> fora do vocabulário`;
2. Papel = META e outra META na mesma alavanca: `CONFLITO: sobredeterminação (<alavanca>; escolha qual manda)`;
3. Papel = TBD, ou Target = TBD ou vazio: `NÃO AVALIÁVEL: meta sem valor ou papel (TBD)`;
4. compromisso declarado preenchido: com EDR no formato `EDR-ddd`, `COMPROMISSO DECLARADO`; sem EDR ou com formato errado,
   `CONFLITO: compromisso sem EDR`;
5. senão, `COERENTE (regras avaliadas: vocabulário e sobredeterminação)`.

Por que a regra 3 existe: um `COERENTE` numa meta vazia diria "ok" onde nada foi avaliado. A comparação é exata (maiúsculas
e minúsculas contam), porque a validação de dados não pega um valor colado por cima. Que o EDR citado existe e está
aprovado é conferido fora da planilha (`tools/conferir_viva.py` e o TC-WB42-001), pois uma cópia do status do EDR na
planilha envelheceria sem aviso. O efeito no objetivo, a malha fechada e o custo ficam para o incremento 7 (spec §10).
No 14_DASHBOARD, a linha 50 mostra a pior coerência (CONFLITO, depois NÃO AVALIÁVEL, depois COMPROMISSO DECLARADO, depois
COERENTE) e a linha 51 conta os compromissos declarados.

## Como promover uma meta

1. Preencher a ficha completa (`docs/metas/TARGET-00x.md`) com os passos G.3 1 a 6.
2. Definir o Papel e, se for META, o Target com valor, justificativa e responsável (Owner). Duas METAs na mesma alavanca dão
   CONFLITO: escolha qual manda.
3. Registrar a decisão em EDR e citá-lo (coluna N, formato `EDR-ddd`) se houver compromisso declarado.
4. Mudar o Status e o Congelamento só com a regra do Guia F.3 cumprida. Quem revisa a promoção é definido na especificação
   de cada meta: **a confirmar** com a equipe (a spec §5, item 10, deixa o processo humano para cada meta).
5. Se a planilha viva da equipe mudou, o usuário (responsável pela planilha) faz o retrato `dados:` depois de
   `tools/conferir_viva.py` dar 0.
