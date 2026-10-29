# Adendo da especificação: incremento 6, MMM e escada de hipóteses

**Data:** 2026-10-27. **Situação:** arquitetura aprovada pelo usuário em 2026-10-27, depois de um conselho rigoroso de
5 assentos, cujas conclusões estão incorporadas aqui. Este adendo aguarda a revisão do usuário antes do plano de
implementação. Nada aqui está implementado. IDs novos (EDR-, TC-) aparecem como **propostos** e só nascem com
autorização (CLAUDE.md, regras de trabalho).

**Base:** `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` (a "spec base"), em especial §7.4
(hipóteses), §7.5 (escada), §7.6 (robustez ao pneu), §8.1 (arquitetura Python), §9 (testes) e §10, linha 6. O que
este adendo não muda continua valendo como está na spec base.

## 1. Escopo e desvios em relação à spec base

O incremento 6 é **só Python**: não sai planilha nova (V4.3) e nenhuma fórmula da planilha muda (usuário,
2026-10-27).

| # | Spec base | Este adendo | Por quê |
|---|---|---|---|
| A1 | §7.5: chaves 1/0 na planilha para as hipóteses que ela implementa | As chaves h2, h3, h7, h8 e h9 já existem na V4.1 (`caso_planilha.caso_da_planilha_v41`). A variante "planilha" de cada hipótese é o `CasoEquilibrio` como a planilha o monta (campo `None` = desligada), e as variantes Python ficam só no Python. Chaves novas na planilha ficam para o incremento 7 | Usuário, 2026-10-27: incremento 6 só no Python; correção pela decisão 1 do plano (EDR-064) |
| A2 | §8.1: `mmm.py` com "grade β × δ" como núcleo | O núcleo é a curva de trim em raio fixo, parametrizada por A_Y. A grade fica para o diagrama e para um teste | Mais robusto perto do pico, que é onde o resultado interessa (§4) |
| A3 | §8.1 e §10 citam só `mmm.py` e `tests/test_escada.py` | Mais `python/escada.py` (orquestração), `tests/test_mmm.py` (física) e `tools/relatorio_escada.py` (relatório) | Física e orquestração testadas em separado; a tabela da escada precisa de um relatório legível para a decisão da tolerância |
| A4 | §7.4: hipóteses ligadas ou desligadas | Cada hipótese tem **variantes** (planilha × Python) | A planilha já implementa as hipóteses 1, 2, 3, 6, 7, 8 e 9; "tudo desligado" não é a planilha |
| A5 | §7.5 item 2: uma hipótese por vez | Uma variante por vez **e** "todas as variantes Python" contra a planilha | As hipóteses não se somam (1 × 2, 3 × 9; §6) |

Escopo do MMM (usuário, 2026-10-27): variantes Python para as hipóteses 1, 2, 3, 7, 9, 10 e 11. A 6 e a 8 são
iguais na planilha e no Python, então só entram no degrau 1. As hipóteses 4, 5 e 12 entram como sensibilidade por
unidade (a geometria é sintética). As hipóteses 13 a 16 ficam declaradas.

## 2. Física e convenções

### 2.1 Cinemática em raio constante

Milliken p. 307, conferido na imagem do PDF: α_F = β + a/R − δ e α_R = β − b/R.

No ISO 8855, numa curva à esquerda, a velocidade de um ponto da roda em (x_i, y_i) é
(V·cos β − r·y_i, V·sen β + r·x_i), com r = V/R. O ângulo de deriva com a convenção do projeto (α < 0 dá Fy > 0 à
esquerda, `equilibrio.py:171-173`) é

  α_i = atan[(sen β + x_i/R) / (cos β − y_i/R)] − δ_i

