"""
Empacotador do posicionador da atuação para Windows x64 (EDR-076): pacote PORTÁTIL, sem instalação — Python embutido da
python.org, rodas `win_amd64` das dependências e lançadores `.bat`. Não é um `.exe` único (PyInstaller não gera Windows a
partir de Linux, e o OpenCascade + vtk passam de 600 MB descompactados).

Uso (raiz do repositório; precisa de `uv`, `git` e rede):
    uv run python -X utf8 tools/empacotar_windows.py [--saida build/pacote_windows] [--python 3.13.17]

Gera `<saida>/posicionador_T11_win64/` e `<saida>/posicionador_T11_win64_<commit>.zip` (+ `.sha256`). O conteúdo de código e de
dados é o do `HEAD` (git archive), nunca da árvore de trabalho, e o commit fica gravado em `VERSAO.txt`.
Montado em qualquer sistema, mas executável SÓ em Windows 10/11 x64: de fora do Windows não há como rodar o pacote, então o
passo de conferência daqui (opção `--conferir PYTHON`) roda o MESMO código-fonte empacotado com um Python do sistema atual e
confirma que ele não depende de nenhum arquivo fora do pacote. A primeira execução de `verificar_instalacao.bat` no Windows é
a prova de que as DLLs carregam.
"""
import argparse
import hashlib
import io
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOME = "posicionador_T11_win64"
# numpy, scipy e cadquery-ocp iguais ao uv.lock de 2026-11-23; matplotlib é opcional (só as figuras)
PINS = ["numpy==2.5.4", "scipy==1.18.1", "cadquery-ocp==8.0.1.1.0", "matplotlib==3.11.2"]
FONTES = ["python/posicionador", "python/kinematics_model.py", "python/hardpoints.py", "tools/posicionar_atuacao.py",
          "data/posicionador", "data/cad", "docs/posicionador/README.md"]

BAT_LANCADOR = r"""@echo off
chcp 65001 >nul
set "AQUI=%~dp0"
"%AQUI%runtime\python\python.exe" -X utf8 "%AQUI%tools\posicionar_atuacao.py" %*
exit /b %errorlevel%
"""

BAT_VERIFICAR = r"""@echo off
chcp 65001 >nul
set "AQUI=%~dp0"
"%AQUI%runtime\python\python.exe" -X utf8 "%AQUI%verificar_instalacao.py"
echo.
pause
"""

BAT_V20 = r"""@echo off
chcp 65001 >nul
set "AQUI=%~dp0"
"%AQUI%runtime\python\python.exe" -X utf8 "%AQUI%tools\posicionar_atuacao.py" --avaliar-v20 --saida "%AQUI%resultados\v20"
echo.
echo Relatorio em: %AQUI%resultados\v20\relatorio.md
pause
"""

BAT_BUSCA = r"""@echo off
chcp 65001 >nul
set "AQUI=%~dp0"
if "%~1"=="" (
  echo Uso: buscar_com_step.bat ARQUIVO.step [amostras]
  echo Ou arraste o arquivo .step em cima deste arquivo.
  pause
  exit /b 2
)
set "AMOSTRAS=%~2"
if "%AMOSTRAS%"=="" set "AMOSTRAS=200"
"%AQUI%runtime\python\python.exe" -X utf8 "%AQUI%tools\posicionar_atuacao.py" --step "%~1" --saida "%AQUI%resultados\busca" --amostras %AMOSTRAS%
echo.
echo Relatorio em: %AQUI%resultados\busca\relatorio.md
pause
"""

