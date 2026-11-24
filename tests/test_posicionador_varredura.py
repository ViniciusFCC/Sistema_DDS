"""
Testes da varredura e da avaliação de um candidato do posicionador (EDR-076, TC-POS-060 a 069).
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
TC-POS-065: falha fechada com NaN (revisão final, I1): a `Cena` recusa primitivo fixo não finito (ValueError); com uma
            Capsula SINTÉTICA com NaN entre os fixos (antes ou depois de uma esfera que colide), nenhuma "folga aos fixos"
            sai OK e o veredito é INVIAVEL "avaliação sem resultado"; o mesmo com o aro NaN.
TC-POS-066: regressão da propriedade de segurança (I4, M6), v20 em cenas SINTÉTICAS: (i) esfera sobre o pivô → folga aos
            fixos do rocker VIOLADA; (ii) gabarito T.1.2 centrado no rocker → VIOLADA ("a atuação bloqueia"); (iii) face
            da AIP em X = 0 → AIP VIOLADA; os três dão INVIAVEL. (iv) parede SINTÉTICA que sozinha fecha o gabarito →
            NAO_VERIFICAVEL "o chassi sozinho já bloqueia" e `relatorio.alertas_regulamento` destaca que o carro reprova o
            T.1.2 independentemente da atuação.
TC-POS-067: regressão do esterçamento da v20 com curso de cremalheira SINTÉTICO de ±30 mm (n = 25): folga ao aro no
            esterçamento 43,6 mm ± 0,1 mm e folga ao eixo do tirante 22,8 mm ± 0,1 mm, as duas OK (valores do próprio
            código na revisão final, não validação).
TC-POS-068: não modelado (I2): toda avaliação tem "folga à manga/freio/pinça dentro do aro" NAO_VERIFICAVEL; com peças
            RODA_/BANDEJA_/DIR_ na cena, também "folga às peças móveis do STEP"; `Cena.nao_modelado` traz os itens da
            spec §4 que a fase 1 não implementa (pneu, coluna, pedais/F.8.6.3, IA/F.8.4.2, V.3.2.4, T.1.3.3, V.3.1.3,
            F.5.3.1); o candidato SINTÉTICO do TC-POS-064 com todos os itens nulos preenchidos não chega a VIAVEL.
TC-POS-069: referencial da configuração (I5): com `Cena.ref_hipotese` (STEP sem esferas REF_), a folga aos fixos sai com
            origem HIPOTESE e a fonte cita `transformacao_step_m`; sem ele, META.
Dados: v20 e curvas do kinlib de data/posicionador/ (saídas do script de atuação, com SHA-256 em origem_v20_script.json).
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
from posicionador import relatorio as rl
from posicionador import varredura as vr
from posicionador.geometria import Caixa, Capsula, Esfera

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
    # a folga à manga/freio/pinça é NAO_VERIFICAVEL em todo candidato da fase 1 (TC-POS-068); fica fora desta conta
    nao_ver = [r.nome for r in a64.restricoes if r.estado == "NAO_VERIFICAVEL" and r.nome != vr.NOME_MANGA]
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

# --- TC-POS-065 ---------------------------------------------------------------------------------------------------
pv20 = hs_v20.points["FL_ROCKER_AXIS_A"].xyz
colide = Esfera(np.array(pv20, dtype=float), 0.05)                                 # SINTÉTICA: colisão certa no pivô
nan_cap = Capsula(np.array([np.nan, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), 0.01)   # SINTÉTICA: primitivo com NaN
try:
    vr.Cena(fixos=[colide, nan_cap], nos=[], aro=cena0.aro, regras=dict(cena0.regras))
    recusa65 = None
except ValueError as e:
    recusa65 = str(e)
res65 = {}
for rot, fixos in (("NaN antes", [nan_cap, colide]), ("NaN depois", [colide, nan_cap]), ("só NaN", [nan_cap])):
    cn = vr.cena_sem_cad(cfg)
    cn.fixos = fixos                       # contorna a validação da Cena de propósito: a avaliação também tem de fechar
    av = vr.avaliar(c_v20, cn, cfg, n=11)
    ok_fix = [r.nome for r in av.restricoes if r.nome.startswith("folga aos fixos") and r.estado == "OK"]
    res65[rot] = (av.veredito, ok_fix, (av.motivo or "")[:90])
cn = vr.cena_sem_cad(cfg)
cn.aro = (float("nan"), cn.aro[1])
av_aro = vr.avaliar(c_v20, cn, cfg, n=11)
ok65 = (recusa65 is not None and "não finito" in recusa65
        and all(v == "INVIAVEL" and not ok and m.startswith("avaliação sem resultado") for v, ok, m in res65.values())
        and av_aro.veredito == "INVIAVEL" and (av_aro.motivo or "").startswith("avaliação sem resultado"))
check("TC-POS-065 NaN nos fixos ou no aro: nenhuma folga OK, INVIAVEL (falha fechada)", ok65,
      f"Cena com NaN: {recusa65!r}; {res65}; aro NaN: {av_aro.veredito} ({(av_aro.motivo or '')[:90]})")

# --- TC-POS-066 ---------------------------------------------------------------------------------------------------
t0 = time.perf_counter()
ci = vr.Cena(fixos=[colide], nos=[], aro=cena0.aro, regras=dict(cena0.regras))
a_i = vr.avaliar(c_v20, ci, cfg, n=11)
# SINTÉTICO: gabarito centrado no rocker da v20 (Y 0,27 m), trecho X de −0,02 a −0,10 m, base de 0,30 a 0,45 m; AIP em X = 0
reg66 = dict(cena0.regras, x_ini_t12_m=-0.02, x_fim_t12_m=-0.10, z_min_t12_m=0.30, z_max_t12_m=0.45, y_centro_t12_m=0.27,
             x_face_traseira_aip_m=0.0)
a_ii = vr.avaliar(c_v20, vr.Cena(fixos=[], nos=[], aro=cena0.aro, regras=reg66), cfg, n=11)
parede = Caixa(np.array([-0.06, 0.27, 0.6]), np.eye(3), np.array([0.005, 0.4, 0.6]))   # SINTÉTICA: fecha o gabarito
a_iv = vr.avaliar(c_v20, vr.Cena(fixos=[parede], nos=[], aro=cena0.aro, regras=reg66), cfg, n=11)
e_i = a_i.restricao("folga aos fixos: rocker")
g_ii, aip_ii, g_iv = a_ii.restricao("gabarito T.1.2"), a_ii.restricao("AIP (F.8.6.1)"), a_iv.restricao("gabarito T.1.2")
alertas = rl.alertas_regulamento([a_iv])
ok66 = (e_i.estado == "VIOLADA" and e_i.valor < 0 and a_i.veredito == "INVIAVEL"
        and g_ii.estado == "VIOLADA" and g_ii.motivo.startswith("a atuação bloqueia") and aip_ii.estado == "VIOLADA"
        and aip_ii.valor < 0 and a_ii.veredito == "INVIAVEL"
        and g_iv.estado == "NAO_VERIFICAVEL" and g_iv.motivo == vr.MOTIVO_CHASSI_BLOQUEIA and len(alertas) == 1
        and "reprova o T.1.2" in alertas[0] and not rl.alertas_regulamento([a_ii]))
check("TC-POS-066 colisão, gabarito e AIP SINTÉTICOS dão VIOLADA; chassi que bloqueia o T.1.2 é destacado", ok66,
      f"(i) {e_i.estado} {e_i.valor * 1e3:.1f} mm, {a_i.veredito}; (ii) gabarito {g_ii.estado} ({g_ii.motivo[:40]}), AIP "
      f"{aip_ii.estado} {aip_ii.valor * 1e3:.1f} mm, {a_ii.veredito}; (iv) {g_iv.estado} ({g_iv.motivo}), alertas "
      f"{len(alertas)}; {time.perf_counter() - t0:.1f} s")

# --- TC-POS-067 ---------------------------------------------------------------------------------------------------
cfg67 = cfg_sintetica({"curso_cremalheira_m": 0.030})
a67 = vr.avaliar(c_v20, vr.cena_sem_cad(cfg67), cfg67, n=25)
ea, et = a67.restricao("esterçamento: folga ao aro"), a67.restricao("esterçamento: folga ao tirante")
ok67 = (ea.estado == "OK" and abs(ea.valor - 0.0436) < 1e-4 and et.estado == "OK" and abs(et.valor - 0.0228) < 1e-4
        and not et.completa)
check("TC-POS-067 esterçamento da v20 com ±30 mm SINTÉTICOS: folga ao aro 43,6 mm e ao tirante 22,8 mm", ok67,
      f"aro {ea.estado} {ea.valor * 1e3:.3f} mm ({ea.motivo}); tirante {et.estado} {et.valor * 1e3:.3f} mm "
      f"(parcial={not et.completa})")

# --- TC-POS-068 ---------------------------------------------------------------------------------------------------
a68 = vr.avaliar(c_v20, cena0, cfg, n=11)
cm = vr.Cena(fixos=[], nos=[], aro=cena0.aro, regras=dict(cena0.regras), pecas_moveis=["RODA_FE", "DIR"])
a68m = vr.avaliar(c_v20, cm, cfg, n=11)
manga, manga_m, moveis = a68.restricao(vr.NOME_MANGA), a68m.restricao(vr.NOME_MANGA), a68m.restricao(vr.NOME_MOVEIS)
txt = " | ".join(cena0.nao_modelado)
termos = ("pneu", "coluna", "F.8.6.3", "F.8.4.2", "V.3.2.4", "T.1.3.3", "V.3.1.3", "F.5.3.1", "manga")
falta68 = [k for k in termos if k not in txt]
cheia = cfg_sintetica(dict(SINT, curso_cremalheira_m=0.020, z_min_t12_m=0.10, z_max_t12_m=0.30))
a68c = vr.avaliar(c64, cena64, cheia, n=11) if c64.hardpoints is not None else None
ok68 = (manga is not None and manga.estado == "NAO_VERIFICAVEL" and a68.restricao(vr.NOME_MOVEIS) is None
        and manga_m.estado == "NAO_VERIFICAVEL" and moveis is not None and moveis.estado == "NAO_VERIFICAVEL"
        and "RODA_FE" in moveis.motivo and not falta68 and all(t in cm.nao_modelado for t in vr.NAO_MODELADO_FASE1)
        and a68c is not None and a68c.veredito == "CONDICIONAL" and vr.NOME_MANGA in (a68c.motivo or ""))
check("TC-POS-068 manga/freio e peças móveis NAO_VERIFICAVEL; não modelado da spec §4 declarado; sem VIAVEL", ok68,
      f"manga: {None if manga is None else manga.estado}; peças móveis: {None if moveis is None else moveis.estado}; "
      f"termos ausentes do nao_modelado: {falta68}; candidato SINTÉTICO cheio: "
      f"{None if a68c is None else (a68c.veredito, (a68c.motivo or '')[:160])}")

# --- TC-POS-069 ---------------------------------------------------------------------------------------------------
longe = Esfera(np.array([-2.0, 0.0, 0.3]), 0.05)                                    # SINTÉTICA
a69h = vr.avaliar(c_v20, vr.Cena(fixos=[longe], nos=[], aro=cena0.aro, regras=dict(cena0.regras),
                                 ref_hipotese="HIPOTESE: SINTÉTICO de teste (TC-POS-069)"), cfg, n=11)
a69r = vr.avaliar(c_v20, vr.Cena(fixos=[longe], nos=[], aro=cena0.aro, regras=dict(cena0.regras)), cfg, n=11)
fh = [a69h.restricao(f"folga aos fixos: {c}") for c in vr.CORPOS]
fr = [a69r.restricao(f"folga aos fixos: {c}") for c in vr.CORPOS]
ok69 = (all(r.origem == "HIPOTESE" and "transformacao_step_m" in r.fonte and r.estado == "OK" for r in fh)
        and all(r.origem == "META" and "transformacao_step_m" not in r.fonte for r in fr))
check("TC-POS-069 referencial da configuração: folga aos fixos com origem HIPOTESE e fonte transformacao_step_m", ok69,
      f"com ref_hipotese: {[(r.origem, r.estado) for r in fh]}; fonte: {fh[0].fonte[-120:]!r}; sem: "
      f"{[r.origem for r in fr]}")

print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
