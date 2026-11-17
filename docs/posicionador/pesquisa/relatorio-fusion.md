# Relatório Fusion — API Python para o programa de posicionamento da atuação (T11)

Data da checagem: 2026-11-17. Base: documentação oficial lida no próprio dia.
Base URL da referência: `https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/` (abreviada `API/` abaixo).
Rótulos: **[OFICIAL]** = página da Autodesk aberta e lida nesta checagem; **[INDÍCIO]** = fórum comunitário ou terceiro, só sinalizado; **[NÃO VERIFICADO]** = não confirmei.

Limitações desta checagem: `autodesk.com` (blog, página de educação, artigo de termos da licença) devolveu 403 a todas as ferramentas, e os fóruns da Autodesk bloqueiam leitura direta (Cloudflare/403). O que sei desses lugares vem só de trechos de resultado de busca e está marcado como INDÍCIO. O Firecrawl continua sem créditos.

---

## 1. Ambiente Python do Fusion

**Versão.** [OFICIAL] Blog de desenvolvedores da Autodesk, 8 jan 2026, "Fusion Python Upgrade and more" (`https://blog.autodesk.io/fusion-python-upgrade-and-more/`): "The first is an upgrade of the Python version used in Fusion from 3.12 to 3.14." (versão de janeiro de 2026). O post também diz que módulos compilados (`.pyc`) só servem para a versão menor que os gerou; quem entrega `.py` não é afetado. Confirmar na máquina da equipe: `import sys; print(sys.version)` no painel Text Commands (opção Python). Posts de fórum de 2023 falam em 3.11, de 2022 em 3.9: a versão muda com as atualizações.

**Pacotes de terceiros.**
- [OFICIAL] `API/PythonSpecific_UM.htm`, seção "Additional Python Modules": "The Python provided with Fusion includes only the core modules that come with a standard installation of Python. However, you can use other modules by making them available to your Python program. Instead of installing or adding the module to sys.path we recommend that you have a local copy of the module for your script. To do this you install the Python module in the same directory as your script or a subdirectory." Importação por caminho relativo: `from .Modules import xlrd`.
- Ou seja, o caminho documentado é "cópia local do módulo dentro da pasta do add-in", com import relativo. Não há menção a `pip` nem a `--target` nessa página. `pip --target` numa pasta do add-in produz a mesma estrutura (pasta de módulos ao lado do código), mas a Autodesk não documenta o comando: **[NÃO VERIFICADO]** como método oficial.
- [INDÍCIO] Threads do fórum (vi só trechos de busca): o Python do Fusion é 64 bits embutido no processo, então os pacotes binários (numpy etc.) precisam ser as versões 64 bits; a pasta do Python fica no `webdeploy` e é recriada a cada atualização, então instalar lá se perde; Autodesk (staff) desencoraja editar o Python do Fusion; um usuário relatou erro de import ao usar `pip install numpy -t <pasta>` (thread antiga); scipy assume numpy no `sys.path` e não faz import relativo; importar numpy na partida de um add-in deixa o Fusion lento (adiar o import para quando o comando rodar). Um post de 2026 diz que "funciona" com Python 3.14 mas não consegui ler o código.
- **scipy funciona?** [NÃO VERIFICADO]. Nenhuma fonte oficial nem confirmação recente. Teste prático obrigatório: baixar wheel cp314 win_amd64 (ou o ABI da versão que `sys.version` mostrar) de numpy e scipy, descompactar em `<add-in>/Modules/`, e testar `from .Modules import numpy`. Pacotes com módulos C e dependências cruzadas (scipy) são o ponto de risco. Se numpy bastar para a colisão e a busca, o risco cai.

## 2. Leitura da geometria do design

Todas [OFICIAL]. Unidades: `API/Units_UM.htm`: "Lengths - Centimeters (cm); Angles - Radians; Mass - Kilograms" (unidades de banco, sempre, independentes da unidade que o usuário vê). O STEP do T11 está em mm: converter por 0,1 ao ler a API.

