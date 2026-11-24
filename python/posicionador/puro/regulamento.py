"""
Regulamento em Python puro: porte de `posicionador.regulamento` (gabarito T.1.2, AIP F.8.6.1; regras lá).
Diferença de método, mesmo resultado: a ocupação da grade (x, z) é calculada por obstáculo, só nas células e amostras que
caem na caixa envolvente do obstáculo inflada por `tol` (fora dela a sdf > tol, então a célula não é ocupada por ele), e
pode ser guardada (`ocupacao`) para reaproveitar a parte fixa da cena entre candidatos.
"""
import bisect
import math
from collections import deque
from dataclasses import dataclass, field

from posicionador.puro.geometria import linspace

LADO_M = 0.350
CHANFRO_M = 0.050
RES_AMOSTRA_M = 0.005


@dataclass
class ResultadoGabarito:
    livre: "bool | None"
    motivo: str
    caminho_z: list = field(default_factory=list)


def gabarito_t12():
    """Octógono (Y, Z relativo à base), anti-horário, 8 vértices (ver posicionador.regulamento.gabarito_t12)."""
    h, c = LADO_M / 2, CHANFRO_M
    return [(-h + c, 0.0), (h - c, 0.0), (h, c), (h, LADO_M - c), (h - c, LADO_M), (-h + c, LADO_M), (-h, LADO_M - c), (-h, c)]


def amostras_gabarito(res=RES_AMOSTRA_M):
    """Pontos (Y, Z) do contorno e do interior do gabarito, ordenados por Z (e depois Y)."""
    g = gabarito_t12()
    pts = []
    for i in range(len(g)):
        a, b = g[i], g[(i + 1) % len(g)]
        n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / res)))
        for k in range(n):
            t = k / n
            pts.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    ny = int(math.ceil(LADO_M / res))
    ys = linspace(-LADO_M / 2, LADO_M / 2, ny + 1)
    zs = linspace(0.0, LADO_M, ny + 1)
    for z in zs:
        for y in ys:
            if all((g[(i + 1) % len(g)][0] - g[i][0]) * (z - g[i][1]) - (g[(i + 1) % len(g)][1] - g[i][1]) * (y - g[i][0]) >= -1e-12
                   for i in range(len(g))):
                pts.append((y, z))
    pts.sort(key=lambda s: (s[1], s[0]))
    return pts


def tolerancia(passo_x):
    return math.hypot(RES_AMOSTRA_M * math.sqrt(2) / 2, passo_x / 2)


def grade(x_ini, x_fim, z_min, z_max, passo_x=0.01, passo_z=0.005):
    nx = int(round(abs(x_fim - x_ini) / passo_x)) + 1
    nz = int(round((z_max - z_min) / passo_z)) + 1
    return linspace(x_ini, x_fim, nx), linspace(z_min, z_max, max(nz, 1))


def ocupacao(obstaculos, xs, zs, y_centro, amostras, tol):
    """occ[i] = bytearray(nz): 1 se o gabarito (base em z, plano X = x_i) tem alguma amostra com sdf <= tol."""
    occ = [bytearray(len(zs)) for _ in xs]
    sz = [s[1] for s in amostras]
    for ob in obstaculos:
        cx = ob.caixa_envolvente() if hasattr(ob, "caixa_envolvente") else None
        for i, x in enumerate(xs):
            if cx is not None and not (cx[0][0] - tol <= x <= cx[1][0] + tol):
                continue
            for j, z in enumerate(zs):
                if occ[i][j]:
                    continue
                if cx is None:
                    cand = amostras
                else:   # só as amostras cuja posição no mundo cai na caixa inflada do obstáculo
                    k0 = bisect.bisect_left(sz, cx[0][2] - tol - z)
                    k1 = bisect.bisect_right(sz, cx[1][2] + tol - z)
                    if k0 >= k1:
                        continue
                    cand = amostras[k0:k1]
                for ys, zz in cand:
                    y = y_centro + ys
                    if cx is not None and not (cx[0][1] - tol <= y <= cx[1][1] + tol):
                        continue
                    if ob.sdf((x, y, z + zz)) <= tol:
                        occ[i][j] = 1
                        break
    return occ


def uniao(a, b):
    return [bytearray(x | y for x, y in zip(ra, rb)) for ra, rb in zip(a, b)]


def caminho_livre(occ, zs):
    """BFS 4-conexa de células livres da coluna 0 à última. Devolve ResultadoGabarito."""
    nx, nz = len(occ), len(zs)
    pai = {}
    fila = deque()
    for j in range(nz):
        if not occ[0][j]:
            pai[(0, j)] = None
            fila.append((0, j))
    fim = None
    while fila:
        i, j = fila.popleft()
        if i == nx - 1:
            fim = (i, j)
            break
        for ii, jj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= ii < nx and 0 <= jj < nz and not occ[ii][jj] and (ii, jj) not in pai:
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


def trajetoria_t12(obstaculos, x_ini, x_fim, z_min, z_max, passo_x=0.01, passo_z=0.005, y_centro=0.0, ocupacao_base=None):
    """Há altura livre para o gabarito T.1.2 do x_ini ao x_fim? (ver o original). `ocupacao_base`: ocupação já calculada
    de outros obstáculos nesta mesma grade (a parte fixa da cena)."""
    if x_ini is None or x_fim is None:
        return ResultadoGabarito(None, "NÃO VERIFICÁVEL: posição da coluna/pedal a confirmar", [])
    xs, zs = grade(x_ini, x_fim, z_min, z_max, passo_x, passo_z)
    occ = ocupacao(obstaculos, xs, zs, y_centro, amostras_gabarito(), tolerancia(passo_x))
    if ocupacao_base is not None:
        occ = uniao(occ, ocupacao_base)
    return caminho_livre(occ, zs)


def limite_aip(x_face_traseira_aip):
    """f(p) = x_face − p_x (m); None se a posição está a confirmar."""
    if x_face_traseira_aip is None:
        return None

    def folga(p):
        return x_face_traseira_aip - p[0]

    return folga
