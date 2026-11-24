#!/bin/bash
# Controle com o mesmo orçamento: busca com STEP, 100 amostras e 10 refinos, δ travado (0) × δ livre (±25°), sementes 0 a 2.
cd /home/user/Sistema_DDS
E=docs/posicionador/conselho2/experimento_delta
for d in 0 25; do for s in 0 1 2; do
  echo "uv run python -X utf8 tools/posicionar_atuacao.py --step data/cad/T11_chassi_2026-11-17.step --saida $E/d${d}_s${s} --amostras 100 --refinos 10 --semente $s --delta-max $d > $E/d${d}_s${s}.log 2>&1"
done; done | xargs -P 3 -I{} bash -c "{}"
echo FIM > $E/FIM
