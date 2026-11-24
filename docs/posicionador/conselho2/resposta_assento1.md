# Resposta: a física do mecanismo e o conflito entre MR e curso

Scripts e saídas em `docs/posicionador/conselho2/trabalho_assento1/` (`curvas.py`, `fase.py`, `refino.py`, `juiz.py`,
`com_step.py`, `mr0.py`; `runs.jsonl`, `refino.jsonl`, `juiz_saida.txt`). A cinemática é o `kinematics_model`,
NOT_VALIDATED (EDR-004): nada aqui é validação física.

## O mecanismo em três relações

1. **[resultado de código + cálculo] O curso usado é ∫dz/MR.** Nos 6 melhores do benchmark e na v20, Lmax − Lmin bate com
   ∫dz/MR(z) a 0,001 mm (`curvas.py`). Como C é posto com L = EYE no droop, "Lmin ≥ 149 mm" equivale a "média harmônica do
   MR no curso ≥ 85,4/61 = 1,4000". **[fato de fonte]** BUMP = 62,4 mm foi definido como 61 × 1,40 − 23 (`config_T11.json`).
   **[cálculo]** Então a meta de curso exige que a média harmônica do MR seja ≥ MR(0), exatamente: com MR(0) fixo em 1,400 pelo
   `brentq`, o problema está no fio da navalha por construção, não por acaso.
2. **[resultado de código]** Os melhores têm curva de MR em U, com o mínimo em dz ≈ 40 mm (no bump) e o máximo nas pontas. Quase
   todo o bump fica abaixo de MR(0): a média harmônica dá 1,383 a 1,389, que corresponde ao déficit de 0,5 a 0,74 mm do benchmark.
3. **[cálculo, confirmado por código]** O braço máximo e o curso inteiro forçam o giro do rocker: giro ≥ 2·asin(61/(2·r2_máx)) =
   44,8° com r2_máx = 80 mm. Medido: 45 a 47,5° em todas as 28 otimizações, com r2 colado em 80 mm em quase todas. Por isso o
   braço máximo é uma restrição ativa escondida. Com cerca de 45° de giro, os ângulos de transmissão (desvio da perpendicular)
   variam cerca de 50° no curso. **[inferência]** O MR ≈ MR_bandeja(z)·r1·cos γ1/(r2·cos γ2), e a variação vem do descompasso
   entre os dois cossenos. **[fato de código]** O `mecanismo.construir` põe o push rod tangente (γ1 = 0) no estático, que fica a
   27 % do curso. **[resultado de código]** Por isso γ1 vai de −13° a +35° e γ2 de −11° a +41°: as duas fases ficam deslocadas
   para o bump, o que dá o U fora do lugar.

**[inferência]** A família quase fechada é esta: r2 no máximo, giro ≈ 45°, e as duas fases centradas no meio do curso e iguais
entre si (razão de cossenos plana), com MR(0) na parte baixa da curva. A tangência no estático (δ = 0) impede justamente isso.

## Q2. Por que não se achou posição viável (experimento rodado)

Refinei os melhores do benchmark com δ (rotação de A0 em volta do eixo do rocker a partir da tangência) como 8ª variável, e
rodei um controle com δ = 0 com o mesmo orçamento (Nelder-Mead, 400 + 500 avaliações). Os dois foram julgados por
`avaliar_convergido`, sem CAD e com o STEP (transformação HIPOTESE). **[resultado de código]**
- Com δ = 0 (4 refinos): os 4 saem INVIAVEL, com Lmin de 0,08 a 0,15 mm abaixo do limite.
- Com δ livre (4 refinos): 1 sai **CONDICIONAL, também com o STEP** (δ = −8,0°; variação de MR 3,88 %; Lmin 149,057 mm; r2 a
  0,62 mm do limite), 1 cumpre a cinemática e falha só a perna da bandeja, e 2 colidem com o chassi (amortecedor de −19 a
  −25 mm).
- Com MR(0) = 1,405 (dentro da faixa de ±0,01 do juiz) e δ = 0: 3 de 4 saem CONDICIONAL sem CAD. Cada 0,01 de MR(0) dá
  61/1,40 ≈ 0,44 mm de curso.

**[inferência]** A causa é principalmente (b), a parametrização: há duas escolhas de construção que não são metas, a tangência
no estático e o MR(0) cravado no centro da faixa. Por cima delas há um conflito de metas real e pequeno (a): a identidade do
item 1. O CAD (c) derruba metade dos candidatos com δ livre. Sobre (d) não sei dizer. O experimento que decide é a busca do
repositório com δ e MR(0) livres, com o STEP, em 6 sementes, comparada a um controle com o mesmo orçamento.

