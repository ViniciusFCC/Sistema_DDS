"""
Testes das melhorias do conselho 2 (EDR-076): δ do push rod, margem como objetivo e convergência por valor (TC-POS-090 a 093).
TC-POS-090: δ = 0 reproduz a construção anterior (mesmos pontos); δ ≠ 0 move PUSH_IN mantendo |PUSH_IN − pivô| = r1, MR(0) = 1,40.
TC-POS-091: `busca.faixas` só tem 8ª variável com delta_max > 0, e `variaveis_de`/`_x_de` fazem a ida e volta de δ.
TC-POS-092: `busca.margem_normalizada` ignora MR(0) e o comprimento máximo (fixados pela construção) e dá a menor folga/|limite|.
TC-POS-094: busca com caixa dinâmica: 2 caixas em volta da elite, mesmo nº de amostras, determinística; sem ela, nenhuma caixa.
TC-POS-093: `varredura._erro_de_valor` marca como indeterminada só a restrição OK cuja folga é menor que a diferença n × 2n.
Entradas SINTÉTICAS de teste (restrições montadas à mão), exceto o ponto da v20 (origem_v20_script.json).
Roda como script: uv run python -X utf8 tests/test_posicionador_melhorias.py
"""
import json
import os

import numpy as np

import hardpoints as hp
from posicionador import busca as bu
from posicionador import config as pc
from posicionador import mecanismo as mec
from posicionador import varredura as vr

DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "posicionador")
results = []


def check(name, condition, detail=""):
    results.append((name, "PASS" if condition else "FAIL", detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}  {detail}")


hs = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"), os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
with open(os.path.join(DADOS, "origem_v20_script.json"), encoding="utf-8") as f:
    x = json.load(f)["x_semente"]
v0 = mec.Variaveis.da_semente_do_script(x)
vd = mec.Variaveis(v0.pivo_m, v0.az_rad, v0.el_rad, v0.r1_m, v0.phi_b_rad, delta_rad=np.radians(-8.0))
c0, cn = mec.construir(hs, v0, cfg), mec.construir(hs, vd, cfg)
c00 = mec.construir(hs, mec.Variaveis(v0.pivo_m, v0.az_rad, v0.el_rad, v0.r1_m, v0.phi_b_rad, delta_rad=0.0), cfg)
ok = c0.hardpoints is not None and cn.hardpoints is not None
if ok:
    p = lambda c, k: c.hardpoints.points[f"FL_{k}"].xyz
    igual = all(np.allclose(p(c0, k), p(c00, k), atol=0, rtol=0) for k in ("PUSH_OUT", "PUSH_IN", "SPRING_CHASSIS"))
    r1 = float(np.linalg.norm(p(cn, "PUSH_IN") - p(cn, "ROCKER_AXIS_A")))
    mudou = float(np.linalg.norm(p(cn, "PUSH_IN") - p(c0, "PUSH_IN")))
    import kinematics_model as km
    mr0 = km.motion_ratio(km.Corner(cn.hardpoints, "FL"), 0.0)["mr_wheel_per_spring"]
    ok = igual and abs(r1 - v0.r1_m) < 1e-9 and mudou > 1e-3 and abs(mr0 - cfg.valor("mr_alvo")) < 1e-6
check("TC-POS-090 δ = 0 igual ao anterior; δ ≠ 0 gira PUSH_IN a r1 constante e MR(0) = alvo", ok,
      f"r1 {r1 * 1e3:.4f} mm; PUSH_IN moveu {mudou * 1e3:.2f} mm; MR(0) {mr0:.6f}" if ok else f"{c0.motivo} {cn.motivo}")

caixa = (np.array([-0.15, 0.0, 0.1]), np.array([0.15, 0.3, 0.5]))
f7, f8 = bu.faixas(cfg, caixa), bu.faixas(cfg, caixa, np.radians(25.0))
xv = np.append(0.5 * (f8.lo[:7] + f8.hi[:7]), np.radians(10.0))
v8 = bu.variaveis_de(xv, f8)
volta = bu._x_de(v8, f8)
check("TC-POS-091 8ª variável só com delta_max > 0; ida e volta de δ", len(f7.lo) == 7 and len(f8.lo) == 8
      and abs(v8.delta_rad - np.radians(10.0)) < 1e-12 and len(volta) == 8 and abs(volta[7] - np.radians(10.0)) < 1e-12
      and bu.variaveis_de(xv[:7], f7).delta_rad == 0.0, f"δ = {np.degrees(v8.delta_rad):.2f}°")


def R(nome, valor, limite, folga, estado="OK"):
    return vr.Restricao(nome, valor, limite, folga, estado, "META", "teste")


def aval(rs):
    return vr.Avaliacao(rs, "CONDICIONAL", None, {}, {}, 11)


a = aval([R("MR(0)", 1.4, (1.39, 1.41), 0.0), R("comprimento do amortecedor (máximo)", 0.21, 0.21, 1e-9),
          R("comprimento do amortecedor (mínimo)", 0.1491, 0.149, 0.0001), R("braço r2 (amortecedor)", 0.07, (0.055, 0.08), 0.01)])
m = bu.margem_normalizada(a)
check("TC-POS-092 margem ignora as restrições fixadas pela construção", abs(m - min(0.0001 / 0.149, 0.01 / 0.08)) < 1e-12
      and bu.margem_normalizada(aval([R("MR(0)", 1.4, (1.39, 1.41), 0.0)])) == float("inf"), f"margem {m:.3e}")

n1 = aval([R("a", 1, 1, 0.0050), R("b", 1, 1, 0.00100), R("c", 1, 1, -0.1, "VIOLADA")])
n2 = aval([R("a", 1, 1, 0.0050), R("b", 1, 1, 0.00099), R("c", 1, 1, -0.1, "VIOLADA")])
n3 = aval([R("a", 1, 1, 0.0050), R("b", 1, 1, 0.00001), R("c", 1, 1, -0.1, "VIOLADA")])
check("TC-POS-093 convergência por valor: indeterminada só se folga < |Δ folga|", vr._erro_de_valor(n1, n2) == []
      and vr._erro_de_valor(n1, n3) == ["b"], f"{vr._erro_de_valor(n1, n2)} {vr._erro_de_valor(n1, n3)}")

cena = vr.cena_sem_cad(cfg)
cx = (np.array([-0.15, 0.0, 0.2]), np.array([0.15, 0.33, 0.6]))
kw = dict(n_amostras=40, n_refinos=0, semente=3, passo_m=0.02, delta_max_rad=np.radians(20.0))
rd1 = bu.buscar(hs, cena, cfg, cx, caixa_dinamica=True, **kw)
rd2 = bu.buscar(hs, cena, cfg, cx, caixa_dinamica=True, **kw)
rf = bu.buscar(hs, cena, cfg, cx, caixa_dinamica=False, **kw)
cd = rd1.estatisticas["caixas_dinamicas"]
check("TC-POS-094 caixa dinâmica: 2 caixas, 40 amostras, determinística; sem ela nenhuma caixa",
      len(cd) == 2 and rd1.estatisticas["n_amostras"] == 40 and cd == rd2.estatisticas["caixas_dinamicas"]
      and rf.estatisticas["caixas_dinamicas"] == [] and hasattr(rd1.mapa, "folga_m") and all(c["hi_m"][0] > c["lo_m"][0] for c in cd),
      f"caixas: {[[round(t, 3) for t in c['lo_m']] for c in cd]}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = len(results) - n_pass
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail:
    raise SystemExit(1)
