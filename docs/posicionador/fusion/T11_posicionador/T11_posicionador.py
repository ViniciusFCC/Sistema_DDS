"""T11_posicionador: o posicionador da atuacao dianteira dentro do Fusion (fase 2, EDR-077). SOMENTE LEITURA.

Nao cria nem altera geometria, nao salva nem fecha documentos. Os corpos temporarios (cilindros finos usados para medir
distancia) existem so em memoria. Abra o T11 em modo Design e rode o script (Shift+S > T11_posicionador > Run).

Pasta do script (pacote autonomo): contem `python/` (modulos), `data/posicionador/` (configuracao e hardpoints) e, opcional,
`posicionador_config.json` com as opcoes da execucao (sem ele valem os padroes abaixo). Em desenvolvimento, o arquivo
C:\\Projetos\\posicionador_fusion_config.json (com "raiz_repo") vale no lugar.

    {"modo": "posicionar" | "medicao" | "raios",       # padrao: posicionar
     "documento_esperado": "T11_atuacao_v20_1_murilo_teste",  # opcional: recusa rodar em outro documento (por prefixo)
     "saida": "C:/caminho/da/pasta",                   # padrao: Documentos/T11_posicionador_saida
     "hardpoints": "data/posicionador/hardpoints_T11_v20_1_cad.csv",
     "mapa_componentes": "C:/caminho/mapa_componentes.json",   # opcional
     "silencioso": false,                              # true: sem caixa de mensagem no fim
     "params": {"n_amostras": 2000, "n_refinos": 20, "semente": 0, "passo_m": 0.01, "corte_m": 0.05,
                "max_aval_refino": 60, "n_finalistas": 20, "caixa_m": [[xmin, ymin, zmin], [xmax, ymax, zmax]]}}

Escreve progresso.log, status.json, resultado.json, relatorio.md e um CSV por candidato na pasta de saida. Os modulos sao
recarregados a cada execucao.
"""
import json
import os
import sys
import time
import traceback

import adsk.core
import adsk.fusion

AQUI = os.path.dirname(os.path.abspath(__file__))
CONFIG_DEV = r"C:\Projetos\posicionador_fusion_config.json"
CONFIG_LOCAL = os.path.join(AQUI, "posicionador_config.json")
PADRAO = {"modo": "posicionar", "hardpoints": "data/posicionador/hardpoints_T11_v20_1_cad.csv", "silencioso": False,
          "params": {"n_amostras": 2000, "n_refinos": 20, "semente": 0, "passo_m": 0.01, "corte_m": 0.05,
                     "max_aval_refino": 60, "n_finalistas": 20}}


def _gravar(caminho, obj):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def _configuracao():
    cfg = json.loads(json.dumps(PADRAO))
    cfg["saida"] = os.path.join(os.path.expanduser("~"), "Documents", "T11_posicionador_saida")
    cfg["raiz_repo"] = AQUI
    for caminho in (CONFIG_LOCAL, CONFIG_DEV):
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                extra = json.load(f)
            params = dict(cfg["params"], **extra.pop("params", {}))
            cfg.update(extra)
            cfg["params"] = params
            cfg["config_usada"] = caminho
            break
    return cfg


