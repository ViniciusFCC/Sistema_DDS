# Revisão anônima, rodada 2

## 1. Avaliação por letra

**A**
- Mais grave: aprovar só pelo BRep não cobre regra (gabarito, escudo, AIP) nem tolerância de fabricação. "Verificador independente" fica reduzido a "folga exata".
- Mais forte: três achados medidos que ninguém mais tem:
  - a cápsula com meia largura superestima a folga em até 5,18 mm, isto é, aprova o que bate;
  - o repositório já tem `kinematics_model.Corner` e `hardpoints.py`, testados;
  - o STEP não traz geometria de construção (0 `GEOMETRIC_CURVE_SET`), o que derruba GEO §8.2.

**B**
- Mais grave: o "vazio provado" depende de limites arbitrários do script (|Pv_x| ≤ 150) e só dos nós de hoje. Prova pouco sobre o problema real, em que a caixa dianteira nem existe. Regra e manufatura quase não aparecem.
- Mais forte: evidência quantitativa de que a formulação estrangula o espaço. As quase-igualdades juntas passam em 0 de 3000 amostras e, por construção, em 16 de 1000. Além disso, 23 + 62,4 = 61 × 1,40 mostra a igualdade escondida no curso.

**C**
- Mais grave: pouco sobre como gerar candidatos e usar o CAD.
- Mais forte, alinhado com o "o que aprova tem de ser válido":
  - a variação do MR converge em cerca de 6,1 %, não 5,2 %;
  - a folga ao aro era medida no segmento errado;
  - a v20 viola cada restrição em cerca de metade das amostras perturbadas;
  - arquitetura gerador × verificador, com convergência de resolução e certificado do que não foi modelado.

**D**
- Mais grave: "congela os hardpoints numa data a partir de julho de 2027". A competição é de 28/07 a 01/08/2027, então isso é incoerente. A conta do teste (≈ 3,5 h num núcleo) contradiz o "menos de uma hora". E manter o `kinlib`/`avaliar` sem notar o erro do aro é arriscado.
- Mais forte: aponta que "o script da suspensão desenha um tubo do chassi" é o defeito de fronteira entre as subequipes. O LHS com MR por construção dá 14 soluções viáveis se a variação de MR for relaxada, o que deixa a decisão na mão da equipe.

**E**
- Mais grave: o eixo "que zera a carga axial", a 74° do eixo da v20, é aproximação de 1ª ordem num `kinlib` não validado. Sustenta uma "troca de conceito" com força maior do que a evidência dá.
- Mais forte: os números são densos (6,1 %, MR regressivo, 47° amortecedor–braço no bump) e é a única resposta a mostrar que coplanaridade e "amortecedor para a frente" podem ser incompatíveis. Isso é decisão de conceito anterior a qualquer busca.

**F**
- Mais grave: σ de 300 a 800 MPa usa carga de outro carro e pontas idealizadas num tubo cuja ponta E está no ar. Serve como ordem de grandeza, não como veredito.
- Mais forte: troca "distância ao nó" por σ e Ke ≥ RR(1−p)/p. Propõe uma matriz de influência barata no laço e o princípio de fechar pivô e olhal no mesmo subconjunto triangulado.

**G**
- Mais grave: não detectou o erro do aro e o repetiu ("só roda reta"). Superestima o gabarito para o rocker: com |Y| > 175, a margem é de 30,6 mm (C). As inferências sobre X_FIM e sobre o corredor N11–N04 são especulativas.
- Mais forte: é a única resposta a etiquetar as restrições por procedência (regra e versão, margem, preferência). Também é a única com o "kit de fixação" (cisalhamento duplo, acesso de chave e tocha, SES) e com a robustez medida: com ±0,5 mm, cerca de 50 % das amostras pedem mais de 61 mm de curso.

## 2. Ranking

RANKING: B > C > A > E > F > G > D

## 3. Divergências para o presidente

1. **Avaliador: manter `kinlib`/`avaliar` (D) ou migrar para `kinematics_model.Corner` (A)?** Migrar, depois de comparar `kinlib`, `Corner` e OptimumK na v20 (C, E). O erro do aro mostra o custo de um código sem teste.
2. **O vazio vem da formulação (B, D) ou da falta de nós (C, F)?** Dos dois. Rodar a fase I com o CAD atual mais os tubos fantasmas regulatórios (F.6.2.3) separa as duas causas, e os ganhos de B mostram que a reformulação é necessária de qualquer forma.
3. **Esforço no laço (F) ou só nos finalistas (D)?** σ e Ke como restrição dura no laço, com o pórtico linear, assim que os casos de carga do T11 existirem. Até lá, no relatório. FEA só nos finalistas. A distância ao nó fica só no relatório: a R27 não a exige.
4. **Conceito decidido pela equipe (E) ou explorado pelo otimizador?** A equipe decide. O script enumera os conceitos A e B como discretos e mostra a carga fora do plano de cada um.
5. **Modelo de obstáculo e gabarito.** Cápsula com raio envolvente, isto é, meia-diagonal mais 0,2 mm (A). O gabarito entra com altura livre mesmo que não pese para o rocker, porque cremalheira, coluna e pés dividem o espaço. Aprovação só com robustez à tolerância medida (C, E, G).
