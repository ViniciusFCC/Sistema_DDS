"""
Medições dentro do Fusion que fundamentam a escolha da cena (API de distância × primitivos aproximados). SOMENTE LEITURA.
Chamado por `T11_posicionador` no modo "medicao"; devolve um dicionário (vira `medicao.json`). Cada experimento é isolado:
um que falha registra o erro e os outros seguem.

E1 semântica da API: distância a um corpo quando o cilindro fino ou o ponto TOCA o corpo (zero? erro?) e a distância certa
   quando não toca (um tubo do chassi, com eixo, parede e fora da parede).
E2 censo dos corpos do chassi: tipos de superfície, volume × volume da caixa alinhada (diz o quanto uma caixa por corpo erra).
E3 custo por segmento com o filtro por caixa, e conferência do filtro contra a medida em todos os corpos do chassi.
E4 erro da aproximação mais simples (uma caixa alinhada por corpo) contra a distância exata da API.
E5 custo por ponto (o mapa de espaço livre).
E6 custo de um candidato inteiro (avaliar da v20 com a cena do Fusion), em n = 11 e n = 25.
"""
import math
import random
import time
import traceback

import adsk.core

from posicionador.fusion import cena as fc
from posicionador.puro import geometria as pg
from posicionador.puro import mecanismo as pmec
from posicionador.puro import varredura as pvr


def _tipos():
    return {int(getattr(adsk.core.SurfaceTypes, n)): n for n in dir(adsk.core.SurfaceTypes) if n.endswith("SurfaceType")}


def _isolado(res, nome, fn):
    t0 = time.perf_counter()
    try:
        res[nome] = fn()
    except Exception:  # noqa: BLE001
        res[nome] = {"ERRO": traceback.format_exc()}
    if isinstance(res[nome], dict):
        res[nome]["tempo_do_experimento_s"] = time.perf_counter() - t0


def _segmentos(n, semente, caixa=((-0.15, 0.0, 0.06), (0.15, 0.326, 0.60)), comp=(0.05, 0.30)):
    rng = random.Random(semente)
    out = []
    for _ in range(n):
        a = tuple(rng.uniform(caixa[0][k], caixa[1][k]) for k in range(3))
        v = [rng.gauss(0, 1) for _ in range(3)]
        nv = math.sqrt(sum(x * x for x in v))
        L = rng.uniform(*comp)
        out.append((a, tuple(a[k] + v[k] / nv * L for k in range(3))))
    return out


def _e1(app, orac, corpos_chassi, geo_corpos):
    tipos = _tipos()
    achado = None
    for id_corpo in corpos_chassi:
        b = orac.corpos[id_corpo]
        for f in b.faces:
            cil = adsk.core.Cylinder.cast(f.geometry)
            if cil and 0.5 <= cil.radius <= 3.0:
                achado = (id_corpo, b, f, cil)
                break
        if achado:
            break
    if not achado:
        return {"obs": "nenhum corpo do chassi com face cilíndrica de raio entre 0,5 e 3 cm"}
    id_corpo, b, f, cil = achado
    o, ax, R = cil.origin, cil.axis, cil.radius
    bb = f.boundingBox
    c = adsk.core.Point3D.create((bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.y + bb.maxPoint.y) / 2, (bb.minPoint.z + bb.maxPoint.z) / 2)
    t = (c.x - o.x) * ax.x + (c.y - o.y) * ax.y + (c.z - o.z) * ax.z
    centro = (o.x + ax.x * t, o.y + ax.y * t, o.z + ax.z * t)
    # um vetor perpendicular ao eixo
    ref = (1.0, 0.0, 0.0) if abs(ax.x) < 0.9 else (0.0, 1.0, 0.0)
    perp = (ax.y * ref[2] - ax.z * ref[1], ax.z * ref[0] - ax.x * ref[2], ax.x * ref[1] - ax.y * ref[0])
    n = math.sqrt(sum(x * x for x in perp))
    perp = tuple(x / n for x in perp)
    eixo = (ax.x, ax.y, ax.z)

    def deslocado(r):
        return tuple(centro[k] + perp[k] * r for k in range(3))

    def seg(r, meio=2.0):
        p = deslocado(r)
        return (tuple(p[k] - eixo[k] * meio for k in range(3)), tuple(p[k] + eixo[k] * meio for k in range(3)))

    out = {"corpo": b.name, "raio_cm": R, "tipo_face": tipos.get(f.geometry.surfaceType), "volume_cm3": b.volume}
    for nome, r in (("eixo", 0.0), ("dentro_da_parede_R-0.02", R - 0.02), ("fora_R+0.5", R + 0.5), ("fora_R+2", R + 2.0)):
        a_, b_ = seg(r)
        try:
            out[f"segmento_fino_{nome}"] = {"valor_cm": orac.dist_segmento(id_corpo, a_, b_, 0.02), "esperado_cm": {"eixo": "0 se maciço; ≈ raio interno se oco", "dentro_da_parede_R-0.02": "0 (toca)", "fora_R+0.5": 0.5 - 0.02, "fora_R+2": 2.0 - 0.02}[nome]}
        except Exception as e:  # noqa: BLE001
            out[f"segmento_fino_{nome}"] = {"ERRO": f"{type(e).__name__}: {e}"}
        try:
            out[f"ponto_{nome}"] = {"valor_cm": orac.dist_ponto(id_corpo, deslocado(r)), }
        except Exception as e:  # noqa: BLE001
            out[f"ponto_{nome}"] = {"ERRO": f"{type(e).__name__}: {e}"}
    orac.n_erros = 0
    return out


