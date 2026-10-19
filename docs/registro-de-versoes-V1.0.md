# Registro de versões — Sistema_DDS — V1.0

Data: 2026-10-09. Regra (usuário): começa em V1.0; o decimal sobe a cada pequena implementação (V1.0 → V1.1 …). Arquivos `.py` usam `_V1_0` no nome porque ponto no nome impede `import`.

## Mapa de arquivos (recebido → V1.0)
| Arquivo recebido (projeto) | md5 (8 primeiros) | Arquivo V1.0 |
|---|---|---|
| `engineering-standard-v0_1-suspensao-fsae.md` | `35b53531` | `engineering-standard-V1.0-suspensao-fsae.md` |
| `arquitetura-consolidada-suspensao-fsae.md` | `d6455536` | `arquitetura-consolidada-V1.0-suspensao-fsae.md` |
| `data-contract-v0_1-excel-python.md` | `d474c1b1` | `data-contract-V1.0-excel-python.md` |
| `suspension_model.py` | `bdf85d6a` | `suspension_model_V1_0.py` |
| `test_suspension_model.py` | `9218b68c` | `test_suspension_model_V1_0.py` |
| `kinematics_model.py` | `4ba49d2c` | `kinematics_model_V1_0.py` |
| `test_kinematics_model.py` | `492757d7` | `test_kinematics_model_V1_0.py` |
| `FSAE_EV_Suspension_Fase1.xlsx` | `162dd9e1` | `FSAE_EV_Suspension_Fase1_V1.0.xlsx` |

O `FSAE_EV_Suspension_Fase1.xlsx` do projeto é a versão original; a V1.0 inclui o Decision Register consolidado (DR-010/011, colunas Status e Origem), a correção de textos desatualizados e o registro no `15_CHANGELOG`.

## Alterações da V1.0 (todas verificadas nos arquivos)
- **Standard:** `SUS-404/405` citavam `TC-010` como teste de sinal (TC-010 é o cálculo inverso de frequência); contagem 38→39 fichas; bullet do Bloco J sobre Design Mode de rolagem atualizado (equação em `SUS-208`); log de validação de kinematics (11/11) e pendências; nomes de arquivo.
- **Arquitetura:** `AS_r` ganha `TF_r` (como em `SUS-302`); `SUS-301/302` passam a depender de `SUS-406`, `SUS-013`, `SUS-014`; adendo com os IDs criados depois da matriz; nota de numeração canônica de TC.
- **Data Contract:** nomes de aba para a arquitetura de 16 abas; seção 5 com o que o contrato descreve mas o código ainda não faz.
- **kinematics:** mensagem de erro de retas paralelas dizia "vista frontal" também na vista lateral; agora indica a vista. `TC-KIN-006` passou a checar isso (sem mudar a contagem de 11 testes). Docstring atualizada (inclui SUS-406).
- **Planilha:** `00_README` (versão, Anti-dive/squat já implementados em `06_SUSPENSION`), `07_KINEMATICS` (11/11), nomes de arquivo e `01_SETUP` (script V1.0).

## Divergências conhecidas que continuam abertas
- **Guide (`Definitive_Guide_DDS.pdf`):** numeração de TC e de DR diverge; DR-008 do Guide (Tire) é DR-011 na planilha. Guide a alinhar depois (decisão do usuário: foco na planilha).
- **Guide no projeto:** a cópia do projeto tem 304 bytes e está em branco; a versão legível (14,9 MB) está no upload da conversa. Substituir a do projeto.
- `SUS-203`/`SUS-204` sem ficha; schema de hardpoints indefinido; `07_KINEMATICS` ainda com valores placeholder (o Guide, cap. 6.9, pede N/A/TBD).
