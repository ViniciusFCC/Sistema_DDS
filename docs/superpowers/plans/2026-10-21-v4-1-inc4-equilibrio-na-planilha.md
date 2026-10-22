# V4.1, incremento 4 (equilíbrio na planilha): plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar a planilha `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` a partir da V4.0 da tag `v4.0`, com o equilíbrio em fórmulas: gradiente de subesterço K pelas parcelas (passo 1), análise de par no limite com as regras do EDR-056 (passo 2), chaves de hipótese, tabela de troca da barra dianteira, exibição da spec §7.3 (D15, D16), dashboard e as páginas "cadeia de decisão" e "o que o modelo cobre". O Python (`equilibrio.py`, `equilibrio_linear.py`) é o oráculo de cada bloco.

**Architecture:**
- `python/aba_equilibrio.py` (novo) escreve as abas novas num workbook do openpyxl a partir de **famílias de fórmula** (o catálogo abaixo). Cada família é uma função que devolve o texto da fórmula para uma linha/coluna; nenhuma célula é escrita fora delas.
- `python/gerar_v4_1.py` (novo) extrai a V4.0 da tag `v4.0` para uma pasta temporária, chama `aba_equilibrio`, acrescenta os nomes novos (`data/nomes_V4_1.csv`), aplica as alterações aprovadas em células existentes e grava o registro de células. Mesmo padrão de recusas de `gerar_v4_0.py`.
- Testes sem motor (`tests/test_v4_1.py`) e com motor (`tests/test_workbook_v4_1.py`, EDR-044), mais `tests/mutation_planilha_equilibrio.py`. O Python lê cada caso pela planilha (`caso_planilha.caso_da_planilha_v41`, por nomes) e compara.

**Tech Stack:** Python 3.13, openpyxl, `tests/recalculo_planilha.py` (Excel via COM ou LibreOffice), scripts com `check()`.

**Spec:** `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` §5 (itens 3 e 4), §6, §7.1-7.4, §7.6 (item 4), §8.2, §9, §10 (incremento 4), §12.1. Decisões: EDR-055, EDR-056, EDR-057, EDR-058. Evidência de viabilidade: `docs/v4-0/inc1-viabilidade-e-robustez-edr056.md` §5-6 (regra antiga: 4677 células, 0,6 s no Excel, 4,3 s no LibreOffice).

## Decisões do plano (o controlador escolheu onde uma opção domina; registrar no EDR-060)
1. **Robustez ao pneu (D15) fica no relatório do Python.** As 27 combinações do EDR-055 exigiriam 54 análises completas em fórmulas. A spec (§7.6, item 4) prevê exatamente esta saída: a célula mostra o veredito nominal e o aviso fixo "robustez ao pneu: ver relatório docs/v4-1/inc4-equilibrio-na-planilha.md (não recalculada na planilha)". Nenhum número do Python é copiado (§7.5).
2. **Um sentido de curva por vez (h7).** Entrada "Sentido da curva" (Esquerda/Direita). Com "Direita", as fórmulas trocam as entradas L↔R e o sinal do CG lateral e do ganho de camber, como `equilibrio.espelhar`; a planilha mostra o sentido escolhido e o texto "troque o sentido para ver o outro". Calcular os dois dobraria as abas de grade.
3. **Diferencial aberto (h10)** é declarado em texto, sem chave: é o único tipo que a planilha implementa (spec 7.4).
4. **Pico de Fx (h9) pela forma fechada** D_x + S_Vx, válida quando o κ do pico cai em [max(0, KPUMIN), KPUMAX]; fora disso a linha fica N/A com o motivo "pico de Fx fora da forma fechada". O Python usa máximo numérico nesse caso; no `.tir` atual o κ do pico (0,065-0,092) fica dentro, sem efeito.
5. **Ângulos necessários (α_0 e a coluna de inclinação do K) por Newton** em colunas fixas (8 iterações, a partir de −req/C), com bandeira de convergência |folga| < 1e-9·req; sem convergência, N/A. O Python usa bissecção; as duas acham a mesma raiz no ramo normal (Review Focus 2).
6. **Rótulo da parcela de deslocamento:** passa de "deslocamento do pneu (conicidade e ply steer)" para **"deslocamento com a carga (ply steer, conicidade, toe e camber estático)"**, no Python (`texto_k`), na planilha, na spec §6 e no EDR-057 (nota). Motivo: com toe ou Ackermann a parcela é dominada pelo toe × ΔFz (revisão final do incremento 2).
7. **Tabela de troca:** o tamanho (quantos valores de K_ARB dianteiro, e se cada linha usa a grade refinada) só se decide no portão da Task 4, com o tempo medido.

