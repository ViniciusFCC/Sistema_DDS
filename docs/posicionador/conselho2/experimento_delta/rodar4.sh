#!/bin/bash
# Tudo ligado (δ ±25°, margem como objetivo, caixa dinâmica): 60 amostras, 4 refinos de 500; sementes 0 a 2.
cd /home/user/Sistema_DDS
E=docs/posicionador/conselho2/experimento_delta
for s in 0 1 2; do
  echo "uv run python -X utf8 tools/posicionar_atuacao.py --step data/cad/T11_chassi_2026-11-17.step --saida $E/t25_s${s} --amostras 60 --refinos 4 --aval-refino 500 --semente $s > $E/t25_s${s}.log 2>&1"
done | xargs -P 3 -I{} bash -c "{}"
echo FIM > $E/FIM4
