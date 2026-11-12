"""Testes do pneu-1 (sensibilidade do pneu e arrasto induzido), EDR-075. Script com check(), não pytest.

Esta parte (Task 1) não precisa do .tir: catálogo, leitura, edição e gravação do caso, e o x da planilha.
Os dados do teste são SINTÉTICOS de teste, não são dado do carro (números do veiculo_base de tests/test_equilibrio.py).
"""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import aba_equilibrio as ae
import caso_pneu1 as cp

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

encerrar()
