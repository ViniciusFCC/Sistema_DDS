# Posicionador da atuação dianteira: metodologia e implementação

Equipe Tupã (FSAE Elétrico, EESC-USP) · EDR-076, fase 1 · Validation = NOT_VALIDATED

## 1. O que é, em uma página

O **posicionador** responde a uma pergunta: *onde o push rod, o rocker e o amortecedor da dianteira podem ficar sem bater em nenhuma peça do carro e sem violar o regulamento, cumprindo as metas da equipe?*

- **Entra:** o CAD do chassi (arquivo `.step`), os pontos fixos da suspensão (v10) e a configuração com as metas e os limites.
- **Sai:** uma lista de posições candidatas (cada uma com seus pontos em CSV) ou, se nenhuma serve, um diagnóstico dizendo **quais restrições brigam entre si**.
- **Não faz:** não desenha nem dimensiona tubos; não calcula tensão no chassi; não substitui o OptimumKinematics. Nunca "aprova": o melhor veredito é `CONDICIONAL`.

Os pontos que ele posiciona são seis: `PUSH_OUT` (push rod na bandeja inferior), `PUSH_IN` (push rod no rocker), `ROCKER_AXIS_A/B` (eixo do rocker), `ROCKER_SPRING` (amortecedor no rocker) e `SPRING_CHASSIS` (amortecedor no chassi). Bandejas, tirante e roda ficam fixos.

## 2. Conceitos de base

- **Motion ratio (MR).** Quanto a roda anda para cada milímetro que o amortecedor anda: `MR = Δ(curso da roda) / Δ(comprimento do amortecedor)`. Meta da equipe: 1,40 ± 0,01 na posição estática.
- **Variação de MR.** `máx(MR) / mín(MR) − 1` ao longo do curso da roda (−23 mm a +62,4 mm). Limite: 4 %. Um MR que varia pouco dá uma suspensão previsível.
- **Curso do amortecedor.** O amortecedor tem 210 mm estendido e 61 mm de curso: o comprimento fica entre 149 e 210 mm. Usar o curso inteiro sem margem deixa a suspensão sem folga antes do batente.
- **Folga.** Distância entre duas peças, descontando a espessura de cada uma. Positiva = não toca. O programa trata cada peça como um cilindro de ponta arredondada (cápsula) ou uma caixa, e calcula a distância com sinal até o obstáculo mais próximo.
- **Resolução convergida.** O curso da roda é amostrado em *n* pontos. Se o resultado muda ao dobrar *n*, a amostragem era grossa. O programa repete a avaliação com *n* e *2n* (25, 50, 100, 200 pontos) até o veredito parar de mudar.

## 3. O pipeline, passo a passo

```
STEP ──► referencial ──► obstáculos ──► espaço livre ─┐
                                                      ├─► busca ─► candidatos ─► relatório
hardpoints v10 + configuração ──► mecanismo ──► varredura ─┘
```

1. **Leitura do STEP** (`cad_step.py`). O OpenCascade lê a montagem. Cada componente de primeiro nível é classificado pelo prefixo do nome (`CHASSI_`, `FIXO_`, `RODA_FE_`, `BANDEJA_FE_`, `DIR_`, `REF_`, `HP_`, `IGNORAR_`); sem prefixo vale `FIXO_`, com aviso. Tubos redondos viram cápsulas, tubos quadrados viram caixas exatas, demais sólidos viram caixas orientadas, sempre conservadoras (nunca menores que o corpo real). Os nós do chassi são achados onde eixos de tubo se encontram.
2. **Referencial.** As esferas `REF_ORIGEM`, `REF_X` e `REF_Y` (Ø 5 mm) definem a origem e os eixos do carro (X para frente, Y para a esquerda, Z para cima). Sem elas, vale a transformação da configuração, rotulada `HIPOTESE`.
3. **Mapa de espaço livre** (`espaco_livre.py`). Grade de pontos na caixa de busca do pivô; cada ponto guarda a folga ao obstáculo mais próximo e a distância ao nó mais próximo.
4. **Mecanismo por construção** (`mecanismo.py`). Dadas 7 variáveis (pivô X, Y, Z; direção do amortecedor; braço r1; ângulo entre os braços), o programa **calcula** o resto em vez de procurar:
   - o plano do rocker contém a junta da bandeja, o pivô e o amortecedor;
   - o push rod sai da bandeja numa reta que passa pela junta, a 35 mm dela, perpendicular ao braço r1 na posição estática;
   - o braço r2 do lado do amortecedor sai de uma equação de uma incógnita: `MR(0) = 1,40` (método de bisseção sobre `kinematics_model.motion_ratio`);
   - o olhal do amortecedor no chassi (C) fica na reta do amortecedor, onde `|B(−23 mm) − C| = 210 mm`.

   Com `--delta-max` > 0 (padrão 25°), o ponto do push rod no rocker pode girar δ em volta do eixo a partir da tangência (8ª variável da busca); com 0, a construção é a do script de atuação. Assim, as metas que antes eram "quase igualdades" (e quase nunca se cumpriam por sorteio) passam a valer por construção.