def run(_context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    saida = None
    status = {"script": "T11_posicionador", "somente_leitura": True, "python": sys.version, "inicio": time.strftime("%Y-%m-%d %H:%M:%S")}
    cfgx = {"silencioso": False}
    try:
        cfgx = _configuracao()
        saida = cfgx["saida"]
        os.makedirs(saida, exist_ok=True)
        log = open(os.path.join(saida, "progresso.log"), "w", encoding="utf-8", buffering=1)

        def say(msg):
            log.write(f"{time.strftime('%H:%M:%S')} {msg}\n")

        _gravar(os.path.join(saida, "status.json"), dict(status, estado="iniciado"))
        raiz = cfgx["raiz_repo"]
        if not os.path.isdir(os.path.join(raiz, "python", "posicionador")):
            raise RuntimeError(f"nao achei python/posicionador em {raiz}: o pacote esta incompleto")
        for k in [k for k in sys.modules if k == "posicionador" or k.startswith("posicionador.")]:
            del sys.modules[k]                       # o Fusion mantem os modulos entre execucoes
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
        status.update(documento=doc, modo=cfgx["modo"], config_usada=cfgx.get("config_usada"))
        say(f"documento {doc}; modo {cfgx['modo']}; Python {sys.version.split()[0]}")

        t0 = time.perf_counter()
        geo, corpos = api.ler_geometria(design)
        say(f"CAD lido: {len(corpos)} corpos, {geo['n_ocorrencias']} ocorrencias ({time.perf_counter() - t0:.2f} s)")
        _gravar(os.path.join(saida, "geometria_lida.json"), geo)
        mapa = rc.carregar_mapa(cfgx["mapa_componentes"]) if cfgx.get("mapa_componentes") and os.path.exists(cfgx["mapa_componentes"]) else None
        cfg = pc.carregar(os.path.join(raiz, "data", "posicionador", "config_T11.json"))
        caminho_hp = os.path.join(raiz, cfgx["hardpoints"])
        orac = api.OraculoFusion(app, corpos)
        params = dict(cfgx["params"])
        ultimo = [0.0]

        def progresso(fase, i, n, melhor):
            agora = time.monotonic()
            if i == n or agora - ultimo[0] >= 5.0:
                ultimo[0] = agora
                say(f"{fase}: {i}/{n}; menor violacao ate aqui {melhor:.4g}; chamadas a API {orac.n_chamadas}")
                adsk.doEvents()                       # mantem a janela do Fusion viva durante a busca

        resumo = ""
        if cfgx["modo"] in ("medicao", "raios"):
            from posicionador.fusion import medicao as md
            prep = pl.preparar(geo, orac, cfg, caminho_hp, mapa, params.get("corte_m", 0.05))
            say(f"cena: {len(prep.fixos)} corpos; promovidos {[d.componente for d in prep.classificacao.promovidos]}")
            if cfgx["modo"] == "raios":
                out = md.raios_da_atuacao(orac, geo, prep)
            else:
                with open(os.path.join(raiz, "data", "posicionador", "origem_v20_script.json"), encoding="utf-8") as f:
                    x20 = json.load(f)["x_semente"]
                out = md.medir(app, prep, orac, cfg, x20, prep.v10, [f.id for f in prep.fixos], None,
                               n_seg=params.get("n_seg", 300), n_exato=params.get("n_exato", 60), n_pontos=params.get("n_pontos", 1000))
            _gravar(os.path.join(saida, cfgx["modo"] + ".json"), out)
            resumo = f"Modo {cfgx['modo']}: resultado em {cfgx['modo']}.json."
        else:
            d, res = pl.executar(geo, orac, cfg, caminho_hp, saida, params, mapa, progresso)
            status.update(n_viaveis=d["estatisticas"].get("n_viaveis"), tempo_s=d["tempo_s"])
            f1 = d.get("fase1") or {}
            resumo = (f"{len(res.candidatos)} candidato(s) viavel(is) em {d['estatisticas'].get('n_amostras')} amostras ({d['tempo_s']:.0f} s)."
                      + (f"\nNenhum viavel. {f1.get('motivo', '')[:300]}" if not res.candidatos else "")
                      + f"\nPromovidos a obstaculo: {d['obstaculos']['promovidos'] or 'nenhum'}.")
        status.update(estado="concluido", fim=time.strftime("%Y-%m-%d %H:%M:%S"), chamadas_api=orac.n_chamadas, erros_api=orac.n_erros)
        _gravar(os.path.join(saida, "status.json"), status)
        say("concluido")
        log.close()
        if not cfgx.get("silencioso"):
            ui.messageBox("T11_posicionador concluido (somente leitura; nada foi salvo).\n\n" + resumo + "\n\nSaidas em:\n" + saida + "\n(abra relatorio.md)")
    except Exception:  # noqa: BLE001
        status.update(estado="ERRO", erro=traceback.format_exc())
        try:
            _gravar(os.path.join(saida or AQUI, "status.json"), status)
        except Exception:  # noqa: BLE001
            pass
        app.log("T11_posicionador falhou:\n" + traceback.format_exc())
        ui.messageBox("T11_posicionador: erro (detalhe em " + os.path.join(saida or AQUI, "status.json") + "):\n" + traceback.format_exc()[-1500:])
