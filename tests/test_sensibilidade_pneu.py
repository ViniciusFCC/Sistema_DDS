"""Testes do pneu-1 (sensibilidade do pneu e arrasto induzido), EDR-075. Script com check(), não pytest.

TC-SEN-001 a 005 não precisam do .tir: catálogo, leitura, edição e gravação do caso, e o x da planilha.
TC-SEN-016 a 019 (regra de muda decisão e Resultado) também não precisam do .tir.
TC-SEN-006 a 008, 010 a 015 e 020 a 022 (linha de comando) precisam dos .tir do TTC Round 6 (DDS_TTC_DIR ou references/ttc/..., a regra de
caso_pneu1.achar_ttc): sem eles, a seção imprime NÃO EXECUTÁVEL e o script sai com o código 3 depois das outras.
Os dados do teste são SINTÉTICOS de teste, não são dado do carro (números do veiculo_base de tests/test_equilibrio.py).
"""
from __future__ import annotations

import copy
import dataclasses
import json
import tempfile
from pathlib import Path

import aba_equilibrio as ae
import caso_planilha as cpl
import caso_pneu1 as cp
import comparacao_pressao as cmp
import equilibrio as eq
import equilibrio_linear as el
import math
import sensibilidade_pneu as sp
from suspension_model import G

results = []


def check(name, cond, detail=""):
    results.append((name, "PASS" if cond else "FAIL"))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def encerrar():
    print("\n--- Resumo ---")
    n = sum(1 for _, s in results if s == "PASS")
    f = len(results) - n
    print(f"{n} PASS, {f} FAIL, de {len(results)} testes")
    if f:
        raise SystemExit(1)


def levanta(fn, trecho) -> bool:
    """True se fn() levanta ValueError com `trecho` na mensagem."""
    try:
        fn()
    except ValueError as exc:
        return trecho in str(exc)
    return False


# SINTÉTICO de teste, não é dado do carro: valor de cada campo (chave do JSON -> valor)
SINT = {
    "m_sem_piloto_kg": 182.0, "m_piloto_kg": 68.0, "h_cg_m": 0.300, "L_m": 1.55, "tF_m": 1.200, "tR_m": 1.150,
    "f_dianteira": 0.46, "muF_kg": 15.0, "muR_kg": 18.0, "d_pneu_F_pol": 18.1, "d_pneu_R_pol": 18.1,
    "razao_hns_F": 1.0, "razao_hns_R": 1.0,
    "KsF_N_m": 40000.0, "KsR_N_m": 45000.0, "MRF": 1.2, "MRR": 1.1, "KarbF_Nm_rad": 3000.0, "KarbR_Nm_rad": 2000.0,
    "zF_m": 0.030, "zR_m": 0.050, "KTF_N_m": 120000.0, "KTR_N_m": 120000.0,
    "DF_N": 400.0, "bal_dianteira": 0.45,
    "dgF_grau_mm": -0.02, "dgR_grau_mm": -0.02, "epsF_rad_rad": 0.0, "epsR_rad_rad": 0.0,
    "gsFL_grau": -1.5, "gsFR_grau": -1.5, "gsRL_grau": -1.0, "gsRR_grau": -1.0, "eixos_tir": "ISO_TYDEX",
    "sentido": "Esquerda", "toeFL_grau": 0.0, "toeFR_grau": 0.0, "toeRL_grau": 0.0, "toeRR_grau": 0.0,
    "R_m": 9.125, "cg_lateral_m": 0.0, "cza_m2": None, "rho_kg_m3": None, "cda_m2": None, "crr": None,
    "h2": 0, "h3": 0, "h7": 0, "h8": 0, "h9": 0, "h2v": 1, "h9v": 1, "fator_neutro": 4 / 3,
    "ackermann_pct": None, "crr_referencia": None,
}


def dados_sinteticos() -> dict:
    campos = {}
    for k, c in cp.CAMPOS.items():
        v = SINT.get(k, 1.0 if k.startswith("lambda_") else None)
        campos[k] = {"valor": v, "unidade": c.unidade, "origem": cp.ORIGEM_A_CONFIRMAR if v is None
                     else "○ Arbitrário / demonstrativo", "fonte": "SINTÉTICO de teste, não é dado do carro",
                     "rotulo": c.rotulo, "unidade_exibicao": c.unidade, "descricao": c.descricao, "editado": False}
    return {"schema": cp.SCHEMA, "aviso": "SINTÉTICO de teste, não é dado do carro", "captura": {}, "campos": campos}


D = dados_sinteticos()

# TC-SEN-001: res_ pela regra da D2 (a, b, m, huF, huR) e o x serve à verificação da planilha
x = cp.x_de_dados(D)
x2 = cp.x_de_dados(cp.editar(D, L_m=1.60))
motivo = ae.motivo_das_entradas(x, ae.VERIFICACOES_V43)
check("TC-SEN-001 x_de_dados: a, b, m, huF, huR pela regra da D2",
      x["a"] == 1.55 * (1 - 0.46) and x["b"] == 1.55 * 0.46 and x["m"] == 182.0 + 68.0
      and x["huF"] == 18.1 * 0.0254 / 2 * 1.0 and x["huR"] == 18.1 * 0.0254 / 2 * 1.0
      and x2["a"] == 1.60 * (1 - 0.46) and x2["b"] == 1.60 * 0.46 and x2["a"] + x2["b"] == 1.60
      and x["coef"] == [1.0] * len(cp.LAMBDAS) and x["motivo_r"] == "" and x["R"] == 9.125
      and x["fator"] == 4 / 3 and motivo is None, f"motivo={motivo}")

# TC-SEN-002: editar devolve cópia; origem e editado; aplicar_set = editar
copia = copy.deepcopy(D)
E = cp.editar(D, h_cg_m=0.31)
iguais = all(E["campos"][k] == D["campos"][k] for k in D["campos"] if k != "h_cg_m")
check("TC-SEN-002 editar: cópia, origem e editado; aplicar_set igual",
      D == copia and E is not D and E["campos"]["h_cg_m"]["valor"] == 0.31
      and E["campos"]["h_cg_m"]["origem"] == cp.ORIGEM_EDITADO and E["campos"]["h_cg_m"]["editado"] is True
      and iguais and cp.aplicar_set(D, ["h_cg_m=0.31"]) == E)

# TC-SEN-003: salvar_caso recusa o demonstrativo (mesmo caminho, relativo, maiúsculas); gravação volta igual
rel = Path("data") / "casos" / "caso_pneu1_demonstrativo.json"
with tempfile.TemporaryDirectory() as tmp:
    salvo = cp.salvar_caso(E, Path(tmp) / "caso.json")
    volta = cp.ler_caso(salvo)
