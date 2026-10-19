"""
Teste de integração das abas de suspensão da planilha V3.0 (EDR-045 a EDR-048): Excel x Python.
Recalcula CÓPIAS pelo Excel (COM) ou pelo LibreOffice (EDR-044; recalculo_planilha.py); a entregue nunca é salva.
Uso: uv run python -X utf8 tests/test_workbook_suspensao.py [<V3_0.xlsx>]   (padrão: excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx)
Namespace TC-WB30-xxx. "Passou" = Excel reproduz o suspension_model/kinematics_model (tol. 1e-9 relativa), não validação física.
TC-WB30-010 a 013 (2ª rodada): origem de cada entrada, lista, cores e avisos (EDR-035) e valores derivados como fórmula (EDR-050).
"""
import csv, math, os, random, shutil, sys, tempfile, warnings
_TMP = tempfile.TemporaryDirectory(prefix="dds_teste_", ignore_cleanup_errors=True); tempfile.tempdir = _TMP.name
import openpyxl
from openpyxl.utils import get_column_letter
import suspension_model as sm
import kinematics_model as km
import recalculo_planilha as rc

MOTOR, DETALHE = rc.escolher()
if MOTOR is None:
    print(f"NÃO EXECUTÁVEL: nenhum motor de recálculo ({DETALHE})"); sys.exit(3)
print(f"MOTOR: {MOTOR} ({DETALHE})")
_RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
V30 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_RAIZ, "excel", "FSAE_EV_Suspension_Fase1_V3_0.xlsx")
results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL")); print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


# entradas (aba, célula) e o nome usado no cálculo Python
ENTRADAS = {
    "m": ("05_VEHICLE", "B4"), "h": ("05_VEHICLE", "B5"), "L": ("05_VEHICLE", "B6"), "tF": ("05_VEHICLE", "B7"), "tR": ("05_VEHICLE", "B8"),
    "a": ("05_VEHICLE", "B9"), "b": ("05_VEHICLE", "B10"), "muF": ("05_VEHICLE", "B14"), "muR": ("05_VEHICLE", "B15"),
    "huF": ("05_VEHICLE", "B16"), "huR": ("05_VEHICLE", "B17"),
    "KsF": ("06_SUSPENSION", "B4"), "KsR": ("06_SUSPENSION", "B5"), "MRF": ("06_SUSPENSION", "B6"), "MRR": ("06_SUSPENSION", "B7"),
    "KarbF": ("06_SUSPENSION", "B10"), "KarbR": ("06_SUSPENSION", "B11"), "zF": ("06_SUSPENSION", "B14"), "zR": ("06_SUSPENSION", "B15"),
    "FBf": ("06_SUSPENSION", "B36"), "TFr": ("06_SUSPENSION", "B37"), "KTF": ("06_SUSPENSION", "B47"), "KTR": ("06_SUSPENSION", "B48"),
    "zICF": ("07_KINEMATICS", "B10"), "dxF": ("07_KINEMATICS", "B11"), "zICR": ("07_KINEMATICS", "B12"), "dxR": ("07_KINEMATICS", "B13"),
    "ax": ("08_VEHICLE_STATE", "B4"), "ay": ("08_VEHICLE_STATE", "B5"), "DF": ("08_VEHICLE_STATE", "B8"), "bal": ("08_VEHICLE_STATE", "B9"),
    "fF": ("11_DESIGN", "B4"), "fR": ("11_DESIGN", "B5"), "lam": ("11_DESIGN", "B18"),
}
# EDR-050: estas entradas são calculadas na V3.0 a partir das parcelas abaixo; o teste lê o valor, mas só escreve as parcelas.
DERIVADAS = {"m", "a", "b", "huF", "huR", "ay"}
PARCELAS = {"m_med": ("05_VEHICLE", "B30"), "m_pil": ("05_VEHICLE", "B31"), "f": ("05_VEHICLE", "B32"),
            "D_F": ("05_VEHICLE", "B33"), "D_R": ("05_VEHICLE", "B34"), "ay_g": ("08_VEHICLE_STATE", "B11")}
