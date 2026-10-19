# python/

Módulos com nomes estáveis (EDR-043): `tire_model`, `suspension_model`,
`kinematics_model`, `hardpoints` e o `build_workbook` da planilha. A versão vem da
tag do Git. O `uv sync` instala o projeto em modo editável, com esta pasta no
caminho de import, e é assim que os testes em `tests/` acham os módulos.

    uv run python -X utf8 tests/<script>.py
    uv run python -X utf8 python/build_workbook.py [saída.xlsx]   (padrão: build/)

Os testes são scripts com `check()`, não pytest. O resumo de cada um é a linha
final `N PASS, M FAIL, de T testes`. O `tests/test_workbook.py` não roda
localmente (depende de LibreOffice e de `/mnt/skills`; SPEC D2).

## Arquivo `.tir` (fora do Git)

`data/Hoosier_R25B_13x7_TTC_provisional.tir` não é versionado (SPEC D4: dados do TTC,
termos de uso não verificados). Sem ele, os testes de pneu e o build da planilha
não rodam num clone novo (SPEC P3).

- Onde está: `importado-claude-ai/saidas-conversas/tire/` e o backup zip na
  OneDrive (`importado-claude-ai_Sistema_DDS_2026-10-18.zip`).
- SHA-256 esperado: `f3bc80fda4145d53da06f69c8c0fcffbddfbbf73f4aab4149e1caa386c77c796`
  (igual ao `cleaned_file_sha256` do `.meta.json` e ao `MANIFEST.sha256`).
- Proveniência contraditória, não resolvida (SPEC P4): o `.meta.json` registra a
  cadeia "TTC -> Stackpole -> terceiro -> usuário", e o histórico gravado por
  `build_workbook.py` (antes `build_workbook_V2_4.py`, linha 422) diz "baixados
  direto do TTC".
