# Resposta: pipeline CAD ↔ Python, tubos e nós, manutenção

Rótulos: [F] fato de relatório; [C] resultado de código (meu, em `assento4_trabalho/`, ou dos relatórios); [K] cálculo; [I] inferência; [H] hipótese.

## Q1. O método atual é adequado?

Não. O defeito central não é o Nelder-Mead: **o script não lê o chassi**.
- **Chassi escrito à mão** [C, `t11_atuacao.py`]: o chassi são quatro constantes (`FH0`, `FH1`, `X_FBH = 490`, polígono do gabarito) e um `-202` solto em `tubo()`.
- **Tubo inventado pela solução** [C]: o tubo de montagem sai da própria solução (paralelo ao plano do rocker, prolongado até o FBH). O script pede ao chassi um tubo onde a suspensão quer, em vez de procurar no chassi.
  - Resultado: E fica no ar, 44,7 mm fora do FBH; `X_FBH` erra o CAD em 4,9 mm [F, GEO §5, §6c].
  - Nenhum tubo entra na colisão [F, REGISTRO achado 4].
- **Referencial sem âncora**: o Z só fecha pelo FH0/FH1 [F, GEO §5].
- **Manutenção** [C]:
  - 256 linhas sem teste.
  - `kinlib` em mm, com docstring do TX (push rod na bandeja superior) enquanto o T11 usa `ARM='L'`; exige pontos falsos (`PI`, `BP`, `SB`, `SC`) e muda o estado global `K.PTS`.
- **O repositório já resolve parte disso** [C, `python/`], e nenhum relatório notou:
  - `kinematics_model.Corner`, com push rod, mola, `motion_ratio`, `sweep` e `steer_sweep` (76 checks).
  - `hardpoints.py`, com os IDs `PUSH_OUT/IN`, `ROCKER_AXIS_A/B`, `ROCKER_SPRING`, `SPRING_CHASSIS` e o campo Status (35 checks).
  - Duas cinemáticas paralelas, uma sem teste, numa equipe que troca de membros, viram erro silencioso [I].

## Q2. Método e arquitetura

Cinco módulos, com contratos em arquivo e testáveis cada um sozinho:

1. **`cad_in`**: STEP → `tubos.json` e `nos.json` (o `step_tubos.py`, endurecido). O SHA-256 do STEP vai em toda saída.
   - Tempo: 0,3 s de leitura [C] e cerca de 3 min de classificação [F, GEO §1]. Roda por revisão do CAD, nunca no laço.
2. **`geometria`**: cápsulas conservadoras. Medi contra o BRep exato (OCP `BRepExtrema`, 300 pontos por corpo) [C, `capsula_vs_brep.saida.txt`]:
   - Tubo redondo reto: exato.
   - Tubo quadrado com R = meia largura (o que `step_tubos.segmentos()` usa): **superestima a folga em até 5,18 mm**, isto é, aprova o que bate.
   - Tubo quadrado com R = meia-diagonal: nunca superestima.
   - FH curvo discretizado: até 0,12 mm otimista.
   - Regra: R envolvente + 0,2 mm. Discordo do PRATICA §4/§6 e do GEO §6b, que usam a meia largura como "folga entre faces".
3. **Cinemática**: o `Corner` do repositório, em SI. O `kinlib` fica só para conferência cruzada, até ser aposentado.
4. **`busca`**:
   - Âncora discreta: nó existente, ponto num tubo a s mm do nó, ou nó proposto.
   - Restrições como desigualdades com margem explícita.
   - Fase I (menor violação e conflitos), depois fase II. A formulação fina fica com quem cuida de otimização.
   - Custo: cápsula em NumPy dá 3,7·10⁶ pares/s [C], cerca de 10 a 30 ms por candidato (10 peças × 25 cursos × 138 elementos) [K]. Cabe no laço.
5. **`verificar`**: o único que aprova.
   - Folga BRep exata nos finalistas, em curso × esterço: 0,3 a 3 ms por consulta por corpo [C], segundos por candidato [K].
   - É independente da busca: a busca pode aproximar, a aprovação não.

