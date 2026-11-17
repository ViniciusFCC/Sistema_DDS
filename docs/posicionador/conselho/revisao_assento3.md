# Revisão anônima (rodada 2)

## 1. Avaliação por letra

**A**
- Erro mais grave: diz que o defeito central é "não ler o chassi", mas não mede nem a viabilidade nem o efeito das quase-igualdades. Entrega a formulação a outro assento sem testar nada. A ida e volta Fusion → STEP com corpos-datum fica sem teste.
- Ponto mais forte: dois achados novos e verificáveis. O primeiro é que o repositório já tem `kinematics_model.Corner` (76 checks) e o schema de hardpoints. O segundo é que a cápsula de tubo quadrado com a meia largura superestima a folga em até 5,18 mm contra o BRep, o que aprovaria o que bate.

**B**
- Erro mais grave: o LHS usa o avaliador original, com MR medido em 11 pontos (C e E mostram que a variação converge para cerca de 6,1 %) e folga ao aro no segmento errado. O "16/1000" conta só as quatro quase-igualdades, não a viabilidade completa. A prova de vazio vale com tolerância de até 50 mm e depende de |Pv_x| ≤ 150, que é escolha da equipe. O branch-and-bound é proposto sem teste.
- Ponto mais forte: dá uma explicação quantitativa para o 1,1 milhão sem solução (cerca de 1e-6 por amostra). Mede o ganho da eliminação por construção (de 0/3000 para 16/1000) e prova por limites, sem busca, que hoje não há par de nós possível.

**C**
- Erro mais grave: rebaixa a tese da formulação, mas a própria amostra dele (0 viáveis; 28 sem MR e sem curso) a confirma. O gerador fica sem especificação.
- Ponto mais forte: corrige os números de partida (variação do MR de 4,0 → 5,19 → 6,08 % com 11, 25 e 201 pontos), acha o bug do aro e mostra que a v20 não resiste a ±1 mm. Propõe gerador separado do verificador, com resolução convergida e Monte Carlo de tolerâncias. É o que mais serve à exigência de que o aprovado seja válido.

**D**
- Erro mais grave: "congelar os hardpoints a partir de julho de 2027" coincide com a data da competição, então o cronograma está incoerente. As 14 soluções sem o limite de 4 % usam a mesma medida de MR em 11 pontos.
- Ponto mais forte: com o MR imposto por construção, mostra que o conflito é MR ≤ 4 % × curso inteiro × tubo ao FH, ou seja, decisão da equipe. Dá um teste falsificável barato: Nelder-Mead com 50 sementes, sem o tubo.

**E**
- Erro mais grave: o eixo a 74° e o mínimo de 66° saem do `kinlib`, que não foi validado e cuja implementação de primeira ordem não está exposta. A recomendação inteira depende disso.
- Ponto mais forte: acha um conflito de conceito que nenhuma busca resolve, entre "mesmo plano" e "amortecedor a ≤ 30° de X". Mostra também que o MR é regressivo no bump (1,384 → 1,468) e que os 90° no estático viram 47° no fim do curso.

**F**
- Erro mais grave: a faixa de 300 a 800 MPa extrapola a carga de outro carro, e o pórtico não foi validado contra Pynite nem FEA. A ride rate admissível depende de um p ilustrativo.
- Ponto mais forte: mostra que o tubo Q–E da v20 é estruturalmente inviável (145 a 393 MPa por kN). Propõe matriz de influência por superposição, o que deixa a tensão no laço a custo de produto de matrizes.

**G**
- Erro mais grave: "parte do batia no gabarito pode ser artefato" é hipótese que C enfraquece (o rocker da v20 em |Y| > 175 tem 30,6 mm de margem). O δ de fabricação não tem valor.
- Ponto mais forte: X_FIM = 350 implica pedal em X 450, o que deixa 32 mm até o FBH, contra os 25 mm de folga que o F.8.6.3 exige. Mostra também que, com δ = 0,5 mm, 0 % das amostras cumprem, e classifica cada restrição por procedência (regra, margem, preferência).

## 2. Ranking

RANKING: C > E > B > A > F > G > D

## 3. Divergências para o presidente decidir

1. **Por que a força bruta falhou: formulação (B, D) ou falta de nós (C, F)?**
   - Posição: as duas causas são reais e independentes.
   - Com os nós de hoje, o vazio está provado por limites (B).
   - Sem exigir nó, as quase-igualdades sozinhas já dão cerca de 0 (B, C e D).
   - Ação: a caixa dianteira desenhada pelo chassi e a eliminação por construção, em paralelo.
2. **Decidir o conceito antes da busca (E) ou deixar a busca enumerar (B, D)?**
   - Posição: o conceito entra como variável discreta enumerada, mas a escolha é da equipe, com a frente de Pareto de cada conceito à vista.
   - Antes disso, conferir no OptimumK o conflito de 74° apontado por E.
3. **Qual cinemática usar: `kinlib` (D) ou `Corner` do repositório (A)?**
   - Posição: o certificador usa o modelo testado do repositório, depois de comparado com o `kinlib` nos 25 pontos da v20 e com a REFERENCE.
   - O `kinlib` fica só como conferência cruzada.
4. **Robustez a tolerâncias: restrição dura (C, E, G) ou só margem (B, D)?**
   - Posição: a busca usa margem.
   - O certificador exige viabilidade em toda a caixa ±δ, com o curso convergido em resolução.
   - O δ é medido pela equipe, nunca inventado.
5. **Estrutura no laço (F) ou só nos finalistas (D)?**
   - Posição: no laço, pela matriz de influência linear, quando o envelope de cargas do T11 existir.
   - Até lá, tensão e distância ao nó saem só no relatório, sem valor de corte.
   - A cápsula usa o raio envolvente, como A mediu.
