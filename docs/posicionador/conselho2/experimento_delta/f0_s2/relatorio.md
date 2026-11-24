# Posicionador da atuação dianteira — relatório

> VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics (REFERENCE, EDR-004). Os vereditos (VIAVEL, CONDICIONAL, INVIAVEL) dizem só se as restrições da configuração foram cumpridas no modelo; não aprovam nem validam peça.

- Data: 2026-11-24T02:51:40+00:00; modo: `busca`; comando: `uv run python -X utf8 tools/posicionar_atuacao.py --step data/cad/T11_chassi_2026-11-17.step --saida docs/posicionador/conselho2/experimento_delta/f0_s2 --amostras 60 --refinos 4 --aval-refino 500 --semente 2 --delta-max 0`
- Configuração: `data/posicionador/config_T11.json` (SHA-256 `a05928ea5650ad6d6bee77cf1e17d0f08b2fb2f3279a9c35ad65295b0ff8db44`)
- Hardpoints de base: `data/posicionador/hardpoints_T11_v10.csv` (SHA-256 `357dce2e7060509eed100509b3db2d74a25da09c693c64bd15c439fb6ede8c35`)
- STEP: `data/cad/T11_chassi_2026-11-17.step` (SHA-256 `a3cbf4b8bfd670a3df1892241a04341a9e315ad17ef01de220f655ea2287e9c0`)
- Referencial STEP → carro: o STEP não tem esferas REF_: usada a transformação da configuração, item `transformacao_step_m` (HIPOTESE): rotação [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], translação [-0.942, 0.0, 0.0774] m. Fonte: docs/posicionador/pesquisa/relatorio-geo.md, §5 (hipótese H2): translação STEP → canto (−942,0; 0; +77,4) mm, sem rotação, ajustada no lado reto do FH com erro ≤ 0,55 mm. Usada só quando o STEP não traz as esferas REF_ (caso do chassi.step atual); com as esferas, elas mandam
- Caixa de busca do pivô (m): mín (-0.1500, 0.0000, 0.0601), máx (0.1500, 0.3257, 1.2574); HIPOTESE: caixa derivada do envelope do chassi (decisão R8). X do item `caixa_busca_pivo_m` (META): t11_atuacao.py (script de atuação), sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: penalidade do custo, |Pv_x| ≤ 150 mm (X do pivô do rocker em [−150; 150] mm). Y e Z null: derivados da caixa envolvente das peças CHASSI/FIXO do lado esquerdo no STEP; sem STEP, a ferramenta exige --caixa. Y, Z derivados do STEP: caixa envolvente (referencial do carro) dos 10896 pontos de amostra de todos os obstáculos fixos (envelope Y [-0.3257; 0.3257] m, Z [0.0601; 1.2574] m), lado esquerdo: Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max] (pontos no eixo das cápsulas e nas 12 arestas das caixas, a cada 5 mm no máximo; o raio das cápsulas não entra)

O resultado vale só para o STEP e a configuração com os SHA-256 acima: se um deles mudar, o resultado fica STALE e a ferramenta tem de rodar de novo.

## Limites desta fase

- Na fase 1 nenhum candidato chega a VIAVEL: a folga ao tirante é sempre parcial (raio do tirante A_CONFIRMAR: só o eixo é conferido), a folga à manga/freio/pinça dentro do aro é sempre NAO_VERIFICAVEL (sem RODA_ modelado) e há itens A_CONFIRMAR na configuração. O melhor veredito possível é CONDICIONAL; ele não dispensa a conferência do que está listado abaixo.
- Incerteza geométrica da fase 1, abaixo de 1 mm e sem margem: a transformação STEP → carro da configuração (sem esferas REF_) foi ajustada só no lado reto do FH, com erro ≤ 0,55 mm; os primitivos dos obstáculos podem deixar um furo de cobertura de até ~0,15 mm (tolerância de cobertura de 0,1 mm + deflexão da malha de 0,05 mm); a folga é o mínimo nos n estados do curso (discretização em dz, convergida em n e 2n, mas sem cota entre estados). Uma folga positiva menor que isso não garante ausência de toque. A margem de fabricação δ é da fase 2 (certificador), não está nas restrições desta fase.

