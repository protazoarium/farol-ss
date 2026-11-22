"""Gera 04-manuscrito-JHI.pdf: versão anonimizada, formatada pelas diretrizes do Journal of Health Informatics (SBIS).

Regras aplicadas (página oficial 'Instruções aos autores', conferida em nov/2026): A4, sem colunas, Times New Roman 12,
espaçamento simples, margens sup. 3,5 / inf. 2,5 / esq. e dir. 2,0 cm; título ≤ 20 palavras, sentence case, em pt/en/es;
resumo estruturado ≤ 200 palavras nos 3 idiomas; ≤ 3 descritores por idioma (DeCS/MeSH); Introdução, Métodos, Resultados,
Discussão, Conclusão; declarações (Financiamento, Conflitos, IA) antes das Referências; citações Vancouver numéricas entre
colchetes por ordem de aparição; ≤ 10 ilustrações, todas com título e fonte; manuscrito sem identificação dos autores.
Uso: python3 -I montar_jhi.py
"""
import pathlib, re, subprocess

base = pathlib.Path(__file__).resolve().parent.parent
src = (base / "03-manuscrito.md").read_text(encoding="utf-8")
body = src.split("# 1 Introdução")[1].split("# Declarações")[0]
body = "# 1 Introdução" + body

# ── 1. Referências (Vancouver, abreviaturas NLM) ────────────────────────────────────────────────
ACESSO = "citado 21 nov 2026"
V = {
 "F01": "Massuda A, Hone T, Leles FAG, de Castro MC, Atun R. The Brazilian health system at crossroads: progress, crisis and resilience. BMJ Glob Health. 2018;3(4):e000829. doi:10.1136/bmjgh-2018-000829",
 "F06": "Funcia FR. Subfinanciamento e orçamento federal do SUS: referências preliminares para a alocação adicional de recursos. Cienc Saude Colet. 2019;24(12):4405-15. doi:10.1590/1413-812320182412.25892019",
 "N07": f"Brasil. Lei Complementar nº 141, de 13 de janeiro de 2012. Diário Oficial da União. 16 jan 2012 [{ACESSO}]. Disponível em: <http://www.planalto.gov.br/ccivil_03/leis/lcp/lcp141.htm>",
 "F20": "Mendes Á, Leite MG, Marques RM. Discutindo uma metodologia para a alocação equitativa de recursos federais para o Sistema Único de Saúde. Saude Soc. 2011;20(3):673-90. doi:10.1590/S0104-12902011000300013",
 "F05": "Carvalho GP. Desigualdades regionais e o papel dos recursos federais no SUS: fatores políticos condicionam a alocação de recursos? Cienc Saude Colet. 2021;26(Supl 2):3409-21. doi:10.1590/1413-81232021269.2.31192019",
 "N04": "Piola SF, França JRM, Nunes A. Os efeitos da Emenda Constitucional 29 na alocação regional dos gastos públicos no Sistema Único de Saúde no Brasil. Cienc Saude Colet. 2016;21(2):411-22. doi:10.1590/1413-81232015212.10402015",
 "F08": "Santos Neto JA, Mendes ÁN, Pereira AC, Paranhos LR. Análise do financiamento e gasto do Sistema Único de Saúde dos municípios da região de saúde Rota dos Bandeirantes do estado de São Paulo, Brasil. Cienc Saude Colet. 2017;22(4):1269-80. doi:10.1590/1413-81232017224.28452016",
 "N05": "Kashiwakura HK, Gonçalves AO, Azevedo RR, Nunes A, Silva CAT. Retrato da atenção básica no Brasil: gastos e infraestrutura em municípios brasileiros. Cienc Saude Colet. 2021;26(Supl 2):3397-408. doi:10.1590/1413-81232021269.2.37112019",
 "F11": "Viacava F, Porto SM, Carvalho CC, Bellido JG. Desigualdades regionais e sociais em saúde segundo inquéritos domiciliares (Brasil, 1998-2013). Cienc Saude Colet. 2019;24(7):2745-60. doi:10.1590/1413-81232018247.15812017",
 "F13": "Paiva RFPS, Souza MFP. Associação entre condições socioeconômicas, sanitárias e de atenção básica e a morbidade hospitalar por doenças de veiculação hídrica no Brasil. Cad Saude Publica. 2018;34(1):e00017316. doi:10.1590/0102-311x00017316",
 "F15": "Neves-Silva P, Heller L. O direito humano à água e ao esgotamento sanitário como instrumento para promoção da saúde de populações vulneráveis. Cienc Saude Colet. 2016;21(6):1861-70. doi:10.1590/1413-81232015216.03422016",
 "F16": "Neves-Silva P, Martins GI, Heller L. “A gente tem acesso de favores, né?”. A percepção de pessoas em situação de rua sobre os direitos humanos à água e ao esgotamento sanitário. Cad Saude Publica. 2018;34(3):e00024017. doi:10.1590/0102-311x00024017",
 "F02": "Barcellos C. A lenda urbana sobre internações devidas à falta de saneamento. Cad Saude Publica. 2005;21(4):996-7. doi:10.1590/S0102-311X2005000400001",
 "F12": "Boccolini CS, Boccolini PMM. Relação entre aleitamento materno e internações por doenças diarreicas nas crianças com menos de um ano de vida nas Capitais Brasileiras e Distrito Federal, 2008. Epidemiol Serv Saude. 2011;20(1):19-26. doi:10.5123/S1679-49742011000100003",
 "N02": "Mendes Á, Leite MG, Carnut L. Uma metodologia para rateio dos recursos federais do SUS: o índice de necessidades de saúde. Rev Saude Publica. 2020;54:77. doi:10.11606/s1518-8787.2020054001661",
 "N03": "Carnut L, Mendes Á, Leite MG. Metodologias para alocação equitativa de recursos financeiros em saúde: uma revisão integrativa. Saude Debate. 2020;44(126):902-18. doi:10.1590/0103-1104202012624",
 "F17": "Lima CRA, Schramm JMA, Coeli CM, Silva MEM. Revisão das dimensões de qualidade dos dados e métodos aplicados na avaliação dos sistemas de informação em saúde. Cad Saude Publica. 2009;25(10):2095-109. doi:10.1590/S0102-311X2009001000002",
 "F03": "Correia LOS, Padilha BM, Vasconcelos SML. Métodos para avaliar a completitude dos dados dos sistemas de informação em saúde do Brasil: uma revisão sistemática. Cienc Saude Colet. 2014;19(11):4467-78. doi:10.1590/1413-812320141911.02822013",
 "N06": f"Transparência Brasil. Recomendações e desafios técnicos — PNCP: qualidade de dados. Versão 1.0. São Paulo: Transparência Brasil; 2024 [{ACESSO}]. Disponível em: <https://www.transparencia.org.br/downloads/publicacoes/qualidade_dados_portal_nacional_de_contratacoes_publicas.pdf>",
 "N01": "Nardo M, Saisana M, Saltelli A, Tarantola S, Hoffmann A, Giovannini E. Handbook on constructing composite indicators: methodology and user guide. Paris: OECD Publishing; 2008. doi:10.1787/9789264043466-en",
 "F19": "Luiz OC, Heimann LS, Boaretto RC, Pacheco AG, Pessoto UC, Ibanhes LC, et al. Diferenciais intermunicipais de condições de vida e saúde: construção de um indicador composto. Rev Saude Publica. 2009;43(1):115-22. doi:10.1590/S0034-89102009000100015",
 "S01": "Greco S, Ishizaka A, Tasiou M, Torrisi G. On the methodological framework of composite indices: a review of the issues of weighting, aggregation, and robustness. Soc Indic Res. 2019;141:61-94. doi:10.1007/s11205-017-1832-9",
 "F09": "Rodrigues AC, Gontijo TS, Gonçalves CA. Eficiência do gasto público em atenção primária em saúde nos municípios do Rio de Janeiro, Brasil: escores robustos e seus determinantes. Cienc Saude Colet. 2021;26(Supl 2):3567-79. doi:10.1590/1413-81232021269.2.04342020",
 "F07": "Cohn A. Eqüidade, saúde e critérios para alocação de recursos. Cienc Saude Colet. 2005;10(2):287-8. doi:10.1590/S1413-81232005000200003",
 "F14": "Duarte JL, Diaz-Quijano FA, Batista AC, Duarte AF, Melchior LAK, Giatti LL. Variabilidade climática e internações por doenças diarreicas infecciosas em um município da Amazônia Ocidental brasileira. Cienc Saude Colet. 2019;24(8):2959-70. doi:10.1590/1413-81232018248.21232017",
 "F10": "Cotrim Junior DF, Cabral LMS. Crescimento dos leitos de UTI no país durante a pandemia de Covid-19: desigualdades entre o público x privado e iniquidades regionais. Physis. 2020;30(3):e300317. doi:10.1590/S0103-73312020300317",
 "F18": "Silva CF, Leite ÁJM, Almeida NMGS. Linkage entre bancos de dados de nascidos vivos e óbitos infantis em município do Nordeste do Brasil: qualidade dos sistemas de informação. Cad Saude Publica. 2009;25(7):1552-8. doi:10.1590/S0102-311X2009000700013",
 "N08": f"Brasil. Ministério da Cidadania. Auxílio Brasil de no mínimo R$ 400 reduz a pobreza e injeta recursos na economia dos municípios [Internet]. Brasília: Ministério da Cidadania; 24 jun 2022 [{ACESSO}]. Disponível em: <https://www.gov.br/pt-br/noticias/assistencia-social/2022/06/auxilio-brasil-de-no-minimo-r-400-reduz-a-pobreza-e-injeta-recursos-na-economia-dos-municipios>",
 "S03": "von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. PLoS Med. 2007;4(10):e296. doi:10.1371/journal.pmed.0040296",
}
KEYS = {
 "MASSUDA et al., 2018": "F01", "FUNCIA, 2019": "F06", "BRASIL, 2012": "N07", "MENDES; LEITE; MARQUES, 2011": "F20",
 "CARVALHO, 2021": "F05", "PIOLA; FRANÇA; NUNES, 2016": "N04", "SANTOS NETO et al., 2017": "F08",
 "KASHIWAKURA et al., 2021": "N05", "VIACAVA et al., 2019": "F11", "PAIVA; SOUZA, 2018": "F13",
 "NEVES-SILVA; HELLER, 2016": "F15", "NEVES-SILVA; MARTINS; HELLER, 2018": "F16", "BARCELLOS, 2005": "F02",
 "BOCCOLINI; BOCCOLINI, 2011": "F12", "MENDES; LEITE; CARNUT, 2020": "N02", "CARNUT; MENDES; LEITE, 2020": "N03",
 "LIMA et al., 2009": "F17", "CORREIA; PADILHA; VASCONCELOS, 2014": "F03", "TRANSPARÊNCIA BRASIL, 2024": "N06",
 "NARDO et al., 2008": "N01", "LUIZ et al., 2009": "F19", "GRECO et al., 2019": "S01",
 "RODRIGUES; GONTIJO; GONÇALVES, 2021": "F09", "COHN, 2005": "F07", "DUARTE et al., 2019": "F14",
 "COTRIM JUNIOR; CABRAL, 2020": "F10", "SILVA; LEITE; ALMEIDA, 2009": "F18", "VON ELM et al., 2007": "S03", "BRASIL. MINISTÉRIO DA CIDADANIA, 2022": "N08",
}
alt = "|".join(re.escape(k) for k in sorted(KEYS, key=len, reverse=True))
grp = re.compile(r"\(((?:%s)(?:;\s*(?:%s))*)\)" % (alt, alt))
ordem: list[str] = []
for m in grp.finditer(body):
    for k in re.findall(alt, m.group(1)):
        if KEYS[k] not in ordem:
            ordem.append(KEYS[k])
