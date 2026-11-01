# Modelo Estático de Pneu V4 — Plano de Implementação

**Goal:** Criar uma nova camada PAC2002 estática no Sistema_DDS que leia `.tir`, permita revisões rastreáveis de coeficientes, calcule forças e momentos em regime permanente e gere curvas exploratórias para carga, pressão nominal, slip angle, cambagem e escorregamento longitudinal.

**Architecture:** Não alterar `python/tire_model.py`, planilhas ou documentos existentes. A camada nova reutiliza o núcleo atual para Fx/Fy, acrescenta Mx/My/Mz segundo as equações PAC2002 documentadas e preserva revisões como overlays JSON vinculados por SHA-256 ao `.tir`. Excel permanece no fluxo atual como implementação de conferência; o contrato do repositório confirma que não há hoje uma ponte JSON Excel↔Python. O notebook serve ao desenvolvimento; aplicação web fica para depois das etapas estática e transiente.

**Tech Stack:** Python 3.13; dependências de execução já declaradas (NumPy, SciPy, openpyxl); Jupyter e Matplotlib para exploração, fora do núcleo do modelo.

## Fontes e materiais verificados antes da implementação

- Guia oficial Hexagon, *Adams 2022.3 Adams Tire User Guide*, baixado para `references/pdf/Adams_2022_3_Adams_Tire_User_Guide.pdf` (local/ignorado pelo Git) e consultado nas seções PAC2002: Mz puro e combinado (pp. 82–83), fatores de turn-slip (p. 84; no-slip, ζ=1), Mx (p. 91) e My (p. 92). Fórmulas também conferidas pelo texto pesquisável do guia oficial: [PDF oficial](https://documentation-be.hexagon.com/bundle/Adams_2022.3_Adams_Tire_User_Guide/raw/resource/enus/Adams_2022.3_Adams_Tire_User_Guide.pdf).
- Besselink, Schmeitz e Pacejka (2010), *An improved Magic Formula/Swift tyre model that can handle inflation pressure changes*, versão autoral no repositório da TU/e. Texto integral consultado: apresenta extensões específicas a MF-Tyre 5.2 para pressão, cambagem, rolling resistance e transientes; também alerta que diferentes versões/eixos/unidades podem ser incompatíveis. [Publicação e PDF na TU/e](https://pure.tue.nl/ws/files/3139490/Metis245615.pdf), [DOI](https://doi.org/10.1080/00423111003748088).
- Pacejka e Besselink (1997), *Magic Formula Tyre Model with Transient Properties*, portal acadêmico TU/e. Resumo consultado para delimitar a futura etapa: diferencia regime permanente da resposta transiente e descreve resposta longitudinal/lateral com relaxação em domínio de baixas frequências. O texto integral não é necessário para esta entrega estática. [Registro da publicação](https://research.tue.nl/en/publications/magic-formula-tyre-model-with-transient-properties/).
- Materiais do repositório: `python/tire_model.py`; `tests/test_tire_oracles.py` (comparação com duas implementações de terceiros, não validação experimental); `data/Hoosier_R25B_13x7_TTC_provisional.meta.json`; `docs/data-contract-V2_4-excel-python.md`; `docs/Engineering_Decision_Register.md` (EDR-008, 037–042); quatro perfis TTC Round 6 do ZIP do usuário.

## Evidência e decisões técnicas

- Os quatro arquivos locais são perfis PAC2002 separados em 8, 10, 12 e 14 psi; são casos com `IP=IP_NOM`, `PPX1..4=PPY1..4=0`. Selecionar os perfis nominais, sem interpolar ou extrapolar pressão. O artigo de 2010 reforça que variação de pressão requer a formulação e a calibração apropriadas.
- O pacote representa o R25B do TTC, não o R60A da equipe. O estado de validação permanece `NOT_VALIDATED`; concordância com código de terceiros para Fx/Fy não é validação física.
- Usar TYDEX W/ISO para as entradas do `.tir`; manter as transformações de roda/veículo fora da função de pneu único nesta etapa. O resultado da varredura não determina sozinho toe/camber ótimos do carro: para isso serão necessários cargas, cinemática, ângulos locais e objetivo veicular.
- Implementar Mz com trail pneumático, momento residual e deslocamento; Mx de tombamento; My de resistência ao rolamento em função da velocidade. Ignorar turn-slip e quaisquer termos de correção de pressão somente porque os perfis são nominalmente avaliados e este escopo não inclui spin.
- Revisões editam uma cópia, nunca o `.tir`; overlays só reabrem se hash, pressão nominal e sistema de eixos coincidirem. IP/IP_NOM não são coeficientes editáveis. Faixas de operação revisadas são verificadas quanto à consistência; coeficientes de momento omitidos são tratados como zero e reportados como hipótese da implementação.

## Escopo e limites

- Inclui carregamento individual e família de `.tir`, seleção das quatro pressões, inspeção de parâmetros/faixas, revisão e persistência de coeficientes, Fx/Fy/Mx/My/Mz, varreduras e gráficos Jupyter.
- Não inclui temperatura, desgaste, dinâmica/transientes, propriedades estruturais/verticais completas, extrapolação ou interpolação de pressão, otimização de toe/camber do veículo, interface web ou edição de workbook.
- Preservar a verificação paralela em Excel existente. O contrato atual diz que a ponte automática ainda não está implementada; não criar uma silenciosamente nem alterar a planilha. O usuário confirmou manter exatamente o fluxo atual nesta etapa.
- Não adicionar dependências ao runtime de produção só para notebook. Confirmar disponibilidade de Jupyter/Matplotlib no ambiente antes de prometer execução local do notebook.

## Arquivos

- Atualizar somente o arquivo novo e ainda local `python/tire_model_static_v4.py` para fechar os contratos PAC2002 e de revisão.
- Atualizar somente o notebook novo `notebooks/tire_static_exploration.ipynb` para inspecionar perfis, respeitar limites e mostrar curvas de Fx/Fy/Mx/My/Mz.
- Atualizar este plano novo, criado nesta tarefa. Não editar documentos versionados preexistentes ou arquivos `.xlsx`.
- Os `.tir` e o PDF do guia ficam sob regras locais/ignoradas; não adicionar nem publicar esses dados.

## Critérios de saída da etapa estática

1. Um `.tir` PAC2002 válido pode ser carregado individualmente; família de pressão só aceita nominal explicitamente presente.
2. Avaliação de ponto devolve Fx, Fy, Mx, My, Mz com unidades/convenções e faixa válidas identificadas.
3. Overlay editável pode ser salvo e reaberto apenas sobre a exata fonte, sem sobrescrever o `.tir`.
4. Notebook permite comparar pressões disponíveis e varrer α, γ, κ, Fz e Vx sem repetir equações.
5. Nenhum workbook ou documento preexistente muda; nenhuma alteração é commitada ou enviada ao GitHub.

## Estado da execução

- [x] Permissão de escrita no repositório e permissão de rede conferidas; PDF oficial do Adams baixado localmente.
- [x] Material PAC2002, formato TTC, convenções e fronteira Excel/Python revisados.
- [x] Implementar e revisar o módulo estático novo contra as equações e os contratos acima.
- [x] Preparar o notebook de exploração para as funções finais; execução fica pendente da instalação local de Jupyter/Matplotlib.
- [x] Fazer revisão estática do código, do estado Git e da ausência de alterações em arquivos existentes.
- [x] Incorporar revisão independente e lint local: vincular overlays ao eixo, tratar coeficientes de momento omitidos explicitamente, validar coerência de faixas e parâmetros positivos revisados (incluindo `LONGVL`), corrigir achados do Ruff.

## Verificação

AST do módulo Python, lint Ruff, JSON/estrutura do notebook e `git diff --check` passaram. Os quatro perfis do ZIP Round 6 foram carregados, selecionados pelas pressões nominais 8/10/12/14 psi e avaliados em pontos centrais dos domínios declarados; Fx/Fy/Mx/My/Mz foram finitos. `PRESSURE_TOLERANCE_PSI` foi elevado a 1e-3 para acomodar o arredondamento das pressões armazenadas nos arquivos. O teste legado `tests/test_tire_model.py` não roda com esse pacote porque espera `data/Hoosier_R25B_13x7_TTC_provisional.tir`, arquivo com nome distinto. Matplotlib, Jupyter e nbclient não estão instalados, portanto o notebook não foi executado. Qualquer afirmação de validade física requer validação futura contra medição/solver independente; o R25B permanece apenas proxy do R60A.

OpenTirePython foi revisado como referência de interface de estado e comparação de PAC2002. Não foi adotado como dependência: não foi confirmado suporte a leitura `.tir` nem compatibilidade com uma versão MF específica.

OpenTirePython foi revisado como referência de interface de estado e comparação de PAC2002. Não foi adotado como dependência: não foi confirmado suporte a leitura `.tir` nem compatibilidade com uma versão MF específica.
