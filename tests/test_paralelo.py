"""
Testes de tools/paralelo.py (progresso, gravação incremental e retomada da execução paralela).
Roda como script: uv run python -X utf8 tests/test_paralelo.py
"""
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paralelo  # noqa: E402

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def dobra(tarefa):
    time.sleep(0.05 * (3 - tarefa["k"] % 3))        # termina fora de ordem
    return dict(k=tarefa["k"], dobro=2 * tarefa["k"], inf=float("inf"))


def quebra(tarefa):
    if tarefa["k"] == 2:
        raise ValueError("falha de teste")
    return tarefa["k"]


def main():
    tarefas = [dict(k=k) for k in range(8)]
    with tempfile.TemporaryDirectory() as d:
        arq = Path(d) / "r.jsonl"

        r1 = paralelo.mapear(dobra, tarefas, 3, "t1", arq, batida_s=1)
        check("TC-PAR-001 ordem original", [x["k"] for x in r1] == list(range(8)), str([x["k"] for x in r1]))
        check("TC-PAR-002 resultado serializado (inf ok)", r1[3]["dobro"] == 6 and r1[3]["inf"] == float("inf"))
        linhas = arq.read_text(encoding="utf-8").splitlines()
        check("TC-PAR-003 uma linha por tarefa no jsonl", len(linhas) == 8, f"{len(linhas)} linhas")

        # retomada: corta o arquivo em 5 linhas (o resto é refeito) e confere que o final é igual
        arq.write_text("\n".join(linhas[:5]) + "\n", encoding="utf-8")
        r2 = paralelo.mapear(dobra, tarefas, 3, "t2", arq)
        check("TC-PAR-004 retomada reproduz o resultado", r2 == r1)
        check("TC-PAR-005 retomada completa o arquivo", len(arq.read_text(encoding="utf-8").splitlines()) == 8)

        # retomada com a última linha cortada no meio (interrupção durante a escrita)
        arq.write_text("\n".join(linhas[:4]) + "\n" + linhas[4][:20], encoding="utf-8")
        r3 = paralelo.mapear(dobra, tarefas, 3, "t3", arq)
        check("TC-PAR-006 última linha truncada é refeita", r3 == r1)

        # tudo pronto: nenhum worker necessário
        r4 = paralelo.mapear(dobra, tarefas, 3, "t4", arq)
        check("TC-PAR-007 tudo já feito devolve direto", r4 == r1)

        # argumentos diferentes com o mesmo arquivo: recusa
        outros = [dict(k=k + 100) for k in range(8)]
        try:
            paralelo.mapear(dobra, outros, 3, "t5", arq)
            recusou = False
        except SystemExit as e:
            recusou = "não bate" in str(e)
        check("TC-PAR-008 hash diferente recusa e não mistura", recusou)

        # erro numa tarefa: relança e preserva o que já saiu
        arq2 = Path(d) / "e.jsonl"
        try:
            paralelo.mapear(quebra, [dict(k=k) for k in range(4)], 1, "t6", arq2)
            relancou = False
        except RuntimeError as e:
            relancou = "tarefa 2" in str(e)
        n_ok = len(arq2.read_text(encoding="utf-8").splitlines()) if arq2.exists() else 0
        check("TC-PAR-009 erro relança e preserva os anteriores", relancou and n_ok == 2, f"{n_ok} gravados")

        # sem jsonl: funciona só na memória
        r7 = paralelo.mapear(dobra, tarefas[:3], 2, "t7")
        check("TC-PAR-010 sem jsonl", [x["k"] for x in r7] == [0, 1, 2])


if __name__ == "__main__":
    main()
    print("\n--- Resumo ---")
    n_pass = sum(1 for _, s, _ in results if s == "PASS")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
    if n_fail > 0:
        raise SystemExit(1)
