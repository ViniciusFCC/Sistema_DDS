R = 9,125 m (método linha central) | R = 8,385 m (método rente aos cones) (a origem de cada R está na rodada correspondente)

# Incremento 6: MMM em raio fixo e escada de hipóteses

Gerado por `tools/relatorio_escada.py`. Não edite à mão: rode o script de novo (`--sobrescrever`).

**Pior origem do caso: ? A confirmar. Geometria sintética** (não há hardpoints do CAD). O pneu é o `.tir` provisório do TTC (R25B); mola, MR, barra e RC são valores demonstrativos (T09/E03). **Nenhum número deste relatório é resultado do carro** nem validação física (Validation = NOT_VALIDATED, EDR-022). O raio R do skidpad é entrada "a confirmar" (diâmetros e bitola provisórios), e cada rodada traz o R usado e a origem dele. "? A confirmar" na pior origem quer dizer que pelo menos uma entrada do caso (ou o pneu) não tem origem registrada na planilha: a célula de origem está vazia ou fora da lista.

Faixa de busca da saturação: 0 a 2,00 g (parâmetro `--ay-max-g`, rótulo de varredura e não dado do carro; o padrão é 2,0 g). Eixo que não satura nela sai como "não satura" ou N/A.

**Sem veredito: tolerância pendente (EDR-065).** As tabelas mostram diferenças e se o sinal inverte, mas nenhuma linha é classificada como "dentro" ou "fora" da tolerância; essa classificação depende do EDR-065.

## 1. Origem

- Data: 2026-11-02T17:01:05
- Commit: `ce6808aea4708160daa33504b504bf151ce41138` (ramo `claude/inc7-plano-0926f7`; árvore sem mudanças pendentes)
- Planilha: `excel/FSAE_EV_Suspension_Fase1_V4_2.xlsx` (SHA-256 antes `0d979440f8db788700900526bce60c7df3202fb93e24c41ca6bf46c59c9ccde0`; depois igual: só uma cópia temporária foi recalculada). O caso é lido com o leitor da V4.1 (`caso_da_planilha_v41`, `passo1=False`), porque a V4.2 contém todos os nomes da V4.1.
- Motor de recálculo da cópia: excel (Excel 16.0 via COM, PID 37616); 117627 fórmulas, 0 erros, 36,8 s
- Pneu: `data/Hoosier_R25B_13x7_TTC_provisional.tir` (SHA-256 `f3bc80fda4145d53da06f69c8c0fcffbddfbbf73f4aab4149e1caa386c77c796`), em ISO_TYDEX (EDR-039)
- Python 3.13.17, numpy 2.5.4; rodadas: 2 (uma por R, abaixo)

## 2. Conferência do `.tir` (passo 1)

**Conclusão: não determinado.**

Origem dos coeficientes combinados do .tir (REX1, RBX*, RCX1, RBY*, RCY1, RVY*): não determinada. O help do Adams 2024.1 (PAC2002) não traz tabela de valores padrão, só dois arquivos de exemplo (pp. 92-107 do PDF; o segundo, em pp. 105-107, tem RCX1 = RCY1 = 1, REX1 = 0, RVY1 = 0), e o .tir tem outros valores (por exemplo RBX1 = 16,0481, RBY1 = 14,6284, RCY1 = 1,04408), então não são os valores desses exemplos; por outro lado REX1 = REX2 = 0,333333, RBY2 = 10,4, RVY1 = 0,01 e RVY6 = 18 são redondos, e o `.meta.json` não diz como o ajuste foi feito (nem se estes foram ajustados ao TTC). Por isso a variante `pac2002` (hipótese 9b) fica como mais uma hipótese sem validação, e não como referência melhor que a elipse.

## Rodada: método linha central

- R = 9,125 m (origem: skidpad, linha central: R = (D_int + D_ext)/4 com D_int = 15,25 m e D_ext = 21,25 m (Formula SAE Rules 2026 v1.0 (10/09/2025), D.10.1.1; entrada provisória, a confirmar com o regulamento da prova); bitolas do caso da planilha (dados demonstrativos, não do carro): t_f = 1,277 m, t_r = 1,271 m (não entra no R da linha central))
- O caso da planilha não tem R (R vazio); o valor do método foi aplicado só ao caso deste relatório. A planilha não foi alterada.
- Caso: L = 1,594 m, bitola dianteira 1,277 m, Ackermann desligado, CG lateral 0,000 m, aero downforce fixa, arrasto desligado.
- Tempos desta rodada: degrau 1 67,6 s, degrau 2 24,2 s, sensibilidades 28,2 s

