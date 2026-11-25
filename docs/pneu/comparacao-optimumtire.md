# Roteiro: comparar o modelo de pneu com o OptimumTire

**Para quem:** quem vai rodar o OptimumTire (OptimumT) e devolver os números. Não é preciso saber Python nem
conhecer o Sistema_DDS. **Tempo estimado:** 1 a 2 h na primeira vez.

**Por que isso existe:** o Python do Sistema_DDS calcula forças e momentos do pneu com as equações do PAC2002.
O OptimumTire é a referência do projeto (EDR-004). Antes de qualquer uso de projeto, os dois precisam dar os
mesmos números para o mesmo arquivo de pneu (condição do EDR-067). Os resultados também decidem um ponto
pendente sobre o momento autoalinhante Mz (EDR-067, item 3). A comparação em si é feita depois, no
repositório; você só precisa **gerar os números do OptimumTire** e entregá-los como descrito no fim.

**Regra de ouro:** não ajuste, ajuste fino ou "fit" nada. O objetivo é avaliar o arquivo `.tir` exatamente
como ele é. Se alguma coisa parecer estranha, anote e siga; quem decide é o responsável pelo repositório.

As referências a seções ("help, seção 6.1") são do arquivo de ajuda do OptimumTire (`Tire_Help_File.pdf`).
Onde este roteiro diz **(conferir na tela)**, o help não mostra o detalhe e a tela da sua versão manda.

---

## O que você recebe

1. O arquivo de pneu:
   `Round_6_Hoosier_R25B_20p5x7_13_on_7in_12psi_PAC02_UM4.tir` (Hoosier R25B, TTC Round 6, 12 psi).
   Ele não vai pelo GitHub (os dados do TTC não são versionados); peça ao responsável.
   **SHA-256 esperado:** `b19835886ecbe21aa4ecfac0352896b2648ab670569d7c3a6023780dda769a99`
2. A grade de pontos: `docs/pneu/grade-comparacao-optimumtire.csv` (405 linhas, uma por ponto).

## Antes de começar

**Confirme que o arquivo é o certo.** No PowerShell, na pasta do arquivo:

```powershell
Get-FileHash .\Round_6_Hoosier_R25B_20p5x7_13_on_7in_12psi_PAC02_UM4.tir -Algorithm SHA256
```

O resultado tem de ser igual ao SHA-256 acima (maiúsculas ou minúsculas tanto faz). Se for diferente, pare e
avise: os números não serviriam.

**O que precisa estar instalado:** OptimumTire com licença ativa e o Microsoft Excel no mesmo computador
(o caminho principal usa o add-in do OptimumTire dentro do Excel).

---

## Entendendo a grade

Cada linha do CSV é um ponto de operação do pneu. As colunas de entrada já estão preenchidas:

| Coluna | O que é | Unidade | Valores na grade |
|---|---|---|---|
| `Fz_N` | carga vertical no pneu | N | 1054, 1277, 1500 |
| `SA_deg` | ângulo de deriva (slip angle) | grau | −8, −4, −2, −1, 0, 1, 2, 4, 8 |
| `SR` | escorregamento longitudinal (slip ratio) | adimensional | −0,08; 0; 0,08 |
| `IA_deg` | cambagem (inclination angle) | grau | −3,9; −2; 0; 2; 3,9 |
| `V_mps` | velocidade | m/s | 11,176 (a do ensaio) |
| `P_bar` | pressão | bar | 0,8274 (12 psi) |

As colunas `Fx_N`, `Fy_N`, `Mx_Nm`, `My_Nm` e `Mz_Nm` estão vazias: são elas que você preenche.

A ordem das colunas de entrada (Fz, SA, SR, IA, V, P) é a mesma das funções do add-in (help, seção 6.1):
`Saída = Função(Fz, SA, SR, IA, V, P, Coeficientes)`. As unidades também são as que o add-in exige
(help, tabela 6.1): N, grau, razão, grau, m/s e bar.

Os valores negativos de SA e IA já cobrem o lado esquerdo do carro. O espelhamento é feito depois, no
repositório; você não precisa fazer nada de especial para isso.

---

## Passo 1: criar o projeto e importar o pneu

1. Abra o OptimumTire e crie um projeto novo.
2. No topo da árvore do projeto (*Tire Project Tree*), clique em **New Tire Model** e escolha o modelo
   **Pacejka 2002** (help, seção 8.7.2). Não escolha "Pacejka 2002 with Inflation Pressure Effects", MF 5.2,
   Pacejka '96 nem Pacejka 2006: o arquivo é PAC2002 (`PROPERTY_FILE_FORMAT = 'PAC2002'`).
