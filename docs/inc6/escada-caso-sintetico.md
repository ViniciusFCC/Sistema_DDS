R = 9,125 m (método linha central (caso sintético)) (a origem de cada R está na rodada correspondente)

# Incremento 6: MMM em raio fixo e escada de hipóteses (caso sintético, Task 15)

Gerado por `tools/relatorio_escada.py`. Não edite à mão: rode o script de novo (`--sobrescrever`).

**CASO SINTÉTICO (Task 15, EDR-065 item 3).** O caso é o da planilha V4.2 mais os valores da tabela abaixo, aplicados só neste relatório; a planilha não foi alterada. **Nenhum valor da tabela é dado do carro**: todos são "sintético (Task 15, sem fonte)" e foram escolhidos para ligar a h2 (Ackermann) e a h9 (tração) e fazer um eixo saturar antes de 2 g, de modo que a escada tenha números e não N/A. O objetivo é dar ao usuário uma tabela de diferenças para decidir a tolerância; o resultado não vale para o carro. As demais entradas são as da planilha (ver a pior origem abaixo).

| Campo | Valor | Unidade | Origem | O que liga ou muda | Por que este valor |
|---|---|---|---|---|---|
| `ackermann_pct` | 100,000 | % | sintético (Task 15, sem fonte) | liga a h2 (SUS-414); 100 % = Ackermann exato | sem dado de geometria, o Ackermann exato é o único valor que não escolhe um desvio |
| `rho_kg_m3` | 1,200 | kg/m³ | sintético (Task 15, sem fonte) | pré-requisito de cda_m2 | densidade do ar, ordem de grandeza |
| `cda_m2` | 1,000 | m² | sintético (Task 15, sem fonte) | liga a h9 (arrasto no Fx exigido) | ordem de grandeza de um monoposto de Fórmula SAE; só precisa ser > 0 para a h9 ficar ligada |
| `crr` | 0,015 | - | sintético (Task 15, sem fonte) | liga a h9 (rolamento no Fx exigido) | ordem de grandeza de pneu de competição em asfalto; só precisa ser > 0 |
| `mass_total` | 500,000 | kg | sintético (Task 15, sem fonte) | faz um eixo saturar antes de 2 g | com a massa da planilha (316,5 kg) nenhum eixo satura até 3 g, nem com o CG mais alto (até 0,9 m), nem com o CG deslocado para frente (a = 0,75 e 0,90 m), nem sem a downforce fixa de 400 N; a massa, com o resto do caso intacto, foi a primeira testada que satura as três linhas de referência. Com 360, 400 e 450 kg a linha `todas` ainda dá N/A; com 500 kg as três linhas de referência (`planilha`, `planilha V4.3`, `todas`) saturam |

**Pior origem do caso: ? A confirmar. Geometria sintética** (não há hardpoints do CAD). O pneu é o `.tir` provisório do TTC (R25B); mola, MR, barra e RC são valores demonstrativos (T09/E03). **Nenhum número deste relatório é resultado do carro** nem validação física (Validation = NOT_VALIDATED, EDR-022). O raio R do skidpad é entrada "a confirmar" (diâmetros e bitola provisórios), e cada rodada traz o R usado e a origem dele. "? A confirmar" na pior origem quer dizer que pelo menos uma entrada do caso (ou o pneu) não tem origem registrada na planilha: a célula de origem está vazia ou fora da lista.

Faixa de busca da saturação: 0 a 2,00 g (parâmetro `--ay-max-g`, rótulo de varredura e não dado do carro; o padrão é 2,0 g). Eixo que não satura nela sai como "não satura" ou N/A.

**Sem veredito: tolerância pendente (EDR-065).** As tabelas mostram diferenças e se o sinal inverte, mas nenhuma linha é classificada como "dentro" ou "fora" da tolerância; essa classificação depende do EDR-065.

## 1. Origem

- Data: 2026-11-09T08:41:42
- Commit: `ae9d1891fbc82435ea9a5cf9a947078a8203d68d` (ramo `claude/inc7-7b-v43-0c2266`; árvore sem mudanças pendentes)
- Planilha: `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx` (SHA-256 antes `0d979440f8db788700900526bce60c7df3202fb93e24c41ca6bf46c59c9ccde0`; depois igual: só uma cópia temporária foi recalculada). O caso é lido com o leitor da V4.1 (`caso_da_planilha_v41`, `passo1=False`), porque a V4.2 contém todos os nomes da V4.1.
- Motor de recálculo da cópia: excel (Excel 16.0 via COM, PID 31404); 117627 fórmulas, 0 erros, 20,9 s
- Pneu: `data/Hoosier_R25B_13x7_TTC_provisional.tir` (SHA-256 `f3bc80fda4145d53da06f69c8c0fcffbddfbbf73f4aab4149e1caa386c77c796`), em ISO_TYDEX (EDR-039)
- Python 3.13.17, numpy 2.5.4; rodadas: 1 (uma por R, abaixo)

