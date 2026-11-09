"""
Testes do estudo da faixa do NEUTRO (incremento 7, Task 6; spec §4.3; EDR-065 item 2). O estudo não muda a regra.
TC-NEU-001: no caso V4.2 sintético (veiculo_base de tests/test_escada.py, pneu de escala LMUY 0,5, R = 8,5 m,
downforce 400 N com 45 % na frente):
  (a) as grades h, h/2, h/4 e h/8 são aninhadas (a h/2^k contém os pontos de a_y e de α da h);
  (b) estudar é determinístico (duas chamadas iguais);
  (c) erro_delta (contra a h/8) <= soma_erros, ou o caso sai marcado como violação;
  a regra não muda: o analise_par dá o veredito medido antes do estudo, e a grade h do estudo reproduz as saturações dele;
  a ordem observada nunca divide por zero (diferença < 1e-9 g dá p = None e dif_nula = True);
  os casos perturbados (λ_f ± 10 %, toe ± 0,1°, R ± 10 %) e a varredura perto do neutro (λ_f +4 % a +7 %) saem
  rotulados "sintético"; erro_delta e soma_erros são recalculados das saturações; o veredito_atual bate com o
  analise_par também no ramo PUSH (λ_f +10 %).
TC-NEU-002 (Task 9): a faixa do NEUTRO decidida pelo usuário (EDR-065 item 2, 2026-11-02): FATOR_NEUTRO = 4/3 só no
|S − S2| de cada eixo que satura nas duas grades; passo e piso sem fator; uma fonte só (analise_par e mmm.limite).
Roda como script: uv run python -X utf8 tests/test_neutro.py

Veículo, pneu de escala, R, downforce e balanço aero são entradas SINTÉTICAS de teste, não do carro.
"""
import math
import os

import equilibrio as eq
import estudo_neutro
import mmm
from suspension_model import G

HERE = os.path.dirname(os.path.abspath(__file__))
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


# O caso-base sintético é uma só função, estudo_neutro.caso_base_sintetico (tests/test_escada.py usa a mesma).
CASO = estudo_neutro.caso_base_sintetico(os.path.join(HERE, ".."))   # sintético de teste
# Veredito do analise_par neste caso, medido no commit b8d622d (antes do estudo existir), com os padrões
# ay_max_g = 2,0, passo_g = 0,05 e n_alfa = 25. O estudo não pode mudá-lo.
VEREDITO_ANTES = eq.LOOSE


