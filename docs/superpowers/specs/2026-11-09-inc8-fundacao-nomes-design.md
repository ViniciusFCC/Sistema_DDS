# Incremento 8: pendências do inc. 7 e fundação parte 2 (V4.4) — desenho

- **Data:** 2026-11-09
- **Entrada:** `docs/passagem-2026-11-09.md` (13 pendências do inc. 7) e o roteiro da spec do inc. 7
  (`docs/superpowers/specs/2026-10-29-inc7-fisica-planilha-design.md`, §10, U1).
- **Decisões:** todas as marcadas "usuário" foram tomadas no brainstorming de 2026-11-09. As marcadas "controlador" foram
  tomadas depois que o usuário pediu, no mesmo dia, que o trabalho seguisse sem interrupção, com as decisões informadas; elas
  valem até a revisão desta spec.
- **IDs autorizados (usuário, 2026-11-09):** EDR-070 e TC-WB44-001 a TC-WB44-006. Nenhum outro ID nasce neste incremento.

## 1. Objetivo e escopo

O incremento 8 tem duas partes, nesta ordem:

- **8a — pendências 1 a 12 do inc. 7.** Só Python e documentação; nenhuma planilha nova sai da 8a. Item da 8a que, no
  plano, se mostrar mudança de célula da planilha passa para a lista de exceções da 8b (§3.4) e é aprovado lá (decisão do
  controlador; hoje isso vale para a pendência 6 e pode valer para a guarda da B28 da pendência 8).
- **8b — fundação parte 2 (V4.4).** As fórmulas das abas 03 a 14 passam a ler por nome toda célula única; a equivalência por
  valor V4.3 → V4.4 substitui o CA-07 por texto contra a versão anterior. Os valores calculados não mudam.
- **Pendência 13 (achado do K)** entra como declaração de limitação (§5), sem física nova.

Fora do escopo (alternativas mostradas e recusadas pelo usuário): a física das hipóteses 10 e 9b na planilha, os itens do
inc. 9 (V5.0, coerência completa), os abertos do §11 do inc. 7, os EDRs em AWAITING_DECISION e a preparação da entrada do
T11. As abas 16 a 20d ficam fora da reescrita: já leem as entradas por nome, e as grades usam endereço relativo interno
(por exemplo `MIN(DK25:DK64)`), que não é o alvo da fundação.

Por que agora: a decisão D13 da spec da V4.0 pede a reescrita **antes** do preenchimento da equipe. A viva V4.3 do Drive
ainda não tem dados (`migrar_viva` com 0 dados em 2026-11-09). Depois que a equipe preencher, cada troca de versão passa a
carregar dados, e a reescrita fica mais cara de provar.

## 2. Versão e viva

- A planilha da 8b é a **V4.4** (usuário). A V5.0 continua reservada ao inc. 9.
- A V4.4 sai de `python/gerar_v4_4.py`, a partir da tag `v4.3`, em `build/`; a cópia para `excel/` é um commit próprio, como
  nas versões anteriores.
- No fechamento, a viva do Drive vira a V4.4 pela diretriz de 2026-10-23: `conferir_viva` (código 0) antes, `migrar_viva`
  por nome para a V4.4, conflito listado e nunca sobrescrito, e a confirmação do usuário antes de qualquer gravação no
  Drive. Se a equipe tiver preenchido a V4.3 até lá, os dados são levados por nome; o TC-WB44-004 garante que os nomes de
  entrada não mudam de célula.

## 3. Reescrita para nomes (8b)

### 3.1 Medição na V4.3 (2026-11-09)

Feita com o `Tokenizer` do openpyxl sobre `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`; o plano refaz a medição como passo
próprio.

- Abas 03 a 14: 454 fórmulas e 2862 referências; 2664 (93 %) já são por nome e 198 não.
- As 198 sem nome: 10_TIRE 118 (blocos do `.tir`, como `'10_TIRE'!B168:B175`), 03_TARGETS 55 (linha própria da ficha,
  como `A5`), 23_LISTAS 14 (listas, como `D43:D52`), 13_VALIDATION 6 (`B37` e vizinhas), 16_EQUILIBRIO 3 (`E188` e
  vizinhas), `'02_REQUIREMENTS'!A:A` 1 e `'04_DECISION_REGISTER'!A:A` 1.
