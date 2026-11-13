"""Sensibilidade do pneu e arrasto induzido (pneu-1, EDR-075): forças por roda e arrasto induzido.

Arrasto induzido (Milliken RCVD §2.9, p. 64-65 e Fig. 2.36, p. 67): cada pneu com ângulo de deriva α_i e força lateral
F_y,i tem uma componente de F_y,i contra o avanço do carro. Aqui, D_i = −F_y,i·sen α_i (D3 do plano), na convenção ISO
do projeto (α > 0 = velocidade para a esquerda da direção da roda; `tire_model.wheel_forces`). Na curva à esquerda,
`equilibrio_linear.angulos_necessarios` dá α < 0 e F_y > 0, e D_i ≥ 0. Usa-se −F_y·sen α, e não F_y·sen|α|, para manter
o sinal certo com empuxo de camber ou toe. Com toe ≠ 0, D(0) > 0: é o arrasto do toe, físico, e não erro.

Somar roda a roda generaliza a bicicleta de duas rodas do Milliken: é uma escolha declarada (spec §7.2). Cada α_i já é
relativo à velocidade da própria roda e F_x = 0, então não há cos δ na soma D = Σ D_i. D em N (J/m, a energia por
distância percorrida).
"""
from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass

import equilibrio as eq
import equilibrio_linear as el
import tire_model as tm
from suspension_model import G

PASSO_REL = 1e-9    # tolerância para o último passo da grade cair em ay_ate


def forcas_por_roda(caso: eq.CasoEquilibrio, ay_ms2: float, alfa_ref: tuple[float, float], *,
                    formas: eq.Formas) -> dict[str, tuple[float, float]]:
    """canto -> (α_i [rad, ISO], F_y,i [N, ISO]) em a_y, com α_ref = (α_f, α_r) dos eixos.

    α_i = α_ref do eixo + Δα da roda (toe e Ackermann, `eq.deriva_total`). Fz e γ são os limitados à faixa do .tir
    (`eq.entrada_limitada`, EDR-056), como em `eq.fy_eixo_limitado`.
    """
    fz, gam = eq.cargas(caso, ay_ms2), eq.camber(caso, ay_ms2)
    dal = eq.deriva_total(caso, formas=formas)
    saida: dict[str, tuple[float, float]] = {}
    for eixo, a_ref in zip(("F", "R"), alfa_ref):
        rodas = eq.RODAS_DO_EIXO[eixo]
        fz_u, gam_u, _ = eq.entrada_limitada(caso, rodas, fz, gam)
        for c in rodas:
            a_i = a_ref + dal[c]
            saida[c] = (a_i, tm.wheel_forces(caso.ds, c, fz_u[c], a_i, gam_u[c], 0.0)[1])
    return saida


@dataclass(frozen=True)
class LinhaArrasto:
    """Uma linha da grade de a_y: α de referência, arrasto induzido total e por roda, e a 1ª ordem.

    d_n: D = Σ_i −F_y,i·sen α_i [N]; d_por_roda: cada D_i [N]; d_1a_ordem_n: Σ_eixo F_y exigida·|α_ref| [N];
    d_sobre_mg: D/(m·g); d_sobre_rolamento: D/(Crr·m·g) só com `crr_referencia` (tamanho de efeito, não decisão).
    """
    ay_ms2: float
    ay_g: float
    alfa_f_rad: float
    alfa_r_rad: float
    d_n: float
    d_por_roda: dict[str, float]
    d_1a_ordem_n: float
    d_sobre_mg: float
    d_sobre_rolamento: float | None
    rotulos: tuple[str, ...]


