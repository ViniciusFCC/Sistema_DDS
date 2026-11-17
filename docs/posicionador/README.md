# Posicionador de pontos da atuação (T11) — documentação

Ferramenta em Python que diz onde push rod, rocker e amortecedor da dianteira podem ficar sem colidir com os gabaritos do
regulamento e com as outras peças do CAD (EDR-076). Não dita tubos e não faz análise estrutural. Não é integrada à planilha.

- Spec: `docs/superpowers/specs/2026-11-17-posicionador-atuacao-design.md`; plano: `docs/superpowers/plans/2026-11-17-posicionador-fase1.md`.
- `registro-de-decisoes.md`: registro da conversa de 2026-11-17 (contexto, achados medidos, diretrizes U1–U6 do usuário,
  correções). Os caminhos `scratchpad/atuacao/...` citados nele e nos relatórios são da pasta de trabalho da sessão, que não
  está no repositório; os arquivos equivalentes estão aqui.
- `pesquisa/`: relatórios gerados por agentes (Claude) em 2026-11-17, cada afirmação rotulada (fato de fonte, código,
  cálculo, inferência, hipótese). São insumo, não fonte de verdade; a fonte de verdade é o EDR.
  `relatorio-geo.md` (STEP do chassi), `relatorio-lit.md` (literatura, modo rigoroso), `relatorio-regras.md` (FSAE Rules
  2027 V1.0), `relatorio-pratica.md` (ferramentas e práticas), `relatorio-skills.md`, `relatorio-fusion.md` (API do Fusion),
  `relatorio-academico.md` e `relatorio-equipes.md` (comparação com equipes de topo).
- `conselho/`: conselho rigoroso de 7 assentos (protocolo, respostas, revisões anônimas e síntese). Letras da revisão:
  A = assento 4 (CAD/software), B = 3 (otimização), C = 5 (cético), D = 6 (pragmático), E = 1 (cinemática),
  F = 2 (estrutura), G = 7 (regras/manufatura).
- Não versionados (de propósito): PDFs e textos baixados de terceiros, figuras do regulamento, o venv de OCP.
