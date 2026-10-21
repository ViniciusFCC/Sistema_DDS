# Sistema_DDS — Tupã Suspension System

Dimensionamento e dinâmica da suspensão do Fórmula SAE Elétrico da equipe Tupã (USP).
A planilha Excel é a interface que a equipe usa; os modelos Python são a implementação
verificada; a documentação de engenharia (docs/) registra as decisões.
Foco declarado: completar a planilha (EDR-019).

## Situação atual
- Fase A concluída (tag `v2.4.1`, repositório privado ViniciusFCC/Sistema_DDS). Fase B
  em andamento (`SPEC.md` §11): o EDR-043 trocou a versão no nome dos `.py` pela tag
  do Git.
- Layout (EDR-043): módulos em `python/` com nomes estáveis; testes em `tests/`
  (`tests/regressao/` guarda a V1.0 congelada e a referência histórica do T09, que não
  conta na aprovação); dados em `data/` (os hardpoints mantêm
  o `_V2.0`, versão do schema; os outros dados mantêm o sufixo de origem). A planilha em
  `excel/` mantém a versão no nome. Docstrings e textos de células em `build_workbook.py`
  ainda citam os nomes `_V2_x` de propósito: não os "corrija" (quebra o CA-07).
- Carro atual: TX/E05. O T09/E03 é só referência histórica, nunca baseline (EDR-012).
  Freio dentro da roda, em volta do cubo; motor no chassi, atrás (usuário, 2026-10-19;
  define a linha do anti-dive e do anti-squat, EDR-048). Mola, MR, barra e RC da
  planilha são valores demonstrativos (T09/E03), não do TX.
- Não há hardpoints reais do CAD (Fusion): toda a cinemática usa geometria sintética.
- V4.0 (incrementos 1 a 3) concluída no código (EDR-058): `excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx` é a
  referência, com 698 nomes definidos e as mesmas 387 fórmulas da V3.0. A viva da equipe continua a V3.0, na pasta
  compartilhada (caminho e responsável a informar), até o usuário decidir a troca. Do incremento 4 em diante a
  versão é a V4.1, numa conversa nova (`docs/registro-de-versoes-V4_0.md`).

## Comandos
- Ambiente: `uv sync` (Python 3.13). No Git Bash, rode `export UV_SYSTEM_CERTS=1` antes de
  `uv sync` ou `uv run`: o `uv run` reconstrói o projeto depois de uma troca de branch e,
  sem isso, falha no certificado do Norton. O `uv sync` instala o
  projeto em modo editável, com `python/` no caminho de import. Nunca `python`/`python3`
  direto: `python3` aqui é o atalho da Microsoft Store.
- Tudo de uma vez: `uv run python -X utf8 tools/rodar_testes.py` (log em
  `build/verificacao-ultima.md`). Log de evidência, só quando for registrar:
  `--saida docs/migracao/<novo>.md --titulo "..."`, numa árvore sem mudanças pendentes;
  nunca regrave os logs existentes. Um teste só: `uv run python -X utf8 tests/<script>.py`. Os testes são
  scripts com `check()`, não pytest: "passou" = a linha final `N PASS, 0 FAIL, de T
  testes` com N igual ao esperado.
- Esperado na V4.0: pneu 43, oráculos 5, suspensão 54, cinemática 76, hardpoints 35,
  equilíbrio 28, equilíbrio linear 18 (incrementos 1 e 2), V4.0 nomes e dados 4 (`tests/test_v4_0.py`, incremento 3), mutação 25/25 do pneu e 6/6 do equilíbrio, autoteste do comparador 15/15; V2.4 regenerada com 347 fórmulas e V3.0 com 387 (356 + 6 da 1ª rodada de feedback, EDR-050, + 19 da 2ª rodada da revisão metodológica, pior origem no 14_DASHBOARD, + 6 de direção, EDR-052), as duas com 0 diferença; V4.0 regenerada da tag `v3.0` com as mesmas 387 fórmulas e os 698 nomes, 0 diferença.
  `tests/test_workbook.py` 19/19 (pneu) e `tests/test_workbook_suspensao.py` 15/15 (suspensão),
  ambos na V3.0 de referência (arquivo da tag `v3.0`; antes da tag, o da árvore), e `tests/test_workbook_v4_0.py` 2/2
  (V4.0 de `excel/`): recalculam cópias pelo Excel via COM ou, sem Excel, pelo
  LibreOffice (EDR-044; `DDS_RECALC=excel|libreoffice` força um). Sem nenhum dos dois eles
  saem NÃO EXECUTÁVEL, que nunca conta como aprovado.
