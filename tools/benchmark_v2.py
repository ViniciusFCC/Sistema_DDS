"""
Benchmark 2: script de atuação × posicionador anterior (v1) × posicionador novo (v2, com δ livre, margem como objetivo e caixa
dinâmica) e as ablações do v2 (EDR-076, conselho 2). Reaproveita o juiz e o controle do `benchmark_posicionador.py`.

Mesmo juiz (varredura convergida, sem CAD: só o aro), mesmo orçamento (≤ 1500 avaliações rápidas por busca), mesmos inícios.
Segundo juiz independente: a mesma solução reavaliada com 401 pontos no curso (o juiz principal converge até 8 × 25); a
concordância entre os dois entra no relatório. Perturbações dos inícios do script e da robustez são SINTÉTICAS (não são dado do carro).

Uso: uv run python -X utf8 tools/benchmark_v2.py --script-atuacao PASTA --saida PASTA_DE_SAIDA [--inicios 20] [--ablacao 10] [--jobs 4]
Relatório: <python com matplotlib> tools/benchmark_v2_relatorio.py --saida PASTA_DE_SAIDA
"""
import argparse
import json
import multiprocessing as mp
import os
import platform
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_posicionador as B  # noqa: E402

# braço: (δ máximo em °, margem como objetivo, caixa dinâmica, amostras, refinos, avaliações por refino). Todos somam ≈ 1500
# avaliações rápidas; o v2 usa menos amostras e refinos mais fundos (a alocação é parte do método novo).
BRACOS = {
    "v1": (0.0, False, False, 300, 20, 60),
    "v2": (25.0, True, True, 100, 4, 350),
    "v2 sem δ": (0.0, True, True, 100, 4, 350),
    "v2 sem margem": (25.0, False, True, 100, 4, 350),
    "v2 sem caixa dinâmica": (25.0, True, False, 100, 4, 350),
}
ABLACOES = ("v2 sem δ", "v2 sem margem", "v2 sem caixa dinâmica")


def juiz2(x):
    """Segundo juiz: a solução (formato do script, 9º número = δ) avaliada com 401 pontos, sem convergência por estados."""
    from posicionador import busca as bu, mecanismo as mec, varredura as vr
    cfg, hs, cena = B._juiz()
    con = mec.construir(hs, mec.Variaveis.da_semente_do_script(x), cfg, r2_m=float(x[7]) / 1000.0)
    if con.hardpoints is None:
        return dict(veredito="INVIAVEL", violacao=float("inf"), var_mr=None)
    av = bu._com_olhal(vr.avaliar(con, cena, cfg, 401), con, cfg)
    r = av.restricao("variação de MR")
    return dict(veredito=av.veredito, violacao=float(bu.violacao(av)),
                var_mr=None if r is None or r.valor is None else float(r.valor),
                n_violadas=sum(q.estado == "VIOLADA" for q in av.restricoes),
                margem=float(bu.margem_normalizada(av)))


