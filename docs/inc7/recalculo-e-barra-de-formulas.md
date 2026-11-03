# Recálculo do protótipo, barra de fórmulas e MATCH/INDEX no LibreOffice (incremento 7, Task 8)

- **Data:** 2026-11-03. Branch `claude/inc7-7b-v43-0c2266`. A única mudança de código é `tools/medir_recalculo.py`, que
  passou a aceitar `--arquivo` (commit 8d76e3b).
- **Situação:** medição para a aprovação da C-G (plano `docs/superpowers/plans/2026-10-29-inc7-fisica-planilha.md`,
  catálogo da V4.3) e diagnóstico da spec §7. Nenhuma fórmula de planilha de referência mudou. O protótipo foi
  descartado: o script e as cópias ficaram fora do Git.
- **Valores de teste.** As cópias "com h9" usam os valores de teste do TC-WB42-005 (`tests/test_workbook_v4_2.py`,
  caso `C_KAPPA` sem a troca do KPUMAX): o `C3` do teste, mais R = 8 m, h3 = 1, ρ = 1,2 kg/m³, h9 = 1, CdA = 1,0 m² e
  Crr = 0,015. Não são dados do carro, do T11 nem do TX. Os números abaixo são tempos desta máquina e valores dessas
  cópias.

## 1. Protótipo

Um script descartável monta a V4.2 pelo caminho do gerador: V4.0 da tag `v4.0`, depois `gerar_v4_1.montar_v41`, depois
`gerar_v4_2.montar_v42`. Nesse caminho, `aba_equilibrio._colunas` e `_linha_grade` foram embrulhados para acrescentar
as colunas da C-G1 a C-G4b (`fy0_R_0 … fy0_R_{n−1}`, `cap0_R`, `idx0_R`, `j_F`, `j_R`, `aF`, `aR`), com o texto do
catálogo, em todas as grades: 17, 18, as duas de cada 20a a 20d e a mini-grade da 19. A C-G5 e a C-G6 (`fxr`, `fat`,
`pre_R`) ficaram de fora, como pede o brief.

- **Conferência do caminho:** a mesma montagem sem as colunas novas dá a V4.2 da tag célula a célula: 0 diferenças,
  117627 fórmulas e 1225 nomes, os mesmos do arquivo da tag. No protótipo, nenhuma célula da V4.2 mudou e entraram
  28723 fórmulas: 1271 na 17, 4455 na 18, 93 na 19 e 5726 em cada 20a a 20d. São 146350 fórmulas no total.
- **Posição das colunas:** depois da última coluna de cada grade. Na 17, FI:GM; na 18, GO:IQ, como diz a C-G. Na
  mini-grade da 19, ES:FW, depois da última de `CL_MINI`, também como diz a C-G. Nas grades pedidas das 20a a 20d, as
  colunas ficaram em ES:FW (linha 23) e não a partir de FI, porque essas grades não têm as colunas de excesso das
  limitações. Nas finas, ficaram em GO:IQ (linha 93). A posição final nas 20a a 20d fica para a Task 11.
- **Chave h9v:** o nome `{h9v}` (24_CURVA B10) ainda não existe. No protótipo, ele aponta para uma célula auxiliar
  fixa, `'PROTO'!$B$1`, numa aba `PROTO` no fim, e entra nas fórmulas pelo nome definido `proto_h9v`. A primeira
  versão escrevia `'PROTO'!$B$1` direto na fórmula (§2.3).

## 2. Tempo de recálculo (Excel via COM)

`tools/medir_recalculo.py --arquivo ARQ`. Cada execução usa uma instância nova do Excel e uma cópia nova do arquivo.
A: arquivo sem valores em cache e com `fullCalcOnLoad`; o Excel calcula tudo dentro do `Workbooks.Open`. B: o arquivo
gravado pelo Excel na 1ª execução de A, que é o estado da viva. Excel 16.0, Windows 10.0.26300, 20 núcleos lógicos,
cálculo multithread ligado. Antes e depois de cada medição havia 0 processos EXCEL.EXE, e nenhuma instância da
ferramenta ficou viva.

### 2.1 Medianas, em segundos (nome definido; 5 execuções por cenário, arquivos alternados)

