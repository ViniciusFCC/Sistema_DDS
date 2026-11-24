"""
Busca de candidatos com diagnóstico (Fase I) do posicionador (EDR-076, spec §5 itens 5 e 6; TC-POS-070, 071 e 073).

Variáveis (as 7 contínuas de `mecanismo.Variaveis`; o lado da tangente do push rod ao rocker, `mecanismo.LADO_ROCKER`, é o
único parâmetro discreto e fica fixo):
- pivô do rocker: pontos de `espaco_livre.Mapa.livres(r_pivo_m)` dentro de `caixa_m` (mapa com raio 0 e o raio do pivô
  pedido em `livres`), sorteados com peso w = 1 / (1 + d / escala_no_m), d = distância do ponto ao nó do chassi mais
  próximo (preferência U3; escala_no_m = 0,05 m por padrão, parâmetro da busca, não dado do carro). Sem nós na cena, o
  peso é uniforme;
- direção do amortecedor: no cone de semiângulo `amort_ang_max_rad` em volta de +X. Coordenadas do cone: θ = ângulo a +X
  e ψ = giro em volta de X, ud = (cos θ, sin θ·cos ψ, sin θ·sin ψ); u = (1 − cos θ)/(1 − cos θ_max) ∈ [0, 1] (uniforme em
  u = uniforme no ângulo sólido) e ψ ∈ [−π, π]; az = atan2(ud_y, ud_x), el = asin(ud_z);
- r1 ∈ [braco_min_m, braco_max_m];
- φB ∈ (0, π): a equipe não declara limite para o ângulo entre os braços do rocker, então a faixa é a geométrica toda.
As 4 últimas (u, ψ, r1, φB) saem de um hipercubo latino (LHS) com `n_amostras` pontos.

Avaliação rápida: `mecanismo.construir` (r2 pelo MR-alvo) + `varredura.avaliar(n = n_rapido = 11)`.

Violação máxima normalizada de uma avaliação (`violacao`): o máximo, nas restrições VIOLADA, de max(0, −folga)/escala, com
escala = |limite| se o limite é não nulo (limite (mín, máx): o lado que foi violado) e 1 mm se o limite é nulo (as
restrições de limite nulo são folgas em m). Restrição VIOLADA sem folga numérica (gabarito T.1.2) conta 1. OK e
NAO_VERIFICAVEL contam 0. Avaliação que falhou (construção, cinemática sem solução, avaliação sem resultado: sem
restrições medidas) tem violação +inf e nunca é refinada; essas falhas são contadas à parte no diagnóstico.

Restrição da busca: `x_max_olhal_m` (X máximo do olhal do amortecedor no chassi) não está em `varredura.avaliar`; a busca a
acrescenta a cada avaliação com resultado, como "X do olhal no chassi" (≤ x_max_olhal_m), e o veredito passa a INVIAVEL
se ela é violada.

Refino: as `n_refinos` amostras de menor violação finita (desempate pela ordem dos viáveis) partem
`scipy.optimize.minimize(method="Nelder-Mead")` sobre as 7 variáveis contínuas (pivô, u, ψ, r1, φB), com no máximo
`max_aval_refino` avaliações, simplex inicial de 10 % de cada faixa e as variáveis recortadas às faixas da amostragem
(o pivô à caixa; o refino pode sair do espaço livre do mapa, e a folga aos fixos é conferida pela avaliação).
Objetivo: f = violação máxima normalizada se > 0; avaliação que falhou: f = 1e6; violação 0: f = −1 + q, com
q = var/(1 + var) + 1e-3·dn/(1 + dn) + 1e-6·fo/(1 + fo) ∈ [0, 1), var = variação de MR, dn = distância do pivô ao nó +
distância do olhal ao nó [m] (0 sem nós), fo = ângulo máximo do push rod fora do plano do rocker [rad]. Os pesos 1, 1e-3
e 1e-6 aproximam a ordem lexicográfica dos viáveis (abaixo); são parâmetros do refino, não de engenharia. O melhor
ponto avaliado em cada refino vira candidato.

Viáveis: os candidatos (amostras e refinos) com veredito rápido VIAVEL ou CONDICIONAL, na ordem abaixo, até
`n_finalistas`, são reavaliados por `varredura.avaliar_convergido` (n0 = 25); só os que continuam VIAVEL ou CONDICIONAL
são devolvidos, com a avaliação convergida. Ordem (`ordenar_viaveis`, na lista dos rápidos, no corte dos finalistas e na
lista final): VIAVEL sempre antes de CONDICIONAL; dentro do mesmo veredito, variação de MR, depois (distância do pivô ao
nó + distância do olhal ao nó), depois ângulo máximo fora do plano.

Progresso: `progresso(fase, i, n, melhor_violacao)` (opcional) é chamado depois de cada amostra (fase "amostras") e de
cada refino (fase "refinos"); só informa, não muda o resultado.

Fase I (sem viável): `Diagnostico` com o candidato de menor violação máxima (reavaliado por `avaliar_convergido`; se houve
viáveis rápidos e nenhum finalista convergiu viável, o motivo diz isso), os pares
de restrições que mais vezes ficam VIOLADA juntas nas amostras (fração das amostras com resultado), a fração de cada
restrição violada e a contagem das falhas por tipo.
"""
import itertools
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize

