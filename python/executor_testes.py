"""Executor de processos dos testes (EDR-068, TC-RUN-001).

Motivo: `subprocess.run(capture_output=True, timeout=T)` não volta no tempo-limite enquanto um NETO (o Excel via COM, por
exemplo) segura o pipe herdado do filho: o timeout mata só o filho e o `communicate()` seguinte espera o pipe fechar. Uma
rodada da suíte travou 5 h assim. Medido no diagnóstico do EDR-068: filho com neto que dorme 60 s, timeout de 3 s, o
`subprocess.run` voltou em 60,5 s.

Aqui a saída vai para arquivos temporários (nunca pipe), então nenhum neto prende a leitura; no tempo-limite a árvore
inteira é encerrada pelo PID do filho (`taskkill /PID <pid> /T /F` no Windows; `os.killpg` em POSIX). Nunca por nome de
programa.
"""
from __future__ import annotations

import datetime as dt
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

CODIGO_TEMPO = 124          # mesmo código do `timeout` do GNU coreutils: o processo foi encerrado por estourar o tempo
ESPERA_APOS_MATAR_S = 10.0


@dataclass(frozen=True)
class Execucao:
    returncode: int
    stdout: str
    stderr: str
    tempo_s: float
    estourou: bool


class Orcamento:
    """Tempo total que um script pode gastar em várias execuções (relógio monotônico, iniciado na criação)."""

    def __init__(self, total_s: float):
        self.total_s = float(total_s)
        self._inicio = time.monotonic()

    def restante(self) -> float:
        return max(0.0, self.total_s - (time.monotonic() - self._inicio))

    def cabe(self, s: float) -> bool:
        return s <= self.restante()


def orcamento_do_ambiente(padrao_s: float) -> Orcamento:
    """Orçamento de `DDS_ORCAMENTO_S` (segundos), ou `padrao_s` se a variável faltar ou não for um número positivo."""
    try:
        valor = float(os.environ.get("DDS_ORCAMENTO_S", ""))
        if valor > 0:
            return Orcamento(valor)
    except ValueError:
        pass
    return Orcamento(padrao_s)


def _matar_arvore(pid: int) -> bool:
    """Encerra a árvore do PID. Devolve False (e avisa no stderr) se o encerramento falhar; nunca levanta exceção."""
    try:
        if os.name == "nt":
            r = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            if r.returncode != 0:
                print(f"[executor] AVISO: taskkill do PID {pid} saiu com código {r.returncode}", file=sys.stderr, flush=True)
                return False
        else:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return True
    except Exception as e:  # noqa: BLE001  (não mascarar a exceção original de quem chamou)
        print(f"[executor] AVISO: não consegui encerrar a árvore do PID {pid}: {e!r}", file=sys.stderr, flush=True)
        return False


def _ler(arq) -> str:
    arq.seek(0)
    return arq.read().decode("utf-8", errors="replace")


def executar(cmd: list[str], *, cwd: Path | str, env: dict | None = None, timeout_s: float) -> Execucao:
    """Roda `cmd` e devolve a saída. Estourado `timeout_s`, encerra a árvore do processo e devolve `CODIGO_TEMPO`."""
    inicio = dt.datetime.now()
    t0 = time.monotonic()
    extra = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    estourou = False
    with tempfile.TemporaryFile() as f_out, tempfile.TemporaryFile() as f_err:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=f_out, stderr=f_err, **extra)
        try:
            try:
                codigo = p.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                estourou = True
                _matar_arvore(p.pid)
                try:
                    p.wait(timeout=ESPERA_APOS_MATAR_S)
                except subprocess.TimeoutExpired:
                    print(f"[executor] AVISO: o PID {p.pid} não encerrou {ESPERA_APOS_MATAR_S:.0f} s após o encerramento da árvore",
                          file=sys.stderr, flush=True)
                codigo = CODIGO_TEMPO
        finally:
            # KeyboardInterrupt ou outra exceção: com CREATE_NEW_PROCESS_GROUP o Ctrl+C não chega ao filho, então a árvore
            # seria deixada órfã. Sempre encerra o que sobrou (sem mascarar a exceção original).
            if p.poll() is None:
                _matar_arvore(p.pid)
        tempo = time.monotonic() - t0
        saida, erro = _ler(f_out), _ler(f_err)
    fim = dt.datetime.now()
    marca = f"[executor] início {inicio:%H:%M:%S}, fim {fim:%H:%M:%S}, {tempo:.1f} s"
    if estourou:
        marca += f"; TIMEOUT depois de {timeout_s:g} s (árvore do PID {p.pid} encerrada)"
    return Execucao(codigo, saida, (erro.rstrip("\n") + "\n" if erro else "") + marca + "\n", tempo, estourou)
