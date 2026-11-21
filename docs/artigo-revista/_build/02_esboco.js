const { P, H1, H2, H3, BUL, NUM, TABLE, BOX, GAP, BREAK, build } = require("./lib");
const c = [];

c.push(BOX("Decisões de partida", [
  "**Tipo de manuscrito:** artigo original — estudo ecológico de série temporal curta com desenvolvimento e avaliação de um índice composto a partir de dados abertos (unidade: município × ano; 185 municípios de Pernambuco; 2020–2024).",
  "**Alvo de tamanho:** 4.500–5.500 palavras no corpo (sem resumo e referências); até 5 tabelas/figuras; 30–40 referências. Ajustar ao limite exato do periódico escolhido (ver documento 04).",
  "**Mensagem central:** é possível, só com dados abertos, tornar visível e auditável o grau em que a alocação municipal de recursos em saúde acompanha a necessidade sanitária — desde que o índice seja avaliado quanto à robustez e às suas limitações.",
  "**Condição para escrever a seção de Resultados:** resolver as pendências críticas da seção 8 deste documento (em especial o cálculo do ranque por ano). Os números atuais do repositório não devem ir ao manuscrito sem essa revisão."], "FDE7E7"));
c.push(GAP());

c.push(H1("1. Título e palavras-chave"));
c.push(BUL("**Título (PT):** Alinhamento entre necessidade sanitária e alocação de recursos em saúde nos municípios de Pernambuco, 2020–2024: um índice composto a partir de dados abertos"));
c.push(BUL("**Title (EN):** Alignment between health needs and health resource allocation in Pernambuco’s municipalities, 2020–2024: a composite index built from open data"));
c.push(BUL("**Título alternativo, mais curto:** Necessidade e alocação em saúde nos 185 municípios de Pernambuco: um índice a partir de dados abertos"));
c.push(BUL("**Palavras-chave (DeCS, já confirmadas na etapa SIPES):** Alocação de Recursos; Gastos em Saúde; Saneamento. Se o periódico aceitar 4–5, acrescentar Sistema Único de Saúde e Controle Social Formal. **Keywords (MeSH/DeCS EN):** Resource Allocation; Health Expenditures; Sanitation."));

c.push(H1("2. O problema"));
c.push(P("**Situação.** A legislação brasileira manda ratear os recursos federais do SUS segundo as necessidades de saúde da população (Lei 8.080/1990, art. 35; LC 141/2012, art. 17). Ao mesmo tempo, a literatura registra que a alocação tende a seguir a produção histórica de serviços e fatores políticos, e que desigualdades regionais de gasto per capita sobreviveram ao aumento real do financiamento (F20, F05, N04). Os portais de transparência publicam repasses, execução e contratações, mas **não os confrontam com a carga de doença nem com o déficit sanitário** do território, e a qualidade e a completude dos sistemas de informação são irregulares (F17, F03, N06)."));
c.push(P("**Lacuna.** Há metodologias de rateio por necessidade, mas elas se dirigem às unidades da federação e são de uso administrativo (N02, F20, N03); há estudos de eficiência do gasto em recortes estaduais pontuais (F09) e análises de desigualdade de gasto (N04, F08, N05). Não se identificou, na literatura reunida, um instrumento **municipal, replicável, de código e dados abertos**, que cruze necessidade (epidemiologia, saneamento, vulnerabilidade) e alocação (repasse federal, execução própria, compras) e que exponha explicitamente os limites dos próprios dados."));
c.push(BOX("Pergunta de pesquisa", [
  "Em que medida a alocação per capita de recursos de saúde acompanha a necessidade sanitária nos 185 municípios de Pernambuco entre 2020 e 2024 e como construir, apenas com dados abertos, um índice transparente e reprodutível capaz de mostrar esse alinhamento — e quão robusto ele é às suas escolhas metodológicas?"], "E8F1FB"));

