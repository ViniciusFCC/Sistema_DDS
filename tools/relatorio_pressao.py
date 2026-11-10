"""Relatório do subprojeto A (pneu com variação de pressão): A1-pneu, A1-carro, A1-escolha e A2 (EDR-071).

Compara os quatro perfis R25B do TTC Round 6 (8, 10, 12 e 14 psi) no pneu e no carro da planilha V4.1, apoia a escolha
da pressão com uma banda heurística e uma regra simétrica, e mostra a pressão contínua (A2) por interpolação rotulada
das saídas. Nada entra na planilha, e nada de `build/` é versionado.

Uso (Git Bash, depois de export UV_SYSTEM_CERTS=1):
    uv run --with matplotlib python -X utf8 tools/relatorio_pressao.py [--planilha ARQ] [--saida ARQ] [--sobrescrever]

Regras:
- A planilha só é COPIADA para uma pasta temporária; só a cópia é recalculada (EDR-044). O SHA-256 da original é
  conferido antes e depois; se mudar, o relatório não é gravado.
- O .tir do caso é o de 12 psi da família real (os coeficientes da 10_TIRE por cima, como em caso_planilha). Os .tir
  do TTC ficam fora do Git (DDS_TTC_DIR ou references/ttc/ da raiz do repositório principal).
- Sem ranking: as tabelas seguem a ordem das pressões da família, nunca a ordem do valor.
- matplotlib é opcional: sem ele o .md sai sem os PNG, com o aviso, e o código continua 0.

Saída: 0 = gravado; 1 = a planilha mudou durante a execução; 2 = recusa; 3 = NÃO EXECUTÁVEL (sem motor de
recálculo ou sem os .tir do TTC).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from importlib.metadata import version
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tests"))   # recalculo_planilha mora em tests/

import openpyxl  # noqa: E402

import caso_planilha as cp  # noqa: E402
import comparacao_pressao as cmp  # noqa: E402
import equilibrio as eq  # noqa: E402
import recalculo_planilha as rc  # noqa: E402
import suspension_model as sm  # noqa: E402
import tire_model_static as ts  # noqa: E402
import tire_pressure as tp  # noqa: E402

PLANILHA = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_1.xlsx"
VARREDURA = RAIZ / "data" / "varredura_pneu_exploratoria.json"
SAIDA_PADRAO = RAIZ / "build" / "relatorio-pressao.md"
SUBDIR = Path("references") / "ttc" / "round6_hoosier_r25b_20p5x7_13_7in"
# A grade da 17_EQUILIBRIO da V4.1 (a mesma do relatorio_inc4); fator_neutro 1.0 como na V4.1.
GRADE = {"ay_max_g": 2.0, "passo_g": 0.05, "n_alfa": 25, "fator_neutro": 1.0}
N_GRADE_FZ = 8
PRESSOES_A2 = (9.0, 11.0, 13.0)
SEM_MATPLOTLIB = ("PNG não gerado: rode com `uv run --with matplotlib python -X utf8 "
                  "tools/relatorio_pressao.py`")


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
    """Número com vírgula decimal; None vira '—'; texto passa como está."""
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    return f"{x:.{casas}f}".replace(".", ",")


def pct(x, casas: int = 2) -> str:
    return "—" if x is None else f"{100.0 * x:.{casas}f} %".replace(".", ",")


def ps(p: float) -> str:
    """Pressão nominal (as chaves reais são 7.999992 etc.)."""
    return f"{p:.0f}"


def graus(rad: float, casas: int = 2) -> str:
    return n(math.degrees(rad), casas) + "°"


def achar_ttc() -> Path | None:
    """DDS_TTC_DIR (se definido, só ele) ou references/ttc/ da raiz deste checkout ou do repositório principal."""
    def ok(c: Path) -> bool:
        return c.is_dir() and len(list(c.glob("*PAC02_UM4.tir"))) >= 4
    env = os.environ.get("DDS_TTC_DIR")
    if env:
        return Path(env) if ok(Path(env)) else None
    candidatos = [RAIZ / SUBDIR]
    if len(RAIZ.parents) >= 3 and RAIZ.parent.name == "worktrees":
        candidatos.append(RAIZ.parents[2] / SUBDIR)
    return next((c for c in candidatos if ok(c)), None)


def tabela(cab: list[str], linhas: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += ["| " + " | ".join(str(c) for c in ln) + " |" for ln in linhas]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--planilha", type=Path, default=PLANILHA)
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    ap.add_argument("--sobrescrever", action="store_true", help="regrava um relatório que já existe")
    a = ap.parse_args()
    saida = a.saida if a.saida.is_absolute() else Path.cwd() / a.saida
    planilha = a.planilha if a.planilha.is_absolute() else Path.cwd() / a.planilha
    if saida.exists() and not a.sobrescrever:
        print(f"RECUSADO: {saida} já existe (use --sobrescrever)", file=sys.stderr)
        return 2
    if not planilha.exists():
        print(f"RECUSADO: falta {planilha}", file=sys.stderr)
        return 2
    ttc = achar_ttc()
    if ttc is None:
        print("NÃO EXECUTÁVEL: .tir do TTC Round 6 não encontrados (defina DDS_TTC_DIR ou coloque em "
              "references/ttc/)", file=sys.stderr)
        return 3
    motor, detalhe_motor = rc.escolher()
    if motor is None:
        print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({detalhe_motor})", file=sys.stderr)
        return 3
    print(f"Motor: {motor} ({detalhe_motor})")
    t_ini = time.perf_counter()

    data = dt.datetime.now().isoformat(timespec="seconds")
    commit, ramo = git("rev-parse", "HEAD"), git("rev-parse", "--abbrev-ref", "HEAD")
    sujo = bool(git("status", "--porcelain", "--untracked-files=normal"))
    h_antes = sha256(planilha)
    var = json.loads(VARREDURA.read_text(encoding="utf-8"))
    fatores = var["fatores"]

    fam = ts.load_profile_family(ttc, source_axis_system="ISO_TYDEX")
    pressoes = fam.pressures_psi
    p12 = fam.at_pressure(12.0)
    tir = p12.source_path
    teto = tp.teto_comum_fz(fam)

    # --- planilha: cópia recalculada, caso e KT ---
    with tempfile.TemporaryDirectory(prefix="dds_rel_pressao_", ignore_cleanup_errors=True) as t:
        copia = Path(t) / "v41_recalculada.xlsx"
        shutil.copyfile(planilha, copia)
        t0 = time.perf_counter()
        resumo_rec = rc.recalcular(str(copia), motor, timeout=900)
        t_rec = time.perf_counter() - t0
        rot_passo1 = "K com o roll steer do caso (passo 1)"
        try:
            caso = cp.caso_da_planilha_v41(copia, tir, passo1=True)
        except ValueError as e:
            caso = cp.caso_da_planilha_v41(copia, tir, passo1=False)
            rot_passo1 = f"K sem roll steer (roll steer sem dado na planilha): {e}"
        wb = openpyxl.load_workbook(copia, data_only=True)
        try:
            kt = {}
            for eixo, chave in (("F", "KTF"), ("R", "KTR")):
                aba, cel = cp.endereco_da_entrada(wb, chave)
                kt[eixo] = float(wb[aba][cel].value)
        finally:
            wb.close()
    if sha256(planilha) != h_antes:
        print("ERRO: a planilha de referência mudou durante a execução; relatório não gravado", file=sys.stderr)
        return 1

    # --- cargas de operação do caso ---
    if rot_passo1.startswith("K com o roll steer") and not any(caso.roll_steer.values()):
        rot_passo1 = "K com roll steer 0 (roll steer sem dado na planilha; passo 1 lido sem erro)"
    fz_a0 = eq.cargas(caso, 0.0)
    fz_estatica_eixo = {"F": 0.5 * (fz_a0["FL"] + fz_a0["FR"]), "R": 0.5 * (fz_a0["RL"] + fz_a0["RR"])}
    cam_eixo = {"F": 0.5 * (caso.camber_estatico_rad["FL"] + caso.camber_estatico_rad["FR"]),
                "R": 0.5 * (caso.camber_estatico_rad["RL"] + caso.camber_estatico_rad["RR"])}

    # --- A1-carro (a parte demorada) ---
    t0 = time.perf_counter()
    res_carro = cmp.comparar_carro(caso, fam, kt_caso_n_m=kt, fatores_lambda=fatores, **GRADE)
    t_carro = time.perf_counter() - t0
    r12a = next(r for r in res_carro if r.variante_kt == "a" and abs(r.pressao_psi - 12.0) < ts.PRESSURE_TOLERANCE_PSI)

    # Fz de operação: 4 rodas em a_y = 0 e no a_y limite do 12 psi (variante a); a roda externa pode passar do teto.
    origem_fz: dict[float, list[str]] = {}
    brutas: list[float] = []
    for c in eq.CANTOS:
        brutas.append(fz_a0[c])
    ay_lim12 = r12a.ay_lim_ms2
    fz_lim: dict | None = None
    if ay_lim12 is not None:
        c12 = eq.espelhar(r12a.caso) if r12a.sentido_pior == "direita" else r12a.caso
        fz_lim = eq.cargas(c12, ay_lim12)
        brutas += [fz_lim[c] for c in eq.CANTOS]
    grade_bruta = tp.grade_fz(fam, brutas, n=N_GRADE_FZ)
    # o rótulo de cada Fz de operação (qual roda, em que a_y); a grade guarda só o valor avaliado
    nomes_op = [(f"{c} em a_y = 0", fz_a0[c]) for c in eq.CANTOS]
    if fz_lim is not None:
        nomes_op += [(f"{c} em a_y limite do 12 psi", fz_lim[c]) for c in eq.CANTOS]
    piso = max(float(p.parameters["FZMIN"]) for p in fam.profiles.values())
    for nome, fz in nomes_op:
        uso = min(max(fz, piso), teto)
        sufixo = "" if uso == fz else f" ({fz:.0f} N, avaliada em {uso:.0f} N)"
        origem_fz.setdefault(round(uso, 3), []).append(nome + sufixo)
    # grade final: pontos igualmente espaçados + operação deduplicada pelo valor avaliado
    pontos_fz: list[tuple[float, str]] = []
    for fz, rot in grade_bruta[:N_GRADE_FZ]:
        pontos_fz.append((fz, "grade"))
    vistos = {round(f, 3) for f, _ in pontos_fz}
    for k in sorted(origem_fz):
        if k in vistos:
            pontos_fz = [(f, r + "; " + "; ".join(origem_fz[k]) if round(f, 3) == k else r) for f, r in pontos_fz]
        else:
            pontos_fz.append((k, "; ".join(origem_fz[k])))
            vistos.add(k)
    pontos_fz.sort()
    gamas = sorted({0.0, cam_eixo["F"], cam_eixo["R"]})

    # --- A1-pneu: métricas por (pressão, Fz, γ) ---
    t0 = time.perf_counter()
    met: dict[tuple[float, float, float], tp.MetricasPneu] = {}
    for q in pressoes:
        prof = fam.profiles[q]
        av, fx = tp.avaliador_perfil(prof), tp.faixa_do_perfil(prof)
        for fz, _ in pontos_fz:
            for g in gamas:
                met[(q, fz, g)] = tp.metricas_pneu(av, fx, fz_n=fz, camber_rad=g)
    t_met = time.perf_counter() - t0

    # --- A1-escolha ---
    esc_ay = cmp.escolher_pressao("a_y_lim", resultados_carro=res_carro)
    esc_ca = cmp.escolher_pressao("C_alpha_operacao", family=fam, fz_estatica_eixo_n=fz_estatica_eixo,
                                  camber_eixo_rad=cam_eixo)

    # --- A2 ---
    fz_a2, g_a2 = min(fz_estatica_eixo["F"], teto), cam_eixo["F"]
    a2 = {}
    for q in PRESSOES_A2:
        p_lo, p_hi, _ = tp.vizinhos(fam, q)
        av_i = tp.avaliador_interpolado(fam, q)
        faixa = tp.faixa_comum((fam.profiles[p_lo], fam.profiles[p_hi]))
        try:
            m = tp.metricas_pneu(av_i, faixa, fz_n=fz_a2, camber_rad=g_a2)
            inter = {s: tp.intervalo_pico_mu_y(fam, q, fz_n=fz_a2, camber_rad=g_a2, sinal=s) for s in (1, -1)}
            borda_viz = {pq: [tp.pico_mu_y(tp.avaliador_perfil(fam.profiles[pq]), faixa, fz_n=fz_a2,
                                           camber_rad=g_a2, sinal=s).borda for s in (1, -1)]
                         for pq in (p_lo, p_hi)}
            alfa_pico = m.mu_y_pos.argumento
            pontos = sorted({0.0, 0.5 * alfa_pico, alfa_pico, min(faixa.alfa_max_rad, 1.5 * alfa_pico), faixa.alfa_max_rad})
            diag = []
            for al in pontos:   # diagnostico=True só em poucos pontos isolados (0,4 s por chamada)
                r = tp.evaluate_interpolated(fam, q, fz_n=fz_a2, alpha_rad=al, camber_rad=g_a2, kappa=0.0,
                                             vx_mps=11.176, diagnostico=True)
                diag.append((al, r))
            a2[q] = {"viz": (p_lo, p_hi), "faixa": faixa, "m": m, "inter": inter, "borda_viz": borda_viz,
                     "diag": diag, "erro": None}
        except ts.StaticTireError as e:
            a2[q] = {"viz": (p_lo, p_hi), "erro": str(e)}

    # --- Diferenças fora de λ (o ds do caso vem da 10_TIRE) ---
    difs = cmp.diferencas_fora_de_lambda(caso.ds, p12, teto)

    # =============================== relatório ===============================
    md: list[str] = []
    w = md.append
    w("# Pneu com variação de pressão (R25B, TTC Round 6): A1, A1-escolha e A2")
    w("")
    w("Gerado por `tools/relatorio_pressao.py`. Não edite à mão: rode o script de novo (`--sobrescrever`). Nada "
      "deste relatório entra na planilha, e nada de `build/` é versionado.")
    w("")

    # 1
    w("## 1. Rótulos e proveniência")
    w("")
    w("Rótulos (spec §5), válidos para tudo o que segue:")
    w("")
    for r in cmp.ROTULOS_FIXOS:
        w(f"- {r}")
    w("- INTERPOLADO: toda saída a 9, 11 e 13 psi é interpolação linear das saídas de dois perfis (EDR-071), não "
      "medição nem ajuste")
    w("- \"Banda\" é faixa heurística, nunca intervalo de confiança; nenhuma tabela ordena as pressões por valor")
    w("")
    w(f"- Data: {data}")
    w(f"- Commit: `{commit}` (ramo `{ramo}`" + ("; com mudanças não commitadas em arquivos versionados" if sujo
                                                  else "; árvore sem mudanças pendentes") + ")")
    w(f"- Planilha: `{planilha.relative_to(RAIZ).as_posix() if planilha.is_relative_to(RAIZ) else planilha}` "
      f"(SHA-256 antes `{h_antes}`; depois igual: só uma cópia temporária foi recalculada)")
    w(f"- Motor de recálculo da cópia: {motor} ({detalhe_motor}); {resumo_rec['total_formulas']} fórmulas, "
      f"{resumo_rec['total_errors']} erros, {n(t_rec, 1)} s")
    w(f"- Caso da planilha: pneu = `.tir` de 12 psi da família, com os coeficientes da 10_TIRE por cima "
      f"(`caso_planilha.caso_da_planilha_v41`); {rot_passo1}")
    w(f"- KTF = {n(kt['F'], 0)} N/m e KTR = {n(kt['R'], 0)} N/m (lidos da cópia recalculada, usados na variante b)")
    w(f"- Família de pneus (ISO_TYDEX, EDR-039), revisão `{p12.revision_id}`; chaves reais das pressões: "
      + ", ".join(f"{q:.6f}" for q in pressoes) + "; teto comum de Fz: " + f"{n(teto, 0)} N")
    w("")
    w("| Pressão nominal [psi] | Arquivo | SHA-256 |")
    w("|---|---|---|")
    for q in pressoes:
        pr = fam.profiles[q]
        w(f"| {ps(q)} | `{pr.source_path.name}` | `{pr.base_sha256}` |")
    w("")
    w(f"- Varredura de robustez: `{VARREDURA.relative_to(RAIZ).as_posix()}` ({var['edr']}, origem "
      f"\"{var['origem']}\"; {var['nota']}); fatores " + "; ".join(f"{k} {v}" for k, v in fatores.items()))
    w(f"- Grade do equilíbrio: ay_max_g {GRADE['ay_max_g']}, passo_g {GRADE['passo_g']}, n_alfa {GRADE['n_alfa']}, "
      f"fator_neutro {GRADE['fator_neutro']} (a da 17_EQUILIBRIO da V4.1)")
    w(f"- Python {platform.python_version()}, openpyxl {version('openpyxl')}")
    w("")

    # 2
    w("## 2. A1-pneu: métricas por pressão")
    w("")
    w(f"Grade de Fz: {N_GRADE_FZ} valores igualmente espaçados de {n(piso, 0)} N (maior FZMIN) ao teto comum de "
      f"{n(teto, 0)} N, mais as Fz de operação do caso (as 4 rodas em a_y = 0 e no a_y limite do 12 psi, variante a). "
      "Fz de operação acima do teto é avaliada no teto e a linha diz isso. Menor carga ensaiada: a confirmar (FZMIN "
      "do `.tir` é o limite declarado, não a carga medida).")
    if fz_lim is None:
        w("**O 12 psi não tem a_y limite nesta grade (nenhum eixo satura até "
          f"{GRADE['ay_max_g']:g} g): não há Fz no a_y limite, e a grade traz só as Fz de a_y = 0.**")
        w("")
    w(f"Fz estática por pneu: eixo dianteiro {n(fz_estatica_eixo['F'], 0)} N, traseiro "
      f"{n(fz_estatica_eixo['R'], 0)} N (carga do eixo dividida por 2, `equilibrio.cargas` em a_y = 0). "
      f"Camber estático médio: dianteiro {graus(cam_eixo['F'])}, traseiro {graus(cam_eixo['R'])}; γ avaliados: "
      + ", ".join(graus(g) for g in gamas) + ".")
    w("")
    w("Sinais: Cα = −∂Fy/∂α e Cγ = −∂Fy/∂γ; Cκ = +∂Fx/∂κ (no `.tir` Fx > 0 para κ > 0; a spec §6 escreve \"−∂Fx/∂κ\", "
      "e a troca de sinal está a confirmar). Asterisco no μ: pico na borda da faixa, \"limitante inferior, sem pico "
      "interior\". Cγ: μy(γ) sem informação de pressão (PDY3 = 2 nos quatro perfis). Cκ e μx: ajuste longitudinal "
      "mal condicionado (PKX2/PKX3 instáveis). Assimetria ±α em parte física (conicidade e ply-steer).")
    w("")
    for g in gamas:
        w(f"### 2.{gamas.index(g) + 1} γ = {graus(g)}")
        w("")
        linhas = []
        for q in pressoes:
            for fz, rot in pontos_fz:
                m = met[(q, fz, g)]
                bordas = [nm for nm, pk in (("μy α>0", m.mu_y_pos), ("μy α<0", m.mu_y_neg),
                                            ("μx tração", m.mu_x_tracao), ("μx frenagem", m.mu_x_frenagem)) if pk.borda]
                st = lambda pk: n(pk.mu, 3) + ("*" if pk.borda else "")   # noqa: E731
                asm = tp.assimetria_alfa(m)
                linhas.append([ps(q), n(fz, 0), rot, n(m.c_alpha_n_rad / 1e3, 2), n(m.c_alpha_por_fz_1_rad, 2),
                               n(m.c_gamma_n_rad / 1e3, 2), n(m.c_kappa_n / 1e3, 1), st(m.mu_y_pos), st(m.mu_y_neg),
                               st(m.mu_x_tracao), st(m.mu_x_frenagem), ", ".join(bordas) or "—",
                               pct(asm.dif_rel), n(m.fy_alpha0_n, 1)])
        w("\n".join(tabela(["p [psi]", "Fz [N]", "Fz: origem", "Cα [kN/rad]", "Cα/Fz [1/rad]", "Cγ [kN/rad]",
                            "Cκ [kN]", "μy α>0", "μy α<0", "μx tração", "μx frenagem", "borda",
                            "assimetria ±α (rel.)", "Fy(α=0) [N]"], linhas)))
        w("")
    # indicadores LOO e monotonicidade
    w("### 2.x Indicadores de incerteza: erro LOO e monotonicidade")
    w("")
    w("Erro LOO = |erro| ao prever o perfil interno (10 e 12 psi) por interpolação linear dos vizinhos; 8 e 14 psi não têm "
      "LOO (extrapolar não é LOO), e isso é declarado, não preenchido. Entre parênteses, o erro relativo. "
      "Monotonicidade com a pressão (ordem crescente de pressão). Sem ranking.")
    w("")
    metricas_ind = [("Cα", lambda m: m.c_alpha_n_rad), ("Cγ", lambda m: m.c_gamma_n_rad),
                    ("Cκ", lambda m: m.c_kappa_n), ("μy α>0", lambda m: m.mu_y_pos.mu),
                    ("μx tração", lambda m: m.mu_x_tracao.mu)]
    UNID_IND = {"Cα": "N/rad", "Cγ": "N/rad", "Cκ": "N", "μy α>0": "adim.", "μx tração": "adim."}
    cab = ["γ", "Fz [N]"]
    for nm, _ in metricas_ind:
        u = UNID_IND[nm]
        cab += [f"{nm}: erro LOO 10 psi [{u}] (rel.)", f"{nm}: erro LOO 12 psi [{u}] (rel.)", f"{nm}: monot."]
    linhas = []
    for g in gamas:
        for fz, _ in pontos_fz:
            ln = [graus(g), n(fz, 0)]
            for nm, f in metricas_ind:
                loo = tp.erro_loo({q: f(met[(q, fz, g)]) for q in pressoes})
                for alvo in (10.0, 12.0):
                    k = next((x for x in loo if abs(x - alvo) < ts.PRESSURE_TOLERANCE_PSI), None)
                    e = loo.get(k) if k is not None else None
                    ln.append("—" if e is None else f"{n(abs(e.erro), 3)} ({pct(abs(e.erro_rel))})"
                              if e.erro_rel is not None else n(abs(e.erro), 3))
                ln.append(tp.monotonicidade({q: f(met[(q, fz, g)]) for q in pressoes}))
            linhas.append(ln)
    w("\n".join(tabela(cab, linhas)))
    w("")
    w("### 2.y Rigidez vertical e anexo t0")
    w("")
    w("Rigidez vertical: valor do arquivo, linear, origem não verificada. Anexo t0 e α do pico de Mz: pendentes do "
      "item 3 do EDR-067; fora do A1-escolha.")
    w("")
    fz_f = min(fz_estatica_eixo["F"], teto)
    k_f = min(((abs(fz - fz_f), fz) for fz, _ in pontos_fz))[1]
    linhas = []
    for q in pressoes:
        vs, orig = tp.rigidez_vertical(fam.profiles[q])
        m = met[(q, k_f, g_a2)]
        linhas.append([ps(q), n(vs, 0), orig, n(m.t0_m * 1e3, 2), n(math.degrees(m.alfa_pico_mz_rad), 2)])
    w("\n".join(tabela(["p [psi]", "VERTICAL_STIFFNESS [N/m]", "origem", f"t0 [mm] (Fz {n(k_f, 0)} N, γ {graus(g_a2)})",
                        "α do pico de Mz [°]"], linhas)))
    w("")
    w(f"Tempo das métricas do pneu: {n(t_met, 1)} s.")
    w("")

    # 3
    w("## 3. A1-carro: `comparar_carro`")
    w("")
    w("O caso da planilha rodado com o `ds` de cada perfil (λ ≠ 1 do caso copiados; FZMAX reescrito para o teto "
      "comum). Variante (a): KT do caso fixo, só muda a aderência. Variante (b): KT = VERTICAL_STIFFNESS do perfil nas "
      "4 rodas, o que muda também o K_φ. Robustez: a varredura de λ (LFZO, LMUY, LKY × 0,8; 1; 1,2) com a hipótese de "
      "que a perda TTC→pista é a mesma em todas as pressões. `resolução` é tolerância numérica, não critério de "
      "diferença. Sem ranking: ordem das pressões da família.")
    w("")
    linhas = []
    for r in res_carro:
        ay = "N/A" if r.ay_lim_ms2 is None else n(r.ay_lim_ms2 / sm.G, 4) + " g"
        rob = "—" if r.robustez is None else f"{r.robustez[0]}: {r.robustez[1]}"
        linhas.append([r.variante_kt, ps(r.pressao_psi), ay, r.sentido_pior, r.eixo_satura or "—", r.veredito,
                       f"{r.k_rad_ms2:.3e}".replace(".", ",") if r.k_rad_ms2 is not None else f"N/A ({r.k_motivo})",
                       "—" if r.resolucao_ms2 is None else n(r.resolucao_ms2 / sm.G, 4) + " g",
                       "sim" if r.borda_alfa else "não", rob])
    w("\n".join(tabela(["var.", "p [psi]", "a_y limite", "sentido pior", "eixo que satura", "veredito",
                        "K [rad/(m/s²)]", "resolução", "borda de α", "robustez ao pneu"], linhas)))
    w("")
    w("Rótulos do caso (variante a, 12 psi):")
    w("")
    for rr in r12a.rotulos:
        w(f"- {rr}")
    w("")
    w("Diferenças fora de λ entre o `ds` do caso (10_TIRE) e o `.tir` de 12 psi (`diferencas_fora_de_lambda`, "
      f"igualdade exata): **{len(difs)}**.")
    w("")
    if difs:
        w("\n".join(tabela(["coeficiente", "caso (10_TIRE)", ".tir 12 psi"],
                           [[k, f"{a_:.12g}", f"{b_:.12g}"] for k, (a_, b_) in difs.items()])))
        w("")
        w("O `ds` de cada pressão usa o coeficiente do `.tir`; o do caso é descartado nessas linhas.")
        w("")
    w(f"Tempo de `comparar_carro` (4 pressões × 2 variantes, com robustez): {n(t_carro, 1)} s.")
    w("")

    # 4
    w("## 4. A1-escolha: `escolher_pressao`")
    w("")
    w("Critério explícito, lista fechada: a_y_lim (máximo) e C_alpha_operacao (máximo, na Fz estática por eixo, no "
      "camber estático do eixo). K, TARGET-006 e TARGET-007 só com alvo definido na ficha; hoje são TBD e o código "
      "recusa. Regra simétrica: A e B são indistinguíveis se |X_A − X_B| ≤ max(banda_A, banda_B). 8 e 14 psi: banda "
      "não medida (maior banda interna, \"limite inferior\"); nunca declaradas melhores sozinhas. Pressão com pico "
      "na borda de α ou com valor/banda indisponível vira \"não decidível\", com o motivo. \"Todas indistinguíveis\" "
      "é um desfecho válido. Banda é faixa heurística, não intervalo de confiança.")
    w("")

    def bloco(titulo: str, esc: cmp.Escolha, fmt) -> None:
        w(f"### {titulo}")
        w("")
        for rot, v in esc.vereditos.items():
            w(f"**{rot}**: {v.desfecho}.")
            w("")
            linhas = []
            for q in pressoes:
                b = v.bandas.get(q)
                val = v.valores.get(q)
                linhas.append([ps(q), "N/A" if val is None else fmt(val),
                               "indisponível" if b is None or b.valor is None else fmt(b.valor),
                               "—" if b is None else (b.rotulo + ("" if b.medida else " [não medida]")),
                               "indistinguível do melhor valor" if q in v.indistinguiveis else "—",
                               v.nao_decidiveis.get(q, "—")])
            w("\n".join(tabela(["p [psi]", "valor", "banda", "tipo da banda", "conjunto indistinguível",
                                "não decidível: motivo"], linhas)))
            w("")
            w(f"- melhor: {'nenhuma declarada' if v.melhor is None else ps(v.melhor) + ' psi'}; indistinguíveis: "
              + (", ".join(ps(q) for q in v.indistinguiveis) or "nenhuma") + "; não decidíveis: "
              + (", ".join(ps(q) for q in sorted(v.nao_decidiveis)) or "nenhuma"))
            w("")
        if esc.veredito_muda_com_kt is not None:
            w(f"O veredito {'MUDA' if esc.veredito_muda_com_kt else 'não muda'} entre as variantes (a) e (b) de KT "
              "(compara o melhor, o conjunto indistinguível e o conjunto não decidível).")
            w("")

    bloco("4.1 Critério a_y_lim", esc_ay, lambda v: n(v / sm.G, 4) + " g")
    bloco("4.2 Critério C_alpha_operacao", esc_ca, lambda v: n(v / 1e3, 2) + " kN/rad")
    w("Rótulos adicionais: " + "; ".join(esc_ca.rotulos[len(cmp.ROTULOS_FIXOS):]) + ".")
    w("")

    # 5
    w("## 5. A2: pressão contínua por interpolação (INTERPOLADO)")
    w("")
    w(f"Curva Fy(α) a {', '.join(ps(q) for q in PRESSOES_A2)} psi, em Fz = {n(fz_a2, 0)} N (Fz estática dianteira) e "
      f"γ = {graus(g_a2)}, κ = 0. Toda saída é INTERPOLADA linearmente entre os dois perfis vizinhos (pesos com as "
      "chaves reais), dentro da interseção das faixas dos vizinhos, e não é medição. O pico de μy é um intervalo: "
      "inferior = máximo da curva misturada; superior = mistura dos picos dos vizinhos (cota, porque o máximo da soma "
      "é no máximo a soma dos máximos).")
    w("")
    for q in PRESSOES_A2:
        d = a2[q]
        w(f"### {ps(q)} psi (vizinhos {ps(d['viz'][0])} e {ps(d['viz'][1])} psi)")
        w("")
        if d["erro"]:
            w(f"Recusado: {d['erro']}")
            w("")
            continue
        m = d["m"]
        w(f"- Cα interpolado: {n(m.c_alpha_n_rad / 1e3, 2)} kN/rad; Cα/Fz: {n(m.c_alpha_por_fz_1_rad, 2)} 1/rad "
          "(métricas recalculadas sobre a curva interpolada)")
        for s, nm in ((1, "α>0"), (-1, "α<0")):
            lo_, hi_ = d["inter"][s]
            w(f"- Pico de μy {nm}: intervalo [{n(lo_, 3)}; {n(hi_, 3)}]")
        borda_nomes = [f"{ps(pq)} psi" for pq, bs in d["borda_viz"].items() if any(bs)]
        if borda_nomes:
            w(f"- **Pico na borda em {', '.join(borda_nomes)}** (vizinho com pico na borda de α): o extremo "
              "\"superior\" do intervalo deixa de ser cota, e o μ desse vizinho é limitante inferior, sem pico "
              "interior; o intervalo não fecha o pico.")
        w("")
        linhas = []
        for al, r in d["diag"]:
            loo = "; ".join(f"{ps(pq)} psi: {n(vv.get('fy_n', float('nan')), 1) if isinstance(vv, dict) else vv}"
                            for pq, vv in getattr(r, "loo_trecho", {}).items()) or "—"
            avisos = " | ".join(getattr(r, "avisos", ())) or "—"
            rot = getattr(r, "rotulo", "")
            linhas.append([graus(al), n(r.fy_n, 1), rot, loo, avisos])
        w("\n".join(tabela(["α", "Fy [N]", "rótulo", "LOO do trecho (Fy)", "avisos"], linhas)))
        w("")
    w("O aviso de pico (entre 12 e 14 psi a mistura junta uma curva com pico e outra sem pico) aparece na coluna de "
      "avisos quando se aplica ao trecho.")
    w("")

    # 6
    w("## 6. A3 e B (registro, sem implementação)")
    w("")
    w("- **A3:** sem implementação. O PAC2002 não tem termo térmico; a variável escondida é a temperatura "
      "(Milliken p. 55-56); a pressão do `.tir` é a de ensaio; falta dado de pressão e temperatura em pista e um "
      "modelo térmico.")
    w("- **B:** os `.tir` têm PTX1-3 = 0, PTY1-2 = 0 e USE_MODE = 4: não há σ (comprimentos de relaxação). Não usar "
      "valor típico como dado. Fonte possível: medir a rigidez lateral da carcaça do pneu da equipe em bancada e usar "
      "σα = C_Fα/C_Fy (Pacejka, TVD). Equações no help do Adams, folhas 53-55 (eq. 121-139, linear) e 55-60 "
      "(eq. 140-170, não linear). A rigidez da carcaça varia com a pressão: o B herda o eixo de pressão do A.")
    w("- **Degraus futuros:** A2 no carro; ajuste PP*/QPZ (rever EDR-015; a recusa de PP* do loader); `ds` por eixo "
      "para pressão diferente entre frente e trás.")
    w("")

    # 7
    w("## 7. Limitações")
    w("")
    for lim in ("Validation = NOT_VALIDATED: nada aqui é validação física nem resultado do carro",
                "R25B ≠ R60A: o pneu da equipe pode ter outra tendência com a pressão",
                "o `.tir` de cada pressão é uma calibração independente; a interpolação (A2) mistura saídas, não "
                "coeficientes, e não é medição",
                "`ds` único nas 4 rodas; sem raio carregado, altura de rodagem e cinemática decorrente",
                "Fy em α = 0 como no modelo (invertido pelo espelhamento nas rodas esquerdas)",
                "o caso é o demonstrativo T09/E03 com coeficientes de 12 psi como linha de base, não o T11",
                "a robustez de λ supõe a mesma perda TTC→pista em todas as pressões (hipótese declarada)",
                "a banda é heurística; o LOO do carro tem só dois nós internos (10 e 12 psi), e 8 e 14 psi usam o maior "
                "|LOO| interno como limite inferior",
                "Cκ e μx: ajuste longitudinal mal condicionado; Cγ: sem informação de pressão na PDY3",
                "pico na borda de α ou da faixa: valor é limitante inferior; a pressão vira \"não decidível\"",
                f"grade do equilíbrio: ay_max_g {GRADE['ay_max_g']}, passo_g {GRADE['passo_g']}, n_alfa "
                f"{GRADE['n_alfa']}; a_y limite fora dessa grade aparece como N/A"):
        w(f"- {lim}")
    w("")

    # PNG
    pngs: list[str] = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        plt = None
    if plt is None:
        w("## PNG")
        w("")
        w(SEM_MATPLOTLIB)
        w("")
    else:
        pasta = saida.parent
        pasta.mkdir(parents=True, exist_ok=True)
        ROT_FIG = ("R25B ≠ R60A; μ do TTC não transferível; pressão de ensaio ≠ fria (a confirmar);\n"
                   "Validation = NOT_VALIDATED; caso demonstrativo T09/E03, não o T11")

        def salvar(fig, arq):
            fig.tight_layout(rect=(0, 0.08, 1, 1))
            fig.text(0.5, 0.01, ROT_FIG, ha="center", va="bottom", fontsize=6.5)
            fig.savefig(arq, dpi=130)
            plt.close(fig)
            pngs.append(arq.name)

        cores = dict(zip(pressoes, ("#1b6ca8", "#2a9d8f", "#e9a100", "#c0392b")))
        g0 = g_a2
        # 1: Cα e Cα/Fz × Fz
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        for q in pressoes:
            fzs = [fz for fz, _ in pontos_fz]
            ax[0].plot(fzs, [met[(q, fz, g0)].c_alpha_n_rad / 1e3 for fz in fzs], "o-", color=cores[q], label=f"{ps(q)} psi")
            ax[1].plot(fzs, [met[(q, fz, g0)].c_alpha_por_fz_1_rad for fz in fzs], "o-", color=cores[q], label=f"{ps(q)} psi")
        ax[0].set(xlabel="Fz [N]", ylabel="Cα [kN/rad]", title=f"Cα (γ = {graus(g0)})")
        ax[1].set(xlabel="Fz [N]", ylabel="Cα/Fz [1/rad]", title="Cα/Fz")
        ax[0].legend()
        salvar(fig, pasta / "pressao-calpha.png")
        # 2: μy pico × Fz com marcador de borda
        fig, ax = plt.subplots(figsize=(6, 4))
        for q in pressoes:
            fzs = [fz for fz, _ in pontos_fz]
            mus = [met[(q, fz, g0)].mu_y_pos.mu for fz in fzs]
            ax.plot(fzs, mus, "-", color=cores[q], label=f"{ps(q)} psi")
            bx = [fz for fz in fzs if met[(q, fz, g0)].mu_y_pos.borda]
            ax.plot(bx, [met[(q, fz, g0)].mu_y_pos.mu for fz in bx], "x", color=cores[q], ms=8)
        ax.set(xlabel="Fz [N]", ylabel="μy pico (α>0)", title="x = pico na borda (limitante inferior)")
        ax.legend()
        salvar(fig, pasta / "pressao-muy.png")
        # 3: Fy(α) nos 4 perfis + curvas interpoladas
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for q in pressoes:
            prof = fam.profiles[q]
            fx = tp.faixa_do_perfil(prof)
            al = np.linspace(0.0, fx.alfa_max_rad, 80)
            av = tp.avaliador_perfil(prof)
            ax.plot(np.degrees(al), [abs(av(fz_a2, a_, g_a2, 0.0, 11.176).fy_n) for a_ in al], "-", color=cores[q],
                    label=f"{ps(q)} psi (perfil)")
        for q in PRESSOES_A2:
            if a2[q]["erro"]:
                continue
            fx = a2[q]["faixa"]
            al = np.linspace(0.0, fx.alfa_max_rad, 80)
            av = tp.avaliador_interpolado(fam, q)
            ax.plot(np.degrees(al), [abs(av(fz_a2, a_, g_a2, 0.0, 11.176).fy_n) for a_ in al], "--", color="0.35",
                    label=f"{ps(q)} psi (INTERPOLADO)")
            k = len(al) // 2
            ax.annotate(f"{ps(q)} psi INTERPOLADO", (np.degrees(al[k]), abs(av(fz_a2, al[k], g_a2, 0.0, 11.176).fy_n)),
                        fontsize=6.5, color="0.2", xytext=(0, 6 + 9 * PRESSOES_A2.index(q)), textcoords="offset points")
        ax.set(xlabel="α [°]", ylabel="|Fy| [N]", title=f"Fy(α), Fz = {n(fz_a2, 0)} N, γ = {graus(g_a2)}; tracejado = INTERPOLADO")
        ax.legend(fontsize=8)
        salvar(fig, pasta / "pressao-fy-alfa.png")
        # 4: a_y_lim por pressão com banda (só se alguma pressão tiver a_y limite)
        tem_ay = any(r.ay_lim_ms2 is not None for r in res_carro)
        if tem_ay:
            fig, ax = plt.subplots(figsize=(6, 4))
            for var, marc in (("a", "o"), ("b", "s")):
                rs = [r for r in res_carro if r.variante_kt == var]
                bd = cmp.banda_carro(rs)
                xs = [r.pressao_psi for r in rs if r.ay_lim_ms2 is not None]
                ys = [r.ay_lim_ms2 / sm.G for r in rs if r.ay_lim_ms2 is not None]
                er = [(bd[r.pressao_psi].valor or 0.0) / sm.G for r in rs if r.ay_lim_ms2 is not None]
                ax.errorbar(xs, ys, yerr=er, fmt=marc, capsize=3, label=f"KT ({var}); barra = banda heurística")
            ax.set(xlabel="pressão [psi]", ylabel="a_y limite [g]", title="a_y limite (demonstrativo T09/E03)")
            ax.legend(fontsize=8)
            salvar(fig, pasta / "pressao-ay-lim.png")
        else:
            (pasta / "pressao-ay-lim.png").unlink(missing_ok=True)   # nada de figura velha
        w("## PNG")
        w("")
        for nm in pngs:
            w(f"- `{(pasta / nm).relative_to(RAIZ).as_posix() if pasta.is_relative_to(RAIZ) else pasta / nm}`")
        if not tem_ay:
            w("- PNG do a_y limite não gerado: a_y limite N/A em todas as pressões")
        w("")

    t_tot = time.perf_counter() - t_ini
    w("## Execução")
    w("")
    w(f"Tempo total: {n(t_tot, 1)} s (recálculo {n(t_rec, 1)} s, métricas do pneu {n(t_met, 1)} s, comparar_carro "
      f"{n(t_carro, 1)} s).")
    w("")

    saida.parent.mkdir(parents=True, exist_ok=True)
    texto = "\n".join(md)
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    print(f"Relatório gravado em {saida} ({len(texto)} caracteres; {n(t_tot, 1)} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
