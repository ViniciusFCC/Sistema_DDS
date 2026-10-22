"""
Teste da V4.1 no motor de recálculo (incremento 4, equilíbrio na planilha; EDR-044): passo 2 (análise de par) × Python.
Recalcula CÓPIAS (aba_equilibrio.copia_v41: V4.0 da tag v4.0 + abas 16-18 + nomes da V4.1 + valores de teste) pelo Excel
(COM) ou pelo LibreOffice (recalculo_planilha.py; DDS_RECALC=excel|libreoffice força um). A V4.0 de referência em excel/
e a V3.0 viva nunca são abertas para escrita. Sem motor: NÃO EXECUTÁVEL (código 3), que nunca conta como aprovado.
Uso: uv run python -X utf8 tests/test_workbook_v4_1.py
Namespace TC-WB41-xxx (IDs autorizados pelo usuário: 001 a 006; este script tem, por enquanto, o 004).

TC-WB41-004: em cada caso (valores de TESTE, só nas cópias; não são o carro), o caso que a 16_EQUILIBRIO calcula, lido
por nomes (caso_planilha.caso_da_planilha_v41), vai a equilibrio.analise_par, e a planilha tem de dar o mesmo:
- por linha da grade pedida (17) e da refinada (18, contra equilibrio._varredura com passo/2 e 2·n − 1): Fz e γ das
  quatro rodas, capacidade e motivo de cada eixo e, na 17, a folga (erro relativo <= 1e-9);
- no resumo: S_f, S_r (17 e 18), resolução, veredito, motivo do N/A (texto exato), a_y limite, C_N, limitações (texto
  exato, uma por roda e limite), tempo de volta no skidpad (com R) e pior origem (pior_origem_do_caso_v41).
Casos: C1 (V4.1 como gerada, demonstrativa); C2 simétrico com LMUY 0,45 (esperado NEUTRO); C3 = C2 com K_ARB dianteiro × 3
(PUSH) e C3b com o traseiro × 3 (LOOSE); C4 = C3 com as hipóteses ligadas (R 8 m, h2, h3, CG lateral 10 mm com h7,
sentido "Direita", h8 com ρ 1,2 e CzA 2,0 e downforce fixa 0, h9 com CdA 1,0 e Crr 0,015, toe 0,25° na frente); C4b = C4
com δi = 22° na 07_KINEMATICS (% Ackermann ≠ 0, exercita a bisseção do Ackermann); C5 = C2 com h_CG 0,7 m (a roda interna
descola antes de saturar: N/A por descolamento).
Variantes do Review Focus: RF1 = C4 sem CzA (N/A "CzA a confirmar" na planilha e o mesmo ValueError no Python, nunca o
resultado da h8 desligada); RF3 = C3 com LKY × 0,9 e LMUY escalado até o eixo traseiro saturar na grade pedida e não
na refinada, perto de 2 g (resolução = passo da grade pedida, regra de equilibrio._resolucao); RF4 está no C1 (limitação que só a grade refinada
teria não entra no aviso: a planilha agrega só a 17, como equilibrio._limitacoes).
O log traz o tempo de recálculo de cada cópia e o número de células com fórmula de cada aba (insumo do portão da Task 4).
"Passou" = a planilha reproduz o oráculo; não é validação física.
"""
import dataclasses, math, sys, tempfile, time
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
from pathlib import Path
import openpyxl
import aba_equilibrio as ae
import caso_planilha as cp
import equilibrio as eq
import recalculo_planilha as rc
from suspension_model import G

MOTOR, DETALHE = rc.escolher()
if MOTOR is None:
    print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({DETALHE})"); sys.exit(3)
print(f"MOTOR: {MOTOR} ({DETALHE})")
_RAIZ = Path(__file__).resolve().parent.parent
TIR = _RAIZ / "data" / "Hoosier_R25B_13x7_TTC_provisional.tir"
TOL_REL = 1e-9
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


# --- Casos (valores de TESTE, só nas cópias) ---
ENT = ae.NOME_ENT
C2 = {"ent_05_rear_track_t_r": 1.277, "ent_05_fracao_de_peso_no_eixo_dianteiro_f": 0.5,
      "ent_05_massa_nao_suspensa_traseira": 15, "ent_06_spring_rate_traseiro": 49909.24,
      "ent_06_k_arb_traseiro": 5012.32, "ent_06_roll_center_traseiro_rh_estatico": 0.0675,
      "ent_07_camber_gain_traseiro_dcamber_dz": -0.6, "ent_10_camber_gama_projeto_topo_para_fora_d": -1.5,
      "ent_10_camber_gama_projeto_topo_para_fora_e": -1.5, "ent_08_aero_balance_fracao_dianteira": 0.5,
      "ent_10_lmuy": 0.45}   # t_R = t_F, a = b, massas, molas, MR, barras, RC, camber e aero iguais nos eixos
