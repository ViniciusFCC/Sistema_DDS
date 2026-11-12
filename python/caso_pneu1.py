"""Caso do pneu-1 (sensibilidade do pneu e arrasto induzido) em JSON editável: catálogo, leitura, edição e gravação.

O caso é o conjunto de entradas que a planilha V4.4 usa para o equilíbrio (abas 05, 06, 07, 08, 10, 16 e 24), guardado
num JSON com origem e fonte de cada valor. `x_de_dados` o transforma no dicionário `x` que
`caso_planilha._caso_de_valores` espera (D1 do plano), com os resultados `res_` recalculados pela regra da célula da
V4.4 (D2). Nada aqui lê o `.tir` nem a planilha: a captura (tools/capturar_caso_pneu1.py) é quem lê a planilha.

Valor sem fonte vale `None` (null no JSON) com a origem `? A confirmar`; nenhum número é inventado.
"""
from __future__ import annotations

import copy
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import aba_curva
import origens
import aba_equilibrio as ae
from equilibrio import FATORES_LAMBDA
from tire_model import AXIS_TRANSFORMS

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_DEMONSTRATIVO = RAIZ / "data" / "casos" / "caso_pneu1_demonstrativo.json"
SCHEMA = "caso_pneu1/1"
ORIGEM_EDITADO = "✎ Editado pelo usuário"
ORIGEM_A_CONFIRMAR = "? A confirmar"

SENTIDOS = ("Esquerda", "Direita")


@dataclass(frozen=True)
class Campo:
    """Um campo do caso. `chave_x`: a chave de `x` (None = só entra numa conta, ou só na §7.2); `nome_definido`: o nome
    definido da V4.4 de onde a captura lê (None = sem nome); `unidade`: a da planilha; `tipo`: num, chave (0 ou 1) ou
    texto."""
    chave_x: str | None
    nome_definido: str | None
    unidade: str
    rotulo: str
    descricao: str
    tipo: Literal["num", "chave", "texto"]


def _v40(k: str) -> str:
    return ae.V40[k]


