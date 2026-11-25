# Passagem da fase 2 do posicionador (Fusion), 2026-11-24

Para quem abre sessão nova. Fonte de verdade dos números: `RELATORIO-investigacao.md` (seções 1 a 8) e os JSON da sondagem nesta pasta. Aqui só o estado e o que falta.

## Onde está o trabalho
- Branch `ccr-4cb60a57-janeru` (remota e sincronizada; último commit `2174356`). O worktree da sessão anterior estava nesta branch.
- Decisão do usuário (2026-11-24): a fase 2 é o posicionador rodando **dentro do Fusion**; o certificador completo fica para depois das medições de tolerância. Regras do projeto: sem ID novo (EDR-, TC-) sem autorização; sem inferência de dado; commits sem linha de atribuição ao Claude.

## Feito e verificado (nesta fase)
1. **Etapa B da sondagem no Fusion** (T11 aberto, só leitura): Python embutido 3.14.7 sem numpy/scipy/pip; `measureMinimumDistance` ~1 ms; aceita corpo temporário (a documentação dizia que não); falha contra ocorrência inteira (`measurement failed`); 320 corpos sólidos, 27 no chassi. Script `T11_sondagem/T11_sondagem.py` v0.2 (saída em `C:\Projetos\fusion_sondagem3.json`; cópia instalada em `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\T11_sondagem\`).
2. **Pontos `REF_` e `HP_` existem como esferas Ø5 mm** dentro de `REF_REFERENCIAS` (3) e `HP_FRENTE` (18: 9 FL + 9 FR), não como pontos de construção.
3. **`python/posicionador/reconhecimento.py`**: categoria do componente pelo nome com nível de confiança (`exata`, `normalizada`, `mapa`, `inferida`, `nao_reconhecido`); só `exata/normalizada/mapa` são usáveis. Cópia idêntica em `T11_sondagem/` (conferida por SHA no teste). T11 real: 31 de 31 componentes `exata`.
4. **`python/posicionador/identificacao.py` + `tools/verificar_identificacao.py`**: portão geométrico (lado por Y do referencial `REF_`, contagens, esferas, o que é IGNORAR, nomes aninhados); saída 0 só sem FALHA. T11 real: 0 falhas, avisos revisáveis. Testes: `tests/test_posicionador_reconhecimento.py` (5 PASS) e `tests/test_posicionador_identificacao.py` (13 PASS: dados reais + 12 mutações). Registrados em `tools/rodar_testes.py` (a suíte inteira **não** foi rodada; só estes e dados/geometria do posicionador).
5. **Cópia do T11 com nomes corrigidos** no Fusion (projeto "Mecânica"): `T11_atuacao_v20_1_murilo_teste_nomes_corrigidos`; as duas rodas traseiras (antes `RODA_FE_ARO_13X7_TX:3/:4`, nome de roda dianteira esquerda) agora são `IGNORAR_TRAS_RODA_TX:1/:2`, via arquivo novo `IGNORAR_TRAS_RODA_TX` + *Replace Component* (o Fusion não deixa renomear nem desvincular componente vinculado). Portão na cópia: 0 falhas, 6 avisos; 0 de 46 ocorrências com geometria diferente do original. Original e `RODA_FE_ARO_13X7_TX` intactos.

## Pendências e decisões abertas
- **Revisão humana de `tabela_ignorados`** (saída do portão): o verificador não sabe se algo `IGNORAR` deveria ser obstáculo. Decisão do usuário, ainda não feita.
- Avisos restantes: `IGNORAR_PONTOS_V20_1` e `IGNORAR_PLANOS` vazios; 4 `TUBO_CARBONO` nos pushrods (explicados: tubo do pushrod, não do chassi).
- Quatro hardpoints FL do CAD diferem 7,6 a 20,6 mm do `hardpoints_T11_v20_script.csv` (TIE_OUT 7,6; UCA_IN_R 13,0; LCA_IN_F 14,8; LCA_IN_R 20,6); provavelmente CAD mais novo que o CSV, **não investigado**.
- Não verificado: juntas nas rodas trocadas; abertura da cópia por outro membro da equipe; custo de `analyzeInterference`/`booleanOperation` com o chassi; rotação do referencial `REF_` (aqui os eixos são paralelos aos do CAD).
- IDs de TC/EDR para reconhecimento e identificação: aguardam autorização (os testes estão sem ID).
- Arquivos novos na nuvem do Fusion que o usuário pode querer apagar: a cópia do T11 e `IGNORAR_TRAS_RODA_TX`.
- Próximo passo de projeto (proposta, ainda sem decisão): núcleo do posicionador em Python puro (bisseção e Nelder-Mead próprios, sem scipy), medindo distância corpo a corpo contra uma lista filtrada de corpos (varrer os 320 custa ~0,6 s por candidato); adaptador fino do Fusion (add-in) por último, conforme o usuário (U5).

## Operação do Fusion neste computador (aprendizados)
- Executar o script: `Shift+S`, buscar `T11_sondagem`, clicar em ▶; o aviso final se fecha com OK. Clicar na barra de abas do Fusion pode trocar a aba ativa: conferir o título antes de rodar.
- Python do repositório: `export UV_SYSTEM_CERTS=1` e `uv run python -X utf8 ...` (o `python` solto é o atalho da Store e trava). `uv run` no Windows não entende caminhos `/c/...`: use `C:/...`.
- Editar `tools/rodar_testes.py` só com a ferramenta de edição (um patch em Python reescreveu as quebras de linha e inflou o diff).

## Atualização (2026-11-24, fim da sessão do núcleo puro)
Feito (commits até `300482a`, sem push): núcleo em Python puro em `python/posicionador/puro/` (12 verificações contra o pacote numpy/scipy, TC-POS-130 a 141), hardpoints do CAD em `data/posicionador/hardpoints_T11_v20_1_cad.*` (alternativa ao v10; data do CAD não confirmada), IDs TC-POS-100 a 141 e EDR-077 (IMPLEMENTED) autorizados e registrados.
Ordem proposta (a mais econômica), nesta ordem:
1. Separar `tabela_ignorados` (saída de `tools/verificar_identificacao.py` sobre `fusion_sondagem3_copia_nomes_corrigidos_2026-11-24.json`) em dianteiro e traseiro e mostrar ao usuário: regra proposta "dianteiro fora do cálculo = obstáculo, traseiro = ignorado" (pendente de confirmação). Só leitura de JSON existente, sem Fusion.
2. Adaptador do Fusion (add-in) fino: lê o CAD pela API, aplica a regra de obstáculos, mede distância corpo a corpo (filtrar antes por caixa envolvente: 320 corpos ≈ 0,6 s por candidato) e chama o núcleo puro. Reaproveita o `cena_de` de `puro/varredura.py` (primitivos puros), o `reconhecimento.py` e o portão de identificação. Medição pela API substitui as SDFs de STEP; decidir se a cena do Fusion usa primitivos aproximados ou a API.
3. Rodar o núcleo no Python 3.14 do Fusion; confirmar a data do CAD (histórico de versões); suíte inteira; atualizar "Situação atual" do CLAUDE.md.
