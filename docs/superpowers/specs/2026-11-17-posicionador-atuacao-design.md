# Spec — posicionador de pontos da atuação dianteira (T11)

Status: APROVADA (usuário, 2026-11-17: "Comece"; EDR-076 e TC-POS- autorizados). Base: `docs/posicionador/registro-de-decisoes.md`
(diretrizes U1–U6), `docs/posicionador/conselho/SINTESE.md` e os relatórios em `docs/posicionador/pesquisa/`.

## 1. Objetivo
Dizer **onde os pontos da atuação podem ficar** (push rod na bandeja e no rocker, pivô e eixo do rocker, amortecedor no
rocker e no chassi) **sem colidir** com os gabaritos e zonas do regulamento e com qualquer outra peça do CAD, ao longo
de todo o curso da suspensão e do esterçamento, cumprindo as metas cinemáticas da equipe (MR, curso do amortecedor).
Proximidade a nó/tubo existente entra como preferência (U3). V1 lê .step; versão final roda dentro do Fusion (U4).

## 2. Não objetivos (U1)
- Não propõe, roteia nem dimensiona tubos; não pede nós ao chassi; não faz análise estrutural (σ, rigidez, FEA).
- Não otimiza a cinemática das bandejas, da direção nem do RC (vêm prontas: v10 aprovada).
- Não substitui a REFERENCE de cinemática (OptimumKinematics, EDR-004) nem a inspeção técnica.

