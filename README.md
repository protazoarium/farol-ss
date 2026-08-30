# Farol da Saúde & Saneamento (Farol-SS)

Monitor territorial de efetividade de gastos em saúde e vulnerabilidade sanitária. Cruza execução financeira com carga epidemiológica, déficit sanitário e vulnerabilidade social, produzindo o **IEAS — Índice de Efetividade da Alocação Sanitária** para os 185 municípios de Pernambuco.

## Status

| Camada | Estado | Nota |
|---|---|---|
| Scaffold, config, seeds | ✅ | 185 municípios, pesos/limiares em `conf/ieas.yml` |
| Ingestão — IBGE | ✅ | população, IPCA, malhas |
| Ingestão — SINAN (epidemiologia) | ✅ | 6 agravos × 5 anos, 185/185 municípios |
| Ingestão — PNCP (L3, compras municipais) | ✅ | 6.150 contratos, 172/185 municípios, 2021–2024 |
| Ingestão — Compras.gov.br (L3 federal) | ⏳ | endpoint validado no spike, módulo não escrito |
| Ingestão — SIOPS (L2) | 🔴 | sem API real; TabNet legado exige scraping de formulário |
| Ingestão — SNIS (saneamento) | 🔴 | domínio `app4.mdr.gov.br` não resolve DNS |
| Ingestão — Portal da Transparência (L1) | 🔴 | HTTP 403 mesmo com chave ativada |
| Ingestão — CadÚnico (vulnerabilidade) | ⏳ | não iniciado |
| Camada silver | ✅ | epidemiologia (3.111 linhas) + PNCP (6.150 linhas) |
| Camada gold (fato município×ano) | ✅ | 925 linhas; população + epidemiologia + L3 deflacionado; L1/L2/saneamento entram como NULL |
| IEAS (`index/ieas.py`) | ✅ | testado com fixtures sintéticas (vermelho/verde/azul/cinza); hoje 100% cinza pela regra de cobertura |
| Detectores de anomalia | ✅ (2 de 4) | desalinhamento estrutural + suspeita de desabastecimento (548 alertas) |
| Painel Streamlit | ✅ | 6 páginas: Home, Farol (mapa), Município, Alertas, Metodologia, API |
| API FastAPI | ✅ | `/municipios`, `/ieas`, `/alertas`, `/fontes` — JSON/CSV, sem auth |

Detalhe de cada bloqueio e das correções de bug está em `docs/spike-fontes.md`.
**Relatório técnico completo (pipeline, decisões, resultados): `docs/relatorio-tecnico.md`.**

## Início rápido

```bash
make install             # uv sync --all-extras (base + pipeline + api + sus + dev)
cp .env.example .env     # PORTAL_TRANSPARENCIA_API_KEY, se/quando destravar

make spike               # sonda as fontes federais, reporta cobertura real
make ingest              # baixa IBGE + SINAN + PNCP para data/bronze e silver/
make silver gold ieas    # camadas derivadas + IEAS + alertas
uv run pytest -q         # 51 testes

make app                 # painel Streamlit (localhost:8501)
make api                 # API aberta FastAPI (localhost:8000/docs)
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
                  gold/fato_municipio_ano.parquet  (grão único: cod_ibge × ano)
                     ↓ index/*.py
              ieas.py → gap, farol   |   anomalies.py → alertas explicáveis
```

**IEAS**: dois eixos normalizados por rank percentil dentro de PE.
- **N (Necessidade)**: epidemiológico (SINAN) + saneamento (SNIS, pendente) + vulnerabilidade (CadÚnico, pendente)
- **A (Alocação)**: R$ per capita deflacionado — L1 repasses + L2 execução própria + L3 compras
- **gap = rank(A) − rank(N)** ∈ [−1, 1] → colore o farol (vermelho = necessidade não atendida)
- **ieas = 1 − |gap|** ∈ [0, 1] → score de alinhamento, usado só para ranquear

Regra do cinza: um eixo cuja fração de componentes presentes cai abaixo do limiar em `conf/ieas.yml` (`cobertura_minima`) não tem IEAS calculado — o farol mostra cinza, nunca um número sobre dado majoritariamente ausente.

## Correção metodológica em relação à proposta original

