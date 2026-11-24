"""
Reconhecimento dos componentes do CAD pelo nome (posicionador, fase 2).

Problema: o documento de exportação do CAD pede prefixos exatos (`CHASSI_`, `BANDEJA_FE_`, `DIR_`, ...), mas o T11 de
verdade tem nomes parecidos e não idênticos. Este módulo diz, para cada componente de primeiro nível, a que categoria ele
pertence, COM O NÍVEL DE CONFIANÇA, para que ninguém dependa de uma suposição silenciosa.

Níveis (do mais ao menos confiável):
- `exata`: o nome começa com um prefixo do documento (sensível a caixa), como o leitor de STEP (`cad_step.PREFIXOS`).
- `normalizada`: igual, depois de tirar acento, caixa, espaços e hífens (`bandeja fe inferior` → `BANDEJA_FE_`).
- `mapa`: o usuário decidiu num arquivo JSON (`{"nome do componente": "CATEGORIA"}`); vale mais que qualquer regra.
- `inferida`: palavras-chave do nome (TIRANTE, WISHBONE, PUSHROD...). É uma SUGESTÃO: `usavel()` devolve falso e quem
  consome deve pedir confirmação ou gravar a decisão no mapa. Nada é inventado: sem palavra-chave, sem categoria.
- `nao_reconhecido`: nenhuma regra serviu. Atenção: o leitor de STEP trataria um nome sem prefixo como `FIXO`
  (obstáculo), então uma peça da suspensão sem nome reconhecido viraria obstáculo e colidiria. Por isso o campo
  `padrao_se_ignorado` avisa disso.

Só biblioteca padrão e nenhum `import adsk`: o mesmo arquivo roda nos testes (Python 3.13) e dentro do Fusion (3.14).
Usada em `docs/posicionador/fusion/T11_sondagem/` (cópia idêntica, conferida por teste).
"""
import json
import re
import unicodedata
from dataclasses import dataclass

# Os mesmos prefixos de cad_step.PREFIXOS (um teste confere a igualdade; aqui não se importa o cad_step porque ele
# puxa numpy, que o Python do Fusion não tem).
PREFIXOS = (("CHASSI_", "CHASSI"), ("FIXO_", "FIXO"), ("RODA_FE_", "RODA_FE"), ("RODA_FD_", "RODA_FD"),
            ("BANDEJA_FE_", "BANDEJA_FE"), ("BANDEJA_FD_", "BANDEJA_FD"), ("DIR_", "DIR"), ("REF_", "REF"),
            ("HP_", "HP"), ("IGNORAR_", "IGNORAR"))
CATEGORIAS = tuple(c for _, c in PREFIXOS)

NIVEIS_USAVEIS = ("exata", "normalizada", "mapa")

# Palavras-chave (sobre os tokens do nome normalizado). "DIR" sozinho NÃO é lado direito: é o prefixo de direção.
_LADO_FE = {"FE", "FL", "LF", "ESQ", "ESQUERDA", "ESQUERDO", "LEFT", "LH"}
_LADO_FD = {"FD", "FR", "RF", "DIREITA", "DIREITO", "RIGHT", "RH"}
_TRASEIRA = {"TRAS", "TRASEIRA", "TRASEIRO", "TE", "TD", "REAR", "RR", "RL"}
_REF = {"REF", "REFERENCIA", "REFERENCIAS", "REFERENCE"}
_HP = {"HP", "HARDPOINT", "HARDPOINTS", "PONTO", "PONTOS"}
_IGNORAR = {"IGNORAR", "IGNORE", "IGNORADO"}
_CHASSI = {"CHASSI", "CHASSIS", "TUBO", "TUBOS", "FRAME", "MONOCOQUE"}
_RODA = {"RODA", "ARO", "PNEU", "WHEEL", "TIRE"}
_BANDEJA = {"BANDEJA", "WISHBONE", "AARM"}
_DIRECAO = {"TIRANTE", "CREMALHEIRA", "RACK", "DIRECAO", "STEERING", "TIEROD"}
_ATUACAO = {"PUSHROD", "PUSH", "ROCKER", "AMORTECEDOR", "AMORTECEDORES", "DAMPER", "ATUACAO", "GABARITO", "MOLA",
            "SPRING"}


@dataclass(frozen=True)
class Reconhecimento:
    nome: str                      # nome recebido, sem o sufixo de instância (":1")
    categoria: str | None          # uma de CATEGORIAS, ou None se não reconhecido
    nivel: str                     # exata | normalizada | mapa | inferida | nao_reconhecido
    motivo: str                    # por que, em uma frase
    padrao_se_ignorado: str = ""   # só em nao_reconhecido: o que o leitor de STEP faria com o nome

    @property
    def usavel(self):
        return usavel(self)


def nome_base(nome):
    """Tira o sufixo de instância do Fusion (`BANDEJA_FE_V20_1:1` → `BANDEJA_FE_V20_1`)."""
    return re.sub(r":\d+$", "", nome.strip())


def normalizar(nome):
    """Maiúsculas, sem acento, separadores (espaço, hífen, ponto, parênteses...) viram `_`."""
    s = unicodedata.normalize("NFKD", nome_base(nome))
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]", "_", s)).strip("_")


