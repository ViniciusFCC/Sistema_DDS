# Posicionador da atuação — fase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Primeira versão funcional do posicionador (EDR-076): lê o STEP do chassi e os hardpoints fixos do T11 e devolve
onde `PUSH_OUT`, `PUSH_IN`, `ROCKER_AXIS_A/B`, `ROCKER_SPRING` e `SPRING_CHASSIS` podem ficar sem colidir com as peças e com
os gabaritos do regulamento, cumprindo as metas da equipe; quando não houver solução, diz quais restrições brigam.

**Architecture:** Pacote `python/posicionador/` com núcleo em SI e sem dependência de CAD (geometria por distância com sinal,
mecanismo por construção, varredura com `kinematics_model.Corner`, busca com vários pontos de partida) e um adaptador de STEP
(OpenCascade, opcional). Ferramenta de linha de comando em `tools/posicionar_atuacao.py`. Nada toca a planilha.

**Tech Stack:** Python 3.13, numpy, scipy, `cadquery-ocp` 8.0.1.1 (grupo opcional `cad`), matplotlib só se já estiver
disponível (figuras opcionais), testes em script com `check()`.

**Spec:** `docs/superpowers/specs/2026-11-17-posicionador-atuacao-design.md` (decisões: EDR-076;
`docs/posicionador/registro-de-decisoes.md`).

## Global Constraints

- SI no núcleo (m, rad, N); mm só na leitura do STEP (convertido na entrada) e na apresentação; unidade no nome do campo em
  JSON/CSV (`X_m`, `folga_mm`).
- Eixos ISO 8855 (X frente, Y esquerda, Z cima); pontos do canto `FL`; MR = Δroda/Δmola, nome `MR [wheel/spring]`.
- Nenhum valor sem fonte: todo limite da configuração tem `origem` ∈ {`REGRA`, `META`, `MARGEM_EQUIPE`, `HIPOTESE`,
  `A_CONFIRMAR`} e `fonte` (texto). `A_CONFIRMAR` com `valor: null` desliga a verificação correspondente e marca o resultado
  `CONDICIONAL`. Valor sintético de teste é rotulado "SINTÉTICO" no teste.
- Veredito de candidato: `VIAVEL` (todas as restrições duras avaliadas e cumpridas e nenhuma verificação desligada),
  `CONDICIONAL` (cumpridas, mas alguma desligada ou NÃO VERIFICÁVEL), `INVIAVEL`. Nunca "aprovado"/"validado" (VERIFIED ≠ validado).
- Testes são scripts com `check(name, condition, detail)` e terminam com `N PASS, 0 FAIL, de T testes` (copiar o cabeçalho e o
  rodapé de `tests/test_skidpad.py`). Teste que precisa de OCP e não o encontra imprime uma linha começando por
  `NÃO EXECUTÁVEL` e sai com código 3.
- Rodar sempre com `uv run python -X utf8 ...` (no Windows, `export UV_SYSTEM_CERTS=1` antes). OCP: `uv sync --extra cad`.
- Não importar nada de fora do repositório; o script do Murilo (`t11_atuacao.py`, `kinlib.py`) nunca entra no repositório:
  só as saídas dele, capturadas uma vez com o SHA-256 dos arquivos de origem.
- Commits separados por propósito: `dados:` para arquivos de dados, `deps:` para `pyproject.toml`/`uv.lock`, `feat(posicionador):`
  para código e testes de uma tarefa, `docs:` para documentação. Mensagens terminam com as linhas de atribuição da sessão.
- Não criar IDs além de TC-POS-001 a TC-POS-099 (autorizados); EDR só o 076.

## Review Focus

1. **STEP sem prefixos** (o `chassi.step` atual): tudo vira `FIXO_` com um aviso por componente, e a análise roda. → Task 3,
   check TC-POS-022.
2. **Escala ou referencial errado** (esferas `REF_X`/`REF_Y` a uma distância diferente de 100 mm de `REF_ORIGEM`, ou não
   ortogonais): erro claro com a distância medida, nunca resultado. → Task 3, check TC-POS-023.
3. **Cinemática que não resolve** em algum ponto do curso ou do esterçamento: o candidato sai `INVIAVEL` com o motivo
   "cinemática sem solução em dz = …", nunca exceção solta nem custo 1e6. → Task 6, check TC-POS-063.
