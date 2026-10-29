"""Estudo da faixa do NEUTRO (incremento 7, Task 6; spec §4.3; EDR-065 item 2). Só estudo: a regra não muda.

A regra de hoje (`equilibrio.analise_par`) declara NEUTRO quando |Δ| <= R, com Δ = S_r − S_f e R = max|S_h − S_h/2|
sobre os eixos (`equilibrio._resolucao`, com o piso de 1e-9 g). O EDR-065 item 2 diz que essa resolução subestima o
erro (o fator 4/3 de Richardson com p = 2). A spec §4.3 reabriu o fator por três motivos: o serrote do máximo discreto
em α (|S_h − S_h/2| pode dar ≈ 0 com erro real ≠ 0), o erro de Δ que pode chegar a e_F + e_R, e o ramo de um eixo só.
Este módulo mede, sem mudar nada no `equilibrio`:
- as saturações nas grades aninhadas h, h/2, h/4 e h/8 (passo/2^k em a_y e 2^k·(n_alfa − 1) + 1 pontos de α, as
  mesmas regras do refinamento do analise_par), a ordem observada p = log2(|s_h − s_h/2| / |s_h/2 − s_h/4|) e a razão;
- o erro de Δ na grade h contra a h/8 (tomada como referência) e a soma e_F + e_R das estimativas por eixo que a regra
  já tem (|S_h − S_h/2|), para ver se a soma cobre o erro;
- o veredito de cada alternativa da spec §4.3 (fator 2^p/(2^p − 1), faixa e_F + e_R, refino do pico por parábola).

Unidades: as saturações, as diferenças e os erros deste módulo estão em g (a_y / G); o analise_par usa m/s².
O estudo roda em casos sintéticos (rotulados); nenhum número daqui é resultado do carro.

Uso (Git Bash, depois de export UV_SYSTEM_CERTS=1):
    uv run python -X utf8 python/estudo_neutro.py [--saida ARQ]
Escreve as tabelas do estudo em Markdown (padrão: build/estudo-neutro-tabelas.md).
"""
from __future__ import annotations

import argparse
import dataclasses
import math
from dataclasses import dataclass
from pathlib import Path

import equilibrio as eq
from suspension_model import G

# Diferença tratada como nula na ordem observada [g]. É o mesmo valor do piso da resolução do analise_par
# (equilibrio._PISO_RESOLUCAO_MS2 = 1e-9·G): ruído de ponto flutuante, não banda de engenharia.
TOL_DIF_G = 1e-9
NIVEIS = 4                      # grades h, h/2, h/4 e h/8
ROTULO = "sintético"


@dataclass(frozen=True)
class Convergencia:
    """Saturação de um eixo nas grades h, h/2, h/4 e h/8 [g] (None onde o eixo não satura) e a ordem observada.

    p = log2(|s_h − s_h/2| / |s_h/2 − s_h/4|) e razao = |s_h − s_h/2| / |s_h/2 − s_h/4|. Se alguma das duas
    diferenças for < TOL_DIF_G, p e razao são None e dif_nula é True (nunca divide por zero). Se o eixo não satura
    em alguma das três primeiras grades, p e razao são None e dif_nula é False.
    """
    eixo: str
    s: tuple[float | None, ...]
    p: float | None
    razao: float | None
    dif_nula: bool


def convergencia(eixo: str, s: tuple) -> Convergencia:
    """Convergencia de um eixo a partir das saturações [g] nas grades h, h/2, h/4 (e h/8, só guardada)."""
    s = tuple(s)
    if any(v is None for v in s[:3]):
        return Convergencia(eixo, s, None, None, False)
    d1, d2 = abs(s[0] - s[1]), abs(s[1] - s[2])
    if d1 < TOL_DIF_G or d2 < TOL_DIF_G:
        return Convergencia(eixo, s, None, None, True)
    razao = d1 / d2
    return Convergencia(eixo, s, math.log2(razao), razao, False)


