"""
Gráficos e relatório do benchmark (lê `resultados.json` de `tools/benchmark_posicionador.py rodar`; precisa de matplotlib).
Paleta: skill dataviz (validada: contraste, separação para daltonismo): laranja = ferramenta do Murilo, azul = posicionador,
cinza = referência (a v20). Texto em tinta neutra, nunca na cor da série. Os números do relatório saem do JSON.
"""
import json
import statistics
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

LARANJA, AZUL, CINZA = "#eb6834", "#2a78d6", "#8a8984"
TINTA, TINTA2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
LIMIAR_PRATICO = 0.01       # 1 % do limite: critério do benchmark ("praticamente cumpre"), não é critério de engenharia
LIMIAR_RESTRICAO = 1e-3     # restrição só conta como violada na tabela de frequência acima de 0,1 % do limite


def _estilo(ax, titulo, xlabel=None, ylabel=None):
    ax.set_facecolor(FUNDO)
    ax.set_title(titulo, fontsize=11, color=TINTA, loc="left", pad=8)
    ax.tick_params(colors=TINTA2, labelsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRADE)
    ax.grid(True, color=GRADE, lw=0.8)
    ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=TINTA2)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=TINTA2)


def _fig(w, h):
    f = plt.figure(figsize=(w, h), dpi=200, facecolor=FUNDO)
    return f


def _salvar(f, caminho):
    f.savefig(caminho, bbox_inches="tight", pad_inches=0.15, facecolor=FUNDO)
    plt.close(f)


def _escala(r):
    lim = r["limite"]
    if isinstance(lim, list):
        lim = max(abs(lim[0]), abs(lim[1]))
    lim = abs(lim) if lim else 0.0
    return lim if lim > 0 else None


def _violada_material(r):
    return r["estado"] == "VIOLADA" and r["viol"] > LIMIAR_RESTRICAO


def f1_mr(d, fig_dir):
    f = _fig(11, 4.3)
    ax1, ax2 = f.subplots(1, 2)
    nos = d["v20"]["curvas_posicionador"]
    m11 = d["v20"]["murilo_11"]
    ax1.plot(np.array(nos["dz_m"]) * 1e3, nos["mr"], color=AZUL, lw=2, label="posicionador: MR local (401 pontos)")
    ax1.plot(np.array(m11["dz_m"]) * 1e3, m11["mr"], color=LARANJA, lw=1.6, marker="o", ms=5,
             label="script do Murilo: diferenças finitas (11 pontos)")
    _estilo(ax1, "MR [wheel/spring] ao longo do curso da v20", "curso da roda [mm]", "MR [wheel/spring]")
    ax1.legend(fontsize=8, frameon=False, loc="upper left", labelcolor=TINTA2)
    vn = d["v20"]["variacao_vs_n"]
    n = [r["n"] for r in vn]
    ax2.plot(n, [100 * r["murilo"] for r in vn], color=LARANJA, lw=1.8, marker="o", ms=5)
    ax2.plot(n, [100 * r["posicionador"] for r in vn], color=AZUL, lw=1.8, marker="o", ms=5)
    ax2.axhline(4.0, color=TINTA2, lw=1, ls="--")
    ax2.set_xscale("log")
    ax2.set_xticks(n)
    ax2.set_xticklabels([str(v) for v in n])
    ax2.text(n[0], 4.0 + 0.12, "limite da equipe: 4 %", fontsize=8, color=TINTA2)
    ax2.text(n[-1], 100 * vn[-1]["murilo"] - 0.35, "Murilo: depende de n", fontsize=8.5, color=TINTA2, ha="right")
    ax2.text(n[-1], 100 * vn[-1]["posicionador"] + 0.15, "posicionador: n = 11 já vê a violação", fontsize=8.5,
             color=TINTA2, ha="right")
    ax2.set_ylim(3.5, 6.8)
    _estilo(ax2, "Variação de MR da v20 × pontos do curso", "pontos do curso (n)", "variação de MR [% = máx/mín − 1]")
    f.tight_layout()
    _salvar(f, fig_dir / "f1_variacao_mr.png")