4. **Ponto dentro de um sólido grande** (longe da superfície): a distância com sinal é negativa e o ponto sai bloqueado.
   → Task 2, check TC-POS-013.
5. **Configuração com valor sem fonte** (`A_CONFIRMAR`, `valor: null`): a verificação correspondente sai `NAO_VERIFICAVEL` e o
   veredito vira `CONDICIONAL`, nunca `VIAVEL`. → Task 6, check TC-POS-064.

---

### Task 1: Dados do T11 e curvas de referência do script atual (E0, parte 1)

**Files:**
- Create: `tools/capturar_v20_murilo.py`
- Create (gerados pela ferramenta, commit `dados:`): `data/posicionador/hardpoints_T11_v10.csv` e `.meta.json`,
  `data/posicionador/hardpoints_T11_v20_murilo.csv` e `.meta.json`, `data/posicionador/curvas_kinlib_v20.csv`,
  `data/posicionador/origem_v20_murilo.json`
- Create (cópia, commit `dados:`): `data/cad/T11_chassi_2026-11-17.step` (STEP recebido em 2026-11-17)
- Test: `tests/test_posicionador_dados.py`

**Interfaces:**
- Produces: os arquivos acima. `origem_v20_murilo.json` = `{"arquivos": {"t11_atuacao.py": "<sha256>", "kinlib.py": "<sha256>",
  "geometria_T11.json": "<sha256>"}, "x_semente": [8 números], "config_do_script": {...}, "data": "2026-11-17"}`.
  `curvas_kinlib_v20.csv` com colunas `dz_m,Ls_m,theta_rocker_rad` em 401 pontos uniformes de −0,023 a +0,0624 m.

- [ ] **Step 1: Escrever `tools/capturar_v20_murilo.py PASTA_DO_SCRIPT`.** Importa `t11_atuacao` e `kinlib` da pasta dada
  (sys.path), roda `avaliar(carregar_x(), corner(), final=True)` e `varrer` nos 401 pontos, e grava:
  - v10: os 9 pontos de `geometria_T11.json` (mm → m) como `FL_LCA_IN_F`=LF, `FL_LCA_IN_R`=LR, `FL_LCA_OUT`=LO,
    `FL_UCA_IN_F`=UF, `FL_UCA_IN_R`=UR, `FL_UCA_OUT`=UO, `FL_TIE_IN`=TI, `FL_TIE_OUT`=TO, `FL_WHEEL_CENTER`=WC, mais
    `FL_SPINDLE_PT` = WC + (0; 0,05; 0) m e `FL_CONTACT_PATCH` = (WC_x; WC_y; 0). Status `PROVISIONAL`. Meta: `geometry_rev`
    "T11-v10 (LR −6 mm)", `ground_plane_z_m` 0,0, `source` "geometria_T11.json do script de atuação (Murilo), recebido
    2026-11-17; SPINDLE_PT e CONTACT_PATCH são HIPÓTESE do kinlib (camber e toe estáticos nulos, solo em Z = 0)".
  - v20: v10 + `FL_PUSH_OUT`=O0 (Component `LCA`), `FL_PUSH_IN`=A0, `FL_ROCKER_AXIS_A`=Pv, `FL_ROCKER_AXIS_B`=Pv + 0,05·n,
    `FL_ROCKER_SPRING`=B0 (`ROCKER`), `FL_SPRING_CHASSIS`=C (`CHASSIS`). Meta `source` cita a saída do script.
  - curvas: `Ls = |B(dz) − C|` e θ do rocker de `varrer`, em m e rad.
  - `origem_v20_murilo.json` com o SHA-256 dos três arquivos de origem e o bloco CONFIGURAÇÃO do script lido como valores.
  Rodar com `-I` e `PYTHONDONTWRITEBYTECODE=1` sobre a cópia do script na pasta de trabalho da sessão
  (`.../scratchpad/atuacao/script_murilo/`).
- [ ] **Step 2: Rodar a ferramenta e conferir que gerou os 6 arquivos de dados.**
- [ ] **Step 3: Escrever `tests/test_posicionador_dados.py`:**
  - TC-POS-001: `hardpoints.load_hardpoints` aceita v10 e v20 (sem exceção); `Corner(hs, "FL").solve(0.0)` resolve nos dois;
    o v20 tem `has_push`.
  - TC-POS-002: `origem_v20_murilo.json` tem os três SHA-256 com 64 caracteres hex e `x_semente` com 8 números.
