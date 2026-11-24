"""
Benchmark da script de atuação (t11_atuacao.py, FORA do repositório) × posicionador da atuação (EDR-076).

Princípio: um juiz único para as duas. A solução de cada ferramenta é reavaliada por `varredura.avaliar_convergido` (a
cena sem CAD: só o aro; as restrições compartilhadas) — o mesmo critério para quem busca com o método do script de atuação e para quem
busca com o posicionador. O script de atuação nunca entra no repositório: `--script-atuacao PASTA` aponta para a pasta dele.

Uso (na raiz do repositório):
    uv run python -X utf8 tools/benchmark_posicionador.py rodar --script-atuacao PASTA --saida PASTA_DE_SAIDA
        [--inicios 6] [--processos 4] [--amostras 300] [--refinos 20] [--maxfev 1500] [--robustez 60]
    <python com matplotlib> tools/benchmark_posicionador.py relatorio --saida PASTA_DE_SAIDA

`rodar` grava `resultados.json`; `relatorio` lê o JSON e grava `figuras/*.png` e `relatorio.md`. Os números do relatório
saem do JSON, nunca digitados à mão.

Valores SINTÉTICOS de teste (não são dado do carro nem tolerância da equipe):
- perturbação dos pontos de partida do método do script de atuação: σ = 10 mm no pivô, 2° em azimute, elevação e φB, 3 mm em r1 e r2;
- perturbação da robustez: ±1 mm no pivô, ±0,5° em azimute, elevação e φB, ±0,5 mm em r1 e r2 (uniforme);
- critério "a script de atuação declara cumprido": custo final ≤ 0,1 (a v20 que ele aceitou tem custo 0,073).

Controle (`sem_tubo`): o método do script de atuação com as restrições que o posicionador não tem (tubo ao Front Hoop, folga do tubo ao
gabarito, triângulo da bandeja superior, gabarito projetado) satisfeitas por construção, para que os dois otimizem
aproximadamente as mesmas restrições. Sem esse controle, a comparação favorece o posicionador.
"""
import argparse
import json
import os
import platform
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paralelo  # noqa: E402

DADOS = RAIZ / "data" / "posicionador"
CUSTO_CUMPRIDO = 0.1
SIGMA_INICIO = dict(pivo_mm=10.0, graus=2.0, braco_mm=3.0)
DELTA = dict(pivo_mm=1.0, graus=0.5, braco_mm=0.5)
CAIXA_PADRAO = ([-0.15, 0.0, 0.0601], [0.15, 0.3257, 1.2574])   # caixa derivada do envelope do chassi (HIPOTESE, R8)
N_MR = (11, 25, 51, 101, 201, 401)


# ------------------------------------------------------------------ juiz
def _juiz():
    from posicionador import config as pc, varredura as vr
    import hardpoints as hp
    cfg = pc.carregar(str(DADOS / "config_T11.json"))
    hs = hp.load_hardpoints(str(DADOS / "hardpoints_T11_v10.csv"), str(DADOS / "hardpoints_T11_v10.meta.json"))
    return cfg, hs, vr.cena_sem_cad(cfg)


def _num(v):
    if isinstance(v, (tuple, list, np.ndarray)):
        return [float(a) for a in v]
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _resumo(av):
    from posicionador import busca as bu
    rs = []
    for r in av.restricoes:
        rs.append(dict(nome=r.nome, estado=r.estado, valor=_num(r.valor), limite=_num(r.limite), folga=_num(r.folga),
                       viol=bu.violacao_restricao(r), origem=r.origem))
    mr = av.restricao("variação de MR")
    return dict(veredito=av.veredito, motivo=av.motivo, violacao=bu.violacao(av), restricoes=rs,
                n_violadas=sum(r["estado"] == "VIOLADA" for r in rs),
                var_mr=None if mr is None else _num(mr.valor), resolucoes=list(av.resolucoes))


def julgar_x(x_script, juiz=None):
    """Reavalia uma solução no formato do script de atuação (8 números: mm e °) pelo juiz convergido."""
    from posicionador import busca as bu, mecanismo as mec, varredura as vr
    cfg, hs, cena = juiz or _juiz()
    v = mec.Variaveis.da_semente_do_script(x_script)
    con = mec.construir(hs, v, cfg, r2_m=float(x_script[7]) / 1000.0)
    if con.hardpoints is None:
        return dict(veredito="INVIAVEL", motivo=f"construção: {con.motivo}", violacao=float("inf"), restricoes=[],
                    n_violadas=0, var_mr=None, resolucoes=[])
    return _resumo(bu._com_olhal(vr.avaliar_convergido(con, cena, cfg), con, cfg))


