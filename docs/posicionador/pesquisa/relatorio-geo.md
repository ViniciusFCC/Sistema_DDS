# Relatório GEO: chassi.step em tubos e nós, e confronto com a v20

Data: 2026-11-17. Pasta: `geo/` (dentro de `atuacao/`). Nada foi escrito fora de `geo/`. Os arquivos do Murilo
(`script_murilo/*.py`, `geometria_T11.json`) foram conferidos por SHA-256 antes e depois e não mudaram.

Rótulos usados: **[código]** = resultado de código rodado aqui; **[cálculo]** = conta feita à mão sobre números do código;
**[inferência]** = conclusão minha a partir dos dados; **[hipótese]** = não verificável com o que existe.

## 1. Ferramenta

- **OpenCascade via `cadquery-ocp` 8.0.1** (Python 3.12, venv isolado em `geo/.venv`, com numpy 2.5, scipy 1.18 e
  matplotlib 3.11). Funcionou. gmsh e o parser textual não foram necessários. **[código]**
- Caminho de leitura: a estrutura da montagem (NAUO, `ITEM_DEFINED_TRANSFORMATION`, `SHAPE_REPRESENTATION_RELATIONSHIP`)
  sai do texto do STEP. Cada sólido é transferido sozinho pelo OCC (`STEPControl_Reader.TransferOne`) e movido com a
  matriz da ocorrência. O XCAF (`STEPCAFControl`) dava segfault ao ler os sub-shapes com nome (bug do binding), então
  ele foi usado só como conferência: as 7 matrizes de ocorrência lidas do texto são iguais às do XCAF
  (diferença máxima de 2e-32). **[código]**
- Tudo rodou com `python -I -B`. O script do Murilo foi importado como biblioteca, sem `__main__` e sem gravar `.pyc`.

Arquivos:

| arquivo | conteúdo |
|---|---|
| `step_tubos.py` | biblioteca: ler STEP → tubos → nós → transformação (`ler_step`, `extrair_tubos`, `achar_nos`, `mais_proximo`, `dist_seg_seg`, `TRANSF_STEP_PARA_SCRIPT`). `python -I step_tubos.py chassi.step` regrava `tubos.json` e `nos.json` (cerca de 3 min) |
| `confronto_v20.py` | referencial, itens 6a a 6c e figuras; grava `confronto_v20.json`, `vistas.png` e `vistas_dianteira.png` (cerca de 11 s) |
| `tubos.json` | 31 corpos, em coordenadas do STEP (mm) |
| `nos.json` | nós com tolerâncias de 2, 5 e 10 mm, em coordenadas do STEP (`pos_mm`) e do script (`pos_script_mm`) |
| `confronto_v20.json` | números completos dos itens 5 e 6 |
| `vistas.png`, `vistas_dianteira.png` | três vistas (carro inteiro; zoom na dianteira com droop, estático e bump) |
| `explor/` | scripts da exploração (descartáveis) |

## 2. Montagem: transformações e conferência

| ocorrência | transformação para a raiz "chassi" (mm) | posição resultante (coordenadas do STEP) |
|---|---|---|
| raiz `chassi` (19 corpos) | identidade | X de −400 a +746 |
| `FH:1` | translação (800, 0, 0) | FH no plano X = 740 |
| `FBH:1` | translação (1496,942, 0, 0) | FBH no plano X = 1436,9 (faces em 1424,4 e 1449,4) |
| `MH-estreito:1` | translação (60, 15, 0) | MH no plano X = 0, Y simétrico (±311) |
| `Orelha Pack:1` a `:4` | rotação de 90° mais translação | rente aos tubos inferiores (Z −17 a +13), em Y ±50 (X −64 a 3) e ±211 a 279 (X −240 a −200) |

Conferência pela bounding box **[código]**: o FH (X 740) fica à frente do MH (X 0) e atrás do FBH (X 1437). As pontas
dos tubos da raiz caem exatamente nos eixos do FH e do MH (nós com espalhamento de 0,0 a 1,3 mm). Todos os corpos são
simétricos em Y a ≤ 0,5 mm (espelho de cada trecho reto contra todos os outros). A única exceção é a diagonal do FBH
(Body7), que é uma diagonal única e por isso não tem par.

