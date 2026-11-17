# Registro — método de posicionamento da atuação dianteira do T11

Pasta de trabalho: `/tmp/claude-0/-home-user-Sistema-DDS/6637db41-949f-5b01-8433-f10e3fa5c55a/scratchpad/atuacao/`
Data: 2026-11-17. Fora do repositório Sistema_DDS (nada é commitado; nenhum ID SUS-/EDR-/TC- é criado).

## Contexto (usuário, 2026-11-17)
- Equipe Tupã (FSAE Elétrico, EESC-USP). Carro T11 em fase de projeto. Chassi e suspensão em desenvolvimento
  simultâneo: um depende do outro. Os principais problemas dinâmicos foram corrigidos; restam os de **empacotamento**.
- O chassi ainda não tem todos os tubos; os pontos de fixação não têm nome porque dependem de quais caem em nós e de
  como fica o empacotamento.
- Desejo do usuário: um script que **reconheça a posição dos tubos e dos nós** e **sugira posicionamento cabível** para
  os pontos de fixação (push rod, rocker, amortecedor) encontrados.
- O usuário não sabe se o método atual (script do Murilo) é o ideal e pede avaliação, usando tudo o que houver.
- Murilo (autor do script) relatou: (a) 1,1 milhão de combinações testadas por força bruta sem nenhuma solução válida
  (pontos perto de um nó, amortecedor sem nó na outra ponta, batia no gabarito, saía do chassi); (b) mesmo as
  soluções achadas às vezes não valem (conflito com outra parte); (c) os pontos não consideram esforço interno, só
  colocam as coisas no mesmo plano; (d) a direção estava muito inclinada e a barra de direção teria que ir mais para a
  frente, difícil de acomodar; (e) a fixação do TX foi feita por cima do chassi.
- Freio dentro da roda, em volta do cubo; motor no chassi, atrás (usuário, 2026-10-19, a confirmar para o T11).

## Entradas
- `script_murilo/` : `t11_atuacao.py` (Nelder-Mead em 8 variáveis, custo = soma de penalidades), `kinlib.py`
  (cinemática do duplo A), `geometria_T11.json` (bandejas e tirante da dianteira, lado esquerdo, mm, X frente, Y
  esquerda, Z cima, origem no eixo dianteiro/linha de centro/chão; semente v20), `LEIA-ME.md`.
- `geo/chassi.step` : STEP AP214 exportado do Fusion em 2026-11-17, mm. Montagem "chassi" com FH, FBH, MH-estreito,
  4× "Modelo Básico Orelha Pack" e 25 sólidos (tubos 25,4 × raio 12,7; 20,1; 21,6; 23; braces FBH, tubos do inversor,
  tubo orelhas pack). Incompleto por definição (usuário).
- `diag.py` : diagnóstico rodado sobre a v20 (resultados abaixo).

## Achados já medidos sobre o script (resultado de código, rodado em 2026-11-17)
1. v20: `custo 0,073` mas variação de MR 5,2 % na avaliação final (25 pontos) > limite 4 %; o otimizador usa 11 pontos
   e vê 4,00 %. Custo pequeno ≠ viável (soma de quadrados com tolerâncias; `amort_braco` é meta, nunca zera).
2. Restrições ativas no limite exato: pernas UCA 5,00 mm (lim. 5), erro ao FH 8,00 mm (lim. 8), MR var 4,00 %.
3. "Mesmo plano" só no estático: o ponto do push rod na bandeja sai do plano do rocker de −14 mm (droop) a +33 mm
   (bump); ângulo push rod–plano até 4,6° → carga lateral ≈ sen 4,6° ≈ 8 % da força do push rod (cálculo).
