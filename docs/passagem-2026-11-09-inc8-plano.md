# Passagem 09/11/2026: spec do incremento 8 pronta; próximo passo é o plano

Sessão anterior: brainstorming do incremento 8, com `docs/passagem-2026-11-09.md` como entrada. Esta passagem substitui o
histórico daquela sessão.

## Estado

- Spec: `docs/superpowers/specs/2026-11-09-inc8-fundacao-nomes-design.md` (commit 1b3c1d8, branch
  `claude/inc7-7b-v43-0c2266`, ainda não enviada ao GitHub). Ela traz todas as decisões, com a marca de quem decidiu
  (usuário ou controlador).
- IDs autorizados pelo usuário: EDR-070 e TC-WB44-001 a 006. Nenhum outro.
- A planilha da 8b se chama V4.4. A viva do Drive continua na V4.3.
- Nenhum código mudou nesta sessão; nenhum teste rodou.

## Regras vigentes para o plano e a execução

- O usuário pediu (2026-11-09) que o trabalho siga sem interrupção, com as decisões informadas. Isso não libera push, PR,
  merge, tag nem gravação no Drive: esses continuam pedindo confirmação.
- Fórmula ou texto de célula só muda pela regra da troca (spec 3.3) ou como exceção aprovada uma a uma (spec 3.4). Os 9
  nomes novos e o texto da limitação do K são aprovados pelo usuário no plano.
- Só Sonnet nos subagentes, inclusive nas revisões. Uma única suíte inteira, no fim do incremento (spec §7); antes disso, só
  os testes afetados.
- `export UV_SYSTEM_CERTS=1` antes do `uv`; um `uv run` por vez; encerrar o Excel só por PID; gravar arquivos em LF.

## Próximo passo

Conversa nova: `superpowers:writing-plans` a partir da spec. O plano começa pela 8a (spec §6 e §11) e mede, na 8b, o tempo de
recálculo da V4.3 para fixar o N dos casos perturbados.
