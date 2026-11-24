"""
Varredura do curso e avaliação de um candidato em Python puro: porte de `posicionador.varredura` (a lista de restrições, as
fontes e o raciocínio estão na docstring de lá; aqui só o que muda).

Mesmas restrições, mesmos nomes, mesmos estados e mesma regra de veredito. Diferenças deliberadas:
- `Construcao.pontos` (dicionário) no lugar de `HardpointSet`; cinemática de `puro.cinematica`;
- cena: `Cena.fixos` são primitivos de `puro.geometria`; `Cena.nos` são tuplas xyz (a leitura do STEP/Fusion fica fora do núcleo);
- o gabarito T.1.2 reaproveita a ocupação da parte fixa da cena entre candidatos (`Cena._cache`), com o mesmo resultado.
`avaliar` nunca levanta exceção: a falha vira INVIAVEL com motivo.
"""
import math
from dataclasses import dataclass, field
from typing import Any

from posicionador.puro import linalg as la
from posicionador.puro import regulamento as reg
from posicionador.puro.cinematica import Canto, ErroCinematica, razao_de_movimento
from posicionador.puro.geometria import Barril, Capsula, dist_seg_seg, folga_segmento, linspace
from posicionador.puro.mecanismo import canto_fl

TOL_MR0 = 0.01
TOL_NUM_M = 1e-9
TOL_RAMO_M = 1e-7
PASSO_FOLGA_M = 0.002
PASSOS_CREMALHEIRA = 4
FORCA_ORIGEM = ("REGRA", "META", "MARGEM_EQUIPE", "HIPOTESE", "A_CONFIRMAR")
CORPOS = ("push rod", "rocker", "amortecedor")
MOTIVO_CHASSI_BLOQUEIA = "o chassi sozinho já bloqueia o gabarito: a atuação não é a causa"
NOME_MANGA = "folga à manga/freio/pinça dentro do aro"
NOME_MOVEIS = "folga às peças móveis do STEP (não modeladas na fase 1)"
FONTE_SEM_COLIDIR = ("spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a configuração "
                     "não declara margem ao chassi)")
PERNAS = (("LCA_OUT", "LCA_IN_F"), ("LCA_OUT", "LCA_IN_R"), ("UCA_OUT", "UCA_IN_F"), ("UCA_OUT", "UCA_IN_R"))
CHAVES = ("PUSH_OUT", "PUSH_IN", "ROCKER_AXIS_A", "ROCKER_SPRING", "SPRING_CHASSIS", "WHEEL_CENTER", "SPINDLE_PT", "TIE_IN",
          "TIE_OUT", "LCA_OUT", "UCA_OUT", "LCA_IN_F", "LCA_IN_R", "UCA_IN_F", "UCA_IN_R")


# Mesmo texto do pacote de referência, copiado para o núcleo não depender de numpy (o teste confere a igualdade).
NAO_MODELADO_FASE1 = (
    "manga, freio e pinça dentro do aro (sem RODA_ modelado): o barril do aro trata o miolo como livre e o push rod nasce "
    "dentro dele; restrição NAO_VERIFICAVEL em todo candidato",
    "pneu (V.3.2.4): só o aro entra, como barril da configuração",
    "V.3.2.4 além do aro: roda e pneu contra suspensão e chassi em todo o curso × esterço até os batentes",
    "coluna de direção: só a posição em X do início do gabarito T.1.2 (x_ini_t12_m), sem o corpo da coluna",
    "pedais e F.8.6.3 (folga ≥ 25 mm do conjunto de pedais)",
    "volume reservado do atenuador de impacto (F.8.4.2): só a face traseira da AIP (F.8.6.1)",
    "sinalizações T.1.3.3 (exige escudo), V.3.1.3 (visibilidade) e F.5.3.1 (furo em tubo regulado → SES)",
    "faixa de ajuste de camber, toe e altura (spec §12 J2): só a geometria estática da v10",
)


@dataclass
class Restricao:
    nome: str
    valor: Any
    limite: Any
    folga: "float | None"
    estado: str
    origem: str
    fonte: str
    motivo: "str | None" = None
    completa: bool = True