5. **Varredura** (`varredura.py`). Para cada ponto do curso da roda (e do esterçamento, se o curso da cremalheira for informado), a cinemática do repositório (`kinematics_model.Corner`) resolve a posição de todas as peças. Em cada estado, o programa confere as restrições (tabela abaixo).
6. **Busca** (`busca.py`).
   - **Amostragem:** sorteia pivôs no espaço livre, com mais peso perto de nós (preferência, nunca exigência), e as demais variáveis por hipercubo latino. Com a **caixa dinâmica** (padrão), a amostragem tem três rodadas (50 %, 30 % e 20 % das amostras): da segunda em diante, 80 % das amostras caem numa caixa em volta dos 10 % melhores (alargada em 25 %, no mínimo 20 mm) e 20 % na caixa inteira.
   - **Refino:** as melhores amostras são refinadas por Nelder-Mead. Sem violação, o objetivo passa a ser **maximizar a margem** (menor folga normalizada entre as restrições, sem as fixadas pela construção: MR(0) e comprimento máximo); a margem é objetivo, nunca exigência.
   - **Convergência:** só vira candidato quem continua VIAVEL ou CONDICIONAL na avaliação com resolução convergida. A convergência é também **por valor**: enquanto uma folga positiva for menor que a diferença entre n e 2n pontos, o programa dobra n (até 8 vezes o inicial); o que sobrar vai em `indeterminadas` (folga não certificada), sem tolerância nova.
   - **Fase I (diagnóstico):** se não há candidato, devolve o de menor violação e os pares de restrições que mais vezes violam juntos.
7. **Relatório** (`relatorio.py`). Veredito, cada restrição com valor, limite, folga e **origem do limite**, itens a confirmar, avisos do STEP, hash do STEP e da configuração.

## 4. O que é conferido (e de onde vem cada limite)

| Restrição | Limite | Origem |
|---|---|---|
| MR na posição estática | 1,40 ± 0,01 | META |
| Variação de MR no curso | ≤ 4 % | META |
| Comprimento do amortecedor | 149 a 210 mm (+ margem de curso) | META (margem: a confirmar) |
| Braços do rocker | 55 a 80 mm | META |
| Giro do rocker | ≤ 60° | META |
| Ângulo do amortecedor ao eixo X | ≤ 30° | META |
| X do olhal no chassi | ≤ 400 mm | META |
| Folga ao aro (push rod, rocker, amortecedor) | ≥ 10 mm | MARGEM_EQUIPE |
| Folga às quatro pernas das bandejas | ≥ 5 mm | MARGEM_EQUIPE |
| Folga push rod × amortecedor | ≥ 5 mm | MARGEM_EQUIPE |
| Folga ao tirante de direção | ≥ 0 (raio do tirante a confirmar) | A_CONFIRMAR |
| Folga a todo obstáculo fixo do STEP | ≥ 0 | spec: "sem colidir" |
| Gabarito T.1.2 (altura livre, T.1.2.2c) | existe trajetória sem interferência | REGRA (FSAE Rules 2027 V1.0) |
| Zona da AIP (F.8.6.1) | nada de suspensão à frente da AIP | REGRA |
| Esterçamento (V.3.2.4) | sem toque até os batentes | REGRA (curso: a confirmar) |

**Origens:** `REGRA` (regulamento, com artigo e versão), `META` (decisão da equipe), `MARGEM_EQUIPE` (folga de projeto, não é regra), `HIPOTESE` (suposição declarada), `A_CONFIRMAR` (sem valor: a verificação **liga o aviso e desliga o veredito VIAVEL**).

## 5. O veredito