def _montar() -> dict[str, Campo]:
    c: dict[str, Campo] = {}

    def add(chave, chave_x, nome, unidade, rotulo, descricao, tipo: Literal["num", "chave", "texto"] = "num"):
        c[chave] = Campo(chave_x, nome, unidade, rotulo, descricao, tipo)

    # 05_VEHICLE
    add("m_sem_piloto_kg", None, "ent_05_massa_medida_sem_piloto", "kg", "Massa do carro sem piloto",
        "Massa do carro pesado sem o piloto.")
    add("m_piloto_kg", None, "ent_05_massa_do_piloto", "kg", "Massa do piloto", "Massa do piloto com equipamento.")
    add("h_cg_m", "h", _v40("h"), "m", "Altura do centro de gravidade",
        "Altura do centro de gravidade do carro todo, medida a partir do chão.")
    add("L_m", "L", _v40("L"), "m", "Entre-eixos", "Distância entre o eixo dianteiro e o traseiro.")
    add("tF_m", "tF", _v40("tF"), "m", "Bitola dianteira", "Distância entre o centro das duas rodas da frente.")
    add("tR_m", "tR", _v40("tR"), "m", "Bitola traseira", "Distância entre o centro das duas rodas de trás.")
    add("f_dianteira", None, "ent_05_fracao_de_peso_no_eixo_dianteiro_f", "-", "Fração do peso na frente",
        "Parte do peso do carro que fica sobre o eixo dianteiro, de 0 a 1.")
    add("muF_kg", "muF", _v40("muF"), "kg", "Massa não suspensa dianteira",
        "Massa das peças da frente que não são sustentadas pela mola (roda, pneu, cubo, parte dos braços), por eixo.")
    add("muR_kg", "muR", _v40("muR"), "kg", "Massa não suspensa traseira",
        "Massa das peças de trás que não são sustentadas pela mola, por eixo.")
    add("d_pneu_F_pol", None, "ent_05_diametro_do_pneu_dianteiro", "in", "Diâmetro do pneu dianteiro",
        "Diâmetro externo do pneu da frente, em polegadas.")
    add("d_pneu_R_pol", None, "ent_05_diametro_do_pneu_traseiro", "in", "Diâmetro do pneu traseiro",
        "Diâmetro externo do pneu de trás, em polegadas.")
    add("razao_hns_F", None, "ent_05_razao_h_ns_raio_do_pneu_dianteiro", "-", "Altura da massa não suspensa, frente",
        "Altura do centro das massas não suspensas da frente, como fração do raio do pneu.")
    add("razao_hns_R", None, "ent_05_razao_h_ns_raio_do_pneu_traseiro", "-", "Altura da massa não suspensa, trás",
        "Altura do centro das massas não suspensas de trás, como fração do raio do pneu.")
    # 06_SUSPENSION
    for e, eixo in (("F", "dianteira"), ("R", "traseira")):
        add(f"Ks{e}_N_m", f"Ks{e}", _v40(f"Ks{e}"), "N/m", f"Rigidez da mola {eixo}",
            f"Rigidez da mola da suspensão {eixo}, medida na própria mola.")
        add(f"MR{e}", f"MR{e}", _v40(f"MR{e}"), "-", f"Relação de movimento {eixo}",
            f"Quanto a roda se move para cada milímetro que a mola se move, suspensão {eixo}.")
        add(f"Karb{e}_Nm_rad", f"Karb{e}", _v40(f"Karb{e}"), "N*m/rad", f"Rigidez da barra estabilizadora {eixo}",
            f"Quanto a barra estabilizadora {eixo} resiste à rolagem da carroceria.")
        add(f"z{e}_m", f"z{e}", _v40(f"z{e}"), "m", f"Altura do centro de rolagem {eixo}",
            f"Altura do centro de rolagem do eixo {eixo}, na posição parada.")
        add(f"KT{e}_N_m", f"KT{e}", _v40(f"KT{e}"), "N/m", f"Rigidez vertical do pneu {eixo}",
            f"Quanto o pneu {eixo} resiste a ser comprimido na vertical.")
    # 08_VEHICLE_STATE
    add("DF_N", "DF", _v40("DF"), "N", "Força aerodinâmica para baixo",
        "Força vertical total que o ar faz sobre o carro, para baixo, usada quando a hipótese h8 está desligada.")
    add("bal_dianteira", "bal", _v40("bal"), "-", "Parte da força aerodinâmica na frente",
        "Fração da força aerodinâmica para baixo que atua no eixo dianteiro, de 0 a 1.")
    # 07_KINEMATICS e 10_TIRE
    add("dgF_grau_mm", "dgF", _v40("dgF"), "deg/mm", "Ganho de camber dianteiro",
        "Quanto o ângulo de camber da roda da frente muda para cada milímetro de curso da suspensão.")
    add("dgR_grau_mm", "dgR", _v40("dgR"), "deg/mm", "Ganho de camber traseiro",
        "Quanto o ângulo de camber da roda de trás muda para cada milímetro de curso da suspensão.")
    add("epsF_rad_rad", "epsF", _v40("epsF"), "°/°", "Esterço de rolagem dianteiro",
        "Quanto a roda da frente esterça sozinha quando a carroceria rola, em graus por grau de rolagem.")
    add("epsR_rad_rad", "epsR", _v40("epsR"), "°/°", "Esterço de rolagem traseiro",
        "Quanto a roda de trás esterça sozinha quando a carroceria rola, em graus por grau de rolagem.")
    for k, nome in (("FL", "dianteira esquerda"), ("FR", "dianteira direita"), ("RL", "traseira esquerda"),
                    ("RR", "traseira direita")):
        add(f"gs{k}_grau", f"gs{k}", _v40(f"gs{k}"), "°", f"Camber estático, roda {nome}",
            f"Inclinação da roda {nome} com o carro parado; positivo = topo da roda para fora.")
    add("eixos_tir", "eixos", _v40("eixos"), "-", "Sistema de eixos do arquivo do pneu",
        "Convenção de eixos em que o arquivo do pneu foi medido (ISO_TYDEX ou SAE_CALSPAN).", "texto")
    # 16_EQUILIBRIO
    add("sentido", "sentido", ae.NOME_ENT["sentido"], "-", "Sentido da curva",
        "Para que lado o carro faz a curva: Esquerda ou Direita.", "texto")
    for k, nome in (("FL", "dianteira esquerda"), ("FR", "dianteira direita"), ("RL", "traseira esquerda"),
                    ("RR", "traseira direita")):
        add(f"toe{k}_grau", f"toe{k}", ae.NOME_ENT[f"toe{k}"], "°", f"Convergência (toe), roda {nome}",
            f"Ângulo da roda {nome} em relação ao eixo do carro; positivo = abre para fora (toe-out).")
    add("R_m", "R", ae.NOME_ENT["R"], "m", "Raio da curva",
        "Raio da curva que o carro percorre, usado pelas hipóteses que dependem da trajetória.")
    add("cg_lateral_m", "cg", ae.NOME_ENT["cg"], "m", "Posição lateral do centro de gravidade",
        "Quanto o centro de gravidade está deslocado para o lado esquerdo do carro; negativo = direita.")
    add("cza_m2", "cza", ae.NOME_ENT["cza"], "m²", "Área efetiva de sustentação (CzA)",
        "Produto do coeficiente de sustentação para baixo pela área de referência.")
    add("rho_kg_m3", "rho", ae.NOME_ENT["rho"], "kg/m³", "Densidade do ar", "Massa de ar por metro cúbico.")
    add("cda_m2", "cda", ae.NOME_ENT["cda"], "m²", "Área efetiva de arrasto (CdA)",
        "Produto do coeficiente de arrasto do ar pela área de referência.")
    add("crr", "crr", ae.NOME_ENT["crr"], "-", "Resistência ao rolamento (Crr)",
        "Fração do peso que vira força contra o movimento por causa do rolamento do pneu.")
    add("h2", "h2", ae.NOME_ENT["h2"], "0/1", "Hipótese h2: geometria de Ackermann",
        "1 = usa a porcentagem de Ackermann da direção; 0 = desligada.", "chave")
    add("h3", "h3", ae.NOME_ENT["h3"], "0/1", "Hipótese h3: cosseno do esterço médio na frente",
        "1 = considera o esterço da roda dianteira na força lateral; 0 = desligada.", "chave")
    add("h7", "h7", ae.NOME_ENT["h7"], "0/1", "Hipótese h7: centro de gravidade deslocado",
        "1 = usa a posição lateral do centro de gravidade; 0 = desligada.", "chave")
    add("h8", "h8", ae.NOME_ENT["h8"], "0/1", "Hipótese h8: aerodinâmica pela velocidade",
        "1 = calcula a força aerodinâmica pela velocidade na curva; 0 = usa a força fixa.", "chave")
    add("h9", "h9", ae.NOME_ENT["h9"], "0/1", "Hipótese h9: tração no eixo traseiro",
        "1 = inclui a força de tração do eixo traseiro; 0 = desligada.", "chave")
    # 24_CURVA
    add("h2v", "h2v", aba_curva.NOME24["h2v"], "0/1", "Forma do Ackermann: ângulos de cada roda",
        "1 = usa os ângulos de esterço de cada roda calculados pela geometria da curva; 0 = forma antiga.", "chave")
    add("h9v", "h9v", aba_curva.NOME24["h9v"], "0/1", "Forma da tração: força exigida pela curva",
        "1 = usa a força longitudinal exigida pela trajetória; 0 = forma antiga.", "chave")
    add("fator_neutro", "fator", aba_curva.NOME24["fator"], "-", "Fator da faixa do equilíbrio neutro",
        "Quanto a diferença entre frente e trás pode variar para o carro ainda contar como neutro.")
    # outros
    add("ackermann_pct", "pct", _v40("pct"), "%", "Porcentagem de Ackermann",
        "Quanto a direção se aproxima da geometria de Ackermann exata; 100 = exata. Só é lida com a h2 ligada.")
    add("crr_referencia", None, None, "-", "Crr de referência",
        "Valor de referência da resistência ao rolamento para comparar com o arrasto; sem fonte, fica a confirmar.")
    # fatores de escala do pneu presentes na 10_TIRE
    for n in FATORES_LAMBDA:
        if n in ae.COEF_TIR:
            add(f"lambda_{n}", None, ae.nome_coef(n), "-", f"Fator de escala {n} do pneu",
                f"Multiplica o coeficiente {n} do modelo do pneu; 1 = sem alteração.")
    return c


