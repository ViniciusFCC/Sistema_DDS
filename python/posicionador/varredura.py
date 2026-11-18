"""
Varredura do curso e avaliação de um candidato do posicionador (EDR-076, TC-POS-060 a 064).

Um candidato é uma `mecanismo.Construcao` (canto FL completo, com o grupo pushrod). `avaliar` resolve o canto com
`kinematics_model.Corner` em n pontos do curso da roda, dz ∈ [−curso_droop_m, +curso_bump_m] (continuação a partir do
estático), e confere cada restrição em todos os estados:
- MR(0) = mr_alvo ± 0,01 (tolerância do plano da fase 1; a mesma escala do custo do t11_atuacao.py); MR [wheel/spring]
  sempre de `kinematics_model.motion_ratio` (não há segunda implementação de MR aqui);
- variação de MR = max/min − 1 do MR local nos n pontos ≤ mr_var_max;
- comprimento do amortecedor |B − C| ∈ [EYE − STROKE + margem, EYE] em todo o curso; margem nula (A_CONFIRMAR) → 0 m,
  com a restrição marcada como parcial (veredito no máximo CONDICIONAL);
- braços r1 (push rod) e r2 (amortecedor) do rocker, medidos ao eixo, em [braco_min_m, braco_max_m];
- giro do rocker (max − min do ângulo no curso) ≤ giro_max_rad;
- ângulo do amortecedor (B → C) ao eixo +X ≤ amort_ang_max_rad, no pior estado do curso;
- folgas dos corpos da atuação: push rod = cápsula O–A (r_prod_m); rocker = cápsulas Pv–A e Pv–B (r_junta_m) e esfera
  em Pv (r_pivo_m); amortecedor = cápsula B–C (r_mola_m). Cada corpo é conferido:
  · aos obstáculos fixos da cena (folga ≥ 0: a spec pede "sem colidir"; a configuração não declara margem ao chassi);
  · ao aro, um `Barril` movido com a manga em cada estado (centro = WHEEL_CENTER, eixo = SPINDLE_PT − WHEEL_CENTER),
    com folga ≥ folga_aro_m; o push rod é o segmento real O→A inteiro;
  · às pernas das bandejas (cápsulas LCA_OUT–LCA_IN_F/R e UCA_OUT–UCA_IN_F/R movidas, raio r_perna_bandeja_m), com folga
    ≥ folga_pernas_m. O push rod é fixado na bandeja inferior em O: os primeiros r_junta_m do push rod a partir de O
    (a região da fixação) não entram nessa conferência;
  · ao eixo do tirante (TIE_IN movido pela cremalheira – TIE_OUT), com raio 0 e folga ≥ 0: o raio do tirante não tem
    fonte, a restrição fica parcial ("raio do tirante a confirmar");
  e o push rod ao amortecedor (folga ≥ folga_prod_amort_m). Cápsula × cápsula usa a distância exata entre segmentos
  (`geometria.dist_seg_seg`); cápsula × primitivo usa `geometria.folga_segmento` (conservadora: desconta passo/2);
- gabarito T.1.2 (`regulamento.trajetoria_t12`) com os corpos inflados de folga_gabarito_m em todos os estados;
- AIP (F.8.6.1, `regulamento.limite_aip`): todo corpo atrás da face traseira da AIP;
- esterçamento: com curso_cremalheira_m, os mesmos estados com a cremalheira em ±curso (deslocamento máximo para cada
  lado a partir do centro; se o dado da equipe for o curso total, a configuração recebe a metade), folga ao aro e ao
  eixo do tirante. Sem o curso: NAO_VERIFICAVEL.
Item nulo da configuração (x_ini_t12_m, x_fim_t12_m, x_face_traseira_aip_m, curso_cremalheira_m) → a restrição sai
NAO_VERIFICAVEL. Veredito: INVIAVEL se alguma restrição é VIOLADA; CONDICIONAL se nenhuma é VIOLADA mas alguma é
NAO_VERIFICAVEL, parcial ou há item A_CONFIRMAR na configuração; VIAVEL só sem nada disso.

`avaliar` nunca levanta exceção: construção sem hardpoints → INVIAVEL "construção: …"; qualquer exceção do solver num
ponto da varredura → INVIAVEL "cinemática sem solução em dz = … mm …".
"""
from dataclasses import dataclass, field
from typing import Any

