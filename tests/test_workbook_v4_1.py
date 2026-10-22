"""
Teste da V4.1 no motor de recálculo (incremento 4, equilíbrio na planilha; EDR-044): passo 2 (análise de par) × Python.
Recalcula CÓPIAS (aba_equilibrio.copia_v41: V4.0 da tag v4.0 + abas 16-18 + nomes da V4.1 + valores de teste) pelo Excel
(COM) ou pelo LibreOffice (recalculo_planilha.py; DDS_RECALC=excel|libreoffice força um). A V4.0 de referência em excel/
e a V3.0 viva nunca são abertas para escrita. Sem motor: NÃO EXECUTÁVEL (código 3), que nunca conta como aprovado.
Uso: uv run python -X utf8 tests/test_workbook_v4_1.py
Namespace TC-WB41-xxx (IDs autorizados pelo usuário: 001 a 006; este script tem o 004, o 005 e o 006, em duas partes).

TC-WB41-004: em cada caso (valores de TESTE, só nas cópias; não são o carro), o caso que a 16_EQUILIBRIO calcula, lido
por nomes (caso_planilha.caso_da_planilha_v41), vai a equilibrio.analise_par, e a planilha tem de dar o mesmo:
- por linha da grade pedida (17) e da refinada (18, contra equilibrio._varredura com passo/2 e 2·n − 1): Fz e γ das
  quatro rodas, capacidade e motivo de cada eixo e, na 17, a folga (erro relativo <= 1e-9);
- no resumo: S_f, S_r (17 e 18), resolução, veredito, motivo do N/A (texto exato), a_y limite, C_N, limitações (texto
  exato, uma por roda e limite), tempo de volta no skidpad (com R) e pior origem (pior_origem_do_caso_v41).
Casos: C1 (V4.1 como gerada, demonstrativa); C2 simétrico com LMUY 0,45 (esperado NEUTRO); C3 = C2 com K_ARB dianteiro × 3
(PUSH) e C3b com o traseiro × 3 (LOOSE); C4 = C3 com as hipóteses ligadas (R 8 m, h2, h3, CG lateral 10 mm com h7,
sentido "Direita", h8 com ρ 1,2 e CzA 2,0 e downforce fixa 0, h9 com CdA 1,0 e Crr 0,015, toe na frente); C4b = C4
com δi = 22° na 07_KINEMATICS (% Ackermann ≠ 0, exercita a bisseção do Ackermann); C5 = C2 com h_CG 0,7 m (a roda interna
descola antes de saturar: N/A por descolamento).
O C4 usa toe 0,25°/0,10° e camber estático −1,5°/−1,0° em FL/FR (assimétricos), para o espelho ser testado.
Variantes do Review Focus: RF1 = C4 sem CzA (N/A "CzA a confirmar" na planilha e o mesmo ValueError no Python, nunca o
resultado da h8 desligada); RF3 = C3 com LKY × 0,9 e LMUY escalado até o eixo traseiro saturar na grade pedida e não
na refinada, perto de 2 g (resolução = passo da grade pedida, regra de equilibrio._resolucao); RF4 está no C1 (limitação que só a grade refinada
teria não entra no aviso: a planilha agrega só a 17, como equilibrio._limitacoes).
TC-WB41-005: nas MESMAS cópias recalculadas (sem recalcular de novo), o passo 1 da 19_EQ_LINEAR contra
equilibrio_linear.tabela_linear(caso, pior_origem=...) (a_y = k·0,05 g, k = 0…8): parcelas k_pneus, k_transferência,
k_deslocamento, k_camber, k_roll_steer e k_total por linha (|Δ| <= 1e-6 °/g; N/A onde o Python dá None), motivo do N/A
(texto exato), k_inclinacao e o motivo dela; os ângulos necessários do Newton (decisão 5 do plano) contra a bissecção de
angulos_necessarios nos 11 pontos (0…0,4 g, 0,005 g e 0,01 g; |Δα| <= 1e-8·max(|α|, 1e-3): outra raiz é falha, Review
Focus 2); a igualdade da 1ª linha k_pneus + k_deslocamento + k_camber = k_inclinacao, com o resíduo da planilha igual ao
do Python (|Δ| <= 1e-6 °/g; a identidade com rel. <= 1e-6 vai ao log como ACHADO: o próprio Python não chega lá, ver
comparar_k); na 16, o
K da 1ª linha (res_16_k_total e as parcelas), V_char e V_crit (velocidade_caracteristica/critica) e a pior origem do K
(pior_origem_do_caso_v41(..., linear=True), que inclui o roll steer da 07_KINEMATICS). Caso com entradas inválidas: todo K
é N/A com o motivo da situação das entradas. Roll steer (07_KINEMATICS B82/B83): RS1 = C2 com ε_f 0,05 e ε_r −0,03 °/°
(TESTE; k_roll_steer ≠ 0 bate com o Python); RS2 = C2 com ε_f vazio (caso_da_planilha_v41 levanta o motivo; a planilha dá
k_roll_steer e K N/A com "… a confirmar" e o resto das parcelas igual ao Python). O passo 2 usa o caso com passo1=False.
TC-WB41-006 (parte 1): nas MESMAS cópias, a tabela de troca da barra dianteira
(20_EQ_TROCA, K_ARB dianteiro × 0,5; 0,75; 1; 1,5; 2 do valor da 06, grade de exibição) contra o Python: para cada linha,
caso_da_planilha_v41 com o K_ARB dianteiro × fator (K_φF por suspension_model.roll_stiffness_axle, a mesma ordem de
verificações), equilibrio.analise_par e equilibrio_linear.parcelas_k(caso, 0): K_φF, λ_f, K, S_f, S_r, a_y limite,
resolução, veredito, C_N e motivos; depois o a_y do acerto neutro pelo cruzamento das saturações (1º par de linhas
vizinhas em que S_r − S_f troca de sinal, por interpolação linear de S_f e S_r, ou vale 0; senão a linha NEUTRO de menor
|S_r − S_f|; senão N/A "neutro fora da faixa da tabela", sem extrapolação) e o custo = a_y do neutro − a_y limite do ×1,
com "limiar não definido" (spec §5, itens 4 e 5). TR1 = C2 com o K_ARB traseiro × 1,25 (TESTE): o neutro cai entre ×1 e
×1,5, e o check exige pelo menos um caso com a interpolação.
TC-WB41-006 (parte 2): nas MESMAS cópias, os textos de exibição da 16_EQUILIBRIO e do 14_DASHBOARD iguais a
equilibrio.texto_veredito(res, pior) e equilibrio_linear.texto_k(p, pior) (sem "-" como motivo; o dashboard repete a 16,
com a mesma pior origem), a linha de apoio (os números da própria cópia formatados pelo Python) e o sentido da curva; na
cópia C1, os textos fixos (aviso de robustez ao lado do veredito, "regimes diferentes" ao lado do K, diferencial), as
cores azul/laranja por formatação condicional e as abas 21 e 22. A pior origem do prefixo D16 é conferida contra uma
construção INDEPENDENTE da fórmula: ORG_TX = C3 com todas as células de Origem (nomes org_*) em "● Dado do TX" (texto sem o
prefixo); ORG_T09 = C3b com tudo em TX e a massa medida sem piloto em "◐ Dado do T09" (texto com o prefixo).
O log traz o tempo de recálculo de cada cópia e o número de células com fórmula de cada aba (insumo do portão da Task 4).
"Passou" = a planilha reproduz o oráculo; não é validação física.
"""
import csv, dataclasses, json, math, os, re, sys, tempfile, threading, time
from types import SimpleNamespace
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
from pathlib import Path
import openpyxl
import aba_equilibrio as ae
import caso_planilha as cp
import equilibrio as eq
import equilibrio_linear as el
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
ESPERADO6 = {}   # nome do caso -> textos de exibição esperados (TC-WB41-006, parte 2): txt_ver, txt_k


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
      ENT["crr"]: 0.015, ENT["toeFL"]: 0.25, ENT["toeFR"]: 0.10,
      # toe e camber estático com FL ≠ FR (TESTE): o "Direita" tem de trocar L↔R, não só inverter o CG lateral
      "ent_10_camber_gama_projeto_topo_para_fora_b": -1.5, "ent_10_camber_gama_projeto_topo_para_fora_c": -1.0}
C4b = {**C4, "ent_07_angulo_da_roda_dianteira_interna_deltai": 22}
C5 = {**C2, "ent_05_altura_do_cg_total": 0.7}
RF1 = {**C4, ENT["cza"]: None}
# Roll steer (SUS-415, 07_KINEMATICS B82/B83, °/°; valores de TESTE, só nas cópias): RS1 com ε_f ≠ ε_r (k_roll_steer ≠ 0,
# pega sinal trocado em ε_f − ε_r; sobre o C2, cujo K sem roll steer é 0); RS2 com ε_f vazio (K N/A "… a confirmar").
EPS_F, EPS_R = "ent_07_roll_steer_dianteiro_epsilon_f", "ent_07_roll_steer_traseiro_epsilon_r"
RS1 = {**C2, EPS_F: 0.05, EPS_R: -0.03}
RS2 = {**C2, EPS_F: None}
# Tabela de troca (TC-WB41-006): TR1 = C2 com o K_ARB traseiro × 1,25 (TESTE), para o neutro cair entre as linhas ×1 e
# ×1,5 da barra dianteira e o cruzamento sair de uma interpolação (no C2 o ×1 já é neutro, com S_r − S_f = 0).
TR1 = {**C2, "ent_06_k_arb_traseiro": 5012.32 * 1.25}
# nome, alterações, veredito esperado (None = só a comparação com o Python), motivo esperado (prefixo) ou None
CASOS = [("C1", {}, None, None), ("C2", C2, eq.NEUTRO, None), ("C3", C3, eq.PUSH, None), ("C3b", C3b, eq.LOOSE, None),
         ("C4", C4, None, None), ("C4b", C4b, None, None), ("C5", C5, eq.NA, "Fz_"), ("RF1", RF1, eq.NA, "CzA a confirmar"),
         ("RS1", RS1, None, None), ("RS2", RS2, None, None), ("TR1", TR1, None, None)]


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


