# Revisão anônima (rodada 2)

Li só `anon/resposta_A.md` a `resposta_G.md` e a "Correção" do REGISTRO. Não rodei código novo. A conta de G, de
X_FIM 350 a 32 mm da face do FBH em 482,4, foi conferida à mão e fecha.

## 1. Por letra

**A**
- Mais grave: arquitetura sem formulação. Não pega a dependência da resolução no MR nem o bug do aro (outras pegam).
- Mais grave: os 10 a 30 ms por candidato e o limite de 0,01 mm na ida e volta são estimativa e escolha próprias. A migração para o `Corner` também não foi testada nesta geometria.
- Mais forte: mediu que a cápsula com meia largura no tubo quadrado superestima a folga em até 5,18 mm, ou seja, aprova o que bate.
- Mais forte: achou no repositório a cinemática testada (76 checks) e o schema de hardpoints, que ninguém mais citou.
- Mais forte: mostrou que o STEP não traz geometria de construção.

**B**
- Mais grave: a "prova de vazio" vale só para o limite arbitrário |Pv_x| ≤ 150 do próprio script. Ela mostra um conflito de limite, não a ausência de nó.
- Mais grave: o branch-and-bound é promessa, sem teste.
- Mais forte: taxas medidas por restrição (MR 0,87 %, conjunto 0/3000). A construção de r2 e de C subiu o conjunto para 16/1000, o que é evidência direta de que a formulação estrangula o espaço.

**C**
- Mais grave: Monte Carlo com 40 amostras não certifica robustez. "Passar em todas as amostras" não é prova.
- Mais grave: pouco sobre como o CAD entra.
- Mais forte: o MR não converge com a malha (4,00 / 5,19 / 5,70 / 6,08 %).
- Mais forte: o bug do aro no segmento errado.
- Mais forte: a v20 fica na fronteira (Ls mín. 148,94 contra 149; cerca de 50 % de violação a ±1 mm). Isso define o que "aprovado" tem de significar.

**D**
- Mais grave: manda manter o `kinlib`, que não foi validado e tem resíduos do TX, quando há módulo testado no repositório.
- Mais grave: confia no ponto nomeado vindo pelo STEP, o que não foi verificado.
- Mais grave: a conta "menos de uma hora" contradiz os 3,5 h que ela mesma calculou.
- Mais forte: com o MR por construção, só aparece viável relaxando os 4 %. Isso transforma o impasse em decisão da equipe.
- Mais forte: o teste das 50 sementes é barato.

**E**
- Mais grave: todos os números saem do `kinlib` não validado. O eixo "a 74°" depende da linearização em 1ª ordem.
- Mais forte: mostra uma incompatibilidade de conceito que nenhuma busca resolve: coplanaridade contra amortecedor a no máximo 30° de X, que exigiria pelo menos 66°.
- Mais forte: MR regressivo no bump e transmissão de 47°.

**F**
- Mais grave: o pórtico é próprio, sem validação, e as paredes são supostas. Os 300 a 800 MPa usam carga de outro carro.
- Mais forte: 145 a 393 MPa por kN no Q–E mostram que a v20 é estruturalmente inviável.
- Mais forte: a matriz de influência por versão do STEP põe a estrutura no laço a custo baixo.

**G**
- Mais grave: pouco sobre algoritmo.
- Mais grave: o δ de tolerância fica sem valor, e "condicional por um NÃO VERIFICÁVEL" pode travar tudo enquanto o CAD estiver incompleto.
- Mais forte: o gabarito está modelado errado. X_FIM 350 deixa 32 mm para os pedais, contra os 25 mm de folga exigidos.
- Mais forte: procedência de cada restrição (regra, margem ou preferência) e um kit de fixação fabricável.

## 2. Ranking

RANKING: B > C > E > A > F > G > D

## 3. Divergências para o presidente

1. **Base cinemática.** D mantém o `kinlib`. A migra para o `kinematics_model`. C e E pedem conferir contra o OptimumK.
   - Minha posição: validar primeiro contra a REFERENCE (EDR-004) na v20.
   - Adotar o módulo testado do repositório e deixar o `kinlib` só como conferência cruzada. Nunca duas cinemáticas vivas.
2. **Por que não há solução.** B e D dizem formulação; C e F, ausência de nós; E, conflito de conceito.
   - Minha posição: as três causas existem.
   - Primeiro as que nenhuma busca resolve: decidir o conceito (E) e o chassi esboçar os membros do F.6.2.3.
   - Depois a reformulação (B). A fase I diagnostica qual das três domina.
3. **O que "aprovado" exige.**
   - Minha posição: um verificador independente com malha convergida (n e 2n dão o mesmo veredito, C) e geometria conservadora (raio envolvente, BRep nos finalistas, A).
   - Robustez em ±δ, com δ "a confirmar", medido no TX (G).
   - Procedência de cada restrição (G).
4. **Estrutura no laço ou só nos finalistas.** F quer no laço; D quer depois.
   - Minha posição: o vetor de carga em forma fechada entra já, porque é barato.
   - A matriz de influência entra quando existir a caixa dianteira no CAD. A FEA de casca fica só nos finalistas.
5. **Referencial e nomes vindos do CAD.** D e o GEO contam com o ponto nomeado vindo pelo STEP. A mostra que este STEP não traz geometria de construção.
   - Minha posição: antes de tudo, testar a ida e volta com corpos-datum nomeados. Se falhar, exportar por script da API.
   - Até lá, todo Z sai condicional (C).
