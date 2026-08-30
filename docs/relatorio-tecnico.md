# Farol da Saúde & Saneamento — Relatório Técnico

**Índice de Efetividade da Alocação Sanitária (IEAS) para os 185 municípios de Pernambuco**

Versão 1.4 · 30 de agosto de 2026

---

## Resumo

O Farol-SS é um monitor territorial que cruza **execução financeira em saúde**
com **carga epidemiológica**, **déficit sanitário** e **vulnerabilidade social**
para os 185 municípios de Pernambuco, no período 2020–2024. O produto analítico
central é o **IEAS — Índice de Efetividade da Alocação Sanitária**, um índice de
*alinhamento territorial* entre o quanto um município precisa e o quanto ele
recebe/gasta, expresso num semáforo de quatro cores mais um estado "sem dado".

Esta versão entrega o **pipeline de dados completo e reprodutível**
(ingestão → silver → gold → índice → alertas), um **painel web institucional**
e uma **API aberta** em JSON/CSV. Sete fontes federais alimentam o índice:
SINAN (epidemiologia), Censo 2022 do IBGE (saneamento), CadÚnico/SAGI
(vulnerabilidade), PNCP (contratação de insumos, L3), SIOPS (execução própria
municipal, L2), Portal da Transparência (repasse federal, L1 — proxy) e IBGE
(população, IPCA, malha). O eixo **Necessidade fica completo em 3 de 3
subíndices** para todos os 185 municípios; o eixo **Alocação** tem L1 completo
(185/185 × 5 anos) e L2/L3 para quase todos. O **IEAS é calculado para 921 dos
925 município-anos** (os 185 municípios em 2024; os 4 cinza restantes são o
Distrito Estadual de Fernando de Noronha, sem execução própria no SIOPS nem
contratações municipais no PNCP). Onde falta a camada L3 do PNCP no ano, a
Alocação pode cair abaixo do limiar e o farol fica cinza: a *regra do cinza*
recusa-se a publicar um número derivado de dado majoritariamente ausente.

Os quatro detectores de anomalia do plano estão ativos, incluindo o de
**resíduo de regressão** (alocação sistematicamente abaixo do que a necessidade
prevê, controlando pelo padrão do estado), viável agora que a Alocação tem as
três camadas.

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
| DATASUS/SINAN (via PySUS) | eixo N · subíndice epidemiológico (arboviroses + veiculação hídrica) | ✅ ingerido |
| DATASUS/SIH-SUS (grupo RD, via PySUS) | eixo N · subíndice epidemiológico (internações por doença relacionada a saneamento) | ✅ **ingerido (185/185 × 5 anos)** — o *spike* concluíra erradamente que o SIH não tinha grupo utilizável |
| IBGE — Censo 2022 (agregados 6803/6805/6892) | eixo N · subíndice de saneamento | ✅ ingerido (déficit de água/esgoto/lixo, 185/185; retrato de 2022 aplicado a todo o recorte — coluna `saneamento_ano_referencia`) |
| CadÚnico — MI Social / SAGI-MDS | eixo N · subíndice de vulnerabilidade | ✅ ingerido (índice Solr, 185/185, 2020–2024) |
| PNCP — Portal Nacional de Contratações Públicas | eixo A · camada L3 (compras municipais) | ✅ ingerido; itens com preço unitário para as contratações de saúde |
| Compras.gov.br | eixo A · camada L3 **federal** (complemento) | ✅ **ingerido**: só a esfera federal (`orgaoEntidadeEsferaId='F'`) em municípios de PE, somada ao L3 municipal; cobre 2021+ |
| SIOPS | eixo A · camada L2 (execução própria municipal) | ✅ ingerido (TabNet legado por POST; 184/185, 2020–2024) |
| Portal da Transparência (CGU) | eixo A · camada L1 (repasse federal) | ✅ ingerido (185/185 × 5 anos), **proxy**: `/transferencias` (repasse fundo a fundo ao ente) dá HTTP 403 mesmo com a chave gratuita — confirmado permanente; usa-se, no lugar, as transferências sociais (Bolsa Família/Novo BF + BPC) por município |
| SNIS | eixo N · subíndice de saneamento | 🔴 encerrado (2023) — substituído pelo Censo 2022 do IBGE (linha acima) |

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
3. **Alocação** — L2 (SIOPS), L3 (PNCP) e L1 (Transparência, proxy) →
   `l2_per_capita`, `l3_per_capita`, `l1_per_capita`, todos **deflacionados
   para 2024** pela média anual do IPCA (o L1 é o valor mensal de junho
   anualizado × 12).
