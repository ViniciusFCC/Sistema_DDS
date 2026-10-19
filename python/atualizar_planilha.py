"""Gera a planilha V2.5 a partir da V2.4: revisão metodológica contra a literatura (EDR-045 a EDR-049).

Uso:
    uv run python -X utf8 python/atualizar_planilha.py [ORIGEM_V2_4.xlsx] [SAIDA_V2_5.xlsx] [--registro ARQ.md]

Padrão: origem excel/FSAE_EV_Suspension_Fase1_V2_4.xlsx, saída build/FSAE_EV_Suspension_Fase1_V2_5.xlsx
(nunca por cima da entregue). Lê a origem e grava uma cópia nova pelo openpyxl; nenhuma planilha é
recalculada nem salva pelo Excel ou pelo LibreOffice.

Toda célula tocada está em ALTERACOES, com a fonte e o EDR. O registro (--registro) lista, para cada
uma, aba, célula, conteúdo anterior (lido da origem) e novo: é a rastreabilidade que o CLAUDE.md exige
para mudança de fórmula. Referências: docs/revisao-metodologica.md.
"""
import argparse
import copy
from pathlib import Path

import openpyxl
from openpyxl.comments import Comment

AQUI = Path(__file__).resolve().parent
V = "'05_VEHICLE'!"
S = "'06_SUSPENSION'!"
K = "'07_KINEMATICS'!"
E = "'08_VEHICLE_STATE'!"
L = "'09_LOADS'!"
D = "'11_DESIGN'!"
T = "'10_TIRE'!"
AUTOR = "Sistema_DDS V2.5"

# Rigidez vertical do pneu: único valor com fonte no projeto é o do .tir TTC provisório (EDR-038).
K_T_PROVISORIO = 120312.0   # N/m, VERTICAL_STIFFNESS de data/Hoosier_R25B_13x7_TTC_provisional.tir
NOTA_KT = ("PROVISÓRIO (EDR-045): VERTICAL_STIFFNESS do .tir TTC provisório (Hoosier R25B, EDR-038). "
           "Não é o pneu do carro nem medição da equipe: substituir pela rigidez vertical do pneu real. "
           "Milliken p. 591, Gillespie eq. 5-8 e Seward eq. 4.1 põem o pneu em série com a mola.")


def _a(aba, cel, novo, ref, estilo=None, comentario=None):
    return {"aba": aba, "cel": cel, "novo": novo, "ref": ref, "estilo": estilo, "comentario": comentario}


