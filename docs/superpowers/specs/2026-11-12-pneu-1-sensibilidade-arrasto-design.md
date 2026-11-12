# pneu-1: estudo de sensibilidade do pneu e arrasto induzido (design)

Data: 2026-11-12. Situação: APROVADA pelo usuário em 2026-11-12, com os IDs EDR-075 e TC-SEN-001 em diante autorizados.
Origem: `docs/pneu/roteiro-modelo-de-pneu.md`, Fase 1, itens 16 e 15.

## 1. Intenção

O roteiro do pneu ordena 18 degraus, mas a ordem é opinião (conselho de 2026-11-11). Este subprojeto mede quanto
cada fonte de incerteza do pneu mexe nas saídas que a equipe usa para decidir. Com isso, a ordem dos próximos degraus
passa a ter número por trás. Ele também calcula o arrasto induzido pela deriva em curva, que entra na energia do
enduro e hoje não tem um número próprio.

Pedidos do usuário nesta conversa (2026-11-12):
- o modelo roda sozinho, sem planilha, sem Excel e sem LibreOffice;
- o usuário pode alterar os dados base (massa, CG, bitola...) para iterar.

## 2. Objetivos, não objetivos e anti-objetivos

Objetivos:
- (a) Sensibilidade de a_y limite, veredito (PUSH/LOOSE/NEUTRO/N/A), Cα de cada eixo e K a λ (LFZO, LMUY, LKY),
  à pressão (8 a 14 psi) e à rigidez vertical do pneu (variante b do EDR-071), com a regra de "muda decisão" da §6.
- (b) Arrasto induzido D = Σ F_y,i·sen α_i (Milliken), por condição de curva no caso, em N (= J/m), com a
  comparação com a forma de 1ª ordem que o código já usa (v43, EDR-066).
- Caso em arquivo próprio, editável, com origem por valor.
- Tabela final: cada degrau do roteiro com "muda decisão: sim / não / não medido aqui".

Não objetivos:
- pressão intermediária no carro (é o pneu-3, A2 no carro); aqui ela só aparece no nível do pneu;
- o termo Fx·κ do arrasto (sem fonte conferida; §7.3);
- modelo de pista ou energia total do enduro (falta o traçado);
- qualquer planilha nova ou célula nova.

Anti-objetivos (fracasso mesmo funcionando):
- um número com cara de resultado do T11 ou de calibragem. Tudo sai rotulado (§9);
- alterar `python/equilibrio.py`, `python/escada.py` ou `python/equilibrio_linear.py` (o incremento 9 os está
  mudando em outra sessão); também não alterar `comparacao_pressao.py` nem `tire_pressure.py`;
- inventar amplitude, limite ou coeficiente.

## 3. Restrições

- Só Python. As fontes de verdade e as convenções do `CLAUDE.md` valem (ISO 8855, SI no núcleo, unidade no nome).
- O `.tir` vem da família TTC Round 6 (`references/ttc/` ou `DDS_TTC_DIR`, fora do Git). Nesta worktree,
  `DDS_TTC_DIR` aponta para `C:\Users\vferr\Documents\Sistema_DDS\references\ttc\round6_hoosier_r25b_20p5x7_13_7in`
  (os 4 `.tir` de 8 a 14 psi, conferidos em 2026-11-12). Sem ela, a ferramenta e os
  testes que precisam dela saem NÃO EXECUTÁVEL (código próprio, nunca "aprovado").