**Aviso: a base "planilha" deste relatório não é a planilha de hoje.** A planilha com R vazio tem a hipótese 3 (cos δ_ref) desligada, e no Python o raio liga o cos δ_ref na dianteira (a Fy dianteira leva cos(L/R)). Com o R informado, a linha `planilha` já tem a hipótese 3 ligada, e o Δ da linha `3` mede só o cos δ do trim contra esse cos δ_ref, não contra a falta dele. Preencha o R na planilha (e ligue a chave da hipótese 3) para a base ser a da planilha.

### 3. Degrau 1: MMM na configuração da planilha contra `analise_par`

O degrau 1 é uma identidade quase por construção: os dois códigos usam a física por roda do mesmo módulo. Ele prova o reuso, não a física do MMM (adendo §5.1). Grade de α comum aos dois (401 pontos), cota da saturação = 2 × a resolução. Diferenças = MMM − `analise_par`.

| Sentido | Veredito MMM | Veredito par | Δ ay_sat F [m/s²] | Δ ay_sat R [m/s²] | C_N MMM (Q) | C_N par | Resolução [m/s²] | Passa o critério numérico | Motivo |
|---|---|---|---|---|---|---|---|---|---|
| esquerda | N/A | N/A | — | — | — | — | — | sim | — |
| direita | N/A | N/A | — | — | — | — | — | sim | — |

Os dois lados dão N/A nos dois sentidos (nenhum eixo satura até 2,00 g neste caso e neste R): o "sim" vale para a coincidência do N/A, e a identidade das saturações e do C_N não foi exercitada neste caso.

"Passa o critério numérico" é o critério de identidade do degrau 1 (mesmo veredito, saturações dentro da cota, C_N dentro da folga equivalente). Não é o veredito de tolerância do degrau 2 (EDR-065).

### 4. Degrau 2: uma variante Python por vez a partir da planilha

Uma linha por variante. Hipóteses numeradas como na spec (1+2 = α cinemático e Ackermann; 3 = cos δ no trim; 7 = os dois sentidos; 9a = Fx exigido por balanço; 9b = PAC2002 combinado; 10 = diferencial travado; 11 = transferência longitudinal em regime; `10+9b` = travado com o PAC2002 combinado). As linhas com a hipótese 7 (`7` e `todas`) mostram o pior sentido. K em °/g; K e o stability index valem em 0,05 g. O stability index (SI) sai em 1/g, com o sinal do C_N estabilizante: positivo = estabilizante (carro estável, subesterço); o Milliken usa o C_N do ISO, de sinal oposto.

A linha `planilha V4.3` (incremento 7, EDR-066) vem logo depois da `planilha`: as fórmulas da V4.3 (Ackermann com o centro da curva na linha do eixo traseiro e Fx exigido por arrasto induzido), desacoplada, com referência na `planilha`. O Δ dela é o efeito das duas formas novas sobre a V4.2. Valor sintético: depende do R desta rodada e do caso sintético, não é resultado do carro.

**Neste caso a linha `planilha V4.3` coincide com a `planilha` por construção, não por medida:** o Ackermann está desligado no caso (a forma v43 do Ackermann não tem deriva para corrigir); hipótese 9 desligada no caso: o Fx exigido não entra; nenhum eixo satura até 2,00 g, então ΔT e ΔC_N ficam sem valor. O efeito aparece com a h2 ou a h9 ligada; ΔT e ΔC_N só com saturação.

**Linhas de controle.** As variantes Python (menos a `7`) são resolvidas por um Newton 2-D em (β, δ) com a rotação a_y = A·cos β e a_x = −A·sen β; a `planilha` usa o trim desacoplado, com a_y = A. Duas linhas de controle resolvem as hipóteses da planilha pelo Newton, sem mudar nenhuma hipótese, e separam os dois efeitos (coluna "Δ contra"):