def tc_neu_001() -> tuple[bool, str]:
    import estudo_neutro as en

    falhas = []
    r1 = en.estudar(CASO)
    r2 = en.estudar(CASO)

    # (a) grades aninhadas: passo/2^k e 2^k·(n_alfa − 1) + 1 pontos de α
    grades = r1["grades"]
    if len(grades) != 4:
        falhas.append(f"(a) {len(grades)} grades, esperadas 4")
    for k in range(1, len(grades)):
        (p0, n0), (pk, nk) = grades[0], grades[k]
        ay0 = {round(j * p0 * G, 12) for j in range(math.floor(2.0 / p0 + 1e-9) + 1)}
        ayk = {round(j * pk * G, 12) for j in range(math.floor(2.0 / pk + 1e-9) + 1)}
        al0 = {round(a, 12) for a in eq.grade_alfa(CASO, n0)}
        alk = {round(a, 12) for a in eq.grade_alfa(CASO, nk)}
        if not (ay0 <= ayk and al0 <= alk):
            falhas.append(f"(a) grade {k} não contém a h (a_y: {ay0 <= ayk}; α: {al0 <= alk})")

    # (b) determinismo
    if r1 != r2:
        falhas.append("(b) duas chamadas de estudar deram resultados diferentes")

    # (c) erro de Δ contra a soma das estimativas por eixo, ou violação listada
    if r1["ramo"] != "dois":
        falhas.append(f"(c) ramo {r1['ramo']!r}; o caso-base deveria saturar nos dois eixos")
    else:
        # erro_delta e soma_erros recalculados aqui das saturações, sem confiar no estudar
        sf, sr = r1["F"].s, r1["R"].s
        ed = abs((sr[0] - sf[0]) - (sr[3] - sf[3]))
        se = max(abs(sf[0] - sf[1]) + abs(sr[0] - sr[1]), 1e-9)
        if abs(ed - r1["erro_delta"]) > 1e-15 or abs(se - r1["soma_erros"]) > 1e-15:
            falhas.append(f"(c) erro_delta {r1['erro_delta']!r} ≠ {ed!r} ou soma_erros {r1['soma_erros']!r} ≠ {se!r}")
        if (ed > se) != r1["violacao"]:
            falhas.append(f"(c) erro_delta = {ed:.3e} g, soma_erros = {se:.3e} g, violacao = {r1['violacao']}")

    # A regra não muda: veredito de antes e saturações da grade h iguais às do analise_par
    res = eq.analise_par(CASO)
    if res.veredito != VEREDITO_ANTES:
        falhas.append(f"veredito {res.veredito}, antes {VEREDITO_ANTES}")
    if (r1["F"].s[0] * G, r1["R"].s[0] * G) != (res.ay_sat_f, res.ay_sat_r):
        falhas.append("a grade h do estudo não reproduz as saturações do analise_par")
    if r1["veredito_atual"] != res.veredito:
        falhas.append(f"veredito_atual do estudo {r1['veredito_atual']} ≠ analise_par {res.veredito}")

    # Ordem observada sem divisão por zero
    c_nula = en.convergencia("F", (1.0, 1.0, 1.0, 1.0))
    c_meia = en.convergencia("F", (1.0, 1.0 + 1e-6, 1.0 + 1.25e-6, 1.0 + 1.3125e-6))
    c_none = en.convergencia("R", (None, 1.0, 1.0, 1.0))
    if not (c_nula.p is None and c_nula.dif_nula and c_nula.razao is None):
        falhas.append(f"diferença nula: {c_nula}")
    if not (c_meia.p is not None and abs(c_meia.p - 2.0) < 1e-6 and not c_meia.dif_nula):
        falhas.append(f"p = 2 esperado: {c_meia}")
    if not (c_none.p is None and not c_none.dif_nula):
        falhas.append(f"eixo sem saturação numa grade: {c_none}")

    # Casos perturbados, todos rotulados sintético
    pert = en.casos_perturbados(CASO)
    if len(pert) != 6 or not all("sintético" in nome for nome in pert):
        falhas.append(f"casos perturbados: {sorted(pert)}")
    k_soma = CASO.cfg.roll_stiffness_front + CASO.cfg.roll_stiffness_rear
    lam = CASO.cfg.roll_stiffness_front / k_soma
    lams = sorted(c.cfg.roll_stiffness_front / (c.cfg.roll_stiffness_front + c.cfg.roll_stiffness_rear)
                  for c in pert.values() if c.cfg is not CASO.cfg)
    raios = sorted(c.raio_m for c in pert.values() if c.raio_m != CASO.raio_m)
    toes = sorted(c.toe_rad["FL"] for c in pert.values() if c.toe_rad != CASO.toe_rad)
    if not (len(lams) == 2 and abs(lams[0] - 0.9 * lam) < 1e-12 and abs(lams[1] - 1.1 * lam) < 1e-12):
        falhas.append(f"λ_f perturbado: {lams} (base {lam})")
    if not (len(raios) == 2 and abs(raios[0] - 0.9 * 8.5) < 1e-12 and abs(raios[1] - 1.1 * 8.5) < 1e-12):
        falhas.append(f"R perturbado: {raios}")
    if not (len(toes) == 2 and abs(toes[0] + math.radians(0.1)) < 1e-15 and abs(toes[1] - math.radians(0.1)) < 1e-15):
        falhas.append(f"toe perturbado: {toes}")

    # A cópia da regra (veredito_atual) também no ramo PUSH: λ_f +10 %
    caso_push = next(c for n, c in pert.items() if n.startswith("λ_f +"))
    res_push = eq.analise_par(caso_push)
    v_push = en.estudar(caso_push)["veredito_atual"]
    if not (res_push.veredito == eq.PUSH and v_push == res_push.veredito):
        falhas.append(f"λ_f +10 %: veredito_atual {v_push}, analise_par {res_push.veredito} (esperado PUSH)")

    # Varredura perto do neutro: λ_f +4 % a +7 % em passos de 0,5 %, rotulada
    perto = en.casos_perto_do_neutro(CASO)
    lams_p = [c.cfg.roll_stiffness_front / (c.cfg.roll_stiffness_front + c.cfg.roll_stiffness_rear)
              for c in perto.values()]
    esperados = [lam * (1.0 + (4.0 + 0.5 * k) / 100.0) for k in range(7)]
    if not (len(perto) == 7 and all("sintético" in n for n in perto)
            and all(abs(a - b) < 1e-12 for a, b in zip(lams_p, esperados))):
        falhas.append(f"casos perto do neutro: {list(perto)}")
    if en.classe(eq.NEUTRO, 0.001) != "NEUTRO" or en.classe(eq.PUSH, 0.001) != "certo" \
            or en.classe(eq.LOOSE, 0.001) != "ERRADO" or en.classe(eq.LOOSE, -0.001) != "certo":
        falhas.append("classe do veredito contra o sinal da h/8")

    det = (f"ramo {r1['ramo']}; p_F = {r1['F'].p}, p_R = {r1['R'].p}; erro_delta = {r1['erro_delta']:.3e} g, "
           f"soma_erros = {r1['soma_erros']:.3e} g; veredito {res.veredito}")
    return not falhas, ("; ".join(falhas) + " | " + det) if falhas else det


