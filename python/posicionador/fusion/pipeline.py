"""
Pipeline do adaptador do Fusion (puro; sem `adsk`): da leitura do CAD ao resultado da busca.

    geo (leitura do CAD) → portão de identificação → regra de obstáculos → cena (FixoFusion por corpo) → hardpoints vivos
    → caixa de busca → `puro.busca.buscar`

O oráculo de distância é injetado (a API do Fusion em `api.OraculoFusion`; nos testes, um falso). Só biblioteca padrão.
"""
import csv
import json
import math
import os
import time
from dataclasses import dataclass, field

from posicionador import identificacao as idf
from posicionador import reconhecimento as rc
from posicionador.fusion import cena as fc
from posicionador.fusion import obstaculos as ob
from posicionador.puro import busca as bp
from posicionador.puro import dados as pdados
from posicionador.puro import varredura as pvr

HP_TOL_AVISO_MM = 0.5     # a mesma tolerância das esferas HP_ do documento de exportação (cad_step.HP_TOL_M)
CATEGORIAS_MOVEIS = ("RODA_FE", "RODA_FD", "BANDEJA_FE", "BANDEJA_FD", "DIR")


class ErroIdentificacao(RuntimeError):
    """O portão de identificação tem FALHA: o modelo não pode ser usado até resolver."""

    def __init__(self, res):
        self.res = res
        super().__init__("portão de identificação bloqueado: " + "; ".join(f"{a.codigo} {a.componente}: {a.mensagem}" for a in res.falhas))


@dataclass
class Preparo:
    res: object
    classificacao: object
    quadro: fc.Quadro
    fixos: list
    cena: object
    v10: dict
    hp_diferencas_mm: list
    contagem: fc.Contagem
    envelope_m: tuple
    avisos: list = field(default_factory=list)


def quadro_do_cad(geo, res):
    q = idf.referencial(geo, res.reconhecimento, [])
    if q is None:
        raise ErroIdentificacao(res)
    o, eixos = q
    return fc.Quadro(tuple(o), tuple(tuple(e) for e in eixos))


def hardpoints_vivos(geo, res, quadro, caminho_base):
    """({id: (xyz_m, componente)}, [(id, diferença mm)]): a base do CSV com os 9 pontos HP_FL lidos do CAD ao vivo (esferas
    HP_FL_<chave> → FL_<chave>, referencial do carro). Os pontos que o CAD não traz (SPINDLE_PT, CONTACT_PATCH) ficam como no CSV."""
    base = pdados.carregar_hardpoints(caminho_base)
    pts, difs = dict(base), []
    for nome, r in res.reconhecimento.items():
        if r.categoria != "HP":
            continue
        for occ in geo["topos"][nome]["ocorrencias"]:
            for c in occ["corpos"]:
                partes = c["nome"].split("_", 2)
                if "esfera" not in c or len(partes) < 3 or partes[1] != "FL":
                    continue
                chave = "FL_" + partes[2]
                p = quadro.para_carro_m(c["esfera"]["centro_mm"])
                comp = base[chave][1] if chave in base else "CHASSIS"
                if chave in base:
                    difs.append((chave, 1000.0 * math.dist(p, base[chave][0])))
                pts[chave] = (p, comp)
    return pts, difs


def preparar(geo, oraculo, cfg, caminho_hardpoints, mapa=None, corte_m=fc.CORTE_M):
    res = idf.verificar(geo, mapa)
    if not res.ok:
        raise ErroIdentificacao(res)
    quadro = quadro_do_cad(geo, res)
    cl = ob.classificar(res)
    contagem = fc.Contagem()
    fixos, avisos = [], []
    for nome in cl.obstaculos:
        for occ in geo["topos"][nome]["ocorrencias"]:
            for c in occ["corpos"]:
                if not c["isSolid"]:
                    avisos.append(f"corpo não sólido fora da cena: {occ['caminho']} / {c['nome']}")
                    continue
                lo, hi = quadro.caixa_carro_m(c["min_mm"], c["max_mm"])
                fixos.append(fc.FixoFusion(c["id"], f"{occ['caminho']} / {c['nome']}", lo, hi, quadro, oraculo, contagem, corte_m))
    if not fixos:
        raise ValueError("a cena não tem nenhum corpo sólido de obstáculo (CHASSI/FIXO): a busca não seria confiável")
    env = (tuple(min(f.lo[k] for f in fixos) for k in range(3)), tuple(max(f.hi[k] for f in fixos) for k in range(3)))
    v10, difs = hardpoints_vivos(geo, res, quadro, caminho_hardpoints)
    for chave, d in difs:
        if d > HP_TOL_AVISO_MM:
            avisos.append(f"hardpoint {chave}: o CAD vivo difere {d:.2f} mm do CSV {os.path.basename(caminho_hardpoints)} (vale o CAD)")
    moveis = sorted({r.categoria for r in res.reconhecimento.values() if r.categoria in CATEGORIAS_MOVEIS})
    nao = [f"peças móveis do CAD ({', '.join(moveis)}) não entram na varredura; o aro vem da configuração",
           "nós do chassi não identificados no Fusion: sorteio dos pivôs sem preferência por nós e critérios de proximidade ao nó zerados",
           f"folga aos fixos medida pela API do Fusion, saturada em {corte_m * 1e3:.0f} mm, com cilindro fino de "
           f"{fc.R_FINO_M * 1e3:.1f} mm sobre o eixo (conservadora em até esse valor)"]
    cena = pvr.cena_de(fixos, [], cfg, pecas_moveis=moveis, nao_modelado=nao)
    return Preparo(res, cl, quadro, fixos, cena, v10, difs, contagem, env, avisos)