V se cancela, e com ângulos pequenos e y_i = 0 essa expressão cai nas fórmulas do Milliken **sem troca de sinal**:
o par (SAE, curva à direita) do livro corresponde ao par (ISO, curva à esquerda) do projeto. A curva à direita sai
de `equilibrio.espelhar`, como hoje. O teste TC-MMM-001 (§8) fixa o sinal sem depender desta dedução.

### 2.2 Sinal do C_N

A planilha e o `analise_par` usam o C_N residual "positivo = push (estabilizante)" (spec base §7.2;
`equilibrio.py:756-759`). No ISO, o momento de guinada é N = Σ(x_i·Fy_i − y_i·Fx_i), sem o Mz (hipótese 14). Numa
curva à esquerda, a sobra da traseira (x = −b) dá N < 0. É o mesmo sinal do Milliken: Q = −0,31 no push da curva à
direita em SAE (p. 306).

O `mmm.py` devolve as duas grandezas, com nomes distintos:
- `cn_iso` = N/(W·L), com sinal;
- `cn_estabilizante` = −cn_iso numa curva à esquerda (a grandeza da planilha).

Nenhum código troca o sinal sem passar por esse nome.

### 2.3 T, Q e P (Milliken p. 306)

- **T:** a_y máximo em trim (C_N = 0), ≈ 1,23 g no exemplo do livro.
- **Q:** o momento residual **no A_Y de T**, vindo do eixo que ainda tem folga. É comparável ao C_N residual do
  `analise_par`.
- **P:** soma vetorial dos pontos de saturação, fora do trim (1,54 g no exemplo). Só é alcançável num transiente. O
  sinal de P é o "final under/oversteer", diagnóstico que fica fora do critério da escada.

Push e loose seguem o eixo que satura primeiro ("Trim at the Limit", §8.5).

### 2.4 Stability index e K

São grandezas diferentes:
- **Stability index:** dC_N/dA_Y numa linha de δ constante, no trim (Milliken cap. 5, "Stability Index", p. 204;
  Fig. 8.21, p. 331).
- **K:** dδ/da_y na curva de trim, em ângulo pequeno δ = L/R + K·a_y.

O oráculo linear compara o K com `equilibrio_linear.parcelas_k`, nunca o stability index.

### 2.5 Balanço longitudinal em regime

Em raio constante, a aceleração do CG é centrípeta. Nos eixos do carro, a_x = −A·sen β e a_y = A·cos β. A força
de tração exigida na traseira, com o diferencial dividindo-a entre as rodas, fica

  Fx_r = D + RR + F_yf,pneu·sen δ − m·A·sen β

onde D é o arrasto, RR a resistência ao rolamento e F_yf,pneu a força lateral do pneu dianteiro nos eixos da roda.
(Revisto em 2026-10-28, EDR-064 item 5.) A rotação para os eixos do carro é a opção `Hipoteses.rotacao_beta`
(padrão `True`, só no caminho acoplado). Com `False`, a_y = A e a_x = 0 em todos os termos (cargas, camber, `transf_long`
"regime", o balanço de Fx via `+ m·a_x` e o fator a_y do ponto P no limite): é a simplificação da planilha, usada como
linha de controle da escada (§5.2). `rotacao_beta` não é uma das hipóteses numeradas; fica em `mmm.FORA_DE_VARIANTES`
junto com `h_cp_m`.
Com ângulos pequenos, δ = L/R + |α_F| − |α_R| e β = b/R − |α_R|, os dois últimos termos somam
F_yf·|α_F| + F_yr·|α_R|: é o arrasto induzido pela deriva. A §7 trata da diferença em relação à fórmula da
planilha.

### 2.6 Transferência longitudinal (hipótese 11)

Com momentos tomados no ponto de contato, as forças do pneu no solo não aparecem:

  ΔFz_traseira = (m·a_x·h + D·h_cp)/L, com a_x = −A·sen β

- A parcela m·a_x·h usa só dados que já existem.
- A parcela D·h_cp precisa da altura do centro de pressão. Esse campo não existe no código, então ela entra como
  sensibilidade por 10 mm de h_cp.

