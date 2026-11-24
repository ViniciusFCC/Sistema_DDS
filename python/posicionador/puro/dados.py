"""Leitura de hardpoints em CSV (schema V2.0) para o núcleo puro: {id: (xyz, componente)} em metros."""
import csv
import math


def carregar_hardpoints(caminho):
    pts = {}
    with open(caminho, encoding="utf-8", newline="") as f:
        for lin in csv.DictReader(f):
            xyz = (float(lin["X_m"]), float(lin["Y_m"]), float(lin["Z_m"]))
            if not all(math.isfinite(c) for c in xyz):
                raise ValueError(f"coordenada não finita em {lin['Point_ID']}")
            if lin["Point_ID"] in pts:
                raise ValueError(f"ponto repetido: {lin['Point_ID']}")
            pts[lin["Point_ID"]] = (xyz, lin["Component"])
    return pts
