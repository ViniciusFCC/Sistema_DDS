import sys, json, time, numpy as np
exec(open('/home/user/Sistema_DDS/docs/posicionador/conselho2/trabalho_assento4/cena.py').read().split("t=time.time()")[0])
from posicionador import mecanismo as mec
import hardpoints as hp
hs=hp.load_hardpoints('/home/user/Sistema_DDS/data/hardpoints_T11_v10.csv' if False else '/home/user/Sistema_DDS/data/posicionador/hardpoints_T11_v10.csv','/home/user/Sistema_DDS/data/posicionador/hardpoints_T11_v10.meta.json')
cena,mont,txt,(R,tt),esf=pa.cena_do_step('/home/user/Sistema_DDS/data/cad/T11_chassi_2026-11-17.step',cfg)
r=json.load(open('/home/user/Sistema_DDS/docs/posicionador/benchmark/resultados.json'))
xs=[b['x'] for b in r['buscas'][-6:]]+[r['x_v20']]
from posicionador.geometria import Caixa
def cena_desloc(d):
    # desloca os fixos por d (m): equivale a mudar t da transformação
    return d
for i,x in enumerate(xs):
    v=mec.Variaveis.da_semente_do_script(x); c=mec.construir(hs,v,cfg,r2_m=x[7]/1000)
    if c.hardpoints is None: print(i,'construcao falhou',c.motivo); continue
    av=vr.avaliar(c,cena,cfg,n=11)
    print(i,'pivo',np.round(x[:3],1),av.veredito)
    for rr in av.restricoes:
        if rr.estado!='OK' : print('   ',rr.nome,rr.estado,rr.valor,rr.folga)
