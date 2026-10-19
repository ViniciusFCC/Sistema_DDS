# Registro de versões — Sistema_DDS — V3.0 (revisão metodológica contra a literatura)

Data: 2026-10-19. Motivo: o usuário pediu que as fórmulas e métodos seguissem a literatura,
principalmente o Milliken, e autorizou todas as propostas da revisão
(`docs/revisao-metodologica.md`, P-01 a P-07). Decisões: EDR-045 a EDR-049; EDR-026 aprovado.

**Numeração (usuário, 2026-10-19):** o trabalho que começou com a revisão metodológica é a
**V3.0**, e não V2.5. A V3.0 fica em desenvolvimento até terminar a implementação das
correções vindas de feedback. A revisão metodológica abriu a V3.0; as rodadas de feedback contam à parte
(usuário, 2026-10-19): a 1ª rodada de feedback é a da equipe, seção abaixo. Os nomes
"V2.5" que aparecem nos títulos dos PRs #5 e #6 e nas mensagens de commit anteriores a esta
troca se referem a esta mesma versão.

## Mapa V2.4 → V3.0

| Anterior | V3.0 | Mudança |
|---|---|---|
| `FSAE_EV_Suspension_Fase1_V2_4.xlsx` | `FSAE_EV_Suspension_Fase1_V3_0.xlsx` | Gerada da V2.4 por `python/atualizar_planilha.py` (openpyxl, sem recálculo nem gravação pelo Excel). 356 fórmulas (347 + 9 novas). Lista célula a célula abaixo. A V2.4 fica em `excel/` como histórico. |
| `suspension_model` V2.1 | V3.0 | Pneu em série (`ride_rate`, `wheel_rate_from_ride_rate`, `roll_stiffness_axle(..., k_tire)`, `arb_required`); `natural_frequency` recebe a ride rate; `wheel_rate_from_target_frequency(f, m, k_tire)`; massa suspensa por eixo (`sprung_mass_axle`, `sprung_cg_to_front`); `lateral_dfz` com termo gravitacional e CG suspenso em a_s (devolve também `a_s`, `h2`, `roll_angle_rad`); bloqueio de instabilidade de rolagem. |
| `tire_model` V2.4 | V3.0 | Ky com um único λFz0 (EDR-049). |
| `kinematics_model` | idem | `REACTION_POINT` do carro (EDR-048); funções do método V1 do SUS-406 marcadas como legado. |
| — | `python/atualizar_planilha.py` | Novo: gera a V3.0 e o registro de alterações. |
| — | `tests/test_workbook_suspensao.py` | Novo: Excel × Python das abas de suspensão (TC-WB30-001..009). |
| `tests/test_workbook.py` | idem | Passa a testar a V3.0 (10_TIRE); TC-WB24-001/002 aceitam só as células da lista de alterações. |
| testes de suspensão, pneu, oráculos, cinemática e mutação | idem | Identidades atualizadas (TC-005, TC-007, TC-008, TC-010, piloto, TC-SUS-V2-004, TC-TIRE-ORC-004) e oráculos da literatura (TC-SUS-V30-001..011, TC-KIN-119, mutante "LFZO extra em Ky"). |
| `tools/rodar_testes.py`, `tools/comparar_planilhas.py` | idem | Contagens novas; CA-07 também regenera a V3.0 e compara com a entregue (356 fórmulas, 0 diferença); CA-09 roda os dois testes de planilha. |
| Engineering Standard V2.0 | com nota V3.0 | Fichas SUS-009, 103, 205-208, 301, 302, 406 atualizadas; novas SUS-211 (K_T) e SUS-212 (ride rate). |
| `Engineering_Decision_Register.md` | idem | EDR-045 a EDR-049 (VERIFIED); EDR-026 APPROVED_WITH_CONDITIONS. |

## Resultados de código (2026-10-19, `tools/rodar_testes.py`)

- Pneu 43/43, oráculos 5/5, suspensão 54/54, cinemática 54/54, hardpoints 35/35, mutação 24/24.
- Planilha: V2.4 regenerada com 347 fórmulas e 0 diferença; V3.0 regenerada com 356 fórmulas e 0 diferença.
- `test_workbook` 19/19 (V3.0, pneu) e `test_workbook_suspensao` 9/9 (V3.0, suspensão), pelo Excel via COM.
- 1ª rodada de feedback (2026-10-19): suíte inteira PASS; V3.0 regenerada com 362 fórmulas e 0 diferença; `test_workbook_suspensao` 13/13 (TC-WB30-010 a 013 novos) pelo Excel via COM e pelo LibreOffice (`DDS_RECALC=libreoffice`); `test_workbook` 19/19.
- Exemplos publicados reproduzidos pelo modelo: Milliken p. 683 (590,8/483,4 lb/g e −2,0 °/g), p. 592 (barra 19 904 lb·ft/rad; K_W 476/254 lb/in), Tab. 16.3 e p. 602-603 (massas e h_s); Seward Ex. 4.1; Gillespie p. 154.

## Efeito nos valores da planilha (recalculada pelo Excel; entradas DEMONSTRATIVAS)

| Grandeza | Célula | V2.4 | V3.0 |
|---|---|---|---|
| K_φF [N·m/rad] | 06_SUSPENSION!B22 | 18 149,7 | 15 316,0 |
| K_φR [N·m/rad] | 06_SUSPENSION!B23 | 14 887,5 | 12 909,8 |
| λ_f | 06_SUSPENSION!B24 | 0,5494 | 0,5426 |
| massa suspensa por canto F [kg] | 06_SUSPENSION!B28 | 68,649 | 69,140 |
| f_n F / R [Hz] | 06_SUSPENSION!B32/B33 | 2,438 / 2,526 | 2,282 / 2,361 |
| anti-dive [%] | 06_SUSPENSION!B40 | 24,29 | 24,29 (mesmo IC placeholder, agora com sinal) |
| anti-squat [%] | 06_SUSPENSION!B41 | 63,25 | −1,01 (linha pelo centro da roda; IC placeholder) |
| ΔFz lateral F / R [N] | 09_LOADS!B19/B20 | 454,6 / 466,6 | 459,1 / 476,5 |
| φ [rad] | 09_LOADS!B21 | — | 0,0282 (1,62°) |
| Fz FL / FR / RL / RR [N] | 09_LOADS!B31:B34 | 543,6 / 1452,8 / 287,6 / 1220,9 | 539,1 / 1457,3 / 277,7 / 1230,7 |
| spring rate necessário F [N/m] | 11_DESIGN!B10 | 52 468,7 | 61 574,9 |
| K_ARB necessário F [N·m/rad] | 11_DESIGN!B20 | 5 058,5 | 5 665,7 |

Os números de 07_KINEMATICS (IC lateral) continuam PLACEHOLDER e o K_T é do .tir
PROVISÓRIO: nada desta tabela é resultado do carro.

## Limites

1. K_T (SUS-211) vem do .tir TTC provisório. Trocar pelo pneu real muda frequência e rigidez de rolagem.
2. Os ICs de 07_KINEMATICS e a altura do centro da roda traseira (B14 = SUS-011) são placeholders: o anti-squat negativo da tabela não diz nada sobre o carro.
3. Continua tudo NOT_VALIDATED fisicamente: a referência é o OptimumKinematics/OptimumTire e medição (EDR-004).
4. Frenagem regenerativa (motor no chassi) e anti-lift traseiro: escopo no EDR-033, sem decisão.

## 1ª rodada de feedback: feedback da equipe (recebido em 2026-10-14; decisões em 2026-10-19)

Feedback de quem vai preencher a planilha, sobre a versão que a equipe recebeu. Cada item foi conferido na própria V3.0
(as 124 constantes numéricas, a legenda e os 49 comentários). Decisões: EDR-025 (opção A), EDR-035 (parte de proveniência),
EDR-050 e EDR-051; testes novos TC-WB30-010 a 013 (IDs autorizados pelo usuário em 2026-10-19).

| Item | Feedback (resumo) | Classe | Evidência na planilha | Decisão | Implementação e teste |
|---|---|---|---|---|---|
| FB-01 | A convenção adotada dá para entender bem | confirmação | — | sem ação | — |
| FB-02 | As cores podem melhorar; o amarelo aparece escrito em azul | apresentação | `00_README!A20` ("■ Amarelo") em fonte azul e sem fundo; as amostras A18/A19 também sem o fundo que descrevem; 22 células com fundo amarelo e fonte azul (já assim na V2.4) | legenda com o estilo real das células; o fundo amarelo "hipótese-chave" sai da planilha e fica o código de papel da V2.4 (azul, verde-teal, laranja, cinza) (usuário, 2026-10-19) | 00_README A16:B20; fundo removido das 22 células (lista abaixo). TC-WB30-011 |
| FB-03 | Separar o que é certo do que é estimado, com a fonte (projeto passado ou não) | apresentação / proveniência | origem só nos comentários (aparecem ao passar o mouse); entradas sem comentário (06 B37, 08 inteira, metas da 11) | coluna Origem com lista de 6 rótulos e símbolo, coluna Fonte visível, cor só na Origem, aviso de origem desatualizada; sem estado novo (EDR-035; EDR-025 = A). Rótulos ajustados pelo usuário: "Hipótese" e "Estimativa" fundidos; "Dado do T09" no lugar de "Outro carro". Desenho discutido por um conselho de quatro lentes | colunas E/F (G/H ocultas) em 05, 06, 07, 08, 11; I/J na 10_TIRE; nome definido `Origens`; formatação condicional; comentários migrados para a Fonte. TC-WB30-010, 011, 012 |
| FB-04 | Mostrar o que está bom e o que está ruim, "como falaram do projeto passado" | escopo novo, ambíguo | — | **PENDING_CONFIRMATION** (usuário, 2026-10-19: "deixe pendente por enquanto"). Leituras possíveis: parecer de cada resultado contra uma meta (as metas da 03_TARGETS estão TBD) ou aba com o retorno que o projeto passado recebeu | não implementado |
| FB-05 | Números calculados que estão digitados, e não como fórmula | rastreabilidade de entrada / fórmula | 05 B4 (248,5 + 68), B9/B10 (L × fração medida, digitados arredondados), B16/B17 (20,0 in / 2), 08 B5 (1,2 g × 9,81) | regra do usuário: com todas as parcelas na planilha, a célula referencia as células; com parcela externa, a parcela vira entrada e a célula vira a conta (EDR-050). Molas, referências do Python (13_VALIDATION B37:B39) e caso VERIF da 10_TIRE ficam como valor, de propósito | 05 B30:B34 e 08 B11 (entradas novas); 05 B4, B9, B10, B16, B17 e 08 B5 (fórmulas). TC-WB30-013; TC-WB30-002/005/006 adaptados |
| FB-06 | O que está no PDF deveria estar na planilha | apresentação | nenhuma orientação de preenchimento na planilha | guia "Como preencher" na 00_README | 00_README A39:E52 |

