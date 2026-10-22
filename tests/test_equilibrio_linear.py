"""
Testes do equilíbrio linear (V4.0, incremento 2).
TC-EQ-021..023: rigidez de deriva e de camber do PAC2002. TC-EQ-024..030: oráculos do Gillespie cap. 6 (IDs autorizados pelo usuário).
Roda como script: uv run python -X utf8 tests/test_equilibrio_linear.py
O dataset sem deslocamentos (ds0) é só de teste; não representa o pneu do carro.
"""

import dataclasses
import math
import os

import tire_model as tm

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
FZ0 = ds.p["FNOMIN"]

# ---------------- TC-EQ-021 : C_alpha = |Ky| sem deslocamentos ----------------
# Cópia só de teste: zera todos os PHY*, PVY* e RHY* (deslocamentos), sem tocar em ds.p.
p0 = {k: (0.0 if k.startswith(("PHY", "PVY", "RHY")) else v) for k, v in ds.p.items()}
ds0 = dataclasses.replace(ds, p=p0)
c_ref = abs(tm.pure_fy0(ds0.p, FZ0, 0.0, 0.0)[1]["Ky"])
c_num = tm.rigidez_deriva(ds0, FZ0)
err_021 = abs(c_num - c_ref) / c_ref
c_real = tm.rigidez_deriva(ds, FZ0)
check("TC-EQ-021: rigidez_deriva = |Ky| do PAC2002 sem deslocamentos (erro rel. < 1e-6); com o ds real, > 0",
      err_021 < 1e-6 and c_real > 0,
      f"C_alpha(ds0)={c_num:.3f} Ky={c_ref:.3f} err={err_021:.2e}; C_alpha(ds)={c_real:.3f} N/rad")

# ---------------- TC-EQ-022 : C_gamma por diferença central com outro passo ----------------
c_g = tm.rigidez_camber(ds, FZ0)
h2 = 1e-5
fy_p = tm.wheel_forces(ds, "FR", FZ0, 0.0, +h2, 0.0)[1]
fy_m = tm.wheel_forces(ds, "FR", FZ0, 0.0, -h2, 0.0)[1]
c_g2 = -(fy_p - fy_m) / (2 * h2)
err_022 = abs(c_g - c_g2) / abs(c_g2)
check("TC-EQ-022: rigidez_camber > 0 e igual à diferença central com passo 1e-5 (erro rel. < 1e-4)",
      c_g > 0 and err_022 < 1e-4,
      f"C_gamma={c_g:.3f} N/rad (passo 1e-5: {c_g2:.3f}) err={err_022:.2e}")

# ---------------- TC-EQ-023 : sensibilidade à carga (Gillespie p. 215) ----------------
c_meio = tm.rigidez_deriva(ds, 0.5 * FZ0)
c_nom = tm.rigidez_deriva(ds, FZ0)
cresce = c_nom > c_meio
razao_cai = (c_nom / FZ0) < (c_meio / (0.5 * FZ0))
check("TC-EQ-023: C_alpha cresce de 0,5*FNOMIN para FNOMIN e C_alpha/Fz cai (Gillespie p. 215; conferido no .tir atual)",
      cresce and razao_cai,
      f"C(0,5Fn)={c_meio:.1f} C(Fn)={c_nom:.1f} N/rad; C/Fz: {c_meio/(0.5*FZ0):.3f} -> {c_nom/FZ0:.3f} rad^-1")

# ---------------- Oráculos do Gillespie cap. 6 (exemplos resolvidos, pp. 231-235) ----------------
# Valores do livro em lb, in, ft e lb/deg; a conversão para SI é feita aqui, no teste.
import equilibrio_linear as el
import kinematics_model as km
from suspension_model import G

LB = 4.4482216
IN = 0.0254
FT = 0.3048
LBDEG = LB * 57.29578  # lb/deg -> N/rad

