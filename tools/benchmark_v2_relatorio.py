"""
Relatório do benchmark 2 (lê `resultados_v2.json`, grava `relatorio_v2.md` e `figuras/g1..g3.png`). Precisa de matplotlib.
Uso: <python com matplotlib> tools/benchmark_v2_relatorio.py --saida PASTA
Os números vêm todos do JSON; o resumo em linguagem simples é escrito à mão em `resumo_simples_v2.md` (se existir) e entra no topo.
"""
import argparse
import json
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ORDEM = ["script de atuação", "controle (script sem as restrições do tubo)", "v1", "v2", "v2 sem δ", "v2 sem margem",
         "v2 sem caixa dinâmica"]
NOME = {"script de atuação": "Script de atuação", "controle (script sem as restrições do tubo)": "Controle do script",
        "v1": "Posicionador anterior (v1)", "v2": "Posicionador novo (v2)", "v2 sem δ": "v2 sem δ", "v2 sem margem": "v2 sem margem",
        "v2 sem caixa dinâmica": "v2 sem caixa dinâmica"}
COR = {"script de atuação": "#e87722", "controle (script sem as restrições do tubo)": "#e87722", "v1": "#8aa9c9", "v2": "#1d5fa8"}
APROVADOS = ("VIAVEL", "CONDICIONAL")


def _fmt(v, casas=2, pct=False):
    if v is None:
        return "N/A"
    return f"{100 * v:.{casas}f} %".replace(".", ",") if pct else f"{v:.{casas}f}".replace(".", ",")


def tabela(buscas):
    por = {}
    for b in buscas:
        por.setdefault(b["braco"], []).append(b)
    linhas = []
    for nome in ORDEM:
        rs = por.get(nome)
        if not rs:
            continue
        j = [r["juiz"] for r in rs if r.get("juiz")]
        viol = [x["violacao"] for x in j if x["violacao"] is not None and x["violacao"] != float("inf")]
        ok = sum(x["veredito"] in APROVADOS for x in j)
        j2 = [r.get("juiz2") for r in rs if r.get("juiz2")]
        conc = sum(1 for r in rs if r.get("juiz") and r.get("juiz2") and (r["juiz"]["veredito"] in APROVADOS) == (r["juiz2"]["veredito"] in APROVADOS))
        t = [r["tempo_s"] for r in rs]
        mr = [x["var_mr"] for x in j if x.get("var_mr") is not None]
        linhas.append(dict(nome=nome, n=len(rs), aprovadas=ok, mediana=st.median(viol) if viol else None,
                           menor=min(viol) if viol else None, ate1=sum(v <= 0.01 for v in viol), mr=st.median(mr) if mr else None,
                           concordancia=(conc, len([1 for r in rs if r.get("juiz2")])), tempo=st.median(t) if t else None,
                           viol=viol))
    return linhas


def figuras(linhas, saida):
    (saida / "figuras").mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for i, l in enumerate(linhas):
        ys = [max(v, 1e-6) for v in l["viol"]]
        ax.scatter([i + (k % 7 - 3) * 0.04 for k in range(len(ys))], ys, s=22, color=COR.get(l["nome"], "#6a8f5a"), alpha=.8)
        if ys:
            ax.hlines(st.median(ys), i - .3, i + .3, color="#222", lw=2)
    ax.set_yscale("log"); ax.axhline(0.01, color="#999", ls="--", lw=1); ax.text(len(linhas) - .5, 0.011, "1 % do limite", ha="right", fontsize=8, color="#666")
    ax.set_xticks(range(len(linhas))); ax.set_xticklabels([NOME[l["nome"]].replace(" (", "\n(") for l in linhas], fontsize=7.5)
    ax.set_ylabel("quanto falta para cumprir (violação máxima, escala log; menor é melhor)")
    ax.set_title("G1 · Distância das metas na solução final de cada busca (cada ponto = 1 busca)", fontsize=10)
    fig.tight_layout(); fig.savefig(saida / "figuras" / "g1_violacao.png", dpi=170); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(range(len(linhas)), [100 * l["aprovadas"] / l["n"] for l in linhas], color=[COR.get(l["nome"], "#6a8f5a") for l in linhas])
    for i, l in enumerate(linhas):
        ax.text(i, 100 * l["aprovadas"] / l["n"] + 1.5, f"{l['aprovadas']}/{l['n']}", ha="center", fontsize=8)
    ax.set_xticks(range(len(linhas))); ax.set_xticklabels([NOME[l["nome"]].replace(" (", "\n(") for l in linhas], fontsize=7.5)
    ax.set_ylim(0, 110); ax.set_ylabel("% das buscas com solução sem violação")
    ax.set_title("G2 · Buscas que terminam cumprindo todas as metas (juiz principal)", fontsize=10)
    fig.tight_layout(); fig.savefig(saida / "figuras" / "g2_aprovadas.png", dpi=170); plt.close(fig)


def gerar(saida):
    d = json.loads((saida / "resultados_v2.json").read_text(encoding="utf-8"))
    linhas = tabela(d["buscas"])
    figuras(linhas, saida)
    cab = "| Braço | Buscas | Sem violação | Mediana da violação | Melhor | ≤ 1 % do limite | Variação de MR (mediana) | Juiz 2 concorda | Tempo por busca |\n|---|---|---|---|---|---|---|---|---|\n"
    corpo = "".join(f"| {NOME[l['nome']]} | {l['n']} | {l['aprovadas']} | {_fmt(l['mediana'], 3, True)} | {_fmt(l['menor'], 4, True)} | "
                    f"{l['ate1']} | {_fmt(l['mr'], 2, True)} | {l['concordancia'][0]}/{l['concordancia'][1]} | {_fmt(l['tempo'], 0)} s |\n" for l in linhas)
    resumo = (saida / "resumo_simples_v2.md")
    texto = [f"# Benchmark 2: script de atuação × posicionador anterior × posicionador novo\n",
             resumo.read_text(encoding="utf-8") if resumo.exists() else "",
             "## Resultado medido\n", cab + corpo,
             "\n![G1](figuras/g1_violacao.png)\n\n![G2](figuras/g2_aprovadas.png)\n",
             f"\nGerado em {d['gerado_em']} · {d['maquina']} · Python {d['python']} · tempo total {d['tempo_total_s']:.0f} s.\n",
             "Braços e orçamento (≈ 1500 avaliações rápidas cada): " + json.dumps(d["bracos"], ensure_ascii=False) + "\n"]
    (saida / "relatorio_v2.md").write_text("\n".join(texto), encoding="utf-8")
    return linhas


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", required=True)
    for l in gerar(Path(ap.parse_args().saida)):
        print(l["nome"], l["n"], l["aprovadas"], l["mediana"])