## 2. Conferência do `.tir` (passo 1)

**Conclusão: não determinado.**

Origem dos coeficientes combinados do .tir (REX1, RBX*, RCX1, RBY*, RCY1, RVY*): não determinada. O help do Adams 2024.1 (PAC2002) não traz tabela de valores padrão, só dois arquivos de exemplo (pp. 92-107 do PDF; o segundo, em pp. 105-107, tem RCX1 = RCY1 = 1, REX1 = 0, RVY1 = 0), e o .tir tem outros valores (por exemplo RBX1 = 16,0481, RBY1 = 14,6284, RCY1 = 1,04408), então não são os valores desses exemplos; por outro lado REX1 = REX2 = 0,333333, RBY2 = 10,4, RVY1 = 0,01 e RVY6 = 18 são redondos, e o `.meta.json` não diz como o ajuste foi feito (nem se estes foram ajustados ao TTC). Por isso a variante `pac2002` (hipótese 9b) fica como mais uma hipótese sem validação, e não como referência melhor que a elipse.

## Rodada: método linha central (caso sintético)

- R = 9,125 m (origem: skidpad, linha central: R = (D_int + D_ext)/4 com D_int = 15,25 m e D_ext = 21,25 m (Formula SAE Rules 2026 v1.0 (10/09/2025), D.10.1.1; entrada provisória, a confirmar com o regulamento da prova); bitolas do caso da planilha (dados demonstrativos, não do carro): t_f = 1,277 m, t_r = 1,271 m (não entra no R da linha central))
- O caso da planilha não tem R (R vazio); o valor do método foi aplicado só ao caso deste relatório. A planilha não foi alterada.
- Caso: massa 500,0 kg, L = 1,594 m, bitola dianteira 1,277 m, Ackermann 100,0 %, CG lateral 0,000 m, aero downforce fixa, arrasto ligado (CdA, Crr).
- Tempos desta rodada: degrau 1 41,0 s, degrau 2 35,6 s, sensibilidades 30,8 s

**Aviso: a base "planilha" deste relatório não é a planilha de hoje.** A planilha com R vazio tem a hipótese 3 (cos δ_ref) desligada, e no Python o raio liga o cos δ_ref na dianteira (a Fy dianteira leva cos(L/R)). Com o R informado, a linha `planilha` já tem a hipótese 3 ligada, e o Δ da linha `3` mede só o cos δ do trim contra esse cos δ_ref, não contra a falta dele. Preencha o R na planilha (e ligue a chave da hipótese 3) para a base ser a da planilha.

### 3. Degrau 1: MMM na configuração da planilha contra `analise_par`

O degrau 1 é uma identidade quase por construção: os dois códigos usam a física por roda do mesmo módulo. Ele prova o reuso, não a física do MMM (adendo §5.1). Grade de α comum aos dois (401 pontos), cota da saturação = 1,5 × a resolução (que já traz o 4/3 do EDR-065, item 2: igual a 2 × |S − S2|). Diferenças = MMM − `analise_par`.

| Sentido | Veredito MMM | Veredito par | Δ ay_sat F [m/s²] | Δ ay_sat R [m/s²] | C_N MMM (Q) | C_N par | Resolução [m/s²] | Passa o critério numérico | Motivo |
|---|---|---|---|---|---|---|---|---|---|
| esquerda | LOOSE | LOOSE | 4,39e-06 | 9,80e-06 | -1,81e-02 | -1,81e-02 | 1,37e-05 | sim | — |
| direita | LOOSE | LOOSE | 4,39e-06 | 9,80e-06 | -1,81e-02 | -1,81e-02 | 1,37e-05 | sim | — |

"Passa o critério numérico" é o critério de identidade do degrau 1 (mesmo veredito, saturações dentro da cota, C_N dentro da folga equivalente). Não é o veredito de tolerância do degrau 2 (EDR-065).

### 4. Degrau 2: uma variante Python por vez a partir da planilha