def caixa_de_busca(cfg, envelope_m, caixa_m=None):
    """((mín[3], máx[3]), texto, origem). `caixa_m` (mín, máx) em m sobrepõe tudo. Senão: X do item `caixa_busca_pivo_m` e
    Y/Z nulos derivados do envelope das caixas dos corpos obstáculo, lado esquerdo (Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max]):
    HIPOTESE (decisão R8 da fase 1; lá o envelope vem de pontos de amostra dos primitivos, aqui das caixas dos corpos)."""
    if caixa_m is not None:
        lo, hi = [float(v) for v in caixa_m[0]], [float(v) for v in caixa_m[1]]
        return (tuple(lo), tuple(hi)), "dada na configuração da execução", "EXECUCAO"
    it = cfg.item("caixa_busca_pivo_m")
    lo, hi = list(it.valor["min_m"]), list(it.valor["max_m"])
    faltam = [i for i in range(3) if lo[i] is None or hi[i] is None]
    if 0 in faltam:
        raise ValueError("o X da caixa de busca do pivô tem de vir da configuração ou da execução")
    emin, emax = envelope_m
    deriv = {1: (0.0, emax[1]), 2: (max(0.0, emin[2]), emax[2])}
    for i in faltam:
        lo[i], hi[i] = deriv[i]
    texto = (f"HIPOTESE: caixa derivada do envelope das caixas dos corpos obstáculo (decisão R8). X do item `caixa_busca_pivo_m` "
             f"({it.origem}); {', '.join('XYZ'[i] for i in faltam)} do envelope Y [{emin[1]:.4f}; {emax[1]:.4f}] m, Z [{emin[2]:.4f}; {emax[2]:.4f}] m, "
             "lado esquerdo")
    return (tuple(lo), tuple(hi)), texto, "HIPOTESE"


def buscar(prep, cfg, caixa, **kw):
    """Chama `puro.busca.buscar` com os hardpoints vivos e a cena do Fusion."""
    return bp.buscar(prep.v10, prep.cena, cfg, caixa, **kw)


# ---------------------------------------------------------------------------------------------------------- saídas
def _restricao_dict(r):
    return {"nome": r.nome, "estado": r.estado, "valor": r.valor if not isinstance(r.valor, tuple) else list(r.valor),
            "limite": r.limite if not isinstance(r.limite, tuple) else list(r.limite), "folga": r.folga, "origem": r.origem,
            "motivo": r.motivo}


def candidato_dict(c):
    return {"origem": c.origem, "violacao": None if not math.isfinite(c.violacao) else c.violacao, "veredito": c.avaliacao.veredito,
            "motivo": c.avaliacao.motivo, "pivo_m": list(c.variaveis.pivo_m) if c.variaveis else None,
            "r2_m": c.construcao.r2_m, "restricoes": [_restricao_dict(r) for r in c.avaliacao.restricoes]}


def resultado_dict(prep, res, caixa, origem_caixa, parametros, tempo_s, oraculo_stats):
    f1 = res.fase1
    return {"rotulo": "VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics; adaptador do Fusion, fase 2 (EDR-077)",
            "parametros": parametros, "tempo_s": tempo_s, "estatisticas": res.estatisticas,
            "caixa_busca_pivo_m": {"min_m": list(caixa[0]), "max_m": list(caixa[1]), "origem": origem_caixa},
            "obstaculos": {"promovidos": [d.componente for d in prep.classificacao.promovidos],
                           "mistos": [d.componente for d in prep.classificacao.mistos],
                           "decisoes": [vars(d) for d in prep.classificacao.decisoes], "n_corpos_na_cena": len(prep.fixos)},
            "hp_diferencas_mm": [{"id": k, "mm": v} for k, v in prep.hp_diferencas_mm], "avisos": prep.avisos,
            "nao_modelado": prep.cena.nao_modelado, "oraculo": oraculo_stats,
            "contagem": vars(prep.contagem), "a_confirmar": {n: cfg_fonte for n, cfg_fonte in parametros.get("a_confirmar", {}).items()},
            "candidatos": [candidato_dict(c) for c in res.candidatos],
            "fase1": None if f1 is None else {"motivo": f1.motivo, "violacoes": f1.violacoes, "falhas": f1.falhas,
                                              "melhor": None if f1.melhor is None else candidato_dict(f1.melhor),
                                              "conflitos": [list(t) for t in f1.conflitos]}}