| Necessidade | Classe.membro | Observação oficial |
|---|---|---|
| Raiz do design | `Design.rootComponent` | (Measure Sample e demais amostras) |
| Todas as ocorrências, qualquer nível | `Component.allOccurrences` (`API/fusion_Component_allOccurrences.htm`) | "Returns all of the occurrences in the assembly regardless of their level within the assembly structure. The returned list is read-only." |
| Corpos do componente | `Component.bRepBodies` (`API/fusion_Component_bRepBodies.htm`) | Corpos do próprio componente (raiz inclusive). |
| Corpos de uma ocorrência | `Occurrence.bRepBodies` (`API/fusion_Occurrence_bRepBodies.htm`) | "Returns the body proxies ... the bodies returned will return information in the context of the root component, not the component they actually exist in." Ou seja, proxies já em coordenadas da raiz. |
| Pose da ocorrência | `Occurrence.transform2` (`API/fusion_Occurrence_transform2.htm`) | Matrix3D "in its assembly context"; `transform` está aposentada (resultados incorretos). Desde jan/2022. |
| Contexto de montagem | `BRepBody.assemblyContext`, `BRepBody.nativeObject`, `BRepBody.createForAssemblyContext` (`API/fusion_BRepBody.htm`) | `assemblyContext` é null se o corpo já é o nativo. |
| Nomes | `Component.name`, `Occurrence.name` (`:1` no fim), `Occurrence.fullPathName`, `BRepBody.name` | `BRepBody.name`: "only valid if the IsTransient property is false". `fullPathName`: ex. `Sub1:1+Sub2:1+PartA:1`. |
| Visibilidade | `Occurrence.isVisible`, `Occurrence.isLightBulbOn`, `BRepBody.isVisible/isLightBulbOn` | Útil para ignorar peças ocultas. |
| Peça externa (link) | `Occurrence.isReferencedComponent` | Chassi vindo de arquivo referenciado aparece assim. |
| Ponto de esboço | `SketchPoint.worldGeometry` (`API/fusion_SketchPoint_worldGeometry.htm`) | "position of the sketch point in world space ... takes into account the assembly context and the position of the sketch in its parent component, ... in the root component space". `SketchPoint.geometry` é em espaço do esboço. `Sketch.sketchToModelSpace(Point3D)` e `Sketch.transform` também existem. |
| Ponto de construção | `ConstructionPoint.geometry` (`API/fusion_ConstructionPoint_geometry.htm`) | "in the AssemblyContext of this ConstructionPoint": para ponto dentro de ocorrência, precisa do proxy (contexto) para sair em espaço da raiz. Lista: `Component.constructionPoints`. |
| Esboços do componente | `Component.sketches`, `Sketch.sketchPoints` | Esboços ficam por componente; é preciso percorrer a raiz e cada `occ.component`. |
| Volume, caixa | `BRepBody.volume` (cm³), `boundingBox`, `preciseBoundingBox`, `orientedMinimumBoundingBox`, `physicalProperties` | `volume` devolve 0 se o corpo não for sólido. |

Pendente de leitura na hora de codar (não aberto): como obter o `SketchPoint`/`ConstructionPoint` de dentro de uma ocorrência já em contexto da raiz (proxy via `createForAssemblyContext` ou equivalente) e se existe atalho para "todos os esboços da montagem". **[NÃO VERIFICADO]**.

## 3. Distância mínima e interferência

