"""T11_sondagem: sondagem SOMENTE LEITURA do Fusion para o posicionador (fase 2).

Nao cria nem altera geometria, nao salva nem fecha documentos, nao instala nada.
Os corpos temporarios usados nos testes de API (TemporaryBRepManager) existem so em memoria
e nunca sao adicionados ao documento.
Grava o resultado em C:\\Projetos\\fusion_sondagem.json (reescrito a cada etapa, para sobrar algo se uma etapa travar).
"""
import importlib
import json
import os
import platform
import sys
import time
import traceback

import adsk.core
import adsk.fusion

# Reconhecimento de componentes pelo nome (modulo em Python puro, copia de python/posicionador/reconhecimento.py,
# na mesma pasta deste script).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reconhecimento as rc  # noqa: E402

SAIDA = r"C:\Projetos\fusion_sondagem2.json"
MAPA_COMPONENTES = r"C:\Projetos\mapa_componentes.json"   # opcional: {"nome do componente": "CATEGORIA"}
VARRER = ("REF_REFERENCIAS", "HP_FRENTE", "IGNORAR_PONTOS_V20_11")   # ocorrencias de primeiro nivel a abrir
PROF_MAX = 4
N_CHAMADAS = 200
MAX_LISTA = 200

app = adsk.core.Application.get()
ui = app.userInterface
res = {"script": "T11_sondagem", "somente_leitura": True}