from posicionador import espaco_livre as el
from posicionador import mecanismo as mec
from posicionador import varredura as vr

N_RAPIDO = 11
ESCALA_NO_M = 0.05        # escala da preferência por nó no sorteio do pivô (parâmetro da busca)
ESCALA_LIMITE_NULO = 1e-3  # 1 mm: escala da violação das restrições de limite nulo (folgas em m)
F_FALHA = 1e6             # objetivo do refino para avaliação sem resultado
EPS_PHI = 1e-6            # φB recortado a [EPS_PHI, π − EPS_PHI] no refino (numérico)
SIMPLEX_FRAC = 0.10       # simplex inicial do Nelder-Mead: 10 % de cada faixa
FALHAS = (("construção", "construção:"), ("cinemática sem solução", "cinemática sem solução"),
          ("avaliação sem resultado", "avaliação sem resultado"))
NOME_OLHAL = "X do olhal no chassi"
VIAVEIS = ("VIAVEL", "CONDICIONAL")


@dataclass
class Candidato:
    variaveis: mec.Variaveis
    construcao: mec.Construcao
    avaliacao: vr.Avaliacao
    violacao: float = float("inf")   # violação máxima normalizada da avaliação guardada
    origem: str = "amostra"          # "amostra" | "refino"


@dataclass
class Diagnostico:
    melhor: Candidato | None
    conflitos: list                  # (restrição, restrição, fração das amostras com resultado em que as duas violam)
    violacoes: dict = field(default_factory=dict)   # restrição -> fração das amostras com resultado em que viola
    falhas: dict = field(default_factory=dict)      # tipo de falha -> número de amostras
    n_amostras: int = 0
    n_com_resultado: int = 0
    motivo: str = ""


@dataclass
class ResultadoBusca:
    candidatos: list                 # Candidato viáveis (VIAVEL/CONDICIONAL convergidos), em ordem
    fase1: Diagnostico | None        # preenchido quando não há viável
    mapa: el.Mapa | None = None
    estatisticas: dict = field(default_factory=dict)


# ------------------------------------------------------------------ violação e ordem
def tipo_falha(av):
    """Tipo da falha ("construção", "cinemática sem solução", "avaliação sem resultado") ou None se há resultado."""
    if av.restricoes and not (len(av.restricoes) == 1 and av.restricoes[0].valor is None
                              and av.restricoes[0].nome in vr.FONTES_FALHA):
        return None
    m = av.motivo or ""
    return next((t for t, prefixo in FALHAS if m.startswith(prefixo)), "avaliação sem resultado")


def violacao_restricao(r):
    """max(0, −folga)/escala (ver o docstring do módulo); 0 se não VIOLADA."""
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
    """Violação máxima normalizada da avaliação; +inf se ela falhou."""
    if tipo_falha(av) is not None:
        return float("inf")
    return max((violacao_restricao(r) for r in av.restricoes), default=0.0)


