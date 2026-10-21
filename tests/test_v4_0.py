"""
Testes da fundação da V4.0 (incremento 3): nomes definidos e dados por chave.
TC-WB40-001 (ID autorizado pelo usuário): tabela de nomes gerada da V3.0 da tag v3.0 é válida e completa
(nomes únicos e aceitos pelo Excel, células existentes, entradas e resultados cobertos, CSV commitado em dia) e
`verificar_cobertura` recusa entrada sem nome, listando as células.
TC-WB40-002: a V4.0 gerada da tag tem exatamente os nomes da tabela (nome -> destino, escopo do workbook), as mesmas
abas e as 387 fórmulas da V3.0 com texto idêntico, valores iguais fora das células de `alteracoes_v4_0()`, e o gerador
recusa saída em excel/ ou igual à origem antes de abrir qualquer arquivo.
TC-WB40-003: CA-07 da V4.0: a regeneração a partir da tag é igual à excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx
(células, fórmulas, nomes definidos, validações e formatação condicional).
TC-WB40-004: dados por chave (python/dados_planilha.py e tools/migrar_dados_v3_v4.py): a V4.0 de referência lida
pelos nomes é igual à V3.0 da tag lida pelos endereços; ida e volta de 5 entradas (valor, Origem e Fonte) de abas
diferentes; conflito listado com base, destino e novo, sem sobrescrever, e a CLI sai com código 1; recusa de saída em
excel/ ou igual à origem antes de abrir qualquer arquivo; célula alterada na viva fora da tabela é erro que a lista;
erro de dado na CLI (entrada com fórmula, abas diferentes da tag, comentário ou hiperlink novo na viva) sai com
código 2 e reescreve o relatório com o erro, listando os objetos; a tag sem mudança passa pela CLI com código 0.
Roda como script: uv run python -X utf8 tests/test_v4_0.py
A V3.0 de partida é o arquivo da tag v3.0, extraído para uma pasta temporária (nunca a planilha viva).
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.comments import Comment
from openpyxl.utils import column_index_from_string
from openpyxl.worksheet.formula import ArrayFormula

import atualizar_planilha as ap
import dados_planilha as dp
import gerar_v4_0 as gv
import nomes_v4_0 as nv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import comparar_planilhas as cp  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = Path(HERE).parent
CSV_NOMES = RAIZ / "data" / "nomes_V4_0.csv"
TAG_V30 = "v3.0"
CAMINHO_V30 = "excel/FSAE_EV_Suspension_Fase1_V3_0.xlsx"
results = []


def raises(fn, exc=ValueError, needle=None):
    try:
        fn()
        return False
    except exc as e:
        return needle is None or needle in str(e)


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def extrair_v30(pasta: Path) -> Path:
    """Arquivo da tag v3.0 numa pasta temporária (binário, sem passar por texto)."""
    destino = pasta / "V3_0_tag.xlsx"
    with open(destino, "wb") as f:
        subprocess.run(["git", "show", f"{TAG_V30}:{CAMINHO_V30}"], cwd=RAIZ, stdout=f, check=True)
    return destino


def eh_formula(v) -> bool:
    return isinstance(v, ArrayFormula) or (isinstance(v, str) and v.startswith("="))


with tempfile.TemporaryDirectory() as tmp:
    v30 = extrair_v30(Path(tmp))
    tabela = nv.tabela_nomes(v30)
    wb = openpyxl.load_workbook(v30)
    try:
        formulas = {(ws.title, c.coordinate) for ws in wb.worksheets if ws.title[:2] in nv.ABAS_RES
                    for lin in ws.iter_rows() for c in lin if eh_formula(c.value)}
        abas = set(wb.sheetnames)
        dims = {ws.title: (ws.max_row, ws.max_column) for ws in wb.worksheets}
    finally:
        wb.close()

    # ---------------- TC-WB40-001 ----------------
    nomes = [n.nome for n in tabela]
    unicos = len(set(nomes)) == len(nomes)
    invalidos = [n for n in nomes if not nv.NOME_VALIDO.fullmatch(n)]
    referencias = [n for n in nomes if nv.parece_referencia(n)]

    def existe(aba, cel):
        if aba not in abas:
            return False
        m = re.fullmatch(r"([A-Z]+)(\d+)", cel)
        return bool(m) and int(m.group(2)) <= dims[aba][0] and column_index_from_string(m.group(1)) <= dims[aba][1]

    inexistentes = [(n.aba, n.celula) for n in tabela if not existe(n.aba, n.celula)]
    por_celula: dict = {}
    for n in tabela:
        por_celula.setdefault((n.aba, n.celula), []).append(n)
    duplicadas = [k for k, v in por_celula.items() if len(v) > 1]
    entradas = ap.celulas_de_entrada()
    ent_mal = sorted(k for k in entradas
                     if len(por_celula.get(k, [])) != 1 or por_celula[k][0].papel not in ("ent", "org", "fte"))
    ent_sobra = sorted(k for k, v in por_celula.items() if v[0].papel in ("ent", "org", "fte") and k not in entradas)
    res_mal = sorted(k for k in formulas if len(por_celula.get(k, [])) != 1 or por_celula[k][0].papel != "res")
    res_sobra = sorted(k for k, v in por_celula.items() if v[0].papel == "res" and k not in formulas)
    papeis_ok = all(n.papel in ("ent", "org", "fte", "res") for n in tabela)
    convencao = [n.nome for n in tabela if not n.nome.startswith(f"{n.papel}_{n.aba[:2]}_")]
    sus_mal = [n.nome for n in tabela if n.sus_id and not all(re.fullmatch(r"SUS-\d{3}(-[FR])?", s)
                                                               for s in n.sus_id.split(";"))]
    ordem_ok = tabela == sorted(tabela, key=lambda n: (n.aba, int(re.sub(r"[A-Z]", "", n.celula)),
                                                         column_index_from_string(re.sub(r"\d", "", n.celula))))
    deterministica = nv.tabela_nomes(v30) == tabela
    csv_igual = CSV_NOMES.exists() and nv.ler_tabela(CSV_NOMES) == tabela
    csv_lf = CSV_NOMES.exists() and b"\r" not in CSV_NOMES.read_bytes()
    csv_cab = CSV_NOMES.exists() and CSV_NOMES.read_bytes().split(b"\n", 1)[0] == b"nome,aba,celula,papel,sus_id,rotulo"
    # Ida e volta do CSV numa pasta temporária (UTF-8, LF, rótulos com vírgula, aspas e acento).
    with tempfile.TemporaryDirectory() as tmp2:
        p = Path(tmp2) / "nomes.csv"
        nv.escrever_tabela(tabela, p)
        ida_volta = nv.ler_tabela(p) == tabela
    # verificar_cobertura (antigo 009): passa com tudo coberto; sem um nome, ValueError que lista as células.
    cob_ok = not raises(lambda: nv.verificar_cobertura(tabela, entradas), Exception)
    faltam = [("05_VEHICLE", "B5"), ("10_TIRE", "B86")]
    parcial = [n for n in tabela if (n.aba, n.celula) not in faltam]
    cob_erro = raises(lambda: nv.verificar_cobertura(parcial, entradas), ValueError, "05_VEHICLE!B5") and \
        raises(lambda: nv.verificar_cobertura(parcial, entradas), ValueError, "10_TIRE!B86")
    ref_ok = all(nv.parece_referencia(x) for x in ("A1", "xfd1048576", "R1C1", "r", "C", "RC", "R12", "abc7")) and \
        not any(nv.parece_referencia(x) for x in ("XFE1", "A1048577", "A0", "res_05_x1", "ent_10_b", "R1C1_x"))
    regex_ok = all(nv.NOME_VALIDO.fullmatch(x) for x in ("a", "ent_05_x", "A" * 255)) and \
        not any(nv.NOME_VALIDO.fullmatch(x) for x in ("1a", "_a", "a-b", "a b", "ação", "A" * 256, ""))
    cont = {p: sum(1 for n in tabela if n.papel == p) for p in ("ent", "org", "fte", "res")}
    # Correção 1 (controlador): letras gregas transliteradas; sus_id só do rótulo e da coluna de ID, nunca da Fonte.
    grego_ok = nv.slug("α [rad]") == "alfa_rad" and nv.slug("Δ Fz (μ, γ)") == "delta_fz_mu_gama" and         nv.slug("Kyγ0 ε") == "kygama0_epsilon" and nv.slug("ÿ Ж z") == "y_z"
    sus_de = {(n.aba, n.celula): n.sus_id for n in tabela}
    sus_rotulo_ok = sus_de.get(("05_VEHICLE", "B5")) == "SUS-002" and sus_de.get(("05_VEHICLE", "F5")) == "SUS-002"
    ok_001 = all((grego_ok, sus_rotulo_ok, unicos, not invalidos, not referencias, not inexistentes, not duplicadas, not ent_mal, not ent_sobra,
                  not res_mal, not res_sobra, papeis_ok, not convencao, not sus_mal, ordem_ok, deterministica, csv_igual,
                  csv_lf, csv_cab, ida_volta, cob_ok, cob_erro, ref_ok, regex_ok))
    check("TC-WB40-001: tabela de nomes da V3.0 (tag) com nomes únicos, válidos e sem cara de referência; células "
          "existentes; cada entrada uma vez como ent/org/fte e cada fórmula das abas 05..14 como res; CSV em dia (UTF-8, "
          "LF); verificar_cobertura lista as células sem nome",
          ok_001,
          f"{len(tabela)} nomes {cont}; únicos={unicos} inválidos={invalidos[:3]} ref={referencias[:3]} "
          f"inexistentes={inexistentes[:3]} dup={duplicadas[:3]} ent={ent_mal[:3]}/{ent_sobra[:3]} "
          f"res={res_mal[:3]}/{res_sobra[:3]} papéis={papeis_ok} conv={convencao[:3]} sus={sus_mal[:3]} "
          f"ordem={ordem_ok} det={deterministica} csv={csv_igual}/{csv_lf}/{csv_cab} ida_volta={ida_volta} "
          f"cobertura={cob_ok}/{cob_erro} ref={ref_ok} regex={regex_ok} grego={grego_ok} sus_rótulo={sus_rotulo_ok} | fórmulas={len(formulas)} entradas={len(entradas)}")

    # ---------------- TC-WB40-002 ----------------
    # Gerador: nomes exatos da tabela (escopo do workbook), mesmas fórmulas e valores da V3.0 fora de alteracoes_v4_0(),
    # registro com o "antes" lido da origem; recusa de saída em excel/ ou igual à origem, sem abrir nem criar arquivo.
    v40 = Path(tmp) / "V4_0.xlsx"
    registro = gv.gerar(v30, v40, tabela)
    alts = gv.alteracoes_v4_0()
    alteradas = {(a["aba"], a["cel"]) for a in alts}
    esperados = {n.nome: f"'{n.aba}'!${re.sub(r'[0-9]', '', n.celula)}${re.sub(r'[A-Z]', '', n.celula)}" for n in tabela}
    wb4 = openpyxl.load_workbook(v40)
    try:
        nomes4 = {k: d.attr_text for k, d in wb4.defined_names.items()}
        locais = [(ws.title, k) for ws in wb4.worksheets for k in ws.defined_names]
        a3 = wb4["00_README"]["A3"].value
        calc = wb4.calculation.fullCalcOnLoad
        novos = {(a["aba"], a["cel"]): wb4[a["aba"]][a["cel"]].value for a in alts}
    finally:
        wb4.close()
    wb3 = openpyxl.load_workbook(v30)
    try:
        nomes3 = {k: d.attr_text for k, d in wb3.defined_names.items()}
        antes3 = {(a["aba"], a["cel"]): wb3[a["aba"]][a["cel"]].value for a in alts}
    finally:
        wb3.close()
    nomes_ok = nomes4 == {**nomes3, **esperados} and "Origens" in nomes3 and not locais
    ok_cmp, rel_cmp = cp.comparar_v40(v40, v30, alteradas, nomes=esperados)
    ok_neg, _ = cp.comparar_v40(v40, v30, set(), nomes=esperados)   # sem as alteradas, a A3 tem de aparecer como diferença
    a3_ok = a3 == gv.TEXTO_A3 and ("00_README", "A3") in alteradas
    novos_ok = all(novos[k] == a["novo"] for a in alts for k in [(a["aba"], a["cel"])]) and \
        {k[0] for k in alteradas} == {"00_README", "15_CHANGELOG"} and len(alteradas) == 4
    reg_cel = [r for r in registro if r["aba"] != "(workbook)"]
    reg_ok = [(r["aba"], r["cel"], r["antes"], r["novo"]) for r in reg_cel] == \
        [(a["aba"], a["cel"], antes3[(a["aba"], a["cel"])], a["novo"]) for a in alts] and \
        all(antes3[k] is None for k in alteradas if k[0] == "15_CHANGELOG") and all(r["ref"] for r in registro)
    # Recusas antes de abrir: origem inexistente com saída em excel/ dá SystemExit (não FileNotFoundError).
    fantasma = Path(tmp) / "nao_existe.xlsx"
    saida_excel = RAIZ / "excel" / "_teste_recusa_V4_0.xlsx"
    rec_excel = raises(lambda: gv.gerar(fantasma, saida_excel, tabela), SystemExit) and not saida_excel.exists()
    rec_viva = raises(lambda: gv.gerar(fantasma, RAIZ / CAMINHO_V30, tabela), SystemExit)
    bytes_v30 = v30.read_bytes()
    rec_origem = raises(lambda: gv.gerar(v30, v30, tabela), SystemExit) and v30.read_bytes() == bytes_v30
    ok_002 = all((nomes_ok, ok_cmp, not ok_neg, a3_ok, novos_ok, reg_ok, calc, rec_excel, rec_viva, rec_origem))
    check("TC-WB40-002: V4.0 gerada da tag com exatamente os nomes da tabela (escopo do workbook, Origens mantido); "
          "mesmas abas e 387 fórmulas idênticas; valores iguais fora de alteracoes_v4_0(); registro com o antes da "
          "origem; recusa saída em excel/ e saída = origem sem abrir nem criar arquivo",
          ok_002,
          f"nomes={nomes_ok} ({len(nomes4)} = {len(nomes3)} + {len(esperados)}; locais={locais[:3]}) comparar_v40={ok_cmp} "
          f"negativo={not ok_neg} A3={a3_ok} novos={novos_ok} registro={reg_ok} fullCalcOnLoad={calc} "
          f"recusas={rec_excel}/{rec_viva}/{rec_origem}" + ("" if ok_cmp else " | " + " ; ".join(rel_cmp[-6:])))

    # ---------------- TC-WB40-003 ----------------
    # CA-07 da V4.0: a regeneração (da tag, com o CSV commitado) é igual à excel/…V4_0.xlsx, inclusive os nomes definidos.
    entregue = RAIZ / "excel" / "FSAE_EV_Suspension_Fase1_V4_0.xlsx"
    regen = Path(tmp) / "V4_0_regen.xlsx"
    gv.gerar(v30, regen, nv.ler_tabela(CSV_NOMES))
    if entregue.exists():
        ok_ca07, rel_ca07 = cp.comparar_xlsx(regen, entregue, cp.FORMULAS_ESPERADAS_V40, estrutura=True)
    else:
        ok_ca07, rel_ca07 = False, [f"não existe: {entregue}"]
    check("TC-WB40-003: CA-07 da V4.0: regeneração a partir da tag v3.0 igual à excel/FSAE_EV_Suspension_Fase1_V4_0.xlsx "
          "(células, 387 fórmulas, nomes definidos, validações, formatação condicional, colunas ocultas)",
          ok_ca07, " ; ".join(r for r in rel_ca07 if not r.startswith("  DIF"))[:400] +
          ("" if ok_ca07 else " | " + " ; ".join(rel_ca07[:8])))

    # ---------------- TC-WB40-004 ----------------
    # Dados por chave: equivalência (antigo 005), ida e volta (006), conflito (007) e recusas do injetor (008).


    CLI = RAIZ / "tools" / "migrar_dados_v3_v4.py"
    ref40 = entregue
    dados_nomes = {n.nome for n in tabela if n.papel in dp.PAPEIS_DADOS}
    por_end = dp.ler_por_endereco(v30, tabela)
    por_nome = dp.ler_por_nome(ref40)
    equiv = set(por_end) == set(por_nome) == dados_nomes and \
        all(dp.iguais(por_end[k], por_nome[k]) for k in dados_nomes)
    # 5 linhas de abas diferentes com valor, Origem e Fonte; valores de teste rotulados (sintéticos).
    linhas: dict = {}
    for n in tabela:
        if n.papel in dp.PAPEIS_DADOS:
            linhas.setdefault((n.aba, nv._partes(n.celula)[1]), {})[n.papel] = n
    escolhidas, abas_usadas = [], set()
    for (aba, _), g in sorted(linhas.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if aba not in abas_usadas and set(g) == {"ent", "org", "fte"} and isinstance(por_end[g["ent"].nome], (int, float)):
            escolhidas.append(g)
            abas_usadas.add(aba)
        if len(escolhidas) == 5:
            break
    novos = {}
    for g in escolhidas:
        e, o, f = g["ent"].nome, g["org"].nome, g["fte"].nome
        novos[e] = por_end[e] + 1.25
        novos[o] = "○ Arbitrário / demonstrativo" if por_end[o] != "○ Arbitrário / demonstrativo" else "? A confirmar"
        novos[f] = "TESTE TC-WB40-004: valor sintético, não é dado do carro"
    viva = Path(tmp) / "viva_teste.xlsx"
    shutil.copy(v30, viva)
    wbv = openpyxl.load_workbook(viva)
    por_nome_tab = {n.nome: n for n in tabela}
    for k, v in novos.items():
        wbv[por_nome_tab[k].aba][por_nome_tab[k].celula].value = v
    wbv.save(viva)
    wbv.close()
    dados_viva = dp.ler_por_endereco(viva, tabela)
    saida_ok = Path(tmp) / "V4_0_com_dados.xlsx"
    r1 = dp.injetar(ref40, dados_viva, saida_ok)
    lido = dp.ler_por_nome(saida_ok)
    ida_volta_ok = len(novos) == 15 and len(escolhidas) == 5 and sorted(r1.escritas) == sorted(novos) and \
        not r1.conflitos and not r1.faltando and len(r1.iguais) == len(dados_nomes) - 15 and \
        set(lido) == dados_nomes and all(dp.iguais(lido[k], novos.get(k, por_nome[k])) for k in dados_nomes)
    # Diferença viva x tag: exatamente as 15 células; com uma célula fora da tabela, verificar_cobertura a lista.
    alt_viva = dp.celulas_alteradas(viva, v30)
    so_dados = [n for n in tabela if n.papel in dp.PAPEIS_DADOS]
    alt_ok = alt_viva == {(por_nome_tab[k].aba, por_nome_tab[k].celula) for k in novos} and \
        not raises(lambda: nv.verificar_cobertura(so_dados, alt_viva), Exception) and \
        raises(lambda: nv.verificar_cobertura(so_dados, alt_viva | {("05_VEHICLE", "Z200")}), ValueError,
               "05_VEHICLE!Z200")
    # Conflito: numa cópia da V4.0, uma das 5 entradas já mudou para outro valor.
    v40_mod = Path(tmp) / "V4_0_editada.xlsx"
    shutil.copy(ref40, v40_mod)
    alvo = escolhidas[0]["ent"]
    outro = novos[alvo.nome] + 10.0
    wbm = openpyxl.load_workbook(v40_mod)
    wbm[alvo.aba][alvo.celula].value = outro
    wbm.save(v40_mod)
    wbm.close()
    saida_conf = Path(tmp) / "V4_0_conflito.xlsx"
    r2 = dp.injetar(v40_mod, dados_viva, saida_conf, base=por_nome)
    lido2 = dp.ler_por_nome(saida_conf)
    conflito_ok = r2.conflitos == [(alvo.nome, por_nome[alvo.nome], outro, novos[alvo.nome])] and \
        sorted(r2.escritas) == sorted(k for k in novos if k != alvo.nome) and lido2[alvo.nome] == outro and \
        all(dp.iguais(lido2[k], novos[k]) for k in novos if k != alvo.nome)
    env = {**os.environ, "PYTHONUTF8": "1"}
    rel_md = Path(tmp) / "migracao.md"
    cli1 = subprocess.run([sys.executable, "-X", "utf8", str(CLI), str(viva), "--v40", str(v40_mod), "--saida",
                           str(Path(tmp) / "cli_conf.xlsx"), "--relatorio", str(rel_md)],
                          cwd=RAIZ, capture_output=True, text=True, env=env)
    texto_md = rel_md.read_text(encoding="utf-8") if rel_md.exists() else ""
    cli_conf_ok = cli1.returncode == 1 and alvo.nome in texto_md and "onflito" in texto_md
    rel_md0 = Path(tmp) / "migracao0.md"
    cli0 = subprocess.run([sys.executable, "-X", "utf8", str(CLI), str(viva), "--v40", str(ref40), "--saida",
                           str(Path(tmp) / "cli_ok.xlsx"), "--relatorio", str(rel_md0)],
                          cwd=RAIZ, capture_output=True, text=True, env=env)
    cli_ok_ok = cli0.returncode == 0 and rel_md0.exists() and \
        dp.ler_por_nome(Path(tmp) / "cli_ok.xlsx") == lido
    # Recusas antes de abrir. Saída em excel/: origem inexistente, então nada pode ser lido nem gravado. Saída = origem:
    # uma cópia temporária como origem e saída (isola a regra e nunca toca excel/, mesmo se as recusas regredirem).
    fantasma = Path(tmp) / "nao_existe.xlsx"
    saida_excel = RAIZ / "excel" / "_teste_recusa_injetor.xlsx"
    copia_rec = Path(tmp) / "V4_0_copia_recusa.xlsx"
    shutil.copy(ref40, copia_rec)
    bytes_copia = copia_rec.read_bytes()
    rec_inj = raises(lambda: dp.injetar(fantasma, {}, saida_excel), SystemExit) and not saida_excel.exists() and \
        raises(lambda: dp.injetar(copia_rec, {}, copia_rec), SystemExit) and copia_rec.read_bytes() == bytes_copia
    cli_rec = subprocess.run([sys.executable, "-X", "utf8", str(CLI), str(fantasma), "--saida", str(saida_excel),
                              "--relatorio", str(Path(tmp) / "rec.md")],
                             cwd=RAIZ, capture_output=True, text=True, env=env)
    rec_cli = cli_rec.returncode != 0 and "recusad" in (cli_rec.stdout + cli_rec.stderr) and \
        not saida_excel.exists() and not (Path(tmp) / "rec.md").exists()

    # Erro de dado na CLI: código 2, relatório reescrito com o erro (o antigo não pode parecer atual), sem saída.
    def cli_erro(viva_err: Path, rotulo: str):
        md, sai = Path(tmp) / f"erro_{rotulo}.md", Path(tmp) / f"erro_{rotulo}.xlsx"
        md.write_text("RELATÓRIO ANTIGO\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-X", "utf8", str(CLI), str(viva_err), "--v40", str(ref40), "--saida",
                            str(sai), "--relatorio", str(md)], cwd=RAIZ, capture_output=True, text=True, env=env)
        txt = md.read_text(encoding="utf-8") if md.exists() else ""
        return r, txt, r.returncode == 2 and "RELATÓRIO ANTIGO" not in txt and "ERRO" in txt and not sai.exists()

    # (1) entrada `ent` da viva com fórmula: ValueError do injetor vira código 2 com o erro no relatório.
    alvo_f = escolhidas[1]["ent"]
    viva_f = Path(tmp) / "viva_formula.xlsx"
    shutil.copy(v30, viva_f)
    wbf = openpyxl.load_workbook(viva_f)
    wbf[alvo_f.aba][alvo_f.celula].value = "=1+1"
    wbf.save(viva_f)
    wbf.close()
    rf, txt_f, base_f = cli_erro(viva_f, "formula")
    erro_formula_ok = base_f and alvo_f.nome in txt_f
    # (3) viva com uma aba a mais: mensagem própria, código 2.
    viva_a = Path(tmp) / "viva_abas.xlsx"
    shutil.copy(v30, viva_a)
    wba = openpyxl.load_workbook(viva_a)
    wba.create_sheet("99_EXTRA_TESTE")
    wba.save(viva_a)
    wba.close()
    ra, txt_a, base_a = cli_erro(viva_a, "abas")
    erro_abas_ok = base_a and "abas da viva diferentes das da V3.0 da tag" in ra.stderr and \
        "99_EXTRA_TESTE" in txt_a and raises(lambda: dp.celulas_alteradas(viva_a, v30), dp.AbasDiferentes)
    # (4) viva com um comentário novo e um hiperlink novo (valores das células intactos): código 2 com os dois listados
    # (aba!célula e tipo); a tag sem mudança passa (código 0).
    viva_o = Path(tmp) / "viva_objetos.xlsx"
    shutil.copy(v30, viva_o)
    wbo = openpyxl.load_workbook(viva_o)
    cel_link = wbo["00_README"]["A1"]
    link_sem_mudar_valor = cel_link.value is not None and wbo["02_REQUIREMENTS"]["A1"].comment is None and \
        cel_link.hyperlink is None
    cel_link.hyperlink = "https://exemplo.invalid/teste-tc-wb40-004"
    wbo["02_REQUIREMENTS"]["A1"].comment = Comment("TESTE TC-WB40-004: comentário sintético", "teste")
    wbo.save(viva_o)
    wbo.close()
    ro, txt_o, base_o = cli_erro(viva_o, "objetos")
    obj_lista = dp.objetos_alterados(viva_o, v30)
    erro_obj_ok = base_o and link_sem_mudar_valor and \
        obj_lista == [("00_README", "A1", "hiperlink"), ("02_REQUIREMENTS", "A1", "comentário")] and \
        "00_README!A1 (hiperlink)" in txt_o and "02_REQUIREMENTS!A1 (comentário)" in txt_o and \
        "não são migrados" in txt_o and not dp.celulas_alteradas(viva_o, v30)
    md_tag, sai_tag = Path(tmp) / "migracao_tag.md", Path(tmp) / "cli_tag.xlsx"
    cli_tag = subprocess.run([sys.executable, "-X", "utf8", str(CLI), str(v30), "--v40", str(ref40), "--saida",
                              str(sai_tag), "--relatorio", str(md_tag)], cwd=RAIZ, capture_output=True, text=True, env=env)
    tag_ok = cli_tag.returncode == 0 and sai_tag.exists() and dp.objetos_alterados(v30, v30) == []
    ok_004 = all((equiv, ida_volta_ok, alt_ok, conflito_ok, cli_conf_ok, cli_ok_ok, rec_inj, rec_cli, erro_formula_ok,
                  erro_abas_ok, erro_obj_ok, tag_ok))
    check("TC-WB40-004: dados por chave: V4.0 lida por nome = V3.0 (tag) lida por endereço; ida e volta de 5 entradas "
          "(15 nomes: valor, Origem, Fonte) sem tocar o resto; conflito listado (base, destino, novo) sem sobrescrever e "
          "CLI com código 1 (0 sem conflito); célula da viva fora da tabela listada; recusa de saída em excel/ ou = origem; "
          "erro de dado (entrada com fórmula, abas diferentes, comentário e hiperlink novos, listados) sai com 2 e reescreve "
          "o relatório; a tag sem mudança sai com 0",
          ok_004,
          f"equiv={equiv} ({len(por_end)} dados) ida_volta={ida_volta_ok} (escritas={len(r1.escritas)} "
          f"iguais={len(r1.iguais)} conf={r1.conflitos[:2]} falt={r1.faltando[:3]}) alteradas={alt_ok} "
          f"conflito={conflito_ok} ({r2.conflitos[:2]}) cli_conf={cli_conf_ok} (rc={cli1.returncode}) "
          f"cli_ok={cli_ok_ok} (rc={cli0.returncode}) recusas={rec_inj}/{rec_cli} "
          f"erro_formula={erro_formula_ok} (rc={rf.returncode}) erro_abas={erro_abas_ok} (rc={ra.returncode}) "
          f"erro_objetos={erro_obj_ok} (rc={ro.returncode}, {obj_lista}) tag={tag_ok} (rc={cli_tag.returncode})"
          + ("" if cli_conf_ok and cli_ok_ok else f" | stderr: {(cli1.stderr + cli0.stderr)[-300:]}")
          + ("" if erro_formula_ok and erro_abas_ok else f" | stderr: {(rf.stderr + ra.stderr)[-400:]}")
          + ("" if erro_obj_ok and tag_ok else f" | stderr: {(ro.stderr + cli_tag.stderr)[-400:]}"))


# ---------------- Resumo ----------------
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