4. **Vulnerabilidade** (CadÚnico) → `extrema_pobreza_por_mil_hab` = famílias em
   extrema pobreza / população × 1000.
5. **Saneamento** (Censo 2022) → `sub_saneamento_bruto` = déficit ponderado de
   água/esgoto/lixo (pesos de `conf/ieas.yml`), um retrato de 2022 aplicado a
   todo o recorte.

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
| Epidemiológico | 0,40 | SINAN + SIH | ✅ |
| Saneamento (déficit de água + esgoto + lixo) | 0,35 | Censo 2022 do IBGE | ✅ |
| Vulnerabilidade (taxa de famílias em extrema pobreza) | 0,25 | CadÚnico/SAGI | ✅ |

O subíndice epidemiológico é, ele próprio, uma combinação ponderada de três
componentes, cada um um rank percentil dentro de PE:
**arboviroses 40%** (dengue + chikungunya + zika, SINAN) +
**veiculação hídrica 35%** (leptospirose + hepatite A + esquistossomose, SINAN) +
**internações por doença relacionada a saneamento 25%** (SIH, grupo RD — o
clássico indicador DRSAI/ISA: diarreias, hepatite A, leptospirose,
esquistossomose, helmintíases, febres tifoides). O peso de internações havia
sido redistribuído na v1.2 por um erro do *spike* (ver §6.5); a chamada correta
é `pysus.sih("PE", ano, mes, group="RD")`, e o grupo RD traz `MUNIC_RES` e
`DIAG_PRINC` para os 185 municípios.

**Eixo A — Alocação** (R$ per capita deflacionado, pesos somam 1,0):

| Camada | Peso | Fonte | Estado |
|---|---|---|---|
| L1 — repasse federal | 0,35 | Portal da Transparência (proxy: transf. sociais) | ✅ 185/185 |
| L2 — execução própria municipal | 0,40 | SIOPS | ✅ |
| L3 — contratação de insumos | 0,25 | PNCP (municipal) + Compras.gov.br (federal) | ✅ |

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

Hoje a **Necessidade está completa (3 de 3 subíndices) para todos os 185
municípios** — o subíndice de saneamento entrou via Censo 2022. Com o **L1
completo (185/185 × 5 anos)**, a **Alocação** também alcança a cobertura mínima
em quase toda a grade: o IEAS é calculado para **921 dos 925 município-anos**
(os 185 municípios em 2024). Os 4 cinza restantes são o Distrito Estadual de
Fernando de Noronha (2020–2023), que não tem execução própria no SIOPS nem
contratações municipais no PNCP — só L1, abaixo do limiar de 50% do eixo. A
coluna `l3_maturidade_pncp_uf` ainda registra que a adesão à Lei 14.133 sobe de
6 municípios em 2021 para 157 em 2024, então um L3 igual a zero em 2020–2021
deve ser lido como possível lacuna de cobertura, não ausência real de compra.

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

### 6.5 Conclusão errada do *spike* sobre o SIH

O *spike* de fontes registrou que "nenhum código de grupo do SIH (`RD`, `RJ`,
`ER`) retorna dado utilizável — só o grupo padrão `SP`, que não tem
`MUNIC_RES` nem `DIAG_PRINC`", e o peso do subíndice de internações foi
redistribuído. Isso estava **errado**: o helper `pysus.sih` aceita um
parâmetro `group`, e `pysus.sih("PE", ano, mes, group="RD")` baixa o grupo
**RD (AIH Reduzida)** — ~2,7 MB por mês para PE, com `MUNIC_RES` (185/185
municípios), `DIAG_PRINC` (CID-10) e `ANO_CMPT`. O erro foi concluir a partir
do grupo default (`SP`) sem testar o parâmetro. A v1.3 destrava o SIH e
restaura o peso do componente de internações. Lição: um "não dá" sobre uma
biblioteca merece a mesma desconfiança que um "a doc diz que dá".

---

## 7. Detectores de anomalia

Os **quatro detectores** do plano estão ativos. Cada alerta traz uma
`explicacao` em linguagem natural: um alerta que um cidadão não consegue ler
não serve para auditoria.

### 7.1 Detector 1 — desalinhamento estrutural

Deriva direto do `gap`: todo farol vermelho é, por definição, um alerta de
necessidade não atendida. É um corte fixo (`gap ≤ −0,33`).

### 7.2 Detector 2 — alocação abaixo do esperado

