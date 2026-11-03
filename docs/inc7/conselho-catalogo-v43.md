# Conselho sobre o catálogo de células da V4.3 (2026-11-02)

Consulta feita antes da aprovação célula a célula do catálogo (plano do inc. 7, seção "Catálogo das células da V4.3").
Nível padrão, 4 assentos e 1 rodada de revisão anônima. Nenhum valor numérico novo entra por este documento.

## Veredito do Conselho
O conselho foi unânime: **aprovar com ajustes**. Nenhum conselheiro reabre a física decidida (D1 a D10, EDR-066,
EDR-069). O Ackermann (C-C), o Fx v43 (C-G) e as contas do R (C-A9 a C-A13) conferem termo a termo com o Python,
inclusive no sinal, e o desenho não tem referência circular. Os defeitos aparecem fora do caminho feliz:
- geometria impossível dá #VALUE!/#DIV/0! na planilha, onde o Python dá N/A com motivo;
- modo do R, chave ou diâmetro inválido passa sem aviso;
- células que leem o B9 ficaram fora do catálogo;
- a aba 19 muda sem que o Python acompanhe;
- a migração perderia o R digitado;
- a regra do 4/3 tem duas leituras e quebra o TC-WB43-003.

Três pontos dependem do usuário (ver "Decisões pendentes").

## Ajustes ao catálogo (sem decisão nova; aplicar antes da 7b)
1. **C-A6/C-A7 (chaves h2v, h9v):** lista `"0,1"`, como as chaves existentes (`python/aba_equilibrio.py:1121`), com o
   significado na coluna F. A redação atual sugere uma lista de textos. **C-A8** passa a testar com `ISNUMBER` e entra nas
   `VERIFICACOES` da 16, como "chave h2 deve ser 0 ou 1" (`aba_equilibrio.py:242`). Assim uma chave vazia ou inválida
   não vira 0 em silêncio.
2. **C-A14/C-A15 (R usado e motivo):** o ramo "Rente aos cones" fica explícito (`EXACT(modo,"Rente aos cones")`) e
   qualquer outro modo dá `""`. O motivo testa primeiro o modo inválido, para não cair no rente em silêncio
   (`skidpad.raio` levanta ValueError, `python/skidpad.py:84`).
3. **C-A9 a C-A12 e C-A16 (contas do R):** guarda `ISNUMBER` em `dint`, `dext`, `tF`, `L` e `b`, com `dext > dint > 0`
   e o motivo "diâmetros a confirmar". A C-A16 aninha os IF: R vazio dá "-", e R ≤ b dá a mensagem própria.
   Validação "positivo" em B5, B6 e B8.
4. **C-A18 e C-C1/C-C2 (θ e Δα):** θ só com `ISNUMBER(rcc)`, `rcc > tF/2` e `h2v = 1`; θ̄ (B25) com guarda.
   Nova verificação "geometria do centro da curva inválida (R ≤ b ou R_c ≤ t_f/2)", condicionada a h2 = 1 e h2v = 1,
   que leva `ok` a 0 antes da B114. O texto é o do Python (`python/equilibrio.py:280-286`). O mesmo item entra em
   `motivo_das_entradas`.
5. **C-B4 e a nova C-B7 (`tvolta`, `aba_equilibrio.py:752-754`):** o B9 vira fórmula. Por isso os leitores testam,
   nesta ordem, `ISNUMBER`, `ISERROR` e `=""`, e não mais `ISBLANK`. A C-A14 é envolvida em `IFERROR(…,"")`. Em par,
   `motivo_das_entradas` (`aba_equilibrio.py:283-287`) passa a tratar `""` como vazio.
6. **B9 na 16 (D4):** estilo de resultado no lugar do estilo de entrada, sem a validação numérica
   (`aba_equilibrio.py:1052`). Rótulo A9 "R usado (fórmula; ver 24_CURVA)" e F9 "Não digite aqui: o R manual fica em
   24_CURVA B8".
