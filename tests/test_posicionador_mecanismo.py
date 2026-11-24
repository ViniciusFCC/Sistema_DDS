"""
Testes do mecanismo por construção e da configuração com procedência do posicionador (EDR-076, TC-POS-050 a 055).
TC-POS-050: a regra de construção, com a semente da v20 e o r2 da v20, reproduz PUSH_OUT, PUSH_IN, ROCKER_AXIS_A e
            ROCKER_SPRING do arquivo v20 (o SPRING_CHASSIS não entra: o plano trocou a regra do olhal do script).
TC-POS-051: com o r2 resolvido, MR [wheel/spring] no estático = MR_ALVO (1,40) ± 1e-4.
TC-POS-052: comprimento do amortecedor no droop máximo = olho a olho (EYE) ± 1e-6 m.
TC-POS-053: config.carregar recusa item sem fonte, sem origem ou com origem desconhecida; a_confirmar() lista os 7 itens.
TC-POS-054: pivô sobre a junta LCA_OUT (plano degenerado) → hardpoints None e motivo não vazio.
TC-POS-055: config.carregar recusa, com ConfigError que cita o nome do item, item obrigatório (config.OBRIGATORIOS) com valor
            null (A_CONFIRMAR) ou ausente, e número não finito (NaN, Infinity) em qualquer item; a configuração do T11
            carrega com todos os obrigatórios numéricos (revisão final da fase 1, I3).
A semente e o r2 vêm de data/posicionador/origem_v20_script.json (saída do script de atuação, com SHA-256); os arquivos de
configuração inválidos do TC-POS-053 e do TC-POS-055 são SINTÉTICOS de teste.
Roda como script: uv run python -X utf8 tests/test_posicionador_mecanismo.py
"""
import copy
import json
import os
import tempfile

import numpy as np

import hardpoints as hp
import kinematics_model as km
from posicionador import config as pc
from posicionador import mecanismo as mec

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DADOS = os.path.join(RAIZ, "data", "posicionador")

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


hs_v10 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"),
                            os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
hs_v20 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v20_script.csv"),
                            os.path.join(DADOS, "hardpoints_T11_v20_script.meta.json"))
with open(os.path.join(DADOS, "origem_v20_script.json"), encoding="utf-8") as f:
    origem = json.load(f)
cfg = pc.carregar(os.path.join(DADOS, "config_T11.json"))
x = origem["x_semente"]
v = mec.Variaveis.da_semente_do_script(x)
r2_v20 = x[7] / 1000.0
droop = cfg.valor("curso_droop_m")
eye = cfg.valor("olho_a_olho_m")

# --- TC-POS-050 ---------------------------------------------------------------------------------------------------
c50 = mec.construir(hs_v10, v, cfg, r2_m=r2_v20)
if c50.hardpoints is None:
    check("TC-POS-050 construção reproduz os pontos da v20", False, f"motivo: {c50.motivo}")
else:
    erros = {k: float(np.linalg.norm(c50.hardpoints.points[f"FL_{k}"].xyz - hs_v20.points[f"FL_{k}"].xyz))
             for k in ("PUSH_OUT", "PUSH_IN", "ROCKER_AXIS_A", "ROCKER_SPRING")}
    # o eixo B é Pv + 0,05·n: confere a direção do eixo (normal do plano) também
    eixo = c50.hardpoints.points["FL_ROCKER_AXIS_B"].xyz - c50.hardpoints.points["FL_ROCKER_AXIS_A"].xyz
    eixo20 = hs_v20.points["FL_ROCKER_AXIS_B"].xyz - hs_v20.points["FL_ROCKER_AXIS_A"].xyz
    e_eixo = float(np.linalg.norm(eixo - eixo20))
    fixos_iguais = all(np.array_equal(c50.hardpoints.points[k].xyz, p.xyz) for k, p in hs_v10.points.items())
    comp_ok = c50.hardpoints.points["FL_PUSH_OUT"].component == "LCA" and c50.r2_m == r2_v20 and c50.motivo is None
    check("TC-POS-050 construção reproduz os pontos da v20",
          max(erros.values()) < 1e-6 and e_eixo < 1e-6 and fixos_iguais and comp_ok,
          "erros [m]: " + ", ".join(f"{k}={e:.2e}" for k, e in erros.items())
          + f", eixo B−A={e_eixo:.2e}; pontos fixos da v10 iguais={fixos_iguais}; PUSH_OUT em LCA e r2 dado={comp_ok}")

# --- TC-POS-051 ---------------------------------------------------------------------------------------------------
c51 = mec.construir(hs_v10, v, cfg)
mr_alvo = cfg.valor("mr_alvo")
if c51.hardpoints is None:
    check("TC-POS-051 r2 resolvido dá MR(0) = MR_ALVO", False, f"motivo: {c51.motivo}")
    check("TC-POS-052 comprimento no droop = olho a olho", False, f"motivo: {c51.motivo}")
else:
    canto = km.Corner(c51.hardpoints, "FL")
    mr = km.motion_ratio(canto, 0.0)["mr_wheel_per_spring"]
    check("TC-POS-051 r2 resolvido dá MR(0) = MR_ALVO", abs(mr - mr_alvo) < 1e-4,
          f"MR(0)={mr:.7f} (alvo {mr_alvo}, erro {abs(mr - mr_alvo):.2e}); r2={c51.r2_m * 1e3:.4f} mm "
          f"(v20: {x[7]:.4f} mm)")

    # --- TC-POS-052 -----------------------------------------------------------------------------------------------
    s0 = canto.solve(0.0)
    sd = canto.solve(-droop, q0=s0.q, phi0=s0.phi)
    ld = canto.spring_length(sd)
    ld50 = None
    if c50.hardpoints is not None:
        c50k = km.Corner(c50.hardpoints, "FL")
        s050 = c50k.solve(0.0)
        ld50 = c50k.spring_length(c50k.solve(-droop, q0=s050.q, phi0=s050.phi))
    ok52 = abs(ld - eye) < 1e-6 and (ld50 is None or abs(ld50 - eye) < 1e-6)
    check("TC-POS-052 comprimento no droop = olho a olho", ok52,
          f"|B(dz=−{droop * 1e3:.1f} mm) − C|={ld:.9f} m (EYE {eye} m, erro {abs(ld - eye):.2e})"
          + ("" if ld50 is None else f"; com o r2 da v20: erro {abs(ld50 - eye):.2e}"))

