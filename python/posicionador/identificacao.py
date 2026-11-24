"""
Verificação da identificação dos componentes do CAD por GEOMETRIA, independente do nome (posicionador, fase 2).

O reconhecimento por nome (`reconhecimento.py`) diz a que categoria o nome pertence. Isto aqui confere se a geometria
confirma: lado (esquerda = +Y, direita = −Y no referencial do carro, ISO 8855), contagem de peças por categoria, esferas
`REF_`/`HP_` (raio, lado, simetria), o que está sendo IGNORADO e nomes aninhados em conflito. Todo achado é `FALHA`
(bloqueia: `Resultado.ok` falso) ou `AVISO` (informa, não bloqueia). Nada é corrigido nem adivinhado.

Entrada: a etapa `geometria_por_componente` do script `T11_sondagem` (mm, coordenadas do CAD):
    {"topos": {"<componente de 1º nível>:1": {"ocorrencias": [{"caminho", "profundidade", "nome",
                "corpos": [{"nome", "isSolid", "min_mm", "max_mm", "esfera": {"centro_mm", "raio_mm"}}]}]}}}
O referencial do carro vem das esferas `REF_ORIGEM`, `REF_X`, `REF_Y` (mesma construção de `cad_step`: origem, X para
REF_X, Y para REF_Y por Gram-Schmidt, Z = X × Y). Só biblioteca padrão.

Limites conhecidos (não verificados aqui): a posição do centro da caixa envolvente decide o lado (peça muito próxima do
plano central dá `FALHA` por ambiguidade); o que é obstáculo de verdade (`IGNORAR` correto ou não) só pode ser decidido
pelo usuário olhando `tabela_ignorados`; as contagens esperadas são as de uma suspensão de duplo A por roda dianteira.
"""
import math
from dataclasses import dataclass, field

from . import reconhecimento as rc

# Contagem esperada de componentes de 1º nível por categoria (duplo A: 2 bandejas por lado; 1 roda por lado; 1 tirante
# de direção por lado). CHASSI: pelo menos 1. REF e HP: exatamente 1 componente cada.
CONTAGEM_ESPERADA = {"BANDEJA_FE": 2, "BANDEJA_FD": 2, "RODA_FE": 1, "RODA_FD": 1, "DIR": 2, "REF": 1, "HP": 1}
CATEGORIAS_USADAS = ("CHASSI", "FIXO", "RODA_FE", "RODA_FD", "BANDEJA_FE", "BANDEJA_FD", "DIR")  # entram na colisão
PALAVRAS_CHASSI = ("CHASSI", "TUBO", "BRACE", "FRAME")  # substrings do nome normalizado
REF_DIST_MM, REF_TOL_DIST_MM, REF_TOL_ANG_GRAUS = 100.0, 0.5, 0.1
RAIO_ESFERA_MM, TOL_RAIO_MM = 2.5, 0.05
MARGEM_LADO_MM = 20.0
TOL_ESPELHO_MM = 0.5


@dataclass(frozen=True)
class Achado:
    gravidade: str      # FALHA | AVISO
    codigo: str
    componente: str
    mensagem: str


@dataclass
class Resultado:
    achados: list = field(default_factory=list)
    reconhecimento: dict = field(default_factory=dict)   # nome → Reconhecimento
    tabela_componentes: list = field(default_factory=list)
    tabela_ignorados: list = field(default_factory=list)

    @property
    def falhas(self):
        return [a for a in self.achados if a.gravidade == "FALHA"]

    @property
    def avisos(self):
        return [a for a in self.achados if a.gravidade == "AVISO"]

    @property
    def ok(self):
        return not self.falhas

    def codigos(self, gravidade=None):
        return sorted({a.codigo for a in self.achados if gravidade in (None, a.gravidade)})


# --- vetores ---------------------------------------------------------------------------------------------------------
def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def _norm(a):
    return math.sqrt(_dot(a, a))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _unit(a):
    n = _norm(a)
    return [x / n for x in a]


def _corpos_do_topo(dados):
    return [c for o in dados["ocorrencias"] for c in o["corpos"]]


def _caixa(corpos):
    """(min, max) da união das caixas envolventes, ou None se não houver corpo."""
    if not corpos:
        return None
    lo = [min(c["min_mm"][i] for c in corpos) for i in range(3)]
    hi = [max(c["max_mm"][i] for c in corpos) for i in range(3)]
    return lo, hi


