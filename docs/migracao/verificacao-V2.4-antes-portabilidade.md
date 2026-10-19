# Verificação da V2.4 antes da portabilidade (originais, commit 0)

Gerado por `tools/rodar_testes.py`. Não edite à mão: rode de novo.

## Ambiente (CA-10)

- Data: 2026-10-18T22:02:59
- Commit: `16cd4f0`
- Sistema: Windows-11-10.0.26300-SP0
- Python: 3.13.15 (C:\Users\vferr\Documents\Sistema_DDS\.venv\Scripts\python.exe)
- numpy 2.5.4, scipy 1.18.1, openpyxl 3.1.5 (fixados no `uv.lock`)
- Execução: `sys.executable -X utf8 <script>`, cwd=`python/`, `PYTHONUTF8=1`

## Resumo

| CA | Item | Status |
|---|---|---|
| CA-05 | pneu | **PASS** |
| CA-05 | oráculos | **PASS** |
| CA-05 | suspensão | **FAIL** |
| CA-05 | cinemática | **PASS** |
| CA-05 | hardpoints | **PASS** |
| CA-06 | mutação | **FAIL** |
| CA-07 | planilha vs V2.4 entregue | **FAIL** |
| CA-08 | layout vs entregue | **FAIL** |
| CA-09 | test_workbook_V2_4.py | **NÃO EXECUTÁVEL** |

## Testes (CA-05)

| Conjunto | Script | Esperado | Obtido | Código | Status | Fonte do esperado |
|---|---|---|---|---|---|---|
| pneu | `test_tire_model_V2_4.py` | 43 | 43 PASS, 0 FAIL, de 43 | 0 | **PASS** | registro-de-versoes-V2_4.md:16 |
| oráculos | `test_tire_oracles_V2_4.py` | 5 | 5 PASS, 0 FAIL, de 5 | 0 | **PASS** | registro-de-versoes-V2_4.md:16 |
| suspensão | `test_suspension_model_V2_1.py` | 42 | 41 PASS, 0 FAIL, de 41 | 0 | **FAIL** | HANDOFF §6.2 |
| cinemática | `test_kinematics_model_V2_1.py` | 53 | 53 PASS, 0 FAIL, de 53 | 0 | **PASS** | HANDOFF §6.2 |
| hardpoints | `test_hardpoints_V2_1.py` | 35 | 35 PASS, 0 FAIL, de 35 | 0 | **PASS** | HANDOFF §6.2 |

## Mutação (CA-06)

- Esperado: 23/23 detectados, com a pré-checagem do original passando.
- Pré-checagem: AUSENTE (o script não verifica o original)
- Obtido: 23/23 detectados; código de saída 0
- Status: **FAIL**

<details><summary>mutation_tire_V2_4.py: saída</summary>

```text
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

- Build: `build_workbook_V2_4.py <tmp>/FSAE_EV_Suspension_Fase1_V2_4.xlsx --layout <tmp>/layout_V2_4.json`, código 1

<details><summary>build: stderr (final)</summary>

```text
Traceback (most recent call last):
  File "C:\Users\vferr\Documents\Sistema_DDS\python\build_workbook_V2_4.py", line 11, in <module>
    ds = t.load_dataset(TIR, source_axis_system="SAE_CALSPAN")
  File "C:\Users\vferr\Documents\Sistema_DDS\python\tire_model_V2_4.py", line 98, in load_dataset
    p, s = parse_tir(path)
           ~~~~~~~~~^^^^^^
  File "C:\Users\vferr\Documents\Sistema_DDS\python\tire_model_V2_4.py", line 48, in parse_tir
    with open(path, encoding="utf-8") as f:
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/claude/work/Hoosier_R25B_13x7_TTC_provisional.tir'
```

</details>

```text
CA-07 FAIL: build não gerou a planilha
CA-08 FAIL: build não gerou o layout
```

## Teste da planilha (CA-09)

- `test_workbook_V2_4.py`: **NÃO EXECUTÁVEL**. depende de LibreOffice e de `/mnt/skills/public/xlsx/scripts/recalc.py` (linhas 10 e 28, chamado com `python3`), que não existem nesta máquina (SPEC D2). Na fase A ele nunca conta como aprovado (R6). Resultado registrado no sandbox: 19/19 (registro-de-versoes-V2_4.md:17), não reproduzido aqui.

