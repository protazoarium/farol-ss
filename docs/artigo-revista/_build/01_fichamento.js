const { P, H1, H2, H3, BUL, TABLE, BOX, GAP, BREAK, build, runs } = require("./lib");
const refs = require("./refs");
const Q = { F01:"A1",F02:"A1",F03:"A1",F04:"A1",F05:"A1",F06:"A1",F07:"A1",F08:"A1",F09:"A1",F10:"A2",F11:"A1",F12:"A2",F13:"A1",F14:"A1",F15:"A1",F16:"A1",F17:"A1",F18:"A1",F19:"A1",F20:"A2" };
const ST = { TI:"Texto integral lido", RES:"Só resumo/metadados — conferir", SUG:"Sugerida — não conferida" };
const c = [];

c.push(H1("1. Como usar este fichamento"));
c.push(P("Este documento reúne **" + refs.length + " fichas** para o artigo sobre o Farol-SS: as 20 fichas da revisão já feita para o SIPES 2026 (texto integral lido) mais 7 fontes acrescentadas nesta etapa (índices compostos, alocação por necessidade, gasto regional, qualidade do PNCP, base legal) e 3 sugestões de leitura ainda não conferidas. Cada ficha traz a referência (NBR 6023), a ideia central em redação própria e **duas variantes prontas de citação indireta** — uma sintética e uma comparativa/crítica — já indicando a seção do artigo onde entram."));
c.push(BOX("Legenda de confiabilidade — leia antes de citar", [
  "**Texto integral lido**: a ficha foi feita a partir do PDF. Ainda assim, confira a página se for incluí-la (a NBR 10520 a torna obrigatória na citação direta e recomendada na indireta).",
  "**Só resumo/metadados**: o conteúdo vem de resumo, página do periódico ou resultado de busca. Leia o texto integral, preencha autoria/DOI marcados entre colchetes e só então use a variante de citação.",
  "**Sugerida — não conferida**: lembrança de literatura conhecida, sem verificação nesta sessão. Não entra no manuscrito sem que você abra a fonte e confirme título, ano, DOI e páginas. Nesses casos, as variantes marcadas “[Preencher após leitura]” são propositalmente incompletas."]));
c.push(GAP());

c.push(H2("1.1 Regras para citar indiretamente sem plagiar"));
for (const t of [
  "**Reescreva a ideia, não as palavras.** Trocar sinônimos de uma frase do autor continua sendo cópia. Leia o trecho, feche o PDF, escreva o que entendeu e só depois confira se o sentido ficou fiel.",
  "**Sintetize em vez de resumir.** A citação mais forte junta dois ou três autores numa mesma afirmação (ex.: “… (PAIVA; SOUZA, 2018; NEVES-SILVA; HELLER, 2016)”) e acrescenta o seu argumento ao final.",
  "**Cite o que o autor sustenta, não o que você quer que ele sustente.** Respeite o delineamento: estudo ecológico não prova causa individual; estudo de um município não generaliza para o estado.",
  "**Autor-data (NBR 10520:2023).** Na citação indireta a página é opcional, mas recomendável quando a ideia vem de passagem específica; “apud” só quando for impossível consultar a fonte primária. Se o periódico escolhido exigir Vancouver (numérico), converta com o gerenciador de referências a partir do `referencias.ris` — não manualmente.",
  "**Verifique a similaridade antes de submeter.** Rode o texto num verificador (o repositório tem `docs/sipes-2026/revisao/_check_plagio.py`, que procura sequências de 8 palavras iguais às dos PDFs) e, se o periódico usar, num verificador institucional. Trechos técnicos inevitáveis (nomes de agravos, siglas de sistemas) não são problema.",
  "**Não reaproveite integralmente texto seu já publicado** (por exemplo, o resumo do SIPES) sem declarar; periódicos tratam isso como autoplágio. O artigo deve ser reescrito e ampliado, e o trabalho em evento citado como apresentação prévia, se o periódico pedir."]) c.push(BUL(t));
