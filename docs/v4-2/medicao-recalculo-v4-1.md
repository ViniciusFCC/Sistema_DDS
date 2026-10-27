# Medição do recálculo da V4.1 sem Excel residual

Gerado por `tools/medir_recalculo.py`. Não edite à mão: rode de novo.

- Data: 2026-10-26.
- Arquivo de origem: `v4.1:excel/FSAE_EV_Suspension_Fase1_V4_1.xlsx` (tag v4.1), SHA-256 `4193ffc5a8dffe824e0fae18a2c53d65117bf51a1956d22cb24c40cf355fdd3b`. A planilha de `excel/` e a viva do Drive não foram abertas.
- Motor: Excel 16.0 via COM; Windows 10.0.26300; Python 3.13.17.
- Núcleos lógicos (`os.cpu_count`): 20. Cálculo multithread do Excel: 20 threads (ligado). `Application.Calculation` lido com a pasta aberta: automático.
- Execuções: 3 por cenário, cada uma numa instância nova do Excel (invisível, alertas desligados) e sobre uma cópia nova do arquivo de origem do cenário.

## O que cada coluna mede

- Abrir: `Workbooks.Open`. No cenário A inclui o cálculo de carga (o arquivo pede `fullCalcOnLoad` e nenhuma fórmula tem valor em cache).
- CalculateFull: recálculo completo a quente, depois da carga.
- Gravar: `Workbook.Save`.
- Fechar: `Workbook.Close` mais `Application.Quit`.
- Total: soma das quatro colunas.
- A 1ª execução de cada cenário pode incluir o custo da partida a frio do Excel; esse custo não é separado.

## Cenário A: arquivo da tag (sem cache, com fullCalcOnLoad)

Estado do arquivo de origem, lido dele: `<calcPr calcId="124519" fullCalcOnLoad="1" />`; fórmulas com valor em cache: 0; fórmulas sem valor em cache: 117569.

| Execução | Abrir | CalculateFull | Gravar | Fechar | Total | Instância saiu |
|---|---|---|---|---|---|---|
| 1 | 10,94 | 0,29 | 3,01 | 0,46 | 14,69 | sim |
| 2 | 7,03 | 0,30 | 1,69 | 0,42 | 9,44 | sim |
| 3 | 8,10 | 0,30 | 2,15 | 0,42 | 10,98 | sim |
| Mediana | 8,10 | 0,30 | 2,15 | 0,42 | 10,98 | |

## Cenário B: arquivo já salvo pelo Excel (como a viva)

Origem: a cópia gravada pela 1ª execução do cenário A, copiada de novo a cada execução.
Estado do arquivo de origem, lido dele: `<calcPr calcId="191029"/>`; fórmulas com valor em cache: 117569; fórmulas sem valor em cache: 0.

| Execução | Abrir | CalculateFull | Gravar | Fechar | Total | Instância saiu |
|---|---|---|---|---|---|---|
| 1 | 1,26 | 0,04 | 1,05 | 0,29 | 2,64 | sim |
| 2 | 1,13 | 0,03 | 0,91 | 0,17 | 2,24 | sim |
| 3 | 1,18 | 0,04 | 0,90 | 0,57 | 2,68 | sim |
| Mediana | 1,18 | 0,04 | 0,91 | 0,29 | 2,64 | |

## Processos EXCEL.EXE

- Antes da medição: 0.
- Depois da medição: 0.
- Diferença: +0. Nenhuma instância da ferramenta ficou viva.
- A ferramenta confere o PID de cada instância depois do `Quit` (inclusive a da sondagem inicial) e nunca encerra processo por nome.

## Limites

- Os tempos são desta máquina e desta sessão (outros programas abertos mudam o resultado); só a ordem de grandeza vale.
- Mede o Excel via COM; o LibreOffice não entra (CLAUDE.md: não recalcular a planilha por ele).