## 3. Inventário de tubos

Contagem **[código]**: 31 corpos (28 sólidos no arquivo; a orelha aparece 4 vezes).

- 12 tubos redondos Ø25,4: 10 retos e 2 curvados (FH e MH).
- 11 corpos de tubo quadrado 25 × 25 × 1,2: 7 retos e 4 quadros com vários trechos no mesmo corpo.
- 4 chapas de 1,2 mm (reforços nos cantos do FBH).
- 4 suportes com furo Ø8 (orelhas do pack).

Segundo caminho **[código]**: os raios contados no texto do STEP dão 28 `CYLINDRICAL_SURFACE` de R 12,7, 8 de R 10,8
(os 8 tubos Body87 a 94, ID 21,6), 2 de R 11,5 (Body128/129, ID 23), 18 de R 10,05 (paredes internas do FH e do MH,
ID 20,1) e 1 de R 4 (furo da orelha). Isso bate com a classificação.

Coordenadas abaixo **no referencial do script** (X+ frente, Y+ esquerda, Z+ cima, mm; origem no eixo dianteiro, na
linha de centro e no chão; ver seção 5). Polilinhas e dobras completas estão em `tubos.json`.

| corpo | tipo | seção (OD × parede) | eixo (início → fim, comprimento) |
|---|---|---|---|
| FH:1/Body2 | curvado, fechado | Ø25,4 × 2,65 | 6 trechos: base (Y ±202, Z 131), 2 diagonais inferiores, 2 laterais retas (277,7), topo (Z 680); dobras R 134,8 (51,8°) ×2 e R 135 (83,2°) ×2; 2 cantos vivos na base |
| MH-estreito:1/Body4 | curvado, fechado | Ø25,4 × 2,65 | 6 trechos: base Z 77, laterais até Z 373, inclinadas até Z 1196, topo Z 1257; dobras R 80 (17,4°) ×2 e R 79,4 (77,5°) ×2 |
| braceFBHesq / dir | tubo quadrado | 25 × 25 × 1,2 | (−190, ±209, 642) → (482, ±156, 445), L 702 (do canto superior do FH ao canto superior do FBH) |
| Body85 / 86 | tubo quadrado | 25 × 25 × 1,2 | (−203, ∓210, 646) → (−942, ∓313, 385), L 790 |
| Body87 / 93 | reto | Ø25,4 × 1,9 | (−202, ∓277, 369) → (−942, ∓313, 385), L 741 |
| Body88 / 90 | reto | Ø25,4 × 1,9 | (−202, ∓281, 225) → (−942, ∓313, 385), L 758 |
| Body94 / 91 | reto | Ø25,4 × 1,9 | (−942, ∓295, 77) → (−202, ∓281, 225), L 755 |
| Body89 / 92 | reto | Ø25,4 × 1,9 | (−942, ∓295, 77) → (−202, ∓198, 131), L 748 |
| Body129 / 128 | reto | Ø25,4 × 1,2 | (−942, ∓295, 77) → (−1342, ∓295, 77), L 400 |
| Body130 / 131 | tubo quadrado | 25 × 25 × 1,2 | (−943, ∓313, 385) → (−1341, ∓313, 385), L 398 |
| tubo inversor 1 / 2 | quadro (U invertido) | 25 × 25 × 1,2 | X −1005 / −1165: pernas em Y ±313 (Z 385 → 455) e travessa em Z 455 |
| tubo orelhas pack | quadro (U baixo) | 25 × 25 × 1,2 | X −1260: pernas de 28 mm e travessa em Z 413 |
| FBH:1/Body6 | quadro quadrado | 25 × 25 × 1,2 | X 494,9; eixos em Y ±155 e Z 131,3 a 441,3 |
| FBH:1/Body7 | tubo quadrado | 25 × 25 × 1,2 | diagonal do FBH, (495, −133, 153) → (495, 133, 419) |
| FBH:1/Body8 a 11 | chapa | 1,2 | reforços nos cantos do FBH |
| Orelha:1 a 4 | suporte | furo Ø8 | perto dos tubos inferiores, atrás do MH |