3. Clique no modelo novo na árvore. Os coeficientes aparecem zerados na área de entrada.
4. No topo da área de entrada, clique em **Options → Import** e escolha o arquivo `.tir` (help, seção 3.2).
   A importação sobrescreve os coeficientes zerados.
5. Confira três coeficientes na tela contra o arquivo (abra o `.tir` no Bloco de Notas para comparar):
   `FNOMIN = 1054`, `PCX1` e `PCY1`. Se algum vier zerado ou diferente, a importação falhou: anote e avise.

## Passo 2: acertar o sistema de coordenadas (o passo mais importante)

O arquivo `.tir` **não diz** em que sistema de coordenadas está (help, seção 3.2.1). Este arquivo está no
sistema **ISO** (eixo W do TYDEX; EDR-039 do repositório). Se o OptimumTire tratar o modelo como SAE, os sinais
de Fy, Mx e Mz saem trocados e a comparação inteira fica errada.

1. Nas propriedades do modelo, ajuste o sistema de coordenadas para **ISO** **(conferir na tela onde fica a
   opção; o help cita quatro sistemas: SAE J670e, Adapted SAE, ISO e Adapted ISO, seção 8.2)**.
   Use **ISO**, não "Adapted ISO".
2. Ajuste as unidades de exibição para **Newton**, **Newton meter**, **degree** e **bar** (help, seção 8.3).
   Assim o que aparece na tela tem as mesmas unidades da grade.

**Teste de sinal (obrigatório).** Avalie um único ponto: Fz = 1054 N, SA = +4°, SR = 0, IA = 0°,
V = 11,176 m/s, P = 0,8274 bar. No sistema ISO, **Fy tem de ser negativo** (no PAC2002 em ISO, a rigidez de
deriva é negativa: help do Adams, tabela de verificação dos coeficientes). Se Fy der positivo, o modelo está em
SAE: volte ao item 1 deste passo. Anote o valor de Fy desse teste.

## Passo 3: gerar os números pelo add-in do Excel (caminho principal)

O add-in calcula o modelo do OptimumTire dentro de uma célula do Excel, ponto a ponto. É o jeito mais simples de
preencher as 405 linhas sem erro de leitura de gráfico.

**3.1 Ativar o add-in no Excel** (help, seção 6.1.1; os menus abaixo são os do Excel atual,
**conferir na tela**):

1. Excel → **Arquivo → Opções → Suplementos**.
2. Embaixo, em **Gerenciar**, escolha **Suplementos do Excel** e clique em **Ir...**.
3. Clique em **Automação...**, escolha **OptimumT.Calculations** e confirme com **OK**.
4. Confira: em **Inserir Função** (botão *fx*), a categoria **OptimumTExcelAddin** aparece com as funções.

**3.2 Copiar o modelo para o Excel** (help, seção 6.1):

1. No OptimumTire, clique no modelo na árvore.
2. **Options → Export → Add-in Model to Clipboard**. Isso copia um texto longo, codificado, que representa
   o modelo (e carrega também o sistema de coordenadas escolhido no Passo 2).
3. Abra a grade (`grade-comparacao-optimumtire.csv`) no Excel e salve **uma cópia** como
   `resultado-optimumtire.xlsx`. Não grave por cima do CSV original.
4. Cole o texto do modelo numa célula livre, por exemplo `N1`. Vamos chamar essa célula de "célula do modelo".

**3.3 Conferir o modelo carregado:**

- Numa célula livre, use a função de informação do modelo, `GetModelInfo` (help, seção 6.1), apontando para a
  célula do modelo. Ela mostra o tipo de modelo e o sistema de coordenadas. Tem de aparecer **Pacejka 2002**
  e **ISO**. Anote o que aparecer exatamente.

**3.4 Preencher as saídas.** Na linha 2 (o primeiro ponto), escreva uma fórmula por coluna de saída. O help só
mostra pelo nome a função de Fy, `CalculateFy`; as demais **(conferir na tela, na lista da categoria
OptimumTExcelAddin)** devem ser as equivalentes para Fx, Mx, My e Mz. Use as funções **combinadas** se a lista
separar pura e combinada, porque a grade tem SR e SA juntos.

Exemplo para Fy (a célula do modelo fixa com `$`):

```
=CalculateFy(B2; C2; D2; E2; F2; G2; $N$1)
```

(B = Fz_N, C = SA_deg, D = SR, E = IA_deg, F = V_mps, G = P_bar. Se o seu Excel usar vírgula como separador de
argumentos, troque `;` por `,`.)

