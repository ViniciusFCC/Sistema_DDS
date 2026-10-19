# references/

Material didático e acadêmico (livros, artigos). Os PDFs e as conversões `.md`
ficam fora do Git (SPEC D3); só este índice é versionado.

| Arquivo | Onde está | Observação |
|---|---|---|
| `Definitive_Guide_DDS.pdf` | `importado-claude-ai/conhecimento/` | importado do claude.ai |
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
