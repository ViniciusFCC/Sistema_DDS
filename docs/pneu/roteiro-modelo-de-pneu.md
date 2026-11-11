# Roteiro do modelo de pneu

Registro de 2026-11-11, feito a pedido do usuário depois do merge do subprojeto A (PR #41, EDR-071). Este documento não
é spec, plano nem decisão. Ele junta, num lugar só, os degraus que já estão na spec do pneu com estado
(`docs/superpowers/specs/2026-11-02-pneu-estado-design.md`, §1 e §12) e os que ficam depois deles. Cada degrau novo
precisa de spec, plano e EDR próprios antes de qualquer implementação.

Status usado na coluna "Situação":
- **feito**: implementado e VERIFIED (código e testes certos; não quer dizer validado fisicamente);
- **na spec**: já citado na spec do pneu com estado, sem plano;
- **sugerido**: não está em spec nem em plano. É sugestão do registro de 2026-11-11, tirada do roadmap
  (`docs/arquitetura-planejada-roadmap-V0-V5.md`, §7.2, §7.4 e §9) e da física do pneu de FSAE. Ainda não foi aprovada.

## Onde estamos

| Degrau | Situação | O que faz | Limite principal |
|---|---|---|---|
| Modelo estático (EDR-067) | feito | Fx e Fy, puros e combinados, a partir dos coeficientes PAC2002 do `.tir` do TTC, sem ajuste próprio | Regime permanente, uma pressão, sem temperatura |
| A1 e A2 (EDR-071) | feito | Compara as 4 pressões medidas (8, 10, 12 e 14 psi) e interpola entre elas, com o rótulo INTERPOLADO | Pneu R25B no lugar do R60A; pressão de ensaio; caso de outro carro |

## Degraus que já estão na spec

| # | Degrau | O que acrescenta | Dado que falta | Depende de |
|---|---|---|---|---|
| 1 | A2 no carro | O caso do carro passa a aceitar qualquer pressão entre 8 e 14 psi e pressão diferente na frente e atrás (`ds` por eixo), que é uma regulagem real do equilíbrio | Nenhum novo | A1 e A2 |
| 2 | Ajuste PP*/QPZ do PAC2002 | Um modelo único e contínuo em pressão, no lugar da interpolação entre perfis ajustados separadamente | Medição bruta do TTC (as varreduras, não só os `.tir`) | Revisão do EDR-015 e da recusa de PP* no carregador |
| 3 | A3: pressão em operação | Liga a pressão fria de calibração à pressão quente da pista, que sobe com a temperatura do ar no pneu; a variável escondida é a temperatura (Milliken, p. 55-56) | Pressão e temperatura medidas em pista e um modelo térmico | A2 no carro |
| 4 | B: transiente do pneu | Comprimento de relaxação σ: a força cresce com a distância rodada, o que pesa na entrada de curva, no slalom e no amortecimento da guinada | σ (os `.tir` têm PTX e PTY nulos); fonte possível: rigidez lateral da carcaça medida em bancada, com σα = C_Fα/C_Fy (Pacejka) | A, porque a rigidez da carcaça varia com a pressão |
| 5 | C: dinâmica do veículo | Modelo do carro no tempo (bicicleta, depois 4 rodas com guinada e rolagem); no roadmap é a V3, com o CarSim como referência | Os mesmos do B, mais os do carro | B |

## Depois desses degraus (sugerido)

Em ordem aproximada de valor para um Fórmula SAE elétrico:

| # | Tema | Por que importa | Dado ou referência que falta |
|---|---|---|---|
| 6 | Pneu da equipe (R60A) | Enquanto o projeto usar o R25B como substituto, todo resultado de pneu é de outro pneu | Dados do R60A, ou correção do R25B pela medição de pista (item 8) |
| 7 | Resistência ao rolamento (My) | Pesa na energia do enduro e na prova de eficiência; também varia com a pressão | Coeficientes com fonte; o roadmap já a lista entre os limites a declarar (§7.4) |
| 8 | Escala do TTC para a pista (λμ), calibrada no skidpad | A cinta do TTC não é asfalto, e hoje o fator de perda é hipótese | a_y e ângulo de volante medidos no skidpad; é o começo da validação (roadmap §9) |
| 9 | Momento auto-alinhante (Mz) e trilha pneumática; Mx | Esforço e sensação no volante; influem no caster e no braço da direção | Coeficientes do `.tir` conferidos; comparação com a referência |
| 10 | Deslizamento combinado validado | Frear ou acelerar em curva depende dele; os coeficientes combinados do `.tir` estão "não determinado" no EDR | Varreduras combinadas do TTC ou medição de pista |
| 11 | Temperatura como estado do pneu | O μ muda com a temperatura da banda: aquecimento nas primeiras voltas e janela de trabalho | Temperatura da banda em pista e um modelo térmico; estende o A3 |
| 12 | Desgaste e degradação no enduro | Perda de aderência ao longo das voltas; estratégia do enduro e da troca de pilotos | Dados de pista ao longo de uma prova |
| 13 | Comportamento vertical e geometria | A rigidez vertical é a mola em série com a suspensão e muda com a pressão; o raio carregado e o de rolamento afetam a altura do carro e a relação de transmissão | Origem da `VERTICAL_STIFFNESS` do `.tir` (não verificada) ou medição em bancada |
| 14 | Comparação com o OptimumTire | Pelo EDR-004 ele é a REFERENCE do pneu e o Python é só o MODEL; ainda não há comparação ponto a ponto | Acesso ao OptimumTire com o mesmo dataset |
| 15 | Ciclo de engenharia (V5 do roadmap) | Prever, medir, comparar e recalibrar, com incertezas registradas; é o que leva o modelo de VERIFIED a validado num domínio declarado | Instrumentação e procedimento repetível (roadmap §9.2) |

## Ordem que faz sentido hoje

Quase tudo depende de dado que o projeto ainda não tem: o R60A, pressão e temperatura em pista, o σ da carcaça e um
skidpad instrumentado. Com o que já existe, só andam o degrau 1 (A2 no carro), o 14 (comparação com o OptimumTire)
e a parte de modelagem do 7, que mesmo assim precisa de coeficiente com fonte. A ordem recomendada:

1. Terminar a planilha, que é o foco declarado do projeto (incremento 9, V5.0).
2. Planejar a coleta de dados com o T11 andando: skidpad, sensores de pressão e temperatura e, se der, a bancada da
   carcaça.
3. Retomar o pneu pelos degraus que esses dados destravarem.

Nada aqui define valor, coeficiente ou limite. Todo número que um degrau futuro usar precisa de fonte; sem fonte, fica
"a confirmar".