import numpy as np

import kinematics_model as km
from posicionador import regulamento as reg
from posicionador.geometria import Barril, Caixa, Capsula, Esfera, dist_seg_seg, folga_segmento

TOL_MR0 = 0.01            # MR(0) = mr_alvo ± 0,01 (plano da fase 1, Task 6; escala do custo do t11_atuacao.py)
TOL_NUM_M = 1e-9          # tolerância numérica de comprimento (o solver fecha a 1e-10); não é margem de engenharia
TOL_RAMO_M = 1e-7         # Ls da continuação × Ls do motion_ratio no mesmo dz: diferença maior = outro ramo do rocker
PASSO_FOLGA_M = 0.002     # passo de folga_segmento (padrão da geometria)
PASSOS_CREMALHEIRA = 4    # continuação em esterço: 0 → ±curso em 4 passos
ESTADOS = ("OK", "VIOLADA", "NAO_VERIFICAVEL")
FORCA_ORIGEM = ("REGRA", "META", "MARGEM_EQUIPE", "HIPOTESE", "A_CONFIRMAR")   # da mais forte para a mais fraca
CORPOS = ("push rod", "rocker", "amortecedor")
PERNAS = (("LCA_OUT", "LCA_IN_F"), ("LCA_OUT", "LCA_IN_R"), ("UCA_OUT", "UCA_IN_F"), ("UCA_OUT", "UCA_IN_R"))


@dataclass
class Restricao:
    nome: str
    valor: Any            # medido (SI); None se não verificável
    limite: Any           # número ou (mín, máx)
    folga: float | None   # distância ao limite (positiva = cumprida)
    estado: str           # "OK" | "VIOLADA" | "NAO_VERIFICAVEL"
    origem: str           # origem mais fraca dos itens da configuração que dão o limite
    fonte: str
    motivo: str | None = None
    completa: bool = True  # False: verificada com valor provisório (margem 0, raio 0) → veredito no máximo CONDICIONAL


@dataclass
class Cena:
    fixos: list           # primitivos fixos (m, referencial do carro)
    nos: list             # cad_step.No com pos_m no referencial do carro
    aro: tuple            # (r_int_m, meia_largura_m)
    regras: dict          # x_ini_t12_m, x_fim_t12_m, z_min_t12_m, z_max_t12_m, y_centro_t12_m, x_face_traseira_aip_m
    nao_modelado: list = field(default_factory=list)   # o que a cena não representa (texto)


@dataclass
class Avaliacao:
    restricoes: list
    veredito: str          # "VIAVEL" | "CONDICIONAL" | "INVIAVEL"
    motivo: str | None
    curvas: dict           # dz_m, MR [wheel/spring], Ls_m, angulo_fora_do_plano_rad, theta_rocker_rad
    dist_no_m: dict        # {"pivo": m | None, "olhal": m | None}
    n: int
    resolucoes: list = field(default_factory=list)   # n avaliados por avaliar_convergido

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


# ------------------------------------------------------------------ cena
def regras_da_config(cfg):
    """Regras do regulamento a partir da configuração (None = a confirmar). A faixa de Z da base do gabarito T.1.2 não
    está na configuração: None até a cena trazê-la; o gabarito fica centrado em Y = 0 (plano de simetria do carro)."""
    return {"x_ini_t12_m": cfg.valor("x_ini_t12_m"), "x_fim_t12_m": cfg.valor("x_fim_t12_m"),
            "z_min_t12_m": None, "z_max_t12_m": None, "y_centro_t12_m": 0.0,
            "x_face_traseira_aip_m": cfg.valor("x_face_traseira_aip_m")}


def _aro(cfg):
    return (float(cfg.valor("aro_r_int_m")), float(cfg.valor("aro_meia_largura_m")))


