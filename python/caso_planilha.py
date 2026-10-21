"""Caso de equilíbrio demonstrativo lido da planilha V3.0 e a pior origem dos dados (V4.0, incremento 1).

`caso_da_planilha` lê as entradas de uma CÓPIA já recalculada (Excel ou LibreOffice, EDR-044) e monta o
`CasoEquilibrio`. `pior_origem_do_caso` abre a planilha SEM valores (só fórmulas) e acha o pior rótulo de origem
entre as raízes das entradas e o pneu (origem lida da 10_TIRE, I84); `pior_origem_entradas` faz o mesmo sem o
pneu. Nenhuma função salva ou recalcula a planilha; a viva só é aberta para leitura.

ENTRADAS_CASO é uma cópia consciente do `ENTRADAS` de tests/test_workbook_suspensao.py (só as chaves usadas aqui).
O incremento 3 troca as duas pelos nomes definidos da planilha.
Toe, camber estático e ganho de camber ficam em 0: não há dado do carro (EDR-036).
"""
from __future__ import annotations

import math
import warnings
from pathlib import Path

import openpyxl

import suspension_model as sm
import tire_model as tm
from equilibrio import CasoEquilibrio
from raizes import Grafo, origem_da_raiz, PIOR_PRIMEIRO, SEM_ROTULO
from atualizar_planilha import CONF

ENTRADAS_CASO: dict[str, tuple[str, str]] = {
    "m": ("05_VEHICLE", "B4"), "h": ("05_VEHICLE", "B5"), "L": ("05_VEHICLE", "B6"),
    "tF": ("05_VEHICLE", "B7"), "tR": ("05_VEHICLE", "B8"), "a": ("05_VEHICLE", "B9"), "b": ("05_VEHICLE", "B10"),
    "muF": ("05_VEHICLE", "B14"), "muR": ("05_VEHICLE", "B15"), "huF": ("05_VEHICLE", "B16"), "huR": ("05_VEHICLE", "B17"),
    "KsF": ("06_SUSPENSION", "B4"), "KsR": ("06_SUSPENSION", "B5"), "MRF": ("06_SUSPENSION", "B6"),
    "MRR": ("06_SUSPENSION", "B7"), "KarbF": ("06_SUSPENSION", "B10"), "KarbR": ("06_SUSPENSION", "B11"),
    "zF": ("06_SUSPENSION", "B14"), "zR": ("06_SUSPENSION", "B15"),
    "KTF": ("06_SUSPENSION", "B47"), "KTR": ("06_SUSPENSION", "B48"),
    "DF": ("08_VEHICLE_STATE", "B8"), "bal": ("08_VEHICLE_STATE", "B9"),
}


def caso_da_planilha(xlsx_recalculado: Path, tir: Path) -> CasoEquilibrio:
    """Monta o CasoEquilibrio a partir de uma cópia recalculada; ValueError se alguma entrada não tem valor."""
    wb = openpyxl.load_workbook(xlsx_recalculado, data_only=True)
    x: dict[str, float] = {}
    for nome, (aba, cel) in ENTRADAS_CASO.items():
        v = wb[aba][cel].value
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError("a cópia precisa ser recalculada (Excel ou LibreOffice) antes da leitura: "
                             f"{aba}!{cel} sem valor")
        x[nome] = float(v)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kw_f, kw_r = sm.wheel_rate(x["KsF"], x["MRF"]), sm.wheel_rate(x["KsR"], x["MRR"])
    kphi_f = sm.roll_stiffness_axle(kw_f, x["tF"], x["KarbF"], x["KTF"])
    kphi_r = sm.roll_stiffness_axle(kw_r, x["tR"], x["KarbR"], x["KTR"])
    cfg = sm.VehicleConfig(
        mass_total=x["m"], cg_height=x["h"], wheelbase=x["L"], track_front=x["tF"], track_rear=x["tR"],
        cg_to_front=x["a"], cg_to_rear=x["b"], unsprung_mass_front=x["muF"], unsprung_mass_rear=x["muR"],
        unsprung_cg_height_front=x["huF"], unsprung_cg_height_rear=x["huR"], roll_center_front=x["zF"],
        roll_center_rear=x["zR"], roll_stiffness_front=kphi_f, roll_stiffness_rear=kphi_r)
    ds = tm.load_dataset(str(tir), source="caso da planilha", source_axis_system="ISO_TYDEX")
    return CasoEquilibrio(cfg, ds, downforce_N=x["DF"], aero_balance_front=x["bal"])


def _origens_entradas(wb) -> set[str]:
    """Rótulos de origem das raízes preenchidas de ENTRADAS_CASO (raiz sem rótulo conta como "? A confirmar")."""
    grafo = Grafo(wb)
    achados = set()
    for no in ENTRADAS_CASO.values():
        for aba, cel in grafo.raizes_preenchidas(no):
            rotulo = origem_da_raiz(wb, aba, cel)
            achados.add(CONF if rotulo == SEM_ROTULO else rotulo)
    return achados


def _origem_pneu(wb) -> str:
    """Origem do pneu na própria planilha: a célula de origem dos coeficientes do .tir na 10_TIRE
    (raizes.celula_origem("10_TIRE", "B86") → I84). Sem rótulo conta como "? A confirmar"."""
    rotulo = origem_da_raiz(wb, "10_TIRE", "B86")   # lê raizes.celula_origem("10_TIRE", "B86"), a I84
    return CONF if rotulo == SEM_ROTULO else rotulo


def pior_origem_entradas(xlsx_formulas: Path) -> str:
    """Pior rótulo de origem (ordem de raizes.PIOR_PRIMEIRO) entre as raízes das entradas, sem o pneu.

    Abre a planilha só para leitura, sem data_only. Raiz sem rótulo conta como "? A confirmar".
    """
    wb = openpyxl.load_workbook(xlsx_formulas, data_only=False)
    achados = _origens_entradas(wb)
    if not achados:
        raise ValueError("nenhuma raiz preenchida nas entradas do caso: a pior origem não está definida")
    return min(achados, key=PIOR_PRIMEIRO.index)


def pior_origem_do_caso(xlsx_formulas: Path) -> str:
    """Pior rótulo de origem (ordem de raizes.PIOR_PRIMEIRO) entre as raízes das entradas e o pneu.

    A origem do pneu é lida da célula de origem dos coeficientes na 10_TIRE (I84), não de uma constante: se a equipe
    trocar o .tir e o rótulo, o caso acompanha. Abre a planilha só para leitura, sem data_only. Raiz sem rótulo conta
    como "? A confirmar".
    """
    wb = openpyxl.load_workbook(xlsx_formulas, data_only=False)
    achados = _origens_entradas(wb) | {_origem_pneu(wb)}
    return min(achados, key=PIOR_PRIMEIRO.index)