- Planilha vigente: V3.0, **fechada em 2026-10-20** (EDR-051). `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`
  é o arquivo vivo da equipe; a referência imutável é o mesmo arquivo na tag `v3.0`. A V3.0 de referência é
  gerada da V2.4 por `python/atualizar_planilha.py` (toda célula alterada fica em `alteracoes()`, com fonte e EDR);
  o script recusa gravar por cima da planilha viva. CA-07: a regeneração bate com a referência, e a viva bate
  com a referência em tudo menos as células de entrada (`atualizar_planilha.celulas_de_entrada()`). Mudança
  de fórmula ou estrutura entra na próxima planilha gerada, nunca editando a planilha à mão. A **V4.0** já existe
  (fundação: nomes definidos, fórmulas iguais às da V3.0; os textos da V3.0 que dizem "V3.1" se referem a ela); a
  próxima planilha com mudança de fórmula ou estrutura é a **V4.1**, do incremento 4 em diante, numa conversa nova
  (usuário, 2026-10-21).
- V4.0 de referência (EDR-058): `python/gerar_v4_0.py` a gera da tag `v3.0` em `build/` (nunca em `excel/`; a cópia
  para `excel/` é um commit próprio), com os nomes de `data/nomes_V4_0.csv` (`python/nomes_v4_0.py`); só mudam
  00_README A3 e a linha 20 do 15_CHANGELOG (`docs/registro-de-versoes-V4_0-celulas.md`). Migração dos dados da viva,
  por nome: `uv run python -X utf8 tools/migrar_dados_v3_v4.py <viva_V3_0.xlsx>` (saída em
  `build/V4_0_com_dados.xlsx`, relatório em `build/migracao-V3-V4.md`); conflito é listado e nunca sobrescrito
  (código 1), célula alterada fora dos nomes de dado é erro (código 2). Commit de dados da equipe é separado
  (`dados: ...`), com `tools/extrato_entradas.py` para o diff legível. A metodologia segue a literatura, principalmente o
  Milliken (usuário, 2026-10-19; `docs/revisao-metodologica.md`). Os livros e o OCR ficam
  em `references/` (fora do Git); busque no `.md`, mas confira a equação na imagem do PDF.
- Rode os testes afetados antes de dizer que uma tarefa terminou.

## Fontes de verdade
- Ordem em caso de divergência: `docs/Engineering_Decision_Register.md` → Engineering
  Standard V2.0 → arquitetura V2.0 → data contract V2.4 → registros de versões.
- O `HANDOFF-Sistema_DDS.md` resume e indexa; não substitui os originais.
- Hierarquia de autoridade (EDR-004): OptimumKinematics (cinemática) e OptimumTire
  (pneu) são REFERENCE. O Python é MODEL/cross-check e nunca substitui a referência.

## Convenções congeladas (erro aqui inverte resultados)
- Eixos ISO 8855: X frente, Y esquerda, Z cima. Lotus exige adaptador X=−X, Y=−Y.
- Camber + = topo da roda para fora; toe + = toe-out (EDR-002).
- MR = Δwheel/Δspring; K_wheel = K_spring/MR². Nome obrigatório `MR [wheel/spring]`.
- Anti-dive/anti-squat nunca reduzem ΔFz longitudinal (EDR-010).
- SI no núcleo; unidade no nome do campo em JSON/CSV (`X_m: 0.450`). Conversão só na
  apresentação, no Excel.