def x_script_de(var, r2_m):
    """mecanismo.Variaveis (SI) + r2 → vetor no formato do script (mm e °)."""
    return [*(np.asarray(var.pivo_m) * 1e3), np.degrees(var.az_rad), np.degrees(var.el_rad), var.r1_m * 1e3,
            np.degrees(var.phi_b_rad), r2_m * 1e3]


# ------------------------------------------------------------------ script de atuação (lido de fora)
_T = {}


def _script(pasta):
    if pasta not in _T:
        sys.path.insert(0, pasta)
        import t11_atuacao as T          # noqa: E402  (módulo do script de atuação, fora do repositório)
        _T[pasta] = (T, T.corner())
    return _T[pasta]


def curva_mr_script(T, c, x, n):
    """Estimador do script (np.gradient sobre n pontos do curso), reaplicado com n pontos."""
    g = T.montar(x, c.P["LO"])
    dzs = np.linspace(-T.DROOP, T.BUMP, n)
    r = T.varrer(c, g, dzs)
    r0 = T.varrer(c, g, [0.0])[0]
    C = r0["B"] + (T.EYE - T.DROOP / T.MR_ALVO) * g["ud"]
    Ls = np.array([np.linalg.norm(q["B"] - C) for q in r])
    mr = -np.gradient(dzs, Ls)
    return dzs / 1e3, mr, float(mr.max() / mr.min() - 1.0)


# ------------------------------------------------------------------ tarefas (em processos separados)
def _job_script(a):
    """Nelder-Mead do script de atuação. `sem_tubo` (controle): o mesmo custo, com satisfeitas as restrições que o posicionador
    NÃO tem (reta ao Front Hoop, folga do tubo ao gabarito, triângulo da bandeja superior e gabarito projetado). O controle
    não copia nem altera o script: só põe, na saída do `avaliar()` dele, valores que cumprem esses termos."""
    from scipy.optimize import minimize
    pasta, rotulo, x0, maxfev, maxiter, *resto = a
    sem_tubo = bool(resto and resto[0])
    T, c = _script(pasta)
    original = T.avaliar

    def avaliar_sem_tubo(x, cc, final=False):
        g = original(x, cc, final)
        if g is not None:
            g["erro_fh"], g["tubo_gab"], g["dentro"], g["gab"] = 0.0, 99.0, 99.0, 99.0
        return g

    opts = dict(maxiter=maxiter, xatol=0.05, fatol=1e-6, adaptive=True)
    if maxfev:
        opts["maxfev"] = maxfev
    if sem_tubo:
        T.avaliar = avaliar_sem_tubo
    try:
        f0 = float(T.custo(x0, c))
        t0 = time.perf_counter()
        res = minimize(T.custo, x0, args=(c,), method="Nelder-Mead", options=opts)
        dt = time.perf_counter() - t0
    finally:
        T.avaliar = original
    g = T.avaliar(res.x, c, final=True)
    var_fina = None if g is None else float(g["MRmax"] / g["MRmin"] - 1.0)
    return dict(ferramenta="script", rotulo=rotulo, sem_tubo=sem_tubo, x=[float(v) for v in res.x], x0=[float(v) for v in x0],
                custo_inicial=f0, custo_final=float(res.fun), nfev=int(res.nfev), tempo_s=dt,
                var_mr_propria_25=var_fina, juiz=julgar_x(res.x))


def _job_nosso(a):
    from posicionador import busca as bu, varredura as vr
    semente, n_am, n_ref, caixa = a
    cfg, hs, cena = _juiz()
    contagem = Counter()
    orig = vr.avaliar

    def contar(*args, **kw):
        n = args[3] if len(args) > 3 else kw.get("n", 25)
        contagem[int(n)] += 1
        return orig(*args, **kw)

    vr.avaliar = contar
    t0 = time.perf_counter()
    try:
        res = bu.buscar(hs, cena, cfg, caixa, n_amostras=n_am, n_refinos=n_ref, semente=semente)
    finally:
        vr.avaliar = orig
    dt = time.perf_counter() - t0
    melhor = res.candidatos[0] if res.candidatos else (res.fase1.melhor if res.fase1 else None)
    if melhor is None:
        return dict(ferramenta="posicionador", rotulo=f"semente {semente}", x=None, tempo_s=dt,
                    nfev_rapidas=int(contagem.get(11, 0)), nfev_total=int(sum(contagem.values())),
                    n_viaveis=len(res.candidatos), juiz=None)
    con = melhor.construcao
    juiz = _resumo(bu._com_olhal(vr.avaliar_convergido(con, cena, cfg), con, cfg))
    return dict(ferramenta="posicionador", rotulo=f"semente {semente}", x=[float(v) for v in x_script_de(melhor.variaveis, con.r2_m)],
                tempo_s=dt, nfev_rapidas=int(contagem.get(11, 0)), nfev_total=int(sum(contagem.values())),
                n_viaveis=len(res.candidatos), estatisticas={k: v for k, v in res.estatisticas.items()
                                                             if isinstance(v, (int, float, str))}, juiz=juiz)