def cena_sem_cad(cfg):
    """Cena só com o aro (sem obstáculos fixos nem nós): a folga aos fixos sai NAO_VERIFICAVEL."""
    return Cena(fixos=[], nos=[], aro=_aro(cfg), regras=regras_da_config(cfg),
                nao_modelado=["CAD ausente: chassi e peças fixas não modelados"])


def cena_do_step(montagem, R, t, cfg, z_t12_m=None):
    """Cena do STEP: obstáculos fixos (`cad_step.obstaculos_fixos`) e nós do chassi, no referencial do carro
    (p = R @ p_step + t). A folga vem só dos primitivos de `obstaculos_fixos` (nunca de `Tubo.r_ext_m`). As peças RODA_,
    BANDEJA_ e DIR_ ainda não entram (o aro vem da configuração); ficam em `nao_modelado`. `z_t12_m` = (z_min, z_max) da
    base do gabarito T.1.2, se a equipe a declarar."""
    from posicionador import cad_step
    R, t = np.asarray(R, dtype=float), np.asarray(t, dtype=float)
    fixos = cad_step.obstaculos_fixos(montagem, R, t)
    _, nos = cad_step.tubos_e_nos(montagem)
    nos_c = [cad_step.No(pos_m=R @ np.asarray(n.pos_m, dtype=float) + t, n_ramos=n.n_ramos, triangulado=n.triangulado,
                         tubos=list(n.tubos), espalhamento_m=n.espalhamento_m) for n in nos]
    regras = regras_da_config(cfg)
    if z_t12_m is not None:
        regras.update(z_min_t12_m=float(z_t12_m[0]), z_max_t12_m=float(z_t12_m[1]))
    moveis = sorted({p.categoria for p in montagem.pecas if p.categoria in ("RODA_FE", "RODA_FD", "BANDEJA_FE",
                                                                              "BANDEJA_FD", "DIR")})
    nao = [f"peças móveis do STEP ({', '.join(moveis)}) não entram na varredura; o aro vem da configuração"] if moveis else []
    return Cena(fixos=fixos, nos=nos_c, aro=_aro(cfg), regras=regras, nao_modelado=nao)


# ------------------------------------------------------------------ procedência
def _proc(cfg, *nomes):
    """(origem mais fraca, fonte) dos itens da configuração."""
    its = [(n, cfg.item(n)) for n in nomes]
    origem = max((it.origem for _, it in its), key=FORCA_ORIGEM.index)
    return origem, "; ".join(f"{n} ({it.origem}): {it.fonte}" for n, it in its)


def _r(nome, valor, limite, folga, cfg, itens, motivo=None, completa=True, estado=None):
    """Restrição com a procedência dos itens da configuração; estado pela folga (≥ 0 = OK) se não for dado."""
    origem, fonte = _proc(cfg, *itens)
    if estado is None:
        estado = "OK" if folga >= 0.0 else "VIOLADA"
    return Restricao(nome, valor, limite, folga, estado, origem, fonte, motivo, completa)


# ------------------------------------------------------------------ cinemática
def _resolver(canto, dz, steer, q0, phi0):
    try:
        return canto.solve(dz, steer, q0=q0, phi0=phi0)
    except Exception as e:  # noqa: BLE001  (KinematicsError, LinAlgError, ValueError...: todos viram INVIAVEL)
        raise _SemSolucao(dz, steer, e) from e


def _varrer(canto, dzs):
    """Soluções nos dz (continuação do estático para cima e para baixo, como kinematics_model.sweep)."""
    s0 = _resolver(canto, 0.0, 0.0, None, 0.0)
    out = {}
    for grupo in (sorted(d for d in dzs if d >= 0.0), sorted((d for d in dzs if d < 0.0), reverse=True)):
        cur = s0
        for d in grupo:
            cur = _resolver(canto, float(d), 0.0, cur.q, cur.phi)
            out[float(d)] = cur
    return s0, [out[float(d)] for d in dzs]


def _esterçar(canto, sols, curso):
    """Para cada estado do curso, a mesma pose com a cremalheira em +curso e −curso (continuação em passos)."""
    out = []
    for s in sols:
        for sinal in (1.0, -1.0):
            cur = s
            for k in range(1, PASSOS_CREMALHEIRA + 1):
                cur = _resolver(canto, s.travel, sinal * curso * k / PASSOS_CREMALHEIRA, cur.q, cur.phi)
            out.append(cur)
    return out


