---
title: "Alinhamento entre necessidade sanitária e alocação de recursos em saúde nos municípios de Pernambuco, 2020–2024: um índice composto a partir de dados abertos"
subtitle: "Manuscrito — versão 1 (rascunho completo para revisão do autor)"
lang: pt-BR
---

**Title:** Alignment between health needs and health resource allocation in Pernambuco's municipalities, 2020–2024: a composite index built from open data

**Autoria:** [nome do autor] — [afiliação] — [e-mail] — [ORCID]

**Descritores (DeCS):** Alocação de Recursos; Gastos em Saúde; Saneamento.
**Keywords (MeSH):** Resource Allocation; Health Expenditures; Sanitation.

> **Estado deste rascunho.** Introdução, Métodos, Resultados, Discussão e Conclusão estão escritos com os números regenerados após a correção metodológica do ranque (por ano) e da composição do eixo de alocação. Todo valor numérico dos Resultados vem dos arquivos de `docs/artigo-revista/resultados/`, gerados por `farol sensibilidade`. Marcas **[A CONFERIR]** indicam o que depende de checagem do autor ou do periódico. Remover esta caixa e as marcas antes de submeter.

# Resumo

**Objetivo:** Desenvolver e avaliar um índice composto de alinhamento entre necessidade sanitária e alocação de recursos em saúde nos 185 municípios de Pernambuco, 2020–2024, utilizando exclusivamente dados abertos.
**Métodos:** Estudo ecológico com unidade município-ano (925 observações). O eixo Necessidade combinou carga de arboviroses e de doenças de veiculação hídrica (SINAN), internações por doenças relacionadas ao saneamento ambiental inadequado (SIH-SUS), déficit de saneamento (Censo 2022) e extrema pobreza (CadÚnico). O eixo Alocação combinou transferências sociais federais per capita, usadas como aproximação do repasse federal (Portal da Transparência), e despesa própria em saúde per capita (SIOPS). Cada componente foi normalizado por ranque percentil dentro do ano e combinado por média ponderada; o contraste entre os eixos (gap) definiu um semáforo de cinco cores. Avaliaram-se a sensibilidade a normalização, pesos, limiares e composição dos eixos, a comparação com componentes principais e a associação com desfecho posterior.
**Resultados:** O índice foi calculado para 920 de 925 município-anos. A associação entre os ranques de necessidade e de alocação foi fraca (Spearman 0,17–0,37 por ano). Em média, 18,7% dos município-anos foram classificados como alocação aquém da necessidade e 17,5% como alocação além; o gap foi persistente (Spearman 0,75–0,86 entre anos consecutivos). Variações de ±20% nos pesos alteraram a cor de 5% a 8% dos município-anos; a remoção do subíndice de saneamento, de L1 ou a troca da agregação por componentes principais alteraram a cor de 48% a 52%. O gap não se associou ao desfecho posterior (Spearman 0,02 e −0,05).
**Conclusão:** O índice é viável como instrumento aberto de triagem e monitoramento territorial, mas sua leitura é relativa (compara municípios no mesmo ano) e depende fortemente de dois componentes — saneamento e a aproximação do repasse federal —, cuja qualidade limita as conclusões. Não houve evidência de validade preditiva no recorte.

**Palavras-chave:** Alocação de Recursos; Gastos em Saúde; Saneamento.

# Abstract

