"""Oráculo das metas e da coerência das fichas (V4.2, incremento 5; EDR-061).

A planilha (03_TARGETS H:Q, 23_LISTAS e o bloco de metas do 14_DASHBOARD, `aba_metas.py`) reproduz estas regras em
fórmulas, e o TC-WB42-006 confere as duas contra a mesma lista de fichas. Nada aqui calcula engenharia: são regras de
processo (vocabulário, sobredeterminação, compromisso com EDR) sobre os campos que a equipe preenche.

Estado de coerência (decisão 4 do plano; a primeira regra que bate decide):
1. campo fora do vocabulário (Papel, Ciclo de vida, Congelamento) -> CONFLITO: <campo> fora do vocabulário;
2. Papel = META e outra META na mesma alavanca -> CONFLITO: sobredeterminação (<alavanca>; escolha qual manda)
   (spec §5, itens 1b e 2);
3. Papel = TBD, ou Target = TBD ou vazio -> NÃO AVALIÁVEL: meta sem valor ou papel (TBD) (extensão do NÃO AVALIÁVEL da
   spec §4.4 a meta sem valor: "COERENTE" numa meta vazia diria "ok" onde nada foi avaliado, spec §5 item 8);
4. compromisso declarado preenchido: com EDR no formato `EDR-ddd` -> COMPROMISSO DECLARADO; sem EDR ou fora do formato ->
   CONFLITO: compromisso sem EDR (spec §5 item 1c);
5. senão -> COERENTE (regras avaliadas: vocabulário e sobredeterminação).
O texto final é `<estado> · <pior origem da grandeza>` (spec §4.4). Que o EDR citado existe e está aprovado é conferido
fora da planilha (TC-WB42-001 e `conferir_viva`): uma cópia do status do EDR na planilha envelheceria em silêncio.

Comparações exatas (maiúsculas e minúsculas contam): na planilha, `EXACT`, porque o `MATCH` e o `=` do Excel não
distinguem "meta" de "META" e a validação de dados não pega um valor colado por cima. Ausência de relação para a meta =
alavanca None (a planilha mostra "sem relação na 23_LISTAS"); ausência de linha é "não avaliado", nunca "ok".

Relações (spec §5 item 8; decisão 5 do plano): cada linha tem fonte L (livro e página, conferida na imagem do PDF), E (EDR
existente e aprovado) ou M (nome do resultado e nome da entrada da alavanca; a entrada tem de ser raiz do resultado no
grafo de fórmulas, `raizes.Grafo`). Linha sem fonte não existe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Vocabulários fechados (Global Constraints do plano). O significado de cada valor está em SIGNIFICADO.
VOCAB: dict[str, tuple[str, ...]] = {
    "papel": ("META", "CONSEQUÊNCIA", "TBD"),
    "ciclo": ("TBD", "OPEN", "PROPOSED", "APPROVED", "FROZEN", "STALE"),
    "congelamento": ("F0", "F1", "F2", "F3", "F4"),
    "coerencia": ("COERENTE", "COMPROMISSO DECLARADO", "CONFLITO", "NÃO AVALIÁVEL"),
    "fonte": ("L", "E", "M"),
}
# campo da ficha (chave de VOCAB) -> nome que aparece no CONFLITO, na ordem em que a regra 1 olha
CAMPOS_VOCAB: tuple[tuple[str, str], ...] = (("papel", "Papel"), ("ciclo", "Ciclo de vida"), ("congelamento", "Congelamento"))

# Significado de cada valor (23_LISTAS). ciclo: [GUIA] G.1; congelamento: [GUIA] §3.2 (significado, uso); coerência: spec §4.4.
SIGNIFICADO: dict[str, dict[str, object]] = {
    "papel": {
        "META": "Valor que a equipe escolhe: manda na alavanca (spec §5, item 2). Duas METAs na mesma alavanca são sobredeterminação.",
        "CONSEQUÊNCIA": "Resultado do modelo, dadas as METAs e as outras alavancas; não é digitado como alvo.",
        "TBD": "Papel ainda não definido.",
    },
    "ciclo": {
        "TBD": "Valor ainda não definido.",
        "OPEN": "Discussão ativa.",
        "PROPOSED": "Proposta submetida.",
        "APPROVED": "Decisão tomada.",
        "FROZEN": "Baseline do ciclo.",
        "STALE": "Não representa a configuração atual.",
    },
    "congelamento": {
        "F0": ("Aberto; exploração.", "Somente para investigação."),
        "F1": ("Conceito definido.", "Para discussão arquitetural."),
        "F2": ("Especificado.", "Pode ser implementado."),
        "F3": ("Implementado e verificado internamente.", "Pode alimentar análises internas."),
        "F4": ("Congelado para o uso definido.", "Pode ser usado como baseline do ciclo."),
    },
    "coerencia": {
        "COERENTE": "Nenhuma regra avaliada foi violada (vocabulário e sobredeterminação; o efeito no objetivo e a malha "
                    "fechada ficam para o incremento 7, spec §10).",
        "COMPROMISSO DECLARADO": "Há custo declarado, com justificativa e um EDR no formato EDR-ddd (que ele existe e está "
                                 "aprovado é conferido fora da planilha).",
        "CONFLITO": "Impossibilidade (campo fora do vocabulário, duas METAs na mesma alavanca) ou compromisso sem EDR.",
        "NÃO AVALIÁVEL": "Meta sem valor ou papel (TBD): nada foi avaliado; não é \"ok\".",
    },
    "fonte": {
        "L": "Livro e página, conferidos na imagem do PDF.",
        "E": "EDR existente e aprovado.",
        "M": "Cálculo da planilha: nome do resultado e nome da entrada da alavanca; a entrada é raiz do resultado.",
    },
}

SEM_RELACAO = "sem relação na 23_LISTAS"          # o que a coluna Alavanca mostra sem relação (G1)
MOTIVO_NAO_AVALIAVEL = "meta sem valor ou papel (TBD)"
MOTIVO_COERENTE = "regras avaliadas: vocabulário e sobredeterminação"
MOTIVO_SEM_EDR = "compromisso sem EDR"
SEPARADOR = " · "                                # entre o estado e a pior origem (spec §4.4)
PIOR_PRIMEIRO = ("CONFLITO", "NÃO AVALIÁVEL", "COMPROMISSO DECLARADO", "COERENTE")   # pior coerência no dashboard

# Fontes L conferidas na imagem do PDF (references/pdf/; página impressa; 2026-10-23): Gillespie p. 214 (itens 2 a 4: projetistas
# buscam mais rigidez de rolagem na frente para garantir subesterço no limite; barra só atrás pode induzir sobresterço),
# Milliken §7.1, p. 283-286 (análise de par: transferência lateral de carga FLT, diagrama de potencial e curva de
# coeficiente de curva, que mostra o efeito da transferência de carga), Milliken p. 313-315 (§8.5: o subesterço no regime linear
# e o push/loose no limite são situações físicas diferentes e não se confundem; faixa linear de 0 a 0,3-0,4 g).
FONTES_L = ("Gillespie p. 214", "Milliken §7.1, p. 283-286", "Milliken p. 313-315")

ALAVANCA_LAMBDA = "distribuição de rolagem λ_f (barras)"


@dataclass(frozen=True)
class Relacao:
    """Uma linha da tabela de relações (23_LISTAS). `n` é interno (sem prefixo REL-). tipo: alavanca | regime. meta: o ID
    da meta (ou "TARGET-006 × TARGET-007" no regime). fonte_tipo: L | E | M; fonte: o texto da fonte (livro e página, EDR, ou
    "resultado ← entrada" nas linhas M). resultado e entrada: só nas linhas M (nomes definidos da planilha)."""
    n: int
    tipo: str
    meta: str
    alavanca: str
    fonte_tipo: str
    fonte: str
    resultado: str | None
    entrada: str | None


def _m(n: int, meta: str, alavanca: str, resultado: str, entrada: str) -> Relacao:
    return Relacao(n, "alavanca", meta, alavanca, "M", f"{resultado} ← {entrada}", resultado, entrada)


RELACOES: tuple[Relacao, ...] = (
    _m(1, "TARGET-001", "mola dianteira", "res_06_frequencia_natural_dianteira", "ent_06_spring_rate_dianteiro"),
    _m(2, "TARGET-002", "mola traseira", "res_06_frequencia_natural_traseira", "ent_06_spring_rate_traseiro"),
    _m(3, "TARGET-003", ALAVANCA_LAMBDA, "res_06_distribuicao_de_rigidez_dianteira_lambda", "ent_06_k_arb_dianteiro"),
    _m(4, "TARGET-004", "geometria dianteira (anti-dive)", "res_06_anti_dive_fb_f_dz_dx_l_h100_anti_pro_div",
       "ent_07_altura_do_ic_lateral_dianteiro_z_icf"),
    _m(5, "TARGET-005", "geometria traseira (anti-squat)", "res_06_anti_squat_tf_r_dz_dx_l_h100_anti_pro_sq",
       "ent_07_altura_do_ic_lateral_traseiro_z_icr"),
    _m(6, "TARGET-006", ALAVANCA_LAMBDA, "res_16_k_total_em_g", "ent_06_k_arb_dianteiro"),
    _m(7, "TARGET-007", ALAVANCA_LAMBDA, "res_16_veredito_no_limite_push_loose_neutro_ou", "ent_06_k_arb_dianteiro"),
    Relacao(8, "alavanca", "TARGET-006", ALAVANCA_LAMBDA, "L", "Gillespie p. 214", None, None),
    Relacao(9, "alavanca", "TARGET-007", ALAVANCA_LAMBDA, "L", "Milliken §7.1, p. 283-286", None, None),
    Relacao(10, "regime", "TARGET-006 × TARGET-007", "regime linear × limite (informativa)", "L",
            "Milliken p. 313-315", None, None),
)
# Nota de cada linha (23_LISTAS, coluna Nota): o que a relação afirma e, nas linhas L, o que a página diz.
NOTAS_RELACAO: dict[int, str] = {
    1: "Frequência natural dianteira (SUS-205) pela mola dianteira; o 11_DESIGN deriva a mola do alvo de frequência, e o "
       "resultado aqui é a grandeza, a mola é a alavanca.",
    2: "Frequência natural traseira (SUS-205) pela mola traseira.",
    3: "λ_f (SUS-208) pelas barras; a K_ARB dianteira é a alavanca da tabela de troca (20_EQ_TROCA).",
    4: "Anti-dive (SUS-301) pela altura e pelo recuo do centro instantâneo lateral dianteiro (07_KINEMATICS).",
    5: "Anti-squat (SUS-302) pela altura e pelo recuo do centro instantâneo lateral traseiro (07_KINEMATICS).",
    6: "Gradiente de subesterço K (SUS-1001), em °/g, pela distribuição de rolagem.",
    7: "Veredito no limite (SUS-1004: push, loose ou neutro) pela distribuição de rolagem.",
    8: "Mais rigidez de rolagem na frente leva ao subesterço no limite; barra só atrás pode induzir sobresterço (itens 2 a 4 "
       "da p. 214).",
    9: "A análise de par (FLT, diagrama de potencial e curva de coeficiente de curva) mostra o efeito da transferência de "
       "carga entre os eixos na capacidade lateral de cada eixo.",
    10: "Regimes diferentes: o K vale no regime linear e o veredito vale no limite; subesterço linear com loose no limite "
        "não é erro. Informativa, fora das fórmulas.",
}


def alavanca(target: str) -> str | None:
    """Alavanca da meta pela tabela de relações (a primeira linha tipo `alavanca` da meta), ou None sem relação."""
    for r in RELACOES:
        if r.tipo == "alavanca" and r.meta == target:
            return r.alavanca
    return None


@dataclass
class Ficha:
    """Os campos de uma ficha de meta que a coerência lê (03_TARGETS). valor = coluna Target (C); ciclo = Status (D);
    pior_origem = o texto da pior origem da grandeza (coluna L)."""
    target: str
    valor: object
    papel: object
    ciclo: object
    congelamento: object
    compromisso: object
    edr: object
    pior_origem: str


def campo_valido(campo: str, valor) -> bool:
    """O valor está no vocabulário de `campo` (chave de VOCAB)? Exato: só texto idêntico a um valor da lista conta
    (como a fórmula EXACT da planilha); número, vazio, espaço a mais e outra caixa não contam."""
    return isinstance(valor, str) and valor in VOCAB[campo]


_EDR = re.compile(r"EDR-[0-9]{3}")


def edr_no_formato(v) -> bool:
    """`EDR-ddd` exato: texto "EDR-" em maiúsculas e três dígitos, nada mais."""
    return isinstance(v, str) and _EDR.fullmatch(v) is not None


def _texto_celula(v) -> str:
    return "" if v is None else str(v).strip(" ")


def valor_tbd(valor) -> bool:
    """Target vazio ou TBD (qualquer caixa, espaços nas pontas ignorados). O número 0 é um valor."""
    t = _texto_celula(valor)
    return t == "" or t.upper() == "TBD"


def compromisso_preenchido(v) -> bool:
    """Compromisso declarado preenchido: texto não vazio e diferente de TBD."""
    return not valor_tbd(v)


def sobredeterminadas(fichas: list[Ficha]) -> set[str]:
    """IDs das metas com Papel = META (exato) cuja alavanca tem outra META (spec §5, itens 1b e 2). Meta sem relação
    nunca é sobredeterminada. É a única definição da regra (`estado_coerencia` a usa) e conta metas distintas, por ID:
    a própria ficha nunca é "outra" META."""
    por_alavanca: dict[str, set[str]] = {}
    for f in fichas:
        a = alavanca(f.target)
        if a is not None and f.papel == "META":
            por_alavanca.setdefault(a, set()).add(f.target)
    return {t for ids in por_alavanca.values() if len(ids) > 1 for t in ids}


def estado_coerencia(f: Ficha, fichas: list[Ficha]) -> tuple[str, str]:
    """(estado, motivo) da ficha `f` entre as `fichas` (que incluem `f`), pela ordem de regras do módulo. O motivo é
    vazio em COMPROMISSO DECLARADO."""
    for chave, nome in CAMPOS_VOCAB:
        if not campo_valido(chave, getattr(f, chave)):
            return "CONFLITO", f"{nome} fora do vocabulário"
    if f.target in sobredeterminadas(fichas):
        return "CONFLITO", f"sobredeterminação ({alavanca(f.target)}; escolha qual manda)"
    if f.papel == "TBD" or valor_tbd(f.valor):
        return "NÃO AVALIÁVEL", MOTIVO_NAO_AVALIAVEL
    if compromisso_preenchido(f.compromisso):
        return ("COMPROMISSO DECLARADO", "") if edr_no_formato(f.edr) else ("CONFLITO", MOTIVO_SEM_EDR)
    return "COERENTE", MOTIVO_COERENTE


def _texto_estado(estado: str, motivo: str) -> str:
    if estado == "COERENTE":
        return f"COERENTE ({motivo})"
    return f"{estado}: {motivo}" if motivo else estado


def texto_coerencia(f: Ficha, fichas: list[Ficha]) -> str:
    """Texto exato da coluna Coerência (G5): `<estado>[: motivo] · <pior origem da grandeza>`."""
    estado, motivo = estado_coerencia(f, fichas)
    return f"{_texto_estado(estado, motivo)}{SEPARADOR}{f.pior_origem}"


def pior_coerencia(textos: list[str]) -> str:
    """Pior estado entre os textos de coerência (CONFLITO > NÃO AVALIÁVEL > COMPROMISSO DECLARADO > COERENTE). Lista
    vazia: NÃO AVALIÁVEL (nada foi avaliado). Texto que não começa por um estado é erro."""
    for t in textos:
        if not any(t.startswith(e) for e in PIOR_PRIMEIRO):
            raise ValueError(f"texto de coerência sem estado conhecido: {t!r}")
    for e in PIOR_PRIMEIRO:
        if any(t.startswith(e) for t in textos):
            return e
    return "NÃO AVALIÁVEL"


def compromissos(textos: list[str]) -> int:
    """Quantos textos de coerência são COMPROMISSO DECLARADO."""
    return sum(t.startswith("COMPROMISSO DECLARADO") for t in textos)
