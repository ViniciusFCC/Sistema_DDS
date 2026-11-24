"""
Busca de candidatos com diagnóstico (Fase I) em Python puro: porte de `posicionador.busca` (variáveis, violação normalizada,
ordem dos viáveis, refino e Fase I estão descritos na docstring de lá; o desenho é o mesmo).

Diferenças deliberadas em relação ao original (numpy/scipy):
- o gerador é `random.Random(semente)`: a mesma semente NÃO dá as mesmas amostras do original (numpy PCG64). A equivalência é
  testada por componente (violação, objetivo, ordem, faixas, mapa) e por veredito de candidatos dados, não por sorteio;
- o refino usa `otimizacao.nelder_mead` (mesmo algoritmo do scipy);
- o mapa de espaço livre vem de `puro.espaco_livre` (folga saturada em `corte_m`).
"""
import bisect
import itertools
import math
import random
import time
from dataclasses import dataclass, field

from posicionador.puro import espaco_livre as el
from posicionador.puro import mecanismo as mec
from posicionador.puro import varredura as vr
from posicionador.puro.otimizacao import nelder_mead

N_RAPIDO = 11
ESCALA_NO_M = 0.05
ESCALA_LIMITE_NULO = 1e-3
F_FALHA = 1e6
EPS_PHI = 1e-6
SIMPLEX_FRAC = 0.10
FALHAS = (("construção", "construção:"), ("cinemática sem solução", "cinemática sem solução"),
          ("avaliação sem resultado", "avaliação sem resultado"))
NOME_OLHAL = "X do olhal no chassi"
VIAVEIS = ("VIAVEL", "CONDICIONAL")


@dataclass
class Candidato:
    variaveis: mec.Variaveis
    construcao: mec.Construcao
    avaliacao: vr.Avaliacao
    violacao: float = math.inf
    origem: str = "amostra"


@dataclass
class Diagnostico:
    melhor: "Candidato | None"
    conflitos: list
    violacoes: dict = field(default_factory=dict)
    falhas: dict = field(default_factory=dict)
    n_amostras: int = 0
    n_com_resultado: int = 0
    motivo: str = ""


@dataclass
class ResultadoBusca:
    candidatos: list
    fase1: "Diagnostico | None"
    mapa: "el.Mapa | None" = None
    estatisticas: dict = field(default_factory=dict)


def tipo_falha(av):
    if av.restricoes and not (len(av.restricoes) == 1 and av.restricoes[0].valor is None
                              and av.restricoes[0].nome in vr.FONTES_FALHA):
        return None
    m = av.motivo or ""
    return next((t for t, prefixo in FALHAS if m.startswith(prefixo)), "avaliação sem resultado")


def violacao_restricao(r):
    if r.estado != "VIOLADA":
        return 0.0
    if r.folga is None:
        return 1.0
    lim = r.limite
    if isinstance(lim, (tuple, list)):
        lo, hi = float(lim[0]), float(lim[1])
        try:
            lim = lo if float(r.valor) < lo else hi
        except (TypeError, ValueError):
            lim = max(abs(lo), abs(hi))
    try:
        esc = abs(float(lim))
    except (TypeError, ValueError):
        esc = 0.0
    esc = esc if esc > 0.0 else ESCALA_LIMITE_NULO
    return max(0.0, -float(r.folga)) / esc


def violacao(av):
    if tipo_falha(av) is not None:
        return math.inf
    return max((violacao_restricao(r) for r in av.restricoes), default=0.0)


def chave_ordem(av):
    r = av.restricao("variação de MR")
    var = float(r.valor) if r is not None and r.valor is not None else math.inf
    dn = sum(float(av.dist_no_m.get(k) or 0.0) for k in ("pivo", "olhal"))
    fo = av.curvas.get("angulo_fora_do_plano_rad")
    fo = float(max(fo)) if fo is not None and len(fo) else 0.0
    return var, dn, fo


def ordenar_viaveis(cands, n_max=None):
    out = sorted(cands, key=lambda c: (c.avaliacao.veredito != "VIAVEL", *chave_ordem(c.avaliacao)))
    return out if n_max is None else out[:max(0, int(n_max))]


def _objetivo(av):
    v = violacao(av)
    if not math.isfinite(v):
        return F_FALHA
    if v > 0.0:
        return v
    var, dn, fo = chave_ordem(av)
    return -1.0 + var / (1.0 + var) + 1e-3 * dn / (1.0 + dn) + 1e-6 * fo / (1.0 + fo)


