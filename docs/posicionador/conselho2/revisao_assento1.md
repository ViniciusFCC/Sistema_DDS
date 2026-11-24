# Revisão (lente: cinemática de suspensão)

Conferido no código: `mecanismo.py` l. 9-16 (push rod tangente a r1 no estático; r2 por brentq para MR(0) = alvo; C a EYE no
droop), `varredura.py` l. 58 (`TOL_MR0` = 0,01, "plano da fase 1") e `config_T11.json` (BUMP = "61 mm × MR"). O limite
2·asin(61/160) = 44,8° de E confere [cálculo]. Não rodei busca nova.

## 1. Por letra

- **A.** Fraqueza: o experimento parte de uma base ruim (violação 8,9 % contra 0,5 % do benchmark, 150 amostras, 1 semente), então o "triângulo" que sai dele mede mais a busca curta que o conflito. Forte: a ordem "mapa sem CAD antes do CAD" e uma pergunta à equipe por limite.
- **B.** Fraqueza: o "custo" é dado como MR(0) = 1,417, que fica fora da tolerância ±0,01. O resultado é uma restrição violada trocada por outra, não uma posição viável. Forte: mostra que as 4 soluções "a 0,7 mm" passam no STEP (folgas de 8 a 176 mm), que os pivôs ficam a 179-281 mm do nó mais próximo e que a avaliação custa 0,12 s sem CAD e 0,38 s com CAD.
- **C.** Fraqueza: as sementes são as 6 finais do benchmark, o que dá viés de região, e as margens são de µm (0,03-0,05 %). Forte: o melhor experimento de parametrização, com controle no mesmo orçamento (0/6 contra 2/6 e 3/6 CONDICIONAL, com o STEP); a tabela de relaxamentos com 40 perturbações; e o achado de que n = 11 é otimista na fronteira (5,00 contra 5,02 %).
- **D.** Fraqueza: as 4 partidas × 260 avaliações não sustentam a fronteira "0,6 mm ↔ 8 mm de r2" como geral. Forte: a convergência compara estados e não valores; o erro de discretização foi medido (1,1e-4 em n = 25); a normalização por |limite| distorce o "≈100×"; o Lmax é satisfeito a 0,000 mm por construção.
- **E.** Fraqueza: o construtor com δ fica fora do repositório, o caso CONDICIONAL é um só, a folga é de 0,057 mm e a sensibilidade é de ±0,75 pp por 0,5°. Forte: é a melhor explicação cinemática. Ela junta ∫dz/MR, o giro mínimo de 44,8° com r2 colado em 80 e a tangência no estático, que desloca as fases γ1 e γ2 para o bump (curva em U fora do lugar). O controle δ = 0 dá 0/4, e δ livre dá CONDICIONAL também com o STEP.
- **F.** Fraqueza: fica quase toda fora do conflito pedido, e o item 4 (regra do hospedeiro) não foi testado. Forte: as cargas por kN são medidas (push rod de 1,5 a 2,0 kN/kN; 205 a 247 N·m/kN no SPRING_CHASSIS) sem inventar envelope.
- **G.** Fraqueza: o bump reduzido é testado só no rejulgamento com a geometria fixa, sem refazer a busca nem usar o CAD. Forte: classifica EYE e STROKE como DADO_COMPONENTE e não como META; usa V.3.1.1 (≥ 50 mm) como piso; e dá um cenário concreto (2 mm de margem com bump de 58,0 mm: 4/6, com folga de 0,41 a 0,47 mm).

## 2. Ranking

RANKING: E > C > D > B > G > F > A

## 3. Divergências para o presidente

1. **Causa principal: meta ou parametrização.** Todas confirmam a identidade ∫dz/MR e o BUMP = 61 × 1,40 − 23, que deixam o problema com margem zero por construção. As respostas divergem sobre o que vem primeiro:
   - B, C e E: a construção (MR(0) cravado e tangência).
   - G e A: as metas.

   Posição: liberar primeiro os graus de construção (δ e MR(0) dentro de ±0,01), que não relaxam meta nenhuma. Antes disso, rodar o experimento de C e E com a busca do repositório e controle (6 sementes, com o STEP).
2. **Custo do MR(0).** Os números são compatíveis (D: 1,41 recupera ≈ 0,43 mm; E: 0,44 mm por 0,01; B: precisa de 1,417 partindo de déficit de 0,7 mm). Só fecha dentro de ±0,01 depois de re-otimizar. Posição: a tolerância de 0,01 é constante do código, sem origem, e tem de ir para a configuração como A_CONFIRMAR (C e B concordam).
3. **"A única violada é o Lmin".** D diz que isso é artefato da normalização e que a fronteira real é a três, com r2. B e G dizem que só o Lmin está ativo. Posição: D e E estão certos que r2 = 80 é ativo escondido, porque o giro de 44,8° obriga. Reportar cada violação em unidade física.
4. **Ordem de relaxamento.** Há três propostas:
   - G: bump com margem de fim de curso primeiro.
   - C: tolerância de MR(0) primeiro.
   - D e E: requisito de curso e margem antes de r2 e da variação.

   Posição: todas concordam em deixar a variação de MR por último. Depois da construção, a pergunta decisiva à equipe é a margem de fim de curso, porque cada 1 mm dela custa ≈ 1,39 mm de bump (G e E).
5. **Veredito com folga de µm.** C, D, E e G mostram candidatos "sem violação" com folga de 0,03 a 0,06 mm, abaixo da tolerância provável de fabricação. Posição: nenhum vira VIAVEL. O certificador exige folga ≥ k·σ (σ do jacobiano × δ_fab, a medir) e convergência por valor (D), e não só por estado.
