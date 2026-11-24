"""
Saídas do posicionador (EDR-076, spec §6): relatório em Markdown, resultado em JSON, conjuntos de hardpoints por candidato
e a tabela-resumo `candidatos.csv`. Só formata: nada aqui calcula restrição nem muda veredito.

Cada saída diz: o rótulo `ROTULO` (VERIFIED ≠ validado; a cinemática do `kinematics_model.Corner` é MODEL e não foi
validada contra o OptimumKinematics, a REFERENCE do EDR-004), os itens A_CONFIRMAR da configuração (com a fonte), os avisos
da leitura do STEP e os SHA-256 do STEP e da configuração (o resultado fica STALE quando o CAD ou a configuração mudam).

Números em SI no JSON e nos CSVs (unidade no nome do campo); no relatório, as distâncias aparecem também em mm
(apresentação).
"""
import csv
import datetime as dt
import json
import math

import numpy as np

import hardpoints as hp
from posicionador import mecanismo as mec
from posicionador import varredura as vr

ROTULO = "VERIFIED ≠ validado; cinemática NOT_VALIDATED contra o OptimumKinematics (REFERENCE, EDR-004)"
STALE = ("O resultado vale só para o STEP e a configuração com os SHA-256 acima: se um deles mudar, o resultado fica "
         "STALE e a ferramenta tem de rodar de novo.")
# Textos fixos do relatório (revisão final da fase 1: I5, M5, M6).
INCERTEZA = ("Incerteza geométrica da fase 1, abaixo de 1 mm e sem margem: a transformação STEP → carro da configuração "
             "(sem esferas REF_) foi ajustada só no lado reto do FH, com erro ≤ 0,55 mm; os primitivos dos obstáculos "
             "podem deixar um furo de cobertura de até ~0,15 mm (tolerância de cobertura de 0,1 mm + deflexão da malha de "
             "0,05 mm); a folga é o mínimo nos n estados do curso (discretização em dz, convergida em n e 2n, mas sem "
             "cota entre estados). Uma folga positiva menor que isso não garante ausência de toque. A margem de fabricação "
             "δ é da fase 2 (certificador), não está nas restrições desta fase.")
POR_QUE_NAO_VIAVEL = ("Na fase 1 nenhum candidato chega a VIAVEL: a folga ao tirante é sempre parcial (raio do tirante "
                      "A_CONFIRMAR: só o eixo é conferido), a folga à manga/freio/pinça dentro do aro é sempre "
                      "NAO_VERIFICAVEL (sem RODA_ modelado) e há itens A_CONFIRMAR na configuração. O melhor veredito "
                      "possível é CONDICIONAL; ele não dispensa a conferência do que está listado abaixo.")
COLUNAS_RESUMO = ["rank", "arquivo_csv", "veredito", "origem", "variacao_MR", "MR0", "dist_no_pivo_m", "dist_no_olhal_m",
                  "angulo_fora_plano_max_rad", "menor_folga_m", "restricao_menor_folga", "pivo_X_m", "pivo_Y_m",
                  "pivo_Z_m", "r1_m", "r2_m", "resolucoes", "motivo"]


