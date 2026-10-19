"""
REFERÊNCIA HISTÓRICA T09/E03 (EDR-012): NÃO é baseline nem teste de aprovação do modelo.

Porte do caso de referência do T09 (original: importado-claude-ai/saidas-conversas/plan/
test_t09_reference_case.py, que importava o suspension_model da v0.1). Decisão A3 do SPEC,
tomada pelo usuário em 2026-10-19: portar como regressão histórica, sem contar na aprovação.

O que este script confere: que o modelo atual, configurado na forma SEM pneu em série
(k_tire = inf), reproduz os números da planilha de cálculo detalhada do T09. Ou seja, confere
a TRANSCRIÇÃO das fórmulas que a equipe usava, não a física. Desde a V3.0 (EDR-045) o projeto
segue a literatura e põe o pneu em série; a forma "com pneu" é mostrada só como informação.

Uso: uv run python -X utf8 tests/regressao/t09_referencia_historica.py
Não entra no tools/rodar_testes.py nem nas contagens do CLAUDE.md. Saída: código 1 se algum
valor histórico deixar de ser reproduzido (sinal de que a transcrição mudou).
"""
import math

from suspension_model import natural_frequency, ride_rate, roll_stiffness_axle, roll_stiffness_distribution

TOL_PCT = 0.5   # tolerância do caso original (em %)
SEM_PNEU = math.inf

# Dados da planilha de cálculo detalhada do T09 (poster "Dynamics"), como no caso original
track = 1.25                      # m (dianteira = traseira no T09)
kw_f, kw_r = 16112.23, 18418.20   # N/m (wheel rate; a planilha chamava de "Ride Rate")
karb_f, karb_r = 5012.324152, 10.78078274   # N·m/rad
ms_eixo_f, ms_eixo_r = 121.5, 148.5          # kg, massa suspensa por eixo do T09

DECLARADO = {
    "Rigidez de rolagem sem ARB - dianteira": 12587.68,
    "Rigidez de rolagem sem ARB - traseira": 14389.22,
    "Rigidez de rolagem total - dianteira": 17600.0,
    "Rigidez de rolagem total - traseira": 14400.0,
    "lambda_f": 0.55,
    "Frequência natural - dianteira [Hz]": 2.592,
    "Frequência natural - traseira [Hz]": 2.507,
}

rs_f0 = roll_stiffness_axle(kw_f, track, 0.0, SEM_PNEU)
rs_r0 = roll_stiffness_axle(kw_r, track, 0.0, SEM_PNEU)
rs_f = roll_stiffness_axle(kw_f, track, karb_f, SEM_PNEU)
rs_r = roll_stiffness_axle(kw_r, track, karb_r, SEM_PNEU)
CALCULADO = {
    "Rigidez de rolagem sem ARB - dianteira": rs_f0,
    "Rigidez de rolagem sem ARB - traseira": rs_r0,
    "Rigidez de rolagem total - dianteira": rs_f,
    "Rigidez de rolagem total - traseira": rs_r,
    "lambda_f": roll_stiffness_distribution(rs_f, rs_r)["lambda_f"],
    "Frequência natural - dianteira [Hz]": natural_frequency(ride_rate(kw_f, SEM_PNEU), ms_eixo_f / 2),
    "Frequência natural - traseira [Hz]": natural_frequency(ride_rate(kw_r, SEM_PNEU), ms_eixo_r / 2),
}

print("=== REFERÊNCIA HISTÓRICA T09/E03 (EDR-012) — não é baseline nem aprovação do modelo ===")
print("Forma sem pneu em série (k_tire = inf), como a planilha do T09.\n")
confere, diverge = 0, 0
for nome, decl in DECLARADO.items():
    calc = CALCULADO[nome]
    erro = 100 * (calc - decl) / decl
    ok = abs(erro) < TOL_PCT
    confere += ok
    diverge += not ok
    print(f"[{'CONFERE' if ok else 'DIVERGE'}] {nome}: calculado={calc:.4f}  T09={decl}  erro={erro:+.3f} %")

print("\nSem dado histórico (não conferível): Fz estático, transferência longitudinal, transferência lateral.")
print("Motivo: não há condição de operação (a_x, a_y) nem Fz medido do T09.")

print("\nInformativo — o mesmo T09 pela forma da V3.0 (pneu em série, EDR-045), com o K_T do .tir")
print("PROVISÓRIO (120312 N/m, não é o pneu do T09): os valores históricos deixam de bater por construção.")
KT = 120312.0
rs_f_t = roll_stiffness_axle(kw_f, track, karb_f, KT)
rs_r_t = roll_stiffness_axle(kw_r, track, karb_r, KT)
print(f"  K_φF={rs_f_t:.1f}  K_φR={rs_r_t:.1f} N·m/rad  λ_f={roll_stiffness_distribution(rs_f_t, rs_r_t)['lambda_f']:.4f}  "
      f"f_F={natural_frequency(ride_rate(kw_f, KT), ms_eixo_f / 2):.3f} Hz  f_R={natural_frequency(ride_rate(kw_r, KT), ms_eixo_r / 2):.3f} Hz")

print(f"\nT09 (referência histórica): {confere} conferem, {diverge} divergem, 3 sem dado")
if diverge:
    raise SystemExit(1)
