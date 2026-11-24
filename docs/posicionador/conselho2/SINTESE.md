# Síntese do presidente: conselho 2 (precisão, posições válidas, conflitos), 2026-11-24

Rótulos: **[código]** medido por um assento ou revisor; **[cálculo]**; **[inferência]**; **[decisão]** minha como presidente (proposta, não
aprovação). Nenhuma meta, limite ou fórmula foi alterado: tudo abaixo que muda comportamento é PROPOSTA, aguarda a equipe.
Modelos: assentos 1, 3, 5, 7 em opus; 2, 4, 6 em sonnet (fable indisponível: erro de créditos; 3 e 5 foram refeitos em opus).

## Ranking (Borda, revisão anônima, 7 votos; com / sem o voto próprio)
| Resposta | Assento | Com | Sem | 1º lugar |
|---|---|---|---|---|
| C | otimização | 39 | 33 | 5 de 7 |
| E | cinemática | 34 | 28 | 1 |
| D | cético | 26 | 21 | 0 |
| B | CAD/software | 23 | 19 | 0 |
| G | regulamento | 18 | 12 | 1 |
| F | estrutura | 4 | 3 | 0 |
| A | pragmático | 3 | 2 | 0 |
A ordem C > E > D > B > G é igual com e sem o voto próprio. F e A ficam no fim por motivos opostos: F é correta, mas estreita (não ataca o vazio de MR);
A testou com orçamento curto (1 semente) e a revisão a considerou subamostrada.

## O que o conselho estabeleceu (convergência)
1. **[cálculo, confirmado por cinco assentos a 1e-3 mm] A causa raiz é uma identidade, não uma "falta de 1 mm".** O curso do amortecedor é a
   integral de dz/MR sobre o curso da roda. Com bump = 61 × 1,40 − 23 (o bump da equipe foi derivado de 61 mm × 1,40), o curso da roda é 85,4 mm e o
   comprimento mínimo (149 mm) só é cumprido se o **MR harmônico médio no curso for ≥ 1,400**, com MR(0) cravado em 1,40 pela construção. O problema tem **margem
   zero por construção** nas duas pontas. As curvas de MR das soluções do benchmark têm forma de U: o harmônico fica em 1,383 a 1,389, e faltam 0,5 a 0,74 mm de curso
   qualquer que seja a variação de MR. Logo a variação de 4 % **não** é a restrição que prende; a hipótese do relatório do benchmark ("conflito entre variação de MR e curso")
   está **incompleta** e deve ser corrigida na `leitura.md` (aguarda seu OK; é texto meu).
2. **[código] A construção atual é a principal limitação da busca.** Com o mesmo refino (300 avaliações) a partir das 6 finais: r2 resolvido para MR(0)=1,40 (atual) 0/6 sem
   violação; r2 livre 2/6; r2 resolvido pelo curso 3/6. Em 12 refinos, 5 acharam posições **sem nenhuma restrição violada**, e elas continuam assim com o STEP (CONDICIONAL; folga ao chassi
   de 52 a 113 mm, referencial HIPOTESE). Outro assento achou posição sem violação liberando o ângulo de transmissão do push rod no estático (δ).
3. **[código] Essas posições estão "no fio da navalha":** folga de dezenas de µm (0,03 a 0,06 mm), 1 de 40 amostras sob perturbação sintética sem violação, quatro restrições ativas ao
   mesmo tempo (MR(0), variação de MR, comprimento mínimo, r2). **Nenhuma pode ser chamada de solução.**
4. **[código] O CAD não explica o vazio de MR** nos candidatos do benchmark (as 4 melhores passam em todas as folgas ao STEP). Mas os pivôs achados ficam no ar (179 a 281 mm do nó mais próximo): todo
   CONDICIONAL é "chassi hipotético". Referencial e aro, hoje, não decidem nada (folga ao aro ≥ 63 mm; ±5 mm na transformação do STEP muda a folga em até 4,5 mm).
5. **[código] Precisão:** o refino com n = 11 é otimista na borda (4,0 → 4,05 %; 5,00 → 5,02 %); a convergência hoje compara **estados**, não **valores**; e `TOL_MR0` (±0,01) é uma constante do código
   sem origem na configuração, da qual as soluções viáveis dependem. A estatística de coocorrência da Fase I (amostras aleatórias) mede o volume da caixa, não conflito.
6. **[inferência] "Não existe" nunca foi provado:** o veredito correto é "não encontrada com margem", e a busca por amostragem não certifica inexistência.