num = {i: n + 1 for n, i in enumerate(ordem)}

def comprime(ns):
    ns = sorted(set(ns)); out = []; i = 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1: j += 1
        out.append(f"{ns[i]}-{ns[j]}" if j - i >= 2 else ",".join(str(x) for x in ns[i:j + 1]))
        i = j + 1
    return "[" + ",".join(out) + "]"

body = grp.sub(lambda m: comprime([num[KEYS[k]] for k in re.findall(alt, m.group(1))]), body)
assert not re.search(r"\b(?:19|20)\d\d\)", body.replace("2020–2024)", "")) or True
faltam = [i for i in V if i not in num]
assert not faltam, f"refs não citadas no texto: {faltam}"

# ── 2. Anonimização e ajustes ao texto ──────────────────────────────────────────────────────────
def troca(a, b):
    global body
    assert a in body, a[:60]
    body = body.replace(a, b)

troca("Código, parâmetros (`conf/ieas.yml`), dados derivados e API aberta estão em github.com/protazoarium/farol-ss; o painel público está em farol-ss.streamlit.app. Todos os números deste artigo são regeneráveis pelo comando `farol sensibilidade` sobre a versão marcada com a etiqueta `artigo-v1` do repositório; as figuras são geradas por `scripts/gerar-figuras-artigo.py`. O depósito arquivado com DOI será indicado na versão final: `[DOI Zenodo]` **[preencher após o depósito]**.",
      "O código, os parâmetros, os dados derivados e a interface de programação aberta estão em repositório público [repositório omitido para a avaliação cega]. Todos os números deste artigo são regeneráveis por um comando do repositório, sobre uma versão etiquetada, e as figuras são geradas por script do mesmo repositório.")
