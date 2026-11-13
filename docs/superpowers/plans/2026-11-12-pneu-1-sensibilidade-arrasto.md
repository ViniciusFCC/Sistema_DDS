# pneu-1: sensibilidade do pneu e arrasto induzido — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** um caso em JSON editável e uma API em Python que medem quanto λ (LMUY, LFZO, LKY), pressão e KT mexem em
a_y_lim, veredito, Cα e K, calculam o arrasto induzido por condição de curva e dizem, degrau a degrau do roteiro, se
alguma decisão muda.

**Architecture:** `python/caso_pneu1.py` cuida do caso: catálogo de campos, leitura, edição, gravação e a montagem do
`CasoEquilibrio` pela mesma rotina que lê a planilha (`caso_planilha._caso_de_valores`). `python/sensibilidade_pneu.py`
orquestra o que já existe (`comparar_carro`, `varredura_pneu`, `escolher_pressao`, `metricas_pneu`,
`angulos_necessarios`), mais duas funções novas: forças por roda e arrasto. Cada estudo devolve um `Resultado` com
`para_dict()`. `tools/` só tem cascas (captura única e gerador de relatório). Nada abre a planilha no caminho de
execução.

**Tech Stack:** Python 3.13 (uv), openpyxl só na captura, testes como scripts com `check()`.

**Spec:** `docs/superpowers/specs/2026-11-12-pneu-1-sensibilidade-arrasto-design.md` (APROVADA em 2026-11-12). O
executor lê os dois.

## Global Constraints

- Não alterar `python/equilibrio.py`, `python/escada.py`, `python/equilibrio_linear.py`,
  `python/comparacao_pressao.py`, `python/tire_pressure.py` nem nenhuma planilha. Eles só são importados.
- IDs autorizados: **EDR-075** e **TC-SEN-001** em diante. Nenhum outro ID novo.
- Nenhum coeficiente, faixa, limite ou referência inventado. Valor sem fonte vale `null` com a origem `? A confirmar`.
- Amplitudes de λ: só as de `data/varredura_pneu_exploratoria.json` (0,8 / 1,0 / 1,2, EDR-055). Pressões: as 4 da
  família (8, 10, 12, 14 psi). Grade: `ay_max_g=2.0`, `passo_g=0.05`, `n_alfa=25`. O `fator_neutro` vem do JSON
  (24_CURVA B34 = 4/3 na V4.4; spec §5.1). Ele difere do 1,0 do `relatorio_pressao`, e o relatório diz isso.
- `.tir` da família: `DDS_TTC_DIR` ou `references/ttc/round6_hoosier_r25b_20p5x7_13_7in` (no checkout ou no
  repositório principal), com a mesma regra de `tests/test_tire_pressure.py::achar_diretorio_ttc`. Sem eles, a
  ferramenta e os testes que precisam deles saem NÃO EXECUTÁVEL com código 3.
- Rótulos da spec §9 em toda saída (constante `ROTULOS` da Task 5), mais o rótulo próprio de cada valor.
- Origens: as da lista Origens da planilha; `--set` grava `✎ Editado pelo usuário`; "Dado do T11" só se o usuário
  escrever.
- Comandos (Git Bash): `export UV_SYSTEM_CERTS=1` antes de `uv run`; testes com
  `DDS_TTC_DIR="C:/Users/vferr/Documents/Sistema_DDS/references/ttc/round6_hoosier_r25b_20p5x7_13_7in" uv run python -X utf8 tests/<script>.py`.
  "Passou" é a linha final `N PASS, 0 FAIL, de N testes`. Nunca rodar a suíte inteira.
- Commits separados por propósito. O JSON capturado vai num commit `dados:` só dele. Nada em `importado-claude-ai/`,
  nenhum `.tir` nem PDF versionado.
- Textos em português do Brasil. Mensagens de erro em linguagem que um leigo entende (spec §5.5).

## Decisões do plano (tomadas a partir do código; o usuário pode mudar)

- **D1. Montagem do caso:** `caso_de_dados` monta o dicionário `x` que `caso_planilha._caso_de_valores(x, tir, passo1,
  aba_equilibrio.VERIFICACOES_V43, fonte)` espera e chama essa rotina. O `tir` é
  `familia.at_pressure(12.0).source_path`. Assim, as verificações, as mensagens e a montagem são as mesmas da
  planilha, e o JSON só precisa reproduzir os `res_`. A chamada à função privada fica isolada em `caso_de_dados`, com
  comentário.
- **D2. `res_` recalculados** (regra da célula da V4.4):

  | Resultado | Regra |
  |---|---|
  | `m` | `m_sem_piloto_kg + m_piloto_kg` (05_VEHICLE B4) |
  | `a` | `L_m·(1 − f_dianteira)` (05 B9) |
  | `b` | `L_m·f_dianteira` (05 B10) |
  | `huF` | `d_pneu_F_pol·0,0254/2·razao_hns_F` (05 B16) |
  | `huR` | o análogo de `huF` com os campos traseiros (05 B17) |

  `R_m` é entrada primária. Na captura, ele vem da regra da 24_CURVA B20 com B13/B18; em "Linha central", é
  `(dint+dext)/4`. `fator_neutro` é entrada (B34 é a fórmula constante `=4/3`; a captura aceita só esse caso de
  fórmula, avaliando o literal). `ackermann_pct` (07 B75, `res_`) é entrada primária com valor `null` e origem
  `? A confirmar`: não se reimplementa a 07, e com h2 = 1 ele precisa ser informado (a verificação da planilha já
  acusa).
