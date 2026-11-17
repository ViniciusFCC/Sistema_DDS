# Resposta: lente de gestão do projeto (prazo, coordenação chassi × suspensão, custo de manter)

Rótulos: [F-xxx] fato de fonte (relatório da fase 1), [código] resultado rodado aqui (scripts e saídas em
`conselho/assento6_trabalho/`), [cálculo], [inferência], [hipótese].

## Q1. O método atual serve?

Como ferramenta de decisão, não. Como base de código, sim. O `kinlib` e o `avaliar` são o ativo a manter: uma
avaliação custa 0,127 s com 11 pontos de curso e 0,29 s com 25 [código, `tempo.py`]. O que falha é a formulação, e um
defeito pesa mais que os outros: **o script da suspensão desenha um tubo do chassi**. Ele impõe a reta Q–E, que tem de
cair a ≤ 8 mm do FH, como quase-igualdade. A v20 cumpre isso exatamente no limite (8,00 mm) [F-REGISTRO 2]. E o "fim
no FBH" é um ponto no ar, 45 mm para fora e 49 mm acima do quadro [F-GEO 6c].

Rodei um hipercubo latino de 4000 amostras numa caixa larga em torno da v20 [código, `lhs.py`].
- Nenhuma amostra cumpre todas as restrições, nem no critério estrito nem no relaxado.
- As que mais derrubam: MR ±0,01 (1,4 % das amostras passam), tubo ao FH (5,8 %), curso inteiro ±1 mm (9,7 %) e
  ângulo de 90° (12,7 %).

Repeti com o MR imposto por construção, corrigindo o braço r2 (800 amostras) [código, `lhs_mr.py`]:
- o MR passa em 86 %;
- continua sem solução viável, mesmo tirando a restrição do tubo;
- surgem 14 soluções quando se tira também o limite de 4 % de variação do MR.

[Inferência] O "1,1 milhão sem solução" é, em grande parte, um **conflito de projeto** entre MR ≤ 4 %, o curso inteiro
do DNM e o tubo amarrado ao FH. Algoritmo melhor não resolve isso. A ressalva é que 800 amostras em 8D não provam que
o conjunto viável é vazio. Algoritmo e formulação continuam sendo problema [F-LIT, Diagnóstico], mas o primeiro
desbloqueio é uma decisão da equipe.

## Q2. Método e arquitetura

O menor passo que destrava é refatorar o script atual. Reescrever do zero gasta prazo.

1. **Fase I primeiro.** O diagnóstico do LHS (`lhs.py`, cerca de 6 min em 4 núcleos) entra como modo `diagnosticar`.
   Ele imprime a taxa de cada restrição e as que nunca se cumprem juntas [F-LIT, item 3 e "Diagnóstico recomendado"].
   É o que a equipe precisa para decidir o que relaxar.
2. **Tirar as quase-igualdades por construção** [F-LIT 1]:
   - r2 sai do MR-alvo, o que já foi testado acima;
   - o comprimento e o curso saem de um catálogo de amortecedores;
   - os 90° saem do custo e viram objetivo no meio do curso [F-LIT, Peixoto p. 123].
3. **Fixação no chassi como escolha discreta**, numa lista de candidatos: nós existentes, pontos em tubo e nós
   propostos com custo. O tubo deixa de ser calculado pela suspensão. Isso também conserta a fronteira entre as duas
   subequipes.
4. **Restrições duras como desigualdades com margem**, e não como penalidade com peso fixo:
   - duras: gabarito, folgas por cápsula ao longo do curso e do esterço, curso do amortecedor, braços, giro e AIP
     [F-REGRAS 5, itens 1 a 8];
   - objetivos: variação do MR, desvio do plano do rocker e distância ao nó.
5. **Algoritmo simples:** enumerar as combinações discretas (nó, `ARM`, `LADO_ROCKER`), com multi-start por LHS e
   SciPy (SLSQP, ou `differential_evolution` se a avaliação não for suave). Valem as regras de Deb [F-LIT 4].
6. **Saída:** uma tabela de candidatos viáveis com as margens de cada restrição e a reavaliação em 25 pontos
   (achado 1: 4,00 % vira 5,2 %). Junto vai um "pedido ao chassi" com o nó que cada candidato exige.

Fica para depois, por custo de manutenção: o Fusion no laço, o MCP, o elemento finito e o NSGA-II. O Pynite entra
quando o critério de esforço for decidido [F-SKILLS 5]. Dependências: só numpy e scipy no laço; o OCP só na leitura do
STEP.

## Q3. Uso dos tubos e nós do CAD