# TC-EQ-024: exemplo 1 (eq. 6-15), com C de eixo = 2 x C por pneu. O livro usa 950 e 776 lb por pneu (arredondados) e
# imprime K = 0,11 deg/g arredondando cada termo (4,09 - 3,98); a conta exata dá 0,1153.
K1 = el.gradiente_pneus(2 * 950 * LB, 2 * 776 * LB, 2 * 232 * LBDEG, 2 * 195 * LBDEG)
K1_dpg = el.para_graus_por_g(K1)
K1_exato = el.para_graus_por_g(el.gradiente_pneus(1901 * LB, 1552 * LB, 2 * 232 * LBDEG, 2 * 195 * LBDEG))
# Termos separados (W_r = 0 ou W_f = 0 zera o outro termo); o livro arredonda cada um antes de subtrair.
t_f = el.para_graus_por_g(el.gradiente_pneus(2 * 950 * LB, 0.0, 2 * 232 * LBDEG, 1.0))
t_r = -el.para_graus_por_g(el.gradiente_pneus(0.0, 2 * 776 * LB, 1.0, 2 * 195 * LBDEG))
K1_impresso = round(t_f, 2) - round(t_r, 2)
check("TC-EQ-024: exemplo 1 do Gillespie (p. 232), K = 950/232 - 776/195 = 0,1153 +- 0,0005 deg/g; termos arredondados (4,09 - 3,98) dão o 0,11 impresso",
      abs(K1_dpg - 0.1153) < 0.0005 and abs(K1_impresso - 0.11) < 1e-9,
      f"K={K1_dpg:.4f} deg/g com 950 e 776 lb por pneu; termos {t_f:.2f} - {t_r:.2f} = {K1_impresso:.2f} (livro imprime 0,11); "
      f"com os pesos exatos 1901/2 e 1552/2: {K1_exato:.4f} deg/g")

# TC-EQ-025: velocidade característica (eq. 6-18) e errata da p. 232
K_book = 0.11 * math.pi / 180 / G  # 0,11 deg/g em rad/(m/s^2)
v_impressa = el.velocidade_caracteristica(110.6 * IN, K_book) / FT
v_problema = el.velocidade_caracteristica(100.6 * IN, K_book) / FT
check("TC-EQ-025: V_char = 393 ft/s com L = 110,6 in (conta impressa) e 375 ft/s com L = 100,6 in, +- 1",
      abs(v_impressa - 393) < 1 and abs(v_problema - 375) < 1,
      f"errata do Gillespie p. 232: V_char usa 110,6 in; o problema dá 100,6 in. "
      f"L=110,6 in: {v_impressa:.1f} ft/s; L=100,6 in: {v_problema:.1f} ft/s")

# TC-EQ-026: ponto neutro (p. 233)
c_neutro_ft = el.ponto_neutro_ate_traseiro(8.38 * FT, 232, 195) / FT
check("TC-EQ-026: ponto neutro a 4,55 ft do eixo traseiro (c' = L C_f/(C_f+C_r), p. 233) +- 0,01",
      abs(c_neutro_ft - 4.55) < 0.01,
      f"c'={c_neutro_ft:.3f} ft; livro 4,55")

# TC-EQ-027: exemplo 2, gradiente de rolagem (eq. 6-32), K_phi em in.lb/deg -> N.m/rad
KPHI = LB * IN * 57.29578
dphi = el.para_graus_por_g(el.gradiente_rolagem(2750 * LB, 10 * IN, 1500 * KPHI, 1606 * KPHI))
check("TC-EQ-027: exemplo 2 (p. 234), dphi/da_y = W h1/(K_phi_f + K_phi_r - W h1) = 10,5 deg/g +- 0,05",
      abs(dphi - 10.5) < 0.05,
      f"dphi/da_y={dphi:.3f} deg/g; livro 10,5")

# TC-EQ-028: parcela de camber (eq. 6-56), Cg/Ca = 0,1, dgamma/dphi = 1 na frente
k_cam = el.parcela_camber(0.1, 1.0, 1.0, 0.1, 1.0, 0.0, 10.5)
check("TC-EQ-028: K_camber = (0,1 x 1,0 - 0,1 x 0) x 10,5 = 1,05 deg/g +- 0,005 (p. 234)",
      abs(k_cam - 1.05) < 0.005, f"K_camber={k_cam:.4f} deg/g; livro 1,05")

