# Especificação: planilha V4.0, bloco de metas e equilíbrio em regime permanente

**Data:** 2026-10-20. **Situação:** desenho aprovado seção a seção no brainstorming (usuário, 2026-10-20);
esta especificação aguarda a revisão do usuário. Nada aqui está implementado. IDs novos (TARGET-, SUS-, EDR-)
aparecem como **propostos** e só nascem com autorização; fórmulas novas e reescritas também dependem de aprovação
explícita (CLAUDE.md, regras de trabalho).

**Leitura prévia:** `docs/arquitetura-planejada.md` (roadmap do Guia e V0-V5, onde o projeto está).

## 1. Objetivo e critério de sucesso

**Objetivo (usuário):** ajudar a equipe a **escolher** metas, e não só a conferir resultados. Vale para todas as
metas pertinentes; começa pelo equilíbrio. O resultado, o método, o processo e a implementação precisam
resistir a um avaliador exigente (régua: estilo de juiz de Design FSAE, como Claude Rouelle).

**Sucesso:** com os dados do TX, a equipe muda a barra (ou o λ_f) e vê, na planilha, o gradiente de subesterço e
o comportamento no limite (push ou loose, e quanto) mudarem; escolhe um ponto sobre a curva de troca e o
justifica com número, fonte e EDR. A planilha e o Python concordam, e a distância entre a simplificação da
planilha e o modelo mais fiel do Python é medida por teste.

**Requisito explícito do usuário (passo 2):** a planilha precisa dizer com clareza se o carro é under ou
oversteer no limite e o quanto.

## 2. Escopo

**Dentro:** processo comum de metas (fichas, lógica entre fichas, estados); equilíbrio linear (gradiente de
subesterço) e no limite (análise de par do Milliken na planilha, MMM no Python); fundação da planilha V4.0
(nomes definidos, dados por chave, equivalência por valor); correções de documentação já aprovadas (seção 12).

**Fora:** dinâmica transitória e amortecedores ([GUIA] §1.5; Milliken p. 283); CarSim; otimização formal com
função-objetivo e pesos; compliance (sem dado); Mz no momento de guinada (Mz do PAC2002 não verificado,
EDR-037); conversão do custo em pontos de competição (depende do melhor tempo dos concorrentes); redesenho
estético da planilha (fase própria, mais tarde; a V4.0 só remove as travas que impediriam essa fase).

## 3. Decisões tomadas no brainstorming (usuário, 2026-10-20)

| # | Decisão | Origem |
|---|---|---|
| D1 | Equilíbrio em dois regimes: linear (passo 1) e limite (passo 2) | resposta (C) |
| D2 | Especificação 1 = processo comum + equilíbrio; as demais metas, uma especificação cada | resposta (A) |
| D3 | Ficha de meta e três níveis (objetivo → comportamento → parâmetro); a meta fica no comportamento e o parâmetro sai do modelo | aval da seção 1 |
| D4 | Lógica entre fichas: "medir, não travar" (conselho de 5 lentes, seção 5) | pedido de conselho e aval |
| D5 | Passo 1 pelo Gillespie cap. 6, com Ky do PAC2002 em vez do polinômio do livro | aval da seção 2 |
| D6 | Passo 2 pela análise de par do Milliken cap. 7 (§7.1 na planilha; §7.2 e MMM do cap. 8 no Python), com escada de modelos | aval da seção 3 revisada; "com uma comprovação da simplificação através do teste" |
| D7 | Liberdade para reorganizar a planilha inteira; V4.0 gerada a partir da tag `v3.0` com nomes definidos e dados por chave | aval da seção 4 |
| D8 | Escada de modelos sem programa à parte: chaves de hipótese na planilha + teste na suíte | aval da seção 4 |
| D9 | Domínio de ID próprio para o equilíbrio (revisão do EDR-005) | resposta (A) |
| D10 | A próxima planilha é a V4.0 (o "V3.1" dos documentos da V3.0 passa a V4.0) | instrução do usuário |
| D11 | Correções aprovadas, para fazer depois: EDR-034 sem proposta escrita; arquitetura §3 com "Validation = STALE" | "pode fazer as duas correções, mas não agora" |