def grades(passo_g: float, n_alfa: int, niveis: int = NIVEIS) -> tuple:
    """(passo_g, n_alfa) das grades aninhadas: passo/2^k e 2^k·(n_alfa − 1) + 1 pontos de α (k = 0…niveis − 1).

    É a regra do refinamento do analise_par (passo/2 e 2·n_alfa − 1) aplicada k vezes: a grade de α de 0 a −A com
    2^k·(n − 1) + 1 pontos contém a de n pontos, e a grade de a_y com passo/2^k contém a de passo.
    """
    return tuple((passo_g / 2 ** k, 2 ** k * (n_alfa - 1) + 1) for k in range(niveis))


# ---------------------------------------------------------------------------
# Alternativa 3 da spec §4.3: refino do pico da capacidade por parábola de 3 pontos (só no estudo)
# ---------------------------------------------------------------------------

def _capacidade_refinada(caso: eq.CasoEquilibrio, eixo: str, ay_ms2: float, n_alfa: int, *,
                         formas: eq.Formas) -> eq.Capacidade:
    """capacidade_eixo com o pico refinado pela parábola que passa pelo máximo da grade e pelos dois vizinhos.

    Parte do resultado de equilibrio.capacidade_eixo (mesmas regras de motivo e de limitação) e só troca fy_max_N e
    alfa_pico_rad pelo vértice da parábola. Sem curvatura de máximo (y₋ − 2y₀ + y₊ >= 0) fica o valor da grade.
    Não é a fórmula da planilha: é o efeito da alternativa 3, que mudaria a fórmula da capacidade (exige aprovação).
    """
    cap = eq.capacidade_eixo(caso, eixo, ay_ms2, n_alfa, formas=formas)
    if cap.motivo is not None or cap.fy_max_N is None:
        return cap
    rodas = eq._rodas(eixo)
    fz_u, gam_u, _ = eq.entrada_limitada(caso, rodas, eq.cargas(caso, ay_ms2), eq.camber(caso, ay_ms2))
    alfas = eq.grade_alfa(caso, n_alfa, formas=formas)
    fatores = None
    if eixo == "R":
        fatores, _ = eq.elipse_traseira(caso, ay_ms2, rodas, fz_u, gam_u, formas=formas, n_alfa=n_alfa)
    i = alfas.index(cap.alfa_pico_rad)
    if i == 0:                  # pico em α = 0: sem vizinho dos dois lados
        return cap
    y_m = eq.fy_eixo_limitado(caso, rodas, fz_u, gam_u, alfas[i - 1], fatores, formas=formas)
    y_p = eq.fy_eixo_limitado(caso, rodas, fz_u, gam_u, alfas[i + 1], fatores, formas=formas)
    y_0 = cap.fy_max_N
    den = y_m - 2.0 * y_0 + y_p
    if den >= 0.0:
        return cap
    x = (y_m - y_p) / (2.0 * den)          # vértice, em passos da grade a partir de alfas[i] (|x| <= 1/2)
    fy = y_0 - (y_p - y_m) ** 2 / (8.0 * den)
    alfa = alfas[i] + x * (alfas[i + 1] - alfas[i])
    return dataclasses.replace(cap, fy_max_N=fy, alfa_pico_rad=alfa)


def _varredura_refinada(caso: eq.CasoEquilibrio, ay_max_g: float, passo_g: float, n_alfa: int, *,
                        formas: eq.Formas) -> tuple:
    """equilibrio._varredura com _capacidade_refinada no lugar de capacidade_eixo (mesma grade de a_y)."""
    n = math.floor(ay_max_g / passo_g + 1e-9)
    linhas = []
    for k in range(n + 1):
        ay = k * passo_g * G
        req_f, req_r = eq.forca_exigida(caso, ay)
        linhas.append(eq.LinhaPar(ay_ms2=ay, fz=eq.cargas(caso, ay),
                                  cap_f=_capacidade_refinada(caso, "F", ay, n_alfa, formas=formas),
                                  cap_r=_capacidade_refinada(caso, "R", ay, n_alfa, formas=formas),
                                  req_f=req_f, req_r=req_r))
    linhas = tuple(linhas)
    return linhas, eq._saturacao(linhas, "F"), eq._saturacao(linhas, "R")


# ---------------------------------------------------------------------------
# Veredito com uma faixa dada (a mesma lógica do analise_par; só a faixa muda)
# ---------------------------------------------------------------------------

