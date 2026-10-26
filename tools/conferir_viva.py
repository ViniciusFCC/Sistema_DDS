"""Confere a planilha viva da equipe (Google Drive) contra a referência da versão dela (EDR-063).

Uso:
    uv run python -X utf8 tools/conferir_viva.py [ARQ]

Sem ARQ, usa a viva localizada (`viva.localizar_viva`: variável DDS_VIVA, ou o único FSAE_EV_Suspension_Fase1_V*.xlsx da pasta
do Drive). A viva é copiada para uma pasta temporária (só leitura do original; nada é gravado no Drive nem em excel/) e a
CÓPIA é lida. A versão vem da 00_README A3 (V4.1 -> tag v4.1; V4.2 -> tag v4.2 ou, antes da tag, excel/) e a conferência é a
`comparar_viva`: tudo igual à referência menos as células de entrada, com a Origem entre os rótulos da versão, fórmulas e
estrutura intactas. Na V4.2 em diante, todo EDR citado nas fichas de meta tem de existir e estar APPROVED no registro.

Código de saída: 0 viva fiel; 1 diverge (as diferenças são listadas); 3 não lida (ausente, 0 byte, bloqueada, Drive
desmontado, versão sem referência). Nunca PASS quando não leu.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))
sys.path.insert(0, str(RAIZ / "tools"))
import comparar_planilhas as cp  # noqa: E402
import viva as v  # noqa: E402

REGISTRO_EDR = RAIZ / "docs" / "Engineering_Decision_Register.md"


def conferir(arquivo: Path, pasta: Path, referencia: Path | None = None,
             registro_edr: Path = REGISTRO_EDR) -> tuple[int, list[str], str]:
    """Copia `arquivo` para `pasta`, lê a versão e confere contra a referência (`referencia`, ou a da tag/excel/ da versão).
    Devolve (código 0/1/3, linhas do relatório, versão ou ""). Não levanta VivaIlegivel: vira código 3 com a mensagem."""
    ver = ""
    try:
        copia = v.copia_local(Path(arquivo), Path(pasta))
        ver = v.versao(copia)
        ref = v.referencia_da(ver)
        arq_ref = Path(referencia) if referencia is not None else v.arquivo_de_referencia(ver, Path(pasta))
        if not arq_ref.is_file():
            raise v.VivaIlegivel(f"referência ausente: {arq_ref}")
        edrs = v.edrs_aprovados(registro_edr) if ref.confere_edr else None
        ok, rel = cp.comparar_viva(copia, arq_ref, ref.entradas(), esperadas=ref.formulas, rotulos=ref.rotulos, edrs=edrs)
    except v.VivaIlegivel as e:
        return 3, [f"NÃO LIDA: {e}"], ver
    cab = [f"viva: {arquivo}", f"versão da viva (00_README A3): {ver}; referência: {arq_ref}", f"SHA-256 da cópia: {v.sha256(copia)}"]
    return (0 if ok else 1), cab + rel, ver


def main() -> int:
    arq = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if len(sys.argv) > 2:
        sys.exit(__doc__)
    try:
        if arq is None:
            arq = v.localizar_viva()
    except ValueError as e:
        print(f"NÃO LIDA: {e}")
        return 3
    if arq is None:
        print("NÃO LIDA: nenhuma viva localizada (Drive desmontado ou DDS_VIVA sem valor)")
        return 3
    with tempfile.TemporaryDirectory(prefix="dds_viva_", ignore_cleanup_errors=True) as tmp:
        codigo, rel, _ = conferir(arq, Path(tmp))
    print("\n".join(rel))
    print({0: "VIVA FIEL (código 0)", 1: "VIVA DIVERGE (código 1)", 3: "VIVA NÃO LIDA (código 3)"}[codigo])
    return codigo


if __name__ == "__main__":
    sys.exit(main())
