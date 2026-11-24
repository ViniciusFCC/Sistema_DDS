## Em linguagem simples: o posicionador é melhor que a v20?

**Resposta curta: no que mede e no quanto chega perto das metas, sim. Como solução pronta, nenhuma das duas serve ainda.**

### O que está sendo comparado

- A **v20** é uma posição de push rod, rocker e amortecedor, encontrada pelo **script de atuação** (`t11_atuacao.py`).
- O **posicionador** é outra ferramenta, que também procura essas posições.
- Para comparar com justiça, as duas foram **medidas pela mesma régua** (a avaliação do posicionador, que repete a medida até ela parar de mudar) e receberam **o mesmo número de tentativas**.

### Onde está a diferença: o tamanho da régua

O motion ratio (MR) é quanto a roda anda para cada milímetro do amortecedor, e a equipe quer que ele varie **no máximo 4 %** ao longo do curso.

Para saber quanto ele varia, é preciso medir em vários pontos do curso. O script de atuação mede em **11 pontos**. É como medir a inclinação de uma ladeira olhando só 11 pontos: entre eles a rampa pode subir e ele não vê.

| Resolução da medida | Variação de MR da v20 |
|---|---|
| Script de atuação, 11 pontos (onde ele otimiza) | **4,0 %** (parece cumprir) |
| Script de atuação, 25 pontos | 5,2 % |
| Script de atuação, 401 pontos | 6,1 % |
| Posicionador (já com 11 pontos) | **6,2 %** (não cumpre) |

Ou seja: a v20 passa na prova **com a régua curta** e reprova com a régua certa. E como o script **para de procurar quando a régua curta diz que está bom**, ele não percebe que ainda não chegou.

### O placar

| Pergunta | Script de atuação (v20) | Posicionador |
|---|---|---|
| A medida da variação de MR está certa? | Não: dá 4,0 % quando é 6,2 % | Sim: confere com 401 pontos |
| Quão longe das metas fica a solução final? | cerca de **55 %** fora do limite | cerca de **0,5 %** fora do limite |
| Quantas das buscas terminam a menos de 1 % das metas? | 0 de 13 | 4 de 6 |
| Existe solução que cumpre tudo? | Nenhuma | Nenhuma |
| Quanto tempo leva uma busca? | 128 a 196 s | 268 a 284 s (cerca de 1,7 vez mais) |

### O que cada uma "pede" e o que cada uma "ganha"

**O script de atuação pede** (e o posicionador não):
- um tubo de montagem encostado no Front Hoop (a menos de 8 mm do tubo existente);
- o push rod dentro do triângulo da bandeja superior;
- o gabarito do regulamento visto de frente, numa altura fixa.

**O posicionador pede** (e o script não):
- não bater em nenhuma peça do CAD do chassi;
- o gabarito com altura livre, a zona da AIP, o tirante e o esterçamento;
- que o resultado só valha depois de a medida convergir;
- dizer de onde vem cada limite e o que ficou sem verificar.

**O que o script de atuação ainda ganha:**
- a v20 foi pensada junto com o chassi (o tubo no Front Hoop);
- ele é mais rápido por busca.

**O que o posicionador ganha:**
- mede a variação de MR corretamente;
- chega perto das metas (o que sobra é o amortecedor 0,7 mm abaixo do mínimo, de 61 mm de curso);
- confere colisão com o CAD real, coisa que o script não faz;
- quando não acha solução, diz **quais metas brigam entre si**.

### O que isso quer dizer na prática

1. **O problema, com as metas atuais, não tem solução em nenhuma das duas ferramentas.** O conflito é entre "variação de MR de até 4 %" e "usar o curso inteiro de 61 mm do amortecedor". Nas melhores buscas do posicionador, ele vale cerca de **0,7 mm de curso**. Relaxar essa ordem de grandeza (hipótese, ainda não testada) pode tornar o problema viável. A decisão é da equipe.
2. **A v20 não cumpre a meta de variação de MR.** Isso aparece quando a medida usa mais pontos.

### Três cuidados para ler este resultado

- **Primeiro resultado com dados do T11, mas não validado.** Os dados são reais (geometria v10, v20 e o STEP do chassi). A cinemática das duas ferramentas ainda não foi comparada com o OptimumKinematics: elas concordam entre si (diferença de 1e-9 m), o que não prova que estão certas.
- **A comparação de busca foi feita sem o CAD** (só o aro). Com o CAD do chassi e 200 amostras, o posicionador também não encontrou posição viável. A vantagem de conferir colisão com o chassi está na tabela da seção 5, não nos gráficos da seção 2.
- **Poucas buscas** (7 do script de atuação, 6 de controle e 6 do posicionador): é um retrato, não uma estatística. O quanto da diferença vem da régua, do método de busca ou da região de partida está explicado na seção "O que o benchmark não prova".

