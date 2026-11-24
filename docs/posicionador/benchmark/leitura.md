## Leitura

Rótulos: **[código]** resultado desta rodada; **[inferência]** conclusão minha; **[hipótese]** ainda não testada.

### O que o benchmark mostra

1. **[código] As duas ferramentas veem a v20 de jeito diferente.** O script do Murilo mede a variação de MR em 4,00 % na resolução
   em que otimiza (11 pontos); o mesmo estimador sobe para 6,14 % com 401 pontos, valor que o posicionador já lê com 11 (6,16 %).
   O limite da equipe é 4 %.
2. **[código] Nenhuma das 19 soluções finais é aprovada pelo juiz** (13 do método do Murilo, contando o controle, e 6 do
   posicionador): todas saem INVIAVEL. O problema, com as metas atuais, continua sem solução nas duas ferramentas.
3. **[código] A distância até cumprir é muito diferente.** Violação mediana da solução final: 54,8 % no método do Murilo, 53,5 % no
   controle e 0,5 % no posicionador (cerca de 100 vezes menos); 4 das 6 buscas do posicionador ficam a menos de 1 % do limite,
   contra nenhuma das 13 do Murilo.
4. **[código] O custo final do script não mede o que ele diz medir.** Em 7 de 7 buscas com a configuração dele, o custo final ficou
   em 0,0012 a 0,098 (ele lê custo próximo de 0 como "tudo cumprido") e o juiz reprova as 7, com variação de MR de 5,9 a 6,3 %.
5. **[código] O controle descarta a explicação mais cômoda.** Sem as restrições que o posicionador removeu (tubo ao Front Hoop,
   folga do tubo ao gabarito, triângulo da bandeja superior, gabarito projetado), o método do Murilo continua em 37 a 59 %. A
   diferença não vem dessas restrições.
6. **[código] O que sobra no posicionador é pequeno e específico.** Em 4 das 6 buscas a única restrição violada é o comprimento
   mínimo do amortecedor, 0,68 a 0,74 mm abaixo de 149 mm (curso de 61 mm), com a variação de MR já em 3,47 a 3,87 %. Nas outras
   duas, o braço r2 passa de 80 mm e a variação de MR fica em 2,96 e 4,14 %.
7. **[código] Custo.** A avaliação de um candidato leva 0,126 s (posicionador, n = 11) contra 0,109 s (script, 11 pontos). Com o
   mesmo número de avaliações rápidas (1.500), cada busca do posicionador leva 268 a 284 s contra 128 a 196 s do Murilo, cerca de
   1,7 vez mais tempo de parede (inclui o mapa de espaço livre e a reavaliação convergida dos finalistas, e a contenção dos 4
   processos em 4 núcleos).
8. **[código] Robustez (perturbação SINTÉTICA).** Mediana da pior violação nas amostras perturbadas: 0,6 % no melhor do
   posicionador, 35,8 % no melhor do Murilo e 53,2 % na v20.

### O que ele sugere

- **[inferência]** O gargalo do método do Murilo, nesta rodada, é a resolução em que ele mede a variação de MR: o otimizador para
  onde vê 4 %, e ali o MR real é 6 %. Com poucos pontos ele não tem como saber.
- **[hipótese]** Há um conflito pequeno entre "variação de MR ≤ 4 %" e "usar o curso inteiro de 61 mm do amortecedor": nas melhores
  buscas ele vale cerca de 0,7 mm de curso. Reduzir a exigência de curso nessa ordem, ou o curso de bump em cerca de 1 mm, pode
  tornar o problema viável. Não foi testado: é decisão da equipe e pode ser verificado trocando o valor em `config_T11.json`.

### O que o benchmark não prova

- **O juiz é do posicionador.** Ele usa o MR local do `kinematics_model` e a avaliação convergida. O estimador do script converge
  para o mesmo valor com muitos pontos (item 1), então a medida do juiz não é arbitrária. Mas o benchmark **não separa** quanto da
  diferença vem do estimador de 11 pontos, da construção do r2 pelo MR e da amostragem global do posicionador, ou da região de
  partida. O experimento que separaria: o método do Murilo com 51 pontos ou mais.
- **Partidas diferentes.** As do Murilo são a v20 perturbada (SINTÉTICA); as do posicionador, amostras na caixa derivada do
  envelope do chassi (HIPOTESE, R8). Amostras pequenas (7, 6 e 6 buscas): nenhuma estatística inferencial.
- **Sem CAD.** A cena tem só o aro. O benchmark compara as restrições compartilhadas de cinemática, não a colisão com o chassi, que
  é o que o posicionador faz e o script não (tabela da seção 5).
- **O juiz não mede** o que o script tem e o posicionador não (tubo ao Front Hoop, triângulo da bandeja superior, gabarito em Z
  fixo). O controle neutraliza isso na otimização, mas esses itens ficam sem medição.
- **Sem validação física.** As duas ferramentas usam cinemática consistente entre si (erro de 1e-9 m no comprimento do amortecedor,
  TC-POS-060), mas nenhuma foi comparada com o OptimumKinematics (REFERENCE, EDR-004). VERIFIED não é validado.
- **O orçamento é um teto.** O Nelder-Mead do Murilo parou por convergência antes do limite em duas buscas (1.090 e 1.348
  avaliações); a busca com a configuração original dele gastou 1.753. O posicionador usou as 1.500 nas seis.
- **Tempos** medidos com 4 processos em 4 núcleos, numa máquina de nuvem; valem como ordem de grandeza.

### Como reproduzir

```
uv run python -X utf8 tools/benchmark_posicionador.py rodar --script-murilo PASTA_DO_SCRIPT --saida docs/posicionador/benchmark
<python com matplotlib> tools/benchmark_posicionador.py relatorio --saida docs/posicionador/benchmark
```
A rodada completa leva cerca de 18 minutos em 4 núcleos. `resultados.json` guarda todos os números; este relatório e os gráficos
saem dele.
