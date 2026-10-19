import subprocess, shutil, os, tempfile, sys, re
# Portabilidade (commit 1, SPEC R3): sys.executable no lugar de python3; pré-checagem
# do original; "detectado" = a saída contém FAIL e o código de saída é != 0.
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
TEST=os.path.join(HERE,'test_tire_model.py'); TIR=os.path.join(ROOT,'data','Hoosier_R25B_13x7_TTC_provisional.tir')
src=open(os.path.join(ROOT,'python','tire_model.py'),encoding='utf-8').read()
def rodar(fonte):
    # EDR-043: cópia temporária com tests/ (teste + modelo) e data/ (.tir), como no repositório.
    # O modelo fica na pasta do teste para ter prioridade sobre o python/ instalado pelo uv;
    # a sonda _origem.py, rodada do mesmo jeito que o teste, confirma que é ele o importado.
    # A pasta (com a cópia do .tir) é apagada no fim.
    d=tempfile.mkdtemp()
    try:
        t=os.path.join(d,'tests'); os.makedirs(t); os.makedirs(os.path.join(d,'data'))
        shutil.copy(TEST,t); shutil.copy(TIR,os.path.join(d,'data'))
        open(os.path.join(t,'tire_model.py'),'w',encoding='utf-8').write(fonte)
        open(os.path.join(t,'_origem.py'),'w',encoding='utf-8').write('import tire_model; print(tire_model.__file__)\n')
        sonda=subprocess.run([sys.executable,'-X','utf8','_origem.py'],cwd=t,capture_output=True,text=True)
        origem=sonda.stdout.strip()
        if sonda.returncode!=0 or os.path.normcase(os.path.dirname(os.path.abspath(origem)))!=os.path.normcase(os.path.abspath(t)):
            print('ERRO: o modelo importado não é a cópia temporária ->',origem or sonda.stderr[-500:]); sys.exit(2)
        return subprocess.run([sys.executable,'-X','utf8','test_tire_model.py'],cwd=t,capture_output=True,text=True)
    finally:
        shutil.rmtree(d,ignore_errors=True)
muts={
 "Ex sinal PEX4":("(1.0 - p[\"PEX4\"] * _sgn(kx))","(1.0 + p[\"PEX4\"] * _sgn(kx))"),
 "Ky PKY2*fz":("p[\"PKY2\"] * fz0","p[\"PKY2\"] * fz"),
 "Bx sem Cx":("Bx = Kx / (Cx * Dx + EPS)","Bx = Kx / (Dx + EPS)"),
 "SVx sem LMUX":("p[\"LVX\"] * p[\"LMUX\"]","p[\"LVX\"]"),
 "Gxa sem denominador":("Gxa = g(a_s) / g(SHxa)","Gxa = g(a_s)"),
 "Gyk sem denominador":("Gyk = gk(k_s) / gk(SHyk)","Gyk = gk(k_s)"),
 "SVyk RVY5 sinal":("math.sin(p[\"RVY5\"] * math.atan(p[\"RVY6\"] * kappa))","math.sin(-p[\"RVY5\"] * math.atan(p[\"RVY6\"] * kappa))"),
 "espelho esquerdo Fy":("return fx, (-fy_right_iso if left else fy_right_iso), info","return fx, fy_right_iso, info"),
 "faixa Fz":("elif not (p[\"FZMIN\"] <= fz <= p[\"FZMAX\"]):","elif not (p[\"FZMIN\"] <= fz <= 2*p[\"FZMAX\"]):"),
 "camber PDY3":("(1.0 - p[\"PDY3\"] * gy * gy)","(1.0 + p[\"PDY3\"] * gy * gy)"),
 "mu_eff":("math.hypot(fx, fy) / fz","math.hypot(fx, fy) / (2*fz)"),
 "Ey sem min/sinal":("min((p[\"PEY1\"] + p[\"PEY2\"] * dfz) * (1.0 - (p[\"PEY3\"] + p[\"PEY4\"] * gy) * _sgn(ay)) * p[\"LEY\"], 1.0)","(p[\"PEY1\"] + p[\"PEY2\"] * dfz) * (1.0 + (p[\"PEY3\"] + p[\"PEY4\"] * gy) * _sgn(ay)) * p[\"LEY\"]"),
 "LKY ignorado":("* p[\"LFZO\"] * p[\"LKY\"]\n    SHy","* p[\"LFZO\"]\n    SHy"),
 "PHY3 camber":("+ p[\"PHY3\"] * gy","- p[\"PHY3\"] * gy"),
 "RVY3 camber":("p[\"RVY3\"] * gamma","p[\"RVY3\"] * 0"),
 "kappa-range":("if not (p[\"KPUMIN\"] <= kappa <= p[\"KPUMAX\"]):","if not (p[\"KPUMIN\"] <= kappa <= 2*p[\"KPUMAX\"]):"),

 "s_F removido (Fy sem inverter)":("fy_right_iso = s_f * fy_file","fy_right_iso = fy_file"),
 "s_alpha removido":("s_a * a_right, s_g * gamma","a_right, s_g * gamma"),
 "s_gamma removido":("s_a * a_right, s_g * gamma","s_a * a_right, gamma"),
 "SAE com sinais ISO":("\"SAE_CALSPAN\": (-1.0, -1.0, -1.0),","\"SAE_CALSPAN\": (1.0, 1.0, 1.0),"),
 "espelho depois da transformacao":("a_right = -alpha if left else alpha","a_right = alpha"),
 "loader aceita eixo None":("if source_axis_system not in AXIS_TRANSFORMS:","if False:"),
 "gamma SAE so s_g=+1":("\"SAE_CALSPAN\": (-1.0, -1.0, -1.0),","\"SAE_CALSPAN\": (-1.0, -1.0, 1.0),"),
}
out=rodar(src)
resumo=(out.stdout.strip().splitlines() or [''])[-1]
m=re.match(r'^(\d+) PASS, 0 FAIL, de (\d+) testes$',resumo)
if out.returncode!=0 or not m or m.group(1)!=m.group(2) or int(m.group(1))==0:
    print('PRE-CHECAGEM FALHOU: original ->',resumo,'| código',out.returncode); print(out.stderr[-2000:]); sys.exit(2)
print('PRE-CHECAGEM OK: original ->',resumo)
det=0
for name,(a,b) in muts.items():
    assert a in src, name
    out=rodar(src.replace(a,b,1))
    ok=out.returncode!=0 and '[FAIL]' in out.stdout
    det+= ok
    print(('DETECTADO     ' if ok else 'NÃO DETECTADO '),name)
print(det,'/',len(muts))
