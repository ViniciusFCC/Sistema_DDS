"""
Cena do Fusion para o núcleo puro: obstáculos fixos que medem a folga PELA API de distância do Fusion (decisão registrada
em `docs/posicionador/fusion/ADAPTADOR.md`), sem aproximar o chassi por primitivos.

Cada corpo sólido do chassi (e dos itens promovidos a obstáculo) vira um `FixoFusion`, que o núcleo trata como qualquer
primitivo: `sdf(p)` (usado pelo mapa de espaço livre), `caixa_envolvente()` (o mapa e o gabarito filtram por ela) e
`folga_segmento(a, b, raio, passo)` (a varredura; `puro.geometria.folga_segmento` o chama no lugar de amostrar a SDF).

Como se mede um segmento engrossado (cápsula) com a API: a API aceita corpo temporário (cilindro) em
`measureMinimumDistance`, mas o cilindro de pontas planas não é a cápsula. Mede-se então um cilindro FINO (raio `R_FINO_M`)
sobre o eixo do segmento e desconta-se o raio verdadeiro:  folga = d_fino − raio. Como o cilindro fino contém o segmento e
está contido na cápsula de raio `R_FINO_M`, d_seg − R_FINO_M ≤ d_fino ≤ d_seg: a folga sai no máximo `R_FINO_M` abaixo da
verdadeira (conservadora). Vale também com penetração: se a cápsula entra no corpo, d_fino − raio < 0 (e se o próprio eixo
atravessa o corpo, d_fino = 0 e a folga é −raio). Uma medida serve a qualquer raio do mesmo segmento.

Saturação: a folga devolvida nunca passa de `corte_m` (o mesmo papel do corte do mapa de espaço livre). A caixa envolvente
do corpo decide antes: se a caixa do segmento (com o raio) está a `corte_m` ou mais da caixa do corpo, devolve-se `corte_m`
sem chamar a API (a distância entre caixas é limite inferior da distância entre os sólidos).

O oráculo (a ponte para a API) é injetado: o módulo não importa `adsk` e os testes usam um oráculo falso.
Unidades do oráculo: as da API do Fusion (cm) e coordenadas do CAD; aqui tudo é convertido na fronteira (núcleo em m, no
referencial do carro). Só biblioteca padrão.
"""
import math
from dataclasses import dataclass, field

R_FINO_M = 0.0002          # raio do cilindro fino medido sobre o eixo do segmento (0,2 mm)
CORTE_M = 0.05             # saturação da folga (m)
CM_POR_M = 100.0


@dataclass
class Quadro:
    """Referencial do carro no CAD: origem e eixos unitários (do `identificacao.referencial`, em mm)."""
    origem_mm: tuple
    eixos: tuple           # (ex, ey, ez) no referencial do CAD

    def para_cad_cm(self, p_m):
        """Ponto do carro (m) → coordenadas do CAD em cm (a unidade da API)."""
        return tuple((self.origem_mm[k] + 1000.0 * (p_m[0] * self.eixos[0][k] + p_m[1] * self.eixos[1][k]
                                                    + p_m[2] * self.eixos[2][k])) / 10.0 for k in range(3))

    def para_carro_m(self, p_cad_mm):
        d = [p_cad_mm[k] - self.origem_mm[k] for k in range(3)]
        return tuple(sum(d[k] * self.eixos[i][k] for k in range(3)) / 1000.0 for i in range(3))

    def caixa_carro_m(self, lo_mm, hi_mm):
        """Caixa alinhada ao carro (m) que contém a caixa alinhada ao CAD (mm), pelos 8 cantos."""
        cantos = [self.para_carro_m((x, y, z)) for x in (lo_mm[0], hi_mm[0]) for y in (lo_mm[1], hi_mm[1])
                  for z in (lo_mm[2], hi_mm[2])]
        return (tuple(min(c[k] for c in cantos) for k in range(3)), tuple(max(c[k] for c in cantos) for k in range(3)))


def dist_caixas(lo1, hi1, lo2, hi2):
    """Distância entre duas caixas alinhadas aos eixos (0 se se tocam ou se cruzam)."""
    return math.sqrt(sum(max(lo1[k] - hi2[k], lo2[k] - hi1[k], 0.0) ** 2 for k in range(3)))


@dataclass
class Contagem:
    """Chamadas ao oráculo e filtradas pela caixa: medidas do custo (vão para o relatório)."""
    segmentos_pedidos: int = 0
    segmentos_medidos: int = 0
    pontos_pedidos: int = 0
    pontos_medidos: int = 0
    tempo_oraculo_s: float = 0.0


@dataclass
class FixoFusion:
    id: int                          # índice do corpo no oráculo
    nome: str
    lo: tuple                        # caixa do corpo no referencial do carro [m]
    hi: tuple
    quadro: Quadro
    oraculo: object
    contagem: Contagem = field(default_factory=Contagem, repr=False)
    corte_m: float = CORTE_M

    def caixa_envolvente(self):
        return self.lo, self.hi

    def sdf(self, p):
        self.contagem.pontos_pedidos += 1
        if dist_caixas(p, p, self.lo, self.hi) >= self.corte_m:
            return self.corte_m
        self.contagem.pontos_medidos += 1
        d = self.oraculo.dist_ponto(self.id, self.quadro.para_cad_cm(p)) / CM_POR_M
        return min(d, self.corte_m)

    def folga_segmento(self, a, b, raio, passo=None):  # noqa: ARG002 (o passo é da amostragem da SDF; aqui não se amostra)
        self.contagem.segmentos_pedidos += 1
        lo = tuple(min(a[k], b[k]) - raio for k in range(3))
        hi = tuple(max(a[k], b[k]) + raio for k in range(3))
        if dist_caixas(lo, hi, self.lo, self.hi) >= self.corte_m:
            return self.corte_m
        self.contagem.segmentos_medidos += 1
        d = self.oraculo.dist_segmento(self.id, self.quadro.para_cad_cm(a), self.quadro.para_cad_cm(b), R_FINO_M * CM_POR_M) / CM_POR_M
        return min(d - raio, self.corte_m)
