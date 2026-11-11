# Incremento 9: coerência completa, regras da competição e V5.0 — desenho

- **Data:** 2026-11-11
- **Entrada:** `docs/passagem-2026-11-11.md` (estado da V4.4, escopo previsto e pendências do inc. 8); spec do inc. 7
  (`docs/superpowers/specs/2026-10-29-inc7-fisica-planilha-design.md`, U1, U7, U9, §10 e §11); spec da V4.0
  (`docs/superpowers/specs/2026-10-20-v4-0-metas-equilibrio-design.md`, §4.4, §5 e §7.2); EDR-065, EDR-066 (item 5), EDR-069.
- **Decisões:** as marcadas "usuário" foram tomadas no brainstorming de 2026-11-11, na sessão do fechamento do inc. 8, depois
  de compactada. As marcadas "controlador" seguem a delegação do usuário (memória do projeto, 2026-10-22) e valem até a revisão
  desta spec.
- **IDs:** nenhum ID é criado por esta spec. A lista da seção 9 é proposta e vai ao passo do usuário entre a 9b e a 9c.

## 1. Decisões que este desenho segue

| # | Decisão | Quem | Data |
|---|---|---|---|
| D1 | Escopo da V5.0: as seis frentes da passagem (regulamento, física do K, coerência completa, retirada da chave 0, CA-07 contra a V4.4, entrada do T11 e triagem dos EDRs) mais as pendências do inc. 8, divididas em 9a, 9b e 9c | usuário | 2026-11-11 |
| D2 | O T11 compete na Formula SAE Brasil 2027. A fonte é o rascunho das FSAE Rules 2027 (SAE International), marcado como **provisório**, trocado pela versão final quando sair, com a troca registrada no EDR | usuário | 2026-11-11 |
| D3 | Física do K pelo caminho A: parcela de força de tração do Gillespie (p. 223-224, eq. 6-62 em diante), com o Fx do arrasto e da resistência ao rolamento e a perda de rigidez lateral do pneu em forma fechada; a forma da perda de rigidez sai de um estudo na 9b | usuário | 2026-11-11 |
| D4 | Desenho das partes 1 (9a e 9b) e 2 (9c, verificação, IDs, sessões) aprovado como apresentado | usuário | 2026-11-11 |
| D5 | A Formula SAE Brasil não tem regulamento próprio: usa as FSAE Rules da SAE International e publica um Addendum, um Handbook e um Dynamic Events Procedures. A fonte é o conjunto; o Addendum prevalece onde muda a regra base | controlador | 2026-11-11 |
| D6 | Efeito no objetivo em **segundos** (Δt do skidpad), nunca em pontos: a fórmula de pontos do skidpad usa T_min e T_max da prova, que não têm fonte. A hierarquia entre provas usa só os pontos máximos (fato do regulamento) | controlador | 2026-11-11 |
| D7 | Triagem dos EDRs em AWAITING_DECISION sem decidir nenhum: cada um recebe o dado que espera e o critério de reabertura; EDR-023 e EDR-036 (IDs) vão ao passo do usuário com recomendação | controlador | 2026-11-11 |

Decisões anteriores que continuam: chave 0 até a V5.0 (U9 do inc. 7); EDR-065 item 3 (planilha completa × Python completo:
só não inverter PUSH/LOOSE; tolerâncias a confirmar com o T11); diretriz do Drive (só a versão atual, conferida no navegador).

## 2. Escopo

**Dentro:**
1. Pendências do inc. 8: a branch do TC-WB43-005 e os minors do PR #37 (9a).
2. Regulamento: download, conversão, nota de fontes, conferência da D.10 (skidpad) contra a 24_CURVA, pontos por prova (9b).
3. Física do K: parcela de força de tração no oráculo e na planilha (9b, 9c).
4. Coerência completa das fichas de meta: efeito no objetivo, custo, malha fechada, ficha-exemplo (9b, 9c).
5. Retirada da chave 0 (h2v e h9v) no Python e na planilha (9b, 9c).
6. CA-07 por texto contra a V4.4 (9b ferramenta, 9c uso).
7. Entrada do T11: contador de entradas por Origem e roteiro de entrada (9b, 9c).
8. Triagem dos EDR-023, 024, 033, 036 e 040 (9b).
9. V5.0, suíte, PR, tag e troca da viva (9c).

