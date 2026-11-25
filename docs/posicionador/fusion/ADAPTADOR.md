# Adaptador do Fusion (fase 2): desenho, decisão da cena e medições — 2026-11-24

Escopo: EDR-077. Sem ID novo de TC/EDR (aguarda autorização). Rótulo: VERIFIED ≠ validado; a cinemática segue NOT_VALIDATED.

## O que é
Um **script** do Fusion (`T11_posicionador/`, instalado em `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\T11_posicionador\`), não um add-in: roda sob demanda (Shift+S), não precisa de instalação persistente. É só leitura: nada é salvo nem alterado; os corpos temporários (cilindros finos) vivem em memória.
Os módulos ficam no repositório (`python/posicionador/fusion/`) e o script os importa pelo caminho de `C:\Projetos\posicionador_fusion_config.json` (`raiz_repo`), recarregando-os a cada execução (o Fusion mantém `sys.modules` entre execuções). Só `api.py` e `medicao.py` importam `adsk`; o resto roda e é testado fora do Fusion.

Fluxo (`pipeline.executar`): leitura do CAD (`api.ler_geometria`) → portão de identificação (`identificacao.verificar`; FALHA bloqueia) → regra de obstáculos (`obstaculos.classificar`) → um `FixoFusion` por corpo sólido de obstáculo → hardpoints (CSV `hardpoints_T11_v20_1_cad.csv` com os 9 `HP_FL` lidos ao vivo do CAD; diferença > 0,5 mm vira aviso e vale o CAD) → caixa de busca (X da configuração; Y e Z do envelope das caixas dos corpos: HIPÓTESE) → `puro.busca.buscar`. Saídas: `resultado.json`, `relatorio.md`, um CSV por candidato.

## Regra de obstáculos
CHASSI e FIXO entram sempre. Entre os `IGNORAR`: vazio, traseiro (`TRAS` no nome ou caixa toda atrás de X = −500 mm), objeto da busca ou do regulamento (ATUACAO, ROCKER, PUSHROD, AMORTECEDOR, GABARITO) ficam fora; **misto** (caixa cruza X = −500 mm: hoje só `IGNORAR_AMORTECEDORES_DNM_ARQUIVO`) fica fora e é listado como decisão pendente; qualquer outro dianteiro é **promovido**. No T11 atual a regra não promove nada (confere com `TABELA-ignorados-2026-11-24.md`); o relatório lista a cada execução o promovido, o misto e o ignorado com o motivo. A divisa −500 mm e a lista de nomes são HIPÓTESE minha, lidas da tabela; a decisão é do usuário.

## Decisão: a cena usa a API de distância, não primitivos aproximados
Medido no Fusion 2706.1.17, Python 3.14.7, cópia `T11_atuacao_v20_1_murilo_teste_nomes_corrigidos`, 27 corpos de chassi (`saidas_2026-11-24/medicao.json`, script no modo `medicao`):

| Medida | Resultado |
|---|---|
| Semântica da API ao tocar (E1) | `measureMinimumDistance` devolve 0 (7e-15 cm), sem erro, quando o cilindro fino toca a parede; respeita o tubo oco (eixo dentro do furo: 1,06 cm = raio do furo − raio fino); distância certa fora (±0,02 cm) |
| Corpos do chassi (E2) | 56 faces cilíndricas, 20 toroidais, 196 planas; volume/volume da caixa alinhada: 0,003 a 0,22 (mediana 0,05) |
| Uma caixa alinhada por corpo × API (E4, 300 segmentos, raio 10 mm) | a caixa dá colisão onde a API dá livre em **69 de 300** (23 %), com folga até 100 mm menor; nenhuma colisão perdida |
| Custo por segmento com filtro por caixa (E3) | 0,56 ms (3,4 % chegam à API) contra 9,7 ms sem filtro; diferença do resultado filtrado contra o exato (60 segmentos): 0 |
| Custo por ponto, mapa de espaço livre (E5) | 0,10 ms |
| Um candidato inteiro (E6, v20, n = 11 / n = 25) | 0,089 s / 0,199 s com a API; 0,062 s / 0,134 s sem obstáculos (a API soma ~30 a 65 ms) |
| Busca completa no Fusion | 2000 amostras, 20 refinos, passo do mapa 10 mm: **371 s**, 119 988 chamadas à API (68 s nelas), 0 erros |

Por que não primitivos: (1) a aproximação mais simples que o Fusion permite sem OCP (caixa por corpo) reprova 23 % dos segmentos que a API libera; (2) cápsulas por tubo exigiriam reimplementar na API a classificação de `cad_step` (tubo reto, curvo, quadrado, dobras, conferência de cobertura), com risco de erro em geometria que a API já mede exatamente; (3) o custo da API, com o filtro por caixa, é de dezenas de milissegundos por candidato: não há ganho de tempo que pague o risco. Os primitivos continuam valendo para o mapa de pivôs no pacote da fase 1 (STEP); no Fusion, o mapa também sai da API.

## Como a folga é medida (cena.py)
Um cilindro **fino** (raio 0,2 mm) sobre o eixo do segmento, temporário, medido contra cada corpo; folga = d_fino − raio. O cilindro fino contém o segmento e cabe na cápsula de raio 0,2 mm, então a folga sai no máximo 0,2 mm abaixo da verdadeira (conservadora), e vale com penetração parcial. O núcleo chama esse método por um hook em `puro.geometria.folga_segmento` (o primitivo que define `folga_segmento` mede por conta própria; os demais seguem pela SDF, igual a antes). Saturação em 50 mm (`corte_m`): se a caixa do segmento com o raio está a 50 mm ou mais da caixa do corpo, devolve 50 mm sem chamar a API (a distância entre caixas é limite inferior).

## Limites (não escondidos)
- **Profundidade de penetração não existe**: se o eixo do segmento atravessa o corpo, a API só diz "toca" e a folga vale −raio, não −(raio + profundidade). O estado VIOLADA é correto; o valor do objetivo do refino é menos informativo nesses casos.
- Folga aos fixos saturada em 50 mm nos relatórios; os nós do chassi não são identificados no Fusion (sorteio de pivôs uniforme; critérios de proximidade ao nó zerados): a ordem entre candidatos viáveis difere da fase 1.
- Caixa de busca derivada das caixas dos corpos (Y 0 a 326 mm, Z 65 a 1270 mm), HIPÓTESE como na fase 1; amostragem 2000 não prova que não existe posição viável.
- Peças móveis (bandejas, rodas, tirantes) e manga/freio/pinça continuam fora (NAO_VERIFICAVEL), como na fase 1.
- Medido num único modelo (a cópia com nomes corrigidos), numa única máquina e numa build do Fusion.

## Resultado da execução completa (2026-11-24, semente 0)
Nenhum candidato viável: 99,7 % das amostras violam a variação de MR; a menor violação máxima normalizada foi 0,0030 e o candidato convergido fica INVIAVEL por comprimento mínimo do amortecedor e braço r2. Coerente com a fase 1 (STEP, 200 amostras): outro gerador de números aleatórios e outro obstáculo (API em vez de primitivos), então só a conclusão qualitativa é comparável. `saidas_2026-11-24/relatorio.md`.

## Núcleo no Python 3.14 do Fusion
`tests/test_posicionador_puro_interpretadores.py`: o mesmo resumo (v20 convergida com e sem obstáculos, Nelder-Mead, brentq, busca de 40 amostras com semente) no 3.13 do repositório e no `python.exe` 3.14.7 do Fusion: iguais a 1e-9. Dentro do Fusion o núcleo rodou a busca acima.

## Repetir
1. Abrir a cópia do T11 no Fusion; escrever `C:\Projetos\posicionador_fusion_config.json` (modelo na docstring do script); Shift+S, buscar `T11_posicionador`, ▶. Saída em `saida`: `status.json`, `progresso.log`, `resultado.json`, `relatorio.md`.
2. Fora do Fusion: `uv run python -X utf8 tests/test_posicionador_fusion_adaptador.py` e `tests/test_posicionador_puro_interpretadores.py`.