def _com_olhal(av, construcao, cfg):
    if tipo_falha(av) is not None or construcao.pontos is None:
        return av
    it = cfg.item("x_max_olhal_m")
    if it.valor is None:
        r = vr.Restricao(NOME_OLHAL, None, None, None, "NAO_VERIFICAVEL", it.origem, f"x_max_olhal_m ({it.origem}): "
                         f"{it.fonte}", "X máximo do olhal a confirmar")
    else:
        cx = float(construcao.pontos["FL_SPRING_CHASSIS"][0][0])
        xm = float(it.valor)
        r = vr.Restricao(NOME_OLHAL, cx, xm, xm - cx, "OK" if xm - cx >= 0.0 else "VIOLADA", it.origem,
                         f"x_max_olhal_m ({it.origem}): {it.fonte}", "X do olhal do amortecedor no chassi (estático)")
    av.restricoes = [q for q in av.restricoes if q.nome != NOME_OLHAL] + [r]
    av.veredito, av.motivo = _veredito_mantido(av, r)
    return av


def avaliar_convergido(construcao, cena, cfg, n0=25):
    return _com_olhal(vr.avaliar_convergido(construcao, cena, cfg, n0), construcao, cfg)


def _veredito_mantido(av, r):
    if r.estado == "VIOLADA":
        if av.veredito == "INVIAVEL":
            return av.veredito, f"{av.motivo}; {NOME_OLHAL} violada"
        return "INVIAVEL", f"restrições violadas: {NOME_OLHAL}"
    if r.estado == "NAO_VERIFICAVEL" and av.veredito == "VIAVEL":
        return "CONDICIONAL", f"não verificáveis: {NOME_OLHAL}"
    return av.veredito, av.motivo


@dataclass(frozen=True)
class Faixas:
    lo: tuple       # [px, py, pz, u, ψ, r1, φB] (+ δ)
    hi: tuple
    amax_rad: float


def faixas(cfg, caixa_m, delta_max_rad=0.0):
    lo_c, hi_c = (tuple(float(v) for v in c) for c in caixa_m)
    bmin, bmax = float(cfg.valor("braco_min_m")), float(cfg.valor("braco_max_m"))
    amax = float(cfg.valor("amort_ang_max_rad"))
    lo = lo_c + (0.0, -math.pi, bmin, EPS_PHI)
    hi = hi_c + (1.0, math.pi, bmax, math.pi - EPS_PHI)
    if delta_max_rad > 0.0:
        lo, hi = lo + (-delta_max_rad,), hi + (delta_max_rad,)
    return Faixas(lo, hi, amax)


def _recortar(x, fx):
    return [min(max(float(v), l), h) for v, l, h in zip(x, fx.lo, fx.hi)]


def variaveis_de(x, fx):
    x = _recortar(x, fx)
    cos_t = 1.0 - x[3] * (1.0 - math.cos(fx.amax_rad))
    sin_t = math.sqrt(max(0.0, 1.0 - cos_t * cos_t))
    ud = (cos_t, sin_t * math.cos(x[4]), sin_t * math.sin(x[4]))
    az = math.atan2(ud[1], ud[0])
    elv = math.asin(min(max(ud[2], -1.0), 1.0))
    return mec.Variaveis(pivo_m=tuple(x[0:3]), az_rad=az, el_rad=elv, r1_m=x[5], phi_b_rad=x[6],
                         delta_rad=x[7] if len(x) > 7 else 0.0)


def _lhs(rng, n, d):
    u = [[0.0] * d for _ in range(n)]
    for j in range(d):
        perm = list(range(n))
        rng.shuffle(perm)
        for i in range(n):
            u[i][j] = (perm[i] + rng.random()) / n
    return u


def _sortear(rng, livres, w, n, fx):
    """n amostras: pivôs entre os pontos livres (pesos w) e as demais variáveis por hipercubo latino."""
    acum = list(itertools.accumulate(w))
    tot = acum[-1]
    idx = [min(bisect.bisect_right(acum, rng.random() * tot), len(livres) - 1) for _ in range(n)]
    u = _lhs(rng, n, len(fx.lo) - 3)
    return [list(livres[i]) + [fx.lo[3 + j] + u[k][j] * (fx.hi[3 + j] - fx.lo[3 + j]) for j in range(len(fx.lo) - 3)]
            for k, i in enumerate(idx)]


