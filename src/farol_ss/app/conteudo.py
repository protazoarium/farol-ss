"""Texto longo, catálogo curado de fontes e catálogo de fórmulas do painel.

Separado de `tema.py` (que cuida do visual) e de `conf/sources.yml` / `conf/ieas.yml`
(os catálogos técnicos que alimentam a ingestão e o cálculo). Aqui vive a
redação institucional: o que cada fonte é, por que entra no IEAS, o que ela
cobre e o que ela **não** cobre; e a lista de fórmulas que a página
Metodologia apresenta. Os **valores dos parâmetros** (pesos, limiares) não
são escritos aqui — são lidos de `conf/ieas.yml` em runtime, para o texto
nunca divergir do cálculo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── O que é o índice, em três níveis de profundidade ───────────────────
O_QUE_E = """
Portais de transparência respondem "quanto foi gasto". Não respondem se esse
gasto **acompanha a necessidade** de cada lugar. O **Farol da Saúde &
Saneamento** existe para tornar esse descompasso mensurável: recurso público em
saúde e carga sanitária não se distribuem da mesma forma no território. Um
município pode concentrar surtos de arbovirose e de doenças de veiculação
hídrica e, ao mesmo tempo, receber e executar menos recurso por habitante do que
a média do estado — e nada nos painéis de despesa mostra isso.

Para os **185 municípios de Pernambuco**, no período **2020–2024**, o painel
cruza **oito fontes federais abertas** num grão único de município × ano e
produz o **IEAS — Índice de Efetividade da Alocação Sanitária**: um índice de
*alinhamento territorial* entre o quanto um município **precisa** e o quanto ele
**recebe e gasta**. O IEAS não avalia qualidade de gestão nem execução
orçamentária; mede posição relativa — onde cada município está no ranking
estadual de necessidade e no de alocação, e o quanto essas duas posições
divergem.
"""

PARA_QUEM = """
- **Controle social e imprensa** — um mapa e alertas em linguagem natural para
  fazer, com base em dado público, a pergunta "por que este município está no
  vermelho?".
- **Gestão pública** — enxergar onde a alocação está desalinhada da necessidade
  *antes* que o desfecho de saúde piore, e priorizar auditoria.
- **Pesquisa e ensino** — um recorte já tratado, com proveniência rastreável
  (`data/manifest.json`), pipeline reprodutível e API aberta em JSON/CSV.
"""

COMO_LER = """
O IEAS compara **dois eixos**, cada um convertido em **rank percentil ∈ [0, 1]
entre os 185 municípios** — o valor absoluto (R$, taxa por 100 mil habitantes)
não entra na conta final, só a **posição relativa** dentro do estado. Isso torna
o índice robusto à inflação, à mudança de escala das fontes e a *outliers*
(um município pequeno com um hospital regional não distorce a escala dos demais).

- **gap = rank(Alocação) − rank(Necessidade)** ∈ [−1, 1] → é o que **colore** o
  farol. Negativo: a alocação está atrás da necessidade (subalocação).
- **ieas = 1 − |gap|** ∈ [0, 1] → mede só o **alinhamento** e serve apenas para
  ordenar, nunca para colorir: um *gap* muito positivo e um muito negativo têm o
  mesmo `|gap|`, mas significados opostos.

