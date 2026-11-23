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
    [--amostras 2000] [--refinos 20] [--semente 0] [--caixa xmin,ymin,zmin,xmax,ymax,zmax]
uv run python -X utf8 tools/posicionar_atuacao.py --avaliar-v20 --saida PASTA [--step ARQ.step]
```

- `--hardpoints` (padrão `data/posicionador/hardpoints_T11_v10.csv`, meta ao lado) e `--config` (padrão
  `data/posicionador/config_T11.json`) trocam as entradas; `--avaliar-v20` avalia `hardpoints_T11_v20_murilo.csv` como
  está, em vez de buscar.
- Sem `--step`, a cena tem só o aro (a folga ao chassi não é conferida) e a busca exige `--caixa`.
- Referencial: com as esferas `REF_ORIGEM`, `REF_X` e `REF_Y` no STEP, elas mandam; sem nenhuma esfera `REF_` (caso do
  STEP atual), vale o item `transformacao_step_m` da configuração (HIPOTESE), e o relatório diz isso.
- Caixa de busca do pivô (HIPOTESE, "caixa derivada do envelope do chassi"): X do item `caixa_busca_pivo_m`; Y e Z nulos
  vêm da caixa envolvente de todos os obstáculos fixos do STEP, lado esquerdo: Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max].
  No STEP atual: X −150 a +150 mm, Y 0 a 325,7 mm, Z 60,1 a 1257,4 mm (contém o pivô da v20). `--caixa` sobrepõe.
- Resultado de 2026-11-23 (STEP atual, 200 amostras, semente 0, essa caixa): nenhum candidato viável; Fase I com a
  variação de MR violada em 99 % das amostras com resultado; o melhor (variação 4,09 %) viola ainda o comprimento mínimo do
  amortecedor e o braço r2. Amostragem curta: não prova que não existe posição viável.
- O progresso da busca vai para o stderr. Com o STEP atual, 200 amostras levam cerca de 11 min; o padrão (2000) é ~10 vezes
  mais.
- Código de saída 0 = saídas gravadas (qualquer veredito); 2 = entrada inválida.

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

## O que ainda é A_CONFIRMAR (desliga a verificação; veredito no máximo CONDICIONAL)

- `curso_cremalheira_m` (esterçamento);
- `margem_curso_amortecedor_m` (fim de curso do amortecedor; hoje 0, restrição parcial);
- `x_face_traseira_aip_m` (AIP, F.8.6.1);
- `x_ini_t12_m`, `x_fim_t12_m`, `z_min_t12_m`, `z_max_t12_m` (trecho e faixa vertical do gabarito T.1.2, T.1.2.2c).

Também em aberto (HIPOTESE): o aro de 13" (`aro_r_int_m`, `aro_meia_largura_m`) até o STEP trazer `RODA_`, a transformação
do STEP (`transformacao_step_m`) até o STEP trazer as esferas `REF_`. O raio do tirante não está na configuração: a folga
ao tirante confere só o eixo (restrição parcial).

## Testes

`tests/test_posicionador_{dados,geometria,cad,regulamento,mecanismo,varredura,busca,ferramenta}.py` (2, 5, 5, 5, 5, 5, 5
e 2 verificações; registrados em `tools/rodar_testes.py`). O `cad` e o TC-POS-081 do `ferramenta` precisam do OCP; sem
ele saem NÃO EXECUTÁVEL (código 3), que nunca conta como PASS.
