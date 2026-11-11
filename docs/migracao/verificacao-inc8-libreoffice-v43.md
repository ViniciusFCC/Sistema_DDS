# Incremento 8 (V4.4), suíte única no LibreOffice: complemento do test_workbook_v4_3

- Commit: e3dc12b (árvore sem mudanças pendentes no código). Data: 2026-11-11, início 08:48:57, fim 09:11:13. Motor: LibreOffice
  (`DDS_RECALC=libreoffice`), com `DDS_CASOS=TC003,TC004`.
- Por que este log existe: na suíte única no LibreOffice (`verificacao-inc8-libreoffice.md`, mesmo commit, 04:12 a 08:48) todos os
  itens deram PASS, menos o CA-09 `tests/test_workbook_v4_3.py`, que saiu com código 3 em 243,5 s sem linha de resumo. Causa: o
  TC-WB43-005 confere `HasFormula`, `FormulaHidden` e `ProtectContents`, que só o Excel expõe (COM); fora do Excel o script imprime
  "TC-WB43-005 NÃO EXECUTÁVEL: só no Excel (COM)" e sai com 3 antes de rodar o TC-WB43-004. Com o motor detectado, o executor da suíte
  conta esse código como FAIL. É código da V4.3, sem mudança nesta branch; a V4.3 nunca tinha rodado no LibreOffice (registro de
  versões V4.3). Nenhuma conferência de valor falhou.
- Decisão do usuário (2026-11-11): registrar, sem mudar código. Este log roda o 003 e o 004 (as conferências de valor) no
  LibreOffice; o 005 passou no Excel (`verificacao-inc8-excel-v43.md`). Fazer o 005 sair PULADO fora do Excel, e o executor aceitar
  isso, fica como pendência do PR.
- Como rodou: `tools/rodar_testes.rodar(['tests/test_workbook_v4_3.py'], timeout=7200)`, a mesma função que a suíte usa, sozinho.

| CA | Item | Script | Esperado | Obtido | Código | Tempo | Resultado |
|---|---|---|---|---|---|---|---|
| CA-09 | planilha LibreOffice x Python (test_workbook_v4_3, 003 e 004) | `tests/test_workbook_v4_3.py` | 2 | 2 PASS, 0 FAIL, de 2 testes | 0 | 1335,2 s | **PASS** |

<details><summary>tests/test_workbook_v4_3.py: stdout</summary>