def _job(a):
    kind = a[0]
    if kind == "script":
        r = B._job_script(a[1:])
        r["braco"] = "controle (script sem as restrições do tubo)" if r.get("sem_tubo") else "script de atuação"
    else:
        from posicionador import busca as bu, varredura as vr
        _, braco, semente = a
        dmax, marg, dina, n_am, n_ref, aval = BRACOS[braco]
        cfg, hs, cena = B._juiz()
        cont, orig = Counter(), vr.avaliar

        def contar(*args, **kw):
            cont[int(args[3] if len(args) > 3 else kw.get("n", 25))] += 1
            return orig(*args, **kw)

        vr.avaliar = contar
        t0 = time.perf_counter()
        try:
            res = bu.buscar(hs, cena, cfg, B.CAIXA_PADRAO, n_amostras=n_am, n_refinos=n_ref, semente=semente,
                            max_aval_refino=aval, delta_max_rad=np.radians(dmax), otimizar_margem=marg, caixa_dinamica=dina)
        finally:
            vr.avaliar = orig
        dt = time.perf_counter() - t0
        melhor = res.candidatos[0] if res.candidatos else (res.fase1.melhor if res.fase1 else None)
        r = dict(ferramenta="posicionador", braco=braco, rotulo=f"semente {semente}", tempo_s=dt, x=None, juiz=None,
                 nfev_rapidas=int(cont.get(11, 0)), n_viaveis=len(res.candidatos))
        if melhor is not None:
            con = melhor.construcao
            r["x"] = [float(v) for v in B.x_script_de(melhor.variaveis, con.r2_m)] + [float(np.degrees(melhor.variaveis.delta_rad))]
            r["juiz"] = B._resumo(bu._com_olhal(vr.avaliar_convergido(con, cena, cfg), con, cfg))
    if r.get("x") is not None and len(r["x"]) >= 8:
        r["juiz2"] = juiz2(r["x"])
        if r.get("juiz") is None:
            r["juiz"] = B.julgar_x(r["x"])
    return r


def rodar(a):
    pasta = str(Path(a.script_atuacao).resolve())
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    origem = json.loads((B.DADOS / "origem_v20_script.json").read_text(encoding="utf-8"))
    x0 = np.asarray(origem["x_semente"], dtype=float)
    rng = np.random.default_rng(20261123)
    inicios = [("v20 (sem perturbação)", x0)]
    for i in range(1, a.inicios):
        d = np.concatenate([rng.normal(0, B.SIGMA_INICIO["pivo_mm"], 3), rng.normal(0, B.SIGMA_INICIO["graus"], 2),
                            [rng.normal(0, B.SIGMA_INICIO["braco_mm"])], [rng.normal(0, B.SIGMA_INICIO["graus"])],
                            [rng.normal(0, B.SIGMA_INICIO["braco_mm"])]])
        inicios.append((f"início {i} (v20 + perturbação SINTÉTICA)", x0 + d))
    jobs = [("script", pasta, f"{r} · mesmo orçamento", x, a.maxfev, 100000) for r, x in inicios]
    jobs += [("script", pasta, f"{r} · sem as restrições do tubo", x, a.maxfev, 100000, True) for r, x in inicios]
    for braco in BRACOS:
        n = a.ablacao if braco in ABLACOES else a.inicios
        jobs += [("nosso", braco, s) for s in range(n)]
    print(f"{len(jobs)} jobs em {a.jobs} processos", file=sys.stderr)
    t0 = time.perf_counter()
    with mp.get_context("spawn").Pool(a.jobs) as pool:
        res = pool.map(_job, jobs, chunksize=1)
    v20 = B.exp_v20(pasta, x0)
    dados = dict(gerado_em=time.strftime("%Y-%m-%d %H:%M:%S"), maquina=f"{platform.platform()} · {os.cpu_count()} núcleos",
                 python=sys.version.split()[0], bracos={k: dict(zip(("delta_max_graus", "margem", "caixa_dinamica", "amostras",
                 "refinos", "aval_por_refino"), v)) for k, v in BRACOS.items()}, inicios=a.inicios, ablacao=a.ablacao,
                 maxfev=a.maxfev, x_v20=[float(v) for v in x0], v20=v20, buscas=res, tempo_total_s=time.perf_counter() - t0)
    (saida / "resultados_v2.json").write_text(json.dumps(dados, indent=1, ensure_ascii=False, allow_nan=False,
                                                          default=lambda o: None if o != o else str(o)), encoding="utf-8")
    print(f"gravado: {saida / 'resultados_v2.json'} ({time.perf_counter() - t0:.0f} s)", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--script-atuacao", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--inicios", type=int, default=20)
    ap.add_argument("--ablacao", type=int, default=10)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--maxfev", type=int, default=1500)
    rodar(ap.parse_args())
