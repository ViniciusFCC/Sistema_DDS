# Resposta: lente de otimização e síntese de mecanismos

Rótulos: [F] fato de fonte (relatório citado); [C] resultado de código (scripts e saídas em `conselho/assento3_trabalho/`); [K] cálculo; [I] inferência; [H] hipótese.

## Q1. O método atual é adequado?

Não. O que falha é a formulação; o Nelder-Mead é só o sintoma.

- [C] Amostrei 3000 pontos por hipercubo latino na caixa que sai dos limites do próprio script (`lhs.py`, modo A; `lhs_A.json`). Cada quase-igualdade sozinha passa em poucas amostras: MR ±0,01 em 0,87 %, Ls estendido ±1 mm em 9,3 % e erro ao FH ≤ 8 mm em 3,6 %. As quatro juntas, contando o curso, passam em 0 de 3000. As demais restrições duras, juntas, passam em 116 (3,9 %). [K] Com o produto das taxas, a chance de uma amostra ser viável fica em torno de 1e-6. Isso basta para explicar 1,1 milhão de combinações sem nenhuma solução. Não é preciso supor azar.
- [K] Uma igualdade já vem embutida nos dados: 23 + 62,4 = 85,4 mm = 61 × 1,40. O curso da roda foi definido como curso do amortecedor × MR, então o amortecedor é usado inteiro, sem margem.
- [F] O REGISTRO (achados 1 e 2) mostra restrições paradas exatamente no limite e o MR em 5,2 % na malha de 25 pontos, quando a de 11 mostra 4,0 %. É o que N&W p. 490 prevê para penalidade quadrática com peso fixo (RELATORIO_LIT). [I] Há também um erro de discretização: restrição que vale "em todo o curso" foi conferida só em 11 pontos.
- [C] Pela regra de "ponto perto de nó", a impossibilidade pode ser provada sem busca (`limites_nos.py`). O script exige |Pv_x| ≤ 150, olhal com C_x ≤ 400, |C − Pv| ≤ 80 + 210 e amortecedor a no máximo 30° de X. Com tolerância de até 50 mm ao nó, nenhum par de nós existentes (N03, N04, N09 a N12) passa nem nessas condições necessárias. A que impede é |Pv_x| ≤ 150, porque os nós do FH estão em X = −202. O conjunto viável "pivô e olhal em nós de hoje" é vazio. Os relatos (a) do Murilo são consequência disso, não falha de busca.

## Q2. Método e arquitetura recomendados

**Variáveis**

- Discretas: ARM; LADO_ROCKER; âncora do pivô e âncora do olhal. Cada âncora é um nó existente, um ponto (tubo, s ∈ [0,1]) num tubo existente ou um nó proposto com custo.
- Contínuas: só o que sobra, ou seja, s, a orientação do plano, r1, φB e a direção do amortecedor.

**Igualdades resolvidas por construção**

- r2 sai do MR(0) = 1,40 em uma dimensão, pois o giro θ(dz) não depende de r2.
- O olhal C sai de Ls(droop) = EYE, em forma fechada.
- O pivô sai da âncora mais o offset da orelha, o que acaba com o "erro ao FH".
- O curso de bump vira saída, com a restrição "curso ≥ mínimo da equipe".
- [C] Testei as duas primeiras construções (modo B, 1000 amostras, `lhs_B.json`). As quatro quase-igualdades juntas passaram de 0/3000 para 16/1000. MR e Ls passaram a valer em cerca de 90 % das amostras válidas.
- [C] O custo da construção aparece em dois lugares. Os braços dentro de 55 a 80 mm passam a valer só em 24,5 %, o que é certo: virou desigualdade honesta. E 20,7 % das amostras falham na cinemática ou na raiz de r2, o que precisa virar restrição, não 1e6.
- [C] O erro ao FH continua em 2,9 %, porque não o eliminei. A construção por âncora é a próxima a fazer.

**Restrições e objetivos**

- Duras, escritas como g_i(x) ≤ 0 normalizadas e varridas em curso × esterço: folgas por cápsulas, gabarito (com a trajetória livre em z, item D5 do RELATORIO_REGRAS), braços, giro, curso, ângulo de transmissão mínimo, F.8.6.1 e limite de tensão no tubo receptor.
- Objetivos: variação do MR, ângulo push rod–plano ao longo do curso (achado 3), flexão no tubo, massa e número de tubos novos, e margens.

**Algoritmo**

