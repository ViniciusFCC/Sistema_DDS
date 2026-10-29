# Incremento 7: física da planilha, raio do skidpad e V4.3 (desenho)

Data: 2026-10-29. Brainstorming com o usuário em 2026-10-28 e 2026-10-29, com revisão de um conselho rigoroso (5
assentos, revisão anônima; registro fora do Git, na pasta de notas da sessão). Spec base:
`2026-10-20-v4-0-metas-equilibrio-design.md`; adendo do incremento 6: `2026-10-27-inc6-mmm-escada-design.md`.

Este documento é desenho. Nenhum ID abaixo existe: os IDs da seção 9 são propostas e só passam a existir com a
autorização do usuário. Nenhuma fórmula da planilha muda sem a aprovação célula a célula no plano (CLAUDE.md).

## 1. Decisões do usuário que este desenho segue

| # | Decisão | Data |
|---|---|---|
| U1 | Decomposição: o inc. 7 é a física da planilha e as pendências; o inc. 8 é a fundação parte 2 (fórmulas reescritas para nomes e equivalência por valor no lugar do CA-07 por texto); o inc. 9 é a coerência completa (efeito no objetivo, custo, malha fechada, Δt, estados ao vivo, ficha-exemplo). A spec base punha os três no inc. 7 | 2026-10-28 |
| U2 | O raio do skidpad R sai por dois métodos, os dois implementados: (i) linha central da faixa; (ii) rente aos cones internos, pela fórmula completa (com o comprimento do carro e as duas bitolas, indicando o eixo que manda) | 2026-10-28 |
| U3 | Bitola do T11 provisória: 1300 mm (valor das iterações do Kinematics e do CarSim) | 2026-10-28 |
| U4 | O R entra no relatório da escada (uma rodada por método) e na planilha nova (método e bitolas dianteira e traseira como entradas) | 2026-10-28 |
| U5 | A planilha nova é a **V4.3** (V4.x, com o número depois do ponto em sequência direta da última versão, a V4.2) | 2026-10-28 |
| U6 | Chaves 1/0 só onde a planilha calcula a variante em forma fechada: as duas fórmulas do EDR-066. A chave 1 é a fórmula nova, a 0 é a antiga (para a escada comparar). **Padrão = 1.** As variantes acopladas e o `sentido` (h7) ficam só no Python, com aviso na planilha | 2026-10-28 |
| U7 | Inc. 9: baixar o regulamento da Formula SAE Brasil (download autorizado para o inc. 9); a coerência passa a ser verificada também contra as regras da competição, não só contra a literatura | 2026-10-28 |
| U8 | Desenho revisto pelo conselho aprovado (seções 3 a 7 abaixo): centro de curva único na linha do eixo traseiro; fator 4/3 do NEUTRO reaberto e medido antes; α_R limitado ao pico, com a forma exata como oráculo; chave na tabela `mmm.VARIANTES`; divisão em 7a e 7b; correção do executor dos testes primeiro | 2026-10-29 |
| U9 | Spec aprovada. Meia largura do pneu tirada do `.tir` em uso; posição dos cones conferida no texto do regulamento; a chave 0 pode sair já ou na V5.0 (a planilha do inc. 9): fica até a V5.0 (seção 5) | 2026-10-29 |

Decisões anteriores que continuam: EDR-064 APPROVED; EDR-065 APPROVED em parte (regra do NEUTRO (a); a tolerância
espera o relatório com R); EDR-066 APPROVED em princípio (troca das duas fórmulas no inc. 7, célula a célula).

## 2. Escopo

**7a (só Python, PR próprio, sem planilha nova):**
1. Correção do executor dos testes (seção 6.1) e diagnóstico da mutação que passou de 5 h.
2. `python/skidpad.py`: R pelos dois métodos (seção 3.2).
3. Fórmulas novas no Python, por adição: Ackermann com centro no eixo traseiro e Fx exigido por arrasto induzido
   (seção 4), selecionadas por `mmm.VARIANTES` (seção 5).
4. Estudo da faixa do NEUTRO (seção 4.3), sem mudar a regra ainda.
5. Escada com as linhas da planilha V4.2 e V4.3 e o relatório `docs/inc6/escada-hipoteses.md` com os dois R.

