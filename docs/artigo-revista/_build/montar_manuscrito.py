"""Monta 03-manuscrito.docx: injeta as referências (de refs.js) e chama o pandoc.

Uso (a partir de docs/artigo-revista/): node -e para dump de refs -> JSON; este script
lê o JSON e o .md. Ver comando no README do pacote.
"""
import json, re, subprocess, sys, pathlib
base = pathlib.Path(__file__).resolve().parent.parent
md = (base / "03-manuscrito.md").read_text(encoding="utf-8")
refs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
# Correções conferidas nas páginas dos periódicos/editores (nov/2026) — substituem o texto de refs.js.
CORRIGIDAS = {
 "F01": "MASSUDA, A.; HONE, T.; LELES, F. A. G.; DE CASTRO, M. C.; ATUN, R. The Brazilian health system at crossroads: progress, crisis and resilience. BMJ Global Health, v. 3, n. 4, e000829, 2018. DOI: 10.1136/bmjgh-2018-000829.",
 "F08": "SANTOS NETO, J. A.; MENDES, Á. N.; PEREIRA, A. C.; PARANHOS, L. R. Análise do financiamento e gasto do Sistema Único de Saúde dos municípios da região de saúde Rota dos Bandeirantes do estado de São Paulo, Brasil. Ciência & Saúde Coletiva, v. 22, n. 4, p. 1269-1280, 2017. DOI: 10.1590/1413-81232017224.28452016.",
 "F11": "VIACAVA, F.; PORTO, S. M.; CARVALHO, C. C.; BELLIDO, J. G. Desigualdades regionais e sociais em saúde segundo inquéritos domiciliares (Brasil, 1998-2013). Ciência & Saúde Coletiva, v. 24, n. 7, p. 2745-2760, 2019. DOI: 10.1590/1413-81232018247.15812017.",
 "F17": "LIMA, C. R. A.; SCHRAMM, J. M. A.; COELI, C. M.; SILVA, M. E. M. Revisão das dimensões de qualidade dos dados e métodos aplicados na avaliação dos sistemas de informação em saúde. Cadernos de Saúde Pública, v. 25, n. 10, p. 2095-2109, 2009. DOI: 10.1590/s0102-311x2009001000002.",
 "N01": "NARDO, M.; SAISANA, M.; SALTELLI, A.; TARANTOLA, S.; HOFFMANN, A.; GIOVANNINI, E. Handbook on constructing composite indicators: methodology and user guide. Paris: OECD Publishing, 2008. DOI: 10.1787/9789264043466-en.",
 "F19": "LUIZ, O. C.; HEIMANN, L. S.; BOARETTO, R. C.; PACHECO, A. G.; PESSOTO, U. C.; IBANHES, L. C. et al. Diferenciais intermunicipais de condições de vida e saúde: construção de um indicador composto. Revista de Saúde Pública, v. 43, n. 1, p. 115-122, 2009. DOI: 10.1590/s0034-89102009000100015.",
 "F14": "DUARTE, J. L.; DIAZ-QUIJANO, F. A.; BATISTA, A. C.; DUARTE, A. F.; MELCHIOR, L. A. K.; GIATTI, L. L. Variabilidade climática e internações por doenças diarreicas infecciosas em um município da Amazônia Ocidental brasileira. Ciência & Saúde Coletiva, v. 24, n. 8, p. 2959-2970, 2019. DOI: 10.1590/1413-81232018248.21232017.",
 "N02": "MENDES, Á.; LEITE, M. G.; CARNUT, L. Uma metodologia para rateio dos recursos federais do SUS: o índice de necessidades de saúde. Revista de Saúde Pública, v. 54, art. 77, 2020. DOI: 10.11606/s1518-8787.2020054001661.",
 "N04": "PIOLA, S. F.; FRANÇA, J. R. M.; NUNES, A. Os efeitos da Emenda Constitucional 29 na alocação regional dos gastos públicos no Sistema Único de Saúde no Brasil. Ciência & Saúde Coletiva, v. 21, n. 2, p. 411-422, 2016. DOI: 10.1590/1413-81232015212.10402015.",
 "N05": "KASHIWAKURA, H. K. et al. Retrato da atenção básica no Brasil: gastos e infraestrutura em municípios brasileiros. Ciência & Saúde Coletiva, v. 26, supl. 2, p. 3397-3408, 2021. DOI: 10.1590/1413-81232021269.2.37112019.",
 "N06": "TRANSPARÊNCIA BRASIL. Recomendações e desafios técnicos — PNCP: qualidade de dados. Versão 1.0. São Paulo: Transparência Brasil, dez. 2024. Disponível em: https://www.transparencia.org.br/downloads/publicacoes/qualidade_dados_portal_nacional_de_contratacoes_publicas.pdf.",
 "S01": "GRECO, S.; ISHIZAKA, A.; TASIOU, M.; TORRISI, G. On the methodological framework of composite indices: a review of the issues of weighting, aggregation, and robustness. Social Indicators Research, v. 141, p. 61-94, 2019. DOI: 10.1007/s11205-017-1832-9.",
 "S03": "VON ELM, E. et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. PLoS Medicine, v. 4, n. 10, e296, 2007. DOI: 10.1371/journal.pmed.0040296.",
}
for r_ in refs:
    if r_["id"] in CORRIGIDAS:
        r_["ref"] = CORRIGIDAS[r_["id"]]
txt = sorted((r["ref"] for r in refs), key=lambda s: re.sub(r"[^A-ZÀ-Ý]", "", s.upper()))
out = "\n\n".join(txt)
(base / "_build" / "_manuscrito_com_refs.md").write_text(md.replace("<!--REFS-->", out), encoding="utf-8")
subprocess.run(["pandoc", str(base / "_build" / "_manuscrito_com_refs.md"), "-o", str(base / "03-manuscrito.docx"),
                "--from", "markdown+pipe_tables", "--resource-path", str(base)], check=True)
print("ok")
