"""
Rótulos de Origem da V4.2 (EDR-062): o projeto atual é o T11, não o TX.

A lista continua com 6 rótulos nas mesmas posições da V4.1 (as fórmulas de pior origem usam o índice na lista,
`IFERROR(MATCH(...,Origens,0),6)`, e as cores usam o símbolo). Mudam só os dois primeiros:
posição 1 `● Dado do TX` -> `● Dado do T11`; posição 2 `◐ Dado do T09` -> `◐ Dado de outro carro (TX, T09)`.

Duas substituições diferentes, nunca misturadas:
- dado (célula de Origem e coluna oculta H): TX e T09 viram OUTRO_CARRO (MAPA_DADO_V41_V42);
- regra (texto explicativo e o literal do D16): TX vira T11 (MAPA_REGRA_V41_V42).

Os rótulos da V4.1 ficam aqui (TX_V41, T09_V41) para quem lê ou testa a V4.1. Nada em `atualizar_planilha`
muda: ele regenera as V3.0 a V4.1 (CA-07).
"""

from __future__ import annotations

from atualizar_planilha import ARB, CONF, EST, SIGNIFICADO, TTC

TX_V41 = "● Dado do TX"
T09_V41 = "◐ Dado do T09"
T11 = "● Dado do T11"
OUTRO_CARRO = "◐ Dado de outro carro (TX, T09)"

ORIGENS_V42 = (T11, OUTRO_CARRO, TTC, EST, ARB, CONF)

MAPA_DADO_V41_V42 = {TX_V41: OUTRO_CARRO, T09_V41: OUTRO_CARRO}
MAPA_REGRA_V41_V42 = {TX_V41: T11}

# rótulo -> (significado para quem preenche, categorias da auditoria V2.1 e tier); os quatro últimos são os da V4.1
SIGNIFICADO_V42: dict[str, tuple[str, str]] = {
    T11: ("Medido no T11 ou tirado de documento do projeto T11.",
          "T3_FONTE_TX_REGISTRADA (T3), aplicada ao T11 (EDR-062)"),
    OUTRO_CARRO: ("Valor de um carro anterior (TX/E05 ou T09/E03; diga qual na Fonte): serve de referência, "
                  "não é o T11.",
                  "REAL_OUTRO_VEICULO_T09/E03 (T2), também para o TX/E05 (EDR-062)"),
    TTC: SIGNIFICADO[TTC],
    EST: SIGNIFICADO[EST],
    ARB: SIGNIFICADO[ARB],
    CONF: SIGNIFICADO[CONF],
}
