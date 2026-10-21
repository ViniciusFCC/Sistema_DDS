"""
Testes do módulo equilibrio (análise de par, Milliken §7.1; V4.0, incremento 1).
TC-EQ-001..003 (IDs autorizados pelo usuário): caso, cargas e camber por roda.
TC-EQ-004..008 (idem): curva do eixo, capacidade, borda da grade, faixa do pneu e sinal do toe.
TC-EQ-009..015 (idem): análise de par (força exigida, saturação, veredito e C_N, Milliken §7.1 e §8.4).
TC-EQ-016..018 (idem): robustez do veredito ao pneu, nomes de fator e texto do veredito (spec 7.3 e 7.6).
TC-EQ-019..020 (idem): caso lido da planilha recalculada e pior origem (leitura apenas, sem salvar a planilha).
Roda como script: uv run python -X utf8 tests/test_equilibrio.py
O veículo e os números de camber abaixo são entradas de teste, não do carro.
"""

import copy
import dataclasses
import math
import os

import equilibrio as eq
import suspension_model as sm
import tire_model as tm
from suspension_model import VehicleConfig, G

TOL = 1e-9
HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []


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
        mass_total=250.0,
        cg_height=0.300,
        wheelbase=1.550,
        track_front=1.200,
        track_rear=1.150,
        cg_to_front=0.837,
        cg_to_rear=0.713,
        unsprung_mass_front=15.0,
        unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230,
        unsprung_cg_height_rear=0.230,
        roll_center_front=0.030,
        roll_center_rear=0.050,
        roll_stiffness_front=20826.4,
        roll_stiffness_rear=26450.0,
    )
    base.update(over)
    return VehicleConfig(**base)


cfg = veiculo_base()
ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")

# ---------------- TC-EQ-001 : a_y = 0 ----------------
caso = eq.CasoEquilibrio(cfg=cfg, ds=ds, downforce_N=400.0, aero_balance_front=0.45)
c0 = eq.cargas(caso, 0.0)
est = sm.static_fz_corner(cfg)
aer = sm.aero_fz_corner(400.0, 0.45)
dif = max(abs(c0[c] - (est[c] + aer[c])) for c in eq.CANTOS)
check("TC-EQ-001: a_y=0 -> Fz = estático + aero em cada canto", dif < TOL, f"max dif={dif:.2e} N")

# ---------------- TC-EQ-002 : a_y = 1,2 g ----------------
c12 = eq.cargas(caso, 1.2 * G)
soma = sum(c12.values())
check("TC-EQ-002: a_y=1,2g -> soma = m·G + DF; FR>FL e RR>RL",
      abs(soma - (cfg.mass_total * G + 400.0)) < TOL and c12["FR"] > c12["FL"] and c12["RR"] > c12["RL"],
      f"soma={soma:.6f} FL={c12['FL']:.1f} FR={c12['FR']:.1f} RL={c12['RL']:.1f} RR={c12['RR']:.1f}")

# ---------------- TC-EQ-003 : camber por roda e validação ----------------
estatico = {"FL": -0.01, "FR": -0.01, "RL": -0.02, "RR": -0.02}
ganho = {"FL": 0.5, "FR": -0.5, "RL": 0.3, "RR": -0.3}
caso_c = eq.CasoEquilibrio(cfg=cfg, ds=ds, camber_estatico_rad=estatico, ganho_camber=ganho)
phi = sm.lateral_dfz(cfg, 1.0 * G)["roll_angle_rad"]
gam = eq.camber(caso_c, 1.0 * G)
dif = max(abs(gam[c] - (estatico[c] + ganho[c] * phi)) for c in eq.CANTOS)
erro_toe = raises(lambda: eq.CasoEquilibrio(cfg=cfg, ds=ds, toe_rad={"FL": 0.0}), ValueError, "toe_rad")
check("TC-EQ-003: camber = estático + ganho·φ (φ de lateral_dfz); toe_rad com cantos faltando -> ValueError",
      dif < 1e-15 and phi != 0.0 and erro_toe, f"phi={phi:.6f} rad, max dif={dif:.2e}")

# ---------------- TC-EQ-004 : fy_eixo = soma das duas rodas ----------------
caso0 = eq.CasoEquilibrio(cfg=cfg, ds=ds)
fz0 = eq.cargas(caso0, 0.0)
dif = 0.0
for a in eq.grade_alfa(caso0, 25):
    esperado = (tm.wheel_forces(ds, "FL", fz0["FL"], a, 0.0, 0.0)[1]
                + tm.wheel_forces(ds, "FR", fz0["FR"], a, 0.0, 0.0)[1])
    dif = max(dif, abs(eq.fy_eixo(caso0, "F", 0.0, a) - esperado))