Uma linha por variante. Hipóteses numeradas como na spec (1+2 = α cinemático e Ackermann; 3 = cos δ no trim; 7 = os dois sentidos; 9a = Fx exigido por balanço; 9b = PAC2002 combinado; 10 = diferencial travado; 11 = transferência longitudinal em regime; `10+9b` = travado com o PAC2002 combinado). As linhas com a hipótese 7 (`7` e `todas`) mostram o pior sentido. K em °/g; K e o stability index valem em 0,05 g. O stability index (SI) sai em 1/g, com o sinal do C_N estabilizante: positivo = estabilizante (carro estável, subesterço); o Milliken usa o C_N do ISO, de sinal oposto.

A linha `planilha V4.3` (incremento 7, EDR-066) vem logo depois da `planilha`: as fórmulas da V4.3 (Ackermann com o centro da curva na linha do eixo traseiro e Fx exigido por arrasto induzido), desacoplada, com referência na `planilha`. O Δ dela é o efeito das duas formas novas sobre a V4.2. Valor sintético: depende do R desta rodada e do caso sintético, não é resultado do carro.

**Linhas de controle.** As variantes Python (menos a `7`) são resolvidas por um Newton 2-D em (β, δ) com a rotação a_y = A·cos β e a_x = −A·sen β; a `planilha` usa o trim desacoplado, com a_y = A. Duas linhas de controle resolvem as hipóteses da planilha pelo Newton, sem mudar nenhuma hipótese, e separam os dois efeitos (coluna "Δ contra"):

- `planilha (acoplado, sem rotação)`: o Newton com a_y = A e a_x = 0, as mesmas da planilha. O Δ contra a `planilha` é só o viés do método.
- `planilha (acoplado)`: o Newton com a rotação. O Δ contra a linha sem rotação é o efeito da simplificação a_y = A da planilha (a rotação não tem número de hipótese). A soma dos dois Δ é o Δ dela contra a `planilha`.

Δ e "Inverte" das linhas acopladas são contra a `planilha (acoplado)`, para que o número de cada linha seja o efeito da hipótese, e não o do método nem o da rotação; o Δ da `7` (desacoplada) é contra a `planilha`.

**Folga do outro eixo em T** (só nas linhas acopladas com T): acima de T não existe trim, então o eixo que não satura fica sem ay_sat ("—"), e a coluna mostra a folga dele em T, nos eixos do carro: a capacidade dele em T menos a força que ele faz no trim, em N e em % da capacidade. É a mesma folga que dá o Q. Nas linhas desacopladas os dois ay_sat existem e a coluna fica "—".

Linhas cuja hipótese está desligada no caso (a chave da planilha está desligada) ainda são calculadas, e a hipótese desligada não muda nada nelas: uma linha de uma hipótese só coincide com a referência por construção; na `todas`, só as hipóteses ligadas contam no Δ. O motivo vem na lista abaixo da tabela.

