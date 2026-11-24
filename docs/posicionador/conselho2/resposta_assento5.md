# Resposta: verificação, evidência contra e incerteza do veredito

Scripts e saídas em `docs/posicionador/conselho2/trabalho_assento5/` (c1 a c4; config original intacta, cópias `cfg_*.json`).

## Q1. Onde se perde precisão

**A medida não é o problema; a tradução dela em veredito é.**
- [resultado de código, c3] O erro de discretização é pequeno. A variação de MR com n = 25 difere da de n = 801 em no máximo 1,1e-4 (com n = 11, até 7,9e-4). O comprimento mínimo do amortecedor não muda com n (0,0 µm), porque o mínimo cai na ponta do curso. O viés tem sinal fixo: max/min de amostras subestima a variação, então ele empurra para "passa".
- [fato de fonte, `varredura.py` `avaliar_convergido`] O critério de convergência compara só os **estados** (OK/VIOLADA), não os valores. Um candidato a 3,99 % em n = 50 converge mesmo que o valor verdadeiro esteja do outro lado. Correção: exigir |Δvalor| < tolerância declarada e uma folga maior que o erro estimado, senão o veredito sai INDETERMINADO.
- [resultado de código, c1] O comprimento máximo é satisfeito **por construção**, com folga 0,000 mm (C é posto a 210 mm no droop). O teste de robustez do benchmark re-resolve C a cada perturbação, por isso nunca mostra esse fio de navalha. Na peça fabricada, o C errado em ±0,5 mm viola o limite em metade dos casos [inferência].
- [cálculo] **A métrica "0,5 % do limite" depende da escala.** A violação é normalizada por |limite|. Por isso 0,7 mm abaixo de 149 mm vale 0,46 %, mas o mesmo 0,7 mm vale 1,15 % do curso de 61 mm e "0,7 mm de batente inexistente" em termos físicos. O "≈100 vezes mais perto" do benchmark muda com a escala. A ordem entre as ferramentas não deve mudar (o script fica 2,2 p.p. acima no MR), mas o fator, sim. Proposta: reportar cada violação na unidade física e em fração da faixa útil (curso, faixa do braço), nunca um escalar único.

## Q2. Por que não há posição viável

**(a) Conflito de metas: confirmado e mais preciso do que se dizia.**
- [resultado de código, c1] Vale a identidade: curso usado = ∫dz/MR. O integral bate com Lmax − Lmin a 1e-3 mm nos 6 casos.
- [fato de fonte, `config_T11.json`] O bump de 62,4 mm foi **derivado** de "61 mm × MR" supondo MR constante, e 23 + 62,4 = 85,4 = 61 × 1,40.
- [cálculo] Com margem de curso zero, a restrição de curso equivale então a "média harmônica do MR no curso ≥ 1,40 = MR(0)". Nenhum MR constante a cumpre com folga: ele dá exatamente 149,000 mm.
- [resultado de código, c1] Todas as melhores curvas têm o mínimo do MR em dz ≈ +40 mm, com média harmônica 1,383 a 1,389. O conflito, portanto, não é "variação ≤ 4 %" contra o curso. É a **forma** da curva (o MR(0) não pode ficar acima da sua média harmônica) somada a uma meta de curso de roda que foi calculada de modo circular.
- [resultado de código, c2] Os três relaxamentos de teste têm efeitos diferentes:
  - MR(0) construído em 1,41, que já cabe na tolerância ±0,01 aceita pelo juiz mas que a construção não explora, recupera cerca de 0,43 mm e não basta.
  - Bump de 61,4 mm deixa 3 de 4 CONDICIONAL, mas com folga de **+0,03 mm**: viável no papel e frágil na prática.
  - Margem de curso de 2 mm (valor ilustrativo; hoje A_CONFIRMAR e tratado como 0) deixa os 4 a −2,7 mm.

  Quando a equipe der a margem real, o problema fica mais difícil, não mais fácil.

**(b) A busca e a escala do objetivo enviesam o diagnóstico.**
- [resultado de código, c4] Refinei os mesmos 4 pontos com o comprimento mínimo escalado em mm (260 avaliações, sem relaxar nada). O déficit de curso cai para 0,07 a 0,13 mm, mas o r2 sobe para 86 a 90 mm (limite 80) e a variação vai a 4,03 a 4,06 %.
- [inferência] "A única restrição violada é o curso" é um artefato da normalização. A fronteira real é a três: variação de MR × curso × r2 ≤ 80 mm. Cerca de 0,6 mm de curso troca por cerca de 8 mm de r2.
- [fato de fonte, `busca.py`] A fração de 99 % de violação de MR na Fase I com STEP mede a densidade de amostras aleatórias, não o conflito. Não deve ser lida como prova.

