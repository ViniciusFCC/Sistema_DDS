"""
Ferramenta do posicionador da atuação dianteira (EDR-076, spec §6): busca candidatos para push rod, rocker e amortecedor
(ou avalia a v20) e grava as saídas numa pasta.

Uso (na raiz do repositório):
    uv run python -X utf8 tools/posicionar_atuacao.py --step ARQ.step --saida PASTA [--amostras N] [--semente S]
        [--refinos R] [--caixa=xmin,ymin,zmin,xmax,ymax,zmax] [--hardpoints CSV] [--config JSON]
    uv run python -X utf8 tools/posicionar_atuacao.py --avaliar-v20 --saida PASTA [--step ARQ.step]

Saídas em PASTA:
- `relatorio.md`: veredito, restrições com folga, origem e fonte, itens A_CONFIRMAR, avisos do STEP, SHA-256 do STEP e
  da configuração, e o rótulo "VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics";
- `resultado.json`: o mesmo em dados (SI), com as curvas de MR e do comprimento do amortecedor;
- busca com candidato: `candidato_NN.csv` + `candidato_NN.meta.json` (um conjunto de hardpoints por candidato, schema V2.0,
  Status PROVISIONAL, sufixo no `geometry_rev`) e `candidatos.csv` (tabela-resumo, um candidato por linha); sem candidato,
  só a Fase I no relatório e no `resultado.json`;
- figuras (`curvas.png`, `mapa_espaco_livre.png`) só se o matplotlib existir.

Referencial do STEP: com as esferas `REF_ORIGEM`, `REF_X` e `REF_Y` no STEP, elas mandam (`cad_step.referencial`); sem
nenhuma esfera `REF_`, vale o item `transformacao_step_m` da configuração (HIPOTESE), e o relatório diz isso; a folga aos
fixos sai então com origem HIPOTESE. Esferas `HP_FL_<chave>` do STEP são comparadas com o CSV de hardpoints (aviso acima
de 0,5 mm, `cad_step.conferir_hp`); a varredura usa o CSV.
Caixa de busca do pivô (decisão R8 do controlador, HIPOTESE): X do item `caixa_busca_pivo_m`; Y e Z nulos no item vêm
do envelope do chassi no STEP (caixa envolvente, no referencial do carro, dos pontos de amostra de TODOS os obstáculos
fixos), lado esquerdo: Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max]. `--caixa` sobrepõe tudo; sem `--step`, a busca exige
`--caixa` (o `--avaliar-v20` não). Sem `--step`, a cena tem só o aro (`varredura.cena_sem_cad`) e a
ferramenta avisa.

Códigos de saída: 0 = saídas gravadas (qualquer veredito); 2 = entrada inválida (arquivo, configuração com item obrigatório
nulo, caixa com mín ≥ máx ou não finita, referencial, primitivo não finito no STEP, OCP ausente com --step). O progresso da busca vai para o stderr, no máximo a cada INTERVALO_PROGRESSO_S segundos.
"""
import argparse
import hashlib
import os
import shlex
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(os.environ["DDS_RAIZ"]) if os.environ.get("DDS_RAIZ") else Path(__file__).resolve().parent.parent   # DDS_RAIZ: executável empacotado
sys.path.insert(0, str(RAIZ / "python"))

import hardpoints as hp  # noqa: E402
from posicionador import busca as bu  # noqa: E402
from posicionador import cad_step as cs  # noqa: E402
from posicionador import config as pc  # noqa: E402
from posicionador import mecanismo as mec  # noqa: E402
from posicionador import relatorio as rl  # noqa: E402
from posicionador import varredura as vr  # noqa: E402
from posicionador.geometria import Caixa, Capsula  # noqa: E402

DADOS = RAIZ / "data" / "posicionador"
INTERVALO_PROGRESSO_S = 5.0
PASSO_AMOSTRA_M = 0.005        # espaçamento dos pontos de amostra (eixo das cápsulas, arestas das caixas) na caixa derivada


class ErroEntrada(Exception):
    """Entrada inválida: a ferramenta sai com código 2."""


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def meta_de(csv_path):
    p = Path(csv_path)
    return p.with_name(p.name[:-4] + ".meta.json") if p.name.endswith(".csv") else p.with_suffix(".meta.json")


def log(msg):
    print(f"[posicionador] {msg}", file=sys.stderr, flush=True)


def _rel(p):
    try:
        return Path(p).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return str(p)


