"""
Suspension & Vehicle Dynamics Model — FSAE EV
Implementa as fichas do Engineering Standard V2.0 (SUS-000 a SUS-208, SUS-701/702).

V3.0 (revisão metodológica contra Milliken, Gillespie e Seward; docs/revisao-metodologica.md):
  EDR-045 pneu em série na frequência (SUS-205, via ride rate SUS-212) e na rigidez de rolagem (SUS-206/207);
  EDR-046 termo gravitacional da rolagem em SUS-103; EDR-047 massa suspensa por eixo exata e CG suspenso em a_s.
  Os valores mudam em relação à V2.1 (intencional; a V1.0 congelada fica em tests/regressao/).
V2.1: cross-check de MR [wheel/spring] contra MR geométrico/de referência (mr_crosscheck). O comportamento do limiar
absoluto MR_WARN_THRESHOLD NÃO foi alterado (decisão pendente, EDR-027).
V2.0: validação de entradas (bloqueios do Guide, Apêndice D.2) e aviso de plausibilidade para Fz<0 (SUS-104; Guide D.4).
Os valores de retorno das funções para entradas válidas são idênticos aos da V1.0 (verificado em test_suspension_model_V2_0.py).

Referência: Milliken & Milliken, Race Car Vehicle Dynamics.
Convenção de sinal: ISO 8855 (X-frente, Y-esquerda, Z-cima).
"""

from dataclasses import dataclass, fields
import math
import warnings

__version__ = "V3.0"

# HIPÓTESE (sem fonte no projeto): abaixo deste MR emite aviso. O Guide (D.2) pede o teste de fronteira "MR muito pequeno"
# mas não define o limite. Revisar com dado real da equipe.
MR_WARN_THRESHOLD = 0.2


class FzLiftoffWarning(UserWarning):
    """Fz negativo em algum canto: perda de contato; o modelo linear (SUS-104) não deve ser extrapolado."""


class SmallMotionRatioWarning(UserWarning):
    """MR abaixo de MR_WARN_THRESHOLD: wheel rate muito sensível ao MR (K_w = K_s/MR^2)."""


def _req(cond, msg):
    if not cond:
        raise ValueError(msg)

G = 9.81  # m/s^2