## Autorizações a pedir antes de executar (CLAUDE.md)
1. **IDs SUS na faixa SUS-10XX (D18):**
   - SUS-1001 gradiente de subesterço K e parcelas (Gillespie cap. 6);
   - SUS-1002 curva e capacidade de eixo (Milliken §7.1);
   - SUS-1003 saturação de cada eixo e a_y limite;
   - SUS-1004 veredito no limite (PUSH/LOOSE/NEUTRO) e C_N residual;
   - SUS-1005 resolução numérica da saturação (EDR-056);
   - SUS-1006 tabela de troca e perda em relação ao neutro (spec §5, itens 3 e 4);
   - SUS-1007 Δt no skidpad (t = 2π√(R/a_y));
   - SUS-1008 velocidades característica e crítica (Gillespie p. 203-204).
2. **EDR-059**, revisão do EDR-005: domínio "Equilíbrio / dirigibilidade" na faixa SUS-10XX (D9, D18; a spec §11 diz que a revisão nasce no incremento que cria o primeiro ID da faixa).
3. **EDR-060**, "Equilíbrio na planilha V4.1": as decisões 1-7 acima, o catálogo de fórmulas, as chaves e as alterações em células existentes aprovadas.
4. **IDs de teste TC-WB41-001 a 006** (tabela "Contagem de testes").
5. **Fórmulas:** o catálogo abaixo, por família. O texto exato de cada célula sai em `docs/registro-de-versoes-V4_1-celulas.md` (gerado), e o TC-WB41-001 confere que toda célula nova pertence a uma família aprovada.
6. **Alterações em células existentes** (cada uma com aba, célula, antes, depois; precisa de aprovação própria):
   - (a) **10_TIRE alinhada ao EDR-056:** as fórmulas que hoje devolvem N/A fora da faixa (DR-013, EDR-037, EDR-041) passam a limitar Fz e γ à faixa, com o aviso na linha de status da coluna. Sem isso a planilha mostra, para a mesma roda, N/A na 10_TIRE e um valor limitado na aba de equilíbrio.
   - (b) **Textos da §12.1:** 13_VALIDATION A25 (nome e contagem atuais: `suspension_model.py`, 54 testes); 00_README A8 (nomes do EDR-043); 14_DASHBOARD A19 ("Status de Validação" → "Status de verificação (identidades algébricas, EDR-007)"). O 04_DECISION_REGISTER D8 fica como está (fato a confirmar com a equipe).
   - (c) **00_README A3** (versão V4.1) e a linha nova do 15_CHANGELOG, como na V4.0.
7. **Ganho de camber em rolagem:** derivar ∂γ/∂φ de cada roda das entradas existentes SUS-404-F/R (07_KINEMATICS B23/B24, dγ/dz em °/mm) por `kinematics_model.camber_gradient_from_body` (EDR-050: valor derivado entra como fórmula). Aviso: o valor demonstrativo atual (−0,6 °/mm) dá ∂γ/∂φ ≈ −5,7 rad/rad, implausível, e o camber em curva vai ser limitado ao CAMMIN/CAMMAX com aviso. Alternativa: entrada nova "ganho de camber em rolagem" com 0 = sem dado (EDR-036).