**Fonte de verdade (EDR-051, decisão do usuário):** enquanto a V3.0 estiver em desenvolvimento, a planilha entregue é
saída do `atualizar_planilha.py` e não é preenchida pela equipe (aviso no item 5 do guia). Ao fechar a V3.0, ela vira o
arquivo vivo da equipe; como o CA-07 trata esse arquivo fica para aprovação no fechamento.

**Efeito numérico:** só o arredondamento antigo de a e b (a digitado 0,82203 m; a conta dá 0,8220258 m). Pelo modelo,
Fz por canto muda no máximo 0,005 N e a massa suspensa por canto dianteira passa de 69,14006 para 69,14048 kg. Nenhuma
outra fórmula existente mudou: a 1ª rodada de feedback acrescenta 6 fórmulas (356 → 362).

**Limites da 1ª rodada de feedback:**
1. O aviso de origem desatualizada só percebe valor mudado com a origem igual; não impede que alguém marque "Dado do TX" num valor estimado. A regra "Dado do TX sem fonte" só reduz esse risco.
2. Lista suspensa e cores conferidas no Excel desktop (COM: a lista `=Origens` e as cores exibidas batem). Não conferidas no Excel web, no LibreOffice nem no Google Sheets. Colar valores por cima de uma célula pode contornar a lista (comportamento do Excel; não testado aqui).
3. Na 10_TIRE (casos de carga e coeficientes) há lista e cores, mas não os avisos de origem desatualizada e de fonte faltando (cinco valores por linha); o guia diz isso.
4. 05_VEHICLE B16/B17 viraram fórmula do diâmetro do pneu (◐ Dado do T09); a estimativa "raio do pneu ≈ altura do CG não suspenso" fica dita na Fonte dessas células, não na lista.
5. "○ Estimativa" e "○ Arbitrário / demonstrativo" têm o mesmo símbolo e a mesma cor (as duas são tier T1, "não é dado do veículo"); o rótulo distingue.
6. Fase 2 do FB-03 (pior origem calculada ao vivo nos resultados principais do dashboard) não foi feita: cria fórmulas novas e precisa de aprovação.
7. A 07_KINEMATICS continua inteira placeholder (aviso já existente em A3/A4 e em B69 "Hardpoints reais carregados: NÃO"); os hardpoints ficam em `data/`, fora da coluna de origem.

## 2ª rodada de feedback (decisões do usuário em 2026-10-19)

Pendências herdadas da 1ª rodada de feedback e ressalvas da revisão metodológica. O usuário escolheu a ordem de trabalho
("siga a ordem mais lógica"); esta seção registra o que já foi decidido e implementado. O resto continua listado no fim.

| Item | Pendência | Decisão (usuário, 2026-10-19) | Implementação e teste |
|---|---|---|---|
| 1 (FB-04) | "Mostrar o que está bom e o que está ruim" | Continua **PENDING_CONFIRMATION**. A equipe não tem o retorno do projeto passado (talvez o obtenha). Direção indicada pelo usuário: formatação condicional na cor da fonte dos resultados calculados, marcando os que estão perto da meta e os que contribuem para ela. Depende de metas com fonte na 03_TARGETS (hoje TBD); nenhum limite é inventado | não implementado |
| 4 | 05 B16/B17: a hipótese "CG não suspenso ≈ raio do pneu" só aparecia na Fonte | "Vamos seguir a metodologia estabelecida" (EDR-050): a hipótese vira entrada. Aprovada a tabela: B35/B36 novas, B16, B17 e 07 B14 (usuário: "Aprovo os dois"). Achado na investigação: 07 B14 (centro da roda traseira, anti-squat) apontava para 05 B17 (CG não suspenso), duas grandezas na mesma célula; a 07 B14 passa a usar o raio direto | 05 B35/B36 (razão h_ns/raio = 1, ○ Estimativa; Milliken p. 672, conferida na imagem); B16 = B33·0,0254/2·B35; B17 = B34·0,0254/2·B36; 07 B14 = B34·0,0254/2. EDR-050 estendido; Standard SUS-010/011. TC-WB30-013 estendido (razão 0,8/0,9 move B16/B17 e não move 07 B14) e TC-WB30-005 com a razão perturbada |
| 2 (FB-03, fase 2) | Pior origem ao vivo nos resultados principais do 14_DASHBOARD | Primeiro passo pedido pelo usuário: refazer o mapa de raízes. As fórmulas do dashboard dependem de aprovação | `tools/mapa_raizes.py` (novo) gera `data/placeholder-dependency-map-V3.0.csv` das fórmulas e da coluna Origem atuais: 362 fórmulas; referência que o parser não reconhece interrompe a geração; coluna inteira (COUNTIF de IDs) é registrada, não vira raiz. Diferenças de tier contra o mapa V2.1 nas 84 fórmulas comuns (22), todas explicadas: 09_LOADS B4:B9 (T3 → T1: a massa total agora separa o piloto de 68 kg, ○ Estimativa, 05 B31); 09 B12:B15 e B23:B28 (T2 → T1: caso de carga sem fonte é ○ Estimativa, tier T1 pela regra de fusão do EDR-035, mais o piloto); 09 B18 (T2 → T1: z_s em a_s depende das massas não suspensas arbitrárias, EDR-047); 14_DASHBOARD B4 e B27:B30 (T3 → sem origem: são texto de setup e contagens de registro, não grandeza física) |
| 5 | EDR-035, N/A e TBD sem decisão | Aprovadas as definições (usuário: "Aprovo os dois"): N/A = não se aplica ou não dá para calcular na configuração atual; TBD = dado, meta, requisito ou decisão pendente (Lifecycle OPEN). Sem estado novo | item 7 do guia "Como preencher" (00_README A53); EDR-035; nota no Standard. Auditoria dos usos: todos coerentes, menos 01_SETUP B10 "N/A (Fase 2)", que pelo significado é TBD (como a Geometry REV em 07 B68): trocado para "TBD (Fase 2)" (aprovado pelo usuário) |

**Efeito numérico:** nenhum. A razão é 1, então B16, B17 e 07 B14 mantêm 0,254 m; o número de fórmulas continua 362
(três trocam de fórmula, B35/B36 são valores).

**Resultados de código (2026-10-19, `tools/rodar_testes.py`):** suíte inteira PASS; V3.0 regenerada com 362 fórmulas e
0 diferença; `test_workbook_suspensao` 13/13 e `test_workbook` 19/19 pelo Excel via COM. Não rodado pelo LibreOffice nesta rodada.

**Documentos recebidos (2026-10-19), guardados em `references/` (fora do Git):** help do OptimumKinematics (101 p.; mesma
contagem e estrutura do help oficial publicado, versão 2.0.2 de 2019-05-20; não comparado página a página); help do OptimumT
1.0.14 (2011; é o publicado no site da OptimumG, mas o programa atual é o OptimumTire 2, sem documentação equivalente
recebida); pacote do fórum do TTC, Round 6, Hoosier R25B 20.5x7-13 em aro de 7 in, quatro `.tir` PAC2002 (8, 10, 12 e 14 psi).
O `.tir` de 12 psi tem todos os coeficientes iguais aos do `data/Hoosier_R25B_13x7_TTC_provisional.tir`: a origem do
arquivo provisório fica confirmada em primeira mão. A equipe usa o R60A, não o R25B: o pneu do carro continua sem arquivo.

**Limites da 2ª rodada (até aqui):**
1. A razão h_ns / raio e a altura do centro da roda usam o raio sem carga (diâmetro / 2). O Milliken usa o raio carregado; a diferença é a deflexão estática do pneu (Fz / K_T), não modelada.
2. O mapa V3.0 é estático: reflete as fórmulas no momento da geração. A ordem de "pior origem" dentro do mesmo tier (Arbitrário antes de Estimativa; Provisório (.tir TTC) antes de Dado do T09) e "? A confirmar" como a pior de todas são proposta, não decisão. O mapa V2.1 fica como registro da auditoria (e continua usado pelo TC-WB30-010).

## Alterações célula a célula (gerado por `python/atualizar_planilha.py --registro`)