**Passo do usuário entre 7a e 7b:** a tolerância do EDR-065, a faixa do NEUTRO a partir do estudo, a lista de IDs e a
aprovação célula a célula da V4.3.

**7b (V4.3, PR próprio):** `python/gerar_v4_3.py` a partir da tag `v4.2`, com o R calculado, as duas chaves, a faixa do
NEUTRO decidida e os avisos; testes; registro de versões; suíte inteira; migração da viva e documentação do Drive (só
com a confirmação do usuário).

**Fora do escopo:** reescrita das fórmulas antigas para nomes (inc. 8); coerência completa e regras da competição
(inc. 9); chaves para as variantes acopladas e o `sentido`; jacking (EDR-053); refino do pico na planilha, salvo se o
estudo da seção 4.3 o indicar e o usuário aprovar.

## 3. Geometria: centro de curva e raio do skidpad

### 3.1 Centro de curva único (vale para R, Ackermann e Fx)

O conselho achou que a fórmula do Ackermann com β = 0 (centro na linha lateral do CG) deixa, com 100 % de Ackermann, um
resíduo ≈ b·t/R² na dianteira, e que o termo traseiro ±b·t/2R² era artefato dessa escolha. O `mmm.alfa_rodas`
"cinemático" usa o β real (`python/mmm.py:197`). Decisão (U8): **o centro da curva fica na linha do eixo traseiro**
(β cinemático = atan(b/R_c)), a geometria de referência do SUS-414.

Referencial (ISO 8855, curva à esquerda; a direita é o espelho de `equilibrio.espelhar`): origem no ponto médio do
eixo traseiro, X para a frente, Y para a esquerda. Rodas: dianteiras em (L, ±t_f/2), traseiras em (0, ±t_r/2). O CG
está em (b, y_cg). Centro da curva C = (0, R_c). O raio do CG é R = √(b² + (R_c − y_cg)²); com o CG lateral nulo,
R = √(b² + R_c²) e R_c = √(R² − b²).

A velocidade da roda i é perpendicular ao raio C → roda; o ângulo dela em relação ao eixo X do carro é
θ_i = atan(X_i/(R_c − Y_i)). Nas traseiras θ = 0. Nas dianteiras θ_FL = atan(L/(R_c − t_f/2)) e
θ_FR = atan(L/(R_c + t_f/2)), que é exatamente o par do Ackermann ideal (cot θ_FR − cot θ_FL = t_f/L).

Limitação (registrar no EDR): o α_R real desloca o centro para a frente da linha do eixo traseiro; a diferença entre
esta geometria e a do Python "cinemático" (β real) é medida pela escada, não corrigida.

### 3.2 Raio do skidpad (`python/skidpad.py`)

Fonte: Formula SAE Rules 2026, versão 1.0 (10/09/2025), D.10.1.1: círculos internos de 15,25 m de diâmetro, externos de
21,25 m, faixa de 3,0 m, centros a 18,25 m. Texto extraído do PDF; a figura não foi vista; o regulamento da FSAE
Brasil fica para o inc. 9.
Onde ficam os cones (conferido em 2026-10-29, só pelo texto): FSAE D.10.1.2 põe os cones "around the inside of each
inner circle" e a linha de giz "inside the inner circle"; o Formula Student Rules 2026 v1.1 (FSG), D 4.1.3 e 4.1.4 (p.
125), põe os cones "around the inside of each inner circle" e a linha "outside the inner circle". Nos dois, o círculo de
15,25 m é a borda interna da faixa de 3 m e os cones ficam dentro dele: a base do cone fica, no máximo, encostada no
círculo. O modo (ii) usa o círculo como limite, o que é o lado seguro. A figura (que poderia cotar o centro do cone)
não foi vista, e os dois textos divergem sobre o lado da linha marcada. Os diâmetros entram como **entradas com fonte**, não como constantes, para a equipe corrigir sem planilha nova.