# --- Modo --medir: custo de recálculo da tabela de troca da barra dianteira (portão da Task 4; não é teste) ---
def _re_nomes(nomes):
    return re.compile(r"(?<![A-Za-z0-9_.!'])(" + "|".join(sorted(map(re.escape, nomes), key=len, reverse=True))
                      + r")(?![A-Za-z0-9_.])")


def _clonar_grade(wb, aba, nova, i):
    """Cópia da aba de grade `aba` como `nova` com um K_φF próprio (H1 = K_φF·(1 + 0,05·i), TESTE de medição: o
    valor só dá um custo, não um resultado do carro; i = 0 reproduz a original). Os nomes do resumo da própria aba
    viram células locais e K_φF e o denominador da rolagem (16) passam a ler H1 e I1."""
    ws = wb.copy_worksheet(wb[aba])
    ws.title = nova
    local = {ae.NOME_RESUMO[(aba, k)]: f"$B${ae.LINHA_RESUMO0 + j}" for j, (k, _, _) in enumerate(ae.RESUMO_GRADE)}
    kphi, den = ae.V40["KphiF"], ae.NOME16["den"]
    local[kphi], local[den] = "$H$1", "$I$1"
    rx = _re_nomes(local)
    for lin in ws.iter_rows():
        for c in lin:
            if isinstance(c.value, str) and c.value.startswith("="):
                c.value = rx.sub(lambda m: local[m.group(1)], c.value)
    ws["G1"] = "TESTE de medição: K_φF da linha, K_φF·(1 + 0,05·i), e o denominador da rolagem com ele"
    ws["H1"] = f"={kphi}*(1+0.05*{i})"
    ws["I1"] = f"={den}+($H$1-{kphi})"
    return ws


def _clonar_k19(wb, i):
    """Linha de a_y = 0 do cálculo auxiliar da 19 (ângulos, parcelas e K da 1ª linha) lendo a cópia `M{i}_17`. Não copia
    a célula que cita outra linha da 19 (só a inclinação do Richardson, kI, que não entra no K); devolve essas células."""
    src, ws = wb[ae.ABA19], wb.create_sheet(f"M{i}_19")
    r0, pulou = ae.LINHA_AUX19, []
    # os pontos a_y ± da transferência de carga usam K_φF e o denominador da rolagem: leem os da cópia M{i}_17 (H1 e I1)
    troca = {ae.V40["KphiF"]: f"'M{i}_17'!$H$1", ae.NOME16["den"]: f"'M{i}_17'!$I$1"}
    rx = _re_nomes(troca)
    for c in src[r0]:
        if isinstance(c.value, str) and c.value.startswith("="):
            f = rx.sub(lambda m: troca[m.group(1)], c.value.replace(f"'{ae.ABA17}'!", f"'M{i}_17'!"))
            local = re.sub(r'"[^"]*"', "", re.sub(r"'[^']*'![$A-Z0-9:]+", "", f))
            if any(int(m.group(1)) != r0 for m in re.finditer(r"(?<![A-Za-z0-9_$!:'])\$?[A-Z]{1,3}\$?(\d+)(?![A-Za-z0-9_(])", local)):
                pulou.append(c.coordinate)
            else:
                ws[c.coordinate] = f
    return pulou


def _variante(tmp, nome, n, refinada, k19):
    """Cópia da V4.1 com `n` análises de par extras (grade pedida, mais a refinada se `refinada`, mais o K da 1ª linha
    do passo 1 se `k19`); `n` = 0 é a V4.1 como gerada. Devolve (caminho, células da 19 não copiadas)."""
    wb = openpyxl.load_workbook(ae.extrair_v40(tmp))
    fora = []
    try:
        ae.montar(wb)
        ae.acrescentar_nomes(wb)
        for i in range(n):
            _clonar_grade(wb, ae.ABA17, f"M{i}_17", i)
            if refinada:
                _clonar_grade(wb, ae.ABA18, f"M{i}_18", i)
            if k19:
                fora = _clonar_k19(wb, i)
        wb.calculation.fullCalcOnLoad = True
        saida = (Path(tmp) / f"{nome}.xlsx").resolve()
        wb.save(saida)
    finally:
        wb.close()
    return saida, fora


def _motor_recalc(motor, caminho):
    t0 = time.perf_counter()
    (rc._excel_recalc if motor == "excel" else rc._libreoffice)(str(caminho.resolve()), 1800)
    return time.perf_counter() - t0


def _excel_detalhado(caminho, aba, cel):
    """No Excel: CalculateFull sozinho (sem gravar o arquivo) e o recálculo automático ao trocar o K_ARB dianteiro
    (06_SUSPENSION, célula `aba`!`cel`), que é o que a equipe sentiria ao editar. Numa cópia; o arquivo não é salvo."""
    xl = rc._abrir_excel()
    vigia = threading.Timer(1800, rc._matar_excel)
    vigia.start()
    try:
        wb = xl.Workbooks.Open(str(caminho.resolve()), UpdateLinks=0, ReadOnly=False)
        try:
            calc0 = xl.Calculation
            xl.Calculation = -4105   # xlCalculationAutomatic
            t0 = time.perf_counter()
            xl.CalculateFull()
            t_full = time.perf_counter() - t0
            c = wb.Worksheets(aba).Range(cel)
            v = c.Value2
            t0 = time.perf_counter()
            c.Value2 = v * 1.01
            t_edit = time.perf_counter() - t0
        finally:
            xl.Calculation = calc0
            wb.Close(SaveChanges=False)
    finally:
        vigia.cancel()
    return t_full, t_edit


def _estat(v):
    return f"{min(v):.1f} / {sum(v) / len(v):.1f} / {max(v):.1f}"


def _igual(a, b):
    if a is None or b is None:
        return False
    return a == b or (num(a) and num(b) and abs(a - b) <= 1e-12 * max(abs(a), abs(b)))


