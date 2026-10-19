# python/

Módulos com nomes estáveis (EDR-043): `tire_model`, `suspension_model`,
`kinematics_model`, `hardpoints` e o `build_workbook` da planilha. A versão do
projeto é a tag do Git (o `version` do `pyproject.toml` acompanha a última tag). O
`uv sync` instala o projeto em modo editável, com esta pasta no caminho de import, e
é assim que os testes em `tests/` acham os módulos. O primeiro `uv sync` precisa de
rede para baixar o hatchling. O caminho gravado no `.pth` é absoluto: numa cópia da
pasta, rode pelo `uv run` (que o refaz), não pelo `.venv\Scripts\python.exe` direto.

Os docstrings e os textos gravados nas células da planilha ainda citam os nomes
antigos (`tire_model_V2_4.py` etc.) de propósito: mudar os textos de células altera
a planilha gerada e quebra a igualdade com a V2.4 entregue (CA-07).

    uv run python -X utf8 tests/<script>.py
    uv run python -X utf8 python/build_workbook.py [saída.xlsx]   (padrão: build/)
    uv run python -X utf8 python/atualizar_planilha.py [V2_4.xlsx] [V2_5.xlsx] [--registro arq.md]

A planilha vigente é a V2.5: o `build_workbook` gera a V2.4 e o `atualizar_planilha`
aplica sobre ela as mudanças da revisão metodológica (EDR-045 a EDR-049), uma célula de
cada vez, listadas em `alteracoes()` com a fonte. Nenhum dos dois recalcula ou salva a
planilha pelo Excel ou pelo LibreOffice.

Os testes são scripts com `check()`, não pytest. O resumo de cada um é a linha
final `N PASS, M FAIL, de T testes`. O `tests/test_workbook.py` recalcula cópias da
planilha pelo Excel (COM, `pywin32` no grupo de desenvolvimento) ou pelo LibreOffice
(EDR-044).

## Arquivo `.tir` (fora do Git)

`data/Hoosier_R25B_13x7_TTC_provisional.tir` não é versionado (SPEC D4: dados do TTC,
termos de uso não verificados). Num clone novo, copie-o para `data/` antes de rodar
os testes de pneu e de oráculos, a mutação e o build da planilha (SPEC P3); sem ele,
esses itens falham com `FileNotFoundError`.

- Onde está: `importado-claude-ai/saidas-conversas/tire/` e o backup zip na
  OneDrive (`importado-claude-ai_Sistema_DDS_2026-10-18.zip`).
- SHA-256 esperado: `f3bc80fda4145d53da06f69c8c0fcffbddfbbf73f4aab4149e1caa386c77c796`
  (igual ao `cleaned_file_sha256` do `.meta.json` e ao `MANIFEST.sha256`).
- Proveniência contraditória, não resolvida (SPEC P4): o `.meta.json` registra a
  cadeia "TTC -> Stackpole -> terceiro -> usuário", e o histórico gravado por
  `build_workbook.py` (célula C15 do histórico de versões; linha 422 do original
  importado, tag `v2.4.0-import`) diz "baixados direto do TTC".
