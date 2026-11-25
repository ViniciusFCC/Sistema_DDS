"""
Regra de obstáculos do adaptador do Fusion (fase 2, posicionador): decide, a partir do portão de identificação, quais
componentes do CAD entram na colisão com a atuação.

Regra (usuário, 2026-11-24, "em tese"): o que está `IGNORAR` e é dianteiro mas fica fora do cálculo vira obstáculo; o
traseiro segue ignorado (versão só da dianteira). "Fora do cálculo" = que não é o objeto da busca (a atuação v20: atuação,
rockers, push rods, amortecedores) nem o gabarito T.1.2 (que o regulamento já trata). Pela tabela
`docs/posicionador/fusion/TABELA-ignorados-2026-11-24.md` a regra não promove nenhum item no T11 atual; o adaptador lista a
cada execução o que ela promoveu, para que uma peça dianteira nova com nome `IGNORAR_` não vire obstáculo sem aviso.

Categorias usadas como obstáculo sem regra: CHASSI e FIXO (as de `identificacao.CATEGORIAS_USADAS` que são fixas no
referencial do carro; as bandejas, rodas e tirantes são móveis e ficam fora da varredura da fase 1).
Só biblioteca padrão.
"""
from dataclasses import dataclass, field

from posicionador import reconhecimento as rc

CATEGORIAS_FIXAS = ("CHASSI", "FIXO")
# Trechos de nome (normalizado) do que a busca posiciona ou o regulamento trata: não é obstáculo. Lidos da tabela de
# 2026-11-24; a decisão final sobre cada nome é do usuário.
OBJETO_DA_BUSCA = ("ATUACAO", "ROCKER", "PUSHROD", "PUSH_ROD", "AMORTECEDOR", "GABARITO")
# Limite entre dianteiro e traseiro no eixo X do carro (mm; eixo dianteiro em X ≈ 0, traseira em −1309 a −1830).
# HIPOTESE: um componente cuja caixa começa atrás disto e termina na frente é "misto" (dianteiro e traseiro juntos).
X_DIVISA_MM = -500.0


@dataclass
class Decisao:
    componente: str
    categoria: str
    destino: str          # "obstaculo" | "promovido" | "ignorado" | "misto"
    motivo: str
    caixa_carro_mm: "list | None" = None
    n_corpos: int = 0


@dataclass
class Classificacao:
    decisoes: list = field(default_factory=list)

    def nomes(self, *destinos):
        return [d.componente for d in self.decisoes if d.destino in destinos]

    @property
    def obstaculos(self):
        """Componentes cujos corpos entram na cena: os fixos e os promovidos."""
        return self.nomes("obstaculo", "promovido")

    @property
    def promovidos(self):
        return [d for d in self.decisoes if d.destino == "promovido"]

    @property
    def mistos(self):
        return [d for d in self.decisoes if d.destino == "misto"]


def _normalizado(nome):
    return rc.normalizar(nome)


def _decidir_ignorado(linha):
    nome = linha["componente"]
    caixa = linha.get("caixa_carro_mm")
    base = dict(componente=nome, categoria="IGNORAR", caixa_carro_mm=caixa, n_corpos=linha["n_corpos"])
    norm = _normalizado(nome)
    if linha["n_corpos"] == 0:
        return Decisao(destino="ignorado", motivo="vazio (sem corpo)", **base)
    if "TRAS" in norm:
        return Decisao(destino="ignorado", motivo="traseiro: ignorado na versão só da dianteira", **base)
    if caixa is not None and caixa[0][0] < X_DIVISA_MM <= caixa[1][0]:
        return Decisao(destino="misto", motivo=(f"dianteiro e traseiro no mesmo componente (X de {caixa[0][0]:.0f} a "
                                                f"{caixa[1][0]:.0f} mm; divisa {X_DIVISA_MM:.0f} mm): decidido por corpo "
                                                "(`decidir_corpo`), sem mudar o CAD"), **base)
    achou = [p for p in OBJETO_DA_BUSCA if p in norm]
    if achou:
        return Decisao(destino="ignorado", motivo=f"objeto da busca ou do regulamento ({', '.join(achou)}): não é obstáculo", **base)
    if caixa is not None and caixa[1][0] < X_DIVISA_MM:
        return Decisao(destino="ignorado", motivo="atrás da divisa dianteiro/traseiro (sem TRAS no nome): tratado como traseiro", **base)
    return Decisao(destino="promovido", motivo="dianteiro, fora do cálculo e fora do objeto da busca: promovido a obstáculo", **base)


def decidir_corpo(nomes, caixa_carro_mm):
    """Destino de UM corpo de um componente misto: ("ignorado" | "promovido", motivo). `nomes` = textos do corpo e da
    ocorrência que o contém; `caixa_carro_mm` = ([x, y, z] mín, máx) no referencial do carro. Atrás da divisa: traseiro,
    ignorado. À frente: se algum nome casa com o objeto da busca, ignorado; senão, promovido a obstáculo."""
    if caixa_carro_mm[1][0] < X_DIVISA_MM:
        return "ignorado", "traseiro (atrás da divisa)"
    achou = sorted({p for n in nomes for p in OBJETO_DA_BUSCA if p in _normalizado(n)})
    if achou:
        return "ignorado", f"objeto da busca ou do regulamento ({', '.join(achou)})"
    return "promovido", "dianteiro, fora do cálculo e fora do objeto da busca"


def classificar(res):
    """`res` = `identificacao.Resultado` (já sem FALHA). Devolve a `Classificacao` de todos os componentes de 1º nível
    CHASSI, FIXO ou IGNORAR; os demais (bandejas, rodas, tirantes, REF, HP) não são obstáculos fixos."""
    out = Classificacao()
    caixas = {t["componente"]: t for t in res.tabela_componentes}
    for nome, r in res.reconhecimento.items():
        if r.categoria in CATEGORIAS_FIXAS:
            t = caixas.get(nome, {})
            out.decisoes.append(Decisao(nome, r.categoria, "obstaculo", f"categoria {r.categoria}: obstáculo fixo",
                                        t.get("caixa_carro_mm"), t.get("n_corpos", 0)))
    for linha in res.tabela_ignorados:
        out.decisoes.append(_decidir_ignorado(linha))
    return out


def texto(cl):
    """Linhas de relatório: o que a regra promoveu, o que ficou misto e o que foi ignorado (a cada execução)."""
    L = []
    prom = cl.promovidos
    L.append(f"Promovidos pela regra a obstáculo: {len(prom)}" + ("" if not prom else " — " + ", ".join(d.componente for d in prom)))
    for d in cl.mistos:
        L.append(f"MISTO (decidido por corpo): {d.componente}: {d.motivo}")
    for d in cl.decisoes:
        if d.destino == "ignorado":
            L.append(f"ignorado: {d.componente} ({d.n_corpos} corpos): {d.motivo}")
    return L