def chave_ordem(av):
    """(variação de MR, distância do pivô ao nó + do olhal ao nó, ângulo máximo fora do plano); None vira 0."""
    r = av.restricao("variação de MR")
    var = float(r.valor) if r is not None and r.valor is not None else float("inf")
    dn = sum(float(av.dist_no_m.get(k) or 0.0) for k in ("pivo", "olhal"))
    fo = av.curvas.get("angulo_fora_do_plano_rad")
    fo = float(np.max(fo)) if fo is not None and len(fo) else 0.0
    return var, dn, fo


def ordenar_viaveis(cands, n_max=None):
    """Candidatos em ordem: VIAVEL antes de CONDICIONAL, depois `chave_ordem`; com `n_max`, só os n_max primeiros."""
    if OTIMIZAR_MARGEM:       # com a margem como objetivo: certificadas antes das indeterminadas, depois a maior margem
        out = sorted(cands, key=lambda c: (c.avaliacao.veredito != "VIAVEL", bool(c.avaliacao.indeterminadas),
                                           -margem_normalizada(c.avaliacao), *chave_ordem(c.avaliacao)))
        return out if n_max is None else out[:max(0, int(n_max))]
    out = sorted(cands, key=lambda c: (c.avaliacao.veredito != "VIAVEL", *chave_ordem(c.avaliacao)))
    return out if n_max is None else out[:max(0, int(n_max))]


SEM_MARGEM = ("MR(0)", "comprimento do amortecedor (máximo)")   # folga fixada pela construção (r2 e C resolvidos): não é margem de busca


def margem_normalizada(av):
    """Menor folga normalizada (folga/|limite|, a mesma escala da violação) entre as restrições OK com valor, sem as fixadas pela
    construção; +inf se não houver nenhuma. É a "margem" que a busca maximiza: sem exigência nova, só objetivo."""
    m = float("inf")
    for r in av.restricoes:
        if r.estado != "OK" or r.folga is None or r.nome in SEM_MARGEM:
            continue
        lim = r.limite
        if isinstance(lim, (tuple, list)):
            lim = lim[0] if abs(float(r.valor) - float(lim[0])) <= abs(float(r.valor) - float(lim[1])) else lim[1]
        try:
            esc = abs(float(lim))
        except (TypeError, ValueError):
            esc = 0.0
        m = min(m, float(r.folga) / (esc if esc > 0.0 else ESCALA_LIMITE_NULO))
    return m


OTIMIZAR_MARGEM = False     # buscar(..., otimizar_margem=True) liga; o padrão da biblioteca é o comportamento anterior


def _objetivo(av):
    v = violacao(av)
    if not np.isfinite(v):
        return F_FALHA
    if v > 0.0:
        return v
    if OTIMIZAR_MARGEM:
        m = margem_normalizada(av)
        var, _, _ = chave_ordem(av)
        return -(min(m, 1.0) if np.isfinite(m) else 0.0) + 1e-3 * var / (1.0 + var)
    var, dn, fo = chave_ordem(av)
    return -1.0 + var / (1.0 + var) + 1e-3 * dn / (1.0 + dn) + 1e-6 * fo / (1.0 + fo)


# ------------------------------------------------------------------ restrição da busca (olhal)
def _com_olhal(av, construcao, cfg):
    """Acrescenta a restrição X do olhal no chassi ≤ x_max_olhal_m (só em avaliação com resultado)."""
    if tipo_falha(av) is not None or construcao.hardpoints is None:
        return av
    it = cfg.item("x_max_olhal_m")
    if it.valor is None:
        r = vr.Restricao(NOME_OLHAL, None, None, None, "NAO_VERIFICAVEL", it.origem, f"x_max_olhal_m ({it.origem}): "
                         f"{it.fonte}", "X máximo do olhal a confirmar")
    else:
        cx = float(construcao.hardpoints.points["FL_SPRING_CHASSIS"].xyz[0])
        xm = float(it.valor)
        r = vr.Restricao(NOME_OLHAL, cx, xm, xm - cx, "OK" if xm - cx >= 0.0 else "VIOLADA", it.origem,
                         f"x_max_olhal_m ({it.origem}): {it.fonte}", "X do olhal do amortecedor no chassi (estático)")
    av.restricoes = [q for q in av.restricoes if q.nome != NOME_OLHAL] + [r]
    av.veredito, av.motivo = _veredito_mantido(av, r)
    return av