def arrasto_induzido(caso: eq.CasoEquilibrio, *, formas: eq.Formas, ay_ate_ms2: float | None,
                     ay_max_g: float = 2.0, passo_g: float = 0.1,
                     crr_referencia: float | None = None) -> tuple[LinhaArrasto, ...]:
    """Arrasto induzido por a_y, de 0 até `ay_ate_ms2` (D4), em passos de `passo_g` (a_y = k·passo_g·g).

    Com `ay_ate_ms2` None, vai até `ay_max_g` e para no último a_y em que `angulos_necessarios` resolve (rótulo
    "sem saturação até X g: grade até o último a_y resolvido", ou o ponto onde parou). Com valor, a última linha tem
    a_y ≤ ay_ate_ms2. Ver o módulo para D3 e a soma roda a roda.
    """
    if passo_g <= 0.0:
        raise ValueError("passo_g deve ser > 0.")
    limite = ay_max_g * G if ay_ate_ms2 is None else min(ay_ate_ms2, ay_max_g * G)
    m_g = caso.cfg.mass_total * G
    linhas: list[LinhaArrasto] = []
    parou_antes: float | None = None
    k = 0
    while True:
        ay = k * passo_g * G
        if ay > limite * (1 + PASSO_REL):
            break
        alfas = el.angulos_necessarios(caso, ay, formas=formas)
        if alfas is None:
            parou_antes = ay
            break
        por_roda = forcas_por_roda(caso, ay, alfas, formas=formas)
        d_i = {c: -fy * math.sin(a) for c, (a, fy) in por_roda.items()}
        d = sum(d_i.values())
        d_1 = sum(f * abs(a) for f, a in zip(eq.forca_exigida(caso, ay), alfas))
        rol = d / (crr_referencia * m_g) if crr_referencia else None
        linhas.append(LinhaArrasto(ay, ay / G, alfas[0], alfas[1], d, d_i, d_1, d / m_g, rol, ()))
        k += 1
    if not linhas:
        raise ValueError("Nenhum a_y da grade tem solução (nem a_y = 0).")
    ult = linhas[-1].ay_g
    rots = []
    if parou_antes is not None:
        rots.append(f"os ângulos de deriva deixam de resolver acima de {ult:.2f} g (a_y = {parou_antes / G:.2f} g "
                    f"sem solução): grade até o último a_y resolvido")
    elif ay_ate_ms2 is None:
        rots.append(f"sem saturação até {ult:.2f} g: grade até o último a_y resolvido")
    if ay_ate_ms2 is not None and ay_ate_ms2 > ay_max_g * G * (1 + PASSO_REL):
        rots.append(f"o limite pedido ({ay_ate_ms2 / G:.2f} g) passa de ay_max_g; grade cortada em {ay_max_g:.2f} g")
    if rots:
        linhas = [dataclasses.replace(l, rotulos=tuple(rots)) for l in linhas]
    return tuple(linhas)


# ---------------------------------------------------------------------------------------------------------------------
# Corridas do estudo: tornado de λ, pressão, combinação e métricas do pneu por pressão (Task 5)
# ---------------------------------------------------------------------------------------------------------------------
import json
from pathlib import Path

import comparacao_pressao as cmp
import equilibrio_linear as _el
import tire_model_static as ts
import tire_pressure as tp
from caso_pneu1 import CasoMontado

GRADE = {"ay_max_g": 2.0, "passo_g": 0.05, "n_alfa": 25}
PRESSAO_DO_CASO_PSI = 12.0
_CAMINHO_FATORES = Path(__file__).resolve().parent.parent / "data" / "varredura_pneu_exploratoria.json"


def _ler_fatores() -> dict[str, list[float]]:
    with open(_CAMINHO_FATORES, encoding="utf-8") as f:
        return {n: [float(v) for v in vs] for n, vs in json.load(f)["fatores"].items()}


FATORES_EXPLORATORIOS: dict[str, list[float]] = _ler_fatores()

# Rótulos da spec §9, um por linha, mais o aviso do fator_neutro (Global Constraints).
ROTULOS: tuple[str, ...] = (
    "caso de outro carro (T09/E03), demonstrativo, não o T11; valores editados marcados",
    "pneu R25B do TTC no lugar do R60A; μ absoluto do TTC não transferível",
    "pressão de ensaio ≠ pressão fria nem quente (a confirmar)",
    "amplitudes de λ exploratórias (EDR-055), não faixa do pneu",
    "banda heurística, não intervalo de confiança",
    "Validation = NOT_VALIDATED; VERIFIED não é validado",
    "Fx·κ fora (sem fonte); traçado do enduro a confirmar",
    "fator_neutro do caso (24_CURVA B34, 4/3 na V4.4) difere do 1,0 do relatorio_pressao: a regra do NEUTRO não é a "
    "daquele relatório",
)


def rigidez_eixos(caso: eq.CasoEquilibrio, *, formas: eq.Formas) -> tuple[float | None, float | None, str | None]:
    """(C_f, C_r [N/rad, de eixo], motivo de N/A) em a_y = 0 (D5): a mesma rigidez que o K usa.

    Chamada isolada à função privada `equilibrio_linear._rigidez_eixo` (spec §10), com Fz e γ de a_y = 0 e α_0 de
    `angulos_necessarios(caso, 0)`. Sem solução em a_y = 0 ou C_α ≤ 0, devolve None com o motivo.
    """
    alfa_0 = el.angulos_necessarios(caso, 0.0, formas=formas)
    if alfa_0 is None:
        return None, None, "os ângulos de deriva não resolvem em a_y = 0"
    fz0, gam0 = eq.cargas(caso, 0.0), eq.camber(caso, 0.0)
    c_f, _, m_f = _el._rigidez_eixo(caso, "F", fz0, gam0, alfa_0[0], formas=formas)
    c_r, _, m_r = _el._rigidez_eixo(caso, "R", fz0, gam0, alfa_0[1], formas=formas)
    motivos = [m for m in (m_f, m_r) if m is not None]
    return c_f, c_r, ("; ".join(motivos) if motivos else None)


