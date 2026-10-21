"""Migra os dados da equipe da V3.0 viva para a V4.0, por nome (incremento 3, fundação; EDR-058).

Uso:
    uv run python -X utf8 tools/migrar_dados_v3_v4.py VIVA_V3.xlsx [--v40 excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx]
        [--saida build/V4_0_com_dados.xlsx] [--relatorio build/migracao-V3-V4.md] [--base V4_0.xlsx]

Passos:
1. recusa (código 2) saída ou relatório em excel/ ou por cima de um arquivo de entrada, antes de abrir qualquer arquivo;
2. compara a viva com a V3.0 da tag v3.0 (extraída para uma pasta temporária): toda célula alterada tem de ter nome de
   dado (`ent`, `org`, `fte`) na tabela `data/nomes_V4_0.csv`; senão, erro (código 2) que lista as células;
3. lê a viva pelos endereços da tabela e injeta os dados numa cópia da V4.0 (`dados_planilha.injetar`). A base dos
   conflitos é, por padrão, a V3.0 da tag lida pelos endereços (igual à V4.0 de referência lida pelos nomes, TC-WB40-004);
   `--base` usa os dados de outra V4.0, lidos pelos nomes;
4. escreve o relatório em Markdown (contagens, conflitos com base, destino e novo, faltas e escritas).
Sai com código 1 se houver conflito ou falta, 0 se não houver. Só lê a viva e a V4.0 de origem; grava só a cópia e o
relatório; nunca recalcula.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))
import dados_planilha as dp  # noqa: E402
from gerar_v4_0 import CSV_NOMES, PASTA_EXCEL, _recusar, extrair_v30  # noqa: E402
from nomes_v4_0 import ler_tabela, verificar_cobertura  # noqa: E402

V40_PADRAO = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_0.xlsx"
SAIDA_PADRAO = RAIZ / "build" / "V4_0_com_dados.xlsx"
RELATORIO_PADRAO = RAIZ / "build" / "migracao-V3-V4.md"


def _recusar_caminhos(a: argparse.Namespace) -> None:
    """Recusas que só comparam caminhos (nenhum arquivo é aberto)."""
    entradas = [a.viva, a.v40] + ([a.base] if a.base else [])
    for e in entradas:
        _recusar(e, a.saida)
    r = a.relatorio.resolve()
    if r.parent == PASTA_EXCEL.resolve() or PASTA_EXCEL.resolve() in r.parents:
        raise SystemExit(f"relatório em excel/ recusado ({a.relatorio})")
    if r in {p.resolve() for p in entradas + [a.saida]}:
        raise SystemExit(f"relatório por cima de uma planilha: recusado ({a.relatorio})")
    if a.relatorio.suffix.lower() != ".md" or a.saida.suffix.lower() != ".xlsx":
        raise SystemExit(f"recusado: o relatório deve ser .md e a saída .xlsx ({a.relatorio}, {a.saida})")


def _md(v) -> str:
    """Valor como texto de célula de tabela Markdown."""
    return "(vazio)" if v is None else repr(v).replace("|", "\\|").replace("\n", " ")


def relatorio(a: argparse.Namespace, rel: dp.RelatorioInjecao, celula: dict[str, str], dados: dict,
              base_txt: str) -> str:
    total = len(rel.escritas) + len(rel.iguais) + len(rel.conflitos) + len(rel.faltando)
    linhas = [
        "# Migração de dados V3.0 → V4.0 (por nome)",
        "",
        f"- Viva (V3.0): `{a.viva}`",
        f"- V4.0 de origem: `{a.v40}`",
        f"- Saída: `{a.saida}`",
        f"- Base dos conflitos: {base_txt}",
        "",
        "| Situação | Nomes |",
        "|---|---|",
        f"| Escritas | {len(rel.escritas)} |",
        f"| Já iguais | {len(rel.iguais)} |",
        f"| Conflitos (não escritos) | {len(rel.conflitos)} |",
        f"| Faltando na V4.0 | {len(rel.faltando)} |",
        f"| Total | {total} |",
        "",
        f"Resultado: **{'FAIL' if rel.conflitos or rel.faltando else 'PASS'}** "
        "(conflito ou falta dão código 1; resolva à mão e rode de novo).",
        "",
        "## Conflitos",
        "",
    ]
    if rel.conflitos:
        linhas += ["| Nome | Célula | Base | Destino (V4.0) | Novo (viva) |", "|---|---|---|---|---|"]
        linhas += [f"| `{n}` | {celula.get(n, '?')} | {_md(b)} | {_md(d)} | {_md(v)} |" for n, b, d, v in rel.conflitos]
    else:
        linhas.append("Nenhum.")
    linhas += ["", "## Faltando na V4.0", ""]
    linhas += [f"- `{n}` ({celula.get(n, '?')})" for n in rel.faltando] or ["Nenhum."]
    linhas += ["", "## Escritas", ""]
    if rel.escritas:
        linhas += ["| Nome | Célula | Novo |", "|---|---|---|"]
        linhas += [f"| `{n}` | {celula.get(n, '?')} | {_md(dados[n])} |" for n in rel.escritas]
    else:
        linhas.append("Nenhuma.")
    return "\n".join(linhas) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Migra os dados da V3.0 viva para uma cópia da V4.0, por nome.")
    p.add_argument("viva", type=Path, help="V3.0 preenchida pela equipe (só leitura)")
    p.add_argument("--v40", type=Path, default=V40_PADRAO, help="V4.0 de origem (só leitura)")
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    p.add_argument("--relatorio", type=Path, default=RELATORIO_PADRAO)
    p.add_argument("--base", type=Path, default=None,
                   help="V4.0 cujos dados (por nome) são a base dos conflitos (padrão: V3.0 da tag, por endereço)")
    p.add_argument("--nomes", type=Path, default=CSV_NOMES, help="tabela de nomes (CSV)")
    a = p.parse_args()
    try:
        _recusar_caminhos(a)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    tabela = ler_tabela(a.nomes)
    celula = {n.nome: f"{n.aba}!{n.celula}" for n in tabela}
    so_dados = [n for n in tabela if n.papel in dp.PAPEIS_DADOS]
    with tempfile.TemporaryDirectory() as tmp:
        v30 = extrair_v30(Path(tmp))
        try:
            verificar_cobertura(so_dados, dp.celulas_alteradas(a.viva, v30))
        except ValueError as e:
            print(f"viva com células alteradas fora dos dados da V4.0: {e}", file=sys.stderr)
            return 2
        if a.base is None:
            base, base_txt = dp.ler_por_endereco(v30, tabela), "V3.0 da tag v3.0 (por endereço)"
        else:
            base, base_txt = dp.ler_por_nome(a.base), f"`{a.base}` (por nome)"
    dados = dp.ler_por_endereco(a.viva, tabela)
    rel = dp.injetar(a.v40, dados, a.saida, base=base)
    a.relatorio.parent.mkdir(parents=True, exist_ok=True)
    with open(a.relatorio, "w", encoding="utf-8", newline="\n") as f:
        f.write(relatorio(a, rel, celula, dados, base_txt))
    print(f"escritas {len(rel.escritas)}, iguais {len(rel.iguais)}, conflitos {len(rel.conflitos)}, "
          f"faltando {len(rel.faltando)} -> {a.saida}; relatório: {a.relatorio}")
    return 1 if rel.conflitos or rel.faltando else 0


if __name__ == "__main__":
    sys.exit(main())
