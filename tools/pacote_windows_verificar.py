"""
Autoteste do pacote portátil do posicionador (vai para a raiz do pacote como `verificar_instalacao.py`).

Confere, nesta ordem, e imprime PASS ou FAIL por passo:
1. versões de numpy e scipy (obrigatórios) e de matplotlib e OCP (OCP: leitura de STEP; matplotlib: figuras);
2. leitura do STEP de exemplo: 31 corpos (prova que o OpenCascade e as DLLs dele carregam neste computador);
3. a v20 na ferramenta: código de saída 0, relatório com INVIAVEL (resultado esperado, EDR-076) e variação de MR.
Grava `verificar_instalacao.log` na raiz do pacote. Código de saída: 0 = tudo certo; 1 = algum passo falhou (mande o .log).
"""
import importlib
import subprocess
import sys
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "python"))
LOG = []


def dizer(txt):
    print(txt)
    LOG.append(txt)


def passo(nome, f):
    try:
        ok, det = f()
    except Exception:                                   # noqa: BLE001 (o autoteste relata qualquer falha)
        ok, det = False, traceback.format_exc(limit=3)
    dizer(f"[{'PASS' if ok else 'FAIL'}] {nome}: {det}")
    return ok


def versoes():
    out, ok = [], True
    for m, obrig in (("numpy", True), ("scipy", True), ("matplotlib", False), ("OCP", False)):
        try:
            mod = importlib.import_module(m)
            out.append(f"{m} {getattr(mod, '__version__', 'ok')}")
        except Exception as e:                          # noqa: BLE001
            out.append(f"{m} AUSENTE ({type(e).__name__}: {e})")
            ok &= not obrig
    return ok, "; ".join(out) + f"; Python {sys.version.split()[0]}"


def ler_exemplo():
    from posicionador import cad_step as cs
    if not cs.OCP_DISPONIVEL:
        return False, "OCP ausente: a leitura de STEP não está disponível (a avaliação da v20 e a busca com --caixa continuam)"
    m = cs.ler_step(str(RAIZ / "data" / "cad" / "T11_chassi_2026-11-17.step"))
    return len(m.pecas) == 31, f"{len(m.pecas)} corpos lidos (esperado 31)"


def avaliar_v20():
    saida = RAIZ / "resultados" / "verificacao"
    r = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "tools" / "posicionar_atuacao.py"), "--avaliar-v20",
                        "--saida", str(saida)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    rel = (saida / "relatorio.md").read_text(encoding="utf-8") if (saida / "relatorio.md").exists() else ""
    ok = r.returncode == 0 and "INVIAVEL" in rel and "variação de MR" in rel
    return ok, f"código {r.returncode}; INVIAVEL no relatório: {'INVIAVEL' in rel}; relatório: {saida / 'relatorio.md'}" + \
        ("" if ok else f"\n{r.stderr[-600:]}")


def main():
    dizer("Autoteste do pacote do posicionador (EDR-076)")
    oks = [passo("bibliotecas", versoes), passo("leitura do STEP de exemplo", ler_exemplo),
           passo("avaliação da v20", avaliar_v20)]
    dizer("RESULTADO: TUDO OK" if all(oks) else "RESULTADO: FALHOU — mande o arquivo verificar_instalacao.log")
    (RAIZ / "verificar_instalacao.log").write_text("\n".join(LOG) + "\n", encoding="utf-8")
    return 0 if all(oks) else 1


if __name__ == "__main__":
    sys.exit(main())