- [ ] **Step 4: Rodar `uv run python -X utf8 tests/test_posicionador_dados.py`. Esperado: `2 PASS, 0 FAIL, de 2 testes`.**
- [ ] **Step 5: Commits:** `dados:` (os arquivos de `data/`), depois `feat(posicionador):` (ferramenta e teste).

### Task 2: Geometria por distância com sinal (`geometria.py`)

**Files:**
- Create: `python/posicionador/__init__.py`, `python/posicionador/geometria.py`
- Test: `tests/test_posicionador_geometria.py`

**Interfaces:**
- Produces:
  - `class Capsula(a: ndarray, b: ndarray, r: float)`, `class Caixa(centro, eixos: ndarray 3×3 (linhas = eixos unitários),
    meias: ndarray 3)`, `class Barril(centro, eixo_unit, r_int, meia_largura)` (aro oco: região sólida = {raio ≥ r_int,
    |axial| ≤ meia_largura}), `class Esfera(c, r)`. Todas com `sdf(p: ndarray (N,3)) -> ndarray (N,)` em m, negativa dentro,
    1-Lipschitz, e `transformada(R: 3×3, t: 3) -> mesma classe`.
  - `folga_segmento(prim, a, b, raio: float, passo: float = 0.002) -> float`: min da `sdf` em pontos espaçados de no máximo
    `passo` sobre [a, b], menos `raio`, menos `passo/2` (conservador pela 1-Lipschitz).
  - `dist_seg_seg(p1, q1, p2, q2) -> float` exata (forma fechada).

- [ ] **Step 1: Teste que falha (`tests/test_posicionador_geometria.py`), valores SINTÉTICOS:**
  - TC-POS-010: `Capsula((0,0,0),(1,0,0),0.1).sdf` em (0,5;0,3;0) = 0,2; em (0,5;0;0) = −0,1; `Caixa` unitária centrada na
    origem, meias (0,5;0,5;0,5): sdf em (1,0,0) = 0,5 e em (0,0,0) = −0,5; `Esfera` idem analítico; erro < 1e-12.
  - TC-POS-011: `dist_seg_seg` bate com força bruta (malha 2001×2001) em 50 pares aleatórios (semente fixa), erro < 1e-6, e
    vale 0 em segmentos que se cruzam.
  - TC-POS-012: `Barril(centro=0, eixo=+Y, r_int=0,158, meia_largura=0,1)`: ponto no eixo (0,0,0) tem sdf = +0,158 (livre,
    dentro do aro); ponto em raio 0,2 e axial 0 tem sdf < 0 (no material do aro, modelado como sólido a partir de r_int);
    ponto axial 0,15 e raio 0,2 tem sdf = 0,05.
  - TC-POS-013 (Review Focus 4): ponto no centro de uma `Caixa` de 1 m tem sdf = −0,5 e `folga_segmento` de um segmento
    inteiramente dentro dela é negativa.
  - TC-POS-014: `folga_segmento` nunca supera a folga exata (calculada por `dist_seg_seg` para a cápsula) e a diferença é
    ≤ `passo` em 200 casos aleatórios.
- [ ] **Step 2: Rodar e ver falhar (ImportError).**
- [ ] **Step 3: Implementar `geometria.py`.** SDF da caixa e da cápsula pelas fórmulas padrão; barril em coordenadas
  (axial a, radial ρ): região sólida S = {ρ ≥ r_int, |a| ≤ w}; fora de S: distância euclidiana 2D até S; dentro: −min(ρ − r_int,
  w − |a|).
- [ ] **Step 4: Rodar. Esperado: `5 PASS, 0 FAIL, de 5 testes`.**
- [ ] **Step 5: Commit `feat(posicionador): geometria por distância com sinal (TC-POS-010 a 014)`.**

### Task 3: Leitor de STEP (`cad_step.py`) e dependência opcional

**Files:**
- Modify: `pyproject.toml` (`[project.optional-dependencies] cad = ["cadquery-ocp>=8.0.1.1"]`), `uv.lock`
- Create: `python/posicionador/cad_step.py` (a partir de `geo/step_tubos.py` da pasta de trabalho, endurecido: SI, sem
  constantes do T11 embutidas, sem prints)
- Test: `tests/test_posicionador_cad.py`