Ao contrário do detector 1, **controla pela relação necessidade→alocação do
estado inteiro**: ajusta, por ano, uma reta `alocacao_rank ~ necessidade_rank`
e mede o resíduo de cada município, com escala robusta (1,4826·MAD, para que os
próprios *outliers* não inflem o corte). Sinaliza quem tem resíduo padronizado
≤ −2 **e** pelo menos 8 pontos percentuais abaixo do previsto — alocação
sistematicamente aquém, dado o padrão do estado. Só roda sobre município-anos
com o eixo de Alocação inteiro (L1+L2+L3), então hoje cobre os 76 município-anos
que têm as três camadas.

### 7.3 Detector 3 — suspeita de sobrepreço

Preço unitário de um item de insumo acima de **Q3 + fator·IQR** da distribuição
da **mesma categoria, mesma unidade de medida e mesma dose/concentração** em PE
(`fator` em `conf/ieas.yml`). O agrupamento tem duas camadas:

- **fina** — (categoria, unidade, dose): `_dose_norm` extrai `500mg`,
  `50mg/ml`, `0,9%` da descrição do item, então "amoxicilina cápsula 500 mg" só
  entra na mesma distribuição de outras "amoxicilina cápsula 500 mg", nunca da
  de 250 mg nem da suspensão 50 mg/ml. Vale quando o grupo fino tem ≥ 5 itens.
- **grossa** — (categoria, unidade): recebe o que não tem dose parseável ou
  cujo grupo fino é pequeno demais (o comportamento das versões anteriores).

A categoria vem da coluna `palavras_chave` curada de `seeds/catmat_saude.csv` —
**não** de classificação CATMAT estruturada: o PNCP não a expõe no item
(`itemCategoriaNome` vem `"Não se aplica"` em 100% dos itens coletados). O
preço por item vem de `/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens`
(`ingest/pncp_itens.py`, retomável), não do recurso de consulta genérico (que
só traz o valor total). Só entram itens `Material` sem orçamento sigiloso.

### 7.4 Detector 4 — suspeita de desabastecimento

O detector mais original do projeto. Liga **incidência sustentada de um agravo**
(SINAN, taxa no percentil 75+ de PE num ano) à **ausência de contratação da
categoria de insumo correspondente**, via o mapa `seeds/agravo_insumo.yml`
(dengue → larvicida, inseticida, teste NS1, soro; leptospirose → antibiótico
penicilina, kit sorológico; etc.).

O casamento "comprou o insumo?" olha **dois textos**: o `objeto_compra` da
contratação (nível de processo, genérico — "aquisição de medicamentos" não diz
nada) **e a `descricao` de cada item** (específica — "AMOXICILINA 500MG",
"LARVICIDA BACILLUS THURINGIENSIS"). Consultar o item é o que dá alguma
precisão à afirmação de ausência. Continua sendo casamento por palavra-chave
curada, não NLP — os alertas são **suspeitas para auditoria**, não conclusões.

Uma salvaguarda importante: o detector **só considera município-ano que aparece
no PNCP naquele ano**. Um município em surto que não publicou nenhuma
contratação é *lacuna de dado* (o PNCP ainda não é universal — ver a coluna
`l3_maturidade_pncp_uf`), não *falha de política* — flagá-lo transformaria a
cobertura incompleta do portal em alarme falso.

---

## 8. Camada de apresentação

### 8.1 Painel Streamlit (`make app` · <https://farol-ss.streamlit.app>)

Identidade institucional própria (`app/tema.py`: cabeçalho, rodapé, cartões e
CSS compartilhados; azul `#1257a8`, o mesmo deste relatório). Home mais seis
páginas, todas lendo o gold via `farol_ss.app.dados` (cacheado); o texto
longo e o catálogo curado de fontes vivem em `app/conteudo.py`.

| Página | Conteúdo |
|---|---|
| **Home** | o que o índice mede e para quem, como se lê o IEAS, o semáforo com a leitura de cada cor, as oito fontes com selo de estado e data da última coleta |
| **Farol** | mapa coroplético dos 185 municípios; seletor de camada (Farol, cada subíndice de Necessidade, cada camada L1/L2/L3 de Alocação); filtro por mesorregião; legenda; ranking de extremos; tabela + CSV |
| **Município** | *drill-down*: valor de cada componente dos dois eixos, cobertura, séries de notificação (SINAN) e internação (SIH), incidência por 100 mil, gasto per capita por camada, contratações no PNCP, alertas |
| **Alertas** | tabela filtrável de anomalias com explicação em linguagem natural; distribuição por ano; a definição de cada um dos quatro detectores; CSV |
| **Fontes** | catálogo curado das oito fontes — papel no IEAS, cobertura real, limitações — cruzado com a proveniência de `manifest.json` |
| **Metodologia** | fórmula do IEAS lida de `conf/ieas.yml`, regra do cinza, decisões metodológicas que mudam o resultado, tabela de proveniência com link para o `dados.gov.br` |
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