recusas = [levanta(lambda c=c: cp.salvar_caso(D, c), "demonstrativo")
           for c in (cp.CAMINHO_DEMONSTRATIVO, rel, Path(str(cp.CAMINHO_DEMONSTRATIVO).upper()),
                     str(cp.CAMINHO_DEMONSTRATIVO))]
check("TC-SEN-003 salvar_caso recusa o demonstrativo e grava em outro caminho", all(recusas) and volta == E,
      f"recusas={recusas}")

# TC-SEN-004: aplicar_set recusa o que não é válido, com a chave na mensagem
check("TC-SEN-004 aplicar_set: chave desconhecida, valor ruim, sem =, chave 2, sentido minúsculo; Direita vale",
      levanta(lambda: cp.aplicar_set(D, ["massa=300"]), "massa")
      and levanta(lambda: cp.aplicar_set(D, ["L_m=abc"]), "L_m")
      and levanta(lambda: cp.aplicar_set(D, ["L_m"]), "L_m")
      and levanta(lambda: cp.aplicar_set(D, ["h2=2"]), "h2")
      and levanta(lambda: cp.aplicar_set(D, ["sentido=esquerda"]), "sentido")
      and cp.aplicar_set(D, ["sentido=Direita"])["campos"]["sentido"]["valor"] == "Direita")

# TC-SEN-005: valores_usados lista os campos e os 5 res_ (com aba e célula); campo nulo = ? A confirmar
vu = cp.valores_usados(D)
res = [v for v in vu if v.calculado_por is not None]
nulo = next(v for v in vu if v.chave == "cza_m2")
check("TC-SEN-005 valores_usados: todos os campos e os 5 res_ com a célula; nulo = ? A confirmar",
      len(vu) == len(cp.CAMPOS) + 5 and {v.chave for v in vu} >= set(cp.CAMPOS) and len(res) == 5
      and {v.calculado_por for v in res} == {"05_VEHICLE B4", "05_VEHICLE B9", "05_VEHICLE B10", "05_VEHICLE B16",
                                             "05_VEHICLE B17"}
      and nulo.valor is None and nulo.origem == cp.ORIGEM_A_CONFIRMAR and not nulo.editado)

# ---------------------------------------------------------------------------------------------------------------------
# Seção com .tir (TC-SEN-006 a 008)
# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------
# TC-SEN-016 a 019: regra de "muda decisão" e Resultado (sem .tir; ResultadoCarro sintético, como o rc() de
# tests/test_tire_pressure.py; os números são SINTÉTICOS de teste, não são dado do carro)
# ---------------------------------------------------------------------------------------------------------------------
NOS = (8.0, 10.0, 12.0, 14.0)


def rc(p, var, ay, borda=False, veredito="PUSH", res=0.01, robustez=None):
    """ResultadoCarro sintético: par={} e caso=None (escolher_pressao só lê par se ay_lim_ms2 for None)."""
    return cmp.ResultadoCarro(pressao_psi=p, variante_kt=var, ay_lim_ms2=ay, sentido_pior="esquerda",
                              eixo_satura=None, veredito=veredito, k_rad_ms2=None, k_motivo=None,
                              resolucao_ms2=res, borda_alfa=borda, robustez=robustez, rotulos=(), par={}, caso=None)


def serie_rc(var, ays, vereditos=None, robustezes=None):
    vs = vereditos or ["PUSH"] * 4
    rb = robustezes or [None] * 4
    return [rc(p, var, a, veredito=v, robustez=r) for p, a, v, r in zip(NOS, ays, vs, rb, strict=True)]


def banda(v):
    return cmp.Banda(v, True, {}, "banda sintética")


def vered(valores, b=0.5):
    return cmp.decidir(dict(zip(NOS, valores, strict=True)), {p: banda(b) for p in NOS}, {})


def escolhas(ay_vals, ca_vals, b=0.5):
    """(esc_ay, esc_ca) sintéticos a partir de Vereditos de `cmp.decidir`."""
    return (cmp.Escolha("a_y_lim", "máximo", {"KT (a)": vered(ay_vals, b)}, None, ()),
            cmp.Escolha("C_alpha_operacao", "máximo", {"eixo F": vered(ca_vals, b), "eixo R": vered(ca_vals, b)},
                        None, ()))


PUSH_ROB = ("PUSH", "mesmo sinal na varredura exploratória do pneu")
NC_ROB = eq.veredito_robusto([eq.PUSH, eq.LOOSE])       # NÃO CONCLUSIVO, "o sinal depende do pneu"
NC_NA_ROB = eq.veredito_robusto([eq.PUSH, eq.NA])      # NÃO CONCLUSIVO, "N/A em parte da varredura (sem inversão...)"
NA_ROB = ("N/A", "N/A em toda a varredura")
l_nao, _ = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[PUSH_ROB] * 4))
l_sim, c_sim = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[PUSH_ROB, PUSH_ROB, NC_ROB, PUSH_ROB]))
l_na, _ = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[PUSH_ROB, NA_ROB, PUSH_ROB, PUSH_ROB]))
l_nc_na, _ = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[NA_ROB, PUSH_ROB, NC_ROB, PUSH_ROB]))
l_loose, _ = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[("LOOSE", "x")] * 4))
l_semrob, _ = sp.decidir_lambda(serie_rc("a", [10.0] * 4))
l_nc_semi, c_semi = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[PUSH_ROB, NC_NA_ROB, PUSH_ROB, PUSH_ROB]))
l_nc_semi_sim, _ = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[NC_NA_ROB, PUSH_ROB, NC_ROB, PUSH_ROB]))
check("TC-SEN-016 decidir_lambda (D6): PUSH/LOOSE nas 4 -> não; NÃO CONCLUSIVO 'o sinal depende do pneu' -> sim; "
      "N/A -> não avaliado; esse + N/A -> sim; NÃO CONCLUSIVO 'N/A em parte…' numa pressão e PUSH nas outras -> "
      "não avaliado (e sim se outra pressão inverte o sinal); sem robustez -> não avaliado; critérios por pressão",
      l_nao == "não" and l_loose == "não" and l_sim == "sim" and l_na == "não avaliado" and l_nc_na == "sim"
      and l_nc_semi == "não avaliado" and l_nc_semi_sim == "sim" and "não avaliado" in c_semi["robustez de λ a 10,0 psi"]
      and l_semrob == "não avaliado" and len(c_sim) == 4 and all(isinstance(v, str) for v in c_sim.values()),
      f"{l_nao}, {l_loose}, {l_sim}, {l_na}, {l_nc_na}, {l_nc_semi}, {l_nc_semi_sim}, {l_semrob}")

