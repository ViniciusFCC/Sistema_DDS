"""
Escada de hipóteses do MMM em raio fixo (incremento 6, Task 6; adendo §5 e §6).

Degrau 1: o MMM na configuração da planilha contra equilibrio.analise_par (prova o reuso da física por roda, não a física
do MMM). Degrau 2: uma variante Python por vez a partir da planilha, mais "10+9b" e "todas". Sensibilidades: uma por
unidade, em outra tabela. Nenhuma função aqui decide "dentro da tolerância": a tolerância da escada é o EDR-065
(pendente) e por isso não existe parâmetro de tolerância. O módulo não conhece a origem dos dados; quem o chama rotula
o número (pior origem do caso, geometria sintética).
"""

import math
from dataclasses import dataclass, replace

import equilibrio as eq
import mmm

# Grade do degrau 1: a do limite (401 pontos de α), a mesma nos dois lados (ver degrau_1).
_N_ALFA = 401
_PASSO_G = 0.01
_RES_PADRAO_MS2 = 0.01   # o padrão de mmm.limite, quando o analise_par não devolve resolução (nenhum eixo satura)


@dataclass(frozen=True)
class ComparacaoDegrau1:
    """MMM (planilha) contra analise_par num sentido. d_ay_sat_* = MMM − analise_par [m/s²] (None se algum lado não tem
    saturação no eixo). cn_mmm é o cn_estabilizante_q; cn_par é o c_n. ok = mesmo veredito, |d_ay_sat| <= resolução do limite + resolução do
    analise_par (= 2·resolucao_ms2) em cada eixo e cn dentro da folga equivalente (ver _julga); motivo diz o que reprovou (None quando ok)."""
    sentido: str
    veredito_mmm: str
    veredito_par: str
    d_ay_sat_f: float | None
    d_ay_sat_r: float | None
    cn_mmm: float | None
    cn_par: float | None
    resolucao_ms2: float | None
    ok: bool
    motivo: str | None


@dataclass(frozen=True)
class LinhaEscada:
    """Uma linha do degrau 2. nome ∈ {"planilha", "1+2", "3", "7", "9a", "9b", "10", "10+9b", "11", "todas"};
    hipoteses são os números cobertos; limite é o mmm.Limite da linha (na 7 e na "todas", o do pior sentido).
    pior_sentido ("esquerda"/"direita") só existe onde a hipótese 7 está ligada (linhas "7" e "todas", que a inclui);
    nas outras é None (curva à esquerda apenas). d_* = linha − planilha (None se algum lado não tem número). `inverte` compara o
    veredito da linha com o da planilha e não classifica nada como "dentro da tolerância" (EDR-065 pendente)."""
    nome: str
    hipoteses: tuple[int, ...]
    limite: mmm.Limite
    pior_sentido: str | None
    d_ay_t: float | None
    d_cn_estabilizante_q: float | None
    d_k: float | None
    inverte: str


