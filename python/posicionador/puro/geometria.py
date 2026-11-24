"""
Geometria por distância com sinal (SDF) em Python puro: porte de `posicionador.geometria`, mas por ponto (um ponto = tupla
de 3 floats; sem vetorização). Cápsula, esfera, caixa orientada e barril do aro. Metros, ISO 8855. Negativa dentro.
"""
import math
from dataclasses import dataclass

from posicionador.puro import linalg as la


def linspace(a, b, n):
    """n pontos de a a b com as pontas exatas (como numpy.linspace com endpoint)."""
    if n == 1:
        return [float(a)]
    passo = (b - a) / (n - 1)
    return [a + i * passo for i in range(n - 1)] + [float(b)]


@dataclass
class Esfera:
    c: tuple
    r: float

    def sdf(self, p):
        return la.norm(la.sub(p, self.c)) - self.r

    def caixa_envolvente(self):
        return la.sub(self.c, (self.r,) * 3), la.add(self.c, (self.r,) * 3)


@dataclass
class Capsula:
    a: tuple
    b: tuple
    r: float

    def sdf(self, p):
        ab = la.sub(self.b, self.a)
        den = la.dot(ab, ab)
        h = 0.0 if den == 0 else min(max(la.dot(la.sub(p, self.a), ab) / den, 0.0), 1.0)
        return la.norm(la.sub(p, la.add(self.a, la.mul(ab, h)))) - self.r

    def caixa_envolvente(self):
        lo = tuple(min(x, y) - self.r for x, y in zip(self.a, self.b))
        hi = tuple(max(x, y) + self.r for x, y in zip(self.a, self.b))
        return lo, hi


@dataclass
class Caixa:
    """Caixa orientada: `eixos` = 3 eixos unitários (tuplas); `meias` = meias-dimensões."""
    centro: tuple
    eixos: tuple
    meias: tuple

    def sdf(self, p):
        d = la.sub(p, self.centro)
        q = [abs(la.dot(d, self.eixos[i])) - self.meias[i] for i in range(3)]
        fora = math.sqrt(sum(max(x, 0.0) ** 2 for x in q))
        return fora + min(max(q), 0.0)

    def caixa_envolvente(self):
        ext = tuple(sum(abs(self.eixos[i][k]) * self.meias[i] for i in range(3)) for k in range(3))
        return la.sub(self.centro, ext), la.add(self.centro, ext)


@dataclass
class Barril:
    """Aro oco: região sólida = {raio >= r_int, |axial| <= meia_largura}; o miolo (raio < r_int) é livre."""
    centro: tuple
    eixo_unit: tuple
    r_int: float
    meia_largura: float

    def sdf(self, p):
        d = la.sub(p, self.centro)
        a = la.dot(d, self.eixo_unit)
        rho = la.norm(la.sub(d, la.mul(self.eixo_unit, a)))
        da, dr = abs(a) - self.meia_largura, self.r_int - rho
        if da > 0 or dr > 0:
            return math.hypot(max(da, 0.0), max(dr, 0.0))
        return max(da, dr)


def folga_segmento(prim, a, b, raio, passo=0.002):
    """Folga (m) entre o segmento [a, b] engrossado por `raio` e o primitivo: mínimo da SDF em pontos espaçados de no máximo
    `passo`, menos `raio`, menos `passo/2` (conservador pela 1-Lipschitz). Aceita a == b."""
    n = max(int(math.ceil(la.norm(la.sub(b, a)) / passo)), 1)
    ab = la.sub(b, a)
    m = min(prim.sdf(la.add(a, la.mul(ab, i / n))) for i in range(n + 1))
    return m - raio - passo / 2


def dist_seg_seg(p1, q1, p2, q2):
    """Distância exata entre os segmentos [p1, q1] e [p2, q2] (forma fechada, Ericson 5.1.9)."""
    d1, d2, r = la.sub(q1, p1), la.sub(q2, p2), la.sub(p1, p2)
    a, e, f = la.dot(d1, d1), la.dot(d2, d2), la.dot(d2, r)
    eps = 1e-14
    clip = lambda x: min(max(x, 0.0), 1.0)  # noqa: E731
    if a <= eps and e <= eps:
        s = t = 0.0
    elif a <= eps:
        s, t = 0.0, clip(f / e)
    else:
        c = la.dot(d1, r)
        if e <= eps:
            s, t = clip(-c / a), 0.0
        else:
            bb = la.dot(d1, d2)
            den = a * e - bb * bb
            s = clip((bb * f - c * e) / den) if den > eps * a * e else 0.0
            t = (bb * s + f) / e
            if t < 0:
                t, s = 0.0, clip(-c / a)
            elif t > 1:
                t, s = 1.0, clip((bb - c) / a)
    return la.norm(la.sub(la.add(p1, la.mul(d1, s)), la.add(p2, la.mul(d2, t))))