Funções (nomes indicativos; o plano fixa as assinaturas):
- `raio_linha_central(d_int, d_ext) = (d_int + d_ext)/4` → 9,125 m. É o raio do CG.
- `raio_rente_aos_cones(d_int, L, b, t_f, t_r, meia_largura_pneu)`: com R_in' = d_int/2 + meia_largura_pneu, cada
  roda interna exige distância ao centro ≥ R_in'. Traseira interna: R_c ≥ R_in' + t_r/2. Dianteira interna:
  √(L² + (R_c − t_f/2)²) ≥ R_in', isto é, R_c ≥ t_f/2 + √(R_in'² − L²) (se R_in' ≤ L, a dianteira não restringe).
  R_c = máximo dos dois; R = √(b² + R_c²). Devolve R, R_c e o eixo que manda ("traseiro", "dianteiro" ou
  "empate"). Esta forma substitui a que foi aprovada em 2026-10-28 (com x_i medido do CG e β = 0), pela decisão U8.
- Meia largura do pneu: WIDTH/2 do `.tir` em uso, `data/Hoosier_R25B_13x7_TTC_provisional.tir` (WIDTH = 0,1778 m,
  "Nominal section width of the tyre", tamanho 177.8/53.6R13), ou seja **0,0889 m**, com origem "◐ pneu de outro
  carro (Hoosier R25B do TTC, provisório, EDR-038)". A largura de seção é a parte mais larga do pneu, a que encosta
  no cone. Quando o pneu do T11 tiver dado, o valor troca pela entrada. Vazia, entra 0 e o resultado é rotulado
  "sem a meia largura do pneu (a confirmar)".
- Modo **manual**: R digitado pela equipe, com origem própria. A planilha tem três modos: linha central, rente aos
  cones e manual.
- Bitola traseira vazia: o R do modo (ii) sai "a confirmar" com o motivo, em vez de supor a dianteira.
- Pior origem do R: a pior entre os diâmetros (regulamento), a bitola (provisória do T11), L e b (demonstrativos do
  T09) e a meia largura; mostrada ao lado do número, não numa aba de notas.
- O caso continua recebendo `raio_m` como número: o `CasoEquilibrio` não conhece o método.

Limitações: o skidpad real tem entrada e saída, e o R é único; o modo (ii) é o limite geométrico de ocupação (piloto
rente ao cone), não a trajetória real.

## 4. Fórmulas novas (EDR-066) e faixa do NEUTRO (EDR-065)

### 4.1 Ackermann (hipótese 2, SUS-414, família F3)

Hoje: Δα_i = toe_i + (δ_i − δ̄), que supõe velocidades paralelas nas rodas do eixo.
Nova (chave 1): Δα_i = toe_i + (δ_i − δ̄_F) − (θ_i − θ̄_F) nas dianteiras e Δα_i = toe_i nas traseiras, com θ_i da
seção 3.1, R_c = √(R² − b²) e θ̄_F a média de θ_FL e θ_FR. Forma fechada por roda, sem iteração.
Consequências: com 100 % de Ackermann o Δα relativo das dianteiras é zero (a menos da diferença entre a média de δ,
amarrada a δ_ref = L/R pela bisseção atual, e a média de θ, de 2ª ordem; o plano mede e justifica a cota); com 0 %
(paralelo) sobra −(θ_i − θ̄_F) ≈ ∓L·t_f/(2R_c²), o termo que a planilha de hoje zera.

### 4.2 Fx exigido na traseira (hipótese 9, EDR-057, família F9)

Hoje: F_x,r = |F_yf|·tan(L/R) + resistências (≈ m·A·b/R).
Derivação conferida pelo conselho (1ª ordem): no balanço F_yf·sen δ − m·A·sen β, com δ = L/R + α_F − α_R e
β = b/R − α_R, os termos em b/R se cancelam e sobra o arrasto induzido **F_yf·|α_F| + F_yr·|α_R|**. O termo de hoje é a
parte que se cancela.
Nova (chave 1): F_x,r = F_yf·|α_F| + F_yr·|α_R| + resistências, com α_F e α_R da grade Fy(α) de cada linha de A (a
grade que a planilha já monta): busca do primeiro α em que a força do eixo alcança a exigida e interpolação linear.
- Para não haver referência circular, α_R sai da curva traseira **sem** o fator de elipse (o fator depende do próprio
  Fx). Aproximação rotulada.
- Se a força exigida passa do pico da curva, α é **limitado ao α do pico** (sem isso a busca falha e um LOOSE pode
  virar N/A). Teste obrigatório do caso LOOSE.
- Omissão rotulada: Σ F_yi·(δ_i − δ̄) por roda (o conselho estima 3 a 4 % do termo; medido pela escada).
- No Python, a forma da planilha é uma réplica; o oráculo é a forma exata no desacoplado (ponto fixo com a elipse) e,
  na escada, o `balanco` acoplado. O Python não copia a aproximação como se fosse a física.

### 4.3 Faixa do NEUTRO (EDR-065 item 2, família F12): reaberta

O fator 4/3 supõe erro liso c·h². O conselho mostrou três problemas (conferidos em `python/equilibrio.py:739-748`): (i)
com as grades aninhadas (passo/2 e 2n−1 pontos), o erro do máximo discreto em α e o da interpolação em a_y dependem da
posição do pico, e |S_h − S_h/2| pode dar ≈ 0 com erro real diferente de zero (a faixa cai no piso de 1e-9 g); (ii) o
veredito compara Δ = S_r − S_f, cujo erro pode chegar a e_F + e_R, com o máximo por eixo; (iii) no ramo em que só um
eixo satura a "resolução" é o próprio passo, onde 4/3 não tem base.

Estudo no 7a (Python, sem mudar a regra): no caso da V4.2 e em casos perturbados (sintéticos, rotulados), grades h,
h/2, h/4 e h/8; ordem observada p e razão das diferenças; frequência de diferença ≈ 0; erro de Δ contra e_F + e_R.
Saem três alternativas para o usuário decidir (a decisão volta ao EDR-065):
1. fator 2^p/(2^p − 1) com o p medido (4/3 se p ≈ 2 de forma estável), só no ramo de Richardson;
2. faixa de Δ com e_F + e_R;
3. refino do pico por parábola de 3 pontos na capacidade (Python e planilha), que tira o serrote; muda a fórmula da
   capacidade e só entra com aprovação.
O ramo de um eixo só continua com o passo. O fator vira constante nomeada lida pela célula e pelo `mmm` (regra da folga
das acopladas, EDR-064 1.3), uma fonte só.

## 5. Arquitetura

- **Chave na tabela `mmm.VARIANTES`, não no `CasoEquilibrio`.** O caso guarda dado físico; a escolha de modelo fica nas
  `Hipoteses`/`VARIANTES`. As entradas `alfa` e `fx_exigido` ganham a variante da V4.2 (a antiga) e a da V4.3 (a nova,
  forma fechada), além da Python. A escada passa a ter as linhas de controle "planilha V4.2" e "planilha V4.3"
  derivadas da mesma tabela; o `assert` de `mmm.py:114` continua valendo.
- **`equilibrio.py` só com adições:** as funções antigas ficam; as novas entram ao lado; o `analise_par` recebe a escolha
  por argumento com padrão igual ao de hoje, de modo que os 28 + 18 checks existentes não mudam. O leitor da planilha
  (`caso_planilha`) devolve a escolha lida das chaves junto com o caso.
- **Chave 0 com prazo (decidido em 2026-10-29):** o usuário deixou a escolha entre retirá-la já ou na V5.0, a planilha
  do inc. 9. Fica até a **V5.0**: a regressão por valor "V4.3 com chave 0 = V4.2" (seção 6.3) é a prova mais forte de
  que só as células aprovadas mudaram e serve de semente à equivalência por valor do inc. 8; o custo é um IF por
  célula. Na V5.0 saem o ramo antigo do Python e do gerador; a tag `v4.2` e o arquivo em `excel/` guardam o
  comportamento antigo.
- **Fonte única do R:** a fórmula da célula sai do gerador e é conferida por teste contra `skidpad.py`.
- **Nomes:** as células novas recebem nomes definidos pelas regras do EDR-058, como na V4.1 e na V4.2 (tabela de nomes
  da V4.3). A reescrita das fórmulas existentes para nomes fica no inc. 8 (U1).

## 6. Verificação

### 6.1 Executor dos testes (primeiro commit do 7a)

Lido no código: `tests/mutation_planilha_equilibrio.py` tem `TIMEOUT = 1500` s por rodada com duas tentativas (linhas 30
e 53-58) e chama o teste com `subprocess.run(..., capture_output=True)`; o `tools/rodar_testes.py` dá 7200 s ao item
(linha 56). Pior caso interno: 6 rodadas × 2 × 1500 s = 18 000 s, as 5 h observadas. Causa provável (não reproduzida):
no tempo-limite só o processo filho morre, e o neto (o Python do teste) segura o pipe, então o `communicate()` depois do
`kill()` não volta. Diagnóstico primeiro (árvore de processos e tempo por rodada), depois a correção:
- saída do filho para arquivo temporário, com hora, em vez de pipe;
- no tempo-limite, encerrar a árvore inteira por PID (nunca por nome de processo);
- orçamentos coerentes (soma interna ≤ externa; a 2ª tentativa só se couber);
- TIMEOUT conta como FAIL e nunca prende a suíte;
- teste do próprio executor: um filho falso que trava com um neto que herda a saída tem de ser encerrado dentro do
  orçamento e contado como FAIL.

### 6.2 Oráculos e testes (7a)

- R: distância da roda interna ao centro (`hypot`) igual a R_in' no eixo que manda; empate frente/trás; R_in' ≤ L;
  bitola traseira vazia; valores da seção 3.2 (9,125 m; com t = 1,3 m e L, b do caso, rotulados).
- Ackermann: oráculo independente pela velocidade de cada roda (ω × r a partir do centro C), sem a fórmula atan; 100 % e
  0 %; curva à esquerda e à direita (sinal no ISO 8855); chave 0 igual ao de hoje.
- Fx: oráculo pelo balanço vetorial exato no desacoplado; a diferença para o arrasto induzido cai como O(α³); ponto fixo
  com a elipse contra a aproximação sem elipse (erro medido, não suposto); caso LOOSE com a força exigida acima do pico.
- Duas réplicas no Python: a de grade (busca e interpolação, igual à célula) para a equivalência célula × Python com
  tolerância apertada; a contínua para a física, com tolerância derivada do passo. Nenhuma tolerância é afrouxada.
- Regressão: com a variante V4.2, os 28 + 18 do equilíbrio, os 11 do MMM e os 3 da escada passam sem mudança.
- Mutação Python: sinal de θ_i, α_F ↔ α_R, sem o limite no pico, fator do NEUTRO ausente, método de R trocado.

### 6.3 Testes da V4.3 (7b)

- Tempo de recálculo medido (`tools/medir_recalculo.py`) antes de aprovar as células da busca de α.
- Regressão por valor: a V4.3 com as chaves em 0 e a V4.2, recalculadas no Excel com as mesmas entradas, têm os mesmos
  valores fora das células novas.
- O diff de texto V4.2 → V4.3 é exatamente a lista de células aprovadas.
- Célula × Python em cada célula nova (réplica de grade), nos dois sentidos de curva e nos três modos de R.
- Os testes da V4.2 que mudam de valor com o padrão 1 são separados em regressão (chave 0) e mudança intencional
  (chave 1).
- Mutação da planilha com mutantes das células novas e orçamento medido antes.
- `migrar_viva`: as entradas novas (modo de R, bitolas, diâmetros, meia largura, chaves) entram com o padrão quando a
  viva da V4.2 não as tem, sem contar como conflito.

## 7. Planilha V4.3 (7b): o que muda, em resumo

O texto exato de cada célula, com a fórmula anterior e a nova, as dependências, a justificativa e o teste, fica no plano,
para a aprovação célula a célula.
- Entradas novas com Origem e Fonte: modo de R (linha central, rente aos cones, manual), diâmetros interno e externo,
  meia largura do pneu, bitola traseira (a dianteira e L, b já existem), R manual, chave do Ackermann e chave do Fx
  (lista suspensa com rótulo em português; o 1/0 é o valor interno).
- Resultados novos: R calculado, R_c, eixo que manda e pior origem do R.
- F3 com a forma nova atrás da chave do Ackermann; F9 com a forma nova atrás da chave do Fx; F12 com a faixa que o
  usuário decidir no estudo.
- Avisos junto de cada veredito (não só no README): o veredito não inclui as hipóteses que ficam só no Python; aviso no
  14_DASHBOARD quando alguma chave estiver em 0 ("resultado não comparável com a V4.3 padrão").
- 00_README e 15_CHANGELOG da V4.3; `docs/registro-de-versoes-V4_3.md` e o arquivo de células.
- Fechamento, só com confirmação: viva do Drive vira a V4.3 com os dados mantidos (`conferir_viva`, `migrar_viva`;
  diretriz de 2026-10-23) e os LEIA-ME e .docx de `Documentacao\` (hoje os da V4.1) são atualizados.

## 8. Ordem de trabalho

1. 7a: executor dos testes (diagnóstico, correção, teste do executor).
2. 7a: `skidpad.py`; variantes e fórmulas novas com oráculos; estudo do NEUTRO; escada com as linhas V4.2 e V4.3;
   relatório com os dois R (em segundo plano: a escada leva ~6 min por rodada).
3. Usuário: tolerância do EDR-065, faixa do NEUTRO, lista de IDs; PR do 7a.
4. 7b: tempo de recálculo; aprovação célula a célula; `gerar_v4_3.py`; testes; cópia para `excel/` em commit próprio.
5. 7b: registro de versões, suíte inteira em segundo plano, PR; Drive só com confirmação.

Commits separados por propósito (executor, física Python, estudo, relatório, gerador, cópia, dados).

## 9. IDs propostos (nenhum criado)

- **EDR-067:** centro de curva único e raio do skidpad (dois métodos e modo manual; fonte D.10.1.1), decomposição dos
  incrementos 7 a 9 e regulamento da FSAE Brasil no inc. 9.
- **EDR-068:** executor dos testes (tempo-limite que encerra a árvore, orçamentos coerentes).
- **Revisão do EDR-065 item 2** (faixa do NEUTRO) com o resultado do estudo, em vez de EDR novo.
- **SUS-1009 a SUS-1011:** raio do skidpad R, eixo que manda, meia largura do pneu.
- **Chaves:** nomes de entrada para as duas chaves (por exemplo h2v e h9v), a definir no plano.
- **TC-SKP-001 a 004** (R), **TC-ACK-001 a 003** (Ackermann), **TC-FXI-001 a 004** (Fx), **TC-NEU-001 a 003** (estudo e
  faixa), **TC-RUN-001** (executor), **TC-WB43-001 a 008** (V4.3).

## 10. Incrementos seguintes (registro)

- **Inc. 8 (fundação parte 2):** reescrita das fórmulas da planilha para nomes, conversão mecânica pelo leitor de
  `python/raizes.py`, cada fórmula registrada; equivalência por valor no lugar do CA-07 por texto, com a regressão por
  valor da seção 6.3 como semente.
- **Inc. 9 (coerência completa):** efeito no objetivo, custo, malha fechada, Δt, estados ao vivo, ficha-exemplo; baixar
  o regulamento da Formula SAE Brasil e verificar a coerência também contra as regras da competição (U7), incluindo a
  conferência da geometria do skidpad da seção 3.2.

## 11. Pendências e limitações registradas

- Tolerância do EDR-065: decisão do usuário a partir do relatório com os dois R.
- Faixa do NEUTRO: decisão do usuário a partir do estudo (seção 4.3).
- A meia largura do pneu vem do `.tir` provisório (outro pneu); a figura do skidpad não foi vista.
- Versão do inc. 9: V5.0 (usuário, 2026-10-29).
- O centro na linha do eixo traseiro despreza o deslocamento causado por α_R; o skidpad real tem entrada e saída; a
  bitola de 1300 mm é provisória e L, b são do T09 (demonstrativos).
- Fora do escopo da re-revisão do inc. 6 e ainda abertos: linha de controle e planilha só à esquerda; `fx_exigido=
  "edr057"` no acoplado usa A e não a_y; `_k_e_si` pode transformar `TireRangeError` em exceção; coeficientes
  combinados do `.tir` com origem "não determinada".
- MAPA.md a regenerar na pasta principal depois do merge do PR do inc. 6.
