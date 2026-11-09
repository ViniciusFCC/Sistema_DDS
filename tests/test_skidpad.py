"""
Testes do módulo skidpad (raio do skidpad, incremento 7, Task 2; EDR-069, SUS-1009 a 1011).
TC-SKP-001: geometria do raio rente aos cones (centro da curva na linha do eixo traseiro, spec §3.2).
TC-SKP-002: entradas vazias, meia largura do .tir e modos do raio.
Roda como script: uv run python -X utf8 tests/test_skidpad.py
L, b e as bitolas abaixo são entradas SINTÉTICAS de teste, não do carro; o único dado com fonte é a meia largura do .tir
(WIDTH/2 = 0,0889 m, .tir TTC provisório) e os diâmetros do regulamento (FSAE Rules 2026 v1.0, D.10.1.1).
"""
import math
import os
import sys
from types import SimpleNamespace

import atualizar_planilha as ap
import skidpad as sk
import tire_model as tm

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import relatorio_escada as rel   # noqa: E402  (o ramo da bitola provisória mora em _raio_do_metodo)

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


# --- TC-SKP-001 ---------------------------------------------------------------------------------------------------
L, B, TF, TR, W = 1.53, 0.765, 1.3, 1.3, 0.0889      # SINTÉTICOS (L e b); bitolas e W do T11/.tir
D_INT = sk.D_INTERNO_M
a_ok = sk.raio_linha_central(15.25, 21.25) == 9.125 and (sk.D_INTERNO_M, sk.D_EXTERNO_M) == (15.25, 21.25)

r = sk.raio_rente_aos_cones(D_INT, L, B, TF, TR, W)
r_in = D_INT / 2 + W
d_tras = math.hypot(0.0, r.raio_c_m - TR / 2)          # roda interna traseira: x = 0
d_diant = math.hypot(L, r.raio_c_m - TF / 2)           # roda interna dianteira: x = L
b_ok = (r.eixo == "traseiro" and abs(d_tras - r_in) < 1e-12 and d_diant >= d_tras
        and abs(r.raio_m - math.hypot(B, r.raio_c_m)) < 1e-12 and r.motivo is None and not r.sem_meia_largura)

# (c) empate construído: t_r tal que os dois limites coincidem
t_r_emp = TF + 2 * (math.sqrt(r_in**2 - L**2) - r_in)
e = sk.raio_rente_aos_cones(D_INT, L, B, TF, t_r_emp, W)
# dianteiro manda: bitola traseira bem menor que a de empate
f = sk.raio_rente_aos_cones(D_INT, L, B, TF, t_r_emp - 0.2, W)
d_f = math.hypot(L, f.raio_c_m - TF / 2)
c_ok = e.eixo == "empate" and f.eixo == "dianteiro" and abs(d_f - r_in) < 1e-12 and f.raio_c_m > e.raio_c_m - 1e-12 - 0.0 \
    and abs(e.raio_c_m - (r_in + t_r_emp / 2)) < 1e-9

# (d) R_in' <= L: dianteira não restringe
g = sk.raio_rente_aos_cones(2.0, L, B, TF, TR, 0.0)     # R_in' = 1,0 < L
h = sk.raio_rente_aos_cones(2 * L, L, B, TF, TR, 0.0)   # R_in' = L exato: sqrt(0)
d_ok = (g.eixo == "traseiro" and abs(g.raio_c_m - (1.0 + TR / 2)) < 1e-12
        and h.eixo == "traseiro" and h.raio_c_m == L + TR / 2)
check("TC-SKP-001 geometria: linha central, rente aos cones (traseiro, dianteiro, empate) e R_in' <= L",
      a_ok and b_ok and c_ok and d_ok,
      f"(b) R_c={r.raio_c_m:.6f} m, R={r.raio_m:.6f} m, eixo={r.eixo}; (c) empate t_r={t_r_emp:.6f} m, eixo={e.eixo}, "
      f"R_c={e.raio_c_m:.6f}, dianteiro R_c={f.raio_c_m:.6f}; (d) R_c={g.raio_c_m:.4f} m, eixo={g.eixo}")

