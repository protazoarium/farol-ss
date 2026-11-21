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