## 4. Processo comum de metas

### 4.1 Três níveis

1. **Objetivo:** o que o carro precisa fazer (prova ou uso: skidpad, autocross, endurance/eficiência,
   previsibilidade para o piloto). A lista de objetivos é decisão da equipe, registrada em EDR; os nomes das
   provas vêm do regulamento.
2. **Comportamento:** grandeza física que se pode medir no carro (gradiente de subesterço, push/loose no limite,
   gradiente de rolagem, frequências).
3. **Parâmetro:** hardware ou acerto (mola, barra, MR, geometria). Sai do modelo no Design Mode; não é digitado
   como meta (a nota da 03_TARGETS A12 já aplica essa regra à mola e ao MR).

### 4.2 Escolha de uma meta: o processo do Guia

Cada meta segue os oito passos do [GUIA] G.3: definir o requisito de comportamento; avaliar pneus e uso do
carro; avaliar massa e envelope de suspensão; comparar literatura e experiência anterior; estudar
sensibilidade; propor faixa; validar contra embalagem e hardware; aprovar e congelar. A ficha (4.3) é o registro
desses passos. Regra de promoção ([GUIA] F.3): uma meta só entra como decisão com responsável, justificativa,
faixa ou valor, fonte ou racional, revisão e estado.

### 4.3 Ficha de meta

Ficha curta na planilha (aba de metas); ficha completa em `docs/metas/TARGET-xxx.md`.

| Campo | Conteúdo |
|---|---|
| Objetivo atendido | Nível 1, em uma frase |
| Grandeza | ID TARGET- e o SUS- que a calcula |
| Papel | META ou CONSEQUÊNCIA (seção 5) |
| Alavanca | Parâmetro que a meta comanda (mapa da seção 5) |
| Método | Equação com livro e página, conferida na imagem do PDF |
| Modelo | Função do Python (VERIFIED) e nome da célula na planilha |
| Compromisso | O que piora quando ela melhora; tabela de troca |
| Faixa da literatura | Só com página; sem fonte, "sem faixa na literatura". Faixa de outro tipo de carro não vale (por exemplo, a especificação de Olley, carro de passeio, citada pelo Milliken) |
| Valor escolhido | Valor, justificativa, responsável, EDR |
| Sensibilidade | Entradas que mais pesam e a pior origem delas |
| Verificação no carro | Teste que confirma (para o equilíbrio: raio constante, Gillespie p. 227-228) |
| Estados | Ciclo de vida da meta, congelamento, validação, coerência (4.4) |

### 4.4 Estados (definições para consulta)

Quatro grupos independentes, que nunca se misturam. Os três primeiros já existem; o quarto é novo.

**Ciclo de vida da meta** ([GUIA] G.1). *Muda em relação ao brainstorming:* a seção 1 aprovada usava o ciclo
de parâmetros (OPEN → DRAFT → CHECKED → FROZEN); o Guia tem um ciclo próprio para metas, e esta especificação
propõe adotá-lo. **Confirmar na revisão.**

| Estado | Significado |
|---|---|
| TBD | Valor ainda não definido |
| OPEN | Discussão ativa |
| PROPOSED | Proposta submetida (ficha completa, passos G.3 1-6 feitos) |
| APPROVED | Decisão tomada pelo responsável, com EDR |
| FROZEN | Baseline do ciclo |
| STALE | Não representa a configuração atual |

**Congelamento** ([GUIA] §3.2): F0 aberto, exploração; F1 conceito definido; F2 especificado (pode ser
implementado); F3 implementado e verificado internamente (alimenta análises internas); F4 congelado para o uso
definido (baseline do ciclo). Promoção proporcional ao uso ([GUIA] §3.12). Proposta para o EDR-034: adotar
F0-F4 com essa regra.

