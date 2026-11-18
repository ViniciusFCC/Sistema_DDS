"""
Mapa de espaço livre do posicionador (EDR-076, spec §5 item 2; TC-POS-072).

Para um ponto do chassi (pivô do rocker, olhal do amortecedor), uma grade regular na caixa de busca declarada, com, em
cada ponto da grade:
- `folga_m` = min_i sdf_i(p) − raio_m, sobre os primitivos fixos da cena (`Cena.fixos`, m, referencial do carro);
  `raio_m` é o raio da peça que vai no ponto (descontado aqui). Sem obstáculos fixos: +inf (nada a descontar);
- `dist_no_m` = distância ao nó do chassi mais próximo (`Cena.nos`, preferência U3); sem nós: +inf.

A grade inclui as duas pontas da caixa em cada eixo, com espaçamento ≤ `passo_m` (np.linspace); eixo com mín = máx vira
um ponto só. Os volumes do regulamento (gabarito T.1.2, AIP) não entram no mapa: dependem de itens a confirmar na
configuração e são conferidos por `varredura.avaliar` em cada candidato (ficam em `Mapa.nao_modelado`). As peças móveis
(aro, bandejas, push rod) também não: elas se movem com o curso.
"""
from dataclasses import dataclass, field

import numpy as np

BLOCO = 20000      # pontos por bloco no cálculo da sdf (só memória; não muda o resultado)


@dataclass
class Mapa:
    grade: np.ndarray        # (nx, ny, nz, 3) pontos [m]
    folga_m: np.ndarray      # (nx, ny, nz) folga aos fixos, já descontado raio_m [m]
    dist_no_m: np.ndarray    # (nx, ny, nz) distância ao nó mais próximo [m] (+inf sem nós)
    raio_m: float = 0.0
    passo_m: float = 0.01
    nao_modelado: list = field(default_factory=list)

    def livres(self, raio_m=0.0):
        """Pontos da grade (k, 3) com folga_m ≥ raio_m: cabe ali uma esfera de raio raio_m além do raio do mapa."""
        return self.grade[self.folga_m >= float(raio_m)]

    def dist_no_livres(self, raio_m=0.0):
        """Distância ao nó dos mesmos pontos de `livres(raio_m)`, na mesma ordem."""
        return self.dist_no_m[self.folga_m >= float(raio_m)]


def _caixa(caixa_m):
    try:
        lo, hi = (np.asarray(c, dtype=float) for c in caixa_m)
    except (TypeError, ValueError) as e:
        raise ValueError(f"caixa_m inválida (esperado (mín[3], máx[3]) em m, sem None): {caixa_m!r} ({e})") from e
    if lo.shape != (3,) or hi.shape != (3,) or not (np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))):
        raise ValueError(f"caixa_m inválida (esperado (mín[3], máx[3]) finitos, em m, sem None): {caixa_m!r}")
    if np.any(hi < lo):
        raise ValueError(f"caixa_m com máx < mín: {caixa_m!r}")
    return lo, hi


def mapa(cena, caixa_m, passo_m=0.01, raio_m=0.0):
    """Mapa de espaço livre da `cena` na caixa `caixa_m` = (mín[3], máx[3]) [m], grade de passo ≤ `passo_m`."""
    lo, hi = _caixa(caixa_m)
    if not passo_m > 0.0:
        raise ValueError(f"passo_m = {passo_m} não positivo")
    eixos = [np.linspace(a, b, int(np.ceil((b - a) / passo_m - 1e-9)) + 1) if b > a else np.array([a])
             for a, b in zip(lo, hi)]
    grade = np.stack(np.meshgrid(*eixos, indexing="ij"), axis=-1)
    pts = grade.reshape(-1, 3)
    folga = np.full(len(pts), np.inf)
    dist = np.full(len(pts), np.inf)
    nos = np.array([np.asarray(n.pos_m, dtype=float) for n in cena.nos]).reshape(-1, 3)
    for i in range(0, len(pts), BLOCO):
        p = pts[i:i + BLOCO]
        for ob in cena.fixos:
            folga[i:i + BLOCO] = np.minimum(folga[i:i + BLOCO], ob.sdf(p))
        if len(nos):
            dist[i:i + BLOCO] = np.linalg.norm(p[:, None, :] - nos[None, :, :], axis=2).min(axis=1)
    folga = folga - float(raio_m)
    forma = grade.shape[:3]
    nao = ["volumes do regulamento (gabarito T.1.2, AIP): conferidos por varredura.avaliar, não pelo mapa",
           "peças móveis (aro, bandejas, push rod): conferidas na varredura do curso"]
    if not cena.fixos:
        nao.insert(0, "sem obstáculos fixos na cena: toda a caixa é livre")
    return Mapa(grade, folga.reshape(forma), dist.reshape(forma), float(raio_m), float(passo_m), nao)