| Cópia | A: abrir | A: CalculateFull | A: total | B: abrir | B: CalculateFull | B: total |
|---|---|---|---|---|---|---|
| V4.2 da tag (padrão) | 8,32 | 0,19 | 10,49 | 1,80 | 0,17 | 3,85 |
| Protótipo (padrão) | 13,80 | 0,17 | 16,43 | 2,23 | 0,21 | 4,83 |
| Razão protótipo ÷ V4.2 | 1,66 | — | 1,57 | 1,24 | — | 1,25 |
| V4.2 com h9 (valores de teste), 2ª rodada | 9,46 | 0,14 | 11,66 | 1,90 | 0,11 | 3,69 |
| Protótipo com h9 e h9v = 1, 2ª rodada | 14,01 | 0,93 | 23,90 | 2,29 | 0,18 | 4,98 |
| V4.2 com h9, 3ª rodada | 9,90 | 0,20 | 12,24 | 1,96 | 0,14 | 4,07 |
| Protótipo com h9 e h9v = 1, 3ª rodada | 13,99 | 0,19 | 17,30 | 2,26 | 0,16 | 5,10 |
| Razão com h9, 3ª rodada | 1,41 | — | 1,41 | 1,15 | — | 1,25 |

"Padrão" quer dizer as entradas como estão na V4.2 da tag. Com elas, o `ok` vale 1 e as grades calculam (na 17,
`cap_F` = 4390,6 N em a_y = 0). A h9 fica em 0, então as colunas novas dão "-".

Na 2ª rodada, o total de A do protótipo com h9 (23,90 s, razão 2,05) saiu de três execuções em que o CalculateFull, a
gravação e o fechamento ficaram lentos ao mesmo tempo (até 1,57 s, 6,99 s e 2,26 s). As outras duas deram 17,80 s e
17,23 s. Como o atraso apareceu também na gravação e no fechamento, a leitura é de interferência externa na máquina, e
a 3ª rodada repetiu o par: razão de 1,41, com as cinco execuções regulares.

### 2.2 Recálculo a quente repetido

Uma instância por arquivo, `Workbooks.Open` e então `CalculateFull` ×7 e `CalculateFullRebuild` ×3, em duas rodadas
alternadas (14 e 6 medidas por arquivo). O script é descartável.

| Cópia | CalculateFull: mediana (mín.) | CalculateFullRebuild: mediana (mín.) |
|---|---|---|
| V4.2 da tag (padrão) | 0,277 (0,090) | 1,887 (1,723) |
| Protótipo (padrão) | 0,119 (0,091) | 3,387 (2,790) |
| V4.2 com h9 | 0,145 (0,097) | 1,981 (1,447) |
| Protótipo com h9 e h9v = 1 | 0,564 (0,149) | 3,625 (3,246) |

O CalculateFull fica abaixo de 1 s e varia muito entre medidas: a V4.2 da tag foi de 0,090 s a 1,026 s no mesmo
arquivo. A razão das medianas não diz muito com esse ruído. O `CalculateFullRebuild` refaz a árvore de dependências e
recalcula tudo, como acontece na carga, e deu razão de 1,80 (padrão) e 1,83 (com h9).

**Conclusão do passo 1.** Nenhuma medida estável passa de 2× a da V4.2: abrir A, 1,4 a 1,7; total A, 1,4 a 1,6; abrir
e total B, 1,15 a 1,25; rebuild, 1,8. O mais perto do limite é o rebuild. A C-G não precisa da alternativa de limitar
as colunas novas à grade pedida.

### 2.3 Achado: referência direta a outra aba desfaz o agrupamento de fórmulas

A 1ª versão do protótipo escrevia `'PROTO'!$B$1` direto nas fórmulas de `fy0_R_i`, `aF` e `aR`. As medianas, com 3
execuções por cenário, foram estas:

| Cópia (1ª versão, referência direta) | A: abrir | A: total | B: abrir | B: total |
|---|---|---|---|---|
| V4.2 da tag | 15,32 | 18,08 | 2,92 | 6,08 |
| Protótipo | 20,14 | 24,05 | 11,24 | 15,45 |
| V4.2 com h9 | 11,28 | 13,63 | 3,10 | 6,24 |
| Protótipo com h9 | 21,58 | 24,81 | 8,30 | 11,96 |

Abrir o arquivo já salvo (B) ficou de 2,7 a 3,8 vezes mais lento. No arquivo gravado pelo Excel, as colunas com a
referência direta (`fy0_R_*`, `aF`, `aR`) estavam todas escritas por extenso, uma fórmula por célula, enquanto as
outras, inclusive `j_F` e `j_R`, saíram como fórmula compartilhada (`<f t="shared" si=…/>`). Na planilha inteira
foram 110230 compartilhadas e 36120 por extenso, contra 107870 e 9757 na V4.2. Com o nome definido no lugar da
referência, o Excel agrupou também essas colunas (135520 compartilhadas e 10830 por extenso; na 17, nenhuma coluna
nova por extenso), e o B voltou ao nível da V4.2 (tabela 2.1). O que se viu é essa correlação. Que a causa seja a
referência direta é inferência, não verificada no código do Excel.

Para a Task 11: as colunas novas devem ler as chaves só por nome definido (`{h9v}`, `{h2v}`), como o catálogo já
escreve. Um teste estrutural que recuse referência direta à 24_CURVA nas grades protegeria esse ponto. Fica como
sugestão, sem ID.