# TC-SEN-017: pressão. Critério 1 (vereditos entre pressões) e critério 2 (D7, bandas)
planas = serie_rc("a", [10.0, 10.0, 10.0, 10.0])
ay_p, ca_p = escolhas([10.0] * 4, [100.0] * 4)
ay_p_real = cmp.escolher_pressao("a_y_lim", resultados_carro=planas)
p_nao, c_nao = sp.decidir_pressao(planas, ay_p_real, ca_p)
p_c1, c_c1 = sp.decidir_pressao(serie_rc("a", [10.0] * 4, vereditos=["PUSH", "PUSH", "PUSH", "LOOSE"]), ay_p, ca_p)
ay_d, ca_d = escolhas([10.0, 20.0, 10.0, 10.0], [100.0] * 4)           # o a_y_lim de 10 psi se destaca: D7
p_c2, _ = sp.decidir_pressao(planas, ay_d, ca_p)
ay_cd, ca_cd = escolhas([10.0] * 4, [100.0, 100.0, 300.0, 100.0])      # um eixo do Cα se destaca
p_c2b, _ = sp.decidir_pressao(planas, ay_p, ca_cd)
na = serie_rc("a", [None] * 4, vereditos=["N/A"] * 4)
ay_na = cmp.escolher_pressao("a_y_lim", resultados_carro=na)
p_na, c_na = sp.decidir_pressao(na, ay_na, ca_p)
p_na1, _ = sp.decidir_pressao(serie_rc("a", [10.0, 10.0, 10.0, None], vereditos=["PUSH", "PUSH", "PUSH", "N/A"]),
                              ay_p, ca_p)
# D7 revista: extremo não resolvido (banda só limite inferior) e 1 decidível só dão "não avaliado"
bd_ext = {8.0: cmp.Banda(0.1, False, {}, "x"), 10.0: banda(0.5), 12.0: banda(0.5), 14.0: cmp.Banda(0.1, False, {}, "x")}
v_nres = cmp.decidir(dict(zip(NOS, (5.0, 10.0, 10.2, 5.0), strict=True)), bd_ext, {})
v_um = cmp.decidir(dict(zip(NOS, (None, None, 10.0, None), strict=True)), {p: banda(0.5) for p in NOS}, {})
esc_nres = cmp.Escolha("a_y_lim", "máximo", {"KT (a)": v_nres}, None, ())
esc_um = cmp.Escolha("a_y_lim", "máximo", {"KT (a)": v_um}, None, ())
p_nres, c_nres = sp.decidir_pressao(planas, esc_nres, ca_p)
p_um, c_um = sp.decidir_pressao(planas, esc_um, ca_p)
# o ramo PUSH -> LOOSE de _frase_pressao (não pode sombrear ps()) e a frase agrupada do λ
try:
    fr_pl = sp._frase_pressao("sim", c_c1, serie_rc("a", [10.0] * 4, vereditos=["PUSH", "PUSH", "PUSH", "LOOSE"]))
except TypeError as exc:
    fr_pl = f"TypeError: {exc}"
_, c_lam = sp.decidir_lambda(serie_rc("a", [10.0] * 4, robustezes=[NC_NA_ROB, NC_NA_ROB, NC_NA_ROB, NA_ROB]))
fr_lam = sp._frase_lambda("não avaliado", c_lam)
check("TC-SEN-017 decidir_pressao: PUSH e bandas que não separam -> não; PUSH×LOOSE -> sim (critério 1); "
      "a_y_lim ou Cα se distinguem -> sim (critério 2); ay None -> não avaliado; um N/A isolado -> não avaliado",
      p_nao == "não" and p_c1 == "sim" and p_c2 == "sim" and p_c2b == "sim" and p_na == "não avaliado"
      and p_na1 == "não avaliado" and len(c_nao) >= 2 and len(c_c1) >= 2
      and p_nres == "não avaliado" and "não resolvida" in c_nres["a_y_lim, KT (a)"]
      and p_um == "não avaliado" and "menos de 2" in c_um["a_y_lim, KT (a)"]
      and "8,0 psi" in fr_pl and "14,0 psi" in fr_pl and "TypeError" not in fr_pl
      and fr_lam.count("o λ exploratório") == 1 and "a 8,0, 10,0 e 12,0 psi: NÃO CONCLUSIVO" in fr_lam
      and "a 14,0 psi: N/A em toda a varredura" in fr_lam and "N/A, N/A" not in fr_lam,
      f"{p_nao}, {p_c1}, {p_c2}, {p_c2b}, {p_na}, {p_na1}; {c_nao}")

# TC-SEN-018: KT, variante a x b
a_s = serie_rc("a", [10.0, 12.0, 14.0, 16.0])
b_ig = serie_rc("b", [10.0, 12.0, 14.0, 16.0])
b_dif = serie_rc("b", [10.0, 15.0, 14.0, 16.0])                       # 10 psi: |Δa_y| = 3 > banda interna (0,01)
b_ver = serie_rc("b", [10.0, 12.0, 14.0, 16.0], vereditos=["PUSH", "PUSH", "LOOSE", "PUSH"])
b_none = serie_rc("b", [10.0, None, 14.0, 16.0])
k_ig, _ = sp.decidir_kt(a_s + b_ig)
k_ay, c_ay = sp.decidir_kt(a_s + b_dif)
k_ver, _ = sp.decidir_kt(a_s + b_ver)
k_none, _ = sp.decidir_kt(a_s + b_none)
k_sem_b, _ = sp.decidir_kt(a_s)
k_none_ver, _ = sp.decidir_kt(a_s + serie_rc("b", [10.0, None, 14.0, 16.0],
                                              vereditos=["PUSH", "PUSH", "LOOSE", "PUSH"]))
k_na_na, c_na_na = sp.decidir_kt(serie_rc("a", [10.0, 12.0, 14.0, 16.0], vereditos=["N/A"] * 4)
                                  + serie_rc("b", [10.0, 12.0, 14.0, 16.0], vereditos=["N/A"] * 4))