CAMPOS: dict[str, Campo] = _montar()
LAMBDAS = tuple(k[len("lambda_"):] for k in CAMPOS if k.startswith("lambda_"))

# res_ recalculados (D2): chave de x -> (aba e célula da V4.4, unidade)
RES = {"m": ("05_VEHICLE B4", "kg"), "a": ("05_VEHICLE B9", "m"), "b": ("05_VEHICLE B10", "m"),
       "huF": ("05_VEHICLE B16", "m"), "huR": ("05_VEHICLE B17", "m")}
# campos de que cada res_ depende
_DEPENDE = {"m": ("m_sem_piloto_kg", "m_piloto_kg"), "a": ("L_m", "f_dianteira"), "b": ("L_m", "f_dianteira"),
            "huF": ("d_pneu_F_pol", "razao_hns_F"), "huR": ("d_pneu_R_pol", "razao_hns_R")}

# Do melhor para o pior, como a lista `Origens` da V4.4 (00_README A43:A48; a 23_LISTAS não guarda origens). A fonte
# única no código é `origens.ORIGENS_V42`, conferida contra a lista da planilha na captura.
_ORDEM_ORIGEM = origens.ORIGENS_V42


def _eh_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


# ---------------------------------------------------------------------------------------------------------------------
# Validação, edição e arquivo
# ---------------------------------------------------------------------------------------------------------------------
def _valida_valor(chave: str, valor, permitir_nulo: bool = False):
    """Devolve o valor normalizado ou levanta ValueError (a mensagem cita a chave)."""
    campo = CAMPOS[chave]
    if valor is None:
        if permitir_nulo:
            return None
        raise ValueError(f"{chave}: precisa de um valor ({campo.rotulo}).")
    if campo.tipo == "texto":
        if chave == "sentido" and valor not in SENTIDOS:
            raise ValueError(f"{chave}: use Esquerda ou Direita (com a primeira letra maiúscula); recebi {valor!r}.")
        if chave == "eixos_tir" and valor not in AXIS_TRANSFORMS:
            raise ValueError(f"{chave}: use um sistema de eixos conhecido ({', '.join(sorted(AXIS_TRANSFORMS))}); "
                             f"recebi {valor!r}.")
        if not isinstance(valor, str):
            raise ValueError(f"{chave}: precisa ser um texto; recebi {valor!r}.")
        return valor
    if not _eh_num(valor):
        raise ValueError(f"{chave}: precisa ser um número; recebi {valor!r}.")
    if campo.tipo == "chave":
        if valor not in (0, 1):
            raise ValueError(f"{chave}: é uma chave, aceita só 0 (desligada) ou 1 (ligada); recebi {valor!r}.")
        return int(valor)
    return valor