7. **Migração e nomes:** regra única em `dados_planilha.eh_dado`/`_destinos`: um nome `ent_`/`org_` cuja célula é
   fórmula na versão de destino não é dado (`python/dados_planilha.py:35-37`, `:113-136`). No `migrar_viva`, B9 → 24_CURVA
   B8 com o modo "Manual", e E9 → 24_CURVA E8. O TC-WB43-006 cobre B9, E9 e F9.
8. **C-D1 (aviso no 14_DASHBOARD):** a linha diz o que mudou em relação à V4.2 e como voltar (h2v = 0, h9v = 0).
   Mostra também a chave inválida e o modo do R inválido. O R de regulamento aparece como tal.
9. **C-G3 (`MATCH(TRUE,INDEX(faixa>=req,0),0)`):** o protótipo da Task 8 roda nos dois motores (Excel e LibreOffice,
   EDR-044). Se o LibreOffice não avaliar a forma matricial, troca-se por uma forma sem matriz equivalente, que é
   decidida e registrada na Task 8.
10. **Menores:** `ISNUMBER({amp})` na C-G1; as expressões do limite dianteiro passam a ficar em células próprias
    (`lim_tras`, `lim_diant`); `ISNUMBER` e ≥ 1 no fator (C-F1); o texto do veredito (B142) cita a faixa com o fator;
    LEIA-ME e .docx do Drive avisam que o B9 virou fórmula (Task 14).

## Decisões pendentes (do usuário)
- **A. Leitura do 4/3.** O usuário escolheu "faixa = 4/3 × a de hoje", com o mesmo fator no ramo de um eixo (texto
  do EDR-065 item 2). O catálogo C-F aplicou o fator só ao |S − S2| e deixou o passo sem ele. As duas leituras coincidem
  quando os dois eixos saturam nas duas grades, que é o único caso que o estudo mediu. Elas divergem quando um eixo
  satura numa grade só. O Python (Task 9) e a planilha precisam seguir a mesma leitura.
- **B. TC-WB43-003.** O 4/3 não tem chave, então muda B137 a B139 e o veredito perto do neutro mesmo com
  h2v = h9v = 0. Há duas saídas: o teste exclui essas células, e o TC-WB43-004 e o TC-NEU-002 as cobrem; ou o fator
  ganha uma chave.
- **C. Aba 19 (K linear).** A 19 lê `{da_FL}`/`{da_FR}` (`aba_equilibrio.py:1418`) e muda com h2v = 1, mas o
  `equilibrio_linear` chama `_fy_eixo_limitado` sem `formas` (`python/equilibrio_linear.py:177-178`). A mini-grade usa
  `_linha_grade` (`aba_equilibrio.py:1497`). Há duas saídas: a 19 segue a V4.3 (`formas` no `equilibrio_linear` e
  colunas novas na mini-grade), ou a 19 fica na V4.2 por desenho, com aviso. Nos dois casos, `_linha_grade` não é
  editado no lugar.
- **D. Apelido `res_16_raio_do_skidpad_usado` (parte da D4).** Ele quebra o invariante "um nome por célula"
  (`tests/test_v4_0.py:101-108`) e é redundante com o `{rusado}` da 24_CURVA. O conselho recomenda não criá-lo.

## Decisões do usuário (2026-11-02, depois do conselho)
- A. 4/3 **só no |S − S2|**; o passo fica sem o fator (EDR-065 item 2 corrigido).
- B. TC-WB43-003 **exclui B137 a B139** e o que depende delas; TC-WB43-004 e TC-NEU-002 cobrem o 4/3.
- C. A aba 19 **segue a V4.3**: `equilibrio_linear` ganha `formas` (padrão V4.2) e a mini-grade ganha as colunas novas, sem editar `_linha_grade` no lugar.
- D. **Sem o apelido** `res_16_raio_do_skidpad_usado` (EDR-069, D4).
- Os ajustes 1 a 10 são aplicados ao catálogo, que volta ao usuário para a aprovação final célula a célula.

## Riscos que sobreviveram à revisão
- Volume: ~28,6 mil fórmulas novas (+24 %). As `fy0_R` repetem a expansão Pacejka, então a Fy traseira dobra de
  custo. A Task 8 mede antes da 7b.
