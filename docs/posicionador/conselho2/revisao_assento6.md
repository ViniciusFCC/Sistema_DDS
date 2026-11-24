# Revisão do assento 6 (lente: pragmática e gestão)

Li as 7 respostas anônimas e o BRIEF. Não rodei código novo: avaliei consistência interna e entre respostas.

## 1. Por letra
- **A**: pior fraqueza: o experimento é n = 1 semente, 150 amostras, máquina carregada; "triângulo" e "relaxar 1 mm não zera" contradizem G, D e E (bump −1 mm dá 3/6 ou 3/4 CONDICIONAL), então a conclusão sai de busca curta, não do conflito. Ponto forte: ordem de trabalho barata (mapa sem CAD antes do CAD) e perguntas objetivas à equipe.
- **B**: fraqueza: reavalia só 6 pontos (n = 11) e a "causa é quase-igualdade" não foi testada em busca completa (admite). Ponto forte: mostra no STEP que o CAD não é o gargalo (4 de 6 sem colisão) e que os pivôs estão a 179 a 281 mm de nó; MR(0) ±0,01 vem de `TOL_MR0`, não de meta.
- **C**: fraqueza: refinos partem das 6 finais (viés de região) e margens de 0,03 a 0,05 % (dezenas de µm). Ponto forte: melhor evidência rodada: 3 parametrizações (0/6, 2/6, 3/6), tabela de relaxamento com margem e 40 perturbações, e crítica da Fase I como "mapa de conflito".
- **D**: fraqueza: conclusões de forma da curva vêm de 4 partidas × 260 avaliações. Ponto forte: precisão: erro de n (1,1e-4), convergência que compara só estados, Lmax com folga 0,000 por construção, normalização por |limite| distorcendo o "100 vezes"; veredito "não encontrado".
- **E**: fraqueza: o construtor com δ é código dela, fora do repositório, e o candidato CONDICIONAL cai com ±0,5°. Ponto forte: acha de fato posição sem violação com o STEP (δ = −8°; Lmin 149,057 mm) com controle de mesmo orçamento (4/4 INVIAVEL), e explica fisicamente (tangência no estático, braço de 80 mm → giro 44,8°).
- **F**: fraqueza: não ataca MR × curso; o item 4 (hospedeiro) é inferência sem teste. Ponto forte: vão do CAD vazio (LCA_IN_F a 325 mm de tubo) e carga por kN sem inventar dado; R1/R2 são úteis ao certificado.
- **G**: fraqueza: a proposta de 62,4 → 58,0 mm de bump com 2 mm de margem inventa margem e redefine EYE/STROKE como "DADO_COMPONENTE" sem aval; é prescritiva demais. Ponto forte: rejulgamento rodado (62,4: 0/6; 61,4: 3/6; 60,4: 4/6) e separação REGRA/META/componente.

## 2. Ranking
RANKING: C > E > D > B > G > A > F

## 3. Divergências para o presidente
1. **Relaxar MR(0)**: B e C dizem que ±0,02 resolve (C: margem 0,23 %); E diz 1,405 dá 3/4 CONDICIONAL; D diz 1,41 recupera só 0,43 mm e não basta. Posição: depende de a busca refinar r2 depois; confiar em C/E (busca completa) e rodar a tolerância como pergunta à equipe, não ação.
2. **Bump −1 mm**: A diz que desloca a violação para r2/MR; G, D e C dizem 3/4 ou 3/6 CONDICIONAL com folga +0,03 mm. Posição: G/D/C (mais amostras); mas folga de 0,03 mm não é viável útil.
3. **Margem de fim de curso**: D e E dizem que ela torna tudo mais difícil e só se paga com bump/MR(0); G propõe 2 mm de margem com bump 58 mm. Posição: sem a margem real, nenhuma proposta fecha; é pergunta nº 1 à equipe.
4. **Parametrização**: E (liberar δ) × B/C (r2 livre ou pelo curso). Não são excludentes; decidir um experimento único com controle de mesmo orçamento e STEP, 6 sementes.
5. **Papel do CAD**: B/C dizem que não restringe; F diz que o vão vazio invalida "viável"; E vê metade dos candidatos colidindo. Posição: CAD não explica o vazio de MR, mas todo CONDICIONAL deve sair com o aviso "chassi hipotético".