@dataclass(frozen=True)
class LinhaCarro:
    """Uma corrida do carro (uma pressão, variante de KT e conjunto de λ), pronta para exibir.

    K em °/g (`para_graus_por_g`); C_f e C_r em N/rad de eixo; `ay_lim_g` = a_y/g."""
    rotulo_corrida: str
    pressao_psi: float
    variante_kt: str
    fatores: dict[str, float]
    ay_lim_ms2: float | None
    ay_lim_g: float | None
    veredito: str
    sentido_pior: str
    c_f_n_rad: float | None
    c_r_n_rad: float | None
    k_grau_g: float | None
    resolucao_ms2: float | None
    borda_alfa: bool
    robustez: tuple | None
    rotulos: tuple[str, ...]


def _sem_repeticao(*grupos) -> tuple[str, ...]:
    saida: list[str] = []
    for g in grupos:
        for s in g:
            if s not in saida:
                saida.append(s)
    return tuple(saida)


def linha_de_resultado(r: cmp.ResultadoCarro, *, formas: eq.Formas,
                       fatores: dict[str, float] | None = None) -> LinhaCarro:
    """Converte um ResultadoCarro em LinhaCarro (C_f e C_r por `rigidez_eixos` no caso rodado; K em °/g)."""
    fat = dict(fatores or {})
    c_f, c_r, _ = rigidez_eixos(r.caso, formas=formas)
    rot = (f"{r.pressao_psi:g} psi, variante {r.variante_kt}"
           + ("; " + ", ".join(f"{n} × {v:g}".replace(".", ",") for n, v in fat.items()) if fat else ""))
    return LinhaCarro(
        rotulo_corrida=rot, pressao_psi=r.pressao_psi, variante_kt=r.variante_kt, fatores=fat,
        ay_lim_ms2=r.ay_lim_ms2, ay_lim_g=None if r.ay_lim_ms2 is None else r.ay_lim_ms2 / G,
        veredito=r.veredito, sentido_pior=r.sentido_pior, c_f_n_rad=c_f, c_r_n_rad=c_r,
        k_grau_g=None if r.k_rad_ms2 is None else _el.para_graus_por_g(r.k_rad_ms2),
        resolucao_ms2=r.resolucao_ms2, borda_alfa=r.borda_alfa, robustez=r.robustez,
        rotulos=_sem_repeticao(ROTULOS, r.rotulos))


def _resultado_12psi(cm: CasoMontado, familia: ts.StaticTireFamily, fatores: dict[str, float],
                     rot_fatores: tuple[str, ...]) -> cmp.ResultadoCarro:
    """12 psi, variante a, com `fatores` (λ) por cima do ds de 12 psi de `perfil_ajustado` (como `comparar_carro`)."""
    ds_p, rot_p = cmp.perfil_ajustado(cm.caso.ds, familia.at_pressure(PRESSAO_DO_CASO_PSI), tp.teto_comum_fz(familia))
    if fatores:
        ds_p = eq.com_fatores(ds_p, fatores)
    caso_p = dataclasses.replace(cm.caso, ds=ds_p)
    par = eq.analise_par_dois_sentidos(caso_p, **GRADE, formas=cm.formas, fator_neutro=cm.fator_neutro)
    res = par[par["pior"] if par["pior"] != "empate" else "esquerda"]
    pk = _el.parcelas_k(caso_p, 0.0, formas=cm.formas)
    # Rótulos que `comparar_carro` anexa a cada corrida (roll steer, KT fixo, ds do caso × .tir de 12 psi).
    rs = cm.caso.roll_steer
    rot_rs = ("K com o roll steer do caso" if (rs["F"] != 0.0 or rs["R"] != 0.0)
              else "K com roll steer 0 = sem dado")
    rot_kt = ("KT do caso, fixo (variante a: só muda a aderência)",)
    difs = cmp.diferencas_fora_de_lambda(cm.caso.ds, familia.at_pressure(PRESSAO_DO_CASO_PSI))
    rot_difs = tuple(f"{n} do caso ({a:g}) difere do .tir de 12 psi ({b:g}); o ds de cada pressão usa o do .tir"
                     for n, (a, b) in difs.items())
    return cmp.ResultadoCarro(
        pressao_psi=PRESSAO_DO_CASO_PSI, variante_kt="a", ay_lim_ms2=res.ay_lim, sentido_pior=par["pior"],
        eixo_satura=cmp._EIXO_POR_VEREDITO.get(res.veredito), veredito=res.veredito, k_rad_ms2=pk.k_total,
        k_motivo=pk.motivo, resolucao_ms2=res.resolucao_ms2, borda_alfa=cmp._borda_alfa(res), robustez=None,
        rotulos=cmp.ROTULOS_FIXOS + (rot_rs,) + rot_kt + cm.rotulos + rot_p + rot_difs + rot_fatores,
        par=par, caso=caso_p)


