"""
Testes do módulo mmm (Milliken Moment Method em raio fixo, incremento 6, Task 2).
TC-MMM-001: cinemática por roda (sinais e limite de raio grande).
TC-MMM-007: trim desacoplado (resíduos, A_Y acima do limite, caso sem raio).
TC-MMM-011: contrato de Hipoteses e VARIANTES.
Roda como script: uv run python -X utf8 tests/test_mmm.py
O veículo, o raio e os números abaixo são entradas de teste, não do carro.
"""

import dataclasses
import math
import os

import equilibrio as eq
import mmm
import tire_model as tm
from suspension_model import VehicleConfig, G

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []

MSG_SEM_RAIO = "MMM em raio fixo exige raio_m (raio do skidpad), que está faltando."


def raises(fn, exc=ValueError, needle=None):
    try:
        fn()
        return False
    except exc as e:
        return needle is None or needle in str(e)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def veiculo_base(**over) -> VehicleConfig:
    """Veículo de teste (números plausíveis, NÃO é setup real)."""
    base = dict(
        mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
        cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
        roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0,
    )
    base.update(over)
    return VehicleConfig(**base)


cfg = veiculo_base()
ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
R_TESTE = 8.5   # sintético de teste: raio do skidpad usado só nos testes, não é dado do carro
L = cfg.wheelbase
A_CG, B_CG = cfg.cg_to_front, cfg.cg_to_rear

# ---------------- TC-MMM-001 : cinemática por roda ----------------
# "A_Y → 0": a cinemática exata não depende de V (V se cancela, adendo §2.1) e, com R fixo em 8,5 m, a
# diferença entre a tangente exata e as fórmulas de ângulo pequeno do Milliken é de ordem (L/R)³ ≈ 1e-3 rad.
# Por isso o limite |α| < 1e-9 é verificado chamando a função cinemática diretamente com um raio muito grande
# (R = 1e6 m, sintético de teste), onde δ = L/R e β = b/R zeram as quatro deriva a menos de O(1/R²).
caso_grande = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=1e6)
hip_c = mmm.Hipoteses(alfa="cinematico")
al0 = mmm.alfa_rodas(caso_grande, hip_c, B_CG / 1e6, L / 1e6)
max_al0 = max(abs(v) for v in al0.values())
# Com δ + 0,01 rad: α_FL e α_FR < 0 e a Fy dianteira (ISO) > 0. Também com R grande: com R = 8,5 m o efeito das
# velocidades não paralelas nas duas dianteiras (≈ L·t/R², adendo §7) passa de 0,01 rad e deixa α_FL > 0
# (informativo no detalhe); o teste de sinal precisa de um passo maior que esse efeito, ou de R grande.
al1 = mmm.alfa_rodas(caso_grande, hip_c, B_CG / 1e6, L / 1e6 + 0.01)
caso_r = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE)
al85 = mmm.alfa_rodas(caso_r, hip_c, B_CG / R_TESTE, L / R_TESTE + 0.01)
fz_a = eq.cargas(caso_grande, 1e-6)
fy_f = sum(tm.wheel_forces(ds, c, fz_a[c], al1[c], 0.0, 0.0)[1] for c in ("FL", "FR"))
check("TC-MMM-001: δ=L/R, β=b/R, toe 0: |α|<1e-9 nas 4 rodas (R grande); com δ+0,01 rad α_FL, α_FR<0 e Fy diant.>0",
      max_al0 < 1e-9 and al1["FL"] < 0 and al1["FR"] < 0 and fy_f > 0,
      f"max|α|={max_al0:.2e} rad; α_FL={al1['FL']:.4f} α_FR={al1['FR']:.4f} rad, Fy_diant={fy_f:.1f} N (R=1e6 m); "
      f"informativo R=8,5 m: α_FL={al85['FL']:.4f} α_FR={al85['FR']:.4f} rad")

# ---------------- TC-MMM-007 : trim desacoplado ----------------
def resíduos(caso_x, tr):
    soma_fy = sum(tr.fy.values())
    n_nm = mmm.cn(tr, caso_x)[0] * caso_x.cfg.mass_total * G * caso_x.cfg.wheelbase
    return abs(soma_fy - caso_x.cfg.mass_total * tr.ay_ms2), abs(n_nm)