LEIA_ME = """POSICIONADOR DA ATUAÇÃO DIANTEIRA — T11 (Equipe Tupã) — pacote portátil para Windows
=====================================================================================
Versão: commit {commit} ({data}). EDR-076, fase 1. Validation = NOT_VALIDATED.

O QUE É
  Diz onde push rod, rocker e amortecedor da dianteira PODEM ficar sem colidir com as peças do CAD (lidas de um .step) e com
  os gabaritos do regulamento (FSAE Rules 2027 V1.0), cumprindo as metas da equipe (MR, curso do amortecedor). Não dita onde
  vão os tubos. Não aprova nada: o melhor veredito possível é CONDICIONAL, e o relatório diz o que não foi verificado.
  A cinemática ainda não foi comparada com o OptimumKinematics (REFERENCE): VERIFIED não é validado.

REQUISITOS
  Windows 10 ou 11, 64 bits. Não precisa instalar Python nem nada: tudo está na pasta `runtime`. Descompacte o zip inteiro num
  caminho curto (ex.: C:\\posicionador). O pacote é grande (cerca de 700 MB descompactado) porque inclui o OpenCascade, que lê o .step.
  Se o antivírus reclamar do python.exe da pasta `runtime`, ele é o Python oficial (python.org, versão 3.13.17, pacote
  "embeddable"); libere a pasta.

PRIMEIRO PASSO
  Dê dois cliques em `verificar_instalacao.bat`. Ele confere as bibliotecas, lê o STEP de exemplo (31 corpos) e avalia a v20.
  Esperado: "RESULTADO: TUDO OK". Se aparecer FALHOU, mande o arquivo `verificar_instalacao.log` (fica nesta pasta).

COMO USAR
  1. `avaliar_v20.bat`  — avalia a v20 (a solução do script do Murilo) com a ferramenta; leva segundos.
     Resultado esperado: INVIAVEL (variação de MR de 6,2 % contra o limite de 4 %, entre outros). Relatório: resultados\\v20\\relatorio.md
  2. `buscar_com_step.bat ARQUIVO.step [amostras]` — busca posições (padrão 200 amostras; leva cerca de 11 minutos).
     Pode arrastar o .step em cima do arquivo. Relatório e candidatos: resultados\\busca\\.
  3. Uso avançado: `posicionar_atuacao.bat --help` lista todas as opções (--semente, --refinos, --caixa, --config, --hardpoints).
     Cada execução sobrescreve a pasta de saída: use outra pasta (--saida) para guardar resultados antigos.

O QUE SAI (em resultados\\...)
  relatorio.md      veredito, cada restrição com folga, origem e fonte do limite, itens a confirmar, avisos do STEP, hash do STEP
  resultado.json    o mesmo em dados (SI)
  candidato_NN.csv  hardpoints de cada candidato (schema V2.0, Status PROVISIONAL) + .meta.json; candidatos.csv resume
  Se não houver candidato, o relatório traz o diagnóstico (quais restrições brigam) e o melhor candidato encontrado.

LIMITES ATUAIS (leia o relatório de cada execução)
  - Itens "A_CONFIRMAR" na configuração (data\\posicionador\\config_T11.json): curso da cremalheira, margem de curso do amortecedor,
    face da AIP, início e fim do gabarito T.1.2 (coluna e pedais) e faixa vertical do gabarito. Enquanto estiverem sem valor, essas
    verificações saem NAO_VERIFICAVEL e o resultado não passa de CONDICIONAL. Para preencher um, edite o valor, a origem e a fonte no
    JSON; não invente: valor sem fonte fica A_CONFIRMAR.
  - Manga, freio, pinça, pneu, coluna de direção e pedais não são modelados nesta fase: aparecem como NAO_VERIFICAVEL.
  - O STEP de exemplo (data\\cad\\T11_chassi_2026-11-17.step) não tem as esferas de referência: a ferramenta usa a transformação
    STEP para carro da configuração (HIPOTESE). Para o formato certo do STEP (prefixos CHASSI_, FIXO_, RODA_FE_, BANDEJA_FE_,
    DIR_, REF_, HP_, IGNORAR_ e esferas REF_ORIGEM, REF_X, REF_Y), veja o documento "Exportação do CAD (.step) para o
    posicionador da atuação" e docs\\posicionador\\README.md.
  - Resultado com o STEP de exemplo e 200 amostras (2026-11-23): nenhum candidato viável; a variação de MR ≤ 4 % é a restrição que
    mais falha. É amostragem curta: não prova que não existe posição viável.
"""


def rodar(cmd, **kw):
    r = subprocess.run(cmd, cwd=RAIZ, **kw)
    if r.returncode:
        raise SystemExit(f"falhou ({r.returncode}): {' '.join(map(str, cmd))}")
    return r


def baixar(url, destino):
    try:
        urllib.request.urlretrieve(url, destino)
    except Exception:                                    # noqa: BLE001  (proxy/certificado: tenta o curl)
        rodar(["curl", "-sSfL", "-m", "600", "-o", str(destino), url])


def gravar(caminho, texto, crlf=True):
    t = texto.replace("\r\n", "\n")
    caminho.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))


