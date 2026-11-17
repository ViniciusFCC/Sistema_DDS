# Resposta: lente de estrutura do chassi tubular

Cálculo próprio em `conselho/assento2_trabalho/cargas_v20.py` (saída em `cargas_v20_saida.txt`). Ele faz a estática do
rocker da v20 e um pórtico 3D do tubo Q–E proposto pelo script, com orelhas rígidas de 42 mm.

Hipóteses:
- F_mola = MR·F_roda (trabalho virtual), sem barra e sem batente;
- aço com E = 200 GPa; o material não está declarado no CAD (GEO §8.7);
- paredes de 1,2, 1,9 e 2,65 mm, as que aparecem no STEP.

Conferência à mão: 432 MPa, contra 393 MPa do pórtico.

## Q1. O método atual é adequado?

Não.

- **O critério estrutural do script é geométrico, sem caminho de carga.** O critério é "tubo paralelo ao plano, a 42 mm,
  que cai a ≤ 8 mm do FH". [código, GEO §6a]:
  - Q fica 65 mm acima de N11, que não é triangulado.
  - E fica no ar, a 66,7 mm de N04.
  - O pivô está a 180 mm de qualquer nó e a 237 mm de um nó triangulado.
- **Cargas, por kN de carga vertical na roda** [resultado de código]:
  - push rod 1,46 kN, amortecedor 1,40 kN, pivô 2,49 kN;
  - no bump, 0,11 kN saem do plano, ao longo do eixo do pivô. São cerca de 8 % da força do push rod, o que confirma o
    achado 3 do REGISTRO.
- **Flexão máxima no Q–E, de 699 mm, por kN na roda** [resultado de código]:
  - de 145 a 268 MPa com as pontas engastadas;
  - de 215 a 393 MPa com as pontas articuladas.
  - Com a ordem de carga de outro carro (push rod de 2994 N, Peixoto, via LIT §1), isso dá cerca de 2 kN na roda e
    300 a 800 MPa.
  - [inferência] Esse arranjo não fecha. As pontas reais são piores que as duas hipóteses, porque E não toca em nada.
- **Rigidez** [resultado de código]: Ke equivalente na roda de 190 a 1220 N/mm.
  - [cálculo] Pela eq. 7.1 de Peixoto (LIT §4), com perda de 5 % (valor ilustrativo), a ride rate admissível fica em
    no máximo 10 a 64 N/mm.
  - A ride rate do T11 está a confirmar.
- **A força bruta sem solução** [inferência]: "perto de um nó" era impossível. Entre o FH e o FBH, na altura das
  bandejas, não há tubo (GEO §3).
- **Discordo da distância ao nó como critério.** A LIT §4 dá 93 a 142 MPa já a 30 mm do nó. O critério certo é tensão
  e rigidez para o envelope de cargas.

## Q2. Método e arquitetura

1. **Para cada candidato, as cargas nas fixações.**
   - Pela estática do rocker, sai o vetor de força no pivô, no olhal C e no push rod, em cada caso de carga.
   - Os casos de carga seguem o método de Peixoto, Ap. E (LIT §4). Os valores do T11 estão a confirmar.
   - O cálculo é em forma fechada e barato.
2. **Variável discreta: o hospedeiro.** Pode ser:
   - um nó existente;
   - um ponto num membro existente ou previsto, com posição contínua s;
   - um nó proposto, com o membro novo que ele exige.
   - O offset da orelha entra com custo: 42 mm × 2,49 kN dá 105 N·m por kN.
3. **Restrições duras.**
   - σ do hospedeiro ≤ admissível (a confirmar).
   - Ke ≥ RR(1−p)/p.
   - Carga axial no pivô dentro do limite do mancal (a confirmar).
   - A distância ao nó só entra no relatório.
4. **Superposição linear.**
   - A cada versão do STEP, calcula-se a matriz de influência do pórtico, com cargas unitárias amostradas ao longo de
     cada hospedeiro. Ferramenta: Pynite (SKILLS, item 5) ou um pórtico de ~100 linhas.
   - No laço, σ e Ke saem de produtos de matrizes.
   - FEA de casca da junta e da orelha, só nos finalistas.
