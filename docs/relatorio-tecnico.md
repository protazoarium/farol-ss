# Farol da Saúde & Saneamento — Relatório Técnico

**Índice de Efetividade da Alocação Sanitária (IEAS) para os 185 municípios de Pernambuco**

Versão 1.0 · 29 de agosto de 2026 · Concebido e implementado com Claude (Anthropic)

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
e uma **API aberta** em JSON/CSV. Três das oito fontes financeiras e de
saneamento previstas estão bloqueadas na origem (HTTP 403, ausência de API,
falha de DNS), o que mantém os dois eixos do IEAS abaixo da cobertura mínima
configurada — por isso o índice, hoje, **não é calculado para nenhum
município** e o mapa é integralmente cinza. Este comportamento é a *regra do
cinza* operando como projetada: o sistema recusa-se a publicar um número
derivado de dado majoritariamente ausente. As camadas que já têm dado real
(epidemiologia via SINAN, contratação de insumos via PNCP) são navegáveis no
painel e servidas pela API.

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
| PNCP — Portal Nacional de Contratações Públicas | eixo A · camada L3 (compras municipais) | ✅ ingerido (parcial) |
| Compras.gov.br / SIASG | eixo A · L3 federal (complemento) | ⏳ endpoint validado, módulo não escrito |
| SIOPS | eixo A · camada L2 (execução própria municipal) | 🔴 sem API REST |
| SNIS | eixo N · subíndice de saneamento | 🔴 sistema encerrado em 2023 (sucessor: SINISA); `app4.mdr.gov.br` não resolve; o catálogo do `dadosabertos.cidades.gov.br` só aponta para o domínio morto |
| Portal da Transparência (CGU) | eixo A · camada L1 (repasse federal) | 🔴 HTTP 403 mesmo com chave ativa |
| CadÚnico | eixo N · subíndice de vulnerabilidade | ⏳ não iniciado |

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
  200 normal em tentativas sucessivas).

### 3.3 Camada silver

- `silver_epidemiologia.py`: consolida os ~30 arquivos `sinan_<agravo>_<ano>`
  num formato longo `(cod_ibge, ano, agravo, casos, casos_confirmados)`.
- `silver_pncp.py`: consolida os arquivos `pncp_<modalidade>_<ano>` numa tabela
  única `(cod_ibge, ano, modalidade, objeto_compra, valor_total_homologado,
  ...)`.

### 3.4 Camada gold

`gold_municipio_ano.montar()` parte da grade completa 185 × 5 e aplica um
`LEFT JOIN` por fonte:

1. **População** (IBGE) → `populacao`, `populacao_fonte`.
2. **Epidemiologia** (SINAN) → `casos_<agravo>` (6 colunas) e
   `taxa_<agravo>` = casos / população × 100 000. Município sem notificação
   recebe **0 casos** (dado real), não `NULL`.
3. **Financeiro L3** (PNCP) → `l3_total` = soma do valor homologado (ou
   estimado, quando o homologado está ausente) por município-ano, **deflacionado
   para 2024** pela média anual do IPCA; `l3_per_capita` = `l3_total` /
   população. As camadas L1 e L2 entram como `NULL` (fontes bloqueadas).

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
| Saneamento (déficit = 1 − cobertura) | 0,35 | SNIS | 🔴 |
| Vulnerabilidade (extrema pobreza, pop. rural, densidade domiciliar) | 0,25 | CadÚnico + IBGE | ⏳ |

O subíndice epidemiológico é, ele próprio, uma combinação ponderada:
**arboviroses 53%** (dengue + chikungunya + zika) + **veiculação hídrica 47%**
(leptospirose + hepatite A + esquistossomose). O peso originalmente previsto
para internações hospitalares (SIH) foi redistribuído proporcionalmente: nenhum
grupo utilizável do SIH nesta versão do PySUS traz simultaneamente município de
residência e diagnóstico principal.