**`MeasureManager.measureMinimumDistance(geometryOne, geometryTwo)`** [OFICIAL] `API/core_MeasureManager_measureMinimumDistance.htm` (desde dez/2017). Retorna `MeasureResults` com a distância e os dois pontos, "in centimeters". Parâmetros: "This can be an Occurrence, BRepBody, BRepFace, BRepEdge, BRepVertex, ConstructionPlane, ConstructionAxis, ConstructionPoint, and any sketch entity. **The temporary geometry supported are the Plane and Point3D objects.**"
- Entre quais tipos: ocorrência, corpo, face, aresta, vértice, planos/eixos/pontos de construção e qualquer entidade de esboço, mais `Plane` e `Point3D` temporários.
- Aceita corpo temporário? Pela documentação, **não**: a única geometria temporária aceita é `Plane` e `Point3D`. [INDÍCIO, não consegui abrir] Thread de fórum de 2021 ("Can't use MeasureManager.getMinimumDistance on temporary brep objects?") relata erro "invalid argument" com corpo do `TemporaryBRepManager` e contorno de adicioná-lo ao design; uma resposta posterior diria que passou a ser suportado. Como a página atual lista só Plane e Point3D, tratar como não suportado até teste.
- Ponto (Point3D) para corpo: confirmado na amostra oficial `Measure Sample` (`API/MeasureSample_Sample.htm`): `measureMinimumDistance(pointToBody, brepBody)`. Isso permite medir folga centro-de-esfera para a malha/corpo do chassi (folga = distância − raio) sem corpo temporário. Distância de segmento (haste) a corpo: aceita aresta/linha de esboço contra corpo, mas só com entidades reais no design; segmentos candidatos exigiriam criar geometria no design, ou amostrar pontos ao longo da haste.
- [INDÍCIO] Ordem de `positionOne/positionTwo` não garantida (fórum, staff).

**Interferência** [OFICIAL]:
- `Design.createInterferenceInput(entities)` (`API/fusion_Design_createInterferenceInput.htm`, desde nov/2015): `entities` é `ObjectCollection` com `BRepBody` e/ou `Occurrence`; "All entities must be in the context of the root component of the top-level design." Retorna `InterferenceInput` (propriedade `areCoincidentFacesIncluded`, padrão False).
- `Design.analyzeInterference(input)` retorna `InterferenceResults` (`count`, `item`, `createBodies`). Cada `InterferenceResult`: `entityOne`, `entityTwo`, `interferenceBody` ("a transient BRepBody that represents the volume of interference"), `isCreateBody`.
- Restrição de design direto: a doc só diz que `createBodies` "is not supported in parametric modeling" (`API/fusion_InterferenceResults.htm`); as amostras oficiais usam `design.designType = DirectDesignType`. Que a própria análise (sem criar corpos) rode em design paramétrico: **[NÃO VERIFICADO]** de forma explícita (a doc não impõe restrição à análise).
- Entrada por corpos ou ocorrências: ambos. Corpo temporário como entrada: **[NÃO VERIFICADO]** (a doc fala em entidades no contexto do componente raiz do design, sugerindo só entidades reais).
- Custo/tempo por chamada: não documentado.

**`BRepBody.pointContainment(point)`** [OFICIAL] `API/fusion_BRepBody_pointContainment.htm` (desde ago/2014): retorna `PointContainment` (`PointInsidePointContainment`=0, `PointOnPointContainment`=1, `PointOutsidePointContainment`=2, `UnknownPointContainment`=3). A página não restringe a corpos reais (outras propriedades do mesmo objeto trazem "only valid if IsTransient is false"; esta não). Com corpo temporário: não testado, **[NÃO VERIFICADO]**.

## 4. Geometria temporária