@dataclass
class VehicleConfig:
    """Inputs de veículo (Bloco A do Engineering Standard)."""
    mass_total: float                  # SUS-001 [kg], inclui piloto
    cg_height: float                   # SUS-002 [m], acima do solo (SUS-000 já aplicado)
    wheelbase: float                   # SUS-003 [m]
    track_front: float                 # SUS-004 [m]
    track_rear: float                  # SUS-005 [m]
    cg_to_front: float                 # SUS-006 "a" [m]
    cg_to_rear: float                  # SUS-006 "b" [m]
    unsprung_mass_front: float         # SUS-007 [kg], ambas as rodas
    unsprung_mass_rear: float          # SUS-008 [kg], ambas as rodas
    unsprung_cg_height_front: float    # SUS-010 [m]
    unsprung_cg_height_rear: float     # SUS-011 [m]
    roll_center_front: float           # SUS-401-F [m], REFERENCE (OptimumKinematics)
    roll_center_rear: float            # SUS-401-R [m], REFERENCE (OptimumKinematics)
    roll_stiffness_front: float        # SUS-206 [N*m/rad]
    roll_stiffness_rear: float         # SUS-207 [N*m/rad]

    def __post_init__(self):
        for f in fields(self):
            v = getattr(self, f.name)
            _req(isinstance(v, (int, float)) and math.isfinite(v), f"{f.name}: valor deve ser número finito (recebido {v!r}).")
        _req(self.mass_total > 0, "SUS-001 mass_total deve ser > 0 (massa zero é bloqueada). Corrija a entrada de massa.")
        _req(self.cg_height > 0, "SUS-002 cg_height deve ser > 0 (altura acima do solo, SUS-000).")
        _req(self.wheelbase > 0, "SUS-003 wheelbase deve ser > 0 (L zero é bloqueado).")
        _req(self.track_front > 0, "SUS-004 track_front deve ser > 0.")
        _req(self.track_rear > 0, "SUS-005 track_rear deve ser > 0.")
        _req(self.cg_to_front > 0 and self.cg_to_rear > 0, "SUS-006 cg_to_front (a) e cg_to_rear (b) devem ser > 0.")
        _req(self.unsprung_mass_front >= 0 and self.unsprung_mass_rear >= 0, "SUS-007/008 massas não-suspensas devem ser >= 0.")
        _req(self.mass_total - self.unsprung_mass_front - self.unsprung_mass_rear > 0,
             "SUS-009 massa suspensa total <= 0: massas não-suspensas (SUS-007/008) maiores ou iguais à massa total (SUS-001).")
        _req(self.unsprung_cg_height_front >= 0 and self.unsprung_cg_height_rear >= 0, "SUS-010/011 alturas não-suspensas devem ser >= 0.")
        _req(self.roll_stiffness_front >= 0 and self.roll_stiffness_rear >= 0
             and (self.roll_stiffness_front + self.roll_stiffness_rear) > 0,
             "SUS-206/207 rigidezes de rolagem devem ser >= 0 com soma > 0.")
        if abs((self.cg_to_front + self.cg_to_rear) - self.wheelbase) > 1e-6:
            raise ValueError(
                f"SUS-006 inconsistente com SUS-003: a+b={self.cg_to_front + self.cg_to_rear} "
                f"!= L={self.wheelbase}"
            )
        ms = self.mass_total - self.unsprung_mass_front - self.unsprung_mass_rear
        hs = (self.mass_total * self.cg_height - self.unsprung_mass_front * self.unsprung_cg_height_front
              - self.unsprung_mass_rear * self.unsprung_cg_height_rear) / ms
        _req(hs > 0, f"SUS-012 h_s={hs:.4f} m <= 0: inconsistência entre SUS-002, 007, 008, 010 e 011 (CG suspenso abaixo do solo).")
        msF = self.mass_total * self.cg_to_rear / self.wheelbase - self.unsprung_mass_front
        msR = self.mass_total * self.cg_to_front / self.wheelbase - self.unsprung_mass_rear
        _req(msF > 0 and msR > 0, f"SUS-009 massa suspensa por eixo <= 0 (F={msF:.2f} kg, R={msR:.2f} kg): "
                                  "a massa não suspensa de um eixo passa do peso estático desse eixo.")


# ---------- SUS-009 / SUS-012 : massa suspensa e altura do CG suspenso ----------

def sprung_mass_total(cfg: VehicleConfig) -> float:
    """SUS-009, primeira etapa: massa suspensa total."""
    return cfg.mass_total - cfg.unsprung_mass_front - cfg.unsprung_mass_rear


def sprung_mass_axle(cfg: VehicleConfig) -> dict:
    """SUS-009 por eixo (EDR-047): m_s,F = m·b/L − m_uF; m_s,R = m·a/L − m_uR
    (Milliken p. 601, Tab. 16.3; Seward eq. 5.14). Hipótese: CG não suspenso sobre o eixo."""
    L = cfg.wheelbase
    return {"front": cfg.mass_total * cfg.cg_to_rear / L - cfg.unsprung_mass_front,
            "rear": cfg.mass_total * cfg.cg_to_front / L - cfg.unsprung_mass_rear}


def sprung_cg_to_front(cfg: VehicleConfig) -> float:
    """a_s: distância do CG suspenso ao eixo dianteiro, a_s = L·m_s,R/m_s (Milliken p. 603)."""
    return cfg.wheelbase * sprung_mass_axle(cfg)["rear"] / sprung_mass_total(cfg)


def sprung_mass_per_corner(cfg: VehicleConfig) -> dict:
    """SUS-009: massa suspensa por canto = massa suspensa do eixo / 2 (simetria lateral)."""
    m = sprung_mass_axle(cfg)
    return {"FL": m["front"] / 2, "FR": m["front"] / 2,
            "RL": m["rear"] / 2, "RR": m["rear"] / 2}


