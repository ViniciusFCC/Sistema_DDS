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
- Projeto atual: **T11**, em fase de projeto e de definição de diretrizes e dados (usuário, 2026-10-22). A planilha
  ainda não tem nenhum dado do T11: os dados que existem são os do TX/E05 e do T09/E03 que já estão nela. O T09/E03
  continua só referência histórica, nunca baseline (EDR-012); o TX/E05 passa a ser o carro anterior, também só
  referência para o T11. O rótulo "● Dado do TX" da lista Origens e o prefixo DEMONSTRATIVO (D16) tratavam o TX
  como o carro do projeto; na V4.2 (branch `feat/v4-2-inc5-metas`, EDR-062) viram `● Dado do T11` e `◐ Dado de outro carro (TX, T09)`.
  Freio dentro da roda, em volta do cubo; motor no chassi, atrás (usuário, 2026-10-19, antes de o T11 ser informado: confirmar se vale para o T11;
  define a linha do anti-dive e do anti-squat, EDR-048). Mola, MR, barra e RC da
  planilha são valores demonstrativos (T09/E03), não do TX nem do T11.
- Não há hardpoints reais do CAD (Fusion): toda a cinemática usa geometria sintética.
- V4.0 (incrementos 1 a 3) concluída no código (EDR-058): `excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx` é a
  referência, com 698 nomes definidos e as mesmas 387 fórmulas da V3.0. Foi a referência até a V4.1 (`docs/registro-de-versoes-V4_0.md`).
