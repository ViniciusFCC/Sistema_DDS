"""
Subprojeto A (pneu com variação de pressão): A1-carro, o caso do equilíbrio rodado com o `ds` de cada pressão.

Base: docs/superpowers/specs/2026-11-02-pneu-estado-design.md (§5, §7), EDR-071.

`comparar_carro` pega o caso (já lido, com os λ do usuário) e, por perfil da família (8, 10, 12 e 14 psi), monta um
`ds` novo (`perfil_ajustado`: coeficientes do perfil, λ ≠ 1 do caso copiados, FZMAX no teto comum) e roda
`equilibrio.analise_par_dois_sentidos`. Duas variantes de rigidez vertical: "a" (KT do caso, fixo; só muda a
aderência) e "b" (KT = VERTICAL_STIFFNESS do perfil; muda também o K_φ de cada eixo).

Rótulos em toda saída: R25B != R60A; μ absoluto do TTC não transferível; pressão de ensaio != pressão fria (a
confirmar); Validation = NOT_VALIDATED; caso demonstrativo T09/E03 com coeficientes de 12 psi como linha de base, não
o T11. A banda e a escolha ficam em outra unidade; aqui só se compara.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import equilibrio as eq
import equilibrio_linear as eql
import tire_model as _base
import tire_model_static as ts
import tire_pressure as tp

ROTULOS_FIXOS = (
    "R25B ≠ R60A (nem a tendência se transfere com certeza)",
    "μ absoluto do TTC não transferível",
    "pressão de ensaio ≠ pressão fria (a confirmar)",
    "Validation = NOT_VALIDATED",
    "caso demonstrativo T09/E03 com coeficientes de 12 psi como linha de base, não o T11",
    "resolucao_ms2 é tolerância numérica, não critério de diferença",
    "ds único nas 4 rodas; sem raio carregado, altura de rodagem e cinemática decorrente",
    "Fy em α = 0 como no modelo (invertido pelo espelhamento nas rodas esquerdas)",
)
_BORDA = "pico na borda da grade de α"
_EIXO_POR_VEREDITO = {eq.PUSH: "F", eq.LOOSE: "R", eq.NEUTRO: "ambos"}


def _lambdas_do_caso(ds_caso: _base.TireDataset) -> dict[str, float]:
    """λ de FATORES_LAMBDA com valor ≠ 1 no ds do caso (ausente conta como 1)."""
    return {n: float(ds_caso.p[n]) for n in eq.FATORES_LAMBDA if n in ds_caso.p and ds_caso.p[n] != 1.0}


def perfil_ajustado(ds_caso: _base.TireDataset, profile: ts.StaticTireProfile,
                    teto_fz_n: float) -> tuple[_base.TireDataset, tuple[str, ...]]:
    """`TireDataset` novo com os coeficientes do perfil, os λ ≠ 1 do caso (valor absoluto) e FZMAX limitado ao teto comum.

    Nada é mutado: `p` é um dict novo. Um λ ≠ 1 do caso que não exista no perfil levanta ValueError com o nome.
    Devolve também os rótulos (λ copiados; FZMAX reescrito).
    """
    p = dict(profile.dataset.p)
    rotulos = []
    lam = _lambdas_do_caso(ds_caso)
    for nome, valor in lam.items():
        if nome not in p:
            raise ValueError(f"λ {nome} = {valor:g} do caso não existe no perfil de {profile.inflation_psi:.0f} psi: "
                             "não há onde copiá-lo.")
        p[nome] = valor
    if lam:
        rotulos.append("λ do caso copiados (valor absoluto): "
                       + "; ".join(f"{n} = {v:g}".replace(".", ",") for n, v in lam.items()))
    if p["FZMAX"] > teto_fz_n:
        rotulos.append(f"FZMAX {p['FZMAX']:g} → {teto_fz_n:g} N (teto comum da família)")
        p["FZMAX"] = float(teto_fz_n)
    ds = dataclasses.replace(profile.dataset, p=p, strings=dict(profile.dataset.strings))
    return ds, tuple(rotulos)


def diferencas_fora_de_lambda(ds_caso: _base.TireDataset, profile: ts.StaticTireProfile,
                              teto_fz_n: float) -> dict[str, tuple[float, float]]:
    """Coeficientes do caso ≠ do perfil, fora de FATORES_LAMBDA e de FZMAX: {nome: (caso, perfil)}.

    O `perfil_ajustado` troca esses coeficientes pelos do `.tir` sem aviso; esta função é o aviso. Só olha nomes que
    existem nos dois. `teto_fz_n` entra só na assinatura (FZMAX já fica de fora, porque é reescrito de propósito).
    """
    del teto_fz_n
    return {n: (float(v), float(profile.parameters[n])) for n, v in ds_caso.p.items()
            if n not in eq.FATORES_LAMBDA and n != "FZMAX" and n in profile.parameters
            and float(v) != float(profile.parameters[n])}


def kphi_com_kt(kphi_n_m_rad: float, track_m: float, kt_antigo_n_m: float, kt_novo_n_m: float) -> float:
    """K_φ do eixo com outro KT: inverte K_φ = série(k_susp, KT·t²/2) para achar k_susp e refaz com o KT novo."""
    kt_phi_antigo = kt_antigo_n_m * track_m ** 2 / 2
    kt_phi_novo = kt_novo_n_m * track_m ** 2 / 2
    if not (kphi_n_m_rad > 0 and kt_phi_antigo > kphi_n_m_rad and kt_phi_novo > 0):
        raise ValueError(f"K_φ = {kphi_n_m_rad:g} deve ser > 0 e menor que KT·t²/2 = {kt_phi_antigo:g} (o pneu em "
                         "série não pode ser mais mole que o eixo inteiro).")
    k_susp = kphi_n_m_rad * kt_phi_antigo / (kt_phi_antigo - kphi_n_m_rad)
    return k_susp * kt_phi_novo / (k_susp + kt_phi_novo)


@dataclass(frozen=True)
class ResultadoCarro:
    """Uma pressão numa variante de KT. `par` é a saída de analise_par_dois_sentidos e `caso` o caso rodado."""
    pressao_psi: float
    variante_kt: str
    ay_lim_ms2: float | None
    sentido_pior: str
    eixo_satura: str | None
    veredito: str
    k_rad_ms2: float | None
    k_motivo: str | None
    resolucao_ms2: float | None
    borda_alfa: bool
    robustez: tuple | None
    rotulos: tuple[str, ...]
    par: dict
    caso: eq.CasoEquilibrio


def _borda_alfa(res: eq.ResultadoPar) -> bool:
    return any(c.motivo == _BORDA for ln in res.linhas if res.ay_lim is None or ln.ay_ms2 <= res.ay_lim
               for c in (ln.cap_f, ln.cap_r))


def comparar_carro(caso: eq.CasoEquilibrio, family: ts.StaticTireFamily, *,
                   kt_caso_n_m: Mapping[str, float] | None = None,
                   fatores_lambda: Mapping[str, Sequence[float]] | None = None,
                   **kw_analise) -> list[ResultadoCarro]:
    """Roda o caso com o ds de cada pressão (ordem crescente): variante "a" e, com `kt_caso_n_m`, a "b".

    `kt_caso_n_m` = {"F": KTF, "R": KTR} [N/m], os KT com que o K_φ do caso foi calculado. `fatores_lambda` liga a
    robustez (varredura_pneu), com a hipótese de que a perda TTC→pista é a mesma em todas as pressões.
    `**kw_analise` (ay_max_g, passo_g, n_alfa, formas…) vai a analise_par_dois_sentidos e a varredura_pneu.
    """
    if not isinstance(family, ts.StaticTireFamily):
        raise TypeError("passe a família de perfis (load_profile_family), não um .tir: caso_da_planilha_v41 grava a "
                        "10_TIRE (coeficientes de 12 psi) por cima do .tir e devolveria 12 psi em silêncio")
    teto = tp.teto_comum_fz(family)
    base12 = family.at_pressure(12.0)
    difs = diferencas_fora_de_lambda(caso.ds, base12, teto)
    rot_difs = tuple(f"{n} do caso ({a:g}) difere do .tir de 12 psi ({b:g}); o ds de cada pressão usa o do .tir"
                     for n, (a, b) in difs.items())
    rs = caso.roll_steer
    rot_rs = ("K com o roll steer do caso" if (rs["F"] != 0.0 or rs["R"] != 0.0)
              else "K com roll steer 0 = sem dado")
    formas = {"formas": kw_analise["formas"]} if "formas" in kw_analise else {}
    variantes = ["a"] + (["b"] if kt_caso_n_m is not None else [])
    saida = []
    for var in variantes:
        for q in family.pressures_psi:
            prof = family.profiles[q]
            ds_p, rot_p = perfil_ajustado(caso.ds, prof, teto)
            caso_p = dataclasses.replace(caso, ds=ds_p)
            rot_kt = ("KT do caso, fixo (variante a: só muda a aderência)",)
            if var == "b":
                vs, origem_vs = tp.rigidez_vertical(prof)
                cfg = dataclasses.replace(
                    caso.cfg,
                    roll_stiffness_front=kphi_com_kt(caso.cfg.roll_stiffness_front, caso.cfg.track_front,
                                                     kt_caso_n_m["F"], vs),
                    roll_stiffness_rear=kphi_com_kt(caso.cfg.roll_stiffness_rear, caso.cfg.track_rear,
                                                    kt_caso_n_m["R"], vs))
                caso_p = dataclasses.replace(caso_p, cfg=cfg)
                rot_kt = (f"KT = VERTICAL_STIFFNESS do perfil ({vs:g} N/m, {origem_vs}) nas 4 "
                          "rodas (variante b: muda também o K_φ)",)
            par = eq.analise_par_dois_sentidos(caso_p, **kw_analise)
            res = par[par["pior"] if par["pior"] != "empate" else "esquerda"]
            pk = eql.parcelas_k(caso_p, 0.0, **formas)
            robustez, rot_rob = None, ()
            if fatores_lambda:
                robustez = eq.veredito_robusto([r.veredito for _, r in eq.varredura_pneu(caso_p, fatores_lambda,
                                                                                         **kw_analise)])
                rot_rob = ("hipótese: a perda TTC→pista é a mesma em todas as pressões",)
            saida.append(ResultadoCarro(
                pressao_psi=q, variante_kt=var, ay_lim_ms2=res.ay_lim, sentido_pior=par["pior"],
                eixo_satura=_EIXO_POR_VEREDITO.get(res.veredito), veredito=res.veredito, k_rad_ms2=pk.k_total,
                k_motivo=pk.motivo, resolucao_ms2=res.resolucao_ms2, borda_alfa=_borda_alfa(res),
                robustez=robustez, rotulos=ROTULOS_FIXOS + (rot_rs,) + rot_kt + rot_p + rot_difs + rot_rob,
                par=par, caso=caso_p))
    return saida


# ---------------------------------------------------------------------------------------------------------
# A1-escolha (spec §8): bandas heurísticas e regra simétrica
# ---------------------------------------------------------------------------------------------------------
CRITERIOS = {"a_y_lim": "máximo", "C_alpha_operacao": "máximo"}
CRITERIOS_TBD = ("K", "TARGET-006", "TARGET-007")
# Piso da banda do pneu, relativo ao valor: escolha heurística declarada, dominada pelo LOO.
PISO_NUMERICO_REL = 1e-6
_ROT_EXTREMO = "limite inferior (banda não medida)"
_ROT_INDISP = "banda indisponível"
_ROT_BANDA = "banda heurística, não intervalo de confiança"
_ROT_SEM_ASSIM = "assimetria não se aplica ao Cα: a derivada em α = 0 não tem lado"
_MOTIVO_BORDA = "pico na borda da grade de α: valor é limitante inferior"


@dataclass(frozen=True)
class Banda:
    """Faixa heurística (nunca intervalo de confiança). `valor` None = banda indisponível; `medida` False nos
    extremos (8 e 14 psi), onde o valor é o maior |LOO| interno (limite inferior)."""
    valor: float | None
    medida: bool
    componentes: Mapping[str, float]
    rotulo: str


def _bandas_com_extremos(internas: Mapping[float, Banda], loo: Mapping[float, tp.ErroLOO],
                         chaves: Sequence[float]) -> dict[float, Banda]:
    """`internas` tem uma Banda por nó interno (valor None se o LOO não existe); os dois extremos recebem o
    maior |LOO| interno disponível, com medida=False, ou valor None se nenhum nó interno tem LOO."""
    ps = sorted(chaves)
    saida: dict[float, Banda] = {}
    maior = max((abs(e.erro) for e in loo.values()), default=None)
    for i, p in enumerate(ps):
        if 0 < i < len(ps) - 1:
            saida[p] = internas[p]
        elif maior is None:
            saida[p] = Banda(None, False, {}, _ROT_INDISP)
        else:
            saida[p] = Banda(maior, False, {"loo_max_interno": maior}, _ROT_EXTREMO)
    return saida


def banda_carro(resultados: Sequence[ResultadoCarro], grandeza: str = "ay_lim_ms2") -> dict[float, Banda]:
    """Banda por pressão, de uma variante de KT só: nó interno = max(|LOO|, resolucao_ms2), com o LOO do carro
    obtido interpolando as saídas `grandeza` dos vizinhos (`tire_pressure.erro_loo`). A assimetria fica fora
    (já está no "sentido pior")."""
    if not resultados:
        return {}
    if len({r.variante_kt for r in resultados}) > 1:
        raise ValueError("banda_carro recebe uma variante de KT só; separe 'a' e 'b' antes "
                         "(escolher_pressao faz isso)")
    if len({r.pressao_psi for r in resultados}) != len(resultados):
        raise ValueError("pressões repetidas nos resultados")
    por_p = {r.pressao_psi: r for r in resultados}
    loo = tp.erro_loo({p: getattr(r, grandeza) for p, r in por_p.items()})
    internas: dict[float, Banda] = {}
    for p, r in por_p.items():
        if p in loo:
            res = r.resolucao_ms2 or 0.0
            internas[p] = Banda(max(abs(loo[p].erro), res), True,
                                {"loo": abs(loo[p].erro), "resolucao_ms2": res}, _ROT_BANDA)
        else:
            internas[p] = Banda(None, True, {}, _ROT_INDISP)
    return _bandas_com_extremos(internas, loo, list(por_p))


def banda_pneu(valores: Mapping[float, float], assimetria: Mapping[float, float] | None) -> dict[float, Banda]:
    """Banda por pressão de uma métrica do pneu: nó interno = max(|LOO|, assimetria ±α, PISO_NUMERICO_REL·|X|).
    `assimetria` None = componente ausente e declarado (não se aplica ao Cα)."""
    loo = tp.erro_loo(valores)
    internas: dict[float, Banda] = {}
    for p, x in valores.items():
        if p not in loo:
            continue
        comp = {"loo": abs(loo[p].erro), "piso_numerico": PISO_NUMERICO_REL * abs(x)}
        rot = _ROT_BANDA
        if assimetria is None:
            rot += "; " + _ROT_SEM_ASSIM
        elif p in assimetria:
            comp["assimetria"] = abs(assimetria[p])
        internas[p] = Banda(max(comp.values()), True, comp, rot)
    return _bandas_com_extremos(internas, loo, list(valores))


@dataclass(frozen=True)
class Veredito:
    melhor: float | None
    indistinguiveis: tuple[float, ...]
    nao_decidiveis: Mapping[float, str]
    desfecho: str
    valores: Mapping[float, float | None]
    bandas: Mapping[float, Banda]


def _ps(ps: Sequence[float]) -> str:
    return ", ".join(f"{p:.3g}" for p in ps)


def decidir(valores: Mapping[float, float | None], bandas: Mapping[float, Banda],
            nao_decidiveis: Mapping[float, str]) -> Veredito:
    """Regra simétrica da spec §8, sentido "máximo".

    1. Não decidível: valor None, pressão em `nao_decidiveis` (ex.: borda de α) ou banda indisponível. Fica
       listada com o motivo; não é excluída.
    2. Entre as decidíveis, x* = maior valor; indistinguíveis = {q : |x* − x_q| ≤ max(banda_x*, banda_q)}.
    3. melhor = x* só se indistinguíveis == {x*}, a banda de x* é medida (8 e 14 psi nunca sozinhas) e não há
       pressão não decidível (com pico na borda o valor é limitante inferior e ela pode superar x*).
    """
    nd: dict[float, str] = dict(nao_decidiveis)
    for p, v in valores.items():
        if p in nd:
            continue
        b = bandas.get(p)
        if v is None:
            nd[p] = "valor N/A"
        elif b is None or b.valor is None:
            nd[p] = _ROT_INDISP
    dec = {p: v for p, v in valores.items() if p not in nd and v is not None}

    def pronto(melhor, indist, desfecho):
        return Veredito(melhor, tuple(indist), nd, desfecho, dict(valores), dict(bandas))

    if not dec:
        return pronto(None, (), "nenhuma pressão decidível")
    p_star = max(dec, key=lambda p: dec[p])
    b_star = bandas[p_star].valor
    indist = sorted(q for q in dec if abs(dec[p_star] - dec[q]) <= max(b_star, bandas[q].valor))
    sufixo = f"; não decidíveis: {_ps(sorted(nd))} psi" if nd else ""
    if indist == [p_star]:
        if nd:
            return pronto(None, indist, f"veredito suspenso: {_ps(sorted(nd))} psi não decidível")
        if not bandas[p_star].medida:
            return pronto(None, indist, f"extremo sem banda medida: {p_star:.3g} psi "
                                        "não é declarada a melhor sozinha")
        return pronto(p_star, indist, f"melhor: {p_star:.3g} psi")
    if len(indist) == len(dec):
        return pronto(None, indist, "todas indistinguíveis" + sufixo)
    return pronto(None, indist, f"indistinguíveis: {_ps(indist)} psi" + sufixo)


@dataclass(frozen=True)
class Escolha:
    criterio: str
    sentido: str
    vereditos: Mapping[str, Veredito]
    veredito_muda_com_kt: bool | None
    rotulos: tuple[str, ...]


def _motivo_na(r: ResultadoCarro) -> str:
    par = r.par or {}
    if par.get("pior") is not None:
        res = par[par["pior"] if par["pior"] != "empate" else "esquerda"]
        if getattr(res, "motivo", None):
            return res.motivo
    return f"a_y_lim N/A ({r.veredito})"


def _assinatura(v: Veredito) -> tuple:
    return (v.melhor, v.indistinguiveis, tuple(sorted(v.nao_decidiveis)))


def escolher_pressao(criterio: str, *, resultados_carro: Sequence[ResultadoCarro] | None = None,
                     family: ts.StaticTireFamily | None = None,
                     fz_estatica_eixo_n: Mapping[str, float] | None = None,
                     camber_eixo_rad: Mapping[str, float] | None = None) -> Escolha:
    """Escolha da pressão por um critério explícito de lista fechada (spec §8); sem ranking que misture critérios.

    `a_y_lim`: um Veredito por variante de KT presente ("KT (a)", "KT (b)"), e `veredito_muda_com_kt` quando as
    duas existem (muda se o melhor, o conjunto indistinguível ou o conjunto não decidível diferem).
    `C_alpha_operacao`: um por eixo ("eixo F", "eixo R"), Cα de `metricas_pneu` na Fz estática do eixo (limitada ao
    teto comum, com rótulo) e no camber estático do eixo; `veredito_muda_com_kt` = None.
    """
    if criterio in CRITERIOS_TBD:
        raise ValueError(f"critério {criterio!r}: meta TBD (sem alvo definido na ficha); só se escolhe por "
                         f"{', '.join(CRITERIOS)}")
    if criterio not in CRITERIOS:
        raise ValueError(f"critério {criterio!r} fora da lista fechada: {', '.join(CRITERIOS)}")
    sentido = CRITERIOS[criterio]
    rotulos = ROTULOS_FIXOS + (_ROT_BANDA,)
    vereditos: dict[str, Veredito] = {}
    muda: bool | None = None
    if criterio == "a_y_lim":
        if not resultados_carro:
            raise ValueError("a_y_lim pede resultados_carro (saída de comparar_carro)")
        for var in sorted({r.variante_kt for r in resultados_carro}):
            rs = [r for r in resultados_carro if r.variante_kt == var]
            nd: dict[float, str] = {}
            for r in rs:
                if r.ay_lim_ms2 is None:
                    nd[r.pressao_psi] = _motivo_na(r)
                elif r.borda_alfa:
                    nd[r.pressao_psi] = _MOTIVO_BORDA
            vereditos[f"KT ({var})"] = decidir({r.pressao_psi: r.ay_lim_ms2 for r in rs}, banda_carro(rs), nd)
        if len(vereditos) == 2:
            a, b = (vereditos[k] for k in sorted(vereditos))
            muda = _assinatura(a) != _assinatura(b)
    else:
        if family is None or fz_estatica_eixo_n is None or camber_eixo_rad is None:
            raise ValueError("C_alpha_operacao pede family, fz_estatica_eixo_n e camber_eixo_rad")
        teto = tp.teto_comum_fz(family)
        for eixo in ("F", "R"):
            fz = float(fz_estatica_eixo_n[eixo])
            fz_uso = min(fz, teto)
            if fz > teto:
                rotulos += (f"eixo {eixo}: Fz estática {fz:g} N acima do teto comum, Cα avaliado em {teto:.0f} N",)
            vals = {}
            for q in family.pressures_psi:
                prof = family.profiles[q]
                vals[q] = tp.metricas_pneu(tp.avaliador_perfil(prof), tp.faixa_do_perfil(prof), fz_n=fz_uso,
                                           camber_rad=float(camber_eixo_rad[eixo])).c_alpha_n_rad
            vereditos[f"eixo {eixo}"] = decidir(vals, banda_pneu(vals, None), {})
    return Escolha(criterio, sentido, vereditos, muda, rotulos)