def sprung_cg_height(cfg: VehicleConfig) -> float:
    """SUS-012: h_s a partir da identidade de CG composto
    (m_s*h_s + m_uF*h_uF + m_uR*h_uR = m*h_CG)."""
    ms = sprung_mass_total(cfg)
    return (cfg.mass_total * cfg.cg_height
            - cfg.unsprung_mass_front * cfg.unsprung_cg_height_front
            - cfg.unsprung_mass_rear * cfg.unsprung_cg_height_rear) / ms


# ---------- SUS-101 : carga estática ----------

def static_fz_corner(cfg: VehicleConfig) -> dict:
    L = cfg.wheelbase
    Wf = cfg.mass_total * G * (cfg.cg_to_rear / L)   # b/L
    Wr = cfg.mass_total * G * (cfg.cg_to_front / L)  # a/L
    return {"FL": Wf / 2, "FR": Wf / 2, "RL": Wr / 2, "RR": Wr / 2}


# ---------- SUS-102 : transferência longitudinal ----------

def longitudinal_dfz(cfg: VehicleConfig, ax: float) -> dict:
    """ax > 0 = aceleração para frente (ISO 8855) -> transfere para o eixo traseiro."""
    L = cfg.wheelbase
    dfz_front_axle = -cfg.mass_total * ax * cfg.cg_height / L
    dfz_rear_axle = +cfg.mass_total * ax * cfg.cg_height / L
    return {"front_per_corner": dfz_front_axle / 2,
            "rear_per_corner": dfz_rear_axle / 2}


# ---------- SUS-103 : modelo de duas molas de Milliken ----------

def lateral_dfz(cfg: VehicleConfig, ay: float) -> dict:
    """SUS-103, Milliken p. 680-683 (fórmula completa) e p. 604; Seward eq. 5.16-5.21; Gillespie eq. 6-31 a 6-34.
    ay > 0 = aceleração para a esquerda (ISO 8855) -> lado direito ganha carga.
    Três massas (suspensa + não suspensas por eixo). O CG suspenso fica em a_s (EDR-047) e o
    deslocamento lateral dele com a rolagem entra pelo termo gravitacional m_s·g·h2 (EDR-046):
        φ = m_s·a_y·h2 / (K_φF + K_φR − m_s·g·h2)
        ΔFz_F = [K_φF·φ + a_y·(m_s,F·z_F + m_uF·h_uF)] / t_F   (análogo atrás)
    h2 = h_s − z_s na vertical (exemplo da Milliken p. 683 e Seward p. 133). φ positivo = rola para
    a direita (rotação + em X, ISO), o lado de fora numa curva à esquerda."""
    L = cfg.wheelbase
    tF, tR = cfg.track_front, cfg.track_rear
    zF, zR = cfg.roll_center_front, cfg.roll_center_rear
    ms = sprung_mass_total(cfg)
    hs = sprung_cg_height(cfg)
    m_ax = sprung_mass_axle(cfg)
    a_s = sprung_cg_to_front(cfg)

    KphiF, KphiR = cfg.roll_stiffness_front, cfg.roll_stiffness_rear
    lambda_f = KphiF / (KphiF + KphiR)
    lambda_r = KphiR / (KphiF + KphiR)

    zs = zF + (zR - zF) * a_s / L
    h2 = hs - zs
    den = KphiF + KphiR - ms * G * h2
    _req(den > 0, f"SUS-103 instabilidade de rolagem: m_s·g·h2 = {ms * G * h2:.1f} N·m/rad >= K_φF+K_φR = "
                  f"{KphiF + KphiR:.1f} N·m/rad (Milliken p. 682). Aumente a rigidez de rolagem ou revise h_s/RC.")
    phi = ms * ay * h2 / den

    dFzF = (KphiF * phi + ay * (m_ax["front"] * zF + cfg.unsprung_mass_front * cfg.unsprung_cg_height_front)) / tF
    dFzR = (KphiR * phi + ay * (m_ax["rear"] * zR + cfg.unsprung_mass_rear * cfg.unsprung_cg_height_rear)) / tR

    return {"front_axle": dFzF, "rear_axle": dFzR,
            "lambda_f": lambda_f, "lambda_r": lambda_r, "z_s": zs, "a_s": a_s, "h2": h2, "roll_angle_rad": phi}


