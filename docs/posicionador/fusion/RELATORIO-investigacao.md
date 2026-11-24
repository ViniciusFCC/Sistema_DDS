# Fase 2 (Fusion): relatório da investigação inicial

Data: 2026-11-24. Máquina do usuário (Windows 11). Roteiro: `ROTEIRO-investigacao.md`.
**Só leitura:** nada do Fusion, do CAD nem do posicionador foi alterado. A única escrita fora do repositório foi criar a pasta do
script de sondagem em `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\T11_sondagem\` (o que o roteiro manda).

**Estado das etapas:** A e B feitas e medidas (B em 2026-11-24, seção 2). C é este relatório. Restam as linhas "a confirmar" da seção 3.

Convenção: `B` = `%LOCALAPPDATA%\Autodesk\webdeploy\production\39e8a3d5e919c70b05ef3ebfe9c6bfc8d9ee001e`;
`U` = `%APPDATA%\Autodesk\Autodesk Fusion 360`.

## 1. Fatos medidos (Etapa A)

| # | Fato | Valor | Fonte / comando |
|---|---|---|---|
| 1 | Versão do Fusion | **2706.1.17** (branch `release/2706.1`) | `B\fusion_version.txt`, `B\version.json`, `U\API\version.txt` |
| 2 | Pasta da instalação ativa | `B` (hash `39e8a3d5…`); as outras 3 de `production\` têm ícones/`FusionLauncher.exe`, safe mode e cache de documentos (`FusionDocStream`), sem `Python` | `ls …\webdeploy\production` |
| 3 | Fusion em execução durante a medida | não (0 processos "fusion") | `tasklist` |
| 4 | Python embutido | **3.14.7** (`python314.dll`) | `B\Python\python.exe --version` |
| 5 | `site-packages` do Python do Fusion | só `README.txt` e `speedtest.py`: **sem numpy, sem scipy, sem OCP, sem cadquery** | `ls B\Python\Lib\site-packages`; `find` por `numpy*/scipy*/OCP*/cadquery*` em todo `B` e em `U`: 0 resultados |
| 6 | pip | `ensurepip` com `pip-26.2.1` empacotado; **não foi executado** | `ls B\Python\Lib\ensurepip\_bundled` |
| 7 | Módulo `adsk` | `B\API\Python\packages\adsk\` (`_core.pyd`, `_fusion.pyd`, `_cam.pyd`, …; `.py` por módulo) | `ls` |
| 8 | Stubs `.py` com assinaturas e docstrings | `B\API\Python\packages\adsk\defs\adsk\{core,fusion}.py` (usei estes, da build 2706). Há outra cópia em `U\API\Python\defs\adsk\` com data de 27/10: pode ser de build mais antiga, não usei | `ls`, `grep` |
| 9 | Pastas de scripts e add-ins do usuário | `U\API\Scripts` e `U\API\AddIns` (ambas **vazias** antes da sondagem). **O roteiro cita `Autodesk Fusion`; o nome real da pasta é `Autodesk Fusion 360`** | `ls` |
| 10 | Precisa de administrador? | Não para criar scripts: a pasta fica em `%APPDATA%` e a criação funcionou sem elevação | `mkdir` feito sem prompt |
| 11 | Outras versões já usadas na máquina | arquivos `Fusion360_2602…`, `2704…`, `2705…`, `2706…` em `U` | `ls U` |
| 12 | Evidência de Python mais antigo em builds anteriores | `U\MyScripts\Samples\__pycache__` tem `.cpython-312.pyc` e `.cpython-314.pyc` (inferência: o Python embutido já mudou de versão entre builds; não verificado de outra forma) | `ls` |

### API relevante (nos stubs da build 2706; assinaturas lidas, nada executado)

| Classe (arquivo:linha) | O que serve ao posicionador |
|---|---|
| `core.MeasureManager` (core.py:8762) | `measureMinimumDistance(geometryOne, geometryTwo) -> MeasureResults` (`.value`, `.positionOne`, `.positionTwo`; **em cm**); `measureAngle`; `getOrientedBoundingBox`. Aceita Occurrence, BRepBody, BRepFace, BRepEdge, BRepVertex, ConstructionPlane/Axis/**Point**, entidades de croqui. **Geometria temporária só é aceita se for `Plane` ou `Point3D`** (docstring), isto é, corpo temporário do `TemporaryBRepManager` **não** consta como suportado: precisa de teste (Etapa B). |
| `fusion.TemporaryBRepManager` (fusion.py:41015) | `createCylinderOrCone`, `createSphere`, `createBox`, `createTorus`, `copy`, `transform`, `booleanOperation(target, tool, tipo)` (alvo tem que ser temporário), `planeIntersection`, `createFromFile`, `exportToFile`. |
| `fusion.BRepBody` (fusion.py:5538) | `pointContainment(point)`, `getPhysicalProperties`, `isSolid`, `isTemporary`, `volume`. |
| `fusion.ConstructionPoint` (fusion.py:12356) | `name`, `geometry` (Point3D), `isParametric`: dá para ler os `REF_`. |
| `fusion.UserParameters` (fusion.py:44654) | `item`, `itemByName`, `add`, `asArray`, `exportUserParameters`, `importUserParameters`. |
| `fusion.Design.analyzeInterference(InterferenceInput)` (fusion.py:54693) | interferência entre BRepBody/Occurrence no contexto do componente raiz (a docstring de `entities` não menciona corpos temporários: a confirmar). |
| `fusion.Occurrence` (27421), `fusion.Sketch` (36876) | leitura de ocorrências e croquis. |

## 2. Etapa B: medido dentro do Fusion (2026-11-24)

Executada no T11 aberto (`T11_atuacao_v20_1_murilo_teste`, modo Design) com `T11_sondagem`, em *Utilities > Scripts and Add-Ins*. Só leitura: nada foi salvo nem
alterado no T11. Saída bruta: `fusion_sondagem_2026-11-24.json` (cópia do `C:\Projetos\fusion_sondagem.json`). O script terminou (`concluido: true`).

| # | Fato | Valor medido | Chave no JSON |
|---|---|---|---|
| 13 | Python em execução no script | 3.14.7 (MSC v.1944, AMD64), executável `Fusion360.exe` | `python` |
| 14 | numpy, scipy, OCP, cadquery, pip, setuptools | **nenhum importável** (`ModuleNotFoundError`) | `bibliotecas` |
| 15 | Modelo T11 | 46 componentes e 46 ocorrências; **320 corpos sólidos** (o script listou 200); tubos do chassi são corpos reais (ex.: `braceFBHdir` em `CHASSI_T11_V20:1+CHASSI_V20_TUBOS:1`) | `design`, `corpos` |
| 16 | Pontos de construção `REF_` na raiz | **0** (0 pontos de construção no total) | `pontos_de_construcao` |
| 17 | Parâmetros do usuário | 0 | `parametros_do_usuario` |
| 18 | Croquis na raiz | 0 | `croquis_e_planos` |
| 19 | `measureMinimumDistance` corpo×corpo | **1,14 ms** em média (200 chamadas; valor em cm) | `medida_distancia_minima` |
| 20 | `measureMinimumDistance` ponto×corpo | **0,36 ms** em média (200 chamadas) | `medida_distancia_ponto_corpo` |
| 21 | Cilindro temporário (`TemporaryBRepManager.createCylinderOrCone`) | criado (`isTemporary` verdadeiro); **0,04 ms** em média (200) | `corpo_temporario_na_api` |
| 22 | `measureMinimumDistance` temporário × corpo real | **aceito** (a docstring dizia que não); **0,42 ms** em média (200) | idem |
| 23 | `booleanOperation` de interseção entre temporários | executou sem erro; resultado sem volume (não houve interseção no par testado) | idem |
| 24 | `analyzeInterference` | 4,7 ms em **1** chamada (par `gabarito_T1_2_350x350` × `braceFBHdir`, 0 interferências) | `analyzeInterference` |
| 25 | Documentos abertos | 24 (as peças do T11 aparecem como documentos abertos, todos salvos e sem modificação) | `documentos` |

Defeito do script: a etapa `fusion` falhou com `AttributeError: 'Application' object has no attribute 'name'`, então a versão do Fusion **não** saiu no JSON
(vale a do fato 1, 2706.1.17, lida de arquivo). Corrigido nesta versão do script (linha `productName` removida); a correção não foi reexecutada.

## 3. O que ainda é desconhecido (a confirmar)

| Pergunta | Estado |
|---|---|
| Onde estão os pontos de referência (`REF_`, `HP_`)? | A raiz não tem nenhum. O T11 tem as ocorrências `REF_REFERENCIAS`, `HP_FRENTE` e `IGNORAR_PONTOS_V20_11`: **a confirmar** se ali são pontos de construção, pontos de croqui ou esferas (a sondagem só varreu a raiz). |
| Tempo de `measureMinimumDistance` entre pontos de construção | não medido (menos de 2 pontos na raiz) |
| Custo da `booleanOperation` e de `analyzeInterference` com geometria do chassi | `booleanOperation` sem tempo medido; `analyzeInterference` só 1 chamada, em par de corpos sem interferência |
| `measureMinimumDistance` com corpo temporário contra **componente inteiro** ou contra o conjunto dos 320 corpos | a confirmar (medido só contra um corpo) |
| O add-in (diferente do script) tem o mesmo Python e as mesmas bibliotecas? | a confirmar |
| `pip install` de numpy sobreviveria a uma atualização do Fusion? | a confirmar; não tentado (não há pip no Python do Fusion, fato 14) |
| Distribuição em outra máquina | não testada |

## 4. Recomendação de arquitetura (PROPOSTA, não decisão)

1. **Sem scipy nem numpy no add-in** (fatos 5 e 14, agora confirmados em execução). Núcleo em Python puro (`math`, listas e tuplas), com bisseção própria no lugar do `brentq` e Nelder-Mead próprio (R9); vendorizar numpy só se o Python puro se mostrar lento.
2. **Distância mínima pela API.** Custo medido ~1 ms (fatos 19 a 22) é compatível com milhares de avaliações por busca. Como o corpo temporário é aceito (fato 22), o elemento móvel pode ser um cilindro temporário medido contra os corpos reais do chassi, sem precisar do OCP. A contradição com a docstring significa que o comportamento deve ser coberto por teste de regressão no add-in (pode mudar entre builds).
3. **Leitura do T11:** os `REF_` não estão na raiz; antes de projetar a leitura, varrer as ocorrências citadas na seção 3. Unidades da API em cm, convertidas para m na fronteira (convenção SI do núcleo).
4. **Núcleo testável fora do Fusion:** módulo Python puro (sem `import adsk`); add-in como camada fina.
5. **Instalação:** `U\API\AddIns\<nome>\` ou `Scripts\`, sem administrador (fato 10).

## 5. Próximo passo sugerido

Estender a sondagem para varrer as ocorrências `REF_REFERENCIAS`, `HP_FRENTE` e `IGNORAR_PONTOS_V20_11` (pontos de construção, croquis, corpos) e medir `measureMinimumDistance` contra o conjunto dos corpos do chassi. Ainda só leitura.

## 6. Sondagem estendida e reconhecimento de componentes (2026-11-24, segunda execução)

Script `T11_sondagem` v0.2, mesma regra (só leitura; nada salvo nem alterado). Saída bruta: `fusion_sondagem2_2026-11-24.json`. Executou até o fim (`concluido: true`, nenhuma etapa com erro).

### 6.1 Correção do relatório: os pontos `REF_` e `HP_` existem, como esferas

Na seção 2 (fatos 16 e 17) a contagem de zero `REF_` valia só para **pontos de construção na raiz**. Dentro das ocorrências, os pontos estão como **corpos esféricos** (1 face, raio 2,5 mm = Ø5 mm):

| Ocorrência | Conteúdo medido |
|---|---|
| `REF_REFERENCIAS:1` | `REF_ORIGEM` (1002,0; 0,0; −141,57 mm no CAD), `REF_X` (+100,0 mm em X) e `REF_Y` (+100,0 mm em Y): distâncias nominais de 100 mm e eixos ortogonais, como o documento de exportação pede |
| `HP_FRENTE:1` | 18 esferas `HP_FL_*` e `HP_FR_*` (9 de cada lado: `LCA_IN_F`, `LCA_IN_R`, `LCA_OUT`, `TIE_IN`, `TIE_OUT`, `UCA_IN_F`, `UCA_IN_R`, `UCA_OUT`, `WHEEL_CENTER`) |
| `IGNORAR_PONTOS_V20_1:1` | não varrida: o nome real termina em `V20_1`, não `V20_11` (erro de transcrição do roteiro; está na lista de componentes reconhecidos) |

Nenhuma dessas ocorrências tem pontos de construção nem croquis. Os centros das esferas saem da face esférica (`Sphere.origin`), não do centro da caixa envolvente.

Conferência com `data/posicionador/hardpoints_T11_v20_script.csv` (coordenadas do CAD menos `REF_ORIGEM`, sem rotação, porque `REF_X` e `REF_Y` são paralelos aos eixos do CAD; conferido só pelos 9 pontos `FL`):
`FL_LCA_OUT`, `FL_UCA_OUT` e `FL_WHEEL_CENTER` batem exatamente (0,0 mm); `FL_TIE_IN` e `FL_UCA_IN_F` diferem 0,18 mm; os outros quatro diferem de 7,6 a 20,6 mm (`FL_TIE_OUT` 7,6; `FL_UCA_IN_R` 13,0; `FL_LCA_IN_F` 14,8; `FL_LCA_IN_R` 20,6). Interpretação **a confirmar**: o CAD é posterior ao CSV do script (v20); isto não foi investigado. O CSV não tem pontos `FR` e tem 8 pontos que o CAD não traz (`PUSH_IN/OUT`, `ROCKER_*`, `SPRING_*`, `SPINDLE_PT`, `CONTACT_PATCH`): são os da atuação, que o posicionador deve calcular.

### 6.2 Reconhecimento de componentes pelo nome (funcionalidade nova)

Motivo: os componentes do T11 não seguem em tudo os nomes do documento de exportação. O módulo `python/posicionador/reconhecimento.py` (só biblioteca padrão, roda no Python 3.13 dos testes e no 3.14 do Fusion) classifica cada componente de primeiro nível e diz **com que confiança**:

| Nível | Regra | Usável sem confirmação? |
|---|---|---|
| `exata` | prefixo do documento, sensível a caixa (os mesmos de `cad_step.PREFIXOS`) | sim |
| `normalizada` | igual, ignorando caixa, acento, espaço e hífen | sim |
| `mapa` | decisão do usuário em `C:\Projetos\mapa_componentes.json` (`{"nome": "CATEGORIA"}`); vence qualquer regra | sim |
| `inferida` | palavras-chave (TIRANTE, WISHBONE, PUSHROD, lado FE/FD...) | **não**: é sugestão |
| `nao_reconhecido` | nenhuma regra serviu (sem categoria inventada) | não |

Cuidado de projeto: o leitor de STEP trata nome sem prefixo como `FIXO` (obstáculo). Uma peça da suspensão sem nome reconhecido viraria obstáculo e colidiria, por isso `nao_reconhecido` traz `padrao_se_ignorado: "FIXO"`. O resumo devolve `a_confirmar`, `nao_reconhecidos` e `modelo_de_mapa` (esqueleto de JSON já com as sugestões, para o usuário corrigir).

Resultado no T11 aberto (31 ocorrências de primeiro nível): **31 `exata`**, 0 normalizada, 0 inferida, 0 não reconhecida. Por categoria: IGNORAR 20, DIR 2, BANDEJA_FE 2, BANDEJA_FD 2, CHASSI 1, RODA_FE 1, RODA_FD 1, REF 1, HP 1. Ou seja, **no nível dos componentes o T11 já segue o documento**; as regras de normalização e inferência existem para versões futuras do modelo e não foram exercitadas no CAD real (só nos testes com nomes sintéticos). Se a divergência que o usuário percebe estiver em outro nível (nomes dos corpos dentro dos componentes, nomes dos `HP_` contra as chaves do schema), o reconhecimento ainda não cobre isso: ver 6.4.

Testes: `tests/test_posicionador_reconhecimento.py`, 5 PASS (inclui os nomes reais do T11 lidos do JSON, o mapa do usuário e a igualdade com `cad_step.PREFIXOS`; a cópia do módulo em `T11_sondagem/` é conferida por SHA-256). Registrado em `tools/rodar_testes.py`. **Sem ID de TC**: prefixo e numeração aguardam autorização do usuário.

### 6.3 Desempenho da API com geometria do chassi

| Medida | Resultado |
|---|---|
| Cilindro temporário × 27 corpos do chassi (5 varreduras) | 9,4 ms por varredura (0,35 ms por corpo) |
| Cilindro temporário × os 320 sólidos (3 varreduras) | 618 ms por varredura (1,9 ms por corpo) |
| Cilindro temporário × **ocorrência inteira** `CHASSI_T11_V20` | **falha**: `RuntimeError: 3 : measurement failed` (a medida contra componente inteiro não funciona; é preciso medir corpo a corpo) |

Implicação (proposta): medir contra a lista de corpos relevantes e, se preciso, filtrar antes por caixa envolvente; 320 corpos por candidato custariam ~0,6 s, caro para milhares de avaliações.

### 6.4 Ainda a confirmar

- Que divergência de nomes o usuário vê (a sondagem acha os 31 componentes corretos); pedir um exemplo para decidir se o reconhecimento deve cobrir nomes de corpos ou chaves `HP_`.
- Diferenças de 7 a 21 mm entre o CAD e o CSV do script em quatro hardpoints `FL` (6.1).
- Rotação do referencial `REF_` em relação ao CAD (aqui assumida nula pelos eixos paralelos medidos).
- Custo de `analyzeInterference` com o conjunto e de `booleanOperation` com geometria do chassi.

## 7. Verificação da identificação por geometria (2026-11-24, terceira execução)

Motivo (pedido do usuário): não pode haver erro na identificação dos componentes. O nome sozinho não basta (um componente `BANDEJA_FE_*` poderia conter a peça do lado direito, e uma peça marcada `IGNORAR` some da colisão sem alarme). O módulo `python/posicionador/identificacao.py` confere o resultado do reconhecimento **pela geometria**, e a ferramenta `tools/verificar_identificacao.py` é o portão: código de saída 0 só sem `FALHA`; qualquer `FALHA` bloqueia o uso do modelo.

Dados: `fusion_sondagem3_2026-11-24.json` (etapa `geometria_por_componente`: 46 ocorrências, 31 componentes de 1º nível, caixa envolvente de cada corpo em mm). Referencial do carro construído das esferas `REF_` (origem, X, Y por Gram-Schmidt, a mesma construção de `cad_step`); lado esquerdo = +Y, direito = −Y (ISO 8855).

### 7.1 O que é verificado

| Código | Gravidade | O que confere |
|---|---|---|
| `IDENT-NOME` | FALHA | nome que não é `exata`, `normalizada` nem decidido no mapa (a decisão é do usuário) |
| `REF` | FALHA | esferas `REF_ORIGEM/X/Y` presentes, a 100 ± 0,5 mm e a 90 ± 0,1° |
| `CONTAGEM` | FALHA | componentes por categoria: 2 bandejas por lado, 1 roda por lado, 2 tirantes (um por lado), 1 `REF`, 1 `HP`, ao menos 1 `CHASSI` |
| `LADO` | FALHA (usada) / AVISO (`IGNORAR`) | o lado do nome (FE/FD) bate com o sinal de Y do centro da caixa (margem de 20 mm) |
| `SEM-CORPO` | FALHA (usada) / AVISO (`IGNORAR`) | componente sem nenhum corpo |
| `ESFERA`, `HP-NOME`, `HP-LADO` | FALHA | esferas `REF_`/`HP_`: 1 face esférica, raio 2,5 ± 0,05 mm, nome `HP_FL_<chave>`/`HP_FR_<chave>`, lado pelo sinal de Y |
| `HP-ESPELHO` | AVISO | par FL/FR não espelhado em Y (0,5 mm) ou sem par |
| `IGNORAR-CHASSI` | FALHA (AVISO se traseira) | componente ou ocorrência `IGNORAR` com nome de chassi/tubos |
| `IGNORAR-CORPO-SUSPEITO` | AVISO | corpo com nome de chassi/tubo dentro de `IGNORAR` (a conferir) |
| `LADO-ANINHADO` | FALHA (pai usado) / AVISO (pai `IGNORAR`) | subcomponente com lado no nome do lado errado |
| `ANINHADO-CONFLITO` | AVISO | subcomponente cujo nome diz outra categoria que a do pai |

### 7.2 Resultado no T11 real: **0 falhas**, 9 avisos

- **Lados confirmados pela geometria** em todas as peças usadas: bandejas FE em Y = +420,7 e +447,9 mm, FD em −420,7 e −447,9; rodas ±650,0; tirantes ±392,1. As 18 esferas `HP_` têm raio 2,5 mm e `FL` em +Y, `FR` em −Y.
- Contagens batem: 2+2 bandejas, 1+1 rodas, 2 tirantes, 1 `REF`, 1 `HP`, 1 `CHASSI` (27 corpos).
- **Avisos reais para o usuário revisar:**
  1. `IGNORAR_PONTOS_V20_1` e `IGNORAR_PLANOS` não têm corpo nenhum (vazios).
  2. Dentro de `IGNORAR_TRASEIRA`, os subcomponentes `RODA_FE_ARO_13X7_TX:3` e `:4` têm nome de **roda dianteira esquerda**, mas são rodas traseiras, e o `:3` está em **Y = −650 mm (lado direito)**: nome errado nos dois sentidos (dianteira/traseira e esquerda/direita). Sem efeito hoje, porque o pai é `IGNORAR`, mas é erro de nome real e quebraria qualquer leitor que desça aos subcomponentes. Recomendo renomear no CAD.
  3. Corpos `TUBO_CARBONO_16x13` nos pushrods (dianteiros e traseiros) dentro de `IGNORAR`: são tubos de carbono do pushrod, não do chassi (conferido pelo nome do componente e pelas dimensões 26 × 238 × 190 mm); fica como aviso porque nome de corpo é evidência fraca.
- **O que o usuário ainda precisa revisar à mão:** `tabela_ignorados` (saída do verificador) lista, com caixa envolvente no referencial do carro, tudo o que está `IGNORAR`: gabarito, atuação dianteira, traseira inteira, amortecedores, pushrods, rockers, toe links e bandejas traseiros. O verificador **não sabe** se algo ignorado deveria ser obstáculo; só confere que nenhum nome de chassi está ali. Isso é decisão de projeto e não foi validado.

Ajuste de regra feito durante a execução (evidência: falso positivo no real): a primeira versão bloqueava por nome de **corpo** com a palavra TUBO, e reprovou os pushrods por causa do `TUBO_CARBONO`. Agora nome de componente/ocorrência bloqueia e nome de corpo só avisa. A regra do nome de corpo ficou mais fraca de propósito; o risco é um corpo do chassi mal agrupado dentro de um `IGNORAR` com nome inocente passar sem bloqueio (só o aviso por palavra-chave o levantaria).

### 7.3 Testes

`tests/test_posicionador_identificacao.py`: 13 PASS (1 com os dados reais, 12 mutações). Cada mutação injeta um erro de identificação nos dados reais e exige o código certo: bandeja FE no lado direito, bandeja a menos, chassi renomeado para `IGNORAR_`, `REF_X` a 120 mm, `HP_FL` no lado direito, nome irreconhecível, componente usado sem corpos, esfera `HP` com raio 3 mm, subcomponente de roda no lado errado, ocorrência com nome de chassi em `IGNORAR`; mais a assimetria de 5 mm nos `HP` (só aviso) e a resolução de nome pelo mapa. Sem ID de TC (aguarda autorização). Registrados em `tools/rodar_testes.py`.

### 7.4 Limites (não verificados)

- O lado é decidido pelo centro da caixa envolvente: peça atravessando o plano central dá falha por ambiguidade (não ocorreu).
- A verificação dos nomes de corpos dentro dos componentes de 1º nível não existe além das esferas `REF_`/`HP_`.
- As contagens esperadas assumem duplo A com um tirante por lado; outra arquitetura exige mudar `CONTAGEM_ESPERADA`.
- Rotação do referencial `REF_` assumida pela construção do `cad_step`; o T11 atual tem eixos paralelos aos do CAD (medido).
- Executado só com o T11 atual, num único modelo.