Fato do arquivo **[código]**: entre o FH (X −202) e o FBH (X 495), os únicos tubos são os dois `braceFBH` (no alto) e o
próprio FBH. Não há trilho inferior, nem lateral, nem tubo na altura das bandejas. É nessa zona que ficam todos os
pontos internos da suspensão dianteira (X −199 a 123).

## 4. Nós

Método **[código]**:

- Encontros dos eixos (trechos retos e dobras discretizadas a cada 5°) de tubos diferentes, e cantos vivos dentro do
  mesmo corpo.
- Cada trecho reto é estendido nas pontas em (R1 + R2 + tol)/sen θ, porque tubo cortado em boca de lobo termina na
  parede do outro, não no eixo.
- Os encontros a menos de 25,4 mm (1 OD) se juntam num nó.
- "Triangulado" = pelo menos 3 ramos (direções de tubo saindo do nó, amostradas entre 20 e 45 mm) não coplanares.
  Um tubo que atravessa o nó conta como 2 ramos colineares.

Resultado: **28 nós, 14 triangulados**.

Sensibilidade **[código]**:

- Tolerância entre eixos de 2, 5 ou 10 mm: os mesmos 28 nós e 14 triangulados. O maior desvio entre eixos num nó é
  0,9 mm (N13/N16, ponta do Body85/86 no MH); o espalhamento máximo é 1,3 mm.
- Raio de agrupamento de 50,8 mm: 26 nós. Juntam-se as pernas curtas do "tubo orelhas pack".
- A tolerância só pesou numa versão anterior do método, que estendia as pontas só em R + tol: a diagonal do FBH, que
  chega ao canto em 45°, só virava nó com 10 mm. A extensão por 1/sen θ resolveu isso.

| nó | posição no script (mm) | n.º de tubos | n.º de ramos | triangulado | tubos |
|---|---|---|---|---|---|
| N02 / N04 | (495, ∓155, 441) | 2 / 3 | 3 / 4 | sim | canto superior do FBH + braceFBH (N04 também com a diagonal) |
| N01 / N03 | (495, ∓155, 131) | 2 / 1 | 3 / 2 | não | canto inferior do FBH (N01 com a diagonal, coplanar) |
| N07 / N10 | (−202, ∓210, 646) | 3 | 4 | sim | dobra superior do FH + braceFBH + Body85/86 |
| N05 / N12 | (−202, ∓281, 225) | 3 | 4 | sim | dobra inferior do FH + Body88/94 (90/91) |
| N06 / N11 | (−202, ∓277, 369) | 2 | 3 | **não** | lado reto do FH + Body87/93 (um tubo só, chegando num tubo reto) |
| N08 / N09 | (−202, ∓198, 131) | 2 | 3 | sim | canto vivo inferior do FH + Body89/92 |
| N13 / N16 | (−942, ∓313, 385) | 5 | 6 | sim | MH + Body85, 87, 88, 130 |
| N14 / N15 | (−942, ∓295, 77) | 4 | 5 | sim | MH (canto inferior) + Body89, 94, 129 |
| N17 a N24 | X −1005 e −1165 | 1 a 2 | 2 a 3 | não | tubos do inversor sobre Body130/131 |
| N25 / N27, N26 / N28 | X −1260 | 2 / 1 | 4 / 2 | sim / não | "orelhas pack"; o "sim" de N25/N27 é artefato (ver seção 7) |

O nó N03 (canto do FBH sem a diagonal) vem do canto vivo do próprio quadro. Os nós dos inversores e do pack ficam
atrás do MH e não interessam à dianteira.

Segundo caminho **[cálculo]**: N12 = ponta do Body91 em (740; 280,9; 147,6) no STEP. A distância ao centro da dobra
inferior do FH, (153,6; 191,8) em YZ, é 134,75 mm, contra R 134,77: o ponto está sobre o eixo da dobra.

## 5. Referencial e transformação STEP → script

Eixos do STEP **[código + inferência]**:

- X+ é a frente: FBH em X 1437, FH em 740, MH em 0.
- Z+ é para cima: topo do MH em Z 1180.
- Y+ é a esquerda: o corpo `braceFBHesq` (esquerda) está em Y > 0 e o `braceFBHdir` em Y < 0. A geometria é simétrica,
  então o sinal de Y só sai dos nomes. Isso é inferência.