def _veredito(sf, sr, faixa_ms2: float | None) -> str | None:
    """Veredito do analise_par (linhas 1003-1014 de equilibrio.py no commit b8d622d) com a faixa dada [m/s²].

    None quando a faixa não é definida (alternativa que não se aplica ao caso).
    """
    S_f, S_r = sf.ay_sat, sr.ay_sat
    if S_f is None and S_r is None:
        return eq.NA
    if faixa_ms2 is None:
        return None
    V_f = sf.ay_valido if sf.ay_valido is not None else -math.inf
    V_r = sr.ay_valido if sr.ay_valido is not None else -math.inf
    if S_f is not None and S_r is not None:
        delta = S_r - S_f
        if abs(delta) <= faixa_ms2:
            return eq.NEUTRO
        return eq.PUSH if delta > 0.0 else eq.LOOSE
    if S_f is not None and V_r >= S_f + faixa_ms2:
        return eq.PUSH
    if S_r is not None and V_f >= S_r + faixa_ms2:
        return eq.LOOSE
    return eq.NA


def _fator(p: float | None) -> float | None:
    """2^p/(2^p − 1) (alternativa 1). None sem p ou com p <= 0 (diferenças que não diminuem: o fator não existe)."""
    if p is None or p <= 0.0:
        return None
    return 2.0 ** p / (2.0 ** p - 1.0)


def _g(x_ms2: float | None) -> float | None:
    return None if x_ms2 is None else x_ms2 / G


def estudar(caso: eq.CasoEquilibrio, *, formas: eq.Formas = eq.FORMAS_V42, passo_g: float = 0.05,
            n_alfa: int = 25, ay_max_g: float = 2.0, refino_pico: bool = False) -> dict:
    """Convergência das saturações nas grades h, h/2, h/4 e h/8 e o efeito das alternativas da spec §4.3.

    Chaves (valores em g, salvo indicação):
    - "F", "R": Convergencia de cada eixo;
    - "ramo": "dois" (os dois eixos saturam na grade h), "um" (só um) ou "nenhum";
    - "grades": as (passo_g, n_alfa) usadas;
    - "est_F", "est_R": estimativa por eixo que a regra já tem, |S_h − S_h/2| (o passo, se o eixo satura numa das
      duas grades só; None se não satura em nenhuma), como em equilibrio._resolucao;
    - "erro_F", "erro_R": erro real por eixo, |S_h − S_h/8| (None sem as duas saturações);
    - "delta": Δ = S_r − S_f em cada grade (None onde algum eixo não satura);
    - "erro_delta": |Δ_h − Δ_h/8| (só no ramo "dois" com Δ_h/8 definido; senão None);
    - "soma_erros": max(est_F + est_R, TOL_DIF_G) (só no ramo "dois"; senão None);
    - "violacao": erro_delta > soma_erros (False quando algum dos dois é None);
    - "faixas": faixa de cada regra [g] ("atual", "alt1", "alt1_43", "alt2", "passo"); None onde não se aplica;
    - "vereditos": veredito da grade h com cada faixa (None onde a faixa não se aplica);
    - "veredito_atual": o mesmo que vereditos["atual"], que tem de bater com o analise_par.
    refino_pico=True troca a capacidade pela de _capacidade_refinada (alternativa 3) em todas as grades.
    """
    sats = []
    for pk, nk in grades(passo_g, n_alfa):
        if refino_pico:
            _, sf, sr = _varredura_refinada(caso, ay_max_g, pk, nk, formas=formas)
        else:
            _, sf, sr = eq._varredura(caso, ay_max_g, pk, nk, formas=formas)
        sats.append((sf, sr))
    s_f = tuple(_g(sf.ay_sat) for sf, _ in sats)
    s_r = tuple(_g(sr.ay_sat) for _, sr in sats)
    conv_f, conv_r = convergencia("F", s_f), convergencia("R", s_r)
    passo_ms2 = passo_g * G

    def est(s):
        if s[0] is not None and s[1] is not None:
            return abs(s[0] - s[1])
        if s[0] is not None or s[1] is not None:
            return passo_g
        return None

    def erro(s):
        return abs(s[0] - s[3]) if s[0] is not None and s[3] is not None else None

    est_f, est_r = est(s_f), est(s_r)
    n_sat = (s_f[0] is not None) + (s_r[0] is not None)
    ramo = {2: "dois", 1: "um", 0: "nenhum"}[n_sat]
    delta = tuple(None if a is None or b is None else b - a for a, b in zip(s_f, s_r))
    erro_delta = soma_erros = None
    if ramo == "dois" and delta[3] is not None:
        erro_delta = abs(delta[0] - delta[3])
    if ramo == "dois":
        soma_erros = max(est_f + est_r, TOL_DIF_G)
    violacao = erro_delta is not None and soma_erros is not None and erro_delta > soma_erros

    sf_h, sr_h = sats[0]
    sf_2, sr_2 = sats[1]
    faixa_atual = eq._resolucao((sf_h.ay_sat, sr_h.ay_sat), (sf_2.ay_sat, sr_2.ay_sat), passo_ms2)
    faixas_ms2 = {"atual": faixa_atual, "alt1": None, "alt1_43": None, "alt2": None, "passo": passo_ms2}
    if ramo == "dois" and est_f is not None and est_r is not None:
        f_f, f_r = _fator(conv_f.p), _fator(conv_r.p)
        if f_f is not None and f_r is not None:
            faixas_ms2["alt1"] = max(f_f * est_f, f_r * est_r, TOL_DIF_G) * G
        faixas_ms2["alt1_43"] = max(4.0 / 3.0 * max(est_f, est_r), TOL_DIF_G) * G
        faixas_ms2["alt2"] = soma_erros * G
    vereditos = {k: _veredito(sf_h, sr_h, v) for k, v in faixas_ms2.items()}

    return {"F": conv_f, "R": conv_r, "ramo": ramo, "grades": grades(passo_g, n_alfa),
            "est_F": est_f, "est_R": est_r, "erro_F": erro(s_f), "erro_R": erro(s_r), "delta": delta,
            "erro_delta": erro_delta, "soma_erros": soma_erros, "violacao": violacao,
            "faixas": {k: _g(v) for k, v in faixas_ms2.items()}, "vereditos": vereditos,
            "veredito_atual": vereditos["atual"]}


