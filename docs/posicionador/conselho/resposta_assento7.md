# Resposta: lente de regulamento, segurança e manufatura

Rótulos: [F-x] fato do relatório x; [C] resultado de código meu (`conselho/assento7_trabalho/`); [K] cálculo; [I] inferência; [H] hipótese.

## Q1. O método atual é adequado?

Não. Além dos defeitos de formulação [F-lit; REGISTRO 1-6], há três que nenhum algoritmo corrige:

1. **Regra modelada errada.**
   - O gabarito T.1.2 tem altura livre (T.1.2.2c). Vale de trás da coluna até 100 mm atrás da face do pedal. Tem 4 chanfros, entalhes e faixa central de 50 mm [F-regras D2-D6].
   - O script fixa Z 200-550 e X ≤ 350. Isso não é conservador nem liberal [I]. Parte do "batia no gabarito" pode ser artefato disso [H].
   - `X_FIM=350` implica pedal em X 450. Sobram 32 mm até a face do FBH (482,4 [F-geo]) para o conjunto de pedais, que ainda exige 25 mm de folga (F.8.6.3) [K]. Isso é improvável [I].
   - Faltam T.1.3.3/4 (escudo removível), V.3.1.3 (fixação visível), F.8.6.1 (nada à frente da AIP), F.5.14 (proteção da cremalheira) e V.3.2.4 (batentes; o aro só é checado com a roda reta) [F-regras §5].
2. **Não fabricável.**
   - O tubo de montagem termina no ar: E fica 45 mm para fora e 49 mm acima do canto do FBH [F-geo §6c].
   - Q fica no meio do FH, 65 mm acima de N11, que não é triangulado [F-geo §6a].
   - É o modo de falha da UM-Rolla: aba no meio do vão dobra o tubo [F-prática §5].
3. **Margem zero contra tolerância.** Perturbei o pivô e o olhal da v20 em ±δ por eixo, com o push rod reajustado ao estático [C]:
   - δ = 0,5 mm: 0 % cumpre os limites do próprio script. Em cerca de 50 % o curso exigido passa de 61 mm, porque a v20 usa 100 % do curso do DNM.
   - δ = 2 mm: a janela do amortecedor anda de −3,5 a +3,1 mm.

Discordo do LIT: a "fixação em nó exigida pelas regras" (Schweighardt) não existe na R27 [F-regras §3.5]. Nó é critério de engenharia e deve entrar como esforço calculado, não como filtro regulamentar.

## Q2. Método e arquitetura

Base do LIT: hospedeiros discretos (nó ou tubo), variáveis contínuas locais, desigualdades com margem, duas fases, multi-start e cápsulas. Acrescento:

- **Procedência de cada restrição.**
  - REGRA, dura, com artigo e versão (R27 V1.0; conferir a V2 e o addendum 2027, que não foi encontrado [F-regras §1]).
  - MARGEM DA EQUIPE, dura e parametrizada. Exemplo: os 10 mm do gabarito são margem, não regra (D8).
  - PREFERÊNCIA, que vai para o objetivo.
- **Gabarito.** Testar se existe trajetória z(x) livre para o contorno completo, de X traseira da coluna até X pedal − 100. A faixa de 50 mm é permitida. O teste inclui coluna, cremalheira, banco e pés.
- **Kit de fixação por ponto.**
  - Abas em cisalhamento duplo (V.3.1.5).
  - Eixo e comprimento do parafuso.
  - Volumes livres para inserir e retirar o parafuso, para a chave e para a tocha de solda.
  - Escudo de T.1.3.3, se a peça ficar no cockpit.
  - Marca de furo em tubo da Primary Structure, que vai para a SES (F.5.3.1).
- **Robustez como restrição dura.** O candidato tem de ser viável em toda a caixa ±δ, com margem de curso e faixa de ajuste do push rod. δ é a capacidade medida da equipe: **dado a medir**.

Saída: lista não dominada, com checklist por regra (PASS, FAIL ou NÃO VERIFICÁVEL). Basta um NÃO VERIFICÁVEL para o candidato sair "condicional", nunca "aprovado".

## Q3. Tubos e nós do CAD incompleto

Três classes de tubo, com etiqueta:

- **Existente:** sai do STEP pelo pipeline GEO, com o hash do arquivo.
- **Regulatório previsto:** corredores que a regra já fixa, como os 3 membros do suporte do FBH (F.6.2.3) e F.5.14. Servem como volume reservado e como hospedeiro candidato.
- **Proposto:** com custo e nó nas duas pontas.

[K] Q–E fica a 65 e 67 mm de N11 e N04. Ligado em N11–N04, viraria candidato a membro superior do suporte do FBH, com nós nas duas pontas [I]. Mas o pivô e o olhal ficam a cerca de 100 mm dessa reta, então é candidato a testar, não conclusão [H].

Pedir ao CAD: pontos nomeados (eixo e chão), face do pedal, coluna, banco e AIP [F-geo §8].

## Q4. Coordenação

1. Um responsável mantém o **envelope regulatório**, com artigo e versão de cada item: gabarito, pedal, AIP, volume do IA (F.8.4.2), Side Impact e corredores F.6.2.3. É o primeiro entregável.
2. O chassi fixa o esqueleto obrigatório, a ergonomia (F.5.6.5) e a coluna e a cremalheira. Avançar a cremalheira, relato (d), esbarra em F.8.6.3, T.1.3.3 e F.5.14.
3. A suspensão roda o script e pede nós.
4. O chassi aceita ou recusa, com custo.
5. Revisão de manufatura antes de congelar: gabarito de solda, acesso e SES.
6. Com o carro construído, medir contra o CAD e realimentar δ.

Rules Questions sobre F.8.6.1 e V.1.1 já: a GR.7 leva duas semanas ou mais.

## Q5. Riscos e teste mínimo

Riscos, do mais grave ao menos:

- Candidato "aprovado" que reprova na inspeção técnica: o carro não corre.
- Mudança de regra.
- Tolerância real maior que δ.
- Escudo e tampa sem espaço reservado.
- Banco, pedal e coluna fora do CAD, o que deixa o gabarito NÃO VERIFICÁVEL.

Testes que derrubariam minha ênfase:

- Rodar Z fixo e existência de z(x) em amostras LHS com o STEP atual. Conjuntos viáveis iguais = correção do gabarito irrelevante.
- Medir o TX contra o CAD. Desvio ≪ 0,5 mm = robustez vira detalhe.

**Recomendação em uma frase:** Adotar o método reformulado (hospedeiros discretos com nós do STEP e corredores de tubo regulatórios, desigualdades com margem e duas fases) e só chamar um candidato de "aprovado" se cada restrição tiver regra e versão, cada ponto tiver kit de fixação fabricável e acessível, e a viabilidade se mantiver em toda a caixa de tolerância de fabricação.

**Confiança: média.** Principal incerteza: os dados ausentes do CAD (pedal, banco, coluna, AIP) e a tolerância real da equipe, ainda não medida.
