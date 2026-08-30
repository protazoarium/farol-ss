# Farol da Saúde & Saneamento — Relatório Técnico

**Índice de Efetividade da Alocação Sanitária (IEAS) para os 185 municípios de Pernambuco**

Versão 1.1 · 30 de agosto de 2026 · Concebido e implementado com Claude (Anthropic)

---

## Resumo

O Farol-SS é um monitor territorial que cruza **execução financeira em saúde**
com **carga epidemiológica**, **déficit sanitário** e **vulnerabilidade social**
para os 185 municípios de Pernambuco, no período 2020–2024. O produto analítico
central é o **IEAS — Índice de Efetividade da Alocação Sanitária**, um índice de
*alinhamento territorial* entre o quanto um município precisa e o quanto ele
recebe/gasta, expresso num semáforo de quatro cores mais um estado "sem dado".

Esta versão entrega o **pipeline de dados completo e reprodutível**
(ingestão → silver → gold → índice → alertas), um **painel web** de seis páginas
e uma **API aberta** em JSON/CSV. Cinco fontes federais alimentam o índice hoje:
SINAN (epidemiologia), CadÚnico/SAGI (vulnerabilidade), PNCP (contratação de
insumos, L3), SIOPS (execução própria municipal, L2) e IBGE (população, IPCA,
malha). Com isso o eixo Necessidade fica **completo em 2 de 3 subíndices** e o
eixo Alocação em **2 de 3 camadas** — ambos acima do limiar de cobertura —, e o
**IEAS é calculado para 335 dos 925 município-anos** (156 dos 185 municípios em
2024). Onde falta a camada L3 do PNCP no ano, a Alocação cai abaixo do limiar e
o farol fica cinza: a *regra do cinza* recusa-se a publicar um número derivado
de dado majoritariamente ausente.

A única fonte ainda bloqueada é o **Portal da Transparência** (repasse federal
L1, HTTP 403 no endpoint `/transferencias`); o SNIS foi encerrado em 2023 e o
subíndice de saneamento aguarda substituição pelo Censo 2022 do IBGE.

Palavras-chave: dados abertos, saúde pública, contratações públicas, PNCP,
SINAN, índice territorial, arquitetura *lakehouse*, DuckDB.

---

## 1. Motivação e objetivo

Gasto público em saúde e necessidade epidemiológica não são distribuídos da
mesma forma no território. Um município pode concentrar surtos de arbovirose e
doenças de veiculação hídrica e, ao mesmo tempo, receber e executar menos
recurso por habitante do que a média do estado. Esse **descompasso** é
invisível nos portais de transparência, que publicam repasse e execução, mas
não os confrontam com desfecho de saúde.

O objetivo do Farol-SS é tornar esse descompasso **mensurável, comparável entre
municípios e explicável para um cidadão** — não para produzir um *ranking* de
gestão, mas para apontar onde a alocação de recurso está desalinhada da
necessidade sanitária, que é uma pergunta de controle social legítima.

**Recorte**: Pernambuco (UF 26), 185 municípios, 2020–2024, valores monetários
deflacionados para 2024.

---

## 2. Fontes de dados

Todas as fontes são federais e abertas. O catálogo canônico, com URL, licença e
link para o conjunto no Portal Brasileiro de Dados Abertos (`dados.gov.br`),
vive em `conf/sources.yml` e alimenta tanto a ingestão quanto a página de
Metodologia do painel e o endpoint `/fontes` da API.

| Fonte | Papel no IEAS | Estado nesta versão |
|---|---|---|
| IBGE — Localidades | dimensão dos 185 municípios | ✅ ingerido |
| IBGE — Estimativas de População | denominador de toda taxa por 100 mil hab. | ✅ ingerido |
| IBGE — IPCA (agregado 1737) | deflator para 2024 | ✅ ingerido |
| IBGE — Malhas Territoriais | geometria municipal (mapa) | ✅ ingerido |
| DATASUS/SINAN (via PySUS) | eixo N · subíndice epidemiológico | ✅ ingerido |
| CadÚnico — MI Social / SAGI-MDS | eixo N · subíndice de vulnerabilidade | ✅ ingerido (índice Solr, 185/185, 2020–2024) |
| PNCP — Portal Nacional de Contratações Públicas | eixo A · camada L3 (compras municipais) | ✅ ingerido (172/185; itens com preço unitário para ~880 contratos de saúde) |
| SIOPS | eixo A · camada L2 (execução própria municipal) | ✅ ingerido (TabNet legado por POST; 184/185, 2020–2024) |
| Compras.gov.br / SIASG | eixo A · L3 federal (complemento) | ⏳ endpoint validado, módulo não escrito |
| SNIS | eixo N · subíndice de saneamento | 🔴 sistema encerrado em 2023 (sucessor: SINISA); domínio da série histórica não resolve. Substituir pelo Censo 2022 do IBGE |
| Portal da Transparência (CGU) | eixo A · camada L1 (repasse federal) | 🔴 endpoint `/transferencias` retorna HTTP 403 (exige nível de acesso gov.br elevado) |