def _finitos(obj):
    for v in vars(obj).values():
        vals = v if isinstance(v, (tuple, list)) else (v,)
        flat = []
        for x in vals:
            flat.extend(x if isinstance(x, (tuple, list)) else (x,))
        for x in flat:
            try:
                if not math.isfinite(float(x)):
                    return False
            except (TypeError, ValueError):
                continue
    return True


@dataclass
class Cena:
    fixos: list
    nos: list              # tuplas xyz [m] dos nós do chassi, referencial do carro
    aro: tuple
    regras: dict
    nao_modelado: list = field(default_factory=list)
    pecas_moveis: list = field(default_factory=list)
    ref_hipotese: "str | None" = None
    _cache: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        ruins = [i for i, ob in enumerate(self.fixos) if not _finitos(ob)]
        if ruins:
            raise ValueError(f"cena com primitivo fixo não finito (NaN ou inf) nos índices {ruins[:10]}: falha fechada")
        if not all(math.isfinite(float(x)) for x in self.aro):
            raise ValueError(f"cena com aro não finito: {self.aro!r}")
        self.nao_modelado = [t for t in NAO_MODELADO_FASE1 if t not in self.nao_modelado] + list(self.nao_modelado)


@dataclass
class Avaliacao:
    restricoes: list
    veredito: str
    motivo: "str | None"
    curvas: dict
    dist_no_m: dict
    n: int
    resolucoes: list = field(default_factory=list)
    indeterminadas: list = field(default_factory=list)

    def restricao(self, nome):
        return next((r for r in self.restricoes if r.nome == nome), None)

    def estados(self):
        return {r.nome: r.estado for r in self.restricoes}


class _SemSolucao(Exception):
    def __init__(self, dz, steer, erro):
        self.dz, self.steer, self.erro = dz, steer, erro
        txt = f"cinemática sem solução em dz = {dz * 1e3:.3f} mm"
        if steer:
            txt += f", cremalheira = {steer * 1e3:+.3f} mm"
        super().__init__(f"{txt}: {type(erro).__name__}: {erro}")


def _valor_opcional(cfg, nome):
    return cfg.valor(nome) if nome in cfg.itens else None


def regras_da_config(cfg):
    return {"x_ini_t12_m": cfg.valor("x_ini_t12_m"), "x_fim_t12_m": cfg.valor("x_fim_t12_m"),
            "z_min_t12_m": _valor_opcional(cfg, "z_min_t12_m"), "z_max_t12_m": _valor_opcional(cfg, "z_max_t12_m"),
            "y_centro_t12_m": 0.0, "x_face_traseira_aip_m": cfg.valor("x_face_traseira_aip_m")}


def _aro(cfg):
    return (float(cfg.valor("aro_r_int_m")), float(cfg.valor("aro_meia_largura_m")))


def cena_sem_cad(cfg):
    return Cena(fixos=[], nos=[], aro=_aro(cfg), regras=regras_da_config(cfg),
                nao_modelado=["CAD ausente: chassi e peças fixas não modelados"])


def cena_de(fixos, nos, cfg, z_t12_m=None, pecas_moveis=(), ref_hipotese=None, nao_modelado=()):
    """Cena a partir de primitivos já no referencial do carro (a leitura do STEP ou do Fusion é do chamador)."""
    regras = regras_da_config(cfg)
    if z_t12_m is not None:
        regras.update(z_min_t12_m=float(z_t12_m[0]), z_max_t12_m=float(z_t12_m[1]))
    return Cena(fixos=list(fixos), nos=[la.vec(n) for n in nos], aro=_aro(cfg), regras=regras,
                nao_modelado=list(nao_modelado), pecas_moveis=list(pecas_moveis), ref_hipotese=ref_hipotese)


def _proc(cfg, *nomes):
    its = [(n, cfg.item(n)) for n in nomes]
    origem = max((it.origem for _, it in its), key=FORCA_ORIGEM.index)
    return origem, "; ".join(f"{n} ({it.origem}): {it.fonte}" for n, it in its)


def _finita(v, o_que):
    v = float(v)
    if not math.isfinite(v):
        raise ValueError(f"{o_que} não finita ({v}): falha fechada")
    return v


def _r(nome, valor, limite, folga, cfg, itens, motivo=None, completa=True, estado=None):
    origem, fonte = _proc(cfg, *itens)
    if folga is not None:
        folga = _finita(folga, f"folga de {nome!r}")
    if estado is None:
        estado = "OK" if folga >= 0.0 else "VIOLADA"
    return Restricao(nome, valor, limite, folga, estado, origem, fonte, motivo, completa)


