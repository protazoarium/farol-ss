# Farol da Saúde & Saneamento (Farol-SS)

Monitor territorial de efetividade de gastos em saúde e vulnerabilidade sanitária. Cruza execução financeira com carga epidemiológica, déficit sanitário e vulnerabilidade social, produzindo o **IEAS — Índice de Efetividade da Alocação Sanitária** para os 185 municípios de Pernambuco (2020–2024).

## Status

| Camada | Estado | Nota |
|---|---|---|
| Scaffold, config, seeds | ✅ | 185 municípios, pesos/limiares em `conf/ieas.yml` |
| Ingestão — IBGE | ✅ | população, IPCA (deflator), malhas |
| Ingestão — SINAN (epidemiologia) | ✅ | 6 agravos × 5 anos, 185/185 municípios |
| Ingestão — SIH-SUS (internações DRSAI) | ✅ | grupo RD (AIH Reduzida), 185/185 × 5 anos |
| Ingestão — Censo 2022 (saneamento) | ✅ | déficit água/esgoto/lixo, 185/185 (retrato de 2022) |
| Ingestão — CadÚnico/SAGI (vulnerabilidade) | ✅ | taxa de extrema pobreza, 185/185 × 5 anos |
| Ingestão — SIOPS (L2, execução própria) | ✅ | R$/hab via TabNet legado, 184/185 × 5 anos |
| Ingestão — PNCP (L3, compras municipais) | ✅ | contratos + itens com preço unitário; adesão cresce ano a ano |
| Ingestão — Compras.gov.br (L3 federal) | ✅ | esfera federal em municípios de PE, 2021+, somada ao L3 |
| Ingestão — Portal da Transparência (L1) | ✅ | transferências sociais (proxy — Bolsa Família/Novo BF + BPC), 185/185 × 5 anos; `/transferencias` fundo a fundo dá 403 permanente com a chave gratuita |
| Camada silver | ✅ | um Parquet por domínio, grão `(cod_ibge, ano)` |
| Camada gold (fato município×ano) | ✅ | 925 linhas; grão único; L1/L2/L3 deflacionados p/ 2024 |
| IEAS (`index/ieas.py`) | ✅ | Necessidade completa (3/3) p/ os 185; 921/925 município-anos com cor (2024: 185/185) |
| Detectores de anomalia | ✅ (4 de 4) | desalinhamento + desabastecimento + sobrepreço + resíduo de regressão — 777 alertas |
| Painel Streamlit | ✅ | Home + 6 páginas (Farol/mapa, Município, Alertas, Fontes, Metodologia, API) — sistema de design institucional, diagrama do índice, Metodologia com todas as fórmulas em `st.latex` |
| API FastAPI | ✅ | `/municipios`, `/ieas`, `/alertas`, `/fontes` — JSON/CSV, sem auth |
| Testes | ✅ | 75 passando (`uv run pytest -q`) |
| Publicação | ⏳ | painel: `https://farol-ss.streamlit.app` (deploy pendente); repo: `github.com/protazoarium/farol-ss` |

Detalhe de cada bloqueio, correção de bug e da conclusão errada do *spike*
sobre o SIH está em `docs/spike-fontes.md`.
**Relatório técnico completo (pipeline, decisões, resultados): `docs/relatorio-tecnico.md`.**

## Início rápido

```bash
make install             # uv sync --all-extras (base + pipeline + api + sus + dev)
cp .env.example .env      # PORTAL_TRANSPARENCIA_API_KEY (chave gratuita, login gov.br)

make spike               # sonda as fontes federais, reporta cobertura real
make ingest              # IBGE + SINAN + SIH + PNCP + Compras.gov.br + SIOPS + CadÚnico + L1
make silver gold ieas    # camadas derivadas + IEAS + alertas
uv run pytest -q         # 70 testes

make app                 # painel Streamlit (localhost:8501)
make api                 # API aberta FastAPI (localhost:8000/docs)
```

