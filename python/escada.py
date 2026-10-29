"""
Escada de hipóteses do MMM em raio fixo (incremento 6, Task 6; adendo §5 e §6).

Degrau 1: o MMM na configuração da planilha contra equilibrio.analise_par (prova o reuso da física por roda, não a física
do MMM). Degrau 2: a planilha, as duas linhas de controle ("planilha (acoplado, sem rotação)" e "planilha (acoplado)") e
uma variante Python por vez, mais "10+9b" e "todas". A linha sem rotação (a planilha resolvida pelo Newton 2-D com
a_y = A, a_x = 0) mede contra a planilha só o viés do método; a linha com rotação (a_y = A·cos β, a_x = −A·sen β) mede
contra a sem rotação o efeito da simplificação a_y = A da planilha; as linhas acopladas medem o Δ contra a linha com
rotação (EDR-064, decisão 2.6 revista). Sensibilidades: uma por
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
# Linhas de controle do degrau 2: a planilha resolvida pelo Newton 2-D, sem e com a rotação β (EDR-064, decisão 2.6 revista).
NOME_CONTROLE_SEM_ROTACAO = "planilha (acoplado, sem rotação)"   # a_y = A, a_x = 0: Δ contra "planilha" = viés do método
NOME_CONTROLE = "planilha (acoplado)"                            # a_y = A·cos β: Δ contra a anterior = efeito de a_y = A


@dataclass(frozen=True)
class ComparacaoDegrau1:
    """MMM (planilha) contra analise_par num sentido. d_ay_sat_* = MMM − analise_par [m/s²] (None se algum lado não tem
    saturação no eixo). cn_mmm é o cn_estabilizante_q; cn_par é o c_n. ok = mesmo veredito, |d_ay_sat| <= 2·resolucao_ms2 (cota empírica,
    ver _julga) em cada eixo e cn dentro da folga equivalente; motivo diz o que reprovou (None quando ok)."""
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
    """Uma linha do degrau 2. nome ∈ {"planilha", "planilha (acoplado, sem rotação)", "planilha (acoplado)", "1+2", "3",
    "7", "9a", "9b", "10", "10+9b", "11", "todas"}; hipoteses são os números cobertos (vazio nas linhas de controle: a
    rotação β não é hipótese numerada); limite é o mmm.Limite da linha (na 7 e na "todas", o do pior sentido).
    pior_sentido ("esquerda"/"direita") só existe onde a hipótese 7 está ligada (linhas "7" e "todas", que a inclui);
    nas outras é None (curva à esquerda apenas). d_* = linha − `referencia` (None se algum lado não tem número):
    "planilha" para a linha "planilha (acoplado, sem rotação)" (viés só do método) e para as linhas desacopladas;
    "planilha (acoplado, sem rotação)" para a "planilha (acoplado)" (efeito da simplificação a_y = A da planilha);
    "planilha (acoplado)" para as linhas que usam o Newton 2-D. A soma dos Δ das duas linhas de controle é o Δ da
    "planilha (acoplado)" contra a "planilha". `inverte` compara o veredito da linha com o da `referencia` e não classifica nada como "dentro da
    tolerância" (EDR-065 pendente). `motivo` é None quando a hipótese da linha está ligada no caso; senão diz qual chave da
    planilha está desligada ("hipótese desligada no caso (<campo>)"): a linha ainda é calculada e a hipótese desligada
    não muda nada nela. Uma linha de uma hipótese só coincide então com a referência por construção; na "todas", só as
    hipóteses ligadas contam no Δ."""
    nome: str
    hipoteses: tuple[int, ...]
    limite: mmm.Limite
    pior_sentido: str | None
    d_ay_t: float | None
    d_cn_estabilizante_q: float | None
    d_k: float | None
    inverte: str
    referencia: str = "planilha"
    motivo: str | None = None


def _julga(veredito_mmm: str, veredito_par: str, d_f: float | None, d_r: float | None, cn_mmm: float | None,
           cn_par: float | None, res_ms2: float, delta_sat_ms2: float | None) -> tuple[bool, str | None]:
    """Critério do degrau 1: mesmo veredito (N/A com N/A conta como o mesmo), |d_ay_sat| <= 2·res_ms2 em cada eixo e, onde
    os dois têm C_N, |cn_mmm − cn_par| <= 2·res·|cn_par|/Δsat. O C_N é a folga do outro eixo em T vezes o braço, e essa
    folga cresce linearmente com a distância Δsat entre as duas saturações (zero quando coincidem); um T deslocado de
    2·res_ms2 muda o C_N de até 2·res·|cn|/Δsat. É a folga equivalente em força, sem número novo.

    Origem da cota 2·res_ms2 (o que se sabe e o que não). Os dois lados usam a mesma grade de α, então a discretização
    de α é comum e some na diferença. Sobra o erro de A_Y de cada código. O MMM acha a saturação por bisseção com
    tolerância resolucao·1e-4 (desprezível). O analise_par interpola linearmente a folga m(a) = capacidade − exigida entre
    linhas de passo h, e a raiz interpolada erra por até |m''|/(8·|m'|)·h² (erro da interpolação linear, com
    (a − a0)(a1 − a) <= h²/4). A curvatura m'' depende da carga e do pneu e não é conhecida a priori, então não há
    cota rigorosa em função da resolução. A `resolucao_ms2` do analise_par é |S_h − S_h/2| (grade refinada): num erro
    assintótico c·h² ela vale 3/4 do erro de S_h, ou seja, o erro real de S_h é cerca de 4/3 da resolução que ele
    declara (Richardson). A resolução declarada SUBESTIMA o erro dele. Estimativa: (4/3 + 1e-4)·res. Adota-se 2·res, 1,5
    vez essa estimativa, como cota EMPÍRICA (a razão |d_ay_sat|/res de cada caso do TC-ESC-001 sai no detalhe do teste).
    Não é cota provada, e a ciência do usuário é pedida no PR (EDR-064, item 2.9). Exigir só <= res_ms2 punha o
    oráculo no limite por construção."""
    cota = 2.0 * res_ms2
    motivos = []
    if veredito_mmm != veredito_par:
        motivos.append(f"veredito {veredito_mmm} (MMM) ≠ {veredito_par} (analise_par)")
    for eixo, d in (("F", d_f), ("R", d_r)):
        if d is not None and abs(d) > cota:
            motivos.append(f"|ay_sat_{eixo} MMM − analise_par| = {abs(d):.3e} > cota empírica 2·resolucao_ms2 = {cota:.3e}")
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


def _compara(sentido: str, caso: eq.CasoEquilibrio, ay_max_g: float = 2.0) -> ComparacaoDegrau1:
    par = eq.analise_par(caso, ay_max_g=ay_max_g, n_alfa=_N_ALFA, passo_g=_PASSO_G)
    res = par.resolucao_ms2 if par.resolucao_ms2 is not None else _RES_PADRAO_MS2
    lim = mmm.limite(caso, mmm.Hipoteses.planilha(), resolucao_ms2=res, ay_max_g=ay_max_g, n_alfa=_N_ALFA)
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


def degrau_1(caso: eq.CasoEquilibrio, ay_max_g: float = 2.0) -> tuple[ComparacaoDegrau1, ComparacaoDegrau1]:
    """MMM na configuração da planilha contra analise_par, (esquerda, direita), a direita via equilibrio.espelhar.

    Mesma grade de α dos dois lados: analise_par com n_alfa = 401 e passo_g = 0,01 (e o limite com o mesmo n_alfa e
    resolucao_ms2 igual à resolução que o próprio analise_par mede). Com a grade padrão dele (n_alfa = 25, passo
    0,05 g) a diferença é de ~3e-3 m/s² e vem da grade de α (a grossa subestima o pico), e não da hipótese; comparar
    nela mediria a grade. A cota da saturação é 2·resolucao_ms2, empírica (ver _julga: a resolução que o
    analise_par declara subestima o erro dele), e `ok` usa a mesma cota. Onde o analise_par não mede resolução (nenhum eixo
    satura), usa-se o padrão do limite. ay_max_g é a faixa de busca da saturação (rotulada; padrão 2,0 g, o do analise_par
    e do limite).
    """
    return _compara("esquerda", caso, ay_max_g), _compara("direita", eq.espelhar(caso), ay_max_g)


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


def _desligadas(caso: eq.CasoEquilibrio, hips: tuple[int, ...]) -> str | None:
    """"hipótese desligada no caso (<campo>)" se alguma hipótese da linha depende de uma chave da planilha que o caso deixa
    desligada, senão None. Chaves: hipótese 9 (e a 10, que age sobre a tração) liga com cda_m2 ou crr (eq.tracao_ativa);
    hipótese 7 liga com cg_lateral_m ≠ 0. As outras linhas não têm chave própria: a 1+2 (α cinemático) muda mesmo sem toe
    nem Ackermann (velocidades não paralelas das rodas), a 3 (cos δ_ref) está sempre ligada porque o MMM exige raio_m, e a
    11 (regime) usa a_x = −A·sen β, que existe sem tração."""
    campos = []
    if (9 in hips or 10 in hips) and not eq.tracao_ativa(caso):
        campos.append("cda_m2 e crr")
    if 7 in hips and caso.cg_lateral_m == 0.0:
        campos.append("cg_lateral_m")
    return f"hipótese desligada no caso ({'; '.join(campos)})" if campos else None


def degrau_2(caso: eq.CasoEquilibrio, ay_max_g: float = 2.0) -> tuple[LinhaEscada, ...]:
    """Planilha, as duas linhas de controle e uma variante Python por vez (1+2, 3, 7, 9a, 9b, 10, 11), mais 10+9b (travado
    com o PAC2002 combinado, adendo §6) e todas, nesta ordem: planilha, planilha (acoplado, sem rotação), planilha
    (acoplado), 1+2, 3, 7, 9a, 9b, 10, 10+9b, 11, todas. As linhas com a hipótese 7 (7 e todas) rodam os dois sentidos
    (caso e espelhar(caso)) e guardam o pior; as outras, só a curva à esquerda.

    Referência do Δ (EDR-064, decisão 2.6 revista), uma cadeia sem hipótese mudada nas linhas de controle:
    - "planilha (acoplado, sem rotação)": as hipóteses da planilha pelo Newton 2-D com a_y = A e a_x = 0, as mesmas da
      planilha; o Δ contra a "planilha" é só o viés do método.
    - "planilha (acoplado)": idem com a rotação a_y = A·cos β e a_x = −A·sen β; o Δ contra a linha sem rotação é o efeito
      da simplificação a_y = A da planilha (a rotação não tem número de hipótese).
    - As linhas que usam o Newton (todas menos a 7) medem Δ e `inverte` contra a "planilha (acoplado)", para que o número
      de cada linha seja o efeito da hipótese; a 7 usa o caminho desacoplado e mede contra a planilha. Linhas que terminam em N/A (por exemplo o travado a R pequeno)
    aparecem como N/A, sem exceção. ay_max_g é a faixa de busca da saturação (rotulada; padrão 2,0 g)."""
    pl = mmm.Hipoteses.planilha()
    v = mmm.VARIANTES
    receitas = [("planilha", (), pl, False),
                (NOME_CONTROLE_SEM_ROTACAO, (), mmm.planilha_acoplada(rotacao=False), False),
                (NOME_CONTROLE, (), mmm.planilha_acoplada(rotacao=True), False)]
    for campo in ("alfa", "cos_delta", "sentido", "fx_exigido", "tracao", "diferencial", "transf_long"):
        receitas.append((v[campo]["nome"], v[campo]["hipoteses"], replace(pl, **{campo: v[campo]["python"]}),
                         campo == "sentido"))
        if campo == "diferencial":   # o travado com o PAC2002 combinado vem logo depois do travado sozinho
            receitas.append(("10+9b", (10, 9), replace(pl, diferencial="travado", tracao="pac2002"), False))
    receitas.append(("todas", (1, 2, 3, 7, 9, 10, 11), mmm.Hipoteses.python_completo(), True))
    espelho = None
    refs = {}   # limite das linhas que servem de referência: planilha e as duas de controle
    linhas = []
    for nome, hips, hip, dois in receitas:
        lim, pior = mmm.limite(caso, hip, ay_max_g=ay_max_g), None
        if nome in ("planilha", NOME_CONTROLE_SEM_ROTACAO, NOME_CONTROLE):
            refs[nome] = lim
        if dois:
            if espelho is None:
                espelho = eq.espelhar(caso)
            lim, pior = _pior(lim, mmm.limite(espelho, hip, ay_max_g=ay_max_g))
        if nome == NOME_CONTROLE:
            nome_ref = NOME_CONTROLE_SEM_ROTACAO
        elif nome != NOME_CONTROLE_SEM_ROTACAO and mmm._e_acoplada(hip):
            nome_ref = NOME_CONTROLE
        else:
            nome_ref = "planilha"
        ref = refs[nome_ref]
        linhas.append(LinhaEscada(
            nome=nome, hipoteses=hips, limite=lim, pior_sentido=pior,
            d_ay_t=_dif(lim.ay_t_ms2, ref.ay_t_ms2),
            d_cn_estabilizante_q=_dif(lim.cn_estabilizante_q, ref.cn_estabilizante_q),
            d_k=_dif(lim.k_rad_por_ms2, ref.k_rad_por_ms2),
            inverte=_inverte(ref.veredito, lim.veredito), referencia=nome_ref, motivo=_desligadas(caso, hips)))
    return tuple(linhas)


def sensibilidades(caso: eq.CasoEquilibrio, ay_max_g: float = 2.0) -> tuple[dict, ...]:
    """Uma sensibilidade por chave de mmm.UNIDADES, na ordem dela, com Hipoteses.planilha(); h_cp, com
    transf_long="regime" (a parcela D·h_cp/L só existe no regime). Cada dict é o de mmm.sensibilidade (sem faixa).
    ay_max_g é a faixa de busca da saturação (rotulada; padrão 2,0 g). A de h_cp parte de h_cp = 0 (None conta como 0): é a
    sensibilidade em torno de zero, não de um valor medido."""
    pl = mmm.Hipoteses.planilha()
    return tuple(mmm.sensibilidade(caso, replace(pl, transf_long="regime") if p == "h_cp" else pl, p, ay_max_g)
                 for p in mmm.UNIDADES)
