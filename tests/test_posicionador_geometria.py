"""
Testes da geometria por distância com sinal do posicionador (EDR-076, TC-POS-010 a 014).
Todos os valores são SINTÉTICOS de teste (não do carro), exceto o raio interno 0,158 m do aro de 13", usado só como exemplo.
Roda como script: uv run python -X utf8 tests/test_posicionador_geometria.py
"""
import numpy as np

from posicionador.geometria import Barril, Caixa, Capsula, Esfera, dist_seg_seg, folga_segmento

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def P(*xs):
    return np.array([xs], dtype=float)


# --- TC-POS-010 ---
cap = Capsula(np.array([0, 0, 0.]), np.array([1, 0, 0.]), 0.1)
cx = Caixa(np.zeros(3), np.eye(3), np.array([0.5, 0.5, 0.5]))
es = Esfera(np.array([1., 2., 3.]), 0.5)
e = [abs(cap.sdf(P(0.5, 0.3, 0))[0] - 0.2), abs(cap.sdf(P(0.5, 0, 0))[0] + 0.1),
     abs(cx.sdf(P(1, 0, 0))[0] - 0.5), abs(cx.sdf(P(0, 0, 0))[0] + 0.5),
     abs(es.sdf(P(1, 2, 5))[0] - 1.5), abs(es.sdf(P(1, 2, 3))[0] + 0.5)]
check("TC-POS-010 sdf analítica de cápsula, caixa e esfera", max(e) < 1e-12, f"erro máx={max(e):.2e}")

# --- TC-POS-011 ---
rng = np.random.default_rng(20261117)
s = np.linspace(0, 1, 2001)


def bruta(p1, q1, p2, q2):
    A = p1 + np.outer(s, q1 - p1)
    B = p2 + np.outer(s, q2 - p2)
    d2 = ((A[:, None, :] - B[None, :, :]) ** 2).sum(-1)
    return float(np.sqrt(d2.min()))


erros = []
for _ in range(50):
    p1, q1, p2, q2 = rng.uniform(-1, 1, (4, 3))
    erros.append(abs(dist_seg_seg(p1, q1, p2, q2) - bruta(p1, q1, p2, q2)))
cruz = dist_seg_seg(np.array([-1, 0, 0.]), np.array([1, 0, 0.]), np.array([0, -1, 0.]), np.array([0, 1, 0.]))
check("TC-POS-011 dist_seg_seg contra força bruta e cruzamento", max(erros) < 1e-6 and cruz == 0.0,
      f"erro máx={max(erros):.2e}; cruzando={cruz}")

# --- TC-POS-012 ---
bar = Barril(np.zeros(3), np.array([0, 1., 0]), 0.158, 0.1)
v = bar.sdf(np.array([[0, 0, 0.], [0.2, 0, 0], [0.2, 0.15, 0]]))
check("TC-POS-012 barril oco: livre no eixo, material no aro, fora axial",
      abs(v[0] - 0.158) < 1e-12 and v[1] < 0 and abs(v[2] - 0.05) < 1e-12, f"sdf={v}")

# --- TC-POS-013 ---
cx1 = Caixa(np.zeros(3), np.eye(3), np.array([0.5, 0.5, 0.5]))
f_in = folga_segmento(cx1, np.array([-0.1, 0, 0.]), np.array([0.1, 0.05, 0]), 0.0)
check("TC-POS-013 interior da caixa: sdf=-0,5 e folga negativa",
      abs(cx1.sdf(P(0, 0, 0))[0] + 0.5) < 1e-12 and f_in < 0, f"folga={f_in:.4f}")

# --- TC-POS-014 ---
viol, difmax = 0, 0.0
for _ in range(200):
    a, b, c = rng.uniform(-1, 1, (3, 3))
    d = rng.uniform(-1, 1, 3)
    r_c, r_s = rng.uniform(0.01, 0.1), rng.uniform(0, 0.05)
    exata = dist_seg_seg(a, b, c, d) - r_c - r_s
    f = folga_segmento(Capsula(c, d, r_c), a, b, r_s, passo=0.002)
    if f > exata + 1e-9:
        viol += 1
    difmax = max(difmax, exata - f)
check("TC-POS-014 folga_segmento conservadora e dentro de passo", viol == 0 and difmax <= 0.002,
      f"violações={viol}; diferença máx={difmax:.2e}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s_, _ in results if s_ == "PASS")
n_fail = sum(1 for _, s_, _ in results if s_ == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
