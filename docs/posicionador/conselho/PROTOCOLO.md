# Protocolo do conselho rigoroso (7 assentos)

Mesmo formato dos conselhos do projeto (EDR-051, EDR-053): lentes independentes, revisão anônima, ranking de Borda,
síntese do presidente (linha principal). Modelo de cada assento: opus, esforço high.

## Assentos
1. Cinemática e dinâmica de suspensão (push rod, rocker, MR, ângulos de transmissão, direção).
2. Estrutura do chassi tubular (nós, triangulação, cargas nas fixações, flexão de tubo, abas).
3. Otimização e síntese de mecanismos (formulação matemática, viabilidade, global × local).
4. CAD e software (pipeline Fusion ↔ Python, representação de tubos/nós, manutenção por equipe estudante).
5. Cético / verificação (evidência contra, como provar que uma solução é válida, testes, modos de falha).
6. Pragmático / gestão do projeto (prazo, coordenação chassi × suspensão, o que fazer primeiro).
7. Regulamento, segurança e manufatura (gabaritos, inspeção técnica, fabricação e montagem).

## Perguntas (iguais para todos)
Q1. O método atual (script do Murilo) é adequado para o problema? Por quê (com evidência dos relatórios)?
Q2. Que método e arquitetura de script você recomenda? Variáveis, restrições (duras × objetivos), algoritmo, saída.
Q3. Como o script deve usar tubos e nós do CAD, sabendo que o chassi está incompleto e muda junto com a suspensão?
Q4. Que processo de coordenação chassi × suspensão você recomenda (quem decide o quê, em que ordem, com que dados)?
Q5. Riscos principais e o que validar primeiro (teste mínimo que derrubaria sua recomendação).

## Regras
- Use só o que está nos relatórios da fase 1 e no código/CAD; rotule fato de fonte, resultado de código, cálculo,
  inferência, hipótese. Nada de número, regra ou referência inventada.
- Máx. ~900 palavras. Termine com "Recomendação em uma frase" e "Confiança (alta/média/baixa) e principal incerteza".

## Revisão anônima
Cada assento recebe as 7 respostas com letras embaralhadas, aponta o erro mais grave e o ponto mais forte de cada uma,
e ranqueia de 1 (melhor) a 7. Borda: 1º = 6 pontos ... 7º = 0. Ranking calculado com e sem o voto próprio.

## Instruções da revisão anônima (rodada 2)
Leia SÓ `conselho/anon/resposta_A.md` a `resposta_G.md` (não abra `resposta_assento*.md` nem investigue a autoria; a
sua própria resposta está entre elas e você deve avaliá-la com o mesmo rigor). Releia a seção "Correção" no fim do
`REGISTRO.md`. Pode conferir uma afirmação rodando código rápido (`geo/.venv/bin/python -I -B`, saídas só na sua pasta
de trabalho). Grave `conselho/revisao_assento<N>.md` (≤ 600 palavras) com:
1. Para cada letra: erro ou fraqueza mais grave e ponto mais forte (1 a 2 linhas cada; cite número quando houver).
2. `RANKING: L1 > L2 > ... > L7` (1º = melhor resposta para o objetivo do usuário, pesando correção técnica,
   evidência e utilidade para a decisão).
3. Até 5 divergências entre as respostas que o presidente precisa decidir, com a sua posição.
Resposta final ao orquestrador: só a linha RANKING.
