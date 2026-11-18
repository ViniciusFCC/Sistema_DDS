"""
Testes do leitor de STEP do posicionador (EDR-076, TC-POS-020 a 024).
TC-POS-020: STEP real do chassi (data/cad/T11_chassi_2026-11-17.step): 31 corpos, 28 nós com 14 triangulados
            (tolerância de 5 mm) e simetria em Y ≤ 0,5 mm (números do docs/posicionador/pesquisa/relatorio-geo.md).
TC-POS-021: STEP SINTÉTICO gerado aqui com o OCP (XCAF, mm, nomes preservados): categorias, centros das esferas e
            referencial das esferas REF_.
TC-POS-022: STEP real sem prefixos: tudo FIXO e um aviso por componente (e por corpo direto na raiz) sem prefixo.
TC-POS-023: STEP SINTÉTICO com REF_X a 100 m (unidade errada simulada): ErroReferencial com a distância medida.
TC-POS-024: folga da Caixa do tubo quadrado SINTÉTICO nunca supera a distância exata do OCP em mais de 0,2 mm; a
            Capsula do tubo redondo SINTÉTICO bate com o OCP em 0,01 mm; no STEP real, os primitivos de todos os
            corpos cobrem a malha (nenhum aviso de cobertura).
Todas as peças, posições e dimensões dos STEPs gerados aqui são SINTÉTICAS de teste (não do carro); os STEPs vão para
uma pasta temporária, nunca para o repositório.
Precisa do extra opcional "cad" (`uv sync --extra cad`); sem ele, sai NÃO EXECUTÁVEL (código 3).
Roda como script: uv run python -X utf8 tests/test_posicionador_cad.py
"""
import math
import os
import tempfile

import numpy as np

from posicionador import cad_step as cs
from posicionador.geometria import Caixa, Capsula

if not cs.OCP_DISPONIVEL:
    print("NÃO EXECUTÁVEL: cadquery-ocp ausente (instale com `uv sync --extra cad`)")
    raise SystemExit(3)

from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut  # noqa: E402
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex  # noqa: E402
from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # noqa: E402
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeSphere  # noqa: E402
from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec  # noqa: E402
from OCP.IFSelect import IFSelect_RetDone  # noqa: E402
from OCP.Message import Message, Message_Gravity  # noqa: E402
from OCP.STEPCAFControl import STEPCAFControl_Writer  # noqa: E402
from OCP.STEPControl import STEPControl_AsIs  # noqa: E402
from OCP.TCollection import TCollection_ExtendedString  # noqa: E402
from OCP.TDataStd import TDataStd_Name  # noqa: E402
from OCP.TDocStd import TDocStd_Document  # noqa: E402
from OCP.TopLoc import TopLoc_Location  # noqa: E402
from OCP.XCAFDoc import XCAFDoc_DocumentTool  # noqa: E402

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STEP_REAL = os.path.join(RAIZ, "data", "cad", "T11_chassi_2026-11-17.step")

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name}  {detail}")


# --- STEP SINTÉTICO ------------------------------------------------------------------------------------------------
L_RED, D_RED, E_RED = 500.0, 25.4, 1.6        # tubo redondo SINTÉTICO (mm): comprimento, diâmetro externo, parede
L_QUA, W_QUA, E_QUA = 300.0, 25.0, 1.2        # tubo quadrado SINTÉTICO (mm)


def _loc(rot_eixo=None, rot_graus=0.0, trans=(0.0, 0.0, 0.0)):
    t = gp_Trsf()
    if rot_eixo is not None:
        t.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(*rot_eixo)), math.radians(rot_graus))
    tt = gp_Trsf()
    tt.SetTranslation(gp_Vec(*trans))
    return TopLoc_Location(tt.Multiplied(t))


def _trsf_de(loc):
    """Matriz 4×4 (mm) de uma TopLoc_Location."""
    t = loc.Transformation()
    M = np.eye(4)
    for i in range(3):
        for j in range(4):
            M[i, j] = t.Value(i + 1, j + 1)
    return M