def _centro(caixa):
    lo, hi = caixa
    return [(lo[i] + hi[i]) / 2 for i in range(3)]


def _normalizado(s):
    return rc.normalizar(s)


# --- referencial -----------------------------------------------------------------------------------------------------
def referencial(geo, rec, achados):
    """(origem, [ex, ey, ez]) a partir das esferas REF_, ou None (e FALHA em `achados`)."""
    nomes_ref = [n for n, r in rec.items() if r.categoria == "REF"]
    if len(nomes_ref) != 1:
        return None  # a contagem é reportada em outro lugar
    esf = {}
    for c in _corpos_do_topo(geo["topos"][nomes_ref[0]]):
        if "esfera" in c:
            esf[c["nome"]] = c["esfera"]["centro_mm"]
    falta = [k for k in ("REF_ORIGEM", "REF_X", "REF_Y") if k not in esf]
    if falta:
        achados.append(Achado("FALHA", "REF", nomes_ref[0], f"esferas ausentes: {falta}"))
        return None
    o = esf["REF_ORIGEM"]
    vx, vy = _sub(esf["REF_X"], o), _sub(esf["REF_Y"], o)
    ok = True
    for nome, v in (("REF_X", vx), ("REF_Y", vy)):
        if abs(_norm(v) - REF_DIST_MM) > REF_TOL_DIST_MM:
            achados.append(Achado("FALHA", "REF", nomes_ref[0],
                                  f"|{nome} − REF_ORIGEM| = {_norm(v):.3f} mm; esperado {REF_DIST_MM:.1f} ± {REF_TOL_DIST_MM} mm"))
            ok = False
    if ok:
        ang = math.degrees(math.acos(max(-1.0, min(1.0, _dot(vx, vy) / (_norm(vx) * _norm(vy))))))
        if abs(ang - 90.0) > REF_TOL_ANG_GRAUS:
            achados.append(Achado("FALHA", "REF", nomes_ref[0], f"ângulo REF_X–REF_Y = {ang:.3f}°; esperado 90° ± {REF_TOL_ANG_GRAUS}°"))
            ok = False
    if not ok:
        return None
    ex = _unit(vx)
    ey0 = vy
    ey = _unit([ey0[i] - _dot(ey0, ex) * ex[i] for i in range(3)])
    return o, [ex, ey, _cross(ex, ey)]


def _para_carro(p, quadro):
    o, (ex, ey, ez) = quadro
    d = _sub(p, o)
    return [_dot(d, ex), _dot(d, ey), _dot(d, ez)]


# --- verificação -----------------------------------------------------------------------------------------------------
def _lado_esperado(nome, categoria):
    if categoria and categoria.endswith("_FE"):
        return "FE"
    if categoria and categoria.endswith("_FD"):
        return "FD"
    return rc.lado_do_nome(nome)


def _confere_lado(lado, y):
    """None se a posição confirma o lado; senão a descrição do problema."""
    if lado == "FE" and y > MARGEM_LADO_MM:
        return None
    if lado == "FD" and y < -MARGEM_LADO_MM:
        return None
    return f"o nome/categoria diz lado {lado} (esquerda = +Y, direita = −Y) mas o centro está em Y = {y:.1f} mm do carro"


