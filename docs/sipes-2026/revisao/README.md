# Revisão de literatura — workflow (SIPES 2026)

Fluxo reprodutível para montar a fundamentação teórica do trabalho sobre o
Farol-SS: **20 artigos de periódicos Qualis A/B**, PDFs em acesso aberto,
texto completo extraído, e um **fichamento em RIS** com resumo, referência
ABNT e candidatos a citação direta/indireta.

## O que o computador faz e o que VOCÊ faz

| Etapa | Automático | Seu (intelectual) |
|---|---|---|
| Selecionar artigos | busca no CrossRef restrita a ISSN Qualis A/B; `excluir:` remove os sem acesso aberto | conferir pertinência, ajustar termos |
| Baixar PDFs | só o que está em **acesso aberto** (Unpaywall/SciELO) | obter os faltantes pelo Portal de Periódicos CAPES / biblioteca |
| Extrair texto | PyMuPDF → `texto/*.txt` | conferir PDFs de imagem (precisam de OCR) |
| Fichar | metadados, **referência ABNT NBR 6023:2018**, resumo original extraído, trechos candidatos | **resumo com suas palavras, citações diretas com página, paráfrases** |
| Pôster | modelo pronto com a logo do evento | preencher com o conteúdo fichado |

> **Antiplágio.** Os campos `[PREENCHER APÓS LER O PDF]` são obrigatoriamente
> seus, escritos com suas palavras. Trechos marcados "CANDIDATO/extraído" vêm do
> PDF e **só viram citação direta depois de você conferir a página no arquivo**.
> Toda ideia de terceiro no texto final leva chamada autor-data (NBR 10520:2023);
> nada é copiado sem aspas + página.

## Rodar

```bash
cd docs/sipes-2026/revisao
pip install pymupdf requests pyyaml        # se preciso
python3 01_montar_ris.py        # -> referencias.ris, referencias.csv, selecao.json
python3 02_baixar_pdfs.py       # -> pdfs/*.pdf, pdfs/_faltantes.txt
python3 03_extrair_texto.py     # -> texto/*.txt
python3 04_gerar_fichamento.py  # -> esqueleto do fichamento
python3 05_fichar_analitico.py  # funde fichas_analiticas.yml (síntese autoral) no fichamento
```

**`fichas_analiticas.yml`** guarda a síntese redigida a partir da leitura de cada
PDF (resumo com suas palavras, citação direta com trecho literal, paráfrase,
conceito, relação com o Farol-SS). O `05` a funde nos campos `N1` do
`fichamento.ris`. As 20 fichas vêm preenchidas — resumo autoral, conceito, relação com o
Farol-SS, citação direta (trecho verbatim, página a conferir no PDF) e
indireta. 6 artigos sem acesso aberto foram retirados do trabalho; 2 sobre
metodologia de índice composto foram acrescentados.

Falhou algo? Amplie as `buscas` em `consulta.yml` (mais termos/anos/`n`), baixe
os PDFs faltantes manualmente para `pdfs/{chave}.pdf`, e rode 03 e 04 de novo.

## Arquivos gerados

| Arquivo | Conteúdo |
|---|---|
| `referencias.ris` | as 20+ referências (importar no Zotero/Mendeley com estilo ABNT) |
| `referencias.csv` | mesma lista, para conferência rápida |
| `selecao.json` | metadados completos (usado por 02–04) |
| `pdfs/` | PDFs em acesso aberto + `_faltantes.txt` |
| `texto/` | texto completo de cada PDF |
| `fichamento.ris` | **o fichamento** — 1 registro por artigo, com as fichas nos campos `N1` |
| `fichamento.md` | espelho legível do fichamento |

## Normas ABNT usadas (versões vigentes)

- **NBR 6023:2018** — referências (formatação em `lib_revisao.referencia_abnt`).
- **NBR 10520:2023** — citações em documentos (sistema autor-data; citação
  direta até 3 linhas entre aspas no corpo; com mais de 3 linhas, recuo de
  4 cm, fonte menor, sem aspas; sempre com página na citação direta).
- **NBR 15437:2006** — pôsteres técnicos e científicos (título, autoria,
  informações do conteúdo, instituição; a especificação de tamanho segue o
  edital do evento: 120 × 90 cm).
- **NBR 6028:2021** — resumo (para o texto de submissão).

Confirme se sua instituição adota alguma dessas com data diferente.

## Qualis

O filtro usa os ISSN de periódicos classificados como **A1/A2** em Saúde
Coletiva / Medicina II / Interdisciplinar no **Qualis Referência 2017–2020**
(Plataforma Sucupira). Reconfira o estrato de cada periódico em
`sucupira.capes.gov.br` — a classificação pode ter mudado.
