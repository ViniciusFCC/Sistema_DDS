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

## Como rodar a ferramenta (fase 1)

Na raiz do repositório (no Windows, `export UV_SYSTEM_CERTS=1` antes; a leitura do STEP precisa do extra opcional:
`uv sync --extra cad`):

```
uv run python -X utf8 tools/posicionar_atuacao.py --step data/cad/T11_chassi_2026-11-17.step --saida PASTA \
    [--amostras 2000] [--refinos 20] [--semente 0] [--caixa=xmin,ymin,zmin,xmax,ymax,zmax]
uv run python -X utf8 tools/posicionar_atuacao.py --avaliar-v20 --saida PASTA [--step ARQ.step]
```

- `--hardpoints` (padrão `data/posicionador/hardpoints_T11_v10.csv`, meta ao lado) e `--config` (padrão
  `data/posicionador/config_T11.json`) trocam as entradas; `--avaliar-v20` avalia `hardpoints_T11_v20_murilo.csv` como
  está, em vez de buscar.
- Sem `--step`, a cena tem só o aro (a folga ao chassi não é conferida) e a busca exige `--caixa`. Escreva
  `--caixa=xmin,...` com o sinal de igual: com `xmin` negativo, `--caixa -0.15,...` é lido como outra opção. A caixa
  precisa de mín < máx nos três eixos (senão, código 2).
- Referencial: com as esferas `REF_ORIGEM`, `REF_X` e `REF_Y` no STEP, elas mandam; sem nenhuma esfera `REF_` (caso do
  STEP atual), vale o item `transformacao_step_m` da configuração (HIPOTESE), o relatório diz isso e a folga aos fixos
  sai com origem HIPOTESE (a fonte cita `transformacao_step_m`).
- Esferas `HP_FL_<chave>` do STEP: comparadas com o CSV de hardpoints; acima de 0,5 mm (tolerância do documento de
  exportação) sai um aviso no relatório. A varredura usa sempre o CSV.
- Caixa de busca do pivô (HIPOTESE, "caixa derivada do envelope do chassi"): X do item `caixa_busca_pivo_m`; Y e Z nulos
  vêm da caixa envolvente de todos os obstáculos fixos do STEP, lado esquerdo: Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max].
  No STEP atual: X −150 a +150 mm, Y 0 a 325,7 mm, Z 60,1 a 1257,4 mm (contém o pivô da v20). `--caixa` sobrepõe.
- Resultado de 2026-11-23 (STEP atual, 200 amostras, semente 0, essa caixa): nenhum candidato viável; Fase I com a
  variação de MR violada em 99 % das amostras com resultado; o melhor (variação 4,09 %) viola ainda o comprimento mínimo do
  amortecedor e o braço r2. Amostragem curta: não prova que não existe posição viável.
- O progresso da busca vai para o stderr. Com o STEP atual, 200 amostras levam cerca de 11 min; o padrão (2000) é ~10 vezes
  mais.
- Código de saída 0 = saídas gravadas (qualquer veredito); 2 = entrada inválida (arquivo ausente, configuração sem
  procedência, item obrigatório nulo ou ausente, número não finito, caixa inválida, referencial inválido, primitivo não
  finito no STEP).

## Saídas (na PASTA)

- `relatorio.md`: veredito de cada candidato (VIAVEL, CONDICIONAL ou INVIAVEL; nunca "aprovado"), a tabela de restrições
  com valor, limite, folga, origem e fonte, distância ao nó mais próximo (preferência, não restrição), faixa de MR e do
  comprimento do amortecedor, os itens A_CONFIRMAR e HIPOTESE da configuração, os avisos do STEP, o que não está modelado,
  e os SHA-256 do STEP, da configuração e dos hardpoints de base (o resultado fica STALE se algum mudar). Sem candidato
  viável, a Fase I: pares de restrições que violam juntas, fração de cada restrição violada e o melhor candidato.
- `resultado.json`: o mesmo em dados (SI, unidade no nome do campo), com as curvas de MR e do amortecedor.
- `candidato_NN.csv` + `candidato_NN.meta.json`: um conjunto de hardpoints por candidato (schema V2.0, Status PROVISIONAL,
  sufixo no `geometry_rev`); carregam com `hardpoints.load_hardpoints`. `candidatos.csv`: tabela-resumo (um por linha).
  Sem candidato viável, esses arquivos não são gravados.
- `curvas.png` e `mapa_espaco_livre.png`: só se o matplotlib existir.

Todo resultado leva o rótulo "VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics (REFERENCE,
EDR-004)".

## Limites da fase 1 (leia antes de usar um candidato)

- **VIAVEL é inalcançável na fase 1.** A folga ao tirante é sempre parcial (o raio do tirante é A_CONFIRMAR: só o eixo é
  conferido), a folga à manga/freio/pinça dentro do aro é sempre NAO_VERIFICAVEL (sem `RODA_` modelado, o barril do aro
  trata o miolo como livre e o push rod nasce dentro dele) e há itens A_CONFIRMAR na configuração. O melhor veredito é
  CONDICIONAL, e ele não dispensa a conferência do que está listado em "O que não está modelado".