c.push(H1("3. Objetivos e hipóteses"));
c.push(H3("Objetivo geral"));
c.push(P("Desenvolver e avaliar um índice composto de alinhamento entre necessidade sanitária e alocação de recursos em saúde (IEAS/Farol-SS) para os municípios de Pernambuco, 2020–2024, utilizando exclusivamente dados abertos."));
c.push(H3("Objetivos específicos"));
for (const t of [
  "Descrever a construção do eixo **Necessidade** (carga epidemiológica de arboviroses e doenças de veiculação hídrica, internações relacionadas ao saneamento, déficit de saneamento e vulnerabilidade social) e do eixo **Alocação** (repasse federal, execução própria e compras públicas de insumos).",
  "Estimar o alinhamento por município e ano e descrever sua distribuição no tempo e no território (mesorregiões e regiões de saúde).",
  "Avaliar a **robustez** do índice: sensibilidade a pesos, à regra de agregação, ao tratamento de dados ausentes e ao modo de normalização (ranque por ano × ranque empilhado × escore-z).",
  "Examinar a **validade** do índice: associação com desfechos posteriores (internações e óbitos por causas sensíveis) e comparação com um índice de necessidades obtido por componentes principais.",
  "Documentar a **qualidade e a cobertura das fontes** (completitude, maturidade do PNCP, natureza de proxy do repasse federal) e discutir como elas condicionam as conclusões.",
  "Disponibilizar o conjunto de dados derivado, o código e uma API aberta, de modo a permitir reprodução e controle social."]) c.push(NUM(t));
c.push(H3("Perguntas/hipóteses para análise (declarar como exploratórias)"));
for (const t of [
  "**P1.** A associação entre os eixos de necessidade e de alocação é fraca a moderada, e não monotônica, entre municípios do mesmo ano.",
  "**P2.** O resultado do semáforo é sensível à escolha do eixo temporal de normalização e aos pesos, a ponto de reclassificar uma fração relevante de municípios.",
  "**P3.** Municípios pequenos concentram as classificações extremas, em parte por instabilidade de taxas (ruído amostral) e não por desalinhamento real.",
  "**P4.** A cobertura crescente do PNCP no período altera mecanicamente o eixo de alocação ao longo do tempo."]) c.push(BUL(t));

c.push(H1("4. Sequência argumentativa"));
c.push(P("A tabela abaixo fixa, movimento a movimento, o raciocínio da Introdução e da Discussão, a afirmação central de cada parágrafo e as fontes que a sustentam (IDs do documento 01). A ordem importa: o leitor deve concordar com cada passo antes de ver o seguinte."));
c.push(TABLE(["#", "Movimento", "Afirmação-núcleo (em uma frase)", "Fontes", "Função retórica"], [
  ["§1", "Contexto", "O SUS ampliou cobertura, mas convive com subfinanciamento e alocação subótima, com piores resultados nas regiões pobres.", "F01, F06", "Estabelecer relevância"],
  ["§2", "Norma × prática", "A lei manda ratear por necessidade; a prática segue o histórico de produção e é permeável a fatores políticos.", "N07, N03, F20, F05", "Enunciar a tensão"],
  ["§3", "Evidência de desigualdade", "Mais recursos, sozinhos, não reduziram o desnível regional de gasto per capita; a desigualdade existe até dentro de uma região de saúde e se liga à infraestrutura.", "N04, F08, N05, F11", "Provar que o problema persiste"],
  ["§4", "Necessidade é multidimensional", "A carga sanitária resulta de saneamento, doenças hídricas, arboviroses e vulnerabilidade — e o indicador hospitalar, isolado, é enganoso.", "F13, F15, F16, F12, F02, F14", "Justificar os componentes do eixo N"],
  ["§5", "Lacuna", "Faltam instrumentos municipais, abertos e verificáveis; as fontes abertas existem, mas têm qualidade desigual.", "N02, N03, F17, F03, F18, N06", "Mostrar que o trabalho é necessário"],
  ["§6", "Proposta", "Apresenta-se um índice composto de alinhamento, com regra de cobertura mínima, e sua avaliação de robustez.", "F19, N01, S01", "Anunciar contribuição e objetivo"],
  ["§7", "(Discussão) Leitura do alinhamento", "Alinhamento não é eficiência nem equidade plena: é a primeira etapa (dotação) das três dimensões de equidade.", "F09, F07", "Delimitar o que o índice diz"],
  ["§8", "(Discussão) Comparação", "Frente aos índices por componentes principais e ao ICVS, a opção por ranque e média ponderada troca parcimônia estatística por transparência.", "F19, F20, N02, N01", "Posicionar frente à literatura"],
  ["§9", "(Discussão) Limites", "Proxy de repasse, saneamento de 2022, PNCP em consolidação, Covid-19, subnotificação e clima condicionam a leitura.", "F14, F10, N06, F17, F12", "Antecipar críticas"],
  ["§10", "(Conclusão) Uso", "Instrumento aberto de monitoramento e controle social; requer validação e fontes melhores.", "F11, F15, N03", "Fechar com implicação prática"],
], [500, 1500, 3700, 1800, 2138]));