def _unit(v):
    return v / np.linalg.norm(v)


def _pontos(canto, s):
    p = {k: canto.pt(s, k) for k in ("PUSH_OUT", "PUSH_IN", "ROCKER_AXIS_A", "ROCKER_SPRING", "SPRING_CHASSIS",
                                     "WHEEL_CENTER", "SPINDLE_PT", "TIE_IN", "TIE_OUT", "LCA_OUT", "UCA_OUT",
                                     "LCA_IN_F", "LCA_IN_R", "UCA_IN_F", "UCA_IN_R")}
    return p


def _pecas(p, cfg):
    """Peças da atuação no estado: (corpo, a, b, raio)."""
    O, A, Pv, B, C = (p[k] for k in ("PUSH_OUT", "PUSH_IN", "ROCKER_AXIS_A", "ROCKER_SPRING", "SPRING_CHASSIS"))
    rj = float(cfg.valor("r_junta_m"))
    return [("push rod", O, A, float(cfg.valor("r_prod_m"))),
            ("rocker", Pv, A, rj), ("rocker", Pv, B, rj), ("rocker", Pv, Pv, float(cfg.valor("r_pivo_m"))),
            ("amortecedor", B, C, float(cfg.valor("r_mola_m")))]


def _barril(p, aro):
    c = p["WHEEL_CENTER"]
    return Barril(c, _unit(p["SPINDLE_PT"] - c), aro[0], aro[1])


def _folga_aro(p, pecas, aro):
    """Folga de cada corpo ao aro movido com a manga {corpo: m}."""
    b = _barril(p, aro)
    out = {}
    for corpo, a, bb, r in pecas:
        f = folga_segmento(b, a, bb, r, PASSO_FOLGA_M)
        out[corpo] = min(out.get(corpo, np.inf), f)
    return out


def _folga_tirante(p, pecas):
    out = {}
    for corpo, a, b, r in pecas:
        f = dist_seg_seg(a, b, p["TIE_IN"], p["TIE_OUT"]) - r
        out[corpo] = min(out.get(corpo, np.inf), f)
    return out


def _min_por_corpo(acum, novos, dz):
    for corpo, v in novos.items():
        if corpo not in acum or v < acum[corpo][0]:
            acum[corpo] = (v, dz)


# ------------------------------------------------------------------ avaliação
FONTES_FALHA = {"cinemática": "kinematics_model.Corner (MODEL; REFERENCE = OptimumKinematics, EDR-004)",
                "construção": "posicionador.mecanismo.construir",
                "avaliação": "posicionador.varredura.avaliar"}


def _inviavel(n, motivo, nome="cinemática"):
    """Avaliação sem resultado: uma única restrição VIOLADA com o motivo."""
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
    """Avalia o candidato em n pontos do curso. Nunca levanta exceção (ver o docstring do módulo)."""
    if construcao is None or construcao.hardpoints is None:
        motivo = getattr(construcao, "motivo", None) or "sem hardpoints"
        return _inviavel(n, f"construção: {motivo}", "construção")
    try:
        return _avaliar(construcao, cena, cfg, int(n))
    except _SemSolucao as e:
        return _inviavel(n, str(e))
    except Exception as e:  # noqa: BLE001  (nada escapa: a falha vira veredito com motivo)
        return _inviavel(n, f"avaliação sem resultado: {type(e).__name__}: {e}", "avaliação")


