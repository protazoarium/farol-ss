# Spike de fontes — resultado (Etapa 2)

Sondagem executada em 2026-08-25 via `make spike`. Reproduzível a qualquer
momento. **11 de 12 fontes acessíveis.**

## Situação por fonte

| Fonte | Status | Cobertura em PE | Nota |
|---|---|---|---|
| IBGE localidades | OK | 185/185 | Base do seed `conf/municipios_pe.csv` |
| IBGE população | OK | 185/185 | Denominador de toda taxa por 100 mil |
| IBGE IPCA | OK | 60 meses | Deflator para 2020–2024 |
| IBGE malhas | OK | 185/185 | GeoJSON 218 KB; `codarea` = código de 7 dígitos |
| **PNCP** | OK | 35.909 contratos/mês (BR) | **Fonte central da camada L3** |
| Compras.gov.br | OK | 1222 UASGs | `codigoMunicipioIbge` geolocaliza a compra federal |
| SNIS (CKAN) | OK | — | Catálogo acessível; extração ainda por arquivo |
| dados.gov.br | OK | — | API exige chave; links fixos em `sources.yml` |
| SINAN (PySUS) | OK | **171/185** | Dengue 2023: 7.960 notificações em PE |
| Catálogo Saúde (PySUS) | OK | — | `sisagua`, `bnafar`, `arboviroses` existem — **não baixados** |
| **Portal da Transparência** | **BLOQUEADO** | — | **Exige chave gratuita (login gov.br)** |

## O que mudou em relação ao plano

**1. Endpoints corrigidos.** Três chamadas do plano estavam erradas e só o
spike revelou:
- IBGE malhas: não existe sufixo `/municipios`; usa-se
  `/malhas/estados/26?intrarregiao=municipio`.
- Compras.gov.br: `statusUasg` é **obrigatório** (sem ele a API devolve 404) e
  o parâmetro de UF chama-se `siglaUf`.
- `dados.gov.br` passou a exigir chave de API. Não é bloqueante: as fontes são
  baixadas dos portais de origem, e o catálogo serve só para citação.

**2. PySUS 2.10.3 tem API incompatível com a assumida.** `pysus.online_data`
não existe mais; o correto é `pysus.sinan(disease, year)` e
`pysus.sih(state, year, month)`. O cache precisa de `PYSUS_CACHEPATH` definido
**antes do import** — `set_cache()` chamado depois não reposiciona os downloads,
e os arquivos escapam para `~/pysus`.

**3. Incidência é por município de RESIDÊNCIA.** Usar `ID_MN_RESI`, não
`ID_MUNICIP` (notificação). A diferença é material: 171/185 municípios por
residência contra 149/185 por notificação. Notificação reflete onde fica o
serviço de saúde, não onde vive a população em risco — usá-la inflaria os
municípios-polo e esvaziaria os pequenos, invertendo justamente o sinal que o
IEAS existe para detectar.

**4. Volume é menor que o temido.** SINAN dengue Brasil/2023 são 1,6 M linhas
em 64 MB, baixadas em 18 s. O recorte de 5 anos cabe folgado nos 12 GB livres.

**5. Fontes novas descobertas no catálogo do PySUS:**
- `SISAGUA` — vigilância da qualidade da água. Reforça o eixo de saneamento com
  medida de desfecho, não só de cobertura declarada ao SNIS.
- `MACROSAUDE` — regiões e macrorregiões de saúde. Supre o recorte que o IBGE
  não fornece; hoje o seed usa mesorregião como aproximação.
- `ECONOMIASAUDE` — inclui SIOPS. Pode substituir o download manual da série
  histórica. Ambos exigem a classe `PySUS().get_saude()`, sem helper direto.

## Limitações confirmadas

- **Portal da Transparência exige chave.** É a única fonte da camada L1
  (repasses federais). Cadastro gratuito em
  `portaldatransparencia.gov.br/api-de-dados/cadastrar-email`, depois
  `PORTAL_TRANSPARENCIA_API_KEY` no `.env`.
- ~~**SIH sem grupo utilizável.**~~ **RESOLVIDO (v1.3).** A conclusão original
  estava errada: `pysus.sih("PE", ano, mes, group="RD")` baixa o grupo **RD
  (AIH Reduzida)**, que traz `MUNIC_RES` (185/185 municípios de PE),
  `DIAG_PRINC` (CID-10) e `ANO_CMPT`, em ~2,7 MB/mês. O erro anterior foi
  chamar o helper sem o parâmetro `group` e concluir a partir do grupo padrão
  `SP`. O subíndice de internações por doença relacionada a saneamento
  (DRSAI/ISA, peso 0,25 do eixo epidemiológico) voltou — ver `ingest/sih.py`.