**Objective:** To develop and evaluate a composite index of alignment between health needs and health resource allocation in the 185 municipalities of Pernambuco, Brazil, 2020–2024, using open data only.
**Methods:** Ecological study, municipality-year unit (925 observations). The Need axis combined arbovirus and waterborne disease burden (SINAN), hospitalizations for sanitation-related diseases (SIH-SUS), sanitation deficit (2022 Census) and extreme poverty (CadÚnico). The Allocation axis combined federal social transfers per capita, used as a proxy for federal health transfers (Transparency Portal), and municipal own health spending per capita (SIOPS). Components were rank-normalized within year and combined by weighted mean; the difference between axes (gap) defined a five-color traffic light. Sensitivity to normalization, weights, thresholds and axis composition, comparison with principal components, and association with a subsequent outcome were assessed.
**Results:** The index was computed for 920 of 925 municipality-years. The association between need and allocation ranks was weak (Spearman 0.17–0.37 by year). On average, 18.7% of municipality-years showed allocation below need and 17.5% above need; the gap was persistent (Spearman 0.75–0.86 between consecutive years). ±20% weight changes altered the color of 5%–8% of municipality-years; removing the sanitation subindex or the federal-transfer component, or replacing the aggregation with principal components, altered 48%–52%. The gap was not associated with the subsequent outcome (Spearman 0.02 and −0.05).
**Conclusion:** The index is feasible as an open screening and monitoring tool, but it is relative (it compares municipalities within the same year) and depends heavily on two components whose quality limits the conclusions. No evidence of predictive validity was found.

**Keywords:** Resource Allocation; Health Expenditures; Sanitation.

# 1 Introdução

O Sistema Único de Saúde (SUS) avançou em cobertura nas últimas décadas, mas convive com financiamento público insuficiente e com uma forma de distribuir recursos que os próprios analistas consideram subótima, o que se reflete em acesso e desfechos piores nas regiões e grupos mais pobres (MASSUDA et al., 2018). O teto de gastos, ao corrigir o orçamento federal apenas pela inflação, tende a reduzir o gasto por habitante com o crescimento da população (FUNCIA, 2019). A legislação complementar determina que o rateio dos recursos da União observe as necessidades de saúde da população em suas dimensões epidemiológica, demográfica, socioeconômica e espacial (BRASIL, 2012); a prática, porém, tem seguido o histórico de produção de serviços (MENDES; LEITE; MARQUES, 2011) e admite a influência de fatores políticos (CARVALHO, 2021).

O desnível resultante é persistente. O aumento real expressivo do gasto público entre 2000 e 2010 deixou praticamente inalterada a desigualdade regional de gasto per capita (PIOLA; FRANÇA; NUNES, 2016); entre municípios de uma mesma região de saúde, o gasto por habitante pode diferir por múltiplos (SANTOS NETO et al., 2017); e o menor gasto acompanha tipologias inferiores de infraestrutura da atenção básica nos municípios brasileiros (AUTORIA A CONFERIR, 2021). Os inquéritos domiciliares confirmam que as desigualdades regionais e sociais de acesso persistem (VIACAVA et al., 2019).

A necessidade que a alocação deveria acompanhar é multidimensional. Esgotamento sanitário inadequado, baixa escolaridade e menor cobertura de atenção básica associam-se à internação por doenças de veiculação hídrica (PAIVA; SOUZA, 2018); o acesso à água e ao esgotamento é um direito cuja efetivação exige transparência e responsabilização (NEVES-SILVA; HELLER, 2016), e as privações se acumulam nos grupos mais vulneráveis (NEVES-SILVA; MARTINS; HELLER, 2018). Ao mesmo tempo, indicadores hospitalares exigem cautela: sua fração atribuível ao saneamento é menor do que o senso comum supõe (BARCELLOS, 2005) e a internação por diarreia é multicausal (BOCCOLINI; BOCCOLINI, 2011).

Existem metodologias de rateio por necessidade, mas voltadas às unidades da federação (MENDES; LEITE; CARNUT, 2020), e uma revisão recente nota que poucos estudos tomam a alocação equitativa como objeto central (CARNUT; MENDES; LEITE, 2020). Não se identificou, na literatura reunida para este estudo, instrumento municipal, aberto e verificável que cruze necessidade e alocação, embora as fontes existam. Elas, contudo, têm qualidade desigual: a avaliação da qualidade dos sistemas de informação é irregular (LIMA et al., 2009), a completitude carece de método padronizado (CORREIA; PADILHA; VASCONCELOS, 2014) e as compras no Portal Nacional de Contratações Públicas (PNCP) ainda apresentam lacunas de preenchimento (TRANSPARÊNCIA BRASIL, [ano] **[A CONFERIR]**).

