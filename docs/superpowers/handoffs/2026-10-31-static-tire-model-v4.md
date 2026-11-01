# Handoff — Modelo estático de pneu V4

## Objetivo e fronteiras

Concluir uma camada exploratória PAC2002 estática, editável e rastreável, capaz de ler perfis `.tir`, avaliar Fx/Fy/Mx/My/Mz e visualizar curvas em Jupyter. O fluxo Excel e Python segue separado. A etapa transiente/dinâmica vem depois. O R25B do TTC é somente proxy do Hoosier R60A da equipe; não há dados nem validação física do R60A.

Não editar planilhas nem documentos preexistentes. Os perfis `.tir` e PDFs de referência são locais/ignorados pelo Git. Não prometer validade física a partir de saída finita, plot suave ou concordância com outra implementação.

## Estado atual

- O protótipo está em `python/tire_model_static_v4.py`; exploração em `notebooks/tire_static_exploration.ipynb`.
- O ZIP Round 6 fornecido pelo usuário contém quatro perfis PAC2002 (8, 10, 12 e 14 psi). Estão em `data/local_tires/round_6_hoosier_r25b/`, caminho local ignorado pelo Git.
- `load_profile_family()` carrega os quatro perfis com `source_axis_system='ISO_TYDEX'`. Pressões numéricas observadas: 7.999992, 10.000062, 11.999987 e 14.000058 psi. A tolerância de seleção está em `1e-3 psi` para corresponder ao arredondamento do arquivo, sem interpolar perfis.
- Notebook executado com sucesso via `nbclient`, seis células de código e três figuras renderizadas. O kernel precisa iniciar com a raiz do repositório como `cwd`.
- Ambiente local `.venv`: Python 3.13, NumPy 2, Jupyter 1.1.1, Matplotlib 3.11.2. Jupyter/Matplotlib foram instalados no `.venv` sem alteração de `pyproject.toml`/`uv.lock`.
- O notebook foi corrigido para escolher velocidade `min(LONGVL)` em vez de 15 m/s, pois `LONGVL` observado é ~11.2 m/s.
- `python/tire_model.py::_sgn` foi corrigido de boolean subtraction para `int(x > 0) - int(x < 0)`, necessário para compatibilidade com NumPy 2.
- O gráfico de My é zero porque QSY1..QSY8 são zero nos quatro arquivos; isso é ausência de parametrização, não evidência de rolling resistance nula.
- Nos gráficos executados, μ efetivo máximo ficou em torno de 2.6; Fy chegou a ~2.8 kN em Fz nominal ~1.05 kN; Mx chegou a algumas centenas de N·m. Tratar como saídas não validadas que requerem conferência independente das equações, unidades e convenções antes de uso de projeto.
- Avisos de execução observados: IDs ausentes nas células do notebook (warning do nbformat) e configuração de event loop/transport do Jupyter no Windows. Execução terminou sem erro.

## Git e publicação

O commit `e5de218` (`feat: add static tire model V4 prototype`) já foi enviado a `origin/main`. Ele incluiu o módulo V4, notebook e plano. No momento do handoff há alterações posteriores não publicadas em `python/tire_model.py`, no notebook (velocidade) e no plano (resultado real da execução); verificar `git status` antes de agir. `.agents/skills/token-context-steward/SKILL.md` é uma skill local pessoal e foi excluída dos commits. Não adicionar `.tir` nem `.pdf`.

## Próximas tarefas, nesta ordem

1. Criar e executar testes focados do V4: quatro perfis e tolerância de pressão; limites de Fz/α/γ/κ/Vx; resultados finitos; save/load overlay, hash/eixos/pressão/esquema inválidos; fonte `.tir` permanece intacta.
2. Revisar de forma independente as equações e convenções de Mx/My/Mz contra o guia Adams/PAC2002; investigar magnitudes e sinais das saídas. OpenTirePython foi avaliado apenas como referência de arquitetura/estado; não confirmou parser `.tir` nem compatibilidade MF específica, portanto não é dependência recomendada.
3. Melhorar metadados/IDs de células do notebook para remover warning de nbformat se fizer parte do acabamento requerido; não é bloqueio de execução.
4. Atualizar este handoff e o plano com resultados reais. Depois, oferecer revisão humana do diff e só então fazer novo commit/push se autorizado no contexto vigente.

## Comandos de retomada

Na raiz do repositório:

```powershell
.venv\Scripts\python.exe -X utf8 -c "import pathlib,nbformat; from nbclient import NotebookClient; n=nbformat.read('notebooks/tire_static_exploration.ipynb',as_version=4); NotebookClient(n,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(pathlib.Path.cwd())}}).execute(); print('notebook OK')"
uv run ruff check python/tire_model_static_v4.py python/tire_model.py
```

Se os `.tir` locais não estiverem presentes, solicitar novamente o ZIP/perfil ao usuário; não procurar cópias em locais não especificados nem versionar os dados.