# I4: banda não medida (14 psi, extremo) com |Δa_y| acima dela = "não avaliado: banda só limite inferior", nunca "sim"
b_ext = serie_rc("b", [10.0, 12.0, 14.0, 19.0])
k_ext, c_ext = sp.decidir_kt(a_s + b_ext)
bd_ext = cmp.banda_carro([r for r in a_s])[14.0]
check("TC-SEN-018 decidir_kt: a = b -> não; |Δa_y| > banda -> sim; veredito difere -> sim; ay None -> não avaliado "
      "(e sim se outro nó dá sim); sem variante b -> não avaliado; N/A nas duas variantes -> critério 1 não avaliado",
      k_ig == "não" and k_ay == "sim" and k_ver == "sim" and k_none == "não avaliado" and k_sem_b == "não avaliado"
      and k_none_ver == "sim" and len(c_ay) >= 1 and k_na_na == "não avaliado"
      and c_na_na["veredito de a e b a 10,0 psi"].startswith("não avaliado")
      and not bd_ext.medida and k_ext == "não avaliado"
      and c_ext["a_y_lim de a e b a 14,0 psi"].startswith("não avaliado: banda só limite inferior"),
      f"{k_ext}, {c_ext}, {k_ig}, {k_ay}, {k_ver}, {k_none}, {k_sem_b}, {k_none_ver}")

# TC-SEN-019: Resultado serializável, 18 decisões, rótulos
tab = sp.tabela_decisoes(("não", {"λ": "não"}), ("sim", {"pressão": "sim: PUSH × LOOSE"}),
                         ("não avaliado", {"KT": "não avaliado"}))
lc = sp.LinhaCarro("12 psi, variante a", 12.0, "a", {"LMUY": 0.8}, 12.3, 1.25, "PUSH", "esquerda", 5.0e4, 4.0e4, 3.1,
                   0.01, False, ("PUSH", "mesmo sinal"), ("r",))
la = sp.LinhaArrasto(1.0, 0.1, 0.01, 0.02, 3.0, {"FL": 1.0, "FR": 2.0}, 3.1, 0.001, None, ())
lp = sp.LinhaPneu(8.0, "F", False, 900.0, 5.0e4, 1.5, False, ("r",))
vu = cp.valores_usados(D)[0]
res_s = sp.Resultado(valores=(vu,), tornado=(lc,), pressao=(lc,), combinacao=None, pneu=(lp,), arrasto=(la,),
                     decisoes=tab, rotulos=sp.ROTULOS, tempos_s={"tornado": 0.5})
try:
    texto = json.dumps(res_s.para_dict(), allow_nan=False)
    volta = json.loads(texto)
except (TypeError, ValueError) as exc:
    texto, volta = "", {}
    print("json:", exc)
res_comb = sp.Resultado(valores=(), tornado=(), pressao=(), combinacao=(lc,), pneu=(), arrasto=(), decisoes=tab,
                        rotulos=sp.ROTULOS, tempos_s={})
dec19 = {d.degrau: d for d in tab}
medidos = {1, 2, 3, 6, 7, 8, 12, 15}
check("TC-SEN-019 Resultado.para_dict em JSON, 18 decisões, fora de {1,2,3,6,7,8,12,15} = 'não medido aqui', "
      "rótulos não vazios, DEGRAUS 1 a 18, resumo uma frase por decisão",
      len(volta.get("decisoes", [])) == 18 and sorted(dec19) == list(range(1, 19))
      and set(sp.DEGRAUS) == set(range(1, 19))
      and all(dec19[g].muda == "não medido aqui" for g in dec19 if g not in medidos)
      and dec19[6].muda == "não" and dec19[8].muda == "não" and dec19[1].muda == "sim" and dec19[3].muda == "sim"
      and dec19[12].muda == "não avaliado" and dec19[7].muda == "não avaliado" and dec19[15].muda == "não avaliado"
      and dec19[16].muda == "não medido aqui" and dec19[16].frase == "este estudo"
      and all(d.rotulos and d.frase and d.nome == sp.DEGRAUS[d.degrau] for d in tab)
      and dec19[2].frase.endswith("não num ajuste PP*/QPZ)") and "ajuste PP*/QPZ" in dec19[2].frase
      and dec19[3].frase.endswith("pressão quente e temperatura não estão no modelo)")
      and not dec19[1].frase.endswith(")")
      and '"caso"' not in texto and volta["combinacao"] is None and len(res_s.resumo()) == 18
      and len(res_comb.para_dict()["combinacao"]) == 1 and volta["decisoes"][0]["fatores"] == ["Pressão"],
      f"{len(volta.get('decisoes', []))}")


TTC = cp.achar_ttc()
if TTC is None:
    print("\nNÃO EXECUTÁVEL: TC-SEN-006 a 008 e 010 a 012 precisam dos .tir do TTC Round 6 (defina DDS_TTC_DIR ou coloque-os em "
          f"{cp.SUBDIR_TTC.as_posix()}). Não conta como aprovado.")
    encerrar()
    raise SystemExit(3)

FAM = cp.familia_ttc()
TIR12 = FAM.at_pressure(12.0).source_path


def campos_diferentes(c1: eq.CasoEquilibrio, c2: eq.CasoEquilibrio) -> list[str]:
    """Nomes dos campos do CasoEquilibrio que diferem (igualdade exata; ds pelo dataclass inteiro)."""
    return [f.name for f in dataclasses.fields(c1) if getattr(c1, f.name) != getattr(c2, f.name)]


# TC-SEN-006: o caso de caso_de_dados é o de _caso_de_valores sobre o x com os res_ escritos à mão; formas; Direita
x_mao = {c.chave_x: D["campos"][k]["valor"] for k, c in cp.CAMPOS.items() if c.chave_x is not None}
x_mao.update(m=182.0 + 68.0, a=1.55 * (1 - 0.46), b=1.55 * 0.46, huF=18.1 * 0.0254 / 2 * 1.0,
             huR=18.1 * 0.0254 / 2 * 1.0, motivo_r="")
x_mao["coef_nomes"] = {n: 1.0 for n in cp.LAMBDAS}
x_mao["coef"] = [1.0] * len(cp.LAMBDAS)
montado = cp.caso_de_dados(D, FAM)
passo1 = True       # epsF e epsR presentes (0) nos dados sintéticos: o mesmo passo1 que caso_de_dados escolhe
oraculo = cpl._caso_de_valores(x_mao, TIR12, passo1, ae.VERIFICACOES_V43, cp.FONTE_CASO)
dif = campos_diferentes(montado.caso, oraculo)
dir_ = cp.caso_de_dados(cp.editar(D, sentido="Direita"), FAM)
dif_dir = campos_diferentes(dir_.caso, eq.espelhar(montado.caso))
check("TC-SEN-006 caso_de_dados = _caso_de_valores(x à mão); formas v43/v43; Direita = espelhar(Esquerda)",
      not dif and montado.caso.cfg == oraculo.cfg and montado.caso.toe_rad == oraculo.toe_rad
      and montado.caso.camber_estatico_rad == oraculo.camber_estatico_rad
      and montado.caso.ganho_camber == oraculo.ganho_camber and montado.caso.raio_m == oraculo.raio_m
      and montado.caso.ds.p == oraculo.ds.p and montado.formas == eq.Formas("v43", "v43")
      and montado.fator_neutro == 4 / 3 and montado.kt_n_m == {"F": 120000.0, "R": 120000.0}
      and montado.valores == cp.valores_usados(D) and not dif_dir and dir_.formas == montado.formas
      and cp.ROTULO_SEM_ROLL_STEER not in montado.rotulos,
      f"diferentes={dif}, direita={dif_dir}, formas={montado.formas}")