def _checar_estrutura(dados: dict) -> None:
    if not isinstance(dados, dict) or dados.get("schema") != SCHEMA or not isinstance(dados.get("campos"), dict):
        raise ValueError(f"o arquivo não é um caso do pneu-1 (esperado schema {SCHEMA!r}).")
    faltam = [k for k in CAMPOS if k not in dados["campos"]]
    sobram = [k for k in dados["campos"] if k not in CAMPOS]
    if faltam or sobram:
        raise ValueError(f"campos do caso não batem com o catálogo: faltam {faltam}, sobram {sobram}.")
    for k, reg in dados["campos"].items():
        if not isinstance(reg, dict) or "valor" not in reg or not isinstance(reg.get("origem"), str):
            raise ValueError(f"{k}: registro sem valor ou sem origem.")
        _valida_valor(k, reg["valor"], permitir_nulo=True)


def ler_caso(caminho: str | Path) -> dict:
    """Lê o JSON do caso e confere a estrutura (schema e o conjunto de campos do catálogo)."""
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    _checar_estrutura(dados)
    return dados


def editar(dados: dict, **chaves) -> dict:
    """Cópia de `dados` com os campos `chaves` trocados; cada um vira origem `✎ Editado pelo usuário` e `editado` true.
    Só aceita chaves de CAMPOS; tudo é conferido antes de qualquer troca."""
    novos = {}
    for k, v in chaves.items():
        if k not in CAMPOS:
            raise ValueError(f"{k}: não é um campo do caso. Campos válidos: {', '.join(CAMPOS)}.")
        novos[k] = _valida_valor(k, v)
    out = copy.deepcopy(dados)
    for k, v in novos.items():
        reg = out["campos"][k]
        reg["valor"] = v
        reg["origem"] = ORIGEM_EDITADO
        reg["editado"] = True
    return out


def aplicar_set(dados: dict, pares: list[str]) -> dict:
    """Lê pares `chave=valor` (a vírgula decimal vale) e chama `editar`. Erro de leitura levanta ValueError citando a
    chave (ou o par, se não tiver `=`)."""
    chaves = {}
    for par in pares:
        if "=" not in par:
            raise ValueError(f"{par!r}: use o formato chave=valor.")
        k, _, txt = par.partition("=")
        k, txt = k.strip(), txt.strip()
        if k not in CAMPOS:
            raise ValueError(f"{k}: não é um campo do caso. Campos válidos: {', '.join(CAMPOS)}.")
        if CAMPOS[k].tipo == "texto":
            chaves[k] = txt
            continue
        try:
            v = float(txt.replace(",", "."))
        except ValueError:
            raise ValueError(f"{k}: {txt!r} não é um número.") from None
        chaves[k] = int(v) if CAMPOS[k].tipo == "chave" and v in (0.0, 1.0) else v
    return editar(dados, **chaves)