| Linha | Hipóteses | Veredito | Eixo que satura | ay_sat F | ay_sat R | T | Folga do outro eixo em T | C_N estab. (Q) | K [°/g] | Pior sentido | Δ T | Δ C_N | Δ K [°/g] | Δ contra | Inverte | SI [1/g] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `planilha` | — | LOOSE | R | 1,7138 g | 1,6696 g | 1,6696 g | — | -0,0181 | -0,384 | — | 0,000000 g | 0,0000 | 0,000 | `planilha` | não | — |
| `planilha V4.3` | — | LOOSE | R | 1,7152 g | 1,6604 g | 1,6604 g | — | -0,0226 | -0,235 | — | -0,009169 g | -0,0044 | 0,148 | `planilha` | não | — |
| `planilha (acoplado, sem rotação)` | — | LOOSE | R | — | 1,6696 g | 1,6696 g | 172,6 N (4,17 %) | -0,0181 | -0,384 | — | 0,000000 g | 0,0000 | 0,000 | `planilha` | não | — |
| `planilha (acoplado)` | — | LOOSE | R | — | 1,6746 g | 1,6746 g | 173,9 N (4,20 %) | -0,0183 | -0,383 | — | 0,005068 g | -0,0001 | 0,001 | `planilha (acoplado, sem rotação)` | não | — |
| `1+2` | 1, 2 | LOOSE | R | — | 1,6748 g | 1,6748 g | 180,4 N (4,36 %) | -0,0190 | -0,231 | — | 0,000131 g | -0,0007 | 0,151 | `planilha (acoplado)` | não | — |
| `3` | 3 | N/A | — | — | — | — | — | — | -0,394 | — | — | — | -0,012 | `planilha (acoplado)` | N/A | — |
| `7` | 7 | LOOSE | R | 1,7138 g | 1,6696 g | 1,6696 g | — | -0,0181 | -0,384 | esquerda | 0,000000 g | 0,0000 | 0,000 | `planilha` | não | — |
| `9a` | 9 | LOOSE | R | — | 1,6413 g | 1,6413 g | 287,2 N (6,86 %) | -0,0302 | -0,383 | — | -0,033376 g | -0,0119 | 0,000 | `planilha (acoplado)` | não | — |
| `9b` | 9 | LOOSE | R | — | 1,6569 g | 1,6569 g | 233,8 N (5,62 %) | -0,0246 | -0,382 | — | -0,017728 g | -0,0063 | 0,001 | `planilha (acoplado)` | não | — |
| `10` | 10 | N/A | — | — | — | — | — | — | — | — | — | — | — | `planilha (acoplado)` | N/A | — |
| `10+9b` | 10, 9 | N/A | — | — | — | — | — | — | -1,339 | — | — | — | -0,957 | `planilha (acoplado)` | N/A | -0,1987 |
| `11` | 11 | N/A | — | — | — | — | — | — | -0,389 | — | — | — | -0,006 | `planilha (acoplado)` | N/A | — |
| `todas` | 1, 2, 3, 7, 9, 10, 11 | LOOSE | R | — | 1,6491 g | 1,6491 g | 31,5 N (0,79 %) | -0,0033 | -1,803 | esquerda | -0,025573 g | 0,0150 | -1,420 | `planilha (acoplado)` | não | -0,3041 |

Motivos e avisos por linha (onde existem):