SAIDAS = {   # nome -> (aba, célula)
    "msF": ("05_VEHICLE", "B25"), "msR": ("05_VEHICLE", "B26"), "a_s": ("05_VEHICLE", "B27"), "hs": ("05_VEHICLE", "B24"),
    "KwF": ("06_SUSPENSION", "B18"), "KwR": ("06_SUSPENSION", "B19"), "KphiF": ("06_SUSPENSION", "B22"), "KphiR": ("06_SUSPENSION", "B23"),
    "lamF": ("06_SUSPENSION", "B24"), "mcF": ("06_SUSPENSION", "B28"), "mcR": ("06_SUSPENSION", "B29"),
    "fnF": ("06_SUSPENSION", "B32"), "fnR": ("06_SUSPENSION", "B33"), "KRF": ("06_SUSPENSION", "B49"), "KRR": ("06_SUSPENSION", "B50"),
    "AD": ("06_SUSPENSION", "B40"), "AS": ("06_SUSPENSION", "B41"),
    "zs": ("09_LOADS", "B18"), "dFzF": ("09_LOADS", "B19"), "dFzR": ("09_LOADS", "B20"), "phi": ("09_LOADS", "B21"),
    "FL": ("09_LOADS", "B31"), "FR": ("09_LOADS", "B32"), "RL": ("09_LOADS", "B33"), "RR": ("09_LOADS", "B34"),
    "KwFd": ("11_DESIGN", "B8"), "KwRd": ("11_DESIGN", "B9"), "KsFd": ("11_DESIGN", "B10"), "KsRd": ("11_DESIGN", "B11"),
    "KphiFd": ("11_DESIGN", "B19"), "KarbFd": ("11_DESIGN", "B20"), "tc005": ("13_VALIDATION", "B6"),
}


