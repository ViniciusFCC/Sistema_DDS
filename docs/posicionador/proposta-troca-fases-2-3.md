# Proposta: trocar a ordem das fases 2 e 3 do posicionador (EDR-076)

**Status: PENDING_CONFIRMATION** (proposta do usuário, 2026-11-24, redigida com análise de impacto; ainda não é decisão).
Enquanto não for confirmada, vale a ordem do EDR-076, Decision item 4, e da spec §13.
Rótulos: **[F]** fato de fonte ou do repositório, **[I]** inferência, **[H]** hipótese.

## 1. O que se propõe

| | Ordem atual (EDR-076 item 4; spec §13) | Ordem proposta |
|---|---|---|
| Fase 1 | feita: E0 a E2 básico, sem δ, sem BRep exato, sem mutação | igual |
| Fase 2 | verificador completo: tolerância de fabricação δ, geometria exata (BRep), mutação 100 % | **add-in do Fusion** (leitura do design, execução, desenho do resultado) |
| Fase 3 | add-in do Fusion | **verificador completo** (δ, BRep exato, mutação) |

## 2. Por que

1. **A fase 3 atual depende de um dado que ainda não existe.** O δ (tolerância de fabricação) só sai de medições no carro
   (por exemplo o TX contra o CAD), que a equipe ainda não tem [F: pendência do usuário, 2026-11-24]. Sem δ, o verificador
   completo não tem valor de entrada e fica parado. [I]
2. **O add-in não depende de δ.** Ele lê o design, roda o núcleo e mostra o resultado. Entrega o que o usuário pediu em U4: reduzir
   a iteração humana (exportar STEP, nomear, rodar, abrir relatório). [F: diretriz U4]
3. **Nada perde validade esperando.** Na fase 1 nenhum candidato chega a VIAVEL, de propósito [F: README do posicionador]; o
   verificador completo não teria o que certificar antes de o CAD ter manga, freio, pedais e coluna e de a equipe definir as metas
   em conflito [I].

## 3. O que muda no trabalho

Pré-requisitos da nova fase 2 (hoje eram da fase 3):
- **Tirar o scipy do núcleo** (`brentq` em `mecanismo.py` e `minimize` em `busca.py`): trocar por bisseção e Nelder-Mead em
  numpy [F: decisão R9; relatório da API do Fusion: scipy não está documentado como suportado]. Exige teste de regressão
  contra a saída atual (TC-POS-050, 060, 070 a 076) para provar que os resultados não mudaram além da tolerância.
- **`AdaptadorFusion`** com a mesma interface do `AdaptadorSTEP` (`cad_step`): corpos por componente e prefixo, esferas `REF_` e `HP_`,
  obstáculos como cápsulas e caixas. Um teste de equivalência (spec CA-8): o mesmo design lido pelo STEP e pelo Fusion dá os mesmos
  obstáculos dentro da tolerância de leitura.
- **Execução fora do thread da interface**: o Fusion trava com script longo e `doEvents` em laço pode derrubá-lo; o padrão
  suportado é thread de trabalho sem chamar a API do Fusion nele, mais evento customizado [F: relatório da API do Fusion, docs
  oficiais da Autodesk]. O núcleo roda no thread; o add-in só lê antes e desenha depois.
- **Saída visual** sem alterar o design (`CustomGraphics`) e gravação dos pontos aceitos como pontos de esboço nomeados.

O que **não** muda: o núcleo (geometria, regulamento, mecanismo, varredura, busca), a configuração com procedência, o formato de
saída (schema de hardpoints, status PROVISIONAL), o rótulo "VERIFIED ≠ validado; cinemática NOT_VALIDATED" e a regra de que o
posicionador **não aprova**: o veredito continua no máximo CONDICIONAL até existir o verificador da fase 3.

## 4. Riscos da troca

1. **Não dá para testar um add-in do Fusion neste ambiente.** O Fusion só roda no computador da equipe [I]. O que se consegue aqui:
   núcleo e adaptador testados contra um substituto (stub) da API `adsk`, mais um roteiro de teste manual. A confirmação real tem de
   vir da equipe, com o log de uma execução no Fusion. É o maior risco de cronograma da proposta. Mitigação: entregar primeiro um
   **extrator** (add-in que só lê o design e grava um JSON que o núcleo já sabe ler), que valida a leitura no Fusion real
   antes do resto.
2. **Licença educacional.** Nenhum texto oficial lido confirma ou proíbe scripts e add-ins próprios [F: relatório da API do Fusion].
   Teste de 5 minutos na máquina da equipe (Utilities → Scripts and Add-ins, rodar um exemplo) antes de começar a fase.
3. **Colisão no Fusion sem geometria exata.** `measureMinimumDistance` não aceita corpo temporário e `analyzeInterference` só
   funciona com corpos ou ocorrências reais [F: docs da API]. Dentro do Fusion a folga continua conservadora (cápsulas e caixas, com
   o furo de cobertura de ~0,15 mm declarado), até o verificador exato da fase 3.
4. **Resultado lido como aprovação.** Um botão dentro do CAD parece oficial. O add-in mostra o mesmo veredito CONDICIONAL, o
   rótulo NOT_VALIDATED e a lista do que não foi modelado, no próprio painel.
5. **Dois adaptadores para manter** (STEP e Fusion) numa equipe que troca de membros. Mitigação: o teste de equivalência CA-8 e um
   só núcleo.
6. **Python do Fusion.** A versão embutida mudou (3.12 para 3.14, segundo o blog da Autodesk de 2026-01) e deve ser conferida com
   `sys.version`; dependências de terceiros só como cópia local na pasta do add-in [F: relatório da API do Fusion] [I: pode exigir
   que o núcleo rode só com numpy empacotado dentro do add-in].

## 5. Alternativas

- **A. Manter a ordem atual.** Mantém a sequência lógica "verificar bem, depois automatizar", mas a fase 2 fica parada à espera de
  δ, sem prazo. Vence se as medições da equipe saírem antes do add-in ficar pronto.
- **B. Trocar (esta proposta).** Avança o que não depende de dado externo. Vence enquanto δ estiver indisponível e a equipe ainda
  trocar STEP à mão.
- **C. Fazer só o extrator na fase 2 e deixar o resto do add-in para depois do verificador.** Menor risco por não depender de
  thread, desenho e API de interferência, mas entrega pouco da automação pedida.

**Recomendação [I, confiança média-alta]: B, com o extrator como primeiro marco.** Condição em que outra alternativa vence: se a
licença educacional não permitir scripts (a fase fica inviável, e A passa a ser a única), ou se as medições de δ chegarem antes de o
add-in ficar pronto.

## 6. O que fica para o usuário decidir

1. Confirmar B, A ou C.
2. Quem testa no Fusion e como a equipe devolve o log (arquivo de texto da execução).
3. Se o teste da licença educacional já pode ser feito.

## 7. Se for confirmada

Registrar no mesmo commit: EDR-076 (item 4 da Decision e o histórico), spec §9 e §13, `docs/posicionador/README.md`,
`docs/posicionador/pendencias-fase1.md` (a troca de scipy sobe de fase 3 para fase 2) e o `CLAUDE.md` (uma frase).
Nenhum ID novo além dos já autorizados (EDR-076; TC-POS-001 a 099).
