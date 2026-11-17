# Síntese do presidente — conselho rigoroso de 7 assentos (2026-11-17)

## Ranking (Borda, revisão anônima; com / sem o voto próprio)
| Resposta | Assento | Com | Sem |
|---|---|---|---|
| B | otimização | 40 | 36 |
| C | cético | 32 | 31 |
| A | CAD/software | 26 | 23 |
| E | cinemática | 26 | 23 |
| F | estrutura | 15 | 13 |
| G | regras/manufatura | 8 | 7 |
| D | pragmático | 0 | 0 |
B em 1º em 6 de 7 votos; D em último em 7 de 7 (motivos: mantém kinlib/avaliar sem ver o bug do aro, usa MR em 25
pontos como se convergido, cronograma "a partir de julho de 2027" incoerente com a competição, conta de tempo
contraditória). O ponto forte de D (o vazio é conflito de metas, decisão da equipe) foi absorvido pelas outras.

## Unanimidade (7/7)
- O método atual não é adequado. Causa em três camadas independentes: (1) quase-igualdades na formulação
  (LHS: 0/3000; 0/4000; 0/2000); (2) ausência de nós na caixa dianteira do CAD (vazio provado por limites com os nós
  de hoje: |Pv_x| ≤ 150 × nós do FH em X = −202); (3) conflito de conceito: "mesmo plano" × "amortecedor ≤ 30° de X"
  (eixo que zera a carga axial a 74° do da v20; assento 1, código, kinlib não validado).
- A v20 não é aprovável: MR var. ≈ 6,1 % convergido (limite 4 %); curso 61,00/61 mm; ±0,5–1 mm de tolerância
  derrubam ~50 % das amostras; tubo Q–E sem nó nas pontas (E no ar), 145–393 MPa por kN de carga na roda.
- Arquitetura: gerador (busca) separado de certificador independente; só o certificador aprova.

## Decisões do presidente sobre as divergências
1. Cinemática: comparar kinlib × `kinematics_model.Corner` × OptimumKinematics (REFERENCE, EDR-004) na v20; depois
   usar o módulo testado do repositório; kinlib só como conferência cruzada. Nunca duas cinemáticas vivas.
2. Causa do vazio: as três somam; a fase I contra o CAD atual + tubos-fantasma obrigatórios (F.6.2.3) separa-as.
3. Estrutura: vetores de carga em forma fechada no laço já; σ e Ke (pórtico linear / matriz de influência) como
   restrição dura quando existir o envelope de cargas do T11; FEA só nos finalistas; distância ao nó só no relatório.
4. Robustez: restrição dura no certificador, δ "a medir" (TX contra o CAD); margem de curso do amortecedor já.
5. Cápsula de tubo quadrado: meia-diagonal + 0,2 mm na busca; BRep exato no certificador (meia largura proibida:
   superestima a folga em até 5,18 mm, medido).
6. Conceito do rocker/amortecedor: decisão da equipe; o script enumera os conceitos e mostra a carga fora do plano.
7. Referencial: testar a ida e volta Fusion → STEP com corpos-datum nomeados; se falhar, exportar por API. Até lá
   todo Z é condicional.
8. Gabarito: altura livre (T.1.2.2c), X da coluna até 100 mm atrás do pedal; NÃO VERIFICÁVEL sem pedal/coluna no CAD.

## Fica com o usuário / a equipe
- Limites em conflito (MR 1,40 com var. ≤ 4 % × curso inteiro do DNM × fixação amarrada ao FH): qual relaxar.
- Conceito do amortecedor (transversal/sobre o chassi como no TX × longitudinal com carga axial no pivô).
- Onde o código vive (repositório Sistema_DDS com EDR e IDs autorizados × script separado).
- Dados: envelope de cargas do T11, ride rate, δ de fabricação, X da face do pedal, curso da cremalheira e batentes,
  envelope de manga/pinça/disco, catálogo de amortecedores.