- **D3. Sinal do arrasto:** D_i = −F_y,i·sen α_i (ISO do projeto: α > 0 = velocidade para a esquerda,
  `tire_model.wheel_forces`). É a projeção do Milliken p. 64. No caso normal, em que F_y e α têm sinais opostos em
  ISO, coincide com F_y·sen|α| da spec §7.2; com empuxo de camber ou toe, mantém o sinal certo. Com toe ≠ 0, D(0) > 0
  (arrasto do toe), e isso é físico, não erro.
- **D4. Grade do arrasto:** de 0 até `ay_lim` do caso (variante a, 12 psi) em passos de 0,1 g. Sem `ay_lim` (N/A),
  vai até `ay_max_g` e para no último a_y em que `angulos_necessarios` resolve, com o rótulo "sem saturação até X g:
  grade até o último a_y resolvido".
- **D5. C_f e C_r:** `equilibrio_linear._rigidez_eixo(caso, eixo, cargas(caso,0), camber(caso,0), α0_eixo,
  formas=…)`, com α0 de `angulos_necessarios(caso, 0.0, formas=…)`. É a mesma rigidez que o K usa. Fica isolado numa
  função, com comentário (spec §10).
- **D6. Estado de cada decisão:** `"sim"` se algum critério dá sim; `"não"` se todos foram avaliados e dão não;
  `"não avaliado"` se nenhum dá sim e algum ficou sem avaliação; `"não medido aqui"` para os degraus da spec §6.1
  fora do estudo. Os degraus 7 e 15 (arrasto × rolamento) ficam `"não avaliado"`: não há Crr com fonte nem regra de
  decisão para energia, e o D sai como tamanho de efeito.
- **D7. "Distingue" no `decidir`:** a pressão muda decisão pelo critério 2 se, num `Veredito` de `escolher_pressao`,
  o conjunto `indistinguiveis` tem menos pressões que as decidíveis (alguma pressão ficou de fora). Sem pressão
  decidível, o critério fica "não avaliado".
- **D8. Divisão de arquivos:** a spec §8 previa um módulo só. O caso vai para `python/caso_pneu1.py` (o catálogo é
  usado pela captura e pelo modelo), e `sensibilidade_pneu.py` reexporta `ler_caso`, `editar`, `salvar_caso`,
  `familia_ttc` e `caso_de_dados`, para que a API da spec §5.3 continue num lugar só.

## Review Focus

1. **O caso não satura até 2 g** (`ay_lim` None em todas as pressões). A grade do arrasto segue a D4; a regra dá
   "não avaliado", nunca "não"; o relatório diz por quê. → testes TC-SEN-012 e TC-SEN-016.
2. **Uma edição deixa o caso inválido** (`f_dianteira = 1.5`; h9 = 1 com `crr` null; `sentido` = "esquerda", em
   minúsculas). O erro tem a mensagem da planilha, sem traceback na linha de comando. → TC-SEN-004, TC-SEN-008 e TC-SEN-020.
3. **Toe ≠ 0 ou camber estático ≠ 0:** D(0) > 0 e nenhum D_i < 0 numa curva normal. → TC-SEN-011.
4. **`salvar_caso` por cima do demonstrativo**, inclusive com outro caminho para o mesmo arquivo (relativo, ou com
   maiúsculas diferentes no Windows): recusado. → TC-SEN-003.
5. **`sentido` = "Direita":** o caso vira `espelhar` do caso "Esquerda", e o arrasto não chama
   `angulos_necessarios` com a_y < 0. → TC-SEN-006.

---

### Task 1: catálogo, leitura, edição e gravação do caso (sem `.tir`)

Modelo sugerido: Sonnet.

**Files:**
- Create: `python/caso_pneu1.py`
- Create: `tests/test_sensibilidade_pneu.py` (esqueleto com `check`, `encerrar` e as seções sem `.tir`)

**Interfaces:**
- Produces:
  - `CAMPOS: dict[str, Campo]`, com `Campo(chave_x: str | None, nome_definido: str | None, unidade: str,
    rotulo: str, descricao: str, tipo: Literal["num","chave","texto"])`. A chave do dicionário é a chave do JSON.
  - `CAMINHO_DEMONSTRATIVO: Path` (`data/casos/caso_pneu1_demonstrativo.json`);
  - `ORIGEM_EDITADO = "✎ Editado pelo usuário"` e `ORIGEM_A_CONFIRMAR = "? A confirmar"`;
  - `ler_caso(caminho: str | Path) -> dict`;
  - `editar(dados: dict, **chaves) -> dict`;
  - `aplicar_set(dados: dict, pares: list[str]) -> dict`, que lê `"chave=valor"` e chama `editar`;
  - `salvar_caso(dados: dict, caminho: str | Path) -> Path`;
  - `x_de_dados(dados: dict) -> dict` (o `x` da D1, com os `res_` da D2);
  - `ValorUsado(chave, valor, unidade, origem, editado: bool, calculado_por: str | None)`;
  - `valores_usados(dados: dict) -> tuple[ValorUsado, ...]` (entradas e `res_` recalculados).

