"""T11_posicionador: o posicionador da atuacao dianteira dentro do Fusion (fase 2, EDR-077). SOMENTE LEITURA.

Nao cria nem altera geometria, nao salva nem fecha documentos. Os corpos temporarios (cilindros finos usados para medir
distancia) existem so em memoria. Le a configuracao da execucao em C:\\Projetos\\posicionador_fusion_config.json:

    {"raiz_repo": "<pasta do repositorio ou do worktree>",          # tem python/ e data/posicionador/
     "modo": "posicionar" | "medicao",
     "documento_esperado": "T11_atuacao_v20_1_murilo_teste_nomes_corrigidos",   # recusa rodar em outro documento
     "saida": "C:\\\\Projetos\\\\posicionador_fusion_saida",
     "hardpoints": "data/posicionador/hardpoints_T11_v20_1_cad.csv",   # base dos pontos; os 9 HP_FL vem do CAD ao vivo
     "mapa_componentes": "C:\\\\Projetos\\\\mapa_componentes.json",   # opcional
     "params": {"n_amostras": 200, "n_refinos": 5, "semente": 0, "passo_m": 0.02, "corte_m": 0.05, ...}}

Os modulos do repositorio sao importados do caminho acima (nada e copiado para a pasta do script) e recarregados a cada
execucao. Escreve progresso.log, status.json e as saidas na pasta `saida`.
"""
import json
import os
import sys
import time
import traceback

import adsk.core
import adsk.fusion

CONFIG = r"C:\Projetos\posicionador_fusion_config.json"


def _gravar(caminho, obj):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def run(_context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    cfgx = None
    saida = r"C:\Projetos\posicionador_fusion_saida"
    status = {"script": "T11_posicionador", "somente_leitura": True, "python": sys.version, "inicio": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfgx = json.load(f)
        saida = cfgx.get("saida", saida)
        os.makedirs(saida, exist_ok=True)
        log = open(os.path.join(saida, "progresso.log"), "w", encoding="utf-8", buffering=1)

        def say(msg):
            log.write(f"{time.strftime('%H:%M:%S')} {msg}\n")

        _gravar(os.path.join(saida, "status.json"), dict(status, estado="iniciado"))
        raiz = cfgx["raiz_repo"]
        for k in [k for k in sys.modules if k == "posicionador" or k.startswith("posicionador.")]:
            del sys.modules[k]                       # o Fusion mantem os modulos entre execucoes: recarrega o repositorio
        sys.path.insert(0, os.path.join(raiz, "python"))
        from posicionador import config as pc
        from posicionador import reconhecimento as rc
        from posicionador.fusion import api, pipeline as pl

        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            raise RuntimeError("sem design ativo: abra o T11 em modo Design e rode de novo")
        doc = app.activeDocument.name
        esperado = cfgx.get("documento_esperado")
        if esperado and not doc.startswith(esperado):
            raise RuntimeError(f"documento ativo {doc!r} nao e o esperado {esperado!r}: nada foi feito")
        status.update(documento=doc, modo=cfgx["modo"])
        say(f"documento {doc}; modo {cfgx['modo']}; Python {sys.version.split()[0]}")

        t0 = time.perf_counter()
        geo, corpos = api.ler_geometria(design)
        say(f"CAD lido: {len(corpos)} corpos, {geo['n_ocorrencias']} ocorrencias ({time.perf_counter() - t0:.2f} s)")
        _gravar(os.path.join(saida, "geometria_lida.json"), geo)
        mapa = rc.carregar_mapa(cfgx["mapa_componentes"]) if cfgx.get("mapa_componentes") and os.path.exists(cfgx["mapa_componentes"]) else None
        cfg = pc.carregar(os.path.join(raiz, "data", "posicionador", "config_T11.json"))
        caminho_hp = os.path.join(raiz, cfgx.get("hardpoints", "data/posicionador/hardpoints_T11_v20_1_cad.csv"))
        orac = api.OraculoFusion(app, corpos)
        params = dict(cfgx.get("params", {}))
        ultimo = [0.0]

        def progresso(fase, i, n, melhor):
            agora = time.monotonic()
            if i == n or agora - ultimo[0] >= 5.0:
                ultimo[0] = agora
                say(f"{fase}: {i}/{n}; menor violacao ate aqui {melhor:.4g}; chamadas a API {orac.n_chamadas}")
                adsk.doEvents()                       # mantem a janela do Fusion viva durante a busca

        if cfgx["modo"] == "medicao":
            from posicionador.fusion import medicao as md
            prep = pl.preparar(geo, orac, cfg, caminho_hp, mapa, params.get("corte_m", 0.05))
            say(f"cena: {len(prep.fixos)} corpos; promovidos {[d.componente for d in prep.classificacao.promovidos]}")
            with open(os.path.join(raiz, "data", "posicionador", "origem_v20_script.json"), encoding="utf-8") as f:
                x20 = json.load(f)["x_semente"]
            out = md.medir(app, prep, orac, cfg, x20, prep.v10, [f.id for f in prep.fixos], None,
                           n_seg=params.get("n_seg", 300), n_exato=params.get("n_exato", 60), n_pontos=params.get("n_pontos", 1000))
            _gravar(os.path.join(saida, "medicao.json"), out)
        else:
            d, res = pl.executar(geo, orac, cfg, caminho_hp, saida, params, mapa, progresso)
            status.update(n_viaveis=d["estatisticas"].get("n_viaveis"), tempo_s=d["tempo_s"])
        status.update(estado="concluido", fim=time.strftime("%Y-%m-%d %H:%M:%S"), chamadas_api=orac.n_chamadas, erros_api=orac.n_erros)
        _gravar(os.path.join(saida, "status.json"), status)
        say("concluido")
        log.close()
    except Exception:  # noqa: BLE001
        status.update(estado="ERRO", erro=traceback.format_exc())
        try:
            _gravar(os.path.join(saida, "status.json"), status)
        except Exception:  # noqa: BLE001
            pass
        app.log("T11_posicionador falhou:\n" + traceback.format_exc())
        ui.messageBox("T11_posicionador: erro (detalhe em " + os.path.join(saida, "status.json") + "):\n" + traceback.format_exc()[-1500:])