def medir(repeticoes=3, rep_lo=None):
    if os.environ.get("DDS_RECALC") or MOTOR != "excel":
        motores = [MOTOR]
    else:
        motores = ["excel"] + (["libreoffice"] if rc._soffice() else [])
    tmp = Path(tempfile.mkdtemp())
    wbn = openpyxl.load_workbook(ae.extrair_v40(tmp))
    ae.acrescentar_nomes(wbn)   # só para ler o destino de um nome (ae._destino)
    aba_k, cel_k = ae._destino(wbn, "ent_06_k_arb_dianteiro")
    wbn.close()
    # (rótulo, n, refinada, k19): 0 = V4.1 como gerada; P = pedida (17); R = pedida + refinada; RK = R + K da 1ª linha
    var = [("0", 0, False, False)] + [(f"{v}{n}", n, v != "P", v == "RK") for v in ("P", "R", "RK") for n in (1, 3, 5)]
    arquivos, erros_clone = {}, {}
    for rot, n, ref, k19 in var:
        arquivos[rot], fora = _variante(tmp, rot, n, ref, k19)
        if fora:
            erros_clone[rot] = fora
        print(f"  variante {rot}: {arquivos[rot].stat().st_size / 1e6:.1f} MB; células da 19 não copiadas: {fora}")
    res = {m: {} for m in motores}
    conf, sens = {}, {}
    for m in motores:
        for rot, *_ in var:
            ts = [_motor_recalc(m, arquivos[rot]) for _ in range(rep_lo if m == "libreoffice" and rep_lo else repeticoes)]
            info = rc._resumo(str(arquivos[rot].resolve()))
            res[m][rot] = (ts, info["total_formulas"], info["total_errors"], info["error_summary"])
            print(f"  {m} {rot}: {_estat(ts)} s; {info['total_formulas']} fórmulas; {info['total_errors']} erros", flush=True)
        # Conferência das cópias: a cópia i = 0 (K_φF × 1) tem de dar o que a 17, a 18 e a 19 dão
        wv = openpyxl.load_workbook(arquivos["RK3"], data_only=True)
        linhas = []
        for aba, cp_ in ((ae.ABA17, "M0_17"), (ae.ABA18, "M0_18")):
            for j, (k, _, _) in enumerate(ae.RESUMO_GRADE):
                a, b = wv[aba][f"B{ae.LINHA_RESUMO0 + j}"].value, wv[cp_][f"B{ae.LINHA_RESUMO0 + j}"].value
                linhas.append((aba, k, a, b, _igual(a, b)))
        kt = f"{ae.CL19['kTot']}{ae.LINHA_AUX19}"
        a, b = wv[ae.ABA19][kt].value, wv["M0_19"][kt].value
        linhas.append((ae.ABA19, f"K total, cálculo auxiliar, a_y = 0 ({kt})", a, b, _igual(a, b)))
        conf[m] = linhas
        # Sensibilidade: com i >= 1 (K_φF × 1,05 e × 1,10) a cópia tem de DIFERIR da original no K total e na carga de uma roda
        col_fz, lin_fz = ae._colunas(ae.N_ALFA, True)["Fz_FL"], ae.PRIMEIRA_LINHA + 20
        sens[m] = {}
        for i in (1, 2):
            itens = []
            for nome, a, b in ((f"K total ({kt})", wv[ae.ABA19][kt].value, wv[f"M{i}_19"][kt].value),
                               (f"Fz_FL da 17 em a_y = 1,0 g ({col_fz}{lin_fz})", wv[ae.ABA17][f"{col_fz}{lin_fz}"].value,
                                wv[f"M{i}_17"][f"{col_fz}{lin_fz}"].value)):
                itens.append((nome, a, b, num(a) and num(b) and a != b))
            sens[m][f"i = {i} (K_φF × {1 + 0.05 * i:.2f})"] = itens
        wv.close()
    det = {}
    if "excel" in motores:
        for rot, *_ in var:
            det[rot] = [_excel_detalhado(arquivos[rot], aba_k, cel_k) for _ in range(repeticoes)]
            print(f"  excel (detalhe) {rot}: CalculateFull {_estat([a for a, _ in det[rot]])} s; "
                  f"troca do K_ARB {_estat([b for _, b in det[rot]])} s", flush=True)
    wbf = openpyxl.load_workbook(arquivos["0"])
    cel = {a: sum(1 for lin in wbf[a].iter_rows() for c in lin if isinstance(c.value, str) and c.value.startswith("="))
           for a in (ae.ABA16, ae.ABA17, ae.ABA18, ae.ABA19)}
    k0 = sum(1 for c in wbf[ae.ABA19][ae.LINHA_AUX19] if isinstance(c.value, str) and c.value.startswith("="))
    wbf.close()
    (_RAIZ / "build").mkdir(exist_ok=True)
    (_RAIZ / "build" / "medir-bruto.json").write_text(json.dumps(
        {"res": {m: {r: list(v[:3]) for r, v in d.items()} for m, d in res.items()}, "det": det}, indent=1), encoding="utf-8")
    escrever_documento(motores, var, res, det, conf, sens, cel, k0, erros_clone, repeticoes, rep_lo)


def _leitura(motores, var, res, det, cel):
    """Seção "Leitura dos números": só fatos calculados dos números desta execução (nenhum limiar, nenhuma conclusão)."""
    L = []
    mean = lambda v: sum(v) / len(v)
    if det:
        mc = max(((max(a for a, _ in det[r]), r, "CalculateFull") for r, *_ in var))
        me = max(((max(b for _, b in det[r]), r, "troca do K_ARB dianteiro") for r, *_ in var))
        maior = max(mc, me)
        L.append(f"- Maior recálculo medido no Excel (máximo das repetições): {maior[0]:.1f} s ({maior[2]}, variante {maior[1]}); "
                 f"CalculateFull máximo {mc[0]:.1f} s (variante {mc[1]}), troca do K_ARB máxima {me[0]:.1f} s (variante {me[1]}).")
        medias = {r: (mean([a for a, _ in det[r]]), mean([b for _, b in det[r]])) for r, *_ in var}
        for fam in ("P", "R", "RK"):
            cf = [medias[f"{fam}{n}"][0] for n in (1, 3, 5)]
            ed = [medias[f"{fam}{n}"][1] for n in (1, 3, 5)]
            cresce = all(x <= y for x, y in zip(cf, cf[1:])) and all(x <= y for x, y in zip(ed, ed[1:]))
            L.append(f"- Excel, variante {fam}, médias com 1, 3 e 5 linhas: CalculateFull {cf[0]:.2f} / {cf[1]:.2f} / {cf[2]:.2f} s; "
                     f"troca do K_ARB {ed[0]:.2f} / {ed[1]:.2f} / {ed[2]:.2f} s ("
                     + ("não decresce com as linhas" if cresce else "não cresce de forma monótona com as linhas") + ").")
    if "excel" in res:
        b = res["excel"]["0"][0]
        d = [mean(res["excel"][r][0]) - mean(b) for r, *_ in var if r != "0"]
        L.append(f"- Tempo de motor do Excel (abrir, recalcular, gravar): a base variou de {min(b):.1f} a {max(b):.1f} s entre as "
                 f"{len(b)} repetições, e a diferença das médias das variantes em relação à base ficou entre {min(d):+.1f} e {max(d):+.1f} s; "
                 "essa diferença está dentro da variação da própria base, então o tempo de motor do Excel não separa as variantes.")
    if "libreoffice" in res:
        lo = res["libreoffice"]
        t0 = mean(lo["0"][0])
        mx = max(((max(lo[r][0]), r) for r, *_ in var))
        dl = [(mean(lo[f"{f}{n}"][0]) - t0) / n for f in ("R", "RK") for n in (1, 3, 5)]
        L.append(f"- LibreOffice (tempo total, que inclui as duas partidas do programa): maior tempo medido {mx[0]:.1f} s (variante {mx[1]}); "
                 f"base {mean(lo['0'][0]):.1f} s; nas variantes R e RK a diferença por linha extra ficou entre {min(dl):.1f} e {max(dl):.1f} s.")
    L.append(f"- Tamanho: a 18 tem {cel[ae.ABA18]} células com fórmula e a 17 tem {cel[ae.ABA17]} (razão {cel[ae.ABA18] / cel[ae.ABA17]:.1f}). "
             f"A variante com mais fórmulas ({max(res[m][r][1] for m in res for r in res[m])}) ficou sem erro de fórmula: "
             f"{sum(res[m][r][2] for m in res for r in res[m])} erros somados em todas as medições.")
    return L