C3 = {**C2, "ent_06_k_arb_dianteiro": 5012.32 * 3}
C3b = {**C2, "ent_06_k_arb_traseiro": 5012.32 * 3}
C4 = {**C3, ENT["R"]: 8.0, ENT["h2"]: 1, ENT["h3"]: 1, ENT["cg"]: 0.010, ENT["h7"]: 1, ENT["sentido"]: "Direita",
      ENT["h8"]: 1, ENT["rho"]: 1.2, ENT["cza"]: 2.0, "ent_08_downforce_total": 0, ENT["h9"]: 1, ENT["cda"]: 1.0,
      ENT["crr"]: 0.015, ENT["toeFL"]: 0.25, ENT["toeFR"]: 0.25}
C4b = {**C4, "ent_07_angulo_da_roda_dianteira_interna_deltai": 22}
C5 = {**C2, "ent_05_altura_do_cg_total": 0.7}
RF1 = {**C4, ENT["cza"]: None}
# nome, alterações, veredito esperado (None = só a comparação com o Python), motivo esperado (prefixo) ou None
CASOS = [("C1", {}, None, None), ("C2", C2, eq.NEUTRO, None), ("C3", C3, eq.PUSH, None), ("C3b", C3b, eq.LOOSE, None),
         ("C4", C4, None, None), ("C4b", C4b, None, None), ("C5", C5, eq.NA, "Fz_"), ("RF1", RF1, eq.NA, "CzA a confirmar")]


def num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


DIF_MAX = [0.0, ""]   # maior |a − b|/escala visto (para o log: diferença entre motores é relatada, não ajustada)


def perto(a, b, escala=None, onde="") -> bool:
    """|a − b| <= TOL_REL·escala (escala padrão: max(|a|, |b|)); a da planilha, b do Python."""
    if not (num(a) and num(b)):
        return False
    e = max(abs(a), abs(b)) if escala is None else escala
    if e > 0 and abs(a - b) / e > DIF_MAX[0]:
        DIF_MAX[:] = [abs(a - b) / e, onde]
    return a == b or abs(a - b) <= TOL_REL * e


def valor(wb, nome):
    aba, cel = ae._destino(wb, nome)
    return wb[aba][cel].value


def recalcular(caminho: Path) -> tuple[dict, float]:
    t0 = time.perf_counter()
    if MOTOR == "excel":
        rc._excel_recalc(str(caminho.resolve()), 900)
    else:
        rc._libreoffice(str(caminho.resolve()), 900)
    t_motor = time.perf_counter() - t0
    return rc._resumo(str(caminho.resolve())), t_motor


def comparar_linhas(ws, linhas, n_alfa, pedida, caso, falhas, rotulo):
    cl = ae._colunas(n_alfa, pedida)
    for k, ln in enumerate(linhas):
        r = ae.PRIMEIRA_LINHA + k
        gam = eq.camber(caso, ln.ay_ms2)
        for c in eq.CANTOS:
            fz, gm = ws[f"{cl['Fz_' + c]}{r}"].value, ws[f"{cl['gam_' + c]}{r}"].value
            if not perto(fz, ln.fz[c], onde=f"{rotulo} Fz"):
                falhas.append(f"{rotulo} k={k} Fz_{c}: planilha {fz!r} Python {ln.fz[c]!r}")
            if not perto(gm, gam[c], max(abs(gam[c]), 1e-3), f"{rotulo} γ"):
                falhas.append(f"{rotulo} k={k} γ_{c}: planilha {gm!r} Python {gam[c]!r}")
        for e, cap, req in (("F", ln.cap_f, ln.req_f), ("R", ln.cap_r, ln.req_r)):
            v, mot = ws[f"{cl['cap_' + e]}{r}"].value, ws[f"{cl['mot_' + e]}{r}"].value
            if (cap.motivo or "-") != mot:
                falhas.append(f"{rotulo} k={k} motivo {e}: planilha {mot!r} Python {cap.motivo!r}")
            if cap.fy_max_N is None:
                if v != "N/A":
                    falhas.append(f"{rotulo} k={k} cap {e}: planilha {v!r}, Python None")
                continue
            if not perto(v, cap.fy_max_N, onde=f"{rotulo} cap"):
                falhas.append(f"{rotulo} k={k} cap {e}: planilha {v!r} Python {cap.fy_max_N!r}")
            if pedida:
                f_sh = ws[f"{cl['folga_' + e]}{r}"].value
                if cap.motivo is None:
                    if not perto(f_sh, cap.fy_max_N - req, max(abs(cap.fy_max_N), abs(req)), f"{rotulo} folga"):
                        falhas.append(f"{rotulo} k={k} folga {e}: planilha {f_sh!r} Python {cap.fy_max_N - req!r}")
                elif f_sh != "N/A":
                    falhas.append(f"{rotulo} k={k} folga {e}: planilha {f_sh!r}, Python sem folga ({cap.motivo})")