def _tubo_redondo():
    ext = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), D_RED / 2, L_RED).Shape()
    inn = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-1, 0, 0), gp_Dir(1, 0, 0)), D_RED / 2 - E_RED, L_RED + 2).Shape()
    return BRepAlgoAPI_Cut(ext, inn).Shape()


def _tubo_quadrado():
    ext = BRepPrimAPI_MakeBox(gp_Pnt(0, -W_QUA / 2, -W_QUA / 2), L_QUA, W_QUA, W_QUA).Shape()
    w = W_QUA - 2 * E_QUA
    inn = BRepPrimAPI_MakeBox(gp_Pnt(-1, -w / 2, -w / 2), L_QUA + 2, w, w).Shape()
    return BRepAlgoAPI_Cut(ext, inn).Shape()


# localizações SINTÉTICAS (com rotação, para exercitar a composição das transformações e a orientação das caixas)
LOC_CHASSI = _loc((0, 0, 1), 30.0, (200.0, -100.0, 50.0))
LOC_REDONDO = _loc(None, 0.0, (0.0, 0.0, 100.0))
LOC_QUADRADO = _loc((1, 1, 0), 35.0, (50.0, 80.0, 0.0))
LOC_CAIXA = _loc((0, 1, 0), 20.0, (-300.0, 50.0, 10.0))
REF_ORIGEM_MM = (10.0, 20.0, 30.0)
HP_MM = (0.0, 600.0, 160.0)


def gravar_step_sintetico(caminho, ref_x_local_mm=(100.0, 0.0, 0.0)):
    """Montagem SINTÉTICA: CHASSI_TESTE (tubo redondo + quadrado), FIXO_CAIXA, REF_REFERENCIAS (3 esferas Ø 5 mm) e
    HP_FRENTE (esfera HP_FL_LCA_OUT), gravada em mm pelo STEPCAFControl_Writer com os nomes."""
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def nome(lab, s):
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(s))
        return lab

    def parte(shape, s):
        return nome(st.AddShape(shape, False), s)

    def montagem(s):
        return nome(st.NewShape(), s)

    def componente(pai, filho, loc, s):
        nome(st.AddComponent(pai, filho, loc), s)

    raiz = montagem("MONTAGEM_SINTETICA")
    ch = montagem("CHASSI_TESTE")
    componente(ch, parte(_tubo_redondo(), "TUBO_REDONDO"), LOC_REDONDO, "TUBO_REDONDO:1")
    componente(ch, parte(_tubo_quadrado(), "TUBO_QUADRADO"), LOC_QUADRADO, "TUBO_QUADRADO:1")
    componente(raiz, ch, LOC_CHASSI, "CHASSI_TESTE:1")
    componente(raiz, parte(BRepPrimAPI_MakeBox(100.0, 50.0, 30.0).Shape(), "FIXO_CAIXA"), LOC_CAIXA, "FIXO_CAIXA:1")
    ref = montagem("REF_REFERENCIAS")
    for n, p in (("REF_ORIGEM", (0.0, 0.0, 0.0)), ("REF_X", ref_x_local_mm), ("REF_Y", (0.0, 100.0, 0.0))):
        componente(ref, parte(BRepPrimAPI_MakeSphere(2.5).Shape(), n), _loc(None, 0.0, p), f"{n}:1")
    componente(raiz, ref, _loc(None, 0.0, REF_ORIGEM_MM), "REF_REFERENCIAS:1")
    hp = montagem("HP_FRENTE")
    componente(hp, parte(BRepPrimAPI_MakeSphere(2.5).Shape(), "HP_FL_LCA_OUT"), _loc(), "HP_FL_LCA_OUT:1")
    componente(raiz, hp, _loc(None, 0.0, HP_MM), "HP_FRENTE:1")
    st.UpdateAssemblies()
    w = STEPCAFControl_Writer()
    w.SetNameMode(True)
    if not w.Transfer(doc, STEPControl_AsIs) or w.Write(caminho) != IFSelect_RetDone:
        raise RuntimeError("falha ao gravar o STEP sintético")


