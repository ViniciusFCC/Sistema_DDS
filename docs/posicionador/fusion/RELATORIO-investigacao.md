# Fase 2 (Fusion): relatório da investigação inicial

Data: 2026-11-24. Máquina do usuário (Windows 11). Roteiro: `ROTEIRO-investigacao.md`.
**Só leitura:** nada do Fusion, do CAD nem do posicionador foi alterado. A única escrita fora do repositório foi criar a pasta do
script de sondagem em `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\T11_sondagem\` (o que o roteiro manda).

**Estado das etapas:** A feita e medida. B **pendente**: o script está pronto e instalado, mas só roda com o T11 aberto no Fusion
(uma ação do usuário, descrita no fim). C é este relatório; as linhas marcadas "a confirmar" dependem da B.

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

## 2. O que ainda é desconhecido (a confirmar)

| Pergunta do roteiro | Estado |
|---|---|
| Existem pontos `REF_` no T11? Quais nomes e coordenadas? | **a confirmar** (B) |
| Quantos corpos tem o T11; os tubos do chassi são corpos sólidos? | **a confirmar** (B) |
| Parâmetros do usuário do T11 | **a confirmar** (B) |
| Tempo de uma chamada de `measureMinimumDistance` (corpo×corpo, ponto×corpo, ponto de construção×ponto) | **a confirmar** (B); o roteiro pede a média de 200 chamadas |
| `measureMinimumDistance` aceita corpo temporário de `TemporaryBRepManager`? | docstring diz que não; **a confirmar** (B tenta e registra o erro) |
| Custo de criar cilindro temporário e de `booleanOperation` de interseção | **a confirmar** (B) |
| Custo de uma `analyzeInterference` | **a confirmar** (B) |
| O add-in (diferente do script) tem as mesmas bibliotecas e o mesmo Python? | **a confirmar**; os scripts e os add-ins rodam no mesmo interpretador embutido, mas isso não foi medido |
| `pip install` de numpy no Python do Fusion funcionaria atrás do Norton, e sobreviveria a uma atualização do Fusion? | **a confirmar**; não foi tentado (roteiro proíbe instalar). Risco conhecido: o Python fica numa pasta com hash da build, que muda a cada atualização |
| Pontos do CAD que o STEP não trouxe (`REF_`): estão como ConstructionPoint ou como pontos de croqui? | **a confirmar** (B lista só ConstructionPoint) |

## 3. Recomendação de arquitetura (PROPOSTA, não decisão; vale só até a Etapa B confirmar os tempos)

1. **Sem scipy nem numpy dentro do add-in.** Fato 5: o Python do Fusion não tem nenhum dos dois, e o `site-packages` mora na pasta da build.
   Proposta: o núcleo que roda no Fusion usa só a biblioteca padrão do Python 3.14 (`math`, listas e tuplas), com bisseção própria no lugar do
   `brentq` e um Nelder-Mead próprio (R9). Antes de decidir, medir se o custo em Python puro é aceitável; só então considerar vendorizar numpy
   dentro da pasta do add-in (wheel para Python 3.14 win_amd64, a confirmar disponibilidade), o que também não depende de escrever no `site-packages` da build.
2. **Distância mínima pela API do Fusion, não pelo OCP.** `MeasureManager.measureMinimumDistance` já trabalha sobre os corpos do modelo e não exige
   biblioteca extra. Se o teste da Etapa B mostrar que ela recusa corpo temporário, a busca do posicionador deve medir contra corpos **reais** do
   modelo (chassi, tubos) e tratar o elemento móvel como pontos (`Point3D`, que é aceito) ou como geometria analítica própria (tubo = segmento + raio).
3. **Leitura do T11:** pontos `REF_` e parâmetros do usuário lidos pela API (`ConstructionPoint.geometry`, `UserParameters`), em cm convertido para m na fronteira,
   para respeitar a convenção SI do núcleo.
4. **Núcleo testável fora do Fusion:** manter a lógica do posicionador num módulo Python puro (sem `import adsk`) e deixar o add-in como camada fina que lê o
   modelo, chama o núcleo e grava o resultado. Isso preserva os testes no Python 3.13 da máquina.
5. **Instalação:** pasta `U\API\AddIns\<nome>\` (ou `Scripts\`) sem administrador (fato 10); distribuição à equipe por cópia da pasta ou por repositório. A distribuição não foi testada em outra máquina.

## 4. Etapa B: script de sondagem pronto, execução pendente

- Arquivos: `docs/posicionador/fusion/T11_sondagem/T11_sondagem.py` e `.manifest` (cópia idêntica instalada em `U\API\Scripts\T11_sondagem\`).
- Só lê. Os corpos temporários dos testes ficam em memória e não entram no documento; nada é salvo nem fechado.
- Saída: `C:\Projetos\fusion_sondagem.json`, reescrito a cada etapa (se uma etapa travar, as anteriores ficam gravadas).
- Verificado por mim: sintaxe compila (`py_compile`) e cada nome de API usado existe nos stubs da build 2706. **Não foi executado** (precisa do Fusion com o T11 aberto), então o comportamento em tempo de execução é desconhecido.
- Ação única do usuário: abrir o T11 no Fusion (modo Design) e, em *Utilities > Scripts and Add-Ins* (atalho Shift+S), selecionar `T11_sondagem` em *Scripts* e clicar em *Run*.