**Formato do JSON** (o mesmo na captura, na Task 2):

```json
{"schema": "caso_pneu1/1",
 "aviso": "DEMONSTRATIVO: caso de outro carro (T09/E03 e TX), não o T11",
 "captura": {"planilha": "excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx", "sha256": "…", "data": "2026-11-12",
             "ferramenta": "tools/capturar_caso_pneu1.py"},
 "campos": {"L_m": {"valor": 1.55, "unidade": "m", "origem": "◐ Dado de outro carro (TX, T09)",
                    "fonte": "ent_05_wheelbase_l (05_VEHICLE B?)", "rotulo": "Entre-eixos",
                    "unidade_exibicao": "mm", "descricao": "…", "editado": false}}}
```

O conjunto de campos e as chaves de `x`:
- **05:** `m_sem_piloto_kg`, `m_piloto_kg`, `h_cg_m`, `L_m`, `tF_m`, `tR_m`, `f_dianteira`, `muF_kg`, `muR_kg`,
  `d_pneu_F_pol`, `d_pneu_R_pol`, `razao_hns_F`, `razao_hns_R`;
- **06:** `KsF_N_m`, `KsR_N_m`, `MRF`, `MRR`, `KarbF_*`, `KarbR_*`, `zF_m`, `zR_m`, `KTF_N_m`, `KTR_N_m`;
- **08:** `DF_N`, `bal_dianteira`;
- **07 e 10:** `dgF_grau_mm`, `dgR_grau_mm`, `epsF_rad_rad`, `epsR_rad_rad`, `gsFL_grau` a `gsRR_grau`, `eixos_tir`;
- **16:** `sentido`, `toeFL_grau` a `toeRR_grau`, `R_m`, `cg_lateral_m`, `cza_m2`, `rho_kg_m3`, `cda_m2`, `crr`,
  `h2`, `h3`, `h7`, `h8`, `h9`;
- **24:** `h2v`, `h9v`, `fator_neutro`;
- **outros:** `ackermann_pct`, `crr_referencia` (sem chave em `x`; só a §7.2) e `lambda_<NOME>` para cada nome de
  `equilibrio.FATORES_LAMBDA` presente na 10_TIRE A86:A177.

A unidade do sufixo é a da planilha. O executor a confere na coluna de unidade da aba e, se não bater, para e relata.
`x` também recebe:
- `"coef"` e `"coef_nomes"` (os `lambda_*` sem o prefixo);
- `"motivo_r": ""`;
- `"R"`, `"fator"` e `"pct"` (de `R_m`, `fator_neutro` e `ackermann_pct`).

- [ ] **Step 1: Write the failing tests** (no início de `tests/test_sensibilidade_pneu.py`, com dados sintéticos
  montados no teste a partir dos números do `veiculo_base` de `tests/test_equilibrio.py`: L = 1,55, f tal que
  a = 0,837, e assim por diante; o rótulo diz "SINTÉTICO de teste")
  - `TC-SEN-001`: `x_de_dados` dá `a`, `b`, `m`, `huF` e `huR` pela regra da D2. Com L = 1,55 e f = 0,46, `a` vale
    `1.55*(1-0.46)` e `b` vale `1.55*0.46`, com igualdade exata em float. Também confere `a + b == L` depois de
    `editar(dados, L_m=1.60)`.
  - `TC-SEN-002`: `editar` devolve uma cópia (`dados` original intacto, conferido com `copy.deepcopy`); a chave
    editada fica com `origem == ORIGEM_EDITADO` e `editado is True`; as outras ficam iguais. `aplicar_set(dados,
    ["h_cg_m=0.31"])` dá o mesmo que `editar(dados, h_cg_m=0.31)`.
  - `TC-SEN-003`: `salvar_caso` levanta `ValueError` para `CAMINHO_DEMONSTRATIVO`, para o mesmo caminho relativo e
    para o mesmo caminho em maiúsculas (comparação por `Path.resolve()` e `os.path.normcase`). Uma gravação num
    `tempfile` volta igual por `ler_caso`.
  - `TC-SEN-004`: `aplicar_set` com chave desconhecida (`"massa=300"`), valor não numérico (`"L_m=abc"`), par sem
    `=`, chave `h2=2` e `sentido=esquerda` (minúsculas) levantam `ValueError`, e a mensagem cita a chave. `sentido=Direita` é aceito como texto.
  - `TC-SEN-005`: `valores_usados` lista todos os campos e os 5 `res_`. Cada `res_` tem `calculado_por` com a aba e
    a célula (ex. `"05_VEHICLE B9"`), e um campo `null` aparece com `valor None` e a origem `? A confirmar`.
- [ ] **Step 2: rodar e ver falhar.** Rode `uv run python -X utf8 tests/test_sensibilidade_pneu.py`. Esperado: o
  `ImportError` de `caso_pneu1`.
- [ ] **Step 3: implementar `python/caso_pneu1.py`** com as interfaces acima. `editar` aceita só chaves de `CAMPOS`;
  `tipo="chave"` aceita só 0 e 1; `sentido` aceita só "Esquerda" e "Direita". Cada `res_` cita a célula num
  comentário. `CAMPOS` traz `rotulo` e `descricao` para todo campo, em linguagem de leigo, sem faixa de valor.
