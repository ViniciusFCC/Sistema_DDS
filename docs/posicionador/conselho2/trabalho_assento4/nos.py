import sys, json, numpy as np
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cad_best.py').read().split("for i,x in enumerate(xs):")[0])
P=np.array([n.pos_m for n in cena.nos]); 
print('nos (mm) x,y,z ramos'); 
for n in sorted(cena.nos,key=lambda n:-n.pos_m[0])[:12]: print(np.round(n.pos_m*1e3,0), n.n_ramos, n.triangulado)
for i in (2,3,4,5,6,0):
    x=xs[i]; pv=np.array(x[:3])/1e3
    d=np.linalg.norm(P-pv,axis=1); j=d.argmin()
    s=min(float(f.sdf(pv[None,:])[0]) for f in cena.fixos)
    # olhal chassi C
    v=mec.Variaveis.da_semente_do_script(x); c=mec.construir(hs,v,cfg,r2_m=x[7]/1000)
    C=c.hardpoints.points['FL_SPRING_CHASSIS'].xyz
    dc=np.linalg.norm(P-C,axis=1)
    sc=min(float(f.sdf(np.array(C)[None,:])[0]) for f in cena.fixos)
    print(i,'pivo: nó mais perto %.0f mm, folga ao tubo mais perto %.0f mm | olhal chassi C=%s nó %.0f mm folga %.0f'%(d[j]*1e3,s*1e3,np.round(np.array(C)*1e3,0),dc.min()*1e3,sc*1e3))
