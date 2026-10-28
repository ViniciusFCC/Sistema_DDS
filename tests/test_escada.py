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
ok_001, dets_001, razao_max = True, [], 0.0
for nome, caso_x in casos.items():
    esq, dir_ = escada.degrau_1(caso_x)
    for c in (esq, dir_):
        ok_001 = ok_001 and c.ok and c.veredito_mmm == c.veredito_par
        razoes = [abs(d) / c.resolucao_ms2 for d in (c.d_ay_sat_f, c.d_ay_sat_r) if d is not None and c.resolucao_ms2]
        razao_max = max(razoes + [razao_max])
        dets_001.append(f"{nome}/{c.sentido}: {c.veredito_mmm}, d_sat=({c.d_ay_sat_f}, {c.d_ay_sat_r}), "
                        f"|d|/res=({', '.join(f'{r:.2f}' for r in razoes)}), "
                        f"cn=({c.cn_mmm}, {c.cn_par}), res={c.resolucao_ms2}, ok={c.ok}"
                        + (f", motivo={c.motivo!r}" if c.motivo else ""))
    ok_001 = ok_001 and (esq.sentido, dir_.sentido) == ("esquerda", "direita")
# Cota da saturação = 2·res, EMPÍRICA (ver escada._julga): a resolução que o analise_par declara é |S_h − S_h/2| e subestima
# o erro de interpolação dele (≈ 4/3 da resolução, Richardson); a razão |d|/res observada em cada caso sai no detalhe.
# Não é cota provada. Exigir só <= res punha o oráculo no limite por construção.
# A comparação não pode ser frouxa: desvios fabricados (de saturação e de veredito) têm de reprovar.
res_f = 0.01
ok_fab = (escada._julga(eq.PUSH, eq.PUSH, 2.5 * res_f, 0.0, None, None, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.PUSH, 0.0, -2.5 * res_f, None, None, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.LOOSE, 0.0, 0.0, None, None, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.PUSH, 0.0, 0.0, 0.5, 0.1, res_f, 1.0)[0] is False
          and escada._julga(eq.PUSH, eq.PUSH, 0.0, 0.0, 0.1, 0.1, res_f, 1.0)[0] is True
          and escada._julga(eq.NA, eq.NA, None, None, None, None, res_f, None)[0] is True)
check("TC-ESC-001: degrau 1 (base, simétrico, com toe, com Ackermann 50 %, com tração; esquerda e direita): mesmo "
      "veredito, |ay_sat − S| <= 2·resolucao_ms2 (cota empírica) por eixo, cn_estabilizante = c_n dentro da folga "
      "equivalente; desvios fabricados reprovam", ok_001 and ok_fab,
      f"maior |d_ay_sat|/res = {razao_max:.2f} (estimativa do erro do analise_par: 4/3 da resolução); " + "; ".join(dets_001))

# ---------------- TC-ESC-002 : degrau 2 ----------------
linhas = escada.degrau_2(casos["base"])
nomes = tuple(l.nome for l in linhas)
esperados = ("planilha", "planilha (acoplado)", "1+2", "3", "7", "9a", "9b", "10", "10+9b", "11", "todas")
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
# Linha de controle (I5): a planilha resolvida pelo Newton 2-D com a rotação a_y = A·cos β. O Δ dela é contra a planilha (viés
# do método e da rotação); o das linhas acopladas é contra ela; o da 7 (desacoplada) e o dela própria, contra a planilha.
ctrl = por_nome["planilha (acoplado)"]
ACOPLADAS = ("1+2", "3", "9a", "9b", "10", "10+9b", "11", "todas")
ok_ctrl = (ctrl.referencia == "planilha" and ctrl.hipoteses == () and ctrl.limite.ay_t_ms2 is not None
           and ctrl.d_ay_t == ctrl.limite.ay_t_ms2 - pl.limite.ay_t_ms2 and ctrl.d_ay_t != 0.0
           and all(por_nome[n].referencia == "planilha (acoplado)" for n in ACOPLADAS)
           and all(por_nome[n].referencia == "planilha" for n in ("planilha", "planilha (acoplado)", "7"))
           and all(abs(por_nome[n].d_ay_t - (por_nome[n].limite.ay_t_ms2 - ctrl.limite.ay_t_ms2)) < 1e-12
                   for n in ("3", "9a", "11") if por_nome[n].d_ay_t is not None))