- [ ] **Step 4: rodar e ver passar.** Esperado: `5 PASS, 0 FAIL, de 5 testes`.
- [ ] **Step 5: commit** `feat(pneu-1): caso em JSON editável (catálogo, leitura, edição)`.

### Task 2: captura do caso da V4.4 (commit `dados:`)

Modelo sugerido: Sonnet.

**Files:**
- Create: `tools/capturar_caso_pneu1.py`
- Create: `data/casos/caso_pneu1_demonstrativo.json` (gerado; commit próprio)

**Interfaces:**
- Consumes: `caso_pneu1.CAMPOS` e `CAMINHO_DEMONSTRATIVO`; `caso_planilha.origem_da_raiz` ou a rotina que
  `_origens_entradas` usa para a origem de uma célula raiz.
- Produces: o JSON no formato da Task 1, com `captura.sha256` da planilha lida.

- [ ] **Step 1: implementar `main(argv) -> int`**: `capturar_caso_pneu1.py <xlsx> [--saida ARQ]`. O padrão de
  `--saida` é `build/pneu1/caso_capturado.json`, nunca o demonstrativo direto.
  - Lê com `openpyxl.load_workbook(xlsx, data_only=False)`; cada campo pelo nome definido (`wb.defined_names`).
  - Recusa, com código 2 e o nome do campo, uma célula de entrada que tenha fórmula. Há duas exceções:
    - `fator_neutro` (B34, `=4/3`), aceito só se a fórmula casar com `^=\d+(\.\d+)?/\d+(\.\d+)?$` e avaliado como
      divisão;
    - `R_m`, calculado pela regra D2 a partir de `ent_24_modo_do_raio_r`, `ent_24_diametro_do_circulo_interno`,
      `ent_24_diametro_do_circulo_externo` e `ent_24_r_manual`. O modo "Rente aos cones" dá código 2 com a mensagem
      "modo do R não suportado na captura: use Linha central ou Manual".
  - A origem vem da coluna `org_` e a fonte da `fte_`; vazio ou ausente vira `? A confirmar`. `ackermann_pct` e
    `crr_referencia` ficam `null` com `? A confirmar`.
  - Imprime a tabela "campo | valor | origem" e a contagem por origem.
- [ ] **Step 2: rodar na V4.4 de `excel/`.** Comando:
  `uv run python -X utf8 tools/capturar_caso_pneu1.py excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx`.
  Esperado: código 0; `R_m` = 9,125, `fator_neutro` = 1,333…, h2 = h3 = h7 = h8 = h9 = 0, h2v = h9v = 1,
  `eixos_tir` = "ISO_TYDEX".
- [ ] **Step 3: parar e mostrar ao usuário** a tabela de origens (spec §11, 2º item). Seguir só com o "ok" dele.
- [ ] **Step 4:** copiar para `data/casos/caso_pneu1_demonstrativo.json` e conferir que `ler_caso` o lê.
- [ ] **Step 5: dois commits.** Primeiro `feat(pneu-1): captura do caso da V4.4` (a ferramenta). Depois
  `dados: caso demonstrativo do pneu-1 capturado da V4.4` (só o JSON).

### Task 3: família TTC e montagem do `CasoEquilibrio`

Modelo sugerido: Opus (a montagem passa pela rotina privada da planilha).

**Files:**
- Modify: `python/caso_pneu1.py`
- Modify: `tests/test_sensibilidade_pneu.py` (seção que precisa dos `.tir`)
- Create: `tests/test_caso_pneu1_equivalencia.py` (opcional da spec §5.4)

**Interfaces:**
- Consumes: `x_de_dados` (Task 1).
- Produces:
  - `achar_ttc() -> Path | None`;
  - `familia_ttc() -> ts.StaticTireFamily`. Sem pasta, levanta `FileNotFoundError` com a mensagem "sem os .tir do
    TTC Round 6: defina DDS_TTC_DIR …";
  - `CasoMontado(caso: eq.CasoEquilibrio, formas: eq.Formas, fator_neutro: float, kt_n_m: dict[str, float],
    valores: tuple[ValorUsado, ...], rotulos: tuple[str, ...])`;
  - `caso_de_dados(dados: dict, familia: ts.StaticTireFamily) -> CasoMontado`. Quando o caso não tem `epsF` ou
    `epsR`, usa `passo1=False` e acrescenta o rótulo "K com roll steer 0 = sem dado".

- [ ] **Step 1: escrever os testes que falham** (seção "com .tir"; sem família, a seção imprime NÃO EXECUTÁVEL e o
  script termina com o código 3 depois das seções sem `.tir`):
  - `TC-SEN-006`: com os dados sintéticos da Task 1, `caso_de_dados(...).caso` tem os mesmos campos de
    `caso_planilha._caso_de_valores(x_mao, tir12, False, VERIFICACOES_V43, ...)`, onde `x_mao` é o `x` com os `res_`
    escritos à mão no teste (`cfg`, `toe_rad`, `camber_estatico_rad`, `ganho_camber`, `raio_m` e `ds.p`, igualdade
    exata). `formas == Formas("v43","v43")` com h2v = h9v = 1. Com `sentido="Direita"`, o caso é igual a
    `eq.espelhar` do caso "Esquerda".
  - `TC-SEN-007`: `caso.ds.p` é o perfil de 12 psi com os `lambda_*` do JSON por cima, e
    `comparacao_pressao.diferencas_fora_de_lambda(caso.ds, fam.at_pressure(12.0))` dá `{}`.
  - `TC-SEN-008`: `editar(dados, f_dianteira=1.5)` e `editar(dados, h9=1)` com `crr` null fazem `caso_de_dados`
    levantar `ValueError` com a mensagem da verificação da planilha (o texto de `aba_equilibrio`, conferido por
    `in`).