## Busca

- Amostras: 60; refinos: 4; semente: 2; pontos da grade do mapa: 127534 (126259 livres para o pivô)
- Falhas nas amostras: {'construção': 29, 'cinemática sem solução': 0, 'avaliação sem resultado': 0}
- Viáveis rápidos: 0; finalistas reavaliados: 0; viáveis convergidos: 0; tempo da busca: 915.5 s

## Fase I (nenhum candidato viável)

- nenhum candidato viável em 60 amostras e 4 refinos; menor violação máxima normalizada (avaliação rápida, n = 11) = 0.001715; convergida: INVIAVEL (restrições violadas: variação de MR, comprimento do amortecedor (mínimo), braço r2 (amortecedor))
- Amostras com resultado: 31 de 60; falhas: {'construção': 29, 'cinemática sem solução': 0, 'avaliação sem resultado': 0}

### Pares de restrições que mais violam juntas (fração das amostras com resultado)

- braço r2 (amortecedor) × variação de MR: 0.484
- folga às pernas das bandejas: push rod × variação de MR: 0.484
- giro do rocker × variação de MR: 0.484
- comprimento do amortecedor (mínimo) × variação de MR: 0.452
- variação de MR × ângulo do amortecedor ao eixo X: 0.419
- folga às pernas das bandejas: push rod × giro do rocker: 0.290
- braço r2 (amortecedor) × comprimento do amortecedor (mínimo): 0.226
- braço r2 (amortecedor) × ângulo do amortecedor ao eixo X: 0.226
- comprimento do amortecedor (mínimo) × folga às pernas das bandejas: push rod: 0.226
- giro do rocker × ângulo do amortecedor ao eixo X: 0.226

### Fração das amostras em que cada restrição é violada

- variação de MR: 0.968
- braço r2 (amortecedor): 0.516
- folga às pernas das bandejas: push rod: 0.484
- giro do rocker: 0.484
- comprimento do amortecedor (mínimo): 0.452
- ângulo do amortecedor ao eixo X: 0.419
- folga aos fixos: push rod: 0.161
- folga aos fixos: rocker: 0.065
- comprimento do amortecedor (máximo): 0.032
- folga ao tirante: push rod: 0.032
- folga aos fixos: amortecedor: 0.032
- folga push rod × amortecedor: 0.032
- folga às pernas das bandejas: rocker: 0.032

### Melhor candidato (menor violação máxima normalizada, reavaliado)

- Veredito: **INVIAVEL** (restrições violadas: variação de MR, comprimento do amortecedor (mínimo), braço r2 (amortecedor))
- Resoluções da varredura (n): [25, 50]; origem: refino
- Pivô do rocker: (-26.3, 311.3, 360.1) mm; r1 = 57.7 mm; r2 = 80.1 mm; φB = 103.8°; δ = 0.0°; azimute = 10.8°; elevação = 16.9°
- Distância ao nó do chassi mais próximo: pivô 179.1 mm, olhal 361.6 mm (preferência U3, não restrição)
- Curva de MR [wheel/spring] no curso: 1.3777 a 1.4329; comprimento do amortecedor: 148.74 a 210.00 mm (curvas completas no resultado.json)
- Pontos da atuação (m, ISO 8855, canto FL): FL_PUSH_OUT = (-0.0096, 0.5865, 0.1780); FL_PUSH_IN = (-0.0792, 0.3113, 0.3368); FL_ROCKER_AXIS_A = (-0.0263, 0.3113, 0.3601); FL_ROCKER_AXIS_B = (-0.0434, 0.3380, 0.3988); FL_ROCKER_SPRING = (-0.0255, 0.2455, 0.4057); FL_SPRING_CHASSIS = (0.1563, 0.2803, 0.4619)