# ---------- SUS-701 / SUS-702 : aero ----------

def aero_fz_corner(downforce_total: float, aero_balance_front: float) -> dict:
    _req(isinstance(aero_balance_front, (int, float)) and 0.0 <= aero_balance_front <= 1.0,
         f"SUS-702 aero_balance_front={aero_balance_front!r} fora de [0,1] (fração dianteira da downforce).")
    _req(math.isfinite(downforce_total), "SUS-701 downforce_total deve ser finito.")
    fz_aero_f = downforce_total * aero_balance_front
    fz_aero_r = downforce_total * (1 - aero_balance_front)
    return {"FL": fz_aero_f / 2, "FR": fz_aero_f / 2,
            "RL": fz_aero_r / 2, "RR": fz_aero_r / 2}


# ---------- SUS-104 : Fz combinado por canto ----------

def fz_plausibility(fz: dict) -> list:
    """Lista de avisos acionáveis para Fz<0 (SUS-104; Guide D.4). Fz == 0 é a fronteira do domínio e não gera aviso."""
    out = []
    for corner, v in fz.items():
        if v < 0:
            out.append({"corner": corner, "fz_N": v,
                        "action": "Perda de contato (liftoff): o modelo linear de SUS-104 não deve ser extrapolado. "
                                  "Reduza a/aceleração, revise rigidez de rolagem/altura do CG, ou trate este ponto como fora do domínio."})
    return out


def combined_fz_corner(cfg: VehicleConfig, ax: float, ay: float,
                        downforce_total: float = 0.0,
                        aero_balance_front: float = 0.5,
                        warn: bool = True) -> dict:
    fz_static = static_fz_corner(cfg)
    long_ = longitudinal_dfz(cfg, ax)
    lat_ = lateral_dfz(cfg, ay)
    aero = aero_fz_corner(downforce_total, aero_balance_front)

    dFzF, dFzR = lat_["front_axle"], lat_["rear_axle"]

    fz = {
        "FL": fz_static["FL"] + long_["front_per_corner"] - dFzF + aero["FL"],
        "FR": fz_static["FR"] + long_["front_per_corner"] + dFzF + aero["FR"],
        "RL": fz_static["RL"] + long_["rear_per_corner"] - dFzR + aero["RL"],
        "RR": fz_static["RR"] + long_["rear_per_corner"] + dFzR + aero["RR"],
    }
    if warn:
        for w in fz_plausibility(fz):
            warnings.warn(FzLiftoffWarning(f"Fz_{w['corner']} = {w['fz_N']:.1f} N < 0. {w['action']}"), stacklevel=2)
    return fz


# ---------- SUS-201 / SUS-202 : motion ratio e wheel rate ----------

def wheel_rate(k_spring: float, mr_wheel_spring: float) -> float:
    """SUS-202, Analysis Mode. MR = wheel/spring."""
    _req(k_spring > 0, "SUS-203/202 k_spring deve ser > 0 (rigidez de mola não positiva é bloqueada).")
    _req(mr_wheel_spring > 0, "SUS-201 MR [wheel/spring] deve ser > 0.")
    if mr_wheel_spring < MR_WARN_THRESHOLD:
        warnings.warn(SmallMotionRatioWarning(
            f"MR={mr_wheel_spring} < {MR_WARN_THRESHOLD} (limite hipotético): K_w = K_s/MR^2 fica muito sensível. "
            "Confirme o MR (convenção wheel/spring, não a inversa)."), stacklevel=2)
    return k_spring / mr_wheel_spring ** 2


def spring_rate_from_wheel_rate(k_wheel: float, mr_wheel_spring: float) -> float:
    """SUS-202, Design Mode (reverso)."""
    _req(k_wheel > 0, "SUS-202 k_wheel deve ser > 0.")
    _req(mr_wheel_spring > 0, "SUS-201 MR [wheel/spring] deve ser > 0.")
    return k_wheel * mr_wheel_spring ** 2


# ---------- SUS-212 : ride rate (mola na roda em série com o pneu, EDR-045) ----------

