import sys, json, numpy as np
sys.path.insert(0,'docs/posicionador/conselho2/trabalho_assento2')
import estrutura as e
R=json.load(open('docs/posicionador/benchmark/resultados.json'))
def an(x,rot):
    c=e.mec.construir(e.hs,e.mec.Variaveis.da_semente_do_script(x),e.cfg,r2_m=float(x[7])/1000)
    if c.hardpoints is None: return None
    P={k:np.asarray(v.xyz,float) for k,v in c.hardpoints.points.items()}
    A,B,PI,PO,RS,SC=[P['FL_'+k] for k in ['ROCKER_AXIS_A','ROCKER_AXIS_B','PUSH_IN','PUSH_OUT','ROCKER_SPRING','SPRING_CHASSIS']]
    u=(B-A)/np.linalg.norm(B-A)
    dpr=(PI-PO)/np.linalg.norm(PI-PO)      # push rod comprime o rocker em PI
    ds=(RS-SC)/np.linalg.norm(RS-SC)       # mola comprimida empurra o rocker em RS para longe do chassi
    Fs=e.MR*1.0                              # kN por kN de roda (trabalho virtual, MR=wheel/spring)
    # equilíbrio de momento no eixo: Fpr*(u.((PI-A)x dpr)) = -Fs*(u.((RS-A)x(-ds)))  (mola reage ao pushrod)
    mpr=u@np.cross(PI-A,dpr); ms=u@np.cross(RS-A,-ds)
    Fpr=-Fs*ms/mpr
    Fpiv=-(Fpr*dpr+Fs*(-ds))   # reação no eixo (sobre o rocker); no chassi: oposta
    Fax=(Fpiv@u); Fperp=np.linalg.norm(Fpiv-Fax*u)
    out={'Fpr':Fpr,'Fpiv':np.linalg.norm(Fpiv),'Fax':Fax,'Fs':Fs,'ang_pr_rocker_graus':None}
    pk={}
    for k in ['LCA_IN_F','LCA_IN_R','UCA_IN_F','UCA_IN_R']: pk[k]=P['FL_'+k]
    pk['AXIS_A']=A; pk['AXIS_B']=B; pk['SPRING_CHASSIS']=SC
    for k,p in pk.items():
        d,nm,s,L=e.prox(p); dn=np.linalg.norm(e.NOS-p,axis=1).min()
        out[k]=(round(d*1000),nm,round(float(s),2),round(L*1000),round(dn*1000))
    # momento de flexão no tubo por kN: força transversal ao tubo mais próxima ao ponto (viga biapoiada nos nós), M=Fperp_tubo*s*(1-s)*L
    def Mflex(p,F,k):
        d,nm,s,L=e.prox(p)
        return abs(F)*s*(1-s)*L
    out['M_mola_Nm_por_kN']=Mflex(SC,Fs,'SC')*1000   # kN*m->N*m por kN
    out['M_pivo_Nm_por_kN']=Mflex(A,Fperp/2,'A')*1000  # metade da reação em cada ponto do eixo
    return out
v20=R['x_v20']
r=an(v20,0); print('v20',json.dumps(r,default=float))
rows=[]
for b in R['buscas']:
    if b['ferramenta']=='script' and not b['rotulo'].startswith('v20'): continue
    r=an(b['x'],0)
    if r: rows.append((b['ferramenta'],b['rotulo'][:22],r))
for f,l,r in rows:
    print(f,l,'Fpr=%.2f Fpiv=%.2f'%(r['Fpr'],r['Fpiv']),'SC',r['SPRING_CHASSIS'][:1]+r['SPRING_CHASSIS'][-1:],'A',r['AXIS_A'][0],r['AXIS_A'][-1],'B',r['AXIS_B'][0],'M_mola %.0f M_piv %.0f'%(r['M_mola_Nm_por_kN'],r['M_pivo_Nm_por_kN']))