| Restrição | Estado | Valor | Limite | Folga | Origem | Fonte | Motivo |
|---|---|---|---|---|---|---|---|
| MR(0) | OK | 1.4 | [1.39; 1.41] | 0.01 | META | mr_alvo (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: MR_ALVO = 1,40 (MR [wheel/spring], curso da roda / curso do amortecedor) | tolerância ± 0.01 do plano da fase 1 (Task 6) |
| variação de MR | VIOLADA | 0.04007 | 0.04 | -6.859e-05 | META | mr_var_max (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: MR_VAR_MAX = 0,04 (variação máxima de MR no curso, 4 %) | MR de 1.3777 a 1.4329 em 50 pontos de dz ∈ [-23.0; 62.4] mm |
| comprimento do amortecedor (máximo) | OK | 0.21 | 0.21 | 1e-09 | META | olho_a_olho_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: EYE = 210 mm (DNM RCP2S, olho a olho estendido) | máximo em dz = -23.00 mm |
| comprimento do amortecedor (mínimo) | VIOLADA (parcial) | 0.1487 | 0.149 | -0.0002555 | A_CONFIRMAR | olho_a_olho_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: EYE = 210 mm (DNM RCP2S, olho a olho estendido); curso_amortecedor_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: STROKE = 61 mm (DNM RCP2S, curso); margem_curso_amortecedor_m (A_CONFIRMAR): não informado para o T11: margem do curso do amortecedor (fim de curso) a confirmar com a equipe | mínimo em dz = 62.40 mm; margem de curso a confirmar (0 usado) |
| braço r1 (push rod) | OK | 0.05774 | [0.055; 0.08] | 0.002743 | META | braco_min_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: BRACO_MIN = 55 mm (braços do rocker r1 e r2); braco_max_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: BRACO_MAX = 80 mm (braços do rocker r1 e r2) |  |
| braço r2 (amortecedor) | VIOLADA | 0.08014 | [0.055; 0.08] | -0.0001372 | META | braco_min_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: BRACO_MIN = 55 mm (braços do rocker r1 e r2); braco_max_m (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: BRACO_MAX = 80 mm (braços do rocker r1 e r2) |  |
| giro do rocker | OK | 0.8183 | 1.047 | 0.2289 | META | giro_max_rad (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: GIRO_MAX = 60° (giro máximo do rocker no curso), convertido para rad |  |
| ângulo do amortecedor ao eixo X | OK | 0.3682 | 0.5236 | 0.1554 | META | amort_ang_max_rad (META): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: AMORT_ANG_MAX = 30° (amortecedor até 30° do eixo X, para a frente), convertido para rad | pior estado em dz = 62.40 mm (direção do olhal do rocker ao olhal do chassi) |
| folga aos fixos: push rod | OK | 0.1009 | 0 | 0.1009 | HIPOTESE | spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a configuração não declara margem ao chassi); referencial STEP → carro da configuração, item transformacao_step_m (HIPOTESE, sem esferas REF_): HIPOTESE: docs/posicionador/pesquisa/relatorio-geo.md, §5 (hipótese H2): translação STEP → canto (−942,0; 0; +77,4) mm, sem rotação, ajustada no lado reto do FH com erro ≤ 0,55 mm. Usada só quando o STEP não traz as esferas REF_ (caso do chassi.step atual); com as esferas, elas mandam | mínimo em dz = 36.26 mm, a 146 primitivos fixos |
| folga aos fixos: rocker | OK | 0.09691 | 0 | 0.09691 | HIPOTESE | spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a configuração não declara margem ao chassi); referencial STEP → carro da configuração, item transformacao_step_m (HIPOTESE, sem esferas REF_): HIPOTESE: docs/posicionador/pesquisa/relatorio-geo.md, §5 (hipótese H2): translação STEP → canto (−942,0; 0; +77,4) mm, sem rotação, ajustada no lado reto do FH com erro ≤ 0,55 mm. Usada só quando o STEP não traz as esferas REF_ (caso do chassi.step atual); com as esferas, elas mandam | mínimo em dz = 36.26 mm, a 146 primitivos fixos |
| folga aos fixos: amortecedor | OK | 0.08179 | 0 | 0.08179 | HIPOTESE | spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a configuração não declara margem ao chassi); referencial STEP → carro da configuração, item transformacao_step_m (HIPOTESE, sem esferas REF_): HIPOTESE: docs/posicionador/pesquisa/relatorio-geo.md, §5 (hipótese H2): translação STEP → canto (−942,0; 0; +77,4) mm, sem rotação, ajustada no lado reto do FH com erro ≤ 0,55 mm. Usada só quando o STEP não traz as esferas REF_ (caso do chassi.step atual); com as esferas, elas mandam | mínimo em dz = -23.00 mm, a 146 primitivos fixos |
| folga ao aro: push rod | OK | 0.07404 | 0.01 | 0.06404 | HIPOTESE | folga_aro_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_ARO = 10 mm; aro_r_int_m (HIPOTESE): kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_R_IN = 158 mm (aro 13", raio interno do barril); aro_meia_largura_m (HIPOTESE): kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_HALF_W = 100 mm (largura total 200 mm centrada no centro da roda) | mínimo em dz = 62.40 mm (aro movido com a manga; segmento real O→A) |
| folga ao aro: rocker | OK | 0.2169 | 0.01 | 0.2069 | HIPOTESE | folga_aro_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_ARO = 10 mm; aro_r_int_m (HIPOTESE): kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_R_IN = 158 mm (aro 13", raio interno do barril); aro_meia_largura_m (HIPOTESE): kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_HALF_W = 100 mm (largura total 200 mm centrada no centro da roda) | mínimo em dz = 62.40 mm (aro movido com a manga) |
| folga ao aro: amortecedor | OK | 0.2163 | 0.01 | 0.2063 | HIPOTESE | folga_aro_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_ARO = 10 mm; aro_r_int_m (HIPOTESE): kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_R_IN = 158 mm (aro 13", raio interno do barril); aro_meia_largura_m (HIPOTESE): kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_HALF_W = 100 mm (largura total 200 mm centrada no centro da roda) | mínimo em dz = 62.40 mm (aro movido com a manga) |
| folga às pernas das bandejas: push rod | OK | 0.01052 | 0.005 | 0.005523 | MARGEM_EQUIPE | folga_pernas_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_PERNAS = 5 mm (push rod às pernas da bandeja); r_perna_bandeja_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), avaliar(): `segseg(...) - 16.` = 8 mm do push rod + 8 mm da perna; sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5 (raio do envelope das pernas das bandejas) | mínimo em dz = -0.34 mm; sem os primeiros 12 mm do push rod a partir de O (fixação na bandeja) |
| folga às pernas das bandejas: rocker | OK | 0.09717 | 0.005 | 0.09217 | MARGEM_EQUIPE | folga_pernas_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_PERNAS = 5 mm (push rod às pernas da bandeja); r_perna_bandeja_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), avaliar(): `segseg(...) - 16.` = 8 mm do push rod + 8 mm da perna; sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5 (raio do envelope das pernas das bandejas) | mínimo em dz = -23.00 mm |
| folga às pernas das bandejas: amortecedor | OK | 0.1224 | 0.005 | 0.1174 | MARGEM_EQUIPE | folga_pernas_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_PERNAS = 5 mm (push rod às pernas da bandeja); r_perna_bandeja_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), avaliar(): `segseg(...) - 16.` = 8 mm do push rod + 8 mm da perna; sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5 (raio do envelope das pernas das bandejas) | mínimo em dz = 62.40 mm |
| folga ao tirante: push rod | OK (parcial) | 0.0331 | 0 | 0.0331 | A_CONFIRMAR | sem raio nem folga declarados para o tirante: confere só que o envelope do corpo não toca o eixo do tirante (TIE_IN–TIE_OUT) | raio do tirante a confirmar (eixo, raio 0); mínimo em dz = 3.14 mm |
| folga ao tirante: rocker | OK (parcial) | 0.1311 | 0 | 0.1311 | A_CONFIRMAR | sem raio nem folga declarados para o tirante: confere só que o envelope do corpo não toca o eixo do tirante (TIE_IN–TIE_OUT) | raio do tirante a confirmar (eixo, raio 0); mínimo em dz = 62.40 mm |
| folga ao tirante: amortecedor | OK (parcial) | 0.1941 | 0 | 0.1941 | A_CONFIRMAR | sem raio nem folga declarados para o tirante: confere só que o envelope do corpo não toca o eixo do tirante (TIE_IN–TIE_OUT) | raio do tirante a confirmar (eixo, raio 0); mínimo em dz = -23.00 mm |
| folga push rod × amortecedor | OK | 0.07637 | 0.005 | 0.07137 | MARGEM_EQUIPE | folga_prod_amort_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_PROD_AMORT = 5 mm (push rod ao amortecedor); r_prod_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: R_PROD = 8 mm (raio do envelope do push rod); r_mola_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: R_MOLA = 25 mm (raio do envelope da mola/amortecedor) | mínimo em dz = -16.03 mm |
| gabarito T.1.2 | NAO_VERIFICAVEL | — | 0.01 | — | A_CONFIRMAR | x_ini_t12_m (A_CONFIRMAR): não informado para o T11: X de início do trecho em que o gabarito T.1.2 vale, a confirmar com a equipe; x_fim_t12_m (A_CONFIRMAR): não informado para o T11: X de fim do trecho em que o gabarito T.1.2 vale, a confirmar com a equipe; folga_gabarito_m (MARGEM_EQUIPE): t11_atuacao.py (script de atuação), bloco CONFIGURAÇÃO, sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: FOLGA_GAB = 10 mm (folga ao gabarito T.1.2 além do raio de cada peça); z_min_t12_m (A_CONFIRMAR): faixa vertical em que o gabarito T.1.2 pode ser movido (T.1.2.2c, FSAE Rules 2027 V1.0); depende do assoalho/banco do T11 — a confirmar; z_max_t12_m (A_CONFIRMAR): faixa vertical em que o gabarito T.1.2 pode ser movido (T.1.2.2c, FSAE Rules 2027 V1.0); depende do assoalho/banco do T11 — a confirmar | posição da coluna/pedal a confirmar (x_ini_t12_m, x_fim_t12_m) (informativo: lateralmente, o corpo mais próximo fica a 33.6 mm da borda do gabarito, com raio e folga) |
| AIP (F.8.6.1) | NAO_VERIFICAVEL | — | 0 | — | A_CONFIRMAR | x_face_traseira_aip_m (A_CONFIRMAR): não informado para o T11: X da face traseira do atenuador de impacto (AIP) a confirmar com a equipe | X da face traseira da AIP a confirmar |
| esterçamento: folga ao aro | NAO_VERIFICAVEL | — | — | — | A_CONFIRMAR | curso_cremalheira_m (A_CONFIRMAR): não informado para o T11: curso da cremalheira a confirmar com a equipe (desliga a verificação de esterçamento) | curso da cremalheira a confirmar |
| esterçamento: folga ao tirante | NAO_VERIFICAVEL | — | — | — | A_CONFIRMAR | curso_cremalheira_m (A_CONFIRMAR): não informado para o T11: curso da cremalheira a confirmar com a equipe (desliga a verificação de esterçamento) | curso da cremalheira a confirmar |
| folga à manga/freio/pinça dentro do aro | NAO_VERIFICAVEL | — | 0 | — | META | spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a configuração não declara margem ao chassi); spec §10 e §12 J4 (peças ausentes deixam a regra NÃO VERIFICÁVEL) | sem RODA_ modelado: o barril do aro trata o miolo como livre e o push rod nasce dentro dele (fase 1) |
| X do olhal no chassi | OK | 0.1563 | 0.4 | 0.2437 | META | x_max_olhal_m (META): t11_atuacao.py (script de atuação), sha256 ceaea43831aa6d23d8caa3db88423dbdad26f39595fb9346107b7ba93227e5a5: penalidade do custo, C_x ≤ 400 mm (X máximo do olhal do amortecedor no chassi) | X do olhal do amortecedor no chassi (estático) |