Usar `longitudinal_dfz` com a_x = Fx/m seria supor h_cp = h_CG sem declarar, ou seja, um coeficiente inventado.

## 3. Arquitetura

### 3.1 Módulos

| Arquivo | Papel | Depende de |
|---|---|---|
| `python/mmm.py` (novo) | Física: `Hipoteses`, cinemática, trim, limite, ponto, diagrama, sensibilidade. Funções puras, SI, ISO | `equilibrio`, `tire_model`, `suspension_model`, `kinematics_model` |
| `python/escada.py` (novo) | Orquestração: degrau 1, degrau 2, tabela de efeitos, sem veredito enquanto não houver tolerância aprovada | `mmm`, `equilibrio` |
| `tools/relatorio_escada.py` (novo) | Relatório `docs/inc6/escada-hipoteses.md` sobre o caso lido da planilha (`caso_planilha.caso_da_planilha_v41`, em cópia recalculada), no padrão de `tools/relatorio_inc4.py` | `escada`, `caso_planilha` |
| `python/equilibrio.py` | Só adição: `_entrada_limitada`, `_fy_eixo_limitado` e `_elipse_traseira` ganham nomes públicos (os privados ficam como apelidos), num commit de reorganização sem mudança de número | — |

A dependência tem um sentido só: escada → mmm → equilibrio. O `mmm.py` não importa o `escada.py`, e o
`equilibrio.py` não importa nenhum dos dois.

### 3.2 `Hipoteses` e o contrato das chaves

`Hipoteses` é um `dataclass` congelado com um campo por hipótese, cada um com valores fixos (enum ou literal).
`Hipoteses.planilha()` reproduz a planilha V4.2. A tabela `mmm.VARIANTES` liga cada hipótese ao campo e às
variantes dela, e é a fonte única que a chave 1/0 do incremento 7 vai usar. Um teste confere que cada entrada
existe em `Hipoteses` e na §7.4 da spec base.

| Hip. | Campo | Variante planilha | Variante Python |
|---|---|---|---|
| 1 e 2 | `alfa` | `"planilha"`: α comum por eixo, mais o Δα do toe e do Ackermann com velocidades paralelas e δ_ref = L/R (`deriva_total`) | `"cinematico"`: α exato por roda (§2.1), com δ do trim e Ackermann pela geometria SUS-414 (`ackermann_inner_ideal_deg`) aplicada ao δ do trim |
| 3 | `cos_delta` | `"ref"`: cos δ_ref | `"trim"`: Fy·cos δ + Fx·sen δ com o δ do trim |
| 7 | `sentido` | `"entrada"`: um sentido por vez | `"dois"`: os dois sentidos, com o pior registrado |
| 9a | `fx_exigido` | `"edr057"`: `fx_exigido_traseira` | `"balanco"`: §2.5 |
| 9b | `tracao` | `"elipse"`: `_elipse_traseira` | `"pac2002"`: `combined_forces` com o κ de cada roda resolvido para o Fx dela |
| 10 | `diferencial` | `"aberto"`: Fx igual nas duas rodas | `"travado"`: ω comum e mesmo raio de rolamento nos dois lados (suposição declarada); κ por roda pela cinemática |
| 11 | `transf_long` | `"nao"` | `"regime"`: §2.6, só a parcela m·a_x·h |

A hipótese 9 se divide em 9a e 9b para que o orçamento separe a fórmula do Fx exigido da forma da curva combinada.
O autoblocante (hipótese 10) fica declarado: não há dado de travamento.

### 3.3 Resultados

`dataclass` congelados:
- `Trim`: A_Y, β, δ e, por roda, α, Fz, Fy, Fx e κ, mais `convergiu`, `residuo` e `motivo`.
- `Limite`: T, a_y de saturação de cada eixo, eixo que satura, push/loose, `cn_iso` e `cn_estabilizante` em Q,
  C_N em P, stability index, K, `resolucao_ms2` e `motivo`.