# TC-EQ-029: roll steer traseiro (eq. 6-57), eps_r = +0,122 rad/rad (SAE)
k_rs = km.roll_steer_understeer_deg_per_g(0.0, 0.122, 10.5)
check("TC-EQ-029: roll steer = (eps_f - eps_r) dphi/da_y = -1,281 +- 0,001 deg/g (SUS-415)",
      abs(k_rs - (-1.281)) < 0.001,
      f"K_rs={k_rs:.4f} deg/g; o livro imprime 1,28 e diz sobresterço (p. 235), coerente com o sinal negativo")

# TC-EQ-030: velocidade crítica vs característica
L_t, K_t = 2.5, 0.0021
check("TC-EQ-030: V_crit(L, -|K|) = V_char(L, |K|); V_char(L, -|K|) e V_crit(L, +|K|) = None",
      math.isclose(el.velocidade_critica(L_t, -K_t), el.velocidade_caracteristica(L_t, K_t), rel_tol=1e-12)
      and el.velocidade_caracteristica(L_t, -K_t) is None and el.velocidade_critica(L_t, K_t) is None,
      f"V={el.velocidade_caracteristica(L_t, K_t):.3f} m/s")

# ---------------- Parcelas de K de um caso e tabela linear (TC-EQ-031..038) ----------------
# Veículos de teste copiados de tests/test_equilibrio.py (números plausíveis, NÃO são setup do carro). Ganhos de
# camber, roll steer, escalas LMUY e geometrias extremas abaixo são entradas de teste rotuladas.
import equilibrio as eq
import suspension_model as sm
from suspension_model import VehicleConfig


def veiculo_base(**over) -> VehicleConfig:
    """Veículo de teste (cópia do tests/test_equilibrio.py; números plausíveis, NÃO é setup real)."""
    base = dict(
        mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
        cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
        roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0,
    )
    base.update(over)
    return VehicleConfig(**base)


cfg_b = veiculo_base()
_k_soma = cfg_b.roll_stiffness_front + cfg_b.roll_stiffness_rear


def veiculo_simetrico(lambda_f=0.5, **over):
    """Carro simétrico do TC-EQ-010 (cópia do tests/test_equilibrio.py; só de teste)."""
    L = cfg_b.wheelbase
    return veiculo_base(**{**dict(cg_to_front=L / 2, cg_to_rear=L / 2, track_rear=cfg_b.track_front,
                                  roll_stiffness_front=lambda_f * _k_soma,
                                  roll_stiffness_rear=(1 - lambda_f) * _k_soma,
                                  roll_center_rear=cfg_b.roll_center_front,
                                  unsprung_mass_rear=cfg_b.unsprung_mass_front,
                                  unsprung_cg_height_rear=cfg_b.unsprung_cg_height_front), **over})


def _sem_excecao(fn):
    try:
        return fn(), None
    except Exception as e:  # o check precisa registrar qualquer exceção como falha
        return None, f"{type(e).__name__}: {e}"


def _gpg(k):
    return "None" if k is None else f"{el.para_graus_por_g(k):+.5f}"


def _resumo_p(p):
    if p is None:
        return "sem resultado"
    return (f"a_y={p.ay_ms2 / G:.3f} g: pneus={_gpg(p.k_pneus)} transf={_gpg(p.k_transferencia)} "
            f"desl={_gpg(p.k_deslocamento)} camber={_gpg(p.k_camber)} rs={_gpg(p.k_roll_steer)} total={_gpg(p.k_total)} °/g, "
            f"dphi/day={_gpg(p.dphi_day)} °/g, motivo={p.motivo!r}")


ds_sim = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.5})      # escala só de teste (TC-EQ-010)
ds_045 = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.45})     # escala só de teste (TC-EQ-011)