def alteracoes(ky_row: int) -> list[dict]:
    """Lista completa das células alteradas ou criadas na V2.5. ky_row = linha de Ky em 10_TIRE (layout)."""
    a = []
    # ---------------- 05_VEHICLE: massa suspensa por eixo e a_s (EDR-047; Milliken p. 601-603) ----------------
    for r, rot, f, un in (
        (25, "Massa suspensa - eixo dianteiro (m·b/L − m_uF)", f"={V}$B$4*{V}$B$10/{V}$B$6-{V}$B$14", "kg"),
        (26, "Massa suspensa - eixo traseiro (m·a/L − m_uR)", f"={V}$B$4*{V}$B$9/{V}$B$6-{V}$B$15", "kg"),
        (27, "CG suspenso -> eixo dianteiro (a_s = L·m_s,R/m_s)", f"={V}$B$6*{V}$B$26/{V}$B$23", "m"),
    ):
        a += [_a("05_VEHICLE", f"A{r}", rot, "EDR-047", ("05_VEHICLE", 23, "A")),
              _a("05_VEHICLE", f"B{r}", f, "EDR-047; Milliken p. 601-603; Seward eq. 5.14", ("05_VEHICLE", 23, "B")),
              _a("05_VEHICLE", f"C{r}", un, "EDR-047", ("05_VEHICLE", 23, "C")),
              _a("05_VEHICLE", f"D{r}", "SUS-009", "EDR-047", ("05_VEHICLE", 23, "D"))]

    # ---------------- 06_SUSPENSION: pneu em série (EDR-045) ----------------
    st = lambda r, c: ("06_SUSPENSION", r, c)
    a.append(_a("06_SUSPENSION", "A2", "Mola, MR, barra e roll center (B4:B15): valores DEMONSTRATIVOS herdados do T09/E03, para referência e "
                                       "teste das fórmulas; não são o TX/E05 (EDR-012/022).", "EDR-012/022", st(35, "A")))
    a.append(_a("06_SUSPENSION", "A46","Pneu em série e ride rate (EDR-045) — K_T PROVISÓRIO: rigidez vertical do .tir TTC, não é o pneu do carro",
                "EDR-045", st(17, "A")))
    for r, rot, val, un, sid, com in (
        (47, "Rigidez vertical do pneu - dianteiro (K_T)", K_T_PROVISORIO, "N/m", "SUS-211", NOTA_KT),
        (48, "Rigidez vertical do pneu - traseiro (K_T)", K_T_PROVISORIO, "N/m", "SUS-211", NOTA_KT),
    ):
        a += [_a("06_SUSPENSION", f"A{r}", rot, "EDR-045", st(4, "A")),
              _a("06_SUSPENSION", f"B{r}", val, "EDR-045 (valor: .tir provisório, EDR-038)", st(4, "B"), com),
              _a("06_SUSPENSION", f"C{r}", un, "EDR-045", st(4, "C")),
              _a("06_SUSPENSION", f"D{r}", sid, "EDR-045", st(4, "D"))]
    for r, rot, f, un, sid in (
        (49, "Ride rate dianteiro K_R = K_W·K_T/(K_W+K_T)", f"={S}$B$18*{S}$B$47/({S}$B$18+{S}$B$47)", "N/m", "SUS-212"),
        (50, "Ride rate traseiro K_R = K_W·K_T/(K_W+K_T)", f"={S}$B$19*{S}$B$48/({S}$B$19+{S}$B$48)", "N/m", "SUS-212"),
        (51, "Rigidez de rolagem do par de pneus - dianteira (K_T·t_F²/2)", f"={S}$B$47*{V}$B$7^2/2", "N*m/rad", "SUS-206"),
        (52, "Rigidez de rolagem do par de pneus - traseira (K_T·t_R²/2)", f"={S}$B$48*{V}$B$8^2/2", "N*m/rad", "SUS-207"),
    ):
        a += [_a("06_SUSPENSION", f"A{r}", rot, "EDR-045", st(18, "A")),
              _a("06_SUSPENSION", f"B{r}", f, "EDR-045; Milliken p. 589-592; Gillespie eq. 5-8; Seward eq. 4.1/4.5", st(18, "B")),
              _a("06_SUSPENSION", f"C{r}", un, "EDR-045", st(18, "C")),
              _a("06_SUSPENSION", f"D{r}", sid, "EDR-045", st(18, "D"))]
    a += [
        _a("06_SUSPENSION", "A20", "Roll Stiffness sem ARB e sem pneu (K_W·t_F²/2) - dianteira", "EDR-045"),
        _a("06_SUSPENSION", "A21", "Roll Stiffness sem ARB e sem pneu (K_W·t_R²/2) - traseira", "EDR-045"),
        _a("06_SUSPENSION", "A22", "Roll Stiffness dianteira K_phiF = (K_W·t²/2 + K_ARB) em série com K_T·t²/2", "EDR-045"),
        _a("06_SUSPENSION", "B22", f"=1/(1/({S}$B$20+{S}$B$10)+1/{S}$B$51)", "EDR-045; Milliken p. 592 e p. 680"),
        _a("06_SUSPENSION", "A23", "Roll Stiffness traseira K_phiR = (K_W·t²/2 + K_ARB) em série com K_T·t²/2", "EDR-045"),
        _a("06_SUSPENSION", "B23", f"=1/(1/({S}$B$21+{S}$B$11)+1/{S}$B$52)", "EDR-045; Milliken p. 592 e p. 680"),
        # massa suspensa por canto (EDR-047)
        _a("06_SUSPENSION", "A27", "Massa suspensa por canto (SUS-009, por eixo: (m·b/L − m_uF)/2 e (m·a/L − m_uR)/2)", "EDR-047"),
        _a("06_SUSPENSION", "B28", f"={V}$B$25/2", "EDR-047; Milliken p. 601, Tab. 16.3"),
        _a("06_SUSPENSION", "B29", f"={V}$B$26/2", "EDR-047; Milliken p. 601, Tab. 16.3"),
        # frequência com ride rate (EDR-045)
        _a("06_SUSPENSION", "A31", "Frequência Natural (SUS-205) — com a ride rate (pneu em série)", "EDR-045"),
        _a("06_SUSPENSION", "B32", f"=(1/(2*PI()))*SQRT({S}$B$49/{S}$B$28)", "EDR-045; Gillespie eq. 5-9; Seward eq. 4.2"),
        _a("06_SUSPENSION", "B33", f"=(1/(2*PI()))*SQRT({S}$B$50/{S}$B$29)", "EDR-045; Gillespie eq. 5-9; Seward eq. 4.2"),
        # anti com sinal e ponto de reação do carro (EDR-048)
        _a("06_SUSPENSION", "A34", "Anti-Dive / Anti-Squat (SUS-301/302) — com sinal (EDR-026/048)", "EDR-048"),
        _a("06_SUSPENSION", "A35", "Milliken p. 618-619: freio no cubo (outboard) -> linha pelo contact patch; motor no chassi com semieixos -> "
                                   "linha pelo centro da roda (Fig. 17.15b). + = anti, − = pro (p. 620). IC de 07_KINEMATICS ainda é PLACEHOLDER.",
           "EDR-048"),
        _a("06_SUSPENSION", "A38", "Inclinação dz/dx da linha contact patch -> IC lateral dianteiro (com sinal; freio no cubo)", "EDR-048"),
        _a("06_SUSPENSION", "A39", "Inclinação dz/dx da linha centro da roda -> IC lateral traseiro (com sinal; motor no chassi)", "EDR-048"),
        _a("06_SUSPENSION", "B39", f"=({K}$B$12-{K}$B$14)/{K}$B$13", "EDR-048; Milliken Fig. 17.15(b); Gillespie eq. 7-19"),
        _a("06_SUSPENSION", "A40", "Anti-Dive (%) = FB_f·(−dz/dx)·L/h·100 (+ = anti, − = pro-dive)", "EDR-048"),
        _a("06_SUSPENSION", "B40", f"={S}$B$36*(-{S}$B$38)*({V}$B$6/{V}$B$5)*100", "EDR-048; Milliken p. 618"),
        _a("06_SUSPENSION", "A41", "Anti-Squat (%) = TF_r·(dz/dx)·L/h·100 (+ = anti, − = pro-squat)", "EDR-048"),
    ]
    # ---------------- 07_KINEMATICS: IC lateral com sinal e altura do centro da roda (EDR-048) ----------------
    a += [
        _a("07_KINEMATICS", "A11", "Δx do IC lateral dianteiro ao contact patch (x_IC − x_CP; ISO: + = à frente)", "EDR-048"),
        _a("07_KINEMATICS", "B11", -2.5, "EDR-048: mesmo PLACEHOLDER (2,5 m), agora com sinal: IC atrás do contact patch (Milliken p. 617)"),
        _a("07_KINEMATICS", "A13", "Δx do IC lateral traseiro ao centro da roda (x_IC − x_WC; ISO: + = à frente)", "EDR-048"),
        _a("07_KINEMATICS", "A14", "Altura do centro da roda traseira (ponto de reação do anti-squat)", "EDR-048", ("07_KINEMATICS", 12, "A")),
        _a("07_KINEMATICS", "B14", f"={V}$B$17", "EDR-048: PLACEHOLDER = SUS-011 (aproximado pela altura do centro da roda)", ("07_KINEMATICS", 12, "B"),
           "PLACEHOLDER: usa a altura do CG não suspenso traseiro (SUS-011), que a ficha aproxima pela altura do centro da roda. "
           "Substituir pela altura do centro da roda do CAD."),
        _a("07_KINEMATICS", "C14", "m", "EDR-048", ("07_KINEMATICS", 12, "C")),
        _a("07_KINEMATICS", "D14", "SUS-406-R", "EDR-048", ("07_KINEMATICS", 12, "D")),
    ]
    # ---------------- 09_LOADS: SUS-103 completa (EDR-046/047) ----------------
    h2 = f"({V}$B$24-{L}$B$18)"
    a += [
        _a("09_LOADS", "A17", "Transferência Lateral — Milliken, três massas, com termo gravitacional (SUS-103)", "EDR-046"),
        _a("09_LOADS", "A18", "Altura do roll axis no CG suspenso (z_s, em a_s)", "EDR-047"),
        _a("09_LOADS", "B18", f"={S}$B$14+({S}$B$15-{S}$B$14)*{V}$B$27/{V}$B$6", "EDR-047; Milliken p. 603"),
        _a("09_LOADS", "B19", f"=IF(ISNUMBER({L}$B$21),({S}$B$22*{L}$B$21+{E}$B$5*({V}$B$25*{S}$B$14+{V}$B$14*{V}$B$16))/{V}$B$7,\"N/A\")",
           "EDR-046/047; Milliken p. 604 e p. 682"),
        _a("09_LOADS", "B20", f"=IF(ISNUMBER({L}$B$21),({S}$B$23*{L}$B$21+{E}$B$5*({V}$B$26*{S}$B$15+{V}$B$15*{V}$B$17))/{V}$B$8,\"N/A\")",
           "EDR-046/047; Milliken p. 604 e p. 682"),
        _a("09_LOADS", "A21", "Ângulo de rolagem φ = m_s·a_y·h2/(K_φF+K_φR − m_s·g·h2) (+ = para fora da curva)", "EDR-046", ("09_LOADS", 19, "A")),
        _a("09_LOADS", "B21", (f"=IF({S}$B$22+{S}$B$23-{V}$B$23*9.81*{h2}<=0,\"N/A - instabilidade de rolagem (m_s·g·h2 >= K_φ, Milliken p. 682)\","
            f"{V}$B$23*{E}$B$5*{h2}/({S}$B$22+{S}$B$23-{V}$B$23*9.81*{h2}))"),
           "EDR-046; Milliken p. 682; Gillespie eq. 6-31", ("09_LOADS", 19, "B")),
        _a("09_LOADS", "C21", "rad", "EDR-046", ("09_LOADS", 19, "C")),
        _a("09_LOADS", "D21", "SUS-103", "EDR-046", ("09_LOADS", 19, "D")),
    ]
    # ---------------- 11_DESIGN: modo reverso com pneu (EDR-045) ----------------
    w = lambda c, m: f"(2*PI()*{D}$B${c})^2*{S}$B${m}"
    a += [
        _a("11_DESIGN", "A7", "Rigidez necessária (equação reversa, SUS-205/212/202; pneu em série)", "EDR-045"),
        _a("11_DESIGN", "A8", "Wheel Rate necessário - dianteira (K_R alvo -> K_W = K_R·K_T/(K_T − K_R))", "EDR-045"),
        _a("11_DESIGN", "B8", f"={w(4, 28)}*{S}$B$47/({S}$B$47-{w(4, 28)})", "EDR-045; Milliken p. 591; Seward eq. 4.4"),
        _a("11_DESIGN", "A9", "Wheel Rate necessário - traseira (K_R alvo -> K_W = K_R·K_T/(K_T − K_R))", "EDR-045"),
        _a("11_DESIGN", "B9", f"={w(5, 29)}*{S}$B$48/({S}$B$48-{w(5, 29)})", "EDR-045; Milliken p. 591; Seward eq. 4.4"),
        _a("11_DESIGN", "A20", "K_ARB dianteiro necessário (com o pneu em série)", "EDR-045"),
        _a("11_DESIGN", "B20", f"={D}$B$19*{S}$B$51/({S}$B$51-{D}$B$19)-{S}$B$20", "EDR-045; Milliken p. 592"),
    ]
    # ---------------- 13_VALIDATION: TC-005 com o termo gravitacional (EDR-046) ----------------
    a += [
        _a("13_VALIDATION", "A6", "TC-005: t_F*dFzF + t_R*dFzR - m*ay*h_CG - m_s*g*h2*φ [deve ser ~0]", "EDR-046"),
        _a("13_VALIDATION", "B6", f"={V}$B$7*{L}$B$19+{V}$B$8*{L}$B$20-{V}$B$4*{E}$B$5*{V}$B$5-{V}$B$23*9.81*{h2}*{L}$B$21",
           "EDR-046; Milliken p. 682-683"),
        _a("13_VALIDATION", "A26", "Piloto de referência: MR=0.8, Ks=100 N/mm, ms=50 kg, pneu rígido -> fn=8.897 Hz (verificado)", "EDR-045"),
    ]
    # ---------------- 10_TIRE: Ky com um único λFz0 (EDR-049) ----------------
    a.append(_a("10_TIRE", f"A{ky_row}", "Ky = PKY1·F'z0·sin(2·atan(Fz/(PKY2·F'z0)))·(1−PKY3·|γy|)·LKY  (um λFz0, EDR-049)", "EDR-049"))
    for c in "BCDEF":
        a.append(_a("10_TIRE", f"{c}{ky_row}", None, "EDR-049; Pacejka (2006) eq. 4.E25; Seward eq. 5.9"))
    return a