def _avaliar(construcao, cena, cfg, n):
    try:
        canto = km.Corner(construcao.hardpoints, "FL")
    except Exception as e:  # noqa: BLE001
        raise _SemSolucao(0.0, 0.0, e) from e
    if not canto.has_push:
        raise ValueError("canto sem grupo pushrod")
    droop, bump = float(cfg.valor("curso_droop_m")), float(cfg.valor("curso_bump_m"))
    dzs = np.linspace(-droop, bump, n)
    s0, sols = _varrer(canto, dzs)

    # MR local (kinematics_model.motion_ratio) e conferência do ramo do rocker
    def mr_em(dz, ls_cont):
        try:
            m = km.motion_ratio(canto, float(dz))
        except Exception as e:  # noqa: BLE001
            raise _SemSolucao(float(dz), 0.0, e) from e
        if ls_cont is not None and abs(m["spring_length_m"] - ls_cont) > TOL_RAMO_M:
            raise _SemSolucao(float(dz), 0.0, km.KinematicsError(
                f"MR local resolvido em outro ramo do rocker (Ls {m['spring_length_m']:.9f} × {ls_cont:.9f} m)"))
        return m["mr_wheel_per_spring"]

    ls = np.array([canto.spring_length(s) for s in sols])
    mr = np.array([mr_em(d, l) for d, l in zip(dzs, ls)])
    mr0 = mr_em(0.0, canto.spring_length(s0))
    th = np.array([s.phi for s in sols])
    P = [_pontos(canto, s) for s in sols]
    eixo = _unit(canto.p0["ROCKER_AXIS_B"] - canto.p0["ROCKER_AXIS_A"])     # eixo do rocker (fixo no chassi)
    fora = np.array([float(np.arcsin(min(1.0, abs(_unit(p["PUSH_IN"] - p["PUSH_OUT"]) @ eixo)))) for p in P])
    curvas = {"dz_m": dzs, "MR [wheel/spring]": mr, "Ls_m": ls, "angulo_fora_do_plano_rad": fora,
              "theta_rocker_rad": th}
    R = []

    # MR
    alvo = float(cfg.valor("mr_alvo"))
    R.append(_r("MR(0)", mr0, (alvo - TOL_MR0, alvo + TOL_MR0), TOL_MR0 - abs(mr0 - alvo), cfg, ["mr_alvo"],
                motivo=f"tolerância ± {TOL_MR0} do plano da fase 1 (Task 6)"))
    var = float(mr.max() / mr.min() - 1.0)
    vmax = float(cfg.valor("mr_var_max"))
    R.append(_r("variação de MR", var, vmax, vmax - var, cfg, ["mr_var_max"],
                motivo=f"MR de {mr.min():.4f} a {mr.max():.4f} em {n} pontos de dz ∈ [{-droop * 1e3:.1f}; "
                       f"{bump * 1e3:.1f}] mm"))

    # comprimento do amortecedor
    eye, stroke = float(cfg.valor("olho_a_olho_m")), float(cfg.valor("curso_amortecedor_m"))
    margem = cfg.valor("margem_curso_amortecedor_m")
    i_max, i_min = int(np.argmax(ls)), int(np.argmin(ls))
    R.append(_r("comprimento do amortecedor (máximo)", float(ls.max()), eye, eye - float(ls.max()) + TOL_NUM_M, cfg,
                ["olho_a_olho_m"], motivo=f"máximo em dz = {dzs[i_max] * 1e3:.2f} mm"))
    lim_min = eye - stroke + (0.0 if margem is None else float(margem))
    R.append(_r("comprimento do amortecedor (mínimo)", float(ls.min()), lim_min, float(ls.min()) - lim_min + TOL_NUM_M,
                cfg, ["olho_a_olho_m", "curso_amortecedor_m", "margem_curso_amortecedor_m"],
                motivo=f"mínimo em dz = {dzs[i_min] * 1e3:.2f} mm"
                       + ("; margem de curso a confirmar (0 usado)" if margem is None else ""),
                completa=margem is not None))

    # braços do rocker (distância ao eixo, no estático)
    bmin, bmax = float(cfg.valor("braco_min_m")), float(cfg.valor("braco_max_m"))
    a_ax = canto.p0["ROCKER_AXIS_A"]
    for nome, chave in (("braço r1 (push rod)", "PUSH_IN"), ("braço r2 (amortecedor)", "ROCKER_SPRING")):
        w = canto.p0[chave] - a_ax
        rb = float(np.linalg.norm(w - (w @ eixo) * eixo))
        R.append(_r(nome, rb, (bmin, bmax), min(rb - bmin, bmax - rb), cfg, ["braco_min_m", "braco_max_m"]))

    # giro e ângulo do amortecedor
    giro = float(th.max() - th.min())
    gmax = float(cfg.valor("giro_max_rad"))
    R.append(_r("giro do rocker", giro, gmax, gmax - giro, cfg, ["giro_max_rad"]))
    ang = np.array([float(np.arccos(np.clip(_unit(p["SPRING_CHASSIS"] - p["ROCKER_SPRING"])[0], -1.0, 1.0)))
                    for p in P])
    amax = float(cfg.valor("amort_ang_max_rad"))
    R.append(_r("ângulo do amortecedor ao eixo X", float(ang.max()), amax, amax - float(ang.max()), cfg,
                ["amort_ang_max_rad"], motivo=f"pior estado em dz = {dzs[int(np.argmax(ang))] * 1e3:.2f} mm "
                                               "(direção do olhal do rocker ao olhal do chassi)"))

    # folgas em todos os estados
    pecas = [_pecas(p, cfg) for p in P]
    rpb = float(cfg.valor("r_perna_bandeja_m"))
    rj = float(cfg.valor("r_junta_m"))
    m_fix, m_aro, m_per, m_tir, m_pa = {}, {}, {}, {}, (np.inf, None)
    for p, pc_, dz in zip(P, pecas, dzs):
        if cena.fixos:
            fx = {}
            for c, a, b, r in pc_:
                f = min(folga_segmento(ob, a, b, r, PASSO_FOLGA_M) for ob in cena.fixos)
                fx[c] = min(fx.get(c, np.inf), f)
            _min_por_corpo(m_fix, fx, dz)
        _min_por_corpo(m_aro, _folga_aro(p, pc_, cena.aro), dz)
        _min_por_corpo(m_tir, _folga_tirante(p, pc_), dz)
        fp = {}
        for c, a, b, r in pc_:
            if c == "push rod":       # a fixação em O (primeiros r_junta_m) não conta contra a própria bandeja
                a = a + rj * _unit(b - a)
            f = min(dist_seg_seg(a, b, p[ext], p[inn]) for ext, inn in PERNAS) - r - rpb
            fp[c] = min(fp.get(c, np.inf), f)
        _min_por_corpo(m_per, fp, dz)
        O, A, B, C = p["PUSH_OUT"], p["PUSH_IN"], p["ROCKER_SPRING"], p["SPRING_CHASSIS"]
        f = dist_seg_seg(O, A, B, C) - float(cfg.valor("r_prod_m")) - float(cfg.valor("r_mola_m"))
        if f < m_pa[0]:
            m_pa = (f, dz)

    for corpo in CORPOS:
        nome = f"folga aos fixos: {corpo}"
        if not cena.fixos:
            R.append(Restricao(nome, None, 0.0, None, "NAO_VERIFICAVEL", "META",
                               "spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a "
                               "configuração não declara margem ao chassi)", "sem CAD: nenhum obstáculo fixo na cena"))
        else:
            v, dz = m_fix[corpo]
            R.append(Restricao(nome, v, 0.0, v, "OK" if v >= 0.0 else "VIOLADA", "META",
                               "spec do posicionador §1 (EDR-076): sem colidir com nenhuma peça do CAD (folga ≥ 0; a "
                               "configuração não declara margem ao chassi)",
                               f"mínimo em dz = {dz * 1e3:.2f} mm, a {len(cena.fixos)} primitivos fixos"))
    faro = float(cfg.valor("folga_aro_m"))
    for corpo in CORPOS:
        v, dz = m_aro[corpo]
        R.append(_r(f"folga ao aro: {corpo}", v, faro, v - faro, cfg,
                    ["folga_aro_m", "aro_r_int_m", "aro_meia_largura_m"],
                    motivo=f"mínimo em dz = {dz * 1e3:.2f} mm (aro movido com a manga"
                           + ("; segmento real O→A" if corpo == "push rod" else "") + ")"))
    fper = float(cfg.valor("folga_pernas_m"))
    for corpo in CORPOS:
        v, dz = m_per[corpo]
        R.append(_r(f"folga às pernas das bandejas: {corpo}", v, fper, v - fper, cfg,
                    ["folga_pernas_m", "r_perna_bandeja_m"],
                    motivo=f"mínimo em dz = {dz * 1e3:.2f} mm"
                           + (f"; sem os primeiros {rj * 1e3:.0f} mm do push rod a partir de O (fixação na bandeja)"
                              if corpo == "push rod" else "")))
    for corpo in CORPOS:
        v, dz = m_tir[corpo]
        R.append(Restricao(f"folga ao tirante: {corpo}", v, 0.0, v, "OK" if v >= 0.0 else "VIOLADA", "A_CONFIRMAR",
                           "sem raio nem folga declarados para o tirante: confere só que o envelope do corpo não toca "
                           "o eixo do tirante (TIE_IN–TIE_OUT)",
                           f"raio do tirante a confirmar (eixo, raio 0); mínimo em dz = {dz * 1e3:.2f} mm",
                           completa=False))
    fpa = float(cfg.valor("folga_prod_amort_m"))
    R.append(_r("folga push rod × amortecedor", m_pa[0], fpa, m_pa[0] - fpa, cfg,
                ["folga_prod_amort_m", "r_prod_m", "r_mola_m"], motivo=f"mínimo em dz = {m_pa[1] * 1e3:.2f} mm"))

    R.append(_gabarito(cena, cfg, pecas))
    R.append(_aip(cena, cfg, pecas))
    R.extend(_esterçamento(canto, sols, cena, cfg))

    dist = {"pivo": None, "olhal": None}
    if cena.nos:
        pos = np.array([np.asarray(no.pos_m, dtype=float) for no in cena.nos])
        dist = {"pivo": float(np.linalg.norm(pos - canto.p0["ROCKER_AXIS_A"], axis=1).min()),
                "olhal": float(np.linalg.norm(pos - canto.p0["SPRING_CHASSIS"], axis=1).min())}
    veredito, motivo = _veredito(R, cfg)
    return Avaliacao(R, veredito, motivo, curvas, dist, n)


