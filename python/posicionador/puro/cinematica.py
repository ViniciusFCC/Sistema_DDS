"""
Cinemática de um canto de double wishbone em Python puro (porte de `kinematics_model.Corner`, só o que o posicionador usa:
`resolver` (= solve), `ponto` (= pt), `comprimento_mola` e `razao_de_movimento`). ISO 8855 (X frente, Y esquerda, Z cima), SI.

Entrada: `pontos` = {chave: (xyz, componente)} do canto, chaves sem o prefixo do canto (`LCA_OUT`, `ROCKER_SPRING`...).
Diferenças deliberadas em relação ao original (numpy):
- sem a validação do schema de hardpoints (quem lê o CSV valida);
- o teste de jacobiano mal condicionado usa a norma 1 (`linalg.cond1`), não a norma 2 por SVD.
"""
import math
from dataclasses import dataclass

from posicionador.puro import linalg as la

_I6 = range(6)


class ErroCinematica(RuntimeError):
    """Falha numérica ou geométrica do solver (equivale a kinematics_model.KinematicsError)."""


def _unit(v):
    try:
        return la.unit(v)
    except la.ErroLinear:
        raise ErroCinematica("vetor de comprimento nulo")


@dataclass
class Solucao:
    q: list            # [wx, wy, wz, tx, ty, tz] da manga
    curso: float       # Z do centro da roda [m]
    cremalheira: float
    phi: float = 0.0   # ângulo do rocker [rad]


