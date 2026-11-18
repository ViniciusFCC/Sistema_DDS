"""
Testes do gabarito T.1.2 e do limite da AIP do posicionador (EDR-076, TC-POS-030 a 033).
Todas as cenas são SINTÉTICAS de teste (não do carro). A regra é a FSAE Rules 2027 V1.0, T.1.2 e F.8.6.1.
Roda como script: uv run python -X utf8 tests/test_posicionador_regulamento.py
"""
import numpy as np

from posicionador.geometria import Caixa
from posicionador.regulamento import gabarito_t12, limite_aip, trajetoria_t12

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def caixa(x0, x1, y0, y1, z0, z1):
    """Caixa alinhada aos eixos (SINTÉTICA) com os limites dados."""
    return Caixa(np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]), np.eye(3),
                 np.array([(x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2]))


# --- TC-POS-030 ---
g = gabarito_t12()
larg = g[:, 0].max() - g[:, 0].min()
alt = g[:, 1].max() - g[:, 1].min()
x, y = g[:, 0], g[:, 1]
area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
d = np.roll(g, -1, axis=0) - g
cruz = d[:, 0] * np.roll(d, -1, axis=0)[:, 1] - d[:, 1] * np.roll(d, -1, axis=0)[:, 0]
convexo = bool(np.all(cruz > 0) or np.all(cruz < 0))
esp = 0.350 ** 2 - 4 * (0.05 ** 2 / 2)
check("TC-POS-030 gabarito T.1.2: 0,350 x 0,350 m, chanfros 0,050 m, convexo",
      g.shape == (8, 2) and abs(larg - 0.35) < 1e-12 and abs(alt - 0.35) < 1e-12 and abs(area - esp) < 1e-12 and convexo,
      f"larg={larg} alt={alt} área={area:.6f} (esperada {esp:.6f}) convexo={convexo}")

# --- TC-POS-031 ---
args = dict(x_ini=0.0, x_fim=1.0, z_min=0.0, z_max=0.6)
r0 = trajetoria_t12([], **args)
# bloqueia toda a faixa de z em x = 0,5 (SINTÉTICO)
r1 = trajetoria_t12([caixa(0.49, 0.51, -1, 1, -1, 2)], **args)
# metade de baixo bloqueada em x 0,2-0,4 e metade de cima em x 0,6-0,8 (SINTÉTICO): sobe-e-desce, sem sobreposição em x
bai = caixa(0.2, 0.4, -1, 1, 0.0, 0.45)
alt_ = caixa(0.6, 0.8, -1, 1, 0.35, 2.0)
r2 = trajetoria_t12([bai, alt_], **args)
zs = r2.caminho_z
ok_alt = (r2.livre is True and len(zs) > 0 and max(zs) - min(zs) > 0.05)
check("TC-POS-031 altura livre: sem obstáculo, parede total, escada em z",
      r0.livre is True and r1.livre is False and ok_alt,
      f"vazio={r0.livre}, parede={r1.livre} ({r1.motivo}), escada={r2.livre} z de {min(zs, default=float('nan')):.3f} "
      f"a {max(zs, default=float('nan')):.3f}")

# --- TC-POS-032 ---
r3 = trajetoria_t12([], 0.0, None, 0.0, 0.6)
r4 = trajetoria_t12([], None, 1.0, 0.0, 0.6)
check("TC-POS-032 posição da coluna/pedal a confirmar -> NÃO VERIFICÁVEL",
      r3.livre is None and r3.motivo.startswith("NÃO VERIFICÁVEL")
      and r4.livre is None and r4.motivo.startswith("NÃO VERIFICÁVEL"), f"{r3.motivo} | {r4.motivo}")

# --- TC-POS-033 ---
f = limite_aip(0.49)
a, b = f(np.array([0.48, 0.1, 0.2])), f(np.array([0.50, 0.1, 0.2]))
fn = limite_aip(None)
check("TC-POS-033 limite da AIP: folga em X (F.8.6.1)",
      abs(a - 0.01) < 1e-12 and abs(b + 0.01) < 1e-12 and np.allclose(f(np.array([[0.48, 0, 0], [0.50, 0, 0]])), [0.01, -0.01])
      and fn is None, f"atrás={a}, à frente={b}, None={fn} (None = NÃO VERIFICÁVEL)")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
