# Incremento 8 (pendências do inc. 7 e V4.4 por nomes) — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** fechar as pendências 1 a 12 do inc. 7 (8a) e gerar a V4.4, em que as fórmulas das abas 03 a 14 leem por nome toda
célula única, com os mesmos valores da V4.3, provados por texto, por invariante e por valor (8b).

**Architecture:** a 8a só mexe em Python, testes e documentos, um commit por propósito. A 8b acrescenta três módulos:
`python/reescrita_nomes.py` (medição e regra da troca, pelo `Tokenizer` do openpyxl), `python/nomes_v4_4.py` (os 23 nomes
novos) e `python/gerar_v4_4.py` (V4.3 da tag `v4.3` → V4.4 em `build/`). Os testes ficam em `tests/test_v4_4.py` (texto,
TC-WB44-001 a 004) e `tests/test_workbook_v4_4.py` (motor, TC-WB44-005 e 006). A mutação fica em
`tests/mutation_planilha_v44.py`. Uma única suíte inteira, no fim.

**Tech Stack:** Python 3.13 (uv), openpyxl (`Tokenizer`), Excel via COM (`tests/recalculo_planilha.py`) com o LibreOffice de
reserva (EDR-044), testes em script com `check()` (não pytest).

**Spec:** `docs/superpowers/specs/2026-11-09-inc8-fundacao-nomes-design.md` (commit 1b3c1d8). Entrada da 8a:
`docs/passagem-2026-11-09.md`. Passagem do brainstorming: `docs/passagem-2026-11-09-inc8-plano.md`.

## Itens para a aprovação do usuário (antes da execução)

O plano só é executado depois que o usuário aprova os itens A1 a A5. Os itens D1 a D6 são decisões do controlador,
registradas para ele saber; qualquer uma pode ser revertida na aprovação.

**Aprovação (usuário, 2026-11-09): A1 a A5 aprovados como estão.** D1 a D6 não foram revertidas. Continuam pendentes: a
lista de ramos não cobertos (Task 16, Step 4) e os passos do fechamento (Task 20).

### A1. Nomes novos: 23, não 9 (`data/nomes_V4_4.csv`)

A medição refeita (2026-11-09, `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`, SHA `b3da017f…`) achou um erro na §3.1 da
spec: as "9 células soltas" eram **9 referências a 6 células** (13_VALIDATION B37:B39 e 16_EQUILIBRIO E188:E190). E das 118
referências da 10_TIRE que a spec chamou de "blocos do `.tir`", 114 apontam para **17 células únicas** sem nome (só 4 são
intervalos). Pelo invariante da §3.5 ("nunca uma folga no invariante"), o plano dá nome às 23 células.
Alternativa recusada pelo controlador: só 6 nomes e a 10_TIRE inteira como exceção do invariante. O motivo é que essa
exceção deixaria 114 referências por endereço justamente na aba do pneu, a de maior risco.

Regras (EDR-058, `python/nomes_v4_0.py`): `<papel>_<aba2>_<slug do rótulo da coluna A>`; na 10_TIRE, as células de caso
(B a F, linhas com casos) levam `_<coluna>`. Papel: célula sem fórmula = `ent` (`_papel_entrada`; na 10_TIRE a coluna I =
`org`); célula com fórmula = `res`. Colisão com nome existente: o nome novo leva `_<célula>`, porque os existentes não
podem mudar (o TC-WB44-004 exige os mesmos destinos).

| nome | aba | célula | papel | sus_id | rótulo (coluna A) | valor na V4.3 |
|---|---|---|---|---|---|---|
| `ent_10_canto_b` | 10_TIRE | B20 | ent | | Canto | FL |
| `ent_10_canto_c` | 10_TIRE | C20 | ent | | Canto | FR |
| `ent_10_canto_d` | 10_TIRE | D20 | ent | | Canto | RL |
| `ent_10_canto_e` | 10_TIRE | E20 | ent | | Canto | RR |
| `ent_10_canto_f` | 10_TIRE | F20 | ent | | Canto | VERIF |
| `ent_10_lado_da_roda_l_esquerda_r_direita_b` | 10_TIRE | B21 | ent | SUS-501 | Lado da roda (L esquerda / R direita) | L |
| `ent_10_lado_da_roda_l_esquerda_r_direita_c` | 10_TIRE | C21 | ent | SUS-501 | idem | R |
| `ent_10_lado_da_roda_l_esquerda_r_direita_d` | 10_TIRE | D21 | ent | SUS-501 | idem | L |
| `ent_10_lado_da_roda_l_esquerda_r_direita_e` | 10_TIRE | E21 | ent | SUS-501 | idem | R |
| `ent_10_lado_da_roda_l_esquerda_r_direita_f` | 10_TIRE | F21 | ent | SUS-501 | idem | R |
| `ent_10_fz_de_09_loads_sus_104_verif_valor_fixo_f` | 10_TIRE | F22 | ent | SUS-104 | Fz (de 09_LOADS, SUS-104; VERIF: valor fixo) | 700 |
| `ent_10_angulo_de_deriva_alfa_iso_8855_velocidad_f` | 10_TIRE | F23 | ent | SUS-501 | Ângulo de deriva α (…) | 3 |
| `ent_10_camber_gama_projeto_topo_para_fora_f` | 10_TIRE | F24 | ent | SUS-404 | Camber γ (…) | 1.5 |
| `ent_10_slip_ratio_kappa_iso_1_travada_em_frenag_f` | 10_TIRE | F25 | ent | SUS-502 | Slip ratio κ (…) | 0.05 |
| `ent_10_epsilon_guarda_de_divisao_por_zero_em_bx` | 10_TIRE | B176 | ent | SUS-501 | ε (guarda de divisão por zero em Bx, By) | 1e-06 |
| `org_10_sistema_de_eixos_do_arquivo_declarado_sa` | 10_TIRE | I11 | org | | Sistema de eixos do arquivo (declarado): … | vazia |
| `org_10_lado_da_roda_l_esquerda_r_direita` | 10_TIRE | I21 | org | SUS-501 | Lado da roda (…) | vazia |
| `org_10_epsilon_guarda_de_divisao_por_zero_em_bx` | 10_TIRE | I176 | org | SUS-501 | ε (…) | texto da hipótese |
| `ent_13_referencia_python_fx_do_caso_verif_n_res` | 13_VALIDATION | B37 | ent | SUS-502 | Referência Python — Fx do caso VERIF [N] (…) | 1373.15… |
| `ent_13_referencia_python_fy_do_caso_verif_n_res` | 13_VALIDATION | B38 | ent | SUS-501 | Referência Python — Fy do caso VERIF [N] (…) | −1212.27… |
| `ent_13_referencia_python_mu_eff_do_caso_verif_r` | 13_VALIDATION | B39 | ent | SUS-503 | Referência Python — μ_eff do caso VERIF (…) | 2.6167… |
| `res_16_gradiente_de_subesterco_k_texto_de_exibi_e188` | 16_EQUILIBRIO | E188 | res | | Gradiente de subesterço K (texto de exibição, linear) | fórmula (pior origem) |
| `res_16_equilibrio_no_limite_texto_de_exibicao_e189` | 16_EQUILIBRIO | E189 | res | | Equilíbrio no limite (texto de exibição) | fórmula |
| `res_16_linha_de_apoio_saturacoes_a_y_limite_c_n_e190` | 16_EQUILIBRIO | E190 | res | | Linha de apoio: saturações, a_y limite, C_N, custo e Δt (…) | fórmula |

Os rótulos completos vêm da coluna A da V4.3 (o gerador lê a célula; a tabela acima abrevia com "…" e "idem"). As três da
16_EQUILIBRIO levam o sufixo porque o slug colide com o nome da coluna B da mesma linha (`res_16_gradiente_…_exibi` é a
B188). Elas são `res`, e não `org`, porque são fórmulas: um `org_` com fórmula seria lido como dado da equipe por
`dados_planilha.eh_dado` e confundiria a migração. Total de nomes da V4.4: 1266 + 23 = **1289**.

### A2. Limitação do K (pendência 13): célula e texto

- **Célula:** `16_EQUILIBRIO!F188`, a coluna de observação da linha que exibe o K (B188, lida pelo 14_DASHBOARD B41). É
  texto, não entra em conta nenhuma.