**Interfaces:**
- Consumes: `geometria.Capsula`, `geometria.Caixa`, `geometria.Esfera`.
- Produces:
  - `ler_step(caminho) -> Montagem` com `Montagem.pecas: list[Peca]`, `Peca(nome_componente: str, nome_corpo: str,
    categoria: str, shape)`; `categoria` ∈ {`CHASSI`, `FIXO`, `RODA_FE`, `RODA_FD`, `BANDEJA_FE`, `BANDEJA_FD`, `DIR`, `REF`,
    `HP`, `IGNORAR`} pelo prefixo do componente de primeiro nível (sem prefixo → `FIXO`); `Montagem.avisos: list[str]`.
  - `tubos_e_nos(montagem) -> (tubos: list[Tubo], nos: list[No])` com `Tubo(nome, pontos_eixo_m: ndarray (k,3), r_ext_m,
    secao: "redonda"|"quadrada")`, `No(pos_m, n_ramos, triangulado: bool)`; só peças `CHASSI` e `FIXO`.
  - `esferas(montagem) -> dict[str, ndarray]`: centro (m) das esferas cujo corpo começa com `REF_` ou `HP_`.
  - `referencial(esferas) -> (R: 3×3, t: 3)` que leva coordenadas do STEP ao referencial do carro (origem em `REF_ORIGEM`,
    X para `REF_X`, Y para `REF_Y`); `ErroReferencial` se |REF_X − REF_ORIGEM| ou |REF_Y − REF_ORIGEM| diferir de 0,100 m em mais
    de 0,5 mm ou se o ângulo entre eles diferir de 90° em mais de 0,1°.
  - `obstaculos_fixos(montagem, R, t) -> list[prim]`: tubo redondo reto → `Capsula`; trecho de tubo curvo → `Capsula` por
    corda com raio + flecha; tubo quadrado → `Caixa` exata; demais sólidos → `Caixa` orientada (OBB do OCP, conservadora).
  - `OCP_DISPONIVEL: bool`.

- [ ] **Step 1: Teste que falha (`tests/test_posicionador_cad.py`; sem OCP → `NÃO EXECUTÁVEL: cadquery-ocp ausente`, código 3):**
  - TC-POS-020: `data/cad/T11_chassi_2026-11-17.step`: 31 corpos lidos; 28 nós com 14 triangulados (tolerância de 5 mm);
    simetria em Y ≤ 0,5 mm entre tubos espelhados (números do relatório da geometria).
  - TC-POS-021: STEP SINTÉTICO gerado no próprio teste com OCP (montagem com componentes `CHASSI_TESTE` (um tubo redondo
    reto Ø 25,4 mm de 500 mm e um tubo quadrado 25 × 25 mm), `FIXO_CAIXA` (caixa 100 × 50 × 30 mm), `REF_REFERENCIAS` (esferas
    Ø 5 mm `REF_ORIGEM` em (10, 20, 30) mm, `REF_X` em (110, 20, 30), `REF_Y` em (10, 120, 30)) e `HP_FRENTE` (esfera
    `HP_FL_LCA_OUT` em (0, 600, 160) mm)) gravado em pasta temporária: categorias corretas; centros das esferas com erro
    < 1e-6 m; `referencial` leva `REF_ORIGEM` a (0,0,0) e `HP_FL_LCA_OUT` a (−0,010; 0,580; 0,130) m com erro < 1e-6 m.
  - TC-POS-022 (Review Focus 1): no STEP real, todas as peças sem prefixo saem `FIXO` e há um aviso por componente sem prefixo.
  - TC-POS-023 (Review Focus 2): STEP sintético com `REF_X` a 100 m (unidade errada simulada) → `ErroReferencial` cuja
    mensagem cita a distância medida.
  - TC-POS-024: para o tubo quadrado sintético, a folga da `Caixa` a 20 pontos ao redor nunca supera a distância exata do OCP
    (`BRepExtrema_DistShapeShape`) em mais de 0,2 mm, e para o tubo redondo a `Capsula` bate com o OCP em 0,01 mm.
- [ ] **Step 2: `uv add --optional cad "cadquery-ocp>=8.0.1.1"`; `uv sync --extra cad`; commit `deps:` (só
  `pyproject.toml` e `uv.lock`).**
