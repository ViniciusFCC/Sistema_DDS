# Revisão metodológica do Sistema_DDS contra a literatura — 1ª rodada (V3.0)

**Situação:** primeira rodada concluída em 2026-10-19. No mesmo dia o usuário mandou seguir a
literatura (principalmente o Milliken) e autorizou todas as propostas da seção 5: elas
estão **aplicadas** na V3.0 (EDR-045 a EDR-049; `docs/registro-de-versoes-V3_0.md`). As
tabelas das seções 2 e 3 descrevem o estado **antes** da V3.0; a coluna "Resultado" vale
para a V2.4. A decisão A3 (seção 4) foi tomada no mesmo dia: o caso T09 virou regressão histórica.

**Script de apoio:** `tools/oraculos_literatura.py` (não altera nada; reproduz os exemplos
numéricos dos livros e mede o efeito de cada divergência). Saída da última execução em
`build/oraculos_literatura.txt`. Rodar com:

```bash
uv run python -X utf8 tools/oraculos_literatura.py
```

## 1. Fontes consultadas

Os PDFs e as conversões ficam em `references/` (fora do Git, SPEC D3); o registro está em
`references/INDEX.md`. Toda citação abaixo usa a **página impressa** do livro.

| Sigla | Obra | Observação |
|---|---|---|
| [MIL] | W. F. Milliken e D. L. Milliken, *Race Car Vehicle Dynamics*, SAE R-146, 1995 (5ª impressão) | digitalização sem texto; conferida por imagem |
| [GIL] | T. D. Gillespie, *Fundamentals of Vehicle Dynamics*, SAE | a página de créditos não está no PDF; edição a confirmar |
| [SEW] | D. Seward, *Race Car Design*, Palgrave, 2014 | digitalização sem texto; conferida por imagem |
| [PAC] | H. B. Pacejka, *Tyre and Vehicle Dynamics*, 2ª ed., Butterworth-Heinemann, 2006 | **não estava entre os três anexados**; estava na mesma biblioteca do usuário e foi incluído por ser a fonte primária que o EDR-042 pedia |

Cada equação citada foi lida na imagem da página (ampliada quando necessário), não só no
OCR. O OCR serve para busca.

## 2. Resumo

- **Confere (estrutura e sinais):** SUS-101, 102, 104, 012, 201/202 (MR [wheel/spring]),
  208, 301/302 (forma da equação), 402, 410, 601; EDR-003, 009, 010, 011, 026; o bloco de
  escorregamento combinado do pneu (Gxα, Gyκ, SVyκ) e a regra de uso de μy em DVyκ.
- **Diverge (as três fontes de dinâmica concordam entre si e discordam do projeto):**
  1. **Rigidez do pneu em série** fora de SUS-205 (frequência natural) e de SUS-206/207
     (rigidez de rolagem). [GIL] eq. 5-8/5-9, [SEW] eq. 4.1/4.2/4.5 e [MIL] p. 588-592
     usam a *ride rate* (mola na roda em série com o pneu). Com o K_T do .tir provisório,
     f_n cai 6,4 % e K_φ cai 13 a 16 % (valores demonstrativos).
  2. **Termo gravitacional da rolagem** fora de SUS-103. [MIL] p. 682 e [GIL] eq. 6-31 a
     6-34 incluem o deslocamento lateral do CG suspenso com a rolagem (denominador
     K_F + K_R − W_s·h2). No exemplo da [MIL] p. 683, o modelo atual dá 3,7 % a menos na
     dianteira.
  3. **Construção do IC lateral** (SUS-406, método V1 do ponto médio): não aparece em
     nenhuma fonte; [GIL] p. 249 e [MIL] p. 612 constroem o IC pelas retas dos braços /
     eixos de pivô. Confirma o achado da nota V2.0 de SUS-406 (%AD −680,7 pelo V1).
  4. **Linha de reação do anti-dive/anti-squat** (o "em aberto" de SUS-301/302/406): a
     fonte resolve o *método*. Freio no cubo (outboard) → linha pelo contact patch; torque
     reagido pelo chassi (freio inboard, diferencial ou motor no chassi com semieixos) →
     linha pelo centro da roda ([MIL] p. 618-619, Fig. 17.12, 17.13 e 17.15; [GIL] eq.
     7-17 a 7-19). Falta só o dado do carro (onde estão freios e motor).
- **Fonte não cobre:** limiar de MR (EDR-027), schema e placeholders (EDR-024/025), a
  convenção do arquivo TTC (EDR-039, só evidência indireta) e a forma PAC2002 exata do
  Fy0 puro (o [PAC] 2ª ed. traz a versão 2004 da Magic Formula).
- **Erros encontrados nas próprias fontes:** [MIL] p. 682 imprime um K_F' que não
  reproduz o exemplo numérico da p. 683; [MIL] p. 718 imprime a razão de direção
  invertida. Detalhes nas fichas.

## 3. Tabela de revisão

Resultado: **C** = confere; **D** = diverge; **N** = fonte não cobre; **C*** = confere
com ressalva registrada.