- `planilha (acoplado, sem rotação)`: o Newton com a_y = A e a_x = 0, as mesmas da planilha. O Δ contra a `planilha` é só o viés do método.
- `planilha (acoplado)`: o Newton com a rotação. O Δ contra a linha sem rotação é o efeito da simplificação a_y = A da planilha (a rotação não tem número de hipótese). A soma dos dois Δ é o Δ dela contra a `planilha`.

Δ e "Inverte" das linhas acopladas são contra a `planilha (acoplado)`, para que o número de cada linha seja o efeito da hipótese, e não o do método nem o da rotação; o Δ da `7` (desacoplada) é contra a `planilha`.

**Folga do outro eixo em T** (só nas linhas acopladas com T): acima de T não existe trim, então o eixo que não satura fica sem ay_sat ("—"), e a coluna mostra a folga dele em T, nos eixos do carro: a capacidade dele em T menos a força que ele faz no trim, em N e em % da capacidade. É a mesma folga que dá o Q. Nas linhas desacopladas os dois ay_sat existem e a coluna fica "—".

Linhas cuja hipótese está desligada no caso (a chave da planilha está desligada) ainda são calculadas, e a hipótese desligada não muda nada nelas: uma linha de uma hipótese só coincide com a referência por construção; na `todas`, só as hipóteses ligadas contam no Δ. O motivo vem na lista abaixo da tabela.

| Linha | Hipóteses | Veredito | Eixo que satura | ay_sat F | ay_sat R | T | Folga do outro eixo em T | C_N estab. (Q) | K [°/g] | Pior sentido | Δ T | Δ C_N | Δ K [°/g] | Δ contra | Inverte | SI [1/g] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `planilha` | — | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha` | N/A | -0,0306 |
| `planilha V4.3` | — | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha` | N/A | -0,0306 |
| `planilha (acoplado, sem rotação)` | — | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha` | N/A | -0,0306 |
| `planilha (acoplado)` | — | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha (acoplado, sem rotação)` | N/A | -0,0305 |
| `1+2` | 1, 2 | N/A | — | — | — | — | — | — | -0,041 | — | — | — | 0,079 | `planilha (acoplado)` | N/A | -0,0100 |
| `3` | 3 | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0305 |
| `7` | 7 | N/A | — | — | — | — | — | — | -0,121 | esquerda | — | — | 0,000 | `planilha` | N/A | -0,0306 |
| `9a` | 9 | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0305 |
| `9b` | 9 | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0305 |
| `10` | 10 | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0305 |
| `10+9b` | 10, 9 | N/A | — | — | — | — | — | — | -0,121 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0305 |
| `11` | 11 | N/A | — | — | — | — | — | — | -0,124 | — | — | — | -0,004 | `planilha (acoplado)` | N/A | -0,0315 |
| `todas` | 1, 2, 3, 7, 9, 10, 11 | N/A | — | — | — | — | — | — | -0,048 | esquerda | — | — | 0,073 | `planilha (acoplado)` | N/A | -0,0113 |

Motivos e avisos por linha (onde existem):

- `planilha`: eixo F: não satura até 2,000 g | eixo F: não satura até 2,000 g; eixo R: não satura até 2,000 g
- `planilha V4.3`: eixo F: não satura até 2,000 g | eixo F: não satura até 2,000 g; eixo R: não satura até 2,000 g
- `planilha (acoplado, sem rotação)`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `planilha (acoplado)`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `1+2`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `3`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `7`: hipótese desligada no caso (cg_lateral_m) | eixo F: não satura até 2,000 g | eixo F: não satura até 2,000 g; eixo R: não satura até 2,000 g
- `9a`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `9b`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `10`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `10+9b`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `11`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `todas`: hipótese desligada no caso (cda_m2 e crr; cg_lateral_m) | o trim existe até 2,000 g: nenhum eixo satura na faixa

### 5. Sensibilidades

Diferença central de ± um passo, na unidade da coluna. Valores em torno da planilha, sem faixa afirmada. `h_cp` liga com a transferência em regime; `h_cg` é por 10 mm de altura do CG (decisão 4 do plano: o jacking não muda a soma das Fz, e o camber já está em `ganho_camber`). A sensibilidade de `h_cp` é em torno de h_cp = 0: sem dado de altura do centro de pressão, `h_cp_m = None` equivale a h_cp = 0 (a parcela D·h_cp/L fica fora), e a tabela mostra o efeito de subir 10 mm a partir daí, não de uma altura medida.