def _resolver(canto, dz, steer, q0, phi0):
    try:
        return canto.resolver(dz, steer, q0=q0, phi0=phi0)
    except Exception as e:  # noqa: BLE001
        raise _SemSolucao(dz, steer, e) from e


def _varrer(canto, dzs):
    s0 = _resolver(canto, 0.0, 0.0, None, 0.0)
    out = {}
    for grupo in (sorted(d for d in dzs if d >= 0.0), sorted((d for d in dzs if d < 0.0), reverse=True)):
        cur = s0
        for d in grupo:
            cur = _resolver(canto, float(d), 0.0, cur.q, cur.phi)
            out[float(d)] = cur
    return s0, [out[float(d)] for d in dzs]


def _esterçar(canto, sols, curso):
    out = []
    for s in sols:
        for sinal in (1.0, -1.0):
            cur = s
            for k in range(1, PASSOS_CREMALHEIRA + 1):
                cur = _resolver(canto, s.curso, sinal * curso * k / PASSOS_CREMALHEIRA, cur.q, cur.phi)
            out.append(cur)
    return out


def _pontos(canto, s):
    return {k: canto.ponto(s, k) for k in CHAVES}


def _pecas(p, cfg):
    O, A, Pv, B, C = (p[k] for k in ("PUSH_OUT", "PUSH_IN", "ROCKER_AXIS_A", "ROCKER_SPRING", "SPRING_CHASSIS"))
    rj = float(cfg.valor("r_junta_m"))
    return [("push rod", O, A, float(cfg.valor("r_prod_m"))),
            ("rocker", Pv, A, rj), ("rocker", Pv, B, rj), ("rocker", Pv, Pv, float(cfg.valor("r_pivo_m"))),
            ("amortecedor", B, C, float(cfg.valor("r_mola_m")))]


def _barril(p, aro):
    c = p["WHEEL_CENTER"]
    return Barril(c, la.unit(la.sub(p["SPINDLE_PT"], c)), aro[0], aro[1])


def _folga_aro(p, pecas, aro):
    b = _barril(p, aro)
    out = {}
    for corpo, a, bb, r in pecas:
        f = _finita(folga_segmento(b, a, bb, r, PASSO_FOLGA_M), f"folga ao aro ({corpo})")
        out[corpo] = min(out.get(corpo, math.inf), f)
    return out


def _folga_tirante(p, pecas):
    out = {}
    for corpo, a, b, r in pecas:
        f = _finita(dist_seg_seg(a, b, p["TIE_IN"], p["TIE_OUT"]) - r, f"folga ao tirante ({corpo})")
        out[corpo] = min(out.get(corpo, math.inf), f)
    return out


def _min_por_corpo(acum, novos, dz):
    for corpo, v in novos.items():
        v = _finita(v, f"folga mínima ({corpo}, dz = {float(dz) * 1e3:.2f} mm)")
        if corpo not in acum or v < acum[corpo][0]:
            acum[corpo] = (v, dz)


FONTES_FALHA = {"cinemática": "puro.cinematica.Canto (MODEL; REFERENCE = OptimumKinematics, EDR-004)",
                "construção": "posicionador.puro.mecanismo.construir",
                "avaliação": "posicionador.puro.varredura.avaliar"}


def _inviavel(n, motivo, nome="cinemática"):
    r = Restricao(nome, None, None, None, "VIOLADA", "HIPOTESE", FONTES_FALHA[nome], motivo)
    return Avaliacao([r], "INVIAVEL", motivo, {}, {"pivo": None, "olhal": None}, n)


def _veredito(restricoes, cfg):
    vio = [r.nome for r in restricoes if r.estado == "VIOLADA"]
    if vio:
        return "INVIAVEL", "restrições violadas: " + ", ".join(vio)
    nv = [r.nome for r in restricoes if r.estado == "NAO_VERIFICAVEL"]
    pa = [r.nome for r in restricoes if r.estado == "OK" and not r.completa]
    ac = cfg.a_confirmar()
    if nv or pa or ac:
        partes = []
        if nv:
            partes.append("não verificáveis: " + ", ".join(nv))
        if pa:
            partes.append("verificadas com valor provisório: " + ", ".join(pa))
        if ac:
            partes.append("itens a confirmar na configuração: " + ", ".join(ac))
        return "CONDICIONAL", "; ".join(partes)
    return "VIAVEL", None


