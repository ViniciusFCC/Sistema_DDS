"""Leva os dados da planilha viva (Drive) para uma cópia da versão nova, por nome (EDR-063; troca a cada versão).

Uso:
    uv run python -X utf8 tools/migrar_viva.py VIVA --para REF_NOVA.xlsx [--saida build/<nome>_com_dados.xlsx]
                                               [--relatorio build/migracao-viva.md]

Diretriz do usuário (2026-10-23): a cada versão que terminarmos, o arquivo do Drive passa a ser o da versão mais recente e
os dados preenchidos se mantêm. Esta ferramenta prepara a cópia; a troca no Drive é um passo à parte, feito pelo usuário.

Passos:
1. recusa (código 2) saída ou relatório em excel/, no Drive, ou por cima de um arquivo de entrada, antes de abrir qualquer arquivo;
2. copia a viva para uma pasta temporária (o original só é lido); 0 byte, ausente ou bloqueada = código 3;
3. lê a versão da viva (00_README A3) e a referência dela (tag Git; `viva.arquivo_de_referencia`). Toda célula em que a viva difere
   dessa referência tem de ter nome de dado (`ent_`, `org_`, `fte_`); senão, código 2 com a lista. Comentário, hiperlink,
   imagem ou gráfico diferentes da referência também dão código 2 (não migráveis);
4. dado da equipe = valor da viva diferente da referência da versão dela, depois de mapear os rótulos de Origem entre versões
   (`viva.MAPAS_ROTULO`; V4.1 -> V4.2: `origens.MAPA_DADO_V41_V42`, EDR-062 decisão 1). O mapa vale para a viva e para a base
   antes da comparação: um `● Dado do TX` que a equipe manteve, ou trocou por `◐ Dado do T09`, vira `◐ Dado de outro carro`
   nos dois lados e não conta como dado da equipe;
5. injeta o dado da equipe na cópia da versão nova (`dados_planilha.injetar`), com a base = a referência antiga mapeada. Se a
   versão nova também mudou a célula em relação à base, é conflito: listado, nunca sobrescrito.
O relatório (Markdown) lista contagens, conflitos (nome, base, destino, novo), faltas e escritas.

Código de saída: 0 migrado; 1 conflito ou nome sem célula na versão nova; 2 célula alterada fora dos nomes de dado, objeto não
migrável, dado com fórmula, abas diferentes ou caminho recusado; 3 viva não lida. Nunca grava no Drive; nunca recalcula.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))
import dados_planilha as dp  # noqa: E402
import viva as v  # noqa: E402

PASTA_EXCEL = RAIZ / "excel"
RELATORIO_PADRAO = RAIZ / "build" / "migracao-viva.md"


def _recusar(viva: Path, para: Path, saida: Path, relatorio: Path, extras: list[Path]) -> str | None:
    """Mensagem da recusa (só compara caminhos; nenhum arquivo é aberto), ou None."""
    entradas = [viva, para, *extras]
    if (m := v.recusa_de_saida(saida, entradas)):
        return m
    if (m := v.recusa_de_saida(relatorio, entradas + [saida], "relatório")):
        return m
    if relatorio.suffix.lower() != ".md" or saida.suffix.lower() != ".xlsx":
        return f"recusado: o relatório deve ser .md e a saída .xlsx ({relatorio}, {saida})"
    return None


def _md(x) -> str:
    return "(vazio)" if x is None else repr(x).replace("|", "\\|").replace("\n", " ")


def _escrever(caminho: Path, linhas: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(linhas) + "\n")


def _falhar(relatorio: Path, codigo: int, cab: list[str], msg: str) -> int:
    """Erro (código 2 ou 3): escreve o relatório com o erro por cima de qualquer relatório antigo, para que nenhum pareça o
    resultado desta execução. A saída .xlsx não é gravada."""
    print(msg, file=sys.stderr)
    _escrever(relatorio, ["# Migração da viva para a versão nova (por nome)", "", *cab, "",
                          f"Resultado: **ERRO** (código {codigo}). Nada foi migrado.", "", "## Erro", "", msg.replace("\n", " ")])
    return codigo


def _mapear(dados: dict, mapa: dict[str, str]) -> dict:
    """Aplica o mapa de rótulos de Origem aos valores `org_` (os outros dados ficam como estão)."""
    return {k: (mapa.get(x, x) if k.startswith("org_") and isinstance(x, str) else x) for k, x in dados.items()}


def migrar(viva: Path, para: Path, saida: Path, relatorio: Path, pasta: Path, referencia_antiga: Path | None = None) -> int:
    """Executa os passos do módulo; devolve o código de saída. `pasta` é a pasta temporária das cópias. `referencia_antiga`
    substitui a referência da tag (para teste)."""
    viva, para, saida, relatorio, pasta = Path(viva), Path(para), Path(saida), Path(relatorio), Path(pasta)
    extras = [Path(referencia_antiga)] if referencia_antiga else []
    recusa = _recusar(viva, para, saida, relatorio, extras)
    if recusa:
        print(recusa, file=sys.stderr)
        return 2
    cab = [f"- Viva: `{viva}`", f"- Versão nova (destino): `{para}`", f"- Saída: `{saida}` (não gravada nesta execução)"]
    try:
        copia = v.copia_local(viva, pasta)
        ver = v.versao(copia)
        ver_nova = v.versao(para)
    except v.VivaIlegivel as e:
        return _falhar(relatorio, 3, cab, f"viva não lida: {e}")
    num = lambda s: tuple(int(x) for x in v.RE_VERSAO_NUM.fullmatch(s).groups())
    if num(ver) > num(ver_nova):
        return _falhar(relatorio, 2, cab, f"a viva é da versão {ver}, mais nova que o destino ({ver_nova}): migrar para trás "
                                          "perderia dados; use como destino a versão da viva ou uma mais nova")
    try:
        ref_antiga = Path(referencia_antiga) if referencia_antiga else v.arquivo_de_referencia(ver, pasta)
    except v.VivaIlegivel as e:
        return _falhar(relatorio, 3, cab, f"viva não lida: {e}")
    cab = [f"- Viva: `{viva}` (versão {ver}, SHA-256 da cópia `{v.sha256(copia)}`)", f"- Referência da versão da viva: `{ref_antiga}`",
           f"- Versão nova (destino): `{para}` (versão {ver_nova})", f"- Saída: `{saida}`"]
    mapa = v.MAPAS_ROTULO.get((ver, ver_nova), {})
    try:
        try:
            alteradas = dp.celulas_alteradas(copia, ref_antiga)
        except dp.AbasDiferentes as e:
            return _falhar(relatorio, 2, cab, f"abas da viva diferentes das da referência {ver}: {e}")
        import openpyxl
        wb = openpyxl.load_workbook(ref_antiga)
        try:
            com_nome = set(dp._destinos(wb).values())
        finally:
            wb.close()
        fora = sorted(alteradas - com_nome)
        if fora:
            return _falhar(relatorio, 2, cab, f"viva com {len(fora)} célula(s) alterada(s) fora dos nomes de dado (ent/org/fte): "
                                              + ", ".join(f"{a}!{c}" for a, c in fora[:40]))
        objetos = dp.objetos_alterados(copia, ref_antiga)
        if objetos:
            return _falhar(relatorio, 2, cab, f"viva com comentários, hiperlinks, imagens ou gráficos diferentes da referência "
                                              f"({len(objetos)}): " + "; ".join(f"{a}!{c} ({t})" for a, c, t in objetos)
                           + ". Estes objetos não são migrados por esta ferramenta: leve-os à mão ou obtenha aprovação para deixá-los de fora.")
        viva_m = _mapear(dp.ler_por_nome(copia), mapa)
        base_m = _mapear(dp.ler_por_nome(ref_antiga), mapa)
        equipe = {n: x for n, x in viva_m.items() if not dp.iguais(x, base_m.get(n))}
        celula = {n: f"{a}!{c}" for n, (a, c) in _destinos_de(para).items()}
        rel = dp.injetar(para, equipe, saida, base=base_m)
    except ValueError as e:
        return _falhar(relatorio, 2, cab, f"erro de dado na migração: {e}")
    falha = bool(rel.conflitos or rel.faltando)
    linhas = ["# Migração da viva para a versão nova (por nome)", "", *cab, f"- Mapa de rótulos de Origem ({ver} -> {ver_nova}): "
              + (", ".join(f"`{a}` -> `{b}`" for a, b in mapa.items()) or "nenhum"), "",
              "| Situação | Nomes |", "|---|---|",
              f"| Dado da equipe (viva ≠ referência {ver}, rótulos mapeados) | {len(equipe)} |",
              f"| Escritos | {len(rel.escritas)} |", f"| Já iguais na versão nova | {len(rel.iguais)} |",
              f"| Conflitos (não escritos) | {len(rel.conflitos)} |", f"| Faltando na versão nova | {len(rel.faltando)} |", "",
              f"Resultado: **{'FAIL' if falha else 'PASS'}** (conflito ou falta dão código 1). Para resolver um conflito, escolha o "
              "valor e acerte-o na viva (pelo Excel) ou na saída desta execução; rodar de novo com a mesma `--saida` a sobrescreve.",
              "", "## Conflitos", ""]
    if rel.conflitos:
        linhas += ["| Nome | Célula | Base | Destino (versão nova) | Novo (viva) |", "|---|---|---|---|---|"]
        linhas += [f"| `{n}` | {celula.get(n, '?')} | {_md(b)} | {_md(d)} | {_md(x)} |" for n, b, d, x in rel.conflitos]
    else:
        linhas.append("Nenhum.")
    linhas += ["", "## Faltando na versão nova", ""] + ([f"- `{n}`" for n in rel.faltando] or ["Nenhum."])
    linhas += ["", "## Escritas", ""]
    if rel.escritas:
        linhas += ["| Nome | Célula | Novo |", "|---|---|---|"] + [f"| `{n}` | {celula.get(n, '?')} | {_md(equipe[n])} |" for n in rel.escritas]
    else:
        linhas.append("Nenhuma.")
    _escrever(relatorio, linhas)
    print(f"dado da equipe {len(equipe)}: escritos {len(rel.escritas)}, iguais {len(rel.iguais)}, conflitos {len(rel.conflitos)}, "
          f"faltando {len(rel.faltando)} -> {saida}; relatório: {relatorio}")
    return 1 if falha else 0


def _destinos_de(xlsx: Path) -> dict[str, tuple[str, str]]:
    import openpyxl
    wb = openpyxl.load_workbook(xlsx)
    try:
        return dp._destinos(wb)
    finally:
        wb.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Leva os dados da viva para uma cópia da versão nova, por nome.")
    p.add_argument("viva", type=Path, help="planilha viva (só leitura)")
    p.add_argument("--para", type=Path, required=True, help="planilha da versão nova (só leitura)")
    p.add_argument("--saida", type=Path, default=None)
    p.add_argument("--relatorio", type=Path, default=RELATORIO_PADRAO)
    a = p.parse_args()
    saida = a.saida or RAIZ / "build" / f"{a.para.stem}_com_dados.xlsx"
    with tempfile.TemporaryDirectory(prefix="dds_viva_", ignore_cleanup_errors=True) as tmp:
        return migrar(a.viva, a.para, saida, a.relatorio, Path(tmp))


if __name__ == "__main__":
    sys.exit(main())
