"""Tabela dos 24 nomes novos da V4.4 (incremento 8, parte 8b; EDR-070; aprovada pelo usuário em 2026-11-09, item A1).

A medição da V4.3 (`reescrita_nomes.medir`) achou 24 células únicas citadas por endereço nas abas 03 a 14 e sem nome:
17 da 10_TIRE (caso, lado, Fz, α, γ, κ e ε; mais as colunas de origem I11, I21 e I176), 3 da 13_VALIDATION (B37:B39) e 3 da
16_EQUILIBRIO (E188:E190). Para o invariante da §3.5 valer sem exceção, todas ganham nome.

Regras (as de `nomes_v4_0`): `<papel>_<aba2>_<slug do rótulo da coluna A>`; na 10_TIRE, as células de caso (B a F, linhas
com casos) levam `_<coluna>`; papel `ent` (sem fórmula), `org` (10_TIRE coluna I) ou `res` (fórmula); em colisão com um
nome existente da V4.3 (que não pode mudar) ou entre os novos, o nome novo leva `_<célula>`. `NOMES_V44` é a tabela
aprovada, literal; `tabela_v44` a deriva dessas regras lendo a V4.3, e o resultado tem de ser igual (o teste confere).
Os rótulos são o texto exato da coluna A da V4.3.
"""
from __future__ import annotations


from nomes_v4_0 import (COLUNAS_CASO, COLUNA_ID, NOME_VALIDO, Nome, _RE_SUS, _chave, _eh_formula, _papel_entrada,
                        _partes, _texto, parece_referencia, slug)
from raizes import nomes_definidos
import reescrita_nomes

_ORDEM_PAPEL = {"ent": 0, "org": 1, "fte": 2, "res": 3}

NOMES_V44: list[Nome] = [
    Nome('ent_10_canto_b', '10_TIRE', 'B20', 'ent', '',
         'Canto'),
    Nome('ent_10_canto_c', '10_TIRE', 'C20', 'ent', '',
         'Canto'),
    Nome('ent_10_canto_d', '10_TIRE', 'D20', 'ent', '',
         'Canto'),
    Nome('ent_10_canto_e', '10_TIRE', 'E20', 'ent', '',
         'Canto'),
    Nome('ent_10_canto_f', '10_TIRE', 'F20', 'ent', '',
         'Canto'),
    Nome('ent_10_lado_da_roda_l_esquerda_r_direita_b', '10_TIRE', 'B21', 'ent', 'SUS-501',
         'Lado da roda (L esquerda / R direita)'),
    Nome('ent_10_lado_da_roda_l_esquerda_r_direita_c', '10_TIRE', 'C21', 'ent', 'SUS-501',
         'Lado da roda (L esquerda / R direita)'),
    Nome('ent_10_lado_da_roda_l_esquerda_r_direita_d', '10_TIRE', 'D21', 'ent', 'SUS-501',
         'Lado da roda (L esquerda / R direita)'),
    Nome('ent_10_lado_da_roda_l_esquerda_r_direita_e', '10_TIRE', 'E21', 'ent', 'SUS-501',
         'Lado da roda (L esquerda / R direita)'),
    Nome('ent_10_lado_da_roda_l_esquerda_r_direita_f', '10_TIRE', 'F21', 'ent', 'SUS-501',
         'Lado da roda (L esquerda / R direita)'),
    Nome('ent_10_fz_de_09_loads_sus_104_verif_valor_fixo_f', '10_TIRE', 'F22', 'ent', 'SUS-104',
         'Fz (de 09_LOADS, SUS-104; VERIF: valor fixo)'),
    Nome('ent_10_angulo_de_deriva_alfa_iso_8855_velocidad_f', '10_TIRE', 'F23', 'ent', 'SUS-501',
         'Ângulo de deriva α (ISO 8855: + = velocidade p/ esquerda)'),
    Nome('ent_10_camber_gama_projeto_topo_para_fora_f', '10_TIRE', 'F24', 'ent', 'SUS-404',
         'Camber γ (projeto: + = topo para fora)'),
    Nome('ent_10_slip_ratio_kappa_iso_1_travada_em_frenag_f', '10_TIRE', 'F25', 'ent', 'SUS-502',
         'Slip ratio κ (ISO: −1 = travada em frenagem)'),
    Nome('ent_10_epsilon_guarda_de_divisao_por_zero_em_bx', '10_TIRE', 'B176', 'ent', 'SUS-501',
         'ε (guarda de divisão por zero em Bx, By)'),
    Nome('org_10_sistema_de_eixos_do_arquivo_declarado_sa', '10_TIRE', 'I11', 'org', '',
         'Sistema de eixos do arquivo (declarado): SAE_CALSPAN ou ISO_TYDEX'),
    Nome('org_10_lado_da_roda_l_esquerda_r_direita', '10_TIRE', 'I21', 'org', 'SUS-501',
         'Lado da roda (L esquerda / R direita)'),
    Nome('org_10_epsilon_guarda_de_divisao_por_zero_em_bx', '10_TIRE', 'I176', 'org', 'SUS-501',
         'ε (guarda de divisão por zero em Bx, By)'),
    Nome('ent_13_referencia_python_fx_do_caso_verif_n_res', '13_VALIDATION', 'B37', 'ent', 'SUS-502',
         'Referência Python — Fx do caso VERIF [N] (resultado de código)'),
    Nome('ent_13_referencia_python_fy_do_caso_verif_n_res', '13_VALIDATION', 'B38', 'ent', 'SUS-501',
         'Referência Python — Fy do caso VERIF [N] (resultado de código)'),
    Nome('ent_13_referencia_python_mu_eff_do_caso_verif_r', '13_VALIDATION', 'B39', 'ent', 'SUS-503',
         'Referência Python — μ_eff do caso VERIF (resultado de código)'),
    Nome('res_16_gradiente_de_subesterco_k_texto_de_exibi_e188', '16_EQUILIBRIO', 'E188', 'res', '',
         'Gradiente de subesterço K (texto de exibição, linear)'),
    Nome('res_16_equilibrio_no_limite_texto_de_exibicao_e189', '16_EQUILIBRIO', 'E189', 'res', '',
         'Equilíbrio no limite (texto de exibição)'),
    Nome('res_16_linha_de_apoio_saturacoes_a_y_limite_c_n_e190', '16_EQUILIBRIO', 'E190', 'res', '',
         'Linha de apoio: saturações, a_y limite, C_N, custo e Δt (spec 7.3, item 2)'),
]

