"""Conferência única do pneu-1 (EDR-075, TC-SEN-009): o caso montado do JSON demonstrativo é o caso que a planilha V4.4
calcula. Script com check(), não pytest. Não roda na suíte da entrega: fica pronto para uma conferência única.

Uso: DDS_COPIA_V44_RECALC=<cópia recalculada da V4.4> DDS_TTC_DIR=<pasta dos .tir> \
     uv run python -X utf8 tests/test_caso_pneu1_equivalencia.py

Compara `caso_pneu1.caso_de_dados(ler_caso(demonstrativo))` com `caso_planilha.caso_da_planilha_v43(copia, tir12,
passo1=...)`, com o mesmo passo1 que caso_de_dados escolhe: `cfg` campo a campo com tolerância relativa de 1e-12 (os
res_ do JSON são recalculados em Python, e a ordem das contas pode mudar o último bit), o resto exato. O `ds` é
comparado pelos coeficientes (`p`), pelas strings e pelo sistema de eixos; o rótulo `source` difere de propósito
(caso_pneu1.FONTE_CASO × "caso da planilha V4.3"). Também confere as formas e o fator do NEUTRO (24_CURVA B34).

A cópia precisa ser uma CÓPIA recalculada (Excel ou LibreOffice, EDR-044) da V4.4 com os mesmos dados da captura;
nunca a planilha viva nem a de referência de excel/ (este script só lê). Sem DDS_COPIA_V44_RECALC, ou sem os .tir:
NÃO EXECUTÁVEL, código 3, que nunca conta como aprovado. "Passou" = o JSON reproduz a planilha; não é validação física.
"""
from __future__ import annotations

import dataclasses
import math
import os
from pathlib import Path

import caso_planilha as cpl
import caso_pneu1 as cp

results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL"))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def nao_executavel(motivo: str):
    print(f"NÃO EXECUTÁVEL: {motivo} Não conta como aprovado.")
    raise SystemExit(3)


copia = os.environ.get("DDS_COPIA_V44_RECALC")
if not copia:
    nao_executavel("defina DDS_COPIA_V44_RECALC com uma cópia recalculada da V4.4 (TC-SEN-009).")
if not Path(copia).is_file():
    nao_executavel(f"DDS_COPIA_V44_RECALC={copia} não é um arquivo.")
if cp.achar_ttc() is None:
    nao_executavel(f"TC-SEN-009 precisa dos .tir do TTC Round 6 (defina DDS_TTC_DIR ou coloque-os em "
                   f"{cp.SUBDIR_TTC.as_posix()}).")

FAM = cp.familia_ttc()
TIR12 = FAM.at_pressure(cp.PRESSAO_DO_CASO_PSI).source_path
dados = cp.ler_caso(cp.CAMINHO_DEMONSTRATIVO)
montado = cp.caso_de_dados(dados, FAM)
passo1 = cp.ROTULO_SEM_ROLL_STEER not in montado.rotulos      # o mesmo passo1 que caso_de_dados escolheu
caso_pl, formas_pl = cpl.caso_da_planilha_v43(Path(copia), TIR12, passo1=passo1)
fator_pl = cpl.fator_neutro_da_planilha(Path(copia))

c_js, c_pl = montado.caso, caso_pl
dif_cfg = [f.name for f in dataclasses.fields(c_js.cfg)
           if not math.isclose(getattr(c_js.cfg, f.name), getattr(c_pl.cfg, f.name), rel_tol=1e-12, abs_tol=0.0)]
dif_resto = [f.name for f in dataclasses.fields(c_js) if f.name not in ("cfg", "ds")
             and getattr(c_js, f.name) != getattr(c_pl, f.name)]
dif_ds = [n for n in ("p", "strings", "axis_system") if getattr(c_js.ds, n) != getattr(c_pl.ds, n)]
dif_p = sorted(k for k in set(c_js.ds.p) | set(c_pl.ds.p) if c_js.ds.p.get(k) != c_pl.ds.p.get(k))
check("TC-SEN-009 caso do JSON demonstrativo = caso da cópia recalculada da V4.4 (cfg 1e-12, resto exato)",
      not dif_cfg and not dif_resto and not dif_ds and montado.formas == formas_pl and montado.fator_neutro == fator_pl,
      f"passo1={passo1}, cfg={dif_cfg}, resto={dif_resto}, ds={dif_ds}, coeficientes={dif_p[:10]}, "
      f"formas={montado.formas}/{formas_pl}, fator={montado.fator_neutro}/{fator_pl}")

print("\n--- Resumo ---")
n = sum(1 for _, s in results if s == "PASS")
f = len(results) - n
print(f"{n} PASS, {f} FAIL, de {len(results)} testes")
if f:
    raise SystemExit(1)
