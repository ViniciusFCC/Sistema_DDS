# Roteiro do modelo de pneu

Registro de 2026-11-11, feito a pedido do usuário depois do merge do subprojeto A (PR #41, EDR-071) e revisto no
mesmo dia com a análise do conselho (5 conselheiros, revisão anônima). Este documento não é spec, plano nem decisão.
Ele junta, num lugar só, os degraus que já estão na spec do pneu com estado
(`docs/superpowers/specs/2026-11-02-pneu-estado-design.md`, §1 e §12) e os que ficam depois deles, com a ordem
recomendada pelo conselho. Cada degrau novo precisa de spec, plano e EDR próprios antes de qualquer implementação.

Status usado na coluna "Situação":
- **feito**: implementado e VERIFIED (código e testes certos; não quer dizer validado fisicamente);
- **na spec**: já citado na spec do pneu com estado, sem plano;
- **sugerido**: não está em spec nem em plano. É sugestão do registro de 2026-11-11, tirada do roadmap
  (`docs/arquitetura-planejada-roadmap-V0-V5.md`, §7.2, §7.4 e §9), da física do pneu de FSAE e do conselho. Ainda
  não foi aprovada.

## Onde estamos

| Degrau | Situação | O que faz | Limite principal |
|---|---|---|---|
| Modelo estático (EDR-067) | feito | Fx e Fy, puros e combinados, e os momentos Mx, My e Mz (PAC2002, Eq. 100-110; `python/tire_model_static.py`), a partir dos coeficientes do `.tir` do TTC, sem ajuste próprio | Regime permanente, uma pressão, sem temperatura; My sai zero porque QSY1 a QSY8 são zero no `.tir`; a forma da Eq. 103 do Mz (até ~28 % do Mz) espera a comparação com o OptimumTire (EDR-067, item 3) |
| A1 e A2 (EDR-071) | feito | Compara as 4 pressões medidas (8, 10, 12 e 14 psi) e interpola entre elas, com o rótulo INTERPOLADO | Pneu R25B no lugar do R60A; pressão de ensaio; caso de outro carro |

Dois fatos do código que mudam a leitura dos degraus:
- O consumidor principal do pneu, `python/equilibrio.py`, importa o `tire_model` base, não o modelo estático. O A2 no
  carro passa por essa migração.
- A `VERTICAL_STIFFNESS` do `.tir` (120312 N/m a 12 psi) é QFZ1·FNOMIN/R0, um coeficiente do ajuste do R25B, e não
  uma medição de bancada.

## Degraus que já estão na spec

| # | Degrau | O que acrescenta | Dado que falta | Depende de |
|---|---|---|---|---|
| 1 | A2 no carro | O caso do carro passa a aceitar qualquer pressão entre 8 e 14 psi e pressão diferente na frente e atrás (`ds` por eixo), que é uma regulagem real do equilíbrio | Nenhum novo; antes, confirmar que a pressão de trabalho da equipe cabe em 8 a 14 psi (Fase 0) | A1 e A2; teste de equivalência por valor entre o `tire_model` base e o estático |
| 2 | Ajuste PP*/QPZ do PAC2002 | Um modelo único e contínuo em pressão, no lugar da interpolação entre perfis ajustados separadamente | Medição bruta do TTC (as varreduras, não só os `.tir`) | Revisão do EDR-015 e da recusa de PP* no carregador; não antes do item 6 |
| 3 | A3: pressão em operação | Liga a pressão fria de calibração à pressão quente da pista, que sobe com a temperatura do ar no pneu; a variável escondida é a temperatura (Milliken, p. 55-56) | Pressão e temperatura medidas em pista e um modelo térmico | A2 no carro |
| 4 | B: transiente do pneu | Comprimento de relaxação σ: a força cresce com a distância rodada, o que pesa na entrada de curva, no slalom e no amortecimento da guinada | σ (os `.tir` têm PTX e PTY nulos); fonte possível: rigidez lateral da carcaça medida em bancada, com σα = C_Fα/C_Fy (Pacejka) | A, porque a rigidez da carcaça varia com a pressão; só pesa junto com o C |
| 5 | C: dinâmica do veículo | Modelo do carro no tempo (bicicleta, depois 4 rodas com guinada e rolagem); no roadmap é a V3, com o CarSim como referência | Os mesmos do B, mais os do carro | B |

## Depois desses degraus (sugerido)

| # | Tema | Por que importa | Dado ou referência que falta |
|---|---|---|---|
| 6 | Pneu substituto do T11 | Enquanto o projeto usar o R25B no lugar do R60A, todo resultado de pneu é de outro pneu. A pergunta é: com que pneu substituto o T11 projeta, e com que margem | Dados do R60A (Hoosier, TTC), ou correção do R25B pela medição de pista (item 8) |
| 7 | Resistência ao rolamento | Pesa na energia do enduro e na prova de eficiência. O My já está no código, mas sai zero (QSY nulos) | Coeficientes com fonte; ou medir a resistência ao rolamento como parâmetro do carro, por coast-down, com as perdas do trem de força declaradas |
| 8 | λμ e λKy calibrados no skidpad | A cinta do TTC não é asfalto, e hoje o fator de perda é hipótese. O skidpad mede o carro, não só o pneu: o λ sai invertendo o modelo de equilíbrio do mesmo carro, como faixa por condição (ou λμ(Fz)), com incerteza | a_y, ângulo de volante e velocidade no skidpad, com repetição e correção da rolagem na IMU; o λKy pelo gradiente de esterçamento |
| 9 | Mz, trilha pneumática e Mx | Esforço e sensação no volante; influem no caster e no braço da direção. Já implementados; o uso de projeto espera o item 14 (EDR-067) | Faz parte do item 14 |
| 10 | Deslizamento combinado validado | Frear ou acelerar em curva, e a regeneração na entrada de curva; os coeficientes combinados do `.tir` estão "não determinado" no EDR | Varreduras combinadas do TTC (fonte de laboratório) ou medição de pista (fonte de pista), rotuladas separadamente |
| 11 | Temperatura como estado, com ciclos térmicos | O μ muda com a temperatura da banda: aquecimento nas primeiras voltas, janela de trabalho, e a degradação ao longo das provas com o mesmo jogo de pneus (o desgaste entra aqui) | Temperatura da banda em pista e um modelo térmico; estende o A3 |
| 12 | Rigidez vertical do pneu | É a mola em série com a suspensão: entra na rigidez de rolagem e no ride, e muda com a pressão. O valor de hoje vem do ajuste do R25B | Deflexão do pneu da equipe sob carga conhecida (ensaio de garagem) ou dado do fabricante com a pressão declarada |
| 13 | Raio carregado e raio de rolamento | Afetam a altura do carro, o κ medido pela velocidade de roda e a relação de transmissão (domínio do trem de força) | Medição com o pneu e o aro da equipe |
| 14 | Comparação com o OptimumTire | Pelo EDR-004 ele é a REFERENCE do pneu e o Python é só o MODEL; ainda não há comparação ponto a ponto. Destrava o item 9 | Licença do OptimumTire com o mesmo `.tir` |
| 15 | Arrasto induzido pela deriva | Na energia do enduro, a perda por escorregamento (Fy·sen α e Fx·κ) pode pesar tanto ou mais que a resistência ao rolamento (Milliken, cap. 2, exemplo do arrasto induzido; conferir a página) | Nenhum novo: o modelo já calcula Fy, Fx, α e κ |
| 16 | Estudo de sensibilidade | Diz, com números, quais degraus mudam alguma decisão do T11: varredura de λμ e de pressão sobre as saídas que a equipe usa (`eq.varredura_pneu` já existe) | Nenhum novo |
| 17 | Instrumentação e contrato de dados de ensaio | Uma só instrumentação (IMU, ângulo de volante, curso dos amortecedores, pressão e temperatura, velocidade de roda) alimenta os itens 3, 7, 8, 10 e 11; o contrato de dados define formato, unidade no nome, origem, calibração, SHA do log e o rótulo de origem | Procedimento escrito e o datalogger da equipe |
| 18 | Ciclo de engenharia (V5 do roadmap) | Guarda-chuva dos itens 6, 8, 10 e 17: prever, medir, comparar e recalibrar, com incertezas registradas; é o que leva o modelo de VERIFIED a validado num domínio declarado | Roadmap §9.2 |

## Ordem recomendada (conselho, 2026-11-11)

Nada de pneu entra na V5.0 (incremento 9). Fases:

**Fase 0: agora, sem código.**
1. Perguntar à equipe: que pneu, que aro e que pressões fria e quente o T11 vai usar; se há licença do OptimumTire;
   se o TX ainda roda e tem datalogger. A Hoosier indica para o R60A uma pressão fria acima de 14 psi (catálogo citado
   por um conselheiro, a confirmar): se a pressão de trabalho ficar fora de 8 a 14 psi, o A2 não cobre o uso real.
2. Pedir à Hoosier e ao TTC os dados do R60A.

Respostas do usuário (2026-11-12):

| Pergunta | Resposta | Consequência |
|---|---|---|
| Pneu e aro do T11 | Hoosier R60A, aro 13 | Mesmo aro do R25B do `.tir` (20.5x7-13); falta confirmar a largura do aro, porque outra largura muda o Cα e a rigidez vertical |
| Pressão de uso | Ainda não definida; faixa de 8 a 14 psi | Cabe na faixa do TTC e do A2: o pneu-3 (A2 no carro) fica liberado. O número de catálogo citado por um conselheiro deixa de importar |
| Licença do OptimumTire | Licença de estudante | O pneu-2 (comparação, itens 14 e 9) fica liberado; falta conferir se a licença importa `.tir` PAC2002 e exporta as curvas |
| TX e datalogger | O TX vai rodar, sem datalogger | A Fase 2 usa métodos sem aquisição (abaixo); coast-down e ângulo de volante ficam para quando houver aquisição |
| Dados do R60A | Pedidos e negados | O R25B continua como substituto. O caminho é calibrar a escala do R25B no skidpad com o R60A montado (corrige o nível de aderência, não a forma das curvas). A conferir: se o TTC tem o R20 (citado para o Round 9 por um conselheiro) e se ele é mais próximo do R60A |

**Fase 1: depois da V5.0, só Python, sem planilha nova.** Verificação pelos testes do pneu; a suíte inteira fica
para o fechamento de versão.
- pneu-1: estudo de sensibilidade (16) e arrasto induzido (15).
- pneu-2: comparação com o OptimumTire (14 e 9), se houver licença.
- pneu-3: A2 no carro (1), com os pré-requisitos da tabela e as bandas do EDR-071; saída rotulada "outro pneu, não é
  calibragem", fora da planilha até uma versão própria. A pressão entra numa estrutura mínima que dá para estender
  depois; uma interface genérica de estado do pneu fica para quando houver dado de temperatura ou de σ.

**Fase 2: coleta, com o procedimento escrito antes, em paralelo.**
- Contrato de dados de ensaio (17), no fluxo de commits `dados:` do repositório.
- Ensaios de garagem: deflexão do pneu (12), balança de cantos, manômetro calibrado.
- Piloto com o TX: skidpad nos dois sentidos (8), pressão e temperatura ao fim de cada stint (3 e 11), coast-down (7).
  O λ medido no TX com o modelo do R25B e aplicado ao T11 é uma dupla substituição e leva rótulo e incerteza próprios.
- Sem datalogger no TX (resposta de 2026-11-12): skidpad cronometrado, com o raio medido a trena e a_y = v²/R,
  v = 2πR/t, várias voltas por sentido para estimar a dispersão; pressão com manômetro calibrado e temperatura com
  pirômetro infravermelho de mão, logo ao fim de cada stint; deflexão do pneu e balança de cantos na garagem. O
  coast-down e o ângulo de volante (λKy) esperam um sistema de aquisição.

**Fase 3: quando o dado chegar.** A3 e temperatura (3 e 11), troca do pneu (6), combinado (10), PP*/QPZ (2), B (4)
e C (5).

## Riscos registrados pelo conselho

- Uma saída de pneu com cara de calibragem pode chegar à equipe antes de qualquer medição; VERIFIED não é validado.
- Os perfis do `.tir` são ajustes independentes e não monotônicos em pressão: parte do "efeito da pressão" pode ser
  ruído entre ajustes (as bandas do EDR-071 tratam isso no A1).
- O skidpad mistura pneu, camber dinâmico, asfalto e piloto: a calibração precisa da cinemática junto.
- A faixa de Fz do TTC precisa cobrir as cargas de canto do T11 (EDR-056).

Nada aqui define valor, coeficiente ou limite. Todo número que um degrau futuro usar precisa de fonte; sem fonte, fica
"a confirmar".