def _despachar(a):
    return _job_script(a[1:]) if a[0] == "script" else _job_nosso(a[1:])


# ------------------------------------------------------------------ experimentos
def exp_v20(pasta, x0):
    """Mesma solução (v20) nas duas ferramentas: o que cada uma vê."""
    T, c = _script(pasta)
    curv = []
    for n in N_MR:
        _, _, vm = curva_mr_script(T, c, x0, n)
        curv.append(dict(n=n, script=vm))
    g11 = T.avaliar(x0, c, final=False)
    g25 = T.avaliar(x0, c, final=True)
    conferencia = dict(script_11=float(g11["MRmax"] / g11["MRmin"] - 1), script_25=float(g25["MRmax"] / g25["MRmin"] - 1))
    assert abs(conferencia["script_11"] - curv[0]["script"]) < 1e-9 and abs(conferencia["script_25"] - curv[1]["script"]) < 1e-9, \
        "o estimador reaplicado não bate com o avaliar() do script"
    from posicionador import mecanismo as mec, varredura as vr
    cfg, hs, cena = _juiz()
    con = mec.construir(hs, mec.Variaveis.da_semente_do_script(x0), cfg, r2_m=float(x0[7]) / 1e3)
    for d in curv:
        av = vr.avaliar(con, cena, cfg, d["n"])
        d["posicionador"] = _num(av.restricao("variação de MR").valor)
    av = vr.avaliar(con, cena, cfg, 401)
    curvas_nossas = dict(dz_m=[float(v) for v in av.curvas["dz_m"]], mr=[float(v) for v in av.curvas["MR [wheel/spring]"]])
    dz11, mr11, _ = curva_mr_script(T, c, x0, 11)
    return dict(variacao_vs_n=curv, conferencia_estimador=conferencia, curvas_posicionador=curvas_nossas,
                script_11=dict(dz_m=[float(v) for v in dz11], mr=[float(v) for v in mr11]),
                custo_script=float(T.custo(x0, c)), juiz=julgar_x(x0))


def exp_robustez(solucoes, n_amostras, semente=20261123):
    """Fração de amostras perturbadas (SINTÉTICO) em que cada restrição sai VIOLADA, por solução."""
    from posicionador import busca as bu, mecanismo as mec, varredura as vr
    cfg, hs, cena = _juiz()
    rng = np.random.default_rng(semente)
    p = rng.uniform(-1, 1, size=(n_amostras, 8))
    esc = np.array([DELTA["pivo_mm"]] * 3 + [DELTA["graus"]] * 2 + [DELTA["braco_mm"], DELTA["graus"], DELTA["braco_mm"]])
    out = {}
    for nome, x in solucoes.items():
        cont, falhas, sem_viol, vmax = Counter(), 0, 0, []
        for d in p * esc:
            xp = np.asarray(x, dtype=float) + d
            con = mec.construir(hs, mec.Variaveis.da_semente_do_script(xp), cfg, r2_m=float(xp[7]) / 1e3)
            if con.hardpoints is None:
                falhas += 1
                continue
            av = vr.avaliar(con, cena, cfg, 11)
            viol = [r.nome for r in av.restricoes if r.estado == "VIOLADA"]
            sem_viol += not viol
            cont.update(viol)
            vmax.append(float(bu.violacao(av)))
        out[nome] = dict(n=n_amostras, falhas_de_construcao=falhas, sem_nenhuma_violada=sem_viol, violacao_max=vmax,
                         violada={k: v / n_amostras for k, v in cont.items()})
    return out


def exp_tempo(pasta, x0):
    T, c = _script(pasta)
    from posicionador import mecanismo as mec, varredura as vr
    cfg, hs, cena = _juiz()
    con = mec.construir(hs, mec.Variaveis.da_semente_do_script(x0), cfg, r2_m=float(x0[7]) / 1e3)

    def med(f, k=5):
        ts = []
        for _ in range(k):
            t = time.perf_counter()
            f()
            ts.append(time.perf_counter() - t)
        return float(np.median(ts))

    return {"script avaliar (11 pontos)": med(lambda: T.avaliar(x0, c, False)),
            "script avaliar (25 pontos)": med(lambda: T.avaliar(x0, c, True)),
            "posicionador avaliar (n = 11)": med(lambda: vr.avaliar(con, cena, cfg, 11)),
            "posicionador avaliar (n = 25)": med(lambda: vr.avaliar(con, cena, cfg, 25)),
            "posicionador avaliar (n = 51)": med(lambda: vr.avaliar(con, cena, cfg, 51), 3),
            "posicionador convergido": med(lambda: vr.avaliar_convergido(con, cena, cfg), 3)}


