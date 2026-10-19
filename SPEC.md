# SPEC — Migração do Sistema_DDS para o Claude Code

Registro vivo do fluxo de execução. Criado em 2026-10-18. Base: veredito do conselho (D1–D5), aprovado pelo usuário em 2026-10-18, e as respostas da entrevista.

## 1. Objetivo

Transformar os artefatos V2.4 exportados do claude.ai num projeto local versionado com Git e **provar que os resultados registrados se reproduzem nesta máquina**, antes de qualquer reorganização ou renomeação.

## 2. Não objetivos

- Decidir as pendências de engenharia (EDR-018, 023–027, 033–036, 040).
- Alterar fórmulas da planilha, equações dos modelos ou dados.
- Converter os scripts de teste para pytest.
- Automatizar o teste da planilha (COM/Excel). Fica para a fase B, com um EDR próprio.
- Configurar CI (GitHub Actions), Zotero ou converter livros para `references/`.
- Recuperar os documentos ausentes listados no §11 do handoff. Eles continuam registrados como lacuna.

## 3. Decisões aprovadas

| ID | Decisão |
|---|---|
| D1 | Versionamento híbrido: Git com tags para código e docs; a planilha entregue à equipe mantém a versão no nome. A renomeação para nomes estáveis acontece só na fase B, depois da reprodução, e exige um EDR novo que revise o EDR-017. |
| D2 | O `test_workbook_V2_4.py` não roda localmente: depende de LibreOffice e de `/mnt/skills/public/xlsx/scripts/recalc.py` (linhas 10 e 28). Na fase A ele é registrado como **NÃO EXECUTÁVEL**. Na fase B, é substituído por um recálculo via pywin32/COM no Excel, com EDR próprio. |
| D3 | PDFs de livros e suas conversões `.md` ficam fora do Git. Entra só `references/INDEX.md`. |
| D4 | Repositório GitHub **privado**. Fora do Git: `*.tir`, PDFs, `importado-claude-ai/`, `Sistema_DDS_CONTEXTO_COMPLETO.md`. Sem Git LFS. |
| D5 | Ordem: backup → commit 0 (cópia fiel) → commit 1 (portabilidade) → reprodução → tag `v2.4.1` → push. A renomeação vem depois. |
| E1 | Fase A com **pasta plana** `python/` (módulos + testes + dados que os testes leem), igual ao layout do sandbox. A separação em `python/`, `tests/` e `data/` vai junto com a renomeação, na fase B. |
| E2 | No fim da fase A, criar `ViniciusFCC/Sistema_DDS` privado e fazer o push, depois de mostrar a lista do que sobe. |
| E3 | Backup em `C:\Users\vferr\OneDrive\Documents\`, com o SHA-256 num `.txt`. |

## 4. Estrutura da fase A

```
Sistema_DDS/
├── CLAUDE.md                     (passo 3 do fluxo global)
├── SPEC.md                       (este arquivo)
├── HANDOFF-Sistema_DDS.md        (versionado; índice da migração)
├── MANIFEST.sha256               (origem e hash de cada arquivo copiado)
├── pyproject.toml / uv.lock      (Python 3.13; numpy, scipy, openpyxl)
├── python/                       (pasta plana: módulos, testes, mutação, build e dados lidos por eles)
├── excel/                        (planilha V2.4 entregue e V2.1, insumo do build)
├── data/                         (CSVs que nenhum script lê por caminho fixo)
├── docs/                         (EDR, Standard, arquitetura, data contract, schema, registros de versões)
│   └── migracao/                 (logs de verificação desta migração)
├── tools/                        (scripts de verificação da migração)
├── references/                   (só INDEX.md versionado)
└── importado-claude-ai/          (somente leitura; fora do Git)
```

### 4.1 Inventário de cópia (commit 0)

Origem: `importado-claude-ai/saidas-conversas/`. A cópia é exata e o hash vai para o `MANIFEST.sha256`.

| Destino | Arquivos (origem) |
|---|---|
| `python/` | `tire/tire_model_V2_4.py`, `tire/test_tire_model_V2_4.py`, `tire/test_tire_oracles_V2_4.py`, `tire/mutation_tire_V2_4.py`, `tire/build_workbook_V2_4.py`, `tire/test_workbook_V2_4.py`, `tire/layout_V2_4.json`, `tire/Hoosier_R25B_13x7_TTC_provisional.meta.json`, `kin/suspension_model_V2_1.py`, `kin/test_suspension_model_V2_1.py`, `kin/kinematics_model_V2_0.py`, `kin/test_kinematics_model_V2_1.py`, `kin/hardpoints_V2_0.py`, `kin/test_hardpoints_V2_1.py`, `kin/hardpoints_synthetic_V2.0.csv`, `kin/hardpoints_synthetic_V2.0.meta.json` |
| `python/` (fora do Git) | `tire/Hoosier_R25B_13x7_TTC_provisional.tir` |
| `excel/` | `tire/FSAE_EV_Suspension_Fase1_V2_4.xlsx` (entregue), `kin/FSAE_EV_Suspension_Fase1_V2.1.xlsx` (insumo do build) |
| `data/` | `kin/kinematics_sweep_synthetic_V2.0.csv`, `kin/placeholder-dependency-map-V2.1.csv`, `tire/tire_comparison_grid_V2_3.csv` |
| `docs/` | `tire/Engineering_Decision_Register.md`, `tire/data-contract-V2_4-excel-python.md`, `kin/engineering-standard-V2.0-suspensao-fsae.md`, `kin/arquitetura-consolidada-V2.0-suspensao-fsae.md`, `kin/hardpoint-schema-V2.0.md`, `kin/registro-de-versoes-V1.0.md`, `kin/registro-de-versoes-V2.0.md`, `tire/registro-de-versoes-V2_2.md`, `tire/registro-de-versoes-V2_3.md`, `tire/registro-de-versoes-V2_4.md` |

As versões anteriores (v0.1, V1.0, V2.0–V2.3) continuam só em `importado-claude-ai/` e no backup.

## 5. Requisitos

- **R1.** Nenhum arquivo de `importado-claude-ai/` é editado, movido ou apagado.
- **R2.** O commit 0 tem só cópias byte a byte. Toda edição vai para commits seguintes, separados por propósito.
- **R3.** O commit 1 (portabilidade) só pode:
  - trocar `/mnt/project` e `/home/claude/work` em `build_workbook_V2_4.py` por argumentos com padrão relativo ao script (`SRC`, `OUT`, `TIR`, saída do layout);
  - trocar `python3` por `sys.executable` em `mutation_tire_V2_4.py`;
  - adicionar à mutação a pré-checagem (o original precisa dar `0 FAIL`) e o critério "detectado = a saída contém FAIL com código ≠ 0".

  Nenhuma equação, fórmula, valor ou critério de teste muda.
- **R4.** Os scripts rodam com `uv run python -X utf8` (UTF-8 sem editar o código) e com o diretório de trabalho em `python/`.
- **R5.** Divergência entre o resultado local e o registrado: parar, registrar e investigar pelo §2.6 do handoff. Nunca ajustar para bater.
- **R6.** O `test_workbook_V2_4.py` nunca é contado como aprovado na fase A.
- **R7.** A ferramenta de verificação (`tools/`) é código novo, num commit próprio. Ela não modifica os scripts que verifica.
- **R8.** Mensagens de commit seguem a `fluxo-github` e terminam com a linha de coautoria.

## 6. Critérios de aceitação

| ID | Critério | Verificação |
|---|---|---|
| CA-01 | O backup zip de `importado-claude-ai/` existe na OneDrive, com SHA-256 registrado, e tem o mesmo número de arquivos e os mesmos hashes da pasta | Script compara as entradas do zip com a pasta |
| CA-02 | Os arquivos do commit 0 batem com a origem | `MANIFEST.sha256` verificado contra `importado-claude-ai/`; tag `v2.4.0-import` |
| CA-03 | Nenhum `.tir`, `.pdf`, dump ou arquivo de `importado-claude-ai/` está no Git | `git ls-files` filtrado |
| CA-04 | O diff do commit 1 contém só as mudanças permitidas por R3 | Revisão do `git diff` linha a linha, mostrada ao usuário |
| CA-05 | Contagens reproduzidas, com 0 FAIL: pneu 43, oráculos 5, suspensão 42, cinemática 53, hardpoints 35 | `tools/` interpreta a linha "N PASS, M FAIL, de T testes" de cada script |
| CA-06 | Mutação 23/23 detectados, com a pré-checagem do original passando | Saída da mutação protegida |
| CA-07 | A planilha regenerada a partir da V2.1 tem 347 fórmulas com texto idêntico, célula a célula, ao da V2.4 entregue, e os mesmos valores nas células sem fórmula | Script com openpyxl lista todas as diferenças (o esperado é nenhuma) |
| CA-08 | O `layout_V2_4.json` regenerado é igual ao entregue | Comparação de JSON |
| CA-09 | O `test_workbook_V2_4.py` aparece no log como NÃO EXECUTÁVEL, com o motivo | Log de verificação |
| CA-10 | Ambiente registrado (Python, numpy, scipy, openpyxl) | `uv.lock` e o log `docs/migracao/verificacao-V2.4-local.md` |
| CA-11 | `CLAUDE.md` do projeto criado | Passo 3 do fluxo global |
| CA-12 | Tag `v2.4.1` e push para o repositório privado, depois de você aprovar a lista de arquivos | `git ls-remote` e visibilidade conferida no GitHub |

Contagens esperadas, com a fonte: pneu, oráculos e mutação vêm de `registro-de-versoes-V2_4.md:16`. Suspensão 42, cinemática 53 e hardpoints 35 vêm do HANDOFF §6.2. Não existe registro de versões da V2.1 para confirmar esses três números. Se a contagem local divergir só nesses três, a primeira suspeita é a fonte do número, e não o código.

## 7. Plano de verificação

1. `tools/verificar_backup.py`: CA-01.
2. `tools/verificar_manifest.py`: CA-02.
3. `tools/rodar_testes.py`: roda cada script com `sys.executable -X utf8` e `cwd=python/`, interpreta o resumo, compara com a tabela esperada e grava `docs/migracao/verificacao-V2.4-local.md` (CA-05, CA-06, CA-09, CA-10).
4. `tools/comparar_planilhas.py`: CA-07 e CA-08, com a planilha gerada numa pasta temporária, nunca por cima da entregue.
5. CA-03 e CA-04: inspeção com `git` na linha principal, mostrada a você.

## 8. Divisão do trabalho (etapa 3)

Todas as partes são sequenciais e pequenas. Cada uma depende do commit anterior, então **não há subagentes**: tudo roda na linha principal.

| Parte | Depende de | Responsável |
|---|---|---|
| Backup (CA-01) | — | principal |
| Estrutura, `.gitignore`, commit 0 (CA-02, CA-03) | backup | principal |
| `pyproject` / `uv` (CA-10) | commit 0 | principal |
| Ferramentas de verificação, em commit próprio | commit 0 | principal |
| Rodar os originais antes da portabilidade (registro do "antes") | ferramentas | principal |
| Commit 1, portabilidade (CA-04) | registro do "antes" | principal |
| Reprodução (CA-05 a CA-09) | commit 1 | principal |
| CLAUDE.md (CA-11) | — (passo 3 do fluxo global) | principal |
| Tag e push (CA-12) | tudo acima, mais a sua aprovação | principal |

## 9. Riscos e premissas frágeis

- **P1.** A V2.1 local (`..._V2.1.xlsx`, SHA-256 16242F19…, igual em `arquivos/` e `kin/`) é a mesma `/mnt/project/..._V2_1.xlsx` usada no build. Não há como verificar. Se o CA-07 falhar, é a primeira suspeita.
- **P2.** As versões de numpy e scipy do sandbox são desconhecidas. Uma diferença numérica pequena pode mudar um `check` com tolerância apertada. Nesse caso vale o R5.
- **P3.** O `.tir` fica fora do Git. Um clone novo não roda os testes de pneu nem o build. O README de `python/` diz de onde ele vem.
- **P4.** A proveniência do `.tir` é contraditória: o meta.json diz "via terceiro" e `build_workbook_V2_4.py:422` diz "baixado direto do TTC". Fica registrada, sem resolução por inferência.
- **P5.** Os termos de uso do TTC não foram verificados. A decisão D4 é conservadora e não depende deles.
- **P6.** Rodar os scripts originais antes do commit 1 vai falhar no build (caminhos `/mnt`) e dar falso positivo na mutação (`python3` é o atalho da Store, verificado). Esse resultado é registrado como o "antes", não como falha da migração.

## 10. Decisões em aberto

- **[ABERTO] A1.** Onde a equipe encontra a planilha vigente (pasta da equipe ou GitHub Releases). Recomendação: decidir na fase B, junto com a versão gravada dentro da planilha. Não afeta a fase A.
- **[ABERTO] A2.** O número do EDR que revisa o EDR-017. Recomendação: o próximo livre, EDR-043, criado só com a sua autorização (regra de não criar IDs sem aprovação). Fica para a fase B.
- **[ABERTO] A3.** `test_t09_reference_case.py` (pasta `plan/`) importa `suspension_model` da v0.1, e não da V2.1. Recomendação: fora da fase A; avaliar na fase B se ele deve ser portado para a V2.1.

## 11. Fase B (depois da `v2.4.1`, fora do mínimo)

1. EDR-043, que revisa o EDR-017 (precisa da sua aprovação).
2. Commit de reestruturação e renomeação (`git mv` para `python/`, `tests/` e `data/`, com nomes estáveis e imports e caminhos ajustados). Testes de novo, com o mesmo resultado da fase A.
3. Versão gravada dentro da planilha (estrutura nova, precisa de aprovação) e o local de distribuição (A1).
4. Recálculo via COM no Excel, substituindo o `recalc.py`, com EDR próprio. O 19/19 deve ser reproduzido, e uma divergência segue o §2.6.

## 12. Ordem no fluxo global

Esta SPEC cobre o passo 2. A construção (seção 8) só começa depois dos passos 3 (CLAUDE.md), 4 (ferramentas) e 5 (aprovação da proposta única).
