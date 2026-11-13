"""Testes do pneu-1 (sensibilidade do pneu e arrasto induzido), EDR-075. Script com check(), não pytest.

TC-SEN-001 a 005 não precisam do .tir: catálogo, leitura, edição e gravação do caso, e o x da planilha.
TC-SEN-006 a 008 e 010 a 012 precisam dos .tir do TTC Round 6 (DDS_TTC_DIR ou references/ttc/..., a regra de
caso_pneu1.achar_ttc): sem eles, a seção imprime NÃO EXECUTÁVEL e o script sai com o código 3 depois das outras.
Os dados do teste são SINTÉTICOS de teste, não são dado do carro (números do veiculo_base de tests/test_equilibrio.py).
"""
from __future__ import annotations

import copy
import dataclasses
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
      and all("deixam de resolver" in r and f"{u_sat.ay_g:.2f} g" in r for l in sat for r in l.rotulos)
      and all("sem saturação" not in r for l in sat for r in l.rotulos)
      and sat_lim[-1].ay_g == u_sat.ay_g and all(l.rotulos and "deixam de resolver" in l.rotulos[0] for l in sat_lim)
      and cortado[-1].ay_g <= 1.0 + 1e-9 and all("passa de ay_max_g" in l.rotulos[-1] for l in cortado),
      f"ultima={u_sat.ay_g}, rotulo={sat[0].rotulos}, cortado={cortado[0].rotulos}")

encerrar()