def avaliar(construcao, cena, cfg, n: int = 25):
    """Avalia o candidato em n pontos do curso. Nunca levanta exceção."""
    if construcao is None or construcao.pontos is None:
        motivo = getattr(construcao, "motivo", None) or "sem hardpoints"
        return _inviavel(n, f"construção: {motivo}", "construção")
    try:
        return _avaliar(construcao, cena, cfg, int(n))
    except _SemSolucao as e:
        return _inviavel(n, str(e))
    except Exception as e:  # noqa: BLE001
        return _inviavel(n, f"avaliação sem resultado: {type(e).__name__}: {e}", "avaliação")


def _avaliar(construcao, cena, cfg, n):
    try:
        canto = canto_fl(construcao.pontos)
    except Exception as e:  # noqa: BLE001
        raise _SemSolucao(0.0, 0.0, e) from e
    if not canto.has_push:
        raise ValueError("canto sem grupo pushrod")
    droop, bump = float(cfg.valor("curso_droop_m")), float(cfg.valor("curso_bump_m"))
    dzs = linspace(-droop, bump, n)
    s0, sols = _varrer(canto, dzs)

    def mr_em(dz, ls_cont):
        try:
            m = razao_de_movimento(canto, float(dz))
        except Exception as e:  # noqa: BLE001
            raise _SemSolucao(float(dz), 0.0, e) from e
        if ls_cont is not None and abs(m["spring_length_m"] - ls_cont) > TOL_RAMO_M:
            raise _SemSolucao(float(dz), 0.0, ErroCinematica(
                f"MR local resolvido em outro ramo do rocker (Ls {m['spring_length_m']:.9f} × {ls_cont:.9f} m)"))
        return m["mr_wheel_per_spring"]

    ls = [canto.comprimento_mola(s) for s in sols]
    mr = [mr_em(d, l) for d, l in zip(dzs, ls)]
    mr0 = mr_em(0.0, canto.comprimento_mola(s0))
    th = [s.phi for s in sols]
    P = [_pontos(canto, s) for s in sols]
    eixo = la.unit(la.sub(canto.p0["ROCKER_AXIS_B"], canto.p0["ROCKER_AXIS_A"]))
    fora = [math.asin(min(1.0, abs(la.dot(la.unit(la.sub(p["PUSH_IN"], p["PUSH_OUT"])), eixo)))) for p in P]
    curvas = {"dz_m": dzs, "MR [wheel/spring]": mr, "Ls_m": ls, "angulo_fora_do_plano_rad": fora, "theta_rocker_rad": th}
    R = []

    alvo = float(cfg.valor("mr_alvo"))
    R.append(_r("MR(0)", mr0, (alvo - TOL_MR0, alvo + TOL_MR0), TOL_MR0 - abs(mr0 - alvo), cfg, ["mr_alvo"],
                motivo=f"tolerância ± {TOL_MR0} do plano da fase 1 (Task 6)"))
    var = float(max(mr) / min(mr) - 1.0)
    vmax = float(cfg.valor("mr_var_max"))
    R.append(_r("variação de MR", var, vmax, vmax - var, cfg, ["mr_var_max"],
                motivo=f"MR de {min(mr):.4f} a {max(mr):.4f} em {n} pontos de dz ∈ [{-droop * 1e3:.1f}; {bump * 1e3:.1f}] mm"))

    eye, stroke = float(cfg.valor("olho_a_olho_m")), float(cfg.valor("curso_amortecedor_m"))
    margem = cfg.valor("margem_curso_amortecedor_m")
    i_max, i_min = ls.index(max(ls)), ls.index(min(ls))
    R.append(_r("comprimento do amortecedor (máximo)", float(max(ls)), eye, eye - float(max(ls)) + TOL_NUM_M, cfg,
                ["olho_a_olho_m"], motivo=f"máximo em dz = {dzs[i_max] * 1e3:.2f} mm"))
    lim_min = eye - stroke + (0.0 if margem is None else float(margem))
    R.append(_r("comprimento do amortecedor (mínimo)", float(min(ls)), lim_min, float(min(ls)) - lim_min + TOL_NUM_M,
                cfg, ["olho_a_olho_m", "curso_amortecedor_m", "margem_curso_amortecedor_m"],
                motivo=f"mínimo em dz = {dzs[i_min] * 1e3:.2f} mm"
                       + ("; margem de curso a confirmar (0 usado)" if margem is None else ""),
                completa=margem is not None))

    bmin, bmax = float(cfg.valor("braco_min_m")), float(cfg.valor("braco_max_m"))
    a_ax = canto.p0["ROCKER_AXIS_A"]
    for nome, chave in (("braço r1 (push rod)", "PUSH_IN"), ("braço r2 (amortecedor)", "ROCKER_SPRING")):
        w = la.sub(canto.p0[chave], a_ax)
        rb = la.norm(la.sub(w, la.mul(eixo, la.dot(w, eixo))))
        R.append(_r(nome, rb, (bmin, bmax), min(rb - bmin, bmax - rb) + TOL_NUM_M, cfg, ["braco_min_m", "braco_max_m"]))

    giro = float(max(th) - min(th))
    gmax = float(cfg.valor("giro_max_rad"))
    R.append(_r("giro do rocker", giro, gmax, gmax - giro, cfg, ["giro_max_rad"]))
    ang = [math.acos(min(max(la.unit(la.sub(p["SPRING_CHASSIS"], p["ROCKER_SPRING"]))[0], -1.0), 1.0)) for p in P]
    amax = float(cfg.valor("amort_ang_max_rad"))
    R.append(_r("ângulo do amortecedor ao eixo X", float(max(ang)), amax, amax - float(max(ang)), cfg, ["amort_ang_max_rad"],
                motivo=f"pior estado em dz = {dzs[ang.index(max(ang))] * 1e3:.2f} mm "
                       "(direção do olhal do rocker ao olhal do chassi)"))

    pecas = [_pecas(p, cfg) for p in P]
    rpb = float(cfg.valor("r_perna_bandeja_m"))
    rj = float(cfg.valor("r_junta_m"))
    m_fix, m_aro, m_per, m_tir, m_pa = {}, {}, {}, {}, (math.inf, None)
    for p, pc_, dz in zip(P, pecas, dzs):
        if cena.fixos:
            fx = {}
            for c, a, b, r in pc_:
                f = min(_finita(folga_segmento(ob, a, b, r, PASSO_FOLGA_M), f"folga aos fixos ({c})") for ob in cena.fixos)
                fx[c] = min(fx.get(c, math.inf), f)
            _min_por_corpo(m_fix, fx, dz)
        _min_por_corpo(m_aro, _folga_aro(p, pc_, cena.aro), dz)
        _min_por_corpo(m_tir, _folga_tirante(p, pc_), dz)
        fp = {}
        for c, a, b, r in pc_:
            if c == "push rod":
                a = la.add(a, la.mul(la.unit(la.sub(b, a)), rj))
            f = min(_finita(dist_seg_seg(a, b, p[ext], p[inn]) - r - rpb, f"folga às pernas ({c})") for ext, inn in PERNAS)
            fp[c] = min(fp.get(c, math.inf), f)
        _min_por_corpo(m_per, fp, dz)
        O, A, B, C = p["PUSH_OUT"], p["PUSH_IN"], p["ROCKER_SPRING"], p["SPRING_CHASSIS"]
        f = _finita(dist_seg_seg(O, A, B, C) - float(cfg.valor("r_prod_m")) - float(cfg.valor("r_mola_m")),
                    "folga push rod × amortecedor")
        if f < m_pa[0]:
            m_pa = (f, dz)

    org_fix, fonte_fix = "META", FONTE_SEM_COLIDIR
    if cena.ref_hipotese:
        org_fix = "HIPOTESE"
        fonte_fix = (f"{FONTE_SEM_COLIDIR}; referencial STEP → carro da configuração, item transformacao_step_m "
                     f"(HIPOTESE, sem esferas REF_): {cena.ref_hipotese}")
    for corpo in CORPOS:
        nome = f"folga aos fixos: {corpo}"
        if not cena.fixos:
            R.append(Restricao(nome, None, 0.0, None, "NAO_VERIFICAVEL", "META", FONTE_SEM_COLIDIR,
                               "sem CAD: nenhum obstáculo fixo na cena"))
        else:
            v, dz = m_fix[corpo]
            R.append(Restricao(nome, v, 0.0, v, "OK" if v >= 0.0 else "VIOLADA", org_fix, fonte_fix,
                               f"mínimo em dz = {dz * 1e3:.2f} mm, a {len(cena.fixos)} primitivos fixos"))
    faro = float(cfg.valor("folga_aro_m"))
    for corpo in CORPOS:
        v, dz = m_aro[corpo]
        R.append(_r(f"folga ao aro: {corpo}", v, faro, v - faro, cfg, ["folga_aro_m", "aro_r_int_m", "aro_meia_largura_m"],
                    motivo=f"mínimo em dz = {dz * 1e3:.2f} mm (aro movido com a manga"
                           + ("; segmento real O→A" if corpo == "push rod" else "") + ")"))
    fper = float(cfg.valor("folga_pernas_m"))
    for corpo in CORPOS:
        v, dz = m_per[corpo]
        R.append(_r(f"folga às pernas das bandejas: {corpo}", v, fper, v - fper, cfg, ["folga_pernas_m", "r_perna_bandeja_m"],
                    motivo=f"mínimo em dz = {dz * 1e3:.2f} mm"
                           + (f"; sem os primeiros {rj * 1e3:.0f} mm do push rod a partir de O (fixação na bandeja)"
                              if corpo == "push rod" else "")))
    for corpo in CORPOS:
        v, dz = m_tir[corpo]
        R.append(Restricao(f"folga ao tirante: {corpo}", v, 0.0, v, "OK" if v >= 0.0 else "VIOLADA", "A_CONFIRMAR",
                           "sem raio nem folga declarados para o tirante: confere só que o envelope do corpo não toca "
                           "o eixo do tirante (TIE_IN–TIE_OUT)",
                           f"raio do tirante a confirmar (eixo, raio 0); mínimo em dz = {dz * 1e3:.2f} mm", completa=False))
    fpa = float(cfg.valor("folga_prod_amort_m"))
    R.append(_r("folga push rod × amortecedor", m_pa[0], fpa, m_pa[0] - fpa, cfg,
                ["folga_prod_amort_m", "r_prod_m", "r_mola_m"], motivo=f"mínimo em dz = {m_pa[1] * 1e3:.2f} mm"))

    R.append(_gabarito(cena, cfg, pecas))
    R.append(_aip(cena, cfg, pecas))
    R.extend(_esterçamento(canto, sols, cena, cfg))
    R.extend(_nao_modelados(cena))

    dist = {"pivo": None, "olhal": None}
    if cena.nos:
        dist = {"pivo": min(la.norm(la.sub(no, canto.p0["ROCKER_AXIS_A"])) for no in cena.nos),
                "olhal": min(la.norm(la.sub(no, canto.p0["SPRING_CHASSIS"])) for no in cena.nos)}
    veredito, motivo = _veredito(R, cfg)
    return Avaliacao(R, veredito, motivo, curvas, dist, n)