Comandos de coleta retomável (para as fontes lentas/instáveis):

```bash
farol ingest-sih          # SIH-SUS (grupo RD)
farol ingest-l3-federal    # Compras.gov.br (L3 federal)
farol ingest-itens         # itens do PNCP com preço unitário (detector 3)
farol ingest-l1            # L1 (Portal da Transparência) — retomável
```

Dependências divididas em `pyproject.toml`: **base** (painel + API, leve) e
extras `pipeline` (ingestão + CLI), `api` (FastAPI), `sus` (PySUS), `dev`.
Deploy do painel: `requirements.txt` + `docs/deploy.md`.

## Arquitetura

Pipeline em camadas, sem servidor de banco — DuckDB lê Parquet direto do disco:

```
Fontes federais → bronze/ (bruto + manifest.json de proveniência)
                     ↓ ingest/*.py
                  silver/  (tipagem, cod_ibge 7 dígitos, grão por fonte)
                     ↓ transform/*.py
                  gold/fato_municipio_ano.parquet  (grão único: cod_ibge × ano, 925 linhas)
                     ↓ index/*.py
              ieas.py → gap, farol   |   anomalies.py → alertas explicáveis
```

**IEAS**: dois eixos normalizados por rank percentil dentro de PE.
- **N (Necessidade)**: epidemiológico (SINAN arboviroses + SINAN veiculação hídrica + SIH internações-saneamento) + saneamento (Censo 2022) + vulnerabilidade (CadÚnico)
- **A (Alocação)**: R$ per capita deflacionado — L1 repasses (Transparência, proxy) + L2 execução própria (SIOPS) + L3 compras (PNCP municipal + Compras.gov.br federal)
- **gap = rank(A) − rank(N)** ∈ [−1, 1] → colore o farol (vermelho = necessidade não atendida)
- **ieas = 1 − |gap|** ∈ [0, 1] → score de alinhamento, usado só para ranquear

Regra do cinza: um eixo cuja fração de componentes presentes cai abaixo do limiar em `conf/ieas.yml` (`cobertura_minima`) não tem IEAS calculado — o farol mostra cinza, nunca um número sobre dado majoritariamente ausente. O eixo Necessidade está completo para os 185 municípios; o cinza que resta é sobretudo município-ano sem contratação no PNCP naquele ano (`l3_maturidade_pncp_uf` mede essa adesão).

## Correção metodológica em relação à proposta original

A proposta assumia poder ver "compras de medicamentos por município" no Compras.gov.br — mas esse portal registra, na maior parte, compras de **órgãos federais** (por UASG), não de prefeituras. O eixo financeiro (Alocação) foi decomposto em três camadas genuinamente municipalizáveis:

| Camada | Fonte | Campo que geolocaliza |
|---|---|---|
| L1 — Repasse federal | Portal da Transparência (proxy: transf. sociais) | `codigoIbge` |
| L2 — Execução própria | SIOPS | município declarante |
| L3 — Contratação de insumos | **PNCP** (municipal) + Compras.gov.br (federal, `orgaoEntidadeEsferaId='F'`) | `unidadeOrgao.codigoIbge` |

O PNCP é a fonte validada com dado real que viabiliza a análise por município. O Compras.gov.br complementa com escopo federal (só a esfera `F`, para não duplicar), documentado como limitação, não escondido.

## Fontes de dados

Catálogo completo com URL, licença e link para `dados.gov.br` em `conf/sources.yml`. Ver `docs/spike-fontes.md` para o resultado da sondagem e todas as correções de endpoint feitas durante a implementação.

## Estrutura