check("TC-EQ-004: fy_eixo = Fy(FL) + Fy(FR) em cada alfa da grade (a_y=0, toe e camber 0)",
      dif < TOL, f"max dif={dif:.2e} N")

# ---------------- TC-EQ-005 : máximo numérico = forma fechada |Dy| + SVy ----------------
fnom = ds.p["FNOMIN"]
info = tm.pure_fy0(ds.p, fnom, 0.0, 0.0)[1]
fechada = abs(info["Dy"]) + info["SVy"]
N = 4001
alfas = [i * ds.p["ALPMIN"] / (N - 1) for i in range(N)]
fys = [tm.wheel_forces(ds, "FR", fnom, a, 0.0, 0.0)[1] for a in alfas]
fmax = max(fys)
i_pico = fys.index(fmax)
rel = abs(fmax - fechada) / fechada
check("TC-EQ-005: max numérico de Fy (FR, FNOMIN, gamma=0) = |Dy|+SVy (erro rel < 1e-4); pico fora da borda",
      rel < 1e-4 and i_pico < N - 1,
      f"num={fmax:.3f} N, fechada={fechada:.3f} N, rel={rel:.2e}, idx={i_pico}, "
      f"alfa={math.degrees(alfas[i_pico]):.2f} deg")

# ---------------- TC-EQ-006 : pico na borda da grade ----------------
# Dataset de teste (PKY1 x 0,05): pneu pouco rígido, pico além da faixa de alfa. Não é pneu.
ds_mole = dataclasses.replace(ds, p={**ds.p, "PKY1": ds.p["PKY1"] * 0.05})
caso_mole = eq.CasoEquilibrio(cfg=cfg, ds=ds_mole)
cap_mole = eq.capacidade_eixo(caso_mole, "F", 0.0, 200)
check("TC-EQ-006: pneu pouco rígido -> motivo 'pico na borda da grade de α' (valor mantido)",
      cap_mole.motivo == "pico na borda da grade de α" and cap_mole.fy_max_N is not None,
      f"motivo={cap_mole.motivo!r}, fy_max={cap_mole.fy_max_N}")

# ---------------- TC-EQ-007 : faixa do pneu (EDR-056; help do Adams PAC2002, p. 83) ----------------
# Fz > 0 e γ fora da faixa entram limitados ao FZMIN/FZMAX ou CAMMIN/CAMMAX, com aviso, e a capacidade
# é válida; Fz <= 0 é descolamento (fora do modelo de transferência de carga, SUS-104) e fica None;
# toe que consome a faixa de α continua None. Nenhum caso pode lançar exceção.
def _cap_sem_excecao(caso_x, ay, eixo="F"):
    try:
        return eq.capacidade_eixo(caso_x, eixo, ay, 25)
    except Exception:  # o check precisa registrar qualquer exceção como falha
        return None


def _cap_ref(caso_x, eixo, fz_usado, gam_usado):
    """Capacidade recomposta: máximo sobre grade_alfa com Fz e γ dados por roda (κ = 0)."""
    dal = eq.deriva_toe(caso_x)
    rodas = ("FL", "FR") if eixo == "F" else ("RL", "RR")
    return max(sum(tm.wheel_forces(ds, c, fz_usado[c], a + dal[c], gam_usado[c], 0.0)[1] for c in rodas)
               for a in eq.grade_alfa(caso_x, 25))


def _limites(cap):
    return getattr(cap, "limites", ()) or ()


# 2,0 g no veículo de teste: 0 < Fz_FL < FZMIN (limitado) e Fz_RL <= 0 (descolamento)
fz2 = eq.cargas(caso0, 2.0 * G)
cap_f2 = _cap_sem_excecao(caso0, 2.0 * G, "F")
cap_r2 = _cap_sem_excecao(caso0, 2.0 * G, "R")
ref_f2 = _cap_ref(caso0, "F", {"FL": ds.p["FZMIN"], "FR": fz2["FR"]}, {"FL": 0.0, "FR": 0.0})
aviso_fl = f"Fz_FL = {fz2['FL']:.1f} N → {ds.p['FZMIN']:.1f} N (FZMIN)"
ok_fzmin = (0.0 < fz2["FL"] < ds.p["FZMIN"] and ds.p["FZMIN"] <= fz2["FR"] <= ds.p["FZMAX"]
            and cap_f2 is not None and cap_f2.fy_max_N is not None and cap_f2.motivo is None
            and aviso_fl in _limites(cap_f2) and abs(cap_f2.fy_max_N - ref_f2) < TOL)
ok_desc = (fz2["RL"] <= 0.0 and cap_r2 is not None and cap_r2.fy_max_N is None and cap_r2.alfa_pico_rad is None
           and (cap_r2.motivo or "").startswith("Fz_RL = ") and "descolamento" in cap_r2.motivo)
