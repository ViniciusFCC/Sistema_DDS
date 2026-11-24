"""Indicadores estruturais por kN de carga vertical na roda (forma fechada, estática, sem dado de carga do T11)."""
import sys, json, numpy as np
sys.path.insert(0,'python'); sys.path.insert(0,'tools')
from posicionador import cad_step, config as pc, mecanismo as mec
import hardpoints as hp
D='data/posicionador/'
cfg=pc.carregar(D+'config_T11.json')
hs=hp.load_hardpoints(D+'hardpoints_T11_v10.csv',D+'hardpoints_T11_v10.meta.json')
m=cad_step.ler_step('data/cad/T11_chassi_2026-11-17.step')
tubos,nos=cad_step.tubos_e_nos(m)
t=np.array([-0.942,0,0.0774])
NOS=np.array([n.pos_m for n in nos])+t
SEG=[]
for tb in tubos:
    P=tb.pontos_eixo_m+t
    for i in range(len(P)-1): SEG.append((tb.nome,P[i],P[i+1]))
def prox(p):
    best=(9,None,None,None)
    for nm,a,b in SEG:
        ab=b-a;u=np.clip((p-a)@ab/(ab@ab),0,1);q=a+u*ab;d=np.linalg.norm(p-q)
        if d<best[0]: best=(d,nm,u,np.linalg.norm(ab))
    return best
MR=1.4
def indicadores(x):
    con=mec.construir(hs,mec.Variaveis.da_semente_do_script(x),cfg,r2_m=float(x[7])/1000)
    if con.hardpoints is None: return None
    P=con.hardpoints.points
    g=lambda k: np.asarray(P[k].xyz,float)
    A,B,PI,PO,RS,SC=[g(k) for k in ['ROCKER_AXIS_A','ROCKER_AXIS_B','PUSH_IN','PUSH_OUT','ROCKER_SPRING','SPRING_CHASSIS']] if 'ROCKER_AXIS_A' in P else None
    return A,B,PI,PO,RS,SC