# ------------------------------------------------------------------ conversão para JSON
def para_json(x):
    """numpy → tipos do JSON; não finito → texto ("inf", "-inf", "nan"), porque o JSON não tem infinito."""
    if isinstance(x, dict):
        return {str(k): para_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [para_json(v) for v in x]
    if isinstance(x, np.ndarray):
        return para_json(x.tolist())
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return x if math.isfinite(x) else str(x)
    return x


def restricao_dict(r):
    return {"nome": r.nome, "estado": r.estado, "valor": r.valor, "limite": r.limite, "folga": r.folga,
            "origem": r.origem, "fonte": r.fonte, "motivo": r.motivo, "completa": r.completa}


def avaliacao_dict(av):
    return {"veredito": av.veredito, "motivo": av.motivo, "n": av.n, "resolucoes": list(av.resolucoes),
            "dist_no_m": dict(av.dist_no_m), "restricoes": [restricao_dict(r) for r in av.restricoes],
            "curvas": {k: v for k, v in av.curvas.items()}}


def pontos_atuacao(hs):
    """{Point_ID: [X_m, Y_m, Z_m]} do grupo pushrod do canto FL."""
    return {f"FL_{k}": hs.points[f"FL_{k}"].xyz for k in hp.PUSH_KEYS if f"FL_{k}" in hs.points}


def variaveis_dict(v):
    if v is None:
        return None
    return {"pivo_m": v.pivo_m, "az_rad": v.az_rad, "el_rad": v.el_rad, "r1_m": v.r1_m, "phi_b_rad": v.phi_b_rad}


def candidato_dict(c, rank=None, arquivos=None):
    d = {"rank": rank, "origem": c.origem, "violacao_max_normalizada": c.violacao,
         "variaveis": variaveis_dict(c.variaveis), "r2_m": None if c.construcao is None else c.construcao.r2_m,
         "pontos_m": None if c.construcao is None or c.construcao.hardpoints is None
         else pontos_atuacao(c.construcao.hardpoints), "avaliacao": avaliacao_dict(c.avaliacao)}
    if arquivos:
        d.update(arquivo_csv=arquivos[0], arquivo_meta=arquivos[1])
    return d


def diagnostico_dict(f):
    if f is None:
        return None
    return {"motivo": f.motivo, "n_amostras": f.n_amostras, "n_com_resultado": f.n_com_resultado, "falhas": f.falhas,
            "violacoes": f.violacoes, "conflitos": [{"a": a, "b": b, "fracao": x} for a, b, x in f.conflitos],
            "melhor": None if f.melhor is None else candidato_dict(f.melhor)}


# ------------------------------------------------------------------ hardpoints por candidato
def conjunto_do_candidato(c, rank, contexto):
    """HardpointSet do candidato (todos os pontos PROVISIONAL), com sufixo no geometry_rev e procedência no source."""
    base = c.construcao.hardpoints
    meta = dict(base.meta)
    rev = str(base.meta["geometry_rev"])
    rev = rev[:-len(mec.SUFIXO_REV)] if rev.endswith(mec.SUFIXO_REV) else rev     # um sufixo só (o do candidato)
    meta["geometry_rev"] = f"{rev} + atuação do posicionador, candidato {rank:02d}"
    meta["source"] = (f"posicionador EDR-076 (tools/posicionar_atuacao.py), candidato {rank:02d}, veredito "
                      f"{c.avaliacao.veredito}, semente {contexto.get('semente')}; STEP sha256 "
                      f"{contexto.get('step_sha256') or 'sem STEP'}; configuração sha256 {contexto['config_sha256']}; "
                      f"{ROTULO}. Base: {base.meta.get('source', '')}")
    meta["timestamp"] = contexto["data"]
    pts = {k: hp.Point(np.array(p.xyz, dtype=float), p.component, "PROVISIONAL") for k, p in base.points.items()}
    return hp.HardpointSet(meta=meta, points=pts)


def _menor_folga(av):
    rs = [r for r in av.restricoes if isinstance(r.folga, (int, float)) and r.estado != "NAO_VERIFICAVEL"
          and r.nome.startswith("folga")]
    if not rs:
        return None, ""
    r = min(rs, key=lambda q: q.folga)
    return float(r.folga), r.nome


def linha_resumo(c, rank, arquivo_csv):
    av = c.avaliacao
    var = av.restricao("variação de MR")
    mr0 = av.restricao("MR(0)")
    fo = av.curvas.get("angulo_fora_do_plano_rad")
    mf, nmf = _menor_folga(av)
    p = c.variaveis.pivo_m
    return {"rank": rank, "arquivo_csv": arquivo_csv, "veredito": av.veredito, "origem": c.origem,
            "variacao_MR": None if var is None else var.valor, "MR0": None if mr0 is None else mr0.valor,
            "dist_no_pivo_m": av.dist_no_m.get("pivo"), "dist_no_olhal_m": av.dist_no_m.get("olhal"),
            "angulo_fora_plano_max_rad": None if fo is None or not len(fo) else float(np.max(fo)),
            "menor_folga_m": mf, "restricao_menor_folga": nmf, "pivo_X_m": p[0], "pivo_Y_m": p[1], "pivo_Z_m": p[2],
            "r1_m": c.variaveis.r1_m, "r2_m": c.construcao.r2_m, "resolucoes": " ".join(map(str, av.resolucoes)),
            "motivo": av.motivo or ""}


def _fmt_csv(v):
    if isinstance(v, (float, np.floating)):
        return f"{float(v):.9g}"
    return "" if v is None else str(v)


def gravar_resumo(caminho, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_RESUMO)
        w.writeheader()
        for ln in linhas:
            w.writerow({k: _fmt_csv(ln.get(k)) for k in COLUNAS_RESUMO})


def gravar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(para_json(dados), f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


# ------------------------------------------------------------------ relatório em Markdown
def _num(v, dig=4):
    if v is None:
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "sim" if v else "não"
    if isinstance(v, (tuple, list)):
        return "[" + "; ".join(_num(x, dig) for x in v) + "]"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{x:.{dig}g}" if math.isfinite(x) else str(x)


def _cel(t):
    return str(t).replace("|", "\\|").replace("\n", " ")


def tabela_restricoes(av):
    ln = ["| Restrição | Estado | Valor | Limite | Folga | Origem | Fonte | Motivo |", "|---|---|---|---|---|---|---|---|"]
    for r in av.restricoes:
        ln.append(f"| {_cel(r.nome)} | {r.estado}{'' if r.completa else ' (parcial)'} | {_num(r.valor)} | "
                  f"{_num(r.limite)} | {_num(r.folga)} | {r.origem} | {_cel(r.fonte)} | {_cel(r.motivo or '')} |")
    return ln


def _mm(v):
    return "—" if v is None else f"{float(v) * 1e3:.1f} mm"


def bloco_candidato(titulo, c):
    av = c.avaliacao
    ln = [f"### {titulo}", "", f"- Veredito: **{av.veredito}**" + (f" ({av.motivo})" if av.motivo else ""),
          f"- Resoluções da varredura (n): {av.resolucoes or [av.n]}; origem: {c.origem}"]
    if c.variaveis is not None:
        v = c.variaveis
        ln.append(f"- Pivô do rocker: ({', '.join(f'{x * 1e3:.1f}' for x in v.pivo_m)}) mm; r1 = {v.r1_m * 1e3:.1f} mm; "
                  f"r2 = {_mm(c.construcao.r2_m)}; φB = {math.degrees(v.phi_b_rad):.1f}°; azimute = "
                  f"{math.degrees(v.az_rad):.1f}°; elevação = {math.degrees(v.el_rad):.1f}°")
    ln.append(f"- Distância ao nó do chassi mais próximo: pivô {_mm(av.dist_no_m.get('pivo'))}, olhal "
              f"{_mm(av.dist_no_m.get('olhal'))} (preferência U3, não restrição)")
    mr, ls = av.curvas.get("MR [wheel/spring]"), av.curvas.get("Ls_m")
    if mr is not None and len(mr):
        ln.append(f"- Curva de MR [wheel/spring] no curso: {float(np.min(mr)):.4f} a {float(np.max(mr)):.4f}; "
                  f"comprimento do amortecedor: {float(np.min(ls)) * 1e3:.2f} a {float(np.max(ls)) * 1e3:.2f} mm "
                  "(curvas completas no resultado.json)")
    if c.construcao is not None and c.construcao.hardpoints is not None:
        ln.append("- Pontos da atuação (m, ISO 8855, canto FL): " + "; ".join(
            f"{k} = ({', '.join(f'{x:.4f}' for x in p)})" for k, p in pontos_atuacao(c.construcao.hardpoints).items()))
    ln += ["", *tabela_restricoes(av), ""]
    return ln


def _avaliacoes(ctx):
    """Avaliações citadas no relatório (v20, candidatos ou melhor da Fase I)."""
    if ctx.get("cand_v20") is not None:
        return [ctx["cand_v20"].avaliacao]
    res = ctx.get("resultado")
    if res is None:
        return []
    out = [c.avaliacao for c in res.candidatos]
    if res.fase1 is not None and res.fase1.melhor is not None:
        out.append(res.fase1.melhor.avaliacao)
    return out


def alertas_regulamento(avaliacoes):
    """Alertas que independem da atuação: o chassi sozinho bloqueia o gabarito T.1.2 (o carro reprova T.1.2)."""
    for av in avaliacoes:
        r = av.restricao("gabarito T.1.2")
        if r is not None and (r.motivo or "").startswith(vr.MOTIVO_CHASSI_BLOQUEIA):
            return ["**ATENÇÃO: o chassi sozinho (obstáculos fixos, sem a atuação) bloqueia o gabarito T.1.2. O carro "
                    "reprova o T.1.2 independentemente de onde a atuação ficar; a restrição sai NAO_VERIFICAVEL nos "
                    "candidatos porque a atuação não é a causa.**"]
    return []


def markdown(ctx):
    """Relatório completo. `ctx`: dicionário montado pela ferramenta (ver tools/posicionar_atuacao.py)."""
    cfg = ctx["cfg"]
    ln = ["# Posicionador da atuação dianteira — relatório", "",
          f"> {ROTULO}. Os vereditos (VIAVEL, CONDICIONAL, INVIAVEL) dizem só se as restrições da configuração foram "
          "cumpridas no modelo; não aprovam nem validam peça.", "",
          f"- Data: {ctx['data']}; modo: `{ctx['modo']}`; comando: `{ctx['comando']}`",
          f"- Configuração: `{ctx['config']}` (SHA-256 `{ctx['config_sha256']}`)",
          f"- Hardpoints de base: `{ctx['hardpoints']}` (SHA-256 `{ctx['hardpoints_sha256']}`)"]
    if ctx.get("step"):
        ln.append(f"- STEP: `{ctx['step']}` (SHA-256 `{ctx['step_sha256']}`)")
        ln.append(f"- Referencial STEP → carro: {ctx['referencial']}")
    else:
        ln.append("- STEP: **nenhum** (sem `--step`): a cena tem só o aro; chassi e peças fixas não foram conferidos "
                  "(folga aos fixos NAO_VERIFICAVEL)")
    if ctx.get("caixa"):
        lo, hi = ctx["caixa"]
        ln.append(f"- Caixa de busca do pivô (m): mín ({', '.join(f'{x:.4f}' for x in lo)}), máx "
                  f"({', '.join(f'{x:.4f}' for x in hi)}); {ctx['caixa_origem']}")
    ln += ["", STALE, ""]
    alertas = alertas_regulamento(_avaliacoes(ctx))
    if alertas:
        ln += [*alertas, ""]
    ln += ["## Limites desta fase", "", f"- {POR_QUE_NAO_VIAVEL}", f"- {INCERTEZA}", ""]

    if ctx["modo"] == "avaliar-v20":
        ln += ["## Avaliação da v20 (script de atuação)", "",
               f"Conjunto `{ctx['v20']}`, avaliado como está (sem construção), com a varredura convergida e a restrição "
               "do olhal da busca.", ""]
        ln += bloco_candidato("v20", ctx["cand_v20"])
    else:
        res = ctx["resultado"]
        est = res.estatisticas
        ln += ["## Busca", "",
               f"- Amostras: {est.get('n_amostras')}; refinos: {est.get('n_refinos', 0)}; semente: {ctx['semente']}; "
               f"pontos da grade do mapa: {est.get('n_pontos_grade')} ({est.get('n_pontos_livres')} livres para o pivô)",
               f"- Falhas nas amostras: {est.get('falhas', {})}",
               f"- Viáveis rápidos: {est.get('n_viaveis_rapidos', 0)}; finalistas reavaliados: {est.get('n_finalistas', 0)};"
               f" viáveis convergidos: {est.get('n_viaveis', 0)}; tempo da busca: {est.get('tempo_s', 0.0):.1f} s", ""]
        if res.candidatos:
            ln += ["## Candidatos", "",
                   "Ordem: VIAVEL antes de CONDICIONAL; depois variação de MR, distância ao nó (pivô + olhal) e ângulo "
                   "fora do plano. Cada um tem um conjunto de hardpoints `candidato_NN.csv` + `.meta.json` (Status "
                   "PROVISIONAL); a tabela-resumo é `candidatos.csv`.", ""]
            for k, c in enumerate(res.candidatos, start=1):
                ln += bloco_candidato(f"Candidato {k:02d} (`candidato_{k:02d}.csv`)", c)
        else:
            f1 = res.fase1
            ln += ["## Fase I (nenhum candidato viável)", "", f"- {f1.motivo}",
                   f"- Amostras com resultado: {f1.n_com_resultado} de {f1.n_amostras}; falhas: {f1.falhas}", "",
                   "### Pares de restrições que mais violam juntas (fração das amostras com resultado)", ""]
            ln += [f"- {a} × {b}: {x:.3f}" for a, b, x in f1.conflitos] or ["- (nenhum par)"]
            ln += ["", "### Fração das amostras em que cada restrição é violada", ""]
            ln += [f"- {k}: {x:.3f}" for k, x in f1.violacoes.items()] or ["- (nenhuma)"]
            ln.append("")
            if f1.melhor is not None:
                ln += bloco_candidato("Melhor candidato (menor violação máxima normalizada, reavaliado)", f1.melhor)
        if ctx.get("figuras"):
            ln += ["## Figuras", "", *[f"- `{f}`" for f in ctx["figuras"]], ""]

    ln += ["## Itens A_CONFIRMAR da configuração", "",
           "Cada um desliga a verificação correspondente (o veredito fica no máximo CONDICIONAL).", ""]
    ln += [f"- `{n}`: {cfg.item(n).fonte}" for n in cfg.a_confirmar()] or ["- (nenhum)"]
    hip = sorted(n for n, it in cfg.itens.items() if it.origem == "HIPOTESE")
    ln += ["", "## Itens HIPOTESE da configuração", ""]
    ln += [f"- `{n}`: {cfg.item(n).fonte}" for n in hip] or ["- (nenhum)"]
    ln += ["", "## Avisos da leitura do STEP", ""]
    ln += [f"- {_cel(a)}" for a in ctx.get("avisos_step", [])] or ["- (nenhum)" if ctx.get("step") else "- (sem STEP)"]
    ln += ["", "## O que não está modelado", ""]
    ln += [f"- {_cel(a)}" for a in ctx.get("nao_modelado", [])] or ["- (nada declarado)"]
    ln += ["", "## Avisos da ferramenta", ""]
    ln += [f"- {_cel(a)}" for a in ctx.get("avisos", [])] or ["- (nenhum)"]
    ln.append("")
    return "\n".join(ln)


def agora():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
