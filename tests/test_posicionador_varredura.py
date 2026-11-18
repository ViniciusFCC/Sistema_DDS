"""
Testes da varredura e da avaliação de um candidato do posicionador (EDR-076, TC-POS-060 a 064).
TC-POS-060: `kinematics_model.Corner` × kinlib na v20: Ls(dz) do Corner bate com `curvas_kinlib_v20.csv` nos 401 pontos
            com erro < 1e-5 m (critério de aprovação do EDR-076; se falhar, a busca não segue).
TC-POS-061: avaliação convergida da v20 sem CAD: variação de MR entre 0,060 e 0,0625 (VIOLADA), folga do push rod ao aro
            no segmento real entre 0,079 e 0,0825 m, veredito INVIAVEL. O brief dá 0,060–0,062 para a variação de MR; o
            MR local exato (motion_ratio) tem o máximo na ponta do bump e dá 0,0621 convergido (n = 400: 0,06206), igual à
            própria curva do kinlib com derivada de 2ª ordem nas pontas (0,06206; com a de 1ª ordem do np.gradient,
            0,06141). A faixa foi ampliada para 0,0625 e a mudança está nos pontos de atenção do relatório da Task 6
            (a confirmar pelo controlador).
TC-POS-062: `avaliar` com n = 25 e n = 50 na v20 dá os mesmos estados em todas as restrições; a variação de MR converge
            (|v50 − v400| < |v25 − v400|).
TC-POS-063: pivô do rocker a 2 m do carro (push rod que não fecha no curso) → INVIAVEL com motivo "cinemática sem
            solução ...", sem exceção.
TC-POS-064: com `curso_cremalheira_m` nulo, o esterçamento sai NAO_VERIFICAVEL e um candidato SINTÉTICO que cumpre todo o
            resto sai CONDICIONAL.
Dados: v20 e curvas do kinlib de data/posicionador/ (saídas do script do Murilo, com SHA-256 em origem_v20_murilo.json).
Os candidatos, as configurações alteradas e a cena do TC-POS-063/064 são SINTÉTICOS de teste, não do carro.
Roda como script: uv run python -X utf8 tests/test_posicionador_varredura.py
"""
import copy
import json
import os
import tempfile
import time

import numpy as np

import hardpoints as hp
import kinematics_model as km
from posicionador import config as pc
from posicionador import mecanismo as mec
from posicionador import varredura as vr
from posicionador.geometria import Esfera

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DADOS = os.path.join(RAIZ, "data", "posicionador")

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


hs_v10 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v10.csv"),
                            os.path.join(DADOS, "hardpoints_T11_v10.meta.json"))
hs_v20 = hp.load_hardpoints(os.path.join(DADOS, "hardpoints_T11_v20_murilo.csv"),
                            os.path.join(DADOS, "hardpoints_T11_v20_murilo.meta.json"))
with open(os.path.join(DADOS, "origem_v20_murilo.json"), encoding="utf-8") as f:
    origem = json.load(f)
CAMINHO_CFG = os.path.join(DADOS, "config_T11.json")
cfg = pc.carregar(CAMINHO_CFG)
x = origem["x_semente"]
c_v20 = mec.Construcao(hardpoints=hs_v20, r2_m=x[7] / 1000.0, motivo=None)
cena0 = vr.cena_sem_cad(cfg)


def estados(av):
    return {r.nome: r.estado for r in av.restricoes}


# --- TC-POS-060 ---------------------------------------------------------------------------------------------------
curvas = np.loadtxt(os.path.join(DADOS, "curvas_kinlib_v20.csv"), delimiter=",", skiprows=1)
canto = km.Corner(hs_v20, "FL")
s0 = canto.solve(0.0)
erros, erros_th = [], []
for dz, ls_k, th_k in curvas:
    s = canto.solve(float(dz), q0=s0.q, phi0=s0.phi)
    erros.append(canto.spring_length(s) - ls_k)
    erros_th.append(s.phi - th_k)
erros = np.abs(np.array(erros))
i_max = int(np.argmax(erros))
check("TC-POS-060 Corner × kinlib na v20 (Ls em 401 pontos)",
      len(curvas) == 401 and float(erros.max()) < 1e-5,
      f"{len(curvas)} pontos; erro máximo de Ls = {erros.max():.3e} m em dz = {curvas[i_max, 0] * 1e3:.4f} mm; "
      f"ângulo do rocker: erro máximo {np.abs(erros_th).max():.3e} rad")