# --- TC-POS-053 ---------------------------------------------------------------------------------------------------
with open(os.path.join(DADOS, "config_T11.json"), encoding="utf-8") as f:
    bruto = json.load(f)


def recusa(mexer):
    """Grava uma cópia SINTÉTICA alterada da configuração e diz se carregar() a recusa com ConfigError."""
    d = copy.deepcopy(bruto)
    mexer(d["itens"])
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "config_sintetica.json")
        with open(p, "w", encoding="utf-8") as g:
            json.dump(d, g)
        try:
            pc.carregar(p)
        except pc.ConfigError as e:
            return True, str(e)
        return False, ""


sem_fonte = recusa(lambda it: it["mr_alvo"].pop("fonte"))
fonte_vazia = recusa(lambda it: it["mr_alvo"].update(fonte="  "))
sem_origem = recusa(lambda it: it["dj_m"].pop("origem"))
origem_ruim = recusa(lambda it: it["dj_m"].update(origem="CHUTE"))
nulo_sem_ac = recusa(lambda it: it["dj_m"].update(valor=None))
esperados = {"curso_cremalheira_m", "margem_curso_amortecedor_m", "x_face_traseira_aip_m", "x_ini_t12_m", "x_fim_t12_m",
             "z_min_t12_m", "z_max_t12_m"}
lista = cfg.a_confirmar()
nulos_ok = all(cfg.valor(n) is None for n in esperados)
sha = origem["arquivos"]["t11_atuacao.py"]
procedencia = all(it.origem in pc.ORIGENS and it.fonte.strip() for it in cfg.itens.values())
sha_ok = all(sha in cfg.item(n).fonte for n in ("curso_droop_m", "olho_a_olho_m", "mr_alvo", "folga_gabarito_m"))
ok53 = (sem_fonte[0] and fonte_vazia[0] and sem_origem[0] and origem_ruim[0] and nulo_sem_ac[0]
        and set(lista) == esperados and len(lista) == 7 and nulos_ok and procedencia and sha_ok)
check("TC-POS-053 configuração com procedência", ok53,
      f"recusa sem fonte={sem_fonte[0]} ({sem_fonte[1]!r}), fonte vazia={fonte_vazia[0]}, sem origem={sem_origem[0]}, "
      f"origem desconhecida={origem_ruim[0]}, null fora de A_CONFIRMAR={nulo_sem_ac[0]}; a_confirmar()={sorted(lista)}; "
      f"todos com origem e fonte={procedencia}; SHA do script na fonte={sha_ok}")

# --- TC-POS-054 ---------------------------------------------------------------------------------------------------
j = hs_v10.points["FL_LCA_OUT"].xyz.copy()
v54 = mec.Variaveis(pivo_m=j, az_rad=v.az_rad, el_rad=v.el_rad, r1_m=v.r1_m, phi_b_rad=v.phi_b_rad)
c54 = mec.construir(hs_v10, v54, cfg)
c54b = mec.construir(hs_v10, v54, cfg, r2_m=r2_v20)
check("TC-POS-054 pivô sobre a junta: geometria degenerada sem exceção",
      c54.hardpoints is None and bool(c54.motivo) and c54b.hardpoints is None and bool(c54b.motivo),
      f"motivo: {c54.motivo!r}")

# --- TC-POS-055 ---------------------------------------------------------------------------------------------------
def a_confirmar(nome):
    def f(it):
        it[nome].update(valor=None, origem="A_CONFIRMAR", fonte="SINTÉTICO de teste (TC-POS-055)")
    return f


casos55 = {nome: recusa(a_confirmar(nome)) for nome in pc.OBRIGATORIOS}
ruins55 = [n for n, (rec, msg) in casos55.items() if not (rec and repr(n) in msg)]
ausente = recusa(lambda it: it.pop("r_prod_m"))
nan55 = recusa(lambda it: it["folga_aro_m"].update(valor=float("nan")))
inf55 = recusa(lambda it: it["transformacao_step_m"]["valor"]["translacao_m"].__setitem__(0, float("inf")))
obrig_ok = all(isinstance(cfg.valor(n), (int, float)) and not isinstance(cfg.valor(n), bool) for n in pc.OBRIGATORIOS)
ok55 = (not ruins55 and len(casos55) == 22 and ausente[0] and "'r_prod_m'" in ausente[1] and nan55[0]
        and "'folga_aro_m'" in nan55[1] and inf55[0] and "'transformacao_step_m'" in inf55[1] and obrig_ok)
check("TC-POS-055 item obrigatório null ou ausente e número não finito: ConfigError com o nome do item", ok55,
      f"{len(casos55)} obrigatórios, recusados com o nome: {len(casos55) - len(ruins55)} (falharam: {ruins55}); "
      f"ex.: {casos55['mr_alvo'][1]!r}; ausente: {ausente[1]!r}; NaN: {nan55[1]!r}; inf: {inf55[1]!r}; "
      f"T11 com todos numéricos={obrig_ok}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