> **Nota (v1.4).** A coleta do L1 (Portal da Transparência) foi concluída para
> os 185 municípios × 5 anos. Os números abaixo refletem esse *build*: o eixo
> Alocação passou a alcançar a cobertura mínima em quase toda a grade, o IEAS
> subiu de 470 para 921 município-anos com cor, e o detector 2 (resíduo de
> regressão) — que só roda onde L1+L2+L3 estão todos presentes — passou de 1
> para 4 alertas.

### 9.1 Volume ingerido

| Camada | Métrica | Valor |
|---|---|---|
| SINAN | notificações 2020–2024 em PE (por residência) | **271.505** |
| | dengue / chikungunya / zika | 144.269 / 103.592 / 16.436 |
| | leptospirose / hepatite A / esquistossomose | 3.880 / 2.492 / 836 |
| | cobertura municipal | 185/185 (grade completa; 171 com ao menos uma notificação) |
| SIH-SUS (grupo RD) | internações por doença relacionada a saneamento (DRSAI) 2020–2024 | **22.597** (4.334 → 5.990 ao ano; 185/185 municípios) |
| PNCP | contratos municipais 2021–2024 | **6.150** (172/185; adesão sobe de 6 municípios em 2021 a 157 em 2024) |
| PNCP itens | itens com preço unitário (878 contratações de saúde) | **4.691** |
| Compras.gov.br (L3 federal) | contratações de saúde da esfera federal em PE 2021–2024 | **858** (10 municípios; R$ 562 mi nominal) |
| SIOPS | município-anos de execução própria em saúde (R$/hab) | **920** (184/185 × 5 anos) |
| CadÚnico/SAGI | município-anos de taxa de extrema pobreza | **925** (185/185 × 5 anos) |
| IBGE Censo 2022 | municípios com déficit de água/esgoto/lixo | **185/185** (cobertura mediana: água 64%, esgoto 48%, lixo 74%) |
| Transparência (L1) | município-anos de transferências sociais federais | **925** (185/185 × 5 anos, coleta completa) |
| Gold | linhas em `fato_municipio_ano` | 925 (185 × 5), grão único, zero código órfão |

### 9.2 IEAS

| Métrica | Valor |
|---|---|
| Município-anos com IEAS calculado | **921 de 925** |
| Farol (todos os anos) | 383 verde · 202 vermelho · 176 azul · 160 amarelo · 4 cinza |
| Farol em 2024 | 104 verde · 60 azul · 19 amarelo · 2 vermelho · 0 cinza |
| Cobertura do eixo Necessidade | **1,00 para todos** — epidemiológico (SINAN+SIH) + saneamento + vulnerabilidade |
| Cobertura do eixo Alocação | 1,00 (L1+L2+L3) em 338 · 0,67 (L1+L2 ou L1+L3) em 583 · 0,33 (só L1) em 4 |

Distribuição do farol por ano (só município-anos com IEAS calculado; os 4 cinza
são Fernando de Noronha em 2020–2023):

| Ano | 🔴 verm. | 🟠 amar. | 🟢 verde | 🔵 azul | cinza |
|---|---|---|---|---|---|
| 2020 | 45 | 45 | 79 | 15 | 1 |
| 2021 | 56 | 48 | 71 | 9 | 1 |
| 2022 | 99 | 42 | 37 | 6 | 1 |
| 2023 | 0 | 6 | 92 | 86 | 1 |
| 2024 | 2 | 19 | 104 | 60 | 0 |

A leitura muda de ano para ano: 2020–2022 concentram os **vermelhos** (necessidade
no topo do estado, alocação no fundo), enquanto 2023–2024 pendem para verde e azul.
Parte dessa virada é real — repasse e execução crescem em termos deflacionados — e
parte reflete o **peso de L1 (0,35)**: as transferências sociais são um número
grande e relativamente uniforme, que empurra para cima o eixo Alocação dos
municípios mais pobres. Como L1 é um *proxy* (§10), essa sensibilidade é uma
ressalva de leitura, não um resultado sobre repasse setorial de saúde. As
coberturas censitárias de saneamento em PE são baixas (água 64%, esgoto 48%,
lixo 74% na mediana), o que mantém o subíndice de Necessidade alto em quase todo
o estado.