## Q1. Precisão

**[resultado de código]**
- O estimador rápido subestima a variação: com 31 pontos ela parecia 4,0 %, e o juiz mediu 4,05 a 4,12 %. A meta tem de ser
  conferida no convergido, como o juiz já faz.
- A sensibilidade do candidato CONDICIONAL é enorme. Cada 0,5° em φB muda a variação em ±0,75 pp e Lmin em ±0,13 mm. Cada 0,5°
  em δ muda a variação em ±0,32 pp. A folga de Lmin é de 0,057 mm.

**[inferência]** Um veredito com essa folga não tem significado sem tolerância de fabricação. Proponho publicar cada folga em
"número de desvios": a folga dividida por |∂g/∂x|·δ_fab, com o jacobiano por diferenças finitas e o δ_fab a medir (decisão do
conselho anterior).

## Q3. Desenho

- Pôr δ na busca (ou parametrizar diretamente por γ1 e γ2 no meio do curso, que são variáveis com sentido físico).
- Tratar MR(0) como variável dentro de uma faixa que a equipe declara.
- Usar a média harmônica como pré-filtro barato do curso.
- Fazer a busca multiobjetivo: variação de MR × curso usado × margem robusta. Só o juiz convergido aprova.

## Q4. Mapa de conflitos (unidades físicas)

**[resultado de código, frente aproximada, limite superior por ser busca local]**
- Variação de MR × curso: 0,12 mm de curso por ponto percentual de variação com δ = 0 (3 % → 61,3 mm; 6 % → 61,0 mm), e cerca
  de 0,18 mm por ponto com δ livre (6 % → 60,7 mm).
- MR(0) × curso: 0,44 mm por 0,01.
- Bump × curso: 1 mm de roda = 0,71 mm de amortecedor.
- Braço máximo × giro: 80 mm → 44,8°; 90 mm → 39,6°; 100 mm → 35,5° (cálculo).

**[inferência]** A margem de fim de curso (`margem_curso_amortecedor_m`, A_CONFIRMAR, hoje 0) domina tudo. Qualquer margem de
alguns milímetros é impagável pela variação de MR (seriam mais de 5 pp por milímetro), e só se paga com bump ou com MR(0).

Ordem proposta, para a equipe decidir:
1. Liberar δ (não relaxa meta nenhuma).
2. Declarar a faixa de MR(0).
3. Fixar a margem de curso e, com ela, o bump.
4. Mexer na variação de MR por último.

Perguntas para a equipe:
- "O MR(0) de projeto é 1,40 exato ou uma faixa? Qual?"
- "Qual margem de fim de curso o amortecedor exige, e o bump de 62,4 mm pode cair em quanto?"
- "Os 4 % valem sobre o curso inteiro, inclusive os últimos milímetros do bump?"
- "O braço de 80 mm é limite de fabricação ou de embalagem?"

## Q5. Riscos e o que não fazer

**[hipótese]**
- O candidato CONDICIONAL é uma lasca do espaço, não uma região: com ±0,5° de fabricação ele cai.
- O construtor com δ é meu e está fora do código do repositório.
- A busca foi local, a partir das sementes do benchmark.
- A cinemática não está validada.

O teste que derrubaria a recomendação: a busca com δ e MR(0) livres, com o STEP e o mesmo orçamento, terminar com 0 de 6
CONDICIONAL, ou o candidato perder o veredito com δ_fab ≥ 0,2°.

Não fazer:
- Usar a borda da tolerância de MR(0) como folga sem decisão da equipe.
- Aprovar com folga menor que a incerteza.
- Afrouxar a variação de MR antes de fixar a margem de curso.

**Recomendação em uma frase:** libere o ângulo de transmissão do push rod no estático e trate o MR(0) como faixa declarada. Com
isso a busca já acha posição sem violação, inclusive com o STEP. A decisão que de fato importa é a margem de fim de curso contra
o bump, e ela fica com a equipe, porque o problema está no fio da navalha por construção (BUMP = 61 × 1,40 − DROOP).

**Confiança:** média. A principal incerteza é a robustez: as folgas de 0,06 mm são muito menores que a tolerância de fabricação
provável, e a cinemática não está validada.
