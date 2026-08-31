# Resultado da coleta (execução de 30/08/2026)

Rodado o workflow (`01` → `04`). Resumo:

| | |
|---|---|
| Artigos selecionados (Qualis A1/A2) | **24** — `referencias.ris`, `referencias.csv` |
| PDFs de acesso aberto baixados | **17** (SciELO/CC-BY + BMJ Global Health via Europe PMC) — `pdfs/` |
| Texto completo extraído | **17** — `texto/` |
| Fichas geradas (esqueleto) | **24** — `fichamento.ris` (+ espelho `fichamento.md`) |

## 7 artigos sem versão de acesso aberto — obter no Portal de Periódicos CAPES

Todos são de editoras comerciais (Elsevier/Lancet, Oxford) ou de servidor que
bloqueia download automático. Baixe cada PDF logado no
**Portal de Periódicos CAPES** (`periodicos.capes.gov.br`, acesso pela sua
instituição ou pela CAFe) e salve em `pdfs/<chave>.pdf`; depois rode
`python3 03_extrair_texto.py && python3 04_gerar_fichamento.py` de novo.

| chave | referência | DOI |
|---|---|---|
| `paim_2011_brazilian` | PAIM, J. et al. The Brazilian health system: history, advances, and challenges. The Lancet, v. 377, n. 9779, 2011. | 10.1016/S0140-6736(11)60054-8 |
| `castro_2019_brazil` | CASTRO, M. C. et al. Brazil's unified health system: the first 30 years and prospects for the future. The Lancet, v. 394, n. 10195, 2019. | 10.1016/S0140-6736(19)31243-7 |
| `barreto_2007_effect` | BARRETO, M. L. et al. Effect of city-wide sanitation programme on reduction in rate of childhood diarrhoea in northeast Brazil. The Lancet, v. 370, n. 9599, 2007. | 10.1016/S0140-6736(07)61638-9 |
| `rasella_2013_effect` | RASELLA, D. et al. Effect of a conditional cash transfer programme on childhood mortality. The Lancet, v. 382, n. 9886, 2013. | 10.1016/S0140-6736(13)60715-1 |
| `dixon_2006_financing` | DIXON, A. et al. Financing mental health services in low- and middle-income countries. Health Policy and Planning, v. 21, n. 3, 2006. | 10.1093/heapol/czl004 |
| `matheus_2021_design` | MATHEUS, R.; JANSSEN, M.; JANOWSKI, T. Design principles for creating digital transparency in government. Government Information Quarterly, v. 38, n. 1, 2021. | 10.1016/j.giq.2020.101550 |
| `boccolini_2011_relacao` | BOCCOLINI, C. S. et al. Relação entre aleitamento materno e internações por doenças diarreicas. Epidemiologia e Serviços de Saúde, v. 20, n. 1, 2011. | 10.5123/s1679-49742011000100003 |

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