- 1266 nomes definidos, todos de escopo da pasta (nenhum local de aba); nenhuma célula tem mais de um nome.
- Nenhuma função volátil ou indireta (`NOW`, `TODAY`, `RAND`, `RANDBETWEEN`, `OFFSET`, `INDIRECT`, `CELL`, `INFO`) em
  nenhuma aba.
- Ramos nas abas 03 a 14: 462 `IF` e 350 `IFERROR`; nenhum `CHOOSE`, `IFS` ou `SWITCH`.

### 3.2 Cobertura de nomes: opção (C) reduzida (usuário)

- Ganham nome novo só as **9 células soltas**: 13_VALIDATION `B37` e vizinhas (6) e 16_EQUILIBRIO `E188` e vizinhas (3).
  Os nomes vão para `data/nomes_V4_4.csv`, com as regras do EDR-058 e o mesmo cabeçalho das tabelas anteriores
  (`nome,aba,celula,papel,sus_id,rotulo`). Cada nome é aprovado pelo usuário no plano.
- Ficam por endereço: intervalos (blocos do `.tir` e listas da 23_LISTAS), a linha própria das fichas da 03_TARGETS e as
  colunas inteiras.

### 3.3 Regra da troca

A regra que o usuário aprova uma vez (opção (C) da aprovação, usuário):

> Numa fórmula das abas 03 a 14, cada operando que é referência a **uma célula** (com ou sem aba, com ou sem `$`) e que é
> o destino exato de um nome definido é trocado por esse nome. Nada mais muda no texto da fórmula.

Detalhes que o gerador segue (controlador):

- A conversão é mecânica, pelo leitor de `python/raizes.py` (`REF`, `nomes_definidos`), sobre os tokens OPERAND/RANGE do
  `Tokenizer`. Texto entre aspas, nomes de função e operadores nunca são tocados.
- Destino ambíguo (dois nomes na mesma célula) para o gerador com erro. A medição de 3.1 diz que hoje não há nenhum; o erro
  existe para que um nome novo futuro não escolha em silêncio.
- Referência a intervalo, coluna inteira ou linha própria da 03_TARGETS não é tocada, mesmo que um nome aponte para o
  intervalo inteiro. Trocar intervalo por nome fica fora desta spec.
- `$` deixa de importar: o nome é absoluto. Como cada célula do `.xlsx` guarda a própria fórmula, isso não muda valor; só
  muda o comportamento se alguém copiar a fórmula à mão para outra célula, o que a regra do projeto já proíbe (mudança de
  fórmula entra pelo gerador).
- O gerador escreve um catálogo de todas as células reescritas (aba, célula, fórmula da V4.3, fórmula da V4.4) em
  `docs/registro-de-versoes-V4_4-celulas.md`, para consulta e conferência por amostragem. O catálogo é gerado, nunca
  editado à mão.

### 3.4 Exceções aprovadas uma a uma

Toda mudança que não seja a troca pura de 3.3 fica numa lista curta (`alteracoes()` do gerador, como no
`atualizar_planilha.py`), com aba, célula, conteúdo anterior, conteúdo novo, motivo e EDR. Cada item é aprovado pelo usuário
no plano. Itens previstos:

1. As células que passam a ler as 9 células soltas pelos nomes novos (a troca é a da regra, mas o nome não existia na V4.3).
2. A célula de texto da limitação do K (§5).
3. A pendência 6 (`aba_curva.TEXTO_B48`, texto fixo "diâmetros do regulamento FSAE 2026 D.10.1.1" mesmo quando B5/B6 são
   editados), se o plano confirmar que a correção muda a célula.
4. A guarda da B28 da 24_CURVA (pendência 8), se o plano confirmar que muda a célula.
5. Os textos de versão: 00_README A3 e a linha nova do 15_CHANGELOG, como nas versões anteriores.

Qualquer outra diferença que o teste de texto (TC-WB44-002) encontrar é FAIL, nunca uma exceção acrescentada depois sem
aprovação.

### 3.5 Invariante dos nomes

> Nas abas 03 a 14 da V4.4, toda referência a célula única é por nome. Por endereço sobram só intervalo, coluna inteira e,
> na 03_TARGETS, referência à própria linha da ficha.

