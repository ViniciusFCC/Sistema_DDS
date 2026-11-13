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
import json
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import comparacao_pressao as cmp
import equilibrio as eq
import equilibrio_linear as el
import tire_model as tm
import tire_model_static as ts
import tire_pressure as tp
from caso_pneu1 import (  # noqa: F401  (D8: ler_caso, editar, salvar_caso, familia_ttc e caso_de_dados reexportados)
    CasoMontado, ValorUsado, caso_de_dados, editar, familia_ttc, ler_caso, salvar_caso, valores_usados)
from suspension_model import G

def ps(p: float) -> str:
    """Pressão para exibir: 1 casa, vírgula decimal. As pressões nominais dos .tir do TTC não são inteiras (7,999992,
    10,000062, 11,999987 e 14,000058 psi): mostrar 8,0, 10,0, 12,0 e 14,0 evita "7.99999 psi"."""
    return f"{p:.1f}".replace(".", ",")


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
    c_f, _, m_f = el._rigidez_eixo(caso, "F", fz0, gam0, alfa_0[0], formas=formas)
    c_r, _, m_r = el._rigidez_eixo(caso, "R", fz0, gam0, alfa_0[1], formas=formas)
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
    rot = (f"{ps(r.pressao_psi)} psi, variante {r.variante_kt}"
           + ("; " + ", ".join(f"{n} × {v:g}".replace(".", ",") for n, v in fat.items()) if fat else ""))
    return LinhaCarro(
        rotulo_corrida=rot, pressao_psi=r.pressao_psi, variante_kt=r.variante_kt, fatores=fat,
        ay_lim_ms2=r.ay_lim_ms2, ay_lim_g=None if r.ay_lim_ms2 is None else r.ay_lim_ms2 / G,
        veredito=r.veredito, sentido_pior=r.sentido_pior, c_f_n_rad=c_f, c_r_n_rad=c_r,
        k_grau_g=None if r.k_rad_ms2 is None else el.para_graus_por_g(r.k_rad_ms2),
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
    pk = el.parcelas_k(caso_p, 0.0, formas=cm.formas)
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


# ---------------------------------------------------------------------------------------------------------------------
# Regra de "muda decisão" (spec §6.3, D6 e D7), Resultado e estudo (Task 6)
# ---------------------------------------------------------------------------------------------------------------------
Muda = Literal["sim", "não", "não avaliado", "não medido aqui"]

# Nomes dos degraus 1 a 18, copiados da tabela de docs/pneu/roteiro-modelo-de-pneu.md.
DEGRAUS: dict[int, str] = {
    1: "A2 no carro",
    2: "Ajuste PP*/QPZ do PAC2002",
    3: "A3: pressão em operação",
    4: "B: transiente do pneu",
    5: "C: dinâmica do veículo",
    6: "Pneu substituto do T11",
    7: "Resistência ao rolamento",
    8: "λμ e λKy calibrados no skidpad",
    9: "Mz, trilha pneumática e Mx",
    10: "Deslizamento combinado validado",
    11: "Temperatura como estado, com ciclos térmicos",
    12: "Rigidez vertical do pneu",
    13: "Raio carregado e raio de rolamento",
    14: "Comparação com o OptimumTire",
    15: "Arrasto induzido pela deriva",
    16: "Estudo de sensibilidade",
    17: "Instrumentação e contrato de dados de ensaio",
    18: "Ciclo de engenharia (V5 do roadmap)",
}

_SIM, _NAO, _NAV, _NMA = "sim", "não", "não avaliado", "não medido aqui"
_VEREDITO_TEXTO = {eq.PUSH: "sair de frente", eq.LOOSE: "sair de traseira", eq.NEUTRO: "neutro no limite"}
_NOTA_REGRA = ("não muda = neste caso demonstrativo, nesta faixa exploratória; a banda é heurística, não intervalo "
               "de confiança")


@dataclass(frozen=True)
class Decisao:
    """Um degrau do roteiro e se ele muda alguma decisão do estudo. `criterios`: critério -> "estado: detalhe"."""
    degrau: int
    nome: str
    fatores: tuple[str, ...]
    muda: Muda
    criterios: dict[str, str]
    frase: str
    rotulos: tuple[str, ...]


def _agregar(estados: Sequence[str]) -> str:
    """D6: "sim" se algum critério dá sim; "não" se todos foram avaliados e dão não; senão "não avaliado"."""
    if _SIM in estados:
        return _SIM
    if estados and all(e == _NAO for e in estados):
        return _NAO
    return _NAV


def _detalhe(criterio: str) -> str:
    return criterio.split(": ", 1)[-1]


def _estado_de(detalhe: str) -> str:
    return detalhe.split(":", 1)[0]


# Motivos de `eq.veredito_robusto`, pelo próprio texto que ela devolve (não copiado à mão).
_MOTIVO_SINAL = eq.veredito_robusto([eq.PUSH, eq.LOOSE])[1]


def decidir_lambda(combinacao: Sequence[cmp.ResultadoCarro]) -> tuple[str, dict[str, str]]:
    """Critério 1 da spec §6.3 em cada pressão, pela robustez da combinação 3×3×3 de λ (D6).

    PUSH ou LOOSE puro -> "não"; NÃO CONCLUSIVO por "o sinal depende do pneu" -> "sim"; NÃO CONCLUSIVO por "N/A em
    parte da varredura (sem inversão de sinal)", N/A ou sem robustez -> "não avaliado" (sem inversão não há prova);
    agregados por D6."""
    criterios: dict[str, str] = {}
    estados: list[str] = []
    for r in sorted(combinacao, key=lambda x: x.pressao_psi):
        chave = f"robustez de λ a {ps(r.pressao_psi)} psi"
        if r.robustez is None:
            est, det = _NAV, "sem robustez calculada"
        else:
            ver, motivo = r.robustez[0], r.robustez[1]
            if ver in (eq.PUSH, eq.LOOSE):
                est = _NAO
            elif ver == eq.NAO_CONCLUSIVO and motivo == _MOTIVO_SINAL:
                est = _SIM
            elif ver == eq.NAO_CONCLUSIVO:
                est = _NAV       # N/A em parte da varredura, sem inversão de sinal: sem prova (spec §6.3)
            else:
                est = _NAV
            det = f"{ver}, {motivo}"
        estados.append(est)
        criterios[chave] = f"{est}: {det}"
    return _agregar(estados), criterios


def _distingue(v: cmp.Veredito) -> tuple[str, str]:
    """D7 (revista): conta como distinguida só a pressão decidível fora de `indistinguiveis` com banda medida.

    Pressão não resolvida (extremo, `medida=False`, Δ > banda) não prova nada: se for a única evidência, o critério
    fica "não avaliado". Com menos de 2 decidíveis, também "não avaliado" (o detalhe lista as não decidíveis)."""
    dec = [p for p, x in v.valores.items() if x is not None and p not in v.nao_decidiveis]
    nd = ", ".join(ps(p) for p in sorted(v.nao_decidiveis) if p in v.valores)
    nd += (", " if nd else "") + ", ".join(ps(p) for p, x in sorted(v.valores.items())
                                           if x is None and p not in v.nao_decidiveis)
    nd = nd.strip(", ")
    if len(dec) < 2:
        return _NAV, (f"menos de 2 pressões decidíveis ({len(dec)}); não decidíveis: {nd or 'nenhuma'} psi "
                      f"({v.desfecho})")
    fora = [q for q in dec if q not in v.indistinguiveis]
    resolvidas = [q for q in fora if v.bandas[q].medida]
    if resolvidas:
        return _SIM, f"as pressões se distinguem pela banda ({v.desfecho})"
    if fora:
        return _NAV, (f"a pressão {', '.join(ps(q) for q in sorted(fora))} psi difere, mas a banda ali é só "
                      "limite inferior: não resolvida")
    return _NAO, f"as pressões não se distinguem pela banda ({v.desfecho})"


def _veredito_por_pressao(resultados: Sequence[cmp.ResultadoCarro]) -> dict[float, str]:
    return {r.pressao_psi: r.veredito for r in sorted(resultados, key=lambda x: x.pressao_psi)}


def decidir_pressao(resultados_a: Sequence[cmp.ResultadoCarro], esc_ay: cmp.Escolha,
                    esc_ca: cmp.Escolha) -> tuple[str, dict[str, str]]:
    """Pressão (spec §6.3). Critério 1: os vereditos PUSH/LOOSE/NEUTRO diferem entre pressões (um N/A é "não
    avaliado" naquela pressão). Critério 2: D7 sobre `esc_ay` e sobre cada eixo de `esc_ca`. Agregado por D6."""
    ver = _veredito_por_pressao(resultados_a)
    com = {p: v for p, v in ver.items() if v != eq.NA}
    sem = [p for p, v in ver.items() if v == eq.NA]
    if len(set(com.values())) > 1:
        est1 = _SIM
        det1 = ", ".join(f"{v} a {ps(p)} psi" for p, v in com.items())
    elif sem or not com:
        est1 = _NAV
        det1 = ("N/A a " + ", ".join(ps(p) for p in sem) + " psi") if sem else "sem veredito"
    else:
        est1, det1 = _NAO, f"{next(iter(com.values()))} em todas as pressões"
    criterios = {"vereditos entre pressões": f"{est1}: {det1}"}
    estados = [est1]
    for nome, esc in (("a_y_lim", esc_ay), ("Cα", esc_ca)):
        for rot, v in esc.vereditos.items():
            est, det = _distingue(v)
            estados.append(est)
            criterios[f"{nome}, {rot}"] = f"{est}: {det}"
    return _agregar(estados), criterios


def decidir_kt(resultados: Sequence[cmp.ResultadoCarro]) -> tuple[str, dict[str, str]]:
    """KT (spec §6.3). Critério 1: o veredito de a e de b difere em alguma pressão. Critério 2: |ay_a − ay_b| passa da
    banda de `banda_carro` da variante a naquela pressão; banda ou ay None = "não avaliado" naquele nó."""
    a = {r.pressao_psi: r for r in resultados if r.variante_kt == "a"}
    b = {r.pressao_psi: r for r in resultados if r.variante_kt == "b"}
    if not a or not b:
        return _NAV, {"variantes a e b": "não avaliado: falta a variante " + ("b" if a else "a")}
    bandas = cmp.banda_carro(list(a.values()))
    criterios: dict[str, str] = {}
    estados: list[str] = []
    for p in sorted(set(a) & set(b)):
        ra, rb = a[p], b[p]
        if eq.NA in (ra.veredito, rb.veredito):
            est1, det1 = _NAV, f"{ra.veredito} (a) e {rb.veredito} (b)"
        else:
            est1 = _SIM if ra.veredito != rb.veredito else _NAO
            det1 = f"{ra.veredito} (a) e {rb.veredito} (b)"
        bd = bandas.get(p)
        if ra.ay_lim_ms2 is None or rb.ay_lim_ms2 is None or bd is None or bd.valor is None:
            est2, det2 = _NAV, "a_y_lim ou banda indisponível"
        else:
            dif = abs(ra.ay_lim_ms2 - rb.ay_lim_ms2)
            est2 = _SIM if dif > bd.valor else _NAO
            det2 = f"|Δa_y_lim| = {dif:.3g} m/s² contra a banda de {bd.valor:.3g} m/s²"
        estados += [est1, est2]
        criterios[f"veredito de a e b a {ps(p)} psi"] = f"{est1}: {det1}"
        criterios[f"a_y_lim de a e b a {ps(p)} psi"] = f"{est2}: {det2}"
    return _agregar(estados), criterios


def _frase_pressao(estado: str, criterios: dict[str, str], resultados_a: Sequence[cmp.ResultadoCarro]) -> str:
    ver = _veredito_por_pressao(resultados_a)
    com = {p: v for p, v in ver.items() if v != eq.NA}
    if estado == _SIM:
        if len(set(com.values())) > 1:
            ps = sorted(com)
            p0 = ps[0]
            p1 = next(p for p in ps if com[p] != com[p0])
            return (f"a pressão muda o veredito: o carro passa de {_VEREDITO_TEXTO.get(com[p0], com[p0])} "
                    f"({ps(p0)} psi) para {_VEREDITO_TEXTO.get(com[p1], com[p1])} ({ps(p1)} psi)")
        return "a pressão muda o a_y_lim ou o Cα além da banda heurística: nem todas as pressões se equivalem"
    if estado == _NAO:
        return f"a pressão não muda a decisão: {_NOTA_REGRA}"
    if not com:
        return "não avaliado: o carro não chega ao limite até 2 g em nenhuma pressão"
    pend = next((_detalhe(c) for c in criterios.values() if _estado_de(c) == _NAV), "critério sem avaliação")
    return f"não avaliado: {pend}; nenhum critério avaliado deu sim"


def _frase_lambda(estado: str, criterios: dict[str, str]) -> str:
    """Frase dos degraus 6 e 8: uma entrada por pressão, com o rótulo em psi já formatado (ver `ps`)."""
    suj = "o λ exploratório (LMUY, LFZO, LKY)"

    def entradas(alvo: str) -> str:
        return "; ".join(f"{k.removeprefix('robustez de λ ')}: {_detalhe(c)}" for k, c in criterios.items()
                         if _estado_de(c) == alvo)
    if estado == _SIM:
        return f"{suj} muda a decisão: {entradas(_SIM)}"
    if estado == _NAO:
        return f"{suj} não muda a decisão: {_NOTA_REGRA}"
    pend = entradas(_NAV)
    return (f"não avaliado ({suj}): {pend or 'sem critério avaliado'}; nenhum critério avaliado deu sim")


def _frase_generica(nome: str, estado: str, criterios: dict[str, str]) -> str:
    if estado == _SIM:
        return f"{nome} muda a decisão: " + "; ".join(_detalhe(c) for c in criterios.values()
                                                    if _estado_de(c) == _SIM)[:300]
    if estado == _NAO:
        return f"{nome} não muda a decisão: {_NOTA_REGRA}"
    pend = [_detalhe(c) for c in criterios.values() if _estado_de(c) == _NAV]
    return f"não avaliado: {pend[0] if pend else 'sem critério avaliado'}; nenhum critério avaliado deu sim"


_FATORES_DE_DEGRAU: dict[int, tuple[str, ...]] = {
    1: ("Pressão",), 2: ("Pressão",), 3: ("Pressão",),
    6: ("LMUY", "LFZO"), 8: ("LMUY", "LFZO", "LKY"),
    12: ("KT",),
    7: ("Arrasto induzido × resistência ao rolamento",), 15: ("Arrasto induzido × resistência ao rolamento",),
}
_ROT_DEGRAU: dict[int, str] = {
    1: "pressão de ensaio ≠ pressão fria nem quente (a confirmar); só 8 a 14 psi",
    2: "interpolação entre perfis ajustados separadamente, não o ajuste PP*/QPZ",
    3: "pressão fria de calibração; a pressão quente de pista e a temperatura não estão no modelo",
    6: "λ exploratório (EDR-055), não o R60A",
    7: "sem Crr com fonte e sem regra de decisão para energia (D6)",
    8: "λ exploratório (EDR-055), não calibrado no skidpad",
    12: "KT do caso × VERTICAL_STIFFNESS do perfil do R25B",
    15: "o arrasto induzido sai como tamanho de efeito (D6); Fx·κ fora (sem fonte)",
    16: "este estudo",
}


_SUFIXO_DEGRAU: dict[int, str] = {
    2: " (nos perfis interpolados entre os .tir, não num ajuste PP*/QPZ)",
    3: " (pressão de ensaio, a fria; pressão quente e temperatura não estão no modelo)",
}


def tabela_decisoes(lam: tuple[str, dict[str, str]], pres: tuple[str, dict[str, str]],
                    kt: tuple[str, dict[str, str]], *, frases: dict[int, str] | None = None) -> tuple[Decisao, ...]:
    """As 18 decisões, uma por degrau: 6 e 8 recebem `lam`; 1, 2 e 3, `pres`; 12, `kt`; 7 e 15 ficam "não avaliado"
    (D6); 16 é "este estudo" ("não medido aqui"); os demais, "não medido aqui" (spec §6.1). `frases` troca a frase
    de um degrau (a padrão só usa o que foi medido)."""
    fr = frases or {}
    saida: list[Decisao] = []
    for g, nome in DEGRAUS.items():
        if g in (6, 8):
            est, cri = lam
        elif g in (1, 2, 3):
            est, cri = pres
        elif g == 12:
            est, cri = kt
        elif g in (7, 15):
            est, cri = _NAV, {"arrasto × rolamento": "não avaliado: sem Crr com fonte e sem regra de decisão para "
                                                     "energia; o arrasto sai como tamanho de efeito"}
        else:
            est, cri = _NMA, {}
        if est == _NMA:
            frase = "este estudo" if g == 16 else "o degrau não entra neste estudo (spec §6.1)"
        elif g in (7, 15):
            frase = ("não avaliado: sem Crr com fonte e sem regra de decisão para energia; o arrasto sai como "
                     "tamanho de efeito")
        else:
            frase = fr.get(g) or _frase_generica(nome, est, cri)
        if g in _SUFIXO_DEGRAU and est != _NMA:
            frase += _SUFIXO_DEGRAU[g]
        rot = ROTULOS + ((_ROT_DEGRAU[g],) if g in _ROT_DEGRAU else ())
        saida.append(Decisao(g, nome, _FATORES_DE_DEGRAU.get(g, ()), est, cri, frase, rot))
    return tuple(saida)


def _json(x):
    """Converte para tipos JSON: dataclass -> dict, tupla -> lista, chaves de dict -> str."""
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: _json(getattr(x, f.name)) for f in dataclasses.fields(x)}
    if isinstance(x, dict):
        return {str(k): _json(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [_json(v) for v in x]
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    raise TypeError(f"valor sem tipo JSON: {type(x).__name__}")


@dataclass(frozen=True)
class Resultado:
    """Saída de `estudo`. `combinacao` é None com `rapido=True`. `tempos_s`: tempo medido de cada corrida."""
    valores: tuple[ValorUsado, ...]
    tornado: tuple[LinhaCarro, ...]
    pressao: tuple[LinhaCarro, ...]
    combinacao: tuple[LinhaCarro, ...] | None
    pneu: tuple[LinhaPneu, ...]
    arrasto: tuple[LinhaArrasto, ...]
    decisoes: tuple[Decisao, ...]
    rotulos: tuple[str, ...]
    tempos_s: dict[str, float]

    def para_dict(self) -> dict:
        """Só tipos JSON (sem `caso` nem `par`, que as linhas não guardam)."""
        return _json(self)

    def resumo(self) -> list[str]:
        """Uma frase por decisão."""
        return [f"Degrau {d.degrau} ({d.nome}): {d.muda}. {d.frase}" for d in self.decisoes]


def estudo(cm: CasoMontado, familia: ts.StaticTireFamily, rapido: bool = False) -> Resultado:
    """Roda as corridas (tornado, pressão, combinação, pneu, arrasto) e monta as 18 decisões.

    `rapido=True`: sem a combinação (`combinacao=None`) e a decisão de λ fica "não avaliado". O arrasto vai do
    a_y = 0 até o a_y_lim de 12 psi, variante a (D4); sem ele, até `GRADE["ay_max_g"]` com rótulo."""
    tempos: dict[str, float] = {}

    def medir(nome, fn):
        t0 = time.perf_counter()
        r = fn()
        tempos[nome] = time.perf_counter() - t0
        return r

    torn = medir("tornado", lambda: tornado(cm, familia))
    pres_res = medir("pressao", lambda: pressao(cm, familia))
    comb_res = None if rapido else medir("combinacao", lambda: combinacao(cm, familia))
    pneu = medir("pneu", lambda: pneu_por_pressao(cm, familia))
    r12 = next((r for r in pres_res if r.variante_kt == "a" and abs(r.pressao_psi - PRESSAO_DO_CASO_PSI) < 1e-6), None)
    ay12 = None if r12 is None else r12.ay_lim_ms2
    arr = medir("arrasto", lambda: arrasto_induzido(cm.caso, formas=cm.formas, ay_ate_ms2=ay12,
                                                    ay_max_g=GRADE["ay_max_g"]))

    res_a = [r for r in pres_res if r.variante_kt == "a"]
    fz0 = eq.cargas(cm.caso, 0.0)
    fz_eixo = {"F": 0.5 * (fz0["FL"] + fz0["FR"]), "R": 0.5 * (fz0["RL"] + fz0["RR"])}
    cam = {"F": 0.5 * (cm.caso.camber_estatico_rad["FL"] + cm.caso.camber_estatico_rad["FR"]),
           "R": 0.5 * (cm.caso.camber_estatico_rad["RL"] + cm.caso.camber_estatico_rad["RR"])}
    esc_ay = cmp.escolher_pressao("a_y_lim", resultados_carro=pres_res)
    esc_ca = cmp.escolher_pressao("C_alpha_operacao", family=familia, fz_estatica_eixo_n=fz_eixo,
                                  camber_eixo_rad=cam)
    pres = decidir_pressao(res_a, esc_ay, esc_ca)
    kt = decidir_kt(pres_res)
    if comb_res is None:
        lam = (_NAV, {"robustez de λ": "não avaliado: combinação não rodada (--rapido)"})
    else:
        lam = decidir_lambda(comb_res)
    frases = {g: _frase_pressao(pres[0], pres[1], res_a) for g in (1, 2, 3)}
    if comb_res is not None:
        frases.update({6: _frase_lambda(*lam), 8: _frase_lambda(*lam)})
    if comb_res is None:
        frases.update({6: "não avaliado: combinação não rodada (--rapido)",
                       8: "não avaliado: combinação não rodada (--rapido)"})
    decisoes = tabela_decisoes(lam, pres, kt, frases=frases)
    return Resultado(
        valores=cm.valores, tornado=torn,
        pressao=tuple(linha_de_resultado(r, formas=cm.formas) for r in pres_res),
        combinacao=None if comb_res is None else tuple(linha_de_resultado(r, formas=cm.formas) for r in comb_res),
        pneu=pneu, arrasto=arr, decisoes=decisoes, rotulos=ROTULOS, tempos_s=tempos)