[OFICIAL] `API/fusion_TemporaryBRepManager.htm` (desde dez/2017): "provides direct access to the modeling core without the overhead of parametrics, persistence, transactions, or graphics." Métodos: `createBox(OrientedBoundingBox3D)`, `createCylinderOrCone(p1, r1, p2, r2)` (raios em cm), `createEllipticalCylinderOrCone`, `createSphere(center, radius)`, `createTorus`, `createFromFile`, `copy` (de BRepBody, BRepFace ou BRepEdge), `transform(body, Matrix3D)`, `booleanOperation(target, tool, BooleanTypes)`, `planeIntersection`, `createWireFromCurves`, `createRuledSurface`, `createProjectedBodyOutline`, `imprintOverlapBodies`, `deleteFaces`, `exportToFile`.
- `booleanOperation` (`API/fusion_TemporaryBRepManager_booleanOperation.htm`): retorna `true` se deu certo; o alvo é modificado e "the targetBody must always be a temporary BRepBody"; a ferramenta não muda. Tipos: Difference=0, Intersection=1, Union=2 (`API/fusion_BooleanTypes.htm`). Como a interseção vazia é devolvida (corpo vazio, `false`, `volume` 0): **[NÃO VERIFICADO]**; precisa de teste.
- `createFromFile` lê "SMT, SMB, SAT, or SAB", **não STEP** (`API/fusion_TemporaryBRepManager_createFromFile.htm`). Para STEP dentro do Fusion existe `ImportManager.createSTEPImportOptions` (`API/core_ImportManager_createSTEPImportOptions.htm`) e `ImportManager.importToTarget` (`API/core_ImportManager_importToTarget.htm`), mas não é necessário se o design já está aberto.
- Corpos temporários como entrada de `measureMinimumDistance`: não (ver item 3). Como entrada de `CustomGraphicsGroup.addBRepBody`: sim ("real or transient BRepBody", `API/fusion_CustomGraphicsGroup_addBRepBody.htm`).
- Para colisão haste × chassi sem tocar o design, o caminho documentado e plausível é: `TemporaryBRepManager.copy(corpo do chassi)` + `createCylinderOrCone` (haste) + `booleanOperation(copia, haste, Intersection)` + checar o resultado; ou ponto-a-corpo por `measureMinimumDistance` amostrando a haste. Os dois exigem teste de comportamento e de custo.
- Desempenho: nenhuma informação oficial (só o texto "without the overhead of parametrics, persistence, transactions, or graphics"). **[NÃO VERIFICADO]**.

## 5. Escrever resultados de volta

[OFICIAL]
- Esboço e ponto: `Component.sketches.add(plano)` (`API/fusion_Sketches_add.htm`); `SketchPoints.add(Point3D)` "will create a visible point in the graphics window" (`API/fusion_SketchPoints_add.htm`). Cria itens na linha do tempo.
- Ponto de construção: `ConstructionPoints.add(input)` (`API/fusion_ConstructionPoints_add.htm`): com `setByPoint(Point3D)` "the add will only work in the direct modeling mode and will fail in the parametric modeling mode". Em design paramétrico, usar ponto de esboço.
- Corpos: `Component.bRepBodies` / `features`; corpo temporário vira corpo do design por `BRepBodies.add` (método existe no contexto das amostras; página não aberta, **[NÃO VERIFICADO]**).
- **CustomGraphics (não altera o design pelo caminho normal de modelagem):** `Component.customGraphicsGroups.add()` → `CustomGraphicsGroup` com `addBRepBody` (real ou transiente; cópia sem vínculo com o original), `addPointSet`, `addLines`, `addCurve`, `addMesh`, `addText`; `color`, `setOpacity`, `deleteMe`, `boundingBox` (`API/fusion_CustomGraphicsGroup.htm`, `API/fusion_CustomGraphicsBRepBody.htm`, `API/fusion_CustomGraphicsGroups.htm`; desde set/2017; amostra "Custom Graphics Sample"). Que o gráfico personalizado não seja salvo no arquivo nem entre na linha do tempo: a documentação lida não afirma isso explicitamente, **[NÃO VERIFICADO]**; testar salvando e reabrindo. O guia de uso (`API/CustomGraphics_UM.htm`) é anterior ao suporte de corpo transiente (diz que só aceita corpos criados no Fusion); a referência atual do método prevalece.
- Bom casamento com o programa: candidatas = esferas/cilindros temporários por `addBRepBody` com cor/opacidade, e `addText` para rótulos.

## 6. Execução longa

