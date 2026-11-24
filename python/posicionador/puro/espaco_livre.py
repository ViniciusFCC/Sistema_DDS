"""
Mapa de espaço livre em Python puro: porte de `posicionador.espaco_livre` (grade regular na caixa de busca; folga aos fixos
e distância ao nó do chassi mais próximo). Mesma grade, mesma ordem dos pontos (x mais externo, z mais interno).
Diferença de método: a folga de cada ponto só considera os primitivos cuja caixa envolvente, inflada por `corte_m`, contém o
ponto; os outros têm sdf > corte_m. Logo `folga_m` é exata onde vale menos que `corte_m` e fica em `corte_m − raio_m` onde
vale mais (o teste confere). `livres(r)` é idêntico ao original para r < corte_m.
"""
import math
from dataclasses import dataclass, field

from posicionador.puro import linalg as la
from posicionador.puro.geometria import linspace

CORTE_M = 0.30


@dataclass
class Mapa:
    grade: list              # [(x, y, z)] na ordem x-y-z
    folga_m: list            # folga aos fixos já descontado raio_m (saturada em corte_m − raio_m)
    dist_no_m: list          # distância ao nó mais próximo (+inf sem nós)
    forma: tuple
    raio_m: float = 0.0
    passo_m: float = 0.01
    nao_modelado: list = field(default_factory=list)

    def livres(self, raio_m=0.0):
        r = float(raio_m)
        return [p for p, f in zip(self.grade, self.folga_m) if f >= r]

    def dist_no_livres(self, raio_m=0.0):
        r = float(raio_m)
        return [d for d, f in zip(self.dist_no_m, self.folga_m) if f >= r]


def _caixa(caixa_m):
    try:
        lo, hi = (tuple(float(x) for x in c) for c in caixa_m)
    except (TypeError, ValueError) as e:
        raise ValueError(f"caixa_m inválida (esperado (mín[3], máx[3]) em m, sem None): {caixa_m!r} ({e})") from e
    if len(lo) != 3 or len(hi) != 3 or not all(math.isfinite(v) for v in lo + hi):
        raise ValueError(f"caixa_m inválida (esperado (mín[3], máx[3]) finitos, em m, sem None): {caixa_m!r}")
    if any(h < l for l, h in zip(lo, hi)):
        raise ValueError(f"caixa_m com máx < mín: {caixa_m!r}")
    return lo, hi


def mapa(cena, caixa_m, passo_m=0.01, raio_m=0.0, corte_m=CORTE_M):
    lo, hi = _caixa(caixa_m)
    if not passo_m > 0.0:
        raise ValueError(f"passo_m = {passo_m} não positivo")
    eixos = [linspace(a, b, int(math.ceil((b - a) / passo_m - 1e-9)) + 1) if b > a else [a] for a, b in zip(lo, hi)]
    caixas = []
    for ob in cena.fixos:
        cx = ob.caixa_envolvente() if hasattr(ob, "caixa_envolvente") else None
        caixas.append((ob, None if cx is None else (la.sub(cx[0], (corte_m,) * 3), la.add(cx[1], (corte_m,) * 3))))
    grade, folga, dist = [], [], []
    for x in eixos[0]:
        # filtro por x: só os primitivos cuja caixa inflada contém este x
        ativos_x = [(ob, cx) for ob, cx in caixas if cx is None or cx[0][0] <= x <= cx[1][0]]
        for y in eixos[1]:
            ativos = [(ob, cx) for ob, cx in ativos_x if cx is None or cx[0][1] <= y <= cx[1][1]]
            for z in eixos[2]:
                p = (x, y, z)
                f = corte_m
                for ob, cx in ativos:
                    if cx is None or (cx[0][2] <= z <= cx[1][2]):
                        s = ob.sdf(p)
                        if s < f:
                            f = s
                grade.append(p)
                folga.append(f - float(raio_m))
                dist.append(min((la.norm(la.sub(p, n)) for n in cena.nos), default=math.inf))
    nao = ["volumes do regulamento (gabarito T.1.2, AIP): conferidos por varredura.avaliar, não pelo mapa",
           "peças móveis (aro, bandejas, push rod): conferidas na varredura do curso"]
    if not cena.fixos:
        nao.insert(0, "sem obstáculos fixos na cena: toda a caixa é livre")
        folga = [math.inf - float(raio_m) for _ in folga]
    return Mapa(grade, folga, dist, (len(eixos[0]), len(eixos[1]), len(eixos[2])), float(raio_m), float(passo_m), nao)
