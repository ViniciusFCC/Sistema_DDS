"""
Portão de identificação dos componentes do CAD (posicionador, fase 2).

Lê o JSON da sondagem do Fusion (etapa `geometria_por_componente`, gerada por `T11_sondagem`), reconhece os componentes
pelo nome e confere o resultado pela geometria. Código de saída: 0 = nenhuma FALHA; 1 = há FALHA (não usar o modelo até
resolver); 2 = arquivo ilegível. Nada é corrigido: decisões de nome vão no mapa JSON (`--mapa`).

Uso:
    uv run python -X utf8 tools/verificar_identificacao.py ARQUIVO_SONDAGEM.json [--mapa MAPA.json] [--saida RELATORIO.md]
    uv run python -X utf8 tools/verificar_identificacao.py --modelo-de-mapa ARQUIVO_SONDAGEM.json   (esqueleto do mapa)
"""
import argparse
import json
import sys

from posicionador import identificacao as idf
from posicionador import reconhecimento as rc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sondagem", help="JSON da sondagem do Fusion")
    ap.add_argument("--mapa", help="JSON {nome do componente: categoria} com decisões do usuário")
    ap.add_argument("--saida", help="grava o relatório Markdown neste arquivo")
    ap.add_argument("--modelo-de-mapa", action="store_true", help="imprime o esqueleto de mapa (sugestões e não reconhecidos)")
    a = ap.parse_args(argv)
    try:
        with open(a.sondagem, encoding="utf-8") as f:
            geo = json.load(f)["geometria_por_componente"]
        mapa = rc.carregar_mapa(a.mapa) if a.mapa else None
    except (OSError, KeyError, ValueError) as e:
        print(f"não consegui ler os dados: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if a.modelo_de_mapa:
        print(json.dumps(rc.modelo_de_mapa(list(rc.reconhecer(n, mapa) for n in geo["topos"])), ensure_ascii=False, indent=2))
        return 0
    res = idf.verificar(geo, mapa)
    texto = idf.relatorio_md(res)
    print(texto)
    if a.saida:
        with open(a.saida, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