**Eixo A — Alocação** (R$ per capita deflacionado, pesos somam 1,0):

| Camada | Peso | Fonte | Estado |
|---|---|---|---|
| L1 — repasse federal | 0,35 | Portal da Transparência | 🔴 |
| L2 — execução própria municipal | 0,40 | SIOPS | 🔴 |
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

Hoje: Necessidade tem 1 de 3 subíndices (33%) e Alocação tem 1 de 3 camadas
(33%). **Os dois eixos ficam abaixo do limiar, então todos os 925
município-anos saem cinza.** Assim que Transparência (L1), SIOPS (L2) e SNIS
(saneamento) forem ingeridos, a cobertura sobe para 67% em cada eixo e as
cores aparecem automaticamente, sem alteração de código.

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

`GET /docs` expõe o Swagger. Valores `NaN` (o caso de hoje, com o farol cinza)
são serializados como `null` JSON válido — coberto por teste
(`tests/test_api.py`).

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
| Gold | linhas em `fato_municipio_ano` | 925 (185 × 5) |
| | município-anos com L3 | 336 |

O PNCP tem **crescimento acentuado de cobertura ano a ano** (6 municípios em
2021 → 157 em 2024), reflexo da adesão progressiva à Lei 14.133/2021 — o que
torna a série mais confiável nos anos recentes e é uma limitação explícita para
análise retrospectiva.

### 9.2 IEAS

| Métrica | Valor |
|---|---|
| Município-anos com IEAS calculado | **0 de 925** |
| Farol | 925 cinza |
| Cobertura do eixo Necessidade | 0,33 (uniforme) — só subíndice epidemiológico |
| Cobertura do eixo Alocação | 0,33 onde há L3, 0,00 no restante |

O subíndice epidemiológico (calculável) tem média 0,50 e vai de 0,23 a 0,78.
Os municípios de maior carga epidemiológica relativa em 2024 concentram-se no
Agreste e na Zona da Mata (Lagoa do Ouro, Moreno, Garanhuns, Limoeiro, Rio
Formoso) — visível no mapa da página Farol quando a camada "Necessidade" é
selecionada.

### 9.3 Alertas

**585 alertas** no total: **581 de suspeita de desabastecimento** (152 municípios
distintos, concentrados nos anos de surto de arbovirose) e **4 de suspeita de
sobrepreço** (itens de dipirona e amoxicilina+clavulanato a 4,7–6,1× a mediana
de PE da categoria).

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

1. **O IEAS não é calculável hoje.** Três fontes bloqueadas na origem mantêm os
   dois eixos abaixo da cobertura mínima. O que se entrega é o *pipeline* que
   produz o índice, validado com fixtures sintéticas nas quatro cores, mais as
   camadas de dado real que já existem.
2. **Cobertura desigual do PNCP no tempo.** A camada L3 é rala em 2021 e densa
   em 2024. Comparações entre anos devem considerar isso.
3. **Casamento compra × insumo por palavra-chave.** O detector 4 casa o objeto
   da licitação com a descrição da categoria (`seeds/catmat_saude.csv`) por
   termos, não por classificação CATMAT estruturada nem NLP. Gera
   falso-positivo quando o insumo foi comprado sob descrição atípica. O alerta
   é uma **suspeita para auditoria**, não uma conclusão.
4. **Rank percentil dentro de PE** mede posição relativa, não suficiência
   absoluta. Um estado inteiro subfinanciado teria municípios "azuis".
5. **População intercensitária interpolada** (2022–2023) introduz erro pequeno
   nos denominadores desses anos.
6. **SIH ausente** empobrece o subíndice epidemiológico, que fica só com
   notificações (SINAN), sem internações.

---

## 11. Reprodutibilidade

