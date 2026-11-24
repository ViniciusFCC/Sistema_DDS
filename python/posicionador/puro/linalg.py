"""Álgebra linear mínima em Python puro: vetores 3D (tuplas), matrizes 3x3 e solução de sistema pequeno."""
import math


class ErroLinear(ArithmeticError):
    """Sistema singular ou vetor nulo."""


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def unit(a, tol=1e-14):
    n = norm(a)
    if n < tol:
        raise ErroLinear("vetor de comprimento nulo")
    return (a[0] / n, a[1] / n, a[2] / n)


def vec(a):
    """Qualquer sequência de 3 números → tupla de floats."""
    return (float(a[0]), float(a[1]), float(a[2]))


I3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def matvec(M, v):
    return (dot(M[0], v), dot(M[1], v), dot(M[2], v))


def matmul(A, B):
    cols = [(B[0][j], B[1][j], B[2][j]) for j in range(3)]
    return tuple(tuple(dot(A[i], cols[j]) for j in range(3)) for i in range(3))


def skew(v):
    return ((0.0, -v[2], v[1]), (v[2], 0.0, -v[0]), (-v[1], v[0], 0.0))


def _mat_comb(a, A, b, B):
    return tuple(tuple(a * A[i][j] + b * B[i][j] for j in range(3)) for i in range(3))


def rot_vec(w):
    """Rodrigues: matriz de rotação do vetor de rotação w (regra da mão direita), com a série de 2ª ordem se |w| < 1e-12."""
    th = norm(w)
    K = skew(w)
    K2 = matmul(K, K)
    if th < 1e-12:
        return _mat_comb(1.0, _mat_comb(1.0, I3, 1.0, K), 0.5, K2)
    return _mat_comb(1.0, _mat_comb(1.0, I3, math.sin(th) / th, K), (1.0 - math.cos(th)) / th ** 2, K2)


def rot_eixo(eixo, ang):
    """Rotação de `ang` em volta de `eixo` (não precisa ser unitário; mesma convenção de rot_vec)."""
    return rot_vec(mul(unit(eixo), ang))


def resolver(A, b):
    """Resolve A x = b (A n×n, listas de listas) por eliminação de Gauss com pivô parcial. ErroLinear se singular."""
    n = len(b)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(M[i][c]))
        if abs(M[p][c]) < 1e-300:
            raise ErroLinear("matriz singular")
        M[c], M[p] = M[p], M[c]
        for i in range(c + 1, n):
            f = M[i][c] / M[c][c]
            if f:
                for j in range(c, n + 1):
                    M[i][j] -= f * M[c][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / M[i][i]
    return x


def inversa(A):
    n = len(A)
    cols = []
    for j in range(n):
        e = [1.0 if i == j else 0.0 for i in range(n)]
        cols.append(resolver(A, e))
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def _norma1(A):
    n = len(A)
    return max(sum(abs(A[i][j]) for i in range(n)) for j in range(n))


def cond1(A):
    """Número de condição na norma 1 (‖A‖₁·‖A⁻¹‖₁). Infinito se singular. Difere da norma 2 (SVD) do numpy por um fator
    de no máximo n; só serve ao teste de degeneração, cujo limite (1e10) está muito longe dos casos normais."""
    try:
        return _norma1(A) * _norma1(inversa(A))
    except ErroLinear:
        return math.inf
