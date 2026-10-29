"""
Testes do estudo da faixa do NEUTRO (incremento 7, Task 6; spec §4.3; EDR-065 item 2). O estudo não muda a regra.
TC-NEU-001: no caso V4.2 sintético (veiculo_base de tests/test_escada.py, pneu de escala LMUY 0,5, R = 8,5 m,
downforce 400 N com 45 % na frente):
  (a) as grades h, h/2, h/4 e h/8 são aninhadas (a h/2^k contém os pontos de a_y e de α da h);
  (b) estudar é determinístico (duas chamadas iguais);
  (c) erro_delta (contra a h/8) <= soma_erros, ou o caso sai marcado como violação;
  a regra não muda: o analise_par dá o veredito medido antes do estudo, e a grade h do estudo reproduz as saturações dele;
  a ordem observada nunca divide por zero (diferença < 1e-9 g dá p = None e dif_nula = True);
  os casos perturbados (λ_f ± 10 %, toe ± 0,1°, R ± 10 %) saem rotulados "sintético".
TC-NEU-002 entra na Task 9, com a regra que o usuário escolher.
Roda como script: uv run python -X utf8 tests/test_neutro.py

Veículo, pneu de escala, R, downforce e balanço aero são entradas SINTÉTICAS de teste, não do carro.
"""
import dataclasses
import math
import os

import equilibrio as eq
import tire_model as tm
from suspension_model import G, VehicleConfig

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def veiculo_base(**over) -> VehicleConfig:
    """Veículo de teste (números plausíveis, NÃO é setup real): o mesmo de tests/test_escada.py."""
    base = dict(mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
                cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
                unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
                roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0)
    base.update(over)
    return VehicleConfig(**base)


ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
ds_teste = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.5})   # escala de teste, não é pneu do carro
CASO = eq.CasoEquilibrio(cfg=veiculo_base(), ds=ds_teste, raio_m=8.5,            # sintético de teste
                         downforce_N=400.0, aero_balance_front=0.45)              # sintético de teste
# Veredito do analise_par neste caso, medido no commit b8d622d (antes do estudo existir), com os padrões
# ay_max_g = 2,0, passo_g = 0,05 e n_alfa = 25. O estudo não pode mudá-lo.
VEREDITO_ANTES = eq.LOOSE