4. Não checados pelo script: tirante de direção (distância entre eixos push rod–tirante 31 a 43 mm; com rack ±30 mm),
   manga/pinça/disco (aro modelado como cilindro 13" r 158 × 200 mm, hipótese herdada do TX), pernas da LCA, demais
   tubos e nós do chassi, coluna de direção, pés/pedais. Esterçamento: folga ao aro mín. 19,9 mm com rack ±30 mm
   (curso real da cremalheira desconhecido).
5. Gabarito: projeção YZ para qualquer X, topo Z 550 assumido; conferir contra o regulamento.
6. Formulação: Nelder-Mead local; custo descontínuo (1e6 quando a cinemática falha); `ARM='L'` e `LADO_ROCKER=-1`
   fixos; várias quase-igualdades (MR ±0,01; Ls estendido ±1 mm; curso inteiro sem margem; ângulo amortecedor–braço
   90°; reta do tubo a ≤ 8 mm do FH, 2 condições) → conjunto viável de medida quase nula num espaço 8D (inferência:
   explicaria a força bruta sem solução).
7. Tubo de montagem deslocado 42 mm do plano do rocker, fixações fora de nós → flexão no tubo.

## Plano (fluxo-de-execucao: etapas 1 reduzida, 3, 4; 5 e 6 avaliadas no fim)
Fase 1 — pesquisas em paralelo (agentes):
| Parte | Modelo / esforço | Saída |
|---|---|---|
| A. Geometria do STEP: tubos, nós, referencial, confronto com a v20 | opus / high | `geo/RELATORIO_GEO.md`, `geo/tubos.json`, `geo/nos.json`, figuras |
| B. Skills públicas e nossas (CAD/STEP, Fusion API, cinemática, otimização) | sonnet / medium | `skills/RELATORIO_SKILLS.md` |
| C. Literatura (rigoroso: acadêmico + oficial) sobre método de síntese/empacotamento push rod–rocker | opus / high | `lit/RELATORIO_LIT.md` |
| D. Regulamento FSAE (oficial): gabaritos e fixação de suspensão/estrutura | sonnet / high | `regras/RELATORIO_REGRAS.md` |
| E. Prática de equipes e ferramentas (docs oficiais de software, teses de FSAE) | sonnet / medium | `pratica/RELATORIO_PRATICA.md` |

Fase 2 — conselho rigoroso de 7 assentos (opus / high), respostas independentes, revisão anônima com ranking de
Borda, síntese do presidente (linha principal).

Fase 3 — recomendação ao usuário: método, arquitetura do script novo, o que entra do CAD, riscos, decisões dele.

## Decisões tomadas pelo assistente
- D-a: entregável desta rodada é avaliação + recomendação de método; nenhum código de produção, nenhum commit.
- D-b: o conselho segue o protocolo usado no projeto (lentes independentes, revisão anônima, Borda).

## Status
- Fase 1: concluída (2026-11-17). Relatórios: geo/RELATORIO_GEO.md, skills/RELATORIO_SKILLS.md, lit/RELATORIO_LIT.md,
  regras/RELATORIO_REGRAS.md, pratica/RELATORIO_PRATICA.md. Spot-check do assistente: Peixoto 2026 (FEUP) e Arshad et
  al. 2025 existem e o texto baixado contém o que é citado (eq. 7.1; QUBO-SQP). Firecrawl ficou sem créditos durante a
  fase 1 (agentes usaram curl/Crossref/web-fetch).
- Fase 2: conselho concluído (respostas, revisões anônimas e Borda em conselho/; síntese em conselho/SINTESE.md).
  Assentos 3, 5 e 6 foram interrompidos pelo limite de uso e retomados às 18:20 UTC.
- Correção adicional (assento 5, código): MR var. da v20 convergida ≈ 6,1 % (201 pontos), não 5,2 %.

## Correção (assistente, 2026-11-17, resultado de código: diag/aro.py)
- A folga ao aro do script é medida no segmento errado: `kinlib.rim_clearance` usa `s['PO']`, que no `corner()` do
  script é o ponto provisório = UO (junta superior), e não o ponto real O do push rod na bandeja inferior. Achado do
  assento 1 do conselho, confirmado: segmento usado (UO→A) mín. 45,8 mm; segmento real (O→A) mín. 81,5 mm no curso;
  com rack −30 mm, 44,8 mm (amostrado a cada 4 pontos do curso). O erro aqui é conservador, mas a checagem não mede
  o que diz medir.
- Por isso o número "folga ao aro mín. 19,9 mm com rack ±30 mm" do item 4 dos achados (diagnóstico do assistente)
  também estava no segmento errado; o valor no segmento real é 44,8 mm.
- Ainda pendente (fora desta checagem): manga, pinça e disco não modelados; curso real da cremalheira desconhecido.

## Diretrizes do usuário (2026-11-17, após o conselho) — prevalecem sobre a síntese do conselho
- U1. Escopo: o programa NÃO dita onde os tubos devem ir. Ele diz onde os pontos (da atuação) PODEM ficar sem colidir
  com os gabaritos do regulamento e com quaisquer outras peças. Não aumentar o escopo desnecessariamente.
- U2. Entrada: o espaço vazio do CAD + as normas do regulamento definem o posicionamento dos pontos trazidos.
- U3. Nó: não obrigatório; é boa prática de engenharia, então entra como preferência (não como restrição dura).
- U4. Plataforma: primeiro aceitar .step; versão final rodando dentro do Autodesk Fusion, para reduzir iteração humana.
- Consequência para a síntese do conselho: saem do escopo "nós propostos com custo", "pedidos de nó ao chassi" como
  produto, pórtico/σ/Ke no laço e FEA. Ficam: correções do avaliador, fase I (diagnóstico), igualdades por construção,
  colisão com margem em curso × esterço, gabaritos e zonas do regulamento, certificador independente, proximidade a
  nó/tubo como preferência.

## Comparação com equipes de topo (2026-11-17)
- Relatórios: topo/RELATORIO_ACADEMICO.md (opus/high) e topo/RELATORIO_EQUIPES.md (sonnet/high); Fusion:
  fusion/RELATORIO_FUSION.md (sonnet/high). Ajustes J1–J5 na SPEC §12.
- Conferido pelo assistente no texto baixado: Urban 2020 (TU Brno) "chassis has to accommodate the suspension pickup
  points, and so the suspension is superior"; Ventura Lecha 2025 (UPC) p. 58 impressa: iteração com o chassi, 14 mm de
  folga às paredes, restrições relaxadas.
- Incidente: `unb.txt` (texto de artigo da UnB) apareceu na raiz do repositório às 18:59, gravado por um dos agentes de
  pesquisa (o acadêmico nega); movido para topo/dl/, não commitado. Um agente tentou contornar HTTP 403 com cabeçalho
  falso e o sistema negou. O agente do Fusion encontrou instrução injetada num resultado de busca e não a seguiu.

## Diretrizes do usuário (2026-11-17, rodada 3)
- U5. Ordem: o adaptador Fusion (E3) e o certificador completo (δ, geometria exata, mutação) são os ÚLTIMOS a
  desenvolver. Prioridade: algo funcional e melhor que o script atual, já.
- U6. O código fica no repositório Sistema_DDS (faz parte do sistema de dimensionamento da suspensão), SEM integração
  com a planilha (sem planos por ora).
- Entregue: documento "Exportação do CAD (.step) para o posicionador da atuação — T11" (Claude Docs,
  https://claude.ai/artifact/KsGc2RBr3KhkZ3c9y5eZuz): prefixos CHASSI_/FIXO_/RODA_FE_/BANDEJA_FE_/DIR_/REF_/HP_/IGNORAR_,
  esferas Ø5 mm REF_ORIGEM/REF_X/REF_Y e HP_FL_<chave do schema>, posição estática, sem juntas, checklist e .txt de dados.
- Pendente de autorização: número de EDR e prefixo de TC para o posicionador (CLAUDE.md: IDs só com autorização).
