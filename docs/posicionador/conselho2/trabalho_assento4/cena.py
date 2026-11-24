import sys, time, pickle, numpy as np
sys.path.insert(0,'/home/user/Sistema_DDS/tools'); sys.path.insert(0,'/home/user/Sistema_DDS/python')
import posicionar_atuacao as pa
from posicionador import config as pc, cad_step as cs, varredura as vr, espaco_livre as el
cfg=pc.carregar('/home/user/Sistema_DDS/data/posicionador/config_T11.json')
t=time.time(); cena,mont,txt,(R,tt),esf=pa.cena_do_step('/home/user/Sistema_DDS/data/cad/T11_chassi_2026-11-17.step',cfg)
print('cena s',time.time()-t,'fixos',len(cena.fixos),'nos',len(cena.nos))
from collections import Counter
print(Counter(type(f).__name__ for f in cena.fixos))
print(Counter(p.categoria for p in mont.pecas))
print(len(mont.avisos)); [print(' ',a[:160]) for a in mont.avisos[:15]]
print(sorted(esf)[:30])
emin,emax,n=pa.caixa_envelope(cena.fixos); print(emin,emax,n)