- `PontoMMM`: um ponto do diagrama.

Os `dataclass` não carregam a origem dos dados: o `mmm.py` e o `escada.py` não a conhecem. O rótulo de origem (pior
origem do caso, como hoje) e a marca "geometria sintética" ficam no relatório (`tools/relatorio_escada.py`). Um ponto que não converge vira `None` com motivo, nunca um número, no padrão de
`Capacidade.motivo`.

## 4. Algoritmo

### 4.1 Trim em raio fixo, parametrizado por A_Y

Fixado A_Y, ficam determinados V = √(A_Y·R), a downforce, as cargas, γ e as forças exigidas por eixo
(`forca_exigida`).

1. **Variantes desacopladas** (as da planilha em 1, 2, 3, 9 e 10): os eixos se separam.
   - A traseira depende só de β. Uma raiz 1-D (Brent com intervalo) dá F_yr = m·A·a/L.
   - Com β fixo, a dianteira depende só de δ. Outra raiz 1-D dá F_yf = m·A·b/L.
   - As duas raízes ficam no ramo ascendente da **soma do eixo**, o mesmo critério de `capacidade_eixo`, e não roda
     a roda: com toe e Ackermann, uma roda pode passar do pico com a soma ainda subindo.
   - Sem raiz no ramo ascendente, não há trim nesse A_Y, e o motivo diz qual eixo faltou.
2. **Variantes acopladas** (`alfa="cinematico"`, `cos_delta="trim"`, `fx_exigido="balanco"`, `tracao="pac2002"`,
   `diferencial="travado"`, `transf_long="regime"`): Newton 2-D em (β, δ) com jacobiano por diferença finita, a
   partir da solução desacoplada. O passo é limitado para não sair do ramo ascendente de cada eixo.
   - Se a iteração não converge, ou converge fora do ramo, o resultado é `None` com motivo.
   - Não há segundo solver escondido: a solução desacoplada é só o chute inicial.
3. **Limite (T):** bisseção em A_Y sobre a existência de trim, com o intervalo inicial tirado da varredura do
   `analise_par`. A resolução é parâmetro explícito e sai no resultado.
4. **Q e push/loose:** em T, o eixo sem raiz é o que satura, e o outro dá a folga (Q).
   (Revisto em 2026-10-28, EDR-064 item 5.) Nas variantes acopladas com T, `Limite.folga_outro_N` e
   `folga_outro_fracao` trazem a folga do eixo que não satura: a capacidade acoplada dele em T menos a força exigida
   dele, nos eixos do carro (a fração é sobre a capacidade dele). O a_y de saturação desse eixo continua `None`
   (acima de T não há trim), e as duas folgas são `None` nas desacopladas e sem T. A regra do NEUTRO não muda (EDR-065).

### 4.2 Ponto e diagrama

- `ponto(caso, hip, β, δ)` resolve o trim lateral ΣFy(A_Y) = m·A_Y por Brent num intervalo [0, A_desc], onde
  A_desc é o primeiro A_Y com alguma Fz ≤ 0. Uma varredura prévia conta as trocas de sinal: com aero forte pode haver
  duas raízes, e `PontoMMM.n_raizes` registra isso.
- `diagrama(...)` aplica `ponto` numa grade β × δ. O diagrama é o de **raio fixo com trim lateral** (C_N contra A_Y,
  com V = √(A_Y·R) em cada ponto), rotulado assim. Ele não se compara diretamente com a Fig. 8.7 do Milliken, que é a
  velocidade constante (60 mph; p. 308). A escada usa só a curva de trim, e o diagrama é exibição.
- **Tempo medido em 2026-10-27** (veículo de teste dos testes): `combined_forces` ≈ 7 µs por chamada,
  `capacidade_eixo` com 401 α ≈ 7 ms e `analise_par` ≈ 0,17 s. O tempo de cálculo não restringe a grade nem o solver.