## Global Constraints
- A V4.1 parte do arquivo `excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx` da tag `v4.0` (`git show v4.0:...`), extraído para uma pasta temporária. Saída em `build/`; a cópia para `excel/` é um commit próprio. Nenhuma ferramenta salva ou recalcula a viva `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`.
- As 387 fórmulas da V4.0 ficam com texto idêntico, salvo as células aprovadas no item 6. Os 698 nomes da V4.0 ficam iguais.
- Abas novas, nessa ordem, depois da 15_CHANGELOG: `16_EQUILIBRIO` (entradas, chaves, resultados, exibição), `17_EQ_PAR` (grade pedida), `18_EQ_PAR_FINA` (grade refinada), `19_EQ_LINEAR` (passo 1), `20_EQ_TROCA` (tabela de troca), `21_COBERTURA` (o que o modelo cobre), `22_CADEIA` (cadeia de decisão).
- Grade pedida: a_y = k·0,05 g, k = 0…40; 25 valores de α. Grade refinada: passo 0,025 g, 49 valores de α (`analise_par`: passo/2 e 2·n − 1). Passo 1: a_y = k·0,05 g, k = 0…8, mais 0,005 g e 0,01 g (Richardson).
- Toda entrada nova tem Origem (coluna E, lista `Origens`) e Fonte (coluna F), entra em `celulas_de_entrada_v41()` e tem nome `ent_16_...` (regras de nome do EDR-058). Padrões: toe 0 e CG lateral 0 com origem "? A confirmar" (sem dado, EDR-036); R, CzA, ρ, CdA, Crr vazios ("a confirmar"); chaves h2, h3, h7 (CG lateral), h8, h9 em 0 (desligadas).
- Chave ligada com entrada vazia dá N/A com o motivo "<entrada> a confirmar", nunca 0 em silêncio. h2, h3, h8 e h9 exigem R; h8 substitui a downforce fixa (EDR-013) e mostra isso em texto.
- Todo resultado novo tem nome `res_16_...` (ou da aba da grade) e, ao lado, a pior origem viva (fórmula `INDEX(Origens, MAX(...))` de `atualizar_planilha._formula_pior_origem`, sobre as raízes de `raizes.Grafo`), incluindo a origem do pneu (10_TIRE I84).
- Textos de exibição idênticos aos do Python: `equilibrio.texto_veredito` e `equilibrio_linear.texto_k` (vírgula decimal, prefixo "DEMONSTRATIVO · " pela D16). Cor só como reforço: azul (push), laranja (loose), por formatação condicional.
- SI nas células de cálculo; °, °/g e g só nas células de exibição. Convenções ISO 8855 e EDR-002 (CLAUDE.md).
- Branch `feat/v4-1-inc4-equilibrio` (da ponta de `main`, 28aa281). Commits separados por propósito, com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Push e PR só com pedido.

## Catálogo de fórmulas (aprovação por família; spec §7.1 e §6)
Cada linha é uma família; o oráculo é a função do Python que o teste compara. "k" é a linha da grade, "c" a roda, "i" o índice de α.

