# Posicionador no Fusion (fase 2): resultado

_VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics; adaptador do Fusion, fase 2 (EDR-077)_

Tempo: 370.8 s; amostras 2000, viáveis 0.

## Obstáculos
- Corpos sólidos na cena: 27.
- Promovidos pela regra (dianteiro fora do cálculo): nenhum.
- Mistos (decisão pendente, não promovidos): ['IGNORAR_AMORTECEDORES_DNM_ARQUIVO:1'].
  - ignorado: IGNORAR_PONTOS_V20_1:1 (0 corpos): vazio (sem corpo)
  - ignorado: IGNORAR_PLANOS:1 (0 corpos): vazio (sem corpo)
  - ignorado: IGNORAR_GABARITO_T1_2:1 (1 corpos): objeto da busca ou do regulamento (GABARITO): não é obstáculo
  - ignorado: IGNORAR_ATUACAO_DIANTEIRA:1 (10 corpos): objeto da busca ou do regulamento (ATUACAO): não é obstáculo
  - ignorado: IGNORAR_TRASEIRA:1 (14 corpos): traseiro: ignorado na versão só da dianteira
  - misto: IGNORAR_AMORTECEDORES_DNM_ARQUIVO:1 (20 corpos): dianteiro e traseiro no mesmo componente (X de -1599 a 260 mm; divisa -500 mm): decisão do usuário pendente, não promovido
  - ignorado: IGNORAR_TRAS_TOE_LINK_TE_V20_1:1 (11 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_TOE_LINK_TD_V20_1:1 (11 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_PUSHROD_FE_V20_1:1 (13 corpos): objeto da busca ou do regulamento (PUSHROD): não é obstáculo
  - ignorado: IGNORAR_ROCKER_FE_V20_1:1 (3 corpos): objeto da busca ou do regulamento (ROCKER): não é obstáculo
  - ignorado: IGNORAR_PUSHROD_FD_V20_1:1 (13 corpos): objeto da busca ou do regulamento (PUSHROD): não é obstáculo
  - ignorado: IGNORAR_ROCKER_FD_V20_1:1 (3 corpos): objeto da busca ou do regulamento (ROCKER): não é obstáculo
  - ignorado: IGNORAR_TRAS_BANDEJA_INFERIOR_TE_V20_1:1 (13 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_BANDEJA_SUPERIOR_TE_V20_1:1 (15 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_PUSHROD_TE_V20_1:1 (13 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_ROCKER_TE_V20_1:1 (3 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_BANDEJA_INFERIOR_TD_V20_1:1 (13 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_BANDEJA_SUPERIOR_TD_V20_1:1 (15 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_PUSHROD_TD_V20_1:1 (13 corpos): traseiro: ignorado na versão só da dianteira
  - ignorado: IGNORAR_TRAS_ROCKER_TD_V20_1:1 (6 corpos): traseiro: ignorado na versão só da dianteira

## Avisos

## Não modelado
- manga, freio e pinça dentro do aro (sem RODA_ modelado): o barril do aro trata o miolo como livre e o push rod nasce dentro dele; restrição NAO_VERIFICAVEL em todo candidato
- pneu (V.3.2.4): só o aro entra, como barril da configuração
- V.3.2.4 além do aro: roda e pneu contra suspensão e chassi em todo o curso × esterço até os batentes
- coluna de direção: só a posição em X do início do gabarito T.1.2 (x_ini_t12_m), sem o corpo da coluna
- pedais e F.8.6.3 (folga ≥ 25 mm do conjunto de pedais)
- volume reservado do atenuador de impacto (F.8.4.2): só a face traseira da AIP (F.8.6.1)
- sinalizações T.1.3.3 (exige escudo), V.3.1.3 (visibilidade) e F.5.3.1 (furo em tubo regulado → SES)
- faixa de ajuste de camber, toe e altura (spec §12 J2): só a geometria estática da v10
- peças móveis do CAD (BANDEJA_FD, BANDEJA_FE, DIR, RODA_FD, RODA_FE) não entram na varredura; o aro vem da configuração
- nós do chassi não identificados no Fusion: sorteio dos pivôs sem preferência por nós e critérios de proximidade ao nó zerados
- folga aos fixos medida pela API do Fusion, saturada em 50 mm, com cilindro fino de 0.2 mm sobre o eixo (conservadora em até esse valor)

## Custo da API: {'n_chamadas': 119988, 'n_erros': 0, 'tempo_s': 68.1790940994033, 'ultimo_erro': None}
Contagem: {'segmentos_pedidos': 3635010, 'segmentos_medidos': 97413, 'pontos_pedidos': 535378, 'pontos_medidos': 22575, 'tempo_oraculo_s': 0.0}

## Resultado
Nenhum candidato viável. nenhum candidato viável em 2000 amostras e 20 refinos; menor violação máxima normalizada (avaliação rápida, n = 11) = 0.002974; convergida: INVIAVEL (restrições violadas: comprimento do amortecedor (mínimo), braço r2 (amortecedor))
Violações por restrição (fração das amostras): {'variação de MR': 0.9967741935483871, 'folga às pernas das bandejas: push rod': 0.7032258064516129, 'braço r2 (amortecedor)': 0.6411290322580645, 'giro do rocker': 0.6008064516129032, 'comprimento do amortecedor (mínimo)': 0.5, 'ângulo do amortecedor ao eixo X': 0.39838709677419354, 'folga ao aro: push rod': 0.09919354838709678, 'folga aos fixos: push rod': 0.08790322580645162, 'comprimento do amortecedor (máximo)': 0.0846774193548387, 'folga aos fixos: amortecedor': 0.05887096774193548, 'folga aos fixos: rocker': 0.05, 'folga push rod × amortecedor': 0.03467741935483871, 'X do olhal no chassi': 0.02258064516129032, 'folga ao tirante: push rod': 0.013709677419354839, 'folga às pernas das bandejas: rocker': 0.0032258064516129032, 'folga ao tirante: rocker': 0.0008064516129032258, 'folga às pernas das bandejas: amortecedor': 0.0008064516129032258}