# ---------------- TC-EQ-031 : carro simétrico -> K = 0 ----------------
caso_sim = eq.CasoEquilibrio(cfg=veiculo_simetrico(0.5), ds=ds_sim)
p031, e031 = _sem_excecao(lambda: el.parcelas_k(caso_sim, 0.3 * G))
ok_031 = False
if p031 is not None and p031.k_total is not None:
    t031 = el.texto_k(p031, "● Dado do TX")
    if p031.k_total == 0.0:
        sinal_ok = t031.endswith(" · Neutro")
    elif p031.k_total > 0.0:
        sinal_ok = t031.endswith(" · Subesterço")
    else:
        sinal_ok = t031.endswith(" · Sobresterço")
    ok_031 = abs(p031.k_pneus) < 1e-12 and abs(p031.k_total) < 1e-12 and sinal_ok
else:
    t031 = None
check("TC-EQ-031: carro simétrico (TC-EQ-010) em 0,3 g -> k_pneus = 0 e k_total ~ 0 (|.| < 1e-12); "
      "'Neutro' só com k_total == 0 exato, senão o sinal manda",
      ok_031, (e031 or _resumo_p(p031)) + f"; k_total={getattr(p031, 'k_total', None)!r}; texto={t031!r}")

# ---------------- TC-EQ-032 : mais rigidez de rolagem na frente -> mais K de transferência ----------------
p05, e05 = _sem_excecao(lambda: el.parcelas_k(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.5), ds=ds_045), 0.3 * G))
p07, e07 = _sem_excecao(lambda: el.parcelas_k(eq.CasoEquilibrio(cfg=veiculo_simetrico(0.7), ds=ds_045), 0.3 * G))
check("TC-EQ-032: lambda_f 0,7 contra 0,5 (LMUY 0,45, só de teste) -> k_transferencia em 0,3 g maior com 0,7 "
      "(Gillespie p. 214)",
      p05 is not None and p07 is not None and p05.k_transferencia is not None
      and p07.k_transferencia is not None and p07.k_transferencia > p05.k_transferencia,
      f"0,5: {e05 or _resumo_p(p05)} | 0,7: {e07 or _resumo_p(p07)}")

# ---------------- TC-EQ-033 : roda descolada -> parcela N/A, sem exceção ----------------
# Bitolas de 0,20 m: geometria só de teste, para a roda interna descolar em 0,4 g.
caso_desc = eq.CasoEquilibrio(cfg=veiculo_base(track_front=0.20, track_rear=0.20), ds=ds)
fz_desc = eq.cargas(caso_desc, 0.4 * G)
p033, e033 = _sem_excecao(lambda: el.parcelas_k(caso_desc, 0.4 * G))
check("TC-EQ-033: roda interna descolada em 0,4 g (bitola de teste) -> k_transferencia e k_total None, motivo com "
      "'descolamento', sem exceção",
      min(fz_desc.values()) <= 0.0 and p033 is not None and p033.k_transferencia is None
      and p033.k_total is None and "descolamento" in (p033.motivo or ""),
      (e033 or _resumo_p(p033)) + f"; Fz={ {c: round(v, 1) for c, v in fz_desc.items()} }")

# ---------------- TC-EQ-034 : passo 1 = inclinação inicial do passo 2 ----------------
GANHO_TESTE = {"FL": -0.8, "FR": 0.8, "RL": -0.6, "RR": 0.6}   # gradientes de eixo 0,8 e 0,6: só de teste
ok_034, det_034 = [], []


def _comparar_034(dset, ganho, **extra):
    """(rel, detalhe) de |k_inclinacao(1ª linha) − (pneus + deslocamento + camber)| / |...|, ou (None, erro).
    extra: outras entradas do CasoEquilibrio (toe, raio, Ackermann; valores de teste)."""
    caso34 = eq.CasoEquilibrio(cfg=cfg_b, ds=dset, ganho_camber=ganho, **extra)
    tab, e34 = _sem_excecao(lambda: el.tabela_linear(caso34, ay_max_g=0.05))
    if (tab is None or tab[0]["k_inclinacao"] is None
            or any(x is None for x in (tab[0]["parcelas"].k_pneus, tab[0]["parcelas"].k_deslocamento,
                                       tab[0]["parcelas"].k_camber))):
        return None, None, e34 or "k_inclinacao ou parcela None"
    p0 = tab[0]["parcelas"]
    soma = p0.k_pneus + p0.k_deslocamento + p0.k_camber
    rel = abs(tab[0]["k_inclinacao"] - soma) / abs(soma)
    return rel, p0, (f"inclinação={_gpg(tab[0]['k_inclinacao'])}, pneus+desl+camber={_gpg(soma)} °/g "
                     f"(pneus={_gpg(p0.k_pneus)}, desl={_gpg(p0.k_deslocamento)}, camber={_gpg(p0.k_camber)}), "
                     f"rel={rel:.2e}")


