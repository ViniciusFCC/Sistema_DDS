## Resumo em linguagem simples

**O que foi medido.** Cada "busca" é uma tentativa de achar a posição da atuação dianteira (pivô do balancim, olhal do amortecedor e ponta do push rod) que cumpra todas as restrições ao mesmo tempo. Cada ferramenta recebeu o mesmo orçamento (cerca de 1500 avaliações rápidas por busca) e partiu de 20 pontos de partida diferentes, sempre os mesmos para todas. Um juiz independente avalia cada resultado. Um segundo juiz, mais fino (401 pontos de curso), reavalia: ele concordou em 100 % dos casos, nos 7 braços. As perturbações dos pontos de partida são **sintéticas**, criadas para o teste, e não são dado do carro.

**Quem achou posição válida (sem nenhuma restrição violada):**

| Ferramenta | Buscas sem violação | Violação mediana | Melhor busca |
|---|---|---|---|
| Script de atuação | 0 de 20 | 53,9 % do limite | 34,2 % |
| Script sem as restrições do tubo (controle) | 0 de 20 | 53,5 % | 9,4 % |
| Posicionador anterior (v1) | 0 de 20 | 2,9 % | 0,22 % |
| **Posicionador novo (v2)** | **15 de 20** | **0 %** | 0 % |

"Violação" é o quanto a pior restrição passa do limite, em % do próprio limite. Zero significa que nenhuma restrição foi violada.

**Em linguagem comum.** O script de atuação, com o mesmo orçamento, não terminou nenhuma das 20 buscas dentro das restrições. O controle, sem as restrições do tubo, também não: portanto o problema do script aqui não é o tubo. O posicionador anterior chegou perto, e o novo cumpriu todas em 15 das 20 buscas.

**Por que o novo funciona (e o antigo não).** Existe um conflito geométrico, não uma falta de busca. Com MR(0) fixado em 1,40, o curso do amortecedor em compressão é a integral de dz/MR. Para o amortecedor não fechar abaixo de 149 mm no fim do curso de 61 mm da roda mais 23 mm de rebote, a média harmônica do MR no curso precisa ser pelo menos igual ao MR(0): a margem de curso é zero por construção. Quem só mexe nas outras posições não tem folga para ceder. O que muda o jogo é uma variável a mais: o ângulo δ, que gira a ponta do push rod em torno do eixo do balancim sem mudar o r1 nem o MR(0).

**O que cada melhoria acrescentou** (as ablações usam os 10 primeiros pontos de partida; neles o v2 completo acertou 10 de 10):

| Versão do v2 | Sem violação (de 10) |
|---|---|
| v2 completo | 10 |
| sem a margem como objetivo | 10 |
| sem a caixa de busca dinâmica | 5 |
| sem o ângulo δ | 0 |

- **δ é o que decide.** Sem ele, nenhuma busca fechou, mesmo com tudo o mais ligado. É o resultado mais forte do benchmark.
- **Caixa dinâmica ajuda.** Sem ela, metade das buscas falha. Amostra pequena (10): é evidência, não prova.
- **A margem como objetivo não aumentou a taxa de acerto.** Com e sem ela, 10 de 10 nos mesmos pontos. Nas 10 buscas restantes só o v2 completo foi rodado (5 falharam), então não dá para dizer se a margem ajudou ou atrapalhou lá. Ela serve para escolher entre candidatos viáveis, não para achá-los.

**Honestidade sobre a margem.** Dos candidatos viáveis, a folga física do comprimento mínimo do amortecedor é de **dezenas de micrômetros** (da ordem de 0,02 a 0,11 mm no melhor candidato de cada busca). Isso é compatível com o limite do conflito acima: com MR(0) fixo e sem decidir uma margem de fim de curso, a folga não passa disso. Um candidato com 0,05 mm de folga existe no modelo, mas não sobrevive a uma tolerância de fabricação real. O veredito é CONDICIONAL, nunca VIAVEL: os itens A_CONFIRMAR (tirante completo, manga, freio, margem de fim de curso) seguem em aberto.

**O que o script de atuação ainda tem a seu favor.** Este benchmark não mede tudo. Ele não avalia a fidelidade ao CAD que o autor do script usou, nem a facilidade de uso dentro do Fusion. O benchmark compara só a capacidade de achar uma posição que cumpra as restrições do modelo. Tempo por busca: 355 s no script contra 726 s no v2, mas as buscas rodaram em paralelo (13 processos), então esses tempos não são comparáveis a um uso interativo.

**Limites deste benchmark**
- 20 pontos de partida para os braços principais e 10 para as ablações: as taxas têm incerteza grande (15 de 20 não é "75 %" com precisão).
- Os pontos de partida do v2 e as ablações não são os mesmos 20: as ablações usam os 10 primeiros.
- Nenhum candidato foi validado contra o OptimumKinematics (só você pode rodar). Posição achada é CONDICIONAL, não aprovada.
- "Não achou" nunca quer dizer "não existe": nos 5 casos do v2 sem solução, o método não achou, e isso não prova que não haja posição viável.