- **Texto da V4.3 (fica no começo):** `regimes diferentes (Milliken p. 313-315): o K vale no regime linear (a_y pequeno) e
  o veredito, no limite. Subesterço no linear com LOOSE no limite não é erro.`
- **Texto da V4.4 (a V4.3 + uma frase):** `regimes diferentes (Milliken p. 313-315): o K vale no regime linear (a_y
  pequeno) e o veredito, no limite. Subesterço no linear com LOOSE no limite não é erro. Limitação (EDR-066): o K não
  inclui o arrasto, a resistência ao rolamento nem o Fx exigido pelo balanço completo (hipóteses 10 e 9b da escada); num
  caso sintético, sem dado do carro, a diferença foi ΔK = +1,57 °/g. A confirmar com dados do T11.`
- O valor +1,57 °/g é o do EDR-065 item 3 e de `docs/inc6/escada-caso-sintetico.md`. Alternativa: pôr a frase no
  14_DASHBOARD (linha 43, que repete o texto de "regimes diferentes"). Ficou na 16 porque é ali que o K é calculado e
  exibido.

### A3. Lista de exceções (`gerar_v4_4.alteracoes()`; spec §3.4)

| # | Aba!célula | Antes (V4.3) | Depois (V4.4) | Motivo | EDR |
|---|---|---|---|---|---|
| X1 | 422 células das abas 03 a 14 | endereço | nome | regra da troca (§3.3). Das 422, 10 leem **só** células que ganham nome na V4.4 (10_TIRE B35:F35, F36, F37; 14_DASHBOARD E41, E42, E44); a aprovação dos 23 nomes (A1) cobre essas trocas, e o TC-WB44-002 as aceita pela regra, já que o nome existe na V4.4 | EDR-070 |
| X2 | 16_EQUILIBRIO!F188 | texto de A2 (V4.3) | texto de A2 (V4.4) | limitação do K (pendência 13) | EDR-066 |
| X3 | 14_DASHBOARD!B48 | fórmula da V4.3 | a mesma, com o trecho `diâmetros do regulamento FSAE 2026 D.10.1.1` trocado por `diâmetros da 24_CURVA B5 e B6` (o trecho aparece uma vez) | pendência 6: o texto valia só enquanto B5/B6 fossem os do regulamento; a fonte da própria 24_CURVA diz "FSAE Brasil a conferir no inc. 9" | EDR-066 |
| X4 | 00_README!A3 | `Versão do workbook: V4.3 (incremento 7: centro da curva, raio do skidpad e Fx por arrasto induzido; projeto T11) \| Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated` | `Versão do workbook: V4.4 (incremento 8: fórmulas das abas 03 a 14 por nome, valores iguais aos da V4.3; projeto T11) \| Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated` | versão | EDR-070 |
| X5 | 15_CHANGELOG!A24:C24 (vazia) | — | A24 `2026-11`; B24 `V4.4, fundação parte 2 (incremento 8): as fórmulas das abas 03 a 14 leem por nome toda célula única (23 nomes novos, data/nomes_V4_4.csv), com valores iguais aos da V4.3 (TC-WB44-005); aviso do R na 14_DASHBOARD B48 cita os diametros da 24_CURVA; limitacao do K na 16_EQUILIBRIO F188. Gerada da tag v4.3 por python/gerar_v4_4.py.`; C24 `EDR-070, EDR-066. Registro celula a celula: docs/registro-de-versoes-V4_4-celulas.md. NOT_VALIDATED fisicamente.` | changelog (mesmo estilo da linha 23, sem acentos onde a V4.3 não usou) | EDR-070 |

A guarda da 24_CURVA B28 (pendência 8), prevista como exceção na spec, **não muda célula**: o problema é do teste
(`tests/test_v4_3.py:205` põe a B28 numa lista fixa de exceções). Ela fica na 8a, Task 9. A `aba_curva.TEXTO_B48` também
não muda: ela gera a V4.3, cuja regeneração tem de continuar com 0 diferença. A troca de X3 mora só em `gerar_v4_4`.

### A4. N dos casos perturbados

- Medição de 2026-11-09 (`tools/medir_recalculo.py` sobre uma cópia da tag `v4.3`, Excel 16.0, 20 threads, 3 execuções):
  cenário A (arquivo gravado pelo openpyxl, sem cache, como as cópias de teste): abrir 8,51 s (inclui o cálculo de carga),
  CalculateFull 0,11 s, gravar 1,41 s, fechar 0,36 s, **total 10,39 s** (mediana). Cenário B (já salvo pelo Excel): 3,19 s.
  O openpyxl leva 1,0 s para abrir, 1,5 s para gravar e 1,0 s para abrir com `data_only`. Log em
  `build/medicao-recalculo-v4-3.md` (fora do Git; o Task 15 o transcreve no registro de versões).
- Custo por caso: duas cópias (V4.3 e V4.4) × (gravar 1,5 + Excel 10,4 + duas leituras 2,0) + comparação ≈ **30 s**.
- **N = 30** casos perturbados, semente `20261109`. Total previsto no Excel: (1 nominal + 30 + ~4 dirigidos) × 30 s ≈ 18
  min. O limite do item na suíte passa a 7200 s (`TIMEOUT_PLANILHAS`), porque o LibreOffice é mais lento e ainda não foi
  medido nesta planilha. O 1º TC-WB44-005 no Excel registra o tempo real por caso. Se passar de 60 s, a execução para e
  avisa, sem reduzir N por conta própria.

### A5. Tolerância da pendência 4 (`tests/test_equilibrio_linear.py` ~277-283)

A spec manda dividir o erro pela soma dos termos (o K comparado), e não pelo maior termo. O comentário do código registra que,
no caso FORMAS_V43 com ganho de teste, o erro relativo à soma dá 4,1e-3 (as parcelas se cancelam: soma = 3e-2 do maior
termo), acima do limite de 1e-3. Dividir pela soma e manter 1e-3 faria o teste falhar. Proposta: o critério desse caso passa
a ser o **erro absoluto ≤ 1e-5 °/g** (o medido é ~5e-6 °/g, margem de 2×), com o erro relativo à soma impresso no detalhe.
Isso é mais apertado que hoje: 1e-3 do maior termo equivale a ~3,3e-2 da soma. Os outros casos continuam com 1e-3 relativo
à soma. O Task 2 mede antes; se o absoluto medido passar de 1e-5, ele para e avisa.

### Decisões do controlador (informadas)

- **D1.** A spec (§11) prevê a cópia da V4.4 para `excel/` depois da mutação. O plano a faz logo depois do gerador (Task 13,
  commit próprio), para o TC-WB44-001 ter contra o que comparar. Se o gerador mudar depois, a cópia é refeita num commit
  próprio.
- **D2.** Conjunto perturbado (spec 4.3): os nomes `ent` das tabelas V4.0 a V4.3 cujo valor na V4.3 é número (não booleano),
  mais as células com validação de lista com papel `ent` ou `org` (opção sorteada da lista). Os 23 nomes novos ficam de
  fora, porque não existem na cópia da V4.3 e a perturbação é escrita por nome nas duas. As Origens (`org`, lista) entram
  porque são entradas de lista e mexem na pior origem e no prefixo DEMONSTRATIVO.
- **D3.** Casos dirigidos iniciais (spec 4.3, item 3): `DIR_ORIGENS_VAZIAS` (todo `org` com lista vazio), `DIR_CHAVES_INVERTIDAS`
  (toda entrada cujo nome tem `chave_h` vai de 0 para 1 e de 1 para 0), `DIR_NUMERICAS_VAZIAS` (toda entrada numérica `ent`
  vazia) e `DIR_ESQUERDA` (`ent_16_sentido_da_curva` = "Esquerda"). Esvaziar não inventa valor, e 0/1 e "Esquerda" são
  opções válidas. A cobertura (Task 16) diz se faltam outros.
- **D4.** A cobertura de ramos (TC-WB44-006) roda sobre as mesmas cópias recalculadas da V4.3 do TC-WB44-005, com a aba
  auxiliar `zz_COBERTURA` acrescentada só nessa cópia e fora da comparação. Assim não se paga um segundo recálculo.
