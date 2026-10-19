"""Gera FSAE_EV_Suspension_Fase1_V2_4.xlsx a partir da V2.1. Só adições/ substituição da aba 10_TIRE; as 88 fórmulas existentes não são tocadas."""
import argparse, copy, math, sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.comments import Comment
import tire_model_V2_4 as t

# Portabilidade (commit 1, SPEC R3): os caminhos fixos do sandbox viraram argumentos
# com padrão relativo a este script. A saída padrão fica em build/, nunca sobre a entregue.
HERE = Path(__file__).resolve().parent
_ap = argparse.ArgumentParser()
_ap.add_argument("out", nargs="?", default=str(HERE.parent / "build" / "FSAE_EV_Suspension_Fase1_V2_4.xlsx"))
_ap.add_argument("--src", default=str(HERE.parent / "excel" / "FSAE_EV_Suspension_Fase1_V2.1.xlsx"))
_ap.add_argument("--tir", default=str(HERE / "Hoosier_R25B_13x7_TTC_provisional.tir"))
_ap.add_argument("--layout", default=None, help="padrão: layout_V2_4.json na pasta de OUT")
_args = _ap.parse_args()
SRC = _args.src
OUT = _args.out
TIR = _args.tir
LAYOUT = _args.layout or str(Path(OUT).parent / "layout_V2_4.json")
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
ds = t.load_dataset(TIR, source_axis_system="SAE_CALSPAN")
P = ds.p

wb = openpyxl.load_workbook(SRC)
old = wb["10_TIRE"]
idx = wb.sheetnames.index("10_TIRE")
tab = old.sheet_properties.tabColor
wb.remove(old)
ws = wb.create_sheet("10_TIRE", idx)
if tab is not None:
    ws.sheet_properties.tabColor = tab
ws.sheet_view.showGridLines = False

# ---------------- estilos (replicam as convenções da V2.1) ----------------
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
F_TITLE = Font(name="Arial", size=14, bold=True, color="FFFFFF"); FILL_TITLE = PatternFill("solid", fgColor="1F4E78")
F_SEC = Font(name="Arial", size=11, bold=True, color="FFFFFF"); FILL_SEC = PatternFill("solid", fgColor="2E75B6")
F_LBL = Font(name="Arial", size=10); F_NOTE = Font(name="Arial", size=10, italic=True)
F_META = Font(name="Arial", size=9, italic=True, color="808080")
F_INPUT = Font(name="Arial", size=10, color="0000FF"); FILL_YEL = PatternFill("solid", fgColor="FFF2CC")
F_REF = Font(name="Arial", size=10, color="007A5E")
F_CALC = Font(name="Arial", size=10, color="000000"); FILL_CALC = PatternFill("solid", fgColor="F2F2F2")
F_PROV = Font(name="Arial", size=10, bold=True, color="C55A11"); FILL_PROV = PatternFill("solid", fgColor="FCE4D6")
F_BOLD = Font(name="Arial", size=10, bold=True)
NF = "0.0000"
COLS = ["B", "C", "D", "E", "F"]          # FL FR RL RR VERIF
LAST = "I"


def put(cell, value, font=F_LBL, fill=None, nf=None, border=False, align=None):
    c = ws[cell]; c.value = value; c.font = font
    if fill: c.fill = fill
    if nf: c.number_format = nf
    if border: c.border = BORDER
    if align: c.alignment = align
    return c


def note(cell, text, w=340, h=150):
    cm = Comment(text, "Sistema_DDS V2.2"); cm.width, cm.height = w, h; ws[cell].comment = cm


def merge_row(r, text, font, fill=None, height=None):
    ws.merge_cells(f"A{r}:{LAST}{r}")
    put(f"A{r}", text, font, fill, align=Alignment(vertical="center", wrap_text=(font is not F_TITLE)))
    if fill:
        for col in "ABCDEFGHI":
            ws[f"{col}{r}"].fill = fill
    if height: ws.row_dimensions[r].height = height


for col, w in zip("ABCDEFGHI", (66, 14, 14, 14, 14, 14, 10, 12, 62)):
    ws.column_dimensions[col].width = w

# ---------------- layout: atribuição de linhas ----------------
rows = {}
r = 1
merge_row(1, "10_TIRE", F_TITLE, FILL_TITLE, 22)
r = 3
merge_row(r, "Aviso — DATASET PROVISÓRIO (dado de desenvolvimento): os coeficientes abaixo vêm de um .tir TTC recebido para permitir o desenvolvimento; "
             "NÃO correspondem necessariamente ao pneu que será usado. Nada nesta aba é medição ou resultado do carro (Guia: o workbook não apresenta μ próprio como medido).",
          F_PROV, FILL_PROV, 44)


def add(name, nrows=1):
    global r
    rows[name] = r; r += nrows


def sec(title):
    global r
    r += 1
    merge_row(r, title, F_SEC, FILL_SEC); r += 1


sec("Dataset (metadados) — SUS-501/502/503, DR-011 e DR-013")
for n in ("m_file", "m_src", "m_fmt", "m_rev", "m_side", "m_conv", "m_axis", "m_sa", "m_sf", "m_sg", "m_level", "m_eqv", "m_valid"):
    add(n)
sec("Entradas por canto (FL, FR, RL, RR) e caso de verificação (VERIF) — α, γ, κ são DEMONSTRATIVOS")
add("hdr"); 
for n in ("side", "fz", "alpha", "camber", "kappa"):
    add(n)
add("status")
sec("Resultados — SUS-501 (Fy), SUS-502 (Fx), SUS-503 (μ efetivo) — convenção do PROJETO")
for n in ("o_fx", "o_fy", "o_mu", "o_fyfile"):
    add(n)
sec("Cálculo — conversões e carga normalizada")
for n in ("mir", "a_rad", "g_rad", "a_eq", "g_use", "dfz"):
    add(n)
sec("Cálculo — Fx puro (Fx0), forma PAC2002/MF 5.2")
for n in ("SHx", "kx", "Cx", "mux", "Dx", "Ex", "Kx", "Bx", "SVx", "Fx0"):
    add(n)
sec("Cálculo — Fy puro (Fy0)")
for n in ("gy", "Ky", "SHy", "ay", "Cy", "muy", "Dy", "Ey", "By", "SVy", "Fy0"):
    add(n)
