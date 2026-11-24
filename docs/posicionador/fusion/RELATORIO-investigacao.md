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