def _avaliar_x(v10, x, fx, cena, cfg, n_rapido, origem):
    v = variaveis_de(x, fx)
    c = mec.construir(v10, v, cfg)
    av = _com_olhal(vr.avaliar(c, cena, cfg, n_rapido), c, cfg)
    return Candidato(v, c, av, violacao(av), origem)


def _refinar(v10, cand, x0, fx, cena, cfg, n_rapido, max_aval):
    melhor = [cand]

    def f(x):
        xc = _recortar(x, fx)
        c = _avaliar_x(v10, xc, fx, cena, cfg, n_rapido, "refino")
        if _objetivo(c.avaliacao) < _objetivo(melhor[0].avaliacao):
            melhor[0] = c
        return _objetivo(c.avaliacao)

    passo = [SIMPLEX_FRAC * (h - l) for l, h in zip(fx.lo, fx.hi)]
    passo = [p if p > 0.0 else 1e-3 for p in passo]
    simplex = [list(x0)]
    for j in range(len(x0)):
        xj = list(x0)
        xj[j] = x0[j] + passo[j] if x0[j] + passo[j] <= fx.hi[j] else x0[j] - passo[j]
        simplex.append(xj)
    nelder_mead(f, list(x0), simplex, int(max_aval), xatol=1e-6, fatol=1e-9)
    return melhor[0]


def _x_de(v, fx):
    ud = mec.direcao_amortecedor(v.az_rad, v.el_rad)
    cos_t = min(max(ud[0], -1.0), 1.0)
    den = 1.0 - math.cos(fx.amax_rad)
    u = (1.0 - cos_t) / den if den > 0.0 else 0.0
    psi = math.atan2(ud[2], ud[1])
    x = list(v.pivo_m) + [u, psi, v.r1_m, v.phi_b_rad]
    return x + [v.delta_rad] if len(fx.lo) > 7 else x


def _coocorrencia(cands, n_conflitos):
    com = [c for c in cands if tipo_falha(c.avaliacao) is None]
    n = len(com)
    cont, pares = {}, {}
    for c in com:
        vio = sorted({r.nome for r in c.avaliacao.restricoes if r.estado == "VIOLADA"})
        for nome in vio:
            cont[nome] = cont.get(nome, 0) + 1
        for a, b in itertools.combinations(vio, 2):
            pares[(a, b)] = pares.get((a, b), 0) + 1
    conflitos = sorted(((a, b, k / n) for (a, b), k in pares.items()), key=lambda t: (-t[2], t[0], t[1]))
    violacoes = {k: cont[k] / n for k in sorted(cont, key=lambda k: (-cont[k], k))} if n else {}
    return conflitos[:n_conflitos], violacoes, n


def _falhas(cands):
    out = {t: 0 for t, _ in FALHAS}
    for c in cands:
        t = tipo_falha(c.avaliacao)
        if t is not None:
            out[t] += 1
    return out


def _caixa_explicita(caixa_m):
    try:
        lo, hi = caixa_m
        vals = list(lo) + list(hi)
    except (TypeError, ValueError) as e:
        raise ValueError(f"caixa_m deve ser (mín[3], máx[3]) em m; veio {caixa_m!r}") from e
    if len(vals) != 6 or any(v is None for v in vals):
        raise ValueError(f"caixa_m com eixo sem valor (None): {caixa_m!r}. A caixa de busca do pivô tem de ser dada inteira")
    return tuple(float(v) for v in lo), tuple(float(v) for v in hi)