- [ ] **Step 3: Rodar o teste e ver falhar (ImportError).**
- [ ] **Step 4: Implementar `cad_step.py`** reaproveitando a leitura da montagem pelo texto do STEP e a classificação de faces
  de `step_tubos.py`; converter mm → m na saída; nomes decodificados (`\X\E1` → á) antes de ler o prefixo.
- [ ] **Step 5: Rodar. Esperado: `5 PASS, 0 FAIL, de 5 testes`.**
- [ ] **Step 6: Commit `feat(posicionador): leitor de STEP com prefixos e esferas (TC-POS-020 a 024)`.**

### Task 4: Regulamento (`regulamento.py`)

**Files:**
- Create: `python/posicionador/regulamento.py`
- Test: `tests/test_posicionador_regulamento.py`

**Interfaces:**
- Consumes: primitivas de `geometria`.
- Produces:
  - `gabarito_t12() -> ndarray (8,2)`: octógono em (Y, Z relativo à base) m: 0,350 × 0,350 com chanfro 0,050 × 0,050 nos 4
    cantos (FSAE Rules 2027 V1.0, T.1.2; entalhes e faixa central de 50 mm ignorados = conservador, rotulado na docstring).
  - `trajetoria_t12(obstaculos: list[prim], x_ini, x_fim, z_min, z_max, passo_x=0.01, passo_z=0.005, y_centro=0.0) ->
    ResultadoGabarito(livre: bool|None, motivo: str, caminho_z: list[float])`: grade (x, z); célula livre se o gabarito
    posto em z, no plano x, não intercepta nenhum obstáculo (sdf de amostras do contorno e do interior > 0); existe trajetória
    se há caminho 4-conexo de células livres da coluna x_ini à x_fim (T.1.2.2c: altura livre). `x_ini` ou `x_fim` `None` →
    `livre=None`, motivo "NÃO VERIFICÁVEL: posição da coluna/pedal a confirmar".
  - `limite_aip(x_face_traseira_aip: float|None) -> callable(p) -> float` (folga em X; F.8.6.1); `None` → NÃO VERIFICÁVEL.

- [ ] **Step 1: Teste que falha, cenas SINTÉTICAS:**
  - TC-POS-030: `gabarito_t12()` tem largura e altura 0,350 m, área = 0,350² − 4·(0,05²/2), e é convexo.
  - TC-POS-031: sem obstáculos → `livre=True`; uma `Caixa` que bloqueia toda a altura entre z_min e z_max num x intermediário
    → `livre=False`; uma caixa que bloqueia só a metade de baixo num trecho e a de cima noutro trecho, sem sobreposição em x,
    → `livre=True` com `caminho_z` mudando de altura (é o caso da altura livre).
  - TC-POS-032: `x_fim=None` → `livre is None` e motivo começando por "NÃO VERIFICÁVEL".
  - TC-POS-033: `limite_aip(0.49)` dá folga 0,01 m para p com x = 0,48 e −0,01 para x = 0,50.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Rodar. Esperado: `4 PASS, 0 FAIL, de 4 testes`.**
- [ ] **Step 5: Commit `feat(posicionador): gabarito T.1.2 com altura livre e limite da AIP (TC-POS-030 a 033)`.**

### Task 5: Configuração com procedência e mecanismo por construção (`config.py`, `mecanismo.py`)

**Files:**
- Create: `python/posicionador/config.py`, `python/posicionador/mecanismo.py`, `data/posicionador/config_T11.json`
- Test: `tests/test_posicionador_mecanismo.py`