def _serie(k1: float, k2: float) -> float:
    """Duas molas em série: k1·k2/(k1+k2). k2 = inf devolve k1 (pneu rígido)."""
    return k1 if math.isinf(k2) else k1 * k2 / (k1 + k2)


def ride_rate(k_wheel: float, k_tire: float) -> float:
    """SUS-212: K_R = K_W·K_T/(K_W+K_T) (Milliken p. 591; Gillespie eq. 5-8; Seward eq. 4.1).
    k_tire = SUS-211 (rigidez vertical do pneu); math.inf só para isolar a mola em teste."""
    _req(k_wheel > 0, "SUS-202 k_wheel deve ser > 0.")
    _req(k_tire > 0, "SUS-211 k_tire (rigidez vertical do pneu) deve ser > 0.")
    return _serie(k_wheel, k_tire)


def wheel_rate_from_ride_rate(k_ride: float, k_tire: float) -> float:
    """SUS-212 reverso: K_W = K_R·K_T/(K_T − K_R) (Milliken p. 591; Seward eq. 4.4). Exige K_T > K_R."""
    _req(k_ride > 0 and k_tire > 0, "SUS-212/211 k_ride e k_tire devem ser > 0.")
    if math.isinf(k_tire):
        return k_ride
    _req(k_tire > k_ride, f"SUS-212 ride rate {k_ride:.1f} N/m >= rigidez do pneu {k_tire:.1f} N/m: "
                          "nenhuma mola consegue (a ride rate nunca passa da rigidez do pneu).")
    return k_ride * k_tire / (k_tire - k_ride)


# ---------- SUS-205 : frequência natural ----------

def natural_frequency(k_ride: float, m_sprung_corner: float) -> float:
    """SUS-205: f = √(K_R/m)/2π com a RIDE RATE (SUS-212), não o wheel rate (EDR-045;
    Gillespie eq. 5-9; Seward eq. 4.2; Milliken p. 588). A função em si é a de 1 GDL."""
    _req(k_ride > 0 and m_sprung_corner > 0, "SUS-205 k_ride e m_sprung_corner devem ser > 0.")
    return (1 / (2 * math.pi)) * math.sqrt(k_ride / m_sprung_corner)


def wheel_rate_from_target_frequency(f_target: float, m_sprung_corner: float, k_tire: float) -> float:
    """SUS-205, Design Mode (reverso): K_R = (2πf)²·m e K_W = K_R·K_T/(K_T − K_R) (EDR-045)."""
    _req(f_target > 0 and m_sprung_corner > 0, "SUS-205 f_target e m_sprung_corner devem ser > 0.")
    return wheel_rate_from_ride_rate((2 * math.pi * f_target) ** 2 * m_sprung_corner, k_tire)


# ---------- SUS-206 / SUS-207 : rigidez de rolagem por eixo ----------

def roll_stiffness_axle(k_wheel: float, track: float, k_arb: float, k_tire: float) -> float:
    """SUS-206/207 (EDR-045): (K_W·t²/2 + K_ARB) em série com o par de pneus (K_T·t²/2).
    Milliken p. 589-592 (barra referida à roda, depois o pneu em série) e p. 680 (as rigidezes
    de rolagem da transferência de carga incluem a deflexão do pneu); Seward eq. 4.5."""
    _req(k_wheel > 0 and track > 0 and k_arb >= 0, "SUS-206/207 k_wheel e track devem ser > 0 e k_arb >= 0.")
    _req(k_tire > 0, "SUS-211 k_tire deve ser > 0.")
    k_susp = (k_wheel * track ** 2) / 2 + k_arb
    return _serie(k_susp, k_tire * track ** 2 / 2)


def arb_required(k_phi_axle_required: float, k_wheel: float, track: float, k_tire: float) -> float:
    """SUS-208 Design (EDR-045): K_ARB que leva o eixo à rigidez total pedida, com o pneu em série.
    K_susp = K_req·K_φT/(K_φT − K_req); K_ARB = K_susp − K_W·t²/2 (pode sair negativo: a mola sozinha já passa)."""
    _req(k_phi_axle_required > 0 and k_wheel > 0 and track > 0 and k_tire > 0, "SUS-208 entradas devem ser > 0.")
    k_phi_t = math.inf if math.isinf(k_tire) else k_tire * track ** 2 / 2
    if not math.isinf(k_phi_t):
        _req(k_phi_t > k_phi_axle_required, "SUS-208 rigidez pedida >= rigidez de rolagem do par de pneus: inalcançável.")
        k_susp = k_phi_axle_required * k_phi_t / (k_phi_t - k_phi_axle_required)
    else:
        k_susp = k_phi_axle_required
    return k_susp - k_wheel * track ** 2 / 2