def avaliar_convergido(construcao, cena, cfg, n0=25):
    """`varredura.avaliar_convergido` com a restrição da busca (X do olhal no chassi): a mesma avaliação dos finalistas,
    para um conjunto dado de fora da busca (ex.: a v20)."""
    return _com_olhal(vr.avaliar_convergido(construcao, cena, cfg, n0), construcao, cfg)


def _veredito_mantido(av, r):
    """Veredito com a restrição do olhal: VIOLADA rebaixa a INVIAVEL; NAO_VERIFICAVEL rebaixa VIAVEL a CONDICIONAL."""
    if r.estado == "VIOLADA":
        if av.veredito == "INVIAVEL":
            return av.veredito, f"{av.motivo}; {NOME_OLHAL} violada"
        return "INVIAVEL", f"restrições violadas: {NOME_OLHAL}"
    if r.estado == "NAO_VERIFICAVEL" and av.veredito == "VIAVEL":
        return "CONDICIONAL", f"não verificáveis: {NOME_OLHAL}"
    return av.veredito, av.motivo


# ------------------------------------------------------------------ faixas e variáveis
@dataclass(frozen=True)
class Faixas:
    lo: np.ndarray       # [px, py, pz, u, ψ, r1, φB] (+ δ, se a busca libera o giro do push rod)
    hi: np.ndarray
    amax_rad: float


def faixas(cfg, caixa_m, delta_max_rad=0.0):
    lo_c, hi_c = (np.asarray(c, dtype=float) for c in caixa_m)
    bmin, bmax = float(cfg.valor("braco_min_m")), float(cfg.valor("braco_max_m"))
    amax = float(cfg.valor("amort_ang_max_rad"))
    lo = np.concatenate([lo_c, [0.0, -np.pi, bmin, EPS_PHI]])
    hi = np.concatenate([hi_c, [1.0, np.pi, bmax, np.pi - EPS_PHI]])
    if delta_max_rad > 0.0:                       # 8ª variável: giro do push rod no rocker a partir da tangência
        lo, hi = np.append(lo, -delta_max_rad), np.append(hi, delta_max_rad)
    return Faixas(lo, hi, amax)


def variaveis_de(x, fx):
    """Vetor [px, py, pz, u, ψ, r1, φB] (recortado às faixas) → mecanismo.Variaveis."""
    x = np.clip(np.asarray(x, dtype=float), fx.lo, fx.hi)
    cos_t = 1.0 - x[3] * (1.0 - np.cos(fx.amax_rad))
    sin_t = np.sqrt(max(0.0, 1.0 - cos_t * cos_t))
    ud = np.array([cos_t, sin_t * np.cos(x[4]), sin_t * np.sin(x[4])])
    az = float(np.arctan2(ud[1], ud[0]))
    elv = float(np.arcsin(np.clip(ud[2], -1.0, 1.0)))
    return mec.Variaveis(pivo_m=x[0:3].copy(), az_rad=az, el_rad=elv, r1_m=float(x[5]), phi_b_rad=float(x[6]),
                         delta_rad=float(x[7]) if len(x) > 7 else 0.0)


def _sortear(rng, livres, w, n, fx, mask=None):
    """n amostras: pivôs sorteados entre os pontos livres (com pesos w; só os de `mask`, se dado) e as demais variáveis por
    hipercubo latino. Sem máscara, a ordem de uso do gerador é a da busca anterior (mesma semente, mesmo resultado)."""
    sel = np.arange(len(livres)) if mask is None else np.flatnonzero(mask)
    if len(sel) == 0:
        sel = np.arange(len(livres))
    ww = w[sel]
    idx = sel[rng.choice(len(sel), size=int(n), p=ww / ww.sum())]
    u = _lhs(rng, int(n), len(fx.lo) - 3)
    return np.column_stack([livres[idx], fx.lo[3:] + u * (fx.hi[3:] - fx.lo[3:])])