**Interfaces:**
- Consumes: `hardpoints`, `kinematics_model.Corner`, `kinematics_model.motion_ratio`, `data/posicionador/origem_v20_murilo.json`.
- Produces:
  - `config.carregar(caminho) -> Config`; cada item `Item(valor, unidade, origem, fonte)`; `Config.valor(nome)` em SI;
    `Config.a_confirmar() -> list[str]`; erro se faltar `origem` ou `fonte` ou se `origem` for desconhecida.
  - `config_T11.json`: os limites do bloco CONFIGURAÇÃO do script (DROOP 23 mm e BUMP 62,4 mm, EYE 210 mm, STROKE 61 mm,
    MR_ALVO 1,40, MR_VAR_MAX 0,04, DJ 35 mm, braços 55–80 mm, GIRO_MAX 60°, AMORT_ANG_MAX 30°, folgas 10/5/5 mm, raios
    25/12/20/8 mm, FOLGA_GAB 10 mm) com `origem: "META"` ou `"MARGEM_EQUIPE"` e `fonte: "t11_atuacao.py (Murilo), bloco
    CONFIGURAÇÃO, sha256 …"`; aro `HIPOTESE` (r_int 0,158 m, meia largura 0,100 m, kinlib); `curso_cremalheira_m`,
    `margem_curso_amortecedor_m`, `x_face_traseira_aip_m`, `x_ini_t12_m`, `x_fim_t12_m`: `A_CONFIRMAR` com `valor: null`;
    `x_max_olhal_m` 0,400 e `caixa_busca_pivo_m` com X ∈ [−0,150; 0,150] (`META`, limites |Pv_x| ≤ 150 mm e C_x ≤ 400 mm do
    script) e Y, Z `null` (derivados da caixa envolvente das peças `CHASSI`/`FIXO` do lado esquerdo no STEP; sem STEP, a
    ferramenta exige `--caixa`); `transformacao_step_m` (`HIPOTESE`: translação (−0,942; 0; +0,0774) m, sem rotação, ajustada
    no lado reto do FH com erro ≤ 0,55 mm, `docs/posicionador/pesquisa/relatorio-geo.md`), usada só quando o STEP não traz as
    esferas `REF_` (caso do `chassi.step` atual); com as esferas, elas mandam.
  - `mecanismo.Variaveis(pivo_m: ndarray 3, az_rad, el_rad, r1_m, phi_b_rad)`;
    `mecanismo.construir(hs_v10, v: Variaveis, cfg, r2_m: float|None = None) -> Construcao(hardpoints: HardpointSet (v10 +
    grupo pushrod), r2_m, motivo: str|None)` (com `r2_m` dado, não resolve o MR): regra do plano e do push rod do script (plano contém a junta `LCA_OUT`, o pivô e a direção do
    amortecedor; push rod na reta da junta, a `DJ` dela, perpendicular ao braço r1 no estático; `LADO_ROCKER` = −1);
    r2 resolvido para MR(0) = MR_ALVO (brentq em [0,2·r1; 3·r1]); olhal C na reta do amortecedor tal que o comprimento no
    droop máximo = EYE. Sem raiz ou geometria degenerada → `hardpoints=None` e `motivo` legível.
- [ ] **Step 1: Teste que falha:**
  - TC-POS-050: `construir` com a `x_semente` da v20 (mm/° convertidos) e r2 forçado ao valor da v20 reproduz `PUSH_OUT`,
    `PUSH_IN`, `ROCKER_AXIS_A`, `ROCKER_SPRING` do arquivo v20 com erro < 1e-6 m.
  - TC-POS-051: com r2 resolvido, `motion_ratio(Corner, 0.0)["mr_wheel_per_spring"]` = 1,40 ± 1e-4.
  - TC-POS-052: |B(dz = −DROOP) − C| = EYE ± 1e-6 m.
  - TC-POS-053: `config.carregar` recusa item sem `fonte`; `a_confirmar()` lista os 5 itens `A_CONFIRMAR` do T11.
  - TC-POS-054: pivô colocado sobre a junta `LCA_OUT` → `hardpoints is None` e motivo não vazio.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar `config.py`, `mecanismo.py` e escrever `config_T11.json`.**
- [ ] **Step 4: Rodar. Esperado: `5 PASS, 0 FAIL, de 5 testes`.**
- [ ] **Step 5: Commits `dados:` (config) e `feat(posicionador): mecanismo por construção e configuração com procedência
  (TC-POS-050 a 054)`.**

### Task 6: Varredura e avaliação de um candidato (`varredura.py`) — E0, parte 2

**Files:**
- Create: `python/posicionador/varredura.py`
- Test: `tests/test_posicionador_varredura.py`

