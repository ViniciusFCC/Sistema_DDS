"""
Execução paralela com progresso visível, gravação incremental e retomada (padrão do projeto, CLAUDE.md).

Substitui o `pool.map(...)` cego: ele só devolve algo quando TODAS as tarefas terminam, então uma execução longa fica
sem nenhuma informação e, se for interrompida, perde tudo.

`mapear(fn, tarefas, n_proc, rotulo, jsonl=None, descrever=None)`:
- usa `spawn` e uma tarefa por vez, como antes; `fn` precisa ser função de módulo (picklável) e receber uma tarefa;
- a cada tarefa pronta imprime em stderr `[k/N] decorrido · estimativa de falta · descrição · duração`;
- sem tarefa pronta há `batida_s` segundos, imprime um sinal de vida ("N em andamento, último término há X min");
- com `jsonl`, grava o resultado de cada tarefa assim que sai (flush + fsync) e, ao reiniciar, pula os já feitos;
  se algum registro do arquivo não bate com a tarefa de mesmo índice (argumentos mudaram), recusa em vez de misturar;
- devolve os resultados na ordem original das tarefas. Todo resultado passa por JSON (ida e volta), igual para as tarefas
  novos e para os retomados; por isso precisa ser serializável (numpy é convertido; nan e inf são aceitos);
- erro em uma tarefa: imprime a tarefa e o traceback, mantém o que já foi gravado e relança.
"""
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
import traceback
from pathlib import Path


def _padrao_json(o):
    if hasattr(o, "tolist"):          # ndarray e escalares do numpy
        return o.tolist()
    return str(o)


def _hash(tarefa):
    return hashlib.sha1(json.dumps(tarefa, default=_padrao_json, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _ida_e_volta(r):
    return json.loads(json.dumps(r, default=_padrao_json))


class _Cronometrado:
    """Chamável picklável: roda fn(tarefa), mede o tempo e devolve o erro como dado (o traceback do worker se perde se subir)."""

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, item):
        i, tarefa = item
        t0 = time.perf_counter()
        try:
            r = self.fn(tarefa)
            return i, time.perf_counter() - t0, None, r
        except BaseException:                       # noqa: BLE001  (relatado e relançado no processo principal)
            return i, time.perf_counter() - t0, traceback.format_exc(), None


def _min(s):
    return f"{s / 60:.0f} min" if s >= 90 else f"{s:.0f} s"


def _ler_jsonl(caminho, tarefas, hashes):
    feitos = {}
    if caminho is None or not caminho.exists():
        return feitos
    linhas = [x for x in caminho.read_text(encoding="utf-8").splitlines() if x.strip()]
    boas = []
    for n, linha in enumerate(linhas, 1):
        try:
            reg = json.loads(linha)
        except json.JSONDecodeError:
            if n == len(linhas):
                break                               # última linha cortada por uma interrupção: a tarefa será refeita
            raise
        i = reg["i"]
        if not (0 <= i < len(tarefas)) or reg["h"] != hashes[i]:
            raise SystemExit(f"{caminho}: o registro da linha {n} (tarefa {i}) não bate com as tarefas desta execução "
                             f"(argumentos diferentes). Apague ou troque o arquivo para recomeçar; nada foi misturado.")
        feitos[i] = reg
        boas.append(linha)
    caminho.write_text("".join(x + "\n" for x in boas), encoding="utf-8")   # tira a linha cortada antes de anexar
    return feitos


def mapear(fn, tarefas, n_proc, rotulo, jsonl=None, descrever=None, batida_s=300):
    tarefas = list(tarefas)
    n = len(tarefas)
    descrever = descrever or (lambda j: repr(j)[:70])
    hashes = [_hash(j) for j in tarefas]
    caminho = Path(jsonl) if jsonl is not None else None
    feitos = _ler_jsonl(caminho, tarefas, hashes)
    resultados = {i: reg["r"] for i, reg in feitos.items()}
    tempos = [reg["t"] for reg in feitos.values()]
    pendentes = [(i, tarefas[i]) for i in range(n) if i not in feitos]
    ini = time.perf_counter()
    print(f"[{rotulo}] {n} tarefas em {n_proc} processos"
          + (f"; {len(feitos)} de {n} já feitos em {caminho}, retomando" if feitos else ""), file=sys.stderr, flush=True)
    if pendentes:
        if caminho is not None:
            caminho.parent.mkdir(parents=True, exist_ok=True)
        arq = open(caminho, "a", encoding="utf-8") if caminho is not None else None
        novos, ultimo = 0, time.perf_counter()
        try:
            with mp.get_context("spawn").Pool(min(n_proc, len(pendentes))) as pool:
                it = pool.imap_unordered(_Cronometrado(fn), pendentes, chunksize=1)
                while novos < len(pendentes):
                    try:
                        i, dt, erro, r = it.next(timeout=batida_s)
                    except mp.TimeoutError:
                        print(f"[{rotulo}] {len(resultados)}/{n} prontos, {len(pendentes) - novos} em andamento ou na fila; "
                              f"último término há {_min(time.perf_counter() - ultimo)}; decorrido {_min(time.perf_counter() - ini)}",
                              file=sys.stderr, flush=True)
                        continue
                    if erro is not None:
                        print(f"[{rotulo}] ERRO na tarefa {i} ({descrever(tarefas[i])}):\n{erro}", file=sys.stderr, flush=True)
                        raise RuntimeError(f"tarefa {i} falhou; os {len(resultados)} anteriores ficaram em {caminho}")
                    ultimo = time.perf_counter()
                    r = _ida_e_volta(r)
                    resultados[i] = r
                    tempos.append(dt)
                    novos += 1
                    if arq is not None:
                        arq.write(json.dumps(dict(i=i, h=hashes[i], t=dt, r=r), default=_padrao_json) + "\n")
                        arq.flush()
                        os.fsync(arq.fileno())
                    falta = n - len(resultados)
                    media = sum(tempos) / len(tempos)
                    print(f"[{rotulo}] [{len(resultados)}/{n}] decorrido {_min(ultimo - ini)}"
                          f" · falta ~{_min(media * falta / max(1, min(n_proc, falta)))} (estimativa)"
                          f" · {descrever(tarefas[i])} · {_min(dt)}", file=sys.stderr, flush=True)
        finally:
            if arq is not None:
                arq.close()
    print(f"[{rotulo}] concluído: {n} tarefas em {_min(time.perf_counter() - ini)}", file=sys.stderr, flush=True)
    return [resultados[i] for i in range(n)]