```bash
uv sync --extra dev --extra sus       # ambiente
cp .env.example .env                  # chave da Transparência, quando houver
make spike                            # sonda as fontes, reporta cobertura real
make ingest                           # baixa IBGE + SINAN + PNCP
make silver gold ieas                 # camadas derivadas + índice + alertas
uv run pytest -q                      # 55 testes
make app                              # painel  (localhost:8501)
make api                              # API     (localhost:8000/docs)
```

- **Determinismo**: a ingestão é idempotente; `data/manifest.json` registra
  SHA-256 e contagem de linhas de cada arquivo bruto.
- **Configuração versionada**: todo parâmetro do índice em `conf/ieas.yml`.
- **Testes**: 55 no total — garantias de grão do gold, regressão dos três bugs
  de corrupção silenciosa, comportamento do IEAS nas quatro cores com fixtures
  sintéticas, os detectores 3 e 4 com fixtures, fumaça da API.
- **Tamanho**: ~3.300 linhas de Python em `src/`, ~700 em `tests/`.

---

## 12. Conformidade com o Concurso de Reúso de Dados Abertos da CGU

- **Requisito de fonte** (≥ 1 conjunto catalogado no `dados.gov.br`): atendido
  com quatro — IBGE, SINAN, PNCP e o próprio Portal da Transparência da CGU.
- **Múltiplas fontes**: o produto cruza epidemiologia (SINAN), contratações
  (PNCP) e demografia (IBGE) num grão único.
- **Transparência / controle social**: proveniência rastreável
  (`manifest.json`), alertas com explicação em linguagem natural, API aberta
  sem autenticação.
- **Acessibilidade**: paleta validada para daltonismo, tabela alternativa a
  cada mapa, contraste verificado.
- **Formato**: painel + API, categorias explicitamente aceitas pelo edital.

Regras completas e cronograma em `docs/concurso-cgu.md`.

---

## 13. Trabalhos futuros

Reconhecimento das fontes bloqueadas feito em 29/08/2026 (com chave e conexão
reais) refinou os caminhos:

1. **Portal da Transparência — L1 parcial já é possível.** A chave gratuita
   **funciona** para vários endpoints por município (`bolsa-familia-por-municipio`,
   `auxilio-emergencial-por-municipio`, `convenios` com `codigoIbge` → HTTP 200).
   Só `/transferencias` retorna 403 — exige nível de acesso gov.br elevado. Dá
   para montar um L1 parcial (transferências sociais + convênios) com o que
   responde.
2. **SIOPS (L2)** — a série histórica de indicadores municipais é distribuída
   por TabNet/CSV; o site responde, mas o link direto de extração precisa ser
   garimpado. É a fonte de Alocação que, sozinha, leva o eixo A a 67% e destrava
   as cores do farol.
3. **SNIS (saneamento)** — *não há mirror funcional.* O sistema foi encerrado em
   2023 (sucessor SINISA, ainda sem série histórica municipal) e o domínio da
   série histórica não resolve. As rotas realistas são **Base dos Dados**
   (`basedosdados.org`, exige BigQuery) ou substituir o subíndice pelos dados de
   **abastecimento de água / esgoto / lixo do Censo 2022 do IBGE** (mesma família
   de fonte já ingerida, catalogada no `dados.gov.br`).
4. **CadÚnico** — subíndice de vulnerabilidade via SAGI/MDS; os endpoints
   antigos deram 404 (o SAGI migrou), a URL atual precisa ser localizada.
5. **Detector 3 (sobrepreço)** — *implementado.* O preço por item vem de
   `/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens` do PNCP (o recurso de consulta
   genérico só traz o valor total); resta refinar a normalização por unidade de
   medida (ampola × frasco) e rodar a coleta completa de itens.
6. **Deploy do painel** — os arquivos estão prontos no repositório
   (`requirements.txt` só com a base leve, `.gitignore` versionando os ~1,7 MB
   de Parquet que o painel lê, `docs/deploy.md` com o passo a passo). Falta o
   push para o GitHub e o "New app" no Streamlit Community Cloud, que dependem
   das contas do autor.

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