# ---------- SUS-208 : distribuição de rigidez de rolagem ----------

def roll_stiffness_distribution(k_phi_f: float, k_phi_r: float) -> dict:
    _req(k_phi_f >= 0 and k_phi_r >= 0 and (k_phi_f + k_phi_r) > 0, "SUS-208 rigidezes de rolagem devem ser >= 0 com soma > 0.")
    total = k_phi_f + k_phi_r
    return {"lambda_f": k_phi_f / total, "lambda_r": k_phi_r / total}


# ---------- V2.1 : cross-check de Motion Ratio (SUS-201 x SUS-409) ----------

def mr_crosscheck(mr_input: float, mr_geometric=None, rel_tol=None) -> dict:
    """Compara o MR [wheel/spring] de entrada com o MR geométrico (SUS-409) ou de uma referência.

    NÃO há tolerância padrão: ela deve ser definida a partir de incerteza geométrica, sensibilidade numérica e
    diferenças de definição (ex.: ponto de operação, definição de curso), que dependem de dados reais ainda
    indisponíveis. Sem tolerância, o resultado traz as diferenças relativas mas status 'TOLERANCE_NOT_SET'.

    Status: NOT_EXECUTED (sem referência) | TOLERANCE_NOT_SET | MATCH | INVERSION_SUSPECTED | MISMATCH |
            MATCH_INVERSION_NOT_DISTINGUISHABLE (MR próximo de 1: direto e inverso coincidem na tolerância).
    'INVERSION_SUSPECTED' é só uma suspeita: investigar unidades, sinais, configuração, ponto de operação e
    método do solver antes de concluir. Toda outra discrepância é 'MISMATCH' (não é classificada como inversão).
    """
    _req(isinstance(mr_input, (int, float)) and math.isfinite(mr_input) and mr_input > 0, "SUS-201 mr_input deve ser finito e > 0.")
    if mr_geometric is None:
        return {"status": "NOT_EXECUTED", "reason": "MR geométrico/de referência não fornecido: cross-check NÃO executado.",
                "rel_diff_direct": None, "rel_diff_if_inverted": None}
    _req(isinstance(mr_geometric, (int, float)) and math.isfinite(mr_geometric) and mr_geometric > 0, "SUS-409 mr_geometric deve ser finito e > 0.")
    direct = abs(mr_input - mr_geometric) / mr_geometric
    inverted = abs(1.0 / mr_input - mr_geometric) / mr_geometric
    out = {"rel_diff_direct": direct, "rel_diff_if_inverted": inverted}
    if rel_tol is None:
        return {**out, "status": "TOLERANCE_NOT_SET", "reason": "Tolerância não definida (sem valor padrão por falta de dados reais)."}
    _req(isinstance(rel_tol, (int, float)) and math.isfinite(rel_tol) and rel_tol >= 0, "rel_tol deve ser finito e >= 0.")
    if direct <= rel_tol and inverted <= rel_tol:
        return {**out, "status": "MATCH_INVERSION_NOT_DISTINGUISHABLE", "reason": "MR ≈ 1 dentro da tolerância: o cross-check não distingue inversão."}
    if direct <= rel_tol:
        return {**out, "status": "MATCH", "reason": "MR de entrada coincide com o MR geométrico dentro da tolerância."}
    if inverted <= rel_tol:
        return {**out, "status": "INVERSION_SUSPECTED",
                "reason": "O inverso do MR de entrada coincide com o MR geométrico: investigar convenção wheel/spring, unidades, configuração e ponto de operação."}
    return {**out, "status": "MISMATCH", "reason": "Discrepância não explicada por inversão: investigar unidades, sinais, configuração, ponto de operação e solver."}