sec("Cálculo — combinação Fx×Fy (Gxα, Gyκ, SVyκ)")
for n in ("SHxa", "Bxa", "Cxa", "Exa", "Gxa_n", "Gxa_d", "Gxa", "SHyk", "Byk", "Cyk", "Eyk", "Gyk_n", "Gyk_d", "Gyk", "DVyk", "SVyk"):
    add(n)
r += 1
merge_row(r, "Coeficientes do dataset (REFERENCE provisório) — .tir PAC2002; unidades do arquivo: N, m, rad. Mx, My, Mz, relaxamento e raio carregado NÃO foram importados (fora do escopo SUS-501..503).", F_SEC, FILL_SEC, 30)
r += 1
PARAMS = [
    ("FNOMIN", "N", "Carga normal nominal"), ("FZMIN", "N", "Carga mínima permitida"), ("FZMAX", "N", "Carga máxima permitida"),
    ("ALPMIN", "rad", "Ângulo de deriva mínimo válido"), ("ALPMAX", "rad", "Ângulo de deriva máximo válido"),
    ("CAMMIN", "rad", "Camber mínimo válido"), ("CAMMAX", "rad", "Camber máximo válido"),
    ("KPUMIN", "-", "Slip ratio mínimo válido"), ("KPUMAX", "-", "Slip ratio máximo válido"),
    ("IP", "Pa", "Pressão de inflação"), ("IP_NOM", "Pa", "Pressão nominal"),
] + [(k, "-", "Fator de escala") for k in ("LFZO", "LCX", "LMUX", "LEX", "LKX", "LHX", "LVX", "LGAX", "LCY", "LMUY", "LEY", "LKY", "LHY", "LVY", "LGAY", "LXAL", "LYKA", "LVYKA")]
PARAMS += [(k, "-", "Coeficiente longitudinal/combinado Fx") for k in ("PCX1", "PDX1", "PDX2", "PDX3", "PEX1", "PEX2", "PEX3", "PEX4", "PKX1", "PKX2", "PKX3", "PHX1", "PHX2", "PVX1", "PVX2", "RBX1", "RBX2", "RCX1", "REX1", "REX2", "RHX1")]
PARAMS += [(k, "-", "Coeficiente lateral/combinado Fy") for k in ("PCY1", "PDY1", "PDY2", "PDY3", "PEY1", "PEY2", "PEY3", "PEY4", "PKY1", "PKY2", "PKY3", "PHY1", "PHY2", "PHY3", "PVY1", "PVY2", "PVY3", "PVY4", "RBY1", "RBY2", "RBY3", "RCY1", "REY1", "REY2", "RHY1", "RHY2", "RVY1", "RVY2", "RVY3", "RVY4", "RVY5", "RVY6")]
PARAMS += [(k, "-", "Efeito de pressão (deve ser 0 — não implementado)") for k in t.PRESSURE_KEYS]
prow = {}
for name, unit, desc in PARAMS:
    prow[name] = r; r += 1
prow["EPS"] = r; r += 1
end_params = r - 1


def p(name):
    return f"$B${prow[name]}"


def R(c, name):
    return f"{c}${rows[name]}"


def G(c, expr):
    return f'=IF({R(c, "status")}<>"OK","N/A",{expr})'


# ---------------- metadados ----------------
def meta(name, label, value, font=F_LBL, fill=None, nf=None, comment=None):
    put(f"A{rows[name]}", label)
    put(f"B{rows[name]}", value, font, fill, nf)
    if comment: note(f"B{rows[name]}", comment)


meta("m_file", "Arquivo do dataset", "Hoosier_R25B_13x7_TTC_provisional.tir", F_PROV, FILL_PROV,
     comment="Recebido do usuário (2026-10-12) como arquivo de TESTE para desenvolvimento, repassado por terceiro em chat (02/03/2026). Cabeçalho do .tir: Stackpole Engineering Services (M. Arbogast), cliente TTC, Hoosier R25B 177.8/53.6R13, aro 7 in, 12 psi, 25 mph, posição Right, criado em 13/10/2020. Prefixos de chat foram removidos; valores NÃO foram alterados. Não é necessariamente o pneu que será usado.")
meta("m_src", "Fonte / proveniência", "TTC via Stackpole (.tir); recebido em chat; PROVISÓRIO", F_PROV, FILL_PROV)
meta("m_fmt", "Formato do modelo", "PAC2002 (≈ MF 5.2), USE_MODE 4 (combinado), estacionário")
meta("m_rev", "Tire REV (01_SETUP)", "='01_SETUP'!$B$11", F_CALC, FILL_CALC)
meta("m_side", "Lado do arquivo (TYRESIDE)", "Right")
meta("m_conv", "convention_status (sinais de α, κ, γ)", "USER_ASSERTED — dados do TTC (SAE); sinal de IA/camber NÃO confirmado", F_PROV, FILL_PROV,
     comment="V2.4: o usuário declarou que os dados foram baixados direto do TTC, que usa a convenção SAE (Calspan). Fonte secundária (tese UNCC 2015): no dado bruto TTC, α>0 = curva à esquerda, Fy<0 e Mz<0 para α>0, Fz negativo; o .tir tem Fz positivo (processado). NÃO confirmado pela documentação do TTC. Sinal de camber: INFERÊNCIA (empuxo de camber aponta para o lado da inclinação); a definição de IA do TTC não foi verificada. A V2.2/V2.3 diziam 'compatível com ISO': afirmação fraca (α e Fy trocam de sinal juntos entre SAE e ISO, então o pareamento não discrimina), retirada.")
meta("m_axis", "Sistema de eixos do arquivo (declarado): SAE_CALSPAN ou ISO_TYDEX", "SAE_CALSPAN", F_PROV, FILL_PROV,
     comment="Palavra-chave lida pelas fórmulas. SAE_CALSPAN: α_arquivo = −α_ISO; Fy_ISO = −Fy_arquivo; γ_arquivo = −γ_projeto (inferido). ISO_TYDEX: identidade. Qualquer outro texto => dataset INVÁLIDO. Fx e κ não mudam. Ver tire_model_V2_4.AXIS_TRANSFORMS e EDR-039.")
