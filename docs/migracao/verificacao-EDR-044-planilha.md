# Verificação com o teste da planilha integrado (EDR-044)

Gerado por `tools/rodar_testes.py`. Não edite à mão: rode de novo.

## Ambiente (CA-10)

- Data: 2026-10-19T01:49:21
- Commit: `ddf1a03`
- Sistema: Windows-11-10.0.26300-SP0
- Python: 3.13.15 (C:\Users\vferr\Documents\Sistema_DDS\.venv\Scripts\python.exe)
- numpy 2.5.4, scipy 1.18.1, openpyxl 3.1.5 (fixados no `uv.lock`)
- Execução: `sys.executable -X utf8 <script>`, cwd=raiz do repositório, `PYTHONUTF8=1`
- Módulos importados de (PASS): `C:\Users\vferr\Documents\Sistema_DDS\python\tire_model.py`, `C:\Users\vferr\Documents\Sistema_DDS\python\suspension_model.py`, `C:\Users\vferr\Documents\Sistema_DDS\python\kinematics_model.py`, `C:\Users\vferr\Documents\Sistema_DDS\python\hardpoints.py`

## Resumo

| CA | Item | Status |
|---|---|---|
| CA-10 | módulos importados de python/ | **PASS** |
| CA-05 | pneu | **PASS** |
| CA-05 | oráculos | **PASS** |
| CA-05 | suspensão | **PASS** |
| CA-05 | cinemática | **PASS** |
| CA-05 | hardpoints | **PASS** |
| CA-06 | mutação | **PASS** |
| CA-07 | autoteste do comparador | **PASS** |
| CA-07 | planilha vs V2.4 entregue | **PASS** |
| CA-08 | layout vs entregue | **PASS** |
| versão | 00_README!A3 = versão no nome do arquivo | **PASS** |
| CA-09 | planilha Excel x Python | **PASS** |

## Testes (CA-05)

| Conjunto | Script | Esperado | Obtido | Código | Status | Fonte do esperado |
|---|---|---|---|---|---|---|
| pneu | `tests/test_tire_model.py` | 43 | 43 PASS, 0 FAIL, de 43 | 0 | **PASS** | registro-de-versoes-V2_4.md:16 |
| oráculos | `tests/test_tire_oracles.py` | 5 | 5 PASS, 0 FAIL, de 5 | 0 | **PASS** | registro-de-versoes-V2_4.md:16 |
| suspensão | `tests/test_suspension_model.py` | 42 | 42 PASS, 0 FAIL, de 42 | 0 | **PASS** | HANDOFF §6.2 |
| cinemática | `tests/test_kinematics_model.py` | 53 | 53 PASS, 0 FAIL, de 53 | 0 | **PASS** | HANDOFF §6.2 |
| hardpoints | `tests/test_hardpoints.py` | 35 | 35 PASS, 0 FAIL, de 35 | 0 | **PASS** | HANDOFF §6.2 |

## Mutação (CA-06)

- Esperado: 23/23 detectados, com a pré-checagem do original passando.
- Pré-checagem: PRE-CHECAGEM OK: original -> 43 PASS, 0 FAIL, de 43 testes
- Obtido: 23/23 detectados; código de saída 0
- Status: **PASS**

<details><summary>tests/mutation_tire.py: saída</summary>

```text
PRE-CHECAGEM OK: original -> 43 PASS, 0 FAIL, de 43 testes
DETECTADO      Ex sinal PEX4
DETECTADO      Ky PKY2*fz
DETECTADO      Bx sem Cx
DETECTADO      SVx sem LMUX
DETECTADO      Gxa sem denominador
DETECTADO      Gyk sem denominador
DETECTADO      SVyk RVY5 sinal
DETECTADO      espelho esquerdo Fy
DETECTADO      faixa Fz
DETECTADO      camber PDY3
DETECTADO      mu_eff
DETECTADO      Ey sem min/sinal
DETECTADO      LKY ignorado
DETECTADO      PHY3 camber
DETECTADO      RVY3 camber
DETECTADO      kappa-range
DETECTADO      s_F removido (Fy sem inverter)
DETECTADO      s_alpha removido
DETECTADO      s_gamma removido
DETECTADO      SAE com sinais ISO
DETECTADO      espelho depois da transformacao
DETECTADO      loader aceita eixo None
DETECTADO      gamma SAE so s_g=+1
23 / 23
```

</details>

## Planilha regenerada (CA-07, CA-08)

- Autoteste do comparador (`tools/test_comparar_planilhas.py`): 10 PASS, 0 FAIL, de 10 (esperado 10): **PASS**
- Build: `python/build_workbook.py <tmp>/FSAE_EV_Suspension_Fase1_V2_4.xlsx --layout <tmp>/layout_V2_4.json`, código 0

<details><summary>build: stdout</summary>

```text
salvo C:\Users\vferr\AppData\Local\Temp\dds_build_zg5_4_98\FSAE_EV_Suspension_Fase1_V2_4.xlsx linhas 177 ref 1526.9250569300661 -1131.8643128749413 2.715269352685693
```

</details>

```text
fórmulas: entregue 347 | gerada 347 | esperado 347
células comparadas: 2042 | diferenças: 0
CA-07 PASS
diferenças no layout: 0
CA-08 PASS
```

## Versão gravada na planilha (fase B, passo 3)

A versão escrita em `00_README!A3` precisa ser a mesma do nome do arquivo.

- `excel/FSAE_EV_Suspension_Fase1_V2.1.xlsx`: A3 diz V2.1: **PASS**
- `excel/FSAE_EV_Suspension_Fase1_V2_4.xlsx`: A3 diz V2.4: **PASS**

## Teste da planilha (CA-09)

- `tests/test_workbook.py`: esperado 19 (registro-de-versoes-V2_4.md:17 (19/19 no sandbox)); obtido 19 PASS, 0 FAIL, de 19; código 0: **PASS**
- MOTOR: excel (Excel 16.0 via COM, PID 45112)