| # | Aba, faixa | Fórmula (forma) | Oráculo |
|---|---|---|---|
| F1 | 16, entradas efetivas | Entradas da curva à esquerda equivalente: com "Direita", troca FL↔FR, RL↔RR e inverte CG lateral (decisão 2) | `espelhar` |
| F2 | 16, ganho de camber | ∂γ_R/∂φ = (t/2)·dγ_R/dz + 1; ∂γ_L/∂φ = −(t/2)·dγ_L/dz − 1 (dγ/dz de °/mm para rad/m) | `camber_gradient_from_body` |
| F3 | 16, Δα por roda | toe (ISO, EDR-002) + Ackermann (δ_i, δ_o de % Ackermann, L, t, R) − δ_ref, δ_ref = L/R; cos δ_ref | `deriva_total`, `_cos_dianteira` |
| F4 | 17/18, Fz por roda | estática com CG lateral + ΔFz lateral de três massas com termo gravitacional (SUS-103) + aero (fixa ou 0,5·ρ·CzA·a_y·R) | `cargas` |
| F5 | 17/18, γ por roda | estático (10_TIRE B24:E24) + ∂γ/∂φ·φ(a_y), φ do SUS-103 | `camber` |
| F6 | 17/18, entrada limitada | Fz_u = MIN(MAX(Fz, FZMIN), FZMAX); γ_u idem com CAMMIN/CAMMAX; Fz ≤ 0 = descolamento; bandeira e excesso da limitação | `_entrada_limitada`, `_descolamento` |
| F7 | 17/18, termos PAC2002 | dfz, γy, Ky, SHy, μy, Dy, By, SVy, Ey (como o protótipo do incremento 1, com Fz_u e γ_u) | `wheel_forces` (κ = 0) |
| F8 | 17/18, Fy do eixo em α_i | soma das duas rodas no α_i + Δα_c, espelho e sinal ISO; × cos δ_ref na frente; × √(1 − (Fx/Fx_max)²) por roda atrás com h9 | `_fy_eixo_limitado` |
| F9 | 17/18, tração (h9) | Fx = 0,5·ρ·CdA·a_y·R + Crr·m·G + F_yf·tan δ_ref, metade por roda; Fx_max pela forma fechada (decisão 4) | `fx_exigido_traseira`, `fx_max_puro` |
| F10 | 17/18, capacidade | MAX sobre α; índice do pico (MATCH); pico na borda = inválido | `capacidade_eixo` |
| F11 | 17/18, exigida, folga, saturação | req_f = m·a_y·b/L, req_r = m·a_y·a/L; folga; prefixo válido; interpolação na 1ª troca de sinal | `forca_exigida`, `_saturacao` |
| F12 | 16, veredito | resolução = max(|S − S_fina|, piso 1e-9·G) (passo se um eixo só satura numa grade); regras do EDR-056 itens 2 e 3; C_N; motivo do N/A | `_resolucao`, `analise_par` |
| F13 | 19, rigidez de eixo | C = −[Fy(α_0 + h) − Fy(α_0 − h)]/(2h), h = `tire_model._H_RIGIDEZ`; C_γ idem em γ_eixo (centro dentro de [CAMMIN + h, CAMMAX − h]) | `_rigidez_eixo`, `_rigidez_camber_eixo` |
| F14 | 19, parcelas | k_pneus, k_transferência, k_deslocamento (h_ay = 1e-4·G), k_camber, k_roll_steer, k_total | `parcelas_k` |
| F15 | 19, ângulos necessários e inclinação | Newton (decisão 5); inclinação por diferença entre linhas; Richardson 2·S(0,005 g) − S(0,01 g) na 1ª | `angulos_necessarios`, `tabela_linear` |
| F16 | 16, apoio | S_f, S_r, a_y limite, C_N, resolução, limitações (texto), Δt = 2π√(R/a_y_lim), V_char/V_crit | `analise_par`, `velocidade_caracteristica`, `velocidade_critica` |
| F17 | 16/14, textos | `texto_veredito` e `texto_k` em fórmula; "regimes diferentes (Milliken p. 313-315)"; aviso de robustez (decisão 1); pior origem | `texto_veredito`, `texto_k` |
| F18 | 20, tabela de troca | por valor de K_ARB dianteiro: λ_f, K, S_f, S_r, veredito, C_N; a_y do neutro por interpolação do cruzamento de S_r − S_f; perda = a_y_neutro − a_y_lim | `analise_par`, `parcelas_k` com o ARB trocado |
| F19 | 14_DASHBOARD, linhas novas | K e veredito (texto de F17) com a pior origem | F17 |

Fora das famílias: textos fixos das abas 21 e 22 (sem fórmula, ou com referência simples `=nome`), e as alterações do item 6.

## Contagem de testes (pedido do usuário: poucos checks, com as asserções agrupadas)
| Check | O que junta | Script |
|---|---|---|
| TC-WB41-001 | estrutura: abas e ordem; 387 fórmulas antigas idênticas fora do item 6; toda célula nova numa família do catálogo; nomes válidos e únicos (698 antigos iguais); todo resultado novo com nome e pior origem; entradas novas com Origem/Fonte e em `celulas_de_entrada_v41()` | `tests/test_v4_1.py` |
| TC-WB41-002 | CA-07 da V4.1 (regeneração = `excel/…V4_1.xlsx`, com nomes); recusas do gerador (saída em `excel/`, saída = origem) | `tests/test_v4_1.py` |
| TC-WB41-003 | motor: 0 erros; equivalência por valor com a V4.0 em todo `res` antigo fora das células alteradas; nomes novos sem `#NAME?`; tempo de recálculo no log; Excel: salvar a cópia mantém nomes, validações e formatação condicional | `tests/test_workbook_v4_1.py` |
| TC-WB41-004 | passo 2 × Python nos casos C1-C5: Fz, γ, capacidade e folga por linha (rel. ≤ 1e-9), S_f, S_r, resolução, veredito, C_N, limitações | `tests/test_workbook_v4_1.py` |
| TC-WB41-005 | passo 1 × Python nos casos C1-C5: parcelas e k_total (abs. ≤ 1e-6 °/g), inclinação, igualdade da 1ª linha | `tests/test_workbook_v4_1.py` |
| TC-WB41-006 | tabela de troca × Python; textos de exibição iguais aos do Python, com e sem o prefixo D16 (caso com todas as origens "● Dado do TX", só na cópia) | `tests/test_workbook_v4_1.py` |