SYS = f"$B${rows['m_axis']}"
for _n, _lab in (("m_sa", "s_α  (α_arquivo = s_α · α_ISO)"), ("m_sf", "s_Fy (Fy_ISO = s_Fy · Fy_arquivo)"), ("m_sg", "s_γ  (γ_arquivo = s_γ · γ_projeto) — INFERÊNCIA no modo SAE")):
    put(f"A{rows[_n]}", _lab)
    put(f"B{rows[_n]}", f'=IF({SYS}="SAE_CALSPAN",-1,IF({SYS}="ISO_TYDEX",1,"N/A"))', F_CALC, FILL_CALC, "0", True)
    ws[f"B{rows[_n]}"].alignment = Alignment(horizontal="left")
meta("m_level", "Nível do modelo (DEC-007)", "2 — avaliação paramétrica dos coeficientes (sem fit próprio)")
meta("m_eqv", "Verificação das equações (V2.3)", "Reproduz 2 códigos de terceiros (Racer CalcMF52; MFeval MF5.2): ≤3e-4 N em 3000 pontos. NÃO validada contra o livro nem contra medição", F_PROV, FILL_PROV,
     comment="tire_model_V2_2 vs. transcrição de RPacejka::CalcMF52 (Racer v0.8.9) e do ramo MF5.2 do MFeval (Fx0/Fy0/combined_slip), 3000 pontos aleatórios na faixa do dataset: dif máx 3,4e-7 N (Racer) e 3,4e-4 N (MFeval). As duas fontes divergem entre si em LFZO e LGAX/LGAY (irrelevante com L*=1). Fonte primária (Pacejka, 2ª/3ª ed.) NÃO consultada diretamente. Ver test_tire_oracles_V2_2.py e EDR-042.")
put(f"A{rows['m_valid']}", "Dataset válido (IP = IP_NOM, PP* = 0, faixas coerentes, eixos declarados)?")
first_pp, last_pp = prow[t.PRESSURE_KEYS[0]], prow[t.PRESSURE_KEYS[-1]]
put(f"B{rows['m_valid']}",
    f'=IF(AND({p("IP")}={p("IP_NOM")},SUMPRODUCT(ABS($B${first_pp}:$B${last_pp}))=0,{p("FZMAX")}>{p("FZMIN")},{p("FNOMIN")}>0,ISNUMBER($B${rows["m_sa"]}),ISNUMBER($B${rows["m_sf"]}),ISNUMBER($B${rows["m_sg"]})),"OK","INVÁLIDO")',
    F_CALC, FILL_CALC, border=True)
for n in ("m_file", "m_src", "m_fmt", "m_rev", "m_side", "m_conv", "m_axis", "m_sa", "m_sf", "m_sg", "m_level", "m_eqv", "m_valid"):
    ws[f"B{rows[n]}"].alignment = Alignment(horizontal="left")

# ---------------- entradas ----------------
put(f"A{rows['hdr']}", "Canto", F_BOLD)
for c, h in zip(COLS, ("FL", "FR", "RL", "RR", "VERIF")):
    put(f"{c}{rows['hdr']}", h, F_BOLD, align=Alignment(horizontal="center"))
put(f"A{rows['side']}", "Lado da roda (L esquerda / R direita)")
for c, v in zip(COLS, ("L", "R", "L", "R", "R")):
    put(f"{c}{rows['side']}", v, F_LBL, border=True, align=Alignment(horizontal="center"))
put(f"G{rows['side']}", "-", F_META); put(f"H{rows['side']}", "SUS-501", F_META)
note(f"B{rows['side']}", "Dataset é de pneu Right (TYRESIDE). Rodas L usam espelhamento (H4, decisão de projeto provisória): α_R=−α e Fy_L=−Fy_R; o camber do projeto (+ = topo para fora) vale nos dois lados. Depois, transformação de eixos do arquivo (SAE_CALSPAN→ISO). VERIF = pneu direito, caso fixo de verificação contra Python.", 340, 130)

put(f"A{rows['fz']}", "Fz (de 09_LOADS, SUS-104; VERIF: valor fixo)")
for c, src in zip(COLS[:4], (31, 32, 33, 34)):
    put(f"{c}{rows['fz']}", f"='09_LOADS'!$B${src}", F_CALC, FILL_CALC, NF, True)
put(f"F{rows['fz']}", 700.0, F_INPUT, FILL_YEL, NF, True)
put(f"A{rows['alpha']}", "Ângulo de deriva α (ISO 8855: + = velocidade p/ esquerda)")
for c, v in zip(COLS, (-3.0, -3.0, -2.0, -2.0, 3.0)):
    put(f"{c}{rows['alpha']}", v, F_INPUT, FILL_YEL, NF, True)
put(f"A{rows['camber']}", "Camber γ (projeto: + = topo para fora)")
for c, v in zip(COLS, (-1.5, -1.5, -1.0, -1.0, 1.5)):
    put(f"{c}{rows['camber']}", v, F_INPUT, FILL_YEL, NF, True)
put(f"A{rows['kappa']}", "Slip ratio κ (ISO: −1 = travada em frenagem)")
for c, v in zip(COLS, (-0.05, -0.05, -0.03, -0.03, 0.05)):
    put(f"{c}{rows['kappa']}", v, F_INPUT, FILL_YEL, NF, True)
for n, u, ref in (("fz", "N", "SUS-104"), ("alpha", "°", "SUS-501"), ("camber", "°", "SUS-404"), ("kappa", "-", "SUS-502")):
    put(f"G{rows[n]}", u, F_META); put(f"H{rows[n]}", ref, F_META)
note(f"B{rows['alpha']}", "DEMONSTRATIVOS (EDR-022): α, γ e κ não vêm de nenhum cálculo do carro (não há modelo de slip na V2). Valores arbitrários coerentes em sinal com 08_VEHICLE_STATE (curva à esquerda, frenagem). Substitua por casos de carga definidos pela equipe.", 340, 120)
note(f"B{rows['camber']}", "Camber de entrada manual (EDR-036 sem decisão: ainda não há ID para camber estático). Convenção do projeto: + = topo para fora, nos dois lados.", 320, 90)
note(f"F{rows['fz']}", "Coluna VERIF: caso fixo (Fz=700 N, α=3°, γ=1,5°, κ=0,05, roda direita) cujo resultado é comparado ao de tire_model_V2_2.py em 13_VALIDATION. Não representa o carro.", 320, 110)