## Figuras

- `curvas.png`
- `mapa_espaco_livre.png`

## Itens A_CONFIRMAR da configuração

Cada um desliga a verificação correspondente (o veredito fica no máximo CONDICIONAL).

- `curso_cremalheira_m`: não informado para o T11: curso da cremalheira a confirmar com a equipe (desliga a verificação de esterçamento)
- `margem_curso_amortecedor_m`: não informado para o T11: margem do curso do amortecedor (fim de curso) a confirmar com a equipe
- `x_face_traseira_aip_m`: não informado para o T11: X da face traseira do atenuador de impacto (AIP) a confirmar com a equipe
- `x_fim_t12_m`: não informado para o T11: X de fim do trecho em que o gabarito T.1.2 vale, a confirmar com a equipe
- `x_ini_t12_m`: não informado para o T11: X de início do trecho em que o gabarito T.1.2 vale, a confirmar com a equipe
- `z_max_t12_m`: faixa vertical em que o gabarito T.1.2 pode ser movido (T.1.2.2c, FSAE Rules 2027 V1.0); depende do assoalho/banco do T11 — a confirmar
- `z_min_t12_m`: faixa vertical em que o gabarito T.1.2 pode ser movido (T.1.2.2c, FSAE Rules 2027 V1.0); depende do assoalho/banco do T11 — a confirmar

