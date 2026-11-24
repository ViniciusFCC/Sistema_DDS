import sys, json, csv, numpy as np
sys.path.insert(0,'python')
from posicionador import cad_step
m = cad_step.ler_step('data/cad/T11_chassi_2026-11-17.step')
tubos, nos = cad_step.tubos_e_nos(m)
t = np.array([-0.942,0,0.0774])
P = np.array([n.pos_m for n in nos]) + t
print(len(tubos),'tubos',len(nos),'nos')
for n,p in zip(nos,P):
    print(f"no {p[0]*1000:7.0f} {p[1]*1000:7.0f} {p[2]*1000:7.0f} ramos={n.n_ramos} tri={n.triangulado} esp={n.espalhamento_m*1000:.1f}mm")
hp={r['Point_ID']:np.array([float(r['X_m']),float(r['Y_m']),float(r['Z_m'])]) for r in csv.DictReader(open('data/posicionador/hardpoints_T11_v20_script.csv'))}
hp10={r['Point_ID']:np.array([float(r['X_m']),float(r['Y_m']),float(r['Z_m'])]) for r in csv.DictReader(open('data/posicionador/hardpoints_T11_v10.csv'))}
def dseg(p,a,b):
    ab=b-a;u=np.clip((p-a)@ab/(ab@ab),0,1);return np.linalg.norm(p-(a+u*ab))
for k in ['FL_ROCKER_AXIS_A','FL_ROCKER_AXIS_B','FL_SPRING_CHASSIS']:
    p=hp[k]; dn=np.linalg.norm(P-p,axis=1)
    dt=[(min(dseg(p,(tb.pontos_eixo_m+t)[i],(tb.pontos_eixo_m+t)[i+1]) for i in range(len(tb.pontos_eixo_m)-1)),tb.nome) for tb in tubos]
    dt.sort()
    print(k,'v20 no mais prox %.0f mm'%(dn.min()*1000),'tubo',[(round(d*1000),n) for d,n in dt[:3]])
print('v10 pts:',[k for k in hp10 if 'ROCK' in k or 'SPRING' in k])
# tubos
for tb in tubos: 
    a=tb.pontos_eixo_m+t; print(tb.nome, tb.secao, round(tb.r_ext_m*1000,1), 'ext', np.round(a.min(0)*1000), np.round(a.max(0)*1000))