def verificar(geo, mapa=None):
    """Roda todas as checagens. `geo` = etapa `geometria_por_componente`; `mapa` = decisões do usuário (reconhecimento)."""
    res = Resultado()
    achados = res.achados
    topos = geo["topos"]
    rec = {n: rc.reconhecer(n, mapa) for n in topos}
    res.reconhecimento = rec

    # 1. nomes: o que não é exata/normalizada/mapa bloqueia (a decisão é do usuário, no mapa)
    for n, r in rec.items():
        if not r.usavel:
            sug = f" (sugestão: {r.categoria})" if r.categoria else f" (o leitor de STEP o trataria como {r.padrao_se_ignorado})"
            achados.append(Achado("FALHA", "IDENT-NOME", n, f"nome não reconhecido com certeza{sug}: {r.motivo}; decidir no mapa de componentes"))

    # 2. referencial
    quadro = referencial(geo, rec, achados)
    if quadro is None and not any(a.codigo == "REF" for a in achados):
        achados.append(Achado("FALHA", "REF", "-", "não há exatamente um componente da categoria REF; sem referencial não dá para verificar os lados"))

    # 3. contagens
    contagem = {}
    for n, r in rec.items():
        if r.categoria:
            contagem[r.categoria] = contagem.get(r.categoria, 0) + 1
    for cat, esperado in CONTAGEM_ESPERADA.items():
        if contagem.get(cat, 0) != esperado:
            achados.append(Achado("FALHA", "CONTAGEM", cat, f"{contagem.get(cat, 0)} componente(s) da categoria {cat}; esperado {esperado}"))
    if contagem.get("CHASSI", 0) < 1:
        achados.append(Achado("FALHA", "CONTAGEM", "CHASSI", "nenhum componente da categoria CHASSI"))
    dir_lados = sorted(str(_lado_esperado(n, r.categoria)) for n, r in rec.items() if r.categoria == "DIR")
    if contagem.get("DIR", 0) == 2 and dir_lados != ["FD", "FE"]:
        achados.append(Achado("FALHA", "CONTAGEM", "DIR", f"os 2 componentes DIR deveriam ser um de cada lado (FE e FD); lados pelo nome: {dir_lados}"))

    # 4. por componente de 1º nível: corpos, lado, tabela
    for n, r in rec.items():
        dados = topos[n]
        corpos = _corpos_do_topo(dados)
        caixa = _caixa(corpos)
        usada = r.categoria in CATEGORIAS_USADAS
        linha = {"componente": n, "categoria": r.categoria, "nivel": r.nivel, "n_corpos": len(corpos),
                 "n_ocorrencias": len(dados["ocorrencias"]), "y_centro_mm": None}
        if caixa is None:
            achados.append(Achado("FALHA" if usada else "AVISO", "SEM-CORPO", n, "componente sem nenhum corpo no modelo"))
        elif quadro is not None:
            lo = _para_carro(caixa[0], quadro)
            hi = _para_carro(caixa[1], quadro)
            centro = _para_carro(_centro(caixa), quadro)
            linha["y_centro_mm"] = round(centro[1], 1)
            linha["caixa_carro_mm"] = [[round(min(lo[i], hi[i]), 1) for i in range(3)], [round(max(lo[i], hi[i]), 1) for i in range(3)]]
            lado = _lado_esperado(n, r.categoria)
            if lado:
                problema = _confere_lado(lado, centro[1])
                if problema:
                    achados.append(Achado("FALHA" if usada else "AVISO", "LADO", n, problema))
        res.tabela_componentes.append(linha)

    # 5. esferas HP_ e REF_
    for n, r in rec.items():
        if r.categoria not in ("HP", "REF"):
            continue
        esferas = []
        for c in _corpos_do_topo(topos[n]):
            if "esfera" not in c:
                achados.append(Achado("FALHA", "ESFERA", n, f"corpo {c['nome']!r} não é uma esfera (1 face esférica)"))
                continue
            raio = c["esfera"]["raio_mm"]
            if abs(raio - RAIO_ESFERA_MM) > TOL_RAIO_MM:
                achados.append(Achado("FALHA", "ESFERA", n, f"{c['nome']}: raio {raio:.3f} mm; esperado {RAIO_ESFERA_MM} ± {TOL_RAIO_MM} mm"))
            esferas.append((c["nome"], c["esfera"]["centro_mm"]))
        if r.categoria == "REF":
            nomes = sorted(e[0] for e in esferas)
            if nomes != ["REF_ORIGEM", "REF_X", "REF_Y"]:
                achados.append(Achado("FALHA", "REF", n, f"esferas {nomes}; esperado exatamente REF_ORIGEM, REF_X e REF_Y"))
            continue
        por_chave = {"FL": {}, "FR": {}}
        for nome, centro in esferas:
            partes = nome.split("_", 2)  # HP, FL|FR, chave
            if len(partes) < 3 or partes[0] != "HP" or partes[1] not in por_chave:
                achados.append(Achado("FALHA", "HP-NOME", n, f"esfera {nome!r} fora do padrão HP_FL_<chave> / HP_FR_<chave>"))
                continue
            lado, chave = ("FE" if partes[1] == "FL" else "FD"), partes[2]
            if quadro is not None:
                p = _para_carro(centro, quadro)
                problema = _confere_lado(lado, p[1])
                if problema:
                    achados.append(Achado("FALHA", "HP-LADO", nome, problema))
                por_chave[partes[1]][chave] = p
            else:
                por_chave[partes[1]][chave] = centro
        if len(por_chave["FL"]) != len(por_chave["FR"]):
            achados.append(Achado("AVISO", "HP-ESPELHO", n, f"{len(por_chave['FL'])} esferas FL e {len(por_chave['FR'])} FR"))
        for chave, pe in por_chave["FL"].items():
            pd = por_chave["FR"].get(chave)
            if pd is None:
                achados.append(Achado("AVISO", "HP-ESPELHO", n, f"HP_FL_{chave} sem par HP_FR_{chave}"))
            elif quadro is not None and (abs(pe[0] - pd[0]) > TOL_ESPELHO_MM or abs(pe[2] - pd[2]) > TOL_ESPELHO_MM
                                         or abs(pe[1] + pd[1]) > TOL_ESPELHO_MM):
                achados.append(Achado("AVISO", "HP-ESPELHO", n, f"par {chave} não é espelho em Y: FL={[round(x, 1) for x in pe]} FR={[round(x, 1) for x in pd]} mm"))

    # 6. o que está sendo ignorado
    for n, r in rec.items():
        if r.categoria != "IGNORAR":
            continue
        # Nome de COMPONENTE/ocorrência com palavra de chassi bloqueia; nome de CORPO só avisa (no T11 real, o corpo
        # TUBO_CARBONO_16x13 do pushrod é um tubo de carbono do pushrod, não do chassi: nome de corpo é fraco demais).
        nomes_estruturais = [n] + [o["nome"] for o in topos[n]["ocorrencias"]]
        nomes_corpos = [c["nome"] for c in _corpos_do_topo(topos[n])]
        achou = sorted({p for nm in nomes_estruturais for p in PALAVRAS_CHASSI if p in _normalizado(nm)})
        achou_corpos = sorted({p for nm in nomes_corpos for p in PALAVRAS_CHASSI if p in _normalizado(nm)})
        traseira = "TRAS" in _normalizado(n)
        if achou:
            achados.append(Achado("AVISO" if traseira else "FALHA", "IGNORAR-CHASSI", n,
                                  f"componente IGNORAR com nome de chassi/tubos ({achou})"
                                  + ("; é traseira, que o T11 ignora de propósito: confirmar" if traseira else "")))
        if achou_corpos:
            achados.append(Achado("AVISO", "IGNORAR-CORPO-SUSPEITO", n,
                                  f"corpo(s) com nome de chassi/tubo dentro de componente IGNORAR ({achou_corpos}): conferir se não é parte do chassi"))
        linha = next(t for t in res.tabela_componentes if t["componente"] == n)
        res.tabela_ignorados.append({"componente": n, "n_corpos": linha["n_corpos"], "caixa_carro_mm": linha.get("caixa_carro_mm"),
                                     "nomes_de_chassi": achou, "corpos_suspeitos": achou_corpos})

    # 7. nomes aninhados
    for n, r in rec.items():
        for o in topos[n]["ocorrencias"]:
            if o["profundidade"] < 1:
                continue
            rn = rc.reconhecer(o["nome"], mapa)
            lado = rc.lado_do_nome(o["nome"])
            caixa = _caixa(o["corpos"])
            if lado and caixa is not None and quadro is not None:
                problema = _confere_lado(lado, _para_carro(_centro(caixa), quadro)[1])
                if problema:
                    achados.append(Achado("AVISO" if r.categoria == "IGNORAR" else "FALHA", "LADO-ANINHADO", o["caminho"], problema))
            if rn.usavel and rn.categoria not in (None, "IGNORAR", r.categoria):
                achados.append(Achado("AVISO", "ANINHADO-CONFLITO", o["caminho"],
                                      f"o nome de {o['nome']!r} diz {rn.categoria}, mas o componente de 1º nível é {r.categoria}"))
    return res


def relatorio_md(res):
    """Texto Markdown curto: veredito, achados e a tabela do que é ignorado (para o usuário revisar)."""
    L = [f"**Veredito: {'OK (nenhuma falha)' if res.ok else 'BLOQUEADO (' + str(len(res.falhas)) + ' falha(s))'}**; "
         f"{len(res.avisos)} aviso(s).", ""]
    for a in res.achados:
        L.append(f"- {a.gravidade} `{a.codigo}` {a.componente}: {a.mensagem}")
    L += ["", "| Componente | Categoria | Nível | Corpos | Y do centro (mm) |", "|---|---|---|---|---|"]
    for t in res.tabela_componentes:
        L.append(f"| {t['componente']} | {t['categoria']} | {t['nivel']} | {t['n_corpos']} | {t['y_centro_mm']} |")
    return "\n".join(L)
