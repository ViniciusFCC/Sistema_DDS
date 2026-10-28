"""
Testes do módulo escada (incremento 6, Task 6): degrau 1 (MMM na configuração da planilha contra analise_par),
degrau 2 (uma hipótese por vez) e sensibilidades por unidade.
TC-ESC-001: degrau 1 nos casos do test_equilibrio.py, nos dois sentidos.
TC-ESC-002: degrau 2 (linhas, Δ = 0 na planilha, sem veredito de tolerância, valores de `inverte`, pior sentido da 7).
TC-ESC-003: sensibilidades (unidade, sinal de cg_lateral com o sentido, sem faixa).
Roda como script: uv run python -X utf8 tests/test_escada.py
Veículo, pneu de escala de teste (LMUY 0,5), R = 8,5 m, downforce, toe, Ackermann, tração e CG lateral são entradas
sintéticas de teste, não do carro.
"""

import dataclasses
import os
import time

import equilibrio as eq
import escada
import mmm
import tire_model as tm
from suspension_model import VehicleConfig

HERE = os.path.dirname(os.path.abspath(__file__))
TIR = os.path.join(HERE, "..", "data", "Hoosier_R25B_13x7_TTC_provisional.tir")
results = []
T0 = time.time()


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


def veiculo_base(**over) -> VehicleConfig:
    """Veículo de teste (números plausíveis, NÃO é setup real)."""
    base = dict(
        mass_total=250.0, cg_height=0.300, wheelbase=1.550, track_front=1.200, track_rear=1.150,
        cg_to_front=0.837, cg_to_rear=0.713, unsprung_mass_front=15.0, unsprung_mass_rear=18.0,
        unsprung_cg_height_front=0.230, unsprung_cg_height_rear=0.230, roll_center_front=0.030,
        roll_center_rear=0.050, roll_stiffness_front=20826.4, roll_stiffness_rear=26450.0,
    )
    base.update(over)
    return VehicleConfig(**base)


cfg = veiculo_base()
k_soma = cfg.roll_stiffness_front + cfg.roll_stiffness_rear


def veiculo_simetrico(lambda_f=0.5, **over):
    L = cfg.wheelbase
    return veiculo_base(**{**dict(cg_to_front=L / 2, cg_to_rear=L / 2, track_rear=cfg.track_front,
                                  roll_stiffness_front=lambda_f * k_soma, roll_stiffness_rear=(1 - lambda_f) * k_soma,
                                  roll_center_rear=cfg.roll_center_front, unsprung_mass_rear=cfg.unsprung_mass_front,
                                  unsprung_cg_height_rear=cfg.unsprung_cg_height_front), **over})


ds = tm.load_dataset(TIR, source_axis_system="ISO_TYDEX")
ds_teste = dataclasses.replace(ds, p={**ds.p, "LMUY": 0.5})   # escala de teste, não é pneu do carro
R_TESTE = 8.5   # sintético de teste: raio do skidpad usado só nos testes
TOE = {"FL": 0.003, "FR": 0.003, "RL": 0.002, "RR": 0.002}   # sintético de teste
AERO = dict(downforce_N=400.0, aero_balance_front=0.45)      # sintético de teste

casos = {
    "base": eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, **AERO),
    "simétrico": eq.CasoEquilibrio(cfg=veiculo_simetrico(0.5), ds=ds_teste, raio_m=R_TESTE),
    "com toe": eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, toe_rad=TOE, **AERO),
    "com Ackermann 50 %": eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, ackermann_pct=50.0, **AERO),
    "com tração": eq.CasoEquilibrio(cfg=cfg, ds=ds_teste, raio_m=R_TESTE, rho_kg_m3=1.2, cda_m2=1.0, crr=0.02, **AERO),
}
# CG lateral ≠ 0 perto do neutro (o mesmo do TC-MMM-006): o sentido decide o veredito.
caso_cg = eq.CasoEquilibrio(cfg=veiculo_base(roll_stiffness_front=23700.0), ds=ds_teste, raio_m=R_TESTE,
                            cg_lateral_m=0.06)

# ---------------- TC-ESC-001 : degrau 1 ----------------
ok_001, dets_001 = True, []
for nome, caso_x in casos.items():
    esq, dir_ = escada.degrau_1(caso_x)
    for c in (esq, dir_):
        ok_001 = ok_001 and c.ok and c.veredito_mmm == c.veredito_par
        dets_001.append(f"{nome}/{c.sentido}: {c.veredito_mmm}, d_sat=({c.d_ay_sat_f}, {c.d_ay_sat_r}), "
                        f"cn=({c.cn_mmm}, {c.cn_par}), res={c.resolucao_ms2}, ok={c.ok}"
                        + (f", motivo={c.motivo!r}" if c.motivo else ""))
    ok_001 = ok_001 and (esq.sentido, dir_.sentido) == ("esquerda", "direita")
