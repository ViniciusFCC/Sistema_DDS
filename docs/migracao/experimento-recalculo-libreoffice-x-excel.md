# Experimento: recálculo da planilha com LibreOffice e com Excel

- Data: 2026-10-19
- Pedido do usuário: instalar o LibreOffice e rodar o teste da planilha com os dois
  motores, para entender as diferenças e o peso de trocar o LibreOffice pelo Excel
  (SPEC §11, passo 4).
- Situação: **experimento**. Nada foi integrado ao repositório; o `test_workbook.py`
  não foi editado e o EDR-044 ainda não existe (depende de autorização).

## Como foi feito

- Planilha: `excel/FSAE_EV_Suspension_Fase1_V2_4.xlsx` (sempre em cópias temporárias;
  o arquivo entregue não foi aberto para escrita).
- `tests/test_workbook.py` rodou **sem edição**. Um script de rascunho (fora do Git)
  interceptou só a chamada `python3 scripts/recalc.py <arquivo>` e a desviou para um
  dos dois motores; todos os checks e tolerâncias são os do teste original.
- **LibreOffice 26.8.1** (instalado pelo winget, pacote oficial da The Document
  Foundation): a mesma macro do `recalc.py` da skill xlsx (`calculateAll()` +
  `store()`), num perfil temporário. O `recalc.py` da skill não foi usado como está
  porque depende de recursos de Linux (shim de socket compilado com gcc).
- **Excel (Office 16)** via COM (`pywin32`, só num ambiente temporário do `uv`, fora
  do projeto): instância própria e invisível, `CalculateFull()` + `Save()`.
- Ambiente: CPython 3.13.15, numpy 2.5.4, scipy 1.18.1, openpyxl 3.1.5.

## Resultados

| | LibreOffice | Excel |
|---|---|---|
| `test_workbook.py` | **19/19** | **19/19** |
| Pior diferença relativa Excel×Python (TC-WB24-003b/004/004b/004d) | 3,5e-15 / 4,2e-15 / 4,1e-15 / 2,9e-15 | 2,0e-16 / 1,1e-15 / 7,9e-16 / 5,7e-16 |
| Erros de fórmula (#REF!, #VALUE!, …) | 0 de 347 | 0 de 347 |
| Tempo por recálculo (17 recálculos) | 6,3 s | 0,9 s |

O 19/19 registrado no sandbox (`registro-de-versoes-V2_4.md:17`) foi **reproduzido
com os dois motores**. A tolerância do teste é 1e-6 relativa; as diferenças estão
nove ordens de grandeza abaixo dela.

Comparação direta LibreOffice × Excel, célula a célula, na planilha entregue
recalculada (347 fórmulas):

- 318 resultados numéricos: 64 idênticos bit a bit; diferença relativa máxima
  **4,0e-15** (absoluta 5,1e-11); nenhum acima de 1e-12.
- 29 resultados não numéricos (textos de status, N/A): **todos iguais**.
- O arquivo entregue não guarda valores calculados (as 347 fórmulas estão sem cache;
  o build marca `fullCalcOnLoad`): quem abre a planilha vê os valores calculados pelo
  próprio Excel na hora.

## Leitura

- As diferenças entre os motores são de arredondamento em ponto flutuante (ordem de
  1e-15), sem efeito em nenhum critério. Trocar o motor não muda nenhum resultado de
  engenharia.
- O Excel é ~7 vezes mais rápido e é o programa que a equipe usa; o LibreOffice roda
  em qualquer sistema (inclusive num CI Linux) e é o motor do resultado original.
- O que pesa na decisão é operacional: o Excel exige Windows com Office e o `pywin32`;
  o LibreOffice exige a instalação dele (~350 MB) e é mais lento.

## Não verificado

- O `recalc.py` exato usado no sandbox em 2026-10-14 (a skill pode ter mudado desde
  então); aqui foi usada a mesma macro, não o mesmo arquivo.
- Comportamento com outras versões do Excel ou do LibreOffice.