# camber estático além de CAMMAX numa roda dianteira (a_y = 0): avaliado com γ = CAMMAX
cam_fora = ds.p["CAMMAX"] + math.radians(1.0)
caso_cam = eq.CasoEquilibrio(cfg=cfg, ds=ds, camber_estatico_rad={"FL": 0.0, "FR": cam_fora, "RL": 0.0, "RR": 0.0})
cap_cam = _cap_sem_excecao(caso_cam, 0.0)
ref_cam = _cap_ref(caso_cam, "F", fz0, {"FL": 0.0, "FR": ds.p["CAMMAX"]})
ok_cam = (cap_cam is not None and cap_cam.fy_max_N is not None and cap_cam.motivo is None
          and any(s.startswith("γ_FR = ") and "(CAMMAX)" in s for s in _limites(cap_cam))
          and abs(cap_cam.fy_max_N - ref_cam) < TOL)
# downforce de teste (não é do carro) que leva Fz das rodas dianteiras acima de FZMAX em a_y = 0
caso_df = eq.CasoEquilibrio(cfg=cfg, ds=ds, downforce_N=4400.0, aero_balance_front=0.5)
fz_df = eq.cargas(caso_df, 0.0)
cap_df = _cap_sem_excecao(caso_df, 0.0)
ref_df = _cap_ref(caso_df, "F", {"FL": ds.p["FZMAX"], "FR": ds.p["FZMAX"]}, {"FL": 0.0, "FR": 0.0})
ok_fzmax = (min(fz_df["FL"], fz_df["FR"]) > ds.p["FZMAX"] and cap_df is not None and cap_df.fy_max_N is not None
            and cap_df.motivo is None and sum("(FZMAX)" in s for s in _limites(cap_df)) == 2
            and abs(cap_df.fy_max_N - ref_df) < TOL)
# toe maior que a faixa de α: continua None
toe_grande = 2.0 * min(abs(ds.p["ALPMIN"]), ds.p["ALPMAX"])
cap_toe = _cap_sem_excecao(eq.CasoEquilibrio(
    cfg=cfg, ds=ds, toe_rad={"FL": toe_grande, "FR": toe_grande, "RL": 0.0, "RR": 0.0}), 0.0)
ok_toe = cap_toe is not None and cap_toe.fy_max_N is None and cap_toe.motivo == "toe consome a faixa de α"
check("TC-EQ-007: faixa do pneu (EDR-056): Fz < FZMIN, Fz > FZMAX e γ > CAMMAX -> limitados, válidos, com aviso "
      "e iguais à recomposição; Fz <= 0 -> None 'descolamento'; toe que consome a faixa -> None; sem exceção",
      ok_fzmin and ok_desc and ok_cam and ok_fzmax and ok_toe,
      f"{ok_fzmin}/{ok_desc}/{ok_cam}/{ok_fzmax}/{ok_toe}; Fz_FL={fz2['FL']:.1f} N, Fz_RL={fz2['RL']:.1f} N, "
      f"Fz_F(DF)={fz_df['FL']:.1f} N; limites={_limites(cap_f2)}, {_limites(cap_cam)}, {_limites(cap_df)}; "
      f"motivos={getattr(cap_r2, 'motivo', None)!r}; {getattr(cap_toe, 'motivo', None)!r}")

# ---------------- TC-EQ-008 : sinal do toe (EDR-002) ----------------
um_grau = math.radians(1.0)
caso_toe = eq.CasoEquilibrio(cfg=cfg, ds=ds, toe_rad={"FL": um_grau, "FR": um_grau, "RL": 0.0, "RR": 0.0})
fzt = eq.cargas(caso_toe, 0.0)
dal = eq.deriva_toe(caso_toe)
fy_fl = tm.wheel_forces(ds, "FL", fzt["FL"], dal["FL"], 0.0, 0.0)[1]
fy_fr = tm.wheel_forces(ds, "FR", fzt["FR"], dal["FR"], 0.0, 0.0)[1]
fy_ax = eq.fy_eixo(caso_toe, "F", 0.0, 0.0)
check("TC-EQ-008: toe-out simétrico de 1 grau -> Fy(FL) > 0, Fy(FR) < 0, soma ~ 0",
      dal["FL"] < 0 < dal["FR"] and fy_fl > 0 and fy_fr < 0 and abs(fy_ax) < TOL,
      f"FL={fy_fl:.3f} N, FR={fy_fr:.3f} N, soma={fy_ax:.2e}")


# ---------------- Análise de par (TC-EQ-009..015) ----------------
def _par_sem_excecao(caso_x, **kw):
    try:
        return eq.analise_par(caso_x, **kw), None
    except Exception as e:  # o check precisa registrar qualquer exceção como falha
        return None, f"{type(e).__name__}: {e}"