# Cota da saturação = resolução do limite + resolução do analise_par (2·res): dois resultados discretizados, cada um
# com a incerteza que declara (decisão do controlador; só <= res punha o oráculo no limite por construção).
# A comparação não pode ser frouxa: desvios fabricados (de saturação e de veredito) têm de reprovar.
res_f = 0.01
ok_fab = (escada._julga(eq.PUSH, eq.PUSH, 2.5 * res_f, 0.0, None, None, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.PUSH, 0.0, -2.5 * res_f, None, None, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.LOOSE, 0.0, 0.0, None, None, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.PUSH, 0.0, 0.0, 0.5, 0.1, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.PUSH, 0.0, 0.0, 0.1, 0.1, res_f, 1.0)[0] is True
          and escada._julga(eq.NA, eq.NA, None, None, None, None, res_f, None)[0] is True)
check("TC-ESC-001: degrau 1 (base, simétrico, com toe, com Ackermann 50 %, com tração; esquerda e direita): mesmo "
      "veredito, |ay_sat − S| <= resolução do limite + do analise_par por eixo, cn_estabilizante = c_n dentro da folga equivalente; "
      "desvios fabricados reprovam", ok_001 and ok_fab, "; ".join(dets_001))

# ---------------- TC-ESC-002 : degrau 2 ----------------
linhas = escada.degrau_2(casos["base"])
nomes = tuple(l.nome for l in linhas)
esperados = ("planilha", "1+2", "3", "7", "9a", "9b", "10", "10+9b", "11", "todas")
por_nome = {l.nome: l for l in linhas}
pl = por_nome["planilha"]
ok_pl = (pl.d_ay_t in (0.0, None) and pl.d_cn_estabilizante_q in (0.0, None) and pl.d_k in (0.0, None)
         and pl.pior_sentido is None)
campos = {f.name for f in dataclasses.fields(escada.LinhaEscada)}
ok_campos = not any("toler" in c or "dentro" in c or c == "ok" for c in campos)
VALIDOS = {"não", "sim", "NEUTRO ↔ PUSH", "NEUTRO ↔ LOOSE", "N/A"}
ok_inv = all(l.inverte in VALIDOS for l in linhas)
ok_h = (por_nome["10+9b"].hipoteses == (10, 9) and por_nome["todas"].hipoteses == (1, 2, 3, 7, 9, 10, 11)
        and por_nome["1+2"].hipoteses == (1, 2) and por_nome["9a"].hipoteses == (9,))
ok_ps = (por_nome["7"].pior_sentido in ("esquerda", "direita")
         and all(l.pior_sentido is None for l in linhas if l.nome not in ("7", "todas")))
# `inverte` por regra, com vereditos fabricados (a regra isolada).
regra = {(eq.PUSH, eq.PUSH): "não", (eq.PUSH, eq.LOOSE): "sim", (eq.LOOSE, eq.PUSH): "sim",
         (eq.NEUTRO, eq.PUSH): "NEUTRO ↔ PUSH", (eq.PUSH, eq.NEUTRO): "NEUTRO ↔ PUSH",
         (eq.NEUTRO, eq.LOOSE): "NEUTRO ↔ LOOSE", (eq.LOOSE, eq.NEUTRO): "NEUTRO ↔ LOOSE",
         (eq.NEUTRO, eq.NEUTRO): "não", (eq.NA, eq.PUSH): "N/A", (eq.PUSH, eq.NA): "N/A", (eq.NA, eq.NA): "N/A"}
ok_regra = all(escada._inverte(a, b) == v for (a, b), v in regra.items())
# Linha 7 = pior dos dois sentidos, conferido com dois limites montados à mão (CG lateral ≠ 0).
l7 = next(l for l in escada.degrau_2(caso_cg) if l.nome == "7")
le, ld = mmm.limite(caso_cg, mmm.Hipoteses.planilha()), mmm.limite(eq.espelhar(caso_cg), mmm.Hipoteses.planilha())
pior_man = "esquerda" if (le.ay_t_ms2 is not None and (ld.ay_t_ms2 is None or le.ay_t_ms2 <= ld.ay_t_ms2)) else "direita"
ok_7 = (le.ay_t_ms2 is not None and ld.ay_t_ms2 is not None and l7.pior_sentido == pior_man
        and l7.limite.ay_t_ms2 == min(le.ay_t_ms2, ld.ay_t_ms2))
# Com tração, o diferencial travado pode dar N/A em R = 8,5 m (Fx oposto nas traseiras): a escada o relata, não falha.
linhas_tr = escada.degrau_2(casos["com tração"])
ok_tr = (tuple(l.nome for l in linhas_tr) == esperados and all(l.inverte in VALIDOS for l in linhas_tr)
         and all((l.inverte == "N/A") == (eq.NA in (l.limite.veredito, linhas_tr[0].limite.veredito))
                 for l in linhas_tr)
         and all(l.limite.motivo for l in linhas_tr if l.limite.veredito == eq.NA))