def _nao_modelados(cena):
    out = [Restricao(NOME_MANGA, None, 0.0, None, "NAO_VERIFICAVEL", "META",
                     f"{FONTE_SEM_COLIDIR}; spec §10 e §12 J4 (peças ausentes deixam a regra NÃO VERIFICÁVEL)",
                     "sem RODA_ modelado: o barril do aro trata o miolo como livre e o push rod nasce dentro dele (fase 1)")]
    if cena.pecas_moveis:
        out.append(Restricao(NOME_MOVEIS, None, 0.0, None, "NAO_VERIFICAVEL", "META",
                             f"{FONTE_SEM_COLIDIR}; spec §5 item 4 (folga contra as peças RODA_/DIR_ movidas)",
                             f"peças {', '.join(cena.pecas_moveis)} do STEP não entram na varredura da fase 1"))
    return out


def _lateral_ao_gabarito(cena, pecas, folga_gab):
    yc = float(cena.regras.get("y_centro_t12_m") or 0.0)
    m = math.inf
    for pc_ in pecas:
        for _, a, b, r in pc_:
            ya, yb = a[1] - yc, b[1] - yc
            dy = 0.0 if ya * yb <= 0.0 else min(abs(ya), abs(yb))
            m = min(m, dy - r - folga_gab - reg.LADO_M / 2)
    return m


