"""
Testes da verificação geométrica da identificação dos componentes (posicionador, fase 2).
IDs: TC-POS-110 a 122 (EDR-077).
1: dados reais do T11 (sondagem do Fusion de 2026-11-24): nenhuma FALHA, e os avisos esperados aparecem.
2 a 13: mutações. Cada uma injeta UM erro de identificação nos dados reais e exige o código de FALHA certo
   (ou só AVISO, no caso da assimetria dos HP). Um verificador que passa tudo seria reprovado aqui.
Roda como script: uv run python -X utf8 tests/test_posicionador_identificacao.py
"""
import copy
import json
import os

from posicionador import identificacao as idf

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SONDAGEM = os.path.join(RAIZ, "docs", "posicionador", "fusion", "fusion_sondagem3_2026-11-24.json")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


with open(SONDAGEM, encoding="utf-8") as f:
    GEO = json.load(f)["geometria_por_componente"]


def novo():
    return copy.deepcopy(GEO)


def corpos(geo, topo):
    return [c for o in geo["topos"][topo]["ocorrencias"] for c in o["corpos"]]


def inverte_y(c):
    """Espelha o corpo em Y (o referencial do carro tem Y do carro = Y do CAD neste modelo: REF_Y é +Y do CAD)."""
    lo, hi = c["min_mm"][1], c["max_mm"][1]
    c["min_mm"][1], c["max_mm"][1] = -hi, -lo
    if "esfera" in c:
        c["esfera"]["centro_mm"][1] *= -1


def roda(nome, geo, mapa=None):
    try:
        r = idf.verificar(geo, mapa)
        return r, None
    except Exception as e:  # pylint:disable=broad-except
        return None, f"{type(e).__name__}: {e}"


def exige(nome, geo, codigo_falha, mapa=None, so_aviso=False):
    r, erro = roda(nome, geo, mapa)
    if erro:
        check(nome, False, erro)
        return
    if so_aviso:
        ok = r.ok and codigo_falha in r.codigos("AVISO")
    else:
        ok = (not r.ok) and codigo_falha in r.codigos("FALHA")
    check(nome, ok, f"esperado {codigo_falha}{' (só aviso)' if so_aviso else ''}; falhas={r.codigos('FALHA')}; avisos={r.codigos('AVISO')}")


# --- 1: dados reais ----------------------------------------------------------------------------------------------
r, erro = roda("real", novo())
if erro:
    check("TC-POS-110 Identificação 1: T11 real sem falhas, com os avisos esperados", False, erro)
else:
    esperados = {"SEM-CORPO", "LADO-ANINHADO", "ANINHADO-CONFLITO", "IGNORAR-CORPO-SUSPEITO"}
    check("TC-POS-110 Identificação 1: T11 real sem falhas, com os avisos esperados",
          r.ok and esperados <= set(r.codigos("AVISO")),
          f"falhas={[(a.codigo, a.componente) for a in r.falhas]}; avisos={r.codigos('AVISO')}")

# --- 2 a 13: mutações --------------------------------------------------------------------------------------------
g = novo()
for c in corpos(g, "BANDEJA_FE_INFERIOR_V20_1:1"):
    inverte_y(c)
exige("TC-POS-111 Identificação 2: bandeja FE no lado direito → LADO", g, "LADO")

g = novo()
del g["topos"]["BANDEJA_FD_SUPERIOR_V20_1:1"]
exige("TC-POS-112 Identificação 3: bandeja a menos → CONTAGEM", g, "CONTAGEM")

g = novo()
g["topos"]["IGNORAR_CHASSI_T11_V20:1"] = g["topos"].pop("CHASSI_T11_V20:1")
exige("TC-POS-113 Identificação 4: chassi renomeado para IGNORAR_ → IGNORAR-CHASSI", g, "IGNORAR-CHASSI")

g = novo()
for c in corpos(g, "REF_REFERENCIAS:1"):
    if c["nome"] == "REF_X":
        c["esfera"]["centro_mm"][0] += 20.0
exige("TC-POS-114 Identificação 5: REF_X a 120 mm → REF", g, "REF")

g = novo()
for c in corpos(g, "HP_FRENTE:1"):
    if c["nome"] == "HP_FL_LCA_OUT":
        inverte_y(c)
exige("TC-POS-115 Identificação 6: HP_FL no lado direito → HP-LADO", g, "HP-LADO")

g = novo()
g["topos"]["Peça 7:1"] = g["topos"].pop("IGNORAR_GABARITO_T1_2:1")
exige("TC-POS-116 Identificação 7: componente sem nome reconhecível → IDENT-NOME", g, "IDENT-NOME")

g = novo()
for o in g["topos"]["DIR_FE_TIRANTE_V20_1:1"]["ocorrencias"]:
    o["corpos"] = []
exige("TC-POS-117 Identificação 8: componente usado sem corpos → SEM-CORPO", g, "SEM-CORPO")

g = novo()
for c in corpos(g, "HP_FRENTE:1"):
    if c["nome"] == "HP_FR_TIE_IN":
        c["esfera"]["centro_mm"][0] += 5.0
exige("TC-POS-118 Identificação 9: assimetria de 5 mm nos HP é só AVISO (HP-ESPELHO)", g, "HP-ESPELHO", so_aviso=True)

g = novo()
for c in corpos(g, "HP_FRENTE:1"):
    if c["nome"] == "HP_FL_TIE_IN":
        c["esfera"]["raio_mm"] = 3.0
exige("TC-POS-119 Identificação 10: esfera HP com raio 3 mm → ESFERA", g, "ESFERA")

g = novo()
for o in g["topos"]["RODA_FE_CONJUNTO:1"]["ocorrencias"]:
    if o["profundidade"] == 1:
        for c in o["corpos"]:
            inverte_y(c)
exige("TC-POS-120 Identificação 11: subcomponente de roda FE no lado errado → LADO-ANINHADO (falha, pai usado)", g, "LADO-ANINHADO")

g = novo()
g["topos"]["Peça 7:1"] = g["topos"].pop("IGNORAR_GABARITO_T1_2:1")
r2, erro2 = roda("mapa", g, mapa=idf.rc.validar_mapa({"Peça 7": "IGNORAR"}))
check("TC-POS-121 Identificação 12: decisão no mapa resolve o nome (sem IDENT-NOME) e nada mais quebra",
      erro2 is None and r2.ok and "IDENT-NOME" not in r2.codigos(),
      erro2 or f"falhas={r2.codigos('FALHA')}")

g = novo()
for o in g["topos"]["IGNORAR_PUSHROD_FE_V20_1:1"]["ocorrencias"]:
    o["nome"] = "CHASSI_TUBO_EXTRA:1"
exige("TC-POS-122 Identificação 13: ocorrência com nome de chassi dentro de IGNORAR (não traseira) → IGNORAR-CHASSI", g, "IGNORAR-CHASSI")

n_pass = sum(1 for _, s, _ in results if s == "PASS")
print(f"\n{n_pass} PASS, {len(results) - n_pass} FAIL, de {len(results)} testes")
raise SystemExit(0 if n_pass == len(results) else 1)
