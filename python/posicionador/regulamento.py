"""
Regulamento no posicionador (EDR-076): gabarito de ocupação do piloto (FSAE Rules 2027 V1.0, T.1.2) e limite da AIP (F.8.6.1).

Eixos ISO 8855 (X frente, Y esquerda, Z cima), SI. O plano do gabarito é perpendicular a X.
Resumo da regra e leitura da figura: docs/posicionador/pesquisa/relatorio-regras.md §2.
"""
from collections import deque
from dataclasses import dataclass, field

import numpy as np

LADO_M = 0.350      # T.1.2: octógono de 350 x 350 mm
CHANFRO_M = 0.050   # T.1.2: chanfro de 50 x 50 mm nos quatro cantos
RES_AMOSTRA_M = 0.005   # espaçamento das amostras do contorno e do interior (resolução relevante dos obstáculos)


@dataclass
class ResultadoGabarito:
    livre: "bool | None"
    motivo: str
    caminho_z: list = field(default_factory=list)


def gabarito_t12():
    """Octógono do gabarito T.1.2 em (Y, Z relativo à base), em m, sentido anti-horário, shape (8, 2).

    0,350 x 0,350 m com chanfro de 0,050 x 0,050 m nos 4 cantos (FSAE Rules 2027 V1.0, T.1.2).
    Os entalhes e a faixa central de 50 mm da figura são IGNORADOS: o octógono cheio é conservador (ocupa mais que o
    gabarito real), conforme a leitura da figura em relatorio-regras.md §2. Y é centrado em 0 (o centro é y_centro na trajetória).
    """
    h, c = LADO_M / 2, CHANFRO_M
    return np.array([
        [-h + c, 0.0], [h - c, 0.0], [h, c], [h, LADO_M - c],
        [h - c, LADO_M], [-h + c, LADO_M], [-h, LADO_M - c], [-h, c],
    ])


def _amostras_gabarito(res=RES_AMOSTRA_M):
    """Pontos (Y, Z) do contorno e do interior do gabarito, espaçamento <= res."""
    g = gabarito_t12()
    pts = []
    for i in range(len(g)):
        a, b = g[i], g[(i + 1) % len(g)]
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / res)))
        t = np.linspace(0.0, 1.0, n + 1)[:-1, None]
        pts.append(a + t * (b - a))
    ny = int(np.ceil(LADO_M / res))
    ys = np.linspace(-LADO_M / 2, LADO_M / 2, ny + 1)
    zs = np.linspace(0.0, LADO_M, ny + 1)
    Y, Z = np.meshgrid(ys, zs)
    G = np.column_stack([Y.ravel(), Z.ravel()])
    dentro = np.ones(len(G), bool)   # polígono convexo anti-horário: produto vetorial >= 0 em todas as arestas
    for i in range(len(g)):
        a, b = g[i], g[(i + 1) % len(g)]
        dentro &= (b[0] - a[0]) * (G[:, 1] - a[1]) - (b[1] - a[1]) * (G[:, 0] - a[0]) >= -1e-12
    pts.append(G[dentro])
    return np.vstack(pts)


def _coluna_livre(obstaculos, x, zs, y_centro, amostras):
    """Para cada z de zs, True se o gabarito (base em z, plano X = x) não toca nenhum obstáculo (sdf > 0 em toda amostra)."""
    n = len(amostras)
    livre = np.ones(len(zs), bool)
    for k0 in range(0, len(zs), 64):   # blocos para limitar a memória
        zb = zs[k0:k0 + 64]
        P = np.empty((len(zb), n, 3))
        P[:, :, 0] = x
        P[:, :, 1] = y_centro + amostras[None, :, 0]
        P[:, :, 2] = zb[:, None] + amostras[None, :, 1]
        P = P.reshape(-1, 3)
        ocupado = np.zeros(len(P), bool)
        for ob in obstaculos:
            ocupado |= np.asarray(ob.sdf(P)) <= 0.0
        livre[k0:k0 + 64] = ~ocupado.reshape(len(zb), n).any(axis=1)
    return livre


def trajetoria_t12(obstaculos, x_ini, x_fim, z_min, z_max, passo_x=0.01, passo_z=0.005, y_centro=0.0):
    """Há altura livre para o gabarito T.1.2 do x_ini ao x_fim (T.1.2.2b e c)?

    Grade (x, z): a célula é livre se o gabarito, com a base em z e no plano X = x, não intercepta nenhum obstáculo
    (sdf <= 0 em alguma amostra do contorno ou do interior). Existe trajetória se há caminho 4-conexo de células livres da
    coluna x_ini à coluna x_fim; subir ou descer em z numa coluna é passar por células livres dela (T.1.2.2c: o gabarito
    pode ser movido na vertical). `caminho_z` traz um z por coluna x, o primeiro em que o caminho entra na coluna.
    `x_ini` ou `x_fim` None (posição da coluna de direção/pedal a confirmar) -> livre None, NÃO VERIFICÁVEL.
    """
    if x_ini is None or x_fim is None:
        return ResultadoGabarito(None, "NÃO VERIFICÁVEL: posição da coluna/pedal a confirmar", [])
    nx = int(round(abs(x_fim - x_ini) / passo_x)) + 1
    nz = int(round((z_max - z_min) / passo_z)) + 1
    xs = np.linspace(x_ini, x_fim, nx)
    zs = np.linspace(z_min, z_max, max(nz, 1))
    am = _amostras_gabarito()
    livre = np.array([_coluna_livre(obstaculos, x, zs, y_centro, am) for x in xs])   # (nx, nz)
    pai = {}
    fila = deque()
    for j in np.flatnonzero(livre[0]):
        pai[(0, int(j))] = None
        fila.append((0, int(j)))
    fim = None
    while fila:
        i, j = fila.popleft()
        if i == nx - 1:
            fim = (i, j)
            break
        for ii, jj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= ii < nx and 0 <= jj < len(zs) and livre[ii, jj] and (ii, jj) not in pai:
                pai[(ii, jj)] = (i, j)
                fila.append((ii, jj))
    if fim is None:
        return ResultadoGabarito(False, "sem altura livre: nenhum caminho de células livres de x_ini a x_fim", [])
    caminho = []
    c = fim
    while c is not None:
        caminho.append(c)
        c = pai[c]
    caminho.reverse()
    primeiro = {}
    for i, j in caminho:
        primeiro.setdefault(i, float(zs[j]))
    return ResultadoGabarito(True, "há altura livre", [primeiro[i] for i in sorted(primeiro)])


def limite_aip(x_face_traseira_aip):
    """Limite da AIP (F.8.6.1: nada da suspensão/direção à frente da face traseira da AIP).

    Devolve f(p) -> folga em X = x_face - p_x (m), p de shape (3,) ou (N,3); positivo = atrás da face = permitido.
    `x_face_traseira_aip` None (posição a confirmar) -> devolve None: NÃO VERIFICÁVEL (a verificação fica desligada).
    """
    if x_face_traseira_aip is None:
        return None

    def folga(p):
        p = np.asarray(p, dtype=float)
        return x_face_traseira_aip - p[..., 0]

    return folga