- Origem do STEP: X = 0 no plano do MH; Z = 0 no eixo do tubo inferior do MH; Y = 0 no plano de simetria.

Ajuste **[código]**: o lado reto esquerdo do FH no CAD vai de (740; 287,43; 207,76) a (740; 254,53; 483,47), com
L = 277,67. No script, FH0 = (−202, 287, 285) e FH1 = (−202, 254, 561), com L = 277,97.

- Direções: diferença de 0,014°. Os dois estão num plano de X constante. Logo não há rotação (a menos de cerca de 0,1°).
- **H1**, translação livre: (−942,0; −0,48; +77,39), resíduo de 0,16 mm em cada ponta.
- **H2**, translação com ΔY = 0 (adotada): (−942,0; 0; +77,39), resíduos de 0,45 e 0,55 mm.
  - É compatível com o arredondamento ao mm dos valores do script.
  - O CAD é simétrico em Y = 0 a ≤ 0,5 mm, e a origem do script fica na linha de centro.
  - **Transformação adotada: script = STEP + (−942,0; 0; +77,4) mm, sem rotação** (`TRANSF_STEP_PARA_SCRIPT`).
- **H3**, Y espelhado: mesmo resíduo de H2, porque o chassi é simétrico. Fica descartada só pelo nome dos braces
  (inferência).

Evidências independentes do ajuste (o ajuste usa só o FH):

1. **[código]** O ponto LR (−199,3; 228,7; 139,1) cai a 14,2 mm do eixo do FH, ou seja, a 1,5 mm da superfície do tubo.
   O ponto UR (−189,5; 305; 243,4) tem X igual ao da face dianteira do tubo do FH (−189,3) e fica a 22,7 mm do eixo.
   Os dois pontos traseiros das bandejas "sentam" no FH. **[inferência]** Isso apoia o ΔX. É indício, não prova:
   eles podem ter sido postos ali por causa do próprio FH0/FH1.
2. **[código]** O FBH do CAD tem o eixo em X = 494,9 e as faces em 482,4 e 507,4, contra `X_FBH = 490` no script:
   **4,9 mm de diferença**. O 490 cai dentro da espessura do tubo, entre a face traseira e o eixo. Ou o FBH andou
   depois, ou o 490 é outra referência. Não dá para saber pelo arquivo.
3. **[cálculo]** O ΔZ (+77,4) só tem o FH como fonte. Com ele, a face inferior do tubo de base do MH fica a 64,7 mm do
   chão e a do FH a 118,6 mm. **[inferência]** Valores plausíveis para altura do chão, mas o STEP não tem chão, roda nem
   eixo dianteiro, então nada fecha o Z de forma independente.

Conclusão: a transformação fecha com confiança em X e Y. Em Z depende de o FH0/FH1 do script estar certo, com erro
residual ≤ 0,55 mm contra ele. ΔX = −942 também significa que o eixo dianteiro está 942 mm à frente do MH. Esse dado
vem do script, não do CAD.

## 6. Confronto com a v20

A v20 foi obtida por `avaliar(carregar_x(), corner(), True)` e `varrer` em 25 pontos de −23 a +62,4 mm **[código]**:

- custo 0,073; MR 1,401; variação de MR de 5,19 %; erro ao FH de 8,0 mm (o mesmo que o REGISTRO).
- Pontos no script (lado esquerdo): Pv (−57,0; 290,2; 476,0); C (152,8; 266,7; 493,1); Q (−202; 277,2; 434,0);
  E (490; 199,7; 490,5); normal n (0,019; 0,693; 0,720).

### 6a. Pontos → tubo e nó mais próximos

**[código]** O lado direito é o espelho em Y e dá números idênticos (outra conferência da simetria).

