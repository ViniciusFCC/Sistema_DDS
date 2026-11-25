"""
Ponte com a API do Fusion (única parte do adaptador que importa `adsk`): lê o CAD, mede distâncias. SOMENTE LEITURA:
corpos temporários vivem só em memória (`TemporaryBRepManager`) e nunca entram no documento; nada é salvo nem alterado.

Unidades da API: cm (conversão na fronteira, em `cena.py` e `pipeline.py`). Coordenadas do CAD (não do carro).
"""
import time

import adsk.core
import adsk.fusion

CM_PARA_MM = 10.0


def _mm(v):
    return [v.x * CM_PARA_MM, v.y * CM_PARA_MM, v.z * CM_PARA_MM]


def ler_geometria(design):
    """(geo, corpos): `geo` no formato de `identificacao.verificar` (etapa `geometria_por_componente` da sondagem, mm,
    coordenadas do CAD), com um campo extra `id` em cada corpo (índice em `corpos`, a lista dos objetos da API)."""
    raiz = design.rootComponent
    topos, corpos = {}, []
    n_occ = 0
    for occ in raiz.allOccurrences:
        n_occ += 1
        partes = occ.fullPathName.split("+")
        g = topos.setdefault(partes[0], {"ocorrencias": []})
        lista = []
        for b in occ.bRepBodies:
            bb = b.boundingBox
            c = {"id": len(corpos), "nome": b.name, "isSolid": bool(b.isSolid), "min_mm": _mm(bb.minPoint), "max_mm": _mm(bb.maxPoint)}
            if b.faces.count == 1:
                sph = adsk.core.Sphere.cast(b.faces.item(0).geometry)
                if sph:
                    c["esfera"] = {"centro_mm": _mm(sph.origin), "raio_mm": sph.radius * CM_PARA_MM}
            corpos.append(b)
            lista.append(c)
        g["ocorrencias"].append({"caminho": occ.fullPathName, "profundidade": len(partes) - 1, "nome": occ.name, "corpos": lista})
    geo = {"unidade": "mm (a API usa cm; convertido aqui)", "n_ocorrencias": n_occ, "n_corpos_raiz": raiz.bRepBodies.count, "topos": topos}
    return geo, corpos


class OraculoFusion:
    """Distâncias pela API. `dist_ponto` e `dist_segmento` devolvem cm; 0 quando se tocam ou se cruzam."""

    def __init__(self, app, corpos):
        self.mm = app.measureManager
        self.tbm = adsk.fusion.TemporaryBRepManager.get()
        self.corpos = corpos
        self.n_chamadas = 0
        self.n_erros = 0
        self.tempo_s = 0.0
        self.ultimo_erro = None

    def _medir(self, geometria, id_corpo):
        t0 = time.perf_counter()
        try:
            self.n_chamadas += 1
            return float(self.mm.measureMinimumDistance(geometria, self.corpos[id_corpo]).value)
        except Exception as e:  # noqa: BLE001  (a falha vira exceção no núcleo, que a trata como INVIAVEL com motivo)
            self.n_erros += 1
            self.ultimo_erro = f"{type(e).__name__}: {e}"
            raise
        finally:
            self.tempo_s += time.perf_counter() - t0

    def dist_ponto(self, id_corpo, p_cm):
        return self._medir(adsk.core.Point3D.create(*p_cm), id_corpo)

    def dist_segmento(self, id_corpo, a_cm, b_cm, r_fino_cm):
        if sum((a_cm[k] - b_cm[k]) ** 2 for k in range(3)) < 1e-12:      # segmento de comprimento nulo: um ponto
            return self.dist_ponto(id_corpo, a_cm)
        cil = self.tbm.createCylinderOrCone(adsk.core.Point3D.create(*a_cm), r_fino_cm, adsk.core.Point3D.create(*b_cm), r_fino_cm)
        return self._medir(cil, id_corpo)