### 2.1 Sondagem de fontes (*spike*)

Antes de escrever qualquer módulo de ingestão, cada fonte foi sondada com uma
requisição real (`make spike`, resultado completo em `docs/spike-fontes.md`).
**11 de 12 fontes responderam.** A sondagem revelou que **três endpoints do
plano original estavam errados** e só apareceram contra dado real:

1. **IBGE malhas** — não existe o sufixo `/municipios`; a chamada correta é
   `/malhas/estados/26?intrarregiao=municipio&qualidade=intermediaria`.
2. **Compras.gov.br** — o parâmetro `statusUasg` é obrigatório (sem ele a API
   devolve 404) e o filtro de UF chama-se `siglaUf`, não `uf`.
3. **PNCP** — o recurso `/v1/contratos` do plano não expõe o município da
   contratação; o recurso útil é `/v1/contratacoes/publicacao`, cujo campo
   `unidadeOrgao.codigoIbge` geolocaliza a compra.

A lição, registrada e reincidente, é: **documentação de API não substitui um
teste contra dado real**.

---

## 3. Arquitetura do pipeline

O sistema segue o padrão *medallion* (bronze → silver → gold), **sem servidor
de banco de dados**: o DuckDB lê Parquet direto do disco, e cada camada é um
diretório de arquivos versionáveis.

```
Fontes federais
      │  ingest/*.py  ─ requisição real, retomável por página, com checksum
      ▼
data/bronze/        dados brutos + data/manifest.json (url, sha256, linhas, timestamp)
      │  transform/silver_*.py  ─ tipagem, cod_ibge de 7 dígitos, grão por fonte
      ▼
data/silver/        epidemiologia.parquet (3.111)  ·  pncp.parquet (6.150)  ·  ibge_*.parquet
      │  transform/gold_municipio_ano.py  ─ LEFT JOIN sobre grade 185 × 5 anos
      ▼
data/gold/fato_municipio_ano.parquet   grão único (cod_ibge, ano) — 925 linhas
      │  index/ieas.py            index/anomalies.py
      ▼                                  ▼
data/gold/ieas.parquet            data/gold/alertas.parquet
      │
      ▼
painel Streamlit  ·  API FastAPI  (leem só o gold, nunca recalculam)
```

### 3.1 Princípios de projeto

- **Grão canônico único**: `(cod_ibge, ano)`. Toda tabela do gold tem exatamente
  uma linha por município-ano, e a grade é *completa* — os 185 municípios ×
  5 anos existem mesmo quando a fonte não tem dado, com as colunas em `NULL`.
  É isso que torna a *ausência* visível em vez de silenciosamente omitida.
- **Município resolvido por código, nunca por nome**. SINAN, SIOPS e SNIS
  divergem na grafia ("Lagoa de Itaenga" vs "Lagoa do Itaenga", travessão vs
  hífen). Toda resolução passa por `io/municipios.resolve_por_codigo`, que
  converte códigos de 6 dígitos (DATASUS) para 7 e devolve `NA` para o que não
  é de PE.
- **Nenhum número mágico no código**. Pesos, limiares, ano-base de deflação e
  recorte temporal vivem em `conf/ieas.yml`. O código carrega e aplica.
- **Proveniência obrigatória**. Cada arquivo em `bronze/` gera uma entrada em
  `data/manifest.json` com URL, SHA-256, contagem de linhas e *timestamp* de
  coleta.
- **A camada de apresentação não calcula**. Painel e API leem o gold. Se um
  número está errado na tela, está errado no Parquet, e o conserto é no
  pipeline.

### 3.2 Camada de ingestão