def relatorio_md(d):
    L = ["# Posicionador no Fusion (fase 2): resultado", "", f"_{d['rotulo']}_", "",
         f"Tempo: {d['tempo_s']:.1f} s; amostras {d['estatisticas'].get('n_amostras')}, viáveis {d['estatisticas'].get('n_viaveis')}.", "",
         "## Obstáculos", f"- Corpos sólidos na cena: {d['obstaculos']['n_corpos_na_cena']}.",
         f"- Promovidos pela regra (dianteiro fora do cálculo): {d['obstaculos']['promovidos'] or 'nenhum'}.",
         f"- Mistos (decisão pendente, não promovidos): {d['obstaculos']['mistos'] or 'nenhum'}."]
    for x in d["obstaculos"]["decisoes"]:
        if x["destino"] in ("ignorado", "misto", "promovido"):
            L.append(f"  - {x['destino']}: {x['componente']} ({x['n_corpos']} corpos): {x['motivo']}")
    L += ["", "## Avisos"] + [f"- {a}" for a in d["avisos"]] + ["", "## Não modelado"] + [f"- {t}" for t in d["nao_modelado"]]
    L += ["", f"## Custo da API: {d['oraculo']}", f"Contagem: {d['contagem']}", "", "## Resultado"]
    if d["candidatos"]:
        for k, c in enumerate(d["candidatos"], 1):
            L.append(f"- candidato {k:02d}: {c['veredito']} pivô {c['pivo_m']} r2 {c['r2_m']} ({c['motivo']})")
    elif d["fase1"]:
        L.append(f"Nenhum candidato viável. {d['fase1']['motivo']}")
        L.append(f"Violações por restrição (fração das amostras): {d['fase1']['violacoes']}")
    return "\n".join(L) + "\n"


def gravar(pasta, d, res):
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2, default=str)
    with open(os.path.join(pasta, "relatorio.md"), "w", encoding="utf-8") as f:
        f.write(relatorio_md(d))
    for k, c in enumerate(res.candidatos, 1):
        with open(os.path.join(pasta, f"candidato_{k:02d}.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Point_ID", "X_m", "Y_m", "Z_m", "Component", "Status"])
            for pid, (xyz, comp) in sorted(c.construcao.pontos.items()):
                w.writerow([pid, f"{xyz[0]:.9f}", f"{xyz[1]:.9f}", f"{xyz[2]:.9f}", comp, "PROVISIONAL"])


def executar(geo, oraculo, cfg, caminho_hardpoints, pasta_saida, params, mapa=None, progresso=None):
    """Roda tudo e grava `resultado.json`, `relatorio.md` e um CSV por candidato. `params`: n_amostras, n_refinos, semente,
    passo_m, max_aval_refino, n_finalistas, corte_m, caixa_m (opcional). Devolve (dict do resultado, ResultadoBusca)."""
    t0 = time.perf_counter()
    prep = preparar(geo, oraculo, cfg, caminho_hardpoints, mapa, params.get("corte_m", fc.CORTE_M))
    caixa, texto_caixa, origem_caixa = caixa_de_busca(cfg, prep.envelope_m, params.get("caixa_m"))
    kw = {k: params[k] for k in ("n_amostras", "n_refinos", "semente", "passo_m", "max_aval_refino", "n_finalistas") if k in params}
    res = buscar(prep, cfg, caixa, progresso=progresso, **kw)
    p = dict(params, caixa_texto=texto_caixa, a_confirmar={n: cfg.item(n).fonte for n in cfg.a_confirmar()})
    stats = {"n_chamadas": oraculo.n_chamadas, "n_erros": oraculo.n_erros, "tempo_s": oraculo.tempo_s, "ultimo_erro": oraculo.ultimo_erro}
    d = resultado_dict(prep, res, caixa, origem_caixa, p, time.perf_counter() - t0, stats)
    gravar(pasta_saida, d, res)
    return d, res
