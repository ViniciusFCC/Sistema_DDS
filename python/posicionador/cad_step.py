"""
Leitor de STEP do posicionador (EDR-076, TC-POS-020 a 024): montagem, prefixos, tubos, nós, esferas e obstáculos.

Porte endurecido do `step_tubos.py` da pesquisa da geometria (`docs/posicionador/pesquisa/relatorio-geo.md`):
- A estrutura da montagem (NEXT_ASSEMBLY_USAGE_OCCURRENCE, ITEM_DEFINED_TRANSFORMATION, SHAPE_REPRESENTATION_RELATIONSHIP)
  é lida do texto do STEP; cada sólido (MANIFOLD_SOLID_BREP / BREP_WITH_VOIDS) é transferido sozinho pelo OpenCascade
  (`STEPControl_Reader.TransferOne`) e movido com a matriz da ocorrência. O XCAF não é usado na leitura (segfault ao ler
  sub-shapes com nome no binding, relatório §1).
- Categoria pelo prefixo do componente de primeiro nível (spec §3.2): `CHASSI_`, `FIXO_`, `RODA_FE_`, `RODA_FD_`,
  `BANDEJA_FE_`, `BANDEJA_FD_`, `DIR_`, `REF_`, `HP_`, `IGNORAR_` (maiúsculas, sensível a caixa). Sem prefixo → `FIXO`,
  com um aviso por componente. Corpo direto na raiz (sem componente) é classificado pelo prefixo do próprio nome do
  corpo; sem prefixo → `FIXO`, com aviso. Os nomes são decodificados (`\\X\\E1` → á) antes de ler o prefixo.
- Unidades: o arquivo tem de estar em mm (o contrário é `ErroSTEP`); as classificações de face trabalham em mm, dentro
  da leitura, e tudo o que sai deste módulo está em m (SI).
- Nenhuma transformação do carro fica aqui: o referencial vem das esferas `REF_` (`referencial`) ou, sem elas, da
  configuração (tarefa posterior).

Os limiares de reconhecimento de tubo (constantes `_..._MM`) são parâmetros do método da pesquisa da geometria, não dado
do carro. Requer `cadquery-ocp` (extra opcional `cad`: `uv sync --extra cad`); sem ele, `OCP_DISPONIVEL` é False e
`ler_step` levanta `ErroSTEP`.
"""
import math
import re
from dataclasses import dataclass, field

import numpy as np

from posicionador.geometria import Caixa, Capsula

try:
    import OCP.STEPControl  # noqa: F401  (só a presença do pacote)
    OCP_DISPONIVEL = True
except ImportError:          # extra opcional "cad" não instalado
    OCP_DISPONIVEL = False

MM = 1e-3                    # m por mm (conversão só na leitura)

# Prefixos do componente de primeiro nível (documento "Exportação do CAD (.step) para o posicionador da atuação — T11",
# 2026-11-17; spec §3.2). Os mais longos primeiro não são necessários (nenhum é prefixo de outro), mas a ordem é fixa.
PREFIXOS = (("CHASSI_", "CHASSI"), ("FIXO_", "FIXO"), ("RODA_FE_", "RODA_FE"), ("RODA_FD_", "RODA_FD"),
            ("BANDEJA_FE_", "BANDEJA_FE"), ("BANDEJA_FD_", "BANDEJA_FD"), ("DIR_", "DIR"), ("REF_", "REF"),
            ("HP_", "HP"), ("IGNORAR_", "IGNORAR"))
CATEGORIAS = tuple(c for _, c in PREFIXOS)

# Referencial das esferas REF_ (brief da Task 3; spec §3.3): distância nominal e tolerâncias.
REF_DIST_M = 0.100
REF_TOL_DIST_M = 0.0005
REF_TOL_ANG_GRAUS = 0.1

# Parâmetros do método de reconhecimento (relatório da geometria §3 e §4; mm, dentro da leitura do STEP).
_R_TUBO_MIN_MM = 9.0         # cilindro convexo com R >= 9 mm é parede externa de tubo (furo de Ø8 não conta)
_TOL_R_MM = 0.02             # tolerância de raio para juntar faces do mesmo tubo
_SEP_FACES_MM = (8.0, 60.0)  # separação de faces opostas que formam um tubo quadrado
_PASSO_MEMBRO_MM = 2.0       # passo do teste "dentro do sólido" ao longo do eixo de um tubo quadrado
_TOL_PONTA_MM = 1e-3         # precisão da bisseção das pontas dos membros de tubo quadrado
_DEFLEXAO_MM = 0.05          # deflexão linear da malha (OBB, extensão das caixas e conferência de cobertura)
_MEIA_MIN_MM = 0.5           # meia-dimensão mínima de uma OBB degenerada (decisão do controlador)
_TOL_COBERTURA_M = 1e-4      # ponto da malha fora da união dos primitivos por mais que isto → OBB de reserva
_PASSO_ARCO_GRAUS = 5.0      # discretização das dobras (corda; erro < 0,15 mm para R 135)


class ErroSTEP(RuntimeError):
    """STEP que não pode ser lido com segurança (OCP ausente, unidade não suportada, estrutura não reconhecida)."""


class ErroReferencial(ValueError):
    """Esferas REF_ ausentes, fora da distância nominal ou não ortogonais."""


@dataclass
class Peca:
    nome_componente: str      # produto de primeiro nível sob a raiz (para corpo direto na raiz: o nome da raiz)
    nome_corpo: str           # nome do sólido no STEP ou, sem nome, o do produto que o contém
    categoria: str
    shape: object             # TopoDS_Shape do OCP, já na posição da montagem (mm, coordenadas do STEP)
    ocorrencia: str = ""      # caminho das ocorrências, ex.: "FH:1" ou "REF_REFERENCIAS:1/REF_X:1"
    step_id: int = 0
    _classe: dict = field(default=None, repr=False, compare=False)


@dataclass
class Montagem:
    pecas: list
    avisos: list
    caminho: str = ""


@dataclass
class Tubo:
    nome: str
    pontos_eixo_m: np.ndarray  # (k, 3), polilinha do eixo (dobras discretizadas)
    r_ext_m: float             # raio externo (tubo quadrado: meia largura)
    secao: str                 # "redonda" | "quadrada"


@dataclass
class No:
    pos_m: np.ndarray
    n_ramos: int
    triangulado: bool
    tubos: list = field(default_factory=list)
    espalhamento_m: float = 0.0


# ================================================================== 1. texto do STEP
_RE_STR = re.compile(r"'(?:[^']|'')*'")
_RE_ESC = re.compile(r"\\\\|\\X\\([0-9A-Fa-f]{2})|\\X2\\((?:[0-9A-Fa-f]{4})+)\\X0\\|\\X4\\((?:[0-9A-Fa-f]{8})+)\\X0\\"
                     r"|\\S\\(.)|\\P[A-I]\\")
_RE_NUM = re.compile(r"[-+]?\d+\.?\d*(?:[Ee][-+]?\d+)?")