def f2_margens(d, fig_dir):
    rs = [r for r in d["v20"]["juiz"]["restricoes"] if r["estado"] in ("OK", "VIOLADA") and r["folga"] is not None
          and _escala(r)]
    marg = []
    for r in rs:
        m = r["folga"] / _escala(r)
        marg.append((100 * (-r["viol"] if r["estado"] == "VIOLADA" else m), r["nome"]))
    marg.sort()
    teto = 100.0
    f = _fig(10, 0.34 * len(marg) + 1.5)
    ax = f.subplots()
    y = np.arange(len(marg))
    ax.barh(y, [min(m, teto) for m, _ in marg], color=AZUL, height=0.62)
    ax.axvline(0, color=TINTA, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([n for _, n in marg], fontsize=8.5, color=TINTA)
    for yi, (m, _) in zip(y, marg):
        if m > teto:
            txt, x, ha = f"> {teto:.0f} %", teto + 2, "left"
        else:
            txt = f"{m:+.1f} %" if abs(m) >= 0.1 else f"{m:+.3f} %"
            x, ha = (max(m, 0) + 2, "left")
        ax.text(x, yi, txt, va="center", ha=ha, fontsize=8, color=TINTA2)
    ax.set_xlim(min(-70, min(m for m, _ in marg) - 10), teto + 22)
    _estilo(ax, "v20: margem de cada restrição (juiz convergido); negativa = viola; barras cortadas em 100 %",
            "margem / limite [%]")
    ax.grid(axis="y", visible=False)
    _salvar(f, fig_dir / "f2_margens_v20.png")


def _grupos(d):
    b = d["buscas"]
    return {"Murilo · mesmo orçamento": [r for r in b if r["ferramenta"] == "murilo" and "mesmo orçamento" in r["rotulo"]
                                         and not r.get("sem_tubo")],
            "Murilo · configuração original": [r for r in b if r["ferramenta"] == "murilo" and "original" in r["rotulo"]],
            "Murilo · controle sem as restrições do tubo": [r for r in b if r.get("sem_tubo")],
            "Posicionador": [r for r in b if r["ferramenta"] == "posicionador" and r["juiz"]]}


def f3_violacao(d, fig_dir):
    g = _grupos(d)
    cores = [LARANJA, LARANJA, LARANJA, AZUL]
    f = _fig(9.5, 4.3)
    ax = f.subplots()
    rng = np.random.default_rng(1)
    for i, ((nome, rs), cor) in enumerate(zip(g.items(), cores)):
        v = np.array([100 * r["juiz"]["violacao"] for r in rs])
        if "controle" in nome:       # mesma ferramenta, outro objetivo: marcador vazado (também legível sem cor)
            ax.scatter(v, i + rng.uniform(-0.12, 0.12, len(v)), s=46, facecolors=FUNDO, edgecolors=cor, linewidth=1.8, zorder=3)
        else:
            ax.scatter(v, i + rng.uniform(-0.12, 0.12, len(v)), s=46, color=cor, edgecolor=FUNDO, linewidth=1.2, zorder=3)
        if len(v):
            med = float(np.median(v))
            ax.plot([med, med], [i - 0.28, i + 0.28], color=TINTA, lw=1.4, zorder=4)
            ax.text(max(v.max(), med) * 1.25 + 0.5, i, f"mediana {med:.1f} %", ha="left", va="center", fontsize=8.5, color=TINTA2)
    ax.set_yticks(range(len(g)))
    ax.set_yticklabels([f"{n} (n = {len(r)})" for n, r in g.items()], fontsize=8.5, color=TINTA)
    ax.invert_yaxis()
    ax.axvline(0, color=TINTA2, lw=1, ls="--")
    ax.axvline(100 * LIMIAR_PRATICO, color=GRADE, lw=1)
    ax.set_xscale("symlog", linthresh=1.0)
    ax.set_xlim(-0.3, 700)
    ax.set_xticks([0, 1, 10, 100])
    ax.set_xticklabels(["0\n(cumpre)", "1", "10", "100"])
    ax.set_ylim(len(g) - 0.4, -0.7)
    _estilo(ax, "Pior violação da solução final de cada busca, vista pelo mesmo juiz (convergido)",
            "violação máxima normalizada pelo limite [%] (escala symlog)")
    ax.grid(axis="y", visible=False)
    f.tight_layout()
    _salvar(f, fig_dir / "f3_busca_violacao_final.png")


def f4_declarado(d, fig_dir):
    rs = [r for r in d["buscas"] if r["ferramenta"] == "murilo" and not r.get("sem_tubo")]
    f = _fig(7.2, 4.2)
    ax = f.subplots()
    x = [r["custo_final"] for r in rs]
    y = [100 * r["juiz"]["violacao"] for r in rs]
    ax.scatter(x, y, s=52, color=LARANJA, edgecolor=FUNDO, linewidth=1.2, zorder=3)
    ax.axvspan(1e-9, 0.1, color=GRADE, alpha=0.55, lw=0)
    xmin = min(1e-4, min(x) / 3)
    ymax = max(y) * 1.2 + 5
    ax.text(xmin * 1.5, ymax * 0.97, "custo ≤ 0,1: a ferramenta\ndeclara 'tudo cumprido'", fontsize=8.5, color=TINTA2, va="top")
    ax.axhline(0, color=TINTA2, lw=1, ls="--")
    ax.set_xscale("log")
    ax.set_xlim(xmin, max(100, max(x) * 3))
    ax.set_ylim(-0.05 * ymax, ymax)
    _estilo(ax, "Custo declarado pelo script do Murilo × violação medida pelo juiz", "custo final do script (escala log)",
            "violação máxima medida pelo juiz [%]")
    f.tight_layout()
    _salvar(f, fig_dir / "f4_custo_declarado_vs_juiz.png")


def _freq(rs):
    out, n = {}, len(rs)
    for r in rs:
        for q in r["juiz"]["restricoes"]:
            if _violada_material(q):
                out[q["nome"]] = out.get(q["nome"], 0) + 1
    return {k: v / n for k, v in out.items()}, n


def f5_restricoes(d, fig_dir):
    g = _grupos(d)
    fm, nm = _freq(g["Murilo · mesmo orçamento"] + g["Murilo · configuração original"])
    fc, nc = _freq(g["Murilo · controle sem as restrições do tubo"])
    fn, nn = _freq(g["Posicionador"])
    nomes = sorted(set(fm) | set(fc) | set(fn), key=lambda k: -(fm.get(k, 0) + fc.get(k, 0) + fn.get(k, 0)))
    f = _fig(9.5, 0.75 * max(len(nomes), 2) + 1.8)
    ax = f.subplots()
    y = np.arange(len(nomes))
    ax.barh(y - 0.26, [100 * fm.get(k, 0) for k in nomes], height=0.24, color=LARANJA, label=f"Murilo, custo completo (n = {nm})")
    ax.barh(y, [100 * fc.get(k, 0) for k in nomes], height=0.24, color=LARANJA, hatch="////", edgecolor=FUNDO, linewidth=0,
            label=f"Murilo, controle sem as restrições do tubo (n = {nc})")
    ax.barh(y + 0.26, [100 * fn.get(k, 0) for k in nomes], height=0.24, color=AZUL, label=f"posicionador (n = {nn})")
    for yi, k in zip(y, nomes):
        for dy, v in ((-0.26, fm.get(k, 0)), (0.0, fc.get(k, 0)), (0.26, fn.get(k, 0))):
            if v > 0:
                ax.text(100 * v + 1.2, yi + dy, f"{100 * v:.0f} %", va="center", fontsize=8, color=TINTA2)
    ax.set_yticks(y)
    ax.set_yticklabels(nomes, fontsize=8.5, color=TINTA)
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.legend(fontsize=8.5, frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.14), ncol=1, labelcolor=TINTA2)
    _estilo(ax, "Restrições violadas (> 0,1 % do limite) na solução final, % das buscas", "% das buscas")
    ax.grid(axis="y", visible=False)
    _salvar(f, fig_dir / "f5_restricoes_violadas.png")