| Aba | Célula | Antes | Depois | Fonte / EDR |
|---|---|---|---|---|
| 05_VEHICLE | A25 | (vazia) | Massa suspensa - eixo dianteiro (m·b/L − m_uF) | EDR-047 |
| 05_VEHICLE | B25 | (vazia) | `='05_VEHICLE'!$B$4*'05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6-'05_VEHICLE'!$B$14` | EDR-047; Milliken p. 601-603; Seward eq. 5.14 |
| 05_VEHICLE | C25 | (vazia) | kg | EDR-047 |
| 05_VEHICLE | D25 | (vazia) | SUS-009 | EDR-047 |
| 05_VEHICLE | A26 | (vazia) | Massa suspensa - eixo traseiro (m·a/L − m_uR) | EDR-047 |
| 05_VEHICLE | B26 | (vazia) | `='05_VEHICLE'!$B$4*'05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6-'05_VEHICLE'!$B$15` | EDR-047; Milliken p. 601-603; Seward eq. 5.14 |
| 05_VEHICLE | C26 | (vazia) | kg | EDR-047 |
| 05_VEHICLE | D26 | (vazia) | SUS-009 | EDR-047 |
| 05_VEHICLE | A27 | (vazia) | CG suspenso -> eixo dianteiro (a_s = L·m_s,R/m_s) | EDR-047 |
| 05_VEHICLE | B27 | (vazia) | `='05_VEHICLE'!$B$6*'05_VEHICLE'!$B$26/'05_VEHICLE'!$B$23` | EDR-047; Milliken p. 601-603; Seward eq. 5.14 |
| 05_VEHICLE | C27 | (vazia) | m | EDR-047 |
| 05_VEHICLE | D27 | (vazia) | SUS-009 | EDR-047 |
| 06_SUSPENSION | A2 | (vazia) | Mola, MR, barra e roll center (B4:B15): valores DEMONSTRATIVOS herdados do T09/E03, para referência e teste das fórmulas; não são o TX/E05 (EDR-012/022). | EDR-012/022 |
| 06_SUSPENSION | A46 | (vazia) | Pneu em série e ride rate (EDR-045) — K_T PROVISÓRIO: rigidez vertical do .tir TTC, não é o pneu do carro | EDR-045 |
| 06_SUSPENSION | A47 | (vazia) | Rigidez vertical do pneu - dianteiro (K_T) | EDR-045 |
| 06_SUSPENSION | B47 | (vazia) | 120312.0 | EDR-045 (valor: .tir provisório, EDR-038) |
| 06_SUSPENSION | C47 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D47 | (vazia) | SUS-211 | EDR-045 |
| 06_SUSPENSION | A48 | (vazia) | Rigidez vertical do pneu - traseiro (K_T) | EDR-045 |
| 06_SUSPENSION | B48 | (vazia) | 120312.0 | EDR-045 (valor: .tir provisório, EDR-038) |
| 06_SUSPENSION | C48 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D48 | (vazia) | SUS-211 | EDR-045 |
| 06_SUSPENSION | A49 | (vazia) | Ride rate dianteiro K_R = K_W·K_T/(K_W+K_T) | EDR-045 |
| 06_SUSPENSION | B49 | (vazia) | `='06_SUSPENSION'!$B$18*'06_SUSPENSION'!$B$47/('06_SUSPENSION'!$B$18+'06_SUSPENSION'!$B$47)` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C49 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D49 | (vazia) | SUS-212 | EDR-045 |
| 06_SUSPENSION | A50 | (vazia) | Ride rate traseiro K_R = K_W·K_T/(K_W+K_T) | EDR-045 |
| 06_SUSPENSION | B50 | (vazia) | `='06_SUSPENSION'!$B$19*'06_SUSPENSION'!$B$48/('06_SUSPENSION'!$B$19+'06_SUSPENSION'!$B$48)` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C50 | (vazia) | N/m | EDR-045 |
| 06_SUSPENSION | D50 | (vazia) | SUS-212 | EDR-045 |
| 06_SUSPENSION | A51 | (vazia) | Rigidez de rolagem do par de pneus - dianteira (K_T·t_F²/2) | EDR-045 |
| 06_SUSPENSION | B51 | (vazia) | `='06_SUSPENSION'!$B$47*'05_VEHICLE'!$B$7^2/2` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C51 | (vazia) | N*m/rad | EDR-045 |
| 06_SUSPENSION | D51 | (vazia) | SUS-206 | EDR-045 |
| 06_SUSPENSION | A52 | (vazia) | Rigidez de rolagem do par de pneus - traseira (K_T·t_R²/2) | EDR-045 |
| 06_SUSPENSION | B52 | (vazia) | `='06_SUSPENSION'!$B$48*'05_VEHICLE'!$B$8^2/2` | EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5 |
| 06_SUSPENSION | C52 | (vazia) | N*m/rad | EDR-045 |
| 06_SUSPENSION | D52 | (vazia) | SUS-207 | EDR-045 |
| 06_SUSPENSION | A20 | Roll Stiffness sem ARB - dianteira | Roll Stiffness sem ARB e sem pneu (K_W·t_F²/2) - dianteira | EDR-045 |
| 06_SUSPENSION | A21 | Roll Stiffness sem ARB - traseira | Roll Stiffness sem ARB e sem pneu (K_W·t_R²/2) - traseira | EDR-045 |
| 06_SUSPENSION | A22 | Roll Stiffness dianteira (K_phiF) | Roll Stiffness dianteira K_phiF = (K_W·t²/2 + K_ARB) em série com K_T·t²/2 | EDR-045 |
| 06_SUSPENSION | B22 | `='06_SUSPENSION'!$B$20+'06_SUSPENSION'!$B$10` | `=1/(1/('06_SUSPENSION'!$B$20+'06_SUSPENSION'!$B$10)+1/'06_SUSPENSION'!$B$51)` | EDR-045; Milliken p. 592 e p. 680 |
| 06_SUSPENSION | A23 | Roll Stiffness traseira (K_phiR) | Roll Stiffness traseira K_phiR = (K_W·t²/2 + K_ARB) em série com K_T·t²/2 | EDR-045 |
| 06_SUSPENSION | B23 | `='06_SUSPENSION'!$B$21+'06_SUSPENSION'!$B$11` | `=1/(1/('06_SUSPENSION'!$B$21+'06_SUSPENSION'!$B$11)+1/'06_SUSPENSION'!$B$52)` | EDR-045; Milliken p. 592 e p. 680 |
| 06_SUSPENSION | A27 | Massa suspensa por canto (SUS-009, distribuição) | Massa suspensa por canto (SUS-009, por eixo: (m·b/L − m_uF)/2 e (m·a/L − m_uR)/2) | EDR-047 |
| 06_SUSPENSION | B28 | `='05_VEHICLE'!$B$23*('05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6)/2` | `='05_VEHICLE'!$B$25/2` | EDR-047; Milliken p. 601, Tab. 16.3 |
| 06_SUSPENSION | B29 | `='05_VEHICLE'!$B$23*('05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6)/2` | `='05_VEHICLE'!$B$26/2` | EDR-047; Milliken p. 601, Tab. 16.3 |
| 06_SUSPENSION | A31 | Frequência Natural (SUS-205) | Frequência Natural (SUS-205) — com a ride rate (pneu em série) | EDR-045 |
| 06_SUSPENSION | B32 | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$18/'06_SUSPENSION'!$B$28)` | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$49/'06_SUSPENSION'!$B$28)` | EDR-045; Gillespie eq. 5-9; Seward eq. 4.2 |
| 06_SUSPENSION | B33 | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$19/'06_SUSPENSION'!$B$29)` | `=(1/(2*PI()))*SQRT('06_SUSPENSION'!$B$50/'06_SUSPENSION'!$B$29)` | EDR-045; Gillespie eq. 5-9; Seward eq. 4.2 |
| 06_SUSPENSION | A34 | Anti-Dive / Anti-Squat (SUS-301/302) — Lifecycle: DRAFT->CHECKED | Anti-Dive / Anti-Squat (SUS-301/302) — com sinal (EDR-026/048) | EDR-048 |
| 06_SUSPENSION | A35 | Metodologia FROZEN (Milliken); linha geométrica (contact patch vs. wheel center) pendente de confirmação com a config. real de freio/trem de força. | Milliken p. 618-619: freio no cubo (outboard) -> linha pelo contact patch; motor no chassi com semieixos -> linha pelo centro da roda (Fig. 17.15b). + = anti, − = pro (p. 620). IC de 07_KINEMATICS ainda é PLACEHOLDER. | EDR-048 |
| 06_SUSPENSION | A38 | tan(phi_f) — dianteiro (a partir do IC lateral) | Inclinação dz/dx da linha contact patch -> IC lateral dianteiro (com sinal; freio no cubo) | EDR-048 |
| 06_SUSPENSION | A39 | tan(phi_r) — traseiro (a partir do IC lateral) | Inclinação dz/dx da linha centro da roda -> IC lateral traseiro (com sinal; motor no chassi) | EDR-048 |
| 06_SUSPENSION | B39 | `='07_KINEMATICS'!$B$12/'07_KINEMATICS'!$B$13` | `=('07_KINEMATICS'!$B$12-'07_KINEMATICS'!$B$14)/'07_KINEMATICS'!$B$13` | EDR-048; Milliken Fig. 17.15(b); Gillespie eq. 7-19 |
| 06_SUSPENSION | A40 | Anti-Dive (%) | Anti-Dive (%) = FB_f·(−dz/dx)·L/h·100 (+ = anti, − = pro-dive) | EDR-048 |
| 06_SUSPENSION | B40 | `='06_SUSPENSION'!$B$36*'06_SUSPENSION'!$B$38*('05_VEHICLE'!$B$6/'05_VEHICLE'!$B$5)*100` | `='06_SUSPENSION'!$B$36*(-'06_SUSPENSION'!$B$38)*('05_VEHICLE'!$B$6/'05_VEHICLE'!$B$5)*100` | EDR-048; Milliken p. 618 |
| 06_SUSPENSION | A41 | Anti-Squat (%) | Anti-Squat (%) = TF_r·(dz/dx)·L/h·100 (+ = anti, − = pro-squat) | EDR-048 |
| 07_KINEMATICS | A11 | Distância contact patch->IC, dianteiro (vista lateral) | Δx do IC lateral dianteiro ao contact patch (x_IC − x_CP; ISO: + = à frente) | EDR-048 |
| 07_KINEMATICS | B11 | 2.5 | -2.5 | EDR-048: mesmo PLACEHOLDER (2,5 m), agora com sinal: IC atrás do contact patch (Milliken p. 617) |
| 07_KINEMATICS | A13 | Distância contact patch->IC, traseiro (vista lateral) | Δx do IC lateral traseiro ao centro da roda (x_IC − x_WC; ISO: + = à frente) | EDR-048 |
| 07_KINEMATICS | A14 | (vazia) | Altura do centro da roda traseira (ponto de reação do anti-squat) | EDR-048 |
| 07_KINEMATICS | B14 | (vazia) | `='05_VEHICLE'!$B$17` | EDR-048: PLACEHOLDER = SUS-011 (aproximado pela altura do centro da roda) |
| 07_KINEMATICS | C14 | (vazia) | m | EDR-048 |
| 07_KINEMATICS | D14 | (vazia) | SUS-406-R | EDR-048 |
| 09_LOADS | A17 | Transferência Lateral — Milliken two-spring (SUS-103) | Transferência Lateral — Milliken, três massas, com termo gravitacional (SUS-103) | EDR-046 |
| 09_LOADS | A18 | Altura do roll axis no CG (z_s) | Altura do roll axis no CG suspenso (z_s, em a_s) | EDR-047 |
| 09_LOADS | B18 | `=('05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6)*'06_SUSPENSION'!$B$14+('05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6)*'06_SUSPENSION'!$B$15` | `='06_SUSPENSION'!$B$14+('06_SUSPENSION'!$B$15-'06_SUSPENSION'!$B$14)*'05_VEHICLE'!$B$27/'05_VEHICLE'!$B$6` | EDR-047; Milliken p. 603 |
| 09_LOADS | B19 | `=('08_VEHICLE_STATE'!$B$5/'05_VEHICLE'!$B$7)*('06_SUSPENSION'!$B$24*'05_VEHICLE'!$B$23*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)+('05_VEHICLE'!$B$10/'05_VEHICLE'!$B$6)*'05_VEHICLE'!$B$23*'06_SUSPENSION'!$B$14+'05_VEHICLE'!$B$14*'05_VEHICLE'!$B$16)` | `=IF(ISNUMBER('09_LOADS'!$B$21),('06_SUSPENSION'!$B$22*'09_LOADS'!$B$21+'08_VEHICLE_STATE'!$B$5*('05_VEHICLE'!$B$25*'06_SUSPENSION'!$B$14+'05_VEHICLE'!$B$14*'05_VEHICLE'!$B$16))/'05_VEHICLE'!$B$7,"N/A")` | EDR-046/047; Milliken p. 604 e p. 682 |
| 09_LOADS | B20 | `=('08_VEHICLE_STATE'!$B$5/'05_VEHICLE'!$B$8)*('06_SUSPENSION'!$B$25*'05_VEHICLE'!$B$23*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)+('05_VEHICLE'!$B$9/'05_VEHICLE'!$B$6)*'05_VEHICLE'!$B$23*'06_SUSPENSION'!$B$15+'05_VEHICLE'!$B$15*'05_VEHICLE'!$B$17)` | `=IF(ISNUMBER('09_LOADS'!$B$21),('06_SUSPENSION'!$B$23*'09_LOADS'!$B$21+'08_VEHICLE_STATE'!$B$5*('05_VEHICLE'!$B$26*'06_SUSPENSION'!$B$15+'05_VEHICLE'!$B$15*'05_VEHICLE'!$B$17))/'05_VEHICLE'!$B$8,"N/A")` | EDR-046/047; Milliken p. 604 e p. 682 |
| 09_LOADS | A21 | (vazia) | Ângulo de rolagem φ = m_s·a_y·h2/(K_φF+K_φR − m_s·g·h2) (+ = para fora da curva) | EDR-046 |
| 09_LOADS | B21 | (vazia) | `=IF('06_SUSPENSION'!$B$22+'06_SUSPENSION'!$B$23-'05_VEHICLE'!$B$23*9.81*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)<=0,"N/A - instabilidade de rolagem (m_s·g·h2 >= K_φ, Milliken p. 682)",'05_VEHICLE'!$B$23*'08_VEHICLE_STATE'!$B$5*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)/('06_SUSPENSION'!$B$22+'06_SUSPENSION'!$B$23-'05_VEHICLE'!$B$23*9.81*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)))` | EDR-046; Milliken p. 682; Gillespie eq. 6-31 |
| 09_LOADS | C21 | (vazia) | rad | EDR-046 |
| 09_LOADS | D21 | (vazia) | SUS-103 | EDR-046 |
| 11_DESIGN | A7 | Rigidez necessária (equação reversa, SUS-202/205) | Rigidez necessária (equação reversa, SUS-205/212/202; pneu em série) | EDR-045 |
| 11_DESIGN | A8 | Wheel Rate necessário - dianteira | Wheel Rate necessário - dianteira (K_R alvo -> K_W = K_R·K_T/(K_T − K_R)) | EDR-045 |
| 11_DESIGN | B8 | `=(2*PI()*'11_DESIGN'!$B$4)^2*'06_SUSPENSION'!$B$28` | `=(2*PI()*'11_DESIGN'!$B$4)^2*'06_SUSPENSION'!$B$28*'06_SUSPENSION'!$B$47/('06_SUSPENSION'!$B$47-(2*PI()*'11_DESIGN'!$B$4)^2*'06_SUSPENSION'!$B$28)` | EDR-045; Milliken p. 591; Seward eq. 4.4 |
| 11_DESIGN | A9 | Wheel Rate necessário - traseira | Wheel Rate necessário - traseira (K_R alvo -> K_W = K_R·K_T/(K_T − K_R)) | EDR-045 |
| 11_DESIGN | B9 | `=(2*PI()*'11_DESIGN'!$B$5)^2*'06_SUSPENSION'!$B$29` | `=(2*PI()*'11_DESIGN'!$B$5)^2*'06_SUSPENSION'!$B$29*'06_SUSPENSION'!$B$48/('06_SUSPENSION'!$B$48-(2*PI()*'11_DESIGN'!$B$5)^2*'06_SUSPENSION'!$B$29)` | EDR-045; Milliken p. 591; Seward eq. 4.4 |
| 11_DESIGN | A20 | K_ARB dianteiro necessário | K_ARB dianteiro necessário (com o pneu em série) | EDR-045 |
| 11_DESIGN | B20 | `='11_DESIGN'!$B$19-'06_SUSPENSION'!$B$20` | `='11_DESIGN'!$B$19*'06_SUSPENSION'!$B$51/('06_SUSPENSION'!$B$51-'11_DESIGN'!$B$19)-'06_SUSPENSION'!$B$20` | EDR-045; Milliken p. 592 |
| 13_VALIDATION | A6 | TC-005: t_F*dFzF + t_R*dFzR - m*ay*h_CG [deve ser ~0] | TC-005: t_F*dFzF + t_R*dFzR - m*ay*h_CG - m_s*g*h2*φ [deve ser ~0] | EDR-046 |
| 13_VALIDATION | B6 | `='05_VEHICLE'!$B$7*'09_LOADS'!$B$19+'05_VEHICLE'!$B$8*'09_LOADS'!$B$20-'05_VEHICLE'!$B$4*'08_VEHICLE_STATE'!$B$5*'05_VEHICLE'!$B$5` | `='05_VEHICLE'!$B$7*'09_LOADS'!$B$19+'05_VEHICLE'!$B$8*'09_LOADS'!$B$20-'05_VEHICLE'!$B$4*'08_VEHICLE_STATE'!$B$5*'05_VEHICLE'!$B$5-'05_VEHICLE'!$B$23*9.81*('05_VEHICLE'!$B$24-'09_LOADS'!$B$18)*'09_LOADS'!$B$21` | EDR-046; Milliken p. 682-683 |
| 13_VALIDATION | A26 | Piloto de referência: MR=0.8, Ks=100 N/mm, ms=50 kg -> fn=8.897 Hz (verificado) | Piloto de referência: MR=0.8, Ks=100 N/mm, ms=50 kg, pneu rígido -> fn=8.897 Hz (verificado) | EDR-045 |
| 10_TIRE | A56 | Ky = PKY1·F'z0·sin(2·atan(Fz/(PKY2·F'z0)))·(1−PKY3·\|γy\|)·LFZO·LKY | Ky = PKY1·F'z0·sin(2·atan(Fz/(PKY2·F'z0)))·(1−PKY3·\|γy\|)·LKY  (um λFz0, EDR-049) | EDR-049 |
| 10_TIRE | B56 | `=IF(B$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(B$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(B$55))*$B$97*$B$108)` | `=IF(B$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(B$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(B$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | C56 | `=IF(C$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(C$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(C$55))*$B$97*$B$108)` | `=IF(C$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(C$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(C$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | D56 | `=IF(D$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(D$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(D$55))*$B$97*$B$108)` | `=IF(D$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(D$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(D$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | E56 | `=IF(E$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(E$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(E$55))*$B$97*$B$108)` | `=IF(E$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(E$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(E$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 10_TIRE | F56 | `=IF(F$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(F$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(F$55))*$B$97*$B$108)` | `=IF(F$26<>"OK","N/A",$B$144*($B$97*$B$86)*SIN(2*ATAN(F$22/($B$145*$B$97*$B$86)))*(1-$B$146*ABS(F$55))*$B$108)` | EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9 |
| 05_VEHICLE | A29 | (vazia) | Entradas de onde saem B4, B9/B10 e B16/B17 (EDR-050: valor que sai de conta não é digitado) | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | A30 | (vazia) | Massa medida sem piloto | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B30 | (vazia) | 248.5 | EDR-050 (feedback da equipe, 2026-10-14); valor: comentário da V2.4 (ver coluna F) |
| 05_VEHICLE | C30 | (vazia) | kg | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | D30 | (vazia) | SUS-001 | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | A31 | (vazia) | Massa do piloto | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B31 | (vazia) | 68 | EDR-050 (feedback da equipe, 2026-10-14); valor: comentário da V2.4 (ver coluna F) |
| 05_VEHICLE | C31 | (vazia) | kg | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | D31 | (vazia) | SUS-001 | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | A32 | (vazia) | Fração de peso no eixo dianteiro (f) | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B32 | (vazia) | 0.4843 | EDR-050 (feedback da equipe, 2026-10-14); valor: comentário da V2.4 (ver coluna F) |
| 05_VEHICLE | C32 | (vazia) | - | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | D32 | (vazia) | SUS-006 | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | A33 | (vazia) | Diâmetro do pneu dianteiro | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B33 | (vazia) | 20.0 | EDR-050 (feedback da equipe, 2026-10-14); valor: comentário da V2.4 (ver coluna F) |
| 05_VEHICLE | C33 | (vazia) | in | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | D33 | (vazia) | SUS-010 | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | A34 | (vazia) | Diâmetro do pneu traseiro | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B34 | (vazia) | 20.0 | EDR-050 (feedback da equipe, 2026-10-14); valor: comentário da V2.4 (ver coluna F) |
| 05_VEHICLE | C34 | (vazia) | in | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | D34 | (vazia) | SUS-011 | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B4 | 316.5 | `='05_VEHICLE'!$B$30+'05_VEHICLE'!$B$31` | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B9 | 0.82203 | `='05_VEHICLE'!$B$6*(1-'05_VEHICLE'!$B$32)` | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B10 | 0.77197 | `='05_VEHICLE'!$B$6*'05_VEHICLE'!$B$32` | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B16 | 0.254 | `='05_VEHICLE'!$B$33*0.0254/2` | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | B17 | 0.254 | `='05_VEHICLE'!$B$34*0.0254/2` | EDR-050 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | A10 | (vazia) | Entrada de onde sai a_y (B5) — EDR-050 | EDR-050 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | A11 | (vazia) | Aceleração lateral em g (entrada de a_y) | EDR-050 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | B11 | (vazia) | 1.2 | EDR-050 (feedback da equipe, 2026-10-14); valor: 11,772 m/s² / 9,81 |
| 08_VEHICLE_STATE | C11 | (vazia) | g | EDR-050 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | D11 | (vazia) | - | EDR-050 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | B5 | 11.772 | `='08_VEHICLE_STATE'!$B$11*9.81` | EDR-050 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | E2 | (vazia) | Origem do valor (lista) | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F2 | (vazia) | Fonte / observação | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | E2 | (vazia) | Origem do valor (lista) | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F2 | (vazia) | Fonte / observação | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | E2 | (vazia) | Origem do valor (lista) | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F2 | (vazia) | Fonte / observação | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | E2 | (vazia) | Origem do valor (lista) | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | F2 | (vazia) | Fonte / observação | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | E2 | (vazia) | Origem do valor (lista) | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | F2 | (vazia) | Fonte / observação | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F4 | (vazia) | Calculada (EDR-050): massa medida sem piloto (B30) + massa do piloto (B31). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | E5 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F5 | (vazia) | E05, Key Parameters (315 mm). Medida a partir do plano do solo (SUS-000), não da origem do CAD. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G5 | (vazia) | 0.315 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H5 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E6 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F6 | (vazia) | E05, Key Parameters (1594 mm). Diverge do E03 (1550 mm, chassi anterior). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G6 | (vazia) | 1.594 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H6 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E7 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F7 | (vazia) | E05, Key Parameters (1277 mm). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G7 | (vazia) | 1.277 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H7 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E8 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F8 | (vazia) | E05, Key Parameters (1271 mm). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G8 | (vazia) | 1.271 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H8 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | F9 | (vazia) | Calculada (EDR-050): L·(1 − f), com f = fração de peso no eixo dianteiro (B32). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F10 | (vazia) | Calculada (EDR-050): L·f, com f = fração de peso no eixo dianteiro (B32). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | E14 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F14 | (vazia) | Não disponível para o TX/E05: a pesagem em plataforma mede a carga total no solo e não separa massa suspensa de não suspensa (confirmado pela equipe). Valor arbitrário: não usar para decisão de projeto. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G14 | (vazia) | 15 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H14 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E15 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F15 | (vazia) | Não disponível para o TX/E05 (mesma razão do SUS-007). Valor arbitrário: não usar para decisão de projeto. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G15 | (vazia) | 18 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H15 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | F16 | (vazia) | Calculada (EDR-050): diâmetro do pneu (B33) × 0,0254 / 2. Estimativa: o raio do pneu aproxima a altura do CG não suspenso; não é medição da equipe. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F17 | (vazia) | Calculada (EDR-050): diâmetro do pneu (B34) × 0,0254 / 2. Estimativa: o raio do pneu aproxima a altura do CG não suspenso; não é medição da equipe. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | E20 | (vazia) | ? A confirmar | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F20 | (vazia) | SUS-000: coordenada Z do solo no sistema de coordenadas da equipe. As alturas desta planilha já são medidas a partir do solo (ficha SUS-000 do Engineering Standard). A origem do valor −0,05 m não está registrada. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G20 | (vazia) | -0.05 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H20 | (vazia) | ? A confirmar | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E30 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F30 | (vazia) | Adesivo SAE Brasil 2026: medição real, sem piloto (248,5 kg). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G30 | (vazia) | 248.5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H30 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E31 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F31 | (vazia) | Piloto de referência (68 kg, padrão FSAE); não é a massa medida do piloto. | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G31 | (vazia) | 68 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H31 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E32 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F32 | (vazia) | Distribuição medida no adesivo do TX/E05: 48,43 % no eixo dianteiro, com piloto (coerente com a massa total, que inclui o piloto). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G32 | (vazia) | 0.4843 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H32 | (vazia) | ● Dado do TX | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E33 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F33 | (vazia) | Pneu 20.0-13 do E03 (diâmetro 20,0 in). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G33 | (vazia) | 20.0 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H33 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | E34 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | F34 | (vazia) | Pneu 20.0-13 do E03 (mesmo pneu na frente e atrás). | EDR-035 (feedback da equipe, 2026-10-14) |
| 05_VEHICLE | G34 | (vazia) | 20.0 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H34 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E4 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F4 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. Calculado a partir da planilha detalhada do T09: ride rate dianteiro 16 112,23 N/m (que é o wheel rate) × MR² (MR = 1,76). Corrige o valor anterior, do spec sheet resumido, que arredondava F e R como iguais. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G4 | (vazia) | 49909.24 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H4 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E5 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F5 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. Calculado a partir da planilha detalhada do T09: ride rate traseiro 18 418,2 N/m × MR² (MR = 1,76). | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G5 | (vazia) | 57052.22 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H5 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E6 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F6 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. E03 (1,76:1). Convenção wheel/spring assumida (igual à do projeto); o E03 não diz a direção. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G6 | (vazia) | 1.76 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H6 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E7 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F7 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. E03 (1,76:1, igual à dianteira). | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G7 | (vazia) | 1.76 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H7 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E10 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F10 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. Planilha detalhada do T09 (AntiRoll Bar Rate dianteiro), valor direto. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G10 | (vazia) | 5012.32 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H10 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E11 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F11 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. Planilha detalhada do T09 (AntiRoll Bar Rate traseiro, ≈ 0, coerente com 'sem ARB'). | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G11 | (vazia) | 10.78 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H11 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E14 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F14 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. Planilha detalhada do T09 (0,0675 m), mais precisa que o spec sheet do E03 (60 mm, arredondado). Provisório até a Fase 2 (OptimumKinematics). | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G14 | (vazia) | 0.0675 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H14 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E15 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F15 | (vazia) | Demonstrativo (EDR-012/022): valor do T09/E03 para referência, comparação e teste das fórmulas (usuário, 2026-10-19); não é o TX/E05. E03 (110 mm, roll center estático acima do solo). Provisório até a Fase 2 (OptimumKinematics). | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G15 | (vazia) | 0.11 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H15 | (vazia) | ◐ Dado do T09 | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E36 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F36 | (vazia) | Placeholder: fração da força de frenagem no eixo dianteiro (brake bias). Substituir pelo balanço de freio real do Setup. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G36 | (vazia) | 0.6 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H36 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E37 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F37 | (vazia) | Hipótese congelada da V1: TF_r = 1 (tração só traseira). Revisitar se a equipe mudar para AWD. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G37 | (vazia) | 1 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H37 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E44 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F44 | (vazia) | Placeholder: razão entre o ângulo do volante e o ângulo médio das rodas dianteiras. Substituir pela medição da cremalheira ou pela geometria do rack. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G44 | (vazia) | 4.5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H44 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E47 | (vazia) | ◐ Provisório (.tir TTC) | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F47 | (vazia) | VERTICAL_STIFFNESS do .tir TTC provisório (Hoosier R25B; EDR-038, EDR-045). Não é o pneu do carro nem medição da equipe: substituir pela rigidez vertical do pneu real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G47 | (vazia) | 120312.0 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H47 | (vazia) | ◐ Provisório (.tir TTC) | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | E48 | (vazia) | ◐ Provisório (.tir TTC) | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | F48 | (vazia) | VERTICAL_STIFFNESS do .tir TTC provisório (Hoosier R25B; EDR-038, EDR-045). Não é o pneu do carro nem medição da equipe: substituir pela rigidez vertical do pneu real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 06_SUSPENSION | G48 | (vazia) | 120312.0 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 06_SUSPENSION | H48 | (vazia) | ◐ Provisório (.tir TTC) | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E10 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F10 | (vazia) | Placeholder geométrico para testar a fórmula; não é hardpoint real. Fase 2: REFERENCE do OptimumKinematics. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G10 | (vazia) | 0.2 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H10 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E11 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F11 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G11 | (vazia) | -2.5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H11 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E12 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F12 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G12 | (vazia) | 0.25 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H12 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E13 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F13 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G13 | (vazia) | 2 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H13 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | F14 | (vazia) | Calculada: = SUS-011 (05_VEHICLE B17). Placeholder: substituir pela altura do centro da roda do CAD. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | E17 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F17 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G17 | (vazia) | 1.5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H17 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E18 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F18 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G18 | (vazia) | 0.15 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H18 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E19 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F19 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G19 | (vazia) | 1.8 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H19 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E20 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F20 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G20 | (vazia) | 0.2 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H20 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E23 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F23 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G23 | (vazia) | -0.6 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H23 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E24 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F24 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G24 | (vazia) | -0.5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H24 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E27 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F27 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G27 | (vazia) | 0.05 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H27 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E28 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F28 | (vazia) | Placeholder geométrico (07_KINEMATICS inteira é placeholder até a Fase 2); não é hardpoint real. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G28 | (vazia) | 0.05 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H28 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E31 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F31 | (vazia) | Placeholder geométrico; não é a medição do curso instalado. Substituir pelo curso real (bump + rebound) com o piloto sentado, conforme V.3.1.1. | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G31 | (vazia) | 60 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H31 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | E32 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | F32 | (vazia) | Placeholder geométrico; não é a medição do curso instalado (ver B31). | EDR-035 (feedback da equipe, 2026-10-14) |
| 07_KINEMATICS | G32 | (vazia) | 65 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 07_KINEMATICS | H32 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | E4 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | F4 | (vazia) | Caso de carga sem fonte registrada. ISO 8855: a_x + = aceleração para frente (transfere carga para o eixo traseiro); negativo = frenagem. | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | G4 | (vazia) | -5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | H4 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | F5 | (vazia) | Calculada (EDR-050): a_y em g (B11) × 9,81. ISO 8855: a_y + = para a esquerda (o lado direito ganha carga). | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | E8 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | F8 | (vazia) | Caso de carga sem fonte registrada. Aero constante por Setup (SUS-701, EDR-013). | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | G8 | (vazia) | 400 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | H8 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | E9 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | F9 | (vazia) | Caso de carga sem fonte registrada. Fração dianteira da downforce (SUS-702, EDR-013). | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | G9 | (vazia) | 0.45 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | H9 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | E11 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | F11 | (vazia) | Caso de carga sem fonte registrada. Curva à esquerda de 1,2 g. | EDR-035 (feedback da equipe, 2026-10-14) |
| 08_VEHICLE_STATE | G11 | (vazia) | 1.2 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 08_VEHICLE_STATE | H11 | (vazia) | ○ Estimativa | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 11_DESIGN | E4 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | F4 | (vazia) | Alvo demonstrativo: a meta da equipe está TBD em 03_TARGETS (TARGET-001). | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | G4 | (vazia) | 2.5 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 11_DESIGN | H4 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 11_DESIGN | E5 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | F5 | (vazia) | Alvo demonstrativo: a meta da equipe está TBD em 03_TARGETS (TARGET-002). | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | G5 | (vazia) | 2.7 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 11_DESIGN | H5 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 11_DESIGN | E18 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | F18 | (vazia) | Alvo demonstrativo: a meta da equipe está TBD em 03_TARGETS (TARGET-003). | EDR-035 (feedback da equipe, 2026-10-14) |
| 11_DESIGN | G18 | (vazia) | 0.55 | EDR-035 (feedback da equipe, 2026-10-14): valor da geração (oculto; aviso de desatualização) |
| 11_DESIGN | H18 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14): origem da geração (oculto; aviso de desatualização) |
| 10_TIRE | I20 | (vazia) | Origem do valor (lista) | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | J20 | (vazia) | Fonte / observação | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | I23 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | J23 | (vazia) | Demonstrativos (EDR-022): α, γ e κ não vêm de cálculo do carro (não há modelo de slip). Valores arbitrários coerentes em sinal com 08_VEHICLE_STATE (curva à esquerda, frenagem). Substituir por casos de carga da equipe. VERIF (F): caso fixo de teste. | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | I24 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | J24 | (vazia) | Camber de entrada manual (EDR-036 sem decisão: ainda não há ID para camber estático). Convenção do projeto: + = topo para fora, nos dois lados. | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | I25 | (vazia) | ○ Arbitrário / demonstrativo | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | J25 | (vazia) | Demonstrativo (EDR-022), como α e γ. | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | I84 | (vazia) | ◐ Provisório (.tir TTC) | EDR-035 (feedback da equipe, 2026-10-14) |
| 10_TIRE | J84 | (vazia) | Todos os coeficientes da tabela abaixo (B86:B175) foram transcritos do .tir provisório (ver os metadados acima). REFERENCE por natureza (DR-011), mas o dataset é provisório. Mudou o dataset: mudar o Tire REV (01_SETUP) e reexecutar 13_VALIDATION; os resultados antigos viram STALE. | EDR-035 (feedback da equipe, 2026-10-14) |
| 00_README | A16 | ■ Azul | ■ Azul | FB-02; estilo = 05_VEHICLE B14 |
| 00_README | A17 | ■ Verde-teal | ■ Verde-teal | FB-02; estilo = 05_VEHICLE B6 |
| 00_README | A18 | ■ Laranja + fundo | ■ Laranja + fundo | FB-02; estilo = 06_SUSPENSION B14 |
| 00_README | A19 | ■ Preto + fundo cinza | ■ Preto + fundo cinza | FB-02; estilo = 05_VEHICLE B23 |
| 00_README | A20 | ■ Amarelo | Origem do valor | FB-02/EDR-035 |
| 00_README | B20 | Hipótese-chave / célula de atenção | Não é cor da célula: fica na coluna E de cada entrada (● ◐ ○ ?). Ver "Como preencher", abaixo. | FB-02/EDR-035 |
| 00_README | A39 | (vazia) | Como preencher esta planilha (EDR-035, EDR-050, EDR-051) | FB-06/EDR-035 |
| 00_README | A40 | (vazia) | 1. Edite só as entradas (fonte azul; verde-teal e laranja quando houver o dado real) das abas 05, 06, 07, 08, 10 (casos de carga) e 11 (metas). Célula com fundo cinza é calculada: não edite. | FB-06/EDR-035 |
| 00_README | A41 | (vazia) | 2. Cada entrada tem ao lado a Origem (coluna E; na 10_TIRE, coluna I) e a Fonte (coluna F; na 10_TIRE, J). Ao trocar um valor, escolha a Origem na lista e escreva na Fonte de onde veio o número. Origens possíveis: | FB-06/EDR-035 |
| 00_README | A42 | (vazia) | Origem | FB-06/EDR-035 |
| 00_README | B42 | (vazia) | Significado | FB-06/EDR-035 |
| 00_README | E42 | (vazia) | Categorias da auditoria V2.1 (data/placeholder-dependency-map-V2.1.csv) | FB-06/EDR-035 |
| 00_README | A43 | (vazia) | ● Dado do TX | FB-06/EDR-035; nome definido 'Origens' |
| 00_README | B43 | (vazia) | Medido no carro atual ou tirado de documento do TX/E05 (ex.: Key Parameters). | FB-06/EDR-035 |
| 00_README | E43 | (vazia) | T3_FONTE_TX_REGISTRADA (T3) | FB-06/EDR-035 |
| 00_README | A44 | (vazia) | ◐ Dado do T09 | FB-06/EDR-035; nome definido 'Origens' |
| 00_README | B44 | (vazia) | Valor do carro anterior (T09/E03): serve para testar as fórmulas, não é o TX. | FB-06/EDR-035 |
| 00_README | E44 | (vazia) | REAL_OUTRO_VEICULO_T09/E03 (T2) | FB-06/EDR-035 |
| 00_README | A45 | (vazia) | ◐ Provisório (.tir TTC) | FB-06/EDR-035; nome definido 'Origens' |
| 00_README | B45 | (vazia) | Vem do arquivo de pneu provisório do TTC; não é o pneu do carro. | FB-06/EDR-035 |
| 00_README | E45 | (vazia) | REAL_OUTRO_VEICULO_PROVISORIO (T2) | FB-06/EDR-035 |
| 00_README | A46 | (vazia) | ○ Estimativa | FB-06/EDR-035; nome definido 'Origens' |
| 00_README | B46 | (vazia) | Estimado ou suposto: inclui hipótese de modelo e caso de carga sem fonte. | FB-06/EDR-035 |
| 00_README | E46 | (vazia) | ESTIMATIVA_NAO_MEDIDA (T1), HIPOTESE_CONGELADA_V1 e CASO_DE_CARGA_SEM_PROVENIENCIA (T2); vale a pior, T1 | FB-06/EDR-035 |
| 00_README | A47 | (vazia) | ○ Arbitrário / demonstrativo | FB-06/EDR-035; nome definido 'Origens' |
| 00_README | B47 | (vazia) | Placeholder, valor arbitrário ou meta de exemplo: não usar para decisão de projeto. | FB-06/EDR-035 |
| 00_README | E47 | (vazia) | ARBITRARIO, PLACEHOLDER, ALVO_DEMONSTRATIVO (T1) | FB-06/EDR-035 |
| 00_README | A48 | (vazia) | ? A confirmar | FB-06/EDR-035; nome definido 'Origens' |
| 00_README | B48 | (vazia) | A origem do valor não está registrada. | FB-06/EDR-035 |
| 00_README | E48 | (vazia) | sem classificação | FB-06/EDR-035 |
| 00_README | A49 | (vazia) | 3. Avisos: Origem com fundo vermelho-alaranjado = o valor mudou e a Origem continuou a mesma (revise a Origem). Fonte com fundo vermelho = a Origem diz "Dado do TX" e falta a Fonte. Na 10_TIRE não há esses avisos: ao trocar um caso de carga, troque a Origem à mão. | FB-06/EDR-035/050/051 |
| 00_README | A50 | (vazia) | 4. Valor que sai de conta não é digitado (EDR-050): digite as parcelas, não o resultado. Exemplo: massa total = massa medida + piloto (05_VEHICLE B30 e B31). | FB-06/EDR-035/050/051 |
| 00_README | A51 | (vazia) | 5. Até a V3.0 ser fechada, esta planilha é gerada pelo script do repositório e o que for digitado nela se perde na próxima geração (EDR-051). Depois do fechamento, ela passa a ser o arquivo da equipe. | FB-06/EDR-035/050/051 |
| 00_README | A52 | (vazia) | 6. Convenções de sinais e eixos: seção acima. Decisões e fichas: pasta docs/ do repositório (Engineering_Decision_Register.md e Engineering Standard). | FB-06/EDR-035/050/051 |
| 05_VEHICLE | A35 | (vazia) | Razão h_ns / raio do pneu dianteiro | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | B35 | (vazia) | 1.0 | EDR-050 (2ª rodada de feedback, usuário 2026-10-19); Milliken p. 672 |
| 05_VEHICLE | C35 | (vazia) | - | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | D35 | (vazia) | SUS-010 | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | A36 | (vazia) | Razão h_ns / raio do pneu traseiro | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | B36 | (vazia) | 1.0 | EDR-050 (2ª rodada de feedback, usuário 2026-10-19); Milliken p. 672 |
| 05_VEHICLE | C36 | (vazia) | - | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | D36 | (vazia) | SUS-011 | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | B16 | `='05_VEHICLE'!$B$33*0.0254/2` | `='05_VEHICLE'!$B$33*0.0254/2*'05_VEHICLE'!$B$35` | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | B17 | `='05_VEHICLE'!$B$34*0.0254/2` | `='05_VEHICLE'!$B$34*0.0254/2*'05_VEHICLE'!$B$36` | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 07_KINEMATICS | B14 | `='05_VEHICLE'!$B$17` | `='05_VEHICLE'!$B$34*0.0254/2` | EDR-050 (2ª rodada de feedback, usuário 2026-10-19): centro da roda separado do CG não suspenso (EDR-048) |
| 05_VEHICLE | E35 | (vazia) | ○ Estimativa | EDR-035 |
| 05_VEHICLE | G35 | (vazia) | 1.0 | EDR-035: valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H35 | (vazia) | ○ Estimativa | EDR-035: origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | F35 | (vazia) | Estimativa: Milliken p. 672 (cap. 18, altura do CG suspenso) toma a altura do centro da roda como "boa primeira aproximação" da altura do CG não suspenso e usa o raio carregado (R_LF, R_LR); razão 1 = essa aproximação. Aqui o raio é o sem carga (diâmetro / 2), sem a deflexão estática do pneu. Trocar pela medição do conjunto não suspenso quando houver. | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | E36 | (vazia) | ○ Estimativa | EDR-035 |
| 05_VEHICLE | G36 | (vazia) | 1.0 | EDR-035: valor da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | H36 | (vazia) | ○ Estimativa | EDR-035: origem da geração (oculto; aviso de desatualização) |
| 05_VEHICLE | F36 | (vazia) | Estimativa: Milliken p. 672 (cap. 18, altura do CG suspenso) toma a altura do centro da roda como "boa primeira aproximação" da altura do CG não suspenso e usa o raio carregado (R_LF, R_LR); razão 1 = essa aproximação. Aqui o raio é o sem carga (diâmetro / 2), sem a deflexão estática do pneu. Trocar pela medição do conjunto não suspenso quando houver. | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | F16 | Calculada (EDR-050): diâmetro do pneu (B33) × 0,0254 / 2. Estimativa: o raio do pneu aproxima a altura do CG não suspenso; não é medição da equipe. | Calculada (EDR-050): raio do pneu (B33 × 0,0254 / 2) × razão h_ns / raio (B35). Estimativa: a hipótese está na razão (B35), não é medição da equipe. | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 05_VEHICLE | F17 | Calculada (EDR-050): diâmetro do pneu (B34) × 0,0254 / 2. Estimativa: o raio do pneu aproxima a altura do CG não suspenso; não é medição da equipe. | Calculada (EDR-050): raio do pneu (B34 × 0,0254 / 2) × razão h_ns / raio (B36). Estimativa: a hipótese está na razão (B36), não é medição da equipe. | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 07_KINEMATICS | F14 | Calculada: = SUS-011 (05_VEHICLE B17). Placeholder: substituir pela altura do centro da roda do CAD. | Calculada: raio sem carga do pneu traseiro (05_VEHICLE B34 × 0,0254 / 2), sem a deflexão estática. Placeholder: substituir pela altura do centro da roda do CAD. | EDR-050 (2ª rodada de feedback, usuário 2026-10-19) |
| 00_README | A53 | (vazia) | 7. N/A = não se aplica, ou não dá para calcular na configuração atual (falta dado, valor fora da faixa do pneu, instabilidade): a célula nunca mostra número inventado. TBD = falta um dado, uma meta ou uma decisão (equivale a OPEN). "? A confirmar" (coluna Origem) é outra coisa: há valor, mas a origem dele não está registrada. | EDR-035 (N/A e TBD; usuário, 2026-10-19) |
| 01_SETUP | B10 | N/A (Fase 2) | TBD (Fase 2) | EDR-035 (N/A e TBD; troca aprovada pelo usuário, 2026-10-19) |
| 06_SUSPENSION | B4 (comentário) | Back-calculado da planilha detalhada T09 ('Ride Rate' front=16112.23 N/m, confirmado ser exatamente o Wheel Rate) x MR=1.76. CORRIGE valor anterior (baseado no spec sheet resumido, que arredondava F/R como iguais). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Back-calculado da planilha detalhada T09 ('Ride Rate' front=16112.23 N/m, confirmado ser exatamente o Wheel Rate) x MR=1.76. CORRIGE valor anterior (baseado no spec sheet resumido, que arredondava F/R como iguais). | EDR-012/022 |
| 06_SUSPENSION | B5 (comentário) | Back-calculado da planilha detalhada T09 ('Ride Rate' rear=18418.2 N/m) x MR=1.76. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Back-calculado da planilha detalhada T09 ('Ride Rate' rear=18418.2 N/m) x MR=1.76. | EDR-012/022 |
| 06_SUSPENSION | B6 (comentário) | Fonte: E03 (1.76:1). Assumido como convencao wheel/spring (igual a nossa) - E03 nao especifica a direcao explicitamente. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (1.76:1). Assumido como convencao wheel/spring (igual a nossa) - E03 nao especifica a direcao explicitamente. | EDR-012/022 |
| 06_SUSPENSION | B7 (comentário) | Fonte: E03 (1.76:1, mesmo valor da dianteira). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (1.76:1, mesmo valor da dianteira). | EDR-012/022 |
| 06_SUSPENSION | B10 (comentário) | Fonte: planilha detalhada T09 (AntiRoll Bar Rate front). Valor direto, ja nao e mais back-calculado - resolve a inconsistencia identificada anteriormente. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (AntiRoll Bar Rate front). Valor direto, ja nao e mais back-calculado - resolve a inconsistencia identificada anteriormente. | EDR-012/022 |
| 06_SUSPENSION | B11 (comentário) | Fonte: planilha detalhada T09 (AntiRoll Bar Rate rear, ~0, consistente com 'sem ARB' declarado). Inconsistencia anterior estava no Wheel Rate do spec sheet resumido, ja corrigida em SUS-203. | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (AntiRoll Bar Rate rear, ~0, consistente com 'sem ARB' declarado). Inconsistencia anterior estava no Wheel Rate do spec sheet resumido, ja corrigida em SUS-203. | EDR-012/022 |
| 06_SUSPENSION | B14 (comentário) | Fonte: planilha detalhada T09 (0.0675m) - mais precisa que o spec sheet resumido do E03 (60mm, arredondado). PROVISORIO ate Fase 2 (OptimumKinematics). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (0.0675m) - mais precisa que o spec sheet resumido do E03 (60mm, arredondado). PROVISORIO ate Fase 2 (OptimumKinematics). | EDR-012/022 |
| 06_SUSPENSION | B15 (comentário) | Fonte: E03 (110mm, Roll center height above ground static). PROVISORIO ate Fase 2 (OptimumKinematics). | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (110mm, Roll center height above ground static). PROVISORIO ate Fase 2 (OptimumKinematics). | EDR-012/022 |
| 10_TIRE | B16 | (texto V2.4) | (texto V3.0) | EDR-042/049 |
| 00_README | A3 | Versão do workbook: V2.4 ... | Versão do workbook: V3.0 ... | EDR-043 |
| 15_CHANGELOG | A16:C16 | (vazia) | (linha V3.0) | EDR-043 |
| 05_VEHICLE | B20 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 06_SUSPENSION | B36 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 06_SUSPENSION | B44 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | F22 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | B23 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | C23 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | D23 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | E23 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | F23 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | B24 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | C24 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | D24 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | E24 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | F24 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | B25 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | C25 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | D25 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | E25 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 10_TIRE | F25 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 11_DESIGN | B4 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 11_DESIGN | B5 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 11_DESIGN | B18 (estilo) | fundo amarelo (hipótese-chave) | sem fundo | FB-02 (usuário, 2026-10-19) |
| 05_VEHICLE | B4 (comentário) | Fonte: adesivo SAE Brasil 2026 - medicao real (248.5 kg sem piloto) + 68 kg de piloto (referencia padrao FSAE, nao medida). | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B5 (comentário) | Fonte: E05 (315mm, Key Parameters). Medida a partir do plano do solo (SUS-000), nao da origem do CAD. | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B6 (comentário) | Fonte: E05 (1594mm, Key Parameters). Diverge do E03 (1550mm, chassi anterior). | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B7 (comentário) | Fonte: E05 (1277mm, Key Parameters). | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B8 (comentário) | Fonte: E05 (1271mm, Key Parameters). | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B9 (comentário) | Derivado da distribuicao real medida no adesivo TX/E05 (48.43% dianteira, COM piloto) x wheelbase - consistente com mass_total (que inclui piloto). | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B10 (comentário) | Derivado da distribuicao real medida no adesivo TX/E05 (51.57% traseira, COM piloto) x wheelbase. | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B14 (comentário) | NAO DISPONIVEL para o TX/E05 (confirmado pela equipe: pesagem em plataforma mede carga total no solo, nao separa massa suspensa/nao-suspensa). Valor abaixo e ARBITRARIO - nao usar para decisao de projeto. | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B15 (comentário) | NAO DISPONIVEL para o TX/E05 (mesma razao do SUS-007). Valor abaixo e ARBITRARIO - nao usar para decisao de projeto. | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B16 (comentário) | Estimativa pelo raio do pneu 20.0-13 (E03, diametro 20.0in/2=0.254m). NAO e medicao real da equipe. | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B17 (comentário) | Estimativa pelo raio do pneu 20.0-13 (E03, mesmo pneu dianteiro/traseiro). NAO e medicao real da equipe. | (removido; texto na coluna Fonte) | EDR-035 |
| 05_VEHICLE | B20 (comentário) | SUS-000: coordenada Z do solo no sistema de coordenadas da equipe. Todas as alturas desta planilha já assumem conversão feita (medidas a partir do solo). Ver Engineering Standard, ficha SUS-000. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B4 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Back-calculado da planilha detalhada T09 ('Ride Rate' front=16112.23 N/m, confirmado ser exatamente o Wheel Rate) x MR=1.76. CORRIGE valor anterior (baseado no spec sheet resumido, que arredondava F/R como iguais). | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B5 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Back-calculado da planilha detalhada T09 ('Ride Rate' rear=18418.2 N/m) x MR=1.76. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B6 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (1.76:1). Assumido como convencao wheel/spring (igual a nossa) - E03 nao especifica a direcao explicitamente. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B7 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (1.76:1, mesmo valor da dianteira). | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B10 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (AntiRoll Bar Rate front). Valor direto, ja nao e mais back-calculado - resolve a inconsistencia identificada anteriormente. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B11 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (AntiRoll Bar Rate rear, ~0, consistente com 'sem ARB' declarado). Inconsistencia anterior estava no Wheel Rate do spec sheet resumido, ja corrigida em SUS-203. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B14 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: planilha detalhada T09 (0.0675m) - mais precisa que o spec sheet resumido do E03 (60mm, arredondado). PROVISORIO ate Fase 2 (OptimumKinematics). | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B15 (comentário) | DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. Fonte: E03 (110mm, Roll center height above ground static). PROVISORIO ate Fase 2 (OptimumKinematics). | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B36 (comentário) | PLACEHOLDER: fracao da forca de frenagem no eixo dianteiro (brake bias). Substituir pelo balanco de freio real do Setup. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B37 (comentário) | TF_r = 1 para RWD (hipotese congelada da V1). Revisitar se a equipe migrar para AWD. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B44 (comentário) | PLACEHOLDER: razao entre angulo do volante e angulo medio das rodas dianteiras. Substituir por medicao real da cremalheira ou geometria do rack. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B47 (comentário) | PROVISÓRIO (EDR-045): VERTICAL_STIFFNESS do .tir TTC provisório (Hoosier R25B, EDR-038). Não é o pneu do carro nem medição da equipe: substituir pela rigidez vertical do pneu real. Milliken p. 591, Gillespie eq. 5-8 e Seward eq. 4.1 põem o pneu em série com a mola. | (removido; texto na coluna Fonte) | EDR-035 |
| 06_SUSPENSION | B48 (comentário) | PROVISÓRIO (EDR-045): VERTICAL_STIFFNESS do .tir TTC provisório (Hoosier R25B, EDR-038). Não é o pneu do carro nem medição da equipe: substituir pela rigidez vertical do pneu real. Milliken p. 591, Gillespie eq. 5-8 e Seward eq. 4.1 põem o pneu em série com a mola. | (removido; texto na coluna Fonte) | EDR-035 |
| 07_KINEMATICS | B10 (comentário) | PLACEHOLDER geometrico para teste de formula - NAO e hardpoint real. Fase 2: REFERENCE do OptimumKinematics. | (removido; texto na coluna Fonte) | EDR-035 |
| 07_KINEMATICS | B14 (comentário) | PLACEHOLDER: usa a altura do CG não suspenso traseiro (SUS-011), que a ficha aproxima pela altura do centro da roda. Substituir pela altura do centro da roda do CAD. | (removido; texto na coluna Fonte) | EDR-035 |
| 07_KINEMATICS | B31 (comentário) | PLACEHOLDER geometrico - NAO e medicao real do curso instalado. Substituir pelo curso real (bump+rebound) com piloto sentado, conforme V.3.1.1. | (removido; texto na coluna Fonte) | EDR-035 |
| 08_VEHICLE_STATE | B4 (comentário) | ISO 8855: a_x positivo = aceleração para frente (transfere carga para o eixo traseiro). Negativo = frenagem. | (removido; texto na coluna Fonte) | EDR-035 |
| 08_VEHICLE_STATE | B5 (comentário) | ISO 8855: a_y positivo = para a esquerda (lado direito do carro ganha carga). | (removido; texto na coluna Fonte) | EDR-035 |
| 10_TIRE | B23 (comentário) | DEMONSTRATIVOS (EDR-022): α, γ e κ não vêm de nenhum cálculo do carro (não há modelo de slip na V2). Valores arbitrários coerentes em sinal com 08_VEHICLE_STATE (curva à esquerda, frenagem). Substitua por casos de carga definidos pela equipe. | (removido; texto na coluna Fonte) | EDR-035 |
| 10_TIRE | B24 (comentário) | Camber de entrada manual (EDR-036 sem decisão: ainda não há ID para camber estático). Convenção do projeto: + = topo para fora, nos dois lados. | (removido; texto na coluna Fonte) | EDR-035 |
| 10_TIRE | B86 (comentário) | Todos os coeficientes desta tabela: transcritos do .tir provisório (ver B-metadados). REFERENCE por natureza (DR-011), mas o DATASET é PROVISÓRIO. Mudou o dataset => mudar Tire REV (01_SETUP) e reexecutar 13_VALIDATION; resultados antigos viram STALE (Guia, H.3). | (removido; texto na coluna Fonte) | EDR-035 |
| (pasta) | nome definido Origens | (vazia) | '00_README'!$A$43:$A$48 | EDR-035 |
| 05_VEHICLE | E3:F36 (formatação) | (vazia) | lista 'Origens' em E; cores por origem; avisos (E: valor mudou e origem não; F: Dado do TX sem fonte); G/H ocultas | EDR-035 |
| 06_SUSPENSION | E3:F52 (formatação) | (vazia) | lista 'Origens' em E; cores por origem; avisos (E: valor mudou e origem não; F: Dado do TX sem fonte); G/H ocultas | EDR-035 |
| 07_KINEMATICS | E3:F69 (formatação) | (vazia) | lista 'Origens' em E; cores por origem; avisos (E: valor mudou e origem não; F: Dado do TX sem fonte); G/H ocultas | EDR-035 |
| 08_VEHICLE_STATE | E3:F11 (formatação) | (vazia) | lista 'Origens' em E; cores por origem; avisos (E: valor mudou e origem não; F: Dado do TX sem fonte); G/H ocultas | EDR-035 |
| 11_DESIGN | E3:F21 (formatação) | (vazia) | lista 'Origens' em E; cores por origem; avisos (E: valor mudou e origem não; F: Dado do TX sem fonte); G/H ocultas | EDR-035 |
| 10_TIRE | I20:J176 (formatação) | (vazia) | lista 'Origens' em I; cores por origem | EDR-035 |
| 00_README | A3 | Versão do workbook: V3.0 ... | (acrescenta a 1ª rodada de feedback) | EDR-035/050/051 |
| 00_README | A39:E52 (mesclagem) | (vazia) | A:E nas linhas de texto; B:D na tabela de origens | FB-06 |
| 15_CHANGELOG | A17:C17 | (vazia) | (linha V3.0, 1ª rodada de feedback) | EDR-035/050/051 |
| 00_README | A53:E53 (mesclagem) | (vazia) | A:E | EDR-035 |
| 00_README | A3 | Versão do workbook: V3.0 ... | (acrescenta a 2ª rodada de feedback) | EDR-035/050 |
| 15_CHANGELOG | A18:C18 | (vazia) | (linha V3.0, 2ª rodada de feedback) | EDR-035/050 |