| Parâmetro | Unidade | ∂T | ∂C_N estab. (Q) | ∂K [°/g] | Veredito − | Veredito + | Motivo |
|---|---|---|---|---|---|---|---|
| `ganho_camber_F` | por 0,1 °/° | — | — | -0,0007 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `ganho_camber_R` | por 0,1 °/° | — | — | 0,0006 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `rc_F` | por 10 mm | — | — | 0,0016 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `rc_R` | por 10 mm | — | — | 0,0040 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `kphi_F` | por 1 kN·m/rad | — | — | 0,0026 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `kphi_R` | por 1 kN·m/rad | — | — | 0,0065 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `h_cg` | por 10 mm | — | — | -0,0069 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `cg_lateral` | por 10 mm | — | — | -0,0001 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `h_cp` | por 10 mm | — | — | 0,0000 | N/A | N/A | lado menos: o trim existe até 2,000 g: nenhum eixo satura na faixa; lado mais: o trim existe até 2,000 g: nenhum eixo satura na faixa |

### 6. Achados do adendo §7 sobre fórmulas da planilha (nenhuma mudança agora)

Estas são duas simplificações físicas da planilha, conferidas no código. O incremento 6 não mexe nelas; qualquer mudança exige EDR e aprovação explícita do usuário. Aqui aparece só o efeito medido no degrau 2.

1. **Ackermann (hipótese 2, SUS-414).** `deriva_ackermann` supõe a mesma direção de velocidade nas duas dianteiras; na cinemática real as direções diferem de ≈ L·t/R², que é o próprio Ackermann ideal. Com L = 1,594 m, t = 1,277 m e R = 9,125 m, L·t/R² = 1,401° entre as rodas (estimativa analítica, não medida no solver). Efeito medido na linha `1+2`: ΔT = —, ΔC_N = —, ΔK = 0,0790 °/g, veredito N/A (inverte: N/A).
2. **Fx exigido (hipótese 9, EDR-057).** `fx_exigido_traseira` usa |F_yf|·tan(L/R) ≈ m·A·b/R, que depende de R e não da deriva; o balanço completo é F_yf·sen δ − m·A·sen β (em primeira ordem, F_yf·|α_F| + F_yr·|α_R|, o arrasto induzido). Efeito medido na linha `9a`: ΔT = —, ΔC_N = —, ΔK = 0,0000 °/g, veredito N/A (inverte: N/A).

Onde ΔT e ΔC_N aparecem como "—", a linha (ou a referência dela, coluna "Δ contra") não tem T: com este caso e este R nenhum eixo satura até 2,00 g, então só o K tem número. O efeito no limite não foi medido.

Nada foi ajustado para bater. Cada efeito vale para este R e para o caso sintético, não para o carro.

## Rodada: método rente aos cones

- R = 8,385 m (origem: skidpad, rente aos cones: R = √(b² + R_c²), R_c = 8,3494 m (eixo traseiro limita), limite geométrico de ocupação e não a trajetória real; D_int = 15,25 m e D_ext = 21,25 m (Formula SAE Rules 2026 v1.0 (10/09/2025), D.10.1.1; entrada provisória, a confirmar com o regulamento da prova); meia largura do pneu 0,0889 m, ◐ Provisório (.tir TTC); bitolas do caso da planilha (dados demonstrativos, não do carro): t_f = 1,277 m, t_r = 1,271 m)
- O caso da planilha não tem R (R vazio); o valor do método foi aplicado só ao caso deste relatório. A planilha não foi alterada.
- Caso: L = 1,594 m, bitola dianteira 1,277 m, Ackermann desligado, CG lateral 0,000 m, aero downforce fixa, arrasto desligado.
- Tempos desta rodada: degrau 1 52,8 s, degrau 2 20,8 s, sensibilidades 24,0 s