- [ ] **Step 2: rodar e ver falhar.**
- [ ] **Step 3: implementar** `achar_ttc`, `familia_ttc` (`ts.load_profile_family(dir,
  source_axis_system="ISO_TYDEX")`) e `caso_de_dados` (D1). `kt_n_m = {"F": KTF_N_m, "R": KTR_N_m}`.
- [ ] **Step 4: escrever `tests/test_caso_pneu1_equivalencia.py`** (`TC-SEN-009`). Com `DDS_COPIA_V44_RECALC`
  apontando para uma cópia recalculada da V4.4, compara `caso_de_dados(ler_caso(demonstrativo))` com
  `caso_planilha.caso_da_planilha_v43(copia, tir12, passo1=...)`, campo a campo: `cfg` com tolerância relativa de
  1e-12, o resto exato. Sem a variável, sai NÃO EXECUTÁVEL com código 3. Não roda na entrega: fica pronto para uma
  conferência única.
- [ ] **Step 5: rodar o teste principal e ver passar.** Esperado: `8 PASS, 0 FAIL, de 8 testes`.
- [ ] **Step 6: commit** `feat(pneu-1): monta o CasoEquilibrio a partir do JSON`.

### Task 4: forças por roda e arrasto induzido

Modelo sugerido: Opus (sinal e convenção).

**Files:**
- Create: `python/sensibilidade_pneu.py` (primeira parte)
- Modify: `tests/test_sensibilidade_pneu.py`

**Interfaces:**
- Produces:
  - `forcas_por_roda(caso, ay_ms2: float, alfa_ref: tuple[float, float], *, formas) -> dict[str, tuple[float,
    float]]`, que dá canto → (α_i [rad, ISO], F_y,i [N, ISO]). A montagem usa:
    - `eq.cargas` e `eq.camber` em a_y;
    - `eq.entrada_limitada` por eixo;
    - α_i = α_ref,eixo + `eq.deriva_total(caso, formas=…)[c]`;
    - `tire_model.wheel_forces(caso.ds, c, fz_u, α_i, γ_u, 0.0)[1]`.

    Só usa funções públicas.
  - `LinhaArrasto(ay_ms2, ay_g, alfa_f_rad, alfa_r_rad, d_n, d_por_roda: dict[str, float], d_1a_ordem_n, d_sobre_mg,
    d_sobre_rolamento: float | None, rotulos)`;
  - `arrasto_induzido(caso, *, formas, ay_ate_ms2: float | None, ay_max_g: float = 2.0, passo_g: float = 0.1,
    crr_referencia: float | None = None) -> tuple[LinhaArrasto, ...]`. Usa D3 e D4;
    `d_1a_ordem_n = Σ_eixo forca_exigida·|α_ref,eixo|`; `d_sobre_rolamento` só existe com `crr_referencia`.

- [ ] **Step 1: escrever os testes que falham** (com `.tir`; caso sintético com o `cfg` do `veiculo_base`, toe 0 e
  γ 0, sem raio, `ds` de 12 psi):
  - `TC-SEN-010` (soma por eixo): para a_y = 0,5 g e 1,0 g, Σ F_y,i das rodas de cada eixo, com `cos δ_ref` na
    dianteira quando houver raio, iguala `eq.fy_eixo_limitado` do eixo no α de `angulos_necessarios`, com |Δ| <
    1e-9·F, e a força exigida (`eq.forca_exigida`), com |Δ| < 1e-6·F.
  - `TC-SEN-011` (sinal, toe e camber):
    - no caso simétrico, `d_n == 0.0` em a_y = 0 (com tolerância de 1e-9 N) e todo `d_por_roda` ≥ 0 em a_y > 0;
    - com toe FL/FR = −0,2° e +0,2° (toe-in nas duas, pela convenção do projeto), D(0) > 0 e nenhum D_i < −1e-9;
    - com F_y = 100 N e α = −0,05 rad dados à mão, −F_y·sen α = 100·sen(0,05).
  - `TC-SEN-012` (1ª ordem e grade):
    - `d_n/d_1a_ordem_n → 1` quando os α encolhem: com ay = 0,2 g, 0,1 g e 0,05 g, `|d_n/d_1a − 1|` decresce e o
      último fica < 1e-3. É um teste de consistência da linearização, como o TC-FXI-001 (sen α ≈ α), e não pretende
      provar O(α³) estrito: no caso simétrico, Fy_roda ≠ Fy_eixo/2;
    - com `ay_ate_ms2=None`, a última linha tem `ay_g ≤ 2,0`, e a linha seguinte da grade não resolve;
    - com `ay_ate_ms2` dado, a última linha tem `ay_ms2 ≤ ay_ate_ms2`.