- V4.1 (incremento 4, equilíbrio na planilha) concluída (PR #17 mesclado em 2026-10-22; tag `v4.1` no
  merge 05d8fb5; EDR-059 e EDR-060 APPROVED, relatório `docs/v4-1/inc4-equilibrio-na-planilha.md`):
  `excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` é a referência (imutável: o arquivo na tag `v4.1`), com as abas 16 a 22 (mais 20a a 20d), 117569 fórmulas e
  1145 nomes (698 da V4.0 e 447 de `data/nomes_V4_1.csv`). De 2026-10-22 a 2026-10-27 a planilha viva da equipe foi a
  cópia da V4.1 no Google Drive da equipe (hoje em `Planilha DDS\_anteriores\`), na pasta `H:\.shortcut-targets-by-id\1Kytf4APy0OtH5Aq5PqlOwH5UY65YMX5U\T11 - Tupã\2. Projeto\Mecanica\Suspensao\Documentacao\Planilha DDS\`, com a documentação
  (LEIA-ME e .docx dos documentos do repositório) em `Documentacao\`; responsável pela planilha e pelos retratos `dados:`: o usuário (Vinicius
  Caetano). A V3.0 viva de `excel/` não tinha dados da equipe (SHA igual ao da tag `v3.0`), então a troca não precisou de
  migração. O incremento 5 em diante é a **V4.2** (usuário, 2026-10-22; `docs/registro-de-versoes-V4_1.md`).
- V4.2 (incremento 5, metas e coerência) concluída (PR #21 mesclado em 2026-10-27; tag `v4.2` no merge e05aaa5;
  `docs/registro-de-versoes-V4_2.md`; EDR-061 a EDR-063, EDR-034 decidido): fichas de meta na 03_TARGETS (H:Q), TARGET-006 e
  007, aba `23_LISTAS`, bloco de metas no 14_DASHBOARD (linhas 49 a 51), Origens do T11 e a viva no Drive. Fichas completas e
  processo em `docs/metas/`. A planilha sai de `python/gerar_v4_2.py` em `build/`; a cópia para `excel/` é um commit próprio
  (feita no commit 9cb19cf). De 2026-10-27 a 2026-11-09 a planilha viva da equipe foi a cópia da V4.2 no Drive
  (`Planilha DDS\FSAE_EV_Suspension_Fase1_V4_2.xlsx`, SHA igual ao da tag `v4.2`; `conferir_viva` código 0). A V4.1 do Drive
  não tinha dados da equipe (SHA igual ao da tag `v4.1`; `migrar_viva` com 0 dados e 0 conflitos) e foi movida para
  `Planilha DDS\_anteriores\`. Diretriz do usuário (2026-10-23): a cada versão terminada, a viva vira a versão nova com os
  dados mantidos. Em 2026-11-09 a V4.2 da viva (sem dados da equipe: `migrar_viva` com 0 dados e 0 conflitos) foi para `Planilha DDS\_anteriores\`.
- Incremento 6 (branch `feat/inc6-mmm-escada`, só Python, sem planilha nova; EDR-064 a EDR-066, adendo
  `docs/superpowers/specs/2026-10-27-inc6-mmm-escada-design.md`): `python/mmm.py` (MMM em raio fixo), `python/escada.py`
  (escada de hipóteses) e `tools/relatorio_escada.py`. Código e testes prontos; o relatório `docs/inc6/escada-hipoteses.md`
  agora roda com os dois R provisórios da 7a (9,125 m na linha central e 8,385 m rente aos cones). Nos dois, nenhum eixo satura até 2 g e todas as linhas dão N/A, com o Ackermann e a h9 desligados; por isso ele não dá base para a tolerância do EDR-065, que precisa de outro caso (Ackermann e tração ligados e um eixo que sature) ou de uma decisão sem ele.
  EDR-064 VERIFIED (suíte única do inc. 8, 2026-11-11); EDR-065 (tolerância e regra do NEUTRO) está APPROVED desde 2026-11-09
  (item 3: só não inverter o veredito; o valor da tolerância fica a confirmar com o T11) e EDR-066 (achados sobre Ackermann e
  Fx exigido) está APPROVED e IMPLEMENTED na V4.3.
- V4.3 (incremento 7, partes 7a e 7b; PRs #32 e #34 mesclados em 2026-11-09; tag `v4.3` no merge f7862de; EDR-065 itens 2 e 3,
  EDR-066, EDR-068 e EDR-069). Desde 2026-11-09 a **planilha viva da equipe é a cópia da V4.3** no Drive
  (`Planilha DDS\FSAE_EV_Suspension_Fase1_V4_3.xlsx`, SHA igual ao da tag `v4.3`; `conferir_viva` código 0), com o LEIA-ME, os
  registros de versões V4.2 e V4.3 e o EDR em .docx de 2026-11-09 em `Documentacao\` (os da V4.1 em `Documentacao\_anteriores\`). A V4.3 de referência está em `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx` (146373 fórmulas, 29 abas, 1266 nomes;
  aba nova `24_CURVA`; `docs/registro-de-versoes-V4_3.md`). Suíte inteira no Excel em 2026-11-09 (commit e94abf0): todos PASS, 2 PULADO (`test_escada`, `test_v4_3`). Revisão final feita
  (pronta para PR); minors adiados no PR #34 (pendências).
- Incremento 8 (branch `claude/frosty-jang-b87ba8`; spec e plano em `docs/superpowers/`; EDR-070 e EDR-064
  VERIFIED na suíte única de 2026-11-11): a parte 8a tratou as pendências do inc. 7 e a 8b gerou a **V4.4** (fundação parte 2,
  2026-11-09): as fórmulas das abas 03 a 14 leem por nome toda célula única, com valores iguais aos da V4.3. A V4.4 de referência é
  `excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx` (146373 fórmulas, 29 abas, 1290 nomes: os 1266 da V4.3 e 24 de `data/nomes_V4_4.csv`;
  `docs/registro-de-versoes-V4_4.md`). Mudam 428 células da V4.3: 422 fórmulas reescritas pela regra e 6 das exceções X2 a X5
  (16_EQUILIBRIO F188, limitação do K do EDR-066; 14_DASHBOARD B48; 00_README A3; 15_CHANGELOG A24:C24). **Ainda não é a viva
  do Drive**: a troca (e o LEIA-ME e os .docx) é o fechamento do incremento e só sai com a confirmação do usuário. A viva continua a
  V4.3. Suíte única feita (2026-11-10 e 11; logs `docs/migracao/verificacao-inc8-*.md`): todos os itens PASS menos o
  `test_workbook_v4_3`, que no Excel estourou os 1800 s (refeito sozinho com 7200 s: 3/3) e no LibreOffice sai com código 3 porque o
  TC-WB43-005 só roda no Excel (003 e 004 refeitos no LibreOffice: 2/2; correção do teste e do executor é pendência). Revisão final
  feita. Falta o PR, o merge e a tag `v4.4`.

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
- Esperado na V4.4 (as contagens da V4.3 continuam valendo): pneu 43, oráculos 5, pneu estático 87 (`tests/test_tire_static.py`, EDR-067; precisa dos `.tir` do TTC Round 6, fora do Git, em `references/ttc/` ou em `DDS_TTC_DIR`; sem eles sai NÃO EXECUTÁVEL), suspensão 54, cinemática 76, hardpoints 35,
  equilíbrio 28, equilíbrio linear 18 (incrementos 1 e 2), V4.0 nomes e dados 4 (`tests/test_v4_0.py`, incremento 3), V4.1 estrutura e CA-07 2 (`tests/test_v4_1.py`, TC-WB41-001 e 002), V4.2 estrutura, CA-07, oráculo das metas e fluxo da viva 4 (`tests/test_v4_2.py`, TC-WB42-001 a 004), MMM 11 (`tests/test_mmm.py`, TC-MMM-001 a 011), executor dos testes 1 (`tests/test_executor.py`, TC-RUN-001), skidpad 2 (`tests/test_skidpad.py`, TC-SKP-001 e 002), formas v43 4 (`tests/test_formas_v43.py`, TC-ACK-001/002 e TC-FXI-001/002), estudo do NEUTRO 2 (`tests/test_neutro.py`, TC-NEU-001 e 002), V4.3 estrutura, CA-07 e migração 3 (`tests/test_v4_3.py`, TC-WB43-001, 002 e 006), V4.4 regeneração, regra, invariante e migração 4 (`tests/test_v4_4.py`, TC-WB44-001 a 004), escada 3 (`tests/test_escada.py`, TC-ESC-001 a 003, ~6 min), mutação 25/25 do pneu, 6/6 do equilíbrio e 5/5 da planilha do equilíbrio (`tests/mutation_planilha_equilibrio.py`, só Excel, minutos), 5/5 do MMM (`tests/mutation_mmm.py`, ~20 min), 5/5 do inc. 7 (`tests/mutation_inc7.py`), 4/4 da planilha V4.3 (`tests/mutation_planilha_v43.py`, Excel, tempo a confirmar na suíte), 4/4 da planilha V4.4 (`tests/mutation_planilha_v44.py`, Excel, ~16 min), autoteste do comparador 15/15; V2.4 regenerada com 347 fórmulas e V3.0 com 387 (356 + 6 da 1ª rodada de feedback, EDR-050, + 19 da 2ª rodada da revisão metodológica, pior origem no 14_DASHBOARD, + 6 de direção, EDR-052), as duas com 0 diferença; V4.0 regenerada da tag `v3.0` com as mesmas 387 fórmulas e os 698 nomes, 0 diferença; V4.1 regenerada da tag `v4.0` com 117569 fórmulas e os 1145 nomes, 0 diferença; V4.2 regenerada da tag `v4.1` com 117627 fórmulas e 1225 nomes definidos no arquivo: 1220 da tabela de nomes (698 + 447 + 75) mais `Origens` e as 4 `Lista_*`, 0 diferença contra `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx`. O CA-07 da V3.0 de `excel/` passa a ser por SHA-256 igual ao da tag `v3.0` (EDR-063). A seção informativa da viva só lê cópia local, nunca a viva do Drive.
  `tests/test_workbook.py` 19/19 (pneu) e `tests/test_workbook_suspensao.py` 15/15 (suspensão),
  ambos na V3.0 de referência (arquivo da tag `v3.0`; antes da tag, o da árvore), e `tests/test_workbook_v4_0.py` 2/2
  (V4.0 de `excel/`) e `tests/test_workbook_v4_1.py` 5/5 (V4.1 de `excel/`; TC-WB41-003 a 006) e `tests/test_workbook_v4_2.py` 2/2 (V4.2 de `excel/`; TC-WB42-005 e 006) e `tests/test_workbook_v4_3.py` 3/3 (V4.3 de `excel/`; TC-WB43-003 a 005) e `tests/test_workbook_v4_4.py` 5/5 (V4.4 de `excel/`; TC-WB44-005 e 006 e 3 checagens de apoio; 61 casos, média de 66,1 s por caso no Excel; tempo total medido no Excel: 4307 s, máximo de 89,0 s por caso): recalculam cópias pelo Excel via COM ou, sem Excel, pelo
  LibreOffice (EDR-044; `DDS_RECALC=excel|libreoffice` força um). Sem nenhum dos dois eles
  saem NÃO EXECUTÁVEL, que nunca conta como aprovado.
- Planilha V3.0, **fechada em 2026-10-20** (EDR-051). `excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx`
  foi o arquivo vivo da equipe até 2026-10-22 (hoje a viva é a cópia da V4.2 no Drive; o CA-07 "viva × referência"
  da suíte passa, na V4.2, a conferir que este arquivo é igual ao da tag `v3.0`, EDR-063); a referência imutável é o mesmo arquivo na tag `v3.0`. A V3.0 de referência é
  gerada da V2.4 por `python/atualizar_planilha.py` (toda célula alterada fica em `alteracoes()`, com fonte e EDR);
  o script recusa gravar por cima da planilha viva. CA-07: a regeneração bate com a referência, e a viva bate
  com a referência em tudo menos as células de entrada (`atualizar_planilha.celulas_de_entrada()`). Mudança
  de fórmula ou estrutura entra na próxima planilha gerada, nunca editando a planilha à mão. A **V4.0** já existe
  (fundação: nomes definidos, fórmulas iguais às da V3.0; os textos da V3.0 que dizem "V3.1" se referem a ela); a
  **V4.1** (equilíbrio em fórmulas) também já existe; a próxima planilha com mudança de fórmula ou estrutura sai a
  partir do incremento 5, com versão a definir com o usuário.
- V4.0 de referência (EDR-058): `python/gerar_v4_0.py` a gera da tag `v3.0` em `build/` (nunca em `excel/`; a cópia
  para `excel/` é um commit próprio), com os nomes de `data/nomes_V4_0.csv` (`python/nomes_v4_0.py`); só mudam
  00_README A3 e a linha 20 do 15_CHANGELOG (`docs/registro-de-versoes-V4_0-celulas.md`). Migração dos dados da viva,
  por nome: `uv run python -X utf8 tools/migrar_dados_v3_v4.py <viva_V3_0.xlsx>` (saída em
  `build/V4_0_com_dados.xlsx`, relatório em `build/migracao-V3-V4.md`); conflito é listado e nunca sobrescrito
  (código 1), célula alterada fora dos nomes de dado é erro (código 2). Commit de dados da equipe é separado
  (`dados: ...`), com `tools/extrato_entradas.py` para o diff legível. A metodologia segue a literatura, principalmente o
  Milliken (usuário, 2026-10-19; `docs/revisao-metodologica.md`). Os livros e o OCR ficam
  em `references/` (fora do Git); busque no `.md`, mas confira a equação na imagem do PDF.
- V4.1 de referência (EDR-059, EDR-060): `python/gerar_v4_1.py` a gera da tag `v4.0` em `build/` (nunca em `excel/`; a
  cópia para `excel/` é um commit próprio), com `python/aba_equilibrio.py` (famílias de fórmula F1-F19; o texto exato de
  cada célula sai do gerador, e `docs/registro-de-versoes-V4_1-celulas.md` resume por aba e família) e os nomes de
  `data/nomes_V4_1.csv`. Células existentes alteradas: 10_TIRE (Fz, α, γ e κ limitados à faixa, EDR-056), 13_VALIDATION
  B40:B43/C43, textos da §12.1 e 00_README A3, A37, A53. O caso da planilha lido por nomes é
  `caso_planilha.caso_da_planilha_v41`. O relatório que a célula de robustez cita (varredura do pneu, EDR-055, que NÃO
  é recalculada na planilha) sai de `uv run python -X utf8 tools/relatorio_inc4.py --sobrescrever` (Excel ou
  LibreOffice, em cópia). Os únicos IDs novos desse incremento são SUS-1001 a SUS-1008, EDR-059, EDR-060 e TC-WB41-001 a 006.
- V4.2 (EDR-061 a EDR-063; suíte inteira de 2026-10-27 sobre o commit 9cb19cf, `build/verificacao-ultima.md`: no Excel, todos os itens PASS, com test_workbook 19/19, suspensão 15/15, V4.0 2/2, V4.1 5/5 e V4.2 2/2; no LibreOffice, os mesmos cinco em 19/19, 15/15, 2/2, 5/5 e 2/2): `python/gerar_v4_2.py`
  gera a V4.2 da tag `v4.1` em `build/` (nunca em `excel/`). Testes: `tests/test_v4_2.py` (TC-WB42-001 a 004) e
  `tests/test_workbook_v4_2.py` (TC-WB42-005 e 006, Excel via COM). Regras das fichas em `python/metas.py` (oráculo) e
  `python/aba_metas.py`. A viva do Drive (`python/viva.py`) só é lida por cópia, nunca gravada nem recalculada:
  `uv run python -X utf8 tools/conferir_viva.py [ARQ]` (0 fiel, 1 diverge, 3 não lida; roda antes de todo retrato e de toda
  troca); `tools/retrato_viva.py` (grava `data/viva/retrato-viva.json`, só se a conferência der 0; commit `dados:`);
  `tools/migrar_viva.py VIVA --para REF_NOVA.xlsx` (leva os dados à versão nova por nome; conflito listado, nunca
  sobrescrito); `tools/medir_recalculo.py` (tempo de recálculo da V4.1 no Excel, em cópia). A viva do Drive é seção informativa
  do log da suíte, fora do resumo.
- V4.3 (EDR-065 itens 2 e 3, EDR-066, EDR-068 e EDR-069): `python/gerar_v4_3.py` gera a V4.3 da tag `v4.2` em `build/` (nunca em
  `excel/`; a cópia para `excel/` é um commit próprio). A aba `24_CURVA` sai de `python/aba_curva.py`. Testes: `tests/test_v4_3.py`
  (TC-WB43-001, 002 e 006) e `tests/test_workbook_v4_3.py` (TC-WB43-003 a 005, Excel via COM ou LibreOffice). V4.3 regenerada da tag
  `v4.2` com 146373 fórmulas e 1266 nomes, 0 diferença contra `excel/FSAE_EV_Suspension_Fase1_V4_3.xlsx`. A troca da viva segue o
  fluxo da V4.2: `tools/conferir_viva.py` (código 0) antes de tudo e `tools/migrar_viva.py VIVA --para REF_NOVA.xlsx` para levar os
  dados por nome (conflito listado, nunca sobrescrito); a viva do Drive só é lida por cópia.
- V4.4 (EDR-070; EDR-066 item 5): `python/gerar_v4_4.py` gera a V4.4 da tag `v4.3` em `build/` (nunca em `excel/`; a cópia para `excel/`
  é um commit próprio), com a regra da troca de `python/reescrita_nomes.py`, os nomes de `data/nomes_V4_4.csv` (`python/nomes_v4_4.py`) e
  o catálogo `docs/registro-de-versoes-V4_4-celulas.md` (gerado, nunca editado à mão). V4.4 regenerada da tag `v4.3` com 146373 fórmulas e
  1290 nomes, 0 diferença contra `excel/FSAE_EV_Suspension_Fase1_V4_4.xlsx`. Testes: `tests/test_v4_4.py` (TC-WB44-001 a 004) e
  `tests/test_workbook_v4_4.py` (TC-WB44-005, equivalência por valor com tolerância zero, e TC-WB44-006, cobertura de ramos; Excel via COM
  ou LibreOffice; limite do item 7200 s). Os casos perturbados são sintéticos de teste, nunca dado do carro. Com `DDS_CASOS44` o
  TC-WB44-006 sai PULADO, que nunca conta como PASS. A V3.0 a V4.3 mantêm o CA-07 como está; a V4.5 volta ao CA-07 por texto, contra a V4.4.
  Antes de qualquer troca da viva: `tools/conferir_viva.py` (código 0) e `tools/migrar_viva.py VIVA --para REF_NOVA.xlsx`.
- `tools/rodar_testes.py --pular-recentes ARQ` (ARQ é um JSON `{"tests/x.py": "<commit>"}`, com o commit em que o teste passou): pula o item cujo conjunto conferido não mudou desde esse commit, nem na árvore de trabalho: o script, os imports locais transitivos (python/, tests/ e tools/, por ast; sem import relativo, de pacote ou dinâmico) e as entradas declaradas do item em `DEPENDENCIAS` (módulos e testes que a mutação abre por caminho, planilhas de `excel/` e dados). Arquivo novo ou não rastreado no conjunto impede o pulo; chave do JSON sem item gera aviso. O item aparece como `PULADO (passou em <commit>; código sem mudança)`, nunca conta como PASS e tem contagem própria; ficam fora da conferência o `.tir` do TTC (não versionado), o que o script lê sem declarar e o ambiente. Sem a opção, nada muda. Para valer como verificação, rode a suíte inteira sem a opção.
- Rode os testes afetados antes de dizer que uma tarefa terminou.

## Fontes de verdade
- Ordem em caso de divergência: `docs/Engineering_Decision_Register.md` → Engineering
  Standard V2.0 → arquitetura V2.0 → data contract V2.4 → registros de versões.
- O `HANDOFF-Sistema_DDS.md` resume e indexa; não substitui os originais.
- Orientação: `MAPA.md` (raiz, ~12 mil tokens) é o mapa estrutural do projeto (árvore, símbolos do código,
  abas das planilhas, sumário dos PDFs e a lista dos arquivos que não se leem inteiros). Leia-o ou busque
  nele antes de explorar pastas; não é fonte de verdade nem é importado aqui. Gerado por
  `~/.claude/skills/gestor-tokens/scripts/mapa_projeto.py`; regenerar (com `--sobrescrever`) quando a
  estrutura mudar.
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