5. **Princípio de arranjo: pivô e C no mesmo subconjunto triangulado.**
   - [cálculo] As componentes axiais no tubo quase se anulam: −1,52 contra +1,30 kN/kN. A força do amortecedor fecha
     localmente.
   - O chassi recebe só a resultante do push rod (1,46 kN/kN).
6. **Algoritmo e saída.**
   - Concordo com a LIT: viabilidade primeiro, enumeração dos hospedeiros mais multi-start.
   - Saída: lista não dominada com σ, Ke, tubos novos e cargas.
   - Se não houver viável, a saída é a lista das restrições em conflito.

## Q3. Uso de tubos e nós do CAD

- **Grafo de pórtico.**
  - Os arquivos `tubos.json` e `nos.json` viram um grafo de pórtico.
  - Cada membro leva OD, parede e a orientação do tubo quadrado. Hoje essa orientação fica de fora (GEO §7).
- **"Triangulado" vem da rigidez local do pórtico, não da contagem de ramos.** A contagem de ramos gera artefatos, como
  os nós N25 e N27 (GEO §7).
- **Três classes de membro, com o rótulo em cada candidato:**
  - **Existente.**
  - **Previsto obrigatório:** fantasma rotulado como hipótese. São os 3 membros de apoio do FBH por lado (F.6.2.3), as
    escoras do FH (F.6.3) e o side impact (F.6.4). São os hospedeiros naturais da dianteira (REGRAS §3.2).
  - **Proposto.**
- **A cada STEP, nova rodada.** Os hospedeiros mudados aparecem pelo ID estável do nó, o que exige corpos com nome
  (GEO §8.6).
- **Regras no relatório de cada candidato:** F.5.3.1 (furo vai para a SES), F.3.4.3 (insertos), F.3.3.2 (tubo não
  estrutural) e V.3.1.5 (cisalhamento duplo).
- **[hipótese]** O braceFBH, 48 mm acima do Q–E (GEO §6c), é hospedeiro candidato.

## Q4. Coordenação chassi × suspensão

- **Interface: uma ficha por fixação** (posição, região admissível, forças por caso, Ke exigido e hospedeiro
  proposto).
- **Responsabilidades:**
  - a suspensão é dona dos pontos e das cargas;
  - o chassi é dono dos nós, das bitolas e da triangulação.
- **Ordem:**
  1. Congelar os casos de carga, a RR e o p.
  2. O chassi desenha a caixa dianteira com os membros obrigatórios, mesmo provisórios.
  3. O script propõe os hospedeiros.
  4. O chassi aceita ou cria nós.
  5. FEA do quadro inteiro nos finalistas (LIT §4: Riley & George; Bortoluzzi).
  6. Repetir a cada versão.
- **A fixação "por cima" do TX** só serve se cair sobre um nó. Senão repete o caso da UM-Rolla: aba no meio do vão e
  falha (PRÁTICA §5).

## Q5. Riscos e o que validar primeiro

- **Validar primeiro: o envelope de cargas do T11.**
  - Teste que derruba: com as cargas reais e a parede real, a v20 com o Q–E apoiado em nós passar σ e Ke com folga.
  - Se passar, o pórtico no laço não se paga, e basta FEA nos finalistas.
- **Riscos:**
  - A viga ignora o esmagamento da parede sob a orelha e a solda.
  - O batente e a barra (fora do cálculo) podem dominar a carga no pivô.
  - Um fantasma errado dá falsa viabilidade.
  - O pórtico próprio ainda não foi validado contra o Pynite nem contra FEA.

**Recomendação em uma frase:** Trocar "perto do nó / tubo cai no FH" por um laço em que cada candidato gera os vetores
de carga das fixações e só é aprovado se o hospedeiro (nó existente, membro existente ou previsto, ou nó proposto)
cumprir tensão e Ke ≥ RR(1−p)/p no pórtico do chassi, com enumeração de hospedeiros e saída em ficha de fixação para o
chassi.

**Confiança: média.**
- **Alta** de que a v20, como desenhada, é estruturalmente inviável: de 145 a 393 MPa por kN, sem nó nas pontas.
- **Principal incerteza:** o envelope de cargas do T11 e a parede do hospedeiro. Eles decidem se a estrutura entra no
  laço ou só nos finalistas.