Este estudo propõe e avalia um índice composto de alinhamento entre necessidade e alocação para os 185 municípios de Pernambuco, entre 2020 e 2024, construído exclusivamente com dados abertos e acompanhado de análise de sensibilidade. Seguem-se as recomendações para índices compostos de agregar com base em um marco teórico explícito e de testar a robustez às escolhas de normalização, ponderação e agregação (NARDO et al., 2008; GRECO et al., 2019 **[A CONFERIR]**). O objetivo é desenvolver e avaliar o índice, descrever o alinhamento entre necessidade e alocação no tempo e no território e documentar em que medida suas conclusões dependem das escolhas metodológicas e da qualidade das fontes.

# 2 Métodos

## 2.1 Desenho e recorte

Estudo ecológico de série temporal curta, com unidade de análise município × ano: 185 municípios de Pernambuco, incluindo o Distrito Estadual de Fernando de Noronha, de 2020 a 2024 (925 observações). Todos os dados são públicos e agregados por município; não há informação individual. O relato segue o STROBE (VON ELM et al., 2007 **[A CONFERIR]**) com a extensão RECORD para dados coletados rotineiramente. Pela natureza dos dados, o estudo dispensa apreciação por comitê de ética em pesquisa (Resolução CNS nº 510/2016, art. 1º, parágrafo único **[A CONFERIR o texto vigente]**).

## 2.2 Fontes e variáveis

A Tabela 1 resume as fontes. Valores monetários foram deflacionados para reais de 2024 pela média anual do IPCA e divididos pela população municipal do IBGE; para os anos sem estimativa publicada (2022 e 2023), a população foi interpolada linearmente. Os municípios foram identificados sempre pelo código IBGE, nunca pelo nome, e cada código reconstruído foi validado contra a lista dos 185 códigos oficiais.

**Tabela 1 — Fontes, variáveis e papel no índice.**

| Fonte | Variável usada | Papel | Cobertura no recorte |
|---|---|---|---|
| SINAN | Taxas por 100 mil hab. de dengue, chikungunya e zika (arboviroses) e de leptospirose, hepatite A e esquistossomose (veiculação hídrica) | Necessidade — epidemiológico | 271.505 notificações; 185/185 municípios × 5 anos |
| SIH-SUS (AIH Reduzida, grupo RD) | Taxa de internações por doenças relacionadas ao saneamento ambiental inadequado (DRSAI), por 100 mil hab. | Necessidade — epidemiológico | 22.597 internações; 185/185 × 5 anos |
| Censo 2022 (IBGE) | Déficit domiciliar de água, esgoto e coleta de lixo | Necessidade — saneamento | 185/185; retrato único de 2022 |
| CadÚnico (SAGI/MDS) | Famílias em extrema pobreza por mil habitantes | Necessidade — vulnerabilidade | 185/185 × 5 anos |
| Portal da Transparência | Transferências sociais federais por habitante (Bolsa Família/Novo Bolsa Família e BPC); aproximação do repasse federal (L1) | Alocação | 185/185 × 5 anos |
| SIOPS | Despesa própria em saúde per capita (L2) | Alocação | 184/185 municípios × 5 anos |
| PNCP e Compras.gov.br | Contratações de insumos de saúde per capita (L3) | Fora da composição principal; sensibilidade e alertas | 0, 8, 102, 72 e 157 município-anos com L3 em 2020–2024 |

## 2.3 Eixo Necessidade (N)

O eixo N é a média ponderada de três subíndices, cada um um ranque percentil em [0, 1] calculado entre os municípios do mesmo ano: epidemiológico (peso 0,40), saneamento (0,35) e vulnerabilidade (0,25).