def f6_robustez(d, fig_dir):
    rob = d["robustez"]
    series = [("v20 (Murilo)", CINZA), ("melhor do método do Murilo", LARANJA), ("melhor do posicionador", AZUL)]
    f = _fig(9.5, 3.6)
    ax = f.subplots()
    rng = np.random.default_rng(2)
    for i, (nome, cor) in enumerate(series):
        v = np.array([100 * x for x in rob[nome]["violacao_max"] if np.isfinite(x)])
        ax.scatter(v, i + rng.uniform(-0.15, 0.15, len(v)), s=18, color=cor, alpha=0.75, edgecolor="none", zorder=3)
        if len(v):
            med = float(np.median(v))
            ax.plot([med, med], [i - 0.3, i + 0.3], color=TINTA, lw=1.4, zorder=4)
            ax.text(max(v.max(), med) * 1.25 + 0.5, i, f"mediana {med:.1f} % · {rob[nome]['sem_nenhuma_violada']} de {rob[nome]['n']} sem violação",
                    ha="left", va="center", fontsize=8.5, color=TINTA2)
    ax.set_yticks(range(len(series)))
    ax.set_yticklabels([n for n, _ in series], fontsize=8.5, color=TINTA)
    ax.axvline(0, color=TINTA2, lw=1, ls="--")
    ax.set_xscale("symlog", linthresh=1.0)
    ax.set_xlim(-0.3, 3000)
    ax.set_xticks([0, 1, 10, 100])
    ax.set_xticklabels(["0\n(cumpre)", "1", "10", "100"])
    ax.set_ylim(len(series) - 0.5, -0.6)
    _estilo(ax, "Violação máxima de cada amostra perturbada (perturbação SINTÉTICA)",
            "violação máxima normalizada pelo limite [%] (escala symlog)")
    ax.grid(axis="y", visible=False)
    _salvar(f, fig_dir / "f6_robustez.png")


