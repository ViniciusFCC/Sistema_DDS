# Resposta: a atuação dianteira vista pela cinemática

Rótulos: [F] fonte (relatório citado); [C] código, em `conselho/assento1_trabalho/k1.py` a `k3.py`, com o `kinlib` sem validação contra o OptimumKinematics; [Cál] cálculo; [I] inferência; [H] hipótese.

## Q1. O método atual é adequado?
Não. Além da formulação (REGISTRO, achado 6; LIT §0), a cinemática tem quatro defeitos.

1. **MR avaliado grosso e sem sinal.**
   - A variação real é **6,1 %** (341 pontos, derivada central) [C]. O otimizador via 4,00 %.
   - O MR cai a 1,384 em dz = +32 e sobe a 1,468 no bump máximo [C]. Com K_w/K_s = 1/MR², a taxa na roda cai cerca de 11 % no fim do bump [Cál]: comportamento regressivo onde se quer o oposto [I].
   - O critério max/min é cego ao sinal e omite dIR/dδ (Milliken, p. 596) [F, LIT].
2. **90° imposto no estático, que fica a 27 % do curso.** No bump máximo, o ângulo push rod–braço chega a 55° e o ângulo amortecedor–braço a **47°**, com 47° de giro [C]. Peixoto (p. 123) recomenda pôr os 90° no meio do curso [F, LIT].
3. **"Mesmo plano" e "amortecedor para a frente" são incompatíveis.**
   - A ponta do push rod se move com n·t = 0,64 em relação ao plano do rocker: daí os 4,6° [C].
   - O eixo que zera a carga axial em 1ª ordem é (−0,92; 0,40; 0,02), a **74°** do eixo da v20 [C].
   - Com esse eixo, o amortecedor teria de ficar a pelo menos 66° do eixo X. O script exige no máximo 30° [C/Cál].
   - É uma troca de conceito escondida, que nenhuma busca resolve [I].
4. **A folga ao aro mede o segmento errado.** O `kinlib` usa PO = UO (a junta superior), mas o push rod sai de O, na bandeja inferior [C].
   - Folga real com a cremalheira em −30 mm: **44,8 mm** (os 19,9 mm do REGISTRO vêm do mesmo erro) [C].
   - O erro está a favor da segurança aqui, mas a verificação não vale em geral.

Também:
- **Curso do amortecedor:** usa 61,00 de 61 mm [C]. Um erro de ±2 mm no olhal ou no pivô leva o amortecedor ao batente dentro do curso [C], sem margem para batente de borracha ou ajuste de altura [I].
- **Push rod × tirante:** 30,8 mm entre eixos (cremalheira em +30 mm), perto do terminal [C]. Não é checado.
- **Freio:** o ponto O fica dentro do aro, 58 mm por dentro do plano da roda, na região do freio [C]. Conflito com pinça e disco não modelado [H].
- **A favor do script:** a linha do push rod passa a no máximo 2,4 mm da junta, então o suporte quase não flexiona [C]. A força no push rod fica entre 1,36 e 1,48 vez a força vertical na roda [C].

## Q2. Método e arquitetura
1. **Conceito decidido pela equipe, não pelo otimizador:**
   - (A) eixo quase longitudinal com amortecedor transversal ou por cima, como no TX;
   - (B) amortecedor longitudinal, aceitando carga axial calculada no pivô.
   - No mesmo nível: em que peça o push rod prende e se a cremalheira fica à frente ou atrás do eixo.
2. **Construção em vez de quase-igualdades:** razão entre os braços tirada do MR-alvo, 90° no meio do giro, amortecedor de catálogo e ajuste de Ls pelo comprimento do push rod.
3. **Restrições duras como desigualdades**, numa grade de curso × esterço:
   - ângulo de transmissão mínimo;
   - carga axial no pivô;
   - margem de curso nas duas pontas do amortecedor;
   - folgas por cápsulas contra tirante, aro, envelope do freio, bandejas, gabarito e tubos.

   Os limites são da equipe, "a confirmar" [F, LIT].
4. **Objetivos:** forma do MR com sinal declarado, reações no chassi e distância ao nó (critério estrutural).
5. **Um avaliador só, com MR analítico ou denso**, igual na busca e no relatório.
6. **Robustez:** um candidato só é aprovado se valer também com os pontos do chassi perturbados pela tolerância de fabricação.
7. **Saída:** candidatos com curvas e vetores de reação. Algoritmo: enumeração dos discretos mais multi-start, como no LIT.

## Q3. Uso do CAD
- Tubos viram cápsulas, e os nós triangulados [F, GEO] são os candidatos a pivô e olhal.
- Tubos previstos e ainda não desenhados entram como cápsulas-fantasma.
- A direção da reação no pivô deve entrar num caminho de carga para o nó. A distância ao nó, sozinha, não basta.
- O CAD precisa trazer, com nome: hardpoints, cremalheira com o curso, manga, envelope do freio e aro [F, GEO §8].

## Q4. Coordenação
1. Suspensão e direção decidem primeiro o conceito e a posição da cremalheira.
2. A suspensão entrega, por ponto: região admissível, vetor de carga e tolerância [F, PRÁTICA].
3. O chassi responde com os nós que oferece. O script reavalia a cada versão do STEP, com o hash registrado.
4. As bandejas da v10 ficam congeladas enquanto isso.

## Q5. Riscos e validação
- **Validar primeiro:** as curvas de MR e de ângulo da v20 no OptimumKinematics. Se divergirem, os números acima caem.
- **Risco do conceito A:** pode não caber no gabarito nem no cockpit [H].
- **Teste que me derrubaria:** a fase I do conceito B, com o avaliador corrigido e ±2 mm de tolerância, sair viável com margem. Nesse caso, consertar o avaliador basta.

**Recomendação em uma frase:** corrigir o avaliador (MR denso com sinal, aro no segmento certo, tirante e freio em curso × esterço, margem de curso), decidir explicitamente o conceito (direção do amortecedor × carga fora do plano) e só então buscar, com desigualdades robustas, entre os nós candidatos.

**Confiança: média.** Principal incerteza: o kinlib, de onde saem todos os números, não foi conferido contra o OptimumKinematics, e os limites do T11 ainda não têm valor.