O subíndice epidemiológico combina três componentes, cada um também um ranque percentil: arboviroses (soma das taxas de dengue, chikungunya e zika; peso 0,40), doenças de veiculação hídrica (soma das taxas de leptospirose, hepatite A e esquistossomose; 0,35) e internações por DRSAI (0,25). A soma antes do ranque dá a um município com carga alta em vários agravos a posição que ele de fato ocupa. O subíndice de saneamento é o ranque do déficit ponderado de água (0,35), esgotamento (0,45) e coleta de lixo (0,20), a partir da cobertura domiciliar do Censo 2022. O subíndice de vulnerabilidade é o ranque da taxa de famílias em extrema pobreza no CadÚnico. Os pesos foram definidos por julgamento, sem calibração empírica, com apoio na literatura sobre determinantes das doenças de veiculação hídrica (PAIVA; SOUZA, 2018) e na cautela quanto ao indicador hospitalar isolado (BARCELLOS, 2005), e foram submetidos à análise de sensibilidade (seção 2.7).

## 2.4 Eixo Alocação (A)

O eixo A é a média ponderada de dois componentes per capita deflacionados, em ranque percentil dentro do ano: L1, transferências sociais federais (peso 0,35 no arquivo de parâmetros) e L2, despesa própria em saúde (0,40). Como a composição usa só esses dois, os pesos são renormalizados para 0,47 e 0,53. A terceira camada prevista inicialmente, L3 (contratação de insumos no PNCP e no Compras.gov.br), ficou fora da composição principal porque sua cobertura cresce no período — nenhum município-ano tinha os três componentes em 2020, e 156 tinham em 2024 — de modo que, com L3 dentro, o mesmo município mudaria de posição apenas porque o PNCP passou a cobri-lo. L3 entra na análise de sensibilidade.

L1 é uma **aproximação**: o repasse fundo a fundo ao ente (`/transferencias`) exige acesso gov.br elevado e responde com erro de autorização à chave gratuita do Portal da Transparência. O que a chave livre acessa são as transferências sociais federais por município. Neste artigo L1 é chamado "transferências sociais federais per capita" e não "repasse de saúde".

## 2.5 Normalização, agregação e regra de cobertura

A normalização é o ranque percentil, robusto a valores extremos e que não supõe distribuição normal, aplicado **separadamente em cada ano**. Essa escolha é central: ranquear os 925 município-anos em conjunto faria o gap medir mudanças de nível entre anos (a mediana de L1 passou de R$ 945 em 2022 para R$ 2.227 em 2023), e não o alinhamento entre municípios. A consequência é que o gap médio é nulo por construção em cada ano; o semáforo compara municípios entre si no mesmo ano e não permite concluir que a alocação estadual melhorou ou piorou.

A agregação é a média ponderada que renormaliza os pesos pelos componentes presentes. Para evitar calcular o índice sobre dado majoritariamente ausente, o eixo N exige ao menos 60% dos subíndices, e o eixo A exige ao menos 50% dos componentes e no mínimo dois; abaixo disso o índice não é calculado e o município-ano recebe a cor cinza, que significa ausência de dado, nunca um resultado.

## 2.6 Gap e semáforo

O contraste é o **gap** = A − N ∈ [−1, 1]. Gap negativo indica alocação em posição inferior à da necessidade. O semáforo usa limiares fixados por julgamento: vermelho (gap ≤ −0,33), amarelo (−0,33 a −0,10), verde (−0,10 a +0,10, alinhamento), verde também entre +0,10 e +0,33 e azul (gap ≥ +0,33, alocação superior à necessidade). O verde é o alvo, não o topo de uma escala. O indicador de alinhamento 1 − |gap| serve apenas para ordenar, nunca para colorir. O semáforo sinaliza desalinhamento relativo entre dois ordenamentos; não mede eficiência, qualidade do gasto nem irregularidade de gestão.

## 2.7 Análise de sensibilidade e validação

Cada variante é uma nova execução do mesmo código do índice, e a concordância é medida pelo percentual de município-anos que mantêm a cor do caso-base (o cinza conta como uma cor) e pelo Spearman do gap com o do caso-base. As variantes foram: (a) normalização — ranque empilhado e escore-z por ano, mapeado por Φ para [0, 1]; (b) pesos — iguais, ±20% em cada peso e 1.000 sorteios de uma distribuição de Dirichlet(1,…,1) para os pesos dos dois eixos; (c) limiares — ±0,05 e ±0,15 (internos) e ±0,25 e ±0,40 (externos); (d) composição do eixo A — com L3 e sem L1; (e) composição do eixo N — remoção de cada subíndice; e (f) agregação do eixo N pelo primeiro componente principal dos três subíndices padronizados, calculado por ano.

