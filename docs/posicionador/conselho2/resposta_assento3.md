# Resposta: formulação, viabilidade e busca

Scripts e saídas em `docs/posicionador/conselho2/trabalho_assento3/` (E1 a E5). Juiz: `busca.avaliar_convergido`, cena sem CAD como no
benchmark, salvo E4. As perturbações e os relaxamentos são de teste: nenhum é valor do carro.

## Q2 primeiro: por que não se achou posição viável

**[cálculo]** Curso da roda: 23 + 62,4 = 85,4 mm, que é 61 × 1,40 (o próprio `config_T11.json` dá como fonte do bump "61 mm de
amortecedor × MR"). O amortecedor gasta ∫dz/MR ao longo do curso, então Lmin ≥ 149 mm equivale a **MR harmônico médio no curso
≥ 1,400**. As metas foram montadas com margem zero.

**[código, E1]** As 6 soluções finais do posicionador têm a curva de MR em U (cerca de 1,41 nas pontas e 1,36 a 1,37 no meio) e
MR(0) = 1,4000, fixado pela construção (`mecanismo.construir` resolve r2 para MR(0) = alvo exato). O MR harmônico fica entre 1,383 e
1,389, o curso usado entre 61,51 e 61,74 mm, e por isso falta 0,5 a 0,74 mm **com qualquer variação de MR** (a de 2,96 % também
fica curta). A v20 tem MR harmônico de 1,4000, mas variação de 6,2 %.

**[código, E2]** Refazendo o Nelder-Mead (300 avaliações, n = 11) a partir das 6 finais em três parametrizações:

| Parametrização | Juiz convergido |
|---|---|
| A, atual: r2 pelo MR(0) = 1,40 (controle, mesmo orçamento) | 0/6 (sempre o Lmin; às vezes r2 > 80) |
| B: r2 livre, MR(0) conferido em ±0,01 | 2/6 CONDICIONAL |
| C: r2 pelo curso (curso usado = 60,95 mm) | 3/6 CONDICIONAL |

**[código, E4]** Com o STEP, as 7 soluções sem violação (E2 e E3) continuam CONDICIONAL. A folga ao chassi fica entre 52 e 113 mm
(referencial HIPOTESE). O CONDICIONAL vem do que não se pode verificar: gabarito, AIP, esterçamento e manga.

Leitura: **(b) parametrização explica o vazio** (a construção descarta a faixa de MR(0)); **(a) o conflito é real, na borda**: MR(0)
no teto, variação 4,00 %, Lmin e r2 = 80 mm ativos juntos; **(c)** o CAD não aperta aqui; **(d)** não testado, e as margens são menores
que a incerteza plausível do modelo (inferência).

## Q1: precisão

1. **[código, E3 e E5]** A região viável é uma fatia fina. A maior margem uniforme que encontrei foi de 0,03 a 0,05 % (Lmin de 149,04
   a 149,07 mm). Com a perturbação SINTÉTICA do benchmark, 1 de 40 amostras fica sem violação. Um veredito binário sobre margem de
   dezenas de µm engana. Mudança: o certificador publica a margem de cada restrição em unidade física e um veredito "viável com
   margem ≥ δ", com δ a medir (decisão anterior do conselho).
2. **[fato, `varredura.py` l. 58 e 393]** A tolerância ±0,01 de MR(0) é uma constante do código ("plano da fase 1"), sem item nem
   origem na configuração. As soluções viáveis dependem dela, então ela tem de ir para `config_T11.json` com origem.
3. **[código, E3, variante 5 %]** A avaliação rápida (n = 11) é otimista na fronteira: o refino leva a variação a 5,00 % e o juiz mede
   5,02 %. Perto da borda, o refino tem de usar n maior ou uma margem de discretização.
4. **[inferência]** A Fase I conta coocorrências em amostras aleatórias (99 % com a variação de MR violada). Isso não mede conflito: o
   conflito se mede na fronteira, depois do refino (Q4).

## Q3: desenho da busca

- **Construção**: r2 como variável, ou resolvido pelo curso (Lmin = 149 mm + margem). MR(0) passa a ser uma restrição conferida.
- **Filtro analítico barato**, condição necessária antes da cinemática completa: MR harmônico ≥ curso da roda/(curso do amortecedor −
  margem). Ele vira também o primeiro item do relatório de conflito.
- **Duas fases explícitas**: a Fase I minimiza a violação máxima (como hoje). A Fase II, nos viáveis, maximiza a menor folga
  normalizada (centro de Chebyshev), e não a variação de MR, porque o que falta é robustez, não otimalidade. Uma restrição que é
  igualdade por construção (Lmax = EYE no droop) fica fora do máximo-mínimo: incluí-la tornou degenerada a primeira rodada de E3
  (`e3a_*`).
- **Partida múltipla** (LHS amplo, parametrização B ou C) e **certificado parcial** de inviabilidade (condições necessárias mais a
  maior margem achada por relaxamento). Não há certificado rigoroso numa caixa-preta.

## Q4: mapa de conflitos medido

**[código, E3 e E5]** Máximo-mínimo com 250 avaliações e 2 partidas: são limites inferiores.

| Relaxamento (teste) | Margem uniforme | Lmin [mm] | Sem violação, 40 perturbações |
|---|---|---|---|
| nenhum | 0,03–0,05 % | 149,04–149,07 | 1 |
| tolerância de MR(0) ±0,02 | 0,23–0,26 % | 149,34–149,39 | 9 |
| braço máximo 85 mm | 0,03–0,27 % | 149,12–149,41 | 0 |
| bump −1 mm (61,4) | 0,40–0,62 % | 149,59–149,93 | 6 |
| variação de MR 5 % | inconclusivo (artefato do n = 11) | — | — |

Nenhum relaxamento isolado dá robustez. Ordem proposta, que é proposta e não ação:

1. **Formalizar a tolerância de MR(0)**: hoje ela não é meta da equipe. Pergunta: "Qual faixa de MR estático é aceitável: 1,40 ± ?, e
   com que fonte (ride rate)?"
2. **Orçamento do curso**: o curso da roda é 61 × 1,40, sem margem. Pergunta: "O bump de 62,4 mm é requisito ou consequência do curso
   do amortecedor? Aceitam 1 mm a menos, ou uma margem de fim de curso no amortecedor?"
3. **Braço máximo de 80 mm**. Pergunta: "O limite vem de espaço ou de rigidez do rocker? Cabe 85 mm?"
4. **Variação de MR de 4 %**, por último: ela é a meta que dá o comportamento ao carro.

## Q5: riscos e o que não fazer

O que pesa contra esta leitura: o E2 partiu das finais do benchmark (há viés de região), a cena não tem CAD móvel e a cinemática é
NOT_VALIDATED. O teste mínimo que derruba a recomendação: (i) LHS amplo com a parametrização B ou C, cerca de 2000 amostras, sem
nenhum CONDICIONAL; ou (ii) o OptimumKinematics dar MR harmônico diferente por mais de 0,3 % na v20. Isso apagaria as margens
(inferência).

Não fazer: aprovar solução com margem de µm, refinar com n = 11 até a fronteira, relaxar primeiro a variação de MR, ou ler as
coocorrências da Fase I como mapa de conflito.

**Recomendação em uma frase:** trocar a construção que fixa MR(0) = 1,40 por r2 livre ou resolvido pelo curso, buscar em duas fases
(viabilidade e depois maior margem mínima) e levar à equipe, na ordem, a tolerância de MR(0) e o orçamento de curso (85,4 = 61 ×
1,40, sem margem), porque com isso 5 de 12 refinos acharam posições sem violação, que também passam no chassi do STEP, mas todas com
margem de dezenas de µm.

**Confiança:** média. Principal incerteza: se a fatia viável existe fora da vizinhança das 6 soluções do benchmark e se ela
sobrevive à validação da cinemática contra o OptimumKinematics.