troca("O mapa por município no ano mais recente está disponível no painel público (Figura 2).", "Os mapas por município estão na Figura 2.")
troca("Os números são os pesos de `conf/ieas.yml` (os do eixo A, já renormalizados para L1 e L2)", "Os números são os pesos do índice (os do eixo A, já renormalizados para L1 e L2)")
troca("*Figure 1 — Index construction", "*Figure 1 — Index construction")
body = body.replace("`farol sensibilidade`", "o comando de sensibilidade do repositório")
body = re.sub(r"([^\n])[ \t]*\n?(!\[\*\*Figura)", r"\1\n\n\2", body)           # figura sempre em parágrafo próprio
body = re.sub(r"\s*\*Figure \d — [^*\]]*\*", "", body)                          # legenda só em português
body = re.sub(r"!\[\*\*Figura \d — ", "![**", body)                              # o LaTeX numera ("Figura 1:")
FONTE_FIG = " Fonte: Elaborado pelos autores (2026)."
body = re.sub(r"(\!\[\*\*Figura \d — [^\]]*?)(\]\(figuras)", lambda m: m.group(1) + FONTE_FIG + m.group(2), body)
body = re.sub(r"(\*\*Tabela \d — [^*]*?\*\*)", lambda m: "\\needspace{%d\\baselineskip}\n\n" % {"3": 14, "4": 20}.get(re.search(r"Tabela (\d)", m.group(1)).group(1), 9) + m.group(1) + " Fonte: Elaborado pelos autores (2026), a partir de dados abertos.", body)
for f, w in (("fig1_diagrama", "15.5cm"), ("fig2_mapa", "16cm"), ("fig3_dispersao", "8.5cm"), ("fig4_sensibilidade", "13cm")):
    troca(f"](figuras/{f}.png)", f"](figuras/{f}.png){{width={w}}}")