**Aviso: a base "planilha" deste relatório não é a planilha de hoje.** A planilha com R vazio tem a hipótese 3 (cos δ_ref) desligada, e no Python o raio liga o cos δ_ref na dianteira (a Fy dianteira leva cos(L/R)). Com o R informado, a linha `planilha` já tem a hipótese 3 ligada, e o Δ da linha `3` mede só o cos δ do trim contra esse cos δ_ref, não contra a falta dele. Preencha o R na planilha (e ligue a chave da hipótese 3) para a base ser a da planilha.

### 3. Degrau 1: MMM na configuração da planilha contra `analise_par`

O degrau 1 é uma identidade quase por construção: os dois códigos usam a física por roda do mesmo módulo. Ele prova o reuso, não a física do MMM (adendo §5.1). Grade de α comum aos dois (401 pontos), cota da saturação = 2 × a resolução. Diferenças = MMM − `analise_par`.

| Sentido | Veredito MMM | Veredito par | Δ ay_sat F [m/s²] | Δ ay_sat R [m/s²] | C_N MMM (Q) | C_N par | Resolução [m/s²] | Passa o critério numérico | Motivo |
|---|---|---|---|---|---|---|---|---|---|
| esquerda | N/A | N/A | — | — | — | — | — | sim | — |
| direita | N/A | N/A | — | — | — | — | — | sim | — |

Os dois lados dão N/A nos dois sentidos (nenhum eixo satura até 2,00 g neste caso e neste R): o "sim" vale para a coincidência do N/A, e a identidade das saturações e do C_N não foi exercitada neste caso.

"Passa o critério numérico" é o critério de identidade do degrau 1 (mesmo veredito, saturações dentro da cota, C_N dentro da folga equivalente). Não é o veredito de tolerância do degrau 2 (EDR-065).

### 4. Degrau 2: uma variante Python por vez a partir da planilha

Uma linha por variante. Hipóteses numeradas como na spec (1+2 = α cinemático e Ackermann; 3 = cos δ no trim; 7 = os dois sentidos; 9a = Fx exigido por balanço; 9b = PAC2002 combinado; 10 = diferencial travado; 11 = transferência longitudinal em regime; `10+9b` = travado com o PAC2002 combinado). As linhas com a hipótese 7 (`7` e `todas`) mostram o pior sentido. K em °/g; K e o stability index valem em 0,05 g. O stability index (SI) sai em 1/g, com o sinal do C_N estabilizante: positivo = estabilizante (carro estável, subesterço); o Milliken usa o C_N do ISO, de sinal oposto.

A linha `planilha V4.3` (incremento 7, EDR-066) vem logo depois da `planilha`: as fórmulas da V4.3 (Ackermann com o centro da curva na linha do eixo traseiro e Fx exigido por arrasto induzido), desacoplada, com referência na `planilha`. O Δ dela é o efeito das duas formas novas sobre a V4.2. Valor sintético: depende do R desta rodada e do caso sintético, não é resultado do carro.

**Neste caso a linha `planilha V4.3` coincide com a `planilha` por construção, não por medida:** o Ackermann está desligado no caso (a forma v43 do Ackermann não tem deriva para corrigir); hipótese 9 desligada no caso: o Fx exigido não entra; nenhum eixo satura até 2,00 g, então ΔT e ΔC_N ficam sem valor. O efeito aparece com a h2 ou a h9 ligada; ΔT e ΔC_N só com saturação.

**Linhas de controle.** As variantes Python (menos a `7`) são resolvidas por um Newton 2-D em (β, δ) com a rotação a_y = A·cos β e a_x = −A·sen β; a `planilha` usa o trim desacoplado, com a_y = A. Duas linhas de controle resolvem as hipóteses da planilha pelo Newton, sem mudar nenhuma hipótese, e separam os dois efeitos (coluna "Δ contra"):

- `planilha (acoplado, sem rotação)`: o Newton com a_y = A e a_x = 0, as mesmas da planilha. O Δ contra a `planilha` é só o viés do método.
- `planilha (acoplado)`: o Newton com a rotação. O Δ contra a linha sem rotação é o efeito da simplificação a_y = A da planilha (a rotação não tem número de hipótese). A soma dos dois Δ é o Δ dela contra a `planilha`.

Δ e "Inverte" das linhas acopladas são contra a `planilha (acoplado)`, para que o número de cada linha seja o efeito da hipótese, e não o do método nem o da rotação; o Δ da `7` (desacoplada) é contra a `planilha`.