- **D5.** A pendência 12 (auditoria humanizer-pt do LEIA-ME e o aviso dos campos dos `.docx`) passa ao fechamento (Task 20),
  porque o LEIA-ME é reescrito para a V4.4 ali; auditar agora o da V4.3 seria trabalho descartado.
- **D6.** O EDR-070 entra como IMPLEMENTED no Task 18 e passa a VERIFIED na suíte única (Task 19), junto com o EDR-064.

## Global Constraints

- IDs novos só: EDR-070 e TC-WB44-001 a TC-WB44-006. Nada de SUS-, REQ- ou outro TC-. Checks novos da 8a entram dentro dos
  TC existentes (as contagens esperadas da suíte não mudam na 8a).
- Nenhuma fórmula ou texto de célula muda fora da regra da troca (spec §3.3) e das exceções X2 a X5 aprovadas. Diferença
  que o TC-WB44-002 achar fora delas é FAIL, nunca uma exceção acrescentada depois.
- `export UV_SYSTEM_CERTS=1` antes de todo `uv`; nunca `python`/`python3` direto; um `uv run` por vez; arquivos em LF;
  encerrar o Excel só por PID (nunca por nome).
- A V4.4 sai de `python/gerar_v4_4.py`, da tag `v4.3`, em `build/`; nunca em `excel/`. A cópia para `excel/` é um commit
  próprio.
- A viva do Drive nunca é gravada, recalculada nem salva por ferramenta. A V4.3 de `excel/` e a de referência nunca são
  recalculadas nem salvas: só cópias em `build/` ou em pasta temporária. No LibreOffice, só cópias.
- Tolerância zero na equivalência por valor (números, textos, booleanos e erros idênticos); nunca afrouxar.
- Valores perturbados são **sintéticos de teste**, rotulados assim no log; nunca dado do carro.
- Docstrings e textos que citam nomes `_V2_x` ficam como estão (CLAUDE.md).
- Commits separados por propósito (cópia, higiene, engenharia, documentação). Cada commit termina com
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Durante a 8a e a 8b rodam só os testes afetados. A suíte inteira roda uma vez, no Task 19, no Excel e no LibreOffice.
- Push, PR, merge, tag e Drive só com a confirmação do usuário (Task 20).
- Subagentes: só o modelo Sonnet, inclusive nas revisões.

## Review Focus

1. **Aspas e nome de aba que começa por dígito.** `'05_VEHICLE'!$B$7` e `'16_EQUILIBRIO'!$E$188` precisam ser
   reconhecidos com as aspas, e nada fora do operando pode mudar (a gravação pelo LibreOffice já removeu essas aspas uma
   vez). Teste: `TC-WB44-002` em fórmula com aba citada e o caso unitário `trocar_formula` com aspas (Task 11).
2. **Texto entre aspas que parece referência.** `"h2v = 0 e h9v = 0 em 24_CURVA B9 e B10"` e `"B37"` dentro de uma string
   nunca são trocados. Teste: caso unitário no Task 11 e o alinhamento de tokens do TC-WB44-002.
3. **`$` misto (`B$22`, `$B22`).** O destino é o mesmo com ou sem `$`; a troca acontece nos dois. Teste: caso unitário no
   Task 11.
4. **Vazio, booleano e erro na comparação por valor.** O openpyxl lê `""` como `None`; `TRUE` ≠ `1`; `#N/A` é texto. A
   comparação usa `dados_planilha.iguais` (tipo e valor) e conta os erros por caso. Teste: caso unitário de `iguais_celula`
   no Task 15 e a contagem de erros no log.
5. **Perturbação que muda a natureza da entrada.** Inteiro continua inteiro, o sinal se mantém, zero continua zero, vazio
   continua vazio, lista só com opção válida. Teste: `TC-WB44-005`, pré-checagem pura de `perturbar()` (Task 15).

---

# Parte 8a — pendências 1 a 12 do inc. 7

### Task 1: laços MUTACAO e PLANILHAS do executor (pendência 3)

**Files:**
- Modify: `tools/rodar_testes.py` (laço de mutação ~399-421 e de planilhas ~530-555 do `main()`)
- Test: `tests/test_executor.py` (novos checks (i) e (j) dentro do TC-RUN-001, perto do (g) ~157-174)

**Interfaces:**
- Produces: `rodar_lista_mutacao(mutacoes, pulavel, pulados, resumo, md) -> None`;
  `argumentos_planilha(script: str) -> list[str]` (a expressão longa de hoje, sem mudança);
  `rodar_lista_planilhas(planilhas, pulavel, pulados, resumo, md) -> None`; `TIMEOUT_PLANILHAS: dict[str, int] = {}`
  (lido como `TIMEOUT_PLANILHAS.get(script, 1800)`). Mesmos efeitos em `resumo`, `md` e `pulados` que o código atual.

- [ ] **Step 1: escrever os checks (i) e (j)** com o padrão do (g) (scripts falsos numa pasta temporária):
  - (i) mutação: `ma.py` imprime `PRE-CHECAGEM OK: x` e `2 / 2` (código 0) → PASS com esperado 2; `mb.py` imprime
    `PRE-CHECAGEM OK: x` e `1 / 2` → FAIL; `mc.py` sem linha PRE-CHECAGEM e `2 / 2` → FAIL; `md.py` pulado (pulavel devolve
    `"abc1234"`) → PULADO. Assert: `[x[2] for x in resumo] == ["PASS", "FAIL", "FAIL", "PULADO"]` e `pulados == [(md_py, "abc1234")]`.
  - (j) planilha: `pa.py` imprime `MOTOR: excel` e `1 PASS, 0 FAIL, de 1 testes` → PASS; `pb.py` imprime
    `NÃO EXECUTÁVEL: sem motor` e sai com 3 → `NÃO EXECUTÁVEL`; `pc.py` pulado → PULADO. Assert da ordem dos status e de
    `"MOTOR: excel"` no `md`.
- [ ] **Step 2:** `uv run python -X utf8 tests/test_executor.py` → FAIL em (i)/(j) (`AttributeError`, função inexistente).
- [ ] **Step 3:** extrair os dois laços para as funções acima, sem mudar o texto que vai ao log, e chamar no `main()`.
- [ ] **Step 4:** `uv run python -X utf8 tests/test_executor.py` → `1 PASS, 0 FAIL, de 1 testes`.
- [ ] **Step 5: commit** `test(executor): laços de mutação e de planilhas em funções, com teste (TC-RUN-001 i, j)`.

### Task 2: critério do FORMAS_V43 em test_equilibrio_linear (pendência 4; A5)

**Files:** Modify: `tests/test_equilibrio_linear.py:274-285`.

- [ ] **Step 1: medir.** No bloco FORMAS_V43, imprimir para os dois ganhos: `erro_abs_graus_g = rel34 * abs(soma34)` convertido
  para °/g (`eq.para_graus_por_g` ou a conversão que `_comparar_034` já usa no `d34`) e `rel_soma = rel34`. Rodar
  `uv run python -X utf8 tests/test_equilibrio_linear.py`. Esperado: com ganho, `rel_soma ≈ 4,1e-3` e o absoluto ≈ 5e-6
  °/g. Se o absoluto passar de 1e-5 °/g: parar e avisar o usuário (A5 não vale).
- [ ] **Step 2:** remover a reescala pelo maior termo. Critério: sem ganho, `rel_soma < 1e-3` (como antes); com ganho,
  `erro_abs ≤ 1e-5 °/g`, com `rel_soma` e o absoluto no `d34`. Atualizar o comentário com os valores medidos no Step 1.
- [ ] **Step 3:** rodar o teste → `18 PASS, 0 FAIL, de 18 testes`.
- [ ] **Step 4: commit** `test(equilibrio_linear): FORMAS_V43 com ganho por erro absoluto (1e-5 °/g), não pelo maior termo`.

### Task 3: `--saida` do caso sintético e regeneração da escada (pendências 5 e 8, último item)

**Files:** Modify: `tools/relatorio_escada.py:394, 434-440`; regerar `docs/inc6/escada-hipoteses.md`.