# TC-SEN-007: ds.p = perfil de 12 psi com os lambda_* do JSON por cima; nada fora dos λ difere do perfil
L = cp.editar(D, lambda_LMUY=1.2, lambda_LKY=0.8)
caso_l = cp.caso_de_dados(L, FAM).caso
perfil12 = FAM.at_pressure(12.0)
esperado = {**dict(perfil12.parameters), **{n: L["campos"][f"lambda_{n}"]["valor"] for n in cp.LAMBDAS}}
fora = cmp.diferencas_fora_de_lambda(caso_l.ds, perfil12)
check("TC-SEN-007 ds.p = perfil de 12 psi com os lambda_* do JSON; diferencas_fora_de_lambda vazio",
      caso_l.ds.p == esperado and caso_l.ds.p["LMUY"] == 1.2 and caso_l.ds.p["LKY"] == 0.8 and fora == {}
      and cmp.diferencas_fora_de_lambda(montado.caso.ds, perfil12) == {}, f"fora={fora}")


def levanta_sem(fn, trecho) -> tuple[bool, str]:
    try:
        fn()
    except ValueError as exc:
        return trecho in str(exc), str(exc)
    return False, "não levantou"


# TC-SEN-008: entrada inválida para a planilha levanta ValueError com o texto da verificação
r_f = levanta_sem(lambda: cp.caso_de_dados(cp.editar(D, f_dianteira=1.5), FAM), "SUS-006")
r_h3 = levanta_sem(lambda: cp.caso_de_dados(cp.editar(D, h9=1), FAM), ae.MSG_H3)
r_crr = levanta_sem(lambda: cp.caso_de_dados(cp.editar(D, h9=1, h3=1, rho_kg_m3=1.2, cda_m2=1.0), FAM),
                    "Crr a confirmar")
D_sem_eps = copy.deepcopy(D)          # editar não aceita null: o campo nulo é escrito direto, como num JSON
D_sem_eps["campos"]["epsF_rad_rad"].update(valor=None, origem=cp.ORIGEM_A_CONFIRMAR)
sem_eps = cp.caso_de_dados(D_sem_eps, FAM)
check("TC-SEN-008 f_dianteira 1,5, h9 sem h3 e h9 com Crr nulo levantam ValueError; eps nulo = passo1 False + rótulo",
      r_f[0] and r_h3[0] and r_crr[0] and cp.ROTULO_SEM_ROLL_STEER in sem_eps.rotulos
      and sem_eps.caso.roll_steer == {"F": 0.0, "R": 0.0}, f"{r_f[1]} | {r_h3[1]} | {r_crr[1]}")

# ---------------------------------------------------------------------------------------------------------------------
# TC-SEN-010 a 012: forças por roda e arrasto induzido (caso SINTÉTICO de teste, não é dado do carro)
# ---------------------------------------------------------------------------------------------------------------------
CASO = montado.caso
FORMAS = montado.formas
COS_F = 1.0 if CASO.raio_m is None else math.cos(CASO.cfg.wheelbase / CASO.raio_m)   # o de eq._cos_dianteira

# TC-SEN-010: Σ F_y,i por eixo (× cos δ_ref na frente com raio) = fy_eixo_limitado no α de angulos_necessarios
# e = força exigida
erros = []
for ay_g in (0.5, 1.0):
    ay = ay_g * G
    alfas = el.angulos_necessarios(CASO, ay, formas=FORMAS)
    por_roda = sp.forcas_por_roda(CASO, ay, alfas, formas=FORMAS)
    fz, gam = eq.cargas(CASO, ay), eq.camber(CASO, ay)
    for eixo, a_ref, req in zip(("F", "R"), alfas, eq.forca_exigida(CASO, ay)):
        rodas = eq.RODAS_DO_EIXO[eixo]
        fz_u, gam_u, _ = eq.entrada_limitada(CASO, rodas, fz, gam)
        soma = sum(por_roda[c][1] for c in rodas) * (COS_F if eixo == "F" else 1.0)
        ref = eq.fy_eixo_limitado(CASO, rodas, fz_u, gam_u, a_ref, formas=FORMAS)
        erros.append((ay_g, eixo, abs(soma - ref) / ref, abs(soma - req) / req))
check("TC-SEN-010 Σ F_y,i do eixo = fy_eixo_limitado (1e-9) e = força exigida (1e-6), a_y 0,5 g e 1,0 g",
      all(e1 < 1e-9 and e2 < 1e-6 for _, _, e1, e2 in erros), f"cos_f={COS_F}, erros={erros}")

# TC-SEN-011: sinal, toe e camber (D_i >= −1e-9 N no simétrico; com toe, a tolerância é a de −0,05 N abaixo)
# caso de sinal: γ = 0 (sem camber estático nem ganho de camber), como no plano; com camber, uma roda pouco carregada
# pode ter F_y e α de mesmo sinal (empuxo de camber), e D_i < 0 ali é físico (D3), não erro
D_G0 = cp.editar(D, gsFL_grau=0.0, gsFR_grau=0.0, gsRL_grau=0.0, gsRR_grau=0.0, dgF_grau_mm=0.0, dgR_grau_mm=0.0)
caso_g0 = cp.caso_de_dados(D_G0, FAM)
lin0 = sp.arrasto_induzido(caso_g0.caso, formas=caso_g0.formas, ay_ate_ms2=1.0 * G)
sim_zero = abs(lin0[0].d_n) < 1e-9 and lin0[0].ay_ms2 == 0.0
sim_pos = all(v >= -1e-9 for l in lin0 for v in l.d_por_roda.values())
caso_toe = cp.caso_de_dados(cp.editar(D_G0, toeFL_grau=-0.2, toeFR_grau=-0.2), FAM)
lin_toe = sp.arrasto_induzido(caso_toe.caso, formas=caso_toe.formas, ay_ate_ms2=1.0 * G)
# com toe, a roda interna chega a α ≈ 0 em ~0,3 g, e o Fy residual do pneu em α = 0 (SHY, PHY3...) dá D_i de alguns
# mN negativos: físico, não erro; o total D fica >= 0 e nenhuma roda passa de −0,05 N
toe_ok = (lin_toe[0].d_n > 0.0 and all(l.d_n >= 0.0 for l in lin_toe)
          and all(v >= -0.05 for l in lin_toe for v in l.d_por_roda.values()))