## 3. Diagnóstico da barra de fórmulas (spec §7)

Excel via COM (instância própria e invisível, PID 72420, encerrada no fim), três cópias locais abertas somente para
leitura:
1. cópia da V4.2 da tag (`git show v4.2:…`);
2. cópia local da viva do Drive (`…\Planilha DDS\FSAE_EV_Suspension_Fase1_V4_2.xlsx`, só copiada; nada foi gravado,
   movido ou recalculado no Drive). O SHA-256 é igual ao da tag (`0d979440…ccde0`). O arquivo do Drive não tem
   `Zone.Identifier`: o volume H: (Google Drive para desktop) não aceita fluxos alternativos, e o
   `Get-Item -Stream *` respondeu "Parâmetro incorreto". A cópia local também saiu sem a marca;
3. a cópia 2 com um `Zone.Identifier` posto à mão (`ZoneId=3`, `HostUrl=https://drive.google.com/`), que simula um
   arquivo baixado pelo navegador.

| Item (ordem do brief) | Cópia 1 (tag) | Cópia 2 (Drive) | Cópia 3 (Drive com marca) |
|---|---|---|---|
| `ws.ProtectContents` | nenhuma das 28 abas | idem | idem |
| `Range.FormulaHidden` (UsedRange de cada aba; B84; BP24) | False em todas; False; False | idem | idem |
| XML: `sheetProtection` / `protection hidden="1"` nos estilos | nenhuma / 0 de 49 | idem | idem |
| XML: `workbookProtection` | `<workbookProtection />` vazio; `ProtectStructure` e `ProtectWindows` = False | idem | idem |
| `Application.DisplayFormulaBar` | True | True | True |
| `ProtectedViewWindows.Count` depois do `Workbooks.Open` | 0 | 0 | 0 |
| `ProtectedViewWindows.Open` (Modo de Exibição Protegido explícito) | Count 1; pasta somente leitura; o COM lê `HasFormula` = True e o texto da fórmula da B84 | idem | idem |
| `Range.HasArray` (B84, BP24, UsedRange de cada aba) | False | False | False |
| `HasFormula` em 16_EQUILIBRIO!B84 (nome `res_16_delta_ref_l_r`) | True; formato `0,0000` | idem | idem |
| `HasFormula` em 17_EQ_PAR!BP24 (sem nome) | True; formato `Geral` | idem | idem |

**Resultado: não reproduzido.** Nada no arquivo esconde a fórmula: não há proteção de aba nem de pasta, nenhuma célula
tem `FormulaHidden`, nenhuma fórmula está gravada como matriz, e as duas células conferidas têm fórmula, não texto (o
formato não é `@`). A barra de fórmulas está ligada nesta máquina. Pelo que se conferiu, não há o que corrigir no
gerador (C-B1).

Três observações do diagnóstico:
- O `Workbooks.Open` por automação não aplica o Modo de Exibição Protegido, nem com a marca da internet (cópia 3).
  Por isso o COM não mostra o que a pessoa vê ao dar dois cliques num arquivo baixado. O modo protegido explícito abre
  a pasta somente para leitura, e mesmo assim o COM lê a fórmula. Se a barra de fórmulas mostra a fórmula nesse modo
  é coisa da interface, e não foi verificado.
- Quem abre a viva direto pelo H: não recebe a marca da internet (o volume não guarda a marca), então não cai no modo
  protegido por esse motivo. Quem baixa o arquivo pelo navegador (drive.google.com) recebe a marca.
- O `<workbookProtection />` vazio vem do gerador (openpyxl) e já está na V4.2 da tag. O Excel o lê como pasta sem
  proteção. Não é a causa, mas fica registrado.

