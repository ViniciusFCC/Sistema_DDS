"""
Geometria por distância com sinal (SDF) do posicionador (EDR-076, TC-POS-010 a 014).
Tubos viram cápsulas; tubos quadrados e outros sólidos viram caixas orientadas; o aro de 13" vira um barril oco.
Todas as SDFs são em metros, negativas dentro e 1-Lipschitz. Eixos ISO 8855. Numpy puro.
"""
from dataclasses import dataclass

import numpy as np


def _arr(x):
    return np.asarray(x, dtype=float)


@dataclass
class Esfera:
    c: np.ndarray
    r: float

    def sdf(self, p):
        return np.linalg.norm(_arr(p) - self.c, axis=1) - self.r

    def transformada(self, R, t):
        return Esfera(_arr(R) @ self.c + _arr(t), self.r)


@dataclass
class Capsula:
    a: np.ndarray
    b: np.ndarray
    r: float

    def sdf(self, p):
        p = _arr(p)
        ab = self.b - self.a
        den = float(ab @ ab)
        h = np.zeros(len(p)) if den == 0 else np.clip((p - self.a) @ ab / den, 0.0, 1.0)
        return np.linalg.norm(p - (self.a + h[:, None] * ab), axis=1) - self.r

    def transformada(self, R, t):
        R, t = _arr(R), _arr(t)
        return Capsula(R @ self.a + t, R @ self.b + t, self.r)


@dataclass
class Caixa:
    """Caixa orientada: `eixos` tem os eixos unitários nas linhas; `meias` são as meias-dimensões."""
    centro: np.ndarray
    eixos: np.ndarray
    meias: np.ndarray

    def sdf(self, p):
        q = np.abs((_arr(p) - self.centro) @ self.eixos.T) - self.meias
        fora = np.linalg.norm(np.maximum(q, 0.0), axis=1)
        return fora + np.minimum(q.max(axis=1), 0.0)

    def transformada(self, R, t):
        R, t = _arr(R), _arr(t)
        return Caixa(R @ self.centro + t, self.eixos @ R.T, self.meias)


@dataclass
class Barril:
    """Aro oco: região sólida = {raio >= r_int, |axial| <= meia_largura}; o miolo (raio < r_int) é livre."""
    centro: np.ndarray
    eixo_unit: np.ndarray
    r_int: float
    meia_largura: float

    def sdf(self, p):
        d = _arr(p) - self.centro
        a = d @ self.eixo_unit
        rho = np.linalg.norm(d - a[:, None] * self.eixo_unit, axis=1)
        da, dr = np.abs(a) - self.meia_largura, self.r_int - rho   # >0 fora da faixa axial / dentro do miolo
        fora = np.hypot(np.maximum(da, 0.0), np.maximum(dr, 0.0))
        return np.where((da > 0) | (dr > 0), fora, np.maximum(da, dr))

    def transformada(self, R, t):
        R, t = _arr(R), _arr(t)
        return Barril(R @ self.centro + t, R @ self.eixo_unit, self.r_int, self.meia_largura)


def folga_segmento(prim, a, b, raio, passo=0.002):
    """Folga (m) entre o segmento [a, b] engrossado por `raio` e o primitivo: mínimo da SDF em pontos espaçados
    de no máximo `passo`, menos `raio`, menos `passo/2` (conservador pela 1-Lipschitz). Aceita a == b."""
    a, b = _arr(a), _arr(b)
    n = max(int(np.ceil(np.linalg.norm(b - a) / passo)), 1)
    pts = a + np.linspace(0.0, 1.0, n + 1)[:, None] * (b - a)
    return float(prim.sdf(pts).min() - raio - passo / 2)


def dist_seg_seg(p1, q1, p2, q2):
    """Distância exata entre os segmentos [p1, q1] e [p2, q2] (forma fechada, Ericson 5.1.9)."""
    p1, q1, p2, q2 = map(_arr, (p1, q1, p2, q2))
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    eps = 1e-14
    if a <= eps and e <= eps:
        s = t = 0.0
    elif a <= eps:
        s, t = 0.0, np.clip(f / e, 0, 1)
    else:
        c = d1 @ r
        if e <= eps:
            s, t = np.clip(-c / a, 0, 1), 0.0
        else:
            bb = d1 @ d2
            den = a * e - bb * bb
            s = np.clip((bb * f - c * e) / den, 0, 1) if den > eps * a * e else 0.0
            t = (bb * s + f) / e
            if t < 0:
                t, s = 0.0, np.clip(-c / a, 0, 1)
            elif t > 1:
                t, s = 1.0, np.clip((bb - c) / a, 0, 1)
    return float(np.linalg.norm((p1 + s * d1) - (p2 + t * d2)))