Depois de escrever as cinco fórmulas na linha 2, selecione as cinco células e arraste até a linha 406.

**3.5 Conferências antes de entregar:**

1. A linha do teste de sinal (Fz 1054, SA +4, SR 0, IA 0) tem de bater com o valor anotado no Passo 2.
   Na grade é a linha com `id` 77.
2. Nenhuma célula de saída com erro (`#VALOR!`, `#NOME?` e parecidos). Se houver `#NOME?`, o add-in não está
   carregado (volte a 3.1).
3. Com SA = 0, SR = 0 e IA = 0, Fx e Fy devem ser pequenos perto dos milhares de N das outras linhas (da ordem
   de 100 N, no máximo). São os desvios do ajuste do ensaio, não erro. Não é um critério de aprovação, só um
   sinal de que nada está grosseiramente errado. Anote se não for assim.
4. Salve. Depois salve também uma versão **só com valores** (copiar → colar especial → valores) em CSV, com o
   nome `resultado-optimumtire.csv`, mantendo as mesmas colunas e o ponto como separador decimal
   **(conferir: no Excel em português, use "CSV UTF-8" e, se as vírgulas decimais aparecerem, avise em vez de
   converter à mão)**.

## Passo 4 (só se o add-in não funcionar): exportar pelos gráficos

Use este caminho apenas se o Passo 3 não for possível (por exemplo, sem licença do add-in). É mais trabalhoso.

1. Crie um gráfico padrão (*Standard Graph*, help, seção 4.1.2) com saída **Mz** no eixo Y e **Slip Angle** no
   eixo X.
2. Nas entradas do gráfico (help, seção 4.1.4), use **Custom Sweep** para o Slip Angle com os valores da grade
   (−8, −4, −2, −1, 0, 1, 2, 4, 8) e **Fixed Value** para os demais (uma combinação de Fz, SR e IA por vez), ou use
   Fz e IA como *Sweep* para ter várias curvas no mesmo gráfico.
3. Exporte com **Export Graph Data** (help, seção 4.3.5): sai um arquivo do Excel, com um cabeçalho por curva
   indicando as condições.
4. Repita para Fx, Fy, Mx e My, e para cada valor de SR.
5. Entregue os arquivos exportados como saíram, sem reorganizar. A conversão para o formato da grade é feita no
   repositório.

## Passo 5: o que entregar

Mande ao responsável pelo repositório:

1. `resultado-optimumtire.xlsx` (com as fórmulas) e `resultado-optimumtire.csv` (só valores), ou os arquivos do
   Passo 4.
2. Um print da tela do modelo mostrando o tipo (Pacejka 2002) e o sistema de coordenadas (ISO), e o texto que
   `GetModelInfo` devolveu.
3. A versão do OptimumTire (menu de ajuda → sobre) e a data em que os números foram gerados.
4. O SHA-256 do `.tir` que você usou (o resultado do `Get-FileHash`).
5. O valor de Fy do teste de sinal e qualquer anotação de coisa estranha (aviso de importação, coeficiente que não
   bateu, mensagem de faixa válida).

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Fy positivo no teste de sinal | modelo em SAE | refazer o Passo 2 com ISO |
| `#NOME?` nas fórmulas | add-in não carregado | refazer 3.1 |
| Todas as saídas zero | modelo colado errado ou coeficientes não importados | refazer 1.4 e 3.2 |
| Mensagem de valor fora da faixa | a faixa do arquivo é Fz 100 a 1521 N, SA ±15°, IA ±4°, SR ±0,25; a grade está dentro dela | anotar a mensagem e o ponto |
| Escolhas que não aparecem na sua versão | versão do OptimumTire diferente da do help | anotar o que aparece e seguir com o mais próximo |

## O que acontece depois (para o responsável pelo repositório)

Com o CSV de volta, o modelo do Python é avaliado nos mesmos 405 pontos (`python/tire_model_static.py`, perfil de
12 psi) e comparado coluna a coluna. Critério do item 3 do EDR-067: fica a forma do Mz, (a) ou (b), cuja diferença
para o OptimumTire é no máximo 5 % do |Mz| da referência ou 1 N·m, o que for maior, em todos os pontos; se
nenhuma atender, a decisão volta ao usuário com a tabela. Fx, Fy, Mx e My entram na mesma tabela; diferença
fora da tolerância segue a ordem de investigação do CLAUDE.md (unidades → coordenadas → ... → equações).
O EDR-067 só sai de APPROVED_WITH_CONDITIONS com essa comparação registrada.