```
reuso_projeto/
├── conf/
│   ├── ieas.yml            # pesos e limiares — sem número mágico no código
│   ├── sources.yml         # catálogo de fontes (URL, licença, dados.gov.br)
│   └── municipios_pe.csv   # SEED: 185 municípios (cod_ibge, meso/microrregião)
├── seeds/
│   ├── catmat_saude.csv    # categoria CATMAT → descrição/palavras-chave
│   ├── cid_saneamento.csv  # CID-10 sensíveis a saneamento (base do subíndice SIH)
│   └── agravo_insumo.yml   # agravo → insumo esperado (base do detector 4)
├── src/farol_ss/
│   ├── config.py
│   ├── io/{duck.py, municipios.py}       # I/O Parquet + resolução de código IBGE
│   ├── ingest/{base, spike, ibge, ibge_saneamento, sinan, sih, pncp, pncp_itens,
│   │           compras_gov, siops, cadunico, transparencia}.py
│   ├── transform/{silver_epidemiologia, silver_pncp, gold_municipio_ano}.py
│   ├── index/{normalize, ieas, anomalies}.py
│   ├── proveniencia.py     # catálogo de fontes × manifesto de coleta
│   ├── api/main.py         # API aberta FastAPI (JSON/CSV)
│   ├── app/                # painel Streamlit — Home.py + pages/1..6 + tema.py + conteudo.py
│   └── cli.py
├── tests/                  # 70 testes — regressão de bugs reais, fixtures, fumaça de API
├── data/                   # derivados versionados (~1,7 MB); bruto gitignored
│   ├── bronze/silver/gold/
│   └── manifest.json       # proveniência: url, sha256, timestamp, linhas
├── docs/
│   ├── spike-fontes.md     # bloqueios, correções de endpoint, bugs encontrados
│   ├── concurso-cgu.md     # regras do Concurso de Reúso de Dados Abertos da CGU
│   ├── deploy.md            # deploy do painel no Streamlit Community Cloud
│   ├── publicacao-reuso.md  # valores prontos para os formulários do concurso
│   ├── passo-a-passo-dados-gov.md  # navegação no dados.gov.br p/ publicar o reúso
│   ├── relatorio-tecnico.md # relatório técnico completo (fonte)
│   └── relatorio-tecnico.docx # idem, formato acadêmico (gerar com scripts/gerar-docx.sh)
└── .streamlit/config.toml
```

## Lições da implementação

Vale ler `docs/spike-fontes.md` na íntegra, mas os pontos que mais mudariam uma reimplementação:

- **Nunca confie em documentação de API — nem numa conclusão sua sobre uma biblioteca — sem testar contra dado real.** Três endpoints do plano original estavam errados (IBGE malhas, Compras.gov.br, PNCP `/v1/contratos`); e o *spike* concluiu erradamente que o SIH não tinha grupo utilizável (a chamada certa é `pysus.sih("PE", ano, mes, group="RD")`).
- **`pysus.sinan(..., as_dataframe=True)` materializa o Brasil inteiro em memória.** Matou o processo duas vezes pelo OOM killer numa máquina de 7,5 GB. Correção: pedir paths (sem `as_dataframe`) e filtrar com DuckDB antes de tocar pandas.
- **Código de município do DATASUS é 6 dígitos sem dígito verificador**, não um código de 7 dígitos truncado. Reconstrução ingênua (`lpad`, `lstrip`) corrompe ou descarta dado silenciosamente — centralizado em `io.municipios.resolve_por_codigo`.
- **`drop_duplicates()` é perigoso em dado de notificação.** Colapsar por (código, data, classificação) subcontou dengue em ~66% num teste — várias pessoas notificadas no mesmo dia com a mesma classificação é o normal, não duplicata.
- **PNCP é operacionalmente instável**: a mesma consulta respondeu timeout, HTTP 204 sem corpo e 200 normal em tentativas sucessivas. A ingestão pagina com try/except por página, preservando progresso parcial.
- **A chave gratuita do Portal da Transparência tem dois tetos**: `/transferencias` (repasse fundo a fundo) é 403 permanente, e volume alto sustentado bloqueia a chave por horas. A coleta de L1 é retomável por construção.

## Licença

Dados públicos das fontes federais (IBGE, DATASUS, PNCP, CGU, MDS). Análise e visualização (IEAS, painel, API) são obra derivada sob domínio público.