- [ ] **Step 1:** `--saida` passa a `default=None`. Sem `--saida`: o padrão do modo (`SAIDA_PADRAO` ou `SAIDA_SINTETICO`).
  Com `--caso-sintetico` e `--saida` resolvendo para `SAIDA_PADRAO`: `RECUSADO: --caso-sintetico não grava em
  docs/inc6/escada-hipoteses.md (o relatório da planilha); use docs/inc6/escada-caso-sintetico.md ou outro caminho` em
  stderr e `sys.exit(2)`, antes de qualquer cálculo.
- [ ] **Step 2: conferir à mão** (não há TC para a ferramenta): `uv run python -X utf8 tools/relatorio_escada.py
  --caso-sintetico --raio 9.125 --saida docs/inc6/escada-hipoteses.md; echo $?` → `2` e a mensagem; e
  `git status --short docs/` vazio. Registrar a saída no corpo do commit.
- [ ] **Step 3: commit** `fix(relatorio_escada): --caso-sintetico recusa gravar no relatório da planilha (código 2)`.
- [ ] **Step 4: regerar** `docs/inc6/escada-hipoteses.md` com a mesma linha de comando registrada no cabeçalho do arquivo
  atual, mais `--sobrescrever` (só depois do commit do Step 3, para o cabeçalho não citar mudanças pendentes). Conferir
  com `git diff --stat`: a mudança esperada é a linha "Caso:" (agora com a massa), o commit citado e a data.
  Qualquer mudança de número é parada e aviso ao usuário.
- [ ] **Step 5: commit** `docs(inc6): escada-hipoteses.md regerado (linha "Caso:" com a massa; números iguais)`, com o
  aviso no corpo: "regerado depois da mudança da linha Caso: do inc. 7; só texto de cabeçalho mudou".

### Task 4: higiene sem mudança de comportamento (pendência 7)

**Files:** Modify: `tools/rodar_testes.py` (`modulos_locais`, a linha `nomes = …`), `python/gerar_v4_3.py:75-76`
(docstring de `aplicar`), `python/escada.py:35, 91, 100, 139`, `tests/test_neutro.py` ~219, `tests/test_workbook_v4_2.py` ~154.

- [ ] **Step 1:** quebrar a linha de `modulos_locais` em duas expressões; juntar a docstring de `aplicar` numa frase só
  (`"""Grava `alteracoes` em `wb` (cada "antes" tem de bater com a célula) e devolve o registro (cópia das alterações)."""`);
  quebrar as linhas com mais de 120 colunas nos outros arquivos. Nenhuma mudança de lógica nem de texto que vá para
  planilha ou relatório.
- [ ] **Step 2:** conferir: `awk 'length > 120 {print FILENAME":"FNR}' python/escada.py tests/test_neutro.py
  tests/test_workbook_v4_2.py` sem as linhas citadas; `uv run python -X utf8 tests/test_executor.py` → 1/1;
  `uv run python -X utf8 tests/test_neutro.py` → `2 PASS, 0 FAIL, de 2 testes`; `uv run python -X utf8 -c "import
  py_compile,sys; [py_compile.compile(f, doraise=True) for f in sys.argv[1:]]" python/gerar_v4_3.py python/escada.py
  tests/test_workbook_v4_2.py` sem erro. (O `test_escada`, ~6 min, e o `test_workbook_v4_2` rodam na suíte do Task 19.)
- [ ] **Step 3: commit** `style: quebra de linhas longas e docstring de gerar_v4_3.aplicar (sem mudança de comportamento)`.

### Task 5: minors da Task 4 do inc. 7 (formas v43)

**Files:** Modify: `tests/test_formas_v43.py` ~300-315; `python/equilibrio.py` (docstring de `fx_exigido_traseira`).

- [ ] **Step 1:** o check "v_r ⟂ (roda − C)" é tautológico (a velocidade é montada como ẑ × (P − C)). Trocar por um cálculo
  independente: `v_roda = v_CG + ω ẑ × (P − CG)`, com `v_CG` de módulo V na direção do corpo girada por β e ω = V/R, e
  conferir `|v_roda · (P − C)| ≤ 1e-9 · |v_roda| · |P − C|`. O check continua dentro do TC-ACK que já o contém.
- [ ] **Step 2:** a docstring de `fx_exigido_traseira` passa a citar a forma de δ que o código usa de fato (ler o corpo).
  Se o corpo usar a aproximação de 1ª ordem, a docstring diz isso; se usar a exata, a docstring a escreve.
- [ ] **Step 3:** `uv run python -X utf8 tests/test_formas_v43.py` → `4 PASS, 0 FAIL, de 4 testes`. Plantar uma vez um erro de
  sinal em ω no check novo (só localmente, sem commit) e ver o check falhar; desfazer.
- [ ] **Step 4: commit** `test(formas_v43): perpendicularidade de v_r por cálculo independente; docstring de δ`.

### Task 6: minors da Task 5 do inc. 7 (MMM e escada)

**Files:** Modify: `tests/test_mmm.py`, `python/mmm.py:376` (comentário), `tests/test_escada.py`.

- [ ] **Step 1:** em `test_mmm.py`, dentro do TC-MMM que exercita `trim`/`limite` com hipóteses, acrescentar a combinação
  mista `eixo_traseiro` + `cos_delta`, conferindo que o resultado com as duas difere do resultado com cada uma sozinha e é
  finito (ou N/A com motivo, se o caso não satura).
- [ ] **Step 2:** o comentário de `mmm.py:376` passa a descrever o que `alfa_rodas` recebe de fato (ler a função).
- [ ] **Step 3:** em `test_escada.py`, a linha "planilha V4.3" (hoje só a 1 g) passa a ser conferida também em 0,5 g e 1,5 g,
  com o mesmo critério do check de 1 g.
- [ ] **Step 4:** `uv run python -X utf8 tests/test_mmm.py` → `11 PASS, 0 FAIL, de 11 testes`;
  `uv run python -X utf8 tests/test_escada.py` (em segundo plano, ~6 min) → `3 PASS, 0 FAIL, de 3 testes`.
- [ ] **Step 5: commit** `test(mmm, escada): combinação mista eixo_traseiro + cos_delta e linha V4.3 a 0,5 e 1,5 g`.

### Task 7: minors da Task 6 do inc. 7 (estudo do NEUTRO)

**Files:** Modify: `python/estudo_neutro.py`, `tests/test_neutro.py` (~149 e o caso-base), `tests/test_escada.py` (caso-base),
`docs/inc6/estudo-neutro.md:266-267` (ou o caminho que o `grep -rn "sinal errado" docs/` der).

- [ ] **Step 1:** o caso-base existe em três cópias (`test_escada`, `test_neutro`, `estudo_neutro`). Deixar uma só, uma função
  pública em `python/estudo_neutro.py` (`caso_base() -> dict`, o mesmo conteúdo da cópia de lá), importada pelos dois
  testes. Conferir antes, com `diff`, que as três cópias são iguais. Se não forem, parar e avisar.
- [ ] **Step 2:** `test_neutro:149` `det =(` → `det = (`. Em `estudo-neutro.md:266-267`, a frase "sinal errado" passa para
  depois da ressalva da h/8 (só ordem, sem mudar afirmação). O d3 da varredura entra na tabela da varredura, como as outras
  colunas: se a tabela é gerada por ferramenta, regerar; se é escrita à mão, acrescentar a coluna com os valores que o
  `test_neutro` já calcula (imprimir e copiar, nunca estimar).
- [ ] **Step 3:** `uv run python -X utf8 tests/test_neutro.py` → 2/2; `uv run python -X utf8 tests/test_escada.py` → 3/3
  (segundo plano).
- [ ] **Step 4: commit** `refactor(neutro): caso-base numa função só; texto e tabela do estudo do NEUTRO`.

### Task 8: minors da Task 7 do inc. 7 (mutation_inc7 e bitola)

**Files:** Modify: `tests/mutation_inc7.py:48-49, 73`; teste do ramo da bitola provisória (o arquivo que testa a função com
esse ramo: `grep -rn "provis" python/skidpad.py python/equilibrio.py`).

- [ ] **Step 1:** `pegou(o)` passa a `o.returncode not in (0, CODIGO_TEMPO) and '[FAIL]' in o.stdout` (importar
  `CODIGO_TEMPO` de `executor_testes`). Um mutante que só estoura o tempo não é detectado e aparece no relatório como
  "tempo esgotado".