O TC-WB44-003 confere o invariante. A "linha própria" é definida no teste como referência sem aba, na mesma linha da célula
que contém a fórmula, quando essa célula está na faixa das fichas da 03_TARGETS (H:Q, como na V4.2). O plano confere, na
medição refeita, que as 55 referências de 3.1 cabem nessa definição; se alguma não couber, ela vira nome novo com aprovação
ou exceção, nunca uma folga no invariante.

## 4. Verificação da V4.4 no lugar do CA-07 por texto

### 4.1 O que acontece com o CA-07 (usuário)

- **V3.0 a V4.3:** nada muda. Os testes dessas versões continuam como estão (por texto ou por SHA). São referências
  congeladas.
- **V4.4:** três verificações:
  1. **Regeneração por texto:** `gerar_v4_4` da tag `v4.3` bate com `excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx`, 0
     diferença (TC-WB44-001). É a parte do CA-07 que continua valendo.
  2. **V4.3 → V4.4 pela regra e pelo valor:** teste de texto da regra com as exceções aprovadas (TC-WB44-002) e
     equivalência por valor (TC-WB44-005 e 006).
  3. **Invariante dos nomes** (TC-WB44-003).
- **V4.5 em diante:** o CA-07 por texto volta ao normal, contra a V4.4. A equivalência por valor fica disponível para as
  versões em que a física muda (como a V5.0), sem obrigação nesta spec.

### 4.2 Teste de texto da regra (TC-WB44-002)

Para cada célula das abas 03 a 14, tokeniza a fórmula da V4.3 e a da V4.4 e alinha os tokens. Passa quando a única diferença
é operando de célula única → nome cujo destino é exatamente aquela célula, ou quando a célula está na lista de exceções com
o conteúdo novo aprovado. Fora das abas 03 a 14, toda célula é igual à da V4.3, salvo as exceções.

### 4.3 Equivalência por valor (TC-WB44-005; usuário)

- **Motor:** Excel via COM, com o LibreOffice de reserva (EDR-044; `DDS_RECALC` força um). As duas planilhas rodam sempre no
  mesmo motor, em cópias em `build/`. A viva e a referência nunca são recalculadas nem salvas; no LibreOffice, só cópias.
- **Tolerância zero:** números, textos, booleanos e erros idênticos em todas as células de todas as abas. Diferença é FAIL e
  se investiga; o critério nunca é afrouxado. A ausência de funções voláteis (3.1) é o que permite tolerância zero sem
  exceções; o teste confere de novo que não há nenhuma e falha se aparecer.
- **Casos:**
  1. o nominal (os valores que já estão na planilha, demonstrativos);
  2. N casos perturbados: cada entrada numérica com nome (papel `ent` nas tabelas de nomes) sorteada numa faixa em torno do
     valor atual (±20 %; o sinal é mantido; entrada inteira continua inteira), com semente fixa; entradas de lista só com
     opções válidas da lista. Esses valores são **sintéticos de teste**, rotulados assim no log, e nunca dado do carro.
     Entrada vazia na V4.3 continua vazia nos casos perturbados (decisão do controlador: preencher uma entrada vazia seria
     inventar um valor que a planilha não tem);
  3. casos dirigidos, se a cobertura (4.4) mostrar ramo descoberto.
- **N** sai da medição do tempo de recálculo da V4.3 no Excel, feita no plano (`tools/medir_recalculo.py` como base). O
  plano registra o tempo medido e o N escolhido.
- **Prova de que o teste reprova:** `tests/mutation_planilha_v44.py` (sem TC, no padrão das outras mutações) altera uma
  fórmula numa cópia da V4.4 por mutante e exige que o TC-WB44-005 falhe. Mutantes previstos: trocar um nome por outro de
  mesmo papel, trocar um nome pelo endereço de uma célula vizinha, inverter um operador num ramo pouco usado de `IF` e
  trocar uma constante. O plano fixa a lista.

### 4.4 Cobertura de ramos (TC-WB44-006)

- Para cada `IF` das abas 03 a 14, o teste registra, em cada caso, se a condição deu verdadeiro ou falso; para cada
  `IFERROR`, se o primeiro argumento deu erro ou não.
- Como medir (controlador): numa cópia da V4.3 em `build/`, uma aba auxiliar recebe, para cada ramo, uma célula com a
  condição do ramo **e** a condição do caminho (conjunção das condições dos `IF` externos que levam a ele), extraídas pelo
  tokenizador. Sem a condição do caminho, um `IF` aninhado contaria como coberto um ramo que nunca é alcançado. A aba
  auxiliar só existe nessa cópia de teste.