# ------------------------------------------------------------------ cena
def cena_do_step(caminho, cfg):
    """(cena, montagem, texto do referencial, (R, t), esferas). Esferas REF_ mandam; sem nenhuma, a transformação da
    configuração (e a cena marca o referencial como HIPOTESE)."""
    if not cs.OCP_DISPONIVEL:
        raise ErroEntrada("cadquery-ocp ausente: a leitura do STEP precisa do extra opcional (uv sync --extra cad)")
    log(f"lendo o STEP {caminho}")
    montagem = cs.ler_step(str(caminho))
    esf = cs.esferas(montagem)
    if any(k.startswith("REF_") for k in esf):
        try:
            R, t = cs.referencial(esf)
        except cs.ErroReferencial as e:
            raise ErroEntrada(f"esferas REF_ presentes no STEP, mas o referencial é inválido: {e}") from e
        texto = "esferas REF_ORIGEM, REF_X e REF_Y do STEP (cad_step.referencial)"
        ref_hip = None
    else:
        it = cfg.item("transformacao_step_m")
        try:
            R = np.asarray(it.valor["rotacao"], dtype=float).reshape(3, 3)
            t = np.asarray(it.valor["translacao_m"], dtype=float).reshape(3)
        except (TypeError, KeyError, ValueError) as e:
            raise ErroEntrada(f"o STEP não tem esferas REF_ e o item `transformacao_step_m` não dá rotação 3×3 e "
                              f"translação [3] ({it.origem}, valor {it.valor!r}): {e}") from e
        texto = (f"o STEP não tem esferas REF_: usada a transformação da configuração, item `transformacao_step_m` "
                 f"({it.origem}): rotação {R.tolist()}, translação {t.tolist()} m. Fonte: {it.fonte}")
        ref_hip = f"{it.origem}: {it.fonte}"
    log("obstáculos fixos e nós do chassi")
    try:
        cena = vr.cena_do_step(montagem, R, t, cfg, ref_hipotese=ref_hip)
    except ValueError as e:
        raise ErroEntrada(f"cena do STEP recusada: {e}") from e
    return cena, montagem, texto, (R, t), esf


def _segmento(a, b):
    n = max(2, int(np.ceil(np.linalg.norm(b - a) / PASSO_AMOSTRA_M)) + 1)
    s = np.linspace(0.0, 1.0, n)[:, None]
    return a[None, :] + s * (b - a)[None, :]


def pontos_de_amostra(prim):
    """Pontos de amostra de um obstáculo fixo (m): eixo da cápsula ou as 12 arestas da caixa, espaçados ≤ PASSO_AMOSTRA_M."""
    if isinstance(prim, Capsula):
        return _segmento(prim.a, prim.b)
    if isinstance(prim, Caixa):
        sinais = [np.array([i, j, k], dtype=float) for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)]
        cantos = [prim.centro + (s * prim.meias) @ prim.eixos for s in sinais]
        arestas = [(a, b) for ia, a in enumerate(cantos) for ib, b in enumerate(cantos)
                   if ia < ib and int(np.sum(sinais[ia] != sinais[ib])) == 1]
        return np.vstack([_segmento(a, b) for a, b in arestas])
    c = getattr(prim, "c", getattr(prim, "centro", None))
    return np.asarray(c, dtype=float).reshape(1, 3) if c is not None else np.zeros((0, 3))


def caixa_envelope(fixos):
    """(mín[3], máx[3]) [m]: caixa envolvente dos pontos de amostra de todos os obstáculos fixos (referencial do carro)."""
    pts = np.vstack([pontos_de_amostra(p) for p in fixos]) if fixos else np.zeros((0, 3))
    if not len(pts):
        raise ErroEntrada("o STEP não tem obstáculos fixos: use --caixa")
    return pts.min(axis=0), pts.max(axis=0), len(pts)


def validar_caixa(lo, hi, origem):
    """(mín[3], máx[3]) finitos com mín < máx em cada eixo; senão ErroEntrada (código 2) com a origem da caixa."""
    lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
    if lo.shape != (3,) or hi.shape != (3,) or not (np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))):
        raise ErroEntrada(f"caixa de busca do pivô ({origem}) inválida: esperado mín[3] e máx[3] finitos em m, veio "
                          f"{lo.tolist()} a {hi.tolist()}")
    ruins = [("X", "Y", "Z")[i] for i in range(3) if not lo[i] < hi[i]]
    if ruins:
        raise ErroEntrada(f"caixa de busca do pivô ({origem}) com mín ≥ máx em {', '.join(ruins)}: mín {lo.tolist()}, "
                          f"máx {hi.tolist()} (a ordem do --caixa é xmin,ymin,zmin,xmax,ymax,zmax, em m)")
    return lo, hi