**Interfaces:**
- Consumes: `Construcao`, `Config`, primitivas, `regulamento`, `Corner`, `motion_ratio`.
- Produces:
  - `Cena(fixos: list[prim], nos: list[No], aro: (r_int_m, meia_largura_m), regras)`;
    `cena_sem_cad(cfg) -> Cena` (só aro) e `cena_do_step(montagem, R, t, cfg) -> Cena`.
  - `avaliar(construcao, cena, cfg, n: int = 25) -> Avaliacao` com `restricoes: list[Restricao(nome, valor, limite, folga,
    estado: "OK"|"VIOLADA"|"NAO_VERIFICAVEL", origem, fonte, motivo)]`, `veredito`, curvas (`dz_m`, `MR [wheel/spring]`,
    `Ls_m`, `angulo_fora_do_plano_rad`), `dist_no_m` (pivô e olhal ao nó mais próximo). Restrições: MR(0) ± 0,01; variação de
    MR ≤ MR_VAR_MAX (max/min do MR local de `motion_ratio` em n pontos); comprimento do amortecedor ∈ [EYE − STROKE + margem,
    EYE] em todo o curso; braços; giro; ângulo do amortecedor a X; folgas (push rod, rocker como cápsulas Pv–A e Pv–B,
    amortecedor como cápsula B–C) aos `fixos`, ao aro (segmento real O→A, aro movido com a manga), às pernas das bandejas e ao
    tirante; gabarito; AIP; esterçamento (se `curso_cremalheira_m` existir; senão NAO_VERIFICAVEL).
  - `avaliar_convergido(construcao, cena, cfg, n0=25) -> Avaliacao`: avalia com n e 2n; se algum estado mudar, dobra até 8·n0;
    se ainda mudar, veredito `INVIAVEL` com motivo "resolução não convergiu".
- [ ] **Step 1: Teste que falha:**
  - TC-POS-060: `Corner` × `kinlib` na v20: `Ls(dz)` de `hardpoints_T11_v20_murilo.csv` com `Corner` bate com
    `curvas_kinlib_v20.csv` em todos os 401 pontos com erro < 1e-5 m. Se falhar, PARAR e reportar (critério de aprovação do
    EDR-076): não seguir com a busca.
  - TC-POS-061: avaliação convergida da v20 (`cena_sem_cad`): variação de MR entre 0,060 e 0,062 → `VIOLADA`; folga ao aro no
    segmento real entre 0,079 e 0,0825 m (relatório: 81,5 mm com o raio de 7,94 mm do kinlib; aqui o raio é R_PROD = 8 mm e a
    amostragem desconta passo/2); veredito `INVIAVEL`.
  - TC-POS-062: `avaliar` com n = 25 e n = 50 na v20 dá os mesmos estados em todas as restrições, exceto a variação de MR,
    cujo valor converge (|v50 − v400| < |v25 − v400|).
  - TC-POS-063 (Review Focus 3): construção com pivô a 2 m do carro (push rod que não fecha) → `INVIAVEL` com motivo que
    começa por "cinemática sem solução", sem exceção.
  - TC-POS-064 (Review Focus 5): com `curso_cremalheira_m` nulo, a restrição de esterçamento sai `NAO_VERIFICAVEL` e um
    candidato SINTÉTICO que cumpre todo o resto sai `CONDICIONAL`.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar `varredura.py`.** Estados da roda por `Corner.solve(travel, steer)`; posições dos pontos por
  `Corner.pt`; aro em cada estado = `Barril(centro = pt(WHEEL_CENTER), eixo = unit(pt(SPINDLE_PT) − centro))`, sem mudar
  `kinematics_model.py`; folgas por
  `geometria.folga_segmento`; captura `KinematicsError` por ponto do curso.
- [ ] **Step 4: Rodar. Esperado: `5 PASS, 0 FAIL, de 5 testes`.**
- [ ] **Step 5: Commit `feat(posicionador): varredura e avaliação convergida (TC-POS-060 a 064)`.**

### Task 7: Mapa de espaço livre e busca com diagnóstico (`espaco_livre.py`, `busca.py`)

**Files:**
- Create: `python/posicionador/espaco_livre.py`, `python/posicionador/busca.py`
- Test: `tests/test_posicionador_busca.py`