# --- TC-POS-061 ---------------------------------------------------------------------------------------------------
t0 = time.perf_counter()
a61 = vr.avaliar_convergido(c_v20, cena0, cfg)
dt61 = time.perf_counter() - t0
mrv = a61.restricao("variação de MR")
aro = a61.restricao("folga ao aro: push rod")
ok61 = (mrv is not None and aro is not None and 0.060 <= mrv.valor <= 0.0625 and mrv.estado == "VIOLADA"
        and 0.079 <= aro.valor <= 0.0825 and a61.veredito == "INVIAVEL")
check("TC-POS-061 v20 convergida sem CAD: variação de MR VIOLADA, folga ao aro, INVIAVEL", ok61,
      f"n = {a61.n} (resoluções {a61.resolucoes}, {dt61:.1f} s); variação de MR = "
      f"{None if mrv is None else round(mrv.valor, 5)} ({None if mrv is None else mrv.estado}); folga ao aro "
      f"(push rod, segmento O→A) = {None if aro is None else round(aro.valor * 1e3, 2)} mm; veredito {a61.veredito}; "
      f"motivo: {a61.motivo}")

# --- TC-POS-062 ---------------------------------------------------------------------------------------------------
a25 = vr.avaliar(c_v20, cena0, cfg, n=25)
a50 = vr.avaliar(c_v20, cena0, cfg, n=50)
a400 = vr.avaliar(c_v20, cena0, cfg, n=400)
e25, e50 = estados(a25), estados(a50)
v25, v50, v400 = (a.restricao("variação de MR").valor for a in (a25, a50, a400))
difs = sorted(k for k in set(e25) | set(e50) if e25.get(k) != e50.get(k))
check("TC-POS-062 n = 25 e n = 50 com os mesmos estados; variação de MR converge",
      e25 == e50 and len(e25) > 0 and abs(v50 - v400) < abs(v25 - v400),
      f"{len(e25)} restrições, estados diferentes: {difs}; variação de MR: n25 = {v25:.6f}, n50 = {v50:.6f}, "
      f"n400 = {v400:.6f} (|v50 − v400| = {abs(v50 - v400):.2e} < |v25 − v400| = {abs(v25 - v400):.2e})")

# --- TC-POS-063 ---------------------------------------------------------------------------------------------------
# SINTÉTICO: o grupo do rocker da v20 (pivô, push rod no rocker, olhal no rocker e no chassi) transladado 2 m em Z, com o
# eixo do rocker vertical: o push rod passa a ter ~2,3 m, quase vertical, e o rocker só move o ponto PUSH_IN na
# horizontal (alcance de ±r1), sem acompanhar a subida da bandeja: o push rod não fecha no curso.
GRUPO = ("FL_PUSH_IN", "FL_ROCKER_AXIS_A", "FL_ROCKER_SPRING", "FL_SPRING_CHASSIS")
linhas = []
for pid, p in hs_v20.points.items():
    xyz = p.xyz + (np.array([0.0, 0.0, 2.0]) if pid in GRUPO else 0.0)
    if pid == "FL_ROCKER_AXIS_B":
        xyz = hs_v20.points["FL_ROCKER_AXIS_A"].xyz + np.array([0.0, 0.0, 2.05])
    linhas.append([pid, repr(float(xyz[0])), repr(float(xyz[1])), repr(float(xyz[2])), p.component, "SYNTHETIC"])
hs_63 = hp.build_hardpoint_set(linhas, dict(hs_v20.meta, geometry_rev="SINTÉTICO: rocker da v20 a 2 m em Z"))
c63 = mec.Construcao(hardpoints=hs_63, r2_m=c_v20.r2_m, motivo=None)
try:
    a63 = vr.avaliar(c63, cena0, cfg, n=25)
    a63c = vr.avaliar_convergido(c63, cena0, cfg)
    sem_exc, txt63 = True, ""
except Exception as e:  # noqa: BLE001  (o teste é justamente que nada escape)
    a63 = a63c = None
    sem_exc, txt63 = False, f"{type(e).__name__}: {e}"