def _silenciar_ocp():
    """O writer do OCP escreve mensagens de progresso no stdout; só falhas passam."""
    ps = Message.DefaultMessenger_s().Printers()
    for i in range(1, ps.Size() + 1):
        ps.Value(i).SetTraceLevel(Message_Gravity.Message_Fail)


def dist_exata_m(shape, p_m):
    """Distância exata (m) do OCP entre o sólido (mm) e o ponto p (m)."""
    v = BRepBuilderAPI_MakeVertex(gp_Pnt(*(float(x) * 1000 for x in p_m))).Vertex()
    d = BRepExtrema_DistShapeShape(shape, v)
    return d.Value() / 1000


_silenciar_ocp()
tmp = tempfile.TemporaryDirectory(prefix="dds_cad_")
STEP_SINT = os.path.join(tmp.name, "sintetico.step")
STEP_UNID = os.path.join(tmp.name, "sintetico_ref_x_100m.step")
gravar_step_sintetico(STEP_SINT)
gravar_step_sintetico(STEP_UNID, ref_x_local_mm=(100000.0, 0.0, 0.0))     # REF_X a 100 m: unidade errada simulada

# --- TC-POS-020 ----------------------------------------------------------------------------------------------------
def _assimetria(tubos):
    """Para cada trecho do eixo: a menor distância (m) entre o seu espelho em Y e outro trecho (pior ponta)."""
    segs = [(t.nome, a, b) for t in tubos for a, b in zip(t.pontos_eixo_m[:-1], t.pontos_eixo_m[1:])
            if np.linalg.norm(b - a) > 1e-4]
    S = np.array([[a, b] for _, a, b in segs])
    esp = np.array([1.0, -1.0, 1.0])
    out = []
    for nome, a, b in segs:
        ma, mb = a * esp, b * esp
        d1 = np.maximum(np.linalg.norm(S[:, 0] - ma, axis=1), np.linalg.norm(S[:, 1] - mb, axis=1))
        d2 = np.maximum(np.linalg.norm(S[:, 0] - mb, axis=1), np.linalg.norm(S[:, 1] - ma, axis=1))
        out.append((float(np.minimum(d1, d2).min()), nome))
    return out, len(segs)


# o relatório da geometria (§2) registra uma única exceção: a diagonal do FBH (FBH:1/Body7), que não tem par.
# A simetria tem de valer sem depender do passo da amostragem dos tubos quadrados: roda com 2,0 mm (padrão) e 1,7 mm.
real = cs.ler_step(STEP_REAL)
tubos, nos = cs.tubos_e_nos(real, tol_m=0.005)
ok20, det20, passo_padrao = True, [], cs._PASSO_MEMBRO_MM
for passo in (passo_padrao, 1.7):
    cs._PASSO_MEMBRO_MM = passo
    m_ = real if passo == passo_padrao else cs.ler_step(STEP_REAL)
    tb_, nos_ = (tubos, nos) if passo == passo_padrao else cs.tubos_e_nos(m_, tol_m=0.005)
    assim, n_segs = _assimetria(tb_)
    sem_par = sorted({n for d, n in assim if d > 0.5e-3})
    d_max = max(d for d, n in assim if n != "FBH:1/Body7")
    n_tri = sum(n.triangulado for n in nos_)
    ok20 &= len(m_.pecas) == 31 and len(nos_) == 28 and n_tri == 14 and sem_par == ["FBH:1/Body7"]
    det20.append(f"passo {passo} mm: corpos={len(m_.pecas)}; nós={len(nos_)}; triangulados={n_tri}; tubos={len(tb_)}; "
                 f"trechos={n_segs}; assimetria máx (exceto FBH:1/Body7)={d_max * 1000:.4f} mm; sem par={sem_par}")
cs._PASSO_MEMBRO_MM = passo_padrao
check("TC-POS-020 STEP real: 31 corpos, 28 nós com 14 triangulados (tol. 5 mm) e simetria em Y ≤ 0,5 mm",
      ok20, " | ".join(det20))

