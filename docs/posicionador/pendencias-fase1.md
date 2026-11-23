# Posicionador — fase 1: decisões do controlador e pendências adiadas

Gerado ao fechar a execução do plano `docs/superpowers/plans/2026-11-17-posicionador-fase1.md` (2026-11-23), a partir do
registro de execução (ledger). Cada tarefa teve revisão independente; houve revisão final do ramo inteiro e uma onda de
correções (commits 6b53511 e 3247dc5). Suíte do posicionador em 2026-11-23: 45 PASS, 0 FAIL, de 45 (8 arquivos, ~15 min).

## Decisões tomadas pelo controlador durante a execução (com custo se estiverem erradas)
- Ruling R1: config `transformacao_step_m` (HIPOTESE, do relatório da geometria) quando não há esferas REF_ — o STEP atual não as tem — custo se errado: Z condicional, já rotulado.
- Ruling R2: faixa do TC-POS-061 para o aro = 0,079–0,0825 m — a diferença é só raio/amostragem — custo: nenhum (valor medido sai no relatório).
- Ruling R3 (Task 6): margem_curso null → verifica com 0 m, motivo "margem a confirmar (0 usado)", veredito no máximo CONDICIONAL. Raio do tirante sem fonte → folga ao eixo (raio 0) com motivo "raio do tirante a confirmar", veredito no máximo CONDICIONAL. Raio das pernas das bandejas = 8 mm do script (t11_atuacao.py, `- 16.` = 8 push rod + 8 perna) → item novo `r_perna_bandeja_m` MARGEM_EQUIPE no config_T11.json (commit dados: próprio). Rocker: cápsulas Pv–A e Pv–B com r_junta; pivô esfera r_pivo; amortecedor cápsula B–C r_mola; push rod cápsula O–A r_prod.
- Ruling R4: faixa do TC-POS-061 para a variação de MR passa de 0,060–0,062 para 0,060–0,0625 — a faixa do plano veio de uma estimativa de 1ª ordem (6,08 %); o valor exato é 0,0621, confirmado na curva do kinlib com derivada de 2ª ordem — custo se errado: nenhum (o valor medido sai no relatório).
- Ruling R5: folga aos obstáculos fixos com limite 0 (não há margem da equipe ao chassi; spec "sem colidir"); pivô/olhal ficam a ≥ raio da peça + raio do tubo do eixo do tubo (fixação por aba) — custo: nenhum.
- Ruling R6: faixa de Z do gabarito (z_min/z_max) vira itens A_CONFIRMAR na Task 8 (config); até lá T.1.2 NAO_VERIFICAVEL — custo: gabarito não verificado na fase 1 (já era, sem posição do pedal).
- Ruling R7: M1 (ordem) — VIAVEL antes de CONDICIONAL na lista final e no corte dos finalistas: chave (veredito != "VIAVEL", *chave_ordem) — a equipe lê de cima para baixo (spec §6) — LEVAR à Task 8 (busca.py + check novo TC-POS-074).
- Ruling R8 (corrige R1/caixa; defeito do controlador): Y e Z nulos da caixa de busca passam a vir da caixa envolvente de TODOS os obstáculos fixos do STEP (chassi inteiro), lado esquerdo: Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max]; X continua do config. Rótulo HIPOTESE no relatório ("caixa derivada do envelope do chassi") e `--caixa` sobrepõe. Motivo: na faixa X do pivô o CAD atual só tem as travessas do FBH; a envolvente local exclui até a v20. Custo se errado: busca mais lenta numa caixa maior, filtrada pelo mapa de espaço livre. Vai na rodada de correção da Task 8.
- Ruling R9: I6 — scipy (brentq, minimize) fica na fase 1; a fase 3 troca por numpy — custo se errado: retrabalho na fase 3, já previsto e documentado.
- Ruling R10: minors deferred de Tasks 1–8 não listados em final-fixes.md ficam adiados (triagem da revisão final: sem risco à segurança) — custo: dívida técnica registrada.
- Ruling R11: o controlador troca o tempo estimado do CLAUDE.md pelo medido na sua rodada da suíte do posicionador — custo: nenhum.