## 3. Entradas
1. CAD da montagem (.step na V1; design aberto no Fusion na final), em mm, com todas as peças disponíveis.
2. Classificação pelo prefixo do componente de primeiro nível (documento "Exportação do CAD (.step) para o
   posicionador da atuação — T11", 2026-11-17): `CHASSI_` (obstáculo fixo; tubos e nós reconhecidos), `FIXO_`
   (obstáculo fixo), `RODA_FE_`/`RODA_FD_` (move com a roda), `BANDEJA_FE_`/`BANDEJA_FD_` (gira com a bandeja), `DIR_`
   (move com o esterçamento e a roda), `REF_` (esferas Ø 5 mm do referencial: `REF_ORIGEM`, `REF_X`, `REF_Y`), `HP_`
   (esferas Ø 5 mm dos hardpoints, `HP_FL_<chave do schema>`), `IGNORAR_` (fora da análise). Sem prefixo = `FIXO_`, com
   aviso. Envoltória de peça não desenhada: sufixo `_ENVELOPE`.
3. Hardpoints fixos (bandejas, tirante, centro da roda): CSV no schema `hardpoint-schema-V2.0` na V1 (dados do T11 v10,
   `geometria_T11.json` do script do Murilo); lidos das esferas `HP_` quando o STEP as trouxer (o programa confere a
   coerência entre os dois e avisa). Referencial: esferas `REF_`; sem elas, transformação declarada na configuração.
4. Configuração com procedência obrigatória em cada limite: REGRA (artigo + versão R27 V1.0), MARGEM DA EQUIPE, META,
   PREFERÊNCIA. Valor sem fonte = "a confirmar" e o programa avisa.

## 4. Volumes gerados pelo programa a partir do regulamento (R27 V1.0)
- T.1.2 seção interna: octógono 350 × 350 com 4 chanfros e entalhes; altura livre (existe trajetória z(x) sem
  interferência); X de trás da coluna até 100 mm atrás da face do pedal; faixa central de 50 mm permitida.
- F.8.6.1: nada de suspensão/direção à frente da face traseira da AIP. F.8.4.2: volume reservado do IA.
- F.8.6.3: folga ≥ 25 mm do conjunto de pedais (quando houver pedal no CAD).
- V.3.2.4: roda/pneu sem tocar suspensão e chassi em todo o curso × esterço (até os batentes).
- Sinalizações (não bloqueiam): T.1.3.3 "exige escudo" (peça móvel entre FH e 100 mm atrás dos pedais); V.3.1.3
  visibilidade; F.5.3.1 furo em tubo regulado → SES.

## 5. Processo
1. **Leitura e modelo de obstáculos:** tubos reconhecidos viram cápsulas (tubo quadrado: raio = meia-diagonal +
   0,2 mm); demais corpos ficam como sólido (BRep/malha). Nós e tubos identificados servem à preferência U3.
2. **Mapa de espaço livre** para os pontos do chassi (pivô, olhal): grade na caixa de busca declarada, cada célula com a
   folga à peça mais próxima e aos volumes do regulamento, descontado o raio da peça que vai ali. É uma das saídas.
3. **Construção do mecanismo** com as metas resolvidas por construção (braço do amortecedor pelo MR-alvo, olhal pelo
   comprimento do amortecedor, 90° no meio do curso como opção); conceito do amortecedor enumerado (sem impor 30°).
4. **Varredura curso × esterço** com resolução que convergiu: folga de push rod, rocker e amortecedor contra obstáculos
   fixos, contra as peças RODA_/DIR_ movidas pela cinemática e contra os volumes do regulamento; curso do amortecedor
   com margem nas duas pontas.
5. **Busca:** amostragem do espaço livre + solver local com restrições explícitas, vários pontos de partida.
6. **Fase I (diagnóstico):** se não houver candidato, devolve o de menor violação e quais restrições conflitam.
7. **Certificador independente:** malha n e 2n com o mesmo veredito, margens explícitas, tolerância de fabricação δ
   (a medir), geometria exata nos finalistas. Só ele aprova.

## 6. Saídas
- Lista de candidatos certificados, cada um com: pontos (schema de hardpoints, Status PROVISIONAL), margem por
  restrição, distância ao nó/tubo mais próximo, curvas de MR e comprimento do amortecedor, flags de regra, hash do CAD
  e lista do que não estava modelado. Aprovação fica STALE quando o CAD muda.
- Mapa de espaço livre (V1: figura e arquivo; final: desenhado no Fusion sem alterar o design).
- Sem candidato: relatório da Fase I.

## 7. Arquitetura (V1 → final)
Núcleo independente do CAD (cinemática, construção, busca, certificador; Python puro + numpy, sem `adsk`) + adaptador
de geometria com a mesma interface: `AdaptadorSTEP` (OpenCascade, V1) e `AdaptadorFusion` (API do Fusion, final).
Restrições da API do Fusion (fusion/RELATORIO_FUSION.md, docs oficiais help.autodesk.com):
- Python embutido 3.12 → 3.14 (blog Autodesk, 2026-01; conferir `sys.version`); módulo de terceiros só documentado
  como cópia na pasta do add-in; scipy/pip não documentados → núcleo não depende de scipy.
- Leitura: `allOccurrences`, `bRepBodies`, `transform2`, `SketchPoint.worldGeometry`, `ConstructionPoint.geometry`
  confirmados; unidade interna cm.
- `measureMinimumDistance` não aceita corpo temporário (só Plane/Point3D temporários); `analyzeInterference` só com
  corpos/ocorrências reais. → colisão no laço por cápsulas/geometria extraída; conferência exata no Fusion nos finalistas.
- Script bloqueia a interface; `doEvents` em laço longo pode derrubar o Fusion; padrão suportado = thread de trabalho
  sem chamadas à API + evento customizado. → o laço pesado roda em thread de trabalho com o núcleo puro.
- Saída visual: `CustomGraphicsGroup.addBRepBody` aceita corpo transiente (mostra o resultado sem alterar o design);
  em design paramétrico, gravar pontos como pontos de esboço.
- Licença educacional: nenhum texto oficial lido confirma ou proíbe scripts → teste de 5 min na máquina da equipe.
Fluxo final no Fusion: botão no add-in → lê o design e extrai obstáculos/hardpoints → thread roda o núcleo com
progresso → desenha mapa de espaço livre e candidatos → conferência exata dos finalistas → usuário aceita e o add-in
grava os pontos como esboço nomeado.

## 8. Critérios de aceitação
- CA-1 Leitura: chassi.step → 31 corpos, 28 nós, lado reto do FH a ≤ 0,55 mm do script (regressão).
- CA-2 Colisão: casos sintéticos de resposta conhecida; a folga da cápsula nunca supera a exata em mais de 0,2 mm.
- CA-3 Gabarito: caso que bloqueia toda trajetória z(x) é reprovado; caso livre passa; dimensões conferidas na figura.
- CA-4 Mutação: o certificador reprova 100 % das violações injetadas (colisão, gabarito, AIP, curso).
- CA-5 Convergência: mesmo veredito com n e 2n pontos de varredura.
- CA-6 Regressão v20: MR var. ≈ 6,1 % (reprova), folga ao aro no segmento real 81,5 / 44,8 mm.
- CA-7 Cinemática: kinlib × `kinematics_model.Corner` × OptimumKinematics na v20 dentro de tolerância a definir.
- CA-8 (final) Fusion × STEP: mesmos vereditos e folgas dentro de tolerância no mesmo design.

## 9. Etapas
Ordem (U5): E0 validar cinemática e corrigir o avaliador · E1 adaptador STEP, obstáculos, volumes do regulamento, mapa de espaço
livre · E2 construção, busca, Fase I e certificador · E3 adaptador Fusion (script/add-in) e visualização no design.

## 10. Riscos
Conjunto vazio com as metas atuais (provável: decisão da equipe sobre o que relaxar); peças ausentes no CAD (pedal,
coluna, manga/freio) deixam regras NÃO VERIFICÁVEIS; nomes/referencial que não sobrevivem ao STEP; δ desconhecido;
cinemática não validada contra a REFERENCE; limites do ambiente Python do Fusion.

## 11. Decisões em aberto
- [ABERTO A3] Quais metas relaxar se a Fase I der vazio (MR var. ≤ 4 %, curso inteiro, MR 1,40).
- [FECHADO A4] Pontos: PUSH_OUT (só na bandeja inferior, usuário 2026-11-17), PUSH_IN, ROCKER_AXIS_A/B, ROCKER_SPRING,
  SPRING_CHASSIS; bandejas, tirante e roda fixos (v10).

## 12. Ajustes vindos da comparação com equipes (topo/RELATORIO_ACADEMICO.md, topo/RELATORIO_EQUIPES.md)
- J1. Usar os graus de liberdade que não mudam a cinemática (posição ao longo do eixo do rocker, deslocamento do plano
  do mecanismo) como variáveis de empacotamento e de aproximação a nó (ETSEIB/UPC 2025; Manresa 2024).
- J2. Incluir na varredura de folga a faixa de ajuste de camber/toe/altura e os extremos combinados curso × esterço ×
  camber (TU Brno 2020; caso de Weingarten em Borowski 2026).
- J3. Núcleo fora do Fusion e add-in fino (sem precedente publicado de posicionamento dentro de CAD comercial).
- J4. Certificar só quando o CAD tiver a cobertura mínima de peças declarada (aro/manga/freio, cremalheira/coluna,
  pedais); abaixo disso o resultado sai "condicional" (evitar falsa confiança).
- J5. δ de fabricação e mutação entram quando houver δ medido; até lá, margem declarada pela equipe.

## 13. Decisões do usuário incorporadas (rodada 3)
- [FECHADO A1] Código no repositório Sistema_DDS, sem integração com a planilha (U6).
- [FECHADO A2] Convenção de nomes e esferas: documento de exportação (REGISTRO, rodada 3).
- Ordem (U5): fase 1 = E0 + E1 + E2 básico (sem δ, sem BRep exato, sem mutação); fase 2 = certificador completo;
  fase 3 = adaptador Fusion.