| ponto (esq.) | tubo mais próximo | distância ao eixo (mm) | distância à superfície (mm) | nó mais próximo | distância (mm) | triangulado? |
|---|---|---|---|---|---|---|
| LF | FH | 324,6 | 311,9 | N09 | 325,1 | sim |
| **LR** | FH | **14,2** | 1,5 | N09 | **32,3** | sim |
| UF | FH | 299,0 | 286,3 | N12 | 303,4 | sim |
| **UR** | FH | **22,7** | 10,0 | N12 | **32,8** | sim |
| TI | FH | 140,4 | 127,7 | N09 | 141,5 | sim |
| Pv (pivô do rocker) | FH | 147,2 | 134,5 | N11 | 180,6 | não (triangulado mais próximo: N10, a 237,3) |
| C (olhal do amortecedor) | braceFBHesq | 97,3 | 84,8 | N04 | 363,6 | sim |
| Q (início do tubo) | FH (lado reto) | 7,5 | −5,2 (eixo dentro do FH) | N11 | 65,0 | não (N12 a 208,9) |
| E (fim do tubo) | braceFBHesq | 62,9 | 50,4 | N04 | 66,7 | sim |

**[inferência]**

- LR e UR estão no FH, a cerca de 32 mm de nós triangulados (N09 e N12), mas não em cima deles.
- LF, UF, TI, Pv e C não têm nenhum tubo a menos de 97 mm. É a consequência direta da caixa dianteira ausente no CAD.
- Q cai no lado reto do FH, 65 mm acima do nó N11 (não triangulado), ou seja, no meio de um tubo sem nó.

### 6b. Folgas (superfície a superfície) ao longo do curso

Peças e raios do script: push rod O–A (R 8), braços do rocker Pv–A e Pv–B (R 12), pivô (esfera R 20) e amortecedor
B–C (R 25). Os tubos usam o raio real: 12,7 nos redondos; nos quadrados, a meia-diagonal de 17,7 (conservador) e
também a meia-largura de 12,5 (folga entre faces). Os dois lados foram checados contra os 23 corpos de tubo, em 25
pontos de curso. **[código]**

| peça | tubo mais crítico | folga mínima (conservadora / faces), mm | curso dz (mm) |
|---|---|---|---|
| amortecedor B–C | braceFBH | **33,0** / 38,2 | −8,8 |
| rocker Pv–B | braceFBH | 46,0 / 51,2 | −8,8 |
| rocker Pv–A | FH | 47,1 | +48,2 |
| push rod O–A | FH | 51,1 | +48,2 |
| pivô Pv | FH | 114,5 | −23 |

**Nenhuma interferência** com os tubos que existem no STEP: a menor folga é 33 mm. **[inferência]** Isso só diz que a
v20 não bate no que está desenhado. A região onde a v20 fica, entre o FH e o FBH abaixo dos braces, está vazia no CAD.
As folgas reais dependem dos tubos que faltam.

### 6c. FH do script × CAD; tubo Q–E × tubos existentes

- **[código]** FH0 e FH1 do script ficam a 0,45 e 0,55 mm do eixo do lado reto do FH do CAD: as diferenças são
  (0; −0,43; −0,16) e (0; −0,53; +0,13) mm. O "lado reto do FH" do script **coincide** com o do CAD, dentro do
  arredondamento.
  - Ressalva: a translação foi ajustada nesse mesmo par. Só a coincidência de direção (0,014°) e de comprimento
    (0,3 mm) é evidência independente.
- **[código]** Q fica a 7,5 mm do eixo do FH do CAD, dentro do limite de 8 do script. Como o tubo tem R 12,7, o eixo
  de Q–E entra no FH: é o encontro pretendido, não um conflito. O ângulo Q–E × FH é 84,6°.
- **[código]** Q–E não cruza nem coincide com nenhum outro tubo. O mais perto é o `braceFBH` do mesmo lado:
  - eixos a 48,0 mm, perto de X ≈ 378 no script (a 585 mm de Q ao longo do tubo), com 21° entre eles;
  - folga de superfície de 22,8 mm contra as faces do quadrado, ou 17,6 mm contra a meia-diagonal.
  - **[inferência]** O tubo proposto corre quase paralelo ao brace superior e logo abaixo dele, numa faixa estreita.
- **[código]** **E não cai no FBH.** E = (490; 199,7; 490,5) fica fora do quadro do FBH, cujos eixos vão de Y −155 a 155
  e de Z 131,3 a 441,3. Está 44,7 mm para fora em Y e 49,2 mm acima do eixo superior. O nó mais próximo é N04 (canto
  superior esquerdo do FBH com o brace), a 66,7 mm. Como o script prolonga o tubo só até `X_FBH`, sem olhar o
  contorno do FBH, o "fim no FBH" da v20 é na verdade um ponto no ar à frente do canto do FBH.