- Passa quando todo ramo é coberto por algum caso ou está na lista aprovada de não cobertos, com o motivo (por exemplo, um
  `IFERROR` cujo erro só ocorre com entrada inválida). Ramo descoberto que não está na lista vira caso dirigido no plano ou
  entra na lista com aprovação.

### 4.5 Migração (TC-WB44-004)

Todo nome com papel `ent` (e os de origem e fonte) da V4.3 existe na V4.4 com o mesmo destino. `tools/migrar_viva.py` com uma
cópia da V4.3 com dados sintéticos rotulados leva todos os dados para a V4.4 com 0 conflitos.

## 5. Limitação do K (pendência 13; opção (B), usuário)

- **Achado:** no caso sintético da escada (`docs/inc6/escada-caso-sintetico.md`), o K da planilha não representa as
  hipóteses 10 (arrasto e resistência ao rolamento) e 9b (Fx exigido pelo balanço completo): ΔK de +1,57 °/g contra a linha
  `todas`. O caso é sintético e, nele, o pneu sai da faixa do `.tir` em algumas linhas.
- **Decisão:** declarar a limitação, sem física nova (a física nova é escopo da V5.0 e quebraria a equivalência da 8b).
  - Item novo nas limitações do **EDR-066** ("Achados da escada sobre fórmulas da planilha"), o registro que trata das
    fórmulas da planilha que a escada examinou (decisão do controlador entre o 065 e o 066).
  - Linha no registro de versões da V4.4.
  - Frase curta na célula de texto ao lado do K na planilha, como exceção de 3.4: o K não inclui arrasto, resistência ao
    rolamento nem o Fx exigido completo; efeito medido num caso sintético: +1,57 °/g; a confirmar com o T11. O plano localiza
    a célula e traz o texto exato para aprovação. Célula de texto não entra em conta, então não afeta a equivalência por
    valor (os dois textos diferem, e o TC-WB44-002 aceita a diferença só porque ela está aprovada).
- A tolerância numérica de T, C_N e K (EDR-065 item 3) continua a confirmar com dados do T11.

## 6. Parte 8a: tratamento das pendências 1 a 12

| # | Pendência | Tratamento |
|---|---|---|
| 1 | Suíte no LibreOffice | Na suíte única do fim do incremento (§7), com `DDS_RECALC=libreoffice` nos itens de planilha |
| 2 | Item "planilha vs V4.3 de referência" da suíte | Na suíte única do fim do incremento (§7) |
| 3 | Laços MUTACAO e PLANILHAS do `main()` sem teste | Extrair para funções e testar como o laço de TESTES no TC-RUN-001, como novos checks do TC-RUN-001 (sem ID novo) |
| 4 | Critério do FORMAS_V43 em `tests/test_equilibrio_linear.py` ~277-283 | Dividir o erro pela soma dos termos, não pelo maior; rodar o teste |
| 5 | `--saida` redirecionado em silêncio no `--caso-sintetico` | Recusar com mensagem e código diferente de 0 (decisão do controlador: avisar e seguir esconderia o erro do mesmo jeito num log longo) |
| 6 | `aba_curva.TEXTO_B48` fixo | Vai para a lista de exceções da 8b (§3.4), porque é texto de célula |
| 7 | Higiene (`modulos_locais`, docstring de `gerar_v4_3.aplicar`, linhas > 120 colunas) | Commit próprio de higiene, sem mudança de comportamento |
| 8 | Minors das Tasks 4 a 7, regex da 17, guarda da B28, regerar `docs/inc6/escada-hipoteses.md` | Um commit por tarefa de origem; a guarda da B28 vai para a 8b se mudar célula; a regeneração do relatório avisa no commit |
| 9 | Parágrafo da V4.3 em Comandos do CLAUDE.md | Escrever no padrão do parágrafo da V4.2 |
| 10 | Status do EDR-064 | Índice (linhas 103 e 119) e CLAUDE.md passam a APPROVED, igual ao corpo (usuário). VERIFIED só na suíte única do fim do incremento |
| 11 | §4.1 da spec do inc. 7 | Citar a forma exata atan(L·t/(R_c² + L² − t²/4)) e o limite de validade da aproximação |
| 12 | Sumário dos `.docx` e auditoria humanizer-pt do LEIA-ME | Rodar a auditoria no LEIA-ME; os `.docx` são gerados de novo no fechamento da V4.4, com o aviso de atualizar os campos no Word |