# status
put(f"A{rows['status']}", "Status do ponto de operação (faixa do dataset)")
for c in COLS:
    fz, a, g, k = (R(c, n) for n in ("fz", "alpha", "camber", "kappa"))
    ar, gr = R(c, "a_eq"), R(c, "g_use")
    f = (f'=IF(NOT(AND(ISNUMBER({fz}),ISNUMBER({a}),ISNUMBER({g}),ISNUMBER({k}))),"N/A - entrada ausente",'
         f'IF($B${rows["m_valid"]}<>"OK","N/A - dataset inválido",'
         f'IF({fz}<=0,"N/A - Fz<=0 (liftoff)",'
         f'IF(OR({fz}<{p("FZMIN")},{fz}>{p("FZMAX")}),"N/A - Fz fora da faixa",'
         f'IF(OR({ar}<{p("ALPMIN")},{ar}>{p("ALPMAX")}),"N/A - α fora da faixa",'
         f'IF(OR({gr}<{p("CAMMIN")},{gr}>{p("CAMMAX")}),"N/A - camber fora da faixa",'
         f'IF(OR({k}<{p("KPUMIN")},{k}>{p("KPUMAX")}),"N/A - κ fora da faixa","OK")))))))')
    put(f"{c}{rows['status']}", f, F_CALC, FILL_CALC, border=True, align=Alignment(horizontal="center", wrap_text=True))
ws.row_dimensions[rows["status"]].height = 28
put(f"I{rows['status']}", "Sem extrapolação: fora da faixa do dataset (FZMIN/FZMAX, α, γ, κ) o resultado é N/A, não um valor extrapolado. Fz≤0 = perda de contato.", F_NOTE, align=Alignment(wrap_text=True, vertical="top"))

# ---------------- cálculo ----------------
def calc(name, label, fn, unit="-", ref="", gate=True, comment=None, nf=NF):
    put(f"A{rows[name]}", label)
    for c in COLS:
        expr = fn(c)
        put(f"{c}{rows[name]}", G(c, expr[1:] if expr.startswith("=") else expr) if gate else expr, F_CALC, FILL_CALC, nf, True)
    put(f"G{rows[name]}", unit, F_META); put(f"H{rows[name]}", ref, F_META)
    if comment: put(f"I{rows[name]}", comment, F_NOTE)


calc("mir", "Fator de espelhamento do lado (L=−1, R=+1)", lambda c: f'=IF({R(c,"side")}="L",-1,1)', "-", "H4", gate=False, nf="0")
calc("a_rad", "α [rad]", lambda c: f'=IF(ISNUMBER({R(c,"alpha")}),RADIANS({R(c,"alpha")}),"N/A")', "rad", "SUS-501", gate=False)
calc("g_rad", "γ [rad]", lambda c: f'=IF(ISNUMBER({R(c,"camber")}),RADIANS({R(c,"camber")}),"N/A")', "rad", "SUS-501", gate=False)
calc("a_eq", "α no referencial do arquivo [rad] = s_α · espelhamento · α", lambda c: f'=IF(AND(ISNUMBER({R(c,"a_rad")}),ISNUMBER($B${rows["m_sa"]})),$B${rows["m_sa"]}*{R(c,"mir")}*{R(c,"a_rad")},"N/A")', "rad", "H3b/H4", gate=False)
calc("g_use", "γ no referencial do arquivo [rad] = s_γ · γ", lambda c: f'=IF(AND(ISNUMBER({R(c,"g_rad")}),ISNUMBER($B${rows["m_sg"]})),$B${rows["m_sg"]}*{R(c,"g_rad")},"N/A")', "rad", "H3b", gate=False)
calc("dfz", "dfz = (Fz − LFZO·FNOMIN)/(LFZO·FNOMIN)", lambda c: f'=({R(c,"fz")}-{p("LFZO")}*{p("FNOMIN")})/({p("LFZO")}*{p("FNOMIN")})', "-", "SUS-501")

calc("SHx", "SHx = (PHX1+PHX2·dfz)·LHX", lambda c: f'=({p("PHX1")}+{p("PHX2")}*{R(c,"dfz")})*{p("LHX")}', "-", "SUS-502")
calc("kx", "κx = κ + SHx", lambda c: f'={R(c,"kappa")}+{R(c,"SHx")}', "-", "SUS-502")
calc("Cx", "Cx = PCX1·LCX", lambda c: f'={p("PCX1")}*{p("LCX")}', "-", "SUS-502")
calc("mux", "μx = (PDX1+PDX2·dfz)·(1−PDX3·(γ·LGAX)²)·LMUX", lambda c: f'=({p("PDX1")}+{p("PDX2")}*{R(c,"dfz")})*(1-{p("PDX3")}*({R(c,"g_use")}*{p("LGAX")})^2)*{p("LMUX")}', "-", "SUS-502")
calc("Dx", "Dx = μx·Fz", lambda c: f'={R(c,"mux")}*{R(c,"fz")}', "N", "SUS-502")
calc("Ex", "Ex = min(1; (PEX1+PEX2·dfz+PEX3·dfz²)·(1−PEX4·sgn κx)·LEX)", lambda c: f'=MIN(1,({p("PEX1")}+{p("PEX2")}*{R(c,"dfz")}+{p("PEX3")}*{R(c,"dfz")}^2)*(1-{p("PEX4")}*SIGN({R(c,"kx")}))*{p("LEX")})', "-", "SUS-502")
calc("Kx", "Kx = Fz·(PKX1+PKX2·dfz)·exp(PKX3·dfz)·LKX", lambda c: f'={R(c,"fz")}*({p("PKX1")}+{p("PKX2")}*{R(c,"dfz")})*EXP({p("PKX3")}*{R(c,"dfz")})*{p("LKX")}', "N", "SUS-502")
calc("Bx", "Bx = Kx/(Cx·Dx+ε)", lambda c: f'={R(c,"Kx")}/({R(c,"Cx")}*{R(c,"Dx")}+{p("EPS")})', "-", "SUS-502")
calc("SVx", "SVx = Fz·(PVX1+PVX2·dfz)·LVX·LMUX", lambda c: f'={R(c,"fz")}*({p("PVX1")}+{p("PVX2")}*{R(c,"dfz")})*{p("LVX")}*{p("LMUX")}', "N", "SUS-502")
calc("Fx0", "Fx0 = Dx·sin(Cx·atan(Bx·κx − Ex·(Bx·κx − atan(Bx·κx)))) + SVx",
     lambda c: f'={R(c,"Dx")}*SIN({R(c,"Cx")}*ATAN({R(c,"Bx")}*{R(c,"kx")}-{R(c,"Ex")}*({R(c,"Bx")}*{R(c,"kx")}-ATAN({R(c,"Bx")}*{R(c,"kx")}))))+{R(c,"SVx")}', "N", "SUS-502")