def decodificar(s):
    """Decodifica um literal de STEP (sem as aspas): '' → ', \\X\\HH (Latin-1), \\X2\\…\\X0\\ (UTF-16), \\X4\\ e \\S\\."""
    s = s.replace("''", "'")

    def sub(m):
        if m.group(0) == "\\\\":
            return "\\"
        if m.group(1):
            return bytes([int(m.group(1), 16)]).decode("latin-1")
        if m.group(2):
            return bytes.fromhex(m.group(2)).decode("utf-16-be")
        if m.group(3):
            return bytes.fromhex(m.group(3)).decode("utf-32-be")
        if m.group(4):
            return chr(ord(m.group(4)) + 128)
        return ""
    return _RE_ESC.sub(sub, s)


def _entidades(caminho):
    """dict id → texto da entidade. Separa as instruções por ';' fora de literais e remove as quebras de linha (que
    não fazem parte do conteúdo no ISO 10303-21)."""
    with open(caminho, encoding="latin-1") as f:
        texto = f.read()
    if "DATA;" not in texto:
        raise ErroSTEP(f"{caminho}: seção DATA ausente (não é um STEP ISO 10303-21)")
    dados = texto.split("DATA;", 1)[1]
    E = {}
    for m in re.finditer(r"((?:'(?:[^']|'')*'|[^';])*);", dados):
        inst = m.group(1).replace("\r", "").replace("\n", "").strip()
        if inst.startswith("ENDSEC"):
            break
        mm = re.match(r"#(\d+)\s*=\s*(.*)$", inst, re.S)
        if mm:
            E[int(mm.group(1))] = mm.group(2).strip()
    return E


def _fecha(txt, i):
    """Índice do ')' que fecha o '(' em txt[i], pulando literais."""
    prof, k = 0, i
    while k < len(txt):
        c = txt[k]
        if c == "'":
            k = _RE_STR.match(txt, k).end()
            continue
        if c == "(":
            prof += 1
        elif c == ")":
            prof -= 1
            if prof == 0:
                return k
        k += 1
    raise ErroSTEP(f"entidade mal formada: {txt[:80]}")


def _args(txt, i=None):
    """Argumentos de primeiro nível de `NOME(a, b, (c, d), 'e')` → ['a', 'b', '(c, d)', "'e'"] (o '(' em txt[i] ou o
    primeiro do texto)."""
    i = txt.index("(") if i is None else i
    f = _fecha(txt, i)
    out, prof, ini, k = [], 0, i + 1, i + 1
    while k < f:
        c = txt[k]
        if c == "'":
            k = _RE_STR.match(txt, k).end()
            continue
        if c == "(":
            prof += 1
        elif c == ")":
            prof -= 1
        elif c == "," and prof == 0:
            out.append(txt[ini:k].strip())
            ini = k + 1
        k += 1
    out.append(txt[ini:f].strip())
    return out


_RE_SUB = re.compile(r"\s*(\w+)\s*\(")


def _partes(txt):
    """Entidade simples ou complexa → {TIPO: [argumentos]}."""
    if not txt.startswith("("):
        m = _RE_SUB.match(txt)
        return {m.group(1): _args(txt, m.end() - 1)} if m else {}
    out, k = {}, 1
    while True:
        m = _RE_SUB.match(txt, k)
        if m is None:
            return out
        out[m.group(1)] = _args(txt, m.end() - 1)
        k = _fecha(txt, m.end() - 1) + 1


def _ref(a):
    m = re.fullmatch(r"#(\d+)", a.strip())
    return int(m.group(1)) if m else None


def _refs(txt):
    return [int(x) for x in re.findall(r"#(\d+)", _RE_STR.sub("''", txt))]


def _str(a):
    a = a.strip()
    return decodificar(a[1:-1]) if a.startswith("'") and a.endswith("'") else ""


def _tipo(E, i):
    t = E.get(i, "")
    m = re.match(r"(\w+)\s*\(", t)
    return m.group(1) if m else ("(complexa)" if t.startswith("(") else "")


def _vetor(E, i):
    return np.array([float(x) for x in _RE_NUM.findall(_RE_STR.sub("''", _args(E[i])[1]))])