**Ciclo de vida de parâmetros** (arquitetura §3): OPEN, DRAFT, CHECKED, FROZEN, STALE. **Validação**
(modelo × referência): NOT_VALIDATED, PASS, WARNING, FAIL (FAIL = não validado, não "modelo errado").
**Registro de decisão** (EDR §1): PROPOSED, AWAITING_DECISION, PENDING_CONFIRMATION, APPROVED_WITH_CONDITIONS,
APPROVED, IMPLEMENTED, VERIFIED (não implica validação física), SUPERSEDED, REOPENED.

**Coerência da ficha** (novo; nomes a confirmar):

| Estado | Significado |
|---|---|
| COERENTE | Nenhuma regra violada; resíduo da malha fechada dentro da tolerância numérica |
| COMPROMISSO DECLARADO | Há custo (incoerência do tipo c), com justificativa e um EDR que existe e está aprovado |
| CONFLITO | Impossibilidade (tipo b) ou custo sem justificativa |
| NÃO AVALIÁVEL | O modelo não cobre o objetivo (por exemplo, transiente) |

Ao lado de qualquer estado de coerência aparece a pior origem das entradas ("COERENTE · ○ demonstrativo").

## 5. Lógica entre fichas (veredito do conselho)

Conselho de 5 lentes (Pragmático, Cético, Arquiteto, Usuário/Produto, Dinâmica veicular), revisão anônima;
ordem sem voto próprio: Cético > Usuário > Dinâmica > Arquiteto > Pragmático. Base: Milliken p. 313 (neutro no
limite é o objetivo "salvo preferência do piloto") e o precedente do projeto (`docs/revisao-metodologica.md:80`,
TLLTD não adotado por ser target sem decisão da equipe).

1. **Três tipos de incoerência.** (a) Erro de categoria (grandeza fora do regime, "final understeer" usado no
   linear, meta posta num parâmetro): vocabulário fechado e fórmula de checagem, porque colar por cima passa pela
   validação de dados. (b) Impossibilidade: duas METAs na mesma alavanca (sobredeterminação), neutro inalcançável
   na faixa de regulagem, velocidade crítica abaixo da velocidade do evento (Gillespie p. 203-204): CONFLITO.
   (c) Troca de valor (push por preferência do piloto, skidpad × endurance): nunca conflito automático; mostra o
   custo e exige justificativa com EDR para promover a ficha. A nota 35 do Milliken (p. 313) trata de curva
   limitada por potência e **não** justifica push no skidpad; lá o push só se justifica por piloto ou segurança.
2. **Papel META/CONSEQUÊNCIA e mapa meta → alavanca.** Duas METAs na mesma alavanca: "escolha qual manda". Com
   uma meta de gradiente de subesterço ou de limite, o λ_f (TARGET-003) passa a CONSEQUÊNCIA.
3. **Tabela de troca:** varredura da alavanca livre (começa pela barra dianteira) com λ_f, K, a_y de saturação de
   cada eixo, push/loose e C_N. Os valores da grade são grade de exibição rotulada, não metas.
4. **Custo do comportamento:** a_y do acerto neutro (cruzamento das saturações na tabela de troca, por
   interpolação) menos a_y limite. Não é a diferença entre as saturações dos dois eixos (superestima a perda).
5. **Limiar:** só por EDR da equipe; até lá a célula mostra o custo sem veredito ("limiar não definido").
6. **Malha fechada no parâmetro:** o parâmetro derivado e o valor real do setup (mola de catálogo, barra
   disponível) voltam para o modelo direto; a ficha mostra o resíduo.