c.push(H2("4.1 Introdução-esqueleto (5 parágrafos com as citações encaixadas)"));
c.push(P("Texto-base para ser reescrito com a sua voz. As citações são indiretas e já parafraseadas; ajuste ao limite de referências do periódico escolhido."));
for (const t of [
  "**[§1–§2]** O Sistema Único de Saúde avançou em cobertura nas últimas décadas, mas convive com financiamento público insuficiente e com uma forma de distribuir recursos que os próprios analistas consideram subótima, o que se reflete em acesso e desfechos piores nas regiões e grupos mais pobres (MASSUDA et al., 2018). O teto de gastos, ao corrigir o orçamento federal apenas pela inflação, tende a reduzir o gasto por habitante com o crescimento da população (FUNCIA, 2019). A legislação complementar determina que o rateio dos recursos da União observe as necessidades de saúde da população em suas dimensões epidemiológica, demográfica, socioeconômica e espacial (BRASIL, 2012); a prática, porém, tem seguido o histórico de produção de serviços (MENDES; LEITE; MARQUES, 2011) e admite a influência de fatores políticos (CARVALHO, 2021).",
  "**[§3]** O desnível resultante é persistente: o aumento real expressivo do gasto público entre 2000 e 2010 deixou praticamente inalterada a desigualdade regional de gasto per capita (PIOLA; FRANÇA; NUNES, 2016); entre municípios de uma mesma região de saúde, o gasto por habitante pode diferir por múltiplos (SANTOS NETO et al., 2017); e o menor gasto acompanha tipologias inferiores de infraestrutura da atenção básica nos municípios brasileiros (AUTORIA A CONFERIR, 2021). Os inquéritos domiciliares confirmam que as desigualdades regionais e sociais de acesso persistem (VIACAVA et al., 2019).",
  "**[§4]** A necessidade que a alocação deveria acompanhar é multidimensional. Esgotamento sanitário inadequado, baixa escolaridade e menor cobertura de atenção básica associam-se à internação por doenças de veiculação hídrica (PAIVA; SOUZA, 2018); o acesso à água e ao esgotamento é um direito cuja efetivação exige transparência e responsabilização (NEVES-SILVA; HELLER, 2016) e as privações se acumulam nos grupos mais vulneráveis (NEVES-SILVA; MARTINS; HELLER, 2018). Ao mesmo tempo, indicadores hospitalares exigem cautela: sua fração atribuível ao saneamento é menor do que o senso comum supõe (BARCELLOS, 2005) e a internação por diarreia é multicausal (BOCCOLINI; BOCCOLINI, 2011).",
  "**[§5]** Existem metodologias de rateio por necessidade, mas voltadas às unidades da federação (MENDES; LEITE; CARNUT, 2020), e uma revisão recente nota que poucos estudos tomam a alocação equitativa como objeto central (CARNUT; MENDES; LEITE, 2020). Não se identificou instrumento municipal, aberto e verificável que cruze necessidade e alocação, embora as fontes existam. Elas, contudo, têm qualidade desigual: a avaliação da qualidade dos sistemas de informação é irregular (LIMA et al., 2009), a completitude carece de método padronizado (CORREIA; PADILHA; VASCONCELOS, 2014) e as compras no PNCP ainda apresentam lacunas de preenchimento (TRANSPARÊNCIA BRASIL, 2024).",
  "**[§6]** Este estudo propõe e avalia um índice composto de alinhamento entre necessidade e alocação para os 185 municípios de Pernambuco, entre 2020 e 2024, construído exclusivamente com dados abertos e acompanhado de análise de sensibilidade. O objetivo é [objetivo geral]."]) c.push(P(t, { indent: { left: 300 } }));