**(c) CAD e (d) modelo.**
- [fato de fonte, `METODOLOGIA.md` §8] O STEP não tem REF_ nem manga, freio ou pinça, e a cinemática é NOT_VALIDATED.
- [inferência] Margens de 0,03 a 0,7 mm ficam abaixo da incerteza declarada ("abaixo de 1 mm") e de qualquer δ de fabricação. Com folgas desse tamanho, nenhum veredito, VIAVEL ou INVIAVEL, se sustenta sem a comparação com o OptimumKinematics.

**Experimento que decide:** um problema reduzido, só com as restrições de cinemática e sem CAD. Maximizar a menor folga física mínima s = min(folga_i / escala_física_i), com multistart (≥ 30 partidas) e orçamento crescente. A resposta só vale se s* se estabilizar entre orçamentos. Se s* < 0 de forma estável, é conflito; se s* > 0, a busca falhou.

## Q3. Desenho que aumenta a chance de achar posições

1. [inferência] Usar a identidade ∫dz/MR como restrição explícita e um alvo de forma da curva (mínimo do MR perto de dz = 0, com tendência de subida no bump), em vez de esperar que o sorteio a acerte.
2. [inferência] Libertar dois graus que a construção fixa: MR(0) dentro de ±0,01 e o ângulo do push rod com r1 no estático (hoje sempre 90°, por tangência). Este último põe o extremo do braço de alavanca no estático e pode impedir a curva em "U" centrada. É uma hipótese a testar com uma 8ª variável.
3. Trocar "violação máxima normalizada por |limite|" por uma **maximização da margem mínima em unidades físicas** declaradas e, em seguida, por um Pareto explícito (curso × variação de MR × r2) a partir das mesmas partidas.
4. O certificador separado (decisão do conselho anterior) passa a exigir folga ≥ k·σ: σ vem da propagação de δ, aplicada **também** ao C e não re-resolvida. Hoje δ é sintético; o valor real é "a medir".

## Q4. Mapa de conflitos e ordem proposta (decisão da equipe)

[resultado de código, c2 e c4] Custos medidos nos 4 melhores, sem CAD:
- curso: 0,68 a 0,74 mm;
- ou r2: +6 a +10 mm acima de 80, com a variação em cerca de 4,05 %;
- MR(0) = 1,41 vale cerca de 0,43 mm.

Ordem que proponho (proposta, não ação):
1. Definir o curso de roda como requisito próprio, e não como 61 × 1,40.
2. Declarar a margem de curso (batente), que hoje é zero por omissão.
3. Só depois disso discutir r2 máximo ou a variação de 4 %.

Perguntas para a equipe:
- "O bump de 62,4 mm é requisito de curso de roda ou só consequência de 61 × 1,40? Se for requisito, de onde vem?"
- "Quantos mm de curso do amortecedor ficam reservados ao batente?"
- "O r2 de até 80 mm é limite de pacote ou de massa? Aceita 85 a 90 mm?"
- "Que forma de curva de MR vocês querem no bump (subindo ou descendo)?"

## Q5. Riscos e testes que derrubam

- [inferência] Derruba "a posição viável não existe": um ponto com s > 0 estável no experimento de Q2, ou a 8ª variável (ângulo do push rod) produzindo média harmônica ≥ 1,40 com a variação ≤ 4 % e r2 ≤ 80. Só tenho 4 partidas × 260 avaliações. A afirmação tem de ficar "não encontrada", nunca "não existe".
- Derruba a minha conclusão sobre a forma da curva: se a identidade ∫dz/MR falhar no OptimumKinematics, isto é, se o MR local do `kinematics_model` não for dLs/dz da referência.
- **Não fazer:**
  - publicar "viável" com folgas de 0,03 mm;
  - relaxar o bump para "fazer passar";
  - continuar a reportar uma violação escalar única como medida de proximidade;
  - deixar a margem de curso nula valer como se fosse um dado.

**Recomendação em uma frase:** tratem o veredito como "não encontrado", não como "não existe". O conflito real está entre a forma da curva de MR (média harmônica ≥ MR(0)), um curso de roda calculado de modo circular e o r2 ≤ 80 mm. Ele aparece com clareza quando cada violação é medida em unidades físicas e quando o veredito exige uma folga maior que a incerteza da medida e da fabricação.

**Confiança:** média. A identidade e os custos são medidos e reproduzíveis. A principal incerteza é se a parametrização (push rod tangente ao rocker no estático, MR(0) fixo) esconde curvas em "U" viáveis, e isso só o experimento de margem máxima com a 8ª variável decide.