hip_pl = mmm.Hipoteses.planilha()
caso_t = eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45)
caso_k = eq.CasoEquilibrio(   # toe, Ackermann 50 % e tração na traseira (valores de teste)
    cfg=cfg, ds=ds, raio_m=R_TESTE, downforce_N=400.0, aero_balance_front=0.45,
    toe_rad={"FL": 0.003, "FR": 0.003, "RL": 0.002, "RR": 0.002}, ackermann_pct=50.0,
    rho_kg_m3=1.2, cda_m2=1.0, crr=0.02)
rs = []
for caso_x, g_ay in ((caso_t, 0.5), (caso_t, 1.0), (caso_k, 0.8)):
    tr = mmm.trim(caso_x, hip_pl, g_ay * G)
    rs.append((tr.convergiu, *(resíduos(caso_x, tr) if tr.convergiu else (math.inf, math.inf))))
ok_res = all(c and rf < 1e-6 and rn < 1e-6 for c, rf, rn in rs)
tr_alto = mmm.trim(caso_t, hip_pl, 5.0 * G)
ok_alto = (not tr_alto.convergiu and bool(tr_alto.motivo) and tr_alto.delta_rad is None and tr_alto.beta_rad is None
           and tr_alto.alfa is None and tr_alto.fz is None and tr_alto.fy is None and tr_alto.fx is None
           and tr_alto.kappa is None and tr_alto.residuo_N is None)
# Sem raiz de verdade (sem descolamento): bitola larga de teste (2,4 m / 2,3 m, sintética) e 3 g, acima da capacidade.
caso_larga = eq.CasoEquilibrio(cfg=veiculo_base(track_front=2.4, track_rear=2.3), ds=ds, raio_m=R_TESTE,
                               downforce_N=400.0, aero_balance_front=0.45)
tr_raiz = mmm.trim(caso_larga, hip_pl, 3.0 * G)
ok_raiz = (not tr_raiz.convergiu and tr_raiz.eixo_sem_raiz in ("F", "R", "F+R") and bool(tr_raiz.motivo)
           and tr_raiz.fy is None and mmm.trim(caso_larga, hip_pl, 1.8 * G).convergiu)
ok_alto = ok_alto and ok_raiz
caso_sem = eq.CasoEquilibrio(cfg=cfg, ds=ds)
ok_raio = raises(lambda: mmm.trim(caso_sem, hip_pl, 1.0 * G), ValueError, MSG_SEM_RAIO)
ok_acopl = raises(lambda: mmm.trim(caso_t, mmm.Hipoteses(cos_delta="trim"), 1.0 * G), NotImplementedError, "Task 4")
check("TC-MMM-007: no trim |ΣFy−m·A_Y|<1e-6 N e |N|<1e-6 N·m; A_Y acima do limite -> convergiu=False com motivo e "
      "campos None; sem raio_m -> ValueError; acoplada -> NotImplementedError (Task 4)",
      ok_res and ok_alto and ok_raio and ok_acopl,
      f"resíduos(F,N)={[(f'{rf:.1e}', f'{rn:.1e}') for _, rf, rn in rs]}; motivo(5g)={tr_alto.motivo!r}; "
      f"eixo_sem_raiz={tr_alto.eixo_sem_raiz}")

# ---------------- TC-MMM-011 : contrato de Hipoteses e VARIANTES ----------------
campos = {f.name for f in dataclasses.fields(mmm.Hipoteses)}
ok_campos = set(mmm.VARIANTES) == campos - {"h_cp_m"}
ok_hip = all(set(v["hipoteses"]) <= {1, 2, 3, 7, 9, 10, 11} for v in mmm.VARIANTES.values())
ok_valor = raises(lambda: mmm.Hipoteses(alfa="x"), ValueError, "alfa")
ok_py = mmm.Hipoteses.python_completo() == mmm.Hipoteses(
    alfa="cinematico", cos_delta="trim", sentido="dois", fx_exigido="balanco", tracao="pac2002",
    diferencial="travado", transf_long="regime")
ok_nomes = {v["nome"] for v in mmm.VARIANTES.values()} == {"1+2", "3", "7", "9a", "9b", "10", "11"}
ok_var = all(v["planilha"] == getattr(hip_pl, k) and v["python"] == getattr(mmm.Hipoteses.python_completo(), k)
             for k, v in mmm.VARIANTES.items())
check("TC-MMM-011: VARIANTES = campos de Hipoteses (sem h_cp_m); hipóteses ⊂ {1,2,3,7,9,10,11}; "
      "Hipoteses(alfa='x') -> ValueError",
      ok_campos and ok_hip and ok_valor and ok_py and ok_nomes and ok_var,
      f"campos={sorted(campos)}")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