for rotulo, ganho in (("sem ganho de camber", {c: 0.0 for c in eq.CANTOS}), ("com ganho de teste", GANHO_TESTE)):
    rel34, _, d34 = _comparar_034(ds, ganho)
    ok_034.append(rel34 is not None and rel34 < 1e-3)
    det_034.append(f"{rotulo}: {d34}")
# Rigidez do eixo no ponto de operação (toe, raio e Ackermann entram no C do passo 1 como no passo 2). Valores de
# teste, NÃO são setup do carro: toe dianteiro 0,25° nas duas rodas (toe-out, EDR-002), R = 8,0 m e Ackermann 100 %.
TOE_TESTE = math.radians(0.25)
EXTRAS_034 = (
    ("toe dianteiro 0,25° (teste)", dict(toe_rad={"FL": TOE_TESTE, "FR": TOE_TESTE, "RL": 0.0, "RR": 0.0})),
    ("R = 8,0 m (teste)", dict(raio_m=8.0)),
    ("R = 8,0 m e Ackermann 100 % (teste)", dict(raio_m=8.0, ackermann_pct=100.0)),
)
for rotulo, extra in EXTRAS_034:
    for rot_g, ganho in (("sem ganho", {c: 0.0 for c in eq.CANTOS}), ("ganho de teste", GANHO_TESTE)):
        rel34, _, d34 = _comparar_034(ds, ganho, **extra)
        ok_034.append(rel34 is not None and rel34 < 1e-3)
        det_034.append(f"{rotulo}, {rot_g}: {d34}")
# Registro (não decide o check): no ds0 (sem PHY/PVY/RHY, só de teste) o deslocamento do pneu some.
_, p34_0, d34_0 = _comparar_034(ds0, {c: 0.0 for c in eq.CANTOS})
det_034.append(f"ds0 (sem deslocamentos): {d34_0}")
check("TC-EQ-034: k_inclinacao da 1ª linha (passo 2, Richardson das secantes de 0,005 e 0,01 g) = k_pneus + k_deslocamento + k_camber "
      "(passo 1), rel < 1e-3, com e sem ganho de camber, também com toe dianteiro 0,25°, R = 8,0 m e R = 8,0 m com "
      "Ackermann 100 % (veículo e entradas de teste, .tir real, sem roll steer: o passo 2 não tem roll steer)",
      len(ok_034) == 2 + 2 * len(EXTRAS_034) and all(ok_034), " | ".join(det_034))

# ---------------- TC-EQ-035 : sinal do camber (EDR-002) ----------------
# Braços paralelos iguais na frente (gradiente de eixo +1, Gillespie p. 234): só de teste.
caso35 = eq.CasoEquilibrio(cfg=cfg_b, ds=ds, ganho_camber={"FL": -1.0, "FR": 1.0, "RL": 0.0, "RR": 0.0})
p035, e035 = _sem_excecao(lambda: el.parcelas_k(caso35, 0.0))
check("TC-EQ-035: gradiente de camber de eixo +1 na frente (só de teste) -> k_camber > 0 (subesterço, exemplo 2 "
      "do Gillespie, p. 234; EDR-002)",
      p035 is not None and p035.k_camber is not None and p035.k_camber > 0.0, e035 or _resumo_p(p035))