- **BNAFAR devolve 0 recursos.** O dataset de estoque de medicamentos seria o
  upgrade natural do detector de desabastecimento — medir estoque em vez de
  inferir da ausência de compra. Está listado no catálogo mas vem vazio;
  reavaliar antes de contar com ele.
- **PNCP oscila.** Devolveu HTTP 503 numa execução e 200 na seguinte. É a
  justificativa concreta da estratégia de snapshot com cache: a demo não pode
  depender da disponibilidade do serviço no momento da apresentação.
- **Chamar um helper do PySUS sem argumentos baixa a base nacional inteira.**
  `pysus.sisagua()` trouxe **5,7 GB** de CSV durante o spike e levou o disco a
  98%. Não é uma listagem de recursos: é um download completo. A ingestão de
  SISAGUA, BNAFAR e afins precisa filtrar por UF e ano **antes** de materializar
  qualquer coisa, e `base.exigir_espaco()` passou a abortar com mensagem clara
  quando sobram menos de 3 GB. As sondas não invocam mais esses helpers.

- **Cobertura não é o mesmo que zero.** 171/185 municípios com notificação de
  dengue significa que 14 tiveram *zero casos*, não *dado ausente*. A regra do
  cinza precisa distinguir os dois, senão pune município saudável.

## Atualização — Etapa 3 (ingestão real)

Execução completa de IBGE, SINAN e PNCP contra a API real revelou mais três
problemas que só apareceram testando, não no spike original (que só validava
alcançabilidade, não o comportamento fim a fim):

- **`ID_MN_RESI` do SINAN é código DATASUS de 6 dígitos sem dígito
  verificador**, não um código IBGE truncado. Uma primeira tentativa de
  reconstrução com `lpad(...,7,'0')` produzia um código que não batia com
  nenhum município e descartava a UF inteira silenciosamente. A correção
  reaproveita `io.municipios.resolve_por_codigo`, já testada.
- **`pysus.sinan(..., as_dataframe=True)` materializa o Brasil inteiro em
  memória antes de qualquer filtro** — em uma máquina com 7,5 GB de RAM isso
  foi morto duas vezes pelo OOM killer (confirmado em `dmesg`, RSS de 6,4 GB),
  e o sintoma era indistinguível de um travamento (processo simplesmente
  desaparecia, sem traceback). A correção usa `pysus.sinan(...)` sem
  `as_dataframe`, que devolve caminhos de Parquet já em disco, e filtra com
  DuckDB antes de tocar pandas.
- **Endpoint do PNCP usado no spike não é o certo para filtrar por
  município.** `/v1/contratos` só filtra por CNPJ de órgão federal já
  conhecido. O endpoint que de fato viabiliza a camada L3 é
  `/v1/contratacoes/publicacao`, que aceita `uf` e devolve
  `unidadeOrgao.codigoIbge` — validado com dado real (Prefeitura de Paulista,
  Recife). `codigoModalidadeContratacao` é obrigatório e não vem como enum na
  spec; os 14 códigos usados são a tabela de domínio do manual do PNCP.
  Volume é alto (310 páginas só para "Dispensa" em 2024), então o escopo foi
  reduzido às 5 modalidades relevantes para saúde/saneamento (Concorrência,
  Pregão eletrônico/presencial, Dispensa, Inexigibilidade).
- **`app4.mdr.gov.br` (aplicativo de série histórica do SNIS) não resolve
  DNS.** Não é indisponibilidade momentânea do serviço — o domínio não
  resolve. `dadosabertos.cidades.gov.br` (CKAN) só aponta para esse mesmo
  link quebrado, sem arquivo de download direto. Alternativa a explorar em
  sessão futura: Base dos Dados (basedosdados.org), que redistribui SNIS
  tratado via BigQuery/Python/R — não implementado ainda, é uma integração
  nova não validada.
- **HEPA (Hepatite A) 2024 devolve vazio de forma consistente** — não é
  falha, é ano ainda não publicado pelo DATASUS para esse agravo especificamente
  (outros agravos têm 2024 completo).