- [ ] **Step 2: rodar e ver falhar.**
- [ ] **Step 3: implementar.** A docstring cita o Milliken RCVD §2.9, p. 64-65 e Fig. 2.36 (p. 67), a D3 e a soma
  roda a roda como escolha declarada (spec §7.2). D = J/m.
- [ ] **Step 4: rodar e ver passar.** Esperado: `11 PASS, 0 FAIL, de 11 testes`.
- [ ] **Step 5: commit** `feat(pneu-1): arrasto induzido por roda (Milliken §2.9)`.

### Task 5: corridas do estudo (tornado, pressão, combinação, pneu)

Modelo sugerido: Sonnet.

**Files:**
- Modify: `python/sensibilidade_pneu.py`
- Modify: `tests/test_sensibilidade_pneu.py`

**Interfaces:**
- Consumes: `CasoMontado` (Task 3) e `comparacao_pressao.comparar_carro`, `ResultadoCarro`.
- Produces:
  - `GRADE = {"ay_max_g": 2.0, "passo_g": 0.05, "n_alfa": 25}`;
  - `FATORES_EXPLORATORIOS: dict[str, list[float]]`, lido de `data/varredura_pneu_exploratoria.json`;
  - `ROTULOS: tuple[str, ...]`, os da spec §9, um por linha, e o aviso do `fator_neutro` (Global Constraints);
  - `rigidez_eixos(caso, *, formas) -> tuple[float | None, float | None, str | None]` (D5);
  - `LinhaCarro(rotulo_corrida, pressao_psi, variante_kt, fatores: dict[str,float], ay_lim_ms2, ay_lim_g, veredito,
    sentido_pior, c_f_n_rad, c_r_n_rad, k_grau_g, resolucao_ms2, borda_alfa, robustez: tuple | None, rotulos)`;
  - `linha_de_resultado(r: ResultadoCarro, *, formas, fatores=None) -> LinhaCarro`;
  - `tornado(cm: CasoMontado, familia) -> tuple[LinhaCarro, ...]`. A primeira linha é a base, com todos os λ em
    1,0; depois vem cada fator em 0,8 e 1,2. Tudo a 12 psi, variante a, `com_fatores` sobre o `ds` de 12 psi de
    `perfil_ajustado`, e `analise_par_dois_sentidos(..., **GRADE, formas=…, fator_neutro=…)`;
  - `pressao(cm, familia) -> tuple[ResultadoCarro, ...]`, que é `comparar_carro(caso, familia,
    kt_caso_n_m=cm.kt_n_m, formas=…, fator_neutro=…, **GRADE)`;
  - `combinacao(cm, familia) -> tuple[ResultadoCarro, ...]`, igual a `pressao` com
    `fatores_lambda=FATORES_EXPLORATORIOS`, só na variante a;
  - `LinhaPneu(pressao_psi, eixo, interpolado: bool, fz_n, c_alpha_n_rad, mu_y_pico, mu_y_borda: bool, rotulos)`;
  - `pneu_por_pressao(cm, familia, passo_psi=0.5) -> tuple[LinhaPneu, ...]`. Vai de 8 a 14 psi. Usa
    `tp.metricas_pneu(tp.avaliador_interpolado(familia, q), tp.faixa_comum(familia.profiles.values()), fz_n=…,
    camber_rad=…)`, com a Fz e o camber de eixo calculados como em `tools/relatorio_pressao.py` (linhas 184-187) e
    a Fz limitada a `teto_comum_fz` (com rótulo). `interpolado = q not in familia.pressures_psi`. O μ é o de
    `mu_y_pos`.

- [ ] **Step 1: escrever os testes que falham** (com `.tir`, caso sintético da Task 4):
  - `TC-SEN-013`: a linha base do tornado tem `ay_lim_ms2` e `veredito` iguais aos de `analise_par_dois_sentidos`
    direto no caso de 12 psi (λ = 1), e o tornado tem 1 + 2·3 = 7 linhas, sem nenhuma de fator 1,0 fora da base.
  - `TC-SEN-014`: `rigidez_eixos` dá C_f e C_r > 0, e o K de `linha_de_resultado` é igual a
    `para_graus_por_g(ResultadoCarro.k_rad_ms2)`. Uma conferência de consistência: `gradiente_pneus(W_f, W_r, C_f,
    C_r)` reproduz `parcelas_k(caso, 0).k_pneus`, com |Δ| < 1e-12 relativo.
  - `TC-SEN-015`: `pneu_por_pressao` tem 13 pressões × 2 eixos, `interpolado` False só em 8, 10, 12 e 14, e o Cα
    em 12 psi é igual ao de `metricas_pneu(avaliador_perfil(perfil12), …)`, com |Δ| < 1e-9 relativo.
- [ ] **Step 2: rodar e ver falhar.**
- [ ] **Step 3: implementar.** A combinação não entra em teste, por ser cara: a Task 7 mede o tempo dela.
- [ ] **Step 4: rodar e ver passar.** Esperado: `14 PASS, 0 FAIL, de 14 testes`.
- [ ] **Step 5: commit** `feat(pneu-1): corridas do estudo de sensibilidade`.

### Task 6: regra de "muda decisão", `Resultado` e `estudo()`

