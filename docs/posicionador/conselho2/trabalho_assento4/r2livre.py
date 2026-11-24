import sys, json, numpy as np
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cad_best.py').read().split("for i,x in enumerate(xs):")[0])
import kinematics_model as km
def info(x,r2):
    v=mec.Variaveis.da_semente_do_script(x); c=mec.construir(hs,v,cfg,r2_m=r2)
    if c.hardpoints is None: return None
    av=vr.avaliar(c,cena,cfg,n=11)
    d={rr.nome:rr for rr in av.restricoes}
    mr=av.curvas['MR [wheel/spring]']
    viol=[rr.nome+f"({rr.folga*1e3 if rr.folga is not None and abs(rr.folga)<1 else rr.folga:.2f})" for rr in av.restricoes if rr.estado=='VIOLADA']
    return mr[len(mr)//2*0+0], mr.min(),mr.max(),(mr.max()-mr.min())/mr.mean(), d['comprimento do amortecedor (mínimo)'].valor, viol
for i in (2,3,4,0,5):
    x=xs[i]; print('cand',i)
    for f in (0.97,0.98,0.99,1.0,1.01,1.02,1.03):
        r2=x[7]/1000*f
        o=info(x,r2)
        print(f'  r2={r2*1e3:.2f}', None if o is None else (f'MRmin {o[1]:.4f} MRmax {o[2]:.4f} var {o[3]*100:.2f}% Lmin {o[4]*1e3:.2f}', o[5]))