calc("gy", "γy = γ·LGAY", lambda c: f'={R(c,"g_use")}*{p("LGAY")}', "rad", "SUS-501")
calc("Ky", "Ky = PKY1·F'z0·sin(2·atan(Fz/(PKY2·F'z0)))·(1−PKY3·|γy|)·LFZO·LKY",
     lambda c: f'={p("PKY1")}*({p("LFZO")}*{p("FNOMIN")})*SIN(2*ATAN({R(c,"fz")}/({p("PKY2")}*{p("LFZO")}*{p("FNOMIN")})))*(1-{p("PKY3")}*ABS({R(c,"gy")}))*{p("LFZO")}*{p("LKY")}', "N/rad", "SUS-501")
calc("SHy", "SHy = (PHY1+PHY2·dfz)·LHY + PHY3·γy", lambda c: f'=({p("PHY1")}+{p("PHY2")}*{R(c,"dfz")})*{p("LHY")}+{p("PHY3")}*{R(c,"gy")}', "rad", "SUS-501")
calc("ay", "αy = α_eq + SHy", lambda c: f'={R(c,"a_eq")}+{R(c,"SHy")}', "rad", "SUS-501")
calc("Cy", "Cy = PCY1·LCY", lambda c: f'={p("PCY1")}*{p("LCY")}', "-", "SUS-501")
calc("muy", "μy = (PDY1+PDY2·dfz)·(1−PDY3·γy²)·LMUY", lambda c: f'=({p("PDY1")}+{p("PDY2")}*{R(c,"dfz")})*(1-{p("PDY3")}*{R(c,"gy")}^2)*{p("LMUY")}', "-", "SUS-501")
calc("Dy", "Dy = μy·Fz", lambda c: f'={R(c,"muy")}*{R(c,"fz")}', "N", "SUS-501")
calc("Ey", "Ey = min(1; (PEY1+PEY2·dfz)·(1−(PEY3+PEY4·γy)·sgn αy)·LEY)", lambda c: f'=MIN(1,({p("PEY1")}+{p("PEY2")}*{R(c,"dfz")})*(1-({p("PEY3")}+{p("PEY4")}*{R(c,"gy")})*SIGN({R(c,"ay")}))*{p("LEY")})', "-", "SUS-501")
calc("By", "By = Ky/(Cy·Dy+ε)", lambda c: f'={R(c,"Ky")}/({R(c,"Cy")}*{R(c,"Dy")}+{p("EPS")})', "1/rad", "SUS-501")
calc("SVy", "SVy = Fz·((PVY1+PVY2·dfz)·LVY + (PVY3+PVY4·dfz)·γy)·LMUY", lambda c: f'={R(c,"fz")}*(({p("PVY1")}+{p("PVY2")}*{R(c,"dfz")})*{p("LVY")}+({p("PVY3")}+{p("PVY4")}*{R(c,"dfz")})*{R(c,"gy")})*{p("LMUY")}', "N", "SUS-501")
calc("Fy0", "Fy0 = Dy·sin(Cy·atan(By·αy − Ey·(By·αy − atan(By·αy)))) + SVy",
     lambda c: f'={R(c,"Dy")}*SIN({R(c,"Cy")}*ATAN({R(c,"By")}*{R(c,"ay")}-{R(c,"Ey")}*({R(c,"By")}*{R(c,"ay")}-ATAN({R(c,"By")}*{R(c,"ay")}))))+{R(c,"SVy")}', "N", "SUS-501")

calc("SHxa", "SHxα = RHX1", lambda c: f'={p("RHX1")}', "-", "SUS-502")
calc("Bxa", "Bxα = RBX1·cos(atan(RBX2·κ))·LXAL", lambda c: f'={p("RBX1")}*COS(ATAN({p("RBX2")}*{R(c,"kappa")}))*{p("LXAL")}', "-", "SUS-502")
calc("Cxa", "Cxα = RCX1", lambda c: f'={p("RCX1")}', "-", "SUS-502")
calc("Exa", "Exα = min(1; REX1+REX2·dfz)", lambda c: f'=MIN(1,{p("REX1")}+{p("REX2")}*{R(c,"dfz")})', "-", "SUS-502")
def gxa(c, arg):
    b, cc, e = R(c, "Bxa"), R(c, "Cxa"), R(c, "Exa")
    return f'COS({cc}*ATAN({b}*{arg}-{e}*({b}*{arg}-ATAN({b}*{arg}))))'
calc("Gxa_n", "Gxα numerador = cos(Cxα·atan(Bxα·αs − Exα·(Bxα·αs − atan(Bxα·αs)))), αs = α_eq+SHxα", lambda c: "=" + gxa(c, f'({R(c,"a_eq")}+{R(c,"SHxa")})'), "-", "SUS-502")
calc("Gxa_d", "Gxα denominador (mesmo termo com αs = SHxα)", lambda c: "=" + gxa(c, R(c, "SHxa")), "-", "SUS-502")
calc("Gxa", "Gxα", lambda c: f'={R(c,"Gxa_n")}/{R(c,"Gxa_d")}', "-", "SUS-502")
calc("SHyk", "SHyκ = RHY1+RHY2·dfz", lambda c: f'={p("RHY1")}+{p("RHY2")}*{R(c,"dfz")}', "-", "SUS-501")
calc("Byk", "Byκ = RBY1·cos(atan(RBY2·(α_eq−RBY3)))·LYKA", lambda c: f'={p("RBY1")}*COS(ATAN({p("RBY2")}*({R(c,"a_eq")}-{p("RBY3")})))*{p("LYKA")}', "-", "SUS-501")
calc("Cyk", "Cyκ = RCY1", lambda c: f'={p("RCY1")}', "-", "SUS-501")
calc("Eyk", "Eyκ = min(1; REY1+REY2·dfz)", lambda c: f'=MIN(1,{p("REY1")}+{p("REY2")}*{R(c,"dfz")})', "-", "SUS-501")
def gyk(c, arg):
    b, cc, e = R(c, "Byk"), R(c, "Cyk"), R(c, "Eyk")
    return f'COS({cc}*ATAN({b}*{arg}-{e}*({b}*{arg}-ATAN({b}*{arg}))))'
