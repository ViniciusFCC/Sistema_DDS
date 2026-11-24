"""
Ponto de entrada do executável único do posicionador da atuação dianteira (EDR-076).

Três jeitos de usar o `posicionador_T11.exe`:
1. dois cliques: abre um menu (avaliar a v20, buscar posições num STEP, rodar o STEP de exemplo);
2. arrastar um arquivo `.step` em cima do `.exe`: busca direta com os valores padrão;
3. linha de comando: `posicionador_T11.exe --avaliar-v20 --saida PASTA` (as mesmas opções de `tools/posicionar_atuacao.py`;
   `--help` lista todas).

Cada execução grava uma pasta `resultados\\AAAAMMDD_HHMMSS_<modo>` ao lado do `.exe` com `relatorio.md`, `resultado.json` e, se
houver candidato, `candidato_NN.csv`. No fim, o programa imprime o resumo na tela. O veredito nunca passa de CONDICIONAL: o
posicionador não aprova nada (VERIFIED não é validado).

Os dados (configuração, hardpoints, STEP de exemplo) vão dentro do `.exe`; o código é o de `python/posicionador/`.
"""
import json
import os
import sys
import time
from pathlib import Path

CONGELADO = bool(getattr(sys, "frozen", False))
RAIZ = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
os.environ.setdefault("DDS_RAIZ", str(RAIZ))
sys.path.insert(0, str(RAIZ / "python"))
sys.path.insert(0, str(RAIZ / "tools"))

import posicionar_atuacao as pa  # noqa: E402

PASTA_SAIDA = (Path(sys.executable).parent if CONGELADO else Path.cwd()) / "resultados"
EXEMPLO_STEP = RAIZ / "data" / "cad" / "T11_chassi_2026-11-17.step"
# (nome, amostras, refinos, estimativa de tempo com STEP; a estimativa vem de medida em 2026-11-23 numa máquina de nuvem)
PREDEFINICOES = [("rápida", 60, 5, "alguns minutos"), ("padrão", 200, 20, "cerca de 11 minutos"),
                 ("completa", 1000, 20, "cerca de uma hora ou mais")]


def configurar_console():
    if os.name == "nt":
        os.system("chcp 65001 >nul")
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def nova_pasta(modo):
    p = PASTA_SAIDA / f"{time.strftime('%Y%m%d_%H%M%S')}_{modo}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _violadas(av):
    return [r["nome"] for r in av.get("restricoes", []) if r.get("estado") == "VIOLADA"]


def _nv(av):
    return [r["nome"] for r in av.get("restricoes", []) if r.get("estado") == "NAO_VERIFICAVEL"]


def _var_mr(av):
    r = next((x for x in av.get("restricoes", []) if x.get("nome") == "variação de MR"), None)
    return None if r is None or r.get("valor") is None else 100 * float(r["valor"])


def imprimir_resumo(pasta):
    """Resumo na tela, lido do resultado.json."""
    arq = Path(pasta) / "resultado.json"
    if not arq.is_file():
        return
    d = json.loads(arq.read_text(encoding="utf-8"))
    print("\n" + "=" * 72)
    print("RESUMO  (VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics)")
    print("=" * 72)
    if d.get("modo") == "avaliar-v20":
        v = d["v20"]
        print(f"Avaliação da v20: {v['veredito']}")
        mr = _var_mr(v)
        print(f"  variação de MR: {mr:.2f} % (limite 4 %)" if mr is not None else "")
        print("  restrições violadas: " + (", ".join(_violadas(v)) or "nenhuma"))
    else:
        cands = d.get("candidatos") or []
        if cands:
            print(f"{len(cands)} candidato(s) (VIAVEL ou CONDICIONAL, reavaliados com resolução convergida):")
            for c in cands[:5]:
                av = c["avaliacao"]
                mr = _var_mr(av)
                print(f"  #{c['rank']:02d} {av['veredito']}  variação de MR {mr:.2f} %  -> {c.get('arquivo_csv')}")
        else:
            f = d.get("fase1") or {}
            print("Nenhum candidato viável nesta busca.")
            print(f"  {f.get('motivo', '')}")
            m = f.get("melhor")
            if m:
                av = m["avaliacao"]
                mr = _var_mr(av)
                print(f"  Melhor encontrado: violação máxima {100 * m['violacao_max_normalizada']:.2f} % do limite"
                      + (f", variação de MR {mr:.2f} %" if mr is not None else ""))
                print("  restrições violadas: " + (", ".join(_violadas(av)) or "nenhuma"))
            print("  Isso não prova que não existe posição viável: a busca é por amostragem.")
        nv = d.get("a_confirmar") or {}
        if nv:
            print(f"  Itens a confirmar na configuração (verificações desligadas): {len(nv)}")
    print(f"\nRelatório completo: {Path(pasta) / 'relatorio.md'}")
    print(f"Tempo: {d.get('tempo_s', 0):.0f} s")