def escrever_documento(motores, var, res, det, conf, sens, cel, k0, erros_clone, repeticoes, rep_lo=None):
    """Escreve o documento inteiro a partir dos números da execução (sem edição à mão)."""
    mean = lambda v: sum(v) / len(v)
    L = ["# Incremento 4 (V4.1): custo de recálculo da tabela de troca da barra dianteira (portão)", "",
         "Gerado por `uv run python -X utf8 tests/test_workbook_v4_1.py --medir`. É uma medição feita antes de a tabela "
         "existir; ela não implementa a tabela. Os valores de K_φF das cópias são de TESTE: só dão um custo, não um "
         "resultado do carro.", "",
         "## O que foi medido e como", "",
         f"- Base: a V4.1 como gerada (V4.0 da tag `v4.0` + `aba_equilibrio.montar`), com as abas 16, 17, 18 e 19 "
         f"({cel[ae.ABA16]}, {cel[ae.ABA17]}, {cel[ae.ABA18]} e {cel[ae.ABA19]} células com fórmula). A linha \"0\" é essa "
         "base, que já traz uma análise na grade pedida e outra na refinada (as do K_ARB dianteiro da 06).",
         "- Uma linha da tabela de troca = uma análise de par completa com o K_ARB dianteiro trocado. Para medir, cada linha é "
         "uma cópia das abas 17 (e 18) dentro do mesmo arquivo (`M<i>_17`, `M<i>_18`), feita por `copy_worksheet` e reescrita "
         "no texto das fórmulas: os nomes do resumo da própria aba viram células locais, e o K_φF e o denominador da rolagem "
         "(16) passam a ler duas células próprias (H1 e I1), com K_φF·(1 + 0,05·i). Isso troca só a entrada da cadeia; o resto "
         "(cargas, termos do PAC2002, Fy por α, capacidade, bisseção da saturação) é o mesmo cálculo. A cópia i = 0 tem de "
         "reproduzir a original, e a cópia i ≥ 1 tem de diferir dela (conferência abaixo). `montar` não foi alterado.",
         "- Variantes: P = grade pedida (17) por linha; R = pedida + refinada (17 + 18) por linha; RK = R + o K da 1ª linha do "
         f"passo 1 (a linha de a_y = 0 do cálculo auxiliar da 19, {k0} células com fórmula, lendo a cópia da 17; sem a tabela "
         "de 0 a 0,4 g). \"Linhas\" são linhas extras além da base; o total de análises é 1 + linhas.",
         f"- Motores: {', '.join(motores)}; {repeticoes} recálculos por arquivo (mín / média / máx, em segundos; LibreOffice com "
         f"{rep_lo or repeticoes}). O tempo do motor é abrir, recalcular tudo (CalculateFull no Excel, calculateAll no "
         "LibreOffice), gravar e fechar; o do LibreOffice inclui as duas partidas do programa. Erros = células com #VALUE!, "
         "#DIV/0! etc. depois do recálculo.",
         "- No Excel, além disso: `CalculateFull` sozinho e o recálculo automático ao trocar o K_ARB dianteiro "
         "(06_SUSPENSION) numa cópia aberta, que é o que a equipe sentiria ao editar. O arquivo não é gravado.", ""]
    for m in motores:
        L += [f"## Resultados: {m}", "",
              "| Variante | Linhas extras | Análises pedida / refinada | Fórmulas | Erros | Motor mín / média / máx (s) | Δ média vs. base (s) | Δ por linha (s) |",
              "|---|---|---|---|---|---|---|---|"]
        t0 = mean(res[m]["0"][0])
        for rot, n, ref, k19 in var:
            ts, nf, ne, _ = res[m][rot]
            L.append(f"| {rot} | {n} | {1 + n} / {1 + n if ref or n == 0 else 1} | {nf} | {ne} | {_estat(ts)} | "
                     f"{mean(ts) - t0:+.1f} | {'-' if n == 0 else f'{(mean(ts) - t0) / n:.1f}'} |")
        if m == "excel":
            L += ["", "No Excel, a diferença do tempo de motor em relação à base (e por isso a coluna \"Δ por linha\") fica dentro "
                  "da variação da própria base entre repetições; não é interpretável como custo por linha. Use a tabela do "
                  "CalculateFull abaixo."]
        L.append("")
    if det:
        L += ["## Excel: CalculateFull sozinho e troca de uma entrada", "",
              "| Variante | CalculateFull mín / média / máx (s) | Troca do K_ARB dianteiro, recálculo automático, mín / média / máx (s) |",
              "|---|---|---|"]
        for rot, *_ in var:
            L.append(f"| {rot} | {_estat([a for a, _ in det[rot]])} | {_estat([b for _, b in det[rot]])} |")
        L.append("")
    L += ["## Conferência das cópias", "",
          "Arquivo RK3, depois do recálculo de cada motor. Com K_φF × 1 (i = 0), a cópia tem de dar o mesmo que a aba "
          "original (resumo da 17 e da 18, e o K total da linha de a_y = 0 da 19; células vazias dos dois lados não contam como "
          "iguais). Com i ≥ 1, a cópia tem de diferir da original: é a prova de que a troca de K_φF pegou.", ""]
    for m in motores:
        ok = all(x[4] for x in conf[m])
        L.append(f"- {m}, i = 0: {sum(1 for x in conf[m] if x[4])} de {len(conf[m])} itens iguais" + ("" if ok else " (DIVERGÊNCIA)"))
        for aba, k, a, b, igual in conf[m]:
            if not igual:
                L.append(f"  - {aba} {k}: original {a!r}, cópia {b!r}")
        for rot, v in sens[m].items():
            L.append(f"- {m}, {rot}: " + "; ".join(f"{nome} original {a!r}, cópia {b!r}" for nome, a, b, _ in v) +
                     f". {'Difere nos dois itens (K total e carga de uma roda na grade): a troca pegou' if all(x[3] for x in v) else 'NÃO difere em algum item: a troca NÃO pegou'}.")
    L += ["", "Células da linha de a_y = 0 da 19 que citam outra linha e por isso não foram copiadas: "
          f"{erros_clone.get('RK1') or 'nenhuma'}.", "",
          "## Leitura dos números", "",
          "Fatos desta execução; não são limiar nem recomendação (spec §9, item 10).", ""]
    L += _leitura(motores, var, res, det, cel)
    L += ["", "## Limites desta medição", "",
          "- Um computador, um Excel e um LibreOffice (os da máquina do projeto); o tempo da equipe depende do computador de cada um.",
          "- As cópias levam também as 10 células de pior origem (coluna E, linhas 4 a 13) de cada aba, que uma linha real talvez "
          "não precise; é pouco perto da grade.",
          "- A cópia da 19 cobre só o K da 1ª linha (parcelas em a_y = 0). Os ângulos de Richardson (kI) e a tabela de 0 a 0,4 g "
          "não entram.",
          "- Não há limiar de tempo registrado (spec §9, item 10): o tempo, sozinho, não decide o tamanho.", "",
          "## Decisão pedida ao usuário", "",
          "1. Quantos valores de K_ARB dianteiro a tabela de troca deve ter? A grade é de exibição, rotulada, e não uma meta. "
          "O valor digitado na 06 (×1) é a base e conta como um deles; o total de análises é 1 + linhas extras.",
          "2. Cada linha deve também medir a resolução (rodar a grade refinada, variantes R e RK), ou basta a grade pedida (P)?",
          "", "A resposta entra no EDR-060. A Task 5 (a tabela) só começa depois dela.", "",
          "## Decisão do usuário (2026-10-22)", "",
          "- 5 valores de K_ARB dianteiro: ×0,5; ×0,75; ×1; ×1,5; ×2 do valor digitado na 06 (o ×1 é a base). A grade é de exibição, "
          "rotulada, e não uma meta.",
          "- Cada linha mede a resolução e o K da 1ª linha (variante RK), porque o EDR-056 só admite NEUTRO dentro da resolução "
          "medida (ruling do controlador).", ""]
    caminho = _RAIZ / "docs" / "v4-1" / "inc4-viabilidade-tabela-de-troca.md"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(L), encoding="utf-8")
    print(f"documento: {caminho}")


if "--medir" in sys.argv:
    _arg = lambda n: int(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else None
    medir(_arg("--repeticoes") or 3, _arg("--repeticoes-lo"))
    sys.exit(0)


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
        caso = cp.caso_da_planilha_v41(copia, TIR, passo1=False)
    except ValueError as e:   # entradas inválidas: a planilha tem de mostrar o mesmo motivo, como N/A
        wb.close()
        ok = r16["status"] == str(e) and r16["ver"] == eq.NA and r16["mot"] == str(e)
        if prefixo is not None:
            ok = ok and str(e).startswith(prefixo)
        if not ok:
            falhas.append(f"{nome}: Python ValueError({e!s}); planilha situação={r16['status']!r} "
                          f"veredito={r16['ver']!r} motivo={r16['mot']!r}")
        ESPERADO6[nome] = {"txt_ver": eq.texto_veredito(SimpleNamespace(veredito=eq.NA, motivo=str(e)),
                                                        cp.pior_origem_do_caso_v41(copia))}
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
    R = valor(wb, ENT["R"])   # o tempo de volta usa o R digitado, com ou sem chave ligada
    if num(R) and R > 0 and res.ay_lim is not None:
        t_py = 2 * math.pi * math.sqrt(R / res.ay_lim)
        if not perto(r16["tvolta"], t_py):
            falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r} Python {t_py!r}")
    elif not (isinstance(r16["tvolta"], str) and r16["tvolta"].startswith("N/A")):
        falhas.append(f"{nome} tempo de volta: planilha {r16['tvolta']!r}, esperado N/A")
    wb.close()
    pior = cp.pior_origem_do_caso_v41(copia)
    if r16["pior"] != pior:
        falhas.append(f"{nome} pior origem: planilha {r16['pior']!r} Python {pior!r}")
    ESPERADO6[nome] = {"txt_ver": eq.texto_veredito(res, pior)}
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


# --- TC-WB41-005: passo 1 (19_EQ_LINEAR e K na 16) × equilibrio_linear.tabela_linear ---
TOL_K = 1e-6        # °/g (parcelas, k_total, k_inclinacao)
TOL_IGUAL = 1e-6    # relativo: k_pneus + k_deslocamento + k_camber = k_inclinacao na 1ª linha
TOL_ANG = 1e-8      # relativo a max(|α|, 1e-3): mesma raiz do Newton e da bissecção
DIF5 = {"k": [0.0, ""], "ang": [0.0, ""], "igual_planilha": [0.0, ""], "igual_python": [0.0, ""]}
ACHADOS5 = []       # identidade da 1ª linha acima de TOL_IGUAL (vai ao log; não decide o check: ver comparar_k)


def _maior(chave, x, onde):
    if x > DIF5[chave][0]:
        DIF5[chave][:] = [x, onde]


def k_igual(sh, py, onde) -> bool:
    """sh (planilha, rad/(m/s²) ou "N/A") e py (Python, rad/(m/s²) ou None) iguais a TOL_K em °/g."""
    if py is None:
        return sh == "N/A"
    if not num(sh):
        return False
    d = abs(el.para_graus_por_g(sh) - el.para_graus_por_g(py))
    _maior("k", d, onde)
    return d <= TOL_K