## 7. Suíte inteira: uma só, no fim

Decisão do usuário (2026-11-09): nenhuma suíte inteira só para promover o EDR-064. Consequência (controlador): a 8a e a 8b
rodam só os testes afetados por cada mudança; **uma** suíte inteira, sem `--pular-recentes`, roda no fim do incremento 8,
depois da 8b, no Excel e no LibreOffice. Essa rodada cobre as pendências 1 e 2, a V4.4 e a promoção do EDR-064 a VERIFIED,
e vira o log de evidência do incremento (`docs/migracao/<novo>.md`, numa árvore sem mudanças pendentes).

## 8. EDR-070 (conteúdo previsto)

Fundação parte 2: a V4.4; a reescrita para nomes nas abas 03 a 14 (regra de 3.3, cobertura (C) reduzida de 3.2); a aprovação
por regra com exceções (3.4); o invariante (3.5); a verificação da V4.4 no lugar do CA-07 contra a versão anterior (§4); e a
suíte única do fim (§7). Alternativas registradas: cobertura total de nomes (intervalos e listas), aprovação célula a
célula, equivalência só no caso nominal e reescrita das abas 16 a 20d.

## 9. Testes e contagens previstas

| ID | Arquivo | O que confere |
|---|---|---|
| TC-WB44-001 | `tests/test_v4_4.py` | Estrutura e regeneração da tag `v4.3`: 0 diferença de texto contra `excel/` |
| TC-WB44-002 | `tests/test_v4_4.py` | Regra da troca e exceções aprovadas (4.2) |
| TC-WB44-003 | `tests/test_v4_4.py` | Invariante dos nomes (3.5) |
| TC-WB44-004 | `tests/test_v4_4.py` | Migração por nome (4.5) |
| TC-WB44-005 | `tests/test_workbook_v4_4.py` | Equivalência por valor, tolerância zero (4.3) |
| TC-WB44-006 | `tests/test_workbook_v4_4.py` | Cobertura de ramos (4.4) |

Esperado: `test_v4_4` 4/4, `test_workbook_v4_4` 2/2 (Excel ou LibreOffice; sem nenhum dos dois, NÃO EXECUTÁVEL),
`mutation_planilha_v44` com todos os mutantes mortos. Os itens novos entram em `tools/rodar_testes.py` com as dependências
declaradas em `DEPENDENCIAS`.

## 10. Riscos e limitações

- **Cobertura não é prova.** A equivalência por valor com casos sorteados mostra igualdade nos pontos testados; a prova de
  que a troca não muda nada é o teste de texto (4.2). As duas juntas são o critério; nenhuma substitui a outra.
- **Tempo de recálculo.** A V4.3 tem 146373 fórmulas. Se o tempo por caso for alto, N fica pequeno, e a cobertura (4.4) passa
  a depender mais dos casos dirigidos.
- **Faixa de ±20 %** pode levar o pneu para fora da faixa do `.tir` ou produzir erros na planilha. Erro igual nas duas versões
  é equivalência válida; o log conta quantas células deram erro por caso, para que um caso "todo erro" não passe como prova.
- **Textos citando versões antigas.** Docstrings e textos de células que citam nomes `_V2_x` continuam como estão (CLAUDE.md).

## 11. Ordem de execução prevista

1. 8a: pendências 3, 4, 5, 7, 8 (o que não muda célula), 9, 10, 11 e 12, um commit por propósito, testes afetados em cada um.
2. 8b: medição refeita; tabela `data/nomes_V4_4.csv` com os 9 nomes para aprovação; gerador com a regra e as exceções;
   catálogo de células; TC-WB44-001 a 004; medição do tempo de recálculo e N; TC-WB44-005 e 006; mutação.
3. Cópia da V4.4 para `excel/` (commit próprio), registro de versões, EDR-070, item do EDR-066 e CLAUDE.md.
4. Suíte única (§7) e promoção do EDR-064.
5. Fechamento: troca da viva do Drive (com confirmação do usuário), `.docx`, PR, merge e tag `v4.4`, cada um com a confirmação
   do usuário.