Para a validade, examinou-se a associação (Spearman) entre o gap em *t* e (i) a variação da taxa de internações por DRSAI entre *t* e *t*+1 e (ii) a taxa em *t*+1, em 736 pares município-ano. Óbitos por causas sensíveis não estão no recorte. As hipóteses foram declaradas como exploratórias: P1, associação fraca a moderada entre os eixos; P2, sensibilidade da cor a pesos e normalização; P3, concentração das classificações extremas em municípios pequenos (< 10 mil hab.); P4, efeito mecânico da cobertura crescente do PNCP.

## 2.8 Disponibilidade de dados e código

Código, parâmetros (`conf/ieas.yml`), dados derivados e API aberta estão em github.com/protazoarium/farol-ss; o painel público está em farol-ss.streamlit.app. Todos os números deste artigo são regeneráveis pelo comando `farol sensibilidade` sobre a versão `[commit/tag]` **[preencher]**, com depósito arquivado em `[DOI Zenodo]` **[preencher]**.

# 3 Resultados

## 3.1 Cobertura e qualidade das fontes

O índice foi calculado para 920 dos 925 município-anos; os cinco restantes são todos os anos de Fernando de Noronha, sem despesa própria no SIOPS (cobertura do eixo A = 0,50, abaixo do piso de dois componentes). O eixo N teve cobertura completa (três subíndices) em todos os município-anos. L1 estava presente nos 925 município-anos e L2 em 920. L3 existia em 0 município-anos em 2020, 8 em 2021, 102 em 2022, 72 em 2023 e 157 em 2024. O saneamento é um retrato de 2022 aplicado aos cinco anos, de modo que o subíndice não varia no tempo.

## 3.2 Distribuição do alinhamento

A Tabela 2 mostra as cores por ano. Considerando os 920 município-anos com índice, 391 (42,5%) foram verdes, 196 (21,3%) amarelos, 172 (18,7%) vermelhos e 161 (17,5%) azuis. A distribuição foi estável entre os anos, como esperado do ranque por ano. O desvio-padrão do gap foi de 0,32 a 0,37 por ano.

**Tabela 2 — Semáforo por ano (n de municípios; o cinza é Fernando de Noronha) e associação entre os ranques de necessidade e de alocação.**

| Ano | Vermelho | Amarelo | Verde | Azul | Cinza | Spearman N × A |
|---|---|---|---|---|---|---|
| 2020 | 35 | 43 | 73 | 33 | 1 | 0,23 |
| 2021 | 36 | 42 | 72 | 34 | 1 | 0,17 |
| 2022 | 35 | 38 | 78 | 33 | 1 | 0,22 |
| 2023 | 34 | 36 | 82 | 32 | 1 | 0,35 |
| 2024 | 32 | 37 | 86 | 29 | 1 | 0,37 |

A associação entre os ranques dos dois eixos foi fraca em todos os anos (Spearman de 0,17 a 0,37), com valores mais altos em 2023–2024 (hipótese P1 corroborada na parte "fraca"; a ausência de monotonicidade não foi testada). A associação isolada de L1 com a extrema pobreza, que também compõe N, foi de 0,35 nos 925 município-anos, e a de L2 com a extrema pobreza, de 0,21.

## 3.3 Persistência e padrão territorial

O gap foi persistente: o Spearman entre anos consecutivos variou de 0,75 a 0,86, e entre 2020 e 2024 foi de 0,65. Trinta e cinco municípios mantiveram a mesma cor nos cinco anos, seis deles em vermelho. Trinta e três municípios foram vermelhos em ao menos três anos e 29 foram azuis em ao menos três anos; 67 municípios foram vermelhos e 63 azuis em ao menos um ano.

**Tabela 3 — Semáforo por mesorregião, município-anos agrupados 2020–2024 (%) e posições médias dos eixos.**