7. **Coerência por Setup:** dois acertos legítimos (skidpad e endurance com barra regulável) não se travam.
8. **Regras como dados:** tabela esparsa de relações na planilha (aba de listas), cada linha com fonte L
   (livro e página), E (EDR) ou M (cálculo, nome da célula). Linha sem fonte não existe; ausência de linha = "não
   avaliado", nunca "ok". Testes conferem a fonte de cada linha e que todo EDR citado existe e está aprovado.
9. **Hierarquia entre objetivos sem pesos inventados:** só pelos pontos máximos de cada prova no regulamento
   (fato com fonte; página a confirmar).
10. **Processo humano:** a especificação de cada meta define quem revisa a promoção; uma ficha-exemplo didática,
    rotulada como demonstrativa, mostra o padrão.

## 6. Passo 1: equilíbrio linear (gradiente de subesterço K)

**Base:** δ = 57,3·L/R + K·a_y (Gillespie eq. 6-15, p. 202); parcelas na tabela-resumo (p. 226).

| Parcela | Equação (Gillespie) | Página | V4.0 |
|---|---|---|---|
| Pneus + transferência lateral | K = D_f − D_r, com D_eixo = W_eixo / C_eixo e C_eixo = Ky(Fz_ext, γ_ext) + Ky(Fz_int, γ_int) | 202, 213, 215-217 | Calcular, forma exata pelo PAC2002 |
| Decomposição | K_tires = mesma conta no Fz estático; K_llt = (pneus + transferência) − K_tires | 202, 217 | Calcular, para explicar |
| Camber | (C_γf/C_αf·∂γ_f/∂φ − C_γr/C_αr·∂γ_r/∂φ)·∂φ/∂a_y | 218-219 | Calcular; sinal amarrado ao EDR-002 por teste (γ_solo = γ_carroceria + φ, eq. 6-50) |
| Roll steer | (ε_f − ε_r)·∂φ/∂a_y | 220 | Já existe (SUS-415) |
| Torque de alinhamento | W·(p/L)·(C_αf + C_αr)/(C_αf·C_αr) | 222 | N/A: Mz não verificado |
| Compliance lateral e da direção | — | 221, 226 | N/A: sem medição |
| Força de tração | — | 222-223 | N/A até haver dado de arrasto |

- **Definição:** a SAE define o gradiente como derivada (Gillespie p. 227). Tabela de a_y de 0 a 0,4 g (faixa
  linear, Milliken p. 315): K em a_y → 0 e K tangente por diferença entre linhas. Acima disso vale o passo 2.
- **K do passo 1 = inclinação inicial das curvas de eixo do passo 2** (seção 7). Um teste exige igualdade.
- **Exibição:** "K = +x °/g (pneus + transferência + camber + roll steer; sem compliance, torque de alinhamento e
  tração)", nunca "K total" com parcela faltando; parcelas lado a lado com porcentagem; rótulo Subesterço /
  Sobresterço pelo sinal (banda de neutro só por EDR); velocidade característica (K > 0) e crítica (K < 0)
  (Gillespie p. 203-204); pior origem ao lado.
- **Verificação cruzada pela forma do livro:** ajustar o polinômio C_α = a·Fz − b·Fz² ao Ky do PAC2002 e
  conferir o K_llt aproximado do Gillespie contra o exato onde C_α ≫ 2b·ΔFz².

## 7. Passo 2: equilíbrio no limite

### 7.1 Método da planilha: análise de par (Milliken §7.1, p. 283-286)

Para cada linha de a_y (0 a cerca de 2 g):

1. Fz das quatro rodas (SUS-103/104 com aero do Setup; CG lateral; aero com V = √(a_y·R)).
2. Camber de cada roda: estático + ∂γ/∂φ·φ(a_y).
3. Para cada eixo, varredura de um α de referência comum (cerca de 25 colunas), com o deslocamento de cada roda
   por toe estático e Ackermann (SUS-414, no esterço do skidpad); Fy dos dois pneus pelo PAC2002; soma × cos δ
   de referência ÷ W_eixo = curva de coeficiente de curva do eixo (a_y do eixo × α).