class Canto:
    def __init__(self, pontos, lado=+1, dir_cremalheira=(0.0, 1.0, 0.0)):
        obrig = ("LCA_OUT", "LCA_IN_F", "LCA_IN_R", "UCA_OUT", "UCA_IN_F", "UCA_IN_R", "TIE_OUT", "TIE_IN",
                 "WHEEL_CENTER", "SPINDLE_PT")
        faltam = [k for k in obrig if k not in pontos]
        if faltam:
            raise ErroCinematica(f"pontos ausentes: {faltam}")
        self.side = lado
        self.p0 = {k: la.vec(v[0]) for k, v in pontos.items()}
        self.comp = {k: v[1] for k, v in pontos.items()}
        self.rack_dir = _unit(dir_cremalheira)
        self.c0 = self.p0["WHEEL_CENTER"]
        d = lambda a, b: la.norm(la.sub(self.p0[a], self.p0[b]))
        self.L = {"LF": d("LCA_OUT", "LCA_IN_F"), "LR": d("LCA_OUT", "LCA_IN_R"),
                  "UF": d("UCA_OUT", "UCA_IN_F"), "UR": d("UCA_OUT", "UCA_IN_R"), "T": d("TIE_OUT", "TIE_IN")}
        self.has_push = "PUSH_OUT" in self.p0
        if self.has_push:
            self.Lpush = d("PUSH_OUT", "PUSH_IN")
        a = _unit(la.sub(self.p0["SPINDLE_PT"], self.c0))
        if self.side * a[1] <= 0:
            raise ErroCinematica("SPINDLE_PT deve estar para fora do centro da roda")

    def _ponto_manga(self, q, P0):
        R = la.rot_vec(q[:3])
        return la.add(la.add(self.c0, la.matvec(R, la.sub(P0, self.c0))), (q[3], q[4], q[5]))

    def _res(self, q, curso, cremalheira):
        p0, L = self.p0, self.L
        R = la.rot_vec(q[:3])
        t = (q[3], q[4], q[5])

        def pm(P0):
            return la.add(la.add(self.c0, la.matvec(R, la.sub(P0, self.c0))), t)

        PL, PU, PT, WC = pm(p0["LCA_OUT"]), pm(p0["UCA_OUT"]), pm(p0["TIE_OUT"]), pm(p0["WHEEL_CENTER"])
        Tin = la.add(p0["TIE_IN"], la.mul(self.rack_dir, cremalheira))

        def dist_res(P, A, l0):
            d = la.sub(P, A)
            return (la.dot(d, d) - l0 * l0) / (2.0 * l0)

        return [dist_res(PL, p0["LCA_IN_F"], L["LF"]), dist_res(PL, p0["LCA_IN_R"], L["LR"]),
                dist_res(PU, p0["UCA_IN_F"], L["UF"]), dist_res(PU, p0["UCA_IN_R"], L["UR"]),
                dist_res(PT, Tin, L["T"]),
                WC[2] - self.c0[2] - curso]

    @staticmethod
    def _n2(r):
        return math.sqrt(sum(x * x for x in r))

    def resolver(self, curso=0.0, cremalheira=0.0, q0=None, phi0=0.0, tol=1e-12, maxit=80):
        """Pose da manga para o curso e a cremalheira dados (equivale a Corner.solve)."""
        q = [0.0] * 6 if q0 is None else [float(x) for x in q0]
        eps = 1e-7
        for _ in range(maxit):
            r = self._res(q, curso, cremalheira)
            n0 = self._n2(r)
            if n0 < tol:
                break
            J = [[0.0] * 6 for _ in _I6]
            for j in _I6:
                qp, qm = list(q), list(q)
                qp[j] += eps
                qm[j] -= eps
                rp, rm = self._res(qp, curso, cremalheira), self._res(qm, curso, cremalheira)
                for i in _I6:
                    J[i][j] = (rp[i] - rm[i]) / (2 * eps)
            if la.cond1(J) > 1e10:
                raise ErroCinematica("jacobiano singular/mal condicionado: configuração degenerada ou curso fora do alcance")
            try:
                dq = la.resolver(J, [-x for x in r])
            except la.ErroLinear:
                raise ErroCinematica("jacobiano singular")
            a, qn = 1.0, q
            while a > 1e-4:
                qn = [q[i] + a * dq[i] for i in _I6]
                if self._n2(self._res(qn, curso, cremalheira)) < n0:
                    break
                a *= 0.5
            q = qn
        if self._n2(self._res(q, curso, cremalheira)) > 1e-10:
            raise ErroCinematica(f"Newton não convergiu para curso={curso * 1e3:.2f} mm, "
                                 f"cremalheira={cremalheira * 1e3:.2f} mm (fora do alcance cinemático ou geometria inconsistente)")
        sol = Solucao(q=q, curso=float(curso), cremalheira=float(cremalheira))
        if self.has_push:
            sol.phi = self._resolver_rocker(sol, phi0)
        return sol

    def _angulo_bandeja(self, sol, qual):
        A = self.p0[f"{qual}_IN_F"]
        u = _unit(la.sub(self.p0[f"{qual}_IN_R"], A))
        v0 = la.sub(self.p0[f"{qual}_OUT"], A)
        v = la.sub(self._ponto_manga(sol.q, self.p0[f"{qual}_OUT"]), A)
        v0p = la.sub(v0, la.mul(u, la.dot(v0, u)))
        vp = la.sub(v, la.mul(u, la.dot(v, u)))
        return math.atan2(la.dot(u, la.cross(v0p, vp)), la.dot(v0p, vp))

    def _ponto_rocker(self, chave, phi):
        A = self.p0["ROCKER_AXIS_A"]
        u = _unit(la.sub(self.p0["ROCKER_AXIS_B"], A))
        return la.add(A, la.matvec(la.rot_eixo(u, phi), la.sub(self.p0[chave], A)))

    def _push_out(self, sol):
        comp = self.comp["PUSH_OUT"]
        if comp == "UPRIGHT":
            return self._ponto_manga(sol.q, self.p0["PUSH_OUT"])
        A = self.p0[f"{comp}_IN_F"]
        u = _unit(la.sub(self.p0[f"{comp}_IN_R"], A))
        return la.add(A, la.matvec(la.rot_eixo(u, self._angulo_bandeja(sol, comp)), la.sub(self.p0["PUSH_OUT"], A)))

    def _resolver_rocker(self, sol, phi0):
        po = self._push_out(sol)
        f = lambda ph: la.norm(la.sub(self._ponto_rocker("PUSH_IN", ph), po)) - self.Lpush
        phi, h = float(phi0), 1e-7
        for _ in range(80):
            fv = f(phi)
            if abs(fv) < 1e-13:
                return phi
            d = (f(phi + h) - f(phi - h)) / (2 * h)
            if abs(d) < 1e-12:
                raise ErroCinematica("rocker singular (pushrod alinhado com o braço do rocker)")
            step = -fv / d
            while abs(step) > 0.5:
                step *= 0.5
            phi += step
        if abs(f(phi)) > 1e-10:
            raise ErroCinematica("rocker não convergiu (pushrod incompatível com o curso)")
        return phi

    def ponto(self, sol, chave):
        comp, P0 = self.comp[chave], self.p0[chave]
        if comp in ("UPRIGHT", "WHEEL"):
            return self._ponto_manga(sol.q, P0)
        if comp == "CHASSIS":
            return P0
        if comp == "RACK":
            return la.add(P0, la.mul(self.rack_dir, sol.cremalheira))
        if comp in ("LCA", "UCA"):
            A = self.p0[f"{comp}_IN_F"]
            u = _unit(la.sub(self.p0[f"{comp}_IN_R"], A))
            return la.add(A, la.matvec(la.rot_eixo(u, self._angulo_bandeja(sol, comp)), la.sub(P0, A)))
        if comp == "ROCKER":
            return self._ponto_rocker(chave, sol.phi)
        raise ErroCinematica(f"componente {comp} não tratado")

    def comprimento_mola(self, sol):
        if not self.has_push:
            raise ErroCinematica("canto sem grupo pushrod/rocker/mola")
        return la.norm(la.sub(self.ponto(sol, "ROCKER_SPRING"), self.ponto(sol, "SPRING_CHASSIS")))


def razao_de_movimento(canto, curso=0.0, dz=1e-5):
    """MR [wheel/spring] = |d(curso da roda)/d(comprimento da mola)| (equivale a km.motion_ratio)."""
    s0 = canto.resolver(curso)
    sp = canto.resolver(curso + dz, q0=s0.q, phi0=s0.phi)
    sm = canto.resolver(curso - dz, q0=s0.q, phi0=s0.phi)
    dL = (canto.comprimento_mola(sp) - canto.comprimento_mola(sm)) / (2 * dz)
    if abs(dL) < 1e-12:
        raise ErroCinematica("mola sem variação de comprimento (MR infinito)")
    return {"mr_wheel_per_spring": abs(1.0 / dL), "dLspring_dz": dL, "spring_length_m": canto.comprimento_mola(s0)}