**Folga do outro eixo em T** (só nas linhas acopladas com T): acima de T não existe trim, então o eixo que não satura fica sem ay_sat ("—"), e a coluna mostra a folga dele em T, nos eixos do carro: a capacidade dele em T menos a força que ele faz no trim, em N e em % da capacidade. É a mesma folga que dá o Q. Nas linhas desacopladas os dois ay_sat existem e a coluna fica "—".

Linhas cuja hipótese está desligada no caso (a chave da planilha está desligada) ainda são calculadas, e a hipótese desligada não muda nada nelas: uma linha de uma hipótese só coincide com a referência por construção; na `todas`, só as hipóteses ligadas contam no Δ. O motivo vem na lista abaixo da tabela.

| Linha | Hipóteses | Veredito | Eixo que satura | ay_sat F | ay_sat R | T | Folga do outro eixo em T | C_N estab. (Q) | K [°/g] | Pior sentido | Δ T | Δ C_N | Δ K [°/g] | Δ contra | Inverte | SI [1/g] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `planilha` | — | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha` | N/A | -0,0298 |
| `planilha V4.3` | — | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha` | N/A | -0,0298 |
| `planilha (acoplado, sem rotação)` | — | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha` | N/A | -0,0298 |
| `planilha (acoplado)` | — | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha (acoplado, sem rotação)` | N/A | -0,0297 |
| `1+2` | 1, 2 | N/A | — | — | — | — | — | — | -0,015 | — | — | — | 0,103 | `planilha (acoplado)` | N/A | -0,0035 |
| `3` | 3 | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0297 |
| `7` | 7 | N/A | — | — | — | — | — | — | -0,118 | esquerda | — | — | 0,000 | `planilha` | N/A | -0,0298 |
| `9a` | 9 | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0297 |
| `9b` | 9 | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0297 |
| `10` | 10 | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0297 |
| `10+9b` | 10, 9 | N/A | — | — | — | — | — | — | -0,118 | — | — | — | 0,000 | `planilha (acoplado)` | N/A | -0,0297 |
| `11` | 11 | N/A | — | — | — | — | — | — | -0,122 | — | — | — | -0,004 | `planilha (acoplado)` | N/A | -0,0308 |
| `todas` | 1, 2, 3, 7, 9, 10, 11 | N/A | — | — | — | — | — | — | -0,021 | esquerda | — | — | 0,096 | `planilha (acoplado)` | N/A | -0,0050 |

Motivos e avisos por linha (onde existem):

- `planilha`: eixo F: não satura até 2,000 g | eixo F: não satura até 2,000 g; eixo R: não satura até 2,000 g
- `planilha V4.3`: eixo F: não satura até 2,000 g | eixo F: não satura até 2,000 g; eixo R: não satura até 2,000 g
- `planilha (acoplado, sem rotação)`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `planilha (acoplado)`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `1+2`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `3`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `7`: hipótese desligada no caso (cg_lateral_m) | eixo F: não satura até 2,000 g | eixo F: não satura até 2,000 g; eixo R: não satura até 2,000 g
- `9a`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `9b`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `10`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `10+9b`: hipótese desligada no caso (cda_m2 e crr) | o trim existe até 2,000 g: nenhum eixo satura na faixa
- `11`: o trim existe até 2,000 g: nenhum eixo satura na faixa
- `todas`: hipótese desligada no caso (cda_m2 e crr; cg_lateral_m) | o trim existe até 2,000 g: nenhum eixo satura na faixa

### 5. Sensibilidades

Diferença central de ± um passo, na unidade da coluna. Valores em torno da planilha, sem faixa afirmada. `h_cp` liga com a transferência em regime; `h_cg` é por 10 mm de altura do CG (decisão 4 do plano: o jacking não muda a soma das Fz, e o camber já está em `ganho_camber`). A sensibilidade de `h_cp` é em torno de h_cp = 0: sem dado de altura do centro de pressão, `h_cp_m = None` equivale a h_cp = 0 (a parcela D·h_cp/L fica fora), e a tabela mostra o efeito de subir 10 mm a partir daí, não de uma altura medida.

