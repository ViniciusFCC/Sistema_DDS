# T11_posicionador: posicionador da atuação dianteira dentro do Fusion

Para quem vai rodar: Murilo. Versão do pacote: 0.2 (2026-11-24). Rótulo obrigatório de qualquer resultado: **VERIFIED ≠ validado; a cinemática é NOT_VALIDATED contra o OptimumKinematics.**

## O que faz
Lê o CAD aberto no Fusion e procura posições para o pivô do rocker, o push rod e o amortecedor da suspensão dianteira esquerda que respeitem as restrições do projeto (variação de MR, curso e ângulo do amortecedor, folgas ao aro, às bandejas, ao tirante e ao chassi, gabarito e AIP quando houver dados). A folga ao chassi é medida **pela própria API de distância do Fusion**, corpo a corpo, sem aproximar o chassi.

**É somente leitura.** Não cria geometria, não salva e não fecha documentos. Os cilindros usados para medir existem só na memória.

## Instalar (uma vez)
1. Copie a pasta `T11_posicionador` inteira para `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\` (cole esse caminho na barra do Explorador). Ou, no Fusion: `Shift+S` > aba Scripts > botão `+` > "Script or add-in from device" > escolha a pasta.
2. Não precisa de Python, pip nem administrador: usa o Python que já vem no Fusion.

## Rodar
1. Abra o T11 (o arquivo com `REF_REFERENCIAS`, `HP_FRENTE` e o chassi) em modo **Design**.
2. `Shift+S`, procure `T11_posicionador`, clique no ▶.
3. A busca padrão (2000 amostras, 20 refinos) leva **uns 6 minutos** no computador onde foi medida. A janela do Fusion pode parecer lenta; não feche. Acompanhe pelo arquivo `progresso.log` na pasta de saída.
4. No fim aparece uma caixa com o resumo. A pasta de saída é `Documentos\T11_posicionador_saida`: abra `relatorio.md`.

Quer uma rodada rápida para testar? Edite `posicionador_config.json` (na pasta do script) e ponha `"n_amostras": 200, "n_refinos": 5` (cerca de 1 minuto: 62 s medidos).

## O que sai
- `relatorio.md`: veredito, obstáculos usados (e o que foi promovido, ignorado ou decidido por corpo), avisos, o que **não** é modelado, custo da API e, se houver, os candidatos.
- `resultado.json`: o mesmo em dados (metros, ISO 8855: X frente, Y esquerda, Z cima).
- `candidato_NN.csv`: hardpoints do candidato (schema V2.0, Status PROVISIONAL).
- Se **nenhum candidato for viável**, o relatório mostra quais restrições são violadas em que fração das amostras e qual foi o melhor caso. Isso também é resultado.

## Antes de confiar (leia)
- **Portão de identificação.** Antes de calcular, o script confere pelos nomes e pela geometria se cada componente é o que o nome diz (lados, contagens, esferas `REF_` e `HP_`). Se houver FALHA, ele para com uma mensagem dizendo qual; corrija o CAD (ou o mapa de nomes) e rode de novo. Avisos não bloqueiam.
- Hardpoints: os 9 `HP_FL_*` vêm do CAD aberto; `SPINDLE_PT` e `CONTACT_PATCH` (que o CAD não traz) vêm do CSV `hardpoints_T11_v20_1_cad.csv` com hipótese de camber e toe nulos. Diferença acima de 0,5 mm entre o CAD e o CSV vira aviso (vale o CAD).
- **Não é modelado:** manga, freio e pinça dentro do aro (restrição NÃO VERIFICÁVEL em todo candidato), pneu além do aro, coluna de direção, pedais, volume do atenuador, tirante com raio. Vários limites estão "a confirmar" (X do gabarito T.1.2, AIP, curso da cremalheira, margem do amortecedor): enquanto estiverem assim, o melhor veredito possível é **CONDICIONAL**, nunca VIÁVEL. Lista completa no relatório.
- Os raios dos envelopes (`r_mola_m` 25 mm, `r_prod_m` etc.) são valores da equipe, não medidos no CAD. O modo `"raios"` (veja abaixo) mede os raios reais no CAD para conferir.
- A busca é amostral: "nenhum candidato" em 2000 amostras **não prova** que não existe posição viável.
- Testado na cópia `T11_atuacao_v20_1_murilo_teste_nomes_corrigidos` (nesta máquina, Fusion 2706.1.17, Python 3.14.7). No original (`T11_atuacao_v20_1_murilo_teste`), o portão de identificação passa (0 falhas, avisos revisáveis sobre as rodas traseiras com nome de roda dianteira), mas o script completo ainda não foi rodado nele.

## Opções (`posicionador_config.json`, todas opcionais)
```json
{
  "modo": "posicionar",
  "documento_esperado": "T11_atuacao_v20_1_murilo_teste",
  "saida": "C:/caminho/da/pasta",
  "silencioso": false,
  "params": {"n_amostras": 2000, "n_refinos": 20, "semente": 0, "passo_m": 0.01, "corte_m": 0.05,
             "caixa_m": [[-0.15, 0.0, 0.065], [0.15, 0.326, 1.27]]}
}
```
`modo`: `posicionar` (padrão), `raios` (mede os raios das faces cilíndricas da atuação do CAD, só leitura) ou `medicao` (tempos da API). `semente` mexe no sorteio: outra semente, outro conjunto de amostras. `caixa_m` (m, referencial do carro) restringe onde o pivô é procurado; sem ela vale uma caixa derivada do envelope do chassi (hipótese, indicada no relatório).

## Se der erro
Aparece uma caixa com o erro e o detalhe fica em `status.json` na pasta de saída. Os mais comuns:
- "sem design ativo": abra o T11 em modo Design.
- "portão de identificação bloqueado": leia o código (LADO, CONTAGEM, REF, ...); é erro de nome ou de posição no CAD.
- "nao achei python/posicionador": a pasta foi copiada pela metade; copie `T11_posicionador` inteira.
Mande `status.json`, `progresso.log` e `relatorio.md` para o Vinícius.
