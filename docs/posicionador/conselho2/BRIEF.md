# Briefing comum do conselho 2 (precisão, achar posições válidas e resolver conflitos)

Você é um assento de um conselho técnico rigoroso de 7 assentos. Responda em português, prosa densa. Rótulos obrigatórios em toda
afirmação que influencia decisão: fato de fonte (cite o arquivo), resultado de código (você rodou), cálculo, inferência, hipótese.
Nada de número, regra ou referência inventada. Discorde do que estiver nos documentos quando tiver motivo, dizendo por quê.

REPOSITÓRIO: /home/user/Sistema_DDS (Python em `.venv/bin/python -X utf8`; numpy, scipy, OCP disponíveis).
NÃO altere nenhum arquivo do repositório fora de `docs/posicionador/conselho2/trabalho_assento<N>/` (seus scripts e saídas) e do
seu arquivo de resposta. Não faça commit nem push. Sem internet, salvo para conferir uma fonte já citada nos documentos.
Rode verificações rápidas (minutos, não horas; no máximo ~10 min de CPU por rodada). Copie `data/posicionador/config_T11.json`
para a sua pasta se quiser mudar limites; nunca edite o original.

LEIA (nesta ordem, só o que precisar de cada um):
1. `docs/posicionador/benchmark/resumo_simples.md`, `docs/posicionador/benchmark/leitura.md`, `docs/posicionador/benchmark/relatorio.md`
   (o resultado novo: posicionador × script de atuação; juiz único; grupo de controle).
2. `docs/posicionador/METODOLOGIA.md` e `docs/posicionador/README.md` (o que o posicionador faz, limites, itens A_CONFIRMAR).
3. `docs/posicionador/conselho/SINTESE.md` (conselho anterior: decisões já tomadas; não as reabra sem motivo novo).
4. Código: `python/posicionador/` (mecanismo.py, varredura.py, busca.py, espaco_livre.py, cad_step.py, regulamento.py, config.py),
   `tools/posicionar_atuacao.py`, `data/posicionador/config_T11.json`, `data/posicionador/hardpoints_T11_v10.*`,
   `data/posicionador/hardpoints_T11_v20_script.*`, `tools/benchmark_posicionador.py`.
5. `docs/posicionador/pesquisa/` (relatórios de literatura, prática, geometria) se precisar de fonte.

FATOS DO ESTADO ATUAL (resultados de código já medidos, ver os relatórios):
- Nenhuma das 19 soluções finais do benchmark é aprovada pelo juiz; com o STEP e 200 amostras o posicionador também não achou
  posição viável (Fase I: variação de MR violada em 99 % das amostras com resultado).
- Melhores buscas do posicionador (sem CAD): violação mediana 0,5 %; em 4 de 6 a única restrição violada é o comprimento mínimo
  do amortecedor, 0,68 a 0,74 mm abaixo de 149 mm (curso de 61 mm), com a variação de MR em 3,47 a 3,87 %.
- Hipótese sugerida e NÃO testada: o conflito é "variação de MR ≤ 4 %" × "usar o curso inteiro de 61 mm"; relaxar cerca de 1 mm
  de curso poderia tornar viável. Metas e limites são decisão da equipe (origens REGRA/META/MARGEM_EQUIPE/HIPOTESE/A_CONFIRMAR).
- Cinemática: `kinematics_model` do repositório, NOT_VALIDATED contra o OptimumKinematics. O posicionador nunca aprova (máx. CONDICIONAL).
- Plataforma da equipe: Windows. Entregável: um `.exe` único (PyInstaller; compilado e testado no CI em Windows). Fusion: ainda não verificado.

O QUE O USUÁRIO QUER AGORA: uma solução ainda melhor em (1) PRECISÃO (a medida e o veredito corretos, com incerteza quantificada),
(2) ACHAR POSIÇÕES VÁLIDAS (aumentar a chance de existir e de a busca achar posição que cumpre tudo, sem enfraquecer o juiz) e
(3) RESOLVER OS CONFLITOS entre metas (identificar quais brigam, quanto custa cada uma, o que relaxar e em que ordem, deixando a
decisão com a equipe). Não vale "ajustar o resultado para bater": mudar meta é proposta, nunca ação.

PERGUNTAS (iguais para todos):
Q1. Onde está a perda de precisão hoje (medida, convergência, veredito, incerteza)? O que mudar, com prioridade, e como provar.
Q2. Por que não se achou posição viável? Separe, com evidência (de preferência rodando algo curto), o que é (a) conflito de metas,
    (b) limitação da busca (amostragem, caixa, parametrização), (c) CAD incompleto/hipótese, (d) erro de modelo. Que experimento decide?
Q3. Que mudança de método/arquitetura aumenta a chance de achar posições válidas (parametrização, busca, restrições duras ×
    objetivos, enumeração de conceitos, otimização multiobjetivo/Pareto, uso do mapa de espaço livre)? Dê o desenho concreto.
Q4. Como resolver os conflitos: mapa de conflitos medido (quais pares de restrições brigam e quanto custa em unidades físicas),
    ordem de relaxamento proposta, e o texto da pergunta que a equipe precisa responder para cada um.
Q5. Riscos e o teste mínimo que derrubaria sua recomendação; o que NÃO fazer.

RESPOSTA: grave em `docs/posicionador/conselho2/resposta_assento<N>.md`, ≤ ~900 palavras. Termine com "Recomendação em uma frase"
e "Confiança (alta/média/baixa) e principal incerteza". Não cite o número nem o nome do seu assento no texto (a revisão será anônima).
Resposta final ao orquestrador: só o caminho do arquivo e a recomendação em uma frase.
