# Proposta: EDR-043 (versão apresentada ao usuário)

Registro histórico da proposta como foi apresentada em 2026-10-18. O usuário autorizou em
2026-10-19 a alternativa (b), com as três recomendações: dados mantêm `_V2.0`, imports pelo uv,
EDR-017 vira SUPERSEDED. O registro vigente está em `docs/Engineering_Decision_Register.md`.

### EDR-043 — Versionamento por Git e nomes estáveis (revisa o EDR-017)

- **Date:** 2026-10-18
- **Status:** AWAITING_DECISION
- **Context:** O EDR-017 versiona pelo nome do arquivo (`tire_model_V2_4.py`,
  `test_suspension_model_V2_1.py`) e nunca sobrescreve os históricos. Com o
  projeto no Git, isso gera três problemas: (1) toda versão nova exige mudar os
  imports de todos os scripts que usam o módulo; (2) teste e módulo têm versões
  diferentes no nome (`test_kinematics_model_V2_1.py` testa `kinematics_model_V2_0.py`),
  como o próprio EDR-017 já previa em Consequences; (3) o histórico passa a
  existir em dobro, no nome e no Git. A fase A (tag `v2.4.1`) provou a
  reprodução com os nomes originais, o que torna a renomeação verificável.
- **Question:** Como versionar código, testes, dados e planilha a partir da V2.4.1?
- **Alternatives:**
  - (a) manter o EDR-017 como está (versão no nome de tudo);
  - (b) **híbrido**: Git com tags para código, testes, dados e docs, com nomes
    estáveis; a planilha entregue à equipe mantém a versão no nome (D1 do SPEC);
  - (c) Git para tudo, inclusive a planilha com nome estável.
- **Decision (proposta):** (b), a decisão D1 do conselho, já aprovada como
  direção no SPEC. Na prática:
  1. **Código e testes** sem versão no nome: `tire_model.py`, `suspension_model.py`,
     `kinematics_model.py`, `hardpoints.py`, `build_workbook.py`,
     `mutation_tire.py`, e os testes `test_<módulo>.py` em `tests/`.
  2. **Dados [decidir]:** (i) nomes estáveis também (`hardpoints_synthetic.csv`),
     com a versão do schema só dentro do `.meta.json`; ou (ii) manter o sufixo
     `_V2.0`, porque ali ele é a versão do *schema* de hardpoints (EDR-024), e não
     a revisão do arquivo. Recomendação: (ii).
  3. **Planilha:** continua `FSAE_EV_Suspension_Fase1_V2_x.xlsx` (a equipe usa o
     arquivo fora do Git). A versão gravada dentro dela é o passo 3 da fase B, com
     aprovação própria.
  4. **Versão do projeto:** tag Git anotada `vX.Y.Z` a cada entrega. `X.Y`
     acompanha a versão da planilha (V2.4 → `v2.4.z`) e `Z` sobe em mudanças sem
     efeito na planilha. O decimal continua subindo a cada pequena implementação,
     como no EDR-017.
  5. **Históricos:** "nunca sobrescrever" passa a ser garantido pelas tags do Git,
     por `importado-claude-ai/` (somente leitura) e pelo backup na OneDrive. A
     referência V1.0 usada pelo `TC-SUS-V2-004` fica congelada em
     `tests/regressao/suspension_model_V1_0.py`, com o nome original, porque o
     teste compara contra aquela versão específica.
  6. **Imports [decidir]:** como os testes em `tests/` acham os módulos em
     `python/`: (i) o `uv sync` instala o projeto em modo editável e põe `python/`
     no caminho de import (uma mudança no `pyproject.toml`, sem tocar nos
     scripts); ou (ii) cada teste insere `python/` no `sys.path`. Recomendação: (i).
- **Rationale:** Nomes estáveis acabam com a mudança de imports a cada versão e
  com o descompasso entre teste e módulo. O Git guarda o histórico com hash e
  data, em vez de cópias. A planilha fica fora dessa regra porque circula fora do
  Git.
- **Evidence:** Fase A: CA-01 a CA-12, tag `v2.4.1`,
  `docs/migracao/verificacao-V2.4-local.md`. Os scripts acham dados por
  `HERE = os.path.dirname(__file__)` (test_hardpoints:7-8, test_kinematics:21,
  test_tire_model:9-10, test_tire_oracles:13-14, test_suspension:267-268) e os
  módulos por import com a versão no nome.
- **Assumptions:** H1: a equipe não depende dos nomes `_V2_x` dos `.py` fora deste
  repositório (não verificado). H2: a confirmação explícita do "V2" pelo usuário,
  ausente no EDR-017, vale a partir desta decisão.
- **Consequences:** A renomeação é um commit próprio de reestruturação, que só
  move arquivos e ajusta imports e caminhos. Nenhuma equação muda, e os testes
  precisam dar o mesmo resultado da fase A (43, 5, 42, 53, 35; mutação 23/23;
  planilha com 347 fórmulas e 0 diferença). O `MANIFEST.sha256` continua valendo
  para a tag `v2.4.0-import`. O `tools/` passa a apontar para os nomes novos.
- **Affected_Artifacts:** `python/*.py`, testes (para `tests/`), dados lidos
  pelos testes (para `data/`), `tools/rodar_testes.py`, `tools/comparar_planilhas.py`,
  `pyproject.toml`, `CLAUDE.md`, `python/README.md`, SPEC.
- **Affected_Tests:** todos os da fase A; o critério é o mesmo resultado.
- **Dependencies:** EDR-017; SPEC D1 e E1.
- **Approval_Conditions:** [decidir]
- **Reopening_Criteria:** a equipe precisar dos `.py` versionados fora do Git, ou
  qualquer diferença de resultado depois da renomeação (vale o R5).
- **Related_Decisions:** EDR-017. **[decidir]** se o EDR-017 vira SUPERSEDED
  (recomendado, porque o EDR-043 repete a regra da planilha) ou continua APPROVED
  só para a planilha.
- **Source_Conversation_or_Document:** Conselho (veredito D1), SPEC §3 e §11,
  sessão de 2026-10-18.