## 7. Limitações

- O CAD está incompleto (o usuário avisou). Todo "não há tubo ali" é fato do arquivo, não do carro. Faltam a caixa
  dianteira (trilhos inferiores e laterais FH–FBH, tubos na altura das bandejas), o gabarito T.1.2, o chão, as rodas e
  as bandejas.
- O Z da transformação depende só do FH0/FH1 do script. O X tem só um indício independente (LR e UR no FH) e uma
  discrepância de 4,9 mm no FBH.
- Tubo quadrado: a "distância ao eixo" é a mesma métrica dos redondos. A folga usa a meia-diagonal (conservadora) e a
  meia-largura; a orientação real das faces não entra na folga.
- O extremo de um trecho reto vem da extensão da face cilíndrica. Em canto vivo ele passa alguns mm do vértice virtual
  (ex.: 4,6 mm na base do FH). Para tabela de dobra, use a `polilinha_virtual_mm`.
- O critério de "triangulado" é geométrico (≥ 3 ramos não coplanares), não estrutural. Ele não verifica se os tubos
  formam triângulos fechados nem a rigidez. Os "sim" de N25/N27 vêm da perna de 28 mm do "tubo orelhas pack": a
  travessa cai dentro da janela de amostragem de 20 a 45 mm e conta como um ramo a mais. É artefato.
- Membros de tubo quadrado são achados pelos planos-médios de faces opostas mais teste de ponto dentro do sólido
  (passo de 2 mm). Seções não retangulares, chapas dobradas e perfis abertos caem em "outro" ou "chapa".
- As orelhas do pack foram classificadas como "suporte" (furo Ø8). A face de B-spline delas não foi analisada.
- O script do Murilo foi tratado como dado: os números da v20 vêm dele sem alteração. Não validei o `kinlib`.

## 8. O que um script de posicionamento precisa do CAD que este STEP ainda não tem

1. **A caixa dianteira entre o FH e o FBH**: trilhos inferiores, laterais (side impact dianteiro), tubos na altura das
   bandejas e o suporte da coluna e da cremalheira. Sem eles não há nó candidato para LF, UF, TI, Pv nem C. Hoje o nó
   triangulado mais próximo de Pv está a 237 mm.
2. **Referências de montagem com nome**: um ponto ou sistema de coordenadas "eixo dianteiro, linha de centro, chão"
   (ou, no mínimo, o chão e o centro da roda), para fechar o Z e o X sem depender de FH0/FH1. Um sketch de eixo ou um
   *construction point* nomeado no Fusion entra no STEP como `AXIS2_PLACEMENT`/`CARTESIAN_POINT` com nome.
3. **A posição definitiva do FBH** em relação ao script: hoje há 4,9 mm entre `X_FBH = 490` e o eixo do FBH no CAD.
4. **O gabarito T.1.2 (e o do cockpit)** como corpos ou sketches, para checar empacotamento contra a geometria real,
   em vez do polígono 350 × 350 com topo em Z 550 fixo.
5. **As bandejas, o tirante, a manga e o aro/disco/pinça** como corpos (ou pelo menos os hardpoints como pontos com
   nome), para a folga ser checada contra a geometria real e não só contra cilindros supostos.
6. **Nome e convenção dos corpos**: nomes do tipo `Body85` não dizem a função. Um prefixo (ex.: `FH_`, `SIDE_`,
   `BRACE_`) ou componentes por grupo deixariam o script reconhecer FH, FBH, trilhos e braces sem heurística. Ajuda
   também ter os tubos modelados até o eixo do outro tubo (como os Body87 a 94) ou com boca de lobo consistente.
7. **Espessura e material** declarados por corpo (hoje saem da geometria: Ø25,4 × 2,65, × 1,9 e × 1,2; quadrado
   25 × 1,2). Isso é necessário quando o método passar a considerar esforço nos nós.
8. **Os pontos de fixação já decididos** (orelhas e suportes da suspensão), para o script tratá-los como restrição e
   não como incógnita.