def comparar_k(nome, copia, falhas):
    """Compara o passo 1 da cópia recalculada com equilibrio_linear; devolve o resumo (texto) do caso."""
    wb = openpyxl.load_workbook(copia, data_only=True)
    lin = [{q: valor(wb, ae.NOME19[(q, k)]) for q in ae.QTD19} for k in range(ae.N_LIN19)]
    r16 = {k: valor(wb, ae.NOME16[k]) for k in ae.CHAVES16_K}
    pior16 = wb[ae.ABA16][f"E{ae.LINHAS16['kTot']}"].value
    pior19 = [wb[ae.ABA19][ae.celula_pior19(k)].value for k in range(ae.N_LIN19)]
    ws19 = wb[ae.ABA19]
    angs = [(ws19[ae.celula_aux19("ang_F", p)].value, ws19[ae.celula_aux19("ang_R", p)].value)
            for p in range(len(ae.PONTOS19))]
    wb.close()
    m_rs = None   # motivo do roll steer sem dado (só o passo 1 o usa): k_roll_steer e k_total N/A, o resto compara
    e = None      # motivo das entradas inválidas (texto)
    try:
        caso = cp.caso_da_planilha_v41(copia, TIR)
    except ValueError as erro:
        try:
            caso = cp.caso_da_planilha_v41(copia, TIR, passo1=False)
            m_rs = str(erro)
        except ValueError as erro2:
            caso, e = None, str(erro2)
    if caso is None:   # entradas inválidas: todo K N/A com o motivo da situação das entradas
        for k, ln in enumerate(lin):
            if not (ln["kTot"] == "N/A" and ln["mot"] == str(e) and ln["kI"] == "N/A" and ln["motI"] == str(e)):
                falhas.append(f"{nome} linha {k}: entradas inválidas ({e}); planilha K={ln['kTot']!r} motivo={ln['mot']!r} "
                              f"inclinação={ln['kI']!r} motivo={ln['motI']!r}")
        if not (r16["kTot"] == "N/A" and r16["kmot"] == str(e)):
            falhas.append(f"{nome} 16: K={r16['kTot']!r} motivo={r16['kmot']!r}, esperado N/A com {e}")
        ESPERADO6[nome]["txt_k"] = el.texto_k(SimpleNamespace(k_total=None, motivo=str(e)),
                                              cp.pior_origem_do_caso_v41(copia, linear=True))
        return f"{nome}: K N/A pelas entradas ({e})"
    pior = cp.pior_origem_do_caso_v41(copia, linear=True)
    tab = el.tabela_linear(caso, pior_origem=pior)
    if len(tab) != ae.N_LIN19:
        falhas.append(f"{nome}: tabela_linear com {len(tab)} linhas, planilha com {ae.N_LIN19}")
    for k, (ln, row) in enumerate(zip(lin, tab)):
        p = row["parcelas"]
        if m_rs is not None:   # o que o Python daria sem o dado: as duas parcelas None e o motivo no fim da lista
            p = dataclasses.replace(p, k_roll_steer=None, k_total=None,
                                    motivo="; ".join(m for m in (p.motivo, m_rs) if m))
        if k == 0:   # texto de exibição do K (TC-WB41-006, parte 2): o da 1ª linha, com o motivo já juntado
            ESPERADO6[nome]["txt_k"] = el.texto_k(p, pior)
        for q, py in (("kP", p.k_pneus), ("kT", p.k_transferencia), ("kD", p.k_deslocamento), ("kC", p.k_camber),
                      ("kRS", p.k_roll_steer), ("kTot", p.k_total), ("kI", row["k_inclinacao"])):
            if not k_igual(ln[q], py, f"{nome} linha {k} {q}"):
                falhas.append(f"{nome} linha {k} {q}: planilha {ln[q]!r} Python {py!r}")
        if p.k_total is None:
            if ln["kTotg"] != "N/A":
                falhas.append(f"{nome} linha {k} K em °/g: planilha {ln['kTotg']!r}, Python None")
        elif not (num(ln["kTotg"]) and abs(ln["kTotg"] - el.para_graus_por_g(p.k_total)) <= TOL_K):
            falhas.append(f"{nome} linha {k} K em °/g: planilha {ln['kTotg']!r} Python {el.para_graus_por_g(p.k_total)!r}")
        if ln["mot"] != (p.motivo or "-"):
            falhas.append(f"{nome} linha {k} motivo: planilha {ln['mot']!r} Python {p.motivo!r}")
        if ln["motI"] != (row["motivo_inclinacao"] or "-"):
            falhas.append(f"{nome} linha {k} motivo da inclinação: planilha {ln['motI']!r} Python {row['motivo_inclinacao']!r}")
        if not perto(ln["ay_g"], row["ay_g"], onde=f"{nome} a_y"):
            falhas.append(f"{nome} linha {k} a_y: planilha {ln['ay_g']!r} Python {row['ay_g']!r}")
        if pior19[k] != pior:
            falhas.append(f"{nome} linha {k} pior origem do K: planilha {pior19[k]!r} Python {pior!r}")
    # Newton (planilha) × bissecção (Python) nos 11 pontos: a mesma raiz, ou N/A onde o Python dá None
    for p_i, ay in enumerate(ae.PONTOS19_AY):
        py = el.angulos_necessarios(caso, ay)
        sh = angs[p_i]
        if py is None:
            if all(num(x) for x in sh):
                falhas.append(f"{nome} ponto {p_i}: Python sem ângulos (None), planilha {sh!r}")
            continue
        for e, a_sh, a_py in (("F", sh[0], py[0]), ("R", sh[1], py[1])):
            if not num(a_sh):
                falhas.append(f"{nome} ponto {p_i} α_{e}: planilha {a_sh!r}, Python {a_py!r}")
                continue
            d = abs(a_sh - a_py) / max(abs(a_py), 1e-3)
            _maior("ang", d, f"{nome} ponto {p_i} α_{e}")
            if d > TOL_ANG:
                falhas.append(f"{nome} ponto {p_i} α_{e}: planilha {a_sh!r} Python {a_py!r} (outra raiz?)")
    # Igualdade da 1ª linha (spec §6): na planilha e, para registro, no Python
    l0, p0 = lin[0], tab[0]["parcelas"]
    if m_rs is not None:
        p0 = dataclasses.replace(p0, k_roll_steer=None, k_total=None)
        if not (l0["kRS"] == "N/A" and l0["mot"] == m_rs and m_rs.endswith("a confirmar")):
            falhas.append(f"{nome}: roll steer sem dado; planilha k_roll_steer={l0['kRS']!r} motivo={l0['mot']!r}, "
                          f"esperado N/A com {m_rs!r}")
    if nome == "RS1" and not (num(l0["kRS"]) and l0["kRS"] != 0.0):
        falhas.append(f"RS1: k_roll_steer da planilha {l0['kRS']!r} deveria ser ≠ 0 (ε_f ≠ ε_r)")
    rel_sh = rel_py = None
    # O check é que a planilha reproduz o resíduo do Python: |resíduo_planilha − resíduo_Python| <= TOL_K em °/g, com
    # resíduo = k_inclinacao − (k_pneus + k_deslocamento + k_camber). A identidade em si, rel. <= TOL_IGUAL, só vai ao log
    # (achado da Task 3): o próprio Python não chega a 1e-6 (resíduo de truncamento do Richardson; com a h8, a downforce
    # 0,5·ρ·CzA·|a_y|·R tem a derivada lateral em a_y = 0 que a diferença central do deslocamento cancela e a inclinação,
    # de um lado só, vê). Com K(0) abaixo de TOL_K (carro simétrico: C2, C5) o relativo não tem sentido e o log mostra o
    # absoluto.
    def residuo(kp, kd, kc, ki):
        soma = kp + kd + kc
        if abs(el.para_graus_por_g(soma)) < TOL_K:
            return ki - soma, abs(el.para_graus_por_g(ki - soma)), "abs °/g"
        return ki - soma, abs(ki - soma) / abs(soma), "rel"
    crit_sh = crit_py = ""
    res_sh = res_py = None
    if all(num(l0[q]) for q in ("kP", "kD", "kC", "kI")):
        res_sh, rel_sh, crit_sh = residuo(l0["kP"], l0["kD"], l0["kC"], l0["kI"])
        if crit_sh == "rel":
            _maior("igual_planilha", rel_sh, nome)
    if None not in (p0.k_pneus, p0.k_deslocamento, p0.k_camber, tab[0]["k_inclinacao"]):
        res_py, rel_py, crit_py = residuo(p0.k_pneus, p0.k_deslocamento, p0.k_camber, tab[0]["k_inclinacao"])
        if crit_py == "rel":
            _maior("igual_python", rel_py, nome)
    if (res_sh is None) != (res_py is None):
        falhas.append(f"{nome}: igualdade da 1ª linha calculável só de um lado (planilha {res_sh!r}, Python {res_py!r})")
    elif res_sh is not None:
        d = abs(el.para_graus_por_g(res_sh) - el.para_graus_por_g(res_py))
        _maior("k", d, f"{nome} resíduo da igualdade")
        if d > TOL_K:
            falhas.append(f"{nome}: resíduo da igualdade da 1ª linha na planilha difere do Python em {d:.2e} °/g")
        if crit_sh == "rel" and rel_sh > TOL_IGUAL:
            ACHADOS5.append(f"{nome}: identidade da 1ª linha com rel. {rel_sh:.2e} > {TOL_IGUAL:g} (Python {rel_py:.2e})")
    # 16: o K da 1ª linha, V_char e V_crit
    for q in ("kP", "kT", "kD", "kC", "kRS", "kTot", "kI", "kTotg"):
        if r16[q] != l0[q]:
            falhas.append(f"{nome} 16 {q}: {r16[q]!r} ≠ 19 linha 0 {l0[q]!r}")
    if r16["kmot"] != l0["mot"]:
        falhas.append(f"{nome} 16 motivo do K: {r16['kmot']!r} ≠ 19 linha 0 {l0['mot']!r}")
    L = caso.cfg.wheelbase
    for q, py in (("vchar", None if p0.k_total is None else el.velocidade_caracteristica(L, p0.k_total)),
                  ("vcrit", None if p0.k_total is None else el.velocidade_critica(L, p0.k_total))):
        if not sat_igual(r16[q], py):
            falhas.append(f"{nome} 16 {q}: planilha {r16[q]!r} Python {py!r}")
    if pior16 != pior:
        falhas.append(f"{nome} 16 pior origem do K: planilha {pior16!r} Python {pior!r}")
    kt = p0.k_total
    krs = '' if p0.k_roll_steer in (None, 0.0) else f", k_roll_steer {el.para_graus_por_g(p0.k_roll_steer):+.4f} °/g"
    return (f"{nome}: K(0) = {'N/A' if kt is None else f'{el.para_graus_por_g(kt):+.4f} °/g'}{krs} "
            f"(motivo {l0['mot']!r}); "
            f"igualdade da 1ª linha: planilha {rel_sh if rel_sh is None else f'{rel_sh:.2e} ({crit_sh})'}, "
            f"Python {rel_py if rel_py is None else f'{rel_py:.2e} ({crit_py})'}")