- [ ] **Step 2:** o rótulo `"alfas_de_arrasto: …"` passa a citar a função interna exata (`_alfa_na_grade`).
- [ ] **Step 3:** acrescentar ao TC existente que cobre a função um check do ramo da bitola provisória: com a bitola
  ausente, o resultado usa a provisória e o motivo/aviso a cita (conferir o texto exato no código).
- [ ] **Step 4:** rodar o teste do Step 3 (contagem igual à de hoje). Rodar `uv run python -X utf8 tests/mutation_inc7.py`
  em segundo plano → `5 / 5` e `PRE-CHECAGEM OK`.
- [ ] **Step 5: commit** `test(inc7): mutação não conta tempo esgotado como detectado; ramo da bitola provisória`.

### Task 9: minors da 7b em test_v4_3 (regex da 17 e guarda da B28)

**Files:** Modify: `tests/test_v4_3.py:200-212, 288-300`.

- [ ] **Step 1:** a comparação da grade da 17 hoje troca abreviações por regex. Ela passa a montar o texto esperado pelo
  dicionário de substituição do catálogo (`cel17`, `faixa`, `nm`), sem regex sobre o texto da planilha.
- [ ] **Step 2:** a exceção fixa `("24_CURVA", "B28")` vira uma regra: um leitor de `{R}` fora das guardas passa se tem
  `ISNUMBER({R})` **e** as chaves `ent_16_chave_h2_ackermann_sus_414` e `ent_24_chave_h2v_forma_do_ackermann` na mesma
  condição `AND`. As outras duas exceções da lista (16 B65 e `tvolta`) ficam como estão (são do catálogo C-B4/C-B7). A
  célula B28 não muda (A3).
- [ ] **Step 3:** `uv run python -X utf8 tests/test_v4_3.py` → `3 PASS, 0 FAIL, de 3 testes`; numa fórmula mutada só em
  memória (tirar o `h2v` da B28), o detector acusa.
- [ ] **Step 4: commit** `test(v4_3): grade da 17 sem regex e guarda da B28 por regra, não por lista`.

### Task 10: documentação da 8a (pendências 9, 10 e 11)

**Files:** Modify: `CLAUDE.md`, `docs/Engineering_Decision_Register.md` (linhas 36, 103 e 119),
`docs/superpowers/specs/2026-10-29-inc7-fisica-planilha-design.md` (§4.1).

- [ ] **Step 1:** CLAUDE.md, em Comandos, um parágrafo da V4.3 no padrão do da V4.2: `python/gerar_v4_3.py` gera a V4.3 da
  tag `v4.2` em `build/` (nunca em `excel/`); testes `tests/test_v4_3.py` (TC-WB43-001, 002, 006) e
  `tests/test_workbook_v4_3.py` (TC-WB43-003 a 005); "V4.3 regenerada da tag `v4.2` com 146373 fórmulas e 1266 nomes, 0
  diferença contra `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`"; `aba_curva.py`; a troca da viva pelo `conferir_viva` e pelo
  `migrar_viva`.