### 4.3 Sensibilidades (hipóteses 4, 5, 12 e as parcelas sem dado)

`sensibilidade(caso, hip, parametro, passo)` devolve a variação de T, de C_N em Q, de K e de push/loose por unidade
do parâmetro, por diferença central. As unidades são declaradas; nenhuma faixa é afirmada (spec base §7.5 item 4):

- **Hip. 4:** ganho de camber de cada eixo, por 0,1 °/°. Com a geometria sintética, a não linearidade não se mede.
- **Hip. 5:** altura do RC de cada eixo, por 10 mm, e K_φ de cada eixo, por 1 kN·m/rad.
- **Hip. 12:** altura do CG (`cfg.cg_height`), por 10 mm. O Python não tem modelo de jacking (o EDR-053 só existe em texto) e o jacking não muda a soma das Fz, só a altura e o camber; o camber já é coberto pela hipótese 4 (decisão 4 do plano, EDR-064).
- **Hip. 7:** CG lateral, por 10 mm (exemplo da spec base §7.5).
- **Hip. 11:** h_cp, por 10 mm (§2.6).

## 5. Escada

### 5.1 Degrau 1

`escada.degrau_1(caso)` compara `mmm.limite(caso, Hipoteses.planilha())` com `equilibrio.analise_par(caso)` nos dois
sentidos (`espelhar`), com a tolerância numérica `resolucao_ms2` que o próprio `analise_par` calcula, sem número
novo. Comparam-se:
- o a_y de saturação de cada eixo;
- o eixo que satura e push/loose;
- o C_N, com `cn_estabilizante` do lado do MMM.

O degrau 1 é uma identidade quase por construção, porque os dois códigos usam a mesma física por roda. Ele prova o
reuso, não a física do MMM. A prova da física fica com os oráculos independentes (§8).

A cadeia até a planilha é declarada: o `analise_par` bate com a planilha pelos testes que já existem
(`tests/test_workbook_v4_1.py`, recalculado no Excel ou no LibreOffice). Ela quebra se o `equilibrio.py` mudar
números, e por isso a reorganização da §3.1 roda os 28 + 18 testes do equilíbrio.

### 5.2 Degrau 2

`escada.degrau_2(caso)` parte de `Hipoteses.planilha()` e liga uma variante Python por vez (1+2, 3, 7, 9a, 9b, 10,
11). Depois liga **todas** juntas, que é o critério 3 da spec base. A tabela traz, para cada linha:
- a_y de saturação de cada eixo, T, push/loose, `cn_estabilizante` em Q e K;
- a diferença em relação à linha de referência dela;
- o `motivo` de cada ponto que não convergiu.

(Revisto em 2026-10-28, EDR-064 item 5.) A tabela tem 12 linhas, nesta ordem: `planilha` (Δ contra si);
`planilha (acoplado, sem rotação)` (`escada.NOME_CONTROLE_SEM_ROTACAO`; Δ contra `planilha` = viés só do método,
Newton 2-D com a_y = A e a_x = 0); `planilha (acoplado)` (Δ contra a linha sem rotação = efeito da simplificação
a_y = A da planilha); as linhas acopladas 1+2, 3, 9a, 9b, 10, 10+9b e 11 (Δ contra `planilha (acoplado)`, para que
cada número seja o efeito da hipótese); a `7`, que usa o caminho desacoplado (Δ contra `planilha`); e `todas`, acoplada
(Δ contra `planilha (acoplado)`). Cota empírica do TC-ESC-002 para a linha sem rotação: |ΔT| ≤ 1e-4 m/s² e
|ΔK| ≤ 1e-9 (medido no caso base sintético de teste: +4,49e-5 m/s² sem rotação; +1,343e-3 m/s² com).