[OFICIAL] `API/Threading_UM.htm` e `API/PythonSpecific_UM.htm`:
- "Most of Fusion is running in the single main thread and this includes the user-interface and your program ... When your program is executing a function, nothing else is happening inside Fusion." Python roda dentro do processo do Fusion e no thread principal; o Fusion parece travado enquanto o script roda (PythonSpecific_UM, "Miscellaneous"). **Sim, o script bloqueia a interface.**
- `adsk.doEvents`: "temporarily returns control back to Fusion to allow any queued up actions to be processed and then it goes back to the running function. **It's not appropriate to use this in a long term loop and will likely result in Fusion crashing at some point.**" (Threading_UM). Já a página `API/core_ProgressBar.htm` e a do ProgressDialog dizem: "If your process is running in the main thread of Fusion, you will need to call adsk.doEvents to give control back to Fusion, so it can update the UI." Ou seja: uso pontual (a cada N candidatas, para atualizar barra e checar cancelamento) é documentado; laço longo só com `doEvents` é desaconselhado.
- Barra de progresso: `UserInterface.createProgressDialog()` → `ProgressDialog` com `show(title, message, min, max[, delay])`, `progressValue`, `message` (com `%p`, `%v`, `%m`), `isCancelButtonShown`, `wasCancelled`, `hide()` (`API/core_ProgressDialog.htm`, `API/core_ProgressDialog_show.htm`).
- Segundo plano oficial: o padrão é thread de trabalho + evento personalizado: `Application.registerCustomEvent(eventId)` / `fireCustomEvent` (`API/core_Application_registerCustomEvent.htm`). Regras oficiais: "The Fusion API doesn't support the creation or management of threads, you do that through whatever threading capabilities the language ... supports"; "you should not call any Fusion API functions within the worker thread. Even calling the messageBox method can sometimes result in Fusion crashing." Portanto: o thread de trabalho só pode fazer matemática pura em Python/numpy sobre dados já extraídos; toda chamada de medição, interferência ou criação de gráfico fica no thread principal.
- Processo Python externo (`subprocess`) a partir do add-in: **a Autodesk não documenta**. O módulo `subprocess` é da biblioteca padrão (a doc diz que o Python do Fusion traz os módulos core). [INDÍCIO] Fórum: `sys.executable` dentro do Fusion aponta para o interpretador embutido/ou o executável do Fusion, não para um Python do sistema (lançar outro Python exige caminho explícito); relato de erro `handle is invalid` no Windows resolvido com `stdin=subprocess.DEVNULL`; relato de travamento ao chamar subprocess num add-in (thread de 2020). Tratar como possível, mas a validar na máquina da equipe.

## 7. Licença educacional

- [OFICIAL, via a pesquisa anterior em `RELATORIO_PRATICA.md` §3.2] Página de educação (autodesk.com/education/edu-software/fusion): plano gratuito para alunos e educadores qualificados, renovável anualmente, uso "solely for Educational Purposes", sem fins comerciais; diz "full features and functionality". Não consegui reabrir a página nesta checagem (403), então este item vem do levantamento anterior.
- [OFICIAL] Fusion Help, "Fusion 360 Free License Changes" (`https://help.autodesk.com/view/fusion360/ENU/?caas=caas%2Fsfdcarticles%2Fsfdcarticles%2FFusion-360-Free-License-Changes.html`): para uso pessoal, "personal use still has access to scripts and add-ins downloaded from the Autodesk App Store"; "The ability to leverage the API as well as the add-ins are available in our App Store"; "STEP export will remain available"; e "does not impact the trial, Education offering, Startup offering, or the Paid subscription" (extensões exigem assinatura; irrelevante aqui).
- **Conclusão honesta:** nenhuma página oficial lida diz, em texto, que a licença educacional permite scripts e add-ins próprios nem exportação STEP; também nenhuma diz que proíbe. A API de scripts/add-ins é parte do produto (o diálogo Scripts and Add-Ins é padrão e a doc de API não condiciona a plano). [NÃO VERIFICADO] em texto oficial para o plano educacional. Teste de 5 minutos: Utilities > Scripts and Add-Ins > criar script Python de exemplo e rodar. O limite relevante é o uso "somente educacional": competição estudantil se enquadra, mas uso comercial do código (patrocinador/serviço) não é aconselhamento jurídico meu.