**Interfaces:**
- Consumes: `Cena`, `Config`, `mecanismo.construir`, `varredura.avaliar`, `varredura.avaliar_convergido`.
- Produces:
  - `mapa(cena, caixa_m: (min3, max3), passo_m=0.01, raio_m=0.0) -> Mapa(grade (nx,ny,nz,3), folga_m, dist_no_m)`;
    `Mapa.livres(raio_m) -> ndarray (k,3)`.
  - `buscar(hs_v10, cena, cfg, caixa_m, n_amostras=2000, n_refinos=20, semente=0) -> ResultadoBusca(candidatos:
    list[Candidato(variaveis, construcao, avaliacao)], fase1: Diagnostico|None)`: pivôs amostrados entre os pontos livres do
    mapa (peso maior perto de nó, U3); demais variáveis por LHS nas faixas da configuração; avaliação rápida (n = 11); os
    melhores por violação máxima normalizada são refinados com `scipy.optimize.minimize` (Nelder-Mead, sobre a violação máxima;
    os parâmetros discretos ficam fixos); todo candidato devolvido como viável passa por `avaliar_convergido`.
    Ordenação dos viáveis: variação de MR, depois distância do pivô e do olhal ao nó, depois ângulo fora do plano.
  - `Diagnostico(melhor: Candidato, conflitos: list[tuple[str, str, float]])`: quando não há viável, o candidato de menor
    violação máxima e os pares de restrições que mais vezes falham juntas nas amostras (coocorrência).
- [ ] **Step 1: Teste que falha:**
  - TC-POS-070: cena SINTÉTICA sem obstáculos e metas folgadas (MR_VAR_MAX 0,5; curso do amortecedor livre) → pelo menos um
    candidato `VIAVEL` ou `CONDICIONAL`, e todos os devolvidos foram reavaliados por `avaliar_convergido`.
  - TC-POS-071: metas impossíveis (MR_VAR_MAX 0,0001) → nenhum viável e `fase1` cita a variação de MR entre os conflitos.
  - TC-POS-072: `mapa` numa cena com uma `Capsula` SINTÉTICA: folga de um ponto da grade = sdf analítica; pontos dentro da
    cápsula fora de `livres(0)`.
  - TC-POS-073: mesma `semente` → mesma lista de candidatos (determinismo).
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Rodar. Esperado: `4 PASS, 0 FAIL, de 4 testes`.**
- [ ] **Step 5: Commit `feat(posicionador): mapa de espaço livre, busca e diagnóstico (TC-POS-070 a 073)`.**

### Task 8: Ferramenta, relatório, registro no executor e documentação

**Files:**
- Create: `tools/posicionar_atuacao.py`, `python/posicionador/relatorio.py`
- Modify: `tools/rodar_testes.py` (itens do posicionador), `CLAUDE.md` (Situação atual e Comandos),
  `docs/Engineering_Decision_Register.md` (EDR-076: Status IMPLEMENTED e Evidence), `docs/posicionador/README.md`
- Test: `tests/test_posicionador_ferramenta.py`

**Interfaces:**
- Consumes: tudo acima.
- Produces: `uv run python -X utf8 tools/posicionar_atuacao.py --step ARQ.step --hardpoints data/posicionador/hardpoints_T11_v10.csv
  --config data/posicionador/config_T11.json --saida PASTA [--avaliar-v20] [--amostras N] [--semente S]` grava em PASTA:
  `candidatos.csv` (schema de hardpoints, Status `PROVISIONAL`, um conjunto por candidato com sufixo no `geometry_rev` do
  meta), `relatorio.md` (veredito, restrições com folga, origem e fonte, itens `A_CONFIRMAR`, avisos do STEP, hash SHA-256 do
  STEP, rótulo "VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics"), `resultado.json`; figuras só se
  matplotlib existir. Sem `--step`: roda com `cena_sem_cad` e avisa.
- [ ] **Step 1: Teste que falha:**
  - TC-POS-080: ferramenta com `--avaliar-v20` sem STEP → código 0, `relatorio.md` contém "INVIAVEL" e "variação de MR".
  - TC-POS-081: ferramenta com o STEP real (se OCP) e `--amostras 200 --semente 0` → código 0; cada conjunto de
    `candidatos.csv`, separado e com o meta, carrega com `hardpoints.load_hardpoints` (ou a pasta traz só `fase1` no
    `resultado.json`).
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar; registrar os testes em `tools/rodar_testes.py` com os N esperados (dados 2, geometria 5, cad 5,
  regulamento 4, mecanismo 5, varredura 5, busca 4, ferramenta 2).**
- [ ] **Step 4: Rodar cada teste do posicionador e `uv run python -X utf8 tests/test_executor.py`. Esperado: todos PASS.**
- [ ] **Step 5: Atualizar EDR-076 (IMPLEMENTED, Evidence com as contagens), `CLAUDE.md` e o README; commits `feat` e `docs`
  separados; push.**