- Amplitudes de λ: as do `data/varredura_pneu_exploratoria.json` (EDR-055: 0,8, 1,0 e 1,2, "○ Arbitrário /
  demonstrativo"). Pressões: as 4 medidas (8, 10, 12 e 14 psi). A grade do equilíbrio é a do `relatorio_pressao`
  (`ay_max_g` 2,0, `passo_g` 0,05, `n_alfa` 25, `fator_neutro` 1,0).
- Verificação só pelos testes afetados, não pela suíte inteira.
- IDs novos (EDR, TC) só com autorização (§11).

## 4. Abordagens consideradas

1. **Escolhida.** Módulo fino `python/sensibilidade_pneu.py`, que só orquestra o que existe
   (`comparacao_pressao.comparar_carro`, `equilibrio.varredura_pneu`, `equilibrio.veredito_robusto`,
   `comparacao_pressao.banda_carro/banda_pneu/decidir`, `tire_pressure.metricas_pneu`,
   `equilibrio_linear.angulos_necessarios/parcelas_k`), com uma função nova de arrasto. O caso vem de um JSON.
   Gerador em `tools/`. Testável sem planilha.
2. Script único em `tools/`. Mais rápido de escrever, mas quase nada fica testável.
3. Só a combinação completa de λ, sem o tornado. Diz se o sinal vira, mas não diz qual fator manda.

Primeiro o usuário escolheu (A), o caso da planilha por cópia recalculada no LibreOffice. Depois pediu que o modelo
rode sem planilha. A 1 ficou com o caso em JSON (§5).

## 5. Caso em arquivo (dados base editáveis)

### 5.1 Formato

`data/casos/caso_pneu1_demonstrativo.json`, versionado. Por campo: `valor`, `origem` (rótulo da lista Origens, ex.
`◐ Dado de outro carro (TX, T09)`), `fonte` (nome definido e célula da V4.4) e, no topo, o SHA-256 do arquivo de
onde saiu e a data. Chaves com unidade no nome (`m_total_kg`, `h_cg_m`, `L_m`, `tF_m`, `KsF_N_m`, `MRF`...).

Entram só as **entradas** (`ent_` da tabela de nomes), nunca os resultados (`res_`). Os resultados que o caso usa (a
e b, massa total, alturas do CG não suspenso, R usado...) são recalculados em Python com a mesma regra da célula
da V4.4, citada no código pela aba e célula. Exemplo: `a = L·(1 − f)` e `b = L·f`, com f = fração de peso no eixo
dianteiro (`ent_05_fracao_de_peso_no_eixo_dianteiro_f`). Assim, editar L não deixa a + b ≠ L. As chaves de
hipótese (h1 a h10, h2v, h9v) e os λ da 10_TIRE também são entradas do JSON.

O conjunto de entradas é o que `caso_planilha.caso_da_planilha_v43` usa (`ENTRADAS_CASO` e as chaves da V4.3),
levado de volta às entradas primárias. As entradas estão espalhadas nas tabelas `data/nomes_V4_0.csv` a
`nomes_V4_4.csv`, em `aba_equilibrio.NOME_ENT` e em `aba_curva.NOME24`; a captura junta todas.

Decisões do Claude depois da revisão do builder (escolhas que o usuário pode mudar):
- **R:** o JSON guarda `R_m` como entrada primária. A captura o calcula uma vez com a regra da 24_CURVA B20 (R
  usado, a partir dos diâmetros e do modo), reproduzida no script de captura e conferida pelo teste da §5.4. O
  usuário itera editando `R_m` direto. Não há reimplementação da 24_CURVA no modelo.
- **fator_neutro** (24_CURVA B34) é entrada do JSON e vai para `analise_par(..., fator_neutro=...)`.
- **Formas:** `h2v` e `h9v` do JSON escolhem `Formas("v43" | "v42", ...)`, como em `caso_da_planilha_v43`, e
  aparecem na tabela "valores usados".
- **Pneu do caso:** `caso.ds` = perfil de 12 psi da família TTC com os λ ≠ 1 do JSON, sem os coeficientes que a
  10_TIRE sobrescrevia. Pelo `references/INDEX.md`, o `.tir` provisório de 12 psi tem os mesmos coeficientes do perfil
  de 12 psi. O teste da §5.4 lista qualquer diferença por `comparacao_pressao.diferencas_fora_de_lambda`.
- **Origem vazia:** quando a coluna `org_` de uma entrada estiver vazia ou faltar, a origem gravada é `? A
  confirmar`, como faz `caso_planilha._origens_entradas`.
- **Crr:** com h9 desligada, o caso não leva `crr`, porque ligá-lo ativa a tração e muda o caso. O JSON tem um
  campo à parte, `crr_referencia`, usado só na comparação da §7.2. Ele fica `null` ("a confirmar") até haver fonte.

### 5.2 Captura (uma vez)

`tools/capturar_caso_pneu1.py <xlsx>` lê, com openpyxl (`data_only=False`), as células de entrada da V4.4 de
`excel/`, com a origem (`org_`) e a fonte (`fte_`), e grava o JSON. Entradas são constantes, então não há recálculo.
A captura recusa uma célula de entrada com fórmula. É a única peça que abre a planilha, e não está no caminho de
execução do modelo. O commit do JSON é separado (`dados: ...`).

### 5.3 Edição para iterar

- `--caso <arquivo.json>`: uma cópia editada pelo usuário.
- `--set chave=valor` (repetível): sobrescreve na hora, sem arquivo novo.
- API em Python, para scripts e notebooks (a linha de comando usa as mesmas funções):
  - `ler_caso(caminho) -> dados`;
  - `editar(dados, **chaves) -> dados novo` (nunca altera o original; marca as chaves editadas);
  - `salvar_caso(dados, caminho)` (grava uma variante com as marcas de editado; nunca por cima do
    `caso_pneu1_demonstrativo.json`);
  - `familia_ttc() -> StaticTireFamily` (lê `DDS_TTC_DIR` ou `references/ttc/`; sem eles, erro claro);
  - `caso_de_dados(dados, familia) -> (CasoEquilibrio, Formas, fator_neutro, ValoresUsados)`;
  - `estudo(caso, formas, familia, rapido=False) -> Resultado` (tornado, combinação, pressão, arrasto,
    `muda_decisao`, `resumo()`).

Todo valor sobrescrito por `--set` ganha a origem `✎ Editado pelo usuário`. Um valor editado no JSON fica com a origem
que o usuário escrever lá. "Dado do T11" só aparece se o usuário marcar. Cada saída começa com a tabela "valores
usados": chave, valor, unidade, origem, editado (sim/não). Entrada incoerente → erro com a mensagem do
`VehicleConfig` ou do `CasoEquilibrio`, que já validam (a + b = L, massas, chaves). Chave desconhecida no `--set`,
ou valor que não é número, também é erro, sem adivinhar.

### 5.5 Preparo para a interface (usuário, 2026-11-12)

O usuário pretende fazer, na última versão, uma interface para que pessoas leigas usem e entendam a ferramenta. A
interface não faz parte deste subprojeto, nem a escolha da tecnologia dela. Para que ela venha sem retrabalho:
- **A API é o núcleo.** A linha de comando e a futura interface são cascas finas sobre `ler_caso`, `editar`,
  `caso_de_dados` e `estudo`. Nenhuma lógica fica no script de `tools/`.
- **O JSON descreve os próprios campos.** Além de `valor`, `origem` e `fonte`, cada campo tem `rotulo` (texto
  legível, ex. "Altura do CG"), `unidade_exibicao` e `descricao` (uma frase). Não há faixa de valor, que seria um
  limite inventado. A validação é a física que já existe, com mensagens em português que um leigo entende.
- **O resultado é dado, não texto.** `estudo()` devolve um objeto com `para_dict()` (serializável em JSON): números,
  unidades, rótulos da §9 e o "muda decisão" de cada degrau. O relatório em Markdown é só uma forma de exibição.
- **Cada conclusão vem com uma frase simples**, ex. "a pressão muda o veredito: entre 8 e 14 psi o carro passa de
  sair de frente para sair de traseira". Os rótulos da §9 vão junto, no mesmo objeto, para que nenhuma tela mostre
  um número sem o aviso.

### 5.4 Equivalência com a planilha (verificação, não dependência)

Um teste opcional confere que `caso_de_dados(JSON capturado)` dá o mesmo `CasoEquilibrio` que
`caso_planilha.caso_da_planilha_v43` sobre uma cópia recalculada da V4.4. Ele só roda se houver uma cópia
recalculada (caminho por variável de ambiente); sem ela sai NÃO EXECUTÁVEL. É o que prova que a regra dos `res_`
foi copiada certa. Fazer essa conferência uma vez, com LibreOffice, está fora do caminho de execução.

## 6. (a) Estudo de sensibilidade

### 6.1 Fatores e degraus

| Fator | Faixa | Degraus do roteiro |
|---|---|---|
| LMUY | 0,8 / 1,0 / 1,2 (EDR-055) | 6 (pneu substituto), 8 (λμ no skidpad) |
| LFZO | 0,8 / 1,0 / 1,2 (EDR-055) | 6, 8 |
| LKY | 0,8 / 1,0 / 1,2 (EDR-055) | 8 (λKy) |
| Pressão | 8, 10, 12, 14 psi (perfis medidos) | 1 (A2 no carro), 2 (PP*/QPZ), 3 (A3, pressão quente) |
| KT | variante a (KT do caso) × b (VERTICAL_STIFFNESS do perfil) | 12 (rigidez vertical) |
| Arrasto induzido × resistência ao rolamento | §7 | 7, 15 |

Não medidos aqui, e declarados assim na tabela final: 4 e 5 (transiente, dinâmica), 9 e 14 (Mz, OptimumTire),
10 (combinado), 11 (temperatura), 13 (raios), 17 e 18 (instrumentação, ciclo).

### 6.2 Corridas

- **Tornado:** um λ por vez em 0,8 e 1,2, com os outros em 1,0, a 12 psi (o perfil de base do caso), variante a.
  Ele é aplicado por `com_fatores` sobre o `ds` do perfil: λ do caso × fator, como faz o `varredura_pneu`.
- **Combinação:** 3×3×3 de λ em cada uma das 4 pressões, por `comparar_carro(..., fatores_lambda=...)`, que já
  devolve a robustez (`veredito_robusto`, no sentido esquerdo, como hoje).
- **Pressão:** `comparar_carro` nas 4 pressões, variantes a e b (b só se o caso tiver KT; o JSON tem).
- **Pressão no nível do pneu:** Cα e pico de μ_y por `tire_pressure` (`metricas_pneu` com `avaliador_interpolado`) de
  8 a 14 psi, passo 0,5 psi, na Fz estática de cada eixo do caso. Rótulo INTERPOLADO nos pontos fora dos medidos.
- `--rapido`: só o tornado e a pressão, sem a combinação (para as iterações).

Saídas por corrida: a_y_lim [m/s² e g], veredito e sentido pior, C_f e C_r [N/rad] (rigidez do eixo que o
`equilibrio_linear` já calcula para o K; o builder escolhe a função pública que a expõe), K [°/g], resolução
numérica, borda de α.

### 6.3 Regra de "muda decisão" (escolha do Claude, sem número novo)

Um fator muda decisão se, dentro da sua faixa:
1. o veredito não fica com um sinal só (`veredito_robusto` ≠ PUSH ou LOOSE puro), **ou**
2. a_y_lim ou Cα sai da banda heurística do EDR-071 (`banda_carro`/`banda_pneu` + `decidir`, como na A1-escolha).

Como cada fator aplica a regra (decisão do Claude depois da revisão do builder):
- **λ (LMUY, LFZO, LKY):** critério 1 pela robustez (`veredito_robusto`) da combinação 3×3×3 em cada pressão. Não
  há banda para λ: o Δa_y_lim do tornado é apresentado como tamanho de efeito, sem virar critério;
- **pressão:** critério 1 = o veredito difere entre as 4 pressões; critério 2 = `decidir` da A1-escolha (bandas
  LOO por nó, extremos como hoje) diz que as pressões se distinguem em a_y_lim ou em Cα. Banda `None` = "não
  avaliado", nunca "não muda";
- **KT:** critério 1 = o veredito difere entre as variantes a e b em alguma pressão; critério 2 = a diferença de
  a_y_lim entre a e b passa da banda da pressão daquele nó.

A banda é heurística e não é intervalo de confiança: o rótulo diz isso. Um "não muda" quer dizer
"não muda neste caso demonstrativo, nesta faixa exploratória", e o texto diz isso.

## 7. (b) Arrasto induzido

### 7.1 Fonte (conferida na imagem do PDF em 2026-11-12)

Milliken & Milliken, *RCVD*, §2.9:
- p. 64 e 65: T ou D = F_x·cos α − F_y·sen α; F_y·sen α é a componente de arrasto induzido (itens 1 a 3 da p. 65);
- p. 67, Fig. 2.36 (bicicleta, sem torque): D_induzido = F_yF·sen α_F + F_yR·sen α_R.

### 7.2 Cálculo

Para cada a_y de uma grade de 0 até o a_y_lim do caso (passo 0,1 g, curva à esquerda; a direita por `espelhar`), no R
do caso:
- α de cada eixo por `angulos_necessarios`; α e F_y de **cada roda** com o mesmo modelo que o equilíbrio usa (toe,
  Ackermann, camber e Fz limitados à faixa). Não há função pública que devolva F_y por roda; a chamada aos internos
  do `equilibrio` (Fz e γ limitados, deriva por roda, `tire_model.wheel_forces`) fica isolada numa única função, com
  um teste que confere que a soma das rodas de cada eixo iguala a F_y do eixo que `angulos_necessarios` resolveu;
- D = Σ_rodas F_y,i·sen |α_i| [N], que é também a energia por metro de curva [J/m];
- comparação: a forma de 1ª ordem do código (F_yf·|α_F| + F_yr·|α_R|, `fx_exigido_traseira` v43) e, se o caso tiver
  Crr com fonte, Crr·m·g. Sem Crr com fonte: "resistência ao rolamento a confirmar" e sem razão;
- D/(m·g), um coeficiente equivalente, só como apresentação.

Generalizar a bicicleta (2 rodas) do Milliken para 4 rodas, somando roda a roda, é escolha do Claude. A soma por roda é
a mesma projeção da p. 64 aplicada a cada roda. O texto do relatório diz isso.

### 7.3 Fx·κ

O Milliken não separa o termo de escorregamento longitudinal: na p. 65 ele o deixa junto da perda por deformação e diz
que os ensaios não conseguem separar os dois. Sem fonte conferida, o termo fica fora e aparece como "a confirmar". O
builder pode procurar uma fonte no Pacejka (`references/md/pacejka-txt/`). Se achar e conferir a equação na imagem,
traz para o usuário aprovar antes de usar. No caso de hoje, sem tração ligada (h9 desligada), F_x = 0 e o termo
seria nulo de qualquer forma.

### 7.4 Energia do enduro

Sem traçado não há energia total. O relatório dá D por condição (a_y, R) e diz que a energia é Σ D·comprimento de
cada trecho de curva, com o traçado "a confirmar".

## 8. Peças

| Arquivo | O que faz |
|---|---|
| `python/sensibilidade_pneu.py` | `caso_de_dados`, aplicação do `--set`, tornado, combinação, pressão, regra da §6.3, `arrasto_induzido`. Só lê os módulos protegidos |
| `tools/capturar_caso_pneu1.py` | captura única do JSON (§5.2) |
| `tools/relatorio_pneu1.py` | `--caso`, `--set`, `--rapido`, `--saida`; grava `build/pneu1/relatorio.md` e `build/pneu1/resultados.json` |
| `data/casos/caso_pneu1_demonstrativo.json` | o caso capturado (commit `dados:`) |
| `tests/test_sensibilidade_pneu.py` | testes no estilo do projeto (`check()`), com o `veiculo_base` sintético; os que precisam dos `.tir` saem NÃO EXECUTÁVEL sem eles |
| `docs/pneu/sensibilidade-e-arrasto.md` | relatório com os números do caso demonstrativo e a tabela por degrau |

Testes mínimos (o plano detalha):
- `caso_de_dados` reproduz o `veiculo_base` montado à mão; `--set` muda só a chave dada e marca a origem;
  chave desconhecida e entrada incoerente dão erro.
- Tornado com todos os λ = 1 dá o mesmo resultado do `analise_par` direto.
- Regra §6.3: casos construídos (só PUSH → não muda; PUSH e LOOSE → muda).
- `arrasto_induzido`: em a_y = 0, D = 0; D bate com a forma de 1ª ordem a menos de O(α³), conferido escalando os α
  (como o TC-FXI-001); com F_y e α dados à mão, a soma confere.
- Os módulos protegidos não mudam (`git diff` vazio neles, conferido no fim).

## 9. Rótulos obrigatórios em toda saída

- caso de outro carro (T09/E03), demonstrativo, não o T11; valores editados marcados;
- pneu R25B do TTC no lugar do R60A; μ absoluto do TTC não transferível;
- pressão de ensaio ≠ pressão fria nem quente (a confirmar);
- amplitudes de λ exploratórias (EDR-055), não faixa do pneu;
- banda heurística, não intervalo de confiança;
- Validation = NOT_VALIDATED; VERIFIED não é validado;
- Fx·κ fora (sem fonte); traçado do enduro a confirmar.

## 10. Riscos

- **O incremento 9 muda `equilibrio.py` e afins.** Este módulo os importa. Uma mudança de assinatura quebra os testes
  daqui, e é assim que vamos saber. Mitigação: usar funções públicas; onde precisar de uma privada (F_y por roda),
  isolar a chamada numa função só, com comentário.
- **A regra dos `res_` copiada errado.** Mitigação: o teste de equivalência da §5.4, uma vez.
- **Tempo da combinação completa** (27 × 4 pressões × `analise_par`): medir na primeira execução; `--rapido` existe
  para iterar.

## 11. Pendências do usuário

- Autorizar os IDs: um EDR para as decisões deste estudo (regra da §6.3, D com sen α roda a roda, caso em JSON) e
  os TC dos testes. Proposta: **EDR-075** (EDR-072 a EDR-074 estão reservados no plano do incremento 9,
  `docs/superpowers/plans/2026-11-11-inc9-v5-0-coerencia.md`) e o prefixo novo **TC-SEN-001** em diante (nenhum TC
  usa `SEN`). Até a autorização, o plano usa marcadores sem número.
- A origem do caso capturado: confirmar que é `◐ Dado de outro carro (TX, T09)` campo a campo (vem das colunas
  `org_` da V4.4).

## 12. O que fica para o builder

- A função pública que dá C_f e C_r.
- O formato exato do `resultados.json` e das tabelas do relatório.
- Os nomes internos e a divisão em funções.