# I1: marca de hipótese desligada. O caso base não tem tração (cda_m2, crr) nem CG lateral, então as linhas 9a, 9b, 10, 10+9b,
# 7 e todas levam "hipótese desligada no caso (<campo>)"; as demais, None. A linha desligada ainda é calculada e, sem a
# hipótese, coincide com a referência por construção (Δ = 0 nas de tração, que são acopladas e idênticas à de controle).
ok_motivo = (all(por_nome[n].motivo == "hipótese desligada no caso (cda_m2 e crr)" for n in ("9a", "9b", "10", "10+9b"))
             and por_nome["7"].motivo == "hipótese desligada no caso (cg_lateral_m)"
             and por_nome["todas"].motivo == "hipótese desligada no caso (cda_m2 e crr; cg_lateral_m)"
             and all(por_nome[n].motivo is None for n in ("planilha", "planilha (acoplado)", "1+2", "3", "11"))
             and all(por_nome[n].limite.ay_t_ms2 is not None and abs(por_nome[n].d_ay_t) < 1e-9
                     for n in ("9a", "9b", "10", "10+9b")))
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
        and l7.limite.ay_t_ms2 == min(le.ay_t_ms2, ld.ay_t_ms2)
        and l7.motivo is None)   # com CG lateral ≠ 0 a hipótese 7 está ligada
# Com tração, o diferencial travado pode dar N/A em R = 8,5 m (Fx oposto nas traseiras): a escada o relata, não falha.
linhas_tr = escada.degrau_2(casos["com tração"])
por_nome_tr = {l.nome: l for l in linhas_tr}
ok_tr = (tuple(l.nome for l in linhas_tr) == esperados and all(l.inverte in VALIDOS for l in linhas_tr)
         and all((l.inverte == "N/A") == (eq.NA in (l.limite.veredito, por_nome_tr[l.referencia].limite.veredito))
                 for l in linhas_tr)
         and all(l.limite.motivo for l in linhas_tr if l.limite.veredito == eq.NA)
         and [l.nome for l in linhas_tr if l.motivo] == ["7", "todas"]   # com tração só a 7 (sem CG lateral) está desligada
         and por_nome_tr["todas"].motivo == "hipótese desligada no caso (cg_lateral_m)")
check("TC-ESC-002: degrau 2 (11 linhas na ordem, com a de controle `planilha (acoplado)`; planilha com Δ = 0; Δ das "
      "acopladas contra a de controle; sem campo de veredito de tolerância; `inverte` ∈ "
      "{não, sim, NEUTRO ↔ PUSH, NEUTRO ↔ LOOSE, N/A} e a regra isolada; pior sentido só na 7 (e na todas, que a inclui), "
      "conferido à mão com CG lateral ≠ 0; hipótese desligada no caso com motivo; com tração, N/A relatado com motivo e "
      "inverte = N/A)",
      nomes == esperados and ok_pl and ok_campos and ok_inv and ok_h and ok_ps and ok_regra and ok_7 and ok_tr
      and ok_ctrl and ok_motivo,
      f"nomes={nomes}; " + "; ".join(f"{l.nome}: T={l.limite.ay_t_ms2}, {l.limite.veredito}, d_T={l.d_ay_t} (vs {l.referencia}), "
                                      f"d_cn={l.d_cn_estabilizante_q}, d_k={l.d_k}, inverte={l.inverte}"
                                      + (f", motivo do limite={l.limite.motivo!r}" if l.limite.motivo else "")
                                      + (f", {l.motivo}" if l.motivo else "") for l in linhas)
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
# Sinal absoluto (curva à esquerda, ISO: +y é a esquerda, o lado de dentro). O caso_cg tem o CG 60 mm para dentro. Deslocar o
# CG mais para dentro soma carga estática nas rodas internas e tira das externas, e a transferência lateral faz o contrário:
# as quatro cargas ficam mais próximas entre si. Com pneu de sensibilidade à carga negativa (μ cai com Fz, concavidade de Fy
# em Fz), cargas mais iguais aumentam a aderência total, então T sobe: d_ay_t > 0 por +10 mm (valor medido no detalhe).
ok_sinal = ok_sinal and s_esq["d_ay_t"] is not None and s_esq["d_ay_t"] > 0.0
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