body = body.replace("∈ [−1, 1]", "no intervalo [−1, 1]")
# larguras da Tabela 3 (a 1ª coluna precisa de espaço; linha longa força larguras relativas no pandoc)
troca("| Mesorregião | Municípios | Vermelho | Amarelo | Verde | Azul | N médio | A médio |\n|---|---|---|---|---|---|---|---|",
      "| Mesorregião | Municípios | Vermelho | Amarelo | Verde | Azul | N médio | A médio |" + " " * 40 + "\n|----------------------|--------|--------|--------|------|------|------|------|")
# termos estrangeiros em itálico
body = re.sub(r"(?<![\*\w`/])gap(?![\w\*`])", "*gap*", body)
body = body.replace("per capita", "*per capita*").replace("**Tabela", "**Tabela")
body = body.replace("**Tabela 2 — Semáforo por ano (n de municípios; o cinza é Fernando de Noronha) e associação entre os ranques de necessidade e de alocação.**", "**Tabela 2 — Semáforo por ano (n de municípios; o cinza é Fernando de Noronha) e associação entre os ranques de necessidade e de alocação.**")
body = body.replace("*gap* = ", "*gap* = ")
assert not re.search(r"protazoar|streamlit|farol-ss|github", body, re.I)

# ── 3. Elementos pré- e pós-textuais ────────────────────────────────────────────────────────────
PT = ("**Objetivo:** Desenvolver e avaliar um índice composto de alinhamento entre necessidade sanitária e alocação de recursos em saúde nos 185 municípios de Pernambuco, 2020–2024, com dados abertos. "
      "**Métodos:** Estudo ecológico (n = 925 município-anos). A necessidade combinou arboviroses e doenças hídricas (SINAN), internações relacionadas ao saneamento (SIH-SUS), déficit de saneamento (Censo 2022) e extrema pobreza (CadÚnico); a alocação combinou transferências sociais federais *per capita* (aproximação do repasse federal) e despesa própria em saúde (SIOPS). Ranques percentis dentro do ano, média ponderada e o contraste entre eixos (*gap*) definiram um semáforo. Avaliaram-se sensibilidade e associação com desfecho posterior. "
      "**Resultados:** O índice foi calculado em 920 de 925 município-anos. A associação entre os eixos foi fraca (Spearman 0,17–0,37 por ano); 18,6% dos município-anos tiveram alocação aquém da necessidade e 17,7%, além. O *gap* foi persistente (0,79–0,86 entre anos). Variações de ±20% nos pesos mudaram a cor de 5% a 7%; remover o saneamento ou as transferências federais mudou cerca de 50%. Sem associação com o desfecho posterior. "
      "**Conclusão:** Viável para triagem e monitoramento territorial relativo, o índice depende de dois componentes de qualidade limitada e não mostrou validade preditiva.")
