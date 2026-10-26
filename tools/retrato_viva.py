"""Retrato dos dados da planilha viva por nome (commit `dados:`; EDR-063).

Uso:
    uv run python -X utf8 tools/retrato_viva.py [ARQ] [--saida data/viva/retrato-viva.json]

Só grava o retrato se a conferência (`conferir_viva`) der 0: com a viva igual à referência da tag + as entradas, o JSON e a
tag reconstroem a viva (o .xlsx de 3,2 MB não entra no Git; o Drive já guarda o histórico do arquivo). O JSON tem
`{"versao", "sha256", "data", "dados": {nome: valor}}`, chaves ordenadas, uma por linha, fim de linha LF:
- `versao`: a da 00_README A3 da viva; `sha256`: o da cópia lida; `data`: o dia do retrato (AAAA-MM-DD);
- `dados`: os nomes `ent_`, `org_` e `fte_` com o valor cru da célula. Texto, número (int e float ficam distintos), booleano e
  vazio são JSON; data e hora viram `{"$tipo": "datetime", "valor": "<ISO 8601>"}` (também "date" e "time"), para a volta
  devolver o mesmo tipo. Fórmula em célula de dado é erro (a conferência já a recusa).
`carregar` faz o caminho de volta (JSON -> dados por nome), que `dados_planilha.injetar` leva a uma cópia da versão.

Código de saída: o da conferência (1 diverge, 3 não lida) sem gravar nada; 0 gravado. Lê só uma cópia da viva; grava só o
JSON (nunca em excel/ nem no Drive).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))
sys.path.insert(0, str(RAIZ / "tools"))
import dados_planilha as dp  # noqa: E402
import viva as v  # noqa: E402
from conferir_viva import conferir  # noqa: E402

SAIDA_PADRAO = RAIZ / "data" / "viva" / "retrato-viva.json"
_TIPOS = {"datetime": dt.datetime, "date": dt.date, "time": dt.time}


def codificar(valor):
    """Valor de célula -> valor JSON, com os tipos que o JSON não tem marcados em `{"$tipo", "valor"}`."""
    for nome, tipo in _TIPOS.items():          # datetime antes de date (datetime é subclasse de date)
        if isinstance(valor, tipo):
            return {"$tipo": nome, "valor": valor.isoformat()}
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    raise ValueError(f"valor de tipo {type(valor).__name__} sem codificação no retrato: {valor!r}")


def decodificar(valor):
    if isinstance(valor, dict):
        if set(valor) != {"$tipo", "valor"} or valor["$tipo"] not in _TIPOS:
            raise ValueError(f"objeto inesperado no retrato: {valor!r}")
        return getattr(_TIPOS[valor["$tipo"]], "fromisoformat")(valor["valor"])
    return valor


def carregar(json_path: Path) -> dict:
    """Retrato -> {"versao", "sha256", "data", "dados": {nome: valor com o tipo original}}."""
    r = json.loads(Path(json_path).read_text(encoding="utf-8"))
    r["dados"] = {k: decodificar(x) for k, x in r["dados"].items()}
    return r


def retratar(arquivo: Path, saida: Path, pasta: Path, referencia: Path | None = None) -> int:
    """Confere `arquivo` (cópia em `pasta`) e, com código 0, grava o retrato em `saida`. Devolve o código da conferência
    (0 gravado; 1 diverge; 3 não lida; 2 dado com fórmula ou tipo sem codificação)."""
    saida = Path(saida)
    destino = saida.resolve()
    if destino.parent == (RAIZ / "excel").resolve():
        print(f"saída em excel/ recusada ({saida})")
        return 2
    codigo, rel, ver = conferir(arquivo, pasta, referencia)
    if codigo != 0:
        print("\n".join(rel))
        print(f"retrato NÃO gravado: a conferência deu código {codigo}")
        return codigo
    copia = Path(pasta) / Path(arquivo).name
    dados = dp.ler_por_nome(copia)
    try:
        com_formula = sorted(k for k, x in dados.items() if dp._eh_formula(x))
        if com_formula:
            raise ValueError(f"dado com fórmula: {com_formula[:5]}")
        codificados = {k: codificar(dados[k]) for k in sorted(dados)}
    except ValueError as e:
        print(f"retrato NÃO gravado: {e}")
        return 2
    retrato = {"versao": ver, "sha256": v.sha256(copia), "data": dt.date.today().isoformat(), "dados": codificados}
    # uma chave por linha: o diff do Git mostra exatamente o que a equipe mudou
    linhas = [f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(x, ensure_ascii=False)}" for k, x in codificados.items()]
    cab = [f"  \"versao\": {json.dumps(ver)}", f"  \"sha256\": {json.dumps(retrato['sha256'])}",
           f"  \"data\": {json.dumps(retrato['data'])}"]
    texto = "{\n" + ",\n".join(cab) + ",\n  \"dados\": {\n" + ",\n".join("  " + l for l in linhas) + "\n  }\n}\n"
    json.loads(texto)    # o texto montado à mão tem de ser JSON válido
    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    print(f"retrato gravado: {saida} ({len(dados)} dados, versão {ver})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Retrato dos dados da viva por nome (só com a conferência em 0).")
    p.add_argument("arquivo", nargs="?", type=Path, default=None)
    p.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    a = p.parse_args()
    try:
        arq = a.arquivo or v.localizar_viva()
    except ValueError as e:
        print(f"NÃO LIDA: {e}")
        return 3
    if arq is None:
        print("NÃO LIDA: nenhuma viva localizada (Drive desmontado ou DDS_VIVA sem valor)")
        return 3
    with tempfile.TemporaryDirectory(prefix="dds_viva_", ignore_cleanup_errors=True) as tmp:
        return retratar(arq, a.saida, Path(tmp))


if __name__ == "__main__":
    sys.exit(main())