- [ ] **Step 2:** EDR-064 = APPROVED no índice (linha 103), na lista da §3 (linha 119, sem o "aguardam o usuário") e no
  CLAUDE.md (onde hoje diz "IMPLEMENTED (VERIFIED depois da suíte inteira)": passa a "APPROVED; VERIFIED depois da suíte
  única do inc. 8"). Atualizar a contagem da linha 36 (AWAITING_DECISION 6 → 5, APPROVED 29 → 30) e acrescentar ao
  histórico dela: "em 2026-11-09, EDR-064 passou de AWAITING_DECISION a APPROVED no índice, igual ao corpo (usuário)".
  Conferir a contagem contra a tabela.
- [ ] **Step 3:** spec do inc. 7, §4.1: onde está "≈ L·t_f/R_c² (1 %)", escrever a forma exata usada pela V4.3,
  θ = atan(L·t/(R_c² + L² − t²/4)), e dizer que a aproximação só vale com R ≳ 15 m (desvio de 1 %).
- [ ] **Step 4:** conferir com `git diff`; `uv run python -X utf8 tests/test_v4_2.py` → 4/4 (ele lê o EDR).
- [ ] **Step 5: commit** `docs: V4.3 em Comandos, EDR-064 APPROVED no índice e θ exato na §4.1 do inc. 7`.

---

# Parte 8b — V4.4: fórmulas das abas 03 a 14 por nome

### Task 11: medição e regra da troca (`python/reescrita_nomes.py`)

**Files:**
- Create: `python/reescrita_nomes.py`
- Test: `tests/test_v4_4.py` (só o esqueleto e uma pré-checagem pura, sem TC; os TC entram no Task 14)

**Interfaces:**
- Produces:
  - `ABAS_ALVO: tuple[str, ...]` = as abas cujo prefixo numérico está entre 03 e 14 (`03_TARGETS` … `14_DASHBOARD`, 12 abas).
  - `destinos_unicos(wb) -> dict[tuple[str, str], str]`: (aba, célula sem `$`) → nome, para todo nome definido cujo destino é
    uma célula única; `ValueError` se dois nomes apontam para a mesma célula (spec §3.3).
  - `@dataclass Medicao: formulas: int; operandos: int; ja_nome: int; trocaveis: int; linha_propria_03: int;
    intervalos: int; colunas: int; soltas: dict[tuple[str, str], list[str]]; volateis: dict[str, int]; ifs: int; iferrors: int`.
  - `medir(wb, destinos: dict) -> Medicao`.
  - `trocar_formula(formula: str, aba: str, destinos: dict) -> str`: a regra da §3.3.
  - `eh_linha_propria_03(aba: str, cel_formula: str, token: str) -> bool`: sem aba, mesma linha, célula da fórmula em H:Q da
    03_TARGETS.

- [ ] **Step 1: pré-checagem pura** em `tests/test_v4_4.py` (impressa, fora da contagem; falha → código 1):
  - `trocar_formula("='05_VEHICLE'!$B$7*2", "09_LOADS", {("05_VEHICLE","B7"): "ent_05_front_track_t_f"}) ==
    "=ent_05_front_track_t_f*2"`;
  - `B$22` e `$B22` na própria aba viram o nome; `'10_TIRE'!$B$168:$B$175` não muda; `'02_REQUIREMENTS'!A:A` não muda;
  - `'=IF(A1>0,"B37 e h2v = 0 em 24_CURVA B9",B37)'` na 13_VALIDATION, com `B37` nomeado: só o operando final muda;
  - uma fórmula sem nenhuma troca volta **idêntica** (o texto, byte a byte);
  - `destinos_unicos` com dois nomes na mesma célula → `ValueError`.
- [ ] **Step 2:** rodar → falha por import.
- [ ] **Step 3: implementar.** Tokenizar com `openpyxl.formula.Tokenizer`; trocar só `OPERAND`/`RANGE` que casam
  `raizes.REF` sem `c2`; a aba vem do token (sem aspas) ou é a da fórmula. Remontar com `"=" + "".join(t.value for t in
  items)` e, **antes de trocar**, conferir que a remontagem dos tokens originais é igual à fórmula original (senão,
  `ValueError` com a célula, para nunca alterar texto fora dos operandos). `medir` classifica cada operando nas categorias
  de `Medicao`, na ordem: já é nome → coluna inteira (`raizes.COLUNA`) → intervalo → trocável (destino em `destinos`) →
  linha própria da 03 → solta. Também conta FUNC OPEN de `IF`/`IFERROR` e dos voláteis (`NOW`, `TODAY`, `RAND`,
  `RANDBETWEEN`, `OFFSET`, `INDIRECT`, `CELL`, `INFO`).
- [ ] **Step 4:** rodar → pré-checagem OK. Rodar `medir` sobre a V4.3 da tag (script curto, saída no commit) e conferir a
  medição de 2026-11-09: `formulas 454, operandos 3274, ja_nome 412, trocaveis 2664, linha_propria_03 35, intervalos 36,
  colunas 4, soltas 23 células (123 referências), volateis {}, IF 462, IFERROR 350`. Diferença → parar e avisar.
- [ ] **Step 5: commit** `feat(v4.4): medição e regra da troca por nome (reescrita_nomes)`.

### Task 12: tabela dos 23 nomes (`data/nomes_V4_4.csv`, `python/nomes_v4_4.py`)

**Files:** Create: `python/nomes_v4_4.py`, `data/nomes_V4_4.csv`.

**Interfaces:**
- Consumes: `nomes_v4_0.Nome`, `slug`, `escrever_tabela`, `ler_tabela`; `reescrita_nomes.medir`.
- Produces: `CELULAS_V44: tuple[tuple[str, str], ...]` (as 23 da tabela A1, nessa ordem);
  `tabela_v44(wb43) -> list[Nome]` (aplica as regras de A1 lendo a V4.3); `NOMES_V44: list[Nome]` (a tabela aprovada,
  literal no módulo); `conferir_tabela(tabela) -> None` (`ValueError` se diferente de `NOMES_V44`, como em `gerar_v4_3`).

- [ ] **Step 1: pré-checagem** em `tests/test_v4_4.py`: `tabela_v44(V4.3 da tag) == NOMES_V44`; os 23 nomes não existem na
  V4.3; `set(CELULAS_V44) == set(medir(V4.3).soltas)`; `ler_tabela("data/nomes_V4_4.csv") == NOMES_V44`.
- [ ] **Step 2:** rodar → falha.
- [ ] **Step 3:** implementar; gerar o CSV com `escrever_tabela` (cabeçalho `nome,aba,celula,papel,sus_id,rotulo`, LF).
- [ ] **Step 4:** rodar → OK; `cat data/nomes_V4_4.csv | wc -l` → 24.
- [ ] **Step 5: commit** `feat(v4.4): tabela dos 23 nomes novos (data/nomes_V4_4.csv), aprovada pelo usuário`.

### Task 13: gerador da V4.4 e catálogo de células; cópia para excel/

**Files:**
- Create: `python/gerar_v4_4.py`, `docs/registro-de-versoes-V4_4-celulas.md` (gerado)
- Create (commit próprio): `excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx`

**Interfaces:**
- Consumes: `reescrita_nomes.destinos_unicos`, `trocar_formula`, `ABAS_ALVO`; `nomes_v4_4.NOMES_V44`, `conferir_tabela`.
- Produces:
  - `TAG_V43 = "v4.3"`; `CAMINHO_V43 = "excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx"`;
    `SAIDA_PADRAO = build/FSAE_EV_Suspension_Fase1_V4_4.xlsx`; `REGISTRO = "docs/registro-de-versoes-V4_4-celulas.md"`.
  - `extrair_v43(pasta) -> Path`; `_recusar(origem, saida)` (como na V4.3: `excel/` ou a própria origem → `SystemExit`).
  - `alteracoes() -> list[dict]` com as chaves `aba, cel, antes, novo, motivo, edr` (X2 a X5 de A3; X3 calcula `novo` como
    `antes.replace(TRECHO_B48_V43, TRECHO_B48_V44)` e exige uma ocorrência).
  - `montar_v44(wb) -> tuple[list[dict], list[dict]]`: acrescenta os 23 nomes (escopo da pasta); reescreve toda fórmula das
    `ABAS_ALVO` que não está em `alteracoes()`; aplica `alteracoes()` (cada `antes` tem de bater com a V4.3, senão
    `ValueError`); devolve (catálogo [{aba, cel, v43, v44}] das reescritas, registro das exceções).
  - `gerar(v43: Path | None, saida: Path, registro: Path | None = None, csv_nomes: Path | None = None) -> tuple[...]`.
  - `copia_v44(tmp: Path, alteracoes: dict | None = None, nome="V4_4_copia.xlsx") -> Path` e
    `copia_v43(tmp, alteracoes=None, nome="V4_3_copia.xlsx") -> Path` (a V4.3 da tag + valores por nome), helpers de teste
    no padrão de `gerar_v4_3.copia_v43`.

- [ ] **Step 1: pré-checagem** em `tests/test_v4_4.py`: `gerar` numa pasta temporária; 1289 nomes; 146373 fórmulas
  (`comparar_planilhas.celulas`); catálogo com **422** linhas e nenhuma célula de `alteracoes()` nele; `_recusar` com saída
  em `excel/` → `SystemExit` antes de abrir arquivo.
- [ ] **Step 2:** rodar → falha.
- [ ] **Step 3: implementar.** O catálogo é escrito com uma introdução fixa ("gerado por `python/gerar_v4_4.py` da tag
  `v4.3`; não edite à mão"), uma tabela `| Aba | Célula | V4.3 | V4.4 |` com as fórmulas em crase, e, no fim, a tabela das
  exceções X2 a X5 (`atualizar_planilha.escrever_registro`). LF. `fullCalcOnLoad = True`.
- [ ] **Step 4:** rodar → OK. `uv run python -X utf8 python/gerar_v4_4.py --registro docs/registro-de-versoes-V4_4-celulas.md`.
  Conferir por amostra (5 linhas do catálogo, uma por aba diferente) que a V4.4 é a V4.3 com operandos trocados.
- [ ] **Step 5: commit** `feat(v4.4): gerador da V4.4 (regra da troca e exceções X2 a X5) e catálogo de células`.
- [ ] **Step 6: cópia** `cp build/FSAE_EV_Suspension_Fase1_V4_4.xlsx excel/` e **commit próprio**
  `excel: V4.4 de referência gerada por python/gerar_v4_4.py (cópia de build/)`.

### Task 14: TC-WB44-001 a 004 (`tests/test_v4_4.py`)

**Files:** Modify: `tests/test_v4_4.py`, `python/viva.py` (`REFERENCIAS["V4.4"]`), `tools/comparar_planilhas.py`
(`FORMULAS_ESPERADAS_V44 = 146373   # = V4.3: a V4.4 só troca operandos`).

**Interfaces:**
- Consumes: `gerar_v4_4.gerar`, `copia_v43`, `alteracoes`; `comparar_planilhas.comparar_xlsx`; `tools/migrar_viva.migrar`.
- Produces: `viva.REFERENCIAS["V4.4"] = Referencia("V4.4", "v4.4", "excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx",
  _entradas_v43, origens.ORIGENS_V42, _cp.FORMULAS_ESPERADAS_V44, confere_edr=True)`. As entradas são as da V4.3: a V4.4 não
  cria entrada nem move nenhuma.

O teste **não** importa `reescrita_nomes`: o 002 e o 003 têm a própria leitura dos tokens, para não repetir um erro do
gerador.

- [ ] **Step 1: escrever os quatro checks** (`check(name, cond, detail)`, linha final `N PASS, 0 FAIL, de N testes`):
  - **TC-WB44-001:** `gerar(None, tmp)` bate com `excel/…V4_4.xlsx` por `comparar_xlsx(…, FORMULAS_ESPERADAS_V44,
    estrutura=True)`; 1289 nomes; `ler_tabela(data/nomes_V4_4.csv) == NOMES_V44`; `00_README!A3` começa com
    `Versão do workbook: V4.4`. Sem `excel/…V4_4.xlsx`: FAIL com a mensagem "falta a cópia (Task 13, Step 6)".
  - **TC-WB44-002:** para cada célula de cada aba da V4.3 da tag e da V4.4 de `excel/`: nas `ABAS_ALVO`, as fórmulas têm o mesmo
    número de tokens e cada par é igual ou (V4.3 = referência a uma célula, V4.4 = nome cujo destino na V4.4 é essa
    célula). Fora das `ABAS_ALVO`, o valor da célula é idêntico. As células de `alteracoes()` têm na V4.4 exatamente o
    `novo` e na V4.3 o `antes`. O detalhe conta as trocas (esperado 2787 = 2664 + 123) e lista as diferenças fora da
    regra (esperado: nenhuma).
  - **TC-WB44-003:** nas `ABAS_ALVO` da V4.4, todo operando de célula única que não é nome está na linha própria da 03
    (definição da spec §3.5). Detalhe: linha própria 35, intervalos 36, colunas 4, células soltas 0.
  - **TC-WB44-004:** todo nome da V4.3 existe na V4.4 com o mesmo destino (`attr_text` igual); os 23 novos não existem na
    V4.3. `migrar_viva.migrar` de uma `copia_v43` com valores **sintéticos de teste** (o mesmo conjunto do TC-WB43-006, que
    escreve um valor em cada tipo de nome de dado) para a V4.4 de `excel/` → código 0, 0 conflitos, todos os dados escritos.
- [ ] **Step 2:** rodar `uv run python -X utf8 tests/test_v4_4.py` → os quatro passam (a cópia do Task 13 existe). Se algum
  falhar: corrigir o gerador e refazer a cópia (D1), nunca afrouxar o teste.
- [ ] **Step 3: prova de que reprovam** (local, sem commit): numa cópia da V4.4, trocar um nome por outro de mesmo papel
  numa fórmula → o 002 falha; trocar um nome pelo endereço → o 003 falha; tirar um nome da tabela → o 001 e o 004 falham.
- [ ] **Step 4:** `uv run python -X utf8 tests/test_v4_3.py` → 3/3 (o `viva` mudou).
- [ ] **Step 5: commit** `test(v4.4): TC-WB44-001 a 004 (regeneração, regra, invariante e migração); V4.4 em viva.REFERENCIAS`.

### Task 15: equivalência por valor (TC-WB44-005)

**Files:** Create: `tests/test_workbook_v4_4.py`.

**Interfaces:**
- Consumes: `gerar_v4_4.copia_v43`, `copia_v44`; `tests/recalculo_planilha.py` (`escolher`, `_excel_recalc`, `_libreoffice`);
  `dados_planilha.iguais`.
- Produces (para o Task 16 e a mutação):
  - `SEMENTE = 20261109`; `N_PERTURBADOS = 30`; `FAIXA = 0.20`.
  - `entradas_perturbaveis(wb43) -> tuple[list[str], dict[str, list]]`: (nomes numéricos `ent` das tabelas V4.0 a V4.3, nome →
    opções da lista para `ent`/`org` com validação de lista). Validação cuja fonte não é nome definido, intervalo ou
    lista literal → `ValueError`.
  - `perturbar(valores: dict, numericos, listas, rng) -> dict`: v·(1 + U(−FAIXA, FAIXA)); `int` → `round`; 0 → 0; `None` →
    fica `None`; lista → `rng.choice(opções)`.
  - `casos() -> list[tuple[str, dict]]`: `NOMINAL` (sem alteração), `P01` a `P30` (`random.Random(SEMENTE + i)`) e os
    dirigidos de D3. `DDS_CASOS44` (lista separada por vírgula) restringe os casos; vazio = todos.
  - `valores_recalculados(caminho: Path) -> dict[tuple[str, str], object]` (data_only, todas as abas, sem a `zz_COBERTURA`).
  - `iguais_celula(a, b) -> bool` (`dados_planilha.iguais`, com `None` == `None`).
  - `EXCLUIDAS_VALOR`: as células de X2 a X5 com valor diferente de propósito (16 F188, 14 B48, 00 A3, 15 A24:C24) mais o
    fecho de dependentes delas pelo grafo de `raizes.referencias` (esperado: vazio; o teste confere o fecho).
  - Variável `DDS_V44`: caminho de uma V4.4 alternativa (a da mutação) no lugar da `excel/…V4_4.xlsx`.

- [ ] **Step 1: pré-checagem pura** (antes de abrir o motor; falha → código 2): `perturbar` mantém tipo `int`, sinal, zero e
  `None`; opção de lista sempre na lista; a mesma semente dá o mesmo caso; `iguais_celula(True, 1) is False`,
  `iguais_celula("#N/A", "#N/A") is True`; nenhuma função volátil na V4.3 nem na V4.4 (contagem 0, senão FAIL).
- [ ] **Step 2: implementar o TC-WB44-005.** Para cada caso: `copia_v43(tmp, caso)` e uma cópia da V4.4 (de `DDS_V44` ou de
  `excel/`) com os mesmos valores por nome; recalcular as duas no mesmo motor; comparar todas as células de todas as abas
  menos `EXCLUIDAS_VALOR`. Passa com 0 diferença em todos os casos. O log diz, por caso: motor, tempo, nº de células
  comparadas, nº de células com erro (`#…`) em cada versão, e o rótulo "valores sintéticos de teste (não são dados do
  carro)". Um caso em que mais de 50 % das fórmulas dão erro aparece como **aviso** no log (spec §10), sem afrouxar nada.
  Sem motor: `NÃO EXECUTÁVEL` e código 3.
- [ ] **Step 3:** rodar no Excel em segundo plano: `DDS_RECALC=excel uv run python -X utf8 tests/test_workbook_v4_4.py` →
  `TC-WB44-005` PASS. Registrar o tempo por caso (A4: se passar de 60 s, parar e avisar).
- [ ] **Step 4: commit** `test(v4.4): TC-WB44-005, equivalência por valor V4.3 x V4.4 (tolerância zero, N = 30)`.

### Task 16: cobertura de ramos (TC-WB44-006) e casos dirigidos

**Files:** Modify: `tests/test_workbook_v4_4.py`.

**Interfaces:**
- Produces: `ramos(formula: str, aba: str) -> list[Ramo]` com `@dataclass Ramo: aba: str; cel: str; tipo: str  # "IF" ou
  "IFERROR"; indice: int; condicao: str; caminho: tuple[str, ...]; matriz: bool`; `aba_cobertura(wb43) ->
  dict[str, tuple[Ramo, str, str]]` (célula da `zz_COBERTURA` → ramo e os dois lados); `NAO_COBERTOS: dict[tuple[str, str,
  int, str], str]` (ramo, lado → motivo; aprovado pelo usuário, Step 4).

- [ ] **Step 1: implementar `ramos`** sobre a árvore de tokens (FUNC OPEN/CLOSE e SEP ARG). Para `IF(c, a, b)`: o lado
  verdadeiro é `AND(caminho…, c)` e o falso é `AND(caminho…, NOT(c))`. Para `IFERROR(x, y)`: o lado do erro é
  `AND(caminho…, ISERROR(x))` e o outro é `AND(caminho…, NOT(ISERROR(x)))`. O caminho acumula a condição do `IF` externo
  (ou o `NOT`) ao descer para `a` ou `b`, e o `ISERROR(x)` ao descer para `y`. No `x` do `IFERROR`, o caminho fica como está.
  Operandos sem aba ganham a aba de origem (`'<aba>'!`), porque as condições vão para outra aba. Ramo dentro de
  `SUMPRODUCT`, `MMULT` ou de argumento de matriz recebe `matriz=True` e não vai à aba auxiliar (vai ao log com o motivo
  "condição avaliada em matriz; não medível por célula").
- [ ] **Step 2:** a `zz_COBERTURA` entra só na cópia da V4.3 de cada caso do TC-WB44-005, com uma célula por lado:
  `=IFERROR(AND(...),"ERRO")`. Depois do recálculo, um lado está coberto se deu `TRUE` em algum caso. TC-WB44-006 passa
  quando todo lado (fora os `matriz=True`) está coberto ou em `NAO_COBERTOS`. Pré-checagem: as contagens de `ramos` sobre a
  V4.3 batem com a medição (462 `IF` e 350 `IFERROR` nas `ABAS_ALVO`).
- [ ] **Step 3:** rodar com `NAO_COBERTOS = {}` e gravar a lista dos descobertos em `build/cobertura-v44.md`. Para cada
  descoberto, primeiro um caso dirigido que o cubra com valores válidos (esvaziar, opção de lista, chave 0/1, sinal de uma
  entrada). Sem valor válido que o alcance, ele vai à proposta da lista, com o motivo.
- [ ] **Step 4: ponto de aprovação.** Levar ao usuário a lista proposta (ramo, lado, motivo) e os `matriz=True`; a execução
  **para** aqui até a resposta. Gravar a lista aprovada em `NAO_COBERTOS` com a data e "aprovado pelo usuário".
- [ ] **Step 5:** rodar tudo (Excel, segundo plano) → `2 PASS, 0 FAIL, de 2 testes`.
- [ ] **Step 6: commit** `test(v4.4): TC-WB44-006, cobertura de ramos com casos dirigidos e lista aprovada de não cobertos`.

### Task 17: mutação (`tests/mutation_planilha_v44.py`)

**Files:** Create: `tests/mutation_planilha_v44.py` (padrão de `tests/mutation_planilha_v43.py`: pré-checagem do original,
orçamento `DDS_ORCAMENTO_S`, `executor_testes.executar`, códigos 0/1/2/3, linha final `D / T`).

Cada mutante altera **uma** fórmula numa cópia da `excel/…V4_4.xlsx` (openpyxl), passada ao teste por `DDS_V44`, com
`DDS_CASOS44=NOMINAL,P01,P02,P03`. Detectado = código ≠ 0 com `[FAIL] TC-WB44-005`. Mutantes (texto da V4.4 depois da troca):

1. 09_LOADS!B4: `ent_05_wheelbase_l` → `ent_05_front_track_t_f` (nome por outro de mesmo papel);
2. 09_LOADS!B5: `ent_05_wheelbase_l` → `'05_VEHICLE'!$B$7` (nome pelo endereço da vizinha);
3. 09_LOADS!B21: `<=0` → `>=0` (operador no ramo de instabilidade de rolagem, pouco usado);
4. 09_LOADS!B4: `9.81` → `9.8` (constante).

Cada mutante confere antes que o trecho existe uma vez na fórmula (senão, código 2: a lista está desatualizada).

- [ ] **Step 1:** escrever o script; `uv run python -X utf8 tests/mutation_planilha_v44.py` (segundo plano) →
  `PRE-CHECAGEM OK` e `4 / 4`.
- [ ] **Step 2: commit** `test(v4.4): mutação da equivalência por valor (4 mutantes, 4/4)`.

### Task 18: executor, registro de versões, EDR-070, EDR-066 e CLAUDE.md

**Files:** Modify: `tools/rodar_testes.py`, `docs/Engineering_Decision_Register.md`, `CLAUDE.md`. Create:
`docs/registro-de-versoes-V4_4.md`.

- [ ] **Step 1: executor.** `TESTES += ("V4.4 (regeneração, regra, invariante e migração)", "tests/test_v4_4.py", 4, "plano do
  inc. 8 (TC-WB44-001 a 004)")`; `PLANILHAS += ("tests/test_workbook_v4_4.py", 2, "V4.4 (TC-WB44-005 e 006); plano do inc.
  8")` com argumentos `[]` em `argumentos_planilha`; `TIMEOUT_PLANILHAS["tests/test_workbook_v4_4.py"] = 7200`;
  `MUTACAO += ("tests/mutation_planilha_v44.py", 4)` com `TIMEOUT_MUTACAO[...] = 7200`; `MODULOS += ["reescrita_nomes",
  "nomes_v4_4", "gerar_v4_4"]`; bloco CA-07 "planilha vs V4.4 de referência (fórmulas por nome)" no padrão do da V4.3
  (`gerar_v4_4.py --saida <tmp>`, `comparar_xlsx(…, FORMULAS_ESPERADAS_V44, estrutura=True)`); `DEPENDENCIAS` de
  `tests/test_v4_4.py` (`data/nomes_V4_4.csv`, `_X + "V4_4.xlsx"`, `_X + "V4_3.xlsx"`,
  `"docs/registro-de-versoes-V4_4-celulas.md"`), de `tests/test_workbook_v4_4.py` (`python/gerar_v4_4.py`, `_X + "V4_4.xlsx"`,
  `_X + "V4_3.xlsx"`, `data/nomes_V4_4.csv`) e de `tests/mutation_planilha_v44.py` (`tests/test_workbook_v4_4.py`,
  `_X + "V4_4.xlsx"`). `uv run python -X utf8 tests/test_executor.py` → 1/1.
- [ ] **Step 2: registro de versões** `docs/registro-de-versoes-V4_4.md` no padrão do da V4.3: o que muda (regra, 23 nomes,
  exceções X2 a X5), a medição (A1 e Task 11), a medição do recálculo e o N (A4), a linha da limitação do K, os testes e o
  aviso de que a V4.5 volta ao CA-07 por texto contra a V4.4 (spec §4.1).
- [ ] **Step 3: EDR.** EDR-070 "Fundação parte 2: V4.4 com as fórmulas das abas 03 a 14 por nome" (conteúdo da spec §8 e
  das alternativas registradas, mais o achado de A1), status IMPLEMENTED (D6). No EDR-066, novo item nas limitações: o K
  da planilha não representa as hipóteses 10 e 9b (ΔK = +1,57 °/g no caso sintético; a confirmar com o T11; declarado na
  16_EQUILIBRIO F188 da V4.4). Índice, contagem da linha 36 (total 70) e a versão do registro (linha 3).
- [ ] **Step 4: CLAUDE.md.** Situação atual: incremento 8 e V4.4; Comandos: parágrafo da V4.4 (gerador, testes, "V4.4
  regenerada da tag `v4.3` com 146373 fórmulas e 1289 nomes, 0 diferença"), as contagens esperadas novas (`test_v4_4` 4,
  `test_workbook_v4_4` 2, mutação 4/4).
- [ ] **Step 5:** `uv run python -X utf8 tests/test_v4_2.py` → 4/4 e `tests/test_v4_4.py` → 4/4 (leem o EDR e o registro).
- [ ] **Step 6: commits** separados: `tools(rodar_testes): itens da V4.4` e `docs: registro da V4.4, EDR-070, item do K no
  EDR-066 e CLAUDE.md`.

### Task 19: suíte única do incremento (spec §7)

- [ ] **Step 1:** árvore sem mudanças pendentes (`git status --short` vazio). Em segundo plano, sem `--pular-recentes`:
  `DDS_RECALC=excel uv run python -X utf8 tools/rodar_testes.py --saida docs/migracao/<próximo>-inc8-excel.md --titulo
  "Incremento 8 (V4.4), suíte única no Excel"`. Esperado: todos os itens PASS, nenhum PULADO, incluindo "planilha vs V4.3 de
  referência" e "planilha vs V4.4 de referência". O nome do arquivo segue a numeração de `docs/migracao/`.
- [ ] **Step 2:** a mesma suíte com `DDS_RECALC=libreoffice` e `--saida docs/migracao/<próximo>-inc8-libreoffice.md`
  (pendência 1). Item que falhar só no LibreOffice: investigar a causa (systematic-debugging) e relatar; nunca afrouxar.
- [ ] **Step 3:** com as duas PASS: EDR-064 e EDR-070 → VERIFIED (índice, corpo, contagem e CLAUDE.md), citando os dois logs.
- [ ] **Step 4: commits** `docs(migracao): suíte única do inc. 8 no Excel e no LibreOffice` (os logs) e
  `docs: EDR-064 e EDR-070 VERIFIED (suíte única do inc. 8)`.

### Task 20: fechamento (cada passo com a confirmação do usuário)

- [ ] **Step 1: viva.** `uv run python -X utf8 tools/conferir_viva.py` (esperado 0). Com dados: `tools/migrar_viva.py VIVA
  --para excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx` (conflito listado, nunca sobrescrito); sem dados, vai a referência
  pura. Preparar `build/drive-v4.4/` com um `PLANO-DE-TROCA.md` no padrão do da V4.3. Gravar no Drive só depois de o
  usuário confirmar.
- [ ] **Step 2: LEIA-ME e `.docx` (pendência 12).** LEIA-ME da V4.4 (o da V4.3, de `build/drive-v4.3/md/leia-me.md` no
  worktree da 7b, mais "O que mudou na V4.4"); passar pelo `humanizer-pt` e rodar
  `auditoria_pos_edicao.py ANTES.md DEPOIS.md` (script da skill) com o resultado no plano de troca. `.docx` por `quarto
  pandoc` com o `--reference-doc` de antes, com o aviso, no plano de troca e no LEIA-ME, de abrir no Word e atualizar os
  campos para o sumário aparecer.
- [ ] **Step 3:** PR (`fluxo-github`, `pr-review-toolkit` com Sonnet), merge e tag `v4.4`, cada um só com o "sim" do usuário.
  Depois do merge: CLAUDE.md e a memória do projeto com a viva na V4.4.

---

## Ordem e dependências

As Tasks 1 a 10 são independentes entre si, menos a 4 (toca `tools/rodar_testes.py`, como a 1: rodar depois dela) e a 7
(toca `tests/test_escada.py`, como a 6: rodar depois dela). As Tasks 11 a 19 são em série. A 16 tem um ponto de aprovação
do usuário (Step 4), e a 20 tem um em cada passo.
