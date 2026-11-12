"""Captura do caso do pneu-1 a partir da planilha V4.4: lê as entradas pelos nomes definidos e grava o JSON do caso.

Uso: uv run python -X utf8 tools/capturar_caso_pneu1.py <xlsx> [--saida ARQ]

Só leitura: a planilha é aberta com data_only=False (a V4.4 de `excel/` não tem valores em cache) e nunca é salva nem
recalculada. O padrão de --saida é build/pneu1/caso_capturado.json; o caso demonstrativo do repositório
(data/casos/caso_pneu1_demonstrativo.json) só recebe uma cópia depois da conferência da tabela de origens.

Códigos de saída: 0 capturou; 2 entrada com fórmula, nome ausente, valor inválido ou modo do R não suportado.

Regras (D2 do plano): `R_m` não é lido (é a fórmula =res_24_r_usado): sai da regra da 24_CURVA B20 com os valores de
entrada (Linha central: (D_int + D_ext)/4; Manual: o R manual; Rente aos cones: não suportado). `fator_neutro` (24_CURVA
B34) é a fórmula constante `=4/3`, aceita só nessa forma. `ackermann_pct` (07 B75 é resultado) e `crr_referencia` (sem
fonte) ficam null com a origem `? A confirmar`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))

import openpyxl  # noqa: E402

import aba_curva  # noqa: E402
import aba_equilibrio as ae  # noqa: E402
import caso_pneu1 as cp  # noqa: E402
import origens  # noqa: E402
import raizes  # noqa: E402

SAIDA_PADRAO = RAIZ / "build" / "pneu1" / "caso_capturado.json"
AVISO = "DEMONSTRATIVO: caso de outro carro (T09/E03 e TX), não o T11"
FORMULA_FATOR = re.compile(r"^=(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)$")
LINHAS_COEF = list(range(86, 176)) + [177]       # 10_TIRE: coeficientes do .tir (A = nome, B = valor)


class ErroCaptura(Exception):
    """Erro que vira código de saída 2, com a mensagem para o usuário."""


def _destino(wb, nome: str) -> tuple[str, str]:
    try:
        return ae._destino(wb, nome)
    except (KeyError, ValueError) as e:
        raise ErroCaptura(f"{nome}: {e}") from None


def _origem_da_celula(wb, aba: str, cel: str) -> str:
    """Origem da célula pela regra do projeto (aba_equilibrio._origem_da_raiz: coluna E nas abas de entrada; 10_TIRE:
    I23 a I25 nos casos de carga e I84 no resto, que é a origem do pneu). 16 e 24 não têm regra lá: coluna E da própria
    linha. Vazio ou fora da lista da V4.4 conta como `? A confirmar`."""
    try:
        aba_o, cel_o = ae._origem_da_raiz(aba, cel)
    except ValueError:
        aba_o, cel_o = aba, f"E{raizes.linha(cel)}"
    v = wb[aba_o][cel_o].value
    return v if v in origens.ORIGENS_V42 else cp.ORIGEM_A_CONFIRMAR


def _pior(rotulos: list[str]) -> str:
    return max(rotulos, key=cp._ORDEM_ORIGEM.index)


def _confere_lista_origens(wb) -> None:
    aba, ref = list(wb.defined_names["Origens"].destinations)[0]
    na_planilha = tuple(c[0].value for c in wb[aba][ref.replace("$", "")])
    if na_planilha != tuple(origens.ORIGENS_V42):
        raise ErroCaptura(f"a lista Origens da planilha {na_planilha} difere de origens.ORIGENS_V42.")


def _valor_de_entrada(wb, chave: str, aba: str, cel: str, nome: str):
    v = wb[aba][cel].value
    if isinstance(v, str) and v.startswith("="):
        raise ErroCaptura(f"{chave}: a célula {aba} {cel} ({nome}) tem fórmula ({v}); só entrada digitada é capturada.")
    return v


def _num(v, chave: str, nome: str):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ErroCaptura(f"{chave}: {nome} não é um número ({v!r}).")
    return v


def _raio(wb) -> tuple[float, str, str, str]:
    """(R_m, origem, fonte, descrição) pela regra da 24_CURVA B20 (D2)."""
    def ent(k):
        nome = aba_curva.NOME24[k]
        aba, cel = _destino(wb, nome)
        return wb[aba][cel].value, aba, cel, nome
    modo, a_m, c_m, n_m = ent("modo")
    if modo == "Linha central":
        (di, a1, c1, n1), (de, a2, c2, n2) = ent("dint")[:4], ent("dext")[:4]
        di, de = _num(di, "R_m", n1), _num(de, "R_m", n2)
        origem = _pior([_origem_da_celula(wb, a1, c1), _origem_da_celula(wb, a2, c2)])
        fonte = (f"(({n1}) + ({n2}))/4, modo Linha central ({a1} {c1} e {c2}; 24_CURVA B20); "
                 f"modo em {n_m} ({a_m} {c_m})")
        return (di + de) / 4, origem, fonte, modo
    if modo == "Manual":
        rm, a, c, n = ent("rman")
        rm = _num(rm, "R_m", n)
        return rm, _origem_da_celula(wb, a, c), f"{n} ({a} {c}), modo Manual (24_CURVA B20)", modo
    if modo == "Rente aos cones":
        raise ErroCaptura("modo do R não suportado na captura: use Linha central ou Manual.")
    raise ErroCaptura(f"R_m: o modo do R {modo!r} não é Linha central, Rente aos cones nem Manual.")


def _fator(wb, nome: str) -> float:
    aba, cel = _destino(wb, nome)
    v = wb[aba][cel].value
    m = FORMULA_FATOR.match(v) if isinstance(v, str) else None
    if m is None:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        raise ErroCaptura(f"fator_neutro: {aba} {cel} tem {v!r}; aceito só um número ou a fórmula =a/b de constantes.")
    return float(m.group(1)) / float(m.group(2))


def _coef_lambda(wb, nome_tir: str, nome_def: str) -> tuple[float, str]:
    """Valor e origem do coeficiente `nome_tir` na 10_TIRE (nome em A, valor em B); confere A contra o nome do .tir."""
    aba, cel = _destino(wb, nome_def)
    r = raizes.linha(cel)
    if r not in LINHAS_COEF or str(wb[aba][f"A{r}"].value).strip() != nome_tir:
        raise ErroCaptura(f"lambda_{nome_tir}: {aba} A{r} é {wb[aba][f'A{r}'].value!r}, não {nome_tir}.")
    return _num(wb[aba][cel].value, f"lambda_{nome_tir}", nome_def), _origem_da_celula(wb, aba, cel)


def capturar(xlsx: Path) -> dict:
    wb = openpyxl.load_workbook(xlsx, data_only=False)
    try:
        _confere_lista_origens(wb)
        campos: dict[str, dict] = {}
        for chave, c in cp.CAMPOS.items():
            valor, origem, fonte = None, cp.ORIGEM_A_CONFIRMAR, ""
            if chave == "R_m":
                valor, origem, fonte, _ = _raio(wb)
            elif chave == "fator_neutro":
                aba, cel = _destino(wb, c.nome_definido)
                valor = _fator(wb, c.nome_definido)
                origem, fonte = _origem_da_celula(wb, aba, cel), f"{c.nome_definido} ({aba} {cel}), fórmula {wb[aba][cel].value}"
            elif chave == "ackermann_pct":
                aba, cel = _destino(wb, c.nome_definido)
                fonte = f"{c.nome_definido} ({aba} {cel}) é resultado: não capturado; informe o valor se a h2 for ligada"
            elif c.nome_definido is None:
                fonte = "sem fonte na planilha: a confirmar"
            else:
                aba, cel = _destino(wb, c.nome_definido)
                fonte = f"{c.nome_definido} ({aba} {cel})"
                origem = _origem_da_celula(wb, aba, cel)
                if chave.startswith("lambda_"):
                    valor, origem = _coef_lambda(wb, chave[len("lambda_"):], c.nome_definido)
                else:
                    valor = _valor_de_entrada(wb, chave, aba, cel, c.nome_definido)
                if valor is None:
                    origem = cp.ORIGEM_A_CONFIRMAR
                else:
                    try:
                        valor = cp._valida_valor(chave, valor)
                    except ValueError as e:
                        raise ErroCaptura(str(e)) from None
            campos[chave] = {"valor": valor, "unidade": c.unidade, "origem": origem, "fonte": fonte,
                             "rotulo": c.rotulo, "unidade_exibicao": c.unidade, "descricao": c.descricao,
                             "editado": False}
    finally:
        wb.close()
    sha = hashlib.sha256(Path(xlsx).read_bytes()).hexdigest()
    try:
        planilha = str(Path(xlsx).resolve().relative_to(RAIZ)).replace("\\", "/")
    except ValueError:
        planilha = str(xlsx)
    return {"schema": cp.SCHEMA, "aviso": AVISO,
            "captura": {"planilha": planilha, "sha256": sha, "data": date.today().isoformat(),
                        "ferramenta": "tools/capturar_caso_pneu1.py"},
            "campos": campos}


def tabela(dados: dict) -> str:
    linhas = ["| campo | valor | origem |", "|---|---|---|"]
    for k, reg in dados["campos"].items():
        v = "null" if reg["valor"] is None else reg["valor"]
        linhas.append(f"| {k} | {v} | {reg['origem']} |")
    cont = Counter(reg["origem"] for reg in dados["campos"].values())
    linhas += ["", "Contagem por origem:"]
    linhas += [f"- {o}: {cont[o]}" for o in cp._ORDEM_ORIGEM if cont.get(o)]
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Captura o caso do pneu-1 da planilha V4.4 (só leitura).")
    ap.add_argument("xlsx")
    ap.add_argument("--saida", default=str(SAIDA_PADRAO))
    args = ap.parse_args(argv)
    try:
        dados = capturar(Path(args.xlsx))
        cp._checar_estrutura(dados)
    except (ErroCaptura, OSError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    if cp._mesmo_caminho(args.saida, cp.CAMINHO_DEMONSTRATIVO):
        print("ERRO: não grave direto no caso demonstrativo; use o padrão (build/pneu1/) e confira a tabela de origens "
              "antes de copiar.", file=sys.stderr)
        return 2
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(tabela(dados))
    print(f"\nGravado em {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
