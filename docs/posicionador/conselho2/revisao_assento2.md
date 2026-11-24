# Revisão anônima (lente: estrutura do chassi)

Base: li só `anon/resposta_A.md` a `G.md` e o BRIEF. Conferi de cabeça a aritmética comum (23 + 62,4 = 85,4 = 61 × 1,40). Não rodei código novo.

## 1. Por letra

- **A.** Pior: o "triângulo" sai de n = 1 por variante, com 150 amostras e máquina carregada. Ele contradiz C, B e E, que acharam candidatos sem violação, e a própria A admite que não prova nada. Melhor: a ordem de trabalho (mapa sem CAD antes do CAD) e o teste mínimo de 3 sementes.
- **B.** Pior: as reavaliações usam n = 11 e só 6 candidatos, e a "caixa estreita Z 300–600" é sugestão sem teste. Melhor: acha a quase-igualdade escondida (MR(0) fixo + olhal em 210 mm). Com r2 variado e MR(0) livre, Lmin = 149,05 mm e a única violação vira MR(0) em 1,417–1,4185. Reavalia no STEP (4 de 6 sem colisão). Mostra os pivôs a 179–281 mm de qualquer nó.
- **C.** Pior: partiu das 6 finais (viés de região) e as margens são de 0,03–0,05 %, o que ele mesmo reconhece. Melhor: compara 3 parametrizações com o mesmo orçamento (0/6, 2/6, 3/6 CONDICIONAL). Tem tabela de custo por relaxamento, e o desenho em duas fases (viabilidade e depois centro de Chebyshev) é o mais completo.
- **D.** Pior: o experimento de escala em mm leva r2 a 86–90 mm, e a conclusão de que o conflito é um triângulo tem só 4 partidas. Melhor: critica que `avaliar_convergido` compara estados e não valores. Mostra que C é satisfeito por construção com folga 0,000 mm. Aponta que a violação normalizada por |limite| depende da escala.
- **E.** Pior: o construtor com δ é código próprio, fora do repositório, e o candidato CONDICIONAL cai com ±0,5°. Melhor: acha o grau de liberdade escondido (tangência γ1 = 0 no estático). Um candidato sai CONDICIONAL também com o STEP (δ = −8°, Lmin 149,057 mm). Dá custo por 0,01 de MR(0) = 0,44 mm.
- **F.** Esta é a mais estreita: ataca a validade estrutural e não o vazio de MR × curso, e as arestas-fantasma são hipótese de topologia, o que ela declara. A afirmação de que o pivô "no nó" colide com o hospedeiro (item 4) é inferência sem teste. Melhor: medi o vão vazio entre FH e FBH (nós só nos dois hoops). Distâncias da v20 aos tubos: 325 e 299 mm nos pontos de bandeja, 147–155 mm nos eixos do rocker. Cargas em forma fechada, por kN, sem inventar dado.
- **G.** Pior: a recomendação (bump 62,4 → 58,0 mm) relaxa uma META para comprar margem que ninguém exigiu. O rejulgamento não refaz a geometria, já que r2 fica fixo. A afirmação "a hipótese se confirma" ignora que 2 das 6 ainda violam r2. Melhor: tabela de bump × resultado (62,4: 0/6; 61,4: 3/6; 60,4: 4/6). Separa DADO_COMPONENTE de META e levanta V.3.1.1.

## 2. Ranking

RANKING: C > B > E > D > G > F > A

(C e B cobrem as duas frentes, parametrização e CAD, com evidência comparada. E tem o achado mais original, mas sem validação no código do repositório. G dá o mapa de relaxamento mais claro, mas propõe mudar meta. F é correta e honesta, mas pouco serve ao objetivo central.)

## 3. Divergências para o presidente

1. **Causa do vazio.** B, C e E apontam a parametrização (MR(0) fixo e tangência no estático). G e A apontam o curso e o bump. D diz "forma da curva + bump circular". Minha posição: a parametrização é a causa primária, pois C mostra 0/6 contra 2–3/6 com o mesmo orçamento. O bump é o conflito de metas que sobra. Decisivo é um LHS amplo com r2 livre e MR(0) com tolerância.
2. **"Nenhum relaxamento isolado zera".** A diz que nenhum zerou. C diz que nenhum dá robustez, e B/E/G acham candidatos sem violação. Todos concordam em "viável na borda, com margem de dezenas de µm". Minha posição: o veredito deve ser "não encontrado com margem", e a margem mínima δ deve ser um requisito da certificação.
3. **A restrição MR(0) ± 0,01** (B, C, D, E). `TOL_MR0` é constante do código sem origem. Minha posição: ela vai para `config_T11.json` com origem rotulada antes de qualquer decisão da equipe.
4. **O chassi.** C, B, E, G concluem que o CAD não aperta. B e F mostram que os pivôs estão longe de qualquer nó ou tubo (179–281 mm de nó, 134–199 mm de tubo; na v20, 97–325 mm). Minha posição: o veredito CONDICIONAL é otimista. É preciso a restrição de existência de caminho de carga (R1 de F, com d_max A_CONFIRMAR) como item NAO_VERIFICAVEL, e a regra do hospedeiro (R2) antes de aprovar qualquer posição.
5. **Ordem de relaxamento.** Há três ordens: MR(0)/definição primeiro (B, C, E), curso/bump primeiro (D, G), variação de MR primeiro (A). Minha posição: primeiro as definições sem custo físico (MR(0), margem de curso), depois o bump, depois r2, por último a variação de MR. Isso concorda com C, D e E.