# --- TC-WB41-006 (parte 1): tabela de troca da barra dianteira (20_EQ_TROCA) × Python ---
def caso_com_karb(copia, fator, passo1):
    """caso_da_planilha_v41 com o K_ARB dianteiro da 06 × fator (o K_φF sai de suspension_model.roll_stiffness_axle
    dentro de caso_planilha._cfg, e a instabilidade de rolagem é conferida com ele, na ordem da planilha). Troca o
    _cfg só durante a chamada; a cópia não muda."""
    orig = cp._cfg
    cp._cfg = lambda x: orig({**x, "KarbF": x["KarbF"] * fator})
    try:
        return cp.caso_da_planilha_v41(copia, TIR, passo1=passo1)
    finally:
        cp._cfg = orig


def linha_troca_python(copia, fator):
    """Esperado de uma linha da tabela: dict com as chaves de ae.TAB20 (None = N/A) e os motivos."""
    try:
        caso = caso_com_karb(copia, fator, False)
    except ValueError as e:   # entradas inválidas (ou instabilidade de rolagem com o K_φF da linha): tudo N/A
        return {"invalida": str(e)}
    m_rs = None
    try:
        p = el.parcelas_k(caso_com_karb(copia, fator, True), 0.0)
    except ValueError as e:   # só o roll steer sem dado: K N/A com o motivo no fim da lista (como comparar_k)
        p0 = el.parcelas_k(caso, 0.0)
        m_rs = str(e)
        p = dataclasses.replace(p0, k_roll_steer=None, k_total=None, motivo="; ".join(m for m in (p0.motivo, m_rs) if m))
    r = eq.analise_par(caso)
    kf, kr = caso.cfg.roll_stiffness_front, caso.cfg.roll_stiffness_rear
    return {"kphi": kf, "lam": kf / (kf + kr), "k": p.k_total, "kmot": p.motivo or "-", "sf": r.ay_sat_f, "sr": r.ay_sat_r,
            "aylim": r.ay_lim, "resol": r.resolucao_ms2, "ver": r.veredito, "cn": r.c_n, "mot": r.motivo or "-"}


def neutro_python(linhas):
    """a_y do acerto neutro pela regra da 20_EQ_TROCA (spec §5, item 4): o 1º par de linhas vizinhas, na ordem dos fatores,
    com as duas saturações em que S_r − S_f troca de sinal (interpolação linear de S_f e S_r entre elas) ou vale 0; sem
    troca, a linha NEUTRO de menor |S_r − S_f| (a 1ª no empate); senão None. Devolve (a_y, ramo, d por linha)."""
    d = [ln["sr"] - ln["sf"] if ln.get("sf") is not None and ln.get("sr") is not None else None for ln in linhas]
    for j, dj in enumerate(d):
        if dj is None:
            continue
        if dj == 0:
            return linhas[j]["sf"], f"zero na linha {j}", d
        if j + 1 < len(d) and d[j + 1] is not None and dj * d[j + 1] < 0:
            sf, sf1 = linhas[j]["sf"], linhas[j + 1]["sf"]
            return sf + (sf1 - sf) * dj / (dj - d[j + 1]), f"interpolação entre as linhas {j} e {j + 1}", d
    neu = [(abs(dj), j) for j, dj in enumerate(d) if dj is not None and linhas[j]["ver"] == eq.NEUTRO]
    if neu:
        j = min(neu)[1]
        return linhas[j]["aylim"], f"linha NEUTRO {j}", d
    return None, "fora da faixa", d


INTERPOLADOS6 = []   # casos em que o neutro saiu de uma interpolação estrita (exigido: pelo menos um)


def comparar_troca(nome, copia, falhas):
    """Compara a 20_EQ_TROCA da cópia recalculada com o Python; devolve o resumo (texto) do caso."""
    wb = openpyxl.load_workbook(copia, data_only=True)
    sh = [{q: valor(wb, ae.NOME20[(q, j)]) for q, _, _ in ae.TAB20 if q != "fator"} for j in range(len(ae.FATORES20))]
    custo = {q: valor(wb, n) for q, n in ae.NOME20_CUSTO.items()}
    status = valor(wb, ae.NOME16["status"])
    wb.close()
    py = [linha_troca_python(copia, f) for f in ae.FATORES20]
    pior = cp.pior_origem_do_caso_v41(copia, linear=True)
    for j, (s, p) in enumerate(zip(sh, py)):
        onde = f"{nome} linha {j} (×{ae.FATORES20[j]:g})"
        if s["pior"] != pior:
            falhas.append(f"{onde} pior origem: planilha {s['pior']!r} Python {pior!r}")
        if "invalida" in p:
            e = p["invalida"]
            if not (s["ver"] == eq.NA and s["mot"] == e and s["k"] == "N/A" and s["kmot"] == e):
                falhas.append(f"{onde}: Python N/A pelas entradas ({e}); planilha veredito={s['ver']!r} motivo={s['mot']!r} "
                              f"K={s['k']!r} motivo do K={s['kmot']!r}")
            continue
        for q in ("kphi", "lam"):
            if not perto(s[q], p[q], onde=f"{nome} troca {q}"):
                falhas.append(f"{onde} {q}: planilha {s[q]!r} Python {p[q]!r}")
        if not k_igual(s["k"], p["k"], f"{onde} K"):
            falhas.append(f"{onde} K: planilha {s['k']!r} Python {p['k']!r}")
        kg_py = None if p["k"] is None else el.para_graus_por_g(p["k"])
        if not (s["kg"] == "N/A" if kg_py is None else num(s["kg"]) and abs(s["kg"] - kg_py) <= TOL_K):
            falhas.append(f"{onde} K em °/g: planilha {s['kg']!r} Python {kg_py!r}")
        for q in ("sf", "sr", "aylim", "resol", "cn"):
            if not sat_igual(s[q], p[q]):
                falhas.append(f"{onde} {q}: planilha {s[q]!r} Python {p[q]!r}")
        for q, base in (("sfg", "sf"), ("srg", "sr"), ("aylimg", "aylim")):
            if not sat_igual(s[q], None if p[base] is None else p[base] / G):
                falhas.append(f"{onde} {q}: planilha {s[q]!r} Python {p[base]!r}/G")
        for q in ("ver", "mot", "kmot"):
            if s[q] != p[q]:
                falhas.append(f"{onde} {q}: planilha {s[q]!r} Python {p[q]!r}")
    # Cruzamento das saturações e custo do comportamento
    ayn, ramo, d = neutro_python(py)
    escala = max([abs(x) for ln in py for x in (ln.get("sf"), ln.get("sr")) if x is not None] or [1.0])
    for j, dj in enumerate(d):
        if not (sh[j]["d"] == "-" if dj is None else perto(sh[j]["d"], dj, escala, f"{nome} troca d")):
            falhas.append(f"{nome} linha {j} S_r − S_f: planilha {sh[j]['d']!r} Python {dj!r}")
    invalida = status != "OK"
    if invalida:
        ok = custo["ayn"] == "N/A" and custo["aynm"] == status and custo["perda"] == "N/A" and custo["perdam"] == status
        if not ok:
            falhas.append(f"{nome} custo com entradas inválidas: planilha {custo!r}, esperado N/A com {status!r}")
        return f"{nome}: tabela N/A pelas entradas ({status})"
    if ayn is None:
        if not (custo["ayn"] == "N/A" and custo["aynm"] == ae.M_NEUTRO_FORA and custo["perda"] == "N/A"
                and custo["perdam"] == ae.M_NEUTRO_FORA and custo["limiar"] == "N/A"):
            falhas.append(f"{nome} neutro fora da faixa: planilha {custo!r}")
    else:
        if not (perto(custo["ayn"], ayn, onde=f"{nome} a_y neutro") and custo["aynm"] == "-"
                and perto(custo["ayng"], ayn / G, onde=f"{nome} a_y neutro g")):
            falhas.append(f"{nome} a_y do neutro: planilha {custo['ayn']!r} / {custo['aynm']!r} Python {ayn!r} ({ramo})")
        lim = py[ae.J_ATUAL]["aylim"]
        if lim is None:
            m = "a_y limite do acerto atual N/A (16_EQUILIBRIO): " + py[ae.J_ATUAL]["mot"]
            if not (custo["perda"] == "N/A" and custo["perdam"] == m):
                falhas.append(f"{nome} custo: planilha {custo['perda']!r} / {custo['perdam']!r}, esperado N/A com {m!r}")
        else:
            e = max(abs(ayn), abs(lim))
            if not (perto(custo["perda"], ayn - lim, e, f"{nome} custo") and perto(custo["perdag"], (ayn - lim) / G, e / G)
                    and custo["perdam"] == "-" and custo["limiar"] == ae.M_LIMIAR):
                falhas.append(f"{nome} custo: planilha {custo['perda']!r} / {custo['perdam']!r} / {custo['limiar']!r} "
                              f"Python {ayn - lim!r}")
        if ramo.startswith("interpolação"):
            INTERPOLADOS6.append(nome)
    g = lambda x: "N/A" if x is None else f"{x / G:.4f} g"
    vs = "/".join(ln.get("ver", "N/A") for ln in py)
    return (f"{nome}: vereditos {vs}; neutro {g(ayn)} ({ramo}); custo "
            f"{'N/A' if ayn is None or py[ae.J_ATUAL].get('aylim') is None else g(ayn - py[ae.J_ATUAL]['aylim'])}")


