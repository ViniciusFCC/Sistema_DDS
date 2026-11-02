"""
Testes do modelo estático de pneu PAC2002 (python/tire_model_static.py), sobre os .tir do TTC Round 6
(Hoosier R25B 20.5x7-13 em aro de 7 in; 8, 10, 12 e 14 psi; eixo ISO_TYDEX).

Os .tir ficam FORA do Git (references/ttc/round6_hoosier_r25b_20p5x7_13_7in/, ou o diretório da variável de
ambiente DDS_TTC_DIR). Sem eles o script diz NÃO EXECUTÁVEL e sai com código 3: isso nunca conta como aprovado.

Mx e Mz são conferidos contra transcrições independentes, escritas aqui, das equações do help do Adams
(MSC Adams Tire, PAC2002: Mx eq. 109, p. 48; Mz eqs. 100-108, p. 47). "Passou" = concordância com a transcrição
da equação, não validação contra medição (Validation = NOT_VALIDATED).

Uso: uv run python -X utf8 tests/test_tire_static.py
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import tire_model as base
import tire_model_static as ts

HERE = Path(__file__).resolve().parent
DEG = math.pi / 180.0
SUBDIR = Path("references") / "ttc" / "round6_hoosier_r25b_20p5x7_13_7in"
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL"))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def tem_quatro_tir(c):
    return c.is_dir() and len(list(c.glob("*PAC02_UM4.tir"))) >= 4


def achar_diretorio_ttc():
    """DDS_TTC_DIR (se definido, só ele: inválido = NÃO EXECUTÁVEL, sem cair para outra pasta), a raiz deste
    checkout ou a raiz do repositório principal (worktrees ficam em .claude/worktrees/x)."""
    env = os.environ.get("DDS_TTC_DIR")
    if env:
        if tem_quatro_tir(Path(env)):
            return Path(env)
        print(f"NÃO EXECUTÁVEL: DDS_TTC_DIR={env} não é uma pasta com os quatro .tir *PAC02_UM4.tir do TTC "
              "Round 6; nenhuma outra pasta foi tentada. Não conta como aprovado.")
        raise SystemExit(3)
    raiz = HERE.parent
    candidatos = [raiz / SUBDIR]
    if len(raiz.parents) >= 3 and raiz.parent.name == "worktrees":
        candidatos.append(raiz.parents[2] / SUBDIR)
    for c in candidatos:
        if tem_quatro_tir(c):
            return c
    return None


TTC = achar_diretorio_ttc()
if TTC is None:
    print("NÃO EXECUTÁVEL: .tir do TTC Round 6 não encontrados (defina DDS_TTC_DIR ou coloque em "
          f"{SUBDIR}). Não conta como aprovado.")
    raise SystemExit(3)

FAMILIA = ts.load_profile_family(TTC, source_axis_system="ISO_TYDEX")
P12 = FAMILIA.at_pressure(12.0)


class Par(dict):
    """Parâmetros do .tir; ausente = default do help (fator L* = 1, demais coeficientes = 0)."""

    def __missing__(self, chave):
        return 1.0 if chave.startswith("L") else 0.0


# ---------------------------------------------------------------------------------------------------------
# Transcrições independentes (não reutilizam _mx nem _mz do módulo)
# ---------------------------------------------------------------------------------------------------------
def mx_eq109(P, fz, fy, gam, qsx6_quadrado=True):
    """Help do Adams, eq. 109 (p. 48), com dpi = 0 (perfil em IP = IP_NOM):
    Mx = R0 Fz { QSX3 Fy/F'z0 + QSX4 cos[QSX5 atan((QSX6 Fz/F'z0)^2)] sin[QSX7 gam + QSX8 atan(QSX9 Fy/F'z0)]
                 + [QSX10 atan(QSX11 Fz/F'z0) - QSX2 (1 + QPX1 dpi)] gam + QSX1 LVMX } LMX"""
    fz0 = P["LFZO"] * P["FNOMIN"]
    R0 = P["UNLOADED_RADIUS"]
    expoente = 2 if qsx6_quadrado else 1                      # False só para provar que o quadrado importa
    chave = (P["QSX3"] * fy / fz0
             + P["QSX4"] * math.cos(P["QSX5"] * math.atan((P["QSX6"] * fz / fz0) ** expoente))
             * math.sin(P["QSX7"] * gam + P["QSX8"] * math.atan(P["QSX9"] * fy / fz0))
             + (P["QSX10"] * math.atan(P["QSX11"] * fz / fz0) - P["QSX2"]) * gam
             + P["QSX1"] * P["LVMX"])
    return R0 * fz * chave * P["LMX"]


def mz_eq100(P, fz, alpha, gam, kappa, fx, fy, info, teto_et=True):
    """Help do Adams, eqs. 100-108 (p. 47). Devolve (termo de trilha, resíduo, s*Fx) separados, para isolar o
    termo de Fx. O Fy do termo de trilha é o Fy com a cambagem real, F'y = Fy - SVyk (Pacejka 4.E71)."""
    fz0 = P["LFZO"] * P["FNOMIN"]
    R0 = P["UNLOADED_RADIUS"]
    dfz = (fz - fz0) / fz0
    gz = gam * P["LGAZ"]
    Kx, Ky = info["Kx"], info["Ky"]
    # eq. 45-46: ângulos de trilha e de resíduo (com deslocamentos)
    a_t = alpha + P["QHZ1"] + P["QHZ2"] * dfz + (P["QHZ3"] + P["QHZ4"] * dfz) * gz
    a_r = alpha + info["SHy"] + info["SVy"] / Ky

    def a_eq(a):                                                                     # eqs. 106 e 107
        return math.atan(math.sqrt(math.tan(a) ** 2 + (Kx / Ky) ** 2 * kappa ** 2) * (1 if a > 0 else -1 if a < 0 else 0))

    Bt = (P["QBZ1"] + P["QBZ2"] * dfz + P["QBZ3"] * dfz ** 2) * (1 + P["QBZ4"] * gz + P["QBZ5"] * abs(gz)) * P["LKY"] / P["LMUY"]
    Ct = P["QCZ1"]
    Dt = fz * (P["QDZ1"] + P["QDZ2"] * dfz) * (1 + P["QDZ3"] * gz + P["QDZ4"] * gz ** 2) * (R0 / fz0) * P["LTR"]
    Et = (P["QEZ1"] + P["QEZ2"] * dfz + P["QEZ3"] * dfz ** 2) * (1 + (P["QEZ4"] + P["QEZ5"] * gz) * (2 / math.pi) * math.atan(Bt * Ct * a_t))
    if teto_et:                                                                      # Et <= 1 (False só para provar o teto)
        Et = min(Et, 1.0)
    at = a_eq(a_t)
    t = Dt * math.cos(Ct * math.atan(Bt * at - Et * (Bt * at - math.atan(Bt * at)))) * math.cos(alpha)      # eq. 102
    Br = P["QBZ9"] * P["LKY"] / P["LMUY"] + P["QBZ10"] * info["By"] * info["Cy"]
    Dr = fz * R0 * P["LMUGAMMA"] * P["LRES"] * (P["QDZ6"] + P["QDZ7"] * dfz + (P["QDZ8"] + P["QDZ9"] * dfz) * gz)
    Mzr = Dr * math.cos(math.atan(Br * a_eq(a_r))) * math.cos(alpha)                                     # eq. 104
    s = (P["SSZ1"] + P["SSZ2"] * fy / fz0 + (P["SSZ3"] + P["SSZ4"] * dfz) * gam) * R0 * P["LS"]         # eq. 108
    Fy_linha = fy - info["SVyk"]                                                                       # eq. 103
    return -t * Fy_linha, Mzr, s * fx


def operar(profile, fz, alpha_deg, gam_deg, kappa, vx=10.0):
    return ts.evaluate_static(profile, fz_n=fz, alpha_rad=alpha_deg * DEG, camber_rad=gam_deg * DEG,
                              kappa=kappa, vx_mps=vx)


def forcas(profile, fz, alpha_deg, gam_deg, kappa):
    return base.combined_forces(profile.dataset, fz, alpha_deg * DEG, gam_deg * DEG, kappa)


# ---------------------------------------------------------------------------------------------------------
# Mx (eq. 109)
# ---------------------------------------------------------------------------------------------------------
P = Par(P12.dataset.p)
pontos = [(fz, a, g, k) for fz in (500.0, 1054.0, 1500.0) for a in (0.0, 4.0, 8.0)
          for g in (0.0, -2.0, -3.0) for k in (0.0, 0.08, -0.10)]
worst_mx = 0.0
for fz, a, g, k in pontos:
    r = operar(P12, fz, a, g, k)
    ref = mx_eq109(P, fz, r.fy_n, g * DEG)
    worst_mx = max(worst_mx, abs(r.mx_nm - ref))
check("estático /Mx-1: Mx do módulo == transcrição independente da eq. 109 em 81 pontos (12 psi); tol. 1e-9 N.m",
      worst_mx < 1e-9, f"dif máx={worst_mx:.2e} N.m")

for (fz, a, g, k), esperado in (((1054.0, 4.0, 0.0, 0.0), -38.6), ((1054.0, 0.0, 0.0, 0.0), -1.2),
                                ((1500.0, 8.0, 0.0, 0.0), -83.0)):
    mx = operar(P12, fz, a, g, k).mx_nm
    check(f"estático /Mx-2: valor de referência da transcrição, Fz={fz:g} N, alpha={a:g}, gamma={g:g} -> {esperado} N.m (tol. 0,1)",
          abs(mx - esperado) < 0.1, f"Mx={mx:.3f}")

# o termo QSX10 so atua com camber (multiplica gamma) e o QSX6 entra ao quadrado: sensibilidade da correção
r0 = operar(P12, 1054.0, 0.0, 0.0, 0.0)
rg = operar(P12, 1054.0, 0.0, -3.0, 0.0)
rev = ts.revise_profile(P12, {"QSX10": P["QSX10"] + 0.01}, reason="teste de sensibilidade", revision_id="T-QSX10")
d0 = operar(rev, 1054.0, 0.0, 0.0, 0.0).mx_nm - r0.mx_nm
dg = operar(rev, 1054.0, 0.0, -3.0, 0.0).mx_nm - rg.mx_nm
check("estático /Mx-3: QSX10 multiplica gamma (sem camber, mudar QSX10 não altera Mx; com camber altera)",
      abs(d0) < 1e-12 and abs(dg) > 1e-3, f"dMx(gamma=0)={d0:.2e}; dMx(gamma=-3)={dg:.4f}")

# ---------------------------------------------------------------------------------------------------------
# Mz (eqs. 100-108): sinal do termo s*Fx
# ---------------------------------------------------------------------------------------------------------
worst_mz = 0.0
worst_sfx = 0.0
for fz, a, g, k in pontos:
    fx, fy, info = forcas(P12, fz, a, g, k)
    trilha, mzr, sfx = mz_eq100(P, fz, a * DEG, g * DEG, k, fx, fy, info)
    r = operar(P12, fz, a, g, k)
    worst_mz = max(worst_mz, abs(r.mz_nm - (trilha + mzr + sfx)))
check("estático /Mz-1: Mz do módulo == -t F'y + Mzr + s Fx da transcrição independente em 81 pontos; tol. 1e-9 N.m",
      worst_mz < 1e-9, f"dif máx={worst_mz:.2e} N.m")

# Isola s*Fx sem depender da transcrição de s: zera SSZ1..SSZ4 por revisão (s = 0) e compara
zerado = ts.revise_profile(P12, {"SSZ1": 0.0, "SSZ2": 0.0, "SSZ3": 0.0, "SSZ4": 0.0}, reason="s = 0 para isolar s*Fx",
                           revision_id="T-S0")
for fz, a, g, k in ((1054.0, 4.0, 0.0, 0.08), (1054.0, 4.0, -2.0, -0.10), (1500.0, 8.0, -3.0, 0.08)):
    fx, fy, info = forcas(P12, fz, a, g, k)
    s = (P["SSZ1"] + P["SSZ2"] * fy / (P["LFZO"] * P["FNOMIN"])
         + (P["SSZ3"] + P["SSZ4"] * (fz - P["LFZO"] * P["FNOMIN"]) / (P["LFZO"] * P["FNOMIN"])) * g * DEG) * P["UNLOADED_RADIUS"] * P["LS"]
    dif = operar(P12, fz, a, g, k).mz_nm - operar(zerado, fz, a, g, k).mz_nm
    check(f"estático /Mz-2: Mz - Mz(s=0) == +s*Fx (sinal positivo), Fz={fz:g}, alpha={a:g}, gamma={g:g}, kappa={k:g}",
          abs(dif - s * fx) < 1e-9 and abs(dif) > 0.1, f"dif={dif:.4f} N.m; s*Fx={s * fx:.4f} N.m")

for (fz, a, g, k), esperado in (((1054.0, 4.0, 0.0, 0.08), 7.5), ((1054.0, 4.0, -2.0, -0.10), 46.9)):
    mz = operar(P12, fz, a, g, k).mz_nm
    check(f"estático /Mz-3: valor de referência (só a correção do sinal), Fz={fz:g}, alpha={a:g}, gamma={g:g}, kappa={k:g} -> {esperado} N.m (tol. 0,1)",
          abs(mz - esperado) < 0.1, f"Mz={mz:.3f}")


# ---------------------------------------------------------------------------------------------------------
# Velocidade: LONGVL é a velocidade de medição do TTC, não um limite
# ---------------------------------------------------------------------------------------------------------
vref = P["LONGVL"]
r_ok = operar(P12, 1054.0, 4.0, 0.0, 0.0, vx=vref)
check("estático /Vx-1: Vx == LONGVL não gera aviso de velocidade",
      not any("LONGVL" in m for m in r_ok.limitations))
try:
    r_alta = operar(P12, 1054.0, 4.0, 0.0, 0.0, vx=1.5 * vref)
    avisos = [m for m in r_alta.limitations if "LONGVL" in m]
    check("estático /Vx-2: Vx > LONGVL não lança erro e acrescenta aviso em limitations",
          len(avisos) == 1 and "My" in avisos[0] and "1.50" in avisos[0], avisos[0] if avisos else "sem aviso")
    check("estático /Vx-3: Fx, Fy, Mx e Mz não dependem de Vx (só o My usa a velocidade)",
          (r_alta.fx_n, r_alta.fy_n, r_alta.mx_nm, r_alta.mz_nm) == (r_ok.fx_n, r_ok.fy_n, r_ok.mx_nm, r_ok.mz_nm))
except ts.StaticTireError as exc:
    check("estático /Vx-2: Vx > LONGVL não lança erro e acrescenta aviso em limitations", False, f"lançou {exc}")
try:
    operar(P12, 1054.0, 4.0, 0.0, 0.0, vx=-1.0)
    check("estático /Vx-4: Vx < 0 lança StaticTireError", False, "não lançou")
except ts.StaticTireError:
    check("estático /Vx-4: Vx < 0 lança StaticTireError", True)


# ---------------------------------------------------------------------------------------------------------
# Perfis e pressões
# ---------------------------------------------------------------------------------------------------------
check("estático /Perfis-1: os quatro perfis (8, 10, 12 e 14 psi) carregam e a lista de pressões bate",
      len(FAMILIA.profiles) == 4 and all(abs(a - b) < 1e-3 for a, b in zip(FAMILIA.pressures_psi, (8.0, 10.0, 12.0, 14.0))),
      str(FAMILIA.pressures_psi))
check("estático /Perfis-2: cada perfil declara eixo ISO_TYDEX e IP == IP_NOM",
      all(pr.dataset.axis_system == "ISO_TYDEX" and pr.dataset.p["IP"] == pr.dataset.p["IP_NOM"] for pr in FAMILIA.profiles.values()))
for psi_sem_perfil in (9.0, 11.0, 13.0, 16.0):
    try:
        FAMILIA.at_pressure(psi_sem_perfil)
        check(f"estático /Perfis-3: {psi_sem_perfil:g} psi sem perfil é recusada (sem interpolação)", False, "não lançou")
    except ts.StaticTireError as exc:
        check(f"estático /Perfis-3: {psi_sem_perfil:g} psi sem perfil é recusada (sem interpolação)", "Interpolação" in str(exc))
try:
    ts.load_profile(next(iter(FAMILIA.profiles.values())).source_path)
    check("estático /Perfis-4: load_profile exige o eixo declarado", False, "não lançou")
except ts.StaticTireError:
    check("estático /Perfis-4: load_profile exige o eixo declarado", True)

# ---------------------------------------------------------------------------------------------------------
# Overlay de revisão (num diretório temporário)
# ---------------------------------------------------------------------------------------------------------
def recusa(nome, fn, trecho):
    try:
        fn()
        check(nome, False, "não lançou")
    except ts.StaticTireError as exc:
        check(nome, trecho in str(exc), str(exc))


sha_antes = hashlib.sha256(P12.source_path.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as tmp:
    rev = ts.revise_profile(P12, {"PDY1": P["PDY1"] * 1.05}, reason="teste de overlay", revision_id="T-OVL")
    arq = Path(tmp) / "rev.json"
    ts.save_revision(rev, arq)
    de_volta = ts.load_revision(P12, arq)
    r1, r2 = operar(rev, 1054.0, 4.0, -2.0, 0.05), operar(de_volta, 1054.0, 4.0, -2.0, 0.05)
    check("estático /Overlay-1: salvar e reabrir reproduz a revisão (mesmo resultado, mesmo id) e difere do perfil base",
          (r1.fy_n, r1.mz_nm) == (r2.fy_n, r2.mz_nm) and de_volta.revision_id == "T-OVL"
          and abs(r1.fy_n - operar(P12, 1054.0, 4.0, -2.0, 0.05).fy_n) > 1.0)
    recusa("estático /Overlay-2: não sobrescreve overlay existente", lambda: ts.save_revision(rev, arq), "já existe")
    payload = json.loads(arq.read_text(encoding="utf-8"))

    def variante(nome, **mudanca):
        d = Path(tmp) / f"{nome}.json"
        d.write_text(json.dumps({**payload, **mudanca}), encoding="utf-8")
        return d

    recusa("estático /Overlay-3: recusa hash do .tir diferente", lambda: ts.load_revision(P12, variante("hash", source_sha256="0" * 64)), "hash")
    recusa("estático /Overlay-4: recusa eixo diferente", lambda: ts.load_revision(P12, variante("eixo", axis_system="SAE_CALSPAN")), "eixos")
    recusa("estático /Overlay-5: recusa pressão diferente", lambda: ts.load_revision(P12, variante("psi", pressure_psi=10.0)), "pressão")
    recusa("estático /Overlay-6: aplicar o overlay de 12 psi a outro perfil é recusado (hash)",
           lambda: ts.load_revision(FAMILIA.at_pressure(10.0), arq), "hash")
    recusa("estático /Overlay-7: overlay de outra versão do modelo é recusado (as equações mudaram na 4.1.0)",
           lambda: ts.load_revision(P12, variante("versao", model_version="4.0.1-static")), "outra versão")
check("estático /Overlay-8: o .tir de origem continua com o mesmo SHA-256",
      hashlib.sha256(P12.source_path.read_bytes()).hexdigest() == sha_antes == P12.base_sha256)

# ---------------------------------------------------------------------------------------------------------
# Resultados finitos dentro das faixas declaradas
# ---------------------------------------------------------------------------------------------------------
n_pts = 0
n_ruim = 0
for psi in FAMILIA.pressures_psi:
    pr = FAMILIA.at_pressure(psi)
    q = pr.dataset.p
    for fz in (q["FZMIN"], 0.5 * (q["FZMIN"] + q["FZMAX"]), q["FNOMIN"], q["FZMAX"]):
        for a in (q["ALPMIN"], 0.0, 0.5 * q["ALPMAX"], q["ALPMAX"]):
            for g in (q["CAMMIN"], 0.0, q["CAMMAX"]):
                for k in (q["KPUMIN"], 0.0, q["KPUMAX"]):
                    r = ts.evaluate_static(pr, fz_n=fz, alpha_rad=a, camber_rad=g, kappa=k, vx_mps=15.0)
                    n_pts += 1
                    if not all(math.isfinite(v) for v in (r.fx_n, r.fy_n, r.mx_nm, r.my_nm, r.mz_nm, r.mu_effective)):
                        n_ruim += 1
check(f"estático /Faixas-1: Fx, Fy, Mx, My, Mz e mu finitos em {n_pts} pontos dentro das faixas declaradas (4 perfis)",
      n_pts > 0 and n_ruim == 0, f"{n_ruim} não finitos")
try:
    operar(P12, 1054.0, 20.0, 0.0, 0.0)
    check("estático /Faixas-2: alpha fora da faixa declarada é recusado", False, "não lançou")
except base.TireRangeError:
    check("estático /Faixas-2: alpha fora da faixa declarada é recusado", True)

# ---------------------------------------------------------------------------------------------------------
# Avisos de coeficientes e fatores ausentes
# ---------------------------------------------------------------------------------------------------------
sem_aviso_momentos = True
fatores_ausentes = {}
for psi in FAMILIA.pressures_psi:
    lim = operar(FAMILIA.at_pressure(psi), 1054.0, 4.0, -2.0, 0.05).limitations
    if any("Coeficientes de momento ausentes" in m for m in lim):
        sem_aviso_momentos = False
    fatores_ausentes[psi] = [m for m in lim if "Fatores de escala ausentes" in m]
check("estático /Avisos-1: nenhum dos quatro perfis tem coeficiente de momento ausente (sem aviso em limitations)",
      sem_aviso_momentos)
esperado_fator = "Fatores de escala ausentes no .tir foram assumidos iguais a 1: LMUGAMMA."
check("estático /Avisos-2: nos quatro perfis falta exatamente o fator LMUGAMMA (os outros nove estão no .tir) e o aviso diz isso",
      all(v == [esperado_fator] for v in fatores_ausentes.values())
      and all(set(ts.MOMENT_SCALING_FACTORS) - set(pr.dataset.p) == {"LMUGAMMA"} for pr in FAMILIA.profiles.values()),
      str(fatores_ausentes))

# ---------------------------------------------------------------------------------------------------------
# Fatores de escala diferentes de 1 (revise_profile), contra as transcrições
# ---------------------------------------------------------------------------------------------------------
FATORES = {"LMX": 0.9, "LVMX": 1.2, "LS": 0.8, "LTR": 1.1, "LKY": 0.95, "LMUY": 1.05, "LGAZ": 0.85}
MOMENTO_DO_FATOR = {"LMX": "mx", "LVMX": "mx", "LS": "mz", "LTR": "mz", "LKY": "mz", "LMUY": "mz", "LGAZ": "mz"}
pontos_fator = [(1054.0, 4.0, -2.0, 0.08), (1500.0, 8.0, -3.0, -0.10), (500.0, 2.0, -1.0, 0.05)]


def mx_mz_transcritos(rev, fz, a, g, k):
    Pr = Par(rev.dataset.p)
    fx, fy, info = forcas(rev, fz, a, g, k)
    return mx_eq109(Pr, fz, fy, g * DEG), sum(mz_eq100(Pr, fz, a * DEG, g * DEG, k, fx, fy, info))


def dif_com_transcricao(rev):
    dmax = 0.0
    for fz, a, g, k in pontos_fator:
        r = operar(rev, fz, a, g, k)
        mx_ref, mz_ref = mx_mz_transcritos(rev, fz, a, g, k)
        dmax = max(dmax, abs(r.mx_nm - mx_ref), abs(r.mz_nm - mz_ref))
    return dmax


for fator, valor in FATORES.items():
    assert fator in P12.dataset.p, fator              # revise_profile recusa parâmetro ausente no .tir
    rev = ts.revise_profile(P12, {fator: valor}, reason=f"teste do fator {fator}", revision_id=f"T-{fator}")
    dif = dif_com_transcricao(rev)
    moment = MOMENTO_DO_FATOR[fator]
    mudou = max(abs(getattr(operar(rev, fz, a, g, k), f"{moment}_nm") - getattr(operar(P12, fz, a, g, k), f"{moment}_nm"))
                for fz, a, g, k in pontos_fator)
    check(f"estático /Escala-1: {fator}={valor:g} -> Mx e Mz do módulo == transcrição e {moment.upper()} muda em relação ao perfil base; tol. 1e-9",
          dif < 1e-9 and mudou > 1e-4, f"dif máx={dif:.2e}; mudança em {moment.upper()}={mudou:.4f}")
rev_todos = ts.revise_profile(P12, FATORES, reason="todos os fatores juntos", revision_id="T-TODOS")
dif = dif_com_transcricao(rev_todos)
check("estático /Escala-2: os sete fatores juntos (LMX, LVMX, LS, LTR, LKY, LMUY, LGAZ) == transcrição; tol. 1e-9",
      dif < 1e-9, f"dif máx={dif:.2e}")

# ---------------------------------------------------------------------------------------------------------
# Teto Et <= 1 (eq. 105)
# ---------------------------------------------------------------------------------------------------------
rev_et = ts.revise_profile(P12, {"QEZ1": 5.0}, reason="QEZ1 alto para ativar o teto de Et", revision_id="T-ET")
Pet = Par(rev_et.dataset.p)
dmax_teto = 0.0
dmax_sem_teto = 0.0
for fz, a, g, k in pontos_fator:
    fx, fy, info = forcas(rev_et, fz, a, g, k)
    com = sum(mz_eq100(Pet, fz, a * DEG, g * DEG, k, fx, fy, info))
    sem = sum(mz_eq100(Pet, fz, a * DEG, g * DEG, k, fx, fy, info, teto_et=False))
    mz = operar(rev_et, fz, a, g, k).mz_nm
    dmax_teto = max(dmax_teto, abs(mz - com))
    dmax_sem_teto = max(dmax_sem_teto, abs(mz - sem))
check("estático /Teto-1: com QEZ1=5 (Et > 1 sem o teto) o Mz do módulo == transcrição com min(Et, 1) e difere da sem teto",
      dmax_teto < 1e-9 and dmax_sem_teto > 1e-3, f"dif com teto={dmax_teto:.2e}; dif sem teto={dmax_sem_teto:.4f} N.m")

# ---------------------------------------------------------------------------------------------------------
# Sensibilidades de Mx: QSX2 e o quadrado do QSX6
# ---------------------------------------------------------------------------------------------------------
fz_s, g_s = 1054.0, -3.0
rev_q2 = ts.revise_profile(P12, {"QSX2": P["QSX2"] + 0.5}, reason="sensibilidade de QSX2", revision_id="T-QSX2")
dmx = operar(rev_q2, fz_s, 0.0, g_s, 0.0).mx_nm - operar(P12, fz_s, 0.0, g_s, 0.0).mx_nm
esperado_q2 = -0.5 * (g_s * DEG) * P["UNLOADED_RADIUS"] * fz_s * P["LMX"]
check("estático /Sens-1: somar 0,5 ao QSX2 muda Mx em -0,5*gamma*R0*Fz*LMX (Fy não depende do QSX2); tol. 1e-9 N.m",
      abs(dmx - esperado_q2) < 1e-9 and abs(dmx) > 1.0, f"dMx={dmx:.6f}; esperado={esperado_q2:.6f}")
rev_q6 = ts.revise_profile(P12, {"QSX4": 1.0, "QSX5": 1.0, "QSX6": 3.0, "QSX8": 0.0},
                           reason="QSX6 grande para distinguir atan(x^2) de atan(x)", revision_id="T-QSX6")
P6 = Par(rev_q6.dataset.p)
dq = 0.0
dsem = 0.0
for fz, a, g, k in pontos_fator:
    mx = operar(rev_q6, fz, a, g, k).mx_nm
    fy = forcas(rev_q6, fz, a, g, k)[1]
    dq = max(dq, abs(mx - mx_eq109(P6, fz, fy, g * DEG)))
    dsem = max(dsem, abs(mx - mx_eq109(P6, fz, fy, g * DEG, qsx6_quadrado=False)))
check("estático /Sens-2: com QSX6 grande, Mx do módulo == transcrição com atan((QSX6 Fz/F'z0)^2) e difere da variante sem o quadrado",
      dq < 1e-9 and dsem > 1e-2, f"dif com quadrado={dq:.2e}; dif sem quadrado={dsem:.4f} N.m")

# ---------------------------------------------------------------------------------------------------------
# Velocidade: Vx = 0 e conteúdo do aviso
# ---------------------------------------------------------------------------------------------------------
try:
    r_zero = operar(P12, 1054.0, 4.0, 0.0, 0.0, vx=0.0)
    check("estático /Vx-5: Vx = 0 é aceito, sem aviso de velocidade e com My finito",
          math.isfinite(r_zero.my_nm) and not any("LONGVL" in m for m in r_zero.limitations))
except ts.StaticTireError as exc:
    check("estático /Vx-5: Vx = 0 é aceito, sem aviso de velocidade e com My finito", False, f"lançou {exc}")
aviso_vx = [m for m in operar(P12, 1054.0, 4.0, 0.0, 0.0, vx=2.0 * vref).limitations if "LONGVL" in m]
check("estático /Vx-6: o aviso de Vx > LONGVL cita My, os termos QSY3/QSY4 e a razão Vx/LONGVL (2.00)",
      len(aviso_vx) == 1 and all(t in aviso_vx[0] for t in ("My", "QSY3", "QSY4", "2.00")),
      aviso_vx[0] if aviso_vx else "sem aviso")

# ---------------------------------------------------------------------------------------------------------
# Caminhos de erro
# ---------------------------------------------------------------------------------------------------------
q = P12.dataset.p


def recusa_tipo(nome, fn, tipo, trecho=""):
    try:
        fn()
        check(nome, False, "não lançou")
    except tipo as exc:
        check(nome, trecho in str(exc), str(exc))


for rotulo, kwargs, trecho in (
    ("Fz = 0", {"fz": 0.0}, "Fz deve ser > 0"),
    ("Fz < 0", {"fz": -100.0}, "Fz deve ser > 0"),
    ("Fz = NaN", {"fz": math.nan}, "finitas"),
    ("alpha = inf", {"alpha_deg": math.inf}, "finitas"),
    ("gamma = NaN", {"gam_deg": math.nan}, "finitas"),
    ("kappa = inf", {"kappa": math.inf}, "finitas"),
    ("Vx = NaN", {"vx": math.nan}, "finitas"),
):
    args = {"fz": 1054.0, "alpha_deg": 4.0, "gam_deg": 0.0, "kappa": 0.0, "vx": 10.0}
    args.update(kwargs)
    recusa_tipo(f"estático /Erro-1: evaluate_static recusa {rotulo}",
                lambda args=args: operar(P12, args["fz"], args["alpha_deg"], args["gam_deg"], args["kappa"], vx=args["vx"]),
                ts.StaticTireError, trecho)
recusa_tipo("estático /Erro-2: gamma acima de CAMMAX é recusado (TireRangeError)",
            lambda: operar(P12, 1054.0, 4.0, q["CAMMAX"] / DEG + 1.0, 0.0),
            base.TireRangeError)
recusa_tipo("estático /Erro-3: kappa acima de KPUMAX é recusado (TireRangeError)",
            lambda: operar(P12, 1054.0, 4.0, 0.0, q["KPUMAX"] + 0.1), base.TireRangeError)
recusa_tipo("estático /Erro-4: Fz acima de FZMAX é recusado (TireRangeError)",
            lambda: operar(P12, q["FZMAX"] + 100.0, 4.0, 0.0, 0.0), base.TireRangeError)

for nome, args, trecho in (
    ("sem justificativa", {"changes": {"PDY1": 1.5}, "reason": "", "revision_id": "X"}, "justificativa"),
    ("sem id", {"changes": {"PDY1": 1.5}, "reason": "motivo", "revision_id": "  "}, "revision_id"),
    ("reason não texto", {"changes": {"PDY1": 1.5}, "reason": None, "revision_id": "X"}, "justificativa"),
    ("parâmetro desconhecido", {"changes": {"XYZ99": 1.0}, "reason": "m", "revision_id": "X"}, "ausentes"),
    ("valor não finito (NaN)", {"changes": {"PDY1": math.nan}, "reason": "m", "revision_id": "X"}, "finitos"),
    ("valor não finito (inf)", {"changes": {"PDY1": math.inf}, "reason": "m", "revision_id": "X"}, "finitos"),
    ("valor não numérico", {"changes": {"PDY1": "abc"}, "reason": "m", "revision_id": "X"}, "Valor inválido"),
    ("valor booleano", {"changes": {"PDY1": True}, "reason": "m", "revision_id": "X"}, "Valor inválido"),
    ("revisão vazia", {"changes": {}, "reason": "m", "revision_id": "X"}, "ao menos um"),
    ("alterar IP", {"changes": {"IP": 1.0e5}, "reason": "m", "revision_id": "X"}, "IP/IP_NOM"),
    ("FZMIN <= 0", {"changes": {"FZMIN": 0.0}, "reason": "m", "revision_id": "X"}, "FZMIN deve permanecer positivo"),
    ("faixa invertida (ALPMIN >= ALPMAX)", {"changes": {"ALPMIN": q["ALPMAX"] + 0.1}, "reason": "m", "revision_id": "X"},
     "Faixa inválida"),
    ("LMUY <= 0", {"changes": {"LMUY": 0.0}, "reason": "m", "revision_id": "X"}, "LMUY deve permanecer positivo"),
    ("LMUY < 0", {"changes": {"LMUY": -1.0}, "reason": "m", "revision_id": "X"}, "LMUY deve permanecer positivo"),
):
    recusa_tipo(f"estático /Erro-5: revise_profile recusa {nome}",
                lambda args=args: ts.revise_profile(P12, args["changes"], reason=args["reason"], revision_id=args["revision_id"]),
                ts.StaticTireError, trecho)

with tempfile.TemporaryDirectory() as tmp:
    tmpd = Path(tmp)
    valido = tmpd / "valido.json"
    ts.save_revision(ts.revise_profile(P12, {"PDY1": P["PDY1"] * 1.05}, reason="base das variantes", revision_id="T-ERRO"), valido)
    base_json = json.loads(valido.read_text(encoding="utf-8"))

    def json_com(nome, **mudanca):
        d = tmpd / f"{nome}.json"
        d.write_text(json.dumps({**base_json, **mudanca}), encoding="utf-8")
        return d

    quebrado = tmpd / "quebrado.json"
    quebrado.write_text("{ isto não é json", encoding="utf-8")
    raiz_lista = tmpd / "lista.json"
    raiz_lista.write_text("[1, 2]", encoding="utf-8")
    for nome, arq, trecho in (
        ("JSON inválido", quebrado, "Não foi possível ler"),
        ("arquivo inexistente", tmpd / "nao_existe.json", "Não foi possível ler"),
        ("raiz que não é objeto", raiz_lista, "objeto na raiz"),
        ("schema incompatível", json_com("schema", schema="outro.v9"), "Schema"),
        ("overrides que não é objeto", json_com("ovr", overrides=[1, 2]), "overrides"),
        ("reason nulo", json_com("reason", reason=None), "reason"),
        ("revision_id nulo", json_com("rid", revision_id=None), "revision_id"),
        ("parent_revision_id numérico", json_com("pai", parent_revision_id=7), "parent_revision_id"),
        ("pressão não numérica", json_com("psi", pressure_psi="doze"), "Pressão inválida"),
        ("override com parâmetro desconhecido", json_com("desc", overrides={"XYZ99": 1.0}), "ausentes"),
    ):
        recusa_tipo(f"estático /Erro-6: load_revision recusa {nome}", lambda arq=arq: ts.load_revision(P12, arq),
                    ts.StaticTireError, trecho)

    vazio = tmpd / "sem_tir"
    vazio.mkdir()
    recusa_tipo("estático /Erro-7: load_profile_family recusa diretório sem .tir", lambda: ts.load_profile_family(vazio, source_axis_system="ISO_TYDEX"),
                ts.StaticTireError, "Nenhum perfil")

    # cópia de um .tir sem a linha de FNOMIN (o original nunca é editado)
    linhas = P12.source_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    sem_fnomin = [ln for ln in linhas if not ln.lstrip().startswith("FNOMIN")]
    check("estático /Erro-8: a cópia de teste perdeu exatamente a linha de FNOMIN", len(sem_fnomin) == len(linhas) - 1)
    copia = tmpd / P12.source_path.name
    copia.write_text("".join(sem_fnomin), encoding="utf-8")
    recusa_tipo("estático /Erro-8: load_profile recusa .tir sem parâmetro obrigatório (FNOMIN)",
                lambda: ts.load_profile(copia, source_axis_system="ISO_TYDEX"), ts.StaticTireError, "FNOMIN")

# ---------------------------------------------------------------------------------------------------------
# DDS_TTC_DIR inválido: NÃO EXECUTÁVEL (código 3), sem cair para outra pasta
# ---------------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    pasta_vazia = Path(tmp) / "vazia"
    pasta_vazia.mkdir()
    pasta_incompleta = Path(tmp) / "incompleta"
    pasta_incompleta.mkdir()
    for arq in sorted(TTC.glob("*PAC02_UM4.tir"))[:3]:                     # só três dos quatro .tir
        (pasta_incompleta / arq.name).write_bytes(arq.read_bytes())
    for nome, pasta in (("inexistente", Path(tmp) / "nao_existe"), ("sem .tir", pasta_vazia), ("com só três .tir", pasta_incompleta)):
        proc = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve())],
                              env={**os.environ, "DDS_TTC_DIR": str(pasta)}, capture_output=True, text=True,
                              encoding="utf-8", timeout=120, check=False)
        check(f"estático /Ambiente-1: DDS_TTC_DIR {nome} -> NÃO EXECUTÁVEL, código 3, mensagem e nenhuma outra pasta tentada",
              proc.returncode == 3 and "NÃO EXECUTÁVEL" in proc.stdout and "DDS_TTC_DIR" in proc.stdout
              and "PASS" not in proc.stdout, f"código={proc.returncode}; {proc.stdout.strip()[:120]}")


# ---------------------------------------------------------------------------------------------------------
def encerrar():
    print("\n--- Resumo ---")
    n = sum(1 for _, s in results if s == "PASS")
    f = len(results) - n
    print(f"{n} PASS, {f} FAIL, de {len(results)} testes")
    if f:
        raise SystemExit(1)


encerrar()