def _na_caixa(prim, lo, hi):
    f = getattr(prim, "caixa_envolvente", None)
    if f is None:
        return True
    cmin, cmax = f()
    return all(cmin[k] <= hi[k] for k in range(3)) and all(cmax[k] >= lo[k] for k in range(3))


def _base_fixa(cena, x_ini, x_fim, z_min, z_max, yc, lo, hi):
    """Parte fixa da cena para o gabarito: (ocupação, resultado só com os fixos). Calculada uma vez por cena e região."""
    chave = (x_ini, x_fim, z_min, z_max, yc)
    if chave not in cena._cache:
        fixos = [ob for ob in cena.fixos if _na_caixa(ob, lo, hi)]
        xs, zs = reg.grade(x_ini, x_fim, z_min, z_max)
        occ = reg.ocupacao(fixos, xs, zs, yc, reg.amostras_gabarito(), reg.tolerancia(0.01))
        cena._cache[chave] = (occ, reg.caminho_livre(occ, zs), zs, xs)
    return cena._cache[chave]


def _gabarito(cena, cfg, pecas):
    nome = "gabarito T.1.2"
    rg = cena.regras
    folga_gab = float(cfg.valor("folga_gabarito_m"))
    itens = ["x_ini_t12_m", "x_fim_t12_m", "folga_gabarito_m"] + [n for n in ("z_min_t12_m", "z_max_t12_m") if n in cfg.itens]
    lat = _lateral_ao_gabarito(cena, pecas, folga_gab)
    info = f"(informativo: lateralmente, o corpo mais próximo fica a {lat * 1e3:.1f} mm da borda do gabarito, com raio e folga)"
    x_ini, x_fim = rg.get("x_ini_t12_m"), rg.get("x_fim_t12_m")
    if x_ini is None or x_fim is None:
        return _r(nome, None, folga_gab, None, cfg, itens, estado="NAO_VERIFICAVEL",
                  motivo=f"posição da coluna/pedal a confirmar (x_ini_t12_m, x_fim_t12_m) {info}")
    z_min, z_max = rg.get("z_min_t12_m"), rg.get("z_max_t12_m")
    if z_min is None or z_max is None:
        return _r(nome, None, folga_gab, None, cfg, itens, estado="NAO_VERIFICAVEL",
                  motivo=f"faixa de Z da base do gabarito a confirmar {info}")
    yc = float(rg.get("y_centro_t12_m") or 0.0)
    caps = [Capsula(a, b, r + folga_gab) for pc_ in pecas for _, a, b, r in pc_]
    tol = math.hypot(reg.RES_AMOSTRA_M * math.sqrt(2) / 2, 0.01 / 2) + 1e-3
    lo = (min(x_ini, x_fim) - tol, yc - reg.LADO_M / 2 - tol, z_min - tol)
    hi = (max(x_ini, x_fim) + tol, yc + reg.LADO_M / 2 + tol, z_max + reg.LADO_M + tol)
    rel = [c for c in caps if _na_caixa(c, lo, hi)]
    if not rel:
        return _r(nome, True, folga_gab, None, cfg, itens, estado="OK",
                  motivo=f"nenhum corpo da atuação (com raio + folga) entra na região varrida pelo gabarito {info}")
    occ_fix, so, zs, xs = _base_fixa(cena, x_ini, x_fim, z_min, z_max, yc, lo, hi)
    occ = reg.uniao(reg.ocupacao(rel, xs, zs, yc, reg.amostras_gabarito(), reg.tolerancia(0.01)), occ_fix)
    res = reg.caminho_livre(occ, zs)
    if res.livre:
        return _r(nome, True, folga_gab, None, cfg, itens, estado="OK", motivo=f"há altura livre com a atuação {info}")
    if not so.livre:
        return _r(nome, False, folga_gab, None, cfg, itens, estado="NAO_VERIFICAVEL", motivo=MOTIVO_CHASSI_BLOQUEIA)
    return _r(nome, False, folga_gab, None, cfg, itens, estado="VIOLADA",
              motivo=f"a atuação bloqueia a passagem do gabarito ({len(rel)} cápsulas na região) {info}")


