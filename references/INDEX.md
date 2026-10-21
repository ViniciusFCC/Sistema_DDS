# references/

Material didático e acadêmico (livros, artigos). Os PDFs e as conversões `.md`
ficam fora do Git (SPEC D3); só este índice é versionado.

| Arquivo | Onde está | Observação |
|---|---|---|
| `Definitive_Guide_DDS.pdf` (*Guia Definitivo de Dimensionamento Dinâmico da Suspensão*, EESC-USP Tupã) | `references/pdf/`; OCR em `references/md/definitive-guide/livro.md` | recebido do usuário em 2026-10-20 (a cópia em `importado-claude-ai/conhecimento/` tem 304 bytes e não abre). 153 folhas sem camada de texto; OCR docling + EasyOCR (pt, en) com `<!-- pdf:N -->` por folha. Página impressa = rodapé "N/140"; conferir citações na imagem. Resumo da arquitetura em `docs/arquitetura-planejada.md` |
| Milliken & Milliken, *Race Car Vehicle Dynamics*, SAE R-146, 1995, 5ª impressão | `references/pdf/`; conversão em `references/md/milliken-rcvd/livro.md` | digitalização sem camada de texto, duas páginas por folha. Página impressa p (par) na folha PDF n = (p + 38)/2 de p. 588 a 708 e n = (p + 36)/2 de p. 48 a 66 (conferido); fora disso, conferir no cabeçalho da página |
| T. D. Gillespie, *Fundamentals of Vehicle Dynamics*, SAE | `references/pdf/`; conversão em `references/md/gillespie-fvd/livro.md` | digitalização; edição a confirmar (o PDF não tem a página de créditos). Folhas PDF 54 a 222 têm duas páginas: p na folha (p + 70)/2 |
| D. Seward, *Race Car Design*, Palgrave, 2014 | `references/pdf/`; conversão em `references/md/seward-rcd/livro.md` | digitalização; página PDF = p + 11 (conferido em p. 89 e 132) |
| H. B. Pacejka, *Tyre and Vehicle Dynamics*, 2ª ed., Butterworth-Heinemann, 2006 | `references/pdf/`; conversão em `references/md/pacejka-tvd/livro.md` e texto bruto em `references/md/pacejka-txt/pacejka.txt` | PDF com texto; página PDF = p + 15. Magic Formula (versão 2004): eq. 4.E1-4.E78, p. 184-190. Convenções de sinal: Apêndice 1, p. 612 |

Origem dos quatro livros: `Z:\Suspensao\Biblioteca e Material Didático\Literatura
Dinâmica Veicular\Livros\` (biblioteca da equipe). O Pacejka não foi anexado na
conversa; entrou por ser a fonte primária que o EDR-042 pedia.

Conversão: docling com OCR (EasyOCR, GPU) e reconhecimento de fórmulas, uma vez por
livro. Cada página do `.md` começa com `<!-- pdf:N lado:E|D|- seq:K -->` (folha do PDF
e metade esquerda/direita). O OCR serve para busca; equações citadas na revisão foram
conferidas na imagem da página (`docs/revisao-metodologica.md`).

## Documentos de software e dados de pneu (recebidos do usuário em 2026-10-19)

| Arquivo | Onde está | Observação |
|---|---|---|
| OptimumKinematics, *Help File* (OptimumG) | `references/pdf/Kinematics_Help_File.pdf`; texto em `references/md/optimum-kinematics-help/livro.md` | 101 p., criado em 2019-06. Mesma contagem e estrutura do help oficial publicado (versão 2.0.2, 2019-05-20, `downloads.optimumg.com`); não comparado página a página. PDF com texto: página PDF = página impressa. É a REFERENCE de cinemática (EDR-004) |
| OptimumT, *Help File*, versão 1.0.14 (OptimumG) | `references/pdf/Tire_Help_File.pdf`; texto em `references/md/optimum-tire-help/livro.md` | 148 p., 2011. É o help publicado no site da OptimumG, mas é do OptimumT 1.x; o programa atual é o OptimumTire 2. Sistemas de coordenadas na seção 8.2 (p. 134-136); modelos Pacejka na 8.7 (p. 141-142) |
| TTC Round 6, Hoosier R25B 20.5x7-13 em aro de 7 in | `references/ttc/` (zip e `.tir` extraídos) | Quatro `.tir` PAC2002, USE_MODE 4, Stackpole para o TTC (2020): 8, 10, 12 e 14 psi. O de 12 psi tem os mesmos coeficientes de `data/Hoosier_R25B_13x7_TTC_provisional.tir`. Termos de uso do TTC não verificados: não versionar. A equipe usa o R60A, não o R25B |

Texto dos dois helps extraído com `pypdf` (camada de texto do PDF), com `<!-- pdf:N -->` no início de cada página;
figuras e equações conferidas na imagem da página.
| Adams 2024.1 Online Help, *Using the PAC2002 Tire Model* (Hexagon) | `references/pdf/Adams_2024_1_PAC2002_help.pdf`; texto em `references/md/adams-pac2002-help/livro.md` | 112 p., impresso do help HTML em 2026-10-19. Eixos (p. 6-8), definições de escorregamento (p. 9), rigidez vertical (p. 10-14), Fx/Fy puros (p. 27-31), combinados (p. 43-45), lado esquerdo/direito (p. 73-74). Equações são imagens: conferir na página |