def _lhs(rng, n, d):
    """Hipercubo latino em [0, 1)^d: uma amostra por estrato em cada dimensão."""
    u = (np.arange(n)[:, None] + rng.random((n, d))) / n
    for j in range(d):
        u[:, j] = u[rng.permutation(n), j]
    return u


# ------------------------------------------------------------------ avaliação de um ponto
def _avaliar_x(hs_v10, x, fx, cena, cfg, n_rapido, origem):
    v = variaveis_de(x, fx)
    c = mec.construir(hs_v10, v, cfg)
    av = _com_olhal(vr.avaliar(c, cena, cfg, n_rapido), c, cfg)
    return Candidato(v, c, av, violacao(av), origem)


def _refinar(hs_v10, cand, x0, fx, cena, cfg, n_rapido, max_aval):
    melhor = [cand]

    def f(x):
        xc = np.clip(x, fx.lo, fx.hi)
        c = _avaliar_x(hs_v10, xc, fx, cena, cfg, n_rapido, "refino")
        if _objetivo(c.avaliacao) < _objetivo(melhor[0].avaliacao):
            melhor[0] = c
        return _objetivo(c.avaliacao)

    passo = SIMPLEX_FRAC * (fx.hi - fx.lo)
    passo = np.where(passo > 0.0, passo, 1e-3)
    simplex = [x0.copy()]
    for j in range(len(x0)):
        xj = x0.copy()
        xj[j] = x0[j] + passo[j] if x0[j] + passo[j] <= fx.hi[j] else x0[j] - passo[j]
        simplex.append(xj)
    minimize(f, x0, method="Nelder-Mead",
             options={"maxfev": int(max_aval), "initial_simplex": np.array(simplex), "xatol": 1e-6, "fatol": 1e-9})
    return melhor[0]


def _x_de(v, fx):
    """mecanismo.Variaveis → vetor [px, py, pz, u, ψ, r1, φB]."""
    ud = mec.direcao_amortecedor(v.az_rad, v.el_rad)
    cos_t = float(np.clip(ud[0], -1.0, 1.0))
    den = 1.0 - np.cos(fx.amax_rad)
    u = (1.0 - cos_t) / den if den > 0.0 else 0.0
    psi = float(np.arctan2(ud[2], ud[1]))
    x = np.concatenate([np.asarray(v.pivo_m, dtype=float), [u, psi, v.r1_m, v.phi_b_rad]])
    return np.append(x, v.delta_rad) if len(fx.lo) > 7 else x


# ------------------------------------------------------------------ diagnóstico
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
        raise ValueError(f"caixa_m com eixo sem valor (None): {caixa_m!r}. A caixa de busca do pivô tem de ser dada "
                         "inteira; na configuração do T11, Y e Z vêm do STEP ou de --caixa")
    return np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)