def _julga(veredito_mmm: str, veredito_par: str, d_f: float | None, d_r: float | None, cn_mmm: float | None,
           cn_par: float | None, res_ms2: float, delta_sat_ms2: float | None) -> tuple[bool, str | None]:
    """Critério do degrau 1: mesmo veredito (N/A com N/A conta como o mesmo), |d_ay_sat| <= 2·res_ms2 em cada eixo e, onde
    os dois têm C_N, |cn_mmm − cn_par| <= 2·res·|cn_par|/Δsat. O C_N é a folga do outro eixo em T vezes o braço, e essa
    folga cresce linearmente com a distância Δsat entre as duas saturações (zero quando coincidem); um T deslocado de
    res_ms2 em cada código muda o C_N de até 2·res·|cn|/Δsat. É a folga equivalente em força, sem número novo.

    Cota da saturação: res_mmm + res_par = 2·res_ms2 (o limite roda com a resolução que o analise_par mede, então as duas
    são iguais). São dois resultados discretizados, cada um com a incerteza que declara; a bisseção do MMM é exata e o
    analise_par interpola a folga entre linhas, com erro de até ~4/3 da sua resolução. Exigir só <= res_ms2 punha o
    oráculo no limite por construção (decisão do controlador, TC-ESC-001)."""
    cota = 2.0 * res_ms2
    motivos = []
    if veredito_mmm != veredito_par:
        motivos.append(f"veredito {veredito_mmm} (MMM) ≠ {veredito_par} (analise_par)")
    for eixo, d in (("F", d_f), ("R", d_r)):
        if d is not None and abs(d) > cota:
            motivos.append(f"|ay_sat_{eixo} MMM − analise_par| = {abs(d):.3e} > resolucao MMM + analise_par = {cota:.3e}")
    if (cn_mmm is None) != (cn_par is None):
        motivos.append(f"C_N só num dos lados (MMM {cn_mmm}, analise_par {cn_par})")
    elif cn_mmm is not None and cn_par is not None:
        if delta_sat_ms2 is None or delta_sat_ms2 <= 0.0:
            motivos.append("C_N sem as duas saturações: a folga equivalente não é definida")
        elif abs(cn_mmm - cn_par) > 2.0 * res_ms2 * abs(cn_par) / delta_sat_ms2:
            motivos.append(f"|cn_mmm − c_n| = {abs(cn_mmm - cn_par):.3e} > folga equivalente "
                           f"{2.0 * res_ms2 * abs(cn_par) / delta_sat_ms2:.3e}")
    return (not motivos), ("; ".join(motivos) or None)