def _folga_em(linhas, eixo, ay):
    """Folga cap − req do eixo ('f' ou 'r') interpolada linearmente em ay, entre as linhas vizinhas."""
    for la, lb in zip(linhas, linhas[1:]):
        if la.ay_ms2 <= ay <= lb.ay_ms2:
            ma = getattr(la, f"cap_{eixo}").fy_max_N - getattr(la, f"req_{eixo}")
            mb = getattr(lb, f"cap_{eixo}").fy_max_N - getattr(lb, f"req_{eixo}")
            return ma + (mb - ma) * (ay - la.ay_ms2) / (lb.ay_ms2 - la.ay_ms2)
    raise AssertionError(f"a_y={ay} fora das linhas")


def _resumo(r):
    if r is None:
        return "sem resultado"
    return (f"veredito={r.veredito}, sat_f={r.ay_sat_f}, sat_r={r.ay_sat_r}, "
            f"lim={r.ay_lim}, c_n={r.c_n}, motivo={r.motivo!r}")


# Dataset de teste: LMUY = 0,5. Escala só de teste, não é pneu ("Risco conhecido" do plano: com o
# .tir sem escala, a roda interna sai da faixa de Fz antes de o eixo saturar).
ds_teste = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.5})
W = cfg.mass_total * G

# ---------------- TC-EQ-009 : força lateral exigida por eixo ----------------
cfg_ab = veiculo_base(cg_to_front=0.85, cg_to_rear=0.70)
caso_ab = eq.CasoEquilibrio(cfg=cfg_ab, ds=ds)
try:
    req = eq.forca_exigida(caso_ab, 9.81)
except Exception as e:  # o check precisa registrar qualquer exceção como falha
    req = (math.nan, math.nan)
esp = (cfg_ab.mass_total * 9.81 * 0.70 / cfg_ab.wheelbase, cfg_ab.mass_total * 9.81 * 0.85 / cfg_ab.wheelbase)
check("TC-EQ-009: forca_exigida = (m·a_y·b/L, m·a_y·a/L) com a != b",
      abs(req[0] - esp[0]) < TOL and abs(req[1] - esp[1]) < TOL,
      f"obtido={req}, esperado={esp}")

# ---------------- TC-EQ-010 : carro simétrico -> NEUTRO ----------------
k_soma = cfg.roll_stiffness_front + cfg.roll_stiffness_rear


def veiculo_simetrico(lambda_f=0.5, **over):
    L = cfg.wheelbase
    return veiculo_base(**{**dict(cg_to_front=L / 2, cg_to_rear=L / 2, track_rear=cfg.track_front,
                                  roll_stiffness_front=lambda_f * k_soma, roll_stiffness_rear=(1 - lambda_f) * k_soma,
                                  roll_center_rear=cfg.roll_center_front, unsprung_mass_rear=cfg.unsprung_mass_front,
                                  unsprung_cg_height_rear=cfg.unsprung_cg_height_front), **over})


r_sim, err_sim = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.5), ds=ds_teste))
_res_sim = getattr(r_sim, "resolucao_ms2", None)
check("TC-EQ-010: carro simétrico (LMUY 0,5) -> as duas saturações existem, NEUTRO, |S_f − S_r| <= resolução "
      "numérica (EDR-056), c_n None",
      r_sim is not None and r_sim.ay_sat_f is not None and r_sim.ay_sat_r is not None
      and isinstance(_res_sim, float) and math.isfinite(_res_sim) and _res_sim > 0.0
      and r_sim.veredito == eq.NEUTRO and abs(r_sim.ay_sat_f - r_sim.ay_sat_r) <= _res_sim
      and r_sim.c_n is None,
      (err_sim or _resumo(r_sim)) + f", resolucao={_res_sim}")

# ---------------- TC-EQ-011 : distribuição de rolagem (Gillespie p. 214) ----------------
# LMUY = 0,45: escala só de teste, não é pneu. Com este pneu, o efeito de lambda_f 0,5 -> 0,7 é
# ~0,03-0,04 g, abaixo do passo padrão de 0,05 g; pelo EDR-056 (Milliken p. 320) o veredito não pode
# depender do passo de exibição: o mesmo veredito sai na grade padrão (0,05 g) e na de 0,01 g, e a
# resolução numérica medida fica abaixo de 0,01 g.
ds_teste_011 = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.45})
PASSO_011 = 0.01
r_push, err_push = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.7), ds=ds_teste_011),
                                    passo_g=PASSO_011)
r_loose, err_loose = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.3), ds=ds_teste_011),
                                      passo_g=PASSO_011)
r_push_p, err_push_p = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.7), ds=ds_teste_011))
r_loose_p, err_loose_p = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.3), ds=ds_teste_011))