def _lateral_ao_gabarito(cena, pecas, folga_gab):
    """Menor distância lateral (Y) dos corpos, com raio e folga, à borda do gabarito (informativo)."""
    yc = float(cena.regras.get("y_centro_t12_m") or 0.0)
    m = np.inf
    for pc_ in pecas:
        for _, a, b, r in pc_:
            ya, yb = a[1] - yc, b[1] - yc
            dy = 0.0 if ya * yb <= 0.0 else min(abs(ya), abs(yb))
            m = min(m, dy - r - folga_gab - reg.LADO_M / 2)
    return m


def _caixa_envolvente(prim):
    """(mín, máx) da caixa alinhada aos eixos que contém o primitivo; None se o tipo não é conhecido (fica no cálculo)."""
    if isinstance(prim, Capsula):
        return np.minimum(prim.a, prim.b) - prim.r, np.maximum(prim.a, prim.b) + prim.r
    if isinstance(prim, Esfera):
        return prim.c - prim.r, prim.c + prim.r
    if isinstance(prim, Caixa):
        ext = np.abs(np.asarray(prim.eixos, dtype=float)).T @ np.asarray(prim.meias, dtype=float)
        return prim.centro - ext, prim.centro + ext
    return None


def _na_caixa(prim, lo, hi):
    cx = _caixa_envolvente(prim)
    return cx is None or bool(np.all(cx[0] <= hi) and np.all(cx[1] >= lo))