A proposta assumia poder ver "compras de medicamentos por município" no Compras.gov.br — mas esse portal registra compras de **órgãos federais** (por UASG), não de prefeituras. O eixo financeiro (Alocação) foi decomposto em três camadas genuinamente municipalizáveis:

| Camada | Fonte | Campo que geolocaliza |
|---|---|---|
| L1 — Repasse federal | Portal da Transparência | `codigoIbge` |
| L2 — Execução própria | SIOPS | município declarante |
| L3 — Contratação de insumos | **PNCP** (municipal) + Compras.gov.br (federal, escopo limitado) | `unidadeOrgao.codigoIbge` |

O PNCP é a fonte validada com dado real que viabiliza a análise por município (ex.: "Prefeitura Municipal de Paulista" com valores de contrato). Compras.gov.br complementa com escopo federal, documentado como limitação, não escondido.

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
│   ├── cid_saneamento.csv  # CID-10 sensíveis a saneamento
│   └── agravo_insumo.yml   # agravo → insumo esperado (base do detector 4)
├── src/farol_ss/
│   ├── config.py
│   ├── io/{duck.py, municipios.py}       # I/O Parquet + resolução de código IBGE
│   ├── ingest/{base.py, spike.py, ibge.py, sinan.py, pncp.py}
│   ├── transform/{silver_epidemiologia.py, silver_pncp.py, gold_municipio_ano.py}
│   ├── index/{normalize.py, ieas.py, anomalies.py}
│   ├── proveniencia.py     # catálogo de fontes × manifesto de coleta
│   ├── api/main.py         # API aberta FastAPI (JSON/CSV)
│   ├── app/                # painel Streamlit — Home.py + pages/1..5
│   └── cli.py
├── tests/                  # 51 testes — regressão de bugs reais, fixtures, fumaça de API
├── data/                   # gitignored
│   ├── bronze/silver/gold/
│   └── manifest.json       # proveniência: url, sha256, timestamp, linhas
├── docs/
│   ├── spike-fontes.md     # bloqueios, correções de endpoint, bugs encontrados
│   ├── concurso-cgu.md     # regras do Concurso de Reúso de Dados Abertos da CGU
│   └── relatorio-tecnico.md # relatório técnico completo
└── .streamlit/config.toml
```

## Lições da implementação

Vale ler `docs/spike-fontes.md` na íntegra, mas os pontos que mais mudariam uma reimplementação:

- **Nunca confie em documentação de API sem testar contra dado real.** Três endpoints do plano original estavam errados (IBGE malhas, Compras.gov.br, PNCP `/v1/contratos`) e só apareceram testando.
- **`pysus.sinan(..., as_dataframe=True)` materializa o Brasil inteiro em memória.** Matou o processo duas vezes pelo OOM killer numa máquina de 7,5 GB (RSS 6,4 GB, confirmado em `dmesg`) — sem traceback, parecendo travamento. Correção: pedir paths (sem `as_dataframe`) e filtrar com DuckDB antes de tocar pandas.
- **Código de município do DATASUS é 6 dígitos sem dígito verificador**, não um código de 7 dígitos truncado. Reconstrução ingênua (`lpad`, `lstrip`) corrompe ou descarta dado silenciosamente — a mesma classe de bug apareceu duas vezes (uma na ingestão de população do IBGE, outra no SINAN) antes de eu centralizar a lógica correta em `io.municipios.resolve_por_codigo`.
- **`drop_duplicates()` é perigoso em dado de notificação.** Colapsar por (código, data, classificação) subcontou dengue em ~66% num teste — várias pessoas notificadas no mesmo dia com a mesma classificação é o normal, não duplicata.
- **PNCP é operacionalmente instável**: mesma consulta respondeu timeout completo, HTTP 204 sem corpo, e 200 normal em tentativas sucessivas. A ingestão pagina com try/except por página, preservando progresso parcial em vez de perder um bloco inteiro por causa de uma página ruim.

## Autoria

Desenhado e implementado com Claude (Anthropic).

---

**Licença**: dados públicos das fontes federais (IBGE, DATASUS, PNCP). Análise e visualização (IEAS, painel) são obra derivada sob domínio público.