4. Capacidade do eixo = máximo da curva. Termos do PAC2002 que dependem só do Fz são calculados uma vez por linha;
   só a fórmula final depende de α.
5. Força exigida: F_yf = m·a_y·b/L, F_yr = m·a_y·a/L. Saturação de cada eixo: a_y em que a capacidade iguala a
   exigência (interpolação entre linhas). a_y limite = o menor. PUSH se a frente satura antes; LOOSE se a
   traseira.

O pico de Fy de cada pneu também tem forma fechada (D_y + S_Vy quando C ≥ 1; PCY1 = 1,42 no `.tir` atual), usada
como teste do máximo numérico.

### 7.2 O "quanto"

| Número | Para quem | Definição | Fonte |
|---|---|---|---|
| C_N residual no limite | Avaliador | Folga do eixo não saturado × distância ao CG ÷ (W·L); positivo = push (estabilizante) | Milliken §8.4, p. 311-312; C_N = N/(W·ℓ), cap. 5 |
| Perda de a_y em relação ao neutro | Equipe | Seção 5, item 4 | Conselho |
| Δt no skidpad | Equipe e juiz | t = 2π√(R/a_y) | R do regulamento, a confirmar |

### 7.3 Exibição (requisito do usuário)

1. Célula principal por fórmula: "▲ PUSH: sai de frente (final understeer)", "▼ LOOSE: sai de traseira (final
   oversteer)", "● NEUTRO no limite", "N/A: \<motivo\>". Termo principal pelo Milliken p. 315 (push/loose no
   limite; under/oversteer reservado ao linear), com nota na célula; termo entre parênteses para familiaridade.
2. Linha de apoio: saturação de cada eixo, a_y limite, C_N, perda em relação ao neutro, Δt.
3. Cor só como reforço: azul para push, laranja para loose (par legível para daltônicos); símbolos para P&B.
4. NEUTRO só quando a diferença entre saturações for menor que o passo da rampa (resolução numérica) ou que uma
   banda registrada em EDR.
5. Linear e limite lado a lado, com "regimes diferentes (Milliken p. 313-315)"; subesterço linear com loose no
   limite não é marcado como erro.
6. Pior origem ao lado.

### 7.4 Hipóteses

| # | Hipótese | Base | Planilha | Python | Efeito se ignorada |
|---|---|---|---|---|---|
| 1 | α comum por eixo com deslocamento por roda | Milliken §7.1 | Sim | Sim (α por roda pelo MMM) | — |
| 2 | Toe e Ackermann por roda | §7.1 | Sim (toe digitado; Ackermann SUS-414, precisa do R) | Sim | Muda a capacidade da frente |
| 3 | cos δ na frente | §7.1 | Sim | Sim | Superestima a frente (ordem de 1,5 % com δ ≈ 10°, estimativa a medir) |
| 4 | Camber em curva | Gillespie eq. 6-50; §7.2 | Linear | Não linear | Capacidade |
| 5 | Três massas, RC fixo, rolagem linear | EDR-009/011 | Sim | RC(φ), K_φ(φ) | Cresce com a rolagem |
| 6 | Termo gravitacional da rolagem | EDR-046 | Sim | Sim | — |
| 7 | CG lateral, dois sentidos de curva | §7.2 | Sim (entrada, 0 até medir) | Sim | Um sentido piora |
| 8 | Aero com V = √(a_y·R) | Milliken cap. 3; EDR-013 | Sim (CzA, balanço, R; 0 ou a confirmar) | Sim | Subestima a_y em alta velocidade |
| 9 | Força de tração na traseira | Gillespie p. 222; §7.1 | Elipse de atrito (Milliken §2.7), Fx por arrasto, rolamento e Fy_f·sen δ; CdA e Crr a confirmar | PAC2002 combinado | Superestima a traseira (puxa para push) |
| 10 | Diferencial | Milliken cap. 20 | Aberto, declarado; tipo real a confirmar | Aberto, autoblocante, travado | Travado puxa para push |
| 11 | Transferência longitudinal pela tração | cap. 18 | Não (limite declarado) | Sim | Pequena; medida |
| 12 | Jacking | Milliken p. 615 | Não | Sim (linha de força, EDR-053) | Altura e camber |
| 13 | Compliance | §7.1; cap. 23 | Não | Só com K&C | Desconhecido, declarado |
| 14 | Mz no momento de guinada | Gillespie p. 222 | Não | Não (Mz não verificado) | Pequeno no linear (< 0,5 °/g, Gillespie) |
| 15 | Pressão, temperatura, superfície | Milliken cap. 2 | Igual | Igual | Mais no a_y absoluto que no equilíbrio; rotular "pneu de teste" |
| 16 | Amortecedor e transiente | Milliken p. 283 | Não | Não | Declarado |

