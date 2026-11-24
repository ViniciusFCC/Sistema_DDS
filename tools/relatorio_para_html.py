"""
Converte o relatório do benchmark (`relatorio.md` + `figuras/*.png`) num HTML único, com os gráficos embutidos (base64), para
repassar como um arquivo só. Precisa do pacote `markdown`.

Uso: python tools/relatorio_para_html.py PASTA_DO_RELATORIO SAIDA.html
"""
import base64
import re
import sys
from pathlib import Path

import markdown

CSS = """body{font:15px/1.55 system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 16px;color:#0b0b0b;background:#fcfcfb}
h1{font-size:1.5rem}h2{font-size:1.2rem;margin-top:2rem;border-bottom:1px solid #e6e5e0;padding-bottom:.2rem}h3{font-size:1.05rem}
img{max-width:100%;height:auto;margin:.6rem 0}table{border-collapse:collapse;font-size:12.5px;display:block;overflow-x:auto}
th,td{border:1px solid #e6e5e0;padding:4px 8px;text-align:left}th{background:#f0efec}code{background:#f0efec;padding:0 3px;border-radius:3px}
pre{background:#f0efec;padding:10px;overflow-x:auto}li{margin:.25rem 0}
@media (prefers-color-scheme:dark){body{background:#1a1a19;color:#f0efec}th,td,h2{border-color:#383835}th,code,pre{background:#2a2a28}}"""


def converter(pasta: Path, saida: Path):
    arq = next(a for a in (pasta / "relatorio_v2.md", pasta / "relatorio.md") if a.exists())
    md = arq.read_text(encoding="utf-8")
    html = markdown.markdown(md, extensions=["tables", "fenced_code"])

    def embutir(m):
        b = base64.b64encode((pasta / m.group(2)).read_bytes()).decode()
        return f'<img alt="{m.group(1)}" src="data:image/png;base64,{b}">'

    html = re.sub(r'<img alt="([^"]*)" src="([^"]+)"\s*/?>', embutir, html)
    saida.write_text(f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" '
                     f'content="width=device-width,initial-scale=1"><title>Benchmark do posicionador</title><style>{CSS}</style>'
                     f'</head><body>{html}</body></html>', encoding="utf-8")


if __name__ == "__main__":
    converter(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"gravado: {sys.argv[2]}")