def _e2(orac, ids, geo_corpos):
    tipos = _tipos()
    linhas, agreg = [], {}
    for i in ids:
        b = orac.corpos[i]
        bb = b.boundingBox
        vb = (bb.maxPoint.x - bb.minPoint.x) * (bb.maxPoint.y - bb.minPoint.y) * (bb.maxPoint.z - bb.minPoint.z)
        n_tipo = {}
        for f in b.faces:
            nome = tipos.get(f.geometry.surfaceType, str(f.geometry.surfaceType))
            n_tipo[nome] = n_tipo.get(nome, 0) + 1
            agreg[nome] = agreg.get(nome, 0) + 1
        linhas.append({"id": i, "nome": b.name, "faces": b.faces.count, "tipos": n_tipo, "volume_cm3": b.volume,
                       "volume_da_caixa_cm3": vb, "razao_volume": b.volume / vb if vb > 0 else None})
    razoes = sorted(l["razao_volume"] for l in linhas if l["razao_volume"] is not None)
    return {"n_corpos": len(linhas), "faces_por_tipo_total": agreg, "razao_volume_min": razoes[0] if razoes else None,
            "razao_volume_mediana": razoes[len(razoes) // 2] if razoes else None, "razao_volume_max": razoes[-1] if razoes else None,
            "corpos": linhas}


def _e3(prep, orac, segs, raio, n_exato):
    fixos = prep.fixos
    prep.contagem.__init__()
    t0 = time.perf_counter()
    filtrado = [min(f.folga_segmento(a, b, raio) for f in fixos) for a, b in segs]
    t_filtro = time.perf_counter() - t0
    c = vars(prep.contagem).copy()
    # sem filtro: todos os corpos, sem saturar (limite alto), só nos primeiros n_exato segmentos
    exatos, dif_max, n_sat = [], 0.0, 0
    t0 = time.perf_counter()
    for (a, b), fil in zip(segs[:n_exato], filtrado):
        q = [f.quadro.para_cad_cm(a) for f in fixos[:1]][0], fixos[0].quadro.para_cad_cm(b)
        m = min(orac.dist_segmento(f.id, q[0], q[1], fc.R_FINO_M * 100.0) / 100.0 - raio for f in fixos)
        exatos.append(m)
        dif_max = max(dif_max, abs(min(m, fixos[0].corte_m) - fil))
    t_exato = time.perf_counter() - t0
    return {"n_segmentos": len(segs), "raio_m": raio, "corpos_na_cena": len(fixos), "tempo_filtrado_s": t_filtro,
            "ms_por_segmento_filtrado": t_filtro / len(segs) * 1e3, "contagem": c,
            "fracao_medida": c["segmentos_medidos"] / max(c["segmentos_pedidos"], 1),
            "n_exato": n_exato, "tempo_exato_s": t_exato, "ms_por_segmento_sem_filtro": t_exato / max(n_exato, 1) * 1e3,
            "maior_diferenca_filtro_vs_exato_m": dif_max,
            "folga_min_filtrada_m": min(filtrado), "folga_max_filtrada_m": max(filtrado),
            "n_com_colisao": sum(1 for v in filtrado if v < 0.0), "n_saturados": sum(1 for v in filtrado if v >= fixos[0].corte_m)}


def _e4(prep, segs, raio, n):
    """Erro de uma caixa alinhada por corpo (a aproximação mais simples, reaproveitando as SDFs do núcleo) contra a API."""
    I = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    caixas = [pg.Caixa(tuple((f.lo[k] + f.hi[k]) / 2 for k in range(3)), I, tuple((f.hi[k] - f.lo[k]) / 2 for k in range(3))) for f in prep.fixos]
    corte = prep.fixos[0].corte_m
    dif, falso_alarme, falta, ambos_livres, ambos_col = [], 0, 0, 0, 0
    t0 = time.perf_counter()
    for a, b in segs[:n]:
        api = min(f.folga_segmento(a, b, raio) for f in prep.fixos)
        cx = min(min(pg.folga_segmento(c, a, b, raio, 0.002), corte) for c in caixas)
        dif.append(cx - api)
        if cx < 0 <= api:
            falso_alarme += 1
        elif api < 0 <= cx:
            falta += 1
        elif api < 0 and cx < 0:
            ambos_col += 1
        else:
            ambos_livres += 1
    dif.sort()
    return {"n": n, "caixa_menos_api_m": {"min": dif[0], "mediana": dif[len(dif) // 2], "max": dif[-1]},
            "caixa_diz_colisao_e_api_diz_livre": falso_alarme, "caixa_diz_livre_e_api_diz_colisao": falta,
            "ambos_livres": ambos_livres, "ambos_colisao": ambos_col, "tempo_caixas_s": time.perf_counter() - t0}


def _e5(prep, n, semente=3, caixa=((-0.15, 0.0, 0.06), (0.15, 0.326, 0.60))):
    rng = random.Random(semente)
    pts = [tuple(rng.uniform(caixa[0][k], caixa[1][k]) for k in range(3)) for _ in range(n)]
    prep.contagem.__init__()
    t0 = time.perf_counter()
    vals = [min(f.sdf(p) for f in prep.fixos) for p in pts]
    dt = time.perf_counter() - t0
    c = vars(prep.contagem).copy()
    return {"n_pontos": n, "tempo_s": dt, "ms_por_ponto": dt / n * 1e3, "contagem": c, "n_com_folga_menor_que_corte": sum(1 for v in vals if v < prep.fixos[0].corte_m),
            "n_dentro_ou_tocando": sum(1 for v in vals if v <= 0.0)}


def _e6(prep, cfg, x20, v10_vivo):
    c20 = pmec.construir(v10_vivo, pmec.Variaveis.da_semente_do_script(x20), cfg, r2_m=x20[7] / 1000.0)
    out = {"construcao_ok": c20.pontos is not None, "motivo": c20.motivo}
    if c20.pontos is None:
        return out
    cena_vazia = pvr.cena_de([], [], cfg)
    for n in (11, 25):
        prep.contagem.__init__()
        t0 = time.perf_counter()
        av = pvr.avaliar(c20, prep.cena, cfg, n)
        dt = time.perf_counter() - t0
        t1 = time.perf_counter()
        av0 = pvr.avaliar(c20, cena_vazia, cfg, n)
        dt0 = time.perf_counter() - t1
        out[f"n={n}"] = {"tempo_com_fixos_s": dt, "tempo_sem_fixos_s": dt0, "veredito": av.veredito, "motivo": av.motivo,
                         "contagem": vars(prep.contagem).copy(),
                         "folgas_aos_fixos": {r.nome: r.folga for r in av.restricoes if r.nome.startswith("folga aos fixos")}}
    return out


def medir(app, prep, orac, cfg, x20, v10_vivo, corpos_chassi, geo_corpos, n_seg=300, n_exato=60, n_pontos=1000):
    res = {}
    segs = _segmentos(n_seg, 11)
    _isolado(res, "E1_semantica_da_api", lambda: _e1(app, orac, corpos_chassi, geo_corpos))
    _isolado(res, "E2_censo_do_chassi", lambda: _e2(orac, corpos_chassi, geo_corpos))
    _isolado(res, "E3_custo_por_segmento", lambda: _e3(prep, orac, segs, 0.010, n_exato))
    _isolado(res, "E4_caixa_alinhada_vs_api", lambda: _e4(prep, segs, 0.010, min(n_seg, 300)))
    _isolado(res, "E5_custo_por_ponto", lambda: _e5(prep, n_pontos))
    _isolado(res, "E6_custo_de_um_candidato", lambda: _e6(prep, cfg, x20, v10_vivo))
    res["oraculo"] = {"n_chamadas": orac.n_chamadas, "n_erros": orac.n_erros, "tempo_s": orac.tempo_s, "ultimo_erro": orac.ultimo_erro}
    return res