~~Peso do subíndice de internações (SIH) redistribuído em `conf/ieas.yml`.~~
**Revertido na v1.3**: o SIH (grupo RD) foi destravado (ver acima), e os pesos
do eixo epidemiológico voltaram a arboviroses 0,40 / veiculação hídrica 0,35 /
internações-saneamento 0,25.

## SIOPS (L2) — tentativa adicional, ainda bloqueado

Investiguei duas rotas além da já documentada (TabNet legado):

1. **`siops-asp.datasus.gov.br` responde em HTTP puro** (a variante HTTPS
   não resolve/conecta), servindo uma interface CGI/TabWin antiga
   (`indicadores.HTM`) que normalmente exige POST com parâmetros específicos
   de sessão para gerar um `.csv`/`.def` — reverso de engenharia caro sem
   inspecionar o formulário num navegador real.
2. **`pysus.PySUS().get_saude()`** dá acesso ao catálogo `ECONOMIASAUDE`
   (que a documentação do PySUS lista como incluindo SIOPS), mas devolve uma
   corrotina não aguardada (`cr_await`, `cr_running` no `dir()`) — API
   assíncrona que os helpers de alto nível (`pysus.sinan`, `pysus.sih`) não
   expõem de forma síncrona. Integrar exigiria `asyncio` explícito e
   investigar a forma dos dados devolvidos, sem garantia de que o resultado
   seja o SIOPS municipal esperado.

Nenhuma das duas rotas foi implementada nesta sessão — fica como próximo
passo, não como bloqueio permanente. A camada L2 (execução própria em saúde)
do IEAS fica sem fonte até uma das duas ser resolvida.

## Atualização — v1.3 (fechamento das lacunas de fonte)

Sessão dedicada a resolver as oito lacunas listadas em `STATUS.md`. Resultado:

- **SIH destravado** (grupo RD). Ver acima. Novo `ingest/sih.py`, novo subíndice
  de internações DRSAI no eixo epidemiológico, peso do SIH restaurado em
  `conf/ieas.yml`.
- **L3 federal (Compras.gov.br) implementado.** Novo `ingest/compras_gov.py`.
  Endpoint `/modulo-contratacoes/1_consultarContratacoes_PNCP_14133` do
  `dadosabertos.compras.gov.br` (aberto, sem chave). Filtra
  `orgaoEntidadeEsferaId == "F"` (só esfera federal — a municipal é o próprio
  PNCP, já coletado) e `unidadeOrgaoCodigoIbge` em PE. Modalidades 3/5/6/7
  (Concorrência-E, Pregão-E, Dispensa, Inexigibilidade). Cobre 2021+. O valor
  federal é somado ao L3 municipal no gold, num único `l3_per_capita`.
- **`/transferencias` do Portal da Transparência: 403 confirmado como
  permanente** com a chave gratuita (testadas as variantes `/transferencias` e
  `/transferencias/por-municipio`). A camada L1 continua sendo um **proxy** —
  transferências sociais federais por município (Bolsa Família/Novo Bolsa
  Família + BPC), não repasse fundo a fundo ao SUS. Documentado em
  `conf/ieas.yml`, `ingest/transparencia.py` e no relatório §10.
- **Detector 3 passou a normalizar dose/concentração.** `_dose_norm` extrai
  `500mg`, `50mg/ml`, `0,9%` etc. da descrição do item; o agrupamento fino é
  (categoria, unidade, dose) e só cai no grosso (categoria, unidade) quando não
  há dose parseável ou o grupo fino é pequeno.
- **Detector 4 passou a consultar a descrição dos itens**, não só o
  `objeto_compra` da contratação. O `itemCategoriaNome` do PNCP foi verificado
  e vem `"Não se aplica"` em 100% dos itens — não há categoria CATMAT
  estruturada a usar; o casamento continua sendo por palavra-chave curada, e
  isso está dito explicitamente no código e no relatório.
- **Saneamento: `saneamento_ano_referencia = 2022`** agora é uma coluna do
  gold, para o painel e a API declararem que é um retrato censitário aplicado a
  todo o recorte (o SNIS anual foi encerrado e não tem substituto municipal).
- **Cobertura desigual do PNCP no tempo: `l3_maturidade_pncp_uf`** agora é uma
  coluna do gold (fração dos 185 municípios de PE com contratação no PNCP
  naquele ano) — baixa em 2020–2021, o que quantifica a ameaça à validade em
  vez de só descrevê-la.