As sensibilidades da §4.3 vêm numa tabela à parte.

**Sem veredito** enquanto a tolerância não for aprovada (EDR proposto na §9). A coluna "inverte push/loose?" já
aparece, porque não depende da tolerância.

### 5.3 Regra de inversão perto do neutro (decisão do usuário)

Uma variante que leva NEUTRO para PUSH ou LOOSE, ou o contrário, conta como inversão? Proposta: sim, pela mesma regra
estrita da robustez ao pneu (spec base §7.6 item 3; EDR-060 item 8). Fica para o EDR da tolerância. Até lá a tabela
marca esses casos como "NEUTRO ↔ <veredito>" sem classificá-los.

### 5.4 Saída

`tools/relatorio_escada.py --sobrescrever` gera `docs/inc6/escada-hipoteses.md` sobre o caso da planilha V4.2 de
`excel/`, lido por nomes numa cópia recalculada. Nenhum número do Python vai para a planilha (spec base §7.5). Todo
número do relatório leva o rótulo de origem: com dados demonstrativos, geometria sintética e o pneu R25B, nenhum é
resultado do carro.

(Revisto em 2026-10-28, EDR-064 item 5.) O relatório traz ΔT com 6 casas em g, para que as linhas de controle (ΔT
da ordem de 1e-5 g) apareçam, e a coluna "Folga do outro eixo em T" (N e % da capacidade, só nas linhas acopladas com
T; "—" nas demais), com a explicação de que acima de T o eixo que não satura fica sem a_y de saturação.

## 6. Interações conhecidas entre hipóteses

- **1 × 2:** o Ackermann da planilha supõe velocidades paralelas nas rodas dianteiras (§7.1). As duas hipóteses só
  se separam juntas, por isso a variante única `alfa`.
- **3 × 9a:** o termo F_yf·sen δ usa o δ do trim nas duas.
- **9b × 10:** com o diferencial travado, Δκ ≈ t/R entre as rodas traseiras. Com os números do veículo de teste e um
  R hipotético de 8,5 m, isso dá ≈ 0,14, perto do pico de κ. O deslizamento combinado derruba a capacidade lateral
  traseira, e o efeito é de primeira ordem. A linha 10 roda com 9b nas duas variantes, e a tabela mostra as duas.
- O "todas ligadas" da §5.2 existe porque essas interações tornam a soma das linhas isoladas diferente do efeito
  conjunto.

## 7. Achados sobre fórmulas da planilha (nenhuma mudança agora)

A revisão do conselho achou duas simplificações físicas na planilha, conferidas no código. O incremento 6 **não**
mexe nelas: elas aparecem só como efeito no degrau 2, e qualquer mudança exige EDR e aprovação explícita do usuário
no incremento 7 ou depois. Nada é ajustado para bater.

1. **Ackermann (hipótese 2, SUS-414).** `deriva_ackermann` (`equilibrio.py:225-237`) usa Δα = −(δ_roda − L/R), o
   que supõe a mesma direção de velocidade nas duas dianteiras. Na cinemática real, as direções diferem de ≈ L·t/R²,
   que é justamente a diferença do Ackermann ideal. Assim:
   - com 100 % de Ackermann o α real das duas rodas é igual, e a planilha dá ±L·t/(2R²);
   - com 0 % (paralelo) a planilha dá zero, e o real não.
   
   Com os números do veículo de teste e R = 8,5 m, ≈ 1,5° entre as rodas. É estimativa, que a variante `alfa` vai
   medir.
2. **Fx exigido (hipótese 9, EDR-057).** `fx_exigido_traseira` (`equilibrio.py:379-397`) usa |F_yf|·tan(L/R) ≈
   m·A·b/R, que depende de R e não da deriva. O balanço completo da §2.5 dá F_yf·|α_F| + F_yr·|α_R|, o arrasto
   induzido. Os dois têm ordem parecida perto de R ≈ 8 m e divergem em raio grande, onde o arrasto induzido continua
   existindo e o termo da planilha vai a zero. A variante `fx_exigido="balanco"` mede a diferença.