calc("Gyk_n", "Gyκ numerador (κs = κ+SHyκ)", lambda c: "=" + gyk(c, f'({R(c,"kappa")}+{R(c,"SHyk")})'), "-", "SUS-501")
calc("Gyk_d", "Gyκ denominador (κs = SHyκ)", lambda c: "=" + gyk(c, R(c, "SHyk")), "-", "SUS-501")
calc("Gyk", "Gyκ", lambda c: f'={R(c,"Gyk_n")}/{R(c,"Gyk_d")}', "-", "SUS-501")
calc("DVyk", "DVyκ = μy·Fz·(RVY1+RVY2·dfz+RVY3·γ)·cos(atan(RVY4·α_eq))", lambda c: f'={R(c,"muy")}*{R(c,"fz")}*({p("RVY1")}+{p("RVY2")}*{R(c,"dfz")}+{p("RVY3")}*{R(c,"g_use")})*COS(ATAN({p("RVY4")}*{R(c,"a_eq")}))', "N", "SUS-501")
calc("SVyk", "SVyκ = DVyκ·sin(RVY5·atan(RVY6·κ))·LVYKA", lambda c: f'={R(c,"DVyk")}*SIN({p("RVY5")}*ATAN({p("RVY6")}*{R(c,"kappa")}))*{p("LVYKA")}', "N", "SUS-501")

# resultados
calc("o_fx", "Fx combinado (SUS-502) = Gxα·Fx0", lambda c: f'={R(c,"Gxa")}*{R(c,"Fx0")}', "N", "SUS-502", comment="Referencial do dataset (idêntico nos dois lados). + = força para frente (κ>0).")
calc("o_fy", "Fy combinado (SUS-501), convenção do projeto", lambda c: f'={R(c,"mir")}*$B${rows["m_sf"]}*({R(c,"Gyk")}*{R(c,"Fy0")}+{R(c,"SVyk")})', "N", "SUS-501", comment="Fy_ISO = espelhamento · s_Fy · Fy_arquivo. Em curva à esquerda (α<0 ISO) Fy>0 = para a esquerda.")
calc("o_mu", "μ efetivo (SUS-503) = √(Fx²+Fy²)/Fz", lambda c: f'=SQRT({R(c,"o_fx")}^2+{R(c,"o_fy")}^2)/{R(c,"fz")}', "-", "SUS-503", comment="μ DERIVADO do dataset provisório — não é medição da equipe nem do carro.")
calc("o_fyfile", "Fy no referencial do arquivo (pneu Right, sem conversão)", lambda c: f'={R(c,"Gyk")}*{R(c,"Fy0")}+{R(c,"SVyk")}', "N", "SUS-501")
for n in ("o_fx", "o_fy", "o_mu"):
    for c in COLS:
        ws[f"{c}{rows[n]}"].font = Font(name="Arial", size=10, bold=True)

# parâmetros
for name, unit, desc in PARAMS:
    rr = prow[name]
    put(f"A{rr}", name)
    put(f"B{rr}", float(P[name]), F_REF, None, "General", True)
    put(f"G{rr}", unit, F_META); put(f"H{rr}", "SUS-501/502", F_META); put(f"I{rr}", desc, F_NOTE)
put(f"A{prow['EPS']}", "ε (guarda de divisão por zero em Bx, By)")
put(f"B{prow['EPS']}", 1e-6, F_INPUT, None, "General", True)
put(f"G{prow['EPS']}", "-", F_META); put(f"H{prow['EPS']}", "SUS-501/502", F_META)
put(f"I{prow['EPS']}", "Hipótese de implementação (mesmo valor em tire_model_V2_2.py); efeito desprezível frente a Cx·Dx.", F_NOTE)
note(f"B{prow['FNOMIN']}", "Todos os coeficientes desta tabela: transcritos do .tir provisório (ver B-metadados). REFERENCE por natureza (DR-011), mas o DATASET é PROVISÓRIO. Mudou o dataset => mudar Tire REV (01_SETUP) e reexecutar 13_VALIDATION; resultados antigos viram STALE (Guia, H.3).", 340, 130)
ws.freeze_panes = None

# ---------------- 01_SETUP ----------------
s = wb["01_SETUP"]
s["B11"].value = "T-REV-A (provisório)"
s["B11"].comment = Comment("T-REV-A = dataset TTC provisório Hoosier R25B (10_TIRE). O rótulo 'A' é proposta do V2.2 (Guia H.1: Tire T-REV-X muda com dataset/modelo). Trocar o dataset => nova revisão.", "Sistema_DDS V2.2")

# ---------------- 04_DECISION_REGISTER ----------------
d = wb["04_DECISION_REGISTER"]
for col in "ABCDEFGH":
    d[f"{col}19"].value = d[f"{col}18"].value; d[f"{col}19"]._style = copy.copy(d[f"{col}18"]._style)
    d[f"{col}18"].value = d[f"{col}17"].value; d[f"{col}18"]._style = copy.copy(d[f"{col}17"]._style)
    d[f"{col}17"]._style = copy.copy(d[f"{col}16"]._style)
d["A17"].value = "DR-013"
d["B17"].value = "SUS-501 / SUS-502 / SUS-503 (Tire) — implementação em 10_TIRE"
d["C17"].value = ("Pneu avaliado em 10_TIRE por nivel 2 (parametrico): equacoes PAC2002/MF 5.2 aplicadas aos coeficientes de um .tir, sem fit proprio. "
                  "Dataset atual = .tir TTC PROVISORIO (Hoosier R25B), so para desenvolvimento. Fora da faixa do dataset o resultado e N/A (sem extrapolar).")
