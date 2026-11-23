"""
Configuração do posicionador com procedência (EDR-076).

Cada item do arquivo JSON (`data/posicionador/config_T11.json`, chave "itens") é
`{"valor", "unidade", "origem", "fonte"}`:
- `valor`: em SI (m, rad, adimensional); a `unidade` só documenta, não há conversão na leitura.
  Pode ser número, lista ou dicionário (caixa de busca, transformação do STEP).
- `origem` ∈ ORIGENS = {REGRA, META, MARGEM_EQUIPE, HIPOTESE, A_CONFIRMAR}.
- `fonte`: texto não vazio (arquivo, bloco, SHA-256, seção do regulamento...).
- `valor: null` só com `origem: "A_CONFIRMAR"`, e `A_CONFIRMAR` sempre com `valor: null`: desliga a verificação
  correspondente, e o resultado do candidato sai CONDICIONAL.

Nomes dos itens lidos pelas outras partes do posicionador (Config.valor(nome)):
- curso da roda e amortecedor: `curso_droop_m`, `curso_bump_m`, `olho_a_olho_m` (EYE), `curso_amortecedor_m` (STROKE);
- motion ratio: `mr_alvo`, `mr_var_max` (MR [wheel/spring]);
- mecanismo: `dj_m` (fixação do push rod a DJ da junta), `braco_min_m`, `braco_max_m`, `giro_max_rad`, `amort_ang_max_rad`;
- folgas: `folga_aro_m`, `folga_pernas_m`, `folga_prod_amort_m`, `folga_gabarito_m`;
- raios dos envelopes: `r_mola_m`, `r_junta_m`, `r_pivo_m`, `r_prod_m`, `r_perna_bandeja_m`;
- aro: `aro_r_int_m`, `aro_meia_largura_m`;
- busca: `x_max_olhal_m`, `caixa_busca_pivo_m` ({"min_m": [x, y, z], "max_m": [x, y, z]}, com null no eixo que vem
  do STEP ou de --caixa);
- STEP: `transformacao_step_m` ({"rotacao": 3×3, "translacao_m": [x, y, z]}, STEP em m → canto);
- a confirmar (null): `curso_cremalheira_m`, `margem_curso_amortecedor_m`, `x_face_traseira_aip_m`, `x_ini_t12_m`,
  `x_fim_t12_m`, `z_min_t12_m`, `z_max_t12_m` (faixa vertical do gabarito T.1.2, T.1.2.2c).

Itens obrigatórios (`OBRIGATORIOS`): o núcleo não tem caminho para eles nulos (não há verificação a desligar), então
`carregar` exige que estejam presentes, com número finito, e recusa (ConfigError com o nome do item) se faltarem ou
vierem A_CONFIRMAR. Todo número da configuração (também dentro de listas e dicionários) tem de ser finito: NaN e
Infinity do JSON são recusados.
"""
import json
import math
from dataclasses import dataclass
from typing import Any

ORIGENS = frozenset({"REGRA", "META", "MARGEM_EQUIPE", "HIPOTESE", "A_CONFIRMAR"})
# lidos com float(cfg.valor(...)) por mecanismo e varredura, sem verificação a desligar quando nulos
OBRIGATORIOS = ("curso_droop_m", "curso_bump_m", "olho_a_olho_m", "curso_amortecedor_m", "mr_alvo", "mr_var_max", "dj_m",
                "braco_min_m", "braco_max_m", "giro_max_rad", "amort_ang_max_rad", "folga_aro_m", "folga_pernas_m",
                "folga_prod_amort_m", "folga_gabarito_m", "r_mola_m", "r_junta_m", "r_pivo_m", "r_prod_m",
                "r_perna_bandeja_m", "aro_r_int_m", "aro_meia_largura_m")
CAMPOS = ("valor", "unidade", "origem", "fonte")


class ConfigError(ValueError):
    """Configuração inválida: item sem procedência, origem desconhecida ou valor nulo fora de A_CONFIRMAR."""