| Parâmetro | Unidade | ∂T | ∂C_N estab. (Q) | ∂K [°/g] | Veredito − | Veredito + | Motivo |
|---|---|---|---|---|---|---|---|
| `ganho_camber_F` | por 0,1 °/° | — | — | -0,0007 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `ganho_camber_R` | por 0,1 °/° | — | — | 0,0006 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `rc_F` | por 10 mm | — | — | 0,0016 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `rc_R` | por 10 mm | — | — | 0,0040 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `kphi_F` | por 1 kN·m/rad | — | — | 0,0026 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `kphi_R` | por 1 kN·m/rad | — | — | 0,0065 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `h_cg` | por 10 mm | — | — | -0,0069 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `cg_lateral` | por 10 mm | — | — | -0,0001 | N/A | N/A | lado menos: eixo F: não satura até 2,000 g; lado mais: eixo F: não satura até 2,000 g |
| `h_cp` | por 10 mm | — | — | 0,0000 | N/A | N/A | lado menos: o trim existe até 2,000 g: nenhum eixo satura na faixa; lado mais: o trim existe até 2,000 g: nenhum eixo satura na faixa |

### 6. Achados do adendo §7 sobre fórmulas da planilha (nenhuma mudança agora)

Estas são duas simplificações físicas da planilha, conferidas no código. O incremento 6 não mexe nelas; qualquer mudança exige EDR e aprovação explícita do usuário. Aqui aparece só o efeito medido no degrau 2.

1. **Ackermann (hipótese 2, SUS-414).** `deriva_ackermann` supõe a mesma direção de velocidade nas duas dianteiras; na cinemática real as direções diferem de ≈ L·t/R², que é o próprio Ackermann ideal. Com L = 1,594 m, t = 1,277 m e R = 8,385 m, L·t/R² = 1,659° entre as rodas (estimativa analítica, não medida no solver). Efeito medido na linha `1+2`: ΔT = —, ΔC_N = —, ΔK = 0,1029 °/g, veredito N/A (inverte: N/A).
2. **Fx exigido (hipótese 9, EDR-057).** `fx_exigido_traseira` usa |F_yf|·tan(L/R) ≈ m·A·b/R, que depende de R e não da deriva; o balanço completo é F_yf·sen δ − m·A·sen β (em primeira ordem, F_yf·|α_F| + F_yr·|α_R|, o arrasto induzido). Efeito medido na linha `9a`: ΔT = —, ΔC_N = —, ΔK = 0,0000 °/g, veredito N/A (inverte: N/A).

Onde ΔT e ΔC_N aparecem como "—", a linha (ou a referência dela, coluna "Δ contra") não tem T: com este caso e este R nenhum eixo satura até 2,00 g, então só o K tem número. O efeito no limite não foi medido.

Nada foi ajustado para bater. Cada efeito vale para este R e para o caso sintético, não para o carro.

## 7. Limitações

- Geometria sintética, pneu provisório do TTC e dados demonstrativos: os números mostram o tamanho relativo de cada hipótese neste caso, não o do carro.
- A tolerância da escada (EDR-065) está pendente; nada aqui é "dentro" nem "fora".
- Este relatório não dá base para fixar a tolerância do EDR-065: nos dois R (9,125 e 8,385 m) todas as linhas dão N/A, porque nenhum eixo satura até 2 g e o Ackermann e a h9 estão desligados. A tolerância precisa de outro caso (Ackermann e tração ligados e um eixo que sature) ou de uma decisão sem ele.
- O raio R é entrada a confirmar; os resultados dependem dele (ver a primeira linha).
- Passou nos critérios do degrau 1 = os dois códigos concordam; não é validação física.
- O arrasto entra inteiro no eixo x do carro; a componente lateral D·sen β (a velocidade faz o ângulo β com o carro) fica fora do balanço lateral. É de 2ª ordem em β e D é uma fração pequena de m·A.
- A precisão de T nas linhas acopladas é da ordem da resolução do limite (0,01 m/s²), e não a da bisseção: a dobra do Newton pode cair até essa distância antes do pico do eixo.
- A cota do degrau 1 (2 × a resolução) é empírica: a resolução que o `analise_par` declara subestima o erro de interpolação dele (EDR-064, item 2.9).