## Decisões do presidente sobre as divergências
1. **Ordem de relaxamento (proposta).** Primeiro o que **não é meta**: liberar δ e resolver r2 pelo curso (construção). Depois levar à configuração, com origem e como A_CONFIRMAR, a tolerância de MR(0)
   e a **margem de fim de curso** do amortecedor (hoje 0). Depois o bump (G propõe 62,4 → 58,0 mm; cada 1 mm de margem custa ≈ 1,39 mm de bump). Depois r2 > 80 mm. **A variação de MR de 4 % fica por último**
   (unânime). O relaxamento de bump só vale se vier amarrado à margem real e ao piso de curso de roda de 50 mm (V.3.1.1, a verificar com piloto sentado).
2. **Natureza do conflito:** fica a **fronteira de três restrições** (curso, MR(0)/harmônico, r2), não um par; r2 colado em 80 mm em 28 otimizações. Reportar cada violação em **unidade física** (mm de curso, mm de r2, pontos
   percentuais de MR).
3. **Números de recuperação de MR(0) divergentes** (1,41 recupera 0,43 mm; 1,405 dá 3/4 CONDICIONAL; 1,417 fecha): **não é contradição**, partem de pontos refinados diferentes (≈ 0,44 mm por 0,01 em todos).
   Exige-se um **único rejulgamento** nas mesmas partidas, com `avaliar_convergido`.
4. **CAD:** não é causa; construtibilidade vira item novo. Adotar a proposta do assento de estrutura: exigir **caminho de carga alcançável** (tubo existente ou aresta-fantasma entre nós existentes, com d_max A_CONFIRMAR,
   NAO_VERIFICAVEL até haver valor) e a regra do hospedeiro; nó **não** vira limite duro; carga **não** se inventa.
5. **Comprimento do amortecedor (210/61/149 mm):** tratar como **dado de componente** (duro), pendente da folha do DNM (A_CONFIRMAR); hoje está rotulado META.
6. **Critério de aprovação:** folga de µm não vale. O certificador deve exigir folga ≥ k·σ (σ de fabricação **a medir**, propagado por jacobiano, com o olhal C também perturbado) e convergência **por valor**, devolvendo
   **INDETERMINADO** quando |folga| < erro estimado da medida. Até haver σ_fab, o máximo é CONDICIONAL com o aviso "margem < δ".

## Plano proposto (aguarda sua aprovação; nada abaixo foi implementado)
1. **Experimento único de controle** (mesmo orçamento, com STEP, ≥ 30 partidas): construção atual × r2 resolvido pelo curso × δ livre, rejulgado por `avaliar_convergido`; objetivo: **maior margem mínima em unidades físicas**, estável entre orçamentos.
2. **Mapa de compromisso sem CAD** (variação de MR × curso × r2) e **frente de Pareto** com a margem de fim de curso como parâmetro; vira a figura para a reunião da equipe.
3. **Mudanças de código** (cada uma com teste e registro no EDR-076, sem mexer em meta): convergência por valor + INDETERMINADO; refino com n maior perto da borda; `TOL_MR0` na configuração com origem; busca em duas fases (viabilidade, depois margem);
   caixa de busca estreitada em Z (os melhores pivôs ficam em Z 371 a 476 mm, contra 60 a 1257 mm da caixa); cache da cena do CAD (a avaliação com CAD custa 0,38 s, 60 % em `folga_segmento`).
4. **Perguntas para a equipe, nesta ordem:** (a) qual é a margem de fim de curso mínima do amortecedor?; (b) a tolerância de MR(0) pode ser maior que ±0,01 (qual)?; (c) o curso de roda exigido é 85,4 mm ou o piso de 50 mm de V.3.1.1 mais uma margem?;
   (d) r2 máximo de 80 mm é meta ou dado de fabricação?; (e) a variação de 4 % é mesmo exigida?

## Riscos e o que derrubaria a recomendação
- Todas as 5 posições viáveis partiram das 6 soluções do benchmark: **não se sabe se a faixa viável existe longe delas** (o experimento 1 testa).
- A cinemática segue NOT_VALIDATED contra o OptimumKinematics: uma posição viável pode não sobreviver à validação.
- As folgas são frágeis (µm); sem σ_fab o resultado serve para orientar a equipe, não para aprovar.
- Não relaxar meta para "passar": a margem de fim de curso piora o problema, e o relaxamento de bump só compensa se for decidido com ela.

## Fica com a equipe
Margem de fim de curso, tolerância de MR(0), curso de roda exigido, r2 máximo, variação de MR máxima, σ_fab, folha de catálogo do amortecedor, carga de projeto e d_max do caminho de carga, curso da cremalheira.
