import sys, json, itertools, numpy as np
sys.path.insert(0,'docs/posicionador/conselho2/trabalho_assento2')
import estrutura as e
R=json.load(open('docs/posicionador/benchmark/resultados.json'))
# nós do vão dianteiro (lado esquerdo Y>0): FH em x=-202, FBH em x=495
N=e.NOS; esq=[n for n in N if n[1]>0 and (abs(n[0]+0.202)<1e-3 or abs(n[0]-0.495)<1e-3)]
print('nós do lado esquerdo no vão:',[tuple(np.round(n*1000)) for n in esq])
virt=[(a,b) for a,b in itertools.combinations(esq,2) if abs(a[0]-b[0])>0.5]   # só arestas FH–FBH
print(len(virt),'arestas-fantasma FH–FBH')
def dseg(p,a,b):
    ab=b-a;u=np.clip((p-a)@ab/(ab@ab),0,1);q=a+u*ab;return np.linalg.norm(p-q),u
def an(x):
    c=e.mec.construir(e.hs,e.e.mec.Variaveis.da_semente_do_script(x) if False else e.mec.Variaveis.da_semente_do_script(x),e.cfg,r2_m=float(x[7])/1000)
    if c.hardpoints is None: return None
    P={k:np.asarray(v.xyz,float) for k,v in c.hardpoints.points.items()}
    pk={k:P['FL_'+k] for k in ['LCA_IN_F','LCA_IN_R','UCA_IN_F','UCA_IN_R','ROCKER_AXIS_A','ROCKER_AXIS_B','SPRING_CHASSIS']}
    res={}
    for k,p in pk.items():
        d0=e.prox(p)[0]
        dv=min(dseg(p,a,b)[0] for a,b in virt)
        res[k]=(round(d0*1000),round(min(d0,dv)*1000))
    return res
for nome,x in [('v20',R['x_v20'])]+[(b['rotulo'][:14],b['x']) for b in R['buscas'] if b['ferramenta']=='posicionador']:
    r=an(x); print(nome,{k:v for k,v in r.items()})
