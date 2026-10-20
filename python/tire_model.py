"""
tire_model_V2_2.py — SUS-501 (Fy), SUS-502 (Fx), SUS-503 (mu_eff). Engineering Standard V2.0 + EDR-015.

Natureza: CONSUMO de um dataset .tir (REFERENCE, DR-011) — sem ajuste (fit) próprio. Este módulo implementa
a AVALIAÇÃO das equações da Magic Formula formato PAC2002/MF 5.2 (sem pressão, sem momentos, sem relaxamento),
escopo estacionário: Fx, Fy puros e combinados, com os coeficientes do arquivo.

HIPÓTESES (rotuladas; nenhuma fonte primária foi consultada nesta etapa):
 H1  Equações de Fx0/Fy0 e de combinação (Gxa, Gyk, SVyk) na forma MF 5.2 reproduzida de memória do formato
     publicado (Pacejka; documentação Adams/PAC2002). NÃO verificadas contra implementação independente
     (não há pacote disponível no ambiente). Verificação disponível: limites analíticos (test_tire_model_V2_2.py).
 H2  Pressão: dpi = 0 (IP = IP_NOM) e coeficientes PP* = 0 -> termos de pressão omitidos; o loader REJEITA
     o arquivo se IP != IP_NOM ou algum PP* != 0.
 H3  Sistema de eixos do arquivo: o .tir provisório é PAC2002 do Adams e os parâmetros dele valem no eixo W do TYDEX
     (orientação ISO; help do Adams 2024.1, PAC2002, p. 7): declarado ISO_TYDEX (EDR-039 reaberto, 2026-10-19;
     convention_status = CONFIRMED, pela documentação do formato). Até a V2.4 era declarado SAE_CALSPAN (usuário; tese UNCC 2015 como fonte secundária).
     O modo SAE_CALSPAN continua disponível para dado bruto em SAE.
 H3b Modo SAE_CALSPAN (alternativo) -> ISO 8855 (pneu direito): alpha_file = -alpha_ISO; Fy_ISO = -Fy_file; Fx e kappa iguais;
     camber: gamma_file = -gamma_proj (INFERÊNCIA: o empuxo de camber aponta para o lado da inclinação; o sinal de IA do TTC
     NÃO foi verificado; os termos de camber do arquivo dão Fy_file<0 para gamma_file>0). O .tir tem Fz positivo
     (o dado bruto TTC é negativo): o arquivo passou por processamento; não se sabe se outros sinais foram convertidos.
 H4  Espelhamento para rodas esquerdas (arquivo é TYRESIDE='Right'): aplicado ANTES da transformação de eixos:
     alpha_R = -alpha_L, Fy_L = -Fy_R_ISO; camber do projeto (+ = topo para fora) entra igual nos dois lados.
 Modo 'ISO_TYDEX' (arquivo já em ISO): transformação identidade. Sistema 'UNKNOWN' ou não declarado: dataset REJEITADO.
Dados: o .tir de teste NÃO corresponde necessariamente ao pneu que será usado (usuário, 2026-10-12).
"""
import math
import re
from dataclasses import dataclass, field

__version__ = "V3.0"
EPS = 1e-6


class TireDataError(ValueError):
    """Dataset inválido ou não suportado (mensagem indica a causa)."""


class TireRangeError(ValueError):
    """Ponto de operação fora da faixa de validade do dataset (não extrapola em silêncio)."""


_ASSIGN = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*([^$!]*)")