# --- TC-WB41-006 (parte 2): textos de exibição da 16_EQUILIBRIO e do 14_DASHBOARD × equilibrio.texto_veredito/texto_k ---
TX, T09 = "● Dado do TX", "◐ Dado do T09"
PREFIXO = "DEMONSTRATIVO · "
# Textos fixos exigidos (plano, decisão 1; spec 7.3, item 5; decisões 2 e 3), escritos aqui à mão para não depender das
# constantes do gerador.
AVISO = "robustez ao pneu: ver relatório docs/v4-1/inc4-equilibrio-na-planilha.md (não recalculada na planilha)"
REGIMES = "regimes diferentes (Milliken p. 313-315)"
SENTIDO = ": um sentido por vez (decisão 2 do plano); troque o sentido da curva na entrada para ver o outro"
DIFERENCIAL = "Diferencial: aberto (h10)"


def _nomes_org() -> list[str]:
    """Todos os nomes de Origem (papel org) da V4.0 (data/nomes_V4_0.csv) e da V4.1 (entradas da 16)."""
    with open(_RAIZ / "data" / "nomes_V4_0.csv", encoding="utf-8", newline="") as f:
        v40 = [ln["nome"] for ln in csv.DictReader(f) if ln["papel"] == "org"]
    return v40 + [n.nome for n in ae.NOMES_V41 if n.papel == "org"]


def _txt(x, casas):
    """format(x, f'.{casas}f') com vírgula (o Python formata; a planilha usa FIXED)."""
    return format(x, f".{casas}f").replace(".", ",")


def _cf(ws, cel) -> list[tuple[str, str]]:
    """(fórmula, cores do preenchimento) das regras de formatação condicional que cobrem `cel`. As cores vêm de fgColor e
    bgColor: o Excel grava o preenchimento sólido do dxf nas duas; o LibreOffice, ao salvar a cópia, só no bgColor."""
    out = []
    for faixa, regras in ws.conditional_formatting._cf_rules.items():
        if cel in faixa.sqref:
            for r in regras:
                f = r.dxf.fill if r.dxf is not None else None
                cor = "" if f is None else f"{f.fgColor.rgb} {f.bgColor.rgb}"
                out.append((" ".join(r.formula or []), str(cor)))
    return out


def comparar_textos(nome, copia, falhas):
    """Textos da 16 e do dashboard contra ESPERADO6[nome] (equilibrio.texto_veredito e equilibrio_linear.texto_k com a
    pior origem do caso) e a linha de apoio contra os números da própria cópia formatados pelo Python."""
    esp = ESPERADO6.get(nome, {})
    n16 = {k: ae.NOME16.get(k) for k in ("txt_ver", "txt_k", "apoio", "txt_sent")}
    n14 = getattr(ae, "NOME14", {})
    if None in n16.values() or not n14:
        falhas.append(f"{nome}: a V4.1 não tem os textos de exibição (16: {n16}; 14_DASHBOARD: {n14})")
        return f"{nome}: sem textos de exibição"
    wb = openpyxl.load_workbook(copia, data_only=True)
    t16 = {k: valor(wb, n) for k, n in n16.items()}
    e16 = {k: wb[ae.ABA16][f"E{ae.LINHAS16[k]}"].value for k in ("txt_ver", "txt_k", "apoio")}
    t14 = {k: valor(wb, n) for k, n in n14.items()}
    num16 = {k: valor(wb, ae.NOME16[k]) for k in ("S_F_g", "S_R_g", "aylim_g", "cn", "tvolta")}
    num20 = {k: valor(wb, ae.NOME20_CUSTO[k]) for k in ("perdag", "limiar")}
    sentido = valor(wb, ENT["sentido"])
    wb.close()
    for k in ("txt_ver", "txt_k"):
        if t16[k] != esp.get(k):
            falhas.append(f"{nome} 16 {k}: planilha {t16[k]!r} Python {esp.get(k)!r}")
        if isinstance(t16[k], str) and "N/A: -" in t16[k]:
            falhas.append(f"{nome} 16 {k}: o \"-\" (sem motivo) apareceu como motivo: {t16[k]!r}")
    g3 = lambda x: f"{_txt(x, 3)} g" if num(x) else "N/A"
    custo = f"{_txt(num20['perdag'], 3)} g ({num20['limiar']})" if num(num20["perdag"]) else "N/A"
    apoio = (f"S_f {g3(num16['S_F_g'])} · S_r {g3(num16['S_R_g'])} · a_y limite {g3(num16['aylim_g'])} · C_N "
             f"{_txt(num16['cn'], 4) if num(num16['cn']) else 'N/A'} · custo do comportamento {custo} · Δt "
             f"{_txt(num16['tvolta'], 2) + ' s' if num(num16['tvolta']) else 'N/A'}")
    if t16["apoio"] != apoio:
        falhas.append(f"{nome} 16 linha de apoio: planilha {t16['apoio']!r}, esperado {apoio!r}")
    sent = {"Direita": "Curva à direita", "Esquerda": "Curva à esquerda"}.get(sentido)
    if sent is None or t16["txt_sent"] != sent + SENTIDO:
        falhas.append(f"{nome} 16 sentido: planilha {t16['txt_sent']!r} (entrada {sentido!r})")
    for k in ("txt_ver", "txt_k", "apoio", "txt_sent"):   # o dashboard repete a 16 (F19), com a mesma pior origem
        if t14.get(k) != t16[k]:
            falhas.append(f"{nome} 14_DASHBOARD {k}: {t14.get(k)!r} ≠ 16 {t16[k]!r}")
        if k in e16 and t14.get(k + "_pior") != e16[k]:
            falhas.append(f"{nome} 14_DASHBOARD pior origem de {k}: {t14.get(k + '_pior')!r} ≠ 16 {e16[k]!r}")
    return f"{nome}: {t16['txt_ver']!r} | {t16['txt_k'][:40]!r}…"


def conferir_fixos(copia, falhas):
    """Textos fixos e cores (na cópia com fórmulas): aviso de robustez ao lado do veredito, "regimes diferentes" ao lado do
    K, diferencial e sentido; formatação condicional azul (▲ PUSH) e laranja (▼ LOOSE) no veredito da 16 e do dashboard."""
    wb = openpyxl.load_workbook(copia)
    try:
        ws16, ws14 = wb[ae.ABA16], wb["14_DASHBOARD"]
        r_ver, r_k = ae.LINHAS16.get("txt_ver"), ae.LINHAS16.get("txt_k")
        if r_ver is None or r_k is None:
            falhas.append("16: sem as linhas de texto de exibição")
            return
        if ws16[f"F{r_ver}"].value != AVISO:
            falhas.append(f"16 F{r_ver} (ao lado do veredito): {ws16[f'F{r_ver}'].value!r}, esperado o aviso de robustez")
        if not str(ws16[f"F{r_k}"].value or "").startswith(REGIMES):
            falhas.append(f"16 F{r_k} (ao lado do K): {ws16[f'F{r_k}'].value!r}, esperado {REGIMES!r}…")
        textos14 = [str(c.value) for lin in ws14.iter_rows() for c in lin if isinstance(c.value, str)]
        for t in (AVISO, REGIMES, DIFERENCIAL):
            if not any(t in x for x in textos14):
                falhas.append(f"14_DASHBOARD sem o texto {t!r}")
        celulas = [(ws16, f"B{r_ver}")] + [(ws14, ae._destino(wb, ae.NOME14["txt_ver"])[1])]
        for ws, cel in celulas:
            regras = _cf(ws, cel)
            azul = any("▲ PUSH" in f and ae.COR_PUSH in c for f, c in regras)
            laranja = any("▼ LOOSE" in f and ae.COR_LOOSE in c for f, c in regras)
            if not (azul and laranja):
                falhas.append(f"{ws.title} {cel}: formatação condicional azul/laranja ausente ({regras})")
        for aba in ("21_COBERTURA", "22_CADEIA"):
            if aba not in wb.sheetnames:
                falhas.append(f"aba {aba} ausente")
        if any(isinstance(ws[c].value, str) and "TESTE" in ws[c].value for aux in ae.AUX20.values() for ws in [wb[aux]]
               for c in ("A1",)):
            falhas.append("título das abas 20a-20d ainda diz TESTE (marca de valor injetado só em cópia)")
    except AttributeError as e:
        falhas.append(f"textos fixos: {e}")
    finally:
        wb.close()