def sat_igual(sh, py) -> bool:
    return sh == "N/A" if py is None else perto(sh, py, onde="resumo")


def comparar_caso(nome, copia, esperado, prefixo, falhas):
    """Compara a cópia recalculada com o Python; devolve o resumo (texto) do caso."""
    wb = openpyxl.load_workbook(copia, data_only=True)
    r16 = {k: valor(wb, n) for k, n in ae.NOME16.items()}
    try:
        caso = cp.caso_da_planilha_v41(copia, TIR)
    except ValueError as e:   # entradas inválidas: a planilha tem de mostrar o mesmo motivo, como N/A
        wb.close()
        ok = r16["status"] == str(e) and r16["ver"] == eq.NA and r16["mot"] == str(e)
        if prefixo is not None:
            ok = ok and str(e).startswith(prefixo)
        if not ok:
            falhas.append(f"{nome}: Python ValueError({e!s}); planilha situação={r16['status']!r} "
                          f"veredito={r16['ver']!r} motivo={r16['mot']!r}")
        return f"{nome}: N/A pelas entradas ({e})"
    res = eq.analise_par(caso)
    fina, sf2, sr2 = eq._varredura(caso, ae.AY_MAX_G, ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1)
    comparar_linhas(wb[ae.ABA17], res.linhas, ae.N_ALFA, True, caso, falhas, f"{nome} 17")
    comparar_linhas(wb[ae.ABA18], fina, 2 * ae.N_ALFA - 1, False, caso, falhas, f"{nome} 18")
    pares = [("S_F", res.ay_sat_f), ("S_R", res.ay_sat_r), ("S2_F", sf2.ay_sat), ("S2_R", sr2.ay_sat),
             ("resol", res.resolucao_ms2), ("aylim", res.ay_lim), ("cn", res.c_n)]
    for k, py in pares:
        if not sat_igual(r16[k], py):
            falhas.append(f"{nome} {k}: planilha {r16[k]!r} Python {py!r}")
    if r16["ver"] != res.veredito:
        falhas.append(f"{nome} veredito: planilha {r16['ver']!r} Python {res.veredito!r}")
    if r16["mot"] != (res.motivo or "-"):
        falhas.append(f"{nome} motivo: planilha {r16['mot']!r} Python {res.motivo!r}")
    lims = [r16[f"lim_{c}_{lim}"] for c in ae.CANTOS for lim in ae.LIMITES]
    lims = tuple(x for x in lims if x != "-")
    if lims != res.limitacoes or r16["lims"] != ("; ".join(res.limitacoes) or "nenhuma"):
        falhas.append(f"{nome} limitações: planilha {lims!r} / {r16['lims']!r} Python {res.limitacoes!r}")
    if caso.raio_m is not None and res.ay_lim is not None:
        t_py = 2 * math.pi * math.sqrt(caso.raio_m / res.ay_lim)
        if not perto(r16["tvolta"], t_py):
            falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r} Python {t_py!r}")
    elif not (isinstance(r16["tvolta"], str) and r16["tvolta"].startswith("N/A")):
        falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r}, esperado N/A")
    wb.close()
    pior = cp.pior_origem_do_caso_v41(copia)
    if r16["pior"] != pior:
        falhas.append(f"{nome} pior origem: planilha {r16['pior']!r} Python {pior!r}")
    if esperado is not None and res.veredito != esperado:
        falhas.append(f"{nome}: veredito do Python {res.veredito} ≠ esperado no plano {esperado} (achado, não ajuste)")
    if prefixo is not None and not (res.motivo or "").startswith(prefixo):
        falhas.append(f"{nome}: motivo do Python {res.motivo!r} não começa por {prefixo!r}")
    g = lambda x: f"{x / G:.4f} g" if x is not None else "None"
    return (f"{nome}: {res.veredito} (motivo {res.motivo!r}); S_f {g(res.ay_sat_f)}, S_r {g(res.ay_sat_r)}, "
            f"resolução {g(res.resolucao_ms2)}, C_N {res.c_n}, {len(res.limitacoes)} limitação(ões)")


LKY_RF3 = 0.9   # escala só de teste: põe o pico traseiro em 2 g entre dois α da grade pedida (a refinada fica acima)