# ------------------------------------------------------------------ tabelas
COBERTURA = [
    ("MR alvo (1,40 ± 0,01)", "sim; diferenças finitas sobre 11 pontos", "sim; MR local (`motion_ratio`)"),
    ("Variação de MR ≤ 4 %", "sim; avaliada em 11 pontos (vê 4,00 %)", "sim; convergida (n e 2n, até 200 pontos)"),
    ("Comprimento e curso do amortecedor", "sim; penalidade quadrática com tolerância", "sim; desigualdade (+ margem de curso, a confirmar)"),
    ("Braços do rocker, giro, ângulo do amortecedor a X", "sim; penalidade", "sim; desigualdade"),
    ("Folga ao aro", "sim, mas no segmento errado (`PO = UO`)", "sim; segmento real, aro movido com a manga"),
    ("Folga às pernas das bandejas", "só as 2 da superior; 21 pontos por segmento", "as 4; distância exata"),
    ("Push rod × amortecedor", "sim", "sim"),
    ("Tirante de direção", "não", "sim (raio do tirante a confirmar: eixo)"),
    ("Esterçamento (curso × esterço)", "não: só rodas retas", "sim, se o curso da cremalheira for informado"),
    ("Obstáculos do chassi (STEP)", "não: uma reta ao Front Hoop, sem tubos", "sim: folga ≥ 0 a todo obstáculo fixo"),
    ("Gabarito T.1.2", "parcial: projeção YZ, Z fixo em 550 mm", "altura livre (T.1.2.2c); NAO_VERIFICAVEL sem coluna e pedal"),
    ("Zona da AIP (F.8.6.1)", "não", "sim; NAO_VERIFICAVEL sem a posição da face"),
    ("Manga, freio e pinça", "não", "declarado NAO_VERIFICAVEL"),
    ("Fixação em tubo ou nó", "impõe um tubo ao Front Hoop (≤ 8 mm)", "só preferência por nó; não impõe tubo"),
    ("Push rod dentro do triângulo da bandeja superior", "sim", "não (não migrado)"),
    ("Resolução do curso conferida", "não", "sim"),
    ("Procedência de cada limite", "não", "sim (origem e fonte; A_CONFIRMAR liga CONDICIONAL)"),
]


def _v(x, fmt=".4g"):
    """Número com vírgula decimal (texto em português)."""
    return format(x, fmt).replace(".", ",")