# ---------------- TC-EQ-036 : K_llt aproximado (eq. 6-49) x exato ----------------
caso36 = eq.CasoEquilibrio(cfg=cfg_b, ds=ds)
x36, e36 = _sem_excecao(lambda: el.cruzamento_transferencia(caso36, 0.2 * G))
ok_036, det_036 = False, e36 or ""
if x36 is not None and x36["b_f"] is not None and x36["b_r"] is not None:
    info_global = (f"ajuste global (só informação): a={x36['a_global']:.4f} 1/rad, b={x36['b_global']:.4e} "
                   f"1/(rad·N), r={x36['r']:.3e}")
    if x36["b_f"] > 0 and x36["b_r"] > 0:
        ap, ex = x36["aprox"], x36["exato"]
        tol = 2.0 * x36["eps"] if x36["eps"] is not None else -1.0
        rel36 = abs(ap - ex) / abs(ex) if (ap is not None and ex) else math.inf
        ok_036 = (ap is not None and ex is not None and ap * ex > 0 and rel36 <= tol and x36["motivo"] is None)
        det_036 = (f"b local: F={x36['b_f']:.4e}, R={x36['b_r']:.4e} 1/(rad·N); aprox={_gpg(ap)} exato={_gpg(ex)} °/g; "
                   f"dif. rel.={rel36:.3e} <= 2·eps={tol:.3e} (eps_f={x36['eps_f']:.3e}, eps_r={x36['eps_r']:.3e}, "
                   f"eixo mais carregado); {info_global}")
    else:
        ok_036 = x36["motivo"] == "polinômio sem sensibilidade à carga no trecho"
        det_036 = f"b local F={x36['b_f']:.4e}, R={x36['b_r']:.4e}; motivo={x36['motivo']!r}; {info_global}"
check("TC-EQ-036: K_llt aproximado (Gillespie eq. 6-49, b = −½·d²C_α/dFz² local no Fz estático de cada eixo) x "
      "exato em 0,2 g: mesmo sinal e diferença <= 2·eps do eixo mais carregado; b local <= 0 -> motivo "
      "'sem sensibilidade'",
      ok_036, det_036)

# ---------------- TC-EQ-037 : texto exato de K ----------------
k037 = math.radians(0.123) / G   # +0,123 °/g em rad/(m/s²); ParcelasK só de teste
t037, e037 = _sem_excecao(lambda: el.texto_k(
    el.ParcelasK(ay_ms2=0.0, k_pneus=k037, k_transferencia=0.0, k_deslocamento=0.0, k_camber=0.0,
                 k_roll_steer=0.0, k_total=k037, dphi_day=0.0, motivo=None), "◐ Dado do T09"))
esp037 = ("DEMONSTRATIVO · K = +0,12 °/g (pneus + transferência + deslocamento com a carga (ply steer, conicidade, toe e "
          "camber estático) + camber + roll steer; sem compliance, torque de alinhamento e tração) · Subesterço")
check("TC-EQ-037: texto_k com pior origem '◐ Dado do T09' e K = +0,123 °/g é o texto exato da spec §6",
      t037 == esp037, e037 or f"obtido={t037!r}")

# ---------------- TC-EQ-038 : tabela linear e roll steer linha a linha ----------------
RS_TESTE = {"F": 0.05, "R": -0.03}   # ε em rad/rad (SUS-415): só de teste
caso38 = eq.CasoEquilibrio(cfg=cfg_b, ds=ds, roll_steer=RS_TESTE)
tab38, e38 = _sem_excecao(lambda: el.tabela_linear(caso38))
ok_038 = False
if tab38 is not None:
    ays = [ln["ay_ms2"] for ln in tab38]
    rs_ok = all(ln["parcelas"].k_roll_steer is not None and ln["parcelas"].dphi_day is not None
                and abs(ln["parcelas"].k_roll_steer
                        - (RS_TESTE["F"] - RS_TESTE["R"]) * ln["parcelas"].dphi_day) < 1e-15 for ln in tab38)
    ok_038 = (len(tab38) == int(0.4 / 0.05) + 1 and all(b > a for a, b in zip(ays, ays[1:])) and rs_ok)
    det_038 = f"{len(tab38)} linhas, a_y [g]={[round(a / G, 3) for a in ays]}; " + _resumo_p(tab38[-1]["parcelas"])
else:
    det_038 = e38
check("TC-EQ-038: tabela_linear tem int(0,4/0,05)+1 linhas, a_y crescente, k_roll_steer = (eps_f − eps_r)·dphi_day "
      "linha a linha (eps de teste)", ok_038, det_038)

# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
