#!/bin/bash
# Refino fundo: 60 amostras, 4 refinos de até 500 avaliações; δ travado × livre; sementes 0 a 2.
cd /home/user/Sistema_DDS
E=docs/posicionador/conselho2/experimento_delta
for d in 0 25; do for s in 0 1 2; do
  echo "uv run python -X utf8 tools/posicionar_atuacao.py --step data/cad/T11_chassi_2026-11-17.step --saida $E/f${d}_s${s} --amostras 60 --refinos 4 --aval-refino 500 --semente $s --delta-max $d > $E/f${d}_s${s}.log 2>&1"
done; done | xargs -P 3 -I{} bash -c "{}"
echo FIM > $E/FIM