def _pct(v, casas=1):
    if v is None:
        return "—"
    if v and abs(v) < 1e-4:
        casas = max(casas, 4)
    elif v and abs(v) < 1e-2:
        casas = max(casas, 3)
    return _v(100 * v, f".{casas}f") + " %"


def _lim(x):
    if isinstance(x, list):
        return "[" + "; ".join(_v(a) for a in x) + "]"
    return "—" if x is None else _v(x)


def _linha_busca(r):
    j = r["juiz"]
    nf = r.get("nfev") if r["ferramenta"] == "murilo" else r.get("nfev_rapidas")
    if j is None:
        return f"| {r['ferramenta']} | {r['rotulo']} | {nf} | {r['tempo_s']:.0f} | — | sem resultado | — | — | — |"
    prop = _v(r["custo_final"], ".4f") if r["ferramenta"] == "murilo" else "—"
    mat = [q["nome"] for q in j["restricoes"] if _violada_material(q)]
    return (f"| {'Murilo' if r['ferramenta'] == 'murilo' else 'posicionador'} | {r['rotulo']} | {nf} | {r['tempo_s']:.0f} | {prop} "
            f"| {j['veredito']} | {_pct(j['violacao'])} | {_pct(j['var_mr'], 2)} | {len(mat)} |")


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, cwd=Path(__file__).resolve().parent.parent).stdout.strip()
    except OSError:
        return "?"


