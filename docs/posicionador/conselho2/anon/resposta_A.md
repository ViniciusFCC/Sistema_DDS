# Resposta: sequência de trabalho, decisões da equipe e custo (lente pragmática)

Rótulos: [fonte] arquivo citado; [código] rodei; [cálculo]; [inferência]; [hipótese].

## Resumo do que mudou na minha leitura
O benchmark já mostra que o posicionador mede melhor que o script de atuação [fonte: benchmark/resumo_simples.md]. O que falta não é mais precisão de medida, é decisão da equipe sobre três limites que brigam. A hipótese "relaxar ~1 mm de curso resolve" [fonte: benchmark/leitura.md] é, na forma como está escrita, incompleta: testei.

## Q2/Q4. Experimento curto (código, `trabalho_<autor>/relaxar.py`, saída em `relaxar.log`)
Busca sem CAD, caixa padrão do benchmark, 1 semente, 150 amostras e 4 refinos (muito menos que as 1.500 avaliações do benchmark, e a máquina estava com carga 9 a 12 em 4 núcleos), alterando UM item de uma cópia da configuração por vez. Melhor candidato de cada variante:
- base: violação 8,9 %; viola variação de MR (4,29 %), comprimento mínimo do amortecedor (0,52 mm) e r2.
- curso de bump da roda −1 mm (62,4 → 61,4 mm): o comprimento mínimo deixa de ser violado; sobram MR (4,08 %, 0,08 p.p. acima) e r2 (violado).
- MR var. máx 5 %: a variação passa; o comprimento mínimo continua violado em 0,7 mm; violação 0,47 %.
- MR-alvo 1,44: sobram MR (4,31 %) e r2.
Leitura [inferência]: o conflito não é um par, é um triângulo: (curso total de roda ÷ MR médio ≤ 61 mm de curso do DNM) × (variação de MR ≤ 4 %) × (r2 ≤ 80 mm, com MR-alvo 1,40). Cada afrouxamento isolado desloca a violação para outra das três; nenhum zerou tudo. Isso contradiz a leitura "só falta 1 mm de curso" para a maioria dos casos, mas é amostra mínima (n = 1 por variante, refino curto): não prova nada sobre existência.

## Q1. Precisão: o que fazer primeiro (barato)
1. Não gastar tempo em mais precisão da medida: a convergência em n já existe (n0 = 25 e dobra) [fonte: busca.py]. O maior risco restante é a cinemática NOT_VALIDATED. Custo menor e retorno maior: comparar `kinematics_model` com o OptimumKinematics em UMA configuração (v20) e UM número (MR em 5 pontos do curso). É o único item que pode invalidar tudo; exige que alguém com a licença rode o OptimumKinematics, ~meio dia de uma pessoa [hipótese de custo].

## Q3. Busca: sequência de melhor retorno
a) Trocar o objetivo do refino por duas fases: primeiro resolver só (curso, r2, MR) com poucas variáveis (pivô livre, direção do amortecedor, r1), depois checar colisão. Custo: edição pequena em `busca.py` [inferência], horas. Justificativa: as três restrições que brigam são da cinemática, não do CAD.
b) Rodar um mapa de Pareto 3D (var. de MR × curso usado × r2) sem CAD, com ~2.000 pontos: custo ~10 min de CPU [cálculo a partir de 0,126 s por avaliação]. Entrega à equipe uma curva "quanto de cada limite compra o outro", que é exatamente o que a decisão precisa.
c) Só depois, repetir com o CAD, para ver quanto o chassi custa a mais. Ordem importa: com CAD, 200 amostras levaram ~11 min [fonte: README]; fazer isto antes de saber a curva sem CAD é o gasto mais caro com a menor informação.

## Q4. Decisões que a equipe precisa tomar (cada uma é proposta, não ação)
1. Curso do amortecedor: "A faixa de curso do DNM RCP2S (61 mm) é um limite duro ou há folga de ~1 mm de bump da roda (62,4 → ~61,4 mm) aceitável pelo batente?" Dado que decide: o curso de bump real necessário (cálculo da pista/ride, mapa de batentes), hoje META copiada do script.
2. Variação de MR: "4 % é requisito de carro ou herdado do script? Qual a sensibilidade de ride rate/ganho de rigidez a 5 %?" Dado: análise de rigidez da planilha (K_wheel = K_spring/MR²).
3. MR-alvo 1,40: "Há faixa aceitável de MR (por exemplo 1,35 a 1,45) ou o valor é fixado pela mola já comprada?" Dado: catálogo/molas existentes.
4. Braço r2 ≤ 80 mm: "É limite do rocker usinável ou preferência?" Dado: desenho/máquina.
5. Conceito do amortecedor (transversal como no TX × longitudinal) [fonte: conselho/SINTESE.md, item que continua com a equipe]; nada na ferramenta resolve isto.
Ordem de relaxamento que proponho como recomendação, não como ação: primeiro o que a equipe puder confirmar sem custo físico (variação de MR 4 → 5 %, que no meu teste zerou a variação mas deixou 0,7 mm de curso), depois o curso de bump (−1 mm), depois MR-alvo. Não relaxar r2 antes de saber se há motivo de fabricação.

## Q5. Riscos e o que não fazer
- Teste mínimo que derruba minha leitura do triângulo: rodar `relaxar.py` com 3 sementes e 1.500 avaliações cada; se a combinação (MR var 5 %, bump −1 mm) der candidato CONDICIONAL em ≥ 1 semente, o triângulo é folgado; se nenhuma, o conflito é real.
- Não reescrever a busca nem montar o pipeline do Fusion antes dessa curva [inferência, mesma linha do conselho anterior].
- Não mudar metas no arquivo de configuração sem registrar quem decidiu e em quê: o benchmark só vale se o juiz permanecer fixo.
- Não tratar CONDICIONAL como aprovação; a cinemática continua NOT_VALIDATED.
- Sem datas de competição: não tenho dado, e a priorização acima independe delas; a equipe deve colocar o prazo para decidir a ordem entre (b) e a validação do OptimumKinematics.

## Recomendação em uma frase
Rodar primeiro o mapa de compromisso sem CAD (variação de MR × curso × r2), levá-lo à equipe junto com a pergunta sobre os três limites, e só depois buscar com CAD.

## Confiança (alta/média/baixa) e principal incerteza
Média para a ordem de trabalho, baixa para a existência do triângulo: o experimento tem uma semente por variante e busca curta sob máquina carregada, e o refino por Nelder-Mead sobre violação máxima é não suave.