def lmuy_rf3(caso_c3) -> float:
    """LMUY (valor da 10_TIRE) em que, com LKY × LKY_RF3, o eixo traseiro do C3 satura na grade pedida e não na
    refinada. Com mais α, a refinada tem capacidade >= em cada linha; o fator de LMUY abaixo do qual cada grade satura
    até 2 g sai por bisseção, e o caso usa o meio da janela entre os dois limiares (folga longe do arredondamento dos
    motores). Valor de TESTE."""
    def satura(f, passo, n):
        cs = dataclasses.replace(caso_c3, ds=eq.com_fatores(caso_c3.ds, {"LMUY": f, "LKY": LKY_RF3}))
        return eq._varredura(cs, ae.AY_MAX_G, passo, n)[2].ay_sat is not None

    def limiar(passo, n):
        lo, hi = 1.3, 2.0
        if not satura(lo, passo, n) or satura(hi, passo, n):
            raise RuntimeError("RF3: o intervalo do fator de LMUY não cerca a saturação traseira em 2 g")
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if satura(mid, passo, n) else (lo, mid)
        return lo
    f_ped, f_fina = limiar(ae.PASSO_G, ae.N_ALFA), limiar(ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1)
    if not f_fina < f_ped:
        raise RuntimeError(f"RF3: sem janela entre as grades (fator pedida {f_ped}, refinada {f_fina})")
    return caso_c3.ds.p["LMUY"] * 0.5 * (f_ped + f_fina)


# --- TC-WB41-004 ---
falhas, resumos, tempos = [], [], []
base = ae.extrair_v40(Path(tempfile.mkdtemp()))
info_b, t_b = recalcular(base)
print(f"  V4.0 da tag (referência de tempo): {t_b:.1f} s no motor, {info_b['total_formulas']} fórmulas, "
      f"{info_b['total_errors']} erros")
caso_c3 = None
for nome, alt, esperado, prefixo in CASOS + [("RF3", None, None, None)]:
    if nome == "RF3":
        alt = {**C3, "ent_10_lmuy": lmuy_rf3(caso_c3), "ent_10_lky": caso_c3.ds.p["LKY"] * LKY_RF3}
    copia = ae.copia_v41(Path(tempfile.mkdtemp()), alt, f"{nome}.xlsx")
    info, t = recalcular(copia)
    tempos.append(t)
    print(f"  {nome}: recalculado em {t:.1f} s no motor; {info['total_formulas']} fórmulas, {info['total_errors']} erros")
    if info["total_errors"]:
        falhas.append(f"{nome}: {info['total_errors']} erro(s) de fórmula {info['error_summary']}")
    if nome == "C1":
        wbf = openpyxl.load_workbook(copia)
        for aba in (ae.ABA16, ae.ABA17, ae.ABA18):
            n = sum(1 for lin in wbf[aba].iter_rows() for c in lin if isinstance(c.value, str) and c.value.startswith("="))
            print(f"  CÉLULAS com fórmula em {aba}: {n}")
        wbf.close()
    if nome == "C3":
        caso_c3 = cp.caso_da_planilha_v41(copia, TIR)
    resumos.append(comparar_caso(nome, copia, esperado, prefixo, falhas))
    if nome == "RF3":
        caso = cp.caso_da_planilha_v41(copia, TIR)
        r = eq.analise_par(caso)
        _, _, sr2 = eq._varredura(caso, ae.AY_MAX_G, ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1)
        if not (r.ay_sat_r is not None and sr2.ay_sat is None and r.resolucao_ms2 == ae.PASSO_G * G):
            falhas.append(f"RF3: o caso não ficou com a traseira saturando só na grade pedida (S_r {r.ay_sat_r}, "
                          f"S_r refinada {sr2.ay_sat}, resolução {r.resolucao_ms2})")
for s in resumos:
    print("  " + s)
print(f"  MAIOR diferença relativa planilha × Python ({MOTOR}): {DIF_MAX[0]:.2e} ({DIF_MAX[1]})")
print(f"  TEMPO de recálculo ({MOTOR}): por cópia da V4.1 mín {min(tempos):.1f} s, máx {max(tempos):.1f} s, "
      f"média {sum(tempos) / len(tempos):.1f} s; V4.0 da tag {t_b:.1f} s")
check("TC-WB41-004: análise de par em fórmulas (16-18) == equilibrio.analise_par nos casos C1-C5, C3b, C4b e nas "
      "variantes RF1/RF3 (Fz, γ, capacidade, motivo e folga por linha, rel. <= 1e-9; S_f, S_r, resolução, veredito, "
      "motivo, a_y limite, C_N, limitações, tempo de volta, pior origem); 0 erros de fórmula",
      not falhas, f"{len(falhas)} divergência(s): {falhas[:8]}")

print("\n--- Resumo ---"); p = sum(1 for _, s in results if s == "PASS"); f = len(results) - p
print(f"{p} PASS, {f} FAIL, de {len(results)} testes")
sys.exit(1 if f else 0)