def _com_lambda(caso: eq.CasoEquilibrio, fator: float) -> eq.CasoEquilibrio:
    """Caso com λ_f = K_φf/(K_φf + K_φr) multiplicado por fator, com a soma K_φf + K_φr mantida."""
    cfg = caso.cfg
    k_soma = cfg.roll_stiffness_front + cfg.roll_stiffness_rear
    lam_n = cfg.roll_stiffness_front / k_soma * fator
    cfg_n = dataclasses.replace(cfg, roll_stiffness_front=lam_n * k_soma, roll_stiffness_rear=(1.0 - lam_n) * k_soma)
    return dataclasses.replace(caso, cfg=cfg_n)


def casos_perto_do_neutro(caso: eq.CasoEquilibrio) -> dict:
    """Varredura SINTÉTICA de λ_f de +4 % a +7 % (relativo), em passos de 0,5 % (7 casos), com _com_lambda.

    No caso-base do estudo, Δ troca de sinal entre o caso-base (LOOSE) e λ_f +10 % (PUSH); a revisão da Task 6
    estimou, por interpolação, Δ_h/8 = 0 perto de +4,8 % e Δ_h = 0 perto de +5,6 % (estimativa a confirmar pela
    própria varredura). O nome de cada caso leva o rótulo "sintético".
    """
    out = {}
    for k in range(7):
        pct = 4.0 + 0.5 * k
        out[f"λ_f +{pct:.1f} % ({ROTULO})".replace(".", ",")] = _com_lambda(caso, 1.0 + pct / 100.0)
    return out


def classe(veredito: str | None, delta_ref: float | None) -> str | None:
    """Classe do veredito da grade h contra o sinal de Δ na referência (h/8): "NEUTRO", "certo" ou "ERRADO".

    Sinal real: PUSH se Δ_ref > 0, LOOSE se Δ_ref < 0. None sem veredito ou sem Δ_ref (ou com Δ_ref = 0 exato).
    A h/8 não convergiu por completo (ver o estudo): o "sinal real" é o da melhor grade calculada, não o exato.
    """
    if veredito is None:
        return None
    if veredito == eq.NEUTRO:
        return "NEUTRO"
    if delta_ref is None or delta_ref == 0.0 or veredito not in (eq.PUSH, eq.LOOSE):
        return None
    real = eq.PUSH if delta_ref > 0.0 else eq.LOOSE
    return "certo" if veredito == real else "ERRADO"