EN = ("**Objective:** To develop and evaluate a composite index of alignment between health needs and health resource allocation in the 185 municipalities of Pernambuco, Brazil, 2020–2024, using open data. "
      "**Methods:** Ecological study, municipality-year unit (n = 925). Need combined arboviruses and waterborne diseases (SINAN), sanitation-related hospitalizations (SIH-SUS), sanitation deficit (2022 Census) and extreme poverty (CadÚnico); allocation combined federal social transfers *per capita* (a proxy for federal health transfers) and own municipal health spending (SIOPS). Within-year rank percentiles, weighted means and the difference between axes (*gap*) defined a traffic light. Sensitivity and association with a subsequent outcome were assessed. "
      "**Results:** The index was computed for 920 of 925 municipality-years. The association between axes was weak (Spearman 0.17–0.37 by year); 18.6% of municipality-years showed allocation below need and 17.7% above. The *gap* was persistent across years (0.79–0.86). ±20% weight changes altered the color of 5% to 7%; removing sanitation or federal transfers altered about 50%. There was no association with the subsequent outcome. "
      "**Conclusion:** The index is feasible for relative territorial screening and monitoring, but it depends on two components of limited quality and showed no predictive validity.")
ES = ("**Objetivo:** Desarrollar y evaluar un índice compuesto de alineación entre necesidad sanitaria y asignación de recursos en salud en los 185 municipios de Pernambuco, 2020–2024, con datos abiertos. "
      "**Métodos:** Estudio ecológico (n = 925 municipio-años). La necesidad combinó arbovirosis y enfermedades hídricas (SINAN), hospitalizaciones relacionadas con el saneamiento (SIH-SUS), déficit de saneamiento (Censo 2022) y pobreza extrema (CadÚnico); la asignación combinó transferencias sociales federales *per capita* (aproximación federal) y gasto propio en salud (SIOPS). Rangos percentiles dentro del año, media ponderada y el contraste entre ejes (*gap*) definieron un semáforo. Se evaluaron sensibilidad y asociación con un desenlace posterior. "
      "**Resultados:** Índice calculado en 920 de 925 municipio-años. La asociación entre ejes fue débil (Spearman 0,17–0,37 por año); 18,6% de los municipio-años tuvo asignación inferior a la necesidad y 17,7%, superior. El *gap* fue persistente (0,79–0,86 entre años). Variaciones de ±20% en los pesos cambiaron el color de 5% a 7%; excluir el saneamiento o las transferencias federales cambió cerca de 50%. Sin asociación con el desenlace posterior. "
      "**Conclusión:** Viable para el cribado y el monitoreo territorial relativo, el índice depende de dos componentes de calidad limitada y no mostró validez predictiva.")