def gravar():
    """Reescreve o JSON inteiro (chamado depois de cada etapa)."""
    try:
        os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
        with open(SAIDA, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    except Exception:  # pylint:disable=broad-except
        app.log("T11_sondagem: falha ao gravar o JSON:\n" + traceback.format_exc())


def etapa(nome):
    """Decorador: roda a etapa, registra erro em res[nome] e grava o arquivo."""
    def deco(fn):
        try:
            res[nome] = fn()
        except Exception:  # pylint:disable=broad-except
            res[nome] = {"ERRO": traceback.format_exc()}
        gravar()
        return fn
    return deco


def media_ms(fn, n=N_CHAMADAS):
    """Tempo medio (ms) de n chamadas e o primeiro valor retornado (ou o erro)."""
    t0 = time.perf_counter()
    primeiro = None
    for i in range(n):
        v = fn()
        if i == 0:
            primeiro = v
    dt = (time.perf_counter() - t0) / n * 1000.0
    return {"n": n, "media_ms": dt, "primeiro_valor": primeiro}


def corpos_do_design(design):
    """Corpos do componente raiz e dos de todas as ocorrencias (proxies no contexto da raiz)."""
    raiz = design.rootComponent
    out = [("raiz", b) for b in raiz.bRepBodies]
    for occ in raiz.allOccurrences:
        for b in occ.bRepBodies:
            out.append((occ.fullPathName, b))
    return out


def run(_context):
    try:
        res["python"] = {
            "sys.version": sys.version,
            "sys.executable": sys.executable,
            "platform": platform.platform(),
            "sys.path": list(sys.path),
        }
        gravar()

        @etapa("bibliotecas")
        def _():
            out = {}
            for mod in ("numpy", "scipy", "scipy.optimize", "OCP", "cadquery", "pip", "setuptools"):
                try:
                    m = importlib.import_module(mod)
                    out[mod] = {"ok": True, "versao": getattr(m, "__version__", None),
                                "arquivo": getattr(m, "__file__", None)}
                except Exception as e:  # pylint:disable=broad-except
                    out[mod] = {"ok": False, "erro": f"{type(e).__name__}: {e}"}
            return out

        @etapa("fusion")
        def _():
            return {
                "version": app.version,
                "isStartupComplete": app.isStartupComplete,
                "preferredLanguage": str(app.preferences.generalPreferences.userLanguage)
                if hasattr(app.preferences, "generalPreferences") else None,
            }

        @etapa("documentos")
        def _():
            docs = []
            for d in app.documents:
                docs.append({"name": d.name, "isSaved": d.isSaved, "isModified": d.isModified,
                             "isActive": d == app.activeDocument})
            return {"n": len(docs), "lista": docs}

        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            res["design"] = {"ativo": False,
                             "obs": "Sem design ativo (abra o T11 em modo Design e rode de novo)."}
            gravar()
            ui.messageBox("T11_sondagem: sem design ativo. Resultado parcial em " + SAIDA)
            return
        raiz = design.rootComponent

        @etapa("design")
        def _():
            return {
                "ativo": True,
                "documento": app.activeDocument.name,
                "designType": str(design.designType),
                "unidade_comprimento_padrao": design.unitsManager.defaultLengthUnits,
                "nota_unidades_api": "a API usa centimetros internamente",
                "n_componentes": design.allComponents.count,
                "n_ocorrencias": raiz.allOccurrences.count,
            }

        corpos = []

        @etapa("corpos")
        def _():
            nonlocal corpos
            corpos = corpos_do_design(design)
            lista = []
            for onde, b in corpos[:MAX_LISTA]:
                lista.append({"onde": onde, "nome": b.name, "isSolid": b.isSolid,
                              "isTemporary": b.isTemporary, "isVisible": b.isVisible,
                              "faces": b.faces.count})
            return {"n_total": len(corpos), "n_listados": len(lista), "lista": lista}

        @etapa("pontos_de_construcao")
        def _():
            ref, outros, total = [], [], 0
            for comp in design.allComponents:
                for cp in comp.constructionPoints:
                    total += 1
                    g = cp.geometry
                    item = {"componente": comp.name, "nome": cp.name,
                            "xyz_cm": [g.x, g.y, g.z], "isParametric": cp.isParametric}
                    if cp.name.startswith("REF_"):
                        ref.append(item)
                    elif len(outros) < 50:
                        outros.append(item)
            return {"n_total": total, "n_REF": len(ref), "REF": ref[:MAX_LISTA],
                    "amostra_outros_ate_50": outros}

        @etapa("parametros_do_usuario")
        def _():
            lista = []
            for p in design.userParameters:
                lista.append({"nome": p.name, "expressao": p.expression, "valor": p.value,
                              "unidade": p.unit, "comentario": p.comment})
            return {"n": len(lista), "lista": lista[:MAX_LISTA]}

        @etapa("croquis_e_planos")
        def _():
            return {"n_croquis_raiz": raiz.sketches.count,
                    "nomes_croquis_raiz": [s.name for s in raiz.sketches][:MAX_LISTA]}

        # ---- desempenho ----
        mm = app.measureManager
        solidos = [(o, b) for o, b in corpos if b.isSolid]
        P3 = adsk.core.Point3D

        @etapa("medida_distancia_minima")
        def _():
            if len(solidos) < 2:
                return {"obs": "menos de 2 corpos solidos; medida nao feita", "n_solidos": len(solidos)}
            b1, b2 = solidos[0][1], solidos[1][1]
            r = media_ms(lambda: mm.measureMinimumDistance(b1, b2).value)
            r["corpos"] = [b1.name, b2.name]
            r["unidade_valor"] = "cm"
            return r

        @etapa("medida_distancia_ponto_corpo")
        def _():
            if not solidos:
                return {"obs": "sem corpo solido"}
            b1 = solidos[0][1]
            pt = P3.create(100.0, 100.0, 100.0)
            r = media_ms(lambda: mm.measureMinimumDistance(pt, b1).value)
            r["corpos"] = [b1.name]
            return r

        @etapa("corpo_temporario_na_api")
        def _():
            """Verifica o que da pra fazer com corpos temporarios (nada vai para o documento)."""
            tbm = adsk.fusion.TemporaryBRepManager.get()
            out = {}
            p1, p2 = P3.create(0, 0, 0), P3.create(0, 0, 30.0)
            cil = tbm.createCylinderOrCone(p1, 1.25, p2, 1.25)
            out["cilindro_temporario_criado"] = cil is not None
            out["cilindro_isTemporary"] = bool(cil.isTemporary) if cil else None
            if cil:
                out["tempo_criar_cilindro"] = media_ms(
                    lambda: tbm.createCylinderOrCone(p1, 1.25, p2, 1.25) is not None)
            if cil and solidos:
                b1 = solidos[0][1]
                try:
                    v = mm.measureMinimumDistance(cil, b1).value
                    out["measure_temporario_vs_corpo"] = {"ok": True, "valor_cm": v}
                    out["tempo_measure_temporario_vs_corpo"] = media_ms(
                        lambda: mm.measureMinimumDistance(cil, b1).value)
                except Exception as e:  # pylint:disable=broad-except
                    out["measure_temporario_vs_corpo"] = {"ok": False,
                                                          "erro": f"{type(e).__name__}: {e}"}
                # interferencia por booleana (copia temporaria do corpo; o original nao e tocado)
                try:
                    alvo = tbm.copy(b1)
                    ok = tbm.booleanOperation(alvo, cil, adsk.fusion.BooleanTypes.IntersectionBooleanType)
                    out["booleana_intersecao_temporaria"] = {
                        "ok": bool(ok), "resultado_tem_volume": bool(alvo.volume > 0) if ok else None}
                except Exception as e:  # pylint:disable=broad-except
                    out["booleana_intersecao_temporaria"] = {"ok": False,
                                                             "erro": f"{type(e).__name__}: {e}"}
            return out

        @etapa("medida_pontos_construcao")
        def _():
            cps = [cp for comp in design.allComponents for cp in comp.constructionPoints]
            if len(cps) < 2:
                return {"obs": "menos de 2 pontos de construcao"}
            a, b = cps[0], cps[1]
            r = media_ms(lambda: mm.measureMinimumDistance(a, b).value)
            r["pontos"] = [a.name, b.name]
            return r

        @etapa("analyzeInterference")
        def _():
            if len(solidos) < 2:
                return {"obs": "menos de 2 corpos solidos"}
            col = adsk.core.ObjectCollection.create()
            col.add(solidos[0][1])
            col.add(solidos[1][1])
            inp = design.createInterferenceInput(col)
            t0 = time.perf_counter()
            r = design.analyzeInterference(inp)
            dt = (time.perf_counter() - t0) * 1000.0
            return {"n_interferencias": r.count, "tempo_ms_1_chamada": dt,
                    "corpos": [solidos[0][1].name, solidos[1][1].name]}

        # ---- reconhecimento dos componentes pelo nome (somente leitura) ----
        mapa_usuario = None
        if os.path.exists(MAPA_COMPONENTES):
            try:
                mapa_usuario = rc.carregar_mapa(MAPA_COMPONENTES)
            except Exception:  # pylint:disable=broad-except
                res["mapa_componentes_ERRO"] = traceback.format_exc()

        @etapa("reconhecimento_componentes")
        def _():
            lista, itens = [], []
            for occ in raiz.occurrences:
                r = rc.reconhecer(occ.name, mapa_usuario)
                lista.append(r)
                item = {"ocorrencia": occ.name, "componente": occ.component.name, "categoria": r.categoria,
                        "nivel": r.nivel, "usavel": r.usavel, "motivo": r.motivo,
                        "n_corpos": occ.component.bRepBodies.count, "n_filhos": occ.childOccurrences.count,
                        "visivel": getattr(occ, "isLightBulbOn", None)}
                if rc.nome_base(occ.component.name) != rc.nome_base(occ.name):
                    rcomp = rc.reconhecer(occ.component.name, mapa_usuario)
                    item["pelo_nome_do_componente"] = {"categoria": rcomp.categoria, "nivel": rcomp.nivel}
                itens.append(item)
            return {"mapa_usado": mapa_usuario is not None, "arquivo_do_mapa": MAPA_COMPONENTES,
                    "n": len(itens), "resumo": rc.resumo(lista), "modelo_de_mapa": rc.modelo_de_mapa(lista),
                    "itens": itens}

        # ---- conteudo das ocorrencias que deveriam guardar os pontos REF_ e HP_ ----
        def xyz(p):
            return [p.x, p.y, p.z]

        def info_corpo(b):
            d = {"nome": b.name, "isSolid": b.isSolid, "n_faces": b.faces.count}
            bb = b.boundingBox
            d["bbox_centro_cm"] = [(bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.y + bb.maxPoint.y) / 2,
                                   (bb.minPoint.z + bb.maxPoint.z) / 2]
            d["bbox_dim_cm"] = [bb.maxPoint.x - bb.minPoint.x, bb.maxPoint.y - bb.minPoint.y,
                                bb.maxPoint.z - bb.minPoint.z]
            if b.faces.count == 1:
                sph = adsk.core.Sphere.cast(b.faces.item(0).geometry)
                if sph:
                    d["esfera"] = {"centro_cm": xyz(sph.origin), "raio_cm": sph.radius}
            return d

        def varrer(occ, prof):
            comp = occ.component
            out = {"ocorrencia": occ.fullPathName, "componente": comp.name, "n_corpos": occ.bRepBodies.count,
                   "corpos": [info_corpo(b) for b in list(occ.bRepBodies)[:MAX_LISTA]]}
            pontos = []
            for cp in comp.constructionPoints:
                try:
                    g, ctx = cp.createForAssemblyContext(occ).geometry, "raiz"
                except Exception:  # pylint:disable=broad-except
                    g, ctx = cp.geometry, "local"
                pontos.append({"nome": cp.name, "xyz_cm": xyz(g), "contexto": ctx})
            out["pontos_de_construcao"] = pontos[:MAX_LISTA]
            croquis = []
            for sk in comp.sketches:
                try:
                    sx, ctx = sk.createForAssemblyContext(occ), "raiz"
                except Exception:  # pylint:disable=broad-except
                    sx, ctx = sk, "local"
                pts = []
                for sp in sx.sketchPoints:
                    try:
                        g = sp.worldGeometry
                    except Exception:  # pylint:disable=broad-except
                        g = sp.geometry
                    pts.append(xyz(g))
                croquis.append({"nome": sk.name, "n_pontos": sx.sketchPoints.count, "contexto": ctx,
                                "pontos_xyz_cm": pts[:MAX_LISTA]})
            out["croquis"] = croquis
            if prof < PROF_MAX:
                out["filhos"] = [varrer(ch, prof + 1) for ch in occ.childOccurrences]
            return out

        @etapa("varredura_ref_hp")
        def _():
            achadas, resultado = [], []
            for occ in raiz.occurrences:
                if rc.nome_base(occ.name).startswith(VARRER):
                    achadas.append(occ.name)
                    resultado.append(varrer(occ, 0))
            return {"procuradas": list(VARRER), "achadas": achadas, "conteudo": resultado}

        # ---- distancia de um corpo temporario contra o chassi e contra todos os solidos ----
        @etapa("distancia_temporario_vs_chassi")
        def _():
            tbm = adsk.fusion.TemporaryBRepManager.get()
            cil = tbm.createCylinderOrCone(P3.create(0, 0, 0), 1.25, P3.create(0, 0, 30.0), 1.25)

            def varre(alvos, reps):
                t0, menor = time.perf_counter(), None
                for _ in range(reps):
                    for b in alvos:
                        v = mm.measureMinimumDistance(cil, b).value
                        menor = v if menor is None or v < menor else menor
                dt = (time.perf_counter() - t0) * 1000.0
                return {"n_corpos": len(alvos), "repeticoes": reps, "tempo_total_ms_por_varredura": dt / reps,
                        "tempo_medio_por_corpo_ms": dt / reps / max(len(alvos), 1), "menor_distancia_cm": menor}

            chassi = [b for o, b in solidos if o.startswith("CHASSI_T11_V20")]
            out = {"chassi": varre(chassi, 5), "todos_os_solidos": varre([b for _, b in solidos], 3)}
            occs = [o for o in raiz.occurrences if o.name.startswith("CHASSI_T11_V20")]
            if occs:
                try:
                    out["contra_ocorrencia_inteira"] = media_ms(
                        lambda: mm.measureMinimumDistance(cil, occs[0]).value, n=20)
                except Exception as e:  # pylint:disable=broad-except
                    out["contra_ocorrencia_inteira"] = {"erro": f"{type(e).__name__}: {e}"}
            return out

        res["concluido"] = True
        gravar()
        ui.messageBox("T11_sondagem concluida (somente leitura).\nResultado em:\n" + SAIDA)
    except Exception:  # pylint:disable=broad-except
        res["ERRO_GERAL"] = traceback.format_exc()
        gravar()
        app.log("T11_sondagem falhou:\n" + traceback.format_exc())