def executar(argv, pasta=None):
    try:
        codigo = pa.principal(argv)
    except pa.ErroEntrada as e:
        print(f"\nERRO: {e}")
        return 2
    except Exception as e:                                # noqa: BLE001  (mensagem curta para quem não programa)
        print(f"\nERRO inesperado ({type(e).__name__}): {e}")
        return 1
    if pasta is not None:
        imprimir_resumo(pasta)
    return codigo


def escolher_step():
    """Janela de seleção de arquivo (tkinter) ou, se não houver, o caminho digitado ou arrastado para a janela."""
    try:
        import tkinter
        from tkinter import filedialog
        raiz = tkinter.Tk()
        raiz.withdraw()
        raiz.attributes("-topmost", True)
        c = filedialog.askopenfilename(title="Escolha o arquivo STEP do chassi", filetypes=[("STEP", "*.step *.stp")])
        raiz.destroy()
        if c:
            return c
    except Exception:                                      # noqa: BLE001
        pass
    return input("Caminho do arquivo .step (pode arrastar o arquivo para esta janela): ").strip().strip('"')


def escolher_predefinicao():
    print("\nTamanho da busca:")
    for i, (n, a, r, t) in enumerate(PREDEFINICOES, start=1):
        print(f"  {i}) {n}: {a} amostras, {r} refinos ({t} com STEP)")
    e = input("Escolha [2]: ").strip() or "2"
    return PREDEFINICOES[int(e) - 1] if e in ("1", "2", "3") else PREDEFINICOES[1]


def busca(step, predef=None):
    nome, am, ref, _ = predef or PREDEFINICOES[1]
    pasta = nova_pasta("busca")
    print(f"\nBusca '{nome}' em {step}\nSaída: {pasta}\n(o progresso aparece abaixo; não feche a janela)\n")
    return executar(["--step", str(step), "--saida", str(pasta), "--amostras", str(am), "--refinos", str(ref)], pasta)


def menu():
    print("=" * 72)
    print(" POSICIONADOR DA ATUAÇÃO DIANTEIRA — T11 (Equipe Tupã)  ·  EDR-076, fase 1")
    print("=" * 72)
    print("Diz onde push rod, rocker e amortecedor PODEM ficar sem colidir com o CAD e")
    print("com o regulamento, cumprindo as metas de MR e de curso do amortecedor.")
    print("Não dita tubos e não aprova nada: o melhor veredito é CONDICIONAL.\n")
    print("  1) Avaliar a v20 (segundos, sem CAD)")
    print("  2) Buscar posições num arquivo STEP")
    print("  3) Buscar no STEP de exemplo do T11")
    print("  0) Sair")
    op = input("\nEscolha: ").strip()
    if op == "1":
        pasta = nova_pasta("v20")
        return executar(["--avaliar-v20", "--saida", str(pasta)], pasta)
    if op == "2":
        step = escolher_step()
        if not step or not os.path.isfile(step):
            print(f"Arquivo não encontrado: {step!r}")
            return 2
        return busca(step, escolher_predefinicao())
    if op == "3":
        return busca(EXEMPLO_STEP, escolher_predefinicao())
    return 0


def principal(argv):
    configurar_console()
    if argv and argv[0].lower().endswith((".step", ".stp")) and len(argv) == 1:
        return busca(argv[0])                                  # arrastar o .step para o .exe
    if argv:
        return executar(argv)                                  # linha de comando completa
    codigo = menu()
    return codigo


if __name__ == "__main__":
    try:
        codigo = principal(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nInterrompido.")
        codigo = 130
    if CONGELADO and len(sys.argv) <= 2:                       # janela aberta por clique ou arraste: não fechar sozinha
        try:
            input("\nEnter para fechar...")
        except EOFError:
            pass
    sys.exit(codigo)
