# Resposta: estrutura do chassi como requisito de validade da posição

Rótulos: [fonte] arquivo citado; [código] rodei (scripts e saídas em `trabalho_<autor>/`); [cálculo]; [inferência]; [hipótese].

## Q2 (a parte estrutural): por que "não há posição viável" também é um problema de estrutura

1. **[fonte] O vão dianteiro do CAD está praticamente vazio.** `relatorio-geo.md` (linha 82) diz que entre o FH (X −202) e o FBH (X 495) só há os dois `braceFBH`, no alto. **[código]** `nos.py` confirma: 32 tubos e 28 nós no STEP; no vão, nós só nos dois hoops (6 por lado). Não existe tubo lateral baixo FH→FBH.
2. **[código] Isso vale para a suspensão inteira, não só para a atuação.** Medi, na v20, a distância de cada fixação ao tubo mais próximo: `LCA_IN_F` 325 mm e `UCA_IN_F` 299 mm (só o FH está perto); `ROCKER_AXIS_A` 147 mm, `ROCKER_AXIS_B` 155 mm, `SPRING_CHASSIS` 97 mm (braceFBH). Só os pontos traseiros (`LCA_IN_R`, `UCA_IN_R`, 14 e 23 mm) caem no FH. Então "nó disponível" não é um dado do CAD atual: é uma saída do projeto conjunto chassi + suspensão. O posicionador trata o chassi como obstáculo fixo e a "preferência por nó" só pode escolher entre os nós de hoje (3 por lado ao alcance de X ≤ 150 mm).
3. **[código] Com arestas-fantasma entre nós existentes (8 arestas FH→FBH do lado esquerdo, hipótese de topologia), o mesmo ponto fica perto de tubo.** `LCA_IN_F` cai de 325 para 33 mm; `UCA_IN_F` para 79 mm; `ROCKER_AXIS_B` de 155 para 129 mm; nos candidatos do posicionador `ROCKER_AXIS_A` chega a 15 mm (semente 4) e `ROCKER_AXIS_B` a 41 mm (semente 1). O tubo lateral baixo que falta é a aresta que a própria `LCA_IN_F` pede (33 mm).
4. **[inferência, a testar] A exigência de folga do pivô pode excluir justo os nós.** `r_pivo_m` = 20 mm (MARGEM_EQUIPE, `config_T11.json`) contra tubo de meia-seção 12,5 mm exige centro a ≥ 32,5 mm da linha do tubo; um ponto "no nó" sempre colide com o próprio hospedeiro. Nas buscas sem CAD, `SPRING_CHASSIS` caiu a 14 mm da linha de tubo em 2 de 6 sementes: com o STEP essas posições seriam rejeitadas por colisão com o tubo que deveria sustentá-las. Teste: contar vóxeis livres do `Mapa` a menos de 40 mm de cada nó; se for zero, falta a regra do hospedeiro (abaixo).

Conclusão de classe: a estrutura é (c) CAD incompleto/hipótese, e não é a causa do conflito de MR × curso. Nada do que segue relaxa o MR; serve para que uma posição que passe seja válida de verdade.

## Q3: o que exigir e medir (desenho concreto)

**Princípio: estrutura vira medida e objetivo; só duas coisas viram restrição dura, e ambas sem dado de carga inventado.**