### 7.5 Escada de modelos

1. O Python na configuração da planilha bate com a planilha na tolerância numérica (padrão CA-09).
2. O Python liga uma hipótese por vez e mede o efeito em a_y de saturação de cada eixo, push/loose, C_N e K
   (orçamento de erro).
3. Critério: a planilha completa dentro de uma tolerância em relação ao Python completo e **nunca** inverter
   push e loose. A tolerância é decisão de engenharia (EDR do usuário); até lá a tabela mostra números sem
   veredito.
4. Hipóteses sem dado: sensibilidade por unidade (por 100 N de Fx, por 10 mm de CG lateral), sem faixa inventada.
5. Com dados do TX a escada roda de novo; a conclusão vale para os dados testados, com a pior origem registrada.

Implementação: chaves 1/0 na planilha para as hipóteses que ela implementa; `tests/test_escada.py` na suíte para o
resto. Nenhum número do Python é copiado para a planilha (valor estático envelhece em silêncio).

## 8. Arquitetura

### 8.1 Python

| Arquivo | Papel |
|---|---|
| `python/equilibrio.py` (novo) | Análise de par §7.1: cargas por a_y, curva de eixo, capacidade, saturações, push/loose, C_N, K pela inclinação, decomposição do Gillespie, tabela de troca. Funções puras, SI. Oráculo da planilha |
| `python/mmm.py` (novo) | Milliken §7.2 e cap. 8: grade β × δ, α por roda, equilíbrio C_N = 0, a_y máximo em equilíbrio, momento residual; chaves por hipótese |
| `python/tire_model.py` | + Ky(Fz, γ) e C_γ |
| `python/kinematics_model.py` | + ∂γ/∂φ pela varredura |
| `python/suspension_model.py` | Sem mudança no que existe; CG lateral e aero por velocidade em funções novas |
| `python/gerar_planilha.py` e extrator/injetor por nome (novos) | Fundação da V4.0 (8.2) |

### 8.2 Planilha V4.0