**Hipóteses de ambiente para levar ao usuário (nenhuma verificada):**
1. arquivo baixado pelo navegador e aberto no Modo de Exibição Protegido (faixa amarela "MODO DE EXIBIÇÃO
   PROTEGIDO"; a edição fica desligada até "Habilitar Edição");
2. planilha vista na pré-visualização do Google Drive no navegador, no Google Planilhas, no Excel na Web ou no
   celular, e não no Excel da área de trabalho;
3. barra de fórmulas desligada no Excel de quem relatou (Exibir > Barra de Fórmulas; é configuração de cada usuário,
   e só a desta máquina foi lida).

Perguntas que fecham o diagnóstico: em que programa e de que jeito a planilha foi aberta, se apareceu a faixa amarela
e em qual célula se clicou. Se a resposta apontar para o ambiente, o texto vai para o LEIA-ME (Task 14). Se apontar
para o arquivo, o diagnóstico precisa ser refeito com o caso relatado.

## 4. MATCH/INDEX no LibreOffice (ajuste 9 do conselho)

Cada cópia do protótipo foi recalculada duas vezes: pelo Excel via COM e pelo LibreOffice 26.8.1.1 headless
(`tests/recalculo_planilha.py`, EDR-044). Só cópias do protótipo passaram pelo LibreOffice, nunca a referência nem a
viva. A comparação foi linha a linha, nas abas 17, 18, 19 (mini-grade) e 20a (as duas grades), 247 linhas por cópia,
das colunas `j_F`, `j_R`, `aF`, `aR` e das de apoio (`req_F`, `cap_F`, `idx_F`, `pre_F`, `fy_F_0`, `req_R`, `cap0_R`,
`idx0_R`, `fy0_R_0`). Número igual quer dizer tolerância relativa de 1e-9; texto, igualdade exata.

| Cópia | Linhas | Diferenças | Casos cobertos |
|---|---|---|---|
| Protótipo com h9 e h9v = 1 | 247 | 0 | j = 1, meio da grade, acima do pico (j = 0 pelo IFERROR) e `semF` na frente |
| Protótipo com h9, h9v = 0 | 247 | 0 | coluna "-" (todo `fy0_R` = "-"; `aF` e `aR` = "-") |
| Protótipo com h9 sem o C3 | 247 | 0 | j = 1 e meio da grade (nenhum eixo satura até 2 g) |
| Protótipo padrão (h9 = 0) | 247 | 0 | `aF` e `aR` = "-" com `j_F` calculado |

Linhas da 17_EQ_PAR, cópia com h9 e h9v = 1 (os valores do LibreOffice são iguais aos do Excel até a tolerância; abaixo,
os do Excel, com 4 algarismos):

| Caso | k (a_y) | req_F | cap_F (idx_F) | j_F Excel / LO | aF Excel / LO [rad] | j_R Excel / LO | aR Excel / LO [rad] |
|---|---|---|---|---|---|---|---|
| requisito abaixo do 1º ponto | 0 (0 g) | 0 | 2005,4 (7) | 1 / 1 | 0 / 0 | 1 / 1 | 0 / 0 |
| meio da grade | 1 (0,05 g) | 77,62 | 1997,3 (7) | 2 / 2 | 2,240E-04 / 2,240E-04 | 2 / 2 | 2,177E-04 / 2,177E-04 |
| meio da grade, perto do pico | 23 (1,15 g) | 1785,3 | 1852,5 (7) | 5 / 5 | 0,03976 / 0,03976 | 4 / 4 | 0,03195 / 0,03195 |
| acima do pico na frente | 24 (1,20 g) | 1862,9 | 1849,3 (7) | 0 / 0 | 0,06545 / 0,06545 (α do pico) | 5 / 5 | 0,04211 / 0,04211 |
| acima do pico nos dois eixos | 25 (1,25 g) | 1940,5 | 1846,0 (7) | 0 / 0 | 0,06545 / 0,06545 | 0 / 0 | 0,06545 / 0,06545 |
| frente sem curva | 40 (2,00 g) | 3104,9 | N/A | 1 / 1 | semF / semF | 0 / 0 | 0,06545 / 0,06545 |
| coluna "-" (cópia com h9v = 0) | 1 (0,05 g) | 77,62 | 1997,3 (7) | 2 / 2 | - / - | 1 / 1 | - / - |

Nas linhas em que a faixa é texto ("N/A" ou "-"), o `j` sai 1 nos dois programas, porque os dois tratam texto como
maior que número na comparação `>=`. O `aF` e o `aR` não usam esse `j`: o primeiro teste (`pre_F<>"-"` ou
`NOT(ISNUMBER(cap0_R))`) e a chave já decidem antes.

**Conclusão do passo 3.** O LibreOffice avalia a forma `MATCH(TRUE,INDEX(faixa>=req,0),0)` da C-G3 e chega aos mesmos
valores do Excel em todos os casos pedidos. A C-G3 fica como está no catálogo, sem adendo e sem forma alternativa.
O descolamento da traseira com h9v = 1 (`aR` = `semF`) não apareceu nessas cópias e não foi exercitado.

## Limites

- Os tempos são desta máquina e desta sessão, e houve interferência externa em algumas execuções (§2.1). Vale a ordem
  de grandeza e a razão entre arquivos medidos na mesma rodada.
- O protótipo não tem as outras mudanças da V4.3 (24_CURVA, C-B, C-C, C-F, C-G5, C-G6). A V4.3 terá mais fórmulas do
  que ele, mas as da 24_CURVA são poucas perto das 28723 das grades.
- A comparação com o LibreOffice cobre as colunas novas e as de apoio listadas, não a planilha inteira.
- O diagnóstico da barra de fórmulas leu o arquivo pelo COM e pelo XML. A interface do Excel não foi vista: nenhuma
  captura de tela, nenhum Excel visível.