# D_i = −F_y,i·sen α_i, conferido contra forcas_por_roda em a_y = 0,5 g (não só a conta à mão)
l5 = sp.arrasto_induzido(caso_g0.caso, formas=caso_g0.formas, ay_ate_ms2=0.5 * G)[-1]
pr5 = sp.forcas_por_roda(caso_g0.caso, l5.ay_ms2, (l5.alfa_f_rad, l5.alfa_r_rad), formas=caso_g0.formas)
d_roda_ok = all(abs(l5.d_por_roda[c] + fy * math.sin(a)) < 1e-12 and a < 0.0 and fy > 0.0
                for c, (a, fy) in pr5.items())
check("TC-SEN-011 D(0) = 0 no simétrico, D_i >= 0; com toe-in D(0) > 0; −F_y·sen α à mão",
      sim_zero and sim_pos and toe_ok and d_roda_ok,
      f"d0={lin0[0].d_n}, d0_toe={lin_toe[0].d_n}")

# TC-SEN-012: 1ª ordem (consistência da linearização) e grade (D4)
razoes = {}
for g in (0.2, 0.1, 0.05):
    l = sp.arrasto_induzido(CASO, formas=FORMAS, ay_ate_ms2=g * G, passo_g=g)[-1]
    razoes[g] = abs(l.d_n / l.d_1a_ordem_n - 1.0)
sem_lim = sp.arrasto_induzido(CASO, formas=FORMAS, ay_ate_ms2=None)
ult = sem_lim[-1]
prox = (round(ult.ay_g / 0.1) + 1) * 0.1
seguinte_ok = prox > 2.0 + 1e-9 or el.angulos_necessarios(CASO, prox * G, formas=FORMAS) is None
com_lim = sp.arrasto_induzido(CASO, formas=FORMAS, ay_ate_ms2=0.73 * G)
check("TC-SEN-012 |D/D1a−1| decresce e fecha < 1e-3; grade sem limite para onde não resolve; com limite, ay <= limite",
      razoes[0.2] > razoes[0.1] > razoes[0.05] and razoes[0.05] < 1e-3 and ult.ay_g <= 2.0 + 1e-9 and seguinte_ok
      and sem_lim[0].rotulos and com_lim[-1].ay_ms2 <= 0.73 * G and abs(com_lim[-1].ay_g - 0.7) < 1e-9,
      f"razoes={razoes}, ultima={ult.ay_g}, rotulo={sem_lim[0].rotulos}")

# TC-SEN-012b: a grade para onde angulos_necessarios deixa de resolver, com rótulo (D4); limite acima de ay_max_g também
# SINTÉTICO de teste: aderência reduzida (LMUY 0,3) só para saturar; não é dado do carro
CASO_SAT = dataclasses.replace(CASO, ds=eq.com_fatores(CASO.ds, {"LMUY": 0.3}))
sat = sp.arrasto_induzido(CASO_SAT, formas=FORMAS, ay_ate_ms2=None)
u_sat = sat[-1]
prox_sat = (round(u_sat.ay_g / 0.1) + 1) * 0.1
sat_lim = sp.arrasto_induzido(CASO_SAT, formas=FORMAS, ay_ate_ms2=2.0 * G)
cortado = sp.arrasto_induzido(CASO, formas=FORMAS, ay_ate_ms2=3.0 * G, ay_max_g=1.0)
check("TC-SEN-012b grade que satura: para antes de 2 g, o próximo ponto não resolve e há rótulo; limite acima de ay_max_g avisa",
      u_sat.ay_g < 1.9 and el.angulos_necessarios(CASO_SAT, u_sat.ay_g * G, formas=FORMAS) is not None
      and el.angulos_necessarios(CASO_SAT, prox_sat * G, formas=FORMAS) is None
      and all("deixam de resolver" in r and f"{u_sat.ay_g:.2f} g".replace(".", ",") in r for l in sat for r in l.rotulos)
      and all("sem saturação" not in r for l in sat for r in l.rotulos)
      and sat_lim[-1].ay_g == u_sat.ay_g and all(l.rotulos and "deixam de resolver" in l.rotulos[0] for l in sat_lim)
      and cortado[-1].ay_g <= 1.0 + 1e-9 and all("passa de ay_max_g" in l.rotulos[-1] for l in cortado),
      f"ultima={u_sat.ay_g}, rotulo={sat[0].rotulos}, cortado={cortado[0].rotulos}")

# ---------------------------------------------------------------------------------------------------------------------
# Corridas do estudo (Task 5): tornado, rigidez de eixo, pneu por pressão. A combinação é cara e não entra aqui.
# ---------------------------------------------------------------------------------------------------------------------
import tire_pressure as tp

# TC-SEN-013: a base do tornado é o caso de 12 psi com λ = 1; 1 + 2·3 linhas, sem fator 1,0 fora da base
torn = sp.tornado(montado, FAM)
ds12, _ = cmp.perfil_ajustado(montado.caso.ds, FAM.at_pressure(12.0), tp.teto_comum_fz(FAM))
par12 = eq.analise_par_dois_sentidos(dataclasses.replace(montado.caso, ds=ds12), **sp.GRADE, formas=montado.formas,
                                     fator_neutro=montado.fator_neutro)
res12 = par12[par12["pior"] if par12["pior"] != "empate" else "esquerda"]
fora_da_base = [l for l in torn[1:] if len(l.fatores) != 1 or any(v == 1.0 for v in l.fatores.values())]
ok13a = (
      len(torn) == 7 and torn[0].ay_lim_ms2 == res12.ay_lim and torn[0].veredito == res12.veredito
      and torn[0].fatores == {} and not fora_da_base
      and {(next(iter(l.fatores)), next(iter(l.fatores.values()))) for l in torn[1:]}
      == {(n, v) for n in sp.FATORES_EXPLORATORIOS for v in (0.8, 1.2)}
      and all(l.pressao_psi == 12.0 and l.variante_kt == "a" for l in torn)
      and all(r in l.rotulos for l in torn for r in sp.ROTULOS)
      )