def _ky_formula(antiga: str, lfzo: str, lky: str) -> str:
    """Remove o segundo λFz0 ('*LFZO*LKY' -> '*LKY') sem tocar no resto da fórmula."""
    alvo = f"*{lfzo}*{lky})"
    if antiga.count(alvo) != 1:
        raise RuntimeError(f"fórmula de Ky inesperada: {antiga!r}")
    return antiga.replace(alvo, f"*{lky})")


def aplicar(src: Path, out: Path, layout: dict) -> list[dict]:
    wb = openpyxl.load_workbook(src)
    prow, rows = layout["prow"], layout["rows"]
    lfzo, lky = f"$B${prow['LFZO']}", f"$B${prow['LKY']}"
    registro = []
    for alt in alteracoes(rows["Ky"]):
        ws = wb[alt["aba"]]
        c = ws[alt["cel"]]
        antes = c.value
        novo = alt["novo"]
        if alt["aba"] == "10_TIRE" and alt["cel"][0] in "BCDEF":
            novo = _ky_formula(antes, lfzo, lky)
        if alt["estilo"]:
            aba_e, linha_e, col_e = alt["estilo"]
            c._style = copy.copy(wb[aba_e][f"{col_e}{linha_e}"]._style)
        c.value = novo
        if alt["comentario"]:
            cm = Comment(alt["comentario"], AUTOR)
            cm.width, cm.height = 340, 120
            c.comment = cm
        registro.append({**alt, "antes": antes, "novo": novo})

    # Valores de mola, MR, barra e RC herdados do T09/E03: só referência e teste de formulação (usuário, 2026-10-19;
    # EDR-012: T09 nunca é baseline; EDR-022: valor demonstrativo rotulado). Muda só comentário e um aviso; nenhum valor.
    sus = wb["06_SUSPENSION"]
    aviso = ("DEMONSTRATIVO (EDR-012/022): valor herdado do T09/E03, usado só para referência, comparação e teste das "
             "fórmulas (confirmado pelo usuário em 2026-10-19). Não é o TX/E05. ")
    for cel in ("B4", "B5", "B6", "B7", "B10", "B11", "B14", "B15"):
        c = sus[cel]
        antes = c.comment.text if c.comment else None
        texto = aviso + (antes or "")
        cm = Comment(texto, AUTOR)
        cm.width, cm.height = 360, 150
        c.comment = cm
        registro.append({"aba": "06_SUSPENSION", "cel": f"{cel} (comentário)", "antes": antes, "novo": texto, "ref": "EDR-012/022"})
    m = wb["00_README"]
    m["A3"].value = ("Versão do workbook: V2.5 (revisão metodológica contra Milliken/Gillespie/Seward/Pacejka: pneu em série, "
                     "termo gravitacional da rolagem, massa suspensa por eixo, anti com sinal, Ky com um λFz0; EDR-045 a EDR-049) "
                     "| Status: DRAFT — cross-check, ainda NÃO REFERENCE-validated")
    tire = wb["10_TIRE"]
    tire[f"B{rows['m_eqv']}"].value = ("Fy0 confere com Seward eq. 5.5-5.13 (PAC'96/2002); combinado (Gxα, Gyκ, SVyκ) com Pacejka 2006 eq. 4.E50-4.E67; "
                                        "Ky com um único λFz0 (EDR-049). Reproduz o MFeval MF5.2. NÃO validado contra medição nem OptimumTire")
    registro.append({"aba": "10_TIRE", "cel": f"B{rows['m_eqv']}", "antes": "(texto V2.4)", "novo": "(texto V2.5)", "ref": "EDR-042/049"})
    registro.append({"aba": "00_README", "cel": "A3", "antes": "Versão do workbook: V2.4 ...", "novo": "Versão do workbook: V2.5 ...", "ref": "EDR-043"})

    c = wb["15_CHANGELOG"]
    for col in "ABCDE":
        c[f"{col}16"]._style = copy.copy(c[f"{col}15"]._style)
    c["A16"].value = "2026-10"
    c["B16"].value = ("V2.5: revisao metodologica contra Milliken (RCVD), Gillespie, Seward e Pacejka. Pneu em serie na frequencia natural e na rigidez de rolagem "
                      "(K_T provisorio do .tir; 06_SUSPENSION l.46-52, B22/B23, B32/B33; 11_DESIGN B8/B9/B20); SUS-103 com termo gravitacional e CG suspenso em a_s "
                      "(09_LOADS B18-B21; 13_VALIDATION B6); massa suspensa por eixo (05_VEHICLE l.25-27; 06 B28/B29); anti-dive/anti-squat com sinal e ponto de reacao "
                      "do carro (freio no cubo, motor no chassi; 06 B39-B41, 07 B11/B13/B14); Ky com um lambda_Fz0 (10_TIRE).")
    c["C16"].value = ("Pedido do usuario (2026-10-19): seguir a literatura, principalmente o Milliken. EDR-045 a EDR-049. Registro celula a celula: "
                      "docs/registro-de-versoes-V2_5.md. Validation: suspensao 54/54 (inclui exemplos da Milliken p. 683, p. 592, Tab. 16.3, Seward 4.1, Gillespie 5-8), "
                      "Excel x Python (test_workbook e test_workbook_suspensao). NOT_VALIDATED fisicamente. Autor: nao registrado.")
    registro.append({"aba": "15_CHANGELOG", "cel": "A16:C16", "antes": None, "novo": "(linha V2.5)", "ref": "EDR-043"})

    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return registro


