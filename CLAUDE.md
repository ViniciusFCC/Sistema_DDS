# Sistema_DDS — Tupã Suspension System

Dimensionamento e dinâmica da suspensão do Fórmula SAE Elétrico da equipe Tupã (USP).
A planilha Excel é a interface que a equipe usa; os modelos Python são a implementação
verificada; a documentação de engenharia (docs/) registra as decisões.
Foco declarado: completar a planilha (EDR-019).

## Situação atual
- Migração do claude.ai em andamento: fase A do `SPEC.md` (reproduzir a V2.4 localmente).
- `python/` é uma pasta plana de propósito: os scripts acham módulos e dados ao lado
  deles (`HERE`). Não separe em tests/ ou data/ nem renomeie `_V2_x` antes da tag
  `v2.4.1` (fase B do SPEC).
- Carro atual: TX/E05. O T09/E03 é só referência histórica, nunca baseline (EDR-012).
- Não há hardpoints reais do CAD (Fusion): toda a cinemática usa geometria sintética.

## Comandos (a confirmar quando o pyproject existir)
- Ambiente: `uv sync` (Python 3.13). Nunca `python`/`python3` direto: `python3` aqui é
  o atalho da Microsoft Store.
- Testes: na pasta `python/`, `uv run python -X utf8 <script>.py`. Os testes são
  scripts com `check()`, não pytest: "passou" = a linha final `N PASS, 0 FAIL, de T
  testes` com N igual ao esperado.
- Esperado na V2.4: pneu 43, oráculos 5, suspensão 42, cinemática 53, hardpoints 35,
  mutação 23/23. `test_workbook_V2_4.py` NÃO roda localmente (depende de LibreOffice e
  de `/mnt/skills`); nunca o conte como aprovado.
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
- `.tir` em SAE_CALSPAN, transformado para ISO na roda direita; rodas esquerdas
  espelhadas antes (EDR-039, com condições).
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
  exige EDR próprio.
- Não recalcule nem salve a planilha entregue pelo LibreOffice (remove as aspas de abas
  iniciadas por dígito) e não a salve pelo Excel: gere sempre uma cópia.
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