### 9.3 Alertas

**777 alertas** no total, dos quatro detectores:

- **570 de suspeita de desabastecimento** — 152 municípios, concentrados nos
  anos de surto de arbovirose (2022 e 2024). A consulta cruza incidência com o
  **objeto e os itens** das contratações. (Não depende de L1; inalterado.)
- **202 de desalinhamento estrutural** — os faróis vermelhos (106 municípios;
  47 de severidade alta, 155 moderada), concentrados em 2020–2022.
- **4 de alocação abaixo do esperado** (detector 2) — todos em 2024, o único ano
  com massa suficiente de município-anos com o eixo Alocação inteiro (L1+L2+L3)
  para um ajuste robusto. Ainda conservador por construção.
- **1 de suspeita de sobrepreço** — após separar a comparação por (categoria,
  unidade, dose), sobra um item de amoxicilina em comprimido a 4,2× a mediana
  de PE (Petrolina, 2023).

| Ano | Desabastecimento |
|---|---|
| 2021 | 20 |
| 2022 | 199 |
| 2023 | 115 |
| 2024 | 236 |

Exemplo de explicação gerada: *"Incidência de Dengue no percentil 75%+ de PE em
2024, mas nenhuma contratação de larvicida, inseticida_adulticida,
teste_rapido_ns1_igm, soro_fisiologico encontrada no PNCP (objeto e itens) para
o município no período."*

---

## 10. Limitações e ameaças à validade

1. **L1 (repasse federal) é um proxy.** O endpoint `/transferencias`
   (repasse fundo a fundo ao ente) responde **HTTP 403** mesmo com a chave
   gratuita — testadas as variantes `/transferencias` e
   `/transferencias/por-municipio`, é limitação permanente do nível de acesso.
   Usa-se, no lugar, a soma das transferências sociais federais por município
   (Bolsa Família/Novo Bolsa Família + BPC, competência junho) como
   aproximação da presença de recurso federal no território. A **cobertura é
   completa** (185/185 × 5 anos) — a chave é bloqueada por volume, mas
   `farol ingest-l1` retoma de onde parou (pausa de 1,5 s/chamada) e a coleta
   foi concluída. A limitação que resta é de **natureza**: transferência
   social não é repasse setorial de saúde, e seu peso (0,35) torna o eixo
   Alocação sensível a ela (§9.2).
2. **Saneamento é um retrato de 2022.** O Censo não é anual; o mesmo déficit é
   aplicado aos 5 anos do recorte (coluna `saneamento_ano_referencia = 2022`
   no gold e na API). O SNIS, que era anual, foi encerrado em 2023 e não tem
   substituto com série municipal.
3. **Cobertura desigual do PNCP no tempo.** A adesão à Lei 14.133 cresce ano a
   ano, e o *snapshot* atual tem modalidade-anos coletados parcialmente (a
   ingestão para na primeira página que o PNCP — instável — não responde). A
   coluna `l3_maturidade_pncp_uf` do gold é o indicador de confiança: fração
   dos 185 municípios de PE presentes no PNCP naquele ano, baixa em 2020–2021.
   Onde o L3 falta, a regra do cinza já retira o município-ano do índice. Uma
   re-ingestão completa do PNCP (paginação resiliente por modalidade-ano) é
   trabalho futuro; comparações entre anos devem considerar a maturidade.
4. **L3 federal (Compras.gov.br) cobre 2021+** e só a esfera federal em
   municípios de PE (poucas UASGs, concentradas em Recife/Petrolina). É um
   complemento pequeno, somado ao L3 municipal; não altera o grão nem os pesos.
5. **Casamento compra × insumo por palavra-chave curada.** Os detectores 3 e 4
   casam texto de licitação (objeto e item) com categorias de
   `seeds/catmat_saude.csv` por termos curados — o PNCP não expõe a
   classificação CATMAT estruturada do item. São **suspeitas para auditoria**,
   não conclusões.
6. **Detector 3 normaliza a dose, mas não converte apresentação.** "Comprimido
   500 mg" e "cápsula 500 mg" hoje são grupos distintos (unidade diferente);
   equivalências farmacêuticas não são resolvidas.