## Itens HIPOTESE da configuração

- `aro_meia_largura_m`: kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_HALF_W = 100 mm (largura total 200 mm centrada no centro da roda)
- `aro_r_int_m`: kinlib.py (script de atuação), sha256 dc976bffc61150850feedb8cc56b82295a5b0368eb1ce2e8c791f6aab54f1628: RIM_R_IN = 158 mm (aro 13", raio interno do barril)
- `transformacao_step_m`: docs/posicionador/pesquisa/relatorio-geo.md, §5 (hipótese H2): translação STEP → canto (−942,0; 0; +77,4) mm, sem rotação, ajustada no lado reto do FH com erro ≤ 0,55 mm. Usada só quando o STEP não traz as esferas REF_ (caso do chassi.step atual); com as esferas, elas mandam

## Avisos da leitura do STEP

- corpo 'braceFBHdir' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'braceFBHesq' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body85' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body86' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body87' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body88' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body89' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body90' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body91' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body92' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body93' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body94' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body128' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body129' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body130' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'Body131' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'tubo inversor 1' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'tubo inversor 2' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- corpo 'tubo orelhas pack' direto na raiz 'chassi' sem prefixo de categoria: tratado como FIXO
- componente 'FH' sem prefixo de categoria: tratado como FIXO
- componente 'FBH' sem prefixo de categoria: tratado como FIXO
- componente 'MH-estreito' sem prefixo de categoria: tratado como FIXO
- componente 'Modelo Básico Orelha Pack' sem prefixo de categoria: tratado como FIXO

## O que não está modelado

- manga, freio e pinça dentro do aro (sem RODA_ modelado): o barril do aro trata o miolo como livre e o push rod nasce dentro dele; restrição NAO_VERIFICAVEL em todo candidato
- pneu (V.3.2.4): só o aro entra, como barril da configuração
- V.3.2.4 além do aro: roda e pneu contra suspensão e chassi em todo o curso × esterço até os batentes
- coluna de direção: só a posição em X do início do gabarito T.1.2 (x_ini_t12_m), sem o corpo da coluna
- pedais e F.8.6.3 (folga ≥ 25 mm do conjunto de pedais)
- volume reservado do atenuador de impacto (F.8.4.2): só a face traseira da AIP (F.8.6.1)
- sinalizações T.1.3.3 (exige escudo), V.3.1.3 (visibilidade) e F.5.3.1 (furo em tubo regulado → SES)
- faixa de ajuste de camber, toe e altura (spec §12 J2): só a geometria estática da v10

## Avisos da ferramenta

- (nenhum)
