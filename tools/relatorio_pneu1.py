"""Relatório do pneu-1 (sensibilidade do pneu e arrasto induzido, EDR-075): linha de comando sobre a API.

Sem lógica de cálculo: lê o caso, aplica os `--set`, chama `sensibilidade_pneu.estudo` e formata o resultado. O caso
padrão é o demonstrativo (dados de outro carro, .tir do R25B do TTC): não é recomendação para o T11.

Uso (Git Bash, depois de export UV_SYSTEM_CERTS=1 e, se preciso, DDS_TTC_DIR):
    uv run python -X utf8 tools/relatorio_pneu1.py [--caso ARQ] [--set chave=valor ...] [--rapido] [--saida DIR]

Grava `relatorio.md` e `resultados.json` em DIR (padrão build/pneu1; `build/` não é versionado).
Saída: 0 = ok; 2 = entrada inválida (mensagem em stderr, sem traceback); 3 = NÃO EXECUTÁVEL (sem os .tir do TTC).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "python"))

import caso_pneu1 as cp  # noqa: E402
import sensibilidade_pneu as sp  # noqa: E402

SAIDA_PADRAO = RAIZ / "build" / "pneu1"
DICA_CHAVES = "veja as chaves em data/casos/caso_pneu1_demonstrativo.json"
AVISO_DEMO = ("**DEMONSTRATIVO.** O caso é o da planilha: dados de outro carro (T09/E03, TX/E05) e o .tir do R25B do "
              "TTC no lugar do R60A. Não é recomendação para o T11.")
AVISO_T11 = "`R_m` é o único valor marcado como \"● Dado do T11\" no caso; todos os outros são de outro carro ou editados."
NOTA_D = ("Energia do enduro: sem traçado não há energia total. D é dado por condição (a_y); a energia é "
          "Σ D·comprimento de cada trecho de curva, com o traçado a confirmar (spec §7.4).")


def n(x, casas: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "sim" if x else "não"
    if isinstance(x, str):
        return x
    if isinstance(x, int):
        return str(x)
    return f"{x:.{casas}f}".replace(".", ",")


def graus(rad, casas: int = 2) -> str:
    return "—" if rad is None else n(math.degrees(rad), casas) + "°"


def tabela(cab: list[str], linhas: list[list]) -> list[str]:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in ln) + " |" for ln in linhas]
    return out


def fatores_txt(f: dict) -> str:
    return ", ".join(f"{k}={n(v, 2)}" for k, v in f.items()) if f else "—"


def tabela_carro(linhas) -> list[str]:
    cab = ["corrida", "pressão (psi)", "KT", "fatores λ", "a_y limite (g)", "veredito", "K (°/g)", "C_f (N/rad)",
           "C_r (N/rad)", "observação"]
    corpo = []
    for l in linhas:
        obs = ("" if l.ay_lim_g is not None else
               f"não avaliado: o carro não chega ao limite até {n(sp.GRADE['ay_max_g'], 1)} g")
        if l.borda_alfa:
            obs = (obs + "; " if obs else "") + "α na borda da grade"
        corpo.append([l.rotulo_corrida, n(l.pressao_psi, 1), l.variante_kt, fatores_txt(l.fatores),
                      n(l.ay_lim_g, 3) if l.ay_lim_g is not None else "N/A", l.veredito,
                      n(l.k_grau_g, 3), n(l.c_f_n_rad, 0), n(l.c_r_n_rad, 0), obs])
    return tabela(cab, corpo)


def montar_relatorio(r: sp.Resultado, rapido: bool, caso_arq: Path) -> str:
    L: list[str] = ["# Pneu-1: sensibilidade e arrasto induzido (EDR-075)", "", AVISO_DEMO, "", AVISO_T11, "",
                    f"Caso: `{caso_arq}`. Modo: {'rápido (sem a combinação de λ)' if rapido else 'completo'}.", ""]
    L += ["## 1. Rótulos obrigatórios", ""] + [f"- {t}" for t in r.rotulos] + [""]
    L += ["## 2. Valores usados", ""]
    L += tabela(["chave", "valor", "unidade", "origem", "editado", "calculado por"],
                [[v.chave, n(v.valor, 4), v.unidade, v.origem, "sim" if v.editado else "não", v.calculado_por or ""]
                 for v in r.valores]) + [""]
    L += ["## 3. Tornado de λ (pressão de 12 psi, KT variante a)", ""] + tabela_carro(r.tornado) + [""]
    L += ["## 4. Pressão (a: KT do caso; b: KT do perfil)", ""] + tabela_carro(r.pressao) + [""]
    L += ["## 5. Combinação de λ", ""]
    if r.combinacao is None:
        L += ["não avaliado: combinação não rodada (--rapido)", ""]
    else:
        L += tabela_carro(r.combinacao) + [""]
    L += ["## 6. Pneu por pressão (os nós medidos são 8, 10, 12 e 14 psi; o resto é interpolação)", ""]
    L += tabela(["pressão (psi)", "eixo", "interpolado", "Fz (N)", "Cα (N/rad)", "μ_y pico", "μ_y na borda"],
                [[n(l.pressao_psi, 1), l.eixo, n(l.interpolado), n(l.fz_n, 1), n(l.c_alpha_n_rad, 0),
                  n(l.mu_y_pico, 3), n(l.mu_y_borda)] for l in r.pneu]) + [""]
    L += ["## 7. Arrasto induzido", "",
          "D = Σ −F_y,i·sen α_i, em N (= J/m, energia por distância percorrida); D/(m·g); D/D_1ª ordem é a razão com a "
          "forma linearizada Σ F_y exigida·|α|.", ""]
    L += tabela(["a_y (g)", "α frente", "α trás", "D (N)", "D/(m·g)", "D/D_1ª ordem"],
                [[n(l.ay_g, 2), graus(l.alfa_f_rad), graus(l.alfa_r_rad), n(l.d_n, 3), n(l.d_sobre_mg, 5),
                  n(l.d_n / l.d_1a_ordem_n, 4) if l.d_1a_ordem_n else "—"] for l in r.arrasto]) + [""]
    rots = sorted({t for l in r.arrasto for t in l.rotulos})
    L += [f"- {t}" for t in rots] + ([""] if rots else [])
    L += [NOTA_D, ""]
    L += ["## 8. Decisões por degrau", ""]
    L += tabela(["degrau", "nome", "muda decisão", "frase"], [[d.degrau, d.nome, d.muda, d.frase] for d in r.decisoes])
    L += ["", "Critérios por degrau:", ""]
    for d in r.decisoes:
        if d.criterios:
            L.append(f"- Degrau {d.degrau}: " + "; ".join(f"{k} ({v})" for k, v in d.criterios.items()))
    L += ["", "## 9. Tempos (s)", ""]
    L += tabela(["parte", "tempo (s)"], [[k, n(v, 1)] for k, v in r.tempos_s.items()])
    L += [f"| total | {n(sum(r.tempos_s.values()), 1)} |", ""]
    return "\n".join(L)


def _mensagem_entrada(exc: ValueError) -> str:
    """Texto simples para o leigo; a mensagem da validação (com o código SUS, se houver) vai entre parênteses."""
    txt = str(exc)
    if "não é um campo do caso" in txt:
        chave = txt.split(":")[0].strip()
        return f"chave desconhecida: {chave} ({DICA_CHAVES})"
    return f"entrada inválida: {txt} ({DICA_CHAVES})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--caso", type=Path, default=cp.CAMINHO_DEMONSTRATIVO)
    ap.add_argument("--set", dest="sets", action="append", default=[], metavar="CHAVE=VALOR")
    ap.add_argument("--rapido", action="store_true", help="sem a combinação de λ")
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = ap.parse_args(argv)

    try:
        dados = cp.aplicar_set(sp.ler_caso(args.caso), args.sets)
    except FileNotFoundError:
        print(f"erro: não achei o arquivo do caso: {args.caso}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"erro: o arquivo {args.caso} não é um JSON válido ({exc})", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"erro: {_mensagem_entrada(exc)}", file=sys.stderr)
        return 2

    if cp.achar_ttc() is None:
        print("NÃO EXECUTÁVEL: faltam os .tir do TTC Round 6 (defina DDS_TTC_DIR ou coloque-os em "
              f"{cp.SUBDIR_TTC.as_posix()}). Não conta como aprovado.", file=sys.stderr)
        return 3
    try:
        familia = sp.familia_ttc()
        montado = sp.caso_de_dados(dados, familia)
        res = sp.estudo(montado, familia, rapido=args.rapido)
    except FileNotFoundError as exc:
        print(f"NÃO EXECUTÁVEL: {exc}", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(f"erro: o caso não passa nas verificações do modelo: {exc}", file=sys.stderr)
        return 2

    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "resultados.json").write_text(
        json.dumps(res.para_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    (args.saida / "relatorio.md").write_text(montar_relatorio(res, args.rapido, args.caso), encoding="utf-8",
                                             newline="\n")
    print(f"gravado em {args.saida} (relatorio.md e resultados.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