# TC-SEN-013 (cont.): caso que satura (CASO_SAT, SINTÉTICO de teste): ay_lim numérico, igual ao direto; λ muda algo;
# a base é a linha de 12 psi, variante a, de sp.pressao; os rótulos de comparar_carro aparecem.
montado_sat = dataclasses.replace(montado, caso=CASO_SAT)
torn_s = sp.tornado(montado_sat, FAM)
ds12_s, _ = cmp.perfil_ajustado(CASO_SAT.ds, FAM.at_pressure(12.0), tp.teto_comum_fz(FAM))
par_s = eq.analise_par_dois_sentidos(dataclasses.replace(CASO_SAT, ds=ds12_s), ay_max_g=2.0, passo_g=0.05, n_alfa=25,
                                     formas=montado.formas, fator_neutro=montado.fator_neutro)
res_s = par_s[par_s["pior"] if par_s["pior"] != "empate" else "esquerda"]
b_s = torn_s[0]
ay_ok = (b_s.ay_lim_ms2 is not None and res_s.ay_lim is not None
         and abs(b_s.ay_lim_ms2 - res_s.ay_lim) <= 1e-9 * abs(res_s.ay_lim))
difere = any(l.ay_lim_ms2 != b_s.ay_lim_ms2 or l.k_grau_g != b_s.k_grau_g for l in torn_s[1:])
pr_s = sp.pressao(montado_sat, FAM)
l12a = next(r for r in pr_s if r.variante_kt == "a" and abs(r.pressao_psi - 12.0) < 1e-3)
rot_extra = ("KT do caso, fixo (variante a: só muda a aderência)", "K com roll steer 0 = sem dado",
             "K com o roll steer do caso")
check("TC-SEN-013 tornado: base = analise_par direto (sintético e com saturação), 7 linhas, λ muda algo, base = pressao(12 psi, a), rótulos de comparar_carro",
      ok13a and ay_ok and b_s.veredito == res_s.veredito and difere
      and b_s.ay_lim_ms2 == l12a.ay_lim_ms2 and b_s.veredito == l12a.veredito
      and all(any(r in l.rotulos for r in rot_extra[1:]) and rot_extra[0] in l.rotulos for l in torn_s + torn),
      f"base={b_s.ay_lim_ms2}, direto={res_s.ay_lim}, pressao={l12a.ay_lim_ms2}")

# TC-SEN-014: C_f, C_r > 0; K da linha = para_graus_por_g; gradiente_pneus reproduz k_pneus
cf, cr, mot = sp.rigidez_eixos(montado.caso, formas=montado.formas)
r_a = cmp.comparar_carro(montado.caso, FAM, kt_caso_n_m=montado.kt_n_m, formas=montado.formas,
                         fator_neutro=montado.fator_neutro, ay_max_g=0.2, passo_g=0.1, n_alfa=9)[0]
lin_a = sp.linha_de_resultado(r_a, formas=montado.formas)
pk0 = el.parcelas_k(montado.caso, 0.0, formas=montado.formas)
w_f, w_r = el._pesos_eixo(montado.caso)
k_cons = el.gradiente_pneus(w_f, w_r, cf, cr)
check("TC-SEN-014 rigidez_eixos > 0; K da linha = para_graus_por_g; gradiente_pneus(W, C) = k_pneus",
      cf > 0 and cr > 0 and mot is None and lin_a.k_grau_g == el.para_graus_por_g(r_a.k_rad_ms2)
      and abs(k_cons - pk0.k_pneus) <= 1e-12 * abs(pk0.k_pneus) and lin_a.c_f_n_rad > 0 and lin_a.c_r_n_rad > 0,
      f"cf={cf}, cr={cr}, dK={k_cons - pk0.k_pneus}")

# TC-SEN-015: pneu por pressão, 13 pressões x 2 eixos; interpolado só fora dos nós; Cα(12) = perfil direto
pneu = sp.pneu_por_pressao(montado, FAM)
nos = {l.pressao_psi for l in pneu if not l.interpolado}
l12f = next(l for l in pneu if l.pressao_psi == 12.0 and l.eixo == "F")
fz0 = eq.cargas(montado.caso, 0.0)
fz_f = min(0.5 * (fz0["FL"] + fz0["FR"]), tp.teto_comum_fz(FAM))
cam_f = 0.5 * (montado.caso.camber_estatico_rad["FL"] + montado.caso.camber_estatico_rad["FR"])
m12 = tp.metricas_pneu(tp.avaliador_perfil(FAM.at_pressure(12.0)), tp.faixa_comum(FAM.profiles.values()),
                       fz_n=fz_f, camber_rad=cam_f)
check("TC-SEN-015 pneu_por_pressao: 13 x 2; interpolado False só em 8, 10, 12, 14; Cα(12) = perfil direto",
      len(pneu) == 26 and {l.pressao_psi for l in pneu} == {8 + 0.5 * i for i in range(13)}
      and nos == {8.0, 10.0, 12.0, 14.0} and {l.eixo for l in pneu} == {"F", "R"}
      and abs(l12f.c_alpha_n_rad - m12.c_alpha_n_rad) <= 1e-9 * abs(m12.c_alpha_n_rad)
      and l12f.mu_y_pico == m12.mu_y_pos.mu,
      f"Ca={l12f.c_alpha_n_rad} vs {m12.c_alpha_n_rad}")

# TC-SEN-020: linha de comando (tools/relatorio_pneu1.py): --rapido com --set; arquivos, origem editada, rótulos;
# entrada inválida -> código 2, mensagem em português e sem traceback (usa o caso demonstrativo e os .tir: ~20 s)
import contextlib
import io
import sys as _sys

_sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import relatorio_pneu1 as rel  # noqa: E402

with tempfile.TemporaryDirectory() as tmp20:
    cod20 = rel.main(["--rapido", "--set", "h_cg_m=0.31", "--saida", tmp20])
    arq_md, arq_js = Path(tmp20) / "relatorio.md", Path(tmp20) / "resultados.json"
    existem = arq_md.is_file() and arq_js.is_file()
    js20 = json.loads(arq_js.read_text(encoding="utf-8")) if existem else {}
    md20 = arq_md.read_text(encoding="utf-8") if existem else ""
    vh = next((v for v in js20.get("valores", []) if v["chave"] == "h_cg_m"), {})
    err20 = io.StringIO()
    with contextlib.redirect_stderr(err20):
        cod_massa = rel.main(["--set", "massa=1", "--saida", tmp20])
msg20 = err20.getvalue()
# código 3: sem o .tir (achar_ttc trocado por um substituto que simula a ausência; o original volta no finally);
# --set sem "=" e --caso inexistente: código 2
achar_orig = cp.achar_ttc
cp.achar_ttc = lambda: None
err3 = io.StringIO()
try:
    with contextlib.redirect_stderr(err3):
        cod3 = rel.main(["--rapido", "--saida", tempfile.gettempdir() + "/pneu1-teste-cod3"])
finally:
    cp.achar_ttc = achar_orig