def casos_origem():
    """Pior origem INDEPENDENTE da função que gera a fórmula: na cópia ORG_TX, todas as células de Origem (nomes org_*)
    em "● Dado do TX"; na ORG_T09, o mesmo com a massa medida sem piloto (05_VEHICLE E30) em "◐ Dado do T09". Sobre o C3
    (PUSH) e o C3b (LOOSE). Valores de TESTE, só nas cópias."""
    todos_tx = {n: TX for n in _nomes_org()}
    return [("ORG_TX", {**C3, **todos_tx}, TX), ("ORG_T09", {**C3b, **todos_tx, "org_05_massa_medida_sem_piloto": T09}, T09)]


def esperado_origem(nome, copia, pior, falhas):
    """Textos esperados com a pior origem conhecida pela construção do caso (não pela fórmula): texto_veredito e texto_k
    com `pior`; a cópia tem de mostrar essa pior origem, sem prefixo com TX e com prefixo com T09."""
    res = eq.analise_par(cp.caso_da_planilha_v41(copia, TIR, passo1=False))
    p = el.parcelas_k(cp.caso_da_planilha_v41(copia, TIR), 0.0)
    ESPERADO6[nome] = {"txt_ver": eq.texto_veredito(res, pior), "txt_k": el.texto_k(p, pior)}
    for k, t in ESPERADO6[nome].items():
        if t.startswith(PREFIXO) != (pior != TX):
            falhas.append(f"{nome}: texto esperado {t!r} com o prefixo errado para a pior origem {pior!r}")
    wb = openpyxl.load_workbook(copia, data_only=True)
    sh = {k: wb[ae.ABA16][f"E{ae.LINHAS16[k]}"].value for k in ("ver", "kTot")}
    wb.close()
    if sh != {"ver": pior, "kTot": pior}:
        falhas.append(f"{nome}: pior origem da planilha {sh!r}, esperado {pior!r} em todas")
    for linear in (False, True):
        if cp.pior_origem_do_caso_v41(copia, linear=linear) != pior:
            falhas.append(f"{nome}: pior_origem_do_caso_v41(linear={linear}) ≠ {pior!r} (o gerador da fórmula diverge)")
    return res.veredito


# --- TC-WB41-004 e TC-WB41-005 (as mesmas cópias recalculadas) ---
falhas, resumos, tempos = [], [], []
falhas5, resumos5 = [], []
falhas6, resumos6 = [], []
falhas6b, resumos6b = [], []
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
        for aba in (ae.ABA16, ae.ABA17, ae.ABA18, ae.ABA19, ae.ABA20, *ae.AUX20.values()):
            n = sum(1 for lin in wbf[aba].iter_rows() for c in lin if isinstance(c.value, str) and c.value.startswith("="))
            print(f"  CÉLULAS com fórmula em {aba}: {n}")
        wbf.close()
    if nome == "C3":
        caso_c3 = cp.caso_da_planilha_v41(copia, TIR, passo1=False)
    resumos.append(comparar_caso(nome, copia, esperado, prefixo, falhas))
    resumos5.append(comparar_k(nome, copia, falhas5))
    resumos6.append(comparar_troca(nome, copia, falhas6))
    resumos6b.append(comparar_textos(nome, copia, falhas6b))
    if nome == "C1":
        conferir_fixos(copia, falhas6b)
    if nome == "RF3":
        caso = cp.caso_da_planilha_v41(copia, TIR, passo1=False)
        r = eq.analise_par(caso)
        _, _, sr2 = eq._varredura(caso, ae.AY_MAX_G, ae.PASSO_G / 2.0, 2 * ae.N_ALFA - 1)
        if not (r.ay_sat_r is not None and sr2.ay_sat is None and r.resolucao_ms2 == ae.PASSO_G * G):
            falhas.append(f"RF3: o caso não ficou com a traseira saturando só na grade pedida (S_r {r.ay_sat_r}, "
                          f"S_r refinada {sr2.ay_sat}, resolução {r.resolucao_ms2})")
for nome, alt, pior_esp in casos_origem():   # TC-WB41-006, parte 2: pior origem conhecida pela construção do caso
    copia = ae.copia_v41(Path(tempfile.mkdtemp()), alt, f"{nome}.xlsx")
    info, t = recalcular(copia)
    tempos.append(t)
    print(f"  {nome}: recalculado em {t:.1f} s no motor; {info['total_formulas']} fórmulas, {info['total_errors']} erros")
    if info["total_errors"]:
        falhas6b.append(f"{nome}: {info['total_errors']} erro(s) de fórmula {info['error_summary']}")
    v = esperado_origem(nome, copia, pior_esp, falhas6b)
    resumos6b.append(f"{comparar_textos(nome, copia, falhas6b)} (veredito {v}, pior origem {pior_esp})")
for s in resumos:
    print("  " + s)
print(f"  MAIOR diferença relativa planilha × Python ({MOTOR}): {DIF_MAX[0]:.2e} ({DIF_MAX[1]})")
print(f"  TEMPO de recálculo ({MOTOR}): por cópia da V4.1 mín {min(tempos):.1f} s, máx {max(tempos):.1f} s, "
      f"média {sum(tempos) / len(tempos):.1f} s; V4.0 da tag {t_b:.1f} s")
check("TC-WB41-004: análise de par em fórmulas (16-18) == equilibrio.analise_par nos casos C1-C5, C3b, C4b e nas "
      "variantes RF1/RF3 (Fz, γ, capacidade, motivo e folga por linha, rel. <= 1e-9; S_f, S_r, resolução, veredito, "
      "motivo, a_y limite, C_N, limitações, tempo de volta, pior origem); 0 erros de fórmula",
      not falhas, f"{len(falhas)} divergência(s): {falhas[:8]}")
for s5 in resumos5:
    print("  " + s5)
print(f"  MAIOR diferença do K planilha × Python ({MOTOR}): {DIF5['k'][0]:.2e} °/g ({DIF5['k'][1]}); ângulos (rel.): "
      f"{DIF5['ang'][0]:.2e} ({DIF5['ang'][1]}); igualdade da 1ª linha: planilha {DIF5['igual_planilha'][0]:.2e} "
      f"({DIF5['igual_planilha'][1]}), Python {DIF5['igual_python'][0]:.2e} ({DIF5['igual_python'][1]})")
for a5 in ACHADOS5:
    print(f"  ACHADO (não decide o check; o Python dá o mesmo): {a5}")
check("TC-WB41-005: passo 1 em fórmulas (19_EQ_LINEAR e o K na 16) == equilibrio_linear.tabela_linear nos casos C1-C5, "
      "C3b, C4b e nas variantes RF1/RF3/RS1/RS2 (parcelas, k_total e k_inclinacao por linha, |Δ| <= 1e-6 °/g; motivos; ângulos "
      "do Newton = bissecção, rel. <= 1e-8; resíduo da igualdade da 1ª linha = o do Python, |Δ| <= 1e-6 °/g; K, V_char, "
      "V_crit e pior origem na 16)",
      not falhas5, f"{len(falhas5)} divergência(s): {falhas5[:8]}")
for s6 in resumos6:
    print("  " + s6)
if not INTERPOLADOS6:
    falhas6.append("nenhum caso pôs o cruzamento das saturações dentro da tabela por interpolação (o TR1 devia pôr)")
check("TC-WB41-006 (parte 1): tabela de troca da barra dianteira (20_EQ_TROCA, K_ARB dianteiro × 0,5; 0,75; 1; 1,5; 2) == "
      "equilibrio.analise_par e equilibrio_linear.parcelas_k com o K_ARB trocado, em todos os casos (K_φF e λ_f rel. <= 1e-9; "
      "K |Δ| <= 1e-6 °/g; S_f, S_r, a_y limite, resolução, C_N, também em g; veredito e motivos exatos; pior origem); "
      "a_y do neutro pelo cruzamento das saturações (interpolação, nunca S_r − S_f) e custo = a_y do neutro − a_y limite "
      f"atual, \"limiar não definido\"; interpolação exercitada em {INTERPOLADOS6}",
      not falhas6, f"{len(falhas6)} divergência(s): {falhas6[:8]}")

for s6 in resumos6b:
    print("  " + s6)
check("TC-WB41-006 (parte 2): textos de exibição da 16_EQUILIBRIO e do 14_DASHBOARD == equilibrio.texto_veredito e "
      "equilibrio_linear.texto_k em todos os casos (sem \"-\" como motivo); sem o prefixo DEMONSTRATIVO com todas as "
      "Origens em \"● Dado do TX\" e com ele com a massa em \"◐ Dado do T09\" (pior origem pela construção do caso); linha "
      "de apoio e sentido da curva; aviso de robustez ao lado do veredito, \"regimes diferentes\" ao lado do K, "
      "diferencial; cores azul/laranja; abas 21 e 22",
      not falhas6b, f"{len(falhas6b)} divergência(s): {falhas6b[:8]}")

print("\n--- Resumo ---"); p = sum(1 for _, s in results if s == "PASS"); f = len(results) - p
print(f"{p} PASS, {f} FAIL, de {len(results)} testes")
sys.exit(1 if f else 0)