def _aip(cena, cfg, pecas):
    nome = "AIP (F.8.6.1)"
    f = reg.limite_aip(cena.regras.get("x_face_traseira_aip_m"))
    if f is None:
        return _r(nome, None, 0.0, None, cfg, ["x_face_traseira_aip_m"], estado="NAO_VERIFICAVEL",
                  motivo="X da face traseira da AIP a confirmar")
    v = min(_finita(float(min(f(a), f(b))) - r, "folga à AIP") for pc_ in pecas for _, a, b, r in pc_)
    return _r(nome, v, 0.0, v, cfg, ["x_face_traseira_aip_m"],
              motivo="folga em X do ponto mais à frente dos corpos (com raio) à face traseira da AIP")


def _esterçamento(canto, sols, cena, cfg):
    nomes = ("esterçamento: folga ao aro", "esterçamento: folga ao tirante")
    curso = cfg.valor("curso_cremalheira_m")
    if curso is None:
        return [_r(nm, None, None, None, cfg, ["curso_cremalheira_m"], estado="NAO_VERIFICAVEL",
                   motivo="curso da cremalheira a confirmar") for nm in nomes]
    curso = float(curso)
    est = _esterçar(canto, sols, curso)
    m_aro, m_tir = (math.inf, None), (math.inf, None)
    for s in est:
        p = _pontos(canto, s)
        pc_ = _pecas(p, cfg)
        fa = min(_folga_aro(p, pc_, cena.aro).values())
        ft = min(_folga_tirante(p, pc_).values())
        if fa < m_aro[0]:
            m_aro = (fa, s)
        if ft < m_tir[0]:
            m_tir = (ft, s)
    faro = float(cfg.valor("folga_aro_m"))
    onde = lambda s: f"pior estado em dz = {s.curso * 1e3:.2f} mm, cremalheira = {s.cremalheira * 1e3:+.2f} mm"  # noqa: E731
    return [_r(nomes[0], m_aro[0], faro, m_aro[0] - faro, cfg, ["curso_cremalheira_m", "folga_aro_m"],
               motivo=f"{onde(m_aro[1])} (cremalheira em ±{curso * 1e3:.1f} mm)"),
            Restricao(nomes[1], m_tir[0], 0.0, m_tir[0], "OK" if m_tir[0] >= 0.0 else "VIOLADA", "A_CONFIRMAR",
                      f"sem raio nem folga declarados para o tirante; curso_cremalheira_m: "
                      f"{cfg.item('curso_cremalheira_m').fonte}",
                      f"raio do tirante a confirmar (eixo, raio 0); {onde(m_tir[1])}", completa=False)]