- `planilha`: stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g | γ_FL = 19,59° → 4,00° (CAMMAX); Fz_FR = 2299,7 N → 1521,0 N (FZMAX); γ_FR = -22,59° → -4,00° (CAMMIN); γ_RL = 15,86° → 4,00° (CAMMAX); Fz_RR = 2431,2 N → 1521,0 N (FZMAX); γ_RR = -17,86° → -4,00° (CAMMIN)
- `planilha V4.3`: stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,700 g]; tração excede o atrito longitudinal em RL em a_y = 1,750 g | γ_FL = 19,48° → 4,00° (CAMMAX); Fz_FR = 2294,1 N → 1521,0 N (FZMAX); γ_FR = -22,48° → -4,00° (CAMMIN); γ_RL = 15,77° → 4,00° (CAMMAX); Fz_RR = 2425,4 N → 1521,0 N (FZMAX); γ_RR = -17,77° → -4,00° (CAMMIN)
- `planilha (acoplado, sem rotação)`: acoplado: além de T não há trim; stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g | γ_FL = 19,59° → 4,00° (CAMMAX); Fz_FR = 2299,7 N → 1521,0 N (FZMAX); γ_FR = -22,59° → -4,00° (CAMMIN); γ_RL = 15,86° → 4,00° (CAMMAX); Fz_RR = 2431,2 N → 1521,0 N (FZMAX); γ_RR = -17,86° → -4,00° (CAMMIN)
- `planilha (acoplado)`: acoplado: além de T não há trim; stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g | γ_FL = 19,59° → 4,00° (CAMMAX); Fz_FR = 2299,5 N → 1521,0 N (FZMAX); γ_FR = -22,59° → -4,00° (CAMMIN); γ_RL = 15,86° → 4,00° (CAMMAX); Fz_RR = 2431,0 N → 1521,0 N (FZMAX); γ_RR = -17,86° → -4,00° (CAMMIN)
- `1+2`: acoplado: além de T não há trim; stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g | γ_FL = 19,57° → 4,00° (CAMMAX); Fz_FR = 2298,6 N → 1521,0 N (FZMAX); γ_FR = -22,57° → -4,00° (CAMMIN); γ_RL = 15,84° → 4,00° (CAMMAX); Fz_RR = 2430,0 N → 1521,0 N (FZMAX); γ_RR = -17,84° → -4,00° (CAMMIN)
- `3`: o trim deixa de existir acima de T = 1,633 g, mas nenhum eixo está no pico (menor folga: eixo F, 10.726 N > 2.570 N = força por m/s² do eixo · 0.01 m/s²) | stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g
- `7`: hipótese desligada no caso (cg_lateral_m) | stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g | γ_FL = 19,59° → 4,00° (CAMMAX); Fz_FR = 2299,7 N → 1521,0 N (FZMAX); γ_FR = -22,59° → -4,00° (CAMMIN); γ_RL = 15,86° → 4,00° (CAMMAX); Fz_RR = 2431,2 N → 1521,0 N (FZMAX); γ_RR = -17,86° → -4,00° (CAMMIN)
- `9a`: acoplado: além de T não há trim; stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,950 g]; tração excede o atrito longitudinal em RL em a_y = 2,000 g | γ_FL = 19,22° → 4,00° (CAMMAX); Fz_FR = 2281,7 N → 1521,0 N (FZMAX); γ_FR = -22,22° → -4,00° (CAMMIN); γ_RL = 15,56° → 4,00° (CAMMAX); Fz_RR = 2412,6 N → 1521,0 N (FZMAX); γ_RR = -17,56° → -4,00° (CAMMIN)
- `9b`: acoplado: além de T não há trim; stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,850 g]; tração excede o atrito longitudinal em RL em a_y = 1,900 g | γ_FL = 19,39° → 4,00° (CAMMAX); Fz_FR = 2290,1 N → 1521,0 N (FZMAX); γ_FR = -22,39° → -4,00° (CAMMIN); γ_RL = 15,70° → 4,00° (CAMMAX); Fz_RR = 2421,3 N → 1521,0 N (FZMAX); γ_RR = -17,70° → -4,00° (CAMMIN)
- `10`: pneu fora da faixa em RL: alpha=-15.00° fora de [-15.0, 15.0] em a_y = 0,050 g (início da varredura) | K indisponível: k_trim: sem trim em a_y = 0,060 g (pneu fora da faixa em RL: alpha=-15.00° fora de [-15.0, 15.0]); stability index indisponível: stability_index: sem trim em a_y = 0,050 g (pneu fora da faixa em RL: alpha=-15.00° fora de [-15.0, 15.0])
- `10+9b`: o trim deixa de existir acima de T = 1,642 g, mas nenhum eixo está no pico (menor folga: eixo R, 9.852 N > 2.519 N = força por m/s² do eixo · 0.01 m/s²)
- `11`: capacidade dos eixos em T: eixo R: pico na borda da faixa do pneu (pneu fora da faixa em FL: alpha=15.06° fora de [-15.0, 15.0]) | stability index indisponível: stability_index: sem raiz de ΣFy = m·A_Y em [0, 1,750 g]; tração excede o atrito longitudinal em RL em a_y = 1,800 g
- `todas`: hipótese desligada no caso (cg_lateral_m) | acoplado: além de T não há trim | γ_FL = 19,24° → 4,00° (CAMMAX); Fz_FR = 2207,7 N → 1521,0 N (FZMAX); γ_FR = -22,24° → -4,00° (CAMMIN); γ_RL = 15,58° → 4,00° (CAMMAX); Fz_RR = 2488,6 N → 1521,0 N (FZMAX); γ_RR = -17,58° → -4,00° (CAMMIN)

### 5. Sensibilidades

Diferença central de ± um passo, na unidade da coluna. Valores em torno da planilha, sem faixa afirmada. `h_cp` liga com a transferência em regime; `h_cg` é por 10 mm de altura do CG (decisão 4 do plano: o jacking não muda a soma das Fz, e o camber já está em `ganho_camber`). A sensibilidade de `h_cp` é em torno de h_cp = 0: sem dado de altura do centro de pressão, `h_cp_m = None` equivale a h_cp = 0 (a parcela D·h_cp/L fica fora), e a tabela mostra o efeito de subir 10 mm a partir daí, não de uma altura medida.