- O tempo de volta passa a ter valor com o R do regulamento (D5, aprovada) e com dados demonstrativos. A pior origem e
  o aviso (ajuste 8) precisam deixar isso visível.
- A forma `MATCH/INDEX` no LibreOffice continua não verificada (ajuste 9).

## Ranking da revisão anônima
| Resposta | Persona | Modelo | Borda (todos) | Borda (sem voto próprio) |
|---|---|---|---|---|
| B | Cético | opus | 10 | 6 |
| D | Arquiteto | sonnet | 9 | 4 |
| A | Física e convenção | opus | 5 | 2 |
| C | Usuário da planilha | sonnet | 0 | 0 |

As duas ordens coincidem. Rankings: Usuário B>D>A>C; Arquiteto D>B>A>C; Física B>A>D>C; Cético D>B>A>C.

## Composição e rigor
Nível padrão, 4 assentos, 1 rodada de revisão anônima. A persona Física e convenção entrou no lugar do Pragmático
porque a pergunta é a fidelidade das fórmulas. Os modelos opus ficaram nos assentos de maior risco (física e casos de
borda). Para poupar tokens, os revisores leram as respostas em arquivos com o texto integral, em vez de recebê-las
coladas no prompt, e foram instruídos a não alterá-los. Esse é um desvio declarado do método.

---

# Relatório do processo

## As lentes do conselho
| Conselheiro | Modelo | Lente | O que recomendou | Posição |
|---|---|---|---|---|
| Cético | opus | defeitos de fórmula e borda | aprovar com 6 ajustes obrigatórios; lista das chaves; 19 e `tvolta` fora do catálogo | 1º |
| Arquiteto | sonnet | estrutura e gerador | aprovar com ajustes; nomes `ent_` presos a fórmula; mini-grade da 19; volume | 2º |
| Física e convenção | opus | fidelidade ao Python | aprovar com ajustes; núcleo fiel; divergência do 4/3 com o EDR | 3º |
| Usuário da planilha | sonnet | quem preenche e lê | aprovar com sinalização; B9 parece entrada; tempo de volta com valor | 4º |

Cada lente trouxe algo próprio:
- Só o Cético viu a lista das chaves e a propagação de erro pelo B9.
- Só o Arquiteto viu a migração (`injetar` recusa fórmula) e o apelido duplicado.
- Só a Física e convenção viu a divergência do 4/3 com o EDR e conferiu o núcleo termo a termo.
- Só o Usuário viu o risco de leitura do tempo de volta. Ficou em último porque não avaliou fórmulas, que eram o
  centro da pergunta.

## O que a revisão anônima mudou
- Dois revisores acharam, sem combinar, o conflito do 4/3 com o TC-WB43-003 (decisão B), que nenhum conselheiro tinha
  visto.
- O "Crítico" da lista das chaves foi rebaixado a ajuste de redação: o gerador já usa `"0,1"`
  (`aba_equilibrio.py:1121`, conferido pelo presidente).
- `tvolta`, a 19, a migração e R ≤ b foram confirmados no código por mais de um revisor.

## O raciocínio do presidente
- **Por que esta decisão:** os quatro conselheiros e os quatro revisores convergiram em "aprovar com ajustes". Os
  ajustes 1 a 10 só tornam a planilha fiel ao Python fora do caminho feliz, sem física nova.
- **Por que não aprovar como está:** há #VALUE! possível na 16 inteira, perda de dado na migração e um teste (003) que
  não fecha.
- **Concordância com o ranking:** a síntese segue B e D na estrutura e incorpora o achado do 4/3 de A e o risco de
  leitura de C.
- **Fatos conferidos pelo presidente:** a lista `"0,1"` das chaves existentes e o `ISBLANK` da `tvolta`. Os demais
  foram conferidos por pelo menos dois revisores.
- **O que mudaria a decisão:** se a Task 8 mostrar recálculo inviável com as `fy0_R`, o desenho do C-G volta à mesa.
