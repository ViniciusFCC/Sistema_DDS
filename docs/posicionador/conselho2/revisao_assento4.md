# Revisão anônima (assento 4)

Li só `anon/resposta_A.md` a `G.md` e o BRIEF. Não rodei código novo: os números abaixo são os que cada texto declara, cruzados entre si.

## 1. Erro ou fraqueza mais grave, e ponto mais forte

- **A.** Fraqueza: o único experimento tem 1 semente por variante, 150 amostras e máquina carregada. Mesmo assim A conclui "triângulo" e diz que isso contradiz o "só falta 1 mm". Mas o bump de −1 mm só é medido em busca curta, e C e G medem o mesmo corte com resultado oposto (3/6 CONDICIONAL). Força: a prioridade de validar o MR contra o OptimumKinematics e o mapa de Pareto sem CAD antes do CAD.
- **B.** Fraqueza: as reavaliações usam n = 11, sem `avaliar_convergido`, e a nova parametrização não foi buscada de verdade. Só se varreu r2 em 3 candidatos. Força: reavaliou as 6 finais no STEP real e mostrou que 4 passam em todas as folgas ao CAD, o que isola (c). Também achou a quase-igualdade (MR(0) pinado, `TOL_MR0` sem origem) e os pivôs a 179 a 281 mm de qualquer nó.
- **C.** Fraqueza: o refino parte das 6 finais do benchmark (viés de região, admitido), e as margens achadas são de 0,03 a 0,05 %. Força: a única resposta que compara três parametrizações com controle de mesmo orçamento (0/6, 2/6 e 3/6) e entrega uma tabela de relaxamentos com margem e robustez. Também diz que a Fase I não mede conflito.
- **D.** Fraqueza: o diagnóstico "triângulo com r2" vem de reescalar o objetivo, que muda o resultado de um refino local, e a 8ª variável não foi testada. Força: achou que `avaliar_convergido` compara só estados e não valores, e que a métrica normalizada por |limite| distorce o "100 vezes mais perto". Também mediu a identidade ∫dz/MR a 1e-3 mm.
- **E.** Fraqueza: o construtor com δ está fora do repositório, a busca é local e a folga do CONDICIONAL é de 0,057 mm, que o próprio E admite ser lasca. Força: único a liberar um grau de liberdade que a construção fixa (tangência no estático) e a obter CONDICIONAL também com o STEP. Dá custos em unidades físicas (0,44 mm por 0,01 de MR(0); 0,12 a 0,18 mm por ponto percentual de variação).
- **F.** Fraqueza: trata a estrutura, não o gargalo de viabilidade. A hipótese 4 (hospedeiro) fica sem teste e "tubos-fantasma" são topologia inventada. Força: números de distância a tubo e de carga por kN, reprodutíveis, sem inventar cargas, e a regra do hospedeiro.
- **G.** Fraqueza: recomenda 58,0 mm de bump (−4,4 mm) com 2 mm de margem de fim de curso, valores que são cenário e não dado. Reclassifica EYE e STROKE como `DADO_COMPONENTE` sem catálogo. Diz que a hipótese do BRIEF "se confirma" quando as folgas são de +0,03 mm. Força: tabela de bump por margem (0/6, 3/6, 4/6) e o desenho de tornar o bump uma saída, com V.3.1.1 como regra.

## 2. Ranking

RANKING: C > E > B > D > G > A > F

## 3. Divergências para o presidente decidir

1. **MR(0) como folga.** B e C dizem que liberar MR(0) basta (B: r2 sozinho com Lmin = 149,05 e MR(0) = 1,417). D diz que 1,41 recupera só 0,43 mm e não basta. E diz que 1,405 dá 3/4 CONDICIONAL. Os números não fecham, porque cada um refinou diferente. Posição: reproduzir uma vez, com o mesmo juiz convergido, MR(0) ∈ {1,405; 1,41; 1,42}. Enquanto isso, a tolerância ±0,01 é constante sem origem e deve ir para a configuração.
2. **Bump −1 mm.** C, D e G medem 3/6 ou 3/4 CONDICIONAL com folga de +0,03 mm. A mede MR e r2 ainda violados. Posição: vale C, D e G (juiz convergido, mais amostras). A divergência vem do orçamento curto de A. Folga de 0,03 mm não é viabilidade.
3. **Causa do vazio: parametrização ou conflito de metas.** B, C e E apontam (b), com conflito pequeno. D e G apontam (a). Posição: as duas, porque 85,4 = 61 × 1,40 deixa margem zero. A parametrização decide se há solução, e a margem de fim de curso (A_CONFIRMAR, hoje 0) decide se ela sobrevive.
4. **CAD como gargalo.** B diz que o CAD não impede nada nas 4 melhores. E diz que o CAD derruba metade dos candidatos com δ livre. G e A não testaram. Posição: nos candidatos atuais o CAD não aperta, mas isso não vale para soluções novas. Rodar o STEP com a nova parametrização.
5. **Relaxar o quê primeiro.** G propõe bump (META). C propõe a tolerância de MR(0). E propõe δ (que não relaxa meta) e depois a margem de curso. Posição: ordem E, depois MR(0), depois margem de curso e bump. Nenhuma meta muda sem a equipe.