def caixa_de_busca(args, cfg, cena):
    """((mín[3], máx[3]), texto da origem, origem) com origem ∈ {"LINHA_DE_COMANDO", item da configuração, "HIPOTESE"}.
    A caixa devolvida sempre tem mín < máx e números finitos (`validar_caixa`)."""
    if args.caixa:
        try:
            v = [float(x) for x in args.caixa.split(",")]
        except ValueError as e:
            raise ErroEntrada(f"--caixa inválida ({args.caixa!r}): {e}") from e
        if len(v) != 6:
            raise ErroEntrada(f"--caixa precisa de 6 números (xmin,ymin,zmin,xmax,ymax,zmax em m); veio {len(v)}")
        return validar_caixa(v[:3], v[3:], "--caixa"), "da linha de comando (--caixa)", "LINHA_DE_COMANDO"
    it = cfg.item("caixa_busca_pivo_m")
    try:
        lo, hi = list(it.valor["min_m"]), list(it.valor["max_m"])
        if len(lo) != 3 or len(hi) != 3:
            raise ValueError("min_m e max_m precisam de 3 valores")
    except (TypeError, KeyError, ValueError) as e:
        raise ErroEntrada(f"item `caixa_busca_pivo_m` ({it.origem}) sem min_m[3] e max_m[3] (valor {it.valor!r}): {e}; "
                          "use --caixa") from e
    faltam = [i for i in range(3) if lo[i] is None or hi[i] is None]
    texto = f"item `caixa_busca_pivo_m` ({it.origem}): {it.fonte}"
    if not faltam:
        return validar_caixa(lo, hi, "caixa_busca_pivo_m"), texto, it.origem
    if args.step is None:
        raise ErroEntrada("sem --step, a busca exige --caixa xmin,ymin,zmin,xmax,ymax,zmax (m): a configuração não tem "
                          "Y nem Z da caixa de busca do pivô")
    if 0 in faltam:
        raise ErroEntrada("o X da caixa de busca do pivô tem de vir da configuração ou de --caixa")
    emin, emax, n = caixa_envelope(cena.fixos)
    deriv = {1: (0.0, float(emax[1])), 2: (max(0.0, float(emin[2])), float(emax[2]))}
    for i in faltam:
        lo[i], hi[i] = deriv[i]
    eixos = ", ".join("XYZ"[i] for i in faltam)
    texto = (f"HIPOTESE: caixa derivada do envelope do chassi (decisão R8). X do item `caixa_busca_pivo_m` ({it.origem}): "
             f"{it.fonte}. {eixos} derivados do STEP: caixa envolvente (referencial do carro) dos {n} pontos de amostra de "
             f"todos os obstáculos fixos (envelope Y [{emin[1]:.4f}; {emax[1]:.4f}] m, Z [{emin[2]:.4f}; {emax[2]:.4f}] m), "
             f"lado esquerdo: Y ∈ [0, y_max], Z ∈ [max(0, z_min), z_max] (pontos no eixo das cápsulas e nas 12 arestas "
             f"das caixas, a cada {PASSO_AMOSTRA_M * 1e3:.0f} mm no máximo; o raio das cápsulas não entra)")
    return validar_caixa(lo, hi, "derivada do envelope do chassi"), texto, "HIPOTESE"


# ------------------------------------------------------------------ figuras
def figuras(pasta, cands, mapa=None):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    out = []
    cands = [(nome, c) for nome, c in cands if c is not None and c.avaliacao.curvas.get("dz_m") is not None]
    if cands:
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
        for nome, c in cands[:5]:
            cv = c.avaliacao.curvas
            dz = np.asarray(cv["dz_m"]) * 1e3
            a1.plot(dz, cv["MR [wheel/spring]"], label=nome)
            a2.plot(dz, np.asarray(cv["Ls_m"]) * 1e3, label=nome)
        a1.set(xlabel="curso da roda dz [mm]", ylabel="MR [wheel/spring]", title="MR no curso")
        a2.set(xlabel="curso da roda dz [mm]", ylabel="comprimento do amortecedor [mm]", title="Amortecedor no curso")
        for a in (a1, a2):
            a.grid(True, alpha=0.3)
            a.legend(fontsize=7)
        fig.suptitle(rl.ROTULO, fontsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(pasta, "curvas.png"), dpi=120)
        plt.close(fig)
        out.append("curvas.png")
    if mapa is not None and mapa.folga_m.size:
        livre = mapa.folga_m >= 0.0
        g = mapa.grade
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
        for ax, (i, j), nome in ((a1, (0, 1), "XY"), (a2, (0, 2), "XZ")):
            eixo = 3 - i - j
            frac = livre.mean(axis=eixo)
            ext = [g[..., i].min() * 1e3, g[..., i].max() * 1e3, g[..., j].min() * 1e3, g[..., j].max() * 1e3]
            im = ax.imshow(frac.T, origin="lower", extent=ext, aspect="auto", vmin=0, vmax=1, cmap="viridis")
            for _, c in cands[:5]:
                if c.variaveis is not None:
                    ax.plot(c.variaveis.pivo_m[i] * 1e3, c.variaveis.pivo_m[j] * 1e3, "r+")
            ax.set(xlabel=f"{'XYZ'[i]} [mm]", ylabel=f"{'XYZ'[j]} [mm]",
                   title=f"fração livre ao longo de {'XYZ'[eixo]} (plano {nome})")
            fig.colorbar(im, ax=ax)
        fig.suptitle("Mapa de espaço livre do pivô (folga ≥ 0 aos fixos; + = pivôs). " + rl.ROTULO, fontsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(pasta, "mapa_espaco_livre.png"), dpi=120)
        plt.close(fig)
        out.append("mapa_espaco_livre.png")
    return out