def rodar(args):
    pasta = str(Path(args.script_script).resolve())
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    origem = json.loads((DADOS / "origem_v20_script.json").read_text(encoding="utf-8"))
    x0 = np.asarray(origem["x_semente"], dtype=float)
    rng = np.random.default_rng(20261123)
    inicios = [("v20 (sem perturbação)", x0)]
    for i in range(1, args.inicios):
        d = np.concatenate([rng.normal(0, SIGMA_INICIO["pivo_mm"], 3), rng.normal(0, SIGMA_INICIO["graus"], 2),
                            [rng.normal(0, SIGMA_INICIO["braco_mm"])], [rng.normal(0, SIGMA_INICIO["graus"])],
                            [rng.normal(0, SIGMA_INICIO["braco_mm"])]])
        inicios.append((f"início {i} (v20 + perturbação SINTÉTICA)", x0 + d))
    tarefas = [("script", pasta, f"{r} · mesmo orçamento", x, args.maxfev, 100000) for r, x in inicios]
    tarefas.append(("script", pasta, "v20 · configuração original do script (maxiter 2000)", x0, None, 2000))
    tarefas += [("script", pasta, f"{r} · sem as restrições do tubo", x, args.maxfev, 100000, True) for r, x in inicios]
    tarefas += [("nosso", s, args.amostras, args.refinos, CAIXA_PADRAO) for s in range(args.inicios)]
    t0 = time.perf_counter()
    resultados = paralelo.mapear(_despachar, tarefas, args.jobs, "benchmark 1", saida / "resultados.jsonl",
                                 descrever=lambda j: j[2] if j[0] == "script" else f"posicionador · semente {j[1]}")
    print(f"busca: {time.perf_counter() - t0:.0f} s", file=sys.stderr)

    v20 = exp_v20(pasta, x0)
    script = [r for r in resultados if r["ferramenta"] == "script"]
    nossos = [r for r in resultados if r["ferramenta"] == "posicionador" and r["juiz"]]
    melhor_m = min(script, key=lambda r: r["juiz"]["violacao"])   # qualquer variante, inclusive o controle
    melhor_n = min(nossos, key=lambda r: r["juiz"]["violacao"])
    rob = exp_robustez({"v20 (script de atuação)": x0, "melhor do método do script de atuação": melhor_m["x"],
                        "melhor do posicionador": melhor_n["x"]}, args.robustez)
    tempo = exp_tempo(pasta, x0)
    dados = dict(gerado_em=time.strftime("%Y-%m-%d %H:%M:%S"), maquina=f"{platform.platform()} · {os.cpu_count()} núcleos",
                 python=sys.version.split()[0], config=dict(inicios=args.inicios, jobs=args.jobs, amostras=args.amostras,
                 refinos=args.refinos, maxfev=args.maxfev, robustez=args.robustez, caixa_m=CAIXA_PADRAO,
                 sigma_inicio=SIGMA_INICIO, delta=DELTA, custo_cumprido=CUSTO_CUMPRIDO, n_mr=list(N_MR)),
                 origem=origem["arquivos"], x_v20=[float(v) for v in x0], v20=v20, buscas=resultados,
                 robustez=rob, tempo_avaliacao_s=tempo, tempo_total_busca_s=time.perf_counter() - t0)
    (saida / "resultados.json").write_text(json.dumps(dados, indent=1, ensure_ascii=False, allow_nan=False,
                                                       default=lambda o: None if o != o else str(o)), encoding="utf-8")
    print(f"gravado: {saida / 'resultados.json'}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rodar")
    r.add_argument("--script-atuacao", required=True)
    r.add_argument("--saida", required=True)
    r.add_argument("--inicios", type=int, default=6)
    r.add_argument("--processos", "--jobs", dest="jobs", type=int, default=4)
    r.add_argument("--amostras", type=int, default=300)
    r.add_argument("--refinos", type=int, default=20)
    r.add_argument("--maxfev", type=int, default=1500)
    r.add_argument("--robustez", type=int, default=60)
    g = sub.add_parser("relatorio")
    g.add_argument("--saida", required=True)
    args = ap.parse_args()
    if args.cmd == "rodar":
        rodar(args)
    else:
        import benchmark_relatorio
        benchmark_relatorio.gerar(Path(args.saida))


if __name__ == "__main__":
    main()