d["D17"].value = ("Pedido do usuario (2026-10-12) com .tir TTC fornecido; DR-011 (sem fit proprio). Guia: o workbook nao apresenta mu proprio como medido.")
d["E17"].value = ("Sistema de eixos do arquivo = SAE (Calspan/TTC), DECLARADO pelo usuario (dados baixados do TTC), transformado para ISO (alpha_arq=-alpha, Fy_ISO=-Fy_arq; camber: empuxo para o lado da inclinacao, INFERIDO: IA do TTC nao verificado). Espelhamento das rodas esquerdas (arquivo e Right) e hipotese de projeto. "
                  "Equacoes: verificadas (V2.3) contra duas implementacoes de terceiros (Racer CalcMF52 e ramo MF5.2 do MFeval; 3000 pontos, dif <= 3e-4 N) e por limites analiticos (tire_model_V2_2.py); "
                  "NAO validadas contra o livro (Pacejka) nem contra medicao/OptimumTire: Validation = NOT_VALIDATED. Mx/My/Mz, pressao e relaxamento fora de escopo.")
d["F17"].value = "Mecanica (decisao de implementacao)"
d["G17"].value = "DRAFT"
d["H17"].value = "V2.2 (proposta); texto revisado na V2.3 e V2.4"
d["E15"].value = d["E15"].value.replace("10_TIRE aguarda a Fase 2.", "10_TIRE implementado na V2.2 com dataset provisorio (ver DR-013).")

# ---------------- 13_VALIDATION ----------------
v = wb["13_VALIDATION"]
ref_fx, ref_fy, _ = t.wheel_forces(ds, "FR", 700.0, math.radians(3), math.radians(1.5), 0.05)
ref_mu = t.mu_effective(ref_fx, ref_fy, 700.0)
base = 35
def vcopy(src_row, dst_row):
    for col in "ABCDE":
        v[f"{col}{dst_row}"]._style = copy.copy(v[f"{col}{src_row}"]._style)
v.merge_cells(f"A{base}:E{base}"); vcopy(28, base)
v[f"A{base}"].value = "Pneu (V2.2) — SUS-501/502/503; dataset TTC PROVISÓRIO (10_TIRE, DR-013). Sem comparação com OptimumTire/TTC: Validation = NOT_VALIDATED"
rowsv = [
    ("Dataset de pneu: validade formal (IP=IP_NOM, PP*=0, faixas)", "='10_TIRE'!$B$%d" % rows["m_valid"], "-", "SUS-501"),
    ("Referência Python — Fx do caso VERIF [N] (resultado de código)", ref_fx, "N", "SUS-502"),
    ("Referência Python — Fy do caso VERIF [N] (resultado de código)", ref_fy, "N", "SUS-501"),
    ("Referência Python — μ_eff do caso VERIF (resultado de código)", ref_mu, "-", "SUS-503"),
]
for i, (lab, val, unit, rid) in enumerate(rowsv, start=1):
    rr = base + i
    for col in "ABCDE": v[f"{col}{rr}"]._style = copy.copy(v[f"{col}29"]._style)
    v[f"A{rr}"].value = lab; v[f"B{rr}"].value = val; v[f"C{rr}"].value = unit; v[f"D{rr}"].value = rid
    if i > 1:
        v[f"B{rr}"].number_format = "0.000000"
        v[f"B{rr}"].font = Font(name="Arial", size=10, color="0000FF"); v[f"B{rr}"].fill = PatternFill(fill_type=None)
def vcheck(rr, label, excel_name, refrow, rid):
    for col in "ABCDE": v[f"{col}{rr}"]._style = copy.copy(v[f"{col}30"]._style)
    v[f"A{rr}"].value = label
    cell = f"'10_TIRE'!$F${rows[excel_name]}"
    v[f"B{rr}"].value = (f'=IF(ISNUMBER({cell}),IF(ABS({cell}-$B${refrow})<=0.000001*MAX(1,ABS($B${refrow})),"PASS","FAIL - Excel diverge do Python"),"N/A - caso VERIF fora da faixa ou dataset inválido")')
    v[f"C{rr}"].value = "-"; v[f"D{rr}"].value = rid
vcheck(base + 5, "Status: Fx Excel (10_TIRE!F) vs Python — tol. numérica 1e-6 relativa", "o_fx", base + 2, "SUS-502")
vcheck(base + 6, "Status: Fy Excel vs Python — tol. numérica 1e-6 relativa", "o_fy", base + 3, "SUS-501")
vcheck(base + 7, "Status: μ_eff Excel vs Python — tol. numérica 1e-6 relativa", "o_mu", base + 4, "SUS-503")
rr = base + 8
for col in "ABCDE": v[f"{col}{rr}"]._style = copy.copy(v[f"{col}29"]._style)
v[f"A{rr}"].value = "Cantos com resultado de pneu válido (de 4, 10_TIRE)"
v[f"B{rr}"].value = f"=COUNTIF('10_TIRE'!$B${rows['status']}:$E${rows['status']},\"OK\")"
v[f"B{rr}"].number_format = "0"; v[f"C{rr}"].value = "-"; v[f"D{rr}"].value = "SUS-501"
rr = base + 9
v.merge_cells(f"A{rr}:E{rr}"); vcopy(33, rr)
v[f"A{rr}"].value = ("Tolerâncias: numérica = 1e-6 relativa (mesmas equações em dupla implementação; não há referência externa); de engenharia = NÃO DEFINIDA (exige OptimumTire/TTC). "
                      "PASS aqui = Excel reproduz Python, NÃO validação física. Python: 34/34 testes + 5/5 contra 2 códigos de terceiros (Racer CalcMF52; MFeval MF5.2) — concordância de TRANSCRIÇÃO, não validação física nem contra o livro.")
v.row_dimensions[rr].height = 52

# ---------------- 14_DASHBOARD ----------------
b = wb["14_DASHBOARD"]
b.merge_cells("A32:E32")
for col in "ABCDE": b[f"{col}32"]._style = copy.copy(b[f"{col}26"]._style)
b["A32"].value = "Pneu — dataset TTC PROVISÓRIO (não é o pneu do carro; μ derivado do dataset, não medido)"
b.row_dimensions[32].height = 30
items = [("Dataset de pneu (validade formal)", f"='10_TIRE'!$B${rows['m_valid']}", "-", "SUS-501", None)]
for cn, col in zip(("FL", "FR", "RL", "RR"), "BCDE"):
    items.append((f"μ efetivo {cn} (demonstrativo)", f"='10_TIRE'!${col}${rows['o_mu']}", "-", "SUS-503", NF))