def _cruzamento(xs: list, ys: list) -> float | None:
    """Primeiro x em que y troca de sinal, por interpolação linear entre pontos vizinhos; None sem troca."""
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if y0 is None or y1 is None:
            continue
        if y0 == 0.0:
            return x0
        if (y0 < 0.0) != (y1 < 0.0):
            return x0 + (x1 - x0) * (-y0) / (y1 - y0)
    return None


def casos_perturbados(caso: eq.CasoEquilibrio) -> dict:
    """Seis casos perturbados do caso dado, todos SINTÉTICOS (o nome leva o rótulo):
    - λ_f ± 10 % (relativo): λ_f = K_φf/(K_φf + K_φr) vezes 1,1 ou 0,9, com a soma K_φf + K_φr mantida
      (VehicleConfig.roll_stiffness_front/rear; o λ_f não é campo do caso);
    - toe ± 0,1°: soma ±0,1° ao toe_rad das quatro rodas (toe + = toe-out, EDR-002);
    - R ± 10 %: raio_m vezes 1,1 ou 0,9. Exige raio_m.
    """
    if caso.raio_m is None:
        raise ValueError("casos_perturbados exige raio_m (a perturbação de R ± 10 % não tem base sem R).")
    d_toe = math.radians(0.1)
    out = {}
    for sinal, txt in ((+1, "+"), (-1, "−")):
        out[f"λ_f {txt}10 % ({ROTULO})"] = _com_lambda(caso, 1.0 + 0.1 * sinal)
    for sinal, txt in ((+1, "+"), (-1, "−")):
        toe = {c: v + sinal * d_toe for c, v in caso.toe_rad.items()}
        out[f"toe {txt}0,1° ({ROTULO})"] = dataclasses.replace(caso, toe_rad=toe)
    for sinal, txt in ((+1, "+"), (-1, "−")):
        out[f"R {txt}10 % ({ROTULO})"] = dataclasses.replace(caso, raio_m=caso.raio_m * (1.0 + 0.1 * sinal))
    return out


# ---------------------------------------------------------------------------
# Tabelas do estudo (Markdown)
# ---------------------------------------------------------------------------

def caso_base_sintetico():
    """Caso V4.2 SINTÉTICO do estudo: veiculo_base de tests/test_escada.py, pneu provisório do TTC com LMUY = 0,5
    (escala de teste), R = 8,5 m, downforce 400 N com 45 % na frente. Nada disto é dado do carro."""
    import tire_model as tm
    from suspension_model import VehicleConfig
    raiz = Path(__file__).resolve().parent.parent
    cfg = VehicleConfig(mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
                        cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
                        unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
                        roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0)
    ds = tm.load_dataset(str(raiz / "data" / "Hoosier_R25B_13x7_TTC_provisional.tir"), source_axis_system="ISO_TYDEX")
    ds = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.5})
    return eq.CasoEquilibrio(cfg=cfg, ds=ds, raio_m=8.5, downforce_N=400.0, aero_balance_front=0.45)


def _f(x, fmt=".7f"):
    """Número com vírgula decimal (pt-BR); "—" para None."""
    return "—" if x is None else format(x, fmt).replace(".", ",")


def _e(x):
    return "—" if x is None else f"{x:.2e}".replace(".", ",")


def _razao(a, b):
    return None if a is None or b is None or b == 0.0 else a / b


def _sinal(a, b):
    """Sinal de a − b como texto ("−", "+" ou "0"); "—" sem os dois."""
    if a is None or b is None:
        return "—"
    return "−" if a < b else ("+" if a > b else "0")