def _mesmo_caminho(a: str | Path, b: str | Path) -> bool:
    return os.path.normcase(str(Path(a).resolve())) == os.path.normcase(str(Path(b).resolve()))


def salvar_caso(dados: dict, caminho: str | Path) -> Path:
    """Grava `dados` em `caminho`. Recusa o caso demonstrativo do repositório (é o dado capturado, imutável)."""
    if _mesmo_caminho(caminho, CAMINHO_DEMONSTRATIVO):
        raise ValueError("não grave por cima do caso demonstrativo (data/casos/caso_pneu1_demonstrativo.json): "
                         "ele guarda o dado capturado da planilha. Escolha outro nome de arquivo.")
    _checar_estrutura(dados)
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destino


# ---------------------------------------------------------------------------------------------------------------------
# Do caso ao x da planilha
# ---------------------------------------------------------------------------------------------------------------------
def _valor(dados: dict, chave: str):
    return dados["campos"][chave]["valor"]


def _res(dados: dict) -> dict:
    """Resultados `res_` recalculados pela regra da célula da V4.4 (D2); None se faltar uma entrada."""
    def tem(*ks):
        return all(_eh_num(_valor(dados, k)) for k in ks)
    r = dict.fromkeys(RES)
    if tem("m_sem_piloto_kg", "m_piloto_kg"):
        r["m"] = _valor(dados, "m_sem_piloto_kg") + _valor(dados, "m_piloto_kg")                  # 05_VEHICLE B4
    if tem("L_m", "f_dianteira"):
        r["a"] = _valor(dados, "L_m") * (1 - _valor(dados, "f_dianteira"))                          # 05_VEHICLE B9
        r["b"] = _valor(dados, "L_m") * _valor(dados, "f_dianteira")                                # 05_VEHICLE B10
    for e in "FR":                                                                                  # B16 e B17
        if tem(f"d_pneu_{e}_pol", f"razao_hns_{e}"):
            r[f"hu{e}"] = _valor(dados, f"d_pneu_{e}_pol") * 0.0254 / 2 * _valor(dados, f"razao_hns_{e}")
    return r


def x_de_dados(dados: dict) -> dict:
    """O `x` que `caso_planilha._caso_de_valores` espera (as chaves de `ENTRADAS16`, `V40`, mais `coef`, `coef_nomes`,
    `motivo_r`, `R`, `fator` e `pct`), com os `res_` recalculados. Campo nulo vira None (a verificação da planilha
    acusa "a confirmar")."""
    x = {c.chave_x: _valor(dados, k) for k, c in CAMPOS.items() if c.chave_x is not None}
    x.update(_res(dados))
    lam = {n: _valor(dados, f"lambda_{n}") for n in LAMBDAS}
    x["coef_nomes"] = lam
    x["coef"] = list(lam.values())
    x["motivo_r"] = ""
    return x


@dataclass(frozen=True)
class ValorUsado:
    chave: str
    valor: float | int | str | None
    unidade: str
    origem: str
    editado: bool
    calculado_por: str | None


def valores_usados(dados: dict) -> tuple[ValorUsado, ...]:
    """Todos os campos do caso e, depois, os cinco `res_` recalculados (com a aba e a célula da regra). A origem de um
    `res_` é a pior das origens das entradas; sem uma entrada, o valor é None e a origem `? A confirmar`."""
    out = [ValorUsado(k, reg["valor"], CAMPOS[k].unidade, reg["origem"], bool(reg.get("editado", False)), None)
           for k, reg in dados["campos"].items()]
    res = _res(dados)

    def pos(o: str) -> int:
        if o == ORIGEM_EDITADO:          # dado do usuário: melhor que qualquer origem da lista
            return -1
        return _ORDEM_ORIGEM.index(o) if o in _ORDEM_ORIGEM else len(_ORDEM_ORIGEM) - 1
    for k, (celula, unidade) in RES.items():
        ent = [dados["campos"][d] for d in _DEPENDE[k]]
        origem = ORIGEM_A_CONFIRMAR if res[k] is None else max((e["origem"] for e in ent), key=pos)
        out.append(ValorUsado(k, res[k], unidade, origem, any(bool(e.get("editado", False)) for e in ent), celula))
    return tuple(out)