def buscar(v10, cena, cfg, caixa_m, n_amostras=2000, n_refinos=20, semente=0, *, passo_m=0.01, n_rapido=N_RAPIDO,
           max_aval_refino=60, n_finalistas=20, escala_no_m=ESCALA_NO_M, n_conflitos=10, progresso=None, delta_max_rad=0.0):
    """Busca candidatos viáveis. `v10` = {id: (xyz, componente)}. Levanta ValueError se `caixa_m` tem None.
    Sem a caixa dinâmica nem a margem como objetivo do original (opcionais lá; não entram no núcleo do Fusion)."""
    t0 = time.perf_counter()
    caixa = _caixa_explicita(caixa_m)
    fx = faixas(cfg, caixa, delta_max_rad)
    m = el.mapa(cena, caixa, passo_m=passo_m, raio_m=0.0)
    r_pivo = float(cfg.valor("r_pivo_m"))
    livres = m.livres(r_pivo)
    est = {"n_pontos_grade": len(m.folga_m), "n_pontos_livres": len(livres), "n_amostras": int(n_amostras)}
    if not livres or n_amostras <= 0:
        motivo = (f"nenhum ponto da grade com folga ≥ r_pivo_m = {r_pivo * 1e3:.1f} mm aos fixos na caixa"
                  if not livres else "nenhuma amostra pedida")
        est["tempo_s"] = time.perf_counter() - t0
        return ResultadoBusca([], Diagnostico(None, [], {}, {}, 0, 0, motivo), m, est)

    rng = random.Random(semente)
    d = m.dist_no_livres(r_pivo)
    w = [1.0] * len(livres) if not any(math.isfinite(v) for v in d) else [1.0 / (1.0 + (v if math.isfinite(v) else math.inf)
                                                                              / float(escala_no_m)) for v in d]
    n_amostras = int(n_amostras)
    X = _sortear(rng, livres, w, n_amostras, fx)
    amostras, melhor_v = [], math.inf
    for x in X:
        amostras.append(_avaliar_x(v10, x, fx, cena, cfg, n_rapido, "amostra"))
        melhor_v = min(melhor_v, amostras[-1].violacao)
        if progresso is not None:
            progresso("amostras", len(amostras), n_amostras, melhor_v)
    est["falhas"] = _falhas(amostras)

    ordem = sorted((i for i, c in enumerate(amostras) if math.isfinite(c.violacao)),
                   key=lambda i: (amostras[i].violacao, chave_ordem(amostras[i].avaliacao), i))
    refinos = []
    sel = ordem[:max(0, int(n_refinos))]
    for k, i in enumerate(sel, start=1):
        refinos.append(_refinar(v10, amostras[i], list(X[i]), fx, cena, cfg, n_rapido, max_aval_refino))
        melhor_v = min(melhor_v, refinos[-1].violacao)
        if progresso is not None:
            progresso("refinos", k, len(sel), melhor_v)
    est["n_refinos"] = len(refinos)

    todos, vistos = [], set()
    for c in amostras + refinos:
        k = tuple(_x_de(c.variaveis, fx))
        if k not in vistos:
            vistos.add(k)
            todos.append(c)
    rapidos = ordenar_viaveis(c for c in todos if c.avaliacao.veredito in VIAVEIS)
    est["n_viaveis_rapidos"] = len(rapidos)
    finais = []
    for c in ordenar_viaveis(rapidos, n_max=n_finalistas):
        av = _com_olhal(vr.avaliar_convergido(c.construcao, cena, cfg), c.construcao, cfg)
        if av.veredito in VIAVEIS:
            finais.append(Candidato(c.variaveis, c.construcao, av, violacao(av), c.origem))
    finais = ordenar_viaveis(finais)
    est["n_finalistas"] = min(len(rapidos), max(0, int(n_finalistas)))
    est["n_viaveis"] = len(finais)

    fase1 = None
    if not finais:
        conflitos, violacoes, n_com = _coocorrencia(amostras, n_conflitos)
        finitos = [c for c in todos if math.isfinite(c.violacao)]
        melhor = None
        if finitos:
            b = min(finitos, key=lambda c: (c.violacao, chave_ordem(c.avaliacao)))
            av = _com_olhal(vr.avaliar_convergido(b.construcao, cena, cfg), b.construcao, cfg)
            melhor = Candidato(b.variaveis, b.construcao, av, violacao(av), b.origem)
            motivo = (f"nenhum candidato viável em {len(amostras)} amostras e {len(refinos)} refinos; menor violação "
                      f"máxima normalizada (avaliação rápida, n = {n_rapido}) = {b.violacao:.4g}; convergida: "
                      f"{av.veredito} ({av.motivo})")
            if rapidos:
                motivo = (f"{len(rapidos)} candidatos foram VIAVEL ou CONDICIONAL na avaliação rápida (n = {n_rapido}), "
                          f"mas nenhum dos {est['n_finalistas']} finalistas reavaliados por avaliar_convergido continuou "
                          f"VIAVEL ou CONDICIONAL; {motivo}")
        else:
            motivo = f"nenhuma das {len(amostras)} amostras teve resultado: falhas {est['falhas']}"
        fase1 = Diagnostico(melhor, conflitos, violacoes, est["falhas"], len(amostras), n_com, motivo)
    est["tempo_s"] = time.perf_counter() - t0
    return ResultadoBusca(finais, fase1, m, est)