# --- TC-POS-021 ----------------------------------------------------------------------------------------------------
sint = cs.ler_step(STEP_SINT)
cats = sorted((p.nome_componente, p.nome_corpo, p.categoria) for p in sint.pecas)
cats_esp = sorted([("CHASSI_TESTE", "TUBO_REDONDO", "CHASSI"), ("CHASSI_TESTE", "TUBO_QUADRADO", "CHASSI"),
                   ("FIXO_CAIXA", "FIXO_CAIXA", "FIXO"), ("REF_REFERENCIAS", "REF_ORIGEM", "REF"),
                   ("REF_REFERENCIAS", "REF_X", "REF"), ("REF_REFERENCIAS", "REF_Y", "REF"),
                   ("HP_FRENTE", "HP_FL_LCA_OUT", "HP")])
esf = cs.esferas(sint)
esf_esp = {"REF_ORIGEM": (10.0, 20.0, 30.0), "REF_X": (110.0, 20.0, 30.0), "REF_Y": (10.0, 120.0, 30.0),
           "HP_FL_LCA_OUT": HP_MM}
erro_esf = max(np.linalg.norm(esf[k] - np.array(v) / 1000) for k, v in esf_esp.items()) if set(esf) == set(esf_esp) \
    else math.inf
R, t = cs.referencial(esf)
erro_ref = max(np.linalg.norm(R @ esf["REF_ORIGEM"] + t),
               np.linalg.norm(R @ esf["HP_FL_LCA_OUT"] + t - np.array([-0.010, 0.580, 0.130])))
check("TC-POS-021 STEP SINTÉTICO: categorias, centros das esferas e referencial",
      cats == cats_esp and sint.avisos == [] and erro_esf < 1e-6 and erro_ref < 1e-6,
      f"categorias {'ok' if cats == cats_esp else cats}; avisos={sint.avisos}; erro esferas={erro_esf:.2e} m; "
      f"erro referencial={erro_ref:.2e} m")

# --- TC-POS-022 ----------------------------------------------------------------------------------------------------
comps = sorted({p.nome_componente for p in real.pecas if p.ocorrencia != p.nome_componente})
corpos_raiz = sorted(p.nome_corpo for p in real.pecas if p.ocorrencia == p.nome_componente)
av_comp = [a for a in real.avisos if a.startswith("componente '")]
av_corpo = [a for a in real.avisos if a.startswith("corpo '") and "direto na raiz" in a]
um_por_comp = all(sum(f"'{c}'" in a for a in av_comp) == 1 for c in comps) and len(av_comp) == len(comps)
um_por_corpo = all(sum(f"'{c}'" in a for a in av_corpo) == 1 for c in corpos_raiz) and len(av_corpo) == len(corpos_raiz)
check("TC-POS-022 STEP real sem prefixos: tudo FIXO e um aviso por componente sem prefixo",
      all(p.categoria == "FIXO" for p in real.pecas) and um_por_comp and um_por_corpo and "Modelo Básico Orelha Pack"
      in comps,
      f"componentes={comps} ({len(av_comp)} avisos); corpos direto na raiz={len(corpos_raiz)} ({len(av_corpo)} avisos)")

# --- TC-POS-023 ----------------------------------------------------------------------------------------------------
unid = cs.ler_step(STEP_UNID)
e_unid = cs.esferas(unid)
d_med = float(np.linalg.norm(e_unid["REF_X"] - e_unid["REF_ORIGEM"]))
try:
    cs.referencial(e_unid)
    msg, ok23 = "nenhum erro", False
except cs.ErroReferencial as ex:
    msg = str(ex)
    ok23 = f"{d_med:.6f}" in msg and "REF_X" in msg
check("TC-POS-023 REF_X a 100 m (unidade errada SINTÉTICA): ErroReferencial com a distância medida",
      ok23 and abs(d_med - 100.0) < 1e-6, f"distância medida={d_med:.6f} m; mensagem: {msg}")