def _dif(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a - b


def _compara(sentido: str, caso: eq.CasoEquilibrio) -> ComparacaoDegrau1:
    par = eq.analise_par(caso, n_alfa=_N_ALFA, passo_g=_PASSO_G)
    res = par.resolucao_ms2 if par.resolucao_ms2 is not None else _RES_PADRAO_MS2
    lim = mmm.limite(caso, mmm.Hipoteses.planilha(), resolucao_ms2=res, n_alfa=_N_ALFA)
    d_f, d_r = _dif(lim.ay_sat_f, par.ay_sat_f), _dif(lim.ay_sat_r, par.ay_sat_r)
    # Um eixo que satura num código e não no outro não é identidade, ainda que a diferença não exista.
    ausencias = [e for e, a, b in (("F", lim.ay_sat_f, par.ay_sat_f), ("R", lim.ay_sat_r, par.ay_sat_r))
                 if (a is None) != (b is None)]
    delta = (abs(par.ay_sat_f - par.ay_sat_r) if par.ay_sat_f is not None and par.ay_sat_r is not None else None)
    ok, motivo = _julga(lim.veredito, par.veredito, d_f, d_r, lim.cn_estabilizante_q, par.c_n, res, delta)
    if ausencias:
        ok = False
        motivo = "; ".join(filter(None, [motivo, f"saturação do eixo {'/'.join(ausencias)} só num dos lados"]))
    return ComparacaoDegrau1(sentido, lim.veredito, par.veredito, d_f, d_r, lim.cn_estabilizante_q, par.c_n,
                             par.resolucao_ms2, ok, motivo)


def degrau_1(caso: eq.CasoEquilibrio) -> tuple[ComparacaoDegrau1, ComparacaoDegrau1]:
    """MMM na configuração da planilha contra analise_par, (esquerda, direita), a direita via equilibrio.espelhar.

    Mesma grade de α dos dois lados: analise_par com n_alfa = 401 e passo_g = 0,01 (e o limite com o mesmo n_alfa e
    resolucao_ms2 igual à resolução que o próprio analise_par mede). Com a grade padrão dele (n_alfa = 25, passo
    0,05 g) a diferença é de ~3e-3 m/s² e vem da grade de α (a grossa subestima o pico), e não da hipótese; comparar
    nela mediria a grade. A cota da saturação é a soma das duas incertezas declaradas (resolução do limite, igual à do
    analise_par, mais a do analise_par), e `ok` usa a mesma cota (ver _julga). Onde o analise_par não mede resolução (nenhum eixo satura), usa-se o padrão do limite.
    """
    return _compara("esquerda", caso), _compara("direita", eq.espelhar(caso))


def _inverte(veredito_planilha: str, veredito_linha: str) -> str:
    """"N/A" se algum for N/A; "não" se iguais; "sim" para PUSH ↔ LOOSE; "NEUTRO ↔ PUSH" ou "NEUTRO ↔ LOOSE" nos
    demais pares. Sem tolerância (EDR-065 pendente)."""
    if eq.NA in (veredito_planilha, veredito_linha):
        return "N/A"
    if veredito_planilha == veredito_linha:
        return "não"
    par = {veredito_planilha, veredito_linha}
    if par == {eq.PUSH, eq.LOOSE}:
        return "sim"
    if par == {eq.NEUTRO, eq.PUSH}:
        return "NEUTRO ↔ PUSH"
    if par == {eq.NEUTRO, eq.LOOSE}:
        return "NEUTRO ↔ LOOSE"
    return "N/A"   # veredito fora do conjunto conhecido: não classifica


def _pior(esq: mmm.Limite, dir_: mmm.Limite) -> tuple[mmm.Limite, str]:
    """Pior sentido: menor T, N/A (sem T) conta como pior, como equilibrio._chave_pior. Empate: esquerda."""
    def chave(lim: mmm.Limite) -> float:
        return -math.inf if (lim.veredito == eq.NA or lim.ay_t_ms2 is None) else lim.ay_t_ms2
    return (esq, "esquerda") if chave(esq) <= chave(dir_) else (dir_, "direita")


def degrau_2(caso: eq.CasoEquilibrio) -> tuple[LinhaEscada, ...]:
    """Planilha e uma variante Python por vez (1+2, 3, 7, 9a, 9b, 10, 11), mais 10+9b (travado com o PAC2002
    combinado, adendo §6) e todas, nesta ordem: planilha, 1+2, 3, 7, 9a, 9b, 10, 10+9b, 11, todas. As linhas com a hipótese 7 (7 e todas)
    rodam os dois sentidos (caso e espelhar(caso)) e guardam o pior; as outras, só a curva à esquerda.
    Linhas que terminam em N/A (por exemplo o travado a R pequeno) aparecem como N/A, sem exceção."""
    pl = mmm.Hipoteses.planilha()
    v = mmm.VARIANTES
    receitas = [("planilha", (), pl, False)]
    for campo in ("alfa", "cos_delta", "sentido", "fx_exigido", "tracao", "diferencial", "transf_long"):
        receitas.append((v[campo]["nome"], v[campo]["hipoteses"], replace(pl, **{campo: v[campo]["python"]}),
                         campo == "sentido"))
        if campo == "diferencial":   # o travado com o PAC2002 combinado vem logo depois do travado sozinho
            receitas.append(("10+9b", (10, 9), replace(pl, diferencial="travado", tracao="pac2002"), False))
    receitas.append(("todas", (1, 2, 3, 7, 9, 10, 11), mmm.Hipoteses.python_completo(), True))
    espelho = None
    base = mmm.limite(caso, pl)
    linhas = []
    for nome, hips, hip, dois in receitas:
        lim, pior = (base if nome == "planilha" else mmm.limite(caso, hip)), None
        if dois:
            if espelho is None:
                espelho = eq.espelhar(caso)
            lim, pior = _pior(lim, mmm.limite(espelho, hip))
        linhas.append(LinhaEscada(
            nome=nome, hipoteses=hips if nome != "planilha" else (), limite=lim, pior_sentido=pior,
            d_ay_t=_dif(lim.ay_t_ms2, base.ay_t_ms2),
            d_cn_estabilizante_q=_dif(lim.cn_estabilizante_q, base.cn_estabilizante_q),
            d_k=_dif(lim.k_rad_por_ms2, base.k_rad_por_ms2),
            inverte=_inverte(base.veredito, lim.veredito)))
    return tuple(linhas)


def sensibilidades(caso: eq.CasoEquilibrio) -> tuple[dict, ...]:
    """Uma sensibilidade por chave de mmm.UNIDADES, na ordem dela, com Hipoteses.planilha(); h_cp, com
    transf_long="regime" (a parcela D·h_cp/L só existe no regime). Cada dict é o de mmm.sensibilidade (sem faixa)."""
    pl = mmm.Hipoteses.planilha()
    return tuple(mmm.sensibilidade(caso, replace(pl, transf_long="regime") if p == "h_cp" else pl, p)
                 for p in mmm.UNIDADES)
