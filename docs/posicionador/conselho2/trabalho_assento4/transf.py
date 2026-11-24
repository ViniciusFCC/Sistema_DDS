import sys, json, numpy as np, itertools
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cad_best.py').read().split("for i,x in enumerate(xs):")[0])
cs_=[]
for i in (2,3,4,5,1):
    x=xs[i]; v=mec.Variaveis.da_semente_do_script(x); cs_.append((i,mec.construir(hs,v,cfg,r2_m=x[7]/1000)))
def minf(R_,t_):
    cn=vr.cena_do_step(mont,R_,t_,cfg)
    out=[]
    for i,c in cs_:
        av=vr.avaliar(c,cn,cfg,n=11); d={r.nome:r for r in av.restricoes}['folga aos fixos: amortecedor']
        out.append(round(d.folga*1e3,1))
    return out
print('nominal',minf(R,tt))
for ax in range(3):
    for s in (-0.005,0.005):
        d=np.zeros(3); d[ax]=s; print('eixo','XYZ'[ax],s*1e3,'mm',minf(R,tt+d))
# rotação 0.5 deg em Z e Y (inclinação do chassi)
def rot(ax,deg):
    a=np.radians(deg); c,s=np.cos(a),np.sin(a)
    return {0:np.array([[1,0,0],[0,c,-s],[0,s,c]]),1:np.array([[c,0,s],[0,1,0],[-s,0,c]]),2:np.array([[c,-s,0],[s,c,0],[0,0,1]])}[ax]
for ax in (1,2):
    for dg in (-1,1):
        print('rot eixo','XYZ'[ax],dg,'deg (em torno da origem do carro)',minf(rot(ax,dg)@R, rot(ax,dg)@tt))