# --- TC-POS-024 ----------------------------------------------------------------------------------------------------
obs = cs.obstaculos_fixos(sint, np.eye(3), np.zeros(3))
peca = {p.nome_corpo: p for p in sint.pecas}
M_qua = _trsf_de(LOC_CHASSI) @ _trsf_de(LOC_QUADRADO)
M_red = _trsf_de(LOC_CHASSI) @ _trsf_de(LOC_REDONDO)
caixas_q = [o for o in obs if isinstance(o, Caixa) and abs(o.meias[0] * 1000 - L_QUA / 2) < 0.2
            and np.allclose(np.sort(o.meias[1:]) * 1000, [W_QUA / 2] * 2, atol=1e-6)]
caps = [o for o in obs if isinstance(o, Capsula)]
rng = np.random.default_rng(0)


def _ponto_local(i, n, comp, meia_w, perto_ponta):
    """Ponto SINTÉTICO ao redor do tubo (mm, local): direção radial e distância variadas; alguns além das pontas."""
    ang = 2 * math.pi * i / n + rng.uniform(0, 0.2)
    r = meia_w * math.sqrt(2) + rng.uniform(2.0, 60.0)
    x = rng.uniform(-40.0, 0.0) if perto_ponta == 0 else (comp + rng.uniform(0.0, 40.0) if perto_ponta == 1
                                                         else rng.uniform(0.05 * comp, 0.95 * comp))
    return np.array([x, r * math.cos(ang), r * math.sin(ang), 1.0])


dif_q, viol_q = [], 0
for i in range(20):
    pl = _ponto_local(i, 20, L_QUA, W_QUA / 2, i % 4 if i % 4 < 2 else 2)
    p = (M_qua @ pl)[:3] / 1000
    exata = dist_exata_m(peca["TUBO_QUADRADO"].shape, p)
    f = min(c.sdf(p[None, :])[0] for c in caixas_q) if caixas_q else math.inf
    dif_q.append(f - exata)
    viol_q += f > exata + 0.2e-3
dif_r = []
n_av = len(real.avisos)
obs_real = cs.obstaculos_fixos(real, np.eye(3), np.zeros(3))
av_cob = [a for a in real.avisos[n_av:] if "cobr" in a]
for i in range(20):
    rr = D_RED / 2 + rng.uniform(1.0, 80.0)
    ang = 2 * math.pi * i / 20
    pl = np.array([rng.uniform(0.02 * L_RED, 0.98 * L_RED), rr * math.cos(ang), rr * math.sin(ang), 1.0])
    p = (M_red @ pl)[:3] / 1000
    exata = dist_exata_m(peca["TUBO_REDONDO"].shape, p)
    f = min(c.sdf(p[None, :])[0] for c in caps) if caps else math.inf
    dif_r.append(f - exata)
check("TC-POS-024 Caixa do tubo quadrado ≤ distância do OCP + 0,2 mm; Capsula do tubo redondo = OCP ± 0,01 mm",
      len(caixas_q) == 1 and viol_q == 0 and len(caps) == 1 and max(abs(d) for d in dif_r) <= 1e-5 and not av_cob,
      f"caixas={len(caixas_q)}; cápsulas={len(caps)}; quadrado: (caixa − OCP) de {min(dif_q) * 1000:.4f} a "
      f"{max(dif_q) * 1000:.4f} mm, violações={viol_q}; redondo: |cápsula − OCP| máx="
      f"{max(abs(d) for d in dif_r) * 1000:.5f} mm; STEP real: {len(obs_real)} primitivos, avisos de cobertura={av_cob}")

tmp.cleanup()
print("\n--- Resumo ---")
n_pass = sum(1 for _, s_, _ in results if s_ == "PASS")
n_fail = sum(1 for _, s_, _ in results if s_ == "FAIL")
print(f"{n_pass} PASS, {n_fail} FAIL, de {len(results)} testes")
if n_fail > 0:
    raise SystemExit(1)
