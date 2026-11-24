# Experimento δ (giro do push rod no rocker): resultado

**O que mudou no código** (EDR-076, proposta do conselho 2, aprovada pelo usuário em 2026-11-24; nenhuma meta nem limite alterado):
`mecanismo.Variaveis.delta_rad` (padrão 0 = tangente, como no script de atuação) gira o ponto do push rod no rocker (A0) em volta do
eixo do rocker; `busca.buscar(..., delta_max_rad)` acrescenta δ como 8ª variável (padrão 0 = comportamento anterior); a linha de comando
ganhou `--delta-max` (graus, padrão 25 = faixa de busca, não meta) e `--aval-refino` (avaliações por refino, padrão 60). O r2 continua
resolvido para MR(0) = 1,40 e a tolerância de MR(0) não foi tocada. Testes de mecanismo (6/6), busca (7/7) passam.

**Experimento** [código, STEP T11 com referencial HIPOTESE, orçamento igual, sementes 0 a 2, 3 sementes por braço = retrato, não estatística]:

| Rodada | δ travado em 0 | δ livre (±25°) |
|---|---|---|
| 100 amostras, 10 refinos de até 60 avaliações | 0/3 viáveis; violação final 0,21 a 3,77 % | 0/3 viáveis; violação final 0,07 a 0,22 % |
| 60 amostras, 4 refinos de até 500 avaliações | **0/3** viáveis; violação final 0,17 a 0,32 % | **2/3** CONDICIONAL (δ = −17,6° e −11,3°; variação de MR 3,67 % e 3,36 %) |

**Leitura.** [inferência] Liberar δ aumentou a chance de a busca achar posição que cumpre todas as metas conferidas, sem mudar meta nenhuma;
a profundidade do refino pesa tanto quanto δ (a rodada rasa não achou nenhuma). [código] As duas posições achadas são **frágeis**: folga do
comprimento mínimo do amortecedor de 0,0015 e 0,0076 mm, olhal no limite máximo (1e-9 m), `r1` e ângulo do amortecedor colados nos limites; elas
não são uma solução, são prova de que a região viável existe com folga ≈ 0. O veredito segue CONDICIONAL (nada é VIAVEL nesta fase) e a cinemática
segue NOT_VALIDATED. Sem tolerância de fabricação medida, não dá para dizer se são fabricáveis.

**Próximo passo de maior retorno (proposta):** maximizar a margem mínima (busca em duas fases: viabilidade, depois margem) e relatar cada violação
em unidade física; depende de decisão da equipe sobre a margem de fim de curso do amortecedor.