c.push(H1("5. Estrutura proposta (IMRaD) com conteúdo, tamanho e visuais"));
c.push(TABLE(["Seção", "Conteúdo essencial", "Palavras", "Visuais"], [
  ["Resumo (PT/EN)", "Estruturado: Objetivo, Métodos, Resultados, Conclusão (≤ 250 palavras; conferir limite). 3–5 descritores.", "250", "—"],
  ["1 Introdução", "Os 6 movimentos (§1–§6), fechando com o objetivo em uma frase.", "700–900", "—"],
  ["2 Métodos", "2.1 Desenho e recorte. 2.2 Fontes e variáveis (tabela). 2.3 Construção do eixo N. 2.4 Construção do eixo A. 2.5 Normalização, agregação e regra de cobertura. 2.6 Semáforo (limiares). 2.7 Análise de sensibilidade e validação. 2.8 Alertas explicáveis (opcional: mover para artigo complementar). 2.9 Ética e disponibilidade de dados/código; checklist STROBE/RECORD.", "1.400–1.800", "Tab. 1 (fontes); Fig. 1 (diagrama do índice)"],
  ["3 Resultados", "3.1 Cobertura e qualidade das fontes. 3.2 Distribuição dos eixos e do alinhamento por ano. 3.3 Padrão territorial (mapa; mesorregiões). 3.4 Robustez: reclassificação sob variações. 3.5 Validação (desfechos posteriores; comparação com PCA).", "1.000–1.300", "Tab. 2; Fig. 2 (mapa); Fig. 3 (N × A); Fig. 4 (sensibilidade)"],
  ["4 Discussão", "Principais achados → interpretação (alinhamento ≠ eficiência) → comparação com a literatura → implicações para controle social/gestão → limitações → trabalhos futuros.", "1.000–1.200", "—"],
  ["5 Conclusão", "2–3 frases ligadas ao objetivo; sem novos dados.", "120–180", "—"],
  ["Declarações", "Financiamento; conflitos de interesse; contribuição dos autores (CRediT); disponibilidade de dados e código; agradecimentos.", "100–150", "—"],
  ["Referências", "30–40 itens (NBR 6023 ou Vancouver, conforme o periódico), com DOI.", "—", "—"],
], [1500, 5100, 1000, 2038]));

c.push(H2("5.1 Tabelas e figuras previstas"));
for (const t of [
  "**Tabela 1 — Fontes, variáveis e papel no índice:** fonte, granularidade, período, cobertura (n de município-anos), tratamento (de variável bruta a coluna do gold). Aproveitar a página “Fontes” do painel.",
  "**Figura 1 — Diagrama do índice:** das fontes aos dois eixos, ao ranque, à diferença e ao semáforo (já existe em `docs/sipes-2026/assets/diagrama-ieas.png`; refazer em alta resolução).",
  "**Figura 2 — Mapa coroplético** do alinhamento no ano mais recente e, se couber, painel com os cinco anos (usar paleta já validada para daltonismo; incluir legenda rotulada).",
  "**Figura 3 — Diagrama de dispersão necessidade × alocação** com a diagonal de alinhamento e destaque dos extremos; marcar municípios pequenos (população < 10 mil) por forma de marcador.",
  "**Figura 4 — Sensibilidade:** percentual de municípios que mudam de cor sob cada variação (pesos ± 20 %, remoção de cada componente, ranque por ano × empilhado, escore-z).",
  "**Tabela 2 — Resultados descritivos** do alinhamento por ano e mesorregião, com intervalo de incerteza por simulação."]) c.push(BUL(t));