Modelo sugerido: Sonnet.

**Files:**
- Modify: `python/sensibilidade_pneu.py`
- Modify: `tests/test_sensibilidade_pneu.py`

**Interfaces:**
- Produces:
  - `Decisao(degrau: int, nome: str, fatores: tuple[str, ...], muda: Literal["sim","não","não avaliado","não medido
    aqui"], criterios: dict[str, str], frase: str, rotulos: tuple[str, ...])`;
  - `DEGRAUS: dict[int, str]`, com os nomes dos degraus 1 a 18 copiados da tabela de
    `docs/pneu/roteiro-modelo-de-pneu.md`;
  - `decidir_lambda(combinacao: Sequence[ResultadoCarro]) -> tuple[str, dict[str,str]]`. É o critério 1 da spec
    §6.3 em cada pressão, com a robustez PUSH ou LOOSE → "não", NÃO CONCLUSIVO → "sim" e N/A → "não avaliado",
    agregados pela D6;
  - `decidir_pressao(resultados_a: Sequence[ResultadoCarro], esc_ay: Escolha, esc_ca: Escolha) -> tuple[str,
    dict[str,str]]`. Critério 1: os vereditos PUSH/LOOSE/NEUTRO diferem entre pressões; um N/A conta como "não
    avaliado" naquela pressão. Critério 2: a D7 sobre `esc_ay` e sobre cada eixo de `esc_ca`;
  - `decidir_kt(resultados: Sequence[ResultadoCarro]) -> tuple[str, dict[str,str]]`. Critério 1: o veredito de a e b
    difere em alguma pressão. Critério 2: `|ay_a − ay_b| > banda_carro(variante a)[p].valor`; banda None ou ay None
    contam como "não avaliado" naquele nó;
  - `Resultado(valores: tuple[ValorUsado,...], tornado, pressao: tuple[LinhaCarro,...], combinacao:
    tuple[LinhaCarro,...] | None, pneu, arrasto, decisoes: tuple[Decisao,...], rotulos, tempos_s: dict[str,float])`,
    com `para_dict() -> dict` (só tipos JSON; sem `caso` nem `par`) e `resumo() -> list[str]` (uma frase por
    decisão);
  - `estudo(cm: CasoMontado, familia, rapido: bool = False) -> Resultado`. Com `rapido=True`: `combinacao=None` e a
    decisão de λ fica "não avaliado" ("combinação não rodada (--rapido)"). Na tabela final entram 18 decisões, uma
    por degrau. Os degraus 6 e 8 recebem `decidir_lambda`; 1, 2 e 3 recebem `decidir_pressao`; 12 recebe
    `decidir_kt`; 7 e 15 ficam "não avaliado" (D6); 16 é "este estudo" ("não medido aqui"); os demais ficam "não
    medido aqui" (spec §6.1).

As frases são simples e só usam o que foi medido. Exemplos: "a pressão muda o veredito: o carro passa de sair de
frente (8 psi) para sair de traseira (14 psi)", ou "não avaliado: o carro não chega ao limite até 2 g em nenhuma
pressão".

- [ ] **Step 1: escrever os testes que falham.** Os testes não usam `.tir`: usam o `ResultadoCarro` sintético, como
  `rc()` de `tests/test_tire_pressure.py`, copiado para o arquivo.
  - `TC-SEN-016` (D6 e λ): com a robustez `(PUSH, …)` nas 4 pressões, o resultado é "não". Com uma pressão `(NÃO
    CONCLUSIVO, …)`, é "sim". Com uma `(N/A, …)` e as outras PUSH, é "não avaliado". Com uma NÃO CONCLUSIVO e uma
    N/A, é "sim".
  - `TC-SEN-017` (pressão): só PUSH e bandas que não separam dão "não"; PUSH em 8 psi e LOOSE em 14 psi dão "sim"
    pelo critério 1; todos os `ay_lim_ms2` None dão "não avaliado".
  - `TC-SEN-018` (KT):
    - a e b iguais dão "não";
    - |Δay| maior que a banda num nó interno dá "sim";
    - veredito diferente entre a e b em uma pressão dá "sim";
    - ay None numa variante dá "não avaliado", se nada mais der "sim".
  - `TC-SEN-019`: `Resultado.para_dict()` passa por `json.dumps` sem erro; tem 18 decisões; todo degrau fora de
    {1,2,3,6,7,8,12,15} vale "não medido aqui"; cada decisão carrega `rotulos` não vazio. Usa um `Resultado`
    montado com listas vazias e as decisões sintéticas.
- [ ] **Step 2: rodar e ver falhar.**
- [ ] **Step 3: implementar.**
- [ ] **Step 4: rodar e ver passar.** Esperado: `18 PASS, 0 FAIL, de 18 testes`.
- [ ] **Step 5: commit** `feat(pneu-1): regra de muda decisão e resultado serializável`.

### Task 7: linha de comando e primeira execução

Modelo sugerido: Sonnet.

**Files:**
- Create: `tools/relatorio_pneu1.py`
- Modify: `tests/test_sensibilidade_pneu.py`