| Parâmetro | Unidade | ∂T | ∂C_N estab. (Q) | ∂K [°/g] | Veredito − | Veredito + | Motivo |
|---|---|---|---|---|---|---|---|
| `ganho_camber_F` | por 0,1 °/° | 0,00000 g | 0,00000 | -0,0011 | LOOSE | LOOSE | — |
| `ganho_camber_R` | por 0,1 °/° | 0,00000 g | 0,00000 | 0,0016 | LOOSE | LOOSE | — |
| `rc_F` | por 10 mm | 0,00929 g | 0,00698 | 0,0112 | LOOSE | LOOSE | — |
| `rc_R` | por 10 mm | -0,01007 g | -0,00886 | 0,0106 | LOOSE | LOOSE | — |
| `kphi_F` | por 1 kN·m/rad | 0,01558 g | 0,01220 | 0,0190 | LOOSE | LOOSE | — |
| `kphi_R` | por 1 kN·m/rad | -0,01723 g | -0,01459 | 0,0169 | LOOSE | LOOSE | — |
| `h_cg` | por 10 mm | -0,02046 g | 0,00146 | -0,0203 | LOOSE | LOOSE | — |
| `cg_lateral` | por 10 mm | 0,01280 g | 0,00037 | -0,0006 | LOOSE | LOOSE | — |
| `h_cp` | por 10 mm | — | — | 0,0000 | N/A | N/A | lado menos: capacidade dos eixos em T: eixo R: pico na borda da faixa do pneu (pneu fora da faixa em FL: alpha=15.06° fora de [-15.0, 15.0]); lado mais: capacidade dos eixos em T: eixo R: pico na borda da faixa do pneu (pneu fora da faixa em FL: alpha=15.06° fora de [-15.0, 15.0]) |

### 6. Achados do adendo §7 sobre fórmulas da planilha (nenhuma mudança agora)

Estas são duas simplificações físicas da planilha, conferidas no código. O incremento 6 não mexe nelas; qualquer mudança exige EDR e aprovação explícita do usuário. Aqui aparece só o efeito medido no degrau 2.

1. **Ackermann (hipótese 2, SUS-414).** `deriva_ackermann` supõe a mesma direção de velocidade nas duas dianteiras; na cinemática real as direções diferem de ≈ L·t/R², que é o próprio Ackermann ideal. Com L = 1,594 m, t = 1,277 m e R = 9,125 m, L·t/R² = 1,401° entre as rodas (estimativa analítica, não medida no solver). Efeito medido na linha `1+2`: ΔT = 0,0001 g, ΔC_N = -0,0007, ΔK = 0,1513 °/g, veredito LOOSE (inverte: não).
2. **Fx exigido (hipótese 9, EDR-057).** `fx_exigido_traseira` usa |F_yf|·tan(L/R) ≈ m·A·b/R, que depende de R e não da deriva; o balanço completo é F_yf·sen δ − m·A·sen β (em primeira ordem, F_yf·|α_F| + F_yr·|α_R|, o arrasto induzido). Efeito medido na linha `9a`: ΔT = -0,0334 g, ΔC_N = -0,0119, ΔK = 0,0001 °/g, veredito LOOSE (inverte: não).

Nada foi ajustado para bater. Cada efeito vale para este R e para o caso sintético, não para o carro.

## 7. Limitações

- Geometria sintética, pneu provisório do TTC e dados demonstrativos: os números mostram o tamanho relativo de cada hipótese neste caso, não o do carro.
- A tolerância da escada (EDR-065) está pendente; nada aqui é "dentro" nem "fora".
- **Caso sintético (Task 15):** ackermann_pct, rho_kg_m3, cda_m2, crr e mass_total são sintéticos e sem fonte (tabela no topo). O relatório existe para o usuário decidir a tolerância do EDR-065 (item 3) a partir das diferenças; ele não propõe valor, e os números não são do carro. Uma tolerância tirada deste caso vale tanto quanto o caso representa o carro, e a massa de 500 kg não é uma estimativa dele. Nas linhas saturadas o pneu fica nos limites CAMMAX, CAMMIN e FZMAX do .tir; na linha `todas` a folga é de 0,79 % no outro eixo; as massas não suspensas ficam fixas.
- O raio R é entrada a confirmar; os resultados dependem dele (ver a primeira linha).
- Passou nos critérios do degrau 1 = os dois códigos concordam; não é validação física.
- O arrasto entra inteiro no eixo x do carro; a componente lateral D·sen β (a velocidade faz o ângulo β com o carro) fica fora do balanço lateral. É de 2ª ordem em β e D é uma fração pequena de m·A.
- A precisão de T nas linhas acopladas é da ordem da resolução do limite (0,01 m/s²), e não a da bisseção: a dobra do Newton pode cair até essa distância antes do pico do eixo.
- A cota do degrau 1 (1,5 × a resolução, igual a 2 × |S − S2| só no caso de dois eixos; nos casos de passo e piso ela caiu de 2× para 1,5×) é empírica: o |S − S2| que o `analise_par` mede subestima o erro de interpolação dele (EDR-064, item 2.9; o 4/3 já está na resolução, EDR-065, item 2).