- Estágio 0: pré-filtro por limites (desigualdades necessárias, como acima) em cada combinação discreta. Corta o espaço e prova que é vazio quando for.
- Estágio 1, Fase I: minimizar a violação máxima com folgas elásticas. Usar multi-start por LHS e solver local (SLSQP se as cápsulas deixarem a avaliação suave), ou evolução diferencial com as regras de Deb se não deixarem.
- Estágio 2: multiobjetivo só entre os viáveis, com ε-restrição ou NSGA-II.
- Estágio 3: certificador independente, determinístico, numa malha pelo menos 4 vezes mais fina que a da busca, com margem e geometria exata (OCC) nos finalistas.

[I] Só o estágio 3 aprova. A busca pode ser heurística, mas a garantia de que tudo o que sai aprovado é válido tem de vir do verificador, não do otimizador.

**Saída**

- Uma frente de Pareto certificada.
- Para cada combinação sem solução: a menor relaxação necessária e as restrições em conflito, pela coocorrência e pelas folgas elásticas.

**Como provar que o conjunto é vazio**

- Os estágios 0 e 1 dão só evidência.
- [I] Depois das eliminações sobram de 4 a 5 variáveis contínuas por combinação. Isso torna viável um branch-and-bound com limites intervalares ou de Lipschitz para provar o vazio de fato.

## Q3. Uso de tubos e nós do CAD

- [F] Use `step_tubos.py`, que extrai eixo, raio e nós com o critério de 1/sen θ (RELATORIO_GEO).
- No laço, tubo é cápsula. Nó é âncora candidata. Cada rodada registra o hash do STEP.
- [F] A caixa dianteira não existe no CAD: nada a menos de 97 mm de Pv nem de C (GEO §6a). Por isso o script tem de admitir nós propostos, com custo, e reservar volumes como "cápsulas fantasma" para os tubos previstos (RELATORIO_PRATICA, risco 3).
- [I] O que hoje sai aprovado contra um chassi incompleto é "viável condicional a esta versão", e tem de ser re-certificado a cada STEP novo.

## Q4. Coordenação chassi × suspensão

[I] Formulação em dois níveis (RELATORIO_LIT §5):

- A suspensão define as metas (MR, curso, faixas) e roda o script sobre cada STEP.
- O resultado vai para o chassi como lista ranqueada de nós propostos, cada um com o tubo de triangulação que exige.
- O chassi decide quais nós criar e devolve o STEP.

As relaxações são decisão humana registrada, não do script: MR ±4 %, |Pv_x| ≤ 150, 30°, faixa dos braços. [F] São escolhas da equipe, não da literatura (LIT §1).

## Q5. Riscos e o que validar primeiro

**Riscos**

- (a) [F] Eliminar variáveis pode mal-condicionar o problema (N&W p. 425).
- (b) [F] A região viável pode ser disjunta. Por isso a enumeração e o multi-start são obrigatórios (Coello p. 1267).
- (c) [F] O `kinlib` não foi validado contra o OptimumKinematics (EDR-004; GEO §7). Se o modelo estiver errado, o certificador certifica o modelo errado.
- (d) [C] As falhas cinemáticas (20,7 % no modo B) precisam ter uma medida de distância ao viável.

**Testes que derrubariam a recomendação**

1. Rodar o estágio 2 com 11 pontos e certificar na malha fina. Se a maioria dos candidatos for reprovada, tratar o curso como restrição semi-infinita na própria busca (máximo por refinamento) antes de qualquer outra coisa.
2. Construir a âncora para o FH. Se a taxa conjunta não subir de forma clara em relação ao modo B, a tese de que o gargalo são as quase-igualdades cai.

## Recomendação em uma frase

Reformular antes de trocar o algoritmo:

- resolver as quase-igualdades por construção (r2 pelo MR, C pelo Ls, pivô pela âncora);
- tratar a escolha de nós e tubos, existentes ou propostos, como variável discreta enumerada com pré-filtro por limites;
- buscar viabilidade primeiro (Fase I com multi-start), depois a frente de Pareto;
- aprovar só o que um certificador independente, em malha fina e geometria exata, confirmar.

## Confiança e principal incerteza

**Média-alta.** Os números da Q1 e o ganho do modo B são medidos. Já se o conjunto viável com nós novos é não vazio é desconhecido: depende de tubos que ainda não existem e das relaxações que a equipe aceitar. A validade do `kinlib`, que vira a base do certificador, também não foi verificada.