def tabela_perto(perto: dict) -> str:
    """Tabela 7: varredura de λ_f perto do neutro (sem refino), com a classe de cada veredito contra o sinal da h/8."""
    L = ["### Tabela 7. Varredura de λ_f perto do neutro, sem refino [g] (sintético)\n",
         "Classe: NEUTRO; \"certo\" ou \"ERRADO\" contra o sinal de Δ_h/8 (a h/8 não convergiu por completo). "
         "A alternativa 3 (refino) não foi calculada nesta varredura.\n",
         "| Caso | Δ_h | Δ_h/8 | sinal real (h/8) | Atual: faixa / veredito / classe | Alt. 1 (p medido) "
         "| Alt. 1 com 4/3 | Alt. 2 (e_F + e_R) | p_F / p_R |",
         "|---|---|---|---|---|---|---|---|---|"]
    erradas = {k: 0 for k in ("atual", "alt1", "alt1_43", "alt2")}
    neutros = dict(erradas)
    for nome, r in perto.items():
        d_ref = r["delta"][3]
        real = "—" if d_ref is None else ("PUSH" if d_ref > 0 else "LOOSE")

        def cel(k):
            v = r["vereditos"][k]
            if v is None:
                return "não se aplica"
            c = classe(v, d_ref)
            erradas[k] += c == "ERRADO"
            neutros[k] += c == "NEUTRO"
            return f"{_e(r['faixas'][k])} / {v} / {c}"
        L.append(f"| {nome} | {_f(r['delta'][0])} | {_f(d_ref)} | {real} | {cel('atual')} | {cel('alt1')} "
                 f"| {cel('alt1_43')} | {cel('alt2')} | {_f(r['F'].p, '.2f')} / {_f(r['R'].p, '.2f')} |")
    xs = [4.0 + 0.5 * k for k in range(len(perto))]
    rs = list(perto.values())
    x_h = _cruzamento(xs, [r["delta"][0] for r in rs])
    x_8 = _cruzamento(xs, [r["delta"][3] for r in rs])
    L.append("")
    L.append(f"- Cruzamento de zero por interpolação linear entre casos vizinhos: Δ_h = 0 em λ_f "
             f"{'—' if x_h is None else '+' + _f(x_h, '.2f') + ' %'}; Δ_h/8 = 0 em λ_f "
             f"{'—' if x_8 is None else '+' + _f(x_8, '.2f') + ' %'}.")
    nomes = {"atual": "regra atual", "alt1": "alt. 1 (p medido)", "alt1_43": "alt. 1 com 4/3", "alt2": "alt. 2"}
    L.append("- Sinal errado / NEUTRO em " + str(len(perto)) + " casos: "
             + "; ".join(f"{nomes[k]} {erradas[k]} / {neutros[k]}" for k in nomes) + ".")
    return "\n".join(L) + "\n"


def conferencia_pico(caso: eq.CasoEquilibrio, eixo: str, ay_g: float, n_alfa: int = 25, n_densa: int = 24001, *,
                     formas: eq.Formas = eq.FORMAS_V42) -> dict:
    """Pico da Fy do eixo [N] em a_y [g]: grade de n_alfa pontos, parábola de 3 pontos e grade densa de n_densa pontos.

    A grade densa (passo A/(n_densa − 1)) faz o papel do pico "verdadeiro" para medir quanto a grade e a parábola erram.
    Só para o estudo; sem tração (fatores da elipse = None), como o caso-base.
    """
    ay = ay_g * G
    rodas = eq._rodas(eixo)
    fz_u, gam_u, _ = eq.entrada_limitada(caso, rodas, eq.cargas(caso, ay), eq.camber(caso, ay))
    densa = eq.grade_alfa(caso, n_densa, formas=formas)
    vals = [eq.fy_eixo_limitado(caso, rodas, fz_u, gam_u, a, formas=formas) for a in densa]
    i = max(range(len(vals)), key=vals.__getitem__)
    cap = eq.capacidade_eixo(caso, eixo, ay, n_alfa, formas=formas)
    par = _capacidade_refinada(caso, eixo, ay, n_alfa, formas=formas)
    return {"densa": (vals[i], densa[i]), "grade": (cap.fy_max_N, cap.alfa_pico_rad),
            "parabola": (par.fy_max_N, par.alfa_pico_rad), "passo_alfa": abs(densa[-1]) / (n_alfa - 1)}