# ------------------------------------------------------------------ busca
def buscar(hs_v10, cena, cfg, caixa_m, n_amostras=2000, n_refinos=20, semente=0, *, passo_m=0.01, n_rapido=N_RAPIDO,
           max_aval_refino=60, n_finalistas=20, escala_no_m=ESCALA_NO_M, n_conflitos=10, progresso=None,
           delta_max_rad=0.0, otimizar_margem=False, caixa_dinamica=False):
    """Busca candidatos viáveis (ver o docstring do módulo). Levanta ValueError se `caixa_m` tem None."""
    global OTIMIZAR_MARGEM
    OTIMIZAR_MARGEM = bool(otimizar_margem)
    t0 = time.perf_counter()
    caixa = _caixa_explicita(caixa_m)
    fx = faixas(cfg, caixa, delta_max_rad)
    m = el.mapa(cena, caixa, passo_m=passo_m, raio_m=0.0)
    r_pivo = float(cfg.valor("r_pivo_m"))
    livres = m.livres(r_pivo)
    est = {"n_pontos_grade": int(m.folga_m.size), "n_pontos_livres": int(len(livres)), "n_amostras": int(n_amostras)}
    if len(livres) == 0 or n_amostras <= 0:
        motivo = (f"nenhum ponto da grade com folga ≥ r_pivo_m = {r_pivo * 1e3:.1f} mm aos fixos na caixa"
                  if len(livres) == 0 else "nenhuma amostra pedida")
        est["tempo_s"] = time.perf_counter() - t0
        return ResultadoBusca([], Diagnostico(None, [], {}, {}, 0, 0, motivo), m, est)

    rng = np.random.default_rng(semente)
    d = m.dist_no_livres(r_pivo)
    w = np.ones(len(livres)) if not np.any(np.isfinite(d)) else 1.0 / (1.0 + np.where(np.isfinite(d), d, np.inf)
                                                                         / float(escala_no_m))
    n_amostras = int(n_amostras)
    if caixa_dinamica and n_amostras >= 20:
        # caixa dinâmica (entropia cruzada, conselho 2): rodada larga, depois caixas em volta da elite (10 %), 20 % das
        # amostras de cada rodada ficam na caixa inteira para não perder outra região
        n0 = int(round(0.5 * n_amostras)); n1 = int(round(0.3 * n_amostras))
        rodadas = [n0, n1, n_amostras - n0 - n1]
    else:
        rodadas = [n_amostras]
    amostras, X, melhor_v, est["caixas_dinamicas"] = [], np.zeros((0, len(fx.lo))), float("inf"), []
    for k, nk in enumerate(rodadas):
        mask = None
        if k > 0:
            fin = [i for i, c in enumerate(amostras) if np.isfinite(c.violacao)]
            fin.sort(key=lambda i: amostras[i].violacao)
            elite = X[fin[:max(5, len(fin) // 10)], :3] if fin else None
            if elite is not None and len(elite):
                lo, hi = elite.min(axis=0), elite.max(axis=0)
                folga_cx = np.maximum(0.25 * (hi - lo), 0.02)     # (não chamar de `m`: é o mapa de espaço livre)
                lo, hi = lo - folga_cx, hi + folga_cx
                est["caixas_dinamicas"].append({"rodada": k, "lo_m": [float(t) for t in lo], "hi_m": [float(t) for t in hi]})
                mask = np.all((livres >= lo) & (livres <= hi), axis=1)
        n_cx = nk if mask is None else int(round(0.8 * nk))
        Xk = _sortear(rng, livres, w, n_cx, fx, mask)
        if n_cx < nk:
            Xk = np.vstack([Xk, _sortear(rng, livres, w, nk - n_cx, fx, None)])
        X = np.vstack([X, Xk])
        for x in Xk:
            amostras.append(_avaliar_x(hs_v10, x, fx, cena, cfg, n_rapido, "amostra"))
            melhor_v = min(melhor_v, amostras[-1].violacao)
            if progresso is not None:
                progresso("amostras", len(amostras), n_amostras, melhor_v)
    est["falhas"] = _falhas(amostras)

    # refino das melhores amostras com violação finita
    ordem = sorted((i for i, c in enumerate(amostras) if np.isfinite(c.violacao)),
                   key=lambda i: (amostras[i].violacao, chave_ordem(amostras[i].avaliacao), i))
    refinos = []
    sel = ordem[:max(0, int(n_refinos))]
    for k, i in enumerate(sel, start=1):
        refinos.append(_refinar(hs_v10, amostras[i], X[i].copy(), fx, cena, cfg, n_rapido, max_aval_refino))
        melhor_v = min(melhor_v, refinos[-1].violacao)
        if progresso is not None:
            progresso("refinos", k, len(sel), melhor_v)
    est["n_refinos"] = len(refinos)

    # viáveis rápidos → avaliação convergida
    todos, vistos = [], set()
    for c in amostras + refinos:
        k = _x_de(c.variaveis, fx).tobytes()
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
        finitos = [c for c in todos if np.isfinite(c.violacao)]
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
            motivo = (f"nenhuma das {len(amostras)} amostras teve resultado: falhas {est['falhas']}")
        fase1 = Diagnostico(melhor, conflitos, violacoes, est["falhas"], len(amostras), n_com, motivo)
    est["tempo_s"] = time.perf_counter() - t0
    return ResultadoBusca(finais, fase1, m, est)