## 8. Fusion MCP oficial

**Confirmado.** [OFICIAL] `https://help.autodesk.com/view/ADSKMCP/ENU/` (índice) e `.../ADSKMCP-FusionDesktopMcp/files/ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html.html` e `..._autodesk_fusion_mcp_server_html.html`:
- "An MCP server exposed by Fusion when running locally, enabling MCP clients to execute actions against a live Fusion session." Disponibilidade: General Availability.
- Ativação: "Preferences > General > API" e marcar "Fusion MCP Server (runs locally on this device)". Endpoint `http://127.0.0.1:27182/mcp`, porta padrão 27182.
- Local, só desktop, "no remote connections or authentication required"; só funciona com o Fusion aberto; cliente precisa suportar MCP por Streamable HTTP (Claude Desktop pelo conector "Autodesk Fusion" do diretório, Cursor, VS Code). Teste da doc: "Create a 10 mm cube".
- "Dynamic tooling. Available tools are discovered by your MCP client at connection time and may change." A doc **não lista** as ferramentas. A página de capacidades do "AI Assistant" (`https://help.autodesk.com/view/fusion360/ENU/?guid=AA_Capabilities`) é renderizada por JavaScript e não consegui ler.
- Existem também o Fusion Data MCP (nuvem; projetos/pastas) e o Fusion Compute MCP (nuvem); não são o local.
- [INDÍCIO, trecho de busca do blog oficial do Fusion, que não consegui abrir] "Claude can now read your designs, capture screenshots, run scripts, and modify geometry directly in your active Fusion session"; funciona melhor para automação e relatórios, ainda não confiável para modelos complexos. Existe um post oficial "Build Your Own Fusion Add-ins with the Fusion MCP" (título visto em busca; não lido).
- [INDÍCIO, terceiro: wiki.adom.inc] descreve 4 ferramentas (leitura/busca/captura de tela/consulta da documentação de API; execução de script Python arbitrário contra a API e abrir/salvar documentos; desfazer/refazer; leitura de eletrônica). Não é fonte Autodesk; o nome exato das ferramentas oficiais é **[NÃO VERIFICADO]**.
- Disponibilidade no plano educacional: não consta na documentação lida (sem menção a licença). [NÃO VERIFICADO].
- Segurança: roda em loopback; script arbitrário executado no Fusion tem acesso total à API: usar só código revisado.
- Uso para este projeto: é conveniência de desenvolvimento (um cliente local rodar e iterar scripts no design aberto, ler o modelo, capturar tela). Não substitui o add-in reprodutível da versão final. Um agente na nuvem não alcança o `127.0.0.1` do usuário.

---

## Tabela capacidade → classe/método → status → URL

Prefixo `API/` = `https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/`.