def python_ref(x):
    """Mesmo cálculo pelos módulos Python (fonte da verdade do MODEL)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        KwF, KwR = sm.wheel_rate(x["KsF"], x["MRF"]), sm.wheel_rate(x["KsR"], x["MRR"])
    KphiF = sm.roll_stiffness_axle(KwF, x["tF"], x["KarbF"], x["KTF"])
    KphiR = sm.roll_stiffness_axle(KwR, x["tR"], x["KarbR"], x["KTR"])
    cfg = sm.VehicleConfig(mass_total=x["m"], cg_height=x["h"], wheelbase=x["L"], track_front=x["tF"], track_rear=x["tR"],
                           cg_to_front=x["a"], cg_to_rear=x["b"], unsprung_mass_front=x["muF"], unsprung_mass_rear=x["muR"],
                           unsprung_cg_height_front=x["huF"], unsprung_cg_height_rear=x["huR"], roll_center_front=x["zF"],
                           roll_center_rear=x["zR"], roll_stiffness_front=KphiF, roll_stiffness_rear=KphiR)
    ax_ = sm.sprung_mass_axle(cfg); mc = sm.sprung_mass_per_corner(cfg); lat = sm.lateral_dfz(cfg, x["ay"])
    fz = sm.combined_fz_corner(cfg, x["ax"], x["ay"], x["DF"], x["bal"], warn=False)
    KRF, KRR = sm.ride_rate(KwF, x["KTF"]), sm.ride_rate(KwR, x["KTR"])
    KwFd = sm.wheel_rate_from_target_frequency(x["fF"], mc["FL"], x["KTF"])
    KwRd = sm.wheel_rate_from_target_frequency(x["fR"], mc["RL"], x["KTR"])
    KphiFd = x["lam"] / (1 - x["lam"]) * KphiR
    ms = sm.sprung_mass_total(cfg)
    return {
        "msF": ax_["front"], "msR": ax_["rear"], "a_s": sm.sprung_cg_to_front(cfg), "hs": sm.sprung_cg_height(cfg),
        "KwF": KwF, "KwR": KwR, "KphiF": KphiF, "KphiR": KphiR, "lamF": KphiF / (KphiF + KphiR), "mcF": mc["FL"], "mcR": mc["RL"],
        "fnF": sm.natural_frequency(KRF, mc["FL"]), "fnR": sm.natural_frequency(KRR, mc["RL"]), "KRF": KRF, "KRR": KRR,
        "AD": km.anti_dive_percent_signed(x["zICF"] / x["dxF"], x["FBf"], x["L"], x["h"]),
        "AS": km.anti_squat_percent_signed((x["zICR"] - x["huR"]) / x["dxR"], x["TFr"], x["L"], x["h"]),
        "zs": lat["z_s"], "dFzF": lat["front_axle"], "dFzR": lat["rear_axle"], "phi": lat["roll_angle_rad"], **fz,
        "KwFd": KwFd, "KwRd": KwRd, "KsFd": sm.spring_rate_from_wheel_rate(KwFd, x["MRF"]), "KsRd": sm.spring_rate_from_wheel_rate(KwRd, x["MRR"]),
        "KphiFd": KphiFd, "KarbFd": sm.arb_required(KphiFd, KwF, x["tF"], x["KTF"]),
        "tc005": x["tF"] * lat["front_axle"] + x["tR"] * lat["rear_axle"] - x["m"] * x["ay"] * x["h"] - ms * 9.81 * lat["h2"] * lat["roll_angle_rad"],
    }


def scenario(mods):
    d = tempfile.mkdtemp(); f = os.path.join(d, "t.xlsx"); shutil.copy(V30, f)
    wb = openpyxl.load_workbook(f)
    for (aba, cel), val in mods.items():
        wb[aba][cel].value = val
    wb.save(f)
    info = rc.recalcular(f, MOTOR, 120)
    return info, openpyxl.load_workbook(f, data_only=True)


def ler_entradas(wbv):
    return {k: wbv[a][c].value for k, (a, c) in ENTRADAS.items()}


def comparar(wbv, x):
    ref = python_ref(x)
    pior, ruins = 0.0, []
    for k, (a, c) in SAIDAS.items():
        ev, pv = wbv[a][c].value, ref[k]
        if not isinstance(ev, (int, float)):
            ruins.append((k, ev)); continue
        escala = 1.0 if k == "tc005" else max(1.0, abs(pv))
        pior = max(pior, abs(ev - pv) / escala)
    return pior, ruins


# ---------- base ----------
info, wbv = scenario({})
check("TC-WB30-001: recálculo da V3.0 sem erros de fórmula (#REF!, #VALUE!, …)", info["total_errors"] == 0, f"fórmulas={info['total_formulas']}")
x0 = ler_entradas(wbv)
pior, ruins = comparar(wbv, x0)
check("TC-WB30-002: base — 05/06/09/11/13 do Excel == suspension_model/kinematics_model (33 saídas, tol. 1e-9)", pior < 1e-9 and not ruins, f"pior dif={pior:.2e}; {ruins}")
v = wbv["13_VALIDATION"]
check("TC-WB30-003: 13_VALIDATION: TC-004, TC-005 (com termo gravitacional) e λ_f+λ_r=1 PASS",
      v["B5"].value == "PASS" and v["B7"].value == "PASS" and abs(v["B8"].value - 1) < 1e-12, f"TC-005 resíduo={v['B6'].value:.2e}")
check("TC-WB30-004: K_T de 06_SUSPENSION é o VERTICAL_STIFFNESS do .tir provisório (120312 N/m) e está rotulado PROVISÓRIO",
      x0["KTF"] == x0["KTR"] == 120312.0 and "PROVISÓRIO" in str(wbv["06_SUSPENSION"]["A46"].value))

# ---------- EDR-050: valores derivados como fórmula, com as parcelas como entrada ----------
wbf = openpyxl.load_workbook(V30)
DERIV = {("05_VEHICLE", "B4"): ("$B$30", "$B$31"), ("05_VEHICLE", "B9"): ("$B$6", "$B$32"), ("05_VEHICLE", "B10"): ("$B$6", "$B$32"),
         ("05_VEHICLE", "B16"): ("$B$33",), ("05_VEHICLE", "B17"): ("$B$34",), ("08_VEHICLE_STATE", "B5"): ("$B$11",)}
eh_formula = all(str(wbf[a][c].value).startswith("=") and all(r in wbf[a][c].value for r in refs) for (a, c), refs in DERIV.items())
v5, v8 = wbv["05_VEHICLE"], wbv["08_VEHICLE_STATE"]
esperado = {"B4": 316.5, "B9": 1.594 * (1 - 0.4843), "B10": 1.594 * 0.4843, "B16": 0.254, "B17": 0.254}
dif = max([abs(v5[k].value - e_) for k, e_ in esperado.items()] + [abs(v8["B5"].value - 11.772)])
parcelas = [v5["B30"].value, v5["B31"].value, v5["B32"].value, v5["B33"].value, v5["B34"].value, v8["B11"].value]
check("TC-WB30-013: B4, B9, B10, B16, B17 (05) e B5 (08) são fórmula das parcelas e reproduzem os valores digitados antes "
      "(a e b só diferem pelo arredondamento antigo, < 1e-5 m)",
      eh_formula and dif < 1e-12 and parcelas == [248.5, 68, 0.4843, 20, 20, 1.2]
      and abs(v5["B9"].value - 0.82203) < 1e-5 and abs(v5["B10"].value - 0.77197) < 1e-5, f"dif={dif:.1e}; parcelas={parcelas}")

# ---------- perturbações aleatórias de todas as entradas ----------
rnd = random.Random(20261019)
pior_all, ruins_all = 0.0, []
p0 = {k: wbv[a][c].value for k, (a, c) in PARCELAS.items()}
for s in range(3):
    x = {k: (v_ * rnd.uniform(0.85, 1.15) if isinstance(v_, (int, float)) else v_) for k, v_ in x0.items()}
    p = {k: v_ * rnd.uniform(0.85, 1.15) for k, v_ in p0.items()}   # a + b = L vem da fórmula (EDR-050)
    p["ay_g"] = p0["ay_g"] * rnd.choice((-1, 1)) * rnd.uniform(0.3, 1.1); x["ax"] = x0["ax"] * rnd.uniform(-1, 1)
    x["bal"] = min(max(x["bal"], 0.0), 1.0); x["lam"] = min(max(x["lam"], 0.3), 0.7)
    mods = {ENTRADAS[k]: x[k] for k in x if k not in DERIVADAS and ENTRADAS[k] != ("07_KINEMATICS", "B14")}
    mods.update({PARCELAS[k]: v_ for k, v_ in p.items()})
    info, wbv = scenario(mods)
    x["huR"] = wbv["05_VEHICLE"]["B17"].value
    p_, r_ = comparar(wbv, ler_entradas(wbv))
    pior_all = max(pior_all, p_); ruins_all += r_ + ([("erros", info["total_errors"])] if info["total_errors"] else [])
check("TC-WB30-005: 3 cenários com TODAS as entradas perturbadas (±15 %, a_y com os dois sinais; derivadas pelas parcelas): Excel == Python",
      pior_all < 1e-9 and not ruins_all, f"pior dif={pior_all:.2e}; {ruins_all}")

# ---------- casos-limite ----------
info, wbv = scenario({("08_VEHICLE_STATE", "B11"): 0.0})   # a_y em g (EDR-050)
l = wbv["09_LOADS"]
check("TC-WB30-006: a_y = 0 -> φ = 0 e ΔFz lateral = 0 nos dois eixos", l["B21"].value == 0 and l["B19"].value == 0 and l["B20"].value == 0)
info, wbv = scenario({("06_SUSPENSION", "B47"): 1e15, ("06_SUSPENSION", "B48"): 1e15})
s_ = wbv["06_SUSPENSION"]
kphi_rig = s_["B20"].value + s_["B10"].value
check("TC-WB30-007: pneu quase rígido (K_T = 1e15) recupera K_φ = K_W·t²/2 + K_ARB e K_R = K_W (forma da V2.4)",
      abs(s_["B22"].value / kphi_rig - 1) < 1e-9 and abs(s_["B49"].value / s_["B18"].value - 1) < 1e-9)
info, wbv = scenario({("06_SUSPENSION", "B4"): 100.0, ("06_SUSPENSION", "B5"): 100.0,
                      ("06_SUSPENSION", "B10"): 0.0, ("06_SUSPENSION", "B11"): 0.0})
check("TC-WB30-008: rigidez de rolagem abaixo de m_s·g·h2 -> φ = 'N/A - instabilidade…' e ΔFz lateral 'N/A' (sem número falso)",
      str(wbv["09_LOADS"]["B21"].value).startswith("N/A - instabilidade") and wbv["09_LOADS"]["B19"].value == "N/A")
info, wbv = scenario({("07_KINEMATICS", "B11"): 2.5})
check("TC-WB30-009: IC lateral dianteiro À FRENTE do contact patch -> anti-dive negativo (pro-dive, Milliken p. 620)",
      wbv["06_SUSPENSION"]["B40"].value < 0, f"AD={wbv['06_SUSPENSION']['B40'].value:.2f} %")

# ---------- EDR-035: origem de cada entrada, lista, cores e avisos ----------
TX, T09, TTC, EST, ARB, CONF = ("● Dado do TX", "◐ Dado do T09", "◐ Provisório (.tir TTC)", "○ Estimativa",
                                "○ Arbitrário / demonstrativo", "? A confirmar")
ROTULOS = [TX, T09, TTC, EST, ARB, CONF]
ABAS = ("05_VEHICLE", "06_SUSPENSION", "07_KINEMATICS", "08_VEHICLE_STATE", "11_DESIGN")
entradas = [(a, r) for a in ABAS for r in range(3, wbf[a].max_row + 1)
            if isinstance(wbf[a][f"B{r}"].value, (int, float)) and not isinstance(wbf[a][f"B{r}"].value, bool)]
sem = [(a, r) for a, r in entradas if wbf[a][f"E{r}"].value not in ROTULOS or not str(wbf[a][f"F{r}"].value or "").strip()]
t10 = wbf["10_TIRE"]
sem += [("10_TIRE", r) for r in (23, 24, 25, 84) if t10[f"I{r}"].value not in ROTULOS or not t10[f"J{r}"].value]
calc_sem_fonte = [(a, c) for (a, c) in DERIV if not wbf[a][f"F{c[1:]}"].value or wbf[a][f"E{c[1:]}"].value is not None]
coment = [(a, r) for a, r in entradas if wbf[a][f"B{r}"].comment is not None]
# Rastreabilidade: a origem de cada entrada que é raiz no mapa da auditoria V2.1 segue a categoria do mapa (nada inferido).
MAPA = {"ARBITRARIO": ARB, "PLACEHOLDER": ARB, "ALVO_DEMONSTRATIVO": ARB, "ESTIMATIVA_NAO_MEDIDA": EST, "HIPOTESE_CONGELADA_V1": EST,
        "CASO_DE_CARGA_SEM_PROVENIENCIA": EST, "REAL_OUTRO_VEICULO_T09": T09, "REAL_OUTRO_VEICULO_E03": T09,
        "REAL_OUTRO_VEICULO_PROVISORIO": TTC}
EXCECOES = {("06_SUSPENSION", "B14"): T09, ("06_SUSPENSION", "B15"): T09}   # RC = T09/E03 (usuário, 2026-10-19; EDR-035)
raizes = {}
with open(os.path.join(_RAIZ, "data", "placeholder-dependency-map-V2.1.csv"), encoding="utf-8") as fh:
    for lin in csv.DictReader(fh):
        for campo in ("raizes_T1_nao_dado_do_veiculo", "raizes_T2_nao_validado_para_TX"):
            for item in filter(None, (s.strip() for s in lin[campo].split(";"))):
                cel, cat = item[:-1].split("[")
                raizes[tuple(cel.split("!"))] = cat
diverge = [(k, cat, wbf[k[0]][f"E{k[1][1:]}"].value) for k, cat in raizes.items()
           if not str(wbf[k[0]][k[1]].value).startswith("=")
           and wbf[k[0]][f"E{k[1][1:]}"].value != EXCECOES.get(k, MAPA[cat])]
check("TC-WB30-010: toda entrada numérica (05, 06, 07, 08, 11; casos e coeficientes da 10_TIRE) tem Origem da lista e Fonte "
      "visíveis, sem comentário duplicado; calculadas sem lista e com Fonte; origens = categorias da auditoria V2.1",
      not sem and not calc_sem_fonte and not coment and not diverge and len(raizes) == 27,
      f"entradas={len(entradas)}; sem origem={sem}; calc={calc_sem_fonte}; coment={coment}; diverge={diverge}; raízes={len(raizes)}")

nome = wbf.defined_names.get("Origens")
lista_ok = nome is not None and [wbf["00_README"][f"A{r}"].value for r in range(43, 49)] == ROTULOS \
    and nome.attr_text == "'00_README'!$A$43:$A$48"
cobertas = set()
for a in ABAS + ("10_TIRE",):
    for dv in wbf[a].data_validations.dataValidation:
        if dv.type == "list" and dv.formula1 == "=Origens":
            cobertas |= {(a, f"{get_column_letter(c_)}{r_}") for rng in dv.sqref.ranges for r_, c_ in rng.cells}
fora = [(a, f"E{r}") for a, r in entradas if (a, f"E{r}") not in cobertas] + \
       [("10_TIRE", f"I{r}") for r in (23, 24, 25, 84) if ("10_TIRE", f"I{r}") not in cobertas]
amarelo = [(w.title, c.coordinate) for w in wbf.worksheets for row in w.iter_rows() for c in row
           if c.fill.fill_type and c.fill.fgColor.rgb == "00FFF2CC"]
m = wbf["00_README"]
estilo = lambda c: (c.fill.fill_type, c.fill.fgColor.rgb if c.fill.fill_type else None, c.font.color.rgb if c.font.color else None)
legenda = [estilo(m[f"A{r}"]) == estilo(wbf[a][c]) for r, (a, c) in zip(range(16, 20), (("05_VEHICLE", "B14"), ("05_VEHICLE", "B6"),
                                                                                        ("06_SUSPENSION", "B14"), ("05_VEHICLE", "B23")))]
check("TC-WB30-011: lista 'Origens' (00_README A43:A48, 6 rótulos) em toda célula de Origem; nenhum fundo amarelo; "
      "amostras da legenda com o estilo real das células e sem a classe 'Amarelo'",
      lista_ok and not fora and not amarelo and all(legenda) and not any("Amarelo" in str(m[f"A{r}"].value) for r in range(16, 21)),
      f"lista={lista_ok}; fora={fora}; amarelo={amarelo[:5]}; legenda={legenda}")

# Avisos: regras na planilha + semântica pelas mesmas fórmulas avaliadas pelo motor de recálculo numa cópia.
regras_ok, ocultas_ok, copia_ok = True, True, True
for a in ABAS:
    ws_ = wbf[a]
    fe = {str(k.sqref): [r.formula[0] for r in v] for k, v in ws_.conditional_formatting._cf_rules.items()}
    e_, f_ = [v for k, v in fe.items() if k.startswith("E3:")], [v for k, v in fe.items() if k.startswith("F3:")]
    regras_ok &= bool(e_) and e_[0][0] == "AND(ISNUMBER($G3),$B3<>$G3,$E3=$H3)" and len(e_[0]) == 5 \
        and bool(f_) and f_[0] == ['AND(LEFT($E3,1)="●",LEN(TRIM($F3))=0)']
    ocultas_ok &= ws_.column_dimensions["G"].hidden and ws_.column_dimensions["H"].hidden
    copia_ok &= all(ws_[f"G{r}"].value == ws_[f"B{r}"].value and ws_[f"H{r}"].value == ws_[f"E{r}"].value for aa, r in entradas if aa == a)
alerta = lambda r: f"=AND(ISNUMBER($G{r}),$B{r}<>$G{r},$E{r}=$H{r})"
falta = lambda r: f'=AND(LEFT($E{r},1)="●",LEN(TRIM($F{r}))=0)'
mods = {("05_VEHICLE", "B14"): 20.0,                                            # valor mudou, origem igual -> aviso
        ("05_VEHICLE", "B15"): 20.0, ("05_VEHICLE", "E15"): TX, ("05_VEHICLE", "F15"): None,   # origem trocada; TX sem fonte
        ("05_VEHICLE", "Z14"): alerta(14), ("05_VEHICLE", "Z15"): alerta(15), ("05_VEHICLE", "Z5"): alerta(5),
        ("05_VEHICLE", "AA14"): falta(14), ("05_VEHICLE", "AA15"): falta(15), ("05_VEHICLE", "AA5"): falta(5)}
info, wbv = scenario(mods)
z = [wbv["05_VEHICLE"][c].value for c in ("Z14", "Z15", "Z5", "AA14", "AA15", "AA5")]
check("TC-WB30-012: cores e avisos da Origem (E) e da Fonte (F) nas 5 abas, G/H ocultas = valor e origem da geração; "
      "semântica: valor mudou com a mesma origem -> aviso; origem trocada -> sem aviso; Dado do TX sem fonte -> aviso",
      regras_ok and ocultas_ok and copia_ok and z == [True, False, False, False, True, False] and info["total_errors"] == 0,
      f"regras={regras_ok}; ocultas={ocultas_ok}; G/H={copia_ok}; avaliação={z}")

print("\n--- Resumo ---"); p = sum(1 for _, s in results if s == "PASS"); f = len(results) - p
print(f"{p} PASS, {f} FAIL, de {len(results)} testes")
sys.exit(1 if f else 0)