| Mesorregião | Municípios | Vermelho | Amarelo | Verde | Azul | N médio | A médio |
|---|---|---|---|---|---|---|---|
| Agreste | 71 | 18,0 | 21,4 | 44,8 | 15,8 | 0,52 | 0,51 |
| Mata | 43 | 18,1 | 18,1 | 40,9 | 22,8 | 0,43 | 0,47 |
| Metropolitana do Recife | 14 | 27,1 | 31,4 | 28,6 | 12,9 | 0,48 | 0,36 |
| Sertão | 41 | 21,0 | 24,4 | 45,9 | 8,8 | 0,58 | 0,51 |
| São Francisco | 15 | 9,3 | 12,0 | 40,0 | 38,7 | 0,46 | 0,65 |

A Região Metropolitana do Recife concentrou a maior proporção de vermelhos e amarelos (58,5% somados) e a menor posição média de alocação (0,36); o São Francisco pernambucano concentrou a maior proporção de azuis (38,7%) e a maior posição média de alocação (0,65). O mapa por município no ano mais recente está disponível no painel público (Figura 2 **[gerar para a versão final]**).

## 3.4 Robustez

A Tabela 4 resume a concordância das variantes com o caso-base. Mudanças de ±20% em um peso isolado alteraram a cor de 5,1% a 7,5% dos município-anos, e pesos iguais, de 11,6%. A mudança dos limiares internos para ±0,05 ou ±0,15 alterou 5,6% e 5,2%, e a dos externos para ±0,25 ou ±0,40, 12,9% e 8,6%. O gap em si foi muito estável a essas variações (Spearman ≥ 0,99). Nos 1.000 sorteios de pesos de Dirichlet, a mediana de município-anos que mantiveram a cor foi de 59,2% (percentis 5–95: 42,7%–78,3%) e o Spearman mediano do gap com o do caso-base foi de 0,80 (0,46–0,95): o ordenamento é razoavelmente estável, mas a cor é sensível quando os pesos variam amplamente, inclusive com componentes de peso próximo de zero.

**Tabela 4 — Concordância das variantes com o caso-base (n = 925 município-anos).**

| Grupo | Variante | Mantém a cor (%) | Spearman do gap |
|---|---|---|---|
| Normalização | Ranque empilhado (925 município-anos) | 45,4 | 0,69 |
| Normalização | Escore-z por ano | 80,1 | 0,96 |
| Pesos | Iguais nos dois eixos | 88,4 | 0,99 |
| Pesos | Cada peso de N ±20% (6 variantes) | 92,5–94,7 | 0,99 |
| Pesos | Cada peso de A ±20% (4 variantes) | 93,4–94,9 | 0,99 |
| Limiares | Internos ±0,05 / ±0,15 | 94,4 / 94,8 | 1,00 |
| Limiares | Externos ±0,25 / ±0,40 | 87,1 / 91,4 | 1,00 |
| Eixo A | Com L3 (3 componentes) | 77,2 | 0,91 |
| Eixo A | Sem L1 (só L2) | 50,7 | 0,65 |
| Eixo N | Sem subíndice epidemiológico | 71,5 | 0,91 |
| Eixo N | Sem subíndice de saneamento | 51,7 | 0,70 |
| Eixo N | Sem subíndice de vulnerabilidade | 70,1 | 0,93 |
| Agregação de N | 1º componente principal | 48,4 | 0,63 |

As escolhas que mais alteraram o resultado foram a normalização (ranque empilhado, 54,6% de mudança de cor, o artefato que a correção por ano elimina), a remoção do saneamento (48,3%), a remoção de L1 (49,3%) e a troca da agregação de N pelo primeiro componente principal (51,6%). O primeiro componente principal explicou, em média, 46,6% da variância dos três subíndices, e seu ordenamento teve correlação de apenas 0,50 com o do eixo N do caso-base: os subíndices medem dimensões pouco correlacionadas entre si, o que sustenta agregá-los por um marco teórico e não por parcimônia estatística.