def _pre_saturacoes(r):
    """As duas saturações existem e nenhuma roda sai da faixa (nos dois eixos) antes delas."""
    if r is None or r.ay_sat_f is None or r.ay_sat_r is None:
        return False
    ate = max(r.ay_sat_f, r.ay_sat_r)
    return all(ln.cap_f.motivo is None and ln.cap_r.motivo is None for ln in r.linhas if ln.ay_ms2 <= ate)


def _sat_g(r):
    if r is None or r.ay_sat_f is None or r.ay_sat_r is None:
        return "sat indisponível"
    return f"sat_f={r.ay_sat_f / G:.4f} g, sat_r={r.ay_sat_r / G:.4f} g"


def _res_ok(r):
    res = getattr(r, "resolucao_ms2", None)
    return isinstance(res, float) and 0.0 < res < 0.01 * G


pre_011 = _pre_saturacoes(r_push) and _pre_saturacoes(r_loose)
pre_011p = _pre_saturacoes(r_push_p) and _pre_saturacoes(r_loose_p)
check("TC-EQ-011: lambda_f = 0,7 -> PUSH; lambda_f = 0,3 -> LOOSE, o mesmo na grade padrão (0,05 g) e na de "
      "0,01 g, com resolução numérica < 0,01 g (LMUY 0,45; pré-condição: duas saturações, nenhuma capacidade "
      "inválida antes delas)",
      pre_011 and pre_011p and all(_res_ok(r) for r in (r_push, r_loose, r_push_p, r_loose_p))
      and r_push.veredito == eq.PUSH and r_push_p.veredito == eq.PUSH
      and r_loose.veredito == eq.LOOSE and r_loose_p.veredito == eq.LOOSE,
      f"0,7 @0,01: {_sat_g(r_push)}; {err_push or _resumo(r_push)}; res={getattr(r_push, 'resolucao_ms2', None)} | "
      f"0,7 @0,05: {_sat_g(r_push_p)}; {err_push_p or _resumo(r_push_p)}; "
      f"res={getattr(r_push_p, 'resolucao_ms2', None)} | "
      f"0,3 @0,01: {_sat_g(r_loose)}; {err_loose or _resumo(r_loose)}; "
      f"res={getattr(r_loose, 'resolucao_ms2', None)} | "
      f"0,3 @0,05: {_sat_g(r_loose_p)}; {err_loose_p or _resumo(r_loose_p)}; "
      f"res={getattr(r_loose_p, 'resolucao_ms2', None)}")

# ---------------- TC-EQ-012 : sinal e recomposição de C_N ----------------
ok_012, det_012 = False, "pré-condição do TC-EQ-011 falhou"
if pre_011 and r_push.veredito == eq.PUSH and r_loose.veredito == eq.LOOSE:
    cs = veiculo_simetrico(0.7)
    a_s, b_s, L_s = cs.cg_to_front, cs.cg_to_rear, cs.wheelbase
    cn_push = _folga_em(r_push.linhas, "r", r_push.ay_lim) * b_s / (W * L_s)
    cn_loose = -_folga_em(r_loose.linhas, "f", r_loose.ay_lim) * a_s / (W * L_s)
    ok_012 = (r_push.c_n > 0 and r_loose.c_n < 0
              and abs(r_push.c_n - cn_push) < 1e-12 and abs(r_loose.c_n - cn_loose) < 1e-12)
    det_012 = (f"PUSH c_n={r_push.c_n:.6f} (recomp. {cn_push:.6f}); "
               f"LOOSE c_n={r_loose.c_n:.6f} (recomp. {cn_loose:.6f})")
check("TC-EQ-012: C_N > 0 em PUSH, < 0 em LOOSE e igual à recomposição pelas linhas", ok_012, det_012)

