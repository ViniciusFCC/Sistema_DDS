import sys, json, numpy as np
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cad_best.py').read().split("for i,x in enumerate(xs):")[0])
for i in (2,3,4,5):
    x=xs[i]; v=mec.Variaveis.da_semente_do_script(x); c=mec.construir(hs,v,cfg,r2_m=x[7]/1000)
    av=vr.avaliar(c,cena,cfg,n=11)
    print(i,[(r.nome[:38],None if r.folga is None else round(r.folga*1e3 if abs(r.folga)<1 else r.folga,2)) for r in av.restricoes if r.estado=='OK'])
