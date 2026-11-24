# Revisão (lente: cético e verificação)

Conferi no código: `TOL_MR0 = 0.01` é constante (`varredura.py:58`); `avaliar_convergido` compara só estados e veredito, não valores
(`varredura.py:636-656`); a margem de curso nula entra como 0 e marca o item incompleto (`varredura.py:403-412`); o config não tem
nenhum item REGRA (13 META, 9 MARGEM_EQUIPE, 7 A_CONFIRMAR, 3 HIPOTESE), e EYE e STROKE são META; o push rod sai tangente a r1 no
estático (`mecanismo.py:9`).

## 1. Por letra
- **A.** Fraqueza: a tese do "triângulo" sai de 1 semente, 150 amostras e base pior que o benchmark (8,9 %), e o próprio teste de 5 %
  (Lmin ainda 0,7 mm curto) contradiz a ideia de que a variação de MR é parte do conflito. Forte: ordem de custo (Pareto sem CAD antes do CAD).
- **B.** Fraqueza: a correção por r2 deixa MR(0) em 1,417 a 1,4185, fora do ±0,01: não achou viável, só moveu a violação; 3 candidatos, n = 11.
  Forte: reavaliação no STEP mostra que o CAD não prende os quatro "a 0,7 mm" e que os pivôs ficam a 134 a 199 mm de tubo.
- **C.** Fraqueza: refinos partem das 6 finais (viés de região) e as margens são de 0,03 a 0,05 %. Forte: controle com o mesmo orçamento
  (0/6 × 2/6 × 3/6) que isola a parametrização, e confere com o STEP.
- **D.** Fraqueza: só 4 partidas × 260 avaliações; não testou a 8ª variável que propõe. Forte: os achados de verificação (convergência só por
  estado, Lmax com folga 0 por construção, escala da métrica "0,5 %"), e c4 mostra que a "única violação" é artefato da normalização (0,6 mm
  de curso ↔ ~8 mm de r2).
- **E.** Fraqueza: 1 CONDICIONAL em 4, com construtor fora do repositório e sensibilidade de ±0,75 pp por 0,5°. Forte: mecanismo físico
  (giro ≥ 44,8° com r2 = 80 mm; tangência desloca o U) e δ livre com controle δ = 0.
- **F.** Fraqueza: não responde ao conflito nem à precisão do veredito; momentos em N·m/kN são limite superior sem uso na decisão atual.
  Forte: regra do hospedeiro (R2), testável e que pode estar excluindo posições boas.
- **G.** Fraqueza: propõe 62,4 → 58,0 mm de bump como 1º relaxamento sem dado de pista, e diz que a hipótese do BRIEF "se confirma" ignorando
  r2 e a parametrização. Forte: separar REGRA/DADO_COMPONENTE/META e trazer V.3.1.1 (≥ 50 mm) como única regra de curso.

## 2. Ranking
RANKING: C > D > E > B > G > A > F

## 3. Divergências para o presidente
1. **Natureza do conflito.** A (e o BRIEF): variação de MR × curso. B, C, D, E e G: identidade curso = ∫dz/MR com BUMP = 61 × 1,40 − 23, logo
   "média harmônica ≥ MR(0) = 1,40". Posição: a identidade (cinco medições independentes, a 1e-3 mm); a variação de 4 % não é a restrição que prende.
2. **O que mexer primeiro.** B, C e E: tolerância de MR(0); D e G: margem de curso/bump; A: variação de MR. Posição: primeiro o que não é meta
   (δ e r2 livres, explorando o ±0,01 que o juiz já aceita), depois levar `TOL_MR0` ao config com origem, e declarar a margem de curso antes de
   qualquer relaxamento, porque ela piora o problema (D, E, G). O corte para 58 mm (G) espera o curso de roda exigido pela equipe.
3. **Viés de discretização.** D: ≤ 1,1e-4 com n = 25; E: 0,05 a 0,12 pp com 31 pontos; C: 0,02 pp. Depende do candidato; adotar a correção de D
   (convergência por valor, senão INDETERMINADO), que eu conferi ser necessária.
4. **Papel do CAD.** B, C e G: não prende; E: derruba 2 de 4 com δ livre; B e F: pivôs no ar. Posição: o CAD não explica o vazio nos pontos do
   benchmark, os 99 % da Fase I medem o volume da caixa, e construtibilidade (R1, d_max) é item novo a confirmar, não causa.
5. **Veredito com folga de µm.** Todos concordam que não se sustenta. Posição: publicar "não encontrada" e CONDICIONAL frágil com folga em mm;
   nenhum VIAVEL sem folga ≥ k·δ_fab medida, com C (o Lmax) também perturbado sem re-resolver (D).
