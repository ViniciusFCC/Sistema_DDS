# Briefing comum do conselho

Você é um assento de um conselho técnico rigoroso de 7 assentos. Responda em português, prosa densa.

PASTA: /tmp/claude-0/-home-user-Sistema-DDS/6637db41-949f-5b01-8433-f10e3fa5c55a/scratchpad/atuacao/

LEIA, nesta ordem:
1. `REGISTRO.md` (contexto, achados medidos sobre o script, plano).
2. `conselho/PROTOCOLO.md` (perguntas Q1–Q5 e regras).
3. Os cinco relatórios da fase 1: `geo/RELATORIO_GEO.md`, `lit/RELATORIO_LIT.md`, `regras/RELATORIO_REGRAS.md`,
   `pratica/RELATORIO_PRATICA.md`, `skills/RELATORIO_SKILLS.md`. Veja `geo/vistas_dianteira.png`.
4. O código, se precisar: `script_script/t11_atuacao.py`, `script_script/kinlib.py`, `geo/step_tubos.py`,
   `geo/tubos.json`, `geo/nos.json`, `geo/confronto_v20.json`.

PODE rodar verificações rápidas (minutos, não horas) com `geo/.venv/bin/python -I -B` (tem numpy, scipy, matplotlib,
OCP), gravando scripts e saídas só em `conselho/assento<N>_trabalho/`. Não altere nenhum outro arquivo da pasta, não
escreva fora dela, não faça commits, não acesse a internet salvo para conferir uma fonte já citada nos relatórios.

O QUE O USUÁRIO QUER: avaliar se o método atual (script de atuação) é o ideal e qual método/arquitetura adotar para um
script que reconheça tubos e nós do chassi (CAD incompleto, em evolução junto com a suspensão) e sugira posições
cabíveis para push rod, rocker e amortecedor da dianteira, com confiabilidade (o que ele aprova tem de ser válido).

RESPOSTA: grave em `conselho/resposta_assento<N>.md` respondendo Q1–Q5 do protocolo, ≤ ~900 palavras, com rótulos
(fato de fonte com a referência do relatório, resultado de código, cálculo, inferência, hipótese). Termine com
"Recomendação em uma frase" e "Confiança e principal incerteza". Não mencione o número nem o nome do seu assento dentro
do texto da resposta (a revisão será anônima). Discorde dos relatórios quando tiver motivo, dizendo por quê.
Na resposta final ao orquestrador, devolva só o caminho do arquivo e a recomendação em uma frase.