def gerar(pasta: Path):
    d = json.loads((pasta / "resultados.json").read_text(encoding="utf-8"))
    figs = pasta / "figuras"
    figs.mkdir(exist_ok=True)
    for f in (f1_mr, f2_margens, f3_violacao, f4_declarado, f5_restricoes, f6_robustez):
        f(d, figs)
    g = _grupos(d)
    murilo = g["Murilo · mesmo orçamento"] + g["Murilo · configuração original"]   # custo completo do script
    ctrl = g["Murilo · controle sem as restrições do tubo"]
    nosso = g["Posicionador"]

    def viol(rs):
        return [r["juiz"]["violacao"] for r in rs]

    def prat(rs):
        return sum(v <= LIMIAR_PRATICO for v in viol(rs))

    declaradas = [r for r in murilo if r["custo_final"] <= d["config"]["custo_cumprido"]]
    falsas = [r for r in declaradas if r["juiz"]["veredito"] == "INVIAVEL"]
    vn = d["v20"]["variacao_vs_n"]
    t = d["tempo_avaliacao_s"]
    c = d["config"]
    L = []
    L.append("# Benchmark: ferramenta do Murilo × posicionador da atuação (EDR-076)\n")
    L.append(f"Gerado em {d['gerado_em']} · {d['maquina']} · Python {d['python']} · código do posicionador no commit `{_git('log', '-1', '--format=%h', '--', 'python/posicionador')}` "
             f"· script do Murilo: `t11_atuacao.py` sha256 `{d['origem']['t11_atuacao.py'][:16]}…` (fora do repositório). "
             "Validation = NOT_VALIDATED: o juiz e as duas ferramentas usam cinemática ainda não comparada com o OptimumKinematics "
             "(REFERENCE, EDR-004); o que segue mede **consistência e cobertura**, não correção física. "
             "(Unidades da tabela da v20 em SI: m, rad.)\n")
    L.append("## Resumo\n")
    L.append(f"- **Mesma v20, dois olhares.** O script do Murilo mede a variação de MR da v20 em {_pct(vn[0]['murilo'], 2)} "
             f"(11 pontos, a resolução em que otimiza) e {_pct(vn[1]['murilo'], 2)} (25 pontos); com {vn[-1]['n']} pontos o mesmo "
             f"estimador chega a {_pct(vn[-1]['murilo'], 2)}. O posicionador mede {_pct(vn[0]['posicionador'], 2)} já com 11 "
             f"pontos. O limite da equipe é 4 %. Custo que o script dá à v20: {_v(d['v20']['custo_murilo'], '.3f')}.")
    L.append(f"- **Busca, mesmo juiz.** Com {c['inicios']} partidas por ferramenta e orçamento igual de avaliações do mecanismo "
             f"(~{c['maxfev']}), a violação mediana da solução final é "
             f"{_pct(statistics.median(viol(g['Murilo · mesmo orçamento'])))} no método do Murilo, "
             f"{_pct(statistics.median(viol(ctrl)))} no mesmo método sem as restrições que o posicionador não tem (controle) e "
             f"{_pct(statistics.median(viol(nosso)))} no posicionador. "
             f"Soluções praticamente cumpridas pelo juiz (violação ≤ {_pct(LIMIAR_PRATICO, 0)} do limite): "
             f"{prat(g['Murilo · mesmo orçamento'])} de {len(g['Murilo · mesmo orçamento'])} (Murilo), {prat(ctrl)} de {len(ctrl)} "
             f"(controle) e {prat(nosso)} de {len(nosso)} (posicionador). "
             f"Soluções que o juiz aprova (VIAVEL ou CONDICIONAL): "
             f"{sum(r['juiz']['veredito'] != 'INVIAVEL' for r in murilo + ctrl)} das {len(murilo) + len(ctrl)} do Murilo e "
             f"{sum(r['juiz']['veredito'] != 'INVIAVEL' for r in nosso)} das {len(nosso)} do posicionador.")
    L.append(f"- **Cumprido segundo quem?** {len(declaradas)} das {len(murilo)} buscas do script terminaram com custo ≤ "
             f"{_v(c['custo_cumprido'])} (que ele lê como 'tudo cumprido'); o juiz reprova {len(falsas)} delas. O posicionador só "
             "devolve candidato depois da avaliação convergida, e quando não há candidato devolve o diagnóstico.")
    L.append(f"- **Custo.** Uma avaliação: {_v(t['murilo avaliar (11 pontos)'], '.3f')} s (Murilo, 11 pontos) contra "
             f"{_v(t['posicionador avaliar (n = 11)'], '.3f')} s (posicionador, n = 11), com mais verificações por avaliação (tabela abaixo).\n")
    L.append("## Método\n")
    L.append("- **Juiz único.** Toda solução, de qualquer ferramenta, é reavaliada por `varredura.avaliar_convergido` na cena sem CAD "
             "(só o aro), com `mecanismo.construir` e o r2 da própria solução (o juiz não o recalcula) e o olhal posto pela regra "
             "do posicionador (|B(−23 mm) − C| = 210 mm). Violação = máx. de max(0, −folga)/|limite| (limite nulo: 1 mm).")
    L.append(f"- **Orçamento igual.** Método do Murilo: Nelder-Mead do próprio script (mesmos `xatol`, `fatol`, `adaptive`) com "
             f"`maxfev` = {c['maxfev']}; posicionador: {c['amostras']} amostras, {c['refinos']} refinos de até 60 avaliações "
             f"(≤ {c['amostras'] + 60 * c['refinos']} avaliações rápidas, n = 11). Mais uma busca do Murilo com a configuração "
             "original dele (`maxiter` 2000), sem limite de avaliações.")
    L.append("- **Controle.** O script do Murilo também otimiza restrições que o posicionador removeu de propósito (a reta do tubo "
             "ao Front Hoop, a folga do tubo ao gabarito, o triângulo da bandeja superior e o gabarito projetado em Z fixo), e o juiz "
             "não as mede. Para não favorecer o posicionador, cada partida do Murilo roda também com esses termos satisfeitos por "
             "construção (`sem_tubo`), sem alterar o script dele. O custo próprio dessas buscas exclui os termos do tubo.")
    L.append(f"- **Partidas.** A primeira do Murilo é a v20; as demais são a v20 mais uma perturbação **SINTÉTICA** (σ = "
             f"{c['sigma_inicio']['pivo_mm']:.0f} mm no pivô, {c['sigma_inicio']['graus']:.0f}° nos ângulos, "
             f"{c['sigma_inicio']['braco_mm']:.0f} mm nos braços). O posicionador usa as sementes 0 a {c['inicios'] - 1} na caixa "
             f"derivada do envelope do chassi (HIPOTESE, R8): X ±150 mm, Y 0 a 326 mm, Z 60 a 1257 mm.")
    L.append("- Amostras pequenas: nenhuma estatística inferencial; as tabelas listam cada busca. As buscas rodaram em "
             f"{c['jobs']} processos em paralelo, então os tempos incluem contenção de núcleos.\n")
    L.append("## 1. A mesma v20, dois olhares\n")
    L.append("![variação de MR](figuras/f1_variacao_mr.png)\n")
    L.append("O estimador do script (`np.gradient` sobre os pontos do curso) suaviza a curva: com poucos pontos ele subestima a "
             "variação, e é nessa resolução (11 pontos) que o otimizador decide. A conferência da reimplementação contra o "
             f"`avaliar()` do script bate (4,0035 % e 5,189 %, diferença < 1e-9).\n")
    L.append("![margens da v20](figuras/f2_margens_v20.png)\n")
    L.append("| restrição (v20, juiz convergido) | estado | valor | limite | violação |")
    L.append("|---|---|---|---|---|")
    for q in d["v20"]["juiz"]["restricoes"]:
        if q["estado"] == "NAO_VERIFICAVEL":
            continue
        val = "—" if q["valor"] is None else (_lim(q["valor"]) if isinstance(q["valor"], list) else _v(q["valor"], ".5g"))
        L.append(f"| {q['nome']} | {q['estado']} | {val} | {_lim(q['limite'])} | "
                 f"{_pct(q['viol'], 2) if q['estado'] == 'VIOLADA' else '—'} |")
    L.append("\n## 2. Busca lado a lado, mesmo juiz\n")
    L.append("![violação final](figuras/f3_busca_violacao_final.png)\n")
    L.append("| ferramenta | busca | avaliações | tempo [s] | custo próprio | veredito do juiz | violação máx. | variação de MR | restrições violadas (> 0,1 %) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in d["buscas"]:
        L.append(_linha_busca(r))
    L.append("\n![custo declarado × juiz](figuras/f4_custo_declarado_vs_juiz.png)\n")
    L.append("![restrições violadas](figuras/f5_restricoes_violadas.png)\n")
    L.append("## 3. Robustez a perturbação dos pontos (SINTÉTICA)\n")
    L.append("As soluções são a v20 e a melhor solução final de cada método (menor violação pelo juiz, seção 2; o veredito nominal "
             "de cada uma está na tabela dela). O gráfico mostra a distribuição da pior violação sob perturbação: uma solução que já "
             "viola na posição nominal só é robusta no sentido de projeto se a distribuição ficar em 0.\n")
    L.append(f"Perturbação uniforme de ±{c['delta']['pivo_mm']:.0f} mm no pivô, ±{_v(c['delta']['graus'])}° nos ângulos e "
             f"±{c['delta']['braco_mm']} mm nos braços, {d['robustez']['v20 (Murilo)']['n']} amostras por solução, avaliação n = 11. "
             "Os valores **não são a tolerância de fabricação da equipe** (a medir).\n")
    L.append("![robustez](figuras/f6_robustez.png)\n")
    L.append("## 4. Custo de uma avaliação\n")
    L.append("| avaliação | tempo mediano [s] |")
    L.append("|---|---|")
    for k, v in t.items():
        L.append(f"| {k} | {_v(v, '.3f')} |")
    L.append("\nAs avaliações não fazem o mesmo trabalho: a do posicionador confere mais restrições (tirante, 4 pernas por distância "
             "exata, convergência) e a do script confere o tubo ao Front Hoop e o triângulo da bandeja superior.\n")
    L.append("## 5. O que cada ferramenta verifica\n")
    L.append("Conferido contra o código das duas em 2026-11-23 (script do Murilo: `custo()` e `avaliar()`).\n")
    L.append("| verificação | script do Murilo | posicionador |")
    L.append("|---|---|---|")
    for a, b, cc in COBERTURA:
        L.append(f"| {a} | {b} | {cc} |")
    leitura = pasta / "leitura.md"
    L.append("\n" + (leitura.read_text(encoding="utf-8") if leitura.exists() else "## Leitura\n\n(a escrever)\n"))
    (pasta / "relatorio.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("gravado:", pasta / "relatorio.md")