## Pendências menores adiadas (triagem da revisão final: sem risco à propriedade de segurança)
- - Task 3: minor (deferred): furo silencioso de até ~0,15 mm na conferência de cobertura (tolerância 0,1 mm + deflexão).
- - Task 3: minor (deferred): conferência de cobertura só nos nós da malha (faces grandes em L).
- - Task 3: minor (deferred, LEVAR às Tasks 6/7): `Tubo.r_ext_m` do tubo quadrado é a meia largura — folga deve usar `obstaculos_fixos` (Caixa exata), nunca `r_ext_m`.
- - Task 3: minor (deferred): teste de raios sem divisão em blocos (memória N×T).
- - Task 3: minor (deferred): avisos duplicam em chamadas repetidas; Interface_Static global.
- - Task 3: minor (deferred): parser não trata comentários /* */ do Part 21.
- - Task 3: minor (deferred): sem teste de unidade ≠ mm nem de escapes \X2\, \S\, ''.
- - Task 3: minor (deferred): módulo 1157 linhas com duas responsabilidades (separar parser em step_texto.py numa próxima mexida); CATEGORIAS sem uso.
- - Task 3: minor (deferred): TC-POS-024 não testa a ponta da cápsula.
- - Task 3: minor (deferred): restauração de _PASSO_MEMBRO_MM no teste sem try/finally; `ponta()` definida dentro do laço.
- - Task 4: minor (deferred, LEVAR à Task 6): `limite_aip(None)` devolve None (coerente com o brief); o consumidor trata None como NAO_VERIFICAVEL.
- - Task 4: minor (deferred): desempenho sem pré-filtro por caixa envolvente por coluna.
- - Task 4: minor (deferred): z_max < z_min é truncado em silêncio para 1 linha.
- - Task 4: minor (deferred): tol usa RES_AMOSTRA_M e não o res das amostras; escada do TC-POS-031 com margem apertada (z 0,040 vs 0,044).
- - Task 5: minor (deferred): faltam testes dos caminhos "sem raiz de r2" e "t ≤ 0/disc < 0"; KeyError com repr; Item.valor mutável; `construir` só captura KinematicsError/HardpointError (LEVAR à Task 6: avaliar deve ser robusto a qualquer exceção numérica → INVIAVEL com motivo).
- - Task 5: minor (deferred): transformacao_step_m Z 0,0774 (plano) vs 77,39 mm (relatório) — 0,01 mm, dentro do erro do ajuste.
- - Task 6: minor (deferred, PRIORITÁRIO na revisão final): NaN numa folga vira inf → OK (falha aberta) em _min_por_corpo/acumuladores; corrigir para ValueError → INVIAVEL.
- - Task 6: minor (deferred): avaliação não convergida sai INVIAVEL sem Restricao VIOLADA; sem teste.
- - Task 6: minor (deferred): rótulos de falha (Corner/ramo do motion_ratio/"avaliação sem resultado"); motion_ratio resolve do zero (phi0=0) e pode rejeitar candidato com giro grande.
- - Task 6: minor (deferred): só os 5 itens previstos aceitam null; outro item A_CONFIRMAR derruba tudo por TypeError.
- - Task 6: minor (deferred): exclusão de r_junta do push rod vale para as 4 pernas; TC-POS-064 não isola NAO_VERIFICAVEL→CONDICIONAL; VIAVEL inalcançável no código até existir raio do tirante; _avaliar ~150 linhas; gabarito trata estados simultâneos (conservador, documentar).
- - Task 7: minor (deferred): M2 coocorrência dominada pela frequência marginal (documentar `violacoes` como leitura principal); M3 corte antes da convergência pode esvaziar candidatos com `melhor` aprovado; M4 motivo do olhal sobrescreve; M5 sem teste do olhal nem do peso por nó; M6 mapa não modela volumes do regulamento (desvio da spec §5.2 registrado, conferido em avaliar).
- - Task 7: minor (deferred): busca padrão estimada em 10–15 min (não medida).
- - Task 8: minor (deferred): caminho dos conjuntos por candidato sem teste automático; TC-POS-081 não prova o texto do fallback HIPOTESE; sem OCP um FAIL do 080 vira NÃO EXECUTÁVEL; sufixo duplicado no geometry_rev; --caixa invertida sem validação; ordenar_viaveis redundante.
- - Task 8: minor (deferred): tempo "~12 min" aproximado no CLAUDE.md; docstring de caixa_de_busca vago.

## Pendências residuais da re-revisão final
- CLAUDE.md "~18 min" estimado (controlador troca pelo medido); HP_ de atuação comparadas com a v10 viram aviso "não está no CSV"; _finitos ignora atributo não convertível (2ª barreira existe); gabarito sem corpo da atuação na região não roda o chassi sozinho (comportamento anterior).