**Regra do cinza:** um eixo cuja fração de componentes presentes cai abaixo do
limiar (`conf/ieas.yml`: Necessidade 60%, Alocação 50%) **não tem IEAS
calculado** — o município aparece cinza. O sistema nunca publica um número
derivado de dado majoritariamente ausente.
"""

CORRECAO_METODOLOGICA = """
A proposta original assumia ser possível ver "compras de medicamentos por
município" no Compras.gov.br. Esse portal registra, na maior parte, compras de
**órgãos federais** (por UASG), **não de prefeituras**. O eixo financeiro foi
então decomposto em três camadas genuinamente municipalizáveis — **L1**
(repasse federal, Portal da Transparência), **L2** (execução própria, SIOPS) e
**L3** (contratação de insumos, PNCP municipal + Compras.gov.br federal). O
PNCP, onde as prefeituras publicam sob a Lei 14.133/2021, é a fonte que
viabiliza a análise por município.
"""

# ── Catálogo curado de fontes ──────────────────────────────────────────
# chave = a mesma de conf/sources.yml e do manifest.json (para casar o resumo
# de coleta). `estado` ∈ {ok, partial, block}.


@dataclass
class Fonte:
    chave: str
    nome: str
    orgao: str
    eixo: str
    papel: str
    cobertura: str
    limitacao: str
    estado: str
    variavel_bruta: str = ""  # o que a fonte fornece (variável / endpoint)
    transformacao: str = ""  # a agregação/fórmula até a coluna do gold
    dados_gov: str = ""
    licenca: str = "Dados abertos"


FONTES: list[Fonte] = [
    Fonte(
        chave="sinan",
        nome="SINAN — Sistema de Informação de Agravos de Notificação",
        orgao="Ministério da Saúde / DATASUS (via PySUS)",
        eixo="Necessidade · epidemiológico",
        papel=(
            "Carga de doença sensível a saneamento: arboviroses (dengue, chikungunya, "
            "zika) e doenças de veiculação hídrica (leptospirose, hepatite A, "
            "esquistossomose). Incidência atribuída ao **município de residência** "
            "(`ID_MN_RESI`), não ao de notificação."
        ),
        cobertura=(
            "6 agravos × 5 anos · 271.505 notificações · 185/185 municípios (grade "
            "completa; 171 com ao menos uma notificação)."
        ),
        limitacao=(
            "Cobertura não é o mesmo que zero: um município sem notificação teve zero "
            "casos, não dado ausente. Hepatite A de 2024 ainda não foi publicada pelo "
            "DATASUS."
        ),
        estado="ok",
        variavel_bruta=(
            "Uma linha por notificação; lê-se `ID_MN_RESI`, `CLASSI_FIN`, `DT_NOTIFIC` "
            "do arquivo DBC de cada agravo/ano."
        ),
        transformacao=(
            "Filtra PE por código, reconstrói o `cod_ibge` de 7 dígitos, conta por "
            "(município, ano); a taxa por 100 mil habitantes é calculada no gold."
        ),
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/arboviroses-dengue",
        licenca="Dados abertos — Ministério da Saúde",
    ),
    Fonte(
        chave="sih",
        nome="SIH-SUS — Sistema de Informações Hospitalares (grupo RD)",
        orgao="Ministério da Saúde / DATASUS (via PySUS)",
        eixo="Necessidade · epidemiológico",
        papel=(
            "Internações por **doença relacionada a saneamento ambiental inadequado** "
            "(DRSAI / ISA): diarreias, hepatite A, leptospirose, esquistossomose, "
            "helmintíases, febres tifoides — desfecho grave, complementar à "
            "notificação. Usa a AIH Reduzida (grupo RD), que traz município de "
            "residência e diagnóstico principal."
        ),
        cobertura="22.597 internações DRSAI no recorte · 185/185 municípios × 5 anos.",
        limitacao=(
            "Conta AIH, não pacientes distintos. A lista de CID sensíveis a saneamento "
            "(`seeds/cid_saneamento.csv`, grupo `veiculacao_hidrica`) é uma escolha "
            "metodológica."
        ),
        estado="ok",
        variavel_bruta="Uma linha por AIH; lê-se `MUNIC_RES` e `DIAG_PRINC` (CID-10).",
        transformacao=(
            "Marca a AIH como DRSAI se o `DIAG_PRINC` casa a lista de CID; soma por "
            "(município, ano) → `internacoes_drsai`; taxa por 100 mil no gold."
        ),
        dados_gov=(
            "https://dados.gov.br/dados/conjuntos-dados/"
            "sistema-de-informacoes-hospitalares-do-sus-sihsus"
        ),
        licenca="Dados abertos — Ministério da Saúde",
    ),
    Fonte(
        chave="ibge_saneamento",
        nome="Censo Demográfico 2022 — saneamento domiciliar",
        orgao="IBGE (agregados 6803 / 6805 / 6892)",
        eixo="Necessidade · saneamento",
        papel=(
            "Déficit de infraestrutura: fração de domicílios **sem** abastecimento de "
            "água por rede, **sem** esgotamento adequado e **sem** coleta de lixo. "
            "Substitui o SNIS, encerrado em 2023."
        ),
        cobertura="185/185 municípios. Cobertura mediana em PE: água 64%, esgoto 48%, lixo 74%.",
        limitacao=(
            "É um **retrato de 2022** aplicado a todo o recorte — o Censo não é anual "
            "(coluna `saneamento_ano_referencia`). O saneamento muda devagar, mas a "
            "série temporal é aproximada."
        ),
        estado="ok",
        variavel_bruta=(
            "Domicílios com/sem cada serviço, por município (variável 381 dos três "
            "agregados do Censo 2022)."
        ),
        transformacao=(
            "déficit = 1 − cobertura, por serviço; `sub_saneamento_bruto` = média "
            "ponderada dos três déficits (pesos de `conf/ieas.yml`, aplicados aqui na "
            "ingestão)."
        ),
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/censo-demografico-2022",
        licenca="Dados abertos — IBGE",
    ),
    Fonte(
        chave="cadunico",
        nome="CadÚnico — Cadastro Único / Matriz de Informações Sociais",
        orgao="Ministério do Desenvolvimento e Assistência Social — SAGI",
        eixo="Necessidade · vulnerabilidade social",
        papel=(
            "Número de famílias em **extrema pobreza** inscritas no CadÚnico "
            "(competência de dezembro de cada ano), base do subíndice de "
            "vulnerabilidade."
        ),
        cobertura="185/185 municípios × 5 anos.",
        limitacao=(
            "A base do CadÚnico tem defasagem de atualização cadastral que varia entre "
            "municípios."
        ),
        estado="ok",
        variavel_bruta=(
            "`cadun_qtde_fam_sit_extrema_pobreza_s` (Solr da SAGI/MDS), competência "
            "dezembro."
        ),
        transformacao=(
            "`extrema_pobreza_por_mil_hab` = famílias em extrema pobreza / população "
            "(IBGE) × 1.000; o subíndice é o rank percentil desse valor."
        ),
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/familias-inscritas-no-cadastro-unico",
        licenca="Dados abertos — MDS",
    ),
    Fonte(
        chave="pncp",
        nome="PNCP — Portal Nacional de Contratações Públicas",
        orgao="Ministério da Gestão e da Inovação",
        eixo="Alocação · L3 (contratação de insumos, municipal)",
        papel=(
            "Contratações que as **prefeituras** publicam sob a Lei 14.133/2021, "
            "geolocalizadas por `unidadeOrgao.codigoIbge`. O recurso de itens traz o "
            "**preço unitário**, matéria-prima do detector de sobrepreço."
        ),
        cobertura=(
            "6.150 contratos + 4.691 itens com preço unitário · 172/185 municípios · "
            "2021–2024."
        ),
        limitacao=(
            "A adesão à Lei 14.133 cresce ano a ano (de 6 municípios em 2021 a 157 em "
            "2024) e o serviço é instável — a coluna `l3_maturidade_pncp_uf` mede a "
            "confiança do dado por ano."
        ),
        estado="ok",
        variavel_bruta=(
            "Uma linha por contratação (`valorTotalHomologado`, `objetoCompra`, "
            "modalidade); os itens vêm de um segundo endpoint por contrato."
        ),
        transformacao=(
            "Soma nominal por (município, ano), somada ao L3 federal, deflacionada "
            "para 2024 e dividida pela população → `l3_per_capita`."
        ),
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/pncp",
        licenca="Dados abertos — Ministério da Gestão",
    ),
    Fonte(
        chave="compras_gov",
        nome="Compras.gov.br — contratações federais",
        orgao="Ministério da Gestão e da Inovação",
        eixo="Alocação · L3 (contratação de insumos, federal)",
        papel=(
            "Complemento de escopo federal ao L3 municipal: contratações de saúde de "
            "**órgãos da esfera federal** (`orgaoEntidadeEsferaId = 'F'`) sediados em "
            "municípios de PE. Somadas ao L3 do PNCP num único valor per capita."
        ),
        cobertura="858 contratações federais de saúde · 10 municípios · 2021–2024.",
        limitacao=(
            "A esfera municipal deste portal é a mesma do PNCP e foi **excluída** para "
            "não duplicar. Poucos órgãos federais, concentrados nas cidades maiores."
        ),
        estado="ok",
        variavel_bruta=(
            "Uma linha por contratação federal (filtrada por esfera, UF e palavra-chave "
            "de saúde no objeto)."
        ),
        transformacao="Soma nominal por (município, ano), incorporada ao mesmo `l3_per_capita`.",
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/compras-publicas-do-governo-federal",
        licenca="Dados abertos — Ministério da Gestão",
    ),
    Fonte(
        chave="siops",
        nome="SIOPS — Sistema de Informações sobre Orçamentos Públicos em Saúde",
        orgao="Ministério da Saúde (TabNet)",
        eixo="Alocação · L2 (execução própria municipal)",
        papel=(
            "Despesa com **recursos próprios** do município em saúde, por habitante — "
            "a definição operacional da execução própria. Coletado do TabNet legado "
            "(POST de formulário, charset ISO-8859-1), pois não há API REST."
        ),
        cobertura="184/185 municípios × 5 anos.",
        limitacao=(
            "O TabNet legado é instável; a série é o indicador `D.R.Próprios em "
            "Saúde/Hab` declarado pelo próprio município."
        ),
        estado="ok",
        variavel_bruta="Indicador `D.R.Próprios_em_Saúde/Hab` (já per capita, R$ correntes).",
        transformacao="Deflacionado para 2024 pelo IPCA → `l2_per_capita` (não se divide por população).",
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/siops",
        licenca="Dados abertos — Ministério da Saúde",
    ),
    Fonte(
        chave="transparencia",
        nome="Portal da Transparência — transferências da União",
        orgao="Controladoria-Geral da União (CGU)",
        eixo="Alocação · L1 (repasse federal)",
        papel=(
            "**Proxy** do dinheiro federal que chega ao território: soma das "
            "transferências sociais por município (Bolsa Família / Novo Bolsa Família "
            "+ BPC, competência de junho anualizada)."
        ),
        cobertura="185/185 municípios × 5 anos (coleta completa).",
        limitacao=(
            "É um **proxy**: o endpoint de repasse fundo a fundo ao ente "
            "(`/transferencias`) responde **HTTP 403** com a chave gratuita — "
            "limitação permanente do nível de acesso. Usa-se, no lugar, a "
            "transferência social, que não é o repasse setorial de saúde."
        ),
        estado="ok",
        variavel_bruta="`valor` mensal (junho) de Bolsa Família / Novo BF e de BPC, por município.",
        transformacao=(
            "`l1_per_capita` = (transf. sociais de junho × 12 × deflator) / população."
        ),
        dados_gov=(
            "https://dados.gov.br/dados/conjuntos-dados/"
            "portal-da-transparencia-do-governo-federal"
        ),
        licenca="Dados abertos — CGU",
    ),
    Fonte(
        chave="ibge_populacao",
        nome="IBGE — Estimativas de População e IPCA",
        orgao="IBGE (agregados 6579 e 1737)",
        eixo="Base",
        papel=(
            "Denominador de toda taxa por 100 mil habitantes e deflator (IPCA) que "
            "leva todos os valores monetários a reais de 2024."
        ),
        cobertura=(
            "185/185 municípios; população de anos intercensitários interpolada "
            "linearmente e marcada como tal (`populacao_fonte`)."
        ),
        limitacao="—",
        estado="ok",
        variavel_bruta="População estimada (variável 9324) e número-índice mensal do IPCA (variável 2266).",
        transformacao=(
            "`deflator[ano]` = média anual do IPCA de 2024 ÷ média anual do ano; "
            "população 2022–2023 interpolada linearmente."
        ),
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/estimativas-de-populacao",
        licenca="Dados abertos — IBGE",
    ),
    Fonte(
        chave="ibge_malhas",
        nome="IBGE — Malhas Territoriais Municipais",
        orgao="IBGE",
        eixo="Base",
        papel="Geometria dos 185 municípios para o mapa coroplético.",
        cobertura="185/185 municípios.",
        limitacao="—",
        estado="ok",
        variavel_bruta="GeoJSON da malha estadual de PE, `codarea` = código IBGE de 7 dígitos.",
        transformacao="Geometria simplificada (tolerância 0,001°) e guardada em `data/bronze`.",
        dados_gov="https://dados.gov.br/dados/conjuntos-dados/malha-geometrica-dos-municipios-brasileiros",
        licenca="Dados abertos — IBGE",
    ),
]

PILL_LABEL = {"ok": "ingerido", "partial": "parcial", "block": "bloqueado"}
PILL_CLASS = {"ok": "fss-ok", "partial": "fss-partial", "block": "fss-block"}


# ── Catálogo de fórmulas (LaTeX) ──────────────────────────────────────
# Estrutura simbólica: a matemática é estável, os valores dos parâmetros
# (pesos, limiares) são mostrados pela página Metodologia a partir de
# `conf/ieas.yml`. `bloco` agrupa as fórmulas por seção da página.


@dataclass
class Formula:
    chave: str
    titulo: str
    latex: str
    glossa: str
    bloco: str = ""
    dependencias: list[str] = field(default_factory=list)


FORMULAS: list[Formula] = [
    # — métricas comuns —
    Formula(
        "taxa",
        "Taxa por 100 mil habitantes",
        r"\text{taxa}_{a,m,t} \;=\; \frac{\text{casos}_{a,m,t}}{\text{população}_{m,t}}\times 100\,000",
        "Normaliza a carga de doença pela população, para comparar municípios de "
        "portes diferentes. Vale para cada agravo do SINAN e para as internações "
        "DRSAI do SIH. Município sem notificação recebe zero casos — dado real, "
        "não ausência.",
        bloco="comuns",
    ),
    Formula(
        "deflator",
        "Deflator IPCA",
        r"\text{deflator}_t \;=\; \frac{\overline{\text{IPCA}}_{2024}}{\overline{\text{IPCA}}_{t}}"
        r"\qquad \text{valor}^{2024}_{m,t} = \text{valor}^{\text{nominal}}_{m,t}\times \text{deflator}_t",
        "Leva todo valor monetário (L1, L2, L3) ao poder de compra de 2024, "
        "usando a média anual do número-índice mensal do IPCA (agregado 1737 do "
        "IBGE). Sem isso, um real de 2020 e um de 2024 entrariam somados como se "
        "fossem a mesma coisa.",
        bloco="comuns",
    ),
    Formula(
        "rank_percentil",
        "Rank percentil",
        r"\text{rank}(x_m) \;=\; \frac{\#\{k : x_k \le x_m\}}{\#\{k : x_k \text{ não é NaN}\}} \;\in\; [0,1]",
        "A métrica comum dos dois eixos: converte qualquer indicador na posição "
        "relativa do município dentro de Pernambuco. Robusto a outliers e a "
        "mudança de escala — não assume distribuição normal, ao contrário do "
        "z-score. Série constante devolve 0,5 para todos; NaN permanece NaN.",
        bloco="comuns",
    ),
    Formula(
        "media_ponderada",
        "Média ponderada tolerante a ausência",
        r"\bar{v}_m \;=\; \frac{\sum_{i \,\in\, P_m} w_i\, v_{i,m}}{\sum_{i \,\in\, P_m} w_i}"
        r"\qquad P_m = \{\, i : v_{i,m}\ \text{presente}\,\}",
        "Quando falta um componente numa linha, o peso é redistribuído entre os "
        "presentes em vez de propagar NaN. É o que permite calcular a Alocação de "
        "um município que ainda não tem L1 coletado — desde que a cobertura "
        "mínima do eixo seja respeitada.",
        bloco="comuns",
    ),
    # — eixo Necessidade —
    Formula(
        "sub_epidemiologico",
        "Subíndice epidemiológico",
        r"\text{sub}^{\text{epi}}_m \;=\; w_{\text{arbo}}\,\text{rank}\!\Big(\textstyle\sum \text{taxa}_{\text{arbo}}\Big)"
        r" + w_{\text{híd}}\,\text{rank}\!\Big(\textstyle\sum \text{taxa}_{\text{híd}}\Big)"
        r" + w_{\text{DRSAI}}\,\text{rank}\big(\text{taxa}_{\text{DRSAI}}\big)",
        "Três componentes: arboviroses (dengue + chikungunya + zika), veiculação "
        "hídrica (leptospirose + hepatite A + esquistossomose) e internações "
        "DRSAI. As taxas são somadas **antes** do rank — assim um município com "
        "carga alta em vários agravos ocupa a posição que de fato lhe cabe, sem "
        "diluição.",
        bloco="necessidade",
        dependencias=["taxa", "rank_percentil"],
    ),
    Formula(
        "sub_saneamento",
        "Subíndice de saneamento",
        r"\text{déficit}^{s}_m = 1 - \text{cobertura}^{s}_m \qquad"
        r"\text{sub}^{\text{san}}_m = \text{rank}\!\Big(\textstyle\sum_{s} w_s\,\text{déficit}^{s}_m\Big)",
        "Para cada serviço s ∈ {água, esgoto, lixo}, o déficit é a fração de "
        "domicílios sem ele (Censo 2022). A média ponderada dos três déficits é "
        "montada na ingestão; o subíndice é o rank percentil desse valor. Déficit "
        "maior = necessidade maior.",
        bloco="necessidade",
        dependencias=["rank_percentil"],
    ),
    Formula(
        "sub_vulnerabilidade",
        "Subíndice de vulnerabilidade",
        r"\text{sub}^{\text{vuln}}_m \;=\; \text{rank}\!\left(\frac{\text{famílias em extrema pobreza}_m}{\text{população}_m}\times 1\,000\right)",
        "Um único componente: o rank percentil da taxa de famílias em extrema "
        "pobreza inscritas no CadÚnico. A fonte não expõe, no grão município-ano "
        "e na série 2020–2024, outras dimensões comparáveis (população rural, "
        "densidade domiciliar).",
        bloco="necessidade",
        dependencias=["rank_percentil"],
    ),
    Formula(
        "eixo_necessidade",
        "Eixo Necessidade",
        r"N_m = \text{rank}\big(\bar{v}^{\,N}_m\big),\quad"
        r"\bar{v}^{\,N}_m = w_{\text{epi}}\,\text{sub}^{\text{epi}}_m + w_{\text{san}}\,\text{sub}^{\text{san}}_m + w_{\text{vuln}}\,\text{sub}^{\text{vuln}}_m",
        "Média ponderada dos três subíndices (com a re-normalização por ausência), "
        "seguida de rank percentil. Se menos de 60% dos componentes estão "
        "presentes, N vira NaN — a regra do cinza.",
        bloco="necessidade",
        dependencias=["media_ponderada", "rank_percentil"],
    ),
    # — eixo Alocação —
    Formula(
        "per_capita",
        "Camadas de gasto per capita (deflacionadas)",
        r"L1_m = \dfrac{\text{transf. sociais}_m \times 12 \times \text{deflator}}{\text{população}_m},\quad"
        r"L2_m = \text{ind. SIOPS}_m \times \text{deflator},\quad"
        r"L3_m = \dfrac{\sum \text{contratos}_m \times \text{deflator}}{\text{população}_m}",
        "L1 é a transferência social de junho anualizada (proxy do repasse "
        "federal). L2 já vem per capita do SIOPS, só é deflacionado. L3 soma "
        "PNCP municipal + Compras.gov.br federal. Todos em reais de 2024.",
        bloco="alocacao",
        dependencias=["deflator"],
    ),
    Formula(
        "eixo_alocacao",
        "Eixo Alocação",
        r"A_m = \text{rank}\big(\bar{v}^{\,A}_m\big),\quad"
        r"\bar{v}^{\,A}_m = w_{L1}\,L1_m + w_{L2}\,L2_m + w_{L3}\,L3_m",
        "Média ponderada das três camadas per capita (re-normalizada por "
        "ausência), seguida de rank percentil. Se menos de 50% das camadas estão "
        "presentes, A vira NaN.",
        bloco="alocacao",
        dependencias=["media_ponderada", "rank_percentil", "per_capita"],
    ),
    # — do eixo ao farol —
    Formula(
        "gap_ieas",
        "Gap e IEAS",
        r"\text{gap}_m = A_m - N_m \;\in\; [-1,\,1] \qquad \text{ieas}_m = 1 - |\text{gap}_m| \;\in\; [0,\,1]",
        "O gap colore o farol: negativo = alocação atrás da necessidade. O IEAS "
        "mede só o alinhamento e serve apenas para ordenar — um gap muito "
        "positivo e um muito negativo têm o mesmo |gap|, mas significam coisas "
        "opostas.",
        bloco="farol",
        dependencias=["eixo_necessidade", "eixo_alocacao"],
    ),
    # — detectores —
    Formula(
        "d1",
        "Detector 1 — desalinhamento estrutural",
        r"\text{alerta}_m \iff \text{gap}_m \le \tau_{\text{vermelho}} \qquad"
        r"\text{severidade} = \begin{cases}\text{alta} & \text{gap}_m \le -0{,}6\\ \text{moderada} & \text{caso contrário}\end{cases}",
        "O farol vermelho é, por definição, o alerta mais direto: necessidade no "
        "topo do estado, alocação no fundo.",
        bloco="detectores",
        dependencias=["gap_ieas"],
    ),
    Formula(
        "d2",
        "Detector 2 — alocação abaixo do esperado",
        r"\hat{A}(N) = \beta_0 + \beta_1 N \;\;(\text{ajuste por ano}) \qquad"
        r"z_m = \frac{r_m - \tilde{r}}{1{,}4826\,\text{MAD}(r)},\quad r_m = A_m - \hat{A}(N_m)",
        "Ajusta, por ano, uma reta necessidade→alocação para todo o estado e mede "
        "o resíduo de cada município com escala robusta (MAD, não desvio-padrão). "
        "Alerta quando z ≤ −2 **e** o resíduo é ≥ 8 pontos percentuais abaixo do "
        "previsto. Só roda onde o eixo Alocação está completo (L1+L2+L3).",
        bloco="detectores",
        dependencias=["gap_ieas"],
    ),
    Formula(
        "d3",
        "Detector 3 — suspeita de sobrepreço",
        r"\text{alerta}_i \iff p_i \;>\; Q_3(G) + k\cdot \big(Q_3(G) - Q_1(G)\big)",
        "p_i é o preço unitário de um item de material; G é o grupo de itens da "
        "mesma categoria, mesma unidade de medida e mesma dose/concentração em "
        "PE (grupo com ≥ 5 itens). k é o fator de IQR de `conf/ieas.yml`. "
        "Severidade alta se o preço for ≥ 3× a mediana do grupo.",
        bloco="detectores",
    ),
    Formula(
        "d4",
        "Detector 4 — suspeita de desabastecimento",
        r"\text{alerta}_{a,m,t} \iff \text{taxa}_{a,m,t} \ge Q_{p}\big(\text{taxa}_a \text{ em PE},\, t\big)"
        r"\;\wedge\; m \in \text{PNCP}_t \;\wedge\; \text{nenhum insumo}(a)\ \text{contratado}",
        "Liga incidência sustentada de um agravo (percentil p de PE naquele ano) "
        "à ausência de contratação da categoria de insumo correspondente — "
        "verificada no objeto **e** na descrição dos itens das compras do "
        "município. Só considera município que aparece no PNCP no ano (senão o "
        "que há é lacuna de dado, não falha de resposta).",
        bloco="detectores",
        dependencias=["taxa"],
    ),
]


def formulas_do_bloco(bloco: str) -> list[Formula]:
    return [f for f in FORMULAS if f.bloco == bloco]


# ── Detectores de anomalia (texto curto para a página Alertas) ─────────
_D1 = (
    "Todo farol vermelho é, por definição, um alerta: a necessidade está no topo "
    "do estado e a alocação, no fundo (`gap ≤ −0,33`)."
)
_D2 = (
    "Controla pela relação necessidade→alocação do estado inteiro: ajusta, por "
    "ano, uma reta e mede o resíduo de cada município com escala robusta (MAD). "
    "Sinaliza quem está sistematicamente aquém do previsto. Só roda onde o eixo "
    "de Alocação está completo (L1+L2+L3)."
)
_D3 = (
    "Preço unitário de um item acima de Q3 + 1,5·IQR da distribuição da mesma "
    "categoria, **mesma unidade e mesma dose** em PE — a dose é extraída da "
    "descrição do item (500 mg, 50 mg/ml, 0,9%)."
)
_D4 = (
    "Liga incidência sustentada de um agravo (percentil 75+ de PE) à ausência de "
    "contratação do insumo correspondente — verificada no objeto **e na descrição "
    "dos itens** das compras do município naquele ano."
)

DETECTORES = [
    ("Desalinhamento estrutural", "desalinhamento_estrutural", _D1),
    ("Alocação abaixo do esperado", "alocacao_abaixo_do_esperado", _D2),
    ("Suspeita de sobrepreço", "suspeita_sobrepreco", _D3),
    ("Suspeita de desabastecimento", "suspeita_desabastecimento", _D4),
]

LIMITACAO_ALERTAS = (
    "Os alertas são **suspeitas para auditoria, não conclusões**. O casamento "
    "compra × insumo é por palavra-chave curada (`seeds/catmat_saude.csv`), não "
    "por classificação CATMAT estruturada — o PNCP não expõe a categoria do item "
    "— nem por processamento de linguagem natural."
)