c63b = mec.Construcao(hardpoints=None, r2_m=None, motivo="SINTÉTICO: geometria que não fecha")
a63b = vr.avaliar(c63b, cena0, cfg)
ok63 = (sem_exc and a63.veredito == "INVIAVEL" and a63.motivo.startswith("cinemática sem solução em dz = ")
        and a63c.veredito == "INVIAVEL" and a63c.motivo.startswith("cinemática sem solução")
        and a63b.veredito == "INVIAVEL" and a63b.motivo.startswith("construção: "))
check("TC-POS-063 pivô a 2 m: INVIAVEL por cinemática sem solução, sem exceção", ok63,
      txt63 or f"motivo: {a63.motivo!r}; convergida: {a63c.motivo!r}; sem hardpoints: {a63b.motivo!r}")

# --- TC-POS-064 ---------------------------------------------------------------------------------------------------
# Candidato SINTÉTICO: o mecanismo construído sobre a v10 com a semente da v20 (r2 resolvido para MR(0) = 1,40), avaliado
# com uma configuração SINTÉTICA em que as metas que a v20 não cumpre estão folgadas e os itens nulos que não são o curso
# da cremalheira têm valor SINTÉTICO, numa cena SINTÉTICA com um obstáculo fixo longe e a faixa do gabarito declarada.
with open(CAMINHO_CFG, encoding="utf-8") as f:
    bruto = json.load(f)
SINT = {"mr_var_max": 0.10, "curso_amortecedor_m": 0.065, "margem_curso_amortecedor_m": 0.001, "braco_max_m": 0.085,
        "folga_pernas_m": 0.003,
        "x_face_traseira_aip_m": 1.0, "x_ini_t12_m": -0.40, "x_fim_t12_m": -1.20}


def cfg_sintetica(valores):
    d = copy.deepcopy(bruto)
    for nome, valor in valores.items():
        d["itens"][nome].update(valor=valor, origem="HIPOTESE", fonte="SINTÉTICO de teste (TC-POS-064)")
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "config_sintetica.json")
        with open(p, "w", encoding="utf-8") as g:
            json.dump(d, g)
        return pc.carregar(p)


cfg64 = cfg_sintetica(SINT)
c64 = mec.construir(hs_v10, mec.Variaveis.da_semente_do_script(x), cfg64)
cena64 = vr.Cena(fixos=[Esfera(np.array([-2.0, 0.0, 0.3]), 0.05)], nos=[], aro=cena0.aro,
                 regras=dict(vr.regras_da_config(cfg64), z_min_t12_m=0.10, z_max_t12_m=0.30))
if c64.hardpoints is None:
    check("TC-POS-064 esterçamento NAO_VERIFICAVEL e candidato SINTÉTICO CONDICIONAL", False, f"construção: {c64.motivo}")
else:
    a64 = vr.avaliar_convergido(c64, cena64, cfg64)
    est = [r for r in a64.restricoes if r.nome.startswith("esterçamento")]
    violadas = [r.nome for r in a64.restricoes if r.estado == "VIOLADA"]
    nao_ver = [r.nome for r in a64.restricoes if r.estado == "NAO_VERIFICAVEL"]
    parciais = [r.nome for r in a64.restricoes if not r.completa]
    # com o curso da cremalheira SINTÉTICO, o esterçamento é avaliado (prova de que o NAO_VERIFICAVEL vem do null)
    cfg64b = cfg_sintetica(dict(SINT, curso_cremalheira_m=0.020))
    a64b = vr.avaliar(c64, cena64, cfg64b, n=25)
    est_b = [r for r in a64b.restricoes if r.nome.startswith("esterçamento")]
    ok64 = (cfg64.valor("curso_cremalheira_m") is None and len(est) > 0
            and all(r.estado == "NAO_VERIFICAVEL" for r in est) and not violadas
            and set(nao_ver) == {r.nome for r in est} and a64.veredito == "CONDICIONAL"
            and len(est_b) == len(est) and all(r.estado == "OK" for r in est_b) and a64b.veredito == "CONDICIONAL")
    check("TC-POS-064 esterçamento NAO_VERIFICAVEL e candidato SINTÉTICO CONDICIONAL", ok64,
          f"esterçamento: {[(r.nome, r.estado) for r in est]}; violadas: {violadas}; não verificáveis: {nao_ver}; "
          f"parciais: {parciais}; veredito {a64.veredito} ({a64.motivo}); com cremalheira SINTÉTICA: "
          f"{[(r.nome, r.estado) for r in est_b]}, veredito {a64b.veredito}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