# --- TC-SKP-002 ---------------------------------------------------------------------------------------------------
vazio = sk.raio_rente_aos_cones(D_INT, L, B, TF, None, W)
sem_w = sk.raio_rente_aos_cones(D_INT, L, B, TF, TR, None)
com_0 = sk.raio_rente_aos_cones(D_INT, L, B, TF, TR, 0.0)
ds = tm.load_dataset(ap.TIR_PROVISORIO, source_axis_system=ap.EIXO_TIR)
w_tir = sk.meia_largura_do_tir(ds)
try:
    sk.meia_largura_do_tir(tm.TireDataset(p={}))
    sem_width = False
except ValueError as exc:
    sem_width = "WIDTH ausente no .tir" in str(exc)
args = dict(d_int=D_INT, d_ext=sk.D_EXTERNO_M, L=L, b=B, t_f=TF, t_r=TR, meia_largura=W)
try:
    sk.raio("outro", r_manual=None, **args)
    invalido = False
except ValueError:
    invalido = True
modos = (sk.raio("manual", r_manual=None, **args) == (None, "R manual vazio: a confirmar")
         and sk.raio("manual", r_manual=8.0, **args) == (8.0, None)
         and sk.raio("linha_central", r_manual=None, **args) == (9.125, None)
         and sk.raio("rente_aos_cones", r_manual=None, **args)[0] == r.raio_m)
# Ramo da bitola provisória do relatório (tools/relatorio_escada._raio_do_metodo; U3 do plano do inc. 7). O VehicleConfig
# recusa bitola <= 0, então o caso é um stand-in com a bitola traseira ausente (SINTÉTICO de teste; L, b e t_f como acima).
# Sem a bitola traseira entra a provisória do argumento (1,25 m de teste, rotulada), o R é o do skidpad com ela, e o texto a cita;
# com as duas bitolas no caso a provisória não entra (rótulos vazios).
caso_sem_tr = SimpleNamespace(cfg=SimpleNamespace(track_front=TF, track_rear=None, wheelbase=L, cg_to_rear=B),
                              ds=ds, raio_m=None)
caso_com_tr = SimpleNamespace(cfg=SimpleNamespace(track_front=TF, track_rear=TR, wheelbase=L, cg_to_rear=B),
                              ds=ds, raio_m=None)
R_pv, txt_pv, _, rot_pv = rel._raio_do_metodo(caso_sem_tr, "rente_aos_cones", 1.25)
R_esp = sk.raio("rente_aos_cones", d_int=D_INT, d_ext=sk.D_EXTERNO_M, L=L, b=B, t_f=TF, t_r=1.25, meia_largura=w_tir,
                r_manual=None)[0]
R_cd, _, _, rot_cd = rel._raio_do_metodo(caso_com_tr, "rente_aos_cones", 1.25)
bitola_pv = (R_pv == R_esp and rot_pv == ["t_r"] and "bitola provisória do T11 (t_r = 1,250 m" in txt_pv
             and rot_cd == [] and R_cd != R_pv)
ok2 = (vazio.raio_m is None and vazio.motivo == "bitola traseira vazia: R rente aos cones a confirmar"
       and sem_w.sem_meia_largura is True and sem_w.raio_m == com_0.raio_m
       and abs(w_tir - 0.0889) < 1e-12 and sem_width and invalido and modos
       and sk.ORIGEM_MEIA_LARGURA == "◐ Provisório (.tir TTC)" and sk.FONTE_DIAMETROS.endswith("D.10.1.1")
       and bitola_pv)
check("TC-SKP-002 entradas vazias, meia largura do .tir e modos",
      ok2, f"WIDTH/2={w_tir}; sem meia largura R={sem_w.raio_m}; modo inválido levanta={invalido}; bitola provisória: "
      f"R={R_pv:.4f} m (esperado {R_esp:.4f}), rótulos={rot_pv}, com a bitola no caso R={R_cd:.4f} m")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
