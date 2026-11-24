import sys, json, numpy as np
from scipy.optimize import brentq
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cad_best.py').read().split("for i,x in enumerate(xs):")[0])
def av_(x,r2):
    v=mec.Variaveis.da_semente_do_script(x); c=mec.construir(hs,v,cfg,r2_m=r2)
    return vr.avaliar(c,cena,cfg,n=11)
for i in (2,3,4):
    x=xs[i]; r0=x[7]/1000
    f=lambda r2: {r.nome:r for r in av_(x,r2).restricoes}['comprimento do amortecedor (mínimo)'].valor-0.14905
    r2=brentq(f,r0*0.96,r0,xtol=1e-7); av=av_(x,r2); d={r.nome:r for r in av.restricoes}
    mr=av.curvas['MR [wheel/spring]']
    print(i,'r2 %.2f mm (nominal %.2f)'%(r2*1e3,r0*1e3),'MR(0)=%.4f'%d['MR(0)'].valor,'var %.2f%%'%(d['variação de MR'].valor*100),'Lmin %.2f'%(d['comprimento do amortecedor (mínimo)'].valor*1e3),
      'violadas:',[r.nome for r in av.restricoes if r.estado=='VIOLADA'])