**Saída**: CSV no schema `hardpoints.py` (Status `PROVISIONAL`) e relatório por candidato (folgas, MR, distância ao nó, hash do STEP). A aprovação vira `STALE` quando o hash muda.

## Q3. Tubos e nós com o CAD incompleto

- **Três camadas de geometria**:
  - existente (STEP);
  - prevista: cápsulas "fantasma" que o chassi declara num JSON versionado, com status;
  - reservada: gabarito T.1.2 com altura livre [F, REGRAS D5], pedais, IA, coluna.
  - Existente e prevista são obstáculo e âncora; a âncora prevista sai "condicional".
- **Primeiro, esboçar os tubos obrigatórios da zona vazia**: superior, inferior e diagonal do Front Bulkhead Support, por lado [F, REGRAS F.6.2.3].
  - Eles vão existir de qualquer jeito e são os nós que faltam: LF, UF, TI, Pv e C estão a mais de 97 mm de qualquer tubo [F, GEO §6a].
- **Reconhecer por geometria, não por nome**:
  - 23 dos 28 sólidos se chamam `BodyNN` (nome padrão do Fusion) [C, grep no STEP].
  - Entre revisões, casar os tubos pelas pontas do eixo; o nome serve só de rótulo.
- **Âncora do referencial**:
  - Este STEP não traz esboço nem geometria de construção: zero `GEOMETRIC_CURVE_SET` [C]. A afirmação do GEO §8.2 de que um ponto de construção nomeado chega pelo STEP não está verificada.
  - Nomes de corpos chegam [C]. Proposta: corpos-datum pequenos e nomeados (esfera Ø5 `REF_ORIGEM`, e cada hardpoint com o Point_ID do schema).
  - Plano B: script da API do Fusion que exporta os pontos para JSON, depois do teste de licença [F, PRATICA §3.2].
- **`analyzeInterference` do Fusion só como conferência visual**: exige design direto e ocorrências [F, PRATICA §3.1] e não é reprodutível.

## Q4. Coordenação

- **Contrato versionado no Git**:
  - o chassi é dono do STEP e dos tubos previstos;
  - a suspensão é dona dos hardpoints e dos volumes reservados;
  - os dois são donos da lista de "pedidos de nó" (proposto → aceito/recusado, com o motivo).
- **Ordem**:
  1. Congelar as bandejas da v10 e os volumes reservados.
  2. O chassi esboça a caixa obrigatória.
  3. O script roda; a fase I mostra os conflitos e os pedidos de nó.
  4. O chassi responde e exporta de novo.
  5. O verificador aprova.
- Cada STEP entra num commit com o hash.
- O código vai para `python/` e `tests/` (padrão `check()`), com LEIA-ME e EDR do método, para sobreviver à troca de membros [I].

## Q5. Riscos e teste mínimo

1. **Aproximação otimista aprova o inválido** (já achei um caso). Teste: em todo finalista, a folga BRep tem de ser ≥ a folga da cápsula − 0,2 mm.
2. **Ida e volta pelo Fusion** (o teste que derruba a Q3): pôr a v20 como corpos-datum, exportar o STEP e ler de volta. Se nome ou posição não voltarem dentro de 0,01 mm, abandonar o STEP como interface e passar para a API.
3. **Referencial**: sem `REF_ORIGEM`, o Z segue dependendo do FH0/FH1.
4. **Conjunto viável vazio** mesmo com o F.6.2.3: aí o problema é de layout, e a fase I tem de mostrar isso antes de otimização cara [H].
5. **Cinemáticas divergentes**: comparar `kinlib` × `Corner` na v20 (MR e comprimento do amortecedor nos 25 pontos) antes de migrar.

**Recomendação em uma frase:** trocar o script por um pipeline modular no repositório, com estes elementos:
- CAD lido por geometria, com hash e datum nomeado;
- cápsulas conservadoras (raio envolvente) na busca;
- a cinemática já testada do `kinematics_model`;
- saída no schema de hardpoints;
- aprovação só por um verificador BRep independente, invalidada quando o STEP muda.

**Confiança: média-alta.** Principal incerteza: se nomes e posições sobrevivem à ida e volta Fusion → STEP → Python (não testado) e se existe solução viável antes de a caixa dianteira obrigatória ser desenhada.