7. **Rank percentil dentro de PE** mede posição relativa, não suficiência
   absoluta. Um estado inteiro subfinanciado teria municípios "azuis".
8. **CadÚnico**: a taxa de extrema pobreza usa a competência de dezembro de cada
   ano; a base tem defasagem de atualização cadastral que varia entre
   municípios.
9. **SIH**: usa só o grupo RD (AIH Reduzida) e conta AIH, não pacientes
   distintos; a definição de DRSAI segue o grupo `veiculacao_hidrica` de
   `seeds/cid_saneamento.csv` (diarreias, hepatite A, leptospirose,
   esquistossomose, helmintíases, febres tifoides).

---

## 11. Reprodutibilidade

```bash
make install                          # uv sync --all-extras
cp .env.example .env                  # chave gratuita do Portal da Transparência
make spike                            # sonda as fontes, reporta cobertura real
make ingest                           # IBGE + SINAN + SIH + PNCP + Compras.gov.br + SIOPS + CadÚnico + L1
farol ingest-itens                    # itens do PNCP (preço unitário; retomável)
make silver gold ieas                 # camadas derivadas + índice + alertas
uv run pytest -q                      # 70 testes
make app                              # painel  (localhost:8501)
make api                              # API     (localhost:8000/docs)
```

Comandos de coleta retomável: `farol ingest-sih`, `farol ingest-l3-federal`,
`farol ingest-itens`, `farol ingest-l1`.

- **Determinismo**: a ingestão é idempotente; `data/manifest.json` registra
  SHA-256 e contagem de linhas de cada arquivo bruto.
- **Configuração versionada**: todo parâmetro do índice em `conf/ieas.yml`.
- **Testes**: 70 no total — grão do gold, os quatro detectores com fixtures,
  regressão dos três bugs de corrupção silenciosa, IEAS nas quatro cores,
  ingestão do SIH (casamento de CID DRSAI), normalização de dose do detector 3,
  detector 4 sobre a descrição dos itens, parsers de SIOPS e CadÚnico, fumaça
  da API.
- **Tamanho**: ~4.200 linhas de Python em `src/`, ~900 em `tests/`.

---

## 12. Conformidade com o Concurso de Reúso de Dados Abertos da CGU

- **Requisito de fonte** (≥ 1 conjunto catalogado no `dados.gov.br`): atendido
  com sobra — IBGE, SINAN, SIH, PNCP, SIOPS, CadÚnico e o Portal da
  Transparência da própria CGU.
- **Múltiplas fontes**: o produto cruza epidemiologia (SINAN + SIH),
  vulnerabilidade (CadÚnico), execução orçamentária (SIOPS), contratações
  (PNCP + Compras.gov.br) e demografia (IBGE) num grão único.
- **Transparência / controle social**: proveniência rastreável
  (`manifest.json`), alertas com explicação em linguagem natural, API aberta
  sem autenticação.
- **Acessibilidade**: paleta validada para daltonismo, tabela alternativa a
  cada mapa, contraste verificado.
- **Formato**: painel + API, categorias explicitamente aceitas pelo edital.

Regras completas e cronograma em `docs/concurso-cgu.md`.

---

## 13. Trabalhos futuros

Da v1.0 à v1.4, todas as fontes e detectores do plano foram destravados —
SIOPS (L2), CadÚnico (vulnerabilidade), Censo 2022 (saneamento), Portal da
Transparência (L1, proxy, 185/185), preço por item do PNCP, **SIH (internações
DRSAI)**, **Compras.gov.br (L3 federal)** — e o detector 3 passou a normalizar
dose e o detector 4 a consultar a descrição dos itens. O que resta:

1. **L1 fundo a fundo.** O proxy de transferências sociais é o teto do acesso
   gov.br gratuito; o repasse fundo a fundo ao ente (`/transferencias`) exige
   um nível de credenciamento que o projeto não tem. Um convênio de acesso com
   a CGU o destravaria.
2. **Equivalência farmacêutica no detector 3.** A dose já é normalizada;
   falta reconhecer que "comprimido 500 mg" e "cápsula 500 mg" são a mesma
   apresentação para fins de preço.
3. **SNIS histórico via Base dos Dados.** Substituiria o retrato censitário de
   2022 por uma série anual de saneamento; é uma integração nova (BigQuery) não
   validada.
4. **Deploy do painel** — arquivos prontos; o push já foi feito para
   <https://github.com/protazoarium/farol-ss>. Falta o "New app" no Streamlit
   Community Cloud (conta do autor).

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