**Interfaces:**
- Consumes: `ler_caso`, `aplicar_set`, `familia_ttc`, `caso_de_dados`, `estudo` e `Resultado.para_dict/resumo`.
- Produces: `main(argv) -> int`. Os argumentos são `--caso ARQ` (padrão: o demonstrativo), `--set CHAVE=VALOR`
  (repetível), `--rapido` e `--saida DIR` (padrão `build/pneu1`). Grava `relatorio.md` e `resultados.json`.

Códigos de saída:

| Código | Situação |
|---|---|
| 0 | ok |
| 2 | entrada inválida (a mensagem vai para stderr, sem traceback) |
| 3 | NÃO EXECUTÁVEL (sem `.tir`) |

O `relatorio.md`, na ordem:
1. os rótulos (`ROTULOS`);
2. a tabela "valores usados";
3. o tornado;
4. a pressão (a e b);
5. a combinação;
6. o pneu por pressão;
7. o arrasto, com D em N (= J/m), D/(m·g), D/D_1ª ordem e a nota da spec §7.4;
8. a tabela por degrau, com "muda decisão" e a frase;
9. os tempos.

Não há lógica no script: só formatação.

- [ ] **Step 1: escrever o teste que falha** `TC-SEN-020`. Ele roda `main(["--rapido", "--set", "h_cg_m=0.31",
  "--saida", tmp])` e confere:
  - código 0;
  - os dois arquivos existem;
  - `resultados.json` tem `h_cg_m` com `editado: true` e a origem `✎ Editado pelo usuário`;
  - `relatorio.md` contém cada linha de `ROTULOS`.

  `main(["--set", "massa=1"])` dá o código 2. Só roda com `.tir`.
- [ ] **Step 2: rodar e ver falhar.**
- [ ] **Step 3: implementar.**
- [ ] **Step 4: rodar e ver passar.** Esperado: `19 PASS, 0 FAIL, de 19 testes`.
- [ ] **Step 5: execução completa** (em segundo plano: a combinação faz 27 × 4 `analise_par`). Rode
  `uv run python -X utf8 tools/relatorio_pneu1.py` e anote o tempo de cada parte (`tempos_s`) para o relatório.
  Esperado: código 0, com `build/pneu1/relatorio.md` e `build/pneu1/resultados.json`.
- [ ] **Step 6: commit** `feat(pneu-1): gerador do relatório (relatorio_pneu1)`. `build/` não é versionado.

### Task 8: EDR-075, relatório em `docs/` e registro no CLAUDE.md

Modelo sugerido: Sonnet, com a passagem pelo `humanizer-pt`.

**Files:**
- Modify: `docs/Engineering_Decision_Register.md` (entrada EDR-075, no formato das entradas vizinhas; Record_Status
  `APPROVED` e `IMPLEMENTED`, Validation `NOT_VALIDATED`)
- Create: `docs/pneu/sensibilidade-e-arrasto.md`
- Modify: `CLAUDE.md` (linha do subprojeto pneu-1 em "Situação atual" e a contagem esperada do teste em "Comandos")
- Modify: `docs/pneu/roteiro-modelo-de-pneu.md` (só a situação dos itens 15 e 16, apontando para o relatório; sem
  mudar a ordem)

- [ ] **Step 1: escrever o EDR-075.** O conteúdo:
  - a regra da spec §6.3 com a D6 e a D7;
  - D com −F_y·sen α roda a roda (D3), com a fonte (Milliken §2.9, p. 64-65, 67) e a generalização para 4 rodas
    como escolha;
  - o Fx·κ fora, sem fonte;
  - o caso em JSON, com os `res_` recalculados (D1 e D2) e o `fator_neutro` 4/3;
  - os IDs TC-SEN-001 a TC-SEN-020.
- [ ] **Step 2: escrever `docs/pneu/sensibilidade-e-arrasto.md`** a partir de `build/pneu1/relatorio.md`. Ele traz:
  - os números do caso demonstrativo e a tabela por degrau;
  - os rótulos da spec §9 no topo;
  - o que "não muda" significa (spec §6.3, último parágrafo);
  - os tempos medidos;
  - as pendências: traçado do enduro, Crr com fonte, Fx·κ, a conferência da §5.4 e a origem dos campos.

  Nenhum número fora do que a ferramenta deu. Depois, o texto passa pelo `humanizer-pt`.
- [ ] **Step 3: atualizar o CLAUDE.md e o roteiro.** No CLAUDE.md entra a linha "pneu-1 (subprojeto; EDR-075):
  `python/caso_pneu1.py`, `python/sensibilidade_pneu.py`, `tools/relatorio_pneu1.py`, 19 checks;
  `tests/test_caso_pneu1_equivalencia.py` só com cópia recalculada".
- [ ] **Step 4: conferir os módulos protegidos.** Rode `git diff --stat origin/main -- python/equilibrio.py
  python/escada.py python/equilibrio_linear.py python/comparacao_pressao.py python/tire_pressure.py excel/`.
  Esperado: saída vazia. Rode também o teste principal uma última vez (`19 PASS, 0 FAIL, de 19 testes`).
- [ ] **Step 5: commit** `docs(pneu-1): EDR-075 e relatório de sensibilidade e arrasto`.

### Fechamento (fora das tasks)

- Revisão do branch inteiro (pr-review-toolkit) e PR pelo `fluxo-github`. A descrição do PR leva os rótulos da §9 e
  as decisões D1 a D8.