err_eq, err_arq = io.StringIO(), io.StringIO()
with contextlib.redirect_stderr(err_eq):
    cod_sem_igual = rel.main(["--set", "h_cg_m", "--saida", tempfile.gettempdir() + "/pneu1-teste-cod2"])
with contextlib.redirect_stderr(err_arq):
    cod_sem_arq = rel.main(["--caso", str(Path(tempfile.gettempdir()) / "nao-existe-pneu1.json"),
                            "--saida", tempfile.gettempdir() + "/pneu1-teste-cod2"])
check("TC-SEN-020 relatorio_pneu1: código 0, dois arquivos, h_cg_m editado com a origem ✎, ROTULOS no relatório; "
      "--set massa=1 dá código 2 com mensagem em português e sem traceback; sem .tir dá código 3; --set sem = e --caso "
      "inexistente dão código 2",
      cod20 == 0 and existem and vh.get("editado") is True and vh.get("origem") == cp.ORIGEM_EDITADO
      and all(t in md20 for t in sp.ROTULOS)
      and cod_massa == 2 and "chave desconhecida: massa" in msg20 and "Traceback" not in msg20
      and "7.99999" not in md20 and "`R_m`" in md20 and "Valores marcados como" in md20
      and cod3 == 3 and "NÃO EXECUTÁVEL" in err3.getvalue() and cp.achar_ttc is achar_orig
      and cod_sem_igual == 2 and "chave=valor" in err_eq.getvalue()
      and cod_sem_arq == 2 and "arquivo do caso" in err_arq.getvalue(),
      f"cod={cod20}, massa={cod_massa}, cod3={cod3}, sem_igual={cod_sem_igual}, sem_arq={cod_sem_arq}, h_cg={vh}, "
      f"msg={msg20.strip()!r}")

# TC-SEN-021: estudo num caso que satura (SINTÉTICO de teste: LMUY 0,3 e Crr 0,02, nenhum é dado do carro): o arrasto para
# no a_y_lim de 12 psi (C1), usa o Crr do caso (I3), rótulos com vírgula (M1) e o rótulo do .tir cru do arrasto
import re

val_crr = tuple(dataclasses.replace(v, valor=0.02, origem=cp.ORIGEM_EDITADO, editado=True)
                if v.chave == "crr_referencia" else v for v in montado_sat.valores)
res21 = sp.estudo(dataclasses.replace(montado_sat, valores=val_crr), FAM, rapido=True)
l12_21 = next(l for l in res21.pressao if l.variante_kt == "a" and abs(l.pressao_psi - 12.0) < 1e-3)
arr21 = res21.arrasto
md21 = rel.montar_relatorio(res21, True, cp.CAMINHO_DEMONSTRATIVO)
arr_sem = sp.arrasto_induzido(CASO, formas=FORMAS, ay_ate_ms2=None)
check("TC-SEN-021 estudo saturante: arrasto até o a_y_lim de 12 psi sem rótulo de 'sem saturação'; Crr do caso nas "
      "linhas e no relatório; rótulos com vírgula; rótulo do .tir cru; sem Crr, a confirmar",
      l12_21.ay_lim_ms2 is not None and arr21[-1].ay_ms2 <= l12_21.ay_lim_ms2 * (1 + 1e-9)
      and arr21[-1].ay_ms2 >= l12_21.ay_lim_ms2 - 0.1 * G - 1e-9
      and all("sem saturação" not in t for l in arr21 for t in l.rotulos)
      and all(sp.ROTULO_ARRASTO in l.rotulos for l in arr21)
      and all(l.d_sobre_rolamento is not None and abs(l.d_sobre_rolamento - l.d_n / (0.02 * CASO.cfg.mass_total * G)) <= 1e-9 * abs(l.d_sobre_rolamento) + 1e-12
              for l in arr21[1:])
      and "Crr informado pelo usuário" in md21 and "D/(Crr·m·g)" in md21
      and any("2,00 g" in t for t in arr_sem[0].rotulos)
      and not any(re.search(r"\d\.\d\d g", t) for l in arr_sem + arr21 for t in l.rotulos)
      and "a confirmar" in md20 and "D/(Crr·m·g)" not in md20 and sp.ROTULO_ARRASTO in md21,
      f"ultima={arr21[-1].ay_ms2}, ay_lim={l12_21.ay_lim_ms2}")

# TC-SEN-022: frase com o motivo medido do N/A (I1) e rótulo do fator_neutro por caso (M2)
class _Res:
    def __init__(self, motivo): self.motivo = motivo


def rc_na(p, motivo):
    return dataclasses.replace(rc(p, "a", None, veredito="N/A"), par={"pior": "esquerda", "esquerda": _Res(motivo)})


M_BORDA, M_SAT = "pico na borda da grade de α em a_y = 0 g", "não satura até 2 g"
fr_igual = sp._frase_pressao("não avaliado", {}, [rc_na(p, M_BORDA) for p in NOS])
fr_mista = sp._frase_pressao("não avaliado", {}, [rc_na(p, M_SAT if p < 14 else M_BORDA) for p in NOS])
linhas_pr = js20.get("pressao", [])
l14_js = next((l for l in linhas_pr if abs(l["pressao_psi"] - 14.0) < 1e-3), {})
l8_js = next((l for l in linhas_pr if abs(l["pressao_psi"] - 8.0) < 1e-3), {})
neutro_x = sp.rotulo_fator_neutro(dataclasses.replace(montado, fator_neutro=1.5))
check("TC-SEN-022 frase usa o motivo medido (igual em todas: uma vez; diferente: por pressão em psi), sem 'não chega ao "
      "limite'; motivo_na na linha; rótulo do fator_neutro só quando difere de 1,0, com o valor real",
      M_BORDA in fr_igual and fr_igual.count(M_BORDA) == 1 and "em todas as pressões" in fr_igual
      and "não chega ao limite" not in fr_igual
      and f"{M_SAT} a 8,0, 10,0 e 12,0 psi" in fr_mista and f"{M_BORDA} a 14,0 psi" in fr_mista
      and "não chega ao limite" not in md20 and "não chega ao limite" not in md21
      and l14_js.get("motivo_na") == M_BORDA and l8_js.get("motivo_na") == M_SAT and M_SAT in md20 and M_BORDA in md20
      and sp.rotulo_fator_neutro(dataclasses.replace(montado, fator_neutro=1.0)) == ()
      and len(neutro_x) == 1 and "1,5" in neutro_x[0]
      and all(t in md20 for t in sp.rotulo_fator_neutro(montado)) and "4/3" not in md20,
      f"{fr_igual!r}; {fr_mista!r}; {l14_js.get('motivo_na')!r}")

encerrar()