# ---------------- TC-EQ-013 : ramos de validade do veredito (EDR-056) ----------------
# Pneu sem escala: a roda interna descola (Fz <= 0) antes de os eixos saturarem -> N/A por descolamento,
# ou, se um eixo saturar, o outro segue válido além de S + resolução.
r_base, err_base = _par_sem_excecao(caso0)
ok_013, det_013 = False, err_base or _resumo(r_base)
if r_base is not None:
    if r_base.veredito == eq.NA:
        # sem a_y_lim, limitacoes junta as capacidades válidas de todas as linhas: um aviso por roda e
        # limite, o de maior excesso (aqui, o menor Fz > 0 abaixo de FZMIN), recomposto pelas linhas
        esp_lim = []
        for roda, eixo in (("FL", "f"), ("FR", "f"), ("RL", "r"), ("RR", "r")):
            fzs = [ln.fz[roda] for ln in r_base.linhas
                   if getattr(ln, f"cap_{eixo}").motivo is None and ln.fz[roda] < ds.p["FZMIN"]]
            if fzs:
                esp_lim.append(f"Fz_{roda} = {min(fzs):.1f} N → {ds.p['FZMIN']:.1f} N (FZMIN)")
        ok_013 = ("descolamento" in (r_base.motivo or "") and r_base.c_n is None
                  and len(esp_lim) >= 2 and r_base.limitacoes == tuple(esp_lim))
        ramo = "N/A"
    elif r_base.veredito in (eq.PUSH, eq.LOOSE):
        nao_sat = "r" if r_base.veredito == eq.PUSH else "f"
        validas = [ln.ay_ms2 for ln in r_base.linhas if getattr(ln, f"cap_{nao_sat}").motivo is None]
        ok_013 = (r_base.ay_lim is not None and r_base.resolucao_ms2 is not None
                  and any(a >= r_base.ay_lim + r_base.resolucao_ms2 for a in validas))
        ramo = r_base.veredito
    else:
        ramo = r_base.veredito
    # nos dois ramos: as saturações conhecidas caem dentro da parte válida da grade de cada eixo
    for eixo, sat in (("f", r_base.ay_sat_f), ("r", r_base.ay_sat_r)):
        if sat is not None:
            ate = [ln for ln in r_base.linhas if ln.ay_ms2 <= sat + 1e-12]
            seguinte = [ln for ln in r_base.linhas if ln.ay_ms2 > sat][:1]
            ok_013 = ok_013 and all(getattr(ln, f"cap_{eixo}").motivo is None for ln in ate + seguinte)
    det_013 = f"ramo={ramo}; {_resumo(r_base)}; limitacoes={r_base.limitacoes}"

# Sub-casos determinísticos dos ramos de validade do veredito (A: eixo não saturado segue válido além de
# S + resolução -> PUSH/LOOSE com c_n; B: a roda interna do eixo não saturado descola (Fz <= 0) antes de S
# do outro -> N/A com o motivo dele). Pelo EDR-056, Fz e γ fora da faixa do pneu não invalidam mais a
# linha (entram limitados); o descolamento continua invalidando. Escala LMUY 0,45 só de teste, não é
# pneu; passo 0,01 g.
ds_013 = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.45})
L_013 = cfg.wheelbase


def _cn_recomp(r, eixo_folga):
    folga = _folga_em(r.linhas, eixo_folga, r.ay_lim)
    # carro simétrico: a = b = L/2, então o braço é L/2 nos dois sinais
    return folga * (L_013 / 2) / (W * L_013) * (1 if eixo_folga == "r" else -1)


def _caso_013(lf, **over):
    return eq.CasoEquilibrio(cfg=veiculo_simetrico(lf, **over), ds=ds_013)


# Ramo A: o eixo traseiro (PUSH) ou dianteiro (LOOSE) não satura, mas a grade o mantém válido além de S.
rA_p, eA_p = _par_sem_excecao(_caso_013(0.7), passo_g=0.01, ay_max_g=1.17)
rA_l, eA_l = _par_sem_excecao(_caso_013(0.3), passo_g=0.01, ay_max_g=1.17)
okA = False
if rA_p is not None and rA_l is not None:
    pre_p = (rA_p.ay_sat_f is not None and rA_p.ay_sat_r is None and rA_p.resolucao_ms2 is not None
             and all(ln.cap_r.motivo is None for ln in rA_p.linhas)
             and rA_p.linhas[-1].ay_ms2 >= rA_p.ay_sat_f + rA_p.resolucao_ms2)
    pre_l = (rA_l.ay_sat_r is not None and rA_l.ay_sat_f is None and rA_l.resolucao_ms2 is not None
             and all(ln.cap_f.motivo is None for ln in rA_l.linhas)
             and rA_l.linhas[-1].ay_ms2 >= rA_l.ay_sat_r + rA_l.resolucao_ms2)
    okA = (pre_p and pre_l
           and rA_p.veredito == eq.PUSH and rA_p.motivo is None and rA_p.c_n is not None and rA_p.c_n > 0
           and abs(rA_p.c_n - _cn_recomp(rA_p, "r")) < 1e-12
           and rA_l.veredito == eq.LOOSE and rA_l.motivo is None and rA_l.c_n is not None and rA_l.c_n < 0
           and abs(rA_l.c_n - _cn_recomp(rA_l, "f")) < 1e-12)

# Ramo B: CG mais alto (h = 0,45 m, só de teste, não é do carro). Com lambda_f = 0,3 a traseira transfere
# mais carga e a RL descola antes de a frente saturar (o PUSH não pode ser confirmado); com lambda_f = 0,7,
# o espelho: a FL descola antes de a traseira saturar.
_H_013B = 0.45
rB_p, eB_p = _par_sem_excecao(_caso_013(0.3, cg_height=_H_013B), passo_g=0.01)
rB_l, eB_l = _par_sem_excecao(_caso_013(0.7, cg_height=_H_013B), passo_g=0.01)