# ------------------------------------------------------------------ principal
def argumentos(argv):
    ap = argparse.ArgumentParser(description="Posicionador da atuação dianteira (EDR-076).")
    ap.add_argument("--step", help="STEP do CAD (mm); sem ele, a cena tem só o aro")
    ap.add_argument("--hardpoints", default=str(DADOS / "hardpoints_T11_v10.csv"),
                    help="hardpoints de base (v10, sem atuação); o meta é o .meta.json ao lado")
    ap.add_argument("--hardpoints-v20", default=str(DADOS / "hardpoints_T11_v20_script.csv"),
                    help="conjunto avaliado por --avaliar-v20")
    ap.add_argument("--config", default=str(DADOS / "config_T11.json"))
    ap.add_argument("--saida", required=True, help="pasta das saídas (criada se não existir)")
    ap.add_argument("--avaliar-v20", action="store_true", help="avalia a v20 em vez de buscar")
    ap.add_argument("--amostras", type=int, default=2000)
    ap.add_argument("--refinos", type=int, default=20)
    ap.add_argument("--semente", type=int, default=0)
    ap.add_argument("--caixa", help="caixa de busca do pivô xmin,ymin,zmin,xmax,ymax,zmax (m); com xmin negativo, use "
                    "--caixa=xmin,... (o argparse lê \"-0.15,...\" como opção)")
    return ap.parse_args(argv)


def progresso_fn():
    ultimo = [0.0]

    def f(fase, i, n, melhor):
        agora = time.monotonic()
        if i == n or agora - ultimo[0] >= INTERVALO_PROGRESSO_S:
            ultimo[0] = agora
            log(f"{fase}: {i}/{n}; menor violação máxima normalizada até aqui = {melhor:.4g}")
    return f


