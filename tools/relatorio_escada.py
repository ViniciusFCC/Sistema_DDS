"""Relatório da escada de hipóteses do MMM em raio fixo (incremento 6, Task 7).

Monta o caso da planilha V4.2 de `excel/` (lido por nomes numa CÓPIA recalculada, como em tools/relatorio_inc4.py) e
escreve, em Markdown, o degrau 1 (MMM na configuração da planilha contra `equilibrio.analise_par`), o degrau 2 (a planilha,
as linhas de controle `planilha (acoplado, sem rotação)` e `planilha (acoplado)`, uma variante Python por vez, mais `10+9b`
e `todas`) e as sensibilidades. Sem veredito: a tolerância da escada é o EDR-065
(pendente). Nenhum número do Python vai para a planilha, que nunca é aberta para escrita (spec base 7.5).

Uso (Git Bash, depois de export UV_SYSTEM_CERTS=1):
    uv run python -X utf8 tools/relatorio_escada.py [--raio R --origem-raio TEXTO] [--ay-max-g G] [--saida ARQ] [--sobrescrever]

O raio R do skidpad é entrada "a confirmar". Este script nunca escolhe um R:
- caso da planilha sem R e sem --raio: sai com código 3 e a mensagem "informe --raio";
- --raio R exige --origem-raio TEXTO, vale só para o caso deste relatório e vai no topo ("R = <valor> m (origem: ...)").
  Num caso sem R, o --raio liga no Python a hipótese 3 (cos δ_ref), que a planilha com R vazio tem desligada: o relatório avisa.
- --ay-max-g G (padrão 2,0) é a faixa de busca da saturação, rotulada no relatório; não é dado do carro.

Saída: 0 = gravado; 1 = a referência mudou durante a execução; 2 = recusa (argumentos, arquivo existente);
3 = falta o raio; 4 = NÃO EXECUTÁVEL (sem motor de recálculo). O arquivo é gravado em UTF-8 com LF.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import math
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))   # recalculo_planilha mora em tests/

import caso_planilha as cp  # noqa: E402
import equilibrio as eq  # noqa: E402
import escada  # noqa: E402
import mmm  # noqa: E402
import recalculo_planilha as rc  # noqa: E402
from suspension_model import G  # noqa: E402

XLSX = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_2.xlsx"
TIR = RAIZ / "data" / "Hoosier_R25B_13x7_TTC_provisional.tir"
SAIDA_PADRAO = RAIZ / "docs" / "inc6" / "escada-hipoteses.md"

# Passo 1 da Task 7 (conferência do .tir combinado). Fonte: help do Adams 2024.1, "Example of PAC2002 Tire Property
# Files" (PDF pp. 92-107; a segunda listagem, pp. 105-107, confirmada na imagem das pp. 106 e 107), e
# `data/Hoosier_R25B_13x7_TTC_provisional.tir` (+ `.meta.json`). O help não traz tabela de valores padrão; só dois
# arquivos de exemplo, e nenhum deles coincide com o .tir.
NOTA_TIR = (
    "Origem dos coeficientes combinados do .tir (REX1, RBX*, RCX1, RBY*, RCY1, RVY*): não determinada. O help do Adams "
    "2024.1 (PAC2002) não traz tabela de valores padrão, só dois arquivos de exemplo (pp. 92-107 do PDF; o segundo, em "
    "pp. 105-107, tem RCX1 = RCY1 = 1, REX1 = 0, RVY1 = 0), e o .tir tem outros valores (por exemplo RBX1 = 16,0481, "
    "RBY1 = 14,6284, RCY1 = 1,04408), então não são os valores desses exemplos; por outro lado REX1 = REX2 = 0,333333, "
    "RBY2 = 10,4, RVY1 = 0,01 e RVY6 = 18 são redondos, e o `.meta.json` não diz como o ajuste foi feito (nem se estes "
    "foram ajustados ao TTC). Por isso a variante `pac2002` (hipótese 9b) fica como mais uma hipótese sem validação, e "
    "não como referência melhor que a elipse."
)
CONCLUSAO_TIR = "não determinado"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else f"indisponível ({r.stderr.strip()})"


def n(x, casas: int = 3) -> str:
    """Número com vírgula decimal; None vira '—'; texto passa como está. Zero negativo arredondado ("-0,000") sai sem o sinal."""
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    t = f"{x:.{casas}f}"
    if float(t) == 0.0:
        t = t.lstrip("-")
    return t.replace(".", ",")


def sci(x, casas: int = 2) -> str:
    if x is None:
        return "—"
    t = f"{x:.{casas}e}"
    if float(t) == 0.0:
        t = t.lstrip("-")
    return t.replace(".", ",")


def g_de(ay_ms2, casas: int = 3) -> str:
    """a_y em m/s² mostrado em g."""
    return "—" if ay_ms2 is None else f"{n(ay_ms2 / G, casas)} g"


def k_graus_por_g(k_rad_por_ms2, casas: int = 3) -> str:
    """K [rad/(m/s²)] em °/g."""
    return "—" if k_rad_por_ms2 is None else n(math.degrees(k_rad_por_ms2) * G, casas)


def folga(lim) -> str:
    """Folga em T do eixo que não satura (variantes acopladas), em N e em % da capacidade dele; '—' sem ela."""
    if lim.folga_outro_N is None:
        return "—"
    return f"{n(lim.folga_outro_N, 1)} N ({n(100.0 * lim.folga_outro_fracao, 2)} %)"


def txt(s) -> str:
    return "—" if s in (None, "") else str(s).replace("|", "/")


def tabela(cab: list[str], linhas: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(l) + " |" for l in linhas]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ap.add_argument("--sobrescrever", action="store_true", help="regrava um relatório que já existe")
    ap.add_argument("--raio", type=float, default=None, help="raio R do skidpad [m], só para o caso deste relatório")
    ap.add_argument("--origem-raio", default=None, help="de onde vem o R (obrigatório com --raio)")
    ap.add_argument("--ay-max-g", type=float, default=2.0,
                    help="faixa de busca da saturação [g] (rotulada no relatório; padrão 2,0; não é dado do carro)")
    a = ap.parse_args()
    if not (a.ay_max_g > 0.0 and math.isfinite(a.ay_max_g)):
        print("RECUSADO: --ay-max-g deve ser um número finito > 0 (g)", file=sys.stderr)
        return 2
    if a.raio is not None:
        if not (a.raio > 0.0 and math.isfinite(a.raio)):
            print("RECUSADO: --raio deve ser um número finito > 0 (m)", file=sys.stderr)
            return 2
        if not (a.origem_raio and a.origem_raio.strip()):
            print("RECUSADO: --raio exige --origem-raio TEXTO (de onde vem o valor)", file=sys.stderr)
            return 2
    elif a.origem_raio:
        print("RECUSADO: --origem-raio sem --raio", file=sys.stderr)
        return 2
    saida = a.saida if a.saida.is_absolute() else Path.cwd() / a.saida
    if saida.exists() and not a.sobrescrever:
        print(f"RECUSADO: {saida} já existe (use --sobrescrever)", file=sys.stderr)
        return 2
    if not XLSX.exists():
        print(f"RECUSADO: falta {XLSX}", file=sys.stderr)
        return 2
    motor, detalhe_motor = rc.escolher()
    if motor is None:
        print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({detalhe_motor})", file=sys.stderr)
        return 4
    print(f"Motor: {motor} ({detalhe_motor})")

    data = dt.datetime.now().isoformat(timespec="seconds")
    commit = git("rev-parse", "HEAD")
    ramo = git("rev-parse", "--abbrev-ref", "HEAD")
    sujo = bool(git("status", "--porcelain", "--untracked-files=no"))
    h_antes = sha256(XLSX)

    with tempfile.TemporaryDirectory(prefix="dds_rel_escada_", ignore_cleanup_errors=True) as t:
        tmp = Path(t)
        copia_f = tmp / "v42_formulas.xlsx"       # só leitura de fórmulas e raízes (nunca recalculada)
        copia_r = tmp / "v42_recalculada.xlsx"    # recalculada pelo motor (EDR-044)
        shutil.copyfile(XLSX, copia_f)
        shutil.copyfile(XLSX, copia_r)
        t0 = time.perf_counter()
        resumo_rec = rc.recalcular(str(copia_r), motor, timeout=900)
        t_rec = time.perf_counter() - t0
        pior_caso = cp.pior_origem_do_caso_v41(copia_f)
        try:
            caso = cp.caso_da_planilha_v41(copia_r, TIR, passo1=False)
        except ValueError as e:
            print(f"RECUSADO: o caso da planilha é inválido para o Python: {e}", file=sys.stderr)
            return 2
    if sha256(XLSX) != h_antes:
        print("ERRO: a V4.2 de referência mudou durante a execução; relatório não gravado", file=sys.stderr)
        return 1

    if a.raio is not None:
        r_planilha = caso.raio_m
        caso = replace(caso, raio_m=a.raio)
        texto_raio = f"R = {n(a.raio, 3)} m (origem: {a.origem_raio.strip()})"
        obs_raio = (f"O caso da planilha tinha R = {n(r_planilha, 3)} m e este valor foi substituído só no caso deste "
                    "relatório." if r_planilha is not None else
                    "O caso da planilha não tem R (chaves que o usam desligadas ou R vazio); o valor foi aplicado só ao "
                    "caso deste relatório. A planilha não foi alterada.")
        aviso_raio = (None if r_planilha is not None else
                      "**Aviso: a base \"planilha\" deste relatório não é a planilha de hoje.** A planilha com R vazio tem a "
                      "hipótese 3 (cos δ_ref) desligada, e no Python o raio liga o cos δ_ref na dianteira (a Fy dianteira "
                      "leva cos(L/R)). Com o `--raio` informado, a linha `planilha` já tem a hipótese 3 ligada, e o Δ da "
                      "linha `3` mede só o cos δ do trim contra esse cos δ_ref, não contra a falta dele. Preencha o R na "
                      "planilha (e ligue a chave da hipótese 3) para a base ser a da planilha.")
    elif caso.raio_m is not None:
        texto_raio = f"R = {n(caso.raio_m, 3)} m (origem: planilha V4.2, caso lido por nomes)"
        obs_raio = "R lido da planilha."
        aviso_raio = None
    else:
        print("RECUSADO (código 3): o caso da planilha não tem raio R (\"a confirmar\"); informe --raio R "
              "--origem-raio TEXTO. O script não escolhe um R.", file=sys.stderr)
        return 3

    t0 = time.perf_counter()
    d1 = escada.degrau_1(caso, a.ay_max_g)
    t_d1 = time.perf_counter() - t0
    t0 = time.perf_counter()
    d2 = escada.degrau_2(caso, a.ay_max_g)
    t_d2 = time.perf_counter() - t0
    t0 = time.perf_counter()
    sens = escada.sensibilidades(caso, a.ay_max_g)
    t_sens = time.perf_counter() - t0

    md: list[str] = []
    w = md.append
    w(texto_raio)
    w("")
    w("# Incremento 6: MMM em raio fixo e escada de hipóteses")
    w("")
    w("Gerado por `tools/relatorio_escada.py`. Não edite à mão: rode o script de novo (`--sobrescrever`).")
    w("")
    w(f"**Pior origem do caso: {pior_caso}. Geometria sintética** (não há hardpoints do CAD). O pneu é o `.tir` provisório "
      "do TTC (R25B); mola, MR, barra e RC são valores demonstrativos (T09/E03). **Nenhum número deste relatório é "
      "resultado do carro** nem validação física (Validation = NOT_VALIDATED, EDR-022). O raio R do skidpad é entrada "
      "\"a confirmar\", e o valor usado está na primeira linha. \"? A confirmar\" na pior origem quer dizer que pelo menos "
      "uma entrada do caso (ou o pneu) não tem origem registrada na planilha: a célula de origem está vazia ou fora da lista.")
    w("")
    if aviso_raio:
        w(aviso_raio)
        w("")
    w(f"Faixa de busca da saturação: 0 a {n(a.ay_max_g, 2)} g (parâmetro `--ay-max-g`, rótulo de varredura e não dado do "
      "carro; o padrão é 2,0 g). Eixo que não satura nela sai como \"não satura\" ou N/A.")
    w("")
    w("**Sem veredito: tolerância pendente (EDR-065).** As tabelas mostram diferenças e se o sinal inverte, mas nenhuma "
      "linha é classificada como \"dentro\" ou \"fora\" da tolerância; essa classificação depende do EDR-065.")
    w("")

    w("## 1. Origem")
    w("")
    w(f"- Data: {data}")
    w(f"- Commit: `{commit}` (ramo `{ramo}`" + ("; com mudanças não commitadas em arquivos versionados" if sujo else
                                                  "; árvore sem mudanças pendentes") + ")")
    w(f"- Planilha: `{XLSX.relative_to(RAIZ).as_posix()}` (SHA-256 antes `{h_antes}`; depois igual: só uma cópia temporária "
      "foi recalculada). O caso é lido com o leitor da V4.1 (`caso_da_planilha_v41`, `passo1=False`), porque a V4.2 contém "
      "todos os nomes da V4.1.")
    w(f"- Motor de recálculo da cópia: {motor} ({detalhe_motor}); {resumo_rec['total_formulas']} fórmulas, "
      f"{resumo_rec['total_errors']} erros, {n(t_rec, 1)} s")
    w(f"- Pneu: `{TIR.relative_to(RAIZ).as_posix()}` (SHA-256 `{sha256(TIR)}`), em ISO_TYDEX (EDR-039)")
    w(f"- Python {platform.python_version()}, numpy {version('numpy')}; tempos: degrau 1 {n(t_d1, 1)} s, degrau 2 "
      f"{n(t_d2, 1)} s, sensibilidades {n(t_sens, 1)} s")
    w(f"- {obs_raio}")
    w(f"- Caso: L = {n(caso.cfg.wheelbase, 3)} m, bitola dianteira {n(caso.cfg.track_front, 3)} m, "
      f"Ackermann {'desligado' if caso.ackermann_pct is None else n(caso.ackermann_pct, 1) + ' %'}, "
      f"CG lateral {n(caso.cg_lateral_m, 3)} m, "
      f"aero {'CzA/ρ' if caso.cza_m2 is not None else 'downforce fixa'}, "
      f"arrasto {'ligado (CdA, Crr)' if caso.cda_m2 is not None else 'desligado'}.")
    w("")

    w("## 2. Conferência do `.tir` (passo 1)")
    w("")
    w(f"**Conclusão: {CONCLUSAO_TIR}.**")
    w("")
    w(NOTA_TIR)
    w("")

    w("## 3. Degrau 1: MMM na configuração da planilha contra `analise_par`")
    w("")
    w("O degrau 1 é uma identidade quase por construção: os dois códigos usam a física por roda do mesmo módulo. Ele prova "
      "o reuso, não a física do MMM (adendo §5.1). Grade de α comum aos dois (401 pontos), cota da saturação = 2 × a "
      "resolução. Diferenças = MMM − `analise_par`.")
    w("")
    linhas = []
    for c in d1:
        linhas.append([c.sentido, c.veredito_mmm, c.veredito_par, sci(c.d_ay_sat_f), sci(c.d_ay_sat_r),
                       sci(c.cn_mmm), sci(c.cn_par), sci(c.resolucao_ms2), "sim" if c.ok else "não", txt(c.motivo)])
    md += tabela(["Sentido", "Veredito MMM", "Veredito par", "Δ ay_sat F [m/s²]", "Δ ay_sat R [m/s²]", "C_N MMM (Q)",
                  "C_N par", "Resolução [m/s²]", "Passa o critério numérico", "Motivo"], linhas)
    w("")
    if all(c.veredito_mmm == eq.NA and c.veredito_par == eq.NA for c in d1):
        w(f"Os dois lados dão N/A nos dois sentidos (nenhum eixo satura até {n(a.ay_max_g, 2)} g neste caso e neste R): o \"sim\" vale "
          "para a coincidência do N/A, e a identidade das saturações e do C_N não foi exercitada neste caso.")
        w("")
    w("\"Passa o critério numérico\" é o critério de identidade do degrau 1 (mesmo veredito, saturações dentro da cota, C_N "
      "dentro da folga equivalente). Não é o veredito de tolerância do degrau 2 (EDR-065).")
    w("")

    w("## 4. Degrau 2: uma variante Python por vez a partir da planilha")
    w("")
    w("Uma linha por variante. Hipóteses numeradas como na spec (1+2 = α cinemático e Ackermann; 3 = cos δ no trim; 7 = "
      "os dois sentidos; 9a = Fx exigido por balanço; 9b = PAC2002 combinado; 10 = diferencial travado; 11 = "
      "transferência longitudinal em regime; `10+9b` = travado com o PAC2002 combinado). As linhas com a hipótese 7 "
      "(`7` e `todas`) mostram o pior sentido. K em °/g; K e o stability index valem em 0,05 g. O stability index (SI) "
      "sai em 1/g, com o sinal do C_N estabilizante: positivo = estabilizante (carro estável, subesterço); o Milliken usa "
      "o C_N do ISO, de sinal oposto.")
    w("")
    w("**Linhas de controle.** As variantes Python (menos a `7`) são resolvidas por um Newton 2-D em (β, δ) com a "
      "rotação a_y = A·cos β e a_x = −A·sen β; a `planilha` usa o trim desacoplado, com a_y = A. Duas linhas de controle "
      "resolvem as hipóteses da planilha pelo Newton, sem mudar nenhuma hipótese, e separam os dois efeitos (coluna "
      "\"Δ contra\"):")
    w("")
    w("- `planilha (acoplado, sem rotação)`: o Newton com a_y = A e a_x = 0, as mesmas da planilha. O Δ contra a "
      "`planilha` é só o viés do método.")
    w("- `planilha (acoplado)`: o Newton com a rotação. O Δ contra a linha sem rotação é o efeito da simplificação "
      "a_y = A da planilha (a rotação não tem número de hipótese). A soma dos dois Δ é o Δ dela contra a `planilha`.")
    w("")
    w("Δ e \"Inverte\" das linhas acopladas são contra a `planilha (acoplado)`, para que o número de cada linha seja o "
      "efeito da hipótese, e não o do método nem o da rotação; o Δ da `7` (desacoplada) é contra a `planilha`.")
    w("")
    w("**Folga do outro eixo em T** (só nas linhas acopladas com T): acima de T não existe trim, então o eixo que não "
      "satura fica sem ay_sat (\"—\"), e a coluna mostra a folga dele em T, nos eixos do carro: a capacidade dele em T "
      "menos a força que ele faz no trim, em N e em % da capacidade. É a mesma folga que dá o Q. Nas linhas desacopladas os "
      "dois ay_sat existem e a coluna fica \"—\".")
    w("")
    if any(ln.motivo for ln in d2):
        w("Linhas cuja hipótese está desligada no caso (a chave da planilha está desligada) ainda são calculadas, e a "
          "hipótese desligada não muda nada nelas: uma linha de uma hipótese só coincide com a referência por construção; "
          "na `todas`, só as hipóteses ligadas contam no Δ. O motivo vem na lista abaixo da tabela.")
        w("")
    linhas = []
    for ln in d2:
        lim = ln.limite
        linhas.append([f"`{ln.nome}`", ", ".join(map(str, ln.hipoteses)) or "—", lim.veredito, txt(lim.eixo_satura),
                       g_de(lim.ay_sat_f, 4), g_de(lim.ay_sat_r, 4), g_de(lim.ay_t_ms2, 4), folga(lim),
                       n(lim.cn_estabilizante_q, 4), k_graus_por_g(lim.k_rad_por_ms2), txt(ln.pior_sentido),
                       g_de(ln.d_ay_t, 6), n(ln.d_cn_estabilizante_q, 4),
                       k_graus_por_g(ln.d_k) if ln.d_k is not None else "—", f"`{ln.referencia}`", ln.inverte,
                       "—" if lim.stability_index is None else n(lim.stability_index * G, 4)])
    md += tabela(["Linha", "Hipóteses", "Veredito", "Eixo que satura", "ay_sat F", "ay_sat R", "T",
                  "Folga do outro eixo em T", "C_N estab. (Q)",
                  "K [°/g]", "Pior sentido", "Δ T", "Δ C_N", "Δ K [°/g]", "Δ contra", "Inverte", "SI [1/g]"], linhas)
    w("")
    motivos = [(ln.nome, ln.motivo, ln.limite.motivo, ln.limite.motivo_sat, ln.limite.limitacoes) for ln in d2]
    if any(d or m or s or l for _, d, m, s, l in motivos):
        w("Motivos e avisos por linha (onde existem):")
        w("")
        for nome, d, m, s, l in motivos:
            partes = [p for p in (d, m, s, "; ".join(l) if l else None) if p]
            if partes:
                w(f"- `{nome}`: {' | '.join(partes)}")
        w("")

    w("## 5. Sensibilidades")
    w("")
    w("Diferença central de ± um passo, na unidade da coluna. Valores em torno da planilha, sem faixa afirmada. "
      "`h_cp` liga com a transferência em regime; `h_cg` é por 10 mm de altura do CG (decisão 4 do plano: o jacking não "
      "muda a soma das Fz, e o camber já está em `ganho_camber`). A sensibilidade de `h_cp` é em torno de h_cp = 0: sem "
      "dado de altura do centro de pressão, `h_cp_m = None` equivale a h_cp = 0 (a parcela D·h_cp/L fica fora), e a "
      "tabela mostra o efeito de subir 10 mm a partir daí, não de uma altura medida.")
    w("")
    linhas = [[f"`{s['parametro']}`", s["unidade"], g_de(s["d_ay_t"], 5), n(s["d_cn_estabilizante_q"], 5),
               k_graus_por_g(s["d_k"], 4), txt(s["veredito_menos"]), txt(s["veredito_mais"]), txt(s["motivo"])]
              for s in sens]
    md += tabela(["Parâmetro", "Unidade", "∂T", "∂C_N estab. (Q)", "∂K [°/g]", "Veredito −", "Veredito +", "Motivo"], linhas)
    w("")

    # --- Achados do adendo §7, com os números medidos nas linhas 1+2 e 9a ---
    por_nome = {ln.nome: ln for ln in d2}
    l12, l9a = por_nome["1+2"], por_nome["9a"]
    esperado_dalfa = caso.cfg.wheelbase * caso.cfg.track_front / caso.raio_m ** 2   # L·t/R² [rad]
    w("## 6. Achados do adendo §7 sobre fórmulas da planilha (nenhuma mudança agora)")
    w("")
    w("Estas são duas simplificações físicas da planilha, conferidas no código. O incremento 6 não mexe nelas; "
      "qualquer mudança exige EDR e aprovação explícita do usuário. Aqui aparece só o efeito medido no degrau 2.")
    w("")
    w(f"1. **Ackermann (hipótese 2, SUS-414).** `deriva_ackermann` supõe a mesma direção de velocidade nas duas "
      f"dianteiras; na cinemática real as direções diferem de ≈ L·t/R², que é o próprio Ackermann ideal. Com L = "
      f"{n(caso.cfg.wheelbase, 3)} m, t = {n(caso.cfg.track_front, 3)} m e R = {n(caso.raio_m, 3)} m, L·t/R² = "
      f"{n(math.degrees(esperado_dalfa), 3)}° entre as rodas (estimativa analítica, não medida no solver). Efeito medido "
      f"na linha `1+2`: ΔT = {g_de(l12.d_ay_t, 4)}, ΔC_N = {n(l12.d_cn_estabilizante_q, 4)}, ΔK = "
      f"{k_graus_por_g(l12.d_k, 4)} °/g, veredito {l12.limite.veredito} (inverte: {l12.inverte}).")
    w(f"2. **Fx exigido (hipótese 9, EDR-057).** `fx_exigido_traseira` usa |F_yf|·tan(L/R) ≈ m·A·b/R, que depende de R e "
      f"não da deriva; o balanço completo é F_yf·sen δ − m·A·sen β (em primeira ordem, F_yf·|α_F| + F_yr·|α_R|, o arrasto "
      f"induzido). Efeito medido na linha `9a`: "
      f"ΔT = {g_de(l9a.d_ay_t, 4)}, ΔC_N = {n(l9a.d_cn_estabilizante_q, 4)}, ΔK = {k_graus_por_g(l9a.d_k, 4)} °/g, "
      f"veredito {l9a.limite.veredito} (inverte: {l9a.inverte}).")
    w("")
    if l12.d_ay_t is None or l9a.d_ay_t is None:
        w(f"Onde ΔT e ΔC_N aparecem como \"—\", a linha (ou a referência dela, coluna \"Δ contra\") não tem T: com este "
          f"caso e este R nenhum eixo satura até {n(a.ay_max_g, 2)} g, então só o K tem número. O efeito no limite não foi "
          f"medido.")
        w("")
    w("Nada foi ajustado para bater. Cada efeito vale para este R e para o caso sintético, não para o carro.")
    w("")

    w("## 7. Limitações")
    w("")
    w("- Geometria sintética, pneu provisório do TTC e dados demonstrativos: os números mostram o tamanho relativo de cada "
      "hipótese neste caso, não o do carro.")
    w("- A tolerância da escada (EDR-065) está pendente; nada aqui é \"dentro\" nem \"fora\".")
    w("- O raio R é entrada a confirmar; os resultados dependem dele (ver a primeira linha).")
    w("- Passou nos critérios do degrau 1 = os dois códigos concordam; não é validação física.")
    w("- O arrasto entra inteiro no eixo x do carro; a componente lateral D·sen β (a velocidade faz o ângulo β com o carro) "
      "fica fora do balanço lateral. É de 2ª ordem em β e D é uma fração pequena de m·A.")
    w("- A precisão de T nas linhas acopladas é da ordem da resolução do limite (0,01 m/s²), e não a da bisseção: a dobra "
      "do Newton pode cair até essa distância antes do pico do eixo.")
    w("- A cota do degrau 1 (2 × a resolução) é empírica: a resolução que o `analise_par` declara subestima o erro de "
      "interpolação dele (EDR-064, item 2.9).")
    w("")

    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(f"relatório: {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