@dataclass(frozen=True)
class Item:
    valor: Any
    unidade: str
    origem: str
    fonte: str


@dataclass
class Config:
    itens: dict          # nome -> Item
    caminho: str | None = None

    def item(self, nome):
        try:
            return self.itens[nome]
        except KeyError:
            raise KeyError(f"item {nome!r} ausente da configuração {self.caminho or ''}; itens: {sorted(self.itens)}")

    def valor(self, nome):
        """Valor em SI (None se o item é A_CONFIRMAR)."""
        return self.item(nome).valor

    def a_confirmar(self):
        """Nomes dos itens com origem A_CONFIRMAR (valor null), em ordem alfabética."""
        return sorted(n for n, it in self.itens.items() if it.origem == "A_CONFIRMAR")


def _nao_finitos(v):
    """True se há algum número não finito em v (número, lista ou dicionário)."""
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return not math.isfinite(v)
    if isinstance(v, (list, tuple)):
        return any(_nao_finitos(x) for x in v)
    if isinstance(v, dict):
        return any(_nao_finitos(x) for x in v.values())
    return False


def _item(nome, d):
    if not isinstance(d, dict):
        raise ConfigError(f"item {nome!r}: esperado objeto com {list(CAMPOS)}, veio {type(d).__name__}")
    faltam = [c for c in CAMPOS if c not in d]
    if faltam:
        raise ConfigError(f"item {nome!r}: faltam os campos {faltam} (todo item precisa de valor, unidade, origem e fonte)")
    extras = sorted(set(d) - set(CAMPOS))
    if extras:
        raise ConfigError(f"item {nome!r}: campos desconhecidos {extras}")
    origem, fonte, unidade = d["origem"], d["fonte"], d["unidade"]
    if origem not in ORIGENS:
        raise ConfigError(f"item {nome!r}: origem {origem!r} desconhecida; use uma de {sorted(ORIGENS)}")
    if not isinstance(fonte, str) or not fonte.strip():
        raise ConfigError(f"item {nome!r}: fonte vazia (todo valor precisa de fonte)")
    if not isinstance(unidade, str) or not unidade.strip():
        raise ConfigError(f"item {nome!r}: unidade vazia")
    if d["valor"] is None and origem != "A_CONFIRMAR":
        raise ConfigError(f"item {nome!r}: valor null só com origem A_CONFIRMAR (veio {origem})")
    if origem == "A_CONFIRMAR" and d["valor"] is not None:
        raise ConfigError(f"item {nome!r}: A_CONFIRMAR exige valor null (valor provisório com fonte é HIPOTESE)")
    if _nao_finitos(d["valor"]):
        raise ConfigError(f"item {nome!r}: valor com número não finito (NaN ou infinito): {d['valor']!r}")
    return Item(valor=d["valor"], unidade=unidade, origem=origem, fonte=fonte)


def carregar(caminho):
    """Lê e valida o JSON da configuração. Levanta ConfigError se algum item não tiver procedência válida."""
    with open(caminho, encoding="utf-8") as f:
        bruto = json.load(f)
    itens = bruto.get("itens") if isinstance(bruto, dict) else None
    if not isinstance(itens, dict) or not itens:
        raise ConfigError(f"{caminho}: esperado objeto com a chave 'itens' (nome -> item)")
    cfg = Config(itens={n: _item(n, d) for n, d in itens.items()}, caminho=str(caminho))
    for nome in OBRIGATORIOS:
        if nome not in cfg.itens:
            raise ConfigError(f"{caminho}: item obrigatório {nome!r} ausente")
        v = cfg.itens[nome].valor
        if v is None:
            raise ConfigError(f"item obrigatório {nome!r} sem valor (A_CONFIRMAR): o posicionador não tem verificação a "
                              "desligar para ele; dê um valor com origem e fonte (HIPOTESE, se provisório)")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ConfigError(f"item obrigatório {nome!r}: esperado número, veio {type(v).__name__}")
    return cfg