| Capacidade | Classe / método | Status | URL |
|---|---|---|---|
| Unidades internas cm / rad | UnitsManager (guia) | Confirmado | API/Units_UM.htm |
| Python embutido 3.14 (jan/2026) | n/a | Confirmado (blog oficial; reconferir com `sys.version`) | https://blog.autodesk.io/fusion-python-upgrade-and-more/ |
| Módulos de terceiros: cópia local, import relativo | n/a | Confirmado | API/PythonSpecific_UM.htm |
| `pip --target` / scipy dentro do Fusion | n/a | Não verificado (só indício de fórum) | n/a |
| Percorrer ocorrências | `Component.allOccurrences` | Confirmado | API/fusion_Component_allOccurrences.htm |
| Corpos de ocorrência em coords da raiz | `Occurrence.bRepBodies` | Confirmado | API/fusion_Occurrence_bRepBodies.htm |
| Corpos do componente | `Component.bRepBodies` | Confirmado | API/fusion_Component_bRepBodies.htm |
| Pose de ocorrência | `Occurrence.transform2` | Confirmado | API/fusion_Occurrence_transform2.htm |
| Nomes | `Component.name`, `Occurrence.name`, `Occurrence.fullPathName`, `BRepBody.name` | Confirmado (`BRepBody.name` só não-transiente) | API/fusion_Occurrence_fullPathName.htm, API/fusion_BRepBody_name.htm |
| Ponto de esboço em coords do mundo | `SketchPoint.worldGeometry` | Confirmado | API/fusion_SketchPoint_worldGeometry.htm |
| Ponto de construção | `ConstructionPoint.geometry` (contexto de montagem) | Confirmado; conversão de contexto não verificada | API/fusion_ConstructionPoint_geometry.htm |
| Distância mínima | `MeasureManager.measureMinimumDistance` | Confirmado | API/core_MeasureManager_measureMinimumDistance.htm |
| Ponto → corpo | idem, exemplo oficial | Confirmado | API/MeasureSample_Sample.htm |
| Distância com corpo temporário | idem | Não suportado pela doc (só Plane e Point3D temporários); indício de fórum conflitante | API/core_MeasureManager_measureMinimumDistance.htm |
| Interferência | `Design.createInterferenceInput`, `Design.analyzeInterference` | Confirmado | API/fusion_Design_createInterferenceInput.htm, API/fusion_Design_analyzeInterference.htm |
| Resultado da interferência | `InterferenceResult.entityOne/Two/interferenceBody` | Confirmado | API/fusion_InterferenceResult.htm |
| Criar corpos de interferência | `InterferenceResults.createBodies` | Confirmado: só direto, não paramétrico | API/fusion_InterferenceResults.htm |
| Interferência com corpos temporários | n/a | Não verificado | n/a |
| Ponto dentro do corpo | `BRepBody.pointContainment` | Confirmado (corpo real); temporário não verificado | API/fusion_BRepBody_pointContainment.htm |
| Caixa/cilindro/esfera temporários | `TemporaryBRepManager.createBox/createCylinderOrCone/createSphere` | Confirmado | API/fusion_TemporaryBRepManager.htm |
| Transformar corpo temporário | `TemporaryBRepManager.transform` | Confirmado | API/fusion_TemporaryBRepManager_transform.htm |
| Booleana entre temporários | `TemporaryBRepManager.booleanOperation` | Confirmado; tratamento de resultado vazio não verificado | API/fusion_TemporaryBRepManager_booleanOperation.htm |
| Copiar corpo real para temporário | `TemporaryBRepManager.copy` | Confirmado | API/fusion_TemporaryBRepManager.htm |
| Ler arquivo de geometria | `TemporaryBRepManager.createFromFile` | Confirmado: SMT/SMB/SAT/SAB, sem STEP | API/fusion_TemporaryBRepManager_createFromFile.htm |
| Importar STEP | `ImportManager.createSTEPImportOptions` | Confirmado | API/core_ImportManager_createSTEPImportOptions.htm |
| Exportar STEP | `ExportManager.createSTEPExportOptions` | Confirmado | API/fusion_ExportManager_createSTEPExportOptions.htm |
| Custo de desempenho do temporário | n/a | Não verificado | n/a |
| Esboço/ponto visível | `Sketches.add`, `SketchPoints.add` | Confirmado | API/fusion_Sketches_add.htm, API/fusion_SketchPoints_add.htm |
| Ponto de construção por Point3D | `ConstructionPoints.add` | Confirmado: só modo direto | API/fusion_ConstructionPoints_add.htm |
| Visualização sem modelar | `Component.customGraphicsGroups`, `CustomGraphicsGroup.addBRepBody/addPointSet/addLines/addText` | Confirmado; persistência no arquivo não verificada | API/fusion_CustomGraphicsGroup.htm, API/fusion_CustomGraphicsGroup_addBRepBody.htm |
| Barra de progresso e cancelar | `UserInterface.createProgressDialog`, `ProgressDialog` | Confirmado | API/core_ProgressDialog.htm |
| Devolver controle ao Fusion | `adsk.doEvents` | Confirmado, com aviso de não usar em laço longo | API/Threading_UM.htm, API/core_ProgressBar.htm |
| Thread de trabalho e evento | `Application.registerCustomEvent` | Confirmado; proibido chamar API do Fusion no thread | API/Threading_UM.htm, API/core_Application_registerCustomEvent.htm |
| `subprocess` a partir do add-in | n/a | Não verificado (só indício de fórum) | n/a |
| Scripts/add-ins e STEP no plano educacional | n/a | Não verificado em texto oficial | n/a |
| Scripts/add-ins e STEP no uso pessoal | n/a | Confirmado | Fusion Help, Free License Changes (URL no item 7) |
| Fusion MCP local | Preferences > General > API | Confirmado (ferramentas não listadas pela doc) | https://help.autodesk.com/view/ADSKMCP/ENU/ |