- `.tir` PAC2002 em ISO_TYDEX (eixo W do TYDEX, help do Adams p. 7; EDR-039 revisto em
  2026-10-19): sem transformação na roda direita; rodas esquerdas espelhadas antes.
  SAE_CALSPAN fica só para dado bruto em SAE. A V2.4 histórica usa SAE_CALSPAN.
- Três estados independentes, nunca misturados: Lifecycle (OPEN…FROZEN, STALE),
  Validation (NOT_VALIDATED/PASS/WARNING/FAIL) e Record_Status do EDR.
  VERIFIED ≠ validado fisicamente. FAIL = "não validado", não "modelo errado".

## Regras de trabalho
- IMPORTANTE: nunca altere fórmula existente da planilha sem aprovação explícita.
  Toda mudança registra aba, célula, fórmula anterior e nova, dependências,
  justificativa e teste.
- Recomendação minha não é aprovação. Instrução ambígua vira PENDING_CONFIRMATION.
- Não crie nem renumere IDs (SUS-, EDR-, REQ-, TC-) sem autorização. Aprovar um ID não
  valida a equação.
- Não preencha lacunas por inferência: nada de referência, coeficiente, target ou
  limite inventado. Valor sem fonte fica "a confirmar".
- Valor sintético ou demonstrativo sempre rotulado; nunca apresentado como resultado
  do carro.
- Toda decisão relevante entra no EDR antes ou durante a implementação.
- Divergência MODEL × REFERENCE: unidades → coordenadas → hardpoints → configuração →
  hipóteses → equações → solver → interpolação. Nunca ajuste o resultado para bater.
- Commits separados por propósito: cópia, portabilidade, reorganização e mudança de
  engenharia nunca no mesmo commit (para isolar regressões).

## Não fazer
- IMPORTANTE: não edite, mova nem apague nada em `importado-claude-ai/`. É o registro
  original da migração (somente leitura; backup na OneDrive).
- Não versione `*.tir` (dados do TTC, termos não verificados), PDFs ou conversões de
  livros, nem `Sistema_DDS_CONTEXTO_COMPLETO.md`.
- Não use xlwings/PyXLL/macros como ponte Excel–Python (EDR-008). Uso só em teste
  exige EDR próprio (o recálculo de cópias no `test_workbook` via COM é o EDR-044).
- Não recalcule nem salve pelo LibreOffice a planilha viva nem a de referência (remove as aspas de abas
  iniciadas por dígito). A equipe salva a planilha viva pelo Excel (verificado em 2026-10-20: o salvamento
  não muda fórmulas nem valores); ferramentas e testes nunca a salvam: trabalham em cópia.
- Não leia o `Sistema_DDS_CONTEXTO_COMPLETO.md` inteiro (721 KB); busque nele.

## Ferramentas ativas neste projeto
Aprovadas em 2026-10-18 (passo 5). Configuração em `.claude/settings.json`.
- `pyright-lsp` (plugin): diagnóstico de imports e nomes ao editar Python, útil no
  commit de portabilidade e na renomeação da fase B.
- `permissions.deny` de Edit/Write em `importado-claude-ai/**`: garante a regra de
  somente leitura (testado: a edição é recusada).
- Push e repositório: use o `gh` CLI. O MCP do plugin `github` falha (HTTP 400).
- Skill `xlsx` só para ler e inspecionar: o recálculo dela usa LibreOffice.
- Para depois (não ativar sem pedido): `serena` (fase B), MCP `matlab` (verificação
  cruzada), `citation-needed` (revisão de fichas e Guide), conector Autodesk Product
  Help (script de exportação do Fusion), hook de testes após `tools/rodar_testes.py`.

## Aprendizados
<!-- Erros repetidos e correções aprovadas pelo usuário. -->