def _erro_de_valor(a, b):
    fa = {r.nome: r.folga for r in a.restricoes}
    out = []
    for r in b.restricoes:
        f0 = fa.get(r.nome)
        if r.estado == "OK" and r.folga is not None and f0 is not None and 0.0 <= r.folga < abs(float(r.folga) - float(f0)):
            out.append(r.nome)
    return sorted(out)


def avaliar_convergido(construcao, cena, cfg, n0=25):
    """Avalia com n e 2n; dobra até 8·n0 se estado ou veredito mudar (ver o original)."""
    n = int(n0)
    a = avaliar(construcao, cena, cfg, n)
    hist = [n]
    while True:
        b = avaliar(construcao, cena, cfg, 2 * n)
        hist.append(2 * n)
        ea, eb = a.estados(), b.estados()
        if ea == eb and a.veredito == b.veredito:
            ind = _erro_de_valor(a, b)
            if not ind or 2 * n >= 8 * n0:
                b.resolucoes = hist
                b.indeterminadas = ind
                if ind:
                    b.motivo = ((b.motivo + "; ") if b.motivo else "") + ("folga menor que o erro da medida em: " + ", ".join(ind))
                return b
            a, n = b, 2 * n
            continue
        if 2 * n >= 8 * n0:
            difs = sorted(k for k in set(ea) | set(eb) if ea.get(k) != eb.get(k))
            b.resolucoes = hist
            b.veredito = "INVIAVEL"
            b.motivo = (f"resolução não convergiu: estados mudaram de n = {n} para n = {2 * n} em {difs or ['veredito']}"
                        + (f"; {b.motivo}" if b.motivo else ""))
            return b
        a, n = b, 2 * n