check("TC-ESC-002: degrau 2 (10 linhas na ordem; planilha com Δ = 0; sem campo de veredito de tolerância; `inverte` ∈ "
      "{não, sim, NEUTRO ↔ PUSH, NEUTRO ↔ LOOSE, N/A} e a regra isolada; pior sentido só na 7 (e na todas, que a inclui), "
      "conferido à mão com CG lateral ≠ 0; com tração, N/A relatado com motivo e inverte = N/A)",
      nomes == esperados and ok_pl and ok_campos and ok_inv and ok_h and ok_ps and ok_regra and ok_7 and ok_tr,
      f"nomes={nomes}; " + "; ".join(f"{l.nome}: T={l.limite.ay_t_ms2}, {l.limite.veredito}, d_T={l.d_ay_t}, "
                                      f"d_cn={l.d_cn_estabilizante_q}, d_k={l.d_k}, inverte={l.inverte}"
                                      + (f", motivo={l.limite.motivo!r}" if l.limite.motivo else "") for l in linhas)
      + "; COM TRAÇÃO: " + "; ".join(f"{l.nome}: T={l.limite.ay_t_ms2}, {l.limite.veredito}, d_T={l.d_ay_t}, "
                                   f"inverte={l.inverte}" + (f", motivo={l.limite.motivo!r}" if l.limite.motivo else "")
                                   for l in linhas_tr)
      + f"; linha 7 (caso_cg): pior={l7.pior_sentido}, T esq={le.ay_t_ms2}, T dir={ld.ay_t_ms2}")

# ---------------- TC-ESC-003 : sensibilidades ----------------
# Caso com tração (rho, CdA, Crr de teste): h_cp só age com o regime e a resistência ao avanço.
sens = escada.sensibilidades(casos["com tração"])
ok_un = (tuple(s["parametro"] for s in sens) == tuple(mmm.UNIDADES)
         and all(s["unidade"] == mmm.UNIDADES[s["parametro"]] for s in sens))
ok_sem_faixa = not any(("faixa" in k or "min" in k or "max" in k) for s in sens for k in s)
# cg_lateral: espelhar(caso) é a curva à esquerda do carro espelhado, onde +10 mm é o sentido oposto ao do carro
# original. A sensibilidade em relação ao deslocamento do carro (+y do carro) na curva à direita é, portanto, o
# negativo da calculada no caso espelhado; é esse o sinal que troca com o sentido.
s_esq = next(s for s in escada.sensibilidades(caso_cg) if s["parametro"] == "cg_lateral")
s_dir_espelho = mmm.sensibilidade(eq.espelhar(caso_cg), mmm.Hipoteses.planilha(), "cg_lateral")
sinais = []
for chave in ("d_ay_t", "d_cn_estabilizante_q"):
    a, b = s_esq[chave], s_dir_espelho[chave]
    sinais.append(a is not None and b is not None and a * (-b) < 0)
ok_sinal = all(sinais)
s_hcp = next(s for s in sens if s["parametro"] == "h_cp")
ok_hcp = (s_hcp["motivo"] != "h_cp só com transf_long=regime" and s_hcp["d_ay_t"] is not None
          and s_hcp["d_ay_t"] != 0.0)   # com o regime ligado, a parcela D·h_cp/L age
check("TC-ESC-003: sensibilidades (uma por chave de UNIDADES, unidade = mmm.UNIDADES; sinal de d_ay_t e de d_cn de "
      "cg_lateral, no referencial do carro, troca com o sentido; h_cp roda com transf_long=regime e age; nenhuma faixa)",
      ok_un and ok_sem_faixa and ok_sinal and ok_hcp,
      f"cg_lateral esq: d_ay_t={s_esq['d_ay_t']}, d_cn={s_esq['d_cn_estabilizante_q']}; dir (caso espelhado, +10 mm "
      f"no referencial dele): d_ay_t={s_dir_espelho['d_ay_t']}, d_cn={s_dir_espelho['d_cn_estabilizante_q']}; "
      + "; ".join(f"{s['parametro']}: d_T={s['d_ay_t']}, d_cn={s['d_cn_estabilizante_q']}, d_k={s['d_k']}, "
                  f"({s['veredito_menos']}, {s['veredito_mais']})" for s in sens))

print(f"\nTempo: {time.time() - T0:.0f} s")
print("\n--- Resumo ---")
n_pass = sum(1 for _, s, _ in results if s == "PASS")
n_fail = sum(1 for _, s, _ in results if s == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