def escrever_registro(registro: list[dict], caminho: Path) -> None:
    def fmt(v):
        if v is None:
            return "(vazia)"
        s = str(v).replace("|", "\\|")
        return f"`{s}`" if s.startswith("=") else s
    linhas = ["| Aba | Célula | Antes | Depois | Fonte / EDR |", "|---|---|---|---|---|"]
    for r in registro:
        linhas.append(f"| {r['aba']} | {r['cel']} | {fmt(r['antes'])} | {fmt(r['novo'])} | {r['ref']} |")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default=str(AQUI.parent / "excel" / "FSAE_EV_Suspension_Fase1_V2_4.xlsx"))
    ap.add_argument("out", nargs="?", default=str(AQUI.parent / "build" / "FSAE_EV_Suspension_Fase1_V2_5.xlsx"))
    ap.add_argument("--layout", default=str(AQUI.parent / "data" / "layout_V2_4.json"))
    ap.add_argument("--registro", default=None)
    a = ap.parse_args()
    if Path(a.out).resolve() == Path(a.src).resolve():
        raise SystemExit("saída igual à origem: recusado (nunca sobrescrever a planilha entregue)")
    layout = json.loads(Path(a.layout).read_text(encoding="utf-8"))
    reg = aplicar(Path(a.src), Path(a.out), layout)
    if a.registro:
        escrever_registro(reg, Path(a.registro))
    print("salvo", a.out, "células alteradas", len(reg))


if __name__ == "__main__":
    main()
