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

# ---------------- TC-EQ-007 : Fz fora da faixa -> None com motivo, sem exceção ----------------
fz2 = eq.cargas(caso0, 2.0 * G)
try:
    cap_fora = eq.capacidade_eixo(caso0, "F", 2.0 * G, 25)
    sem_excecao = True
except Exception:  # o check precisa registrar qualquer exceção como falha
    cap_fora = None
    sem_excecao = False
def _cap_sem_excecao(caso_x, ay):
    try:
        return eq.capacidade_eixo(caso_x, "F", ay, 25)
    except Exception:  # o check precisa registrar qualquer exceção como falha
        return None


# camber estático além de CAMMAX numa roda dianteira, e toe maior que a faixa de α
cam_fora = ds.p["CAMMAX"] + math.radians(1.0)
cap_cam = _cap_sem_excecao(eq.CasoEquilibrio(
    cfg=cfg, ds=ds, camber_estatico_rad={"FL": 0.0, "FR": cam_fora, "RL": 0.0, "RR": 0.0}), 0.0)
toe_grande = 2.0 * min(abs(ds.p["ALPMIN"]), ds.p["ALPMAX"])
cap_toe = _cap_sem_excecao(eq.CasoEquilibrio(
    cfg=cfg, ds=ds, toe_rad={"FL": toe_grande, "FR": toe_grande, "RL": 0.0, "RR": 0.0}), 0.0)
check("TC-EQ-007: Fz, camber ou toe fora da faixa do pneu -> fy_max None com motivo, sem exceção",
      fz2["FL"] < ds.p["FZMIN"] and sem_excecao and cap_fora.fy_max_N is None
      and cap_fora.alfa_pico_rad is None and "fora da faixa do pneu" in (cap_fora.motivo or "")
      and cap_cam is not None and cap_cam.fy_max_N is None and cap_cam.alfa_pico_rad is None
      and cap_cam.motivo.startswith("camber_FR = ") and "fora da faixa do pneu" in cap_cam.motivo
      and cap_toe is not None and cap_toe.fy_max_N is None and cap_toe.motivo == "toe consome a faixa de α",
      f"Fz_FL={fz2['FL']:.1f} N, FZMIN={ds.p['FZMIN']}, motivos={getattr(cap_fora, 'motivo', None)!r}; "
      f"{getattr(cap_cam, 'motivo', None)!r}; {getattr(cap_toe, 'motivo', None)!r}")

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


def veiculo_simetrico(lambda_f=0.5):
    L = cfg.wheelbase
    return veiculo_base(cg_to_front=L / 2, cg_to_rear=L / 2, track_rear=cfg.track_front,
                        roll_stiffness_front=lambda_f * k_soma, roll_stiffness_rear=(1 - lambda_f) * k_soma,
                        roll_center_rear=cfg.roll_center_front, unsprung_mass_rear=cfg.unsprung_mass_front,
                        unsprung_cg_height_rear=cfg.unsprung_cg_height_front)


r_sim, err_sim = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.5), ds=ds_teste))
check("TC-EQ-010: carro simétrico (LMUY 0,5) -> as duas saturações existem, NEUTRO, c_n None",
      r_sim is not None and r_sim.ay_sat_f is not None and r_sim.ay_sat_r is not None
      and r_sim.veredito == eq.NEUTRO and abs(r_sim.ay_sat_f - r_sim.ay_sat_r) < r_sim.passo_ms2
      and r_sim.c_n is None,
      err_sim or _resumo(r_sim))

# ---------------- TC-EQ-011 : distribuição de rolagem (Gillespie p. 214) ----------------
# Com LMUY = 0,5 a roda interna sai da faixa de Fz antes de o eixo saturar; por isso LMUY = 0,45
# (escala só de teste, não é pneu) e passo de 0,01 g.
# Com este pneu, o efeito de lambda_f 0,5 -> 0,7 é ~0,03-0,04 g, abaixo do passo padrão de 0,05 g.
ds_teste_011 = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.45})
PASSO_011 = 0.01
r_push, err_push = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.7), ds=ds_teste_011),
                                    passo_g=PASSO_011)
r_loose, err_loose = _par_sem_excecao(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.3), ds=ds_teste_011),
                                      passo_g=PASSO_011)


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


pre_011 = _pre_saturacoes(r_push) and _pre_saturacoes(r_loose)
check("TC-EQ-011: lambda_f = 0,7 -> PUSH; lambda_f = 0,3 -> LOOSE (LMUY 0,45, passo 0,01 g; "
      "pré-condição: duas saturações, sem roda fora da faixa antes delas)",
      pre_011 and r_push.veredito == eq.PUSH and r_loose.veredito == eq.LOOSE,
      f"0,7: {_sat_g(r_push)}; {err_push or _resumo(r_push)} | "
      f"0,3: {_sat_g(r_loose)}; {err_loose or _resumo(r_loose)}")

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

# ---------------- TC-EQ-013 : pneu sem escala -> roda sai da faixa antes de saturar ----------------
r_base, err_base = _par_sem_excecao(caso0)
ok_013, det_013 = False, err_base or _resumo(r_base)
if r_base is not None:
    if r_base.veredito == eq.NA:
        ok_013 = "fora da faixa do pneu" in (r_base.motivo or "") and r_base.c_n is None
        ramo = "N/A"
    elif r_base.veredito in (eq.PUSH, eq.LOOSE):
        nao_sat = "r" if r_base.veredito == eq.PUSH else "f"
        validas = [ln.ay_ms2 for ln in r_base.linhas if getattr(ln, f"cap_{nao_sat}").motivo is None]
        ok_013 = r_base.ay_lim is not None and any(a > r_base.ay_lim for a in validas)
        ramo = r_base.veredito
    else:
        ramo = r_base.veredito
    # nos dois ramos: as saturações conhecidas caem dentro da parte válida da grade de cada eixo
    for eixo, sat in (("f", r_base.ay_sat_f), ("r", r_base.ay_sat_r)):
        if sat is not None:
            ate = [ln for ln in r_base.linhas if ln.ay_ms2 <= sat + 1e-12]
            seguinte = [ln for ln in r_base.linhas if ln.ay_ms2 > sat][:1]
            ok_013 = ok_013 and all(getattr(ln, f"cap_{eixo}").motivo is None for ln in ate + seguinte)
    det_013 = f"ramo={ramo}; {_resumo(r_base)}"
check("TC-EQ-013: ds sem escala -> N/A 'fora da faixa do pneu', ou PUSH/LOOSE com o eixo não saturado válido "
      "além de ay_lim; nenhuma capacidade inválida usada", ok_013, det_013)

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