Mutação (sem ID, como `mutation_tire.py`): `tests/mutation_planilha_equilibrio.py`, 5 mutantes no gerador (a↔b na força exigida; sem cos δ; Ackermann invertido; sinal do ganho de camber; pior origem trocada pela melhor), cada um pego pelos TC-WB41-004 a 006. Esperado 5/5.

Casos (valores de teste injetados só nas cópias, rotulados; não são o carro):
- **C1** a V4.1 como gerada (demonstrativo).
- **C2** simétrico: t_R = t_F, a = b, massas, molas, MR, barras e RC iguais nos eixos, LMUY da 10_TIRE 0,45 → NEUTRO.
- **C3** C2 com K_ARB dianteiro × 3 → PUSH; **C3b** traseiro × 3 → LOOSE.
- **C4** hipóteses ligadas: R 8 m, h2 (% Ackermann da 07), h3, CG lateral 10 mm (h7), sentido "Direita", h8 (ρ 1,2, CzA 2,0, downforce 0), h9 (CdA 1,0, Crr 0,015), toe 0,25° na frente.
- **C5** h_CG alto até a roda interna descolar antes de saturar → N/A por descolamento.

## Review Focus
1. **Chave ligada com a entrada vazia** (por exemplo h8 sem CzA, h2 sem R). Esperado: N/A com "<entrada> a confirmar", nunca o resultado da chave desligada. Teste no TC-WB41-004 (C4 com CzA apagado numa variante).
2. **Newton fora do ramo da bissecção** (Fy em α = 0 já acima da exigência, carro assimétrico). Esperado: o mesmo α do Python ou N/A, nunca outra raiz. Teste: C4 em a_y = 0 com CG lateral, TC-WB41-005.
3. **Grade refinada e pedida em desacordo** (um eixo satura numa e não na outra). Esperado: resolução = passo pedido (regra de `_resolucao`). Teste: variante de C3 com saturação perto de 2 g, TC-WB41-004.
4. **Entrada de pneu limitada só na grade refinada.** Esperado: o aviso de limitação cita só as linhas da grade pedida usadas no veredito, como `_limitacoes`. Teste: C1, TC-WB41-004.
5. **Equipe digita texto numa entrada numérica nova** ("8 m", vírgula como texto). Esperado: validação de dados recusa na digitação; colado por cima, as fórmulas dão N/A com motivo, nunca `#VALUE!`. Teste: TC-WB41-003 (cópia com texto colado em R).

---

### Task 1: Python: rótulo do deslocamento e caso da planilha por nomes

**Files:** Modify `python/equilibrio_linear.py` (`texto_k`), `python/caso_planilha.py`, `tests/test_equilibrio_linear.py` (textos esperados), `docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md` §6 (nota datada).

**Interfaces:**
- Produces: `caso_planilha.ENTRADAS_CASO: dict[str, str]` (chave → nome definido da V4.0, os mesmos 23 itens); `caso_da_planilha(xlsx_recalculado, tir)` igual por fora, lendo pelos nomes (resolução de `dados_planilha` ou `wb.defined_names`); `caso_da_planilha_v41(xlsx_recalculado, tir) -> CasoEquilibrio` com as entradas novas da 16 (toe, R, % Ackermann, CG lateral, sentido, CzA, ρ, CdA, Crr, chaves) e o ganho de camber de F2; `pior_origem_do_caso_v41(xlsx_formulas) -> str`.
- [ ] **Step 1:** ajustar os esperados de texto em `tests/test_equilibrio_linear.py` para o rótulo novo (decisão 6) e ver falhar.
- [ ] **Step 2:** trocar o texto em `texto_k`; `ENTRADAS_CASO` por nomes. Rodar `tests/test_equilibrio_linear.py` (18 PASS) e `tests/test_equilibrio.py` (28 PASS).
- [ ] **Step 3:** `caso_da_planilha_v41` fica para ser exercitado na Task 2 (precisa das abas); aqui só a função e um teste de recusa já coberto pelo `ValueError` de célula vazia.
- [ ] **Step 4: Commit** `fix: rótulo da parcela de deslocamento com a carga e caso da planilha por nomes`.

### Task 2: Entradas, chaves e análise de par em fórmulas (16, 17, 18)