def tabelas(resultados: dict, refinados: dict) -> str:
    """Markdown das tabelas do estudo. resultados e refinados: {nome do caso: estudar(...)}."""
    L = []
    L.append("### Tabela 1. Saturação por grade, sem refino [g] (sintético)\n")
    L.append("| Caso | Eixo | S_h | S_h/2 | S_h/4 | S_h/8 | d1 = \\|S_h − S_h/2\\| | d2 = \\|S_h/2 − S_h/4\\| "
             "| d3 = \\|S_h/4 − S_h/8\\| | razão d1/d2 | p | dif. nula | erro real \\|S_h − S_h/8\\| | erro real / d1 "
             "| sinal de S_h − S_h/8 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for nome, r in resultados.items():
        for c in (r["F"], r["R"]):
            s = c.s
            d = [None if s[k] is None or s[k + 1] is None else abs(s[k] - s[k + 1]) for k in range(3)]
            err = None if s[0] is None or s[3] is None else abs(s[0] - s[3])
            L.append(f"| {nome} | {c.eixo} | {_f(s[0])} | {_f(s[1])} | {_f(s[2])} | {_f(s[3])} | {_e(d[0])} "
                     f"| {_e(d[1])} | {_e(d[2])} | {_f(c.razao, '.3g')} | {_f(c.p, '.2f')} "
                     f"| {'sim' if c.dif_nula else 'não'} | {_e(err)} | {_f(_razao(err, d[0]), '.2f')} "
                     f"| {_sinal(s[0], s[3])} |")
    L.append("")
    L.append("### Tabela 2. Erro de Δ contra e_F + e_R, sem refino [g] (sintético)\n")
    L.append("| Caso | Ramo | Δ_h | Δ_h/8 | erro real F | erro real R | e_F = d1_F | e_R = d1_R | erro de Δ "
             "| \\|erro real R − erro real F\\| | e_F + e_R | violação de (c) | resolução atual | erro de Δ / resolução "
             "| erro real F / e_F | erro real R / e_R |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for nome, r in resultados.items():
        res = r["faixas"]["atual"]
        q = None if r["erro_delta"] is None or not res else r["erro_delta"] / res
        dif = None if r["erro_F"] is None or r["erro_R"] is None else abs(r["erro_R"] - r["erro_F"])
        L.append(f"| {nome} | {r['ramo']} | {_f(r['delta'][0])} | {_f(r['delta'][3])} | {_e(r['erro_F'])} "
                 f"| {_e(r['erro_R'])} | {_e(r['est_F'])} | {_e(r['est_R'])} | {_e(r['erro_delta'])} | {_e(dif)} "
                 f"| {_e(r['soma_erros'])} | {'SIM' if r['violacao'] else 'não'} | {_e(res)} | {_f(q, '.2f')} "
                 f"| {_f(_razao(r['erro_F'], r['est_F']), '.2f')} | {_f(_razao(r['erro_R'], r['est_R']), '.2f')} |")
    L.append("")
    L.append("### Tabela 3. Faixa e veredito de cada regra na grade h (sintético)\n")
    L.append("| Caso | Δ_h | Atual: faixa / veredito | Alt. 1 (p medido): faixa / veredito "
             "| Alt. 1 com 4/3: faixa / veredito | Alt. 2 (e_F + e_R): faixa / veredito "
             "| Alt. 3 (refino, regra atual): Δ_h / faixa / veredito | Δ_h/8 sem refino |")
    L.append("|---|---|---|---|---|---|---|---|")
    for nome, r in resultados.items():
        fx, vd = r["faixas"], r["vereditos"]
        rr = refinados[nome]

        def par(k):
            return "não se aplica" if vd[k] is None else f"{_e(fx[k])} / {vd[k]}"
        L.append(f"| {nome} | {_f(r['delta'][0])} | {par('atual')} | {par('alt1')} | {par('alt1_43')} | {par('alt2')} "
                 f"| {_f(rr['delta'][0])} / {_e(rr['faixas']['atual'])} / {rr['veredito_atual']} "
                 f"| {_f(r['delta'][3])} |")
    L.append("")
    L.append("### Tabela 4. Com refino do pico por parábola (alternativa 3) [g] (sintético)\n")
    L.append("| Caso | Eixo | S_h | S_h/2 | S_h/4 | S_h/8 | d1 | d2 | p | dif. nula | erro real \\|S_h − S_h/8\\| |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for nome, r in refinados.items():
        for c, err in ((r["F"], r["erro_F"]), (r["R"], r["erro_R"])):
            s = c.s
            d = [None if s[k] is None or s[k + 1] is None else abs(s[k] - s[k + 1]) for k in range(2)]
            L.append(f"| {nome} | {c.eixo} | {_f(s[0])} | {_f(s[1])} | {_f(s[2])} | {_f(s[3])} | {_e(d[0])} "
                     f"| {_e(d[1])} | {_f(c.p, '.2f')} | {'sim' if c.dif_nula else 'não'} | {_e(err)} |")
    L.append("")
    L.append("### Tabela 5. Erro de Δ com refino [g] (sintético)\n")
    L.append("| Caso | Δ_h | Δ_h/8 | erro de Δ | e_F + e_R | violação de (c) | erro de Δ sem refino |")
    L.append("|---|---|---|---|---|---|---|")
    for nome, rr in refinados.items():
        L.append(f"| {nome} | {_f(rr['delta'][0])} | {_f(rr['delta'][3])} | {_e(rr['erro_delta'])} "
                 f"| {_e(rr['soma_erros'])} | {'SIM' if rr['violacao'] else 'não'} "
                 f"| {_e(resultados[nome]['erro_delta'])} |")
    L.append("")
    for titulo, rs in (("sem refino", resultados), ("com refino", refinados)):
        n_eixos = sum(1 for r in rs.values() for c in (r["F"], r["R"]) if c.s[0] is not None and c.s[1] is not None)
        d1_nulo = sum(1 for r in rs.values() for c in (r["F"], r["R"])
                      if c.s[0] is not None and c.s[1] is not None and abs(c.s[0] - c.s[1]) < TOL_DIF_G)
        nulas = sum(1 for r in rs.values() for c in (r["F"], r["R"]) if c.dif_nula)
        viol = [n for n, r in rs.items() if r["violacao"]]
        n_menor = sum(1 for r in rs.values() for c in (r["F"], r["R"])
                      if c.s[0] is not None and c.s[3] is not None and c.s[0] < c.s[3])
        L.append(f"- {titulo}: d1 < 1e-9 g em {d1_nulo} de {n_eixos} eixos; dif. nula (d1 ou d2 < 1e-9 g) em "
                 f"{nulas} de {n_eixos}; S_h < S_h/8 em {n_menor} de {n_eixos}; violações de (c): {len(viol)} "
                 f"({', '.join(viol) if viol else 'nenhuma'}).")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", default=str(Path(__file__).resolve().parent.parent / "build" / "estudo-neutro-tabelas.md"))
    a = ap.parse_args(argv)
    base = caso_base_sintetico()
    casos = {f"base ({ROTULO})": base, **casos_perturbados(base)}
    resultados = {n: estudar(c) for n, c in casos.items()}
    refinados = {n: estudar(c, refino_pico=True) for n, c in casos.items()}
    texto = tabelas(resultados, refinados)
    r0 = resultados[f"base ({ROTULO})"]
    L = ["### Tabela 6. Pico da Fy do eixo no caso-base, na a_y de saturação da grade h/8 (sintético)\n",
         "| Eixo | a_y [g] | Pico denso (24001 pontos) [N] | Grade h (25 pontos): erro [N] "
         "| Parábola de 3 pontos: erro [N] | α do pico denso / grade / parábola [rad] |",
         "|---|---|---|---|---|---|"]
    for c in (r0["F"], r0["R"]):
        cf = conferencia_pico(base, c.eixo, c.s[3])
        (yd, ad), (yg, ag), (yp, ap) = cf["densa"], cf["grade"], cf["parabola"]
        L.append(f"| {c.eixo} | {_f(c.s[3])} | {_f(yd, '.4f')} | {_f(yg - yd, '+.4f')} | {_f(yp - yd, '+.4f')} "
                 f"| {_f(ad, '.5f')} / {_f(ag, '.5f')} / {_f(ap, '.5f')} |")
    L.append(f"\nPasso da grade h em α: {_f(cf['passo_alfa'], '.5f')} rad.\n")
    texto += "\n" + "\n".join(L)
    perto = {n: estudar(c) for n, c in casos_perto_do_neutro(base).items()}
    texto += "\n" + tabela_perto(perto)
    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(texto, encoding="utf-8", newline="\n")
    print(texto)
    print(f"gravado em {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