# As 24 células, na ordem da tabela aprovada.
CELULAS_V44: tuple[tuple[str, str], ...] = tuple((n.aba, n.celula) for n in NOMES_V44)


def tabela_v44(wb43) -> list[Nome]:
    """Deriva a tabela dos nomes novos pelas regras de A1, lendo a V4.3 aberta em `wb43`: as células soltas medidas por
    `reescrita_nomes.medir`, na ordem (aba, papel, linha, coluna)."""
    soltas = reescrita_nomes.medir(wb43, reescrita_nomes.destinos_unicos(wb43)).soltas
    existentes = set(nomes_definidos(wb43))
    base = []
    for aba, cel in soltas:
        ws = wb43[aba]
        col, r = _partes(cel)
        rotulo = _texto(ws[f"A{r}"].value)
        papel = "res" if _eh_formula(ws[cel].value) else _papel_entrada(aba, cel)
        s = slug(rotulo)
        if s and aba == "10_TIRE" and col in COLUNAS_CASO and any(ws[f"{x}{r}"].value is not None for x in "CDEF"):
            s = f"{s}_{col.lower()}"
        textos = [_texto(ws[f"A{r}"].value), _texto(ws[f"{COLUNA_ID.get(aba, 'A')}{r}"].value)]
        ids = ";".join(dict.fromkeys(m for t in textos for m in _RE_SUS.findall(t)))
        base.append([f"{papel}_{aba[:2]}_{s}" if s else f"{papel}_{aba[:2]}_{cel.lower()}", aba, cel, papel, ids, rotulo])
    base.sort(key=lambda b: (b[1], _ORDEM_PAPEL[b[3]], *_chave(b[1], b[2])[1:]))
    contagem: dict[str, int] = {}
    for b in base:
        contagem[b[0]] = contagem.get(b[0], 0) + 1
    out = []
    for nome, aba, cel, papel, ids, rotulo in base:
        if nome in existentes or contagem[nome] > 1:
            nome = f"{nome}_{cel.lower()}"
        out.append(Nome(nome, aba, cel, papel, ids, rotulo))
    vistos: set[str] = set()
    for n in out:
        if n.nome in vistos or n.nome in existentes:
            raise ValueError(f"nome repetido ou já existente na V4.3: {n.nome}")
        if not NOME_VALIDO.fullmatch(n.nome) or parece_referencia(n.nome):
            raise ValueError(f"nome inválido para o Excel: {n.nome!r} ({n.aba}!{n.celula})")
        vistos.add(n.nome)
    return out


def conferir_tabela(tabela: list) -> None:
    """A tabela (data/nomes_V4_4.csv) tem de ser exatamente `NOMES_V44`: as trocas por nome usam esses nomes."""
    if list(tabela) != list(NOMES_V44):
        dif = sorted(n.nome for n in set(tabela) ^ set(NOMES_V44))[:5]
        raise ValueError(f"data/nomes_V4_4.csv difere de nomes_v4_4.NOMES_V44 (regrave com --saida): {dif}")


def main() -> None:
    import argparse
    from pathlib import Path

    from nomes_v4_0 import escrever_tabela
    p = argparse.ArgumentParser(description="Regrava data/nomes_V4_4.csv a partir de NOMES_V44.")
    p.add_argument("--saida", type=Path, required=True, help="CSV de saída (data/nomes_V4_4.csv)")
    a = p.parse_args()
    escrever_tabela(NOMES_V44, a.saida)
    print(f"{len(NOMES_V44)} nomes gravados em {a.saida}")


if __name__ == "__main__":
    main()