| Item | Projeto (resumo) | Fonte e local | Resultado | Evidência / observação |
|---|---|---|---|---|
| SUS-000/002 | alturas medidas do solo | [MIL] p. 680, Fig. 18.9; p. 694 (eixos SAE no solo) | C | Todas as alturas da transferência de carga são do solo. |
| SUS-101 | W_f = m·g·b/L | [MIL] p. 692; [SEW] eq. 5.14-5.15 | C | Igual. |
| SUS-102 | ΔFz = m·a_x·h/L | [MIL] p. 684-685; [GIL] eq. 7-1; [MIL] p. 617 | C | Igual, inclusive o sinal (frenagem aumenta o eixo dianteiro). |
| SUS-104 | superposição linear + aero /2 | [MIL] p. 707 ("assumes superposition works"); p. 694-695 | C* | Superposição é a hipótese da fonte. O livro inclui o momento aerodinâmico de rolagem distribuído pela rigidez (p. 695); o projeto não modela (hipótese já declarada). |
| SUS-009 | m_s,canto = m_s·(b/L)/2 | [MIL] p. 601, Tab. 16.3 (W_SF = W_F − W_UF); [SEW] eq. 5.14 | C* | A fonte calcula a massa suspensa por eixo sem aproximação: m_s,F = m·b/L − m_uF. O projeto aproxima pelo CG total (hipótese documentada em SUS-006). Diferença na planilha V2.4: 68,65 × 69,14 kg (−0,7 %). Proposta P-04. |
| SUS-012 | h_s pela identidade do CG composto | [MIL] p. 602 | C | Mesma fórmula; a fonte usa o raio carregado do pneu como altura do CG não suspenso, que é a aproximação de SUS-010/011. |
| SUS-201 | MR [wheel/spring] | [SEW] p. 101, eq. 4.6 (R_m = roda/mola, K_s = R_m²·K_W); [MIL] p. 595-596 (*installation ratio* IR = mola/roda) | C | As duas fontes usam razões **inversas** entre si. Isso confirma o risco que motivou o EDR-003 e o nome obrigatório `MR [wheel/spring]`. |
| SUS-202 | K_wheel = K_spring/MR² | [MIL] p. 596: K_W = F_s·dIR/dδ + K_s·IR²; [SEW] eq. 4.6 | C* | O termo F_s·dIR/dδ (taxa geométrica) é o mesmo omitido em SUS-409 (hipótese declarada). A fonte avisa que ele pesa com mola mole (Tab. 16.2). Na geometria sintética: +0,32 % (desprezível). Reavaliar com a geometria real. |
| SUS-205 | f = √(K_wheel/m)/2π | [GIL] eq. 5-8, 5-9 (p. 148); [SEW] eq. 4.1-4.2 (p. 95); [MIL] p. 588, 601 | **D** | As três fontes usam a *ride rate* K_R = K_W·K_T/(K_W+K_T), não K_W. Planilha V2.4 + K_T do .tir provisório: f_F 2,438 → 2,282 Hz (−6,4 %); f_R 2,526 → 2,361 Hz. Proposta P-01. |
| SUS-205 (Design) | K_wheel = (2πf)²·m | [MIL] p. 591-592; [SEW] eq. 4.4 | **D** | Da frequência-alvo sai K_R; depois K_W = K_R·K_T/(K_T − K_R). Mesma proposta P-01. |
| SUS-206/207 | K_φ = K_W·t²/2 + K_ARB | [GIL] eq. 6-26 (p. 211-212); [MIL] p. 589, 592, 680; [SEW] eq. 4.5, p. 136 | **D** | A forma K_W·t²/2 confere com [GIL] 6-26. Mas a [MIL] p. 680 diz que as rigidezes de rolagem da transferência de carga **incluem a deflexão do pneu**, e a p. 592 mostra o cálculo em série (barra referida à roda). [SEW] usa K_R. Efeito (demonstrativo): K_φF −15,6 %, K_φR −13,3 %; λ_f 0,5494 → 0,5426. Proposta P-02. |
| SUS-206 (ARB) | K_ARB entra direto em N·m/rad | [MIL] p. 599-600 (K_φB = K_θB·I_B²·T²/L²); [SEW] eq. 4.10-4.13 | C* | A entrada direta é simplificação declarada. As fontes dão o cálculo a partir da barra, útil para um futuro bloco de projeto da barra. |
| SUS-208 | λ_f = K_φF/(K_φF+K_φR) | [MIL] p. 684; [SEW] p. 136 | C | Igual. O modo Design da [MIL] p. 604-605 parte da distribuição de transferência total (TLLTD), não de λ; é heurística da fonte, **não adotada** (seria um target sem decisão da equipe). |
| SUS-103 | duas molas com massas não suspensas separadas | [MIL] p. 604 (FLT/A_y = K_φF·φ/T + W_SF·Z_F/T + W_UF·RL_F/T); [SEW] eq. 5.16-5.21; [MIL] p. 680-683; [GIL] eq. 6-27 a 6-34 | C* / **D** | A estrutura confere com [MIL] p. 604 e [SEW] passo a passo. Duas diferenças: (a) a fonte posiciona o CG suspenso pela distribuição da massa suspensa (a_s), não pelo CG total; (b) [MIL] p. 682 e [GIL] 6-31/6-34 incluem o termo W_s·h2 no denominador. Exemplo da [MIL] p. 683 (lb/g): livro F 590,8 / R 483,4; projeto 569,1 / 480,9; (a) sozinho dá 575,0 / 475,0; (b) sozinho, 584,7 / 489,2; (a)+(b) reproduz o livro exatamente. Propostas P-03 e P-04. |
| SUS-103 (fonte) | - | [MIL] p. 682 | erro na fonte | Com o K_F' impresso (K_F − (ℓ−a_s)·W_s·h2/ℓ), a fórmula dá 577,7 / 472,3, que não é o resultado do próprio exemplo. Com K_F' = K_F dá 590,8 / 483,4, igual ao livro, igual à forma da §18.10 (p. 703) e à de [GIL] 6-33. A versão sem a correção é a fisicamente coerente: o momento total vira W·h + W_s·h2·φ, que é o equilíbrio do carro com o CG deslocado. |
| TC-005 | t_F·ΔF_F + t_R·ΔF_R = m·a_y·h | [MIL] p. 679, 683 | C* | A identidade vale para a forma sem o termo gravitacional. Se P-03 for aprovada, o teste muda para m·a_y·h + m_s·g·h2·φ. |
| SUS-401/402 | RC por linha contact patch → IC frontal | [MIL] p. 613-614, Fig. 17.7; [GIL] p. 258 | C | Igual. A fonte frisa que o RC não fica necessariamente na linha de centro com o carro rolado (Fig. 17.7b): é o que SUS-412 (`axle_roll_center`) já faz. |
| SUS-403 | IC frontal pela reta ball joint → bucha | [MIL] p. 612 | C* | Igual sob a hipótese de eixo de pivô paralelo a X (declarada). |
| SUS-406 (V1) | IC lateral pela reta ball joint → ponto médio das buchas | [GIL] p. 249 ("projected intersection of the control arm axes"); [MIL] p. 612, Fig. 17.12-17.15 | **D** | Nenhuma fonte usa o ponto médio. Na geometria sintética: V1 dá %AD −680,7; eixos de pivô 38,0; cinemático (SUS-412) 36,3. Confirma a proposta da nota V2.0 de SUS-406 (P-05). |
| SUS-406 / 412 | IC 3D | [MIL] p. 612-613, Fig. 17.6 (eixo instantâneo) | N | A fonte apresenta o eixo instantâneo de forma qualitativa. A leitura literal (eixo do helicoide cruzando o plano pelo centro da roda) dá um IC frontal muito diferente da construção clássica da própria fonte (Fig. 17.7), porque o passo do helicoide é grande (−0,47 m/rad na geometria sintética). Conclusão: a fonte não define o IC 3D com rigor suficiente; a REFERENCE (OptimumKinematics) decide (TC-011). |
| SUS-301 | AD = FB_f·tan φ·L/h·100 | [MIL] p. 618, Fig. 17.12-17.13; [GIL] eq. 7-28 | C | Igual. φ é medido do contact patch com freio outboard e do centro da roda com freio inboard. |
| SUS-302 | AS = TF_r·tan φ·L/h·100 | [MIL] p. 619, Fig. 17.15; [GIL] eq. 7-15, 7-19, 7-29 | C | Igual. Eixo rígido: linha pelo contact patch; suspensão independente com torque reagido pelo chassi: linha pelo centro da roda ([GIL] 7-19 usa e − r). |
| SUS-301/302 (sinal) | proposta V2.0 de forma com sinal | [MIL] p. 620 (*pro-dive, squat, lift*) | C | A fonte reconhece o "anti" negativo. Apoia o EDR-026 e a forma com sinal. |
| SUS-404/407 | ganho de camber | [MIL] p. 615 (taxa ≈ atan(1/fvsa)) | C* | A fonte dá a aproximação 2D; o solver 3D é mais completo. Pode virar um teste cruzado simples. |
| SUS-405/408 | toe / bump steer | [MIL] cap. 19 | não conferido | Fica para a próxima rodada. |
| SUS-410 | caster, KPI, scrub, trail | [MIL] p. 710, Fig. 19.1; p. 713 | C | Sinais iguais: scrub negativo com a interseção do eixo do pino por fora do contact patch; trail positivo com a interseção à frente. A fonte mede o trail na horizontal (como o projeto) e cita a alternativa perpendicular ao eixo. |
| SUS-413/601 | SR = Δvolante/Δroda; SR = (360/c)/(dyaw/ds) | [MIL] p. 716, 718 | C* | Definição igual. A fórmula da p. 718 está impressa invertida ("sin⁻¹(c/braço)/360" dá graus de roda por volta, não a razão); a forma correta, 360/sin⁻¹(c/braço), coincide com a do projeto para ângulos pequenos. Erro da fonte, não do projeto. |
| SUS-701/702 | downforce e balanço fixos | [MIL] p. 694-695 | C | Equivalente (C_LF = ½·C_L + C_PM). |
| SUS-501/502 (Fx0) | MF PAC2002 | [PAC] eq. 4.E9-4.E18 (p. 187) | C* | Estrutura igual. O [PAC] traz a versão 2004 (μx sem o termo PDX3·γ², que é do PAC2002). Com λ = 1 não há diferença de escala. |
| SUS-501 (Fy0) | MF PAC2002 | [SEW] eq. 5.5-5.13 (p. 131-133); [PAC] 4.E19-4.E30 | C* | [SEW] traz a forma PAC'96/2002 do Fy0 e confere com o módulo, inclusive (1 − PDY3·γ²) e o Ey com sgn(α_y). Diferenças só de fatores de escala λ (SHy, SVy) e, em Ky, do λFz0 extra (ver abaixo). |
| SUS-501 (Ky, EDR-042 i) | Ky com LFZO extra (forma Racer) | [SEW] eq. 5.9; [PAC] eq. 4.E25 (com γ = 0) | **D** (sem efeito hoje) | As duas fontes têm um único λFz0 multiplicando (via F'z0 = λFz0·Fz0), como o MFeval; o módulo segue o Racer e aplica um segundo. Com LFZO = 1 (o .tir atual) não muda nada. Proposta P-06. |
| SUS-501/502 (EDR-042 ii) | LGAX/LGAY aplicados ao camber | [SEW] p. 131 (γ_y = camber real); [PAC] 4.E (γ* sem esse fator) | N | Nenhuma das duas fontes tem λγ; a 2ª ed. do [PAC] usa λKyγ. Sem efeito com LGAY = 1. |
| SUS-501/502 (entrada α) | α em rad | [PAC] eq. 4.E3 (α* = tan α·sgn Vcx), 4.E4 (γ* = sin γ); [SEW] p. 132 (α em rad) | C* | O [PAC] define α* = tan α; o [SEW] usa α. A 12°, tan α difere de α em 1,5 %. Depende de como o OptimumTire ajustou o arquivo: **a confirmar** com a documentação do OptimumTire (TC do EDR-040). |
| Combinado (Gxα, Gyκ, SVyκ) | - | [PAC] eq. 4.E50-4.E67 (p. 189) | C | Igual termo a termo (sem rBx3 e rBy4, que o PAC2002 não tem). Fx = Gxα·Fx0; Fy = Gyκ·Fy0 + SVyκ. |
| DVyκ (μy) | usa o μy local | [PAC] eq. 4.E67 | C | A fonte primária usa μy (4.E23), o mesmo do módulo. Resolve a ambiguidade do código do Racer citada no EDR-042. |
| SUS-503 | μ_eff = √(Fx²+Fy²)/Fz | [SEW] p. 131 | C* | Fórmula trivial. Achado relevante: o [SEW] diz que os dados do TTC (FSAE Tire Test Consortium) superestimam o atrito e que λμy ≈ 0,6-0,7 dá resultados mais realistas. É valor de fonte publicada, mas a aplicação é decisão da equipe: **não aplicado**. Reforça que o μ da planilha é demonstrativo. |
| EDR-039 (γ) | γ_arquivo = −γ_projeto (inferência) | [PAC] Apêndice 1 (p. 612); [MIL] p. 62-63, Fig. 2.24, 2.27-2.29 | N (evidência indireta) | Em SAE e em ISO o γ positivo é a mesma inclinação física (só o "adapted ISO" inverte), e o empuxo de camber aponta para o lado da inclinação. Num arquivo SAE padrão, então, γ_arquivo = +γ_projeto no pneu direito. O arquivo se comporta ao contrário, o que a inferência H3b explica. A [MIL] mostra dados Calspan TIRF publicados em *camber* de roda esquerda (−5° = inclinada para a direita), que é o sinal oposto ao do IA SAE. Se o TTC usa a mesma variável, a H3b está certa. Continua **a confirmar** na documentação do TTC. |
| EDR-003 | MR [wheel/spring] | [SEW] eq. 4.6; [MIL] p. 595-596 | C | Ver SUS-201. |
| EDR-009 | RC estático | [MIL] p. 613-615; [GIL] p. 258 | C | As fontes usam o RC estático na transferência de carga e avisam que ele migra com o curso. |
| EDR-010 | anti não muda ΔFz total | [MIL] p. 617 (em negrito: "do not change the steady-state load transfer at the tire patch"); [GIL] eq. 7-11 | C | Confirmado. |
| EDR-011 | Milliken duas molas | ver SUS-103 | C* | Ver SUS-103. |
| EDR-015/037 | pneu como REFERENCE | - | N | Política do projeto, não física. |
| EDR-026 | + = anti; − = pro | [MIL] p. 620 | C | Ver SUS-301/302. |
| EDR-027 | limiar de MR | [MIL] p. 627 | N | A fonte só recomenda razões próximas de 1:1, de forma qualitativa. Não há limiar numérico em nenhuma das fontes. |
| EDR-042 | equações do pneu | [PAC] 4.E; [SEW] 5.5-5.13 | C* | Fonte primária agora consultada. A condição (a) do EDR-042 ("conferência no livro") fica **parcialmente** atendida: o combinado confere com o [PAC]; o Fy0 puro confere com o [SEW] (forma PAC'96/2002); o Fx0 confere em estrutura com o [PAC] 2004. A forma exata do PAC2002 (documentação TNO/Adams) continua não consultada. |

## 4. Decisão A3 (caso de referência do T09)

O `importado-claude-ai/saidas-conversas/plan/test_t09_reference_case.py` usa só
`roll_stiffness_axle`, `roll_stiffness_distribution` e `natural_frequency`, que existem
com o mesmo nome e a mesma assinatura no `python/suspension_model.py` atual. Refiz os
mesmos 7 cálculos com o módulo atual (sem copiar nem rodar o arquivo importado): todos
batem com os valores declarados do T09 (erro máximo 0,014 %).

O que isso significa e o que não significa:

- O caso T09 confere **a transcrição**: a planilha histórica da equipe calculava a
  rigidez de rolagem e a frequência sem o pneu, como o projeto faz hoje. Ele não confere
  a física.
- A revisão mostra que a literatura inclui o pneu (P-01 e P-02). Se o caso T09 for
  portado como teste com status PASS, ele vai **congelar o método que a literatura
  contradiz**, e vai falhar assim que P-01/P-02 forem aprovadas.
- Observação: os valores de entrada da planilha V2.4 (K_s 49 909 e 57 052 N/m com MR
  1,76; K_ARB 5 012 e 10,78 N·m/rad) reproduzem exatamente os wheel rates e as barras do
  T09 (16 112 e 18 418 N/m). Pelo EDR-012 o T09 nunca é baseline. **Conferido:** na V2.4 os
  comentários dessas células citavam o T09 como fonte, mas não diziam que o valor é só
  demonstrativo. O usuário confirmou (2026-10-19) que são valores de referência e de teste
  de formulação; na V3.0 eles ganharam o aviso DEMONSTRATIVO (06_SUSPENSION A2 e comentários
  de B4:B15).
- Com a V3.0 (pneu em série), o caso T09 deixa de bater por construção: a planilha
  histórica do T09 calculava sem o pneu.

**Decisão do usuário (2026-10-19):** portar como **regressão histórica**, rotulada como
referência histórica (EDR-012) e sem contar na aprovação do modelo. Feito em
`tests/regressao/t09_referencia_historica.py`: o script roda o modelo atual na forma sem
pneu (`k_tire = inf`), reproduz os 7 valores da planilha do T09 (erro máximo 0,014 %),
mostra a forma da V3.0 só como informação e fica fora do `tools/rodar_testes.py`.

## 5. Propostas de correção (aplicadas na V3.0 em 2026-10-19)

Autorizadas pelo usuário em 2026-10-19 e implementadas: P-01 e P-02 no EDR-045 (novos
SUS-211 e SUS-212), P-03 no EDR-046, P-04 no EDR-047, P-05 e P-07 no EDR-048 (com a
configuração do carro: freio dentro da roda, em volta do cubo; motor no chassi, atrás) e
P-06 no EDR-049. Nenhuma inventa valor: o único número novo é o K_T, que vem do .tir
provisório (`VERTICAL_STIFFNESS = 120312 N/m`, EDR-038) e está rotulado PROVISÓRIO.
Verificação: os modelos reproduzem os exemplos publicados (Milliken p. 592, 601-603 e
683-684; Seward Ex. 4.1; Gillespie p. 154) e a planilha V3.0 reproduz os modelos
(`tests/test_workbook_suspensao.py` 9/9, `tests/test_workbook.py` 19/19).

| ID provisório | Mudança | Fontes | Efeito medido (demonstrativo) | O que exige |
|---|---|---|---|---|
| P-01 | SUS-205: usar K_R = K_W·K_T/(K_W+K_T) na frequência; no Design, K_W = K_R·K_T/(K_T − K_R) | [GIL] 5-8/5-9; [SEW] 4.1, 4.2, 4.4; [MIL] p. 588-592 | f_n −6,4 % | entrada nova K_T (ID novo, faixa SUS-2XX); fórmulas novas em 06_SUSPENSION e 11_DESIGN; testes TC-009/010 e piloto |
| P-02 | SUS-206/207: K_φ = série(K_W·t²/2 + K_ARB, K_T·t²/2) | [MIL] p. 589-592, 680; [SEW] 4.5 | K_φ −13 a −16 %; λ_f −0,007 | mesma entrada K_T; muda 06_SUSPENSION B20:B23 e o Design de SUS-208; TC-006 |
| P-03 | SUS-103: denominador K_F + K_R − m_s·g·h2 (termo gravitacional) | [MIL] p. 682-683, 703; [GIL] 6-31 a 6-34 | +2,7 % F, +1,7 % R no exemplo da [MIL] | muda 09_LOADS B19:B20; TC-005 passa a m·a_y·h + m_s·g·h2·φ |
| P-04 | SUS-009/103: massa suspensa por eixo exata, m_s,F = m·b/L − m_uF, e a_s = L·m_s,R/m_s | [MIL] p. 601-603; [SEW] 5.14 | m_canto −0,7 % / +0,7 %; SUS-103 +1,0 % F no exemplo da [MIL] | muda 06_SUSPENSION B28:B29 e 09_LOADS B18:B20; atualiza a hipótese de SUS-006 |
| P-05 | SUS-406: aposentar o método do ponto médio; adotar o IC cinemático (SUS-412) ou o dos eixos de pivô | [GIL] p. 249; [MIL] p. 612 | %AD −680,7 → 36,3 (sintético) | já proposto na nota V2.0; a fonte confirma. Escolha entre os dois métodos: a REFERENCE decide (TC-011) |
| P-06 | Ky: um único λFz0 (forma MFeval/[SEW]/[PAC]) | [SEW] 5.9; [PAC] 4.E25 | zero com LFZO = 1 | muda `tire_model.py` e 10_TIRE (fórmula de Ky); ajustar TC-TIRE-ORC (o oráculo Racer passa a divergir quando LFZO ≠ 1) |
| P-07 | SUS-301/302: fixar `reaction_point` pela regra da fonte | [MIL] p. 618-619; [GIL] 7-17 a 7-19 | - | dado do carro: posição dos freios (cubo ou chassi) e do motor/redução (no cubo ou no chassi). Sem esse dado, fica a confirmar |

O que continua dependendo de dado ou de REFERENCE: a rigidez vertical do pneu real
(SUS-211), os ICs e a altura do centro da roda em 07_KINEMATICS (placeholders) e a escolha
entre IC cinemático e eixos de pivô (TC-011).

## 6. O que fica para a próxima rodada

- Cap. 19 da [MIL] (bump steer e Ackermann) contra SUS-405/408/413.
- Cap. 5 da [MIL] (modelo de bicicleta) e cap. 6 do [GIL] (gradiente de subesterço), se
  a planilha ganhar esse bloco.
- Documentação TNO/Adams do PAC2002 (forma exata do Fy0 e dos fatores λ).
- Documentação do TTC sobre o sinal do IA (EDR-039).
- Anti-lift traseiro sob frenagem regenerativa (motor no chassi: linha pelo centro da roda;
  escopo no EDR-033).
- Definição α* = tan α (Pacejka eq. 4.E3) contra α (Seward; módulo atual): depende de como o
  OptimumTire ajustou o arquivo (EDR-040).

## 7. 2ª rodada: conferência contra a documentação dos programas (2026-10-19)

Documentos recebidos do usuário em 2026-10-19 (em `references/`, fora do Git; ver `references/INDEX.md`): help do
OptimumKinematics (REFERENCE de cinemática, EDR-004), help do OptimumT 1.0.14, help do Adams 2024.1 "Using the PAC2002
Tire Model" (o `.tir` provisório declara `PAC2002 2018`, `COMPATIBILITY: Adams Tire 2018`, feito pela Stackpole para o
TTC) e o pacote do TTC Round 6 (R25B; o `.tir` de 12 psi é o provisório). Equações conferidas na imagem da página.

### 7.1 Convenções

| Convenção do projeto | Documento | Situação |
|---|---|---|
| Eixos ISO 8855 (X frente, Y esquerda, Z cima) | OptimumKinematics §5.1, fig. 15 (p. 31): X para a frente, Z para cima, Y para a esquerda pela figura (a tabela diz só "front or rear"); Adams: eixos C e W do TYDEX com orientação ISO (p. 6-7) | mantém |
| Camber + = topo para fora; toe + = toe-out (EDR-002) | OptimumKinematics §7.3.3.5 e 7.3.3.6 (p. 88-89): mesmas definições | mantém |
| MR = Δroda/Δmola (EDR, nome `MR [wheel/spring]`) | OptimumKinematics §7.3.3.7 (p. 89): "Wheel Displacement / Spring Displacement" | mantém |
| Anti-dive pelo contact patch (freio no cubo); anti-squat pelo centro da roda (motor no chassi) (EDR-048) | OptimumKinematics §7.3.3.1-7.3.3.3 (p. 84-86): anti-dive com o ângulo a partir do contact patch; anti-squat com o torque aplicado no centro da roda; anti-lift traseiro pelo contact patch com freio fora do chassi e pelo centro da roda com freio dentro | mantém; reforça o escopo do EDR-033 (regeneração pelo motor no chassi reage pelo centro da roda) |
| Scrub radius + com o eixo de esterço cortando o solo entre a linha de centro e o contact patch | OptimumKinematics §7.3.3.12 (p. 92) | mantém (pela expressão de `kinematics_model`, com `side` = +1 à esquerda) |
| Sistema de eixos do `.tir`: SAE_CALSPAN (EDR-039) | Adams p. 7: "the parameters in the tire property file must always be valid for the TYDEX W-axis system (ISO oriented)". Avaliação do arquivo: Fy(α > 0) < 0 e Fy(γ = 2°, α = 0) = −160 N (+27 N com γ = 0); Pacejka App. 1 (p. 612) e OptimumT fig. 8.2: γ > 0 desloca Fy para baixo só no ISO | **não se mantinha**: o arquivo é ISO (TYDEX W). Corrigido em 2026-10-19 (usuário): EDR-039 reaberto, dataset declarado `ISO_TYDEX` (identidade, sem o s_γ inferido); efeito medido no registro de versões V3.0 |
| Espelhamento das rodas esquerdas (H4) | Adams p. 73-74: com TYRESIDE, o pneu do outro lado é espelhado em relação a α = 0 (troca o sinal de PEY3, PHY1, PHY2, PVY1, PVY2, RHX1, RBY3, RVY1, RVY2 e de termos de Mz/Mx) | mantém (espelhar α, γ e Fy em ISO equivale a trocar o sinal desses termos ímpares) |

### 7.2 Métodos

| Método | Documento | Situação |
|---|---|---|
| Fy0 puro (SUS-501) | Adams eq. 30-44 (p. 30-31) | confere termo a termo, menos o fator λKyγ (`LKYG`) nos termos de camber de S_Hy e S_Vy, que o código não aplica. Com `LKYG = 1` no arquivo, o efeito é zero hoje |
| Ky com um único λFz0 (EDR-049) | Adams eq. 38: K_y0 = p_Ky1·F_z0·sin[2·atan(F_z/(p_Ky2·F'_z0))]·λ_Fz0·λ_Ky, com F'_z0 = λ_Fz0·F_z0 | mantém (idêntico à forma do código) |
| Fx0 puro e combinados (G_xα, G_yκ, S_Vyκ) | Adams eq. 18-29 e 80-99 (p. 27-28, 43-45) | conferem termo a termo |
| α ou tan α (EDR-040) | Adams eq. 4 define α por tan α = V_sy/\|V_x\| e as equações usam α (eq. 32); OptimumT (p. 141) e Pacejka 2006 (eq. 4.E3) usam tan α em outras versões do modelo | mantém α para arquivos PAC2002 (forma do programa para o qual o `.tir` foi feito). A dúvida do EDR-040 sobre "como o OptimumTire ajustou" não se aplica a este arquivo (foi ajustado pela Stackpole, não no OptimumTire) |
| Rigidez vertical K_T = `VERTICAL_STIFFNESS` (SUS-211, EDR-045) | Adams p. 10-14: `VERTICAL_STIFFNESS` só vale com QFZ1 = 0; com QFZ1 ≠ 0, C_z = q_Fz1·F_z0/R_0 | mantém: o arquivo tem QFZ1 = 29,7127 e QFZ2 = 0, e 29,7127 × 1054 / 0,2603 = 120 312 N/m, o mesmo valor. Modelo linear, como no Adams com QFZ2 = 0 |
| IC frontal e lateral cinemáticos (SUS-412) | OptimumKinematics §7.3.3.13, 7.3.3.16 e 7.3.3.20 (p. 93-95): eixo instantâneo do conjunto não suspenso (pequeno deslocamento da roda, com a barra de direção); IC = interseção desse eixo com o plano vertical que passa pelos contact patches (transversal na vista frontal, longitudinal na lateral) | **diferente na construção**: o código projeta as velocidades de dois ball joints no plano da vista e cruza as normais. As duas coincidem quando o eixo instantâneo é perpendicular ao plano da vista; com caster, anti e esterço, não. Diferença não quantificada |
| RC cinemático (SUS-412) | OptimumKinematics §6.10 e §7.3.3.23 (p. 62 e 97): RC = interseção dos planos (eixo instantâneo + contact patch) esquerdo e direito com o plano vertical central; difere do RC geométrico | mesma observação do IC: equivale ao do código só no caso plano |
| Barra anti-rolagem como rigidez pronta | OptimumKinematics §7.3.3.7: MR da barra = ângulo de rolagem / deslocamento angular da barra | simplificação continua válida; com o OptimumKinematics, a rigidez da barra na roda pode sair da geometria |

### 7.3 Pendências da 1ª rodada (seção 6), situação em 2026-10-19

| Pendência | Situação |
|---|---|
| Cap. 19 da Milliken contra SUS-405/408/413 | aberta |
| Modelo de bicicleta e gradiente de subesterço | aberta (só se a planilha ganhar o bloco) |
| Forma exata do Fy0 e dos fatores λ no PAC2002 | **resolvida** (7.2); resta a lacuna do `LKYG` |
| Sinal do IA do TTC (EDR-039) | **resolvida**: o arquivo é ISO (Adams p. 7); trocado para ISO_TYDEX em 2026-10-19 (EDR-039 revisto) |
| Anti-lift com regeneração (EDR-033) | método confirmado pelo OptimumKinematics; faltam os dados de divisão de frenagem da equipe |
| α* = tan α (EDR-040) | **resolvida para PAC2002**: α. A escolha do formato do pneu real (R60A) continua aberta |
| Ressalvas: limiar de MR | sem fonte (nenhum dos documentos dá limiar); decisão da equipe |
| Ressalvas: IC em 3D | definição da REFERENCE conhecida (7.2); falta implementar o método dela e medir a diferença |
| Ressalvas: simplificações (RC fixo, superposição, barra pronta, aero, taxa geométrica do MR) | continuam aceitas; nenhum documento as contradiz |
| K_T do pneu real, hardpoints do CAD, comparação com OptimumKinematics/OptimumTire | dependem de dados |

## 8. 2ª rodada: cap. 19 da Milliken (direção) e definição do IC/RC (2026-10-19)

### 8.1 Cap. 19 da Milliken (p. 709-727), com Gillespie cap. 6 e 8 e Seward 6.3

O capítulo é quase todo qualitativo. As equações vêm do Gillespie e do Seward; a Milliken dá definições, sinais e
recomendações. Decisão: EDR-052 (fichas novas SUS-414, 415 e 416).

| Seção | O que o livro diz | Situação no projeto |
|---|---|---|
| 19.1 Geometria do pino mestre (p. 709-713) | Fig. 19.1: KPI, scrub, spindle length (pino mestre ao plano da roda, na altura do eixo), caster e trail. KPI com spindle positivo levanta o carro nos dois sentidos; caster levanta de um lado e baixa do outro (peso diagonal); caster positivo dá camber negativo na roda externa | Convenções da SUS-410 conferidas (também Gillespie Fig. 8.8). Spindle length acrescentado (TC-KIN-121). Efeitos de camber e elevação: SUS-416 nova (`steer_effects`, TC-KIN-127a/b) |
| 19.2 Ackermann (p. 713-716) | Ackermann = trajetórias com centro comum; para corrida, paralelo ou um pouco de reverso; a compliance pode superar o efeito | Não havia nada no projeto (nem no carro anterior). SUS-414 nova: `cot δo − cot δi = t/L` (Gillespie eq. 8-1/8-2), % Ackermann e raio externo; Tab. 6.2 do Seward reproduzida (TC-KIN-122a); Ackermann da geometria (TC-KIN-123); planilha 07 B72:B76 |
| 19.3 Caixa de direção (p. 716-719) | Razão total = ângulo do volante / ângulo da roda; com cremalheira, SR ≈ função de c e do braço de direção (p. 718) | SUS-601 e SUS-413 revistas: razão total pela média das rodas (SAE J670 9.4.6); aproximação da cremalheira com **errata**: a p. 718 imprime asin(c/braço)/360, inverso da razão da p. 716; adotado 360/asin(c/braço) (conferido na imagem; TC-KIN-124b). Planilha 07 B78:B80 |
| 19.4 Ride e roll steer (p. 721-725) | Ride steer em °/in, curvas lineares são aceitáveis, curvas são "a evitar"; sinal: na frente, esterçar para fora da curva = subesterço | SUS-408 revista (`ride_steer`: inclinação, curvatura, desvio da reta; TC-KIN-125). Roll steer: SUS-415 nova, ε e K = (ε_f − ε_r)·∂φ/∂a_y (Gillespie eq. 6-57, conferida na imagem; TC-KIN-126). Planilha 07 B82:B85 |
| 19.5 Alinhamento (p. 726-727) | Procedimento de medição de toe e camber; regra de bolso camber/esterço | Fora do modelo (procedimento de oficina) |

### 8.2 IC e RC: definição primária no MODEL (EDR-053)

Conselho de 4 lentes com revisão anônima (veredito completo na conversa de 2026-10-19). Conclusão: a grandeza que a
planilha usa é a linha de força, e a definição exata dela é a do trabalho virtual (SAE J670, Gillespie Apêndice A): a
linha passa pelo ponto de reação e é perpendicular à velocidade dele por unidade de curso. Na geometria sintética (FL):

| Método | RC do canto [mm] | Inclinação da linha do anti-dive | %AD (L 1,55; h 0,315; FB 0,6) |
|---|---|---|---|
| Linha de força pelo trabalho virtual (primária) | 17,7 | −0,1307 | 38,6 |
| Ball joints (método anterior, legado) | 14,8 | −0,1230 | 36,3 |
| Leitura literal do help do OptimumKinematics (eixo ∩ plano, passo −0,47 m/rad) | −142,6 | −0,314 | cerca de 93 |

O método anterior depende do par de pontos escolhido (o RC vai de −98,6 a +36,0 mm conforme o par), porque os ball
joints não estão no plano da vista. A leitura literal ignora a translação ao longo do eixo (o passo). As três coincidem
no mecanismo plano (TC-KIN-120a, 128). O que o OptimumKinematics faz de fato com o passo é desconhecido: a comparação,
quando houver dados, começa por curvas que não dependem da definição de IC e por digitar a geometria sintética no
programa (EDR-053).