## 8. Testes

Scripts com `check()`, no padrão do projeto, cada um rodando em segundos. Os IDs são propostos.

**`tests/test_mmm.py`, física:**

| TC proposto | Verifica | Tipo |
|---|---|---|
| TC-MMM-001 | Com δ = L/R, β = b/R e toe nulo, α = 0 nas quatro rodas em baixa velocidade; com δ um pouco maior, α_F < 0 e F_yf > 0 | Oráculo cinemático, fixa o sinal ISO |
| TC-MMM-002 | Pneu de brinquedo (tanh, sem sensibilidade à carga): T e eixo limitante em forma fechada; com μ constante, os dois eixos saturam juntos (NEUTRO) | Oráculo analítico |
| TC-MMM-003 | Força bruta numa grade β × δ, sem `capacidade_eixo`: a existência de trim em A_Y abaixo e acima de T concorda com a bisseção | Oráculo independente do caminho do solver |
| TC-MMM-004 | K da curva de trim em a_y baixo = K de `equilibrio_linear.parcelas_k`, com as premissas conferidas no teste (sem aero, sem toe, sem Ackermann). Revisto em 2026-10-28 (EDR-064 item 5): oráculo de convergência, com K medido em A_Y = 0,05, 0,025 e 0,0125 g, queda monótona do erro e extrapolação quadrática a A_Y → 0 com erro ≤ 1e-2 | Oráculo linear |
| TC-MMM-005 | Carro com a = b e eixos iguais: o trim fica em δ = L/R para qualquer β, e C_N em Q ≈ 0 | Simetria |
| TC-MMM-006 | `espelhar`: \|T\| e push/loose iguais, `cn_iso` troca de sinal, `cn_estabilizante` não troca, forças por roda trocam de lado | Simetria e sinal |
| TC-MMM-007 | No trim devolvido, os resíduos de ΣFy − m·A_Y e de C_N ficam abaixo da tolerância; um caso forçado sem trim devolve `None` com motivo | Consistência |
| TC-MMM-008 | `alfa="cinematico"` com 100 % de Ackermann: Δα ≈ 0 entre as dianteiras; a variante da planilha dá ±L·t/(2R²) | Achado 7.1 |
| TC-MMM-009 | Diferencial travado em curva à esquerda dá N < 0 (push); diferencial aberto dá contribuição nula de Fx ao C_N | Sinal do diferencial |
| TC-MMM-010 | Caso com aero alta força `n_raizes > 1` em `ponto` | Solução múltipla |
| TC-MMM-011 | `VARIANTES` cobre exatamente os campos de `Hipoteses`, e cada hipótese existe na §7.4 da spec base | Contrato das chaves |

**`tests/test_escada.py`, orquestração:**

| TC proposto | Verifica |
|---|---|
| TC-ESC-001 | Degrau 1 nos casos de teste do `test_equilibrio.py`, nos dois sentidos: mesmo eixo que satura, a_y de saturação dentro de `resolucao_ms2`, mesmo push/loose, C_N comparado pela grandeza certa |
| TC-ESC-002 | Degrau 2: uma linha por variante, mais "todas ligadas"; a linha da planilha tem diferença nula; nenhuma linha traz veredito sem tolerância aprovada |
| TC-ESC-003 | Sensibilidades: unidade declarada em cada linha, sem faixa; o sinal da sensibilidade ao CG lateral troca com o sentido da curva |

**Mutação:** 5 mutantes no fechamento do incremento, não por tarefa, no padrão de `tests/mutation_*`. Os mutantes
são: sinal do α dianteiro, troca de a/R por b/R, troca de sinal na conversão do C_N, retirada de m·A·sen β e
δ_ref no lugar do δ do trim. Cada um precisa ser pego por pelo menos um TC acima.