def _tokens(nome):
    return set(normalizar(nome).split("_"))


def validar_mapa(mapa):
    """Mapa `{nome: categoria}` com chave normalizada. ValueError se a categoria não existir."""
    out = {}
    for nome, cat in (mapa or {}).items():
        if cat not in CATEGORIAS:
            raise ValueError(f"categoria {cat!r} do componente {nome!r} não existe; use uma de {CATEGORIAS}")
        out[normalizar(nome)] = cat
    return out


def carregar_mapa(caminho):
    """Lê o JSON `{"nome do componente": "CATEGORIA", ...}` (chaves que começam com `_` são comentários)."""
    with open(caminho, encoding="utf-8") as f:
        bruto = json.load(f)
    return validar_mapa({k: v for k, v in bruto.items() if not k.startswith("_")})


def _lado(tokens):
    fe, fd = bool(tokens & _LADO_FE), bool(tokens & _LADO_FD)
    if fe and not fd:
        return "FE"
    if fd and not fe:
        return "FD"
    return None


def lado_do_nome(nome):
    """'FE' (esquerda, +Y), 'FD' (direita, −Y) ou None, pelas palavras de lado do nome (FE/FD/ESQ/DIREITA...)."""
    return _lado(_tokens(nome))


def _inferir(nome):
    """(categoria, motivo) por palavra-chave, ou (None, motivo) se nenhuma regra serviu."""
    t = _tokens(nome)
    lado = _lado(t)
    if t & _REF:
        return "REF", "palavra de referencial no nome"
    if t & _HP:
        return "HP", "palavra de hardpoint/pontos no nome"
    if t & _IGNORAR:
        return "IGNORAR", "a palavra IGNORAR aparece no nome"
    if t & _TRASEIRA:
        return "IGNORAR", "marca de traseira no nome; o T11 ignora a traseira (IGNORAR_TRASEIRA)"
    if t & _CHASSI:
        return "CHASSI", "palavra de chassi/tubos no nome"
    if t & _RODA:
        if lado:
            return f"RODA_{lado}", f"palavra de roda e lado {lado} no nome"
        return None, "palavra de roda sem lado (FE ou FD) identificável"
    if t & _BANDEJA:
        if lado:
            return f"BANDEJA_{lado}", f"palavra de bandeja e lado {lado} no nome"
        return None, "palavra de bandeja sem lado (FE ou FD) identificável"
    if t & _DIRECAO:
        return "DIR", "palavra de direção (tirante/cremalheira) no nome"
    if t & _ATUACAO:
        return "IGNORAR", "peça da atuação/gabarito: o posicionador a trata como IGNORAR (convenção do T11)"
    return None, "nenhuma palavra-chave conhecida no nome"


def reconhecer(nome, mapa=None):
    """Classifica um componente de primeiro nível. `mapa` já validado (`validar_mapa`/`carregar_mapa`) ou None."""
    base = nome_base(nome)
    chave = normalizar(base)
    if mapa and chave in mapa:
        return Reconhecimento(base, mapa[chave], "mapa", "decisão do usuário no mapa de componentes")
    for prefixo, cat in PREFIXOS:
        if base.startswith(prefixo):
            return Reconhecimento(base, cat, "exata", f"prefixo {prefixo}")
    for prefixo, cat in PREFIXOS:
        if chave.startswith(prefixo):
            return Reconhecimento(base, cat, "normalizada", f"prefixo {prefixo} depois de normalizar o nome")
    cat, motivo = _inferir(base)
    if cat:
        return Reconhecimento(base, cat, "inferida", motivo)
    return Reconhecimento(base, None, "nao_reconhecido", motivo, padrao_se_ignorado="FIXO")


def reconhecer_todos(nomes, mapa=None):
    return [reconhecer(n, mapa) for n in nomes]


def usavel(r):
    """Pode ser usado sem pedir confirmação? Só exata, normalizada e mapa."""
    return r.nivel in NIVEIS_USAVEIS


def resumo(lista):
    """Contagens por nível e por categoria, mais as listas que pedem decisão do usuário."""
    por_nivel, por_cat = {}, {}
    for r in lista:
        por_nivel[r.nivel] = por_nivel.get(r.nivel, 0) + 1
        if r.categoria:
            por_cat[r.categoria] = por_cat.get(r.categoria, 0) + 1
    return {
        "por_nivel": por_nivel,
        "por_categoria": por_cat,
        "a_confirmar": [{"nome": r.nome, "sugestao": r.categoria, "motivo": r.motivo}
                        for r in lista if r.nivel == "inferida"],
        "nao_reconhecidos": [{"nome": r.nome, "motivo": r.motivo, "padrao_se_ignorado": r.padrao_se_ignorado}
                             for r in lista if r.nivel == "nao_reconhecido"],
    }


def modelo_de_mapa(lista):
    """Esqueleto de mapa JSON para o usuário preencher: as sugestões inferidas e os não reconhecidos (valor vazio)."""
    out = {"_comentario": "Preencha a categoria de cada componente. Categorias: " + ", ".join(CATEGORIAS)}
    for r in lista:
        if r.nivel == "inferida":
            out[r.nome] = r.categoria
        elif r.nivel == "nao_reconhecido":
            out[r.nome] = ""
    return out