try:
    ok, det = tc_neu_001()
except Exception as exc:   # RED: o módulo ainda não existe
    ok, det = False, f"exceção {type(exc).__name__}: {exc}"
check("TC-NEU-001 estudo do NEUTRO: grades aninhadas, determinismo, erro de Δ × e_F + e_R e regra sem mudança",
      ok, det)

def tc_neu_002() -> tuple[bool, str]:
    import estudo_neutro as en

    falhas = []
    passo = 0.05 * G

    # (a) a regra da faixa em _resolucao, valores exatos: fator só no |S − S2|; passo e piso sem fator
    if not math.isclose(eq.FATOR_NEUTRO, 4.0 / 3.0, rel_tol=0, abs_tol=0):
        falhas.append(f"(a) FATOR_NEUTRO = {eq.FATOR_NEUTRO!r}, esperado 4/3")
    r_dois = eq._resolucao((10.0, 12.0), (9.99, 12.003), 0.5)
    if r_dois is None or abs(r_dois - 4.0 / 3.0 * 0.01) > 1e-15:
        falhas.append(f"(a) dois eixos nas duas grades: {r_dois!r}, esperado 4/3·0,01")
    r_passo = eq._resolucao((10.0, None), (None, None), 0.5)      # um eixo numa grade só: o passo, sem fator
    r_mista = eq._resolucao((10.0, 12.0), (9.99, None), 0.5)      # um eixo nas duas (4/3·0,01) e outro numa só (passo)
    r_mista_pequena = eq._resolucao((10.0, 12.0), (9.99, None), 0.001)   # passo menor que 4/3·|S − S2|: vale o 4/3
    if r_passo != 0.5 or r_mista != 0.5 or r_mista_pequena is None or abs(r_mista_pequena - 4.0 / 3.0 * 0.01) > 1e-15:
        falhas.append(f"(a) passo sem fator: {r_passo!r}, {r_mista!r}, {r_mista_pequena!r}")
    if eq._resolucao((10.0, 12.0), (10.0, 12.0), 0.5) != 1e-9 * G:   # piso sem fator
        falhas.append("(a) o piso de 1e-9 g mudou ou ganhou o fator")
    if eq._resolucao((None, None), (None, None), 0.5) is not None:
        falhas.append("(a) nenhum eixo satura: esperado None")

    # (b) as duas bordas da faixa nova no caso sintético da varredura do estudo (λ_f relativo, SINTÉTICO). O caso de
    # λ_f +4,7 % dá LOOSE com a faixa de ontem (|Δ| > R) e NEUTRO com a nova; λ_f +6,5 %, o mesmo no PUSH. A bisseção em λ_f
    # acha o par adjacente (fora, dentro) de cada borda e confere |Δ| × faixa dos dois lados.
    def par_de(lam_rel):
        return eq.analise_par(en._com_lambda(CASO, lam_rel))

    def delta_e_faixa(r):
        return abs(r.ay_sat_r - r.ay_sat_f), r.resolucao_ms2

    det_b = []
    for rotulo, fora, dentro, v_fora in (("borda LOOSE", 1.043, 1.047, eq.LOOSE), ("borda PUSH", 1.068, 1.065, eq.PUSH)):
        r_fora, r_dentro = par_de(fora), par_de(dentro)
        if r_fora.veredito != v_fora or r_dentro.veredito != eq.NEUTRO:
            falhas.append(f"(b) {rotulo}: extremos {r_fora.veredito}/{r_dentro.veredito}, esperado {v_fora}/NEUTRO")
            continue
        a, b = fora, dentro            # a: fora da faixa; b: dentro. Invariante preservada passo a passo.
        for _ in range(16):
            m = 0.5 * (a + b)
            if par_de(m).veredito == eq.NEUTRO:
                b = m
            else:
                a = m
        r_a, r_b = par_de(a), par_de(b)
        d_a, f_a = delta_e_faixa(r_a)
        d_b, f_b = delta_e_faixa(r_b)
        if not (r_b.veredito == eq.NEUTRO and d_b <= f_b and r_a.veredito == v_fora and d_a > f_a):
            falhas.append(f"(b) {rotulo}: dentro {r_b.veredito} |Δ| = {d_b:.4e} faixa {f_b:.4e}; fora {r_a.veredito} "
                          f"|Δ| = {d_a:.4e} faixa {f_a:.4e}")
        # a faixa é a nova: o NEUTRO de dentro seria PUSH/LOOSE com a faixa de ontem (sem o fator)
        if not d_b > f_b / eq.FATOR_NEUTRO:
            falhas.append(f"(b) {rotulo}: |Δ| = {d_b:.4e} cabe na faixa de ontem {f_b / eq.FATOR_NEUTRO:.4e}; não prova o fator")
        # os dois lados estão colados à borda (|Δ|/faixa perto de 1; medido 1,0000, e 16 passos de bisseção dão margem de 1e-3)
        if not (abs(d_b / f_b - 1.0) < 1e-3 and abs(d_a / f_a - 1.0) < 1e-3):
            falhas.append(f"(b) {rotulo}: |Δ|/faixa = {d_b / f_b:.5f} (dentro) e {d_a / f_a:.5f} (fora), longe da borda")
        det_b.append(f"{rotulo}: λ_f x{b:.7f} NEUTRO |Δ|/faixa = {d_b / f_b:.4f}; "
                     f"x{a:.7f} {r_a.veredito} {d_a / f_a:.4f}")

    # (c) eixo que satura numa grade só: a faixa é o passo da grade pedida, como hoje, sem o fator. ay_max = 1,475 g
    # deixa a última linha da grade pedida em 1,45 g (antes das saturações, em ~1,47 g) e a da refinada em 1,475 g
    # (depois): os dois eixos saturam só na refinada. O ramo de um eixo só (PUSH/LOOSE por um eixo) lê esta mesma faixa.
    r_c = eq.analise_par(CASO, ay_max_g=1.475)
    if not (r_c.ay_sat_f is None and r_c.ay_sat_r is None and r_c.resolucao_ms2 == passo):
        falhas.append(f"(c) satura numa grade só: S = ({r_c.ay_sat_f}, {r_c.ay_sat_r}), faixa {r_c.resolucao_ms2!r} ≠ passo {passo!r}")

    # (d) uma fonte só: o mmm não tem constante própria e, recebendo a faixa do analise_par, dá o mesmo veredito
    # (caminho desacoplado, mesma grade de α) dos dois lados das bordas e no meio da faixa; no acoplado, a folga lê a
    # mesma faixa (resolucao_ms2 devolvida igual) e o meio da faixa continua NEUTRO.
    if hasattr(mmm, "FATOR_NEUTRO"):
        falhas.append("(d) mmm tem FATOR_NEUTRO próprio: a fonte deve ser só equilibrio.FATOR_NEUTRO")
    det_d = []
    for lam_rel in (1.043, 1.047, 1.055, 1.065, 1.07):
        caso = en._com_lambda(CASO, lam_rel)
        par = eq.analise_par(caso)
        lim = mmm.limite(caso, mmm.Hipoteses.planilha(), resolucao_ms2=par.resolucao_ms2, n_alfa=25)
        if lim.veredito != par.veredito or lim.resolucao_ms2 != par.resolucao_ms2:
            falhas.append(f"(d) λ_f x{lam_rel}: mmm.limite {lim.veredito} ≠ analise_par {par.veredito}")
        det_d.append(f"{par.veredito}")
        if lam_rel == 1.055:
            lim_ac = mmm.limite(caso, mmm.planilha_acoplada(), resolucao_ms2=par.resolucao_ms2, n_alfa=25)
            if lim_ac.veredito != eq.NEUTRO or lim_ac.resolucao_ms2 != par.resolucao_ms2:
                falhas.append(f"(d) acoplado no meio da faixa: {lim_ac.veredito}, resolução {lim_ac.resolucao_ms2}")

    det = f"{'; '.join(det_b)}; (c) faixa = passo = {r_c.resolucao_ms2 / G:.4f} g; (d) vereditos {'/'.join(det_d)}"
    return not falhas, ("; ".join(falhas) + " | " + det) if falhas else det


try:
    ok, det = tc_neu_002()
except Exception as exc:
    ok, det = False, f"exceção {type(exc).__name__}: {exc}"
check("TC-NEU-002 faixa do NEUTRO (EDR-065 item 2): 4/3 só no |S − S2|, NEUTRO na borda, PUSH/LOOSE fora, passo sem fator, "
      "analise_par e mmm.limite com a mesma constante", ok, det)

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