def _gabarito(cena, cfg, pecas):
    nome = "gabarito T.1.2"
    rg = cena.regras
    folga_gab = float(cfg.valor("folga_gabarito_m"))
    itens = ["x_ini_t12_m", "x_fim_t12_m", "folga_gabarito_m"]
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
    caps = [Capsula(np.asarray(a, float), np.asarray(b, float), r + folga_gab) for pc_ in pecas for _, a, b, r in pc_]
    # filtro exato: a trajetória só ocupa a célula com sdf ≤ tol (regulamento); cápsula cuja caixa envolvente fica a mais
    # de tol da região varrida pelo gabarito não muda o resultado
    tol = float(np.hypot(reg.RES_AMOSTRA_M * np.sqrt(2) / 2, 0.01 / 2)) + 1e-3
    lo = np.array([min(x_ini, x_fim), yc - reg.LADO_M / 2, z_min]) - tol
    hi = np.array([max(x_ini, x_fim), yc + reg.LADO_M / 2, z_max + reg.LADO_M]) + tol
    rel = [c for c in caps if _na_caixa(c, lo, hi)]
    if not rel:
        return _r(nome, True, folga_gab, None, cfg, itens, estado="OK",
                  motivo=f"nenhum corpo da atuação (com raio + folga) entra na região varrida pelo gabarito {info}")
    fixos = [ob for ob in cena.fixos if _na_caixa(ob, lo, hi)]
    res = reg.trajetoria_t12(fixos + rel, x_ini, x_fim, z_min, z_max, y_centro=yc)
    if res.livre:
        return _r(nome, True, folga_gab, None, cfg, itens, estado="OK", motivo=f"há altura livre com a atuação {info}")
    so = reg.trajetoria_t12(fixos, x_ini, x_fim, z_min, z_max, y_centro=yc)
    if not so.livre:
        return _r(nome, False, folga_gab, None, cfg, itens, estado="NAO_VERIFICAVEL",
                  motivo="o chassi sozinho já bloqueia o gabarito: a atuação não é a causa")
    return _r(nome, False, folga_gab, None, cfg, itens, estado="VIOLADA",
              motivo=f"a atuação bloqueia a passagem do gabarito ({len(rel)} cápsulas na região) {info}")