A inclusão de L3 no eixo A (hipótese P4) alterou a cor de 0% dos município-anos em 2020, 5,9% em 2021, 40,5% em 2022, 37,8% em 2023 e 29,7% em 2024, com variação média absoluta do gap de 0,00, 0,03, 0,16, 0,15 e 0,12. O efeito aparece justamente nos anos em que a cobertura do PNCP passa de poucos a muitos municípios, o que confirma a escolha de mantê-lo fora da composição principal.

## 3.5 Municípios pequenos e validade

Municípios com menos de 10 mil habitantes (20 municípios, 86 município-anos) tiveram menos classificações extremas (vermelho ou azul: 22,1%) que os demais (37,6%), o oposto do previsto em P3: não houve evidência de que a instabilidade de taxas em municípios pequenos concentre os extremos. O gap em *t* não se associou à variação da taxa de internações por DRSAI de *t* a *t*+1 (Spearman 0,02) nem à taxa em *t*+1 (−0,05), em 736 pares: o recorte não oferece evidência de validade preditiva.

# 4 Discussão

**Principais achados.** O alinhamento entre necessidade e alocação em Pernambuco, medido por este índice, é fraco e persistente: a posição de um município na alocação pouco acompanha sua posição na necessidade (Spearman 0,17–0,37), cerca de um terço dos município-anos fica nas faixas extremas e a posição se mantém de um ano para o outro. Esse padrão é compatível com a literatura que descreve uma alocação que segue o histórico de produção e fatores não ligados à necessidade (MENDES; LEITE; MARQUES, 2011; CARVALHO, 2021), mas o desenho ecológico e os limites de dados abaixo impedem inferir causa.

**O que o índice mede.** O alinhamento aqui é a primeira etapa — a dotação — das dimensões de equidade (COHN, 2005); não é eficiência do gasto, que exige modelos próprios de produção (RODRIGUES; GONTIJO; GONÇALVES, 2021), nem qualidade da atenção. O semáforo é relativo ao ano: por construção, o gap médio é nulo e o instrumento não diz se a alocação estadual melhorou. Uma versão anterior do cálculo, que ranqueava todos os anos em conjunto, produzia uma "virada" de vermelho para azul em 2023 que era apenas o salto do nível de L1; a correção por ano elimina o artefato; o ranque empilhado muda a cor de 54,6% dos município-anos em relação ao ranque por ano. Quem usa índices compostos para apoiar decisões deve, portanto, declarar a base de comparação da normalização.

**Comparação com a literatura.** As metodologias de rateio por necessidade existentes se dirigem às unidades da federação e a fins administrativos (MENDES; LEITE; CARNUT, 2020; CARNUT; MENDES; LEITE, 2020). Frente a índices compostos por componentes principais (LUIZ et al., 2009), este estudo optou por ranque e média ponderada, trocando parcimônia estatística por transparência: o primeiro componente explicou menos da metade da variância, e os dois ordenamentos diferiram bastante, o que mostra que a escolha da agregação não é neutra e deve ser reportada junto ao índice (NARDO et al., 2008).

**Robustez e dependência de poucos componentes.** O resultado é robusto a variações moderadas de pesos e limiares (5% a 13% de mudança de cor) e frágil à remoção de um componente estrutural. A dependência do saneamento é a mais marcante: ele tem o segundo maior peso em N e sua remoção é a que mais altera o resultado, mas é um retrato de 2022, de modo que a variação temporal de N reflete só epidemiologia e pobreza. Além disso, o eixo A com apenas dois componentes torna L1 decisivo, e L1 é uma aproximação do repasse de saúde.

**Municípios pequenos.** A hipótese de que a instabilidade de taxas em municípios pequenos concentraria os extremos não se confirmou. É possível que o uso de ranques e da soma de agravos atenue esse ruído; a hipótese de que os pequenos tendam a ficar no meio da distribuição por motivos distintos (p. ex. repasses mínimos per capita elevados e carga epidemiológica baixa) não foi testada aqui.

**Validade.** Não se encontrou associação entre o gap e a evolução posterior das internações por DRSAI. Isso não invalida o índice como instrumento de monitoramento da dotação, mas impede afirmar que ele antecipe pior desfecho. O desfecho disponível é fraco para essa finalidade: as internações compõem o próprio eixo N, a janela de um ano é curta e óbitos por causas sensíveis não estão no recorte. A validação externa deve usar desfechos independentes dos componentes e janelas mais longas.

