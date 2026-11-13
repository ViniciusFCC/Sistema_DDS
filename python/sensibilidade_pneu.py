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