**Fora:** pontos estimados por prova (falta T_min e T_max); a tolerância da escada (EDR-065 item 3; só com dados do T11);
decisão de qualquer EDR em AWAITING_DECISION; pneu combinado PAC2002 na planilha (caminho B, exige iteração e o EDR-008 proíbe
macro); MF 6.x (EDR-040); jacking (EDR-053); hardpoints reais (não existem).

## 3. Parte 9a: pendências do inc. 8

Sem mudança de engenharia; nenhum valor muda.

1. **TC-WB43-005 fora do Excel.** A branch `claude/adoring-morse-84a3d8` (commits ab2cb30, 3028748, 2b9cd26) parte do 7631be1.
   Traz a `main` (o `tools/rodar_testes.py` mudou no PR #37), resolve o conflito mantendo o `TIMEOUT_PLANILHAS` da `main`,
   roda `test_executor` e o `test_workbook_v4_3` nos dois motores e vira PR próprio (com o "sim" do usuário).
2. **Minors do PR #37**, em lotes por arquivo (lista na descrição do PR #37, seção Pendências):
   - T1 `argumentos_planilha(ref30=None)` gera "None";
   - T4/T5 linhas longas em `escada.py` e `equilibrio.py`;
   - T6 `test_skidpad` (só registro: a conversão LF já está feita);
   - T9 `guarda_h2_h2v` por substring (vira por chave);
   - T11 limites do Tokenizer na `reescrita_nomes` (espaço duplo, `_xlfn.`, maiúsculas, escopo de aba): documentar e testar;
   - T12/T15 SHA da V4.3 de `excel/` sem conferência contra a tag; `nomes_v4_4` importa funções privadas;
   - T13 pré-checagem de X2 a X5 sem conteúdo; `docProps/core.xml` não reproduzível (documentar);
   - T14 junções da linha `mig_ok`; comentário que cita `igual_ao_padrao`; `BaseException` que engole o Ctrl+C;
   - T16 `NAO_COBERTOS` obsoleto não detectado; cache de cobertura só pelo hash do layout;
   - T17 mutante identidade (vai para a mutação da V5.0, seção 6.4, e fica registrado aqui);
   - T18 parágrafo da 8a no registro não conferido item a item; `test_executor` (j) acoplado ao valor do limite.

   Minor que só faz sentido junto com a V5.0 passa para a 9c com o motivo no ledger.
3. Verificação: os testes afetados e o `test_executor`. A suíte inteira fica para a 9c.

## 4. Parte 9b: Python e fontes

### 4.1 Regulamento (D2, D5)

- **Documentos** (download só com o "sim" do usuário na hora, com nome, fonte e tamanho):
  - FSAE Rules 2027, rascunho para comentários (`fsaeonline.com`, DocumentID 9574fa97-c13e-4b90-9c75-044e30348cab);
  - FSAEB 2026 Rules Addendum V1.0, Handbook V2.1 e Dynamic Events Procedures (`arquivos.saebrasil.org.br/2026/Formula/`).
    A edição 2027 deles não saiu em 2026-11-11; a 2026 entra como provisória, declarada.
- PDFs e conversões ficam em `references/` (fora do Git, regra do CLAUDE.md); conversão para `.md` uma vez (docling ou
  markitdown). No Git entra só `docs/regulamento/fontes-2027.md`: documento, versão, data, regra usada e página, sem
  transcrever o texto além de citações curtas.
- **Conferências:**
  1. D.10 (skidpad): diâmetros, largura da faixa, posição dos cones. Compara com a 24_CURVA (B5, B6 e o método rente aos
     cones do `python/skidpad.py`). Fecha a condição pendente do EDR-069; divergência vira proposta de mudança para o passo do
     usuário, nunca correção direta.
  2. D.1.1 (pontos máximos por prova), com a confirmação no Addendum: dá a hierarquia entre objetivos (spec V4.0 §5 item 9).
     Nas Rules 2026, skidpad 75 de 675; o valor de 2027 se confere no rascunho.
  3. Fórmula de pontos do skidpad: registrada na nota como contexto do D6, não implementada.
- **Teste:** TC-REG (proposto) confere que todo valor de regulamento usado no código e na planilha tem linha na nota de fontes
  com documento e página.

### 4.2 Física do K (D3)

- **Oráculo:** função nova em `python/equilibrio_linear.py` (nome no plano) com a parcela de força de tração do Gillespie
  (p. 223-224; equações conferidas na imagem do PDF, regra do CLAUDE.md). O Fx vem de: arrasto aerodinâmico (½·ρ·CdA·V², com
  V² = a_y·R) e resistência ao rolamento (Crr·W), na roda motriz traseira (RWD, motor no chassi atrás; a confirmar para o T11).
  Entradas novas (CdA, Crr) e a existente ρ ficam "a confirmar", com Origem.
- **Estudo** (`docs/inc9/estudo-k-tracao.md`): duas formas para a perda de rigidez lateral do pneu com o Fx: (i) só o termo
  do Gillespie p. 223-224; (ii) com a perda de rigidez em forma fechada (Gillespie p. 299, ou elipse de atrito). Compara as
  duas com a linha `todas` da escada (`docs/inc6/escada-caso-sintetico.md`) no caso sintético, e a linha `planilha V4.3`
  (ΔK = +1,57 °/g) como ponto de partida. Critério: a forma não inverte o veredito (EDR-065 item 3) e, entre as que passam,
  a mais próxima do Python completo, com a mais simples em empate (regra "decidir quando uma opção domina"). O ΔK restante é
  registrado como informação, sem tolerância.
- O rótulo do K muda de "sem compliance, torque de alinhamento e tração" para "sem compliance e torque de alinhamento; tração
  por aproximação (Gillespie p. 223-224)".

### 4.3 Coerência completa (spec V4.0 §4.4 e §5)

O estado de coerência de cada ficha (`metas.estado_coerencia`) ganha três regras, na ordem de precedência abaixo das
existentes (vocabulário, sobredeterminação, TBD):

1. **Malha fechada (item 6):** campo novo na ficha, "valor real do setup" (mola de catálogo, barra disponível). Preenchido:
   o valor volta ao modelo direto e a ficha mostra o resíduo (grandeza resultante com o valor real menos o target); fora da
   tolerância numérica é CONFLITO com motivo "resíduo da malha fechada". Vazio: NÃO AVALIÁVEL ("sem valor real do setup").
   COERENTE só com o resíduo dentro da tolerância numérica (definição da §4.4).
2. **Custo (itens 1c, 4 e 5):** o custo do comportamento já calculado na 20_EQ_TROCA entra no estado das fichas de
   equilíbrio. Custo positivo sem EDR: CONFLITO ("custo sem justificativa"); com EDR aprovado: COMPROMISSO DECLARADO. O
   limiar continua só por EDR ("limiar não definido").
3. **Efeito no objetivo (D6):** cada ficha de equilíbrio mostra o Δt do skidpad do acerto atual em relação ao acerto neutro,
   em segundos, com o R da 24_CURVA. Informativo: não muda o estado.

A tolerância numérica do resíduo é medida (resolução do modelo), não escolhida; o plano define como medir.
Ficha-exemplo: `docs/metas/ficha-exemplo.md`, didática, rotulada DEMONSTRATIVA, preenchida com a TARGET-003 (λ_f), mostrando
os quatro estados.

### 4.4 Retirada da chave 0 no Python

Saem as formas antigas do Ackermann e do Fx exigido: `FORMAS_V42` e o parâmetro `formas` de `equilibrio_linear.parcelas_k`
(padrão hoje `FORMAS_V42`) e das funções que o recebem; as entradas de `mmm.VARIANTES` para h2v e h9v ficam com uma só forma;
a linha "planilha V4.2" da escada e os testes que só existiam para ela (`test_formas_v43` muda para conferir a forma única).
O relatório `docs/inc6/escada-hipoteses.md` é regenerado. A tag `v4.2` guarda a forma antiga.

### 4.5 CA-07 por texto contra a V4.4

Ferramenta (módulo no plano) que lê a V4.4 da tag `v4.4` (SHA conferido contra a tag, minor T12) e a V5.0 gerada, e
reprova toda célula com texto diferente que não esteja no catálogo de mudanças da V5.0. É a forma do CA-07 que valeu até a
V4.2, agora contra a V4.4 (registro da V4.4).

### 4.6 Entrada do T11

- Contador por Origem: quantas células de entrada estão em cada Origem (T11, outro carro, estimativa, etc.), calculado no
  oráculo a partir de `atualizar_planilha.celulas_de_entrada()` e dos nomes de dado.
- Roteiro de entrada: seção nova do LEIA-ME (ordem sugerida: massa e geometria, pneu, mola e barra, aero), sem valores.

### 4.7 Triagem dos EDRs

| EDR | Aguarda | Critério de reabertura |
|---|---|---|
| 023 (SUS-407 a 413) | Decisão de IDs pelo usuário | Passo do usuário (recomendação pronta) |
| 024 (schema de hardpoints) | Primeira importação real do CAD | Export do OptimumKinematics ou do Fusion do T11 |
| 033 (AD/AS e anti-lift) | Dados de trem de força e freio do T11 | Split hidráulico/regenerativo definido |
| 036 (IDs de camber/toe estáticos) | EDR-023 resolvido | Passo do usuário |
| 040 (formato do pneu) | Dataset real e escolha do formato | Pneu do T11 escolhido |

Texto acrescentado ao corpo de cada um, sem mudar o status.

### 4.8 Saída da 9b

Relatório para o passo do usuário (`docs/inc9/passo-usuario.md`): fórmulas novas e alteradas célula a célula (aba, célula,
fórmula anterior, nova, dependências, justificativa, teste), a escolha do estudo do K, a conferência da D.10, a lista de
IDs propostos e as recomendações para EDR-023 e EDR-036.

## 5. Parte 9c: V5.0

1. `python/gerar_v5_0.py` gera a V5.0 da tag `v4.4` em `build/` (nunca em `excel/`; cópia para `excel/` em commit próprio).
2. Mudanças (só as aprovadas no passo):
   - 24_CURVA: saem B9 e B10 (chaves); as fórmulas do Ackermann e do Fx ficam na forma única; diâmetros e cones citam a D.10
     do rascunho 2027 (provisório);
   - 16_EQUILIBRIO: parcela de tração no K, entradas CdA e Crr com Origem e Fonte; F188 diz qual aproximação foi usada;
   - 03_TARGETS: campo do valor real do setup, resíduo, efeito no objetivo e o estado de coerência com as regras novas;
   - 14_DASHBOARD: contador por Origem, hierarquia por pontos máximos (com fonte), B48 revisto;
   - 00_README, 15_CHANGELOG.
3. Toda fórmula nova lê por nome (regra da V4.4); nomes novos em `data/nomes_V5_0.csv`.
4. Catálogo gerado `docs/registro-de-versoes-V5_0-celulas.md` (nunca editado à mão); `docs/registro-de-versoes-V5_0.md`; EDRs.
5. Suíte inteira nos dois motores (cerca de 3h40 cada, em segundo plano); limite do `test_workbook_v5_0` começa em 7200 s.
6. PR, tag `v5.0` e troca da viva, cada um com o "sim" do usuário. A troca segue `conferir_viva` (código 0) e
   `migrar_viva`; o Drive fica só com a V5.0 e os documentos; conferido no navegador.

## 6. Verificação

1. **CA-07 por texto (4.5):** 0 diferença fora do catálogo.
2. **Regeneração:** V5.0 regenerada da tag `v4.4`, 0 diferença contra `excel/`.
3. **Equivalência por valor com o oráculo** (TC-WB50, proposto; Excel via COM ou LibreOffice, casos sintéticos rotulados):
   K com a parcela de tração = função Python; estado de coerência = `metas.py`; contador por Origem = oráculo; nos casos com
   h2v = h9v = 1 (o padrão), toda célula fora do catálogo tem o mesmo valor da V4.4.
4. **Mutação da planilha V5.0:** um mutante por regra nova (parcela de tração, malha fechada, custo, contador) e o mutante
   identidade (minor T17), que precisa sobreviver.
5. **Escada:** a linha da planilha V5.0 não inverte o veredito contra `todas`; ΔK registrado.
6. Testes do Python afetados pela retirada da chave 0 e pela coerência, com as contagens novas no CLAUDE.md.

## 7. Arquitetura (unidades e dependências)

- `python/equilibrio_linear.py`: parcela de tração (oráculo do K). Depende do `.tir` em uso e das entradas da 16.
- `python/metas.py`: regras novas do estado de coerência; sem dependência da planilha.
- `python/aba_metas.py`, `python/aba_equilibrio.py`, `python/aba_curva.py`: fórmulas da planilha a partir do oráculo, como já
  fazem; a V5.0 as chama pelo gerador.
- `python/gerar_v5_0.py`: compõe a V5.0 a partir da V4.4; nada mais lê a V4.4 por endereço.
- Ferramenta do CA-07 (4.5): independente do gerador, para não conferir o gerador com ele mesmo.

## 8. Ordem e sessões

1. **9a** (sessão nova, Sonnet): pode rodar em paralelo com a 9b, porque mexe em arquivos de teste e de ferramentas que a 9b
   não toca no começo; o plano lista os arquivos de cada uma e a ordem de merge (9a antes da 9c).
2. **9b** (uma ou duas sessões: o estudo do K pode ficar sozinho; Opus no estudo do K e na coerência, Sonnet no resto).
3. **Passo do usuário:** aprovação das fórmulas e dos IDs.
4. **9c** (uma sessão para a geração e os testes; a suíte e a troca da viva podem ir a uma segunda).

## 9. IDs propostos (nenhum criado)

| Tipo | ID | Para quê |
|---|---|---|
| EDR | EDR-071 | Física do K: parcela de tração e escolha do estudo |
| EDR | EDR-072 | Coerência completa: malha fechada, custo, efeito no objetivo |
| EDR | EDR-073 | Regulamento 2027 provisório; fecha a condição do EDR-069 |
| EDR | EDR-074 | V5.0: retirada da chave 0 e CA-07 contra a V4.4 |
| SUS | SUS-1012 a SUS-1015 (aprox.) | Parcela de tração, resíduo da malha fechada, efeito no objetivo, contador por Origem |
| TC | TC-REG-001 em diante | Fontes do regulamento |
| TC | TC-WB50-001 em diante | Estrutura, CA-07, regeneração, equivalência, cobertura e mutação da V5.0 |

## 10. Riscos e limitações

- O rascunho de 2027 pode mudar a D.10 ou os pontos; o EDR-073 tem o critério de reabertura (versão final publicada).
- O caminho A é aproximação; a diferença para o Python completo fica como informação até haver dados do T11.
- A tração na roda traseira (RWD) e o motor no chassi atrás vêm de 2026-10-19, antes do T11 ser informado: a confirmar.
- A malha fechada sem valor real do setup dá NÃO AVALIÁVEL em todas as fichas enquanto não houver catálogo de mola e barra.
- A suíte cresce com a V5.0; o tempo real se mede na 9c.
- Validation continua NOT_VALIDATED: "passou" quer dizer que a planilha reproduz o oráculo, não validação física.