```text
MOTOR: libreoffice (LibreOffice em C:\Program Files\LibreOffice\program\soffice.exe)
  grafo de dependências (146373 fórmulas) em 39 s
  EXCLUÍDAS (decisão B: 16 B137 a B139 e as linhas dif da 20_EQ_TROCA ['B34', 'B35', 'C34', 'C35', 'D34', 'D35', 'E34', 'E35'], mais o fecho transitivo): 115 células: 03_TARGETS: 1 (K11); 14_DASHBOARD: 2 (B42, B44); 16_EQUILIBRIO: 17 (B137, B138, B139, B140, B141, B142, B143, B145, B146, B147, B148, B149…); 20_EQ_TROCA: 88 (L5, P5, Q5, R5, V5, L6, P6, Q6, R6, V6, L7, P7…); 22_CADEIA: 7 (D22, D23, D24, D25, D28, D29, D30)
  mudança intencional permitida no caso MANUAL_VAZIO (C-B4, C-B7, C-B7b: 16 B65, B173, E173 e o que depende): 143426 células: 03_TARGETS: 1 (K10); 14_DASHBOARD: 1 (B41); 16_EQUILIBRIO: 93 (B65, G65, G66, G67, G68, G69, G70, G71, G72, G73, G74, G75…); 17_EQ_PAR: 8005 (B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, B17, C17…); 18_EQ_PAR_FINA: 20341 (B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, AA17, AB17…); 19_EQ_LINEAR: 2828 (C5, D5, E5, F5, G5, H5, I5, J5, K5, L5, C6, D6…); 20_EQ_TROCA: 104 (F5, G5, H5, I5, J5, K5, M5, N5, O5, S5, T5, U5…); 20a_TROCA: 28012 (B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, B17, C17…); 20b_TROCA: 28012 (B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, B17, C17…); 20c_TROCA: 28012 (B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, B17, C17…); 20d_TROCA: 28012 (B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, B17, C17…); 22_CADEIA: 5 (D19, D20, D21, D26, D27)
  C1_H: V4.2 11 s, V4.3 13 s; 125958 células comparadas, 3 de texto constante reescrito pelo gerador
  C4b: V4.2 11 s, V4.3 12 s; 125959 células comparadas, 3 de texto constante reescrito pelo gerador
  ORG_TX_H: V4.2 10 s, V4.3 12 s; 125958 células comparadas, 3 de texto constante reescrito pelo gerador
  MANUAL_VAZIO: V4.2 10 s, V4.3 12 s; 125954 células comparadas, 3 de texto constante reescrito pelo gerador
  MUDANÇA INTENCIONAL (C-B4/C-B7/C-B7b) MANUAL_VAZIO 16_EQUILIBRIO!B173: V4.2 'N/A: raio do skidpad R a confirmar' -> V4.3 'N/A: raio do skidpad R a confirmar (R manual vazio: a confirmar)'
  texto constante reescrito (fora da comparação, 3 células): 00_README: 1 (A3); 16_EQUILIBRIO: 2 (A9, F9)
  MANUAL_VAZIO 16 B65: V4.2 '-' -> V4.3 '-'
  MANUAL_VAZIO 16 B173: V4.2 'N/A: raio do skidpad R a confirmar' -> V4.3 'N/A: raio do skidpad R a confirmar (R manual vazio: a confirmar)'
  MANUAL_VAZIO 16 E173: V4.2 '? A confirmar' -> V4.3 '? A confirmar'
[PASS] TC-WB43-003: V4.3 com h2v = h9v = 0, modo Manual e R manual = o B9 da V4.2 == V4.2, recalculadas no Excel, em todas as células da V4.2 (rel. <= 1e-9) fora das excluídas pela decisão B (16 B137 a B139, as linhas dif da 20_EQ_TROCA e o fecho transitivo no grafo de fórmulas; lista no log) e dos textos constantes reescritos; casos C1_H, C4b, ORG_TX_H e MANUAL_VAZIO (só o texto do B173 pelo motivo do R manual vazio e o E173)  0 divergência(s): []; 115 excluídas; comparações [('C1_H', 125958, 3), ('C4b', 125959, 3), ('ORG_TX_H', 125958, 3), ('MANUAL_VAZIO', 125954, 3)]; 1 mudança(s) intencional(is); recálculo (s) [11, 13, 11, 12, 10, 12, 10, 12]
  M_MAN_D: recalculado em 12.3 s; 146373 fórmulas, 0 erros
  M_MAN_E: recalculado em 12.7 s; 146373 fórmulas, 0 erros
  M_LC_D: recalculado em 12.5 s; 146373 fórmulas, 0 erros
  M_LC_E: recalculado em 13.1 s; 146373 fórmulas, 0 erros
  M_RC_D: recalculado em 12.5 s; 146373 fórmulas, 0 erros
  M_RC_E: recalculado em 12.3 s; 146373 fórmulas, 0 erros
  LOOSE_PICO: recalculado em 12.5 s; 146373 fórmulas, 0 erros
  PUSH_PICO: recalculado em 12.8 s; 146373 fórmulas, 0 erros
  FRENTE_DESCOLADA: recalculado em 12.0 s; 146373 fórmulas, 0 erros
   FRENTE_DESCOLADA ponto 8 α_R ISOLADO: planilha -0.000764952800470158 Python -0.0007649528109126907; |Δα| = 1.044e-11 rad; relativo a max(|α|, 1e-3) = 1.044e-08 (limite do V4.1: 1e-08; teto do isolado: 2e-08)
  FX_ASSIM: recalculado em 12.4 s; 146373 fórmulas, 0 erros
  H2V_0: recalculado em 12.5 s; 146373 fórmulas, 0 erros
  H9V_0: recalculado em 11.9 s; 146373 fórmulas, 0 erros
  CHAVE_H2V_2: recalculado em 10.7 s; 146373 fórmulas, 0 erros
  CHAVE_H2V_VAZIA: recalculado em 11.2 s; 146373 fórmulas, 0 erros
  CHAVE_H9V_TEXTO: recalculado em 10.9 s; 146373 fórmulas, 0 erros
  GEO_RB: recalculado em 11.0 s; 146373 fórmulas, 0 erros
  GEO_RC: recalculado em 10.9 s; 146373 fórmulas, 0 erros
  GEO_RB_ACK: recalculado em 10.9 s; 146373 fórmulas, 0 erros
  GEO_RC_ACK: recalculado em 10.9 s; 146373 fórmulas, 0 erros
  GEO_RB_H2V0: recalculado em 10.9 s; 146373 fórmulas, 0 erros
  GEO_RC_H2V0: recalculado em 10.8 s; 146373 fórmulas, 0 erros
  MODO_ERRADO: recalculado em 11.0 s; 146373 fórmulas, 0 erros
  MODO_TEXTO: recalculado em 10.8 s; 146373 fórmulas, 0 erros
  MODO_INV_H0: recalculado em 11.9 s; 146373 fórmulas, 0 erros
  DINT_VAZIO: recalculado em 11.0 s; 146373 fórmulas, 0 erros
  DEXT_LE_DINT: recalculado em 10.7 s; 146373 fórmulas, 0 erros
  RIN_LE_L: recalculado em 12.1 s; 146373 fórmulas, 0 erros
  BITOLA_TR_VAZIA: 35 erro(s) de fórmula, os mesmos da V4.2 (bitola traseira vazia; nenhum na 16, 17, 18 ou 24)
  BITOLA_TR_VAZIA: recalculado em 10.7 s; 146373 fórmulas, 35 erros
  MEIA_LARG_VAZIA: recalculado em 11.9 s; 146373 fórmulas, 0 erros
  MANUAL_VAZIO_H2: recalculado em 11.0 s; 146373 fórmulas, 0 erros
  MANUAL_VAZIO_H0: recalculado em 11.8 s; 146373 fórmulas, 0 erros
  FATOR_05: recalculado em 11.3 s; 146372 fórmulas, 0 erros
  NEUTRO_43: recalculado em 12.2 s; 146373 fórmulas, 0 erros
   NEUTRO_43: K_ARB dianteiro ×1.059204: V4.3 NEUTRO (4/3), Python sem o fator PUSH, V4.2 na planilha PUSH
  RF3_43: recalculado em 12.4 s; 146373 fórmulas, 0 erros
   RF3_43: S_r 19.618823143207283, S_r refinada None, resolução 0.49050000000000005 (passo 0.49050000000000005), planilha 0.4905
  M_MAN_D: PUSH (motivo None); S_f 1.0946 g, S_r 1.1225 g, resolução 0.0014 g, R 8 (Manual), formas v43/v43
  M_MAN_E: PUSH (motivo None); S_f 1.0974 g, S_r 1.1248 g, resolução 0.0011 g, R 8 (Manual), formas v43/v43
  M_LC_D: PUSH (motivo None); S_f 1.1051 g, S_r 1.1273 g, resolução 0.0016 g, R 9.125 (Linha central), formas v43/v43
  M_LC_E: PUSH (motivo None); S_f 1.1077 g, S_r 1.1295 g, resolução 0.0014 g, R 9.125 (Linha central), formas v43/v43
  M_RC_D: PUSH (motivo None); S_f 1.0985 g, S_r 1.1240 g, resolução 0.0016 g, R 8.39033937096706 (Rente aos cones), formas v43/v43
  M_RC_E: PUSH (motivo None); S_f 1.1013 g, S_r 1.1264 g, resolução 0.0012 g, R 8.39033937096706 (Rente aos cones), formas v43/v43
  LOOSE_PICO: PUSH (motivo None); S_f 1.1966 g, S_r 1.2098 g, resolução 0.0001 g, R 8 (Manual), formas v43/v43
  PUSH_PICO: PUSH (motivo None); S_f 1.1886 g, S_r 1.2215 g, resolução 0.0004 g, R 8 (Manual), formas v43/v43
  FRENTE_DESCOLADA: N/A (motivo 'Fz_FL = -19,1 N ≤ 0: descolamento, fora do domínio do modelo de transferência de carga (SUS-104) em a_y = 0,8 g'); S_f None, S_r None, resolução None, R 8 (Manual), formas v43/v43
  FX_ASSIM: N/A (motivo 'não satura até 2 g'); S_f None, S_r None, resolução None, R 8 (Manual), formas v43/v43
  H2V_0: PUSH (motivo None); S_f 1.0918 g, S_r 1.1220 g, resolução 0.0013 g, R 8 (Manual), formas v42/v43
  H9V_0: PUSH (motivo None); S_f 1.0946 g, S_r 1.1172 g, resolução 0.0012 g, R 8 (Manual), formas v43/v42
  CHAVE_H2V_2: N/A pelas entradas (chave h2v deve ser 0 ou 1)
  CHAVE_H2V_VAZIA: N/A pelas entradas (chave h2v deve ser 0 ou 1)
  CHAVE_H9V_TEXTO: N/A pelas entradas (chave h9v deve ser 0 ou 1)
  GEO_RB: N/A pelas entradas (geometria do centro da curva inválida (R ≤ b ou R_c ≤ t_f/2))
  GEO_RC: N/A pelas entradas (geometria do centro da curva inválida (R ≤ b ou R_c ≤ t_f/2))
  GEO_RB_ACK: N/A pelas entradas (L/R fora do alcance da geometria de Ackermann (SUS-414); revise o raio)
  GEO_RC_ACK: N/A pelas entradas (L/R fora do alcance da geometria de Ackermann (SUS-414); revise o raio)
  GEO_RB_H2V0: N/A pelas entradas (L/R fora do alcance da geometria de Ackermann (SUS-414); revise o raio)
  GEO_RC_H2V0: N/A pelas entradas (L/R fora do alcance da geometria de Ackermann (SUS-414); revise o raio)
  MODO_ERRADO: N/A pelas entradas (raio do skidpad R a confirmar (modo do R inválido (use Linha central, Rente aos cones ou Manual)))
  MODO_TEXTO: N/A pelas entradas (raio do skidpad R a confirmar (modo do R inválido (use Linha central, Rente aos cones ou Manual)))
  MODO_INV_H0: PUSH (motivo None); S_f 1.2146 g, S_r 1.2248 g, resolução 0.0013 g, R None (linha central), formas v43/v43
  DINT_VAZIO: N/A pelas entradas (raio do skidpad R a confirmar (diâmetros do skidpad a confirmar (D_ext > D_int > 0)))
  DEXT_LE_DINT: N/A pelas entradas (raio do skidpad R a confirmar (diâmetros do skidpad a confirmar (D_ext > D_int > 0)))
  RIN_LE_L: N/A (motivo 'não satura até 2 g'); S_f None, S_r None, resolução None, R 1.88931191852104 (Rente aos cones), formas v43/v43
  BITOLA_TR_VAZIA: N/A pelas entradas (Rear Track (t_R) (05_VEHICLE B8) a confirmar)
  MEIA_LARG_VAZIA: N/A (motivo 'não satura até 2 g'); S_f None, S_r None, resolução None, R 8.29649350120071 (Rente aos cones), formas v43/v43
  MANUAL_VAZIO_H2: N/A pelas entradas (raio do skidpad R a confirmar (R manual vazio: a confirmar))
  MANUAL_VAZIO_H0: PUSH (motivo None); S_f 1.2146 g, S_r 1.2248 g, resolução 0.0013 g, R None (Manual), formas v43/v43
  FATOR_05: N/A pelas entradas (fator da faixa do NEUTRO (24_CURVA B34) deve ser número ≥ 1)
  NEUTRO_43: NEUTRO (motivo None); S_f 1.2197 g, S_r 1.2201 g, resolução 0.0005 g, R 9.125 (Linha central), formas v43/v43
  RF3_43: PUSH (motivo None); S_f 1.8717 g, S_r 1.9999 g, resolução 0.0500 g, R 9.125 (Linha central), formas v43/v43
  MAIOR diferença relativa planilha × Python (libreoffice): 1.24e-11 (M_RC_E 18 aF); colunas novas: {'alfa': 1234, 'pico_F': 420, 'pico_R': 400, 'semF': 141}
[PASS] TC-WB43-004: V4.3 em fórmulas (24_CURVA, 16 a 20 e a mini-grade da 19) == caso_da_planilha_v43 + analise_par(formas=, fator_neutro=) + tabela_linear(formas=): grades 17/18 e mini-grade (aF, aR, fxr; capacidade, motivo, folga), K e ângulos, resumo, tempo de volta, R usado/motivo/θ/geometria/pior origem do R, E173, B48 e a aba 20; dois sentidos, três modos do R, LOOSE_PICO/PUSH_PICO, dianteira descolada, geometria, chaves, modo, diâmetros, R_in' <= L, Manual vazio, fator  0 divergência(s): []; recálculo (s) [12, 13, 12, 13, 13, 12, 12, 13, 12, 12, 12, 12, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 12, 11, 11, 12, 11, 12, 11, 12, 11, 12, 12]

--- Resumo ---
2 PASS, 0 FAIL, de 2 testes
```

</details>

<details><summary>tests/test_workbook_v4_3.py: stderr</summary>

```text
[executor] início 08:48:57, fim 09:11:13, 1335.2 s
```

</details>