def tornado(cm: CasoMontado, familia: ts.StaticTireFamily) -> tuple[LinhaCarro, ...]:
    """Base (todos os λ em 1,0) e cada λ de FATORES_EXPLORATORIOS em 0,8 e 1,2, um de cada vez (12 psi, variante a)."""
    aviso = ("λ exploratório (EDR-055), um fator por vez sobre o ds de 12 psi",)
    linhas = [linha_de_resultado(_resultado_12psi(cm, familia, {}, ()), formas=cm.formas)]
    for nome, valores in FATORES_EXPLORATORIOS.items():
        for v in valores:
            if v == 1.0:
                continue
            fat = {nome: v}
            linhas.append(linha_de_resultado(_resultado_12psi(cm, familia, fat, aviso), formas=cm.formas,
                                             fatores=fat))
    return tuple(linhas)


def pressao(cm: CasoMontado, familia: ts.StaticTireFamily) -> tuple[cmp.ResultadoCarro, ...]:
    """As 4 pressões da família, variantes a e b, com a grade do estudo (`comparar_carro`)."""
    return tuple(cmp.comparar_carro(cm.caso, familia, kt_caso_n_m=cm.kt_n_m, formas=cm.formas,
                                    fator_neutro=cm.fator_neutro, **GRADE))


def combinacao(cm: CasoMontado, familia: ts.StaticTireFamily) -> tuple[cmp.ResultadoCarro, ...]:
    """Igual a `pressao`, só na variante a e com a robustez de todos os λ (FATORES_EXPLORATORIOS). Cara: não é testada."""
    return tuple(cmp.comparar_carro(cm.caso, familia, fatores_lambda=FATORES_EXPLORATORIOS, formas=cm.formas,
                                    fator_neutro=cm.fator_neutro, **GRADE))


@dataclass(frozen=True)
class LinhaPneu:
    """Métricas do pneu num eixo e numa pressão. μ é o pico de α > 0 (`mu_y_pos`); `mu_y_borda`: limitante inferior."""
    pressao_psi: float
    eixo: str
    interpolado: bool
    fz_n: float
    c_alpha_n_rad: float
    mu_y_pico: float
    mu_y_borda: bool
    rotulos: tuple[str, ...]


def pneu_por_pressao(cm: CasoMontado, familia: ts.StaticTireFamily, passo_psi: float = 0.5) -> tuple[LinhaPneu, ...]:
    """Cα e μ_y de cada eixo, de 8 a 14 psi em `passo_psi`, na Fz estática e no camber estático médio do eixo.

    Fz e γ de eixo como em `tools/relatorio_pressao.py`; a Fz é limitada ao teto comum da família (com rótulo).
    Pressão fora dos perfis é interpolada (`avaliador_interpolado`)."""
    if passo_psi <= 0.0:
        raise ValueError("passo_psi deve ser > 0.")
    caso = cm.caso
    fz0 = eq.cargas(caso, 0.0)
    fz_eixo = {"F": 0.5 * (fz0["FL"] + fz0["FR"]), "R": 0.5 * (fz0["RL"] + fz0["RR"])}
    cam = {"F": 0.5 * (caso.camber_estatico_rad["FL"] + caso.camber_estatico_rad["FR"]),
           "R": 0.5 * (caso.camber_estatico_rad["RL"] + caso.camber_estatico_rad["RR"])}
    teto = tp.teto_comum_fz(familia)
    faixa = tp.faixa_comum(familia.profiles.values())
    n = int(round((14.0 - 8.0) / passo_psi))
    saida: list[LinhaPneu] = []
    for i in range(n + 1):
        q = 8.0 + i * passo_psi
        av = tp.avaliador_interpolado(familia, q)
        interp = not any(abs(q - p) < ts.PRESSURE_TOLERANCE_PSI for p in familia.pressures_psi)
        for eixo in ("F", "R"):
            fz = min(fz_eixo[eixo], teto)
            rot = ROTULOS + ((f"Fz estática do eixo {eixo} ({fz_eixo[eixo]:.0f} N) limitada ao teto comum da família "
                              f"({teto:g} N)",) if fz_eixo[eixo] > teto else ())
            m = tp.metricas_pneu(av, faixa, fz_n=fz, camber_rad=cam[eixo])
            saida.append(LinhaPneu(q, eixo, interp, fz, m.c_alpha_n_rad, m.mu_y_pos.mu, m.mu_y_pos.borda,
                                   _sem_repeticao(rot, m.rotulos)))
    return tuple(saida)
