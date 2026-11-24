# Fase 2 (Fusion): roteiro da investigação inicial

Decisão do usuário (2026-11-24): a fase 2 é o posicionador rodando dentro do Fusion. Este roteiro levanta, **sem alterar nada do projeto nem do Fusion**,
o que o Fusion da máquina do usuário permite. Resultado = `docs/posicionador/fusion/RELATORIO-investigacao.md` (fatos medidos, não suposições).

## O que precisamos saber (e por quê)
1. **Versão do Fusion e do Python embutido.** O código atual é Python 3.13 com numpy e scipy; o Python do Fusion pode ser outro.
2. **Bibliotecas disponíveis no Python do Fusion** (numpy? scipy? pacotes instaláveis?). O scipy (`brentq`, Nelder-Mead) precisa sair se não existir (R9).
3. **API de geometria:** distância mínima entre sólidos/curvas, interferência, corpos temporários (`TemporaryBRepManager`), leitura de esferas/pontos de construção do CAD (os `REF_` que o STEP não trouxe), cotas e parâmetros.
4. **Como o add-in lê o modelo T11 aberto** (chassi, tubos, hardpoints) e **como grava o resultado** (pontos de construção, parâmetros, relatório).
5. **Desempenho:** custo de uma chamada de distância mínima na API (a busca faz milhares de avaliações).
6. **Instalação:** onde ficam add-ins/scripts, se precisa de aprovação de administrador, e como distribuir à equipe.

## Etapa A: sem abrir o Fusion (só leitura de arquivos)
- Localizar a instalação (`%LOCALAPPDATA%\Autodesk\webdeploy\production\*` e `%PROGRAMFILES%\Autodesk`), anotar a versão/build.
- Localizar o Python embutido (`...\Python\python.exe` ou `Python\Lib`), anotar a versão (`--version`), listar `site-packages` (numpy, scipy, outros).
- Localizar os stubs/documentação offline da API (`adsk`, `.pyi`, `Python\Lib\adsk`) e listar as classes de interesse: `MeasureManager`, `TemporaryBRepManager`,
  `BRepBody`, `ConstructionPoint`, `Sketch`, `UserParameters`, `Occurrence`.
- Conferir os caminhos dos add-ins do usuário (`%APPDATA%\Autodesk\Autodesk Fusion\API\AddIns` e `\Scripts`).
Não instale nem altere nada; só leia e relate.

## Etapa B: sondagem dentro do Fusion (um clique do usuário)
Criar o script de sondagem `T11_sondagem` em `%APPDATA%\Autodesk\Autodesk Fusion\API\Scripts\T11_sondagem\` (arquivos `T11_sondagem.py` e
`T11_sondagem.manifest`) que, ao ser executado em *Utilities > Scripts and Add-Ins*, **só lê** e grava `C:\Projetos\fusion_sondagem.json` com:
`sys.version`, `sys.path`, importa numpy/scipy/OCP (try/except, com a versão), `adsk.core.Application.get().version`, lista de documentos abertos, e, se houver
design ativo: nº de corpos, nomes de pontos de construção que começam com `REF_`, parâmetros do usuário, e o tempo médio de 200 chamadas de
`MeasureManager.measureMinimumDistance` entre dois corpos quaisquer (se houver ≥ 2). Não pode criar nem alterar geometria nem salvar o documento.
Pedir ao usuário **uma única ação**: abrir o T11 no Fusion e executar o script. Se o usuário não puder, relatar que a Etapa B não foi feita.

## Etapa C: relatório
Escrever `docs/posicionador/fusion/RELATORIO-investigacao.md` com: tabela de fatos (valor medido, fonte, comando), o que ainda é desconhecido,
e uma recomendação de arquitetura **rotulada como proposta** (por exemplo: números de numpy puro dentro do add-in; scipy substituído por bisseção e Nelder-Mead próprios;
distância mínima via API em vez de OCP). Sem inventar: o que não foi medido fica "a confirmar".
Fazer commit só desse relatório e do script de sondagem (cópia em `docs/posicionador/fusion/T11_sondagem/`), `git pull --no-rebase` e push na branch `ccr-4cb60a57-janeru`.

## Regras
- Não editar código do posicionador nem arquivos do CAD; não salvar nem fechar documentos do Fusion; não instalar pacotes no Python do Fusion.
- Não use fable. Siga o CLAUDE.md do projeto (execução longa com `tools/paralelo.py`; sem inferência de dados; rótulos de hipótese).