c.push(GAP());
c.push(BOX("Exemplo de transformação", [
  "**Trecho da fonte (resumo de Mendes, Leite e Marques, 2011, em síntese):** a alocação tende a seguir o histórico de produção e não as necessidades.",
  "**Cópia disfarçada (evitar):** “A alocação de recursos segue a produção histórica e não as necessidades da população (MENDES; LEITE; MARQUES, 2011).”",
  "**Citação indireta aceitável:** “O padrão histórico de repasses, ancorado no volume de serviços já produzidos, tende a reproduzir a oferta existente em vez de responder à demanda sanitária da população — situação que contraria o princípio da equidade (MENDES; LEITE; MARQUES, 2011).”"], "E8F1FB"));

c.push(BREAK());
c.push(H1("2. Quadro-resumo"));
const rows = refs.map(r => [r.id, r.cham, Q[r.id] || "—", ST[r.st], r.sec]);
c.push(TABLE(["ID", "Chamada", "Qualis*", "Situação", "Seção do esboço"], rows, [700, 3000, 900, 2700, 2338]));
c.push(P("*Estrato do Qualis Referência 2017–2020 registrado na revisão do SIPES. O Qualis por quadriênio foi encerrado como instrumento de avaliação (ver documento de periódicos); trate-o como informação histórica e reconfira no painel Sucupira.", { run: { size: 18, color: "555555" } }));

c.push(BREAK());
c.push(H1("3. Fichas"));
for (const r of refs) {
  c.push(H3(r.id + " · " + r.cham));
  c.push(P("**Situação:** " + ST[r.st] + (Q[r.id] ? " · **Qualis (2017–2020):** " + Q[r.id] : "") + " · **Onde entra:** " + r.onde, { keepNext: true }));
  c.push(P("**Referência (NBR 6023):** " + r.ref));
  c.push(P("**Ideia central (redação própria):** " + r.ideia));
  c.push(P("**Citação indireta — variante 1 (sintética):** " + r.a, { indent: { left: 360 } }));
  c.push(P("**Citação indireta — variante 2 (comparativa/crítica):** " + r.b, { indent: { left: 360 } }));
  c.push(P("**Cuidado:** " + r.cuidado, { run: { color: "8A4B00" } }));
}

c.push(BREAK());
c.push(H1("4. Lacunas de literatura a preencher"));
c.push(P("A revisão cobre bem financiamento do SUS, saneamento e qualidade de sistemas de informação. Faltam fontes em quatro frentes que um avaliador de periódico provavelmente cobrará; sugere-se uma busca dirigida (SciELO, LILACS, PubMed, Scopus) antes da submissão:"));
for (const t of [
  "**Arboviroses e determinantes locais** (dengue, chikungunya, zika em Pernambuco e no Nordeste; subnotificação no SINAN; relação com saneamento e resíduos). A busca desta etapa encontrou apenas estudos sobre chikungunya na 1ª Região de Saúde (2015–2021), uma análise 2018–2021 da pandemia e uma dissertação da UFPE sobre dengue com modelos para dados em painel — leia-os, mas são insuficientes e parte é dissertação.",
  "**Compras públicas de saúde com dados abertos** (PNCP, Painel de Preços, Banco de Preços em Saúde) e detecção de anomalias em contratações — a busca retornou sobretudo dissertações, anais (SBC) e relatórios; faltam artigos em periódico de saúde coletiva.",
  "**Suavização de taxas em áreas pequenas** (métodos bayesianos empíricos) e autocorrelação espacial: necessários porque o recorte inclui municípios com poucos milhares de habitantes.",
  "**Impacto da Covid-19 nos sistemas de informação e no financiamento (2020–2022)**: subnotificação de agravos e recursos extraordinários transferidos aos municípios."]) c.push(BUL(t));
build("../01-fichamento-citacoes-indiretas.docx", "Fichamento e citações indiretas", "Farol-SS — revisão bibliográfica para o artigo científico", c);