- **IBGE** (`ingest/ibge.py`): APIs REST de localidades, agregados (população
  6579, IPCA 1737) e malhas. População dos anos censitários intermediários
  (2022, 2023) é interpolada linearmente e marcada como tal no manifesto.
- **SINAN** (`ingest/sinan.py`): via PySUS 2.10.3. A biblioteca baixa o arquivo
  do Brasil inteiro por agravo-ano; o módulo pede **os caminhos dos Parquet**
  (sem `as_dataframe`), filtra Pernambuco por `ID_MN_RESI` **com DuckDB** e só
  então materializa em pandas. Incidência é atribuída ao **município de
  residência**, não de notificação (ver §6.3).
- **PNCP** (`ingest/pncp.py`): paginação do recurso
  `/v1/contratacoes/publicacao` por (modalidade, ano). Cada página é gravada
  com `try/except` individual, preservando progresso parcial — o PNCP responde
  de forma instável (a mesma consulta retorna *timeout*, HTTP 204 sem corpo e
  200 normal em tentativas sucessivas). `ingest/pncp_itens.py` complementa com o
  recurso de item (`/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens`), que traz o
  preço unitário — matéria-prima do detector 3.
- **SIOPS** (`ingest/siops.py`): o SIOPS não tem API REST. A série histórica de
  indicadores municipais vive no TabNet legado (`siops-asp.datasus.gov.br`), um
  CGI que responde a um POST de formulário. Dois detalhes destravaram a coleta:
  o CGI é **ISO-8859-1** (mandar UTF-8 devolve "Tabela de conversao nao
  encontrada"), e com um único arquivo-ano a `Coluna` do TabNet tem de ser
  `--Não-Ativa--`. Indicador: `D.R.Próprios_em_Saúde/Hab` — despesa com recursos
  próprios do município em saúde, por habitante (a definição operacional da
  camada L2).
- **CadÚnico** (`ingest/cadunico.py`): a Matriz de Informações Sociais do
  SAGI/MDS é um índice Solr em `aplicacoes.mds.gov.br/sagi/servicos/misocial`.
  Não é documentada como API, mas aceita consultas Solr padrão. Campos usados
  (competência de dezembro de cada ano): famílias em extrema pobreza no
  CadÚnico e total de famílias cadastradas.

### 3.3 Camada silver

- `silver_epidemiologia.py`: consolida os ~30 arquivos `sinan_<agravo>_<ano>`
  num formato longo `(cod_ibge, ano, agravo, casos, casos_confirmados)`.
- `silver_pncp.py`: consolida os arquivos `pncp_<modalidade>_<ano>` numa tabela
  única `(cod_ibge, ano, modalidade, objeto_compra, valor_total_homologado, …)`.
- `silver/siops.parquet` e `silver/cadunico.parquet` já saem no grão
  `(cod_ibge, ano)` direto da ingestão.

### 3.4 Camada gold

`gold_municipio_ano.montar()` parte da grade completa 185 × 5 e aplica um
`LEFT JOIN` por fonte:

1. **População** (IBGE) → `populacao`, `populacao_fonte`.
2. **Epidemiologia** (SINAN) → `casos_<agravo>` (6 colunas) e
   `taxa_<agravo>` = casos / população × 100 000. Município sem notificação
   recebe **0 casos** (dado real), não `NULL`.
3. **Alocação L3** (PNCP) e **L2** (SIOPS) → `l3_per_capita` e `l2_per_capita`,
   ambos **deflacionados para 2024** pela média anual do IPCA. A camada L1
   (Portal da Transparência) entra como `NULL`.
4. **Vulnerabilidade** (CadÚnico) → `extrema_pobreza_por_mil_hab` = famílias em
   extrema pobreza / população × 1000.

O resultado, `fato_municipio_ano.parquet`, tem **925 linhas, zero código órfão,
zero par (município, ano) duplicado** — garantido por teste
(`tests/test_gold.py`).

---

## 4. Metodologia do IEAS

### 4.1 Dois eixos, cada um um rank percentil

O IEAS compara dois eixos, cada um normalizado como **rank percentil ∈ [0, 1]
entre os 185 municípios**. O valor absoluto (R$, taxa por 100 mil) não entra na
conta final — apenas a **posição relativa** dentro do estado. Isso torna o
índice robusto a inflação, a mudança de escala das fontes e a *outliers*.

**Eixo N — Necessidade** (pesos em `conf/ieas.yml`, somam 1,0):

| Subíndice | Peso | Fonte | Estado |
|---|---|---|---|
| Epidemiológico | 0,40 | SINAN | ✅ |
| Saneamento (déficit = 1 − cobertura) | 0,35 | SNIS | 🔴 (substituir por Censo 2022 IBGE) |
| Vulnerabilidade (taxa de famílias em extrema pobreza) | 0,25 | CadÚnico/SAGI | ✅ |

O subíndice epidemiológico é, ele próprio, uma combinação ponderada:
**arboviroses 53%** (dengue + chikungunya + zika) + **veiculação hídrica 47%**
(leptospirose + hepatite A + esquistossomose). O peso originalmente previsto
para internações hospitalares (SIH) foi redistribuído proporcionalmente: nenhum
grupo utilizável do SIH nesta versão do PySUS traz simultaneamente município de
residência e diagnóstico principal.

**Eixo A — Alocação** (R$ per capita deflacionado, pesos somam 1,0):

| Camada | Peso | Fonte | Estado |
|---|---|---|---|
| L1 — repasse federal | 0,35 | Portal da Transparência | 🔴 HTTP 403 |
| L2 — execução própria municipal | 0,40 | SIOPS | ✅ |
| L3 — contratação de insumos | 0,25 | PNCP + Compras.gov.br | ✅ (PNCP) |

### 4.2 Do eixo ao farol

- **gap = rank(A) − rank(N)** ∈ [−1, 1]
- **ieas = 1 − |gap|** ∈ [0, 1] — usado **apenas para ranquear**, nunca para
  colorir. Um *gap* muito positivo e um muito negativo têm o mesmo `|gap|`, mas
  significam coisas opostas; por isso o farol usa o `gap` **com sinal**.

| Faixa de gap | Farol | Leitura |
|---|---|---|
| gap ≤ −0,33 | 🔴 vermelho | necessidade muito acima da alocação |
| −0,33 < gap ≤ −0,10 | 🟠 amarelo | subalocação leve |
| \|gap\| ≤ 0,10 | 🟢 verde | alinhado |
| gap ≥ 0,33 | 🔵 azul | alocação acima da necessidade |

### 4.3 A regra do cinza

Um eixo cuja **fração de componentes presentes** cai abaixo do limiar
(`conf/ieas.yml`: Necessidade 60%, Alocação 50%) **não tem IEAS calculado** —
o `gap` vira `NaN` e o farol fica cinza. O sistema nunca publica um número
derivado de dado majoritariamente ausente.

Hoje: Necessidade tem **2 de 3** subíndices (epidemiológico + vulnerabilidade,
67%) e Alocação tem **2 de 3** camadas (L2 + L3, 67% — mas só onde há PNCP no
ano). Os dois eixos passam o limiar para **335 dos 925 município-anos** (156 dos
185 municípios em 2024). Os 590 município-anos cinza são, na maioria, os que não
têm contratação publicada no PNCP naquele ano — a cobertura da camada L3 sobe de
6 municípios em 2021 para 157 em 2024, então 2020–2021 saem quase inteiros cinza.
Ingerir a camada L1 (Portal da Transparência) fecharia o eixo Alocação em 3 de 3
e reduziria bastante o cinza.

---

## 5. Correção metodológica sobre a proposta original

A proposta inicial assumia ser possível ver "compras de medicamentos por
município" no Compras.gov.br. **Esse portal registra compras de órgãos
federais** (identificados por UASG), **não de prefeituras**. Manter a premissa
produziria um eixo financeiro que mede a presença de órgãos federais no
território, não a alocação municipal.

O eixo de Alocação foi então **decomposto em três camadas genuinamente
municipalizáveis**:

| Camada | Fonte | Campo que geolocaliza no município |
|---|---|---|
| L1 — repasse federal | Portal da Transparência | `codigoIbge` da transferência |
| L2 — execução própria | SIOPS | município declarante |
| L3 — contratação de insumos | **PNCP** (municipal) + Compras.gov.br (federal, escopo limitado) | `unidadeOrgao.codigoIbge` |

O **PNCP** — onde as prefeituras publicam suas contratações sob a Lei
14.133/2021 — é a fonte validada com dado real que viabiliza a análise por
município. O Compras.gov.br entra como complemento de escopo federal,
**documentado como limitação, não escondido**.

---

## 6. Bugs de corrupção silenciosa encontrados

Três classes de bug que **não quebram o processo** — produzem resultado
plausível, porém errado — só apareceram no teste contra dado real e são hoje
cobertas por teste de regressão.

### 6.1 Manipulação de string para reconstruir código

`.lstrip("260")` foi usado para normalizar códigos IBGE. `str.lstrip()` remove
**um conjunto de caracteres**, não um prefixo: `"2602001"` (Bodocó) virava
`"1"` após remoção de todos os `2`, `6` e `0` iniciais. **22 de 185 municípios**
mapeados para o código errado, silenciosamente. Correção: indexação explícita
(`codigo[:6]`) e validação imediata contra o conjunto de códigos de PE.

### 6.2 Materialização de dataset grande sem filtro

`pysus.sinan(..., as_dataframe=True)` carrega o Brasil inteiro (~1,6 M linhas)
em memória pandas **antes de qualquer filtro**. Numa máquina de 7,5 GB, o
processo foi morto pelo *OOM killer* (RSS 6,4 GB, confirmado em `dmesg`), sem
*traceback*, parecendo travamento. Correção: pedir os caminhos dos Parquet e
filtrar com DuckDB antes de tocar pandas.

### 6.3 Deduplicação que perde semântica de domínio

`drop_duplicates(subset=[cod_ibge, data, classificacao])` sobre notificações
de agravo **subcontou dengue em ~66%** (12.630 em vez de 36.761 num teste).
Várias pessoas notificadas no mesmo dia com a mesma classificação é o **normal
epidemiológico**, não erro de digitação. Correção: agregação com
`groupby().sum()` que preserva cardinalidade, e teste contra número oficial.

### 6.4 Município de residência vs. de notificação

A incidência é atribuída ao **município de residência** (`ID_MN_RESI`), não ao
de notificação (`ID_MUNICIP`). A diferença é material: 171/185 municípios
cobertos por residência contra 149/185 por notificação. Notificação reflete
onde fica o serviço de saúde, não onde vive a população em risco — usá-la
inflaria os municípios-polo e esvaziaria os pequenos, **invertendo justamente o
sinal que o IEAS existe para detectar**.

---

## 7. Detectores de anomalia

Do plano de quatro detectores, **três estão ativos**. Cada alerta traz uma
`explicacao` em linguagem natural: um alerta que um cidadão não consegue ler
não serve para auditoria.

### 7.1 Detector 1 — desalinhamento estrutural

Deriva direto do `gap`: todo farol vermelho é, por definição, um alerta de
necessidade não atendida. Depende do IEAS ter cor, portanto **não produz linhas
nesta versão** (tudo cinza).

### 7.2 Detector 3 — suspeita de sobrepreço

Preço unitário de um item de insumo acima de **Q3 + fator·IQR** da distribuição
da mesma categoria em PE (`fator` em `conf/ieas.yml`). Comparar só dentro da
categoria — via a coluna `palavras_chave` curada de `seeds/catmat_saude.csv` —
evita o falso-positivo de confrontar o preço de uma seringa com o de um
tomógrafo.

O preço por item **não** vem do recurso de consulta genérico do PNCP (esse só
traz o valor total da compra); vem de
`/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens`. `ingest/pncp_itens.py` percorre
esse recurso para as ~800 contratações de saúde (modalidades Pregão, Dispensa e
Inexigibilidade; Concorrência é obra, sem preço unitário comparável), de forma
retomável. Só entram itens `Material` sem orçamento sigiloso.

### 7.3 Detector 4 — suspeita de desabastecimento

O detector mais original do projeto. Liga **incidência sustentada de um agravo**
(SINAN, taxa no percentil 75+ de PE num ano) à **ausência de contratação da
categoria de insumo correspondente** no PNCP, via o mapa
`seeds/agravo_insumo.yml` (dengue → larvicida, inseticida, teste NS1, soro;
leptospirose → antibiótico penicilina, kit sorológico; etc.).

Uma salvaguarda importante: o detector **só considera município-ano que aparece
no PNCP naquele ano**. Um município em surto que não publicou nenhuma
contratação é *lacuna de dado* (o PNCP ainda não é universal), não *falha de
política* — flagá-lo transformaria a cobertura incompleta do portal em alarme
falso.

O detector 2 (resíduo de regressão robusta) fica de fora: exige o eixo de
Alocação completo (L1+L2+L3), e L1/L2 seguem bloqueados.

---

## 8. Camada de apresentação

### 8.1 Painel Streamlit (`make app`)

Seis páginas, todas lendo o gold via `farol_ss.app.dados` (cacheado):

| Página | Conteúdo |
|---|---|
| **Home** | o que o IEAS mede, estado real das fontes, por que o farol está cinza |
| **Farol** | mapa coroplético dos 185 municípios; seletor de camada (Farol / Necessidade / L3); filtro por mesorregião; legenda; tabela + CSV |
| **Município** | *drill-down*: componentes presentes/ausentes de cada eixo, série de notificações por agravo, incidência por 100 mil, contratações no PNCP, alertas |
| **Alertas** | tabela filtrável de anomalias com explicação em linguagem natural; distribuição por ano; CSV |
| **Metodologia** | fórmula do IEAS lida de `conf/ieas.yml`, regra do cinza, tabela de proveniência lida de `manifest.json` com link para o `dados.gov.br` |
| **API** | documentação das rotas e *download* direto do gold |

**Acessibilidade.** A paleta do semáforo
(`#c62828` vermelho, `#ef6c00` amarelo, `#00897b` verde, `#1565c0` azul, mais
`#9e9e9e` para "sem dado") foi validada com o script `validate_palette.js`
(*six-checks* para daltonismo, modo claro, superfície `#fcfcfb`): os quatro
tons cromáticos passam o piso de separação para protanopia/deuteranopia
(ΔE ≥ 8 em OKLab) e o piso de visão normal (ΔE ≥ 15). A cor **nunca aparece
sozinha** — todo mapa vem acompanhado de legenda rotulada, *tooltip* com o nome
da categoria e uma tabela alternativa.

### 8.2 API aberta FastAPI (`make api`)

Sem autenticação, JSON por padrão, `?formato=csv` em qualquer rota. Serve o
gold, não recalcula.

| Rota | Descrição |
|---|---|
| `GET /municipios` | os 185 municípios com meso/microrregião |
| `GET /municipios/{cod_ibge}` | série completa de um município |
| `GET /ieas?ano=&farol=` | IEAS por município-ano, filtrável |
| `GET /alertas?tipo=&ano=` | alertas explicáveis |
| `GET /fontes` | catálogo + proveniência |

`GET /docs` expõe o Swagger. Valores `NaN` (o farol cinza, a camada L1) são
serializados como `null` JSON válido — coberto por teste (`tests/test_api.py`).

---

## 9. Resultados

### 9.1 Volume ingerido

| Camada | Métrica | Valor |
|---|---|---|
| SINAN | notificações 2020–2024 em PE (por residência) | **271.505** |
| | dengue / chikungunya / zika | 144.269 / 103.592 / 16.436 |
| | leptospirose / hepatite A / esquistossomose | 3.880 / 2.492 / 836 |
| | cobertura municipal | 185/185 (grade completa; 171 com ao menos uma notificação) |
| PNCP | contratos municipais 2021–2024 | **6.150** |
| | municípios cobertos | 172/185 |
| | valor homologado total (nominal) | **R$ 3,28 bilhões** |
| | por modalidade | Dispensa 2.646 · Pregão eletrônico 1.610 · Concorrência 1.140 · Inexigibilidade 751 |
| PNCP itens | itens com preço unitário (contratações de saúde) | **4.691** de 878 contratações |
| SIOPS | município-anos de execução própria em saúde (R$/hab) | **920** (184/185 municípios × 5 anos) |
| CadÚnico/SAGI | município-anos de extrema pobreza | **925** (185/185 × 5 anos) |
| Gold | linhas em `fato_municipio_ano` | 925 (185 × 5) |
| | município-anos com L3 | 336 |

O PNCP tem **crescimento acentuado de cobertura ano a ano** (6 municípios em
2021 → 157 em 2024), reflexo da adesão progressiva à Lei 14.133/2021 — o que
torna a série mais confiável nos anos recentes e é uma limitação explícita para
análise retrospectiva.

### 9.2 IEAS

| Métrica | Valor |
|---|---|
| Município-anos com IEAS calculado | **335 de 925** |
| Farol (todos os anos) | 130 verde · 92 vermelho · 62 azul · 51 amarelo · 590 cinza |
| Farol em 2024 | 68 verde · 41 azul · 26 amarelo · 21 vermelho · 29 cinza |
| Cobertura do eixo Necessidade | 0,67 (uniforme) — epidemiológico + vulnerabilidade |
| Cobertura do eixo Alocação | 0,67 onde há L2 + L3; 0,33 onde só L2 |

Distribuição do farol por ano (só município-anos com IEAS calculado):

| Ano | 🔴 verm. | 🟠 amar. | 🟢 verde | 🔵 azul | cinza |
|---|---|---|---|---|---|
| 2020 | — | — | — | — | 185 |
| 2021 | 3 | 1 | 2 | 0 | 179 |
| 2022 | 50 | 16 | 32 | 4 | 83 |
| 2023 | 18 | 8 | 28 | 17 | 114 |
| 2024 | 21 | 26 | 68 | 41 | 29 |

Os municípios **vermelhos** em 2024 — necessidade no topo do estado, alocação no
fundo — concentram-se na Zona da Mata Norte e no Agreste: Aliança (necessidade
percentil 93, alocação 16), Paudalho (74 / 6), Bonito (88 / 21), Moreno (79 /
13), Catende (91 / 25). É exatamente o descompasso que o IEAS existe para
detectar. O subíndice epidemiológico tem média 0,50 (faixa 0,23–0,78); o de
vulnerabilidade, taxa de extrema pobreza mediana de ~190 famílias por mil
habitantes (faixa 6–608).

### 9.3 Alertas

**677 alertas** no total:

- **581 de suspeita de desabastecimento** — 152 municípios, concentrados nos
  anos de surto de arbovirose (2022 e 2024).
- **92 de desalinhamento estrutural** — os faróis vermelhos, agora que o índice
  tem cor (o detector 1 não produzia nada na versão anterior).
- **4 de suspeita de sobrepreço** — itens de dipirona e amoxicilina+clavulanato
  a 4,7–6,1× a mediana de PE da categoria.

| Ano | Desabastecimento |
|---|---|
| 2021 | 20 |
| 2022 | 203 |
| 2023 | 121 |
| 2024 | 237 |

Exemplo de explicação gerada: *"Incidência de Dengue no percentil 75%+ de PE em
2024, mas nenhuma contratação de larvicida, inseticida_adulticida,
teste_rapido_ns1_igm, soro_fisiologico encontrada no PNCP para o município no
período."*

---

## 10. Limitações e ameaças à validade

1. **O eixo Alocação ainda tem só 2 de 3 camadas.** Falta L1 (repasse federal,
   Portal da Transparência). O `gap` de hoje compara necessidade contra L2+L3;
   quando L1 entrar, o ranking de alocação muda para alguns municípios.
2. **O subíndice de saneamento está ausente** (SNIS encerrado). O eixo
   Necessidade combina epidemiologia e vulnerabilidade, mas não déficit
   sanitário — que é justamente o elo mais forte com as doenças de veiculação
   hídrica. Substituto planejado: Censo 2022 do IBGE.
3. **Cobertura desigual do PNCP no tempo.** A camada L3 é rala em 2020–2021
   (2020 sai inteiro cinza) e densa em 2024. Comparações entre anos devem
   considerar isso.
4. **Casamento compra × insumo por palavra-chave.** Os detectores 3 e 4 casam
   texto de licitação com categorias de `seeds/catmat_saude.csv` por termos
   curados, não por classificação CATMAT estruturada nem NLP. São **suspeitas
   para auditoria**, não conclusões.
5. **Detector 3 não normaliza por unidade de medida.** Compara preços unitários
   de "ampola" com "frasco" dentro da mesma categoria — a explicação mostra a
   unidade para o auditor julgar, mas o corte por IQR ainda mistura unidades.
6. **Rank percentil dentro de PE** mede posição relativa, não suficiência
   absoluta. Um estado inteiro subfinanciado teria municípios "azuis".
7. **CadÚnico**: a taxa de extrema pobreza usa a competência de dezembro de cada
   ano; a base do CadÚnico tem defasagem de atualização cadastral que varia
   entre municípios.
8. **SIH ausente** empobrece o subíndice epidemiológico (só notificações SINAN,
   sem internações).

---

## 11. Reprodutibilidade

```bash
make install                          # uv sync --all-extras
cp .env.example .env                  # chave da Transparência, quando houver
make spike                            # sonda as fontes, reporta cobertura real
make ingest                           # IBGE + SINAN + PNCP + SIOPS + CadÚnico
farol ingest-itens                    # itens do PNCP (preço unitário; retomável)
make silver gold ieas                 # camadas derivadas + índice + alertas
uv run pytest -q                      # 59 testes
make app                              # painel  (localhost:8501)
make api                              # API     (localhost:8000/docs)
```

- **Determinismo**: a ingestão é idempotente; `data/manifest.json` registra
  SHA-256 e contagem de linhas de cada arquivo bruto.
- **Configuração versionada**: todo parâmetro do índice em `conf/ieas.yml`.
- **Testes**: 59 no total — grão do gold (incluindo o join L2/vulnerabilidade),
  regressão dos três bugs de corrupção silenciosa, IEAS nas quatro cores e os
  detectores 3 e 4 com fixtures, parsers de SIOPS e CadÚnico, fumaça da API.
- **Tamanho**: ~3.700 linhas de Python em `src/`, ~800 em `tests/`.

---

## 12. Conformidade com o Concurso de Reúso de Dados Abertos da CGU

- **Requisito de fonte** (≥ 1 conjunto catalogado no `dados.gov.br`): atendido
  com seis — IBGE, SINAN, PNCP, SIOPS, CadÚnico e o Portal da Transparência.
- **Múltiplas fontes**: o produto cruza epidemiologia (SINAN), vulnerabilidade
  (CadÚnico), execução orçamentária (SIOPS), contratações (PNCP) e demografia
  (IBGE) num grão único.
- **Transparência / controle social**: proveniência rastreável
  (`manifest.json`), alertas com explicação em linguagem natural, API aberta
  sem autenticação.
- **Acessibilidade**: paleta validada para daltonismo, tabela alternativa a
  cada mapa, contraste verificado.
- **Formato**: painel + API, categorias explicitamente aceitas pelo edital.

Regras completas e cronograma em `docs/concurso-cgu.md`.

---

## 13. Trabalhos futuros

Entre a v1.0 e a v1.1, três fontes que constavam como bloqueadas foram
destravadas — SIOPS (L2), CadÚnico (vulnerabilidade) e o recurso de item do
PNCP (detector 3) —, o que deu cor ao farol. O que resta:

1. **Portal da Transparência — L1.** O endpoint `/transferencias` exige nível de
   acesso gov.br elevado (HTTP 403). A chave gratuita já **funciona** para
   `bolsa-familia-por-municipio`, `auxilio-emergencial-por-municipio` e
   `convenios` (todos com `codigoIbge` → HTTP 200); dá para montar um L1 parcial
   com esses e fechar o eixo Alocação em 3 de 3 camadas.
2. **Saneamento (substituto do SNIS).** O SNIS foi encerrado em 2023 (sucessor
   SINISA, sem série histórica municipal) e o domínio da série histórica não
   resolve. Substituir o subíndice pelos dados de **abastecimento de água /
   esgoto / lixo do Censo 2022 do IBGE** — mesma família de fonte já ingerida,
   catalogada no `dados.gov.br` —, o que fecha o eixo Necessidade em 3 de 3.
3. **Detector 3 — normalização por unidade.** Comparar preço unitário só entre
   itens da mesma unidade de medida (ou converter mg/ml → dose), e rodar
   `farol ingest-itens` completo (hoje ~880 de ~1.400 contratos de saúde).
4. **Detector 2 (resíduo de regressão)** passa a ser viável quando L1 entrar e o
   eixo Alocação ficar completo.
5. **Deploy do painel** — arquivos prontos no repositório; o push já foi feito
   para <https://github.com/protazoarium/farol-ss>. Falta o "New app" no
   Streamlit Community Cloud (conta do autor).

---

## Referências de dados

| Conjunto | dados.gov.br |
|---|---|
| PNCP | `dados.gov.br/dados/conjuntos-dados/portal-nacional-de-contratacoes-publicas-pncp` |
| SINAN | `dados.gov.br/dados/conjuntos-dados/sistema-de-informacao-de-agravos-de-notificacao-sinan` |
| IBGE — Estimativas de População | `dados.gov.br/dados/conjuntos-dados/estimativas-de-populacao` |
| Portal da Transparência | `dados.gov.br/dados/conjuntos-dados/portal-da-transparencia-do-governo-federal` |

Licença: dados públicos das fontes federais (IBGE, DATASUS, PNCP, CGU). A
análise e a visualização (IEAS, painel, API) são obra derivada sob domínio
público.