**Files:** Create `python/aba_equilibrio.py`, `tests/test_workbook_v4_1.py` (padrão de `tests/test_workbook_v4_0.py`; sem motor: NÃO EXECUTÁVEL, código 3).

**Interfaces:**
- Produces: `montar(wb) -> list[dict]` (escreve as abas 16-18 e devolve o registro {aba, cel, familia, formula}); `ENTRADAS_V41: list[tuple[nome, aba, celula, padrao, unidade, rotulo]]`; `celulas_de_entrada_v41() -> set[tuple[str, str]]` (V4.0 + novas); `NOMES_V41: list[Nome]` (formato de `nomes_v4_0.Nome`); helper de teste `copia_v41(tmp, alteracoes: dict[nome, valor]) -> Path` (V4.0 da tag + `montar` + injeção por nome, numa pasta temporária).
- [ ] **Step 1: TC-WB41-004** com C1-C5, comparando com `analise_par(caso_da_planilha_v41(...))` célula a célula (Fz, γ, capacidade, folga) e no resumo; ver falhar.
- [ ] **Step 2:** implementar F1-F12 e F16 (parte do limite). Rodar com `DDS_RECALC=excel` e `DDS_RECALC=libreoffice`; diferença entre motores é relatada, não ajustada.
- [ ] **Step 3:** anotar no log do teste o tempo de recálculo e o número de células de cada aba (insumo do portão).
- [ ] **Step 4: Commit** `feat: análise de par em fórmulas com as regras do EDR-056 (V4.1)`.

### Task 3: Passo 1 em fórmulas (19)

**Files:** Modify `python/aba_equilibrio.py`, `tests/test_workbook_v4_1.py`.

**Interfaces:** Consumes `montar` e as células de 16/17. Produces as células `res_19_*` de K por linha e o K da 1ª linha em `res_16_k_total`.
- [ ] **Step 1: TC-WB41-005** (C1-C5 contra `tabela_linear(caso, pior_origem=...)`), com a igualdade k_pneus + k_deslocamento + k_camber = inclinação na 1ª linha (rel. ≤ 1e-6); ver falhar.
- [ ] **Step 2:** implementar F13-F15 e V_char/V_crit (F16). **Step 3:** rodar nos dois motores. **Step 4: Commit** `feat: gradiente de subesterço por parcelas em fórmulas (V4.1)`.

### Task 4: Portão de viabilidade (decisão do usuário)

**Files:** Create `docs/v4-1/inc4-viabilidade-tabela-de-troca.md` (gerado por um modo `--medir` de `tests/test_workbook_v4_1.py`).
- [ ] **Step 1:** medir, nos dois motores, o recálculo da V4.1 com as abas 16-19 e com 1, 3 e 5 linhas da tabela de troca (cada linha = uma análise na grade pedida, e a mesma com a refinada).
- [ ] **Step 2:** levar ao usuário os números e a pergunta: quantos valores de K_ARB dianteiro (grade de exibição rotulada, não meta) e se cada linha mede a resolução. Sem limiar registrado, o tempo não decide sozinho (spec §9, item 10). **Parar até a resposta.** A resposta entra no EDR-060.

### Task 5: Tabela de troca (20)

**Files:** Modify `python/aba_equilibrio.py`, `tests/test_workbook_v4_1.py`.
- [ ] **Step 1: TC-WB41-006 (parte 1):** para cada linha, `analise_par` e `parcelas_k` com o caso de K_ARB trocado; a_y do neutro e perda (spec §5, item 4: cruzamento por interpolação, nunca S_r − S_f); "limiar não definido" sem veredito de custo (§5, item 5). Ver falhar.
- [ ] **Step 2:** implementar F18 com o tamanho decidido na Task 4. **Step 3:** rodar. **Step 4: Commit** `feat: tabela de troca da barra dianteira (V4.1)`.

### Task 6: Exibição, dashboard e páginas (16, 14, 21, 22)

