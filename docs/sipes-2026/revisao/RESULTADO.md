# Resultado da coleta (execução de 30/08/2026)

Rodado o workflow (`01` → `04`). Resumo:

| | |
|---|---|
| Artigos selecionados (Qualis A1/A2) | **24** — `referencias.ris`, `referencias.csv` |
| PDFs de acesso aberto baixados | **18** (SciELO/CC-BY + BMJ Global Health + Epidemiol. Serv. Saúde via SciELO-IEC) — `pdfs/` |
| Texto completo extraído | **18** — `texto/` |
| Fichas analíticas redigidas | **24 de 24** — 18 a partir do texto integral, 6 a partir do resumo publicado (PubMed/Semantic Scholar) — `fichamento.ris` / `fichamento.md` |

## 5 artigos sem PDF — ficha redigida a partir do resumo publicado; obter o texto integral na CAPES para as citações diretas

Boccolini (Epidemiol. Serv. Saúde) foi obtido do SciELO-IEC e já tem ficha
completa. Os cinco abaixo (Elsevier/Lancet, Oxford, Elsevier/GIQ) têm ficha
**parcial**, redigida a partir do resumo publicado — o resumo autoral, o
conceito, a relação com o Farol-SS e a citação indireta já estão prontos; falta
o **trecho literal e a página** da citação direta, que exigem o texto integral.
Baixe cada PDF logado no **Portal de Periódicos CAPES**
(`periodicos.capes.gov.br`, via instituição ou CAFe), salve em
`pdfs/<chave>.pdf`, acrescente a citação direta em `fichas_analiticas.yml`
(removendo `tipo: parcial`) e rode `03` e `05` de novo.

| chave | referência | DOI |
|---|---|---|
| `paim_2011_brazilian` | PAIM, J. et al. The Brazilian health system: history, advances, and challenges. The Lancet, v. 377, n. 9779, 2011. | 10.1016/S0140-6736(11)60054-8 |
| `castro_2019_brazil` | CASTRO, M. C. et al. Brazil's unified health system: the first 30 years and prospects for the future. The Lancet, v. 394, n. 10195, 2019. | 10.1016/S0140-6736(19)31243-7 |
| `barreto_2007_effect` | BARRETO, M. L. et al. Effect of city-wide sanitation programme on reduction in rate of childhood diarrhoea in northeast Brazil. The Lancet, v. 370, n. 9599, 2007. | 10.1016/S0140-6736(07)61638-9 |
| `rasella_2013_effect` | RASELLA, D. et al. Effect of a conditional cash transfer programme on childhood mortality. The Lancet, v. 382, n. 9886, 2013. | 10.1016/S0140-6736(13)60715-1 |
| `dixon_2006_financing` | DIXON, A. et al. Financing mental health services in low- and middle-income countries. Health Policy and Planning, v. 21, n. 3, 2006. | 10.1093/heapol/czl004 |
| `matheus_2021_design` | MATHEUS, R.; JANSSEN, M.; JANOWSKI, T. Design principles for creating digital transparency in government. Government Information Quarterly, v. 38, n. 1, 2021. | 10.1016/j.giq.2020.101550 |

> `barreto_2007` e `rasella_2013` são referências de peso (efeito de saneamento
> e de transferência de renda sobre desfechos infantis) — vale o esforço de
> obtê-las.

## Artigos que talvez você queira substituir (pouco aderentes)

Ao revisar `referencias.csv`, avalie trocar por termos de busca melhores em
`consulta.yml` (e rodar `01` de novo):

- `cotrim-junior_2020_crescimento` (leitos de UTI na pandemia) — só se for usar o argumento de desigualdade regional de oferta.
- `pinheiro_2020_analise` / `batista_2019_registro` — entram pelo método (análise espacial; qualidade de SIS), não pelo tema; mantenha 1 de cada no máximo.

## Próximo passo

Ler os 17 PDFs em `texto/` (ou os próprios arquivos em `pdfs/`) e preencher os
campos `[PREENCHER APÓS LER O PDF]` de `fichamento.ris`/`fichamento.md` — o
resumo com **suas palavras**, as citações diretas com a **página real** e as
paráfrases. Só então montar a introdução e a discussão do pôster.