def montar(saida, versao_py):
    pasta = saida / NOME
    if pasta.exists():
        shutil.rmtree(pasta)
    (pasta / "runtime" / "python").mkdir(parents=True)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    data = subprocess.run(["git", "log", "-1", "--format=%cd", "--date=short"], cwd=RAIZ, capture_output=True,
                          text=True).stdout.strip()
    # 1. Python embutido
    emb = saida / f"python-{versao_py}-embed-amd64.zip"
    if not emb.exists():
        baixar(f"https://www.python.org/ftp/python/{versao_py}/python-{versao_py}-embed-amd64.zip", emb)
    zipfile.ZipFile(emb).extractall(pasta / "runtime" / "python")
    # 2. dependências (rodas win_amd64, resolvidas pelo uv de qualquer sistema)
    sp = pasta / "runtime" / "python" / "Lib" / "site-packages"
    rodar([shutil.which("uv") or "uv", "pip", "install", "--target", str(sp), "--python-platform", "windows",
           "--python-version", ".".join(versao_py.split(".")[:2]), "--only-binary", ":all:", *PINS])
    for pth in (pasta / "runtime" / "python").glob("python3*._pth"):
        zip_py = pth.read_text(encoding="utf-8").splitlines()[0].strip()
        gravar(pth, f"{zip_py}\n.\nLib\\site-packages\nimport site\n")
    # 3. código e dados do HEAD
    tmp = subprocess.run(["git", "archive", "--format=zip", "HEAD", *FONTES], cwd=RAIZ, capture_output=True, check=True).stdout
    zipfile.ZipFile(io.BytesIO(tmp)).extractall(pasta)
    shutil.copy(RAIZ / "tools" / "pacote_windows_verificar.py", pasta / "verificar_instalacao.py")
    # 4. lançadores e textos
    gravar(pasta / "posicionar_atuacao.bat", BAT_LANCADOR)
    gravar(pasta / "verificar_instalacao.bat", BAT_VERIFICAR)
    gravar(pasta / "avaliar_v20.bat", BAT_V20)
    gravar(pasta / "buscar_com_step.bat", BAT_BUSCA)
    gravar(pasta / "LEIA-ME.txt", LEIA_ME.format(commit=commit, data=data))
    gravar(pasta / "VERSAO.txt", f"commit {commit} ({data})\nPython embutido {versao_py} (python.org, amd64)\n" +
           "\n".join(PINS) + "\n(+ dependências resolvidas pelo uv: vtk, pillow, kiwisolver, fonttools etc.)\n")
    (pasta / "resultados").mkdir()
    return pasta, commit


def zipar(pasta, saida, commit):
    alvo = saida / f"{NOME}_{commit}.zip"
    with zipfile.ZipFile(alvo, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in sorted(pasta.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, Path(NOME) / f.relative_to(pasta))
    h = hashlib.sha256()
    with open(alvo, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    (saida / f"{alvo.name}.sha256").write_text(f"{h.hexdigest()}  {alvo.name}\n", encoding="utf-8")
    return alvo, h.hexdigest()


def conferir(pasta, python):
    """Roda o autoteste do pacote com um Python do sistema atual (não é Windows): só prova o fechamento do código."""
    r = subprocess.run([python, "-X", "utf8", str(pasta / "verificar_instalacao.py")], cwd=pasta, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.returncode:
        print(r.stderr[-800:], file=sys.stderr)
        raise SystemExit("conferência do fechamento do código falhou")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--saida", default=str(RAIZ / "build" / "pacote_windows"))
    ap.add_argument("--python", default="3.13.17", help="versão do Python embutido (3.13.x com pacote 'embed-amd64')")
    ap.add_argument("--conferir", metavar="PYTHON", help="roda o autoteste do pacote com este Python (fechamento do código)")
    a = ap.parse_args()
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    pasta, commit = montar(saida, a.python)
    if a.conferir:
        conferir(pasta, a.conferir)
        shutil.rmtree(pasta / "resultados")           # o autoteste gravou o log e a saída da v20 aqui
        (pasta / "resultados").mkdir()
        (pasta / "verificar_instalacao.log").unlink(missing_ok=True)
    alvo, h = zipar(pasta, saida, commit)
    print(f"{alvo} ({alvo.stat().st_size / 1e6:.0f} MB) sha256 {h}")


if __name__ == "__main__":
    main()