**Regressão:** os testes do equilíbrio (28) e do equilíbrio linear (18) rodam em toda tarefa que toque o
`equilibrio.py`. Os testes novos entram em `tools/rodar_testes.py` e nas contagens esperadas do CLAUDE.md. A suíte
inteira roda uma vez, no fim, em segundo plano.

## 9. IDs propostos (nenhum criado)

- **EDR-064:** método do MMM e da escada no Python. Registra:
  - as convenções da §2 (cinemática ISO, as duas grandezas de C_N, T/Q/P, stability index × K);
  - as variantes da §3.2 e as suposições declaradas (raio de rolamento igual no diferencial travado, h_cp por
    sensibilidade);
  - os desvios A1 a A5.
- **EDR-065:** tolerância da escada e regra do NEUTRO (§5.3). É decisão do usuário. Até ela, a tabela fica sem
  veredito.
- **EDR-066:** os dois achados da §7, para decisão no incremento 7. Reabre parcialmente o EDR-057 e o SUS-414 sem
  alterá-los agora.
- **TCs:** TC-MMM-001 a 011 e TC-ESC-001 a 003.
- **SUS-:** nenhum previsto, porque não há grandeza nova na planilha. Se o plano precisar de um, pede a partir de
  SUS-1009.

## 10. Riscos e premissas

- **Coeficientes combinados do `.tir`** (REX1 = 0,333333, RBY2 = 10,4, RVY1 = 0,01, entre outros) podem ser valores
  padrão, e não um ajuste. O plano tem uma tarefa de conferência. Se forem padrão, a variante `pac2002` é outra
  hipótese sem validação, não uma referência melhor que a elipse, e o relatório diz isso.
- **Tabela 8.3 do Milliken:** o exemplo é a velocidade constante e tem um valor fora de ordem na linha 4
  (C_Y = 0,173, provavelmente erro de impressão). Por isso não entra como oráculo numérico.
- **Newton 2-D perto do pico:** pode não convergir. Nesse caso sai `None` com motivo, e a bisseção em A_Y só conta
  pontos com trim.
- **Dados:** com geometria sintética, pneu R25B e dados demonstrativos, nenhum número da escada é resultado do carro.
  Com dados do T11, a escada roda de novo (spec base §7.5 item 5).
- **Premissa do degrau 1:** o `analise_par` continua batendo com a planilha (CA-09). Ela vale enquanto o
  `equilibrio.py` não mudar números.

## 11. Pendências do usuário

1. Revisar este adendo (depois dele, o plano).
2. Autorizar os IDs da §9 (no plano).
3. Tolerância da escada e regra do NEUTRO (EDR-065). Pode esperar o relatório do degrau 2.
4. Da equipe: tipo de diferencial do T11, raio do skidpad, CdA e Crr, h_cp, e se vale para o T11 o layout de motor no
   chassi, atrás.

## 12. Fontes

- Milliken & Milliken, *Race Car Vehicle Dynamics*:
  - §8.4, p. 301-312 (diagrama C_N-A_Y, T, Q e P, p. 306; cinemática de raio constante, p. 307);
  - p. 308 (C_N-A_Y a velocidade constante × C_N-C_Y a raio constante);
  - §8.5 ("Trim at the Limit", push e loose);
  - cap. 5, "Stability Index", p. 204, e Fig. 8.21, p. 331 (stability index). A página 204 saiu da marcação de
    página do OCR e não foi conferida na imagem.
  
  Equações conferidas na imagem do PDF (págs. 306-307) em 2026-10-27.
- Pacejka, *Tyre and Vehicle Dynamics*, §1.3.5 (MMM como gráfico de Gough do carro inteiro).
- Código: `python/equilibrio.py` (linhas citadas no texto), `python/equilibrio_linear.py`, `python/tire_model.py`.