- **R1 (dura, topologia).** Cada fixação (`ROCKER_AXIS_A/B`, `SPRING_CHASSIS`, e os 4 pontos de bandeja) deve estar a ≤ d_max do conjunto "tubos existentes ∪ arestas-fantasma entre nós existentes". d_max = A_CONFIRMAR (a equipe); enquanto nulo, a restrição fica NAO_VERIFICAVEL, nunca OK. Só rejeita posição no meio do ar, e o conjunto de fantasmas é finito (8 arestas por lado), então não trava a busca.
- **R2 (dura, geométrica).** Regra do hospedeiro: o olhal/pivô pode tocar o tubo que o sustenta; a folga `r_pivo`/`r_prod` vale contra todo outro obstáculo. Sem ela, a Fase I tem viés contra as melhores posições estruturais.
- **Objetivos (Pareto, não restrição):** (i) comprimento total de tubo a adicionar (soma das distâncias às arestas escolhidas, mm); (ii) nº de tubos novos; (iii) braço de flexão por fixação. O relatório lista "tubos a adicionar" por candidato, com a aresta-fantasma escolhida; é a entrega que a equipe pode levar ao chassi.
- **Cargas sem dado do T11: em forma fechada, por kN de carga vertical na roda.** [cálculo] Trabalho virtual com MR = 1,4 dá F_mola = 1,4 kN/kN (convenção MR = Δroda/Δmola do CLAUDE.md). [código] Equilíbrio de momento no eixo do rocker na v20: push rod 1,46 kN/kN e reação no pivô 2,49 kN/kN; nos candidatos do posicionador, push rod 1,5 a 2,0 e pivô 1,95 a 2,76. Isto concorda com a "regra de bolso" de ≈150 % do push rod em `pesquisa/relatorio-equipes.md` (compressão axial; o sinal negativo do meu script é convenção minha, só a magnitude vale). Momento de flexão no tubo (viga biapoiada nos nós, carga toda transversal, portanto limite superior): em `SPRING_CHASSIS`, **205 a 247 N·m por kN** em 8 de 8 candidatos e na v20 (246), porque o olhal cai no meio de um vão de 705 mm. Tensão exige seção e espessura do tubo (A_CONFIRMAR); então só reporto N·m/kN, nunca MPa nem coeficiente de segurança. O envelope de carga do T11 continua pendente (SINTESE, "Fica com a equipe").
- **Por que não tornar o nó restrição dura:** [fonte] `relatorio-equipes.md` (JUIZ DesignJudges): fixação em nó é ideal, "muitos se amarram em nós" com geometria ruim, e nenhuma fonte dá distância numérica. Discordo de elevar a distância ao nó a limite; concordo com a SINTESE de usá-la como relatório. O que cobra é a existência de caminho de carga (R1) e a flexão (objetivo).

## Q4: conflitos que a estrutura adiciona (a medir)

Pares a medir na Fase I já com R1/R2: (MR ≤ 4 % × curso 61 mm) segue sendo o conflito dominante [fonte, benchmark]; novos: (X ≤ 150 mm da caixa × tubo a adicionar curto) e (`x_max_olhal` 400 mm × FBH em 495 mm: olhal a ≥ 95 mm do hoop dianteiro). Pergunta à equipe: "Aceitam adicionar um tubo lateral baixo FH→FBH e, se sim, qual comprimento máximo de tubo novo por fixação (d_max) e qual diâmetro/espessura de tubo vale para o cálculo de flexão?"

## Q1/Q5: riscos, o que não fazer, teste mínimo

- **Não fazer:** declarar viável por distância a nó; usar MPa sem seção; aprovar com carga inventada; transformar fantasmas em "chassi do T11" (são hipótese de topologia, rotular).
- **Risco:** o limite superior de flexão (carga toda transversal) superestima; um número maior que o real não derruba a decisão, mas não serve para dimensionar. A transformação STEP→carro é HIPOTESE (±0,55 mm), irrelevante na escala de dezenas de mm usada aqui.
- **Teste que derruba a recomendação:** se, com R2 ativo e o STEP, a Fase I não mudar a fração de amostras sem colisão perto dos tubos (vóxeis livres < 40 mm de nó permanecem não nulos hoje), o item 4 está errado e R2 é desnecessário. Se R1 com d_max razoável não rejeitar nenhum dos 8 candidatos já medidos, R1 só informa.

## Recomendação em uma frase
Exigir da estrutura apenas a existência de um caminho de carga alcançável (tubo existente ou aresta-fantasma entre nós existentes, com d_max a confirmar) e a regra do hospedeiro, e reportar "tubos a adicionar" e N·m por kN de roda como objetivos, sem inventar carga nem transformar nó em limite duro.

## Confiança e principal incerteza
Média. Os números de distância e carga por kN foram rodados e são reprodutíveis; a incerteza principal é a topologia do chassi final (as arestas-fantasma são hipótese) e o item 4, que ainda é inferência sem teste rodado.