def _pre_b(r, sat, eixo_inv, roda):
    """Pré-condições do ramo B pelas linhas: só o outro eixo satura; o eixo alvo fica inválido por
    descolamento da roda interna numa linha com a_y <= S do outro; antes disso ele é válido."""
    if r is None or sat(r) is None:
        return False
    inval = [ln for ln in r.linhas if getattr(ln, f"cap_{eixo_inv}").motivo is not None]
    if not inval:
        return False
    prim = inval[0]
    validas_antes = all(getattr(ln, f"cap_{eixo_inv}").motivo is None for ln in r.linhas if ln.ay_ms2 < prim.ay_ms2)
    return (prim.ay_ms2 <= sat(r) and validas_antes and prim.fz[roda] <= 0.0
            and "descolamento" in getattr(prim, f"cap_{eixo_inv}").motivo)


okB = False
if rB_p is not None and rB_l is not None:
    pre_bp = rB_p.ay_sat_r is None and _pre_b(rB_p, lambda r: r.ay_sat_f, "r", "RL")
    pre_bl = rB_l.ay_sat_f is None and _pre_b(rB_l, lambda r: r.ay_sat_r, "f", "FL")
    okB = (pre_bp and pre_bl
           and rB_p.veredito == eq.NA and rB_p.c_n is None
           and (rB_p.motivo or "").startswith("Fz_RL = ") and "descolamento" in rB_p.motivo
           and rB_l.veredito == eq.NA and rB_l.c_n is None
           and (rB_l.motivo or "").startswith("Fz_FL = ") and "descolamento" in rB_l.motivo)
ok_013 = ok_013 and okA and okB
det_013 += (f" | A push: {eA_p or _resumo(rA_p)} | A loose: {eA_l or _resumo(rA_l)}"
            f" | B push: {eB_p or _resumo(rB_p)} | B loose: {eB_l or _resumo(rB_l)}")
check("TC-EQ-013: ramos de validade do veredito, determinísticos (ds sem escala: N/A por descolamento ou "
      "PUSH/LOOSE válido; A: eixo não saturado válido além de S + resolução -> PUSH/LOOSE com c_n e recomposição; "
      "B: roda interna do eixo não saturado descola antes de S -> N/A com o motivo dele); "
      "nenhuma capacidade inválida usada",
      ok_013, det_013)

# ---------------- TC-EQ-014 : grade curta -> não satura ----------------
r_curta, err_curta = _par_sem_excecao(caso0, ay_max_g=0.3)
check("TC-EQ-014: ay_max_g = 0,3 -> N/A 'não satura até 0.3 g'",
      r_curta is not None and r_curta.veredito == eq.NA and "não satura até 0.3 g" in (r_curta.motivo or "")
      and r_curta.c_n is None and r_curta.ay_lim is None,
      err_curta or _resumo(r_curta))

# ---------------- TC-EQ-015 : parâmetros inválidos ----------------
erros = [raises(lambda: eq.analise_par(caso0, ay_max_g=0)),
         raises(lambda: eq.analise_par(caso0, passo_g=-0.05)),
         raises(lambda: eq.analise_par(caso0, n_alfa=2))]
check("TC-EQ-015: ay_max_g=0, passo_g=-0,05 e n_alfa=2 -> ValueError cada um", all(erros), f"{erros}")

# ---------------- TC-EQ-016 : robustez ao pneu (spec 7.6) ----------------
_M = "mesmo sinal na varredura exploratória do pneu"
_dep = (eq.NAO_CONCLUSIVO, "o sinal depende do pneu")
ok_016 = (eq.veredito_robusto([eq.PUSH, eq.PUSH]) == (eq.PUSH, _M)
          and eq.veredito_robusto([eq.LOOSE, eq.LOOSE]) == (eq.LOOSE, _M)
          and eq.veredito_robusto([eq.PUSH, eq.LOOSE]) == _dep
          and eq.veredito_robusto([eq.PUSH, eq.NEUTRO]) == _dep
          and eq.veredito_robusto([eq.PUSH, eq.NA]) == _dep
          and eq.veredito_robusto([eq.NA, eq.NA]) == (eq.NA, "N/A em toda a varredura")
          and eq.veredito_robusto([]) == (eq.NA, "robustez ao pneu não avaliada"))
check("TC-EQ-016: veredito_robusto (PUSH/PUSH, LOOSE/LOOSE, inversão, NEUTRO, N/A misto, N/A, vazio)", ok_016)