def principal(argv=None):
    args = argumentos(argv)
    t0 = time.perf_counter()
    for nome, p in (("--config", args.config), ("--hardpoints", args.hardpoints), ("--step", args.step)):
        if p is not None and not os.path.isfile(p):
            raise ErroEntrada(f"{nome}: arquivo {p} não encontrado")
    cfg = pc.carregar(args.config)
    hs_v10 = hp.load_hardpoints(args.hardpoints, meta_de(args.hardpoints))
    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    ctx = {"cfg": cfg, "data": rl.agora(), "modo": "avaliar-v20" if args.avaliar_v20 else "busca",
           "comando": "uv run python -X utf8 tools/posicionar_atuacao.py " + " ".join(shlex.quote(a) for a in
                                                                                       (argv or sys.argv[1:])),
           "config": _rel(args.config), "config_sha256": sha256(args.config), "hardpoints": _rel(args.hardpoints),
           "hardpoints_sha256": sha256(args.hardpoints), "semente": args.semente, "avisos": [], "avisos_step": []}
    if args.step:
        cena, montagem, ref, (R_step, t_step), esf_step = cena_do_step(args.step, cfg)
        ctx.update(step=_rel(args.step), step_sha256=sha256(args.step), referencial=ref,
                   avisos_step=list(montagem.avisos))
    else:
        cena = vr.cena_sem_cad(cfg)
        ctx["avisos"].append("sem --step: cena só com o aro (varredura.cena_sem_cad); a folga ao chassi e às peças fixas "
                             "não foi conferida")
        log(ctx["avisos"][-1])
    ctx["nao_modelado"] = list(cena.nao_modelado)

    dados = {"rotulo": rl.ROTULO, "stale": rl.STALE, "modo": ctx["modo"], "data": ctx["data"], "comando": ctx["comando"],
             "config": ctx["config"], "config_sha256": ctx["config_sha256"], "hardpoints": ctx["hardpoints"],
             "hardpoints_sha256": ctx["hardpoints_sha256"], "step": ctx.get("step"),
             "step_sha256": ctx.get("step_sha256"), "referencial": ctx.get("referencial"),
             "a_confirmar": {n: cfg.item(n).fonte for n in cfg.a_confirmar()}, "avisos_step": ctx["avisos_step"],
             "nao_modelado": ctx["nao_modelado"], "avisos": ctx["avisos"]}

    hs20 = None
    if args.avaliar_v20:
        if not os.path.isfile(args.hardpoints_v20):
            raise ErroEntrada(f"--hardpoints-v20: arquivo {args.hardpoints_v20} não encontrado")
        hs20 = hp.load_hardpoints(args.hardpoints_v20, meta_de(args.hardpoints_v20))
    if args.step:
        av_hp, comp_hp = cs.conferir_hp(esf_step, R_step, t_step, hs20 if hs20 is not None else hs_v10)
        ctx["avisos"].extend(av_hp)
        dados["esferas_hp"] = [{"point_id": k, "distancia_m": d} for k, d in comp_hp]
        for a in av_hp:
            log(a)

    if args.avaliar_v20:
        log("avaliando a v20 (varredura convergida)")
        c = mec.Construcao(hs20, None, None)
        cand = bu.Candidato(None, c, bu.avaliar_convergido(c, cena, cfg), origem="v20")
        cand.violacao = bu.violacao(cand.avaliacao)
        ctx.update(v20=_rel(args.hardpoints_v20), cand_v20=cand)
        dados.update(v20_arquivo=ctx["v20"], v20_sha256=sha256(args.hardpoints_v20),
                     v20=rl.candidato_dict(cand)["avaliacao"] | {"pontos_m": rl.pontos_atuacao(hs20)})
        ctx["figuras"] = figuras(str(pasta), [("v20", cand)])
    else:
        caixa, origem_caixa, rotulo_caixa = caixa_de_busca(args, cfg, cena)
        ctx.update(caixa=caixa, caixa_origem=origem_caixa)
        log(f"busca: {args.amostras} amostras, {args.refinos} refinos, semente {args.semente}; caixa {caixa[0].round(4)}"
            f" a {caixa[1].round(4)} m")
        try:
            res = bu.buscar(hs_v10, cena, cfg, caixa, n_amostras=args.amostras, n_refinos=args.refinos,
                            semente=args.semente, progresso=progresso_fn())
        except ValueError as e:
            if str(e).startswith("caixa_m"):
                raise ErroEntrada(f"caixa de busca do pivô inválida: {e}") from e
            raise
        ctx["resultado"] = res
        resumo, cands_json = [], []
        for k, c in enumerate(res.candidatos, start=1):
            arq = (f"candidato_{k:02d}.csv", f"candidato_{k:02d}.meta.json")
            hs = rl.conjunto_do_candidato(c, k, ctx | {"semente": args.semente})
            hp.write_hardpoints(str(pasta / arq[0]), str(pasta / arq[1]), hs)
            resumo.append(rl.linha_resumo(c, k, arq[0]))
            cands_json.append(rl.candidato_dict(c, k, arq))
        if resumo:
            rl.gravar_resumo(str(pasta / "candidatos.csv"), resumo)
        dados.update(caixa_busca_pivo_m={"min_m": caixa[0], "max_m": caixa[1], "origem": rotulo_caixa,
                                         "fonte": origem_caixa},
                     semente=args.semente, amostras=args.amostras, refinos=args.refinos,
                     estatisticas=res.estatisticas, candidatos=cands_json, fase1=rl.diagnostico_dict(res.fase1),
                     mapa_nao_modelado=None if res.mapa is None else res.mapa.nao_modelado)
        figs = [(f"candidato {k:02d}", c) for k, c in enumerate(res.candidatos, start=1)]
        if not figs and res.fase1 is not None and res.fase1.melhor is not None:
            figs = [("melhor da Fase I", res.fase1.melhor)]
        ctx["figuras"] = figuras(str(pasta), figs, res.mapa)
    dados["figuras"] = ctx.get("figuras", [])
    dados["tempo_s"] = time.perf_counter() - t0
    rl.gravar_json(str(pasta / "resultado.json"), dados)
    with open(pasta / "relatorio.md", "w", encoding="utf-8") as f:
        f.write(rl.markdown(ctx))
    log(f"saídas em {pasta} ({dados['tempo_s']:.1f} s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except (ErroEntrada, pc.ConfigError, hp.HardpointError, cs.ErroSTEP) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(2)