def _aip(cena, cfg, pecas):
    nome = "AIP (F.8.6.1)"
    f = reg.limite_aip(cena.regras.get("x_face_traseira_aip_m"))
    if f is None:
        return _r(nome, None, 0.0, None, cfg, ["x_face_traseira_aip_m"], estado="NAO_VERIFICAVEL",
                  motivo="X da face traseira da AIP a confirmar")
    v = min(float(min(f(a), f(b))) - r for pc_ in pecas for _, a, b, r in pc_)
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
    m_aro, m_tir = (np.inf, None), (np.inf, None)
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
    onde = lambda s: f"pior estado em dz = {s.travel * 1e3:.2f} mm, cremalheira = {s.steer * 1e3:+.2f} mm"  # noqa: E731
    return [_r(nomes[0], m_aro[0], faro, m_aro[0] - faro, cfg, ["curso_cremalheira_m", "folga_aro_m"],
               motivo=f"{onde(m_aro[1])} (cremalheira em ±{curso * 1e3:.1f} mm)"),
            Restricao(nomes[1], m_tir[0], 0.0, m_tir[0], "OK" if m_tir[0] >= 0.0 else "VIOLADA", "A_CONFIRMAR",
                      f"sem raio nem folga declarados para o tirante; curso_cremalheira_m: "
                      f"{cfg.item('curso_cremalheira_m').fonte}",
                      f"raio do tirante a confirmar (eixo, raio 0); {onde(m_tir[1])}", completa=False)]


def avaliar_convergido(construcao, cena, cfg, n0=25):
    """Avalia com n e 2n; se algum estado (ou o veredito) mudar, dobra até 8·n0. Sem convergência: INVIAVEL com motivo
    "resolução não convergiu". Devolve a avaliação da maior resolução usada."""
    n = int(n0)
    a = avaliar(construcao, cena, cfg, n)
    hist = [n]
    while True:
        b = avaliar(construcao, cena, cfg, 2 * n)
        hist.append(2 * n)
        ea, eb = a.estados(), b.estados()
        if ea == eb and a.veredito == b.veredito:
            b.resolucoes = hist
            return b
        if 2 * n >= 8 * n0:
            difs = sorted(k for k in set(ea) | set(eb) if ea.get(k) != eb.get(k))
            b.resolucoes = hist
            b.veredito = "INVIAVEL"
            b.motivo = (f"resolução não convergiu: estados mudaram de n = {n} para n = {2 * n} em {difs or ['veredito']}"
                        + (f"; {b.motivo}" if b.motivo else ""))
            return b
        a, n = b, 2 * n