**Limitações.** (i) L1 é uma aproximação (transferência social) correlacionada com a extrema pobreza (Spearman 0,35), de modo que parte do eixo A mede necessidade e aproxima mecanicamente os dois eixos, reduzindo o gap. (ii) O saneamento é um retrato de 2022. (iii) A cobertura do PNCP está em consolidação e deixou L3 fora da composição principal. (iv) Os pesos e limiares foram fixados por julgamento, e a sensibilidade mostra que a cor de uma fração relevante de município-anos depende deles. (v) Subnotificação e qualidade desigual dos sistemas de informação (LIMA et al., 2009; CORREIA; PADILHA; VASCONCELOS, 2014; SILVA; LEITE; ALMEIDA, 2009) afetam as taxas, assim como a variabilidade climática afeta as doenças diarreicas (DUARTE et al., 2019) e a pandemia de Covid-19 alterou o padrão de internações em 2020–2021 (COTRIM JUNIOR; CABRAL, 2020). (vi) O ranque limita a escala a [0, 1] e impede detectar diferenças de magnitude;. (vii) O estudo se restringe a um estado.

**Uso responsável.** O semáforo sinaliza desalinhamento relativo e prioridade de verificação; não indica má gestão nem irregularidade, e nenhum município deve ser tratado como culpado a partir dele. O código e os dados abertos permitem que qualquer pessoa reproduza e questione os resultados, o que é parte da proposta de controle social.

# 5 Conclusão

Um índice aberto e reprodutível mostrou que, em Pernambuco, a posição dos municípios na alocação de recursos em saúde acompanha pouco a sua posição na necessidade sanitária, e que esse desalinhamento é persistente. O índice é adequado como instrumento de triagem e de monitoramento territorial relativo, mas depende fortemente do saneamento e da aproximação do repasse federal e não mostrou validade preditiva, de modo que seu uso exige as fontes melhores e a validação externa indicadas aqui.

# Declarações

**Financiamento:** [preencher]. **Conflitos de interesse:** [preencher]. **Contribuição dos autores (CRediT):** [preencher]. **Disponibilidade de dados e código:** ver seção 2.8. **Agradecimentos:** [preencher].

# Referências

<!--REFS-->

---

# Notas de revisão (remover antes de submeter)

1. **Tabelas e figuras em falta.** As Figuras 1–4 do esboço ainda precisam ser produzidas: Figura 1 (diagrama; há uma versão em `docs/sipes-2026/assets/diagrama-ieas.png`), Figura 2 (mapa), Figura 3 (dispersão N × A, municípios pequenos em outro marcador) e Figura 4 (sensibilidade, a partir de `resultados/variantes.csv`). O ambiente não tem biblioteca de gráficos instalada.
2. **Referências [A CONFERIR].** N05 (autoria e DOI), N06 (relatório da Transparência Brasil), N02 (título), N04 (paginação), GRECO et al. (2019) e VON ELM et al. (2007) vieram marcadas como sugeridas ou não conferidas no fichamento; confirmar antes de submeter. Trocar "AUTORIA A CONFERIR, 2021" pelo sobrenome correto.
3. **Resolução CNS 510/2016** — confirmar o texto vigente do art. 1º, parágrafo único.
4. **Contagem de município-anos com os três componentes.** O esboço cita 156 em 2024 (eixo A completo) e a Tabela 1 cita 157 município-anos com L3 em 2024; a diferença é Fernando de Noronha, que tem L3 mas não L2. Padronizar no texto final.
5. **Afirmação sobre P3.** A explicação para os pequenos municípios na Discussão é hipótese, não resultado.
6. **Mapas e mesorregiões.** A Tabela 3 agrupa município-anos 2020–2024 (n = 920); conferir se o periódico prefere o ano mais recente.
7. **Tamanho.** Contar as palavras do corpo e ajustar ao limite do periódico (alvo do esboço: 4.500–5.500 palavras).
