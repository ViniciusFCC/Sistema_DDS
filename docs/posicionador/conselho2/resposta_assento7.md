# Resposta: o que é regra, o que é meta e o que se pode relaxar com segurança

Rótulos: [F] fato de fonte (arquivo citado); [C] resultado de código meu (`conselho2/trabalho_assento7/rejulgar_curso.py`, saída `rejulgar_curso.json`, cerca de 1 min); [K] cálculo; [I] inferência; [H] hipótese.

## Q1. Onde se perde precisão no veredito

1. **Nenhum item da configuração tem origem REGRA** [F `data/posicionador/config_T11.json`]. As duas regras modeladas estão desligadas porque os valores são nulos (A_CONFIRMAR): o gabarito T.1.2 (x/z_ini/fim_t12) e F.8.6.1 (x_face_traseira_aip) [F `varredura.py`, docstring]. Hoje o juiz não confere nenhum artigo do regulamento. Ele só confere metas da equipe e margens.
2. **V.3.1.1 (curso útil de roda ≥ 50 mm com piloto sentado; R27 p.20)** [F `pesquisa/relatorio-regras.md` §3.1] não é uma restrição explícita. O relatório o dá como "atendido por valores do script" [F idem, item 18]. Ninguém confirmou que dz = 0 corresponde ao piloto sentado: **a confirmar**.
3. **EYE = 210 mm e STROKE = 61 mm estão rotulados META** [F config]. Discordo do rótulo. São dados de componente (DNM RCP2S) e precisam de catálogo como fonte. Hoje a fonte é o script, sem a folha do fabricante: **a confirmar**. Relaxá-los não é decisão de meta. Só se pode trocar de amortecedor.
4. **O OK com folga de +0,03 mm é tratado como cumprido** [C]. Contra a tolerância de fabricação, isso não significa nada: no conselho anterior, ±0,5 mm derrubou cerca de 50 % das amostras [F `conselho/SINTESE.md`].

Prioridade:
- (a) Criar a origem `DADO_COMPONENTE`, que é dura e só muda com a troca da peça. Rotular EYE e STROKE com ela.
- (b) Tornar V.3.1.1 uma restrição REGRA explícita no certificador, com a condição "dz = 0 com piloto sentado" como item A_CONFIRMAR.
- (c) Publicar toda folga em mm ao lado da δ de fabricação, que está "a medir".

Prova: um teste em que o candidato com folga de 0,03 mm sai CONDICIONAL com o aviso "margem < δ".

## Q2. Por que não há posição viável (sem CAD)

**(a) O conflito de metas existe por construção.**
- O olhal do chassi é posto de modo que o amortecedor fique em EYE exatamente no droop [F `mecanismo.py`, `construir`].
- O bump vale 62,4 mm = 61 × 1,40 − 23 [F config, fonte de `curso_bump_m`].
- Então MR(0) = 1,40 e "curso inteiro" se equilibram só se o MR médio no curso for ≥ 1,40 [K]. Qualquer MR médio abaixo disso consome mais que 61 mm de curso do amortecedor. Margem zero nas duas pontas é escolha da formulação, não da física.

**Rejulgamento das 6 soluções finais do posicionador** [C]. A geometria é a mesma, com r2 fixo; só muda o curso de bump.

| Bump (curso total da roda) | Sem violação | Folga do comprimento mínimo |
|---|---|---|
| 62,4 mm (85,4) | 0/6 | −0,51 a −0,74 mm |
| 61,4 mm (84,4) | 3/6 CONDICIONAL | +0,03 mm |
| 60,4 mm (83,4) | 4/6 CONDICIONAL | +0,68 a +0,75 mm |

As outras duas violam o braço r2 > 80 mm; a variação de MR cai um pouco (3,87 → 3,70 % na semente 0).

A hipótese do BRIEF se confirma sem CAD [C]. A causa (a) responde por tudo o que sobra nas restrições compartilhadas. Com o STEP, a variação de MR é violada em 99 % das amostras [F BRIEF]. Isso é outra causa, (b) ou (c), e fica para as outras lentes.

Experimento que decide: repetir a busca com o STEP e bump em 60,4 mm. Se a fração com a variação de MR violada não cair, o vazio com o CAD não vem das metas de curso.

## Q3. Mudança de método

Classificar cada restrição pela procedência e dar a cada classe um tratamento:

- **Duras e inegociáveis:** REGRA com artigo e versão (R27 V1.0; conferir a V2 e o addendum FSAEB do ano [F relatório-regras §1]); DADO_COMPONENTE; não colidir com o chassi.
- **Duras e parametrizadas:** MARGEM_EQUIPE.
- **Eixos de Pareto:** as META.

A mudança concreta é **tirar o bump fixo da entrada**:
- O curso de roda disponível vira uma saída: ∫ MR dLs, de EYE − margem_topo até EYE − STROKE + margem_fundo.
- A restrição dura passa a ser "curso disponível ≥ 50 mm (V.3.1.1) com piloto sentado".
- A meta de 85,4 mm vira um objetivo.