- `INVIAVEL`: alguma restrição foi violada.
- `CONDICIONAL`: nenhuma violada, mas algo não pôde ser verificado (`NAO_VERIFICAVEL`) ou usa valor provisório (`A_CONFIRMAR`). É o melhor resultado possível nesta fase.
- `VIAVEL`: reservado para quando nada ficar a confirmar. Hoje inalcançável de propósito.

Falhas de cálculo (cinemática sem solução, geometria que não fecha, valor não finito) **sempre** resultam em `INVIAVEL` com o motivo: o programa falha para o lado seguro.

**Violação normalizada** (usada para ordenar e refinar): `máx( max(0, −folga) / |limite| )` sobre as restrições violadas; para limites nulos, a escala é 1 mm.

## 6. Estrutura do código

| Arquivo | Função |
|---|---|
| `python/posicionador/geometria.py` | cápsula, caixa, barril (aro), esfera; distância com sinal; folga de um segmento |
| `python/posicionador/cad_step.py` | leitura do STEP, prefixos, tubos, nós, referencial, obstáculos |
| `python/posicionador/regulamento.py` | gabarito T.1.2 com altura livre; limite da AIP |
| `python/posicionador/config.py` | configuração com origem e fonte de cada limite |
| `python/posicionador/mecanismo.py` | construção do push rod, rocker e amortecedor |
| `python/posicionador/varredura.py` | avaliação de um candidato, restrições, veredito, convergência |
| `python/posicionador/espaco_livre.py`, `busca.py` | mapa de espaço livre; busca e diagnóstico |
| `python/posicionador/relatorio.py` | relatório, JSON e CSV de saída |
| `tools/posicionar_atuacao.py`, `tools/posicionador_exe.py` | linha de comando e executável |

A cinemática vem do módulo `kinematics_model` do repositório (comparada com o script de atuação em 401 pontos: diferença máxima de 1e-9 m no comprimento do amortecedor).

## 7. Como usar o executável

- **Dois cliques:** abre um menu (avaliar a v20; buscar num STEP; buscar no STEP de exemplo).
- **Arrastar um `.step`** em cima do `.exe`: busca direta.
- **Linha de comando:** `posicionador_T11.exe --help` lista as opções (`--avaliar-v20`, `--step`, `--amostras`, `--semente`, `--caixa`, `--config`…).

Cada execução cria `resultados\AAAAMMDD_HHMMSS_<modo>\` ao lado do `.exe`, com `relatorio.md`, `resultado.json` e, havendo candidato, `candidato_NN.csv`. A busca com STEP padrão leva cerca de 11 minutos (200 amostras); a avaliação da v20 leva segundos. O executável se descompacta numa pasta temporária a cada execução, o que leva alguns segundos antes de começar.

Para o STEP ser lido do jeito certo, os componentes precisam de prefixo e o modelo deve ter as esferas de referência (documento "Exportação do CAD (.step) para o posicionador da atuação").

## 8. Limites desta fase (o que ele ainda não sabe)

- **Cinemática não validada** contra o OptimumKinematics (REFERENCE). VERIFIED não é validado.
- **Não modelados:** manga, freio e pinça dentro do aro; pneu; coluna de direção; pedais (F.8.6.3); volume do atenuador (F.8.4.2); batentes além do aro; sinalizações T.1.3.3, V.3.1.3 e F.5.3.1. Aparecem como `NAO_VERIFICAVEL`.
- **Itens a confirmar:** curso da cremalheira, margem de curso do amortecedor, face da AIP, início e fim do gabarito (coluna e pedais) e sua faixa vertical.
- **Incerteza abaixo de 1 mm** (transformação do STEP, cobertura da malha, discretização do curso); a margem de fabricação δ é de uma fase posterior.
- **Busca por amostragem:** "nenhum candidato" não prova que não existe posição viável.
- **Margem de micrômetros:** com as metas atuais o curso do amortecedor não tem folga por construção (bump = 61 × 1,40 − 23), e a maior margem achada é da ordem de 0,03 a 0,07 mm. Um candidato assim é CONDICIONAL e frágil, não é solução; a margem de fim de curso é decisão da equipe.
- **Fixação:** a distância ao nó do chassi é só preferência; os pivôs achados podem ficar longe de qualquer tubo existente.
- **Aro** de 13" (raio interno 158 mm, largura 200 mm) é hipótese até o STEP trazer as peças da roda.