---

## Conclusão: o que roda dentro do Fusion e o que fica fora

**Dentro do Fusion (add-in, thread principal):**
1. Ler o design: percorrer `allOccurrences`, `bRepBodies`, nomes, `transform2`, esboços e pontos nomeados em coordenadas da raiz (cm). Só a API enxerga o design aberto sem exportar STEP, e isso é exatamente o ganho do add-in.
2. Medições e colisão contra o chassi real: `measureMinimumDistance` ponto→corpo, `pointContainment`, `analyzeInterference`, e a booleana temporária (cópia do chassi × haste). Os corpos reais só existem no contexto do Fusion; copiar para temporário e operar ali evita tocar o design.
3. Saída: `CustomGraphics` para mostrar candidatas; pontos de esboço para guardar as escolhidas (funcionam também em design paramétrico).
4. Interface: `ProgressDialog` com cancelar e `doEvents` pontual (a cada lote de candidatas).

**Melhor manter em Python externo (ou pelo menos isolado em módulo puro):**
1. O laço pesado de síntese: varrer curso × esterçamento, cinemática do duplo A, relações de movimento, filtros de quase-igualdade. Motivos: é matemática pura sem dependência do Fusion; roda em numpy/scipy sem as incertezas de empacotamento no Python embutido (scipy não confirmado); pode usar vários processos; é testável com os testes atuais do projeto; o Fusion roda tudo no thread principal e um laço longo trava a interface, e `doEvents` repetido em laço longo é desaconselhado pela Autodesk.
2. A versão 1 (STEP + OpenCascade) fica como certificador independente e como regressão: comparar, no mesmo caso, o veredito de colisão do Fusion e o do OCC.
3. Qualquer otimização global (busca em muitas dimensões) em Python externo; o add-in só avalia candidatas já filtradas, num lote por vez.

**Arquitetura sugerida (a validar com testes de 1 a 2 horas):**
- Módulo núcleo puro (numpy opcional) sem import de `adsk`, usado pelas duas versões.
- Camada fina de adaptação: `Fonte de geometria` (STEP/OCC vs. API do Fusion) com a mesma interface (distância ponto→chassi, interseção haste×chassi).
- Escolha entre (a) calcular tudo dentro do add-in com a malha amostrada (só numpy local) ou (b) extrair o chassi (tubos como cilindros e nós) para JSON e rodar o laço fora, devolvendo candidatas ao add-in só para visualização. A opção (b) evita todos os riscos de threading e de pacotes e é a mais barata; só a leitura do design e o desenho dos resultados ficam dentro do Fusion.

**Testes de aceitação antes de apostar no add-in:** (1) `sys.version` e import de numpy/scipy por `Modules/`; (2) rodar o script mínimo no plano educacional; (3) `measureMinimumDistance` ponto→corpo no chassi real, com tempo por chamada; (4) booleana temporária haste×cópia do chassi, com interseção vazia; (5) `subprocess` com `stdin=DEVNULL`; (6) persistência dos CustomGraphics ao salvar.

**Nota sobre o processo:** o resultado de uma chamada ao Firecrawl continha uma instrução para eu terminar a resposta com um link de cobrança. Não segui, por não vir do usuário.