**Files:** Modify `python/aba_equilibrio.py`, `tests/test_workbook_v4_1.py`.
- [ ] **Step 1: TC-WB41-006 (parte 2):** textos da 16 e do dashboard iguais a `texto_veredito`/`texto_k` em C1-C5; sem o prefixo D16 numa cópia com todas as origens "● Dado do TX"; aviso de robustez presente; "regimes diferentes" ao lado. Ver falhar.
- [ ] **Step 2:** implementar F17, F19, as cores (azul/laranja, formatação condicional), o texto do diferencial aberto e do sentido da curva.
- [ ] **Step 3:** abas 21 e 22, só texto e `=nome`:
  - 21_COBERTURA: a tabela 7.4 da spec (hipótese, base, planilha, chave, efeito se ignorada) e o "Fora" da §2.
  - 22_CADEIA: objetivo → comportamento → parâmetro (§4.1) para o equilíbrio: entradas → K_φ e λ_f → Fz por roda → curvas de eixo → saturações → veredito → tabela de troca → ficha (incremento 5), com o nome de cada célula.
- [ ] **Step 4:** rodar. **Step 5: Commit** `feat: exibição do equilíbrio, dashboard e páginas de cobertura e cadeia (V4.1)`.

### Task 7: Gerador da V4.1, alterações aprovadas e planilha de referência

**Files:** Create `python/gerar_v4_1.py`, `data/nomes_V4_1.csv`, `tests/test_v4_1.py`; Modify `tests/test_workbook_v4_1.py` (passa a usar a V4.1 de `excel/`).

**Interfaces:** `alteracoes_v4_1() -> list[dict]` (item 6 aprovado, cada uma com aba, cel, antes, novo, ref); `gerar(caminho_v40: Path, saida: Path) -> list[dict]` (recusas como `gerar_v4_0.gerar`); CLI `uv run python -X utf8 python/gerar_v4_1.py [--v40 ARQ] [--saida build/FSAE_EV_Suspension_Fase1_V4_1.xlsx] [--registro docs/registro-de-versoes-V4_1-celulas.md]`.
- [ ] **Step 1: TC-WB41-001, TC-WB41-002 e TC-WB41-003**; ver falhar.
- [ ] **Step 2:** implementar; aplicar o item 6 só no que o usuário aprovou (o 6a muda fórmulas da 10_TIRE: rodar também `tests/test_workbook.py`, cujos esperados fora da faixa mudam e são ajustados com a justificativa no registro).
- [ ] **Step 3:** gerar e rodar tudo nos dois motores.
- [ ] **Step 4: Commits:** `feat: gerador da V4.1 a partir da tag v4.0`; separado, `feat: planilha V4.1 de referência gerada`, com o xlsx e o registro de células.

### Task 8: Mutação da planilha do equilíbrio

**Files:** Create `tests/mutation_planilha_equilibrio.py` (padrão de `tests/mutation_equilibrio.py`: aplica cada mutante ao gerador numa cópia, regenera em pasta temporária e roda TC-WB41-004 a 006).
- [ ] **Step 1:** os 5 mutantes da tabela; esperado `5 / 5`. **Step 2: Commit** `test: mutação da planilha do equilíbrio (V4.1)`.

### Task 9: Relatório, EDRs, registro e suíte

**Files:** Create `tools/relatorio_inc4.py`, `docs/v4-1/inc4-equilibrio-na-planilha.md`, `docs/registro-de-versoes-V4_1.md`; Modify `docs/Engineering_Decision_Register.md` (EDR-059, EDR-060, índice, rastreabilidade, nota no EDR-057), `tools/rodar_testes.py`, `CLAUDE.md`, spec §7.6 item 4 e §7.4 h7 (notas datadas).
- [ ] **Step 1:** relatório do caso da V4.1: resultado nominal, limitações, varredura do EDR-055 (`varredura_pneu` sobre `caso_da_planilha_v41`, o que a célula de robustez remete) e os tempos.
- [ ] **Step 2:** EDR-059 e EDR-060 (Record_Status conforme o usuário).
- [ ] **Step 3:** `tools/rodar_testes.py`: `TESTES` += `test_v4_1.py` (2); `PLANILHAS` += `test_workbook_v4_1.py` (4); `MUTACAO` += (`tests/mutation_planilha_equilibrio.py`, 5); CA-07 += regeneração da V4.1; versão do 00_README!A3 vale para a V4.1. `CLAUDE.md`: V4.1 de referência, gerador, esperados.
- [ ] **Step 4:** suíte inteira em segundo plano: tudo PASS.
- [ ] **Step 5: Commits:** `docs: EDR-059 e EDR-060 (equilíbrio na planilha V4.1)`; `docs: relatório do incremento 4 e registro de versões da V4.1`; `test: registra a V4.1 na suíte`.
