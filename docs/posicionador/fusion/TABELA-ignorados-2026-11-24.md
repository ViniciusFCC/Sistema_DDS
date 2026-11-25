# Itens `IGNORAR` do T11 (cópia com nomes corrigidos), separados em dianteiro e traseiro — 2026-11-24

Fonte: `fusion_sondagem3_copia_nomes_corrigidos_2026-11-24.json`, saída `tabela_ignorados` do portão de identificação. Caixas no referencial do carro (mm; X para a frente, origem em `REF_ORIGEM`; o eixo dianteiro está em X ≈ 0). A coluna "função" é leitura do nome e da posição, não confirmada com o CAD pelo usuário.

Regra proposta pelo usuário (2026-11-24, "em tese"): na versão só da dianteira, o dianteiro fora do cálculo entra como obstáculo; o traseiro segue ignorado.

| Componente | Corpos | Caixa X (mm) | Lado | Função (a confirmar) | Pela regra |
|---|---|---|---|---|---|
| `IGNORAR_ATUACAO_DIANTEIRA` | 10 | −44 a 14 | dianteiro | a atuação que o posicionador calcula | fora do cálculo? **não**: é o objeto da busca; ignorar |
| `IGNORAR_ROCKER_FE/FD_V20_1` | 3 + 3 | −31 a 1 | dianteiro | rockers da v20 (atuação) | idem: ignorar |
| `IGNORAR_PUSHROD_FE/FD_V20_1` | 13 + 13 | −22 a 4 | dianteiro | push rods da v20 (atuação) | idem: ignorar |
| `IGNORAR_AMORTECEDORES_DNM_ARQUIVO` | 20 | −1599 a 261 | **dianteiro e traseiro no mesmo componente** | amortecedores (os dianteiros são a atuação) | decisão pendente: ver abaixo |
| `IGNORAR_GABARITO_T1_2` | 1 | 331 a 338 | dianteiro | volume do gabarito do piloto | não é peça: o regulamento já o trata (`gabarito T.1.2`); ignorar |
| `IGNORAR_PONTOS_V20_1`, `IGNORAR_PLANOS` | 0 | — | — | vazios | nada a fazer |
| `IGNORAR_TRASEIRA` e 11 `IGNORAR_TRAS_*` (bandejas, rockers, push rods, toe links, TE e TD) | 14 + 13 + 13 + 15 + 15 + 3 + 6 + 13 + 13 + 11 + 11 | −1830 a −1309 | traseiro | suspensão e conjunto traseiros | ignorar (versão só dianteira) |

## Achado
Pela leitura dos nomes e das posições, **nenhum item dianteiro fica fora do cálculo e seria promovido a obstáculo**: tudo o que é dianteiro e `IGNORAR` é a própria atuação (o que o posicionador posiciona), o gabarito (já tratado pelo regulamento) ou está vazio. A regra "dianteiro fora do cálculo = obstáculo" é segura, mas hoje não muda nada.

## Pendências
- `IGNORAR_AMORTECEDORES_DNM_ARQUIVO` junta os amortecedores dianteiros e traseiros num componente só (X de −1599 a 261 mm). Os dianteiros são a atuação em busca; se o amortecedor real do carro for restrição ao chassi, o arquivo precisa ser separado em dianteiro e traseiro, ou o adaptador tratar por corpo. Decisão do usuário.
- Se o CAD ganhar peça dianteira nova (suporte, sensor, cabo) com nome `IGNORAR_`, ela cairia na regra e viraria obstáculo; o adaptador deve listar, a cada execução, o que a regra promoveu.