def tc_neu_001() -> tuple[bool, str]:
    import estudo_neutro as en

    falhas = []
    r1 = en.estudar(CASO)
    r2 = en.estudar(CASO)

    # (a) grades aninhadas: passo/2^k e 2^k·(n_alfa − 1) + 1 pontos de α
    grades = r1["grades"]
    if len(grades) != 4:
        falhas.append(f"(a) {len(grades)} grades, esperadas 4")
    for k in range(1, len(grades)):
        (p0, n0), (pk, nk) = grades[0], grades[k]
        ay0 = {round(j * p0 * G, 12) for j in range(math.floor(2.0 / p0 + 1e-9) + 1)}
        ayk = {round(j * pk * G, 12) for j in range(math.floor(2.0 / pk + 1e-9) + 1)}
        al0 = {round(a, 12) for a in eq.grade_alfa(CASO, n0)}
        alk = {round(a, 12) for a in eq.grade_alfa(CASO, nk)}
        if not (ay0 <= ayk and al0 <= alk):
            falhas.append(f"(a) grade {k} não contém a h (a_y: {ay0 <= ayk}; α: {al0 <= alk})")

    # (b) determinismo
    if r1 != r2:
        falhas.append("(b) duas chamadas de estudar deram resultados diferentes")

    # (c) erro de Δ contra a soma das estimativas por eixo, ou violação listada
    if r1["ramo"] != "dois":
        falhas.append(f"(c) ramo {r1['ramo']!r}; o caso-base deveria saturar nos dois eixos")
    else:
        dentro = r1["erro_delta"] <= r1["soma_erros"]
        if dentro == r1["violacao"]:
            falhas.append(f"(c) erro_delta = {r1['erro_delta']:.3e} g, soma_erros = {r1['soma_erros']:.3e} g, "
                          f"violacao = {r1['violacao']}")

    # A regra não muda: veredito de antes e saturações da grade h iguais às do analise_par
    res = eq.analise_par(CASO)
    if res.veredito != VEREDITO_ANTES:
        falhas.append(f"veredito {res.veredito}, antes {VEREDITO_ANTES}")
    if (r1["F"].s[0] * G, r1["R"].s[0] * G) != (res.ay_sat_f, res.ay_sat_r):
        falhas.append("a grade h do estudo não reproduz as saturações do analise_par")
    if r1["veredito_atual"] != res.veredito:
        falhas.append(f"veredito_atual do estudo {r1['veredito_atual']} ≠ analise_par {res.veredito}")

    # Ordem observada sem divisão por zero
    c_nula = en.convergencia("F", (1.0, 1.0, 1.0, 1.0))
    c_meia = en.convergencia("F", (1.0, 1.0 + 1e-6, 1.0 + 1.25e-6, 1.0 + 1.3125e-6))
    c_none = en.convergencia("R", (None, 1.0, 1.0, 1.0))
    if not (c_nula.p is None and c_nula.dif_nula and c_nula.razao is None):
        falhas.append(f"diferença nula: {c_nula}")
    if not (c_meia.p is not None and abs(c_meia.p - 2.0) < 1e-6 and not c_meia.dif_nula):
        falhas.append(f"p = 2 esperado: {c_meia}")
    if not (c_none.p is None and not c_none.dif_nula):
        falhas.append(f"eixo sem saturação numa grade: {c_none}")

    # Casos perturbados, todos rotulados sintético
    pert = en.casos_perturbados(CASO)
    if len(pert) != 6 or not all("sintético" in nome for nome in pert):
        falhas.append(f"casos perturbados: {sorted(pert)}")
    k_soma = CASO.cfg.roll_stiffness_front + CASO.cfg.roll_stiffness_rear
    lam = CASO.cfg.roll_stiffness_front / k_soma
    lams = sorted(c.cfg.roll_stiffness_front / (c.cfg.roll_stiffness_front + c.cfg.roll_stiffness_rear)
                  for c in pert.values() if c.cfg is not CASO.cfg)
    raios = sorted(c.raio_m for c in pert.values() if c.raio_m != CASO.raio_m)
    toes = sorted(c.toe_rad["FL"] for c in pert.values() if c.toe_rad != CASO.toe_rad)
    if not (len(lams) == 2 and abs(lams[0] - 0.9 * lam) < 1e-12 and abs(lams[1] - 1.1 * lam) < 1e-12):
        falhas.append(f"λ_f perturbado: {lams} (base {lam})")
    if not (len(raios) == 2 and abs(raios[0] - 0.9 * 8.5) < 1e-12 and abs(raios[1] - 1.1 * 8.5) < 1e-12):
        falhas.append(f"R perturbado: {raios}")
    if not (len(toes) == 2 and abs(toes[0] + math.radians(0.1)) < 1e-15 and abs(toes[1] - math.radians(0.1)) < 1e-15):
        falhas.append(f"toe perturbado: {toes}")

    det = (f"ramo {r1['ramo']}; p_F = {r1['F'].p}, p_R = {r1['R'].p}; erro_delta = {r1['erro_delta']:.3e} g, "
           f"soma_erros = {r1['soma_erros']:.3e} g; veredito {res.veredito}")
    return not falhas, ("; ".join(falhas) + " | " + det) if falhas else det


try:
    ok, det = tc_neu_001()
except Exception as exc:   # RED: o módulo ainda não existe
    ok, det = False, f"exceção {type(exc).__name__}: {exc}"
check("TC-NEU-001 estudo do NEUTRO: grades aninhadas, determinismo, erro de Δ × e_F + e_R e regra sem mudança",
      ok, det)

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