- Gerada a partir do arquivo da tag `v3.0` (reabre o EDR-051: a alternativa "parte da tag e os dados entram por
  chave" vira o caminho principal).
- **Nomes definidos** em todas as entradas e resultados; fórmulas reescritas para usar nomes (conversão mecânica
  pelo leitor de referências de `python/raizes.py`, cada fórmula registrada com aba, célula, antes e depois).
- **Dados por chave:** extrator lê a viva pelos nomes; o gerador injeta pelo mesmo nome.
- **Equivalência por valor** no lugar do CA-07 por texto: com as entradas da V3.0 de referência, todo resultado com
  nome tem o mesmo valor na V4.0. Testes passam a ler por nome (fim da dependência de `layout_V2_4.json`).
- Renomear abas e reorganizar passa a ser permitido. Abas novas: equilíbrio (rampa, curvas, K, limite, chaves de
  hipótese, tabela de troca) e listas (vocabulário, relações L/E/M, mapa meta → alavanca). Metas: linhas novas e
  colunas da ficha. Dashboard: K, limite, pior coerência, contador de compromissos.
- Entradas novas com Origem e Fonte e incluídas na lista de células de entrada: toe por roda, raio do skidpad, CG
  lateral, aero do Setup, CdA e resistência ao rolamento, tipo de diferencial, justificativa, EDR e responsável
  nas fichas.
- A equipe continua na V3.0 viva até o incremento 7; só então há retrato, congelamento do preenchimento e
  injeção dos dados. O local oficial da viva precisa estar decidido antes do retrato.

### 8.3 Documentação

`docs/metas/README.md` (processo, níveis, ficha, estados, F0-F4); `docs/metas/TARGET-xxx.md` e ficha-exemplo;
`docs/metas/orcamento-de-erro.md` (gerado só ao registrar evidência); fichas novas no Standard;
`docs/registro-de-versoes-V4_0.md`.

## 9. Testes

1. **Oráculos da literatura** (estendem `tools/oraculos_literatura.py`): exemplo resolvido do Gillespie cap. 6
   (p. 231-233: pesos por eixo, rigidez de deriva por carga, K, velocidade característica); exemplo de
   transferência do Milliken p. 683 (já existe); pico em forma fechada × máximo numérico.
2. **Física:** eixos idênticos dão K = 0 e neutro; mais barra dianteira aumenta K e empurra para push (Gillespie
   p. 214); K_llt aproximado × exato; sinal do camber; K pela inclinação = soma das parcelas.
3. **Equivalência V4.0 × V3.0** por valor; ida e volta dos dados da viva por chave.
4. **Planilha × Python** em cada bloco novo, recalculado por Excel (COM) e LibreOffice (EDR-044); NÃO EXECUTÁVEL
   não conta como aprovado.
5. **Escada** (7.5).
6. **Metas:** fonte em toda relação; EDR citado existe e está aprovado; sobredeterminação; cada estado de
   coerência forçado; valor fora do vocabulário colado por cima é pego.
7. **Rotulagem:** nenhum resultado novo sem pior origem.
8. **Mutação** (estende a 25/25): trocar a por b na força exigida, tirar cos δ, inverter Ackermann ou camber,
   trocar a pior origem.
9. **Salvar pelo Excel:** nomes, validações e formatação condicional sobrevivem (como no EDR-051 para a V3.0).
10. **Desempenho:** tempo de recálculo no log; limite só por decisão registrada.

Verificação no carro (fora da suíte): teste de raio constante quando houver carro e aquisição; até lá
Validation = NOT_VALIDATED.

## 10. Ordem de entrega

| # | Incremento | Entrega |
|---|---|---|
| 1 | Viabilidade | Protótipo descartável da análise de par no Excel e no LibreOffice: tempo de recálculo, α do pico dentro de ALPMAX. Relatório "vai ou não vai"; se não for, a alternativa (tabela do Python) é decisão do usuário |
| 2 | Fundação V4.0 | Gerador, nomes, chave, equivalência; nenhuma grandeza nova |
| 3 | Metas, estrutura | `docs/metas/`, F0-F4 (EDR-034), aba de listas, META/CONSEQUÊNCIA, sobredeterminação, fichas das metas atuais e das novas (K e limite, TBD) |
| 4 | Equilíbrio no Python | `equilibrio.py`, Ky, C_γ, ∂γ/∂φ |
| 5 | Equilíbrio na planilha | Aba de equilíbrio, exibição, chaves, tabela de troca, dashboard |
| 6 | MMM e escada | `mmm.py`, `test_escada.py`, orçamento de erro, EDR da tolerância |
| 7 | Coerência completa e fechamento | Efeito no objetivo, custo, malha fechada, Δt, estados ao vivo, ficha-exemplo, retrato e injeção da viva, registro de versões, tag `v4.0` |

Cada incremento: branch própria, PR, suíte inteira passando, commits separados por propósito (CLAUDE.md).

## 11. IDs e EDRs propostos (nenhum criado)

- **EDRs:** processo de metas e coerência; método do equilíbrio (análise de par na planilha, §7.2/MMM no Python,
  escada); tolerância da escada (decisão do usuário); revisão do EDR-005 com a faixa nova; EDR-051 reaberto
  (caminho por chave); EDR-034 resolvido com F0-F4; lista de objetivos da equipe.
- **Faixa de ID:** domínio próprio "Equilíbrio / dirigibilidade" (decisão D9). Número a confirmar (por exemplo
  SUS-10XX: as faixas 0XX a 9XX estão ocupadas).
- **TARGET:** gradiente de subesterço; comportamento no limite.
- **Prefixo das relações de coerência** (por exemplo REL-): só com autorização; até lá, numeração interna da tabela.

## 12. Correções de documentação aprovadas (fazer depois, D11)

1. EDR-034: registrar que a proposta citada (`kinematics-exploratory-and-promotion-V2.1.md` §F) nunca existiu; os
   critérios passam a ser os desta especificação (4.4).
2. Arquitetura §3: "Validation = STALE" → STALE é estado de ciclo de vida.

Achados ainda sem aprovação (só registrados): a proposta da Decisão C (EDR §4) usa SUS-414 a 416, já ocupados pelo
EDR-052; o cabeçalho do índice do EDR está desatualizado (53 registros: 16 VERIFIED, 7 APPROVED_WITH_CONDITIONS,
6 AWAITING_DECISION); o EDR-041 ainda cita o fundo amarelo; a §3 do EDR lista o EDR-025 e o EDR-035 como
pendentes.

## 13. Riscos e premissas

- A análise de par pode ficar pesada no Excel ou no LibreOffice (incremento 1 decide).
- A justificativa pode virar carimbo: teste de EDR existente e aprovado; contador de compromissos no dashboard.
- Fadiga de alerta com dados demonstrativos: rótulo de origem ao lado, nunca no lugar do veredito.
- O custo depende principalmente da sensibilidade do pneu à carga, a parte menos confiável do `.tir` do TTC; a
  ficha diz isso.
- Listas dependentes (INDIRECT/FILTER) ficam fora (frágeis no LibreOffice e no openpyxl).
- A reescrita das 387 fórmulas para nomes é mecânica, mas grande; a equivalência por valor é a rede de segurança.
- Tudo é regime permanente: "skidpad coerente" não é "carro coerente".

## 14. Pendências do usuário

1. Revisar esta especificação.
2. Adotar o ciclo de vida de metas do Guia (G.1) no lugar do de parâmetros (4.4).
3. Número da faixa de ID do equilíbrio.
4. Tolerância da escada (pode esperar o incremento 6).
5. Local oficial da planilha viva (antes do incremento 7).
6. Lista de objetivos da equipe e responsável por cada meta.
7. Pendências de `docs/arquitetura-planejada.md` §7 (roadmap canônico e separação das numerações).

## 15. Fontes

[GUIA] *Guia Definitivo de Dimensionamento Dinâmico da Suspensão*, EESC-USP Tupã (`references/pdf/`). Milliken &
Milliken, *Race Car Vehicle Dynamics*, SAE, 1995: cap. 2 (§2.7), 5, 7 (p. 279-288), 8 (§8.4-8.5, p. 311-315),
18, 19, 20, 23. T. D. Gillespie, *Fundamentals of Vehicle Dynamics*, SAE: cap. 6 (p. 202-233). Equações a
conferir na imagem do PDF antes da implementação (CLAUDE.md). Nesta sessão, o Milliken e o Gillespie foram lidos
só no OCR (`references/md/`), sem conferência na imagem; do Guia, as folhas 23-25, 32-34, 43-44 e 136-137 foram
conferidas na imagem.
