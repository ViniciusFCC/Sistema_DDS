# Revisão (lente: regulamento e manufatura)

Conferi na fonte: `varredura.py:58` (`TOL_MR0 = 0.01`, "plano da fase 1", fora da configuração); `config_T11.json` não tem nenhum
item com origem REGRA, e EYE/STROKE do DNM estão como META com fonte no script, não no catálogo; V.3.1.1 (≥ 50 mm de curso útil com
piloto sentado) está em `pesquisa/relatorio-regras.md` l. 95 e não é restrição do juiz.

## 1. Por letra

- **A.** Fraqueza: o experimento parte de uma busca curta (base com 8,9 % de violação, n = 1 por variante). Com isso o "triângulo" e
  o "MR 5 % não resolve" não se comparam com as finais do benchmark, que estão a 0,5 %. Forte: a ordem de gasto, com o mapa sem CAD
  antes do CAD, e a pergunta sobre a validação no OptimumKinematics.
- **B.** Fraqueza: os pivôs "no ar", a 18 a 28 cm de nó, viram restrição com L_max sem fonte; e os MR(0) de 1,417 a 1,4185 ficam
  fora até de ±0,01, sem novo refino. Forte: reavaliou no STEP as 6 finais (folga de 8 a 130 mm); o CAD não é o gargalo. Também
  achou o `TOL_MR0` sem origem e propõe o cache da cena para o `.exe`.
- **C.** Fraqueza: os 5/12 sem violação partem das 6 finais (viés de região) e têm margem de 0,03 a 0,05 %, sem tolerância de
  fabricação. Forte: comparou as parametrizações com controle no mesmo orçamento (0/6, 2/6, 3/6), conferiu no STEP e mediu a tabela
  de relaxamento com perturbação.
- **D.** Fraqueza: não achou posição; o "8ª variável" fica como hipótese. Forte: o erro de n (1,1e-4 com n = 25) e a convergência
  por estado, não por valor. Viu que Lmax é igual por construção (fio de navalha na fabricação do olhal C) e que a métrica escalar
  depende da escala (0,7 mm = 0,46 % ou 1,15 %).
- **E.** Fraqueza: o construtor com δ é externo ao repositório. O CONDICIONAL tem 0,057 mm de folga e ±0,5° em φB move a variação
  em ±0,75 pp, uma lasca que não se fabrica. Forte: é a explicação física do U (tangência no estático, giro ≥ 44,8° com r2 = 80) e
  o único CONDICIONAL com STEP com controle δ = 0; os custos estão em mm por pp.
- **F.** Fraqueza: não responde ao conflito MR × curso. Os 205 a 247 N·m/kN são limite superior (carga toda transversal) e o item 4
  (o hospedeiro excluir o nó) não foi testado. Forte: a manufatura de verdade. A LCA_IN_F a 325 mm de tubo, as arestas-fantasma,
  a regra do hospedeiro e o push rod a cerca de 1,5 kN/kN, sem carga inventada.
- **G.** Fraqueza: o caso de 58,0 mm de bump com 2 mm de margem é uma reavaliação de 6 geometrias fixas, sem STEP. "Aumenta a
  segurança" vale para o batente, não para o desempenho. Forte: separa REGRA, DADO_COMPONENTE e META e põe a V.3.1.1 como piso
  explícito. É a única proposta que troca folga de µm por margem física declarada (+0,41 a +0,47 mm além de 2 mm de batente).

## 2. Ranking

RANKING: G > E > C > D > B > F > A

## 3. Divergências para o presidente

1. **Usar a faixa ±0,01 de MR(0) como grau livre.** C e E a usam (E: 1,405 dá 3/4 CONDICIONAL); B mostra que é constante de
   código sem origem. Posição: nada de usar a borda antes de levar `TOL_MR0` para `config_T11.json` com origem (META, a confirmar
   com a equipe). Os números de D (1,41 não basta), E (1,405 basta) e B (1,417) não se contradizem: partem de pontos refinados
   diferentes. Todos dão cerca de 0,44 mm por 0,01.
2. **Reduzir o bump.** D e E dizem "não relaxar o bump para passar"; G propõe 62,4 → 58,0 mm. Posição: com G, desde que venha
   amarrado à margem de fim de curso (o problema fica mais difícil, como D diz, mas a margem passa a ser real) e com o piso de 50 mm
   da V.3.1.1 verificado com piloto sentado.
3. **EYE/STROKE.** Hoje são META; G diz DADO_COMPONENTE. Posição: DADO_COMPONENTE, duro e sujeito à folha do DNM (A_CONFIRMAR).
4. **Estrutura.** B quer restrição dura com L_max; F quer R1 só "tubo existente ou aresta-fantasma" com d_max A_CONFIRMAR
   (NAO_VERIFICAVEL até lá), mais a regra do hospedeiro, sem o nó como limite. Posição: F.
5. **Critério de aprovação.** Todos concordam que folga de 0,03 a 0,06 mm não vale. Posição: o certificador exige folga ≥ k·σ_fab,
   com σ_fab medido e propagado também ao olhal C (D) e por jacobiano (E). Até haver σ_fab, o veredito máximo é CONDICIONAL com o
   aviso "margem < δ" (G).
