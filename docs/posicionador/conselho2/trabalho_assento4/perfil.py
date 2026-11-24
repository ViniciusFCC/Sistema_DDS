import sys, time, cProfile, pstats, numpy as np
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cena.py').read().split("t=time.time()")[0])
import hardpoints as hp
cena,mont,txt,(R,tt),esf=pa.cena_do_step('/home/user/Sistema_DDS/data/cad/T11_chassi_2026-11-17.step',cfg)
hs=hp.load_hardpoints('/home/user/Sistema_DDS/data/posicionador/hardpoints_T11_v20_script.csv','/home/user/Sistema_DDS/data/posicionador/hardpoints_T11_v20_script.meta.json')
from posicionador import mecanismo as mec
sem=vr.cena_sem_cad(cfg)
for nome,c in (('semCAD',sem),('CAD',cena)):
    t=time.time(); av=vr.avaliar(mec.Construcao(hs,None,None),c,cfg,n=11); print(nome,'n=11',time.time()-t,av.veredito)
cProfile.run("vr.avaliar(mec.Construcao(hs,None,None),cena,cfg,n=11)",'/tmp/p.out')
pstats.Stats('/tmp/p.out').sort_stats('cumtime').print_stats(12)
