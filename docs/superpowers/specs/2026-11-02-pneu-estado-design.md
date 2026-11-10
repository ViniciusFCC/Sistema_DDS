# Subprojeto A: pneu com variação de estado (pressão) — design

Data: 2026-11-02 a 2026-11-03. Brainstorming com o usuário (superpowers:brainstorming, caminho arquitetural), com dois
conselhos (padrão, 4 assentos, sobre o rascunho; leve, 3 assentos, sobre as seções 3 e 4 revistas). Estado: design
aprovado seção a seção pelo usuário; spec revisada e aprovada sem mudanças (2026-11-03). Nada implementado.

## 1. Contexto e progressão

"Parte dinâmica" do pneu foi dividida pelo usuário em três subprojetos, cada um com spec, plano e implementação
próprios: **A. pneu com variação de estado** → **B. transiente do pneu** → **C. dinâmica do veículo**. A vem primeiro
porque é o único com dado real; B fecha o pneu como componente antes de C.

Dentro do A, em progressão: **A1** comparar as pressões discretas (8, 10, 12, 14 psi) e apoiar a escolha da pressão →
**A2** pressão contínua entre 8 e 14 psi → **A3** pressão variando em operação (sem dado; só registro).

## 2. Fonte dos dados

- Só os quatro `.tir` PAC2002 do TTC Round 6, Hoosier R25B 20.5x7-13 em aro de 7 in, 8/10/12/14 psi, fora do Git em
  `references/ttc/round6_hoosier_r25b_20p5x7_13_7in/` (usuário: "Tudo que possuímos já foi enviado"; não há dado bruto
  do TTC nem dado térmico).
- Os perfis são ajustes independentes. Os coeficientes não são monotônicos com a pressão (PDX1 2,85/2,67/2,81/2,39;
  PKY1 −42/−53/−58/−58), o FNOMIN difere (1112 N a 8 psi, 1054 N nos demais) e o FZMAX também (1549/1546/1521/1546 N).
  Só as saídas (forças, μ, Cα) se comparam entre perfis; os coeficientes não.
- Achados dos conselheiros (números do MODEL, reproduzidos como teste na implementação): a 14 psi PCY1 ≈ 0,99 e o
  |Fy| máximo cai na borda ALPMAX (μy "pico" é limitante inferior); PKY2 cresce monotonicamente (1,116/1,408/1,745/1,939)
  e Cα é o sinal mais consistente com a pressão (Milliken, RCVD §2.6, p. 54-55); o erro de interpolação deixando um perfil
  de fora (μy −4 %, Cα −6,5 %, μx −10 a −11 %) é da ordem do efeito da pressão; PKX2/PKX3 instáveis (Fx mal
  condicionado); PDY3 = 2 nos quatro (μy(γ) não informa sobre pressão).
- R25B substitui o R60A da equipe; nem a tendência se transfere com certeza. A pressão do `.tir` é a de ensaio, não a
  pressão fria de box (a confirmar).

## 3. Equações (conferidas na imagem do PDF `references/pdf/Adams_2024_1_PAC2002_help.pdf`)

O PAC2002 tem um modelo de pressão (folhas 21, 28, 31, 34, 50):

