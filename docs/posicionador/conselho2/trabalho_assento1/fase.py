"""Parte 2: o ângulo de transmissão do push rod no estático (δ) como variável livre.

mecanismo.construir fixa o push rod tangente ao círculo do rocker no estático (δ = 0: push rod ⟂ braço r1). Aqui A0 é
girado de δ em volta do eixo do rocker (n, por Pv) a partir do ponto de tangência; o resto da construção é o mesmo
(O0 na linha J→A0 a DJ, B0 = Pv + r2·Rot(n, φB)·(A0−Pv)/r1, r2 resolvido para MR(0) = alvo, C pela regra do droop).
Avaliador rápido (só cinemática: var MR, Lmin, braços, giro, ângulo do amortecedor) e Nelder-Mead.
Uso: fase.py MODO SEMENTE CAP  (MODO: d0 = δ fixo em 0; dlivre = δ livre). Saída JSON em stdout (última linha).
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import brentq, minimize
RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "python"))
import hardpoints as hp, kinematics_model as km
from posicionador import config as pc, mecanismo as mec

cfg = pc.carregar(str(RAIZ / "data/posicionador/config_T11.json"))
hs = hp.load_hardpoints(str(RAIZ / "data/posicionador/hardpoints_T11_v10.csv"),
                        str(RAIZ / "data/posicionador/hardpoints_T11_v10.meta.json"))
DROOP, BUMP = cfg.valor("curso_droop_m"), cfg.valor("curso_bump_m")
EYE, STROKE, DJ = cfg.valor("olho_a_olho_m"), cfg.valor("curso_amortecedor_m"), cfg.valor("dj_m")
BMIN, BMAX = cfg.valor("braco_min_m"), cfg.valor("braco_max_m")
GMAX, AMAX = cfg.valor("giro_max_rad"), cfg.valor("amort_ang_max_rad")
J = hs.points["FL_LCA_OUT"].xyz.astype(float)
NRAP = 31


def construir(x, mr_alvo=1.40):
    px, py, pz, az, el, r1, phib, delta = x
    Pv = np.array([px, py, pz]) / 1e3; r1 /= 1e3
    ud = mec.direcao_amortecedor(np.radians(az), np.radians(el))
    n = np.cross(Pv - J, ud)
    if np.linalg.norm(n) < 1e-9:
        return None
    n = n / np.linalg.norm(n)
    d = Pv - J; L = np.linalg.norm(d)
    if not (0 < r1 < L):
        return None
    beta = np.arcsin(r1 / L); u = d / L; perp = np.cross(n, u)
    A_t = J + np.sqrt(L * L - r1 * r1) * (np.cos(beta) * u + mec.LADO_ROCKER * np.sin(beta) * perp)
    A0 = Pv + mec._rot(n, np.radians(delta)) @ (A_t - Pv)
    lj = np.linalg.norm(A0 - J)
    if DJ >= lj:
        return None
    O0 = J + DJ * (A0 - J) / lj
    e_b = mec._rot(n, np.radians(phib)) @ ((A0 - Pv) / r1)

    def conj(r2, C=None):
        B0 = Pv + r2 * e_b
        C = B0 + EYE * ud if C is None else C
        return mec._montar_conjunto(hs, mec._pontos(Pv, n, A0, O0, B0, C)), B0

    def f(r2):
        return km.motion_ratio(km.Corner(conj(r2)[0], "FL"), 0.0)["mr_wheel_per_spring"] - mr_alvo
    try:
        a, b = 0.2 * r1, 3 * r1
        if f(a) * f(b) > 0:
            return None
        r2 = brentq(f, a, b, xtol=1e-10)
        h, B0 = conj(r2); cn = km.Corner(h, "FL")
        s0 = cn.solve(0.0); sd = cn.solve(-DROOP, q0=s0.q, phi0=s0.phi)
        w = B0 - cn.pt(sd, "ROCKER_SPRING"); pb = w @ ud
        disc = pb * pb - (w @ w - EYE * EYE)
        if disc < 0:
            return None
        t = -pb + np.sqrt(disc)
        if t <= 0:
            return None
        return mec.Construcao(conj(r2, B0 + t * ud)[0], r2, None)
    except Exception:
        return None


def medir(c, n=NRAP):
    cn = km.Corner(c.hardpoints, "FL")
    dzs = np.linspace(-DROOP, BUMP, n)
    s0 = cn.solve(0.0); sol = {}
    for g in (sorted(d for d in dzs if d >= 0), sorted((d for d in dzs if d < 0), reverse=True)):
        cur = s0
        for d in g:
            cur = cn.solve(float(d), q0=cur.q, phi0=cur.phi); sol[float(d)] = cur
    S = [sol[float(d)] for d in dzs]
    ls = np.array([cn.spring_length(s) for s in S])
    mr = np.abs(1 / np.gradient(ls, dzs, edge_order=2))
    th = np.array([s.phi for s in S])
    ang = max(np.arccos(np.clip(mec._unit(cn.pt(s, "SPRING_CHASSIS") - cn.pt(s, "ROCKER_SPRING"))[0], -1, 1)) for s in S)
    eixo = mec._unit(cn.p0["ROCKER_AXIS_B"] - cn.p0["ROCKER_AXIS_A"])
    def braco(k):
        w = cn.p0[k] - cn.p0["ROCKER_AXIS_A"]; return np.linalg.norm(w - (w @ eixo) * eixo)
    # ângulo de transmissão (desvio da perpendicular) dos dois braços, no curso
    def gam(s, ka, kb, kbraco):
        pa, pb_ = cn.pt(s, ka), cn.pt(s, kb); arm = cn.pt(s, kbraco) - cn.pt(s, "ROCKER_AXIS_A")
        arm = arm - (arm @ eixo) * eixo
        return np.degrees(np.arcsin(np.clip(mec._unit(pb_ - pa) @ mec._unit(arm), -1, 1)))
    g1 = [gam(s, "PUSH_OUT", "PUSH_IN", "PUSH_IN") for s in (S[0], S[len(S) // 2], S[-1])]
    g2 = [gam(s, "ROCKER_SPRING", "SPRING_CHASSIS", "ROCKER_SPRING") for s in (S[0], S[len(S) // 2], S[-1])]
    return dict(var=float(mr.max() / mr.min() - 1), curso_mm=float((ls.max() - ls.min()) * 1e3),
                lmin_mm=float(ls.min() * 1e3), lmax_mm=float(ls.max() * 1e3), r1=float(braco("PUSH_IN") * 1e3),
                r2=float(braco("ROCKER_SPRING") * 1e3), giro=float(np.degrees(th.max() - th.min())),
                ang=float(np.degrees(ang)), g1=g1, g2=g2)


def penal(m, cap, com_curso=True):
    p = max(0, m["var"] - cap) * 100 / 0.1          # 0,1 pp de var = 1
    if com_curso:
        p += max(0, (EYE - STROKE) * 1e3 - m["lmin_mm"]) / 0.1   # 0,1 mm = 1
    p += max(0, m["lmax_mm"] - EYE * 1e3 - 1e-6) / 0.1
    for r in (m["r1"], m["r2"]):
        p += max(0, BMIN * 1e3 - r, r - BMAX * 1e3)            # 1 mm = 1
    p += max(0, m["giro"] - np.degrees(GMAX)) + max(0, m["ang"] - np.degrees(AMAX))   # 1° = 1
    return p


def rodar(modo, semente, cap, objetivo, maxfev):
    res = json.load(open(RAIZ / "docs/posicionador/benchmark/resultados.json"))
    b = [b for b in res["buscas"] if b["ferramenta"] == "posicionador"][semente]
    x0 = np.array(b["x"][:7] + [0.0])
    livre = modo == "dlivre"
    def f(z):
        x = np.concatenate([z, [0.0]]) if not livre else z
        c = construir(x)
        if c is None:
            return 1e6
        try:
            m = medir(c)
        except Exception:
            return 1e6
        if objetivo == "viavel":     # chegar a tudo cumprido, com folga pequena de margem na meta
            return penal(m, cap) - 0.01 * max(0, min(50, (m["lmin_mm"] - 149) / 0.1))
        return m["curso_mm"] + 10 * penal(m, cap, com_curso=False)     # Pareto: curso usado mínimo dado var ≤ cap
    z0 = x0 if livre else x0[:7]
    passo = np.array([10, 10, 10, 3, 3, 3, 5] + ([5] if livre else []))
    simplex = np.vstack([z0] + [z0 + np.eye(len(z0))[i] * passo[i] for i in range(len(z0))])
    r = minimize(f, z0, method="Nelder-Mead", options=dict(maxfev=maxfev, initial_simplex=simplex, xatol=1e-3, fatol=1e-5))
    x = np.concatenate([r.x, [0.0]]) if not livre else r.x
    m = medir(construir(x), n=201)
    return dict(modo=modo, semente=semente, cap=cap, objetivo=objetivo, x=[float(v) for v in x], nfev=int(r.nfev),
                **m, penal=penal(m, cap))


if __name__ == "__main__":
    modo, sem, cap, obj = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    mf = int(sys.argv[5]) if len(sys.argv) > 5 else 400
    print(json.dumps(rodar(modo, sem, cap, obj, mf)))