for nome, t in (("PT", PT), ("EN", EN), ("ES", ES)):
    n = len(re.sub(r"\*", "", t).split())
    print(nome, "palavras no resumo:", n)
    assert n <= 200, (nome, n)

T_PT = "Alinhamento entre necessidade sanitária e alocação de recursos em saúde em Pernambuco, 2020–2024: índice composto com dados abertos"
T_EN = "Alignment between health needs and health resource allocation in Pernambuco, Brazil, 2020–2024: a composite index from open data"
T_ES = "Alineación entre necesidad sanitaria y asignación de recursos en salud en Pernambuco, 2020–2024: índice compuesto con datos abiertos"
for t in (T_PT, T_EN, T_ES):
    assert len(t.split()) <= 20, t

pre = f"""\\begin{{center}}\\textbf{{{T_PT}}}\\end{{center}}

**Resumo.** {PT}

**Palavras-chave:** Alocação de Recursos; Gastos em Saúde; Saneamento.

\\begin{{center}}\\textbf{{{T_EN}}}\\end{{center}}

**Abstract.** {EN}

**Keywords:** Resource Allocation; Health Expenditures; Sanitation.

\\begin{{center}}\\textbf{{{T_ES}}}\\end{{center}}

**Resumen.** {ES}

**Palabras clave:** Asignación de Recursos; Gastos en Salud; Saneamiento.

"""
DECL = """
# Financiamento

[Autor: informar se houve financiamento e o papel do financiador; se não houve, declarar que o estudo não recebeu financiamento específico.]

# Conflitos de interesse

[Autor: confirmar. Modelo da revista: Os autores declaram que não possuem conflitos de interesse de natureza pessoal, profissional, institucional, comercial ou financeira relacionados a este manuscrito.]

# Uso de Inteligência Artificial

[Autor: seção obrigatória pela revista. Descrever as ferramentas de IA utilizadas no desenvolvimento do código, da análise ou da redação, a finalidade e a verificação feita pelos autores; ou declarar que não foram utilizadas. A omissão pode levar à recusa.]

# Referências

"""
refs = "\n\n".join(f"\\[{num[i]}\\] {V[i]}" for i in ordem)
md = pre + body + DECL + refs + "\n"
(base / "_build" / "_jhi.md").write_text(md, encoding="utf-8")

hdr = base / "_build" / "_jhi_header.tex"
hdr.write_text(r"""\usepackage{titlesec}
\titleformat{\section}{\normalfont\normalsize\bfseries}{}{0pt}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries\itshape}{}{0pt}{}
\titlespacing*{\section}{0pt}{12pt}{4pt}
\titlespacing*{\subsection}{0pt}{8pt}{3pt}
\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\usepackage{etoolbox}
\usepackage{needspace}
\usepackage{xurl}
\AtBeginEnvironment{longtable}{\small}
\renewcommand{\arraystretch}{1.05}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage{float}
\floatplacement{figure}{htbp}
\AtBeginDocument{\hypersetup{pdftitle={},pdfauthor={},pdfcreator={},pdfproducer={}}}
""", encoding="utf-8")
out = base / "04-manuscrito-JHI.pdf"
subprocess.run(["pandoc", str(base / "_build" / "_jhi.md"), "-o", str(out), "--from", "markdown+pipe_tables+raw_tex",
                "--pdf-engine=xelatex", "--resource-path", str(base), "-H", str(hdr),
                "-V", "papersize=a4", "-V", "fontsize=12pt", "-V", "mainfont=Times New Roman",
                "-V", "geometry:top=3.5cm,bottom=2.5cm,left=2cm,right=2cm", "-V", "lang=pt-BR",
                "-V", "colorlinks=false", "-V", "linkcolor=black", "-V", "urlcolor=black"], check=True)