## Q4. Mapa de conflitos e ordem de relaxamento

**Custo medido** [C, K]:
- Cada 1 mm de bump libera cerca de 0,72 mm de amortecedor (≈ 1/MR).
- Logo, cada 1 mm de margem de fim de curso custa ≈ 1,39 mm de bump.
- Com 2 mm de margem de fim de curso [C]:
  - bump de 59,4 mm: 0/6 sem violação;
  - bump de 58,6 mm: 3/6, com folga de só +0,03 mm;
  - bump de 58,0 mm (curso total 81,0 mm): 4/6 CONDICIONAL, com +0,41 a +0,47 mm além da margem.
- Com 3 mm de margem e 58,0 mm de bump: 0/6.

**Ordem proposta**, da mais segura à mais arriscada:

1. **Curso de bump (META).**
   - É legítimo. O piso da regra é 50 mm; 81,0 mm deixam 31 mm acima dele [K].
   - Aproveita para criar a margem de fim de curso. Essa margem protege o amortecedor e o olhal do impacto no batente, e a SINTESE já pedia "margem de curso do amortecedor já".
   - Pergunta à equipe: "Qual curso de roda (bump e droop, com piloto sentado) vocês exigem do T11, e qual margem de fim de curso do amortecedor (mm, nas duas pontas, incluindo o batente de borracha do DNM)?"
2. **Braço r2 ≤ 80 mm (META).**
   - Não é regra. Relaxar é legítimo se o rocker couber e a folga ao chassi continuar positiva.
   - Pergunta: "O limite de 80 mm vem de quê (peso, rigidez, chapa disponível)? Aceitam até quanto?"
3. **Variação de MR ≤ 4 % (META de desempenho, sem segurança).**
   - Pergunta: "Os 4 % se medem em que curso? Aceitam variar se o MR for progressivo?"
4. **Ângulo do amortecedor ≤ 30° (META).**
   - Mexe na carga fora do plano no pivô, com envelope de cargas a confirmar.
   - Só relaxar com verificação estrutural.

**Relaxamentos perigosos ou reprovados:**
- Encurtar o comprimento mínimo (149 mm) ou alongar o curso além do catálogo. O amortecedor bate no fim de curso: é fisicamente impossível, não é relaxamento.
- Zerar a margem de fim de curso.
- Cortar a folga do aro ou das pernas abaixo da deflexão real (sem dado).
- Reduzir a folga do gabarito. A regra tem folga zero [F relatório-regras D8], mas a inspeção mede o carro real, não o CAD.
- Qualquer item REGRA: T.1.2, F.8.6.1, V.3.1.3, T.1.3.3/4, V.3.2.4, V.1.1.
- Depois da aprovação na inspeção, o curso tem de ser mantido (IN.16.2.1 [F relatório-regras §3.1]). Um batente escolhido depois não pode tirar o curso abaixo de 50 mm.

## Q5. Riscos, o que derrubaria esta recomendação e o que não fazer

**Riscos:** CONDICIONAL tratado como pronto; dz = 0 não ser a altura com piloto sentado; curso útil de catálogo < 61 mm (batente de borracha); as regras hoje desligadas (T.1.2, AIP) reprovarem depois.

**Testes que derrubam esta recomendação:**
- (1) Com o CAD e δ medida, o caso de 58,0 mm de bump e 2 mm de margem perde as 4 soluções (por colisão ou por tolerância).
- (2) A folha do DNM RCP2S traz curso útil diferente de 61 mm.
- (3) Com o STEP e o bump reduzido, a variação de MR continua violada em cerca de 99 %. Nesse caso o curso não é o gargalo com CAD.

**Não fazer:**
- Editar `config_T11.json` como se a mudança fosse aprovada. Os cenários aqui são CENÁRIO/HIPOTESE, gravados só na minha pasta.
- Chamar de VIAVEL o que tem folga de 0,03 mm.
- Relaxar DADO_COMPONENTE ou REGRA.

**Recomendação em uma frase:** Tratar o comprimento do amortecedor como dado de componente (duro) e V.3.1.1 como a única regra de curso (≥ 50 mm com piloto sentado), transformar o curso de bump de 62,4 mm em objetivo e propor à equipe, como primeiro relaxamento, 62,4 → 58,0 mm de bump (curso total 81,0 mm, ainda 31 mm acima da regra) em troca de 2 mm de margem de fim de curso. Medido sem CAD, isso deixa 4 de 6 soluções sem violação e ainda aumenta a segurança, em vez de aceitar folgas de 0,03 mm.

**Confiança: média.** Principal incerteza: não está confirmado que dz = 0 é a altura com piloto sentado, nem qual é o curso útil do DNM no catálogo, e o efeito com o STEP não foi testado.
