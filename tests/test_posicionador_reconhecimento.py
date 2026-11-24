"""
Testes do reconhecimento de componentes do CAD pelo nome (posicionador, fase 2).
Sem ID de TC: o prefixo e o número de TC-POS novos aguardam autorização do usuário (CLAUDE.md).
1: os componentes de primeiro nível do T11 real (JSON da sondagem de 2026-11-24) são todos reconhecidos, nenhum só por inferência.
2: variações de nome (caixa, acento, espaço, hífen) são `normalizada`.
3: nomes fora do padrão viram `inferida` (não usável) ou `nao_reconhecido` (com o aviso do FIXO); nada é inventado.
4: o mapa do usuário vale mais que as regras, e categoria inexistente no mapa é recusada.
5: PREFIXOS iguais aos de cad_step e cópia do módulo na pasta do script de sondagem idêntica.
Roda como script: uv run python -X utf8 tests/test_posicionador_reconhecimento.py
"""
import hashlib
import json
import os


from posicionador import cad_step, reconhecimento as rc

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SONDAGEM = os.path.join(RAIZ, "docs", "posicionador", "fusion", "fusion_sondagem_2026-11-24.json")
COPIA = os.path.join(RAIZ, "docs", "posicionador", "fusion", "T11_sondagem", "reconhecimento.py")
results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def sha(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --- 1: nomes reais do T11 ------------------------------------------------------------------------------------------
try:
    with open(SONDAGEM, encoding="utf-8") as f:
        dados = json.load(f)
    primeiros = sorted({c["onde"].split("+")[0] for c in dados["corpos"]["lista"] if c["onde"] != "raiz"})
    lista = rc.reconhecer_todos(primeiros)
    esperado = {"CHASSI_T11_V20:1": "CHASSI", "HP_FRENTE:1": "HP", "REF_REFERENCIAS:1": "REF",
                "BANDEJA_FE_INFERIOR_V20_1:1": "BANDEJA_FE", "BANDEJA_FD_INFERIOR_V20_1:1": "BANDEJA_FD",
                "DIR_FE_TIRANTE_V20_1:1": "DIR", "DIR_FD_TIRANTE_V20_1:1": "DIR",
                "RODA_FE_CONJUNTO:1": "RODA_FE", "RODA_FD_CONJUNTO:1": "RODA_FD",
                "IGNORAR_TRASEIRA:1": "IGNORAR", "IGNORAR_PUSHROD_FE_V20_1:1": "IGNORAR"}
    por_nome = {nome: r for nome, r in zip(primeiros, lista)}
    faltam = [n for n in esperado if n not in por_nome]
    erradas = [n for n, c in esperado.items() if n in por_nome and por_nome[n].categoria != c]
    so_exata = all(r.nivel == "exata" for r in lista)
    check("Reconhecimento 1: T11 real: categorias esperadas e todas por prefixo exato",
          len(primeiros) >= 10 and not faltam and not erradas and so_exata,
          f"{len(primeiros)} componentes; faltam={faltam}; erradas={erradas}; níveis={rc.resumo(lista)['por_nivel']}")
except Exception as e:  # pylint:disable=broad-except
    check("Reconhecimento 1: T11 real: categorias esperadas e todas por prefixo exato", False, f"{type(e).__name__}: {e}")

# --- 2: normalização -------------------------------------------------------------------------------------------------
try:
    casos = {"bandeja_fe_inferior": "BANDEJA_FE", "Bandeja FD Superior": "BANDEJA_FD", "dir-fe-tirante": "DIR",
             "Chassi T11": "CHASSI", "ref referências": "REF", "IGNORAR-traseira:1": "IGNORAR",
             "roda_FE_conjunto:2": "RODA_FE"}
    res2 = {n: rc.reconhecer(n) for n in casos}
    ok = all(r.categoria == casos[n] and r.nivel == "normalizada" and r.usavel for n, r in res2.items())
    check("Reconhecimento 2: caixa, acento, espaço e hífen são `normalizada` e usáveis", ok,
          str({n: (r.categoria, r.nivel) for n, r in res2.items() if r.nivel != "normalizada" or r.categoria != casos[n]}))
except Exception as e:  # pylint:disable=broad-except
    check("Reconhecimento 2: caixa, acento, espaço e hífen são `normalizada` e usáveis", False, f"{type(e).__name__}: {e}")

# --- 3: inferida e não reconhecido -----------------------------------------------------------------------------------
try:
    inf = {"Wishbone esquerdo inferior": "BANDEJA_FE", "Tirante de direção FD": "DIR", "Pneu FD": "RODA_FD",
           "Tubos do chassi": "CHASSI", "Pushrod": "IGNORAR", "Roda traseira TE": "IGNORAR"}
    r_inf = {n: rc.reconhecer(n) for n in inf}
    ok_inf = all(r.categoria == inf[n] and r.nivel == "inferida" and not r.usavel for n, r in r_inf.items())
    nao = ["Bandeja", "Roda 13x7", "Parafuso M8", "Peça 123", "Bandeja esquerda e direita"]
    r_nao = {n: rc.reconhecer(n) for n in nao}
    ok_nao = all(r.categoria is None and r.nivel == "nao_reconhecido" and r.padrao_se_ignorado == "FIXO"
                 and not r.usavel for r in r_nao.values())
    check("Reconhecimento 3: fora do padrão: inferida não é usável; sem palavra-chave ou sem lado não inventa categoria",
          ok_inf and ok_nao,
          f"inf={[(n, r.categoria, r.nivel) for n, r in r_inf.items() if r.categoria != inf[n] or r.nivel != 'inferida']}; "
          f"nao={[(n, r.categoria, r.nivel) for n, r in r_nao.items() if r.nivel != 'nao_reconhecido']}")
except Exception as e:  # pylint:disable=broad-except
    check("Reconhecimento 3: fora do padrão: inferida não é usável; sem palavra-chave ou sem lado não inventa categoria",
          False, f"{type(e).__name__}: {e}")

# --- 4: mapa do usuário ----------------------------------------------------------------------------------------------
try:
    mapa = rc.validar_mapa({"Parafuso M8": "FIXO", "Pneu FD": "RODA_FD", "bandeja fe inferior": "IGNORAR"})
    a, b, c = rc.reconhecer("Parafuso M8:1", mapa), rc.reconhecer("Pneu FD", mapa), rc.reconhecer("BANDEJA_FE_INFERIOR", mapa)
    ok_mapa = (a.nivel == "mapa" and a.categoria == "FIXO" and a.usavel and b.nivel == "mapa" and b.usavel
               and c.nivel == "mapa" and c.categoria == "IGNORAR")  # o mapa vence até o prefixo exato
    try:
        rc.validar_mapa({"X": "INVENTADA"})
        recusa = False
    except ValueError:
        recusa = True
    modelo = rc.modelo_de_mapa(rc.reconhecer_todos(["Pneu FD", "Parafuso M8", "CHASSI_T11"]))
    ok_modelo = modelo.get("Pneu FD") == "RODA_FD" and modelo.get("Parafuso M8") == "" and "CHASSI_T11" not in modelo
    check("Reconhecimento 4: mapa do usuário vence as regras; categoria inexistente é recusada; modelo de mapa só pede o que falta",
          ok_mapa and recusa and ok_modelo, f"mapa={ok_mapa}; recusa={recusa}; modelo={ok_modelo}")
except Exception as e:  # pylint:disable=broad-except
    check("Reconhecimento 4: mapa do usuário vence as regras; categoria inexistente é recusada; modelo de mapa só pede o que falta",
          False, f"{type(e).__name__}: {e}")

# --- 5: consistência com cad_step e cópia do script -----------------------------------------------------------------
try:
    iguais = tuple(cad_step.PREFIXOS) == tuple(rc.PREFIXOS) and tuple(cad_step.CATEGORIAS) == tuple(rc.CATEGORIAS)
    copia_ok = os.path.exists(COPIA) and sha(COPIA) == sha(rc.__file__)
    check("Reconhecimento 5: PREFIXOS iguais aos de cad_step e cópia do módulo no script de sondagem idêntica",
          iguais and copia_ok, f"prefixos={iguais}; cópia={copia_ok}")
except Exception as e:  # pylint:disable=broad-except
    check("Reconhecimento 5: PREFIXOS iguais aos de cad_step e cópia do módulo no script de sondagem idêntica",
          False, f"{type(e).__name__}: {e}")

n_pass = sum(1 for _, s, _ in results if s == "PASS")
print(f"\n{n_pass} PASS, {len(results) - n_pass} FAIL, de {len(results)} testes")
raise SystemExit(0 if n_pass == len(results) else 1)