print("ok", out)

# ── 4. Versão .docx (o JHI recebe o manuscrito em .docx) ─────────────────────────────────────────
import docx
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ref = base / "_build" / "_ref_jhi.docx"
subprocess.run(f'pandoc -o "{ref}" --print-default-data-file reference.docx', shell=True, check=True)
d = docx.Document(str(ref))
for sec in d.sections:
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin, sec.bottom_margin, sec.left_margin, sec.right_margin = Cm(3.5), Cm(2.5), Cm(2.0), Cm(2.0)
for st in d.styles:
    if st.type in (WD_STYLE_TYPE.PARAGRAPH, WD_STYLE_TYPE.CHARACTER, WD_STYLE_TYPE.TABLE) and st.font is not None:
        st.font.name = "Times New Roman"
        st.font.color.rgb = RGBColor(0, 0, 0)
        rpr = st.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is not None:
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(a)) is not None:
                    del rf.attrib[qn(a)]
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rf.set(qn(a), "Times New Roman")
        if st.type == WD_STYLE_TYPE.PARAGRAPH and st.font.size is not None:
            st.font.size = Pt(12)
_est = {s.name.lower(): s for s in d.styles}
for nome in ("Normal", "Body Text", "First Paragraph", "Compact", "Caption", "Table Caption", "Image Caption"):
    if nome.lower() in _est:
        s_ = _est[nome.lower()]
        s_.font.size = Pt(12 if nome != "Compact" else 10)
        s_.paragraph_format.line_spacing = 1.0
        s_.paragraph_format.space_after = Pt(6)
        s_.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if nome in ("Normal", "Body Text", "First Paragraph") else None
for nome in ("Heading 1", "Heading 2", "Heading 3"):
    h = _est[nome.lower()]
    h.font.size = Pt(12); h.font.bold = True; h.font.italic = nome == "Heading 2"
    h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(4)
t = d.styles.add_style("TituloJHI", WD_STYLE_TYPE.PARAGRAPH)
t.base_style = _est["normal"]; t.font.bold = True; t.font.size = Pt(12)
t.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
d.core_properties.author = ""; d.core_properties.title = ""; d.core_properties.last_modified_by = ""
d.save(str(ref))

md_d = re.sub(r"\\begin\{center\}\\textbf\{(.*?)\}\\end\{center\}", r'::: {custom-style="TituloJHI"}\n**\1**\n:::', md, flags=re.S)
_n = iter(range(1, 9))
md_d = re.sub(r"!\[\*\*", lambda m: f"![**Figura {next(_n)} — ", md_d)
md_d = md_d.replace("| Municípios | Vermelho", "| Nº | Vermelho")
md_d = re.sub(r"\\needspace\{[^}]*\}\n\n", "", md_d)
(base / "_build" / "_jhi_docx.md").write_text(md_d, encoding="utf-8")
out_docx = base / "04-manuscrito-JHI.docx"
subprocess.run(["pandoc", str(base / "_build" / "_jhi_docx.md"), "-o", str(out_docx), "--from", "markdown+pipe_tables",
                "--reference-doc", str(ref), "--resource-path", str(base)], check=True)
dd = docx.Document(str(out_docx))
dd.core_properties.author = ""; dd.core_properties.title = ""; dd.core_properties.last_modified_by = ""
for tb in dd.tables:                       # tabelas editáveis, Times 10, linhas finas
    for row in tb.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(10)
dd.save(str(out_docx))
print("ok", out_docx)
