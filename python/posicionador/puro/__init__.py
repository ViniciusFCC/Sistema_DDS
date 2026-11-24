"""
Núcleo do posicionador em Python puro (só biblioteca padrão: math, random, csv, json), para rodar no Python embutido do
Autodesk Fusion (3.14, sem numpy nem scipy; docs/posicionador/fusion/RELATORIO-investigacao.md, seção 4).

Cada módulo daqui reproduz o módulo de mesmo nome do pacote `posicionador` (numpy/scipy), que continua sendo a
referência de comportamento: os testes `tests/test_posicionador_puro_*.py` comparam os dois nos mesmos dados.
Vetores são tuplas de 3 floats; matrizes 3x3 são tuplas de 3 tuplas; nada importa `numpy`, `scipy` nem `adsk`.
"""
