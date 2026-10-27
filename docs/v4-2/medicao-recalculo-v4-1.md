# Medição do recálculo da V4.1 sem Excel residual

Gerado por `tools/medir_recalculo.py`. Não edite à mão: rode de novo.

- Data: 2026-10-26.
- Arquivo medido: v4.1:excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx (tag v4.1), em cópia temporária (SHA-256 `4193ffc5a8dffe824e0fae18a2c53d65117bf51a1956d22cb24c40cf355fdd3b`). A planilha de `excel/` e a viva do Drive não foram abertas.
- Motor: Excel 16.0 via COM; Windows 10.0.26300; Python 3.13.17.
- Execuções: 3, cada uma numa instância nova do Excel (invisível, alertas desligados).

## Tempos por execução (segundos)

| Execução | Abrir | CalculateFull | Gravar | Fechar | Total | Instância saiu |
|---|---|---|---|---|---|---|
| 1 | 7,96 | 0,20 | 5,72 | 0,38 | 14,26 | sim |
| 2 | 1,22 | 0,04 | 1,25 | 1,52 | 4,03 | sim |
| 3 | 1,16 | 0,03 | 1,11 | 0,35 | 2,65 | sim |
| Mediana | 1,22 | 0,04 | 1,25 | 0,38 | 4,03 | |

## Processos EXCEL.EXE

- Antes da medição: 0.
- Depois da medição: 0.
- Diferença: +0. Nenhuma instância da ferramenta ficou viva.
- A ferramenta confere o PID de cada instância depois do `Quit` e nunca encerra processo por nome.

## Limites

- Os tempos são desta máquina e desta sessão (outros programas abertos mudam o resultado); só a ordem de grandeza vale.
- Mede o Excel via COM; o LibreOffice não entra (CLAUDE.md: não recalcular a planilha por ele).