- **Falha fechada.** Primitivo do STEP ou número da configuração não finito (NaN, infinito) é recusado na leitura; folga
  não finita na avaliação vira INVIAVEL "avaliação sem resultado". Itens obrigatórios (`config.OBRIGATORIOS`: cursos,
  olho a olho, MR, braços, giro, ângulo, folgas, raios e aro) não podem ser nulos: a configuração é recusada com o nome do
  item.
- **Incerteza geométrica abaixo de 1 mm, sem margem.** A transformação STEP → carro da configuração foi ajustada só no
  lado reto do FH (erro ≤ 0,55 mm); os primitivos dos obstáculos podem deixar um furo de cobertura de até ~0,15 mm
  (tolerância de cobertura de 0,1 mm + deflexão da malha de 0,05 mm); a folga é o mínimo nos n estados do curso
  (discretização em dz, convergida em n e 2n, sem cota entre estados). A margem de fabricação δ é da fase 2
  (certificador).
- **Gabarito T.1.2 bloqueado pelo chassi sozinho:** a restrição sai NAO_VERIFICAVEL (a atuação não é a causa) e o relatório
  destaca, no topo, que o carro reprova o T.1.2 independentemente da atuação.
- **scipy no núcleo (decisão do controlador, revisão final):** a fase 1 usa `scipy.optimize.brentq` (r2 pelo MR-alvo, em
  `mecanismo.py`) e `scipy.optimize.minimize(method="Nelder-Mead")` (refino, em `busca.py`). A spec §7 pede núcleo sem
  scipy para rodar no Python do Fusion: a fase 3 tem de trocá-los por bisseção e Nelder-Mead em numpy.

## O que não está modelado (spec §4 não implementada na fase 1)

Vai em `nao_modelado` no `relatorio.md` e no `resultado.json` de toda execução (`varredura.NAO_MODELADO_FASE1`):
- manga, freio e pinça dentro do aro (restrição NAO_VERIFICAVEL em todo candidato);
- pneu (V.3.2.4): só o aro entra, como barril da configuração;
- V.3.2.4 além do aro: roda e pneu contra suspensão e chassi em todo o curso × esterço até os batentes;
- coluna de direção (só o X de início do gabarito T.1.2, `x_ini_t12_m`, sem o corpo da coluna);
- pedais e F.8.6.3 (folga ≥ 25 mm do conjunto de pedais);
- volume reservado do atenuador de impacto (F.8.4.2): só a face traseira da AIP (F.8.6.1) é conferida;
- sinalizações T.1.3.3 (exige escudo), V.3.1.3 (visibilidade) e F.5.3.1 (furo em tubo regulado → SES);
- faixa de ajuste de camber, toe e altura (spec §12 J2).
Com peças `RODA_`, `BANDEJA_` ou `DIR_` no STEP, sai também a restrição NAO_VERIFICAVEL "folga às peças móveis do STEP
(não modeladas na fase 1)".

## O que ainda é A_CONFIRMAR (desliga a verificação; veredito no máximo CONDICIONAL)

- `curso_cremalheira_m` (esterçamento);
- `margem_curso_amortecedor_m` (fim de curso do amortecedor; hoje 0, restrição parcial);
- `x_face_traseira_aip_m` (AIP, F.8.6.1);
- `x_ini_t12_m`, `x_fim_t12_m`, `z_min_t12_m`, `z_max_t12_m` (trecho e faixa vertical do gabarito T.1.2, T.1.2.2c).

Também em aberto (HIPOTESE): o aro de 13" (`aro_r_int_m`, `aro_meia_largura_m`) até o STEP trazer `RODA_`, a transformação
do STEP (`transformacao_step_m`) até o STEP trazer as esferas `REF_`. O raio do tirante não está na configuração: a folga
ao tirante confere só o eixo (restrição parcial).

## Testes

`tests/test_posicionador_{dados,geometria,cad,regulamento,mecanismo,varredura,busca,ferramenta}.py` (2, 5, 6, 5, 6, 10, 7
e 4 verificações; registrados em `tools/rodar_testes.py`; cerca de 18 min no total, 11 deles no TC-POS-081). O `cad` e o
TC-POS-081 do `ferramenta` precisam do OCP; sem ele saem NÃO EXECUTÁVEL (código 3), que nunca conta como PASS (o
`ferramenta` sai com 1 se algum dos outros falhou). A revisão final da fase 1 acrescentou a regressão da propriedade de
segurança: NaN nos fixos (TC-POS-065), colisão, gabarito e AIP SINTÉTICOS (066), busca com obstáculo na caixa (075),
itens obrigatórios (055), não modelado (068, 025) e referencial da configuração (069).