- **Passo offline, fora do laço de busca.** O `step_tubos.py` já faz isso: lê o STEP em cerca de 3 min e grava
  `tubos.json` e `nos.json` [F-GEO 1]. Cada rodada registra o hash do STEP.
- **Um `reserva.json` mantido à mão pelo chassi:**
  - cápsulas "fantasma" para os tubos previstos e ainda não desenhados [F-PRATICA, risco 3];
  - entre eles, os obrigatórios por regra: apoio do FBH com três membros por lado e Side Impact [F-REGRAS 3.2].
  - [Inferência] Sem isso o script "aprova" espaço vazio. Hoje a zona entre o FH e o FBH está vazia [F-GEO 3] e o nó
    triangulado mais próximo do pivô está a 237 mm [F-GEO 6a].
- **Convenção barata no Fusion:**
  - prefixo nos corpos (`FH_`, `FBS_`, `SIDE_`);
  - um ponto nomeado "eixo dianteiro, linha de centro, chão" [F-GEO 8.2 e 8.6].
  - Isso custa menos do que manter heurísticas de reconhecimento. Hoje o Z depende só do FH0/FH1 do script.

## Q4. Coordenação chassi × suspensão

1. **O chassi entrega primeiro** o esqueleto da caixa dianteira, só com a linha dos tubos obrigatórios por regra,
   mais o `reserva.json`.
2. **A suspensão roda a Fase I e a Fase II** contra esse esqueleto e devolve candidatos e pedidos de nó.
3. **O chassi aceita ou recusa** cada pedido, com o custo em tubos e massa: é o bi-nível com biblioteca de nós
   [F-LIT 5].
4. **Congela os hardpoints** numa data marcada a partir de julho de 2027. A data é a equipe que define; não proponho
   nenhuma.

Regras de trabalho:
- **Uma interface só:** uma tabela de hardpoints com dono, estado (proposto, aceito, congelado) e hash do STEP.
- **Sincronização periódica** a cada nova versão do STEP.
- **Dados que bloqueiam, cada um com responsável:** X da face dos pedais (fim do gabarito) [F-REGRAS 5.3]; curso da
  cremalheira e batentes [F-REGRAS 4]; envelope de aro, manga e pinça (freio dentro da roda); posição do FBH (há 4,9 mm
  de divergência) [F-GEO 5]; modelo do amortecedor.
- **Contra a troca de pessoas:** cada limite no bloco de configuração tem fonte ou o rótulo "decisão da equipe". Um
  caso de teste com resultado conhecido (a v20) roda antes de cada mudança.

## Q5. Riscos e o que validar primeiro

Riscos:
1. **O conjunto viável é vazio com os limites atuais.** É provável pelo LHS. Então o produto é uma decisão: relaxar o
   MR ≤ 4 %, trocar o amortecedor ou o MR-alvo, ou criar um nó. Isso não é código.
2. **O chassi muda e invalida os candidatos.** Mitigação: o `reserva.json` e o hash do STEP.
3. **Excesso de engenharia consome o prazo** [inferência]. Não fazer o pipeline do Fusion antes de a Fase I responder.
4. **O `kinlib` nunca foi validado** [F-GEO 7]. Conferir um caso contra o OptimumKinematics, que é a REFERENCE
   (EDR-004).
5. **O limite de distância ao nó não tem número** em regra nem em literatura [F-REGRAS 3.5; F-LIT 4]. Tem de virar
   critério de esforço, sem inventar valor.

Teste mínimo que derrubaria esta recomendação: tirar só a restrição do tubo ao FH e rodar o Nelder-Mead atual a
partir de cerca de 50 sementes do LHS. Se ele achar soluções que cumprem tudo no critério estrito e na reavaliação em
25 pontos, o conflito é só o acoplamento do tubo. Aí basta essa correção e a refatoração pode esperar. Custo: menos de
uma hora de máquina [cálculo: 0,127 s × cerca de 2000 avaliações × 50 sementes ≈ 3,5 h em um núcleo, cerca de 1 h em
4].

## Recomendação em uma frase

Mantenha o `kinlib` e o `avaliar` e acrescente primeiro o modo de diagnóstico (Fase I). Leve à equipe a decisão sobre
os limites em conflito. Troque o tubo imposto ao FH por escolha de fixação numa lista de nós e reservas que a subequipe
de chassi mantém, e só então ponha a busca com restrições explícitas.

## Confiança e principal incerteza

Média. A principal incerteza é se o vazio do LHS reflete um conflito real ou só a caixa de amostragem larga e as
poucas amostras: 800 a 4000 em 8D.
