# Revisão anônima (lente: otimização e síntese de mecanismos)

Conferi no código: `TOL_MR0 = 0.01` é constante de `varredura.py:58` ("plano da fase 1"); `mecanismo.construir` põe o push rod
tangente ao círculo de r1 no estático e resolve r2 por brentq para MR(0) = alvo. As premissas de B, C, D e E sobre a construção
estão corretas.

## 1. Por letra

**A.** Fraqueza: o "triângulo" sai de n = 1 por variante, 150 amostras e máquina carregada; o resultado "MR 5 % deixa 0,7 mm" é
justamente o que C mostra ser artefato do n = 11. Diz que não precisa de mais precisão, e C, D e E desmentem isso. Forte: a ordem
"Pareto sem CAD antes de buscar com CAD" e as perguntas à equipe são úteis.

**B.** Fraqueza: a conclusão "o conflito é só MR(0)" se apoia em 3 candidatos com r2 varrido, sem rodar busca. O estreitamento da
caixa usa os mesmos 6 pontos que ele mesmo diz para não usar. Forte: reavaliou as 6 finais no STEP (4 sem colisão, folga de 8 a
130 mm), descartando (c). Também propôs resolver r2 por Lmin e pôr curto-circuito antes do CAD (60 % do tempo em `folga_segmento`).

**C.** Fraqueza: os refinos partem das finais do benchmark (viés de região, que ele mesmo declara), e as margens achadas são de
0,03 a 0,05 %. Forte: comparou parametrizações com controle de mesmo orçamento (A 0/6, B 2/6, C 3/6) e confirmou no STEP. Propôs
Fase II por centro de Chebyshev e mostrou que ninguém fixa a tolerância de MR(0). É a evidência mais limpa sobre (b).

**D.** Fraqueza: a 8ª variável (ângulo do push rod) fica como hipótese não rodada, e são só 4 partidas. Forte: mostrou que
"só o curso viola" é artefato da normalização por |limite| (escalado em mm: déficit de 0,07 a 0,13 mm, mas r2 em 86 a 90 mm). Achou
que a convergência compara só os estados e que C é feito com folga zero por construção. Melhor contribuição sobre precisão.

**E.** Fraqueza: o construtor com δ é dele, fora do repositório. O único CONDICIONAL com o STEP tem 0,057 mm de folga e cai com
±0,5°. Forte: identificou a causa de síntese (tangência no estático com 27 % do curso, que tira o U do lugar). Mediu o giro forçado
≥ 44,8° por r2 = 80 mm e rodou o δ livre contra um controle (0/4 com δ = 0, 1 CONDICIONAL com STEP). Deu custos em mm por unidade
de cada meta.

**F.** Fraqueza: fora do conflito central; não mexe na existência de posição cinemática, e o item 4 (regra do hospedeiro) não foi
testado. Forte: mediu que até as fixações das bandejas da v20 estão no ar (LCA_IN_F a 325 mm do tubo). Deu carga por kN de roda
sem inventar envelope; R1 e R2 são restrições bem desenhadas.

**G.** Fraqueza: propõe relaxar primeiro uma META (bump 62,4 → 58,0 mm) sem antes explorar os graus de construção (δ, MR(0)) que
dão viabilidade sem relaxar nada. A folga obtida (+0,41 a +0,47 mm) ainda fica abaixo de ±0,5 mm de fabricação. Forte: a origem
DADO_COMPONENTE para EYE/STROKE, a V.3.1.1 como restrição REGRA e o curso de roda como saída são reformulações corretas.

## 2. Ranking

RANKING: C > E > D > B > G > F > A

## 3. Divergências para o presidente

1. **Ordem de relaxamento.** G põe o bump primeiro, A a variação de MR, e C/E o MR(0) e o δ. Minha posição: primeiro liberar as
   escolhas de construção que não são metas (δ e o r2 resolvido pelo curso, e não pelo MR(0)), sem relaxar nada. Depois declarar
   em `config_T11.json`, com origem, a tolerância de MR(0) e a margem de fim de curso. A variação de MR fica por último.
2. **"Par" × "triângulo".** B e G dizem que basta MR(0) ou curso. A e D dizem que a fronteira tem três restrições (curso × variação
   × r2), e E mede r2 colado em 80 mm em 28 otimizações. Fico com a fronteira de três restrições. Decidir com o experimento de
   margem máxima em unidades físicas (D) com δ livre (E), em ≥ 30 partidas, e só aceitar s* estável entre orçamentos.
3. **Números de recuperação de MR(0).** D: com 1,41 recupera 0,43 mm, insuficiente. E: com 1,405 dá 3/4 CONDICIONAL. Não é
   contradição: as partidas diferem (finais do benchmark × refinadas, com déficit de 0,08 a 0,15 mm). O presidente deve exigir um
   rejulgamento único, nas mesmas partidas, pelo `avaliar_convergido`.
4. **Precisão.** A diz que a medida basta. Mas C e E mostraram que o n = 11 é otimista na borda (5,00 → 5,02 %; 4,0 → 4,05 %), e D
   mostrou que a convergência compara só os estados. Fico com C, D e E: o refino precisa de n maior perto da borda, e o critério
   tem de comparar valores, com INDETERMINADO quando |folga| < erro estimado.
5. **Veredito com margem de µm.** Todos os viáveis achados (C, E, G) têm folga de 0,03 a 0,5 mm. Minha posição: nenhum vira VIAVEL
   nem é apresentado como solução enquanto não houver δ_fab medido e a folga não for ≥ k·σ. O relatório deve dizer "fatia viável
   achada, não robusta", e não "posição achada".