def _posicionamento(E, i):
    """AXIS2_PLACEMENT_3D → matriz 4×4 (colunas: ref_direction, axis × ref_direction, axis; origem)."""
    a = _args(E[i])
    p = _vetor(E, _ref(a[1]))
    z = _vetor(E, _ref(a[2])) if len(a) > 2 and _ref(a[2]) else np.array([0.0, 0.0, 1.0])
    x = _vetor(E, _ref(a[3])) if len(a) > 3 and _ref(a[3]) else np.array([1.0, 0.0, 0.0])
    z = z / np.linalg.norm(z)
    x = x - (x @ z) * z
    x = x / np.linalg.norm(x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, np.cross(z, x), z, p
    return M


def _conferir_unidade(E, caminho):
    """Toda LENGTH_UNIT usada em GLOBAL_UNIT_ASSIGNED_CONTEXT tem de ser SI_UNIT(.MILLI.,.METRE.)."""
    usadas = set()
    for v in E.values():
        if "GLOBAL_UNIT_ASSIGNED_CONTEXT" in v:
            p = _partes(v).get("GLOBAL_UNIT_ASSIGNED_CONTEXT")
            if p:
                usadas.update(_refs(p[0]))
    achou = False
    for u in usadas:
        p = _partes(E.get(u, ""))
        if "LENGTH_UNIT" not in p:
            continue
        achou = True
        si = p.get("SI_UNIT")
        if si is None or si[0].strip() != ".MILLI." or si[1].strip() != ".METRE.":
            raise ErroSTEP(f"{caminho}: unidade de comprimento não suportada (#{u} = {E[u]}); o leitor espera mm")
    if not achou:
        raise ErroSTEP(f"{caminho}: unidade de comprimento não encontrada")


# ================================================================== 2. montagem
def _montagem(E, caminho, avisos):
    """Ocorrências da árvore: lista de dicts {pd, M (4×4, local → raiz, mm), primeiro (nome do produto de 1º nível ou
    None para a raiz), raiz (nome), caminho (ocorrências), solidos [(id, nome)]}."""
    tipos = {k: _tipo(E, k) for k in E}

    def nome_pd(pd):
        a = _args(E[pd])
        form = _ref(a[2])
        prod = _ref(_args(E[form])[2]) if form in E else None
        if prod in E and tipos[prod] == "PRODUCT":
            pa = _args(E[prod])
            return _str(pa[1]) or _str(pa[0])
        return _str(a[1]) or _str(a[0])

    pds = [k for k, t in tipos.items() if t == "PRODUCT_DEFINITION"]
    nomes = {pd: nome_pd(pd) for pd in pds}
    rep_do_pd = {}
    for k, t in tipos.items():
        if t == "SHAPE_DEFINITION_REPRESENTATION":
            a = _args(E[k])
            pds_ = _ref(a[0])
            alvo = _ref(_args(E[pds_])[2]) if pds_ in E else None
            if alvo in nomes:
                rep_do_pd[alvo] = _ref(a[1])
    # ligações sem transformação entre representações (ex.: SHAPE_REPRESENTATION ↔ ADVANCED_BREP_SHAPE_REPRESENTATION)
    lig, rel_transf = {}, {}
    for k, v in E.items():
        if tipos[k] != "SHAPE_REPRESENTATION_RELATIONSHIP" and not (v.startswith("(") and
                                                                     "REPRESENTATION_RELATIONSHIP" in v):
            continue
        p = _partes(v)
        rr = p.get("REPRESENTATION_RELATIONSHIP") or p.get("SHAPE_REPRESENTATION_RELATIONSHIP")
        if not rr or len(rr) < 4:
            continue
        r1, r2 = _ref(rr[2]), _ref(rr[3])
        if "REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION" in p:
            rel_transf[k] = (r1, r2, _ref(p["REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION"][0]))
        else:
            lig.setdefault(r1, set()).add(r2)
            lig.setdefault(r2, set()).add(r1)

    def grupo(rep):
        vistos, pilha = set(), [rep]
        while pilha:
            r = pilha.pop()
            if r in vistos or r is None:
                continue
            vistos.add(r)
            pilha.extend(lig.get(r, ()))
        return vistos

    def solidos(pd):
        out = []
        for rep in sorted(grupo(rep_do_pd.get(pd))):
            if rep not in E:
                continue
            for p in _partes(E[rep]).values():
                if len(p) < 2 or not p[1].startswith("("):
                    continue
                for it in _refs(p[1]):
                    t = tipos.get(it, "")
                    if t in ("MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS"):
                        out.append((it, _str(_args(E[it])[0])))
                    elif t in ("SHELL_BASED_SURFACE_MODEL", "MAPPED_ITEM", "FACETED_BREP", "GEOMETRIC_CURVE_SET"):
                        avisos.append(f"{nomes[pd]}: item #{it} ({t}) não é sólido B-rep e foi ignorado")
        return sorted(set(out))

    # filhos de cada produto, com a transformação local (filho → pai)
    filhos, nauo_com_transf = {}, set()
    for k, t in tipos.items():
        if t != "CONTEXT_DEPENDENT_SHAPE_REPRESENTATION":
            continue
        a = _args(E[k])
        rel, pds_ = _ref(a[0]), _ref(a[1])
        nauo = _ref(_args(E[pds_])[2])
        if tipos.get(nauo) != "NEXT_ASSEMBLY_USAGE_OCCURRENCE" or rel not in rel_transf:
            raise ErroSTEP(f"{caminho}: ocorrência #{k} sem NEXT_ASSEMBLY_USAGE_OCCURRENCE ou transformação reconhecida")
        an = _args(E[nauo])
        pai, filho = _ref(an[3]), _ref(an[4])
        r1, r2, idt = rel_transf[rel]
        if tipos.get(idt) != "ITEM_DEFINED_TRANSFORMATION":
            raise ErroSTEP(f"{caminho}: transformação #{idt} ({tipos.get(idt)}) não suportada")
        ai = _args(E[idt])
        P1, P2 = _posicionamento(E, _ref(ai[2])), _posicionamento(E, _ref(ai[3]))
        g = grupo(rep_do_pd.get(filho))
        if r1 in g:
            M = P2 @ np.linalg.inv(P1)
        elif r2 in g:
            M = P1 @ np.linalg.inv(P2)
        else:
            raise ErroSTEP(f"{caminho}: a transformação #{rel} não liga a representação do filho {nomes.get(filho)}")
        nome_occ = _str(an[1]) or _str(an[0])
        filhos.setdefault(pai, []).append((nome_occ, filho, M))
        nauo_com_transf.add(nauo)
    for k, t in tipos.items():
        if t == "NEXT_ASSEMBLY_USAGE_OCCURRENCE" and k not in nauo_com_transf:
            an = _args(E[k])
            filhos.setdefault(_ref(an[3]), []).append((_str(an[1]) or _str(an[0]), _ref(an[4]), np.eye(4)))
            avisos.append(f"ocorrência {_str(an[1])} sem transformação no STEP: tomada como identidade")
    usados = {f for lst in filhos.values() for _, f, _ in lst}
    raizes = [pd for pd in pds if pd not in usados]
    if not raizes:
        raise ErroSTEP(f"{caminho}: nenhuma raiz de montagem")
    if len(raizes) > 1:
        avisos.append(f"{len(raizes)} raízes de montagem no STEP: {', '.join(nomes[r] for r in raizes)}")
    occ = []

    def visitar(pd, M, primeiro, raiz, cam, prof):
        if prof > 32:
            raise ErroSTEP(f"{caminho}: montagem com mais de 32 níveis (ciclo?)")
        occ.append(dict(pd=pd, M=M, primeiro=primeiro, raiz=raiz, caminho=cam, nome=nomes[pd], solidos=solidos(pd)))
        for nome_occ, f, Ml in filhos.get(pd, []):
            visitar(f, M @ Ml, primeiro if primeiro is not None else nomes[f], raiz,
                    nome_occ if not cam else f"{cam}/{nome_occ}", prof + 1)
    for r in raizes:
        visitar(r, np.eye(4), None, nomes[r], "", 0)
    return occ


def _categoria(nome):
    for pref, cat in PREFIXOS:
        if nome.startswith(pref):
            return cat
    return None


def ler_step(caminho):
    """Lê o STEP (mm) e devolve a `Montagem`: uma `Peca` por sólido de cada ocorrência, já na posição da montagem."""
    if not OCP_DISPONIVEL:
        raise ErroSTEP("cadquery-ocp ausente: instale o extra opcional com `uv sync --extra cad`")
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.Interface import Interface_Static
    from OCP.STEPControl import STEPControl_Reader

    caminho = str(caminho)
    avisos = []
    E = _entidades(caminho)
    _conferir_unidade(E, caminho)
    occ = _montagem(E, caminho, avisos)
    r = STEPControl_Reader()
    Interface_Static.SetCVal_s("xstep.cascade.unit", "MM")
    if r.ReadFile(caminho) != IFSelect_RetDone:
        raise ErroSTEP(f"{caminho}: o OpenCascade não leu o arquivo")
    modelo = r.StepModel()
    cache, pecas, avisados = {}, [], set()
    for o in occ:
        for sid, nome_solido in o["solidos"]:
            if sid not in cache:
                n = modelo.NextNumberForLabel(f"#{sid}", 0, False)
                if n <= 0 or not r.TransferOne(n):
                    raise ErroSTEP(f"{caminho}: falha ao transferir o sólido #{sid}")
                cache[sid] = r.Shape(r.NbShapes())
            M = o["M"]
            t = gp_Trsf()
            t.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
            shape = BRepBuilderAPI_Transform(cache[sid], t, True).Shape()
            nome_corpo = nome_solido or o["nome"]
            if o["primeiro"] is None:                       # corpo direto na raiz: prefixo do próprio corpo
                comp, cat = o["raiz"], _categoria(nome_corpo)
                if cat is None:
                    cat = "FIXO"
                    avisos.append(f"corpo '{nome_corpo}' direto na raiz '{comp}' sem prefixo de categoria: tratado "
                                  f"como FIXO")
                ocorr = o["raiz"]
            else:
                comp, cat = o["primeiro"], _categoria(o["primeiro"])
                if cat is None:
                    cat = "FIXO"
                    if comp not in avisados:
                        avisados.add(comp)
                        avisos.append(f"componente '{comp}' sem prefixo de categoria: tratado como FIXO")
                ocorr = o["caminho"]
            pecas.append(Peca(comp, nome_corpo, cat, shape, ocorr, sid))
    return Montagem(pecas, avisos, caminho)


# ================================================================== 3. faces e sólidos (OCP, mm)
def _v3(p):
    return np.array([p.X(), p.Y(), p.Z()])


def _faces(shape):
    """Faces do sólido: tipo e parâmetros (coordenadas da montagem, mm)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepLProp import BRepLProp_SLProps
    from OCP.BRepTools import BRepTools
    from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Sphere, GeomAbs_Torus
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    out = []
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face(ex.Current())
        a = BRepAdaptor_Surface(f)
        ty = a.GetType()
        u0, u1, v0, v1 = BRepTools.UVBounds_s(f)
        rev = f.Orientation() == TopAbs_REVERSED
        d = dict(u=(u0, u1), v=(v0, v1))
        if ty == GeomAbs_Cylinder:
            c = a.Cylinder()
            ax = c.Axis()
            d.update(tipo="cil", R=c.Radius(), p=_v3(ax.Location()), d=_v3(ax.Direction()))
        elif ty == GeomAbs_Torus:
            c = a.Torus()
            ax, pos = c.Axis(), c.Position()
            d.update(tipo="toro", Rmaj=c.MajorRadius(), rmin=c.MinorRadius(), c=_v3(ax.Location()),
                     n=_v3(ax.Direction()), xdir=_v3(pos.XDirection()), ydir=_v3(pos.YDirection()))
        elif ty == GeomAbs_Plane:
            ax = a.Plane().Axis()
            d.update(tipo="plano", p=_v3(ax.Location()), n=_v3(ax.Direction()) * (-1.0 if rev else 1.0))
        elif ty == GeomAbs_Sphere:
            s = a.Sphere()
            d.update(tipo="esfera", c=_v3(s.Location()), R=s.Radius())
        else:
            d.update(tipo=f"outro{int(ty)}")
        um, vm = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        pr = BRepLProp_SLProps(a, um, vm, 1, 1e-6)
        nn = _v3(pr.Normal()) if pr.IsNormalDefined() else np.zeros(3)
        d.update(pt=_v3(a.Value(um, vm)), nrm=-nn if rev else nn)
        if d["tipo"] in ("cil", "toro"):
            d["convexa"] = bool(_convexa(d))
        out.append(d)
        ex.Next()
    return out


def _vertices(shape):
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_VERTEX
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    pts = []
    ex = TopExp_Explorer(shape, TopAbs_VERTEX)
    while ex.More():
        pts.append(_v3(BRep_Tool.Pnt_s(TopoDS.Vertex(ex.Current()))))
        ex.Next()
    return np.unique(np.round(np.array(pts), 6), axis=0) if pts else np.zeros((0, 3))


def _malha(shape):
    """Triangulação do sólido (mm), com deflexão linear `_DEFLEXAO_MM`: (nós (N, 3), triângulos (T, 3, 3))."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    BRepMesh_IncrementalMesh(shape, _DEFLEXAO_MM, False, 0.2, True)
    pts, tris = [], []
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(TopoDS.Face(ex.Current()), loc)
        if tri is not None:
            tr = loc.Transformation()
            base = len(pts)
            for i in range(1, tri.NbNodes() + 1):
                pts.append(_v3(tri.Node(i).Transformed(tr)))
            for i in range(1, tri.NbTriangles() + 1):
                tris.append([base + j - 1 for j in tri.Triangle(i).Get()])
        ex.Next()
    pts = np.array(pts) if pts else np.zeros((0, 3))
    return pts, (pts[np.array(tris)] if tris else np.zeros((0, 3, 3)))


def _convexa(f):
    """Face cilíndrica/toroidal convexa (parede externa de tubo) ou côncava (parede interna, boca de lobo)."""
    P, N = f["pt"], f["nrm"]
    if f["tipo"] == "cil":
        w = P - f["p"]
        rad = w - (w @ f["d"]) * f["d"]
    else:
        w = P - f["c"]
        w = w - (w @ f["n"]) * f["n"]
        rad = P - (f["c"] + f["Rmaj"] * w / np.linalg.norm(w))
    return rad @ N > 0


def _coaxial(a, b, tol_ang=1e-7, tol_d=0.05):
    if abs(abs(a["d"] @ b["d"]) - 1) > tol_ang:
        return False
    w = b["p"] - a["p"]
    return np.linalg.norm(w - (w @ a["d"]) * a["d"]) < tol_d


def _linha_linha(p1, d1, p2, d2):
    """Pontos mais próximos entre duas retas infinitas (None se paralelas) e os parâmetros (s, t)."""
    w = p1 - p2
    a, b, c, d, e = d1 @ d1, d1 @ d2, d2 @ d2, d1 @ w, d2 @ w
    den = a * c - b * b
    if abs(den) < 1e-9 * a * c:
        return None, None, None
    s = (b * e - c * d) / den
    t = (a * e - b * d) / den
    return p1 + s * d1, p2 + t * d2, (s, t)


def _dist_pt_seg(p, a, b):
    d = b - a
    s = np.clip((p - a) @ d / (d @ d), 0, 1)
    q = a + s * d
    return np.linalg.norm(p - q), q


def _tubo_de_cilindros(faces, R_ext):
    """Faces cilíndricas convexas de raio R_ext → trechos retos coaxiais {p0, p1, d, L} (extensão pelo parâmetro v)."""
    cil = [f for f in faces if f["tipo"] == "cil" and abs(f["R"] - R_ext) < _TOL_R_MM and f["convexa"]]
    grupos = []
    for f in cil:
        for g in grupos:
            if _coaxial(g[0], f):
                g.append(f)
                break
        else:
            grupos.append([f])
    trechos = []
    for g in grupos:
        d, p = g[0]["d"], g[0]["p"]
        ts = [((f["p"] + v * f["d"]) - p) @ d for f in g for v in f["v"]]
        t0, t1 = min(ts), max(ts)
        if t1 - t0 < 1.0:          # meia face de 0,1 a 0,6 mm no canto vivo (solda em meia-esquadria)
            continue
        trechos.append(dict(p0=p + t0 * d, p1=p + t1 * d, d=d, L=t1 - t0))
    return trechos


def _dobras(faces, R_ext):
    """Faces toroidais convexas de raio menor R_ext (dobras): centro, normal, raio de dobra, ângulo e extremos."""
    out = []
    for f in faces:
        if f["tipo"] != "toro" or abs(f["rmin"] - R_ext) > _TOL_R_MM or not f["convexa"]:
            continue
        u0, u1 = f["u"]
        ends = [f["c"] + f["Rmaj"] * (np.cos(u) * f["xdir"] + np.sin(u) * f["ydir"]) for u in (u0, u1)]
        out.append(dict(c=f["c"], n=f["n"], Rmaj=f["Rmaj"], ang=u1 - u0, a=ends[0], b=ends[1]))
    return out


def _encadear(trechos, dobras, R, tol=1.0):
    """Encadeia trechos retos: por dobra, ponta com ponta ou canto vivo (retas a < 0,5 mm perto das duas pontas).
    Devolve (ordem, juntas, fechado); `ordem` pode não cobrir todos os trechos (o chamador confere)."""
    n = len(trechos)
    lig = {}

    def liga(a, b, info):
        lig.setdefault(a, []).append((b, info))
        lig.setdefault(b, []).append((a, info))

    def ponta(i, k):
        return trechos[i]["p0"] if k == 0 else trechos[i]["p1"]
    for j, d in enumerate(dobras):
        la = [(i, k) for i in range(n) for k in (0, 1) if np.linalg.norm(ponta(i, k) - d["a"]) < tol]
        lb = [(i, k) for i in range(n) for k in (0, 1) if np.linalg.norm(ponta(i, k) - d["b"]) < tol]
        if la and lb:
            liga(la[0], lb[0], dict(tipo="dobra", idx=j))
    for i in range(n):
        for k in (0, 1):
            for i2 in range(i + 1, n):
                for k2 in (0, 1):
                    if (i, k) in lig or (i2, k2) in lig:
                        continue
                    p, q = ponta(i, k), ponta(i2, k2)
                    if np.linalg.norm(p - q) < tol:
                        liga((i, k), (i2, k2), dict(tipo="continuo", p=0.5 * (p + q)))
                        continue
                    a, b, _ = _linha_linha(trechos[i]["p0"], trechos[i]["d"], trechos[i2]["p0"], trechos[i2]["d"])
                    if a is not None and np.linalg.norm(a - b) < 0.5:
                        X = 0.5 * (a + b)
                        if np.linalg.norm(X - p) < 2 * R + 2 and np.linalg.norm(X - q) < 2 * R + 2:
                            liga((i, k), (i2, k2), dict(tipo="canto_vivo", p=X))
    livres = [(i, k) for i in range(n) for k in (0, 1) if (i, k) not in lig]
    fechado = not livres
    ini = livres[0] if livres else (0, 0)
    ordem, juntas, usados, cur = [], [], set(), ini
    while True:
        i, k = cur
        if i in usados:
            break
        usados.add(i)
        t = trechos[i]
        ordem.append(dict(t, orig=i) if k == 0 else dict(p0=t["p1"], p1=t["p0"], d=-t["d"], L=t["L"], orig=i))
        sai = (i, 1 - k)
        nx = [x for x in lig.get(sai, []) if x[0][0] not in usados]
        if not nx:
            if fechado:
                fim = [x for x in lig.get(sai, []) if x[0][0] == ordem[0]["orig"]]
                if fim:
                    juntas.append(fim[0][1])
            break
        juntas.append(nx[0][1])
        cur = nx[0][0]
    return ordem, juntas, fechado


# três direções de raio fora de qualquer plano notável (paridade por maioria: robusto a raio que passa numa aresta)
_RAIOS = np.array([[0.5773, 0.5779, 0.5767], [-0.6011, 0.2987, 0.7413], [0.3119, -0.8402, 0.4436]])


def _dentro_malha(tris, P):
    """P (N, 3) mm → True se o ponto está dentro do sólido: paridade das interseções de raios com a triangulação
    fechada (Möller–Trumbore vetorizado), por maioria de três direções. Substitui o `BRepClass3d_SolidClassifier`
    do script de origem (lento em faces B-spline); o erro de forma é a deflexão da malha (`_DEFLEXAO_MM`)."""
    P = np.atleast_2d(P)
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    votos = np.zeros(len(P), dtype=int)
    for d in _RAIOS:
        h = np.cross(d, e2)
        a = np.einsum("ij,ij->i", e1, h)
        ok = np.abs(a) > 1e-12
        f = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
        s = P[:, None, :] - v0[None, :, :]
        u = f * np.einsum("nij,ij->ni", s, h)
        q = np.cross(s, e1[None, :, :])
        v = f * (q @ d)
        t = f * np.einsum("nij,ij->ni", q, e2)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        votos += hit.sum(axis=1) % 2
    return votos >= 2


def _membros_planos(tris, planos, vtx):
    """Corpo só de planos (tubo quadrado/retangular, inteiro ou em quadro): planos-médios dos pares de faces opostas
    (material entre elas, separação em `_SEP_FACES_MM`) → eixos candidatos = interseção de planos-médios
    perpendiculares → o eixo vale onde os 4 pontos de parede (0,3 mm para dentro das faces) estão dentro do sólido."""
    pares = []
    for i, A in enumerate(planos):
        for B in planos[i + 1:]:
            if A["n"] @ B["n"] > -0.9999:
                continue
            n = A["n"]
            s = n @ (A["p"] - B["p"])
            if _SEP_FACES_MM[0] <= s <= _SEP_FACES_MM[1]:
                pares.append(dict(n=n, mid=n @ (A["p"] + B["p"]) / 2, w=s))
    meds = []
    for p in pares:
        n = p["n"] * (1 if p["n"][np.argmax(np.abs(p["n"]))] > 0 else -1)
        mid = n @ (p["n"] * p["mid"])
        for m in meds:
            if abs(m["n"] @ n) > 0.9999 and abs(m["mid"] - mid) < 0.05:
                m["w"] = max(m["w"], p["w"])
                break
        else:
            meds.append(dict(n=n, mid=mid, w=p["w"]))
    membros, curtos = [], []
    for i, A in enumerate(meds):
        for B in meds[i + 1:]:
            if abs(A["n"] @ B["n"]) > 1e-3:
                continue
            d = np.cross(A["n"], B["n"])
            d /= np.linalg.norm(d)
            p0 = np.linalg.solve(np.array([A["n"], B["n"], d]), np.array([A["mid"], B["mid"], 0.0]))
            ts = (vtx - p0) @ d
            tt = np.arange(ts.min() - 1, ts.max() + 1 + _PASSO_MEMBRO_MM, _PASSO_MEMBRO_MM)
            a, b = A["w"] / 2 - 0.3, B["w"] / 2 - 0.3
            desl = np.array([a * A["n"], -a * A["n"], b * B["n"], -b * B["n"]])
            P = (p0 + tt[:, None] * d)[:, None, :] + desl[None, :, :]
            ok = list(_dentro_malha(tris, P.reshape(-1, 3)).reshape(len(tt), 4).all(axis=1))

            def ponta(t_in, t_out):
                """Bisseção entre um parâmetro dentro (4 pontos de parede no sólido) e um fora, até
                `_TOL_PONTA_MM`: a ponta do eixo não depende do passo da grade."""
                while abs(t_out - t_in) > _TOL_PONTA_MM:
                    tm = 0.5 * (t_in + t_out)
                    if _dentro_malha(tris, p0 + tm * d + desl).all():
                        t_in = tm
                    else:
                        t_out = tm
                return t_in
            k = 0
            while k < len(ok):
                if not ok[k]:
                    k += 1
                    continue
                j = k
                while j + 1 < len(ok) and ok[j + 1]:
                    j += 1
                t0 = ponta(tt[k], tt[k] - _PASSO_MEMBRO_MM)
                t1 = ponta(tt[j], tt[j] + _PASSO_MEMBRO_MM)
                w, L = max(A["w"], B["w"]), t1 - t0
                m = dict(p0=p0 + t0 * d, p1=p0 + t1 * d, d=d, L=L, secao=(A["w"], B["w"]), n1=A["n"], n2=B["n"])
                if L > w:
                    membros.append(m)
                elif L > 0.5 * w and not (k == 0 and j == len(ok) - 1):
                    curtos.append(m)
                k = j + 1
    # trechos curtos (0,5 w a w; ex.: perna de um U baixo) só valem se uma ponta encosta no eixo de um membro longo
    for m in curtos:
        for o in list(membros):
            if min(_dist_pt_seg(m[k], o["p0"], o["p1"])[0] for k in ("p0", "p1")) < max(m["secao"]):
                membros.append(m)
                break
    return membros


def _estender_ate_eixo(membros):
    """Membros de tubo quadrado do mesmo corpo terminam na face do outro: leva a ponta até a interseção dos eixos."""
    for m in membros:
        for k in ("p0", "p1"):
            for o in membros:
                if o is m:
                    continue
                a, b, _ = _linha_linha(m["p0"], m["d"], o["p0"], o["d"])
                if a is None or np.linalg.norm(a - b) > 0.5:
                    continue
                if np.linalg.norm(a - m[k]) < max(m["secao"]):
                    so = (a - o["p0"]) @ o["d"]
                    if -max(m["secao"]) <= so <= o["L"] + max(m["secao"]):
                        m[k] = a
        m["L"] = np.linalg.norm(m["p1"] - m["p0"])
    return membros


def _caixa_do_membro(m, malha):
    """Caixa exata do membro de tubo quadrado (mm): seção pelas faces externas; comprimento pela extensão dos nós da
    malha dentro do prisma da seção, até 1 largura além das pontas do eixo (cobre o canto externo de um quadro)."""
    d, n1, n2 = m["d"], m["n1"], m["n2"]
    w1, w2 = m["secao"]
    w = max(w1, w2)
    rel = malha - m["p0"]
    u, a, b = rel @ d, rel @ n1, rel @ n2
    sel = (np.abs(a) <= w1 / 2 + 0.1) & (np.abs(b) <= w2 / 2 + 0.1) & (u >= -w) & (u <= m["L"] + w)
    us = np.concatenate([u[sel], [0.0, m["L"]]])
    umin, umax = us.min() - _DEFLEXAO_MM, us.max() + _DEFLEXAO_MM
    centro = m["p0"] + 0.5 * (umin + umax) * d
    return centro, np.array([d, n1, n2]), np.array([0.5 * (umax - umin), w1 / 2, w2 / 2])


def _classificar(peca):
    """Tipo do corpo (mm): 'tubo_reto' e 'tubo_curvado' (redondos), 'tubo_quadrado' e 'quadro_tubo_quadrado', 'outro'.
    O resultado fica em cache na peça."""
    if peca._classe is not None:
        return peca._classe
    s = peca.shape
    faces = _faces(s)
    vtx = _vertices(s)
    malha, tris = _malha(s)
    base = dict(malha=malha)
    cilc = [f for f in faces if f["tipo"] == "cil" and f["convexa"] and f["R"] >= _R_TUBO_MIN_MM]
    if cilc:
        R = max(f["R"] for f in cilc)
        trechos, dob = _tubo_de_cilindros(faces, R), _dobras(faces, R)
        if trechos:
            base.update(secao="redonda", R=R, trechos=trechos, dobras=dob)
            if len(trechos) == 1 and not dob:
                base.update(tipo="tubo_reto")
            else:
                ordem, juntas, fechado = _encadear(trechos, dob, R)
                base.update(tipo="tubo_curvado", ordem=ordem, juntas=juntas, fechado=fechado)
            peca._classe = base
            return base
    planos = [f for f in faces if f["tipo"] == "plano"]
    so_planos = len(planos) == len(faces) - sum(1 for f in faces if f["tipo"] == "toro")
    mem = _membros_planos(tris, planos, vtx) if so_planos and planos else []
    if mem:
        mem = _estender_ate_eixo(mem)
        for m in mem:
            m["caixa"] = _caixa_do_membro(m, malha)
        base.update(tipo="tubo_quadrado" if len(mem) == 1 else "quadro_tubo_quadrado", secao="quadrada",
                    R=max(max(m["secao"]) for m in mem) / 2, membros=mem)
    else:
        base.update(tipo="outro")
    esf = [f for f in faces if f["tipo"] == "esfera"]
    if esf:
        base["esferas"] = esf
        base["n_faces"] = len(faces)
    peca._classe = base
    return base


# ================================================================== 4. eixo, tubos e nós (m)
def _rot(n, th):
    n = n / np.linalg.norm(n)
    K = np.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def _arco(d, passo_graus=_PASSO_ARCO_GRAUS):
    """Pontos (mm) da dobra discretizada de a até b."""
    c, a, b, nrm = d["c"], d["a"] - d["c"], d["b"] - d["c"], d["n"]
    ang = d["ang"]
    sgn = 1.0 if np.cross(a, b) @ nrm >= 0 else -1.0
    if np.linalg.norm(_rot(nrm, sgn * ang) @ a - b) > 0.5:
        sgn = -sgn
    n = max(2, int(np.ceil(math.degrees(ang) / passo_graus)))
    return [c + _rot(nrm, sgn * ang * k / n) @ a for k in range(n + 1)], ang / n


def _elementos(cl):
    """Elementos de eixo do corpo (mm): [(k, p, q, R, 'reto'|'arco')]."""
    out = []
    if cl["secao"] == "redonda":
        for k, t in enumerate(cl["trechos"]):
            out.append((k, t["p0"], t["p1"], cl["R"], "reto"))
        for kd, d in enumerate(cl["dobras"]):
            pts, _ = _arco(d)
            for p, q in zip(pts[:-1], pts[1:]):
                out.append((f"dobra{kd}", p, q, cl["R"], "arco"))
    else:
        for k, m in enumerate(cl["membros"]):
            out.append((k, m["p0"], m["p1"], cl["R"], "reto"))
    return out


def _pecas_fixas(montagem):
    return [p for p in montagem.pecas if p.categoria in ("CHASSI", "FIXO")]


def _nomes_unicos(pecas):
    vistos, out = {}, []
    for p in pecas:
        base = f"{p.ocorrencia}/{p.nome_corpo}"
        vistos[base] = vistos.get(base, 0) + 1
        out.append(base if vistos[base] == 1 else f"{base}#{vistos[base]}")
    return out


def _polilinha(cl):
    """Polilinha (mm) de um tubo redondo curvado encadeado; None se o encadeamento não cobre todos os trechos."""
    ordem, juntas = cl["ordem"], cl["juntas"]
    if len(ordem) != len(cl["trechos"]):
        return None
    pts = [ordem[0]["p0"], ordem[0]["p1"]]
    for k in range(1, len(ordem) + (1 if cl["fechado"] else 0)):
        nxt = ordem[k % len(ordem)]
        j = juntas[k - 1] if k - 1 < len(juntas) else None
        if j is not None and j["tipo"] == "dobra":
            arc, _ = _arco(cl["dobras"][j["idx"]])
            if np.linalg.norm(arc[0] - pts[-1]) > np.linalg.norm(arc[-1] - pts[-1]):
                arc = arc[::-1]
            pts.extend(arc)
        elif j is not None and j["tipo"] == "canto_vivo":
            pts.append(j["p"])
        if k < len(ordem):
            pts.extend([nxt["p0"], nxt["p1"]])
        else:
            pts.append(nxt["p0"])
    return np.array(pts)


def _triangulado(dirs, tol=0.05):
    """>= 3 ramos com direções não coplanares (determinante de alguma tripla > tol)."""
    if len(dirs) < 3:
        return False
    D = [d / np.linalg.norm(d) for d in dirs]
    for i in range(len(D)):
        for j in range(i + 1, len(D)):
            for k in range(j + 1, len(D)):
                if abs(np.linalg.det(np.array([D[i], D[j], D[k]]))) > tol:
                    return True
    return False


def _dist_seg_seg_pts(p1, q1, p2, q2):
    """Distância entre segmentos e os pontos mais próximos (Ericson 5.1.9)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a < 1e-18 and e < 1e-18:
        return np.linalg.norm(r), p1, p2
    if a < 1e-18:
        s, t = 0.0, np.clip(f / e, 0, 1)
    else:
        c = d1 @ r
        if e < 1e-18:
            t, s = 0.0, np.clip(-c / a, 0, 1)
        else:
            b = d1 @ d2
            den = a * e - b * b
            s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 * a * e else 0.0
            t = (b * s + f) / e
            if t < 0:
                t, s = 0.0, np.clip(-c / a, 0, 1)
            elif t > 1:
                t, s = 1.0, np.clip((b - c) / a, 0, 1)
    c1, c2 = p1 + s * d1, p2 + t * d2
    return np.linalg.norm(c1 - c2), c1, c2


def _achar_nos(el, nomes, tol_m, raio_grupo_m, janela_m):
    """Nós = encontros de eixos de corpos diferentes (ou canto vivo no mesmo corpo), em m. Cada trecho reto é estendido
    nas pontas em (R1 + R2 + tol)/sen θ (tubo cortado em boca de lobo termina na parede do outro); encontros a menos de
    `raio_grupo_m` se juntam; ramos = direções do eixo a `janela_m` do nó; triangulado = >= 3 ramos não coplanares."""
    enc = []
    for a in range(len(el)):
        ia, _, p1, q1, R1, ta = el[a]
        u1 = (q1 - p1) / np.linalg.norm(q1 - p1)
        for b in range(a + 1, len(el)):
            ib, _, p2, q2, R2, tb = el[b]
            u2 = (q2 - p2) / np.linalg.norm(q2 - p2)
            sen = np.linalg.norm(np.cross(u1, u2))
            if ia == ib and (ta != "reto" or tb != "reto" or sen < 0.09):
                continue
            e = (R1 + R2 + tol_m) / max(sen, 0.3)
            P1, Q1 = (p1 - e * u1, q1 + e * u1) if ta == "reto" else (p1, q1)
            P2, Q2 = (p2 - e * u2, q2 + e * u2) if tb == "reto" else (p2, q2)
            d, c1, c2 = _dist_seg_seg_pts(P1, Q1, P2, Q2)
            if d < tol_m:
                enc.append(dict(p=0.5 * (c1 + c2), el=(a, b), d=d))
    amostras = {}
    for i, _, p, q, _, _ in el:
        m = max(2, int(np.linalg.norm(q - p) / 0.001) + 1)
        amostras.setdefault(i, []).extend(p + np.outer(np.linspace(0, 1, m), q - p))
    amostras = {i: np.array(v) for i, v in amostras.items()}
    pai = list(range(len(enc)))

    def acha(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i
    for i in range(len(enc)):
        for j in range(i + 1, len(enc)):
            if np.linalg.norm(enc[i]["p"] - enc[j]["p"]) < raio_grupo_m:
                pai[acha(i)] = acha(j)
    grupos = {}
    for i in range(len(enc)):
        grupos.setdefault(acha(i), []).append(i)
    nos = []
    for g in grupos.values():
        P = np.mean([enc[i]["p"] for i in g], 0)
        corpos = sorted({el[e][0] for i in g for e in enc[i]["el"]})
        dirs = []
        for i in corpos:
            pts = amostras[i]
            r = np.linalg.norm(pts - P, axis=1)
            cand = pts[(r > janela_m[0]) & (r < janela_m[1])] - P
            grupos_d = []
            for v in cand:
                v = v / np.linalg.norm(v)
                for gd in grupos_d:
                    if gd[0] @ v > 0.9:
                        gd.append(v)
                        break
                else:
                    grupos_d.append([v])
            for gd in grupos_d:
                mm = np.mean(gd, 0)
                dirs.append(mm / np.linalg.norm(mm))
        nos.append(No(P, len(dirs), _triangulado(dirs), [nomes[i] for i in corpos],
                      float(max(np.linalg.norm(enc[i]["p"] - P) for i in g))))
    nos.sort(key=lambda n: (-round(n.pos_m[0] * 1000), round(n.pos_m[1] * 1000), n.pos_m[2]))
    return nos


def tubos_e_nos(montagem, tol_m=0.005, raio_grupo_m=0.0254, janela_ramos_m=(0.020, 0.045)):
    """Tubos e nós das peças `CHASSI` e `FIXO`, em coordenadas do STEP (m). Parâmetros padrão do relatório da
    geometria §4 (tolerância entre eixos 5 mm; agrupamento a 1 OD = 25,4 mm; ramos amostrados de 20 a 45 mm)."""
    pecas = _pecas_fixas(montagem)
    nomes = _nomes_unicos(pecas)
    tubos, el, nomes_el = [], [], {}
    for ip, (p, nome) in enumerate(zip(pecas, nomes)):
        cl = _classificar(p)
        if cl["tipo"] == "outro":
            continue
        R = cl["R"] * MM
        nomes_el[ip] = nome
        for k, a, b, Rr, tp in _elementos(cl):
            el.append((ip, k, a * MM, b * MM, Rr * MM, tp))
        if cl["secao"] == "redonda":
            pl = None
            if cl["tipo"] == "tubo_reto":
                pl = np.array([cl["trechos"][0]["p0"], cl["trechos"][0]["p1"]])
            else:
                pl = _polilinha(cl)
            if pl is not None:
                tubos.append(Tubo(nome, pl * MM, R, "redonda"))
            else:
                montagem.avisos.append(f"{nome}: encadeamento dos trechos incompleto; tubos por trecho e por dobra")
                for k, t in enumerate(cl["trechos"]):
                    tubos.append(Tubo(f"{nome}[{k}]", np.array([t["p0"], t["p1"]]) * MM, R, "redonda"))
                for kd, d in enumerate(cl["dobras"]):
                    tubos.append(Tubo(f"{nome}[dobra{kd}]", np.array(_arco(d)[0]) * MM, R, "redonda"))
        else:
            mem = cl["membros"]
            for k, m in enumerate(mem):
                tubos.append(Tubo(nome if len(mem) == 1 else f"{nome}[{k}]", np.array([m["p0"], m["p1"]]) * MM,
                                  max(m["secao"]) / 2 * MM, "quadrada"))
    nos = _achar_nos(el, nomes_el, tol_m, raio_grupo_m, janela_ramos_m)
    return tubos, nos


# ================================================================== 5. esferas e referencial
def esferas(montagem):
    """Centro (m, coordenadas do STEP) das esferas cujo nome de corpo começa com `REF_` ou `HP_`. Corpo com esse
    prefixo que não é uma esfera (todas as faces esféricas com o mesmo centro) é ignorado com aviso; nome repetido
    também (fica o primeiro)."""
    out = {}
    for p in montagem.pecas:
        if not p.nome_corpo.startswith(("REF_", "HP_")):
            continue
        cl = _classificar(p)
        esf = cl.get("esferas", [])
        if not esf or cl.get("n_faces") != len(esf):
            montagem.avisos.append(f"corpo '{p.nome_corpo}' com prefixo de esfera não é uma esfera: ignorado")
            continue
        cs = np.array([f["c"] for f in esf])
        if np.ptp(cs, axis=0).max() > 1e-6:
            montagem.avisos.append(f"corpo '{p.nome_corpo}': faces esféricas com centros diferentes: ignorado")
            continue
        if p.nome_corpo in out:
            montagem.avisos.append(f"esfera '{p.nome_corpo}' repetida: fica a primeira")
            continue
        out[p.nome_corpo] = cs[0] * MM
    return out


def referencial(esferas):
    """(R, t) com p_carro = R @ p_step + t: origem em REF_ORIGEM, X para REF_X, Y para REF_Y (Gram-Schmidt), Z = X × Y.
    `ErroReferencial` se faltar esfera, se |REF_X − REF_ORIGEM| ou |REF_Y − REF_ORIGEM| diferir de 0,100 m em mais de
    0,5 mm, ou se o ângulo entre eles diferir de 90° em mais de 0,1°."""
    falta = [k for k in ("REF_ORIGEM", "REF_X", "REF_Y") if k not in esferas]
    if falta:
        raise ErroReferencial(f"esferas do referencial ausentes: {', '.join(falta)}")
    O, X, Y = (np.asarray(esferas[k], dtype=float) for k in ("REF_ORIGEM", "REF_X", "REF_Y"))
    vx, vy = X - O, Y - O
    dx, dy = float(np.linalg.norm(vx)), float(np.linalg.norm(vy))
    for nome, d in (("REF_X", dx), ("REF_Y", dy)):
        if abs(d - REF_DIST_M) > REF_TOL_DIST_M:
            raise ErroReferencial(f"|{nome} − REF_ORIGEM| = {d:.6f} m medido; esperado {REF_DIST_M:.3f} m ± "
                                  f"{REF_TOL_DIST_M * 1000:.1f} mm (unidade ou escala do CAD errada?)")
    ang = math.degrees(math.acos(max(-1.0, min(1.0, float(vx @ vy) / (dx * dy)))))
    if abs(ang - 90.0) > REF_TOL_ANG_GRAUS:
        raise ErroReferencial(f"ângulo entre REF_X e REF_Y = {ang:.4f}° medido; esperado 90° ± {REF_TOL_ANG_GRAUS}°")
    ex = vx / dx
    ey = vy - (vy @ ex) * ex
    ey = ey / np.linalg.norm(ey)
    R = np.array([ex, ey, np.cross(ex, ey)])
    return R, -R @ O


# ================================================================== 6. obstáculos fixos
def _obb(shape, nome, avisos):
    """Caixa orientada (mm) do OCP (`BRepBndLib.AddOBB`, sobre a triangulação já feita em `_malha`), aumentada da
    deflexão da malha (conservadora)."""
    from OCP.Bnd import Bnd_OBB
    from OCP.BRepBndLib import BRepBndLib
    obb = Bnd_OBB()
    BRepBndLib.AddOBB_s(shape, obb, True, True, True)
    obb.Enlarge(_DEFLEXAO_MM)
    eixos = np.array([_v3(obb.XDirection()), _v3(obb.YDirection()), _v3(obb.ZDirection())])
    meias = np.array([obb.XHSize(), obb.YHSize(), obb.ZHSize()])
    if meias.min() < _MEIA_MIN_MM:
        avisos.append(f"{nome}: caixa orientada degenerada (meia-dimensão {meias.min():.3f} mm): aumentada para "
                      f"{_MEIA_MIN_MM} mm")
        meias = np.maximum(meias, _MEIA_MIN_MM)
    return Caixa(_v3(obb.Center()), eixos, meias)


def _prims_do_corpo(peca, cl, nome, avisos):
    """Primitivos (em mm) do corpo classificado."""
    if cl["tipo"] in ("tubo_reto", "tubo_curvado"):
        R = cl["R"]
        prims = [Capsula(t["p0"], t["p1"], R) for t in cl["trechos"]]
        for d in cl["dobras"]:
            pts, dth = _arco(d)
            flecha = d["Rmaj"] * (1 - math.cos(dth / 2))
            prims += [Capsula(p, q, R + flecha) for p, q in zip(pts[:-1], pts[1:])]
        return prims
    if cl["tipo"] in ("tubo_quadrado", "quadro_tubo_quadrado"):
        return [Caixa(*m["caixa"]) for m in cl["membros"]]
    return [_obb(peca.shape, nome, avisos)]


def _em_metros(prim):
    if isinstance(prim, Capsula):
        return Capsula(prim.a * MM, prim.b * MM, prim.r * MM)
    return Caixa(prim.centro * MM, prim.eixos, prim.meias * MM)


def _inflado(prim, delta):
    if isinstance(prim, Capsula):
        return Capsula(prim.a, prim.b, prim.r + delta)
    return Caixa(prim.centro, prim.eixos, prim.meias + delta)


def obstaculos_fixos(montagem, R, t):
    """Primitivos (m, referencial do carro: p = R @ p_step + t) das peças `CHASSI` e `FIXO`: tubo redondo reto →
    `Capsula`; trecho de tubo curvo → `Capsula` por corda com raio + flecha; tubo quadrado → `Caixa` exata por membro;
    demais sólidos → `Caixa` orientada (OBB do OCP).
    Conferência de cobertura (conservadora): se algum nó da malha do corpo fica fora da união dos seus primitivos por
    δ > 0,1 mm, os primitivos do corpo são aumentados de δ + deflexão da malha quando δ não passa do raio externo do
    tubo; senão o corpo vira a caixa orientada. Os dois casos geram aviso."""
    R, t = np.asarray(R, dtype=float), np.asarray(t, dtype=float)
    pecas = _pecas_fixas(montagem)
    out = []
    for p, nome in zip(pecas, _nomes_unicos(pecas)):
        cl = _classificar(p)
        prims = [_em_metros(q) for q in _prims_do_corpo(p, cl, nome, montagem.avisos)]
        nos_m = cl["malha"] * MM
        fora = float(np.min([q.sdf(nos_m) for q in prims], axis=0).max()) if len(nos_m) else 0.0
        if fora > _TOL_COBERTURA_M and cl["tipo"] != "outro":
            if fora <= cl["R"] * MM:
                delta = fora + _DEFLEXAO_MM * MM
                prims = [_inflado(q, delta) for q in prims]
                montagem.avisos.append(f"{nome}: {cl['tipo']} não cobria a malha ({fora * 1000:.2f} mm fora): "
                                       f"primitivos aumentados de {delta * 1000:.2f} mm")
            else:
                prims = [_em_metros(_obb(p.shape, nome, montagem.avisos))]
                montagem.avisos.append(f"{nome}: {cl['tipo']} não cobre a malha ({fora * 1000:.2f} mm fora): usada a "
                                       f"caixa orientada")
        out.extend(q.transformada(R, t) for q in prims)
    return out