c.push(H1("6. Resumo estruturado (rascunho com lacunas)"));
c.push(P("**Objetivo:** Desenvolver e avaliar um índice composto de alinhamento entre necessidade sanitária e alocação de recursos em saúde nos 185 municípios de Pernambuco, 2020–2024, com dados abertos. **Métodos:** Estudo ecológico com unidade município-ano. O eixo Necessidade combinou carga de arboviroses e doenças de veiculação hídrica (SINAN), internações relacionadas ao saneamento (SIH-SUS), déficit de saneamento (Censo 2022) e extrema pobreza (CadÚnico); o eixo Alocação combinou repasse federal (Portal da Transparência, aproximação), despesa própria em saúde (SIOPS) e compras de insumos (PNCP). Cada componente foi normalizado por ranque percentil [por ano] e combinado por média ponderada; municípios com cobertura insuficiente não tiveram índice calculado. Avaliou-se a sensibilidade a pesos, agregação e normalização e a associação com [desfecho]. **Resultados:** [n] município-anos com índice; [descrever distribuição e associação entre eixos]; [percentual de reclassificação sob variações]. **Conclusão:** [uma frase que decorra dos resultados; ex.: o índice é viável como instrumento de triagem, mas depende de ...]. **Descritores:** Alocação de Recursos; Gastos em Saúde; Saneamento."));

c.push(H1("7. Cuidados de redação para torná-lo publicável"));
for (const t of [
  "**Escreva um artigo de pesquisa, não um relatório de software.** Os bugs de pipeline (lstrip, deduplicação, OOM) entram só como uma frase de validação de dados nos Métodos; o detalhe fica no repositório e num artigo de dados/software.",
  "**Separe contribuições.** Um artigo sobre o índice (este) e, se houver, outro sobre os alertas de desabastecimento/sobrepreço, que exige validação própria (ver documento 05).",
  "**Declare o delineamento e o relato:** estudo ecológico; STROBE com extensão RECORD para dados coletados rotineiramente; justifique a ausência de submissão a comitê de ética pela natureza de dados públicos agregados (Resolução CNS 510/2016, art. 1º, parágrafo único — confirmar o texto vigente).",
  "**Evite linguagem acusatória.** O índice sinaliza desalinhamento, não má gestão nem irregularidade; use “suspeita para verificação” e nunca nomeie municípios como culpados.",
  "**Todo número do texto deve ser regenerável** por um comando do repositório; cite versão/commit e DOI de depósito dos dados (Zenodo ou similar).",
  "**Use inglês técnico no resumo e nas legendas** mesmo que o corpo seja em português: aumenta a descoberta em bases internacionais."]) c.push(BUL(t));

c.push(H1("8. Pendências críticas antes de escrever Resultados"));
c.push(P("Achados da leitura do código e dos dados do repositório (`src/farol_ss/index/ieas.py`, `cli.py`, `data/gold/ieas.parquet`). Detalhes e propostas de correção no documento 05."));
c.push(TABLE(["Pendência", "Evidência", "Impacto no artigo"], [
  ["**Ranque calculado sobre os 925 município-anos empilhados, não por ano.**", "`calcular_ieas` é chamado uma vez sobre toda a tabela; a média do ranque de alocação vai de 0,30 (2020–2022) a 0,82 (2023). A diferença média (alocação − necessidade) passa de −0,32 em 2022 para +0,34 em 2023.", "A virada de “vermelho” para “azul” em 2023 reflete o nível do repasse federal e a adesão ao PNCP, não uma mudança de alinhamento entre municípios. A leitura temporal do semáforo fica inválida até recalcular por ano."],
  ["**Repasse federal (L1) é proxy de transferência social.**", "Bolsa Família/BPC por habitante; correlação de Spearman com extrema pobreza ≈ 0,35.", "Parte do eixo A mede pobreza, que também alimenta o eixo N: correlação mecânica que reduz a diferença e mascara desalinhamento."],
  ["**Cobertura do PNCP muda no período.**", "Município-anos com eixo A completo: 0 em 2020, 8 em 2021, 102 em 2022, 72 em 2023, 156 em 2024.", "Comparações entre anos confundem mudança de cobertura com mudança de alocação."],
  ["**Saneamento é retrato de 2022 aplicado a 2020–2024.**", "Coluna `saneamento_ano_referencia = 2022`.", "A necessidade varia no tempo apenas por epidemiologia e CadÚnico."],
  ["**Sem validação externa nem análise de sensibilidade.**", "Pesos e limiares (±0,10; ±0,33) fixados por julgamento.", "Exigência provável de qualquer parecerista que conheça o manual da OCDE (N01)."]], [2500, 4000, 3138]));
build("../02-esboco-artigo.docx", "Esboço do artigo científico", "Farol-SS — problema, objetivos, sequência argumentativa e estrutura IMRaD", c);