def parse_tir(path):
    """Lê um .tir (MDI) e devolve (params, strings). Só 'KEY = valor' numérico ou 'texto'. Ignora tabelas {…}."""
    params, strings = {}, {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.lstrip().startswith(("$", "!", "{")):
                continue
            m = _ASSIGN.match(line)
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("'"):
                strings[key] = val.strip("'").strip()
                continue
            try:
                params[key] = float(val.split()[0])
            except (ValueError, IndexError):
                strings[key] = val
    return params, strings


REQUIRED = ["FNOMIN", "KPUMIN", "KPUMAX", "ALPMIN", "ALPMAX", "CAMMIN", "CAMMAX", "FZMIN", "FZMAX", "IP", "IP_NOM",
            "LFZO", "LCX", "LMUX", "LEX", "LKX", "LHX", "LVX", "LGAX", "LCY", "LMUY", "LEY", "LKY", "LHY", "LVY", "LGAY",
            "LXAL", "LYKA", "LVYKA", "LKYG",
            "PCX1", "PDX1", "PDX2", "PDX3", "PEX1", "PEX2", "PEX3", "PEX4", "PKX1", "PKX2", "PKX3", "PHX1", "PHX2",
            "PVX1", "PVX2", "RBX1", "RBX2", "RCX1", "REX1", "REX2", "RHX1",
            "PCY1", "PDY1", "PDY2", "PDY3", "PEY1", "PEY2", "PEY3", "PEY4", "PKY1", "PKY2", "PKY3", "PHY1", "PHY2",
            "PHY3", "PVY1", "PVY2", "PVY3", "PVY4", "RBY1", "RBY2", "RBY3", "RCY1", "REY1", "REY2", "RHY1", "RHY2",
            "RVY1", "RVY2", "RVY3", "RVY4", "RVY5", "RVY6"]
PRESSURE_KEYS = ["PPX1", "PPX2", "PPX3", "PPX4", "PPY1", "PPY2", "PPY3", "PPY4"]


# (s_alpha, s_Fy, s_gamma): alpha_file = s_alpha*alpha_ISO ; Fy_ISO = s_Fy*Fy_file ; gamma_file = s_gamma*gamma_ISO  (pneu direito)
AXIS_TRANSFORMS = {
    "SAE_CALSPAN": (-1.0, -1.0, -1.0),   # H3b (s_gamma é inferência)
    "ISO_TYDEX": (1.0, 1.0, 1.0),
}


@dataclass
class TireDataset:
    p: dict
    strings: dict = field(default_factory=dict)
    source: str = ""
    axis_system: str = "ISO_TYDEX"                        # evita transformação implícita em usos diretos de combined_forces
    convention_status: str = "USER_ASSERTED"              # H3

    @property
    def side(self):
        return self.strings.get("TYRESIDE", "UNKNOWN")


def load_dataset(path, source="", source_axis_system=None):
    p, s = parse_tir(path)
    missing = [k for k in REQUIRED if k not in p]
    if missing:
        raise TireDataError(f"coeficientes ausentes: {missing}")
    if s.get("PROPERTY_FILE_FORMAT") not in ("PAC2002", "MF_05", "MF5.2"):
        raise TireDataError(f"PROPERTY_FILE_FORMAT={s.get('PROPERTY_FILE_FORMAT')!r} não suportado (só PAC2002/MF 5.2-like).")
    if s.get("LENGTH") != "meter" or s.get("FORCE") != "newton" or s.get("ANGLE") != "radians":
        raise TireDataError(f"unidades do arquivo {s.get('LENGTH')}/{s.get('FORCE')}/{s.get('ANGLE')} != meter/newton/radians.")
    if p["IP"] != p["IP_NOM"] or any(p.get(k, 0.0) != 0.0 for k in PRESSURE_KEYS):
        raise TireDataError("pressão: IP != IP_NOM ou PP* != 0 — efeitos de pressão não implementados (H2).")
    if source_axis_system not in AXIS_TRANSFORMS:
        raise TireDataError(f"sistema de eixos do arquivo não declarado/desconhecido ({source_axis_system!r}); use um de {sorted(AXIS_TRANSFORMS)}.")
    if s.get("TYRESIDE") not in ("Right", "Left"):
        raise TireDataError("TYRESIDE ausente/desconhecido: convenção de lado não determinada.")
    if p["FNOMIN"] <= 0 or p["FZMIN"] <= 0 or p["FZMAX"] <= p["FZMIN"]:
        raise TireDataError("FNOMIN/FZMIN/FZMAX inconsistentes (Fz deve ser positivo).")
    return TireDataset(p=p, strings=s, source=source, axis_system=source_axis_system)


def in_range(ds, fz, alpha, gamma, kappa):
    """Lista de violações de faixa (vazia = dentro). alpha, gamma em rad; kappa adimensional; Fz em N (>0 = carga)."""
    p, out = ds.p, []
    if not all(math.isfinite(x) for x in (fz, alpha, gamma, kappa)):
        return ["valor não finito"]
    if fz <= 0:
        out.append(f"Fz={fz:.1f} N <= 0 (perda de contato; fora do domínio)")
    elif not (p["FZMIN"] <= fz <= p["FZMAX"]):
        out.append(f"Fz={fz:.1f} N fora de [{p['FZMIN']:.0f}, {p['FZMAX']:.0f}]")
    if not (p["ALPMIN"] <= alpha <= p["ALPMAX"]):
        out.append(f"alpha={math.degrees(alpha):.2f}° fora de [{math.degrees(p['ALPMIN']):.1f}, {math.degrees(p['ALPMAX']):.1f}]")
    if not (p["CAMMIN"] <= gamma <= p["CAMMAX"]):
        out.append(f"camber={math.degrees(gamma):.2f}° fora de [{math.degrees(p['CAMMIN']):.1f}, {math.degrees(p['CAMMAX']):.1f}]")
    if not (p["KPUMIN"] <= kappa <= p["KPUMAX"]):
        out.append(f"kappa={kappa:.3f} fora de [{p['KPUMIN']}, {p['KPUMAX']}]")
    return out


def _sgn(x):
    return (x > 0) - (x < 0)


def _mf(B, C, D, E, x):
    return D * math.sin(C * math.atan(B * x - E * (B * x - math.atan(B * x))))


def pure_fx0(p, fz, gamma, kappa):
    fz0 = p["LFZO"] * p["FNOMIN"]
    dfz = (fz - fz0) / fz0
    gx = gamma * p["LGAX"]
    SHx = (p["PHX1"] + p["PHX2"] * dfz) * p["LHX"]
    kx = kappa + SHx
    Cx = p["PCX1"] * p["LCX"]
    mux = (p["PDX1"] + p["PDX2"] * dfz) * (1.0 - p["PDX3"] * gx * gx) * p["LMUX"]
    Dx = mux * fz
    Ex = min((p["PEX1"] + p["PEX2"] * dfz + p["PEX3"] * dfz ** 2) * (1.0 - p["PEX4"] * _sgn(kx)) * p["LEX"], 1.0)
    Kx = fz * (p["PKX1"] + p["PKX2"] * dfz) * math.exp(p["PKX3"] * dfz) * p["LKX"]
    Bx = Kx / (Cx * Dx + EPS)
    SVx = fz * (p["PVX1"] + p["PVX2"] * dfz) * p["LVX"] * p["LMUX"]
    return _mf(Bx, Cx, Dx, Ex, kx) + SVx, {"Kx": Kx, "Dx": Dx, "SHx": SHx, "SVx": SVx, "Bx": Bx, "Cx": Cx, "Ex": Ex}


def pure_fy0(p, fz, alpha, gamma):
    fz0 = p["LFZO"] * p["FNOMIN"]
    dfz = (fz - fz0) / fz0
    gy = gamma * p["LGAY"]
    # EDR-049: um único λFz0 (via F'z0 = LFZO·FNOMIN), como Pacejka (2006) eq. 4.E25 e Seward eq. 5.9; a forma do Racer tinha um segundo
    Ky = p["PKY1"] * fz0 * math.sin(2.0 * math.atan(fz / (p["PKY2"] * fz0))) * (1.0 - p["PKY3"] * abs(gy)) * p["LKY"]
    SHy = (p["PHY1"] + p["PHY2"] * dfz) * p["LHY"] + p["PHY3"] * gy * p["LKYG"]   # λKyγ: Adams PAC2002 eq. 41-42 (EDR-042)
    ay = alpha + SHy
    Cy = p["PCY1"] * p["LCY"]
    muy = (p["PDY1"] + p["PDY2"] * dfz) * (1.0 - p["PDY3"] * gy * gy) * p["LMUY"]
    Dy = muy * fz
    Ey = min((p["PEY1"] + p["PEY2"] * dfz) * (1.0 - (p["PEY3"] + p["PEY4"] * gy) * _sgn(ay)) * p["LEY"], 1.0)
    By = Ky / (Cy * Dy + EPS)
    SVy = fz * ((p["PVY1"] + p["PVY2"] * dfz) * p["LVY"] + (p["PVY3"] + p["PVY4"] * dfz) * gy * p["LKYG"]) * p["LMUY"]
    return _mf(By, Cy, Dy, Ey, ay) + SVy, {"Ky": Ky, "Dy": Dy, "SHy": SHy, "SVy": SVy, "By": By, "Cy": Cy, "Ey": Ey, "muy": muy}


def combined_forces(ds, fz, alpha, gamma, kappa, check_range=True):
    """Fx, Fy no referencial do PRÓPRIO dataset (pneu 'Right' do arquivo, convenção do arquivo). Sem espelhamento."""
    if check_range:
        v = in_range(ds, fz, alpha, gamma, kappa)
        if v:
            raise TireRangeError("; ".join(v))
    p = ds.p
    fz0 = p["LFZO"] * p["FNOMIN"]
    dfz = (fz - fz0) / fz0
    fx0, ix = pure_fx0(p, fz, gamma, kappa)
    fy0, iy = pure_fy0(p, fz, alpha, gamma)
    # Fx combinado: Gxa
    SHxa = p["RHX1"]
    Bxa = p["RBX1"] * math.cos(math.atan(p["RBX2"] * kappa)) * p["LXAL"]
    Cxa = p["RCX1"]
    Exa = min(p["REX1"] + p["REX2"] * dfz, 1.0)
    a_s = alpha + SHxa
    def g(x):
        return math.cos(Cxa * math.atan(Bxa * x - Exa * (Bxa * x - math.atan(Bxa * x))))
    Gxa = g(a_s) / g(SHxa)
    # Fy combinado: Gyk e SVyk
    SHyk = p["RHY1"] + p["RHY2"] * dfz
    Byk = p["RBY1"] * math.cos(math.atan(p["RBY2"] * (alpha - p["RBY3"]))) * p["LYKA"]
    Cyk = p["RCY1"]
    Eyk = min(p["REY1"] + p["REY2"] * dfz, 1.0)
    k_s = kappa + SHyk
    def gk(x):
        return math.cos(Cyk * math.atan(Byk * x - Eyk * (Byk * x - math.atan(Byk * x))))
    Gyk = gk(k_s) / gk(SHyk)
    DVyk = iy["muy"] * fz * (p["RVY1"] + p["RVY2"] * dfz + p["RVY3"] * gamma) * math.cos(math.atan(p["RVY4"] * alpha))
    SVyk = DVyk * math.sin(p["RVY5"] * math.atan(p["RVY6"] * kappa)) * p["LVYKA"]
    return Gxa * fx0, Gyk * fy0 + SVyk, {"fx0": fx0, "fy0": fy0, "Gxa": Gxa, "Gyk": Gyk, "SVyk": SVyk, **ix, **iy}


def wheel_forces(ds, corner, fz, alpha, gamma, kappa):
    """SUS-501/502 por canto na convenção do PROJETO (ISO 8855): alpha em ISO (+ = velocidade p/ esquerda; rad), gamma do projeto
    (+ = topo para fora), kappa (ISO). Retorna Fx, Fy_proj (ISO), info. Ordem: espelhamento (rodas L) -> transformação de eixos do arquivo."""
    if corner not in ("FL", "FR", "RL", "RR"):
        raise ValueError("corner deve ser FL/FR/RL/RR")
    s_a, s_f, s_g = AXIS_TRANSFORMS[ds.axis_system]
    left = corner.endswith("L")
    a_right = -alpha if left else alpha
    fx, fy_file, info = combined_forces(ds, fz, s_a * a_right, s_g * gamma, kappa)
    fy_right_iso = s_f * fy_file
    return fx, (-fy_right_iso if left else fy_right_iso), info


def mu_effective(fx, fy, fz):
    """SUS-503: mu_eff = sqrt(Fx^2+Fy^2)/Fz. Fz<=0 é bloqueado."""
    if not (fz > 0 and math.isfinite(fz)):
        raise ValueError("SUS-503: Fz deve ser > 0.")
    return math.hypot(fx, fy) / fz


def sign_report(ds, fz=None):
    """Sinais EMPÍRICOS no referencial DO ARQUIVO (avaliação direta, sem transformação)."""
    fz = fz or ds.p["FNOMIN"]
    r = {}
    r["Fy(alpha=+4deg, gamma=0, kappa=0)"] = combined_forces(ds, fz, math.radians(4), 0.0, 0.0)[1]
    r["Fy(alpha=0, gamma=+3deg, kappa=0)"] = combined_forces(ds, fz, 0.0, math.radians(3), 0.0)[1]
    r["Fx(kappa=+0.10)"] = combined_forces(ds, fz, 0.0, 0.0, 0.10)[0]
    r["Fx(kappa=-0.10)"] = combined_forces(ds, fz, 0.0, 0.0, -0.10)[0]
    return r


def project_sign_report(ds, fz=None):
    """Sinais na convenção do PROJETO (ISO, roda direita, camber + = topo para fora) após a transformação do arquivo."""
    fz = fz or ds.p["FNOMIN"]
    r = {}
    r["Fy_ISO(alpha_ISO=+4deg)"] = wheel_forces(ds, "FR", fz, math.radians(4), 0.0, 0.0)[1]
    r["Fy_ISO(gamma=+3deg topo p/ fora)"] = wheel_forces(ds, "FR", fz, 0.0, math.radians(3), 0.0)[1]
    r["Fy_ISO(alpha=0, gamma=0, kappa=0)"] = wheel_forces(ds, "FR", fz, 0.0, 0.0, 0.0)[1]
    r["Fx(kappa=-0.10)"] = wheel_forces(ds, "FR", fz, 0.0, 0.0, -0.10)[0]
    return r