# ---------------- TC-EQ-017 : varredura do pneu ----------------
# Grade reduzida e fatores abaixo são só de teste, não são amplitudes do EDR-055.
_kw = dict(ay_max_g=1.0, passo_g=0.1, n_alfa=9)
v1 = eq.varredura_pneu(caso0, {"LMUY": [1.0]}, **_kw)
ok_017a = (len(v1) == 1 and v1[0][0] == {"LMUY": 1.0} and v1[0][1] == eq.analise_par(caso0, **_kw))
p_antes = copy.deepcopy(ds.p)
v4 = eq.varredura_pneu(caso0, {"LFZO": [0.9, 1.1], "LKY": [0.9, 1.1]}, **_kw)
ok_017b = len(v4) == 4 and ds.p == p_antes and caso0.ds is ds
ok_017c = eq.varredura_pneu(caso0, {}, **_kw) == []
check("TC-EQ-017: fator 1,0 reproduz analise_par; 4 combinações; ds.p intacto; dict vazio -> []",
      ok_017a and ok_017b and ok_017c, f"{ok_017a}/{ok_017b}/{ok_017c}")

# ---------------- TC-EQ-018 : nomes de fator e texto do veredito ----------------
erros_018 = [raises(lambda: eq.com_fatores(ds, {"PDY2": 1.1})),
             raises(lambda: eq.com_fatores(ds, {"LMUX ": 1.0})),
             raises(lambda: eq.com_fatores(ds, {"LXYZ": 1.0}))]
ds_f = eq.com_fatores(ds, {"LMUY": 0.5})
ok_018a = all(erros_018) and ds_f.p["LMUY"] == ds.p["LMUY"] * 0.5 and ds.p == p_antes
_r = lambda v, m=None: eq.ResultadoPar(linhas=(), passo_ms2=0.0, ay_sat_f=None, ay_sat_r=None,
                                       ay_lim=None, veredito=v, motivo=m, c_n=None)
TX, T09 = "● Dado do TX", "◐ Dado do T09"
ok_018b = (eq.texto_veredito(_r(eq.PUSH), T09) == "DEMONSTRATIVO · ▲ PUSH: sai de frente (final understeer)"
           and eq.texto_veredito(_r(eq.LOOSE), TX) == "▼ LOOSE: sai de traseira (final oversteer)"
           and eq.texto_veredito(_r(eq.NEUTRO), TX) == "● NEUTRO no limite"
           and eq.texto_veredito(_r(eq.NA, "motivo x"), TX) == "N/A: motivo x"
           and eq.texto_veredito(_r(eq.PUSH), TX, (eq.PUSH, "mesmo")) == "▲ PUSH: sai de frente (final understeer)"
           and eq.texto_veredito(_r(eq.PUSH), T09, _dep)
           == "DEMONSTRATIVO · ? NÃO CONCLUSIVO: o sinal depende do pneu")
check("TC-EQ-018: nome de fator inválido -> ValueError; textos exatos de 7.3 e prefixo DEMONSTRATIVO",
      ok_018a and ok_018b, f"{ok_018a}/{ok_018b}")

# ---------------- TC-EQ-019 : planilha sem valores calculados ----------------
import hashlib
import tempfile

import openpyxl

import caso_planilha as cp
import raizes

with tempfile.TemporaryDirectory(prefix="dds_eq019_") as _tmp:
    _f = os.path.join(_tmp, "sem_valores.xlsx")
    _wb = openpyxl.Workbook()
    _wb.remove(_wb.active)
    for _aba in sorted({a for a, _ in cp.ENTRADAS_CASO.values()}):
        _wb.create_sheet(_aba)
    for _aba, _cel in cp.ENTRADAS_CASO.values():
        _wb[_aba][_cel].value = "=1+1"
    _wb.save(_f)
    ok_019a = raises(lambda: cp.caso_da_planilha(_f, TIR), ValueError, "precisa ser recalculada")
ok_019b = (len(cp.ENTRADAS_CASO) == 23 and cp.ENTRADAS_CASO["DF"] == ("08_VEHICLE_STATE", "B8")
           and cp.ENTRADAS_CASO["bal"] == ("08_VEHICLE_STATE", "B9"))
check("TC-EQ-019: planilha sem valor calculado -> ValueError 'precisa ser recalculada'; mapa de entradas",
      ok_019a and ok_019b, f"{ok_019a}/{ok_019b}")

# ---------------- TC-EQ-020 : pior origem da planilha viva (só leitura) ----------------
VIVA = os.path.join(HERE, "..", "excel", "FSAE_EV_Suspension_Fase1_V3_0.xlsx")


def _sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


_h0 = _sha(VIVA)
_pior = cp.pior_origem_do_caso(VIVA)
_h1 = _sha(VIVA)
ok_020 = _pior in raizes.PIOR_PRIMEIRO and _pior != "● Dado do TX" and _h0 == _h1
check("TC-EQ-020: pior origem da viva é rótulo conhecido e não é TX; arquivo intacto (SHA-256)",
      ok_020, f"pior = {_pior}")

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