items.append(("Convenção de sinais do pneu", "SAE→ISO (declarada); camber não confirmado", "-", "DR-013", None))
for i, (lab, f, u, rid, nf) in enumerate(items, start=33):
    for col in "ABCD": b[f"{col}{i}"]._style = copy.copy(b[f"{col}27"]._style)
    b[f"A{i}"].value = lab; b[f"B{i}"].value = f; b[f"C{i}"].value = u; b[f"D{i}"].value = rid
    if nf: b[f"B{i}"].number_format = nf
b["B38"].font = F_PROV; b["B38"].fill = FILL_PROV

# ---------------- 00_README ----------------
m = wb["00_README"]
m["A3"].value = "Versão do workbook: V2.4 (inclui pneu SUS-501/502/503 em 10_TIRE com dataset PROVISÓRIO; decisões A/B/C da V2.1 seguem pendentes) | Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated"
m["A7"].value = "(SUS-001 a SUS-104, SUS-201/202/205/206/207/208, SUS-501/502/503, SUS-701/702), já verificadas no piloto Python"
m["A8"].value = "(suspension_model_V2_1.py, tire_model_V2_2.py e seus testes; ver 13_VALIDATION)."
m.merge_cells("A37:E37"); m["A37"]._style = copy.copy(m["A36"]._style)
m["A37"].value = ("• Pneu (10_TIRE): coeficientes de um .tir TTC PROVISÓRIO (pode não ser o pneu real); arquivo em SAE (TTC, declarado) transformado para ISO, sinal de camber não confirmado; sem Mx/My/Mz, pressão ou relaxamento; "
                  "fora da faixa do dataset o resultado é N/A. μ efetivo é derivado do dataset, não medido pela equipe.")
m.row_dimensions[37].height = 42

# ---------------- 15_CHANGELOG ----------------
c = wb["15_CHANGELOG"]
for col in "ABCDE": c[f"{col}13"]._style = copy.copy(c[f"{col}12"]._style)
c["A13"].value = "2026-10"
c["B13"].value = ("V2.2: 10_TIRE implementada (SUS-501 Fy, SUS-502 Fx, SUS-503 mu efetivo; PAC2002/MF 5.2 nivel 2, combinado) a partir de .tir TTC PROVISORIO; "
                  "entradas por canto (Fz de 09_LOADS; alpha/gamma/kappa demonstrativos), faixa do dataset com N/A, caso VERIF. 13_VALIDATION linhas 35-44; 14_DASHBOARD linhas 32-38; "
                  "04_DECISION_REGISTER DR-013 (e texto de DR-011 E15); 01_SETUP Tire REV; README. Python: tire_model_V2_2.py + test_tire_model_V2_2.py.")
c["C13"].value = ("Pedido do usuario com dataset TTC para desenvolvimento. Somente adicoes + substituicao da aba 10_TIRE: as 88 formulas anteriores nao foram alteradas. "
                  "Impacto: nenhum resultado existente muda. Validation: Python 34/34 (mutacao 17/17); Excel x Python (test_workbook_V2_2.py). NOT_VALIDATED fisicamente (sem OptimumTire).")
c["C13"].value += " Revision: T-REV-A. Pendentes: confirmar convencao de sinais e espelhamento; dataset real; EDR-025/035/036; fichas SUS-501..503 do Standard devem refletir nivel 2 e convencao. Autor: nao registrado."

for col in "ABCDE": c[f"{col}14"]._style = copy.copy(c[f"{col}12"]._style)
c["A14"].value = "2026-10"
c["B14"].value = ("V2.3: verificacao das equacoes do pneu contra 2 codigos de terceiros (Racer CalcMF52; MFeval ramo MF5.2) em 3000 pontos (dif <= 3,4e-4 N); novo metadado em 10_TIRE; texto de DR-013, 13_VALIDATION l.44 e README ajustados. Nenhuma formula alterada em relacao a V2.2.")
c["C14"].value = ("Pedido do usuario: encontrar fonte primaria e validar as equacoes. Fonte primaria (livro) nao acessivel; usadas fontes de terceiros. Impacto: apenas texto/metadado. "
                  "Validation: test_tire_oracles_V2_2.py 5/5; Excel x Python mantido (test_workbook). Pendente: livro (Pacejka), OptimumTire e medicao. Revision: T-REV-A. Autor: nao registrado.")

for col in "ABCDE": c[f"{col}15"]._style = copy.copy(c[f"{col}12"]._style)
c["A15"].value = "2026-10"
c["B15"].value = ("V2.4: sistema de eixos do arquivo declarado (SAE_CALSPAN, dados do TTC) com transformacao explicita para ISO em 10_TIRE (s_alpha, s_Fy, s_gamma; alpha_arq=-alpha, Fy_ISO=-Fy_arq, gamma_arq=-gamma); eixo desconhecido invalida o dataset; "
                  "retirada a afirmacao 'compativel com ISO' (nao discriminava SAE de ISO). Fy muda ~3% a 4 graus de deriva, empuxo de camber ~30% a 3 graus e o offset de Fy em zero slip inverte de sinal; Fx so muda com alpha != 0.")
c["C15"].value = ("Pedido do usuario apos informar que o TTC usa SAE e que os dados foram baixados direto do TTC. Impacto: Fy/Fx/mu de 10_TIRE, 13_VALIDATION l.37-39 (referencia Python recalculada) e dashboard. "
                  "Validation: tire_model_V2_4 43/43, oraculos 5/5, mutacao 23/23, Excel x Python (test_workbook_V2_4). Pendente: definicao de IA do TTC (sinal do camber) e comparacao com OptimumTire. Revision: T-REV-A. Autor: nao registrado.")

wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
import json
json.dump({"rows": rows, "prow": prow, "ref": {"fx": ref_fx, "fy": ref_fy, "mu": ref_mu}, "base": base}, open(LAYOUT, "w"))
print("salvo", OUT, "linhas", r, "ref", ref_fx, ref_fy, ref_mu)
