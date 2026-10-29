"""
Raio do skidpad (incremento 7, Task 2; EDR-067, SUS-1009 a 1011; spec 2026-10-29-inc7-fisica-planilha-design.md §3).

Centro da curva único, na linha do eixo traseiro (U8). Referencial ISO 8855, curva à esquerda: origem no ponto médio do
eixo traseiro, X para a frente, Y para a esquerda; rodas dianteiras em (L, ±t_f/2), traseiras em (0, ±t_r/2); CG em
(b, 0); centro C = (0, R_c). O raio do CG é R = sqrt(b² + R_c²).

Três modos do R: "linha_central" (R = (D_int + D_ext)/4, o raio do CG na faixa), "rente_aos_cones" (limite geométrico de
ocupação: a roda interna de cada eixo fica a, no mínimo, D_int/2 + meia largura do pneu do centro) e "manual" (R digitado).
Limitações: o skidpad real tem entrada e saída, e o R é único; o modo rente aos cones não é a trajetória real. Os
diâmetros são entradas com fonte, não constantes físicas: a equipe corrige sem planilha nova.
"""
import math
from dataclasses import dataclass

import atualizar_planilha

# Formula SAE Rules 2026 v1.0, D.10.1.1: círculos internos de 15,25 m e externos de 21,25 m (FSAE Brasil: inc. 9).
D_INTERNO_M = 15.25
D_EXTERNO_M = 21.25
FONTE_DIAMETROS = "Formula SAE Rules 2026 v1.0 (10/09/2025), D.10.1.1"
ORIGEM_MEIA_LARGURA = atualizar_planilha.TTC     # "◐ Provisório (.tir TTC)"

MODOS = ("linha_central", "rente_aos_cones", "manual")
MOTIVO_BITOLA_TRASEIRA = "bitola traseira vazia: R rente aos cones a confirmar"
MOTIVO_MANUAL_VAZIO = "R manual vazio: a confirmar"
MOTIVO_SEM_MEIA_LARGURA = "sem a meia largura do pneu (a confirmar)"
TOL_EMPATE_M = 1e-9


@dataclass(frozen=True)
class RaioRente:
    raio_m: float | None          # R do CG
    raio_c_m: float | None        # R_c, distância do centro da curva à linha do eixo traseiro
    eixo: str | None              # "traseiro", "dianteiro" ou "empate"
    motivo: str | None            # por que não há número
    sem_meia_largura: bool        # meia largura vazia: entrou 0


def raio_linha_central(d_int: float, d_ext: float) -> float:
    """Raio do CG na linha central da faixa: (D_int + D_ext)/4."""
    return (d_int + d_ext) / 4.0


def raio_rente_aos_cones(d_int: float, L: float, b: float, t_f: float, t_r: float | None,
                         meia_largura: float | None) -> RaioRente:
    """R com a roda interna de cada eixo encostada no círculo interno, dilatado pela meia largura do pneu (R_in').

    Traseira interna: R_c >= R_in' + t_r/2. Dianteira interna: sqrt(L² + (R_c - t_f/2)²) >= R_in', isto é,
    R_c >= t_f/2 + sqrt(R_in'² - L²) (só se R_in' > L). R_c é o máximo dos dois; R = sqrt(b² + R_c²)."""
    if t_r is None:
        return RaioRente(None, None, None, MOTIVO_BITOLA_TRASEIRA, False)
    sem_w = meia_largura is None
    r_in = d_int / 2.0 + (0.0 if sem_w else meia_largura)
    lim_tras = r_in + t_r / 2.0
    lim_diant = t_f / 2.0 + math.sqrt(r_in**2 - L**2) if r_in > L else -math.inf
    if abs(lim_tras - lim_diant) <= TOL_EMPATE_M:
        eixo = "empate"
    else:
        eixo = "traseiro" if lim_tras > lim_diant else "dianteiro"
    r_c = max(lim_tras, lim_diant)
    return RaioRente(math.hypot(b, r_c), r_c, eixo, None, sem_w)


def meia_largura_do_tir(ds) -> float:
    """Meia largura de seção do pneu: WIDTH/2 do .tir em uso."""
    try:
        return ds.p["WIDTH"] / 2.0
    except KeyError:
        raise ValueError("WIDTH ausente no .tir") from None


def raio(modo: str, *, d_int, d_ext, L, b, t_f, t_r, meia_largura, r_manual) -> tuple[float | None, str | None]:
    """(R, motivo) do modo escolhido. Sem número, R é None e o motivo diz o que falta."""
    if modo == "linha_central":
        return raio_linha_central(d_int, d_ext), None
    if modo == "rente_aos_cones":
        r = raio_rente_aos_cones(d_int, L, b, t_f, t_r, meia_largura)
        if r.raio_m is None:
            return None, r.motivo
        return r.raio_m, (MOTIVO_SEM_MEIA_LARGURA if r.sem_meia_largura else None)
    if modo == "manual":
        return (None, MOTIVO_MANUAL_VAZIO) if r_manual is None else (r_manual, None)
    raise ValueError(f"modo do raio inválido: {modo!r}; use um de {MODOS}")