- eq. 17: dpi = (pi − p'i0)/p'i0, com p'i0 = λip·pi0;
- eq. 24: μx = (PDX1 + PDX2·dfz)(1 + PPX3·dpi + PPX4·dpi²)(1 − PDX3·γ²)λμx;
- eq. 26: Kx = Fz(PKX1 + PKX2·dfz)·exp(PKX3·dfz)(1 + PPX1·dpi + PPX2·dpi²)λKx;
- eq. 36: μy = (PDY1 + PDY2·dfz)(1 + PPY3·dpi + PPY4·dpi²)(1 − PDY3·γy²)λμy;
- eq. 38: Ky0 = PKY1·Fz0(1 + PPY1·dpi)·sin[2·atan{Fz/(PKY2·F'z0(1 + PPY2·dpi))}]λFz0λKy;
- eq. 54: Dt com (1 − QPZ1·dpi); eq. 58: Dr com (1 + QPZ2·dpi); QPX1 no Mx (folha 50).

Nos quatro `.tir` todos esses termos valem zero, e o `tire_model` não os implementa (recusa PP* ≠ 0 e IP ≠ IP_NOM em
`python/tire_model.py:107`; QPZ1-2 e QPX1 não são conferidos). Por isso este subprojeto **não** usa o modelo de pressão
do PAC2002: ajustá-lo (abordagem 2 do brainstorming) seria um ajuste de ajustes, sem medição, e fica como degrau futuro.

A2 usa interpolação linear das **saídas** entre os perfis vizinhos, no mesmo ponto (Fz, α, γ, κ, vx):
w = (p − p_lo)/(p_hi − p_lo), X(p) = (1 − w)·X(p_lo) + w·X(p_hi) para X ∈ {Fx, Fy, Mx, My, Mz}; μ_eff recalculado de
Fx e Fy. Não estima parâmetro nenhum (compatível com o EDR-015). O pico da curva interpolada obedece
max_α[(1−w)F₁ + wF₂] ≤ (1−w)·max F₁ + w·max F₂ e é reportado como esse intervalo.

## 4. Escopo

**Dentro, nesta ordem:** A1-pneu → A1-carro → A1-escolha → A2-pneu → A3 (registro) e achados do B (registro).

**Fora:** A2 no carro; ajuste PP*/QPZ no OptimumTire e sua implementação (exigiria rever o EDR-015); pressão diferente
entre frente e trás (um `ds` por eixo); raio carregado e altura de rodagem; qualquer mudança na planilha.

## 5. Arquitetura

| Unidade | Papel | Depende de |
|---|---|---|
| `python/tire_model_static.py` (4.2.0) | Comportamento igual, exceto: a mensagem do `at_pressure` cita a rota interpolada e mantém a palavra "Interpolação" (`tests/test_tire_static.py:231`); o loader passa a recusar QPZ1-2 e QPX1 ≠ 0 | `tire_model` |
| `python/tire_pressure.py` (novo) | `evaluate_interpolated` (A2); `metricas_pneu(avaliador, ...)` com o avaliador como função; indicadores `erro_loo` e `assimetria_alfa` | `tire_model_static`, `tire_model` |
| `python/comparacao_pressao.py` (novo) | `comparar_carro(caso, family, ...)`; `escolher_pressao(resultados, criterio, ...)` | `equilibrio`, `tire_pressure` |
| `tools/relatorio_pressao.py` (novo) | `.md` e PNG em `build/` com a família real; nada versionado | os dois módulos |

Sem um Protocol de "avaliador de pneu" agora: a interface do A2 no carro fica para esse degrau (pela rota PP*, o
resultado seria um `.tir`, e o contrato atual do equilíbrio bastaria).

**Rótulos em toda saída:** R25B ≠ R60A (nem a tendência se transfere com certeza); μ absoluto do TTC não transferível;
pressão de ensaio ≠ pressão fria (a confirmar); Validation = NOT_VALIDATED; INTERPOLADO quando for o caso; caso
demonstrativo T09/E03 com coeficientes de 12 psi como linha de base, não o T11.

## 6. A1-pneu: métricas e indicadores

Grade: Fz até o teto comum da família (1521 N) e nas Fz de operação do caso (4 rodas, estática e no a_y limite); o
trecho abaixo da menor carga ensaiada é rotulado "carga ensaiada a confirmar". γ em lista dada (padrão: 0 e o camber
estático do caso).

| Métrica | Definição | Rótulo |
|---|---|---|
| **Cα** e Cα/Fz (principal) | −∂Fy/∂α em α=0, κ=0, via `tire_model.rigidez_deriva` | — |
| Cγ | `tire_model.rigidez_camber` | μy(γ) sem informação de pressão (PDY3 = 2) |
| Cκ | −∂Fx/∂κ em κ=0 | ajuste longitudinal mal condicionado |
| μy pico e α do pico | max\|Fy\|/Fz, α>0 e α<0 separados, κ=0 | pico na borda: "limitante inferior, sem pico interior" |
| μx pico (tração, frenagem) e κ do pico | max\|Fx\|/Fz, α=0 | mesma regra de borda; mal condicionado |
| Penalidade de transferência | Fy_max(Fz0+ΔFz) + Fy_max(Fz0−ΔFz) − 2·Fy_max(Fz0), Fz absoluto | ΔFz dado por quem chama |
| Rigidez vertical | `VERTICAL_STIFFNESS` do `.tir` | valor do arquivo, linear, origem não verificada |
| Anexo: trilha t0 e α do pico de Mz | t0 = −(∂Mz/∂α)/(∂Fy/∂α) em α=0 | pendente do item 3 do EDR-067; fora do A1-escolha |

Indicadores de incerteza, ao lado de cada métrica: erro deixando um perfil de fora (|LOO|, em 10 e 12 psi; ausente em
8 e 14, declarado); assimetria ±α (pico α>0 vs α<0 e Fy em α=0; em parte física: conicidade e ply-steer);
monotonicidade com a pressão. Derivadas por diferença central com o passo do `tire_model` (1e-6). Tabelas sem ranking.

## 7. A1-carro: `comparar_carro`

- Caso da V4.1 lido uma vez; por perfil, `dataclasses.replace(caso, ds=perfil_ajustado)` → `analise_par_dois_sentidos`.
  Recusa receber um `.tir`: `caso_da_planilha_v41` grava a 10_TIRE (coeficientes de 12 psi) por cima do `.tir` e
  devolveria 12 psi em silêncio.
- `perfil_ajustado`: λ ≠ 1 do `ds` do caso copiados (nome ausente no perfil = erro); FZMAX reescrito para o teto comum
  1521 N, rotulado.
- Variantes de rigidez vertical: (a) KTF/KTR do caso, fixos (só aderência); (b) KT = `VERTICAL_STIFFNESS` do perfil nas
  4 rodas (efeito no K_φ).
- Também com a robustez λ existente (`com_fatores`, `varredura_pneu`); hipótese declarada: a perda TTC→pista é a mesma
  em todas as pressões.
- Saída por pressão e variante: a_y_lim, sentido pior, eixo que satura, K, comportamento no limite. `resolucao_ms2` é
  tolerância numérica, não critério de diferença.
- Limitações: `ds` único nas 4 rodas; sem raio carregado, altura de rodagem e cinemática decorrente; Fy em α=0 como no
  modelo (invertido pelo espelhamento nas rodas esquerdas); linha de base demonstrativa.

## 8. A1-escolha: `escolher_pressao`

- Critério explícito, de lista fechada, com o sentido de "melhor": `a_y_lim` (máximo); `C_alpha_operacao` (máximo, na
  Fz estática por eixo). `K` (TARGET-006) e `TARGET-007` só com alvo definido na ficha; hoje são TBD e o código só
  recusa ("meta TBD"). Sem ranking que misture critérios.
- Banda (faixa heurística, não intervalo de confiança):
  - pneu: max(|LOO| da métrica, assimetria ±α, piso numérico);
  - carro: max(|LOO| do carro, `resolucao_ms2`), com o LOO do carro obtido interpolando as **saídas** do carro
    (a_y_lim, K) de 10 psi a partir de 8 e 12, e de 12 a partir de 10 e 14. A assimetria fica fora (já está no
    "sentido pior").
  - 8 e 14 psi: banda não medida; usa-se o maior |LOO| interno, rotulado "limite inferior", e essas pressões nunca são
    declaradas melhor sozinhas.
- Regra simétrica: A e B indistinguíveis se |X_A − X_B| ≤ max(banda_A, banda_B).
- Borda: pressão cujo critério é afetado vira "não decidível" (não é excluída). a_y_lim é afetado quando alguma roda no
  limite chega a ALPMAX naquele perfil; Cα nunca.
- Saída: a melhor (se houver), o conjunto indistinguível, as não decidíveis, critério, variante de KT (roda as duas e diz
  se o veredito muda), bandas e rótulos. "Todas indistinguíveis" é desfecho válido e esperado com estes dados.

## 9. A2: `evaluate_interpolated(family, p, fz, α, γ, κ, vx)`

Interpolação da §3. Na pressão exata, resultado bit a bit igual ao `evaluate_static`. Recusa: fora de [8, 14] psi, fora
da interseção das faixas dos vizinhos, vizinhos com `revision_id` diferentes. Resultado com INTERPOLADO, pesos,
vizinhos, SHA de cada `.tir`, |LOO| do trecho e o aviso de que entre 12 e 14 psi a mistura junta uma curva com pico e
outra sem pico. Métricas recalculadas sobre a curva interpolada; pico como intervalo. Fora das tabelas do A1 e do
A1-escolha.

## 10. Testes previstos

`tests/test_tire_pressure.py`, script com `check()` como os demais; sem os `.tir` sai NÃO EXECUTÁVEL (nunca aprovado).
Registrado em `tools/rodar_testes.py` com a contagem que o teste tiver.

1. A2: identidade bit a bit nas pressões exatas.
2. A2: componentes entre os vizinhos e cota do pico max(mistura) ≤ mistura(max); μ_eff só pela cota superior.
3. A2: recusas (fora de [8, 14], fora da interseção, revisões diferentes).
4. Cα das métricas = `tire_model.rigidez_deriva`.
5. μ pico contra varredura fina independente, nos dois sentidos de α.
6. Borda detectada nos 14 psi ("sem pico interior").
7. t0 pela razão de derivadas contra diferença finita independente.
8. Família sintética linear em p: LOO = 0; quadrática: LOO igual ao erro analítico.
9. `comparar_carro` = chamada direta com o `ds` do perfil; os quatro casos dão Fy diferentes; recusa de `.tir`.
10. Âncora: perfil de 12 psi com λ e FZMAX ajustados reproduz `analise_par_dois_sentidos(caso)` dentro de `resolucao_ms2`.
11. λ propagados ou recusados; FZMAX reescrito e rotulado; variante (b) de KT muda o K_φ.
12. `escolher_pressao`: veredito, empate parcial, empate total, simetria da regra, pressão de borda "não decidível",
    extremos nunca melhores sozinhos, recusa de critério TBD.
13. Guarda QPZ1-2/QPX1 no loader; `tests/test_tire_static.py` continua 87/87 e o pneu 43/43.

## 11. IDs (autorizados pelo usuário em 2026-11-03: "Autorizo")

- **EDR-071** (EDR-068 e EDR-069 já estão em uso em outras branches; o EDR-070 foi para o incremento 8, V4.4; o 071 foi autorizado pelo usuário em 2026-11-09 e confirmado livre em todas as branches): pressão
  com interpolação rotulada de saídas (emenda o item 6 do EDR-067), regra da banda e critérios do A1-escolha, guarda
  QPZ/QPX1, limitações e degraus futuros.
- **TC-TIRE-011** em diante, para os testes da §10.

## 12. A3 e B (registro)

- **A3:** sem implementação. O PAC2002 não tem termo térmico; a variável escondida é a temperatura (Milliken p. 55-56);
  a pressão do `.tir` é a de ensaio; falta dado de pressão e temperatura em pista e um modelo térmico.
- **B:** os `.tir` têm PTX1-3 = 0, PTY1-2 = 0 e USE_MODE = 4: não há σ (comprimentos de relaxação). Não usar valor
  típico como dado. Fonte possível: medir a rigidez lateral da carcaça do pneu da equipe em bancada e usar
  σα = C_Fα/C_Fy (Pacejka, TVD). Equações no help do Adams, folhas 53-55 (eq. 121-139, linear) e 55-60 (eq. 140-170,
  não linear). A rigidez da carcaça varia com a pressão: o B herda o eixo de pressão do A.
- **Degraus futuros:** A2 no carro; ajuste PP*/QPZ (rever EDR-015; a recusa de PP* do loader); `ds` por eixo para
  pressão diferente entre frente e trás.
